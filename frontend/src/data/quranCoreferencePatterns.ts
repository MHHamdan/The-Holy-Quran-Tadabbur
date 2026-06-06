/**
 * Quran Coreference Pattern Dictionary — Phase U.
 *
 * Each pattern is a *deterministic, anchored* rule that proposes one or more
 * candidate entity links from Quran text. The pattern alone never asserts
 * identity:
 *   - The scanner downgrades confidence further if multiple candidates apply.
 *   - Every emitted mention defaults to reviewStatus="needs_review".
 *   - Patterns that would produce many false positives (e.g. bare possessives
 *     like "أمه" applied globally) are constrained to:
 *         (a) a story-range window, OR
 *         (b) the presence of an explicit/alias mention of an anchor entity
 *             in the same surah,
 *     so the rule cannot "leak" Maryam into unrelated mothers.
 *
 * Hard rules:
 *   - No Quran text is embedded here.
 *   - All `surfaceArabicNormalised` values are written WITHOUT diacritics so
 *     they match the scanner's `normaliseArabic` pipeline.
 *   - Each pattern carries its own `warnings[]` explaining the limitation.
 *
 * Story ranges come from the existing curated story segments. We intentionally
 * pin object/animal patterns (staff/dog/throne) to those ranges so the
 * scanner cannot match "his staff" or "his dog" outside the relevant story.
 */

import type { CoreferencePattern } from '../types/quranCoreference';

// ---------------------------------------------------------------------------
// Helper factory.
// ---------------------------------------------------------------------------

function pat(p: Omit<CoreferencePattern, 'sourceIds'> & { sourceIds?: string[] }): CoreferencePattern {
  return {
    sourceIds: ['quran_uthmani_cloud'],
    ...p,
  };
}

// ---------------------------------------------------------------------------
// 1. Maryam / Isa / Aal Imran family-and-pronoun patterns
// ---------------------------------------------------------------------------

const MARYAM_RANGE = [
  { surahNumber: 3, ayahStart: 33, ayahEnd: 60, storyId: 'story_maryam' },
  { surahNumber: 19, ayahStart: 1, ayahEnd: 40, storyId: 'story_maryam' },
  { surahNumber: 5, ayahStart: 110, ayahEnd: 120, storyId: 'story_table_spread' },
];

// Reserved for future Isa-specific patterns; currently the Maryam patterns
// already cover the cross-entity surfaces. Exported so it can be reused
// without re-declaration when more patterns are added.
export const ISA_RANGES = [
  { surahNumber: 3, ayahStart: 33, ayahEnd: 60, storyId: 'story_isa' },
  { surahNumber: 4, ayahStart: 156, ayahEnd: 172, storyId: 'story_isa' },
  { surahNumber: 5, ayahStart: 17, ayahEnd: 120, storyId: 'story_isa' },
  { surahNumber: 19, ayahStart: 16, ayahEnd: 40, storyId: 'story_isa' },
  { surahNumber: 43, ayahStart: 57, ayahEnd: 65, storyId: 'story_isa' },
  { surahNumber: 61, ayahStart: 6, ayahEnd: 14, storyId: 'story_isa' },
];

export const MARYAM_PATTERNS: CoreferencePattern[] = [
  pat({
    patternId: 'maryam_ibn_maryam_family',
    description: '"ابن مريم" — explicit family reference connecting Isa to Maryam.',
    surfaceType: 'family_reference',
    surfaceArabicNormalised: 'ابن مريم',
    candidateEntityId: 'entity_person_maryam',
    requiresEntityAnchorInSurah: [],
    allowedSurahs: [],
    allowedStoryRanges: [],
    resolutionMethod: 'rule_pattern',
    baseConfidence: 0.85,
    warnings: ['Family reference; needs_review until scholar confirms.'],
  }),
  pat({
    patternId: 'isa_ibn_maryam_link',
    description: '"ابن مريم" — same surface phrase, candidate Isa (via title-style reference).',
    surfaceType: 'family_reference',
    surfaceArabicNormalised: 'ابن مريم',
    candidateEntityId: 'entity_prophet_isa',
    requiresEntityAnchorInSurah: [],
    allowedSurahs: [],
    allowedStoryRanges: [],
    resolutionMethod: 'rule_pattern',
    baseConfidence: 0.85,
    warnings: ['Title-style reference; refers to Isa son of Maryam.'],
  }),
  pat({
    patternId: 'maryam_pronoun_mother_isa_anchor',
    description: '"أمه" — "his mother" anchored to Isa context; candidate Maryam.',
    surfaceType: 'possessive_pronoun',
    surfaceArabicNormalised: 'أمه',
    candidateEntityId: 'entity_person_maryam',
    requiresEntityAnchorInSurah: ['entity_prophet_isa', 'entity_person_maryam'],
    allowedSurahs: [],
    allowedStoryRanges: MARYAM_RANGE,
    resolutionMethod: 'same_passage_context',
    baseConfidence: 0.55,
    warnings: [
      '"أمه" matches "his mother" of any antecedent; restricted to surahs/ranges where Isa/Maryam already appear. needs_review.',
    ],
  }),
  pat({
    patternId: 'maryam_direct_address_walidatuka',
    description: '"والدتك" — direct address "your mother", anchored to Isa speaking context (5:110).',
    surfaceType: 'family_reference',
    surfaceArabicNormalised: 'والدتك',
    candidateEntityId: 'entity_person_maryam',
    requiresEntityAnchorInSurah: ['entity_prophet_isa'],
    allowedSurahs: [],
    allowedStoryRanges: [
      { surahNumber: 5, ayahStart: 110, ayahEnd: 115, storyId: 'story_table_spread' },
    ],
    resolutionMethod: 'rule_pattern',
    baseConfidence: 0.7,
    warnings: ['Direct-address phrase in 5:110; needs reviewer confirmation.'],
  }),
  pat({
    patternId: 'isa_masih_title',
    description: '"المسيح" — title of Isa.',
    surfaceType: 'title',
    surfaceArabicNormalised: 'المسيح',
    candidateEntityId: 'entity_prophet_isa',
    requiresEntityAnchorInSurah: [],
    allowedSurahs: [],
    allowedStoryRanges: [],
    resolutionMethod: 'rule_pattern',
    baseConfidence: 0.85,
    warnings: ['Title "Al-Masih" refers to Isa; needs_review.'],
  }),
];

// ---------------------------------------------------------------------------
// 2. Zakariyya–Maryam guardianship in Aal Imran
// ---------------------------------------------------------------------------

export const ZAKARIYYA_PATTERNS: CoreferencePattern[] = [
  pat({
    patternId: 'zakariyya_kafala_aal_imran',
    description: '"كفلها زكريا" / "كفلها" — guardianship of Maryam by Zakariyya in 3:37.',
    surfaceType: 'implicit_context',
    surfaceArabicNormalised: 'كفلها',
    candidateEntityId: 'entity_prophet_zakariyya',
    requiresEntityAnchorInSurah: ['entity_person_maryam'],
    allowedSurahs: [3],
    allowedStoryRanges: [
      { surahNumber: 3, ayahStart: 35, ayahEnd: 44, storyId: 'story_maryam' },
    ],
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.7,
    warnings: ['Guardianship reference; needs reviewer confirmation.'],
  }),
];

// ---------------------------------------------------------------------------
// 3. Musa story patterns: staff, sea crossing, Bani Israel, Firawn
// ---------------------------------------------------------------------------

const MUSA_RANGES = [
  { surahNumber: 7, ayahStart: 103, ayahEnd: 137, storyId: 'story_musa' },
  { surahNumber: 20, ayahStart: 9, ayahEnd: 99, storyId: 'story_musa' },
  { surahNumber: 26, ayahStart: 10, ayahEnd: 68, storyId: 'story_musa' },
  { surahNumber: 28, ayahStart: 3, ayahEnd: 46, storyId: 'story_musa' },
];

export const MUSA_PATTERNS: CoreferencePattern[] = [
  pat({
    patternId: 'musa_staff_asaa_h',
    description: '"عصاه" — staff possessive in Musa context.',
    surfaceType: 'possessive_pronoun',
    surfaceArabicNormalised: 'عصاه',
    candidateEntityId: 'entity_object_staff_musa',
    requiresEntityAnchorInSurah: ['entity_prophet_musa'],
    allowedSurahs: [],
    allowedStoryRanges: MUSA_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.7,
    warnings: ['Staff possessive anchored to Musa story window; needs_review.'],
  }),
  pat({
    patternId: 'musa_staff_asaa_k',
    description: '"عصاك" — staff direct-address in Musa context.',
    surfaceType: 'possessive_pronoun',
    surfaceArabicNormalised: 'عصاك',
    candidateEntityId: 'entity_object_staff_musa',
    requiresEntityAnchorInSurah: ['entity_prophet_musa'],
    allowedSurahs: [],
    allowedStoryRanges: MUSA_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.7,
    warnings: ['Staff direct-address anchored to Musa story window; needs_review.'],
  }),
  pat({
    patternId: 'musa_sea_crossing',
    description: '"فانفلق" / "فرق" near "البحر" — sea-crossing event.',
    surfaceType: 'implicit_context',
    surfaceArabicNormalised: 'فانفلق',
    candidateEntityId: 'entity_event_sea_crossing',
    requiresEntityAnchorInSurah: ['entity_prophet_musa'],
    allowedSurahs: [],
    allowedStoryRanges: MUSA_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.75,
    warnings: ['Sea-splitting event; needs_review.'],
  }),
];

// ---------------------------------------------------------------------------
// 4. People of the Cave: dog (كلبهم) anchored to Surah Al-Kahf
// ---------------------------------------------------------------------------

const KAHF_RANGES = [
  { surahNumber: 18, ayahStart: 9, ayahEnd: 26, storyId: 'story_kahf' },
];

export const KAHF_PATTERNS: CoreferencePattern[] = [
  pat({
    patternId: 'kahf_kalbuhum_dog',
    description: '"كلبهم" — "their dog", anchored to Ashab al-Kahf passage.',
    surfaceType: 'possessive_pronoun',
    surfaceArabicNormalised: 'كلبهم',
    candidateEntityId: 'entity_animal_dog_cave',
    requiresEntityAnchorInSurah: ['entity_people_ashab_kahf'],
    allowedSurahs: [18],
    allowedStoryRanges: KAHF_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.85,
    warnings: ['Dog of the Cave; anchored to Surah Al-Kahf only.'],
  }),
  pat({
    patternId: 'kahf_alfityah',
    description: '"الفتية" — "the youths" in Al-Kahf, candidate Ashab al-Kahf.',
    surfaceType: 'role_reference',
    surfaceArabicNormalised: 'الفتيه',
    candidateEntityId: 'entity_people_ashab_kahf',
    requiresEntityAnchorInSurah: [],
    allowedSurahs: [18],
    allowedStoryRanges: KAHF_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.65,
    warnings: ['Generic word for "youths"; matched only inside Surah Al-Kahf.'],
  }),
];

// ---------------------------------------------------------------------------
// 5. Bilqis / Sulayman / Throne of Bilqis — Surah An-Naml only
// ---------------------------------------------------------------------------

const NAML_BILQIS_RANGES = [
  { surahNumber: 27, ayahStart: 15, ayahEnd: 44, storyId: 'story_bilqis' },
];

export const BILQIS_PATTERNS: CoreferencePattern[] = [
  pat({
    patternId: 'bilqis_arshuha_throne',
    description: '"عرشها" — her throne, anchored to An-Naml passage.',
    surfaceType: 'possessive_pronoun',
    surfaceArabicNormalised: 'عرشها',
    candidateEntityId: 'entity_object_throne_bilqis',
    requiresEntityAnchorInSurah: ['entity_prophet_sulayman'],
    allowedSurahs: [27],
    allowedStoryRanges: NAML_BILQIS_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.8,
    warnings: ['Throne possessive anchored to Surah An-Naml; needs_review.'],
  }),
  pat({
    patternId: 'bilqis_implicit_imratan_tamlikuhum',
    description: '"امرأة تملكهم" — "a woman who rules them", anchored to An-Naml 27:23.',
    surfaceType: 'role_reference',
    surfaceArabicNormalised: 'امراه تملكهم',
    candidateEntityId: 'entity_person_bilqis',
    requiresEntityAnchorInSurah: ['entity_prophet_sulayman'],
    allowedSurahs: [27],
    allowedStoryRanges: NAML_BILQIS_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.6,
    warnings: [
      'Bilqis is never named explicitly in the Quran; this role-reference is needs_review.',
    ],
  }),
  pat({
    patternId: 'bilqis_malikat_saba_title',
    description: '"ملكة سبأ" — "Queen of Saba" descriptive title (not in Quran text directly).',
    surfaceType: 'title',
    surfaceArabicNormalised: 'ملكه سبا',
    candidateEntityId: 'entity_person_bilqis',
    requiresEntityAnchorInSurah: ['entity_prophet_sulayman', 'entity_people_saba'],
    allowedSurahs: [27],
    allowedStoryRanges: NAML_BILQIS_RANGES,
    resolutionMethod: 'tafsir_source',
    baseConfidence: 0.4,
    warnings: [
      'Title not present in Quran text; only used in tafsir. needs_review until verified tafsir source attached.',
    ],
  }),
];

// ---------------------------------------------------------------------------
// 6. Adam / Hawwa — "زوجه" anchored to Adam story window only
// ---------------------------------------------------------------------------

const ADAM_RANGES = [
  { surahNumber: 2, ayahStart: 30, ayahEnd: 39, storyId: 'story_adam' },
  { surahNumber: 7, ayahStart: 11, ayahEnd: 27, storyId: 'story_adam' },
  { surahNumber: 20, ayahStart: 115, ayahEnd: 127, storyId: 'story_adam' },
];

export const ADAM_PATTERNS: CoreferencePattern[] = [
  pat({
    patternId: 'adam_zawjuhu_hawwa',
    description: '"زوجه" — "his wife", anchored to Adam-story window; candidate Hawwa.',
    surfaceType: 'family_reference',
    surfaceArabicNormalised: 'زوجه',
    candidateEntityId: 'entity_person_hawwa',
    requiresEntityAnchorInSurah: ['entity_prophet_adam'],
    allowedSurahs: [2, 7, 20],
    allowedStoryRanges: ADAM_RANGES,
    resolutionMethod: 'story_segment_context',
    baseConfidence: 0.55,
    warnings: [
      'Hawwa is never named explicitly in the Quran; "زوجه" anchored to Adam window. needs_review.',
    ],
  }),
];

// ---------------------------------------------------------------------------
// 7. Combined dictionary
// ---------------------------------------------------------------------------

export const QURAN_COREFERENCE_PATTERNS: CoreferencePattern[] = [
  ...MARYAM_PATTERNS,
  ...ZAKARIYYA_PATTERNS,
  ...MUSA_PATTERNS,
  ...KAHF_PATTERNS,
  ...BILQIS_PATTERNS,
  ...ADAM_PATTERNS,
];

export function getPatternById(patternId: string): CoreferencePattern | undefined {
  return QURAN_COREFERENCE_PATTERNS.find((p) => p.patternId === patternId);
}
