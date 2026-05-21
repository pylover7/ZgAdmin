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

const prevFirstTime = ref<number | null>(null);

const updateChart = () => {
  if (!props.data.length) return;

  const firstTime = props.data[0]?.time;
  const isFirstRender = prevFirstTime.value === null;
  const isReset = !isFirstRender && prevFirstTime.value !== firstTime;

  const xData = props.data.map(p => {
    const d = new Date(p.time);
    return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}:${d.getSeconds().toString().padStart(2, "0")}`;
  });

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
    data: props.data.map(p => p[s.key] ?? 0)
  }));

  setOptions({
    clear: isFirstRender || isReset,
    animationDurationUpdate: 300,
    animationEasingUpdate: "linear",
    tooltip: {
      trigger: "axis",
      backgroundColor: isDark.value
        ? "rgba(30,30,30,0.9)"
        : "rgba(255,255,255,0.95)",
      borderColor: isDark.value ? "#444" : "#ddd",
      textStyle: { color: isDark.value ? "#e0e0e0" : "#303133", fontSize: 12 },
      formatter: (params: any[]) => {
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0]?.axisValue}</div>`;
        params.forEach(p => {
          const val =
            typeof p.value === "number"
              ? p.value >= 1048576
                ? (p.value / 1048576).toFixed(1) + " MB/s"
                : p.value >= 1024
                  ? (p.value / 1024).toFixed(1) + " KB/s"
                  : p.value.toFixed(1) + " B/s"
              : p.value;
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
      type: "category",
      data: xData,
      boundaryGap: false,
      axisLine: { lineStyle: { color: isDark.value ? "#444" : "#ddd" } },
      axisLabel: {
        color: isDark.value ? "#888" : "#999",
        fontSize: 10,
        interval: "auto" as any,
        showMaxLabel: true,
        showMinLabel: true
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: isDark.value ? "#888" : "#999",
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
  prevFirstTime.value = firstTime ?? null;
};

watch(
  () => [props.data, props.series, isDark.value],
  () => updateChart(),
  { deep: true }
);

onMounted(() => updateChart());
</script>

<template>
  <div ref="chartRef" :style="{ width: '100%', height }" />
</template>
