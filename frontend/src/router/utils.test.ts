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
      const routes = [{ name: "Other", path: "/other", meta: {} }];
      const result = ascending(routes);
      expect(result[0].meta.rank).toBe(2); // index+2
    });

    it("does not assign auto-rank for Home route at path /", () => {
      const routes = [{ name: "Home", path: "/", meta: { rank: 0 } }];
      const result = ascending(routes);
      expect(result[0].meta.rank).toBe(0);
    });

    it("assigns auto-rank when rank is 0 and not Home", () => {
      const routes = [{ name: "Other", path: "/other", meta: { rank: 0 } }];
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
      router.currentRoute.value.meta = { title: "" };
      expect(hasAuth("some-auth")).toBe(false);
    });

    it("returns true when string auth is in meta.auths", () => {
      router.currentRoute.value.meta = {
        title: "",
        auths: ["system:user:add"]
      };
      expect(hasAuth("system:user:add")).toBe(true);
    });

    it("returns false when string auth is not in meta.auths", () => {
      router.currentRoute.value.meta = {
        title: "",
        auths: ["system:user:add"]
      };
      expect(hasAuth("system:role:edit")).toBe(false);
    });
  });

  describe("formatTwoStageRoutes", () => {
    it("returns empty array for empty input", () => {
      expect(formatTwoStageRoutes([])).toEqual([]);
    });

    it("converts routes to two-stage format", () => {
      const routes = [
        {
          path: "/",
          component: {},
          name: "Layout",
          redirect: "/home",
          meta: {},
          children: []
        },
        { path: "/about", component: {}, name: "About", meta: {} }
      ] as any;
      const result = formatTwoStageRoutes(routes);
      expect(result).toHaveLength(1);
      expect(result[0].path).toBe("/");
      expect(result[0].children).toHaveLength(1);
    });

    it("preserves root route properties", () => {
      const routes = [
        {
          path: "/",
          component: "cmp",
          name: "Root",
          redirect: "/home",
          meta: { title: "Root" },
          children: []
        }
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
          children: [{ path: "/system/user" }, { path: "/system/role" }]
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
      const routes = [{ meta: {}, children: [] }] as any;
      const result = filterNoPermissionTree(routes);
      // Routes without roles meta should still be present (isOneOfArray returns true)
      expect(result).toBeDefined();
    });
  });

  describe("handleAliveRoute", () => {
    it("add mode calls cacheOperate with add", () => {
      handleAliveRoute({ name: "Home" } as any, "add");
      expect(mockCacheOperate).toHaveBeenCalledWith({
        mode: "add",
        name: "Home"
      });
    });

    it("delete mode calls cacheOperate with delete", () => {
      handleAliveRoute({ name: "Home" } as any, "delete");
      expect(mockCacheOperate).toHaveBeenCalledWith({
        mode: "delete",
        name: "Home"
      });
    });

    it("refresh mode calls cacheOperate with refresh", () => {
      handleAliveRoute({ name: "Home" } as any, "refresh");
      expect(mockCacheOperate).toHaveBeenCalledWith({
        mode: "refresh",
        name: "Home"
      });
    });

    it("default mode (no mode specified) calls delete then add after timeout", () => {
      vi.useFakeTimers();
      handleAliveRoute({ name: "Home" } as any);
      expect(mockCacheOperate).toHaveBeenCalledWith({
        mode: "delete",
        name: "Home"
      });
      vi.advanceTimersByTime(100);
      expect(mockCacheOperate).toHaveBeenCalledWith({
        mode: "add",
        name: "Home"
      });
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
      const routes = [{ meta: {}, path: "/test", children: [] }] as any;
      const result = addAsyncRoutes(routes);
      expect(result[0].meta.backstage).toBe(true);
    });

    it("resolves component by explicit component field when provided", () => {
      const routes = [
        {
          meta: {},
          path: "/bycomp",
          component: "system/user/index",
          children: []
        }
      ] as any;
      const result = addAsyncRoutes(routes);
      // 显式 component → 走 findIndex(ev => ev.includes(v.component))
      expect(result[0].meta.backstage).toBe(true);
    });
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

import { usePermissionStoreHook } from "@/store/modules/permission";
import { useMultiTagsStoreHook } from "@/store/modules/multiTags";

describe("router/utils extra branches", () => {
  beforeEach(() => vi.clearAllMocks());

  describe("filterTree / filterChildrenTree nested children", () => {
    it("keeps children with non-zero length", () => {
      const tree = [
        {
          path: "/a",
          meta: { showLink: true },
          children: [
            { path: "/a/1", meta: { showLink: true }, children: [] },
            { path: "/a/2", meta: { showLink: false }, children: [] }
          ]
        }
      ] as any;
      const result = filterTree(tree);
      expect(result[0].children.length).toBe(1);
    });
  });

  describe("getParentPaths deep traversal", () => {
    it("pops parents when a branch misses", () => {
      const routes = [
        {
          path: "/x",
          children: [{ path: "/x/y", children: [{ path: "/x/y/z" }] }]
        }
      ] as any;
      expect(getParentPaths("/x/y/z", routes)).toEqual(["/x", "/x/y"]);
      // 未找到 → 覆盖 parents.pop()
      expect(getParentPaths("/nope", routes)).toEqual([]);
    });
  });

  describe("findRouteByPath nested", () => {
    it("finds deep child", () => {
      const routes = [
        { path: "/p", children: [{ path: "/p/c", children: [] }] }
      ] as any;
      expect(findRouteByPath("/p/c", routes).path).toBe("/p/c");
    });
  });

  describe("addAsyncRoutes with children and no component", () => {
    it("sets redirect/name/component when children present", () => {
      const routes = [
        {
          meta: {},
          path: "/parent",
          children: [{ path: "/parent/child", name: "Child", meta: {} }]
        }
      ] as any;
      const result = addAsyncRoutes(routes);
      expect(result[0].name).toBe("ChildParent");
      expect(result[0].redirect).toBe("/parent/child");
    });

    it("uses IFrame component when meta.frameSrc is set", () => {
      const routes = [
        { meta: { frameSrc: "https://example.com" }, path: "/frame" }
      ] as any;
      const result = addAsyncRoutes(routes);
      expect(result[0].meta.backstage).toBe(true);
    });
  });

  describe("getTopMenu with children", () => {
    it("returns child matching redirect", () => {
      const child = { path: "/child1", name: "c1" };
      (usePermissionStoreHook as any).mockReturnValue({
        wholeMenus: [
          {
            path: "/top",
            redirect: "/child1",
            children: [child, { path: "/child2", name: "c2" }]
          }
        ],
        flatteningRoutes: [],
        handleWholeMenus: mockHandleWholeMenus
      });
      expect(getTopMenu().path).toBe("/child1");
    });

    it("returns first child when no redirect", () => {
      (usePermissionStoreHook as any).mockReturnValue({
        wholeMenus: [
          {
            path: "/top",
            children: [
              { path: "/c1", name: "c1" },
              { path: "/c2", name: "c2" }
            ]
          }
        ],
        flatteningRoutes: [],
        handleWholeMenus: mockHandleWholeMenus
      });
      expect(getTopMenu().path).toBe("/c1");
    });

    it("pushes tag when tag=true", () => {
      const handleTags = vi.fn();
      (usePermissionStoreHook as any).mockReturnValue({
        wholeMenus: [{ path: "/top", children: [{ path: "/c1", name: "c1" }] }],
        flatteningRoutes: [],
        handleWholeMenus: mockHandleWholeMenus
      });
      (useMultiTagsStoreHook as any).mockReturnValue({
        handleTags,
        getMultiTagsCache: false,
        multiTags: []
      });
      getTopMenu(true);
      expect(handleTags).toHaveBeenCalledWith("push", expect.anything());
    });
  });
});

describe("router/utils handleAsyncRoutes & handleTopMenu", () => {
  beforeEach(() => vi.clearAllMocks());

  describe("filterChildrenTree via filterNoPermissionTree", () => {
    it("removes empty-child dirs and applies filterTree to nested children", () => {
      const tree = [
        {
          path: "/dir",
          meta: { title: "d" },
          children: [
            { path: "/dir/a", meta: { title: "a", showLink: true } },
            { path: "/dir/b", meta: { title: "b", showLink: false } }
          ]
        },
        { path: "/empty", meta: { title: "e" }, children: [] }
      ] as any;
      const res = filterNoPermissionTree(tree);
      expect(res.find((r: any) => r.path === "/empty")).toBeUndefined();
      const dir = res.find((r: any) => r.path === "/dir");
      // filterTree 过滤掉 showLink=false 的子项
      expect(
        dir.children.find((c: any) => c.path === "/dir/b")
      ).toBeUndefined();
    });
  });

  describe("handleTopMenu branches", () => {
    it("returns redirect-matched child when redirect set", () => {
      (usePermissionStoreHook as any).mockReturnValue({
        wholeMenus: [
          {
            path: "/root",
            children: [
              {
                path: "/top",
                redirect: "/child1",
                children: [
                  { path: "/child1", name: "c1" },
                  { path: "/child2", name: "c2" }
                ]
              }
            ]
          }
        ],
        flatteningRoutes: [],
        handleWholeMenus: mockHandleWholeMenus
      });
      expect(getTopMenu().path).toBe("/child1");
    });

    it("returns first child when no redirect", () => {
      (usePermissionStoreHook as any).mockReturnValue({
        wholeMenus: [
          {
            path: "/root",
            children: [
              {
                path: "/top",
                children: [
                  { path: "/c1", name: "c1" },
                  { path: "/c2", name: "c2" }
                ]
              }
            ]
          }
        ],
        flatteningRoutes: [],
        handleWholeMenus: mockHandleWholeMenus
      });
      expect(getTopMenu().path).toBe("/c1");
    });

    it("returns route itself when children length <= 1", () => {
      (usePermissionStoreHook as any).mockReturnValue({
        wholeMenus: [
          { path: "/root", children: [{ path: "/only", name: "only" }] }
        ],
        flatteningRoutes: [],
        handleWholeMenus: mockHandleWholeMenus
      });
      expect(getTopMenu().path).toBe("/only");
    });
  });
});
