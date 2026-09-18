import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({ mockRequest: vi.fn() }));

vi.mock("@/utils/http", () => ({ http: { request: mockRequest } }));

import { getCardList } from "@/api/list";

describe("api/list", () => {
  beforeEach(() => vi.clearAllMocks());

  it("getCardList POSTs /get-card-list with data", () => {
    getCardList({ page: 1 });
    expect(mockRequest).toHaveBeenCalledWith("post", "/get-card-list", {
      data: { page: 1 }
    });
  });

  it("getCardList works without args", () => {
    getCardList();
    expect(mockRequest).toHaveBeenCalledWith("post", "/get-card-list", {
      data: undefined
    });
  });
});
