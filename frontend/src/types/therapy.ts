// ============================================================================
// Spiritual Guidance & Emotional Support — Phase T / T2
// ============================================================================

export type EmotionCategory =
  | 'anxiety'
  | 'sadness'
  | 'grief'
  | 'fear'
  | 'loneliness'
  | 'hopelessness'
  | 'anger'
  | 'stress'
  | 'guilt'
  | 'doubt'
  | 'gratitude'
  | 'general';

export interface GuidanceCard {
  reference: string;
  surah: number;
  ayah_start: number;
  ayah_end: number;
  surah_name_ar: string;
  surah_name_en: string;
  text_uthmani: string;
  text_imlaei: string;
  theme: string;
  theme_ar: string;
  theme_en: string;
  lesson_en: string;
  lesson_ar: string;
  reflection_en: string;
  reflection_ar: string;
  dua_en: string;
  dua_ar: string;
  prophet_story?: string;
}

export interface AskRequest {
  message: string;
  language?: string;
  emotion_override?: string;
  // Phase T3 — personalization context
  previous_emotion?: string;
  previous_theme?: string;
  reinforcement_index?: number;
}

export interface SpiritualGuidanceResponse {
  ok: boolean;
  session_id: string;
  emotion: EmotionCategory;
  emotion_label_en: string;
  emotion_label_ar: string;
  empathy_en: string;
  empathy_ar: string;
  reinforcement_en: string;
  reinforcement_ar: string;
  cards: GuidanceCard[];
  recommended_themes: string[];
  follow_up_prompts_en: string[];
  follow_up_prompts_ar: string[];
  // Phase T3
  suggested_theme?: string;
  suggested_theme_reason_en?: string;
  suggested_theme_reason_ar?: string;
  personalization_note_en?: string;
  personalization_note_ar?: string;
  // Phase T4 — NLI classifier confidence (0.0 = keyword fallback was used)
  emotion_confidence?: number;
  // Phase T5-C — adaptive tone profile label
  tone_profile?: string;
  // Phase T5-D — reflection journal prompt
  reflection_prompt_en?: string;
  reflection_prompt_ar?: string;
  disclaimer_en: string;
  disclaimer_ar: string;
  // Crisis-safety layer (Phase T-Crisis)
  crisis_level?: 'none' | 'elevated' | 'crisis';
  crisis_banner_en?: string | null;
  crisis_banner_ar?: string | null;
  crisis_hotlines?: CrisisHotlineOut[];
}

export interface CrisisHotlineOut {
  region_code: string;
  region_name_en: string;
  region_name_ar: string;
  number: string;
  organisation_en: string;
  organisation_ar: string;
  url: string;
  is_muslim_specific: boolean;
}

// =============================================================================
// Phase T-Situations — Situation Atlas
// =============================================================================

export interface SituationSummary {
  key: string;
  label_en: string;
  label_ar: string;
  description_en: string;
  description_ar: string;
  primary_emotion: string;
  healing_themes: string[];
  refer_to_professional: boolean;
}

export interface SituationHadithRef {
  collection: string;
  number: string;
  narrator_en: string;
  narrator_ar: string;
  note_en: string;
  note_ar: string;
  url: string;
}

export interface SituationDua {
  key: string;
  arabic: string;
  transliteration: string;
  translation_en: string;
  translation_ar: string;
}

export interface SituationDetail extends SituationSummary {
  duas: SituationDua[];
  hadith_refs: SituationHadithRef[];
  review_status: string;
  human_review_required: boolean;
  disclaimer_en: string;
  disclaimer_ar: string;
}

export interface SituationsListResponse {
  total: number;
  situations: SituationSummary[];
  disclaimer_en: string;
  disclaimer_ar: string;
}

// =============================================================================
// Phase T-Ruqyah — Authenticated evidence pack
// =============================================================================

export interface RuqyahEvidenceItem {
  kind: 'hadith' | 'ayah';
  title_en: string;
  title_ar: string;
  summary_en: string;
  summary_ar: string;
  reference: string;
  url: string;
  review_status: string;
}

export interface RuqyahEvidenceResponse {
  total: number;
  items: RuqyahEvidenceItem[];
  disclaimer_en: string;
  disclaimer_ar: string;
  scope_note_en: string;
  scope_note_ar: string;
}

// Phase T5-D — Reflection Journal
export interface ReflectionRecord {
  session_id: string;
  emotion: string;
  label_en: string;
  label_ar: string;
  theme?: string;
  reflection: string;
  verses: string[];
  timestamp: string;
}

export interface ReflectionsResponse {
  ok: boolean;
  reflections: ReflectionRecord[];
}

// ============================================================================
// Phase T2 — Chat & Insights types
// ============================================================================

export interface ChatCitation {
  source_id: string;
  source_name: string;
  verse_reference: string;
  excerpt: string;
}

export interface ChatRequest {
  message: string;
  language: string;
  emotion_override?: string;
  session_id?: string;
  conversation_context?: Array<{ role: string; content: string }>;
}

export interface ChatResponse {
  ok: boolean;
  session_id: string;
  emotion: string;
  emotion_label_en: string;
  emotion_label_ar: string;
  answer: string;
  answer_language: string;
  citations: ChatCitation[];
  related_verses: string[];
  follow_up_suggestions: string[];
  fallback_cards: GuidanceCard[];
  used_rag: boolean;
  // Phase T4
  emotion_confidence?: number;
  // Phase T5-C
  tone_profile?: string;
  disclaimer_en: string;
  disclaimer_ar: string;
}

export interface EmotionCount {
  emotion: string;
  label_en: string;
  label_ar: string;
  count: number;
}

export interface EmotionPoint {
  session_id: string;
  emotion: string;
  label_en: string;
  label_ar: string;
  theme?: string;
  timestamp: string;
}

export interface InsightsResponse {
  ok: boolean;
  total_sessions: number;
  emotion_distribution: EmotionCount[];
  most_visited_theme?: string;
  streak_days: number;
  top_emotion?: string;
  top_emotion_label_en?: string;
  top_emotion_label_ar?: string;
  // Phase T3
  suggested_next_theme?: string;
  growth_prompt_en?: string;
  growth_prompt_ar?: string;
  // Phase T5-B
  emotion_timeline: EmotionPoint[];
  trend: string;
  weekly_change?: number;
}

export interface HealingTheme {
  key: string;
  ar: string;
  en: string;
  desc_en: string;
  desc_ar: string;
  icon: string;
  color: string;
}

export interface ThemesResponse {
  ok: boolean;
  themes: HealingTheme[];
}

export interface ThemeDetailResponse {
  ok: boolean;
  theme: HealingTheme;
  cards: GuidanceCard[];
  disclaimer_en: string;
  disclaimer_ar: string;
}

export interface EmotionInfo {
  key: EmotionCategory;
  label_en: string;
  label_ar: string;
}

export interface EmotionsResponse {
  ok: boolean;
  emotions: EmotionInfo[];
}

export interface ReflectionEntry {
  session_id: string;
  reflection: string;
  timestamp: number;
  emotion: EmotionCategory;
  verses: string[];
}

// ============================================================================
// Phase T-Adaptive — Topic Knowledge (hadith + wise phrases)
// ============================================================================

export interface TopicHadith {
  arabic: string;
  transliteration: string;
  translation_en: string;
  translation_ar: string;
  source_en: string;
  source_ar: string;
}

export interface TopicWisePhrase {
  text_en: string;
  text_ar: string;
  scholar_en: string;
  scholar_ar: string;
  source_en: string;
  source_ar: string;
}

export interface TopicResourcesResponse {
  ok: boolean;
  topic_key: string;
  topic_en: string;
  topic_ar: string;
  intro_en: string;
  intro_ar: string;
  hadith: TopicHadith[];
  wise_phrases: TopicWisePhrase[];
}
