# 前端架构详细文档

## 技术栈

- **框架**：Vue 3（Composition API + `<script setup>`）
- **语言**：TypeScript
- **构建**：Vite 8
- **UI 库**：Element Plus
- **CSS**：Tailwind CSS 4 + SCSS
- **状态管理**：Pinia
- **路由**：Vue Router 5（History 模式）
- **HTTP**：Axios（封装在 `src/utils/http/`）
- **国际化**：vue-i18n（`locales/zh-CN.yaml`、`locales/en.yaml`）
- **包管理器**：Bun
- **基础模板**：vue-pure-admin

## 目录结构

```
frontend/src/
├── main.ts               # 应用入口
├── App.vue               # 根组件
├── api/                  # API 调用封装
│   ├── base.ts           # 初始化配置、验证码
│   ├── user.ts           # 登录、Token 刷新
│   ├── system.ts         # 用户/角色/菜单/部门/日志/API 管理
│   ├── notice.ts         # 通知管理
│   ├── settings.ts       # 通用/登录/安全设置
│   ├── monitor.ts        # 系统监控
│   ├── file.ts           # 文件上传/下载/预览/统计
│   ├── routes.ts         # 动态路由获取
│   ├── list.ts           # 列表接口
│   ├── mock.ts           # Mock 数据接口
│   └── utils.ts          # API URL 前缀工具
├── views/                # 页面视图
│   ├── login/            # 登录页（含 QQ/微信/注册组件）
│   ├── welcome/          # 首页仪表盘
│   ├── system/           # 系统管理（用户/角色/菜单/部门/通知）
│   ├── monitor/          # 系统监控（登录/操作/系统日志）
│   ├── settings/         # 系统设置（通用/登录/安全）
│   ├── resource/         # 资源管理（文件上传/管理）
│   ├── account-settings/ # 账户设置（个人信息/安全日志/偏好）
│   ├── about/            # 关于页面
│   └── error/            # 错误页（403/404/500）
├── layout/               # 布局框架
│   ├── index.vue         # 主布局
│   ├── components/       # 布局组件
│   │   ├── lay-sidebar/  # 侧边栏
│   │   ├── lay-navbar/   # 导航栏
│   │   ├── lay-tag/      # 标签页
│   │   ├── lay-notice/   # 通知铃铛（对接后端通知 API）
│   │   ├── lay-search/  # 全局搜索
│   │   ├── lay-panel/   # 面板
│   │   ├── lay-setting/ # 设置面板
│   │   └── lay-footer/  # 页脚
│   └── hooks/            # 布局相关 hooks
├── router/               # 路由
│   ├── index.ts          # 路由实例 + 守卫
│   ├── utils.ts          # 动态路由加载、菜单构建
│   └── modules/          # 静态路由模块（自动导入）
├── store/                # Pinia 状态管理
│   ├── modules/
│   │   ├── user.ts       # 用户状态（登录/登出/Token 刷新）
│   │   ├── permission.ts # 权限状态（动态路由/菜单）
│   │   ├── app.ts        # 应用全局状态
│   │   ├── multiTags.ts  # 标签页状态
│   │   ├── settings.ts   # 设置状态
│   │   └── epTheme.ts    # Element Plus 主题
│   └── types.ts          # Store 类型定义
├── components/           # 公共组件（Re* 系列）
├── config/               # 全局配置
│   └── index.ts          # platform-config.json 加载 + 后端 /base/init 合并
├── plugins/              # 插件注册
│   ├── elementPlus.ts    # Element Plus 按需注册
│   ├── i18n.ts           # 国际化
│   ├── echarts.ts        # ECharts
│   └── vxeTable.ts       # VXE Table
├── directives/           # 自定义指令（auth、perms、copy、longpress 等）
├── style/                # 全局样式（SCSS + Tailwind CSS）
├── types/                # TypeScript 类型定义
├── utils/                # 工具函数
│   ├── http/             # Axios 封装（PureHttp，Token 自动刷新）
│   ├── auth.ts           # Token 存储（Cookie + localStorage）
│   ├── message.ts        # 消息提示
│   ├── tree.ts           # 树形数据处理
│   └── sso.ts            # SSO 单点登录
└── assets/               # 静态资源（SVG、图片、图标字体）
```

## 请求层架构

**HTTP 封装**（`src/utils/http/`）：

- `PureHttp` 类封装 Axios，自动注入 Token、自动刷新过期 Token
- 请求白名单：`/refreshToken`、`/accessToken`、`/base/init`、`/base/captcha`
- Token 过期时自动调用 `refreshTokenApi` 刷新，排队等待的请求在刷新成功后重发
- 响应 401 自动登出，403 跳转错误页

**Token 存储**（`src/utils/auth.ts`）：

- `accessToken` + `refreshToken` + `expires` 存储在 Cookie（`authorized-token`）
- 用户信息（`username`、`nickname`、`roles`、`permissions`）存储在 localStorage（`user-info`）

## 路由与权限

**路由模式**：混合模式（静态路由 + 动态路由）

1. **静态路由**：`src/router/modules/` 下自动导入，登录前即可访问（如 `/login`、`/welcome`、`/about`）
2. **动态路由**：登录后调用 `getAsyncRoutes` 从后端获取菜单数据 → `initRouter()` 构建动态路由 → `router.addRoute()`

**路由守卫**（`src/router/index.ts`）：

- 已登录用户不能访问 `/login`
- 无权限页面跳转 `/error/403`
- 动态路由加载完成后自动跳转

**菜单权限**：后端返回的菜单数据中包含角色信息，前端根据用户角色过滤可访问菜单。

## 页面开发约定

### 组件选型优先级（铁律）

开发前端功能时，**必须**按以下顺序选型，严禁跳级造轮子：

1. **pure-admin 体系复用组件/工具**：Re* 组件、`@pureadmin/table`、`@pureadmin/descriptions`、`@pureadmin/utils`、自定义指令、预集成第三方库
2. **Element Plus 组件**：确认 pure-admin 体系没有封装后使用
3. **自行实现**：仅当以上两级都无法满足时

### 文件组织

每个功能页面遵循以下文件组织模式：

```
views/system/xxx/
├── index.vue       # 页面主组件
├── form.vue        # 表单弹窗组件（如有）
└── utils/
    ├── hook.tsx     # 页面逻辑 Hook（Composition API）
    ├── types.ts     # 页面类型定义
    └── rule.ts      # 表单校验规则
```

**API 调用约定**：

```typescript
// src/api/xxx.ts
const xxxUrl = (url: string) => apiV1(`/module${url}`);
export const getXxxList = (params) => http.request<ResultTable>("post", xxxUrl("/list"), { data, params });
```

**分页响应类型**：`ResultTable` = `{ code, success, msg, data, total, currentPage, pageSize }`

## 模板规则

### 单一根节点（铁律）

所有路由页面组件的 `<template>` **必须只有一个根元素**，用 `<div>` 包裹全部内容。

**原因**：布局组件 `lay-content/index.vue` 使用 `<Transition>` 包裹 `<router-view>` 渲染的路由组件，`<Transition>` 要求子组件为单根节点，多根节点（fragment）会导致 Vue 警告且动画失效。

**ESLint 自动强制**：`eslint.config.js` 中已对 `src/views/**/*.vue` 启用 `vue/no-multiple-template-root` 规则（error 级别）。非 views 目录的组件不受此限制。

### 表格自适应高度（adaptiveConfig）

`<pure-table adaptive>` 用于让表格自动撑满剩余视口高度，**禁止硬编码 `adaptiveConfig` 对象字面量**。

必须使用 `inject<ComputedRef<AdaptiveConfig>>("adaptiveConfig")` 获取。

## 配置加载流程

1. 读取 `public/platform-config.json`（静态配置：标题、主题、布局等）
2. 调用 `/api/v1/base/init` 获取后端动态配置（站点信息、功能开关、安全配置）
3. 后端配置覆盖静态配置中的对应字段
4. 最终配置通过 `getConfig()` 全局访问

## 开发行为规范

### 参考 pure-admin 文档

开发前端功能时，务必先查阅 [pure-admin 官方文档](https://github.com/pure-admin/pure-admin-doc)，了解框架已提供的组件、Hooks、工具函数，不要重新造轮子。

### UI 设计参考 `ui-ux-pro-max` Skill

涉及页面布局、交互设计、组件选型等 UI/UX 决策时，应加载 `ui-ux-pro-max` Skill 获取设计规范和最佳实践指导。
