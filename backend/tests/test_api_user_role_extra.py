"""API 路由补充测试 — system/user 与 system/role 边界分支"""

from uuid import uuid4


class TestUserRouterExtra:
    def test_add_reserved_admin_raises(self, client, admin_headers, db, security_policy):
        resp = client.post(
            "/api/v1/system/user/add",
            headers=admin_headers,
            json={
                "username": "admin",
                "nickname": "x",
                "email": "admin2@test.com",
                "password": "Passw0rd123",
                "phone": "13700137010",
                "remark": "",
                "status": 1,
                "is_superuser": False,
            },
        )
        assert resp.status_code == 400

    def test_get_roles_ids_missing_user(self, client, admin_headers, db):
        resp = client.post("/api/v1/system/user/getRolesIds", headers=admin_headers, json={"id": str(uuid4())})
        assert resp.json()["msg"] == "没有这个用户"

    def test_get_roles_ids_ok(self, client, admin_headers, db, normal_user, test_role):
        db.add(normal_user)
        normal_user.roles = [test_role]
        db.add(normal_user)
        db.commit()
        resp = client.post("/api/v1/system/user/getRolesIds", headers=admin_headers, json={"id": str(normal_user.id)})
        body = resp.json()
        assert body["code"] == 200
        assert str(test_role.id) in body["data"]

    def test_update_user_not_found(self, client, admin_headers, db):
        resp = client.post(
            "/api/v1/system/user/update",
            headers=admin_headers,
            json={"id": str(uuid4()), "username": "ghost", "email": "g@test.com"},
        )
        assert resp.status_code == 404

    def test_update_user_name_conflict(self, client, admin_headers, db, admin_user, normal_user):
        resp = client.post(
            "/api/v1/system/user/update",
            headers=admin_headers,
            json={"id": str(normal_user.id), "username": admin_user.username, "email": "n@test.com"},
        )
        assert resp.status_code == 400

    def test_update_user_ok_and_list_filter(self, client, admin_headers, db, normal_user, test_department):
        resp = client.post(
            "/api/v1/system/user/update",
            headers=admin_headers,
            json={"id": str(normal_user.id), "username": normal_user.username, "email": "changed@test.com"},
        )
        assert resp.json()["code"] == 200

        normal_user.department_id = test_department.id
        db.add(normal_user)
        db.commit()

        listing = client.post(
            "/api/v1/system/user/list",
            headers=admin_headers,
            json={"username": normal_user.username, "email": None, "deptId": str(test_department.id)},
        ).json()
        assert listing["code"] == 200

    def test_update_roles_not_found(self, client, admin_headers, db):
        resp = client.post(
            "/api/v1/system/user/updateRoles",
            headers=admin_headers,
            json={"id": str(uuid4()), "roleIds": []},
        )
        assert resp.status_code == 404

    def test_update_status_not_found(self, client, admin_headers, db):
        resp = client.post(
            "/api/v1/system/user/updateStatus",
            headers=admin_headers,
            json={"id": str(uuid4()), "status": 1},
        )
        assert resp.status_code == 404

    def test_reset_pwd_not_found(self, client, admin_headers, db):
        resp = client.post(
            "/api/v1/system/user/resetPwd",
            headers=admin_headers,
            json={"id": str(uuid4()), "newPwd": "NewPass123"},
        )
        assert resp.status_code == 404

    def test_unlock_not_found(self, client, admin_headers, db):
        resp = client.post("/api/v1/system/user/unlock", headers=admin_headers, json={"id": str(uuid4())})
        assert resp.status_code == 404

    def test_unlock_not_locked(self, client, admin_headers, db, normal_user):
        normal_user.locked_until = None
        normal_user.failed_login_count = 0
        db.add(normal_user)
        db.commit()
        resp = client.post("/api/v1/system/user/unlock", headers=admin_headers, json={"id": str(normal_user.id)})
        assert "未处于锁定状态" in resp.json()["msg"]

    def test_delete_user_not_found_still_succeeds(self, client, admin_headers, db):
        resp = client.post("/api/v1/system/user/delete", headers=admin_headers, json=[str(uuid4())])
        assert resp.json()["code"] == 200


class TestRoleRouterExtra:
    def test_list_with_filters(self, client, admin_headers, db, test_role):
        resp = client.post(
            "/api/v1/system/role/list?currentPage=1&pageSize=15",
            headers=admin_headers,
            json={"name": test_role.name, "code": test_role.code, "status": "0"},
        )
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1
        assert "userCount" in body["data"][0]

    def test_update_role(self, client, admin_headers, db, test_role):
        resp = client.post(
            "/api/v1/system/role/update",
            headers=admin_headers,
            json={"id": str(test_role.id), "name": "更新角色", "code": test_role.code, "status": 0},
        )
        assert resp.json()["code"] == 200

    def test_update_status_not_found(self, client, admin_headers, db):
        resp = client.post(
            "/api/v1/system/role/updateStatus",
            headers=admin_headers,
            json={"id": str(uuid4()), "status": 1},
        )
        assert resp.status_code == 404

    def test_get_role_auth_not_found(self, client, admin_headers, db):
        resp = client.post("/api/v1/system/role/getRoleAuth", headers=admin_headers, json={"id": str(uuid4())})
        assert resp.status_code == 404

    def test_update_role_auth_with_missing_menus_and_apis(self, client, admin_headers, db, test_role):
        resp = client.post(
            "/api/v1/system/role/updateRoleAuth",
            headers=admin_headers,
            json={"id": str(test_role.id), "menuIds": [str(uuid4())], "apiIds": [str(uuid4())]},
        )
        assert resp.json()["code"] == 200

    def test_update_role_auth_not_found_role(self, client, admin_headers, db):
        # updateMenus/updateApis 对不存在的角色返回 None，路由仍返回成功
        resp = client.post(
            "/api/v1/system/role/updateRoleAuth",
            headers=admin_headers,
            json={"id": str(uuid4()), "menuIds": [], "apiIds": []},
        )
        assert resp.json()["code"] == 200
