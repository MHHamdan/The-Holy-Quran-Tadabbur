/**
 * Quran Story Connection — Entity & Edge Taxonomy
 *
 * Used by:
 *   - scripts/scan-quran-story-connections.ts
 *   - scripts/build-quran-story-connection-graph.ts
 *   - frontend pages under /story-atlas/connections
 *
 * Hard rules (mirror docs/whole-quran-story-connection-reference-audit.md):
 *   - No Quran text is embedded in any record of these types — only
 *     surahNumber, ayahStart, ayahEnd references.
 *   - explicit_name and manual_seed detections MAY carry a high confidence,
 *     but `reviewStatus` of "verified" still requires explicit human review.
 *   - story_context, pronoun_context, and tafsir_context MUST be
 *     `needs_review` and humanReviewRequired = true.
 *   - Every connection/edge MUST carry at least one evidenceReferences entry.
 *   - Every sourceId referenced MUST exist in sourceRegistry.ts.
 */

// ---------------------------------------------------------------------------
// Entity taxonomy
// ---------------------------------------------------------------------------

export type QuranStoryEntityType =
  | 'prophet'
  | 'person'
  | 'people_or_nation'
  | 'place'
  | 'animal'
  | 'object'
  | 'event'
  | 'angel'
  | 'jinn'
  | 'title_or_role'
  | 'family_relation'
  | 'abstract_concept'
  | 'unknown';

export type DetectionType =
  | 'explicit_name'
  | 'alias_match'
  | 'story_context'
  | 'pronoun_context'
  | 'tafsir_context'
  | 'manual_seed';

export type ConnectionReviewStatus = 'verified' | 'needs_review' | 'rejected';

export interface QuranEntityReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  detectionType: DetectionType;
  /** 0 ≤ confidence ≤ 1. Inferred from detectionType + alias specificity. */
  confidence: number;
  /** sourceIds referenced for this detection (must exist in sourceRegistry). */
  sourceIds: string[];
  reviewStatus: ConnectionReviewStatus;
  humanReviewRequired: boolean;
  /** Optional matched surface token (Arabic). Never the full ayah text. */
  matchedAliasArabic?: string;
}

export interface QuranStoryEntity {
  entityId: string;
  type: QuranStoryEntityType;
  labelArabic: string;
  labelEnglish: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
  /** Common transliterations (Romanised). Used by entity search. */
  transliterations?: string[];
  quranReferences: QuranEntityReference[];
  relatedStories: string[];
  relatedEntities: string[];
  relatedThemes: string[];
  /** Chronology group ID — see quranStoryChronologySeeds.ts. */
  chronologicalGroup?: string;
  notesArabic?: string;
  notesEnglish?: string;
  warnings: string[];
  /**
   * Whether a human reviewer has approved this seed entry as production-safe.
   * Defaults to false. Approval gates verified display.
   */
  reviewedDictionary: boolean;
}

// ---------------------------------------------------------------------------
// Confidence helpers (pure — safe to import in client + scripts)
// ---------------------------------------------------------------------------

/** Confidence band for a given detection type. */
export const DETECTION_CONFIDENCE: Record<DetectionType, number> = {
  explicit_name: 0.95,
  alias_match: 0.7,
  story_context: 0.5,
  pronoun_context: 0.35,
  tafsir_context: 0.6,
  manual_seed: 0.85,
};

/** Initial review status for a given detection type. */
export const DETECTION_REVIEW_STATUS: Record<DetectionType, ConnectionReviewStatus> = {
  explicit_name: 'needs_review',
  alias_match: 'needs_review',
  story_context: 'needs_review',
  pronoun_context: 'needs_review',
  tafsir_context: 'needs_review',
  manual_seed: 'needs_review',
};

/** A detection always needs human review until a reviewer flips it. */
export function defaultHumanReviewRequired(_d: DetectionType): boolean {
  return true;
}

// ---------------------------------------------------------------------------
// Connection graph — node & edge types
// ---------------------------------------------------------------------------

export type ConnectionNodeType =
  | 'surah'
  | 'ayah_range'
  | 'story'
  | 'story_segment'
  | 'entity'
  | 'prophet'
  | 'person'
  | 'place'
  | 'animal'
  | 'object'
  | 'event'
  | 'theme'
  | 'chronology_group';

export type ConnectionEdgeType =
  | 'MENTIONED_IN'
  | 'APPEARS_IN_SURAH'
  | 'PART_OF_STORY'
  | 'SAME_ENTITY'
  | 'RELATED_ENTITY'
  | 'SAME_EVENT'
  | 'SAME_THEME'
  | 'SAME_PEOPLE'
  | 'SAME_PLACE'
  | 'SAME_ANIMAL_OR_OBJECT'
  | 'CHRONOLOGICALLY_BEFORE'
  | 'REVELATION_ORDER_BEFORE'
  | 'REPEATED_NARRATIVE'
  | 'CONTRASTED_WITH'
  | 'NEEDS_TAFSIR_REVIEW';

export type ConnectionEvidenceType =
  | 'quran_explicit'
  | 'dictionary_alias'
  | 'story_data'
  | 'kg_data'
  | 'tafsir_source'
  | 'manual_seed'
  | 'needs_review';

export interface ConnectionEvidenceReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  sourceIds: string[];
  evidenceType: ConnectionEvidenceType;
}

export interface ConnectionNode {
  id: string;
  type: ConnectionNodeType;
  labelArabic?: string;
  labelEnglish?: string;
  /** Free-form extra fields kept by node type (surahNumber, storyId, etc). */
  metadata?: Record<string, unknown>;
}

export interface ConnectionEdge {
  edgeId: string;
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: ConnectionEdgeType;
  evidenceReferences: ConnectionEvidenceReference[];
  confidence: number;
  reviewStatus: ConnectionReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

export interface ConnectionGraph {
  version: string;
  generatedAt: string;
  nodeCount: number;
  edgeCount: number;
  nodes: ConnectionNode[];
  edges: ConnectionEdge[];
}

// ---------------------------------------------------------------------------
// Chronology
// ---------------------------------------------------------------------------

export type ChronologyType = 'story_world' | 'revelation_order';
export type ChronologyCertainty = 'high' | 'medium' | 'low' | 'disputed';

export interface ChronologyEntry {
  chronologyType: ChronologyType;
  /** Refers to entityId (for story_world) or surahNumber-as-string (for revelation_order). */
  itemId: string;
  /** 1-based ordering inside the chronology group. */
  orderIndex?: number;
  certainty: ChronologyCertainty;
  sourceIds: string[];
  notesArabic?: string;
  notesEnglish?: string;
  reviewStatus: ConnectionReviewStatus;
}

// ---------------------------------------------------------------------------
// Scan output
// ---------------------------------------------------------------------------

export interface ScanSurahEntry {
  surahNumber: number;
  surahNameArabic?: string;
  surahNameEnglish?: string;
  /** entityIds detected in this surah. */
  detectedEntityIds: string[];
  /** Story-cluster candidates inferred from adjacent entity hits. */
  storyClusterCandidates: StoryClusterCandidate[];
  /** Mapped existing storyIds whose ayah ranges intersect this surah. */
  mappedStoryIds: string[];
  warnings: string[];
}

export interface EntitySurahIndexEntry {
  entityId: string;
  occurrences: Array<{
    surahNumber: number;
    ayahStart: number;
    ayahEnd?: number;
    detectionType: DetectionType;
    matchedAliasArabic?: string;
  }>;
}

export interface StoryClusterCandidate {
  candidateId: string;
  surahNumber: number;
  ayahStart: number;
  ayahEnd: number;
  entityIds: string[];
  /** Linked existing storyId if a story already covers this range. */
  linkedStoryId?: string;
  reviewStatus: ConnectionReviewStatus;
  warnings: string[];
}

export interface CrossSurahLink {
  entityId: string;
  surahNumbers: number[];
  occurrenceCount: number;
  /** "REPEATED_NARRATIVE" if both surahs already host a known story. */
  edgeType: ConnectionEdgeType;
  reviewStatus: ConnectionReviewStatus;
}

export interface ScanOutput {
  version: string;
  generatedAt: string;
  scannedSurahs: number;
  totalEntitiesDetected: number;
  entityTypeCounts: Partial<Record<QuranStoryEntityType, number>>;
  surahs: ScanSurahEntry[];
  entityIndex: EntitySurahIndexEntry[];
  crossSurahLinks: CrossSurahLink[];
  unmappedClusterCandidateIds: string[];
  warnings: string[];
}
