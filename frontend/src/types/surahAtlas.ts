/**
 * Surah Atlas — Type System
 *
 * Safety rules:
 * - All summaries are pedagogical paraphrases, never reproduced Quran text
 * - Every SurahAtlasEntry must cite sourceIds from sourceRegistry
 * - All entries start as "needs_review" until scholarly validation
 * - Arabic text in previews comes from quran_uthmani.json only
 * - No tafsir text is reproduced — source IDs are referenced, not content
 */

import type { SunniReviewStatus } from './quranStory';
import type { RevelationType } from './surahMemoryAtlas';

// ---------------------------------------------------------------------------
// Shared building blocks
// ---------------------------------------------------------------------------

export interface BilingualText {
  en: string;
  ar: string;
}

export interface AyahRef {
  surah: number;
  ayah: number;
  rangeEnd?: number;
  display: string;
}

export interface EvidenceReference {
  sourceId: string;
  refLabel?: string;
  note?: string;
}

// ---------------------------------------------------------------------------
// Surah Theme
// ---------------------------------------------------------------------------

export interface SurahTheme {
  id: string;
  label: BilingualText;
  ayahRefs: AyahRef[];
  evidenceRefs: EvidenceReference[];
}

// ---------------------------------------------------------------------------
// Surah Section — logical structural division of a surah
// ---------------------------------------------------------------------------

export interface SurahSection {
  id: string;
  title: BilingualText;
  ayahRange: { start: number; end: number };
  summary: BilingualText;
  keyLessons: { en: string[]; ar: string[] };
  relatedStoryIds: string[];
  rareWordIds: string[];
  evidenceRefs: EvidenceReference[];
}

// ---------------------------------------------------------------------------
// Tafsir Highlight — a key insight from classical tafsir
// ---------------------------------------------------------------------------

export interface TafsirHighlight {
  id: string;
  ayahRef: AyahRef;
  insight: BilingualText;
  sourceId: string;
  reviewStatus: SunniReviewStatus;
  humanReviewRequired: boolean;
}

// ---------------------------------------------------------------------------
// Surah Memorization Map
// ---------------------------------------------------------------------------

export interface SurahMemorizationMap {
  difficultyLevel: 'easy' | 'medium' | 'hard' | 'very_hard' | 'needs_review';
  openingStyle: string;
  closingStyle: string;
  confusionPairIds: string[];
  anchorAyahRefs: AyahRef[];
  reviewPriority: 'high' | 'medium' | 'low';
  memorizerNotes: BilingualText;
}

// ---------------------------------------------------------------------------
// Similar Surah reference
// ---------------------------------------------------------------------------

export interface SimilarSurah {
  surahNumber: number;
  similarityReason: BilingualText;
  linkType:
    | 'same_theme'
    | 'same_story'
    | 'same_opening'
    | 'same_closing'
    | 'same_prophet'
    | 'same_nation'
    | 'contrast'
    | 'chronological_relation';
  confidence: 'high' | 'medium' | 'low';
}

// ---------------------------------------------------------------------------
// Repeated Phrase
// ---------------------------------------------------------------------------

export interface RepeatedPhrase {
  id: string;
  phraseArabic: string;
  phraseTransliteration?: string;
  meaningEn: string;
  occurrencesInSurah: AyahRef[];
  occurrencesElsewhere: AyahRef[];
  memorizerNote: BilingualText;
}

// ---------------------------------------------------------------------------
// Story reference inside a surah
// ---------------------------------------------------------------------------

export interface SurahStoryRef {
  storyId: string;
  titleEn: string;
  titleAr: string;
  ayahRange: AyahRef;
  coverage: 'complete' | 'partial' | 'mention_only';
}

// ---------------------------------------------------------------------------
// Surah Atlas Entry — the core data type
// ---------------------------------------------------------------------------

export interface SurahAtlasEntry {
  surahNumber: number;
  slug: string;
  nameArabic: string;
  nameTransliteration: string;
  nameEnglishMeaning: string;
  revelationType: RevelationType | 'mixed' | 'disputed' | 'needs_review';
  ayahCount: number;
  wordCount?: number;
  uniqueWordCount?: number;
  juzRefs: string[];
  hizbRefs: string[];
  rukus?: number;
  sajdahAyat?: AyahRef[];

  mainThemes: SurahTheme[];
  subThemes: SurahTheme[];
  storiesMentioned: SurahStoryRef[];
  prophetsMentioned: string[];
  nationsMentioned: string[];
  keyConcepts: string[];
  rareWordIds: string[];

  summary: {
    short: BilingualText;
    detailed: BilingualText;
    memorizer: BilingualText;
    childFriendly: BilingualText;
  };

  structure: SurahSection[];
  openingStyle: string;
  closingStyle: string;
  repeatedPhrases: RepeatedPhrase[];
  similarSurahs: SimilarSurah[];
  memorizationMap: SurahMemorizationMap;
  tafsirHighlights: TafsirHighlight[];
  learningObjectives: { en: string[]; ar: string[] };

  evidenceRefs: EvidenceReference[];
  sourceIds: string[];
  reviewStatus: SunniReviewStatus;
  humanReviewRequired: boolean;
}

// ---------------------------------------------------------------------------
// Surah Atlas Collection
// ---------------------------------------------------------------------------

export interface SurahAtlas {
  version: string;
  generatedAt: string;
  totalSurahs: number;
  surahs: SurahAtlasEntry[];
  reviewNote: BilingualText;
}

// ---------------------------------------------------------------------------
// Filter types used by SurahAtlasPage
// ---------------------------------------------------------------------------

export type SurahAtlasSortKey =
  | 'quranOrder'
  | 'ayahCount'
  | 'storyCount'
  | 'rareWordCount'
  | 'difficultyAsc'
  | 'difficultyDesc';

export type SurahAtlasFilter = {
  revelationType?: RevelationType | 'all';
  prophet?: string;
  theme?: string;
  story?: string;
  difficultyLevel?: 'easy' | 'medium' | 'hard' | 'very_hard' | 'all';
  searchQuery?: string;
  sortBy?: SurahAtlasSortKey;
};
