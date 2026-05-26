"""core/exceptions.py 单元测试 — 异常处理器"""
import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    SettingNotFound,
    IntegrityHandle,
    HttpExcHandle,
    RequestValidationHandle,
    ResponseValidationHandle,
)
from app.core.init import register_exceptions


class TestExceptionHandlers:
    @pytest.fixture
    def exc_app(self):
        app = FastAPI()
        register_exceptions(app)
        return app

    @pytest.mark.asyncio
    async def test_integrity_handle(self, exc_app):
        from fastapi import Request
        from starlette.responses import JSONResponse

        mock_request = Request({"type": "http", "headers": []})
        exc = IntegrityError("stmt", "params", Exception("orig"))
        response = await IntegrityHandle(mock_request, exc)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_http_exc_handle_500(self, exc_app):
        from fastapi import Request, HTTPException
        from starlette.responses import JSONResponse

        mock_request = Request({"type": "http", "headers": []})
        exc = HTTPException(status_code=500, detail="Server Error")
        response = await HttpExcHandle(mock_request, exc)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_http_exc_handle_404(self, exc_app):
        from fastapi import Request, HTTPException
        from starlette.responses import JSONResponse

        mock_request = Request({"type": "http", "headers": []})
        exc = HTTPException(status_code=404, detail="Not Found")
        response = await HttpExcHandle(mock_request, exc)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_request_validation_handle(self):
        from fastapi import Request
        from starlette.responses import JSONResponse

        mock_request = Request({"type": "http", "headers": []})
        exc = RequestValidationError([])
        response = await RequestValidationHandle(mock_request, exc)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_response_validation_handle(self):
        from fastapi import Request
        from starlette.responses import JSONResponse

        mock_request = Request({"type": "http", "headers": []})
        exc = ResponseValidationError([])
        response = await ResponseValidationHandle(mock_request, exc)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestSettingNotFound:
    def test_is_exception(self):
        exc = SettingNotFound()
        assert isinstance(exc, Exception)
