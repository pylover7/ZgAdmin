import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
  type ComputedRef
} from "vue";

export interface AdaptiveConfig {
  offsetBottom: number;
  fixHeader: boolean;
  timeout: number;
  zIndex: number;
}

/**
 * 表格 body wrapper 下方到视口底部的固定间距（不含页脚）。
 *
 * @pureadmin/table 的 adaptive 计算公式：
 *   height = window.innerHeight - tableEl.getBoundingClientRect().top - offsetBottom
 *
 * offsetBottom 需要补偿表格 body wrapper 下方所有到视口底部的空间：
 * - .main-content margin-bottom: 24px（lay-content CSS）
 * - PureTableBar pb-2: 8px
 * - el-pagination 高度: ~32px
 * - 安全余量: ~8px
 * 合计: ~72px
 */
const NON_FOOTER_BOTTOM_SPACE = 108;

/**
 * 自动计算表格 adaptive 所需的 offsetBottom。
 *
 * 工作原理：
 * 1. 布局层 provide adaptiveConfig（初始 offsetBottom = 72，不含页脚高度）
 * 2. onMounted 后测量页脚，更新 offsetBottom = footerHeight + 72
 * 3. 通过 watch 监听变化，dispatch resize 事件触发 pure-table 重算高度
 *
 * 注意：@pureadmin/table 的 adaptive 不会 watch adaptiveConfig 变化，
 * 只在 onMounted 和 window resize 时计算高度，因此需要 dispatch resize 事件。
 */
export function useTableAdaptive() {
  const footerHeight = ref(0);
  let resizeObserver: ResizeObserver | undefined;
  let mutationObserver: MutationObserver | undefined;

  const adaptiveConfig: ComputedRef<AdaptiveConfig> = computed(() => ({
    offsetBottom: footerHeight.value + NON_FOOTER_BOTTOM_SPACE,
    fixHeader: true,
    timeout: 60,
    zIndex: 3
  }));

  /** footerHeight 变化时，dispatch resize 让 pure-table 重算高度 */
  watch(footerHeight, () => {
    nextTick(() => {
      window.dispatchEvent(new Event("resize"));
    });
  });

  onMounted(() => {
    measureFooter();

    // 监听页脚的增删（hideFooter 切换时 v-if 会移除/重建 DOM）
    const scrollbar = document.querySelector(".app-main .el-scrollbar__view");
    if (scrollbar) {
      mutationObserver = new MutationObserver(() => {
        requestAnimationFrame(() => measureFooter());
      });
      mutationObserver.observe(scrollbar, { childList: true, subtree: true });
    }
  });

  onBeforeUnmount(() => {
    resizeObserver?.disconnect();
    mutationObserver?.disconnect();
  });

  function measureFooter() {
    const footer = document.querySelector(".layout-footer");
    if (!footer) {
      footerHeight.value = 0;
      resizeObserver?.disconnect();
      resizeObserver = undefined;
      return;
    }

    footerHeight.value = Math.ceil(footer.getBoundingClientRect().height);

    // 始终跟踪当前 footer 元素的高度变化
    resizeObserver?.disconnect();
    resizeObserver = new ResizeObserver(() => {
      const h = Math.ceil(footer.getBoundingClientRect().height);
      if (h !== footerHeight.value) footerHeight.value = h;
    });
    resizeObserver.observe(footer);
  }

  return { adaptiveConfig };
}
