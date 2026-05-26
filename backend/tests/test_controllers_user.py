"""controllers/user.py 单元测试 — 登录失败/账号锁定/更新/解锁"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, Request
from sqlmodel import Session, SQLModel, create_engine, select
from unittest.mock import Mock, AsyncMock, patch

from app.controllers.user import userController
from app.models import User, UserCreate, UserUpdate
from app.models.login import CredentialsSchema
from app.models.security import SecurityPolicy
from app.utils.password import get_password_hash


# ─── 独立内存 DB ─────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def user_engine():
    _engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture
def user_session(user_engine):
    from sqlalchemy import event
    connection = user_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _mock_request():
    """创建模拟 Request 对象"""
    req = Mock(spec=Request)
    req.client = Mock()
    req.client.host = "127.0.0.1"
    req.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"}
    return req


# ═══════════════════════════════════════════════════════════════════════
# create — 密码策略校验
# ═══════════════════════════════════════════════════════════════════════

class TestUserCreate:
    @pytest.mark.asyncio
    async def test_create_with_strict_policy(self, user_session):
        policy = SecurityPolicy(
            min_password_length=8, require_uppercase=True,
            require_lowercase=True, require_digit=True, require_special=True,
        )
        user_session.add(policy)
        user_session.commit()

        user_in = UserCreate(
            username="policyuser", nickname="P", email="policy@test.com",
            password="Admin@123", phone="13800000001", remark="test",
        )
        user = await userController.create(user_session, user_in)
        assert user.id is not None

    @pytest.mark.asyncio
    async def test_create_weak_password_raises(self, user_session):
        policy = SecurityPolicy(min_password_length=12)
        user_session.add(policy)
        user_session.commit()

        user_in = UserCreate(
            username="weakuser", nickname="W", email="weak@test.com",
            password="longbutnouppercase",  # 满足 min_length=8 但不满足 require_uppercase
            phone="13800000002", remark="test",
        )
        # 使用策略开启 require_uppercase
        policy2 = SecurityPolicy(min_password_length=8, require_uppercase=True)
        user_session.add(policy2)
        user_session.commit()

        user_in2 = UserCreate(
            username="weakuser2", nickname="W2", email="weak2@test.com",
            password="alllowercase123",  # 无大写
            phone="13800000012", remark="test",
        )
        with pytest.raises(HTTPException) as exc_info:
            await userController.create(user_session, user_in2)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_with_password_history(self, user_session):
        policy = SecurityPolicy(password_history_count=3)
        user_session.add(policy)
        user_session.commit()

        user_in = UserCreate(
            username="histuser", nickname="H", email="hist@test.com",
            password="History123", phone="13800000003", remark="test",
        )
        user = await userController.create(user_session, user_in)
        assert user.password_history is not None
        assert len(user.password_history) == 1


# ═══════════════════════════════════════════════════════════════════════
# update — 含密码更新
# ═══════════════════════════════════════════════════════════════════════

class TestUserUpdate:
    @pytest.mark.asyncio
    async def test_update_basic_fields(self, user_session):
        user = User(
            username="upuser", nickname="Up", email="up@test.com",
            password=get_password_hash("old12345678"), phone="13800000010", remark="old",
        )
        user_session.add(user)
        user_session.commit()
        user_session.refresh(user)

        update = UserUpdate(
            username="upuser", nickname="Updated", email="up2@test.com",
            phone="13800000011",
        )
        result = await userController.update(user_session, user.id, update)
        assert result is not None
        assert result.nickname == "Updated"

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, user_session):
        update = UserUpdate(username="ghost", nickname="G", email="g@g.com")
        result = await userController.update(user_session, uuid4(), update)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════
# authenticate — 登录核心路径
# ═══════════════════════════════════════════════════════════════════════

class TestUserAuthenticate:
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, user_session):
        """用户不存在 → 400"""
        req = _mock_request()
        cred = CredentialsSchema(username="ghost", password="whatever")
        with patch("app.controllers.user.getIpAddress", new_callable=AsyncMock, return_value=""):
            with patch("app.controllers.user.getReqSysBro", new_callable=AsyncMock, return_value=Mock(system="Win", browser="Chrome")):
                with pytest.raises(HTTPException) as exc_info:
                    await userController.authenticate(user_session, cred, req)
                assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_authenticate_locked_account(self, user_session):
        """已锁定账号（锁定未过期）→ 400"""
        user = User(
            username="lockeduser", nickname="L", email="locked@test.com",
            password=get_password_hash("Locked12345"), phone="13800000020",
            remark="test", status=1, is_superuser=False,
            locked_until=datetime.now() + timedelta(minutes=30),
            failed_login_count=0,
        )
        user_session.add(user)
        user_session.commit()

        req = _mock_request()
        cred = CredentialsSchema(username="lockeduser", password="Locked12345")
        with patch("app.controllers.user.getIpAddress", new_callable=AsyncMock, return_value=""):
            with patch("app.controllers.user.getReqSysBro", new_callable=AsyncMock, return_value=Mock(system="Win", browser="Chrome")):
                with pytest.raises(HTTPException) as exc_info:
                    await userController.authenticate(user_session, cred, req)
                assert "锁定" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_expired_lock_resets(self, user_session):
        """锁定已过期 → 重置锁定，允许登录"""
        user = User(
            username="expiredlock", nickname="EL", email="el@test.com",
            password=get_password_hash("ExpiredLock123"), phone="13800000021",
            remark="test", status=1, is_superuser=False,
            locked_until=datetime.now() - timedelta(minutes=1),  # 已过期
            failed_login_count=3,
        )
        user_session.add(user)
        user_session.commit()

        req = _mock_request()
        cred = CredentialsSchema(username="expiredlock", password="ExpiredLock123")
        with patch("app.controllers.user.getIpAddress", new_callable=AsyncMock, return_value=""):
            with patch("app.controllers.user.getReqSysBro", new_callable=AsyncMock, return_value=Mock(system="Win", browser="Chrome")):
                with patch("app.controllers.user.logger") as mock_logger:
                    mock_logger.loginSuccess = AsyncMock()
                    result = await userController.authenticate(user_session, cred, req)
                    assert result.username == "expiredlock"
                    assert result.failed_login_count == 0

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password_increments_count(self, user_session):
        """密码错误 → 失败次数 +1"""
        user = User(
            username="failuser", nickname="F", email="fail@test.com",
            password=get_password_hash("Right12345"), phone="13800000022",
            remark="test", status=1, is_superuser=False,
            failed_login_count=0,
        )
        user_session.add(user)
        policy = SecurityPolicy(max_login_attempts=5, lockout_duration_minutes=30)
        user_session.add(policy)
        user_session.commit()

        req = _mock_request()
        cred = CredentialsSchema(username="failuser", password="Wrong12345")
        with patch("app.controllers.user.getIpAddress", new_callable=AsyncMock, return_value=""):
            with patch("app.controllers.user.getReqSysBro", new_callable=AsyncMock, return_value=Mock(system="Win", browser="Chrome")):
                with patch("app.controllers.user.logger") as mock_logger:
                    mock_logger.loginFail = AsyncMock()
                    with pytest.raises(HTTPException):
                        await userController.authenticate(user_session, cred, req)

        user_session.refresh(user)
        assert user.failed_login_count == 1

    @pytest.mark.asyncio
    async def test_authenticate_max_failures_locks_account(self, user_session):
        """连续失败达到上限 → 账号锁定"""
        user = User(
            username="maxfail", nickname="MF", email="mf@test.com",
            password=get_password_hash("Right12345"), phone="13800000023",
            remark="test", status=1, is_superuser=False,
            failed_login_count=4,  # 已失败 4 次
        )
        user_session.add(user)
        policy = SecurityPolicy(max_login_attempts=5, lockout_duration_minutes=30)
        user_session.add(policy)
        user_session.commit()

        req = _mock_request()
        cred = CredentialsSchema(username="maxfail", password="Wrong12345")
        with patch("app.controllers.user.getIpAddress", new_callable=AsyncMock, return_value=""):
            with patch("app.controllers.user.getReqSysBro", new_callable=AsyncMock, return_value=Mock(system="Win", browser="Chrome")):
                with patch("app.controllers.user.logger") as mock_logger:
                    mock_logger.loginFail = AsyncMock()
                    with pytest.raises(HTTPException) as exc_info:
                        await userController.authenticate(user_session, cred, req)
                    assert "锁定" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_superuser_wrong_password(self, user_session):
        """超级管理员密码错误 → 直接报错，不计数"""
        user = User(
            username="supadmin", nickname="SA", email="sa@test.com",
            password=get_password_hash("Super12345"), phone="13800000024",
            remark="test", status=1, is_superuser=True,
        )
        user_session.add(user)
        user_session.commit()

        req = _mock_request()
        cred = CredentialsSchema(username="supadmin", password="Wrong12345")
        with patch("app.controllers.user.getIpAddress", new_callable=AsyncMock, return_value=""):
            with patch("app.controllers.user.getReqSysBro", new_callable=AsyncMock, return_value=Mock(system="Win", browser="Chrome")):
                with patch("app.controllers.user.logger") as mock_logger:
                    mock_logger.loginFail = AsyncMock()
                    with pytest.raises(HTTPException) as exc_info:
                        await userController.authenticate(user_session, cred, req)
                    assert exc_info.value.status_code == 400
                    # 超级管理员不应被计数
                    user_session.refresh(user)
                    assert user.failed_login_count == 0

    @pytest.mark.asyncio
    async def test_authenticate_disabled_user(self, user_session):
        """禁用用户正确密码 → 400"""
        user = User(
            username="disabledauth", nickname="DA", email="da@test.com",
            password=get_password_hash("Disabled12345"), phone="13800000025",
            remark="test", status=0, is_superuser=False,
        )
        user_session.add(user)
        user_session.commit()

        req = _mock_request()
        cred = CredentialsSchema(username="disabledauth", password="Disabled12345")
        with patch("app.controllers.user.getIpAddress", new_callable=AsyncMock, return_value=""):
            with patch("app.controllers.user.getReqSysBro", new_callable=AsyncMock, return_value=Mock(system="Win", browser="Chrome")):
                with patch("app.controllers.user.logger") as mock_logger:
                    mock_logger.loginSuccess = AsyncMock()
                    with pytest.raises(HTTPException) as exc_info:
                        await userController.authenticate(user_session, cred, req)
                    assert "禁用" in exc_info.value.detail


# ═══════════════════════════════════════════════════════════════════════
# 其他方法
# ═══════════════════════════════════════════════════════════════════════

class TestUserMisc:
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_session):
        user = User(
            username="emailfind", nickname="EF", email="findme@test.com",
            password=get_password_hash("Find12345"), phone="13800000030", remark="test",
        )
        user_session.add(user)
        user_session.commit()

        result = await userController.get_user_by_email(user_session, "findme@test.com")
        assert result is not None
        assert result.username == "emailfind"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_session):
        result = await userController.get_user_by_email(user_session, "nobody@test.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_unlock_user(self, user_session):
        user = User(
            username="unlockme", nickname="UL", email="ul@test.com",
            password=get_password_hash("Unlock12345"), phone="13800000031", remark="test",
            failed_login_count=5, locked_until=datetime.now() + timedelta(minutes=30),
        )
        user_session.add(user)
        user_session.commit()

        result = await userController.unlock_user(user_session, user.id)
        assert result is not None
        assert result.failed_login_count == 0
        assert result.locked_until is None

    @pytest.mark.asyncio
    async def test_unlock_nonexistent_user(self, user_session):
        result = await userController.unlock_user(user_session, uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_last_login(self, user_session):
        user = User(
            username="lastlogin", nickname="LL", email="ll@test.com",
            password=get_password_hash("Last12345"), phone="13800000032", remark="test",
        )
        user_session.add(user)
        user_session.commit()

        result = await userController.update_last_login(user_session, user.id)
        assert result.last_login is not None
