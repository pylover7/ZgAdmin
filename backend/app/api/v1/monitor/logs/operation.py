from fastapi import APIRouter

from app.models import SuccessExtra

operationRouter = APIRouter()


@operationRouter.post("/list")
async def get_operation_logs():
    return SuccessExtra(msg="登录日志查询成功！", data=[], total=0, pageSize=10, currentPage=1)