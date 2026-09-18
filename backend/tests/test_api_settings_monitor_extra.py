"""settings 与 monitor 路由补充测试 — 未初始化分支、过滤条件、速率追踪"""

from unittest.mock import patch


class TestSettingsNotInitialized:
    def test_email_get_not_initialized(self, client, admin_headers, db):
        body = client.get("/api/v1/settings/email", headers=admin_headers).json()
        assert body["code"] in (200, 400)
        assert body.get("data") is None

    def test_email_update_not_initialized(self, client, admin_headers, db):
        body = client.post("/api/v1/settings/email", headers=admin_headers, json={"host": "smtp.x.com"}).json()
        assert body["code"] in (200, 400)

    def test_general_get_not_initialized(self, client, admin_headers, db):
        body = client.get("/api/v1/settings/general", headers=admin_headers).json()
        assert body["code"] in (200, 400)

    def test_general_update_not_initialized(self, client, admin_headers, db):
        body = client.post("/api/v1/settings/general", headers=admin_headers, json={"site_name": "X"}).json()
        assert body["code"] in (200, 400)

    def test_login_get_not_initialized(self, client, admin_headers, db):
        body = client.get("/api/v1/settings/login", headers=admin_headers).json()
        assert body["code"] in (200, 400)

    def test_login_update_not_initialized(self, client, admin_headers, db):
        body = client.post("/api/v1/settings/login", headers=admin_headers, json={"qq_app_id": "x"}).json()
        assert body["code"] in (200, 400)


class TestSecurityIpRulesExtra:
    def test_update_nonexistent_rule(self, client, admin_headers, db):
        from uuid import uuid4

        body = client.post(
            "/api/v1/settings/security/ip-rules/update",
            headers=admin_headers,
            json={"id": str(uuid4()), "ip_cidr": "1.2.3.4"},
        ).json()
        assert "不存在" in body["msg"]

    def test_get_ip_rules_order(self, client, admin_headers, db, test_redis):
        client.post(
            "/api/v1/settings/security/ip-rules/add",
            headers=admin_headers,
            json={"ip_cidr": "9.9.0.0/16", "rule_type": "whitelist"},
        )
        body = client.get("/api/v1/settings/security/ip-rules", headers=admin_headers).json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)


class TestMonitorLogsFilters:
    def _seed_log(self, db):
        from datetime import UTC, datetime

        from app.models.logs import LoginLog

        db.add(
            LoginLog(
                username="loguser",
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

    def test_login_logs_with_filters(self, client, admin_headers, db, admin_user):
        self._seed_log(db)
        body = client.post(
            "/api/v1/monitor/logs/login/list?currentPage=1&pageSize=10",
            headers=admin_headers,
            json={"username": "loguser", "level": "success"},
        ).json()
        assert body["code"] == 200

    def test_login_logs_with_time_range(self, client, admin_headers, db, admin_user):
        self._seed_log(db)
        body = client.post(
            "/api/v1/monitor/logs/login/list",
            headers=admin_headers,
            json={"loginTime": ["2000-01-01 00:00:00", "2999-12-31 23:59:59"]},
        ).json()
        assert body["code"] == 200

    def test_operation_logs(self, client, admin_headers, db):
        from app.models.logs import OperationLog

        db.add(OperationLog(username="u", message="m", level="info"))
        db.commit()
        body = client.post("/api/v1/monitor/logs/operation/list", headers=admin_headers, json={}).json()
        assert body["code"] == 200

    def test_system_logs(self, client, admin_headers, db):
        from app.models.logs import SystemLog

        db.add(SystemLog(module="m", message="m", level="info"))
        db.commit()
        body = client.post("/api/v1/monitor/logs/system/list", headers=admin_headers, json={}).json()
        assert body["code"] == 200


class TestRateTracker:
    def test_first_sample_no_rates(self):
        from app.api.v1.monitor.system import _RateTracker

        tracker = _RateTracker()
        result = tracker.compute({"eth0": {"bytes_sent": 100}}, {"bytes_sent": "sent"})
        assert result["eth0"]["bytes_sent"] == 100
        # 首次采样无速率字段
        assert "sent_speed_raw" not in result["eth0"]

    def test_second_sample_computes_rate(self):
        from app.api.v1.monitor.system import _RateTracker

        tracker = _RateTracker()
        tracker.compute({"eth0": {"bytes_sent": 100}}, {"bytes_sent": "sent"})
        tracker._prev_time = tracker._prev_time  # 保留真实时间
        with patch("app.api.v1.monitor.system.time.time", return_value=tracker._prev_time + 1.0):
            result = tracker.compute({"eth0": {"bytes_sent": 300}}, {"bytes_sent": "sent"})
        assert result["eth0"]["sent_speed_raw"] == 200.0
        assert "sent_speed" in result["eth0"]

    def test_history_window_trim(self):
        from app.api.v1.monitor.system import _RateTracker

        tracker = _RateTracker(history_window_ms=1)
        tracker._prev_time = 100.0
        with patch("app.api.v1.monitor.system.time.time", return_value=100.0):
            tracker.compute({"eth0": {"bytes_sent": 1}}, {"bytes_sent": "sent"})
        with patch("app.api.v1.monitor.system.time.time", return_value=200.0):
            result = tracker.compute({"eth0": {"bytes_sent": 2}}, {"bytes_sent": "sent"})
        # 旧数据被裁剪，仅保留最新一个点
        assert len(result["eth0"]["history"]) == 1


class TestMonitorSystemEndpoint:
    def test_system_status(self, client, admin_headers):
        body = client.get("/api/v1/monitor/system/status", headers=admin_headers).json()
        assert body["code"] == 200

    def test_system_network_and_disk_io(self, client, admin_headers):
        for path in ("/api/v1/monitor/system/network", "/api/v1/monitor/system/disk-io"):
            assert client.get(path, headers=admin_headers).json()["code"] == 200
