import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockStorage } = vi.hoisted(() => ({
  mockStorage: {
    config: vi.fn(),
    setItem: vi.fn(),
    getItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    keys: vi.fn(),
    INDEXEDDB: "asyncStorage",
    LOCALSTORAGE: "localStorageWrapper"
  }
}));

vi.mock("localforage", () => ({
  default: mockStorage
}));

import { localForage } from "@/utils/localforage";

describe("localforage StorageProxy", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("configures localforage on construction", () => {
    localForage();
    expect(mockStorage.config).toHaveBeenCalledWith({
      driver: ["asyncStorage", "localStorageWrapper"],
      name: "pure-admin"
    });
  });

  describe("setItem", () => {
    it("stores data with no expiration (m=0)", async () => {
      mockStorage.setItem.mockImplementation((k, v) => Promise.resolve(v));
      const store = localForage();
      await store.setItem("key", "value", 0);
      expect(mockStorage.setItem).toHaveBeenCalledWith("key", {
        data: "value",
        expires: 0
      });
    });

    it("stores data with expiration in minutes", async () => {
      mockStorage.setItem.mockImplementation((k, v) => Promise.resolve(v));
      const store = localForage();
      await store.setItem("key", "value", 30);
      const call = mockStorage.setItem.mock.calls[0];
      expect(call[1].data).toBe("value");
      expect(call[1].expires).toBeGreaterThan(Date.now());
    });

    it("resolves with data on success", async () => {
      mockStorage.setItem.mockResolvedValue({ data: "stored", expires: 0 });
      const store = localForage();
      const result = await store.setItem("key", "stored", 0);
      expect(result).toBe("stored");
    });

    it("rejects on error", async () => {
      mockStorage.setItem.mockRejectedValue(new Error("Write error"));
      const store = localForage();
      await expect(store.setItem("key", "value")).rejects.toThrow("Write error");
    });
  });

  describe("getItem", () => {
    it("returns data when not expired", async () => {
      mockStorage.getItem.mockResolvedValue({
        data: "cached",
        expires: Date.now() + 60000
      });
      const store = localForage();
      const result = await store.getItem("key");
      expect(result).toBe("cached");
    });

    it("returns data when expires is 0 (permanent)", async () => {
      mockStorage.getItem.mockResolvedValue({
        data: "permanent",
        expires: 0
      });
      const store = localForage();
      const result = await store.getItem("key");
      expect(result).toBe("permanent");
    });

    it("returns null when expired", async () => {
      mockStorage.getItem.mockResolvedValue({
        data: "old",
        expires: Date.now() - 60000
      });
      const store = localForage();
      const result = await store.getItem("key");
      expect(result).toBeNull();
    });

    it("returns null when item does not exist", async () => {
      mockStorage.getItem.mockResolvedValue(null);
      const store = localForage();
      const result = await store.getItem("missing");
      expect(result).toBeNull();
    });

    it("rejects on error", async () => {
      mockStorage.getItem.mockRejectedValue(new Error("Read error"));
      const store = localForage();
      await expect(store.getItem("key")).rejects.toThrow("Read error");
    });
  });

  describe("removeItem", () => {
    it("removes item from storage", async () => {
      mockStorage.removeItem.mockResolvedValue(undefined);
      const store = localForage();
      await store.removeItem("key");
      expect(mockStorage.removeItem).toHaveBeenCalledWith("key");
    });

    it("rejects on error", async () => {
      mockStorage.removeItem.mockRejectedValue(new Error("Remove error"));
      const store = localForage();
      await expect(store.removeItem("key")).rejects.toThrow("Remove error");
    });
  });

  describe("clear", () => {
    it("clears all items", async () => {
      mockStorage.clear.mockResolvedValue(undefined);
      const store = localForage();
      await store.clear();
      expect(mockStorage.clear).toHaveBeenCalled();
    });

    it("rejects on error", async () => {
      mockStorage.clear.mockRejectedValue(new Error("Clear error"));
      const store = localForage();
      await expect(store.clear()).rejects.toThrow("Clear error");
    });
  });

  describe("keys", () => {
    it("returns all keys", async () => {
      mockStorage.keys.mockResolvedValue(["key1", "key2"]);
      const store = localForage();
      const result = await store.keys();
      expect(result).toEqual(["key1", "key2"]);
    });

    it("rejects on error", async () => {
      mockStorage.keys.mockRejectedValue(new Error("Keys error"));
      const store = localForage();
      await expect(store.keys()).rejects.toThrow("Keys error");
    });
  });
});
