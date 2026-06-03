from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class DepartmentBase(BaseModel):
    name: str = Field(max_length=20, unique=True, description="部门名称", schema_extra={"examples": ["技术部"]})
    parentId: UUID | None = Field(
        default=None,
        nullable=True,
        description="父部门ID（顶级部门为null）",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]},
    )
    sort: int = Field(default=0, description="排序（数字越小越靠前）", schema_extra={"examples": [1]})
    phone: str = Field(
        default=None,
        max_length=20,
        nullable=True,
        description="部门联系电话",
        schema_extra={"examples": ["010-12345678"]},
    )
    principal: str = Field(
        default=None, max_length=20, nullable=True, description="部门负责人", schema_extra={"examples": ["李四"]}
    )
    email: str = Field(
        default=None,
        max_length=255,
        nullable=True,
        description="部门邮箱",
        schema_extra={"examples": ["tech@example.com"]},
    )
    status: int = Field(default=0, description="状态：0-启用，1-停用", schema_extra={"examples": [0]})
    remark: str = Field(
        default=None, max_length=500, nullable=True, description="备注信息", schema_extra={"examples": ["负责产品研发"]}
    )


class Department(DepartmentBase, TimestampMixin, table=True):
    users: list["User"] = Relationship(back_populates="department")


class DepartCreate(DepartmentBase):
    user: list = []  # noqa: RUF012


class DepartUpdate(SQLModel):
    id: UUID = Field(description="部门ID", schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    name: str = Field(description="部门名称", schema_extra={"examples": ["技术部"]})
    parentId: UUID | None = Field(
        default=None, description="父部门ID", schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]}
    )
    sort: int | None = Field(default=None, description="排序", schema_extra={"examples": [1]})
    phone: str | None = Field(default=None, description="部门联系电话", schema_extra={"examples": ["010-12345678"]})
    principal: str | None = Field(default=None, description="部门负责人", schema_extra={"examples": ["李四"]})
    email: str | None = Field(default=None, description="部门邮箱", schema_extra={"examples": ["tech@example.com"]})
    status: int | None = Field(default=None, description="状态：0-启用，1-停用", schema_extra={"examples": [0]})
    remark: str | None = Field(default=None, description="备注信息", schema_extra={"examples": ["负责产品研发"]})
