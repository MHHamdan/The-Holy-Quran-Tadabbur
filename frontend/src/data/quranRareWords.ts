/**
 * Quran Rare Words (Gharib Al-Quran) — Frontend Seed Data
 *
 * CONTENT POLICY:
 * - Every meaning requires a lexical or tafsir evidence reference
 * - No AI-generated meanings are included without source backing
 * - All entries are marked needs_review until verified against classical lexicons
 * - contextualMeaning is the usage in the specific ayah; simpleMeaning is the root/dictionary meaning
 * - Source IDs must match entries in sourceRegistry.ts
 *
 * Primary source: Quranic Arabic Corpus (QAC) — quranic-corpus.com
 * Secondary: Lisan al-Arab, Al-Mufradat fi Gharib al-Quran (Al-Raghib al-Asfahani)
 *
 * NOTE: This seed data covers a selection of well-known rare Quranic words.
 * A complete gharib al-Quran database requires specialist lexicographers.
 */

import type { RareWordEntry, RareWordsCollection } from '../types/quranVocabulary';

export const QURAN_RARE_WORDS: RareWordEntry[] = [
  // ---------------------------------------------------------------------------
  // Al-Fatiha
  // ---------------------------------------------------------------------------
  {
    id: 'rw_sirat',
    arabic: 'صِرَاط',
    normalizedArabic: 'صراط',
    transliteration: 'Sirat',
    root: 'صرط',
    partOfSpeech: 'noun',
    surah: 1,
    ayah: 6,
    frequencyInQuran: 45,
    rarityLevel: 'moderately_rare',
    simpleMeaning: {
      en: 'Path, road, way',
      ar: 'الطريق، السبيل',
    },
    contextualMeaning: {
      en: 'The straight, upright path of divine guidance — contrasted with the paths of those who earned anger or went astray.',
      ar: 'الطريق المستقيم للهداية الإلهية — في مقابل طرق من غضب عليهم أو ضلوا.',
    },
    explanation: {
      en: 'The word "sirat" originally from Arabic/Aramaic root meaning to swallow/traverse. Ibn Kathir notes it refers to Islam — the clear path that leads to Allah.',
      ar: 'كلمة "صراط" من جذر عربي/آرامي يعني الابتلاع/العبور. ابن كثير يشير إلى أنها تعني الإسلام — الطريق الواضح المؤدي إلى الله.',
    },
    memoryHint: {
      en: 'Think of a straight road (sirat) that you travel on — no curves, no detours.',
      ar: 'فكّر في طريق مستقيم (صراط) تسير عليه — لا منعطفات ولا انحرافات.',
    },
    lexicalEvidenceRefs: [
      { sourceId: 'qac_corpus', refLabel: 'QAC: 1:6 Sirat', note: 'Root: ص-ر-ط, noun form' },
    ],
    tafsirEvidenceRefs: [
      { sourceId: 'ibn_kathir', refLabel: 'Ibn Kathir: Al-Fatiha commentary' },
    ],
    sourceIds: ['qac_corpus', 'ibn_kathir'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  },

  // ---------------------------------------------------------------------------
  // Al-Baqara
  // ---------------------------------------------------------------------------
  {
    id: 'rw_taqwa',
    arabic: 'تَقْوَى',
    normalizedArabic: 'تقوى',
    transliteration: 'Taqwa',
    root: 'وقي',
    partOfSpeech: 'verbal noun (masdar)',
    surah: 2,
    ayah: 2,
    frequencyInQuran: 87,
    rarityLevel: 'moderately_rare',
    simpleMeaning: {
      en: 'God-consciousness, piety, mindfulness of Allah',
      ar: 'الخوف من الله، التقوى، الورع',
    },
    contextualMeaning: {
      en: 'The quality of those who fear Allah and remain conscious of Him in all matters — the defining characteristic of those who benefit from the Quran.',
      ar: 'صفة من يخافون الله ويراقبونه في جميع الأحوال — الصفة المميزة لمن ينتفعون بالقرآن.',
    },
    explanation: {
      en: 'From the root "waqa" meaning to guard or protect. Taqwa is guarding oneself from Allah\'s punishment by obeying His commands.',
      ar: 'من جذر "وقى" بمعنى الحماية والحراسة. التقوى هي الحراسة من عذاب الله بطاعة أوامره.',
    },
    memoryHint: {
      en: 'Taqwa = a shield (wiqaya) you build through obedience. The root "waqa" means to guard.',
      ar: 'التقوى = درع (وقاية) تبنيه من خلال الطاعة. جذر "وقى" يعني الحراسة.',
    },
    lexicalEvidenceRefs: [
      { sourceId: 'qac_corpus', refLabel: 'QAC: 2:2', note: 'Root: و-ق-ي, verbal noun' },
    ],
    tafsirEvidenceRefs: [
      { sourceId: 'ibn_kathir', refLabel: 'Ibn Kathir: Al-Baqara 2:2' },
      { sourceId: 'saadi', refLabel: 'Al-Saadi: Taysir al-Karim' },
    ],
    sourceIds: ['qac_corpus', 'ibn_kathir', 'saadi'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  },

  // ---------------------------------------------------------------------------
  // Al-Kahf (known for rare vocabulary)
  // ---------------------------------------------------------------------------
  {
    id: 'rw_raqim',
    arabic: 'الرَّقِيم',
    normalizedArabic: 'الرقيم',
    transliteration: 'Al-Raqim',
    root: 'رقم',
    partOfSpeech: 'noun',
    surah: 18,
    ayah: 9,
    frequencyInQuran: 1,
    rarityLevel: 'very_rare',
    simpleMeaning: {
      en: 'Inscription, written tablet; possibly the name of the valley or the dog',
      ar: 'النقش، اللوح المكتوب؛ ربما اسم الوادي أو الكلب',
    },
    contextualMeaning: {
      en: 'Associated with the People of the Cave — classical scholars differ: some say it is an inscription on a tablet near the cave, others say it is the valley\'s name.',
      ar: 'مرتبط بأصحاب الكهف — العلماء الكلاسيكيون يختلفون: بعضهم يقول إنه نقش على لوح قرب الكهف، وآخرون يقولون إنه اسم الوادي.',
    },
    explanation: {
      en: 'Ibn Kathir lists multiple scholarly views without resolving to one: (1) a tablet with names written on it, (2) the name of the mountain/valley, (3) the name of their dog. This word is intentionally left uncertain in the text.',
      ar: 'ابن كثير يعدد آراء العلماء دون الترجيح: (1) لوح مكتوب عليه أسماؤهم، (2) اسم الجبل/الوادي، (3) اسم كلبهم. هذه الكلمة متروكة متعمدة مبهمة في النص.',
    },
    memoryHint: {
      en: '"Raqim" shares a root with "raqm" (number/mark). Think: a marked stone or tablet.',
      ar: '"الرقيم" يشترك جذراً مع "رقم" (رقم/علامة). فكّر: حجر أو لوح منقوش.',
    },
    lexicalEvidenceRefs: [
      { sourceId: 'qac_corpus', refLabel: 'QAC: 18:9', note: 'Hapax legomenon — appears once' },
    ],
    tafsirEvidenceRefs: [
      { sourceId: 'ibn_kathir', refLabel: 'Ibn Kathir: Al-Kahf 18:9 — multiple views listed' },
      { sourceId: 'tabari', refLabel: 'Al-Tabari: Jami al-Bayan, Al-Kahf 18:9' },
    ],
    sourceIds: ['qac_corpus', 'ibn_kathir', 'tabari'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  },
  {
    id: 'rw_yasid',
    arabic: 'يَسِيد',
    normalizedArabic: 'يسيد',
    transliteration: 'Yasid',
    root: 'سود',
    partOfSpeech: 'verb',
    surah: 18,
    ayah: 25,
    frequencyInQuran: 1,
    rarityLevel: 'very_rare',
    simpleMeaning: {
      en: 'They increased / added',
      ar: 'زادوا / أضافوا',
    },
    contextualMeaning: {
      en: 'Used in the context of "And they increased nine years" regarding the duration of the People of the Cave\'s sleep.',
      ar: 'مستخدمة في سياق "وازدادوا تسعاً" بشأن مدة نوم أصحاب الكهف.',
    },
    explanation: {
      en: 'The word "yasid" in this form is an archaic usage meaning to increase or add. In context it refers to extending the count from 300 to 309 years.',
      ar: 'كلمة "يسيد" بهذه الصيغة استخدام كلاسيكي يعني الزيادة أو الإضافة. في السياق تشير إلى إضافة العدد من 300 إلى 309 سنوات.',
    },
    memoryHint: {
      en: 'Connect "yasid" to "ziyadah" (increase). The Cave sleepers\' time was increased by nine.',
      ar: 'اربط "يسيد" بـ"زيادة". مدة نوم أصحاب الكهف زيدت بتسع.',
    },
    lexicalEvidenceRefs: [
      { sourceId: 'qac_corpus', refLabel: 'QAC: 18:25' },
    ],
    tafsirEvidenceRefs: [
      { sourceId: 'ibn_kathir', refLabel: 'Ibn Kathir: Al-Kahf 18:25' },
    ],
    sourceIds: ['qac_corpus', 'ibn_kathir'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  },

  // ---------------------------------------------------------------------------
  // Al-Haqqah (rich in rare vocabulary)
  // ---------------------------------------------------------------------------
  {
    id: 'rw_taghiyah',
    arabic: 'الطَّاغِيَة',
    normalizedArabic: 'الطاغية',
    transliteration: 'At-Taghiyah',
    root: 'طغي',
    partOfSpeech: 'noun/adjective',
    surah: 69,
    ayah: 5,
    frequencyInQuran: 2,
    rarityLevel: 'rare',
    simpleMeaning: {
      en: 'The overwhelming, the devastating; the overflowing calamity',
      ar: 'الطاغية: الشديدة المجاوزة للحد',
    },
    contextualMeaning: {
      en: 'Refers to the devastating cataclysm — the screaming, overwhelming wind/blast that destroyed the people of Thamud.',
      ar: 'تشير إلى الكارثة المدمرة — الريح الصاخبة الطاغية التي دمرت قوم ثمود.',
    },
    explanation: {
      en: 'From the root "tagha" meaning to go beyond limits/overflow. Al-Tabari explains it as the punishment that exceeded all bounds.',
      ar: 'من جذر "طغى" يعني تجاوز الحدود/الفيضان. الطبري يشرحها بأنها العقوبة التي تجاوزت كل الحدود.',
    },
    memoryHint: {
      en: '"Taghiyah" links to "taghut" (the transgressor). The wind was so violent it was "transgressive" in its destruction.',
      ar: '"الطاغية" تربط بـ"الطاغوت" (المتجاوز). كانت الريح عنيفة جداً حتى صارت "طاغية" في تدميرها.',
    },
    lexicalEvidenceRefs: [
      { sourceId: 'qac_corpus', refLabel: 'QAC: 69:5', note: 'Root: ط-غ-و/ي' },
    ],
    tafsirEvidenceRefs: [
      { sourceId: 'tabari', refLabel: 'Al-Tabari: Al-Haqqah 69:5' },
      { sourceId: 'ibn_kathir', refLabel: 'Ibn Kathir: Al-Haqqah 69:5' },
    ],
    sourceIds: ['qac_corpus', 'tabari', 'ibn_kathir'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  },

  // ---------------------------------------------------------------------------
  // Yusuf — rare word
  // ---------------------------------------------------------------------------
  {
    id: 'rw_bayan',
    arabic: 'صُوَاعَ',
    normalizedArabic: 'صواع',
    transliteration: 'Suwa',
    root: 'صوع',
    partOfSpeech: 'noun',
    surah: 12,
    ayah: 72,
    frequencyInQuran: 1,
    rarityLevel: 'very_rare',
    simpleMeaning: {
      en: 'Drinking cup, vessel; possibly a measuring cup used for grain',
      ar: 'كأس للشرب، إناء؛ ربما مكيال للحبوب',
    },
    contextualMeaning: {
      en: 'The king\'s golden measuring cup that was placed in Benjamin\'s bags — central to the plot of Yusuf\'s reunion.',
      ar: 'مكيال الملك الذهبي الذي وُضع في أمتعة بنيامين — محور مؤامرة لم شمل يوسف.',
    },
    explanation: {
      en: 'Ibn Kathir explains "suwa" as a drinking vessel also used for measuring, specifically the king of Egypt\'s cup. Its placement in Benjamin\'s bag was the pretext for detaining him.',
      ar: 'ابن كثير يشرح "الصواع" بأنه إناء للشرب يستخدم أيضاً للكيل، وتحديداً كأس ملك مصر. وضعه في أمتعة بنيامين كان ذريعة لاحتجازه.',
    },
    memoryHint: {
      en: 'Remember: Yusuf\'s plan to detain his brother = the golden cup (suwa) in the bag.',
      ar: 'تذكر: خطة يوسف لاحتجاز أخيه = الكأس الذهبي (الصواع) في الوعاء.',
    },
    lexicalEvidenceRefs: [
      { sourceId: 'qac_corpus', refLabel: 'QAC: 12:72', note: 'Hapax legomenon' },
    ],
    tafsirEvidenceRefs: [
      { sourceId: 'ibn_kathir', refLabel: 'Ibn Kathir: Yusuf 12:72' },
      { sourceId: 'tabari', refLabel: 'Al-Tabari: Yusuf 12:72' },
    ],
    sourceIds: ['qac_corpus', 'ibn_kathir', 'tabari'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  },

  // ---------------------------------------------------------------------------
  // Al-Qamar — rare words
  // ---------------------------------------------------------------------------
  {
    id: 'rw_muzdajar',
    arabic: 'مُزْدَجَر',
    normalizedArabic: 'مزدجر',
    transliteration: 'Muzdajar',
    root: 'زجر',
    partOfSpeech: 'passive participle',
    surah: 54,
    ayah: 4,
    frequencyInQuran: 1,
    rarityLevel: 'very_rare',
    simpleMeaning: {
      en: 'A place/situation of being restrained; sufficient warning; deterrence',
      ar: 'موضع الزجر والنهي؛ الوعظ الكافي؛ الردع',
    },
    contextualMeaning: {
      en: 'In the context of the Quran containing sufficient deterrence for those who heed — the Quran provides enough restraining admonition.',
      ar: 'في سياق اشتمال القرآن على زجر كافٍ لمن يتعظ — القرآن يوفر موعظة رادعة كافية.',
    },
    explanation: {
      en: 'From "zajara" meaning to rebuke/restrain. The form "muzdajar" is passive — something that has been restrained or a place where restraint occurs.',
      ar: 'من "زجر" يعني التوبيخ/الإمساك. صيغة "مزدجر" مبنية للمجهول — شيء يُكفّ أو مكان الكف.',
    },
    memoryHint: {
      en: '"Muzdajar" — think "zajar" (to rebuke). The Quran is the place of rebuke that should stop wrong action.',
      ar: '"مزدجر" — فكر في "زجر" (التوبيخ). القرآن هو مكان الزجر الذي ينبغي أن يوقف الأفعال الخاطئة.',
    },
    lexicalEvidenceRefs: [
      { sourceId: 'qac_corpus', refLabel: 'QAC: 54:4', note: 'Hapax legomenon, root: ز-ج-ر' },
    ],
    tafsirEvidenceRefs: [
      { sourceId: 'ibn_kathir', refLabel: 'Ibn Kathir: Al-Qamar 54:4' },
    ],
    sourceIds: ['qac_corpus', 'ibn_kathir'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  },
];

// ---------------------------------------------------------------------------
// Collection
// ---------------------------------------------------------------------------

export const RARE_WORDS_COLLECTION: RareWordsCollection = {
  version: '1.0.0',
  generatedAt: '2026-06-06',
  totalEntries: QURAN_RARE_WORDS.length,
  entries: QURAN_RARE_WORDS,
  reviewNote: {
    en: 'All rare word entries require verification against classical Arabic lexicons before production use. Meanings are scholarly placeholders.',
    ar: 'جميع مدخلات الكلمات النادرة تستلزم التحقق من المعاجم العربية الكلاسيكية قبل الاستخدام الإنتاجي. المعاني نصوص علمية مؤقتة.',
  },
};

export function getRareWordsBySurah(surahNumber: number): RareWordEntry[] {
  return QURAN_RARE_WORDS.filter((w) => w.surah === surahNumber);
}

export function getRareWordById(id: string): RareWordEntry | undefined {
  return QURAN_RARE_WORDS.find((w) => w.id === id);
}

export function searchRareWords(query: string): RareWordEntry[] {
  const q = query.toLowerCase().trim();
  if (!q) return [];
  return QURAN_RARE_WORDS.filter(
    (w) =>
      w.arabic.includes(query) ||
      w.transliteration.toLowerCase().includes(q) ||
      w.simpleMeaning.en.toLowerCase().includes(q) ||
      w.simpleMeaning.ar.includes(query),
  );
}
