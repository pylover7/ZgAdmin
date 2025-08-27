from fastapi import APIRouter

from app.controllers.department import deptController
from app.models import Success, DepartCreate, DepartUpdate
from app.core.dependency import SessionDep

departRouter = APIRouter()


@departRouter.post("/add", summary="添加部门")
async def add_depart(session: SessionDep, data: DepartCreate):
    result = await deptController.create(session, data)
    return Success(msg="部门添加成功！", data=await result.to_dict())


@departRouter.post("/delete", summary="删除部门")
async def delete_depart(session: SessionDep, data: list[str]):
    await deptController.delete(session, data)
    return Success(msg="部门删除成功！")


@departRouter.get("/list", summary="获取部门列表")
async def depart_list(session: SessionDep):
    depart_obj = await deptController.all(session)
    data = [await obj.to_dict() for obj in depart_obj]
    return Success(msg="部门列表查询成功！", data=data)


@departRouter.post("/update", summary="修改部门信息")
async def update_depart(session: SessionDep, data: DepartUpdate):
    result = await deptController.update(session, data.id, data)
    data_dict = await result.to_dict() if result is not None else None
    return Success(msg="部门更新成功！", data=data_dict)
