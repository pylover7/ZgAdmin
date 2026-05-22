/** 站点信息 */
export interface SiteInfo {
  site_name: string;
  site_desc: string;
  logo: string;
  default_lang: string;
  copyright: string;
  icp: string;
}

/** 功能开关 */
export interface Features {
  qq_login: boolean;
  wechat_login: boolean;
  email: boolean;
  monitor_log: boolean;
}

/** 安全配置 */
export interface SecurityConfig {
  captcha_enabled: boolean;
}

/** 初始化配置响应 */
export interface InitConfigResult {
  code: number;
  success: boolean;
  data: {
    site: SiteInfo;
    features: Features;
    security: SecurityConfig;
  };
}

/** 验证码响应 */
export interface CaptchaResult {
  code: number;
  success: boolean;
  data: { captcha_key: string; captcha_image: string };
}
