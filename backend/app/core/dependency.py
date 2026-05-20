from uuid import UUID
import time
import asyncio
from collections.abc import Generator
from typing import Annotated

import jwt
from sqlmodel import Session
from fastapi import Depends, Header, HTTPException, Request

from app.controllers.user import userController
from app.core.database import engine
from app.core.ctx import CTX_USER_ID
from app.models import Role, User
from app.settings import settings
from app.settings.log import logger


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


class AuthControl:
    @classmethod
    async def is_authed(cls, session: SessionDep,
                        authorization: str = Header(..., description="token验证")):
        try:
            token = authorization.split(" ")[1]
            decode_data = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=settings.JWT_ALGORITHM)
            user_id: str = decode_data.get("user_id")
            CTX_USER_ID.set(user_id)
            user = await userController.get(session, UUID(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="验证失败！！！")
            if user.is_superuser:  # 超级管理员不验证状态
                return user
            if not user.status:
                raise HTTPException(status_code=400, detail="用户已被禁用")
            for item in user.roles:
                if not item.status:
                    raise HTTPException(status_code=400, detail="用户已被禁用")
            return user
        except jwt.DecodeError as exc:
            raise HTTPException(status_code=401, detail="无效的Token") from exc
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=401, detail="登录已过期") from exc


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(
            AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path
        roles: list[Role] = current_user.roles
        if not roles:
            raise HTTPException(status_code=403,
                                detail="The user is not bound to a role")
        apis = [role.apis for role in roles]
        permission_apis = list(set((api.method, api.path)
                               for api in sum(apis, [])))
        # path = "/api/v1/auth/userinfo"
        # method = "GET"
        if (method, path) not in permission_apis:
            logger.debug(
                f"已禁止用户 {
                    current_user.username} 访问 {method} {path} 接口")
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied method:{method} path:{path}")
        logger.debug(
            f"已允许用户 {
                current_user.username} 访问 {method} {path} 接口")


DependAuth = Depends(AuthControl.is_authed)
DependPermission = Depends(PermissionControl.has_permission)
# 类型注解辅助：直接注入当前用户对象（替代不可靠的 ContextVar）
DependUser = Annotated[User, DependAuth]


class RateLimiter:
    """IP 级别请求限流 — 防止登录暴力破解"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max = max_requests
        self.window = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def _cleanup(self):
        now = time.monotonic()
        cutoff = now - self.window
        self._attempts = {
            ip: [t for t in times if t > cutoff]
            for ip, times in self._attempts.items() if any(t > cutoff for t in times)
        }

    async def check(self, request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        async with self._lock:
            await self._cleanup()
            attempts = self._attempts.get(ip, [])
            if len(attempts) >= self.max:
                raise HTTPException(
                    status_code=429,
                    detail="请求过于频繁，请稍后再试"
                )
            attempts.append(time.monotonic())
            self._attempts[ip] = attempts


rate_limiter = RateLimiter()
DependRateLimit = Depends(rate_limiter.check)
