import { http } from "@/utils/http";
import { apiV1 } from "./utils";
import type { FormItemRule } from "element-plus";

const settingsUrl = (url: string) => apiV1(`/settings${url}`);

type Result = {
  code: number;
  msg: string;
  success: boolean;
  data?: any;
};

/** 登录方式类型（公开） */
export interface LoginMethods {
  qq: {
    enabled: boolean;
  };
  wechat: {
    enabled: boolean;
  };
}

/** 登录配置类型（管理员） */
export interface LoginConfig {
  qq?: {
    app_id: string;
    app_key: string;
    redirect_uri: string;
    enabled: boolean;
  };
  wechat?: {
    app_id: string;
    app_secret: string;
    redirect_uri: string;
    enabled: boolean;
  };
}

/**
 * 将配置类型转换为表单规则类型
 * 例如：{ qq: { app_id: string } } -> { qq: { app_id: FormItemRule[] } }
 */
type ConfigToRules<T> = {
  [K in keyof T]?: T[K] extends object
    ? {
        [P in keyof T[K]]?: FormItemRule[];
      }
    : never;
};

/** 登录配置表单规则类型 */
export type LoginConfigRules = ConfigToRules<LoginConfig>;

/** 获取登录方式（公开接口） */
export const getLoginMethods = () => {
  return http.request<Result>("get", settingsUrl("/login/methods"));
};

/** 获取登录配置（管理员接口） */
export const getLoginConfig = () => {
  return http.request<Result>("get", settingsUrl("/login"));
};

/** 更新登录配置 */
export const updateLoginConfig = (data: LoginConfig) => {
  return http.request<Result>("post", settingsUrl("/login"), { data });
};
