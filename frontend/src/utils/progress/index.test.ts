import { describe, it, expect, vi } from "vitest";

vi.mock("nprogress", () => ({
  default: {
    configure: vi.fn(),
    start: vi.fn(),
    done: vi.fn()
  }
}));

vi.mock("nprogress/nprogress.css", () => ({}));

import NProgress from "@/utils/progress";

describe("progress", () => {
  it("exports configured NProgress instance", () => {
    expect(NProgress).toBeDefined();
    expect(NProgress.start).toBeTypeOf("function");
    expect(NProgress.done).toBeTypeOf("function");
  });

  it("NProgress.configure was called with correct options", async () => {
    // Re-import to trigger configuration
    const { default: NProgressModule } = await import("nprogress");
    expect(NProgressModule.configure).toHaveBeenCalledWith({
      easing: "ease",
      speed: 500,
      showSpinner: false,
      trickleSpeed: 200,
      minimum: 0.3
    });
  });
});
