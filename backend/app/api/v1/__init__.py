from fastapi import APIRouter

from app.core.dependency import DependPermission

from .base import base_router
from .system import systemRouter
from .monitor import monitorRouter
from .settings import settingsRouter
from .settings.login import loginProtectedRouter
from .settings.general import generalProtectedRouter
from .settings.security import securityProtectedRouter
from .resource import resourceRouter

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(
    systemRouter,
    prefix="/system",
    dependencies=[DependPermission])
# 登录配置管理接口（需要认证）
v1_router.include_router(
    loginProtectedRouter,
    prefix="/settings/login",
    dependencies=[DependPermission])
# 通用设置 - 管理接口（需要认证）
v1_router.include_router(
    generalProtectedRouter,
    prefix="/settings/general",
    dependencies=[DependPermission])
# 安全设置 - 管理接口（需要认证）
v1_router.include_router(
    securityProtectedRouter,
    prefix="/settings/security",
    dependencies=[DependPermission])
# 其他设置接口需要认证
v1_router.include_router(
    settingsRouter,
    prefix="/settings",
    dependencies=[DependPermission])
v1_router.include_router(
    monitorRouter,
    prefix="/monitor",
    dependencies=[DependPermission]
)
v1_router.include_router(
    resourceRouter,
    prefix="/resource",
    dependencies=[DependPermission]
)
