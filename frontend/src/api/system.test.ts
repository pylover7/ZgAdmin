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
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/user/add",
      { data: { username: "test" } }
    );
  });

  it("deleteUser calls POST /api/v1/system/user/delete", () => {
    systemApi.deleteUser(["id1"]);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/user/delete",
      { data: ["id1"] }
    );
  });

  it("updateUser calls POST /api/v1/system/user/update", () => {
    systemApi.updateUser({ id: "1", username: "updated" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/user/update",
      { data: { id: "1", username: "updated" } }
    );
  });

  it("updateUserStatus calls POST /api/v1/system/user/updateStatus", () => {
    systemApi.updateUserStatus({ id: "1", is_active: true });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/user/updateStatus",
      { data: { id: "1", is_active: true } }
    );
  });

  it("getUserList calls POST /api/v1/system/user/list", () => {
    systemApi.getUserList("admin", "a@b.com", "dept1", 15, 1);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/user/list",
      expect.objectContaining({
        data: { username: "admin", email: "a@b.com", deptId: "dept1" },
        params: { pageSize: 15, currentPage: 1 }
      })
    );
  });

  it("getRoleIds calls POST /api/v1/system/user/getRolesIds", () => {
    systemApi.getRoleIds("user-1");
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/user/getRolesIds",
      { data: { id: "user-1" } }
    );
  });

  // Role APIs
  it("addRole calls POST /api/v1/system/role/add", () => {
    systemApi.addRole({ name: "role1" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/role/add",
      { data: { name: "role1" } }
    );
  });

  it("deleteRole calls POST /api/v1/system/role/delete", () => {
    systemApi.deleteRole(["r1"]);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/role/delete",
      { data: ["r1"] }
    );
  });

  it("getAllRoleList calls GET /api/v1/system/role/all", () => {
    systemApi.getAllRoleList();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/role/all");
  });

  it("getRoleList calls POST /api/v1/system/role/list", () => {
    systemApi.getRoleList("name", "code", "active", 1, 15);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/role/list",
      expect.objectContaining({
        data: { name: "name", code: "code", status: "active" },
        params: { pageSize: 15, currentPage: 1 }
      })
    );
  });

  it("getRoleAuth calls POST /api/v1/system/role/getRoleAuth", () => {
    systemApi.getRoleAuth({ id: "r1" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/role/getRoleAuth",
      { data: { id: "r1" } }
    );
  });

  it("updateRoleAuth calls POST /api/v1/system/role/updateRoleAuth", () => {
    systemApi.updateRoleAuth({ id: "r1", menus: [], apis: [] });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/role/updateRoleAuth",
      { data: { id: "r1", menus: [], apis: [] } }
    );
  });

  it("getApiList calls GET /api/v1/system/api/list", () => {
    systemApi.getApiList();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/api/list");
  });

  // Menu APIs
  it("addMenu calls POST /api/v1/system/menu/add", () => {
    systemApi.addMenu({ title: "menu1" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/menu/add",
      { data: { title: "menu1" } }
    );
  });

  it("deleteMenu calls POST /api/v1/system/menu/delete", () => {
    systemApi.deleteMenu(["m1"]);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/menu/delete",
      { data: ["m1"] }
    );
  });

  it("getMenuList calls GET /api/v1/system/menu/list", () => {
    systemApi.getMenuList();
    expect(mockRequest).toHaveBeenCalledWith(
      "get",
      "/api/v1/system/menu/list",
      { data: undefined }
    );
  });

  // Dept APIs
  it("addDept calls POST /api/v1/system/dept/add", () => {
    systemApi.addDept({ name: "dept1" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/dept/add",
      { data: { name: "dept1" } }
    );
  });

  it("deleteDept calls POST /api/v1/system/dept/delete", () => {
    systemApi.deleteDept(["d1"]);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/dept/delete",
      { data: ["d1"] }
    );
  });

  it("getDeptList calls GET /api/v1/system/dept/list", () => {
    systemApi.getDeptList();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/dept/list");
  });

  // Monitor APIs
  it("deleteLoginLogs calls POST /api/v1/monitor/logs/login/delete", () => {
    systemApi.deleteLoginLogs(["log1"]);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/monitor/logs/login/delete",
      { data: ["log1"] }
    );
  });

  it("clearLoginLogs calls GET /api/v1/monitor/logs/login/clear", () => {
    systemApi.clearLoginLogs();
    expect(mockRequest).toHaveBeenCalledWith(
      "get",
      "/api/v1/monitor/logs/login/clear"
    );
  });

  it("getSystemVersion calls GET /api/v1/system/version", () => {
    systemApi.getSystemVersion();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/system/version");
  });
});

// ─── 补充：操作日志 / 系统日志 / 版本检查 ───
import { describe as _d, it as _i, expect as _e, vi as _v } from "vitest";

_d("systemApi extra", () => {
  _i("getOperationLogsList posts to /monitor/logs/operation/list", () => {
    mockRequest.mockClear();
    systemApi.getOperationLogsList(["info"], null, 1, 15);
    _e(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/monitor/logs/operation/list",
      {
        data: { level: ["info"], operationTime: null },
        params: { pageSize: 15, currentPage: 1 }
      }
    );
  });

  _i("deleteOperationLogs posts to delete", () => {
    mockRequest.mockClear();
    systemApi.deleteOperationLogs(["o1"]);
    _e(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/monitor/logs/operation/delete",
      { data: ["o1"] }
    );
  });

  _i("clearOperationLogs gets clear", () => {
    mockRequest.mockClear();
    systemApi.clearOperationLogs();
    _e(mockRequest).toHaveBeenCalledWith(
      "get",
      "/api/v1/monitor/logs/operation/clear"
    );
  });

  _i("getSystemLogsList posts to /monitor/logs/system/list", () => {
    mockRequest.mockClear();
    systemApi.getSystemLogsList("m", null, 1, 15);
    _e(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/monitor/logs/system/list",
      {
        data: { module: "m", operationTime: null },
        params: { pageSize: 15, currentPage: 1 }
      }
    );
  });

  _i("deleteSystemLogs posts to delete", () => {
    mockRequest.mockClear();
    systemApi.deleteSystemLogs(["s1"]);
    _e(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/monitor/logs/system/delete",
      { data: ["s1"] }
    );
  });

  _i("clearSystemLogs gets clear", () => {
    mockRequest.mockClear();
    systemApi.clearSystemLogs();
    _e(mockRequest).toHaveBeenCalledWith(
      "get",
      "/api/v1/monitor/logs/system/clear"
    );
  });

  _i("checkUpdate gets check-update", () => {
    mockRequest.mockClear();
    systemApi.checkUpdate();
    _e(mockRequest).toHaveBeenCalledWith(
      "get",
      "/api/v1/system/version/check-update"
    );
  });

  _i("getLoginLogsList posts to /monitor/logs/login/list", () => {
    mockRequest.mockClear();
    systemApi.getLoginLogsList("", "", null, 1, 15);
    _e(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/monitor/logs/login/list",
      {
        data: { username: "", level: "", loginTime: null },
        params: { pageSize: 15, currentPage: 1 }
      }
    );
  });

  _i("updateDept / getApiList / getRoleIds smoke", () => {
    mockRequest.mockClear();
    systemApi.updateDept({ id: "d1" });
    systemApi.getApiList();
    systemApi.getRoleIds("u1");
    _e(mockRequest).toHaveBeenCalledTimes(3);
  });
});

_d("systemApi extra 2", () => {
  _i("updateRole / updateRoleStatus / updateMenu", () => {
    mockRequest.mockClear();
    systemApi.updateRole({ id: "r1" });
    systemApi.updateRoleStatus({ id: "r1" });
    systemApi.updateMenu({ id: "m1" });
    _e(mockRequest).toHaveBeenCalledTimes(3);
  });
});
