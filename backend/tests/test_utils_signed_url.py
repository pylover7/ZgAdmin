"""utils/signed_url.py 单元测试 — HMAC 签名 URL 生成/验证"""
import pytest
import time
from uuid import uuid4

from app.utils.signed_url import generate_signed_url, verify_signed_url


class TestSignedUrl:
    def test_generate_and_verify_valid(self):
        file_id = uuid4()
        url = generate_signed_url(file_id, expires_seconds=300)
        # 解析 URL 参数
        assert str(file_id) in url
        assert "expires=" in url
        assert "sign=" in url

    def test_verify_valid_signature(self):
        file_id = uuid4()
        url = generate_signed_url(file_id, expires_seconds=300)
        # 手动解析参数
        params = dict(p.split("=") for p in url.split("?")[1].split("&"))
        expires = int(params["expires"])
        sign = params["sign"]
        assert verify_signed_url(file_id, expires, sign) is True

    def test_verify_tampered_signature(self):
        file_id = uuid4()
        url = generate_signed_url(file_id, expires_seconds=300)
        params = dict(p.split("=") for p in url.split("?")[1].split("&"))
        expires = int(params["expires"])
        sign = params["sign"] + "tampered"
        assert verify_signed_url(file_id, expires, sign) is False

    def test_verify_wrong_file_id(self):
        file_id = uuid4()
        url = generate_signed_url(file_id, expires_seconds=300)
        params = dict(p.split("=") for p in url.split("?")[1].split("&"))
        expires = int(params["expires"])
        sign = params["sign"]
        wrong_id = uuid4()
        assert verify_signed_url(wrong_id, expires, sign) is False

    def test_verify_expired_url(self):
        file_id = uuid4()
        # 已过期的 URL（expires 在过去）
        past_expires = int(time.time()) - 100
        sign = "anysign"
        assert verify_signed_url(file_id, past_expires, sign) is False

    def test_default_expires_seconds(self):
        file_id = uuid4()
        url = generate_signed_url(file_id)  # 默认 300 秒
        params = dict(p.split("=") for p in url.split("?")[1].split("&"))
        expires = int(params["expires"])
        assert expires > int(time.time())
        assert expires <= int(time.time()) + 300
