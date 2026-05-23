---
name: frontend-patterns
description: vue-pure-admin 可复用页面模式参考。需要参考已有页面模式开发新页面时加载。
---

# vue-pure-admin 可复用页面模式

> **用途**：开发新页面时，优先参考这些已验证的模式，避免从零设计。
> **来源**：[vue-pure-admin/src/views](https://github.com/pure-admin/vue-pure-admin/tree/main/src/views)
> **使用方式**：这些是 **vue-pure-admin 的参考实现**，不是本项目已安装的组件。需要时，去 GitHub 对应目录查看源码，复制核心逻辑到项目中，并安装所需依赖。

---

## 组件用法示例（views/components/）

| 页面 | 功能 | 实现要点 | 可能需要安装的依赖 |
|------|------|---------|-------------------|
| `contextmenu/` | 右键菜单 | 基于 `@pureadmin/components` 的 `ContextMenu` | `@pureadmin/components` |
| `upload/` | 文件上传 | el-upload + 后端接口对接 | 无额外依赖 |
| `virtual-list/` | 虚拟列表 | el-table-v2 或 `vue-virtual-scroller` | `vue-virtual-scroller` |
| `waterfall/` | 瀑布流 | CSS columns 或 `vue-waterfall-plugin-next` | `vue-waterfall-plugin-next` |
| `slider/` | 幻灯片/走马灯 | `swiper` 包 | `swiper` |
| `cascader.vue` | 级联选择器 | el-cascader 省市区联动 | 无额外依赖 |
| `check-card.vue` | 勾选卡片 | el-checkbox + 卡片样式 | 无额外依赖 |
| `color-picker.vue` | 颜色选择器 | el-color-picker | 无额外依赖 |
| `json-editor.vue` | JSON 编辑器 | `vue-json-pretty` + JSON.parse 校验 | `vue-json-pretty` |
| `statistic.vue` | 统计数值展示 | el-statistic + ReCountTo | 无额外依赖 |
| `swiper.vue` | 轮播组件 | `swiper` 包 | `swiper` |
| `timeline.vue` | 时间线 | el-timeline | 无额外依赖 |

---

## 功能能力（views/able/）

| 页面 | 功能 | 实现要点 | 可能需要安装的依赖 |
|------|------|---------|-------------------|
| `print/` | 打印功能 | `print-js` | `print-js` |
| `video-frame/` | 视频帧截取 | canvas drawImage + video seek | 无额外依赖 |
| `wavesurfer/` | 音频波形可视化 | `wavesurfer.js` | `wavesurfer.js` |
| `debounce.vue` | 防抖用法 | `@pureadmin/utils` 的 `debounce` | 无额外依赖 |
| `download.vue` | 文件下载 | `@pureadmin/utils` 的 `downloadByData` | 无额外依赖 |
| `draggable.vue` | 拖拽排序 | `vuedraggable` / `sortablejs` | `vuedraggable` |
| `excel.vue` | Excel 导入导出 | `xlsx` + `@pureadmin/utils` 的 `downloadByData` | `xlsx` |
| `infinite-scroll.vue` | 无限滚动 | el-table 的 `v-infinite-scroll` | 无额外依赖 |
| `pdf.vue` | PDF 预览 | `vue-pdf-embed` | `vue-pdf-embed` |
| `pinyin.vue` | 拼音转换 | `@pureadmin/utils` 的 `pinyin` | 无额外依赖 |
| `sensitive.vue` | 敏感词过滤 | 自定义 Trie 树匹配 | 无额外依赖 |
| `video.vue` | 视频播放 | `@videojs-player/vue` | `video.js` |
| `watermark.vue` | 水印 | `@pureadmin/utils` 的 `useWatermark` | 无额外依赖 |

---

## 表格模式（views/table/）

| 模式 | 功能 | 实现要点 |
|------|------|---------|
| `base/` | 基础表格 | el-table + 分页，参考本项目已有页面 |
| `edit/` | 可编辑表格 | el-table + el-input/el-select 行内编辑 + 保存逻辑 |
| `high/` | 高级表格 | 配合 `RePureTableBar`（工具栏+列设置+全屏），参考本项目已有页面 |
| `virtual/` | 虚拟滚动表格 | `vxe-table` 虚拟滚动或 el-table-v2，万行级别 |

---

## 结果页模式（views/result/）

| 页面 | 功能 | 实现要点 |
|------|------|---------|
| `success.vue` | 操作成功结果页 | el-result icon="success" + 描述 + 操作按钮 |
| `fail.vue` | 操作失败结果页 | el-result icon="error" + 描述 + 操作按钮 |

---

## Schema 表单（views/schema-form/）

| 页面 | 功能 | 实现要点 |
|------|------|---------|
| `index.vue` | Schema 驱动动态表单 | JSON Schema → 动态渲染 el-form-item，参考 [pure-admin 文档](https://pure-admin.cn/) |
