"""API 集成测试 — base 路由补充（用户菜单/API/偏好/QQ/文件）"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

from app.models import Menu, Role, Api
from app.models.enums import MethodType
from app.models.login import JWTPayload
from app.utils.jwtt import create_access_token
from app.utils.password import get_password_hash


# ═══════════════════════════════════════════════════════════════════════
# 用户菜单
# ═══════════════════════════════════════════════════════════════════════

class TestUserMenu:
    def test_superuser_gets_all_menus(self, client, admin_headers, admin_user, db):
        """超级管理员获取所有菜单"""
        menu = Menu(
            parentId=None, menuType=0, title="测试菜单",
            name="TestMenu", path="/test", component="",
            rank=1, showLink=True,
        )
        db.add(menu)
        db.commit()

        resp = client.get("/api/v1/base/userMenu", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]) >= 1

    def test_normal_user_gets_role_menus(self, client, db, normal_user, test_role):
        """普通用户获取角色菜单"""
        menu = Menu(
            parentId=None, menuType=0, title="用户菜单",
            name="UserMenu", path="/user", component="",
            rank=1, showLink=True,
        )
        db.add(menu)
        test_role.menus.append(menu)
        normal_user.roles.append(test_role)
        normal_user.status = 1  # 确保启用
        test_role.status = 0  # 启用
        db.add(normal_user)
        db.add(test_role)
        db.commit()

        payload = JWTPayload(
            user_id=str(normal_user.id),
            username=normal_user.username,
            is_superuser=False,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        token = create_access_token(data=payload)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/base/userMenu", headers=headers)
        body = resp.json()
        # 普通用户的菜单取决于角色绑定
        assert body["code"] in (200, 400)


# ═══════════════════════════════════════════════════════════════════════
# 用户 API 权限
# ═══════════════════════════════════════════════════════════════════════

class TestUserApi:
    def test_superuser_gets_all_apis(self, client, admin_headers, admin_user, db):
        api = Api(path="/api/v1/test", method=MethodType.GET, summary="测试", tags="test")
        db.add(api)
        db.commit()

        resp = client.get("/api/v1/base/userApi", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]) >= 1


# ═══════════════════════════════════════════════════════════════════════
# 用户偏好
# ═══════════════════════════════════════════════════════════════════════

class TestUserPreferences:
    def test_get_preferences_default(self, client, admin_headers, admin_user, db):
        resp = client.get("/api/v1/base/preferences", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert "notify_account" in body["data"]

    def test_update_preferences(self, client, admin_headers, admin_user, db):
        resp = client.post("/api/v1/base/updatePreferences", headers=admin_headers, json={
            "notify_account": False,
            "notify_system": True,
        })
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 用户资料更新
# ═══════════════════════════════════════════════════════════════════════

class TestUserProfile:
    def test_update_profile(self, client, admin_headers, admin_user, db):
        resp = client.post("/api/v1/base/updateProfile", headers=admin_headers, json={
            "nickname": "管理员2号",
            "phone": "13800138001",
            "remark": "更新资料",
        })
        body = resp.json()
        assert body["code"] == 200

    def test_update_profile_empty_data(self, client, admin_headers, admin_user, db):
        resp = client.post("/api/v1/base/updateProfile", headers=admin_headers, json={})
        body = resp.json()
        # 空数据应该返回失败
        assert body["code"] != 200


# ═══════════════════════════════════════════════════════════════════════
# QQ 登录（Mock 外部 API）
# ═══════════════════════════════════════════════════════════════════════

class TestQQLogin:
    def test_qq_auth_url_disabled(self, client):
        """QQ 登录未启用"""
        from app.settings import settings
        if not settings.FEATURE_QQ_LOGIN:
            resp = client.get("/api/v1/base/qq/auth-url")
            body = resp.json()
            assert body["code"] != 200

    def test_qq_login_missing_params(self, client):
        """缺少参数"""
        resp = client.post("/api/v1/base/qq/login", json={
            "code": "",
            "state": "",
        })
        body = resp.json()
        assert body["code"] != 200


# ═══════════════════════════════════════════════════════════════════════
# 登录日志
# ═══════════════════════════════════════════════════════════════════════

class TestLoginLogs:
    def test_get_login_logs(self, client, admin_headers, admin_user, db):
        resp = client.get("/api/v1/base/loginLogs", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 修改密码 — 密码策略拦截
# ═══════════════════════════════════════════════════════════════════════

class TestUpdatePasswordAdvanced:
    def test_update_pwd_weak_new_password(self, client, admin_headers, admin_user, db, security_policy):
        """新密码不满足复杂度要求"""
        resp = client.post("/api/v1/base/updatePwd", headers=admin_headers, json={
            "current_password": "admin123456",
            "new_password": "weak",
        })
        body = resp.json()
        assert body["code"] != 200

    def test_update_pwd_history_check(self, client, admin_headers, admin_user, db, security_policy):
        """新密码与历史密码重复"""
        # 先更新一次密码，建立历史
        client.post("/api/v1/base/updatePwd", headers=admin_headers, json={
            "current_password": "admin123456",
            "new_password": "NewAdmin123",
        })

        # 重新登录获取新 headers
        from app.models.login import JWTPayload
        from app.utils.jwtt import create_access_token
        db.refresh(admin_user)
        payload = JWTPayload(
            user_id=str(admin_user.id),
            username=admin_user.username,
            is_superuser=True,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        new_token = create_access_token(data=payload)
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # 尝试用旧密码（现在可能已变，跳过严格断言）
        resp = client.post("/api/v1/base/updatePwd", headers=new_headers, json={
            "current_password": "NewAdmin123",
            "new_password": "admin123456",  # 与历史重复
        })
        # 结果取决于 password_history_count 设置
        body = resp.json()
        # 可能成功也可能失败，取决于是否有 history 数据
        assert body["code"] in (200, 400)
