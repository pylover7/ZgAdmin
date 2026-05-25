"""utils/captcha.py 单元测试 — 验证码生成/校验"""
import pytest
import base64

from app.utils.captcha import (
    _generate_code,
    _create_captcha_image,
    generate_captcha,
    verify_captcha,
    CAPTCHA_KEY_PREFIX,
)
from app.core.redis import MemoryRedis


class TestGenerateCode:
    def test_default_length(self):
        code = _generate_code()
        assert len(code) == 4

    def test_custom_length(self):
        code = _generate_code(length=6)
        assert len(code) == 6

    def test_no_confusing_chars(self):
        confusing = set("0O1I2Z5S8B")
        for _ in range(100):
            code = _generate_code()
            assert not any(c in confusing for c in code), f"Found confusing char in {code}"

    def test_uppercase_and_digits_only(self):
        import string
        valid_chars = set(string.ascii_uppercase + string.digits) - set("0O1I2Z5S8B")
        for _ in range(100):
            code = _generate_code()
            assert all(c in valid_chars for c in code)


class TestCreateCaptchaImage:
    def test_returns_png_bytes(self):
        image_bytes = _create_captcha_image("ABCD")
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        assert image_bytes[:4] == b"\x89PNG"


class TestGenerateCaptcha:
    @pytest.mark.asyncio
    async def test_returns_key_and_base64(self):
        redis = MemoryRedis()
        captcha_key, b64_image = await generate_captcha(redis)
        assert isinstance(captcha_key, str)
        assert len(captcha_key) > 0
        assert b64_image.startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_code_stored_in_redis(self):
        redis = MemoryRedis()
        captcha_key, _ = await generate_captcha(redis)
        # 验证码应存在 Redis 中
        stored = await redis.get(f"{CAPTCHA_KEY_PREFIX}{captcha_key}")
        assert stored is not None
        assert len(stored) == 4  # 4 位验证码


class TestVerifyCaptcha:
    @pytest.mark.asyncio
    async def test_correct_code(self):
        redis = MemoryRedis()
        captcha_key, _ = await generate_captcha(redis)
        # 从 Redis 取出验证码
        stored = await redis.get(f"{CAPTCHA_KEY_PREFIX}{captcha_key}")
        result = await verify_captcha(redis, captcha_key, stored)
        assert result is True

    @pytest.mark.asyncio
    async def test_wrong_code(self):
        redis = MemoryRedis()
        captcha_key, _ = await generate_captcha(redis)
        result = await verify_captcha(redis, captcha_key, "XXXX")
        # 可能恰好相同（极低概率），但大部分情况应失败
        stored = await redis.get(f"{CAPTCHA_KEY_PREFIX}{captcha_key}")
        if stored != "XXXX":
            assert result is False

    @pytest.mark.asyncio
    async def test_case_insensitive(self):
        redis = MemoryRedis()
        captcha_key, _ = await generate_captcha(redis)
        stored = await redis.get(f"{CAPTCHA_KEY_PREFIX}{captcha_key}")
        # 小写输入
        result = await verify_captcha(redis, captcha_key, stored.lower() if stored else "")
        assert result is True

    @pytest.mark.asyncio
    async def test_one_time_use(self):
        """验证码验证后应被删除，二次验证失败"""
        redis = MemoryRedis()
        captcha_key, _ = await generate_captcha(redis)
        stored = await redis.get(f"{CAPTCHA_KEY_PREFIX}{captcha_key}")
        # 第一次验证
        result1 = await verify_captcha(redis, captcha_key, stored)
        assert result1 is True
        # 第二次验证（验证码已被删除）
        result2 = await verify_captcha(redis, captcha_key, stored)
        assert result2 is False

    @pytest.mark.asyncio
    async def test_nonexistent_key(self):
        redis = MemoryRedis()
        result = await verify_captcha(redis, "nonexistent-key", "ABCD")
        assert result is False
