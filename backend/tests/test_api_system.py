"""API 集成测试 — system 路由（核心 CRUD 100%）"""
from uuid import uuid4

# ═══════════════════════════════════════════════════════════════════════
# 用户管理
# ═══════════════════════════════════════════════════════════════════════

class TestUserAPI:
    def test_add_user(self, client, admin_headers, db, security_policy):
        resp = client.post("/api/v1/system/user/add", headers=admin_headers, json={
            "username": "newuser",
            "nickname": "新用户",
            "email": "newuser@test.com",
            "password": "NewUser123",
            "phone": "13700137001",
            "remark": "测试用户",
            "status": 1,
            "is_superuser": False,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_add_duplicate_user_fails(self, client, admin_headers, db, admin_user, security_policy):
        resp = client.post("/api/v1/system/user/add", headers=admin_headers, json={
            "username": "admin",
            "nickname": "重复",
            "email": "dup@test.com",
            "password": "DupUser123",
            "phone": "13700137002",
            "remark": "重复用户",
            "status": 1,
            "is_superuser": False,
        })
        assert resp.json()["code"] != 200 or "detail" in resp.json()

    def test_list_users(self, client, admin_headers, db, admin_user):
        resp = client.post("/api/v1/system/user/list", headers=admin_headers, json={
            "username": None, "email": None, "deptId": None,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1

    def test_get_user(self, client, admin_headers, db, admin_user):
        resp = client.get(f"/api/v1/system/user/get?user_id={admin_user.id}", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["username"] == "admin"
        assert "password" not in body["data"]

    def test_get_nonexistent_user(self, client, admin_headers, db):
        resp = client.get(f"/api/v1/system/user/get?user_id={uuid4()}", headers=admin_headers)
        assert resp.json()["code"] != 200

    def test_update_user_status(self, client, admin_headers, db, normal_user):
        resp = client.post("/api/v1/system/user/updateStatus", headers=admin_headers, json={
            "id": str(normal_user.id),
            "status": 0,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_update_user_roles(self, client, admin_headers, db, normal_user, test_role):
        resp = client.post("/api/v1/system/user/updateRoles", headers=admin_headers, json={
            "id": str(normal_user.id),
            "roleIds": [str(test_role.id)],
        })
        body = resp.json()
        assert body["code"] == 200

    def test_reset_user_password(self, client, admin_headers, db, normal_user):
        resp = client.post("/api/v1/system/user/resetPwd", headers=admin_headers, json={
            "id": str(normal_user.id),
            "newPwd": "ResetPwd123",
        })
        body = resp.json()
        assert body["code"] == 200

    def test_unlock_user(self, client, admin_headers, db, normal_user):
        resp = client.post("/api/v1/system/user/unlock", headers=admin_headers, json={
            "id": str(normal_user.id),
        })
        body = resp.json()
        assert body["code"] == 200

    def test_delete_user(self, client, admin_headers, db, normal_user):
        resp = client.post("/api/v1/system/user/delete", headers=admin_headers, json=[
            str(normal_user.id),
        ])
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 角色管理
# ═══════════════════════════════════════════════════════════════════════

class TestRoleAPI:
    def test_add_role(self, client, admin_headers, db):
        resp = client.post("/api/v1/system/role/add", headers=admin_headers, json={
            "name": "测试角色",
            "code": "test_role_api",
            "status": 0,
            "remark": "API测试创建",
        })
        body = resp.json()
        assert body["code"] == 200

    def test_list_roles(self, client, admin_headers, db, test_role):
        resp = client.post("/api/v1/system/role/list", headers=admin_headers, json={
            "name": None, "code": None, "status": None,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_get_all_roles(self, client, admin_headers, db, test_role):
        resp = client.get("/api/v1/system/role/all", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]) >= 1

    def test_update_role_status(self, client, admin_headers, db, test_role):
        resp = client.post("/api/v1/system/role/updateStatus", headers=admin_headers, json={
            "id": str(test_role.id),
            "status": 1,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_get_role_auth(self, client, admin_headers, db, test_role):
        resp = client.post("/api/v1/system/role/getRoleAuth", headers=admin_headers, json={
            "id": str(test_role.id),
        })
        body = resp.json()
        assert body["code"] == 200
        assert "menus" in body["data"]
        assert "apis" in body["data"]

    def test_update_role_auth(self, client, admin_headers, db, test_role):
        resp = client.post("/api/v1/system/role/updateRoleAuth", headers=admin_headers, json={
            "id": str(test_role.id),
            "menuIds": [],
            "apiIds": [],
        })
        body = resp.json()
        assert body["code"] == 200

    def test_delete_role(self, client, admin_headers, db):
        # 先创建再删除
        resp = client.post("/api/v1/system/role/add", headers=admin_headers, json={
            "name": "待删除角色",
            "code": "to_delete_role",
            "status": 0,
            "remark": "待删除",
        })
        role_id = resp.json()["data"]["id"]

        resp = client.post("/api/v1/system/role/delete", headers=admin_headers, json=[role_id])
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 部门管理
# ═══════════════════════════════════════════════════════════════════════

class TestDepartmentAPI:
    def test_add_department(self, client, admin_headers, db):
        resp = client.post("/api/v1/system/dept/add", headers=admin_headers, json={
            "name": "测试部门API",
            "sort": 1,
            "status": 0,
            "phone": "13800138000",
            "principal": "张三",
            "email": "dept@test.com",
            "remark": "测试",
            "user": [],
        })
        body = resp.json()
        assert body["code"] == 200

    def test_list_departments(self, client, admin_headers, db, test_department):
        resp = client.get("/api/v1/system/dept/list", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]) >= 1

    def test_update_department(self, client, admin_headers, db, test_department):
        resp = client.post("/api/v1/system/dept/update", headers=admin_headers, json={
            "id": str(test_department.id),
            "name": "更新后部门",
            "sort": 1,
            "status": 0,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_delete_department(self, client, admin_headers, db, test_department):
        resp = client.post("/api/v1/system/dept/delete", headers=admin_headers, json=[
            str(test_department.id),
        ])
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 通知管理
# ═══════════════════════════════════════════════════════════════════════

class TestNoticeAPI:
    def test_add_notice(self, client, admin_headers, db, admin_user):
        resp = client.post("/api/v1/system/notice/add", headers=admin_headers, json={
            "title": "测试通知",
            "content": "这是一条测试通知",
            "type": 0,
            "level": "info",
            "status": 1,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["title"] == "测试通知"

    def test_list_notices(self, client, admin_headers, db):
        # 先创建通知
        client.post("/api/v1/system/notice/add", headers=admin_headers, json={
            "title": "列表测试通知",
            "content": "test",
            "type": 0,
            "status": 1,
        })
        resp = client.post("/api/v1/system/notice/list", headers=admin_headers, json={
            "title": None, "type": None, "level": None, "status": None,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_update_notice(self, client, admin_headers, db, admin_user):
        # 先创建
        resp = client.post("/api/v1/system/notice/add", headers=admin_headers, json={
            "title": "更新前标题",
            "content": "test",
            "type": 0,
            "status": 1,
        })
        notice_id = resp.json()["data"]["id"]

        resp = client.post("/api/v1/system/notice/update", headers=admin_headers, json={
            "id": notice_id,
            "title": "更新后标题",
        })
        body = resp.json()
        assert body["code"] == 200

    def test_get_unread_notices(self, client, admin_headers, db, admin_user):
        # 先发布一条通知
        client.post("/api/v1/system/notice/add", headers=admin_headers, json={
            "title": "未读测试通知",
            "content": "test",
            "type": 0,
            "status": 1,
        })
        resp = client.get("/api/v1/system/notice/unread", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert "count" in body["data"]

    def test_mark_notice_read(self, client, admin_headers, db, admin_user):
        # 先发布通知
        resp = client.post("/api/v1/system/notice/add", headers=admin_headers, json={
            "title": "标记已读测试",
            "content": "test",
            "type": 0,
            "status": 1,
        })
        notice_id = resp.json()["data"]["id"]

        # 标记已读
        resp = client.post("/api/v1/system/notice/read", headers=admin_headers, json={
            "notice_id": notice_id,
        })
        body = resp.json()
        assert body["code"] == 200

    def test_mark_all_read(self, client, admin_headers, db, admin_user):
        resp = client.post("/api/v1/system/notice/readAll", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200

    def test_delete_notice(self, client, admin_headers, db, admin_user):
        # 先创建
        resp = client.post("/api/v1/system/notice/add", headers=admin_headers, json={
            "title": "待删除通知",
            "content": "test",
            "type": 0,
            "status": 1,
        })
        notice_id = resp.json()["data"]["id"]

        resp = client.post("/api/v1/system/notice/delete", headers=admin_headers, json=[notice_id])
        body = resp.json()
        assert body["code"] == 200
