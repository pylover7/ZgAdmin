"""utils/jwtt.py 单元测试 — JWT 创建/解码、OAuth state"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.models import User
from app.models.login import JWTPayload
from app.settings import settings
from app.utils.jwtt import (
    blacklist_token,
    create_access_token,
    create_oauth_state,
    create_token_pair,
    decode_access_token,
    find_or_create_qq_user,
    get_qq_access_token,
    get_qq_userinfo,
    validate_token_and_get_user,
    validate_user_status,
    verify_oauth_state,
)


class TestCreateAccessToken:
    def test_returns_valid_jwt(self):
        payload = JWTPayload(
            user_id="test-user-id",
            username="testuser",
            is_superuser=False,
            exp=datetime.now(UTC) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_decodable(self):
        payload = JWTPayload(
            user_id="abc-123",
            username="admin",
            is_superuser=True,
            exp=datetime.now(UTC) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        decoded = decode_access_token(token)
        assert decoded.user_id == "abc-123"
        assert decoded.username == "admin"
        assert decoded.is_superuser is True

    def test_token_contains_exp(self):
        exp_time = datetime.now(UTC) + timedelta(hours=2)
        payload = JWTPayload(
            user_id="x",
            username="y",
            is_superuser=False,
            exp=exp_time,
        )
        token = create_access_token(data=payload)
        decoded_raw = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert "exp" in decoded_raw


class TestDecodeAccessToken:
    def test_valid_token(self):
        payload = JWTPayload(
            user_id="user-1",
            username="testuser",
            is_superuser=False,
            exp=datetime.now(UTC) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        decoded = decode_access_token(token)
        assert decoded.user_id == "user-1"
        assert decoded.username == "testuser"

    def test_expired_token_raises(self):
        payload = JWTPayload(
            user_id="expired",
            username="expired_user",
            is_superuser=False,
            exp=datetime.now(UTC) - timedelta(seconds=1),
        )
        token = create_access_token(data=payload)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token("invalid.token.string")

    def test_tampered_signature_raises(self):
        payload = JWTPayload(
            user_id="tamper",
            username="tamper_user",
            is_superuser=False,
            exp=datetime.now(UTC) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        tampered = token + "x"
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token(tampered)


class TestOAuthState:
    def test_create_and_verify(self):
        state = create_oauth_state(purpose="qq_login")
        assert verify_oauth_state(state, purpose="qq_login") is True

    def test_wrong_purpose_fails(self):
        state = create_oauth_state(purpose="qq_login")
        assert verify_oauth_state(state, purpose="wechat_login") is False

    def test_expired_state_fails(self):
        _state = create_oauth_state(purpose="qq_login")
        # 手动构造已过期的 state
        expired_payload = {
            "purpose": "qq_login",
            "nonce": "test",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        }
        expired_state = pyjwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert verify_oauth_state(expired_state, purpose="qq_login") is False

    def test_invalid_state_returns_false(self):
        assert verify_oauth_state("invalid_state_token", purpose="qq_login") is False


class TestCreateTokenPair:
    @pytest.mark.asyncio
    async def test_creates_pair(self):
        pair = await create_token_pair("uid", "uname", True)
        assert pair.accessToken and pair.refreshToken
        assert pair.expires < pair.refreshExpires
        decoded = decode_access_token(pair.accessToken)
        assert decoded.user_id == "uid"
        assert decoded.is_superuser is True


class TestValidateUserStatus:
    def _user(self, is_superuser=False, status=1, role_status=1):
        role = MagicMock()
        role.status = role_status
        user = MagicMock(spec=User)
        user.is_superuser = is_superuser
        user.status = status
        user.roles = [role]
        return user

    def test_superuser_always_ok(self):
        assert validate_user_status(self._user(is_superuser=True, status=0)) is None

    def test_disabled_user(self):
        assert validate_user_status(self._user(status=0)) == "用户已被禁用"

    def test_disabled_role(self):
        assert validate_user_status(self._user(role_status=0)) == "用户已被禁用"

    def test_ok(self):
        assert validate_user_status(self._user()) is None


class TestValidateTokenAndGetUser:
    @pytest.mark.asyncio
    async def test_blacklisted_token(self, db, test_redis):
        import hashlib

        token = create_access_token(
            data=JWTPayload(user_id="x", username="y", is_superuser=False, exp=datetime.now(UTC) + timedelta(hours=1))
        )
        await test_redis.set(f"token:blacklist:{hashlib.sha256(token.encode()).hexdigest()[:16]}", "1", ex=60)
        with pytest.raises(HTTPException) as exc:
            await validate_token_and_get_user(token, db)
        assert exc.value.status_code == 401
        assert "失效" in exc.value.detail

    @pytest.mark.asyncio
    async def test_expired_token(self, db, test_redis):
        token = create_access_token(
            data=JWTPayload(user_id="x", username="y", is_superuser=False, exp=datetime.now(UTC) - timedelta(hours=1))
        )
        with pytest.raises(HTTPException) as exc:
            await validate_token_and_get_user(token, db)
        assert exc.value.detail == "登录已过期"

    @pytest.mark.asyncio
    async def test_invalid_token(self, db, test_redis):
        with pytest.raises(HTTPException) as exc:
            await validate_token_and_get_user("garbage", db)
        assert exc.value.detail == "无效的Token"

    @pytest.mark.asyncio
    async def test_missing_user_id(self, db, test_redis):
        token = pyjwt.encode(
            {"username": "y", "exp": datetime.now(UTC) + timedelta(hours=1)},
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            await validate_token_and_get_user(token, db)
        assert exc.value.detail == "Token格式错误"

    @pytest.mark.asyncio
    async def test_user_not_found(self, db, test_redis):
        token = create_access_token(
            data=JWTPayload(
                user_id="00000000-0000-0000-0000-000000000000",
                username="y",
                is_superuser=False,
                exp=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        with pytest.raises(HTTPException) as exc:
            await validate_token_and_get_user(token, db)
        assert exc.value.detail == "用户不存在"

    @pytest.mark.asyncio
    async def test_disabled_user_raises(self, db, test_redis, admin_user):
        admin_user.is_superuser = False
        admin_user.status = 0
        db.add(admin_user)
        db.commit()
        token = create_access_token(
            data=JWTPayload(
                user_id=str(admin_user.id), username="u", is_superuser=False, exp=datetime.now(UTC) + timedelta(hours=1)
            )
        )
        with pytest.raises(HTTPException) as exc:
            await validate_token_and_get_user(token, db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_success(self, db, test_redis, admin_user):
        token = create_access_token(
            data=JWTPayload(
                user_id=str(admin_user.id),
                username="u",
                is_superuser=True,
                exp=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        user = await validate_token_and_get_user(token, db)
        assert user.id == admin_user.id


class TestBlacklistToken:
    @pytest.mark.asyncio
    async def test_expired_token_silently_skipped(self, test_redis):
        token = create_access_token(
            data=JWTPayload(user_id="x", username="y", is_superuser=False, exp=datetime.now(UTC) - timedelta(hours=1))
        )
        await blacklist_token(token)

    @pytest.mark.asyncio
    async def test_invalid_token_silently_skipped(self, test_redis):
        await blacklist_token("not-a-token")

    @pytest.mark.asyncio
    async def test_valid_token_stored(self, test_redis):
        import hashlib

        token = create_access_token(
            data=JWTPayload(user_id="x", username="y", is_superuser=False, exp=datetime.now(UTC) + timedelta(hours=1))
        )
        await blacklist_token(token)
        key = f"token:blacklist:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
        assert await test_redis.exists(key)


class _FakeOAuthConfig:
    qq_app_id = "cid"
    qq_app_key = "ckey"
    qq_redirect_uri = "https://example.com/cb"


def _patch_oauth_session(monkeypatch, config=None):
    session = MagicMock()
    session.exec.return_value.first.return_value = config
    ctx = MagicMock()
    ctx.__enter__.return_value = session
    ctx.__exit__.return_value = False
    monkeypatch.setattr("app.utils.jwtt.DatabaseSession", lambda: ctx)


def _patch_http(monkeypatch, response=None, error=None):
    client = AsyncMock()
    if error is not None:
        client.__aenter__.return_value.get = AsyncMock(side_effect=error)
    else:
        client.__aenter__.return_value.get = AsyncMock(return_value=response)
    client.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr("app.utils.jwtt.httpx.AsyncClient", lambda **kw: client)


class TestGetQqAccessToken:
    @pytest.mark.asyncio
    async def test_success(self, monkeypatch):
        _patch_oauth_session(monkeypatch, _FakeOAuthConfig())
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "access_token=AT&expires_in=7776000&refresh_token=RT&openid=OID&scope=s"
        _patch_http(monkeypatch, resp)
        result = await get_qq_access_token("code")
        assert result.access_token == "AT"
        assert result.expires_in == 7776000
        assert result.openid == "OID"

    @pytest.mark.asyncio
    async def test_falls_back_to_settings(self, monkeypatch):
        _patch_oauth_session(monkeypatch, None)
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "access_token=AT&openid=OID"
        _patch_http(monkeypatch, resp)
        result = await get_qq_access_token("code")
        assert result.openid == "OID"

    @pytest.mark.asyncio
    async def test_non_200(self, monkeypatch):
        _patch_oauth_session(monkeypatch, _FakeOAuthConfig())
        resp = MagicMock()
        resp.status_code = 400
        _patch_http(monkeypatch, resp)
        with pytest.raises(HTTPException):
            await get_qq_access_token("code")

    @pytest.mark.asyncio
    async def test_incomplete_params(self, monkeypatch):
        _patch_oauth_session(monkeypatch, _FakeOAuthConfig())
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "no_params=1"
        _patch_http(monkeypatch, resp)
        with pytest.raises(HTTPException) as exc:
            await get_qq_access_token("code")
        assert exc.value.detail == "QQ API返回参数不完整"

    @pytest.mark.asyncio
    async def test_request_error(self, monkeypatch):
        import httpx as _httpx

        _patch_oauth_session(monkeypatch, _FakeOAuthConfig())
        _patch_http(monkeypatch, error=_httpx.RequestError("boom"))
        with pytest.raises(HTTPException) as exc:
            await get_qq_access_token("code")
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_non_digit_expires(self, monkeypatch):
        _patch_oauth_session(monkeypatch, _FakeOAuthConfig())
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "access_token=AT&openid=OID&expires_in=abc"
        _patch_http(monkeypatch, resp)
        result = await get_qq_access_token("code")
        assert result.expires_in == 0


class TestGetQqUserInfo:
    @pytest.mark.asyncio
    async def test_success_hd_avatar(self, monkeypatch):
        _patch_oauth_session(monkeypatch, _FakeOAuthConfig())
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "ret": 0,
            "nickname": "昵称",
            "figureurl_qq_2": "hd.jpg",
            "figureurl_qq_1": "sd.jpg",
        }
        _patch_http(monkeypatch, resp)
        info = await get_qq_userinfo("AT", "OID")
        assert info.avatar == "hd.jpg"
        assert info.nickname == "昵称"

    @pytest.mark.asyncio
    async def test_fallback_avatar_and_default_nickname(self, monkeypatch):
        _patch_oauth_session(monkeypatch, None)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"ret": 0, "figureurl_qq_1": "sd.jpg"}
        _patch_http(monkeypatch, resp)
        info = await get_qq_userinfo("AT", "OID")
        assert info.avatar == "sd.jpg"
        assert info.nickname == "QQ用户"

    @pytest.mark.asyncio
    async def test_api_error_ret(self, monkeypatch):
        _patch_oauth_session(monkeypatch, None)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"ret": 1, "msg": "bad"}
        _patch_http(monkeypatch, resp)
        with pytest.raises(HTTPException) as exc:
            await get_qq_userinfo("AT", "OID")
        assert "bad" in exc.value.detail

    @pytest.mark.asyncio
    async def test_non_200(self, monkeypatch):
        _patch_oauth_session(monkeypatch, None)
        resp = MagicMock()
        resp.status_code = 500
        _patch_http(monkeypatch, resp)
        with pytest.raises(HTTPException):
            await get_qq_userinfo("AT", "OID")

    @pytest.mark.asyncio
    async def test_request_error(self, monkeypatch):
        import httpx as _httpx

        _patch_oauth_session(monkeypatch, None)
        _patch_http(monkeypatch, error=_httpx.RequestError("boom"))
        with pytest.raises(HTTPException) as exc:
            await get_qq_userinfo("AT", "OID")
        assert exc.value.status_code == 500


class TestFindOrCreateQqUser:
    @pytest.mark.asyncio
    async def test_creates_new_user(self, db):
        info = MagicMock()
        info.openid = "OID12345"
        info.nickname = "新用户"
        info.avatar = "a.jpg"
        user = await find_or_create_qq_user(db, info)
        assert user.qq_openid == "OID12345"
        assert user.nickname == "新用户"
        assert user.qq_avatar == "a.jpg"

    @pytest.mark.asyncio
    async def test_creates_without_nickname(self, db):
        info = MagicMock()
        info.openid = "OID99999"
        info.nickname = ""
        info.avatar = ""
        user = await find_or_create_qq_user(db, info)
        assert user.nickname.startswith("QQ用户_")

    @pytest.mark.asyncio
    async def test_updates_existing_user(self, db):
        info = MagicMock()
        info.openid = "OIDUPD"
        info.nickname = "first"
        info.avatar = "a.jpg"
        user = await find_or_create_qq_user(db, info)
        info.nickname = "second"
        info.avatar = "b.jpg"
        updated = await find_or_create_qq_user(db, info)
        assert updated.id == user.id
        assert updated.nickname == "second"
        assert updated.qq_avatar == "b.jpg"

    @pytest.mark.asyncio
    async def test_error_rolls_back(self, db):
        info = MagicMock()
        info.openid = "OIDERR"
        info.nickname = "x"
        info.avatar = ""
        with (
            patch("app.utils.jwtt.User", side_effect=RuntimeError("db down")),
            pytest.raises(HTTPException) as exc,
        ):
            await find_or_create_qq_user(db, info)
        assert exc.value.status_code == 500
