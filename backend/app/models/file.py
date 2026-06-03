from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class FileCreate(SQLModel):
    pass


class FileUpdate(BaseModel):
    name: str | None = Field(
        default=None, max_length=255, description="文件名（重命名）", schema_extra={"examples": ["季度报告.pdf"]}
    )


class FileFilter(SQLModel):
    name: str | None = Field(default=None, description="文件名（模糊搜索）", schema_extra={"examples": ["报告"]})
    file_type: str | None = Field(
        default=None, description="文件分类：image/document/video/audio/other", schema_extra={"examples": ["document"]}
    )
    uploader_id: UUID | None = Field(
        default=None, description="上传者ID", schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]}
    )


class File(BaseModel, TimestampMixin, table=True):
    name: str = Field(max_length=255, description="原始文件名", schema_extra={"examples": ["季度报告.pdf"]})
    path: str = Field(
        max_length=500, description="存储相对路径", schema_extra={"examples": ["uploads/2026/05/a1b2c3d4.pdf"]}
    )
    size: int = Field(default=0, description="文件大小（字节）", schema_extra={"examples": [1048576]})
    mime_type: str = Field(
        default="", max_length=100, description="MIME类型（magic检测）", schema_extra={"examples": ["application/pdf"]}
    )
    file_type: str = Field(
        default="other",
        max_length=20,
        description="文件分类：image/document/video/audio/other",
        schema_extra={"examples": ["document"]},
    )
    extension: str = Field(
        default="", max_length=20, description="文件扩展名（小写）", schema_extra={"examples": ["pdf"]}
    )
    uploader_id: UUID | None = Field(
        default=None,
        foreign_key="user.id",
        description="上传者ID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]},
    )
    uploader: Optional["User"] = Relationship()
