import { describe, it, expect, vi, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";

const { mockGetLogin, mockQQLogin, mockRefreshToken, mockLogoutApi } =
  vi.hoisted(() => ({
    mockGetLogin: vi.fn(),
    mockQQLogin: vi.fn(),
    mockRefreshToken: vi.fn(),
    mockLogoutApi: vi.fn()
  }));

vi.mock("@/api/user", () => ({
  getLogin: mockGetLogin,
  qqLogin: mockQQLogin,
  refreshTokenApi: mockRefreshToken,
  logoutApi: mockLogoutApi
}));

vi.mock("@/utils/auth", () => ({
  setToken: vi.fn(),
  getToken: vi.fn(() => ({
    accessToken: "at",
    refreshToken: "rt",
    expires: 0
  })),
  removeToken: vi.fn(),
  userKey: "user-info",
  TokenKey: "authorized-token"
}));

const { mockHandleTags } = vi.hoisted(() => ({
  mockHandleTags: vi.fn()
}));

vi.mock("@/store/modules/multiTags", () => ({
  useMultiTagsStoreHook: vi.fn(() => ({
    handleTags: mockHandleTags
  }))
}));

vi.mock("@/router", () => ({
  router: { push: vi.fn() },
  resetRouter: vi.fn()
}));

vi.mock("@/store", async () => {
  const { createPinia: cp } = await import("pinia");
  return { store: cp() };
});

vi.mock("@/layout/types", () => ({
  routerArrays: []
}));

vi.mock("@pureadmin/utils", () => ({
  storageLocal: vi.fn(() => ({
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn()
  }))
}));

import { useUserStore } from "@/store/modules/user";
import { setToken, removeToken } from "@/utils/auth";
import { router, resetRouter } from "@/router";

describe("store/modules/user", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("state", () => {
    it("has default state values", () => {
      const store = useUserStore();
      expect(store.username).toBe("");
      expect(store.nickname).toBe("");
      expect(store.roles).toEqual([]);
      expect(store.permissions).toEqual([]);
      expect(store.verifyCode).toBe("");
      expect(store.currentPage).toBe(0);
      expect(store.isRemembered).toBe(false);
    });
  });

  describe("SET_* actions", () => {
    it("SET_USERNAME sets username", () => {
      const store = useUserStore();
      store.SET_USERNAME("admin");
      expect(store.username).toBe("admin");
    });

    it("SET_NICKNAME sets nickname", () => {
      const store = useUserStore();
      store.SET_NICKNAME("Admin User");
      expect(store.nickname).toBe("Admin User");
    });

    it("SET_ROLES sets roles", () => {
      const store = useUserStore();
      store.SET_ROLES(["admin", "editor"]);
      expect(store.roles).toEqual(["admin", "editor"]);
    });

    it("SET_PERMS sets permissions", () => {
      const store = useUserStore();
      store.SET_PERMS(["system:user:add"]);
      expect(store.permissions).toEqual(["system:user:add"]);
    });

    it("SET_VERIFYCODE sets verify code", () => {
      const store = useUserStore();
      store.SET_VERIFYCODE("abc123");
      expect(store.verifyCode).toBe("abc123");
    });

    it("SET_CURRENTPAGE sets current page", () => {
      const store = useUserStore();
      store.SET_CURRENTPAGE(2);
      expect(store.currentPage).toBe(2);
    });

    it("SET_ISREMEMBERED sets remembered flag", () => {
      const store = useUserStore();
      store.SET_ISREMEMBERED(true);
      expect(store.isRemembered).toBe(true);
    });
  });

  describe("loginByUsername", () => {
    it("calls setToken on successful login", async () => {
      mockGetLogin.mockResolvedValue({
        success: true,
        data: { accessToken: "at", refreshToken: "rt", expires: new Date() }
      });
      const store = useUserStore();
      const result = await store.loginByUsername({
        username: "admin",
        password: "123456"
      });
      expect(setToken).toHaveBeenCalled();
      expect(result.success).toBe(true);
    });

    it("does not call setToken on failed login", async () => {
      mockGetLogin.mockResolvedValue({ success: false, msg: "wrong password" });
      const store = useUserStore();
      const result = await store.loginByUsername({
        username: "admin",
        password: "wrong"
      });
      expect(setToken).not.toHaveBeenCalled();
      expect(result.success).toBe(false);
    });

    it("rejects on API error", async () => {
      mockGetLogin.mockRejectedValue(new Error("Network error"));
      const store = useUserStore();
      await expect(
        store.loginByUsername({ username: "admin" })
      ).rejects.toThrow("Network error");
    });
  });

  describe("loginByQQ", () => {
    it("calls setToken on successful QQ login", async () => {
      mockQQLogin.mockResolvedValue({
        success: true,
        data: { accessToken: "at", refreshToken: "rt", expires: new Date() }
      });
      const store = useUserStore();
      const result = await store.loginByQQ({ code: "abc", state: "xyz" });
      expect(setToken).toHaveBeenCalled();
      expect(result.success).toBe(true);
    });
  });

  describe("logOut", () => {
    it("clears user state and navigates to login", async () => {
      mockLogoutApi.mockResolvedValue({});
      const store = useUserStore();
      store.SET_USERNAME("admin");
      store.SET_ROLES(["admin"]);
      store.SET_PERMS(["*:*:*"]);

      await store.logOut();

      expect(store.username).toBe("");
      expect(store.roles).toEqual([]);
      expect(store.permissions).toEqual([]);
      expect(removeToken).toHaveBeenCalled();
      expect(resetRouter).toHaveBeenCalled();
      expect(router.push).toHaveBeenCalledWith("/login");
    });
  });

  describe("handRefreshToken", () => {
    it("calls setToken on successful refresh", async () => {
      mockRefreshToken.mockResolvedValue({
        data: {
          accessToken: "new-at",
          refreshToken: "new-rt",
          expires: new Date()
        }
      });
      const store = useUserStore();
      await store.handRefreshToken({ refreshToken: "old-rt" });
      expect(setToken).toHaveBeenCalled();
    });
  });
});
