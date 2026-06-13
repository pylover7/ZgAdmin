import Cookies from "js-cookie";
import { useUserStoreHook } from "@/store/modules/user";
import { storageLocal, isString, isIncludeAllChildren } from "@pureadmin/utils";

export interface DataInfo<T> {
  /** token */
  accessToken: string;
  /** `accessToken`的过期时间（时间戳） */
  expires: T;
  /** `refreshToken`的过期时间（时间戳） */
  refreshExpires: T;
  /** 用于调用刷新accessToken的接口时所需的token */
  refreshToken: string;
  /** 用户名 */
  username?: string;
  /** 昵称 */
  nickname?: string;
  /** 当前登录用户的角色 */
  roles?: Array<string>;
  /** 当前登录用户的按钮级别权限 */
  permissions?: Array<string>;
}

export const userKey = "user-info";
export const TokenKey = "authorized-token";
/**
 * 通过`multiple-tabs`是否在`cookie`中，判断用户是否已经登录系统，
 * 从而支持多标签页打开已经登录的系统后无需再登录。
 * 浏览器完全关闭后`multiple-tabs`将自动从`cookie`中销毁，
 * 再次打开浏览器需要重新登录系统
 * */
export const multipleTabsKey = "multiple-tabs";

/** 获取`token` */
export function getToken(): DataInfo<number> {
  // 此处与`TokenKey`相同，此写法解决初始化时`Cookies`中不存在`TokenKey`报错
  return Cookies.get(TokenKey)
    ? JSON.parse(Cookies.get(TokenKey))
    : storageLocal().getItem(userKey);
}

/**
 * @description 设置`token`以及一些必要信息并采用无感刷新`token`方案
 *
 * 核心逻辑：
 * - `TokenKey` Cookie：存储 accessToken/refreshToken/expires/refreshExpires
 *   - 不勾选"记住我"：过期时间=accessToken过期时间（浏览器关闭前有效，短期）
 *   - 勾选"记住我"：过期时间=refreshToken过期时间（跨浏览器会话，长期）
 * - `multipleTabsKey` Cookie：用于路由守卫判断是否已登录
 *   - 不勾选"记住我"：无 expires（浏览器关闭即清除）
 *   - 勾选"记住我"：过期时间=refreshToken过期时间
 * - `user-info` localStorage：存储用户信息 + refreshToken + expires + refreshExpires
 */
export function setToken(data: DataInfo<number>) {
  const { accessToken, refreshToken, expires, refreshExpires } = data;
  const { isRemembered } = useUserStoreHook();
  const cookieString = JSON.stringify({
    accessToken,
    expires,
    refreshExpires,
    refreshToken
  });

  // TokenKey Cookie：勾选"记住我"时用 refreshToken 过期时间，否则用 accessToken 过期时间
  const cookieExpires = isRemembered
    ? (refreshExpires - Date.now()) / 86400000
    : (expires - Date.now()) / 86400000;

  cookieExpires > 0
    ? Cookies.set(TokenKey, cookieString, { expires: cookieExpires })
    : Cookies.set(TokenKey, cookieString);

  // multipleTabsKey Cookie：勾选"记住我"时设置过期时间，否则浏览器关闭即清除
  Cookies.set(
    multipleTabsKey,
    "true",
    isRemembered ? { expires: (refreshExpires - Date.now()) / 86400000 } : {}
  );

  function setUserKey({ username, nickname, roles, permissions }) {
    useUserStoreHook().SET_USERNAME(username);
    useUserStoreHook().SET_NICKNAME(nickname);
    useUserStoreHook().SET_ROLES(roles);
    useUserStoreHook().SET_PERMS(permissions);
    storageLocal().setItem(userKey, {
      refreshToken,
      expires,
      refreshExpires,
      username,
      nickname,
      roles,
      permissions
    });
  }

  if (data.username && data.roles) {
    const { username, roles } = data;
    setUserKey({
      username,
      nickname: data?.nickname ?? "",
      roles,
      permissions: data?.permissions ?? []
    });
  } else {
    const username =
      storageLocal().getItem<DataInfo<number>>(userKey)?.username ?? "";
    const nickname =
      storageLocal().getItem<DataInfo<number>>(userKey)?.nickname ?? "";
    const roles =
      storageLocal().getItem<DataInfo<number>>(userKey)?.roles ?? [];
    const permissions =
      storageLocal().getItem<DataInfo<number>>(userKey)?.permissions ?? [];
    setUserKey({
      username,
      nickname,
      roles,
      permissions
    });
  }
}

/** 删除`token`以及key值为`user-info`的localStorage信息 */
export function removeToken() {
  Cookies.remove(TokenKey);
  Cookies.remove(multipleTabsKey);
  storageLocal().removeItem(userKey);
}

/** 格式化token（jwt格式） */
export const formatToken = (token: string): string => {
  return "Bearer " + token;
};

/** 是否有按钮级别的权限（根据登录接口返回的`permissions`字段进行判断）*/
export const hasPerms = (value: string | Array<string>): boolean => {
  if (!value) return false;
  const allPerms = "*:*:*";
  const { permissions } = useUserStoreHook();
  if (!permissions) return false;
  if (permissions.length === 1 && permissions[0] === allPerms) return true;
  const isAuths = isString(value)
    ? permissions.includes(value)
    : isIncludeAllChildren(value, permissions);
  return isAuths ? true : false;
};
