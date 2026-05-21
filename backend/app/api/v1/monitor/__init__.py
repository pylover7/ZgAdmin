from fastapi import APIRouter

from .logs import logsRouter
from .system import systemMonitorRouter

monitorRouter = APIRouter()
monitorRouter.include_router(logsRouter, prefix="/logs", tags=["日志管理"])
monitorRouter.include_router(systemMonitorRouter, prefix="/system", tags=["系统监控"])
