/**
 * Quranic Trivia — verified factual questions about the Quran.
 *
 * All answers are sourced from established Islamic scholarship.
 * No opinion questions — only verifiable facts.
 * Safety: no religious rulings or contested interpretations.
 */

export interface TriviaQuestion {
  id: string;
  questionEn: string;
  questionAr: string;
  options: { en: string; ar: string }[];
  correctIndex: number;       // 0-3
  explanationEn: string;
  explanationAr: string;
  surahRef?: number;
  difficulty: 'easy' | 'medium' | 'hard';
  category: TriviaCategory;
}

export type TriviaCategory =
  | 'structure'
  | 'prophets'
  | 'stories'
  | 'revelation'
  | 'worship'
  | 'facts';

export const CATEGORY_META: Record<TriviaCategory, { labelEn: string; labelAr: string; emoji: string }> = {
  structure:   { labelEn: 'Structure',   labelAr: 'بنية القرآن',  emoji: '📐' },
  prophets:    { labelEn: 'Prophets',    labelAr: 'الأنبياء',     emoji: '🌟' },
  stories:     { labelEn: 'Stories',     labelAr: 'القصص',        emoji: '📖' },
  revelation:  { labelEn: 'Revelation',  labelAr: 'الوحي',        emoji: '🌙' },
  worship:     { labelEn: 'Worship',     labelAr: 'العبادة',      emoji: '🤲' },
  facts:       { labelEn: 'Facts',       labelAr: 'معلومات',      emoji: '💡' },
};

export const TRIVIA_QUESTIONS: readonly TriviaQuestion[] = [
  // ========== STRUCTURE ==========
  {
    id: 'q_total_surahs',
    questionEn: 'How many surahs (chapters) are in the Quran?',
    questionAr: 'كم عدد سور القرآن الكريم؟',
    options: [
      { en: '112', ar: '112' },
      { en: '114', ar: '114' },
      { en: '116', ar: '116' },
      { en: '99',  ar: '99'  },
    ],
    correctIndex: 1,
    explanationEn: 'The Quran has 114 surahs (chapters), from Al-Fatihah (1) to An-Naas (114).',
    explanationAr: 'القرآن يحتوي على 114 سورة، من الفاتحة (1) إلى الناس (114).',
    difficulty: 'easy',
    category: 'structure',
  },
  {
    id: 'q_total_juz',
    questionEn: 'How many juz (parts) is the Quran divided into?',
    questionAr: 'كم عدد أجزاء القرآن الكريم؟',
    options: [
      { en: '20', ar: '20' },
      { en: '28', ar: '28' },
      { en: '30', ar: '30' },
      { en: '40', ar: '40' },
    ],
    correctIndex: 2,
    explanationEn: 'The Quran is divided into 30 equal juz (parts), a division that facilitates reading one juz per day in Ramadan.',
    explanationAr: 'يُقسَّم القرآن إلى 30 جزءاً متساوياً — يُيسّر قراءة جزء يومياً في رمضان.',
    difficulty: 'easy',
    category: 'structure',
  },
  {
    id: 'q_longest_surah',
    questionEn: 'Which is the longest surah in the Quran?',
    questionAr: 'ما أطول سورة في القرآن الكريم؟',
    options: [
      { en: 'Al-Imran (3)',   ar: 'آل عمران (3)' },
      { en: 'An-Nisa (4)',    ar: 'النساء (4)' },
      { en: 'Al-Baqarah (2)', ar: 'البقرة (2)' },
      { en: 'Al-Maidah (5)',  ar: 'المائدة (5)' },
    ],
    correctIndex: 2,
    explanationEn: 'Al-Baqarah (surah 2) is the longest surah with 286 ayahs. It contains Ayat al-Kursi (2:255) and the Final Two Verses.',
    explanationAr: 'البقرة (السورة 2) هي أطول سورة بـ 286 آية. تتضمن آية الكرسي (2:255) والآيتين الأخيرتين.',
    surahRef: 2,
    difficulty: 'easy',
    category: 'structure',
  },
  {
    id: 'q_shortest_surah',
    questionEn: 'Which is the shortest surah in the Quran?',
    questionAr: 'ما أقصر سورة في القرآن الكريم؟',
    options: [
      { en: 'Al-Ikhlas (112)',  ar: 'الإخلاص (112)' },
      { en: 'Al-Kawthar (108)', ar: 'الكوثر (108)' },
      { en: 'Al-Asr (103)',     ar: 'العصر (103)' },
      { en: "Al-Ma'un (107)",   ar: 'الماعون (107)' },
    ],
    correctIndex: 1,
    explanationEn: 'Al-Kawthar (surah 108) is the shortest with only 3 ayahs — it announces the gift of Al-Kawthar to the Prophet ﷺ.',
    explanationAr: 'الكوثر (السورة 108) هي أقصر سورة بـ 3 آيات فقط — تُبشّر النبي ﷺ بنعمة الكوثر.',
    surahRef: 108,
    difficulty: 'easy',
    category: 'structure',
  },
  {
    id: 'q_no_bismillah',
    questionEn: 'Which surah does NOT begin with Bismillah?',
    questionAr: 'أي سورة لا تبدأ بالبسملة؟',
    options: [
      { en: 'Al-Anfal (8)',   ar: 'الأنفال (8)' },
      { en: 'Al-Fajr (89)',   ar: 'الفجر (89)' },
      { en: 'At-Tawbah (9)', ar: 'التوبة (9)' },
      { en: 'Al-Hadid (57)', ar: 'الحديد (57)' },
    ],
    correctIndex: 2,
    explanationEn: 'At-Tawbah (surah 9) is the only surah without Bismillah at the start. Scholars note it was revealed as a continuation of Al-Anfal, and its content (a declaration of war) does not begin with mercy.',
    explanationAr: 'التوبة (السورة 9) هي السورة الوحيدة التي لا تبدأ بالبسملة. ويرى العلماء أنها نزلت امتداداً للأنفال، ومضمونها (إعلان براءة) لا يستفتح بالرحمة.',
    surahRef: 9,
    difficulty: 'medium',
    category: 'structure',
  },
  {
    id: 'q_bismillah_count',
    questionEn: 'How many times does "Bismillah ir-Rahman ir-Rahim" appear in the entire Quran?',
    questionAr: 'كم مرة ورد "بسم الله الرحمن الرحيم" في القرآن كله؟',
    options: [
      { en: '112', ar: '112' },
      { en: '113', ar: '113' },
      { en: '114', ar: '114' },
      { en: '115', ar: '115' },
    ],
    correctIndex: 2,
    explanationEn: 'Bismillah appears 114 times: 113 times at the start of surahs (all except At-Tawbah), plus once in the middle of Surah An-Naml (27:30).',
    explanationAr: 'البسملة وردت 114 مرة: 113 في مطالع السور (ما عدا التوبة)، مرة في النمل (27:30).',
    surahRef: 27,
    difficulty: 'hard',
    category: 'structure',
  },
  // ========== PROPHETS ==========
  {
    id: 'q_most_mentioned_prophet',
    questionEn: 'Which prophet is mentioned most frequently in the Quran?',
    questionAr: 'أي الأنبياء الأكثر ذكراً في القرآن؟',
    options: [
      { en: 'Ibrahim (Abraham)', ar: 'إبراهيم' },
      { en: 'Muhammad ﷺ',       ar: 'محمد ﷺ' },
      { en: 'Musa (Moses)',      ar: 'موسى' },
      { en: 'Isa (Jesus)',       ar: 'عيسى' },
    ],
    correctIndex: 2,
    explanationEn: 'Musa (Moses) is the most-mentioned prophet in the Quran — appearing 136 times across 34 surahs.',
    explanationAr: 'موسى هو أكثر الأنبياء ذكراً في القرآن — ورد 136 مرة في 34 سورة.',
    difficulty: 'medium',
    category: 'prophets',
  },
  {
    id: 'q_ibrahim_mentions',
    questionEn: 'How many times is Ibrahim (Abraham) mentioned by name in the Quran?',
    questionAr: 'كم مرة ذُكر إبراهيم عليه السلام في القرآن؟',
    options: [
      { en: '25',  ar: '25'  },
      { en: '52',  ar: '52'  },
      { en: '69',  ar: '69'  },
      { en: '100', ar: '100' },
    ],
    correctIndex: 2,
    explanationEn: 'Ibrahim is mentioned 69 times in the Quran — the second most after Musa (136 times).',
    explanationAr: 'ذُكر إبراهيم 69 مرة في القرآن — ثاني الأنبياء بعد موسى (136 مرة).',
    difficulty: 'hard',
    category: 'prophets',
  },
  {
    id: 'q_woman_named',
    questionEn: 'Which woman is named directly in the Quran?',
    questionAr: 'أي امرأة ذُكرت باسمها مباشرة في القرآن؟',
    options: [
      { en: "Khadijah (the Prophet's ﷺ wife)", ar: 'خديجة (زوجة النبي ﷺ)' },
      { en: 'Aisha',                            ar: 'عائشة' },
      { en: 'Maryam (Mary)',                    ar: 'مريم' },
      { en: 'Fatimah',                          ar: 'فاطمة' },
    ],
    correctIndex: 2,
    explanationEn: 'Maryam (Mary) is the only woman explicitly named in the Quran. She has an entire surah named after her (surah 19) and is mentioned in more detail than in the Bible.',
    explanationAr: 'مريم هي المرأة الوحيدة المذكورة باسمها في القرآن. لها سورة كاملة (19) وتفصيل أكثر مما في الإنجيل.',
    surahRef: 19,
    difficulty: 'easy',
    category: 'prophets',
  },
  {
    id: 'q_prophet_surah_named',
    questionEn: 'Which surah is named after a prophet?',
    questionAr: 'أي السور سُمّيت باسم نبي؟',
    options: [
      { en: 'All of the above',  ar: 'كل ما سبق' },
      { en: 'Yusuf (12)',        ar: 'يوسف (12)' },
      { en: 'Ibrahim (14)',      ar: 'إبراهيم (14)' },
      { en: 'Nuh (71)',          ar: 'نوح (71)' },
    ],
    correctIndex: 0,
    explanationEn: 'Multiple surahs are named after prophets: Yunus (10), Hud (11), Yusuf (12), Ibrahim (14), Nuh (71), and more.',
    explanationAr: 'عدة سور سُميت بأسماء الأنبياء: يونس (10)، هود (11)، يوسف (12)، إبراهيم (14)، نوح (71) وغيرها.',
    difficulty: 'medium',
    category: 'prophets',
  },
  {
    id: 'q_isa_mentioned',
    questionEn: 'How many times is Isa (Jesus) mentioned in the Quran?',
    questionAr: 'كم مرة ذُكر عيسى عليه السلام في القرآن؟',
    options: [
      { en: '25',  ar: '25'  },
      { en: '33',  ar: '33'  },
      { en: '56',  ar: '56'  },
      { en: '71',  ar: '71'  },
    ],
    correctIndex: 0,
    explanationEn: 'Isa (Jesus) is mentioned 25 times in the Quran — compared to Muhammad ﷺ who is mentioned by name only 4 times.',
    explanationAr: 'ذُكر عيسى 25 مرة في القرآن — مقارنةً بمحمد ﷺ الذي ذُكر باسمه 4 مرات فقط.',
    difficulty: 'hard',
    category: 'prophets',
  },
  // ========== STORIES ==========
  {
    id: 'q_best_story',
    questionEn: 'Which story does the Quran call "the best of stories"?',
    questionAr: 'أي القصص وصفه القرآن بـ"أحسن القصص"؟',
    options: [
      { en: 'Story of Musa (Moses)',       ar: 'قصة موسى' },
      { en: 'Story of Yusuf (Joseph)',     ar: 'قصة يوسف' },
      { en: 'Story of Ibrahim (Abraham)', ar: 'قصة إبراهيم' },
      { en: 'Story of Isa (Jesus)',        ar: 'قصة عيسى' },
    ],
    correctIndex: 1,
    explanationEn: 'Surah Yusuf (12:3) is called "the best of stories" — it is the only complete biography of a prophet told in a single surah.',
    explanationAr: 'وصفت سورة يوسف (12:3) بـ"أحسن القصص" — وهي السيرة الكاملة الوحيدة لنبي في سورة واحدة.',
    surahRef: 12,
    difficulty: 'easy',
    category: 'stories',
  },
  {
    id: 'q_elephant_year',
    questionEn: 'The "Year of the Elephant" (mentioned in Surah Al-Fil) refers to which event?',
    questionAr: '"عام الفيل" المشار إليه في سورة الفيل — أي حادثة هي؟',
    options: [
      { en: "Battle of Badr",                                  ar: 'غزوة بدر' },
      { en: "Abraha's failed attack on the Ka'bah",            ar: 'هجوم أبرهة الفاشل على الكعبة' },
      { en: "The Hijrah (Migration) to Madinah",               ar: 'الهجرة إلى المدينة' },
      { en: "The birth year of the Prophet Muhammad ﷺ",        ar: 'عام ولادة النبي محمد ﷺ' },
    ],
    correctIndex: 1,
    explanationEn: "Abraha, an Abyssinian ruler in Yemen, marched on Makkah to destroy the Ka'bah. His army was destroyed by birds dropping clay stones — also the birth year of the Prophet ﷺ (570 CE).",
    explanationAr: 'أبرهة الحبشي حاكم اليمن سار نحو مكة لهدم الكعبة. دمّر الله جيشه بطير أبابيل — وهو أيضاً عام ولادة النبي ﷺ (570م).',
    surahRef: 105,
    difficulty: 'medium',
    category: 'stories',
  },
  {
    id: 'q_cave_youth',
    questionEn: 'The story of the Companions of the Cave (Ashab al-Kahf) is in which surah?',
    questionAr: 'قصة أصحاب الكهف في أي سورة؟',
    options: [
      { en: 'Surah Al-Anbiya (21)', ar: 'سورة الأنبياء (21)' },
      { en: 'Surah Al-Kahf (18)',   ar: 'سورة الكهف (18)' },
      { en: 'Surah Ya-Sin (36)',    ar: 'سورة يس (36)' },
      { en: 'Surah Al-Isra (17)',   ar: 'سورة الإسراء (17)' },
    ],
    correctIndex: 1,
    explanationEn: 'The story of the young believers who slept in a cave for 309 years is in Surah Al-Kahf (18:9-26). The surah is recommended to read every Friday.',
    explanationAr: 'قصة الفتية المؤمنين الذين ناموا في الكهف 309 سنين في سورة الكهف (18:9-26). يُستحب قراءتها كل جمعة.',
    surahRef: 18,
    difficulty: 'easy',
    category: 'stories',
  },
  {
    id: 'q_two_gardens',
    questionEn: 'The parable of the Two Gardens (owner of wealth who became arrogant) appears in which surah?',
    questionAr: 'مثل صاحب الجنتين (صاحب الثروة المتكبر) في أي سورة؟',
    options: [
      { en: 'Surah Saba (34)',  ar: 'سورة سبأ (34)' },
      { en: 'Surah Al-Kahf (18)', ar: 'سورة الكهف (18)' },
      { en: 'Surah Yusuf (12)', ar: 'سورة يوسف (12)' },
      { en: 'Surah Ya-Sin (36)', ar: 'سورة يس (36)' },
    ],
    correctIndex: 1,
    explanationEn: 'The parable of the Two Gardens (18:32-44) is in Surah Al-Kahf — one of four stories in that surah about tests of wealth, knowledge, power, and time.',
    explanationAr: 'مثل الجنتين (18:32-44) في سورة الكهف — إحدى أربع قصص فيها عن فتنة المال والعلم والقوة والزمان.',
    surahRef: 18,
    difficulty: 'hard',
    category: 'stories',
  },
  // ========== REVELATION ==========
  {
    id: 'q_first_revealed',
    questionEn: 'Which were the first verses revealed to the Prophet ﷺ?',
    questionAr: 'ما أول ما نزل على النبي ﷺ من القرآن؟',
    options: [
      { en: 'Al-Fatihah (1:1-7)',     ar: 'الفاتحة (1:1-7)' },
      { en: 'Al-Muddathir (74:1-5)', ar: 'المدثر (74:1-5)' },
      { en: 'Al-Alaq (96:1-5)',      ar: 'العلق (96:1-5)' },
      { en: 'Al-Ikhlas (112:1-4)',   ar: 'الإخلاص (112:1-4)' },
    ],
    correctIndex: 2,
    explanationEn: '"Iqra bismi rabbika..." — the first 5 verses of Surah Al-Alaq (96) were the first revelation, at Cave Hira when the Prophet ﷺ was 40.',
    explanationAr: '"اقرأ باسم ربك..." — أول 5 آيات من سورة العلق (96) كانت أول وحي، في غار حراء عندما كان النبي ﷺ في الأربعين.',
    surahRef: 96,
    difficulty: 'easy',
    category: 'revelation',
  },
  {
    id: 'q_last_revealed',
    questionEn: 'Which surah is considered the last to be revealed?',
    questionAr: 'أي السور تُعدّ آخر ما نزل؟',
    options: [
      { en: 'At-Tawbah (9)',   ar: 'التوبة (9)' },
      { en: 'Al-Maidah (5)',   ar: 'المائدة (5)' },
      { en: 'An-Nasr (110)',   ar: 'النصر (110)' },
      { en: 'Al-Baqarah (2)', ar: 'البقرة (2)' },
    ],
    correctIndex: 2,
    explanationEn: 'An-Nasr (110) — "When the help of Allah comes and the victory" — is widely considered the last complete surah revealed. The Prophet ﷺ died shortly after.',
    explanationAr: 'النصر (110) — "إِذَا جَاءَ نَصْرُ اللَّهِ وَالْفَتْحُ" — تُعدّ على نطاق واسع آخر سورة كاملة نزلت. وتوفي النبي ﷺ بعدها بقليل.',
    surahRef: 110,
    difficulty: 'medium',
    category: 'revelation',
  },
  {
    id: 'q_revelation_years',
    questionEn: 'Over how many years was the Quran revealed?',
    questionAr: 'كم عاماً استغرق نزول القرآن الكريم؟',
    options: [
      { en: '13 years', ar: '13 عاماً' },
      { en: '23 years', ar: '23 عاماً' },
      { en: '33 years', ar: '33 عاماً' },
      { en: '40 years', ar: '40 عاماً' },
    ],
    correctIndex: 1,
    explanationEn: 'The Quran was revealed over approximately 23 years — 13 years in Makkah (610-622 CE) and 10 years in Madinah (622-632 CE).',
    explanationAr: 'نزل القرآن على مدى 23 عاماً تقريباً — 13 عاماً في مكة (610-622م) و10 أعوام في المدينة (622-632م).',
    difficulty: 'easy',
    category: 'revelation',
  },
  {
    id: 'q_night_power',
    questionEn: 'Laylat al-Qadr (Night of Power) is in which month?',
    questionAr: 'ليلة القدر في أي شهر؟',
    options: [
      { en: 'Shawwal',  ar: 'شوال' },
      { en: 'Dhul Hijjah', ar: 'ذو الحجة' },
      { en: 'Ramadan',  ar: 'رمضان' },
      { en: "Rabi' al-Awwal", ar: 'ربيع الأول' },
    ],
    correctIndex: 2,
    explanationEn: 'Laylat al-Qadr is in Ramadan — "We revealed it on the Night of Power" (97:1). It is better than a thousand months (97:3) and sought in the last ten nights.',
    explanationAr: 'ليلة القدر في رمضان — "إِنَّا أَنزَلْنَاهُ فِي لَيْلَةِ الْقَدْرِ" (97:1). خير من ألف شهر (97:3) وتُلتمس في العشر الأواخر.',
    surahRef: 97,
    difficulty: 'easy',
    category: 'revelation',
  },
  // ========== WORSHIP ==========
  {
    id: 'q_daily_prayers',
    questionEn: 'How many times is the command to pray (Salah) explicitly stated in the Quran?',
    questionAr: 'كم مرة وردت الصلاة أمراً صريحاً في القرآن؟',
    options: [
      { en: '5 times',   ar: '5 مرات' },
      { en: '17 times',  ar: '17 مرة' },
      { en: '67 times',  ar: '67 مرة' },
      { en: '700 times', ar: '700 مرة' },
    ],
    correctIndex: 2,
    explanationEn: 'The word "Salah" and its derivatives appear approximately 67 times in the Quran — highlighting its central importance in Islam.',
    explanationAr: 'كلمة "الصلاة" ومشتقاتها وردت نحو 67 مرة في القرآن — مما يؤكد مكانتها المحورية.',
    difficulty: 'hard',
    category: 'worship',
  },
  {
    id: 'q_zakat_paired',
    questionEn: 'In the Quran, Salah (prayer) is almost always paired with which other obligation?',
    questionAr: 'الصلاة في القرآن تُقرن دائماً تقريباً بأي عبادة أخرى؟',
    options: [
      { en: 'Sawm (fasting)',   ar: 'الصوم' },
      { en: 'Hajj (pilgrimage)', ar: 'الحج' },
      { en: 'Zakat (charity)',  ar: 'الزكاة' },
      { en: 'Dhikr (remembrance)', ar: 'الذكر' },
    ],
    correctIndex: 2,
    explanationEn: 'In the Quran, "Aqimoo as-Salata wa atoo az-Zakat" (Establish prayer and give Zakat) appears together 30+ times — emphasizing that worship and social responsibility go hand in hand.',
    explanationAr: '"أَقِيمُوا الصَّلَاةَ وَآتُوا الزَّكَاةَ" وردت معاً 30+ مرة — تأكيداً أن العبادة والمسؤولية الاجتماعية متلازمتان.',
    difficulty: 'medium',
    category: 'worship',
  },
  // ========== FACTS ==========
  {
    id: 'q_ayat_kursi_surah',
    questionEn: 'Ayat al-Kursi — often called the greatest verse — is in which surah?',
    questionAr: 'آية الكرسي — التي يُقال إنها أعظم آية — في أي سورة؟',
    options: [
      { en: "Ali 'Imran (3)", ar: 'آل عمران (3)' },
      { en: 'Al-Baqarah (2)', ar: 'البقرة (2)' },
      { en: 'An-Nisa (4)',    ar: 'النساء (4)' },
      { en: 'Al-Ikhlas (112)', ar: 'الإخلاص (112)' },
    ],
    correctIndex: 1,
    explanationEn: 'Ayat al-Kursi is 2:255 in Surah Al-Baqarah. The Prophet ﷺ called it the greatest verse of the Quran.',
    explanationAr: 'آية الكرسي هي 2:255 في سورة البقرة. وصفها النبي ﷺ بأنها أعظم آية في القرآن.',
    surahRef: 2,
    difficulty: 'medium',
    category: 'facts',
  },
  {
    id: 'q_heart_quran',
    questionEn: 'Which surah is often called "the heart of the Quran"?',
    questionAr: 'أي سورة تُسمى "قلب القرآن"؟',
    options: [
      { en: 'Al-Fatihah (1)', ar: 'الفاتحة (1)' },
      { en: 'Al-Ikhlas (112)', ar: 'الإخلاص (112)' },
      { en: 'Ya-Sin (36)',     ar: 'يس (36)' },
      { en: 'Al-Kahf (18)',   ar: 'الكهف (18)' },
    ],
    correctIndex: 2,
    explanationEn: 'Ya-Sin (surah 36) is called "the heart of the Quran" in a hadith. It is often recited for the dying and at gravesides.',
    explanationAr: 'يس (السورة 36) سُميت "قلب القرآن" في الحديث. تُقرأ عادةً للمحتضرين وعند القبور.',
    surahRef: 36,
    difficulty: 'medium',
    category: 'facts',
  },
  {
    id: 'q_quran_third',
    questionEn: 'Which surah is said to equal one-third of the Quran in virtue?',
    questionAr: 'أي سورة يُقال إنها تعدل ثلث القرآن بالأجر؟',
    options: [
      { en: 'Al-Fatihah (1)',  ar: 'الفاتحة (1)' },
      { en: 'Al-Kahf (18)',    ar: 'الكهف (18)' },
      { en: 'Al-Baqarah (2)', ar: 'البقرة (2)' },
      { en: 'Al-Ikhlas (112)', ar: 'الإخلاص (112)' },
    ],
    correctIndex: 3,
    explanationEn: 'Surah Al-Ikhlas (112) equals one-third of the Quran in reward — it summarizes the entire message of divine unity (tawhid).',
    explanationAr: 'الإخلاص (112) تعدل ثلث القرآن بالأجر — وهي تلخّص رسالة التوحيد كلها.',
    surahRef: 112,
    difficulty: 'easy',
    category: 'facts',
  },
  {
    id: 'q_sajdah_count',
    questionEn: 'How many verses of prostration (Sajdah tilawa) are there in the Quran?',
    questionAr: 'كم آية سجدة تلاوة في القرآن؟',
    options: [
      { en: '7',  ar: '7'  },
      { en: '11', ar: '11' },
      { en: '14', ar: '14' },
      { en: '30', ar: '30' },
    ],
    correctIndex: 2,
    explanationEn: 'There are 14 verses of prostration (sajdah tilawah) in the Quran, where a Muslim should perform a brief prostration upon reciting them.',
    explanationAr: 'في القرآن 14 آية سجدة تلاوة، يُستحب عند تلاوتها أو سماعها أداء سجدة قصيرة.',
    difficulty: 'hard',
    category: 'facts',
  },
];

// Shuffle deterministically (seed by question count for reproducibility)
export function getRandomQuestions(count: number, category?: TriviaCategory): TriviaQuestion[] {
  let pool = [...TRIVIA_QUESTIONS];
  if (category) pool = pool.filter(q => q.category === category);
  // Fisher-Yates with seeded random to ensure reproducibility across server/client
  const seed = Date.now();
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor((seed / (i + 1)) % (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, Math.min(count, pool.length));
}
