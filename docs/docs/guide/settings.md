# 系统设置

ZgAdmin 提供「通用设置」和「登录设置」两个配置页面，修改后**无需重启服务**即可生效。

## 通用设置

路径：`系统设置 → 通用设置`（`/settings/general`）

### 配置项

| 配置项 | 字段 | 说明 |
|--------|------|------|
| 站点名称 | `site_name` | 显示在浏览器标题栏和系统各处，必填，最长 50 字符 |
| 站点描述 | `site_desc` | 站点简介，最长 200 字符 |
| Logo | `logo` | Logo 图片 URL，支持实时预览 |
| 默认语言 | `default_lang` | 支持 `zh-CN` 和 `en` |
| 启用邮件 | `enable_email` | 开关，控制邮件发送功能 |
| 版权信息 | `copyright` | 页脚版权文字 |
| 备案号 | `icp` | ICP 备案号 |

### 保存后自动生效

保存通用设置后，前端会自动：
- 更新浏览器标题栏
- 更新全局配置（站点名称、语言、描述、Logo 等）

## 登录设置

路径：`系统设置 → 登录设置`（`/settings/login`）

### QQ 登录

| 配置项 | 字段 | 说明 |
|--------|------|------|
| 启用 QQ 登录 | `qq.enabled` | 开关 |
| App ID | `qq.app_id` | QQ 互联应用的 App ID |
| App Key | `qq.app_key` | QQ 互联应用的 App Key |
| 回调地址 | `qq.redirect_uri` | OAuth 回调 URL，必须以 `http://` 或 `https://` 开头 |

### 微信登录

| 配置项 | 字段 | 说明 |
|--------|------|------|
| 启用微信登录 | `wechat.enabled` | 开关 |
| App ID | `wechat.app_id` | 微信开放平台 App ID |
| App Secret | `wechat.app_secret` | 微信开放平台 App Secret |
| 回调地址 | `wechat.redirect_uri` | OAuth 回调 URL，必须以 `http://` 或 `https://` 开头 |

### 配置步骤

**QQ 登录配置流程**：

1. 前往 [QQ 互联](https://connect.qq.com/) 注册开发者账号
2. 创建网站应用，获取 App ID 和 App Key
3. 设置回调地址（通常为 `https://yourdomain.com/api/v1/auth/qq/callback`）
4. 在登录设置页面填入配置并保存

**微信登录配置流程**：

1. 前往 [微信开放平台](https://open.weixin.qq.com/) 注册账号
2. 创建网站应用，获取 App ID 和 App Secret
3. 设置回调地址（通常为 `https://yourdomain.com/api/v1/auth/wechat/callback`）
4. 在登录设置页面填入配置并保存

> 关闭第三方登录开关后，相关配置项变为只读，登录页面将隐藏对应入口。

## 后端 API

### 通用设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/settings/general` | 获取通用配置 |
| POST | `/api/v1/settings/general` | 更新通用配置 |

### 登录设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/settings/login` | 获取登录配置 |
| POST | `/api/v1/settings/login` | 更新登录配置 |

### 请求示例

**更新通用设置**

```json
POST /api/v1/settings/general
{
  "site_name": "我的系统",
  "site_desc": "企业级管理平台",
  "logo": "https://example.com/logo.png",
  "default_lang": "zh-CN",
  "enable_email": true,
  "copyright": "© 2026 MyCompany",
  "icp": "京ICP备XXXXXXXX号"
}
```

**更新登录设置**

```json
POST /api/v1/settings/login
{
  "qq": {
    "enabled": true,
    "app_id": "123456",
    "app_key": "xxxxxxxx",
    "redirect_uri": "https://example.com/api/v1/auth/qq/callback"
  },
  "wechat": {
    "enabled": false,
    "app_id": "",
    "app_secret": "",
    "redirect_uri": ""
  }
}
```

## 配置存储

所有设置存储在 INI 配置文件中（`backend/static/config.ini`），通过后端 API 修改后立即生效，无需重启服务。

也可以通过环境变量控制功能开关（需要重启）：

```bash
FEATURE_QQ_LOGIN=False          # 关闭 QQ 登录
FEATURE_WECHAT_LOGIN=False      # 关闭微信登录
FEATURE_EMAIL=False             # 关闭邮件发送
```

前端会查询 `/api/v1/base/features` 并根据返回值隐藏对应入口。
