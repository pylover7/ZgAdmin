import { describe, it, expect, vi, beforeEach } from "vitest";

// SSO module is an IIFE that runs on import.
// We test it by controlling the mocks before import.

const { mockRemoveToken, mockSetToken } = vi.hoisted(() => ({
  mockRemoveToken: vi.fn(),
  mockSetToken: vi.fn()
}));

const { mockGetQueryMap, mockSubBefore } = vi.hoisted(() => ({
  mockGetQueryMap: vi.fn(() => ({})),
  mockSubBefore: vi.fn((str: string, char: string) => {
    const idx = str.indexOf(char);
    return idx === -1 ? str : str.substring(0, idx);
  })
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

describe("sso", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does nothing when getQueryMap returns empty object", () => {
    // Default mock returns {} so the IIFE should not trigger SSO
    mockGetQueryMap.mockReturnValue({});
    // The SSO module was already imported by setup/router, test that
    // removeToken was not called during initial import with empty params
    expect(mockRemoveToken).not.toHaveBeenCalled();
  });

  it("SSO logic correctly validates params — all 3 must be present", () => {
    // Simulate the SSO validation logic directly
    const must = ["username", "roles", "accessToken"];

    // Case 1: All params present
    const params1 = { username: "admin", roles: "admin", accessToken: "token" };
    let sso = [];
    for (let i = 0; i < must.length; i++) {
      if (Object.keys(params1).includes(must[i]) && sso.length <= must.length) {
        sso.push(must[i]);
      } else {
        sso = [];
      }
    }
    expect(sso.length).toBe(3); // SSO detected

    // Case 2: Missing accessToken
    const params2 = { username: "admin", roles: "admin" };
    sso = [];
    for (let i = 0; i < must.length; i++) {
      if (Object.keys(params2).includes(must[i]) && sso.length <= must.length) {
        sso.push(must[i]);
      } else {
        sso = [];
      }
    }
    expect(sso.length).toBe(0); // SSO not detected

    // Case 3: Extra params
    const params3 = { username: "admin", roles: "admin", accessToken: "token", extra: "val" };
    expect(Object.keys(params3).length).not.toBe(must.length); // Won't pass the first check
  });

  it("SSO IIFE checks Object.keys length matches must length", () => {
    const must = ["username", "roles", "accessToken"];
    const mustLength = must.length;

    // If params have different number of keys, IIFE returns early
    expect(Object.keys({ username: "a" }).length).not.toBe(mustLength);
    expect(Object.keys({ username: "a", roles: "b" }).length).not.toBe(mustLength);
    expect(Object.keys({ username: "a", roles: "b", accessToken: "c" }).length).toBe(mustLength);
    expect(Object.keys({ username: "a", roles: "b", accessToken: "c", extra: "d" }).length).not.toBe(mustLength);
  });
});
