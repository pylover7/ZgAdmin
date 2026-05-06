"""默认菜单数据 — 模板用户在此修改或添加菜单"""
DEFAULT_MENUS = [
    dict(
        menuType=0, title="系统管理", name="system", path="/system",
        component="", rank=7, icon="ep:operation",
        children=[
            dict(menuType=0, title="用户管理", name="SystemUser",
                 path="/system/user", component="system/user/index",
                 icon="ri:admin-line", rank=1),
            dict(menuType=0, title="角色管理", name="SystemRole",
                 path="/system/role", component="system/role/index",
                 icon="ri:admin-fill", rank=2),
            dict(menuType=0, title="部门管理", name="SystemDept",
                 path="/system/dept", component="system/dept/index",
                 icon="ri:git-branch-line", rank=4),
            dict(menuType=0, title="菜单管理", name="SystemMenu",
                 path="/system/menu", component="system/menu/index",
                 icon="fluent:clover-48-regular", rank=3),
        ],
    ),
    dict(
        menuType=0, title="系统监控", name="Monitor", path="/monitor",
        component="", rank=8, icon="ep:monitor",
        children=[
            dict(menuType=0, title="登录日志", name="LoginLog",
                 path="/monitor/login-log", component="monitor/logs/login/index",
                 icon="ri:window-line", rank=1),
            dict(menuType=0, title="操作日志", name="OperationLog",
                 path="/monitor/operation-logs", component="monitor/logs/operation/index",
                 icon="ri:history-fill", rank=2),
            dict(menuType=0, title="系统日志", name="SystemLog",
                 path="/monitor/system-logs", component="monitor/logs/system/index",
                 icon="ri:file-search-line", rank=3),
        ],
    ),
    dict(
        menuType=0, title="系统设置", name="settings", path="/settings",
        component="", rank=9, icon="ep:setting",
        children=[
            dict(menuType=0, title="通用设置", name="GenSettings",
                 path="/settings/general", component="settings/general/index",
                 icon="ri:code-line", rank=1),
            dict(menuType=0, title="登录设置", name="LoginSettings",
                 path="/settings/login", component="settings/login/index",
                 icon="ri:settings-2-line", rank=2),
        ],
    ),
]
