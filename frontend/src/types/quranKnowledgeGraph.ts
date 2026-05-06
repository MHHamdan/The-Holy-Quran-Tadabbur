/**
 * Quran Knowledge Graph — TypeScript type definitions.
 *
 * Nodes and edges are referenced by surah/ayah IDs only.
 * No Quran text is embedded here; text is fetched at runtime.
 */

// =============================================================================
// NODE TYPES
// =============================================================================

export type NodeType =
  | "ayah"
  | "surah"
  | "concept"
  | "theme"
  | "story"
  | "story_segment"
  | "person"
  | "source";

export interface AyahNode {
  id: string;           // "ayah:2:255"
  type: "ayah";
  surahNumber: number;
  ayahNumber: number;
  surahNameAr?: string;
  surahNameEn?: string;
  juzNo?: number;
  pageNo?: number;
}

export interface SurahNode {
  id: string;           // "surah:2"
  type: "surah";
  surahNumber: number;
  nameAr?: string;
  nameEn?: string;
  ayahCount?: number;
}

export interface ConceptNode {
  id: string;           // "concept:patience"
  type: "concept";
  slug: string;
  labelAr: string;
  labelEn: string;
  conceptCategory: ConceptCategory;
  iconHint?: string;
}

export interface ThemeNode {
  id: string;           // "theme:mercy"
  type: "theme";
  slug: string;
  labelAr: string;
  labelEn: string;
}

export interface StoryNode {
  id: string;           // "story:yusuf"
  type: "story";
  storyId: string;
  nameAr: string;
  nameEn: string;
  category: string;
  mainFigures: string[];
  themes: string[];
  surasmentioned: number[];
}

export interface StorySegmentNode {
  id: string;           // "story_segment:yusuf:01"
  type: "story_segment";
  segmentId: string;
  storyId: string;
  narrativeOrder: number;
  aspect: string;
  surahNumber: number;
  ayahStart: number;
  ayahEnd: number;
}

export interface PersonNode {
  id: string;           // "person:musa"
  type: "person";
  slug: string;
  labelAr: string;
  labelEn: string;
  personKind: "prophet" | "named" | "group" | "angel";
}

export interface SourceNode {
  id: string;           // "source:ibn-kathir"
  type: "source";
  sourceId: string;
  titleAr: string;
  titleEn: string;
  author?: string;
  reliabilityLevel?: string;
}

export type KGNode =
  | AyahNode
  | SurahNode
  | ConceptNode
  | ThemeNode
  | StoryNode
  | StorySegmentNode
  | PersonNode
  | SourceNode;

// =============================================================================
// EDGE TYPES
// =============================================================================

export type EdgeType =
  | "SAME_STORY"
  | "SAME_STORY_SEGMENT"
  | "SAME_PROPHET_OR_PERSON"
  | "SAME_THEME"
  | "SAME_CONCEPT"
  | "SAME_ROOT"
  | "SAME_LEMMA"
  | "SAME_SURAH"
  | "ADJACENT_AYAH"
  | "TAFSIR_SUPPORTS_RELATION"
  | "ASBAB_CONTEXT_RELATED"
  | "MUNASABAH_RELATED"
  | "CONTRASTS_WITH"
  | "PARALLEL_EVENT_PATTERN"
  | "SHARED_MORAL_LESSON"
  | "SEMANTICALLY_SIMILAR"
  | "TRANSLATION_SIMILARITY"
  | "SOURCE_CITES";

export type RelationStatus = "approved" | "needs_review" | "experimental";
export type GeneratedBy =
  | "rule"
  | "tafsir"
  | "story"
  | "semantic_embedding"
  | "manual_review";

export type ConceptCategory =
  | "theme"
  | "moral"
  | "miracle"
  | "rhetorical"
  | "historical"
  | "theological";

export interface EdgeEvidence {
  sourceId: string;
  surahNumber?: number;
  ayahNumber?: number;
  tafsirReference?: string;
  storyId?: string;
  segmentId?: string;
  explanationArabic?: string;
  explanationEnglish?: string;
}

export interface KGEdge {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: EdgeType;
  weight: number;                // 0–1
  evidence: EdgeEvidence[];
  relationStatus: RelationStatus;
  humanReviewRequired: boolean;
  generatedBy: GeneratedBy;
  warnings: string[];
}

// =============================================================================
// GRAPH STRUCTURES
// =============================================================================

export interface QuranKnowledgeGraph {
  version: string;
  generatedAt: string;
  nodeCount: number;
  edgeCount: number;
  nodes: KGNode[];
  edges: KGEdge[];
}

// =============================================================================
// SIMILARITY RESULT TYPES
// =============================================================================

export interface SimilarityEvidence {
  sourceId: string;
  sourceTitleArabic?: string;
  sourceTitleEnglish?: string;
  storyId?: string;
  conceptId?: string;
  themeId?: string;
  tafsirReference?: string;
  relationStatus: RelationStatus;
}

export interface PathExplanation {
  nodes: string[];
  edges: string[];
  explanationArabic?: string;
  explanationEnglish?: string;
}

export interface RelatedAyah {
  surahNumber: number;
  ayahNumber: number;
  score: number;
  relationTypes: EdgeType[];
  explanationArabic: string;
  explanationEnglish: string;
  evidence: SimilarityEvidence[];
  warnings: string[];
  humanReviewRequired: boolean;
  pathExplanation?: PathExplanation;
}

export interface AyahSimilarityResult {
  sourceAyah: {
    surahNumber: number;
    ayahNumber: number;
  };
  relatedAyahs: RelatedAyah[];
}

// =============================================================================
// PATH EXPLANATION
// =============================================================================

export interface PathStep {
  nodeId: string;
  nodeType: NodeType;
  label: string;
  edgeType?: EdgeType;
}

export interface AyahRelationPath {
  fromAyah: string;
  toAyah: string;
  steps: PathStep[];
  explanationEnglish: string;
  explanationArabic: string;
}

// =============================================================================
// GRAPH SUMMARY (generated output)
// =============================================================================

export interface KGNodeCounts {
  ayah: number;
  surah: number;
  concept: number;
  theme: number;
  story: number;
  story_segment: number;
  person: number;
  source: number;
}

export interface KGEdgeCounts {
  byType: Record<EdgeType, number>;
  byStatus: Record<RelationStatus, number>;
  byGenerator: Record<GeneratedBy, number>;
}

export interface KGSummary {
  version: string;
  generatedAt: string;
  nodeCounts: KGNodeCounts;
  edgeCounts: KGEdgeCounts;
  totalNodes: number;
  totalEdges: number;
  warnings: string[];
}
