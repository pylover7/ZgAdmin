from pathlib import Path

import logging.config

from alembic import command
from alembic.config import Config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sqlmodel import Session, SQLModel, select

from app.controllers.user import userController
from app.core import DatabaseSession, engine
from app.core.schedule import update_expired_orders
from app.models import Api, User, UserCreate
from app.models.config import EmailConfig, OAuthConfig, SiteConfig
from app.models.link import RoleApiLink
from app.models.security import SecurityPolicy
from app.seed import seed_all
from app.settings import settings
from app.settings.log import logger
from app.utils.staticFileUtils import check_dir_exists

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
            existing = session.exec(select(Api).where(Api.path == path, Api.method == method_upper)).first()
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
            for link in session.exec(select(RoleApiLink).where(RoleApiLink.api_id == db_api.id)).all():
                session.delete(link)
            session.delete(db_api)
    session.commit()


async def init_data(app: FastAPI) -> None:
    logger.info("初始化数据库...")
    SQLModel.metadata.create_all(engine)
    logger.info("检查静态文件目录...")
    check_dir_exists([settings.STATIC_PATH])

    with DatabaseSession() as session:
        # 种子数据：部门、菜单
        dept = seed_all(session)

        # 创建默认管理员（在安全策略之前，避免密码复杂度校验阻止种子用户创建）
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
                remark="这是管理员",
            )
            admin = await userController.create(session=session, obj_in=user_in)
            logger.info(f"管理员创建成功: {admin.username}")
            if dept is not None:
                dept.users.append(admin)
                session.add(dept)
                session.commit()
        else:
            logger.info("管理员账户已存在，跳过创建")

        # 确保安全策略配置存在（单行表，只有一条记录）
        security_policy = session.exec(select(SecurityPolicy)).first()
        if not security_policy:
            logger.info("创建默认安全策略...")
            security_policy = SecurityPolicy()
            session.add(security_policy)
            session.commit()

        # 确保站点配置存在
        site_config = session.exec(select(SiteConfig)).first()
        if not site_config:
            logger.info("创建默认站点配置...")
            session.add(SiteConfig())
            session.commit()

        # 确保 OAuth 配置存在
        oauth_config = session.exec(select(OAuthConfig)).first()
        if not oauth_config:
            logger.info("创建默认OAuth配置...")
            session.add(OAuthConfig())
            session.commit()

        # 确保邮件配置存在
        email_config = session.exec(select(EmailConfig)).first()
        if not email_config:
            logger.info("创建默认邮件配置...")
            session.add(EmailConfig())
            session.commit()

        # 同步 API 路由到数据库
        logger.info("同步API路由...")
        _sync_api_routes(app, session)

        # 定时任务
        logger.info("启动定时任务...")
        scheduler.add_job(update_expired_orders, "interval", seconds=120)
        scheduler.start()

    # 同步 alembic 版本标记，确保 create_all 建表后 alembic 不会重复跑迁移
    alembic_cfg = Config(str(Path(__file__).resolve().parent.parent.parent / "alembic.ini"))
    command.stamp(alembic_cfg, "head")
    # alembic 内部会调用 logging.basicConfig()，给 root logger 添加 handler，
    # 这会破坏 uvicorn 的 logging 层级关系，导致 access log 不输出，
    # 重新应用 APP_LOG_CONFIG 修复此问题
    logging.config.dictConfig(settings.APP_LOG_CONFIG)
    logger.info("Alembic 版本已标记为 head")
