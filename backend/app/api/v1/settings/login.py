from fastapi import APIRouter

from app.controllers.config import oauthConfigController
from app.core.dependency import DependUser, SessionDep
from app.models import Fail, Success
from app.models.config import OAuthConfigUpdate
from app.settings.log import logger

loginProtectedRouter = APIRouter()


@loginProtectedRouter.get("", summary="获取登录配置")
async def get_login_config(session: SessionDep):
    """获取QQ和微信登录配置完整信息（管理员接口）"""
    config = oauthConfigController.get(session)
    if not config:
        return Fail(msg="OAuth配置未初始化")
    data = await config.to_dict()
    data = oauthConfigController.mask_sensitive(data)
    return Success(msg="获取成功！", data=data)


@loginProtectedRouter.post("", summary="更新登录配置")
async def update_login_config(session: SessionDep, current_user: DependUser, data: OAuthConfigUpdate):
    """更新QQ和微信登录配置"""
    config = oauthConfigController.update(session, data)
    if not config:
        return Fail(msg="OAuth配置未初始化")

    await logger.operationInfo(user=current_user.username, msg="更新登录配置")
    result = await config.to_dict()
    result = oauthConfigController.mask_sensitive(result)
    return Success(data=result, msg="保存成功！")
