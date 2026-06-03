"""API 集成测试 — monitor 路由（日志管理 + 系统监控）"""
from unittest.mock import MagicMock, patch

from app.models import LoginLog, OperationLog, SystemLog

# ═══════════════════════════════════════════════════════════════════════
# 登录日志
# ═══════════════════════════════════════════════════════════════════════

class TestLoginLogAPI:
    def _create_login_log(self, db, username="testuser", level="INFO"):
        log = LoginLog(
            username=username,
            ip="127.0.0.1",
            address="内网IP",
            system="Windows",
            browser="Chrome",
            behavior="登录成功",
            level=level,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def test_list_login_logs(self, client, admin_headers, db):
        self._create_login_log(db)
        resp = client.post("/api/v1/monitor/logs/login/list", headers=admin_headers, json={
            "username": None, "level": None, "loginTime": None,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1

    def test_list_login_logs_with_filter(self, client, admin_headers, db):
        self._create_login_log(db, username="filteruser")
        resp = client.post("/api/v1/monitor/logs/login/list", headers=admin_headers, json={
            "username": "filteruser", "level": None, "loginTime": None,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1

    def test_list_login_logs_with_level_filter(self, client, admin_headers, db):
        self._create_login_log(db, level="ERROR")
        resp = client.post("/api/v1/monitor/logs/login/list", headers=admin_headers, json={
            "username": None, "level": "ERROR", "loginTime": None,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_delete_login_logs(self, client, admin_headers, db):
        log = self._create_login_log(db)
        resp = client.post("/api/v1/monitor/logs/login/delete", headers=admin_headers, json=[str(log.id)])
        body = resp.json()
        assert body["code"] == 200

    def test_clear_login_logs(self, client, admin_headers, db, admin_user):
        self._create_login_log(db)
        resp = client.get("/api/v1/monitor/logs/login/clear", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200

    def test_list_login_logs_pagination(self, client, admin_headers, db):
        for i in range(5):
            self._create_login_log(db, username=f"paguser{i}")
        resp = client.post(
            "/api/v1/monitor/logs/login/list?currentPage=1&pageSize=2",
            headers=admin_headers,
            json={"username": None, "level": None, "loginTime": None},
        )
        body = resp.json()
        assert body["code"] == 200
        assert body["pageSize"] == 2
        assert len(body["data"]) <= 2


# ═══════════════════════════════════════════════════════════════════════
# 操作日志
# ═══════════════════════════════════════════════════════════════════════

class TestOperationLogAPI:
    def _create_operation_log(self, db, level="INFO", message="测试操作"):
        log = OperationLog(
            username="admin",
            level=level,
            message=message,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def test_list_operation_logs(self, client, admin_headers, db):
        self._create_operation_log(db)
        resp = client.post("/api/v1/monitor/logs/operation/list", headers=admin_headers, json={
            "level": [], "operationTime": None,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1

    def test_list_operation_logs_with_level_filter(self, client, admin_headers, db):
        self._create_operation_log(db, level="WARNING")
        resp = client.post("/api/v1/monitor/logs/operation/list", headers=admin_headers, json={
            "level": ["WARNING"], "operationTime": None,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_delete_operation_logs(self, client, admin_headers, db):
        log = self._create_operation_log(db)
        resp = client.post("/api/v1/monitor/logs/operation/delete", headers=admin_headers, json=[str(log.id)])
        body = resp.json()
        assert body["code"] == 200

    def test_clear_operation_logs(self, client, admin_headers, db):
        self._create_operation_log(db)
        resp = client.get("/api/v1/monitor/logs/operation/clear", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 系统日志
# ═══════════════════════════════════════════════════════════════════════

class TestSystemLogAPI:
    def _create_system_log(self, db, module="系统", message="测试日志"):
        log = SystemLog(
            module=module,
            level="INFO",
            message=message,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def test_list_system_logs(self, client, admin_headers, db):
        self._create_system_log(db)
        resp = client.post("/api/v1/monitor/logs/system/list", headers=admin_headers, json={
            "module": None, "operationTime": None,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1

    def test_list_system_logs_with_module_filter(self, client, admin_headers, db):
        self._create_system_log(db, module="测试模块")
        resp = client.post("/api/v1/monitor/logs/system/list", headers=admin_headers, json={
            "module": "测试模块", "operationTime": None,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_delete_system_logs(self, client, admin_headers, db):
        log = self._create_system_log(db)
        resp = client.post("/api/v1/monitor/logs/system/delete", headers=admin_headers, json=[str(log.id)])
        body = resp.json()
        assert body["code"] == 200

    def test_clear_system_logs(self, client, admin_headers, db):
        self._create_system_log(db)
        resp = client.get("/api/v1/monitor/logs/system/clear", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 系统监控
# ═══════════════════════════════════════════════════════════════════════

class TestSystemMonitorAPI:
    def test_system_status(self, client, admin_headers, db):
        """系统状态 — 需要 mock psutil"""
        mock_cpu = MagicMock(return_value=45.0)
        with patch("app.api.v1.monitor.system.psutil.cpu_percent", mock_cpu), \
             patch("app.api.v1.monitor.system.get_load_info") as mock_load, \
             patch("app.api.v1.monitor.system.get_cpu_info") as mock_cpu_info, \
             patch("app.api.v1.monitor.system.get_memory_info") as mock_mem, \
             patch("app.api.v1.monitor.system.get_disk_info") as mock_disk, \
             patch("app.api.v1.monitor.system.get_top_processes") as mock_top:
            mock_load.return_value = MagicMock(
                load1=1.0, load5=1.5, load15=2.0,
                status="正常", cores=4, percent=45.0,
            )
            mock_cpu_info.return_value = MagicMock(
                percent=45.0, freq=2400, per_cpu=[40, 50],
                physical_cores=2, logical_cores=4,
            )
            mock_mem.return_value = MagicMock(
                percent=60.0, total=16384, used=9830,
                available=6554, cached=2000, buffers=500, shared=100,
            )
            mock_disk.return_value = MagicMock(
                percent=70.0, total=512000, used=358400, free=153600,
            )
            mock_top.return_value = []
            resp = client.get("/api/v1/monitor/system/status", headers=admin_headers)
            body = resp.json()
            assert body["code"] == 200
            assert "load" in body["data"]
            assert "cpu" in body["data"]
            assert "memory" in body["data"]
            assert "disk" in body["data"]

    def test_network_monitor(self, client, admin_headers, db):
        with patch("app.api.v1.monitor.system.get_network_io") as mock_net:
            mock_net.return_value = {
                "eth0": {"bytes_sent": 1000, "bytes_recv": 5000},
            }
            resp = client.get("/api/v1/monitor/system/network", headers=admin_headers)
            body = resp.json()
            assert body["code"] == 200

    def test_network_monitor_with_iface(self, client, admin_headers, db):
        with patch("app.api.v1.monitor.system.get_network_io") as mock_net:
            mock_net.return_value = {
                "eth0": {"bytes_sent": 1000, "bytes_recv": 5000},
                "lo": {"bytes_sent": 100, "bytes_recv": 100},
            }
            resp = client.get("/api/v1/monitor/system/network?iface=eth0", headers=admin_headers)
            body = resp.json()
            assert body["code"] == 200

    def test_disk_io_monitor(self, client, admin_headers, db):
        with patch("app.api.v1.monitor.system.get_disk_io") as mock_disk_io:
            mock_disk_io.return_value = {
                "sda": {"read_bytes": 10000, "write_bytes": 5000},
            }
            resp = client.get("/api/v1/monitor/system/disk-io", headers=admin_headers)
            body = resp.json()
            assert body["code"] == 200
