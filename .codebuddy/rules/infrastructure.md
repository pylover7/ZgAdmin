# 基础设施

## 环境要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.13 | 后端运行时 |
| uv | latest | Python 包管理 |
| Node.js | ≥ 20.19 | 前端运行时 |
| bun | ≥ 1.3.0 | 前端包管理 |
| Docker | latest | 容器化部署（可选） |
| Git | latest | 版本控制 |

## 本地启动

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

## 数据库

### 支持的数据库

| 模式 | 配置 | 说明 |
|------|------|------|
| SQLite | `DB_SCHEME=sqlite` | 默认，零配置，适合开发和轻量部署 |
| PostgreSQL | `DB_SCHEME=postgresql` | 生产推荐，需配置 `DB_SERVER`/`DB_PORT`/`DB_USER`/`DB_PASSWORD` |

连接字符串由 `app/settings/database.py` 的 `db_engine()` 根据配置自动生成。

### 数据库初始化

启动时 `init_data()` 自动执行：

1. `SQLModel.metadata.create_all(engine)` — 创建所有表
2. 种子数据：默认部门、菜单
3. 创建默认管理员（如不存在）
4. 创建默认安全策略（如不存在）
5. 同步 API 路由到数据库（`_sync_api_routes`）
6. 启动定时任务（订单过期检查）

## Docker 部署

```bash
docker compose up -d
```

- 前端：`http://localhost:80`（Nginx 服务）
- 后端 API：`http://localhost:7001`
- PostgreSQL 和 Redis 默认不启动（需取消 `profiles` 注释或使用 `--profile postgres`）

### Docker 多阶段构建

`Dockerfile` 分四个阶段：

1. **frontend-builder**：Node + Bun 构建前端
2. **frontend**：Nginx 托管前端静态文件
3. **backend**：Python + uv 安装后端依赖
4. **最终镜像**：Python + Nginx，前后端合并

### Nginx 配置要点

- `/` → 前端 SPA（`try_files $uri $uri/ /index.html`）
- `/api/` → 代理到 `http://localhost:7001/api/`
- 安全头：X-Frame-Options、X-Content-Type-Options、X-XSS-Protection
- 静态资源长缓存（1 年）

## 环境变量速查

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENVIRONMENT` | `local` | 运行模式：local/staging/production |
| `HOST` | `0.0.0.0` | 后端监听地址 |
| `PORT` | `7001` | 后端端口 |
| `SECRET_KEY` | 自动生成 | JWT 签名密钥 |
| `DB_SCHEME` | `sqlite` | 数据库类型 |
| `DB_SERVER` | `localhost` | 数据库主机 |
| `DB_PORT` | `5432` | 数据库端口 |
| `DB_USER` | — | 数据库用户 |
| `DB_PASSWORD` | — | 数据库密码 |
| `DB_PATH` | `zgadmin.sqlite` | 数据库名/文件路径 |
| `REDIS_URL` | 空 | Redis URL（空=dev 用内存） |
| `FRONTEND_HOST` | `http://localhost:7000` | 前端地址 |
| `FIRST_SUPERUSER` | `admin` | 初始管理员用户名 |
| `FEATURE_QQ_LOGIN` | `False` | QQ 登录功能开关 |
| `FEATURE_WECHAT_LOGIN` | `False` | 微信登录功能开关 |
| `FEATURE_EMAIL` | `False` | 邮件功能开关 |
| `FEATURE_MONITOR_LOG` | `True` | 监控日志功能开关 |
| `QQ_APP_ID` | 空 | QQ 登录 AppID |
| `QQ_APP_KEY` | 空 | QQ 登录 AppKey |
| `QQ_REDIRECT_URI` | `http://localhost:7000/login/qq/callback` | QQ 登录回调地址 |
| `RELOAD` | `False` | 后端热重载开关 |
| `DEBUG` | `False` | 调试模式 |
| `MAX_UPLOAD_SIZE` | `104857600` | 最大上传文件大小（字节，默认 100MB） |
| `SENTRY_DSN` | 空 | Sentry DSN（错误追踪） |
| `SMTP_HOST` | 空 | SMTP 服务器地址 |
| `SMTP_PORT` | `587` | SMTP 端口 |
| `SMTP_USER` | 空 | SMTP 用户名 |
| `SMTP_PASSWORD` | 空 | SMTP 密码 |
| `SMTP_TLS` | `True` | SMTP 使用 TLS |
| `SMTP_SSL` | `False` | SMTP 使用 SSL |
| `EMAILS_FROM_EMAIL` | 空 | 发件人地址 |
| `EMAILS_FROM_NAME` | 项目名 | 发件人名称 |
| `VITE_PORT` | `7000` | 前端开发端口 |
