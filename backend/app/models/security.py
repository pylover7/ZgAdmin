"""安全策略 & IP 规则模型"""

from typing import ClassVar
from uuid import UUID

from sqlmodel import Field, SQLModel

from .base import BaseModel, TimestampMixin

# ─── 安全策略（全局单行配置表） ──────────────────────────────────────────


class SecurityPolicyBase(SQLModel):
    min_password_length: int = Field(default=8, description="最小密码长度（6-32）", schema_extra={"examples": [8]})
    require_uppercase: bool = Field(default=True, description="密码需要大写字母", schema_extra={"examples": [True]})
    require_lowercase: bool = Field(default=True, description="密码需要小写字母", schema_extra={"examples": [True]})
    require_digit: bool = Field(default=True, description="密码需要数字", schema_extra={"examples": [True]})
    require_special: bool = Field(default=False, description="密码需要特殊字符", schema_extra={"examples": [False]})
    password_history_count: int = Field(
        default=3, description="历史密码不可重用次数（0=不检查，最大24）", schema_extra={"examples": [3]}
    )
    max_login_attempts: int = Field(default=5, description="最大登录失败次数（3-20）", schema_extra={"examples": [5]})
    lockout_duration_minutes: int = Field(
        default=30, description="账户锁定时长（分钟，5-1440）", schema_extra={"examples": [30]}
    )
    captcha_enabled: bool = Field(default=True, description="启用登录验证码", schema_extra={"examples": [True]})


class SecurityPolicy(SecurityPolicyBase, BaseModel, TimestampMixin, table=True):
    """安全策略配置 — 全局只有一条记录（id 固定为 seed 生成的值）"""

    SENSITIVE_FIELDS: ClassVar[list[str]] = []


class SecurityPolicyUpdate(SQLModel):
    min_password_length: int | None = Field(
        default=None, description="最小密码长度（6-32）", schema_extra={"examples": [10]}
    )
    require_uppercase: bool | None = Field(
        default=None, description="密码需要大写字母", schema_extra={"examples": [True]}
    )
    require_lowercase: bool | None = Field(
        default=None, description="密码需要小写字母", schema_extra={"examples": [True]}
    )
    require_digit: bool | None = Field(default=None, description="密码需要数字", schema_extra={"examples": [True]})
    require_special: bool | None = Field(
        default=None, description="密码需要特殊字符", schema_extra={"examples": [True]}
    )
    password_history_count: int | None = Field(
        default=None, description="历史密码不可重用次数（0=不检查，最大24）", schema_extra={"examples": [5]}
    )
    max_login_attempts: int | None = Field(
        default=None, description="最大登录失败次数（3-20）", schema_extra={"examples": [3]}
    )
    lockout_duration_minutes: int | None = Field(
        default=None, description="账户锁定时长（分钟，5-1440）", schema_extra={"examples": [60]}
    )
    captcha_enabled: bool | None = Field(default=None, description="启用登录验证码", schema_extra={"examples": [True]})


# ─── IP 规则（黑白名单） ─────────────────────────────────────────────────


class IPRuleBase(SQLModel):
    ip_cidr: str = Field(
        max_length=50, description="IP地址或CIDR，如 192.168.1.0/24", schema_extra={"examples": ["192.168.1.0/24"]}
    )
    rule_type: str = Field(
        max_length=10,
        description="规则类型：whitelist（白名单）/ blacklist（黑名单）",
        schema_extra={"examples": ["whitelist"]},
    )
    description: str = Field(
        default="", max_length=200, description="规则备注说明", schema_extra={"examples": ["内网白名单"]}
    )
    is_active: bool = Field(default=True, description="是否启用", schema_extra={"examples": [True]})


class IPRule(IPRuleBase, BaseModel, TimestampMixin, table=True):
    """IP 黑白名单规则"""


class IPRuleCreate(IPRuleBase):
    pass


class IPRuleUpdate(SQLModel):
    id: UUID = Field(description="IP规则ID", schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    ip_cidr: str | None = Field(
        default=None, max_length=50, description="IP地址或CIDR", schema_extra={"examples": ["10.0.0.0/8"]}
    )
    rule_type: str | None = Field(
        default=None,
        max_length=10,
        description="规则类型：whitelist/blacklist",
        schema_extra={"examples": ["blacklist"]},
    )
    description: str | None = Field(
        default=None, max_length=200, description="规则备注说明", schema_extra={"examples": ["恶意IP段"]}
    )
    is_active: bool | None = Field(default=None, description="是否启用", schema_extra={"examples": [True]})
