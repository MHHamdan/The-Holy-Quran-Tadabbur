/**
 * Adhkar (Remembrances) — common Quranic and prophetic dhikr.
 *
 * Each entry includes the Arabic phrase, transliteration, meaning,
 * the target count, and the Quranic reference or hadith source.
 *
 * Safety: meanings are translational (not rulings). All references are cited.
 * Prophetic references cite Sahih Bukhari/Muslim. No AI-generated content.
 */

export type DhikrCategory =
  | 'morning'
  | 'evening'
  | 'after_salah'
  | 'any_time'
  | 'quranic';

export interface DhikrEntry {
  id: string;
  arabicPhrase: string;
  transliteration: string;
  meaningEn: string;
  meaningAr: string;
  targetCount: number;
  category: DhikrCategory;
  sourceRef: string;
  sourceRefAr: string;
  benefitEn: string;
  benefitAr: string;
}

export const CATEGORY_META: Record<DhikrCategory, { labelEn: string; labelAr: string; color: string; emoji: string }> = {
  morning:     { labelEn: 'Morning',      labelAr: 'الصباح',       color: 'amber',   emoji: '🌅' },
  evening:     { labelEn: 'Evening',      labelAr: 'المساء',       color: 'indigo',  emoji: '🌙' },
  after_salah: { labelEn: 'After Prayer', labelAr: 'بعد الصلاة',   color: 'emerald', emoji: '🤲' },
  any_time:    { labelEn: 'Anytime',      labelAr: 'في كل وقت',    color: 'violet',  emoji: '♾️' },
  quranic:     { labelEn: 'Quranic',      labelAr: 'من القرآن',    color: 'teal',    emoji: '📖' },
};

export const ADHKAR: readonly DhikrEntry[] = [
  {
    id: 'subhanallah',
    arabicPhrase: 'سُبْحَانَ اللَّهِ',
    transliteration: 'SubhanAllah',
    meaningEn: 'Glory be to Allah',
    meaningAr: 'سبحان الله',
    targetCount: 33,
    category: 'after_salah',
    sourceRef: 'Bukhari 843, Muslim 597',
    sourceRefAr: 'البخاري 843، مسلم 597',
    benefitEn: 'Reciting 33× after each prayer, then completing with la ilaha illallah',
    benefitAr: 'قولها 33 مرة بعد كل صلاة، ثم إتمامها بلا إله إلا الله',
  },
  {
    id: 'alhamdulillah',
    arabicPhrase: 'الْحَمْدُ لِلَّهِ',
    transliteration: 'Alhamdulillah',
    meaningEn: 'All praise and thanks are due to Allah',
    meaningAr: 'الحمد لله',
    targetCount: 33,
    category: 'after_salah',
    sourceRef: 'Bukhari 843, Muslim 597',
    sourceRefAr: 'البخاري 843، مسلم 597',
    benefitEn: '"It fills the scale" — the Prophet ﷺ',
    benefitAr: '"تملأ الميزان" — النبي ﷺ',
  },
  {
    id: 'allahu_akbar',
    arabicPhrase: 'اللَّهُ أَكْبَرُ',
    transliteration: 'Allahu Akbar',
    meaningEn: 'Allah is the Greatest',
    meaningAr: 'الله أكبر',
    targetCount: 34,
    category: 'after_salah',
    sourceRef: 'Bukhari 843, Muslim 597',
    sourceRefAr: 'البخاري 843، مسلم 597',
    benefitEn: 'Completes the 100-count tasbih with SubhanAllah (33) + Alhamdulillah (33) + Allahu Akbar (34)',
    benefitAr: 'يُكمل التسبيح المئة: سبحان الله (33) + الحمد لله (33) + الله أكبر (34)',
  },
  {
    id: 'la_ilaha_illallah',
    arabicPhrase: 'لَا إِلَهَ إِلَّا اللَّهُ',
    transliteration: 'La ilaha illallah',
    meaningEn: 'There is no god but Allah',
    meaningAr: 'لا إله إلا الله',
    targetCount: 100,
    category: 'any_time',
    sourceRef: 'Bukhari 6403, Muslim 2693',
    sourceRefAr: 'البخاري 6403، مسلم 2693',
    benefitEn: '"The best of dhikr" — Prophet ﷺ. Erases sins like foam of the sea.',
    benefitAr: '"أفضل الذكر" — النبي ﷺ. تمحو الذنوب كزبد البحر.',
  },
  {
    id: 'astaghfirullah',
    arabicPhrase: 'أَسْتَغْفِرُ اللَّهَ',
    transliteration: 'Astaghfirullah',
    meaningEn: 'I seek forgiveness from Allah',
    meaningAr: 'أستغفر الله',
    targetCount: 100,
    category: 'any_time',
    sourceRef: 'Muslim 2702',
    sourceRefAr: 'مسلم 2702',
    benefitEn: 'The Prophet ﷺ sought forgiveness 100× daily. Opens doors of sustenance (71:10-12).',
    benefitAr: 'كان النبي ﷺ يستغفر 100 مرة يومياً. يفتح أبواب الرزق (71:10-12).',
  },
  {
    id: 'salawat',
    arabicPhrase: 'اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ',
    transliteration: 'Allahumma salli ala Muhammad',
    meaningEn: 'O Allah, send blessings upon Muhammad',
    meaningAr: 'اللهم صل على محمد',
    targetCount: 10,
    category: 'any_time',
    sourceRef: 'Quran 33:56 — "Allah and His angels send blessings on the Prophet"',
    sourceRefAr: 'القرآن 33:56 — "إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ"',
    benefitEn: '10 blessings returned for each salawah — 10× in morning/evening especially recommended',
    benefitAr: 'عشر صلوات مقابل كل واحدة — 10× صباحاً ومساءً موصى به',
  },
  {
    id: 'ayat_kursi',
    arabicPhrase: 'اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ',
    transliteration: 'Ayat al-Kursi (2:255)',
    meaningEn: 'Allah — there is no deity except Him, the Ever-Living, the Self-Sustaining…',
    meaningAr: 'آية الكرسي (2:255)',
    targetCount: 1,
    category: 'after_salah',
    sourceRef: 'Quran 2:255 — Reciting after each prayer, one will be in Paradise\'s protection',
    sourceRefAr: 'القرآن 2:255 — قراءتها بعد كل صلاة تضمن دخول الجنة',
    benefitEn: '"Whoever recites Ayat al-Kursi after each prayer — only death prevents him from entering Paradise" (Nasai)',
    benefitAr: '"من قرأ آية الكرسي بعد كل صلاة لم يمنعه من دخول الجنة إلا الموت" (النسائي)',
  },
  {
    id: 'hasbunallah',
    arabicPhrase: 'حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ',
    transliteration: 'HasbunAllahu wa ni\'mal wakil',
    meaningEn: 'Sufficient for us is Allah, and He is the best disposer of affairs',
    meaningAr: 'حسبنا الله ونعم الوكيل',
    targetCount: 7,
    category: 'any_time',
    sourceRef: 'Quran 3:173 — said by the believers facing the army',
    sourceRefAr: 'القرآن 3:173 — قالها المؤمنون في وجه الجيش',
    benefitEn: 'Ibrahim ﷺ said it when cast into fire — Allah made it cool (Bukhari 4563)',
    benefitAr: 'قالها إبراهيم ﷺ حين أُلقي في النار فجعلها الله برداً (البخاري 4563)',
  },
  {
    id: 'la_hawla',
    arabicPhrase: 'لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ',
    transliteration: "La hawla wa la quwwata illa billah",
    meaningEn: 'There is no power and no strength except with Allah',
    meaningAr: 'لا حول ولا قوة إلا بالله',
    targetCount: 100,
    category: 'any_time',
    sourceRef: 'Bukhari 6409, Muslim 2704',
    sourceRefAr: 'البخاري 6409، مسلم 2704',
    benefitEn: '"A treasure from the treasures of Paradise" — Prophet ﷺ',
    benefitAr: '"كنز من كنوز الجنة" — النبي ﷺ',
  },
  {
    id: 'bismillah',
    arabicPhrase: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
    transliteration: 'Bismillah ir-Rahman ir-Rahim',
    meaningEn: 'In the name of Allah, the Most Gracious, the Most Merciful',
    meaningAr: 'بسم الله الرحمن الرحيم',
    targetCount: 1,
    category: 'quranic',
    sourceRef: 'Quran 1:1 — opening of the Quran, 113 surahs begin with it',
    sourceRefAr: 'القرآن 1:1 — فاتحة القرآن، 113 سورة تبدأ بها',
    benefitEn: 'Said before every act — blessing and protection. 114 times in the Quran.',
    benefitAr: 'تُقال قبل كل عمل — بركة وحماية. وردت 114 مرة في القرآن.',
  },
  {
    id: 'inna_lillah',
    arabicPhrase: 'إِنَّا لِلَّهِ وَإِنَّا إِلَيْهِ رَاجِعُونَ',
    transliteration: 'Inna lillahi wa inna ilayhi raji\'un',
    meaningEn: 'Indeed, to Allah we belong and to Him we shall return',
    meaningAr: 'إنا لله وإنا إليه راجعون',
    targetCount: 3,
    category: 'quranic',
    sourceRef: 'Quran 2:156 — said by the patient in adversity',
    sourceRefAr: 'القرآن 2:156 — يقولها الصابرون في المصيبة',
    benefitEn: '"Those are the ones upon whom are blessings from their Lord and mercy" (2:157)',
    benefitAr: '"أُولَٰئِكَ عَلَيْهِمْ صَلَوَاتٌ مِّن رَّبِّهِمْ وَرَحْمَةٌ" (2:157)',
  },
  {
    id: 'rabbana_atina',
    arabicPhrase: 'رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً',
    transliteration: "Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan",
    meaningEn: 'Our Lord, give us good in this world and good in the next',
    meaningAr: 'ربنا آتنا في الدنيا حسنة وفي الآخرة حسنة',
    targetCount: 3,
    category: 'quranic',
    sourceRef: 'Quran 2:201 — the best of supplications',
    sourceRefAr: 'القرآن 2:201 — أفضل الأدعية',
    benefitEn: 'The Prophet ﷺ most frequently made this supplication (Bukhari 4522)',
    benefitAr: 'كان النبي ﷺ يكثر من هذا الدعاء (البخاري 4522)',
  },
  {
    id: 'morning_zikr_sabah',
    arabicPhrase: 'أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ',
    transliteration: 'Asbahna wa asbahal-mulku lillah',
    meaningEn: 'We enter the morning and sovereignty belongs to Allah',
    meaningAr: 'أصبحنا وأصبح الملك لله',
    targetCount: 1,
    category: 'morning',
    sourceRef: 'Abu Dawud 5071, Tirmidhi 3391',
    sourceRefAr: 'أبو داود 5071، الترمذي 3391',
    benefitEn: 'Opens the morning with acknowledgment of divine sovereignty',
    benefitAr: 'يفتح الصباح بالإقرار بالسيادة الإلهية',
  },
  {
    id: 'evening_zikr',
    arabicPhrase: 'أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ',
    transliteration: 'Amsayna wa amsal-mulku lillah',
    meaningEn: 'We enter the evening and sovereignty belongs to Allah',
    meaningAr: 'أمسينا وأمسى الملك لله',
    targetCount: 1,
    category: 'evening',
    sourceRef: 'Abu Dawud 5071',
    sourceRefAr: 'أبو داود 5071',
    benefitEn: 'Evening counterpart of the morning dhikr',
    benefitAr: 'نظير المساء لذكر الصباح',
  },
  {
    id: 'tasbih_fatima',
    arabicPhrase: 'سُبْحَانَ اللَّهِ • الْحَمْدُ لِلَّهِ • اللَّهُ أَكْبَرُ',
    transliteration: 'SubhanAllah (33) · Alhamdulillah (33) · Allahu Akbar (34)',
    meaningEn: 'Tasbih of Fatima — after every obligatory prayer and at bedtime',
    meaningAr: 'تسبيح فاطمة — بعد كل صلاة مفروضة وعند النوم',
    targetCount: 100,
    category: 'after_salah',
    sourceRef: 'Bukhari 3113, Muslim 2727',
    sourceRefAr: 'البخاري 3113، مسلم 2727',
    benefitEn: '"Better for you than a servant" — Prophet ﷺ to Ali and Fatima',
    benefitAr: '"خير لكما من خادم" — النبي ﷺ لعلي وفاطمة',
  },
];
