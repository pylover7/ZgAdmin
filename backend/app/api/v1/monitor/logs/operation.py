from uuid import UUID

from fastapi import APIRouter, Query
from sqlmodel import and_, col

from app.controllers.logs import operationLogController
from app.core.dependency import DependUser, SessionDep
from app.models import SuccessExtra
from app.models.base import Success
from app.models.logs import OperationLog, OperationLogFilter
from app.settings.log import logger

operationRouter = APIRouter()


@operationRouter.post("/delete")
async def delete_operation_logs(
    session: SessionDep,
    current_user: DependUser,
    data: list[UUID],
):
    await operationLogController.delete(session, data)
    await logger.operationInfo(user=current_user.username, msg=f"删除操作日志: {[str(d) for d in data]}")
    return Success(msg="操作日志删除成功！")


@operationRouter.get("/clear")
async def clear_operation_logs(
    session: SessionDep,
    current_user: DependUser,
):
    await operationLogController.delete_all(session)
    await logger.operationWarning(user=current_user.username, msg="清空操作日志")
    return Success(msg="操作日志清空成功！")


@operationRouter.post("/list")
async def get_operation_logs(
    session: SessionDep,
    data: OperationLogFilter,
    currentPage: int = Query(1, description="页码"),
    pageSize: int = Query(15, description="每页数量"),
):
    where = []
    if len(data.level) > 0:
        where.append(col(OperationLog.level).in_(data.level))
    if data.operationTime and len(data.operationTime) == 2:  # noqa: PLR2004
        where.append(OperationLog.time >= data.operationTime[0])
        where.append(OperationLog.time <= data.operationTime[1])
    where = and_(*where) if len(where) > 0 else None
    order = col(OperationLog.time).desc()
    total, log_objs = await operationLogController.list(session, currentPage, pageSize, where, order)
    result = []
    for obj in log_objs:
        result.append(await obj.to_dict())
    return SuccessExtra(msg="登录日志查询成功！", data=result, total=total, pageSize=pageSize, currentPage=currentPage)
