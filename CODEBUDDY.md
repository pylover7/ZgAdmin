# ZgAdmin — 项目 AI Agent 导航手册

> 本文档为 AI Agent 提供 ZgAdmin 项目的全景导览，涵盖架构、技术栈、目录结构、核心模块、开发约定与部署方式。Agent 在对本项目进行任何代码操作前，应先通读本文档。

---

## 1. 项目概述

**ZgAdmin** 是一个开源的后台管理系统模板，采用前后端分离架构：

- **后端**：Python 3.13+ / FastAPI / SQLModel / PostgreSQL 或 SQLite
- **前端**：Vue 3 + TypeScript + Vite + Element Plus + Tailwind CSS 4
- **部署**：Docker 多阶段构建 + Nginx 反向代理，一键 `docker compose up -d`

**核心功能**：用户/角色/菜单/部门多级权限管理、JWT 鉴权、多种登录方式（账号密码/QQ/微信）、实时系统监控（登录/操作/系统日志）、通知系统、安全策略配置、国际化（中/英）。

**当前版本**：见 `/VERSION` 文件，前后端共享

---

## 2. 项目根目录结构

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

---

## 3. 后端架构（Backend）

### 3.1 入口与启动

```
backend/main.py → uvicorn.run("app:app", ...)
                → app/__init__.py → create_app()
```

- `create_app()` 创建 FastAPI 实例，注册中间件、路由、异常处理器
- `lifespan_context` 在启动时初始化 Redis、数据库种子数据、同步 API 路由到数据库、启动定时任务
- 应用挂载 `/static` 静态文件目录

### 3.2 目录结构详解

```
backend/app/
├── __init__.py           # create_app()、lifespan_context
├── api/v1/               # API 路由层
│   ├── __init__.py       # v1_router 汇总所有子路由
│   ├── base/             # 公开接口（登录、验证码、初始化配置）
│   ├── system/           # 系统管理接口（用户/角色/菜单/部门/通知/API管理）
│   ├── monitor/          # 监控接口（系统信息、日志查询）
│   ├── settings/         # 设置接口（通用/登录/安全设置）
│   └── pay/              # 支付接口（微信支付，暂未完成）
├── controllers/          # 业务逻辑层（Controller 模式）
├── models/               # SQLModel 数据模型 + Pydantic Schema
├── core/                 # 核心基础设施
│   ├── crud.py           # CRUDBase 泛型基类
│   ├── database.py       # 数据库引擎、初始化、种子数据
│   ├── dependency.py    # FastAPI 依赖注入（认证、权限、限流）
│   ├── redis.py          # Redis 抽象层（生产真实 Redis / 开发内存适配器）
│   ├── exceptions.py     # 自定义异常
│   ├── middlewares.py    # 中间件
│   └── ctx.py            # ContextVar（存储当前用户 ID）
├── seed/                 # 种子数据
│   └── data/menus.py     # 默认菜单数据（使用 i18n 键名）
├── settings/             # 配置管理
│   ├── __init__.py       # Settings 类（pydantic-settings，读 .env）
│   ├── config.py         # Config 类（INI 文件读写，运行时可改）
│   ├── database.py       # db_engine() 数据库连接字符串生成
│   └── log.py            # Loguru 日志配置
├── utils/                # 工具函数
│   ├── jwtt.py           # JWT 创建/解码、QQ OAuth
│   ├── password.py       # 密码哈希/验证
│   ├── password_policy.py# 密码复杂度校验、历史检查
│   ├── captcha.py        # 服务端图形验证码
│   ├── ip.py             # IP 地址工具
│   ├── emails.py         # 邮件发送
│   └── system_info.py    # 系统信息采集
└── cli/                  # CLI 命令（generate 脚手架）
```

### 3.3 API 路由结构

所有 API 以 `/api/v1` 为前缀，路由注册在 `app/api/v1/__init__.py`：

| 路由前缀 | 模块 | 认证要求 | 说明 |
|----------|------|---------|------|
| `/api/v1/base` | `base_router` | 部分公开 | 登录、验证码、初始化配置、Token 刷新 |
| `/api/v1/system` | `systemRouter` | `DependPermission` | 用户/角色/菜单/部门/通知/API 管理 |
| `/api/v1/monitor` | `monitorRouter` | `DependPermission` | 系统监控、日志查询 |
| `/api/v1/settings/general` | `generalProtectedRouter` | `DependPermission` | 通用设置管理 |
| `/api/v1/settings/login` | `loginProtectedRouter` | `DependPermission` | 登录设置管理 |
| `/api/v1/settings/security` | `securityProtectedRouter` | `DependPermission` | 安全策略管理 |
| `/api/v1/settings` | `settingsRouter` | `DependPermission` | 其他设置 |
| `/api/v1/pay` | `payRouter` | `DependPermission` | 支付设置（开发中） |

### 3.4 数据模型（SQLModel）

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

**关联表**（`link.py`）：

- `UserRoleLink`：用户 ↔ 角色（多对多）
- `RoleMenuLink`：角色 ↔ 菜单（多对多）
- `RoleApiLink`：角色 ↔ API（多对多）

### 3.5 认证与权限体系

**认证流程**（`app/core/dependency.py`）：

1. `AuthControl.is_authed`：解析 JWT Token → 获取用户 → 校验用户/角色状态
2. `PermissionControl.has_permission`：检查当前用户角色绑定的 API 是否包含请求的 (method, path)
3. 超级管理员（`is_superuser=True`）跳过所有权限检查

**依赖注入速查**：

| 依赖 | 用途 |
|------|------|
| `DependAuth` | 仅认证，返回 User 对象 |
| `DependPermission` | 认证 + 权限检查 |
| `DependUser` | `Annotated[User, DependAuth]`，直接注入当前用户 |
| `SessionDep` | 数据库 Session 注入 |
| `DependRateLimit` | IP 级别限流（Redis 滑动窗口） |

**JWT 配置**（`app/settings/__init__.py`）：

- Access Token 有效期：2 小时
- Refresh Token 有效期：2 天
- 算法：HS256
- SECRET_KEY：未设置时自动生成并持久化到 `.secret_key` 文件

### 3.6 统一响应格式

定义在 `app/models/base.py`：

```python
Success(code=200, msg="OK", data=..., success=True)
Fail(code=400, msg="Fail", data=None)
SuccessExtra(code=200, data=..., total=0, currentPage=1, pageSize=20)  # 分页
FailAuth(code=401, msg="Unauthorized")
```

### 3.7 Controller 模式

业务逻辑封装在 `app/controllers/` 下的 Controller 类中，继承 `CRUDBase`：

```python
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    async def create(session, obj_in) -> ModelType
    async def delete(session, idList) -> bool
    async def update(session, pk, obj_in) -> Optional[ModelType]
    async def get(session, pk) -> ModelType | None
    async def list(session, currentPage, pageSize, where, order) -> (Total, list)
```

### 3.8 Redis 抽象层

`app/core/redis.py` 定义了 `RedisClient` Protocol，提供两种实现：

- **生产**：真实 Redis 连接（`REDIS_URL` 环境变量配置）
- **开发**：`MemoryRedis` 内存适配器（功能完全等价，无需安装 Redis）

### 3.9 配置管理

双轨配置：

1. **环境变量**（`pydantic-settings`）：`.env` 文件 → `Settings` 类，启动时只读
2. **INI 文件**（`app/settings/config.py`）：`config/base.ini`、`config/pay.ini` → `Config` 类，运行时读写

`/api/v1/base/init` 接口合并两种配置源，返回前端初始化所需的站点信息、功能开关、安全配置。

### 3.10 数据库迁移

使用 Alembic，常用命令：

```bash
cd backend
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
uv run alembic downgrade -1
```

迁移脚本位于 `backend/alembic/versions/`。

---

## 4. 前端架构（Frontend）

### 4.1 技术栈

- **框架**：Vue 3（Composition API + `<script setup>`）
- **语言**：TypeScript
- **构建**：Vite 8
- **UI 库**：Element Plus
- **CSS**：Tailwind CSS 4 + SCSS
- **状态管理**：Pinia
- **路由**：Vue Router 5（History 模式）
- **HTTP**：Axios（封装在 `src/utils/http/`）
- **国际化**：vue-i18n（`locales/zh-CN.yaml`、`locales/en.yaml`）
- **包管理器**：Bun
- **基础模板**：vue-pure-admin

### 4.2 目录结构详解

```
frontend/src/
├── main.ts               # 应用入口
├── App.vue               # 根组件
├── api/                  # API 调用封装
│   ├── base.ts           # 初始化配置、验证码
│   ├── user.ts           # 登录、Token 刷新
│   ├── system.ts         # 用户/角色/菜单/部门/日志/API 管理
│   ├── notice.ts         # 通知管理
│   ├── settings.ts       # 通用/登录/安全设置
│   ├── monitor.ts        # 系统监控
│   ├── routes.ts         # 动态路由获取
│   ├── list.ts           # 列表接口
│   ├── mock.ts           # Mock 数据接口
│   └── utils.ts          # API URL 前缀工具
├── views/                # 页面视图
│   ├── login/            # 登录页（含 QQ/微信/注册组件）
│   ├── welcome/          # 首页仪表盘
│   ├── system/           # 系统管理（用户/角色/菜单/部门/通知）
│   ├── monitor/          # 系统监控（登录/操作/系统日志）
│   ├── settings/         # 系统设置（通用/登录/安全）
│   ├── account-settings/ # 账户设置（个人信息/安全日志/偏好）
│   ├── about/            # 关于页面
│   └── error/            # 错误页（403/404/500）
├── layout/               # 布局框架
│   ├── index.vue         # 主布局
│   ├── components/       # 布局组件
│   │   ├── lay-sidebar/  # 侧边栏
│   │   ├── lay-navbar/   # 导航栏
│   │   ├── lay-tag/      # 标签页
│   │   ├── lay-notice/   # 通知铃铛（对接后端通知 API）
│   │   ├── lay-search/  # 全局搜索
│   │   ├── lay-panel/   # 面板
│   │   ├── lay-setting/ # 设置面板
│   │   └── lay-footer/  # 页脚
│   └── hooks/            # 布局相关 hooks
├── router/               # 路由
│   ├── index.ts          # 路由实例 + 守卫
│   ├── utils.ts          # 动态路由加载、菜单构建
│   └── modules/          # 静态路由模块（自动导入）
├── store/                # Pinia 状态管理
│   ├── modules/
│   │   ├── user.ts       # 用户状态（登录/登出/Token 刷新）
│   │   ├── permission.ts # 权限状态（动态路由/菜单）
│   │   ├── app.ts        # 应用全局状态
│   │   ├── multiTags.ts  # 标签页状态
│   │   ├── settings.ts   # 设置状态
│   │   └── epTheme.ts    # Element Plus 主题
│   └── types.ts          # Store 类型定义
├── components/           # 公共组件（Re* 系列）
├── config/               # 全局配置
│   └── index.ts          # platform-config.json 加载 + 后端 /base/init 合并
├── plugins/              # 插件注册
│   ├── elementPlus.ts    # Element Plus 按需注册
│   ├── i18n.ts           # 国际化
│   ├── echarts.ts        # ECharts
│   └── vxeTable.ts       # VXE Table
├── directives/           # 自定义指令（auth、perms、copy、longpress 等）
├── style/                # 全局样式（SCSS + Tailwind CSS）
├── types/                # TypeScript 类型定义
├── utils/                # 工具函数
│   ├── http/             # Axios 封装（PureHttp，Token 自动刷新）
│   ├── auth.ts           # Token 存储（Cookie + localStorage）
│   ├── message.ts        # 消息提示
│   ├── tree.ts           # 树形数据处理
│   └── sso.ts            # SSO 单点登录
└── assets/               # 静态资源（SVG、图片、图标字体）
```

### 4.3 请求层架构

**HTTP 封装**（`src/utils/http/`）：

- `PureHttp` 类封装 Axios，自动注入 Token、自动刷新过期 Token
- 请求白名单：`/refreshToken`、`/accessToken`、`/base/init`、`/base/captcha`
- Token 过期时自动调用 `refreshTokenApi` 刷新，排队等待的请求在刷新成功后重发
- 响应 401 自动登出，403 跳转错误页

**Token 存储**（`src/utils/auth.ts`）：

- `accessToken` + `refreshToken` + `expires` 存储在 Cookie（`authorized-token`）
- 用户信息（`username`、`nickname`、`roles`、`permissions`）存储在 localStorage（`user-info`）

### 4.4 路由与权限

**路由模式**：混合模式（静态路由 + 动态路由）

1. **静态路由**：`src/router/modules/` 下自动导入，登录前即可访问（如 `/login`、`/welcome`、`/about`）
2. **动态路由**：登录后调用 `getAsyncRoutes` 从后端获取菜单数据 → `initRouter()` 构建动态路由 → `router.addRoute()`

**路由守卫**（`src/router/index.ts`）：

- 已登录用户不能访问 `/login`
- 无权限页面跳转 `/error/403`
- 动态路由加载完成后自动跳转

**菜单权限**：后端返回的菜单数据中包含角色信息，前端根据用户角色过滤可访问菜单。

### 4.5 页面开发约定

每个功能页面遵循以下文件组织模式：

```
views/system/xxx/
├── index.vue       # 页面主组件
├── form.vue        # 表单弹窗组件（如有）
└── utils/
    ├── hook.tsx     # 页面逻辑 Hook（Composition API）
    ├── types.ts     # 页面类型定义
    └── rule.ts      # 表单校验规则
```

**API 调用约定**：

```typescript
// src/api/xxx.ts
const xxxUrl = (url: string) => apiV1(`/module${url}`);
export const getXxxList = (params) => http.request<ResultTable>("post", xxxUrl("/list"), { data, params });
```

**分页响应类型**：`ResultTable` = `{ code, success, msg, data, total, currentPage, pageSize }`

### 4.6 前端配置加载流程

1. 读取 `public/platform-config.json`（静态配置：标题、主题、布局等）
2. 调用 `/api/v1/base/init` 获取后端动态配置（站点信息、功能开关、安全配置）
3. 后端配置覆盖静态配置中的对应字段
4. 最终配置通过 `getConfig()` 全局访问

### 4.7 公共组件库（Re* 系列）

> **重要**：开发业务页面时，优先使用以下已有组件，避免重复造轮子。参考 [pure-admin 官方文档](https://github.com/pure-admin/pure-admin-doc) 获取更多用法。

#### 布局与容器

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `ReCol` | `components/ReCol/` | 响应式列，封装 el-col 统一所有断点 | `<ReCol :value="6">` 等同 xs/sm/md/lg/xl=6 |
| `ReSplitPane` | `components/ReSplitPane/` | 可拖拽分割面板，支持水平/垂直 | `<SplitPane :splitSet="{ split:'vertical', defaultPercent:30, minPercent:20 }">` 插槽 `#paneL`/`#paneR` |

#### 对话框与抽屉（命令式调用）

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `ReDialog` | `components/ReDialog/` | 命令式对话框，支持多弹窗叠加、自定义渲染器、全屏、Loading | `addDialog({ title, contentRenderer, beforeSure })` / `closeDialog()` / `closeAllDialog()` |
| `ReDrawer` | `components/ReDrawer/` | 命令式抽屉，与 ReDialog API 一致 | `addDrawer({ title, direction, contentRenderer })` / `closeDrawer()` |

#### 表格工具栏

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `RePureTableBar` | `components/RePureTableBar/` | Element Plus Table 工具栏：刷新、密度切换、列设置(拖拽排序/显隐/固定)、全屏 | `<PureTableBar :columns="cols" @refresh="fn"><template #buttons>...</template><template #default="{ size, dynamicColumns }"><pure-table :columns="dynamicColumns" :size="size" /></template></PureTableBar>` |
| `ReVxeTableBar` | `components/ReVxeTableBar/` | VxeTable 工具栏，与 RePureTableBar 功能类似 | `<VxeTableBar :vxeTableRef="xTable" :columns="cols">` 用法同上 |

#### 权限控制

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `ReAuth` | `components/ReAuth/` | 角色权限控制，有权限则渲染子内容 | `<Auth :value="['admin']">内容</Auth>` |
| `RePerms` | `components/RePerms/` | 按钮/操作权限控制 | `<Perms :value="['btn_add']"><el-button>新增</el-button></Perms>` |

#### 图标系统

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `ReIcon` | `components/ReIcon/` | 统一图标渲染入口，自动识别图标类型 | `useRenderIcon(icon, attrs?)` 返回组件 |
| `IconSelect` | `components/ReIcon/Select.vue` | 图标选择器，支持分类浏览和搜索 | `<IconSelect v-model="iconName" />` |

#### 数据展示

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `ReText` | `components/ReText/` | 文本省略+悬停提示，基于 el-text | `<ReText :lineClamp="2">长文本...</ReText>` |
| `ReTreeLine` | `components/ReTreeLine/` | el-tree 树形连接线 | 在 el-tree 的 `#default` 插槽中 `<ReTreeLine :node="node" :data="data" />` |
| `ReSegmented` | `components/ReSegmented/` | 分段控制器（类 Ant Design） | `<ReSegmented v-model="idx" :options="[{label:'日',icon:'ep:calendar'},{label:'周'}]" />` |
| `ReFlicker` | `components/ReFlicker/` | 圆点/方形闪烁动画 | `useRenderFlicker({ width:'12px', background:'#67C23A' })` |
| `ReCountTo` | `components/ReCountTo/` | 数字滚动动画（普通+弹跳翻牌两种） | `<ReNormalCountTo :startVal="0" :endVal="9999" :duration="2000" prefix="$" />` |
| `ReFlop` | `components/ReFlop/` | 翻牌式时钟 | `<ReFlop />` |
| `ReTypeit` | `components/ReTypeit/` | 打字机效果 | `<TypeIt :options="{ strings: ['Hello'], speed: 100 }" />` |

#### 媒体处理

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `ReCropper` | `components/ReCropper/` | 图片裁剪，支持圆形/矩形、右键菜单操作 | `<ReCropper src="url" :circled="true" @cropper="onCropper" />` |
| `ReCropperPreview` | `components/ReCropperPreview/` | 裁剪+预览，右侧 Popover 展示结果 | `<ReCropperPreview imgSrc="url" @cropper="onCropper" />` |
| `ReQrcode` | `components/ReQrcode/` | 二维码生成，支持 canvas/img、Logo 嵌套、过期遮罩 | `<ReQrcode :text="'https://example.com'" :width="200" />` |
| `ReBarcode` | `components/ReBarcode/` | 条形码生成 | `<ReBarcode tag="canvas" text="123456789" type="CODE128" />` |
| `ReImageVerify` | `components/ReImageVerify/` | Canvas 图形验证码 | `<ReImageVerify v-model:code="verifyCode" />` |

#### 其他

| 组件 | 路径 | 功能 | 核心用法 |
|------|------|------|----------|
| `ReAnimateSelector` | `components/ReAnimateSelector/` | animate.css 动画选择器，悬停预览 | `<ReAnimateSelector v-model="name" />` |
| `ReSeamlessScroll` | `components/ReSeamlessScroll/` | 无缝滚动，支持上下左右、悬停暂停 | `<ReSeamlessScroll :data="list" :classOption="{ direction:'top', step:0.5 }">` |
| `ReSelector` | `components/ReSelector/` | 范围选择器 | `<ReSelector :max="[1..10]" :echo="[2,5]" @selectedVal="fn" />` |
| `ReMap/Amap` | `components/ReMap/` | 高德地图组件 | `<Amap />` |
| `ReFlowChart` | `components/ReFlowChart/` | LogicFlow 流程图（Control/NodePanel/DataDialog） | 按需导入子组件 |

### 4.8 样式体系与复用指南

> **核心原则**：业务页面 `<style>` 标签应为空，优先使用 Tailwind 工具类、Element Plus 组件样式和全局 CSS 变量，避免自定义样式。

#### Tailwind 自定义工具类（`src/style/tailwind.css`）

| 类名 | 效果 | 使用频率 |
|------|------|----------|
| `flex-c` | flex 水平垂直居中 | 极高 |
| `flex-ac` | flex 均匀分布 + 垂直居中 | 中等 |
| `flex-bc` | flex 两端对齐 + 垂直居中 | 高 |
| `navbar-bg-hover` | 导航栏过渡 hover 效果 | 导航专用 |
| `bg-bg_color` | 页面背景色（桥接 `--el-bg-color`） | 高 |
| `text-primary` | 主题色文字（桥接 `--el-color-primary`） | 高 |
| `text-text_color_primary` | 主要文字色 | 中等 |
| `text-text_color_regular` | 常规文字色 | 中等 |

#### 全局 CSS 变量（`:root` 作用域）

| 变量 | 亮色值 | 暗色值 | 用途 |
|------|--------|--------|------|
| `--pure-transition-duration` | `0.3s` | `0.3s` | 侧边栏动画时长，全局复用 |
| `--pure-border-color` | `rgb(5 5 5 / 6%)` | `rgb(253 253 253 / 12%)` | 通用边框色 |
| `--pure-switch-off-color` | `#a6a6a6` | `#ffffff3f` | Switch 关闭色 |
| `--pure-theme-menu-bg` | 由主题定义 | 由主题定义 | 菜单背景色 |
| `--pure-theme-menu-text` | 由主题定义 | 由主题定义 | 菜单文字色 |
| `--pure-theme-sub-menu-active-text` | 由主题定义 | 由主题定义 | 子菜单激活文字色 |

#### Element Plus 辅助类（`src/style/element-plus.scss`）

| 类名 | 效果 | 使用方式 |
|------|------|----------|
| `.reset-margin` | 重置按钮内图标与文字间距为 2px | `<el-button class="reset-margin">` |
| `.pure-popper` | Popover 无内边距 | `<el-popover popper-class="pure-popper">` |
| `.pure-scrollbar` | 自定义滚动条（6px 宽、圆角） | `popper-class="pure-scrollbar"` 或容器 class |
| `.pure-dialog` | 自定义 Dialog 样式（关闭按钮、footer） | `<el-dialog class="pure-dialog">` |
| `.pure-message` | 自定义 ElMessage 样式 | `ElMessage({ customClass: "pure-message" })` |

#### 全局功能类

| 类名 | 效果 | 作用范围 |
|------|------|----------|
| `.html-grey` | 灰色模式（100% 灰度） | 添加到 `<html>` |
| `.html-weakness` | 色弱模式（80% 反色） | 添加到 `<html>` |
| `.clearfix` | 清除浮动 | 容器 |
| `.dark` | `color-scheme: dark` | 暗色模式标识 |

#### Vue 过渡动画（`src/style/transition.scss`）

| 过渡名 | 效果 | 用法 |
|--------|------|------|
| `fade` | 淡入淡出（0.28s） | `<Transition name="fade">` |
| `fade-transform` | 淡入 + 左滑入 / 淡出 + 右滑出（0.5s） | `<Transition name="fade-transform" mode="out-in">` |
| `breadcrumb` | 面包屑项滑入 + 淡入 | `<TransitionGroup name="breadcrumb">` |

#### 主题系统（`src/style/theme.scss`）

8 套主题通过 `html[data-theme="xxx"]` 切换，自动覆盖 CSS 变量：

| data-theme | 主题名 | 菜单背景色 |
|------------|--------|------------|
| `light` | 亮白色 | `#fff` |
| `default` | 道奇蓝 | `#001529` |
| `saucePurple` | 深紫罗兰色 | `#130824` |
| `pink` | 深粉色 | `#28081a` |
| `dusk` | 猩红色 | `#2a0608` |
| `volcano` | 橙红色 | `#2b0e05` |
| `mingQing` | 绿宝石 | `#032121` |
| `auroraGreen` | 酸橙绿 | `#0b1e15` |

#### 业务页面样式编写原则

1. **优先 Tailwind**：间距、字体、颜色、布局全部用 Tailwind 类完成
2. **使用 `flex-c` / `flex-bc` / `flex-ac`**：居中、两端对齐等布局场景
3. **使用全局 CSS 变量**：`var(--pure-border-color)` 等保证主题适配
4. **使用 Element Plus 辅助类**：`.pure-popper`、`.pure-scrollbar`、`.reset-margin`
5. **禁止在业务页面写自定义样式**：目标 `<style scoped>` 标签内容为空
6. **确实需要自定义样式时**：先检查是否可用 Tailwind/Element Plus/全局变量解决，仍不行再写

### 4.9 自定义指令

| 指令 | 功能 | 用法 |
|------|------|------|
| `v-auth` | 角色权限控制，无权限移除 DOM | `<div v-auth="['admin']">内容</div>` |
| `v-perms` | 按钮/操作权限控制，无权限移除 DOM | `<el-button v-perms="['btn_add']">新增</el-button>` |
| `v-copy` | 文本复制，默认双击复制 | `<span v-copy="text">双击复制</span>` / `<span v-copy:click="text">单击复制</span>` |
| `v-longpress` | 长按触发 | `<button v-longpress="fn">500ms</button>` / `v-longpress:2000="fn"` / `v-longpress:1000:200="fn"` |
| `v-optimize` | 防抖/节流 | `v-optimize="{ event:'click', fn:submit }"` / `v-optimize:throttle="{ event:'input', fn:search, timeout:500 }"` |
| `v-ripple` | 水波纹点击效果 | `<button v-ripple>` / `v-ripple.center` / `v-ripple.circle` / `v-ripple="{ class:'text-gray-300' }"` |

### 4.10 vue-pure-admin 可复用页面模式

> **用途**：开发新页面时，优先参考这些已验证的模式，避免从零设计。
> **来源**：[vue-pure-admin/src/views](https://github.com/pure-admin/vue-pure-admin/tree/main/src/views)
> **使用方式**：这些是 **vue-pure-admin 的参考实现**，不是本项目已安装的组件。需要时，去 GitHub 对应目录查看源码，复制核心逻辑到项目中，并安装所需依赖。

#### 组件用法示例（views/components/）

| 页面 | 功能 | 实现要点 | 可能需要安装的依赖 |
|------|------|---------|-------------------|
| `contextmenu/` | 右键菜单 | 基于 `@pureadmin/components` 的 `ContextMenu` | `@pureadmin/components` |
| `upload/` | 文件上传 | el-upload + 后端接口对接 | 无额外依赖 |
| `virtual-list/` | 虚拟列表 | el-table-v2 或 `vue-virtual-scroller` | `vue-virtual-scroller` |
| `waterfall/` | 瀑布流 | CSS columns 或 `vue-waterfall-plugin-next` | `vue-waterfall-plugin-next` |
| `slider/` | 幻灯片/走马灯 | `swiper` 包 | `swiper` |
| `cascader.vue` | 级联选择器 | el-cascader 省市区联动 | 无额外依赖 |
| `check-card.vue` | 勾选卡片 | el-checkbox + 卡片样式 | 无额外依赖 |
| `color-picker.vue` | 颜色选择器 | el-color-picker | 无额外依赖 |
| `json-editor.vue` | JSON 编辑器 | `vue-json-pretty` + JSON.parse 校验 | `vue-json-pretty` |
| `statistic.vue` | 统计数值展示 | el-statistic + ReCountTo | 无额外依赖 |
| `swiper.vue` | 轮播组件 | `swiper` 包 | `swiper` |
| `timeline.vue` | 时间线 | el-timeline | 无额外依赖 |

#### 功能能力（views/able/）

| 页面 | 功能 | 实现要点 | 可能需要安装的依赖 |
|------|------|---------|-------------------|
| `print/` | 打印功能 | `print-js` | `print-js` |
| `video-frame/` | 视频帧截取 | canvas drawImage + video seek | 无额外依赖 |
| `wavesurfer/` | 音频波形可视化 | `wavesurfer.js` | `wavesurfer.js` |
| `debounce.vue` | 防抖用法 | `@pureadmin/utils` 的 `debounce` | 无额外依赖 |
| `download.vue` | 文件下载 | `@pureadmin/utils` 的 `downloadByData` | 无额外依赖 |
| `draggable.vue` | 拖拽排序 | `vuedraggable` / `sortablejs` | `vuedraggable` |
| `excel.vue` | Excel 导入导出 | `xlsx` + `@pureadmin/utils` 的 `downloadByData` | `xlsx` |
| `infinite-scroll.vue` | 无限滚动 | el-table 的 `v-infinite-scroll` | 无额外依赖 |
| `pdf.vue` | PDF 预览 | `vue-pdf-embed` | `vue-pdf-embed` |
| `pinyin.vue` | 拼音转换 | `@pureadmin/utils` 的 `pinyin` | 无额外依赖 |
| `sensitive.vue` | 敏感词过滤 | 自定义 Trie 树匹配 | 无额外依赖 |
| `video.vue` | 视频播放 | `@videojs-player/vue` | `video.js` |
| `watermark.vue` | 水印 | `@pureadmin/utils` 的 `useWatermark` | 无额外依赖 |

#### 表格模式（views/table/）

| 模式 | 功能 | 实现要点 |
|------|------|---------|
| `base/` | 基础表格 | el-table + 分页，参考本项目已有页面 |
| `edit/` | 可编辑表格 | el-table + el-input/el-select 行内编辑 + 保存逻辑 |
| `high/` | 高级表格 | 配合 `RePureTableBar`（工具栏+列设置+全屏），参考本项目已有页面 |
| `virtual/` | 虚拟滚动表格 | `vxe-table` 虚拟滚动或 el-table-v2，万行级别 |

#### 结果页模式（views/result/）

| 页面 | 功能 | 实现要点 |
|------|------|---------|
| `success.vue` | 操作成功结果页 | el-result icon="success" + 描述 + 操作按钮 |
| `fail.vue` | 操作失败结果页 | el-result icon="error" + 描述 + 操作按钮 |

#### Schema 表单（views/schema-form/）

| 页面 | 功能 | 实现要点 |
|------|------|---------|
| `index.vue` | Schema 驱动动态表单 | JSON Schema → 动态渲染 el-form-item，参考 [pure-admin 文档](https://pure-admin.cn/) |

### 4.11 @pureadmin/utils 工具函数库

> **共 140+ 工具函数**，项目已安装。**导入方式**：`import { 函数名 } from "@pureadmin/utils"`。开发时优先使用这些工具函数，不要重新造轮子。详细文档：[pure-admin-utils 文档](https://pure-admin-utils.netlify.app/)
> **签名来源**：已从 `node_modules/@pureadmin/utils/dist/index.d.mts` 源码验证。

#### Vue Hooks

| Hook | 功能 | 签名 | 用法示例 |
|------|------|------|---------|
| `useECharts` | ECharts 初始化与自适应 | `(elRef: Ref\<HTMLDivElement\>, options?) → { setOptions, echarts, resize, ... }` | `const { setOptions } = useECharts(chartRef); setOptions({ series: [...] })` |
| `useDark` | 暗黑模式切换 | `(options?: { selector?, className? }) → { isDark, toggleDark }` | `const { isDark, toggleDark } = useDark()` |
| `useDraggable` | 元素拖拽（弹窗类） | `(targetRef, dragRef, args?) → { draggable, transform, init, reset }` | `const { init } = useDraggable(dialogRef, headerRef)` |
| `useWatermark` | 水印生成 | `(appendEl?, resizeReDraw?) → { setWatermark, clear }` | `const { setWatermark, clear } = useWatermark(); setWatermark("ZgAdmin")` |
| `useLoader` | 动态加载 CSS/JS | `(destroy?) → { loadCss, loadScript }` | `const { loadScript } = useLoader(); loadScript({ src: "https://cdn..." })` |
| `useResizeObserver` | 监听元素尺寸 | `(target, callback, options?) → { stop, restart }` | `const { stop } = useResizeObserver(elRef, (entries) => {...})` |
| `useScrollTo` | 缓动滚动 | `(options: { el, to, directions, duration?, callback? }) → { start, stop }` | `const { start } = useScrollTo({ el: elRef, to: 0, directions: "scrollTop", duration: 500 })` |
| `useCopyToClipboard` | 复制到剪贴板 | `(defaultValue?) → { clipboardValue, copied, update }` | `const { copied, update } = useCopyToClipboard(); update("复制的文本")` |
| `useAttrs` | 增强的 attrs | `(params?: { excludeListeners?, excludeKeys? }) → filtered attrs` | `const attrs = useAttrs({ excludeListeners: true, excludeKeys: ["class"] })` |

#### 常用工具函数

| 分类 | 函数 | 功能 | 签名（已验证） |
|------|------|------|-----------------|
| **数组/树** | `buildHierarchyTree` | 扁平数组转树（基于 id/parentId） | `buildHierarchyTree(tree: any[], pathList?) → any` 注意：需数据含 `id`、`parentId` 字段 |
| | `handleTree` | 扁平数组转树（自定义键名） | `handleTree(data, id?="id", parentId?="parentId", children?="children") → any` |
| | `deleteChildren` | 删除空 children 并组建 uniqueId | `deleteChildren(tree, pathList?) → any` 注意：空 children 的节点会被删除该字段 |
| | `getNodeByUniqueId` | 按 uniqueId 查找节点 | `getNodeByUniqueId(tree, uniqueId: number\|string) → node` |
| | `appendFieldByUniqueId` | 向指定节点追加字段 | `appendFieldByUniqueId(tree, uniqueId, fields: object) → any` |
| | `extractPathList` | 提取所有 uniqueId 路径 | `extractPathList(tree) → any[]` |
| **对象** | `clone` | 克隆（默认浅拷） | `clone(val, deep?=false) → any` |
| | `cloneDeep` | 深克隆 | `cloneDeep(val) → any` |
| | `cleanObject` | 清理空值属性 | `cleanObject(obj, options?) → obj` options 含 `includeKeys`/`excludeKeys`/`customFilter` 等 |
| | `deepEqual` | 深度比较 | `deepEqual(a, b) → boolean` |
| **类型判断** | `isString` ~ `isPromise` | 类型守卫 | `(val: unknown) => val is T` 统一模式 |
| | `isEmail` / `isPhone` / `isUrl` | 格式校验 | `(value: string) => boolean` 注意：`isPhone` 参数是 `any` |
| | `isEmpty` | 判空（数组/对象/字符串） | `isEmpty(val) => boolean` |
| | `isAllEmpty` | 判空（含 null/undefined） | `isAllEmpty(val) => boolean` |
| **字符串** | `hideTextAtIndex` | 敏感信息隐藏 | `hideTextAtIndex(text, index, symbol?="*") → string` index 支持 `number`/`number[]`/`{start,end}`/`{start,end}[]` |
| | `hasCNChars` | 判断含中文 | `hasCNChars(value, options?) → boolean` options 含 `all`(是否全中文)、`pure`(去空格) |
| | `priceToThousands` | 金额千分位 | `priceToThousands(amount: number, options?) → string` options 含 `digit`(小数位,默认0)、`round`(四舍五入) |
| **日期** | `getCurrentDate` | 当前日期时间 | `getCurrentDate(options?) → { ymd, hms, week }` options 含 `type`(1=汉字/2=横杠/3=斜杠)、`prefix` |
| | `dateFormat` | 日期格式化 | `dateFormat(format: string) → string` 仅传格式串，如 `"YYYY-MM-DD HH:mm:ss"` |
| **颜色** | `randomColor` | 随机颜色 | `randomColor(options?) → string\|string[]` options 含 `type`("rgb"/"hex"/"hsl"，默认"rgb")、`num`(数量) |
| | `darken` / `lighten` | 颜色加深/变浅 | `(color: string, level: number) → string` color 为 hex 格式 |
| | `hexToRgb` | hex 转 rgb | `hexToRgb(str) → [r, g, b]` |
| | `rgbToHex` | rgb 转 hex | `rgbToHex(r, g, b) → string` |
| **DOM** | `downloadByData` | Blob 数据下载 | `downloadByData(data: BlobPart, filename, mime?, bom?) → void` |
| | `downloadByOnlineUrl` | 在线 URL 下载 | `downloadByOnlineUrl(url, filename, mime?, bom?) → void` |
| | `downloadByBase64` | Base64 下载 | `downloadByBase64(buf: string, filename, mime?, bom?) → void` |
| **其他** | `debounce` | 防抖 | `debounce(fn, timeout?=200, immediate?=false) → () => void` |
| | `throttle` | 节流 | `throttle(fn, timeout?=1000) → () => void` |
| | `storageLocal` | localStorage 封装 | `storageLocal() → { setItem\<T\>, getItem\<T\>, removeItem, clear }` |
| | `storageSession` | sessionStorage 封装 | 同 `storageLocal` 接口 |
| | `deviceDetection` | 设备检测 | `deviceDetection() → boolean` true=移动端，false=PC |
| | `delay` | 延时等待 | `delay(timeout?=20) → Promise` |
| | `buildUUID` | 32 位 UUID（无横杠） | `buildUUID() → string` |
| | `buildGUID` | 36 位 GUID（带横杠） | `buildGUID() → string` |
| | `openLink` | 新窗口打开链接 | `openLink(href, target?="_blank") → void` |

---

## 5. 开发环境

### 5.1 环境要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.13 | 后端运行时 |
| uv | latest | Python 包管理 |
| Node.js | ≥ 20.19 | 前端运行时 |
| bun | ≥ 1.3.0 | 前端包管理 |
| Docker | latest | 容器化部署（可选） |
| Git | latest | 版本控制 |

### 5.2 本地启动

**后端**：

```bash
cd backend
cp ../.env.example ../.env    # 编辑 .env 配置数据库等
uv sync
uv run python main.py         # 监听 http://localhost:7001
```

**前端**：

```bash
cd frontend
bun install
bun dev                       # 监听 http://localhost:7000
```

开发模式下前端 `/api` 请求自动代理到后端（Vite proxy 配置在 `vite.config.ts`）。

**一键启动**（推荐）：

```bash
./scripts/start.sh dev    # 开发模式：SQLite + 内存 Redis
./scripts/start.sh prod   # 生产模式：PostgreSQL + 真实 Redis
```

### 5.3 常用命令

```bash
# 后端
cd backend && uv run pytest          # 测试
cd backend && uv run pylint app/     # 代码检查

# 前端
cd frontend && bun run typecheck     # TS + Vue 类型检查
cd frontend && bun run lint          # ESLint + Prettier + Stylelint
cd frontend && bun run build         # 生产构建
```

---

## 6. 数据库

### 6.1 支持的数据库

| 模式 | 配置 | 说明 |
|------|------|------|
| SQLite | `DB_SCHEME=sqlite` | 默认，零配置，适合开发和轻量部署 |
| PostgreSQL | `DB_SCHEME=postgresql` | 生产推荐，需配置 `DB_SERVER`/`DB_PORT`/`DB_USER`/`DB_PASSWORD` |

连接字符串由 `app/settings/database.py` 的 `db_engine()` 根据配置自动生成。

### 6.2 数据库初始化

启动时 `init_data()` 自动执行：

1. `SQLModel.metadata.create_all(engine)` — 创建所有表
2. 种子数据：默认部门、菜单
3. 创建默认管理员（如不存在）
4. 创建默认安全策略（如不存在）
5. 同步 API 路由到数据库（`_sync_api_routes`）
6. 启动定时任务（订单过期检查）

---

## 7. 部署

### 7.1 Docker 部署（推荐）

```bash
docker compose up -d
```

- 前端：`http://localhost:80`（Nginx 服务）
- 后端 API：`http://localhost:7001`
- PostgreSQL 和 Redis 默认不启动（需取消 `profiles` 注释或使用 `--profile postgres`）

### 7.2 Docker 多阶段构建

`Dockerfile` 分四个阶段：

1. **frontend-builder**：Node + Bun 构建前端
2. **frontend**：Nginx 托管前端静态文件
3. **backend**：Python + uv 安装后端依赖
4. **最终镜像**：Python + Nginx，前后端合并

### 7.3 Nginx 配置要点

- `/` → 前端 SPA（`try_files $uri $uri/ /index.html`）
- `/api/` → 代理到 `http://localhost:7001/api/`
- 安全头：X-Frame-Options、X-Content-Type-Options、X-XSS-Protection
- 静态资源长缓存（1 年）

---

## 8. 功能模块清单

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

---

## 9. 关键约定与模式

### 9.1 后端约定

1. **API 路由风格**：RESTful 风格，使用 POST 传查询条件 + GET 参数分页
2. **响应格式**：统一使用 `Success`/`Fail`/`SuccessExtra` 包装响应
3. **认证依赖**：所有需认证的接口使用 `DependPermission` 或 `DependUser`
4. **Controller 模式**：业务逻辑放在 `controllers/`，不在路由函数中直接写
5. **模型定义**：SQLModel 同时作为 ORM 模型和 Pydantic Schema，使用 `*Create`/`*Update` 变体做输入校验
6. **UUID 主键**：所有模型使用 UUID4 作为主键
7. **配置双轨**：环境变量（只读）+ INI 文件（运行时可改）
8. **日志**：使用 Loguru，登录/操作/系统日志写入数据库
9. **慎用 try/except**：非必要不使用 try 语句，优先通过完整的条件判断、类型检查、默认值处理等方式保证代码健壮性，而非依赖异常捕获来控制流程

### 9.2 前端约定

1. **Composition API**：全部使用 `<script setup>` + TypeScript
2. **页面 Hook 模式**：页面逻辑抽取到 `utils/hook.tsx`，返回响应式数据和方法
3. **API 封装**：所有 API 调用封装在 `src/api/` 下，不在组件中直接调用 Axios
4. **类型安全**：API 响应使用 `Result`/`ResultTable` 等泛型类型
5. **国际化**：菜单标题使用 i18n 键名（如 `menus.pureUser`），通过 `transformI18n` 自动翻译
6. **组件命名**：`Re*` 前缀为公共组件（如 `ReDialog`、`ReIcon`），业务页面优先复用，禁止重复实现
7. **状态管理**：Pinia，Store 定义在 `src/store/modules/` 下
8. **慎用 try/catch**：非必要不使用 try 语句，优先通过完整的条件判断、可选链（`?.`）、空值合并（`??`）、类型守卫等方式保证代码健壮性，而非依赖异常捕获来控制流程
9. **样式零自定义原则**：业务页面 `<style scoped>` 应为空，优先使用 Tailwind 工具类（`flex-c`/`flex-bc`/`bg-bg_color`/`text-primary` 等）、Element Plus 辅助类（`.pure-popper`/`.pure-scrollbar`/`.reset-margin`）、全局 CSS 变量（`var(--pure-border-color)` 等），严禁在业务页面写自定义 CSS
10. **参考 pure-admin 文档**：开发前端功能时，务必先查阅 [pure-admin 官方文档](https://github.com/pure-admin/pure-admin-doc)，了解框架已提供的组件、Hooks、工具函数，不要重新造轮子
11. **UI 设计参考 `ui-ux-pro-max` Skill**：涉及页面布局、交互设计、组件选型等 UI/UX 决策时，应加载 `ui-ux-pro-max` Skill 获取设计规范和最佳实践指导

### 9.3 分支策略

- 每个功能基于 `main` 创建独立分支（如 `feat/notice`、`feat/security`）
- 完成后提 PR → review → squash merge 回 `main`
- 当前分支：`feat/general-settings`

---

## 10. 环境变量速查

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENVIRONMENT` | `local` | 运行模式：local/staging/production |
| `HOST` | `0.0.0.0` | 后端监听地址 |
| `PORT` | `7001` | 后端端口 |
| `SECRET_KEY` | 自动生成 | JWT 签名密钥 |
| `DB_SCHEME` | `sqlite` | 数据库类型 |
| `DB_SERVER` | `localhost` | 数据库主机 |
| `DB_PORT` | `5432` | 数据库端口 |
| `DB_USER` | - | 数据库用户 |
| `DB_PASSWORD` | - | 数据库密码 |
| `DB_PATH` | `zgadmin.sqlite` | 数据库名/文件路径 |
| `REDIS_URL` | 空 | Redis URL（空=dev 用内存） |
| `FRONTEND_HOST` | `http://localhost:7000` | 前端地址 |
| `FIRST_SUPERUSER` | `admin` | 初始管理员用户名 |
| `FIRST_SUPERUSER_PASSWORD` | `admin123456` | 初始管理员密码 |
| `FEATURE_QQ_LOGIN` | `False` | QQ 登录功能开关 |
| `FEATURE_WECHAT_LOGIN` | `False` | 微信登录功能开关 |
| `FEATURE_EMAIL` | `False` | 邮件功能开关 |
| `FEATURE_MONITOR_LOG` | `True` | 监控日志功能开关 |
| `QQ_APP_ID` | 空 | QQ 登录 AppID |
| `QQ_APP_KEY` | 空 | QQ 登录 AppKey |
| `VITE_PORT` | `7000` | 前端开发端口 |

---

## 11. 常见操作速查

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

---

## 12. 测试

后端测试位于 `backend/tests/`，使用 pytest：

```bash
cd backend
uv run pytest                 # 运行所有测试
uv run pytest -v              # 详细输出
uv run pytest tests/test_models.py  # 运行指定测试文件
```

---

## 13. 安全注意事项

- 生产环境必须修改 `SECRET_KEY` 和 `FIRST_SUPERUSER_PASSWORD`
- CORS 配置仅允许可信域名
- 所有需认证的 API 使用 `DependPermission`
- 密码使用 bcrypt 哈希存储
- JWT Token 设置合理过期时间
- RateLimiter 基于 Redis 滑动窗口
- 验证码使用服务端生成（非前端 Canvas）
- 敏感操作需二次确认 + 操作日志

---

*本文档由 AI Agent 维护，应随项目演进同步更新。*
