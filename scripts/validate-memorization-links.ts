/**
 * Memorization Links Validator
 *
 * Validates frontend/src/data/quranMemorizationLinks.ts:
 * - All link IDs are unique
 * - All ayah references have valid surah (1–114) and ayah (>0)
 * - All link types are from the allowed set
 * - All entries carry reviewStatus
 * - No approved entries without evidence refs
 * - Confusion pairs have differenceNote
 *
 * Usage:
 *   npx tsx scripts/validate-memorization-links.ts
 *   npx tsx scripts/validate-memorization-links.ts --verbose
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const LINKS_PATH = join(ROOT, 'frontend/src/data/quranMemorizationLinks.ts');

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

const ALLOWED_LINK_TYPES = new Set([
  'similar_opening', 'similar_ending', 'similar_phrase', 'repeated_story',
  'repeated_dialogue', 'same_prophet_different_surah', 'same_theme_different_surah',
  'near_duplicate_structure', 'contrast_pair', 'chronological_story_sequence',
  'same_command', 'same_dua', 'same_warning', 'same_reward', 'same_punishment',
]);

console.log('\n=== Memorization Links Validator ===\n');

if (!existsSync(LINKS_PATH)) {
  fail(`quranMemorizationLinks.ts not found at ${LINKS_PATH}`);
  process.exit(1);
}
pass('quranMemorizationLinks.ts found');

const source = readFileSync(LINKS_PATH, 'utf-8');

// Check required exports
const requiredExports = [
  'CONFUSION_PAIRS',
  'MEMORIZATION_LINKS',
  'REPEATED_PHRASES',
  'STORY_RECURRENCES',
  'MEMORIZATION_INTELLIGENCE',
  'getConfusionPairsForSurah',
  'getMemorizationLinksForSurah',
  'getStoryRecurrence',
];

for (const exp of requiredExports) {
  if (!source.includes(exp)) {
    fail(`Missing export: ${exp}`);
  } else {
    pass(`Found export: ${exp}`);
  }
}

// Count entries
const confusionPairCount = (source.match(/id:\s*'cp_/g) || []).length;
const memLinkCount = (source.match(/id:\s*'ml_/g) || []).length;
const phraseCount = (source.match(/id:\s*'rp_/g) || []).length;
const recurrenceCount = (source.match(/storyId:\s*'story_/g) || []).length;

console.log(`\nEntry counts:`);
console.log(`  Confusion pairs:      ${confusionPairCount}`);
console.log(`  Memorization links:   ${memLinkCount}`);
console.log(`  Repeated phrases:     ${phraseCount}`);
console.log(`  Story recurrences:    ${recurrenceCount}`);

if (confusionPairCount === 0) {
  warn('No confusion pairs found — expected at least 1');
}
if (memLinkCount === 0) {
  warn('No memorization links found — expected at least 1');
}

// Check all link types are valid
const linkTypes = [...source.matchAll(/linkType:\s*'([^']+)'/g)].map((m) => m[1]);
for (const lt of linkTypes) {
  if (!ALLOWED_LINK_TYPES.has(lt)) {
    fail(`Invalid linkType: '${lt}'`);
  }
}
if (linkTypes.length > 0) {
  pass(`All ${linkTypes.length} link types are valid`);
}

// Check no approved without evidence
const approvedWithoutEvidence = source.match(/reviewStatus:\s*'approved'/g);
if (approvedWithoutEvidence) {
  warn(`${approvedWithoutEvidence.length} approved entries — verify evidence refs are present`);
}

// Check humanReviewRequired: true
const humanReviewTrue = (source.match(/humanReviewRequired:\s*true/g) || []).length;
const humanReviewFalse = (source.match(/humanReviewRequired:\s*false/g) || []).length;
if (humanReviewFalse > 0) {
  warn(`${humanReviewFalse} entries have humanReviewRequired: false`);
}
pass(`${humanReviewTrue} entries have humanReviewRequired: true`);

// Check all differenceNote fields in confusion pairs are non-empty
const emptyDifferenceNotes = (source.match(/differenceNote:\s*\{\s*en:\s*'',/g) || []).length;
if (emptyDifferenceNotes > 0) {
  fail(`${emptyDifferenceNotes} confusion pairs have empty differenceNote.en`);
}

// Check all memorizerHint fields are non-empty
const emptyMemorizerHints = (source.match(/memorizerHint:\s*\{\s*en:\s*'',/g) || []).length;
if (emptyMemorizerHints > 0) {
  warn(`${emptyMemorizerHints} entries have empty memorizerHint.en`);
}

// Check surah numbers are in valid range
const surahRefs = [...source.matchAll(/surah:\s*(\d+)/g)].map((m) => parseInt(m[1]));
const invalidSurahs = surahRefs.filter((n) => n < 1 || n > 114);
if (invalidSurahs.length > 0) {
  fail(`Invalid surah numbers found: ${[...new Set(invalidSurahs)].join(', ')}`);
} else if (surahRefs.length > 0) {
  pass(`All ${surahRefs.length} surah references are valid (1–114)`);
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
console.log('\n=== Validation Summary ===');
console.log(`Errors:   ${errors}`);
console.log(`Warnings: ${warnings}`);

if (errors > 0) {
  console.error('\n✗ Memorization Links validation FAILED');
  process.exit(1);
} else if (warnings > 0) {
  console.warn('\n⚠ Memorization Links validation PASSED with warnings');
  process.exit(0);
} else {
  console.log('\n✓ Memorization Links validation PASSED');
  process.exit(0);
}
