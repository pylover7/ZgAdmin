import type { FormItemRule } from "element-plus";

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

// ─── 通用设置 ───

/** 站点基本信息（公开） */
export interface SiteInfo {
  site_name: string;
  site_desc: string;
  logo: string;
  default_lang: string;
  copyright: string;
  icp: string;
}

/** 通用设置配置（管理员） */
export interface GeneralConfig {
  site_name: string;
  site_desc: string;
  logo: string;
  default_lang: string;
  enable_email: boolean;
  copyright: string;
  icp: string;
}

/** 通用设置表单规则 */
export type GeneralConfigRules = {
  [K in keyof GeneralConfig]?: FormItemRule[];
};

// ─── 安全设置 ───

/** 安全策略配置 */
export interface SecurityPolicy {
  id?: string;
  min_password_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_digit: boolean;
  require_special: boolean;
  password_history_count: number;
  max_login_attempts: number;
  lockout_duration_minutes: number;
  captcha_enabled: boolean;
}

/** IP 规则 */
export interface IPRule {
  id?: string;
  ip_cidr: string;
  rule_type: "whitelist" | "blacklist";
  description: string;
  is_active: boolean;
  created_at?: string;
}
