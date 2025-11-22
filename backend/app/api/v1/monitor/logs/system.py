from operator import and_
from unittest import result
from fastapi import APIRouter, Query
from sqlmodel import col

from app.core.dependency import SessionDep
from app.models.logs import SystemLog, SystemLogFilter
from app.controllers.logs import  systemLogController
from app.models.base import SuccessExtra

systemRouter = APIRouter()


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
    if data.oprationTime and len(data.oprationTime) == 2:
        where.append(SystemLog.time >= data.oprationTime[0])
        where.append(SystemLog.time <= data.oprationTime[1])
    if len(where) > 0:
        where = and_(*where)
    else:
        where = None
    order = col(SystemLog.time).desc()
    total, log_obj = await systemLogController.list(session, currentPage, pageSize, where, order)
    result = []
    for obj in log_obj:
        result.append(await obj.to_dict())
    return SuccessExtra(msg="系统日志查询成功！", data=result, total=total, pageSize=pageSize, currentPage=currentPage)
    