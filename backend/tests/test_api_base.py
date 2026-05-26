"""API 集成测试 — base 路由（核心路径 100%）"""
import pytest
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from app.models import User, SecurityPolicy
from app.models.login import JWTPayload
from app.utils.password import get_password_hash
from app.utils.jwtt import create_access_token
from app.utils.captcha import CAPTCHA_KEY_PREFIX


def _get_captcha_code_sync(test_redis, captcha_key: str) -> str | None:
    """同步获取 Redis 中的验证码"""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    async def _fetch():
        return await test_redis.get(f"{CAPTCHA_KEY_PREFIX}{captcha_key}")

    if loop and loop.is_running():
        # 已在异步上下文中 — 用线程执行
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, _fetch())
            return future.result()
    else:
        return asyncio.run(_fetch())


# ═══════════════════════════════════════════════════════════════════════
# 公开接口
# ═══════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/v1/base/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestCaptcha:
    def test_get_captcha(self, client):
        resp = client.get("/api/v1/base/captcha")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "captcha_key" in data
        assert "captcha_image" in data
        assert data["captcha_image"].startswith("data:image/png;base64,")


class TestInitConfig:
    def test_get_init_config(self, client, security_policy):
        resp = client.get("/api/v1/base/init")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "site" in data
        assert "features" in data
        assert "security" in data


# ═══════════════════════════════════════════════════════════════════════
# 登录流程（核心路径！）
# ═══════════════════════════════════════════════════════════════════════

class TestLogin:
    def test_login_success(self, client, db, admin_user, test_redis, security_policy):
        """完整登录流程：获取验证码 → 登录 → 返回 Token"""
        # 1. 获取验证码
        captcha_resp = client.get("/api/v1/base/captcha")
        captcha_key = captcha_resp.json()["data"]["captcha_key"]

        # 2. 从 Redis 取出验证码
        code = _get_captcha_code_sync(test_redis, captcha_key)
        assert code is not None, "验证码未存入 Redis，检查 get_redis 全局替换是否生效"

        # 3. 登录
        resp = client.post("/api/v1/base/accessToken", json={
            "username": "admin",
            "password": "admin123456",
            "captcha_key": captcha_key,
            "captcha_code": code,
        })
        body = resp.json()
        assert body["code"] == 200
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]

    def test_login_wrong_password(self, client, db, admin_user, test_redis, security_policy):
        """密码错误 → 401"""
        captcha_resp = client.get("/api/v1/base/captcha")
        captcha_key = captcha_resp.json()["data"]["captcha_key"]
        code = _get_captcha_code_sync(test_redis, captcha_key)

        resp = client.post("/api/v1/base/accessToken", json={
            "username": "admin",
            "password": "wrongpassword",
            "captcha_key": captcha_key,
            "captcha_code": code,
        })
        body = resp.json()
        assert body["code"] in (400, 401)

    def test_login_wrong_captcha(self, client, db, admin_user, test_redis, security_policy):
        """验证码错误 → 失败"""
        resp = client.post("/api/v1/base/accessToken", json={
            "username": "admin",
            "password": "admin123456",
            "captcha_key": "fake-key",
            "captcha_code": "XXXX",
        })
        body = resp.json()
        assert body["code"] != 200

    def test_login_captcha_disabled(self, client, db, admin_user, test_redis):
        """验证码关闭时无需验证码"""
        policy = SecurityPolicy(captcha_enabled=False)
        db.add(policy)
        db.commit()

        resp = client.post("/api/v1/base/accessToken", json={
            "username": "admin",
            "password": "admin123456",
        })
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# Token 刷新
# ═══════════════════════════════════════════════════════════════════════

class TestRefreshToken:
    def test_refresh_token_success(self, client, admin_user):
        """有效 refreshToken → 返回新 Token"""
        refresh_payload = JWTPayload(
            user_id=str(admin_user.id),
            username=admin_user.username,
            is_superuser=True,
            exp=datetime.now(timezone.utc) + timedelta(days=1),
        )
        refresh_token = create_access_token(data=refresh_payload)

        resp = client.post("/api/v1/base/refreshToken", json={
            "refreshToken": refresh_token,
        })
        body = resp.json()
        assert body["code"] == 200
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]

    def test_refresh_token_expired(self, client, admin_user):
        """过期 refreshToken → 401"""
        expired_payload = JWTPayload(
            user_id=str(admin_user.id),
            username=admin_user.username,
            is_superuser=True,
            exp=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        expired_token = create_access_token(data=expired_payload)

        resp = client.post("/api/v1/base/refreshToken", json={
            "refreshToken": expired_token,
        })
        body = resp.json()
        assert body["code"] == 401


# ═══════════════════════════════════════════════════════════════════════
# 用户信息 / 菜单 / API
# ═══════════════════════════════════════════════════════════════════════

class TestUserInfo:
    def test_get_userinfo(self, client, admin_headers, admin_user):
        """获取用户信息"""
        resp = client.get("/api/v1/base/userinfo", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["username"] == "admin"
        assert "password" not in body["data"]

    def test_get_userinfo_no_auth(self, client, admin_user):
        """未认证 → 401/403/422"""
        resp = client.get("/api/v1/base/userinfo")
        # FastAPI 对缺少 required header 返回 422，认证失败返回 401/403
        assert resp.status_code in (401, 403, 422)


# ═══════════════════════════════════════════════════════════════════════
# 修改密码
# ═══════════════════════════════════════════════════════════════════════

class TestUpdatePassword:
    def test_update_password_success(self, client, admin_headers, admin_user, db, security_policy):
        """修改密码成功"""
        resp = client.post("/api/v1/base/updatePwd", headers=admin_headers, json={
            "current_password": "admin123456",
            "new_password": "NewAdmin123",
        })
        body = resp.json()
        assert body["code"] == 200

    def test_update_password_wrong_current(self, client, admin_headers, admin_user, db, security_policy):
        """旧密码错误 → 失败"""
        resp = client.post("/api/v1/base/updatePwd", headers=admin_headers, json={
            "current_password": "wrongpassword",
            "new_password": "NewAdmin123",
        })
        body = resp.json()
        assert body["code"] != 200
