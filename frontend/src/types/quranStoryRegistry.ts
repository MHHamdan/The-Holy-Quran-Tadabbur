/**
 * Canonical Quran Story Registry — shared schema for /stories and /story-atlas.
 *
 * Goals:
 *   - Single source of truth merging authored stories, generated prophet
 *     story pages, and entity / topic / knowledge-graph layers.
 *   - Every entry carries explicit Quran references — never invented.
 *   - Every generated candidate defaults to needs_review.
 *
 * Read by:
 *   - frontend/src/pages/StoryAtlasPage.tsx
 *   - frontend/src/pages/StoriesPage.tsx (via storyRegistryAdapter)
 *   - scripts/validate-quran-story-registry.ts
 *   - backend/app/api/routes/story_atlas_registry.py
 */

export type RegistryStoryCategory =
  | 'prophet'
  | 'prophetic_sirah'
  | 'person'
  | 'nation'
  | 'parable'
  | 'historical'
  | 'unseen'
  | 'compact_profile'
  | 'needs_review';

export type RegistryStorySourceType =
  | 'authored_story'
  | 'prophet_story_page'
  | 'entity_story_cluster'
  | 'generated_candidate';

export type RegistryStoryReviewStatus =
  | 'verified'
  | 'needs_review'
  | 'missing_metadata';

export type RegistryQuranReferenceLinkType =
  | 'explicit'
  | 'contextual'
  | 'coreference'
  | 'story_segment'
  | 'needs_review';

export interface RegistryQuranReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  linkType: RegistryQuranReferenceLinkType;
  reviewStatus: 'verified' | 'needs_review';
}

export interface RegistryStoryEntry {
  storyId: string;
  titleArabic: string;
  titleEnglish: string;
  category: RegistryStoryCategory;
  sourceType: RegistryStorySourceType;
  quranReferences: RegistryQuranReference[];
  relatedProphets: string[];
  relatedEntities: string[];
  relatedTopics: string[];
  relatedStories: string[];
  segmentCount: number;
  surahCount: number;
  ayahRangeCount: number;
  hasDetailPage: boolean;
  detailRoute?: string;
  reviewStatus: RegistryStoryReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

export interface RegistryCoverageSummary {
  totalStories: number;
  authoredStories: number;
  prophetProfiles: number;
  generatedCandidates: number;
  missingMetadataCount: number;
  surahsCovered: number;
  prophetsCovered: number;
  ayahRangesLinked: number;
  reviewPendingCount: number;
}

export interface QuranStoryRegistryFile {
  version: string;
  generatedAt: string;
  categories: RegistryStoryCategory[];
  coverage: RegistryCoverageSummary;
  stories: RegistryStoryEntry[];
  warnings: string[];
}

export const REGISTRY_CATEGORY_LABELS: Record<
  RegistryStoryCategory,
  { ar: string; en: string }
> = {
  prophet: { ar: 'الأنبياء', en: 'Prophets' },
  prophetic_sirah: { ar: 'السيرة النبوية', en: 'Prophetic Sirah' },
  person: { ar: 'شخصيات', en: 'People' },
  nation: { ar: 'الأمم', en: 'Nations' },
  parable: { ar: 'أمثال', en: 'Parables' },
  historical: { ar: 'تاريخية', en: 'Historical' },
  unseen: { ar: 'الغيب', en: 'Unseen' },
  compact_profile: { ar: 'ملفات موجزة', en: 'Compact Profiles' },
  needs_review: { ar: 'تحتاج مراجعة', en: 'Needs Review' },
};

export const REGISTRY_CATEGORY_ORDER: RegistryStoryCategory[] = [
  'prophet',
  'prophetic_sirah',
  'person',
  'nation',
  'parable',
  'historical',
  'unseen',
  'compact_profile',
  'needs_review',
];

/**
 * Maps legacy category aliases (used by the backend `stories` table and
 * older atlas builds) to registry categories so the unified registry can
 * absorb both without dropping rows.
 */
export const REGISTRY_CATEGORY_ALIASES: Record<string, RegistryStoryCategory> = {
  prophet: 'prophet',
  prophetic: 'prophet',
  prophetic_sira: 'prophetic_sirah',
  prophetic_sirah: 'prophetic_sirah',
  named_char: 'person',
  person: 'person',
  righteous: 'person',
  companions: 'person',
  battles: 'historical',
  nation: 'nation',
  parable: 'parable',
  historical: 'historical',
  unseen: 'unseen',
  compact_profile: 'compact_profile',
  mission_summary: 'prophetic_sirah',
  needs_review: 'needs_review',
};
