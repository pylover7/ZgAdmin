from uuid import UUID
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class FileCreate(SQLModel):
    pass


class FileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255, description="文件名")


class FileFilter(SQLModel):
    name: str | None = None
    file_type: str | None = None
    uploader_id: UUID | None = None


class File(BaseModel, TimestampMixin, table=True):
    name: str = Field(max_length=255, description="原始文件名")
    path: str = Field(max_length=500, description="存储相对路径")
    size: int = Field(default=0, description="文件大小(字节)")
    mime_type: str = Field(default="", max_length=100, description="MIME类型(magic检测)")
    file_type: str = Field(default="other", max_length=20, description="文件分类: image/document/video/audio/other")
    extension: str = Field(default="", max_length=20, description="文件扩展名(小写)")
    uploader_id: UUID | None = Field(default=None, foreign_key="user.id", description="上传者")
    uploader: Optional["User"] = Relationship()
