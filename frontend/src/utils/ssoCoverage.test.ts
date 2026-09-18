import { describe, it, expect, vi, beforeEach } from "vitest";

const {
  mockRemoveToken,
  mockSetToken,
  mockGetQueryMap,
  mockSubBefore,
  mockReplace
} = vi.hoisted(() => ({
  mockRemoveToken: vi.fn(),
  mockSetToken: vi.fn(),
  mockGetQueryMap: vi.fn(() => ({})),
  mockSubBefore: vi.fn((str: string, char: string) => {
    const idx = str.indexOf(char);
    return idx === -1 ? str : str.substring(0, idx);
  }),
  mockReplace: vi.fn()
}));

vi.mock("@/utils/auth", () => ({
  removeToken: mockRemoveToken,
  setToken: mockSetToken,
  userKey: "user-info",
  TokenKey: "authorized-token",
  multipleTabsKey: "multiple-tabs"
}));

vi.mock("@pureadmin/utils", () => ({
  getQueryMap: mockGetQueryMap,
  subBefore: mockSubBefore
}));

async function loadSso(params: Record<string, string>) {
  mockGetQueryMap.mockReturnValue(params);
  vi.resetModules();
  await import("@/utils/sso");
}

describe("utils/sso IIFE", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // happy-dom 下替换 location.replace 以捕获跳转
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        href: "http://localhost/#/login?username=a",
        origin: "http://localhost",
        pathname: "/",
        hash: "#/page/index?username=sso&roles=admin&accessToken=tok",
        replace: mockReplace
      }
    });
  });

  it("does nothing when params count mismatches", async () => {
    await loadSso({ foo: "bar" });
    expect(mockRemoveToken).not.toHaveBeenCalled();
  });

  it("performs SSO flow when all required params present", async () => {
    await loadSso({
      username: "sso",
      roles: "admin",
      accessToken: "tok"
    });
    expect(mockRemoveToken).toHaveBeenCalled();
    expect(mockSetToken).toHaveBeenCalled();
    expect(mockReplace).toHaveBeenCalled();
  });

  it("falls into else branch when a must param is missing", async () => {
    await loadSso({ username: "sso", roles: "admin", extra: "x" });
    // key 数量与 must 相同但不匹配 → sso 被清空
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
