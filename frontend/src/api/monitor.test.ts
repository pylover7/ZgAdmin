import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import * as monitorApi from "@/api/monitor";

describe("api/monitor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getSystemStatus calls GET /api/v1/monitor/system/status", () => {
    monitorApi.getSystemStatus();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/monitor/system/status");
  });

  it("getNetworkMonitor calls GET /api/v1/monitor/system/network without params", () => {
    monitorApi.getNetworkMonitor();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/monitor/system/network", { params: {} });
  });

  it("getNetworkMonitor calls GET /api/v1/monitor/system/network with iface param", () => {
    monitorApi.getNetworkMonitor("eth0");
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/monitor/system/network", { params: { iface: "eth0" } });
  });

  it("getDiskIOMonitor calls GET /api/v1/monitor/system/disk-io", () => {
    monitorApi.getDiskIOMonitor();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/monitor/system/disk-io");
  });
});
