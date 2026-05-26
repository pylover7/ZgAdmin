"""utils/jwtt.py 单元测试 — JWT 创建/解码、OAuth state"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt as pyjwt

from app.utils.jwtt import (
    create_access_token,
    decode_access_token,
    create_oauth_state,
    verify_oauth_state,
)
from app.models.login import JWTPayload
from app.settings import settings


class TestCreateAccessToken:
    def test_returns_valid_jwt(self):
        payload = JWTPayload(
            user_id="test-user-id",
            username="testuser",
            is_superuser=False,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_decodable(self):
        payload = JWTPayload(
            user_id="abc-123",
            username="admin",
            is_superuser=True,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        decoded = decode_access_token(token)
        assert decoded.user_id == "abc-123"
        assert decoded.username == "admin"
        assert decoded.is_superuser is True

    def test_token_contains_exp(self):
        exp_time = datetime.now(timezone.utc) + timedelta(hours=2)
        payload = JWTPayload(
            user_id="x", username="y", is_superuser=False, exp=exp_time,
        )
        token = create_access_token(data=payload)
        decoded_raw = pyjwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        assert "exp" in decoded_raw


class TestDecodeAccessToken:
    def test_valid_token(self):
        payload = JWTPayload(
            user_id="user-1",
            username="testuser",
            is_superuser=False,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
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
            exp=datetime.now(timezone.utc) - timedelta(seconds=1),
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
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
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
        state = create_oauth_state(purpose="qq_login")
        # 手动构造已过期的 state
        expired_payload = {
            "purpose": "qq_login",
            "nonce": "test",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_state = pyjwt.encode(
            expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        assert verify_oauth_state(expired_state, purpose="qq_login") is False

    def test_invalid_state_returns_false(self):
        assert verify_oauth_state("invalid_state_token", purpose="qq_login") is False
