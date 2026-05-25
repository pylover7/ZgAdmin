import { describe, it, expect, vi, beforeEach } from "vitest";
import type { App } from "vue";

const { mockStorageGetData } = vi.hoisted(() => ({
  mockStorageGetData: vi.fn(() => null)
}));

vi.mock("responsive-storage", () => ({
  default: {
    getData: mockStorageGetData,
    install: vi.fn()
  }
}));

vi.mock("@/layout/types", () => ({
  routerArrays: []
}));

vi.mock("@/config", () => ({
  responsiveStorageNameSpace: vi.fn(() => "responsive-")
}));

import { injectResponsiveStorage } from "@/utils/responsive";

describe("responsive", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("injects responsive storage into app with default config", () => {
    const mockApp = {
      use: vi.fn(),
      config: { globalProperties: {} }
    } as unknown as App;

    const config = {
      Locale: "zh",
      Layout: "vertical",
      Theme: "light",
      DarkMode: false,
      SidebarStatus: true,
      EpThemeColor: "#409EFF",
      ThemeMode: "light",
      Grey: false,
      Weak: false,
      HideTabs: false,
      HideFooter: true,
      ShowLogo: true,
      TagsStyle: "smart",
      MultiTagsCache: false,
      Stretch: false
    } as PlatformConfigs;

    injectResponsiveStorage(mockApp, config);

    expect(mockApp.use).toHaveBeenCalled();
    // Should use Storage.getData for persisted values
    expect(mockStorageGetData).toHaveBeenCalled();
  });

  it("includes tags in storage when MultiTagsCache is enabled", () => {
    const mockApp = {
      use: vi.fn(),
      config: { globalProperties: {} }
    } as unknown as App;

    const config = {
      Locale: "zh",
      Layout: "vertical",
      Theme: "light",
      MultiTagsCache: true
    } as PlatformConfigs;

    injectResponsiveStorage(mockApp, config);

    // Should call getData for tags when MultiTagsCache is enabled
    expect(mockStorageGetData).toHaveBeenCalledWith("tags", "responsive-");
  });

  it("does not include tags when MultiTagsCache is disabled", () => {
    const mockApp = {
      use: vi.fn(),
      config: { globalProperties: {} }
    } as unknown as App;

    const config = {
      MultiTagsCache: false
    } as PlatformConfigs;

    injectResponsiveStorage(mockApp, config);

    // Should not call getData for tags
    const tagsCall = mockStorageGetData.mock.calls.find(
      (call: any[]) => call[0] === "tags"
    );
    expect(tagsCall).toBeUndefined();
  });
});
