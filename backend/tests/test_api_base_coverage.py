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
