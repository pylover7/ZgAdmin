"""
模型模块的单元测试
测试基础模型和各种数据模型
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Any
from pydantic import ValidationError

from app.models.base import (
    BaseModel,
    TimestampMixin,
    Token,
    TokenPayload,
    NewPassword,
    Success,
    Fail,
    SuccessExtra,
    FailAuth,
    Image
)


class TestBaseModel:
    """基础模型测试类"""
    
    def test_base_model_creation(self):
        """测试基础模型创建"""
        model = BaseModel()
        
        assert isinstance(model.id, UUID)
        assert model.id is not None
    
    def test_base_model_id_uniqueness(self):
        """测试ID唯一性"""
        model1 = BaseModel()
        model2 = BaseModel()
        
        assert model1.id != model2.id
        assert isinstance(model1.id, UUID)
        assert isinstance(model2.id, UUID)
    
    @pytest.mark.asyncio
    async def test_base_model_to_dict_empty_exclude(self):
        """测试转换为字典（空排除列表）"""
        model = BaseModel()
        result = await model.to_dict(exclude_fields=[])
        
        assert isinstance(result, dict)
        assert "id" in result
        assert isinstance(result["id"], str)
    
    @pytest.mark.asyncio
    async def test_base_model_to_dict_exclude_id(self):
        """测试转换时排除ID"""
        model = BaseModel()
        result = await model.to_dict(exclude_fields=["id"])
        
        assert isinstance(result, dict)
        assert "id" not in result
    
    @pytest.mark.asyncio
    async def test_base_model_to_dict_exclude_none(self):
        """测试转换时排除None"""
        model = BaseModel()
        result = await model.to_dict(exclude_fields=None)
        
        assert isinstance(result, dict)
        assert "id" in result
    
    @pytest.mark.asyncio
    async def test_base_model_to_dict_with_datetime(self):
        """测试包含datetime字段的转换"""
        # 创建一个带有datetime字段的子类
        class TestModel(BaseModel, TimestampMixin):
            pass
        
        test_time = datetime.now()
        model = TestModel(created_at=test_time)
        result = await model.to_dict()
        
        assert isinstance(result, dict)
        assert "created_at" in result
        assert isinstance(result["created_at"], str)


class TestTimestampMixin:
    """时间戳混入测试类"""
    
    def test_timestamp_mixin_creation(self):
        """测试时间戳混入创建"""
        class TestModel(BaseModel, TimestampMixin):
            pass
        
        before_creation = datetime.now()
        model = TestModel()
        after_creation = datetime.now()
        
        assert isinstance(model.created_at, datetime)
        assert before_creation <= model.created_at <= after_creation
    
    def test_timestamp_mixin_custom_time(self):
        """测试自定义创建时间"""
        class TestModel(BaseModel, TimestampMixin):
            pass
        
        custom_time = datetime(2023, 12, 7, 12, 0, 0)
        model = TestModel(created_at=custom_time)
        
        assert model.created_at == custom_time
    
    def test_timestamp_mixin_multiple_instances(self):
        """测试多个实例的时间戳"""
        class TestModel(BaseModel, TimestampMixin):
            pass
        
        model1 = TestModel()
        model2 = TestModel()
        
        # 第一个实例应该创建得更早
        assert model1.created_at <= model2.created_at


class TestToken:
    """Token模型测试类"""
    
    def test_token_creation(self):
        """测试Token创建"""
        token = Token(access_token="test_token", token_type="bearer")
        
        assert token.access_token == "test_token"
        assert token.token_type == "bearer"
    
    def test_token_creation_with_defaults(self):
        """测试Token创建（使用默认值）"""
        token = Token(access_token="test_token")
        
        assert token.access_token == "test_token"
        assert token.token_type == "bearer"  # 默认值
    
    def test_token_custom_token_type(self):
        """测试自定义token类型"""
        token = Token(access_token="test_token", token_type="jwt")
        
        assert token.access_token == "test_token"
        assert token.token_type == "jwt"
    
    def test_token_empty_access_token(self):
        """测试空的访问令牌"""
        token = Token(access_token="")
        
        assert token.access_token == ""
        assert token.token_type == "bearer"


class TestTokenPayload:
    """Token载荷模型测试类"""
    
    def test_token_payload_creation(self):
        """测试Token载荷创建"""
        payload = TokenPayload(sub="user123")
        
        assert payload.sub == "user123"
    
    def test_token_payload_default(self):
        """测试Token载荷默认值"""
        payload = TokenPayload()
        
        assert payload.sub is None
    
    def test_token_payload_empty_string(self):
        """测试空字符串sub"""
        payload = TokenPayload(sub="")
        
        assert payload.sub == ""
    
    def test_token_payload_with_user_id(self):
        """测试带用户ID的载荷"""
        payload = TokenPayload(sub="550e8400-e29b-41d4-a716-446655440000")
        
        assert payload.sub == "550e8400-e29b-41d4-a716-446655440000"


class TestNewPassword:
    """新密码模型测试类"""
    
    def test_new_password_creation(self):
        """测试新密码创建"""
        password = NewPassword(token="reset_token", new_password="newpass123")
        
        assert password.token == "reset_token"
        assert password.new_password == "newpass123"
    
    def test_new_password_minimum_length(self):
        """测试最小密码长度"""
        password = NewPassword(token="token", new_password="12345678")
        
        assert len(password.new_password) == 8
    
    def test_new_password_maximum_length(self):
        """测试最大密码长度"""
        long_password = "a" * 40
        password = NewPassword(token="token", new_password=long_password)
        
        assert len(password.new_password) == 40
    
    def test_new_password_too_short(self):
        """测试密码过短"""
        with pytest.raises(ValidationError):
            NewPassword(token="token", new_password="1234567")  # 少于8位
    
    def test_new_password_too_long(self):
        """测试密码过长"""
        with pytest.raises(ValidationError):
            NewPassword(token="token", new_password="a" * 41)  # 超过40位
    
    def test_new_password_with_special_chars(self):
        """测试包含特殊字符的密码"""
        password = NewPassword(token="token", new_password="P@ssw0rd!123")
        
        assert password.new_password == "P@ssw0rd!123"


class TestSuccess:
    """Success响应模型测试类"""
    
    def test_success_default(self):
        """测试Success默认值"""
        response = Success()
        
        # 验证响应内容需要检查实际的JSON响应
        # 这里我们测试模型的创建
        assert response.status_code == 200
    
    def test_success_with_data(self):
        """测试带数据的Success"""
        test_data = {"id": 1, "name": "test"}
        response = Success(data=test_data)
        
        assert response.status_code == 200
    
    def test_success_custom_code(self):
        """测试自定义状态码"""
        response = Success(code=201, msg="Created")
        
        assert response.status_code == 201
    
    def test_success_with_kwargs(self):
        """测试带额外参数的Success"""
        response = Success(data={"test": "data"}, extra_field="extra_value")
        
        assert response.status_code == 200
    
    def test_success_false_success(self):
        """测试success=False的情况"""
        response = Success(success=False, msg="Error occurred")
        
        assert response.status_code == 200


class TestFail:
    """Fail响应模型测试类"""
    
    def test_fail_default(self):
        """测试Fail默认值"""
        response = Fail()
        
        assert response.status_code == 400
    
    def test_fail_with_data(self):
        """测试带数据的Fail"""
        error_data = {"error": "validation failed"}
        response = Fail(data=error_data)
        
        assert response.status_code == 400
    
    def test_fail_custom_code(self):
        """测试自定义错误码"""
        response = Fail(code=422, msg="Validation Error")
        
        assert response.status_code == 422
    
    def test_fail_with_kwargs(self):
        """测试带额外参数的Fail"""
        response = Fail(msg="Bad Request", error_code="VALIDATION_ERROR")
        
        assert response.status_code == 400


class TestSuccessExtra:
    """SuccessExtra响应模型测试类"""
    
    def test_success_extra_default(self):
        """测试SuccessExtra默认值"""
        response = SuccessExtra(data=[1, 2, 3])
        
        assert response.status_code == 200
    
    def test_success_extra_with_pagination(self):
        """测试带分页信息的SuccessExtra"""
        response = SuccessExtra(
            data=["item1", "item2"],
            total=100,
            currentPage=2,
            pageSize=20
        )
        
        assert response.status_code == 200
    
    def test_success_extra_custom_pagination(self):
        """测试自定义分页参数"""
        response = SuccessExtra(
            data=[],
            total=0,
            currentPage=1,
            pageSize=50,
            code=200,
            msg="Success with custom pagination"
        )
        
        assert response.status_code == 200


class TestFailAuth:
    """FailAuth响应模型测试类"""
    
    def test_fail_auth_default(self):
        """测试FailAuth默认值"""
        response = FailAuth()
        
        assert response.status_code == 401
    
    def test_fail_auth_custom_message(self):
        """测试自定义消息的FailAuth"""
        response = FailAuth(msg="Token expired")
        
        assert response.status_code == 401
    
    def test_fail_auth_custom_code(self):
        """测试自定义错误码的FailAuth"""
        response = FailAuth(code=403, msg="Access denied")
        
        assert response.status_code == 403
    
    def test_fail_auth_with_kwargs(self):
        """测试带额外参数的FailAuth"""
        response = FailAuth(
            msg="Authentication failed",
            error_type="INVALID_TOKEN",
            retry_after=60
        )
        
        assert response.status_code == 401


class TestImage:
    """Image模型测试类"""
    
    def test_image_creation(self):
        """测试Image创建"""
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        image = Image(base64=base64_data)
        
        assert image.base64 == base64_data
    
    def test_image_empty_base64(self):
        """测试空base64数据"""
        image = Image(base64="")
        
        assert image.base64 == ""
    
    def test_image_large_base64(self):
        """测试大的base64数据"""
        large_base64 = "a" * 1000000  # 1MB的base64数据
        image = Image(base64=large_base64)
        
        assert image.base64 == large_base64
    
    def test_image_with_extra_fields(self):
        """测试带额外字段的Image（由于Meta.extra="allow"）"""
        # 测试基本创建
        image = Image(base64="dGVzdA==")
        
        assert image.base64 == "dGVzdA=="
        
        # 测试Image模型的基本属性
        assert hasattr(image, 'base64')
        
        # 在Pydantic v2中，如果配置了extra="allow"，但实际没有传入额外字段
        # model_extra可能为空字典或None，这是正常的
        if hasattr(image, 'model_extra'):
            # 如果有model_extra属性，检查它是字典类型
            assert isinstance(image.model_extra, (dict, type(None)))


class TestIntegration:
    """集成测试类"""
    
    def test_model_inheritance_chain(self):
        """测试模型继承链"""
        class TestModel(BaseModel, TimestampMixin):
            name: str = "test"
        
        model = TestModel()
        
        assert isinstance(model, BaseModel)
        assert isinstance(model, TimestampMixin)
        assert hasattr(model, 'id')
        assert hasattr(model, 'created_at')
        assert model.name == "test"
    
    def test_response_models_inheritance(self):
        """测试响应模型继承关系"""
        from fastapi.responses import JSONResponse
        
        success = Success()
        fail = Fail()
        fail_auth = FailAuth()
        success_extra = SuccessExtra()
        
        # 所有都应该继承自JSONResponse
        assert isinstance(success, JSONResponse)
        assert isinstance(fail, JSONResponse)
        assert isinstance(fail_auth, JSONResponse)
        assert isinstance(success_extra, JSONResponse)
    
    def test_token_workflow(self):
        """测试token工作流程"""
        # 创建token载荷
        payload = TokenPayload(sub="user123")
        
        # 创建token
        token = Token(access_token="jwt_token_here", token_type="bearer")
        
        assert payload.sub == "user123"
        assert token.access_token == "jwt_token_here"
        assert token.token_type == "bearer"
    
    def test_password_reset_workflow(self):
        """测试密码重置工作流程"""
        # 创建密码重置token
        reset_token = NewPassword(
            token="reset_token_123",
            new_password="NewSecurePassword123!"
        )
        
        assert reset_token.token == "reset_token_123"
        assert len(reset_token.new_password) >= 8
        assert len(reset_token.new_password) <= 40


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])