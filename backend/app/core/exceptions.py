from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.settings.log import logger


class SettingNotFound(Exception):
    pass


async def IntegrityHandle(_: Request, exc: IntegrityError) -> JSONResponse:
    await logger.systemError("Database", f"IntegrityError: {exc}")
    content = dict(
        code=500,
        msg=f"IntegrityError，{exc}",
    )
    return JSONResponse(content=content, status_code=500)


async def HttpExcHandle(_: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code >= 500:
        await logger.systemError("System", f"HTTP {exc.status_code}: {exc.detail}")
    content = dict(code=exc.status_code, msg=exc.detail, data=None)
    return JSONResponse(content=content, status_code=exc.status_code)


async def RequestValidationHandle(
        _: Request, exc: RequestValidationError) -> JSONResponse:
    await logger.systemWarning("System", f"RequestValidationError: {exc}")
    content = dict(code=422, msg=f"RequestValidationError, {exc}")
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(
        _: Request, exc: ResponseValidationError) -> JSONResponse:
    await logger.systemError("System", f"ResponseValidationError: {exc}")
    content = dict(code=500, msg=f"ResponseValidationError, {exc}")
    return JSONResponse(content=content, status_code=500)
