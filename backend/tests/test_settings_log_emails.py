"""settings/log.py 与 utils/emails.py 单元测试"""

import sys
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import SQLModel, create_engine
from sqlmodel.pool import StaticPool

import app.core as core_module
from app.settings import settings
from app.settings.log import Logger, logger
from app.utils.emails import send_email

log_module = sys.modules["app.settings.log"]


def _mem_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.logs  # noqa: F401

    SQLModel.metadata.create_all(engine)
    return engine


class TestLoginType:
    def test_all_variants(self):
        assert logger.loginType(0) == "账号登录"
        assert logger.loginType(1) == "微信登录"
        assert logger.loginType(2) == "QQ登录"
        assert logger.loginType(3) == "手机号登录"
        assert logger.loginType(99) == "未知登录"


class TestSyncLogMethods:
    def test_levels(self):
        log = Logger()
        for method in (log.info, log.debug, log.warning, log.error, log.success):
            assert method("hello") is None


class TestSystemLogs:
    @pytest.mark.asyncio
    async def test_monitor_off_returns_early(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_MONITOR_LOG", False)
        await logger.systemInfo("m", "msg")
        await logger.systemWarning("m", "msg")
        await logger.systemError("m", "msg")
        await logger.systemDebug("m", "msg")

    @pytest.mark.asyncio
    async def test_monitor_on_writes_db(self, monkeypatch):
        engine = _mem_engine()
        monkeypatch.setattr(core_module, "engine", engine, raising=False)
        monkeypatch.setattr(settings, "FEATURE_MONITOR_LOG", True)
        monkeypatch.setattr(log_module, "engine", engine, raising=False)
        await logger.systemInfo("m", "msg")
        await logger.systemWarning("m", "msg")
        await logger.systemError("m", "msg")
        await logger.systemDebug("m", "msg")


class TestLoginAndOperationLogs:
    @pytest.mark.asyncio
    async def test_login_monitor_off(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_MONITOR_LOG", False)
        await logger.loginSuccess("u", "1.1.1.1", "addr", "sys", "br", 0)
        await logger.loginFail("u", "1.1.1.1", "addr", "sys", "br", 1)

    @pytest.mark.asyncio
    async def test_login_monitor_on(self, monkeypatch):
        engine = _mem_engine()
        monkeypatch.setattr(log_module, "engine", engine, raising=False)
        monkeypatch.setattr(settings, "FEATURE_MONITOR_LOG", True)
        await logger.loginSuccess("u", "1.1.1.1", "addr", "sys", "br", 0)
        await logger.loginFail("u", "1.1.1.1", "addr", "sys", "br", 2)

    @pytest.mark.asyncio
    async def test_operation_monitor_off(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_MONITOR_LOG", False)
        await logger.operationInfo("u", "msg")
        await logger.operationWarning("u", "msg")
        await logger.operationError("u", "msg")

    @pytest.mark.asyncio
    async def test_operation_monitor_on(self, monkeypatch):
        engine = _mem_engine()
        monkeypatch.setattr(log_module, "engine", engine, raising=False)
        monkeypatch.setattr(settings, "FEATURE_MONITOR_LOG", True)
        await logger.operationInfo("u", "msg")
        await logger.operationWarning("u", "msg")
        await logger.operationError("u", "msg")


class TestSendEmail:
    @pytest.mark.asyncio
    async def test_feature_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_EMAIL", False)
        assert await send_email("a@b.com", "s", "body") is False

    @pytest.mark.asyncio
    async def test_no_config(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_EMAIL", True)
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        ctx = MagicMock()
        ctx.__enter__.return_value = session
        ctx.__exit__.return_value = False
        with patch("app.utils.emails.DatabaseSession", return_value=ctx):
            assert await send_email("a@b.com", "s", "body") is False

    @pytest.mark.asyncio
    async def test_config_without_host(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_EMAIL", True)
        config = MagicMock()
        config.host = ""
        session = MagicMock()
        session.exec.return_value.first.return_value = config
        ctx = MagicMock()
        ctx.__enter__.return_value = session
        ctx.__exit__.return_value = False
        with patch("app.utils.emails.DatabaseSession", return_value=ctx):
            assert await send_email("a@b.com", "s", "body") is False

    @pytest.mark.asyncio
    async def test_send_success(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_EMAIL", True)
        config = MagicMock()
        config.host = "smtp.example.com"
        config.port = 25
        config.use_tls = True
        config.username = "u"
        config.password = "p"
        config.sender = "s@example.com"
        session = MagicMock()
        session.exec.return_value.first.return_value = config
        ctx = MagicMock()
        ctx.__enter__.return_value = session
        ctx.__exit__.return_value = False
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        with (
            patch("app.utils.emails.DatabaseSession", return_value=ctx),
            patch("app.utils.emails.smtplib.SMTP", return_value=smtp),
        ):
            assert await send_email("a@b.com", "s", "body") is True
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_failure(self, monkeypatch):
        monkeypatch.setattr(settings, "FEATURE_EMAIL", True)
        config = MagicMock()
        config.host = "smtp.example.com"
        config.port = 25
        config.use_tls = False
        config.username = "u"
        config.password = "p"
        config.sender = "s@example.com"
        session = MagicMock()
        session.exec.return_value.first.return_value = config
        ctx = MagicMock()
        ctx.__enter__.return_value = session
        ctx.__exit__.return_value = False
        with (
            patch("app.utils.emails.DatabaseSession", return_value=ctx),
            patch("app.utils.emails.smtplib.SMTP", side_effect=RuntimeError("smtp down")),
        ):
            assert await send_email("a@b.com", "s", "body") is False
