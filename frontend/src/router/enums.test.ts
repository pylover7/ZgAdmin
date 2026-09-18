import { describe, it, expect } from "vitest";

import { HOME, ERROR, ABOUT } from "@/router/enums";

describe("router/enums", () => {
  it("exports rank constants", () => {
    expect(HOME).toBe(0);
    expect(ERROR).toBe(110);
    expect(ABOUT).toBe(999);
  });
});
