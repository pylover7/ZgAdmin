# 后端架构详细文档

## 入口与启动

```
backend/main.py → uvicorn.run("app:app", ...)
                → app/__init__.py → create_app()
```

- `create_app()` 创建 FastAPI 实例，注册中间件、路由、异常处理器
- `lifespan_context` 在启动时初始化 Redis、数据库种子数据、同步 API 路由到数据库、启动定时任务
- 应用挂载 `/static` 静态文件目录

## 目录结构

```
backend/app/
├── __init__.py           # create_app()、lifespan_context
├── api/v1/               # API 路由层
│   ├── __init__.py       # v1_router 汇总所有子路由
│   ├── base/             # 公开接口（登录、验证码、初始化配置）
│   ├── system/           # 系统管理接口（用户/角色/菜单/部门/通知/API管理）
│   ├── monitor/          # 监控接口（系统信息、日志查询）
│   ├── settings/         # 设置接口（通用/登录/安全/邮件设置）
│   └── resource/         # 资源管理接口（文件上传/下载/预览）
├── controllers/          # 业务逻辑层（Controller 模式）
├── models/               # SQLModel 数据模型 + Pydantic Schema
├── core/                 # 核心基础设施
│   ├── crud.py           # CRUDBase 泛型基类
│   ├── database.py       # 数据库引擎、初始化、种子数据
│   ├── dependency.py     # FastAPI 依赖注入（认证、权限、限流）
│   ├── redis.py          # Redis 抽象层（生产真实 Redis / 开发内存适配器）
│   ├── exceptions.py     # 自定义异常
│   ├── middlewares.py    # 中间件
│   └── ctx.py            # ContextVar（存储当前用户 ID）
├── seed/                 # 种子数据
│   └── data/menus.py     # 默认菜单数据（使用 i18n 键名）
├── settings/             # 配置管理
│   ├── __init__.py       # Settings 类（pydantic-settings，读 .env）
│   ├── database.py       # db_engine() 数据库连接字符串生成
│   └── log.py            # Loguru 日志配置
├── utils/                # 工具函数
│   ├── jwtt.py           # JWT 创建/解码、QQ OAuth
│   ├── password.py       # 密码哈希/验证
│   ├── password_policy.py# 密码复杂度校验、历史检查
│   ├── captcha.py        # 服务端图形验证码
│   ├── ip.py             # IP 地址工具
│   ├── emails.py         # 邮件发送
│   ├── system_info.py    # 系统信息采集
│   ├── file_upload.py    # 文件上传校验（扩展名白名单、MIME 检测、分类）
│   ├── localTime.py      # 本地时间工具
│   ├── signed_url.py     # 签名 URL 生成
│   ├── staticFileUtils.py# 静态文件路径工具
│   └── version.py        # 版本信息工具
```

## API 路由结构

所有 API 以 `/api/v1` 为前缀，路由注册在 `app/api/v1/__init__.py`：

| 路由前缀 | 模块 | 认证要求 | 说明 |
|----------|------|---------|------|
| `/api/v1/base` | `base_router` | 部分公开 | 登录、验证码、初始化配置、Token 刷新 |
| `/api/v1/system` | `systemRouter` | `DependPermission` | 用户/角色/菜单/部门/通知/API 管理 |
| `/api/v1/monitor` | `monitorRouter` | `DependPermission` | 系统监控、日志查询 |
| `/api/v1/settings/general` | `generalProtectedRouter` | `DependPermission` | 通用设置管理 |
| `/api/v1/settings/login` | `loginProtectedRouter` | `DependPermission` | 登录设置管理 |
| `/api/v1/settings/security` | `securityProtectedRouter` | `DependPermission` | 安全策略管理 |
| `/api/v1/settings/email` | `emailProtectedRouter` | `DependPermission` | 邮件配置管理 |
| `/api/v1/settings` | `settingsRouter` | `DependPermission` | 其他设置 |
| `/api/v1/resource` | `resourceRouter` | `DependPermission` | 文件上传/下载/预览/统计 |

## 数据模型（SQLModel）

所有模型定义在 `app/models/` 下，基类为 `BaseModel`（UUID 主键）+ `TimestampMixin`（created_at）。

**核心模型**：

| 模型 | 文件 | 说明 |
|------|------|------|
| `User` | `user.py` | 用户（含 QQ 登录字段、密码历史、偏好） |
| `Role` | `role.py` | 角色 |
| `Menu` | `menu.py` | 菜单（树形结构） |
| `Department` | `department.py` | 部门（树形结构） |
| `Api` | `api.py` | API 接口（自动同步注册路由） |
| `Notice` | `notice.py` | 通知 |
| `NoticeRead` | `notice.py` | 通知已读关联 |
| `LoginLog` | `logs.py` | 登录日志 |
| `OperationLog` | `logs.py` | 操作日志 |
| `SystemLog` | `logs.py` | 系统日志 |
| `SecurityPolicy` | `security.py` | 安全策略（单行表） |
| `IPRule` | `security.py` | IP 黑白名单 |
| `SiteConfig` | `config.py` | 站点配置（全局单行表） |
| `OAuthConfig` | `config.py` | OAuth 登录配置（全局单行表） |
| `EmailConfig` | `config.py` | 邮件配置（全局单行表） |
| `File` | `file.py` | 文件（上传/下载/预览） |
| `Item` | `items.py` | 条目（示例模型，owner 外键） |

**关联表**（`link.py`）：

- `UserRoleLink`：用户 ↔ 角色（多对多）
- `RoleMenuLink`：角色 ↔ 菜单（多对多）
- `RoleApiLink`：角色 ↔ API（多对多）

## 认证与权限体系

**认证流程**（`app/core/dependency.py`）：

1. `AuthControl.is_authed`：解析 JWT Token → 获取用户 → 校验用户/角色状态
2. `PermissionControl.has_permission`：检查当前用户角色绑定的 API 是否包含请求的 (method, path)
3. 超级管理员（`is_superuser=True`）跳过所有权限检查

**JWT 配置**（`app/settings/__init__.py`）：

- Access Token 有效期：2 小时
- Refresh Token 有效期：3 天
- 算法：HS256
- SECRET_KEY：未设置时自动生成并持久化到 `.secret_key` 文件

## 配置管理

1. **环境变量**（`pydantic-settings`）：`.env` 文件 → `Settings` 类，启动时只读
2. **数据库配置表**（`app/models/config.py` + `app/controllers/config.py`）：
   - `SiteConfig`：站点名称/Logo/描述/语言/版权/ICP
   - `OAuthConfig`：QQ/微信登录 AppID/AppKey/回调地址
   - `EmailConfig`：SMTP 服务器配置
   - `SecurityPolicy`：验证码/密码策略/IP 规则
   - 由 `ConfigController` 统一管理，支持敏感字段脱敏

`/api/v1/base/init` 接口合并环境变量 + 数据库配置，返回前端初始化所需的站点信息、功能开关、安全配置。

## Redis 抽象层

`app/core/redis.py` 定义了 `RedisClient` Protocol，提供两种实现：

- **生产**：真实 Redis 连接（`REDIS_URL` 环境变量配置）
- **开发**：`MemoryRedis` 内存适配器（功能完全等价，无需安装 Redis）

## 数据库迁移

使用 Alembic，常用命令：

```bash
cd backend
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
uv run alembic downgrade -1
```

迁移脚本位于 `backend/alembic/versions/`。
