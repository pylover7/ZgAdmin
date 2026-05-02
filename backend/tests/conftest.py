"""
pytest配置文件
定义测试夹具和共享配置
"""
import pytest
import asyncio
from unittest.mock import Mock
from fastapi import FastAPI
from sqlmodel import Session, create_engine, SQLModel
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """创建一个事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_app():
    """创建模拟的FastAPI应用"""
    app = FastAPI(title="Test App")
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app


@pytest.fixture
def mock_session():
    """创建模拟的数据库会话"""
    session = Mock(spec=Session)
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.refresh = Mock()
    session.exec = Mock()
    session.query = Mock()
    session.delete = Mock()
    
    return session


@pytest.fixture
def mock_user():
    """创建模拟用户对象"""
    user = Mock()
    user.id = "test-user-id"
    user.username = "testuser"
    user.email = "test@example.com"
    user.password = "hashed_password"
    user.is_active = True
    user.is_superuser = False
    user.created_at = "2023-12-07T12:00:00Z"
    
    return user


@pytest.fixture
def mock_request():
    """创建模拟请求对象"""
    request = Mock()
    request.method = "GET"
    request.url.path = "/test"
    request.headers = {
        "User-Agent": "Mozilla/5.0 (Test Browser)",
        "X-Forwarded-For": "127.0.0.1"
    }
    request.query_params = {}
    request.json = Mock(return_value={"test": "data"})
    
    return request


@pytest.fixture
def sample_jwt_payload():
    """示例JWT载荷"""
    return {
        "sub": "testuser",
        "exp": 1234567890,
        "iat": 1234567890 - 3600
    }


@pytest.fixture
def sample_password_data():
    """示例密码数据"""
    return {
        "plain_password": "test_password_123",
        "hashed_password": "$2b$12$test_hashed_password_here",
        "md5_hash": "5d41402abc4b2a76b9719d911017c592"
    }


@pytest.fixture
def sample_qq_userinfo():
    """示例QQ用户信息"""
    return {
        "openid": "test_openid_123",
        "nickname": "测试用户",
        "avatar": "http://example.com/avatar.jpg",
        "unionid": "test_unionid_456"
    }


@pytest.fixture
def sample_email_data():
    """示例邮件数据"""
    return {
        "receiver": "recipient@example.com",
        "subject": "Test Subject",
        "body": "This is a test email body.",
        "sender": "sender@example.com",
        "host": "smtp.example.com",
        "port": "587"
    }


@pytest.fixture
def sample_ip_responses():
    """示例IP API响应"""
    return {
        "api2_response": '{"data":{"address":"北京市 电信"}}',
        "api1_response": '{"data":[{"location":"上海市 移动"}]}',
        "error_response": '{"error":"not_found"}',
        "empty_response": '{"data":[]}'
    }


@pytest.fixture
def sample_time_data():
    """示例时间数据"""
    return {
        "utc_time": "2023-12-07T12:00:00.000Z",
        "beijing_time": "2023-12-07T20:00:00+08:00",
        "ny_time": "2023-12-07T07:00:00-05:00"
    }


@pytest.fixture
def error_responses():
    """示例错误响应"""
    return {
        "integrity_error": "UNIQUE constraint failed: user.email",
        "http_404": "Not Found",
        "http_500": "Internal Server Error",
        "validation_error": "field required",
        "response_validation_error": "invalid response format"
    }


# 测试数据库配置
@pytest.fixture(scope="session")
def test_db_url():
    """测试数据库URL"""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """创建测试数据库引擎"""
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    return engine


@pytest.fixture
def test_session(test_engine):
    """创建测试数据库会话"""
    SQLModel.metadata.create_all(test_engine)
    session = Session(test_engine)
    try:
        yield session
    finally:
        session.close()
        SQLModel.metadata.drop_all(test_engine)


# 测试客户端
@pytest.fixture
def test_client(mock_app):
    """创建测试客户端"""
    return TestClient(mock_app)


# 异步测试支持
@pytest.fixture
async def async_client(mock_app):
    """创建异步测试客户端"""
    from httpx import AsyncClient
    async with AsyncClient(app=mock_app, base_url="http://test") as client:
        yield client


# Mock工具函数
@pytest.fixture
def mock_httpx_get():
    """Mock httpx.get函数"""
    with pytest.MonkeyPatch().context() as m:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content.decode.return_value = '{"data": {"test": "value"}}'
        mock_response.json.return_value = {"data": {"test": "value"}}
        
        def mock_get(*args, **kwargs):
            return mock_response
        
        m.setattr("httpx.get", mock_get)
        yield mock_response


@pytest.fixture
def mock_smtp():
    """Mock SMTP服务器"""
    with pytest.MonkeyPatch().context() as m:
        mock_server = Mock()
        mock_server.starttls = Mock()
        mock_server.login = Mock()
        mock_server.sendmail = Mock()
        
        def mock_smtp_server(*args, **kwargs):
            return mock_server
        
        m.setattr("smtplib.SMTP", mock_smtp_server)
        yield mock_server


@pytest.fixture
def mock_logger():
    """Mock日志器"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    
    return logger


# 配置相关
@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    import tempfile
    import os
    
    config_content = """
[test]
string_value = "test_string"
int_value = 123
bool_value = true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    yield temp_path
    
    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# 环境变量管理
@pytest.fixture
def env_manager():
    """环境变量管理器"""
    import os
    original_env = os.environ.copy()
    
    class EnvManager:
        def set(self, key, value):
            os.environ[key] = value
        
        def get(self, key, default=None):
            return os.environ.get(key, default)
        
        def delete(self, key):
            if key in os.environ:
                del os.environ[key]
        
        def restore(self):
            os.environ.clear()
            os.environ.update(original_env)
    
    manager = EnvManager()
    yield manager
    manager.restore()


# 测试数据生成器
@pytest.fixture
def data_generator():
    """测试数据生成器"""
    import uuid
    import secrets
    from datetime import datetime
    
    class DataGenerator:
        def uuid(self):
            return str(uuid.uuid4())
        
        def random_string(self, length=10):
            return secrets.token_urlsafe(length)[:length]
        
        def email(self):
            return f"{self.random_string()}@example.com"
        
        def phone(self):
            return f"1{secrets.randbelow(9000000000) + 1000000000}"
        
        def datetime_str(self):
            return datetime.now().isoformat()
        
        def password(self, length=12):
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
            return ''.join(secrets.choice(chars) for _ in range(length))
    
    return DataGenerator()


# 断言辅助工具
@pytest.fixture
def assertions():
    """断言辅助工具"""
    class Assertions:
        def assert_json_response(self, response, expected_code=200, expected_keys=None):
            assert response.status_code == expected_code
            json_data = response.json()
            if expected_keys:
                for key in expected_keys:
                    assert key in json_data
            return json_data
        
        def assert_time_within_range(self, actual_time, expected_time, tolerance_seconds=5):
            from datetime import datetime, timedelta
            if isinstance(actual_time, str):
                actual_time = datetime.fromisoformat(actual_time.replace('Z', '+00:00'))
            if isinstance(expected_time, str):
                expected_time = datetime.fromisoformat(expected_time.replace('Z', '+00:00'))
            
            diff = abs(actual_time - expected_time)
            assert diff.total_seconds() <= tolerance_seconds
        
        def assert_uuid_format(self, uuid_string):
            import uuid as uuid_lib
            try:
                uuid_obj = uuid_lib.UUID(uuid_string)
                assert str(uuid_obj) == uuid_string
            except ValueError:
                pytest.fail(f"Invalid UUID format: {uuid_string}")
        
        def assert_email_format(self, email):
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            assert re.match(pattern, email), f"Invalid email format: {email}"
        
        def assert_password_strength(self, password):
            assert len(password) >= 8, "Password too short"
            assert any(c.isupper() for c in password), "Password missing uppercase"
            assert any(c.islower() for c in password), "Password missing lowercase"
            assert any(c.isdigit() for c in password), "Password missing digit"
    
    return Assertions()