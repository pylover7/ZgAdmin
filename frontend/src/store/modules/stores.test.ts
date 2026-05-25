import { describe, it, expect, vi, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";

const { mockSetItem } = vi.hoisted(() => ({
  mockSetItem: vi.fn()
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
    getItem: vi.fn(() => ({ sidebarStatus: true, layout: "vertical", epThemeColor: "#409eff", theme: "light" })),
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
  usePermissionStoreHook: vi.fn(() => ({
    flatteningRoutes: []
  }))
}));

import { useAppStore } from "@/store/modules/app";
import { useSettingStore } from "@/store/modules/settings";
import { useEpThemeStore } from "@/store/modules/epTheme";

describe("store/modules/app", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("state", () => {
    it("has default sidebar state", () => {
      const store = useAppStore();
      expect(store.sidebar.opened).toBe(true);
      expect(store.sidebar.withoutAnimation).toBe(false);
      expect(store.sidebar.isClickCollapse).toBe(false);
    });

    it("has device based on deviceDetection", () => {
      const store = useAppStore();
      expect(store.device).toBe("desktop");
    });

    it("has viewportSize", () => {
      const store = useAppStore();
      // happy-dom may return 0 for clientWidth/Height
      expect(typeof store.viewportSize.width).toBe("number");
      expect(typeof store.viewportSize.height).toBe("number");
    });
  });

  describe("getters", () => {
    it("getSidebarStatus returns opened", () => {
      const store = useAppStore();
      expect(store.getSidebarStatus).toBe(true);
    });

    it("getDevice returns device", () => {
      const store = useAppStore();
      expect(store.getDevice).toBe("desktop");
    });

    it("getViewportWidth returns width", () => {
      const store = useAppStore();
      expect(typeof store.getViewportWidth).toBe("number");
    });

    it("getViewportHeight returns height", () => {
      const store = useAppStore();
      expect(typeof store.getViewportHeight).toBe("number");
    });
  });

  describe("actions", () => {
    it("TOGGLE_SIDEBAR toggles sidebar opened", () => {
      const store = useAppStore();
      expect(store.sidebar.opened).toBe(true);
      store.TOGGLE_SIDEBAR(false);
      expect(store.sidebar.opened).toBe(false);
    });

    it("toggleDevice sets device", () => {
      const store = useAppStore();
      store.toggleDevice("mobile");
      expect(store.device).toBe("mobile");
    });

    it("setLayout sets layout", () => {
      const store = useAppStore();
      store.setLayout("horizontal");
      expect(store.layout).toBe("horizontal");
    });

    it("setViewportSize sets viewport size", () => {
      const store = useAppStore();
      store.setViewportSize({ width: 1920, height: 1080 });
      expect(store.viewportSize.width).toBe(1920);
      expect(store.viewportSize.height).toBe(1080);
    });

    it("setSortSwap sets sortSwap", () => {
      const store = useAppStore();
      store.setSortSwap(true);
      expect(store.sortSwap).toBe(true);
    });
  });
});

describe("store/modules/settings", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("state", () => {
    it("has default values from config", () => {
      const store = useSettingStore();
      expect(store.title).toBe("ZgAdmin");
      expect(store.fixedHeader).toBe(false);
      expect(store.hiddenSideBar).toBe(false);
    });
  });

  describe("getters", () => {
    it("getTitle returns title", () => {
      const store = useSettingStore();
      expect(store.getTitle).toBe("ZgAdmin");
    });

    it("getFixedHeader returns fixedHeader", () => {
      const store = useSettingStore();
      expect(store.getFixedHeader).toBe(false);
    });

    it("getHiddenSideBar returns hiddenSideBar", () => {
      const store = useSettingStore();
      expect(store.getHiddenSideBar).toBe(false);
    });
  });

  describe("actions", () => {
    it("CHANGE_SETTING updates existing key", () => {
      const store = useSettingStore();
      store.CHANGE_SETTING({ key: "title", value: "NewTitle" });
      expect(store.title).toBe("NewTitle");
    });

    it("CHANGE_SETTING ignores unknown key", () => {
      const store = useSettingStore();
      store.CHANGE_SETTING({ key: "unknown", value: "value" });
      expect((store as any).unknown).toBeUndefined();
    });

    it("changeSetting delegates to CHANGE_SETTING", () => {
      const store = useSettingStore();
      store.changeSetting({ key: "fixedHeader", value: true });
      expect(store.fixedHeader).toBe(true);
    });
  });
});

describe("store/modules/epTheme", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("state", () => {
    it("has default epThemeColor from config", () => {
      const store = useEpThemeStore();
      expect(store.epThemeColor).toBe("#409eff");
    });
  });

  describe("getters", () => {
    it("getEpThemeColor returns epThemeColor", () => {
      const store = useEpThemeStore();
      expect(store.getEpThemeColor).toBe("#409eff");
    });

    it("fill returns #409eff for light theme", () => {
      const store = useEpThemeStore();
      store.epTheme = "light";
      expect(store.fill).toBe("#409eff");
    });

    it("fill returns #fff for dark theme", () => {
      const store = useEpThemeStore();
      store.epTheme = "dark";
      expect(store.fill).toBe("#fff");
    });
  });

  describe("actions", () => {
    it("setEpThemeColor updates color and saves to localStorage", () => {
      const store = useEpThemeStore();
      store.setEpThemeColor("#ff0000");
      expect(store.epThemeColor).toBe("#ff0000");
      expect(mockSetItem).toHaveBeenCalled();
    });
  });
});
