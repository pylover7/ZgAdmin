from fastapi import APIRouter

from .file import fileRouter

resourceRouter = APIRouter()
resourceRouter.include_router(fileRouter, prefix="/file", tags=["文件管理"])
