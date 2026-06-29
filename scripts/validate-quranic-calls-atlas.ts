/**
 * Validator: quranicCallsAtlas.json
 *
 * Exits 0 if valid, 1 if any structural/integrity errors found.
 * Usage: npx tsx scripts/validate-quranic-calls-atlas.ts
 */
import { readFileSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const FILE = join(ROOT, 'frontend/src/data/generated/quranicCallsAtlas.json');

let errors = 0;
let warnings = 0;

function error(msg: string) { console.error(`  ✗ ERROR: ${msg}`); errors++; }
function warn(msg: string)  { console.warn(`  ⚠ WARN:  ${msg}`); warnings++; }

console.log('Validating quranicCallsAtlas.json…');

let atlas: Record<string, unknown>;
try {
  atlas = JSON.parse(readFileSync(FILE, 'utf-8'));
} catch (e) {
  error(`Cannot parse JSON: ${e}`);
  process.exit(1);
}

// Top-level fields
for (const field of ['version', 'generatedAt', 'totalCalls', 'totalAyahsWithCalls', 'statistics', 'calls']) {
  if (!(field in atlas)) error(`Missing top-level field: ${field}`);
}

const calls = (atlas.calls ?? []) as Record<string, unknown>[];
if (!Array.isArray(calls)) { error('calls must be an array'); process.exit(1); }

if (calls.length === 0) error('calls array is empty — scan must have detected at least 1 call');
if (calls.length < 100) warn(`Only ${calls.length} calls — expected ≥ 200 from whole-Quran scan`);

const VALID_PATTERNS = new Set([
  'ya_direct','ya_ayyuhal','ya_ayatuha','ya_bani','ya_qawmi','ya_ibadi','ya_ahl',
  'ya_rabbi','ya_abati','ya_bunayya','ya_prophet_name','ya_lament','ya_wish',
  'supplication','indirect_address','dialogue_address','unknown',
]);
const VALID_ADDRESSEES = new Set([
  'believers','mankind','disbelievers','people_of_book','bani_israel','prophet',
  'specific_person','people_or_nation','family_member','soul','jinn','allah','unknown',
]);
const VALID_CALLERS = new Set([
  'allah','prophet','angel','believer','disbeliever','people_group','family_member',
  'jinn','narrative_speaker','unknown',
]);

const seenIds = new Set<string>();

for (let i = 0; i < calls.length; i++) {
  const c = calls[i];
  const ref = c.ayahReference ?? `index[${i}]`;

  // Required fields
  for (const f of ['callId','surahNumber','ayahNumber','ayahReference','surahNameAr','surahNameEn','ayahTextUthmani','callPattern','caller','addressee','callFunction','tone','confidence','reviewStatus','humanReviewRequired']) {
    if (!(f in c)) error(`[${ref}] Missing field: ${f}`);
  }

  // callId uniqueness
  const cid = c.callId as string;
  if (seenIds.has(cid)) error(`[${ref}] Duplicate callId: ${cid}`);
  seenIds.add(cid);

  // callId format
  if (!/^call_\d+_\d+_\d+$/.test(cid ?? '')) error(`[${ref}] Invalid callId format: ${cid}`);

  // Pattern valid
  if (!VALID_PATTERNS.has(c.callPattern as string)) error(`[${ref}] Unknown callPattern: ${c.callPattern}`);

  // Addressee structure
  const addr = c.addressee as Record<string, unknown>;
  if (!addr || typeof addr !== 'object') { error(`[${ref}] addressee must be an object`); }
  else {
    if (!VALID_ADDRESSEES.has(addr.addresseeType as string))
      warn(`[${ref}] Unknown addresseeType: ${addr.addresseeType}`);
    if (!addr.labelArabic) error(`[${ref}] addressee.labelArabic is required`);
    if (!addr.labelEnglish) error(`[${ref}] addressee.labelEnglish is required`);
  }

  // Caller structure
  const caller = c.caller as Record<string, unknown>;
  if (!caller || typeof caller !== 'object') { error(`[${ref}] caller must be an object`); }
  else {
    if (!VALID_CALLERS.has(caller.callerType as string))
      warn(`[${ref}] Unknown callerType: ${caller.callerType}`);
    if (typeof caller.confidence !== 'number') error(`[${ref}] caller.confidence must be a number`);
  }

  // reviewStatus + humanReviewRequired must always be correct defaults
  if (c.reviewStatus !== 'needs_review')
    warn(`[${ref}] reviewStatus is not 'needs_review' — was it manually overridden?`);
  if (c.humanReviewRequired !== true)
    error(`[${ref}] humanReviewRequired must be true for all auto-scanned calls`);

  // Ayah text must not be empty (we never modify it)
  if (!c.ayahTextUthmani || (c.ayahTextUthmani as string).trim() === '')
    error(`[${ref}] ayahTextUthmani is empty`);

  // Surah number in valid range
  const sn = c.surahNumber as number;
  if (typeof sn !== 'number' || sn < 1 || sn > 114) error(`[${ref}] surahNumber out of range: ${sn}`);

  // Confidence in range
  const conf = c.confidence as number;
  if (typeof conf !== 'number' || conf < 0 || conf > 1) error(`[${ref}] confidence out of range: ${conf}`);
}

// Statistics cross-check
const stats = atlas.statistics as Record<string, unknown>;
if (stats && typeof stats.totalWarnings === 'number' && stats.totalWarnings < 0) {
  error('statistics.totalWarnings cannot be negative');
}
const statTotal = (atlas.totalCalls as number) ?? 0;
if (Math.abs(statTotal - calls.length) > 5) {
  warn(`totalCalls (${statTotal}) diverges from calls.length (${calls.length}) by > 5`);
}

console.log('');
console.log(`Validated ${calls.length} calls`);
console.log(`Errors:   ${errors}`);
console.log(`Warnings: ${warnings}`);

if (errors > 0) {
  console.error('\n✗ Validation FAILED');
  process.exit(1);
}
console.log('\n✓ Validation PASSED');
