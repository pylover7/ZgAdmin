# API 权限管理

ZgAdmin 支持基于角色的 API 级别权限控制，可精细控制每个角色能访问的接口。

## 功能概览

- 角色 ↔ API 绑定，控制角色可访问的接口
- 超级用户（is_superuser=true）自动拥有全部 API 权限
- API 路由自动同步到数据库
- 前端角色编辑弹窗集成"API 权限"选项卡

## 工作原理

1. **路由同步**：后端启动时，`_sync_api_routes` 自动将所有注册路由同步到 `api_permission` 表
2. **权限绑定**：通过角色编辑界面的"API 权限"选项卡，勾选该角色可访问的 API
3. **权限检查**：请求经过 `DependPermission` 中间件时，校验当前用户角色是否绑定了该 API

## API 权限表

每条记录对应一个后端路由端点：

| 字段 | 说明 |
|------|------|
| id | UUID |
| path | API 路径（如 `/api/v1/system/notice/list`） |
| method | HTTP 方法（POST/GET/PUT/DELETE） |
| summary | 接口描述 |
| module | 所属模块 |

## 后端 API

所有接口前缀：`/api/v1/system/api`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/list` | 获取所有 API 权限列表 |
| GET | `/by-role/{role_id}` | 获取指定角色绑定的 API |

角色 API 绑定通过角色管理接口操作：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/system/role/update` | 更新角色（含 `api_ids` 字段） |

### 请求示例

**更新角色的 API 权限**

```json
POST /api/v1/system/role/update
{
  "id": "role-uuid",
  "name": "编辑",
  "code": "editor",
  "api_ids": ["api-uuid-1", "api-uuid-2", "api-uuid-3"]
}
```

## 前端使用

路径：`系统管理 → 角色管理`（`/system/role`）

操作步骤：

1. 点击角色列表中的"编辑"按钮
2. 在弹窗中切换到"API 权限"选项卡
3. 勾选该角色可访问的 API
4. 保存

> 超级用户不受 API 权限限制，始终可访问所有接口。

## 二次开发

### 新增 API 自动同步

新增的后端路由只要注册到 `v1_router` 并使用 `DependPermission` 依赖，重启后会自动同步到 API 权限表，无需手动添加。

### 自定义权限检查

如果某个接口不需要权限检查，使用 `DependUser` 替代 `DependPermission`：

```python
# 需要权限检查
@router.post("/list", dependencies=[DependPermission])

# 仅需登录，不需要权限检查
@router.get("/mine", dependencies=[DependUser])
```
