# PyTool

管理平台模板 — Python/FastAPI 后端 + Vue 3/TypeScript 前端，Docker 一键部署。

- 🔐 **完善的权限体系** — 用户/角色/菜单/部门多级权限，支持 JWT 鉴权
- 🔑 **多种登录方式** — 账号密码、QQ 登录、微信登录
- 📊 **实时系统监控** — 在线用户、登录日志、操作日志全方位追踪
- 🌍 **国际化支持** — 中文 / English 无缝切换
- 🐳 **一键部署** — Docker 多阶段构建，SQLite 零配置即用

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.13+ / FastAPI / SQLModel / PostgreSQL |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Tailwind CSS 4 |
| 部署 | Docker 多阶段构建 + nginx 反向代理 |

## 功能

- **用户管理** — 用户/角色/菜单/部门 CRUD，权限控制
- **登录认证** — 账号密码登录、QQ 登录、微信登录，JWT 鉴权
- **系统监控** — 登录日志、操作日志、系统日志，支持条件筛选与批量删除
- **系统设置** — 登录方式配置（QQ/微信 AppID 等）
- **国际化** — 中文 / English 切换

## 本地开发

### 环境要求

- Python ≥ 3.13 + [uv](https://docs.astral.sh/uv/)
- Node ≥ 20.19 + [bun](https://bun.sh/)

### 启动后端

```bash
cd backend
cp ../.env.example ../.env    # 编辑 .env 配置数据库等
uv sync
uv run python main.py         # 监听 http://localhost:7001
```

### 启动前端

```bash
cd frontend
bun install
bun dev                       # 监听 http://localhost:7000
```

开发模式下前端 `/api` 请求自动代理到后端。

### 常用命令

```bash
# 后端
cd backend && uv run pytest          # 测试
cd backend && uv run pylint app/     # 代码检查

# 前端
cd frontend && bun run typecheck     # TS + Vue 类型检查
cd frontend && bun run lint          # ESLint + Prettier + Stylelint
```

### 数据迁移

```bash
cd backend

# 生成迁移脚本（根据模型变更自动检测）
uv run alembic revision --autogenerate -m "add xxx column"

# 执行迁移到最新版本
uv run alembic upgrade head

# 回退一个版本
uv run alembic downgrade -1

# 查看当前迁移状态
uv run alembic current

# 查看迁移历史
uv run alembic history

# 生成 SQL 而不执行（离线模式）
uv run alembic upgrade head --sql
```

## Docker 部署

### 拉取镜像

```bash
docker pull docker.cnb.cool/pylover/pytool
```

### Docker Compose（推荐）

```bash
docker compose up -d
```

访问：
- 前端：http://localhost:80
- 后端 API：http://localhost:7001

```bash
docker compose down          # 停止
docker compose logs -f       # 查看日志
```

### 直接运行容器

```bash
docker run -d \
  --name pytool-app \
  -p 80:80 \
  -p 7001:7001 \
  docker.cnb.cool/pylover/pytool
```

## 配置

### 环境变量（`.env`）

```env
# 数据库
DB_SCHEME=postgresql
DB_SERVER=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password

# QQ 登录（可选）
QQ_APP_ID=your_qq_app_id
QQ_APP_KEY=your_qq_app_key
QQ_REDIRECT_URI=http://localhost:7000/login/qq/callback
```

QQ/微信登录也可通过系统设置 → 登录设置页面在线配置，无需重启。

### 默认管理员

- 用户名：`admin`
- 密码：`admin123456`

## 项目结构

```
├── backend/          # FastAPI 后端（端口 7001）
│   ├── app/api/v1/   # API 路由
│   ├── app/models/   # SQLModel 数据模型
│   ├── app/settings/ # 配置（Pydantic + INI）
│   └── app/utils/    # JWT、密码、QQ/微信 OAuth
├── frontend/         # Vue 3 前端（端口 80）
│   ├── src/views/    # 页面（登录、系统管理、监控、设置）
│   ├── src/api/      # API 调用封装
│   └── locales/      # 国际化文案
├── docs/             # VitePress 文档站点
├── Dockerfile        # 多阶段构建
├── nginx.conf        # 前端代理 /api → 后端
└── docker-compose.yml
```
