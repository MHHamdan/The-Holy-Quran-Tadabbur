/**
 * Surah Memory Atlas — type definitions
 *
 * All ayah text (firstAyahPreview, lastAyahPreview, ...) is verbatim Tanzil
 * verse text from data/raw/quran_tanzil.json — never hardcoded or
 * AI-generated. Tanzil keeps the Bismillah in a separate field, so verse text
 * never contains it and must be rendered as is.
 * Makki/Madani classification is from curated scholarly metadata (needs_review).
 * Topics and memory clues are only shown when from a trusted source.
 */

export type RevelationType = 'makki' | 'madani' | 'unknown';

export type LengthCategory = 'short' | 'medium' | 'long' | 'very_long';

export type QuranPosition = 'beginning' | 'early' | 'middle' | 'late' | 'ending';

export type ReviewStatus = 'verified' | 'needs_review' | 'missing_metadata';

export interface SurahMemoryItem {
  surahNumber: number;
  nameArabic: string;
  nameTransliteration: string;
  nameEnglish?: string;
  revelationType: RevelationType;
  ayahCount: number;
  lengthCategory: LengthCategory;
  quranPosition: QuranPosition;
  juzStart: number;
  juzEnd: number;
  pageStart: number;
  pageEnd: number;
  firstAyahRef: string;
  secondAyahRef?: string;
  midAyah1Ref?: string;
  midAyah2Ref?: string;
  prevLastAyahRef?: string;
  lastAyahRef: string;
  firstAyahPreview?: string;       // ayah 1 — verbatim from quran_tanzil.json (no Bismillah prefix)
  secondAyahPreview?: string;      // ayah 2 — verbatim from quran_tanzil.json
  midAyah1Preview?: string;        // ayah ~40% through — verbatim from quran_tanzil.json
  midAyah2Preview?: string;        // ayah ~60% through — verbatim from quran_tanzil.json
  prevLastAyahPreview?: string;    // second-to-last ayah — verbatim from quran_tanzil.json
  lastAyahPreview?: string;        // last ayah — verbatim from quran_tanzil.json
  mainTopicsArabic: string[];
  mainTopicsEnglish: string[];
  memoryClueArabic?: string;
  memoryClueEnglish?: string;
  relatedStories: string[];
  relatedThemes: string[];
  mainFigures: string[];
  sourceIds: string[];
  reviewStatus: ReviewStatus;
}

export interface StoryName {
  ar: string;
  en: string;
}

export interface SurahMemoryAtlasWithStories extends SurahMemoryAtlas {
  storyNames: Record<string, StoryName>;
}

export interface SurahMemoryAtlas {
  version: string;
  generatedAt: string;
  totalSurahs: number;
  sourceNote: string;
  surahs: SurahMemoryItem[];
}
