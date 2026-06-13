import secrets
import warnings
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.database import db_engine


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    if isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", env_file=["../.env"], env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = ""
    # 60 minutes * 24 hours * 8 days = 8 days
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 3
    FRONTEND_HOST: str = "http://localhost:7000"
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 7001
    WORKERS: int = 1
    RELOAD: bool = False
    DEBUG: bool = False
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    DISPLAY_TIMEZONE: str = "Asia/Shanghai"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | list[str] | str, BeforeValidator(parse_cors)] = ["*"]

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [self.FRONTEND_HOST]

    PROJECT_NAME: str = "ZgAdmin"
    PROJECT_DESCRIPTION: str = "一个开源的在线工具箱"

    @computed_field
    @property
    def VERSION(self) -> str:
        """从 VERSION 文件读取版本号"""
        try:
            version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
            return version_file.read_text().strip()
        except Exception:
            return "unknown"

    STATIC_PATH: str = str(Path(__file__).parent.parent.parent.joinpath("static"))
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024

    SENTRY_DSN: HttpUrl | None = None

    # 功能开关 — 设为 false 可关闭对应模块
    FEATURE_QQ_LOGIN: bool = False
    FEATURE_WECHAT_LOGIN: bool = False
    FEATURE_EMAIL: bool = False
    FEATURE_MONITOR_LOG: bool = True

    DB_SCHEME: str = "sqlite"
    DB_SERVER: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "test"  # noqa: S105
    DB_PATH: str = "zgadmin.sqlite"
    REDIS_URL: str = ""  # 空=自动（dev用内存，prod需配置redis://host:port/db）

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return db_engine(self.DB_SCHEME, self.DB_USER, self.DB_PASSWORD, self.DB_SERVER, self.DB_PORT, self.DB_PATH)

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: str = "test@example.com"
    FIRST_SUPERUSER: str = "admin"

    # QQ登录配置
    QQ_APP_ID: str = ""
    QQ_APP_KEY: str = ""
    QQ_REDIRECT_URI: str = "http://localhost:7000/login/qq/callback"

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", for security, please change it, at least for deployments.'
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    def _resolve_secret_key(self) -> str:
        """生成持久化的 SECRET_KEY，重启后保持不变。仅用于本地开发环境。"""
        secret_key_file = Path(__file__).parent.parent.parent / ".secret_key"
        key = ""

        # 1. 从文件读取已有的 key
        if secret_key_file.exists():
            key = secret_key_file.read_text().strip()

        # 2. 生成新 key 并持久化
        if not key:
            key = secrets.token_urlsafe(32)
            secret_key_file.write_text(key)

        return key

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        if not self.SECRET_KEY or self.SECRET_KEY == "changethis":
            if self.ENVIRONMENT in ("production", "staging"):
                raise ValueError(
                    "生产/预发布环境必须显式设置 SECRET_KEY（通过 .env 或环境变量），"
                    "不可依赖自动生成的密钥。"
                )
            self.SECRET_KEY = self._resolve_secret_key()
        # 生产环境检查 CORS 不为 *
        if self.ENVIRONMENT == "production":
            cors_origins = self.BACKEND_CORS_ORIGINS
            if cors_origins in (["*"], "*"):
                raise ValueError('生产环境 BACKEND_CORS_ORIGINS 不可为 ["*"]，请在 .env 或环境变量中配置具体域名')
        return self

    APP_LOG_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": "%(asctime)s | %(levelprefix)s %(client_addr)s - %(status_code)s - %(request_line)s",
            },
        },
        "handlers": {
            "default": {"formatter": "default", "class": "logging.StreamHandler", "stream": "ext://sys.stderr"},
            "access": {"formatter": "access", "class": "logging.StreamHandler", "stream": "ext://sys.stderr"},
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }


settings = Settings()
