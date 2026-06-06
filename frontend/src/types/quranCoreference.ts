/**
 * Quran Coreference Layer — type contracts for the Phase U implicit-entity
 * linking system. Sits on top of `quranEntityGraph.ts` and consumes the
 * existing explicit entity mentions.
 *
 * Used by:
 *   - frontend/src/data/quranCoreferencePatterns.ts (pattern dictionary)
 *   - scripts/scan-quran-coreference.ts (mention + chain producer)
 *   - scripts/enrich-quran-entity-relations-with-coreference.ts
 *   - scripts/validate-quran-coreference*.ts
 *   - frontend pages under /entities (implicit-section UI)
 *   - backend routes under /api/v1/quran/entities/{id}/coreference*
 *
 * Safety rules (mirror docs/quran-content-policy.md):
 *   - No Quran text is embedded in any record — only surah/ayah numbers and
 *     short normalised surface tokens (`surfaceText`, <=80 chars).
 *   - Every coreference mention defaults to reviewStatus = "needs_review"
 *     and humanReviewRequired = true.
 *   - `cross_surah_candidate` chains are ALWAYS needs_review, never auto-
 *     promoted.
 *   - `tafsir_source` resolutions require a trusted sourceId; otherwise the
 *     scanner falls back to a generic relation candidate.
 *   - `selectedEntityId` is informational only — it never represents a
 *     verified identity until a reviewer signs off.
 */

import type { QuranReference } from './quranEntityGraph';

// ============================================================================
// Surface taxonomy
// ============================================================================

/**
 * The shape of the surface token that triggered the coreference candidate.
 * `explicit_name` is included so chains can include an explicit anchor; the
 * scanner does not emit `explicit_name` as a new mention — it reuses the
 * existing entity-mention record.
 */
export type CoreferenceSurfaceType =
  | 'pronoun'
  | 'possessive_pronoun'
  | 'title'
  | 'family_reference'
  | 'role_reference'
  | 'demonstrative'
  | 'implicit_context'
  | 'explicit_name';

// ============================================================================
// Resolution method
// ============================================================================

export type CoreferenceResolutionMethod =
  | 'rule_pattern'
  | 'same_ayah_nearest_entity'
  | 'same_passage_context'
  | 'story_segment_context'
  | 'existing_entity_graph'
  | 'tafsir_source'
  | 'manual_review';

// ============================================================================
// Review status (re-exported for convenience; matches entity layer)
// ============================================================================

export type CoreferenceReviewStatus = 'verified' | 'needs_review' | 'rejected';

// ============================================================================
// Evidence reference
// ============================================================================

export type CoreferenceEvidenceType =
  | 'quran_text_pattern'
  | 'story_segment'
  | 'entity_graph'
  | 'tafsir_source'
  | 'manual_seed';

export interface CoreferenceEvidenceReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  sourceIds: string[];
  evidenceType: CoreferenceEvidenceType;
}

// ============================================================================
// Mention
// ============================================================================

export interface CoreferenceMention {
  mentionId: string;
  surfaceType: CoreferenceSurfaceType;
  /** Short normalised Arabic surface (<=80 chars, no newlines). */
  surfaceText?: string;
  surahNumber: number;
  ayahNumber: number;
  tokenIndex?: number;
  phraseStart?: number;
  phraseEnd?: number;
  /** Always at least one — the scanner refuses to emit empty candidates. */
  candidateEntityIds: string[];
  /** Top-1 candidate when the scanner is confident; never auto-verified. */
  selectedEntityId?: string;
  confidence: number;
  resolutionMethod: CoreferenceResolutionMethod;
  evidenceReferences: CoreferenceEvidenceReference[];
  reviewStatus: CoreferenceReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Chain
// ============================================================================

export type CoreferenceChainType =
  | 'local_passage'
  | 'surah_level'
  | 'story_level'
  | 'cross_surah_candidate';

export interface CoreferenceChain {
  chainId: string;
  entityId: string;
  /** Member mentionIds (must reference real CoreferenceMention or explicit
   *  entity mention IDs). Always >=2. */
  mentions: string[];
  /** Distinct surahs covered by this chain. */
  surahScope: number[];
  /** Inclusive start, formatted "S:A". */
  ayahRangeStart: string;
  /** Inclusive end, formatted "S:A". */
  ayahRangeEnd: string;
  chainType: CoreferenceChainType;
  confidence: number;
  reviewStatus: CoreferenceReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Pattern dictionary
// ============================================================================

/**
 * A coreference pattern is a deterministic rule that emits *candidate* entity
 * links from Quran text. Patterns are intentionally conservative: they limit
 * matches by surah, by an existing entity-graph anchor, or by a story-segment
 * window. They never assert a final identity.
 */
export interface CoreferencePattern {
  patternId: string;
  /** Short human-readable description (for review docs). */
  description: string;
  surfaceType: CoreferenceSurfaceType;
  /** Normalised Arabic phrase to match in the ayah text (post-normalisation). */
  surfaceArabicNormalised: string;
  /** The entity this pattern proposes as a candidate. */
  candidateEntityId: string;
  /**
   * Anchor constraint: at least one of the listed entityIds must have an
   * explicit/alias mention in the SAME surah for the pattern to fire. Empty
   * array means "no entity anchor required" (still requires either a story
   * anchor or an explicit surah allowlist).
   */
  requiresEntityAnchorInSurah: string[];
  /** Surah allowlist. Empty array means "any surah". */
  allowedSurahs: number[];
  /** Story-segment anchor: pattern fires only if (surah, ayah) falls within
   *  one of these story ranges. Empty array means "no story anchor". */
  allowedStoryRanges: Array<{ surahNumber: number; ayahStart: number; ayahEnd: number; storyId?: string }>;
  resolutionMethod: CoreferenceResolutionMethod;
  /** Base confidence ∈ [0,1]; may be downgraded by the scanner. */
  baseConfidence: number;
  /** SourceIds attached to every emitted mention (e.g. `quran_uthmani_cloud`). */
  sourceIds: string[];
  /** Notes propagated as `warnings[]` on the emitted mention. */
  warnings: string[];
}

// ============================================================================
// Outputs
// ============================================================================

export interface CoreferenceScanOutput {
  version: string;
  generatedAt: string;
  totalMentions: number;
  totalChains: number;
  mentionsBySurfaceType: Partial<Record<CoreferenceSurfaceType, number>>;
  mentionsByResolutionMethod: Partial<Record<CoreferenceResolutionMethod, number>>;
  /** entityIds that previously had zero explicit mentions but now gained at
   *  least one coreference candidate. */
  zeroMatchEntitiesImproved: string[];
  /** Full mention list (sorted by surah, ayah). */
  mentions: CoreferenceMention[];
  warnings: string[];
}

export interface CoreferenceChainsOutput {
  version: string;
  generatedAt: string;
  totalChains: number;
  chainsByType: Partial<Record<CoreferenceChainType, number>>;
  chains: CoreferenceChain[];
  warnings: string[];
}

// ============================================================================
// Enriched-relation output
// ============================================================================

export type EnrichedCoreferenceEdgeType =
  | 'IMPLICITLY_REFERS_TO'
  | 'PRONOUN_REFERS_TO'
  | 'TITLE_REFERS_TO'
  | 'FAMILY_REFERENCE_TO'
  | 'CONTEXTUAL_ENTITY_LINK'
  | 'STORY_OBJECT_LINK';

export interface EnrichedCoreferenceEdge {
  sourceEntityId: string;
  targetEntityId: string;
  edgeType: EnrichedCoreferenceEdgeType;
  mentionIds: string[];
  evidenceReferences: QuranReference[];
  sourceIds: string[];
  confidence: number;
  reviewStatus: CoreferenceReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

export interface EnrichedRelationsOutput {
  version: string;
  generatedAt: string;
  /** Mirrors the upstream `quranEntityRelations.json` for traceability. */
  baseRelationCount: number;
  /** Number of coreference-derived edges added. */
  coreferenceEdgeCount: number;
  /** Original explicit relations, untouched. */
  baseRelations: unknown[];
  coreferenceEdges: EnrichedCoreferenceEdge[];
  /** Conflicts where a coreference edge contradicts an existing verified
   *  relation. These edges remain needs_review and are NOT applied. */
  conflicts: Array<{
    sourceEntityId: string;
    targetEntityId: string;
    explicitRelationType: string;
    coreferenceEdgeType: EnrichedCoreferenceEdgeType;
    reason: string;
  }>;
  warnings: string[];
}

// ============================================================================
// Default review status helpers
// ============================================================================

/**
 * Only an `explicit_name` mention may carry a default of `needs_review` at
 * the high-confidence band; every other surface stays `needs_review` until a
 * reviewer signs off. No surface ever auto-`verified`.
 */
export function defaultCoreferenceReviewStatus(
  _s: CoreferenceSurfaceType
): CoreferenceReviewStatus {
  return 'needs_review';
}

export function defaultCoreferenceHumanReviewRequired(
  _s: CoreferenceSurfaceType
): boolean {
  return true;
}
