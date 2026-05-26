"""utils/password.py 单元测试 — 纯函数，无需 DB"""
import pytest
from app.utils.password import (
    get_password_hash,
    verify_password,
    md5_encrypt,
    generate_password,
)


class TestMd5Encrypt:
    def test_normal_string(self):
        result = md5_encrypt("hello")
        assert result == "5d41402abc4b2a76b9719d911017c592"

    def test_empty_string(self):
        result = md5_encrypt("")
        assert result == "d41d8cd98f00b204e9800998ecf8427e"

    def test_none_input(self):
        assert md5_encrypt(None) == ""

    def test_unicode_string(self):
        result = md5_encrypt("你好世界")
        assert isinstance(result, str)
        assert len(result) == 32

    def test_deterministic(self):
        assert md5_encrypt("test") == md5_encrypt("test")


class TestGetPasswordHash:
    def test_returns_bcrypt_hash(self):
        hashed = get_password_hash("mypassword")
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_different_salts(self):
        h1 = get_password_hash("samepassword")
        h2 = get_password_hash("samepassword")
        assert h1 != h2  # 不同盐值产生不同哈希


class TestVerifyPassword:
    def test_correct_password(self):
        hashed = get_password_hash("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_wrong_password(self):
        hashed = get_password_hash("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_none_plain_password(self):
        hashed = get_password_hash("test")
        assert verify_password(None, hashed) is False

    def test_none_hashed_password(self):
        assert verify_password("test", None) is False

    def test_invalid_hash_format(self):
        assert verify_password("test", "not_a_hash") is False

    def test_too_short_hash(self):
        assert verify_password("test", "$2b$12$abc") is False

    def test_wrong_prefix(self):
        assert verify_password("test", "$2a$12$" + "a" * 53) is False


class TestGeneratePassword:
    def test_default_length(self):
        pwd = generate_password()
        assert len(pwd) == 12

    def test_contains_expected_chars(self):
        pwd = generate_password()
        assert isinstance(pwd, str)
        assert len(pwd) > 0

    def test_randomness(self):
        p1 = generate_password()
        p2 = generate_password()
        # 极低概率相同
        assert p1 != p2 or len(p1) == 0
