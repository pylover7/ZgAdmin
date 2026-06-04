from fastapi import APIRouter

from .api import apiRouter
from .depart import departRouter
from .menu import menuRouter
from .notice import noticeRouter
from .role import roleRouter
from .user import userRouter
from .version import versionRouter

systemRouter = APIRouter()
systemRouter.include_router(userRouter, prefix="/user", tags=["系统用户模块"])
systemRouter.include_router(departRouter, prefix="/dept", tags=["系统部门模块"])
systemRouter.include_router(roleRouter, prefix="/role", tags=["系统角色模块"])
systemRouter.include_router(menuRouter, prefix="/menu", tags=["系统菜单模块"])
systemRouter.include_router(apiRouter, prefix="/api", tags=["系统接口模块"])
systemRouter.include_router(versionRouter, prefix="/version", tags=["版本信息模块"])
systemRouter.include_router(noticeRouter, prefix="/notice", tags=["通知管理模块"])


__all__ = ["systemRouter"]
