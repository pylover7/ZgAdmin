"""版本工具"""

import re

import httpx
from packaging.version import Version

from app.settings import settings
from app.settings.log import logger

RELEASE_LATEST_URL = "https://cnb.cool/pylover/Tools/ZgAdmin/-/releases/latest"
RELEASE_BASE_URL = "https://cnb.cool/pylover/Tools/ZgAdmin/-/releases"
HTTP_TEMPORARY_REDIRECT = 307


def _strip_v(version: str) -> str:
    """去掉版本号 v 前缀，用于语义化版本比较"""
    return version.lstrip("v")


async def check_for_update() -> dict:
    """
    对比本地版本与远程仓库最新版本（方案 C：HEAD 请求 + 307 重定向提取版本号）
    返回: {"current_version", "latest_version", "has_update", "release_url"}
    """
    current = settings.VERSION
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.head(RELEASE_LATEST_URL, follow_redirects=False)

        if res.status_code == HTTP_TEMPORARY_REDIRECT:
            location = res.headers.get("location", "")
            match = re.search(r"/releases/tag/(v[\d.]+)", location)
            if match:
                latest = match.group(1)
                release_url = f"{RELEASE_BASE_URL}/tag/{match.group(1)}"
            else:
                latest = "unknown"
                release_url = ""
        else:
            # 404 或其他状态码 = 无 Release
            latest = "unknown"
            release_url = ""

        has_update = latest != "unknown" and Version(_strip_v(latest)) > Version(_strip_v(current))
    except Exception as e:
        logger.debug(f"检查更新失败: {e}")
        latest = "unknown"
        release_url = ""
        has_update = False

    return {
        "current_version": current,
        "latest_version": latest,
        "has_update": has_update,
        "release_url": release_url,
    }
