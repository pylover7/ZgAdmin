import time
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import col, and_, select

from app.core.dependency import SessionDep
from app.controllers.user import userController
from app.models.base import BaseModel, Success, SuccessExtra, Fail
from app.models.user import UserCreate, UserUpdate, User, UserFiter, UserResetPwd, UserAvatar, UpdateStatus, \
    UpdateUserRoles
from app.models.role import Role
from app.settings.log import logger
from app.settings import settings
from app.utils import base_decode
from app.utils.password import get_password_hash, md5_encrypt

userRouter = APIRouter()


@userRouter.post("/add", summary="新增用户")
async def create_user(
        session: SessionDep,
        data: UserCreate,
):
    user = await userController.get_user_by_name(session, data.username)
    if user or (data.username == "admin"):
        raise HTTPException(
            status_code=400,
            detail="该用户已存在！",
        )
    try:
        await userController.create(session, data)
        await logger.systemInfo("系统管理", f"创建用户: {data.username}")
        return Success(msg="用户创建成功！")
    except Exception as e:
        await logger.systemError("系统管理", f"用户创建失败 [{data.username}]: {e}")
        raise HTTPException(status_code=400, detail="用户创建失败！") from e


@userRouter.post("/delete", summary="删除用户")
async def delete_user(
        session: SessionDep,
        data: list[UUID]
):
    try:
        await userController.delete(session, data)
        await logger.systemInfo("系统管理", f"删除用户: {[str(d) for d in data]}")
        return Success(msg="Deleted Successfully")
    except Exception as e:
        await logger.systemError("系统管理", f"用户删除失败: {e}")
        raise HTTPException(status_code=400, detail="用户删除失败！") from e


@userRouter.get("/get", summary="查看用户")
async def get_user(
        session: SessionDep,
        user_id: UUID = Query(..., description="用户ID"),
):
    user_obj = await userController.get(session, user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在！")
    user_dict = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=user_dict)


@userRouter.post("/list", summary="查看用户列表")
async def list_user(
        session: SessionDep,
        data: UserFiter,
        currentPage: int = Query(1, description="页码"),
        pageSize: int = Query(15, description="每页数量"),
):
    where = []
    if data.username:
        where.append(User.username == data.username)
    if data.email:
        where.append(User.email == data.email)
    if data.deptId:
        where.append(User.department_id == data.deptId)
    if len(where) > 0:
        where = and_(*where, )
    else:
        where = None
    order = col(User.id).desc()
    total, user_objs = await userController.list(
        session,
        currentPage,
        pageSize,
        where,
        order,
        options=[selectinload(User.department),
                 selectinload(User.roles)]
    )
    result = []
    for obj in user_objs:
        obj_dict = await obj.to_dict(exclude_fields=["password"])
        obj_dict["roleIds"] = [str(item.id) for item in obj.roles]
        obj_dict["dept"] = await obj.department.to_dict() if obj.department else None
        result.append(obj_dict)
    return SuccessExtra(data=result, total=total,
                        currentPage=currentPage, pageSize=pageSize)

@userRouter.post("/getRolesIds", summary="获取用户角色 id 列表")
async def get_user_roles_id_list(session: SessionDep, data: BaseModel):
    user_obj = await userController.get(session, data.id)
    if user_obj is None:
        return Fail(msg="没有这个用户")
    result = [role.id for role in user_obj.roles]
    return Success(msg="xxx", data=result)


@userRouter.post("/update", summary="更新用户")
async def update_user(
        session: SessionDep,
        data: UserUpdate,
):
    user = await userController.get(session, data.id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")
    if hasattr(data, 'username') and data.username:
        existing = await userController.get_user_by_name(session, data.username)
        if existing and existing.id != data.id:
            raise HTTPException(status_code=400, detail="用户名已存在！")
    del data.username
    await userController.update(session, user.id, data)
    await logger.systemInfo("系统管理", f"更新用户信息: {user.username}")
    return Success(msg="用户信息更新成功！")


@userRouter.post("/updateAvatar", summary="更新用户头像")
async def update_avatar(
        session: SessionDep,
        data: UserAvatar,
):
    user = await userController.get(session, data.id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")
    avatar_name = f"{
        md5_encrypt(
            str(
                user.id))}_{
        time.time_ns()}.{
                    data.avatar.base64.split(';')[0].split('/')[
                        -1]}"
    avatar_path = Path.joinpath(Path(settings.AVATAR_PATH), avatar_name)
    with open(avatar_path, "wb") as f:
        imgData = base_decode(data.avatar.base64.split(",")[1])
        f.write(imgData)
    user.avatar = avatar_name
    session.add(user)
    session.commit()
    return Success(msg="用户头像信息更新成功！")


@userRouter.post("/updateRoles", summary="更新用户角色")
async def update_roles(
        session: SessionDep,
        data: UpdateUserRoles,
):
    user = await userController.get(session, data.id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")
    role_ids = [UUID(rid) for rid in data.roleIds]
    roleList = list(session.exec(select(Role).where(col(Role.id).in_(role_ids))).all())
    user.roles = roleList
    session.add(user)
    session.commit()
    await logger.systemInfo("系统管理", f"更新用户角色: {user.username}")
    return Success(msg="用户角色信息更新成功！")


@userRouter.post("/updateStatus", summary="更新用户状态")
async def update_status(session: SessionDep, data: UpdateStatus):
    user = await userController.get(session, data.id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")
    user.status = data.status
    session.add(user)
    session.commit()
    await logger.systemInfo("系统管理", f"更新用户状态: {user.username} -> {data.status}")
    return Success(msg="用户状态更新成功！")


@userRouter.post("/resetPwd", summary="重置用户密码")
async def reset_pwd(
        session: SessionDep,
        data: UserResetPwd,
):
    user = await userController.get(session, data.id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")
    user.password = get_password_hash(data.newPwd)
    session.add(user)
    session.commit()
    await logger.systemInfo("系统管理", f"重置用户密码: {user.username}")
    return Success(msg="密码重置成功！")
