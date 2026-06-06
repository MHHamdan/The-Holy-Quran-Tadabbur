/**
 * Quran Topic Discovery Atlas — type contracts for Phase V.
 *
 * Used by:
 *   - frontend/src/data/quranTopicSeeds.ts (seed taxonomy)
 *   - scripts/scan-quran-topic-links.ts
 *   - scripts/discover-quran-topic-clusters.ts
 *   - scripts/build-quran-topic-relation-graph.ts
 *   - scripts/validate-quran-topic-*.ts
 *   - backend Pydantic mirrors + API responses
 *   - frontend pages under /topics, /surah-topics
 *
 * Safety rules (mirror docs/quran-content-policy.md):
 *   - No Quran text is embedded in any record — only surah/ayah numbers.
 *   - Every record defaults to reviewStatus = "needs_review" and
 *     humanReviewRequired = true.
 *   - "verified" status is reserved for human reviewer sign-off; the
 *     pipeline never emits "verified" automatically.
 *   - Semantic/discovery-based links must carry source-availability warnings
 *     and remain needs_review.
 */

import type { QuranReference } from './quranEntityGraph';

// ============================================================================
// Topic taxonomy
// ============================================================================

export type QuranTopicType =
  | 'faith'
  | 'worship'
  | 'ethics'
  | 'story_theme'
  | 'legal_theme'
  | 'social_theme'
  | 'emotional_theme'
  | 'divine_attribute'
  | 'hereafter'
  | 'creation_sign'
  | 'warning'
  | 'promise'
  | 'command'
  | 'prohibition'
  | 'concept_cluster'
  | 'discovered_candidate';

export const TOPIC_TYPE_META: Record<QuranTopicType, { labelAr: string; labelEn: string }> = {
  faith: { labelAr: 'العقيدة والإيمان', labelEn: 'Faith & creed' },
  worship: { labelAr: 'العبادات', labelEn: 'Worship' },
  ethics: { labelAr: 'الأخلاق', labelEn: 'Ethics' },
  story_theme: { labelAr: 'مواضيع قصصية', labelEn: 'Story themes' },
  legal_theme: { labelAr: 'مواضيع تشريعية', labelEn: 'Legal themes' },
  social_theme: { labelAr: 'الحياة الاجتماعية', labelEn: 'Social life' },
  emotional_theme: { labelAr: 'وجدانية وروحية', labelEn: 'Emotional / spiritual' },
  divine_attribute: { labelAr: 'صفات الله', labelEn: 'Divine attributes' },
  hereafter: { labelAr: 'الآخرة', labelEn: 'Hereafter' },
  creation_sign: { labelAr: 'آيات الكون والخلق', labelEn: 'Creation & signs' },
  warning: { labelAr: 'الإنذارات', labelEn: 'Warnings' },
  promise: { labelAr: 'الوعود', labelEn: 'Promises' },
  command: { labelAr: 'الأوامر', labelEn: 'Commands' },
  prohibition: { labelAr: 'النواهي', labelEn: 'Prohibitions' },
  concept_cluster: { labelAr: 'مجموعة مفاهيم', labelEn: 'Concept cluster' },
  discovered_candidate: { labelAr: 'مرشّح مكتشف', labelEn: 'Discovered candidate' },
};

// ============================================================================
// Review status
// ============================================================================

export type TopicReviewStatus = 'verified' | 'needs_review' | 'rejected';

// ============================================================================
// Ayah-link types
// ============================================================================

export type QuranTopicLinkType =
  | 'explicit_keyword'
  | 'alias_match'
  | 'concept_match'
  | 'story_context'
  | 'entity_context'
  | 'coreference_context'
  | 'semantic_embedding'
  | 'graph_community'
  | 'tafsir_source'
  | 'manual_seed';

export const TOPIC_LINK_DEFAULT_CONFIDENCE: Record<QuranTopicLinkType, number> = {
  explicit_keyword: 0.85,
  alias_match: 0.7,
  concept_match: 0.65,
  story_context: 0.55,
  entity_context: 0.55,
  coreference_context: 0.5,
  semantic_embedding: 0.55,
  graph_community: 0.5,
  tafsir_source: 0.75,
  manual_seed: 0.8,
};

export type QuranTopicEvidenceType =
  | 'quran_keyword'
  | 'entity_graph'
  | 'story_data'
  | 'coreference'
  | 'kg_edge'
  | 'tafsir_source'
  | 'semantic_candidate'
  | 'manual_seed';

export interface QuranTopicEvidenceReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  sourceIds: string[];
  evidenceType: QuranTopicEvidenceType;
}

export interface QuranTopicAyahLink {
  surahNumber: number;
  ayahNumber: number;
  linkType: QuranTopicLinkType;
  confidence: number;
  evidenceReferences: QuranTopicEvidenceReference[];
  reviewStatus: TopicReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Topic
// ============================================================================

export interface QuranTopic {
  topicId: string;
  topicType: QuranTopicType;
  labelArabic: string;
  labelEnglish: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
  parentTopicId?: string;
  childTopicIds: string[];
  relatedTopicIds: string[];
  ayahLinks: QuranTopicAyahLink[];
  relatedEntities: string[];
  relatedStories: string[];
  relatedThemes: string[];
  relatedEmotions: string[];
  sourceIds: string[];
  reviewStatus: TopicReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Seed (input to the scanner)
// ============================================================================

export interface QuranTopicSeed {
  topicId: string;
  topicType: QuranTopicType;
  labelArabic: string;
  labelEnglish: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
  parentTopicId?: string;
  relatedEntities?: string[];
  relatedStories?: string[];
  relatedThemes?: string[];
  relatedEmotions?: string[];
  warnings?: string[];
}

// ============================================================================
// Discovered cluster
// ============================================================================

export type QuranTopicClusterMethod =
  | 'seed_taxonomy'
  | 'embedding_clustering'
  | 'graph_community'
  | 'entity_story_overlap'
  | 'tafsir_source'
  | 'manual_review';

export interface QuranTopicCluster {
  clusterId: string;
  labelArabic: string;
  labelEnglish: string;
  memberTopicIds: string[];
  ayahReferences: QuranReference[];
  generatedBy: QuranTopicClusterMethod;
  coherenceScore: number;
  reviewStatus: TopicReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ============================================================================
// Outputs
// ============================================================================

export interface QuranTopicAtlasOutput {
  version: string;
  generatedAt: string;
  totalTopics: number;
  totalAyahLinks: number;
  topicsByType: Partial<Record<QuranTopicType, number>>;
  ayahLinksByLinkType: Partial<Record<QuranTopicLinkType, number>>;
  topTopicsByCoverage: Array<{ topicId: string; ayahCount: number; surahCount: number }>;
  surahTopicDiversity: Array<{ surahNumber: number; uniqueTopics: number; ayahCount: number }>;
  ayahsWithMultipleTopics: number;
  ayahsWithoutTopics: number;
  topics: QuranTopic[];
  warnings: string[];
}

export interface QuranTopicClustersOutput {
  version: string;
  generatedAt: string;
  totalClusters: number;
  clustersByMethod: Partial<Record<QuranTopicClusterMethod, number>>;
  clusters: QuranTopicCluster[];
  warnings: string[];
}

// ============================================================================
// Relation graph
// ============================================================================

export type TopicNodeType =
  | 'topic'
  | 'ayah'
  | 'surah'
  | 'entity'
  | 'story'
  | 'emotion'
  | 'concept'
  | 'theme';

export type TopicEdgeType =
  | 'TOPIC_IN_AYAH'
  | 'TOPIC_IN_SURAH'
  | 'TOPIC_RELATED_TO_ENTITY'
  | 'TOPIC_RELATED_TO_STORY'
  | 'TOPIC_RELATED_TO_EMOTION'
  | 'TOPIC_RELATED_TO_TOPIC'
  | 'SHARED_AYAH'
  | 'SHARED_ENTITY'
  | 'SHARED_STORY'
  | 'SEMANTIC_CLUSTER'
  | 'TAFSIR_SUPPORTS_TOPIC'
  | 'NEEDS_REVIEW';

export interface TopicGraphNode {
  id: string;
  type: TopicNodeType;
  labelArabic?: string;
  labelEnglish?: string;
  metadata?: Record<string, unknown>;
}

export interface TopicGraphEdge {
  edgeId: string;
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: TopicEdgeType;
  evidenceReferences: QuranReference[];
  sourceIds: string[];
  confidence: number;
  reviewStatus: TopicReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

export interface QuranTopicRelationGraphOutput {
  version: string;
  generatedAt: string;
  nodeCount: number;
  edgeCount: number;
  nodesByType: Partial<Record<TopicNodeType, number>>;
  edgesByType: Partial<Record<TopicEdgeType, number>>;
  nodes: TopicGraphNode[];
  edges: TopicGraphEdge[];
  warnings: string[];
}

// ============================================================================
// Helpers
// ============================================================================

export function defaultTopicReviewStatus(_t: QuranTopicLinkType): TopicReviewStatus {
  return 'needs_review';
}

export function defaultTopicHumanReviewRequired(_t: QuranTopicLinkType): boolean {
  return true;
}
