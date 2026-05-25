import { describe, it, expect, vi, beforeEach } from "vitest";

vi.unmock("@/config");

const { mockAxios } = vi.hoisted(() => ({
  mockAxios: vi.fn()
}));

vi.mock("axios", () => ({
  default: mockAxios
}));

import { getConfig, setConfig, responsiveStorageNameSpace, paginationConf, getPlatformConfig } from "@/config";

describe("config", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setConfig({ ResponsiveStorageNameSpace: "responsive-" });
  });

  describe("setConfig / getConfig", () => {
    it("returns config after setting", () => {
      setConfig({ Title: "TestApp", Layout: "vertical" });
      const result = getConfig();
      expect(result.Title).toBe("TestApp");
      expect(result.Layout).toBe("vertical");
    });

    it("merges new config with existing", () => {
      setConfig({ Title: "First" });
      setConfig({ Layout: "horizontal" });
      const result = getConfig();
      expect(result.Title).toBe("First");
      expect(result.Layout).toBe("horizontal");
    });

    it("overrides existing keys", () => {
      setConfig({ Title: "Old" });
      setConfig({ Title: "New" });
      expect(getConfig().Title).toBe("New");
    });

    it("returns nested value by dot-separated key", () => {
      setConfig({ Theme: { primary: "#409eff" } });
      expect(getConfig("Theme.primary")).toBe("#409eff");
    });

    it("returns null for non-existent nested key", () => {
      setConfig({ Theme: { primary: "#409eff" } });
      expect(getConfig("Theme.nonexistent")).toBeNull();
    });

    it("returns null for deeply nested non-existent key", () => {
      setConfig({ a: 1 });
      expect(getConfig("a.b.c")).toBeNull();
    });

    it("returns whole config when key is not a string", () => {
      setConfig({ Title: "Test" });
      expect(getConfig(undefined as any).Title).toBe("Test");
    });

    it("returns null for empty string key", () => {
      setConfig({ Title: "Test" });
      expect(getConfig("")).toBeNull();
    });

    it("handles numeric key path gracefully", () => {
      setConfig({ items: ["a", "b", "c"] });
      expect(getConfig("items.0")).toBe("a");
    });
  });

  describe("responsiveStorageNameSpace", () => {
    it("returns the ResponsiveStorageNameSpace from config", () => {
      setConfig({ ResponsiveStorageNameSpace: "my-app-" });
      expect(responsiveStorageNameSpace()).toBe("my-app-");
    });

    it("returns the value when ResponsiveStorageNameSpace is set", () => {
      setConfig({ ResponsiveStorageNameSpace: "my-app-" });
      expect(responsiveStorageNameSpace()).toBe("my-app-");
    });

    it("returns previously set value when overwritten", () => {
      setConfig({ ResponsiveStorageNameSpace: "responsive-" });
      expect(responsiveStorageNameSpace()).toBe("responsive-");
      setConfig({ ResponsiveStorageNameSpace: "new-ns-" });
      expect(responsiveStorageNameSpace()).toBe("new-ns-");
    });
  });

  describe("paginationConf", () => {
    it("has correct default values", () => {
      expect(paginationConf.total).toBe(0);
      expect(paginationConf.pageSize).toBe(15);
      expect(paginationConf.currentPage).toBe(1);
      expect(paginationConf.pageSizes).toEqual([5, 15, 30, 50, 100]);
      expect(paginationConf.background).toBe(true);
    });
  });

  describe("getPlatformConfig", () => {
    it("fetches platform config and merges with API data", async () => {
      const mockApp = {
        config: { globalProperties: { $config: {} } },
        use: vi.fn()
      } as any;

      // First axios call: fetch platform-config.json
      // Second axios call: fetch /api/v1/base/init
      mockAxios
        .mockResolvedValueOnce({
          data: {
            Title: "Platform Title",
            Layout: "vertical",
            ResponsiveStorageNameSpace: "responsive-"
          }
        })
        .mockResolvedValueOnce({
          data: {
            success: true,
            data: {
              site: {
                site_name: "ZgAdmin",
                site_desc: "Admin Panel",
                logo: "/logo.png",
                default_lang: "zh",
                copyright: "2024",
                icp: "ICP123"
              },
              features: { qq_login: false, wechat_login: false, email: true, monitor_log: true },
              security: { captcha_enabled: true }
            }
          }
        });

      const result = await getPlatformConfig(mockApp);

      expect(mockAxios).toHaveBeenCalledTimes(2);
      expect(mockApp.config.globalProperties.$config.Title).toBe("ZgAdmin");
      expect(mockApp.config.globalProperties.$config.Features.qq_login).toBe(false);
      expect(mockApp.config.globalProperties.$config.Security.captcha_enabled).toBe(true);
    });

    it("handles API failure gracefully", async () => {
      const mockApp = {
        config: { globalProperties: { $config: {} } },
        use: vi.fn()
      } as any;

      mockAxios
        .mockResolvedValueOnce({
          data: { Title: "Platform Title" }
        })
        .mockRejectedValueOnce(new Error("API unavailable"));

      const result = await getPlatformConfig(mockApp);
      expect(mockApp.config.globalProperties.$config.Title).toBe("Platform Title");
    });

    it("throws when platform-config.json is unavailable", async () => {
      const mockApp = {
        config: { globalProperties: { $config: {} } },
        use: vi.fn()
      } as any;

      mockAxios.mockRejectedValueOnce(new Error("Config not found"));

      await expect(getPlatformConfig(mockApp)).rejects.toBe(
        "请在public文件夹下添加platform-config.json配置文件"
      );
    });

    it("merges API site info only when apiData is valid", async () => {
      const mockApp = {
        config: { globalProperties: { $config: {} } },
        use: vi.fn()
      } as any;

      mockAxios
        .mockResolvedValueOnce({ data: { Title: "Default" } })
        .mockResolvedValueOnce({ data: { success: false } });

      await getPlatformConfig(mockApp);
      // Should keep default title when API returns success=false
      expect(mockApp.config.globalProperties.$config.Title).toBe("Default");
    });
  });
});
