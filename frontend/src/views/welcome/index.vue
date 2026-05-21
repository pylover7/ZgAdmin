<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import SystemGauge from "./components/SystemGauge.vue";
import MonitorChart from "./components/MonitorChart.vue";
import {
  getSystemStatus,
  getNetworkMonitor,
  getDiskIOMonitor,
  type SystemStatus,
  type HistoryPoint,
  type NetworkInterface,
  type DiskIODevice
} from "@/api/monitor";

defineOptions({ name: "Welcome" });

const { t } = useI18n();

// ─── 工具函数 ───
const formatBytes = (b: number) => {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (b >= 1024 && i < units.length - 1) {
    b /= 1024;
    i++;
  }
  return `${b.toFixed(2)} ${units[i]}`;
};

// ─── 加载与错误状态 (#1, #2) ───
const loading = ref(true);
const error = ref("");

// ─── 系统状态 ───
const status = reactive<SystemStatus>({
  load: { load1: 0, load5: 0, load15: 0, status: "", cores: 0, percent: 0 },
  cpu: {
    percent: 0,
    freq: "",
    per_cpu: [],
    physical_cores: 0,
    logical_cores: 0
  },
  memory: {
    percent: 0,
    total: "0",
    used: "0",
    available: "0",
    cached: "0",
    buffers: "0",
    shared: "0"
  },
  disk: { percent: 0, total: "0", used: "0", free: "0" },
  top_cpu: []
});

// ─── 监控数据 ───
const activeTab = ref("network");
const networkData = reactive<Record<string, NetworkInterface>>({});
const diskIOData = reactive<Record<string, DiskIODevice>>({});
const selectedIface = ref("");

const ifaceList = computed(() => Object.keys(networkData));
const diskList = computed(() => Object.keys(diskIOData));

// ─── 仪表盘配置 ───

const cpuDetail = computed(() => ({
  [t("system.monitor.cpuFreq")]: status.cpu.freq,
  [t("system.monitor.physicalCores")]: String(status.cpu.physical_cores),
  [t("system.monitor.logicalCores")]: String(status.cpu.logical_cores)
}));

const memDetail = computed(() => ({
  [t("system.monitor.total")]: status.memory.total,
  [t("system.monitor.used")]: status.memory.used,
  [t("system.monitor.available")]: status.memory.available,
  [t("system.monitor.cached")]: status.memory.cached,
  [t("system.monitor.buffers")]: status.memory.buffers
}));

const diskDetail = computed(() => ({
  [t("system.monitor.total")]: status.disk.total,
  [t("system.monitor.used")]: status.disk.used,
  [t("system.monitor.free")]: status.disk.free
}));

// ─── 网络图表 ───
const networkChartData = computed<HistoryPoint[]>(() => {
  if (!selectedIface.value || !networkData[selectedIface.value]) return [];
  return networkData[selectedIface.value].history || [];
});

const networkSeries = computed(() => [
  { key: "sent_speed", name: t("system.monitor.upload"), color: "#67C23A" },
  { key: "recv_speed", name: t("system.monitor.download"), color: "#409EFF" }
]);

// ─── 磁盘IO图表 ───
const selectedDisk = ref("");
const diskIOChartData = computed<HistoryPoint[]>(() => {
  if (!selectedDisk.value || !diskIOData[selectedDisk.value]) return [];
  return diskIOData[selectedDisk.value].history || [];
});

const diskIOSeries = computed(() => [
  { key: "read_speed", name: t("system.monitor.read"), color: "#E6A23C" },
  { key: "write_speed", name: t("system.monitor.write"), color: "#F56C6C" }
]);

// ─── 轮询 ───
let timer: ReturnType<typeof setInterval> | null = null;

const fetchStatus = async () => {
  try {
    const { data } = await getSystemStatus();
    if (data) {
      Object.assign(status.load, data.load);
      Object.assign(status.cpu, data.cpu);
      Object.assign(status.memory, data.memory);
      Object.assign(status.disk, data.disk);
      status.top_cpu = data.top_cpu || [];
    }
  } catch (e) {
    console.error("Failed to fetch system status", e);
    error.value = t("system.monitor.fetchError");
  }
};

const fetchNetwork = async () => {
  try {
    const { data } = await getNetworkMonitor();
    if (data) {
      Object.keys(data).forEach(k => {
        networkData[k] = data[k];
      });
      if (!selectedIface.value && Object.keys(data).length) {
        selectedIface.value = Object.keys(data)[0];
      }
    }
  } catch (e) {
    console.error("Failed to fetch network monitor", e);
  }
};

const fetchDiskIO = async () => {
  try {
    const { data } = await getDiskIOMonitor();
    if (data) {
      Object.keys(data).forEach(k => {
        diskIOData[k] = data[k];
      });
      if (!selectedDisk.value && Object.keys(data).length) {
        selectedDisk.value = Object.keys(data)[0];
      }
    }
  } catch (e) {
    console.error("Failed to fetch disk IO", e);
  }
};

const fetchAll = async () => {
  await Promise.allSettled([fetchStatus(), fetchNetwork(), fetchDiskIO()]);
  if (loading.value) loading.value = false;
};

onMounted(() => {
  fetchAll();
  timer = setInterval(fetchAll, 3000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
</script>

<template>
  <div class="monitor-dashboard">
    <!-- #2: 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      class="error-alert"
      @close="error = ''"
    />

    <!-- #1: 加载骨架屏 -->
    <div v-if="loading" class="gauge-row">
      <el-row :gutter="16">
        <el-col v-for="i in 4" :key="i" :xs="12" :sm="12" :md="6">
          <el-card shadow="hover" class="gauge-card-wrap">
            <div class="skeleton-gauge">
              <div class="skeleton-bar skeleton-animate" style="width: 60px" />
              <div class="skeleton-circle skeleton-animate" />
              <div class="skeleton-bar skeleton-animate" style="width: 80px" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 系统状态区 -->
    <template v-else>
      <div class="section-title">
        <span class="section-bar" />
        <span class="section-label">{{
          t("system.monitor.systemStatus")
        }}</span>
      </div>
      <el-row :gutter="12" class="gauge-row">
        <el-col :xs="12" :sm="12" :md="6">
          <el-card shadow="hover" class="gauge-card-wrap">
            <SystemGauge
              :name="t('system.monitor.load')"
              :percent="status.load.percent"
              :subtitle="status.load.status"
              color="#E6A23C"
              :dynamic-color="true"
              :detail="{
                [t('system.monitor.load1')]: String(status.load.load1),
                [t('system.monitor.load5')]: String(status.load.load5),
                [t('system.monitor.load15')]: String(status.load.load15),
                [t('system.monitor.cores')]: String(status.load.cores)
              }"
            />
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card shadow="hover" class="gauge-card-wrap">
            <SystemGauge
              :name="t('system.monitor.cpu')"
              :percent="status.cpu.percent"
              :subtitle="status.cpu.freq"
              color="#409EFF"
              :dynamic-color="true"
              :detail="cpuDetail"
              :top5="status.top_cpu"
            />
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card shadow="hover" class="gauge-card-wrap">
            <SystemGauge
              :name="t('system.monitor.memory')"
              :percent="status.memory.percent"
              :subtitle="`${status.memory.used} / ${status.memory.total}`"
              color="#67C23A"
              :dynamic-color="true"
              :detail="memDetail"
            />
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card shadow="hover" class="gauge-card-wrap">
            <SystemGauge
              :name="t('system.monitor.disk')"
              :percent="status.disk.percent"
              :subtitle="`${status.disk.used} / ${status.disk.total}`"
              color="#F56C6C"
              :dynamic-color="true"
              :detail="diskDetail"
            />
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 监控图表区 -->
    <div class="section-title">
      <span class="section-bar" />
      <span class="section-label">
        {{ t("system.monitor.realtimeMonitor") }}
      </span>
    </div>
    <el-card shadow="hover" class="chart-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="t('system.monitor.network')" name="network">
          <div class="chart-header">
            <el-select
              v-model="selectedIface"
              size="small"
              style="width: 140px"
            >
              <el-option
                v-for="iface in ifaceList"
                :key="iface"
                :label="iface"
                :value="iface"
              />
            </el-select>
            <span v-if="networkData[selectedIface]" class="speed-info">
              <span class="speed-badge upload">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M12 19V5" />
                  <path d="m5 12 7-7 7 7" />
                </svg>
                {{ networkData[selectedIface].sent_speed }}
              </span>
              <span class="speed-badge download">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M12 5v14" />
                  <path d="m19 12-7 7-7-7" />
                </svg>
                {{ networkData[selectedIface].recv_speed }}
              </span>
              <span class="speed-badge">
                {{ t("system.monitor.totalSent") }}:
                {{ formatBytes(networkData[selectedIface].bytes_sent) }}
              </span>
              <span class="speed-badge">
                {{ t("system.monitor.totalRecv") }}:
                {{ formatBytes(networkData[selectedIface].bytes_recv) }}
              </span>
            </span>
          </div>
          <MonitorChart
            :data="networkChartData"
            :series="networkSeries"
            height="300px"
          />
        </el-tab-pane>

        <el-tab-pane :label="t('system.monitor.diskIO')" name="disk-io">
          <div class="chart-header">
            <el-select v-model="selectedDisk" size="small" style="width: 140px">
              <el-option v-for="d in diskList" :key="d" :label="d" :value="d" />
            </el-select>
            <span v-if="diskIOData[selectedDisk]" class="speed-info">
              <span class="speed-badge read">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                </svg>
                {{ diskIOData[selectedDisk].read_speed }}
              </span>
              <span class="speed-badge write">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                </svg>
                {{ diskIOData[selectedDisk].write_speed }}
              </span>
            </span>
          </div>
          <MonitorChart
            :data="diskIOChartData"
            :series="diskIOSeries"
            height="300px"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.monitor-dashboard {
  padding: 0;
}

.error-alert {
  margin-bottom: 12px;
}

/* 区域标题 */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  margin-top: 8px;
}

.section-bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--el-color-primary);
}

.section-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.gauge-row {
  margin-bottom: 16px;
}

/* #1: 加载骨架屏 */
.skeleton-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
}

.skeleton-bar {
  height: 16px;
  border-radius: 4px;
  background: var(--el-fill-color);
}

.skeleton-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--el-fill-color);
}

.skeleton-animate {
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-animate {
    animation: none;
    opacity: 0.6;
  }
}

.gauge-card-wrap {
  border: none;
  background: var(--el-fill-color-light);

  :deep(.el-card__body) {
    padding: 10px 6px 8px;
    display: flex;
    justify-content: center;
  }
}

.chart-card {
  border: none;
  background: var(--el-fill-color-light);

  :deep(.el-card__body) {
    padding: 12px 16px;
  }
}

.chart-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.speed-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
}

.speed-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 12px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  font-weight: 500;
  white-space: nowrap;

  &.upload {
    color: #67c23a;
    background: rgba(103, 194, 58, 0.1);
  }
  &.download {
    color: #409eff;
    background: rgba(64, 158, 255, 0.1);
  }
  &.read {
    color: #e6a23c;
    background: rgba(230, 162, 60, 0.1);
  }
  &.write {
    color: #f56c6c;
    background: rgba(245, 108, 108, 0.1);
  }
}
</style>
