"""seed/seeder.py 幂等种子导入单元测试"""
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.models import Department, Menu
from app.seed import seed_all, seed_departments, seed_menus


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


class TestSeedDepartments:
    def test_first_run_creates_and_returns_first(self):
        with Session(_engine()) as session:
            dept = seed_departments(session)
            assert dept is not None
            assert session.exec(select(Department)).first() is not None

    def test_second_run_is_noop(self):
        engine = _engine()
        with Session(engine) as session:
            seed_departments(session)
            before = len(session.exec(select(Department)).all())
        with Session(engine) as session:
            assert seed_departments(session) is None
            assert len(session.exec(select(Department)).all()) == before


class TestSeedMenus:
    def test_creates_menu_tree(self):
        engine = _engine()
        with Session(engine) as session:
            seed_menus(session)
            menus = session.exec(select(Menu)).all()
            assert len(menus) > 1
            # 至少存在一个子菜单（parentId 非空）
            assert any(m.parentId for m in menus)

    def test_second_run_is_noop(self):
        engine = _engine()
        with Session(engine) as session:
            seed_menus(session)
            count = len(session.exec(select(Menu)).all())
        with Session(engine) as session:
            seed_menus(session)
            assert len(session.exec(select(Menu)).all()) == count


class TestSeedAll:
    def test_seed_all_returns_dept(self):
        engine = _engine()
        with Session(engine) as session:
            dept = seed_all(session)
            assert dept is not None
            assert session.exec(select(Menu)).first() is not None
