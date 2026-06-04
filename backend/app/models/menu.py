from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin
from .link import RoleMenuLink

if TYPE_CHECKING:
    from app.models import Role


class MenuCreate(SQLModel):
    parentId: UUID | None = Field(
        default=None,
        nullable=True,
        description="父菜单ID（顶级菜单为null）",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]},
    )
    menuType: int = Field(
        default=0, description="菜单类型：0-菜单，1-iframe，2-外链，3-按钮", schema_extra={"examples": [0]}
    )
    title: str = Field(
        max_length=50, description="菜单名称（i18n键名或直接文字）", schema_extra={"examples": ["menus.notice"]}
    )
    name: str = Field(max_length=50, description="路由名称（必须唯一）", schema_extra={"examples": ["Notice"]})
    path: str = Field(max_length=100, description="菜单路径", schema_extra={"examples": ["/system/notice"]})
    component: str = Field(
        max_length=100, nullable=True, description="前端组件路径", schema_extra={"examples": ["system/notice/index"]}
    )
    rank: int = Field(default=1, description="排序（数字越小越靠前）", schema_extra={"examples": [1]})
    redirect: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="重定向路径",
        schema_extra={"examples": ["/system/notice/list"]},
    )
    icon: str = Field(
        default=None, max_length=100, nullable=True, description="菜单图标", schema_extra={"examples": ["ep:bell"]}
    )
    extraIcon: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="右侧额外图标",
        schema_extra={"examples": ["ep:setting"]},
    )
    transitionName: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="当前页面过渡动画名称",
        schema_extra={"examples": ["fade"]},
    )
    enterTransition: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="进入动画名称",
        schema_extra={"examples": ["slide-right"]},
    )
    leaveTransition: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="离开动画名称",
        schema_extra={"examples": ["slide-left"]},
    )
    dynamicLevel: int = Field(default=1, description="显示在标签页的最大数量", schema_extra={"examples": [1]})
    activePath: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="菜单激活路径",
        schema_extra={"examples": ["/system/notice"]},
    )
    auths: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="权限标识",
        schema_extra={"examples": ["system:notice:list"]},
    )
    frameSrc: str = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="iframe嵌入地址",
        schema_extra={"examples": ["https://example.com/embed"]},
    )
    frameLoading: bool = Field(default=True, description="iframe加载动画", schema_extra={"examples": [True]})
    keepAlive: bool = Field(default=False, description="缓存页面（keep-alive）", schema_extra={"examples": [False]})
    hiddenTag: bool = Field(default=False, description="是否隐藏标签页", schema_extra={"examples": [False]})
    fixedTag: bool = Field(default=False, description="是否固定标签页", schema_extra={"examples": [False]})
    showLink: bool = Field(default=True, description="是否在菜单中显示", schema_extra={"examples": [True]})
    showParent: bool = Field(default=False, description="是否显示父菜单", schema_extra={"examples": [False]})


class MenuUpdate(MenuCreate, BaseModel):
    pass


class Menu(MenuUpdate, TimestampMixin, table=True):
    roles: list["Role"] = Relationship(back_populates="menus", link_model=RoleMenuLink)
