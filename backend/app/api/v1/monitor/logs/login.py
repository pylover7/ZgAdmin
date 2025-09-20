from fastapi import APIRouter

from app.models import SuccessExtra

loginRouter = APIRouter()


@loginRouter.post("/list")
async def get_login_logs():
    return SuccessExtra(msg="登录日志查询成功！", data=[], total=0, pageSize=10, currentPage=1)