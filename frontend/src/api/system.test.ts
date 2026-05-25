import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import * as systemApi from "@/api/system";

describe("api/system", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // User APIs
  it("addUser calls POST /api/v1/system/user/add", () => {
    systemApi.addUser({ username: "test" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/user/add", { data: { username: "test" } });
  });

  it("deleteUser calls POST /api/v1/system/user/delete", () => {
    systemApi.deleteUser(["id1"]);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/user/delete", { data: ["id1"] });
  });

  it("updateUser calls POST /api/v1/system/user/update", () => {
    systemApi.updateUser({ id: "1", username: "updated" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/user/update", { data: { id: "1", username: "updated" } });
  });

  it("updateUserStatus calls POST /api/v1/system/user/updateStatus", () => {
    systemApi.updateUserStatus({ id: "1", is_active: true });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/user/updateStatus", { data: { id: "1", is_active: true } });
  });

  it("getUserList calls POST /api/v1/system/user/list", () => {
    systemApi.getUserList("admin", "a@b.com", "dept1", 15, 1);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/user/list", expect.objectContaining({
      data: { username: "admin", email: "a@b.com", deptId: "dept1" },
      params: { pageSize: 15, currentPage: 1 }
    }));
  });

  it("getRoleIds calls POST /api/v1/system/user/getRolesIds", () => {
    systemApi.getRoleIds("user-1");
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/user/getRolesIds", { data: { id: "user-1" } });
  });

  // Role APIs
  it("addRole calls POST /api/v1/system/role/add", () => {
    systemApi.addRole({ name: "role1" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/role/add", { data: { name: "role1" } });
  });

  it("deleteRole calls POST /api/v1/system/role/delete", () => {
    systemApi.deleteRole(["r1"]);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/role/delete", { data: ["r1"] });
  });

  it("getAllRoleList calls GET /api/v1/system/role/all", () => {
    systemApi.getAllRoleList();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/role/all");
  });

  it("getRoleList calls POST /api/v1/system/role/list", () => {
    systemApi.getRoleList("name", "code", "active", 1, 15);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/role/list", expect.objectContaining({
      data: { name: "name", code: "code", status: "active" },
      params: { pageSize: 15, currentPage: 1 }
    }));
  });

  it("getRoleAuth calls POST /api/v1/system/role/getRoleAuth", () => {
    systemApi.getRoleAuth({ id: "r1" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/role/getRoleAuth", { data: { id: "r1" } });
  });

  it("updateRoleAuth calls POST /api/v1/system/role/updateRoleAuth", () => {
    systemApi.updateRoleAuth({ id: "r1", menus: [], apis: [] });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/role/updateRoleAuth", { data: { id: "r1", menus: [], apis: [] } });
  });

  it("getApiList calls GET /api/v1/system/api/list", () => {
    systemApi.getApiList();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/api/list");
  });

  // Menu APIs
  it("addMenu calls POST /api/v1/system/menu/add", () => {
    systemApi.addMenu({ title: "menu1" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/menu/add", { data: { title: "menu1" } });
  });

  it("deleteMenu calls POST /api/v1/system/menu/delete", () => {
    systemApi.deleteMenu(["m1"]);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/menu/delete", { data: ["m1"] });
  });

  it("getMenuList calls GET /api/v1/system/menu/list", () => {
    systemApi.getMenuList();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/menu/list", { data: undefined });
  });

  // Dept APIs
  it("addDept calls POST /api/v1/system/dept/add", () => {
    systemApi.addDept({ name: "dept1" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/dept/add", { data: { name: "dept1" } });
  });

  it("deleteDept calls POST /api/v1/system/dept/delete", () => {
    systemApi.deleteDept(["d1"]);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/system/dept/delete", { data: ["d1"] });
  });

  it("getDeptList calls GET /api/v1/system/dept/list", () => {
    systemApi.getDeptList();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/dept/list");
  });

  // Monitor APIs
  it("deleteLoginLogs calls POST /api/v1/monitor/logs/login/delete", () => {
    systemApi.deleteLoginLogs(["log1"]);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/monitor/logs/login/delete", { data: ["log1"] });
  });

  it("clearLoginLogs calls GET /api/v1/monitor/logs/login/clear", () => {
    systemApi.clearLoginLogs();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/monitor/logs/login/clear");
  });

  it("getSystemVersion calls GET /api/v1/system/version", () => {
    systemApi.getSystemVersion();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/version");
  });
});
