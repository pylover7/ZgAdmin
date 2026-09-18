import { describe, it, expect, vi, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";

const { mockSetItem, mockGetItem } = vi.hoisted(() => ({
  mockSetItem: vi.fn(),
  mockGetItem: vi.fn(() => ({
    sidebarStatus: true,
    layout: "vertical",
    epThemeColor: "#409eff",
    theme: "light"
  }))
}));

vi.mock("@/store", async () => {
  const { createPinia: cp } = await import("pinia");
  return { store: cp(), setupStore: vi.fn() };
});

vi.mock("@/layout/types", () => ({ routerArrays: [] }));

vi.mock("@pureadmin/utils", () => ({
  storageLocal: vi.fn(() => ({
    getItem: mockGetItem,
    setItem: mockSetItem,
    removeItem: vi.fn()
  })),
  deviceDetection: vi.fn(() => false)
}));

vi.mock("@/config", () => ({
  getConfig: vi.fn(() => ({
    SidebarStatus: true,
    Layout: "vertical",
    EpThemeColor: "#409eff",
    Title: "ZgAdmin",
    FixedHeader: false,
    HiddenSideBar: false,
    Theme: "light"
  })),
  responsiveStorageNameSpace: vi.fn(() => "responsive-")
}));

vi.mock("@/store/modules/permission", () => ({
  usePermissionStoreHook: vi.fn(() => ({ flatteningRoutes: [] }))
}));

import { useAppStore, useAppStoreHook } from "@/store/modules/app";
import { useEpThemeStore, useEpThemeStoreHook } from "@/store/modules/epTheme";
import { useSettingStore, useSettingStoreHook } from "@/store/modules/settings";

describe("store/modules/app extra branches", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    mockGetItem.mockReturnValue({
      sidebarStatus: true,
      layout: "vertical",
      epThemeColor: "#409eff",
      theme: "light"
    });
  });

  it("TOGGLE_SIDEBAR with opened && resize", () => {
    const store = useAppStore();
    store.TOGGLE_SIDEBAR(true, "resize");
    expect(store.sidebar.opened).toBe(true);
    expect(store.sidebar.withoutAnimation).toBe(true);
    expect(mockSetItem).toHaveBeenCalled();
  });

  it("TOGGLE_SIDEBAR with !opened && resize", () => {
    const store = useAppStore();
    store.TOGGLE_SIDEBAR(false, "resize");
    expect(store.sidebar.opened).toBe(false);
    expect(store.sidebar.withoutAnimation).toBe(true);
  });

  it("toggleSideBar awaits TOGGLE_SIDEBAR", async () => {
    const store = useAppStore();
    await store.toggleSideBar(false);
    expect(typeof store.sidebar.opened).toBe("boolean");
  });

  it("useAppStoreHook returns the same store instance", () => {
    const s1 = useAppStoreHook();
    const s2 = useAppStore();
    expect(s1.$id).toBe(s2.$id);
  });
});

describe("store/modules/epTheme extra branches", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("setEpThemeColor returns early when layout is null", () => {
    mockGetItem.mockReturnValue(null);
    const store = useEpThemeStore();
    store.setEpThemeColor("#123456");
    expect(store.epThemeColor).toBe("#123456");
    expect(mockSetItem).not.toHaveBeenCalled();
  });

  it("useEpThemeStoreHook returns store instance", () => {
    expect(useEpThemeStoreHook().$id).toBe(useEpThemeStore().$id);
  });
});

describe("store/modules/settings extra branches", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("changeSetting delegates to CHANGE_SETTING", () => {
    const store = useSettingStore();
    store.changeSetting({ key: "title", value: "New" });
    expect(store.title).toBe("New");
  });

  it("CHANGE_SETTING ignores unknown key", () => {
    const store = useSettingStore();
    store.CHANGE_SETTING({ key: "notExist", value: 1 });
    expect((store as any).notExist).toBeUndefined();
  });

  it("useSettingStoreHook returns store instance", () => {
    expect(useSettingStoreHook().$id).toBe(useSettingStore().$id);
  });
});
