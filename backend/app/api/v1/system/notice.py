from uuid import UUID

from fastapi import APIRouter, Query
from sqlmodel import and_, col

from app.controllers.notice import noticeController
from app.core.dependency import DependUser, SessionDep
from app.models import Fail, Success, SuccessExtra
from app.models.notice import Notice, NoticeCreate, NoticeFilter, NoticeUpdate
from app.settings.log import logger

noticeRouter = APIRouter()


@noticeRouter.post("/add", summary="发布通知")
async def add_notice(session: SessionDep, current_user: DependUser, data: NoticeCreate):
    obj = await noticeController.create(session, data)
    # 写入操作日志
    await logger.operationInfo(user=current_user.username, msg=f"发布通知: {obj.title}")
    return Success(msg="通知发布成功！", data=await obj.to_dict())


@noticeRouter.post("/list", summary="通知列表")
async def get_notice_list(
    session: SessionDep,
    data: NoticeFilter,
    currentPage: int = Query(1, description="页码"),
    pageSize: int = Query(15, description="每页数量"),
):
    where = []
    if data.title:
        where.append(col(Notice.title).contains(data.title))
    if data.type is not None:
        where.append(Notice.type == data.type)
    if data.level:
        where.append(Notice.level == data.level)
    if data.status is not None:
        where.append(Notice.status == data.status)
    where_clause = and_(*where) if where else None
    order = col(Notice.created_at).desc()
    total, items = await noticeController.list(session, currentPage, pageSize, where_clause, order)
    result = [await obj.to_dict() for obj in items]
    return SuccessExtra(data=result, total=total, currentPage=currentPage, pageSize=pageSize)


@noticeRouter.post("/update", summary="编辑通知")
async def update_notice(session: SessionDep, current_user: DependUser, data: NoticeUpdate):
    obj = await noticeController.update(session, data.id, data)
    if not obj:
        return Fail(msg="通知不存在")
    await logger.operationInfo(user=current_user.username, msg=f"编辑通知: {obj.title}")
    return Success(msg="通知更新成功！", data=await obj.to_dict())


@noticeRouter.post("/delete", summary="删除通知")
async def delete_notice(session: SessionDep, current_user: DependUser, data: list[UUID]):
    await noticeController.delete(session, data)
    await logger.operationInfo(user=current_user.username, msg=f"删除通知: {[str(d) for d in data]}")
    return Success(msg="通知删除成功！")


@noticeRouter.get("/unread", summary="当前用户未读通知")
async def get_unread_notices(session: SessionDep, current_user: DependUser):
    count = await noticeController.get_unread_count(session, current_user.id)
    items = await noticeController.get_unread_list(session, current_user.id, limit=20)

    # 按 type 分组：0,2 → 通知；1 → 消息
    notify_list = []
    message_list = []
    for item in items:
        d = await item.to_dict()
        if item.type == 1:
            message_list.append(d)
        else:
            notify_list.append(d)

    return Success(data={"count": count, "notify": notify_list, "message": message_list})


@noticeRouter.post("/read", summary="标记单条已读")
async def mark_notice_read(session: SessionDep, current_user: DependUser, data: dict):
    notice_id = data.get("notice_id")
    if not notice_id:
        return Fail(msg="缺少 notice_id")
    await noticeController.mark_as_read(session, UUID(notice_id), current_user.id)
    return Success(msg="标记已读成功")


@noticeRouter.post("/readAll", summary="全部标记已读")
async def mark_all_read(session: SessionDep, current_user: DependUser):
    count = await noticeController.mark_all_as_read(session, current_user.id)
    return Success(msg=f"已标记 {count} 条通知为已读")
