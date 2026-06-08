"""utils/password_policy.py 单元测试 — 密码复杂度 + 历史检查"""
import pytest

from app.models.security import SecurityPolicy
from app.utils.password import get_password_hash
from app.utils.password_policy import (
    check_password_history,
    update_password_history,
    validate_password_strength,
)

# ═══════════════════════════════════════════════════════════════════════
# validate_password_strength
# ═══════════════════════════════════════════════════════════════════════

class TestValidatePasswordStrength:
    @pytest.fixture
    def strict_policy(self):
        """所有策略全开的严格策略"""
        return SecurityPolicy(
            min_password_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digit=True,
            require_special=True,
        )

    @pytest.fixture
    def lenient_policy(self):
        """只要求长度的宽松策略"""
        return SecurityPolicy(
            min_password_length=6,
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
            require_special=False,
        )

    def test_strong_password_passes(self, strict_policy):
        ok, msg = validate_password_strength("Admin@123", strict_policy)
        assert ok is True
        assert msg == ""

    def test_too_short(self, strict_policy):
        ok, msg = validate_password_strength("Ab@1", strict_policy)
        assert ok is False
        assert "少于" in msg

    def test_no_uppercase(self, strict_policy):
        ok, msg = validate_password_strength("admin@123", strict_policy)
        assert ok is False
        assert "大写" in msg

    def test_no_lowercase(self, strict_policy):
        ok, msg = validate_password_strength("ADMIN@123", strict_policy)
        assert ok is False
        assert "小写" in msg

    def test_no_digit(self, strict_policy):
        ok, msg = validate_password_strength("Admin@pass", strict_policy)
        assert ok is False
        assert "数字" in msg

    def test_no_special(self, strict_policy):
        ok, msg = validate_password_strength("Admin1234", strict_policy)
        assert ok is False
        assert "特殊字符" in msg

    def test_lenient_policy_simple(self, lenient_policy):
        ok, _msg = validate_password_strength("abcdef", lenient_policy)
        assert ok is True

    def test_lenient_policy_too_short(self, lenient_policy):
        ok, _msg = validate_password_strength("abc", lenient_policy)
        assert ok is False

    def test_exact_min_length(self, strict_policy):
        ok, _msg = validate_password_strength("Aa!12345", strict_policy)
        assert ok is True

    def test_empty_password(self, strict_policy):
        ok, _msg = validate_password_strength("", strict_policy)
        assert ok is False


# ═══════════════════════════════════════════════════════════════════════
# check_password_history
# ═══════════════════════════════════════════════════════════════════════

class TestCheckPasswordHistory:
    def test_empty_history_passes(self):
        result = check_password_history("anypassword", None, count=3)
        assert result is False  # 无历史=不重复

    def test_password_in_history_fails(self):
        old_hash = get_password_hash("oldpassword")
        result = check_password_history("oldpassword", [old_hash], count=3)
        assert result is True  # 重复了

    def test_password_not_in_history_passes(self):
        old_hash = get_password_hash("oldpassword")
        result = check_password_history("newpassword", [old_hash], count=3)
        assert result is False

    def test_count_limits_check_range(self):
        # 历史 5 条，但只检查最近 2 条
        hashes = [get_password_hash(f"pw{i}") for i in range(5)]
        # pw0 不在最近 2 条中
        result = check_password_history("pw0", hashes, count=2)
        assert result is False  # pw0 不在最近 2 条
        # pw4 在最近 2 条中
        result = check_password_history("pw4", hashes, count=2)
        assert result is True

    def test_count_zero_checks_all(self):
        """count=0 时 list[-0:] 等于 list[0:] 返回完整列表，因此会检查所有历史"""
        hashes = [get_password_hash(f"pw{i}") for i in range(3)]
        result = check_password_history("pw0", hashes, count=0)
        # Python 中 [-0:] == [0:]，返回完整列表，所以 pw0 会被检查到
        assert result is True

    def test_empty_list_passes(self):
        result = check_password_history("pw", [], count=3)
        assert result is False


# ═══════════════════════════════════════════════════════════════════════
# update_password_history
# ═══════════════════════════════════════════════════════════════════════

class TestUpdatePasswordHistory:
    def test_append_to_empty(self):
        result = update_password_history("hash1", None, max_count=3)
        assert result == ["hash1"]

    def test_append_to_existing(self):
        result = update_password_history("hash2", ["hash1"], max_count=3)
        assert result == ["hash1", "hash2"]

    def test_truncate_when_exceeds_max(self):
        result = update_password_history("hash4", ["hash1", "hash2", "hash3"], max_count=3)
        assert result == ["hash2", "hash3", "hash4"]
        assert len(result) == 3

    def test_no_truncate_within_limit(self):
        result = update_password_history("hash2", ["hash1"], max_count=5)
        assert result == ["hash1", "hash2"]
        assert len(result) == 2

    def test_empty_list_treated_as_empty(self):
        result = update_password_history("hash1", [], max_count=3)
        assert result == ["hash1"]
