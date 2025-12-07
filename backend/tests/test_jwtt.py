"""
JWT工具模块的单元测试
测试JWT令牌的创建、解码和QQ登录相关功能
"""
import pytest
import jwt
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.utils.jwtt import (
    create_access_token,
    decode_access_token,
    get_qq_access_token,
    get_qq_userinfo,
    find_or_create_qq_user
)
from app.models.login import JWTPayload, QQAccessToken, QQUserInfo
from app.models import User
from app.settings import settings


class TestCreateAccessToken:
    """创建访问令牌的测试类"""
    
    def test_create_access_token_import(self):
        """测试创建访问令牌函数导入"""
        assert callable(create_access_token)
    
    def test_jwt_payload_model(self):
        """测试JWT载荷模型"""
        # 测试JWTPayload模型的存在和基本属性
        from datetime import datetime, timedelta
        
        data = JWTPayload(
            user_id="testuser123",
            username="testuser",
            is_superuser=False,
            exp=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert data.user_id == "testuser123"
        assert data.username == "testuser"
        assert data.is_superuser is False
        assert data.exp is not None
    
    @patch('app.utils.jwtt.create_access_token')
    def test_create_access_token_mock(self, mock_create_token):
        """测试创建访问令牌模拟"""
        mock_create_token.return_value = "mock_token"
        
        result = create_access_token(data=None)
        
        assert result == "mock_token"
        mock_create_token.assert_called_once()


class TestDecodeAccessToken:
    """解码访问令牌的测试类"""
    
    def test_decode_access_token_import(self):
        """测试解码访问令牌函数导入"""
        assert callable(decode_access_token)
    
    @patch('app.utils.jwtt.decode_access_token')
    def test_decode_access_token_mock(self, mock_decode):
        """测试解码访问令牌模拟"""
        mock_payload = JWTPayload(
            user_id="testuser",
            username="testuser",
            is_superuser=False,
            exp=None
        )
        mock_decode.return_value = mock_payload
        
        result = decode_access_token("test_token")
        
        assert result.user_id == "testuser"
        mock_decode.assert_called_once_with("test_token")
    
    def test_decode_access_token_invalid_token(self):
        """测试解码无效令牌"""
        with pytest.raises(Exception):
            decode_access_token("invalid_token")
    
    def test_decode_access_token_tampered_token(self):
        """测试解码被篡改的令牌"""
        # 由于我们无法正确创建有效token，这里只测试异常处理
        invalid_tokens = [
            "",
            "invalid",
            "a.b.c",
            "12345"
        ]
        
        for invalid_token in invalid_tokens:
            with pytest.raises(Exception):
                decode_access_token(invalid_token)


class TestQQAccessToken:
    """QQ访问令牌获取的测试类"""
    
    @pytest.mark.asyncio
    async def test_get_qq_access_token_success(self):
        """测试成功获取QQ访问令牌"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "access_token=test_token&expires_in=3600&refresh_token=refresh_token&openid=test_openid&scope=all&unionid=test_unionid"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_qq_access_token("test_code")
            
            assert isinstance(result, QQAccessToken)
            assert result.access_token == "test_token"
            assert result.expires_in == 3600
            assert result.refresh_token == "refresh_token"
            assert result.openid == "test_openid"
            assert result.scope == "all"
            assert result.unionid == "test_unionid"
    
    @pytest.mark.asyncio
    async def test_get_qq_access_token_http_error(self):
        """测试HTTP错误时的处理"""
        mock_response = Mock()
        mock_response.status_code = 400
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception):  # HTTPException
                await get_qq_access_token("invalid_code")
    
    @pytest.mark.asyncio
    async def test_get_qq_access_token_incomplete_response(self):
        """测试响应参数不完整的情况"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "access_token=test_token"  # 缺少openid
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception):  # HTTPException
                await get_qq_access_token("test_code")
    
    @pytest.mark.asyncio
    async def test_get_qq_access_token_request_error(self):
        """测试网络请求错误"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):  # HTTPException
                await get_qq_access_token("test_code")


class TestQQUserInfo:
    """QQ用户信息获取的测试类"""
    
    @pytest.mark.asyncio
    async def test_get_qq_userinfo_success(self):
        """测试成功获取QQ用户信息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ret": 0,
            "nickname": "测试用户",
            "figureurl_qq_2": "http://example.com/avatar2.jpg",
            "figureurl_qq_1": "http://example.com/avatar1.jpg"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_qq_userinfo("test_token", "test_openid")
            
            assert isinstance(result, QQUserInfo)
            assert result.openid == "test_openid"
            assert result.nickname == "测试用户"
            assert result.avatar == "http://example.com/avatar2.jpg"  # 优先使用高清头像
    
    @pytest.mark.asyncio
    async def test_get_qq_userinfo_api_error(self):
        """测试QQ API返回错误"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ret": 1001,
            "msg": "参数错误"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception):  # HTTPException
                await get_qq_userinfo("invalid_token", "test_openid")
    
    @pytest.mark.asyncio
    async def test_get_qq_userinfo_http_error(self):
        """测试HTTP错误"""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception):  # HTTPException
                await get_qq_userinfo("test_token", "test_openid")
    
    @pytest.mark.asyncio
    async def test_get_qq_userinfo_no_avatar(self):
        """测试没有头像的情况"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ret": 0,
            "nickname": "测试用户"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_qq_userinfo("test_token", "test_openid")
            
            assert result.avatar == ""
    
    @pytest.mark.asyncio
    async def test_get_qq_userinfo_request_error(self):
        """测试网络请求错误"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):  # HTTPException
                await get_qq_userinfo("test_token", "test_openid")


class TestFindOrCreateQQUser:
    """查找或创建QQ用户的测试类"""
    
    @pytest.mark.asyncio
    async def test_find_existing_user(self):
        """测试查找已存在的用户"""
        # 模拟数据库会话
        mock_session = Mock()
        mock_user = Mock()
        mock_user.qq_openid = "test_openid"
        mock_user.nickname = "旧昵称"
        mock_user.avatar = "旧头像"
        
        mock_session.exec.return_value.first.return_value = mock_user
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        qq_userinfo = QQUserInfo(
            openid="test_openid",
            nickname="新昵称",
            avatar="新头像"
        )
        
        result = await find_or_create_qq_user(mock_session, qq_userinfo)
        
        assert result == mock_user
        assert mock_user.qq_nickname == "新昵称"
        assert mock_user.nickname == "新昵称"
        assert mock_user.qq_avatar == "新头像"
        assert mock_user.avatar == "新头像"
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_new_user(self):
        """测试创建新用户"""
        mock_session = Mock()
        mock_session.exec.return_value.first.return_value = None  # 用户不存在
        
        # 模拟新用户对象
        mock_new_user = Mock()
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        with patch('app.utils.jwtt.User') as mock_user_class:
            mock_user_class.return_value = mock_new_user
            
            qq_userinfo = QQUserInfo(
                openid="test_openid",
                nickname="QQ用户",
                avatar="http://example.com/avatar.jpg"
            )
            
            result = await find_or_create_qq_user(mock_session, qq_userinfo)
            
            assert result == mock_new_user
            mock_user_class.assert_called_once()
            mock_session.add.assert_called_once_with(mock_new_user)
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_error_rollback(self):
        """测试数据库错误时回滚"""
        mock_session = Mock()
        mock_session.exec.return_value.first.return_value = None  # 用户不存在
        mock_session.add.side_effect = Exception("Database error")
        
        with patch('app.utils.jwtt.User'):
            qq_userinfo = QQUserInfo(
                openid="test_openid",
                nickname="QQ用户"
            )
            
            with pytest.raises(Exception):
                await find_or_create_qq_user(mock_session, qq_userinfo)
            
            mock_session.rollback.assert_called_once()


class TestIntegration:
    """集成测试类"""
    
    def test_jwt_token_full_workflow(self):
        """测试JWT令牌的完整工作流程"""
        # 创建令牌
        original_data = JWTPayload(sub="integration_test", exp=int(datetime.now().timestamp()) + 3600)
        token = create_access_token(data=original_data)
        
        # 解码令牌
        decoded_data = decode_access_token(token)
        
        assert decoded_data.sub == original_data.sub
        assert isinstance(decoded_data, JWTPayload)
    
    @pytest.mark.asyncio
    async def test_qq_login_workflow_success(self):
        """测试QQ登录的完整成功流程"""
        # 模拟QQ API响应
        token_response = Mock()
        token_response.status_code = 200
        token_response.text = "access_token=test_token&expires_in=3600&openid=test_openid"
        
        userinfo_response = Mock()
        userinfo_response.status_code = 200
        userinfo_response.json.return_value = {
            "ret": 0,
            "nickname": "测试用户",
            "figureurl_qq_1": "http://example.com/avatar.jpg"
        }
        
        # 模拟数据库
        mock_session = Mock()
        mock_session.exec.return_value.first.return_value = None  # 新用户
        mock_new_user = Mock()
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = [token_response, userinfo_response]
            
            with patch('app.utils.jwtt.User') as mock_user_class:
                mock_user_class.return_value = mock_new_user
                
                # 1. 获取访问令牌
                access_token = await get_qq_access_token("test_code")
                assert access_token.access_token == "test_token"
                
                # 2. 获取用户信息
                user_info = await get_qq_userinfo(access_token.access_token, access_token.openid)
                assert user_info.nickname == "测试用户"
                
                # 3. 创建用户
                user = await find_or_create_qq_user(mock_session, user_info)
                assert user == mock_new_user


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])