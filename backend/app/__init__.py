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
from app.settings.log import logger

try:
    from app.settings import settings
except ImportError:
    raise SettingNotFound("无法加载配置文件，请检查配置文件是否存在！！！")


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


def create_app() -> FastAPI:
    Path(settings.STATIC_PATH).mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan_context,
    )
    register_exceptions(app)
    register_routers(app, prefix="/api")
    app.mount("/static", StaticFiles(directory=settings.STATIC_PATH), name="static")
    return app


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    # 启动时执行的逻辑
    await logger.systemInfo("System", f"应用启动 - {settings.PROJECT_NAME} v{settings.VERSION}")
    await init_data(app)
    await logger.systemInfo("System", "数据库初始化完成")
    yield
    # 关闭时执行的逻辑（如果需要）
    await logger.systemInfo("System", "应用关闭")


app = create_app()
