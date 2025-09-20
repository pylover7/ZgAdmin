from fastapi import APIRouter

from .logs import logsRouter

monitorRouter = APIRouter()
monitorRouter.include_router(logsRouter, prefix="/logs", tags=["日志管理"])
