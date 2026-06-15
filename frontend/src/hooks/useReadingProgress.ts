/**
 * useReadingProgress — tracks khatmah progress, last-read surah, and daily streaks.
 *
 * Competitors like Quranly, Ayat, and Muslim Pro all offer reading
 * progress / khatmah tracking as a core engagement loop.
 * This hook provides an equivalent purely from localStorage so no
 * backend auth is required.
 *
 * Storage key: tadabbur_reading_v2
 * Schema: { visited: number[], lastRead: {...} | null, streak: number, longestStreak: number, lastReadDate: string | null }
 */
import { useState, useCallback } from 'react';

const KEY = 'tadabbur_reading_v2';

export interface LastRead {
  surah: number;
  nameAr: string;
  nameEn: string;
  ts: number;
}

export interface ReadingProgress {
  visited: Set<number>;
  lastRead: LastRead | null;
  streak: number;
  longestStreak: number;
  lastReadDate: string | null;
}

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function yesterdayStr(): string {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

function load(): ReadingProgress {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) {
      // Migrate from v1 if present
      const old = localStorage.getItem('tadabbur_reading_v1');
      if (old) {
        const parsed = JSON.parse(old) as { visited: number[]; lastRead: LastRead | null };
        return { visited: new Set(parsed.visited ?? []), lastRead: parsed.lastRead ?? null, streak: 0, longestStreak: 0, lastReadDate: null };
      }
      return { visited: new Set(), lastRead: null, streak: 0, longestStreak: 0, lastReadDate: null };
    }
    const parsed = JSON.parse(raw) as {
      visited: number[];
      lastRead: LastRead | null;
      streak: number;
      longestStreak: number;
      lastReadDate: string | null;
    };
    return {
      visited: new Set(parsed.visited ?? []),
      lastRead: parsed.lastRead ?? null,
      streak: parsed.streak ?? 0,
      longestStreak: parsed.longestStreak ?? 0,
      lastReadDate: parsed.lastReadDate ?? null,
    };
  } catch {
    return { visited: new Set(), lastRead: null, streak: 0, longestStreak: 0, lastReadDate: null };
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

export function useReadingProgress() {
  const [progress, setProgress] = useState<ReadingProgress>(load);

  const markVisited = useCallback((surah: number, nameAr: string, nameEn: string) => {
    setProgress(prev => {
      const { streak, longestStreak } = computeStreak(prev.streak, prev.longestStreak, prev.lastReadDate);
      const next: ReadingProgress = {
        visited: new Set([...prev.visited, surah]),
        lastRead: { surah, nameAr, nameEn, ts: Date.now() },
        streak,
        longestStreak,
        lastReadDate: todayStr(),
      };
      save(next);
      return next;
    });
  }, []);

  const resetProgress = useCallback(() => {
    const empty: ReadingProgress = { visited: new Set(), lastRead: null, streak: 0, longestStreak: 0, lastReadDate: null };
    save(empty);
    setProgress(empty);
  }, []);

  return { progress, markVisited, resetProgress };
}

/** Singleton helpers for use outside React (e.g., QuranPage effect) */
export function recordSurahVisit(surah: number, nameAr: string, nameEn: string): void {
  try {
    const current = load();
    const { streak, longestStreak } = computeStreak(current.streak, current.longestStreak, current.lastReadDate);
    const next: ReadingProgress = {
      visited: new Set([...current.visited, surah]),
      lastRead: { surah, nameAr, nameEn, ts: Date.now() },
      streak,
      longestStreak,
      lastReadDate: todayStr(),
    };
    save(next);
  } catch {
    // ignore
  }
}

export function getReadingProgress(): ReadingProgress {
  return load();
}
