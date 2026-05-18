/**
 * Story Registry Adapter — shared by /stories and /story-atlas.
 *
 * Loads the canonical registry from
 * `frontend/src/data/generated/quranStoryRegistry.json` and exposes
 * functions both pages can use without duplicating filter / search logic.
 *
 * Both pages must use this adapter — anything reading story data directly
 * from quranStories.ts or from the backend should be migrated.
 *
 * The registry is the source of truth for: titles, categories,
 * Quran references, related prophets/entities/topics, review status.
 */

import registryRaw from '../data/generated/quranStoryRegistry.json';
import type {
  QuranStoryRegistryFile,
  RegistryStoryEntry,
  RegistryStoryCategory,
} from '../types/quranStoryRegistry';

const registry = registryRaw as QuranStoryRegistryFile;

export function getRegistry(): QuranStoryRegistryFile {
  return registry;
}

export function getAllStoriesForCards(): RegistryStoryEntry[] {
  return registry.stories;
}

export function getStoriesByCategory(category: RegistryStoryCategory | 'all'): RegistryStoryEntry[] {
  if (category === 'all') return registry.stories;
  return registry.stories.filter((s) => s.category === category);
}

export function searchStories(query: string): RegistryStoryEntry[] {
  const q = query.trim().toLowerCase();
  if (!q) return registry.stories;

  // Allow searching by surah number (e.g. "12" matches Yusuf)
  const surahMatch = /^\d{1,3}$/.test(q) ? parseInt(q, 10) : null;

  return registry.stories.filter((s) => {
    if (s.titleArabic.toLowerCase().includes(q)) return true;
    if (s.titleEnglish.toLowerCase().includes(q)) return true;
    if (s.storyId.toLowerCase().includes(q)) return true;
    if (s.relatedProphets.some((p) => p.toLowerCase().includes(q))) return true;
    if (s.relatedEntities.some((e) => e.toLowerCase().includes(q))) return true;
    if (s.relatedTopics.some((t) => t.toLowerCase().includes(q))) return true;
    if (surahMatch !== null && s.quranReferences.some((r) => r.surahNumber === surahMatch)) {
      return true;
    }
    return false;
  });
}

export function getStoryDetailRoute(storyId: string): string | undefined {
  return registry.stories.find((s) => s.storyId === storyId)?.detailRoute;
}

export function getStoryReviewStatus(storyId: string): RegistryStoryEntry['reviewStatus'] | null {
  return registry.stories.find((s) => s.storyId === storyId)?.reviewStatus ?? null;
}

export function getStorySourceType(storyId: string): RegistryStoryEntry['sourceType'] | null {
  return registry.stories.find((s) => s.storyId === storyId)?.sourceType ?? null;
}

export function getCoverage() {
  return registry.coverage;
}

export function getWarnings(): string[] {
  return registry.warnings;
}

export function isRegistryHealthy(): boolean {
  return registry.stories.length > 0;
}

/** Backwards-compatibility for components written before the registry existed. */
export interface RegistryStoryCard {
  id: string;
  name_ar: string;
  name_en: string;
  category: string;
  main_figures: string[];
  themes: string[];
  summary_ar?: string;
  summary_en?: string;
  suras_mentioned: number[];
  total_verses: number;
}

export function toLegacyStoryCard(entry: RegistryStoryEntry): RegistryStoryCard {
  const surahs = Array.from(new Set(entry.quranReferences.map((r) => r.surahNumber)));
  const totalVerses = entry.quranReferences.reduce((acc, r) => {
    return acc + ((r.ayahEnd ?? r.ayahStart) - r.ayahStart + 1);
  }, 0);
  return {
    id: entry.storyId,
    name_ar: entry.titleArabic,
    name_en: entry.titleEnglish,
    category: entry.category,
    main_figures: entry.relatedProphets,
    themes: entry.relatedTopics,
    summary_ar: undefined,
    summary_en: undefined,
    suras_mentioned: surahs,
    total_verses: totalVerses,
  };
}
