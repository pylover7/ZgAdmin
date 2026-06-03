from uuid import UUID

from fastapi import APIRouter, Query
from sqlmodel import and_, col

from app.controllers.logs import loginLoginController
from app.core.dependency import DependUser, SessionDep
from app.models import Success, SuccessExtra
from app.models.logs import LoginLog, LoginLogFilter
from app.settings.log import logger

loginRouter = APIRouter()


@loginRouter.post("/delete")
async def delete_login_logs(session: SessionDep, current_user: DependUser, data: list[UUID]):
    await loginLoginController.delete(session, data)
    await logger.operationInfo(user=current_user.username, msg=f"删除登录日志: {[str(d) for d in data]}")
    return Success(msg="登录日志删除成功！")


@loginRouter.get("/clear")
async def clear_login_logs(session: SessionDep, current_user: DependUser):
    await loginLoginController.delete_all(session)
    await logger.operationError(user=current_user.username, msg="用户清空登录日志")
    return Success(msg="登录日志清空成功！")


@loginRouter.post("/list")
async def get_login_logs(
    session: SessionDep,
    data: LoginLogFilter,
    currentPage: int = Query(1, description="页码"),
    pageSize: int = Query(15, description="每页数量"),
):
    where = []
    if data.username:
        where.append(LoginLog.username == data.username)
    if data.level:
        where.append(LoginLog.level == data.level)
    if data.loginTime and len(data.loginTime) == 2:  # noqa: PLR2004
        where.append(LoginLog.time >= data.loginTime[0])
        where.append(LoginLog.time <= data.loginTime[1])
    where = and_(*where) if len(where) > 0 else None
    order = col(LoginLog.time).desc()
    total, log_objs = await loginLoginController.list(session, currentPage, pageSize, where, order)
    result = []
    for obj in log_objs:
        result.append(await obj.to_dict())
    return SuccessExtra(msg="登录日志查询成功！", data=result, total=total, pageSize=pageSize, currentPage=currentPage)
