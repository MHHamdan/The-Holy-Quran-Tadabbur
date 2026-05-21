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
  SubcategoryGroup,
} from '../types/quranStoryRegistry';
import {
  parseSubcategory,
  SUBCATEGORY_GROUP_ORDER,
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
    if (s.themes?.some((t) => t.toLowerCase().includes(q))) return true;
    if (s.mainFigures?.some((f) => f.toLowerCase().includes(q))) return true;
    if (s.subcategories?.some((sc) => sc.toLowerCase().includes(q))) return true;
    if (surahMatch !== null && s.quranReferences.some((r) => r.surahNumber === surahMatch)) {
      return true;
    }
    return false;
  });
}

/**
 * Filter stories by either a full "group:tag" subcategory string (e.g.
 * "animal:cow") or by the parent group alone (e.g. "animal" matches every
 * animal:* tag).
 */
export function getStoriesBySubcategory(subcategory: string): RegistryStoryEntry[] {
  if (!subcategory || subcategory === 'all') return registry.stories;
  if (subcategory.includes(':')) {
    return registry.stories.filter((s) => s.subcategories?.includes(subcategory));
  }
  const prefix = `${subcategory}:`;
  return registry.stories.filter((s) =>
    s.subcategories?.some((sc) => sc.startsWith(prefix)),
  );
}

/**
 * Build a histogram of every subcategory tag that appears across the
 * registry, grouped by parent group. Sorted by descending count within
 * each group, with groups returned in canonical SUBCATEGORY_GROUP_ORDER.
 */
export function getSubcategoryFacets(): Array<{
  group: SubcategoryGroup;
  tags: Array<{ tag: string; storyCount: number }>;
  totalStoryCount: number;
}> {
  const tagCounts = new Map<string, Set<string>>(); // group:tag → storyIds
  const groupStoryIds = new Map<SubcategoryGroup, Set<string>>();
  for (const s of registry.stories) {
    for (const tag of s.subcategories || []) {
      const parsed = parseSubcategory(tag);
      if (!parsed) continue;
      if (!tagCounts.has(tag)) tagCounts.set(tag, new Set());
      tagCounts.get(tag)!.add(s.storyId);
      if (!groupStoryIds.has(parsed.group)) groupStoryIds.set(parsed.group, new Set());
      groupStoryIds.get(parsed.group)!.add(s.storyId);
    }
  }
  const result: ReturnType<typeof getSubcategoryFacets> = [];
  for (const group of SUBCATEGORY_GROUP_ORDER) {
    const tags: Array<{ tag: string; storyCount: number }> = [];
    for (const [tag, ids] of tagCounts.entries()) {
      if (tag.startsWith(`${group}:`)) {
        tags.push({ tag, storyCount: ids.size });
      }
    }
    if (tags.length === 0) continue;
    tags.sort((a, b) => b.storyCount - a.storyCount || a.tag.localeCompare(b.tag));
    result.push({
      group,
      tags,
      totalStoryCount: groupStoryIds.get(group)?.size ?? 0,
    });
  }
  return result;
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
