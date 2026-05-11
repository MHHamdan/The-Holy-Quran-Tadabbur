/**
 * Surah Memory Atlas Validator
 *
 * Validates frontend/src/data/generated/surahMemoryAtlas.json against:
 * - data/raw/quran_uthmani.json (canonical Quran data)
 * - frontend/src/data/sourceRegistry.ts (source ID whitelist)
 *
 * Usage:
 *   npx tsx scripts/validate-surah-memory-atlas.ts
 *   npx tsx scripts/validate-surah-memory-atlas.ts --verbose
 *
 * Exit codes:
 *   0 = all checks passed
 *   1 = one or more checks failed
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const QURAN_PATH = join(ROOT, 'data/raw/quran_uthmani.json');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/surahMemoryAtlas.json');
const SOURCE_REGISTRY_PATH = join(ROOT, 'frontend/src/data/sourceRegistry.ts');

const args = process.argv.slice(2);
const VERBOSE = args.includes('--verbose');

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
  lastAyahRef: string;
  firstAyahPreview?: string;
  lastAyahPreview?: string;
  mainTopicsArabic: string[];
  mainTopicsEnglish: string[];
  relatedStories: string[];
  relatedThemes: string[];
  sourceIds: string[];
  reviewStatus: ReviewStatus;
}

interface QuranAyah {
  sura_no: number;
  aya_no: number;
  aya_text: string;
  page: number;
  jozz: number;
}

const errors: string[] = [];
const warnings: string[] = [];

function fail(msg: string) {
  errors.push(msg);
  if (VERBOSE) console.error('  FAIL:', msg);
}

function warn(msg: string) {
  warnings.push(msg);
  if (VERBOSE) console.warn('  WARN:', msg);
}

function pass(msg: string) {
  if (VERBOSE) console.log('  PASS:', msg);
}

// ---------------------------------------------------------------------------
// Load files
// ---------------------------------------------------------------------------

if (!existsSync(ATLAS_PATH)) {
  console.error('Atlas file not found:', ATLAS_PATH);
  console.error('Run: npx tsx scripts/build-surah-memory-atlas.ts');
  process.exit(1);
}

if (!existsSync(QURAN_PATH)) {
  console.error('Quran data not found:', QURAN_PATH);
  process.exit(1);
}

const atlas = JSON.parse(readFileSync(ATLAS_PATH, 'utf-8'));
const quranRaw = JSON.parse(readFileSync(QURAN_PATH, 'utf-8')) as QuranAyah[];
const registrySource = readFileSync(SOURCE_REGISTRY_PATH, 'utf-8');

// Extract source IDs from registry
const sourceIdMatches = registrySource.matchAll(/sourceId:\s*'([^']+)'/g);
const knownSourceIds = new Set(Array.from(sourceIdMatches, m => m[1]));

console.log('\nSurah Memory Atlas Validator');
console.log('============================');
console.log(`Atlas: ${ATLAS_PATH}`);
console.log(`Quran: ${QURAN_PATH}`);
console.log(`Known source IDs: ${knownSourceIds.size}`);
console.log('');

// ---------------------------------------------------------------------------
// Build ground truth from Quran data
// ---------------------------------------------------------------------------

const surahGroundTruth: Record<number, {
  ayahCount: number;
  pages: Set<number>;
  juzs: Set<number>;
  firstAyahText: string;
  lastAyahText: string;
}> = {};

for (const ayah of quranRaw) {
  const s = ayah.sura_no;
  if (!surahGroundTruth[s]) {
    surahGroundTruth[s] = {
      ayahCount: 0,
      pages: new Set(),
      juzs: new Set(),
      firstAyahText: '',
      lastAyahText: '',
    };
  }
  surahGroundTruth[s].ayahCount++;
  if (ayah.page) surahGroundTruth[s].pages.add(ayah.page);
  if (ayah.jozz) surahGroundTruth[s].juzs.add(ayah.jozz);
}

// Get first and last ayah text per surah
for (const ayah of quranRaw) {
  const s = ayah.sura_no;
  const gt = surahGroundTruth[s];
  if (ayah.aya_no === 1) gt.firstAyahText = ayah.aya_text;
  if (ayah.aya_no === gt.ayahCount) gt.lastAyahText = ayah.aya_text;
}

// ---------------------------------------------------------------------------
// Check 1: Atlas structure
// ---------------------------------------------------------------------------

console.log('Check 1: Atlas structure');
if (!atlas.surahs || !Array.isArray(atlas.surahs)) {
  fail('atlas.surahs is not an array');
} else {
  pass('atlas.surahs is an array');
}
if (!atlas.version) fail('Missing atlas.version');
if (!atlas.generatedAt) fail('Missing atlas.generatedAt');
if (!atlas.totalSurahs) fail('Missing atlas.totalSurahs');

// ---------------------------------------------------------------------------
// Check 2: Exactly 114 surahs
// ---------------------------------------------------------------------------

console.log('Check 2: Surah count');
const surahs: SurahMemoryItem[] = atlas.surahs ?? [];
if (surahs.length !== 114) {
  fail(`Expected 114 surahs, found ${surahs.length}`);
} else {
  pass(`Exactly 114 surahs`);
}
if (atlas.totalSurahs !== surahs.length) {
  fail(`atlas.totalSurahs (${atlas.totalSurahs}) does not match surahs.length (${surahs.length})`);
}

// ---------------------------------------------------------------------------
// Check 3: Surah numbers 1–114, no duplicates
// ---------------------------------------------------------------------------

console.log('Check 3: Surah numbers 1–114, no duplicates');
const seenNumbers = new Set<number>();
for (const s of surahs) {
  if (typeof s.surahNumber !== 'number') {
    fail(`surahNumber is not a number: ${JSON.stringify(s.surahNumber)}`);
    continue;
  }
  if (s.surahNumber < 1 || s.surahNumber > 114) {
    fail(`Invalid surahNumber: ${s.surahNumber}`);
  }
  if (seenNumbers.has(s.surahNumber)) {
    fail(`Duplicate surahNumber: ${s.surahNumber}`);
  }
  seenNumbers.add(s.surahNumber);
}
for (let i = 1; i <= 114; i++) {
  if (!seenNumbers.has(i)) fail(`Missing surahNumber: ${i}`);
}
if (errors.length === 0) pass('Surah numbers 1–114 with no duplicates');

// ---------------------------------------------------------------------------
// Check 4: Required string fields present
// ---------------------------------------------------------------------------

console.log('Check 4: Required string fields');
for (const s of surahs) {
  if (!s.nameArabic || typeof s.nameArabic !== 'string') {
    fail(`Surah ${s.surahNumber}: missing or invalid nameArabic`);
  }
  if (!s.nameTransliteration || typeof s.nameTransliteration !== 'string') {
    fail(`Surah ${s.surahNumber}: missing or invalid nameTransliteration`);
  }
}
if (errors.filter(e => e.includes('nameArabic') || e.includes('nameTransliteration')).length === 0) {
  pass('All surahs have nameArabic and nameTransliteration');
}

// ---------------------------------------------------------------------------
// Check 5: revelationType valid
// ---------------------------------------------------------------------------

console.log('Check 5: revelationType validity');
const validRevelationTypes: RevelationType[] = ['makki', 'madani', 'unknown'];
for (const s of surahs) {
  if (!validRevelationTypes.includes(s.revelationType as RevelationType)) {
    fail(`Surah ${s.surahNumber}: invalid revelationType "${s.revelationType}"`);
  }
}
pass('All revelationType values are valid');

// ---------------------------------------------------------------------------
// Check 6: lengthCategory valid and matches ayahCount
// ---------------------------------------------------------------------------

console.log('Check 6: lengthCategory validity');
const validLengths: LengthCategory[] = ['short', 'medium', 'long', 'very_long'];
for (const s of surahs) {
  if (!validLengths.includes(s.lengthCategory as LengthCategory)) {
    fail(`Surah ${s.surahNumber}: invalid lengthCategory "${s.lengthCategory}"`);
  }
  // Verify computed value
  const expected =
    s.ayahCount <= 20 ? 'short' :
    s.ayahCount <= 80 ? 'medium' :
    s.ayahCount <= 180 ? 'long' : 'very_long';
  if (s.lengthCategory !== expected) {
    fail(`Surah ${s.surahNumber}: lengthCategory "${s.lengthCategory}" does not match ayahCount ${s.ayahCount} (expected "${expected}")`);
  }
}
pass('All lengthCategory values valid and match ayahCount');

// ---------------------------------------------------------------------------
// Check 7: quranPosition valid and matches surahNumber
// ---------------------------------------------------------------------------

console.log('Check 7: quranPosition validity');
const validPositions: QuranPosition[] = ['beginning', 'early', 'middle', 'late', 'ending'];
for (const s of surahs) {
  if (!validPositions.includes(s.quranPosition as QuranPosition)) {
    fail(`Surah ${s.surahNumber}: invalid quranPosition "${s.quranPosition}"`);
  }
  const expected =
    s.surahNumber <= 10 ? 'beginning' :
    s.surahNumber <= 30 ? 'early' :
    s.surahNumber <= 70 ? 'middle' :
    s.surahNumber <= 100 ? 'late' : 'ending';
  if (s.quranPosition !== expected) {
    fail(`Surah ${s.surahNumber}: quranPosition "${s.quranPosition}" does not match surahNumber (expected "${expected}")`);
  }
}
pass('All quranPosition values valid and match surahNumber');

// ---------------------------------------------------------------------------
// Check 8: ayahCount matches ground truth
// ---------------------------------------------------------------------------

console.log('Check 8: ayahCount matches Quran data');
for (const s of surahs) {
  const gt = surahGroundTruth[s.surahNumber];
  if (!gt) {
    fail(`Surah ${s.surahNumber}: not found in ground truth Quran data`);
    continue;
  }
  if (s.ayahCount !== gt.ayahCount) {
    fail(`Surah ${s.surahNumber}: ayahCount ${s.ayahCount} does not match Quran data ${gt.ayahCount}`);
  }
}
pass('All ayahCounts match Quran data');

// ---------------------------------------------------------------------------
// Check 9: page range matches ground truth
// ---------------------------------------------------------------------------

console.log('Check 9: page range validity');
for (const s of surahs) {
  const gt = surahGroundTruth[s.surahNumber];
  if (!gt || gt.pages.size === 0) continue;
  const expectedStart = Math.min(...gt.pages);
  const expectedEnd = Math.max(...gt.pages);
  if (s.pageStart !== expectedStart) {
    fail(`Surah ${s.surahNumber}: pageStart ${s.pageStart} does not match Quran data ${expectedStart}`);
  }
  if (s.pageEnd !== expectedEnd) {
    fail(`Surah ${s.surahNumber}: pageEnd ${s.pageEnd} does not match Quran data ${expectedEnd}`);
  }
}
pass('All page ranges match Quran data');

// ---------------------------------------------------------------------------
// Check 10: juz range matches ground truth
// ---------------------------------------------------------------------------

console.log('Check 10: juz range validity');
for (const s of surahs) {
  const gt = surahGroundTruth[s.surahNumber];
  if (!gt || gt.juzs.size === 0) continue;
  const expectedStart = Math.min(...gt.juzs);
  const expectedEnd = Math.max(...gt.juzs);
  if (s.juzStart !== expectedStart) {
    fail(`Surah ${s.surahNumber}: juzStart ${s.juzStart} does not match Quran data ${expectedStart}`);
  }
  if (s.juzEnd !== expectedEnd) {
    fail(`Surah ${s.surahNumber}: juzEnd ${s.juzEnd} does not match Quran data ${expectedEnd}`);
  }
}
pass('All juz ranges match Quran data');

// ---------------------------------------------------------------------------
// Check 11: firstAyahRef and lastAyahRef valid
// ---------------------------------------------------------------------------

console.log('Check 11: ayah references validity');
for (const s of surahs) {
  const expectedFirst = `${s.surahNumber}:1`;
  const expectedLast = `${s.surahNumber}:${s.ayahCount}`;
  if (s.firstAyahRef !== expectedFirst) {
    fail(`Surah ${s.surahNumber}: firstAyahRef "${s.firstAyahRef}" should be "${expectedFirst}"`);
  }
  if (s.lastAyahRef !== expectedLast) {
    fail(`Surah ${s.surahNumber}: lastAyahRef "${s.lastAyahRef}" should be "${expectedLast}"`);
  }
}
pass('All ayah references valid');

// ---------------------------------------------------------------------------
// Check 12: firstAyahPreview / lastAyahPreview match Quran data
// ---------------------------------------------------------------------------

console.log('Check 12: ayah previews match Quran data');
for (const s of surahs) {
  const gt = surahGroundTruth[s.surahNumber];
  if (!gt) continue;
  if (s.firstAyahPreview !== undefined && s.firstAyahPreview !== gt.firstAyahText) {
    fail(`Surah ${s.surahNumber}: firstAyahPreview does not match Quran data`);
  }
  if (s.lastAyahPreview !== undefined && s.lastAyahPreview !== gt.lastAyahText) {
    fail(`Surah ${s.surahNumber}: lastAyahPreview does not match Quran data`);
  }
}
pass('All ayah previews match Quran data');

// ---------------------------------------------------------------------------
// Check 13: No unknown sourceIds
// ---------------------------------------------------------------------------

console.log('Check 13: sourceIds are all in registry');
for (const s of surahs) {
  if (!Array.isArray(s.sourceIds)) {
    fail(`Surah ${s.surahNumber}: sourceIds is not an array`);
    continue;
  }
  for (const sid of s.sourceIds) {
    if (!knownSourceIds.has(sid)) {
      fail(`Surah ${s.surahNumber}: unknown sourceId "${sid}"`);
    }
  }
}
pass('All sourceIds are registered');

// ---------------------------------------------------------------------------
// Check 14: reviewStatus valid
// ---------------------------------------------------------------------------

console.log('Check 14: reviewStatus validity');
const validStatuses: ReviewStatus[] = ['verified', 'needs_review', 'missing_metadata'];
for (const s of surahs) {
  if (!validStatuses.includes(s.reviewStatus as ReviewStatus)) {
    fail(`Surah ${s.surahNumber}: invalid reviewStatus "${s.reviewStatus}"`);
  }
}
pass('All reviewStatus values valid');

// ---------------------------------------------------------------------------
// Check 15: No impossible numeric values
// ---------------------------------------------------------------------------

console.log('Check 15: No impossible numeric values');
for (const s of surahs) {
  if (s.ayahCount <= 0) fail(`Surah ${s.surahNumber}: ayahCount must be > 0`);
  if (s.pageStart <= 0) fail(`Surah ${s.surahNumber}: pageStart must be > 0`);
  if (s.pageEnd < s.pageStart) fail(`Surah ${s.surahNumber}: pageEnd < pageStart`);
  if (s.juzStart <= 0 || s.juzStart > 30) fail(`Surah ${s.surahNumber}: juzStart out of range`);
  if (s.juzEnd <= 0 || s.juzEnd > 30) fail(`Surah ${s.surahNumber}: juzEnd out of range`);
  if (s.juzEnd < s.juzStart) fail(`Surah ${s.surahNumber}: juzEnd < juzStart`);
  if (s.pageEnd > 604) warn(`Surah ${s.surahNumber}: pageEnd ${s.pageEnd} > 604 (unusual)`);
}
pass('Numeric values are within valid ranges');

// ---------------------------------------------------------------------------
// Check 16: Arrays are arrays (not undefined)
// ---------------------------------------------------------------------------

console.log('Check 16: Array fields are arrays');
for (const s of surahs) {
  if (!Array.isArray(s.mainTopicsArabic)) fail(`Surah ${s.surahNumber}: mainTopicsArabic not array`);
  if (!Array.isArray(s.mainTopicsEnglish)) fail(`Surah ${s.surahNumber}: mainTopicsEnglish not array`);
  if (!Array.isArray(s.relatedStories)) fail(`Surah ${s.surahNumber}: relatedStories not array`);
  if (!Array.isArray(s.relatedThemes)) fail(`Surah ${s.surahNumber}: relatedThemes not array`);
  if (!Array.isArray(s.sourceIds)) fail(`Surah ${s.surahNumber}: sourceIds not array`);
}
pass('All array fields are arrays');

// ---------------------------------------------------------------------------
// Results
// ---------------------------------------------------------------------------

console.log('');
console.log('============================');
console.log(`Checks complete`);
console.log(`Errors:   ${errors.length}`);
console.log(`Warnings: ${warnings.length}`);

if (errors.length > 0) {
  console.error('\nFailed checks:');
  for (const e of errors) console.error(' -', e);
  process.exit(1);
}

if (warnings.length > 0) {
  console.warn('\nWarnings:');
  for (const w of warnings) console.warn(' -', w);
}

console.log('\nAll validation checks passed.');
process.exit(0);
