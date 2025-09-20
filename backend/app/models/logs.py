from datetime import datetime

from sqlmodel import Field, SQLModel

from .base import BaseModel


class Log(BaseModel):
    time: datetime = Field(
        default_factory=datetime.now, index=True, description="日志时间"
    )

class LogLevel(BaseModel):
    level: str = Field(index=True, description="日志级别")

class LoginLogCreate(LogLevel):
    user: str = Field(index=True, description="用户名")
    ip: str = Field(index=True, description="登录IP")
    ip_area: str = Field(default="", description="IP归属地")
    system: str = Field(default="", description="操作系统")
    browser: str = Field(default="", description="浏览器")
    behavior: str = Field(default="", description="登录行为")

class LoginLog(Log, LoginLogCreate, table=True):
    pass

class LoginLogUpdate(LoginLogCreate):
    pass

class OperationLogCreate(LogLevel):
    user: str = Field(index=True, description="用户名")
    message: str = Field(default="", description="操作描述")

class OperationLog(Log, OperationLogCreate, table=True):
    pass

class OperationLogUpdate(OperationLogCreate):
    pass

class SystemLogCreate(LogLevel):
    message: str = Field(default="", description="日志内容")


class SystemLog(Log, SystemLogCreate, table=True):
    pass

class SystemLogUpdate(SystemLogCreate):
    pass
