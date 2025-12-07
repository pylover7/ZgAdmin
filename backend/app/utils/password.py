import hashlib
import secrets
import string
import bcrypt


def md5_encrypt(input_string) -> str:
    """MD5加密函数"""
    if input_string is None:
        return ""
    # 创建md5对象
    md5_hash = hashlib.md5()
    # 更新哈希值
    md5_hash.update(input_string.encode('utf-8'))
    # 获取加密后的十六进制表示
    encrypted_string = md5_hash.hexdigest()
    return encrypted_string


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        if plain_password is None or hashed_password is None:
            return False
        
        # 检查哈希格式是否正确（bcrypt哈希应该以$2b$开头且长度为60）
        if not isinstance(hashed_password, str) or not hashed_password.startswith('$2b$') or len(hashed_password) != 60:
            return False
        
        # 双重MD5：与创建过程保持一致
        md5_once = md5_encrypt(plain_password)
        md5_twice = md5_encrypt(md5_once)
        
        return bcrypt.checkpw(md5_twice.encode('utf-8'),
                              hashed_password.encode('utf-8'))
    except (ValueError, TypeError, AttributeError, Exception):
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(md5_encrypt(password).encode('utf-8'), salt)
    return hashed.decode('utf-8')


def generate_password() -> str:
    """生成随机密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(12))
