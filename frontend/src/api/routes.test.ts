import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import { getAsyncRoutes } from "@/api/routes";

describe("api/routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getAsyncRoutes calls GET /api/v1/base/userMenu", () => {
    getAsyncRoutes();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/base/userMenu");
  });
});
