#!/usr/bin/env npx tsx
/**
 * Phase X2 — Build story pages for the prophets that lack one.
 *
 * Inputs:
 *   - frontend/src/data/generated/quranProphetsAtlas.json
 *   - frontend/src/data/quranProphetSeeds.ts (for spelling / aliases)
 *
 * Output:
 *   - frontend/src/data/generated/quranProphetStoryPages.json
 *   - docs/generated/missing-prophet-story-pages-summary.md
 *
 * Safety rules:
 *   - Never invent ayah references; every section MUST be backed by
 *     ayahs already present in the prophet's atlas profile.
 *   - Compact-profile prophets keep their `sectionType` = "limited_mentions".
 *   - Muhammad ﷺ uses `pageType = "mission_summary"` with the
 *     not-full-biography warning.
 *   - Every section is `reviewStatus: "needs_review"` and
 *     `humanReviewRequired: true`.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';

import type {
  ProphetStoryPage,
  ProphetStoryPageType,
  ProphetStoryReference,
  ProphetStoryReferenceLinkType,
  ProphetStorySection,
  ProphetStorySectionType,
  ProphetStoryPagesFile,
  ChronologyNote,
  QuranReference,
} from '../frontend/src/types/quranProphetStoryPage';
import {
  PHASE_X2_REQUIRED_PROPHET_IDS,
  COMPACT_PROFILE_PROPHET_IDS,
  MISSION_SUMMARY_PROPHET_IDS,
  PROPHET_STORY_LINK_CONFIDENCE,
  MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_AR,
  MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_EN,
  LIMITED_QURAN_MENTIONS_WARNING_AR,
  LIMITED_QURAN_MENTIONS_WARNING_EN,
} from '../frontend/src/types/quranProphetStoryPage';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetsAtlas.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranProphetStoryPages.json');
const OUT_MD = join(ROOT, 'docs/generated/missing-prophet-story-pages-summary.md');
const VERSION = '1.0.0';

// ---------------------------------------------------------------------------
// Load atlas
// ---------------------------------------------------------------------------

if (!existsSync(ATLAS_PATH)) {
  throw new Error(`Run scripts/build-quran-prophets-atlas.ts first; missing ${ATLAS_PATH}`);
}
const atlas = JSON.parse(readFileSync(ATLAS_PATH, 'utf-8'));
const profileById = new Map<string, any>();
for (const p of atlas.profiles) profileById.set(p.prophetId, p);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function ref(
  surahNumber: number,
  ayahNumber: number,
  linkType: ProphetStoryReferenceLinkType,
  sourceIds: string[] = ['quran_uthmani_cloud'],
): ProphetStoryReference {
  return {
    surahNumber,
    ayahStart: ayahNumber,
    linkType,
    confidence: PROPHET_STORY_LINK_CONFIDENCE[linkType],
    sourceIds,
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  };
}

function quranRef(s: number, a: number, e?: number): QuranReference {
  return e ? { surahNumber: s, ayahStart: a, ayahEnd: e } : { surahNumber: s, ayahStart: a };
}

function section(
  prophetId: string,
  i: number,
  type: ProphetStorySectionType,
  labelAr: string,
  labelEn: string,
  ayahReferences: QuranReference[],
  opts?: { summaryAr?: string; summaryEn?: string; warnings?: string[] },
): ProphetStorySection {
  return {
    sectionId: `${prophetId}:section:${i + 1}`,
    labelArabic: labelAr,
    labelEnglish: labelEn,
    ayahReferences,
    sectionType: type,
    summaryArabic: opts?.summaryAr,
    summaryEnglish: opts?.summaryEn,
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: opts?.warnings ?? [],
  };
}

function pickAyahs(
  profile: any,
  surahNumbers: number[],
  limit = 20,
): QuranReference[] {
  const allowed = new Set(surahNumbers);
  const refs: QuranReference[] = [];
  for (const m of profile.explicitMentions ?? []) {
    if (allowed.size === 0 || allowed.has(m.surahNumber)) {
      refs.push({ surahNumber: m.surahNumber, ayahStart: m.ayahNumber });
    }
    if (refs.length >= limit) break;
  }
  return refs;
}

function familyEntityList(profile: any): string[] {
  const fam = new Set<string>();
  for (const r of profile.relatedProphets ?? []) {
    if (r.relationType === 'family_relation') fam.add(r.targetProphetId);
  }
  return Array.from(fam);
}

function explicitRefs(profile: any): ProphetStoryReference[] {
  return (profile.explicitMentions ?? [])
    .slice(0, 30)
    .map((m: any) => ref(m.surahNumber, m.ayahNumber, 'explicit_name'));
}

function entitiesOfType(profile: any, prefix: string): string[] {
  return (profile.relatedEntities ?? []).filter((e: string) => e.startsWith(prefix));
}

// ---------------------------------------------------------------------------
// Section builders per missing prophet
// ---------------------------------------------------------------------------

function buildIshaq(profile: any): ProphetStoryPage {
  const sections: ProphetStorySection[] = [];

  const familyRefs = pickAyahs(profile, [2, 3, 6, 11, 14, 19, 21, 29, 37, 38], 12);
  if (familyRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'birth_or_family',
        'النسب: ابن إبراهيم وأبو يعقوب',
        'Lineage: son of Ibrahim, father of Yaqub',
        familyRefs,
        {
          summaryAr:
            'يُذكر إسحاق ضمن سلسلة الذرية النبوية: ابنُ إبراهيم وأبو يعقوب، في آيات تتحدث عن العهد والميثاق والذرّية المباركة.',
          summaryEn:
            'Ishaq appears in the prophetic-lineage passages: son of Ibrahim and father of Yaqub, in ayahs about covenant, oath, and blessed progeny.',
        },
      ),
    );
  }

  const annunRefs = pickAyahs(profile, [11], 8);
  if (annunRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'miracle_or_sign',
        'بشارة الميلاد لإبراهيم وسارة',
        'Glad tidings of his birth to Ibrahim and Sarah',
        annunRefs,
        {
          summaryAr:
            'بشّر الملائكة إبراهيم وسارة بإسحاق ومن وراء إسحاق يعقوب — حدثٌ آية على رحمة الله وقدرته.',
          summaryEn:
            'Angels announced Ishaq, and beyond Ishaq Yaqub, to Ibrahim and Sarah — a sign of divine mercy and power.',
        },
      ),
    );
  }

  return {
    storyPageId: 'storypage_ishaq',
    prophetId: profile.prophetId,
    titleArabic: 'إسحاق عليه السلام',
    titleEnglish: 'Ishaq (Isaac)',
    pageType: 'full_story',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_ibrahim', 'prophet_yaqub', 'prophet_yusuf'],
    relatedFigures: ['figure_sarah'],
    relatedPlaces: [],
    relatedNations: [],
    relatedObjects: [],
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [
      {
        chronologyType: 'story_world_guided',
        noteArabic: 'يقع زمن إسحاق بعد إبراهيم وقبل يعقوب ضمن قراءة إرشادية.',
        noteEnglish: 'Ishaq is placed after Ibrahim and before Yaqub in the guided reading order.',
        certainty: 'medium',
        sourceIds: ['quran_uthmani_cloud'],
        reviewStatus: 'needs_review',
      },
    ],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: ['AI-assisted summary; needs scholarly review.'],
  };
}

function buildYaqub(profile: any): ProphetStoryPage {
  const sections: ProphetStorySection[] = [];

  const lineageRefs = pickAyahs(profile, [2, 3, 4, 6, 11, 19, 21, 29, 38], 12);
  if (lineageRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'birth_or_family',
        'النسب: ابن إسحاق وأبو يوسف',
        'Lineage: son of Ishaq, father of Yusuf',
        lineageRefs,
        {
          summaryAr:
            'يعقوب — المسمّى إسرائيل — يرد في آيات النسب والميثاق، أبٌ ليوسف وحفيدٌ لإبراهيم.',
          summaryEn:
            'Yaqub — called Israel — appears in ayahs of lineage and covenant, father of Yusuf and grandson of Ibrahim.',
        },
      ),
    );
  }

  const yusufRefs = pickAyahs(profile, [12], 12);
  if (yusufRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'dialogue',
        'في قصة يوسف: الحوار مع أبنائه والحزن والصبر',
        'In Yusuf\'s story: dialogue with his sons, grief, and patience',
        yusufRefs,
        {
          summaryAr:
            'يعقوب في سورة يوسف: التحذير من تأويل الرؤيا، الحزن على يوسف، الصبر الجميل، ولقاء الإيمان والرضى في الختام.',
          summaryEn:
            'Yaqub in Surah Yusuf: warning at the dream, grief over Yusuf, beautiful patience, and the closing reunion in faith.',
          warnings: [
            'Coreference within Surah Yusuf is reviewer-territory; needs scholarly verification.',
          ],
        },
      ),
    );
  }

  return {
    storyPageId: 'storypage_yaqub',
    prophetId: profile.prophetId,
    titleArabic: 'يعقوب عليه السلام',
    titleEnglish: 'Yaqub (Jacob)',
    pageType: 'full_story',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_ishaq', 'prophet_yusuf', 'prophet_ibrahim'],
    relatedFigures: [],
    relatedPlaces: [],
    relatedNations: [],
    relatedObjects: [],
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [
      {
        chronologyType: 'story_world_guided',
        noteArabic: 'يعقوب بعد إسحاق وقبل يوسف ضمن قراءة إرشادية.',
        noteEnglish: 'Yaqub follows Ishaq and precedes Yusuf in the guided reading order.',
        certainty: 'medium',
        sourceIds: ['quran_uthmani_cloud'],
        reviewStatus: 'needs_review',
      },
    ],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: ['AI-assisted summary; needs scholarly review.'],
  };
}

function buildHarun(profile: any): ProphetStoryPage {
  const sections: ProphetStorySection[] = [];

  const callRefs = pickAyahs(profile, [20, 26], 12);
  if (callRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'mission',
        'البعثة مع موسى',
        'Joint mission with Musa',
        callRefs,
        {
          summaryAr:
            'بُعث هارون مع أخيه موسى إلى فرعون وآل فرعون، وزيرًا في الرسالة كما طلب موسى من ربه.',
          summaryEn:
            'Harun was sent with his brother Musa to Pharaoh and his people, a wazir in the message as Musa asked of his Lord.',
        },
      ),
    );
  }

  const peopleRefs = pickAyahs(profile, [7, 10, 26, 28], 10);
  if (peopleRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'people_or_nation',
        'مع فرعون وبني إسرائيل',
        'With Pharaoh and Bani Israel',
        peopleRefs,
        {
          summaryAr:
            'مواجهة فرعون وآله، ودعوة بني إسرائيل، تدور مع موسى وهارون في آيات متعددة.',
          summaryEn:
            'Confronting Pharaoh and his people, and calling Bani Israel — appearing alongside Musa across multiple ayahs.',
        },
      ),
    );
  }

  const calfRefs = pickAyahs(profile, [7, 20], 8);
  if (calfRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'trial',
        'محنة العجل في غياب موسى',
        'The trial of the calf in Musa\'s absence',
        calfRefs,
        {
          summaryAr:
            'يبيّن القرآن دور هارون عند فتنة العجل ودفاعَه عن أمانة موسى وحرصه على وحدة بني إسرائيل.',
          summaryEn:
            'The Quran describes Harun\'s stance during the calf trial, his defence of Musa\'s trust, and his concern for the unity of Bani Israel.',
        },
      ),
    );
  }

  return {
    storyPageId: 'storypage_harun',
    prophetId: profile.prophetId,
    titleArabic: 'هارون عليه السلام',
    titleEnglish: 'Harun (Aaron)',
    pageType: 'full_story',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_musa'],
    relatedFigures: ['figure_firawn'],
    relatedPlaces: entitiesOfType(profile, 'entity_place_'),
    relatedNations: entitiesOfType(profile, 'entity_people_'),
    relatedObjects: entitiesOfType(profile, 'entity_object_'),
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [
      {
        chronologyType: 'story_world_guided',
        noteArabic: 'تتزامن قصة هارون مع موسى في زمن فرعون.',
        noteEnglish: 'Harun\'s story coincides with Musa\'s in the time of Pharaoh.',
        certainty: 'medium',
        sourceIds: ['quran_uthmani_cloud'],
        reviewStatus: 'needs_review',
      },
    ],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: ['AI-assisted summary; needs scholarly review.'],
  };
}

function buildDhulKifl(profile: any): ProphetStoryPage {
  // Compact profile — Quran detail is sparse.
  const refs = pickAyahs(profile, [21, 38], 4);
  const sections: ProphetStorySection[] = [
    section(
      profile.prophetId,
      0,
      'limited_mentions',
      'ذكر قرآني محدود',
      'Limited Quranic mention',
      refs,
      {
        summaryAr:
          'يَرِدُ ذو الكفل في القرآن ضمن قائمة الصابرين والأخيار، دون تفصيل قصصي.',
        summaryEn:
          'Dhul-Kifl appears in the Quran within lists of the patient and the righteous, without narrative detail.',
        warnings: [LIMITED_QURAN_MENTIONS_WARNING_AR, LIMITED_QURAN_MENTIONS_WARNING_EN],
      },
    ),
  ];
  return {
    storyPageId: 'storypage_dhulkifl',
    prophetId: profile.prophetId,
    titleArabic: 'ذو الكفل عليه السلام',
    titleEnglish: 'Dhul-Kifl',
    pageType: 'compact_profile',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_ayyub', 'prophet_alyasa'],
    relatedFigures: [],
    relatedPlaces: [],
    relatedNations: [],
    relatedObjects: [],
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: [
      LIMITED_QURAN_MENTIONS_WARNING_AR,
      LIMITED_QURAN_MENTIONS_WARNING_EN,
      'AI-assisted summary; needs scholarly review.',
    ],
  };
}

function buildIlyas(profile: any): ProphetStoryPage {
  const sections: ProphetStorySection[] = [];

  const callRefs = pickAyahs(profile, [37], 12);
  if (callRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'mission',
        'دعوة إلى التوحيد ومواجهة عبادة "بعل"',
        'Call to tawhid and confrontation with the worship of Ba\'l',
        callRefs,
        {
          summaryAr:
            'بُعث إلياس إلى قومه يدعوهم إلى عبادة الله وحده، ويحذرهم من عبادة "بعل"، في مقطعٍ من سورة الصافات.',
          summaryEn:
            'Ilyas was sent to his people calling them to worship Allah alone and warning against the worship of "Ba\'l", in a passage of Surah As-Saffat.',
        },
      ),
    );
  }

  const listRefs = pickAyahs(profile, [6], 4);
  if (listRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'relation_to_other_prophet',
        'ضمن سلسلة الأنبياء',
        'Within the prophetic sequence',
        listRefs,
        {
          summaryAr:
            'ذكر إلياس في سورة الأنعام ضمن قائمة الأنبياء الذين هداهم الله.',
          summaryEn:
            'Ilyas appears in Surah Al-An\'am within the list of prophets whom Allah guided.',
        },
      ),
    );
  }

  return {
    storyPageId: 'storypage_ilyas',
    prophetId: profile.prophetId,
    titleArabic: 'إلياس عليه السلام',
    titleEnglish: 'Ilyas (Elijah)',
    pageType: 'full_story',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_alyasa'],
    relatedFigures: [],
    relatedPlaces: [],
    relatedNations: [],
    relatedObjects: [],
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: ['AI-assisted summary; needs scholarly review.'],
  };
}

function buildAlYasa(profile: any): ProphetStoryPage {
  const refs = pickAyahs(profile, [6, 38], 4);
  const sections: ProphetStorySection[] = [
    section(
      profile.prophetId,
      0,
      'limited_mentions',
      'ذكر قرآني محدود',
      'Limited Quranic mention',
      refs,
      {
        summaryAr:
          'ذُكر اليسع في سورتي الأنعام وص ضمن قائمة الأنبياء الأخيار، دون تفصيل قصصي.',
        summaryEn:
          'Al-Yasa appears in Surahs Al-An\'am and Saad within lists of righteous prophets, without narrative detail.',
        warnings: [LIMITED_QURAN_MENTIONS_WARNING_AR, LIMITED_QURAN_MENTIONS_WARNING_EN],
      },
    ),
  ];
  return {
    storyPageId: 'storypage_alyasa',
    prophetId: profile.prophetId,
    titleArabic: 'اليسع عليه السلام',
    titleEnglish: 'Al-Yasa (Elisha)',
    pageType: 'compact_profile',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_ilyas', 'prophet_dhulkifl'],
    relatedFigures: [],
    relatedPlaces: [],
    relatedNations: [],
    relatedObjects: [],
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: [
      LIMITED_QURAN_MENTIONS_WARNING_AR,
      LIMITED_QURAN_MENTIONS_WARNING_EN,
      'AI-assisted summary; needs scholarly review.',
    ],
  };
}

function buildSulayman(profile: any): ProphetStoryPage {
  const sections: ProphetStorySection[] = [];

  const lineage = pickAyahs(profile, [2, 4, 6, 21, 38], 10);
  if (lineage.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'birth_or_family',
        'النسب: ابن داود',
        'Lineage: son of Dawud',
        lineage,
        {
          summaryAr:
            'سليمان ابن داود، آتاه الله الملك والحكمة، وفضّله بآياتٍ كريمة.',
          summaryEn:
            'Sulayman, son of Dawud, was given kingdom and wisdom and was singled out by Allah\'s grace.',
        },
      ),
    );
  }

  const naml = pickAyahs(profile, [27], 12);
  if (naml.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'miracle_or_sign',
        'في سورة النمل: النملة والهدهد',
        'In Surah An-Naml: the ant and the hoopoe',
        naml,
        {
          summaryAr:
            'في سورة النمل: كلام النملة، وغيبة الهدهد، ونبأ سبأ وملكتها، ودعوة قومها إلى الإيمان.',
          summaryEn:
            'In Surah An-Naml: the speech of the ant, the absence of the hoopoe, the news from Sheba and its queen, and the call of her people to faith.',
        },
      ),
    );
  }

  const saba = pickAyahs(profile, [34, 38], 8);
  if (saba.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'people_or_nation',
        'سبأ والريح والجن',
        'Saba, the wind, and the jinn',
        saba,
        {
          summaryAr:
            'سُخّرت لسليمان الريح والجنُّ يعملون له، ومُلكٌ لا ينبغي لأحدٍ من بعده.',
          summaryEn:
            'The wind was placed under Sulayman\'s command, and jinn worked for him — a kingdom singular in its kind.',
        },
      ),
    );
  }

  return {
    storyPageId: 'storypage_sulayman',
    prophetId: profile.prophetId,
    titleArabic: 'سليمان عليه السلام',
    titleEnglish: 'Sulayman (Solomon)',
    pageType: 'full_story',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_dawud'],
    relatedFigures: ['figure_bilqis'],
    relatedPlaces: entitiesOfType(profile, 'entity_place_'),
    relatedNations: entitiesOfType(profile, 'entity_people_'),
    relatedObjects: entitiesOfType(profile, 'entity_object_'),
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [
      {
        chronologyType: 'story_world_guided',
        noteArabic: 'سليمان بعد داود في القراءة الإرشادية.',
        noteEnglish: 'Sulayman follows Dawud in the guided reading order.',
        certainty: 'medium',
        sourceIds: ['quran_uthmani_cloud'],
        reviewStatus: 'needs_review',
      },
    ],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: ['AI-assisted summary; needs scholarly review.'],
  };
}

function buildIsmail(profile: any): ProphetStoryPage {
  const sections: ProphetStorySection[] = [];

  const familyRefs = pickAyahs(profile, [2, 3, 4, 6, 14, 19, 21, 38], 12);
  if (familyRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'birth_or_family',
        'النسب: ابن إبراهيم',
        'Lineage: son of Ibrahim',
        familyRefs,
        {
          summaryAr:
            'إسماعيل ابن إبراهيم، يُذكر في آيات النسب والميثاق والقربان وبناء البيت.',
          summaryEn:
            'Ismail, son of Ibrahim, appears in ayahs about lineage, covenant, sacrifice, and the building of the Kaaba.',
        },
      ),
    );
  }

  const buildingRefs = pickAyahs(profile, [2], 8);
  if (buildingRefs.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'mission',
        'بناء البيت مع إبراهيم',
        'Building the Kaaba with Ibrahim',
        buildingRefs,
        {
          summaryAr:
            'يُذكر بناء البيت العتيق بإبراهيم وإسماعيل في سورة البقرة، ودعاؤهما عند رفع القواعد.',
          summaryEn:
            'The building of the Sacred House by Ibrahim and Ismail is mentioned in Surah Al-Baqarah, with their du\'a as they raised the foundations.',
        },
      ),
    );
  }

  const saffat = pickAyahs(profile, [37], 6);
  if (saffat.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'trial',
        'الذبح في سورة الصافات',
        'The sacrifice in Surah As-Saffat',
        saffat,
        {
          summaryAr:
            'في سورة الصافات: ابتلاء إبراهيم وإسماعيل بالذبح وامتثالهما واستبداله بذبحٍ عظيم.',
          summaryEn:
            'In Surah As-Saffat: the trial of Ibrahim and Ismail with the sacrifice, their submission, and the great ransom.',
        },
      ),
    );
  }

  return {
    storyPageId: 'storypage_ismail',
    prophetId: profile.prophetId,
    titleArabic: 'إسماعيل عليه السلام',
    titleEnglish: 'Ismail (Ishmael)',
    pageType: 'full_story',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: ['prophet_ibrahim', 'prophet_ishaq'],
    relatedFigures: [],
    relatedPlaces: ['entity_place_makkah'],
    relatedNations: [],
    relatedObjects: [],
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [
      {
        chronologyType: 'story_world_guided',
        noteArabic: 'إسماعيل بعد إبراهيم في القراءة الإرشادية.',
        noteEnglish: 'Ismail follows Ibrahim in the guided reading order.',
        certainty: 'medium',
        sourceIds: ['quran_uthmani_cloud'],
        reviewStatus: 'needs_review',
      },
    ],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: ['AI-assisted summary; needs scholarly review.'],
  };
}

function buildMuhammad(profile: any): ProphetStoryPage {
  const explicit = pickAyahs(profile, [3, 33, 47, 48, 61], 5);
  const sections: ProphetStorySection[] = [
    section(
      profile.prophetId,
      0,
      'mission',
      'البعثة الخاتمة',
      'The final mission',
      explicit,
      {
        summaryAr:
          'هذه الصفحة تعرض الشواهد القرآنية الصريحة لاسم النبي ﷺ ولا تستوعب سيرته كاملة.',
        summaryEn:
          'This page surfaces the explicit Quranic name-mentions of the Prophet ﷺ and is not a full biographical account.',
        warnings: [
          MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_AR,
          MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_EN,
        ],
      },
    ),
  ];

  // Continuity-with-previous-prophets — surfaced only via the relations
  // already detected (no invented evidence).
  const continuityTargets = (profile.relatedProphets ?? [])
    .filter((r: any) => r.targetProphetId !== 'prophet_muhammad')
    .map((r: any) => r.targetProphetId);
  if (continuityTargets.length > 0) {
    sections.push(
      section(
        profile.prophetId,
        sections.length,
        'relation_to_other_prophet',
        'استمرار الرسالة مع الأنبياء السابقين',
        'Continuity with previous prophets',
        explicit,
        {
          summaryAr:
            'يقرّر القرآن استمرار الرسالة، ويصل دعوة النبي ﷺ بدعوات سابقيه من الأنبياء.',
          summaryEn:
            'The Quran affirms the continuity of the message, linking the Prophet ﷺ to earlier prophets.',
          warnings: ['Coreference-resolved generic-prophet references are deferred to a future scan.'],
        },
      ),
    );
  }

  return {
    storyPageId: 'storypage_muhammad',
    prophetId: profile.prophetId,
    titleArabic: 'محمد ﷺ — ملف الرسالة القرآني',
    titleEnglish: 'Muhammad ﷺ — Quranic mission profile',
    pageType: 'mission_summary',
    quranReferences: explicitRefs(profile),
    storySections: sections,
    relatedProphets: continuityTargets,
    relatedFigures: ['figure_maryam'],
    relatedPlaces: [],
    relatedNations: entitiesOfType(profile, 'entity_people_'),
    relatedObjects: [],
    relatedTopics: profile.relatedTopics ?? [],
    chronologyNotes: [
      {
        chronologyType: 'mushaf_order',
        noteArabic: 'الترتيب المصحفي للآيات الخمس الصريحة موثوق.',
        noteEnglish: 'Mushaf order for the 5 explicit name-ayahs is reliable.',
        certainty: 'high',
        sourceIds: ['quran_uthmani_cloud'],
        reviewStatus: 'needs_review',
      },
    ],
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: [
      MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_AR,
      MUHAMMAD_PAGE_NOT_FULL_BIOGRAPHY_WARNING_EN,
      'seerah_deferred: detailed biography is deferred to a separate module.',
    ],
  };
}

// ---------------------------------------------------------------------------
// Dispatch
// ---------------------------------------------------------------------------

const builders: Record<string, (profile: any) => ProphetStoryPage> = {
  prophet_ishaq: buildIshaq,
  prophet_yaqub: buildYaqub,
  prophet_harun: buildHarun,
  prophet_dhulkifl: buildDhulKifl,
  prophet_ilyas: buildIlyas,
  prophet_alyasa: buildAlYasa,
  prophet_sulayman: buildSulayman,
  prophet_muhammad: buildMuhammad,
  prophet_ismail: buildIsmail,
};

const pages: ProphetStoryPage[] = [];
const warnings: string[] = [];
for (const pid of PHASE_X2_REQUIRED_PROPHET_IDS) {
  const profile = profileById.get(pid);
  if (!profile) {
    warnings.push(`missing_profile: ${pid} is not present in the atlas; cannot build a story page.`);
    continue;
  }
  const builder = builders[pid];
  if (!builder) {
    warnings.push(`no_builder: ${pid} has no story-page builder.`);
    continue;
  }
  const page = builder(profile);
  // Apply automatic pageType guards for compact / mission
  if (COMPACT_PROFILE_PROPHET_IDS.has(pid)) page.pageType = 'compact_profile';
  if (MISSION_SUMMARY_PROPHET_IDS.has(pid)) page.pageType = 'mission_summary';
  pages.push(page);
}

// ---------------------------------------------------------------------------
// Page-type breakdown
// ---------------------------------------------------------------------------

const breakdown: Partial<Record<ProphetStoryPageType, number>> = {};
for (const p of pages) {
  breakdown[p.pageType] = (breakdown[p.pageType] ?? 0) + 1;
}

// ---------------------------------------------------------------------------
// Write outputs
// ---------------------------------------------------------------------------

const out: ProphetStoryPagesFile = {
  version: VERSION,
  generatedAt: new Date().toISOString(),
  totalPages: pages.length,
  pageTypeBreakdown: breakdown,
  prophetIdsCovered: pages.map((p) => p.prophetId),
  pages,
  warnings,
};

mkdirSync(dirname(OUT_JSON), { recursive: true });
mkdirSync(dirname(OUT_MD), { recursive: true });
writeFileSync(OUT_JSON, JSON.stringify(out, null, 2), 'utf-8');

const md: string[] = [];
md.push('# Missing Prophet Story Pages — Build Summary');
md.push('');
md.push(`- Version: ${out.version}`);
md.push(`- Generated: ${out.generatedAt}`);
md.push(`- Pages: **${out.totalPages}**`);
md.push('');
md.push('## Per-prophet snapshot');
md.push('| Prophet | pageType | Sections | quranReferences | Warnings |');
md.push('|---|---|---:|---:|---:|');
for (const p of pages) {
  md.push(
    `| ${p.titleEnglish} | ${p.pageType} | ${p.storySections.length} | ${p.quranReferences.length} | ${p.warnings.length} |`,
  );
}
md.push('');
md.push('## Page-type breakdown');
for (const [k, v] of Object.entries(breakdown)) md.push(`- ${k}: ${v}`);
md.push('');
md.push('## Generation warnings');
if (warnings.length === 0) md.push('_None._');
else for (const w of warnings) md.push(`- ${w}`);
writeFileSync(OUT_MD, md.join('\n') + '\n', 'utf-8');

console.log(`[missing-prophet-story-pages] wrote ${pages.length} pages to ${OUT_JSON}`);
console.log(`[missing-prophet-story-pages] summary at ${OUT_MD}`);
