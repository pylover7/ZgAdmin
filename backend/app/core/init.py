from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.exceptions import (
    FastAPIHTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.settings import settings
from app.settings.config import base_config

from .middlewares import BackGroundTaskMiddleware, IPFilterMiddleware


def _get_cors_origins() -> list[str]:
    """获取 CORS 允许的来源列表，优先读取 INI 配置"""
    # 1. 尝试从 base.ini [security] cors_origins 读取
    ini_origins = base_config.get_config("security", "cors_origins", fallback="")
    if ini_origins:
        return [o.strip() for o in ini_origins.split(",") if o.strip()]

    # 2. 回退到 .env / Settings 配置
    return settings.all_cors_origins


def make_middlewares():
    cors_origins = _get_cors_origins()
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_origin_regex=r"https?://.*\.cnb\.space",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(IPFilterMiddleware),
        Middleware(BackGroundTaskMiddleware),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(FastAPIHTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(
        ResponseValidationError,
        ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)
