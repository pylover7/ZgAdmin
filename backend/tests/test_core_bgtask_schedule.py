"""core/bgtask.py、core/schedule.py、core/ctx.py、core/__init__.py 单元测试"""

from unittest.mock import MagicMock

import pytest
from fastapi.background import BackgroundTasks
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core import DatabaseSession
from app.core.bgtask import BgTasks
from app.core.ctx import CTX_BG_TASKS, CTX_USER_ID
from app.core.schedule import update_expired_orders


class TestBgTasks:
    @pytest.mark.asyncio
    async def test_init_and_get_bg_tasks_obj(self):
        await BgTasks.init_bg_tasks_obj()
        obj = await BgTasks.get_bg_tasks_obj()
        assert isinstance(obj, BackgroundTasks)

    @pytest.mark.asyncio
    async def test_add_task_and_execute(self):
        await BgTasks.init_bg_tasks_obj()
        calls = []
        await BgTasks.add_task(calls.append, 1)
        await BgTasks.execute_tasks()
        assert calls == [1]

    @pytest.mark.asyncio
    async def test_execute_tasks_without_tasks(self):
        await BgTasks.init_bg_tasks_obj()
        # 无任务时不应抛错
        await BgTasks.execute_tasks()

    def test_ctx_defaults(self):
        assert CTX_USER_ID.get() == ""
        assert CTX_BG_TASKS.get() is None


class TestSchedule:
    @pytest.mark.asyncio
    async def test_update_expired_orders(self, monkeypatch):
        plan = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(plan)
        import app.core.schedule as schedule_module

        monkeypatch.setattr(schedule_module, "engine", plan, raising=False)
        assert await update_expired_orders() is None


class TestDatabaseSession:
    def test_context_manager_commit(self, monkeypatch):
        plan = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        import app.core as core_module

        monkeypatch.setattr(core_module, "engine", plan, raising=False)
        with DatabaseSession() as session:
            assert isinstance(session, Session)
        # __exit__ 无异常 → 正常关闭

    def test_context_manager_rollback_on_error(self, monkeypatch):
        plan = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        import app.core as core_module

        monkeypatch.setattr(core_module, "engine", plan, raising=False)
        mock_session = MagicMock()
        monkeypatch.setattr(core_module, "Session", MagicMock(return_value=mock_session))
        with pytest.raises(ValueError, match="boom"), DatabaseSession():
            raise ValueError("boom")
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
