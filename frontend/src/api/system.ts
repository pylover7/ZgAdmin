import { http } from "@/utils/http";

import { apiV1 } from "./utils";

const systemUrl = (url: string) => apiV1(`/system${url}`);
const deptUrl = (url: string) => systemUrl(`/dept${url}`);
const munuUrl = (url: string) => systemUrl(`/menu${url}`);

type Result = {
  code: number;
  msg: string;
  success: boolean;
  data?: Array<any>;
};

type ResultTable = {
  code: number;
  msg: string;
  success: boolean;
  data?: {
    /** 列表数据 */
    list: Array<any>;
    /** 总条目数 */
    total?: number;
    /** 每页显示条目个数 */
    pageSize?: number;
    /** 当前页数 */
    currentPage?: number;
  };
};

/** 获取系统管理-用户管理列表 */
export const getUserList = (data?: object) => {
  return http.request<ResultTable>("post", "/user", { data });
};

/** 系统管理-用户管理-获取所有角色列表 */
export const getAllRoleList = () => {
  return http.request<Result>("get", "/list-all-role");
};

/** 系统管理-用户管理-根据userId，获取对应角色id列表（userId：用户id） */
export const getRoleIds = (data?: object) => {
  return http.request<Result>("post", "/list-role-ids", { data });
};

/** 获取系统管理-角色管理列表 */
export const getRoleList = (data?: object) => {
  return http.request<ResultTable>("post", "/role", { data });
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

/** 获取系统监控-登录日志列表 */
export const getLoginLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/login-logs", { data });
};

/** 获取系统监控-操作日志列表 */
export const getOperationLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/operation-logs", { data });
};

/** 获取系统监控-系统日志列表 */
export const getSystemLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/system-logs", { data });
};

/** 获取系统监控-系统日志-根据 id 查日志详情 */
export const getSystemLogsDetail = (data?: object) => {
  return http.request<Result>("post", "/system-logs-detail", { data });
};

/** 获取角色管理-权限-菜单权限 */
export const getRoleMenu = (data?: object) => {
  return http.request<Result>("post", "/role-menu", { data });
};

/** 获取角色管理-权限-菜单权限-根据角色 id 查对应菜单 */
export const getRoleMenuIds = (data?: object) => {
  return http.request<Result>("post", "/role-menu-ids", { data });
};
