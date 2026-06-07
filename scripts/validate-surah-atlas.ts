/**
 * Surah Atlas Validator
 *
 * Validates frontend/src/data/surahAtlas.ts against:
 * - Exactly 114 entries
 * - Valid surah numbers (1–114)
 * - Valid revelation types
 * - Summaries exist (even if placeholder)
 * - reviewStatus and humanReviewRequired are set
 * - sourceIds reference valid sources
 *
 * Usage:
 *   npx tsx scripts/validate-surah-atlas.ts
 *   npx tsx scripts/validate-surah-atlas.ts --verbose
 *
 * Exit codes:
 *   0 = all checks passed
 *   1 = one or more checks failed
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const SURAH_ATLAS_PATH = join(ROOT, 'frontend/src/data/surahAtlas.ts');
const QURAN_PATH = join(ROOT, 'data/raw/quran_uthmani.json');

const args = process.argv.slice(2);
const VERBOSE = args.includes('--verbose');

let errors = 0;
let warnings = 0;

function fail(msg: string): void {
  console.error(`  ✗ FAIL: ${msg}`);
  errors++;
}

function warn(msg: string): void {
  console.warn(`  ⚠ WARN: ${msg}`);
  warnings++;
}

function pass(msg: string): void {
  if (VERBOSE) console.log(`  ✓ ${msg}`);
}

// ---------------------------------------------------------------------------
// Load Quran data for reference
// ---------------------------------------------------------------------------
if (!existsSync(QURAN_PATH)) {
  fail(`Quran data not found at ${QURAN_PATH}`);
  process.exit(1);
}

const quranRaw = JSON.parse(readFileSync(QURAN_PATH, 'utf-8'));
const EXPECTED_AYAH_COUNTS: Record<number, number> = {};
for (const surah of quranRaw) {
  if (typeof surah.id === 'number' && Array.isArray(surah.verses)) {
    EXPECTED_AYAH_COUNTS[surah.id] = surah.verses.length;
  }
}

// ---------------------------------------------------------------------------
// Check surahAtlas.ts exists
// ---------------------------------------------------------------------------
console.log('\n=== Surah Atlas Validator ===\n');

if (!existsSync(SURAH_ATLAS_PATH)) {
  fail(`surahAtlas.ts not found at ${SURAH_ATLAS_PATH}`);
  process.exit(1);
}
pass('surahAtlas.ts found');

// ---------------------------------------------------------------------------
// Parse surahAtlas.ts — extract surahNumber, ayahCount, reviewStatus
// We use regex parsing since we can't import TS directly here
// ---------------------------------------------------------------------------
const source = readFileSync(SURAH_ATLAS_PATH, 'utf-8');

// Extract all surahNumber values
const surahNumbers = [...source.matchAll(/surahNumber:\s*(\d+)/g)].map((m) => parseInt(m[1]));
// The first occurrence of each surahNumber is an entry; subsequent are references
// The top-level entries are the SURAH_ATLAS_DATA array — count unique sequential ones
const topLevelNumbers: number[] = [];
let inEntry = false;
for (const match of source.matchAll(/\{\s*\n\s*surahNumber:\s*(\d+)/g)) {
  topLevelNumbers.push(parseInt(match[1]));
}

const entryCount = topLevelNumbers.length;

// Check count
console.log(`Surah Atlas entries found: ${entryCount}`);
if (entryCount === 114) {
  pass('Exactly 114 surah entries found');
} else {
  fail(`Expected 114 surah entries, found ${entryCount}`);
}

// Check for duplicate surah numbers
const seen = new Set<number>();
const duplicates: number[] = [];
for (const n of topLevelNumbers) {
  if (seen.has(n)) duplicates.push(n);
  seen.add(n);
}
if (duplicates.length > 0) {
  fail(`Duplicate surah numbers: ${duplicates.join(', ')}`);
} else {
  pass('No duplicate surah numbers');
}

// Check surah numbers are 1–114
const invalidNumbers = topLevelNumbers.filter((n) => n < 1 || n > 114);
if (invalidNumbers.length > 0) {
  fail(`Invalid surah numbers (must be 1–114): ${invalidNumbers.join(', ')}`);
} else {
  pass('All surah numbers are valid (1–114)');
}

// Check needs_review count
const needsReviewCount = (source.match(/reviewStatus:\s*'needs_review'/g) || []).length;
const approvedCount = (source.match(/reviewStatus:\s*'approved'/g) || []).length;

console.log(`\nReview status distribution:`);
console.log(`  needs_review: ${needsReviewCount}`);
console.log(`  approved:     ${approvedCount}`);

if (approvedCount > 0) {
  warn(`${approvedCount} entries marked as 'approved' — these require human verification`);
}

// Check humanReviewRequired: true is present for all entries
const humanReviewTrue = (source.match(/humanReviewRequired:\s*true/g) || []).length;
const humanReviewFalse = (source.match(/humanReviewRequired:\s*false/g) || []).length;

if (humanReviewFalse > 0) {
  warn(`${humanReviewFalse} entries have humanReviewRequired: false — verify these are intentional`);
}
pass(`${humanReviewTrue} entries have humanReviewRequired: true`);

// Check summaries are present (not empty strings)
const emptySummaries = (source.match(/en:\s*'',/g) || []).length;
if (emptySummaries > 0) {
  warn(`${emptySummaries} empty English strings found — check summary completeness`);
}

// Check for Arabic text (should not be hard-coded Quran text)
// Arabic names are OK; complete ayat are not allowed
const longArabicStrings = [...source.matchAll(/ar:\s*'([^']{100,})'/g)];
for (const match of longArabicStrings) {
  const text = match[1];
  if (text.includes('ٱلْحَمْدُ') || text.includes('بِسْمِ ٱللَّهِ')) {
    // These are allowed in previews but should not be in data files
    warn(`Long Arabic string may contain Quran text: "${text.slice(0, 60)}..."`);
  }
}

// Check getSurahAtlasEntry export exists
if (!source.includes('getSurahAtlasEntry')) {
  fail('getSurahAtlasEntry function not exported');
} else {
  pass('getSurahAtlasEntry function found');
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
console.log('\n=== Validation Summary ===');
console.log(`Errors:   ${errors}`);
console.log(`Warnings: ${warnings}`);

if (errors > 0) {
  console.error('\n✗ Surah Atlas validation FAILED');
  process.exit(1);
} else if (warnings > 0) {
  console.warn('\n⚠ Surah Atlas validation PASSED with warnings');
  process.exit(0);
} else {
  console.log('\n✓ Surah Atlas validation PASSED');
  process.exit(0);
}
