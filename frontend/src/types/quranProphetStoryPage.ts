/**
 * Quran Prophet Story Page — TypeScript type definitions (Phase X2).
 *
 * Used by:
 *   - scripts/build-missing-prophet-story-pages.ts
 *   - scripts/validate-quran-prophet-story-pages.ts
 *   - frontend/src/data/generated/quranProphetStoryPages.json
 *   - backend Pydantic mirrors in app/api/routes/prophets.py
 *   - frontend ProphetDetailPage.tsx
 *
 * Safety contract (mirrors docs/quran-content-policy.md):
 *   - No Quran text is embedded — only surah/ayah references.
 *   - Every section MUST cite at least one ayahReferences entry, except
 *     for `sectionType: "limited_mentions"` / `"summary_only"` which
 *     MAY (and typically do) cite a smaller set.
 *   - All summaries default to reviewStatus = "needs_review".
 *   - Storytelling is not tafsir — never auto-promote to verified.
 *   - For prophets with limited Quran detail (Dhul-Kifl, Al-Yasa) the
 *     pageType MUST be "compact_profile" with a warning.
 *   - For Muhammad ﷺ the pageType MUST be "mission_summary" with a
 *     not-full-biography warning.
 */

import type { QuranReference } from './quranEntityGraph';

export type { QuranReference };

// ============================================================================
// Page-level
// ============================================================================

export type ProphetStoryPageType =
  | 'full_story'
  | 'compact_profile'
  | 'contextual_mentions'
  | 'mission_summary'
  | 'limited_quran_mentions';

export type ProphetStoryPageReviewStatus =
  | 'verified'
  | 'needs_review'
  | 'missing_source';

// ============================================================================
// References (a slim sibling of QuranReference with link metadata)
// ============================================================================

export type ProphetStoryReferenceLinkType =
  | 'explicit_name'
  | 'same_passage'
  | 'related_entity'
  | 'coreference'
  | 'story_context'
  | 'topic_context'
  | 'tafsir_source';

export interface ProphetStoryReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  linkType: ProphetStoryReferenceLinkType;
  /** 0 ≤ confidence ≤ 1, derived from linkType. */
  confidence: number;
  sourceIds: string[];
  reviewStatus: 'needs_review' | 'verified';
  humanReviewRequired: boolean;
}

// ============================================================================
// Sections
// ============================================================================

export type ProphetStorySectionType =
  | 'birth_or_family'
  | 'mission'
  | 'trial'
  | 'dialogue'
  | 'miracle_or_sign'
  | 'people_or_nation'
  | 'scripture_or_revelation'
  | 'relation_to_other_prophet'
  | 'summary_only'
  | 'limited_mentions';

export interface ProphetStorySection {
  sectionId: string;
  labelArabic: string;
  labelEnglish: string;
  /** REQUIRED: every section must cite ≥ 1 ayah reference. */
  ayahReferences: QuranReference[];
  sectionType: ProphetStorySectionType;
  summaryArabic?: string;
  summaryEnglish?: string;
  sourceIds: string[];
  reviewStatus: 'needs_review' | 'verified';
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Chronology notes (page-level)
// ============================================================================

export type ProphetChronologyType =
  | 'mushaf_order'
  | 'story_world_guided'
  | 'revelation_order';

export type ProphetChronologyCertainty = 'high' | 'medium' | 'low' | 'disputed';

export interface ChronologyNote {
  chronologyType: ProphetChronologyType;
  noteArabic: string;
  noteEnglish: string;
  certainty: ProphetChronologyCertainty;
  sourceIds: string[];
  reviewStatus: 'needs_review' | 'verified';
}

// ============================================================================
// Full page
// ============================================================================

export interface ProphetStoryPage {
  storyPageId: string;
  prophetId: string;
  titleArabic: string;
  titleEnglish: string;
  pageType: ProphetStoryPageType;
  quranReferences: ProphetStoryReference[];
  storySections: ProphetStorySection[];
  relatedProphets: string[];
  relatedFigures: string[];
  relatedPlaces: string[];
  relatedNations: string[];
  relatedObjects: string[];
  relatedTopics: string[];
  chronologyNotes: ChronologyNote[];
  sourceIds: string[];
  reviewStatus: ProphetStoryPageReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Generated file shape
// ============================================================================

export interface ProphetStoryPagesFile {
  version: string;
  generatedAt: string;
  totalPages: number;
  pageTypeBreakdown: Partial<Record<ProphetStoryPageType, number>>;
  prophetIdsCovered: string[];
  pages: ProphetStoryPage[];
  warnings: string[];
}

// ============================================================================
// Helpers
// ============================================================================

export const PROPHET_STORY_LINK_CONFIDENCE: Record<
  ProphetStoryReferenceLinkType,
  number
> = {
  explicit_name: 0.95,
  same_passage: 0.75,
  related_entity: 0.6,
  coreference: 0.55,
  story_context: 0.55,
  topic_context: 0.5,
  tafsir_source: 0.6,
};

/**
 * The 9 prophets that were missing story pages at the end of Phase X.
 * Validators assert that every one of these has a story page entry.
 *
 * Note: the original Phase X2 brief listed 8 prophets; Ismail was added
 * during validator review because the Phase X atlas build flagged him
 * as `missing_story_page` too. Adding him keeps the coverage guarantee
 * intact for all 25 prophets.
 */
export const PHASE_X2_REQUIRED_PROPHET_IDS = [
  'prophet_ishaq',
  'prophet_yaqub',
  'prophet_harun',
  'prophet_dhulkifl',
  'prophet_ilyas',
  'prophet_alyasa',
  'prophet_sulayman',
  'prophet_muhammad',
  'prophet_ismail',
] as const;

export type PhaseX2RequiredProphetId = (typeof PHASE_X2_REQUIRED_PROPHET_IDS)[number];

/** Prophets that must default to compact_profile because the Quran's
 *  detail about them is brief (≤ 2 explicit ayahs). */
export const COMPACT_PROFILE_PROPHET_IDS: ReadonlySet<string> = new Set([
  'prophet_dhulkifl',
  'prophet_alyasa',
]);

/** Prophets that must default to mission_summary with extra warnings. */
export const MISSION_SUMMARY_PROPHET_IDS: ReadonlySet<string> = new Set([
  'prophet_muhammad',
]);

export const MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_AR =
  'هذه الصفحة تعرض الشواهد القرآنية فقط ولا تمثل سيرة كاملة للنبي ﷺ.';
export const MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_EN =
  'This page presents Quranic evidence only and is not a full biography of the Prophet ﷺ.';

export const LIMITED_QURAN_MENTIONS_WARNING_AR =
  'القرآن لا يفصّل قصة هذا النبي؛ هذا ملف موجز.';
export const LIMITED_QURAN_MENTIONS_WARNING_EN =
  'The Quran does not narrate this prophet in detail; this is a compact profile.';
