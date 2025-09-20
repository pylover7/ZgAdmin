import datetime
from typing import Optional
from uuid import UUID
from sqlmodel import Session, select
from fastapi.exceptions import HTTPException
from fastapi import Request

from app.settings.log import logger
from app.utils.ip import getIpAddress, getReqSysBro
from app.utils.password import get_password_hash, verify_password
from app.models import User, UserCreate, UserUpdate
from app.models.login import CredentialsSchema
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
        db_obj = User.model_validate(
            obj_in, update={
                "hashed_password": get_password_hash(
                    obj_in.password)}
        )
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    async def update(self, session: Session, id: UUID,
                     obj_in: UserUpdate) -> User | None:
        db_user = session.get(User, id)
        if db_user is None:
            return None
        user_data = obj_in.model_dump(exclude_unset=True)
        extra_data = {}
        if "password" in user_data:
            password = user_data["password"]
            hashed_password = get_password_hash(password)
            extra_data["hashed_password"] = hashed_password
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
        user: User | None = await self.get_user_by_name(session=session, username=credentials.username)
        sysBro = await getReqSysBro(request=request)
        ip_area = await getIpAddress(request.client.host if request.client else "unknown")
        if user is None:
            raise HTTPException(status_code=400, detail="无效的用户名")
        try:
            result = verify_password(credentials.password, user.password)
            if not result:
                raise HTTPException(status_code=400, detail="密码错误!")
        except Exception:
            await logger.loginFail(
                username=user.username,
                ip=request.client.host if request.client else "unknown",
                address=ip_area,
                system=sysBro.system,
                browser=sysBro.browser,
                behavior=0
            )
            raise HTTPException(status_code=400, detail="密码错误!")
        if user.is_superuser:  # 超级管理员不验证状态
            await logger.loginSuccess(
                username=user.username,
                ip=request.client.host if request.client else "unknown",
                address=ip_area,
                system=sysBro.system,
                browser=sysBro.browser,
                behavior=0
            )
            return user
        if not user.status:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        for item in user.roles:
            if not item.status:
                raise HTTPException(status_code=400, detail="用户已被禁用")
        await logger.loginSuccess(
            username=user.username,
            ip=request.client.host if request.client else "unknown",
            address=ip_area,
            system=sysBro.system,
            browser=sysBro.browser,
            behavior=0
        )
        return user

    async def update_last_login(self, session: Session, id: UUID):
        user = session.get(User, id)
        user.last_login = now(0) # type: ignore
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


userController = UserController()
