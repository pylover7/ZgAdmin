# ZgAdmin 后台管理系统 — 功能完善执行计划

- [ ] 数据库更改为 PostgreSQL
- [x] 首页监控保留半个小时数据就行了
- [x] 前端访问，终端的日志怎么不输出了
- [x] 更新脚本的实现
- [ ] 部分国际化失败（进行中，已修复核心问题，待验证）
  - **根因**：`@intlify/unplugin-vue-i18n` v11 将 YAML 叶子值编译为 AST 对象（`leafType: 'object'`），原 `getByPath` 只认 `string` 类型，导致 `transformI18n` 和 `$t` 都翻译失败
  - **修复方案**（3 处核心改动 + 11 处关联改动）：
    1. `plugins/i18n.ts` — `transformI18n` 中含 `.` 的字符串委托 `i18n.global.t()`，只有 `t()` 才能解析 AST 消息格式；不含 `.` 的视为纯文本直接返回
    2. `views/system/user/utils/hook.tsx` — `columns` 改为 `computed(() => [...])`，切换语言后表头标签重新计算
    3. `components/RePureTableBar/src/bar.tsx` — 加 `watch(columnsValue, ...)` 让 `PureTableBar` 感知 `columns` 变化并更新内部状态
    4. 11 个文件的 `zh` → `zh-CN` 统一化（必须：否则 `i18n.global.t()` 在 `"zh"` locale 下找不到 `"zh-CN"` key 的消息）
  - **改动文件清单**：
    - `frontend/public/platform-config.json` — `Locale: "zh"` → `"zh-CN"`
    - `frontend/src/App.vue` — locale 判断 `"zh"` → `"zh-CN"`
    - `frontend/src/plugins/i18n.ts` — 核心修复：`transformI18n` 委托 `t()`
    - `frontend/src/views/system/user/utils/hook.tsx` — `columns` 改 `computed`
    - `frontend/src/components/RePureTableBar/src/bar.tsx` — 响应式适配 `columns` prop
    - `frontend/src/layout/components/lay-navbar/index.vue` — locale 比较 `"zh"` → `"zh-CN"`
    - `frontend/src/layout/components/lay-search/components/SearchModal.vue` — locale 比较 `"zh"` → `"zh-CN"`
    - `frontend/src/layout/components/lay-sidebar/NavHorizontal.vue` — locale 比较 `"zh"` → `"zh-CN"`
    - `frontend/src/layout/components/lay-sidebar/NavMix.vue` — locale 比较 `"zh"` → `"zh-CN"`
    - `frontend/src/layout/hooks/useLayout.ts` — locale 默认值 `"zh"` → `"zh-CN"`
    - `frontend/src/layout/hooks/useTranslationLang.ts` — locale 赋值 `"zh"` → `"zh-CN"`
    - `frontend/src/views/login/index.vue` — locale 比较 `"zh"` → `"zh-CN"`
    - `frontend/src/utils/responsive.ts` — locale 默认值 `"zh"` → `"zh-CN"`
    - `frontend/src/utils/responsive.test.ts` — 测试数据 `"zh"` → `"zh-CN"`
  - **待验证**：切换语言后所有页面的表头、表单验证提示、菜单标题等 i18n 是否正常
