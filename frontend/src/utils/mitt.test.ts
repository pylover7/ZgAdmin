import { describe, it, expect } from "vitest";
import { emitter } from "@/utils/mitt";

describe("mitt emitter", () => {
  it("emits and receives events", () => {
    let received = "";
    emitter.on("openPanel", (val: string) => {
      received = val;
    });
    emitter.emit("openPanel", "test-value");
    expect(received).toBe("test-value");
    emitter.off("openPanel");
  });

  it("supports multiple event types", () => {
    let tagValue = "";
    let logoValue = false;
    emitter.on("tagOnClick", (val: string) => {
      tagValue = val;
    });
    emitter.on("logoChange", (val: boolean) => {
      logoValue = val;
    });

    emitter.emit("tagOnClick", "tag1");
    emitter.emit("logoChange", true);

    expect(tagValue).toBe("tag1");
    expect(logoValue).toBe(true);

    emitter.off("tagOnClick");
    emitter.off("logoChange");
  });
});
