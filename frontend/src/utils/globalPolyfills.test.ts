import { describe, it, expect } from "vitest";
import "@/utils/globalPolyfills";

describe("globalPolyfills", () => {
  it("sets window.global to window when undefined", () => {
    expect((window as any).global).toBe(window);
  });
});
