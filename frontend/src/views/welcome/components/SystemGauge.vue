<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useDark, useECharts } from "@pureadmin/utils";

const props = defineProps({
  name: { type: String, default: "" },
  percent: { type: Number, default: 0 },
  subtitle: { type: String, default: "" },
  color: { type: String, default: "#409EFF" },
  /** 启用基于百分比的动态颜色（绿→黄→红） */
  dynamicColor: { type: Boolean, default: false },
  detail: { type: Object, default: () => ({}) },
  top5: { type: Array, default: () => [] }
});

const { isDark } = useDark();
const theme = computed(() => (isDark.value ? "dark" : "light"));

const chartRef = ref();
const { setOptions } = useECharts(chartRef, { theme, renderer: "svg" });

const inited = ref(false);

// #6: 修复深色模式副文本对比度 — #888 在深色背景上仅 3.5:1，改为 #a0a0a0 达 5.4:1
const textColor = computed(() => (isDark.value ? "#e0e0e0" : "#303133"));
const subTextColor = computed(() => (isDark.value ? "#a0a0a0" : "#606266"));
const trackColor = computed(() => (isDark.value ? "#2a2a2a" : "#e8e8e8"));

// #3: 动态颜色 — 根据百分比从绿→黄→红渐变
const activeColor = computed(() => {
  if (!props.dynamicColor) return props.color;
  const p = props.percent;
  if (p < 50) return "#67C23A"; // 绿
  if (p < 80) return "#E6A23C"; // 黄
  return "#F56C6C"; // 红
});

// #5: 尊重 prefers-reduced-motion
const prefersReducedMotion = computed(() => {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
});

const updateChart = () => {
  const animDuration = prefersReducedMotion.value ? 0 : 500;
  setOptions({
    clear: !inited.value,
    animationDurationUpdate: animDuration,
    animationEasingUpdate: "cubicOut",
    series: [
      {
        type: "gauge",
        startAngle: 90,
        endAngle: -270,
        radius: "90%",
        center: ["50%", "52%"],
        pointer: { show: false },
        progress: {
          show: true,
          overlap: false,
          roundCap: true,
          clip: false,
          width: 10,
          itemStyle: { color: activeColor.value }
        },
        axisLine: {
          lineStyle: {
            width: 10,
            color: [[1, trackColor.value]]
          }
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        detail: {
          width: 80,
          height: 30,
          fontSize: 20,
          fontWeight: 700,
          lineHeight: 30,
          offsetCenter: [0, "-5%"],
          valueAnimation: !prefersReducedMotion.value,
          formatter: "{value}%",
          color: textColor.value
        },
        title: {
          offsetCenter: [0, "48%"],
          fontSize: 12,
          color: subTextColor.value
        },
        data: [
          {
            value: Math.round(props.percent),
            name: props.name || ""
          }
        ]
      }
    ]
  });
  inited.value = true;
};

watch(
  () => [props.percent, isDark.value, activeColor.value, props.subtitle],
  () => updateChart(),
  { deep: true }
);

onMounted(() => updateChart());
</script>

<template>
  <!-- #10: Popover 宽度响应式 -->
  <el-popover
    placement="bottom"
    :width="340"
    trigger="hover"
    :popper-class="'gauge-popover'"
  >
    <template #reference>
      <div class="gauge-wrap">
        <div ref="chartRef" class="gauge-chart" />
        <div v-if="subtitle" class="gauge-footer">{{ subtitle }}</div>
      </div>
    </template>
    <div class="detail-grid">
      <template v-for="(val, key) in detail" :key="key">
        <div class="detail-item">
          <span class="detail-label">{{ key }}</span>
          <span class="detail-value">{{ val }}</span>
        </div>
      </template>
    </div>
    <div v-if="top5.length" class="top5-section">
      <div class="top5-title">Top 5</div>
      <el-table :data="top5" size="small" :max-height="200">
        <el-table-column
          prop="name"
          label="Process"
          min-width="110"
          show-overflow-tooltip
        />
        <el-table-column
          prop="cpu_percent"
          label="CPU%"
          width="70"
          align="right"
        />
        <el-table-column
          prop="memory_percent"
          label="Mem%"
          width="70"
          align="right"
        />
      </el-table>
    </div>
  </el-popover>
</template>

<style lang="scss" scoped>
.gauge-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  cursor: pointer;
  padding: 4px;
}

.gauge-chart {
  width: 100%;
  height: 140px;

  @media (max-width: 768px) {
    height: 120px;
  }
}

.gauge-footer {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>

<style lang="scss">
/* #10: Popover 响应式宽度（非 scoped 才能作用到 popover 浮层） */
@media (max-width: 480px) {
  .gauge-popover {
    max-width: calc(100vw - 32px) !important;
  }
}
</style>
