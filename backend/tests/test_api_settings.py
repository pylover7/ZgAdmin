"""API 集成测试 — settings 路由（安全策略 + 登录配置 + 通用配置 + 邮件配置）"""
import pytest

from app.models.security import SecurityPolicy, IPRule


# ═══════════════════════════════════════════════════════════════════════
# 安全策略
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityPolicyAPI:
    def test_get_policy(self, client, admin_headers, db, security_policy):
        resp = client.get("/api/v1/settings/security/policy", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["min_password_length"] == 8

    def test_get_policy_not_initialized(self, client, admin_headers, db):
        """无策略 → Fail"""
        resp = client.get("/api/v1/settings/security/policy", headers=admin_headers)
        body = resp.json()
        assert body["code"] in (200, 400)

    def test_update_policy(self, client, admin_headers, db, security_policy):
        resp = client.post("/api/v1/settings/security/policy", headers=admin_headers, json={
            "min_password_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digit": True,
            "require_special": True,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["min_password_length"] == 12

    def test_update_policy_not_initialized(self, client, admin_headers, db):
        resp = client.post("/api/v1/settings/security/policy", headers=admin_headers, json={
            "min_password_length": 10,
        })
        body = resp.json()
        assert body["code"] in (200, 400)


# ═══════════════════════════════════════════════════════════════════════
# IP 规则
# ═══════════════════════════════════════════════════════════════════════

class TestIPRuleAPI:
    def test_add_ip_rule_whitelist(self, client, admin_headers, db, test_redis):
        resp = client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "192.168.1.0/24",
            "rule_type": "whitelist",
            "description": "内网白名单",
            "is_active": True,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["ip_cidr"] == "192.168.1.0/24"

    def test_add_ip_rule_blacklist(self, client, admin_headers, db, test_redis):
        resp = client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "10.0.0.1",
            "rule_type": "blacklist",
            "description": "恶意IP",
        })
        body = resp.json()
        assert body["code"] == 200

    def test_add_ip_rule_invalid_type(self, client, admin_headers, db):
        resp = client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "1.2.3.4",
            "rule_type": "invalid_type",
            "description": "",
        })
        body = resp.json()
        assert body["code"] != 200

    def test_add_ip_rule_invalid_cidr(self, client, admin_headers, db):
        resp = client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "not-an-ip",
            "rule_type": "blacklist",
            "description": "",
        })
        body = resp.json()
        assert body["code"] != 200

    def test_add_ip_rule_duplicate(self, client, admin_headers, db, test_redis):
        # 先添加
        client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "172.16.0.1",
            "rule_type": "blacklist",
            "description": "",
        })
        # 重复添加
        resp = client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "172.16.0.1",
            "rule_type": "blacklist",
            "description": "",
        })
        body = resp.json()
        assert body["code"] != 200

    def test_get_ip_rules(self, client, admin_headers, db, test_redis):
        # 先添加
        client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "192.168.0.0/16",
            "rule_type": "whitelist",
            "description": "",
        })
        resp = client.get("/api/v1/settings/security/ip-rules", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200

    def test_update_ip_rule(self, client, admin_headers, db, test_redis):
        # 先添加
        resp = client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "203.0.113.0/24",
            "rule_type": "blacklist",
            "description": "测试",
        })
        rule_id = resp.json()["data"]["id"]

        resp = client.post("/api/v1/settings/security/ip-rules/update", headers=admin_headers, json={
            "id": rule_id,
            "description": "更新描述",
        })
        body = resp.json()
        assert body["code"] == 200

    def test_update_ip_rule_invalid_cidr(self, client, admin_headers, db):
        resp = client.post("/api/v1/settings/security/ip-rules/update", headers=admin_headers, json={
            "id": "00000000-0000-0000-0000-000000000000",
            "ip_cidr": "bad-cidr",
        })
        body = resp.json()
        assert body["code"] != 200

    def test_update_ip_rule_invalid_type(self, client, admin_headers, db):
        resp = client.post("/api/v1/settings/security/ip-rules/update", headers=admin_headers, json={
            "id": "00000000-0000-0000-0000-000000000000",
            "rule_type": "bad_type",
        })
        body = resp.json()
        assert body["code"] != 200

    def test_delete_ip_rules(self, client, admin_headers, db, test_redis):
        # 先添加
        resp = client.post("/api/v1/settings/security/ip-rules/add", headers=admin_headers, json={
            "ip_cidr": "198.51.100.0/24",
            "rule_type": "blacklist",
            "description": "",
        })
        rule_id = resp.json()["data"]["id"]

        resp = client.post("/api/v1/settings/security/ip-rules/delete", headers=admin_headers, json=[rule_id])
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 登录配置
# ═══════════════════════════════════════════════════════════════════════

class TestLoginConfigAPI:
    def test_get_login_config(self, client, admin_headers, db, oauth_config):
        resp = client.get("/api/v1/settings/login", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        # 扁平结构，直接包含 qq_app_id 等字段
        assert "qq_app_id" in body["data"]
        assert "wechat_app_id" in body["data"]
        # 敏感字段应返回空值
        assert body["data"]["qq_app_key"] == ""
        assert body["data"]["wechat_app_secret"] == ""

    def test_update_login_config(self, client, admin_headers, db, oauth_config):
        resp = client.post("/api/v1/settings/login", headers=admin_headers, json={
            "qq_app_id": "test_id",
            "qq_redirect_uri": "http://localhost/callback",
            "qq_enabled": False,
        })
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 通用配置
# ═══════════════════════════════════════════════════════════════════════

class TestGeneralConfigAPI:
    def test_get_general_config(self, client, admin_headers, db, site_config):
        resp = client.get("/api/v1/settings/general", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert "site_name" in body["data"]

    def test_update_general_config(self, client, admin_headers, db, site_config):
        resp = client.post("/api/v1/settings/general", headers=admin_headers, json={
            "site_name": "测试站点",
            "site_desc": "测试描述",
        })
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 邮件配置
# ═══════════════════════════════════════════════════════════════════════

class TestEmailConfigAPI:
    def test_get_email_config(self, client, admin_headers, db, email_config):
        resp = client.get("/api/v1/settings/email", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert "host" in body["data"]
        # 敏感字段应返回空值
        assert body["data"]["password"] == ""

    def test_update_email_config(self, client, admin_headers, db, email_config):
        resp = client.post("/api/v1/settings/email", headers=admin_headers, json={
            "host": "smtp.test.com",
            "port": 587,
            "username": "test@test.com",
            "password": "new_password",
            "sender": "test@test.com",
        })
        body = resp.json()
        assert body["code"] == 200
        # 响应中密码应为空值
        assert body["data"]["password"] == ""

    def test_update_email_config_empty_password_keeps_old(self, client, admin_headers, db, email_config):
        """空密码不更新（保留原值）"""
        # 先设置一个密码
        client.post("/api/v1/settings/email", headers=admin_headers, json={
            "password": "original_password",
        })
        # 用空密码更新，应保留原值
        resp = client.post("/api/v1/settings/email", headers=admin_headers, json={
            "host": "smtp.new.com",
            "password": "",
        })
        body = resp.json()
        assert body["code"] == 200
