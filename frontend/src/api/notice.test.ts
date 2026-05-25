import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import * as noticeApi from "@/api/notice";

describe("api/notice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("addNotice calls POST /api/v1/system/notice/add", () => {
    noticeApi.addNotice({ title: "test" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/notice/add",
      { data: { title: "test" } }
    );
  });

  it("getNoticeList calls POST /api/v1/system/notice/list", () => {
    noticeApi.getNoticeList("title", null, "info", null, 1, 15);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/notice/list",
      expect.objectContaining({
        data: { title: "title", type: null, level: "info", status: null },
        params: { pageSize: 15, currentPage: 1 }
      })
    );
  });

  it("updateNotice calls POST /api/v1/system/notice/update", () => {
    noticeApi.updateNotice({ id: "1", title: "updated" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/notice/update",
      { data: { id: "1", title: "updated" } }
    );
  });

  it("deleteNotice calls POST /api/v1/system/notice/delete", () => {
    noticeApi.deleteNotice(["1"]);
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/notice/delete",
      { data: ["1"] }
    );
  });

  it("getUnreadNotices calls GET /api/v1/system/notice/unread", () => {
    noticeApi.getUnreadNotices();
    expect(mockRequest).toHaveBeenCalledWith(
      "get",
      "/api/v1/system/notice/unread"
    );
  });

  it("markNoticeRead calls POST /api/v1/system/notice/read", () => {
    noticeApi.markNoticeRead("notice-1");
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/notice/read",
      { data: { notice_id: "notice-1" } }
    );
  });

  it("markAllRead calls POST /api/v1/system/notice/readAll", () => {
    noticeApi.markAllRead();
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/system/notice/readAll"
    );
  });
});
