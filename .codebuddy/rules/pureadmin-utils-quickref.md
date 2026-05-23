# @pureadmin/utils 快速索引

> **导入方式**：`import { 函数名 } from "@pureadmin/utils"`。完整 API 详见 `pureadmin-utils` Skill。

## Vue Hooks

| Hook | 功能 |
|------|------|
| `useECharts` | ECharts 初始化与自适应 |
| `useDark` | 暗黑模式切换 |
| `useDraggable` | 元素拖拽 |
| `useWatermark` | 水印生成 |
| `useLoader` | 动态加载 CSS/JS |
| `useResizeObserver` | 监听元素尺寸 |
| `useScrollTo` | 缓动滚动 |
| `useCopyToClipboard` | 复制到剪贴板 |
| `useAttrs` | 增强的 attrs |
| `useGlobal` | Vue 全局属性 |
| `useDynamicComponent` | TSX 动态组件 |

## 金额

`addZero` `centsToDollars` `dollarsToCents` `getDecimalPlaces` `priceUppercase` `priceToThousands`

## 数组/树

`buildHierarchyTree` `handleTree` `deleteChildren` `getNodeByUniqueId` `appendFieldByUniqueId` `extractPathList` `isIncludeAllChildren` `intersection` `swapOrder` `getKeyList` `randomDivide` `arrayAllExist` `arrayAllExistDeep` `arrayAnyExist` `arrayAnyExistDeep` `extractFields`

## 克隆/比较

`clone` `cloneDeep` `deepEqual` `isEqualObject` `isEqualArray` `isEqual` `mapsEqual` `setsEqual` `hasOwnProp`

## 对象

`cleanObject` `delObjectProperty` `toSet` `shouldCleanKey` `isInvalidValue` `entries`

## 类型判断

`is` `isObject` `isPlainObject` `isDef` `isUnDef` `isNull` `isNullAndUnDef` `isNullOrUnDef` `isEmpty` `isAllEmpty` `isDate` `isLeapYear` `isNumber` `isPromise` `isString` `isFunction` `isBoolean` `isRegExp` `isArray` `isJSON` `isWindow` `isElement` `isUrl` `isPhone` `isEmail` `isQQ` `isPostCode` `hasCNChars` `isLowerCase` `isUpperCase` `isAlphabets` `isExistSpace` `isHtml` `isBase64` `isHex` `isRgb` `isRgba` `isServer` `isClient` `isBrowser`

## 字符串

`subBefore` `subAfter` `subBothSides` `subBetween` `subTextAddEllipsis` `splitNum` `hideTextAtIndex` `removeLeftSpace` `removeRightSpace` `removeBothSidesSpace` `removeAllSpace` `nameCamelize` `nameHyphenate`

## 日期

`dateFormat` `getCurrentWeek` `monthDays` `createYear` `getCurrentDate` `getTime`

## 颜色

`randomColor` `randomGradient` `hexToRgb` `rgbToHex` `darken` `lighten`

## 数学

`max` `min` `sum` `average` `numberToChinese` `exceedMathMax` `addition` `subtraction` `multiplication` `divisionOperation` `formatBytes`

## DOM/下载

`downloadByData` `downloadByOnlineUrl` `downloadByBase64` `downloadByUrl` `openLink`

## CSS 类

`hasClass` `addClass` `removeClass` `toggleClass` `getClass`

## Base64

`dataURLtoBlob` `urlToBase64` `convertImageToGray`

## 鼠标事件

`banMouseEvent` `allowMouseEvent`

## FormData

`formDataHander` `createFormData`

## 坐标转换

`bd09togcj02` `gcj02tobd09` `wgs84togcj02` `gcj02towgs84` `out_of_china`

## UUID

`buildUUID` `buildGUID` `buildPrefixUUID` `uuid`

## URL

`getLocation` `getQueryMap`

## 其他

`convertPath` `getSvgInfo` `getPerformance` `getPackageSize` `getBrowserInfo` `deviceDetection` `debounce` `throttle` `delay` `storageLocal` `storageSession` `withInstall` `withNoopInstall` `withInstallFunction` `copyTextToClipboard` `shuffleArray` `easeInOutQuad`
