from uuid import UUID

from fastapi import APIRouter

from app.controllers.department import deptController
from app.core.dependency import SessionDep
from app.models import DepartCreate, DepartUpdate, Success
from app.models.logs import LogModule
from app.settings.log import logger

departRouter = APIRouter()


@departRouter.post("/add", summary="添加部门")
async def add_depart(session: SessionDep, data: DepartCreate):
    try:
        result = await deptController.create(session, data)
        await logger.systemInfo(LogModule.SYSTEM_MANAGEMENT, f"添加部门: {data.name}")
        return Success(msg="部门添加成功！", data=await result.to_dict())
    except Exception as e:
        await logger.systemError(LogModule.SYSTEM_MANAGEMENT, f"部门添加失败 [{data.name}]: {e}")
        if "IntegrityError" in str(e.__class__.__name__):
            return Success(success=False, msg="部门名称已存在，请更换后重试！")


@departRouter.post("/delete", summary="删除部门")
async def delete_depart(session: SessionDep, data: list[UUID]):
    await deptController.delete(session, data)
    await logger.systemInfo(LogModule.SYSTEM_MANAGEMENT, f"删除部门: {data}")
    return Success(msg="部门删除成功！")


@departRouter.get("/list", summary="获取部门列表")
async def depart_list(session: SessionDep):
    depart_obj = await deptController.all(session)
    data = [await obj.to_dict() for obj in depart_obj]
    return Success(msg="部门列表查询成功！", data=data)


@departRouter.post("/update", summary="修改部门信息")
async def update_depart(session: SessionDep, data: DepartUpdate):
    if str(data.id) == str(data.parentId):
        return Success(success=False, msg="上级部门不能选择自己，请更换后重试！")
    result = await deptController.update(session, data.id, data)
    data_dict = await result.to_dict() if result is not None else None
    await logger.systemInfo(LogModule.SYSTEM_MANAGEMENT, f"修改部门信息: {data.name}")
    return Success(msg="部门更新成功！", data=data_dict)
