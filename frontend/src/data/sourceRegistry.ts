/**
 * Source Registry — Tadabbur Al-Quran
 *
 * Every content source used by this platform must have an entry here.
 * This registry is the single source of truth for source attribution
 * displayed to users and used in integrity validation.
 *
 * Do not add a source without filling all required fields.
 * Do not set reliabilityLevel to "canonical" without human verification.
 */

export type SourceType =
  | 'quran_text'
  | 'tafsir'
  | 'translation'
  | 'metadata'
  | 'audio'
  | 'internal_mapping'
  | 'lexicon'            // Classical Arabic dictionaries and Quranic vocabulary works
  | 'service';           // Third-party services the app calls (prayer times, maps)

export type ReliabilityLevel =
  | 'canonical'   // Mutawatir Quran text, or universally accepted scholarly work
  | 'verified'    // License confirmed, scholarly credentials established
  | 'supporting'  // Useful supplementary material; license pending or informal
  | 'experimental'; // Not yet validated for production display

/**
 * Licence clearance, tracked separately from scholarly reliability.
 *
 * A source can be scholarly impeccable and still be legally unshippable, so
 * reliabilityLevel alone must never decide whether something is displayed.
 */
export type LicenseStatus =
  | 'cleared'      // Terms confirmed at source and permit display in this product
  | 'restricted'   // Terms confirmed but limit use (non-commercial, no-derivatives, ...)
  | 'unverified'   // Terms could not be confirmed at source
  | 'blocked';     // Must not be shown to users until cleared

export interface Source {
  sourceId: string;
  titleArabic: string;
  titleEnglish: string;
  author: string;
  language: string;         // ISO 639-1 code: 'ar', 'en', 'ur', etc.
  type: SourceType;
  reliabilityLevel: ReliabilityLevel;
  licenseOrTerms: string;
  sourceUrl: string;
  lastVerifiedAt: string;   // ISO 8601 date string; 'unverified' if not yet checked
  notes: string;
  /**
   * Licence clearance, required on every entry (unknown terms are
   * 'unverified', never 'cleared'). A 'DO NOT DISPLAY' marker at the start of
   * `notes` also blocks display, whatever the status.
   */
  licenseStatus: LicenseStatus;
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

export const SOURCE_REGISTRY: Source[] = [
  // === Quran Text ===
  {
    sourceId: 'tanzil_quran_uthmani',
    titleArabic: 'نص القرآن الكريم — مشروع تنزيل (الرسم العثماني والإملائي)',
    titleEnglish: 'Tanzil Quran Text (Uthmani and Simple)',
    author: 'Tanzil Project',
    language: 'ar',
    type: 'quran_text',
    reliabilityLevel: 'canonical',
    licenseOrTerms: 'Creative Commons Attribution 3.0. Verbatim copies only, changing the text is not allowed. May be used in any website or application provided the source (Tanzil Project) is clearly indicated with a link to tanzil.net, and the copyright notice is kept in derived files.',
    sourceUrl: 'https://tanzil.net/download/',
    lastVerifiedAt: '2026-10-14',
    licenseStatus: 'cleared',
    notes: 'Canonical Qur\'an text since 2026-10-14. Verbatim Tanzil files (copyright blocks intact) in data/raw/tanzil/; data/raw/quran_tanzil.json is built from them by scripts/build_quran_tanzil.py and is what the database, API, generators and bundled data use. The opening Bismillah is kept apart from verse 1 as Tanzil gives it. Attribution with a link is shown wherever the text appears (QuranTextAttribution). Same letters as the previous KFGQPC text in every verse apart from encoding conventions (backend/tests/test_quran_text_source.py).',
  },
  {
    sourceId: 'quran_hafs_local',
    titleArabic: 'القرآن الكريم — برواية حفص',
    titleEnglish: 'Quran — Hafs Recitation (Local Backup)',
    author: 'Local copy',
    language: 'ar',
    type: 'quran_text',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Unverified. Derived from King Fahd Complex (KFGQPC) digital output; KFGQPC publishes no machine-readable licence and its servers refuse automated retrieval, so redistribution terms could not be confirmed.',
    sourceUrl: 'assets/hafs_smart_v8.json',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'NOT SERVED, SEEDED OR BUNDLED since 2026-10-14. assets/hafs_smart_v8.json and data/raw/quran_uthmani.json are byte-identical copies of this KFGQPC text (the latter was previously mislabelled as an alquran.cloud download). KFGQPC terms grant no redistribution, so the app switched to tanzil_quran_uthmani. Kept in the repository only as the cross-reference that proves the Tanzil text is the same Mushaf. The KFGQPC glyph fonts are not used (the app uses Scheherazade New, Amiri and Noto Naskh, all OFL).',
  },

  // === English Translations ===
  {
    sourceId: 'sahih_international',
    titleArabic: 'ترجمة صحيح إنترناشيونال',
    titleEnglish: 'Sahih International',
    author: 'Saheeh International (A. B. al-Mehri, et al.)',
    language: 'en',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'All rights reserved by the translator/publisher. Tanzil serves it for non-commercial purposes only, with permission from the translator or publisher required for any other use. Attribution required; no modifications.',
    sourceUrl: 'https://tanzil.net/trans/en.sahih',
    lastVerifiedAt: '2026-09-23',
    licenseStatus: 'restricted',
    notes: 'Not used at runtime since 2026-10-14. The reader shows quranenc_english_saheeh (the same work, published with a republication grant), and the en.sahih id used by RAG retrieval, the quiz and the tafsir defaults is answered from that licensed copy in the translations table (backend/app/services/tafseer_api.py LICENSED_DB_EDITIONS); nothing is fetched from Tanzil or alquran.cloud. Other English editions (Pickthall, Yusuf Ali, transliteration) are refused. Kept here for provenance of older citations.',
  },

  // === Translations of the meanings — QuranEnc.com (data/manifests/translation_sources.json) ===
  {
    sourceId: 'quranenc_english_saheeh',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'English Translation - Noor International Center',
    author: 'Saheeh International (Noor International Center)',
    language: 'en',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/english_saheeh',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=english_saheeh); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_english_rwwad',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'English Translation - Rowwad Translation Center',
    author: 'Rowwad Translation Center',
    language: 'en',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/english_rwwad',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=english_rwwad); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_english_hilali_khan',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'English Translation - Hilali and Khan',
    author: 'Muhammad Taqi-ud-Din al-Hilali and Muhammad Muhsin Khan',
    language: 'en',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/english_hilali_khan',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=english_hilali_khan); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_urdu_junagarhi',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Urdu Translation - Muhammad Junagarhi',
    author: 'Muhammad Junagarhi',
    language: 'ur',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/urdu_junagarhi',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=urdu_junagarhi); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_indonesian_affairs',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Indonesian Translation - Ministry of Religious Affairs',
    author: 'Ministry of Religious Affairs, Indonesia',
    language: 'id',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/indonesian_affairs',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=indonesian_affairs); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_turkish_rwwad',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Turkish Translation - Rowwad Translation Center',
    author: 'Rowwad Translation Center',
    language: 'tr',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/turkish_rwwad',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=turkish_rwwad); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_french_montada',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'French translation - Noor International Center',
    author: 'Noor International Center',
    language: 'fr',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/french_montada',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=french_montada); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_spanish_montada_eu',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Spanish Translation - Noor International Center',
    author: 'Noor International Center',
    language: 'es',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/spanish_montada_eu',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=spanish_montada_eu); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_german_bubenheim',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'German Translation - Frank Bubenheim',
    author: 'Frank Bubenheim and Nadeem Elyas',
    language: 'de',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/german_bubenheim',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=german_bubenheim); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_persian_ih',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Persian Translation - Rowwad Translation Center',
    author: 'Rowwad Translation Center',
    language: 'fa',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/persian_ih',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=persian_ih); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_hindi_omari',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Hindi Translation - Azizul Haq Al-Omari',
    author: 'Azizul Haq Al-Omari',
    language: 'hi',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/hindi_omari',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=hindi_omari); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_chinese_suliman',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Chinese Translation - Muhammad Suleiman',
    author: 'Muhammad Suleiman',
    language: 'zh',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/chinese_suliman',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=chinese_suliman); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_portuguese_nasr',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Portuguese Translation - Helmi Nasr',
    author: 'Helmi Nasr',
    language: 'pt',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/portuguese_nasr',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=portuguese_nasr); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_dutch_center',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Dutch Translation - Rowwad Translation Center',
    author: 'Rowwad Translation Center',
    language: 'nl',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/dutch_center',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=dutch_center); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_bosnian_rwwad',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Bosnian Translation - Rowwad Translation Centre',
    author: 'Rowwad Translation Center',
    language: 'bs',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/bosnian_rwwad',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=bosnian_rwwad); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_swahili_barawani',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Swahili Translation - Ali Mohsin Al-Barwani',
    author: 'Ali Mohsin Al-Barwani',
    language: 'sw',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/swahili_barawani',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=swahili_barawani); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_hausa_gummi',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Hausa Translation - Abu Bakr Jumi',
    author: 'Abu Bakr Mahmoud Gumi',
    language: 'ha',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/hausa_gummi',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=hausa_gummi); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_somali_yacob',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Somali Translation - Abdullah Hasan Yaqoub',
    author: 'Abdullah Hasan Yaqoub',
    language: 'so',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/somali_yacob',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=somali_yacob); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_tamil_baqavi',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Tamil Translation - Abdulhamid Baqawi',
    author: 'Abdulhamid Baqawi',
    language: 'ta',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/tamil_baqavi',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=tamil_baqavi); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_malayalam_kunhi',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Malayalam Translation - Abdul Hamid Haidar and Kunhi Muhammad',
    author: 'Abdul Hamid Haidar and Kunhi Muhammad',
    language: 'ml',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/malayalam_kunhi',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=malayalam_kunhi); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_uzbek_mansour',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Uzbek Translation - Alaauddin Mansour',
    author: 'Alauddin Mansour',
    language: 'uz',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/uzbek_mansour',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=uzbek_mansour); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },
  {
    sourceId: 'quranenc_japanese_saeedsato',
    titleArabic: 'ترجمة معاني القرآن الكريم — موسوعة القرآن الكريم',
    titleEnglish: 'Japanese Translation - Saeed Sato',
    author: 'Saeed Sato',
    language: 'ja',
    type: 'translation',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'QuranEnc.com republication terms: verbatim only (no modification, addition or deletion), publisher and QuranEnc.com credited, version number stated, footnotes kept, latest version tracked, no inappropriate advertising.',
    sourceUrl: 'https://quranenc.com/en/browse/japanese_saeedsato',
    lastVerifiedAt: '2026-10-13',
    licenseStatus: 'cleared',
    notes: 'Served from the translations table (translator=japanese_saeedsato); version recorded in translation_editions. Label as a translation of the meanings, show the version and QuranEnc.com, keep footnotes.',
  },

  // === Tafsir (Arabic) ===
  {
    sourceId: 'ibn_kathir_ar',
    titleArabic: 'تفسير ابن كثير',
    titleEnglish: 'Tafsir Ibn Kathir (Arabic)',
    author: 'Ismail ibn Umar ibn Kathir (d. 774 AH / 1373 CE)',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'canonical',
    licenseOrTerms: 'Public domain: classical text (d. 774 AH). Digital text from the riotu-lab/Quran-Tafseers dataset (Apache-2.0). Attribution required.',
    sourceUrl: 'https://huggingface.co/datasets/riotu-lab/Quran-Tafseers',
    lastVerifiedAt: '2026-10-15',
    licenseStatus: 'cleared',
    notes: 'Primary Arabic tafsir. Bil-mathur methodology (narration-based). Stored copy reseeded on 2026-10-15 from the Apache-2.0 Hugging Face dataset riotu-lab/Quran-Tafseers at pinned revision 9ddbdeec22bfabd9821b14c6584ad9587ed7bffa (SHA-256 checked) by backend/scripts/datasets/fetch_hf_tafseers.py and seed_tafseer.py --replace; it had previously been loaded from a spa5k CDN copy whose terms are not recorded. Ayat the dataset lacks have no stored passage and the reader says so.',
  },
  {
    sourceId: 'tabari_ar',
    titleArabic: 'جامع البيان عن تأويل آي القرآن (تفسير الطبري)',
    titleEnglish: 'Jami al-Bayan (Tafsir al-Tabari)',
    author: 'Muhammad ibn Jarir al-Tabari (d. 310 AH / 923 CE)',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'canonical',
    licenseOrTerms: 'Public domain: classical text (d. 310 AH). Digital text from the riotu-lab/Quran-Tafseers dataset (Apache-2.0). Attribution required.',
    sourceUrl: 'https://huggingface.co/datasets/riotu-lab/Quran-Tafseers',
    lastVerifiedAt: '2026-10-15',
    licenseStatus: 'cleared',
    notes: 'Earliest comprehensive narration-based tafsir. Stored copy reseeded on 2026-10-15 from the Apache-2.0 Hugging Face dataset riotu-lab/Quran-Tafseers at pinned revision 9ddbdeec22bfabd9821b14c6584ad9587ed7bffa (SHA-256 checked) by backend/scripts/datasets/fetch_hf_tafseers.py and seed_tafseer.py --replace; it had previously been loaded from a spa5k CDN copy whose terms are not recorded. Ayat the dataset lacks have no stored passage and the reader says so.',
  },
  {
    sourceId: 'qurtubi_ar',
    titleArabic: 'الجامع لأحكام القرآن (تفسير القرطبي)',
    titleEnglish: 'Al-Jami li-Ahkam al-Quran (Tafsir al-Qurtubi)',
    author: 'Muhammad ibn Ahmad al-Qurtubi (d. 671 AH / 1273 CE)',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'canonical',
    licenseOrTerms: 'Public domain: classical text (d. 671 AH). Digital text from the riotu-lab/Quran-Tafseers dataset (Apache-2.0). Attribution required.',
    sourceUrl: 'https://huggingface.co/datasets/riotu-lab/Quran-Tafseers',
    lastVerifiedAt: '2026-10-15',
    licenseStatus: 'cleared',
    notes: 'Jurisprudence-focused tafsir. Stored copy reseeded on 2026-10-15 from the Apache-2.0 Hugging Face dataset riotu-lab/Quran-Tafseers at pinned revision 9ddbdeec22bfabd9821b14c6584ad9587ed7bffa (SHA-256 checked) by backend/scripts/datasets/fetch_hf_tafseers.py and seed_tafseer.py --replace; it had previously been loaded from a spa5k CDN copy whose terms are not recorded. Ayat the dataset lacks have no stored passage and the reader says so.',
  },
  {
    sourceId: 'baghawi_ar',
    titleArabic: 'معالم التنزيل (تفسير البغوي)',
    titleEnglish: 'Ma\'alim al-Tanzil (Tafsir al-Baghawi)',
    author: 'Al-Husayn ibn Mas\'ud al-Baghawi (d. 516 AH / 1122 CE)',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'canonical',
    licenseOrTerms: 'Public domain: classical text (d. 516 AH). Digital text from the riotu-lab/Quran-Tafseers dataset (Apache-2.0). Attribution required.',
    sourceUrl: 'https://huggingface.co/datasets/riotu-lab/Quran-Tafseers',
    lastVerifiedAt: '2026-10-06',
    licenseStatus: 'cleared',
    notes: 'Narration-based tafsir. Seeded into tafseer_sources from the Apache-2.0 Hugging Face dataset riotu-lab/Quran-Tafseers at pinned revision 9ddbdeec22bfabd9821b14c6584ad9587ed7bffa (SHA-256 checked) by backend/scripts/datasets/fetch_hf_tafseers.py: 6,235 verse passages (none for 1:1). The reader tafsir panel serves it from that stored copy.',
  },
  {
    sourceId: 'asbab_wahidi',
    titleArabic: 'أسباب النزول (الواحدي)',
    titleEnglish: 'Asbab al-Nuzul (al-Wahidi)',
    author: 'Abu al-Hasan al-Wahidi (d. 468 AH / 1076 CE)',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Public domain: classical text (d. 468 AH). Digital edition via alquran.cloud (ar.wahidi). Attribution required.',
    sourceUrl: 'https://alquran.cloud/api',
    lastVerifiedAt: '2026-10-14',
    licenseStatus: 'cleared',
    notes: 'Served at /api/v1/quran/asbab/{surah}. Licence assessed on the author\'s death date; the digital edition has not been proof-read against a printed edition.',
  },

  // === Tafsir (English) ===
  {
    sourceId: 'ibn_kathir_en',
    titleArabic: 'تفسير ابن كثير (إنجليزي)',
    titleEnglish: 'Tafsir Ibn Kathir (English)',
    author: 'Ismail ibn Umar ibn Kathir; modern English abridgement (Darussalam)',
    language: 'en',
    type: 'tafsir',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Modern English translation under copyright; publisher permission not obtained. Not public domain.',
    sourceUrl: 'https://api.quran-tafsir.com/tafsir/169',
    lastVerifiedAt: '2026-10-14',
    licenseStatus: 'blocked',
    notes: 'DO NOT DISPLAY. Disabled in tafseer_sources (alembic ws3a1b2c3d4e5) and no longer proxied from Quran.com (tafsir_id=169). It was seeded as "public domain" by mistake: the age of the Arabic original does not cover a modern translation.',
  },
  {
    sourceId: 'jalalayn_en',
    titleArabic: 'تفسير الجلالين (إنجليزي)',
    titleEnglish: 'Tafsir al-Jalalayn (English)',
    author: 'Al-Mahalli and al-Suyuti; English translation by Feras Hamza (Royal Aal al-Bayt Institute)',
    language: 'en',
    type: 'tafsir',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Modern English translation under copyright; permission from the Royal Aal al-Bayt Institute not obtained.',
    sourceUrl: 'https://www.altafsir.com',
    lastVerifiedAt: '2026-10-14',
    licenseStatus: 'blocked',
    notes: 'DO NOT DISPLAY. Disabled in tafseer_sources (alembic ws3a1b2c3d4e5). Seeded from the spa5k CDN as "public domain" by mistake.',
  },

  // === Tafsir (Pending Verification: licence on hold) ===
  {
    sourceId: 'muyassar_ar',
    titleArabic: 'التفسير الميسر',
    titleEnglish: 'Al-Muyassar (Simplified Arabic Tafsir)',
    author: 'King Fahd Complex for Printing the Holy Quran',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'King Fahd Complex (KFGQPC) publication. The KFGQPC terms are pending owner confirmation; not cleared. Not served while they are unconfirmed (interim hold).',
    sourceUrl: 'https://qurancomplex.gov.sa',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified', // KFGQPC terms pending owner confirmation: never 'cleared' or 'restricted' until confirmed
    notes: 'Interim hold since 2026-10-16: license_verified=0 in tafseer_sources (alembic r5c1a2b3c4d5) and listed in licence_hold_ids in data/manifests/tafseer_sources.json (status pending_owner_confirmation). The row and stored text are kept, but the reader, the Mushaf tafsir sheet, /tafseer/compare, the AI tafsir assistant, RAG citations and story/theme evidence do not serve it, and the reader default is Tafsir al-Baghawi. The owner\'s 2026-10-14 note (attributed, non-commercial display under docs/distribution-policy.md, since Tadabbur is free with no ads, purchases, subscriptions or paid tiers) did not confirm the KFGQPC terms; qurancomplex.gov.sa refuses automated retrieval, so the terms were not read at source. Final decision queued for the owner (data/review/owner_review_queue.json, legal-muyassar-and-audio-licences): confirm the KFGQPC terms in writing, or switch to QuranEnc arabic_moyassar. Stored text: spa5k tafsir_api CDN (ar-tafsir-muyassar), identical to riotu-lab/Quran-Tafseers at the pinned revision for all 6,235 verses that dataset carries.',
  },
  {
    sourceId: 'mukhtasar_en',
    titleArabic: 'المختصر في التفسير (إنجليزي)',
    titleEnglish: 'Al-Mukhtasar fi al-Tafsir (English)',
    author: 'Tafsir Center for Quranic Studies (English edition, via QuranEnc.com)',
    language: 'en',
    type: 'tafsir',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'QuranEnc.com republication terms (verbatim, credit publisher and QuranEnc.com, state the version). Coverage of this tafsir key pending confirmation from QuranEnc.',
    sourceUrl: 'https://quranenc.com',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'Seeded by backend/scripts/ingest/seed_tafsir_quranenc.py with license_verified=0 and is_enabled=0; also gated by FEATURE_MUKHTASAR_EN. Enable only after the owner records QuranEnc confirmation in data/manifests/tafseer_sources.json.',
  },
  {
    sourceId: 'mukhtasar_ar',
    titleArabic: 'المختصر في التفسير',
    titleEnglish: 'Al-Mukhtasar fi al-Tafsir',
    author: 'Tafsir Center for Quranic Studies (via QuranEnc.com)',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'QuranEnc.com republication terms (verbatim, credit publisher and QuranEnc.com, state the version). Coverage of this tafsir key pending confirmation from QuranEnc.',
    sourceUrl: 'https://quranenc.com',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'Seeded by backend/scripts/ingest/seed_tafsir_quranenc.py with license_verified=0 and is_enabled=0 until the owner records QuranEnc confirmation.',
  },
  {
    sourceId: 'tafheem_mawdudi_en',
    titleArabic: 'تفهيم القرآن (إنجليزي)',
    titleEnglish: 'Tafheem-ul-Quran (Mawdudi, English)',
    author: 'Sayyid Abul Ala Mawdudi',
    language: 'en',
    type: 'tafsir',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'All rights reserved. Tafhim-ul-Quran is actively published in English by Kube Publishing / The Islamic Foundation, which maintains a rights and permissions process. Not redistributable without written permission.',
    sourceUrl: 'https://api.quran-tafsir.com/tafsir/95',
    lastVerifiedAt: '2026-09-23',
    licenseStatus: 'blocked',
    notes: 'DO NOT DISPLAY to users until license is verified. tafsir_id=95. Assessed 2026-09-23: confirmed under active commercial copyright (Mawdudi d. 1979); the English edition is sold by Kube Publishing. Requires written permission from the publisher, not merely from the API provider.',
  },

  // === Metadata & Internal Mappings ===
  {
    sourceId: 'stories_manifest',
    titleArabic: 'مخطوطة القصص القرآنية',
    titleEnglish: 'Quranic Stories Manifest',
    author: 'Tadabbur Editorial Team',
    language: 'ar,en',
    type: 'internal_mapping',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'Original research — internal use. All verse references must be cross-checked with Quran text.',
    sourceUrl: 'data/manifests/stories.json',
    lastVerifiedAt: '2026-01-02',
    licenseStatus: 'cleared', // the project's own editorial data
    notes: '122+ curated stories with verse references and tafsir chunk IDs as evidence. No AI-generated content.',
  },
  {
    sourceId: 'concepts_dictionary',
    titleArabic: 'معجم المفاهيم القرآنية',
    titleEnglish: 'Quranic Concepts Dictionary',
    author: 'Tadabbur Editorial Team',
    language: 'ar,en',
    type: 'internal_mapping',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'Original research — internal use.',
    sourceUrl: 'data/concepts/curated_concepts.json',
    lastVerifiedAt: '2026-01-02',
    licenseStatus: 'cleared', // the project's own editorial data
    notes: 'Curated dictionary of Quranic persons, events, places, and attributes. Descriptions are brief and non-interpretive.',
  },
  {
    sourceId: 'themes_taxonomy',
    titleArabic: 'تصنيف المحاور القرآنية',
    titleEnglish: 'Quranic Themes Taxonomy',
    author: 'Tadabbur Editorial Team',
    language: 'ar,en',
    type: 'internal_mapping',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'Original research — internal use. Methodology: Sunni Orthodox (4 madhabs).',
    sourceUrl: 'backend/app/data/themes/quranic_themes.json',
    lastVerifiedAt: '2026-01-02',
    licenseStatus: 'cleared', // the project's own editorial data
    notes: 'Hierarchical theme taxonomy. Each theme links to tafsir sources for evidence.',
  },

  // === Vocabulary (Planned — Phase F) ===
  {
    sourceId: 'vocabulary_planned',
    titleArabic: 'غريب القرآن — المعجم المخطط',
    titleEnglish: 'Quranic Vocabulary Module (Planned)',
    author: 'Pending — planned sources: Lisan Al-Arab, Mufradat Al-Raghib',
    language: 'ar',
    type: 'internal_mapping',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'License not yet confirmed. Requires human verification of each source before use.',
    sourceUrl: '/api/v1/vocabulary/status',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'DO NOT DISPLAY to users. Placeholder for Phase F vocabulary module. No verified word-level data integrated yet. See docs/quran-vocabulary-module-plan.md.',
  },

  // === Lexicons — Classical Arabic (Planned — Phase F) ===
  {
    sourceId: 'gharib_al_quran_ibn_qutaybah',
    titleArabic: 'غريب القرآن',
    titleEnglish: "Ibn Qutayba's Gharib Al-Quran",
    author: "Abu Muhammad ibn Qutayba al-Dinawari (d. 276 AH / 889 CE)",
    language: 'ar',
    type: 'lexicon',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'Public domain — classical text (d. 276 AH). No modern edition rights established.',
    sourceUrl: 'https://shamela.ws/book/11388',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified', // classical work; digital edition terms not verified
    notes: 'DO NOT DISPLAY to users — no data integrated yet. The earliest specialized work on rare and unusual Quranic vocabulary. Foundational Sunni reference. Era: 3rd century AH. Requires license verification for the specific digital edition before use.',
  },
  {
    sourceId: 'mufradat_al_raghib',
    titleArabic: 'مفردات ألفاظ القرآن',
    titleEnglish: 'Mufradat Al-Raghib Al-Isfahani',
    author: 'Abu al-Qasim al-Raghib al-Isfahani (d. 502 AH / 1108 CE)',
    language: 'ar',
    type: 'lexicon',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'Public domain — classical text (d. 502 AH). No modern edition rights established.',
    sourceUrl: 'https://shamela.ws/book/1655',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified', // classical work; digital edition terms not verified
    notes: 'DO NOT DISPLAY to users — no data integrated yet. The most cited specialized lexicon of Quranic terminology and vocabulary. Used by all major Sunni tafsir scholars. Era: 5th century AH. Priority source for Phase F integration.',
  },
  {
    sourceId: 'lisan_al_arab',
    titleArabic: 'لسان العرب',
    titleEnglish: 'Lisan Al-Arab (Ibn Manzur)',
    author: 'Jamal al-Din Muhammad ibn Manzur (d. 711 AH / 1311 CE)',
    language: 'ar',
    type: 'lexicon',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'Public domain — classical text (d. 711 AH). Digital edition rights require verification.',
    sourceUrl: 'https://shamela.ws/book/891',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified', // classical work; digital edition terms not verified
    notes: 'DO NOT DISPLAY to users — no data integrated yet. The largest classical Arabic dictionary — 20 volumes with extensive Quranic and poetic citations. Authoritative Sunni reference. Era: 7th century AH.',
  },
  {
    sourceId: 'qamus_al_muhit',
    titleArabic: 'القاموس المحيط',
    titleEnglish: 'Al-Qamus Al-Muhit (Al-Fayruzabadi)',
    author: 'Majd al-Din Muhammad al-Fayruzabadi (d. 817 AH / 1414 CE)',
    language: 'ar',
    type: 'lexicon',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'Public domain — classical text (d. 817 AH). Digital edition rights require verification.',
    sourceUrl: 'https://shamela.ws/book/819',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified', // classical work; digital edition terms not verified
    notes: 'DO NOT DISPLAY to users — no data integrated yet. Comprehensive classical Arabic lexicon widely used in Sunni scholarship. Era: 9th century AH.',
  },
  {
    sourceId: 'al_nihaya_ibn_al_athir',
    titleArabic: 'النهاية في غريب الحديث والأثر',
    titleEnglish: "Al-Nihaya fi Gharib Al-Hadith (Ibn Al-Athir)",
    author: "Abu al-Sa'adat Mubarak ibn Al-Athir al-Jazari (d. 606 AH / 1209 CE)",
    language: 'ar',
    type: 'lexicon',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'Public domain — classical text (d. 606 AH). Digital edition rights require verification.',
    sourceUrl: 'https://shamela.ws/book/11341',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified', // classical work; digital edition terms not verified
    notes: 'DO NOT DISPLAY to users — no data integrated yet. Covers rare and unusual words in Hadith narrations and the Quran. Major Sunni reference for Arabic lexicography. Era: 6th century AH.',
  },
  {
    sourceId: 'lanes_lexicon',
    titleArabic: 'معجم لين العربي الإنجليزي',
    titleEnglish: "Lane's Arabic-English Lexicon",
    author: 'Edward William Lane (d. 1876 CE)',
    language: 'en',
    type: 'lexicon',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'Public domain — compiled 1863-1893, Lane d. 1876. No digital edition rights expected for the original text.',
    sourceUrl: 'https://archive.org/details/ArabicEnglishLexicon.CopiousEasternSources',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified', // public-domain print work; no digital edition chosen or verified
    notes: 'DO NOT DISPLAY to users — no data integrated yet. The most comprehensive Arabic-English lexicon ever compiled — 8 volumes. Extensively cites Lisan Al-Arab and other classical sources. Standard English reference for Quranic Arabic. Registry corrected 2026-09-23: the previous sourceUrl (lane.quran.com) no longer resolves, and laneslexicon.org is also down. Two further caveats before integration — no structured JSON edition of Lane is known to exist, and Lane died at the letter qaf, so volumes VI-VIII are posthumous and materially incomplete.',
  },
  {
    sourceId: 'quranic_arabic_corpus',
    titleArabic: 'مدوّنة القرآن العربية',
    titleEnglish: 'Quranic Arabic Corpus (corpus.quran.com)',
    author: 'Kais Dukes, University of Leeds (2009–2011)',
    language: 'ar,en',
    type: 'lexicon',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'GNU General Public License (GPL), with the same verbatim-only clause as Tanzil: copies may be distributed but the annotation data may not be changed. Attribution and a link to corpus.quran.com required. (c) Kais Dukes.',
    sourceUrl: 'https://corpus.quran.com',
    lastVerifiedAt: '2026-09-23',
    licenseStatus: 'restricted',
    notes: 'INTEGRATED AND LIVE. All 77,430 QAC v0.4 words are seeded and served via /api/v1/vocabulary (see backend/app/api/routes/vocabulary.py). Registry corrected 2026-09-23 — this entry previously carried a display block and claimed no data was integrated, which had been false since the Phase H vocabulary seeding. Constraint to respect: the no-modification clause means any normalised or derived form of the morphology must be stored alongside, not in place of, the verbatim original. Upstream is frozen (last release v0.4) and its syntactic layer covers only part of the Quran; EQTB (CC BY 4.0, complete) is the intended successor.',
  },

  // === Surah Atlas Metadata (Makki/Madani, English meanings) ===
  {
    sourceId: 'surah_atlas_metadata',
    titleArabic: 'بيانات أطلس السور — تصنيف مكي/مدني والمعاني',
    titleEnglish: 'Surah Atlas Metadata — Makki/Madani Classification and English Meanings',
    author: 'Curated from Al-Suyuti (Al-Itqan fi Ulum al-Quran) and standard Islamic scholarship',
    language: 'ar,en',
    type: 'metadata',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Curated internal dataset — based on classical Islamic scholarship (public domain). Requires human scholarly review before canonical use.',
    sourceUrl: 'internal://scripts/build-surah-memory-atlas.ts',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'cleared', // the project's own curated dataset (needs scholarly review, not a licence)
    notes: 'Makki/Madani classification derived from Al-Itqan fi Ulum al-Quran (Al-Suyuti). 7 disputed surahs marked revelationType:unknown. English surah meanings from standard scholarly consensus. ALL entries generated from this source must display a needs_review badge. Do not display as verified without human scholar review.',
  },

  // === Audio ===
  {
    sourceId: 'quran_audio_cdn',
    titleArabic: 'تلاوات القرآن الكريم',
    titleEnglish: 'Quran Audio Recitations',
    author: 'Various certified reciters (served via backend audio API)',
    language: 'ar',
    type: 'audio',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'Per-reciter terms. Attribution of reciter name required in UI.',
    sourceUrl: '/api/v1/quran/audio/',
    lastVerifiedAt: '2026-01-02',
    licenseStatus: 'unverified', // per-reciter terms not recorded
    notes: 'Audio served via CDN URLs. Reciter name must always be displayed. License terms vary per reciter.',
  },
  {
    sourceId: 'quran_com_verse_audio',
    titleArabic: 'تلاوات الآيات — قرآن دوت كوم (مشاري العفاسي)',
    titleEnglish: 'Per-Verse Quran Recitations — Quran.com CDN (Mishary Alafasy)',
    author: 'Mishary Rashid Alafasy (via verses.quran.com / BunnyCDN)',
    language: 'ar',
    type: 'audio',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'Served by Quran.com (Quran Foundation). Reciter attribution required. See https://quran.com for terms.',
    sourceUrl: 'https://verses.quran.com/Alafasy/mp3/',
    lastVerifiedAt: '2026-05-17',
    licenseStatus: 'unverified', // Quran.com streaming terms not recorded
    notes: 'Per-ayah MP3 stream. URL pattern: https://verses.quran.com/Alafasy/mp3/{SSS}{AAA}.mp3 (zero-padded surah/ayah). Used by the Asmā\' Allah al-Ḥusnā page to recite the primary Quranic verse of each Name. Reciter name "Mishary Rashid Alafasy" must always be displayed in the player.',
  },

  {
    sourceId: 'everyayah_audio',
    titleArabic: 'تلاوات الآيات — EveryAyah',
    titleEnglish: 'Per-verse recitations — EveryAyah',
    author: 'everyayah.com (reciter recordings)',
    language: 'ar',
    type: 'audio',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Free public recordings; streaming and offline-caching terms not yet confirmed with the site.',
    sourceUrl: 'https://everyayah.com',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'Primary per-verse audio host in backend/app/services/audio_service.py (EVERYAYAH_BASE). Reciter name shown in the player. Terms pending owner confirmation.',
  },
  {
    sourceId: 'islamic_network_audio',
    titleArabic: 'تلاوات — شبكة Islamic Network',
    titleEnglish: 'Recitations — Islamic Network CDN',
    author: 'cdn.islamic.network (alquran.cloud)',
    language: 'ar',
    type: 'audio',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Free public CDN; redistribution terms not yet confirmed.',
    sourceUrl: 'https://alquran.cloud/cdn',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'Fallback audio host in backend/app/services/audio_service.py (ALQURAN_CLOUD_BASE). Terms pending owner confirmation.',
  },
  {
    sourceId: 'quranicaudio_audio',
    titleArabic: 'تلاوات السور — QuranicAudio',
    titleEnglish: 'Surah recitations — QuranicAudio',
    author: 'download.quranicaudio.com',
    language: 'ar',
    type: 'audio',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Free public recordings; redistribution terms not yet confirmed.',
    sourceUrl: 'https://quranicaudio.com',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'Surah-level audio host in backend/app/services/audio_service.py (QURANICAUDIO_BASE). Terms pending owner confirmation.',
  },

  // === Third-party services ===
  {
    sourceId: 'aladhan_api',
    titleArabic: 'مواقيت الصلاة والتقويم الهجري — AlAdhan',
    titleEnglish: 'Prayer times and Hijri calendar — AlAdhan',
    author: 'AlAdhan (api.aladhan.com)',
    language: 'ar,en',
    type: 'service',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Public API. Receives the location or city you enter; nothing is sent to our server.',
    sourceUrl: 'https://aladhan.com/prayer-times-api',
    lastVerifiedAt: 'unverified',
    licenseStatus: 'unverified',
    notes: 'Called from the browser by frontend/src/lib/islamicApis.ts (prayer times, Hijri date conversion). See the privacy page.',
  },
  {
    sourceId: 'openstreetmap',
    titleArabic: 'الخرائط وأسماء الأماكن — OpenStreetMap',
    titleEnglish: 'Maps and place names — OpenStreetMap',
    author: 'OpenStreetMap contributors (Nominatim, Overpass)',
    language: 'ar,en',
    type: 'service',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Map data © OpenStreetMap contributors, Open Database License (ODbL). Attribution required.',
    sourceUrl: 'https://www.openstreetmap.org/copyright',
    lastVerifiedAt: '2026-10-14',
    licenseStatus: 'cleared',
    notes: 'Place search and mosque finder. Receives your location from the browser; nothing is sent to our server.',
  },

  // === Asmā' Allah al-Ḥusnā — Tirmidhi list reference (curated) ===
  {
    sourceId: 'tirmidhi_asma_husna_list',
    titleArabic: 'قائمة أسماء الله الحسنى — جامع الترمذي ٣٥٠٧',
    titleEnglish: "Asmā' Allah al-Ḥusnā — Jāmiʿ al-Tirmidhī 3507 (curated)",
    author: 'Narrated by al-Walīd ibn Muslim, collected by al-Tirmidhī; curated mapping verified via Wikipedia and Quran.com',
    language: 'ar,en',
    type: 'internal_mapping',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Curated reference list — based on the widely-attested Tirmidhi 99 Names list (public-tradition scholarship). The hadith is graded ḍaʿīf by some scholars; the list is universally taught for memorisation. Each Name→ayah mapping requires reviewer-verification before display as "verified".',
    sourceUrl: 'https://en.wikipedia.org/wiki/Names_of_God_in_Islam',
    lastVerifiedAt: '2026-05-17',
    licenseStatus: 'unverified', // curated mapping; reference terms not recorded
    notes: 'Provides each Name\'s primary Quranic verse references (surah:ayah). NOT a substitute for the corpus-derived occurrence count — these are the verses scholars cite as the canonical reference for each Name, regardless of how many times the lemma appears in the Quran. All entries flagged needs_review until a human reviewer verifies.',
  },
];

// ---------------------------------------------------------------------------
// Lookup helpers
// ---------------------------------------------------------------------------

export function getSourceById(sourceId: string): Source | undefined {
  return SOURCE_REGISTRY.find((s) => s.sourceId === sourceId);
}

export function getSourcesByType(type: SourceType): Source[] {
  return SOURCE_REGISTRY.filter((s) => s.type === type);
}

export function getVerifiedSources(): Source[] {
  return SOURCE_REGISTRY.filter(
    (s) => s.reliabilityLevel === 'canonical' || s.reliabilityLevel === 'verified'
  );
}

/**
 * True when a source must not be rendered to users.
 *
 * An explicit licence block, or a 'DO NOT DISPLAY' marker in notes, overrides
 * every other signal. The notes marker blocks entries whose terms may be
 * fine but that have no data integrated yet (the planned lexicons).
 *
 * 'unverified' deliberately does NOT block. Unconfirmed terms are a deployment
 * risk to resolve before shipping publicly, not a reason to blank the reader —
 * they surface as the "unverified" badge in SourceAttribution instead.
 */
export const DISPLAY_BLOCK_MARKER = 'DO NOT DISPLAY';

export function isSourceDisplayBlocked(source: Source): boolean {
  if (source.licenseStatus === 'blocked') return true;
  // Anchored to the start of `notes` on purpose: an unanchored substring match
  // also fires on prose that merely refers to the marker.
  return source.notes.trimStart().startsWith(DISPLAY_BLOCK_MARKER);
}

/**
 * Display gate for content attribution.
 *
 * Gates on licence clearance first, then scholarly reliability. An unknown
 * sourceId is never displayable — an unregistered source is an unattributable
 * one, which the content policy forbids.
 *
 * 'supporting' is displayable: it is the level used for scholarly material
 * whose licence is informal rather than absent, and it is what the production
 * tafsir defaults sit at.
 */
export function isSourceSafeToDisplay(sourceId: string): boolean {
  const source = getSourceById(sourceId);
  if (!source) return false;
  if (isSourceDisplayBlocked(source)) return false;
  return (
    source.reliabilityLevel === 'canonical' ||
    source.reliabilityLevel === 'verified' ||
    source.reliabilityLevel === 'supporting'
  );
}

/** Every registry entry currently blocked from display, for admin/audit views. */
export function getDisplayBlockedSources(): Source[] {
  return SOURCE_REGISTRY.filter(isSourceDisplayBlocked);
}

// ---------------------------------------------------------------------------
// Validation (used by tests and integrity checks)
// ---------------------------------------------------------------------------

export const REQUIRED_SOURCE_FIELDS: (keyof Source)[] = [
  'sourceId',
  'titleArabic',
  'titleEnglish',
  'author',
  'language',
  'type',
  'reliabilityLevel',
  'licenseOrTerms',
  'sourceUrl',
  'lastVerifiedAt',
  'notes',
];

export function validateSourceRegistry(registry: Source[]): string[] {
  const errors: string[] = [];
  const seenIds = new Set<string>();

  for (const source of registry) {
    // Check required fields
    for (const field of REQUIRED_SOURCE_FIELDS) {
      if (!source[field] || String(source[field]).trim() === '') {
        errors.push(`Source "${source.sourceId || 'UNKNOWN'}": missing required field "${field}"`);
      }
    }

    // Check for duplicate IDs
    if (seenIds.has(source.sourceId)) {
      errors.push(`Duplicate sourceId: "${source.sourceId}"`);
    }
    seenIds.add(source.sourceId);

    // Experimental sources must have a warning in notes
    if (source.reliabilityLevel === 'experimental' && !isSourceDisplayBlocked(source)) {
      errors.push(`Source "${source.sourceId}": experimental sources must open notes with "${DISPLAY_BLOCK_MARKER}" or set licenseStatus="blocked"`);
    }

    // Unverified sources should not be canonical
    if (source.lastVerifiedAt === 'unverified' && source.reliabilityLevel === 'canonical') {
      errors.push(`Source "${source.sourceId}": cannot be "canonical" with lastVerifiedAt="unverified"`);
    }

    // A cleared licence and an active display block cannot both be true
    if (source.licenseStatus === 'cleared' && isSourceDisplayBlocked(source)) {
      errors.push(`Source "${source.sourceId}": licenseStatus="cleared" contradicts its display block`);
    }

    // The marker only takes effect at the start of notes; anywhere else it is
    // inert prose and would give a false sense of being enforced.
    if (
      source.notes.includes(DISPLAY_BLOCK_MARKER) &&
      !source.notes.trimStart().startsWith(DISPLAY_BLOCK_MARKER) &&
      source.licenseStatus !== 'blocked'
    ) {
      errors.push(
        `Source "${source.sourceId}": "${DISPLAY_BLOCK_MARKER}" appears mid-note and is not enforced. ` +
        `Move it to the start of notes, or set licenseStatus="blocked".`,
      );
    }

    // Experimental sources must be blocked at the licence layer too, not just by note
    if (source.reliabilityLevel === 'experimental' && source.licenseStatus === 'cleared') {
      errors.push(`Source "${source.sourceId}": experimental sources cannot have licenseStatus="cleared"`);
    }
  }

  return errors;
}
