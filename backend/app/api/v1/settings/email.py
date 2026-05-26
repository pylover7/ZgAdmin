"""邮件配置 API"""
from fastapi import APIRouter

from app.core.dependency import DependUser, SessionDep
from app.models.base import Success, Fail
from app.controllers.config import emailConfigController
from app.models.config import EmailConfigUpdate
from app.settings.log import logger

emailProtectedRouter = APIRouter()


@emailProtectedRouter.get("", summary="获取邮件配置")
async def get_email_config(session: SessionDep):
    """获取邮件配置完整信息（管理员接口）"""
    config = emailConfigController.get(session)
    if not config:
        return Fail(msg="邮件配置未初始化")
    data = await config.to_dict()
    data = emailConfigController.mask_sensitive(data)
    return Success(msg="获取成功！", data=data)


@emailProtectedRouter.post("", summary="更新邮件配置")
async def update_email_config(
        session: SessionDep, current_user: DependUser, data: EmailConfigUpdate):
    """更新邮件配置"""
    config = emailConfigController.update(session, data)
    if not config:
        return Fail(msg="邮件配置未初始化")

    await logger.operationInfo(user=current_user.username, msg="更新邮件配置")
    result = await config.to_dict()
    result = emailConfigController.mask_sensitive(result)
    return Success(data=result, msg="保存成功！")
