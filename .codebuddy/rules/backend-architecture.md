# 后端架构（Backend）

> 后端开发时，请先加载 `backend-patterns` Skill 获取完整编码规范和架构文档。
> 详细架构说明见 `.codebuddy/skills/backend-patterns/references/architecture.md`。

## 后端编码规范速查

1. **API 路由风格**：RESTful 风格，使用 POST 传查询条件 + GET 参数分页
2. **响应格式**：统一使用 `Success`/`Fail`/`SuccessExtra`/`FailAuth` 包装响应
3. **认证依赖**：按场景选择 `DependPermission` / `DependAuth` / `DependUser` / `DependRateLimit`
4. **Controller 模式**：业务逻辑放在 `controllers/`，不在路由函数中直接写；支持 `CRUDBase`（多行 CRUD）和 `ConfigController`（单行配置表）两种模式
5. **模型定义**：SQLModel 同时作为 ORM 模型和 Pydantic Schema，使用 `*Create`/`*Update` 变体做输入校验
6. **UUID 主键**：所有模型使用 UUID4 作为主键
7. **配置管理**：环境变量（`.env` + `pydantic-settings`）+ 数据库配置表（`SiteConfig`/`OAuthConfig`/`EmailConfig`/`SecurityPolicy`，运行时可改）
8. **日志**：使用 Loguru，登录/操作/系统日志写入数据库
9. **慎用 try/except**：非必要不使用 try 语句，优先通过完整的条件判断、类型检查、默认值处理等方式保证代码健壮性，而非依赖异常捕获控制流程
10. **慎用 noqa**：新增 `# noqa` 注释需要获得用户显式授权，原则上不允许使用。noqa 属于「绕过手段」，与 try/except / `@ts-ignore` / `eslint-disable` 同类。lint 报错是信号不是麻烦，应理解真实问题后通过重构解决
11. **Session 生命周期**：`DatabaseSession` / `get_db` 均为 `expire_on_commit=False`，commit 不会使已加载对象属性失效；需要「commit 后读 DB 最新值」时必须显式 `session.refresh(obj)`
12. **模型字段必须有消费方**：新增字段必须至少有一个写入方**或**一个读取方。自问「这个字段谁写？谁读？」——两个都答不上来就是死字段。确需预留的字段必须在 `description` 中标注「预留」并写明预期消费场景，否则不得合入。
    - **该判据跨越前后端**：后端字段增删时，`src/api/` 下对应的 `interface` 必须同步——前端 TS 可选字段不报错、零成本存在，比后端字段更难被发现。
    - **成组字段必须逐个验证，不能以「同组其他字段在用」代替**：部分正确的证据链会掩盖缺失的那一环，比孤立死字段更隐蔽。

## 添加新后端 API 模块

1. 在 `app/models/` 创建数据模型（字段须满足上方第 12 条）
2. 在 `app/controllers/` 创建 Controller（继承 `CRUDBase`）
3. 在 `app/api/v1/` 创建路由文件
4. 在 `app/api/v1/__init__.py` 注册路由到 `v1_router`
5. **按下方「数据模型变更铁律」处理迁移**
6. 启动后 `_sync_api_routes` 自动将新路由同步到数据库

## 数据模型变更铁律（⚠️ 本项目当前为**违规状态**，见下方「现状与待办」）

> **背景**：本项目 `init_data()` 当前使用 `SQLModel.metadata.create_all(engine)` 建表，随后 `command.stamp(cfg, "head")` 把版本号直接标记为 head。
> 该机制意味着：**迁移脚本从未在空库上被验证过**——它只被写入过，但从未真正执行过。
> 参考项目 MineAdmin 曾因同一机制导致迁移链「从未在空库跑通」（缺 8 张表建表语句 + 5 个 `upgrade()` 为空的空迁移），本项目存在同样风险。

1. **改数据模型必须生成迁移脚本**：修改 `app/models/` 下任何字段定义（增/删/改列、改类型、改约束）后，**必须**执行 `alembic revision --autogenerate -m "描述"`，不得只改模型了事。
2. **必须打开文件确认 `upgrade()` 非空**：若当前库的表是「非迁移方式」（即 `create_all`）建出的，autogenerate 会因看不到差异而生成**空迁移**——这正是下述「现状」的直接后果。生成后必须打开文件确认。
3. **必须手动执行迁移验证（AI 亲自跑，不可只跑测试）**：`uv run alembic upgrade head`，亲身确认无报错。失败则**改脚本**，不要改测试或加守卫绕过。
   - **报告时必须附上手动执行的命令与输出摘要**（执行结果、步数、最终 revision）。本条约束力完全来自「输出可检查」——不附输出等于未执行。
   - 理由：测试用临时空库，与用户的真实库本质不同（有数据 vs 零数据；起点是上一版本产物 vs 空库）。**用户最真实的场景是「手上有旧版库（有数据），装了新代码，执行迁移」**，若中途失败库会停在改了一半的状态——这比测试失败严重得多，而**手动执行是发现「中途失败」的唯一手段**。
4. **验证载体固定为开发环境真实使用的库**（`DB_PATH` 指向的那个）；临时库只能作补充场景（老库带数据升级、往返），**不得用它替代「已在开发库验证」的结论**。
   - **执行前必须先做「步骤 0 前置校验」，任一条不过 → 立即中断、给出方案交用户抉择**（**禁止自行 stamp / 手工补列 / 改迁移去迁就库**）：
     - **0.1 版本号必须可信**：`alembic_version` 的值必须存在于当前迁移链中。若报 `Can't locate revision identified by 'xxxx'` → 孤儿版本号 → **中断**。
     - **0.2 结构必须与模型零差异**：逐表逐列比对（表集合 + 每张表列集合）与 `SQLModel.metadata` **必须完全一致**。**只抽查一两张表不算通过**——参考项目曾因只查 `user` 一张表就断言「结构与模型一致」，实际另有 2 张表缺列。
   - 理由：**「在开发库验证」成立的前提是该库本身可信**。库被污染时迁移跑不通**不代表迁移写错**。
   - **开发库不可信时的正解是重建**：停后端（SQLite 文件被占用）→ 备份 → 删库 → 启动后端走完整迁移链 → 重走 `/init` 向导。**判断库是否可信的标准是「它由迁移链生成」而非「它能正常启动」**（后者可能只是被补列掩盖）。
5. **必须做往返迁移测试 + 老库升级测试**：覆盖四类场景（缺一即不可信）——迁移链**单头**、**空库 `upgrade head`** 结构与模型一致、**往返**（`downgrade base` → `upgrade head` 后结构不变）、**老库升级**（相邻/跳版本后结构与模型一致）。
6. **迁移脚本必须双向可用**：`downgrade()` 与 `upgrade()` 必须对称；对因历史原因不适用的分支要显式注释说明。
7. **`alembic history` 的折行会产生「多头」假象**：判断分支数**必须用 `alembic heads`**，不要用 `history` 的视觉输出。
8. **SQLite 注意点**：不支持 `DROP COLUMN`，需 `batch_alter_table(...)` 重建表；加 `NOT NULL` 列需 `server_default`；`ADD COLUMN ... NOT NULL`（无 DEFAULT）**只在表已有数据时失败**（空表会成功）——写测试时表里必须先插数据才能复现。

### 现状与待办（截至本文档编写时，**未验证项已标注**）

| 项 | 现状 |
|----|------|
| `init_data` 建表方式 | `create_all(engine)` + `command.stamp(cfg, "head")`（`app/core/database.py:127` 与 `:145`） |
| `alembic/versions/` 脚本数 | 4 个 |
| 迁移往返测试 | **不存在**（无 `test_alembic_migration_roundtrip.py`） |

**待办方向**（需用户决策后执行，不要擅自开工）：

- 将 `init_data` 改为「版本检测 → alembic 执行」，移除 `create_all` 全库建表与 `stamp` 兜底；
- 补齐 `582670eaa9ea` 之后的建表语句缺口（**是否真有缺口未验证**——需实际用一个全新空库跑 `alembic upgrade head` 才能确认）；
- 新增迁移往返测试文件。

> ⚠️ **在改造完成前**：凡改模型字段，**仍必须**生成迁移脚本并手动验证，**不要以为「反正 create_all 会建表」**。当前机制下新字段在老库上不会被自动添加，**且没有任何自愈兜底**。
