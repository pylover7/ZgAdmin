"""core/database.py 全链路单元测试 — init_data / _sync_api_routes / _ensure_admin / _ensure_configs"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.core as core_module
from app.core import database as db_module
from app.models import Api, User
from app.models.config import EmailConfig, OAuthConfig, SiteConfig
from app.models.link import RoleApiLink
from app.models.security import SecurityPolicy


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _app_with_paths(paths):
    app = FastAPI()

    @app.get("/api/v1/keep")
    async def keep():  # pragma: no cover - 仅用于生成 openapi
        return {"ok": True}

    return app


class TestSyncApiRoutes:
    def test_insert_and_update(self):
        engine = _engine()
        app = FastAPI()

        @app.get("/api/v1/demo", tags=["demo"], summary="示例")
        async def demo():  # pragma: no cover
            return {}

        with Session(engine) as session:
            db_module._sync_api_routes(app, session)
            api = session.exec(select(Api).where(Api.path == "/api/v1/demo")).first()
            assert api is not None
            assert api.summary == "示例"

            # 再次同步 → 走 update 分支
            db_module._sync_api_routes(app, session)
            assert len(session.exec(select(Api).where(Api.path == "/api/v1/demo")).all()) == 1

    def test_deletes_stale_routes_and_links(self):
        engine = _engine()
        app = FastAPI()

        @app.get("/api/v1/alive")
        async def alive():  # pragma: no cover
            return {}

        with Session(engine) as session:
            stale = Api(path="/api/v1/dead", method="GET", tags="", summary="")
            session.add(stale)
            session.commit()
            session.refresh(stale)
            session.add(RoleApiLink(role_id=uuid4(), api_id=stale.id))
            session.commit()

            db_module._sync_api_routes(app, session)
            assert session.exec(select(Api).where(Api.path == "/api/v1/dead")).first() is None
            assert session.exec(select(RoleApiLink).where(RoleApiLink.api_id == stale.id)).first() is None
            assert session.exec(select(Api).where(Api.path == "/api/v1/alive")).first() is not None


class TestEnsureConfigs:
    def test_creates_all_defaults(self):
        with Session(_engine()) as session:
            db_module._ensure_configs(session)
            assert session.exec(select(SecurityPolicy)).first() is not None
            assert session.exec(select(SiteConfig)).first() is not None
            assert session.exec(select(OAuthConfig)).first() is not None
            assert session.exec(select(EmailConfig)).first() is not None

    def test_idempotent(self):
        engine = _engine()
        with Session(engine) as session:
            db_module._ensure_configs(session)
        with Session(engine) as session:
            db_module._ensure_configs(session)
            assert len(session.exec(select(SiteConfig)).all()) == 1
            assert len(session.exec(select(SecurityPolicy)).all()) == 1


class TestEnsureAdmin:
    @pytest.mark.asyncio
    async def test_creates_admin_with_dept(self):
        from app.models import Department

        engine = _engine()
        with Session(engine) as session:
            dept = Department(name="总部", name_en="Head")
            session.add(dept)
            session.commit()
            session.refresh(dept)
            await db_module._ensure_admin(session, dept)
            admin = session.exec(select(User).where(User.is_superuser)).first()
            assert admin is not None
            assert admin in dept.users

    @pytest.mark.asyncio
    async def test_skips_when_exists(self):
        engine = _engine()
        with Session(engine) as session:
            session.add(User(username="admin", email="a@b.com", password="x" * 60, is_superuser=True, status=1))
            session.commit()
            before = len(session.exec(select(User)).all())
            await db_module._ensure_admin(session, None)
            assert len(session.exec(select(User)).all()) == before

    @pytest.mark.asyncio
    async def test_no_dept(self):
        engine = _engine()
        with Session(engine) as session:
            await db_module._ensure_admin(session, None)
            assert session.exec(select(User).where(User.is_superuser)).first() is not None


class TestInitData:
    @pytest.mark.asyncio
    async def test_full_init(self):
        engine = _engine()
        app = FastAPI()

        @app.get("/api/v1/health")
        async def health():  # pragma: no cover
            return {"ok": True}

        mock_scheduler = MagicMock()
        with (
            patch.object(db_module, "engine", engine, create=True),
            patch.object(core_module, "engine", engine, create=True),
            patch.object(db_module, "seed_all", return_value=None),
            patch.object(db_module, "_ensure_admin", AsyncMock()),
            patch.object(db_module, "scheduler", mock_scheduler),
            patch.object(db_module, "check_dir_exists"),
            # init_data 已改为「版本检测 → alembic 迁移」，不再走 create_all + stamp。
            # 此处只替换「迁移执行」与「结构自愈」两个动作，使其不触碰真实库；
            # 版本检测 / 默认配置 / 路由同步仍跑真实实现，故下面的断言才有意义。
            patch.object(db_module, "_upgrade_to_head"),
            patch.object(db_module, "_repair_dirty_tables"),
            patch.object(db_module.logging.config, "dictConfig"),
        ):
            await db_module.init_data(app)

        mock_scheduler.add_job.assert_called_once()
        mock_scheduler.start.assert_called_once()
        # 默认配置 + 同步路由均生效（本测试已将共享 engine 指向临时内存库）
        with Session(engine) as session:
            assert session.exec(select(SecurityPolicy)).first() is not None
            assert session.exec(select(Api).where(Api.path == "/api/v1/health")).first() is not None
