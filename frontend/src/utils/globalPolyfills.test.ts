import { describe, it, expect, vi } from "vitest";
import "@/utils/globalPolyfills";

describe("globalPolyfills", () => {
  it("sets window.global to window when undefined", () => {
    expect((window as any).global).toBe(window);
  });
});

describe("globalPolyfills fallback branch", () => {
  it("assigns window.global when it is undefined", async () => {
    const original = (window as any).global;
    delete (window as any).global;
    vi.resetModules();
    await import("@/utils/globalPolyfills");
    expect((window as any).global).toBe(window);
    (window as any).global = original;
  });
});
