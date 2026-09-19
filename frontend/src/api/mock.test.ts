import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({ mockRequest: vi.fn() }));

vi.mock("@/utils/http", () => ({ http: { request: mockRequest } }));

import { mapJson, formUpload } from "@/api/mock";

describe("api/mock", () => {
  beforeEach(() => vi.clearAllMocks());

  it("mapJson GETs /get-map-info with params", () => {
    mapJson({ id: 1 });
    expect(mockRequest).toHaveBeenCalledWith("get", "/get-map-info", {
      params: { id: 1 }
    });
  });

  it("formUpload POSTs multipart to mocky", () => {
    const data = { file: "x" };
    formUpload(data);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "https://run.mocky.io/v3/3aa761d7-b0b3-4a03-96b3-6168d4f7467b",
      { data },
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  });
});
