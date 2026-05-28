---
name: backend-patterns
description: 后端编码规范、Controller 模式、依赖注入、响应格式、配置管理的完整参考。开发后端 API/模块时加载。
---

# 后端编码模式参考

> 开发后端功能时，先加载此 Skill 获取规范参考，再查阅 `references/` 下的详细架构文档。

---

## 后端编码规范（9 条）

1. **API 路由风格**：RESTful 风格，使用 POST 传查询条件 + GET 参数分页
2. **响应格式**：统一使用 `Success`/`Fail`/`SuccessExtra`/`FailAuth` 包装响应
3. **认证依赖**：所有需认证的接口使用 `DependPermission` 或 `DependUser`
4. **Controller 模式**：业务逻辑放在 `controllers/`，不在路由函数中直接写
5. **模型定义**：SQLModel 同时作为 ORM 模型和 Pydantic Schema，使用 `*Create`/`*Update` 变体做输入校验
6. **UUID 主键**：所有模型使用 UUID4 作为主键
7. **配置管理**：环境变量（`.env` + `pydantic-settings`）+ 数据库配置表（`SiteConfig`/`OAuthConfig`/`EmailConfig`/`SecurityPolicy`，运行时可改）
8. **日志**：使用 Loguru，登录/操作/系统日志写入数据库
9. **慎用 try/except**：非必要不使用 try 语句，优先通过完整的条件判断、类型检查、默认值处理等方式保证代码健壮性，而非依赖异常捕获来控制流程

---

## 架构速查

详细架构文档见 `references/architecture.md`，核心速查如下：

### 依赖注入速查

| 依赖 | 用途 |
|------|------|
| `DependAuth` | 仅认证，返回 User 对象 |
| `DependPermission` | 认证 + 权限检查 |
| `DependUser` | `Annotated[User, DependAuth]`，直接注入当前用户 |
| `SessionDep` | 数据库 Session 注入 |
| `DependRateLimit` | IP 级别限流（Redis 滑动窗口） |

### 统一响应格式

```python
Success(code=200, msg="OK", data=..., success=True)
Fail(code=400, msg="Fail", data=None)
SuccessExtra(code=200, data=..., total=0, currentPage=1, pageSize=20)  # 分页
FailAuth(code=401, msg="Unauthorized")
```

### Controller 模式

两种控制器模式：

**1. CRUDBase — 多行 CRUD 控制器**

```python
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    async def create(session, obj_in) -> ModelType
    async def delete(session, idList) -> bool
    async def delete_all(session) -> int
    async def update(session, pk, obj_in) -> Optional[ModelType]
    async def get(session, pk) -> ModelType | None
    async def get_latest(session) -> ModelType | None
    async def all(session) -> list[ModelType]
    async def list(session, currentPage, pageSize, where, order, options) -> (Total, list)
```

**2. ConfigController — 单行配置控制器**

用于全局只有一条记录的配置表，不继承 CRUDBase：

```python
class ConfigController(Generic[T, U]):
    def get(session) -> T | None
    def update(session, data) -> T | None
    def mask_sensitive(data) -> dict

# 实例
siteConfigController = ConfigController(SiteConfig, SiteConfigUpdate)
oauthConfigController = ConfigController(OAuthConfig, OAuthConfigUpdate)
emailConfigController = ConfigController(EmailConfig, EmailConfigUpdate)
securityPolicyController = ConfigController(SecurityPolicy, SecurityPolicyUpdate)
```

### 添加新后端 API 模块

1. 在 `app/models/` 创建数据模型
2. 在 `app/controllers/` 创建 Controller（继承 `CRUDBase`）
3. 在 `app/api/v1/` 创建路由文件
4. 在 `app/api/v1/__init__.py` 注册路由到 `v1_router`
5. 运行 `alembic revision --autogenerate` + `alembic upgrade head`
6. 启动后 `_sync_api_routes` 自动将新路由同步到数据库
