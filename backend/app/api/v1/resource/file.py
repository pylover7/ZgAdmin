import os
from uuid import UUID

from fastapi import APIRouter, Query, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import selectinload
from sqlmodel import and_, col

from app.controllers.file import fileController
from app.core.dependency import DependUser, SessionDep
from app.models import Fail, Success, SuccessExtra
from app.models.file import File, FileFilter, FileUpdate
from app.settings import settings
from app.settings.log import logger
from app.utils.file_upload import format_file_size
from app.utils.signed_url import generate_signed_url

fileRouter = APIRouter()


@fileRouter.post("/upload", summary="上传单个文件")
async def upload_file(
    session: SessionDep,
    current_user: DependUser,
    file: UploadFile = FastAPIFile(..., description="上传文件"),
):
    if not file.filename:
        return Fail(msg="文件名不能为空")
    content = await file.read()
    result = await fileController.create_from_upload(
        session=session,
        filename=file.filename,
        file_content=content,
        uploader_id=current_user.id,
    )
    if isinstance(result, tuple):
        _, err = result
        return Fail(msg=err)
    await logger.operationInfo(
        user=current_user.username, msg=f"上传文件: {result.name}"
    )
    data = await result.to_dict()
    data["uploader_name"] = current_user.nickname or current_user.username
    return Success(msg="上传成功", data=data)


@fileRouter.post("/upload-batch", summary="批量上传文件")
async def upload_batch(
    session: SessionDep,
    current_user: DependUser,
    files: list[UploadFile] = FastAPIFile(..., description="上传文件列表"),
):
    success_list = []
    fail_list = []
    for file in files:
        if not file.filename:
            fail_list.append({"filename": "未知文件", "reason": "文件名不能为空"})
            continue
        content = await file.read()
        result = await fileController.create_from_upload(
            session=session,
            filename=file.filename,
            file_content=content,
            uploader_id=current_user.id,
        )
        if isinstance(result, tuple):
            _, err = result
            fail_list.append({"filename": file.filename, "reason": err})
        else:
            data = await result.to_dict()
            data["uploader_name"] = current_user.nickname or current_user.username
            success_list.append(data)
    return Success(
        msg=f"上传完成: {len(success_list)}个成功, {len(fail_list)}个失败",
        data={"success": success_list, "fail": fail_list},
    )


@fileRouter.post("/list", summary="文件列表")
async def get_file_list(
    session: SessionDep,
    data: FileFilter,
    currentPage: int = Query(1, description="页码"),
    pageSize: int = Query(15, description="每页数量"),
):
    where = []
    if data.name:
        where.append(col(File.name).contains(data.name))
    if data.file_type:
        where.append(File.file_type == data.file_type)
    if data.uploader_id:
        where.append(File.uploader_id == data.uploader_id)
    where_clause = and_(*where) if where else None
    order = col(File.created_at).desc()
    options = [selectinload(File.uploader)]
    total, items = await fileController.list(
        session, currentPage, pageSize, where_clause, order, options
    )
    result = []
    for obj in items:
        d = await obj.to_dict()
        d["uploader_name"] = (
            obj.uploader.nickname or obj.uploader.username
            if obj.uploader
            else ""
        )
        d["size_display"] = format_file_size(obj.size)
        result.append(d)
    return SuccessExtra(
        data=result, total=total, currentPage=currentPage, pageSize=pageSize
    )


@fileRouter.post("/update", summary="重命名文件")
async def update_file(session: SessionDep, data: FileUpdate):
    obj = await fileController.update(session, data.id, data)
    if not obj:
        return Fail(msg="文件不存在")
    return Success(msg="重命名成功", data=await obj.to_dict())


@fileRouter.post("/delete", summary="删除文件")
async def delete_file(session: SessionDep, data: list[UUID]):
    success, failed = await fileController.delete_files(session, data)
    return Success(msg=f"删除完成: {success}个成功, {failed}个失败")


@fileRouter.get("/preview/{file_id}", summary="预览文件（需认证）")
async def preview_file(
    file_id: UUID,
    session: SessionDep,
    _current_user: DependUser,
):
    file_obj = session.get(File, file_id)
    if not file_obj:
        return Fail(msg="文件不存在")
    abs_path = f"{settings.STATIC_PATH}/{file_obj.path}"
    if not os.path.exists(abs_path):
        return Fail(msg="文件已丢失")
    return FileResponse(
        path=abs_path,
        media_type=file_obj.mime_type,
        filename=file_obj.name,
    )


@fileRouter.get("/sign-url/{file_id}", summary="获取文件下载签名URL")
async def get_sign_url(
    file_id: UUID,
    session: SessionDep,
    _current_user: DependUser,
):
    file_obj = session.get(File, file_id)
    if not file_obj:
        return Fail(msg="文件不存在")
    signed_url = generate_signed_url(file_id)
    return Success(data={"url": signed_url})


@fileRouter.get("/stats", summary="存储统计")
async def get_storage_stats(session: SessionDep, _current_user: DependUser):
    stats = await fileController.get_storage_stats(session)
    stats["total_size_display"] = format_file_size(stats["total_size"])
    for item in stats["type_stats"]:
        item["size_display"] = format_file_size(item["size"])
    return Success(data=stats)
