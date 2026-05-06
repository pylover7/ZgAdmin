from sqlmodel import Session, create_engine, select
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.controllers.user import userController
from app.core.schedule import update_expired_orders
from app.models import *
from app.settings.log import logger
from app.utils.staticFileUtils import check_dir_exists
from app.core import engine, DatabaseSession

scheduler = AsyncIOScheduler()


def init_api(app: FastAPI, session: Session):
    """
    初始化API
    :param app:
    :param session: Session
    :return:
    """
    apiOld = session.exec(select(Api)).all()
    apiList = []
    apis = app.openapi()["paths"]
    for path, value in apis.items():
        for method, value2 in value.items():
            tags = value2.get("tags", [])
            tag = ",".join(tags) if tags else ""
            summary = value2.get("summary")
            if len(apiOld) == 0:
                api = Api(
                    path=path,
                    method=method.upper(),
                    tags=tag,
                    summary=summary
                )
                session.add(api)
                apiList.append(api.id)
                session.commit()
            else:
                apiIsNew = True
                for api in apiOld:
                    if api.path == path:
                        apiIsNew = False
                        api.method = method.upper()
                        api.summary = summary
                        api.tags = tag
                        session.add(api)
                        break
                if apiIsNew:
                    api = Api(
                        path=path,
                        method=method.upper(),
                        tags=tag,
                        summary=summary
                    )
                    session.add(api)
    session.commit()
    return apiList


def init_menus(session: Session):
    """
    初始化菜单
    :return:
    """
    menus = session.exec(select(Menu)).all()
    if len(menus) == 0:
        system = Menu(
            menuType=0,
            title="系统管理",
            name="system",
            path="/system",
            component="",
            rank=7,
            icon="ep:operation",
        )
        session.add(system)
        session.commit()
        session.refresh(system)
        systemUser = Menu(
            parentId=system.id,
            menuType=0,
            title="用户管理",
            name="SystemUser",
            path="/system/user",
            component="system/user/index",
            icon="ri:admin-line",
            rank=1
        )
        systemDept = Menu(
            parentId=system.id,
            menuType=0,
            title="部门管理",
            name="SystemDept",
            path="/system/dept",
            component="system/dept/index",
            icon="ri:git-branch-line",
            rank=4
        )
        systemRole = Menu(
            parentId=system.id,
            menuType=0,
            title="角色管理",
            name="SystemRole",
            path="/system/role",
            component="system/role/index",
            icon="ri:admin-fill",
            rank=2
        )
        systemMenu = Menu(
            parentId=system.id,
            menuType=0,
            title="菜单管理",
            name="SystemMenu",
            path="/system/menu",
            component="system/menu/index",
            icon="fluent:clover-48-regular",
        )
        session.add(systemMenu)
        session.add(systemRole)
        session.add(systemDept)
        session.add(systemUser)

        monitor = Menu(
            menuType=0,
            title="系统监控",
            name="Monitor",
            path="/monitor",
            component="",
            rank=8,
            icon="ep:monitor",
        )
        session.add(monitor)
        session.commit()
        session.refresh(monitor)
        loginLog = Menu(
            parentId=monitor.id,
            menuType=0,
            title="登录日志",
            name="LoginLog",
            path="/monitor/login-log",
            component="monitor/logs/login/index",
            icon="ri:window-line",
        )
        operationLog = Menu(
            parentId=monitor.id,
            menuType=0,
            title="操作日志",
            name="OperationLog",
            path="/monitor/operation-logs",
            component="monitor/logs/operation/index",
            icon="ri:history-fill",
        )
        systemLog = Menu(
            parentId=monitor.id,
            menuType=0,
            title="系统日志",
            name="SystemLog",
            path="/monitor/system-logs",
            component="monitor/logs/system/index",
            icon="ri:file-search-line",
        )
        session.add(loginLog)
        session.add(operationLog)
        session.add(systemLog)
        session.commit()

        settings = Menu(
            menuType=0,
            title="系统设置",
            name="settings",
            path="/settings",
            component="",
            rank=9,
            icon="ep:setting",
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
        genSettings = Menu(
            parentId=settings.id,
            menuType=0,
            title="通用设置",
            name="GenSettings",
            path="/settings/general",
            component="settings/general/index",
            icon="ri:code-line",
            rank=1
        )
        loginSettings = Menu(
            parentId=settings.id,
            menuType=0,
            title="登录设置",
            name="LoginSettings",
            path="/settings/login",
            component="settings/login/index",
            icon="ri:settings-2-line",
            rank=2
        )
        session.add(genSettings)
        session.add(loginSettings)
        session.commit()


async def init_dept(session: Session):
    """
    初始化部门
    :return:
    """
    depts = session.exec(select(Department)).all()
    if len(depts) == 0:
        dept = Department(
            name="管理员",
            status=1,
            remark="管理员所属部门",
        )
        session.add(dept)
        session.commit()
        session.refresh(dept)
        return dept


async def init_data(app: FastAPI) -> None:
    logger.info("初始化数据库...")
    SQLModel.metadata.create_all(engine)
    logger.info("检查静态文件目录...")
    check_dir_exists([
        settings.STATIC_PATH,
        settings.AVATAR_PATH,
        settings.GOODS_PATH,
    ])
    with DatabaseSession() as session:
        dept = await init_dept(session)
        admin = session.exec(
            select(User).where(
                (User.email == settings.EMAIL_TEST_USER) | 
                (User.username == settings.FIRST_SUPERUSER) |
                (User.is_superuser == True)
            )
        ).first()
        if not admin:
            logger.info("创建管理员账户...")
            user_in = UserCreate(
                username=settings.FIRST_SUPERUSER,
                nickname="管理员",
                email=settings.EMAIL_TEST_USER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                status=1,
                is_superuser=True,
                phone="13800138000",
                remark="这是管理员"
            )
            admin = await userController.create(session=session, obj_in=user_in)
            logger.info(f"创建管理员账户成功，管理员用户名为：{admin.username}")
            if dept is not None:
                dept.users.append(admin)
                session.add(dept)
                session.commit()
                session.refresh(admin)
        else:
            logger.info("管理员账户已存在，跳过管理员创建...")

        logger.info("初始化API...")
        init_api(app, session)
        logger.info("初始化菜单...")
        init_menus(session)
        logger.info("启动定时任务...")
        scheduler.add_job(update_expired_orders, "interval", seconds=120)
        scheduler.start()
