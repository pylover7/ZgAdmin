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
10. **Session 生命周期**：`DatabaseSession` / `get_db` 用的都是**裸 `Session(engine)`**，即 SQLAlchemy 默认 `expire_on_commit=True`。
    - **后果**：`commit()` 会**使该 Session 内已加载对象的属性失效**；之后访问会触发新的 SELECT，Session 已关闭时则抛 `DetachedInstanceError`。
    - **判据**：需要「commit 后继续读已加载对象」时，必须在 commit **之前**把值取出（推荐，零额外查询），或 commit 后 `session.refresh(obj)` 重新加载。
    - **`refresh()` 的边界**：它只对**仍持有 Session** 的对象有效；Session 已关闭时用不了（此时只能取出值再用）。
    - ⚠️ **不得照搬「本项目 `expire_on_commit=False`」的说法**——那是参考项目（MineAdmin）的事实（它显式传了该参数），**与 ZgAdmin 相反**。本项目的语义以本条为准。
11. **模型字段必须有消费方**：新增字段必须至少有一个写入方**或**一个读取方。自问「这个字段谁写？谁读？」——两个都答不上来就是死字段。确需预留的字段必须在 `description` 中标注「预留」并写明预期消费场景，否则不得合入。
    - **该判据跨越前后端**：后端字段增删时，`src/api/` 下对应的 `interface` 必须同步——前端 TS 可选字段不报错、零成本存在，比后端字段更难被发现。
    - **成组字段必须逐个验证，不能以「同组其他字段在用」代替**：部分正确的证据链会掩盖缺失的那一环，比孤立死字段更隐蔽。
    - **半套机制比零套更危险**：成对存在的死字段（如 `a` + `a_type` 两个都没人用）恰好证明这是「设计时预埋的完整机制」而非「漏了一个 if」——**零套会让人看出「这里没做」，半套会让人相信「这里已经做了」**。核查时不能因为「形态完整」就判定已接线，**必须逐个字段追读写链路**。
12. **慎用 noqa**：新增 `# noqa` 注释需要获得用户显式授权，原则上不允许使用。
    - **理由**：noqa 属于「**绕过手段**」，与 try/except、`@ts-ignore`、`eslint-disable`、`skip` 同类。**lint 报错是信号不是麻烦**，应在理解真实问题后通过重构代码解决，而不是把问题藏起来。
    - **拒绝经验主义**：不能因为「这里之前就有 noqa」就认为「这里该有 noqa」。
    - **本条是「向前约束」**：只约束**新增**的 noqa。存量 noqa 属既有事实，不在本条追责范围，**但也不得据此认为它们合理**。
    - **易踩的误报**：RUF100 对「规则已启用但被 noqa 抑制」的场景会误报 unused，**不能盲目 `ruff --fix` 删 noqa**。

## 添加新后端 API 模块

1. 在 `app/models/` 创建数据模型（字段须满足上方第 11 条）
2. 在 `app/controllers/` 创建 Controller（继承 `CRUDBase`）
3. 在 `app/api/v1/` 创建路由文件
4. 在 `app/api/v1/__init__.py` 注册路由到 `v1_router`
5. **按下方「数据模型变更铁律」处理迁移**
6. 启动后 `_sync_api_routes` 自动将新路由同步到数据库

## 数据模型变更铁律

> **背景**：`init_data()` 原以 `create_all` + `command.stamp` 建表；已改造为「版本检测 → alembic 执行」+ 脏库自愈。
> 改造后的机制：读 `alembic_version` 取当前版本（无表返回 `None`）→ `ScriptDirectory.get_heads()` 取 head（多头显式抛错）→ 版本不一致才 `upgrade` → 执行自愈补齐缺表/缺列。

1. **改数据模型必须生成迁移脚本**：修改 `app/models/` 下任何字段定义（增/删/改列、改类型、改约束）后，**必须**执行 `alembic revision --autogenerate -m "描述"`，不得只改模型了事。
   - `--autogenerate` 是**常规路径**（可防止人漏写字段）；**手动改脚本**是异常路径——仅当 autogenerate 产物有误或执行失败时才动手。本项目**不使用**「一律手写 revision 禁用 autogenerate」的做法。
2. **必须打开文件确认 `upgrade()` 非空**：生成后必须打开文件确认，**空迁移不得合入**（例外见下方「历史遗留的空迁移」）。
3. **必须手动执行迁移验证（AI 亲自跑，不可只跑测试）**：`uv run alembic upgrade head`，亲身确认无报错。失败则**改脚本**，不要改测试或加守卫绕过。
   - **报告时必须附上手动执行的命令与输出摘要**（执行结果、步数、最终 revision）。
   - 理由：测试用临时空库，与用户的真实库本质不同。**用户最真实的场景是「手上有旧版库（有数据），装了新代码，执行迁移」**——若这个过程中途失败，库会停在**改了一半**的状态，**这比测试失败严重得多**（用户的库没有备份）。**手动执行是发现「中途失败」的唯一手段**（测试空库跑不出这类问题）：

     | | 测试临时库 | 用户的真实库 |
     |---|---|---|
     | 数据 | **零数据** | **有数据** |
     | 起点 | 空库或 `downgrade` 产物 | 上一版本的库 |
     | 失败模式 | 断言失败 | **迁移跑一半失败，库停在中间态** |

   - ⚠️ **本条无任何自动护栏，唯一执行力来自「输出可检查」**：不像「必须生成迁移脚本」会被「空库 `upgrade head`」测试自动抓住，**「有没有手动跑过」没有任何机制能自动验证**。因此**交付迁移相关工作时必须显式列出手动执行的命令与结果摘要——不附输出即视为未执行**。把「靠自觉」变成「输出可检查」，是本条唯一可能的落实方式。
4. **验证载体固定为开发环境真实使用的库**（`settings.STATIC_PATH` 下的 `zgadmin.sqlite`，**注意 `sqlite` 分支路径硬编码、`DB_PATH` 不生效**）；临时库只能作补充场景（老库带数据升级、往返），**不得用它替代「已在开发库验证」的结论**。
   - **执行前必须先做「步骤 0 前置校验」，任一条不过 → 立即中断、给出方案交用户抉择**（**禁止自行 stamp / 手工补列 / 改迁移去迁就库**）：
     - **0.1 版本号必须可信**：`alembic_version` 的值必须存在于当前迁移链中。若报 `Can't locate revision identified by 'xxxx'` → 孤儿版本号 → **中断**。
     - **0.2 结构必须与模型零差异**：逐表逐列比对（表集合 + 每张表列集合）与 `SQLModel.metadata` **必须完全一致**。**只抽查一两张表不算通过**——参考项目曾因只查 `user` 一张表就断言「结构与模型一致」，实际另有 2 张表缺列。
   - 理由：**「在开发库验证」成立的前提是该库本身可信**。库被污染时迁移跑不通**不代表迁移写错**。
   - **开发库不可信时的正解是重建**：停后端（SQLite 文件被占用）→ 备份 → 删库 → 启动后端走完整迁移链 → 重走 `/init` 向导。**判断库是否可信的标准是「它由迁移链生成」而非「它能正常启动」**（后者可能只是被补列掩盖）。
   - ⚠️ **「开发库不存在」的结论会随任何写盘操作失效**：跑一次 `pytest` 就可能把它建出来（`create_app()` 会 `mkdir`，`init_data` 会建库）。**凡断言「某物不存在」，在跑过任何写盘命令后必须重新验证**。
5. **必须做往返迁移测试 + 老库升级测试**：回归护栏固定为 `backend/tests/test_alembic_migration_roundtrip.py`（**不得删除或跳过**）。覆盖：迁移链**单头**、**空库 `upgrade head`** 结构与模型一致、**往返**（`downgrade base` → `upgrade head`）、**老库升级**、**老库带数据升级数据保真**、**自愈三类场景**。
   - 改动迁移链 / `init_data` / 自愈逻辑后**必须跑该文件**。它不覆盖的场景（如真实库中途失败）仍需第 3 条的手动验证。
6. **迁移脚本必须双向可用**：`downgrade()` 与 `upgrade()` 必须对称；对因历史原因不适用的分支要显式注释说明。
7. **`alembic history` 的折行会产生「多头」假象**：判断分支数**必须用 `alembic heads`**，不要用 `history` 的视觉输出。
8. **SQLite 注意点**：不支持 `DROP COLUMN`，需 `batch_alter_table(...)` 重建表；加 `NOT NULL` 列需 `server_default`；`ADD COLUMN ... NOT NULL`（无 DEFAULT）**只在表已有数据时失败**（空表会成功）——写测试时表里必须先插数据才能复现。
9. **⚠️ 构造测试数据前必须先 `inspect()` 查真实 schema**：不得凭字段名推测列名与 NOT NULL 约束。实例如 `user` 表密码列是 `password`（非 `hashed_password`）、计数字段是 `failed_login_count`（非 `failed_status_count`），且 `sex` / `failed_login_count` 为 NOT NULL 无默认。
10. **⚠️ SQLite 上「结构跨版本升级」是空转，验证强度有限**：链上结构变更实际只有 `582670eaa9ea`（建全部表）；`f9c9610dbf51` 是纯数据迁移；`30bcfbeddb70` 在 `bind.dialect.name == "sqlite"` 时直接 `return`。因此**在 SQLite 上 downgrade 到任何非 base 版本结构都不变**，真正的结构跨版本升级需在 PostgreSQL 上才有验证意义。**SQLite 上真正有效的老库场景是「模型加了字段但库上缺列」→ 自愈兜底**（见第 11 条）。

### 脏库自愈 `_repair_dirty_tables`

自愈会在**用户库上执行 DDL**（`ALTER TABLE ADD COLUMN`），写错比迁移失败更严重——迁移失败只是启动不了，自愈写错是库被改坏。

- **覆盖**：缺表（`create_all` 指定表）/ 缺列（`ALTER TABLE ADD COLUMN`）。
- **已知限制（不得视为 bug）**：**不处理列类型变更**（如 `String` → `Integer`，库会带着错误类型继续跑）、**不处理列删除**（模型删了字段库上仍残留，无害）、**不处理约束变更**（nullable / unique）。
- ⚠️ **自愈会掩盖「改了模型但忘记生成迁移脚本」的错误**（高频陷阱）：

  ```
  改模型加了列但忘记生成迁移脚本
    → 老库启动 → 自动补列 → 服务正常运行 → 问题被完全掩盖
    → 只有「全新库」才会暴露（迁移链上没有该列 → no such column）
  ```

  即：**自愈把验证责任全部推给了「全新空库场景」，而没人会主动去跑空库。**
  - **判据：看到启动日志出现「检测到缺失的…正在补齐」= 有人漏了迁移脚本**，必须回头补上迁移，**不要认为「自愈已修好」**。

- ⚠️ **补列 SQL 只带类型、不带任何约束**（**已实测**）：实现是
  `col_type = column.type.compile(dialect)` → `ALTER TABLE "t" ADD COLUMN "c" INTEGER`。
  - **后果**：模型上的 `nullable=False` / default 都**不会**出现在补列语句里，补出来的列恒为**可空、无默认值**。
    **库结构会静默偏离模型定义**（`inspect()` 看得见差异，但没有任何告警）。
  - **因此先前「补列会撞 `NOT NULL` 而抛错」的说法是错的**（实测：`department.status` 编译结果仅为 `INTEGER`，补列成功不抛错）。
    **不要把 `NOT NULL` 当成自愈的失败路径**——自愈根本不生成该约束。
  - **`ADD COLUMN ... NOT NULL` 只在表非空时失败**（SQLite 特性）——它约束的是**手写迁移脚本**，不适用于自愈。
  - **待验证**：补列丢失的约束是否会在后续某处造成实际错误（尚未实跑确认，不得写成结论）。

- ⚠️ **自愈函数无异常保护**：`_repair_dirty_tables()` 自身**没有 try/except**，其内部 SQL 一旦抛错（如补列语句与库已有对象冲突）会冒泡打断 `init_data` → **服务启动失败**；`_upgrade_to_head()` 的 `command.upgrade()` 同样无保护（属有意设计）。
  - **不得在任何文案里承诺「自愈失败不影响使用」**——缺列会让**后续启动步骤**（依赖该表的查询）直接抛错，**「带病启动」在实现上做不到**。
  - **教训（一般化）**：**一条与实现相反的规则，比没有规则更危险**——它会让排查者**主动排除掉正确的假设**（「文档说不阻断启动，那这次启动失败肯定是别的原因」）。**写下「不阻断 / 不抛错 / 自动兜底」这类承诺前，必须回读实现确认**；**归因也必须实测，不能从「症状相似」推到「机制相同」**（本次即因此写出过错误归因）。详见 `.codebuddy/memory/MEMORY.md` 3.6。

### 历史遗留的空迁移

`1e99a7fcad44`（`add_security_features`）的 `upgrade()` / `downgrade()` **均为 `pass`**，文件内注释说明「原操作已并入 `582670eaa9ea` 基线，保留空函数以维持链历史」。

- **该空迁移是既有事实，不是缺陷**；但它是 `alembic downgrade -1` 变成无操作的原因。
- **新迁移不得为空**（见第 2 条）；历史空迁移**不得**为「补内容」而改动其 `upgrade()` 语义。
- **历史迁移只能追加，不得修改**：已落过 `stamp` 版本的库存在「同版本号、不同内容」的并存风险。

### 迁移验证的复现方式（供后续复跑）

```bash
cd backend
# 回归护栏（首选，覆盖 9 个场景）
uv run pytest tests/test_alembic_migration_roundtrip.py

# 临时库手工验证
ALEMBIC_DB_URL="sqlite:////tmp/verify.sqlite" uv run alembic upgrade head
ALEMBIC_DB_URL="sqlite:////tmp/verify.sqlite" uv run alembic downgrade base
ALEMBIC_DB_URL="sqlite:////tmp/verify.sqlite" uv run alembic upgrade head

# 开发库实跑（先做步骤 0 校验）
uv run alembic current    # 版本号
```

- `alembic/env.py:27` 支持 `ALEMBIC_DB_URL` 环境变量覆盖，**无需改动 `.env` 即可用临时库验证**。
- **比对必须逐表逐列做 set 比较，不能用抽查**（理由见第 4 条第 0.2 项）。
- **注意**：`init_data` 会主动把 `ALEMBIC_DB_URL` 设为 `settings.SQLALCHEMY_DATABASE_URI`（避免「检测一个库、升级另一个库」的错配）。手工用 `ALEMBIC_DB_URL` 跑 alembic 时走的是显式覆盖值，不受影响。
