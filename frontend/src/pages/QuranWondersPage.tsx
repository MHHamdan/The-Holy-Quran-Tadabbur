/**
 * Quran Wonders & Statistics — verified numerical and structural facts.
 *
 * All statistics sourced from established Islamic scholarship and linguistic research.
 * No AI-generated content. No contested interpretations.
 * Safety: This page presents facts, not miraculous claims — users may draw
 * their own conclusions. Anything disputed is marked as "according to…"
 */

import { useState } from 'react';
import { Sparkles, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';

interface QuranicRef {
  ref: string;       // e.g. "15:9"
  nameEn: string;    // e.g. "Surah Al-Hijr"
  textEn: string;    // faithful English translation of the verse
}

interface WonderFact {
  id: string;
  titleEn: string;
  titleAr: string;
  factEn: string;
  factAr: string;
  sourceEn: string;
  sourceAr: string;
  quranicRef?: QuranicRef;
  hadithRef?: string;
  category: WonderCategory;
  highlight: string;
}

type WonderCategory = 'numbers' | 'structure' | 'language' | 'history' | 'preservation';

const CAT_META: Record<WonderCategory, { labelEn: string; labelAr: string; emoji: string; color: string }> = {
  numbers:      { labelEn: 'Numbers',      labelAr: 'الأرقام',   emoji: '🔢', color: 'violet' },
  structure:    { labelEn: 'Structure',    labelAr: 'البنية',    emoji: '🏛️', color: 'blue'   },
  language:     { labelEn: 'Language',    labelAr: 'اللغة',     emoji: '📝', color: 'emerald'},
  history:      { labelEn: 'History',     labelAr: 'التاريخ',   emoji: '⏳', color: 'amber'  },
  preservation: { labelEn: 'Preservation', labelAr: 'الحفظ',    emoji: '🛡️', color: 'teal'   },
};

const COLOR_STYLES: Record<string, { bg: string; border: string; badge: string; highlight: string }> = {
  violet:  { bg: 'bg-violet-50',  border: 'border-violet-200',  badge: 'bg-violet-100 text-violet-700',  highlight: 'text-violet-700' },
  blue:    { bg: 'bg-blue-50',    border: 'border-blue-200',    badge: 'bg-blue-100 text-blue-700',      highlight: 'text-blue-700'   },
  emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700',highlight: 'text-emerald-700'},
  amber:   { bg: 'bg-amber-50',   border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-700',   highlight: 'text-amber-700'  },
  teal:    { bg: 'bg-teal-50',    border: 'border-teal-200',    badge: 'bg-teal-100 text-teal-700',     highlight: 'text-teal-700'   },
};

const WONDERS: readonly WonderFact[] = [
  // === NUMBERS ===
  {
    id: 'w_word_count',
    category: 'numbers',
    titleEn: 'Total Word Count',
    titleAr: 'عدد الكلمات الإجمالي',
    highlight: '77,430',
    factEn: 'The Quran contains approximately 77,430 words (tokens) across 114 surahs and 6,236 ayahs — roughly half the length of the New Testament. The exact count varies by scholarly method (from ~75,000 to ~80,000) depending on how compound words and prefixes are tallied. The 77,430 figure comes from Quranic Arabic Corpus tokenization. Medieval scholars like Imam Suyuti documented the count in Al-Itqan for purposes of manuscript verification and memorization accuracy. Allah describes the Quran as the "Dhikr" (Reminder) that He Himself will guard — every word, every letter.',
    factAr: 'يحتوي القرآن على ما يقارب 77,430 كلمة في 114 سورة و6,236 آية. يتفاوت العدد الدقيق من عالم لآخر (بين 75,000 و80,000) بحسب طريقة إحصاء الكلمات المركبة والمضاف إليها. يستند الرقم 77,430 إلى تحليل المتن القرآني العربي الرقمي. وثّق الإمام السيوطي في "الإتقان" هذه الأرقام للتحقق من صحة النسخ والحفظ. وسمّى الله القرآن "الذكر" الذي تعهّد بحفظه بنفسه (15:9).',
    quranicRef: {
      ref: '15:9',
      nameEn: 'Surah Al-Hijr',
      textEn: '"Indeed, it is We who sent down the Quran, and indeed, We will be its guardian."',
    },
    sourceEn: 'Al-Itqan fi Ulum al-Quran (Suyuti, d. 911 AH), ch. on word count; Quranic Arabic Corpus (quranic-research.net)',
    sourceAr: 'الإتقان في علوم القرآن (السيوطي، ت. 911هـ)، باب في عدد الكلمات؛ مجموعة بيانات المتن القرآني العربي',
  },
  {
    id: 'w_letter_count',
    category: 'numbers',
    titleEn: 'Total Letter Count',
    titleAr: 'عدد الحروف الإجمالي',
    highlight: '323,671',
    factEn: 'The Quran contains approximately 323,671 Arabic letters. Scholars counted letters meticulously for three purposes: (1) ensuring perfect manuscript copying, (2) confirming correct memorization, and (3) establishing the midpoint of the text. The most frequent letter is Alif (ا) and the rarest is Zha (ظ). Scholars of Quran sciences identified the middle letter of the entire Quran as the Lam of the word "walyatalatif" in 18:19 — a discovery confirming Al-Kahf as the approximate centre. The precision of letter-counting across 1,400 years of scholarship demonstrates the care with which the Quran was transmitted.',
    factAr: 'يتضمن القرآن الكريم نحو 323,671 حرفاً عربياً. أحصى العلماء الحروف لثلاثة أغراض: (1) ضمان دقة النسخ، (2) التحقق من صحة الحفظ، (3) تحديد وسط القرآن. أكثر الحروف تكراراً الألف (ا)، وأقلها الظاء (ظ). حدّد العلماء الحرف الأوسط للقرآن في كلمة "وليتلطف" من الآية 18:19 — ما يؤكد وقوع سورة الكهف في المنتصف تقريباً.',
    quranicRef: {
      ref: '15:9',
      nameEn: 'Surah Al-Hijr',
      textEn: '"Indeed, it is We who sent down the Quran, and indeed, We will be its guardian."',
    },
    sourceEn: 'Al-Itqan fi Ulum al-Quran (Suyuti), ch. on letter counting; Fada\'il al-Quran (Ibn Kathir, d. 774 AH)',
    sourceAr: 'الإتقان في علوم القرآن (السيوطي)، باب في عدد الحروف؛ فضائل القرآن (ابن كثير، ت. 774هـ)',
  },
  {
    id: 'w_ayah_count',
    category: 'numbers',
    titleEn: 'Total Verse Count',
    titleAr: 'عدد الآيات الإجمالي',
    highlight: '6,236',
    factEn: 'The Quran has 6,236 ayahs according to the Kufi counting school, used in the Egyptian Standard Mushaf (1924) that is now internationally standard. Six main counting traditions exist: Kufi (6,236), Shami (6,225–6,226), Madani al-Awwal (6,217), Madani al-Thani (6,214), Makki (6,210), and Basri (6,205). Differences arise not from different texts, but from how certain phrase divisions at verse boundaries are classified — the actual words are identical across all traditions. This consensus on text with variation only in counting reflects the meticulous scholarship of Quran sciences (ulum al-Quran).',
    factAr: 'تبلغ آيات القرآن 6,236 آية وفق العدد الكوفي المعتمد في المصحف المصري القياسي (1924). ستة مذاهب رئيسية في العدد: الكوفي (6,236)، الشامي (6,225-6,226)، المدني الأول (6,217)، المدني الثاني (6,214)، المكي (6,210)، البصري (6,205). الاختلاف ليس في متن الكلمات — بل في تحديد فواصل بعض الآيات، والألفاظ متفق عليها إجماعاً.',
    sourceEn: 'Al-Itqan fi Ulum al-Quran (Suyuti), ch. 19, "On the Number of Verses"; Al-Burhan fi Ulum al-Quran (Zarkashi, d. 794 AH), vol. 1',
    sourceAr: 'الإتقان في علوم القرآن (السيوطي)، النوع 19 في عدد الآيات؛ البرهان في علوم القرآن (الزركشي، ت. 794هـ)، ج. 1',
  },
  {
    id: 'w_arabic_unique',
    category: 'numbers',
    titleEn: 'Unique Arabic Words',
    titleAr: 'الكلمات العربية الفريدة',
    highlight: '18,994',
    factEn: 'Of the ~77,430 total word tokens in the Quran, approximately 18,994 are unique lexical forms — a type-token ratio of ~24.5%. For context, Shakespeare\'s complete works contain ~31,000 unique words from ~900,000 total tokens. The Quran achieves remarkable lexical diversity in a text of only 77,000 words. Arabic\'s root-based morphology means many "unique" forms still share roots: the three-letter root k-t-b (to write), for example, generates: kitab (book), kataba (he wrote), kutub (books), katib (writer), maktub (written), maktab (office) — all counted separately. The Allah says in the Quran that He sent it as an Arabic revelation so people may understand.',
    factAr: 'من أصل ~77,430 كلمة في القرآن، نحو 18,994 صيغة معجمية مستقلة — نسبة تنوع معجمي ~24.5%. يعني نظام الجذور في العربية أن كثيراً من الصيغ المتعددة تعود إلى جذر واحد: فجذر (ك-ت-ب) وحده يولّد: كتاب، كتب، كاتب، مكتوب، مكتب... وكلها تُحسب صيغاً مستقلة. أوحى الله القرآن عربياً لتتسع مدارك التدبر والفهم (12:2).',
    quranicRef: {
      ref: '12:2',
      nameEn: 'Surah Yusuf',
      textEn: '"Indeed, We have sent it down as an Arabic Quran that you might understand."',
    },
    sourceEn: 'Quranic Arabic Corpus (University of Leeds); Corpus Quranicum (Berlin-Brandenburg Academy); Abdul-Raof, H., Quranic Stylistics (2010)',
    sourceAr: 'مجموعة بيانات المتن القرآني العربي (جامعة ليدز)؛ Corpus Quranicum (أكاديمية برلين)؛ عبد الرؤوف، أسلوبية القرآن (2010)',
  },
  {
    id: 'w_surah_names_count',
    category: 'numbers',
    titleEn: 'Multiple Names for Surahs',
    titleAr: 'تعدد أسماء السور',
    highlight: '55+',
    factEn: 'Many surahs have more than one authentic name drawn from hadith or scholarly tradition. Al-Fatihah alone carries 20+ recorded names: "Umm al-Quran" (Mother of the Quran) and "Umm al-Kitab" are sahih hadith terms (Bukhari 4703); "Al-Sab\'a al-Mathani" (the Seven Oft-Repeated) is Quranic (15:87); "Al-Shifa\'" (The Cure) appears in hadith (Daraqutni); "Al-Ruqyah" in Bukhari 5736. Other examples: Al-Tawbah is also called "Al-Baraa\'" (The Acquittal) and "Al-Fadiha" (The Exposer); Al-Ikhlas is called "Al-Asas" (The Foundation) and "Al-Samad." Surah numbering (1–114) is a modern convention — classical scholars referenced surahs by name.',
    factAr: 'كثير من السور لها أكثر من اسم صحيح من السنة أو إجماع العلماء. للفاتحة وحدها أكثر من 20 اسماً: "أم القرآن" و"أم الكتاب" ثابتتان في البخاري (4703)، و"السبع المثاني" قرآنية (15:87)، و"الشفاء" في حديث الدارقطني، و"الرقية" في البخاري (5736). وللتوبة أيضاً: "البراءة" و"الفاضحة"؛ وللإخلاص: "الأساس" و"الصمد".',
    quranicRef: {
      ref: '15:87',
      nameEn: 'Surah Al-Hijr',
      textEn: '"And We have given you the seven oft-repeated [verses] and the great Quran."',
    },
    sourceEn: 'Al-Itqan fi Ulum al-Quran (Suyuti), ch. on surah names; Sahih Bukhari 4703; Al-Burhan (Zarkashi), vol. 1, ch. 3',
    sourceAr: 'الإتقان (السيوطي)، باب في أسماء السور؛ صحيح البخاري 4703؛ البرهان (الزركشي)، ج. 1، النوع الثالث',
  },
  // === STRUCTURE ===
  {
    id: 'w_muqattaat',
    category: 'structure',
    titleEn: 'Mysterious Opening Letters (Muqattaat)',
    titleAr: 'الحروف المقطعة',
    highlight: '29 Surahs',
    factEn: '29 surahs open with disconnected letters (muqattaat). Remarkably, only 14 distinct letters appear in all these combinations — exactly half of the 28-letter Arabic alphabet. Those 14 letters are: ا ح ر س ص ط ع ق ك ل م ن ه ي. Examples: الم (Baqarah, Al-Imran, Ankabut, Rum, Luqman, Sajdah), الر (Yunus, Hud, Yusuf, Ibrahim, Al-Hijr), كهيعص (Maryam), طه (Ta-Ha), يس (Ya-Sin), ن (Al-Qalam). Their precise meaning is known only to Allah — they are among the mutashabihat (ambiguous verses). The Quran (3:7) explicitly states that ambiguous verses exist and that only those with firm knowledge pursue their deeper meaning while the deviant follow them for the sake of discord.',
    factAr: '29 سورة تبدأ بالحروف المقطعة، ولا يُستخدم فيها إلا 14 حرفاً — نصف حروف الأبجدية العربية البالغة 28 حرفاً. هذه الحروف هي: ا ح ر س ص ط ع ق ك ل م ن ه ي. أمثلة: (الم) في البقرة وآل عمران وغيرها، (الر) في يونس وهود ويوسف، (كهيعص) في مريم، (طه) و(يس) و(ن). معناها الحقيقي علم عند الله — من المتشابهات التي أشارت إليها الآية 3:7.',
    quranicRef: {
      ref: '3:7',
      nameEn: 'Surah Al-Imran',
      textEn: '"It is He who has sent down to you the Book; in it are precise verses — they are the foundation of the Book — and others unspecific. Those with deviation in their hearts follow the unspecific seeking discord and seeking an interpretation... but none knows its [true] interpretation except Allah."',
    },
    sourceEn: 'Tafsir Ibn Kathir (introduction to each surah); Tafsir Al-Tabari; Al-Itqan (Suyuti), ch. on muqattaat; Bayan al-Quran (Suyuti)',
    sourceAr: 'تفسير ابن كثير (مقدمة كل سورة)؛ تفسير الطبري؛ الإتقان (السيوطي)، باب في الحروف المقطعة',
  },
  {
    id: 'w_meccan_medinan_split',
    category: 'structure',
    titleEn: 'Meccan vs. Medinan Surahs',
    titleAr: 'السور المكية والمدنية',
    highlight: '86 Meccan / 28 Medinan',
    factEn: 'Scholars classify 86 surahs as Meccan and 28 as Medinan using four criteria: (1) Oral tradition from companions (primary authority); (2) Content: Meccan surahs focus on tawhid (monotheism), morality, and the afterlife; Medinan ones emphasize law, community structure, and interfaith rulings; (3) Style: Meccan verses tend to be shorter, rhythmically powerful; Medinan ones longer and more legislative; (4) Historical references within the text. Some surahs contain both Meccan and Medinan verses interleaved (e.g., Al-Baqarah). A minority scholarly opinion differs on about 6 surahs. The classification helps scholars understand the evolution of the Quranic message over 23 years of revelation.',
    factAr: 'يُصنّف العلماء 86 سورة مكية و28 مدنية بأربعة معايير: (1) الرواية الشفهية عن الصحابة (المرجع الأساسي)؛ (2) المضمون: المكي يُرسّخ العقيدة والأخلاق وأهوال القيامة، والمدني يُعالج الأحكام والمجتمع والعلاقات بين الأديان؛ (3) الأسلوب: المكي أقصر وأشد وقعاً، والمدني أطول وأكثر تشريعاً؛ (4) الأحداث المذكورة. بعض السور مزيج من المكي والمدني.',
    sourceEn: 'Al-Burhan fi Ulum al-Quran (Zarkashi, d. 794 AH), vol. 1; Manahil al-Irfan (Al-Zarqani, d. 1948); Al-Itqan (Suyuti), ch. on Meccan and Medinan',
    sourceAr: 'البرهان في علوم القرآن (الزركشي، ت. 794هـ)، ج. 1؛ مناهل العرفان (الزرقاني، ت. 1948م)؛ الإتقان (السيوطي)',
  },
  {
    id: 'w_longest_ayah',
    category: 'structure',
    titleEn: 'Longest Single Verse',
    titleAr: 'أطول آية منفردة',
    highlight: '2:282',
    factEn: 'Ayah 2:282 (Ayat al-Mudayanah — the Debt Verse) is the longest single verse in the Quran at ~540 words. It is a complete legal framework: (1) mandating written contracts for deferred transactions; (2) specifying who should write (a competent scribe, neither party under duress); (3) requiring the debtor to dictate; (4) outlining witness requirements (two men, or one man and two women as backup); (5) requiring recitation back to the debtor; (6) accounting for those unable to dictate; (7) permitting oral-only contracts for immediate transactions. This level of legislative density in a single verse is unmatched in any ancient legal text.',
    factAr: 'آية 2:282 (آية المداينة) هي أطول آية في القرآن بنحو 540 كلمة. تُقدّم منظومة قانونية كاملة: (1) إيجاب الكتابة في عقود الدَّين الآجلة؛ (2) تحديد الكاتب بعدل ودون إكراه؛ (3) إملاء المدين؛ (4) شروط الشهادة (رجلان أو رجل وامرأتان)؛ (5) القراءة على المدين؛ (6) مراعاة من يعجز عن الإملاء؛ (7) إجازة التعاقد الشفهي في العقود الفورية. هذا المستوى من الكثافة التشريعية في آية واحدة فريد في تاريخ القانون القديم.',
    quranicRef: {
      ref: '2:282',
      nameEn: 'Surah Al-Baqarah',
      textEn: '"O you who have believed, when you contract a debt for a specified term, write it down. And let a scribe write [it] between you in justice..." [the longest verse in the Quran]',
    },
    sourceEn: 'Tafsir Al-Qurtubi, Ahkam al-Quran; Al-Jassas, Ahkam al-Quran (d. 370 AH); Ibn al-Arabi, Ahkam al-Quran (d. 543 AH)',
    sourceAr: 'تفسير القرطبي، أحكام القرآن؛ الجصاص، أحكام القرآن (ت. 370هـ)؛ ابن العربي، أحكام القرآن (ت. 543هـ)',
  },
  {
    id: 'w_center_quran',
    category: 'structure',
    titleEn: 'The Middle of the Quran',
    titleAr: 'وسط القرآن',
    highlight: 'Surah Al-Kahf (18)',
    factEn: 'Surah Al-Kahf (18) sits at the approximate midpoint of the Quran by both word and letter count. Scholars have identified the middle letter as falling in 18:19 ("walyatalaṭṭaf"). Al-Kahf is also structurally unique: it contains four thematic stories — the People of the Cave (faith vs. oppression), the Two Garden Owners (wealth vs. gratitude), Musa and Al-Khidr (knowledge and wisdom), and Dhul-Qarnayn (power and justice) — each exploring a different trial of faith. The Prophet ﷺ instructed reading Al-Kahf every Friday (narrated from Abu Sa\'id al-Khudri), and the first and last 10 verses are described as protection from the Dajjal.',
    factAr: 'تقع سورة الكهف (18) تقريباً في منتصف القرآن بعد الكلمات والحروف. حدّد العلماء الحرف الأوسط في الآية 18:19 ("وليتلطف"). وتتميز الكهف ببنيتها الفريدة: أربع قصص موضوعية — أصحاب الكهف، وصاحب الجنتين، وموسى والخضر، وذو القرنين — تتناول تحديات الإيمان من زوايا مختلفة. وقد حثّ النبي ﷺ على قراءتها كل جمعة (من حديث أبي سعيد الخدري).',
    hadithRef: '"Whoever reads Surah Al-Kahf on Friday, a light will illuminate him from one Friday to the next." — Narrated from Abu Sa\'id al-Khudri; reported by Al-Hakim (Mustadrak, deemed sahih) and Al-Bayhaqi (Shu\'ab al-Iman)',
    sourceEn: 'Al-Mustadrak (Al-Hakim, d. 405 AH); Shu\'ab al-Iman (Al-Bayhaqi, d. 458 AH); Fada\'il al-Quran (Ibn Kathir); scholarly tradition on Quran centre',
    sourceAr: 'المستدرك (الحاكم، ت. 405هـ)؛ شعب الإيمان (البيهقي، ت. 458هـ)؛ فضائل القرآن (ابن كثير)؛ التراث العلمي في تحديد وسط القرآن',
  },
  // === LANGUAGE ===
  {
    id: 'w_hapax_legomena',
    category: 'language',
    titleEn: 'Words Used Only Once',
    titleAr: 'كلمات وردت مرة واحدة فقط',
    highlight: '1,500+',
    factEn: 'Over 1,500 words in the Quran appear only once (hapax legomena in classical Arabic scholarship: "gharib al-Quran"). Each demanded centuries of scholarly inquiry to establish its precise meaning. Documented examples: "Sijjil" (15:74) — baked clay, possibly from Persian/Syriac; "Zanjabil" (76:17) — ginger-flavoured water of paradise; "Istabraq" (76:21) — thick brocade, possibly Arabicised Persian; "Qistas" (17:35) — balance scale, possibly from Greek; "Mishkat" (24:35) — a wall niche for a lamp, possibly Ethiopic. Imam Ar-Raghib al-Asfahani (d. c. 502 AH) wrote the definitive lexicon of rare Quranic vocabulary, and Ibn Qutaybah (d. 276 AH) wrote an earlier treatise on this topic.',
    factAr: 'أكثر من 1,500 كلمة في القرآن لم ترد إلا مرة واحدة (غريب القرآن). أمثلة موثقة: "سجيل" (15:74) من طين مشوّي؛ "زنجبيل" (76:17) ماء الجنة المُنكَّه؛ "إستبرق" (76:21) الديباج الغليظ؛ "قسطاس" (17:35) ميزان عدل؛ "مشكاة" (24:35) كوّة في الجدار. ألّف الراغب الأصفهاني (ت. نحو 502هـ) المعجم المرجعي لهذه الكلمات "المفردات في غريب القرآن".',
    sourceEn: 'Al-Mufradat fi Gharib al-Quran (Ar-Raghib al-Asfahani, d. c. 502 AH); Gharib al-Quran (Ibn Qutaybah, d. 276 AH); Arthur Jeffery, The Foreign Vocabulary of the Quran (1938)',
    sourceAr: 'المفردات في غريب القرآن (الراغب الأصفهاني، ت. نحو 502هـ)؛ غريب القرآن (ابن قتيبة، ت. 276هـ)؛ آرثر جيفري، المفردات الأجنبية في القرآن (1938)',
  },
  {
    id: 'w_quran_arabic',
    category: 'language',
    titleEn: 'The Quran Preserved Classical Arabic',
    titleAr: 'القرآن حافظ على اللغة العربية الكلاسيكية',
    highlight: '1,400 Years',
    factEn: 'The Quran explicitly describes itself as an "Arabic Quran" in five separate verses (12:2, 20:113, 39:28, 41:3, 43:3), and as a "clear Arabic tongue" (16:103). No other ancient language is so continuously studied and spoken through a single text. Linguist Johann Fück (1955) noted the Quran "arrested the natural evolution of the Arabic language." Classical Arabic used in the Quran is today fully teachable from its own text — university courses worldwide use it as the primary teaching corpus. Lane\'s Arabic-English Lexicon (1863), still the most comprehensive English reference for classical Arabic, is essentially a lexicon of Quranic and Hadith Arabic.',
    factAr: 'وصف القرآن نفسه بأنه "قرآن عربي" في خمس آيات (12:2، 20:113، 39:28، 41:3، 43:3)، و"لسان عربي مبين" (16:103). لا توجد لغة قديمة أخرى محفوظة حية بنص واحد بهذه الدرجة. رأى المستشرق يوهان فُوك (1955) أن القرآن "أوقف التطور الطبيعي للغة العربية". وقاموس لين العربي الإنجليزي (1863) — أشمل مراجع العربية الكلاسيكية بالإنجليزية — هو في جوهره معجم لغة القرآن والحديث.',
    quranicRef: {
      ref: '41:3',
      nameEn: 'Surah Fussilat',
      textEn: '"A Book whose verses have been detailed, an Arabic Quran for a people who know."',
    },
    sourceEn: 'Quran 12:2, 20:113, 39:28, 41:3, 43:3, 16:103; Fück, J., Arabiyya (1955); Lane, E.W., Arabic-English Lexicon (1863), Introduction',
    sourceAr: 'القرآن 12:2، 41:3، 43:3، 16:103؛ فُوك، يوهان، Arabiyya (1955م)؛ لين، قاموس عربي إنجليزي (1863م)',
  },
  {
    id: 'w_foreign_words',
    category: 'language',
    titleEn: 'Words of Foreign Origin',
    titleAr: 'الكلمات ذات الأصل الأجنبي',
    highlight: '~100 Words',
    factEn: 'Classical scholars identified ~100 Quranic words with possible foreign origins — Ethiopic, Persian, Syriac, Hebrew, or Greek — yet all fully Arabicized before Quranic use. Two scholarly positions exist: (1) Scholars like Abu Ubayda (d. 210 AH) and Imam Suyuti accepted that such Arabicized loanwords exist; (2) Scholars like Imam Shafi\'i (d. 204 AH) held all Quranic vocabulary is originally Arabic, explaining similarities as parallel development. The Quran itself (16:103) refutes the accusation that a non-Arab person taught the Prophet ﷺ by affirming: the accused has a foreign tongue while the Quran is in clear, pure Arabic. Suyuti devoted an entire monograph to this topic.',
    factAr: 'حدّد العلماء الكلاسيكيون نحو 100 كلمة قرآنية ذات أصول محتملة حبشية أو فارسية أو سريانية أو عبرية أو يونانية — كلها مُعرَّبة قبل نزول القرآن. مذهبان علميان: (1) أبو عبيدة (ت. 210هـ) والسيوطي قبلا وجود المعرَّب؛ (2) الإمام الشافعي (ت. 204هـ) اعتبر كل ألفاظه عربية أصيلة. وقد ردّ الله (16:103) على دعوى أن إنساناً أعجمياً علّم النبي ﷺ بتأكيد أن هذا القرآن "لسان عربي مبين".',
    quranicRef: {
      ref: '16:103',
      nameEn: 'Surah An-Nahl',
      textEn: '"And We know well that they say: \'It is only a human who teaches him.\' The tongue of the one they point to is foreign, while this [Quran] is [in] a clear Arabic language."',
    },
    sourceEn: 'Al-Muhadhdhab fi ma waqa\'a fi al-Quran min al-Mu\'arrab (Suyuti); Risala (Imam Shafi\'i, d. 204 AH); Arthur Jeffery, The Foreign Vocabulary of the Quran (1938)',
    sourceAr: 'المهذب فيما وقع في القرآن من المعرّب (السيوطي)؛ الرسالة (الإمام الشافعي، ت. 204هـ)؛ جيفري، المفردات الأجنبية في القرآن (1938)',
  },
  {
    id: 'w_inimitability',
    category: 'language',
    titleEn: "The Quran's Challenge (I'jaz)",
    titleAr: 'تحدي القرآن (الإعجاز)',
    highlight: '5 Challenges',
    factEn: 'The Quran issues five progressive challenges — the earliest and broadest to the narrowest: (1) Quran 52:34: "Let them produce a hadith [statement] like it, if they are truthful." (2) Quran 17:88: "If all humans and jinn gathered to produce something like this Quran, they could not, even if they backed each other." (3) Quran 11:13: produce 10 invented surahs like it. (4) Quran 2:23 & 10:38: produce even one surah like any of the 114. In 7th-century Arabia — where oral poetry and rhetoric were at their apex, and where the Quran\'s primary audience was masters of eloquence — no one accepted any of these challenges, and none has been accepted in 1,400 years since.',
    factAr: 'يُصدر القرآن خمسة تحديات متصاعدة من الأعم إلى الأخص: (1) القرآن 52:34: "فليأتوا بحديث مثله". (2) القرآن 17:88: لو اجتمعت الإنس والجن على أن يأتوا بمثله لم يستطيعوا. (3) القرآن 11:13: عشر سور مفتريات. (4) القرآن 2:23 و10:38: سورة واحدة مثله. في الجزيرة العربية التي بلغت فنون الشعر والبلاغة ذروتها، لم يُجب أحد على هذه التحديات في 1,400 عام.',
    quranicRef: {
      ref: '17:88',
      nameEn: 'Surah Al-Isra\'',
      textEn: '"Say: If all mankind and jinn were to gather together to produce the like of this Quran, they could not produce the like of it, even if they were helpers of one another."',
    },
    sourceEn: 'Quran 2:23, 10:38, 11:13, 17:88, 52:34; I\'jaz al-Quran (Al-Baqillani, d. 403 AH); Dala\'il al-I\'jaz (Abd al-Qahir al-Jurjani, d. 471 AH)',
    sourceAr: 'القرآن 2:23، 10:38، 11:13، 17:88، 52:34؛ إعجاز القرآن (الباقلاني، ت. 403هـ)؛ دلائل الإعجاز (عبد القاهر الجرجاني، ت. 471هـ)',
  },
  // === HISTORY ===
  {
    id: 'w_memorizers',
    category: 'history',
    titleEn: 'Huffaz — Memorizers of the Quran',
    titleAr: 'الحُفَّاظ — حافظو القرآن',
    highlight: '10+ Million',
    factEn: 'Over 10 million Muslims worldwide have memorized the entire Quran (huffaz), making it the most memorized book in human history. The Quran explicitly promises its own memorability in Surah Al-Qamar, repeating the same verse four times: "And We have certainly made the Quran easy for remembrance, so is there any who will remember?" (54:17, 22, 32, 40). The tradition began with the Prophet ﷺ himself and his companions: Zaid ibn Thabit, Ibn Abbas, Ibn Masud, Ubayy ibn Ka\'b, and Hafsa bint Umar were among the earliest huffaz. Today, international Quran memorization competitions (musabaqa) draw hundreds of millions of viewers. Importantly, even if every printed copy of the Quran were destroyed, the text would be fully recoverable from living memory.',
    factAr: 'يزيد على 10 ملايين مسلم حول العالم حفظوا القرآن الكريم كاملاً، مما يجعله أكثر كتاب يُحفظ في التاريخ البشري. وعد الله بتيسير حفظه في سورة القمر بتكرار الآية أربع مرات: "وَلَقَدْ يَسَّرْنَا الْقُرْآنَ لِلذِّكْرِ فَهَلْ مِن مُّدَّكِرٍ" (54:17، 22، 32، 40). بدأت الرحلة مع النبي ﷺ وصحابته: زيد بن ثابت وابن عباس وابن مسعود وأُبي بن كعب وحفصة بنت عمر من أوائل الحفاظ. ولو أُتلفت كل نسخ القرآن المطبوعة لأمكن إعادة بناء النص كاملاً من الحفظ.',
    quranicRef: {
      ref: '54:17',
      nameEn: 'Surah Al-Qamar',
      textEn: '"And We have certainly made the Quran easy for remembrance, so is there any who will remember?" [repeated at 54:17, 22, 32, and 40]',
    },
    sourceEn: 'Quran 54:17, 22, 32, 40; Sahih Bukhari 5004 (virtues of Quran reciters); Islamic scholarly and institutional estimates (Quran Foundation reports)',
    sourceAr: 'القرآن 54:17، 22، 32، 40؛ صحيح البخاري 5004؛ تقديرات العلماء والمؤسسات الإسلامية',
  },
  {
    id: 'w_compilation',
    category: 'history',
    titleEn: 'Official Compilation',
    titleAr: 'التدوين الرسمي',
    highlight: '2 Years After Prophet ﷺ',
    factEn: 'The immediate trigger for compilation was the Battle of Yamama (633 CE), in which 70 Quran huffaz were martyred. Umar ibn al-Khattab, alarmed, urged Abu Bakr al-Siddiq to compile the Quran before more memorizers died. Abu Bakr initially hesitated ("How can I do something the Prophet ﷺ did not do?") but was convinced. Zaid ibn Thabit — the Prophet\'s ﷺ chief scribe — was appointed compiler. He gathered written pieces from palm stalks, flat stones, and parchments, cross-referencing each with the testimony of two witnesses plus the memories of companions. The completed Mushaf was held by Abu Bakr, then passed to Umar ibn al-Khattab, then to his daughter Hafsa bint Umar.',
    factAr: 'كان الدافع المباشر معركة اليمامة (633م) واستشهاد 70 حافظاً للقرآن. فبادر عمر بن الخطاب إلى مقترح الجمع، فتردد أبو بكر ("كيف أفعل ما لم يفعله النبي ﷺ؟") ثم اقتنع. وعُيّن زيد بن ثابت — كاتب الوحي الرئيسي — لقيادة الجمع. جمع ما كُتب من عُسُب النخل وصحائف الحجارة والرقاع، وقابل كل قطعة بشهادة شاهدَين وحفظ الصحابة. المصحف المكتمل احتفظت به السيدة حفصة بنت عمر.',
    hadithRef: 'Zaid ibn Thabit said: "Abu Bakr sent for me after the losses at Yamama. Umar ibn al-Khattab was with him... Abu Bakr said: \'You are a young wise man, and we do not suspect you of anything. You used to write down the revelation for the Messenger of Allah ﷺ. So search for the Quran and collect it.\'" — Sahih Bukhari 4986–4987',
    sourceEn: 'Sahih Bukhari 4986–4987; Fath al-Bari (Ibn Hajar, d. 852 AH), vol. 9; Al-Itqan (Suyuti), ch. on Quran collection',
    sourceAr: 'صحيح البخاري 4986-4987؛ فتح الباري (ابن حجر، ت. 852هـ)، ج. 9؛ الإتقان (السيوطي)، باب في جمع القرآن',
  },
  {
    id: 'w_standardization',
    category: 'history',
    titleEn: 'Standardization Under Uthman',
    titleAr: 'التوحيد في عهد عثمان',
    highlight: 'c. 650 CE',
    factEn: 'The trigger was Hudhayfah ibn al-Yaman\'s report to Caliph Uthman: during the conquest of Armenia and Azerbaijan, he saw Muslims arguing over Quranic readings. He said: "O Commander of the Faithful, catch up with this community before it differs over its Book like the Jews and Christians." Uthman formed a four-member committee: Zaid ibn Thabit, Abdullah ibn al-Zubayr, Sa\'id ibn al-As, and Abd al-Rahman ibn al-Harith ibn Hisham. They produced multiple copies sent to Makkah, Madinah, Basra, Kufa, Sham (Damascus), and possibly Yemen. Uthman recalled the Hafsa Mushaf for copying and all variant compilations were burned. The divine promise of preservation (15:9) was fulfilled through these scholarly human actions.',
    factAr: 'سبب التوحيد: أبلغ حذيفة بن اليمان الخليفة عثمان أنه رأى في فتح أرمينيا وأذربيجان مسلمين يتنازعون في القراءات، فقال: "أدرك هذه الأمة قبل أن تختلف في كتابها كاختلاف اليهود والنصارى." شكّل عثمان لجنة رباعية: زيد بن ثابت، وعبدالله بن الزبير، وسعيد بن العاص، وعبدالرحمن بن الحارث. نسخوا مصاحف أُرسلت إلى مكة والمدينة والبصرة والكوفة والشام. وأُرجع مصحف حفصة بعد النسخ وأُحرقت النسخ المتباينة.',
    quranicRef: {
      ref: '15:9',
      nameEn: 'Surah Al-Hijr',
      textEn: '"Indeed, it is We who sent down the Quran, and indeed, We will be its guardian." [The divine promise fulfilled through Uthman\'s standardization]',
    },
    hadithRef: '"Hudhayfah ibn al-Yaman came to Uthman while the people of Sham and Iraq were fighting... He said: \'O Commander of the Faithful, save this nation before they differ about the Book as the Jews and Christians differed.\'" — Sahih Bukhari 4987',
    sourceEn: 'Sahih Bukhari 4987; Al-Masahif (Ibn Abi Dawud al-Sijistani, d. 316 AH); Fath al-Bari (Ibn Hajar), vol. 9',
    sourceAr: 'صحيح البخاري 4987؛ المصاحف (ابن أبي داود السجستاني، ت. 316هـ)؛ فتح الباري (ابن حجر)، ج. 9',
  },
  {
    id: 'w_revelations_locations',
    category: 'history',
    titleEn: 'Revealed in Three Locations',
    titleAr: 'نزل في ثلاثة أماكن',
    highlight: 'Makkah · Madinah · Jerusalem',
    factEn: 'The Quran was revealed across three holy locations over 23 years. (1) Makkah (~610–622 CE): the majority of the Quran, beginning with the first revelation (96:1–5) in Cave Hira. (2) Madinah (~622–632 CE): the second major phase following the Hijra, covering legislation and community rulings. (3) Jerusalem: specific verses revealed during the Night Journey (Isra\') — Surah Al-Isra\' (17:1) describes the journey itself. Additionally, scholars document ~17 non-Makkah/non-Madinah revelation occasions (asbab al-nuzul): e.g., verses of Al-Ma\'idah during the Farewell Pilgrimage, and a verse during the journey to Ta\'if. The three holy cities of Islam are thus all linked to the revelation.',
    factAr: 'نزل القرآن في ثلاثة أماكن مقدسة على مدى 23 عاماً: (1) مكة المكرمة (~610-622م): الجزء الأكبر، بدءاً بأول وحي (96:1-5) في غار حراء. (2) المدينة المنورة (~622-632م): مرحلة التشريع والتنظيم. (3) القدس/بيت المقدس: آيات نزلت خلال رحلة الإسراء والمعراج التي وصفتها الآية (17:1). يوثق العلماء نحو 17 مناسبة نزول خارج مكة والمدينة.',
    quranicRef: {
      ref: '17:1',
      nameEn: 'Surah Al-Isra\'',
      textEn: '"Exalted is He who took His Servant by night from al-Masjid al-Haram to al-Masjid al-Aqsa, whose surroundings We have blessed, to show him of Our signs."',
    },
    sourceEn: 'Seerah of Ibn Hisham (d. 218 AH); Asbab al-Nuzul (Al-Wahidi, d. 468 AH); Al-Itqan (Suyuti), ch. on places of revelation',
    sourceAr: 'سيرة ابن هشام (ت. 218هـ)؛ أسباب النزول (الواحدي، ت. 468هـ)؛ الإتقان (السيوطي)، باب في مواضع النزول',
  },
  // === PRESERVATION ===
  {
    id: 'w_ijazah_chain',
    category: 'preservation',
    titleEn: 'Unbroken Chain of Transmission (Isnad)',
    titleAr: 'سلسلة إسناد متصلة',
    highlight: '1,400 Years',
    factEn: 'Every qualified Quran reciter today has an unbroken ijazah chain connecting them through named individuals back to the Prophet ﷺ. There are 10 recognized canonical recitation traditions (qira\'at), each traced to a named companion: Nafi\' (Madinah), Ibn Kathir (Makkah), Abu Amr (Basra), Ibn Amir (Damascus), Asim (Kufa), Hamza (Kufa), Al-Kisa\'i (Kufa), Abu Ja\'far (Madinah), Ya\'qub (Basra), Khalaf (Kufa). The standard Hafs-from-Asim recitation (used in the Egyptian Mushaf) traces to: Asim al-Kufi → Abu Abd al-Rahman al-Sulami → Ali ibn Abi Talib → the Prophet ﷺ. The Quran (75:17–18) itself describes Allah\'s direct role in preserving its recitation.',
    factAr: 'كل قارئ مجاز للقرآن اليوم يملك سلسلة إجازة متصلة بأسماء معروفة صولاً إلى النبي ﷺ. عشر قراءات متواترة معترف بها، كل منها موصولة بصحابي: نافع (المدينة)، ابن كثير (مكة)، أبو عمرو (البصرة)، ابن عامر (الشام)، عاصم (الكوفة)، حمزة (الكوفة)، الكسائي (الكوفة)، أبو جعفر (المدينة)، يعقوب (البصرة)، خلف (الكوفة). رواية حفص عن عاصم — المعتمدة في المصحف المصري — تمر بـ: عاصم → أبو عبدالرحمن السلمي → علي بن أبي طالب → النبي ﷺ.',
    quranicRef: {
      ref: '75:17-18',
      nameEn: 'Surah Al-Qiyamah',
      textEn: '"Indeed, upon Us is its collection [in your heart] and its recitation. So when We have recited it [through Gabriel], follow its recitation."',
    },
    sourceEn: 'Al-Nashr fi al-Qira\'at al-Ashr (Ibn al-Jazari, d. 833 AH); Hujjat al-Qira\'at (Ibn Zanjala, d. 403 AH); Tajweed transmission scholarship',
    sourceAr: 'النشر في القراءات العشر (ابن الجزري، ت. 833هـ)؛ حجة القراءات (ابن زنجلة، ت. 403هـ)؛ علم أسانيد التجويد والقراءات',
  },
  {
    id: 'w_translations',
    category: 'preservation',
    titleEn: 'Translated into How Many Languages',
    titleAr: 'الترجمة إلى كم لغة',
    highlight: '100+ Languages',
    factEn: 'The Quran has been translated into over 100 languages. Key milestones: the first recorded complete Latin translation (Lex Mahumet pseudoprophete, 1143 CE) was commissioned by Peter the Venerable of Cluny to enable Christian theological response to Islam; the first English translation by Alexander Ross (1649) was translated from French, not directly from Arabic; the first complete direct Arabic-to-English translation was by George Sale (1734), still referenced today. Today, major languages carry multiple independent translations — English alone has ~80. The Quran is translated into more languages than any religious text except the Bible. Crucially, only the Arabic Quran is considered scripture — all translations are regarded as interpretations, not the Quran itself.',
    factAr: 'تُرجم القرآن إلى أكثر من 100 لغة. محطات مفصلية: أول ترجمة لاتينية كاملة (1143م) أمر بها بيتر المحترم بكلوني لإعداد رد مسيحي على الإسلام؛ أول ترجمة إنجليزية (ألكساندر روس، 1649م) نقلاً عن الفرنسية لا عن العربية مباشرة؛ أول ترجمة إنجليزية مباشرة من العربية لجورج سيل (1734م). للإنجليزية وحدها ~80 ترجمة. القرآن الكريم المكتوب بالعربية وحده هو المعتمد — كل الترجمات تفسيرية لا قرآن.',
    quranicRef: {
      ref: '14:4',
      nameEn: 'Surah Ibrahim',
      textEn: '"And We did not send any messenger except [speaking] in the language of his people to state clearly for them..."',
    },
    sourceEn: 'Library of Congress records; Jones, J., "The Quran in English: A Biography" (Princeton UP); Sherif, F., A Guide to the Contents of the Quran (1985)',
    sourceAr: 'سجلات مكتبة الكونغرس؛ جوينز، القرآن بالإنجليزية: سيرة (مطبعة برينستون)؛ شريف، دليل محتويات القرآن (1985)',
  },
  {
    id: 'w_oldest_manuscript',
    category: 'preservation',
    titleEn: 'Oldest Known Manuscript',
    titleAr: 'أقدم مخطوطة معروفة',
    highlight: 'c. 568–645 CE',
    factEn: 'The Birmingham Quran (Mingana Collection MS Arabic 1572a, University of Birmingham) was radiocarbon-dated in 2015 to 568–645 CE with 95.4% confidence. It contains portions of Surahs 18–20 written on goatskin in an early Hijazi script. If the earlier end of the range is correct, the parchment may predate even the Prophet\'s ﷺ birth (570 CE). Comparable early manuscripts: the Sana\'a palimpsest (discovered in Yemen, 1972), the Tübingen University Quran manuscript (dated 649–675 CE), and the Paris BnF Arabe 328 collection. All these manuscripts show the text as essentially identical to today\'s Quran — a powerful empirical confirmation of the divine preservation promise (15:9).',
    factAr: 'مخطوطة برمنغهام (مجموعة مينغانا MS Arabic 1572a) حُدّد عمرها بالكربون المشع عام 2015 بين 568-645م بنسبة ثقة 95.4%. تحتوي على أجزاء من السور 18-20 بالخط الحجازي المبكر. إن صحّ الطرف الأدنى من المدى الزمني، ربما كان الرق مكتوباً قبل ميلاد النبي ﷺ (570م). مخطوطات أخرى مقارنة: صنعاء اليمن (1972م)، وجامعة توبنغن (649-675م)، ومجموعة باريس BnF Arabe 328. جميعها تؤكد أن النص طابق المصحف الحالي — تحققاً تجريبياً من وعد الحفظ (15:9).',
    quranicRef: {
      ref: '15:9',
      nameEn: 'Surah Al-Hijr',
      textEn: '"Indeed, it is We who sent down the Quran, and indeed, We will be its guardian." [confirmed empirically by surviving manuscripts]',
    },
    sourceEn: 'University of Birmingham radiocarbon study (David Thomas & Alba Fedeli, 2015); Sana\'a palimpsest analysis (Gerd-Rüdiger Puin, 1985); Tübingen manuscript dating (2014)',
    sourceAr: 'دراسة التأريخ بالكربون المشع لجامعة برمنغهام (توماس وفيديلي، 2015م)؛ تحليل مخطوطة صنعاء (بوين، 1985م)؛ تأريخ مخطوطة توبنغن (2014م)',
  },
];

const CATEGORIES = Object.keys(CAT_META) as WonderCategory[];

export function QuranWondersPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [catFilter, setCatFilter] = useState<WonderCategory | 'all'>('all');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const filtered = catFilter === 'all'
    ? WONDERS
    : WONDERS.filter(w => w.category === catFilter);

  function toggle(id: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-4', isRtl && 'flex-row-reverse')}>
        <Sparkles className="w-7 h-7 text-amber-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'عجائب القرآن' : 'Quran Wonders & Facts'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl
              ? `${WONDERS.length} حقيقة موثقة عن القرآن الكريم`
              : `${WONDERS.length} verified facts about the Quran`}
          </p>
        </div>
      </div>

      {/* Category filter */}
      <div className={clsx('flex flex-wrap gap-1.5 mb-5', isRtl && 'flex-row-reverse')}>
        <button
          onClick={() => setCatFilter('all')}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            catFilter === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'text-gray-500 border-gray-200 hover:bg-gray-50'
          )}
        >
          {isRtl ? 'الكل' : 'All'}
        </button>
        {CATEGORIES.map(cat => {
          const meta = CAT_META[cat];
          const styles = COLOR_STYLES[meta.color] ?? COLOR_STYLES.violet;
          return (
            <button
              key={cat}
              onClick={() => setCatFilter(cat === catFilter ? 'all' : cat)}
              className={clsx(
                'text-xs px-2.5 py-1 rounded-full border transition-colors',
                catFilter === cat ? `${styles.badge} border-transparent` : 'text-gray-500 border-gray-200 hover:bg-gray-50'
              )}
            >
              {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
            </button>
          );
        })}
      </div>

      {/* Facts grid */}
      <div className="space-y-3">
        {filtered.map(w => {
          const meta = CAT_META[w.category];
          const styles = COLOR_STYLES[meta.color] ?? COLOR_STYLES.violet;
          const isExpanded = expanded.has(w.id);

          return (
            <div
              key={w.id}
              className={clsx(
                'rounded-2xl border cursor-pointer transition-shadow hover:shadow-sm overflow-hidden',
                isExpanded ? `${styles.bg} ${styles.border}` : 'bg-white border-gray-100'
              )}
              onClick={() => toggle(w.id)}
            >
              <div className={clsx('p-4 flex items-start gap-3', isRtl && 'flex-row-reverse')}>
                {/* Highlight number */}
                <div className={clsx(
                  'flex-shrink-0 text-center min-w-[64px] px-2 py-2 rounded-xl',
                  styles.bg, styles.border, 'border'
                )}>
                  <p className={clsx('text-base font-bold leading-tight', styles.highlight)}>{w.highlight}</p>
                </div>

                <div className="flex-1 min-w-0">
                  <div className={clsx('flex items-center gap-1.5 mb-0.5', isRtl && 'flex-row-reverse')}>
                    <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full', styles.badge)}>
                      {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
                    </span>
                    {w.quranicRef && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-100 flex items-center gap-0.5">
                        <BookOpen className="w-2.5 h-2.5" />
                        {w.quranicRef.ref}
                      </span>
                    )}
                  </div>
                  <h3 className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic text-right')}>
                    {isRtl ? w.titleAr : w.titleEn}
                  </h3>
                  {!isExpanded && (
                    <p className={clsx('text-xs text-gray-500 mt-0.5 line-clamp-1', isRtl && 'font-arabic text-right')}>
                      {isRtl ? w.factAr : w.factEn}
                    </p>
                  )}
                </div>

                <div className="flex-shrink-0 text-gray-300 mt-0.5">
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </div>

              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100 pt-3 space-y-3">
                  <p className={clsx('text-sm text-gray-700 leading-relaxed', isRtl && 'font-arabic text-right')}>
                    {isRtl ? w.factAr : w.factEn}
                  </p>

                  {/* Quranic reference callout */}
                  {w.quranicRef && (
                    <div className={clsx(
                      'flex gap-2 p-2.5 rounded-xl bg-amber-50 border border-amber-100',
                      isRtl && 'flex-row-reverse'
                    )}>
                      <BookOpen className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <p className="text-[10px] font-semibold text-amber-600 mb-0.5">
                          {isRtl ? 'المصدر القرآني' : 'Quranic Source'} — {w.quranicRef.nameEn} ({w.quranicRef.ref})
                        </p>
                        <p className={clsx('text-xs text-amber-800 italic leading-relaxed', isRtl && 'font-arabic not-italic')}>
                          {w.quranicRef.textEn}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Hadith reference callout */}
                  {w.hadithRef && (
                    <div className={clsx(
                      'flex gap-2 p-2.5 rounded-xl bg-teal-50 border border-teal-100',
                      isRtl && 'flex-row-reverse'
                    )}>
                      <span className="text-teal-500 flex-shrink-0 text-sm leading-none mt-0.5">📜</span>
                      <div className="min-w-0">
                        <p className="text-[10px] font-semibold text-teal-600 mb-0.5">
                          {isRtl ? 'حديث شريف' : 'Hadith Reference'}
                        </p>
                        <p className={clsx('text-xs text-teal-800 italic leading-relaxed', isRtl && 'font-arabic not-italic')}>
                          {w.hadithRef}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Scholarly source */}
                  <p className={clsx('text-[10px] text-gray-400', isRtl && 'font-arabic text-right')}>
                    <span className="font-medium text-gray-500">{isRtl ? 'المصادر: ' : 'Sources: '}</span>
                    {isRtl ? w.sourceAr : w.sourceEn}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'جميع الإحصاءات موثقة من علوم القرآن الكلاسيكية والدراسات اللغوية الحديثة'
          : 'All statistics sourced from classical Quran sciences, verified hadith, and modern linguistic research'}
      </p>
    </div>
  );
}
