# 前端知识库

**生成时间:** 2026-05-05 | **提交:** 85fef5b | **分支:** feat/youhua

**PyTool 前端** — Vue 3 + TypeScript + Vite 7 + Element Plus + Tailwind CSS 4

## 目录结构
```
frontend/
├── index.html              # HTML 入口
├── src/
│   ├── main.ts             # 应用引导（插件、指令、组件注册）
│   ├── App.vue             # 根组件
│   ├── api/                # Axios 接口模块
│   ├── components/         # 可复用组件（Re* 前缀，26 个模块）
│   ├── config/             # 平台配置加载器
│   ├── directives/         # 自定义指令（auth、copy、perms、ripple 等）
│   ├── layout/             # 应用框架：侧边栏、导航栏、标签页、搜索、设置
│   ├── plugins/            # 插件初始化（ElementPlus、ECharts、i18n、vxeTable）
│   ├── router/             # Vue Router + 路由模块
│   ├── store/              # Pinia store 模块
│   ├── style/              # SCSS + Tailwind + Element Plus 覆盖
│   ├── types/              # 全局 TS 类型别名（global.d.ts）
│   ├── utils/              # HTTP 客户端、localforage、进度条、响应式
│   └── views/              # 页面视图（登录、系统管理、监控、设置等）
├── build/                  # Vite 构建工具（插件、CDN、压缩、优化、别名）
├── mock/                   # vite-plugin-fake-server Mock API
├── locales/                # 国际化：en.yaml、zh-CN.yaml
├── public/                 # 静态资源 + platform-config.json
├── .husky/                 # Git 钩子（commit-msg、pre-commit）
├── vite.config.ts          # Vite 配置（代理、别名、插件）
├── eslint.config.js        # ESLint Flat 配置（TS + Vue + Prettier）
└── package.json            # 依赖 + 脚本（bun）
```

## 从哪找
| 任务 | 位置 | 备注 |
|------|------|------|
| 应用引导 | `src/main.ts` | 插件链、异步配置加载、挂载 |
| Vite 配置 | `vite.config.ts` + `build/` | 插件、代理、CDN、优化 |
| 路由定义 | `src/router/modules/` | home、error、about、remaining |
| 状态管理 | `src/store/modules/` | app、user、permission、settings、multiTags、epTheme |
| HTTP 客户端 | `src/utils/http/` | Axios 拦截器、令牌刷新 |
| 国际化 | `src/plugins/i18n.ts` + `locales/` | vue-i18n、YAML 文案 |
| 平台配置 | `src/config/index.ts` | 加载 `public/platform-config.json` |
| 布局框架 | `src/layout/` | Frame、redirect、index + 组件 |
| 组件注册 | `src/main.ts#L36-L49` | 全局组件 + 指令注册 |
| Mock 数据 | `mock/` | 本地开发假数据 |

## 组件约定
- **Re 前缀**：所有可复用组件 — `ReDialog`、`ReAuth`、`ReIcon`、`ReCropper` 等
- **子目录模式**：`/src/ReFoo/src/` 存放实现，父级 `index.vue` 或 `index.ts` 导出
- **全局注册**：图标组件（`IconifyIconOffline`、`IconifyIconOnline`、`FontIcon`）、`Auth`、`Perms` 在 `main.ts` 中注册
- **表格组件**：`@pureadmin/table`、`vxe-table`、`RePureTableBar`、`ReVxeTableBar`
- **强制自闭合标签**：ESLint `vue/html-self-closing` 规则

## Store 约定 (Pinia)
- 模块文件放在 `src/store/modules/` — 一个模块一个领域
- 核心模块：`user`（认证状态）、`permission`（路由权限）、`multiTags`（标签页导航）、`settings`（应用偏好）、`app`（全局状态）、`epTheme`（Element Plus 主题）

## 代码检查与格式化
- **ESLint** Flat 配置 (`eslint.config.js`)：JS + TS + Vue + Prettier 集成
- **Prettier**：2 空格缩进，auto endOfLine
- **Stylelint**：SCSS + Vue + recess-order
- **TypeScript**：`strict: false`，`strictFunctionTypes: false`，`noImplicitAny: false`（宽松模式）
- **类型导入**：强制 `consistent-type-imports`（`inline-type-imports` 风格）
- **Husky + lint-staged**：提交时自动检查，commitlint 检查提交信息
- **Vue 特定**：允许多词组件名不强制、允许 v-html、不强制默认 prop 值和 emit

## 常用命令
```bash
bun dev              # 开发服务器（Vite，端口通过 .env 配置）
bun run build        # 生产构建
bun run typecheck    # tsc --noEmit + vue-tsc
bun run lint         # ESLint + Prettier + Stylelint（全部自动修复）
bun run preview      # 预览生产构建
```

## 注意事项
- 包管理器：**bun**（锁文件：`bun.lock`），非 npm/yarn
- 要求 Node ≥20.19（`engines` 字段）
- 开发代理：`/api` → `BACKEND_URL`（定义在 `build/utils.ts`）
- Vue Reactivity Transform 全局变量（`$ref`、`$computed` 等）在 ESLint 中声明 — 非标准 Vue 3 语法
- Tailwind CSS 4 通过 `@tailwindcss/vite` 插件使用（非 PostCSS 配置方式）
- `vite-plugin-fake-server` 在开发模式提供 Mock API
- `vite-plugin-cdn-import` 在生产环境外置重型依赖
- `version-rocket` + `generate-version-file` 用于版本追踪
- `code-inspector-plugin` 用于开发时 IDE 源码导航
