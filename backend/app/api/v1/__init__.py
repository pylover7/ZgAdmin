from fastapi import APIRouter

from app.core.dependency import DependPermission

from .base import base_router
from .system import systemRouter
from .pay import payRouter
from .monitor import monitorRouter
from .settings import settingsRouter
from .settings.login import loginPublicRouter, loginProtectedRouter

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(
    systemRouter,
    prefix="/system",
    dependencies=[DependPermission])
# 登录方式查询接口（公开）
v1_router.include_router(loginPublicRouter, prefix="/settings/login")
# 登录配置管理接口（需要认证）
v1_router.include_router(
    loginProtectedRouter,
    prefix="/settings/login",
    dependencies=[DependPermission])
# 其他设置接口需要认证
v1_router.include_router(
    settingsRouter,
    prefix="/settings",
    dependencies=[DependPermission])
v1_router.include_router(
    monitorRouter,
    prefix="/monitor",
    dependencies=[DependPermission])
