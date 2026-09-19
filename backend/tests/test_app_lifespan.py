"""app/__init__.py — create_app / custom_generate_unique_id / lifespan_context 测试"""

from unittest.mock import AsyncMock, MagicMock, patch


class TestCustomGenerateUniqueId:
    def test_builds_id_from_tag_and_name(self):
        from app import custom_generate_unique_id

        route = MagicMock()
        route.tags = ["用户模块"]
        route.name = "get_user"
        assert custom_generate_unique_id(route) == "用户模块-get_user"


class TestCreateApp:
    def test_create_app_registers_routes(self):
        from app import create_app

        application = create_app()
        assert application.title
        assert application.openapi_url == "/openapi.json"

    def test_sentry_init_when_configured(self, monkeypatch):
        import importlib

        import app as app_module

        monkeypatch.setattr(app_module.settings, "SENTRY_DSN", "https://x@y.ingest.sentry.io/1", raising=False)
        monkeypatch.setattr(app_module.settings, "ENVIRONMENT", "production", raising=False)
        with patch.object(app_module.sentry_sdk, "init") as mock_init:
            importlib.reload(app_module)
            mock_init.assert_called_once()
        monkeypatch.undo()
        importlib.reload(app_module)


class TestLifespan:
    async def _run(self):
        from app import lifespan_context

        app = MagicMock()
        with (
            patch("app.core.redis.init_redis", AsyncMock()),
            patch("app.core.redis.close_redis", AsyncMock()),
            patch("app.init_data", AsyncMock()),
        ):
            async with lifespan_context(app) as ctx:
                assert ctx is None

    def test_lifespan_startup_shutdown(self):
        import asyncio

        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(self._run())
