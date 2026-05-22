import { http } from "@/utils/http";
import { apiV1 } from "./utils";
import type { Result } from "@/types";
import type {
  LoginMethods,
  LoginConfig,
  SiteInfo,
  GeneralConfig,
  SecurityPolicy,
  IPRule
} from "@/types/settings";

const settingsUrl = (url: string) => apiV1(`/settings${url}`);

// ─── 登录设置 ───

/** 获取登录方式（公开接口） */
export const getLoginMethods = () => {
  return http.request<Result<LoginMethods>>(
    "get",
    settingsUrl("/login/methods")
  );
};

/** 获取登录配置（管理员接口） */
export const getLoginConfig = () => {
  return http.request<Result<LoginConfig>>("get", settingsUrl("/login"));
};

/** 更新登录配置 */
export const updateLoginConfig = (data: LoginConfig) => {
  return http.request<Result>("post", settingsUrl("/login"), { data });
};

// ─── 通用设置 ───

/** 获取站点基本信息（公开接口） */
export const getSiteInfo = () => {
  return http.request<Result<SiteInfo>>("get", settingsUrl("/general/info"));
};

/** 获取通用设置（管理员接口） */
export const getGeneralConfig = () => {
  return http.request<Result<GeneralConfig>>("get", settingsUrl("/general"));
};

/** 更新通用设置 */
export const updateGeneralConfig = (data: GeneralConfig) => {
  return http.request<Result>("post", settingsUrl("/general"), { data });
};

// ─── 安全设置 ───

/** 获取安全策略 */
export const getSecurityPolicy = () => {
  return http.request<Result<SecurityPolicy>>(
    "get",
    settingsUrl("/security/policy")
  );
};

/** 更新安全策略 */
export const updateSecurityPolicy = (data: Partial<SecurityPolicy>) => {
  return http.request<Result>("post", settingsUrl("/security/policy"), {
    data
  });
};

/** 获取 IP 规则列表 */
export const getIPRules = () => {
  return http.request<Result<IPRule[]>>(
    "get",
    settingsUrl("/security/ip-rules")
  );
};

/** 新增 IP 规则 */
export const addIPRule = (data: {
  ip_cidr: string;
  rule_type: string;
  description?: string;
  is_active?: boolean;
}) => {
  return http.request<Result>("post", settingsUrl("/security/ip-rules/add"), {
    data
  });
};

/** 修改 IP 规则 */
export const updateIPRule = (data: Partial<IPRule> & { id: string }) => {
  return http.request<Result>(
    "post",
    settingsUrl("/security/ip-rules/update"),
    { data }
  );
};

/** 删除 IP 规则 */
export const deleteIPRules = (data: string[]) => {
  return http.request<Result>(
    "post",
    settingsUrl("/security/ip-rules/delete"),
    { data }
  );
};
