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
  | 'lexicon';           // Classical Arabic dictionaries and Quranic vocabulary works

export type ReliabilityLevel =
  | 'canonical'   // Mutawatir Quran text, or universally accepted scholarly work
  | 'verified'    // License confirmed, scholarly credentials established
  | 'supporting'  // Useful supplementary material; license pending or informal
  | 'experimental'; // Not yet validated for production display

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
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

export const SOURCE_REGISTRY: Source[] = [
  // === Quran Text ===
  {
    sourceId: 'quran_uthmani_cloud',
    titleArabic: 'المصحف العثماني',
    titleEnglish: 'Uthmani Quran Script',
    author: 'Provided by AlQuran.Cloud',
    language: 'ar',
    type: 'quran_text',
    reliabilityLevel: 'canonical',
    licenseOrTerms: 'Public domain — the text of the Quran is not subject to copyright',
    sourceUrl: 'https://api.alquran.cloud/v1/quran/quran-uthmani',
    lastVerifiedAt: '2026-01-02',
    notes: 'Uthmani rasm with full diacritics (tashkeel). Downloaded once and stored locally in data/raw/quran_uthmani.json. Never modify this file directly.',
  },
  {
    sourceId: 'quran_hafs_local',
    titleArabic: 'القرآن الكريم — برواية حفص',
    titleEnglish: 'Quran — Hafs Recitation (Local Backup)',
    author: 'Local copy',
    language: 'ar',
    type: 'quran_text',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'Public domain',
    sourceUrl: 'assets/hafs_smart_v8.json',
    lastVerifiedAt: 'unverified',
    notes: 'Backup copy. Use quran_uthmani_cloud as primary. Do not serve this without cross-checking against the primary. Marked supporting until independently verified against quran_uthmani_cloud.',
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
    licenseOrTerms: 'Creative Commons Attribution-NonCommercial-NoDerivatives 3.0 (CC BY-NC-ND 3.0). Non-commercial use only, no modifications, attribution required.',
    sourceUrl: 'https://tanzil.net/trans/en.sahih',
    lastVerifiedAt: '2026-01-02',
    notes: 'Primary English translation. Must be labeled as "Translation" in the UI — never displayed as Quran text itself. License prohibits commercial use.',
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
    licenseOrTerms: 'Public domain — classical text (d. 774 AH). Attribution required.',
    sourceUrl: 'https://api.quran-tafsir.com/tafsir/1',
    lastVerifiedAt: '2026-01-02',
    notes: 'Primary Arabic tafsir. Bil-mathur methodology (narration-based). Retrieved via quran-tafsir.com API, tafsir_id=1. Rate limit: 2 req/sec, 60 req/min.',
  },

  // === Tafsir (English) ===
  {
    sourceId: 'ibn_kathir_en',
    titleArabic: 'تفسير ابن كثير (إنجليزي)',
    titleEnglish: 'Tafsir Ibn Kathir (English)',
    author: 'Ismail ibn Umar ibn Kathir; English edition via quran-tafsir.com',
    language: 'en',
    type: 'tafsir',
    reliabilityLevel: 'verified',
    licenseOrTerms: 'API access — attribution required. Commercial use status: pending verification. Do not use commercially until confirmed.',
    sourceUrl: 'https://api.quran-tafsir.com/tafsir/169',
    lastVerifiedAt: '2026-01-02',
    notes: 'English translation of Ibn Kathir. tafsir_id=169. Commercial use requires explicit confirmation from API provider. Do not enable without license check.',
  },

  // === Tafsir (Pending Verification) ===
  {
    sourceId: 'al_muyassar_ar',
    titleArabic: 'التفسير الميسر',
    titleEnglish: 'Al-Muyassar (Simplified Arabic Tafsir)',
    author: 'King Fahd Complex for Printing the Holy Quran',
    language: 'ar',
    type: 'tafsir',
    reliabilityLevel: 'supporting',
    licenseOrTerms: 'License not yet confirmed. Requires permission from King Fahd Complex before use.',
    sourceUrl: 'https://api.quran-tafsir.com/tafsir/16',
    lastVerifiedAt: 'unverified',
    notes: 'DO NOT DISPLAY to users until license is verified. tafsir_id=16. Status: pending_user_input.',
  },
  {
    sourceId: 'tafheem_mawdudi_en',
    titleArabic: 'تفهيم القرآن (إنجليزي)',
    titleEnglish: 'Tafheem-ul-Quran (Mawdudi, English)',
    author: 'Sayyid Abul Ala Mawdudi',
    language: 'en',
    type: 'tafsir',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'License not yet confirmed. Status: pending_user_input.',
    sourceUrl: 'https://api.quran-tafsir.com/tafsir/95',
    lastVerifiedAt: 'unverified',
    notes: 'DO NOT DISPLAY to users until license is verified. tafsir_id=95.',
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
    licenseOrTerms: 'Public domain — 19th century work. No digital edition rights issues expected. Available at lane.quran.com.',
    sourceUrl: 'https://lane.quran.com',
    lastVerifiedAt: 'unverified',
    notes: 'DO NOT DISPLAY to users — no data integrated yet. The most comprehensive Arabic-English lexicon ever compiled — 8 volumes. Extensively cites Lisan Al-Arab and other classical sources. Standard English reference for Quranic Arabic.',
  },
  {
    sourceId: 'quranic_arabic_corpus',
    titleArabic: 'مدوّنة القرآن العربية',
    titleEnglish: 'Quranic Arabic Corpus (corpus.quran.com)',
    author: 'Kais Dukes, University of Leeds (2009–2011)',
    language: 'ar,en',
    type: 'lexicon',
    reliabilityLevel: 'experimental',
    licenseOrTerms: 'GNU General Public License (GPL). Open-source data available at corpus.quran.com.',
    sourceUrl: 'https://corpus.quran.com',
    lastVerifiedAt: 'unverified',
    notes: 'DO NOT DISPLAY to users — no data integrated yet. Word-by-word morphological and syntactic annotation of all 77,430 Quranic words. Modern digital resource; most permissive license among planned sources. Priority for morphology/root lookups.',
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
    notes: 'Per-ayah MP3 stream. URL pattern: https://verses.quran.com/Alafasy/mp3/{SSS}{AAA}.mp3 (zero-padded surah/ayah). Used by the Asmā\' Allah al-Ḥusnā page to recite the primary Quranic verse of each Name. Reciter name "Mishary Rashid Alafasy" must always be displayed in the player.',
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

export function isSourceSafeToDisplay(sourceId: string): boolean {
  const source = getSourceById(sourceId);
  if (!source) return false;
  return (
    source.reliabilityLevel === 'canonical' ||
    source.reliabilityLevel === 'verified'
  );
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
    if (source.reliabilityLevel === 'experimental' && !source.notes.includes('DO NOT DISPLAY')) {
      errors.push(`Source "${source.sourceId}": experimental sources must include "DO NOT DISPLAY" warning in notes`);
    }

    // Unverified sources should not be canonical
    if (source.lastVerifiedAt === 'unverified' && source.reliabilityLevel === 'canonical') {
      errors.push(`Source "${source.sourceId}": cannot be "canonical" with lastVerifiedAt="unverified"`);
    }
  }

  return errors;
}
