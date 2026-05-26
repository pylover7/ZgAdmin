import { describe, it, expect, vi, beforeEach } from "vitest";
import Cookies from "js-cookie";
import { storageLocal } from "@pureadmin/utils";

// Mock useUserStoreHook before importing auth
const mockStore = {
  isRemembered: false,
  loginDay: 7,
  username: "",
  nickname: "",
  roles: [] as string[],
  permissions: [] as string[],
  SET_USERNAME: vi.fn(),
  SET_NICKNAME: vi.fn(),
  SET_ROLES: vi.fn(),
  SET_PERMS: vi.fn()
};

vi.mock("@/store/modules/user", () => ({
  useUserStoreHook: () => mockStore
}));

import {
  formatToken,
  hasPerms,
  getToken,
  setToken,
  removeToken,
  userKey,
  TokenKey,
  multipleTabsKey
} from "@/utils/auth";

describe("auth utils", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockStore.isRemembered = false;
    mockStore.loginDay = 7;
    mockStore.permissions = [];
  });

  describe("formatToken", () => {
    it("prepends 'Bearer ' to token", () => {
      expect(formatToken("abc123")).toBe("Bearer abc123");
    });

    it("handles empty string", () => {
      expect(formatToken("")).toBe("Bearer ");
    });
  });

  describe("getToken", () => {
    it("returns parsed cookie value when cookie exists", () => {
      const tokenData = {
        accessToken: "test",
        expires: 123,
        refreshToken: "refresh"
      };
      (Cookies.get as ReturnType<typeof vi.fn>).mockReturnValue(
        JSON.stringify(tokenData)
      );
      const result = getToken();
      expect(result).toEqual(tokenData);
    });

    it("falls back to localStorage when cookie does not exist", () => {
      (Cookies.get as ReturnType<typeof vi.fn>).mockReturnValue(undefined);
      const localData = {
        accessToken: "local",
        expires: 456,
        refreshToken: "r2"
      };
      (storageLocal as ReturnType<typeof vi.fn>).mockReturnValue({
        getItem: vi.fn(() => localData)
      });
      const result = getToken();
      expect(result).toEqual(localData);
    });
  });

  describe("setToken", () => {
    it("sets cookie with future expiry and calls store SET methods when username+roles provided", () => {
      const futureDate = new Date(Date.now() + 86400000);
      const data = {
        accessToken: "at",
        refreshToken: "rt",
        expires: futureDate,
        username: "admin",
        roles: ["admin"],
        permissions: ["*:*:*"]
      };

      (storageLocal as ReturnType<typeof vi.fn>).mockReturnValue({
        getItem: vi.fn(() => null),
        setItem: vi.fn()
      });

      setToken(data);

      expect(Cookies.set).toHaveBeenCalledWith(
        TokenKey,
        expect.any(String),
        expect.objectContaining({})
      );
      expect(Cookies.set).toHaveBeenCalledWith(
        multipleTabsKey,
        "true",
        expect.any(Object)
      );
      expect(mockStore.SET_USERNAME).toHaveBeenCalledWith("admin");
      expect(mockStore.SET_ROLES).toHaveBeenCalledWith(["admin"]);
      expect(mockStore.SET_PERMS).toHaveBeenCalledWith(["*:*:*"]);
    });

    it("sets cookie without expiry when expires is 0", () => {
      const data = {
        accessToken: "at",
        refreshToken: "rt",
        expires: new Date(0)
      };

      (storageLocal as ReturnType<typeof vi.fn>).mockReturnValue({
        getItem: vi.fn(() => ({
          username: "cached",
          roles: ["r"],
          permissions: []
        })),
        setItem: vi.fn()
      });

      setToken(data);
      // Should call Cookies.set with 2 args (no expires option)
      expect(Cookies.set).toHaveBeenCalledWith(TokenKey, expect.any(String));
    });

    it("sets cookie with isRemembered and loginDay", () => {
      mockStore.isRemembered = true;
      mockStore.loginDay = 30;

      const data = {
        accessToken: "at",
        refreshToken: "rt",
        expires: new Date(Date.now() + 86400000),
        username: "admin",
        roles: ["admin"]
      };

      (storageLocal as ReturnType<typeof vi.fn>).mockReturnValue({
        getItem: vi.fn(() => null),
        setItem: vi.fn()
      });

      setToken(data);
      expect(Cookies.set).toHaveBeenCalledWith(multipleTabsKey, "true", {
        expires: 30
      });
    });
  });

  describe("removeToken", () => {
    it("removes cookies and localStorage item", () => {
      const mockRemoveItem = vi.fn();
      (storageLocal as ReturnType<typeof vi.fn>).mockReturnValue({
        removeItem: mockRemoveItem
      });

      removeToken();
      expect(Cookies.remove).toHaveBeenCalledWith(TokenKey);
      expect(Cookies.remove).toHaveBeenCalledWith(multipleTabsKey);
      expect(mockRemoveItem).toHaveBeenCalledWith(userKey);
    });
  });

  describe("hasPerms", () => {
    it("returns false for falsy value", () => {
      expect(hasPerms("")).toBe(false);
    });

    it("returns false for undefined value", () => {
      expect(hasPerms(undefined as any)).toBe(false);
    });

    it("returns true when permissions has '*:*:*' (superuser)", () => {
      mockStore.permissions = ["*:*:*"];
      expect(hasPerms("system:user:add")).toBe(true);
    });

    it("returns true when string permission is in permissions list", () => {
      mockStore.permissions = ["system:user:add", "system:role:edit"];
      expect(hasPerms("system:user:add")).toBe(true);
    });

    it("returns false when string permission is NOT in permissions list", () => {
      mockStore.permissions = ["system:user:add"];
      expect(hasPerms("system:menu:delete")).toBe(false);
    });

    it("returns false when permissions is empty array", () => {
      mockStore.permissions = [];
      expect(hasPerms("system:user:add")).toBe(false);
    });
  });
});
