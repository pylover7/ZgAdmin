from uuid import UUID
from fastapi import APIRouter, Query
from sqlmodel import and_, col

from app.core.dependency import SessionDep
from app.models import SuccessExtra
from app.models.logs import OperationLogFilter, OperationLog
from app.controllers.logs import operationLogController
from app.models.base import Success

operationRouter = APIRouter()


@operationRouter.post("/delete")
async def delete_operation_logs(
    session: SessionDep,
    data: list[UUID],
):
    await operationLogController.delete(session, data)
    return Success(msg="操作日志删除成功！")


@operationRouter.get("/clear")
async def clear_operation_logs(
    session: SessionDep,  # type: ignore
):
    await operationLogController.delete_all(session)
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
    if data.operationTime and len(data.operationTime) == 2:
        where.append(OperationLog.time >= data.operationTime[0])
        where.append(OperationLog.time <= data.operationTime[1])
    if len(where) > 0:
        where = and_(*where, )
    else:
        where = None
    order = col(OperationLog.time).desc()
    total, log_objs = await operationLogController.list(
        session,
        currentPage,
        pageSize,
        where,
        order
    )
    result = []
    for obj in log_objs:
        result.append(await obj.to_dict())
    return SuccessExtra(
        msg="登录日志查询成功！",
        data=result,
        total=total,
        pageSize=pageSize,
        currentPage=currentPage
    )
