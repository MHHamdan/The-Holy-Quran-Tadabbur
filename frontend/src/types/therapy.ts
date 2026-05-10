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
  disclaimer_en: string;
  disclaimer_ar: string;
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
