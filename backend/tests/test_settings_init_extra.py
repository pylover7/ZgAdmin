"""settings/__init__.py 边界测试 — parse_cors、VERSION、emails_enabled、密钥与 CORS 校验"""

import warnings
from pathlib import Path

import pytest

from app.settings import Settings, parse_cors


class TestParseCors:
    def test_comma_separated_string(self):
        assert parse_cors("http://a.com,http://b.com") == ["http://a.com", "http://b.com"]

    def test_list_passthrough(self):
        assert parse_cors(["http://a.com"]) == ["http://a.com"]

    def test_bracket_string_passthrough(self):
        assert parse_cors('["http://a.com"]') == '["http://a.com"]'

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_cors(123)


class TestVersionField:
    def test_reads_version_file(self):
        assert Settings().VERSION

    def test_missing_file_returns_unknown(self, monkeypatch):
        def boom(self, *args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(Path, "read_text", boom)
        assert Settings(SECRET_KEY="fixed-key").VERSION == "unknown"


class TestEmailsEnabled:
    def test_disabled_by_default(self):
        assert Settings(EMAILS_FROM_EMAIL="", SMTP_HOST="").emails_enabled is False

    def test_enabled_when_both_set(self):
        assert Settings(EMAILS_FROM_EMAIL="a@b.com", SMTP_HOST="smtp.x.com").emails_enabled is True


class TestCheckDefaultSecret:
    def test_changethis_warns_in_local(self):
        s = Settings()
        s.ENVIRONMENT = "local"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s._check_default_secret("SECRET_KEY", "changethis")
        assert len(w) == 1

    def test_changethis_raises_in_prod(self):
        s = Settings()
        s.ENVIRONMENT = "production"
        with pytest.raises(ValueError, match="changethis"):
            s._check_default_secret("SECRET_KEY", "changethis")

    def test_other_value_noop(self):
        s = Settings()
        s._check_default_secret("X", "safe")


class TestResolveSecretKey:
    def test_generates_and_persists(self, monkeypatch):
        """真实调用 _resolve_secret_key：文件不存在 → 生成新 key 并落盘"""
        import sys
        from pathlib import Path as RealPath

        settings_mod = sys.modules["app.settings"]
        real_root = RealPath(settings_mod.__file__).parent.parent.parent
        real_key_file = real_root / ".secret_key"
        backup = real_key_file.read_text() if real_key_file.exists() else None
        if real_key_file.exists():
            real_key_file.unlink()
        try:
            s = Settings(SECRET_KEY="x")
            generated = s._resolve_secret_key()
            assert generated and real_key_file.exists()
            assert real_key_file.read_text() == generated
        finally:
            if backup is not None:
                real_key_file.write_text(backup)
            elif real_key_file.exists():
                real_key_file.unlink()

    def test_reads_existing_file(self):
        """真实调用 _resolve_secret_key：文件已存在 → 直接读取"""
        import sys
        from pathlib import Path as RealPath

        settings_mod = sys.modules["app.settings"]
        real_root = RealPath(settings_mod.__file__).parent.parent.parent
        real_key_file = real_root / ".secret_key"
        backup = real_key_file.read_text() if real_key_file.exists() else None
        real_key_file.write_text("persisted-key")
        try:
            s = Settings(SECRET_KEY="x")
            assert s._resolve_secret_key() == "persisted-key"
        finally:
            if backup is not None:
                real_key_file.write_text(backup)
            elif real_key_file.exists():
                real_key_file.unlink()


class TestModelValidator:
    def test_prod_default_secret_raises(self):
        with pytest.raises(ValueError, match="SECRET_KEY"):
            Settings(ENVIRONMENT="production", SECRET_KEY="changethis", BACKEND_CORS_ORIGINS=["http://x.com"])

    def test_prod_star_cors_raises(self):
        with pytest.raises(ValueError, match="CORS"):
            Settings(ENVIRONMENT="production", SECRET_KEY="a-strong-key", BACKEND_CORS_ORIGINS=["*"])

    def test_local_auto_resolves_secret(self, monkeypatch):
        monkeypatch.setattr(Settings, "_resolve_secret_key", lambda self: "resolved-key")
        s = Settings(ENVIRONMENT="local", SECRET_KEY="")
        assert s.SECRET_KEY == "resolved-key"

    def test_local_star_cors_allowed(self, monkeypatch):
        monkeypatch.setattr(Settings, "_resolve_secret_key", lambda self: "resolved-key")
        s = Settings(ENVIRONMENT="local", SECRET_KEY="", BACKEND_CORS_ORIGINS=["*"])
        assert s.SECRET_KEY == "resolved-key"
