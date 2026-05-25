"""core/dependency.py 单元测试 — AuthControl / PermissionControl / RateLimiter"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.core.dependency import AuthControl, PermissionControl, RateLimiter
from app.models import User, Role, Api
from app.models.login import JWTPayload
from app.utils.jwtt import create_access_token
from app.utils.password import get_password_hash


class TestAuthControl:
    @pytest.mark.asyncio
    async def test_valid_superuser(self, db, admin_user):
        payload = JWTPayload(
            user_id=str(admin_user.id),
            username=admin_user.username,
            is_superuser=True,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        # 模拟 authorization header
        user = await AuthControl.is_authed(session=db, authorization=f"Bearer {token}")
        assert user.id == admin_user.id
        assert user.is_superuser is True

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self, db):
        with pytest.raises(HTTPException) as exc_info:
            await AuthControl.is_authed(session=db, authorization="Bearer invalid.token.here")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self, db):
        payload = JWTPayload(
            user_id="test",
            username="test",
            is_superuser=False,
            exp=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        token = create_access_token(data=payload)
        with pytest.raises(HTTPException) as exc_info:
            await AuthControl.is_authed(session=db, authorization=f"Bearer {token}")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_disabled_user_raises_400(self, db, disabled_user):
        payload = JWTPayload(
            user_id=str(disabled_user.id),
            username=disabled_user.username,
            is_superuser=False,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        with pytest.raises(HTTPException) as exc_info:
            await AuthControl.is_authed(session=db, authorization=f"Bearer {token}")
        assert exc_info.value.status_code == 400
        assert "禁用" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_401(self, db):
        payload = JWTPayload(
            user_id="00000000-0000-0000-0000-000000000000",
            username="ghost",
            is_superuser=False,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        with pytest.raises(HTTPException) as exc_info:
            await AuthControl.is_authed(session=db, authorization=f"Bearer {token}")
        assert exc_info.value.status_code == 401


class TestPermissionControl:
    @pytest.mark.asyncio
    async def test_superuser_bypasses(self, db, admin_user):
        """超级管理员无需权限检查"""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/system/user/add"
        # 不应抛异常
        await PermissionControl.has_permission(mock_request, admin_user)

    @pytest.mark.asyncio
    async def test_user_without_roles_raises_403(self, db, normal_user):
        """无角色的用户访问受保护路由 → 403"""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/system/user/add"
        with pytest.raises(HTTPException) as exc_info:
            await PermissionControl.has_permission(mock_request, normal_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_user_with_permission_passes(self, db, normal_user, test_role):
        """有权限的角色访问 → 通过"""
        # 给角色添加 API 权限
        api = Api(path="/api/v1/system/user/add", method="POST", summary="添加用户", tags="system")
        db.add(api)
        test_role.apis.append(api)
        normal_user.roles.append(test_role)
        db.add(normal_user)
        db.add(test_role)
        db.commit()

        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/system/user/add"
        # 不应抛异常
        await PermissionControl.has_permission(mock_request, normal_user)

    @pytest.mark.asyncio
    async def test_user_without_specific_permission_raises_403(self, db, normal_user, test_role):
        """角色有权限但访问无权限的路由 → 403"""
        # 给角色添加一个不相关的 API
        api = Api(path="/api/v1/system/role/list", method="POST", summary="角色列表", tags="system")
        db.add(api)
        test_role.apis.append(api)
        normal_user.roles.append(test_role)
        db.add(normal_user)
        db.add(test_role)
        db.commit()

        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/system/user/add"
        with pytest.raises(HTTPException) as exc_info:
            await PermissionControl.has_permission(mock_request, normal_user)
        assert exc_info.value.status_code == 403


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_under_limit_passes(self, test_redis):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        # 发送 4 个请求不应触发限流
        for _ in range(4):
            await limiter.check(mock_request)

    @pytest.mark.asyncio
    async def test_over_limit_raises_429(self, test_redis):
        # 清除之前的限流记录
        await test_redis.delete("rate_limit:127.0.0.2")

        limiter = RateLimiter(max_requests=3, window_seconds=60)
        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.2"
        # 发送 3 个请求
        for _ in range(3):
            await limiter.check(mock_request)
        # 第 4 个应触发限流
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check(mock_request)
        assert exc_info.value.status_code == 429
