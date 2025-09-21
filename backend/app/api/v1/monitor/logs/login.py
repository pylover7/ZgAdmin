from fastapi import APIRouter, Query
from sqlmodel import Session, and_, col

from app.models import SuccessExtra
from app.controllers.logs import loginLoginController
from app.core.dependency import SessionDep
from app.models.logs import LoginLogFilter, LoginLog
from app.utils.localTime import convert_utc_to_local_time

loginRouter = APIRouter()


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
      if data.loginTime and len(data.loginTime) == 2:
          where.append(LoginLog.time >= data.loginTime[0])
          where.append(LoginLog.time <= data.loginTime[1])
      if len(where) > 0:
        where = and_(*where, )
      else:
          where = None
      order = col(LoginLog.time).desc()
      total, log_objs = await loginLoginController.list(session, currentPage, pageSize, where, order)
      result = []
      for obj in log_objs:
          result.append(await obj.to_dict())
      return SuccessExtra(msg="登录日志查询成功！", data=result, total=total, pageSize=pageSize, currentPage=currentPage)