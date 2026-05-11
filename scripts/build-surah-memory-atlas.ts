/**
 * Build Surah Memory Atlas
 *
 * Generates frontend/src/data/generated/surahMemoryAtlas.json
 * from data/raw/quran_uthmani.json (the only trusted Quran text source).
 * Also loads data/manifests/stories.json to populate relatedStories per surah.
 *
 * Safety rules:
 * - All ayah text is loaded from quran_uthmani.json only — never hardcoded
 * - Makki/Madani is from curated scholarly metadata (Al-Suyuti) — marked needs_review
 * - English meanings are from curated scholarly metadata — marked needs_review
 * - Topics and memory clues are NOT generated — marked missing_metadata
 * - Page/juz data is from quran_uthmani.json — trusted
 * - Story IDs and names are from stories.json — factual manifest data
 *
 * Usage:
 *   npx tsx scripts/build-surah-memory-atlas.ts
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const QURAN_PATH = join(ROOT, 'data/raw/quran_uthmani.json');
const STORIES_PATH = join(ROOT, 'data/manifests/stories.json');
const OUTPUT_JSON = join(ROOT, 'frontend/src/data/generated/surahMemoryAtlas.json');
const OUTPUT_MD = join(ROOT, 'docs/generated/surah-memory-atlas-summary.md');

// ---------------------------------------------------------------------------
// Types (local, matching SurahMemoryItem in types/surahMemoryAtlas.ts)
// ---------------------------------------------------------------------------

type RevelationType = 'makki' | 'madani' | 'unknown';
type LengthCategory = 'short' | 'medium' | 'long' | 'very_long';
type QuranPosition = 'beginning' | 'early' | 'middle' | 'late' | 'ending';
type ReviewStatus = 'verified' | 'needs_review' | 'missing_metadata';

interface SurahMemoryItem {
  surahNumber: number;
  nameArabic: string;
  nameTransliteration: string;
  nameEnglish?: string;
  revelationType: RevelationType;
  ayahCount: number;
  lengthCategory: LengthCategory;
  quranPosition: QuranPosition;
  juzStart: number;
  juzEnd: number;
  pageStart: number;
  pageEnd: number;
  firstAyahRef: string;
  secondAyahRef?: string;
  midAyah1Ref?: string;
  midAyah2Ref?: string;
  prevLastAyahRef?: string;
  lastAyahRef: string;
  firstAyahPreview?: string;
  secondAyahPreview?: string;
  midAyah1Preview?: string;
  midAyah2Preview?: string;
  prevLastAyahPreview?: string;
  lastAyahPreview?: string;
  mainTopicsArabic: string[];
  mainTopicsEnglish: string[];
  memoryClueArabic?: string;
  memoryClueEnglish?: string;
  relatedStories: string[];
  relatedThemes: string[];
  mainFigures: string[];
  sourceIds: string[];
  reviewStatus: ReviewStatus;
}

interface QuranAyah {
  id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  aya_text: string;
  aya_text_emlaey: string;
  page: number;
  jozz: number;
  line_start: number | null;
  line_end: number | null;
}

interface StoryEntry {
  id: string;
  name_ar?: string;
  name_en?: string;
  themes?: string[];
  main_figures?: string[];
  suras_mentioned?: number[];
  segments?: Array<{ sura_no?: number }>;
}

// ---------------------------------------------------------------------------
// Curated Makki/Madani classification
// Source: Al-Itqan fi Ulum al-Quran (Al-Suyuti, d. 911 AH)
// Standard scholarly consensus — disputed surahs marked unknown
// All marked needs_review — requires human scholarly verification
// ---------------------------------------------------------------------------

const REVELATION_TYPE: Record<number, RevelationType> = {
  // Makki surahs (revealed before Hijra, primarily in Mecca)
  1: 'makki', 6: 'makki', 7: 'makki', 10: 'makki', 11: 'makki',
  12: 'makki', 14: 'makki', 15: 'makki', 17: 'makki', 18: 'makki',
  19: 'makki', 20: 'makki', 21: 'makki', 23: 'makki', 25: 'makki',
  26: 'makki', 27: 'makki', 28: 'makki', 34: 'makki', 35: 'makki',
  36: 'makki', 37: 'makki', 38: 'makki', 40: 'makki', 41: 'makki',
  43: 'makki', 44: 'makki', 45: 'makki', 46: 'makki', 50: 'makki',
  51: 'makki', 52: 'makki', 53: 'makki', 54: 'makki', 56: 'makki',
  67: 'makki', 68: 'makki', 69: 'makki', 70: 'makki', 71: 'makki',
  72: 'makki', 74: 'makki', 75: 'makki', 77: 'makki', 78: 'makki',
  79: 'makki', 80: 'makki', 81: 'makki', 82: 'makki', 83: 'makki',
  84: 'makki', 85: 'makki', 86: 'makki', 87: 'makki', 88: 'makki',
  89: 'makki', 90: 'makki', 91: 'makki', 92: 'makki', 93: 'makki',
  94: 'makki', 95: 'makki', 96: 'makki', 100: 'makki', 101: 'makki',
  102: 'makki', 103: 'makki', 104: 'makki', 105: 'makki', 106: 'makki',
  109: 'makki', 111: 'makki', 112: 'makki', 113: 'makki', 114: 'makki',

  // Madani surahs (revealed after Hijra, primarily in Medina)
  2: 'madani', 3: 'madani', 4: 'madani', 5: 'madani', 8: 'madani',
  9: 'madani', 24: 'madani', 33: 'madani', 47: 'madani', 48: 'madani',
  49: 'madani', 57: 'madani', 58: 'madani', 59: 'madani', 60: 'madani',
  61: 'madani', 62: 'madani', 63: 'madani', 64: 'madani', 65: 'madani',
  66: 'madani', 98: 'madani', 110: 'madani',

  // Disputed surahs — marked unknown (scholars differ)
  13: 'unknown', 16: 'makki', 22: 'unknown', 29: 'unknown', 30: 'makki',
  31: 'makki', 32: 'makki', 39: 'makki', 42: 'makki', 55: 'unknown',
  73: 'makki', 76: 'unknown', 97: 'unknown', 99: 'unknown', 107: 'makki',
  108: 'makki',
};

// ---------------------------------------------------------------------------
// Curated English meanings of surah names
// Source: Standard scholarly translations (Pickthall, Yusuf Ali, Sahih International consensus)
// Marked needs_review — requires human verification
// ---------------------------------------------------------------------------

const ENGLISH_MEANINGS: Record<number, string> = {
  1: 'The Opening', 2: 'The Cow', 3: 'The Family of Imran', 4: 'The Women',
  5: 'The Table Spread', 6: 'The Cattle', 7: 'The Heights', 8: 'The Spoils of War',
  9: 'The Repentance', 10: 'Jonah', 11: 'Hud', 12: 'Joseph',
  13: 'The Thunder', 14: 'Abraham', 15: 'The Rocky Tract', 16: 'The Bee',
  17: 'The Night Journey', 18: 'The Cave', 19: 'Mary', 20: 'Ta-Ha',
  21: 'The Prophets', 22: 'The Pilgrimage', 23: 'The Believers', 24: 'The Light',
  25: 'The Criterion', 26: 'The Poets', 27: 'The Ant', 28: 'The Story',
  29: 'The Spider', 30: 'The Romans', 31: 'Luqman', 32: 'The Prostration',
  33: 'The Combined Forces', 34: 'Sheba', 35: 'The Originator', 36: 'Ya-Sin',
  37: 'Those Ranged in Ranks', 38: 'Sad', 39: 'The Groups', 40: 'The Forgiver',
  41: 'Explained in Detail', 42: 'The Consultation', 43: 'The Ornaments',
  44: 'The Smoke', 45: 'The Crouching', 46: 'The Wind-Curved Sandhills',
  47: 'Muhammad', 48: 'The Victory', 49: 'The Private Apartments',
  50: 'Qaf', 51: 'The Winnowing Winds', 52: 'The Mount', 53: 'The Star',
  54: 'The Moon', 55: 'The Beneficent', 56: 'The Inevitable', 57: 'The Iron',
  58: 'The Pleading', 59: 'The Exile', 60: 'The Examined One',
  61: 'The Ranks', 62: 'Friday', 63: 'The Hypocrites', 64: 'The Mutual Disillusion',
  65: 'The Divorce', 66: 'The Prohibition', 67: 'The Sovereignty',
  68: 'The Pen', 69: 'The Reality', 70: 'The Ascending Stairways',
  71: 'Noah', 72: 'The Jinn', 73: 'The Enshrouded One', 74: 'The Cloaked One',
  75: 'The Resurrection', 76: 'The Man', 77: 'The Emissaries',
  78: 'The Tidings', 79: 'Those who drag forth', 80: 'He Frowned',
  81: 'The Overthrowing', 82: 'The Cleaving', 83: 'The Defrauding',
  84: 'The Sundering', 85: 'The Great Stars', 86: 'The Nightcomer',
  87: 'The Most High', 88: 'The Overwhelming', 89: 'The Dawn',
  90: 'The City', 91: 'The Sun', 92: 'The Night', 93: 'The Morning Hours',
  94: 'The Relief', 95: 'The Fig', 96: 'The Clot', 97: 'The Night of Power',
  98: 'The Clear Proof', 99: 'The Earthquake', 100: 'The Courser',
  101: 'The Calamity', 102: 'The Rivalry in World Increase',
  103: 'The Declining Day', 104: 'The Traducer', 105: 'The Elephant',
  106: 'Quraysh', 107: 'The Small Kindnesses', 108: 'The Abundance',
  109: 'The Disbelievers', 110: 'The Divine Support', 111: 'The Palm Fiber',
  112: 'The Sincerity', 113: 'The Daybreak', 114: 'Mankind',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function lengthCategory(ayahCount: number): LengthCategory {
  if (ayahCount <= 20) return 'short';
  if (ayahCount <= 80) return 'medium';
  if (ayahCount <= 180) return 'long';
  return 'very_long';
}

function quranPosition(surahNumber: number): QuranPosition {
  if (surahNumber <= 10) return 'beginning';
  if (surahNumber <= 30) return 'early';
  if (surahNumber <= 70) return 'middle';
  if (surahNumber <= 100) return 'late';
  return 'ending';
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  console.log('Reading Quran data from:', QURAN_PATH);
  if (!existsSync(QURAN_PATH)) {
    console.error('ERROR: Quran data file not found:', QURAN_PATH);
    process.exit(1);
  }

  const raw = JSON.parse(readFileSync(QURAN_PATH, 'utf-8')) as QuranAyah[];
  console.log(`Loaded ${raw.length} ayahs from Quran data`);

  // Load stories manifest for surah->story/theme/figure relationships
  console.log('Reading stories manifest from:', STORIES_PATH);
  const surahStoriesMap: Record<number, string[]> = {};
  const surahThemesMap: Record<number, Set<string>> = {};
  const surahFiguresMap: Record<number, Set<string>> = {};
  const storyNames: Record<string, { ar: string; en: string }> = {};

  if (existsSync(STORIES_PATH)) {
    const storiesManifest = JSON.parse(readFileSync(STORIES_PATH, 'utf-8')) as { stories: StoryEntry[] };
    const stories = storiesManifest.stories ?? [];
    console.log(`Loaded ${stories.length} stories from manifest`);

    for (const story of stories) {
      // Build story name lookup
      if (story.name_ar || story.name_en) {
        storyNames[story.id] = {
          ar: story.name_ar ?? story.id,
          en: story.name_en ?? story.id,
        };
      }

      // Resolve surahs this story touches
      const suras: number[] = [...(story.suras_mentioned ?? [])];
      if (suras.length === 0) {
        const segSuras = new Set<number>();
        for (const seg of story.segments ?? []) {
          if (seg.sura_no) segSuras.add(seg.sura_no);
        }
        suras.push(...segSuras);
      }

      for (const sura of suras) {
        // Story IDs
        if (!surahStoriesMap[sura]) surahStoriesMap[sura] = [];
        if (!surahStoriesMap[sura].includes(story.id)) {
          surahStoriesMap[sura].push(story.id);
        }
        // Themes
        if (!surahThemesMap[sura]) surahThemesMap[sura] = new Set();
        for (const theme of story.themes ?? []) {
          surahThemesMap[sura].add(theme);
        }
        // Figures
        if (!surahFiguresMap[sura]) surahFiguresMap[sura] = new Set();
        for (const fig of story.main_figures ?? []) {
          // Skip generic/group labels
          if (!['His son', 'His wife', 'His people', 'His daughters', 'Their dog', 'His army'].includes(fig)) {
            surahFiguresMap[sura].add(fig);
          }
        }
      }
    }
    console.log(`Built story mappings for ${Object.keys(surahStoriesMap).length} surahs`);
    console.log(`Built theme mappings for ${Object.keys(surahThemesMap).length} surahs`);
    console.log(`Built figure mappings for ${Object.keys(surahFiguresMap).length} surahs`);
  } else {
    console.warn('Stories manifest not found — relatedStories will be empty');
  }

  // Group ayahs by surah
  const surahMap: Record<number, QuranAyah[]> = {};
  for (const ayah of raw) {
    if (!surahMap[ayah.sura_no]) surahMap[ayah.sura_no] = [];
    surahMap[ayah.sura_no].push(ayah);
  }

  const surahNumbers = Object.keys(surahMap).map(Number).sort((a, b) => a - b);
  if (surahNumbers.length !== 114) {
    console.error(`ERROR: Expected 114 surahs, found ${surahNumbers.length}`);
    process.exit(1);
  }

  const surahs: SurahMemoryItem[] = [];
  let needsReviewCount = 0;

  for (const surahNo of surahNumbers) {
    const ayahs = surahMap[surahNo].sort((a, b) => a.aya_no - b.aya_no);
    const firstAyah = ayahs[0];
    const lastAyah = ayahs[ayahs.length - 1];
    const ayahCount = ayahs.length;

    const pages = ayahs.map(a => a.page).filter(p => p != null);
    const juzs = ayahs.map(a => a.jozz).filter(j => j != null);

    const revelationType: RevelationType = REVELATION_TYPE[surahNo] ?? 'unknown';
    const nameEnglish = ENGLISH_MEANINGS[surahNo];
    const reviewStatus: ReviewStatus = 'needs_review';
    needsReviewCount++;

    // Additional ayah previews: 2nd ayah, two middle ayahs, second-to-last
    const getAyah = (no: number): QuranAyah | undefined => ayahs.find(a => a.aya_no === no);

    const second = ayahCount >= 3 ? getAyah(2) : undefined;
    // Middle: ~40% and ~60% through (distinct from first/second and last two)
    const midIdx1 = Math.max(3, Math.round(ayahCount * 0.40));
    const midIdx2 = Math.min(ayahCount - 2, Math.round(ayahCount * 0.60));
    const mid1 = ayahCount >= 8 && midIdx1 >= 3 ? getAyah(midIdx1) : undefined;
    const mid2 = ayahCount >= 9 && midIdx2 > midIdx1 ? getAyah(midIdx2) : undefined;
    const prevLast = ayahCount >= 3 ? getAyah(ayahCount - 1) : undefined;

    // Related stories (up to 5 per surah, from stories manifest)
    const relatedStories = (surahStoriesMap[surahNo] ?? []).slice(0, 5);
    // Themes: up to 6 per surah, sorted by specificity (longer = more specific first)
    const relatedThemes = [...(surahThemesMap[surahNo] ?? [])].slice(0, 6);
    // Figures: up to 6 per surah
    const mainFigures = [...(surahFiguresMap[surahNo] ?? [])].slice(0, 6);

    const item: SurahMemoryItem = {
      surahNumber: surahNo,
      nameArabic: firstAyah.sura_name_ar,
      nameTransliteration: firstAyah.sura_name_en,
      nameEnglish,
      revelationType,
      ayahCount,
      lengthCategory: lengthCategory(ayahCount),
      quranPosition: quranPosition(surahNo),
      juzStart: Math.min(...juzs),
      juzEnd: Math.max(...juzs),
      pageStart: Math.min(...pages),
      pageEnd: Math.max(...pages),
      firstAyahRef: `${surahNo}:1`,
      secondAyahRef: second ? `${surahNo}:2` : undefined,
      midAyah1Ref: mid1 ? `${surahNo}:${midIdx1}` : undefined,
      midAyah2Ref: mid2 ? `${surahNo}:${midIdx2}` : undefined,
      prevLastAyahRef: prevLast ? `${surahNo}:${ayahCount - 1}` : undefined,
      lastAyahRef: `${surahNo}:${ayahCount}`,
      firstAyahPreview: firstAyah.aya_text,
      secondAyahPreview: second?.aya_text,
      midAyah1Preview: mid1?.aya_text,
      midAyah2Preview: mid2?.aya_text,
      prevLastAyahPreview: prevLast?.aya_text,
      lastAyahPreview: lastAyah.aya_text,
      mainTopicsArabic: [],
      mainTopicsEnglish: [],
      relatedStories,
      relatedThemes,
      mainFigures,
      sourceIds: ['quran_hafs_local', 'surah_atlas_metadata'],
      reviewStatus,
    };

    surahs.push(item);
  }

  const makkiCount = surahs.filter(s => s.revelationType === 'makki').length;
  const madaniCount = surahs.filter(s => s.revelationType === 'madani').length;
  const unknownRevelationCount = surahs.filter(s => s.revelationType === 'unknown').length;

  const atlas = {
    version: '1.1.0',
    generatedAt: new Date().toISOString(),
    totalSurahs: surahs.length,
    sourceNote: 'Ayah text from quran_uthmani.json (canonical). Makki/Madani and English meanings from curated scholarly metadata (needs_review). Story links from stories.json manifest. Topics/clues not yet available.',
    storyNames,
    surahs,
  };

  // Write JSON
  const outputDir = join(ROOT, 'frontend/src/data/generated');
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });
  writeFileSync(OUTPUT_JSON, JSON.stringify(atlas, null, 2), 'utf-8');
  console.log(`\nWrote ${surahs.length} surah entries to: ${OUTPUT_JSON}`);
  console.log(`Story names embedded: ${Object.keys(storyNames).length}`);

  // Write summary markdown
  const docsGenDir = join(ROOT, 'docs/generated');
  if (!existsSync(docsGenDir)) mkdirSync(docsGenDir, { recursive: true });

  const summaryLines: string[] = [
    '# Surah Memory Atlas — Generated Summary',
    '',
    `Generated: ${new Date().toISOString()}`,
    '',
    '## Statistics',
    '',
    `- Total surahs: ${surahs.length}`,
    `- Makki: ${makkiCount}`,
    `- Madani: ${madaniCount}`,
    `- Unknown/disputed revelation type: ${unknownRevelationCount}`,
    `- All entries: needs_review (Makki/Madani and English meanings require human verification)`,
    `- Story names embedded: ${Object.keys(storyNames).length}`,
    '',
    '## Length Distribution',
    '',
    `- Short (1–20 ayahs): ${surahs.filter(s => s.lengthCategory === 'short').length}`,
    `- Medium (21–80 ayahs): ${surahs.filter(s => s.lengthCategory === 'medium').length}`,
    `- Long (81–180 ayahs): ${surahs.filter(s => s.lengthCategory === 'long').length}`,
    `- Very Long (181+ ayahs): ${surahs.filter(s => s.lengthCategory === 'very_long').length}`,
    '',
    '## Position Distribution',
    '',
    `- Beginning (1–10): ${surahs.filter(s => s.quranPosition === 'beginning').length}`,
    `- Early (11–30): ${surahs.filter(s => s.quranPosition === 'early').length}`,
    `- Middle (31–70): ${surahs.filter(s => s.quranPosition === 'middle').length}`,
    `- Late (71–100): ${surahs.filter(s => s.quranPosition === 'late').length}`,
    `- Ending (101–114): ${surahs.filter(s => s.quranPosition === 'ending').length}`,
    '',
    '## Data Availability',
    '',
    '| Field | Status |',
    '|---|---|',
    '| Arabic name | ✓ verified (from quran_uthmani.json) |',
    '| English transliteration | ✓ verified (from quran_uthmani.json) |',
    '| English meaning | needs_review (curated scholarly metadata) |',
    '| Ayah count | ✓ verified (from quran_uthmani.json) |',
    '| Page range | ✓ verified (from quran_uthmani.json) |',
    '| Juz range | ✓ verified (from quran_uthmani.json) |',
    '| Ayah previews (6 per surah) | ✓ verified (from quran_uthmani.json) |',
    '| Makki/Madani | needs_review (curated from Al-Suyuti) |',
    '| Related stories | from stories.json manifest |',
    '| Main topics | missing — not yet available |',
    '| Memory clues | missing — not yet available |',
    '',
    '## Surah List',
    '',
    '| # | Arabic Name | Transliteration | Type | Ayahs | Juz | Pages | Stories |',
    '|---|---|---|---|---|---|---|---|',
    ...surahs.map(s =>
      `| ${s.surahNumber} | ${s.nameArabic} | ${s.nameTransliteration} | ${s.revelationType} | ${s.ayahCount} | ${s.juzStart}–${s.juzEnd} | ${s.pageStart}–${s.pageEnd} | ${s.relatedStories.length} |`
    ),
  ];

  writeFileSync(OUTPUT_MD, summaryLines.join('\n'), 'utf-8');
  console.log(`Wrote summary to: ${OUTPUT_MD}`);
  console.log('\nDone. All entries marked needs_review.');
}

main();
