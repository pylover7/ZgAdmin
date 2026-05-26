from fastapi import APIRouter

from app.core.dependency import DependUser, SessionDep
from app.models import Success, Fail
from app.controllers.config import siteConfigController
from app.models.config import SiteConfigUpdate
from app.settings.log import logger

generalProtectedRouter = APIRouter()


@generalProtectedRouter.get("", summary="获取通用设置")
async def get_general_config(session: SessionDep):
    """获取通用设置完整信息（管理员接口）"""
    config = siteConfigController.get(session)
    if not config:
        return Fail(msg="站点配置未初始化")
    data = await config.to_dict()
    data = siteConfigController.mask_sensitive(data)
    return Success(msg="获取成功！", data=data)


@generalProtectedRouter.post("", summary="更新通用设置")
async def update_general_config(
        session: SessionDep, current_user: DependUser, data: SiteConfigUpdate):
    """更新通用设置"""
    config = siteConfigController.update(session, data)
    if not config:
        return Fail(msg="站点配置未初始化")

    await logger.operationInfo(user=current_user.username, msg="更新通用设置")
    result = await config.to_dict()
    result = siteConfigController.mask_sensitive(result)
    return Success(data=result, msg="保存成功！")
