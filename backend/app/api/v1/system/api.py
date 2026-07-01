from fastapi import APIRouter

from app.controllers.api import apiController
from app.core.dependency import SessionDep
from app.models import Success

apiRouter = APIRouter()


@apiRouter.post("/delete", summary="删除接口")
async def delete_api(session: SessionDep, data: list[str]):
    await apiController.delete(session, data)
    return Success(msg="接口删除成功！")


@apiRouter.get("/all", summary="获取所有接口")
async def api_all(session: SessionDep):
    api_obj = await apiController.all(session)
    result = [await item.to_dict() for item in api_obj]
    return Success(msg="接口列表查询成功！", data=result)


@apiRouter.get("/list", summary="获取接口列表")
async def api_list(session: SessionDep):
    api_obj = await apiController.all(session)
    result = [await item.to_dict() for item in api_obj]
    return Success(msg="接口列表查询成功！", data=result)
