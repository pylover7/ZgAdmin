import { http } from "@/utils/http";
import { apiV1 } from "./utils";
import type { Result, ResultTable } from "@/types";

const systemUrl = (url: string) => apiV1(`/system${url}`);
const deptUrl = (url: string) => systemUrl(`/dept${url}`);
const munuUrl = (url: string) => systemUrl(`/menu${url}`);
const userUrl = (url: string) => systemUrl(`/user${url}`);
const roleUrl = (url: string) => systemUrl(`/role${url}`);

const monitorUrl = (url: string) => apiV1(`/monitor${url}`);
const logsUrl = (url: string) => monitorUrl(`/logs${url}`);
const loginLogsUrl = (url: string) => logsUrl(`/login${url}`);
const operationLogsUrl = (url: string) => logsUrl(`/operation${url}`);
const systemLogsUrl = (url: string) => logsUrl(`/system${url}`);

/** 新增用户 */
export const addUser = (data?: object) => {
  return http.request<Result>("post", userUrl("/add"), { data });
};

/** 删除用户 */
export const deleteUser = (data?: [string]) => {
  return http.request<Result>("post", userUrl("/delete"), { data });
};

/** 更新用户信息 */
export const updateUser = (data?: object) => {
  return http.request<Result>("post", userUrl("/update"), { data });
};

/** 更新用户状态 */
export const updateUserStatus = (data?: object) => {
  return http.request<Result>("post", userUrl("/updateStatus"), { data });
};

/** 获取系统管理-用户管理列表 */
export const getUserList = (
  username?: string,
  email?: string,
  deptId?: string,
  pageSize?: number,
  currentPage?: number
) => {
  return http.request<ResultTable>("post", userUrl("/list"), {
    data: { username, email, deptId },
    params: {
      pageSize: pageSize,
      currentPage: currentPage
    } // 忽略取消重复请求
  });
};

/** 新增角色 */
export const addRole = (data?: object) => {
  return http.request<Result>("post", roleUrl("/add"), { data });
};

/** 删除角色 */
export const deleteRole = (data?: [string]) => {
  return http.request<Result>("post", roleUrl("/delete"), { data });
};

/** 更新角色信息 */
export const updateRole = (data?: object) => {
  return http.request<Result>("post", roleUrl("/update"), { data });
};

/** 更新角色状态 */
export const updateRoleStatus = (data?: object) => {
  return http.request<Result>("post", roleUrl("/updateStatus"), { data });
};

/** 系统管理-用户管理-获取所有角色列表 */
export const getAllRoleList = () => {
  return http.request<Result>("get", roleUrl("/all"));
};

/** 系统管理-用户管理-根据userId，获取对应角色id列表（userId：用户id） */
export const getRoleIds = (data?: object) => {
  return http.request<Result>("post", "/list-role-ids", { data });
};

/** 获取系统管理-角色管理列表 */
export const getRoleList = (
  name: string,
  code: string,
  status: string,
  currentPage: number,
  pageSize: number
) => {
  return http.request<ResultTable>("post", roleUrl("/list"), {
    data: { name, code, status },
    params: {
      pageSize,
      currentPage
    }
  });
};

/** 获取角色管理-权限-菜单权限-根据角色 id 查对应菜单 */
export const getRoleMenuIds = (data?: object) => {
  return http.request<Result>("post", roleUrl("/getRoleAuth"), { data });
};

/** 更新角色菜单权限 */
export const updateRoleAuth = (data?: object) => {
  return http.request<Result>("post", roleUrl("/updateRoleAuth"), { data });
};

/** 新增菜单 */
export const addMenu = (data?: object) => {
  return http.request<Result>("post", munuUrl("/add"), { data });
};

/** 删除菜单 */
export const deleteMenu = (data?: [string]) => {
  return http.request<Result>("post", munuUrl("/delete"), { data });
};

/** 更新菜单信息 */
export const updateMenu = (data?: object) => {
  return http.request<Result>("post", munuUrl("/update"), { data });
};

/** 获取系统管理-菜单管理列表 */
export const getMenuList = (data?: object) => {
  return http.request<Result>("get", munuUrl("/list"), { data });
};

/** 新增部门 */
export const addDept = (data?: object) => {
  return http.request<Result>("post", deptUrl("/add"), { data });
};

/** 删除部门 */
export const deleteDept = (data?: [string]) => {
  return http.request<Result>("post", deptUrl("/delete"), { data });
};

/** 更新部门信息 */
export const updateDept = (data?: object) => {
  return http.request<Result>("post", deptUrl("/update"), { data });
};

/** 获取系统管理-部门管理列表 */
export const getDeptList = () => {
  return http.request<Result>("get", deptUrl("/list"));
};

/** 获取系统监控-在线用户列表 */
export const getOnlineLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/online-logs", { data });
};

/** 删除登录日志 */
export const deleteLoginLogs = (data?: string[]) => {
  return http.request<Result>("post", loginLogsUrl("/delete"), { data });
};

/** 删除所有登录日志 */
export const clearLoginLogs = () => {
  return http.request<Result>("get", loginLogsUrl("/clear"));
};

/** 获取系统监控-登录日志列表 */
export const getLoginLogsList = (
  username: string,
  level: string,
  loginTime: [string, string] | null,
  currentPage: number,
  pageSize: number
) => {
  return http.request<ResultTable>("post", loginLogsUrl("/list"), {
    data: { username, level, loginTime },
    params: {
      pageSize,
      currentPage
    }
  });
};

/** 批量删除操作日志 */
export const deleteOperationLogs = (data?: string[]) => {
  return http.request<Result>("post", operationLogsUrl("/delete"), { data });
};

/** 删除全部操作日志 */
export const clearOperationLogs = () => {
  return http.request<Result>("get", operationLogsUrl("/clear"));
};

/** 获取系统监控-操作日志列表 */
export const getOperationLogsList = (
  level: string[],
  operationTime: [string, string] | null,
  currentPage: number,
  pageSize: number
) => {
  return http.request<ResultTable>("post", operationLogsUrl("/list"), {
    data: { level, operationTime },
    params: {
      pageSize,
      currentPage
    }
  });
};

/** 删除系统日志 */
export const deleteSystemLogs = (data?: string[]) => {
  return http.request<Result>("post", systemLogsUrl("/delete"), { data });
};

/** 获取系统监控-系统日志列表 */
export const getSystemLogsList = (
  module: string,
  operationTime: [string, string] | null,
  currentPage: number,
  pageSize: number
) => {
  return http.request<ResultTable>("post", systemLogsUrl("/list"), {
    data: { module, operationTime },
    params: {
      pageSize,
      currentPage
    }
  });
};

/** 删除全部系统日志 */
export const clearSystemLogs = () => {
  return http.request<Result>("post", systemLogsUrl("/clear"));
};

/** 获取系统监控-系统日志-根据 id 查日志详情 */
export const getSystemLogsDetail = (data?: object) => {
  return http.request<Result>("post", "/system-logs-detail", { data });
};
