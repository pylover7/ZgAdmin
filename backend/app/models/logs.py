from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel

from .base import BaseModel


class LogModule(StrEnum):
    """系统日志模块常量，作为 module 字段的值存储到数据库"""
    SYSTEM = "system"
    SYSTEM_MANAGEMENT = "system_management"
    DATABASE = "database"


class Log(BaseModel):
    time: datetime = Field(
        default_factory=datetime.now, index=True, description="日志时间"
    )


class LogLevel(SQLModel):
    level: str = Field(index=True, description="日志级别")


class LoginLogCreate(LogLevel):
    username: str = Field(index=True, description="用户名")
    ip: str = Field(index=True, description="登录IP")
    address: str = Field(default="", description="IP归属地")
    system: str = Field(default="", description="操作系统")
    browser: str = Field(default="", description="浏览器")
    behavior: str = Field(default="", description="登录行为")


class LoginLog(Log, LoginLogCreate, table=True):
    pass


class LoginLogUpdate(LoginLogCreate):
    pass


class LoginLogFilter(SQLModel):
    username: str | None = Field(default=None, description="用户名")
    level: str | None = Field(default=None, description="登录状态")
    loginTime: list[datetime] | None = Field(
        default=None, description="登录时间范围"
    )


class OperationLogCreate(LogLevel):
    username: str = Field(index=True, description="用户名")
    message: str = Field(default="", description="操作描述")


class OperationLog(Log, OperationLogCreate, table=True):
    pass


class OperationLogUpdate(OperationLogCreate):
    pass


class OperationLogFilter(SQLModel):
    level: list[str] = Field(default=None, description="日志等级")
    operationTime: list[datetime] | None = Field(
        default=None, description="操作时间范围"
    )


class SystemLogCreate(LogLevel):
    module: str = Field(default="", description="所属模块")
    message: str = Field(default="", description="日志内容")


class SystemLog(Log, SystemLogCreate, table=True):
    pass


class SystemLogUpdate(SystemLogCreate):
    pass


class SystemLogFilter(SQLModel):
    module: str | None = Field(default=None, description="模块名称")
    operationTime: list[datetime] | None = Field(
        default=None, description="操作时间范围"
    )
