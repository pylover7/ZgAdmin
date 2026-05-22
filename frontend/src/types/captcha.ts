/** 验证码响应 */
export interface CaptchaResult {
  code: number;
  success: boolean;
  data: { captcha_key: string; captcha_image: string };
}

/** 安全配置（公开） */
export interface SecurityConfigResult {
  code: number;
  success: boolean;
  data: { captcha_enabled: boolean };
}
