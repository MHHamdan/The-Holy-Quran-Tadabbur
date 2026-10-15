import { describe, expect, it } from 'vitest';
import {
  ayahCount,
  ayahHref,
  excerptKey,
  formatAyahRef,
  isValidAyahRef,
  parseAyahRef,
} from '../utils/ayahRef';

describe('ayah counts', () => {
  it('cover 114 surahs and 6236 verses (Hafs)', () => {
    let total = 0;
    for (let s = 1; s <= 114; s++) {
      expect(ayahCount(s)).toBeGreaterThan(0);
      total += ayahCount(s);
    }
    expect(total).toBe(6236);
    expect(ayahCount(0)).toBe(0);
    expect(ayahCount(115)).toBe(0);
  });

  it('match well-known surah lengths', () => {
    expect(ayahCount(1)).toBe(7);
    expect(ayahCount(2)).toBe(286);
    expect(ayahCount(9)).toBe(129);
    expect(ayahCount(114)).toBe(6);
  });
});

describe('parseAyahRef', () => {
  it('parses single verses, ranges and word spans', () => {
    expect(parseAyahRef('9:60')).toEqual({ sura: 9, ayaStart: 60 });
    expect(parseAyahRef('2:255-257')).toEqual({ sura: 2, ayaStart: 255, ayaEnd: 257 });
    expect(parseAyahRef('2:255#1-4')).toEqual({ sura: 2, ayaStart: 255, wordStart: 1, wordEnd: 4 });
    expect(parseAyahRef('9:60-60')).toEqual({ sura: 9, ayaStart: 60 });
  });

  it('rejects malformed or out-of-range references', () => {
    expect(parseAyahRef('')).toBeNull();
    expect(parseAyahRef('9')).toBeNull();
    expect(parseAyahRef('115:1')).toBeNull();
    expect(parseAyahRef('1:8')).toBeNull();
    expect(parseAyahRef('2:10-5')).toBeNull();
    expect(parseAyahRef('2:0')).toBeNull();
    expect(parseAyahRef('2:1#4-1')).toBeNull();
  });
});

describe('formatting and links', () => {
  it('builds excerpt keys in the generator format', () => {
    expect(excerptKey({ sura: 9, ayaStart: 60 })).toBe('9:60');
    expect(excerptKey({ sura: 2, ayaStart: 255, ayaEnd: 257 })).toBe('2:255-257');
    expect(excerptKey({ sura: 2, ayaStart: 255, wordStart: 1, wordEnd: 4 })).toBe('2:255#1-4');
  });

  it('formats references and reader links', () => {
    expect(formatAyahRef({ sura: 9, ayaStart: 60 })).toBe('9:60');
    expect(formatAyahRef({ sura: 2, ayaStart: 255, ayaEnd: 257 })).toBe('2:255–257');
    expect(ayahHref({ sura: 9, ayaStart: 60 })).toBe('/quran/9?aya=60');
  });

  it('validates word spans need both ends', () => {
    expect(isValidAyahRef({ sura: 1, ayaStart: 1, wordStart: 1 })).toBe(false);
    expect(isValidAyahRef({ sura: 1, ayaStart: 1, wordStart: 1, wordEnd: 2 })).toBe(true);
  });
});
