import { describe, it, expect, vi, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";

const { mockMultiTags } = vi.hoisted(() => ({
  mockMultiTags: [{ name: "Home" }, { name: "About" }]
}));

vi.mock("@/store/modules/multiTags", () => ({
  useMultiTagsStoreHook: vi.fn(() => ({
    multiTags: mockMultiTags
  }))
}));

vi.mock("@/store", async () => {
  const { createPinia: cp } = await import("pinia");
  return { store: cp() };
});

vi.mock("@/router/utils", () => ({
  ascending: vi.fn((arr: any[]) => arr),
  filterTree: vi.fn((arr: any[]) => arr),
  filterNoPermissionTree: vi.fn((arr: any[]) => arr),
  formatFlatteningRoutes: vi.fn((arr: any[]) => arr)
}));

vi.mock("@/layout/types", () => ({
  routerArrays: []
}));

vi.mock("@/config", () => ({
  getConfig: vi.fn(() => ({})),
  responsiveStorageNameSpace: vi.fn(() => "responsive-")
}));

vi.mock("@pureadmin/utils", () => ({
  storageLocal: vi.fn(() => ({
    getItem: vi.fn(() => null),
    setItem: vi.fn()
  })),
  isUrl: vi.fn((v: string) => v.startsWith("http")),
  isEqual: vi.fn((a: any, b: any) => JSON.stringify(a) === JSON.stringify(b)),
  isNumber: vi.fn((v: any) => typeof v === "number"),
  isBoolean: vi.fn((v: any) => typeof v === "boolean"),
  debounce: vi.fn((fn: Function) => {
    return function (this: any, ...args: any[]) {
      fn.apply(this, args);
    };
  }),
  getKeyList: vi.fn(() => ["Home", "About"]),
  cloneDeep: vi.fn((obj: any) => JSON.parse(JSON.stringify(obj))),
  deviceDetection: vi.fn(() => "pc")
}));

import { usePermissionStore } from "@/store/modules/permission";

describe("store/modules/permission", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("state", () => {
    it("has default state values", () => {
      const store = usePermissionStore();
      expect(store.wholeMenus).toEqual([]);
      expect(store.flatteningRoutes).toEqual([]);
      expect(store.cachePageList).toEqual([]);
    });
  });

  describe("handleWholeMenus", () => {
    it("assembles whole menus from constant menus and new routes", () => {
      const store = usePermissionStore();
      store.handleWholeMenus([{ path: "/new" } as any]);
    });
  });

  describe("cacheOperate", () => {
    it("adds page to cache list (kept because it exists in multiTags)", () => {
      const store = usePermissionStore();
      store.cacheOperate({ mode: "add", name: "Home" });
      expect(store.cachePageList).toContain("Home");
    });

    it("deletes page from cache list", () => {
      const store = usePermissionStore();
      store.cacheOperate({ mode: "add", name: "Home" });
      store.cacheOperate({ mode: "delete", name: "Home" });
      expect(store.cachePageList).not.toContain("Home");
    });

    it("refresh removes page from cache list", () => {
      const store = usePermissionStore();
      store.cacheOperate({ mode: "add", name: "Home" });
      store.cacheOperate({ mode: "refresh", name: "Home" });
      expect(store.cachePageList).not.toContain("Home");
    });
  });

  describe("clearAllCachePage", () => {
    it("clears wholeMenus and cachePageList", () => {
      const store = usePermissionStore();
      store.cacheOperate({ mode: "add", name: "Home" });
      store.clearAllCachePage();
      expect(store.wholeMenus).toEqual([]);
      expect(store.cachePageList).toEqual([]);
    });
  });
});
