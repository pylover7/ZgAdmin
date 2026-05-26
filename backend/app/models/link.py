from uuid import UUID

from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Uuid
from sqlmodel import SQLModel, Field


class UserRoleLink(SQLModel, table=True):
    user_id: UUID | None = Field(
        default=None,
        sa_column=Column(Uuid, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
        description="用户id")
    role_id: UUID | None = Field(
        default=None,
        sa_column=Column(Uuid, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
        description="角色id")


class RoleMenuLink(SQLModel, table=True):
    role_id: UUID | None = Field(
        default=None,
        sa_column=Column(Uuid, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
        description="角色id")
    menu_id: UUID | None = Field(
        default=None,
        sa_column=Column(Uuid, ForeignKey("menu.id", ondelete="CASCADE"), primary_key=True),
        description="菜单id")


class RoleApiLink(SQLModel, table=True):
    role_id: UUID | None = Field(
        default=None,
        sa_column=Column(Uuid, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
        description="角色id")
    api_id: UUID | None = Field(
        default=None,
        sa_column=Column(Uuid, ForeignKey("api.id", ondelete="CASCADE"), primary_key=True),
        description="接口id")
