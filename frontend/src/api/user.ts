import { http } from "@/utils/http";
import { apiV1 } from "./utils";
import type { ResultTable } from "@/types";
import type {
  UserInfoResult,
  RefreshTokenResult,
  UserResult
} from "@/types/user";
import type { loginResult } from "@/types/login";

const baseUrl = (url: string) => apiV1(`/base${url}`);

/** 登录 */
export const getLogin = (data?: object) => {
  return http.request<UserResult>("post", baseUrl("/accessToken"), { data });
};

/** 刷新`token` */
export const refreshTokenApi = (data?: object) => {
  return http.request<RefreshTokenResult>("post", baseUrl("/refreshToken"), {
    data
  });
};

/** 账户设置-个人信息 */
export const getMine = (data?: object) => {
  return http.request<UserInfoResult>("get", "/mine", { data });
};

/** 账户设置-个人安全日志 */
export const getMineLogs = (data?: object) => {
  return http.request<ResultTable>("get", "/mine-logs", { data });
};

/** 获取QQ授权链接 */
export const getQQAuthUrl = () => {
  return http.request<{ auth_url: string; state: string }>(
    "get",
    baseUrl("/qq/auth-url")
  );
};

/** QQ登录 */
export const qqLogin = (data: { code: string; state: string }) => {
  return http.request<UserResult>("post", baseUrl("/qq/login"), { data });
};

/** 获取登录方式配置 */
export const getLoginMethods = () => {
  return http.request<loginResult>("get", apiV1("/settings/login/methods"));
};
