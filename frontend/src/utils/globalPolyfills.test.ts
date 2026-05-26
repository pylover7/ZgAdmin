import { describe, it, expect } from "vitest";
import { globalPolyfills } from "@/utils/globalPolyfills";

describe("globalPolyfills", () => {
  it("module exports nothing (side-effect only)", () => {
    // The file is side-effect only; importing it sets window.global
    expect(globalPolyfills).toBeUndefined();
  });

  it("sets window.global to window when undefined", () => {
    // Already set by import
    expect((window as any).global).toBe(window);
  });
});
