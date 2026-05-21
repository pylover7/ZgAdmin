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

// ─── 系统状态 ───
const status = reactive<SystemStatus>({
  load: { load1: 0, load5: 0, load15: 0, status: "", cores: 0 },
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
const loadPercent = computed(() => {
  const cores = status.load.cores || 1;
  return Math.min(Math.round((status.load.load1 / cores) * 100), 100);
});

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

const networkSeries = [
  { key: "sent_speed", name: "Upload", color: "#67C23A" },
  { key: "recv_speed", name: "Download", color: "#409EFF" }
];

// ─── 磁盘IO图表 ───
const selectedDisk = ref("");
const diskIOChartData = computed<HistoryPoint[]>(() => {
  if (!selectedDisk.value || !diskIOData[selectedDisk.value]) return [];
  return diskIOData[selectedDisk.value].history || [];
});

const diskIOSeries = [
  { key: "read_speed", name: "Read", color: "#E6A23C" },
  { key: "write_speed", name: "Write", color: "#F56C6C" }
];

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

const fetchAll = () => {
  fetchStatus();
  fetchNetwork();
  fetchDiskIO();
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
    <!-- 系统状态区 -->
    <el-row :gutter="16" class="gauge-row">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="gauge-card-wrap">
          <SystemGauge
            :name="t('system.monitor.load')"
            :percent="loadPercent"
            :subtitle="status.load.status"
            color="#E6A23C"
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
            :detail="diskDetail"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 监控图表区 -->
    <el-card shadow="hover" class="chart-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="t('system.monitor.network')" name="network">
          <div class="chart-header">
            <el-select
              v-model="selectedIface"
              size="small"
              style="width: 160px"
            >
              <el-option
                v-for="iface in ifaceList"
                :key="iface"
                :label="iface"
                :value="iface"
              />
            </el-select>
            <span v-if="networkData[selectedIface]" class="speed-info">
              <span class="speed-item upload">
                ↑ {{ networkData[selectedIface].sent_speed }}
              </span>
              <span class="speed-item download">
                ↓ {{ networkData[selectedIface].recv_speed }}
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
            <el-select v-model="selectedDisk" size="small" style="width: 160px">
              <el-option v-for="d in diskList" :key="d" :label="d" :value="d" />
            </el-select>
            <span v-if="diskIOData[selectedDisk]" class="speed-info">
              <span class="speed-item read">
                R {{ diskIOData[selectedDisk].read_speed }}
              </span>
              <span class="speed-item write">
                W {{ diskIOData[selectedDisk].write_speed }}
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

.gauge-row {
  margin-bottom: 16px;
}

.gauge-card-wrap {
  :deep(.el-card__body) {
    padding: 12px 8px;
    display: flex;
    justify-content: center;
  }
}

.chart-card {
  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.speed-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  font-weight: 500;
}

.speed-item {
  &.upload {
    color: #67c23a;
  }
  &.download {
    color: #409eff;
  }
  &.read {
    color: #e6a23c;
  }
  &.write {
    color: #f56c6c;
  }
}
</style>
