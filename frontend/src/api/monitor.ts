import { http } from "@/utils/http";
import { apiV1 } from "./utils";

const monitorUrl = (url: string) => apiV1(`/monitor/system${url}`);

type Result = {
  code: number;
  msg: string;
  success: boolean;
  data?: any;
};

// ─── 类型定义 ───

export interface LoadInfo {
  load1: number;
  load5: number;
  load15: number;
  status: string;
  cores: number;
  percent: number;
}

export interface CpuInfo {
  percent: number;
  freq: string;
  per_cpu: number[];
  physical_cores: number;
  logical_cores: number;
}

export interface MemoryInfo {
  percent: number;
  total: string;
  used: string;
  available: string;
  cached: string;
  buffers: string;
  shared: string;
}

export interface DiskInfo {
  percent: number;
  total: string;
  used: string;
  free: string;
}

export interface ProcessItem {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
}

export interface SystemStatus {
  load: LoadInfo;
  cpu: CpuInfo;
  memory: MemoryInfo;
  disk: DiskInfo;
  top_cpu: ProcessItem[];
}

export interface HistoryPoint {
  time: number;
  [key: string]: number;
}

export interface NetworkInterface {
  bytes_sent: number;
  bytes_recv: number;
  sent_speed: string;
  recv_speed: string;
  sent_speed_raw: number;
  recv_speed_raw: number;
  history: HistoryPoint[];
}

export interface DiskIODevice {
  read_bytes: number;
  write_bytes: number;
  read_speed: string;
  write_speed: string;
  read_speed_raw: number;
  write_speed_raw: number;
  history: HistoryPoint[];
}

// ─── API 函数 ───

/** 获取系统状态（负载/CPU/内存/磁盘） */
export const getSystemStatus = () => {
  return http.request<Result>("get", monitorUrl("/status"));
};

/** 获取网络监控数据 */
export const getNetworkMonitor = (iface?: string) => {
  const params = iface ? { iface } : {};
  return http.request<Result>("get", monitorUrl("/network"), { params });
};

/** 获取磁盘IO监控数据 */
export const getDiskIOMonitor = () => {
  return http.request<Result>("get", monitorUrl("/disk-io"));
};
