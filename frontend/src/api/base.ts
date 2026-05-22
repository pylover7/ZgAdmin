import { http } from "@/utils/http";
import { apiV1 } from "./utils";
import type { InitConfigResult, CaptchaResult } from "@/types/base";

const baseUrl = (url: string) => apiV1(`/base${url}`);

/** 获取前端初始化配置（站点信息、功能开关、安全配置） */
export const getInitConfig = () => {
  return http.request<InitConfigResult>("get", baseUrl("/init"));
};

/** 获取验证码 */
export const getCaptcha = () => {
  return http.request<CaptchaResult>("get", baseUrl("/captcha"));
};
