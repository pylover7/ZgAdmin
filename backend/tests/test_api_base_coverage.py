"""base 路由补充测试 — 覆盖 captcha/init/logout/qq/download/异常分支"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.utils.signed_url import generate_signed_url


@pytest.fixture(autouse=True)
def _clear_rate_limit(test_redis):
    """每个用例前清空 IP 限流窗口，避免相邻用例累计触发 429（直接操作内存适配器）"""
    test_redis._sorted_sets.pop("rate_limit:testclient", None)
    test_redis._data.pop("rate_limit:testclient", None)
    yield


class TestCaptchaAndInit:
    def test_captcha(self, client):
        body = client.get("/api/v1/base/captcha").json()
        assert body["code"] == 200
        assert body["data"]["captcha_key"]
        assert body["data"]["captcha_image"].startswith("data:image")

    def test_init_without_configs(self, client, db, security_policy, site_config, oauth_config):
        body = client.get("/api/v1/base/init").json()
        assert body["code"] == 200
        assert "site" in body["data"]
        assert "features" in body["data"]

    def test_init_no_site_config(self, client, db):
        # 无站点配置时走兜底默认值
        body = client.get("/api/v1/base/init").json()
        assert body["data"]["site"]["site_name"] == "ZgAdmin"


class TestLogout:
    def test_logout_with_refresh_token(self, client, admin_headers, admin_user, test_redis):
        resp = client.post(
            "/api/v1/base/logout",
            headers=admin_headers,
            json={"refreshToken": "some-refresh-token"},
        )
        assert resp.json()["code"] == 200

    def test_logout_without_body(self, client, admin_headers, admin_user):
        resp = client.post("/api/v1/base/logout", headers=admin_headers)
        assert resp.json()["code"] == 200


class TestUserInfoAndMenus:
    def test_userinfo(self, client, admin_headers, admin_user):
        body = client.get("/api/v1/base/userinfo", headers=admin_headers).json()
        assert body["code"] == 200

    def test_userinfo_missing_user(self, client, db, monkeypatch):
        from app.models.login import JWTPayload
        from app.utils.jwtt import create_access_token

        token = create_access_token(
            data=JWTPayload(
                user_id=str(uuid4()),
                username="ghost",
                is_superuser=False,
                exp=__import__("datetime").datetime.now(__import__("datetime").UTC)
                + __import__("datetime").timedelta(hours=1),
            )
        )
        resp = client.get("/api/v1/base/userinfo", headers={"Authorization": f"Bearer {token}"})
        body = resp.json()
        assert body["code"] == 401

    def test_user_menu_superuser(self, client, admin_headers, admin_user, db):
        from app.models import Menu

        db.add(Menu(title="顶级", name=f"Top{uuid4().hex[:6]}", path="/top", component="", rank=1))
        db.commit()
        body = client.get("/api/v1/base/userMenu", headers=admin_headers).json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)

    def test_user_api_superuser(self, client, admin_headers, admin_user, db):
        from app.models import Api

        db.add(Api(path="/api/v1/x", method="GET", tags="", summary=""))
        db.commit()
        body = client.get("/api/v1/base/userApi", headers=admin_headers).json()
        assert body["code"] == 200
        assert any(a.startswith("get/api/v1/x") for a in body["data"])

    def test_user_api_normal_role(self, client, db, normal_user, test_role):
        from app.core.redis import MemoryRedis  # noqa: F401
        from app.models import Api
        from app.models.login import JWTPayload
        from app.utils.jwtt import create_access_token

        api = Api(path="/api/v1/role-api", method="POST", tags="", summary="")
        db.add(api)
        db.commit()
        db.refresh(api)
        test_role.apis = [api]
        test_role.status = 1
        normal_user.roles = [test_role]
        db.add_all([test_role, normal_user])
        db.commit()

        from datetime import UTC, datetime, timedelta

        token = create_access_token(
            data=JWTPayload(
                user_id=str(normal_user.id),
                username="n",
                is_superuser=False,
                exp=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        body = client.get("/api/v1/base/userApi", headers={"Authorization": f"Bearer {token}"}).json()
        assert body["code"] == 200, body
        assert "post/api/v1/role-api" in body["data"]


class TestProfileAndPreferences:
    def test_update_profile_ok(self, client, admin_headers, admin_user, db):
        resp = client.post("/api/v1/base/updateProfile", headers=admin_headers, json={"nickname": "新昵称"})
        assert resp.json()["code"] == 200

    def test_update_profile_empty(self, client, admin_headers, admin_user):
        resp = client.post("/api/v1/base/updateProfile", headers=admin_headers, json={})
        body = resp.json()
        assert body["code"] != 200 or body.get("success") is False

    def test_preferences_default(self, client, admin_headers, admin_user):
        body = client.get("/api/v1/base/preferences", headers=admin_headers).json()
        assert body["code"] == 200
        assert body["data"]["notify_account"] is True

    def test_update_preferences(self, client, admin_headers, admin_user):
        body = client.post(
            "/api/v1/base/updatePreferences", headers=admin_headers, json={"notify_system": False}
        ).json()
        assert body["code"] == 200
        assert body["data"]["notify_system"] is False

    def test_login_logs(self, client, admin_headers, admin_user):
        body = client.get("/api/v1/base/loginLogs?pageSize=5&currentPage=1", headers=admin_headers).json()
        assert body["code"] == 200


class TestQqFlow:
    def test_auth_url_enabled(self, client, db, oauth_config, monkeypatch):
        oauth_config.qq_app_id = "appid123"
        oauth_config.qq_enabled = True
        db.add(oauth_config)
        db.commit()

        from app.settings import settings

        monkeypatch.setattr(settings, "FEATURE_QQ_LOGIN", True, raising=False)
        body = client.get("/api/v1/base/qq/auth-url").json()
        assert body["code"] == 200
        assert "graph.qq.com" in body["data"]["auth_url"]

    def test_auth_url_missing_appid(self, client, db, oauth_config, monkeypatch):
        oauth_config.qq_app_id = ""
        oauth_config.qq_enabled = True
        db.add(oauth_config)
        db.commit()

        from app.settings import settings

        monkeypatch.setattr(settings, "FEATURE_QQ_LOGIN", True, raising=False)
        monkeypatch.setattr(settings, "QQ_APP_ID", "", raising=False)
        body = client.get("/api/v1/base/qq/auth-url").json()
        assert body["code"] == 400
        assert "未配置" in body["msg"]

    def test_qq_login_success(self, client, db, security_policy):
        from app.models.login import QQUserInfo
        from app.utils.jwtt import create_oauth_state

        state = create_oauth_state()
        token_data = MagicMock()
        token_data.access_token = "AT"
        token_data.openid = "OID"

        user_info = QQUserInfo(openid="OIDX", nickname="qq", avatar="a.jpg")
        with (
            patch("app.api.v1.base.base.get_qq_access_token", AsyncMock(return_value=token_data)),
            patch("app.api.v1.base.base.get_qq_userinfo", AsyncMock(return_value=user_info)),
        ):
            body = client.post("/api/v1/base/qq/login", json={"code": "c", "state": state}).json()
        assert body["code"] == 200, body
        assert body["data"]["accessToken"]

    def test_qq_login_invalid_state(self, client, db):
        body = client.post("/api/v1/base/qq/login", json={"code": "c", "state": "bad"}).json()
        assert body["code"] == 401

    def test_qq_login_missing_params(self, client):
        body = client.post("/api/v1/base/qq/login", json={"code": "", "state": ""}).json()
        assert body["code"] == 401

    def test_qq_login_unexpected_error(self, client, db, security_policy):
        from app.utils.jwtt import create_oauth_state

        state = create_oauth_state()
        with patch("app.api.v1.base.base.get_qq_access_token", AsyncMock(side_effect=RuntimeError("boom"))):
            body = client.post("/api/v1/base/qq/login", json={"code": "c", "state": state}).json()
        assert body["code"] == 401

    def test_qq_login_http_exception_propagates(self, client, db, security_policy):
        from fastapi import HTTPException

        from app.utils.jwtt import create_oauth_state

        state = create_oauth_state()
        with patch(
            "app.api.v1.base.base.get_qq_access_token",
            AsyncMock(side_effect=HTTPException(status_code=400, detail="bad")),
        ):
            resp = client.post("/api/v1/base/qq/login", json={"code": "c", "state": state})
        assert resp.status_code == 400


class TestDownload:
    def _upload(self, client, admin_headers):
        return client.post(
            "/api/v1/resource/file/upload",
            headers=admin_headers,
            files={"file": ("dl.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        ).json()["data"]

    def test_download_invalid_sign(self, client, db):
        body = client.get(f"/api/v1/base/file/download/{uuid4()}?expires=9999999999&sign=bad").json()
        assert body["code"] == 400
        assert "签名无效" in body["msg"]

    def test_download_success(self, client, admin_headers, admin_user, db):
        data = self._upload(client, admin_headers)
        url = generate_signed_url(data["id"])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_download_missing_file(self, client, db, admin_user):
        fid = uuid4()
        url = generate_signed_url(fid)
        body = client.get(url).json()
        assert body["code"] == 400
        assert "文件不存在" in body["msg"]


class TestLoginCaptchaEnabled:
    def _enable_captcha(self, db, security_policy):
        security_policy.captcha_enabled = True
        db.add(security_policy)
        db.commit()

    def test_login_missing_captcha(self, client, db, admin_user, security_policy, test_redis):
        self._enable_captcha(db, security_policy)
        body = client.post("/api/v1/base/accessToken", json={"username": "admin", "password": "admin123456"}).json()
        assert body["code"] != 200
        assert "验证码" in body["msg"]

    def test_login_wrong_captcha(self, client, db, admin_user, security_policy, test_redis):
        self._enable_captcha(db, security_policy)
        body = client.post(
            "/api/v1/base/accessToken",
            json={
                "username": "admin",
                "password": "admin123456",
                "captcha_key": "k",
                "captcha_code": "zzzz",
            },
        ).json()
        assert "验证码" in body["msg"]

    def test_login_correct_captcha_then_dept_failure(self, client, db, admin_user, security_policy, test_redis):
        self._enable_captcha(db, security_policy)
        # 预置验证码
        import asyncio

        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
            test_redis.set("captcha:key1", "AB12", None)
        )
        with patch("app.api.v1.base.base.deptController.get_all_name", side_effect=RuntimeError("dept fail")):
            body = client.post(
                "/api/v1/base/accessToken",
                json={
                    "username": "admin",
                    "password": "admin123456",
                    "captcha_key": "key1",
                    "captcha_code": "AB12",
                },
            ).json()
        assert body["code"] == 200
        assert body["data"]["depart"] == ""


class TestAuthenticatedUserGone:
    """已通过鉴权但用户随后被删除 → FailAuth 分支"""

    def test_userinfo(self, client, admin_headers, admin_user):
        with patch("app.api.v1.base.base.userController.get", AsyncMock(return_value=None)):
            body = client.get("/api/v1/base/userinfo", headers=admin_headers).json()
        assert body["code"] == 401

    def test_update_pwd(self, client, admin_headers, admin_user):
        with patch("app.api.v1.base.base.userController.get", AsyncMock(return_value=None)):
            body = client.post(
                "/api/v1/base/updatePwd",
                headers=admin_headers,
                json={"current_password": "admin123456", "new_password": "NewAdmin123"},
            ).json()
        assert body["code"] == 401

    def test_update_profile(self, client, admin_headers, admin_user):
        with patch("app.api.v1.base.base.userController.get", AsyncMock(return_value=None)):
            body = client.post("/api/v1/base/updateProfile", headers=admin_headers, json={"nickname": "x"}).json()
        assert body["code"] == 401

    def test_preferences(self, client, admin_headers, admin_user):
        with patch("app.api.v1.base.base.userController.get", AsyncMock(return_value=None)):
            body = client.get("/api/v1/base/preferences", headers=admin_headers).json()
        assert body["code"] == 401

    def test_update_preferences(self, client, admin_headers, admin_user):
        with patch("app.api.v1.base.base.userController.get", AsyncMock(return_value=None)):
            body = client.post(
                "/api/v1/base/updatePreferences", headers=admin_headers, json={"notify_system": False}
            ).json()
        assert body["code"] == 401

    def test_login_logs(self, client, admin_headers, admin_user):
        with patch("app.api.v1.base.base.userController.get", AsyncMock(return_value=None)):
            body = client.get("/api/v1/base/loginLogs", headers=admin_headers).json()
        assert body["code"] == 401


class TestUpdatePwdNoPolicy:
    def test_update_pwd_without_policy(self, client, admin_headers, admin_user, db):
        # 无 SecurityPolicy → 跳过复杂度校验与历史校验
        from sqlmodel import select

        from app.models.security import SecurityPolicy

        for policy in db.exec(select(SecurityPolicy)).all():
            db.delete(policy)
        db.commit()
        body = client.post(
            "/api/v1/base/updatePwd",
            headers=admin_headers,
            json={"current_password": "admin123456", "new_password": "Whatever123"},
        ).json()
        assert body["code"] == 200


class TestBaseMoreBranches:
    def test_user_menu_missing_user(self, client, admin_headers, admin_user):
        with patch("app.api.v1.base.base.userController.get", AsyncMock(return_value=None)):
            body = client.get("/api/v1/base/userMenu", headers=admin_headers).json()
        assert body["code"] in (200, 401)

    def test_user_menu_user_row_gone(self, client, admin_headers, admin_user, db):
        """鉴权通过后 session 中查不到用户行 → FailAuth"""
        from sqlalchemy.sql import Select

        from app.models import Menu, Role, User

        real_exec = db.exec

        def fake_exec(stmt, *args, **kwargs):
            if (
                isinstance(stmt, Select)
                and stmt.column_descriptions
                and stmt.column_descriptions[0].get("entity") is User
            ):
                result = MagicMock()
                result.first.return_value = None
                result.all.return_value = []
                return result
            return real_exec(stmt, *args, **kwargs)

        with patch.object(db, "exec", side_effect=fake_exec):
            body = client.get("/api/v1/base/userMenu", headers=admin_headers).json()
        assert body["code"] == 401
        del Menu, Role

    def test_qq_login_dept_failure(self, client, db, security_policy):
        from app.models.login import QQUserInfo
        from app.utils.jwtt import create_oauth_state

        state = create_oauth_state()
        token_data = MagicMock()
        token_data.access_token = "AT"
        token_data.openid = "OIDD"
        user_info = QQUserInfo(openid="OIDD", nickname="q", avatar="a.jpg")
        with (
            patch("app.api.v1.base.base.get_qq_access_token", AsyncMock(return_value=token_data)),
            patch("app.api.v1.base.base.get_qq_userinfo", AsyncMock(return_value=user_info)),
            patch("app.api.v1.base.base.deptController.get_all_name", side_effect=RuntimeError("dept")),
        ):
            body = client.post("/api/v1/base/qq/login", json={"code": "c", "state": state}).json()
        assert body["code"] == 200
        assert body["data"]["depart"] == ""

    def test_download_signed_but_file_on_disk_missing(self, client, db, admin_user):
        from app.models.file import File
        from app.utils.signed_url import generate_signed_url

        f = File(
            name="ghost.png",
            path="uploads/nonexistent/ghost.png",
            size=1,
            file_type="image",
            mime_type="image/png",
            extension="png",
        )
        db.add(f)
        db.commit()
        db.refresh(f)
        url = generate_signed_url(f.id)
        body = client.get(url).json()
        assert body["code"] == 400
        assert "文件已丢失" in body["msg"]


class _GoneAfterAuth:
    """让 userController.get 第一次（鉴权）正常返回，之后返回 None"""

    def __init__(self, real_get):
        self.real_get = real_get
        self.calls = 0

    async def __call__(self, session, pk):
        self.calls += 1
        if self.calls == 1:
            return await self.real_get(session, pk)
        return None


class TestBaseFailAuthForAllEndpoints:
    """鉴权通过但用户行被删除 → 各端点 FailAuth"""

    def _patch_get(self):
        from app.controllers.user import userController as real_uc

        original = real_uc.get
        return patch.object(real_uc, "get", _GoneAfterAuth(original))

    def test_userinfo_row_gone(self, client, admin_headers, admin_user):
        with self._patch_get():
            body = client.get("/api/v1/base/userinfo", headers=admin_headers).json()
        assert body["code"] == 401

    def test_update_pwd_row_gone(self, client, admin_headers, admin_user):
        with self._patch_get():
            body = client.post(
                "/api/v1/base/updatePwd",
                headers=admin_headers,
                json={"current_password": "admin123456", "new_password": "NewAdmin123"},
            ).json()
        assert body["code"] == 401

    def test_profile_row_gone(self, client, admin_headers, admin_user):
        with self._patch_get():
            body = client.post("/api/v1/base/updateProfile", headers=admin_headers, json={"nickname": "x"}).json()
        assert body["code"] == 401

    def test_preferences_row_gone(self, client, admin_headers, admin_user):
        with self._patch_get():
            body = client.get("/api/v1/base/preferences", headers=admin_headers).json()
        assert body["code"] == 401

    def test_update_preferences_row_gone(self, client, admin_headers, admin_user):
        with self._patch_get():
            body = client.post(
                "/api/v1/base/updatePreferences", headers=admin_headers, json={"notify_system": False}
            ).json()
        assert body["code"] == 401

    def test_login_logs_row_gone(self, client, admin_headers, admin_user):
        with self._patch_get():
            body = client.get("/api/v1/base/loginLogs", headers=admin_headers).json()
        assert body["code"] == 401


class TestLoginWrongPasswordMessage:
    def test_wrong_password_returns_failauth(self, client, db, security_policy):
        """authenticate 返回 None → 路由返回 FailAuth(401)"""
        security_policy.captcha_enabled = False
        db.add(security_policy)
        db.commit()
        with patch("app.api.v1.base.base.userController.authenticate", AsyncMock(return_value=None)):
            body = client.post("/api/v1/base/accessToken", json={"username": "admin", "password": "x"}).json()
        assert body["code"] == 401


class TestUserMenuNormalUser:
    def test_non_superuser_role_menus_branch(self, client, db, normal_user, test_role):
        from datetime import UTC, datetime, timedelta

        from app.models import Menu
        from app.models.login import JWTPayload
        from app.utils.jwtt import create_access_token

        child = Menu(
            parentId=None,
            menuType=0,
            title="普通菜单",
            name=f"Norm{uuid4().hex[:6]}",
            path="/norm",
            component="",
            rank=1,
            showLink=True,
        )
        db.add(child)
        db.commit()
        db.refresh(child)
        test_role.menus = [child]
        test_role.status = 1
        normal_user.roles = [test_role]
        normal_user.status = 1
        db.add_all([test_role, normal_user])
        db.commit()

        token = create_access_token(
            data=JWTPayload(
                user_id=str(normal_user.id),
                username=normal_user.username,
                is_superuser=False,
                exp=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        body = client.get("/api/v1/base/userMenu", headers={"Authorization": f"Bearer {token}"}).json()
        assert body["code"] == 200
        assert any(m["title"] == "普通菜单" for m in body["data"])


class TestPasswordHistoryReuse:
    def test_reuse_recent_password(self, client, admin_headers, admin_user, db):
        from app.models.security import SecurityPolicy

        policy = db.exec(__import__("sqlmodel").select(SecurityPolicy)).first()
        if policy is None:
            policy = SecurityPolicy()
            db.add(policy)
        policy.password_history_count = 3
        policy.min_password_length = 8
        policy.require_uppercase = False
        policy.require_lowercase = False
        policy.require_digit = False
        policy.require_special = False
        db.add(policy)
        db.commit()

        # 首次修改，记录历史
        client.post(
            "/api/v1/base/updatePwd",
            headers=admin_headers,
            json={"current_password": "admin123456", "new_password": "historypass1"},
        )
        # 再改回旧密码 → 命中历史校验
        body = client.post(
            "/api/v1/base/updatePwd",
            headers=admin_headers,
            json={"current_password": "historypass1", "new_password": "admin123456"},
        ).json()
        assert "最近" in body.get("msg", "")


class TestLoginLogsWithData:
    def test_logs_to_dict_branch(self, client, admin_headers, admin_user, db):
        from datetime import UTC, datetime

        from app.models.logs import LoginLog

        db.add(
            LoginLog(
                username=admin_user.username,
                ip="1.1.1.1",
                address="x",
                system="s",
                browser="b",
                behavior="账号登录",
                level="success",
                time=datetime.now(UTC),
            )
        )
        db.commit()
        body = client.get("/api/v1/base/loginLogs", headers=admin_headers).json()
        assert body["code"] == 200
        assert body["total"] >= 1
        assert body["data"][0]["summary"] == "账号登录"


class TestUnlockLockedUserViaApi:
    def test_unlock_actually_locked(self, client, admin_headers, db, normal_user):
        from datetime import UTC, datetime, timedelta

        normal_user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
        normal_user.failed_login_count = 5
        db.add(normal_user)
        db.commit()
        body = client.post("/api/v1/system/user/unlock", headers=admin_headers, json={"id": str(normal_user.id)}).json()
        assert "解锁成功" in body["msg"]


class TestUserApiRowGone:
    def test_user_api_row_gone(self, client, admin_headers, admin_user, db):
        """鉴权后 session.exec 查不到用户行 → FailAuth"""
        from sqlalchemy.sql import Select

        from app.models import User

        real_exec = db.exec

        def fake_exec(stmt, *a, **k):
            if (
                isinstance(stmt, Select)
                and stmt.column_descriptions
                and stmt.column_descriptions[0].get("entity") is User
            ):
                r = MagicMock()
                r.first.return_value = None
                r.all.return_value = []
                return r
            return real_exec(stmt, *a, **k)

        with patch.object(db, "exec", side_effect=fake_exec):
            body = client.get("/api/v1/base/userApi", headers=admin_headers).json()
        assert body["code"] == 401


class TestDownloadWithoutSession:
    def test_download_db_unavailable(self, client, db, admin_user):
        """get_db 返回 None → 数据库连接失败分支"""
        from uuid import uuid4 as _uuid4

        from app.core.dependency import get_db
        from app.utils.signed_url import generate_signed_url

        def _none_db():
            yield None

        # 通过覆盖依赖注入，让 session 为 None（无需真实 DB）
        from tests.conftest import create_test_app

        application = create_test_app()
        application.dependency_overrides[get_db] = _none_db
        from fastapi.testclient import TestClient

        with TestClient(application) as c:
            url = generate_signed_url(_uuid4())
            body = c.get(url).json()
        assert body["code"] == 400
        assert "数据库连接失败" in body["msg"]
