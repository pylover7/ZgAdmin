import { describe, it, expect, vi, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";

// Mock dependencies
vi.mock("@/store/modules/permission", () => ({
  usePermissionStoreHook: vi.fn(() => ({
    flatteningRoutes: [],
    wholeMenus: []
  }))
}));

vi.mock("@/store", async () => {
  const { createPinia: cp } = await import("pinia");
  return { store: cp() };
});

vi.mock("@/layout/types", () => ({
  routerArrays: []
}));

const { mockSetItem, mockRemoveItem } = vi.hoisted(() => ({
  mockSetItem: vi.fn(),
  mockRemoveItem: vi.fn()
}));

vi.mock("@pureadmin/utils", () => ({
  storageLocal: vi.fn(() => ({
    getItem: vi.fn(() => null),
    setItem: mockSetItem,
    removeItem: mockRemoveItem
  })),
  isUrl: vi.fn((v: string) => v.startsWith("http")),
  isEqual: vi.fn((a: any, b: any) => JSON.stringify(a) === JSON.stringify(b)),
  isNumber: vi.fn((v: any) => typeof v === "number"),
  isBoolean: vi.fn((v: any) => typeof v === "boolean"),
  debounce: vi.fn((fn: Function) => fn),
  getKeyList: vi.fn(() => []),
  cloneDeep: vi.fn((obj: any) => JSON.parse(JSON.stringify(obj))),
  deviceDetection: vi.fn(() => "pc")
}));

vi.mock("@/config", () => ({
  getConfig: vi.fn(() => ({})),
  responsiveStorageNameSpace: vi.fn(() => "responsive-")
}));

vi.mock("@/router/utils", () => ({
  ascending: vi.fn((arr: any[]) => arr),
  filterTree: vi.fn((arr: any[]) => arr),
  filterNoPermissionTree: vi.fn((arr: any[]) => arr),
  formatFlatteningRoutes: vi.fn((arr: any[]) => arr)
}));

import { useMultiTagsStore } from "@/store/modules/multiTags";
import { isUrl, isBoolean, isNumber, storageLocal } from "@pureadmin/utils";
import { getConfig } from "@/config";

describe("store/modules/multiTags", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("state", () => {
    it("has default multiTags as empty array", () => {
      const store = useMultiTagsStore();
      expect(store.multiTags).toEqual([]);
    });

    it("has default multiTagsCache as undefined/null", () => {
      const store = useMultiTagsStore();
      // multiTagsCache comes from localStorage, defaults to falsy
      expect(store.multiTagsCache).toBeFalsy();
    });
  });

  describe("getMultiTagsCache", () => {
    it("returns multiTagsCache value", () => {
      const store = useMultiTagsStore();
      expect(store.getMultiTagsCache).toBeFalsy();
    });
  });

  describe("multiTagsCacheChange", () => {
    it("enables cache and saves to localStorage", () => {
      const store = useMultiTagsStore();
      store.multiTagsCacheChange(true);
      expect(store.multiTagsCache).toBe(true);
      expect(mockSetItem).toHaveBeenCalled();
    });

    it("disables cache and removes from localStorage", () => {
      const store = useMultiTagsStore();
      store.multiTagsCacheChange(false);
      expect(store.multiTagsCache).toBe(false);
      expect(mockRemoveItem).toHaveBeenCalledWith("responsive-tags");
    });
  });

  describe("handleTags", () => {
    describe("equal mode", () => {
      it("replaces multiTags array", () => {
        const store = useMultiTagsStore();
        store.handleTags("equal", [{ path: "/home", name: "Home", meta: {} }] as any);
        expect(store.multiTags).toHaveLength(1);
        expect(store.multiTags[0].path).toBe("/home");
      });
    });

    describe("push mode", () => {
      it("adds new tag", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/home", name: "Home", meta: { title: "Home" } } as any);
        expect(store.multiTags).toHaveLength(1);
      });

      it("skips hidden tags", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/hidden", name: "Hidden", meta: { hiddenTag: true, title: "Hidden" } } as any);
        expect(store.multiTags).toHaveLength(0);
      });

      it("skips URL-named tags", () => {
        (isUrl as ReturnType<typeof vi.fn>).mockReturnValue(true);
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/ext", name: "http://example.com", meta: { title: "Ext" } } as any);
        expect(store.multiTags).toHaveLength(0);
        (isUrl as ReturnType<typeof vi.fn>).mockReturnValue(false);
      });

      it("skips tags with empty title", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/empty", name: "Empty", meta: { title: "" } } as any);
        expect(store.multiTags).toHaveLength(0);
      });

      it("skips tags with showLink=false", () => {
        (isBoolean as ReturnType<typeof vi.fn>).mockReturnValue(true);
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/hidden", name: "Hidden", meta: { title: "Hidden", showLink: false } } as any);
        expect(store.multiTags).toHaveLength(0);
        (isBoolean as ReturnType<typeof vi.fn>).mockReturnValue(false);
      });

      it("skips duplicate tags (same path, query, params)", () => {
        const store = useMultiTagsStore();
        const tag = { path: "/home", name: "Home", meta: { title: "Home" } } as any;
        store.handleTags("push", tag);
        store.handleTags("push", tag);
        expect(store.multiTags).toHaveLength(1);
      });

      it("adds tag with different query", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/home", name: "Home", meta: { title: "Home" }, query: { a: 1 } } as any);
        store.handleTags("push", { path: "/home", name: "Home", meta: { title: "Home" }, query: { b: 2 } } as any);
        // isEqual mock returns false for different objects
        expect(store.multiTags).toHaveLength(2);
      });

      it("replaces first dynamic tag when limit reached", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/dynamic", name: "D1", meta: { title: "D1", dynamicLevel: 2 } } as any);
        store.handleTags("push", { path: "/dynamic", name: "D2", meta: { title: "D2", dynamicLevel: 2 }, query: { x: 1 } } as any);
        store.handleTags("push", { path: "/dynamic", name: "D3", meta: { title: "D3", dynamicLevel: 2 }, query: { x: 2 } } as any);
        // Should have replaced the first one (dynamicLevel=2, so max 2 tags for same path)
        const dynamicTags = store.multiTags.filter(t => t.path === "/dynamic");
        expect(dynamicTags.length).toBeLessThanOrEqual(2);
      });
    });

    describe("splice mode", () => {
      it("removes tag by path without position", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/home", name: "Home", meta: { title: "Home" } } as any);
        store.handleTags("splice", "/home" as any);
        expect(store.multiTags).toHaveLength(0);
      });

      it("removes tag at position", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/home", name: "Home", meta: { title: "Home" } } as any);
        store.handleTags("push", { path: "/about", name: "About", meta: { title: "About" } } as any);
        store.handleTags("splice", undefined as any, { startIndex: 0, length: 1 });
        expect(store.multiTags).toHaveLength(1);
        expect(store.multiTags[0].path).toBe("/about");
      });

      it("does nothing when path not found", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/home", name: "Home", meta: { title: "Home" } } as any);
        store.handleTags("splice", "/nonexistent" as any);
        expect(store.multiTags).toHaveLength(1);
      });
    });

    describe("slice mode", () => {
      it("returns last tag", () => {
        const store = useMultiTagsStore();
        store.handleTags("push", { path: "/home", name: "Home", meta: { title: "Home" } } as any);
        store.handleTags("push", { path: "/about", name: "About", meta: { title: "About" } } as any);
        const result = store.handleTags("slice");
        expect(result).toHaveLength(1);
        expect(result[0].path).toBe("/about");
      });
    });
  });
});
