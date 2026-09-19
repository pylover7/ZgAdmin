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
12. **`dangerouslyUseHTMLString` 只允许在消息体确实含 HTML 标签时开启**：该开关会绕过 Vue 默认转义，把消息体当 HTML 解析。
    - **判据**：**去掉该开关后消息渲染是否变形**——不变形 = 该开关是多余的，**必须删除**（`ElMessageBox` / `ElNotification` 的纯文本消息一律禁止开启）。
    - **能用「结构性消除」就不要用「约定性防御」**：「删掉危险能力」严格优于「小心翼翼地使用危险能力」——**没有开关就没有被误开的可能**。
    - **确需 HTML 时**（如消息体含 `<a>` / `<code>`）：**保留开关，且每一个动态插入值都必须经 `escapeHtml`（`@/utils/escapeHtml`）转义**，禁止直接拼 `row.xxx` 等原始值。
13. **HTML 转义统一走 `@/utils/escapeHtml`，禁止在业务页面自建副本**：转义的**完备性取决于值所处的上下文**，不取决于「有没有调用转义函数」。自建副本极易写出「对当前上下文够用、换上下文即失效」的残缺集合。
    - 共享工具 `escapeHtml`（转义 `& < > " '`）的**适用边界**：✅ 文本节点 / ⚠️ 带引号属性（可阻断闭合，但**伪协议如 `javascript:` 不在转义范围内**，调用方须另行校验协议）/ ❌ 不带引号属性 / ❌ 执行上下文。
    - **属性上下文（`href` / `src`）必须用 `escapeForHtml(value, { isUrl: true })`**：它先做协议白名单校验（仅 `http` / `https` / 站内相对路径），再转义；不安全则返回空串。**「转义了就等于安全」是错的**——`href="javascript:alert(1)"` 转义后依然可点击执行。
    - **需要更强保证时改用 DOM API**（`textContent` / `setAttribute`），让浏览器负责转义，而不是自己拼字符串。`ElMessageBox` / `ElNotification` 的 `message` 只接受字符串、做不到这一点，故上述协议校验不可省。
    - **判据**：安全工具的价值不仅在于「功能正确」，还在于「**边界清晰**」——没有标注适用边界的转义函数，在被移动到新上下文时会**静默失效**。

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
