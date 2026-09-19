/**
 * HTML 转义工具 — 用于 `dangerouslyUseHTMLString` 场景的动态值消毒。
 *
 * ## ⚠️ 适用边界（务必先读，用错上下文会**静默失效**）
 *
 * 转义的**完备性取决于值所处的上下文**，不取决于「有没有调用转义函数」：
 *
 * | 上下文 | 本函数是否足够 |
 * |---|---|
 * | 文本节点（`<div>${v}</div>`） | ✅ 足够 |
 * | 带引号的属性（`<a href="${v}">`） | ⚠️ 可阻断引号闭合，**但挡不住 `javascript:` 等伪协议** |
 * | 不带引号的属性（`<a href=${v}>`） | ❌ 不足（空格即可逃逸属性） |
 * | 执行上下文（`<script>` / `onclick=`） | ❌ 不足 |
 *
 * **需要更强保证时改用 DOM API**（`textContent` / `setAttribute`），让浏览器负责转义，
 * 而不是自己拼字符串——但 `ElMessageBox` / `ElNotification` 的 `message` 只接受字符串，
 * 这些场景做不到，此时必须**对 URL 类值另行校验协议白名单**（见 `isSafeHttpUrl`）。
 *
 * @see .codebuddy/rules/frontend-architecture.md 第 12 / 13 条
 */

/** 转义映射：`&` 必须最先替换，否则会二次转义后续产生的实体 */
const ESCAPE_MAP: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
};

const ESCAPE_RE = /[&<>"']/g;

/**
 * 转义 HTML 特殊字符（`& < > " '`）。
 *
 * @param value 待转义的值，非字符串会被 `String()` 转换（`null` / `undefined` 转为空串）
 * @returns 转义后的字符串
 *
 * @example
 * escapeHtml('<script>alert(1)</script>')
 * // => '&lt;script&gt;alert(1)&lt;/script&gt;'
 */
export function escapeHtml(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value).replace(ESCAPE_RE, char => ESCAPE_MAP[char]);
}

/**
 * 校验 URL 是否使用安全的协议（`http` / `https`），用于填补 `escapeHtml` 挡不住
 * 伪协议的空档。
 *
 * **背景**：`href="javascript:alert(1)"` 即使引号被转义，点击仍会执行。
 * 因此凡是把动态值放进 `href` / `src` 的位置，**必须**同时调用本函数。
 *
 * 判定方式采用「**白名单**」而非「黑名单」：黑名单永远列不全（`data:`、`vbscript:`、
 * 大小写变形、前导空白等），白名单只放行已知安全的协议。
 *
 * @param url 待校验的 URL
 * @returns 协议为 `http` / `https`（或站内相对路径）时返回 `true`
 *
 * @example
 * isSafeHttpUrl("https://example.com")   // => true
 * isSafeHttpUrl("/about")                // => true（站内相对路径）
 * isSafeHttpUrl("javascript:alert(1)")   // => false
 */
export function isSafeHttpUrl(url: unknown): boolean {
  if (typeof url !== "string") return false;
  // 站内相对路径：以单个 "/" 开头（排除协议相对路径 "//evil.com"）
  const trimmed = url.trim();
  if (trimmed.startsWith("/") && !trimmed.startsWith("//")) return true;
  return /^https?:\/\//i.test(trimmed);
}

/**
 * 把动态值安全地放进 HTML 属性或文本节点：先转义，再按需校验为安全 URL。
 *
 * @param value 待处理的值
 * @param options.isUrl 为 `true` 时额外做协议白名单校验，不安全则返回空串
 * @returns 可直接拼进 HTML 字符串的值
 *
 * @example
 * // 文本节点
 * `<p>${escapeForHtml(res.data.version)}</p>`
 * // 属性上下文（href / src）
 * `<a href="${escapeForHtml(res.data.release_url, { isUrl: true })}">`
 */
export function escapeForHtml(
  value: unknown,
  options: { isUrl?: boolean } = {}
): string {
  if (options.isUrl && !isSafeHttpUrl(value)) return "";
  return escapeHtml(value);
}
