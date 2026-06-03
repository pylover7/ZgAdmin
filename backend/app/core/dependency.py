import functools
import operator
import time
from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request
from sqlmodel import Session

from app.core.ctx import CTX_USER_ID
from app.core.database import engine
from app.core.redis import get_redis
from app.models import Role, User
from app.models.login import refreshTokenSchema
from app.settings import settings
from app.settings.log import logger
from app.utils.jwtt import validate_token_and_get_user


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


class AuthControl:
    @classmethod
    async def is_authed(cls, session: SessionDep, authorization: str = Header(..., description="token验证")):
        token = authorization.split(" ")[1]
        # 设置上下文用户ID（供日志等场景使用）
        try:
            decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = decode_data.get("user_id", "")
            CTX_USER_ID.set(user_id)
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=401, detail="登录已过期") from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=401, detail="无效的Token") from exc
        return await validate_token_and_get_user(token, session)


async def validate_refresh_token(session: SessionDep, body: refreshTokenSchema) -> User:
    """依赖：验证 refreshToken 并返回有效用户"""
    return await validate_token_and_get_user(body.refreshToken, session)


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path
        roles: list[Role] = current_user.roles
        if not roles:
            raise HTTPException(status_code=403, detail="The user is not bound to a role")
        apis = [role.apis for role in roles]
        permission_apis = list({(api.method, api.path) for api in functools.reduce(operator.iadd, apis, [])})
        if (method, path) not in permission_apis:
            logger.debug(f"已禁止用户 {current_user.username} 访问 {method} {path} 接口")
            raise HTTPException(status_code=403, detail=f"Permission denied method:{method} path:{path}")
        logger.debug(f"已允许用户 {current_user.username} 访问 {method} {path} 接口")


DependAuth = Depends(AuthControl.is_authed)
DependPermission = Depends(PermissionControl.has_permission)
DependUser = Annotated[User, DependAuth]
DependRefreshUser = Annotated[User, Depends(validate_refresh_token)]


class RateLimiter:
    """IP 级别请求限流 — 基于 Redis 的滑动窗口"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max = max_requests
        self.window = window_seconds

    async def check(self, request: Request) -> None:
        redis = get_redis()
        ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{ip}"
        now = time.monotonic()

        results = await redis.pipeline_exec(
            [
                ("zremrangebyscore", key, 0, now - self.window),
                ("zcard", key),
                ("zadd", key, {str(now): now}),
                ("expire", key, self.window),
            ]
        )
        count = results[1]
        if count >= self.max:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


rate_limiter = RateLimiter()
DependRateLimit = Depends(rate_limiter.check)
