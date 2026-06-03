import hashlib
import secrets
import string

import bcrypt


def md5_encrypt(input_string) -> str:
    """MD5加密函数"""
    if input_string is None:
        return ""
    # 创建md5对象
    md5_hash = hashlib.md5()  # noqa: S324
    # 更新哈希值
    md5_hash.update(input_string.encode("utf-8"))
    # 获取加密后的十六进制表示
    encrypted_string = md5_hash.hexdigest()
    return encrypted_string


def verify_password(plain_password: str | None, hashed_password: str | None) -> bool:
    """验证密码 — 纯bcrypt"""
    try:
        if plain_password is None or hashed_password is None:
            return False
        if not isinstance(hashed_password, str) or not hashed_password.startswith("$2b$") or len(hashed_password) != 60:
            return False
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError, AttributeError):
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希 — 纯bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def generate_password() -> str:
    """生成随机密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(12))
