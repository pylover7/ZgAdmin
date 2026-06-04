"""
测试基础设施 — SQLite 内存 DB + MemoryRedis + TestClient

核心设计:
- test_engine: Session 级 SQLite 内存引擎，所有表只创建一次
- test_redis: Session 级 MemoryRedis 实例
- db: Function 级 Session，使用嵌套事务(savepoint)隔离，测试结束自动回滚
- client: TestClient，依赖注入覆盖 get_db / get_redis
- admin_user / admin_headers: 预创建超级管理员 + JWT
"""
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.core.dependency import get_db
from app.core.init import register_exceptions, register_routers
from app.core.redis import MemoryRedis
from app.core.redis import get_redis as _orig_get_redis

# ─── 确保所有 Model 注册到 SQLModel.metadata ───────────────────────────
from app.models import (  # noqa: F401
    Api,
    Department,
    EmailConfig,
    File,
    IPRule,
    LoginLog,
    Menu,
    Notice,
    NoticeRead,
    OAuthConfig,
    OperationLog,
    Role,
    RoleApiLink,
    RoleMenuLink,
    SecurityPolicy,
    SiteConfig,
    SystemLog,
    User,
    UserRoleLink,
)
from app.models.login import JWTPayload
from app.utils.jwtt import create_access_token
from app.utils.password import get_password_hash


# ─── 测试专用 App 工厂（无 lifespan，不触发 init_data） ────────────────
def create_test_app() -> FastAPI:
    application = FastAPI(
        title="Test App",
        openapi_url="/openapi.json",
    )
    register_exceptions(application)
    register_routers(application, prefix="/api")
    return application


# ═══════════════════════════════════════════════════════════════════════
# Session 级 fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_engine():
    """Session 级 SQLite 内存引擎 — 所有表只创建一次"""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    SQLModel.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="session")
def test_redis():
    """Session 级 MemoryRedis 实例"""
    redis = MemoryRedis()
    yield redis


# ═══════════════════════════════════════════════════════════════════════
# Function 级 fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def db(test_engine):
    """
    Function 级 DB Session — 嵌套事务隔离。
    每个 test 获得独立 savepoint，API 路由中的 commit 只释放 savepoint，
    测试结束后外层事务回滚，确保测试之间零污染。
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)

    # 开启嵌套事务（savepoint），使 session.commit() 只释放 savepoint
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db, test_redis):
    """TestClient — 覆盖 get_db / get_redis 依赖注入 + 全局 Redis 替换"""
    from unittest.mock import patch

    application = create_test_app()

    def _override_get_db():
        yield db

    def _override_get_redis():
        return test_redis

    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[_orig_get_redis] = _override_get_redis

    # 全局替换 Redis 单例 — 因为部分代码直接调用 get_redis() 而非依赖注入
    import app.core.redis as redis_mod
    original_instance = redis_mod.redis_manager._instance
    redis_mod.redis_manager._instance = test_redis

    # Mock getIpAddress — TestClient 的 client.host 为 "testclient"，不是合法 IP
    async def _mock_get_ip_address(ip: str) -> str:
        return "内网IP"

    # 必须在 import 位置 patch，而非定义位置
    with patch("app.controllers.user.getIpAddress", side_effect=_mock_get_ip_address), TestClient(application) as c:
        yield c

    application.dependency_overrides.clear()
    redis_mod.redis_manager._instance = original_instance


# ═══════════════════════════════════════════════════════════════════════
# 用户 / 认证 fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def admin_user(db):
    """创建超级管理员并返回 User 对象"""
    user = User(
        username="admin",
        nickname="测试管理员",
        email="admin@test.com",
        password=get_password_hash("admin123456"),
        phone="13800138000",
        status=1,
        is_superuser=True,
        sex=1,
        remark="测试管理员",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user):
    """超级管理员的 Authorization headers"""
    payload = JWTPayload(
        user_id=str(admin_user.id),
        username=admin_user.username,
        is_superuser=True,
        exp=datetime.now(UTC) + timedelta(hours=2),
    )
    token = create_access_token(data=payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def normal_user(db):
    """创建普通用户（非管理员）并返回 User 对象"""
    user = User(
        username="normaluser",
        nickname="普通用户",
        email="normal@test.com",
        password=get_password_hash("normal123456"),
        phone="13900139000",
        status=1,
        is_superuser=False,
        sex=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def disabled_user(db):
    """创建已禁用用户"""
    user = User(
        username="disabled_user",
        nickname="禁用用户",
        email="disabled@test.com",
        password=get_password_hash("disabled123456"),
        status=0,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def security_policy(db):
    """创建默认安全策略"""
    policy = SecurityPolicy()
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@pytest.fixture
def site_config(db):
    """创建默认站点配置"""
    config = SiteConfig()
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@pytest.fixture
def oauth_config(db):
    """创建默认 OAuth 配置"""
    config = OAuthConfig()
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@pytest.fixture
def email_config(db):
    """创建默认邮件配置"""
    config = EmailConfig()
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@pytest.fixture
def test_department(db):
    """创建测试部门"""
    dept = Department(
        name="测试部门",
        sort=0,
        status=0,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@pytest.fixture
def test_role(db):
    """创建测试角色"""
    role = Role(
        name="测试角色",
        code="test_role",
        status=0,
        remark="用于测试的角色",
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role
