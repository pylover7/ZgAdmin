import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  type ComputedRef
} from "vue";

export interface AdaptiveConfig {
  offsetBottom: number;
  fixHeader: boolean;
  timeout: number;
  zIndex: number;
}

/**
 * 自动计算表格 adaptive 所需的 offsetBottom。
 *
 * @pureadmin/table 的 adaptive 计算公式：
 *   height = window.innerHeight - table.getBoundingClientRect().top - offsetBottom
 *
 * getBoundingClientRect().top 已自动包含搜索栏高度，
 * offsetBottom 只需补偿表格下方到视口底部的固定元素（页脚 + 间距）。
 */
export function useTableAdaptive() {
  const footerHeight = ref(0);

  let observer: ResizeObserver | undefined;

  onMounted(() => {
    const footer = document.querySelector(".layout-footer");
    if (!footer) return;

    const update = () => {
      footerHeight.value = Math.ceil(footer.getBoundingClientRect().height);
    };
    update();

    observer = new ResizeObserver(update);
    observer.observe(footer);
  });

  onBeforeUnmount(() => {
    observer?.disconnect();
  });

  const adaptiveConfig: ComputedRef<AdaptiveConfig> = computed(() => ({
    offsetBottom: footerHeight.value + 16,
    fixHeader: true,
    timeout: 60,
    zIndex: 3
  }));

  return { adaptiveConfig };
}
