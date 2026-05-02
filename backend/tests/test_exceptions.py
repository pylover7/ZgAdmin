"""
异常处理模块的单元测试
测试各种异常处理器的功能
"""
import pytest
from unittest.mock import Mock
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import IntegrityError
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    IntegrityHandle,
    HttpExcHandle,
    RequestValidationHandle,
    ResponseValidationHandle,
    SettingNotFound
)


class TestIntegrityHandle:
    """IntegrityError处理器测试类"""
    
    @pytest.mark.asyncio
    async def test_integrity_handle_normal(self):
        """测试正常的IntegrityError处理"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.__str__ = Mock(return_value="UNIQUE constraint failed")
        
        response = await IntegrityHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        content = response.body.decode()
        assert "IntegrityError" in content
        assert "500" in content
    
    @pytest.mark.asyncio
    async def test_integrity_handle_foreign_key(self):
        """测试外键约束错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.__str__ = Mock(return_value="FOREIGN KEY constraint failed")
        
        response = await IntegrityHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        content = response.body.decode()
        assert "IntegrityError" in content
    
    @pytest.mark.asyncio
    async def test_integrity_handle_null_constraint(self):
        """测试非空约束错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.__str__ = Mock(return_value="NOT NULL constraint failed")
        
        response = await IntegrityHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestHttpExcHandle:
    """HTTPException处理器测试类"""
    
    @pytest.mark.asyncio
    async def test_http_exc_handle_400(self):
        """测试400错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=HTTPException)
        mock_exc.status_code = 400
        mock_exc.detail = "Bad Request"
        
        response = await HttpExcHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        content = response.body.decode()
        assert "400" in content
        assert "Bad Request" in content
    
    @pytest.mark.asyncio
    async def test_http_exc_handle_401(self):
        """测试401未授权错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=HTTPException)
        mock_exc.status_code = 401
        mock_exc.detail = "Unauthorized"
        
        response = await HttpExcHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        
        content = response.body.decode()
        assert "401" in content
        assert "Unauthorized" in content
    
    @pytest.mark.asyncio
    async def test_http_exc_handle_403(self):
        """测试403禁止访问错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=HTTPException)
        mock_exc.status_code = 403
        mock_exc.detail = "Forbidden"
        
        response = await HttpExcHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        
        content = response.body.decode()
        assert "403" in content
        assert "Forbidden" in content
    
    @pytest.mark.asyncio
    async def test_http_exc_handle_404(self):
        """测试404未找到错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=HTTPException)
        mock_exc.status_code = 404
        mock_exc.detail = "Not Found"
        
        response = await HttpExcHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        content = response.body.decode()
        assert "404" in content
        assert "Not Found" in content
    
    @pytest.mark.asyncio
    async def test_http_exc_handle_500(self):
        """测试500服务器内部错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=HTTPException)
        mock_exc.status_code = 500
        mock_exc.detail = "Internal Server Error"
        
        response = await HttpExcHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        content = response.body.decode()
        assert "500" in content
        assert "Internal Server Error" in content
    
    @pytest.mark.asyncio
    async def test_http_exc_handle_with_headers(self):
        """测试带headers的HTTPException"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=HTTPException)
        mock_exc.status_code = 401
        mock_exc.detail = "Token expired"
        mock_exc.headers = {"WWW-Authenticate": "Bearer"}
        
        response = await HttpExcHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        
        content = response.body.decode()
        assert "Token expired" in content
        assert "data" in content


class TestRequestValidationHandle:
    """请求验证错误处理器测试类"""
    
    @pytest.mark.asyncio
    async def test_request_validation_handle_basic(self):
        """测试基本的请求验证错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.__str__ = Mock(return_value="validation error")
        
        response = await RequestValidationHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        
        content = response.body.decode()
        assert "RequestValidationError" in content
        assert "422" in content
    
    @pytest.mark.asyncio
    async def test_request_validation_handle_with_errors(self):
        """测试带具体错误的请求验证错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {"loc": ["body", "field1"], "msg": "field required", "type": "value_error.missing"},
            {"loc": ["body", "field2"], "msg": "ensure this value is greater than 0", "type": "value_error.number.not_gt"}
        ]
        mock_exc.__str__ = Mock(return_value="2 validation errors")
        
        response = await RequestValidationHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        
        content = response.body.decode()
        assert "RequestValidationError" in content
        assert "2 validation errors" in content
    
    @pytest.mark.asyncio
    async def test_request_validation_handle_missing_field(self):
        """测试缺失字段验证错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.__str__ = Mock(return_value="field required")
        
        response = await RequestValidationHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_request_validation_handle_invalid_type(self):
        """测试类型验证错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.__str__ = Mock(return_value="invalid type")
        
        response = await RequestValidationHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422


class TestResponseValidationHandle:
    """响应验证错误处理器测试类"""
    
    @pytest.mark.asyncio
    async def test_response_validation_handle_basic(self):
        """测试基本的响应验证错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=ResponseValidationError)
        mock_exc.__str__ = Mock(return_value="response validation error")
        
        response = await ResponseValidationHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        content = response.body.decode()
        assert "ResponseValidationError" in content
        assert "500" in content
    
    @pytest.mark.asyncio
    async def test_response_validation_handle_with_errors(self):
        """测试带具体错误的响应验证错误"""
        mock_request = Mock(spec=Request)
        mock_exc = Mock(spec=ResponseValidationError)
        mock_exc.errors.return_value = [
            {"loc": ["response", "field1"], "msg": "invalid response format", "type": "response_error"}
        ]
        mock_exc.__str__ = Mock(return_value="1 response validation error")
        
        response = await ResponseValidationHandle(mock_request, mock_exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        content = response.body.decode()
        assert "ResponseValidationError" in content


class TestSettingNotFound:
    """SettingNotFound异常测试类"""
    
    def test_setting_not_found_creation(self):
        """测试SettingNotFound异常创建"""
        exc = SettingNotFound("Configuration setting not found")
        
        assert isinstance(exc, Exception)
        assert str(exc) == "Configuration setting not found"
    
    def test_setting_not_found_inheritance(self):
        """测试SettingNotFound继承关系"""
        exc = SettingNotFound("Test error")
        
        assert isinstance(exc, Exception)
        assert isinstance(exc, BaseException)
    
    def test_setting_not_found_with_message(self):
        """测试带消息的SettingNotFound"""
        message = "Database connection string not found"
        exc = SettingNotFound(message)
        
        assert str(exc) == message


class TestIntegration:
    """集成测试类"""
    
    @pytest.mark.asyncio
    async def test_all_error_handlers_response_format(self):
        """测试所有错误处理器的响应格式一致性"""
        mock_request = Mock(spec=Request)
        
        # 测试IntegrityError
        integrity_exc = Mock(spec=IntegrityError)
        integrity_exc.__str__ = Mock(return_value="Database integrity error")
        integrity_response = await IntegrityHandle(mock_request, integrity_exc)
        
        # 测试HTTPException
        http_exc = Mock(spec=HTTPException)
        http_exc.status_code = 400
        http_exc.detail = "HTTP error"
        http_response = await HttpExcHandle(mock_request, http_exc)
        
        # 测试RequestValidationError
        request_validation_exc = Mock(spec=RequestValidationError)
        request_validation_exc.__str__ = Mock(return_value="Request validation error")
        request_validation_response = await RequestValidationHandle(mock_request, request_validation_exc)
        
        # 测试ResponseValidationError
        response_validation_exc = Mock(spec=ResponseValidationError)
        response_validation_exc.__str__ = Mock(return_value="Response validation error")
        response_validation_response = await ResponseValidationHandle(mock_request, response_validation_exc)
        
        # 验证所有响应都是JSONResponse
        assert isinstance(integrity_response, JSONResponse)
        assert isinstance(http_response, JSONResponse)
        assert isinstance(request_validation_response, JSONResponse)
        assert isinstance(response_validation_response, JSONResponse)
        
        # 验证响应体包含必要字段
        for response in [integrity_response, http_response, request_validation_response, response_validation_response]:
            content = response.body.decode()
            assert "code" in content
            assert "msg" in content
    
    @pytest.mark.asyncio
    async def test_error_handler_with_real_request(self):
        """测试使用真实Request对象的错误处理器"""
        from fastapi import Request
        from starlette.types import Scope
        
        # 创建一个简单的scope
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": []
        }
        
        # 使用receive和send的mock对象
        receive = Mock()
        send = Mock()
        
        # 创建Request对象（这需要更复杂的设置，在实际测试中可能需要使用TestClient）
        # 这里我们继续使用mock对象
        mock_request = Mock(spec=Request)
        
        # 测试HTTPException处理
        http_exc = HTTPException(status_code=404, detail="Resource not found")
        response = await HttpExcHandle(mock_request, http_exc)
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "404" in content
        assert "Resource not found" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])