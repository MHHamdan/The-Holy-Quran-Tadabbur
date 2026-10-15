/**
 * Qur'an text bundled with the app for offline reading.
 *
 * frontend/public/offline-quran/{1..114}.json are written by
 * scripts/export-offline-quran.ts, verbatim from data/raw/quran_tanzil.json
 * (the same Tanzil text the API serves). They ship inside the web build and
 * the Android/iOS packages, so a surah or Mushaf page can be read with no
 * network and no earlier visit. Only the Arabic text is bundled: translations
 * of the meanings, tafsir and audio still need the API.
 *
 * The readers use this only when the API cannot be reached. Text is passed
 * through as loaded: never edited, trimmed or re-normalised here.
 */
import type { Verse } from './api';

export interface OfflineVerse {
  id: number;
  aya_no: number;
  text_uthmani: string;
  text_imlaei: string;
  bismillah_uthmani: string | null;
  bismillah_imlaei: string | null;
  page_no: number;
  juz_no: number;
  hizb_no: number;
  rub_no: number;
  sajda_type: 'recommended' | 'obligatory' | null;
  quarter_start: boolean;
}

export interface OfflineSurahFile {
  format: string;
  copyright: { uthmani: string; simple: string; attribution: string };
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  verses: OfflineVerse[];
}

export interface OfflineManifest {
  format: string;
  source_sha256: string;
  verse_count: number;
  /** Mushaf page -> [first [sura, aya], last [sura, aya]] */
  pages: Record<string, [[number, number], [number, number]]>;
  files: Record<string, string>;
}

export const OFFLINE_QURAN_FORMAT = 'tadabbur-offline-quran/1';

const BASE = `${(import.meta.env?.BASE_URL as string | undefined) ?? '/'}offline-quran/`;

async function fetchJson<T>(name: string): Promise<T> {
  const res = await fetch(BASE + name);
  if (!res.ok) throw new Error(`offline-quran/${name}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

const surahFiles = new Map<number, Promise<OfflineSurahFile>>();
let manifestPromise: Promise<OfflineManifest> | null = null;

function surahFile(suraNo: number): Promise<OfflineSurahFile> {
  let p = surahFiles.get(suraNo);
  if (!p) {
    p = fetchJson<OfflineSurahFile>(`${suraNo}.json`).then((f) => {
      if (f.format !== OFFLINE_QURAN_FORMAT || f.sura_no !== suraNo) throw new Error(`offline-quran/${suraNo}.json: unexpected content`);
      return f;
    });
    p.catch(() => surahFiles.delete(suraNo));
    surahFiles.set(suraNo, p);
  }
  return p;
}

function manifest(): Promise<OfflineManifest> {
  if (!manifestPromise) {
    manifestPromise = fetchJson<OfflineManifest>('manifest.json');
    manifestPromise.catch(() => { manifestPromise = null; });
  }
  return manifestPromise;
}

/** Convert one bundled surah to the API's Verse shape (no translations). */
export function toVerses(file: OfflineSurahFile): Verse[] {
  return file.verses.map((v) => ({
    id: v.id,
    sura_no: file.sura_no,
    sura_name_ar: file.sura_name_ar,
    sura_name_en: file.sura_name_en,
    aya_no: v.aya_no,
    text_uthmani: v.text_uthmani,
    text_imlaei: v.text_imlaei,
    page_no: v.page_no,
    juz_no: v.juz_no,
    hizb_no: v.hizb_no,
    rub_no: v.rub_no,
    sajda_type: v.sajda_type,
    quarter_start: v.quarter_start,
    bismillah_uthmani: v.bismillah_uthmani,
    bismillah_imlaei: v.bismillah_imlaei,
    translations: [],
  }));
}

/** Every verse of a surah (1-114) from the bundled text. */
export async function loadOfflineSurah(suraNo: number): Promise<Verse[]> {
  if (!Number.isInteger(suraNo) || suraNo < 1 || suraNo > 114) throw new Error(`invalid surah ${suraNo}`);
  return toVerses(await surahFile(suraNo));
}

/** Every verse on a Madinah Mushaf page (1-604) from the bundled text. */
export async function loadOfflinePage(pageNo: number): Promise<Verse[]> {
  if (!Number.isInteger(pageNo) || pageNo < 1 || pageNo > 604) throw new Error(`invalid page ${pageNo}`);
  const range = (await manifest()).pages[String(pageNo)];
  if (!range) throw new Error(`page ${pageNo} not in offline manifest`);
  const [[firstSura], [lastSura]] = range;
  const out: Verse[] = [];
  for (let s = firstSura; s <= lastSura; s++) {
    for (const v of toVerses(await surahFile(s))) if (v.page_no === pageNo) out.push(v);
  }
  return out;
}

/** React Query key for bundled text (deliberately not under 'quran': never persisted). */
export const offlineQuranKey = (kind: 'sura' | 'page', n: number) => ['offline-quran', kind, n] as const;
