/**
 * Qur'an verse references: parse, format and link — never text.
 *
 * Pages that used to hand-type a verse now hold only a reference
 * ({ sura, ayaStart, ayaEnd?, wordStart?, wordEnd? }); the text itself is
 * shown by the reader (/quran/:sura?aya=) or by a generated excerpt keyed
 * with excerptKey() ('s:a[-b][#w1-w2]', the key format of
 * src/data/generated/quranExcerpts.json built from the canonical Tanzil file).
 */

export interface AyahRef {
  sura: number;
  ayaStart: number;
  ayaEnd?: number;
  wordStart?: number;
  wordEnd?: number;
}

/** Verse counts per surah (Hafs, 6236 in total). */
const AYAH_COUNTS = [
  7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
  112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
  54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
  14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
  29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
  11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
];

export function ayahCount(sura: number): number {
  return AYAH_COUNTS[sura - 1] ?? 0;
}

/** True when the reference points at verses that exist. */
export function isValidAyahRef(ref: AyahRef): boolean {
  const n = ayahCount(ref.sura);
  if (!Number.isInteger(ref.sura) || n === 0) return false;
  if (!Number.isInteger(ref.ayaStart) || ref.ayaStart < 1 || ref.ayaStart > n) return false;
  if (ref.ayaEnd !== undefined && (!Number.isInteger(ref.ayaEnd) || ref.ayaEnd < ref.ayaStart || ref.ayaEnd > n)) return false;
  if ((ref.wordStart === undefined) !== (ref.wordEnd === undefined)) return false;
  if (ref.wordStart !== undefined && ref.wordEnd !== undefined) {
    if (ref.wordStart < 1 || ref.wordEnd < ref.wordStart) return false;
  }
  return true;
}

/**
 * Parse '9:60', '2:255-257', '2:255#1-4', '9:60-60'. Returns null for
 * anything malformed or out of range.
 */
export function parseAyahRef(input: string): AyahRef | null {
  const m = /^\s*(\d{1,3})\s*:\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?(?:#(\d{1,3})-(\d{1,3}))?\s*$/.exec(input);
  if (!m) return null;
  const ref: AyahRef = { sura: Number(m[1]), ayaStart: Number(m[2]) };
  if (m[3] !== undefined && Number(m[3]) !== ref.ayaStart) ref.ayaEnd = Number(m[3]);
  if (m[4] !== undefined) {
    ref.wordStart = Number(m[4]);
    ref.wordEnd = Number(m[5]);
  }
  return isValidAyahRef(ref) ? ref : null;
}

/** Key into the generated excerpt file: 's:a[-b][#w1-w2]'. */
export function excerptKey(ref: AyahRef): string {
  let key = `${ref.sura}:${ref.ayaStart}`;
  if (ref.ayaEnd !== undefined && ref.ayaEnd !== ref.ayaStart) key += `-${ref.ayaEnd}`;
  if (ref.wordStart !== undefined && ref.wordEnd !== undefined) key += `#${ref.wordStart}-${ref.wordEnd}`;
  return key;
}

/** '9:60' or '2:255–257' with Western digits; render it inside <bdi dir="ltr">. */
export function formatAyahRef(ref: AyahRef): string {
  const tail = ref.ayaEnd !== undefined && ref.ayaEnd !== ref.ayaStart ? `–${ref.ayaEnd}` : '';
  return `${ref.sura}:${ref.ayaStart}${tail}`;
}

/** Reader link that opens the surah scrolled to (and highlighting) the first verse. */
export function ayahHref(ref: AyahRef): string {
  return `/quran/${ref.sura}?aya=${ref.ayaStart}`;
}
