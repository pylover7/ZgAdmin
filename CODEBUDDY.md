# ZgAdmin — CodeBuddy 持久上下文

> 本文件仅包含**无法从代码本身推断**的持久上下文：常用命令、代码风格、工作流规则。
> 架构、组件库、工具函数等详细文档已拆分至 `.codebuddy/rules/` 和 `.codebuddy/skills/`。

---

## 规则总章索引

**分层原则**：个人规则跨项目通用 / 项目技术规则归项目目录 / 项目事实与教训归记忆。

| 层 | 位置 | 内容 |
|----|------|------|
| 个人规则（跨项目） | `~/.codebuddy/CODEBUDDY.md` | 核心思维与输出规范、Skill 加载机制、最高优先级铁律、AI 编程协作规则（角色 / 优先级 / 工作流程 / 禁止事项 / 自主级别） |
| 项目技术规则 | `.codebuddy/rules/*.md` | `collaboration.md`（工程标准：快速交付 / 代码标准 / 测试标准 / 安全权限 / Git / 沟通输出）、`backend-architecture.md`（含**数据模型变更铁律**）、`frontend-architecture.md`、`project-structure.md`、`security.md`、`infrastructure.md`、`pureadmin-utils-quickref.md` |
| 项目事实与教训 | `.codebuddy/memory/` | `MEMORY.md`（长期：工程方法论 / 技术教训）、`YYYY-MM-DD.md`（日志） |
| 项目 Skill | `.codebuddy/skills/` | 项目级 Skill 包 |

**协商机制摘要**（完整定义见全局个人规则）：

- 定位：AI = 资深软件工程师 + 结对程序员 + 代码审查者；用户 = 关键决策者、验收者、最终责任人
- 自主级别：默认 **L2**（先给计划、等确认）；触碰关键决策清单（架构 / schema / 公共 API / 鉴权 / 支付 / 依赖引入 / 大重构 / 部署配置）强制降 **L1**
- 小任务客观判据（须全满足，否则降级大任务）：① 文件数 ≤ 2；② 不触碰 `app/models/` 字段定义、不修改已注册路由函数签名；③ 属关键决策清单之外；④ 验证命令 < 3 分钟且无需人工构造测试数据
- **必须落实**：验证命令必跑（lint / typecheck / test / build）；交付五项（变更摘要 / 文件列表 / 验证命令及结果 / 未验证部分与风险 / 下一步或待确认）
- **项目记忆优先**：分析任务前先阅读 `.codebuddy/memory/` 下记忆，理解此前工作与经验教训

---

## 常用命令

### 启动

```bash
# 后端（端口 7001）
cd backend && uv sync && uv run python main.py

# 前端（端口 7000）
cd frontend && bun install && bun dev

# 一键启动
./scripts/start.sh dev    # 开发模式：SQLite + 内存 Redis
./scripts/start.sh prod   # 生产模式：PostgreSQL + 真实 Redis
```

### 测试 & 检查

```bash
cd backend && uv run pytest                # 后端测试
cd backend && uv run ruff check app/        # 后端 lint
cd backend && uv run ruff format app/        # 后端格式化
cd frontend && bun run typecheck            # 前端类型检查
cd frontend && bun run lint                # 前端 lint
cd frontend && bun run build                # 前端构建
```

### 数据库迁移

```bash
cd backend
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
uv run alembic downgrade -1
```

---

## 代码风格

### 后端（9 条）

1. **API 路由风格**：RESTful 风格，使用 POST 传查询条件 + GET 参数分页
2. **响应格式**：统一使用 `Success`/`Fail`/`SuccessExtra`/`FailAuth` 包装响应
3. **认证依赖**：按场景选择 `DependPermission` / `DependAuth` / `DependUser` / `DependRateLimit`
4. **Controller 模式**：业务逻辑放在 `controllers/`，不在路由函数中直接写；支持 `CRUDBase`（多行 CRUD）和 `ConfigController`（单行配置表）两种模式
5. **模型定义**：SQLModel 同时作为 ORM 模型和 Pydantic Schema，使用 `*Create`/`*Update` 变体做输入校验
6. **UUID 主键**：所有模型使用 UUID4 作为主键
7. **配置管理**：环境变量（`.env` + `pydantic-settings`）+ 数据库配置表（`SiteConfig`/`OAuthConfig`/`EmailConfig`/`SecurityPolicy`，运行时可改）
8. **日志**：使用 Loguru，登录/操作/系统日志写入数据库
9. **慎用 try/except**：非必要不使用 try 语句，优先通过完整的条件判断、类型检查、默认值处理等方式保证代码健壮性，而非依赖异常捕获来控制流程

### 前端（11 条）

1. **Composition API**：全部使用 `<script setup>` + TypeScript
2. **页面 Hook 模式**：页面逻辑抽取到 `utils/hook.tsx`，返回响应式数据和方法
3. **API 封装**：所有 API 调用封装在 `src/api/` 下，不在组件中直接调用 Axios
4. **类型安全**：API 响应使用 `Result`/`ResultTable` 等泛型类型
5. **国际化**：菜单标题使用 i18n 键名（如 `menus.pureUser`），通过 `transformI18n` 自动翻译
6. **组件选型优先级**：开发前端功能时，必须按以下顺序选型——① pure-admin 体系复用组件/工具（Re* 组件、`@pureadmin/table`、`@pureadmin/descriptions`、`@pureadmin/utils`、自定义指令、预集成第三方库） → ② Element Plus 组件 → ③ 自行实现。`Re*` 前缀为公共组件（如 `ReDialog`、`ReIcon`），业务页面优先复用，禁止重复实现
7. **状态管理**：Pinia，Store 定义在 `src/store/modules/` 下
8. **慎用 try/catch**：非必要不使用 try 语句，优先通过完整的条件判断、可选链（`?.`）、空值合并（`??`）、类型守卫等方式保证代码健壮性，而非依赖异常捕获来控制流程
9. **样式零自定义原则**：业务页面 `<style scoped>` 应为空，优先使用 Tailwind 工具类（`flex-c`/`flex-bc`/`bg-bg_color`/`text-primary` 等）、Element Plus 辅助类（`.pure-popper`/`.pure-scrollbar`/`.reset-margin`）、全局 CSS 变量（`var(--pure-border-color)` 等），严禁在业务页面写自定义 CSS
10. **参考 pure-admin 文档**：开发前端功能时，务必先查阅 [pure-admin 官方文档](https://github.com/pure-admin/pure-admin-doc)，了解框架已提供的组件、Hooks、工具函数，不要重新造轮子
11. **UI 设计参考 `ui-ux-pro-max` Skill**：涉及页面布局、交互设计、组件选型等 UI/UX 决策时，应加载 `ui-ux-pro-max` Skill 获取设计规范和最佳实践指导

---

## 工作流规则

### 分支策略

- 每个功能基于 `main` 创建独立分支（如 `feat/notice`、`feat/security`）
- 完成后提 PR → review → squash merge 回 `main`

### 添加新后端 API 模块

1. 在 `app/models/` 创建数据模型（**每个字段必须有消费方**——自问「这个字段谁写？谁读？」；纯预留字段须在 `description` 标注「预留」+ 预期场景）
2. 在 `app/controllers/` 创建 Controller（继承 `CRUDBase`）
3. 在 `app/api/v1/` 创建路由文件
4. 在 `app/api/v1/__init__.py` 注册路由到 `v1_router`
5. **生成迁移脚本 → 打开确认 `upgrade()` 非空 → 手动执行验证 → 跑往返测试**（四步缺一不可）
6. 启动后 `_sync_api_routes` 自动将新路由同步到数据库

> **改任何数据模型字段都必须走第 5 步**。完整铁律与「步骤 0 前置校验」见 `.codebuddy/rules/backend-architecture.md`「数据模型变更铁律」。
>
> ⚠️ **本项目 `init_data` 当前使用 `create_all` + `stamp(head)`**，迁移脚本从未在空库上被真正执行过——这意味着**新字段在老库上不会被自动添加，且没有任何自愈兜底**。该问题与改造待办见上述规则文件的「现状与待办」。

### 添加新前端页面

1. 在 `src/views/` 创建页面目录和组件
2. 在 `src/api/` 创建 API 封装
3. 在 `backend/app/seed/data/menus.py` 添加菜单项（使用 i18n 键名）
4. 在 `locales/zh-CN.yaml` 和 `locales/en.yaml` 添加翻译
5. 后端重启后菜单自动同步到前端
