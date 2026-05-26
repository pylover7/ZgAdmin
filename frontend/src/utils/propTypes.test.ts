import { describe, it, expect } from "vitest";

describe("propTypes", () => {
  it("exports propTypes class with style and VNodeChild getters", async () => {
    const { default: propTypes } = await import("@/utils/propTypes");
    expect(propTypes).toBeDefined();
    expect(propTypes.style).toBeDefined();
    expect(propTypes.VNodeChild).toBeDefined();
  });
});
