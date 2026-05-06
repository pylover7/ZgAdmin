# 快速开始

5 分钟从零到运行。

## 环境要求

- Python ≥ 3.13 + [uv](https://docs.astral.sh/uv/)
- Node ≥ 20.19 + [bun](https://bun.sh/)

## 1. 克隆项目

```bash
git clone <your-repo-url> my-project
cd my-project
```

## 2. 一键启动

```bash
./scripts/start.sh
```

首次运行会自动：
- 从 `.env.example` 创建 `.env` 配置文件
- 安装前后端依赖
- 创建 SQLite 数据库和默认管理员
- 导入默认菜单和部门

## 3. 打开浏览器

| 地址 | 说明 |
|---|---|
| `http://localhost:7000` | 前端页面 |
| `http://localhost:7001/api/v1/docs` | API 文档（Swagger） |
| `http://localhost:7001/api/v1/base/health` | 健康检查 |

## 4. 登录

```
用户名: admin
密码:   admin123456
```

## 常用命令

```bash
./scripts/start.sh              # 启动前后端
./scripts/start.sh backend      # 仅后端
./scripts/start.sh frontend     # 仅前端
./scripts/start.sh sync         # 仅安装依赖
./scripts/start.sh stop         # 停止
./scripts/start.sh status       # 查看状态
```

## 下一步

- [添加新模块](/guide/add-module) — 生成第一个 CRUD
- [自定义配置](/guide/customization) — 改 Logo、主题色、菜单
