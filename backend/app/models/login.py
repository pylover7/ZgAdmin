from datetime import datetime

from sqlmodel import Field, SQLModel


class CredentialsSchema(SQLModel):
    username: str = Field(..., description="用户名称", schema_extra={"examples": ["admin"]})
    password: str = Field(..., description="密码", schema_extra={"examples": ["MyP@ssw0rd"]})
    captcha_key: str | None = Field(
        default=None, description="验证码key（由验证码接口返回）", schema_extra={"examples": ["captcha-uuid-string"]}
    )
    captcha_code: str | None = Field(
        default=None, description="验证码（图片中的字符）", schema_extra={"examples": ["a3b7"]}
    )


class refreshTokenSchema(SQLModel):
    refreshToken: str = Field(
        ..., description="刷新令牌", schema_extra={"examples": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]}
    )


class JWTReOut(SQLModel):
    accessToken: str = Field(
        description="访问令牌", schema_extra={"examples": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]}
    )
    refreshToken: str = Field(
        description="刷新令牌", schema_extra={"examples": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]}
    )
    expires: int = Field(description="accessToken过期时间（毫秒时间戳）", schema_extra={"examples": [1748275200000]})


class JWTOut(SQLModel):
    username: str = Field(description="用户名称", schema_extra={"examples": ["admin"]})
    nickname: str = Field(default="", description="用户昵称", schema_extra={"examples": ["管理员"]})
    depart: str = Field(description="所属部门", schema_extra={"examples": ["技术部"]})
    roles: list[str] = Field(description="角色编码列表", schema_extra={"examples": [["admin", "editor"]]})
    accessToken: str = Field(
        description="访问令牌", schema_extra={"examples": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]}
    )
    refreshToken: str = Field(
        description="刷新令牌", schema_extra={"examples": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]}
    )
    expires: int = Field(description="accessToken过期时间（毫秒时间戳）", schema_extra={"examples": [1748275200000]})


class JWTPayload(SQLModel):
    user_id: str = Field(description="用户ID", schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    username: str = Field(description="用户名称", schema_extra={"examples": ["admin"]})
    is_superuser: bool = Field(description="是否为超级管理员", schema_extra={"examples": [True]})
    exp: datetime = Field(description="过期时间", schema_extra={"examples": ["2026-05-26T12:00:00"]})


class QQLoginSchema(SQLModel):
    code: str = Field(..., description="QQ授权码（OAuth回调获取）", schema_extra={"examples": ["AUTHORIZATION_CODE"]})
    state: str = Field(..., description="状态参数（防CSRF）", schema_extra={"examples": ["random-state-string"]})


class QQUserInfo(SQLModel):
    openid: str = Field(..., description="用户OpenID", schema_extra={"examples": ["A1B2C3D4E5F6G7H8"]})
    nickname: str = Field(..., description="用户昵称", schema_extra={"examples": ["QQ用户"]})
    avatar: str = Field(..., description="头像URL", schema_extra={"examples": ["https://q.qlogo.cn/xxx.jpg"]})
    unionid: str | None = Field(default=None, description="用户UnionID", schema_extra={"examples": ["UNION_ID_STRING"]})


class QQAccessToken(SQLModel):
    access_token: str = Field(..., description="访问令牌", schema_extra={"examples": ["ACCESS_TOKEN_STRING"]})
    expires_in: int = Field(..., description="过期时间（秒）", schema_extra={"examples": [7776000]})
    refresh_token: str = Field(..., description="刷新令牌", schema_extra={"examples": ["REFRESH_TOKEN_STRING"]})
    openid: str = Field(..., description="用户OpenID", schema_extra={"examples": ["A1B2C3D4E5F6G7H8"]})
    scope: str = Field(..., description="授权范围", schema_extra={"examples": ["get_user_info"]})
    unionid: str | None = Field(default=None, description="用户UnionID", schema_extra={"examples": ["UNION_ID_STRING"]})


class LogoutSchema(SQLModel):
    refreshToken: str | None = Field(default=None, description="刷新令牌")
