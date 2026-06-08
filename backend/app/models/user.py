import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, TimestampMixin
from .department import Department
from .link import UserRoleLink

if TYPE_CHECKING:
    from . import Role


class UserBase(BaseModel):
    nickname: str = Field(
        default=None, max_length=30, nullable=True, description="用户昵称", schema_extra={"examples": ["张三"]}
    )
    username: str = Field(
        max_length=20, unique=True, description="用户名称（登录账号）", schema_extra={"examples": ["zhangsan"]}
    )
    email: EmailStr = Field(
        unique=True,
        index=True,
        max_length=255,
        description="邮箱地址",
        schema_extra={"examples": ["zhangsan@example.com"]},
    )
    password: str = Field(
        min_length=8, max_length=256, description="密码", schema_extra={"examples": ["MyP@ssw0rd123"]}
    )
    phone: str = Field(
        default=None,
        max_length=20,
        nullable=True,
        unique=True,
        description="手机号码",
        schema_extra={"examples": ["13800138000"]},
    )
    status: int = Field(default=1, index=True, description="是否激活：0-停用，1-启用", schema_extra={"examples": [1]})
    is_superuser: bool = Field(default=False, description="是否为超级管理员", schema_extra={"examples": [False]})
    sex: int = Field(default=1, description="性别：0-女，1-男", schema_extra={"examples": [1]})
    remark: str = Field(
        default=None, max_length=500, nullable=True, description="备注", schema_extra={"examples": ["前端开发工程师"]}
    )
    department_id: uuid.UUID | None = Field(
        default=None,
        index=True,
        foreign_key="department.id",
        description="所属部门ID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]},
    )
    # QQ登录相关字段
    qq_openid: str | None = Field(
        default=None,
        max_length=100,
        nullable=True,
        unique=True,
        description="QQ OpenID",
        schema_extra={"examples": ["A1B2C3D4E5F6"]},
    )
    qq_unionid: str | None = Field(
        default=None,
        max_length=100,
        nullable=True,
        unique=True,
        description="QQ UnionID",
        schema_extra={"examples": ["U1N2I3O4N5ID"]},
    )
    qq_nickname: str | None = Field(
        default=None, max_length=100, nullable=True, description="QQ昵称", schema_extra={"examples": ["QQ用户"]}
    )
    qq_avatar: str | None = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="QQ头像URL",
        schema_extra={"examples": ["https://q.qlogo.cn/xxx.jpg"]},
    )


class User(UserBase, TimestampMixin, table=True):
    last_login: datetime = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="最后登录时间",
        schema_extra={"examples": ["2026-05-26T10:30:00+00:00"]},
    )
    failed_login_count: int = Field(default=0, description="连续登录失败次数", schema_extra={"examples": [0]})
    locked_until: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="锁定截止时间",
        schema_extra={"examples": ["2026-05-26T11:00:00+00:00"]},
    )
    password_history: list[str] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True), description="最近N次密码hash列表，防止重复使用"
    )
    preferences: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="用户偏好设置",
        schema_extra={"examples": [{"notify_account": True, "notify_system": True, "notify_task": True}]},
    )
    department: Department | None = Relationship(back_populates="users")

    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: str = Field(
        max_length=20, unique=True, description="用户名称（登录账号）", schema_extra={"examples": ["zhangsan"]}
    )
    nickname: str = Field(
        default=None, max_length=30, nullable=True, description="用户昵称", schema_extra={"examples": ["张三"]}
    )
    email: EmailStr = Field(
        unique=True,
        index=True,
        max_length=255,
        description="邮箱地址",
        schema_extra={"examples": ["zhangsan@example.com"]},
    )
    sex: int = Field(default=1, description="性别：0-女，1-男", schema_extra={"examples": [1]})
    phone: str = Field(
        default=None,
        max_length=20,
        nullable=True,
        unique=True,
        description="手机号码",
        schema_extra={"examples": ["13800138000"]},
    )


class UpdatePassword(SQLModel):
    current_password: str = Field(
        min_length=8, max_length=40, description="当前密码", schema_extra={"examples": ["OldP@ssw0rd"]}
    )
    new_password: str = Field(
        min_length=8, max_length=40, description="新密码", schema_extra={"examples": ["NewP@ssw0rd123"]}
    )


class UserFiter(BaseModel):
    username: str | None = Field(default=None, description="用户名（模糊搜索）", schema_extra={"examples": ["zhang"]})
    email: str | None = Field(default=None, description="邮箱（模糊搜索）", schema_extra={"examples": ["example.com"]})
    deptId: str | None = Field(
        default=None, description="部门ID", schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]}
    )


class UserResetPwd(BaseModel):
    newPwd: str = Field(description="新密码", schema_extra={"examples": ["NewP@ssw0rd123"]})


class UpdateStatus(BaseModel):
    status: int = Field(description="用户状态：0-停用，1-启用", schema_extra={"examples": [1]})


class UpdateUserRoles(BaseModel):
    roleIds: list[str] = Field(
        description="角色ID列表", schema_extra={"examples": [["550e8400-e29b-41d4-a716-446655440000"]]}
    )


class UpdateProfile(SQLModel):
    nickname: str | None = Field(
        default=None, max_length=30, description="用户昵称", schema_extra={"examples": ["张三"]}
    )
    email: EmailStr | None = Field(
        default=None, description="邮箱地址", schema_extra={"examples": ["zhangsan@example.com"]}
    )
    phone: str | None = Field(
        default=None, max_length=20, description="手机号码", schema_extra={"examples": ["13800138000"]}
    )
    remark: str | None = Field(
        default=None, max_length=500, description="备注", schema_extra={"examples": ["前端开发工程师"]}
    )


class UpdatePreferences(SQLModel):
    notify_account: bool | None = Field(default=None, description="账户相关变更通知", schema_extra={"examples": [True]})
    notify_system: bool | None = Field(
        default=None, description="系统公告和运维通知", schema_extra={"examples": [True]}
    )
    notify_task: bool | None = Field(default=None, description="任务完成和审批通知", schema_extra={"examples": [True]})
