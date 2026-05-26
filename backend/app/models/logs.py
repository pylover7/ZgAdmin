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
        default_factory=datetime.now, index=True,
        description="日志时间",
        schema_extra={"examples": ["2026-05-26T10:30:00"]})


class LogLevel(SQLModel):
    level: str = Field(
        index=True,
        description="日志级别：success/fail（登录日志）；DEBUG/INFO/WARNING/ERROR/CRITICAL（系统日志）",
        schema_extra={"examples": ["success"]})


class LoginLogCreate(LogLevel):
    username: str = Field(
        index=True,
        description="登录用户名",
        schema_extra={"examples": ["admin"]})
    ip: str = Field(
        index=True,
        description="登录IP地址",
        schema_extra={"examples": ["192.168.1.100"]})
    address: str = Field(
        default="",
        description="IP归属地",
        schema_extra={"examples": ["北京市"]})
    system: str = Field(
        default="",
        description="客户端操作系统",
        schema_extra={"examples": ["Windows 10"]})
    browser: str = Field(
        default="",
        description="客户端浏览器",
        schema_extra={"examples": ["Chrome 126"]})
    behavior: str = Field(
        default="",
        description="登录行为：login-登录，logout-登出",
        schema_extra={"examples": ["login"]})


class LoginLog(Log, LoginLogCreate, table=True):
    pass


class LoginLogUpdate(LoginLogCreate):
    pass


class LoginLogFilter(SQLModel):
    username: str | None = Field(
        default=None,
        description="用户名（模糊搜索）",
        schema_extra={"examples": ["admin"]})
    level: str | None = Field(
        default=None,
        description="登录状态：success/fail",
        schema_extra={"examples": ["success"]})
    loginTime: list[datetime] | None = Field(
        default=None,
        description="登录时间范围 [开始时间, 结束时间]",
        schema_extra={"examples": [["2026-05-01T00:00:00", "2026-05-26T23:59:59"]]})


class OperationLogCreate(LogLevel):
    username: str = Field(
        index=True,
        description="操作人用户名",
        schema_extra={"examples": ["admin"]})
    message: str = Field(
        default="",
        description="操作描述",
        schema_extra={"examples": ["修改了用户 zhangsan 的角色"]})


class OperationLog(Log, OperationLogCreate, table=True):
    pass


class OperationLogUpdate(OperationLogCreate):
    pass


class OperationLogFilter(SQLModel):
    level: list[str] = Field(
        default=None,
        description="日志等级列表",
        schema_extra={"examples": [["INFO", "WARNING"]]})
    operationTime: list[datetime] | None = Field(
        default=None,
        description="操作时间范围 [开始时间, 结束时间]",
        schema_extra={"examples": [["2026-05-01T00:00:00", "2026-05-26T23:59:59"]]})


class SystemLogCreate(LogLevel):
    module: str = Field(
        default="",
        description="所属模块",
        schema_extra={"examples": ["system"]})
    message: str = Field(
        default="",
        description="日志内容",
        schema_extra={"examples": ["系统启动完成"]})


class SystemLog(Log, SystemLogCreate, table=True):
    pass


class SystemLogUpdate(SystemLogCreate):
    pass


class SystemLogFilter(SQLModel):
    module: str | None = Field(
        default=None,
        description="模块名称",
        schema_extra={"examples": ["system"]})
    operationTime: list[datetime] | None = Field(
        default=None,
        description="操作时间范围 [开始时间, 结束时间]",
        schema_extra={"examples": [["2026-05-01T00:00:00", "2026-05-26T23:59:59"]]})
