"""密码复杂度策略 & 历史密码检查"""

import re

from app.models.security import SecurityPolicy
from app.utils.password import verify_password


def validate_password_strength(password: str, policy: SecurityPolicy) -> tuple[bool, str]:
    """
    校验密码复杂度

    :param password: 明文密码
    :param policy: 安全策略配置
    :return: (是否通过, 错误信息)
    """
    if len(password) < policy.min_password_length:
        return False, f"密码长度不能少于 {policy.min_password_length} 个字符"

    if policy.require_uppercase and not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"

    if policy.require_lowercase and not re.search(r"[a-z]", password):
        return False, "密码必须包含至少一个小写字母"

    if policy.require_digit and not re.search(r"\d", password):
        return False, "密码必须包含至少一个数字"

    if policy.require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        return False, "密码必须包含至少一个特殊字符"

    return True, ""


def check_password_history(plain_password: str, password_history: list[str] | None, count: int) -> bool:
    """
    检查密码是否在历史 N 次中重复

    :param plain_password: 明文密码
    :param password_history: 历史密码 hash 列表
    :param count: 检查最近 N 条
    :return: True=重复了（不通过），False=未重复（通过）
    """
    if not password_history:
        return False

    # 只检查最近 N 条
    recent_hashes = password_history[-count:] if count > 0 else password_history

    return any(verify_password(plain_password, old_hash) for old_hash in recent_hashes)


def update_password_history(current_hash: str, password_history: list[str] | None, max_count: int) -> list[str]:
    """
    更新密码历史列表

    :param current_hash: 当前密码的 hash（即将成为历史）
    :param password_history: 现有历史密码列表
    :param max_count: 最多保留条数
    :return: 更新后的历史密码列表
    """
    history = list(password_history) if password_history else []
    history.append(current_hash)

    # 只保留最近 max_count 条
    if len(history) > max_count:
        history = history[-max_count:]

    return history
