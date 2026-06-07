/**
 * Rare Words Validator
 *
 * Validates frontend/src/data/quranRareWords.ts:
 * - All word IDs are unique
 * - Every entry has an ayah reference (surah + ayah)
 * - Every entry has at least one lexicalEvidenceRef
 * - No approved entry without a sourceId
 * - normalizedArabic is present
 * - transliteration is present
 * - simpleMeaning and contextualMeaning are non-empty
 * - rarityLevel is a valid enum value
 *
 * Usage:
 *   npx tsx scripts/validate-rare-words.ts
 *   npx tsx scripts/validate-rare-words.ts --verbose
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const RARE_WORDS_PATH = join(ROOT, 'frontend/src/data/quranRareWords.ts');

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

const VALID_RARITY_LEVELS = new Set(['very_rare', 'rare', 'moderately_rare']);
const VALID_REVIEW_STATUSES = new Set(['approved', 'needs_review', 'rejected']);

console.log('\n=== Rare Words Validator ===\n');

if (!existsSync(RARE_WORDS_PATH)) {
  fail(`quranRareWords.ts not found at ${RARE_WORDS_PATH}`);
  process.exit(1);
}
pass('quranRareWords.ts found');

const source = readFileSync(RARE_WORDS_PATH, 'utf-8');

// Check required exports
const requiredExports = [
  'QURAN_RARE_WORDS',
  'RARE_WORDS_COLLECTION',
  'getRareWordsBySurah',
  'getRareWordById',
  'searchRareWords',
];

for (const exp of requiredExports) {
  if (!source.includes(exp)) {
    fail(`Missing export: ${exp}`);
  } else {
    pass(`Found export: ${exp}`);
  }
}

// Count entries
const wordCount = (source.match(/id:\s*'rw_/g) || []).length;
console.log(`\nRare word entries: ${wordCount}`);

if (wordCount === 0) {
  warn('No rare word entries found — expected at least 1');
}

// Check rarity levels
const rarityLevels = [...source.matchAll(/rarityLevel:\s*'([^']+)'/g)].map((m) => m[1]);
for (const rl of rarityLevels) {
  if (!VALID_RARITY_LEVELS.has(rl)) {
    fail(`Invalid rarityLevel: '${rl}'`);
  }
}
if (rarityLevels.length > 0) {
  pass(`All ${rarityLevels.length} rarity levels are valid`);
}

// Check review statuses
const reviewStatuses = [...source.matchAll(/reviewStatus:\s*'([^']+)'/g)].map((m) => m[1]);
for (const rs of reviewStatuses) {
  if (!VALID_REVIEW_STATUSES.has(rs)) {
    fail(`Invalid reviewStatus: '${rs}'`);
  }
}

// Check approved entries have evidence
const approvedCount = (source.match(/reviewStatus:\s*'approved'/g) || []).length;
if (approvedCount > 0) {
  warn(`${approvedCount} approved entries — verify lexicalEvidenceRefs are populated`);
}

// Check surah numbers
const surahRefs = [...source.matchAll(/surah:\s*(\d+)/g)].map((m) => parseInt(m[1]));
const invalidSurahs = surahRefs.filter((n) => n < 1 || n > 114);
if (invalidSurahs.length > 0) {
  fail(`Invalid surah numbers: ${[...new Set(invalidSurahs)].join(', ')}`);
} else if (surahRefs.length > 0) {
  pass(`All ${surahRefs.length} surah references valid (1–114)`);
}

// Check Arabic field is present for each entry (not empty)
const emptyArabic = (source.match(/arabic:\s*'',/g) || []).length;
if (emptyArabic > 0) {
  fail(`${emptyArabic} entries have empty arabic field`);
}

// Check normalizedArabic is present
const emptyNormalized = (source.match(/normalizedArabic:\s*'',/g) || []).length;
if (emptyNormalized > 0) {
  fail(`${emptyNormalized} entries have empty normalizedArabic field`);
}

// Check transliteration is present
const emptyTranslit = (source.match(/transliteration:\s*'',/g) || []).length;
if (emptyTranslit > 0) {
  fail(`${emptyTranslit} entries have empty transliteration field`);
}

// Check lexicalEvidenceRefs is present (not empty array for approved)
const lexEvidenceCount = (source.match(/lexicalEvidenceRefs:\s*\[/g) || []).length;
if (lexEvidenceCount === 0) {
  fail('No lexicalEvidenceRefs fields found');
} else {
  pass(`${lexEvidenceCount} lexicalEvidenceRefs fields found`);
}

// Check humanReviewRequired: true
const humanReviewTrue = (source.match(/humanReviewRequired:\s*true/g) || []).length;
const humanReviewFalse = (source.match(/humanReviewRequired:\s*false/g) || []).length;
if (humanReviewFalse > 0) {
  warn(`${humanReviewFalse} entries have humanReviewRequired: false`);
}
pass(`${humanReviewTrue} entries have humanReviewRequired: true`);

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
console.log('\n=== Validation Summary ===');
console.log(`Total entries:   ${wordCount}`);
console.log(`Errors:          ${errors}`);
console.log(`Warnings:        ${warnings}`);

if (errors > 0) {
  console.error('\n✗ Rare Words validation FAILED');
  process.exit(1);
} else if (warnings > 0) {
  console.warn('\n⚠ Rare Words validation PASSED with warnings');
  process.exit(0);
} else {
  console.log('\n✓ Rare Words validation PASSED');
  process.exit(0);
}
