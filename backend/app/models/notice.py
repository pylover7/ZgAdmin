from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin


# ─── 通知类型枚举 ───
class NoticeType(SQLModel):
    type: int = Field(
        default=0,
        description="通知类型：0-系统通知, 1-业务通知, 2-公告",
        schema_extra={"examples": [0]})


# ─── 创建 ───
class NoticeCreate(SQLModel):
    title: str = Field(
        max_length=200,
        description="通知标题",
        schema_extra={"examples": ["系统维护通知"]})
    content: str = Field(
        default="",
        description="通知内容",
        schema_extra={"examples": ["系统将于今晚 22:00 进行维护升级"]})
    type: int = Field(
        default=0,
        description="通知类型：0-系统通知, 1-业务通知, 2-公告",
        schema_extra={"examples": [0]})
    level: str = Field(
        default="info",
        description="通知级别：info/warning/important",
        schema_extra={"examples": ["info"]})
    status: int = Field(
        default=0,
        description="状态：0-草稿, 1-已发布",
        schema_extra={"examples": [1]})


# ─── 更新 ───
class NoticeUpdate(BaseModel):
    title: str | None = Field(
        default=None, max_length=200,
        description="通知标题",
        schema_extra={"examples": ["系统维护通知（已更新）"]})
    content: str | None = Field(
        default=None,
        description="通知内容",
        schema_extra={"examples": ["维护时间调整为 23:00"]})
    type: int | None = Field(
        default=None,
        description="通知类型：0-系统通知, 1-业务通知, 2-公告",
        schema_extra={"examples": [0]})
    level: str | None = Field(
        default=None,
        description="通知级别：info/warning/important",
        schema_extra={"examples": ["warning"]})
    status: int | None = Field(
        default=None,
        description="状态：0-草稿, 1-已发布",
        schema_extra={"examples": [1]})


# ─── 过滤 ───
class NoticeFilter(SQLModel):
    title: str | None = Field(
        default=None,
        description="通知标题（模糊搜索）",
        schema_extra={"examples": ["维护"]})
    type: int | None = Field(
        default=None,
        description="通知类型：0-系统通知, 1-业务通知, 2-公告",
        schema_extra={"examples": [0]})
    level: str | None = Field(
        default=None,
        description="通知级别：info/warning/important",
        schema_extra={"examples": ["info"]})
    status: int | None = Field(
        default=None,
        description="状态：0-草稿, 1-已发布",
        schema_extra={"examples": [1]})


# ─── 通知主表 ───
class Notice(BaseModel, NoticeCreate, TimestampMixin, table=True):
    status: int = Field(
        default=0,
        description="状态：0-草稿, 1-已发布",
        schema_extra={"examples": [1]})
    creator_id: UUID | None = Field(
        default=None, foreign_key="user.id",
        description="创建人ID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    reads: list["NoticeRead"] = Relationship(back_populates="notice")


# ─── 已读记录表（多对多：通知 ↔ 用户）───
class NoticeRead(BaseModel, TimestampMixin, table=True):
    notice_id: UUID | None = Field(
        default=None, foreign_key="notice.id", primary_key=True,
        description="通知ID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    user_id: UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True,
        description="用户ID",
        schema_extra={"examples": ["660e8400-e29b-41d4-a716-446655440001"]})
    notice: Notice | None = Relationship(back_populates="reads")
