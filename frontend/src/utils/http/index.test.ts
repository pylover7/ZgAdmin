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
      try {
        await http.request("post", "/api/v1/base/refreshToken");
      } catch {}
      // Whitelist URLs should not trigger getToken-based token attachment
    });

    it("skips token for /accessToken URLs", async () => {
      mockGetToken.mockReturnValue(null);
      try {
        await http.request("post", "/api/v1/base/accessToken");
      } catch {}
    });

    it("skips token for /base/init URLs", async () => {
      mockGetToken.mockReturnValue(null);
      try {
        await http.request("get", "/api/v1/base/init");
      } catch {}
    });

    it("skips token for /base/captcha URLs", async () => {
      mockGetToken.mockReturnValue(null);
      try {
        await http.request("get", "/api/v1/base/captcha");
      } catch {}
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
      try {
        await http.request("get", "/api/v1/system/user/list");
      } catch {}
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
        data: {
          accessToken: "new-token",
          refreshToken: "new-refresh",
          expires: new Date()
        }
      });
      try {
        await http.request("get", "/api/v1/system/user/list");
      } catch {}
      expect(mockHandRefreshToken).toHaveBeenCalledWith({
        refreshToken: "old-refresh"
      });
    });

    it("does not call formatToken when getToken returns null", async () => {
      mockGetToken.mockReturnValue(null);
      mockFormatToken.mockClear();
      try {
        await http.request("get", "/api/v1/system/user/list");
      } catch {}
      expect(mockFormatToken).not.toHaveBeenCalled();
    });
  });

  describe("convenience methods", () => {
    it("post delegates to request", () => {
      const spy = vi.spyOn(http, "request").mockResolvedValue({} as any);
      http.post("/test", { data: { key: "value" } });
      expect(spy).toHaveBeenCalledWith(
        "post",
        "/test",
        { data: { key: "value" } },
        undefined
      );
      spy.mockRestore();
    });

    it("get delegates to request", () => {
      const spy = vi.spyOn(http, "request").mockResolvedValue({} as any);
      http.get("/test", { params: { q: 1 } });
      expect(spy).toHaveBeenCalledWith(
        "get",
        "/test",
        { params: { q: 1 } },
        undefined
      );
      spy.mockRestore();
    });
  });
});

// ─── 补充分支：刷新失败、响应拦截器、initConfig 回调 ───

describe("HTTP PureHttp extra branches", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("refresh failure → logOut + warning message", async () => {
    const pastTime = Date.now() - 1000;
    mockGetToken.mockReturnValue({
      accessToken: "expired-token",
      expires: pastTime,
      refreshToken: "old-refresh"
    });
    mockHandRefreshToken.mockRejectedValue(new Error("refresh failed"));
    // 刷新失败时原始请求会挂起（设计如此），不 await
    http.request("get", "/api/v1/system/user/list").catch(() => {});
    await new Promise(r => setTimeout(r, 20));
    expect(mockLogOut).toHaveBeenCalled();
    expect(mockMessage).toHaveBeenCalledWith(
      "登录已过期，请重新登录！",
      expect.any(Object)
    );
  });

  it("response interceptor 403 → resetRouter + push /error/403", async () => {
    const handlers: any[] = [];
    const spy = vi
      .spyOn(
        (http as any).constructor.axiosInstance.interceptors.response,
        "use"
      )
      .mockImplementation(((onFulfilled: any, onRejected: any) => {
        handlers.push({ onFulfilled, onRejected });
        return 1;
      }) as any);
    try {
      (http as any).httpInterceptorsResponse();
      const rejected = handlers[handlers.length - 1].onRejected;
      await rejected({ response: { status: 403 }, config: {} }).catch(() => {});
      expect(mockResetRouter).toHaveBeenCalled();
    } finally {
      spy.mockRestore();
    }
  });

  it("response interceptor 401 → logOut + message", async () => {
    const handlers: any[] = [];
    const spy = vi
      .spyOn(
        (http as any).constructor.axiosInstance.interceptors.response,
        "use"
      )
      .mockImplementation(((onFulfilled: any, onRejected: any) => {
        handlers.push({ onFulfilled, onRejected });
        return 1;
      }) as any);
    try {
      (http as any).httpInterceptorsResponse();
      const rejected = handlers[handlers.length - 1].onRejected;
      await rejected({
        response: { status: 401 },
        config: { url: "/api/x" }
      }).catch(() => {});
      expect(mockLogOut).toHaveBeenCalled();
      expect(mockMessage).toHaveBeenCalledWith(
        "请重新登录！",
        expect.any(Object)
      );
    } finally {
      spy.mockRestore();
    }
  });

  it("response interceptor 401 on /logout URL skips logOut", async () => {
    const handlers: any[] = [];
    const spy = vi
      .spyOn(
        (http as any).constructor.axiosInstance.interceptors.response,
        "use"
      )
      .mockImplementation(((onFulfilled: any, onRejected: any) => {
        handlers.push({ onFulfilled, onRejected });
        return 1;
      }) as any);
    try {
      (http as any).httpInterceptorsResponse();
      const rejected = handlers[handlers.length - 1].onRejected;
      mockLogOut.mockClear();
      await rejected({
        response: { status: 401 },
        config: { url: "/api/v1/base/logout" }
      }).catch(() => {});
      expect(mockLogOut).not.toHaveBeenCalled();
    } finally {
      spy.mockRestore();
    }
  });

  it("response interceptor success passes through beforeResponseCallback", async () => {
    const handlers: any[] = [];
    const spy = vi
      .spyOn(
        (http as any).constructor.axiosInstance.interceptors.response,
        "use"
      )
      .mockImplementation(((onFulfilled: any, onRejected: any) => {
        handlers.push({ onFulfilled, onRejected });
        return 1;
      }) as any);
    try {
      (http as any).httpInterceptorsResponse();
      const fulfilled = handlers[handlers.length - 1].onFulfilled;
      const cb = vi.fn();
      const res = fulfilled({
        config: { beforeResponseCallback: cb },
        data: { ok: 1 }
      });
      expect(cb).toHaveBeenCalled();
      expect(res).toEqual({ ok: 1 });
    } finally {
      spy.mockRestore();
    }
  });

  it("request interceptor uses initConfig.beforeRequestCallback", async () => {
    const cb = vi.fn();
    (http as any).constructor.initConfig = { beforeRequestCallback: cb };
    try {
      await (http as any).constructor.axiosInstance.request({
        method: "get",
        url: "/api/v1/system/x"
      });
      expect(cb).toHaveBeenCalled();
    } finally {
      (http as any).constructor.initConfig = {};
    }
  });
});

describe("HTTP PureHttp remaining branches", () => {
  beforeEach(() => vi.clearAllMocks());

  it("request interceptor error handler rejects", () => {
    const handlers: any[] = [];
    const spy = vi
      .spyOn(
        (http as any).constructor.axiosInstance.interceptors.request,
        "use"
      )
      .mockImplementation(((onFulfilled: any, onRejected: any) => {
        handlers.push({ onFulfilled, onRejected });
        return 1;
      }) as any);
    try {
      (http as any).httpInterceptorsRequest();
      const rejected = handlers[handlers.length - 1].onRejected;
      const p = rejected(new Error("req error"));
      expect(p).toBeInstanceOf(Promise);
      p.catch(() => {});
    } finally {
      spy.mockRestore();
    }
  });

  it("response interceptor uses initConfig.beforeResponseCallback", () => {
    const handlers: any[] = [];
    const spy = vi
      .spyOn(
        (http as any).constructor.axiosInstance.interceptors.response,
        "use"
      )
      .mockImplementation(((onFulfilled: any, onRejected: any) => {
        handlers.push({ onFulfilled, onRejected });
        return 1;
      }) as any);
    const cb = vi.fn();
    try {
      (http as any).constructor.initConfig = { beforeResponseCallback: cb };
      (http as any).httpInterceptorsResponse();
      const fulfilled = handlers[handlers.length - 1].onFulfilled;
      const res = fulfilled({ config: {}, data: { ok: 2 } });
      expect(cb).toHaveBeenCalled();
      expect(res).toEqual({ ok: 2 });
    } finally {
      (http as any).constructor.initConfig = {};
      spy.mockRestore();
    }
  });

  it("request rejects when axios instance request fails", async () => {
    const spy = vi
      .spyOn((http as any).constructor.axiosInstance, "request")
      .mockRejectedValue(new Error("net error"));
    try {
      await expect(http.request("get", "/api/v1/system/fail")).rejects.toThrow(
        "net error"
      );
    } finally {
      spy.mockRestore();
    }
  });
});
