/**
 * Quranic Root Families — most frequent trilateral Arabic roots in the Quran.
 *
 * Sources:
 *   - Quranic Arabic Corpus (quranic-research.net)
 *   - Lane's Lexicon (E.W. Lane)
 *   - Hans Wehr Arabic-English Dictionary
 *   - Frequency data: Buckwalter/Quranic Corpus analyses
 *
 * Safety: Meanings are from classical lexica only. No AI-generated definitions.
 * Frequency counts are approximate (scholarly corpus estimates).
 */

export interface RootDerivative {
  arabic: string;
  transliteration: string;
  partOfSpeech: string;
  meaningEn: string;
  meaningAr: string;
  frequencyInQuran: number;
  exampleRef?: string;   // e.g. "2:152"
}

export interface RootFamily {
  id: string;
  rootArabic: string;           // e.g. "ك-ت-ب"
  rootTransliteration: string;  // e.g. "K-T-B"
  coreMeaningEn: string;
  coreMeaningAr: string;
  totalOccurrences: number;     // approx combined frequency
  noteEn: string;
  noteAr: string;
  category: RootCategory;
  derivatives: RootDerivative[];
}

export type RootCategory =
  | 'worship'
  | 'knowledge'
  | 'ethics'
  | 'cosmology'
  | 'community'
  | 'prophethood';

export const ROOT_CATEGORY_META: Record<RootCategory, { labelEn: string; labelAr: string; emoji: string; color: string }> = {
  worship:     { labelEn: 'Worship',     labelAr: 'العبادة',    emoji: '🕌', color: 'emerald' },
  knowledge:   { labelEn: 'Knowledge',   labelAr: 'المعرفة',   emoji: '📖', color: 'blue'    },
  ethics:      { labelEn: 'Ethics',      labelAr: 'الأخلاق',   emoji: '⚖️', color: 'violet'  },
  cosmology:   { labelEn: 'Cosmology',   labelAr: 'الكون',     emoji: '🌌', color: 'indigo'  },
  community:   { labelEn: 'Community',   labelAr: 'المجتمع',   emoji: '🤝', color: 'amber'   },
  prophethood: { labelEn: 'Prophethood', labelAr: 'النبوة',    emoji: '✨', color: 'rose'    },
};

export const ROOT_FAMILIES: readonly RootFamily[] = [
  {
    id: 'root_qlm',
    rootArabic: 'ع-ل-م',
    rootTransliteration: 'ʿ-L-M',
    coreMeaningEn: 'To know, to mark/brand (whence: knowledge, world)',
    coreMeaningAr: 'العلم والمعرفة والإدراك',
    totalOccurrences: 854,
    category: 'knowledge',
    noteEn: 'The most frequent root related to cognitive states in the Quran. ʿAlim (All-Knowing) is among the 99 Names of Allah.',
    noteAr: 'الجذر المعرفي الأكثر ورودًا في القرآن. "العليم" من أسماء الله الحسنى.',
    derivatives: [
      { arabic: 'عَلِمَ', transliteration: 'ʿalima', partOfSpeech: 'verb (perfect)', meaningEn: 'he knew', meaningAr: 'عَلِمَ', frequencyInQuran: 149, exampleRef: '2:216' },
      { arabic: 'عِلْم', transliteration: 'ʿilm', partOfSpeech: 'noun', meaningEn: 'knowledge', meaningAr: 'علم', frequencyInQuran: 105, exampleRef: '58:11' },
      { arabic: 'عَالَم', transliteration: 'ʿālam', partOfSpeech: 'noun', meaningEn: 'world, realm', meaningAr: 'عالَم', frequencyInQuran: 73, exampleRef: '1:2' },
      { arabic: 'عَلِيم', transliteration: 'ʿAlīm', partOfSpeech: 'adjective (divine attribute)', meaningEn: 'All-Knowing', meaningAr: 'عليم', frequencyInQuran: 157, exampleRef: '2:32' },
      { arabic: 'مُعَلِّم', transliteration: 'muʿallim', partOfSpeech: 'noun (agent)', meaningEn: 'teacher', meaningAr: 'معلم', frequencyInQuran: 3, exampleRef: '96:4' },
      { arabic: 'تَعَلَّمَ', transliteration: 'taʿallama', partOfSpeech: 'verb (V pattern)', meaningEn: 'to learn', meaningAr: 'تعلّم', frequencyInQuran: 2, exampleRef: '2:102' },
      { arabic: 'أَعْلَم', transliteration: 'aʿlam', partOfSpeech: 'adjective (elative)', meaningEn: 'most knowing', meaningAr: 'أعلم', frequencyInQuran: 48, exampleRef: '6:117' },
    ],
  },
  {
    id: 'root_ktb',
    rootArabic: 'ك-ت-ب',
    rootTransliteration: 'K-T-B',
    coreMeaningEn: 'To write, to prescribe (whence: book, scripture, decree)',
    coreMeaningAr: 'الكتابة والتدوين والفرض',
    totalOccurrences: 319,
    category: 'knowledge',
    noteEn: 'Central to the Quranic worldview — the Quran itself is "al-Kitab" (the Book). Katabna expresses divine decrees.',
    noteAr: 'محوري في الرؤية القرآنية — القرآن نفسه هو "الكتاب". كَتَبْنَا تعبّر عن القضاء الإلهي.',
    derivatives: [
      { arabic: 'كَتَبَ', transliteration: 'kataba', partOfSpeech: 'verb (perfect)', meaningEn: 'he wrote / He prescribed', meaningAr: 'كَتَبَ', frequencyInQuran: 58, exampleRef: '2:183' },
      { arabic: 'كِتَاب', transliteration: 'kitāb', partOfSpeech: 'noun', meaningEn: 'book, scripture', meaningAr: 'كتاب', frequencyInQuran: 230, exampleRef: '2:2' },
      { arabic: 'كَاتِب', transliteration: 'kātib', partOfSpeech: 'noun (agent)', meaningEn: 'scribe, writer', meaningAr: 'كاتب', frequencyInQuran: 5, exampleRef: '2:282' },
      { arabic: 'مَكْتُوب', transliteration: 'maktūb', partOfSpeech: 'passive participle', meaningEn: 'written (decreed)', meaningAr: 'مكتوب', frequencyInQuran: 2, exampleRef: '7:157' },
      { arabic: 'اكْتَتَبَ', transliteration: 'iktātaba', partOfSpeech: 'verb (VIII pattern)', meaningEn: 'to copy for oneself', meaningAr: 'اكتتب', frequencyInQuran: 1, exampleRef: '25:5' },
    ],
  },
  {
    id: 'root_rhm',
    rootArabic: 'ر-ح-م',
    rootTransliteration: 'R-Ḥ-M',
    coreMeaningEn: 'Mercy, womb — enveloping compassion and nurture',
    coreMeaningAr: 'الرحمة — المحبة والعطف الشاملان',
    totalOccurrences: 339,
    category: 'ethics',
    noteEn: 'Two of the three parts of the Basmala come from this root: Ar-Raḥmān and Ar-Raḥīm. The womb (raḥim) shares the same root — mercy as intimate nurture.',
    noteAr: 'جزءان من البسملة من هذا الجذر: الرحمن والرحيم. "الرحم" يشترك في نفس الجذر — رحمة بالغة القرب كحنان الأم.',
    derivatives: [
      { arabic: 'رَحِمَ', transliteration: 'raḥima', partOfSpeech: 'verb (perfect)', meaningEn: 'to have mercy on', meaningAr: 'رَحِمَ', frequencyInQuran: 48, exampleRef: '7:151' },
      { arabic: 'رَحْمَة', transliteration: 'raḥmah', partOfSpeech: 'noun', meaningEn: 'mercy, compassion', meaningAr: 'رحمة', frequencyInQuran: 79, exampleRef: '7:156' },
      { arabic: 'الرَّحْمَن', transliteration: 'Ar-Raḥmān', partOfSpeech: 'divine attribute', meaningEn: 'The Most Gracious (encompassing mercy)', meaningAr: 'الرحمن', frequencyInQuran: 57, exampleRef: '1:3' },
      { arabic: 'الرَّحِيم', transliteration: 'Ar-Raḥīm', partOfSpeech: 'divine attribute', meaningEn: 'The Most Merciful (special mercy for believers)', meaningAr: 'الرحيم', frequencyInQuran: 115, exampleRef: '1:3' },
      { arabic: 'رَحِيم', transliteration: 'raḥīm', partOfSpeech: 'adjective', meaningEn: 'merciful', meaningAr: 'رحيم', frequencyInQuran: 96, exampleRef: '9:128' },
      { arabic: 'رَحِم', transliteration: 'raḥim', partOfSpeech: 'noun', meaningEn: 'womb; kinship', meaningAr: 'رَحِم', frequencyInQuran: 13, exampleRef: '4:1' },
    ],
  },
  {
    id: 'root_sbr',
    rootArabic: 'ص-ب-ر',
    rootTransliteration: 'Ṣ-B-R',
    coreMeaningEn: 'To bind, withhold — patience, steadfast endurance',
    coreMeaningAr: 'الصبر والثبات والتحمل',
    totalOccurrences: 103,
    category: 'ethics',
    noteEn: 'Ṣabr in the Quran is active, not passive — it means to withhold the soul from despair, the tongue from complaint, and the body from unlawful reaction.',
    noteAr: 'الصبر في القرآن فعّال لا سلبي — شدّ النفس عن اليأس واللسان عن الشكوى والجسد عن الفعل المحرّم.',
    derivatives: [
      { arabic: 'صَبَرَ', transliteration: 'ṣabara', partOfSpeech: 'verb (perfect)', meaningEn: 'to be patient', meaningAr: 'صَبَرَ', frequencyInQuran: 41, exampleRef: '2:153' },
      { arabic: 'صَبْر', transliteration: 'ṣabr', partOfSpeech: 'noun (maṣdar)', meaningEn: 'patience, steadfastness', meaningAr: 'صبر', frequencyInQuran: 11, exampleRef: '2:45' },
      { arabic: 'صَابِر', transliteration: 'ṣābir', partOfSpeech: 'noun (agent)', meaningEn: 'one who is patient', meaningAr: 'صابر', frequencyInQuran: 16, exampleRef: '2:177' },
      { arabic: 'صَبُور', transliteration: 'ṣabūr', partOfSpeech: 'adjective (intensified)', meaningEn: 'very patient', meaningAr: 'صبور', frequencyInQuran: 2, exampleRef: '11:11' },
      { arabic: 'اصْطَبَرَ', transliteration: 'iṣṭabara', partOfSpeech: 'verb (VIII)', meaningEn: 'to persevere with firm resolve', meaningAr: 'اصطبر', frequencyInQuran: 3, exampleRef: '20:132' },
    ],
  },
  {
    id: 'root_dkr',
    rootArabic: 'ذ-ك-ر',
    rootTransliteration: 'D-K-R',
    coreMeaningEn: 'To remember, mention, warn — the root of dhikr (remembrance of Allah)',
    coreMeaningAr: 'الذكر والتذكر والتذكير',
    totalOccurrences: 292,
    category: 'worship',
    noteEn: 'This root commands "Remember Me and I will remember you" (2:152). The Quran itself is called "ad-Dhikr" — the reminder.',
    noteAr: 'هذا الجذر يحمل أمر "فَاذْكُرُونِي أَذْكُرْكُمْ" (2:152). القرآن نفسه يُسمى "الذكر".',
    derivatives: [
      { arabic: 'ذَكَرَ', transliteration: 'dhakara', partOfSpeech: 'verb (perfect)', meaningEn: 'to remember, to mention', meaningAr: 'ذَكَرَ', frequencyInQuran: 97, exampleRef: '2:198' },
      { arabic: 'ذِكْر', transliteration: 'dhikr', partOfSpeech: 'noun', meaningEn: 'remembrance; reminder; the Quran', meaningAr: 'ذكر', frequencyInQuran: 75, exampleRef: '15:9' },
      { arabic: 'تَذَكَّرَ', transliteration: 'tadhakkara', partOfSpeech: 'verb (V pattern)', meaningEn: 'to take heed, to be reminded', meaningAr: 'تذكّر', frequencyInQuran: 26, exampleRef: '38:29' },
      { arabic: 'مُذَكِّر', transliteration: 'mudhakkir', partOfSpeech: 'noun (agent)', meaningEn: 'one who reminds', meaningAr: 'مُذَكِّر', frequencyInQuran: 1, exampleRef: '88:21' },
      { arabic: 'ذَكَّرَ', transliteration: 'dhakkara', partOfSpeech: 'verb (II pattern)', meaningEn: 'to remind', meaningAr: 'ذكَّر', frequencyInQuran: 7, exampleRef: '51:55' },
    ],
  },
  {
    id: 'root_hmd',
    rootArabic: 'ح-م-د',
    rootTransliteration: 'Ḥ-M-D',
    coreMeaningEn: 'To praise wholeheartedly — genuine and deserved commendation',
    coreMeaningAr: 'الحمد والثناء المستحق',
    totalOccurrences: 68,
    category: 'worship',
    noteEn: "The Quran opens with \"Al-Ḥamdu lillāh\" — the Quran's most-repeated opening phrase. The Prophet ﷺ is named Muḥammad (the most praised) and Aḥmad.",
    noteAr: 'القرآن يفتتح بـ"الحمد لله". اسم النبي ﷺ محمد وأحمد كلاهما من هذا الجذر.',
    derivatives: [
      { arabic: 'حَمِدَ', transliteration: 'ḥamida', partOfSpeech: 'verb (perfect)', meaningEn: 'to praise', meaningAr: 'حَمِدَ', frequencyInQuran: 7, exampleRef: '9:112' },
      { arabic: 'الحَمْد', transliteration: 'al-ḥamd', partOfSpeech: 'noun', meaningEn: 'praise (to Allah)', meaningAr: 'الحمد', frequencyInQuran: 38, exampleRef: '1:2' },
      { arabic: 'مُحَمَّد', transliteration: 'Muḥammad', partOfSpeech: 'proper noun', meaningEn: 'the praised one', meaningAr: 'مُحَمَّد', frequencyInQuran: 4, exampleRef: '3:144' },
      { arabic: 'أَحْمَد', transliteration: 'Aḥmad', partOfSpeech: 'proper noun (elative)', meaningEn: 'most praiseworthy', meaningAr: 'أحمد', frequencyInQuran: 1, exampleRef: '61:6' },
      { arabic: 'حَمِيد', transliteration: 'Ḥamīd', partOfSpeech: 'divine attribute', meaningEn: 'All-Praiseworthy', meaningAr: 'حميد', frequencyInQuran: 17, exampleRef: '14:8' },
    ],
  },
  {
    id: 'root_slm',
    rootArabic: 'س-ل-م',
    rootTransliteration: 'S-L-M',
    coreMeaningEn: 'To be safe, whole, at peace — the root of Islam, Muslim, Salam',
    coreMeaningAr: 'السلامة والكمال والإسلام',
    totalOccurrences: 172,
    category: 'worship',
    noteEn: 'This root gives Islam its name — "submission to Allah in safety." Salām (peace) is the greeting of Paradise; As-Salām is one of the divine Names.',
    noteAr: 'هذا الجذر يُعطي الإسلام اسمه — الاستسلام لله في أمان. السلام تحية الجنة وهو اسم إلهي.',
    derivatives: [
      { arabic: 'إِسْلَام', transliteration: 'islām', partOfSpeech: 'noun (IV maṣdar)', meaningEn: 'submission to God; Islam', meaningAr: 'إسلام', frequencyInQuran: 8, exampleRef: '3:19' },
      { arabic: 'سَلَام', transliteration: 'salām', partOfSpeech: 'noun', meaningEn: 'peace, greeting of peace', meaningAr: 'سلام', frequencyInQuran: 43, exampleRef: '6:54' },
      { arabic: 'مُسْلِم', transliteration: 'muslim', partOfSpeech: 'noun (active participle)', meaningEn: 'one who submits to God', meaningAr: 'مُسلم', frequencyInQuran: 38, exampleRef: '2:131' },
      { arabic: 'السَّلَام', transliteration: 'As-Salām', partOfSpeech: 'divine attribute', meaningEn: 'The Source of Peace', meaningAr: 'السلام', frequencyInQuran: 1, exampleRef: '59:23' },
      { arabic: 'سَلَّمَ', transliteration: 'sallama', partOfSpeech: 'verb (II pattern)', meaningEn: 'to send peace upon; to submit', meaningAr: 'سلّم', frequencyInQuran: 13, exampleRef: '4:65' },
      { arabic: 'أَسْلَمَ', transliteration: 'aslama', partOfSpeech: 'verb (IV pattern)', meaningEn: 'to surrender to God', meaningAr: 'أسلم', frequencyInQuran: 22, exampleRef: '2:112' },
    ],
  },
  {
    id: 'root_hdy',
    rootArabic: 'ه-د-ي',
    rootTransliteration: 'H-D-Y',
    coreMeaningEn: 'To guide, lead to the right way; the root of hidāyah (guidance)',
    coreMeaningAr: 'الهداية والإرشاد والتوجيه',
    totalOccurrences: 316,
    category: 'prophethood',
    noteEn: 'Every Muslim asks for hidāyah 17+ times daily in Al-Fatihah. Al-Hādī (The Guide) is a divine name.',
    noteAr: 'كل مسلم يطلب الهداية 17+ مرة يومياً في الفاتحة. "الهادي" اسم إلهي.',
    derivatives: [
      { arabic: 'هَدَى', transliteration: 'hadā', partOfSpeech: 'verb (perfect)', meaningEn: 'to guide', meaningAr: 'هَدَى', frequencyInQuran: 143, exampleRef: '1:6' },
      { arabic: 'هِدَايَة', transliteration: 'hidāyah', partOfSpeech: 'noun', meaningEn: 'guidance', meaningAr: 'هداية', frequencyInQuran: 3, exampleRef: '2:2' },
      { arabic: 'هُدَى', transliteration: 'hudan', partOfSpeech: 'noun (accusative of purpose)', meaningEn: 'guidance (as a quality)', meaningAr: 'هُدًى', frequencyInQuran: 89, exampleRef: '2:2' },
      { arabic: 'هَادٍ', transliteration: 'hādin', partOfSpeech: 'noun (active participle)', meaningEn: 'guide', meaningAr: 'هادٍ', frequencyInQuran: 12, exampleRef: '13:7' },
      { arabic: 'اهْتَدَى', transliteration: 'ihtadā', partOfSpeech: 'verb (VIII)', meaningEn: 'to be guided, to follow the right path', meaningAr: 'اهتدى', frequencyInQuran: 42, exampleRef: '7:178' },
    ],
  },
  {
    id: 'root_qra',
    rootArabic: 'ق-ر-أ',
    rootTransliteration: 'Q-R-Ā',
    coreMeaningEn: 'To read, recite — the root of Quran itself',
    coreMeaningAr: 'القراءة والتلاوة — جذر كلمة القرآن',
    totalOccurrences: 90,
    category: 'knowledge',
    noteEn: "The very first word revealed was \"Iqraʾ\" (Read/Recite). The Quran's name derives from this root — the Book meant to be continually recited.",
    noteAr: 'أول كلمة نزلت "اقرأ". اسم "القرآن" مشتق من هذا الجذر — الكتاب الذي يُتلى باستمرار.',
    derivatives: [
      { arabic: 'قَرَأَ', transliteration: 'qaraʾa', partOfSpeech: 'verb (perfect)', meaningEn: 'to read, recite', meaningAr: 'قَرَأَ', frequencyInQuran: 17, exampleRef: '96:1' },
      { arabic: 'الْقُرْآن', transliteration: 'al-Qurʾān', partOfSpeech: 'proper noun', meaningEn: 'the Quran (the recitation)', meaningAr: 'القرآن', frequencyInQuran: 70, exampleRef: '2:185' },
      { arabic: 'اقْرَأْ', transliteration: 'iqraʾ', partOfSpeech: 'imperative', meaningEn: 'Read! Recite!', meaningAr: 'اقرأ', frequencyInQuran: 5, exampleRef: '96:1' },
      { arabic: 'قِرَاءَة', transliteration: 'qirāʾah', partOfSpeech: 'noun (maṣdar II)', meaningEn: 'recitation, reading', meaningAr: 'قراءة', frequencyInQuran: 1, exampleRef: '17:78' },
    ],
  },
  {
    id: 'root_wqy',
    rootArabic: 'و-ق-ي',
    rootTransliteration: 'W-Q-Y',
    coreMeaningEn: 'To protect, guard from harm — the root of taqwā (God-consciousness)',
    coreMeaningAr: 'الوقاية والحفظ من الشر — جذر "التقوى"',
    totalOccurrences: 258,
    category: 'ethics',
    noteEn: "Taqwā (from this root) is the Quran's central ethical concept — a shield (wiqāyah) of God-consciousness that protects one from sin.",
    noteAr: 'التقوى (من هذا الجذر) هي المحور الأخلاقي في القرآن — وقاية روحية من المعاصي.',
    derivatives: [
      { arabic: 'وَقَى', transliteration: 'waqā', partOfSpeech: 'verb (perfect)', meaningEn: 'to protect, shield', meaningAr: 'وَقَى', frequencyInQuran: 14, exampleRef: '40:9' },
      { arabic: 'تَقْوَى', transliteration: 'taqwā', partOfSpeech: 'noun (maṣdar V)', meaningEn: 'God-consciousness, piety', meaningAr: 'تقوى', frequencyInQuran: 87, exampleRef: '2:2' },
      { arabic: 'مُتَّقِي', transliteration: 'muttaqī', partOfSpeech: 'noun (active participle VIII)', meaningEn: 'God-fearing, pious person', meaningAr: 'مُتَّقِي', frequencyInQuran: 57, exampleRef: '2:2' },
      { arabic: 'وِقَايَة', transliteration: 'wiqāyah', partOfSpeech: 'noun', meaningEn: 'protection, shield', meaningAr: 'وقاية', frequencyInQuran: 2, exampleRef: '76:11' },
      { arabic: 'اتَّقَى', transliteration: 'ittaqā', partOfSpeech: 'verb (VIII pattern)', meaningEn: 'to fear Allah, to be pious', meaningAr: 'اتّقى', frequencyInQuran: 60, exampleRef: '2:189' },
    ],
  },
];
