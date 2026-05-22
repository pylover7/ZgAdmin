from fastapi import APIRouter

from app.models import Success, Fail
from app.settings.config import base_config

# 认证接口：管理员获取/修改配置
generalProtectedRouter = APIRouter()


@generalProtectedRouter.get("", summary="获取通用设置")
async def get_general_config():
    """获取通用设置完整信息（管理员接口）"""
    try:
        result = {
            "site_name": base_config.get_config("general", "site_name", fallback="ZgAdmin"),
            "site_desc": base_config.get_config("general", "site_desc", fallback="一个开源的在线工具箱"),
            "logo": base_config.get_config("general", "logo", fallback=""),
            "default_lang": base_config.get_config("general", "default_lang", fallback="zh-CN"),
            "enable_email": base_config.get_config("general", "enable_email", fallback="false").lower() == "true",
            "copyright": base_config.get_config("general", "copyright", fallback=""),
            "icp": base_config.get_config("general", "icp", fallback=""),
        }
        return Success(msg="获取成功！", data=result)
    except Exception:
        result = {
            "site_name": "ZgAdmin",
            "site_desc": "一个开源的在线工具箱",
            "logo": "",
            "default_lang": "zh-CN",
            "enable_email": False,
            "copyright": "",
            "icp": "",
        }
        return Success(msg="获取成功！", data=result)


@generalProtectedRouter.post("", summary="更新通用设置")
async def update_general_config(data: dict):
    """更新通用设置"""
    try:
        if "site_name" in data:
            base_config.set_config("general", "site_name", str(data["site_name"]))
        if "site_desc" in data:
            base_config.set_config("general", "site_desc", str(data["site_desc"]))
        if "logo" in data:
            base_config.set_config("general", "logo", str(data["logo"]))
        if "default_lang" in data:
            base_config.set_config("general", "default_lang", str(data["default_lang"]))
        if "enable_email" in data:
            base_config.set_config("general", "enable_email", str(data["enable_email"]).lower())
        if "copyright" in data:
            base_config.set_config("general", "copyright", str(data["copyright"]))
        if "icp" in data:
            base_config.set_config("general", "icp", str(data["icp"]))

        return Success(msg="保存成功！")
    except Exception as e:
        return Fail(msg=f"保存失败：{str(e)}")
