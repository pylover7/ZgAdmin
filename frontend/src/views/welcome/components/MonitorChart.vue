<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useDark, useECharts } from "@pureadmin/utils";
import type { HistoryPoint } from "@/api/monitor";

const props = defineProps({
  data: { type: Array as () => HistoryPoint[], default: () => [] },
  series: {
    type: Array as () => { key: string; name: string; color: string }[],
    default: () => []
  },
  unit: { type: String, default: "" },
  height: { type: String, default: "280px" }
});

const { isDark } = useDark();
const theme = computed(() => (isDark.value ? "dark" : "light"));

const chartRef = ref();
const { setOptions } = useECharts(chartRef, { theme, renderer: "svg" });

const chartInited = ref(false);

// #5: 尊重 prefers-reduced-motion
const prefersReducedMotion = computed(() => {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
});

const updateChart = () => {
  if (!props.data.length) {
    chartInited.value = false;
    return;
  }

  const animDuration = prefersReducedMotion.value ? 0 : 300;

  const seriesList = props.series.map(s => ({
    name: s.name,
    type: "line",
    smooth: true,
    symbol: "none",
    areaStyle: {
      opacity: 0.15,
      color: s.color
    },
    lineStyle: {
      width: 2,
      color: s.color
    },
    itemStyle: { color: s.color },
    data: props.data.map(p => [p.time, p[s.key] ?? 0])
  }));

  setOptions({
    clear: !chartInited.value,
    animationDurationUpdate: animDuration,
    animationEasingUpdate: "linear",
    tooltip: {
      trigger: "axis",
      backgroundColor: isDark.value
        ? "rgba(30,30,30,0.9)"
        : "rgba(255,255,255,0.95)",
      borderColor: isDark.value ? "#444" : "#ddd",
      textStyle: { color: isDark.value ? "#e0e0e0" : "#303133", fontSize: 12 },
      formatter: (params: any[]) => {
        const d = new Date(params[0]?.value?.[0] ?? params[0]?.axisValue);
        const timeStr = `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}:${d.getSeconds().toString().padStart(2, "0")}`;
        let html = `<div style="font-weight:600;margin-bottom:4px">${timeStr}</div>`;
        params.forEach(p => {
          const raw = p.value?.[1] ?? p.value;
          const val =
            typeof raw === "number"
              ? raw >= 1048576
                ? (raw / 1048576).toFixed(1) + " MB/s"
                : raw >= 1024
                  ? (raw / 1024).toFixed(1) + " KB/s"
                  : raw.toFixed(1) + " B/s"
              : raw;
          html += `<div style="display:flex;align-items:center;gap:6px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
            ${p.seriesName}: <b>${val}</b></div>`;
        });
        return html;
      }
    },
    legend: {
      show: seriesList.length > 1,
      bottom: 0,
      textStyle: { color: isDark.value ? "#a0a0a0" : "#606266", fontSize: 12 }
    },
    grid: {
      top: 16,
      left: 10,
      right: 16,
      bottom: seriesList.length > 1 ? 32 : 8,
      containLabel: true
    },
    xAxis: {
      type: "time",
      axisLine: { lineStyle: { color: isDark.value ? "#444" : "#ddd" } },
      axisLabel: {
        color: isDark.value ? "#a0a0a0" : "#999",
        fontSize: 10,
        formatter: (ts: number) => {
          const d = new Date(ts);
          return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
        }
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: isDark.value ? "#a0a0a0" : "#999",
        fontSize: 10,
        formatter: (v: number) => {
          if (v >= 1048576) return (v / 1048576).toFixed(0) + "MB";
          if (v >= 1024) return (v / 1024).toFixed(0) + "KB";
          return v.toFixed(0) + "B";
        }
      },
      splitLine: {
        lineStyle: { color: isDark.value ? "#333" : "#f0f0f0" }
      }
    },
    series: seriesList as any
  });
  chartInited.value = true;
};

watch(
  () => [props.data, props.series, isDark.value],
  () => updateChart(),
  { deep: true }
);

onMounted(() => updateChart());
</script>

<template>
  <div class="monitor-chart-wrap">
    <!-- #7: 空状态反馈 -->
    <div v-if="!data.length" class="chart-empty" :style="{ height }">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="40"
        height="40"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="empty-icon"
      >
        <path d="M3 3v18h18" />
        <path d="M7 16l4-8 4 4 4-6" opacity="0.4" />
      </svg>
      <span class="empty-text">No data yet</span>
    </div>
    <div
      v-show="data.length"
      ref="chartRef"
      :style="{ width: '100%', height }"
    />
  </div>
</template>

<style lang="scss" scoped>
.monitor-chart-wrap {
  position: relative;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;

  /* height 移至模板 :style 绑定 */
  color: var(--el-text-color-secondary);
}

.empty-icon {
  opacity: 0.4;
}

.empty-text {
  font-size: 13px;
  opacity: 0.6;
}
</style>
