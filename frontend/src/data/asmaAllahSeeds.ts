/**
 * Asmā' Allah al-Ḥusnā Seeds — Phase W.
 *
 * Each entry is a *candidate* detection record. The build script
 * (`scripts/build-asma-allah-atlas.ts`) consumes these aliases to detect
 * Quran occurrences. Findings default to reviewStatus="needs_review" and
 * humanReviewRequired=true.
 *
 * Hard rules:
 *   - The 99 traditional names are seeded for navigation; not every name
 *     necessarily occurs explicitly in the Quran text. Names with zero
 *     Quran occurrences are surfaced with a warning by the script.
 *   - Aliases are surface forms — typically `name_simple` without tashkeel.
 *     The scanner additionally normalises both sides (drop tashkeel/hamza,
 *     alif/ya/ta-marbuta unification).
 *   - Categories (dhat / jamal / jalal / kamal / afaal) carry the project's
 *     existing classification (from `backend/app/data/allah_names.py`), but
 *     they remain `needs_review` for the atlas until a verified source is
 *     attached.
 */

import type { AsmaAllahSeed } from '../types/asmaAllah';

export const ASMA_ALLAH_SEEDS: AsmaAllahSeed[] = [
  // === Allah — اسم الجلالة (The Divine Name, shown separately from the 99) ===
  // Per docs/asma-name-detection-policy.md, "Allah" is the supreme/Divine
  // Name that the 99 Beautiful Names describe — it is NOT one of the 99.
  // We keep the seed here so the scanner still detects occurrences and the
  // standalone hero panel can render its Quran evidence, but the atlas
  // builder partitions it out of the primary 99-Names list.
  {
    nameId: 'allah',
    arabicName: 'اللَّه',
    transliteration: 'Allah',
    englishName: 'Allah',
    category: 'dhat',
    aliasesArabic: ['الله', 'اللَّه', 'ٱللَّه'],
    inTraditional99: false,
    warnings: [
      'Highest-frequency lemma in the Quran; the scanner uses strict word-boundary detection on the right side and accepts Arabic clitic prefixes (و, ف, ل, ب, ك) on the left.',
      'The Divine Name "Allah" (اسم الجلالة) is displayed separately from the 99 Beautiful Names list — it is the supreme Name that the 99 describe.',
    ],
  },

  // === 99 names (canonical order from the existing backend module) ===
  { nameId: 'ar_rahman', arabicName: 'الرَّحْمَنُ', transliteration: 'Ar-Rahman', englishName: 'The Most Gracious', category: 'jamal', aliasesArabic: ['الرحمن', 'الرحمٰن'] },
  { nameId: 'ar_raheem', arabicName: 'الرَّحِيمُ', transliteration: 'Ar-Raheem', englishName: 'The Most Merciful', category: 'jamal', aliasesArabic: ['الرحيم'] },
  { nameId: 'al_malik', arabicName: 'المَلِكُ', transliteration: 'Al-Malik', englishName: 'The King', category: 'jalal', aliasesArabic: ['الملك'], warnings: ['"الملك" also means "the dominion/kingdom"; reviewer must verify each occurrence in context.'] },
  { nameId: 'al_quddus', arabicName: 'القُدُّوسُ', transliteration: 'Al-Quddus', englishName: 'The Most Holy', category: 'dhat', aliasesArabic: ['القدوس'] },
  { nameId: 'as_salam', arabicName: 'السَّلَامُ', transliteration: 'As-Salam', englishName: 'The Source of Peace', category: 'dhat', aliasesArabic: ['السلام'], warnings: ['"السلام" also means "peace" (the greeting); reviewer must verify each occurrence as a divine name.'] },
  { nameId: 'al_mumin', arabicName: 'المُؤْمِنُ', transliteration: "Al-Mu'min", englishName: 'The Granter of Security', category: 'jamal', aliasesArabic: ['المؤمن'], warnings: ['"المؤمن" most commonly refers to "the believer"; only one verse (59:23) uses it as a divine name. Reviewer must verify.'] },
  { nameId: 'al_muhaymin', arabicName: 'المُهَيْمِنُ', transliteration: 'Al-Muhaymin', englishName: 'The Guardian', category: 'jalal', aliasesArabic: ['المهيمن'] },
  { nameId: 'al_aziz', arabicName: 'العَزِيزُ', transliteration: 'Al-Aziz', englishName: 'The Almighty', category: 'jalal', aliasesArabic: ['العزيز'], warnings: ['"العزيز" is also a personal-name title (Aziz of Egypt in Surah Yusuf); reviewer must verify each occurrence.'] },
  { nameId: 'al_jabbar', arabicName: 'الجَبَّارُ', transliteration: 'Al-Jabbar', englishName: 'The Compeller', category: 'jalal', aliasesArabic: ['الجبار'] },
  { nameId: 'al_mutakabbir', arabicName: 'المُتَكَبِّرُ', transliteration: 'Al-Mutakabbir', englishName: 'The Supreme', category: 'jalal', aliasesArabic: ['المتكبر'] },
  { nameId: 'al_khaliq', arabicName: 'الخَالِقُ', transliteration: 'Al-Khaliq', englishName: 'The Creator', category: 'afaal', aliasesArabic: ['الخالق'] },
  { nameId: 'al_bari', arabicName: 'البَارِئُ', transliteration: "Al-Bari'", englishName: 'The Originator', category: 'afaal', aliasesArabic: ['البارئ'] },
  { nameId: 'al_musawwir', arabicName: 'المُصَوِّرُ', transliteration: 'Al-Musawwir', englishName: 'The Fashioner', category: 'afaal', aliasesArabic: ['المصور'] },
  { nameId: 'al_ghaffar', arabicName: 'الغَفَّارُ', transliteration: 'Al-Ghaffar', englishName: 'The Oft-Forgiving', category: 'jamal', aliasesArabic: ['الغفار'] },
  { nameId: 'al_qahhar', arabicName: 'القَهَّارُ', transliteration: 'Al-Qahhar', englishName: 'The Subduer', category: 'jalal', aliasesArabic: ['القهار'] },
  { nameId: 'al_wahhab', arabicName: 'الوَهَّابُ', transliteration: 'Al-Wahhab', englishName: 'The Bestower', category: 'jamal', aliasesArabic: ['الوهاب'] },
  { nameId: 'ar_razzaq', arabicName: 'الرَّزَّاقُ', transliteration: 'Ar-Razzaq', englishName: 'The Provider', category: 'jamal', aliasesArabic: ['الرزاق'] },
  { nameId: 'al_fattah', arabicName: 'الفَتَّاحُ', transliteration: 'Al-Fattah', englishName: 'The Opener', category: 'afaal', aliasesArabic: ['الفتاح'] },
  { nameId: 'al_alim', arabicName: 'العَلِيمُ', transliteration: 'Al-Alim', englishName: 'The All-Knowing', category: 'dhat', aliasesArabic: ['العليم'] },
  { nameId: 'al_qabid', arabicName: 'القَابِضُ', transliteration: 'Al-Qabid', englishName: 'The Withholder', category: 'afaal', aliasesArabic: ['القابض'], warnings: ['Rarely used as an explicit divine name in Quran text; reviewer must verify any occurrence.'] },
  { nameId: 'al_basit', arabicName: 'البَاسِطُ', transliteration: 'Al-Basit', englishName: 'The Expander', category: 'afaal', aliasesArabic: ['الباسط'], warnings: ['Rarely used as an explicit divine name in Quran text; reviewer must verify any occurrence.'] },
  { nameId: 'al_khafid', arabicName: 'الخَافِضُ', transliteration: 'Al-Khafid', englishName: 'The Abaser', category: 'afaal', aliasesArabic: ['الخافض'], warnings: ['Not in Quran as an explicit divine name; from hadith traditions.'] },
  { nameId: 'ar_rafi', arabicName: 'الرَّافِعُ', transliteration: 'Ar-Rafi', englishName: 'The Exalter', category: 'afaal', aliasesArabic: ['الرافع'] },
  { nameId: 'al_muizz', arabicName: 'المُعِزُّ', transliteration: "Al-Mu'izz", englishName: 'The Bestower of Honor', category: 'afaal', aliasesArabic: ['المعز'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_mudhill', arabicName: 'المُذِلُّ', transliteration: 'Al-Mudhill', englishName: 'The Humiliator', category: 'afaal', aliasesArabic: ['المذل'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'as_sami', arabicName: 'السَّمِيعُ', transliteration: 'As-Sami', englishName: 'The All-Hearing', category: 'dhat', aliasesArabic: ['السميع'] },
  { nameId: 'al_basir', arabicName: 'البَصِيرُ', transliteration: 'Al-Basir', englishName: 'The All-Seeing', category: 'dhat', aliasesArabic: ['البصير'] },
  { nameId: 'al_hakam', arabicName: 'الحَكَمُ', transliteration: 'Al-Hakam', englishName: 'The Judge', category: 'jalal', aliasesArabic: ['الحكم'], warnings: ['"الحكم" is also a personal name (Hakam ibn Awana); reviewer must verify.'] },
  { nameId: 'al_adl', arabicName: 'العَدْلُ', transliteration: 'Al-Adl', englishName: 'The Just', category: 'kamal', aliasesArabic: ['العدل'], warnings: ['"العدل" most commonly means "justice" as a noun; rarely used as an explicit divine name.'] },
  { nameId: 'al_latif', arabicName: 'اللَّطِيفُ', transliteration: 'Al-Latif', englishName: 'The Subtle One', category: 'jamal', aliasesArabic: ['اللطيف'] },
  { nameId: 'al_khabir', arabicName: 'الخَبِيرُ', transliteration: 'Al-Khabir', englishName: 'The All-Aware', category: 'dhat', aliasesArabic: ['الخبير'] },
  { nameId: 'al_halim', arabicName: 'الحَلِيمُ', transliteration: 'Al-Halim', englishName: 'The Forbearing', category: 'jamal', aliasesArabic: ['الحليم'] },
  { nameId: 'al_azim', arabicName: 'العَظِيمُ', transliteration: 'Al-Azim', englishName: 'The Magnificent', category: 'dhat', aliasesArabic: ['العظيم'] },
  { nameId: 'al_ghafur', arabicName: 'الغَفُورُ', transliteration: 'Al-Ghafur', englishName: 'The All-Forgiving', category: 'jamal', aliasesArabic: ['الغفور'] },
  { nameId: 'ash_shakur', arabicName: 'الشَّكُورُ', transliteration: 'Ash-Shakur', englishName: 'The Appreciative', category: 'jamal', aliasesArabic: ['الشكور'] },
  { nameId: 'al_aliyy', arabicName: 'العَلِيُّ', transliteration: 'Al-Aliyy', englishName: 'The Most High', category: 'dhat', aliasesArabic: ['العلي'] },
  { nameId: 'al_kabir', arabicName: 'الكَبِيرُ', transliteration: 'Al-Kabir', englishName: 'The Great', category: 'dhat', aliasesArabic: ['الكبير'] },
  { nameId: 'al_hafiz', arabicName: 'الحَفِيظُ', transliteration: 'Al-Hafiz', englishName: 'The Preserver', category: 'afaal', aliasesArabic: ['الحفيظ'] },
  { nameId: 'al_muqit', arabicName: 'المُقِيتُ', transliteration: 'Al-Muqit', englishName: 'The Sustainer', category: 'afaal', aliasesArabic: ['المقيت'] },
  { nameId: 'al_hasib', arabicName: 'الحَسِيبُ', transliteration: 'Al-Hasib', englishName: 'The Reckoner', category: 'afaal', aliasesArabic: ['الحسيب'] },
  { nameId: 'al_jalil', arabicName: 'الجَلِيلُ', transliteration: 'Al-Jalil', englishName: 'The Majestic', category: 'jalal', aliasesArabic: ['الجليل'], warnings: ['Rarely used as a standalone divine name; appears within "ذو الجلال والإكرام".'] },
  { nameId: 'al_karim', arabicName: 'الكَرِيمُ', transliteration: 'Al-Karim', englishName: 'The Generous', category: 'jamal', aliasesArabic: ['الكريم'] },
  { nameId: 'ar_raqib', arabicName: 'الرَّقِيبُ', transliteration: 'Ar-Raqib', englishName: 'The Watchful', category: 'dhat', aliasesArabic: ['الرقيب'] },
  { nameId: 'al_mujib', arabicName: 'المُجِيبُ', transliteration: 'Al-Mujib', englishName: 'The Responsive', category: 'jamal', aliasesArabic: ['المجيب'] },
  { nameId: 'al_wasi', arabicName: 'الوَاسِعُ', transliteration: 'Al-Wasi', englishName: 'The All-Encompassing', category: 'dhat', aliasesArabic: ['الواسع'] },
  { nameId: 'al_hakim', arabicName: 'الحَكِيمُ', transliteration: 'Al-Hakim', englishName: 'The All-Wise', category: 'kamal', aliasesArabic: ['الحكيم'] },
  { nameId: 'al_wadud', arabicName: 'الوَدُودُ', transliteration: 'Al-Wadud', englishName: 'The Most Loving', category: 'jamal', aliasesArabic: ['الودود'] },
  { nameId: 'al_majid_glorious', arabicName: 'المَجِيدُ', transliteration: 'Al-Majid', englishName: 'The Glorious', category: 'jalal', aliasesArabic: ['المجيد'] },
  { nameId: 'al_baith', arabicName: 'البَاعِثُ', transliteration: "Al-Ba'ith", englishName: 'The Resurrector', category: 'afaal', aliasesArabic: ['الباعث'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'ash_shahid', arabicName: 'الشَّهِيدُ', transliteration: 'Ash-Shahid', englishName: 'The Witness', category: 'dhat', aliasesArabic: ['الشهيد'], warnings: ['"الشهيد" also means "the martyr" or "the witness"; reviewer must verify each occurrence as a divine name.'] },
  { nameId: 'al_haqq', arabicName: 'الحَقُّ', transliteration: 'Al-Haqq', englishName: 'The Truth', category: 'dhat', aliasesArabic: ['الحق'], warnings: ['"الحق" overwhelmingly means "the truth" as a noun; only some occurrences are divine-name usages. Reviewer must verify.'] },
  { nameId: 'al_wakil', arabicName: 'الوَكِيلُ', transliteration: 'Al-Wakil', englishName: 'The Trustee', category: 'jamal', aliasesArabic: ['الوكيل'] },
  { nameId: 'al_qawiyy', arabicName: 'القَوِيُّ', transliteration: 'Al-Qawiyy', englishName: 'The All-Strong', category: 'jalal', aliasesArabic: ['القوي'] },
  { nameId: 'al_matin', arabicName: 'المَتِينُ', transliteration: 'Al-Matin', englishName: 'The Firm', category: 'jalal', aliasesArabic: ['المتين'] },
  { nameId: 'al_waliyy', arabicName: 'الوَلِيُّ', transliteration: 'Al-Waliyy', englishName: 'The Protecting Friend', category: 'jamal', aliasesArabic: ['الولي'] },
  { nameId: 'al_hamid', arabicName: 'الحَمِيدُ', transliteration: 'Al-Hamid', englishName: 'The Praiseworthy', category: 'kamal', aliasesArabic: ['الحميد'] },
  { nameId: 'al_muhsi', arabicName: 'المُحْصِي', transliteration: 'Al-Muhsi', englishName: 'The Reckoner', category: 'dhat', aliasesArabic: ['المحصي'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_mubdi', arabicName: 'المُبْدِئُ', transliteration: 'Al-Mubdi', englishName: 'The Originator', category: 'afaal', aliasesArabic: ['المبدئ'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_muid', arabicName: 'المُعِيدُ', transliteration: "Al-Mu'id", englishName: 'The Restorer', category: 'afaal', aliasesArabic: ['المعيد'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_muhyi', arabicName: 'المُحْيِي', transliteration: 'Al-Muhyi', englishName: 'The Giver of Life', category: 'afaal', aliasesArabic: ['المحيي'] },
  { nameId: 'al_mumit', arabicName: 'المُمِيتُ', transliteration: 'Al-Mumit', englishName: 'The Taker of Life', category: 'afaal', aliasesArabic: ['المميت'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_hayy', arabicName: 'الحَيُّ', transliteration: 'Al-Hayy', englishName: 'The Ever-Living', category: 'dhat', aliasesArabic: ['الحي'] },
  { nameId: 'al_qayyum', arabicName: 'القَيُّومُ', transliteration: 'Al-Qayyum', englishName: 'The Self-Subsisting', category: 'dhat', aliasesArabic: ['القيوم'] },
  { nameId: 'al_wajid', arabicName: 'الوَاجِدُ', transliteration: 'Al-Wajid', englishName: 'The Finder', category: 'dhat', aliasesArabic: ['الواجد'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_majid_noble', arabicName: 'المَاجِدُ', transliteration: 'Al-Majid (Noble)', englishName: 'The Noble', category: 'jamal', aliasesArabic: ['الماجد'], warnings: ['Distinct from المَجِيدُ (al_majid_glorious); rarely used as an explicit divine-name lemma in Quran text.'] },
  { nameId: 'al_wahid', arabicName: 'الوَاحِدُ', transliteration: 'Al-Wahid', englishName: 'The One', category: 'dhat', aliasesArabic: ['الواحد'] },
  { nameId: 'al_ahad', arabicName: 'الأَحَدُ', transliteration: 'Al-Ahad', englishName: 'The Unique', category: 'dhat', aliasesArabic: ['الأحد', 'أحد'] },
  { nameId: 'as_samad', arabicName: 'الصَّمَدُ', transliteration: 'As-Samad', englishName: 'The Eternal Refuge', category: 'dhat', aliasesArabic: ['الصمد'] },
  { nameId: 'al_qadir', arabicName: 'القَادِرُ', transliteration: 'Al-Qadir', englishName: 'The Capable', category: 'jalal', aliasesArabic: ['القادر'] },
  { nameId: 'al_muqtadir', arabicName: 'المُقْتَدِرُ', transliteration: 'Al-Muqtadir', englishName: 'The All-Powerful', category: 'jalal', aliasesArabic: ['المقتدر'] },
  { nameId: 'al_muqaddim', arabicName: 'المُقَدِّمُ', transliteration: 'Al-Muqaddim', englishName: 'The Expediter', category: 'afaal', aliasesArabic: ['المقدم'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_muakhkhir', arabicName: 'المُؤَخِّرُ', transliteration: "Al-Mu'akhkhir", englishName: 'The Delayer', category: 'afaal', aliasesArabic: ['المؤخر'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_awwal', arabicName: 'الأَوَّلُ', transliteration: 'Al-Awwal', englishName: 'The First', category: 'dhat', aliasesArabic: ['الأول'], warnings: ['"الأول" most commonly means "the first" in general; only some occurrences are divine-name usages.'] },
  { nameId: 'al_akhir', arabicName: 'الآخِرُ', transliteration: 'Al-Akhir', englishName: 'The Last', category: 'dhat', aliasesArabic: ['الآخر'], warnings: ['"الآخر" most commonly means "the last/the next"; only some occurrences are divine-name usages.'] },
  { nameId: 'az_zahir', arabicName: 'الظَّاهِرُ', transliteration: 'Az-Zahir', englishName: 'The Manifest', category: 'dhat', aliasesArabic: ['الظاهر'] },
  { nameId: 'al_batin', arabicName: 'البَاطِنُ', transliteration: 'Al-Batin', englishName: 'The Hidden', category: 'dhat', aliasesArabic: ['الباطن'] },
  { nameId: 'al_wali', arabicName: 'الوَالِي', transliteration: 'Al-Wali', englishName: 'The Governor', category: 'jalal', aliasesArabic: ['الوالي'] },
  { nameId: 'al_mutaali', arabicName: 'المُتَعَالِي', transliteration: "Al-Muta'ali", englishName: 'The Most Exalted', category: 'dhat', aliasesArabic: ['المتعالي', 'المتعال'] },
  { nameId: 'al_barr', arabicName: 'البَرُّ', transliteration: 'Al-Barr', englishName: 'The Source of Goodness', category: 'jamal', aliasesArabic: ['البر'], warnings: ['"البر" also means "land" or "righteousness"; reviewer must verify divine-name usage.'] },
  { nameId: 'at_tawwab', arabicName: 'التَّوَّابُ', transliteration: 'At-Tawwab', englishName: 'The Accepter of Repentance', category: 'jamal', aliasesArabic: ['التواب'] },
  { nameId: 'al_muntaqim', arabicName: 'المُنْتَقِمُ', transliteration: 'Al-Muntaqim', englishName: 'The Avenger', category: 'jalal', aliasesArabic: ['المنتقم'] },
  { nameId: 'al_afuww', arabicName: 'العَفُوُّ', transliteration: 'Al-Afuww', englishName: 'The Pardoner', category: 'jamal', aliasesArabic: ['العفو'] },
  { nameId: 'ar_rauf', arabicName: 'الرَّؤُوفُ', transliteration: "Ar-Ra'uf", englishName: 'The Compassionate', category: 'jamal', aliasesArabic: ['الرؤوف', 'الرءوف'] },
  { nameId: 'malik_al_mulk', arabicName: 'مَالِكُ المُلْكِ', transliteration: 'Malik al-Mulk', englishName: 'The Owner of Sovereignty', category: 'jalal', aliasesArabic: ['مالك الملك'] },
  { nameId: 'dhul_jalali_wal_ikram', arabicName: 'ذُو الجَلَالِ وَالإِكْرَامِ', transliteration: 'Dhul-Jalali wal-Ikram', englishName: 'The Lord of Majesty and Bounty', category: 'kamal', aliasesArabic: ['ذو الجلال والإكرام', 'ذي الجلال والإكرام'] },
  { nameId: 'al_muqsit', arabicName: 'المُقْسِطُ', transliteration: 'Al-Muqsit', englishName: 'The Equitable', category: 'kamal', aliasesArabic: ['المقسط'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_jami', arabicName: 'الجَامِعُ', transliteration: 'Al-Jami', englishName: 'The Gatherer', category: 'afaal', aliasesArabic: ['الجامع'] },
  { nameId: 'al_ghaniyy', arabicName: 'الغَنِيُّ', transliteration: 'Al-Ghaniyy', englishName: 'The Self-Sufficient', category: 'dhat', aliasesArabic: ['الغني'] },
  { nameId: 'al_mughni', arabicName: 'المُغْنِي', transliteration: 'Al-Mughni', englishName: 'The Enricher', category: 'jamal', aliasesArabic: ['المغني'], warnings: ['Rarely used as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'al_mani', arabicName: 'المَانِعُ', transliteration: 'Al-Mani', englishName: 'The Withholder', category: 'afaal', aliasesArabic: ['المانع'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'ad_darr', arabicName: 'الضَّارُّ', transliteration: 'Ad-Darr', englishName: 'The Distressor', category: 'afaal', aliasesArabic: ['الضار'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'an_nafi', arabicName: 'النَّافِعُ', transliteration: 'An-Nafi', englishName: 'The Benefactor', category: 'afaal', aliasesArabic: ['النافع'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
  { nameId: 'an_nur', arabicName: 'النُّورُ', transliteration: 'An-Nur', englishName: 'The Light', category: 'jamal', aliasesArabic: ['النور'], warnings: ['"النور" most commonly means "light" as a noun; only some occurrences (e.g. 24:35) are divine-name usages.'] },
  { nameId: 'al_hadi', arabicName: 'الهَادِي', transliteration: 'Al-Hadi', englishName: 'The Guide', category: 'jamal', aliasesArabic: ['الهادي'] },
  { nameId: 'al_badi', arabicName: 'البَدِيعُ', transliteration: 'Al-Badi', englishName: 'The Originator', category: 'afaal', aliasesArabic: ['البديع'] },
  { nameId: 'al_baqi', arabicName: 'البَاقِي', transliteration: 'Al-Baqi', englishName: 'The Ever-Lasting', category: 'dhat', aliasesArabic: ['الباقي'], warnings: ['"الباقي" also means "what remains"; reviewer must verify divine-name usage.'] },
  { nameId: 'al_warith', arabicName: 'الوَارِثُ', transliteration: 'Al-Warith', englishName: 'The Inheritor', category: 'dhat', aliasesArabic: ['الوارث'] },
  { nameId: 'ar_rashid', arabicName: 'الرَّشِيدُ', transliteration: 'Ar-Rashid', englishName: 'The Guide to the Right Path', category: 'kamal', aliasesArabic: ['الرشيد'], warnings: ['"الرشيد" is also a personal name; reviewer must verify divine-name usage.'] },
  { nameId: 'as_sabur', arabicName: 'الصَّبُورُ', transliteration: 'As-Sabur', englishName: 'The Patient', category: 'kamal', aliasesArabic: ['الصبور'], warnings: ['Not in Quran as an explicit divine-name lemma; from hadith traditions.'] },
];

export function getAsmaSeedById(id: string): AsmaAllahSeed | undefined {
  return ASMA_ALLAH_SEEDS.find((s) => s.nameId === id);
}

export function getAsmaSeedsByCategory(cat: string): AsmaAllahSeed[] {
  return ASMA_ALLAH_SEEDS.filter((s) => s.category === cat);
}
