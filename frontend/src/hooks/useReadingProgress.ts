/**
 * useReadingProgress — tracks khatmah progress and last-read surah.
 *
 * Competitors like Quranly, Ayat, and Muslim Pro all offer reading
 * progress / khatmah tracking as a core engagement loop.
 * This hook provides an equivalent purely from localStorage so no
 * backend auth is required.
 *
 * Storage key: tadabbur_reading_v1
 * Schema: { visited: number[], lastRead: { surah, nameAr, nameEn, ts } | null }
 */
import { useState, useCallback } from 'react';

const KEY = 'tadabbur_reading_v1';

export interface LastRead {
  surah: number;
  nameAr: string;
  nameEn: string;
  ts: number;
}

export interface ReadingProgress {
  visited: Set<number>;
  lastRead: LastRead | null;
}

function load(): ReadingProgress {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { visited: new Set(), lastRead: null };
    const parsed = JSON.parse(raw) as { visited: number[]; lastRead: LastRead | null };
    return { visited: new Set(parsed.visited ?? []), lastRead: parsed.lastRead ?? null };
  } catch {
    return { visited: new Set(), lastRead: null };
  }
}

function save(p: ReadingProgress): void {
  try {
    localStorage.setItem(
      KEY,
      JSON.stringify({ visited: Array.from(p.visited), lastRead: p.lastRead })
    );
  } catch {
    // ignore full storage
  }
}

export function useReadingProgress() {
  const [progress, setProgress] = useState<ReadingProgress>(load);

  const markVisited = useCallback((surah: number, nameAr: string, nameEn: string) => {
    setProgress(prev => {
      const next: ReadingProgress = {
        visited: new Set([...prev.visited, surah]),
        lastRead: { surah, nameAr, nameEn, ts: Date.now() },
      };
      save(next);
      return next;
    });
  }, []);

  const resetProgress = useCallback(() => {
    const empty: ReadingProgress = { visited: new Set(), lastRead: null };
    save(empty);
    setProgress(empty);
  }, []);

  return { progress, markVisited, resetProgress };
}

/** Singleton helpers for use outside React (e.g., QuranPage effect) */
export function recordSurahVisit(surah: number, nameAr: string, nameEn: string): void {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? (JSON.parse(raw) as { visited: number[]; lastRead: LastRead | null }) : { visited: [], lastRead: null };
    const visitedSet = new Set(parsed.visited ?? []);
    visitedSet.add(surah);
    localStorage.setItem(KEY, JSON.stringify({ visited: Array.from(visitedSet), lastRead: { surah, nameAr, nameEn, ts: Date.now() } }));
  } catch {
    // ignore
  }
}

export function getReadingProgress(): ReadingProgress {
  return load();
}
