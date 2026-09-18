"""剩余未覆盖分支补测 — middlewares/dependency/controllers/role-api"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models import Department, User
from app.settings.log import logger as userController_logger
from app.utils.password import get_password_hash


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


class TestSimpleBaseMiddlewareCall:
    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        from app.core.middlewares import SimpleBaseMiddleware

        app = AsyncMock()
        mw = SimpleBaseMiddleware(app)
        assert mw.app is app
        await mw(scope={"type": "websocket"}, receive=None, send=None)
        app.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_http_scope_full_cycle(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from app.core.middlewares import BackGroundTaskMiddleware

        app = FastAPI()

        @app.get("/ping")
        async def ping():
            return {"ok": True}

        app.add_middleware(BackGroundTaskMiddleware)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as client:
            resp = await client.get("/ping")
        assert resp.json() == {"ok": True}


class TestGetDbGenerator:
    def test_yields_session(self, monkeypatch):
        import app.core.dependency as dep

        engine = _engine()
        monkeypatch.setattr(dep, "engine", engine, raising=False)
        gen = dep.get_db()
        session = next(gen)
        assert isinstance(session, Session)
        gen.close()


class TestDepartmentMultiLevelName:
    def test_nested_department_full_name(self):
        from app.controllers.department import deptController

        engine = _engine()
        with Session(engine) as session:
            root = Department(name="总部", sort=0, status=0)
            session.add(root)
            session.commit()
            session.refresh(root)
            child = Department(name="研发", parentId=root.id, sort=0, status=0)
            session.add(child)
            session.commit()
            session.refresh(child)
            user = MagicMock(spec=User)
            user.department = child
            assert deptController.get_all_name(session, user) == "研发"

    def test_department_without_parent(self):
        from app.controllers.department import deptController

        engine = _engine()
        with Session(engine) as session:
            dept = Department(name="总部", sort=0, status=0)
            session.add(dept)
            session.commit()
            session.refresh(dept)
            user = MagicMock(spec=User)
            user.department = dept
            assert deptController.get_all_name(session, user) == ""

    def test_no_department(self):
        from app.controllers.department import deptController

        engine = _engine()
        with Session(engine) as session:
            user = MagicMock(spec=User)
            user.department = None
            assert deptController.get_all_name(session, user) == ""


class TestUserControllerBranches:
    @pytest.mark.asyncio
    async def test_update_with_password_hashes(self):
        from app.controllers.user import userController
        from app.models.user import UserUpdate

        engine = _engine()
        with Session(engine) as session:
            user = User(
                username="upd",
                email="upd@test.com",
                password=get_password_hash("old123456"),
                status=1,
                is_superuser=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            data = UserUpdate(username="upd", email="upd@test.com", password="NewPass123")
            updated = await userController.update(session, user.id, data)
            assert updated is not None
            assert updated.password != get_password_hash("old123456")

    @pytest.mark.asyncio
    async def test_login_success_writes_log(self):
        from app.controllers.user import userController
        from app.models.login import CredentialsSchema

        engine = _engine()
        with Session(engine) as session:
            user = User(
                username="loginer",
                email="login@test.com",
                password=get_password_hash("Good123456"),
                status=1,
                is_superuser=False,
            )
            session.add(user)
            session.commit()

            req = Mock(spec=Request)
            req.client = Mock()
            req.client.host = "8.8.8.8"
            req.headers = {"User-Agent": "Mozilla/5.0 (X11) Chrome/120.0"}

            with (
                patch("app.controllers.user.getIpAddress", AsyncMock(return_value="美国")),
                patch.object(userController_logger, "loginSuccess", AsyncMock()) as mock_login_success,
            ):
                result = await userController.authenticate(
                    session=session,
                    credentials=CredentialsSchema(username="loginer", password="Good123456"),
                    request=req,
                )
            assert result is not None
            mock_login_success.assert_awaited_once()


class TestRoleApiError:
    def test_update_role_auth_exception(self, client, admin_headers, db, test_role):
        with patch(
            "app.api.v1.system.role.roleController.updateMenus",
            AsyncMock(side_effect=RuntimeError("boom")),
        ):
            resp = client.post(
                "/api/v1/system/role/updateRoleAuth",
                headers=admin_headers,
                json={"id": str(test_role.id), "menuIds": [], "apiIds": []},
            )
        assert resp.status_code == 400


class TestRoleControllerSkipSlashId:
    @pytest.mark.asyncio
    async def test_update_apis_skips_string_with_slash(self):
        from app.controllers.role import roleController

        engine = _engine()
        with Session(engine) as session:
            from app.models import Role

            role = Role(name="r", code="r1", status=0, remark="")
            session.add(role)
            session.commit()
            session.refresh(role)
            # 传入含 "/" 的字符串 → 走 continue 分支
            await roleController.updateApis(session, role.id, ["a/b"])
            assert role.apis == []


class TestFileControllerMimeMismatch:
    @pytest.mark.asyncio
    async def test_mime_extension_mismatch_removes_file(self):
        import os

        from app.controllers.file import fileController

        engine = _engine()
        with (
            Session(engine) as session,
            patch("app.controllers.file.os.remove") as mock_remove,
            patch("app.controllers.file.detect_mime", return_value="application/pdf"),
        ):
            result = await fileController.create_from_upload(
                session=session,
                filename="notreally.png",
                file_content=b"%PDF-1.4 fake",
                uploader_id=uuid4(),
            )
        assert isinstance(result, tuple)
        assert result[0] is None
        mock_remove.assert_called_once()
        del os


class TestApiErrorBranches:
    def test_create_user_exception(self, client, admin_headers, db, security_policy):
        with patch("app.api.v1.system.user.userController.create", AsyncMock(side_effect=RuntimeError("boom"))):
            resp = client.post(
                "/api/v1/system/user/add",
                headers=admin_headers,
                json={
                    "username": "boomuser",
                    "nickname": "x",
                    "email": "boom@test.com",
                    "password": "Passw0rd123",
                    "phone": "13700137111",
                    "remark": "",
                    "status": 1,
                    "is_superuser": False,
                },
            )
        assert resp.status_code == 400

    def test_delete_user_exception(self, client, admin_headers, db):
        with patch("app.api.v1.system.user.userController.delete", AsyncMock(side_effect=RuntimeError("boom"))):
            resp = client.post("/api/v1/system/user/delete", headers=admin_headers, json=[str(uuid4())])
        assert resp.status_code == 400

    def test_list_user_filter_by_email(self, client, admin_headers, db, normal_user):
        body = client.post(
            "/api/v1/system/user/list",
            headers=admin_headers,
            json={"username": None, "email": normal_user.email, "deptId": None},
        ).json()
        assert body["code"] == 200

    @pytest.mark.asyncio
    async def test_batch_upload_empty_filename(self, db, admin_user):
        """直接调用路由函数：含空文件名 → 走 fail_list 分支"""
        from app.api.v1.resource.file import upload_batch

        empty = Mock()
        empty.filename = ""
        import json

        resp = await upload_batch(session=db, current_user=admin_user, files=[empty])
        payload = json.loads(resp.body)
        assert payload["code"] == 200
        assert len(payload["data"]["fail"]) == 1
        assert payload["data"]["fail"][0]["filename"] == "未知文件"

    def test_operation_logs_time_range(self, client, admin_headers, db):
        from app.models.logs import OperationLog

        db.add(OperationLog(username="u", message="m", level="info"))
        db.commit()
        body = client.post(
            "/api/v1/monitor/logs/operation/list",
            headers=admin_headers,
            json={
                "level": ["info"],
                "operationTime": ["2000-01-01 00:00:00", "2999-12-31 23:59:59"],
            },
        ).json()
        assert body["code"] == 200

    def test_system_logs_time_range(self, client, admin_headers, db):
        from app.models.logs import SystemLog

        db.add(SystemLog(module="m", message="m", level="info"))
        db.commit()
        body = client.post(
            "/api/v1/monitor/logs/system/list",
            headers=admin_headers,
            json={"module": "m", "operationTime": ["2000-01-01 00:00:00", "2999-12-31 23:59:59"]},
        ).json()
        assert body["code"] == 200


class TestUserControllerMoreBranches:
    @pytest.mark.asyncio
    async def test_update_with_password_bearing_schema(self):
        """传入含 password 字段的 schema（如 UserCreate）→ 走 hashed 分支"""
        from app.controllers.user import userController
        from app.models import UserCreate

        engine = _engine()
        with Session(engine) as session:
            user = User(
                username="pwdup2",
                email="pwdup2@test.com",
                password=get_password_hash("Old123456"),
                status=1,
                is_superuser=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            old_hash = user.password
            data = UserCreate(
                username="pwdup2",
                email="pwdup2@test.com",
                password="BrandNew123",
                status=1,
                is_superuser=False,
            )
            updated = await userController.update(session, user.id, data)
            assert updated is not None
            assert updated.password != old_hash

    @pytest.mark.asyncio
    async def test_authenticate_role_disabled(self):
        from app.controllers.user import userController
        from app.models import Role
        from app.models.login import CredentialsSchema

        engine = _engine()
        with Session(engine) as session:
            role = Role(name="disabledrole", code="dr", status=0, remark="")
            session.add(role)
            session.commit()
            session.refresh(role)
            user = User(
                username="roledisabled",
                email="rd@test.com",
                password=get_password_hash("Good123456"),
                status=1,
                is_superuser=False,
            )
            user.roles = [role]
            session.add(user)
            session.commit()

            req = Mock(spec=Request)
            req.client = Mock()
            req.client.host = "8.8.4.4"
            req.headers = {"User-Agent": "Mozilla/5.0 (X11) Chrome/120.0"}
            with (
                patch("app.controllers.user.getIpAddress", AsyncMock(return_value="美国")),
                pytest.raises(HTTPException) as exc,
            ):
                await userController.authenticate(
                    session=session,
                    credentials=CredentialsSchema(username="roledisabled", password="Good123456"),
                    request=req,
                )
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_last_login_missing_user(self):
        from app.controllers.user import userController

        engine = _engine()
        with Session(engine) as session, pytest.raises(HTTPException) as exc:
            await userController.update_last_login(session, uuid4())
        assert exc.value.status_code == 404
