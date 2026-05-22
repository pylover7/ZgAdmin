from pathlib import Path

from sqlmodel import Session, SQLModel, select
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from alembic.config import Config as AlembicConfig
from alembic.command import upgrade

from app.controllers.user import userController
from app.core.schedule import update_expired_orders
from app.models import User, UserCreate, Api
from app.models.link import RoleApiLink
from app.settings.log import logger
from app.settings import settings
from app.utils.staticFileUtils import check_dir_exists
from app.core import engine, DatabaseSession
from app.seed import seed_all

scheduler = AsyncIOScheduler()


def _sync_api_routes(app: FastAPI, session: Session):
    apis = app.openapi()["paths"]
    # 收集当前注册的所有 (method, path) 组合
    current_routes: set[tuple[str, str]] = set()
    for path, methods in apis.items():
        for method, meta in methods.items():
            tags = ",".join(meta.get("tags", []))
            summary = meta.get("summary", "")
            method_upper = method.upper()
            current_routes.add((method_upper, path))
            existing = session.exec(
                select(Api).where(Api.path == path, Api.method == method_upper)
            ).first()
            if existing:
                existing.summary = summary
                existing.tags = tags
                session.add(existing)
            else:
                session.add(Api(path=path, method=method_upper, tags=tags, summary=summary))
    # 删除数据库中已不存在的路由（手动清理关联的 RoleApiLink）
    all_db_apis = session.exec(select(Api)).all()
    for db_api in all_db_apis:
        if (db_api.method, db_api.path) not in current_routes:
            for link in session.exec(
                select(RoleApiLink).where(RoleApiLink.api_id == db_api.id)
            ).all():
                session.delete(link)
            session.delete(db_api)
    session.commit()


async def init_data(app: FastAPI) -> None:
    logger.info("初始化数据库...")
    SQLModel.metadata.create_all(engine)
    logger.info("检查静态文件目录...")
    check_dir_exists([settings.STATIC_PATH, settings.GOODS_PATH])

    with DatabaseSession() as session:
        # 种子数据：部门、菜单
        dept = seed_all(session)

        # 创建默认管理员
        admin = session.exec(
            select(User).where(
                (User.email == settings.EMAIL_TEST_USER)
                | (User.username == settings.FIRST_SUPERUSER)
                | (User.is_superuser)
            )
        ).first()
        if not admin:
            logger.info("创建管理员账户...")
            user_in = UserCreate(
                username=settings.FIRST_SUPERUSER,
                nickname="管理员",
                email=settings.EMAIL_TEST_USER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                status=1,
                is_superuser=True,
                phone="13800138000",
                remark="这是管理员"
            )
            admin = await userController.create(session=session, obj_in=user_in)
            logger.info(f"管理员创建成功: {admin.username}")
            if dept is not None:
                dept.users.append(admin)
                session.add(dept)
                session.commit()
        else:
            logger.info("管理员账户已存在，跳过创建")

        # 同步 API 路由到数据库
        logger.info("同步API路由...")
        _sync_api_routes(app, session)

        # 定时任务
        logger.info("启动定时任务...")
        scheduler.add_job(update_expired_orders, "interval", seconds=120)
        scheduler.start()
