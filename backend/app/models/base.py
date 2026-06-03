from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi.responses import JSONResponse
from sqlmodel import Field, SQLModel

from app.settings import settings

# 约束命名约定 — 让 Alembic 迁移能通过名称引用约束，解决 SQLite batch mode 下
# drop_constraint(None) 报 ValueError 的问题
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
SQLModel.metadata.naming_convention = NAMING_CONVENTION


class BaseModel(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="主键UUID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]},
    )

    async def to_dict(self, exclude_fields: list[str] | None = None):
        if exclude_fields is None:
            exclude_fields = []

        d = {}
        for field in self.__class__.model_fields:
            if field not in exclude_fields:
                value = getattr(self, field)
                if isinstance(value, datetime):
                    value = value.strftime(settings.DATETIME_FORMAT)
                if isinstance(value, UUID):
                    value = str(value)
                d[field] = value
        return d


class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=datetime.now, description="创建时间", schema_extra={"examples": ["2026-05-26T10:30:00"]}
    )


class Token(SQLModel):
    access_token: str = Field(
        description="访问令牌", schema_extra={"examples": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]}
    )
    token_type: str = Field(default="bearer", description="令牌类型", schema_extra={"examples": ["bearer"]})


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = Field(
        default=None,
        description="令牌主体（用户标识）",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]},
    )


class NewPassword(SQLModel):
    token: str = Field(description="重置密码令牌", schema_extra={"examples": ["reset-token-string"]})
    new_password: str = Field(
        min_length=8, max_length=40, description="新密码", schema_extra={"examples": ["NewP@ssw0rd123"]}
    )


class Success(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: str | None = "OK",
        success: bool = True,
        data: Any | None = None,
        **kwargs,
    ):
        content = {"code": code, "success": success, "msg": msg, "data": data}
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class Fail(JSONResponse):
    def __init__(
        self,
        code: int = 400,
        msg: str | None = "Fail",
        data: Any | None = None,
        **kwargs,
    ):
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class SuccessExtra(JSONResponse):
    def __init__(  # noqa: PLR0913
        self,
        code: int = 200,
        success: bool = True,
        msg: str | None = "OK",
        data: Any | None = None,
        total: int = 0,
        currentPage: int = 1,
        pageSize: int = 20,
        **kwargs,
    ):
        content = {
            "code": code,
            "success": success,
            "msg": msg,
            "data": data,
            "total": total,
            "currentPage": currentPage,
            "pageSize": pageSize,
        }
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class FailAuth(JSONResponse):
    def __init__(
        self,
        code: int = 401,
        msg: str | None = "Unauthorized",
        **kwargs,
    ):
        content = {"code": code, "msg": msg}
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class Image(SQLModel):
    base64: str = Field(
        description="Base64编码的图片数据", schema_extra={"examples": ["data:image/png;base64,iVBORw0KGgo..."]}
    )

    class Meta:
        extra = "allow"
