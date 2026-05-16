/**
 * Quran Story Entity Seeds — candidate detection dictionary.
 *
 * Used by the surah-by-surah scanner (scripts/scan-quran-story-connections.ts)
 * and by the connection-graph builder.
 *
 * Hard rules:
 *   - This file is a CANDIDATE-DETECTION dictionary, not approved data.
 *   - Every entry is `reviewedDictionary: false` and ships with an empty
 *     `quranReferences` list (the scanner fills it).
 *   - Aliases are written WITHOUT diacritics so the scanner can normalise
 *     ayah text and compare.
 *   - No Quran text is included anywhere in this file.
 *
 * Adding entries:
 *   - Add Arabic spellings AS THEY APPEAR in the mushaf (with and without
 *     tanwin), but drop tashkeel — the scanner strips diacritics from both
 *     the alias and the ayah before comparing.
 *   - Aliases should be specific enough to avoid common-word false positives.
 *   - When an entity has a generic common-word alias (e.g. "ant" matches
 *     "نمل"), keep it; the scanner respects per-occurrence confidence
 *     downgrades for short aliases.
 */

import type { QuranStoryEntity } from '../types/quranStoryConnection';

// ---------------------------------------------------------------------------
// Helper: shorthand factory for unreviewed seed entries.
// ---------------------------------------------------------------------------

function seed(partial: Partial<QuranStoryEntity> & {
  entityId: string;
  type: QuranStoryEntity['type'];
  labelArabic: string;
  labelEnglish: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
}): QuranStoryEntity {
  return {
    quranReferences: [],
    relatedStories: [],
    relatedEntities: [],
    relatedThemes: [],
    warnings: [],
    reviewedDictionary: false,
    ...partial,
  };
}

// ---------------------------------------------------------------------------
// 1. Prophets and messengers
// ---------------------------------------------------------------------------

export const PROPHET_SEEDS: QuranStoryEntity[] = [
  seed({
    entityId: 'entity_prophet_adam', type: 'prophet',
    labelArabic: 'آدم عليه السلام', labelEnglish: 'Adam',
    aliasesArabic: ['آدم'],
    aliasesEnglish: ['Adam'],
    transliterations: ['Adam'],
    relatedStories: ['story_adam'],
    chronologicalGroup: 'chrono_primordial',
  }),
  seed({
    entityId: 'entity_prophet_idris', type: 'prophet',
    labelArabic: 'إدريس عليه السلام', labelEnglish: 'Idris (Enoch)',
    aliasesArabic: ['إدريس', 'ادريس'],
    aliasesEnglish: ['Idris', 'Enoch'],
    transliterations: ['Idris', 'Enoch'],
    relatedStories: ['story_idris'],
    chronologicalGroup: 'chrono_antediluvian',
  }),
  seed({
    entityId: 'entity_prophet_nuh', type: 'prophet',
    labelArabic: 'نوح عليه السلام', labelEnglish: 'Nuh (Noah)',
    aliasesArabic: ['نوح', 'نوحا', 'نوحاً'],
    aliasesEnglish: ['Nuh', 'Noah'],
    transliterations: ['Nuh', 'Noah', 'Nooh'],
    relatedStories: ['story_nuh'],
    chronologicalGroup: 'chrono_antediluvian',
  }),
  seed({
    entityId: 'entity_prophet_hud', type: 'prophet',
    labelArabic: 'هود عليه السلام', labelEnglish: 'Hud',
    aliasesArabic: ['هود', 'هودا', 'هوداً'],
    aliasesEnglish: ['Hud'],
    transliterations: ['Hud'],
    relatedStories: ['story_hud'],
    chronologicalGroup: 'chrono_ancient_arabia',
  }),
  seed({
    entityId: 'entity_prophet_salih', type: 'prophet',
    labelArabic: 'صالح عليه السلام', labelEnglish: 'Salih',
    aliasesArabic: ['صالح', 'صالحا', 'صالحاً'],
    aliasesEnglish: ['Salih', 'Saleh'],
    transliterations: ['Salih', 'Saleh'],
    relatedStories: ['story_salih'],
    chronologicalGroup: 'chrono_ancient_arabia',
  }),
  seed({
    entityId: 'entity_prophet_ibrahim', type: 'prophet',
    labelArabic: 'إبراهيم عليه السلام', labelEnglish: 'Ibrahim (Abraham)',
    // Quran orthography is إِبْرَٰهِيمُ (dagger alif). After diacritic strip
    // this normalises to ابرهيم — that's the form actually present in the
    // corpus. Include the long form too in case any future source uses it.
    aliasesArabic: ['إبراهيم', 'ابراهيم', 'ابرهيم', 'الخليل'],
    aliasesEnglish: ['Ibrahim', 'Abraham', 'Khalil'],
    transliterations: ['Ibrahim', 'Abraham', 'Ibraheem'],
    relatedStories: ['story_ibrahim'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_lut', type: 'prophet',
    labelArabic: 'لوط عليه السلام', labelEnglish: 'Lut (Lot)',
    aliasesArabic: ['لوط', 'لوطا', 'لوطاً'],
    aliasesEnglish: ['Lut', 'Lot'],
    transliterations: ['Lut', 'Lot'],
    relatedStories: ['story_lut'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_ismail', type: 'prophet',
    labelArabic: 'إسماعيل عليه السلام', labelEnglish: 'Ismail (Ishmael)',
    // Quran spelling إِسْمَٰعِيلَ normalises to اسمعيل (no alif after meem).
    aliasesArabic: ['إسماعيل', 'اسماعيل', 'اسمعيل'],
    aliasesEnglish: ['Ismail', 'Ishmael'],
    transliterations: ['Ismail', 'Ishmael'],
    relatedStories: ['story_ismail'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_ishaq', type: 'prophet',
    labelArabic: 'إسحاق عليه السلام', labelEnglish: 'Ishaq (Isaac)',
    // Quran spelling إِسْحَٰقَ normalises to اسحق (no alif).
    aliasesArabic: ['إسحاق', 'اسحاق', 'اسحق'],
    aliasesEnglish: ['Ishaq', 'Isaac'],
    transliterations: ['Ishaq', 'Isaac'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_yaqub', type: 'prophet',
    labelArabic: 'يعقوب عليه السلام', labelEnglish: 'Yaqub (Jacob)',
    aliasesArabic: ['يعقوب', 'إسرائيل'],
    aliasesEnglish: ['Yaqub', 'Jacob', 'Israel'],
    transliterations: ['Yaqub', 'Jacob', 'Yaaqub'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_yusuf', type: 'prophet',
    labelArabic: 'يوسف عليه السلام', labelEnglish: 'Yusuf (Joseph)',
    aliasesArabic: ['يوسف'],
    aliasesEnglish: ['Yusuf', 'Joseph'],
    transliterations: ['Yusuf', 'Joseph', 'Yousef'],
    relatedStories: ['story_yusuf'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_shuayb', type: 'prophet',
    labelArabic: 'شعيب عليه السلام', labelEnglish: 'Shuayb (Jethro)',
    aliasesArabic: ['شعيب', 'شعيبا', 'شعيباً'],
    aliasesEnglish: ['Shuayb', 'Jethro'],
    transliterations: ['Shuayb', 'Shoaib'],
    relatedStories: ['story_shuayb'],
    chronologicalGroup: 'chrono_ancient_arabia',
  }),
  seed({
    entityId: 'entity_prophet_musa', type: 'prophet',
    labelArabic: 'موسى عليه السلام', labelEnglish: 'Musa (Moses)',
    aliasesArabic: ['موسى', 'موسٰى', 'كليم الله'],
    aliasesEnglish: ['Musa', 'Moses', 'Kalimullah'],
    transliterations: ['Musa', 'Moses', 'Moosa'],
    relatedStories: ['story_musa'],
    chronologicalGroup: 'chrono_israelite',
  }),
  seed({
    entityId: 'entity_prophet_harun', type: 'prophet',
    labelArabic: 'هارون عليه السلام', labelEnglish: 'Harun (Aaron)',
    aliasesArabic: ['هارون'],
    aliasesEnglish: ['Harun', 'Aaron'],
    transliterations: ['Harun', 'Aaron', 'Haroon'],
    chronologicalGroup: 'chrono_israelite',
  }),
  seed({
    entityId: 'entity_prophet_dawud', type: 'prophet',
    labelArabic: 'داود عليه السلام', labelEnglish: 'Dawud (David)',
    aliasesArabic: ['داود', 'داوود'],
    aliasesEnglish: ['Dawud', 'David', 'Daud'],
    transliterations: ['Dawud', 'David', 'Daoud'],
    relatedStories: ['story_dawud'],
    chronologicalGroup: 'chrono_kingdom',
  }),
  seed({
    entityId: 'entity_prophet_sulayman', type: 'prophet',
    labelArabic: 'سليمان عليه السلام', labelEnglish: 'Sulayman (Solomon)',
    // Quran spelling سُلَيْمَٰنَ normalises to سليمن.
    aliasesArabic: ['سليمان', 'سليمن'],
    aliasesEnglish: ['Sulayman', 'Solomon'],
    transliterations: ['Sulayman', 'Solomon', 'Suleiman'],
    relatedStories: ['story_bilqis'],
    chronologicalGroup: 'chrono_kingdom',
  }),
  seed({
    entityId: 'entity_prophet_ayyub', type: 'prophet',
    labelArabic: 'أيوب عليه السلام', labelEnglish: 'Ayyub (Job)',
    aliasesArabic: ['أيوب', 'ايوب'],
    aliasesEnglish: ['Ayyub', 'Job'],
    transliterations: ['Ayyub', 'Job'],
    relatedStories: ['story_ayyub'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_yunus', type: 'prophet',
    labelArabic: 'يونس عليه السلام', labelEnglish: 'Yunus (Jonah)',
    aliasesArabic: ['يونس', 'ذا النون', 'ذو النون', 'صاحب الحوت'],
    aliasesEnglish: ['Yunus', 'Jonah', 'Dhul-Nun'],
    transliterations: ['Yunus', 'Jonah'],
    relatedStories: ['story_yunus'],
    chronologicalGroup: 'chrono_israelite',
  }),
  seed({
    entityId: 'entity_prophet_zakariyya', type: 'prophet',
    labelArabic: 'زكريا عليه السلام', labelEnglish: 'Zakariyya (Zechariah)',
    aliasesArabic: ['زكريا', 'زكرياء'],
    aliasesEnglish: ['Zakariyya', 'Zechariah'],
    transliterations: ['Zakariyya', 'Zechariah'],
    relatedStories: ['story_zakariyya_yahya'],
    chronologicalGroup: 'chrono_late_israelite',
  }),
  seed({
    entityId: 'entity_prophet_yahya', type: 'prophet',
    labelArabic: 'يحيى عليه السلام', labelEnglish: 'Yahya (John)',
    aliasesArabic: ['يحيى', 'يحيىٰ'],
    aliasesEnglish: ['Yahya', 'John'],
    transliterations: ['Yahya', 'John'],
    relatedStories: ['story_zakariyya_yahya'],
    chronologicalGroup: 'chrono_late_israelite',
  }),
  seed({
    entityId: 'entity_prophet_isa', type: 'prophet',
    labelArabic: 'عيسى عليه السلام', labelEnglish: 'Isa (Jesus)',
    aliasesArabic: ['عيسى', 'المسيح', 'ابن مريم'],
    aliasesEnglish: ['Isa', 'Jesus', 'Christ', 'Messiah', 'Son of Mary'],
    transliterations: ['Isa', 'Jesus'],
    relatedStories: ['story_isa'],
    chronologicalGroup: 'chrono_late_israelite',
  }),
  seed({
    entityId: 'entity_prophet_dhulkifl', type: 'prophet',
    labelArabic: 'ذو الكفل عليه السلام', labelEnglish: 'Dhul-Kifl',
    aliasesArabic: ['ذا الكفل', 'ذو الكفل'],
    aliasesEnglish: ['Dhul-Kifl'],
    transliterations: ['Dhul-Kifl'],
    chronologicalGroup: 'chrono_patriarchs',
  }),
  seed({
    entityId: 'entity_prophet_muhammad', type: 'prophet',
    labelArabic: 'محمد ﷺ', labelEnglish: 'Muhammad ﷺ',
    aliasesArabic: ['محمد', 'أحمد', 'الرسول'],
    aliasesEnglish: ['Muhammad', 'Ahmad'],
    transliterations: ['Muhammad', 'Mohammad', 'Ahmed'],
    chronologicalGroup: 'chrono_prophetic_era',
    warnings: [
      'Alias "الرسول" is generic and frequently matches non-Muhammad usages; downgrade confidence in scanner.',
    ],
  }),
];

// ---------------------------------------------------------------------------
// 2. Other named persons & figures
// ---------------------------------------------------------------------------

export const PERSON_SEEDS: QuranStoryEntity[] = [
  seed({
    entityId: 'entity_person_maryam', type: 'person',
    labelArabic: 'مريم عليها السلام', labelEnglish: 'Maryam (Mary)',
    aliasesArabic: ['مريم'],
    aliasesEnglish: ['Maryam', 'Mary'],
    transliterations: ['Maryam', 'Mary'],
    relatedStories: ['story_maryam', 'story_isa'],
  }),
  seed({
    entityId: 'entity_person_firawn', type: 'person',
    labelArabic: 'فرعون', labelEnglish: 'Firawn (Pharaoh)',
    aliasesArabic: ['فرعون'],
    aliasesEnglish: ['Firawn', 'Pharaoh'],
    transliterations: ['Firawn', 'Pharaoh', 'Firaun'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_person_haman', type: 'person',
    labelArabic: 'هامان', labelEnglish: 'Haman',
    aliasesArabic: ['هامان'],
    aliasesEnglish: ['Haman'],
    transliterations: ['Haman'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_person_qarun', type: 'person',
    labelArabic: 'قارون', labelEnglish: 'Qarun (Korah)',
    aliasesArabic: ['قارون'],
    aliasesEnglish: ['Qarun', 'Korah'],
    transliterations: ['Qarun', 'Korah'],
    relatedStories: ['story_qarun'],
  }),
  seed({
    entityId: 'entity_person_talut', type: 'person',
    labelArabic: 'طالوت', labelEnglish: 'Talut (Saul)',
    aliasesArabic: ['طالوت'],
    aliasesEnglish: ['Talut', 'Saul'],
    transliterations: ['Talut', 'Saul'],
    relatedStories: ['story_talut_jalut'],
  }),
  seed({
    entityId: 'entity_person_jalut', type: 'person',
    labelArabic: 'جالوت', labelEnglish: 'Jalut (Goliath)',
    aliasesArabic: ['جالوت'],
    aliasesEnglish: ['Jalut', 'Goliath'],
    transliterations: ['Jalut', 'Goliath'],
    relatedStories: ['story_talut_jalut'],
  }),
  seed({
    entityId: 'entity_person_bilqis', type: 'person',
    labelArabic: 'بلقيس', labelEnglish: 'Bilqis (Queen of Sheba)',
    aliasesArabic: ['بلقيس', 'ملكة سبأ'],
    aliasesEnglish: ['Bilqis', 'Queen of Sheba'],
    transliterations: ['Bilqis', 'Balqis'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_person_dhulqarnayn', type: 'person',
    labelArabic: 'ذو القرنين', labelEnglish: 'Dhul-Qarnayn',
    aliasesArabic: ['ذو القرنين', 'ذا القرنين'],
    aliasesEnglish: ['Dhul-Qarnayn'],
    transliterations: ['Dhul-Qarnayn'],
    relatedStories: ['story_dhulqarnayn'],
  }),
  seed({
    entityId: 'entity_person_luqman', type: 'person',
    labelArabic: 'لقمان الحكيم', labelEnglish: 'Luqman the Wise',
    // Quran spelling لُقْمَٰنَ normalises to لقمن.
    aliasesArabic: ['لقمان', 'لقمن'],
    aliasesEnglish: ['Luqman'],
    transliterations: ['Luqman'],
    relatedStories: ['story_luqman'],
  }),
  seed({
    entityId: 'entity_person_iblis', type: 'person',
    labelArabic: 'إبليس', labelEnglish: 'Iblis (Satan)',
    aliasesArabic: ['إبليس', 'الشيطان', 'الشّيطان'],
    aliasesEnglish: ['Iblis', 'Satan', 'Devil'],
    transliterations: ['Iblis', 'Satan'],
    warnings: ['"الشيطان" is generic; scanner downgrades alias confidence for it.'],
  }),
  seed({
    entityId: 'entity_person_zayd', type: 'person',
    labelArabic: 'زيد', labelEnglish: 'Zayd ibn Haritha',
    aliasesArabic: ['زيد', 'زيدا', 'زيداً'],
    aliasesEnglish: ['Zayd', 'Zaid'],
    transliterations: ['Zayd'],
    warnings: ['Only one explicit naming in Surah Al-Ahzab (33:37); other matches need review.'],
  }),
  seed({
    entityId: 'entity_person_abu_lahab', type: 'person',
    labelArabic: 'أبو لهب', labelEnglish: 'Abu Lahab',
    aliasesArabic: ['أبي لهب'],
    aliasesEnglish: ['Abu Lahab'],
    transliterations: ['Abu Lahab'],
    warnings: ['Only one explicit naming in Surah Al-Masad (111:1).'],
  }),
  seed({
    entityId: 'entity_person_hawwa', type: 'person',
    labelArabic: 'حواء', labelEnglish: 'Hawwa (Eve)',
    aliasesArabic: ['زوجه', 'حواء'],
    aliasesEnglish: ['Hawwa', 'Eve'],
    transliterations: ['Hawwa', 'Eve'],
    relatedStories: ['story_adam'],
    warnings: ['Hawwa is never named explicitly in the Quran; "زوجه" matches are needs_review.'],
  }),
  seed({
    entityId: 'entity_person_aziz', type: 'person',
    labelArabic: 'العزيز', labelEnglish: 'Al-Aziz of Egypt',
    aliasesArabic: ['العزيز', 'عزيز مصر'],
    aliasesEnglish: ['Aziz of Egypt'],
    transliterations: ['Aziz'],
    relatedStories: ['story_yusuf'],
    warnings: ['"العزيز" is also a Divine Name; scanner downgrades confidence outside Surah Yusuf.'],
  }),
  seed({
    entityId: 'entity_person_imran', type: 'person',
    labelArabic: 'عمران', labelEnglish: 'Imran',
    aliasesArabic: ['عمران', 'آل عمران'],
    aliasesEnglish: ['Imran'],
    transliterations: ['Imran'],
  }),
];

// ---------------------------------------------------------------------------
// 3. Peoples / nations
// ---------------------------------------------------------------------------

export const PEOPLE_SEEDS: QuranStoryEntity[] = [
  seed({
    entityId: 'entity_people_bani_israel', type: 'people_or_nation',
    labelArabic: 'بنو إسرائيل', labelEnglish: 'Children of Israel',
    aliasesArabic: ['بني إسرائيل', 'بنو إسرائيل', 'إسرائيل'],
    aliasesEnglish: ['Bani Israel', 'Children of Israel', 'Israelites'],
    transliterations: ['Bani Israel'],
  }),
  seed({
    entityId: 'entity_people_aad', type: 'people_or_nation',
    labelArabic: 'قوم عاد', labelEnglish: 'People of Aad',
    aliasesArabic: ['عاد', 'عادا', 'عاداً'],
    aliasesEnglish: ['Aad', 'Ad'],
    transliterations: ['Aad'],
    relatedStories: ['story_hud'],
  }),
  seed({
    entityId: 'entity_people_thamud', type: 'people_or_nation',
    labelArabic: 'قوم ثمود', labelEnglish: 'People of Thamud',
    aliasesArabic: ['ثمود', 'ثمودا', 'ثموداً'],
    aliasesEnglish: ['Thamud'],
    transliterations: ['Thamud'],
    relatedStories: ['story_salih'],
  }),
  seed({
    entityId: 'entity_people_madyan', type: 'people_or_nation',
    labelArabic: 'أهل مدين', labelEnglish: 'People of Madyan',
    aliasesArabic: ['مدين', 'أصحاب الأيكة'],
    aliasesEnglish: ['Madyan', 'Midian'],
    transliterations: ['Madyan'],
    relatedStories: ['story_shuayb'],
  }),
  seed({
    entityId: 'entity_people_qawm_nuh', type: 'people_or_nation',
    labelArabic: 'قوم نوح', labelEnglish: 'People of Nuh',
    aliasesArabic: ['قوم نوح'],
    aliasesEnglish: ['People of Noah'],
    relatedStories: ['story_nuh'],
  }),
  seed({
    entityId: 'entity_people_qawm_lut', type: 'people_or_nation',
    labelArabic: 'قوم لوط', labelEnglish: 'People of Lut',
    aliasesArabic: ['قوم لوط', 'المؤتفكات', 'المؤتفكة'],
    aliasesEnglish: ['People of Lot', 'Sodom'],
    relatedStories: ['story_lut'],
  }),
  seed({
    entityId: 'entity_people_ashab_kahf', type: 'people_or_nation',
    labelArabic: 'أصحاب الكهف', labelEnglish: 'People of the Cave',
    aliasesArabic: ['أصحاب الكهف', 'الكهف', 'الفتية'],
    aliasesEnglish: ['People of the Cave', 'Companions of the Cave'],
    relatedStories: ['story_kahf'],
  }),
  seed({
    entityId: 'entity_people_ashab_fil', type: 'people_or_nation',
    labelArabic: 'أصحاب الفيل', labelEnglish: 'People of the Elephant',
    aliasesArabic: ['أصحاب الفيل'],
    aliasesEnglish: ['People of the Elephant'],
    relatedStories: ['story_elephant'],
  }),
  seed({
    entityId: 'entity_people_sabt', type: 'people_or_nation',
    labelArabic: 'أصحاب السبت', labelEnglish: 'The Sabbath-breakers',
    aliasesArabic: ['أصحاب السبت', 'السبت'],
    aliasesEnglish: ['Sabbath-breakers'],
    relatedStories: ['story_sabbath_breakers'],
  }),
  seed({
    entityId: 'entity_people_ashab_jannah', type: 'people_or_nation',
    labelArabic: 'أصحاب الجنة', labelEnglish: 'Owners of the Garden',
    aliasesArabic: ['أصحاب الجنة'],
    aliasesEnglish: ['Owners of the Garden'],
    relatedStories: ['story_garden_owners'],
  }),
  seed({
    entityId: 'entity_people_ashab_ukhdud', type: 'people_or_nation',
    labelArabic: 'أصحاب الأخدود', labelEnglish: 'People of the Ditch',
    aliasesArabic: ['أصحاب الأخدود'],
    aliasesEnglish: ['People of the Ditch'],
    relatedStories: ['story_ukhdud'],
  }),
  seed({
    entityId: 'entity_people_ashab_qarya', type: 'people_or_nation',
    labelArabic: 'أصحاب القرية', labelEnglish: 'People of the Town',
    aliasesArabic: ['أصحاب القرية'],
    aliasesEnglish: ['People of the Town'],
    relatedStories: ['story_qarya'],
  }),
  seed({
    entityId: 'entity_people_aal_firawn', type: 'people_or_nation',
    labelArabic: 'آل فرعون', labelEnglish: "Pharaoh's people",
    aliasesArabic: ['آل فرعون'],
    aliasesEnglish: ["Pharaoh's people"],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_people_quraysh', type: 'people_or_nation',
    labelArabic: 'قريش', labelEnglish: 'Quraysh',
    aliasesArabic: ['قريش'],
    aliasesEnglish: ['Quraysh'],
  }),
  seed({
    entityId: 'entity_people_yajuj_majuj', type: 'people_or_nation',
    labelArabic: 'يأجوج ومأجوج', labelEnglish: 'Gog and Magog',
    aliasesArabic: ['يأجوج', 'ومأجوج', 'مأجوج'],
    aliasesEnglish: ['Yajuj', 'Majuj', 'Gog', 'Magog'],
    relatedStories: ['story_dhulqarnayn'],
  }),
  seed({
    entityId: 'entity_people_saba', type: 'people_or_nation',
    labelArabic: 'سبأ', labelEnglish: 'Saba',
    aliasesArabic: ['سبإ', 'سبأ'],
    aliasesEnglish: ['Saba', 'Sheba'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_people_rass', type: 'people_or_nation',
    labelArabic: 'أصحاب الرس', labelEnglish: 'People of Ar-Rass',
    aliasesArabic: ['أصحاب الرس', 'الرس'],
    aliasesEnglish: ['People of Ar-Rass'],
  }),
  seed({
    entityId: 'entity_people_tubba', type: 'people_or_nation',
    labelArabic: 'قوم تبع', labelEnglish: 'People of Tubba',
    aliasesArabic: ['قوم تبع'],
    aliasesEnglish: ['Tubba'],
    warnings: ['Bare "تبع" alias removed — matched many unrelated verb forms.'],
  }),
];

// ---------------------------------------------------------------------------
// 4. Animals
// ---------------------------------------------------------------------------

export const ANIMAL_SEEDS: QuranStoryEntity[] = [
  seed({
    entityId: 'entity_animal_baqarah', type: 'animal',
    labelArabic: 'بقرة بني إسرائيل', labelEnglish: 'Cow of Bani Israel',
    aliasesArabic: ['البقرة', 'بقرة'],
    aliasesEnglish: ['Cow'],
    relatedStories: ['story_baqarah_cow'],
    warnings: ['Generic — overlap with Surah Al-Baqarah name. Scanner downgrades confidence.'],
  }),
  seed({
    entityId: 'entity_animal_naqah', type: 'animal',
    labelArabic: 'ناقة صالح', labelEnglish: 'She-camel of Salih',
    aliasesArabic: ['الناقة', 'ناقة الله'],
    aliasesEnglish: ['She-camel'],
    relatedStories: ['story_salih'],
  }),
  seed({
    entityId: 'entity_animal_hoopoe', type: 'animal',
    labelArabic: 'الهدهد', labelEnglish: 'Hoopoe',
    aliasesArabic: ['الهدهد'],
    aliasesEnglish: ['Hoopoe'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_animal_ants', type: 'animal',
    labelArabic: 'النمل', labelEnglish: 'Ants',
    aliasesArabic: ['النمل', 'نملة'],
    aliasesEnglish: ['Ant', 'Ants'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_animal_dog_cave', type: 'animal',
    labelArabic: 'كلب أصحاب الكهف', labelEnglish: 'Dog of the Cave',
    aliasesArabic: ['كلبهم'],
    aliasesEnglish: ['Dog of the Cave'],
    relatedStories: ['story_kahf'],
  }),
  seed({
    entityId: 'entity_animal_whale', type: 'animal',
    labelArabic: 'حوت يونس', labelEnglish: 'Whale of Yunus',
    aliasesArabic: ['الحوت', 'النون'],
    aliasesEnglish: ['Whale', 'Great Fish'],
    relatedStories: ['story_yunus'],
  }),
  seed({
    entityId: 'entity_animal_birds_ibrahim', type: 'animal',
    labelArabic: 'طيور إبراهيم', labelEnglish: 'Birds of Ibrahim',
    aliasesArabic: ['الطير'],
    aliasesEnglish: ['Birds'],
    relatedStories: ['story_ibrahim'],
  }),
  seed({
    entityId: 'entity_animal_spider', type: 'animal',
    labelArabic: 'العنكبوت', labelEnglish: 'Spider',
    aliasesArabic: ['العنكبوت'],
    aliasesEnglish: ['Spider'],
  }),
  seed({
    entityId: 'entity_animal_bee', type: 'animal',
    labelArabic: 'النحل', labelEnglish: 'Bee',
    aliasesArabic: ['النحل'],
    aliasesEnglish: ['Bee'],
  }),
  seed({
    entityId: 'entity_animal_elephant', type: 'animal',
    labelArabic: 'الفيل', labelEnglish: 'Elephant',
    aliasesArabic: ['الفيل'],
    aliasesEnglish: ['Elephant'],
    relatedStories: ['story_elephant'],
  }),
  seed({
    entityId: 'entity_animal_crow', type: 'animal',
    labelArabic: 'الغراب', labelEnglish: 'Crow',
    aliasesArabic: ['غرابا', 'غراب'],
    aliasesEnglish: ['Crow'],
    relatedStories: ['story_habil_qabil'],
  }),
  seed({
    entityId: 'entity_animal_snake_staff', type: 'animal',
    labelArabic: 'حية موسى', labelEnglish: 'Snake of Musa',
    aliasesArabic: ['حية', 'ثعبان', 'الجان'],
    aliasesEnglish: ['Snake', 'Serpent'],
    relatedStories: ['story_musa'],
  }),
];

// ---------------------------------------------------------------------------
// 5. Places
// ---------------------------------------------------------------------------

export const PLACE_SEEDS: QuranStoryEntity[] = [
  seed({
    entityId: 'entity_place_makkah', type: 'place',
    labelArabic: 'مكة', labelEnglish: 'Makkah',
    aliasesArabic: ['مكة', 'بكة', 'أم القرى', 'البلد الأمين'],
    aliasesEnglish: ['Makkah', 'Mecca', 'Bakkah'],
  }),
  seed({
    entityId: 'entity_place_madinah', type: 'place',
    labelArabic: 'المدينة', labelEnglish: 'Madinah',
    aliasesArabic: ['يثرب', 'المدينة'],
    aliasesEnglish: ['Madinah', 'Yathrib'],
    warnings: ['"المدينة" is common; scanner downgrades confidence for non-Madani surahs.'],
  }),
  seed({
    entityId: 'entity_place_egypt', type: 'place',
    labelArabic: 'مصر', labelEnglish: 'Egypt',
    aliasesArabic: ['مصر'],
    aliasesEnglish: ['Egypt', 'Misr'],
    relatedStories: ['story_musa', 'story_yusuf'],
  }),
  seed({
    entityId: 'entity_place_madyan_place', type: 'place',
    labelArabic: 'مدين', labelEnglish: 'Madyan',
    aliasesArabic: ['مدين'],
    aliasesEnglish: ['Madyan'],
    relatedStories: ['story_shuayb'],
  }),
  seed({
    entityId: 'entity_place_sinai', type: 'place',
    labelArabic: 'طور سيناء', labelEnglish: 'Mount Sinai',
    aliasesArabic: ['الطور', 'طور سيناء', 'طور سينين'],
    aliasesEnglish: ['Mount Sinai', 'Tur'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_place_arafat', type: 'place',
    labelArabic: 'عرفات', labelEnglish: 'Arafat',
    aliasesArabic: ['عرفات'],
    aliasesEnglish: ['Arafat'],
  }),
  seed({
    entityId: 'entity_place_safa_marwah', type: 'place',
    labelArabic: 'الصفا والمروة', labelEnglish: 'Safa and Marwah',
    aliasesArabic: ['الصفا', 'المروة'],
    aliasesEnglish: ['Safa', 'Marwah'],
  }),
  seed({
    entityId: 'entity_place_babylon', type: 'place',
    labelArabic: 'بابل', labelEnglish: 'Babylon',
    aliasesArabic: ['بابل'],
    aliasesEnglish: ['Babylon'],
  }),
  seed({
    entityId: 'entity_place_saba_place', type: 'place',
    labelArabic: 'أرض سبأ', labelEnglish: 'Land of Saba',
    aliasesArabic: ['سبأ', 'سبإ'],
    aliasesEnglish: ['Saba', 'Sheba'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_place_ahqaf', type: 'place',
    labelArabic: 'الأحقاف', labelEnglish: 'Al-Ahqaf',
    aliasesArabic: ['الأحقاف'],
    aliasesEnglish: ['Al-Ahqaf'],
    relatedStories: ['story_hud'],
  }),
  seed({
    entityId: 'entity_place_cave', type: 'place',
    labelArabic: 'الكهف', labelEnglish: 'The Cave',
    aliasesArabic: ['الكهف'],
    aliasesEnglish: ['The Cave'],
    relatedStories: ['story_kahf'],
  }),
  seed({
    entityId: 'entity_place_jerusalem', type: 'place',
    labelArabic: 'بيت المقدس', labelEnglish: 'Jerusalem',
    aliasesArabic: ['الأقصى', 'بيت المقدس'],
    aliasesEnglish: ['Jerusalem', 'Al-Aqsa'],
  }),
];

// ---------------------------------------------------------------------------
// 6. Objects & events
// ---------------------------------------------------------------------------

export const OBJECT_EVENT_SEEDS: QuranStoryEntity[] = [
  seed({
    entityId: 'entity_object_ark', type: 'object',
    labelArabic: 'سفينة نوح', labelEnglish: 'Ark of Nuh',
    aliasesArabic: ['الفلك', 'السفينة'],
    aliasesEnglish: ['Ark'],
    relatedStories: ['story_nuh'],
  }),
  seed({
    entityId: 'entity_object_staff_musa', type: 'object',
    labelArabic: 'عصا موسى', labelEnglish: 'Staff of Musa',
    aliasesArabic: ['عصاه', 'عصاك'],
    aliasesEnglish: ['Staff'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_object_tablets', type: 'object',
    labelArabic: 'الألواح', labelEnglish: 'Tablets',
    aliasesArabic: ['الألواح'],
    aliasesEnglish: ['Tablets'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_object_table_spread', type: 'object',
    labelArabic: 'المائدة', labelEnglish: 'Table Spread',
    aliasesArabic: ['المائدة', 'مائدة'],
    aliasesEnglish: ['Table'],
    relatedStories: ['story_table_spread'],
  }),
  seed({
    entityId: 'entity_object_throne_bilqis', type: 'object',
    labelArabic: 'عرش بلقيس', labelEnglish: 'Throne of Bilqis',
    aliasesArabic: ['عرشها'],
    aliasesEnglish: ['Throne'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_object_two_gardens', type: 'object',
    labelArabic: 'الجنتان', labelEnglish: 'Two Gardens',
    aliasesArabic: ['جنتين', 'جنتان'],
    aliasesEnglish: ['Two Gardens'],
    relatedStories: ['story_two_gardens'],
  }),
  seed({
    entityId: 'entity_object_barrier', type: 'object',
    labelArabic: 'سد ذي القرنين', labelEnglish: 'Wall of Dhul-Qarnayn',
    aliasesArabic: ['ردما', 'السد', 'سدا'],
    aliasesEnglish: ['Wall', 'Barrier'],
    relatedStories: ['story_dhulqarnayn'],
  }),
  seed({
    entityId: 'entity_event_sea_crossing', type: 'event',
    labelArabic: 'انفلاق البحر', labelEnglish: 'Crossing of the Sea',
    aliasesArabic: ['فانفلق', 'فرق بكم البحر'],
    aliasesEnglish: ['Sea splitting'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_event_flood', type: 'event',
    labelArabic: 'الطوفان', labelEnglish: 'The Flood',
    aliasesArabic: ['الطوفان'],
    aliasesEnglish: ['Flood', 'Deluge'],
    relatedStories: ['story_nuh'],
  }),
  seed({
    entityId: 'entity_event_fire_ibrahim', type: 'event',
    labelArabic: 'نار إبراهيم', labelEnglish: 'Fire of Ibrahim',
    aliasesArabic: ['حرقوه', 'نارا'],
    aliasesEnglish: ['Fire of Ibrahim'],
    relatedStories: ['story_ibrahim'],
    warnings: ['"نارا" matches many ayahs about Hellfire; downgrade confidence outside Surah Al-Anbiya/Al-Saffat.'],
  }),
  seed({
    entityId: 'entity_event_virgin_birth', type: 'event',
    labelArabic: 'ولادة عيسى', labelEnglish: 'Birth of Isa',
    aliasesArabic: ['فأجاءها المخاض'],
    aliasesEnglish: ['Birth of Isa'],
    relatedStories: ['story_maryam'],
  }),
];

// ---------------------------------------------------------------------------
// 7. Angels (small set — explicit names only)
// ---------------------------------------------------------------------------

export const ANGEL_SEEDS: QuranStoryEntity[] = [
  seed({
    entityId: 'entity_angel_jibreel', type: 'angel',
    labelArabic: 'جبريل عليه السلام', labelEnglish: 'Jibreel (Gabriel)',
    aliasesArabic: ['جبريل', 'الروح الأمين'],
    aliasesEnglish: ['Jibreel', 'Gabriel'],
  }),
  seed({
    entityId: 'entity_angel_mikail', type: 'angel',
    labelArabic: 'ميكال عليه السلام', labelEnglish: 'Mikail (Michael)',
    aliasesArabic: ['ميكال', 'ميكائيل'],
    aliasesEnglish: ['Mikail', 'Michael'],
  }),
  seed({
    entityId: 'entity_angel_malak_mawt', type: 'angel',
    labelArabic: 'ملك الموت', labelEnglish: 'Angel of Death',
    aliasesArabic: ['ملك الموت'],
    aliasesEnglish: ['Angel of Death'],
  }),
];

// ---------------------------------------------------------------------------
// 8. Combined seed export
// ---------------------------------------------------------------------------

export const QURAN_STORY_ENTITY_SEEDS: QuranStoryEntity[] = [
  ...PROPHET_SEEDS,
  ...PERSON_SEEDS,
  ...PEOPLE_SEEDS,
  ...ANIMAL_SEEDS,
  ...PLACE_SEEDS,
  ...OBJECT_EVENT_SEEDS,
  ...ANGEL_SEEDS,
];

export function getEntitySeedById(entityId: string): QuranStoryEntity | undefined {
  return QURAN_STORY_ENTITY_SEEDS.find((e) => e.entityId === entityId);
}

export function getEntitySeedsByType(type: QuranStoryEntity['type']): QuranStoryEntity[] {
  return QURAN_STORY_ENTITY_SEEDS.filter((e) => e.type === type);
}
