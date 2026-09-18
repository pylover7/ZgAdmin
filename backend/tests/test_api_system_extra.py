"""API 路由补充测试 — system/api、menu、version、depart"""


class TestApiRouter:
    def test_list_and_all(self, client, admin_headers, db):
        for path in ("/api/v1/system/api/list", "/api/v1/system/api/all"):
            resp = client.get(path, headers=admin_headers)
            body = resp.json()
            assert body["code"] == 200
            assert isinstance(body["data"], list)

    def test_delete(self, client, admin_headers, db):
        from app.models import Api

        api = Api(path="/tmp/x", method="GET", tags="", summary="")
        db.add(api)
        db.commit()
        db.refresh(api)

        resp = client.post("/api/v1/system/api/delete", headers=admin_headers, json=[str(api.id)])
        assert resp.json()["code"] == 200


class TestMenuRouter:
    def _payload(self, **overrides):
        payload = {
            "parentId": None,
            "menuType": 0,
            "title": "测试菜单",
            "name": "TestMenuX",
            "path": "/test-menu-x",
            "component": "test/index",
            "redirect": "",
            "icon": "ep:menu",
            "extraIcon": "",
            "transitionName": "",
            "enterTransition": "",
            "leaveTransition": "",
            "activePath": "",
            "auths": "",
            "frameSrc": "",
        }
        payload.update(overrides)
        return payload

    def test_add_list_update_delete(self, client, admin_headers, db):
        add = client.post("/api/v1/system/menu/add", headers=admin_headers, json=self._payload())
        body = add.json()
        assert body["code"] == 200
        menu_id = body["data"]["id"]

        listing = client.get("/api/v1/system/menu/list", headers=admin_headers).json()
        assert listing["code"] == 200
        assert any(m["id"] == menu_id for m in listing["data"])

        upd = client.post(
            "/api/v1/system/menu/update",
            headers=admin_headers,
            json=self._payload(id=menu_id, title="改名后"),
        )
        assert upd.json()["code"] == 200

        dele = client.post("/api/v1/system/menu/delete", headers=admin_headers, json=[menu_id])
        assert dele.json()["code"] == 200


class TestDepartRouter:
    def test_add_list_update_delete(self, client, admin_headers, db):
        add = client.post(
            "/api/v1/system/dept/add",
            headers=admin_headers,
            json={
                "name": "研发部X",
                "parentId": None,
                "sort": 0,
                "phone": "",
                "principal": "",
                "email": "",
                "remark": "",
            },
        )
        body = add.json()
        assert body["code"] == 200
        dept_id = body["data"]["id"]

        listing = client.get("/api/v1/system/dept/list", headers=admin_headers).json()
        assert listing["code"] == 200

        upd = client.post(
            "/api/v1/system/dept/update",
            headers=admin_headers,
            json={"id": dept_id, "name": "研发部Y", "parentId": None},
        )
        assert upd.json()["code"] == 200

        dele = client.post("/api/v1/system/dept/delete", headers=admin_headers, json=[dept_id])
        assert dele.json()["code"] == 200

    def test_update_parent_self_rejected(self, client, admin_headers, db):
        from uuid import uuid4

        fake_id = str(uuid4())
        resp = client.post(
            "/api/v1/system/dept/update",
            headers=admin_headers,
            json={"id": fake_id, "name": "X", "parentId": fake_id},
        )
        body = resp.json()
        assert body.get("success") is False
        assert "不能选择自己" in body["msg"]

    def test_add_duplicate_name(self, client, admin_headers, db):
        payload = {
            "name": "重复部",
            "parentId": None,
            "sort": 0,
            "phone": "",
            "principal": "",
            "email": "",
            "remark": "",
        }
        assert client.post("/api/v1/system/dept/add", headers=admin_headers, json=payload).json()["code"] == 200
        dup = client.post("/api/v1/system/dept/add", headers=admin_headers, json=payload).json()
        assert dup.get("success") is False


class TestVersionRouter:
    def test_get_version_info(self, client, admin_headers):
        resp = client.get("/api/v1/system/version", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert "python_version" in body["data"]
        assert "uv_version" in body["data"]

    def test_get_uv_version_failure(self, monkeypatch):
        from unittest.mock import patch

        from app.api.v1.system import version as version_mod

        with patch("app.api.v1.system.version.subprocess.run", side_effect=OSError("no uv")):
            assert version_mod._get_uv_version() == "unknown"

    def test_get_uv_version_success(self):
        from app.api.v1.system.version import _get_uv_version

        assert isinstance(_get_uv_version(), str)

    def test_check_update(self, client, admin_headers, monkeypatch):
        from unittest.mock import AsyncMock, patch

        with patch(
            "app.api.v1.system.version.check_for_update",
            AsyncMock(return_value={"current_version": "v1", "latest_version": "v1", "has_update": False}),
        ):
            resp = client.get("/api/v1/system/version/check-update", headers=admin_headers)
        assert resp.json()["code"] == 200
