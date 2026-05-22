import { http } from "@/utils/http";
import { apiV1 } from "./utils";
import type { Result, ResultTable } from "@/types";
import type {
  UserInfoResult,
  RefreshTokenResult,
  UserResult,
  UpdateProfileParams,
  UserPreferences
} from "@/types/user";

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
export const getMine = () => {
  return http.request<UserInfoResult>("get", baseUrl("/userinfo"));
};

/** 更新个人资料 */
export const updateProfile = (data: UpdateProfileParams) => {
  return http.request("post", baseUrl("/updateProfile"), { data });
};

/** 修改密码 */
export const updatePassword = (data: {
  current_password: string;
  new_password: string;
}) => {
  return http.request("post", baseUrl("/updatePwd"), { data });
};

/** 获取用户偏好 */
export const getPreferences = () => {
  return http.request<Result<UserPreferences>>("get", baseUrl("/preferences"));
};

/** 更新用户偏好 */
export const updatePreferences = (data: Partial<UserPreferences>) => {
  return http.request("post", baseUrl("/updatePreferences"), { data });
};

/** 账户设置-个人安全日志 */
export const getMineLogs = (params?: {
  pageSize?: number;
  currentPage?: number;
}) => {
  return http.request<ResultTable>("get", baseUrl("/loginLogs"), { params });
};

/** 获取QQ授权链接 */
export const getQQAuthUrl = () => {
  return http.request<Result<{ auth_url: string; state: string }>>(
    "get",
    baseUrl("/qq/auth-url")
  );
};

/** QQ登录 */
export const qqLogin = (data: { code: string; state: string }) => {
  return http.request<UserResult>("post", baseUrl("/qq/login"), { data });
};
