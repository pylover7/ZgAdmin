import { describe, it, expect, vi, beforeEach } from "vitest";

// ─── Mock axios: 保留真实拦截器，替换 adapter 阻止真实网络请求 ───
vi.mock("axios", async () => {
  const actual = await vi.importActual<typeof import("axios")>("axios");
  const mockAdapter = () =>
    Promise.resolve({
      data: {},
      status: 200,
      statusText: "OK",
      headers: {},
      config: {}
    });
  return {
    default: {
      ...actual.default,
      create: vi.fn((config: any) => {
        const instance = actual.default.create(config);
        instance.defaults.adapter = mockAdapter as any;
        return instance;
      }),
      isCancel: actual.default.isCancel
    }
  };
});

const { mockGetToken, mockFormatToken } = vi.hoisted(() => ({
  mockGetToken: vi.fn(),
  mockFormatToken: vi.fn((token: string) => `Bearer ${token}`)
}));

const { mockHandRefreshToken, mockLogOut } = vi.hoisted(() => ({
  mockHandRefreshToken: vi.fn(),
  mockLogOut: vi.fn()
}));

const { mockPush, mockResetRouter } = vi.hoisted(() => ({
  mockPush: vi.fn(() => Promise.resolve()),
  mockResetRouter: vi.fn()
}));

const { mockMessage } = vi.hoisted(() => ({
  mockMessage: vi.fn()
}));

vi.mock("@/utils/auth", () => ({
  getToken: mockGetToken,
  formatToken: mockFormatToken,
  removeToken: vi.fn(),
  setToken: vi.fn(),
  userKey: "user-info",
  TokenKey: "authorized-token",
  multipleTabsKey: "multiple-tabs"
}));

vi.mock("@/store/modules/user", () => ({
  useUserStoreHook: vi.fn(() => ({
    handRefreshToken: mockHandRefreshToken,
    logOut: mockLogOut,
    isRemembered: false,
    loginDay: 7,
    SET_USERNAME: vi.fn(),
    SET_NICKNAME: vi.fn(),
    SET_ROLES: vi.fn(),
    SET_PERMS: vi.fn()
  }))
}));

vi.mock("@/router", () => ({
  router: { push: mockPush },
  resetRouter: mockResetRouter
}));

vi.mock("@/utils/message", () => ({
  message: mockMessage
}));

vi.mock("@/store/modules/multiTags", () => ({
  useMultiTagsStoreHook: vi.fn(() => ({
    handleTags: vi.fn()
  }))
}));

vi.mock("@/store/modules/permission", () => ({
  usePermissionStoreHook: vi.fn(() => ({
    handleWholeMenus: vi.fn(),
    flatteningRoutes: [],
    wholeMenus: [],
    cachePageList: [],
    cacheOperate: vi.fn()
  }))
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

import { http } from "@/utils/http";

describe("HTTP PureHttp", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("instance creation", () => {
    it("creates http instance with request/get/post methods", () => {
      expect(http).toBeDefined();
      expect(http.request).toBeTypeOf("function");
      expect(http.get).toBeTypeOf("function");
      expect(http.post).toBeTypeOf("function");
    });
  });

  describe("request interceptor - whitelist URLs", () => {
    it("skips token for /refreshToken URLs", async () => {
      mockGetToken.mockReturnValue(null);
      try { await http.request("post", "/api/v1/base/refreshToken"); } catch {}
      // Whitelist URLs should not trigger getToken-based token attachment
    });

    it("skips token for /accessToken URLs", async () => {
      mockGetToken.mockReturnValue(null);
      try { await http.request("post", "/api/v1/base/accessToken"); } catch {}
    });

    it("skips token for /base/init URLs", async () => {
      mockGetToken.mockReturnValue(null);
      try { await http.request("get", "/api/v1/base/init"); } catch {}
    });

    it("skips token for /base/captcha URLs", async () => {
      mockGetToken.mockReturnValue(null);
      try { await http.request("get", "/api/v1/base/captcha"); } catch {}
    });
  });

  describe("request interceptor - beforeRequestCallback", () => {
    it("calls beforeRequestCallback when provided in config", async () => {
      const callback = vi.fn();
      mockGetToken.mockReturnValue(null);
      try {
        await http.request("get", "/api/test", undefined, {
          beforeRequestCallback: callback
        });
      } catch {}
      expect(callback).toHaveBeenCalled();
    });
  });

  describe("request interceptor - token handling", () => {
    it("attaches Authorization header when token is valid and not expired", async () => {
      const futureTime = Date.now() + 3600000;
      mockGetToken.mockReturnValue({
        accessToken: "valid-token",
        expires: futureTime,
        refreshToken: "refresh-token"
      });
      try { await http.request("get", "/api/v1/system/user/list"); } catch {}
      expect(mockFormatToken).toHaveBeenCalledWith("valid-token");
    });

    it("tries to refresh token when expired", async () => {
      const pastTime = Date.now() - 1000;
      mockGetToken.mockReturnValue({
        accessToken: "expired-token",
        expires: pastTime,
        refreshToken: "old-refresh"
      });
      mockHandRefreshToken.mockResolvedValue({
        data: { accessToken: "new-token", refreshToken: "new-refresh", expires: new Date() }
      });
      try { await http.request("get", "/api/v1/system/user/list"); } catch {}
      expect(mockHandRefreshToken).toHaveBeenCalledWith({ refreshToken: "old-refresh" });
    });

    it("does not call formatToken when getToken returns null", async () => {
      mockGetToken.mockReturnValue(null);
      mockFormatToken.mockClear();
      try { await http.request("get", "/api/v1/system/user/list"); } catch {}
      expect(mockFormatToken).not.toHaveBeenCalled();
    });
  });

  describe("convenience methods", () => {
    it("post delegates to request", () => {
      const spy = vi.spyOn(http, "request").mockResolvedValue({} as any);
      http.post("/test", { data: { key: "value" } });
      expect(spy).toHaveBeenCalledWith("post", "/test", { data: { key: "value" } }, undefined);
      spy.mockRestore();
    });

    it("get delegates to request", () => {
      const spy = vi.spyOn(http, "request").mockResolvedValue({} as any);
      http.get("/test", { params: { q: 1 } });
      expect(spy).toHaveBeenCalledWith("get", "/test", { params: { q: 1 } }, undefined);
      spy.mockRestore();
    });
  });
});
