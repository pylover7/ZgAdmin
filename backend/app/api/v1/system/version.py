"""版本信息接口"""
from fastapi import APIRouter
from app.models import Success
from app.settings import settings

versionRouter = APIRouter()


@versionRouter.get("/info", summary="获取版本信息")
async def get_version_info():
    """获取项目版本信息"""
    return Success(data={
        "version": settings.VERSION,
        "project_name": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "environment": settings.ENVIRONMENT
    })


@versionRouter.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return Success(data={
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    })