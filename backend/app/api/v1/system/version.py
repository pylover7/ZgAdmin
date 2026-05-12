"""版本信息接口"""
import sys
import subprocess
import asyncio
from fastapi import APIRouter
from app.models import Success
from app.settings import settings
from app.settings.log import logger

versionRouter = APIRouter()


def _get_uv_version() -> str:
    """安全获取 uv 版本"""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        return result.stdout.strip()
    except Exception as e:
        logger.debug(f"获取 uv 版本失败: {e}")
        return "unknown"


@versionRouter.get("", summary="获取版本信息")
async def get_version_info():
    """获取项目版本信息"""

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    uv_version = await asyncio.to_thread(_get_uv_version)
    data = {
        "version": settings.VERSION,
        "project_name": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "environment": settings.ENVIRONMENT,
        "uv_version": uv_version,
        "python_version": python_version,
    }
    logger.debug(f"版本信息: {data}")
    return Success(data=data)
