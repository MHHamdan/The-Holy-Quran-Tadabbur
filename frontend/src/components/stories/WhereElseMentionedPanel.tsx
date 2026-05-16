/**
 * WhereElseMentionedPanel — shows where else a story / entity is mentioned.
 *
 * Data source: scan output (frontend/src/data/generated/quranStoryConnections.json).
 *
 * Safety:
 *   - Renders surah/ayah references only — no Quran text.
 *   - Every link carries the scan's `needs_review` status.
 */

import { Link } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import scanData from '../../data/generated/quranStoryConnections.json';
import { QURAN_STORY_ENTITY_SEEDS } from '../../data/quranStoryEntitySeeds';
import { QURAN_STORIES_FIRST_BATCH } from '../../data/quranStories';
import type { ScanOutput } from '../../types/quranStoryConnection';

const scan = scanData as ScanOutput;

interface Props {
  /** Either entityId or storyId — when storyId is given, resolves to all
   * entities whose `relatedStories` includes that storyId. */
  entityId?: string;
  storyId?: string;
  maxSurahs?: number;
}

export function WhereElseMentionedPanel({ entityId, storyId, maxSurahs = 8 }: Props) {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  let targets: string[] = [];
  if (entityId) {
    targets = [entityId];
  } else if (storyId) {
    targets = QURAN_STORY_ENTITY_SEEDS
      .filter((e) => e.relatedStories.includes(storyId))
      .map((e) => e.entityId);
  }
  if (targets.length === 0) return null;

  const surahSet = new Set<number>();
  for (const t of targets) {
    const entry = scan.entityIndex.find((e) => e.entityId === t);
    if (!entry) continue;
    for (const occ of entry.occurrences) surahSet.add(occ.surahNumber);
  }
  if (surahSet.size === 0) return null;

  const surahs = Array.from(surahSet).sort((a, b) => a - b).slice(0, maxSurahs);
  const surahLookup = scan.surahs;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-sm">
          {isArabic ? 'حيث ذُكر هذا في القرآن' : 'Where else this is mentioned'}
        </h4>
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
          {isArabic ? 'بحاجة للمراجعة' : 'needs_review'}
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-3">
        {isArabic
          ? 'الروابط مبنية على الاسم الصريح؛ تحتاج مراجعة علمية.'
          : 'Links are explicit-name candidates pending scholarly review.'}
      </p>
      <ul className="flex flex-wrap gap-2">
        {surahs.map((s) => {
          const name = surahLookup.find((x) => x.surahNumber === s);
          return (
            <li key={s}>
              <Link
                to={`/quran/${s}`}
                className="inline-flex items-center text-xs px-2 py-1 rounded border border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
              >
                {s}. {isArabic ? name?.surahNameArabic : name?.surahNameEnglish ?? name?.surahNameArabic}
                <ExternalLink className="w-3 h-3 ml-1" />
              </Link>
            </li>
          );
        })}
        {surahSet.size > maxSurahs && (
          <li>
            <Link
              to="/story-atlas/connections"
              className="text-xs text-emerald-700 underline px-2 py-1"
            >
              +{surahSet.size - maxSurahs} {isArabic ? 'سور أخرى' : 'more surahs'}
            </Link>
          </li>
        )}
      </ul>
    </div>
  );
}

/** Convenience helper for the StoryDetailPage. */
export function getRelatedSurahsForStory(storyId: string): number[] {
  const found = new Set<number>();
  const targets = QURAN_STORY_ENTITY_SEEDS
    .filter((e) => e.relatedStories.includes(storyId))
    .map((e) => e.entityId);
  for (const t of targets) {
    const entry = scan.entityIndex.find((e) => e.entityId === t);
    if (!entry) continue;
    for (const occ of entry.occurrences) found.add(occ.surahNumber);
  }
  return Array.from(found).sort((a, b) => a - b);
}

/** Detects whether the story exists in the curated stories file (for UI guards). */
export function storyExists(storyId: string): boolean {
  return QURAN_STORIES_FIRST_BATCH.some((s) => s.storyId === storyId);
}
