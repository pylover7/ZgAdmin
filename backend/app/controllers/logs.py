from app.core.crud import CRUDBase
from app.models import (
    LoginLog,
    LoginLogCreate,
    LoginLogUpdate,
    OperationLog,
    OperationLogCreate,
    OperationLogUpdate,
    SystemLog,
    SystemLogCreate,
    SystemLogUpdate,
)


class LoginLogController(CRUDBase[LoginLog, LoginLogCreate, LoginLogUpdate]):
    def __init__(self):
        super().__init__(LoginLog)


class OperationLogController(CRUDBase[OperationLog, OperationLogCreate, OperationLogUpdate]):
    def __init__(self):
        super().__init__(OperationLog)


class SystemLogController(CRUDBase[SystemLog, SystemLogCreate, SystemLogUpdate]):
    def __init__(self):
        super().__init__(SystemLog)


loginLoginController = LoginLogController()
operationLogController = OperationLogController()
systemLogController = SystemLogController()
