"""默认菜单数据 — 模板用户在此修改或添加菜单  title 使用 i18n 键名，前端 transformI18n 自动翻译"""
DEFAULT_MENUS = [
    {
        "menuType": 0,
        "title": "menus.pureSysManagement",
        "name": "system",
        "path": "/system",
        "component": "",
        "rank": 7,
        "icon": "ep:operation",
        "children": [
            {
                "menuType": 0,
                "title": "menus.pureUser",
                "name": "SystemUser",
                "path": "/system/user",
                "component": "system/user/index",
                "icon": "ri:admin-line",
                "rank": 1
            },
            {
                "menuType": 0,
                "title": "menus.pureRole",
                "name": "SystemRole",
                "path": "/system/role",
                "component": "system/role/index",
                "icon": "ri:admin-fill",
                "rank": 2
            },
            {
                "menuType": 0,
                "title": "menus.pureDept",
                "name": "SystemDept",
                "path": "/system/dept",
                "component": "system/dept/index",
                "icon": "ri:git-branch-line",
                "rank": 4},
            {
                "menuType": 0,
                "title": "menus.pureSystemMenu",
                "name": "SystemMenu",
                "path": "/system/menu",
                "component": "system/menu/index",
                "icon": "fluent:clover-48-regular",
                "rank": 3
            },
            {
                "menuType": 0,
                "title": "menus.zgNoticeSettings",
                "name": "SystemNotice",
                "path": "/system/notice",
                "component": "system/notice/index",
                "icon": "ri:notification-3-line",
                "rank": 500,
            }
        ],
    },
    {
        "menuType": 0,
        "title": "menus.pureSysMonitor",
        "name": "Monitor",
        "path": "/monitor",
        "component": "",
        "rank": 8,
        "icon": "ep:monitor",
        "children": [
            {
                "menuType": 0,
                "title": "menus.pureLoginLog",
                "name": "LoginLog",
                "path": "/monitor/login-log",
                "component": "monitor/logs/login/index",
                "icon": "ri:window-line",
                "rank": 1
            },
            {
                "menuType": 0,
                "title": "menus.pureOperationLog",
                "name": "OperationLog",
                "path": "/monitor/operation-logs",
                "component": "monitor/logs/operation/index",
                "icon": "ri:history-fill",
                "rank": 2
            },
            {
                "menuType": 0,
                "title": "menus.pureSystemLog",
                "name": "SystemLog",
                "path": "/monitor/system-logs",
                "component": "monitor/logs/system/index",
                "icon": "ri:file-search-line",
                "rank": 3
            },
        ],
    },
    {
        "menuType": 0,
        "title": "menus.pureSysSettings",
        "name": "settings",
        "path": "/settings",
        "component": "",
        "rank": 9,
        "icon": "ep:setting",
        "children": [
            {
                "menuType": 0,
                "title": "menus.pureGenSettings",
                "name": "GenSettings",
                "path": "/settings/general",
                "component": "settings/general/index",
                "icon": "ri:code-line",
                "rank": 1
            },
            {
                "menuType": 0,
                "title": "menus.pureLoginSettings",
                "name": "LoginSettings",
                "path": "/settings/login",
                "component": "settings/login/index",
                "icon": "ri:settings-2-line",
                "rank": 2
            },
            {
                "menuType": 0,
                "title": "menus.pureSecuritySettings",
                "name": "SecuritySettings",
                "path": "/settings/security",
                "component": "settings/security/index",
                "icon": "ri:shield-check-line",
                "rank": 3
            },
        ],
    },
    {
        "menuType": 0,
        "title": "menus.zgResourceManagement",
        "name": "resource",
        "path": "/resource",
        "component": "",
        "rank": 6,
        "icon": "ep:folder-opened",
        "children": [
            {
                "menuType": 0,
                "title": "menus.zgFileManager",
                "name": "FileManager",
                "path": "/resource/file",
                "component": "resource/file/index",
                "icon": "ri:file-list-3-line",
                "rank": 1
            },
        ],
    },
]
