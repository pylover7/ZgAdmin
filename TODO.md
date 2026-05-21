# ZgAdmin 后台管理系统 — 功能完善执行计划

---

## 分支策略总览

| 分支 | 阶段 | 内容 | 依赖 | 风险 |
|------|------|------|------|------|
| `fix/critical-bugs` | Phase 0 | 后端 + 前端已知 Bug 修复 | 无 | 🟢 |
| `refactor/log-unify` | Phase 1 | 日志双轨统一（保留数据库，废弃文件） | Phase 0 | 🔴 |
| `feat/notice` | Phase 2 | 通知 / 消息系统 ⬅️ **当前分支** | Phase 0 | 🟡 |
| `feat/account-settings` | Phase 3 | 账户设置对接（个人信息 / 安全日志 / 偏好） | Phase 0 | 🟢 |
| `feat/general-settings` | Phase 3 | 通用设置页面 | Phase 0 | 🟢 |
| `feat/dashboard-data` | Phase 3 | 仪表盘接入真实数据 | Phase 0 | 🟢 |
| `feat/online-users` | Phase 3 | 在线用户管理 | Phase 0 | 🟡 |
| `feat/api-permission` | Phase 4 | API 权限管理 + API 管理页面 | Phase 0, 角色模型 | 🟡 |
| `feat/security` | Phase 4 | 登录安全增强 + IP 过滤 + 限流 Redis 化 | Phase 0 | 🟡 |
| `feat/data-dict` | Phase 5 | 数据字典 | 无 | 🟢 |
| `feat/file-manager` | Phase 5 | 文件管理（上传 / 列表 / 删除） | 无 | 🟢 |
| `feat/dept-manage` | Phase 5 | 部门 / 组织架构管理 | 用户模型 | 🟢 |
| `feat/scheduled-tasks` | Phase 5 | 定时任务调度 | 无 | 🟡 |
| `feat/data-io` | Phase 5 | 数据导入导出 | 用户 / 日志模型 | 🟢 |
| `feat/audit-log` | Phase 5 | 操作审计日志（含变更 diff） | Phase 1（统一日志层） | 🟡 |
| `feat/system-health` | Phase 5 | 系统健康检查 / 监控端点 | 无 | 🟢 |
| `feat/payment` | Phase 6 | 微信支付模块 | 订单模型 | 🟡 |
| `feat/data-backup` | Phase 7 | 数据备份与恢复 | 无 | 🟡 |
| `test/core-coverage` | Phase 7 | 后端单元测试 / 集成测试 / 前端 E2E | 所有功能完成 | 🟢 |
| `chore/i18n-docs` | Phase 7 | 国际化 + 文档补充 | 所有功能完成 | 🟢 |

### 执行顺序

```
Phase 0 (立即) → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
                    ↑          ↑
                    └─ 注意 ──┘ Phase 2 依赖 Phase 1 完成（通知需要稳定的日志层）
```

### 分支合并策略

- 每个分支基于 `main` 创建，完成后提 PR → review → squash merge 回 `main`
- Phase 0 修复分支最先合并，为后续分支提供干净的基线
- Phase 3 的 4 个分支彼此独立，可并行开发
- Phase 5 的 7 个分支彼此独立，可并行开发

---

## Phase 0 — 关键 Bug 修复（P0，立即执行）

> **分支**：`fix/critical-bugs`
> **风险**：🟢 低 — 修复范围明确，改动小，回滚简单。
> **依赖**：无。从 `main` 创建，完成后立即合回。

### 0.1 后端 Bug

- [x] `pay/setting.py`：`pay_setting_update` 的 `wechat` 分支补充 `set_config` 实现
- [x] `pay/test.py`：发送邮件测试接口加 `DependPermission` 鉴权 ⚠️ 安全
- [x] `settings/login.py`：`update_login_config` 异常时 `Success(msg="保存成功！")` 改为 `Fail`
- [x] `system/role.py`：`delete_role` 补充缺失的 `return` 语句
- [x] `system/user.py`：`update_user` 逻辑修正 — `if user.id != data.id` 永远不会为 True（先查了 `data.id` 再判断）
- [x] `RateLimiter` 限流器：从纯内存存储改为 Redis 存储（多进程/多容器部署兼容）⚠️ 架构

### 0.2 前端 Bug

- [x] `api/system.ts`：`getRoleIds` 路径 `/list-role-ids` → `/system/role/list-role-ids`
- [x] `api/system.ts`：`getOnlineLogsList` 路径 `/online-logs` → 修正为正确路径
- [x] `api/system.ts`：`getSystemLogsDetail` 路径 `/system-logs-detail` → 修正为正确路径
- [x] `api/system.ts`：`clearSystemLogs` 请求方法 `POST` → `GET`（与后端一致）
- [x] 通知铃铛组件：`data.ts` 中硬编码数据替换为动态数据（为 Phase 2 通知系统铺路）

---

## Phase 1 — 架构债务清理（P0）

> **分支**：`refactor/log-unify`
> **风险**：🔴 高 — 删除文件日志接口可能影响多页面；logger 改数据库写入需验证性能。
> **回滚方案**：保留 `system/monitor.py` 旧接口，新增数据库写入为 opt-in，确认稳定后再删旧代码。
> **依赖**：Phase 0（`fix/critical-bugs` 合入 main 后基于 main 创建）。

### 1.1 日志双轨统一（保留数据库，废弃文件）

当前两套实现：
- **文件日志**：`system/monitor.py` 直接读写 `.log` 文件
- **数据库日志**：`monitor/logs/` 下 SQLModel `LoginLog / OperationLog / SystemLog`

- [x] 最终确认统一方案为"保留数据库日志，废弃文件日志"
- [x] `app/settings/log.py` 的 logger 增加数据库 handler（登录日志、操作日志、系统日志分别写对应表）
- [x] `system/monitor.py` 中基于文件读写的接口标记 `@deprecated`，保留一个版本过渡期
- [x] 确认前端 `api/system.ts` 所有日志 API 指向 `monitor/logs/*` 数据库接口
- [x] 确认 `monitor/logs/login|operation|system` 三个前端页面对接数据库接口正确
- [x] 过渡期结束后删除 `system/monitor.py` 中 `getLoginLogs / getOperationLogs / getSystemLogs` 及对应 `clear*`
- [x] 生成 Alembic 迁移脚本（如需新增日志表字段）

---

## Phase 2 — 通知系统（P0，当前分支 `feat/notice`）

> **分支**：`feat/notice`（当前所在分支）
> **风险**：🟡 中 — 全新模块，涉及前后端多处改动；铃铛组件改造需兼容现有布局。
> **依赖**：Phase 0（Bug 修复合入 main 后 rebase）；建议等 Phase 1（日志统一）合入后再继续，通知需写入操作日志。

### 2.1 后端通知模块

- [x] 创建 `Notice` 数据模型（`backend/app/models/notice.py`）：标题、内容、类型（系统/业务/公告）、级别、状态（草稿/已发布）、创建人
- [x] 创建 `NoticeRead` 关联模型（多对多，通知 ↔ 用户已读状态）
- [x] 创建 `NoticeController`（`backend/app/controllers/notice.py`）：CRUD + 未读计数 + 未读列表 + 标记已读 + 全部已读
- [x] 创建通知 API 路由（`backend/app/api/v1/system/notice.py`）：
  - `POST /notice/add` — 发布通知
  - `POST /notice/list` — 通知列表（分页、按类型/级别/状态筛选）
  - `POST /notice/update` — 编辑通知
  - `POST /notice/delete` — 删除通知
  - `GET /notice/unread` — 当前用户未读通知
  - `POST /notice/read` — 标记单条已读
  - `POST /notice/readAll` — 全部标记已读
- [x] 注册路由到 `v1_router`（`systemRouter.include_router(noticeRouter, prefix="/notice")`）
- [x] 🔒 补充权限：`/list`、`/update`、`/delete` 三个接口添加 `DependUser` 依赖
- [x] 🔄 生成 Alembic 迁移脚本并执行
- [x] `seed/data/menus.py` 新增通知管理菜单项（系统管理下子菜单）

### 2.2 前端通知功能

- [x] 创建 `frontend/src/api/notice.ts` 通知 API 封装（7 个方法与后端一一对应）
- [x] 创建 `frontend/src/views/system/notice/index.vue` 通知管理页（CRUD 表格 + 发布/编辑弹窗）
- [x] 改造 `frontend/src/layout/components/lay-notice/` 铃铛组件：
  - `data.ts` 中 `noticesData` 从 API 实时拉取（调用 `getUnreadNotices()`）
  - "通知" tab 对接 `/notice/unread`
  - "标记已读" 对接 `/notice/read`（调用 `markNoticeRead()`）
  - "全部已读" 对接 `/notice/readAll`（调用 `markAllRead()`）
  - "查看更多" 跳转到通知管理页
- [x] 铃铛红点实时显示未读数（定时轮询 `/notice/unread`，30s 间隔）
- [x] 🔄 国际化：`locales/zh-CN.yaml` 和 `locales/en.yaml` 补充通知相关翻译键

---

## Phase 3 — 空白页面 & 账户设置对接（P1）

> Phase 3 内 4 个分支彼此独立，可并行开发。

### 3.1 账户设置对接

> **分支**：`feat/account-settings`
> **风险**：🟢 低 — 主要是 API 对接修正，无新增模型。

- [x] `getMine` API 指向 `/mine` 但后端无此路由 → 改为指向 `/api/v1/base/userinfo`
- [x] 头像上传统一对接 `updateAvatar` 接口（复用 Phase 5 文件管理模块）
- [x] 昵称 / 邮箱 / 手机号编辑保存功能
- [x] `getMineLogs` API 指向 `/mine-logs` 但后端无此路由 → 后端新增当前用户安全日志查询接口
- [x] `Preferences.vue` 扩展：语言偏好、通知偏好设置项
- [x] 后端存储用户偏好到数据库
- [x] 🔄 用户偏好表生成 Alembic 迁移脚本

### 3.2 通用设置页面

> **分支**：`feat/general-settings`
> **风险**：🟢 低 — 新增页面 + 接口，独立模块。

- [x] 设计"通用设置"页面布局（`settings/general/index.vue`）
- [x] 后端新增 `GET/POST /api/v1/settings/general` 接口（站点名称、Logo、描述、默认语言等）
- [x] 🔄 生成 Alembic 迁移脚本（新增 settings 配置表）
- [x] 表单校验 + 保存交互

### 3.3 仪表盘真实数据

> **分支**：`feat/dashboard-data`
> **风险**：🟢 低 — 替换硬编码数据为 API 调用。

- [ ] 后端新增 `GET /api/v1/base/dashboard` 统计接口（用户总数、今日新增、在线人数、系统负载等）
- [ ] 前端 `data.ts` 中 `chartData / barChartData / progressData / tableData` 改为 API 拉取
- [ ] "上周/本周"切换联动真实数据查询

### 3.4 ~~在线用户管理~~

> **分支**：`feat/online-users`
> **风险**：🟡 中 — 依赖 Redis；强制下线需处理 WebSocket / Token 失效。

- [ ] 后端实现在线用户追踪（Redis 存储活跃 Token → 用户映射，TTL 过期自动清理）
- [ ] 后端新增 `POST /api/v1/monitor/online/list` 分页查询
- [ ] 后端新增 `POST /api/v1/monitor/online/offline` 强制下线（Redis 删除对应 key + Token 加入黑名单）
- [ ] 前端 `hook.tsx` 调用真实 API 替换 mock 数据
- [ ] 移除页面上"仅演示，操作后不生效"提示

---

## Phase 4 — 安全与权限加固（P1）

### 4.1 API 权限管理

> **分支**：`feat/api-permission`
> **风险**：🟡 中 — 改动角色鉴权逻辑，可能影响现有用户访问。

- [ ] `role.py`：`getRoleAuth` 同时返回 `menuIds` + `apiIds`
- [ ] `role.py`：`updateRoleAuth` 同时更新 `menuIds` + `apiIds`
- [ ] 前端角色管理弹窗新增 "API 权限" tab，展示所有 API 列表，勾选绑定
- [ ] 前端新增 `system/api/index.vue` 页面（API 接口管理 CRUD）
- [ ] 后端 `api.py` 接口增强（分页查询、搜索过滤）
- [ ] `seed/data/menus.py` 新增 API 管理菜单项

### 4.2 登录安全 & 网络防护

> **分支**：`feat/security`
> **风险**：🟡 中 — 新增模块；IP 黑名单可能误封。

- [ ] 登录验证码（图形验证码 / 滑块验证）
- [ ] 登录失败锁定策略：连续 N 次失败锁定账号 M 分钟
- [ ] 双因素认证（2FA / TOTP，可选启用）
- [ ] 🔄 用户表新增 `failed_login_count`、`locked_until`、`totp_secret` 字段 + Alembic 迁移
- [ ] IP 白名单 / 黑名单管理页面
- [ ] `RateLimiter` 从内存改为 Redis 存储（与 Phase 0 中 Bug 修复联动，此处做完整方案）
- [ ] 密码复杂度策略配置（最小长度、特殊字符、历史密码不可重用）

---

## Phase 5 — 扩展功能（P2）

> Phase 5 内 7 个分支彼此独立，可并行开发。

### 5.1 数据字典

> **分支**：`feat/data-dict`
> **风险**：🟢 低 — 标准 CRUD 模块。

- [ ] 后端新增 `Dictionary` 模型（字典类型：编码、名称、状态）+ `DictionaryItem` 模型（字典项：类型关联、编码、值、排序）
- [ ] 🔄 生成 Alembic 迁移脚本
- [ ] 后端 CRUD 接口（类型管理 + 项管理）
- [ ] 前端新增 `system/dict/index.vue` 字典管理页（两级表格：类型 → 项）
- [ ] `seed/data/menus.py` 新增菜单项

### 5.2 文件管理

> **分支**：`feat/file-manager`
> **风险**：🟢 低 — 标准模块，注意存储容量和文件类型安全。

- [ ] 后端新增文件上传接口（支持本地存储 / S3 兼容 OSS，通过配置切换）
- [ ] 后端文件列表 / 删除接口
- [ ] 后端新增 `File` 模型（文件名、路径、大小、类型、上传者、创建时间）
- [ ] 🔄 生成 Alembic 迁移脚本
- [ ] 前端新增 `system/file/index.vue` 文件管理页
- [ ] 头像上传切换为使用文件管理模块统一接口
- [ ] 上传安全：文件类型白名单、大小限制、病毒扫描（可选）
- [ ] `seed/data/menus.py` 新增菜单项

### 5.3 部门 / 组织架构管理

> **分支**：`feat/dept-manage`
> **风险**：🟢 低 — 标准树形 CRUD。

- [ ] 后端新增 `Department` 模型（名称、父级ID、排序、负责人、状态）
- [ ] 🔄 生成 Alembic 迁移脚本 + 用户表新增 `dept_id` 外键
- [ ] 后端 CRUD + 树形查询接口
- [ ] 前端新增 `system/dept/index.vue` 部门管理页（树形表格 + 新增/编辑弹窗）
- [ ] 用户管理页面增加"所属部门"筛选和展示
- [ ] `seed/data/menus.py` 新增菜单项

### 5.4 定时任务

> **分支**：`feat/scheduled-tasks`
> **风险**：🟡 中 — APScheduler / Celery 引入新依赖；Cron 错误可能导致任务堆积。

- [ ] 后端集成 APScheduler（轻量）或 Celery（重量，按需选择）
- [ ] 后端新增 `ScheduledTask` 模型（任务名、Cron 表达式、状态、最后执行时间、执行结果）
- [ ] 🔄 生成 Alembic 迁移脚本
- [ ] 后端 CRUD + 手动执行 / 暂停 / 恢复接口
- [ ] 任务执行日志记录（成功/失败 + 错误信息 + 耗时）
- [ ] 前端新增 `monitor/task/index.vue` 定时任务管理页
- [ ] `seed/data/menus.py` 新增菜单项

### 5.5 数据导入导出

> **分支**：`feat/data-io`
> **风险**：🟢 低 — 标准功能。

- [ ] 后端日志列表接口增加 `export` 参数，返回 CSV / Excel 文件流
- [ ] 后端用户批量导入接口（上传 CSV/Excel → 解析 → 校验 → 批量创建）
- [ ] 前端日志页面增加"导出"按钮
- [ ] 前端用户管理页增加"批量导入"按钮（上传文件 + 预览 + 确认导入）
- [ ] 导入模板下载功能

### 5.6 操作审计日志（含变更 diff）

> **分支**：`feat/audit-log`
> **风险**：🟡 中 — 需在现有操作日志基础上扩展 diff 记录；存储量可能较大。
> **依赖**：Phase 1（统一日志层，确保日志基础设施稳定）。

- [ ] 操作日志扩展：记录每次 CRUD 操作的变更前后 diff（JSON 格式存储 before/after）
- [ ] 前端操作日志详情页增加"变更对比"视图（diff 高亮展示）
- [ ] 日志保留策略：按时间自动归档或清理（配置项 `LOG_RETENTION_DAYS`）
- [ ] 敏感字段脱敏（密码、密钥等字段在 diff 中不记录原始值）

### 5.7 系统健康检查

> **分支**：`feat/system-health`
> **风险**：🟢 低 — 标准端点，无业务依赖。

- [ ] 后端新增 `GET /api/v1/health` 端点（数据库连接、Redis 连接、磁盘使用率、内存）
- [ ] 后端新增 `GET /api/v1/metrics` 端点（Prometheus 格式，请求计数、延迟分位数、错误率）
- [ ] Docker 健康检查指令指向 `/api/v1/health`

---

## Phase 6 — 支付模块（P2）

> **分支**：`feat/payment`
> **风险**：🟡 中 — 支付涉及资金安全；回调处理需防重复通知。

- [ ] 取消 `base.py` 中 `notify/wechat` 和 `websocket/wechat` 注释，完善支付回调逻辑
- [ ] 实现 `Order` 数据模型 + `OrderController`
- [ ] 🔄 生成 Alembic 迁移脚本（订单表）
- [ ] 实现 `backend/app/core/schedule.py` 中 `update_expired_orders` 订单过期自动取消
- [ ] 前端新增支付页面或支付弹窗组件
- [ ] 支付回调幂等处理（防重复通知）

---

## Phase 7 — 质量保障（P3）

### 7.1 数据备份与恢复

> **分支**：`feat/data-backup`
> **风险**：🟡 中 — 备份文件安全存储；恢复操作不可逆。

- [ ] 后端新增数据库备份接口（导出 SQL dump 或 JSON）
- [ ] 后端新增恢复接口（从备份文件恢复，需二次确认 + 超级管理员权限）
- [ ] 定时自动备份（通过 Phase 5 定时任务模块驱动）
- [ ] 备份文件加密存储（AES）
- [ ] 前端新增 `system/backup/index.vue` 备份管理页

### 7.2 测试

> **分支**：`test/core-coverage`
> **风险**：🟢 低。

- [ ] 后端单元测试：用户、角色、权限、通知模块
- [ ] 后端集成测试：所有 API 端点（login → CRUD → logout 完整流程）
- [ ] 前端 E2E 测试：登录、用户 CRUD、通知收发关键路径

### 7.3 国际化与文档

> **分支**：`chore/i18n-docs`
> **风险**：🟢 低。

- [ ] `frontend/locales/zh-CN.yaml` 和 `en.yaml` 补充所有新增页面的翻译键
- [ ] `seed/data/menus.py` 新增菜单项使用 i18n key 替代硬编码中文
- [ ] `docs/` 补充新增模块的使用文档
- [ ] FastAPI Swagger Schema 描述补充完整（`description`、`example`）

---

## 风险评估汇总

| 风险等级 | 分支 | 主要风险 | 缓解措施 |
|---------|------|---------|---------|
| 🔴 高 | `refactor/log-unify` | 删旧接口可能大面积断连；DB 写入性能 | 渐进式废弃（先标记 deprecated → 过渡 → 删除）；压测验证 |
| 🔴 高 | `fix/critical-bugs` — `update_user` 逻辑 | 修改鉴权逻辑可能引入新 Bug | 仅修正逻辑条件，不改 API 签名 |
| 🟡 中 | `feat/notice` | 新模块前后端多处改动 | 按 2.1 → 2.2 顺序实施，每步验证 |
| 🟡 中 | `feat/online-users` | Redis 依赖引入；强制下线 Token 失效 | Redis 降级处理（不可用时优雅降级） |
| 🟡 中 | `feat/api-permission` | 角色鉴权改动影响现有用户 | 默认不绑定 API = 无 API 权限（fail-safe） |
| 🟡 中 | `feat/security` | IP 黑名单误封；2FA 锁死 | IP 白名单优先于黑名单；2FA 提供恢复码 |
| 🟡 中 | `feat/scheduled-tasks` | 新依赖引入；Cron 配置错误 | APScheduler 任务隔离；默认暂停状态 |
| 🟡 中 | `feat/audit-log` | diff 存储量可能较大 | 日志保留天数配置 + 定期清理 |
| 🟡 中 | `feat/payment` | 资金安全；回调重复 | 回调幂等 key；事务保证 |
| 🟡 中 | `feat/data-backup` | 恢复操作不可逆 | 二次确认 + 超级管理员权限 + 操作日志 |
| 🟢 低 | 其余 10 个分支 | 标准 CRUD / 页面开发 | 常规 review 即可 |

---

## 安全检查清单

> 每个 Phase 完成后，对照此清单自查。

### 鉴权与访问控制
- [ ] 所有新增 API 端点均添加 `DependPermission` 鉴权装饰器
- [ ] 无硬编码的 Token / 密钥在前端代码中
- [ ] 敏感操作（删除、强制下线、恢复备份）需二次确认 + 操作日志

### 注入防护
- [ ] 所有原生 SQL（`psycopg`）查询使用参数化，禁止字符串拼接
- [ ] 前端用户输入渲染前经过 XSS 转义（Vue 默认安全，检查 `v-html` 使用点）
- [ ] 文件上传校验 MIME 类型 + 扩展名白名单

### 敏感信息保护
- [ ] 日志中不记录密码明文、Token、密钥
- [ ] 审计 diff 中对密码/密钥字段脱敏（不记录原始值）
- [ ] `.env` / `platform-config.json` 不提交到仓库（检查 `.gitignore`）
- [ ] 备份文件加密存储，传输使用 HTTPS

### 会话与认证
- [ ] JWT Token 设置合理过期时间（Access Token ≤ 2h，Refresh Token ≤ 7d）
- [ ] 登出时服务端 Token 失效（Redis 黑名单）
- [ ] 密码复杂度策略已配置并生效

### 网络安全
- [ ] CORS 配置仅允许受信任的域名
- [ ] HTTPS 强制（生产环境 nginx 配置 `HSTS`）
- [ ] IP 白名单/黑名单功能正常工作

### 依赖安全
- [ ] 定期 `uv lock --upgrade` / `bun update` 更新依赖
- [ ] 不使用已知有 CVE 的依赖版本（CI 中集成 `pip-audit` / `bun audit`）

### 数据完整性
- [ ] 所有数据库迁移脚本可正向执行 + 可回滚（`downgrade` 已定义）
- [ ] 数据库备份定期自动执行 + 备份完整性校验

---

## 附录：缺失功能已补充

相比于原始 TODO，本次新增以下模块：

| 新增模块 | 分支 | 理由 |
|---------|------|------|
| 部门/组织架构管理 | `feat/dept-manage` | 用户管理需关联组织，标准后台功能 |
| 数据导入导出 | `feat/data-io` | 批量操作效率需求，原只有导出无导入 |
| 操作审计日志（含 diff） | `feat/audit-log` | "谁在几点改了哪条记录的什么字段"的完整追溯 |
| 系统健康检查 | `feat/system-health` | Docker 部署场景下的监控必需 |
| 登录安全增强 | `feat/security` | 验证码、2FA、锁定策略、IP 过滤 — 原只有简单的 RateLimiter |
| 数据备份恢复 | `feat/data-backup` | 运维基本需求 |
