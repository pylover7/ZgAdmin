import { describe, it, expect } from "vitest";

// Test that the store module exports correctly (basic smoke test)
// Deep store testing requires full pinia setup which is tested via component tests

describe("store/index", () => {
  it("exports createPinia store", async () => {
    const mod = await import("@/store");
    expect(mod.store).toBeDefined();
  });
});
