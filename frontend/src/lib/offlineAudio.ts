/**
 * Offline recitation: download a surah's verse files once, play them without
 * a connection.
 *
 * Storage: the device filesystem in the Android/iOS apps (Capacitor
 * Filesystem, app data directory), Cache Storage in browsers. The files come
 * from the primary verse CDN (everyayah.com, CORS-enabled); nothing is
 * re-hosted. Which surahs are saved is recorded in localStorage so the player
 * can check synchronously.
 */
import { Capacitor } from '@capacitor/core';
import { isNativeApp } from './native';

const INDEX_KEY = 'tadabbur_offline_audio_v1';
const CACHE_NAME = 'tadabbur-audio-v1';
const CONCURRENCY = 4;

export interface SavedSurah {
  verses: number;
  bytes: number;
  savedAt: number;
}

type Index = Record<string, SavedSurah>;

const key = (reciter: string, sura: number) => `${reciter}:${sura}`;

function loadIndex(): Index {
  try {
    return JSON.parse(localStorage.getItem(INDEX_KEY) ?? '{}') as Index;
  } catch {
    return {};
  }
}

function saveIndex(index: Index) {
  try { localStorage.setItem(INDEX_KEY, JSON.stringify(index)); } catch { /* storage unavailable */ }
}

export const offlineAudioSupported = isNativeApp || (typeof window !== 'undefined' && 'caches' in window);

export function savedSurah(reciter: string, sura: number): SavedSurah | null {
  return loadIndex()[key(reciter, sura)] ?? null;
}

/** Filesystem path for a verse file, e.g. audio/mishary_afasy/002255.mp3 */
function nativePath(reciter: string, url: string): string {
  const file = url.split('/').pop() ?? 'verse.mp3';
  return `audio/${reciter}/${file}`;
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
  if (isNativeApp) {
    const blob = await response.blob();
    const { Filesystem, Directory } = await import('@capacitor/filesystem');
    await Filesystem.writeFile({
      path: nativePath(reciter, url),
      data: await blobToBase64(blob),
      directory: Directory.Data,
      recursive: true,
    });
    return blob.size;
  }
  const blob = await response.blob();
  const cache = await caches.open(CACHE_NAME);
  await cache.put(url, new Response(blob, { headers: { 'Content-Type': blob.type || 'audio/mpeg' } }));
  return blob.size;
}

/**
 * Download every verse of a surah. Resolves when done; rejects on the first
 * failure (already-saved files stay, and the surah is not marked saved).
 */
export async function saveSurah(
  reciter: string,
  sura: number,
  urls: string[],
  onProgress: (done: number, total: number) => void,
  signal: AbortSignal,
): Promise<SavedSurah> {
  let done = 0;
  let bytes = 0;
  const queue = [...urls];
  const worker = async () => {
    for (let url = queue.shift(); url; url = queue.shift()) {
      if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
      // Await first: `bytes += await ...` would read bytes before the await and
      // concurrent workers would overwrite each other's totals.
      const size = await storeOne(reciter, url, signal);
      bytes += size;
      done += 1;
      onProgress(done, urls.length);
    }
  };
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, urls.length) }, worker));
  const entry: SavedSurah = { verses: urls.length, bytes, savedAt: Date.now() };
  const index = loadIndex();
  index[key(reciter, sura)] = entry;
  saveIndex(index);
  return entry;
}

export async function removeSurah(reciter: string, sura: number, urls: string[]): Promise<void> {
  if (isNativeApp) {
    const { Filesystem, Directory } = await import('@capacitor/filesystem');
    await Promise.all(urls.map((url) =>
      Filesystem.deleteFile({ path: nativePath(reciter, url), directory: Directory.Data }).catch(() => undefined),
    ));
  } else {
    const cache = await caches.open(CACHE_NAME);
    await Promise.all(urls.map((url) => cache.delete(url)));
  }
  const index = loadIndex();
  delete index[key(reciter, sura)];
  saveIndex(index);
}

/**
 * The URL to give <audio>: the saved copy when this verse was downloaded,
 * otherwise the network URL. Callers revoke blob: URLs they no longer need.
 */
export async function playableUrl(reciter: string, sura: number, url: string): Promise<string> {
  if (!savedSurah(reciter, sura)) return url;
  try {
    if (isNativeApp) {
      const { Filesystem, Directory } = await import('@capacitor/filesystem');
      const { uri } = await Filesystem.getUri({ path: nativePath(reciter, url), directory: Directory.Data });
      return Capacitor.convertFileSrc(uri);
    }
    const cached = await (await caches.open(CACHE_NAME)).match(url);
    return cached ? URL.createObjectURL(await cached.blob()) : url;
  } catch {
    return url;
  }
}
