# 后端知识库

**生成时间:** 2026-05-05 | **提交:** 85fef5b | **分支:** feat/youhua

**PyTool 后端** — Python 3.13+ / FastAPI / SQLModel / PostgreSQL

## 目录结构
```
backend/
├── main.py              # uvicorn 入口
├── app/
│   ├── __init__.py      # FastAPI 应用工厂 (create_app)
│   ├── api/v1/          # API 路由（base、monitor、pay、settings、system）
│   ├── controllers/     # 路由处理函数（user、role、menu、dept、logs）
│   ├── core/            # 数据库、通用 CRUD、中间件、异常、定时任务、后台任务
│   ├── models/          # SQLModel/Pydantic 模型
│   ├── settings/        # Pydantic-settings + .ini 配置
│   └── utils/           # JWT、邮件、密码、IP、支付
├── tests/               # pytest 测试（conftest.py + test_*.py）
├── pyproject.toml       # 依赖 + 工具配置
└── uv.lock              # 锁定文件
```

## 从哪找
| 任务 | 位置 | 备注 |
|------|------|------|
| 应用工厂 | `app/__init__.py` | `create_app()` — 中间件、路由、异常 |
| 路由注册 | `app/core/init.py` | `register_routers()`、`register_exceptions()` |
| API 接口 | `app/api/v1/` | `__init__.py` 聚合各子路由 |
| 数据库访问 | `app/core/database.py` | SQLModel session + init_data |
| 通用 CRUD | `app/core/crud.py` | 基础 CRUD 类 |
| 认证/JWT | `app/utils/jwtt.py` | JWT 令牌工具 |
| 后台任务 | `app/core/bgtask.py` | 后台任务执行器 |
| 定时任务 | `app/core/schedule.py` | APScheduler 集成 |
| 配置 | `app/settings/__init__.py` | Pydantic `BaseSettings` |
| 运行时配置 | `app/settings/config.py` | INI 文件读写（pay.ini、base.ini） |
| 测试 | `tests/` | `conftest.py` 设置测试夹具 |

## 约定
- **SQLModel** 做 ORM — 融合 SQLAlchemy 表定义 + Pydantic 校验
- **通过 psycopg 执行原生 SQL** 处理复杂查询（与 SQLModel 并存）
- **生命周期上下文** (`lifespan_context`) 处理启动流程：`init_data()` 初始化数据库
- **自定义异常**: `SettingNotFound`、`HTTPException`、`IntegrityError`、`RequestValidationError`、`ResponseValidationError`
- **路由标签** 用作唯一 ID 前缀：`custom_generate_unique_id()` = `{tag}-{name}`
- **控制器与 API 组对应**：user → `controllers/user.py`，role → `controllers/role.py`

## 测试
- 框架：**pytest** + pytest-cov + pytest-asyncio
- 夹具：`tests/conftest.py` — 共享测试环境
- 文件命名：`test_*.py` 模式
- 运行：`uv run pytest` 或 `python tests/run_tests.py`

## 代码检查与格式化
- 要求 **Python ≥3.13**
- **autopep8**：最大行宽 100 字符，aggressive 模式，排除 `tests/` 和 `migrations/`
- **pylint**：最大行宽 120 字符，单文件最大 1500 行，函数最多 6 个参数
- Pylint 禁用：缺失文档字符串、公有方法太少、宽异常捕获、重复代码
- Pylint 启用：consider-using-f-string、unused-import、inconsistent-return-statements
- UV 使用腾讯镜像源：`https://mirrors.cloud.tencent.com/pypi/simple`

## 注意事项
- `pyjwt>=2.10.1`（不是 PyJWT） — 包名不常规，注意导入方式
- `emails>=0.6` 用于发送邮件（HTML + 附件）
- `wechatpayv3` 用于微信支付 v3 API 集成
- `loguru` 用于结构化日志（替代标准库 logging）
- 默认端口 7001，通过 settings 配置
