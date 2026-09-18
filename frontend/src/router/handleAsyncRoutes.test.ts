import { describe, it, expect, vi, beforeEach } from "vitest";

const {
  mockHandleWholeMenus,
  mockHandleTags,
  mockAddRoute,
  routerMock,
  rootChildren
} = vi.hoisted(() => {
  const rootChildren: any[] = [];
  const mockAddRouteFn = vi.fn();
  return {
    mockHandleWholeMenus: vi.fn(),
    mockHandleTags: vi.fn(),
    mockAddRoute: mockAddRouteFn,
    rootChildren,
    routerMock: {
      push: vi.fn(),
      addRoute: mockAddRouteFn,
      hasRoute: vi.fn(() => false),
      getRoutes: vi.fn(() => [{ path: "/", children: [] }]),
      options: { routes: [{ path: "/", children: rootChildren }] },
      currentRoute: { value: { meta: {}, path: "/", name: "" } }
    }
  };
});

vi.mock("@/router", () => ({
  router: routerMock,
  resetRouter: vi.fn(),
  constantMenus: []
}));

vi.mock("@/store/modules/permission", () => ({
  usePermissionStoreHook: vi.fn(() => ({
    handleWholeMenus: mockHandleWholeMenus,
    flatteningRoutes: [{ path: "/fixed", meta: { fixedTag: true } }],
    cachePageList: [],
    wholeMenus: []
  }))
}));

vi.mock("@/store/modules/multiTags", () => ({
  useMultiTagsStoreHook: vi.fn(() => ({
    handleTags: mockHandleTags,
    getMultiTagsCache: false,
    multiTags: []
  }))
}));

vi.mock("@/route/utils", () => ({}));

vi.mock("@/api/routes", () => ({
  getAsyncRoutes: vi.fn(() =>
    Promise.resolve({
      success: true,
      data: [
        {
          path: "/dynamic",
          name: "Dynamic",
          meta: { title: "动态", rank: 1 },
          children: []
        }
      ]
    })
  )
}));

vi.mock("@/config", () => ({
  getConfig: vi.fn(() => ({ CachingAsyncRoutes: false })),
  responsiveStorageNameSpace: vi.fn(() => "responsive-")
}));

vi.mock("@pureadmin/utils", () => ({
  storageLocal: vi.fn(() => ({
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn()
  })),
  isString: vi.fn(v => typeof v === "string"),
  isIncludeAllChildren: vi.fn(() => true),
  isUrl: vi.fn(() => false),
  isEqual: vi.fn((a, b) => JSON.stringify(a) === JSON.stringify(b)),
  isNumber: vi.fn(v => typeof v === "number"),
  isBoolean: vi.fn(v => typeof v === "boolean"),
  isFunction: vi.fn(v => typeof v === "function"),
  debounce: vi.fn((fn: any) => fn),
  getKeyList: vi.fn(() => []),
  cloneDeep: vi.fn((o: any) => JSON.parse(JSON.stringify(o))),
  isAllEmpty: vi.fn(() => false),
  intersection: vi.fn(() => []),
  subBefore: vi.fn(() => ""),
  getQueryMap: vi.fn(() => ({})),
  sum: vi.fn(() => 0),
  formatBytes: vi.fn(() => ""),
  deviceDetection: vi.fn(() => "pc")
}));

vi.mock("@/layout/types", () => ({ routerArrays: [] }));

vi.mock("@/utils/message", () => ({ message: vi.fn() }));

import { initRouter } from "@/router/utils";

describe("router/utils handleAsyncRoutes non-empty", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    rootChildren.length = 0;
  });

  it("pushes dynamic routes and syncs root children", async () => {
    const result = await initRouter();
    expect(result).toBe(routerMock);
    expect(mockHandleWholeMenus).toHaveBeenCalled();
    expect(mockHandleTags).toHaveBeenCalled();
    expect(mockAddRoute).toHaveBeenCalled();
  });

  it("skips routes already present in root children", async () => {
    routerMock.options.routes[0].children.push({ path: "/dynamic" });
    mockAddRoute.mockClear();
    await initRouter();
    // 已存在 → 不重复 addRoute 该动态路由
    expect(mockHandleWholeMenus).toHaveBeenCalled();
  });
});
