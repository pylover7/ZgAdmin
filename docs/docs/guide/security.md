# 安全设置

ZgAdmin 提供完整的安全策略配置，包括密码复杂度策略、账户锁定策略、验证码开关和 IP 黑白名单。

## 功能概览

- 密码复杂度策略（长度、大小写、数字、特殊字符）
- 密码历史检查（防止重复使用近期密码）
- 账户锁定策略（失败次数 + 锁定时长）
- 登录验证码开关
- IP 黑白名单管理

## 密码策略

| 配置项 | 字段 | 默认值 | 范围 |
|--------|------|--------|------|
| 最小密码长度 | `min_password_length` | 8 | 6–32 |
| 需要大写字母 | `require_uppercase` | true | — |
| 需要小写字母 | `require_lowercase` | true | — |
| 需要数字 | `require_digit` | true | — |
| 需要特殊字符 | `require_special` | false | — |
| 密码历史检查数 | `password_history_count` | 3 | 0–24 |

> `password_history_count` 设为 0 表示不检查历史密码。设为 N 表示不允许使用最近 N 次的密码。

## 账户锁定策略

| 配置项 | 字段 | 默认值 | 范围 |
|--------|------|--------|------|
| 最大登录尝试次数 | `max_login_attempts` | 5 | 3–20 |
| 锁定时长（分钟） | `lockout_duration_minutes` | 30 | 5–1440 |

连续登录失败达到最大次数后，账户将被锁定指定时长。

## 验证码

| 配置项 | 字段 | 默认值 |
|--------|------|--------|
| 启用验证码 | `captcha_enabled` | true |

启用后，登录页面将展示服务端生成的验证码。

## IP 黑白名单

支持添加 IP 或 CIDR 规则：

| 规则类型 | 说明 | 优先级 |
|---------|------|--------|
| whitelist | 白名单，允许指定 IP 访问 | 黑名单优先 |
| blacklist | 黑名单，拒绝指定 IP 访问 | 高于白名单 |

> **优先级规则**：如果同一 IP 同时匹配黑名单和白名单，黑名单优先。

### 支持的格式

- 单个 IP：`192.168.1.100`
- CIDR 段：`10.0.0.0/24`

### 规则属性

| 字段 | 说明 |
|------|------|
| ip_cidr | IP 地址或 CIDR |
| rule_type | whitelist / blacklist |
| description | 规则描述 |
| is_active | 是否启用 |

## 后端 API

所有接口前缀：`/api/v1/settings/security`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/policy` | 获取安全策略 |
| POST | `/policy` | 更新安全策略 |
| GET | `/ip-rules` | 获取 IP 规则列表 |
| POST | `/ip-rules` | 新增 IP 规则 |
| POST | `/ip-rules/update` | 更新 IP 规则 |
| POST | `/ip-rules/delete` | 删除 IP 规则（传 ID 数组） |

### 请求示例

**更新安全策略**

```json
POST /api/v1/settings/security/policy
{
  "min_password_length": 10,
  "require_uppercase": true,
  "require_lowercase": true,
  "require_digit": true,
  "require_special": true,
  "password_history_count": 5,
  "max_login_attempts": 3,
  "lockout_duration_minutes": 60,
  "captcha_enabled": true
}
```

**新增 IP 规则**

```json
POST /api/v1/settings/security/ip-rules
{
  "ip_cidr": "10.0.0.0/24",
  "rule_type": "whitelist",
  "description": "内网白名单",
  "is_active": true
}
```

## 前端使用

路径：`系统设置 → 安全设置`（`/settings/security`）

页面分为两个卡片：

1. **安全策略配置**：表单配置密码策略和锁定策略，修改后点"保存策略"
2. **IP 黑白名单**：表格展示规则列表，支持新增、编辑、删除

## 配置存储

安全策略和 IP 规则存储在 INI 配置文件中，修改后**无需重启服务**即可生效。

## 数据模型

### SecurityPolicy

| 字段 | 类型 | 说明 |
|------|------|------|
| min_password_length | int | 最小密码长度 |
| require_uppercase | bool | 需要大写字母 |
| require_lowercase | bool | 需要小写字母 |
| require_digit | bool | 需要数字 |
| require_special | bool | 需要特殊字符 |
| password_history_count | int | 密码历史检查数 |
| max_login_attempts | int | 最大登录尝试次数 |
| lockout_duration_minutes | int | 锁定时长（分钟） |
| captcha_enabled | bool | 是否启用验证码 |

### IPRule

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ip_cidr | str | IP/CIDR |
| rule_type | str | whitelist / blacklist |
| description | str | 描述 |
| is_active | bool | 是否启用 |
| created_at | datetime | 创建时间 |
