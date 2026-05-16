/**
 * Quran Story Chronology Seeds
 *
 * Two SEPARATE chronologies live here:
 *   1) story_world  — narrative order across prophet stories. BROAD and CAUTIOUS.
 *   2) revelation_order — order of revelation (نزول). Cited or DISPUTED.
 *
 * Rules (mirror docs/quran-story-chronology-policy.md):
 *   - Story-world chronology is broad. We do NOT pin precise dates.
 *   - Revelation order is NOT settled scholarship; every entry must cite a
 *     source or be marked `disputed`.
 *   - All entries default to `reviewStatus: 'needs_review'`. Promotion to
 *     `verified` requires reviewer sign-off and at least one sourceId.
 *
 * This file is consumed by:
 *   - scripts/build-quran-story-connection-graph.ts
 *   - scripts/validate-quran-story-chronology.ts
 *   - the UI Chronology view under /story-atlas/connections
 */

import type { ChronologyEntry } from '../types/quranStoryConnection';

// ---------------------------------------------------------------------------
// Story-world chronology
//
// This is a CAUTIOUS broad ordering of prophet narratives, grouped by
// chronological band (chronologicalGroup IDs match the seeds).
// We DO NOT claim that "Yusuf came directly after Ibrahim". We claim only
// that "Yusuf is in the patriarchs band, after Adam, before Musa".
// ---------------------------------------------------------------------------

export const STORY_WORLD_CHRONOLOGY: ChronologyEntry[] = [
  {
    chronologyType: 'story_world',
    itemId: 'chrono_primordial',
    orderIndex: 1,
    certainty: 'high',
    sourceIds: ['ibn_kathir', 'tabari'],
    notesArabic: 'البدء — قصة آدم عليه السلام',
    notesEnglish: 'Primordial — Adam (peace be upon him).',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'story_world',
    itemId: 'chrono_antediluvian',
    orderIndex: 2,
    certainty: 'high',
    sourceIds: ['ibn_kathir', 'tabari'],
    notesArabic: 'ما قبل الطوفان — إدريس ونوح عليهما السلام',
    notesEnglish: 'Antediluvian — Idris and Nuh.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'story_world',
    itemId: 'chrono_ancient_arabia',
    orderIndex: 3,
    certainty: 'medium',
    sourceIds: ['ibn_kathir', 'tabari'],
    notesArabic: 'الأنبياء في جزيرة العرب القديمة — هود وصالح وشعيب',
    notesEnglish: 'Ancient Arabian prophets — Hud, Salih, Shuayb.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'story_world',
    itemId: 'chrono_patriarchs',
    orderIndex: 4,
    certainty: 'high',
    sourceIds: ['ibn_kathir', 'tabari', 'qurtubi'],
    notesArabic: 'عصر الآباء — إبراهيم ولوط وإسماعيل وإسحاق ويعقوب ويوسف وأيوب وذو الكفل',
    notesEnglish: 'Patriarchs — Ibrahim, Lut, Ismail, Ishaq, Yaqub, Yusuf, Ayyub, Dhul-Kifl.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'story_world',
    itemId: 'chrono_israelite',
    orderIndex: 5,
    certainty: 'high',
    sourceIds: ['ibn_kathir', 'tabari', 'qurtubi'],
    notesArabic: 'بنو إسرائيل — موسى وهارون ويونس',
    notesEnglish: 'Israelite era — Musa, Harun, Yunus.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'story_world',
    itemId: 'chrono_kingdom',
    orderIndex: 6,
    certainty: 'high',
    sourceIds: ['ibn_kathir', 'tabari'],
    notesArabic: 'الملك في بني إسرائيل — داود وسليمان',
    notesEnglish: 'Kingship in Bani Israel — Dawud and Sulayman.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'story_world',
    itemId: 'chrono_late_israelite',
    orderIndex: 7,
    certainty: 'high',
    sourceIds: ['ibn_kathir', 'tabari'],
    notesArabic: 'العصر المتأخر — زكريا ويحيى وعيسى',
    notesEnglish: 'Late Israelite era — Zakariyya, Yahya, Isa.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'story_world',
    itemId: 'chrono_prophetic_era',
    orderIndex: 8,
    certainty: 'high',
    sourceIds: ['ibn_kathir'],
    notesArabic: 'العصر النبوي — محمد ﷺ',
    notesEnglish: 'Prophetic era — Muhammad ﷺ.',
    reviewStatus: 'needs_review',
  },
];

// ---------------------------------------------------------------------------
// Revelation order — DISPUTED layer
//
// Scholars differ. The Cairo edition (al-Suyuti's Itqan) lists one ordering,
// but other lists vary. We seed only a SHORT, well-known set and mark each
// as needs_review. The validator will reject any non-disputed entry that
// lacks a sourceId.
// ---------------------------------------------------------------------------

export const REVELATION_ORDER_DISPUTED_NOTE_AR =
  'هذا الترتيب تقريبي أو محل مراجعة عند وجود خلاف.';
export const REVELATION_ORDER_DISPUTED_NOTE_EN =
  'This order is approximate or requires review where scholarly disagreement exists.';

export const REVELATION_ORDER_SEEDS: ChronologyEntry[] = [
  {
    chronologyType: 'revelation_order',
    itemId: '96', // Surah Al-Alaq
    orderIndex: 1,
    certainty: 'high',
    sourceIds: ['ibn_kathir'],
    notesArabic: 'سورة العلق — أول ما نزل (إقرأ).',
    notesEnglish: 'Surah Al-Alaq — first revelation (Iqra).',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'revelation_order',
    itemId: '68',
    orderIndex: 2,
    certainty: 'medium',
    sourceIds: ['ibn_kathir'],
    notesArabic: 'سورة القلم — من أوائل ما نزل بمكة. الترتيب فيه خلاف.',
    notesEnglish: 'Surah Al-Qalam — early Makki. Order disputed.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'revelation_order',
    itemId: '73',
    orderIndex: 3,
    certainty: 'medium',
    sourceIds: ['ibn_kathir'],
    notesArabic: 'سورة المزمل — مكية مبكرة. الترتيب فيه خلاف.',
    notesEnglish: 'Surah Al-Muzzammil — early Makki. Order disputed.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'revelation_order',
    itemId: '74',
    orderIndex: 4,
    certainty: 'medium',
    sourceIds: ['ibn_kathir'],
    notesArabic: 'سورة المدثر — مكية مبكرة.',
    notesEnglish: 'Surah Al-Muddaththir — early Makki.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'revelation_order',
    itemId: '110',
    orderIndex: 113,
    certainty: 'medium',
    sourceIds: ['ibn_kathir'],
    notesArabic: 'سورة النصر — من آخر ما نزل بإجماع كثير من المفسرين.',
    notesEnglish: 'Surah An-Nasr — among the last revealed by consensus of many mufassirun.',
    reviewStatus: 'needs_review',
  },
  {
    chronologyType: 'revelation_order',
    itemId: '5',
    orderIndex: 114,
    certainty: 'disputed',
    sourceIds: ['ibn_kathir', 'qurtubi'],
    notesArabic: 'سورة المائدة — ترتيب نزولها فيه خلاف؛ بعض الآيات منها من آخر ما نزل.',
    notesEnglish: 'Surah Al-Maidah — order of revelation disputed; some ayahs among the last revealed.',
    reviewStatus: 'needs_review',
  },
];

export const QURAN_STORY_CHRONOLOGY_SEEDS: ChronologyEntry[] = [
  ...STORY_WORLD_CHRONOLOGY,
  ...REVELATION_ORDER_SEEDS,
];
