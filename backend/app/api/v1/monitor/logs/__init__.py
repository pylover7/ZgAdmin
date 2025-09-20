from fastapi import APIRouter
from .login import loginRouter

logsRouter = APIRouter()
logsRouter.include_router(loginRouter, prefix="/login", tags=["登录管理"])
