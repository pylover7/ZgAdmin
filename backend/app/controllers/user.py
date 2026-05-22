from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlmodel import Session, select
from fastapi.exceptions import HTTPException
from fastapi import Request

from app.settings.log import logger
from app.utils.ip import getIpAddress, getReqSysBro
from app.utils.password import get_password_hash, verify_password
from app.utils.password_policy import validate_password_strength
from app.models import User, UserCreate, UserUpdate
from app.models.login import CredentialsSchema
from app.models.security import SecurityPolicy
from app.utils import now
from app.core.crud import CRUDBase


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def create(self, session: Session, obj_in: UserCreate) -> User:
        """
        创建用户

        :param session: session
        :param obj_in: 用户创建数据
        :return: 用户对象
        """
        # 密码复杂度校验
        policy = session.exec(select(SecurityPolicy)).first()
        if policy:
            valid, msg = validate_password_strength(obj_in.password, policy)
            if not valid:
                raise HTTPException(status_code=400, detail=msg)

        db_obj = User.model_validate(obj_in)
        db_obj.password = get_password_hash(obj_in.password)
        # 初始化密码历史
        if policy and policy.password_history_count > 0:
            db_obj.password_history = [db_obj.password]
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    async def update(self, session: Session, pk: UUID,
                     obj_in: UserUpdate) -> User | None:
        db_user = session.get(User, pk)
        if db_user is None:
            return None
        user_data = obj_in.model_dump(exclude_unset=True)
        extra_data = {}
        if "password" in user_data:
            hashed = get_password_hash(user_data.pop("password"))
            extra_data["password"] = hashed
        db_user.sqlmodel_update(user_data, update=extra_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    async def get_user_by_email(
            self, session: Session, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        session_user = session.exec(statement).first()
        return session_user

    async def get_user_by_name(self, session: Session, username: str) -> Optional[User]:
        """
        通过用户名获取用户

        :param session: session
        :param username: 用户名
        :return: 用户对象
        """
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        return user

    async def authenticate(
        self, session: Session,
        credentials: CredentialsSchema,
        request: Request
    ) -> User:
        user: User | None = await self.get_user_by_name(
            session=session,
            username=credentials.username
        )
        sysBro = await getReqSysBro(request=request)
        ip = request.client.host if request.client else "unknown"
        ip_area = await getIpAddress(ip)

        if user is None:
            raise HTTPException(status_code=400, detail="用户名或密码错误")

        # 检查账号锁定（超级管理员不受锁定限制）
        if not user.is_superuser and user.locked_until:
            if datetime.now() < user.locked_until:
                remaining = int((user.locked_until - datetime.now()).total_seconds() / 60)
                raise HTTPException(
                    status_code=400,
                    detail=f"账号已锁定，请 {remaining} 分钟后重试"
                )
            # 锁定已过期，重置
            user.failed_login_count = 0
            user.locked_until = None

        # 验证密码
        result = verify_password(credentials.password, user.password)
        if not result:
            # 密码错误 — 非超级管理员记录失败次数
            if not user.is_superuser:
                policy = session.exec(select(SecurityPolicy)).first()
                max_attempts = policy.max_login_attempts if policy else 5
                lockout_minutes = policy.lockout_duration_minutes if policy else 30

                user.failed_login_count = (user.failed_login_count or 0) + 1

                if user.failed_login_count >= max_attempts:
                    user.locked_until = datetime.now() + timedelta(minutes=lockout_minutes)
                    user.failed_login_count = 0
                    await logger.loginFail(
                        username=user.username, ip=ip, address=ip_area,
                        system=sysBro.system, browser=sysBro.browser, behavior=0
                    )
                    session.add(user)
                    session.commit()
                    raise HTTPException(
                        status_code=400,
                        detail=f"连续登录失败 {max_attempts} 次，账号已锁定 {lockout_minutes} 分钟"
                    )

                await logger.loginFail(
                    username=user.username, ip=ip, address=ip_area,
                    system=sysBro.system, browser=sysBro.browser, behavior=0
                )
                session.add(user)
                session.commit()
                remaining_attempts = max_attempts - user.failed_login_count
                raise HTTPException(
                    status_code=400,
                    detail=f"用户名或密码错误，还可尝试 {remaining_attempts} 次"
                )

            await logger.loginFail(
                username=user.username, ip=ip, address=ip_area,
                system=sysBro.system, browser=sysBro.browser, behavior=0
            )
            raise HTTPException(status_code=400, detail="用户名或密码错误")

        # 密码正确 — 清零失败计数
        user.failed_login_count = 0
        user.locked_until = None

        if user.is_superuser:
            await logger.loginSuccess(
                username=user.username, ip=ip, address=ip_area,
                system=sysBro.system, browser=sysBro.browser, behavior=0
            )
            session.add(user)
            session.commit()
            return user

        if not user.status:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        for item in user.roles:
            if not item.status:
                raise HTTPException(status_code=400, detail="用户已被禁用")

        await logger.loginSuccess(
            username=user.username, ip=ip, address=ip_area,
            system=sysBro.system, browser=sysBro.browser, behavior=0
        )
        session.add(user)
        session.commit()
        return user

    async def update_last_login(self, session: Session, pk: UUID):
        user = session.get(User, pk)
        user.last_login = now(0)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    async def unlock_user(self, session: Session, pk: UUID) -> User | None:
        """管理员手动解锁用户"""
        user = session.get(User, pk)
        if user is None:
            return None
        user.failed_login_count = 0
        user.locked_until = None
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


userController = UserController()
