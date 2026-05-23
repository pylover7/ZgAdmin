# 项目结构与操作

## 项目概述

**ZgAdmin** 是一个开源的后台管理系统模板，采用前后端分离架构：

- **后端**：Python 3.13+ / FastAPI / SQLModel / PostgreSQL 或 SQLite
- **前端**：Vue 3 + TypeScript + Vite + Element Plus + Tailwind CSS 4
- **部署**：Docker 多阶段构建 + Nginx 反向代理，一键 `docker compose up -d`

**核心功能**：用户/角色/菜单/部门多级权限管理、JWT 鉴权、多种登录方式（账号密码/QQ/微信）、实时系统监控（登录/操作/系统日志）、通知系统、安全策略配置、国际化（中/英）。

**当前版本**：见 `/VERSION` 文件，前后端共享

## 根目录结构

```
/workspace/
├── backend/              # FastAPI 后端（端口 7001）
│   ├── app/              # 应用主代码
│   ├── alembic/          # 数据库迁移脚本
│   ├── config/           # INI 配置文件（运行时读写）
│   ├── static/           # 静态文件（头像、商品等）
│   ├── tests/            # 后端测试
│   ├── main.py           # 入口：uvicorn 启动
│   └── pyproject.toml    # 后端依赖与工具配置
├── frontend/             # Vue 3 前端（端口 7000/80）
│   ├── src/              # 前端源码
│   ├── locales/          # 国际化翻译文件
│   ├── mock/             # Mock 数据
│   ├── public/           # 静态资源（platform-config.json 等）
│   ├── build/            # Vite 构建配置
│   └── package.json      # 前端依赖
├── scripts/              # 运维脚本（start.sh、build.sh 等）
├── docs/                 # VitePress 文档站点
├── .env                  # 环境变量（不入库）
├── Dockerfile            # 多阶段构建（前端构建 → Nginx + 后端）
├── docker-compose.yml    # Docker Compose 编排
├── nginx.conf            # Nginx 配置（/api 代理到后端）
└── VERSION               # 项目版本号
```

## 功能模块清单

| 模块 | 后端路由 | 前端页面 | 说明 |
|------|---------|---------|------|
| 用户管理 | `/api/v1/system/user` | `views/system/user/` | CRUD、角色分配、状态管理 |
| 角色管理 | `/api/v1/system/role` | `views/system/role/` | CRUD、菜单权限+API权限绑定 |
| 菜单管理 | `/api/v1/system/menu` | `views/system/menu/` | 树形 CRUD |
| 部门管理 | `/api/v1/system/dept` | `views/system/dept/` | 树形 CRUD |
| 通知管理 | `/api/v1/system/notice` | `views/system/notice/` | CRUD + 未读/已读/全部已读 |
| API 管理 | `/api/v1/system/api` | `views/system/role/` | 自动同步、只读列表 |
| 登录日志 | `/api/v1/monitor/logs/login` | `views/monitor/logs/login/` | 分页查询、删除、清空 |
| 操作日志 | `/api/v1/monitor/logs/operation` | `views/monitor/logs/operation/` | 分页查询、删除、清空 |
| 系统日志 | `/api/v1/monitor/logs/system` | `views/monitor/logs/system/` | 分页查询、详情、删除、清空 |
| 通用设置 | `/api/v1/settings/general` | `views/settings/general/` | 站点名称/Logo/描述/语言等 |
| 登录设置 | `/api/v1/settings/login` | `views/settings/login/` | QQ/微信登录 AppID 配置 |
| 安全设置 | `/api/v1/settings/security` | `views/settings/security/` | 验证码、密码策略、IP 黑白名单 |
| 账户设置 | `/api/v1/base/userinfo` 等 | `views/account-settings/` | 个人信息/安全日志/偏好 |
| 通知铃铛 | 同通知管理 | `layout/components/lay-notice/` | 实时未读数、标记已读 |

## 常见操作

### 添加新的后端 API 模块

1. 在 `app/models/` 创建数据模型
2. 在 `app/controllers/` 创建 Controller（继承 `CRUDBase`）
3. 在 `app/api/v1/` 创建路由文件
4. 在 `app/api/v1/__init__.py` 注册路由到 `v1_router`
5. 运行 `alembic revision --autogenerate` + `alembic upgrade head`
6. 启动后 `_sync_api_routes` 自动将新路由同步到数据库

### 添加新的前端页面

1. 在 `src/views/` 创建页面目录和组件
2. 在 `src/api/` 创建 API 封装
3. 在 `backend/app/seed/data/menus.py` 添加菜单项（使用 i18n 键名）
4. 在 `locales/zh-CN.yaml` 和 `locales/en.yaml` 添加翻译
5. 后端重启后菜单自动同步到前端

### 修改数据库模型

1. 修改 `app/models/` 下的模型定义
2. `uv run alembic revision --autogenerate -m "描述"`
3. 检查生成的迁移脚本
4. `uv run alembic upgrade head`
