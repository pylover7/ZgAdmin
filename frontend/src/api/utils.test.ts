import { describe, it, expect } from "vitest";
import { baseUrlApi, apiV1 } from "@/api/utils";

describe("api utils", () => {
  describe("baseUrlApi", () => {
    it("prepends /api to url", () => {
      expect(baseUrlApi("/users")).toBe("/api/users");
    });

    it("handles empty string", () => {
      expect(baseUrlApi("")).toBe("/api");
    });
  });

  describe("apiV1", () => {
    it("prepends /api/v1 to url", () => {
      expect(apiV1("/users")).toBe("/api/v1/users");
    });

    it("handles empty string", () => {
      expect(apiV1("")).toBe("/api/v1");
    });
  });
});
