<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useDark, useECharts } from "@pureadmin/utils";

const props = defineProps({
  name: { type: String, default: "" },
  percent: { type: Number, default: 0 },
  subtitle: { type: String, default: "" },
  color: { type: String, default: "#409EFF" },
  detail: { type: Object, default: () => ({}) },
  top5: { type: Array, default: () => [] }
});

const { isDark } = useDark();
const theme = computed(() => (isDark.value ? "dark" : "light"));

const chartRef = ref();
const { setOptions } = useECharts(chartRef, { theme, renderer: "svg" });

const inited = ref(false);
const textColor = computed(() => (isDark.value ? "#e0e0e0" : "#303133"));
const subTextColor = computed(() => (isDark.value ? "#888" : "#606266"));
const trackColor = computed(() => (isDark.value ? "#2a2a2a" : "#e8e8e8"));

const updateChart = () => {
  setOptions({
    clear: !inited.value,
    animationDurationUpdate: 500,
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
          width: 14,
          itemStyle: { color: props.color }
        },
        axisLine: {
          lineStyle: {
            width: 14,
            color: [[1, trackColor.value]]
          }
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        detail: {
          width: 80,
          height: 36,
          fontSize: 30,
          fontWeight: 700,
          lineHeight: 36,
          offsetCenter: [0, "-8%"],
          valueAnimation: true,
          formatter: "{value}%",
          color: textColor.value
        },
        title: {
          offsetCenter: [0, "60%"],
          fontSize: 13,
          color: subTextColor.value
        },
        data: [
          {
            value: Math.round(props.percent),
            name: props.subtitle || ""
          }
        ]
      }
    ]
  });
  inited.value = true;
};

watch(
  () => [props.percent, isDark.value, props.color, props.subtitle],
  () => updateChart(),
  { deep: true }
);

onMounted(() => updateChart());
</script>

<template>
  <el-popover placement="bottom" :width="340" trigger="hover">
    <template #reference>
      <div class="gauge-wrap">
        <div class="gauge-name">{{ name }}</div>
        <div ref="chartRef" class="gauge-chart" />
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

.gauge-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 2px;
}

.gauge-chart {
  width: 100%;
  height: 190px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.detail-label {
  color: var(--el-text-color-secondary);
}

.detail-value {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.top5-section {
  margin-top: 10px;
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 8px;
}

.top5-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--el-text-color-primary);
}
</style>
