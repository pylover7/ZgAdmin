import hashlib
import hmac
import time
from uuid import UUID

from app.settings import settings


def generate_signed_url(file_id: UUID, expires_seconds: int = 300) -> str:
    """生成 HMAC-SHA256 签名下载 URL"""
    expires = int(time.time()) + expires_seconds
    message = f"{file_id}:{expires}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"/api/v1/base/file/download/{file_id}?expires={expires}&sign={signature}"


def verify_signed_url(file_id: UUID, expires: int, sign: str) -> bool:
    """验证签名 URL 是否有效"""
    if time.time() > expires:
        return False
    message = f"{file_id}:{expires}"
    expected = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(sign, expected)
