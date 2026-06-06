/**
 * Quran Entity Seeds — candidate-detection dictionary for the
 * Entity-Centered Quran Narrative GraphRAG system.
 *
 * Used by:
 *   - scripts/scan-quran-entity-mentions.ts
 *   - scripts/build-quran-entity-relations.ts
 *   - scripts/build-quran-entity-journeys.ts
 *
 * Hard rules:
 *   - This file is a CANDIDATE-DETECTION dictionary, not approved data.
 *   - Every entry is `reviewedDictionary: false` until a specialist signs off.
 *   - Aliases are written without diacritics where possible — the scanner
 *     strips tashkeel before matching, so canonical Quranic spellings work
 *     once normalised.
 *   - No Quran text is included.
 *   - Aliases must be specific enough to avoid common-word false positives;
 *     overly generic aliases (e.g. "الرسول") are noted in `warnings`.
 *
 * Adding entries:
 *   - Include the most distinctive Arabic spellings as they appear in the
 *     mushaf after normalisation.
 *   - Add English transliterations and common Western names for search.
 *   - Cross-link to existing storyIds and themeIds where the mapping is
 *     unambiguous.
 */

import type {
  EntitySeed,
  EntityRelationType,
  QuranEntityType,
} from '../types/quranEntityGraph';

// ---------------------------------------------------------------------------
// Helper: shorthand factory.
// ---------------------------------------------------------------------------

function seed(s: Omit<EntitySeed, 'reviewedDictionary'> & { reviewedDictionary?: boolean }): EntitySeed {
  return {
    relatedStories: [],
    relatedThemes: [],
    knownRelatives: [],
    warnings: [],
    reviewedDictionary: false,
    ...s,
  };
}

// Convenience: typed family-relation factory.
function rel(entityId: string, relationType: EntityRelationType): { entityId: string; relationType: EntityRelationType } {
  return { entityId, relationType };
}

// ---------------------------------------------------------------------------
// 1. Prophets and messengers (25 named in the Quran)
// ---------------------------------------------------------------------------

export const PROPHET_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_prophet_adam',
    entityType: 'prophet',
    labelArabic: 'آدم عليه السلام',
    labelEnglish: 'Adam',
    aliasesArabic: ['آدم', 'ادم'],
    aliasesEnglish: ['Adam'],
    transliterations: ['Adam'],
    relatedStories: ['story_adam'],
    knownRelatives: [rel('entity_person_hawwa', 'wife_of')],
  }),
  seed({
    entityId: 'entity_prophet_idris',
    entityType: 'prophet',
    labelArabic: 'إدريس عليه السلام',
    labelEnglish: 'Idris (Enoch)',
    aliasesArabic: ['إدريس', 'ادريس'],
    aliasesEnglish: ['Idris', 'Enoch'],
    transliterations: ['Idris', 'Enoch'],
    relatedStories: ['story_idris'],
  }),
  seed({
    entityId: 'entity_prophet_nuh',
    entityType: 'prophet',
    labelArabic: 'نوح عليه السلام',
    labelEnglish: 'Nuh (Noah)',
    aliasesArabic: ['نوح', 'نوحا'],
    aliasesEnglish: ['Nuh', 'Noah'],
    transliterations: ['Nuh', 'Noah', 'Nooh'],
    relatedStories: ['story_nuh'],
  }),
  seed({
    entityId: 'entity_prophet_hud',
    entityType: 'prophet',
    labelArabic: 'هود عليه السلام',
    labelEnglish: 'Hud',
    aliasesArabic: ['هود', 'هودا'],
    aliasesEnglish: ['Hud'],
    transliterations: ['Hud'],
    relatedStories: ['story_hud'],
  }),
  seed({
    entityId: 'entity_prophet_salih',
    entityType: 'prophet',
    labelArabic: 'صالح عليه السلام',
    labelEnglish: 'Salih',
    // Quran writes صَٰلِحٌ — dagger-alif strips to صلح. Add both spellings.
    aliasesArabic: ['صالح', 'صالحا', 'صلح', 'صلحا'],
    aliasesEnglish: ['Salih', 'Saleh'],
    transliterations: ['Salih', 'Saleh'],
    relatedStories: ['story_salih'],
  }),
  seed({
    entityId: 'entity_prophet_ibrahim',
    entityType: 'prophet',
    labelArabic: 'إبراهيم عليه السلام',
    labelEnglish: 'Ibrahim (Abraham)',
    // After diacritic strip the Quranic spelling normalises to ابرهيم.
    aliasesArabic: ['إبراهيم', 'ابراهيم', 'ابرهيم', 'الخليل'],
    aliasesEnglish: ['Ibrahim', 'Abraham', 'Khalil'],
    transliterations: ['Ibrahim', 'Abraham', 'Ibraheem'],
    relatedStories: ['story_ibrahim'],
    knownRelatives: [
      rel('entity_prophet_ismail', 'father_of'),
      rel('entity_prophet_ishaq', 'father_of'),
    ],
    warnings: ['"الخليل" is generic; scanner downgrades it.'],
  }),
  seed({
    entityId: 'entity_prophet_lut',
    entityType: 'prophet',
    labelArabic: 'لوط عليه السلام',
    labelEnglish: 'Lut (Lot)',
    aliasesArabic: ['لوط', 'لوطا'],
    aliasesEnglish: ['Lut', 'Lot'],
    transliterations: ['Lut', 'Lot'],
    relatedStories: ['story_lut'],
  }),
  seed({
    entityId: 'entity_prophet_ismail',
    entityType: 'prophet',
    labelArabic: 'إسماعيل عليه السلام',
    labelEnglish: 'Ismail (Ishmael)',
    aliasesArabic: ['إسماعيل', 'اسماعيل', 'اسمعيل'],
    aliasesEnglish: ['Ismail', 'Ishmael'],
    transliterations: ['Ismail', 'Ishmael'],
    knownRelatives: [rel('entity_prophet_ibrahim', 'son_of')],
  }),
  seed({
    entityId: 'entity_prophet_ishaq',
    entityType: 'prophet',
    labelArabic: 'إسحاق عليه السلام',
    labelEnglish: 'Ishaq (Isaac)',
    aliasesArabic: ['إسحاق', 'اسحاق', 'اسحق'],
    aliasesEnglish: ['Ishaq', 'Isaac'],
    transliterations: ['Ishaq', 'Isaac'],
    knownRelatives: [
      rel('entity_prophet_ibrahim', 'son_of'),
      rel('entity_prophet_yaqub', 'father_of'),
    ],
  }),
  seed({
    entityId: 'entity_prophet_yaqub',
    entityType: 'prophet',
    labelArabic: 'يعقوب عليه السلام',
    labelEnglish: 'Yaqub (Jacob)',
    aliasesArabic: ['يعقوب', 'إسرائيل'],
    aliasesEnglish: ['Yaqub', 'Jacob', 'Israel'],
    transliterations: ['Yaqub', 'Jacob', 'Yaaqub'],
    knownRelatives: [
      rel('entity_prophet_ishaq', 'son_of'),
      rel('entity_prophet_yusuf', 'father_of'),
    ],
    warnings: ['"إسرائيل" alias is also a people name; scanner disambiguates by adjacency.'],
  }),
  seed({
    entityId: 'entity_prophet_yusuf',
    entityType: 'prophet',
    labelArabic: 'يوسف عليه السلام',
    labelEnglish: 'Yusuf (Joseph)',
    aliasesArabic: ['يوسف'],
    aliasesEnglish: ['Yusuf', 'Joseph'],
    transliterations: ['Yusuf', 'Joseph', 'Yousef'],
    relatedStories: ['story_yusuf'],
    knownRelatives: [rel('entity_prophet_yaqub', 'son_of')],
  }),
  seed({
    entityId: 'entity_prophet_shuayb',
    entityType: 'prophet',
    labelArabic: 'شعيب عليه السلام',
    labelEnglish: 'Shuayb (Jethro)',
    aliasesArabic: ['شعيب', 'شعيبا'],
    aliasesEnglish: ['Shuayb', 'Jethro'],
    transliterations: ['Shuayb', 'Shoaib'],
    relatedStories: ['story_shuayb'],
  }),
  seed({
    entityId: 'entity_prophet_musa',
    entityType: 'prophet',
    labelArabic: 'موسى عليه السلام',
    labelEnglish: 'Musa (Moses)',
    aliasesArabic: ['موسى', 'موسٰى', 'كليم الله'],
    aliasesEnglish: ['Musa', 'Moses', 'Kalimullah'],
    transliterations: ['Musa', 'Moses', 'Moosa'],
    relatedStories: ['story_musa'],
    knownRelatives: [rel('entity_prophet_harun', 'brother_of')],
    warnings: ['"كليم الله" is a generic descriptive title; downgrade confidence.'],
  }),
  seed({
    entityId: 'entity_prophet_harun',
    entityType: 'prophet',
    labelArabic: 'هارون عليه السلام',
    labelEnglish: 'Harun (Aaron)',
    // Quran writes هَٰرُونَ — dagger-alif strips to هرون.
    aliasesArabic: ['هارون', 'هرون'],
    aliasesEnglish: ['Harun', 'Aaron'],
    transliterations: ['Harun', 'Aaron', 'Haroon'],
  }),
  seed({
    entityId: 'entity_prophet_dawud',
    entityType: 'prophet',
    labelArabic: 'داود عليه السلام',
    labelEnglish: 'Dawud (David)',
    aliasesArabic: ['داود', 'داوود'],
    aliasesEnglish: ['Dawud', 'David', 'Daud'],
    transliterations: ['Dawud', 'David', 'Daoud'],
    relatedStories: ['story_dawud'],
    knownRelatives: [rel('entity_prophet_sulayman', 'father_of')],
  }),
  seed({
    entityId: 'entity_prophet_sulayman',
    entityType: 'prophet',
    labelArabic: 'سليمان عليه السلام',
    labelEnglish: 'Sulayman (Solomon)',
    aliasesArabic: ['سليمان', 'سليمن'],
    aliasesEnglish: ['Sulayman', 'Solomon'],
    transliterations: ['Sulayman', 'Solomon', 'Suleiman'],
    relatedStories: ['story_bilqis'],
    knownRelatives: [rel('entity_prophet_dawud', 'son_of')],
  }),
  seed({
    entityId: 'entity_prophet_ayyub',
    entityType: 'prophet',
    labelArabic: 'أيوب عليه السلام',
    labelEnglish: 'Ayyub (Job)',
    aliasesArabic: ['أيوب', 'ايوب'],
    aliasesEnglish: ['Ayyub', 'Job'],
    transliterations: ['Ayyub', 'Job'],
    relatedStories: ['story_ayyub'],
  }),
  seed({
    entityId: 'entity_prophet_yunus',
    entityType: 'prophet',
    labelArabic: 'يونس عليه السلام',
    labelEnglish: 'Yunus (Jonah)',
    aliasesArabic: ['يونس', 'ذا النون', 'ذو النون', 'صاحب الحوت'],
    aliasesEnglish: ['Yunus', 'Jonah', 'Dhul-Nun'],
    transliterations: ['Yunus', 'Jonah'],
    relatedStories: ['story_yunus'],
    warnings: ['"صاحب الحوت" is descriptive; downgrade confidence.'],
  }),
  seed({
    entityId: 'entity_prophet_zakariyya',
    entityType: 'prophet',
    labelArabic: 'زكريا عليه السلام',
    labelEnglish: 'Zakariyya (Zechariah)',
    aliasesArabic: ['زكريا', 'زكرياء'],
    aliasesEnglish: ['Zakariyya', 'Zechariah'],
    transliterations: ['Zakariyya', 'Zechariah'],
    relatedStories: ['story_zakariyya_yahya'],
    knownRelatives: [
      rel('entity_prophet_yahya', 'father_of'),
      rel('entity_person_maryam', 'guardian_of'),
    ],
  }),
  seed({
    entityId: 'entity_prophet_yahya',
    entityType: 'prophet',
    labelArabic: 'يحيى عليه السلام',
    labelEnglish: 'Yahya (John)',
    aliasesArabic: ['يحيى', 'يحيىٰ'],
    aliasesEnglish: ['Yahya', 'John'],
    transliterations: ['Yahya', 'John'],
    relatedStories: ['story_zakariyya_yahya'],
    knownRelatives: [rel('entity_prophet_zakariyya', 'son_of')],
  }),
  seed({
    entityId: 'entity_prophet_isa',
    entityType: 'prophet',
    labelArabic: 'عيسى عليه السلام',
    labelEnglish: 'Isa (Jesus)',
    aliasesArabic: ['عيسى', 'المسيح', 'ابن مريم'],
    aliasesEnglish: ['Isa', 'Jesus', 'Christ', 'Messiah', 'Son of Mary'],
    transliterations: ['Isa', 'Jesus'],
    relatedStories: ['story_isa'],
    knownRelatives: [rel('entity_person_maryam', 'son_of')],
  }),
  seed({
    entityId: 'entity_prophet_dhulkifl',
    entityType: 'prophet',
    labelArabic: 'ذو الكفل عليه السلام',
    labelEnglish: 'Dhul-Kifl',
    aliasesArabic: ['ذا الكفل', 'ذو الكفل'],
    aliasesEnglish: ['Dhul-Kifl'],
    transliterations: ['Dhul-Kifl'],
  }),
  seed({
    entityId: 'entity_prophet_ilyas',
    entityType: 'prophet',
    labelArabic: 'إلياس عليه السلام',
    labelEnglish: 'Ilyas (Elijah)',
    // Quranic spellings: إِلْيَاسَ (6:85) and إِلْ يَاسِينَ / إِلْيَاسِينَ (37:130).
    aliasesArabic: ['إلياس', 'الياس', 'إلياسين', 'الياسين'],
    aliasesEnglish: ['Ilyas', 'Elijah', 'Elias'],
    transliterations: ['Ilyas', 'Elias', 'Elijah'],
  }),
  seed({
    entityId: 'entity_prophet_alyasa',
    entityType: 'prophet',
    labelArabic: 'اليسع عليه السلام',
    labelEnglish: 'Al-Yasa (Elisha)',
    // Quranic spellings: ٱلْيَسَعَ (6:86, 38:48).
    aliasesArabic: ['اليسع', 'إليسع'],
    aliasesEnglish: ['Al-Yasa', 'Alyasa', 'Elisha'],
    transliterations: ['Al-Yasa', 'Alyasa', 'Elisha'],
  }),
  seed({
    entityId: 'entity_prophet_muhammad',
    entityType: 'prophet',
    labelArabic: 'محمد ﷺ',
    labelEnglish: 'Muhammad (peace be upon him)',
    aliasesArabic: ['محمد', 'أحمد'],
    aliasesEnglish: ['Muhammad', 'Ahmad'],
    transliterations: ['Muhammad', 'Mohammad', 'Ahmed'],
    warnings: [
      'Generic alias "الرسول" omitted to avoid widespread false positives; rely on explicit "محمد" / "أحمد" namings.',
    ],
  }),
];

// ---------------------------------------------------------------------------
// 2. Other named persons (men & women)
// ---------------------------------------------------------------------------

export const PERSON_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_person_maryam',
    entityType: 'woman',
    labelArabic: 'مريم عليها السلام',
    labelEnglish: 'Maryam (Mary)',
    // Pronoun-form "أمه" (his mother) is included for descriptive coverage but
    // the scanner only emits pronoun_context matches when the surah also
    // contains an explicit "مريم" mention. "أم عيسى" never appears as a phrase
    // and is intentionally omitted.
    aliasesArabic: ['مريم', 'ابن مريم', 'أمه'],
    aliasesEnglish: [
      'Maryam',
      'Mary',
      'Mary mother of Jesus',
      'mother of Isa',
      'Isa son of Maryam',
      'Jesus son of Mary',
    ],
    transliterations: ['Maryam', 'Mary', 'Maryem'],
    relatedStories: ['story_maryam', 'story_isa'],
    relatedThemes: ['theme_glad_tidings', 'theme_chosen_women'],
    knownRelatives: [
      rel('entity_prophet_isa', 'mother_of'),
      rel('entity_person_imran', 'daughter_of'),
      rel('entity_prophet_zakariyya', 'family_of'),
    ],
    warnings: [
      '"أمه" matches "his mother" of any antecedent — scanner restricts it to surahs that already contain explicit "مريم".',
      '"ابن مريم" is a family-relation alias (Isa-son-of-Maryam) and is tagged accordingly.',
    ],
  }),
  seed({
    entityId: 'entity_person_firawn',
    entityType: 'person',
    labelArabic: 'فرعون',
    labelEnglish: 'Firawn (Pharaoh)',
    aliasesArabic: ['فرعون'],
    aliasesEnglish: ['Firawn', 'Pharaoh'],
    transliterations: ['Firawn', 'Pharaoh', 'Firaun'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_person_haman',
    entityType: 'person',
    labelArabic: 'هامان',
    labelEnglish: 'Haman',
    // Quran writes هَٰمَٰنَ — strip dagger-alifs.
    aliasesArabic: ['هامان', 'همن'],
    aliasesEnglish: ['Haman'],
    transliterations: ['Haman'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_person_qarun',
    entityType: 'person',
    labelArabic: 'قارون',
    labelEnglish: 'Qarun (Korah)',
    // Quran writes قَٰرُونَ — dagger-alif strips to قرون (also Arabic for "centuries";
    // scanner downgrades via the generic-alias list).
    aliasesArabic: ['قارون', 'قرون'],
    aliasesEnglish: ['Qarun', 'Korah'],
    transliterations: ['Qarun', 'Korah'],
    relatedStories: ['story_qarun'],
    warnings: ['Alias "قرون" overlaps with the Arabic noun for "generations/centuries"; scanner downgrades it.'],
  }),
  seed({
    entityId: 'entity_person_talut',
    entityType: 'person',
    labelArabic: 'طالوت',
    labelEnglish: 'Talut (Saul)',
    aliasesArabic: ['طالوت'],
    aliasesEnglish: ['Talut', 'Saul'],
    transliterations: ['Talut', 'Saul'],
    relatedStories: ['story_talut_jalut'],
  }),
  seed({
    entityId: 'entity_person_jalut',
    entityType: 'person',
    labelArabic: 'جالوت',
    labelEnglish: 'Jalut (Goliath)',
    aliasesArabic: ['جالوت'],
    aliasesEnglish: ['Jalut', 'Goliath'],
    transliterations: ['Jalut', 'Goliath'],
    relatedStories: ['story_talut_jalut'],
  }),
  seed({
    entityId: 'entity_person_bilqis',
    entityType: 'woman',
    labelArabic: 'بلقيس',
    labelEnglish: 'Bilqis (Queen of Sheba)',
    aliasesArabic: ['ملكة سبأ'],
    aliasesEnglish: ['Bilqis', 'Queen of Sheba'],
    transliterations: ['Bilqis', 'Balqis'],
    relatedStories: ['story_bilqis'],
    warnings: [
      'Bilqis is never named explicitly in the Quran; "ملكة سبأ" is a descriptive title. All mentions are needs_review story_context.',
    ],
  }),
  seed({
    entityId: 'entity_person_dhulqarnayn',
    entityType: 'person',
    labelArabic: 'ذو القرنين',
    labelEnglish: 'Dhul-Qarnayn',
    aliasesArabic: ['ذو القرنين', 'ذا القرنين'],
    aliasesEnglish: ['Dhul-Qarnayn'],
    transliterations: ['Dhul-Qarnayn'],
    relatedStories: ['story_dhulqarnayn'],
  }),
  seed({
    entityId: 'entity_person_luqman',
    entityType: 'person',
    labelArabic: 'لقمان الحكيم',
    labelEnglish: 'Luqman the Wise',
    aliasesArabic: ['لقمان', 'لقمن'],
    aliasesEnglish: ['Luqman'],
    transliterations: ['Luqman'],
    relatedStories: ['story_luqman'],
  }),
  seed({
    entityId: 'entity_person_imran',
    entityType: 'person',
    labelArabic: 'عمران',
    labelEnglish: 'Imran',
    // Quran writes عِمْرَٰنَ — strip dagger-alif → عمرن.
    aliasesArabic: ['عمران', 'عمرن', 'آل عمران', 'آل عمرن'],
    aliasesEnglish: ['Imran'],
    transliterations: ['Imran'],
    knownRelatives: [rel('entity_person_maryam', 'father_of')],
    warnings: ['"آل عمران" matches the family/lineage as a unit, not Imran himself.'],
  }),
  seed({
    entityId: 'entity_person_iblis',
    entityType: 'jinn',
    labelArabic: 'إبليس',
    labelEnglish: 'Iblis (Satan)',
    aliasesArabic: ['إبليس'],
    aliasesEnglish: ['Iblis', 'Satan', 'Devil'],
    transliterations: ['Iblis', 'Satan'],
    warnings: ['Generic alias "الشيطان" omitted; it has hundreds of contextual usages distinct from Iblis specifically.'],
  }),
  seed({
    entityId: 'entity_person_hawwa',
    entityType: 'woman',
    labelArabic: 'حواء',
    labelEnglish: 'Hawwa (Eve)',
    aliasesArabic: ['زوجه'],
    aliasesEnglish: ['Hawwa', 'Eve'],
    transliterations: ['Hawwa', 'Eve'],
    relatedStories: ['story_adam'],
    knownRelatives: [rel('entity_prophet_adam', 'wife_of')],
    warnings: ['Hawwa is never named explicitly in the Quran; "زوجه" alias matches many other spouses.'],
  }),
  seed({
    entityId: 'entity_person_aziz',
    entityType: 'person',
    labelArabic: 'العزيز',
    labelEnglish: 'Al-Aziz of Egypt',
    aliasesArabic: ['عزيز مصر'],
    aliasesEnglish: ['Aziz of Egypt'],
    transliterations: ['Aziz'],
    relatedStories: ['story_yusuf'],
    warnings: ['"العزيز" alone is a Divine Name; omitted to avoid massive false positives.'],
  }),
  seed({
    entityId: 'entity_person_zayd',
    entityType: 'person',
    labelArabic: 'زيد',
    labelEnglish: 'Zayd ibn Haritha',
    aliasesArabic: ['زيد'],
    aliasesEnglish: ['Zayd', 'Zaid'],
    transliterations: ['Zayd'],
    warnings: ['Only one explicit naming in Surah Al-Ahzab (33:37); other surface matches need review.'],
  }),
  seed({
    entityId: 'entity_person_abu_lahab',
    entityType: 'person',
    labelArabic: 'أبو لهب',
    labelEnglish: 'Abu Lahab',
    aliasesArabic: ['أبي لهب'],
    aliasesEnglish: ['Abu Lahab'],
    transliterations: ['Abu Lahab'],
    warnings: ['Only one explicit naming in Surah Al-Masad (111:1).'],
  }),
  seed({
    entityId: 'entity_person_aasiya',
    entityType: 'woman',
    labelArabic: 'آسية امرأة فرعون',
    labelEnglish: 'Asiya, wife of Pharaoh',
    aliasesArabic: ['امرأت فرعون', 'امرأة فرعون'],
    aliasesEnglish: ['Asiya', 'wife of Pharaoh'],
    transliterations: ['Asiya'],
    knownRelatives: [rel('entity_person_firawn', 'wife_of')],
    relatedStories: ['story_musa'],
    warnings: ['Asiya is not named explicitly in the Quran; alias "امرأت فرعون" is descriptive.'],
  }),
  seed({
    entityId: 'entity_person_imrat_imran',
    entityType: 'woman',
    labelArabic: 'امرأة عمران',
    labelEnglish: 'Wife of Imran (mother of Maryam)',
    // Quran writes ٱمْرَأَتُ عِمْرَٰنَ — after normalisation امرات عمرن.
    aliasesArabic: ['امرأت عمران', 'امرات عمرن'],
    aliasesEnglish: ['Wife of Imran'],
    transliterations: ['Imrat Imran'],
    knownRelatives: [
      rel('entity_person_imran', 'wife_of'),
      rel('entity_person_maryam', 'mother_of'),
    ],
    warnings: ['Descriptive, not a personal name; needs_review.'],
  }),
];

// ---------------------------------------------------------------------------
// 3. Peoples and nations
// ---------------------------------------------------------------------------

export const PEOPLE_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_people_bani_israel',
    entityType: 'people_or_nation',
    // Quran rasm: بَنِىٓ إِسْرَٰٓءِيلَ → after stripping diacritics + hamza + dagger-alif → بني اسريل
    labelArabic: 'بنو إسرائيل',
    labelEnglish: 'Children of Israel',
    aliasesArabic: ['بني إسرائيل', 'بنو إسرائيل', 'بني اسريل', 'بني اسرءيل'],
    aliasesEnglish: ['Bani Israel', 'Children of Israel', 'Israelites'],
    transliterations: ['Bani Israel'],
  }),
  seed({
    entityId: 'entity_people_aal_imran',
    entityType: 'family_relation',
    labelArabic: 'آل عمران',
    labelEnglish: 'Family of Imran',
    // Quran rasm: ءَالَ عِمْرَٰنَ → ال عمرن after normalisation
    aliasesArabic: ['آل عمران', 'ال عمران', 'ال عمرن'],
    aliasesEnglish: ['Family of Imran'],
    transliterations: ['Aal Imran'],
    knownRelatives: [
      rel('entity_person_imran', 'family_of'),
      rel('entity_person_maryam', 'family_of'),
    ],
  }),
  seed({
    entityId: 'entity_people_aad',
    entityType: 'people_or_nation',
    labelArabic: 'قوم عاد',
    labelEnglish: 'People of Aad',
    aliasesArabic: ['عاد', 'عادا'],
    aliasesEnglish: ['Aad', 'Ad'],
    transliterations: ['Aad'],
    relatedStories: ['story_hud'],
  }),
  seed({
    entityId: 'entity_people_thamud',
    entityType: 'people_or_nation',
    labelArabic: 'قوم ثمود',
    labelEnglish: 'People of Thamud',
    aliasesArabic: ['ثمود', 'ثمودا'],
    aliasesEnglish: ['Thamud'],
    transliterations: ['Thamud'],
    relatedStories: ['story_salih'],
  }),
  seed({
    entityId: 'entity_people_madyan',
    entityType: 'people_or_nation',
    labelArabic: 'أهل مدين',
    labelEnglish: 'People of Madyan',
    aliasesArabic: ['مدين', 'أصحاب الأيكة'],
    aliasesEnglish: ['Madyan', 'Midian'],
    transliterations: ['Madyan'],
    relatedStories: ['story_shuayb'],
  }),
  seed({
    entityId: 'entity_people_qawm_nuh',
    entityType: 'people_or_nation',
    labelArabic: 'قوم نوح',
    labelEnglish: 'People of Nuh',
    aliasesArabic: ['قوم نوح'],
    aliasesEnglish: ['People of Noah'],
    transliterations: ['Qawm Nuh'],
    relatedStories: ['story_nuh'],
  }),
  seed({
    entityId: 'entity_people_qawm_lut',
    entityType: 'people_or_nation',
    labelArabic: 'قوم لوط',
    labelEnglish: 'People of Lut',
    aliasesArabic: ['قوم لوط', 'المؤتفكات', 'المؤتفكة'],
    aliasesEnglish: ['People of Lot', 'Sodom'],
    transliterations: ['Qawm Lut'],
    relatedStories: ['story_lut'],
  }),
  seed({
    entityId: 'entity_people_ashab_kahf',
    entityType: 'people_or_nation',
    labelArabic: 'أصحاب الكهف',
    labelEnglish: 'People of the Cave',
    aliasesArabic: ['أصحاب الكهف', 'الفتية'],
    aliasesEnglish: ['People of the Cave', 'Companions of the Cave'],
    transliterations: ['Ashab al-Kahf'],
    relatedStories: ['story_kahf'],
  }),
  seed({
    entityId: 'entity_people_ashab_fil',
    entityType: 'people_or_nation',
    labelArabic: 'أصحاب الفيل',
    labelEnglish: 'People of the Elephant',
    // Quran rasm: أَصْحَٰبِ ٱلْفِيلِ → أصحب الفيل (dagger-alif on ح).
    aliasesArabic: ['أصحاب الفيل', 'أصحب الفيل'],
    aliasesEnglish: ['People of the Elephant'],
    transliterations: ['Ashab al-Fil'],
    relatedStories: ['story_elephant'],
  }),
  seed({
    entityId: 'entity_people_sabt',
    entityType: 'people_or_nation',
    labelArabic: 'أصحاب السبت',
    labelEnglish: 'The Sabbath-breakers',
    aliasesArabic: ['أصحاب السبت', 'أصحب السبت'],
    aliasesEnglish: ['Sabbath-breakers'],
    transliterations: ['Ashab al-Sabt'],
    relatedStories: ['story_sabbath_breakers'],
  }),
  seed({
    entityId: 'entity_people_aal_firawn',
    entityType: 'people_or_nation',
    labelArabic: 'آل فرعون',
    labelEnglish: "Pharaoh's people",
    aliasesArabic: ['آل فرعون'],
    aliasesEnglish: ["Pharaoh's people"],
    transliterations: ['Aal Firawn'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_people_quraysh',
    entityType: 'people_or_nation',
    labelArabic: 'قريش',
    labelEnglish: 'Quraysh',
    aliasesArabic: ['قريش'],
    aliasesEnglish: ['Quraysh'],
    transliterations: ['Quraysh'],
  }),
  seed({
    entityId: 'entity_people_yajuj_majuj',
    entityType: 'people_or_nation',
    labelArabic: 'يأجوج ومأجوج',
    labelEnglish: 'Gog and Magog',
    aliasesArabic: ['يأجوج', 'ومأجوج', 'مأجوج'],
    aliasesEnglish: ['Yajuj', 'Majuj', 'Gog', 'Magog'],
    transliterations: ['Yajuj Majuj'],
    relatedStories: ['story_dhulqarnayn'],
  }),
  seed({
    entityId: 'entity_people_saba',
    entityType: 'people_or_nation',
    labelArabic: 'سبأ',
    labelEnglish: 'Saba',
    aliasesArabic: ['سبإ', 'سبأ'],
    aliasesEnglish: ['Saba', 'Sheba'],
    transliterations: ['Saba'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_people_ashab_ukhdud',
    entityType: 'people_or_nation',
    labelArabic: 'أصحاب الأخدود',
    labelEnglish: 'People of the Ditch',
    aliasesArabic: ['أصحاب الأخدود', 'أصحب الأخدود'],
    aliasesEnglish: ['People of the Ditch'],
    transliterations: ['Ashab al-Ukhdud'],
    relatedStories: ['story_ukhdud'],
  }),
  seed({
    entityId: 'entity_people_hawariyyun',
    entityType: 'people_or_nation',
    labelArabic: 'الحواريون',
    labelEnglish: 'Disciples of Isa',
    aliasesArabic: ['الحواريون', 'الحواريين'],
    aliasesEnglish: ['Disciples', 'Apostles'],
    transliterations: ['Hawariyyun'],
    relatedStories: ['story_isa', 'story_table_spread'],
    knownRelatives: [rel('entity_prophet_isa', 'family_of')],
  }),
];

// ---------------------------------------------------------------------------
// 4. Animals
// ---------------------------------------------------------------------------

export const ANIMAL_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_animal_naqah',
    entityType: 'animal',
    labelArabic: 'ناقة صالح',
    labelEnglish: 'She-camel of Salih',
    aliasesArabic: ['ناقة الله'],
    aliasesEnglish: ['She-camel'],
    transliterations: ['Naqat Allah'],
    relatedStories: ['story_salih'],
  }),
  seed({
    entityId: 'entity_animal_hoopoe',
    entityType: 'animal',
    labelArabic: 'الهدهد',
    labelEnglish: 'Hoopoe',
    aliasesArabic: ['الهدهد'],
    aliasesEnglish: ['Hoopoe'],
    transliterations: ['Hudhud'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_animal_ants',
    entityType: 'animal',
    labelArabic: 'النمل',
    labelEnglish: 'Ants',
    aliasesArabic: ['النمل', 'نملة'],
    aliasesEnglish: ['Ant', 'Ants'],
    transliterations: ['Naml'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_animal_whale',
    entityType: 'animal',
    labelArabic: 'حوت يونس',
    labelEnglish: 'Whale of Yunus',
    aliasesArabic: ['الحوت'],
    aliasesEnglish: ['Whale', 'Great Fish'],
    transliterations: ['Hut'],
    relatedStories: ['story_yunus'],
  }),
  seed({
    entityId: 'entity_animal_dog_cave',
    entityType: 'animal',
    labelArabic: 'كلب أصحاب الكهف',
    labelEnglish: 'Dog of the Cave',
    aliasesArabic: ['كلبهم'],
    aliasesEnglish: ['Dog of the Cave'],
    transliterations: ['Kalbuhum'],
    relatedStories: ['story_kahf'],
  }),
  seed({
    entityId: 'entity_animal_elephant',
    entityType: 'animal',
    labelArabic: 'الفيل',
    labelEnglish: 'Elephant',
    aliasesArabic: ['الفيل'],
    aliasesEnglish: ['Elephant'],
    transliterations: ['Fil'],
    relatedStories: ['story_elephant'],
  }),
];

// ---------------------------------------------------------------------------
// 5. Places
// ---------------------------------------------------------------------------

export const PLACE_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_place_makkah',
    entityType: 'place',
    labelArabic: 'مكة المكرمة',
    labelEnglish: 'Makkah',
    aliasesArabic: ['مكة', 'بكة', 'أم القرى', 'البلد الأمين'],
    aliasesEnglish: ['Makkah', 'Mecca', 'Bakkah'],
    transliterations: ['Makkah'],
  }),
  seed({
    entityId: 'entity_place_madinah',
    entityType: 'place',
    labelArabic: 'المدينة المنورة',
    labelEnglish: 'Madinah',
    aliasesArabic: ['يثرب'],
    aliasesEnglish: ['Madinah', 'Yathrib'],
    transliterations: ['Madinah'],
    warnings: ['Bare "المدينة" omitted — generic "the city" usage is too broad.'],
  }),
  seed({
    entityId: 'entity_place_egypt',
    entityType: 'place',
    labelArabic: 'مصر',
    labelEnglish: 'Egypt',
    aliasesArabic: ['مصر'],
    aliasesEnglish: ['Egypt', 'Misr'],
    transliterations: ['Misr'],
    relatedStories: ['story_musa', 'story_yusuf'],
  }),
  seed({
    entityId: 'entity_place_sinai',
    entityType: 'place',
    labelArabic: 'طور سيناء',
    labelEnglish: 'Mount Sinai',
    aliasesArabic: ['الطور', 'طور سيناء', 'طور سينين'],
    aliasesEnglish: ['Mount Sinai', 'Tur'],
    transliterations: ['Tur Sina'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_place_cave',
    entityType: 'place',
    labelArabic: 'الكهف',
    labelEnglish: 'The Cave',
    aliasesArabic: ['الكهف'],
    aliasesEnglish: ['The Cave'],
    transliterations: ['Al-Kahf'],
    relatedStories: ['story_kahf'],
  }),
  seed({
    entityId: 'entity_place_jerusalem',
    entityType: 'place',
    labelArabic: 'بيت المقدس',
    labelEnglish: 'Jerusalem',
    // The Quran refers to it as ٱلْمَسْجِدِ ٱلْأَقْصَا (17:1); "بيت المقدس" is the
    // traditional name and does not appear in the Quranic text itself.
    aliasesArabic: ['الأقصا', 'الأقصى', 'بيت المقدس'],
    aliasesEnglish: ['Jerusalem', 'Al-Aqsa'],
    transliterations: ['Bayt al-Maqdis'],
    warnings: ['"بيت المقدس" is not in the Quran text directly; only الأقصى (17:1) is.'],
  }),
  seed({
    entityId: 'entity_place_kaaba',
    entityType: 'place',
    labelArabic: 'الكعبة',
    labelEnglish: 'The Kaaba',
    aliasesArabic: ['الكعبة', 'البيت الحرام', 'البيت العتيق'],
    aliasesEnglish: ['Kaaba', 'Sacred House'],
    transliterations: ['Kaaba'],
  }),
];

// ---------------------------------------------------------------------------
// 6. Objects
// ---------------------------------------------------------------------------

export const OBJECT_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_object_ark',
    entityType: 'object',
    labelArabic: 'سفينة نوح',
    labelEnglish: 'Ark of Nuh',
    aliasesArabic: ['الفلك', 'السفينة'],
    aliasesEnglish: ['Ark'],
    transliterations: ['Safinat Nuh'],
    relatedStories: ['story_nuh'],
  }),
  seed({
    entityId: 'entity_object_staff_musa',
    entityType: 'object',
    labelArabic: 'عصا موسى',
    labelEnglish: 'Staff of Musa',
    aliasesArabic: ['عصاه', 'عصاك'],
    aliasesEnglish: ['Staff of Musa'],
    transliterations: ['Asa'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_object_tablets',
    entityType: 'object',
    labelArabic: 'الألواح',
    labelEnglish: 'Tablets',
    aliasesArabic: ['الألواح'],
    aliasesEnglish: ['Tablets'],
    transliterations: ['Alwah'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_object_table_spread',
    entityType: 'object',
    labelArabic: 'المائدة',
    labelEnglish: 'Table Spread',
    aliasesArabic: ['المائدة', 'مائدة'],
    aliasesEnglish: ['Table Spread'],
    transliterations: ['Maidah'],
    relatedStories: ['story_table_spread'],
  }),
  seed({
    entityId: 'entity_object_throne_bilqis',
    entityType: 'object',
    labelArabic: 'عرش بلقيس',
    labelEnglish: 'Throne of Bilqis',
    aliasesArabic: ['عرشها'],
    aliasesEnglish: ['Throne of Bilqis'],
    transliterations: ['Arsh Bilqis'],
    relatedStories: ['story_bilqis'],
  }),
  seed({
    entityId: 'entity_object_barrier',
    entityType: 'object',
    labelArabic: 'سد ذي القرنين',
    labelEnglish: 'Wall of Dhul-Qarnayn',
    aliasesArabic: ['ردما', 'السد'],
    aliasesEnglish: ['Wall', 'Barrier'],
    transliterations: ['Sadd'],
    relatedStories: ['story_dhulqarnayn'],
  }),
];

// ---------------------------------------------------------------------------
// 7. Scriptures
// ---------------------------------------------------------------------------

export const SCRIPTURE_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_scripture_quran',
    entityType: 'scripture',
    labelArabic: 'القرآن الكريم',
    labelEnglish: 'The Quran',
    aliasesArabic: ['القرآن', 'الفرقان', 'الذكر', 'الكتاب'],
    aliasesEnglish: ['Quran', 'Furqan'],
    transliterations: ['Quran'],
    warnings: ['Generic aliases ("الذكر", "الكتاب") match many non-scripture contexts; scanner downgrades.'],
  }),
  seed({
    entityId: 'entity_scripture_tawrat',
    entityType: 'scripture',
    labelArabic: 'التوراة',
    labelEnglish: 'Tawrat (Torah)',
    // Quran rasm: ٱلتَّوْرَىٰةَ → after norm (ى→ي, ة→ه) → التوريه.
    aliasesArabic: ['التوراة', 'التوريه'],
    aliasesEnglish: ['Torah', 'Tawrat'],
    transliterations: ['Tawrat'],
  }),
  seed({
    entityId: 'entity_scripture_injil',
    entityType: 'scripture',
    labelArabic: 'الإنجيل',
    labelEnglish: 'Injil (Gospel)',
    aliasesArabic: ['الإنجيل'],
    aliasesEnglish: ['Gospel', 'Injil'],
    transliterations: ['Injil'],
  }),
  seed({
    entityId: 'entity_scripture_zabur',
    entityType: 'scripture',
    labelArabic: 'الزبور',
    labelEnglish: 'Zabur (Psalms)',
    aliasesArabic: ['الزبور'],
    aliasesEnglish: ['Psalms', 'Zabur'],
    transliterations: ['Zabur'],
  }),
  seed({
    entityId: 'entity_scripture_suhuf_ibrahim',
    entityType: 'scripture',
    labelArabic: 'صحف إبراهيم',
    labelEnglish: 'Scrolls of Ibrahim',
    // Quran rasm uses ابرهيم — match the normalised form.
    aliasesArabic: ['صحف إبراهيم', 'صحف ابرهيم'],
    aliasesEnglish: ['Scrolls of Ibrahim'],
    transliterations: ['Suhuf Ibrahim'],
  }),
];

// ---------------------------------------------------------------------------
// 8. Events
// ---------------------------------------------------------------------------

export const EVENT_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_event_flood',
    entityType: 'event',
    labelArabic: 'الطوفان',
    labelEnglish: 'The Flood',
    aliasesArabic: ['الطوفان'],
    aliasesEnglish: ['Flood', 'Deluge'],
    transliterations: ['Tufan'],
    relatedStories: ['story_nuh'],
  }),
  seed({
    entityId: 'entity_event_sea_crossing',
    entityType: 'event',
    labelArabic: 'انفلاق البحر',
    labelEnglish: 'Crossing of the Sea',
    aliasesArabic: ['فانفلق'],
    aliasesEnglish: ['Sea splitting'],
    transliterations: ['Infilaq al-bahr'],
    relatedStories: ['story_musa'],
  }),
  seed({
    entityId: 'entity_event_virgin_birth',
    entityType: 'event',
    labelArabic: 'ولادة عيسى عليه السلام',
    labelEnglish: 'Birth of Isa',
    aliasesArabic: ['فأجاءها المخاض'],
    aliasesEnglish: ['Birth of Isa'],
    transliterations: ['Wiladat Isa'],
    relatedStories: ['story_maryam'],
  }),
  seed({
    entityId: 'entity_event_glad_tidings',
    entityType: 'event',
    labelArabic: 'بشارة الملائكة لمريم',
    labelEnglish: 'Glad tidings to Maryam',
    aliasesArabic: ['يبشرك', 'يبشرك الله'],
    aliasesEnglish: ['Glad tidings'],
    transliterations: ['Bishara'],
    relatedStories: ['story_maryam'],
    warnings: ['"يبشرك" matches multiple annunciation contexts (also Zakariyya); needs_review story_context.'],
  }),
  seed({
    entityId: 'entity_event_table_descended',
    entityType: 'event',
    labelArabic: 'نزول المائدة',
    labelEnglish: 'Descent of the Table',
    aliasesArabic: ['أنزل علينا مائدة'],
    aliasesEnglish: ['Table descended'],
    transliterations: ['Nuzul al-Maidah'],
    relatedStories: ['story_table_spread'],
  }),
];

// ---------------------------------------------------------------------------
// 9. Angels
// ---------------------------------------------------------------------------

export const ANGEL_SEEDS: EntitySeed[] = [
  seed({
    entityId: 'entity_angel_jibreel',
    entityType: 'angel',
    labelArabic: 'جبريل عليه السلام',
    labelEnglish: 'Jibreel (Gabriel)',
    aliasesArabic: ['جبريل', 'الروح الأمين', 'روح القدس'],
    aliasesEnglish: ['Jibreel', 'Gabriel'],
    transliterations: ['Jibreel', 'Gabriel'],
  }),
  seed({
    entityId: 'entity_angel_mikail',
    entityType: 'angel',
    labelArabic: 'ميكال عليه السلام',
    labelEnglish: 'Mikail (Michael)',
    // Quran rasm: مِيكَىٰلَ → ميكيل after ى→ي + dagger-alif strip.
    aliasesArabic: ['ميكال', 'ميكائيل', 'ميكيل'],
    aliasesEnglish: ['Mikail', 'Michael'],
    transliterations: ['Mikail'],
  }),
  seed({
    entityId: 'entity_angel_malak_mawt',
    entityType: 'angel',
    labelArabic: 'ملك الموت',
    labelEnglish: 'Angel of Death',
    aliasesArabic: ['ملك الموت'],
    aliasesEnglish: ['Angel of Death'],
    transliterations: ['Malak al-Mawt'],
  }),
];

// ---------------------------------------------------------------------------
// 10. Combined export
// ---------------------------------------------------------------------------

export const QURAN_ENTITY_SEEDS: EntitySeed[] = [
  ...PROPHET_SEEDS,
  ...PERSON_SEEDS,
  ...PEOPLE_SEEDS,
  ...ANIMAL_SEEDS,
  ...PLACE_SEEDS,
  ...OBJECT_SEEDS,
  ...SCRIPTURE_SEEDS,
  ...EVENT_SEEDS,
  ...ANGEL_SEEDS,
];

// ---------------------------------------------------------------------------
// Lookup helpers
// ---------------------------------------------------------------------------

export function getEntitySeedById(entityId: string): EntitySeed | undefined {
  return QURAN_ENTITY_SEEDS.find((e) => e.entityId === entityId);
}

export function getEntitySeedsByType(type: QuranEntityType): EntitySeed[] {
  return QURAN_ENTITY_SEEDS.filter((e) => e.entityType === type);
}

export function getAllEntityIds(): string[] {
  return QURAN_ENTITY_SEEDS.map((e) => e.entityId);
}
