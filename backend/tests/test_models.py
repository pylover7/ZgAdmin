"""models 层单元测试 — 序列化、校验、默认值、边界"""
import pytest
from datetime import datetime, timezone
from uuid import UUID

from app.models.base import BaseModel, TimestampMixin, Success, Fail, SuccessExtra, FailAuth
from app.models.user import User, UserCreate, UserUpdate, UpdatePassword
from app.models.role import Role, RoleCreate
from app.models.notice import Notice, NoticeCreate, NoticeRead
from app.models.security import SecurityPolicy, SecurityPolicyUpdate, IPRule, IPRuleCreate
from app.models.login import CredentialsSchema, JWTPayload, JWTOut
from app.models.file import File, FileCreate
from app.models.logs import LoginLog, OperationLog, SystemLog
from app.models.enums import MethodType


# ═══════════════════════════════════════════════════════════════════════
# BaseModel
# ═══════════════════════════════════════════════════════════════════════

class TestBaseModel:
    def test_id_auto_generated(self):
        user = User(
            username="test", email="t@t.com", password="12345678",
        )
        assert user.id is not None
        assert isinstance(user.id, UUID)

    @pytest.mark.asyncio
    async def test_to_dict(self):
        user = User(
            username="test", email="t@t.com", password="12345678",
        )
        d = await user.to_dict()
        assert "id" in d
        assert "username" in d
        assert d["username"] == "test"

    @pytest.mark.asyncio
    async def test_to_dict_exclude_fields(self):
        user = User(
            username="test", email="t@t.com", password="12345678",
        )
        d = await user.to_dict(exclude_fields=["password"])
        assert "password" not in d
        assert "username" in d

    @pytest.mark.asyncio
    async def test_to_dict_uuid_as_string(self):
        user = User(username="test", email="t@t.com", password="12345678")
        d = await user.to_dict()
        assert isinstance(d["id"], str)


# ═══════════════════════════════════════════════════════════════════════
# TimestampMixin
# ═══════════════════════════════════════════════════════════════════════

class TestTimestampMixin:
    def test_created_at_auto_filled(self):
        user = User(username="test", email="t@t.com", password="12345678")
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


# ═══════════════════════════════════════════════════════════════════════
# 响应模型
# ═══════════════════════════════════════════════════════════════════════

class TestResponseModels:
    def test_success_default(self):
        resp = Success()
        assert resp.status_code == 200
        data = resp.body.decode()
        assert '"code":200' in data
        assert '"success":true' in data

    def test_success_with_data(self):
        resp = Success(data={"key": "value"})
        assert resp.status_code == 200

    def test_fail_default(self):
        resp = Fail()
        assert resp.status_code == 400

    def test_fail_custom_code(self):
        resp = Fail(code=500, msg="Server Error")
        assert resp.status_code == 500

    def test_success_extra_pagination(self):
        resp = SuccessExtra(data=[], total=100, currentPage=1, pageSize=20)
        assert resp.status_code == 200

    def test_fail_auth(self):
        resp = FailAuth()
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# User 模型
# ═══════════════════════════════════════════════════════════════════════

class TestUserModel:
    def test_user_create_minimal(self):
        uc = UserCreate(
            username="testuser",
            email="test@example.com",
            password="12345678",
        )
        assert uc.username == "testuser"
        assert uc.status == 1  # 默认值
        assert uc.is_superuser is False

    def test_user_create_defaults(self):
        uc = UserCreate(
            username="test", email="t@t.com", password="12345678",
        )
        assert uc.sex == 1
        assert uc.status == 1
        assert uc.is_superuser is False

    def test_update_password_validation(self):
        up = UpdatePassword(current_password="old123456", new_password="new123456")
        assert up.current_password == "old123456"
        assert up.new_password == "new123456"


# ═══════════════════════════════════════════════════════════════════════
# Role 模型
# ═══════════════════════════════════════════════════════════════════════

class TestRoleModel:
    def test_role_create(self):
        rc = RoleCreate(name="管理员", code="admin", status=0)
        assert rc.name == "管理员"
        assert rc.status == 0

    def test_role_create_default_status(self):
        rc = RoleCreate(name="用户", code="user")
        assert rc.status == 0


# ═══════════════════════════════════════════════════════════════════════
# Notice 模型
# ═══════════════════════════════════════════════════════════════════════

class TestNoticeModel:
    def test_notice_create(self):
        nc = NoticeCreate(title="系统维护通知", content="今晚维护", type=0)
        assert nc.title == "系统维护通知"
        assert nc.type == 0
        assert nc.level == "info"  # 默认

    def test_notice_create_with_level(self):
        nc = NoticeCreate(title="紧急", content="", level="important")
        assert nc.level == "important"

    def test_notice_default_status_draft(self):
        nc = NoticeCreate(title="草稿", content="")
        assert nc.status == 0


# ═══════════════════════════════════════════════════════════════════════
# SecurityPolicy 模型
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityPolicyModel:
    def test_default_values(self):
        policy = SecurityPolicy()
        assert policy.min_password_length == 8
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digit is True
        assert policy.require_special is False
        assert policy.password_history_count == 3
        assert policy.max_login_attempts == 5
        assert policy.lockout_duration_minutes == 30
        assert policy.captcha_enabled is True

    def test_update_partial(self):
        update = SecurityPolicyUpdate(min_password_length=12)
        assert update.min_password_length == 12
        assert update.require_uppercase is None  # 未设置


# ═══════════════════════════════════════════════════════════════════════
# IPRule 模型
# ═══════════════════════════════════════════════════════════════════════

class TestIPRuleModel:
    def test_ip_rule_create(self):
        rule = IPRuleCreate(
            ip_cidr="192.168.1.0/24",
            rule_type="whitelist",
            description="内网",
        )
        assert rule.ip_cidr == "192.168.1.0/24"
        assert rule.rule_type == "whitelist"
        assert rule.is_active is True  # 默认

    def test_ip_rule_default_active(self):
        rule = IPRuleCreate(ip_cidr="10.0.0.1", rule_type="blacklist")
        assert rule.is_active is True


# ═══════════════════════════════════════════════════════════════════════
# Login 模型
# ═══════════════════════════════════════════════════════════════════════

class TestLoginModels:
    def test_credentials_schema(self):
        cred = CredentialsSchema(username="admin", password="pass")
        assert cred.username == "admin"
        assert cred.captcha_key is None
        assert cred.captcha_code is None

    def test_jwt_payload(self):
        payload = JWTPayload(
            user_id="abc",
            username="admin",
            is_superuser=True,
            exp=datetime.now(timezone.utc),
        )
        assert payload.user_id == "abc"
        assert payload.is_superuser is True


# ═══════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════

class TestEnums:
    def test_method_type_values(self):
        assert MethodType.GET.value == "GET"
        assert MethodType.POST.value == "POST"

    def test_method_type_get_member_values(self):
        values = MethodType.get_member_values()
        assert "GET" in values
        assert "POST" in values

    def test_method_type_get_member_names(self):
        names = MethodType.get_member_names()
        assert "GET" in names
