import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: vi.fn()
}));

vi.mock("@/utils/http", () => ({
  http: { request: mockRequest }
}));

import {
  getLogin,
  refreshTokenApi,
  getMine,
  updateProfile,
  updatePassword,
  getPreferences,
  updatePreferences,
  getMineLogs,
  getQQAuthUrl,
  qqLogin
} from "@/api/user";

describe("api/user", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getLogin calls POST /api/v1/base/accessToken", () => {
    getLogin({ username: "admin", password: "123456" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/base/accessToken",
      { data: { username: "admin", password: "123456" } }
    );
  });

  it("refreshTokenApi calls POST /api/v1/base/refreshToken", () => {
    refreshTokenApi({ refreshToken: "rt" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/base/refreshToken",
      { data: { refreshToken: "rt" } }
    );
  });

  it("getMine calls GET /api/v1/base/userinfo", () => {
    getMine();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/base/userinfo");
  });

  it("updateProfile calls POST /api/v1/base/updateProfile", () => {
    updateProfile({ nickname: "new" });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/base/updateProfile",
      { data: { nickname: "new" } }
    );
  });

  it("updatePassword calls POST /api/v1/base/updatePwd", () => {
    updatePassword({ current_password: "old", new_password: "new" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/base/updatePwd", {
      data: { current_password: "old", new_password: "new" }
    });
  });

  it("getPreferences calls GET /api/v1/base/preferences", () => {
    getPreferences();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/base/preferences");
  });

  it("updatePreferences calls POST /api/v1/base/updatePreferences", () => {
    updatePreferences({ notify_account: true });
    expect(mockRequest).toHaveBeenCalledWith(
      "post",
      "/api/v1/base/updatePreferences",
      { data: { notify_account: true } }
    );
  });

  it("getMineLogs calls GET /api/v1/base/loginLogs", () => {
    getMineLogs({ pageSize: 15, currentPage: 1 });
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/base/loginLogs", {
      params: { pageSize: 15, currentPage: 1 }
    });
  });

  it("getQQAuthUrl calls GET /api/v1/base/qq/auth-url", () => {
    getQQAuthUrl();
    expect(mockRequest).toHaveBeenCalledWith("get", "/api/v1/base/qq/auth-url");
  });

  it("qqLogin calls POST /api/v1/base/qq/login", () => {
    qqLogin({ code: "abc", state: "xyz" });
    expect(mockRequest).toHaveBeenCalledWith("post", "/api/v1/base/qq/login", {
      data: { code: "abc", state: "xyz" }
    });
  });
});
