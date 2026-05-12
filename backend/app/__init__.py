from pathlib import Path
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from app.core.database import init_data
from app.core.exceptions import SettingNotFound
from app.core.init import make_middlewares, register_routers, register_exceptions
from app.settings import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


def create_app() -> FastAPI:
    Path(settings.STATIC_PATH).mkdir(parents=True, exist_ok=True)

    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan_context,
    )
    register_exceptions(application)
    register_routers(application, prefix="/api")
    application.mount("/static", StaticFiles(directory=settings.STATIC_PATH), name="static")
    return application


@asynccontextmanager
async def lifespan_context(application: FastAPI):
    # 启动时执行的逻辑
    await init_data(application)
    yield
    # 关闭时执行的逻辑（如果需要）


app = create_app()
