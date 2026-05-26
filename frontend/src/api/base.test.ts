import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import { getInitConfig, getCaptcha } from "@/api/base";

describe("api/base", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getInitConfig calls GET /api/v1/base/init", () => {
    getInitConfig();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/base/init");
  });

  it("getCaptcha calls GET /api/v1/base/captcha", () => {
    getCaptcha();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/base/captcha");
  });
});
