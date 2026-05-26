"""运行时可修改的配置表 — 全局单行表模式（与 SecurityPolicy 同模式）"""
from typing import ClassVar

from sqlmodel import Field, SQLModel

from .base import BaseModel, TimestampMixin


# ─── 站点配置 ────────────────────────────────────────────────────────────

class SiteConfigBase(SQLModel):
    site_name: str = Field(default="ZgAdmin", max_length=100, description="站点名称")
    site_desc: str = Field(
        default="一个开源的在线工具箱", max_length=500, description="站点描述")
    logo: str = Field(default="", max_length=500, description="Logo URL")
    default_lang: str = Field(default="zh-CN", max_length=10, description="默认语言")
    enable_email: bool = Field(default=False, description="启用邮件功能")
    copyright: str = Field(default="", max_length=200, description="版权信息")
    icp: str = Field(default="", max_length=100, description="ICP 备案号")


class SiteConfig(SiteConfigBase, BaseModel, TimestampMixin, table=True):
    """站点配置 — 全局只有一条记录"""

    SENSITIVE_FIELDS: ClassVar[list[str]] = []


class SiteConfigUpdate(SQLModel):
    site_name: str | None = Field(default=None, max_length=100)
    site_desc: str | None = Field(default=None, max_length=500)
    logo: str | None = Field(default=None, max_length=500)
    default_lang: str | None = Field(default=None, max_length=10)
    enable_email: bool | None = Field(default=None)
    copyright: str | None = Field(default=None, max_length=200)
    icp: str | None = Field(default=None, max_length=100)


# ─── OAuth 登录配置 ──────────────────────────────────────────────────────

class OAuthConfigBase(SQLModel):
    # QQ 登录
    qq_app_id: str = Field(default="", max_length=100, description="QQ AppID")
    qq_app_key: str = Field(default="", max_length=100, description="QQ AppKey")
    qq_redirect_uri: str = Field(default="", max_length=500, description="QQ 回调地址")
    qq_enabled: bool = Field(default=False, description="启用 QQ 登录")
    # 微信登录
    wechat_app_id: str = Field(default="", max_length=100, description="微信 AppID")
    wechat_app_secret: str = Field(default="", max_length=100, description="微信 AppSecret")
    wechat_redirect_uri: str = Field(default="", max_length=500, description="微信回调地址")
    wechat_enabled: bool = Field(default=False, description="启用微信登录")


class OAuthConfig(OAuthConfigBase, BaseModel, TimestampMixin, table=True):
    """OAuth 登录配置 — 全局只有一条记录"""

    SENSITIVE_FIELDS: ClassVar[list[str]] = ["qq_app_key", "wechat_app_secret"]


class OAuthConfigUpdate(SQLModel):
    qq_app_id: str | None = Field(default=None, max_length=100)
    qq_app_key: str | None = Field(default=None, max_length=100)
    qq_redirect_uri: str | None = Field(default=None, max_length=500)
    qq_enabled: bool | None = Field(default=None)
    wechat_app_id: str | None = Field(default=None, max_length=100)
    wechat_app_secret: str | None = Field(default=None, max_length=100)
    wechat_redirect_uri: str | None = Field(default=None, max_length=500)
    wechat_enabled: bool | None = Field(default=None)


# ─── 邮件配置 ────────────────────────────────────────────────────────────

class EmailConfigBase(SQLModel):
    host: str = Field(default="", max_length=200, description="SMTP 服务器地址")
    port: int = Field(default=587, description="SMTP 端口")
    username: str = Field(default="", max_length=200, description="SMTP 用户名")
    password: str = Field(default="", max_length=200, description="SMTP 密码")
    sender: str = Field(default="", max_length=200, description="发件人地址")
    use_tls: bool = Field(default=True, description="使用 TLS")
    use_ssl: bool = Field(default=False, description="使用 SSL")


class EmailConfig(EmailConfigBase, BaseModel, TimestampMixin, table=True):
    """邮件配置 — 全局只有一条记录"""

    SENSITIVE_FIELDS: ClassVar[list[str]] = ["password"]


class EmailConfigUpdate(SQLModel):
    host: str | None = Field(default=None, max_length=200)
    port: int | None = Field(default=None)
    username: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, max_length=200)
    sender: str | None = Field(default=None, max_length=200)
    use_tls: bool | None = Field(default=None)
    use_ssl: bool | None = Field(default=None)
