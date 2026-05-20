from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin


# ─── 通知类型枚举 ───
class NoticeType(SQLModel):
    type: int = Field(
        default=0, description="通知类型：0-系统通知, 1-业务通知, 2-公告"
    )


# ─── 创建 ───
class NoticeCreate(SQLModel):
    title: str = Field(max_length=200, description="通知标题")
    content: str = Field(default="", description="通知内容")
    type: int = Field(default=0, description="通知类型：0-系统, 1-业务, 2-公告")
    level: str = Field(default="info", description="通知级别：info/warning/important")
    status: int = Field(default=0, description="0-草稿, 1-已发布")


# ─── 更新 ───
class NoticeUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    type: int | None = None
    level: str | None = None
    status: int | None = Field(default=None, description="0-草稿, 1-已发布")


# ─── 过滤 ───
class NoticeFilter(SQLModel):
    title: str | None = None
    type: int | None = None
    level: str | None = None
    status: int | None = None


# ─── 通知主表 ───
class Notice(BaseModel, NoticeCreate, TimestampMixin, table=True):
    status: int = Field(default=0, description="0-草稿, 1-已发布")
    creator_id: UUID | None = Field(
        default=None, foreign_key="user.id", description="创建人"
    )
    reads: list["NoticeRead"] = Relationship(back_populates="notice")


# ─── 已读记录表（多对多：通知 ↔ 用户）───
class NoticeRead(BaseModel, TimestampMixin, table=True):
    notice_id: UUID | None = Field(
        default=None, foreign_key="notice.id", primary_key=True
    )
    user_id: UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    notice: Notice | None = Relationship(back_populates="reads")
