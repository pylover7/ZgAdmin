import { describe, it, expect, vi, beforeEach } from "vitest";
import { message, closeAllMessage } from "@/utils/message";
import { ElMessage } from "element-plus";

describe("message utils", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls ElMessage with default antd style when no params", () => {
    message("hello");
    expect(ElMessage).toHaveBeenCalledWith({
      message: "hello",
      customClass: "pure-message"
    });
  });

  it("calls ElMessage with antd customClass when customClass is 'antd'", () => {
    message("hello", { customClass: "antd" });
    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        customClass: "pure-message"
      })
    );
  });

  it("calls ElMessage with empty customClass when customClass is 'el'", () => {
    message("hello", { customClass: "el" });
    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        customClass: ""
      })
    );
  });

  it("passes all params to ElMessage", () => {
    const onClose = vi.fn();
    message("hello", {
      type: "success",
      plain: true,
      duration: 5000,
      showClose: true,
      onClose
    });
    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "success",
        plain: true,
        duration: 5000,
        showClose: true,
        onClose: expect.any(Function)
      })
    );
  });

  it("closeAllMessage calls ElMessage.closeAll", () => {
    closeAllMessage();
    expect(ElMessage.closeAll).toHaveBeenCalled();
  });
});

describe("message onClose closure", () => {
  beforeEach(() => vi.clearAllMocks());

  it("invokes provided onClose callback", () => {
    const onClose = vi.fn();
    message("hi", { onClose });
    const arg = (ElMessage as any).mock.calls[0][0];
    arg.onClose();
    expect(onClose).toHaveBeenCalled();
  });

  it("handles non-function onClose gracefully", () => {
    message("hi", { onClose: "not-a-function" as any });
    const arg = (ElMessage as any).mock.calls[0][0];
    expect(() => arg.onClose()).not.toThrow();
  });
});
