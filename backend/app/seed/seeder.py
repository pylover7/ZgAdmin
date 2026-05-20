"""幂等种子数据导入器 — 只创建缺失的数据，重复运行安全"""
from sqlmodel import Session, select

from app.models import Menu, Department
from app.settings.log import logger
from .data.menus import DEFAULT_MENUS
from .data.departments import DEFAULT_DEPARTMENTS


def _create_menu_tree(session: Session, parent: Menu, children: list[dict]):
    for item in children:
        sub_children = item.pop("children", [])
        menu = Menu(parentId=parent.id, **item)
        session.add(menu)
        session.commit()
        session.refresh(menu)
        if sub_children:
            _create_menu_tree(session, menu, sub_children)


def seed_menus(session: Session):
    existing = session.exec(select(Menu)).first()
    if existing:
        logger.info("菜单已存在，跳过种子数据导入")
        return
    logger.info("导入默认菜单...")
    for item in DEFAULT_MENUS:
        children = item.pop("children", [])
        menu = Menu(**item)
        session.add(menu)
        session.commit()
        session.refresh(menu)
        _create_menu_tree(session, menu, children)
    logger.info("默认菜单导入完成")


def seed_departments(session: Session):
    existing = session.exec(select(Department)).first()
    if existing:
        logger.info("部门已存在，跳过种子数据导入")
        return None
    logger.info("导入默认部门...")
    for item in DEFAULT_DEPARTMENTS:
        dept = Department(**item)
        session.add(dept)
        session.commit()
        session.refresh(dept)
    logger.info("默认部门导入完成")
    return session.exec(select(Department)).first()


def seed_all(session: Session):
    """运行所有种子数据导入"""
    dept = seed_departments(session)
    seed_menus(session)
    return dept
