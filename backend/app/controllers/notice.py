from uuid import UUID

from sqlmodel import Session, select, func, col

from app.core.crud import CRUDBase
from app.models.notice import Notice, NoticeCreate, NoticeUpdate, NoticeRead


class NoticeController(CRUDBase[Notice, NoticeCreate, NoticeUpdate]):
    def __init__(self):
        super().__init__(Notice)

    async def get_unread_count(self, session: Session, user_id: UUID) -> int:
        """获取用户未读通知数量"""
        # 已读通知 ID 集合
        read_ids = select(NoticeRead.notice_id).where(
            NoticeRead.user_id == user_id
        )
        # 已发布通知中未读的数量
        count_stmt = (
            select(func.count())
            .select_from(Notice)
            .where(Notice.status == 1)
            .where(col(Notice.id).not_in(read_ids))
        )
        return session.exec(count_stmt).one()

    async def get_unread_list(
        self, session: Session, user_id: UUID, limit: int = 10
    ) -> list[Notice]:
        """获取用户未读通知列表"""
        read_ids = select(NoticeRead.notice_id).where(
            NoticeRead.user_id == user_id
        )
        stmt = (
            select(Notice)
            .where(Notice.status == 1)
            .where(col(Notice.id).not_in(read_ids))
            .order_by(col(Notice.created_at).desc())
            .limit(limit)
        )
        return list(session.exec(stmt).all())

    async def mark_as_read(
        self, session: Session, notice_id: UUID, user_id: UUID
    ) -> bool:
        """标记单条已读"""
        existing = session.exec(
            select(NoticeRead).where(
                NoticeRead.notice_id == notice_id,
                NoticeRead.user_id == user_id,
            )
        ).first()
        if existing:
            return False
        read = NoticeRead(notice_id=notice_id, user_id=user_id)
        session.add(read)
        session.commit()
        return True

    async def mark_all_as_read(self, session: Session, user_id: UUID) -> int:
        """标记全部已读，返回标记数量"""
        read_ids = select(NoticeRead.notice_id).where(
            NoticeRead.user_id == user_id
        )
        unread_stmt = (
            select(Notice.id)
            .where(Notice.status == 1)
            .where(col(Notice.id).not_in(read_ids))
        )
        unread_ids = list(session.exec(unread_stmt).all())
        count = 0
        for nid in unread_ids:
            session.add(NoticeRead(notice_id=nid, user_id=user_id))
            count += 1
        session.commit()
        return count


noticeController = NoticeController()
