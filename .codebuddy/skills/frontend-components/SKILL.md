---
name: frontend-components
description: 前端公共组件库、样式体系、自定义指令的完整使用手册。开发前端页面/组件时加载。
---

# 前端组件、样式与指令手册

## ⚠️ 总体原则：组件/工具选型优先级

开发前端功能时，**必须**按以下顺序检查可用方案，严禁跳级造轮子：

| 优先级 | 检查来源 | 说明 |
|--------|---------|------|
| **1（最高）** | **pure-admin 体系复用组件/工具** | 本文档列出的 Re* 组件、`@pureadmin/table`、`@pureadmin/descriptions`、`@pureadmin/utils`、自定义指令、预集成第三方库 |
| **2** | **Element Plus 组件** | 确认 pure-admin 体系没有封装后，再使用 Element Plus 原生组件 |
| **3（最低）** | **自行实现** | 仅当以上两级都无法满足时，才考虑自己实现。实现前需说明理由 |

> **参考**：[pure-admin 官方文档](https://github.com/pure-admin/pure-admin-doc) | [pure-admin 演示站组件页](https://pure-admin.github.io/vue-pure-admin/#/components/statistic)

---

## 一、公共组件库（Re* 系列）

### 布局与容器

#### ReCol

**路径**：`components/ReCol/`

响应式列组件，封装 el-col 统一所有断点。

```vue
<ReCol :value="6">内容</ReCol>
<!-- 等同于 xs=6, sm=6, md=6, lg=6, xl=6 -->
```

**Props**：
| Prop | 类型 | 说明 |
|------|------|------|
| `value` | `number` | 统一所有断点的列数（0-24） |

---

#### ReSplitPane

**路径**：`components/ReSplitPane/`

可拖拽分割面板，支持水平/垂直分割。

```vue
<SplitPane :splitSet="{ split: 'vertical', defaultPercent: 30, minPercent: 20 }">
  <template #paneL>左侧内容</template>
  <template #paneR>右侧内容</template>
</SplitPane>
```

**Props**：
| Prop | 类型 | 说明 |
|------|------|------|
| `splitSet.split` | `'vertical' \| 'horizontal'` | 分割方向 |
| `splitSet.defaultPercent` | `number` | 默认分割百分比 |
| `splitSet.minPercent` | `number` | 最小分割百分比 |

**Slots**：`#paneL`（左/上）、`#paneR`（右/下）

---

### 对话框与抽屉（命令式调用）

#### ReDialog

**路径**：`components/ReDialog/`

命令式对话框，支持多弹窗叠加、自定义渲染器、全屏、Loading。

**核心 API**：

```typescript
import { addDialog, closeDialog, closeAllDialog } from "@/components/ReDialog";

// 打开对话框
addDialog({
  title: "标题",
  contentRenderer: ({ options, formData }) => <MyFormComponent formData={formData} />,
  beforeSure: (done, { options }) => {
    // 确认回调，done() 关闭对话框
  },
  beforeCancel: (done) => {
    // 取消回调
  },
  props: { /* 传递给 contentRenderer 组件的 props */ },
  width: "50%",
  fullscreen: false,
  closeOnClickModal: false,
  hideFooter: false,
  headerRenderer: () => <CustomHeader />,  // 自定义头部
  footerRenderer: ({ options, index }) => <CustomFooter />,  // 自定义底部
});

closeDialog();      // 关闭最上层对话框
closeAllDialog();   // 关闭所有对话框
```

**addDialog 参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `title` | `string` | 对话框标题 |
| `contentRenderer` | `Function` | 内容渲染函数，接收 `{ options, formData }` |
| `beforeSure` | `Function` | 确认回调，接收 `(done, { options })` |
| `beforeCancel` | `Function` | 取消回调，接收 `(done)` |
| `props` | `object` | 传递给 contentRenderer 的 props |
| `width` | `string` | 宽度，默认 `"40%"` |
| `fullscreen` | `boolean` | 是否全屏 |
| `closeOnClickModal` | `boolean` | 点击遮罩关闭 |
| `hideFooter` | `boolean` | 隐藏底部按钮 |
| `headerRenderer` | `Function` | 自定义头部渲染 |
| `footerRenderer` | `Function` | 自定义底部渲染 |

---

#### ReDrawer

**路径**：`components/ReDrawer/`

命令式抽屉，API 与 ReDialog 一致。

```typescript
import { addDrawer, closeDrawer } from "@/components/ReDrawer";

addDrawer({
  title: "标题",
  direction: "rtl",  // rtl / ltr / ttb / btt
  contentRenderer: ({ options }) => <MyComponent />,
  beforeSure: (done) => { /* ... */ },
});
```

**addDrawer 额外参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `direction` | `'rtl' \| 'ltr' \| 'ttb' \| 'btt'` | 抽屉方向，默认 `'rtl'` |
| `size` | `string` | 抽屉宽度/高度，默认 `"40%"` |

---

### 表格工具栏

#### RePureTableBar

**路径**：`components/RePureTableBar/`

Element Plus Table 工具栏：刷新、密度切换、列设置（拖拽排序/显隐/固定）、全屏。

```vue
<PureTableBar :columns="columns" @refresh="onRefresh">
  <template #buttons>
    <el-button type="primary">新增</el-button>
  </template>
  <template #default="{ size, dynamicColumns }">
    <pure-table :columns="dynamicColumns" :size="size" :data="tableData" />
  </template>
</PureTableBar>
```

**Props**：
| Prop | 类型 | 说明 |
|------|------|------|
| `columns` | `array` | 表格列配置 |
| `tableRef` | `ref` | 表格实例 ref（用于全屏） |

**Events**：`@refresh` — 点击刷新按钮触发

**Slots**：
| 插槽 | 作用域参数 | 说明 |
|------|-----------|------|
| `#buttons` | — | 工具栏左侧按钮区域 |
| `#default` | `{ size, dynamicColumns }` | 表格区域，size 控制密度，dynamicColumns 为处理后的列 |

---

#### ReVxeTableBar

**路径**：`components/ReVxeTableBar/`

VxeTable 工具栏，与 RePureTableBar 功能类似。

```vue
<VxeTableBar :vxeTableRef="xTable" :columns="columns">
  <template #buttons>...</template>
  <template #default="{ size, dynamicColumns }">
    <vxe-table ref="xTable" :columns="dynamicColumns" :size="size" />
  </template>
</VxeTableBar>
```

---

### 权限控制

#### ReAuth

**路径**：`components/ReAuth/`

角色权限控制，有权限则渲染子内容。

```vue
<Auth :value="['admin']">仅 admin 可见</Auth>
```

**Props**：`value` — `string[]`，允许的角色列表

---

#### RePerms

**路径**：`components/RePerms/`

按钮/操作权限控制。

```vue
<Perms :value="['btn_add']">
  <el-button>新增</el-button>
</Perms>
```

**Props**：`value` — `string[]`，允许的权限标识列表

> **对比**：`v-auth`/`v-perms` 指令功能相同，但以指令方式使用。组件方式更灵活（可包裹任意内容），指令方式更简洁。

---

### 图标系统

#### ReIcon

**路径**：`components/ReIcon/`

统一图标渲染入口，自动识别图标类型（Element Plus 图标 / Iconify / 本地 SVG）。

**函数式使用**：

```typescript
import { useRenderIcon } from "@/components/ReIcon";

const icon = useRenderIcon("ep:user");  // Element Plus 图标
const icon2 = useRenderIcon("ri:home-line");  // Iconify 图标
```

**组件式使用**：

```vue
<IconifyIconOffline :icon="DownloadIcon" />  <!-- 本地 SVG -->
<IconifyIconOnline icon="ep:user" />  <!-- 在线 Iconify -->
```

#### IconSelect

**路径**：`components/ReIcon/Select.vue`

图标选择器，支持分类浏览和搜索。

```vue
<IconSelect v-model="iconName" />
```

---

### 数据展示

#### ReText

**路径**：`components/ReText/`

文本省略 + 悬停提示，基于 el-text。

```vue
<ReText :lineClamp="2">长文本内容...</ReText>
```

---

#### ReTreeLine

**路径**：`components/ReTreeLine/`

el-tree 树形连接线，在 el-tree 的 `#default` 插槽中使用。

```vue
<el-tree :data="treeData">
  <template #default="{ node, data }">
    <ReTreeLine :node="node" :data="data" />
  </template>
</el-tree>
```

---

#### ReSegmented

**路径**：`components/ReSegmented/`

分段控制器（类 Ant Design）。

```vue
<ReSegmented v-model="activeIndex" :options="[
  { label: '日', icon: 'ep:calendar' },
  { label: '周', icon: 'ep:calendar' },
  { label: '月', icon: 'ep:calendar' },
]" />
```

---

#### ReFlicker

**路径**：`components/ReFlop/`

圆点/方形闪烁动画，函数式调用。

```typescript
import { useRenderFlicker } from "@/components/ReFlop";

const flicker = useRenderFlicker({
  width: "12px",
  height: "12px",
  background: "#67C23A",
  borderRadius: "50%",  // 圆形
});
```

---

#### ReCountTo

**路径**：`components/ReCountTo/`

数字滚动动画，提供两种模式：

```vue
<!-- 普通滚动 -->
<ReNormalCountTo :startVal="0" :endVal="9999" :duration="2000" prefix="$" />

<!-- 弹跳翻牌 -->
<ReboundCountTo :startVal="0" :endVal="9999" :duration="2000" />
```

---

#### ReFlop

**路径**：`components/ReFlop/`

翻牌式时钟。

```vue
<ReFlop />
```

---

#### ReTypeit

**路径**：`components/ReTypeit/`

打字机效果，基于 typeit。

```vue
<TypeIt :options="{ strings: ['Hello', 'World'], speed: 100 }" />
```

---

### 媒体处理

#### ReCropper

**路径**：`components/ReCropper/`

图片裁剪，支持圆形/矩形、右键菜单操作。

```vue
<ReCropper src="url" :circled="true" @cropper="onCropper" />
```

**Props**：
| Prop | 类型 | 说明 |
|------|------|------|
| `src` | `string` | 图片地址 |
| `circled` | `boolean` | 圆形裁剪 |
| `aspectRatio` | `number` | 宽高比 |

**Events**：`@cropper` — 裁剪完成，返回 Blob

---

#### ReCropperPreview

**路径**：`components/ReCropperPreview/`

裁剪 + 预览，右侧 Popover 展示结果。

```vue
<ReCropperPreview imgSrc="url" @cropper="onCropper" />
```

---

#### ReQrcode

**路径**：`components/ReQrcode/`

二维码生成，支持 canvas/img、Logo 嵌套、过期遮罩。

```vue
<ReQrcode :text="'https://example.com'" :width="200" />
```

**Props**：
| Prop | 类型 | 说明 |
|------|------|------|
| `text` | `string` | 二维码内容 |
| `width` | `number` | 宽度 |
| `logo` | `string` | Logo 图片地址 |
| `tag` | `'canvas' \| 'img'` | 渲染方式 |

---

#### ReBarcode

**路径**：`components/ReBarcode/`

条形码生成。

```vue
<ReBarcode tag="canvas" text="123456789" type="CODE128" />
```

---

#### ReImageVerify

**路径**：`components/ReImageVerify/`

Canvas 图形验证码。

```vue
<ReImageVerify v-model:code="verifyCode" />
```

---

### 其他组件

#### ReAnimateSelector

**路径**：`components/ReAnimateSelector/`

animate.css 动画选择器，悬停预览。

```vue
<ReAnimateSelector v-model="animationName" />
```

---

#### ReSeamlessScroll

**路径**：`components/ReSeamlessScroll/`

无缝滚动，支持上下左右、悬停暂停。

```vue
<ReSeamlessScroll :data="list" :classOption="{ direction: 'top', step: 0.5 }">
  <div v-for="item in list">{{ item }}</div>
</ReSeamlessScroll>
```

**classOption**：
| 参数 | 说明 |
|------|------|
| `direction` | `'top' \| 'bottom' \| 'left' \| 'right'` |
| `step` | 滚动速度 |
| `hoverStop` | 悬停暂停，默认 `true` |

---

#### ReSelector

**路径**：`components/ReSelector/`

范围选择器。

```vue
<ReSelector :max="[1,2,3,4,5,6,7,8,9,10]" :echo="[2,5]" @selectedVal="onSelect" />
```

---

#### ReMap/Amap

**路径**：`components/ReMap/`

高德地图组件。

```vue
<Amap />
```

---

#### ReFlowChart

**路径**：`components/ReFlowChart/`

LogicFlow 流程图，按需导入子组件：Control、NodePanel、DataDialog。

---

## 二、样式体系与复用指南

> **核心原则**：业务页面 `<style>` 标签应为空，优先使用 Tailwind 工具类、Element Plus 组件样式和全局 CSS 变量，避免自定义样式。

### Tailwind 自定义工具类（`src/style/tailwind.css`）

| 类名 | 效果 | 使用频率 |
|------|------|----------|
| `flex-c` | flex 水平垂直居中 | 极高 |
| `flex-ac` | flex 均匀分布 + 垂直居中 | 中等 |
| `flex-bc` | flex 两端对齐 + 垂直居中 | 高 |
| `navbar-bg-hover` | 导航栏过渡 hover 效果 | 导航专用 |
| `bg-bg_color` | 页面背景色（桥接 `--el-bg-color`） | 高 |
| `text-primary` | 主题色文字（桥接 `--el-color-primary`） | 高 |
| `text-text_color_primary` | 主要文字色 | 中等 |
| `text-text_color_regular` | 常规文字色 | 中等 |

### 全局 CSS 变量（`:root` 作用域）

| 变量 | 亮色值 | 暗色值 | 用途 |
|------|--------|--------|------|
| `--pure-transition-duration` | `0.3s` | `0.3s` | 侧边栏动画时长，全局复用 |
| `--pure-border-color` | `rgb(5 5 5 / 6%)` | `rgb(253 253 253 / 12%)` | 通用边框色 |
| `--pure-switch-off-color` | `#a6a6a6` | `#ffffff3f` | Switch 关闭色 |
| `--pure-theme-menu-bg` | 由主题定义 | 由主题定义 | 菜单背景色 |
| `--pure-theme-menu-text` | 由主题定义 | 由主题定义 | 菜单文字色 |
| `--pure-theme-sub-menu-active-text` | 由主题定义 | 由主题定义 | 子菜单激活文字色 |

### Element Plus 辅助类（`src/style/element-plus.scss`）

| 类名 | 效果 | 使用方式 |
|------|------|----------|
| `.reset-margin` | 重置按钮内图标与文字间距为 2px | `<el-button class="reset-margin">` |
| `.pure-popper` | Popover 无内边距 | `<el-popover popper-class="pure-popper">` |
| `.pure-scrollbar` | 自定义滚动条（6px 宽、圆角） | `popper-class="pure-scrollbar"` 或容器 class |
| `.pure-dialog` | 自定义 Dialog 样式（关闭按钮、footer） | `<el-dialog class="pure-dialog">` |
| `.pure-message` | 自定义 ElMessage 样式 | `ElMessage({ customClass: "pure-message" })` |

### 全局功能类

| 类名 | 效果 | 作用范围 |
|------|------|----------|
| `.html-grey` | 灰色模式（100% 灰度） | 添加到 `<html>` |
| `.html-weakness` | 色弱模式（80% 反色） | 添加到 `<html>` |
| `.clearfix` | 清除浮动 | 容器 |
| `.dark` | `color-scheme: dark` | 暗色模式标识 |

### Vue 过渡动画（`src/style/transition.scss`）

| 过渡名 | 效果 | 用法 |
|--------|------|------|
| `fade` | 淡入淡出（0.28s） | `<Transition name="fade">` |
| `fade-transform` | 淡入 + 左滑入 / 淡出 + 右滑出（0.5s） | `<Transition name="fade-transform" mode="out-in">` |
| `breadcrumb` | 面包屑项滑入 + 淡入 | `<TransitionGroup name="breadcrumb">` |

### 主题系统（`src/style/theme.scss`）

8 套主题通过 `html[data-theme="xxx"]` 切换，自动覆盖 CSS 变量：

| data-theme | 主题名 | 菜单背景色 |
|------------|--------|------------|
| `light` | 亮白色 | `#fff` |
| `default` | 道奇蓝 | `#001529` |
| `saucePurple` | 深紫罗兰色 | `#130824` |
| `pink` | 深粉色 | `#28081a` |
| `dusk` | 猩红色 | `#2a0608` |
| `volcano` | 橙红色 | `#2b0e05` |
| `mingQing` | 绿宝石 | `#032121` |
| `auroraGreen` | 酸橙绿 | `#0b1e15` |

### 业务页面样式编写原则

1. **优先 Tailwind**：间距、字体、颜色、布局全部用 Tailwind 类完成
2. **使用 `flex-c` / `flex-bc` / `flex-ac`**：居中、两端对齐等布局场景
3. **使用全局 CSS 变量**：`var(--pure-border-color)` 等保证主题适配
4. **使用 Element Plus 辅助类**：`.pure-popper`、`.pure-scrollbar`、`.reset-margin`
5. **禁止在业务页面写自定义样式**：目标 `<style scoped>` 标签内容为空
6. **确实需要自定义样式时**：先检查是否可用 Tailwind/Element Plus/全局变量解决，仍不行再写

---

## 三、自定义指令

### v-auth — 角色权限控制

无权限移除 DOM 元素。

```vue
<div v-auth="['admin']">仅 admin 可见</div>
```

**值**：`string[]` — 允许的角色列表

---

### v-perms — 按钮/操作权限控制

无权限移除 DOM 元素。

```vue
<el-button v-perms="['btn_add']">新增</el-button>
```

**值**：`string[]` — 允许的权限标识列表

---

### v-copy — 文本复制

默认双击复制，支持单击复制。

```vue
<span v-copy="text">双击复制</span>
<span v-copy:click="text">单击复制</span>
```

**值**：`string` — 要复制的文本
**修饰符**：`click` — 改为单击触发

---

### v-longpress — 长按触发

```vue
<button v-longpress="handler">默认 500ms</button>
<button v-longpress:2000="handler">自定义 2000ms</button>
<button v-longpress:1000:200="handler">1000ms 触发，200ms 间隔重复</button>
```

**值**：`Function` — 长按回调
**修饰符**：第一个数字为触发时长（ms），第二个为重复间隔（ms）

---

### v-optimize — 防抖/节流

```vue
<!-- 防抖（默认） -->
<button v-optimize="{ event: 'click', fn: submit }">提交</button>
<!-- 节流 -->
<input v-optimize:throttle="{ event: 'input', fn: search, timeout: 500 }" />
```

**值**：`{ event: string, fn: Function, timeout?: number }`
**修饰符**：`throttle` — 改为节流模式（默认防抖）

---

### v-ripple — 水波纹点击效果

```vue
<button v-ripple>默认</button>
<button v-ripple.center>居中</button>
<button v-ripple.circle>圆形</button>
<button v-ripple="{ class: 'text-gray-300' }">自定义颜色</button>
```

**修饰符**：`center` — 居中扩散、`circle` — 圆形
**值**：`{ class?: string }` — 自定义水波纹样式

---

## 四、pure-admin 增强组件

> 这些组件由 pure-admin 官方团队封装，已在项目中全局注册，直接使用即可。

### PureTable（@pureadmin/table）

**安装**：已在 `main.ts` 中全局注册，无需单独 import

二次封装 Element Plus Table，核心改进：**列配置从模板移到 JS/TS**，支持 `cellRenderer`/`headerRenderer`（JSX）、内置分页、加载动画、自适应高度。

```vue
<pure-table
  :columns="columns"
  :data="tableData"
  :pagination="pagination"
  :loading="loading"
  adaptive
  :adaptiveConfig="{ offsetBottom: 96 }"
/>
```

**核心类型**：

```typescript
import type { TableColumns, PaginationProps } from "@pureadmin/table";
```

#### TableColumns（扩展 el-table-column）

| 属性 | 类型 | 说明 |
|------|------|------|
| `label` | `string` | 列标题 |
| `prop` | `string` | 字段名 |
| `type` | `'selection' \| 'index' \| 'expand'` | 特殊列类型 |
| `width` | `string \| number` | 列宽 |
| `minWidth` | `string \| number` | 最小列宽 |
| `fixed` | `true \| 'left' \| 'right'` | 固定列 |
| `sortable` | `false \| true \| 'custom'` | 排序 |
| `align` | `'left' \| 'center' \| 'right'` | 对齐 |
| `hide` | `boolean \| Function` | 是否隐藏该列 |
| `cellRenderer` | `(data: TableColumnRenderer) => VNode` | 自定义单元格渲染（JSX） |
| `headerRenderer` | `(data: TableColumnRenderer) => VNode` | 自定义表头渲染（JSX） |
| `slot` | `string` | 自定义列内容插槽名 |
| `headerSlot` | `string` | 自定义表头插槽名 |
| `filterIconSlot` | `string` | 自定义 filter 图标插槽名 |
| `expandSlot` | `string` | 展开列内容插槽名 |
| `children` | `TableColumns[]` | 多级表头 |

> 其他属性与 Element Plus `el-table-column` 一致，参见 [EP 文档](https://element-plus.org/zh-CN/component/table.html#table-column-attributes)

#### PaginationProps（内置分页配置）

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pageSize` | `number` | ✅ | 每页条数 |
| `currentPage` | `number` | ✅ | 当前页码 |
| `total` | `number` | ✅ | 总条数 |
| `background` | `boolean` | | 分页按钮背景色，默认 `true` |
| `pageSizes` | `number[]` | | 每页条数选项，默认 `[5,10,15,20]` |
| `layout` | `string` | | 布局，默认 `"total, sizes, prev, pager, next, jumper"` |
| `align` | `'left' \| 'center' \| 'right'` | | 分页对齐，默认 `'right'` |
| `hideOnSinglePage` | `boolean` | | 只有一页时隐藏 |

#### LoadingConfig（加载动画）

| 属性 | 类型 | 说明 |
|------|------|------|
| `text` | `string` | 加载文案 |
| `spinner` | `string` | 自定义加载图标 |
| `svg` | `string` | 自定义 SVG 图标 |
| `background` | `string` | 遮罩颜色 |

#### AdaptiveConfig（自适应高度）

| 属性 | 类型 | 说明 |
|------|------|------|
| `offsetBottom` | `number` | 距离页面底部偏移量，默认 `96` |
| `fixHeader` | `boolean` | 是否固定表头，默认 `true` |
| `timeout` | `number` | resize 防抖时间(ms)，默认 `60` |

#### 典型用法（配合 PureTableBar）

```vue
<PureTableBar :columns="columns" @refresh="onRefresh">
  <template #buttons>
    <el-button type="primary" @click="onAdd">新增</el-button>
  </template>
  <template #default="{ size, dynamicColumns }">
    <pure-table
      :columns="dynamicColumns"
      :size="size"
      :data="tableData"
      :pagination="pagination"
      :loading="loading"
      adaptive
    />
  </template>
</PureTableBar>
```

---

### PureDescriptions（@pureadmin/descriptions）

**安装**：已在 `main.ts` 中全局注册，无需单独 import

二次封装 Element Plus Descriptions，核心改进：**项配置从模板移到 JS/TS**，支持 `cellRenderer`/`labelRenderer`。

```vue
<PureDescriptions border :data="data" :columns="columns" :column="5" />
```

#### DescriptionsColumns

| 属性 | 类型 | 说明 |
|------|------|------|
| `label` | `string` | 标签文本 |
| `prop` | `string` | 字段名（从 data 读取） |
| `value` | `string \| number` | 直接设置值（设置后 prop 失效） |
| `width` | `string \| number` | 列宽 |
| `minWidth` | `string \| number` | 最小列宽 |
| `align` | `'left' \| 'center' \| 'right'` | 对齐 |
| `hide` | `Function` | 动态隐藏 |
| `slot` | `Slots` | 自定义内容插槽 |
| `copy` | `boolean` | 是否支持点击复制 |
| `cellRenderer` | `Function` | 自定义内容渲染 |
| `labelRenderer` | `Function` | 自定义标签渲染 |

> 其他属性与 Element Plus `el-descriptions-item` 一致

---

## 五、预集成第三方库参考

> 以下库已存在于项目 `package.json` 依赖中，在需要相关功能时**优先使用**，不要另装新库。标注"未使用"的库可能是残留依赖，使用前请确认是否仍可用。

### 活跃使用

| 库 | 用途 | 参考用法 |
|----|------|---------|
| `sortablejs` | 拖拽排序 | `RePureTableBar`/`ReVxeTableBar` 内部用于列排序，`SearchHistory` 用于搜索项排序。示例：`Sortable.create(el, { animation: 300, onEnd: handler })` |
| `vue-json-pretty` | JSON 树形展示 | 日志详情页、流程图数据对话框。`<vue-json-pretty :data="obj" :deep="3" />` |
| `plus-pro-components` | 业务组件库（仅语言包） | `App.vue` 中合并其语言包到 Element Plus 国际化 |

### 依赖已安装但代码中未使用（pure-admin 演示站有参考）

| 库 | 用途 | pure-admin 演示参考 |
|----|------|---------------------|
| `@howdyjs/mouse-menu` | 右键上下文菜单 | [contextmenu 演示](https://pure-admin.github.io/vue-pure-admin/#/components/contextmenu) |
| `v-contextmenu` | 右键上下文菜单（备选） | 同上 |
| `vue-virtual-scroller` | 大数据虚拟滚动列表 | [virtual-list 演示](https://pure-admin.github.io/vue-pure-admin/#/components/virtual-list) |
| `vue-waterfall-plugin-next` | 瀑布流/瀑布图布局 | [waterfall 演示](https://pure-admin.github.io/vue-pure-admin/#/components/waterfall) |
| `swiper` | 轮播/走马灯 | [swiper 演示](https://pure-admin.github.io/vue-pure-admin/#/components/swiper) |
| `codemirror` / `codemirror-editor-vue3` | 代码编辑器 | [json-editor 演示](https://pure-admin.github.io/vue-pure-admin/#/components/json-editor) |
| `vuedraggable` | Vue 拖拽组件（sortablejs 的 Vue 封装） | 简化拖拽场景，比直接用 sortablejs 更 Vue 风格 |

### Element Plus 组件参考示例

pure-admin 演示站提供了以下 Element Plus 组件的使用示例，遇到这些场景时可先查看参考：

| 组件 | 演示页 |
|------|--------|
| el-button | button / el-button |
| el-cascader | cascader |
| el-check-tag | check-button |
| el-collapse | collapse |
| el-color-picker | color-picker / color-picker-panel |
| el-date-picker | date-picker / datetime-picker / time-picker |
| el-message | message |
| el-progress | progress |
| el-slider | slider |
| el-statistic | statistic |
| el-tag | tag |
| el-timeline | timeline |
| el-upload | upload（含高级用法：拖拽、排序、裁剪、进度） |
