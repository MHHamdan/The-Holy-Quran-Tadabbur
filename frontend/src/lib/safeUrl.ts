/**
 * Accept only http(s) URLs for links built from data we do not control
 * (third-party APIs, generated files). Anything else — javascript:, data:,
 * vbscript:, relative or malformed values — returns null, and the caller
 * drops the link.
 */
export function safeHttpUrl(u: unknown): string | null {
  if (typeof u !== 'string' || !u.trim()) return null;
  try {
    const parsed = new URL(u.trim());
    return parsed.protocol === 'https:' || parsed.protocol === 'http:' ? parsed.href : null;
  } catch {
    return null;
  }
}
