"""版本工具"""

from pathlib import Path

import httpx
from packaging.version import Version

from app.settings.log import logger

REMOTE_VERSION_URL = "https://cnb.cool/pylove1/ZgAdmin/-/git/raw/dev/VERSION"


def get_local_version() -> str:
    """获取本地版本号"""
    version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
    return version_file.read_text().strip()


async def check_for_update() -> dict:
    """
    对比本地版本与远程仓库最新版本
    返回: {"current_version", "latest_version", "update_available"}
    """
    current = get_local_version()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(REMOTE_VERSION_URL)
            res.raise_for_status()
            latest = res.text.strip()
        update_available = Version(latest) > Version(current)
    except Exception as e:
        logger.debug(f"检查更新失败: {e}")
        latest = "unknown"
        update_available = False
    return {
        "current_version": current,
        "latest_version": latest,
        "update_available": update_available,
    }
