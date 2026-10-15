/**
 * The Qur'an text bundled for offline reading (public/offline-quran/) must be
 * byte-for-byte the canonical Tanzil text in data/raw/quran_tanzil.json, for
 * all 6,236 ayat, and the loader must hand it to the readers unchanged.
 */
import { createHash } from 'crypto';
import { existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';
import { loadOfflinePage, loadOfflineSurah, OFFLINE_QURAN_FORMAT, type OfflineSurahFile } from './offlineQuran';

const ROOT = resolve(__dirname, '../../..');
const TANZIL = join(ROOT, 'data/raw/quran_tanzil.json');
const OUT = join(ROOT, 'frontend/public/offline-quran');

interface TanzilVerse {
  id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  aya_text: string;
  aya_text_emlaey: string;
  bismillah: string | null;
  bismillah_emlaey: string | null;
  page: number;
  jozz: number;
}

const tanzilRaw = readFileSync(TANZIL, 'utf-8');
const tanzil = JSON.parse(tanzilRaw) as { copyright: Record<string, string>; verses: TanzilVerse[] };
const readOut = (name: string) => readFileSync(join(OUT, name), 'utf-8');
const sha256 = (s: string) => createHash('sha256').update(s).digest('hex');

describe('bundled offline Qur\'an text', () => {
  const files = new Map<number, OfflineSurahFile>();
  for (let s = 1; s <= 114; s++) files.set(s, JSON.parse(readOut(`${s}.json`)) as OfflineSurahFile);
  const manifest = JSON.parse(readOut('manifest.json'));

  it('has 114 surah files and 6236 ayat', () => {
    expect(existsSync(join(OUT, '115.json'))).toBe(false);
    const total = [...files.values()].reduce((n, f) => n + f.verses.length, 0);
    expect(total).toBe(6236);
    expect(manifest.verse_count).toBe(6236);
  });

  it('equals quran_tanzil.json byte for byte, verse by verse', () => {
    const bundled = [...files.values()].flatMap((f) => f.verses.map((v) => ({ f, v })));
    expect(bundled).toHaveLength(tanzil.verses.length);
    const mismatches: string[] = [];
    tanzil.verses.forEach((t, i) => {
      const { f, v } = bundled[i];
      const pairs: [unknown, unknown, string][] = [
        [f.sura_no, t.sura_no, 'sura_no'],
        [v.aya_no, t.aya_no, 'aya_no'],
        [v.id, t.id, 'id'],
        [v.text_uthmani, t.aya_text, 'text_uthmani'],
        [v.text_imlaei, t.aya_text_emlaey, 'text_imlaei'],
        [v.bismillah_uthmani, t.bismillah, 'bismillah_uthmani'],
        [v.bismillah_imlaei, t.bismillah_emlaey, 'bismillah_imlaei'],
        [v.page_no, t.page, 'page_no'],
        [v.juz_no, t.jozz, 'juz_no'],
        [f.sura_name_ar, t.sura_name_ar, 'sura_name_ar'],
        [f.sura_name_en, t.sura_name_en, 'sura_name_en'],
      ];
      for (const [a, b, field] of pairs) if (a !== b) mismatches.push(`${t.sura_no}:${t.aya_no} ${field}`);
      // Same UTF-8 bytes, not just equal after some normalisation.
      if (Buffer.compare(Buffer.from(v.text_uthmani, 'utf-8'), Buffer.from(t.aya_text, 'utf-8')) !== 0) {
        mismatches.push(`${t.sura_no}:${t.aya_no} bytes`);
      }
    });
    expect(mismatches.slice(0, 10)).toEqual([]);
  });

  it('carries the Tanzil copyright block in every file', () => {
    for (const f of files.values()) {
      expect(f.format).toBe(OFFLINE_QURAN_FORMAT);
      expect(f.copyright.uthmani).toBe(tanzil.copyright.uthmani);
      expect(f.copyright.simple).toBe(tanzil.copyright.simple);
      expect(f.copyright.simple).toContain('CHANGING IT IS NOT ALLOWED');
    }
    expect(manifest.copyright.attribution).toBe(tanzil.copyright.attribution);
  });

  it('manifest checksums match the source and every file', () => {
    expect(manifest.source_sha256).toBe(sha256(tanzilRaw));
    expect(Object.keys(manifest.files)).toHaveLength(114);
    for (const [name, digest] of Object.entries(manifest.files)) expect(sha256(readOut(name))).toBe(digest);
  });

  it('page index covers the 604 Madinah Mushaf pages', () => {
    expect(Object.keys(manifest.pages)).toHaveLength(604);
    expect(manifest.pages['1']).toEqual([[1, 1], [1, 7]]);
    expect(manifest.pages['604'][1]).toEqual([114, 6]);
  });
});

describe('offlineQuran loader', () => {
  beforeAll(() => {
    vi.stubGlobal('fetch', async (url: string) => {
      const name = String(url).split('/offline-quran/')[1];
      const path = join(OUT, name);
      if (!existsSync(path)) return new Response('missing', { status: 404 });
      return new Response(readFileSync(path, 'utf-8'), { status: 200 });
    });
  });
  afterAll(() => vi.unstubAllGlobals());

  it('loads a surah unchanged in the API Verse shape', async () => {
    const verses = await loadOfflineSurah(2);
    expect(verses).toHaveLength(286);
    const t = tanzil.verses.filter((v) => v.sura_no === 2);
    verses.forEach((v, i) => {
      expect(v.text_uthmani).toBe(t[i].aya_text);
      expect(v.text_imlaei).toBe(t[i].aya_text_emlaey);
      expect(v.sura_no).toBe(2);
      expect(v.translations).toEqual([]);
    });
    expect(verses[0].bismillah_uthmani).toBe(t[0].bismillah);
  });

  it('loads a Mushaf page that spans several surahs', async () => {
    const page = await loadOfflinePage(604);
    const expected = tanzil.verses.filter((v) => v.page === 604);
    expect(page.map((v) => `${v.sura_no}:${v.aya_no}`)).toEqual(expected.map((v) => `${v.sura_no}:${v.aya_no}`));
    expect(new Set(page.map((v) => v.sura_no)).size).toBeGreaterThan(1);
  });

  it('rejects out-of-range requests', async () => {
    await expect(loadOfflineSurah(115)).rejects.toThrow();
    await expect(loadOfflinePage(0)).rejects.toThrow();
  });
});
