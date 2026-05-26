# 通知系统

ZgAdmin 内置完整的通知系统，支持系统通知、业务通知和公告，前端通过铃铛图标实时展示未读数。

## 功能概览

- 通知 CRUD（创建、编辑、删除、批量删除）
- 三种通知类型：系统通知、业务通知、公告
- 三种通知级别：info、warning、important
- 两种状态：草稿、已发布
- 前端铃铛组件 30 秒轮询未读数
- 支持标记已读、全部已读

## 通知类型与级别

### 类型（type）

| 值 | 含义 | 标签颜色 |
|---|------|---------|
| 0 | 系统通知 | primary |
| 1 | 业务通知 | success |
| 2 | 公告 | warning |

### 级别（level）

| 值 | 含义 | 标签颜色 |
|---|------|---------|
| info | 一般 | info |
| warning | 警告 | warning |
| important | 重要 | danger |

### 状态（status）

| 值 | 含义 | 标签颜色 |
|---|------|---------|
| 0 | 草稿 | info |
| 1 | 已发布 | success |

## 后端 API

所有接口前缀：`/api/v1/system/notice`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/list` | 分页查询通知列表 |
| POST | `/add` | 新增通知 |
| POST | `/update` | 更新通知 |
 | POST | `/delete` | 删除通知（传 ID 数组） |
| GET | `/unread-count` | 获取当前用户未读数 |
| POST | `/mark-read/{id}` | 标记指定通知已读 |
| POST | `/mark-all-read` | 标记全部已读 |

### 请求示例

**创建通知**

```json
POST /api/v1/system/notice/add
{
  "title": "系统维护通知",
  "content": "系统将于今晚 22:00 进行维护",
  "type": 0,
  "level": "warning",
  "status": 1
}
```

**查询通知列表**

```json
POST /api/v1/system/notice/list
{
  "title": "",
  "type": null,
  "level": "",
  "status": null,
  "page": 1,
  "pageSize": 10
}
```

## 数据模型

### Notice

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| title | str | 通知标题 |
| content | str | 通知内容 |
| type | int | 通知类型（0/1/2） |
| level | str | 级别（info/warning/important） |
| status | int | 状态（0=草稿，1=已发布） |
| created_by | UUID | 创建人 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### NoticeRead

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| notice_id | UUID | 通知 ID |
| user_id | UUID | 用户 ID |
| read_at | datetime | 阅读时间 |

## 前端使用

### 管理页面

路径：`系统管理 → 通知管理`（`/system/notice`）

功能：
- 按标题、类型、级别、状态筛选
- 新增/编辑通知（弹窗表单）
- 单条删除、批量删除
- 分页浏览

### 铃铛通知组件

铃铛组件自动轮询（30 秒间隔）获取未读通知数，展示在顶部导航栏。点击可展开通知列表，支持逐条已读和全部已读。

## 二次开发

### 自定义通知类型

如需新增通知类型，修改：

1. 后端模型 `backend/app/models/notice.py` 中 `type` 字段注释
2. 前端映射 `frontend/src/views/system/notice/utils/hooks.tsx` 中的 `typeMap` 和 `typeTagType`
3. 国际化文件中的翻译键

### 推送通知

在业务代码中调用 Controller 发送通知：

```python
from app.controllers.notice import notice_controller

# 给所有用户发送系统通知
notice = await notice_controller.create(obj_in=NoticeCreate(
    title="新功能上线",
    content="文件管理模块已上线，欢迎使用",
    type=0,
    level="info",
    status=1,
    created_by=current_user.id
))
```
