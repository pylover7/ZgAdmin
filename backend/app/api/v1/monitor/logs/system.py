from uuid import UUID

from fastapi import APIRouter, Query
from sqlmodel import and_, col

from app.controllers.logs import systemLogController
from app.core.dependency import DependUser, SessionDep
from app.models.base import Success, SuccessExtra
from app.models.logs import SystemLog, SystemLogFilter
from app.settings.log import logger

systemRouter = APIRouter()


@systemRouter.post("/delete")
async def delete_system_logs(
    session: SessionDep,
    current_user: DependUser,
    ids: list[UUID],
):
    await systemLogController.delete(session, ids)
    await logger.operationInfo(user=current_user.username, msg=f"删除系统日志: {[str(i) for i in ids]}")
    return Success(msg="系统日志删除成功！")


@systemRouter.get("/clear")
async def clear_system_logs(
    session: SessionDep,
    current_user: DependUser,
):
    await systemLogController.delete_all(session)
    await logger.operationWarning(user=current_user.username, msg="清空系统日志")
    return Success(msg="系统日志清空成功！")


@systemRouter.post("/list")
async def get_system_logs(
    session: SessionDep,
    data: SystemLogFilter,
    currentPage: int = Query(1, description="页码"),
    pageSize: int = Query(15, description="每页数量"),
):
    where = []
    if data.module:
        where.append(SystemLog.module == data.module)
    if data.operationTime and len(data.operationTime) == 2:  # noqa: PLR2004
        where.append(SystemLog.time >= data.operationTime[0])
        where.append(SystemLog.time <= data.operationTime[1])
    where = and_(*where) if len(where) > 0 else None
    order = col(SystemLog.time).desc()
    total, log_obj = await systemLogController.list(session, currentPage, pageSize, where, order)
    result = []
    for obj in log_obj:
        result.append(await obj.to_dict())
    return SuccessExtra(msg="系统日志查询成功！", data=result, total=total, pageSize=pageSize, currentPage=currentPage)
