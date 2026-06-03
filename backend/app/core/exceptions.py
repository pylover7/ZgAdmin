from fastapi.exceptions import (
    HTTPException as FastAPIHTTPException,
)
from fastapi.exceptions import (
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.models.logs import LogModule
from app.settings.log import logger


class SettingNotFound(Exception):
    pass


async def IntegrityHandle(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, IntegrityError)  # noqa: S101
    await logger.systemError(LogModule.DATABASE, f"IntegrityError: {exc}")
    content = {"code": 500, "msg": f"IntegrityError，{exc}"}
    return JSONResponse(content=content, status_code=500)


async def HttpExcHandle(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, FastAPIHTTPException)  # noqa: S101
    if exc.status_code >= 500:
        await logger.systemError(LogModule.SYSTEM, f"HTTP {exc.status_code}: {exc.detail}")
    content = {"code": exc.status_code, "msg": exc.detail, "data": None}
    return JSONResponse(content=content, status_code=exc.status_code)


async def RequestValidationHandle(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101
    await logger.systemWarning(LogModule.SYSTEM, f"RequestValidationError: {exc}")
    content = {"code": 422, "msg": f"RequestValidationError, {exc}"}
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ResponseValidationError)  # noqa: S101
    await logger.systemError(LogModule.SYSTEM, f"ResponseValidationError: {exc}")
    content = {"code": 500, "msg": f"ResponseValidationError, {exc}"}
    return JSONResponse(content=content, status_code=500)
