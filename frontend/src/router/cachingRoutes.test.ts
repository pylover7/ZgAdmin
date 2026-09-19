import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockGetItem, mockSetItem } = vi.hoisted(() => ({
  mockGetItem: vi.fn(),
  mockSetItem: vi.fn()
}));

const { routerMock } = vi.hoisted(() => ({
  routerMock: {
    push: vi.fn(),
    addRoute: vi.fn(),
    hasRoute: vi.fn(() => false),
    getRoutes: vi.fn(() => [{ path: "/", children: [] }]),
    options: { routes: [{ path: "/", children: [] }] }
  }
}));

vi.mock("@/router", () => ({
  router: routerMock,
  resetRouter: vi.fn(),
  constantMenus: []
}));

vi.mock("@/store/modules/permission", () => ({
  usePermissionStoreHook: vi.fn(() => ({
    handleWholeMenus: vi.fn(),
    flatteningRoutes: [],
    cachePageList: [],
    wholeMenus: []
  }))
}));

vi.mock("@/store/modules/multiTags", () => ({
  useMultiTagsStoreHook: vi.fn(() => ({
    handleTags: vi.fn(),
    getMultiTagsCache: true,
    multiTags: []
  }))
}));

vi.mock("@/api/routes", () => ({
  getAsyncRoutes: vi.fn(() =>
    Promise.resolve({
      success: true,
      data: [
        {
          path: "/dyn2",
          name: "Dyn2",
          meta: { title: "t", rank: 1 },
          children: []
        }
      ]
    })
  )
}));

vi.mock("@/config", () => ({
  getConfig: vi.fn(() => ({ CachingAsyncRoutes: true })),
  responsiveStorageNameSpace: vi.fn(() => "responsive-")
}));

vi.mock("@pureadmin/utils", () => ({
  storageLocal: vi.fn(() => ({
    getItem: mockGetItem,
    setItem: mockSetItem,
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

describe("router/utils CachingAsyncRoutes", () => {
  beforeEach(() => vi.clearAllMocks());

  it("uses cached routes from localStorage when present", async () => {
    mockGetItem.mockReturnValue([
      {
        path: "/cached",
        name: "Cached",
        meta: { title: "c", rank: 1 },
        children: []
      }
    ]);
    await initRouter();
    expect(mockGetItem).toHaveBeenCalledWith("async-routes");
  });

  it("fetches and caches async routes when cache empty", async () => {
    mockGetItem.mockReturnValue(null);
    await initRouter();
    expect(mockSetItem).toHaveBeenCalledWith("async-routes", expect.anything());
  });
});
