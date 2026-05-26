"""controllers/notice.py + controllers/role.py 单元测试"""
import pytest
from uuid import uuid4

from sqlmodel import Session, SQLModel, create_engine, select

from app.controllers.notice import noticeController
from app.controllers.role import roleController
from app.models import User, Role, Menu, Api, Notice, NoticeRead
from app.models.enums import MethodType
from app.models.notice import NoticeCreate, NoticeUpdate
from app.models.role import RoleCreate
from app.utils.password import get_password_hash


# ─── 独立内存 DB ─────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def ctrl_engine():
    _engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture
def ctrl_session(ctrl_engine):
    from sqlalchemy import event
    connection = ctrl_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ═══════════════════════════════════════════════════════════════════════
# NoticeController
# ═══════════════════════════════════════════════════════════════════════

class TestNoticeController:
    @pytest.mark.asyncio
    async def test_get_unread_count_empty(self, ctrl_session):
        user = User(
            username="ncuser", nickname="NC", email="nc@test.com",
            password=get_password_hash("Nc12345678"), phone="13800000100", remark="test",
        )
        ctrl_session.add(user)
        ctrl_session.commit()
        ctrl_session.refresh(user)

        count = await noticeController.get_unread_count(ctrl_session, user.id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unread_count_with_unread(self, ctrl_session):
        user = User(
            username="ncuser2", nickname="NC2", email="nc2@test.com",
            password=get_password_hash("Nc22345678"), phone="13800000101", remark="test",
        )
        ctrl_session.add(user)
        ctrl_session.commit()
        ctrl_session.refresh(user)

        # 发布通知
        notice = Notice(title="unread test", content="test", type=0, level="info", status=1)
        ctrl_session.add(notice)
        ctrl_session.commit()
        ctrl_session.refresh(notice)

        count = await noticeController.get_unread_count(ctrl_session, user.id)
        assert count >= 1

    @pytest.mark.asyncio
    async def test_get_unread_list(self, ctrl_session):
        user = User(
            username="ncuser3", nickname="NC3", email="nc3@test.com",
            password=get_password_hash("Nc32345678"), phone="13800000102", remark="test",
        )
        ctrl_session.add(user)
        ctrl_session.commit()
        ctrl_session.refresh(user)

        notice = Notice(title="list test", content="test", type=0, level="info", status=1)
        ctrl_session.add(notice)
        ctrl_session.commit()

        items = await noticeController.get_unread_list(ctrl_session, user.id, limit=20)
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_mark_as_read(self, ctrl_session):
        user = User(
            username="ncuser4", nickname="NC4", email="nc4@test.com",
            password=get_password_hash("Nc42345678"), phone="13800000103", remark="test",
        )
        ctrl_session.add(user)
        notice = Notice(title="read test", content="test", type=0, level="info", status=1)
        ctrl_session.add(user)
        ctrl_session.add(notice)
        ctrl_session.commit()
        ctrl_session.refresh(user)
        ctrl_session.refresh(notice)

        result = await noticeController.mark_as_read(ctrl_session, notice.id, user.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_mark_as_read_duplicate(self, ctrl_session):
        """重复标记已读 → 返回 False"""
        user = User(
            username="ncuser5", nickname="NC5", email="nc5@test.com",
            password=get_password_hash("Nc52345678"), phone="13800000104", remark="test",
        )
        notice = Notice(title="dup read", content="test", type=0, level="info", status=1)
        ctrl_session.add(user)
        ctrl_session.add(notice)
        ctrl_session.commit()
        ctrl_session.refresh(user)
        ctrl_session.refresh(notice)

        await noticeController.mark_as_read(ctrl_session, notice.id, user.id)
        result = await noticeController.mark_as_read(ctrl_session, notice.id, user.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, ctrl_session):
        user = User(
            username="ncuser6", nickname="NC6", email="nc6@test.com",
            password=get_password_hash("Nc62345678"), phone="13800000105", remark="test",
        )
        ctrl_session.add(user)
        for i in range(3):
            ctrl_session.add(Notice(title=f"all read {i}", content="t", type=0, level="info", status=1))
        ctrl_session.commit()
        ctrl_session.refresh(user)

        count = await noticeController.mark_all_as_read(ctrl_session, user.id)
        assert count >= 3


# ═══════════════════════════════════════════════════════════════════════
# RoleController
# ═══════════════════════════════════════════════════════════════════════

class TestRoleController:
    @pytest.mark.asyncio
    async def test_update_menus(self, ctrl_session):
        role = Role(name="菜单角色", code="menu_role", status=0, remark="test")
        ctrl_session.add(role)
        menu = Menu(
            parentId=None, menuType=0, title="测试菜单", name="TestMenu",
            path="/test", component="", rank=1, showLink=True,
        )
        ctrl_session.add(menu)
        ctrl_session.commit()
        ctrl_session.refresh(role)
        ctrl_session.refresh(menu)

        await roleController.updateMenus(ctrl_session, role.id, [menu.id])
        ctrl_session.refresh(role)
        assert len(role.menus) == 1

    @pytest.mark.asyncio
    async def test_update_menus_nonexistent_role(self, ctrl_session):
        result = await roleController.updateMenus(ctrl_session, uuid4(), [])
        assert result is None

    @pytest.mark.asyncio
    async def test_update_apis(self, ctrl_session):
        role = Role(name="API角色", code="api_role", status=0, remark="test")
        ctrl_session.add(role)
        api = Api(path="/api/v1/test", method=MethodType.GET, summary="测试", tags="test")
        ctrl_session.add(api)
        ctrl_session.commit()
        ctrl_session.refresh(role)
        ctrl_session.refresh(api)

        await roleController.updateApis(ctrl_session, role.id, [api.id])
        ctrl_session.refresh(role)
        assert len(role.apis) == 1

    @pytest.mark.asyncio
    async def test_update_apis_nonexistent_role(self, ctrl_session):
        result = await roleController.updateApis(ctrl_session, uuid4(), [])
        assert result is None
