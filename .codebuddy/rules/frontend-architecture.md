# 前端架构（Frontend）

> 前端开发时，请先加载 `frontend-components` Skill（组件/样式/指令手册）和 `frontend-patterns` Skill（可复用页面模式）。
> 详细架构说明见 `.codebuddy/skills/frontend-components/references/architecture.md`。

## 前端编码规范速查

1. **Composition API**：全部使用 `<script setup>` + TypeScript
2. **页面 Hook 模式**：页面逻辑抽取到 `utils/hook.tsx`，返回响应式数据和方法
3. **API 封装**：所有 API 调用封装在 `src/api/` 下，不在组件中直接调用 Axios
4. **类型安全**：API 响应使用 `Result`/`ResultTable` 等泛型类型
5. **国际化**：菜单标题使用 i18n 键名（如 `menus.pureUser`），通过 `transformI18n` 自动翻译
6. **组件选型优先级**：开发前端功能时，必须按以下顺序选型——① pure-admin 体系复用组件/工具（Re* 组件、`@pureadmin/table`、`@pureadmin/descriptions`、`@pureadmin/utils`、自定义指令、预集成第三方库） → ② Element Plus 组件 → ③ 自行实现
7. **状态管理**：Pinia，Store 定义在 `src/store/modules/` 下
8. **慎用 try/catch**：非必要不使用 try 语句，优先通过完整的条件判断、可选链（`?.`）、空值合并（`??`）、类型守卫等方式保证代码健壮性
9. **样式零自定义原则**：业务页面 `<style scoped>` 应为空，优先使用 Tailwind 工具类（`flex-c`/`flex-bc`/`bg-bg_color`/`text-primary` 等）、Element Plus 辅助类（`.pure-popper`/`.pure-scrollbar`/`.reset-margin`）、全局 CSS 变量（`var(--pure-border-color)` 等），严禁在业务页面写自定义 CSS
10. **参考 pure-admin 文档**：开发前端功能时，务必先查阅 [pure-admin 官方文档](https://github.com/pure-admin/pure-admin-doc)，了解框架已提供的组件、Hooks、工具函数
11. **UI 设计参考 `ui-ux-pro-max` Skill**：涉及页面布局、交互设计、组件选型等 UI/UX 决策时，应加载 `ui-ux-pro-max` Skill

## 关键模板规则

### 单一根节点

所有路由页面组件的 `<template>` **必须只有一个根元素**，用 `<div>` 包裹全部内容。

原因：布局组件使用 `<Transition>` 包裹 `<router-view>`，要求子组件为单根节点。ESLint 已自动强制。

### 表格自适应高度

`<pure-table adaptive>` 必须使用 `inject<ComputedRef<AdaptiveConfig>>("adaptiveConfig")` 获取配置，**禁止硬编码**对象字面量。ESLint 已自动强制。

## 添加新前端页面

1. 在 `src/views/` 创建页面目录和组件
2. 在 `src/api/` 创建 API 封装
3. 在 `backend/app/seed/data/menus.py` 添加菜单项（使用 i18n 键名）
4. 在 `locales/zh-CN.yaml` 和 `locales/en.yaml` 添加翻译
5. 后端重启后菜单自动同步到前端
