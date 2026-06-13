export type UserInfo = {
  /** 用户名 */
  username: string;
  /** 昵称 */
  nickname: string;
  /** 邮箱 */
  email: string;
  /** 联系电话 */
  phone: string;
  /** QQ头像 */
  qq_avatar?: string;
  /** 简介（对应后端 remark） */
  remark: string;
};

export type UpdateProfileParams = {
  nickname?: string;
  email?: string;
  phone?: string;
  remark?: string;
};

export type UserPreferences = {
  notify_account: boolean;
  notify_system: boolean;
  notify_task: boolean;
};

export type UserResult = {
  code: number;
  msg: string;
  success: boolean;
  data: {
    /** 用户名 */
    username: string;
    /** 昵称 */
    nickname: string;
    /** 当前登录用户的角色 */
    roles: Array<string>;
    /** 按钮级别权限 */
    permissions: Array<string>;
    /** `token` */
    accessToken: string;
    /** 用于调用刷新`accessToken`的接口时所需的`token` */
    refreshToken: string;
    /** `accessToken`的过期时间（毫秒时间戳） */
    expires: number;
    /** `refreshToken`的过期时间（毫秒时间戳） */
    refreshExpires: number;
  };
};

export type UserInfoResult = {
  success: boolean;
  data: UserInfo;
};

export type RefreshTokenResult = {
  success: boolean;
  data: {
    /** `token` */
    accessToken: string;
    /** 用于调用刷新`accessToken`的接口时所需的`token` */
    refreshToken: string;
    /** `accessToken`的过期时间（毫秒时间戳） */
    expires: number;
    /** `refreshToken`的过期时间（毫秒时间戳） */
    refreshExpires: number;
  };
};
