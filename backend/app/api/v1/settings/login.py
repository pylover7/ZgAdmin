from fastapi import APIRouter

from app.core.dependency import DependUser
from app.models import Success, Fail
from app.settings.config import base_config
from app.settings.log import logger

# 认证接口：管理员获取/修改配置
loginProtectedRouter = APIRouter()


@loginProtectedRouter.get("", summary="获取登录配置")
async def get_login_config():
    """获取QQ和微信登录配置完整信息（管理员接口）"""
    try:
        result = {
            "qq": {
                "app_id": base_config.get_config("login", "qq_app_id", fallback=""),
                "app_key": base_config.get_config("login", "qq_app_key", fallback=""),
                "redirect_uri": base_config.get_config(
                    "login", "qq_redirect_uri", fallback=""
                ),
                "enabled": base_config.get_config(
                    "login", "qq_enabled", fallback="false"
                ).lower()
                == "true",
            },
            "wechat": {
                "app_id": base_config.get_config(
                    "login", "wechat_app_id", fallback=""
                ),
                "app_secret": base_config.get_config(
                    "login", "wechat_app_secret", fallback=""
                ),
                "redirect_uri": base_config.get_config(
                    "login", "wechat_redirect_uri", fallback=""
                ),
                "enabled": base_config.get_config(
                    "login", "wechat_enabled", fallback="false"
                ).lower()
                == "true",
            },
        }
        return Success(msg="获取成功！", data=result)
    except Exception:
        # 如果配置文件不存在，返回默认空配置
        result = {
            "qq": {
                "app_id": "",
                "app_key": "",
                "redirect_uri": "",
                "enabled": False,
            },
            "wechat": {
                "app_id": "",
                "app_secret": "",
                "redirect_uri": "",
                "enabled": False,
            },
        }
        return Success(msg="获取成功！", data=result)


@loginProtectedRouter.post("", summary="更新登录配置")
async def update_login_config(current_user: DependUser, data: dict):
    """更新QQ和微信登录配置"""
    try:
        if "qq" in data:
            qq_config = data["qq"]
            base_config.set_config("login", "qq_app_id", qq_config.get("app_id", ""))
            base_config.set_config(
                "login", "qq_app_key", qq_config.get("app_key", "")
            )
            base_config.set_config(
                "login", "qq_redirect_uri", qq_config.get("redirect_uri", "")
            )
            base_config.set_config(
                "login", "qq_enabled", str(qq_config.get("enabled", False)).lower()
            )

        if "wechat" in data:
            wechat_config = data["wechat"]
            base_config.set_config(
                "login", "wechat_app_id", wechat_config.get("app_id", "")
            )
            base_config.set_config(
                "login", "wechat_app_secret", wechat_config.get("app_secret", "")
            )
            base_config.set_config(
                "login",
                "wechat_redirect_uri",
                wechat_config.get("redirect_uri", ""),
            )
            base_config.set_config(
                "login",
                "wechat_enabled",
                str(wechat_config.get("enabled", False)).lower(),
            )

        await logger.operationInfo(user=current_user.username, msg="更新登录配置")
        return Success(msg="保存成功！")
    except Exception as e:
        return Fail(msg=f"保存失败： {str(e)}")
