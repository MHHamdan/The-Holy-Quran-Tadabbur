/**
 * Calendar dates in the reader's own time zone.
 *
 * `new Date().toISOString().slice(0, 10)` is the UTC date: for a reader in
 * UTC+3 the "day" rolled over at 03:00, so morning dhikr counts and the daily
 * challenge reset in the middle of the night. Use these helpers instead.
 */

const pad = (n: number) => String(n).padStart(2, '0');

/** YYYY-MM-DD of `d` in local time. */
export function localDateStr(d: Date = new Date()): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** YYYY-MM-DD of the local day before `d`. */
export function localYesterdayStr(d: Date = new Date()): string {
  const y = new Date(d.getFullYear(), d.getMonth(), d.getDate() - 1);
  return localDateStr(y);
}
