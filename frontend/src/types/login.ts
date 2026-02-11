export type loginType = {
  qq: { enabled: boolean };
  wechat: { enabled: boolean };
};

export type loginResult = {
  code: number;
  msg: string;
  success: boolean;
  data?: loginType;
};
