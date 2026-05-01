# PyTool 知识库

**生成时间:** 2026-05-01 | **提交:** 54cbb43 | **分支:** feat/qqLogin

## 概述
PyTool — 全栈管理平台。Python/FastAPI 后端 + Vue 3/TypeScript 前端，Docker 部署。

## 目录结构
```
./
├── backend/           # Python FastAPI 后端（端口 7001）
├── frontend/          # Vue 3 + Vite + Element Plus 前端（端口 80）
├── docs/              # VitePress 文档站点
├── scripts/           # 构建/检查脚本
├── Dockerfile         # 多阶段构建：node build → nginx + python:3.13-slim
├── docker-compose.yml # 单服务：pytool-app
├── nginx.conf         # 前端代理，/api → 后端
└── .cnb.yml           # CNB CI：推送同步到 GitHub，PR 触发 TCA 代码扫描
```

## 从哪找
| 任务 | 位置 | 备注 |
|------|------|------|
| 后端 API 路由 | `backend/app/api/v1/` | 版本化，挂载在 `/api/v1/` |
| 前端页面 | `frontend/src/views/` | 登录、系统管理、监控、设置 |
| 前端可复用组件 | `frontend/src/components/` | `Re*` 前缀命名规范 |
| 共享类型 | `frontend/src/types/` | 全局 TS 类型别名 |
| 国际化文案 | `frontend/locales/` | en.yaml、zh-CN.yaml |
| CI/CD 流水线 | `.cnb.yml` | CNB 云原生构建 |
| Docker 入口 | `Dockerfile` | 多阶段：前端 → nginx，后端 → python |
| 后端配置 | `backend/app/settings/` | Pydantic-settings + .ini 配置文件 |
| 平台运行时配置 | `frontend/public/platform-config.json` | 应用启动时加载 |

## 约定
- **行宽**: 后端 100-120 (autopep8/pylint)，前端 2 空格缩进 (`.editorconfig`)
- **提交检查**: Conventional Commits，使用 commitlint (`@commitlint/config-conventional`)
- **Pre-commit 钩子**: Husky + lint-staged (ESLint、Prettier、Stylelint)
- **组件命名**: 可复用组件使用 `Re` 前缀 (`ReDialog`、`ReAuth`、`ReIcon`)
- **Python**: 开启类型注解，无需 `from __future__ import annotations`（Python 3.13+）
- **Vue**: 组合式 API (`<script setup lang="ts">`)，强制自闭合标签
- **导入路径**: `@/*` → `frontend/src/*`，`@build/*` → `frontend/build/*`

## 本项目禁止项（反模式）
- 不要在 `tsconfig.json` 中设 `strict: true` — `strictFunctionTypes: false`，`noImplicitAny: false`
- 不要用 `ban-ts-comment` 规则 — `@typescript-eslint/ban-ts-comment: off`
- 不要用 `no-explicit-any` 规则 — `@typescript-eslint/no-explicit-any: off`
- Python pylint：禁用 `C0114`、`C0115`（缺失文档字符串检查）
- Python pylint：禁用 `W1203`（日志中不用 f-string）
- autopep8 忽略 `E226,E24,E501,W503`

## 独特风格
- 后端使用 SQLModel（SQLAlchemy + Pydantic 融合），复杂查询直接用 `psycopg` 执行原生 SQL
- 自定义异常处理：所有异常在 `app.core.init.register_exceptions()` 中注册
- 前端使用 Vue Reactivity Transform (`$ref`、`$computed`、`$shallowRef`) — 在 ESLint 中声明为全局变量
- 前端将平台配置存在 `platform-config.json`，`app.mount()` 之前异步加载
- 多标签页导航，Pinia store 管理 (`multiTags`) — 保持已打开页签的状态
- 本地开发使用 `vite-plugin-fake-server` 提供 Mock 服务

## 常用命令
```bash
# 后端
cd backend && uv sync && uv run python main.py       # 开发服务器
cd backend && uv run pytest                           # 测试
cd backend && uv run pylint app/                      # 代码检查
cd backend && uv run autopep8 -r app/                 # 格式化

# 前端
cd frontend && bun install && bun dev                 # 开发服务器
cd frontend && bun run build                          # 生产构建
cd frontend && bun run typecheck                      # TS + Vue 类型检查
cd frontend && bun run lint                           # ESLint + Prettier + Stylelint

# 文档
cd docs && bun run docs:dev                           # VitePress 开发

# Docker
docker compose up -d                                  # 生产环境启动
docker build -t pytool .                              # 构建镜像
```

## 注意事项
- 后端要求 Python ≥3.13（使用 `uv` 管理包）
- 前端使用 `bun` 作为包管理器（非 npm/yarn），Node ≥20.19
- 代理：Vite 开发时将 `/api` 代理到 `BACKEND_URL`；生产环境由 nginx 处理
- 当 `SENTRY_DSN` 设置且 `ENVIRONMENT != "local"` 时启用 Sentry SDK
- CNB 在推送到 main 时自动同步到 GitHub；PR 到 main/dev 分支时触发 TCA 代码分析
