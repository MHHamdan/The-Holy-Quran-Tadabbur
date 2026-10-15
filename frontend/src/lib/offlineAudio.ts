/**
 * Offline recitation: download a surah's verse files once, play them without
 * a connection.
 *
 * Storage: the device filesystem in the Android/iOS apps (Capacitor
 * Filesystem), Cache Storage in browsers. The files come from the primary
 * verse CDN (everyayah.com, CORS-enabled); nothing is re-hosted.
 *
 * The index (localStorage) records, per reciter and surah, every verse's ayah
 * number and URL, so the player can build its playlist and the files can be
 * removed with no network call at all.
 */
import { Capacitor } from '@capacitor/core';
import { isNativeApp } from './native';

const INDEX_KEY = 'tadabbur_offline_audio_v2';
const LEGACY_INDEX_KEY = 'tadabbur_offline_audio_v1';
const CACHE_NAME = 'tadabbur-audio-v1';
const AUDIO_DIR = 'audio';
const CONCURRENCY = 4;

export interface SavedSurah {
  verses: number;
  bytes: number;
  savedAt: number;
  /** Ayah numbers, in playback order (empty for entries saved before v2). */
  ayahs: number[];
  /** Verse file URLs, parallel to ayahs (empty for entries saved before v2). */
  urls: string[];
}

export interface SavedSurahRow extends SavedSurah {
  reciter: string;
  sura: number;
}

export interface OfflineVerse {
  aya_no: number;
  url: string;
}

type Index = Record<string, SavedSurah>;

const key = (reciter: string, sura: number) => `${reciter}:${sura}`;

function readJson(storageKey: string): Index | null {
  try {
    const raw = localStorage.getItem(storageKey);
    return raw ? (JSON.parse(raw) as Index) : null;
  } catch {
    return null;
  }
}

function saveIndex(index: Index) {
  try { localStorage.setItem(INDEX_KEY, JSON.stringify(index)); } catch { /* storage unavailable */ }
}

/**
 * v1 entries had no URLs. They are carried over with empty `ayahs`/`urls`;
 * the player fills them in the next time the surah is opened online
 * (recordSurahVerses), after which they work fully offline.
 */
function loadIndex(): Index {
  const index = readJson(INDEX_KEY);
  if (index) return index;
  const legacy = readJson(LEGACY_INDEX_KEY);
  if (!legacy) return {};
  const migrated: Index = {};
  for (const [k, v] of Object.entries(legacy)) {
    migrated[k] = { verses: v.verses ?? 0, bytes: v.bytes ?? 0, savedAt: v.savedAt ?? Date.now(), ayahs: [], urls: [] };
  }
  saveIndex(migrated);
  try { localStorage.removeItem(LEGACY_INDEX_KEY); } catch { /* storage unavailable */ }
  return migrated;
}

export const offlineAudioSupported = isNativeApp || (typeof window !== 'undefined' && 'caches' in window);

export function savedSurah(reciter: string, sura: number): SavedSurah | null {
  return loadIndex()[key(reciter, sura)] ?? null;
}

/** True when the entry carries its own playlist (saved with v2). */
export function hasPlaylist(entry: SavedSurah | null | undefined): boolean {
  return !!entry && entry.urls.length > 0 && entry.urls.length === entry.ayahs.length;
}

/** Every saved surah, newest first. */
export function listSaved(): SavedSurahRow[] {
  return Object.entries(loadIndex())
    .map(([k, v]) => {
      const sep = k.lastIndexOf(':');
      return { ...v, reciter: k.slice(0, sep), sura: Number(k.slice(sep + 1)) };
    })
    .filter((row) => Number.isFinite(row.sura))
    .sort((a, b) => b.savedAt - a.savedAt);
}

/** Fill in the playlist of a pre-v2 entry (called by the player when online). */
export function recordSurahVerses(reciter: string, sura: number, verses: OfflineVerse[]) {
  const index = loadIndex();
  const entry = index[key(reciter, sura)];
  if (!entry || hasPlaylist(entry) || verses.length === 0) return;
  index[key(reciter, sura)] = { ...entry, ayahs: verses.map((v) => v.aya_no), urls: verses.map((v) => v.url) };
  saveIndex(index);
}

/**
 * Filesystem path for a verse file, e.g. audio/mishary_afasy/002255.mp3.
 * Directory.LibraryNoCloud: iOS Library/NoCloud (re-downloadable media must
 * not go into the iCloud backup); Android: the app files dir (same as Data).
 */
function nativePath(reciter: string, url: string): string {
  const file = url.split('/').pop() ?? 'verse.mp3';
  return `${AUDIO_DIR}/${reciter}/${file}`;
}

async function nativeFs() {
  const { Filesystem, Directory } = await import('@capacitor/filesystem');
  return { Filesystem, directory: Directory.LibraryNoCloud };
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

async function storeOne(reciter: string, url: string, signal: AbortSignal): Promise<number> {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const blob = await response.blob();
  if (isNativeApp) {
    const { Filesystem, directory } = await nativeFs();
    await Filesystem.writeFile({
      path: nativePath(reciter, url),
      data: await blobToBase64(blob),
      directory,
      recursive: true,
    });
    return blob.size;
  }
  const cache = await caches.open(CACHE_NAME);
  await cache.put(url, new Response(blob, { headers: { 'Content-Type': blob.type || 'audio/mpeg' } }));
  return blob.size;
}

async function deleteFiles(reciter: string, urls: string[]): Promise<void> {
  if (urls.length === 0) return;
  if (isNativeApp) {
    const { Filesystem, directory } = await nativeFs();
    await Promise.all(urls.map((url) =>
      Filesystem.deleteFile({ path: nativePath(reciter, url), directory }).catch(() => undefined),
    ));
    return;
  }
  const cache = await caches.open(CACHE_NAME);
  await Promise.all(urls.map((url) => cache.delete(url)));
}

/**
 * Download every verse of a surah. Resolves when done. On failure or abort
 * the files already written are deleted again and the surah is not marked
 * saved, so nothing is left orphaned.
 */
export async function saveSurah(
  reciter: string,
  sura: number,
  verses: OfflineVerse[],
  onProgress: (done: number, total: number) => void,
  signal: AbortSignal,
): Promise<SavedSurah> {
  let done = 0;
  let bytes = 0;
  const written: string[] = [];
  const queue = [...verses];
  const worker = async () => {
    for (let v = queue.shift(); v; v = queue.shift()) {
      if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
      // Await first: `bytes += await ...` would read bytes before the await and
      // concurrent workers would overwrite each other's totals.
      const size = await storeOne(reciter, v.url, signal);
      written.push(v.url);
      bytes += size;
      done += 1;
      onProgress(done, verses.length);
    }
  };
  try {
    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, verses.length) }, worker));
  } catch (err) {
    queue.length = 0; // stop the other workers
    await deleteFiles(reciter, written).catch(() => undefined);
    throw err;
  }
  const entry: SavedSurah = {
    verses: verses.length,
    bytes,
    savedAt: Date.now(),
    ayahs: verses.map((v) => v.aya_no),
    urls: verses.map((v) => v.url),
  };
  const index = loadIndex();
  index[key(reciter, sura)] = entry;
  saveIndex(index);
  return entry;
}

/** Remove a saved surah using only the index (works offline). */
export async function removeSurah(reciter: string, sura: number): Promise<void> {
  const entry = savedSurah(reciter, sura);
  try {
    if (entry) await deleteFiles(reciter, entry.urls);
  } finally {
    const index = loadIndex();
    delete index[key(reciter, sura)];
    saveIndex(index);
  }
}

/** Delete every saved recitation and the index (settings, "delete my data"). */
export async function clearAll(): Promise<void> {
  try {
    if (isNativeApp) {
      const { Filesystem, directory } = await nativeFs();
      await Filesystem.rmdir({ path: AUDIO_DIR, directory, recursive: true }).catch(() => undefined);
    } else if (typeof caches !== 'undefined') {
      await caches.delete(CACHE_NAME);
    }
  } finally {
    saveIndex({});
    try { localStorage.removeItem(LEGACY_INDEX_KEY); } catch { /* storage unavailable */ }
  }
}

/**
 * The URL to give <audio>: the saved copy when this verse was downloaded,
 * otherwise the network URL. Callers revoke blob: URLs they no longer need.
 */
export async function playableUrl(reciter: string, sura: number, url: string): Promise<string> {
  if (!savedSurah(reciter, sura)) return url;
  try {
    if (isNativeApp) {
      const { Filesystem, directory } = await nativeFs();
      const { uri } = await Filesystem.getUri({ path: nativePath(reciter, url), directory });
      return Capacitor.convertFileSrc(uri);
    }
    const cached = await (await caches.open(CACHE_NAME)).match(url);
    return cached ? URL.createObjectURL(await cached.blob()) : url;
  } catch {
    return url;
  }
}

/** True when this verse URL is part of a saved surah (skip network preloads). */
export function isSavedVerse(reciter: string, sura: number, url: string): boolean {
  const entry = savedSurah(reciter, sura);
  return !!entry && entry.urls.includes(url);
}
