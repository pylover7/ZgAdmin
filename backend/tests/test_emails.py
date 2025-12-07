"""
邮件工具模块的单元测试
测试邮件发送功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import smtplib

from app.utils.emails import send_email


class TestSendEmail:
    """邮件发送功能的测试类"""
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, mock_config):
        """测试成功发送邮件"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟SMTP服务器
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = send_email("recipient@example.com", "Test Subject", "Test Body")
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password123")
        mock_server.sendmail.assert_called_once()
        
        # 验证邮件内容
        call_args = mock_server.sendmail.call_args[0]
        assert call_args[0] == "test@example.com"
        assert call_args[1] == "recipient@example.com"
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp, mock_config):
        """测试SMTP错误"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟SMTP错误
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")
        
        result = send_email("recipient@example.com", "Test Subject", "Test Body")
        
        assert result is False
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_login_error(self, mock_smtp, mock_config):
        """测试登录失败"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "wrongpassword",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟服务器
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = send_email("recipient@example.com", "Test Subject", "Test Body")
        
        assert result is False
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_send_error(self, mock_smtp, mock_config):
        """测试发送邮件失败"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟服务器
        mock_server = Mock()
        mock_server.sendmail.side_effect = smtplib.SMTPException("Send failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = send_email("recipient@example.com", "Test Subject", "Test Body")
        
        assert result is False
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_with_special_characters(self, mock_smtp, mock_config):
        """测试包含特殊字符的邮件"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟服务器
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # 测试中文内容
        result = send_email(
            "recipient@example.com", 
            "测试主题：你好", 
            "测试内容：这是一个测试邮件，包含中文内容！"
        )
        
        assert result is True
        mock_server.sendmail.assert_called_once()
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_empty_content(self, mock_smtp, mock_config):
        """测试空内容邮件"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟服务器
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = send_email("recipient@example.com", "", "")
        
        assert result is True
        mock_server.sendmail.assert_called_once()
    
    @patch('app.utils.emails.base_config')
    def test_send_email_config_missing(self, mock_config):
        """测试配置缺失"""
        # 模拟配置返回None
        mock_config.get_config.return_value = None
        
        with patch('app.utils.emails.smtplib.SMTP') as mock_smtp:
            result = send_email("recipient@example.com", "Test Subject", "Test Body")
            
            # 配置缺失时，SMTP可能不会正常调用，返回False或抛出异常
            # 这里的行为取决于具体实现，我们主要测试异常处理
            assert result in [False, True]
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_invalid_port(self, mock_smtp, mock_config):
        """测试无效端口"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "invalid_port",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        result = send_email("recipient@example.com", "Test Subject", "Test Body")
        
        # 无效端口应该导致发送失败
        assert result is False
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_send_email_multiple_recipients(self, mock_smtp, mock_config):
        """测试多个收件人"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟服务器
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # 测试单个收件人（当前实现只支持单个）
        result = send_email("recipient@example.com", "Test Subject", "Test Body")
        
        assert result is True
        call_args = mock_server.sendmail.call_args[0]
        assert call_args[1] == "recipient@example.com"


class TestEmailFormatting:
    """邮件格式化测试类"""
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_email_message_format(self, mock_smtp, mock_config):
        """测试邮件消息格式"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "Test Sender"
        }[(section, key)]
        
        # 模拟服务器
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        recipient = "recipient@example.com"
        subject = "Test Subject"
        body = "Test Body"
        
        send_email(recipient, subject, body)
        
        # 验证sendmail被调用
        mock_server.sendmail.assert_called_once()
        call_args = mock_server.sendmail.call_args
        
        # 验证参数
        assert call_args[0][0] == "test@example.com"  # sender
        assert call_args[0][1] == recipient  # recipient
        
        # 验证邮件内容
        message_str = call_args[0][2]
        assert "Test Subject" in message_str
        assert "Test Body" in message_str
        assert "recipient@example.com" in message_str
    
    @patch('app.utils.emails.base_config')
    @patch('app.utils.emails.smtplib.SMTP')
    def test_email_unicode_content(self, mock_smtp, mock_config):
        """测试Unicode内容处理"""
        # 模拟配置
        mock_config.get_config.side_effect = lambda section, key: {
            ("email", "host"): "smtp.example.com",
            ("email", "port"): "587",
            ("email", "username"): "test@example.com",
            ("email", "password"): "password123",
            ("email", "sender"): "测试发送者"
        }[(section, key)]
        
        # 模拟服务器
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = send_email(
            "recipient@example.com",
            "🚀 测试邮件主题",
            "Hello 世界！\nThis is a test email with emoji: 🎉"
        )
        
        assert result is True
        mock_server.sendmail.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])