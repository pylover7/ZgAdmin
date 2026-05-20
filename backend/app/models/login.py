from datetime import datetime

from sqlmodel import SQLModel, Field


class CredentialsSchema(SQLModel):
    username: str = Field(..., description="用户名称")
    password: str = Field(..., description="密码")


class refreshTokenSchema(SQLModel):
    refreshToken: str = Field(..., description="刷新令牌")


class JWTReOut(SQLModel):
    accessToken: str
    refreshToken: str
    expires: str


class JWTOut(SQLModel):
    username: str
    nickname: str = ""
    depart: str
    roles: list[str]
    accessToken: str
    refreshToken: str
    expires: str


class JWTPayload(SQLModel):
    user_id: str
    username: str
    is_superuser: bool
    exp: datetime


class QQLoginSchema(SQLModel):
    code: str = Field(..., description="QQ授权码")
    state: str = Field(..., description="状态参数")


class QQUserInfo(SQLModel):
    openid: str = Field(..., description="用户OpenID")
    nickname: str = Field(..., description="用户昵称")
    avatar: str = Field(..., description="头像URL")
    unionid: str | None = Field(default=None, description="用户UnionID")


class QQAccessToken(SQLModel):
    access_token: str = Field(..., description="访问令牌")
    expires_in: int = Field(..., description="过期时间(秒)")
    refresh_token: str = Field(..., description="刷新令牌")
    openid: str = Field(..., description="用户OpenID")
    scope: str = Field(..., description="授权范围")
    unionid: str | None = Field(default=None, description="用户UnionID")
