import logging.config
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sqlalchemy import inspect, text
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

ALEMBIC_INI_PATH = Path(__file__).resolve().parent.parent.parent / "alembic.ini"


def _make_alembic_config() -> Config:
    """构造 alembic Config，并确保 env.py 与 app.core.engine 指向同一个库。

    env.py 优先读取 ALEMBIC_DB_URL（见 alembic/env.py:27）。若本进程显式设置了该变量，
    版本检测（走 app.core.engine）与迁移执行（走 env.py 自建引擎）就会指向不同的库，
    出现「检测一个库、升级另一个库」的错配。此处统一以 app.core.engine 为准，
    使两条路径强制同一。
    """
    os.environ["ALEMBIC_DB_URL"] = settings.SQLALCHEMY_DATABASE_URI
    return Config(str(ALEMBIC_INI_PATH))


def _current_revision(alembic_cfg: Config) -> str | None:
    """读取当前库的 alembic 版本号；alembic_version 表不存在时返回 None。

    不使用 command.current()：它只把结果打印到 stdout，拿不到结构化返回值。
    """
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        return None
    with engine.connect() as conn:
        row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
    return row[0] if row else None


def _head_revision(alembic_cfg: Config) -> str:
    """取迁移链的 head 版本号；存在多个 head（分支）时显式抛错。"""
    heads = ScriptDirectory.from_config(alembic_cfg).get_heads()
    if len(heads) > 1:
        raise RuntimeError(f"迁移链存在多个 head（分支），必须先合并分支再启动：{sorted(heads)}")
    return heads[0]


def _upgrade_to_head(alembic_cfg: Config) -> None:
    """版本检测 → 执行迁移。已是 head 时跳过。迁移失败直接抛错，让启动失败。"""
    current = _current_revision(alembic_cfg)
    head = _head_revision(alembic_cfg)
    if current == head:
        logger.info(f"数据库已是最新版本（{head}），跳过迁移")
        return
    logger.info(f"执行数据库迁移: {current or '空库'} → {head}")
    command.upgrade(alembic_cfg, "head")


def _repair_dirty_tables() -> None:
    """自愈：补齐缺失的表与列，使历史遗留库能继续启动。

    ⚠️ 该机制会掩盖「改了模型但忘记生成迁移脚本」的错误——被它补齐的库看起来是正常的，
    而全新环境部署时才会暴露。因此它只是兜底，不能替代迁移脚本，且失败不阻断启动。
    """
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())
    model_tables = SQLModel.metadata.tables
    missing_tables = sorted(set(model_tables) - db_tables)

    if missing_tables:
        logger.warning(f"检测到缺失的表，正在补齐: {missing_tables}")
        SQLModel.metadata.create_all(engine, tables=[model_tables[t] for t in missing_tables])
        db_tables |= set(missing_tables)

    for table_name in sorted(db_tables & set(model_tables)):
        db_columns = {c["name"] for c in inspector.get_columns(table_name)}
        missing_columns = [c for c in model_tables[table_name].columns if c.name not in db_columns]
        if not missing_columns:
            continue
        logger.warning(f"表 {table_name} 检测到缺失的列，正在补齐: {[c.name for c in missing_columns]}")
        for column in missing_columns:
            col_type = column.type.compile(engine.dialect)
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {col_type}'))


def _setup_logging() -> None:
    """重新应用应用日志配置。

    alembic 内部会调用 logging.basicConfig()，给 root logger 添加 handler，
    破坏 uvicorn 的 logging 层级关系（表现：access log 不输出）。
    """
    logging.config.dictConfig(settings.APP_LOG_CONFIG)


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


async def _ensure_admin(session: Session, dept: object | None) -> None:
    """创建默认管理员（如果不存在）。在安全策略之前执行，避免密码复杂度校验阻止种子用户创建。"""
    import secrets
    import string

    admin = session.exec(
        select(User).where(
            (User.email == settings.EMAIL_TEST_USER) | (User.username == settings.FIRST_SUPERUSER) | (User.is_superuser)
        )
    ).first()
    if not admin:
        logger.info("创建管理员账户...")
        # 随机生成强密码（满足默认密码策略：大小写+数字+特殊字符，16位）
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            admin_password = "".join(secrets.choice(alphabet) for _ in range(16))
            if (
                any(c.isupper() for c in admin_password)
                and any(c.islower() for c in admin_password)
                and any(c.isdigit() for c in admin_password)
                and any(c in "!@#$%^&*" for c in admin_password)
            ):
                break
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            nickname="管理员",
            email=settings.EMAIL_TEST_USER,
            password=admin_password,
            status=1,
            is_superuser=True,
            phone="13800138000",
            remark="这是管理员",
        )
        admin = await userController.create(session=session, obj_in=user_in)
        logger.info(f"管理员创建成功: {admin.username}")
        # 醒目打印管理员凭据
        logger.warning("=" * 60)
        logger.warning("  首次启动 — 已自动生成管理员密码")
        logger.warning(f"  用户名: {settings.FIRST_SUPERUSER}")
        logger.warning(f"  密码:   {admin_password}")
        logger.warning("  请妥善保存此密码，关闭后将无法再次查看！")
        logger.warning("=" * 60)
        if dept is not None:
            dept.users.append(admin)
            session.add(dept)
            session.commit()
    else:
        logger.info("管理员账户已存在，跳过创建")


def _ensure_configs(session: Session) -> None:
    """确保所有配置单行表存在默认记录"""
    if not session.exec(select(SecurityPolicy)).first():
        logger.info("创建默认安全策略...")
        session.add(SecurityPolicy())
        session.commit()

    if not session.exec(select(SiteConfig)).first():
        logger.info("创建默认站点配置...")
        session.add(SiteConfig())
        session.commit()

    if not session.exec(select(OAuthConfig)).first():
        logger.info("创建默认OAuth配置...")
        session.add(OAuthConfig())
        session.commit()

    if not session.exec(select(EmailConfig)).first():
        logger.info("创建默认邮件配置...")
        session.add(EmailConfig())
        session.commit()


async def init_data(app: FastAPI) -> None:
    logger.info("初始化数据库...")
    alembic_cfg = _make_alembic_config()
    _upgrade_to_head(alembic_cfg)
    _repair_dirty_tables()
    _setup_logging()

    logger.info("检查静态文件目录...")
    check_dir_exists([settings.STATIC_PATH])

    with DatabaseSession() as session:
        dept = seed_all(session)
        await _ensure_admin(session, dept)
        _ensure_configs(session)

        logger.info("同步API路由...")
        _sync_api_routes(app, session)

        logger.info("启动定时任务...")
        scheduler.add_job(update_expired_orders, "interval", seconds=120)
        scheduler.start()
