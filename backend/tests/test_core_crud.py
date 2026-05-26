"""core/crud.py CRUDBase 单元测试 — 使用真实 SQLite"""
import pytest
from uuid import uuid4

from sqlmodel import Session, SQLModel, create_engine, select

from app.core.crud import CRUDBase
from app.models import User, Role, Department, Notice
from app.models.user import UserCreate
from app.models.role import RoleCreate
from app.utils.password import get_password_hash


# 用于不需要 UpdateSchema 的 CRUDBase 实例化
class _DummyUpdateSchema(SQLModel):
    pass


# ─── 使用独立的内存 DB，避免与 conftest 冲突 ──────────────────────────
@pytest.fixture(scope="module")
def crud_engine():
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture
def crud_session(crud_engine):
    connection = crud_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)

    nested = connection.begin_nested()

    from sqlalchemy import event

    @event.listens_for(session, "after_transaction_end")
    def _restart(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ─── User CRUD 测试 ───────────────────────────────────────────────────

class TestCRUDBaseUser:
    @pytest.fixture
    def user_crud(self):
        return CRUDBase[User, UserCreate, _DummyUpdateSchema](User)

    def _make_user_create(self, suffix: str) -> UserCreate:
        return UserCreate(
            username=f"testuser{suffix}",
            nickname=f"Test{suffix}",
            email=f"test{suffix}@example.com",
            password=get_password_hash("Test12345678"),
            phone=f"13800138{suffix.zfill(4)}",  # 确保 phone 唯一
            remark="test",
            status=1,
            is_superuser=False,
        )

    @pytest.mark.asyncio
    async def test_create(self, crud_session, user_crud):
        user_in = self._make_user_create("1")
        user = await user_crud.create(crud_session, obj_in=user_in)
        assert user.id is not None
        assert user.username == "testuser1"

    @pytest.mark.asyncio
    async def test_get(self, crud_session, user_crud):
        user_in = self._make_user_create("2")
        created = await user_crud.create(crud_session, obj_in=user_in)
        fetched = await user_crud.get(crud_session, created.id)
        assert fetched is not None
        assert fetched.username == "testuser2"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, crud_session, user_crud):
        result = await user_crud.get(crud_session, uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_all(self, crud_session, user_crud):
        for i in range(3):
            user_in = self._make_user_create(f"all{i}")
            await user_crud.create(crud_session, obj_in=user_in)
        users = await user_crud.all(crud_session)
        assert len(users) >= 3

    @pytest.mark.asyncio
    async def test_list_pagination(self, crud_session, user_crud):
        for i in range(5):
            user_in = self._make_user_create(f"list{i}")
            await user_crud.create(crud_session, obj_in=user_in)
        total, page = await user_crud.list(crud_session, currentPage=1, pageSize=2)
        assert total >= 5
        assert len(page) == 2

    @pytest.mark.asyncio
    async def test_delete(self, crud_session, user_crud):
        user_in = self._make_user_create("del")
        created = await user_crud.create(crud_session, obj_in=user_in)
        result = await user_crud.delete(crud_session, [created.id])
        assert result is True
        assert await user_crud.get(crud_session, created.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_id(self, crud_session, user_crud):
        result = await user_crud.delete(crud_session, [uuid4()])
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_all(self, crud_session, user_crud):
        user_in = self._make_user_create("delall")
        await user_crud.create(crud_session, obj_in=user_in)
        count = await user_crud.delete_all(crud_session)
        assert count >= 1


# ─── Role CRUD 测试 ───────────────────────────────────────────────────

class TestCRUDBaseRole:
    @pytest.fixture
    def role_crud(self):
        return CRUDBase[Role, RoleCreate, _DummyUpdateSchema](Role)

    @pytest.mark.asyncio
    async def test_create_role(self, crud_session, role_crud):
        role_in = RoleCreate(
            name="测试角色",
            code="test_role",
            status=0,
            remark="测试",
        )
        role = await role_crud.create(crud_session, obj_in=role_in)
        assert role.id is not None
        assert role.name == "测试角色"
        assert role.code == "test_role"

    @pytest.mark.asyncio
    async def test_get_latest(self, crud_session, role_crud):
        # 先创建一个角色确保有数据
        role_in = RoleCreate(name="最新角色", code="latest_role", status=0, remark="")
        await role_crud.create(crud_session, obj_in=role_in)
        latest = await role_crud.get_latest(crud_session)
        assert latest is not None
        assert latest.code == "latest_role"


# ─── list with where 条件过滤 ────────────────────────────────────────

class TestCRUDBaseListFilter:
    @pytest.fixture
    def user_crud(self):
        return CRUDBase[User, UserCreate, _DummyUpdateSchema](User)

    def _make_user_create(self, suffix: str) -> UserCreate:
        return UserCreate(
            username=f"filteruser{suffix}",
            nickname=f"Filter{suffix}",
            email=f"filter{suffix}@example.com",
            password=get_password_hash("Test12345678"),
            phone="13800138000",
            remark="test",
            status=1,
            is_superuser=False,
        )

    @pytest.mark.asyncio
    async def test_list_with_where(self, crud_session, user_crud):
        user_in = self._make_user_create("1")
        await user_crud.create(crud_session, obj_in=user_in)
        from sqlmodel import col
        total, results = await user_crud.list(
            crud_session,
            where=User.username == "filteruser1",
        )
        assert total >= 1
        assert all(u.username == "filteruser1" for u in results)

    @pytest.mark.asyncio
    async def test_list_empty_result(self, crud_session, user_crud):
        total, results = await user_crud.list(
            crud_session,
            where=User.username == "nonexistent_user_xyz",
        )
        assert total == 0
        assert len(results) == 0
