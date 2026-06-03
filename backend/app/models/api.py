from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from .base import BaseModel, TimestampMixin
from .enums import MethodType
from .link import RoleApiLink

if TYPE_CHECKING:
    from app.models import Role


class Api(BaseModel, TimestampMixin, table=True):
    path: str = Field(max_length=100, description="API路径", schema_extra={"examples": ["/api/v1/system/notice/list"]})
    method: MethodType = Field("GET", description="请求方法：GET/POST/PUT/DELETE", schema_extra={"examples": ["POST"]})
    summary: str = Field(max_length=500, description="接口简介", schema_extra={"examples": ["获取通知列表"]})
    tags: str = Field(max_length=100, description="API标签/分组", schema_extra={"examples": ["通知管理"]})

    roles: list["Role"] = Relationship(back_populates="apis", link_model=RoleApiLink)


class ApiCreate:
    pass


class ApiUpdate:
    pass
