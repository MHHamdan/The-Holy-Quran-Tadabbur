/**
 * Quran Prophets Atlas — TypeScript type definitions.
 *
 * Used by:
 *   - frontend/src/data/quranProphetSeeds.ts
 *   - frontend/src/data/generated/quranProphetsAtlas.json
 *   - scripts/build-quran-prophets-atlas.ts
 *   - scripts/validate-quran-prophets-atlas.ts
 *   - scripts/validate-quran-prophet-journeys.ts
 *   - scripts/validate-quran-prophet-relations.ts
 *   - backend Pydantic mirrors in app/api/routes/prophets.py
 *   - frontend pages under /prophets
 *
 * Safety rules (mirror docs/quran-content-policy.md and the prophet-list
 * policy in docs/prophets-atlas-prophet-list-policy.md):
 *   - No Quran text is embedded — only surah / ayah references.
 *   - Every storytelling field MUST be reviewStatus = "needs_review" until
 *     a human reviewer signs off.
 *   - The atlas list MUST contain exactly 25 prophets.
 *   - Disputed figures (Luqman, Dhul-Qarnayn, Maryam, Bilqis, Khidr, …)
 *     MUST NEVER appear as prophet profiles.
 *   - Every journey stage MUST carry at least one ayahReference.
 *   - Story-world chronology is always "needs_review" or "disputed".
 */

import type { QuranReference } from './quranEntityGraph';

export type { QuranReference };

// ============================================================================
// Review status (mirrors EntityReviewStatus)
// ============================================================================

export type ProphetReviewStatus =
  | 'verified'
  | 'needs_review'
  | 'missing_source';

// ============================================================================
// Ayah link
// ============================================================================

export type ProphetAyahLinkType =
  | 'explicit_name'
  | 'alias'
  | 'story_context'
  | 'coreference'
  | 'related_entity'
  | 'tafsir_source'
  | 'manual_seed';

export interface ProphetAyahLink {
  surahNumber: number;
  ayahNumber: number;
  linkType: ProphetAyahLinkType;
  /** 0 ≤ confidence ≤ 1 — deterministic, derived from linkType. */
  confidence: number;
  sourceIds: string[];
  reviewStatus: 'verified' | 'needs_review';
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Prophet-to-prophet (and prophet-to-figure) relation
// ============================================================================

export type ProphetRelationType =
  | 'family_relation'
  | 'same_people'
  | 'same_place'
  | 'similar_trial'
  | 'shared_theme'
  | 'chronological_sequence'
  | 'mentioned_together'
  | 'mission_parallel'
  | 'scripture_relation'
  | 'needs_review';

export interface ProphetRelation {
  sourceProphetId: string;
  targetProphetId: string;
  relationType: ProphetRelationType;
  /** At least one evidenceReference is REQUIRED; validators enforce. */
  evidenceReferences: QuranReference[];
  /** Generic, source-aware explanation. Never invented tafsir. */
  explanationArabic?: string;
  explanationEnglish?: string;
  confidence: number;
  sourceIds: string[];
  reviewStatus: 'verified' | 'needs_review';
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Journey
// ============================================================================

export type ProphetJourneyType =
  | 'mushaf_order'
  | 'story_world_order'
  | 'revelation_order'
  | 'thematic_order'
  | 'learning_order';

export type ProphetJourneyCertainty = 'high' | 'medium' | 'low' | 'disputed';

export interface ProphetJourneyStage {
  stageId: string;
  orderIndex: number;
  labelArabic: string;
  labelEnglish: string;
  /** REQUIRED: every stage must cite at least one ayah. */
  ayahReferences: QuranReference[];
  relatedEntities: string[];
  relatedTopics: string[];
  storytellingArabic?: string;
  storytellingEnglish?: string;
  sourceIds: string[];
  reviewStatus: 'verified' | 'needs_review';
  humanReviewRequired: boolean;
  warnings: string[];
}

export interface ProphetJourney {
  journeyId: string;
  prophetId: string;
  journeyType: ProphetJourneyType;
  titleArabic: string;
  titleEnglish: string;
  stages: ProphetJourneyStage[];
  certainty: ProphetJourneyCertainty;
  reviewStatus: 'verified' | 'needs_review';
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Prophet profile
// ============================================================================

export interface QuranProphetProfile {
  prophetId: string;
  /** Display label including عليه السلام (or ﷺ for the Prophet Muhammad). */
  nameArabic: string;
  nameEnglish: string;
  transliteration: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];

  /** Total count across explicit + alias mentions (deduped by ayah). */
  quranMentionCount: number;
  /** Unique surah count where the prophet is mentioned. */
  surahCount: number;

  explicitMentions: ProphetAyahLink[];
  contextualMentions: ProphetAyahLink[];
  coreferenceMentions: ProphetAyahLink[];

  /** Cross-link into existing storyIds (`story_*`). */
  storyIds: string[];

  /** Cross-link into existing entityIds (relatives, peoples, places, …). */
  relatedEntities: string[];
  relatedPeopleOrNations: string[];
  relatedPlaces: string[];
  relatedAnimals: string[];
  relatedObjects: string[];
  relatedEvents: string[];

  /** Cross-link into existing topicIds (themes & topics atlas). */
  relatedTopics: string[];

  relatedProphets: ProphetRelation[];

  journeys: ProphetJourney[];

  /** Optional, NEVER tafsir — needs_review until reviewed. */
  storytellingSummaryArabic?: string;
  storytellingSummaryEnglish?: string;

  sourceIds: string[];
  reviewStatus: ProphetReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Seed (input to the build script)
// ============================================================================

export interface ProphetSeed {
  prophetId: string;
  nameArabic: string;
  nameEnglish: string;
  transliteration: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
  /** Common Western/Anglicised spelling variants for search & detection. */
  spellingVariants: string[];
  /** Entity ID inside the existing graph (must start with `entity_prophet_`). */
  entityId: string;
  /** Cross-links into existing graph (used for relation seeding). */
  knownRelatedEntityIds: string[];
  knownRelatedStoryIds: string[];
  /** Initial story-world order index (1-based). Always needs_review. */
  initialStoryWorldOrderIndex: number;
  /** True once a reviewer has signed off on the canonical prophet entry. */
  reviewStatus: ProphetReviewStatus;
  notes?: string;
}

// ============================================================================
// Related-figures policy entry (NOT a prophet)
// ============================================================================

export interface ProphetRelatedFigure {
  figureId: string;
  nameArabic: string;
  nameEnglish: string;
  /** Why this figure is NOT classified as a prophet. */
  policyReason: string;
  /** Optional Quran ayah anchors for the figure. */
  ayahReferences: QuranReference[];
  /** True if scholars disagree about prophethood. */
  disputed: boolean;
  /** Notes summarising the dispute (kept short, source-aware). */
  disputeNotes: string;
  /** Which prophet profile(s) the figure should appear under. */
  relatedProphetIds: string[];
}

// ============================================================================
// Build-time output (the generated atlas file)
// ============================================================================

export interface ProphetAtlasSummary {
  totalProphets: number;
  totalExplicitMentions: number;
  totalContextualMentions: number;
  totalCoreferenceMentions: number;
  totalRelations: number;
  totalJourneys: number;
  totalAyahLinks: number;
  prophetsWithStoryPages: number;
  prophetsMissingStoryPages: string[];
  prophetsWeakData: string[];
  topRelatedProphets: Array<{ sourceProphetId: string; targetProphetId: string; count: number }>;
  reviewWarnings: string[];
}

export interface QuranProphetsAtlas {
  version: string;
  generatedAt: string;
  profiles: QuranProphetProfile[];
  relatedFigures: ProphetRelatedFigure[];
  summary: ProphetAtlasSummary;
  warnings: string[];
}

// ============================================================================
// Helpers
// ============================================================================

/** Confidence band per ayah-link type. */
export const PROPHET_LINK_CONFIDENCE: Record<ProphetAyahLinkType, number> = {
  explicit_name: 0.95,
  alias: 0.8,
  story_context: 0.5,
  coreference: 0.55,
  related_entity: 0.5,
  tafsir_source: 0.6,
  manual_seed: 0.7,
};

/**
 * Returns the default review status for an ayah link of this type.
 * Only explicit_name is allowed to default to verified, and even then
 * humanReviewRequired remains true until a reviewer signs off.
 */
export function defaultProphetLinkReviewStatus(
  t: ProphetAyahLinkType,
): 'verified' | 'needs_review' {
  // Even explicit_name defaults to needs_review at the link level —
  // exactly mirroring MENTION_TYPE_DEFAULT_STATUS in quranEntityGraph.ts.
  void t;
  return 'needs_review';
}

export function isProphetEntityId(entityId: string): boolean {
  return entityId.startsWith('entity_prophet_');
}
