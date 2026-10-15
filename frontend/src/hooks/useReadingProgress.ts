/**
 * useReadingProgress — tracks khatmah progress, last-read surah, and daily streaks.
 *
 * Purely localStorage, so no backend auth is required.
 *
 * A surah counts as read (khatmah progress) only when its last ayah was
 * reached in the reader or the reader tapped "Mark as read"; opening it only
 * marks it as started.
 *
 * Storage key: tadabbur_reading_v3
 * Schema: {
 *   visited: number[]      surahs read to the end (khatmah progress; the field
 *                          keeps this name because every progress view reads it)
 *   started: number[]      surahs opened but not finished
 *   maxAya: {[surah]: n}   furthest ayah reached per surah
 *   lastRead, streak, longestStreak, lastReadDate
 * }
 * v2 stored every opened surah in `visited`; those migrate to `started`.
 */
import { useState, useCallback } from 'react';
import { SURAH_VERSE_COUNTS } from '../data/surahVerseCounts';

const KEY = 'tadabbur_reading_v3';
const LEGACY_KEYS = ['tadabbur_reading_v2', 'tadabbur_reading_v1'];

export interface LastRead {
  surah: number;
  nameAr: string;
  nameEn: string;
  ts: number;
  /** Last verse reached in that surah, when known. */
  aya?: number;
  /** Last Mushaf page open in the page reader, when known. */
  page?: number;
}

export interface ReadingProgress {
  /** Surahs read to the end (khatmah progress). */
  visited: Set<number>;
  /** Surahs opened but not finished. */
  started: Set<number>;
  /** Furthest ayah reached, per surah. */
  maxAya: Record<number, number>;
  lastRead: LastRead | null;
  streak: number;
  longestStreak: number;
  lastReadDate: string | null;
}

const empty = (): ReadingProgress => ({
  visited: new Set(), started: new Set(), maxAya: {}, lastRead: null, streak: 0, longestStreak: 0, lastReadDate: null,
});

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function yesterdayStr(): string {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

const lastAyaOf = (surah: number): number => SURAH_VERSE_COUNTS[surah - 1] ?? Number.POSITIVE_INFINITY;

function load(): ReadingProgress {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as {
        visited?: number[]; started?: number[]; maxAya?: Record<number, number>;
        lastRead?: LastRead | null; streak?: number; longestStreak?: number; lastReadDate?: string | null;
      };
      return {
        visited: new Set(parsed.visited ?? []),
        started: new Set(parsed.started ?? []),
        maxAya: parsed.maxAya ?? {},
        lastRead: parsed.lastRead ?? null,
        streak: parsed.streak ?? 0,
        longestStreak: parsed.longestStreak ?? 0,
        lastReadDate: parsed.lastReadDate ?? null,
      };
    }
    // Migrate: older versions counted every opened surah as read.
    for (const legacyKey of LEGACY_KEYS) {
      const old = localStorage.getItem(legacyKey);
      if (!old) continue;
      const parsed = JSON.parse(old) as {
        visited?: number[]; lastRead?: LastRead | null; streak?: number; longestStreak?: number; lastReadDate?: string | null;
      };
      const migrated: ReadingProgress = {
        ...empty(),
        started: new Set(parsed.visited ?? []),
        lastRead: parsed.lastRead ?? null,
        streak: parsed.streak ?? 0,
        longestStreak: parsed.longestStreak ?? 0,
        lastReadDate: parsed.lastReadDate ?? null,
      };
      save(migrated);
      for (const k of LEGACY_KEYS) localStorage.removeItem(k);
      return migrated;
    }
    return empty();
  } catch {
    return empty();
  }
}

function computeStreak(current: number, longestStreak: number, lastReadDate: string | null): { streak: number; longestStreak: number } {
  const today = todayStr();
  const yesterday = yesterdayStr();
  let streak = current;
  if (lastReadDate === today) {
    // Already read today, no change
  } else if (lastReadDate === yesterday) {
    streak = current + 1;
  } else {
    streak = 1;
  }
  return { streak, longestStreak: Math.max(streak, longestStreak) };
}

function save(p: ReadingProgress): void {
  try {
    localStorage.setItem(
      KEY,
      JSON.stringify({
        visited: Array.from(p.visited),
        started: Array.from(p.started),
        maxAya: p.maxAya,
        lastRead: p.lastRead,
        streak: p.streak,
        longestStreak: p.longestStreak,
        lastReadDate: p.lastReadDate,
      })
    );
  } catch {
    // ignore full storage
  }
}

/** Apply a reading event: opening (aya undefined), reaching an ayah, or marking read. */
function advance(
  current: ReadingProgress,
  ev: { surah: number; nameAr: string; nameEn: string; aya?: number; page?: number; markRead?: boolean },
): ReadingProgress {
  const { streak, longestStreak } = computeStreak(current.streak, current.longestStreak, current.lastReadDate);
  const maxAya = { ...current.maxAya };
  if (ev.aya) maxAya[ev.surah] = Math.max(maxAya[ev.surah] ?? 0, ev.aya);
  const finished = ev.markRead || (maxAya[ev.surah] ?? 0) >= lastAyaOf(ev.surah);
  const visited = new Set(current.visited);
  const started = new Set(current.started);
  if (finished) {
    visited.add(ev.surah);
    started.delete(ev.surah);
  } else if (!visited.has(ev.surah)) {
    started.add(ev.surah);
  }
  return {
    visited,
    started,
    maxAya,
    lastRead: {
      surah: ev.surah,
      nameAr: ev.nameAr,
      nameEn: ev.nameEn,
      ts: Date.now(),
      aya: ev.aya ?? (current.lastRead?.surah === ev.surah ? current.lastRead.aya : undefined),
      page: ev.page ?? current.lastRead?.page,
    },
    streak,
    longestStreak,
    lastReadDate: todayStr(),
  };
}

export function useReadingProgress() {
  const [progress, setProgress] = useState<ReadingProgress>(load);

  /** Opening a surah: it becomes "started" (not read). */
  const markVisited = useCallback((surah: number, nameAr: string, nameEn: string) => {
    setProgress(prev => {
      const next = advance(prev, { surah, nameAr, nameEn });
      save(next);
      return next;
    });
  }, []);

  const markRead = useCallback((surah: number, nameAr: string, nameEn: string) => {
    setProgress(prev => {
      const next = advance(prev, { surah, nameAr, nameEn, markRead: true });
      save(next);
      return next;
    });
  }, []);

  const resetProgress = useCallback(() => {
    const next = empty();
    save(next);
    setProgress(next);
  }, []);

  return { progress, markVisited, markRead, resetProgress };
}

/** Singleton helpers for use outside React (e.g., QuranPage effect) */
export function recordSurahVisit(surah: number, nameAr: string, nameEn: string): void {
  try {
    save(advance(load(), { surah, nameAr, nameEn }));
  } catch {
    // ignore
  }
}

/** The reader tapped "Mark as read" at the end of a surah. */
export function markSurahRead(surah: number, nameAr: string, nameEn: string): void {
  try {
    save(advance(load(), { surah, nameAr, nameEn, markRead: true }));
  } catch {
    // storage unavailable: progress is best-effort
  }
}

/**
 * Remember the exact place reached: the verse (Quran reader) and/or the page
 * (Mushaf reader). Counts as reading for the streak; reaching the last ayah
 * completes the surah.
 */
export function recordReadingPosition(pos: {
  surah: number;
  aya: number;
  nameAr: string;
  nameEn: string;
  page?: number;
}): void {
  try {
    save(advance(load(), pos));
  } catch {
    // storage unavailable: progress is best-effort
  }
}

export function getReadingProgress(): ReadingProgress {
  return load();
}

/** Where "continue reading" should open: the last verse read, else Al-Fatiha. */
export function continueReadingPath(): string {
  const last = load().lastRead;
  if (!last) return '/quran/1';
  return last.aya && last.aya > 1 ? `/quran/${last.surah}?aya=${last.aya}` : `/quran/${last.surah}`;
}
