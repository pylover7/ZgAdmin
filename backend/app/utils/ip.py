import ipaddress
import re

import httpx
from fastapi import Request
from pydantic import BaseModel

from app.settings.log import logger

api1 = "https://opendata.baidu.com/api.php?query={}&co=&resource_id=6006&oe=utf8"
api2 = "https://searchplugin.csdn.net/api/v1/ip/get?ip={}"


async def getIpAddress(ip: str) -> str:
    if ipaddress.ip_address(ip).is_private:
        return "内网IP"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(api2.format(ip))
            return res.json()["data"]["address"].replace(" ", "")
        except Exception:
            logger.error("获取IP地址失败，API2失效！")
        try:
            res = await client.get(api1.format(ip))
            return res.json()["data"][0]["location"].replace(" ", "")
        except Exception:
            logger.error("获取IP地址失败，API1失效！")
            return ""


class SysBro(BaseModel):
    system: str
    browser: str


async def getReqSysBro(request: Request) -> SysBro:
    ua = request.headers.get("User-Agent")
    if ua:
        system_match = re.findall(r"\(([^;]+)", ua)
        system = system_match[0] if system_match else "未知系统"
        browser_match = re.findall(r"(Chrome|Edg|Safari|Firefox|MSIE|Trident)/", ua)
        browser = browser_match[0] if browser_match else "未知浏览器"
    else:
        system = "未知系统"
        browser = "未知浏览器"
    return SysBro(system=system, browser=browser)


if __name__ == "__main__":
    pass
