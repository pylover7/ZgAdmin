import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import * as settingsApi from "@/api/settings";

describe("api/settings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getLoginConfig calls GET /api/v1/settings/login", () => {
    settingsApi.getLoginConfig();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/settings/login");
  });

  it("updateLoginConfig calls POST /api/v1/settings/login", () => {
    settingsApi.updateLoginConfig({ qq: { app_id: "1", app_key: "k", redirect_uri: "/cb", enabled: true } });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/settings/login", { data: expect.any(Object) });
  });

  it("getGeneralConfig calls GET /api/v1/settings/general", () => {
    settingsApi.getGeneralConfig();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/settings/general");
  });

  it("updateGeneralConfig calls POST /api/v1/settings/general", () => {
    settingsApi.updateGeneralConfig({ site_name: "Test" } as any);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/settings/general", { data: expect.any(Object) });
  });

  it("getSecurityPolicy calls GET /api/v1/settings/security/policy", () => {
    settingsApi.getSecurityPolicy();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/settings/security/policy");
  });

  it("updateSecurityPolicy calls POST /api/v1/settings/security/policy", () => {
    settingsApi.updateSecurityPolicy({ min_password_length: 10 });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/settings/security/policy", { data: { min_password_length: 10 } });
  });

  it("getIPRules calls GET /api/v1/settings/security/ip-rules", () => {
    settingsApi.getIPRules();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/settings/security/ip-rules");
  });

  it("addIPRule calls POST /api/v1/settings/security/ip-rules/add", () => {
    settingsApi.addIPRule({ ip_cidr: "192.168.0.0/24", rule_type: "whitelist" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/settings/security/ip-rules/add", {
      data: { ip_cidr: "192.168.0.0/24", rule_type: "whitelist" }
    });
  });

  it("updateIPRule calls POST /api/v1/settings/security/ip-rules/update", () => {
    settingsApi.updateIPRule({ id: "1", ip_cidr: "10.0.0.0/8" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/settings/security/ip-rules/update", {
      data: { id: "1", ip_cidr: "10.0.0.0/8" }
    });
  });

  it("deleteIPRules calls POST /api/v1/settings/security/ip-rules/delete", () => {
    settingsApi.deleteIPRules(["1", "2"]);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/settings/security/ip-rules/delete", {
      data: ["1", "2"]
    });
  });
});
