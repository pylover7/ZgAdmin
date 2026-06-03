from fastapi import APIRouter

from .login import loginRouter
from .operation import operationRouter
from .system import systemRouter

logsRouter = APIRouter()
logsRouter.include_router(loginRouter, prefix="/login", tags=["登录管理"])
logsRouter.include_router(operationRouter, prefix="/operation", tags=["操作日志"])
logsRouter.include_router(systemRouter, prefix="/system", tags=["系统日志"])
