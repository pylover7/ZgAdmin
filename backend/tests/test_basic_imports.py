"""
基础导入测试
测试所有主要模块是否能正确导入
"""
import pytest


class TestBasicImports:
    """基础导入测试类"""
    
    def test_import_utils(self):
        """测试工具模块导入"""
        try:
            from app.utils.password import md5_encrypt, verify_password, get_password_hash, generate_password
            from app.utils.jwtt import create_access_token, decode_access_token
            from app.utils.emails import send_email
            from app.utils.ip import getIpAddress, getReqSysBro
            from app.utils.localTime import convert_utc_to_local_time
            
            assert callable(md5_encrypt)
            assert callable(verify_password)
            assert callable(get_password_hash)
            assert callable(generate_password)
            assert callable(create_access_token)
            assert callable(decode_access_token)
            assert callable(send_email)
            assert callable(getIpAddress)
            assert callable(getReqSysBro)
            assert callable(convert_utc_to_local_time)
        except ImportError as e:
            pytest.fail(f"Failed to import utils modules: {e}")
    
    def test_import_core(self):
        """测试核心模块导入"""
        try:
            from app.core.database import init_api
            from app.core.crud import CRUDBase
            from app.core.dependency import get_db
            from app.core.exceptions import IntegrityHandle, HttpExcHandle
            from app.core.init import register_routers, register_exceptions
            
            assert callable(init_api)
            assert CRUDBase is not None
            assert callable(get_db)
            assert callable(IntegrityHandle)
            assert callable(HttpExcHandle)
            assert callable(register_routers)
            assert callable(register_exceptions)
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")
    
    def test_import_models(self):
        """测试模型模块导入"""
        try:
            from app.models.base import BaseModel, TimestampMixin, Token, Success, Fail
            from app.models.login import JWTPayload, QQAccessToken, QQUserInfo
            from app.models.user import User
            
            assert BaseModel is not None
            assert TimestampMixin is not None
            assert Token is not None
            assert Success is not None
            assert Fail is not None
            assert JWTPayload is not None
            assert QQAccessToken is not None
            assert QQUserInfo is not None
            assert User is not None
        except ImportError as e:
            pytest.fail(f"Failed to import model modules: {e}")
    
    def test_import_controllers(self):
        """测试控制器模块导入"""
        try:
            from app.controllers.user import userController
            from app.controllers.role import roleController
            from app.controllers.department import deptController
            from app.controllers.menu import menuController
            from app.controllers.logs import loginLoginController, operationLogController, systemLogController
            from app.controllers.api import apiController
            
            assert userController is not None
            assert roleController is not None
            assert deptController is not None
            assert menuController is not None
            assert loginLoginController is not None
            assert operationLogController is not None
            assert systemLogController is not None
            assert apiController is not None
        except ImportError as e:
            pytest.fail(f"Failed to import controller modules: {e}")
    
    def test_import_settings(self):
        """测试设置模块导入"""
        try:
            from app.settings import settings
            from app.settings.config import base_config
            from app.settings.database import db_engine
            from app.settings.log import logger
            
            assert settings is not None
            assert base_config is not None
            assert callable(db_engine)
            assert logger is not None
        except ImportError as e:
            pytest.fail(f"Failed to import settings modules: {e}")


class TestBasicFunctionality:
    """基础功能测试类"""
    
    def test_password_functions_basic(self):
        """测试密码函数基本功能"""
        try:
            from app.utils.password import md5_encrypt, generate_password
            
            # 测试MD5加密
            result = md5_encrypt("hello")
            assert isinstance(result, str)
            assert len(result) == 32
            
            # 测试密码生成
            password = generate_password()
            assert isinstance(password, str)
            assert len(password) == 12
            
        except Exception as e:
            pytest.fail(f"Password functions failed: {e}")
    
    def test_time_conversion_basic(self):
        """测试时间转换基本功能"""
        try:
            from app.utils.localTime import convert_utc_to_local_time
            from datetime import datetime
            
            # 测试基本时间转换
            utc_time = "2023-12-07T12:00:00.000Z"
            result = convert_utc_to_local_time(utc_time)
            assert isinstance(result, datetime)
            
        except Exception as e:
            pytest.fail(f"Time conversion failed: {e}")
    
    def test_ip_utilities_basic(self):
        """测试IP工具基本功能"""
        try:
            from app.utils.ip import getIpAddress
            
            # 测试私有IP
            result = getIpAddress("127.0.0.1")
            assert isinstance(result, str)
            
        except Exception as e:
            pytest.fail(f"IP utilities failed: {e}")
    
    def test_model_creation_basic(self):
        """测试模型创建基本功能"""
        try:
            from app.models.base import Success, Fail
            from app.models.login import QQUserInfo
            
            # 测试响应模型
            success = Success(data={"test": "data"})
            assert success.status_code == 200
            
            fail = Fail(msg="test error")
            assert fail.status_code == 400
            
            # 测试QQ用户信息模型
            qq_user = QQUserInfo(
                openid="test_openid",
                nickname="test用户",
                avatar="http://example.com/avatar.jpg"
            )
            assert qq_user.openid == "test_openid"
            assert qq_user.nickname == "test用户"
            
        except Exception as e:
            pytest.fail(f"Model creation failed: {e}")


class TestModuleStructure:
    """模块结构测试类"""
    
    def test_main_modules_exist(self):
        """测试主要模块存在"""
        modules_to_test = [
            'app.utils',
            'app.core',
            'app.models',
            'app.controllers',
            'app.settings'
        ]
        
        for module_name in modules_to_test:
            try:
                import importlib
                module = importlib.import_module(module_name)
                assert module is not None
            except ImportError as e:
                pytest.fail(f"Module {module_name} not found: {e}")
    
    def test_submodules_structure(self):
        """测试子模块结构"""
        import app
        
        # 检查主要子模块是否存在
        expected_submodules = ['utils', 'core', 'models', 'controllers', 'settings']
        
        for submodule in expected_submodules:
            # 这里我们只检查模块目录是否存在，不强制要求所有子模块都能导入
            try:
                import importlib
                importlib.import_module(f'app.{submodule}')
                module_exists = True
            except ImportError:
                module_exists = False
            
            # 至少大部分模块应该存在
            assert module_exists or submodule in ['controllers']  # 允许某些模块可选
    
    def test_package_configuration(self):
        """测试包配置"""
        try:
            import app
            
            # 检查包的基本属性
            assert hasattr(app, '__name__')
            assert hasattr(app, '__file__')
            assert app.__name__ == 'app'
            
        except ImportError:
            pytest.fail("Failed to import app package")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])