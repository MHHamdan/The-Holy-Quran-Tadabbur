/**
 * Qur'an excerpts by reference.
 *
 * Content that quotes the Qur'an stores a key, never the text. The text comes
 * from frontend/src/data/generated/quranExcerpts.json, which
 * scripts/build-quran-excerpts.ts copies verbatim from the Tanzil simple text
 * (data/raw/quran_tanzil.json). Re-run that script after adding a key; the
 * integrity validator fails while the file is stale.
 *
 * Keys: 's:a', 's:a-b' (consecutive verses), 's:a#w1-w2' or 's:a#w1-'
 * (words of one verse, 1-based, inclusive).
 */
import data from '../data/generated/quranExcerpts.json';

const EXCERPTS = (data as { excerpts: Record<string, string> }).excerpts;

/** Tanzil's attribution line; show it (or QuranTextAttribution) wherever excerpts appear. */
export const QURAN_EXCERPT_ATTRIBUTION: string = (data as { quranTextAttribution: string }).quranTextAttribution;

export function quranExcerpt(key: string): string {
  const text = EXCERPTS[key];
  if (text === undefined) {
    // A missing key means the generator was not re-run; never invent text.
    if (import.meta.env?.DEV) console.warn(`quranExcerpt: unknown key ${key}; run scripts/build-quran-excerpts.ts`);
    return '';
  }
  return text;
}

/** The verse reference part of a key, e.g. '2:255' for '2:255#1-4'. */
export function excerptRef(key: string): string {
  return key.split('#')[0];
}
