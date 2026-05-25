import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import * as fileApi from "@/api/file";

describe("api/file", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uploadFile calls POST /api/v1/resource/file/upload with FormData", () => {
    const fd = new FormData();
    fd.append("file", new Blob(["test"]), "test.txt");
    fileApi.uploadFile(fd);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/resource/file/upload", expect.objectContaining({
      headers: { "Content-Type": "multipart/form-data" }
    }));
  });

  it("uploadBatch calls POST /api/v1/resource/file/upload-batch", () => {
    const fd = new FormData();
    fileApi.uploadBatch(fd);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/resource/file/upload-batch", expect.objectContaining({
      headers: { "Content-Type": "multipart/form-data" }
    }));
  });

  it("getFileList calls POST /api/v1/resource/file/list", () => {
    fileApi.getFileList({ category: "image" }, 1, 15);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/resource/file/list", {
      data: { category: "image" },
      params: { currentPage: 1, pageSize: 15 }
    });
  });

  it("updateFile calls POST /api/v1/resource/file/update", () => {
    fileApi.updateFile({ id: "1", name: "renamed" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/resource/file/update", { data: { id: "1", name: "renamed" } });
  });

  it("deleteFile calls POST /api/v1/resource/file/delete", () => {
    fileApi.deleteFile(["f1"]);
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/resource/file/delete", { data: ["f1"] });
  });

  it("previewFile calls GET /api/v1/resource/file/preview/:id with blob response", () => {
    fileApi.previewFile("file-1");
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/resource/file/preview/file-1", { responseType: "blob" });
  });

  it("getSignedUrl calls GET /api/v1/resource/file/sign-url/:id", () => {
    fileApi.getSignedUrl("file-1");
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/resource/file/sign-url/file-1");
  });

  it("getStorageStats calls GET /api/v1/resource/file/stats", () => {
    fileApi.getStorageStats();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/resource/file/stats");
  });
});
