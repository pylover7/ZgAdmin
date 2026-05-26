"""core/middlewares.py 单元测试 — IP 过滤中间件"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from app.core.middlewares import IPFilterMiddleware, BackGroundTaskMiddleware, SimpleBaseMiddleware


class TestIPFilterMiddleware:
    @pytest.fixture
    def middleware(self):
        mock_app = Mock()
        return IPFilterMiddleware(mock_app)

    def test_get_client_ip_forwarded(self, middleware):
        req = Mock()
        req.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        assert middleware._get_client_ip(req) == "1.2.3.4"

    def test_get_client_ip_real_ip(self, middleware):
        req = Mock()
        req.headers = {"X-Real-IP": "9.8.7.6"}
        assert middleware._get_client_ip(req) == "9.8.7.6"

    def test_get_client_ip_direct(self, middleware):
        req = Mock()
        req.headers = {}
        req.client = Mock()
        req.client.host = "10.0.0.1"
        assert middleware._get_client_ip(req) == "10.0.0.1"

    def test_get_client_ip_no_client(self, middleware):
        req = Mock()
        req.headers = {}
        req.client = None
        assert middleware._get_client_ip(req) == "unknown"

    def test_ip_matches_cidr_exact(self, middleware):
        assert middleware._ip_matches_cidr("1.2.3.4", "1.2.3.4") is True
        assert middleware._ip_matches_cidr("1.2.3.4", "5.6.7.8") is False

    def test_ip_matches_cidr_network(self, middleware):
        assert middleware._ip_matches_cidr("192.168.1.100", "192.168.1.0/24") is True
        assert middleware._ip_matches_cidr("192.168.2.1", "192.168.1.0/24") is False

    def test_ip_matches_cidr_invalid_ip(self, middleware):
        assert middleware._ip_matches_cidr("invalid", "192.168.1.0/24") is False

    def test_ip_matches_cidr_invalid_cidr(self, middleware):
        assert middleware._ip_matches_cidr("1.2.3.4", "not-a-cidr") is False

    @pytest.mark.asyncio
    async def test_get_rules_from_redis_cache(self, middleware):
        """从 Redis 缓存获取规则"""
        mock_redis = AsyncMock()
        cached_data = json.dumps([{"ip_cidr": "1.2.3.4", "rule_type": "blacklist"}])
        mock_redis.get = AsyncMock(return_value=cached_data)

        with patch("app.core.middlewares.get_redis", return_value=mock_redis):
            rules = await middleware._get_rules()
        assert len(rules) == 1
        assert rules[0]["ip_cidr"] == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_get_rules_empty_cache(self, middleware):
        """Redis 无缓存 → 返回空列表（因为测试 DB 无数据）"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch("app.core.middlewares.get_redis", return_value=mock_redis):
            rules = await middleware._get_rules()
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_before_request_health_path(self, middleware):
        """健康检查路径放行"""
        req = Mock()
        req.url.path = "/api/v1/base/health"
        req.headers = {}
        req.client = Mock()
        req.client.host = "1.2.3.4"
        result = await middleware.before_request(req)
        assert result == middleware.app

    @pytest.mark.asyncio
    async def test_before_request_openapi(self, middleware):
        req = Mock()
        req.url.path = "/openapi.json"
        req.headers = {}
        req.client = Mock()
        req.client.host = "1.2.3.4"
        result = await middleware.before_request(req)
        assert result == middleware.app

    @pytest.mark.asyncio
    async def test_before_request_docs(self, middleware):
        req = Mock()
        req.url.path = "/docs"
        req.headers = {}
        req.client = Mock()
        req.client.host = "1.2.3.4"
        result = await middleware.before_request(req)
        assert result == middleware.app

    @pytest.mark.asyncio
    async def test_before_request_no_rules(self, middleware):
        """无规则 → 放行"""
        req = Mock()
        req.url.path = "/api/v1/base/login"
        req.headers = {}
        req.client = Mock()
        req.client.host = "1.2.3.4"

        with patch.object(middleware, '_get_rules', new_callable=AsyncMock, return_value=[]):
            result = await middleware.before_request(req)
        assert result == middleware.app

    @pytest.mark.asyncio
    async def test_before_request_blacklisted(self, middleware):
        """黑名单 IP → 403"""
        from starlette.responses import JSONResponse

        req = Mock()
        req.url.path = "/api/v1/base/login"
        req.headers = {"X-Forwarded-For": "10.0.0.1"}
        req.client = Mock()
        req.client.host = "10.0.0.1"

        rules = [{"ip_cidr": "10.0.0.1", "rule_type": "blacklist"}]
        with patch.object(middleware, '_get_rules', new_callable=AsyncMock, return_value=rules):
            result = await middleware.before_request(req)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 403

    @pytest.mark.asyncio
    async def test_before_request_whitelist_mismatch(self, middleware):
        """白名单不匹配 → 403"""
        from starlette.responses import JSONResponse

        req = Mock()
        req.url.path = "/api/v1/base/login"
        req.headers = {"X-Forwarded-For": "10.0.0.1"}
        req.client = Mock()
        req.client.host = "10.0.0.1"

        rules = [{"ip_cidr": "192.168.1.0/24", "rule_type": "whitelist"}]
        with patch.object(middleware, '_get_rules', new_callable=AsyncMock, return_value=rules):
            result = await middleware.before_request(req)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 403

    @pytest.mark.asyncio
    async def test_before_request_whitelist_match(self, middleware):
        """白名单匹配 → 放行"""
        req = Mock()
        req.url.path = "/api/v1/base/login"
        req.headers = {"X-Forwarded-For": "192.168.1.5"}
        req.client = Mock()
        req.client.host = "192.168.1.5"

        rules = [{"ip_cidr": "192.168.1.0/24", "rule_type": "whitelist"}]
        with patch.object(middleware, '_get_rules', new_callable=AsyncMock, return_value=rules):
            result = await middleware.before_request(req)
        assert result == middleware.app

    @pytest.mark.asyncio
    async def test_before_request_rules_load_error(self, middleware):
        """规则加载失败 → 放行"""
        req = Mock()
        req.url.path = "/api/v1/base/login"
        req.headers = {}
        req.client = Mock()
        req.client.host = "1.2.3.4"

        with patch.object(middleware, '_get_rules', new_callable=AsyncMock, side_effect=Exception("DB error")):
            result = await middleware.before_request(req)
        assert result == middleware.app


class TestBackGroundTaskMiddleware:
    @pytest.mark.asyncio
    async def test_before_request(self):
        from app.core.bgtask import BgTasks
        middleware = BackGroundTaskMiddleware(Mock())
        req = Mock()
        with patch.object(BgTasks, "init_bg_tasks_obj", new_callable=AsyncMock):
            await middleware.before_request(req)

    @pytest.mark.asyncio
    async def test_after_request(self):
        from app.core.bgtask import BgTasks
        middleware = BackGroundTaskMiddleware(Mock())
        req = Mock()
        with patch.object(BgTasks, "execute_tasks", new_callable=AsyncMock):
            await middleware.after_request(req)


class TestSimpleBaseMiddleware:
    @pytest.mark.asyncio
    async def test_before_request_default(self):
        middleware = SimpleBaseMiddleware(Mock())
        result = await middleware.before_request(Mock())
        assert result == middleware.app

    @pytest.mark.asyncio
    async def test_after_request_default(self):
        middleware = SimpleBaseMiddleware(Mock())
        result = await middleware.after_request(Mock())
        assert result is None
