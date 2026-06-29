/**
 * Validator: quranicCallsClassified.json
 * Exits 0 if valid, 1 otherwise.
 */
import { readFileSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const FILE = join(ROOT, 'frontend/src/data/generated/quranicCallsClassified.json');

let errors = 0;

function error(msg: string) { console.error(`  ✗ ERROR: ${msg}`); errors++; }

console.log('Validating quranicCallsClassified.json…');

let data: Record<string, unknown>;
try {
  data = JSON.parse(readFileSync(FILE, 'utf-8'));
} catch (e) {
  error(`Cannot parse JSON: ${e}`);
  process.exit(1);
}

for (const f of ['version', 'classifiedAt', 'totalClassified', 'calls', 'classificationSummary']) {
  if (!(f in data)) error(`Missing field: ${f}`);
}

const calls = (data.calls ?? []) as Record<string, unknown>[];
if (!Array.isArray(calls)) { error('calls must be an array'); process.exit(1); }
if (calls.length === 0) error('calls array is empty');

const VALID_METHODS = new Set(['rule_based', 'topic_signal', 'entity_signal', 'unclassified']);

for (let i = 0; i < calls.length; i++) {
  const c = calls[i];
  const ref = c.ayahReference ?? `[${i}]`;

  if (!c.callId) error(`[${ref}] Missing callId`);
  if (c.humanReviewRequired !== true) error(`[${ref}] humanReviewRequired must be true`);
  if (c.reviewStatus !== 'needs_review') error(`[${ref}] reviewStatus must be needs_review`);
  if (!c.classificationMethod) error(`[${ref}] Missing classificationMethod`);
  if (!VALID_METHODS.has(c.classificationMethod as string))
    error(`[${ref}] Invalid classificationMethod: ${c.classificationMethod}`);
  if (!Array.isArray(c.classificationSignals)) error(`[${ref}] classificationSignals must be an array`);
}

const total = data.totalClassified as number;
if (Math.abs(total - calls.length) > 2) error(`totalClassified (${total}) != calls.length (${calls.length})`);

console.log(`Validated ${calls.length} classified calls. Errors: ${errors}`);
if (errors > 0) { console.error('✗ Validation FAILED'); process.exit(1); }
console.log('✓ Validation PASSED');
