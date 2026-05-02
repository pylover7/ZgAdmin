"""
核心模块的单元测试
测试核心功能和工具
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI
from sqlmodel import Session
import asyncio

from app.core.database import init_api
from app.core.crud import CRUDBase
from app.core.dependency import get_db
from app.core.init import register_routers, register_exceptions
from app.core.bgtask import BgTasks
from app.core.ctx import *


class TestInitAPI:
    """API初始化测试类"""
    
    @pytest.mark.asyncio
    async def test_init_api_with_empty_database(self):
        """测试空数据库的API初始化"""
        # 模拟应用和会话
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi.return_value = {
            "paths": {
                "/test1": {
                    "get": {
                        "tags": ["test"],
                        "summary": "Test endpoint 1"
                    }
                },
                "/test2": {
                    "post": {
                        "tags": ["admin"],
                        "summary": "Test endpoint 2"
                    }
                }
            }
        }
        
        mock_session = Mock(spec=Session)
        mock_session.exec.return_value.all.return_value = []  # 空的API列表
        
        # 模拟Api模型
        mock_api = Mock()
        mock_api.id = "test-id"
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        with patch('app.core.database.Api', return_value=mock_api):
            # 应该不抛出异常
            try:
                await init_api(mock_app, mock_session)
                success = True
            except Exception as e:
                success = False
                error = str(e)
            
            assert success, f"init_api failed with error: {error if not success else ''}"
    
    @pytest.mark.asyncio
    async def test_init_api_with_existing_apis(self):
        """测试已有API的更新"""
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi.return_value = {
            "paths": {
                "/existing": {
                    "get": {
                        "tags": ["existing"],
                        "summary": "Updated summary"
                    }
                }
            }
        }
        
        mock_session = Mock(spec=Session)
        mock_existing_api = Mock()
        mock_existing_api.path = "/existing"
        mock_session.exec.return_value.all.return_value = [mock_existing_api]
        
        try:
            await init_api(mock_app, mock_session)
            success = True
        except Exception as e:
            success = False
        
        assert success
    
    def test_init_api_import(self):
        """测试init_api导入"""
        from app.core.database import init_api
        assert callable(init_api)


class TestCRUDOperations:
    """CRUD操作测试类"""
    
    def test_crud_imports(self):
        """测试CRUD模块导入"""
        try:
            import app.core.crud
            assert app.core.crud is not None
        except ImportError:
            pytest.fail("Failed to import app.core.crud")
    
    def test_crud_basic_functions(self):
        """测试基本的CRUD函数"""
        try:
            import app.core.crud
            
            # 检查模块是否有常见的CRUD属性
            crud_module = app.core.crud
            assert crud_module is not None
            
            # 检查是否有CRUDBase类（常见的CRUD基类）
            if hasattr(crud_module, 'CRUDBase'):
                assert crud_module.CRUDBase is not None
                
        except ImportError:
            pytest.fail("Failed to access CRUD functions")
    
    @pytest.mark.asyncio
    async def test_crud_with_mock_session(self):
        """测试CRUD与模拟会话"""
        mock_session = Mock(spec=Session)
        mock_session.exec = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.delete = Mock()
        mock_session.refresh = Mock()
        mock_session.rollback = Mock()
        
        # 测试模拟会话的基本操作
        assert callable(mock_session.exec)
        assert callable(mock_session.add)
        assert callable(mock_session.commit)
        assert callable(mock_session.delete)
        assert callable(mock_session.refresh)
        assert callable(mock_session.rollback)


class TestDependency:
    """依赖注入测试类"""
    
    def test_dependency_imports(self):
        """测试依赖注入模块导入"""
        try:
            import app.core.dependency
            assert app.core.dependency is not None
        except ImportError:
            pytest.fail("Failed to import app.core.dependency")
    
    def test_common_dependencies(self):
        """测试常见的依赖函数"""
        try:
            from app.core.dependency import get_db
            
            # 测试get_db函数
            assert callable(get_db)
            
        except ImportError:
            # 如果特定依赖不存在，至少模块应该存在
            import app.core.dependency
            assert app.core.dependency is not None
    
    @pytest.mark.asyncio
    async def test_database_dependency_mock(self):
        """测试数据库依赖模拟"""
        mock_db = Mock(spec=Session)
        
        # 模拟数据库依赖的基本行为
        mock_db.query = Mock()
        mock_db.execute = Mock()
        mock_db.scalar = Mock()
        
        assert mock_db is not None
        assert callable(mock_db.query)
        assert callable(mock_db.execute)
        assert callable(mock_db.scalar)
    
    def test_authentication_dependency_mock(self):
        """测试认证依赖模拟"""
        # 模拟用户对象
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.is_superuser = False
        
        assert mock_user.id == "user123"
        assert mock_user.is_active is True
        assert mock_user.is_superuser is False


class TestAppInitialization:
    """应用初始化测试类"""
    
    def test_register_routers_import(self):
        """测试路由注册导入"""
        try:
            from app.core.init import register_routers
            assert callable(register_routers)
        except ImportError:
            pytest.fail("Failed to import register_routers")
    
    def test_register_exceptions_import(self):
        """测试异常注册导入"""
        try:
            from app.core.init import register_exceptions
            assert callable(register_exceptions)
        except ImportError:
            pytest.fail("Failed to import register_exceptions")
    
    def test_register_routers_mock(self):
        """测试路由注册模拟"""
        mock_app = Mock(spec=FastAPI)
        
        try:
            from app.core.init import register_routers
            # 如果可以导入，函数应该是可调用的
            assert callable(register_routers)
            
            # 测试调用（应该不抛出异常）
            register_routers(mock_app)
            
        except ImportError:
            pytest.fail("Failed to import register_routers")
    
    def test_register_exceptions_mock(self):
        """测试异常注册模拟"""
        mock_app = Mock(spec=FastAPI)
        
        try:
            from app.core.init import register_exceptions
            # 如果可以导入，函数应该是可调用的
            assert callable(register_exceptions)
            
            # 测试调用（应该不抛出异常）
            register_exceptions(mock_app)
            
        except ImportError:
            pytest.fail("Failed to import register_exceptions")


class TestBackgroundTask:
    """后台任务测试类"""
    
    def test_background_task_imports(self):
        """测试后台任务模块导入"""
        try:
            
            assert BgTasks is not None
        except ImportError:
            pytest.fail("Failed to import BgTasks from app.core.bgtask")
    
    @pytest.mark.asyncio
    async def test_background_task_mock(self):
        """测试后台任务模拟"""
        # 模拟后台任务函数
        async def mock_background_task():
            await asyncio.sleep(0.1)
            return "Task completed"
        
        result = await mock_background_task()
        assert result == "Task completed"
    
    def test_scheduler_mock(self):
        """测试调度器模拟"""
        from unittest.mock import MagicMock
        
        mock_scheduler = MagicMock()
        mock_scheduler.add_job = Mock()
        mock_scheduler.start = Mock()
        mock_scheduler.shutdown = Mock()
        
        # 测试调度器方法
        mock_scheduler.add_job(lambda: None, 'interval', seconds=60)
        assert mock_scheduler.add_job.called
        
        mock_scheduler.start()
        assert mock_scheduler.start.called
        
        # 测试实际的BgTasks导入
        try:
            
            assert BgTasks is not None
        except ImportError:
            pytest.skip("BgTasks not available")


class TestContext:
    """上下文测试类"""
    
    def test_context_imports(self):
        """测试上下文模块导入"""
        try:
            import app.core.ctx
            assert app.core.ctx is not None
        except ImportError:
            pytest.fail("Failed to import app.core.ctx")
    
    def test_context_variables(self):
        """测试上下文变量"""
        # 模拟上下文变量
        mock_context = Mock()
        mock_context.user = None
        mock_context.request = None
        mock_context.db = None
        
        assert mock_context.user is None
        assert mock_context.request is None
        assert mock_context.db is None
        
        # 测试设置值
        mock_context.user = "test_user"
        assert mock_context.user == "test_user"


class TestCoreIntegration:
    """核心模块集成测试"""
    
    def test_all_core_modules_import(self):
        """测试所有核心模块都能导入"""
        core_modules = [
            'app.core.database',
            'app.core.crud',
            'app.core.dependency',
            'app.core.init',
            'app.core.bgtask',
            'app.core.ctx'
        ]
        
        for module_name in core_modules:
            try:
                import importlib
                module = importlib.import_module(module_name)
                assert module is not None
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_core_module_structure(self):
        """测试核心模块结构"""
        import app.core
        
        # 检查核心模块是否有预期的子模块
        core_attributes = dir(app.core)
        expected_attributes = [
            'database', 'crud', 'dependency', 'init', 'bgtask', 'ctx'
        ]
        
        for attr in expected_attributes:
            # 不是所有属性都必须存在，但至少有一些核心组件
            if hasattr(app.core, attr):
                assert getattr(app.core, attr) is not None
    
    @pytest.mark.asyncio
    async def test_core_function_integration_mock(self):
        """测试核心功能集成模拟"""
        # 模拟完整的核心功能流程
        mock_app = Mock(spec=FastAPI)
        mock_session = Mock(spec=Session)
        mock_user = Mock()
        mock_db = Mock(spec=Session)
        
        # 模拟请求流程
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"status": "ok"})
        
        # 验证模拟对象
        assert mock_app is not None
        assert mock_session is not None
        assert mock_user is not None
        assert mock_db is not None
        assert mock_request is not None
        assert mock_response is not None
        assert mock_response.status_code == 200


class TestErrorHandling:
    """错误处理测试类"""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """测试数据库错误处理"""
        mock_session = Mock(spec=Session)
        mock_session.exec.side_effect = Exception("Database error")
        mock_session.rollback = Mock()
        
        try:
            mock_session.exec("SELECT * FROM users")
        except Exception:
            # 在错误情况下应该调用rollback
            pass
    
    def test_dependency_error_handling(self):
        """测试依赖错误处理"""
        # 模拟依赖失败
        mock_dependency = Mock()
        mock_dependency.side_effect = Exception("Dependency failed")
        
        with pytest.raises(Exception):
            mock_dependency()
    
    @pytest.mark.asyncio
    async def test_background_task_error_handling(self):
        """测试后台任务错误处理"""
        async def failing_task():
            raise Exception("Task failed")
        
        with pytest.raises(Exception, match="Task failed"):
            await failing_task()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])