"""
密码工具模块的单元测试
测试覆盖 md5_encrypt, verify_password, get_password_hash, generate_password 函数
"""
import pytest
import bcrypt
from app.utils.password import (
    md5_encrypt,
    verify_password,
    get_password_hash,
    generate_password
)


class TestMD5Encrypt:
    """md5_encrypt 函数的测试类"""
    
    def test_md5_encrypt_normal_string(self):
        """测试正常字符串的MD5加密"""
        # 测试固定字符串的MD5值
        assert md5_encrypt("hello") == "5d41402abc4b2a76b9719d911017c592"
        assert md5_encrypt("world") == "7d793037a0760186574b0282f2f435e7"
        assert md5_encrypt("") == "d41d8cd98f00b204e9800998ecf8427e"  # 空字符串
    
    def test_md5_encrypt_unicode(self):
        """测试Unicode字符的MD5加密"""
        assert md5_encrypt("你好") == "7eca689f0d3389d9dea66ae112e5cfd7"
        assert md5_encrypt("测试123") == "4a65a5d2287e0466e510470dbebee60d"
        assert md5_encrypt("🚀 emoji") == "ee19d12f2a0a0cd0f45b38ab62519331"
    
    def test_md5_encrypt_special_characters(self):
        """测试特殊字符的MD5加密"""
        assert md5_encrypt("!@#$%^&*()") == "05b28d17a7b6e7024b6e5d8cc43a8bf7"
        assert md5_encrypt("password123!") == "b7e283a09511d95d6eac86e39e7942c0"
        assert md5_encrypt("\n\t\r") == "d6be636be5830be03a22447e0030f343"
    
    def test_md5_encrypt_numbers(self):
        """测试纯数字的MD5加密"""
        assert md5_encrypt("123456789") == "25f9e794323b453885f5181f1b624d0b"
        assert md5_encrypt("0") == "cfcd208495d565ef66e7dff9f98764da"
    
    def test_md5_encrypt_long_string(self):
        """测试长字符串的MD5加密"""
        long_string = "a" * 1000
        result = md5_encrypt(long_string)
        assert len(result) == 32  # MD5总是32位十六进制
        assert all(c in "0123456789abcdef" for c in result)
    
    def test_md5_encrypt_return_type(self):
        """测试返回值类型"""
        result = md5_encrypt("test")
        assert isinstance(result, str)
        assert len(result) == 32
        assert result.islower()  # 应该是小写十六进制
    
    def test_md5_encrypt_consistency(self):
        """测试相同输入产生相同输出"""
        input_str = "consistency_test"
        result1 = md5_encrypt(input_str)
        result2 = md5_encrypt(input_str)
        assert result1 == result2
    
    def test_md5_encrypt_none_input(self):
        """测试None输入"""
        result = md5_encrypt(None)  # type: ignore
        assert result == ""


class TestVerifyPassword:
    """verify_password 函数的测试类"""
    
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_inputs(self):
        """测试空输入"""
        hashed = get_password_hash("test")
        assert verify_password("", hashed) is False
        assert verify_password("test", "") is False
        assert verify_password("", "") is False
    
    def test_verify_password_invalid_hash(self):
        """测试无效哈希值"""
        assert verify_password("test", "invalid_hash") is False
        assert verify_password("test", "$2b$12$invalid") is False
        assert verify_password("test", None) is False  # type: ignore
    
    def test_verify_password_none_inputs(self):
        """测试None输入"""
        assert verify_password(None, "hash") is False  # type: ignore
        assert verify_password("password", None) is False  # type: ignore
        assert verify_password(None, None) is False  # type: ignore
    
    def test_verify_password_special_characters(self):
        """测试特殊字符密码"""
        password = "p@$$w0rd!@#$%^&*()"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("p@$$w0rd", hashed) is False


class TestGetPasswordHash:
    """get_password_hash 函数的测试类"""
    
    def test_get_password_hash_normal(self):
        """测试正常密码哈希生成"""
        password = "test_password"
        hashed = get_password_hash(password)
        
        # 验证哈希格式
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")  # bcrypt哈希格式
        assert len(hashed) == 60  # bcrypt哈希长度
    
    def test_get_password_hash_empty_password(self):
        """测试空密码哈希生成"""
        hashed = get_password_hash("")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
    
    def test_get_password_hash_special_characters(self):
        """测试特殊字符密码哈希生成"""
        password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
    
    def test_get_password_hash_unicode(self):
        """测试Unicode密码哈希生成"""
        password = "密码123你好🚀"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
    
    def test_get_password_hash_uniqueness(self):
        """测试哈希值的唯一性（salt应该使每次结果不同）"""
        password = "test_password"
        hashed1 = get_password_hash(password)
        hashed2 = get_password_hash(password)
        assert hashed1 != hashed2  # 由于salt不同，哈希应该不同
        
        # 但两个哈希都应该能验证原密码
        assert verify_password(password, hashed1)
        assert verify_password(password, hashed2)
    
    def test_get_password_hash_long_password(self):
        """测试长密码哈希生成"""
        password = "a" * 1000
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60


class TestGeneratePassword:
    """generate_password 函数的测试类"""
    
    def test_generate_password_length(self):
        """测试生成密码长度"""
        password = generate_password()
        assert len(password) == 12
    
    def test_generate_password_character_set(self):
        """测试生成密码字符集"""
        password = generate_password()
        # 检查是否只包含允许的字符
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*")
        assert all(c in allowed_chars for c in password)
    
    def test_generate_password_uniqueness(self):
        """测试生成密码的唯一性"""
        passwords = [generate_password() for _ in range(100)]
        # 生成100个密码，应该都是唯一的
        assert len(set(passwords)) == 100
    
    def test_generate_password_character_types(self):
        """测试生成密码包含不同类型的字符"""
        password = generate_password()
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*" for c in password)
        
        # 虽然不能保证每次都有所有类型，但应该包含大部分
        # 这里只检查至少包含几种类型
        char_types = sum([has_lower, has_upper, has_digit, has_special])
        assert char_types >= 2  # 至少包含2种字符类型
    
    def test_generate_password_no_repetition_in_batch(self):
        """测试批量生成密码时避免重复"""
        passwords = set()
        for _ in range(1000):
            password = generate_password()
            assert password not in passwords  # 理论上不应该重复
            passwords.add(password)
    
    def test_generate_password_consistency(self):
        """测试生成密码的一致性（每次调用都应该是新的）"""
        password1 = generate_password()
        password2 = generate_password()
        assert password1 != password2
        assert len(password1) == len(password2) == 12


class TestIntegration:
    """集成测试类"""
    
    def test_password_workflow(self):
        """测试完整的密码工作流程"""
        # 1. 生成随机密码
        password = generate_password()
        assert len(password) == 12
        
        # 2. 生成哈希
        hashed = get_password_hash(password)
        assert hashed.startswith("$2b$")
        
        # 3. 验证正确密码
        assert verify_password(password, hashed) is True
        
        # 4. 验证错误密码
        assert verify_password("wrong_password", hashed) is False
    
    def test_md5_with_password_workflow(self):
        """测试MD5加密与密码哈希的集成"""
        password = "integration_test"
        
        # 直接MD5加密
        md5_hash = md5_encrypt(password)
        assert len(md5_hash) == 32
        
        # 通过密码流程
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        
        # 验证MD5一致性
        assert md5_encrypt(password) == md5_encrypt(password)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])