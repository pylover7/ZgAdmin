import { describe, it, expect } from "vitest";
import { escapeHtml, escapeForHtml, isSafeHttpUrl } from "@/utils/escapeHtml";

describe("escapeHtml", () => {
  describe("基础转义", () => {
    it("转义全部 5 个特殊字符", () => {
      expect(escapeHtml(`& < > " '`)).toBe("&amp; &lt; &gt; &quot; &#39;");
    });

    it("阻断 script 标签闭合", () => {
      expect(escapeHtml("<script>alert(1)</script>")).toBe(
        "&lt;script&gt;alert(1)&lt;/script&gt;"
      );
    });

    it("阻断属性逃逸", () => {
      // 若 & 未先替换，会二次转义成 &amp;quot;
      expect(escapeHtml(`" onmouseover="alert(1)`)).toBe(
        "&quot; onmouseover=&quot;alert(1)"
      );
    });
  });

  describe("非字符串输入", () => {
    it("null / undefined 返回空串", () => {
      expect(escapeHtml(null)).toBe("");
      expect(escapeHtml(undefined)).toBe("");
    });

    it("数字与布尔值被字符串化", () => {
      expect(escapeHtml(1.5)).toBe("1.5");
      expect(escapeHtml(false)).toBe("false");
    });

    it("普通字符串原样返回", () => {
      expect(escapeHtml("v1.2.3")).toBe("v1.2.3");
    });

    it("中文与 emoji 不受影响", () => {
      expect(escapeHtml("新版本 v2 🎉")).toBe("新版本 v2 🎉");
    });
  });

  describe("边界：转义函数覆盖不到的场景（须由调用方另行防护）", () => {
    it("⚠️ 转义挡不住 javascript: 伪协议——这正是需要 isSafeHttpUrl 的原因", () => {
      const escaped = escapeHtml("javascript:alert(1)");
      // 转义后字符串本身没有特殊字符，HTML 实体化救不了它
      expect(escaped).toBe("javascript:alert(1)");
      // 放进 href 依然可点击执行 —— 故必须配合协议校验
      expect(escapeForHtml("javascript:alert(1)", { isUrl: true })).toBe("");
    });
  });
});

describe("isSafeHttpUrl", () => {
  it("放行 http / https", () => {
    expect(isSafeHttpUrl("http://example.com")).toBe(true);
    expect(isSafeHttpUrl("https://example.com/a?b=1#c")).toBe(true);
    expect(isSafeHttpUrl("HTTPS://EXAMPLE.COM")).toBe(true);
  });

  it("放行站内相对路径", () => {
    expect(isSafeHttpUrl("/about")).toBe(true);
  });

  it("拦截伪协议", () => {
    expect(isSafeHttpUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeHttpUrl("JavaScript:alert(1)")).toBe(false);
    expect(isSafeHttpUrl("  javascript:alert(1)")).toBe(false);
    expect(isSafeHttpUrl("data:text/html,<script>alert(1)</script>")).toBe(
      false
    );
    expect(isSafeHttpUrl("vbscript:msgbox(1)")).toBe(false);
  });

  it("拦截协议相对路径 //evil.com（会被当作跨站地址）", () => {
    expect(isSafeHttpUrl("//evil.com")).toBe(false);
  });

  it("拦截非字符串", () => {
    expect(isSafeHttpUrl(null)).toBe(false);
    expect(isSafeHttpUrl(undefined)).toBe(false);
    expect(isSafeHttpUrl(123)).toBe(false);
    expect(isSafeHttpUrl({})).toBe(false);
  });
});

describe("escapeForHtml", () => {
  it("默认等价于 escapeHtml（仅转义）", () => {
    expect(escapeForHtml("<b>hi</b>")).toBe("&lt;b&gt;hi&lt;/b&gt;");
  });

  it("isUrl 时对不安全 URL 返回空串", () => {
    expect(escapeForHtml("javascript:alert(1)", { isUrl: true })).toBe("");
    expect(escapeForHtml("data:text/html,x", { isUrl: true })).toBe("");
  });

  it("isUrl 时对安全 URL 正常转义", () => {
    expect(escapeForHtml("https://example.com?a=1&b=2", { isUrl: true })).toBe(
      "https://example.com?a=1&amp;b=2"
    );
  });

  it("isUrl 不成立时回退空串，不残留部分内容", () => {
    expect(escapeForHtml("javascript:alert(1)", { isUrl: true })).not.toContain(
      "javascript"
    );
  });
});
