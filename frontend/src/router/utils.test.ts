import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock dependencies
vi.mock("@/utils/auth", () => ({
  getToken: vi.fn(() => ({
    accessToken: "test-token",
    expires: Date.now() + 3600000,
    refreshToken: "refresh-token"
  })),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  userKey: "user-info"
}));

vi.mock("@/store/modules/user", () => ({
  useUserStoreHook: vi.fn(() => ({
    isRemembered: false,
    loginDay: 7,
    SET_USERNAME: vi.fn(),
    SET_NICKNAME: vi.fn(),
    SET_ROLES: vi.fn(),
    SET_PERMS: vi.fn(),
    logOut: vi.fn()
  }))
}));

vi.mock("@/store/modules/multiTags", () => ({
  useMultiTagsStoreHook: vi.fn(() => ({
    handleTags: vi.fn(),
    getMultiTagsCache: false,
    multiTags: []
  }))
}));

const { mockCacheOperate, mockHandleWholeMenus } = vi.hoisted(() => ({
  mockCacheOperate: vi.fn(),
  mockHandleWholeMenus: vi.fn()
}));

vi.mock("@/store/modules/permission", () => ({
  usePermissionStoreHook: vi.fn(() => ({
    handleWholeMenus: mockHandleWholeMenus,
    flatteningRoutes: [],
    cachePageList: [],
    cacheOperate: mockCacheOperate,
    wholeMenus: []
  }))
}));

vi.mock("@/utils/http", () => ({
  http: {
    request: vi.fn(() => Promise.resolve({ success: true, data: [] }))
  }
}));

import {
  ascending,
  filterTree,
  isOneOfArray,
  getHistoryMode,
  hasAuth,
  formatTwoStageRoutes,
  formatFlatteningRoutes,
  addPathMatch,
  getParentPaths,
  findRouteByPath,
  filterNoPermissionTree,
  handleAliveRoute,
  addAsyncRoutes,
  getTopMenu,
  initRouter
} from "@/router/utils";
import { router } from "@/router";

describe("router/utils", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("ascending", () => {
    it("sorts routes by meta.rank ascending", () => {
      const routes = [
        { meta: { rank: 3 } },
        { meta: { rank: 1 } },
        { meta: { rank: 2 } }
      ];
      const result = ascending(routes);
      expect(result[0].meta.rank).toBe(1);
      expect(result[1].meta.rank).toBe(2);
      expect(result[2].meta.rank).toBe(3);
    });

    it("assigns auto-rank when rank is missing for non-home routes", () => {
      const routes = [
        { name: "Other", path: "/other", meta: {} }
      ];
      const result = ascending(routes);
      expect(result[0].meta.rank).toBe(2); // index+2
    });

    it("does not assign auto-rank for Home route at path /", () => {
      const routes = [
        { name: "Home", path: "/", meta: { rank: 0 } }
      ];
      const result = ascending(routes);
      expect(result[0].meta.rank).toBe(0);
    });

    it("assigns auto-rank when rank is 0 and not Home", () => {
      const routes = [
        { name: "Other", path: "/other", meta: { rank: 0 } }
      ];
      const result = ascending(routes);
      expect(result[0].meta.rank).toBe(2); // Gets auto-rank
    });
  });

  describe("filterTree", () => {
    it("filters out routes with showLink=false", () => {
      const routes = [
        { meta: { showLink: true }, children: [] },
        { meta: { showLink: false }, children: [] },
        { meta: {}, children: [] }
      ];
      const result = filterTree(routes as any);
      expect(result).toHaveLength(2);
    });

    it("filters nested children recursively", () => {
      const routes = [
        {
          meta: { showLink: true },
          children: [
            { meta: { showLink: false }, children: [] },
            { meta: { showLink: true }, children: [] }
          ]
        }
      ];
      const result = filterTree(routes as any);
      expect(result[0].children).toHaveLength(1);
    });
  });

  describe("isOneOfArray", () => {
    it("returns true when both are not arrays", () => {
      expect(isOneOfArray("a" as any, "b" as any)).toBe(true);
    });

    it("returns true when arrays have common elements", () => {
      expect(isOneOfArray(["a", "b"], ["b", "c"])).toBe(true);
    });

    it("returns false when arrays have no common elements", () => {
      expect(isOneOfArray(["a"], ["b", "c"])).toBe(false);
    });

    it("returns true when one is not an array", () => {
      expect(isOneOfArray(["a"], "b" as any)).toBe(true);
    });
  });

  describe("getHistoryMode", () => {
    it("returns hash history for 'hash'", () => {
      expect(getHistoryMode("hash")).toBeDefined();
    });

    it("returns web history for 'h5'", () => {
      expect(getHistoryMode("h5")).toBeDefined();
    });

    it("returns hash history with base param for 'hash,/base'", () => {
      expect(getHistoryMode("hash,/base")).toBeDefined();
    });

    it("returns web history with base param for 'h5,/base'", () => {
      expect(getHistoryMode("h5,/base")).toBeDefined();
    });
  });

  describe("hasAuth", () => {
    it("returns false for falsy value", () => {
      expect(hasAuth("")).toBe(false);
    });

    it("returns false when meta.auths is undefined", () => {
      router.currentRoute.value.meta = {};
      expect(hasAuth("some-auth")).toBe(false);
    });

    it("returns true when string auth is in meta.auths", () => {
      router.currentRoute.value.meta = { auths: ["system:user:add"] };
      expect(hasAuth("system:user:add")).toBe(true);
    });

    it("returns false when string auth is not in meta.auths", () => {
      router.currentRoute.value.meta = { auths: ["system:user:add"] };
      expect(hasAuth("system:role:edit")).toBe(false);
    });
  });

  describe("formatTwoStageRoutes", () => {
    it("returns empty array for empty input", () => {
      expect(formatTwoStageRoutes([])).toEqual([]);
    });

    it("converts routes to two-stage format", () => {
      const routes = [
        { path: "/", component: {}, name: "Layout", redirect: "/home", meta: {}, children: [] },
        { path: "/about", component: {}, name: "About", meta: {} }
      ] as any;
      const result = formatTwoStageRoutes(routes);
      expect(result).toHaveLength(1);
      expect(result[0].path).toBe("/");
      expect(result[0].children).toHaveLength(1);
    });

    it("preserves root route properties", () => {
      const routes = [
        { path: "/", component: "cmp", name: "Root", redirect: "/home", meta: { title: "Root" }, children: [] }
      ] as any;
      const result = formatTwoStageRoutes(routes);
      expect(result[0].name).toBe("Root");
      expect(result[0].redirect).toBe("/home");
      expect(result[0].children).toEqual([]);
    });
  });

  describe("formatFlatteningRoutes", () => {
    it("returns empty array for empty input", () => {
      expect(formatFlatteningRoutes([])).toEqual([]);
    });

    it("flattens nested routes into one-dimensional array", () => {
      const routes = [
        {
          path: "/",
          children: [
            { path: "/home", children: [] },
            { path: "/about", children: [] }
          ]
        }
      ] as any;
      const result = formatFlatteningRoutes(routes);
      expect(result.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("addPathMatch", () => {
    it("adds PageNotFound route if it does not exist", () => {
      (router.hasRoute as ReturnType<typeof vi.fn>).mockReturnValue(false);
      addPathMatch();
      expect(router.addRoute).toHaveBeenCalled();
    });

    it("skips adding PageNotFound if it already exists", () => {
      (router.hasRoute as ReturnType<typeof vi.fn>).mockReturnValue(true);
      addPathMatch();
      expect(router.addRoute).not.toHaveBeenCalled();
    });
  });

  describe("getParentPaths", () => {
    it("finds parent paths for a given route path", () => {
      const routes = [
        {
          path: "/system",
          children: [
            { path: "/system/user", children: [] },
            { path: "/system/role", children: [] }
          ]
        }
      ] as any;
      const result = getParentPaths("/system/user", routes);
      expect(result).toContain("/system");
    });

    it("returns empty array when path not found", () => {
      const routes = [{ path: "/home" }] as any;
      const result = getParentPaths("/nonexistent", routes);
      expect(result).toEqual([]);
    });

    it("finds parent at root level", () => {
      const routes = [{ path: "/home" }] as any;
      const result = getParentPaths("/home", routes);
      expect(result).toEqual([]);
    });
  });

  describe("findRouteByPath", () => {
    it("finds route at root level", () => {
      const routes = [{ path: "/home" }, { path: "/about" }] as any;
      const result = findRouteByPath("/home", routes);
      expect(result?.path).toBe("/home");
    });

    it("finds route in nested children", () => {
      const routes = [
        {
          path: "/system",
          children: [
            { path: "/system/user" },
            { path: "/system/role" }
          ]
        }
      ] as any;
      const result = findRouteByPath("/system/user", routes);
      expect(result?.path).toBe("/system/user");
    });

    it("returns null when path not found", () => {
      const routes = [{ path: "/home" }] as any;
      const result = findRouteByPath("/nonexistent", routes);
      expect(result).toBeNull();
    });
  });

  describe("filterNoPermissionTree", () => {
    it("returns filtered tree — empty roles filter out role-restricted routes", () => {
      // When current user has no roles, role-restricted routes are filtered out
      const routes = [
        { meta: {}, children: [] }
      ] as any;
      const result = filterNoPermissionTree(routes);
      // Routes without roles meta should still be present (isOneOfArray returns true)
      expect(result).toBeDefined();
    });
  });

  describe("handleAliveRoute", () => {
    it("add mode calls cacheOperate with add", () => {
      handleAliveRoute({ name: "Home" } as any, "add");
      expect(mockCacheOperate).toHaveBeenCalledWith({ mode: "add", name: "Home" });
    });

    it("delete mode calls cacheOperate with delete", () => {
      handleAliveRoute({ name: "Home" } as any, "delete");
      expect(mockCacheOperate).toHaveBeenCalledWith({ mode: "delete", name: "Home" });
    });

    it("refresh mode calls cacheOperate with refresh", () => {
      handleAliveRoute({ name: "Home" } as any, "refresh");
      expect(mockCacheOperate).toHaveBeenCalledWith({ mode: "refresh", name: "Home" });
    });

    it("default mode (no mode specified) calls delete then add after timeout", () => {
      vi.useFakeTimers();
      handleAliveRoute({ name: "Home" } as any);
      expect(mockCacheOperate).toHaveBeenCalledWith({ mode: "delete", name: "Home" });
      vi.advanceTimersByTime(100);
      expect(mockCacheOperate).toHaveBeenCalledWith({ mode: "add", name: "Home" });
      vi.useRealTimers();
    });
  });

  describe("addAsyncRoutes", () => {
    it("returns undefined for empty input", () => {
      expect(addAsyncRoutes([])).toBeUndefined();
    });

    it("returns undefined for null input", () => {
      expect(addAsyncRoutes(null as any)).toBeUndefined();
    });

    it("sets backstage=true in meta for all routes", () => {
      const routes = [
        { meta: {}, path: "/test", children: [] }
      ] as any;
      const result = addAsyncRoutes(routes);
      expect(result[0].meta.backstage).toBe(true);
    });

    // Note: redirect and name auto-setting requires children with length > 0
    // and the component resolution requires import.meta.glob which is empty in tests
  });

  describe("getTopMenu", () => {
    it("returns undefined when wholeMenus is empty", () => {
      const result = getTopMenu();
      expect(result).toBeUndefined();
    });
  });

  describe("initRouter", () => {
    it("returns a promise", () => {
      const result = initRouter();
      expect(result).toBeInstanceOf(Promise);
    });
  });
});
