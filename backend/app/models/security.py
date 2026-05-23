"""安全策略 & IP 规则模型"""
from uuid import UUID

from sqlmodel import Field, SQLModel

from .base import BaseModel, TimestampMixin


# ─── 安全策略（全局单行配置表） ──────────────────────────────────────────

class SecurityPolicyBase(SQLModel):
    min_password_length: int = Field(default=8, description="最小密码长度")
    require_uppercase: bool = Field(default=True, description="需要大写字母")
    require_lowercase: bool = Field(default=True, description="需要小写字母")
    require_digit: bool = Field(default=True, description="需要数字")
    require_special: bool = Field(default=False, description="需要特殊字符")
    password_history_count: int = Field(default=3, description="历史密码不可重用次数")
    max_login_attempts: int = Field(default=5, description="最大登录失败次数")
    lockout_duration_minutes: int = Field(default=30, description="锁定时长(分钟)")
    captcha_enabled: bool = Field(default=True, description="启用登录验证码")


class SecurityPolicy(SecurityPolicyBase, BaseModel, TimestampMixin, table=True):
    """安全策略配置 — 全局只有一条记录（id 固定为 seed 生成的值）"""


class SecurityPolicyUpdate(SQLModel):
    min_password_length: int | None = Field(default=None, description="最小密码长度")
    require_uppercase: bool | None = Field(default=None, description="需要大写字母")
    require_lowercase: bool | None = Field(default=None, description="需要小写字母")
    require_digit: bool | None = Field(default=None, description="需要数字")
    require_special: bool | None = Field(default=None, description="需要特殊字符")
    password_history_count: int | None = Field(default=None, description="历史密码不可重用次数")
    max_login_attempts: int | None = Field(default=None, description="最大登录失败次数")
    lockout_duration_minutes: int | None = Field(default=None, description="锁定时长(分钟)")
    captcha_enabled: bool | None = Field(default=None, description="启用登录验证码")


# ─── IP 规则（黑白名单） ─────────────────────────────────────────────────

class IPRuleBase(SQLModel):
    ip_cidr: str = Field(max_length=50, description="IP地址或CIDR，如 192.168.1.0/24")
    rule_type: str = Field(max_length=10, description="whitelist 或 blacklist")
    description: str = Field(default="", max_length=200, description="备注")
    is_active: bool = Field(default=True, description="是否启用")


class IPRule(IPRuleBase, BaseModel, TimestampMixin, table=True):
    """IP 黑白名单规则"""


class IPRuleCreate(IPRuleBase):
    pass


class IPRuleUpdate(SQLModel):
    id: UUID
    ip_cidr: str | None = Field(default=None, max_length=50)
    rule_type: str | None = Field(default=None, max_length=10)
    description: str | None = Field(default=None, max_length=200)
    is_active: bool | None = Field(default=None)
