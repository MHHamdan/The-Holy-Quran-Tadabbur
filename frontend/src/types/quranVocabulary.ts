/**
 * Quran Vocabulary — Frontend Type System
 *
 * Covers rare words (gharib al-Quran) and lexical entries.
 *
 * Safety rules:
 * - Every meaning requires a lexicalEvidenceRef
 * - No AI-generated meanings without source backing
 * - All entries start as "needs_review"
 * - contextualMeaning is distinct from dictionary meaning
 */

import type { AyahRef, BilingualText, EvidenceReference } from './surahAtlas';
import type { SunniReviewStatus } from './quranStory';

// ---------------------------------------------------------------------------
// Rarity Level
// ---------------------------------------------------------------------------

export type RarityLevel = 'very_rare' | 'rare' | 'moderately_rare';

// ---------------------------------------------------------------------------
// Rare Word Entry
// ---------------------------------------------------------------------------

export interface RareWordEntry {
  id: string;
  arabic: string;
  normalizedArabic: string;
  transliteration: string;
  root?: string;
  lemma?: string;
  partOfSpeech?: string;
  surah: number;
  ayah: number;
  wordPosition?: number;
  frequencyInQuran?: number;
  rarityLevel: RarityLevel;
  simpleMeaning: BilingualText;
  contextualMeaning: BilingualText;
  explanation: BilingualText;
  memoryHint: BilingualText;
  lexicalEvidenceRefs: EvidenceReference[];
  tafsirEvidenceRefs: EvidenceReference[];
  sourceIds: string[];
  reviewStatus: SunniReviewStatus;
  humanReviewRequired: boolean;
}

// ---------------------------------------------------------------------------
// Vocabulary Collection
// ---------------------------------------------------------------------------

export interface RareWordsCollection {
  version: string;
  generatedAt: string;
  totalEntries: number;
  entries: RareWordEntry[];
  reviewNote: BilingualText;
}

// ---------------------------------------------------------------------------
// Vocabulary Source (extends source registry)
// ---------------------------------------------------------------------------

export interface VocabularySource {
  sourceId: string;
  titleEn: string;
  titleAr: string;
  author: string;
  language: 'ar' | 'en' | 'both';
  type: 'lexicon' | 'tafsir' | 'corpus';
  reliabilityLevel: 'canonical' | 'high' | 'medium' | 'needs_review';
}
