import axios from 'axios';

// Use relative URL for Vite proxy, or absolute URL from env for production
const API_BASE = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Verse {
  id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  text_uthmani: string;
  text_imlaei: string;
  page_no: number;
  juz_no: number;
  translations: Translation[];
}

export interface Translation {
  language: string;
  translator: string;
  text: string;
}

// =============================================================================
// Search API Types
// =============================================================================

export interface SearchMatch {
  verse_id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  reference: string;
  text_uthmani: string;
  text_imlaei: string;
  page_no: number;
  juz_no: number;
  highlighted_text: string;
  context_before: string;
  context_after: string;
  relevance_score: number;
  tfidf_score: number;
  exact_match: boolean;
  word_role?: string;
  word_role_ar?: string;
  sentence_type?: string;
  sentence_type_ar?: string;
}

export interface EnhancedSearchResponse {
  query: string;
  query_normalized: string;
  total_matches: number;
  search_time_ms: number;
  matches: SearchMatch[];
  sura_distribution: Record<number, number>;
  juz_distribution: Record<number, number>;
  related_terms: string[];
}

export interface WordContextResponse {
  word: string;
  verse: Verse;
  surrounding_verses: Verse[];
  grammatical_analysis?: {
    word_role: string;
    word_role_ar: string;
    sentence_type: string;
    sentence_type_ar: string;
    morphology?: Record<string, unknown>;
  };
}

export interface SuraAnalytics {
  count: number;
  sura_name_ar: string;
  sura_name_en: string;
  percentage: number;
}

export interface WordAnalyticsResponse {
  word: string;
  word_normalized: string;
  total_occurrences: number;
  by_sura: Record<string, SuraAnalytics>;
  by_juz: Record<string, number>;
  top_verses: Array<{
    reference: string;
    text_uthmani: string;
    sura_name_ar: string;
  }>;
  co_occurring_words: Array<{
    word: string;
    count: number;
  }>;
}

export interface WordFrequencyItem {
  word: string;
  count: number;
  percentage: number;
}

export interface WordFrequencyResponse {
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  total_words: number;
  frequencies: WordFrequencyItem[];
}

export interface SearchCategoriesResponse {
  grammatical_roles: Record<string, string>;
  sentence_types: Record<string, string>;
}

// =============================================================================
// Semantic Search Types
// =============================================================================

export interface SemanticMatch {
  verse_id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  reference: string;
  text_uthmani: string;
  text_imlaei: string;
  semantic_score: number;
  shared_concepts: string[];
  themes: string[];
  connection_type: string;
}

export interface SimilarVersesResponse {
  source_verse: {
    reference: string;
    sura_name_ar: string;
    sura_name_en: string;
    text_uthmani: string;
  };
  similar_verses: SemanticMatch[];
  total_found: number;
}

export interface ThematicConnection {
  source_verse: string;
  target_verse: string;
  theme: string;
  theme_ar: string;
  similarity_score: number;
  shared_keywords: string[];
}

export interface ThematicConnectionsResponse {
  source_reference: string;
  connections: ThematicConnection[];
  total_connections: number;
}

export interface ConceptEvolutionResponse {
  concept: string;
  concept_normalized: string;
  total_occurrences: number;
  chronological_order: Array<{
    reference: string;
    sura_name_ar: string;
    sura_name_en: string;
    text_snippet: string;
    themes: string[];
    juz_no: number;
  }>;
  related_concepts: string[];
}

export interface ThemeInfo {
  id: string;
  name_en: string;
  name_ar: string;
}

export interface AvailableThemesResponse {
  themes: ThemeInfo[];
}

export interface Story {
  id: string;
  name_ar: string;
  name_en: string;
  category: string;
  main_figures: string[];
  themes: string[];
  summary_ar: string | null;
  summary_en: string | null;
  total_verses: number;
  suras_mentioned: number[];
}

export interface StorySegment {
  id: string;
  narrative_order: number;
  segment_type: string | null;
  aspect: string | null;
  sura_no: number;
  aya_start: number;
  aya_end: number;
  verse_reference: string;
  summary_ar: string | null;
  summary_en: string | null;
  semantic_tags?: string[];
  narrative_role?: string;
  is_entry_point?: boolean;
}

export interface StoryDetail extends Story {
  segments: StorySegment[];
}

export interface StoryGraphNode {
  id: string;
  type: string;
  label: string;
  data: Record<string, unknown>;
}

export interface StoryGraphEdge {
  source: string;
  target: string;
  type: string;
  label: string | null;
}

export interface StoryGraph {
  nodes: StoryGraphNode[];
  edges: StoryGraphEdge[];
}

export interface Citation {
  chunk_id: string;
  source_id: string;
  source_name: string;
  source_name_ar: string;
  verse_reference: string;
  excerpt: string;
  relevance_score: number;
}

export interface EvidenceChunk {
  chunk_id: string;
  source_id: string;
  source_name: string;
  source_name_ar: string;
  verse_reference: string;
  sura_no: number;
  aya_start: number;
  aya_end: number;
  content: string;
  content_ar: string | null;
  content_en: string | null;
  relevance_score: number;
  methodology: string | null;
}

// === NEW: Chat experience types ===
export interface RelatedVerse {
  sura_no: number;
  aya_no: number;
  verse_reference: string;
  text_ar: string;
  text_en: string;
  sura_name_ar?: string;
  sura_name_en?: string;
  topic?: string;
  relevance_score: number;
}

export interface TafsirExplanation {
  source_id: string;
  source_name: string;
  source_name_ar: string;
  author_name?: string;
  author_name_ar?: string;
  methodology?: string;
  explanation: string;
  verse_reference: string;
  era: string;
  reliability_score: number;
}

export interface RAGResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  scholarly_consensus: string | null;
  warnings: string[];
  related_queries: string[];
  intent: string;
  processing_time_ms: number;
  evidence: EvidenceChunk[];
  evidence_density?: {
    chunk_count: number;
    source_count: number;
  };
  cached?: boolean;  // Indicates if response came from cache
  // === NEW: Chat experience fields ===
  session_id?: string;  // Session ID for conversation continuity
  related_verses?: RelatedVerse[];  // Quranic verses displayed first
  tafsir_by_source?: Record<string, TafsirExplanation[]>;  // Tafsir grouped by source
  follow_up_suggestions?: string[];  // Suggested follow-up questions
}

// Chat session types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  verses_referenced?: string[];
}

export interface ChatSession {
  session_id: string;
  language: string;
  preferred_sources: string[];
  created_at: string;
  last_activity: string;
  message_count: number;
  messages: ChatMessage[];
}

export interface TafseerSource {
  id: string;
  name_ar: string;
  name_en: string;
  author_ar: string;
  author_en: string;
  methodology: string;
  era: string;
  language: string;
  reliability_score: number;
  is_primary_source: boolean;
  is_enabled: boolean;
}

export interface TafseerSourcesResponse {
  sources: TafseerSource[];
  count: number;
}

// API functions
export const quranApi = {
  getSuraVerses: (suraNo: number) =>
    api.get<Verse[]>(`/quran/suras/${suraNo}`),

  getVerse: (suraNo: number, ayaNo: number) =>
    api.get<Verse>(`/quran/verses/${suraNo}/${ayaNo}`),

  getVerseRange: (suraNo: number, ayaStart: number, ayaEnd: number) =>
    api.get<Verse[]>(`/quran/verses/${suraNo}/${ayaStart}/${ayaEnd}`),

  getPageVerses: (pageNo: number) =>
    api.get<Verse[]>(`/quran/page/${pageNo}`),

  getTafseer: (suraNo: number, ayaNo: number, sources?: string[]) =>
    api.get(`/quran/tafseer/${suraNo}/${ayaNo}`, { params: { sources } }),

  search: (query: string) =>
    api.get(`/quran/search`, { params: { q: query } }),

  // Enhanced Search API
  enhancedSearch: (word: string, params?: {
    limit?: number;
    offset?: number;
    sura?: number;
    juz?: number;
    include_semantic?: boolean;
    theme?: string;
  }) =>
    api.get<EnhancedSearchResponse>(`/quran/search/enhanced/${encodeURIComponent(word)}`, { params }),

  getWordContext: (word: string, suraNo: number, ayaNo: number, includeGrammar?: boolean) =>
    api.get<WordContextResponse>(`/quran/search/enhanced/${encodeURIComponent(word)}/context/${suraNo}/${ayaNo}`, {
      params: { include_grammar: includeGrammar }
    }),

  getWordAnalytics: (word: string) =>
    api.get<WordAnalyticsResponse>(`/quran/search/analytics/${encodeURIComponent(word)}`),

  searchPhrase: (phrase: string, params?: { exact?: boolean; limit?: number; offset?: number }) =>
    api.get<EnhancedSearchResponse>('/quran/search/phrase', {
      params: { phrase, ...params }
    }),

  getSuraWordFrequency: (suraNo: number, topN?: number) =>
    api.get<WordFrequencyResponse>(`/quran/search/sura/${suraNo}/frequency`, {
      params: { top_n: topN }
    }),

  getSearchCategories: () =>
    api.get<SearchCategoriesResponse>('/quran/search/categories'),

  // Semantic Search API
  findSimilarVerses: (suraNo: number, ayaNo: number, params?: {
    top_k?: number;
    theme_filter?: string;
    exclude_same_sura?: boolean;
  }) =>
    api.get<SimilarVersesResponse>(`/quran/semantic/similar/${suraNo}/${ayaNo}`, { params }),

  getThematicConnections: (suraNo: number, ayaNo: number, params?: {
    theme?: string;
    top_k?: number;
  }) =>
    api.get<ThematicConnectionsResponse>(`/quran/semantic/connections/${suraNo}/${ayaNo}`, { params }),

  getConceptEvolution: (concept: string, includeRelated?: boolean) =>
    api.get<ConceptEvolutionResponse>(`/quran/semantic/evolution/${encodeURIComponent(concept)}`, {
      params: { include_related: includeRelated }
    }),

  getAvailableThemes: () =>
    api.get<AvailableThemesResponse>('/quran/semantic/themes'),

  // Advanced Similarity Search
  getAdvancedSimilarity: (suraNo: number, ayaNo: number, params?: {
    top_k?: number;
    min_score?: number;
    theme?: string;
    exclude_same_sura?: boolean;
    connection_type?: string;
  }) =>
    api.get<AdvancedSimilarityResponse>(`/quran/similarity/advanced/${suraNo}/${ayaNo}`, { params }),

  getCrossSuraConnections: (suraNo: number, ayaNo: number, topK?: number) =>
    api.get(`/quran/similarity/cross-sura/${suraNo}/${ayaNo}`, { params: { top_k: topK } }),

  getVersesByTheme: (theme: string, limit?: number) =>
    api.get(`/quran/similarity/theme/${theme}`, { params: { limit } }),

  getConnectionTypes: () =>
    api.get('/quran/similarity/connection-types'),

  // Search History & Personalization
  recordSearch: (sessionId: string, data: {
    query: string;
    query_type?: string;
    result_count?: number;
    themes?: string[];
  }) =>
    api.post<{ status: string; session_id: string }>('/quran/history/search', data, {
      params: { session_id: sessionId }
    }),

  recordVerseClick: (sessionId: string, data: {
    sura_no: number;
    aya_no: number;
    context?: string;
  }) =>
    api.post<{ status: string; verse: string }>('/quran/history/click', data, {
      params: { session_id: sessionId }
    }),

  getSearchHistory: (sessionId: string, params?: {
    limit?: number;
    query_type?: string;
  }) =>
    api.get<SearchHistoryEntry[]>('/quran/history', {
      params: { session_id: sessionId, ...params }
    }),

  getSearchSuggestions: (sessionId: string, params?: {
    prefix?: string;
    limit?: number;
  }) =>
    api.get<SearchSuggestion[]>('/quran/history/suggestions', {
      params: { session_id: sessionId, ...params }
    }),

  getPersonalizedRecommendations: (sessionId: string, limit?: number) =>
    api.get<VerseRecommendation[]>('/quran/history/recommendations', {
      params: { session_id: sessionId, limit }
    }),

  getThemeInterests: (sessionId: string) =>
    api.get<{ session_id: string; interests: Record<string, number>; top_themes: [string, number][] }>('/quran/history/interests', {
      params: { session_id: sessionId }
    }),

  clearSearchHistory: (sessionId: string) =>
    api.delete<{ status: string; session_id: string }>('/quran/history', {
      params: { session_id: sessionId }
    }),

  getSearchStats: () =>
    api.get<SearchStats>('/quran/history/stats'),
};

// Advanced Similarity Types
export interface SimilarityScores {
  jaccard: number;
  cosine: number;
  concept_overlap: number;
  grammatical: number;
  semantic: number;
  root_based: number;
  combined: number;
}

export interface AdvancedSimilarityMatch {
  verse_id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  text_uthmani: string;
  text_imlaei: string;
  reference: string;
  scores: SimilarityScores;
  connection_type: string;
  connection_strength: string;
  shared_words: string[];
  shared_roots: string[];
  shared_concepts: string[];
  shared_themes: string[];
  primary_theme: string;
  primary_theme_ar: string;
  theme_color: string;
  sentence_structure: string;
  sentence_structure_ar: string;
  similarity_explanation_ar: string;
  similarity_explanation_en: string;
}

export interface AdvancedSimilarityResponse {
  source_verse: {
    verse_id: number;
    sura_no: number;
    sura_name_ar: string;
    sura_name_en: string;
    aya_no: number;
    text_uthmani: string;
    text_imlaei: string;
    reference: string;
  };
  source_themes: string[];
  source_structure: string;
  total_similar: number;
  matches: AdvancedSimilarityMatch[];
  theme_distribution: Record<string, number>;
  connection_type_distribution: Record<string, number>;
  search_time_ms: number;
  theme_colors: Record<string, string>;
  connection_types: { id: string; name_en: string; name_ar: string; color: string }[];
}

// Cross-story connection type
export interface CrossStoryConnection {
  id: number;
  source_story_id: string;
  target_story_id: string;
  connection_type: string;
  strength: number;
  label_en: string | null;
  label_ar: string | null;
  explanation_en: string | null;
  shared_themes: string[] | null;
  shared_figures: string[] | null;
}

export interface SimilarStory {
  id: string;
  title_ar: string;
  title_en: string;
  similarity_score: number;
  shared_concepts: string[];
  shared_themes: string[];
  shared_figures: string[];
}

export const storiesApi = {
  listStories: (category?: string) =>
    api.get<Story[]>('/stories/', { params: { category } }),

  getStory: (storyId: string) =>
    api.get<StoryDetail>(`/stories/${storyId}`),

  getStoryGraph: (storyId: string, language: 'ar' | 'en' = 'en') =>
    api.get<StoryGraph>(`/stories/${storyId}/graph`, { params: { language } }),

  getCategories: () =>
    api.get('/stories/categories'),

  getCrossConnections: (storyId: string) =>
    api.get<CrossStoryConnection[]>(`/stories/${storyId}/cross-connections`),

  getSimilarStories: (storyId: string, limit: number = 10) =>
    api.get<SimilarStory[]>(`/stories/${storyId}/similar`, { params: { limit } }),
};

// Story Atlas Types
export interface StoryCluster {
  id: string;
  title_ar: string;
  title_en: string;
  short_title_en: string | null;
  category: string;
  era: string | null;
  main_persons: string[];
  places: Record<string, unknown>[];
  tags: string[];
  event_count: number;
  primary_sura: number | null;
  summary_en: string | null;
}

export interface StoryClusterListResponse {
  clusters: StoryCluster[];
  total: number;
  offset: number;
  limit: number;
}

export interface StoryAtlasEvent {
  id: string;
  title_ar: string;
  title_en: string;
  narrative_role: string;
  chronological_index: number;
  sura_no: number;
  aya_start: number;
  aya_end: number;
  verse_reference: string;
  summary_ar: string;
  summary_en: string;
  semantic_tags: string[];
  is_entry_point: boolean;
  evidence: Record<string, unknown>[];
}

export interface StoryClusterDetail extends StoryCluster {
  short_title_ar: string | null;
  groups: string[];
  era_basis: string;
  time_description_en: string | null;
  ayah_spans: Record<string, unknown>[];
  suras_mentioned: number[] | null;
  summary_ar: string | null;
  lessons_ar: string[] | null;
  lessons_en: string[] | null;
  total_verses: number;
  events: StoryAtlasEvent[];
}

export interface AtlasGraphNode {
  id: string;
  type: string;
  label: string;
  data: Record<string, unknown>;
  position: { x: number; y: number } | null;
}

export interface AtlasGraphEdge {
  source: string;
  target: string;
  type: string;
  label: string | null;
  is_chronological: boolean;
  strength: number;
  data: Record<string, unknown>;
}

export interface AtlasGraphResponse {
  cluster_id: string;
  nodes: AtlasGraphNode[];
  edges: AtlasGraphEdge[];
  entry_node_id: string | null;
  is_valid_dag: boolean;
  layout_mode: string;
}

export interface RelatedCluster {
  cluster_id: string;
  title_en: string;
  title_ar: string;
  connection_type: string;
  strength: number;
  label_en: string | null;
  shared_persons: string[];
  shared_places: string[];
  shared_themes: string[];
}

export interface SimilarCluster {
  id: string;
  title_ar: string;
  title_en: string;
  similarity_score: number;
  shared_concepts: string[];
  shared_themes: string[];
  shared_figures: string[];
}

export const storyAtlasApi = {
  listClusters: (params?: { category?: string; era?: string; person?: string; tag?: string; search?: string; limit?: number; offset?: number }) =>
    api.get<StoryClusterListResponse>('/story-atlas', { params }),

  getCluster: (clusterId: string) =>
    api.get<StoryClusterDetail>(`/story-atlas/${clusterId}`),

  getClusterGraph: (clusterId: string, language: 'ar' | 'en' = 'en', mode: string = 'timeline') =>
    api.get<AtlasGraphResponse>(`/story-atlas/${clusterId}/graph`, { params: { language, mode } }),

  getTimeline: (clusterId: string, language: 'ar' | 'en' = 'en') =>
    api.get(`/story-atlas/${clusterId}/timeline`, { params: { language } }),

  getFacets: () =>
    api.get('/story-atlas/facets'),

  getCategories: () =>
    api.get('/story-atlas/categories'),

  getEras: () =>
    api.get('/story-atlas/eras'),

  getRelatedClusters: (clusterId: string) =>
    api.get<RelatedCluster[]>(`/story-atlas/${clusterId}/related`),

  getSimilarClusters: (clusterId: string, limit: number = 10) =>
    api.get<SimilarCluster[]>(`/story-atlas/${clusterId}/similar`, { params: { limit } }),
};

export const ragApi = {
  // Main ask endpoint with session support
  ask: (question: string, language: string = 'en', preferredSources: string[] = [], sessionId?: string) =>
    api.post<RAGResponse>('/rag/ask', {
      question,
      language,
      include_scholarly_debate: true,
      preferred_sources: preferredSources,
      session_id: sessionId,
    }),

  // Follow-up question within a session
  askFollowup: (sessionId: string, question: string, language: string = 'en') =>
    api.post<RAGResponse>('/rag/ask/followup', {
      session_id: sessionId,
      question,
      language,
    }),

  // Expand on a topic within a session
  expand: (sessionId: string, topic: string, language: string = 'en', verseReference?: string) =>
    api.post<RAGResponse>('/rag/ask/expand', {
      session_id: sessionId,
      topic,
      language,
      verse_reference: verseReference,
    }),

  // Get session history
  getSession: (sessionId: string) =>
    api.get<{ ok: boolean; session: ChatSession }>(`/rag/sessions/${sessionId}`),

  // Delete a session
  deleteSession: (sessionId: string) =>
    api.delete(`/rag/sessions/${sessionId}`),

  getIntents: () =>
    api.get('/rag/intents'),

  getSampleQuestions: (language: string = 'en') =>
    api.get('/rag/sample-questions', { params: { language } }),

  getSources: (language?: string) =>
    api.get<TafseerSourcesResponse>('/rag/sources', { params: { language } }),

  // Auto-suggestions for search box
  getSuggestions: (query: string, language: string = 'en', limit: number = 8) =>
    api.get<{
      ok: boolean;
      query: string;
      suggestions: Array<{ text: string; type: string; concept_type?: string }>;
      count: number;
    }>('/rag/suggestions', { params: { q: query, language, limit } }),

  // Admin endpoints (use X-Admin-Token header for security)
  toggleSource: (sourceId: string, isEnabled: boolean, adminToken: string) =>
    api.put(`/rag/admin/sources/${sourceId}/toggle`, { is_enabled: isEnabled }, {
      headers: { 'X-Admin-Token': adminToken }
    }),

  getAdminSources: (adminToken: string) =>
    api.get<TafseerSourcesResponse>('/rag/admin/sources', {
      headers: { 'X-Admin-Token': adminToken }
    }),
};

// Concept Graph Types
export interface ConceptSummary {
  id: string;
  slug: string;
  label_ar: string;
  label_en: string;
  type: string;
  icon_hint: string | null;
  is_curated: boolean;
  occurrence_count: number;
}

export interface ConceptListResponse {
  concepts: ConceptSummary[];
  total: number;
  offset: number;
  limit: number;
}

export interface ConceptDetail {
  id: string;
  slug: string;
  label_ar: string;
  label_en: string;
  type: string;
  aliases_ar: string[];
  aliases_en: string[];
  description_ar: string | null;
  description_en: string | null;
  parent_id: string | null;
  icon_hint: string | null;
  is_curated: boolean;
  source: string | null;
}

export interface ConceptOccurrence {
  id: number;
  concept_id: string;
  ref_type: string;
  ref_id: string | null;
  sura_no: number | null;
  ayah_start: number | null;
  ayah_end: number | null;
  page_no: number | null;  // Mushaf page number for page-level navigation
  verse_reference: string;
  weight: number;
  context_ar: string | null;
  context_en: string | null;
  has_evidence: boolean;
  is_verified: boolean;
}

export interface OccurrenceListResponse {
  occurrences: ConceptOccurrence[];
  total: number;
  offset: number;
  limit: number;
}

export interface ConceptAssociation {
  id: number;
  concept_a_id: string;
  concept_b_id: string;
  other_concept_id: string;
  other_concept_label_ar: string;
  other_concept_label_en: string;
  other_concept_type: string;
  relation_type: string;
  relation_label_ar: string;
  relation_label_en: string;
  is_directional: boolean;
  strength: number;
  explanation_ar: string | null;
  explanation_en: string | null;
  has_sufficient_evidence: boolean;
}

export interface ConceptTypeFacet {
  type: string;
  label_ar: string;
  label_en: string;
  count: number;
}

export interface MiracleWithAssociations {
  id: string;
  slug: string;
  label_ar: string;
  label_en: string;
  description_ar: string | null;
  description_en: string | null;
  icon_hint: string | null;
  related_persons: ConceptSummary[];
  related_stories: string[];
  occurrence_count: number;
}

// Grammar (إعراب) Types
export interface GrammarToken {
  word: string;
  word_index: number;
  pos: string;           // Part of speech in Arabic
  role: string;          // Grammatical role in Arabic
  case_ending: string | null;
  i3rab: string;         // Full إعراب explanation
  root: string | null;
  pattern: string | null;
  confidence: number;
  notes_ar: string;
}

export interface GrammarAnalysis {
  verse_reference: string;
  text: string;
  sentence_type: string;  // جملة اسمية، جملة فعلية، شبه جملة
  tokens: GrammarToken[];
  notes_ar: string;
  overall_confidence: number;
  source: string;         // "corpus", "llm", "hybrid", "fallback"
}

export interface GrammarLabels {
  pos_tags: string[];
  roles: string[];
  sentence_types: string[];
  case_endings: string[];
}

export interface GrammarHealth {
  status: string;
  ollama_available: boolean;
  model: string;
  message_ar: string;
  message_en: string;
}

export const conceptsApi = {
  listConcepts: (params?: { type?: string; search?: string; curated_only?: boolean; limit?: number; offset?: number }) =>
    api.get<ConceptListResponse>('/concepts', { params }),

  getConceptTypes: () =>
    api.get<ConceptTypeFacet[]>('/concepts/types'),

  searchConcepts: (q: string, limit: number = 20) =>
    api.get<ConceptSummary[]>('/concepts/search', { params: { q, limit } }),

  getConceptsByStory: (storyId: string) =>
    api.get<ConceptSummary[]>(`/concepts/by-story/${storyId}`),

  getConcept: (conceptId: string) =>
    api.get<ConceptDetail>(`/concepts/${conceptId}`),

  getConceptOccurrences: (conceptId: string, params?: { ref_type?: string; limit?: number; offset?: number }) =>
    api.get<OccurrenceListResponse>(`/concepts/${conceptId}/occurrences`, { params }),

  getConceptAssociations: (conceptId: string, params?: { relation_type?: string; limit?: number }) =>
    api.get<ConceptAssociation[]>(`/concepts/${conceptId}/associations`, { params }),

  getAllMiracles: () =>
    api.get<MiracleWithAssociations[]>('/concepts/miracles/all'),
};

// Grammar (إعراب) API
export const grammarApi = {
  analyzeText: (text: string, verseReference?: string) =>
    api.post<GrammarAnalysis>('/grammar/analyze', {
      text,
      verse_reference: verseReference,
    }),

  analyzeAyah: (suraAyah: string) =>
    api.get<GrammarAnalysis>(`/grammar/ayah/${suraAyah}`),

  getLabels: () =>
    api.get<GrammarLabels>('/grammar/labels'),

  health: () =>
    api.get<GrammarHealth>('/grammar/health'),
};

// =============================================================================
// Knowledge Graph API Types
// =============================================================================

export interface KGClusterResponse {
  cluster: {
    id: string;
    slug: string;
    title: string;
    short_title: string;
    category: string;
    era: string | null;
    main_persons: string[];
    summary: string;
    lessons: string[];
    ayah_spans: Array<{ sura: number; start: number; end: number }>;
    total_verses: number | null;
    is_complete: boolean;
    event_count: number;
  };
  events: KGEventSummary[];
  timeline: KGTimelineEdge[];
}

export interface KGEventSummary {
  id: string;
  index: number;
  title: string;
  narrative_role: string;
  verse_reference: string;
  summary: string;
  memorization_cue: string;
  semantic_tags: string[];
  is_entry_point: boolean;
}

export interface KGTimelineEdge {
  source: string;
  target: string;
  gap_type: string;
}

export interface KGGraphNode {
  id: string;
  type: string;
  label: string;
  data: Record<string, unknown>;
  position: { x: number; y: number } | null;
}

export interface KGGraphEdge {
  source: string;
  target: string;
  type: string;
  label: string | null;
  data: Record<string, unknown>;
}

export interface KGStoryGraphResponse {
  cluster_id: string;
  nodes: KGGraphNode[];
  edges: KGGraphEdge[];
  entry_node_id: string | null;
  is_valid_dag: boolean;
  layout_mode: string;
}

export interface KGTimelineEvent {
  id: string;
  index: number;
  title_ar: string;
  title_en: string;
  verse_reference: string;
  narrative_role: string;
  summary_ar: string;
  summary_en: string;
  semantic_tags: string[];
  is_entry_point: boolean;
  memorization_cue_ar: string | null;
  memorization_cue_en: string | null;
}

export interface KGTimelineResponse {
  cluster_id: string;
  title_ar: string;
  title_en: string;
  events: KGTimelineEvent[];
}

export interface KGSearchResults {
  clusters: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
  persons: Array<Record<string, unknown>>;
  concepts: Array<Record<string, unknown>>;
}

export interface KGHealthResponse {
  status: string;
  surreal_host: string;
  surreal_port: number;
  namespace: string;
  database: string;
  message_ar: string;
  message_en: string;
}

export interface KGEvidenceDebug {
  input_chunk_ids: string[];
  vector_hits: Array<Record<string, unknown>>;
  graph_expanded_ids: string[];
  evidence_count: number;
  evidence: Array<Record<string, unknown>>;
  debug_info: Record<string, unknown>;
}

// =============================================================================
// Knowledge Graph API
// =============================================================================

export const kgApi = {
  /**
   * Get story cluster with events and timeline.
   * Returns localized content based on lang parameter.
   */
  getStoryCluster: (clusterId: string, lang: 'ar' | 'en' = 'ar') =>
    api.get<KGClusterResponse>(`/kg/story/${clusterId}`, { params: { lang } }),

  /**
   * Get story as graph nodes and edges for visualization.
   * Modes: 'timeline' (chronological) or 'concept' (includes thematic links)
   */
  getStoryGraph: (clusterId: string, mode: 'timeline' | 'concept' = 'timeline', lang: 'ar' | 'en' = 'ar') =>
    api.get<KGStoryGraphResponse>(`/kg/story/${clusterId}/graph`, { params: { mode, lang } }),

  /**
   * Get linear timeline of story events.
   */
  getStoryTimeline: (clusterId: string, lang: 'ar' | 'en' = 'ar') =>
    api.get<KGTimelineResponse>(`/kg/story/${clusterId}/timeline`, { params: { lang } }),

  /**
   * Hybrid search across clusters, events, persons, and concepts.
   */
  search: (query: string, lang: 'ar' | 'en' = 'ar', limit: number = 10) =>
    api.get<KGSearchResults>('/kg/search', { params: { q: query, lang, limit } }),

  /**
   * Debug endpoint showing full evidence trace.
   * For troubleshooting RAG responses.
   */
  debugEvidence: (chunkIds: string[]) =>
    api.get<KGEvidenceDebug>('/kg/debug/evidence', { params: { chunk_ids: chunkIds.join(',') } }),

  /**
   * Check Knowledge Graph health (SurrealDB availability).
   */
  health: () =>
    api.get<KGHealthResponse>('/kg/health'),

  /**
   * Initialize Knowledge Graph schema.
   * Should be called once during setup.
   */
  initSchema: () =>
    api.post<{ status: string; message_ar: string; message_en: string }>('/kg/init-schema'),
};

// =============================================================================
// Search History & Personalization Types
// =============================================================================

export interface SearchHistoryEntry {
  query: string;
  query_type: string;
  timestamp: string;
  result_count: number;
  clicked_verses: string[];
}

export interface SearchSuggestion {
  query: string;
  query_type: string;
  frequency: number;
  relevance_score: number;
}

export interface VerseRecommendation {
  sura_no: number;
  aya_no: number;
  reference: string;
  text_uthmani: string;
  sura_name_ar: string;
  sura_name_en: string;
  reason: string;
  reason_ar: string;
  confidence: number;
}

export interface SearchStats {
  active_sessions: number;
  total_searches: number;
  unique_queries: number;
  total_verse_clicks: number;
  top_searches: [string, number][];
  top_clicked_verses: [string, number][];
}

// =============================================================================
// Graph Explorer Types
// =============================================================================

export interface GraphSearchHit {
  id: string;
  type: 'theme' | 'story' | 'person' | 'event';
  title: string;
  title_ar: string;
  content: string;
  content_ar: string;
  score: number;
  confidence: number;
  verse_reference?: string | null;
  metadata: Record<string, unknown>;
  highlights?: string[];
}

export interface SemanticSearchResponse {
  ok: boolean;
  query: string;
  expanded_query: string;
  intent: string;
  hits: GraphSearchHit[];
  total_found: number;
  related_concepts: Array<{
    id: string;
    label_ar: string;
    label_en: string;
    type: string;
    relevance: number;
  }>;
  suggested_queries: string[];
  search_time_ms: number;
}

export interface GraphStatsResponse {
  ok: boolean;
  node_counts: Record<string, number>;
  edge_counts: Record<string, number>;
  total_nodes: number;
  total_edges: number;
  most_connected: Array<{
    id: string;
    title_en: string;
    title_ar: string;
    type: string;
    connection_count: number;
  }>;
}

export interface EntityTypeInfo {
  key: string;
  label_en: string;
  label_ar: string;
  description_en?: string;
  description_ar?: string;
  icon: string;
}

export interface GraphOverviewResponse {
  ok: boolean;
  stats: Record<string, number>;
  entity_types: EntityTypeInfo[];
  sample_entities: {
    stories: Array<Record<string, unknown>>;
    concepts: Array<Record<string, unknown>>;
    persons: Array<Record<string, unknown>>;
  };
}

export interface GraphExplorationNode {
  id: string;
  type: string;
  label: string;
  label_ar: string;
  depth: number;
  weight: number;
  data: Record<string, unknown>;
}

export interface GraphExplorationEdge {
  source: string;
  target: string;
  type: string;
  label: string;
  weight: number;
}

export interface GraphExplorationResponse {
  ok: boolean;
  nodes: GraphExplorationNode[];
  edges: GraphExplorationEdge[];
  center_node?: string;
  max_depth: number;
  total_nodes: number;
  total_edges: number;
}

export interface EntityDetailsResponse {
  ok: boolean;
  entity: Record<string, unknown>;
  relationships: {
    outgoing: Array<{
      type: string;
      target_id: string;
      target_data: Record<string, unknown>;
    }>;
    incoming: Array<{
      type: string;
      source_id: string;
      source_data: Record<string, unknown>;
    }>;
  };
}

// =============================================================================
// Graph Explorer API
// =============================================================================

export const graphApi = {
  /**
   * Semantic search across stories, themes, and persons.
   */
  semanticSearch: (query: string, options?: {
    lang?: 'ar' | 'en';
    intent?: string;
    expand?: boolean;
    limit?: number;
    min_confidence?: number;
  }) =>
    api.get<SemanticSearchResponse>('/graph/search/semantic', {
      params: { q: query, ...options }
    }),

  /**
   * Get search intents for UI display.
   */
  getSearchIntents: () =>
    api.get<{
      ok: boolean;
      intents: Array<{ value: string; label_en: string; label_ar: string }>;
    }>('/graph/search/intents'),

  /**
   * Get graph statistics.
   */
  getStats: () =>
    api.get<GraphStatsResponse>('/graph/stats'),

  /**
   * Get available entity types.
   */
  getEntityTypes: () =>
    api.get<{ ok: boolean; types: EntityTypeInfo[] }>('/graph/entity-types'),

  /**
   * Get graph overview with stats, types, and sample entities.
   */
  getOverview: () =>
    api.get<GraphOverviewResponse>('/graph/overview'),

  /**
   * Get entity details with relationships.
   */
  getEntity: (entityId: string) =>
    api.get<EntityDetailsResponse>(`/graph/entity/${encodeURIComponent(entityId)}`),

  /**
   * BFS exploration from a starting node.
   */
  exploreBFS: (startId: string, options?: {
    depth?: number;
    edge_types?: string[];
    limit?: number;
  }) =>
    api.get<GraphExplorationResponse>('/graph/explore/bfs', {
      params: { start_id: startId, ...options }
    }),

  /**
   * DFS exploration from a starting node.
   */
  exploreDFS: (startId: string, options?: {
    depth?: number;
    edge_types?: string[];
    limit?: number;
  }) =>
    api.get<GraphExplorationResponse>('/graph/explore/dfs', {
      params: { start_id: startId, ...options }
    }),

  /**
   * Get thematic journey connecting themes.
   */
  getThematicJourney: (theme: string, options?: {
    lang?: 'ar' | 'en';
    limit?: number;
  }) =>
    api.get<{
      ok: boolean;
      theme: string;
      stops: Array<{
        type: string;
        id: string;
        title_ar: string;
        title_en: string;
        description: string;
      }>;
    }>('/graph/thematic/journey', {
      params: { theme, ...options }
    }),

  /**
   * Get related entities for a given entity.
   */
  getRelated: (entityId: string, options?: {
    limit?: number;
    edge_types?: string[];
  }) =>
    api.get<GraphExplorationResponse>('/graph/related', {
      params: { entity_id: entityId, ...options }
    }),
};

// =============================================================================
// Audio Recitation Types
// =============================================================================

export interface ReciterInfo {
  id: string;
  name_ar: string;
  name_en: string;
  style: string;
}

export interface SurahAudioResponse {
  ok: boolean;
  sura_no: number;
  reciter: string;
  audio_url: string;
  type: 'surah';
}

export interface VerseAudioResponse {
  ok: boolean;
  sura_no: number;
  aya_no: number;
  reference: string;
  reciter: string;
  audio_url: string;
  fallback_url?: string;  // Alternative source if primary fails
  type: 'verse';
}

export interface VerseAudioInfo {
  sura_no: number;
  aya_no: number;
  reference: string;
  url: string;
  fallback_url?: string;  // Primary fallback URL
  fallback_urls?: string[];  // Array of additional fallback URLs for high availability
}

export interface RangeAudioResponse {
  ok: boolean;
  sura_no: number;
  aya_start: number;
  aya_end: number;
  reciter: string;
  verse_audios: VerseAudioInfo[];
  total_verses: number;
  type: 'range';
}

export interface PageAudioResponse {
  ok: boolean;
  page_no: number;
  reciter: string;
  verse_audios: VerseAudioInfo[];
  total_verses: number;
  type: 'page';
}

// =============================================================================
// Audio API
// =============================================================================

export const audioApi = {
  /**
   * Get list of available reciters.
   */
  getReciters: () =>
    api.get<{ ok: boolean; reciters: ReciterInfo[] }>('/quran/audio/reciters'),

  /**
   * Get audio URL for a complete Surah.
   */
  getSurahAudio: (suraNo: number, reciter?: string) =>
    api.get<SurahAudioResponse>(`/quran/audio/surah/${suraNo}`, {
      params: reciter ? { reciter } : undefined
    }),

  /**
   * Get audio URL for a single verse.
   */
  getVerseAudio: (suraNo: number, ayaNo: number, reciter?: string) =>
    api.get<VerseAudioResponse>(`/quran/audio/verse/${suraNo}/${ayaNo}`, {
      params: reciter ? { reciter } : undefined
    }),

  /**
   * Get audio URLs for a range of verses.
   */
  getRangeAudio: (suraNo: number, ayaStart: number, ayaEnd: number, reciter?: string) =>
    api.get<RangeAudioResponse>(`/quran/audio/range/${suraNo}/${ayaStart}/${ayaEnd}`, {
      params: reciter ? { reciter } : undefined
    }),

  /**
   * Get audio URLs for all verses on a Mushaf page.
   */
  getPageAudio: (pageNo: number, reciter?: string) =>
    api.get<PageAudioResponse>(`/quran/audio/page/${pageNo}`, {
      params: reciter ? { reciter } : undefined
    }),
};


// =============================================================================
// Concept Highlights API
// =============================================================================

export interface ConceptHighlight {
  sura_no: number;
  aya_no: number;
  reference: string;
  weight: number;
}

export interface ConceptHighlightsResponse {
  ok: boolean;
  concept_id: string;
  highlights: ConceptHighlight[];
  total: number;
}

export const conceptHighlightsApi = {
  /**
   * Get verse highlights for a specific concept.
   * Useful for highlighting concept-related verses in the Quran reader.
   */
  getConceptHighlights: (
    conceptId: string,
    options?: { pageNo?: number; suraNo?: number }
  ) =>
    api.get<ConceptHighlightsResponse>(`/quran/highlights/concept/${conceptId}`, {
      params: {
        page_no: options?.pageNo,
        sura_no: options?.suraNo,
      }
    }),
};


// =============================================================================
// Multi-Concept Search API
// =============================================================================

export interface MultiConceptHighlight {
  sura_no: number;
  aya_no: number;
  reference: string;
  weight: number;
  matched_concepts: string[];
  is_primary_match: boolean;
}

export interface MultiConceptHighlightsResponse {
  ok: boolean;
  concept_ids: string[];
  expanded_concepts: string[];
  expansion_info: Record<string, Array<{
    id: string;
    relation: string;
    strength: number;
  }>>;
  highlights: MultiConceptHighlight[];
  total: number;
  stats: {
    primary_matches: number;
    expanded_matches: number;
    multi_concept_matches: number;
  };
}

export interface ConceptExpansionResult {
  concept: {
    id: string;
    slug: string;
    label: string;
    label_ar: string;
    label_en: string;
    type: string;
  };
  aliases: {
    ar: string[];
    en: string[];
  };
  related_concepts: Array<{
    id: string;
    label_ar: string;
    label_en: string;
    relation_type: string;
    strength: number;
  }>;
  suggested_query: string;
}

export interface ConceptExpansionResponse {
  ok: boolean;
  query: string;
  matched_concepts: ConceptExpansionResult[];
  total: number;
  cross_language_expansion: {
    source_language: string;
    arabic_terms: string[];
    english_terms: string[];
    detected_themes: string[];
    life_lessons: string[];
  };
}

// Multi-Concept Natural Language Search Types
export interface MultiConceptMatch {
  verse_id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  text_uthmani: string;
  text_imlaei: string;
  page_no: number;
  juz_no: number;
  reference: string;
  highlighted_text: string;
  relevance_score: number;
  matched_concepts: Array<{
    concept: string;
    matched_terms: string[];
    positions: Array<[number, number]>;
  }>;
}

export interface MultiConceptSearchResponse {
  ok: boolean;
  parsed_query: {
    original: string;
    concepts: string[];
    connector_type: 'and' | 'or';
    is_multi_concept: boolean;
    language: 'ar' | 'en' | 'mixed';
  };
  total_matches: number;
  matches: MultiConceptMatch[];
  concept_distribution: Record<string, number>;
  concept_expansions: Record<string, string[]>;
  search_time_ms: number;
}

export interface ConceptSuggestion {
  key: string;
  ar: string[];
  en: string[];
  related: string[];
  match_score: number;
}

export interface ConceptSuggestionsResponse {
  ok: boolean;
  query: string;
  suggestions: ConceptSuggestion[];
  count: number;
}

export interface AvailableConceptsResponse {
  ok: boolean;
  total_concepts: number;
  categories: {
    prophets: Array<{
      key: string;
      ar: string[];
      en: string[];
      related: string[];
    }>;
    virtues: Array<{
      key: string;
      ar: string[];
      en: string[];
      related: string[];
    }>;
    places_events: Array<{
      key: string;
      ar: string[];
      en: string[];
      related: string[];
    }>;
  };
}

export const multiConceptApi = {
  /**
   * Get verse highlights for multiple concepts with query expansion.
   * Supports "Suleiman + Queen of Sheba" style queries.
   */
  getMultiConceptHighlights: (
    conceptIds: string[],
    options?: {
      pageNo?: number;
      suraNo?: number;
      expandRelated?: boolean;
      includeAliases?: boolean;
    }
  ) =>
    api.get<MultiConceptHighlightsResponse>('/quran/highlights/concepts/multi', {
      params: {
        concept_ids: conceptIds.join(','),
        page_no: options?.pageNo,
        sura_no: options?.suraNo,
        expand_related: options?.expandRelated ?? true,
        include_aliases: options?.includeAliases ?? true,
      }
    }),

  /**
   * Expand a search query to related concepts.
   * Given "patience" or "صبر", returns matching concepts and related ones.
   */
  expandConceptQuery: (
    query: string,
    options?: {
      maxConcepts?: number;
      includeAliases?: boolean;
    }
  ) =>
    api.get<ConceptExpansionResponse>('/quran/search/concepts/expand', {
      params: {
        query,
        max_concepts: options?.maxConcepts ?? 10,
        include_aliases: options?.includeAliases ?? true,
      }
    }),

  /**
   * Multi-concept search for Quran verses.
   * Parses queries like "Solomon and Queen of Sheba" to find verses
   * mentioning either or both concepts.
   *
   * Arabic: البحث متعدد المفاهيم في آيات القرآن
   */
  searchMultiConcept: (
    query: string,
    options?: {
      limit?: number;
      offset?: number;
      suraNo?: number;
      connector?: 'and' | 'or';
    }
  ) =>
    api.get<MultiConceptSearchResponse>('/quran/search/multi-concept', {
      params: {
        query,
        limit: options?.limit ?? 50,
        offset: options?.offset ?? 0,
        sura_no: options?.suraNo,
        connector: options?.connector ?? 'or',
      }
    }),

  /**
   * Get auto-suggestions for concept search.
   * Returns matching concepts with Arabic and English forms.
   *
   * Arabic: الحصول على اقتراحات البحث عن المفاهيم
   */
  getConceptSuggestions: (query: string, limit?: number) =>
    api.get<ConceptSuggestionsResponse>('/quran/search/concept-suggestions', {
      params: {
        query,
        limit: limit ?? 10,
      }
    }),

  /**
   * List all available concepts for multi-concept search.
   * Grouped by category (prophets, virtues, places).
   *
   * Arabic: قائمة المفاهيم المتاحة للبحث
   */
  listAvailableConcepts: () =>
    api.get<AvailableConceptsResponse>('/quran/search/concepts/list'),
};


// =============================================================================
// Semantic Verse Search API (Qdrant Vector Search)
// =============================================================================

export interface SemanticSearchResult {
  verse_id: number;
  sura_no: number;
  aya_no: number;
  reference: string;
  text_uthmani: string;
  text_imlaei: string;
  similarity_score: number;
  matched_themes: string[];
}

export interface SemanticSearchResponse {
  ok: boolean;
  query: string;
  results: SemanticSearchResult[];
  total: number;
  index_status: 'indexed' | 'not_indexed';
  vectors_count?: number;
  message?: string;
  cross_language_expansion?: {
    source_language: string;
    arabic_terms: string[];
    english_terms: string[];
    detected_concepts: string[];
  };
}

export interface SemanticSimilarVersesResponse {
  ok: boolean;
  source_verse: string;
  similar_verses: SemanticSearchResult[];
  total: number;
  index_status: 'indexed' | 'not_indexed';
}

export interface SemanticSearchStats {
  ok: boolean;
  collection: string;
  stats: {
    exists: boolean;
    vectors_count?: number;
    points_count?: number;
    segments_count?: number;
    status?: string;
  };
  model: string;
  embedding_dimension: number;
}

export const semanticSearchApi = {
  /**
   * Semantic search for Quran verses using vector embeddings.
   * Supports Arabic and English queries for cross-language matching.
   */
  search: (
    query: string,
    options?: {
      limit?: number;
      minScore?: number;
      suraNo?: number;
      juzNo?: number;
      includeCrossLanguage?: boolean;
    }
  ) =>
    api.get<SemanticSearchResponse>('/quran/search/semantic', {
      params: {
        query,
        limit: options?.limit ?? 20,
        min_score: options?.minScore ?? 0.3,
        sura_no: options?.suraNo,
        juz_no: options?.juzNo,
        include_cross_language: options?.includeCrossLanguage ?? true,
      }
    }),

  /**
   * Find verses semantically similar to a specific verse.
   */
  findSimilar: (
    suraNo: number,
    ayaNo: number,
    options?: {
      limit?: number;
      minScore?: number;
      excludeSameSura?: boolean;
    }
  ) =>
    api.get<SimilarVersesResponse>(`/quran/search/similar/${suraNo}/${ayaNo}`, {
      params: {
        limit: options?.limit ?? 10,
        min_score: options?.minScore ?? 0.5,
        exclude_same_sura: options?.excludeSameSura ?? false,
      }
    }),

  /**
   * Get semantic search index statistics.
   */
  getStats: () =>
    api.get<SemanticSearchStats>('/quran/search/semantic/stats'),

  /**
   * Index verses for semantic search (admin).
   */
  indexVerses: (batchSize: number = 100) =>
    api.post<{ ok: boolean; indexed_count: number; total_verses: number }>(
      '/quran/search/semantic/index',
      null,
      { params: { batch_size: batchSize } }
    ),
};

// =============================================================================
// Quranic Themes API (المحاور القرآنية)
// =============================================================================

export interface QuranicTheme {
  id: string;
  slug: string;
  title_ar: string;
  title_en: string;
  short_title_ar: string | null;
  short_title_en: string | null;
  category: string;
  category_label_ar: string;
  category_label_en: string;
  order_of_importance: number;
  key_concepts: string[];
  segment_count: number;
  total_verses: number;
  has_consequences: boolean;
  parent_id: string | null;
}

export interface ThemeCategory {
  category: string;
  label_ar: string;
  label_en: string;
  theme_count: number;
  order: number;
}

export interface ThemeSegment {
  id: string;
  segment_order: number;
  chronological_index: number | null;
  sura_no: number;
  ayah_start: number;
  ayah_end: number;
  verse_reference: string;
  title_ar: string | null;
  title_en: string | null;
  summary_ar: string;
  summary_en: string;
  semantic_tags: string[];
  revelation_context: string | null;
  is_entry_point: boolean;
  is_verified: boolean;
  importance_weight: number;
  evidence_count: number;
  // Discovery fields
  match_type: string | null;
  confidence: number | null;
  reasons_ar: string | null;
  reasons_en: string | null;
  is_core: boolean | null;
  discovered_at: string | null;
}

export interface ThemeCoverage {
  theme_id: string;
  title_ar: string;
  title_en: string;
  total_segments: number;
  total_verses: number;
  manual_segments: number;
  discovered_segments: number;
  core_segments: number;
  supporting_segments: number;
  avg_confidence: number;
  by_match_type: Record<string, number>;
  by_confidence_band: Record<string, number>;
  tafsir_sources_used: string[];
  quran_coverage_percentage: number;
}

export interface SegmentEvidence {
  segment_id: string;
  theme_id: string;
  theme_title_ar: string;
  theme_title_en: string;
  sura_no: number;
  ayah_no: number;
  text_uthmani: string;
  match_type: string;
  confidence: number;
  reasons_ar: string;
  reasons_en: string | null;
  is_core: boolean;
  evidence_sources: Array<{ source_id: string; chunk_id: string; snippet: string }>;
  matching_keywords: string[];
}

export interface ThemeDetail extends QuranicTheme {
  description_ar: string | null;
  description_en: string | null;
  related_theme_ids: string[];
  tafsir_sources: string[];
  suras_mentioned: number[];
  makki_percentage: number;
  madani_percentage: number;
  is_complete: boolean;
  children: QuranicTheme[];
}

export interface ThemeConsequence {
  id: number;
  consequence_type: string;
  type_label_ar: string;
  type_label_en: string;
  description_ar: string;
  description_en: string;
  supporting_verses: Array<{ sura: number; ayah: number; relevance: string }>;
  display_order: number;
}

export interface ThemeGraphNode {
  id: string;
  type: string;
  label: string;
  label_ar: string;
  data: Record<string, unknown>;
  x: number | null;
  y: number | null;
}

export interface ThemeGraphEdge {
  source: string;
  target: string;
  type: string;
  label: string | null;
  label_ar: string | null;
  is_sequential: boolean;
  strength: number;
}

export interface ThemeGraph {
  theme_id: string;
  theme_title_ar: string;
  theme_title_en: string;
  nodes: ThemeGraphNode[];
  edges: ThemeGraphEdge[];
  entry_node_id: string | null;
  is_valid_dag: boolean;
  layout_mode: string;
  total_segments: number;
  total_connections: number;
}

export const themesApi = {
  /**
   * List all themes with optional filtering
   */
  listThemes: (params?: { category?: string; parent_only?: boolean; search?: string }) =>
    api.get<{ themes: QuranicTheme[] }>('/themes', { params }),

  /**
   * Get theme categories with counts
   */
  getCategories: () =>
    api.get<ThemeCategory[]>('/themes/categories'),

  /**
   * Get theme by category
   */
  getByCategory: (category: string) =>
    api.get<{ themes: QuranicTheme[] }>(`/themes/by-category/${category}`),

  /**
   * Get theme detail
   */
  getTheme: (themeId: string) =>
    api.get<ThemeDetail>(`/themes/${themeId}`),

  /**
   * Get theme segments with filters
   */
  getSegments: (themeId: string, params?: {
    verified_only?: boolean;
    match_type?: string;
    min_confidence?: number;
    is_core?: boolean;
    limit?: number;
    offset?: number;
  }) =>
    api.get<{ segments: ThemeSegment[]; total: number }>(`/themes/${themeId}/segments`, { params }),

  /**
   * Get theme coverage statistics
   */
  getCoverage: (themeId: string) =>
    api.get<ThemeCoverage>(`/themes/${themeId}/coverage`),

  /**
   * Get segment evidence ("Why this verse?")
   */
  getSegmentEvidence: (themeId: string, segmentId: string) =>
    api.get<SegmentEvidence>(`/themes/${themeId}/segments/${segmentId}/evidence`),

  /**
   * Get theme graph for visualization
   */
  getGraph: (themeId: string, params?: { language?: string; layout_mode?: string }) =>
    api.get<ThemeGraph>(`/themes/${themeId}/graph`, { params }),

  /**
   * Get theme consequences (rewards/punishments)
   * Note: Backend returns array directly
   */
  getConsequences: (themeId: string) =>
    api.get<ThemeConsequence[]>(`/themes/${themeId}/consequences`),

  /**
   * Get related themes
   * Note: Backend returns array directly
   */
  getRelated: (themeId: string) =>
    api.get<QuranicTheme[]>(`/themes/${themeId}/related`),

  /**
   * Get themes for a specific surah
   */
  getBySura: (suraNo: number) =>
    api.get<{ themes: QuranicTheme[] }>(`/themes/by-sura/${suraNo}`),
};
