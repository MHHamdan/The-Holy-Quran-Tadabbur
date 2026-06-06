/**
 * Quran Entity Graph — TypeScript type definitions for the
 * Entity-Centered Quran Narrative GraphRAG system.
 *
 * Used by:
 *   - frontend/src/data/quranEntitySeeds.ts (seed dictionary)
 *   - frontend/src/data/generated/quranEntityMentions.json (scan output)
 *   - frontend/src/data/generated/quranEntityRelations.json (relation output)
 *   - frontend/src/data/generated/quranEntityJourneys.json (journey output)
 *   - scripts/scan-quran-entity-mentions.ts
 *   - scripts/build-quran-entity-relations.ts
 *   - scripts/build-quran-entity-journeys.ts
 *   - scripts/validate-quran-entity-*.ts
 *   - backend Pydantic mirrors and API responses
 *   - frontend pages under /entities
 *
 * Safety rules (mirror docs/quran-content-policy.md):
 *   - No Quran text is embedded in any record of these types — only
 *     surahNumber, ayahStart, ayahEnd references.
 *   - Every relation MUST carry at least one evidenceReferences entry.
 *   - Every sourceId referenced MUST exist in sourceRegistry.ts.
 *   - story_context, pronoun_context, tafsir_context, family_relation
 *     mention types MUST default to reviewStatus = "needs_review" and
 *     humanReviewRequired = true.
 *   - Chronology stages must clearly separate story_world, mushaf_order,
 *     revelation_order, and thematic_order — they are never mixed.
 *   - "verified" status is reserved for human reviewer sign-off; the
 *     pipeline never emits "verified" automatically.
 */

// ============================================================================
// Entity taxonomy
// ============================================================================

export type QuranEntityType =
  | 'prophet'
  | 'person'
  | 'woman'
  | 'people_or_nation'
  | 'place'
  | 'animal'
  | 'object'
  | 'event'
  | 'angel'
  | 'jinn'
  | 'scripture'
  | 'title_or_role'
  | 'family_relation'
  | 'concept'
  | 'theme'
  | 'unknown';

export const ENTITY_TYPE_META: Record<QuranEntityType, { labelAr: string; labelEn: string }> = {
  prophet: { labelAr: 'نبي', labelEn: 'Prophet' },
  person: { labelAr: 'شخصية', labelEn: 'Person' },
  woman: { labelAr: 'امرأة', labelEn: 'Woman' },
  people_or_nation: { labelAr: 'أمة/قوم', labelEn: 'People or Nation' },
  place: { labelAr: 'مكان', labelEn: 'Place' },
  animal: { labelAr: 'حيوان', labelEn: 'Animal' },
  object: { labelAr: 'شيء', labelEn: 'Object' },
  event: { labelAr: 'حدث', labelEn: 'Event' },
  angel: { labelAr: 'ملك', labelEn: 'Angel' },
  jinn: { labelAr: 'جن', labelEn: 'Jinn' },
  scripture: { labelAr: 'كتاب سماوي', labelEn: 'Scripture' },
  title_or_role: { labelAr: 'لقب/دور', labelEn: 'Title or Role' },
  family_relation: { labelAr: 'صلة قرابة', labelEn: 'Family Relation' },
  concept: { labelAr: 'مفهوم', labelEn: 'Concept' },
  theme: { labelAr: 'محور', labelEn: 'Theme' },
  unknown: { labelAr: 'غير محدد', labelEn: 'Unknown' },
};

// ============================================================================
// Review and confidence
// ============================================================================

export type EntityReviewStatus = 'verified' | 'needs_review' | 'rejected';

export type EntityMentionType =
  | 'explicit_name'
  | 'alias'
  | 'title'
  | 'family_relation'
  | 'story_context'
  | 'pronoun_context'
  | 'tafsir_context';

/** Mention-type confidence band (deterministic; safe for both client + scripts). */
export const MENTION_TYPE_CONFIDENCE: Record<EntityMentionType, number> = {
  explicit_name: 0.95,
  alias: 0.8,
  title: 0.65,
  family_relation: 0.6,
  story_context: 0.5,
  pronoun_context: 0.35,
  tafsir_context: 0.55,
};

/**
 * Only `explicit_name` may be auto-promoted in the pipeline to a high-confidence
 * needs_review mention — every other type stays needs_review until reviewed.
 * No type is ever auto-`verified`.
 */
export const MENTION_TYPE_DEFAULT_STATUS: Record<EntityMentionType, EntityReviewStatus> = {
  explicit_name: 'needs_review',
  alias: 'needs_review',
  title: 'needs_review',
  family_relation: 'needs_review',
  story_context: 'needs_review',
  pronoun_context: 'needs_review',
  tafsir_context: 'needs_review',
};

// ============================================================================
// Quran reference (no text embedded)
// ============================================================================

export interface QuranReference {
  surahNumber: number;
  ayahStart: number;
  /** Inclusive end of range. If absent the reference is a single ayah. */
  ayahEnd?: number;
}

// ============================================================================
// Entity mention
// ============================================================================

export interface EntityMention {
  surahNumber: number;
  ayahNumber: number;
  mentionType: EntityMentionType;
  /** 0 ≤ confidence ≤ 1, derived from mentionType + alias specificity. */
  confidence: number;
  /** Surface Arabic token (normalised). Never the full ayah text. */
  matchedText?: string;
  sourceIds: string[];
  reviewStatus: EntityReviewStatus;
  humanReviewRequired: boolean;
}

// ============================================================================
// Entity relation
// ============================================================================

export type EntityRelationType =
  | 'mother_of'
  | 'son_of'
  | 'father_of'
  | 'daughter_of'
  | 'wife_of'
  | 'husband_of'
  | 'brother_of'
  | 'sister_of'
  | 'guardian_of'
  | 'family_of'
  | 'same_story'
  | 'same_event'
  | 'same_surah_context'
  | 'theological_discussion'
  | 'chronological_before'
  | 'chronological_after'
  | 'related_theme'
  | 'related_tafsir'
  | 'mentioned_with';

export interface EntityRelation {
  sourceEntityId: string;
  targetEntityId: string;
  relationType: EntityRelationType;
  /** At least one ayah reference is REQUIRED. Validators reject empty arrays. */
  evidenceReferences: QuranReference[];
  /** Generic, source-aware explanation. Never invented tafsir. */
  explanationArabic?: string;
  explanationEnglish?: string;
  confidence: number;
  reviewStatus: EntityReviewStatus;
  humanReviewRequired: boolean;
  sourceIds: string[];
  warnings: string[];
}

// ============================================================================
// Chronological staging
// ============================================================================

export type ChronologyStageType =
  | 'story_world'
  | 'mushaf_order'
  | 'revelation_order'
  | 'thematic_order';

export type ChronologyCertainty = 'high' | 'medium' | 'low' | 'disputed';

export interface ChronologicalStage {
  stageId: string;
  labelArabic: string;
  labelEnglish: string;
  orderIndex: number;
  stageType: ChronologyStageType;
  ayahReferences: QuranReference[];
  certainty: ChronologyCertainty;
  reviewStatus: EntityReviewStatus;
  sourceIds: string[];
  warnings: string[];
}

// ============================================================================
// Entity node — the canonical entry
// ============================================================================

export interface EntityNode {
  entityId: string;
  entityType: QuranEntityType;
  labelArabic: string;
  labelEnglish: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
  transliterations: string[];
  descriptionArabic?: string;
  descriptionEnglish?: string;
  quranMentions: EntityMention[];
  relatedEntities: EntityRelation[];
  /** storyIds from the existing story system. */
  relatedStories: string[];
  /** themeIds from the existing theme system. */
  relatedThemes: string[];
  chronologicalStages: ChronologicalStage[];
  reviewStatus: EntityReviewStatus;
  humanReviewRequired: boolean;
  sourceIds: string[];
  warnings: string[];
}

// ============================================================================
// Seed entry — minimal input to the scanner
// ============================================================================

/**
 * A seed is a candidate-detection dictionary entry. The scanner converts
 * it into an EntityNode by attaching `quranMentions`. Seeds intentionally
 * carry no mentions of their own.
 */
export interface EntitySeed {
  entityId: string;
  entityType: QuranEntityType;
  labelArabic: string;
  labelEnglish: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
  transliterations?: string[];
  descriptionArabic?: string;
  descriptionEnglish?: string;
  /** Cross-link to existing story IDs. */
  relatedStories?: string[];
  /** Cross-link to existing theme IDs. */
  relatedThemes?: string[];
  /** Cross-link to existing entityIds (used for hard family relations). */
  knownRelatives?: Array<{
    entityId: string;
    relationType: EntityRelationType;
  }>;
  warnings?: string[];
  /** Whether a human reviewer has approved this seed entry as production-safe. */
  reviewedDictionary?: boolean;
}

// ============================================================================
// Scan output
// ============================================================================

export interface EntityMentionScanOutput {
  version: string;
  generatedAt: string;
  scannedSurahs: number;
  totalEntities: number;
  totalMentions: number;
  mentionsByEntityType: Partial<Record<QuranEntityType, number>>;
  mentionsBySurah: Record<number, number>;
  /** Detailed per-entity mention list. */
  entities: Array<{
    entityId: string;
    entityType: QuranEntityType;
    labelArabic: string;
    labelEnglish: string;
    mentions: EntityMention[];
  }>;
  /** Entities with zero detected mentions. */
  emptyEntityIds: string[];
  /** Aliases that triggered downgrade warnings (generic common words). */
  ambiguousAliases: Array<{
    entityId: string;
    aliasArabic: string;
    reason: string;
  }>;
  warnings: string[];
}

// ============================================================================
// Relation output
// ============================================================================

export interface EntityRelationOutput {
  version: string;
  generatedAt: string;
  totalRelations: number;
  totalEntitiesInvolved: number;
  relationsByType: Partial<Record<EntityRelationType, number>>;
  relations: EntityRelation[];
  warnings: string[];
}

// ============================================================================
// Journey output
// ============================================================================

export interface EntityJourneySection {
  sectionId: string;
  labelArabic: string;
  labelEnglish: string;
  /** The thematic bucket if stageType is thematic_order. */
  themeKey?: string;
  ayahReferences: QuranReference[];
  notesArabic?: string;
  notesEnglish?: string;
  reviewStatus: EntityReviewStatus;
  warnings: string[];
}

export interface EntityJourney {
  entityId: string;
  stageType: ChronologyStageType;
  certainty: ChronologyCertainty;
  sections: EntityJourneySection[];
  /** Surface-level reviewStatus for the entire journey (worst-of). */
  reviewStatus: EntityReviewStatus;
  sourceIds: string[];
  warnings: string[];
}

export interface EntityJourneyOutput {
  version: string;
  generatedAt: string;
  totalEntities: number;
  journeysByStageType: Partial<Record<ChronologyStageType, number>>;
  /** entityId -> journeys keyed by stageType. */
  journeys: Record<string, Partial<Record<ChronologyStageType, EntityJourney>>>;
  warnings: string[];
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Family-relation, story-context, pronoun-context, tafsir-context mentions
 * MUST be needs_review unless promoted by a reviewer.
 */
export function defaultMentionReviewStatus(mt: EntityMentionType): EntityReviewStatus {
  return MENTION_TYPE_DEFAULT_STATUS[mt];
}

export function defaultHumanReviewRequired(mt: EntityMentionType): boolean {
  // Even explicit_name is needs_review at the mention level; every type
  // requires human review until promoted.
  void mt;
  return true;
}

export function isVerifiedRelationType(rt: EntityRelationType): boolean {
  // Hard family-relation types can carry verified status ONLY when reviewed.
  // This helper is informational — the pipeline never auto-verifies.
  return (
    rt === 'mother_of' ||
    rt === 'son_of' ||
    rt === 'father_of' ||
    rt === 'daughter_of' ||
    rt === 'wife_of' ||
    rt === 'husband_of'
  );
}
