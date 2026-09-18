"""utils/version.py、utils/password.py 边界、captcha、file_upload 补充测试"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.captcha import verify_captcha
from app.utils.file_upload import validate_extension, validate_mime_extension
from app.utils.password import md5_encrypt, verify_password
from app.utils.version import _strip_v, check_for_update


class _FakeSettings:
    def __init__(self, version):
        self.VERSION = version


class TestStripV:
    def test_strip(self):
        assert _strip_v("v1.2.3") == "1.2.3"
        assert _strip_v("1.2.3") == "1.2.3"


class TestCheckForUpdate:
    @pytest.mark.asyncio
    async def test_has_update(self, monkeypatch):
        monkeypatch.setattr("app.utils.version.settings", _FakeSettings("v1.0.0"))
        resp = MagicMock()
        resp.status_code = 307
        resp.headers = {"location": "https://x/releases/tag/v1.2.0"}
        client = AsyncMock()
        client.__aenter__.return_value.head = AsyncMock(return_value=resp)
        client.__aexit__ = AsyncMock(return_value=False)
        with patch("app.utils.version.httpx.AsyncClient", return_value=client):
            result = await check_for_update()
        assert result["latest_version"] == "v1.2.0"
        assert result["has_update"] is True
        assert result["release_url"].endswith("/tag/v1.2.0")

    @pytest.mark.asyncio
    async def test_no_update_and_no_match(self, monkeypatch):
        monkeypatch.setattr("app.utils.version.settings", _FakeSettings("v1.2.0"))
        resp = MagicMock()
        resp.status_code = 307
        resp.headers = {"location": "https://x/no-tag-here"}
        client = AsyncMock()
        client.__aenter__.return_value.head = AsyncMock(return_value=resp)
        client.__aexit__ = AsyncMock(return_value=False)
        with patch("app.utils.version.httpx.AsyncClient", return_value=client):
            result = await check_for_update()
        assert result["latest_version"] == "unknown"
        assert result["has_update"] is False

    @pytest.mark.asyncio
    async def test_no_release(self, monkeypatch):
        monkeypatch.setattr("app.utils.version.settings", _FakeSettings("v1.0.0"))
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        client = AsyncMock()
        client.__aenter__.return_value.head = AsyncMock(return_value=resp)
        client.__aexit__ = AsyncMock(return_value=False)
        with patch("app.utils.version.httpx.AsyncClient", return_value=client):
            result = await check_for_update()
        assert result["latest_version"] == "unknown"

    @pytest.mark.asyncio
    async def test_network_error(self, monkeypatch):
        monkeypatch.setattr("app.utils.version.settings", _FakeSettings("v1.0.0"))
        client = AsyncMock()
        client.__aenter__.return_value.head = AsyncMock(side_effect=RuntimeError("net"))
        client.__aexit__ = AsyncMock(return_value=False)
        with patch("app.utils.version.httpx.AsyncClient", return_value=client):
            result = await check_for_update()
        assert result["has_update"] is False


class TestVerifyPasswordEdges:
    def test_none_inputs(self):
        assert verify_password(None, "x") is False
        assert verify_password("x", None) is False

    def test_non_str_hash(self):
        assert verify_password("x", 12345) is False

    def test_wrong_prefix(self):
        assert verify_password("x", "$2a$" + "a" * 56) is False

    def test_wrong_length(self):
        assert verify_password("x", "$2b$short") is False

    def test_value_error_branch(self):
        # 长度/前缀合法但内容非法 → bcrypt 抛 ValueError 被捕获
        assert verify_password("x", "$2b$" + "!" * 56) is False


class TestMd5Encrypt:
    def test_none(self):
        assert md5_encrypt(None) == ""

    def test_value(self):
        assert md5_encrypt("abc") == "900150983cd24fb0d6963f7d28e17f72"


class TestValidateMimeExtension:
    def test_unknown_mime_passes(self):
        assert validate_mime_extension("application/octet-stream", "bin") == (True, None)

    def test_match(self):
        assert validate_mime_extension("image/png", "png") == (True, None)

    def test_mismatch(self):
        ok, msg = validate_mime_extension("image/png", "jpg")
        assert ok is False and "不匹配" in msg


class TestValidateExtension:
    def test_empty_filename(self):
        assert validate_extension("") == (None, "文件名无扩展名")

    def test_no_dot(self):
        assert validate_extension("README") == (None, "文件名无扩展名")

    def test_disallowed(self):
        ext, msg = validate_extension("evil.exe")
        assert ext is None and "不允许" in msg

    def test_allowed_uppercase(self):
        assert validate_extension("A.PNG") == ("png", None)


class TestVerifyCaptcha:
    @pytest.mark.asyncio
    async def test_none_code(self):
        assert await verify_captcha(MagicMock(), "k", None) is False

    @pytest.mark.asyncio
    async def test_missing_stored(self):
        redis = MagicMock()
        redis.pipeline_exec = AsyncMock(return_value=[None, 1])
        assert await verify_captcha(redis, "k", "1234") is False

    @pytest.mark.asyncio
    async def test_match_case_insensitive(self):
        redis = MagicMock()
        redis.pipeline_exec = AsyncMock(return_value=["ab12", 1])
        assert await verify_captcha(redis, "k", "AB12") is True

    @pytest.mark.asyncio
    async def test_mismatch(self):
        redis = MagicMock()
        redis.pipeline_exec = AsyncMock(return_value=["ab12", 1])
        assert await verify_captcha(redis, "k", "zzzz") is False
