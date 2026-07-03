/**
 * Asmā' Allah al-Ḥusnā Atlas — type contracts for Phase W.
 *
 * Used by:
 *   - frontend/src/data/asmaAllahSeeds.ts (seed list)
 *   - scripts/build-asma-allah-atlas.ts (extraction)
 *   - scripts/validate-asma-allah-atlas.ts
 *   - backend Pydantic mirrors and API responses
 *   - frontend Asmā' UI pages
 *
 * Safety rules (mirror docs/quran-content-policy.md):
 *   - No Quran text is mutated.
 *   - `matchedForm` may contain a short, normalised Arabic surface token
 *     extracted directly from the canonical Quran data — never paraphrased.
 *   - `meaningArabic` / `meaningEnglish` default to undefined; values may
 *     only be set when a trusted scholarly source is attached and the
 *     reviewStatus is verified.
 *   - `category` defaults to "needs_review" until a reviewer-approved
 *     category source provides it.
 *   - `contextual_attribute` occurrences are needs_review.
 *   - `exact_name` matching means the string was detected — it does NOT
 *     mean the interpretation is verified.
 */

export type AsmaCategory = 'dhat' | 'jamal' | 'jalal' | 'kamal' | 'afaal' | 'unknown';

export const ASMA_CATEGORY_META: Record<AsmaCategory, { labelAr: string; labelEn: string }> = {
  dhat: { labelAr: 'الذات', labelEn: 'Essence' },
  jamal: { labelAr: 'الجمال', labelEn: 'Beauty' },
  jalal: { labelAr: 'الجلال', labelEn: 'Majesty' },
  kamal: { labelAr: 'الكمال', labelEn: 'Perfection' },
  afaal: { labelAr: 'الأفعال', labelEn: 'Actions' },
  unknown: { labelAr: 'غير مصنف', labelEn: 'Unclassified' },
};

export type AsmaReviewStatus = 'verified' | 'needs_review' | 'missing_source' | 'rejected';

export type AsmaOccurrenceReviewStatus = 'verified' | 'needs_review';

export type AsmaMatchType =
  | 'exact_name'
  | 'definite_form'
  | 'name_pairing'
  | 'contextual_attribute'
  | 'basmalah_excluded'
  | 'needs_review';

// ---------------------------------------------------------------------------
// Quran reference (no text embedded)
// ---------------------------------------------------------------------------

export interface QuranReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  /**
   * Short scholarly note (≤ 200 chars, no Quran text). Used by the Tirmidhi
   * primary-references map to flag verses cited by concept rather than by
   * exact lemma (e.g. al_qabid at 2:245). Optional; null when the lemma is
   * directly present.
   */
  note?: string;
}

// ---------------------------------------------------------------------------
// Occurrence
// ---------------------------------------------------------------------------

export interface AsmaOccurrence {
  surahNumber: number;
  ayahNumber: number;
  /** Short Arabic surface form (≤80 chars, no newlines). */
  matchedForm: string;
  matchType: AsmaMatchType;
  isBasmalah: boolean;
  /** When false (e.g. basmalah_excluded), this occurrence is shown but
   *  does not contribute to occurrenceCount. */
  counted: boolean;
  confidence: number;
  sourceIds: string[];
  reviewStatus: AsmaOccurrenceReviewStatus;
  humanReviewRequired: boolean;
}

// ---------------------------------------------------------------------------
// Pairing (two names co-occurring inside the same ayah)
// ---------------------------------------------------------------------------

export interface AsmaNamePairing {
  firstNameId: string;
  secondNameId: string;
  occurrenceCount: number;
  ayahReferences: QuranReference[];
  reviewStatus: AsmaOccurrenceReviewStatus;
}

// ---------------------------------------------------------------------------
// Name (the canonical entry)
// ---------------------------------------------------------------------------

export interface AsmaAllahName {
  nameId: string;
  arabicName: string;
  transliteration: string;
  englishName?: string;
  rootArabic?: string;
  category: AsmaCategory;
  /** Verified meaning, only when source-backed; otherwise leave undefined. */
  meaningArabic?: string;
  meaningEnglish?: string;
  /** Short reviewer-supplied reflection (Optional, also source-gated). */
  shortReflectionArabic?: string;
  shortReflectionEnglish?: string;
  quranOccurrences: AsmaOccurrence[];
  /** Number of `counted=true` occurrences (excludes basmalah-excluded). */
  occurrenceCount: number;
  surahCount: number;
  firstOccurrence?: QuranReference;
  lastOccurrence?: QuranReference;
  /**
   * Curated primary Quranic references for this Name from the Tirmidhi
   * tradition (see `data/asmaAllahQuranicReferences.ts`). These are the
   * verses scholars cite as the canonical evidence for the Name, even when
   * the literal lemma is hadith-only (e.g. al_qabid, al_baith). Each entry
   * is `needs_review` until a human reviewer promotes it.
   */
  primaryQuranicReferences: QuranReference[];
  commonPairings: AsmaNamePairing[];
  relatedTopics: string[];
  relatedEntities: string[];
  sourceIds: string[];
  reviewStatus: AsmaReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ---------------------------------------------------------------------------
// Seed (input to the extraction script)
// ---------------------------------------------------------------------------

export interface AsmaAllahSeed {
  nameId: string;
  arabicName: string;
  transliteration: string;
  englishName?: string;
  rootArabic?: string;
  /** Suggested default category; remains needs_review until reviewed. */
  category: AsmaCategory;
  /** Arabic surface forms (normalised against the Quran scanner pipeline). */
  aliasesArabic: string[];
  /** Optional warnings carried into the atlas. */
  warnings?: string[];
  /**
   * Whether this seed is one of the 99 traditional names of Asmā' Allah
   * al-Ḥusnā. The Divine Name itself (Allah / اسم الجلالة) is NOT one of the
   * 99 — it is the supreme Name that the 99 describe. Defaults to true; set
   * to false only for the standalone Divine Name "Allah".
   */
  inTraditional99?: boolean;
}

// ---------------------------------------------------------------------------
// Atlas output
// ---------------------------------------------------------------------------

export interface AsmaCategoryCount {
  category: AsmaCategory;
  names: number;
  countedOccurrences: number;
}

export interface AsmaAtlasOutput {
  version: string;
  generatedAt: string;
  /** Documents the basmalah-counting setting at the time of generation. */
  basmalahPolicy: {
    countBasmalaInFatihah: boolean;
    excludeRepeatedSurahOpeningBasmalah: boolean;
    notes: string;
  };
  /**
   * Names in the primary display list. Equals 99 when the Divine Name "Allah"
   * is shown separately; equals 99 (or 100 if Allah is included) when policy
   * places Allah inside the list. The frontend uses this as the "all" count.
   */
  totalNames: number;
  totalCountedOccurrences: number;
  totalExcludedBasmalahOccurrences: number;
  namesWithOccurrences: number;
  namesWithZeroOccurrences: number;
  topNamesByOccurrence: Array<{ nameId: string; arabicName: string; occurrenceCount: number; surahCount: number }>;
  topPairings: Array<{ firstNameId: string; secondNameId: string; occurrenceCount: number }>;
  categoryCounts: AsmaCategoryCount[];
  names: AsmaAllahName[];
  /** Count of the 99 traditional names — always 99 once the policy is enforced. */
  traditionalNamesCount: number;
  /** Whether the Divine Name "Allah" is bundled into the primary list (false = separate). */
  divineNameAllahIncluded: boolean;
  /** Count rendered for the main "All" tab in the UI. */
  allDisplayCount: number;
  /** Number of traditional 99 names that have at least one counted Quran occurrence. */
  quranEvidenceNamesCount: number;
  /** Number of traditional 99 names with zero counted occurrences (hadith-only). */
  zeroExactOccurrenceNamesCount: number;
  /** nameIds removed by the builder as duplicates (alternate spellings/forms). */
  duplicateNamesRemoved: string[];
  /** When Allah is shown separately, this carries its standalone record. */
  divineNameAllah?: AsmaAllahName;
  warnings: string[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function defaultOccurrenceReviewStatus(_m: AsmaMatchType): AsmaOccurrenceReviewStatus {
  return 'needs_review';
}

export function defaultOccurrenceHumanReviewRequired(_m: AsmaMatchType): boolean {
  return true;
}
