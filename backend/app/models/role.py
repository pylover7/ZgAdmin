from typing import TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin
from .link import UserRoleLink, RoleMenuLink, RoleApiLink


if TYPE_CHECKING:
    from . import Menu, Api, User


class RoleCreate(SQLModel):
    name: str = Field(
        max_length=20, unique=True,
        description="角色名称",
        schema_extra={"examples": ["编辑"]})
    code: str = Field(
        max_length=20, unique=True,
        description="角色编码",
        schema_extra={"examples": ["editor"]})
    status: int = Field(
        default=0,
        description="状态：0-启用，1-停用",
        schema_extra={"examples": [0]})
    remark: str = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="角色描述",
        schema_extra={"examples": ["内容编辑人员，可编辑和发布文章"]})


class Role(BaseModel, RoleCreate, TimestampMixin, table=True):
    menus: list["Menu"] = Relationship(
        back_populates="roles",
        link_model=RoleMenuLink)
    apis: list["Api"] = Relationship(
        back_populates="roles",
        link_model=RoleApiLink)
    users: list["User"] = Relationship(
        back_populates="roles",
        link_model=UserRoleLink)


class RoleUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        description="角色名称",
        schema_extra={"examples": ["高级编辑"]})
    code: str | None = Field(
        default=None,
        description="角色编码",
        schema_extra={"examples": ["senior_editor"]})
    remark: str | None = Field(
        default=None,
        description="角色描述",
        schema_extra={"examples": ["高级编辑人员，可审核和发布文章"]})


class UpdateRoleStatus(BaseModel):
    status: int = Field(
        description="状态：0-启用，1-停用",
        schema_extra={"examples": [0]})


class RoleFilter(SQLModel):
    name: str | None = Field(
        default=None,
        description="角色名称（模糊搜索）",
        schema_extra={"examples": ["编辑"]})
    code: str | None = Field(
        default=None,
        description="角色编码（模糊搜索）",
        schema_extra={"examples": ["editor"]})
    status: str | None = Field(
        default=None,
        description="状态：0-启用，1-停用",
        schema_extra={"examples": ["0"]})


class UpdateRoleAuth(BaseModel):
    id: UUID = Field(
        description="角色ID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    menuIds: list[UUID] = Field(
        description="菜单ID列表",
        schema_extra={"examples": [["550e8400-e29b-41d4-a716-446655440001"]]})
    apiIds: list[UUID] = Field(
        default=[],
        description="API权限ID列表",
        schema_extra={"examples": [["550e8400-e29b-41d4-a716-446655440002"]]})
