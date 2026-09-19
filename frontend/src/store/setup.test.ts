import { describe, it, expect, vi } from "vitest";

vi.unmock("@/store");

describe("store/index", () => {
  it("exports a pinia instance and setupStore installs it", async () => {
    const mod = await import("@/store");
    expect(mod.store).toBeDefined();
    const app = { use: vi.fn() } as any;
    mod.setupStore(app);
    expect(app.use).toHaveBeenCalledWith(mod.store);
  });
});
