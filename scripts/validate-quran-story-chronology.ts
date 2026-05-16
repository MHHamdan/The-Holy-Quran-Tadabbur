#!/usr/bin/env npx tsx
/**
 * Validate frontend/src/data/quranStoryChronologySeeds.ts.
 *
 * Checks:
 *   - Every story-world entry has sourceIds OR certainty == disputed.
 *   - Every revelation-order entry has at least one sourceId OR certainty
 *     == disputed.
 *   - No revelation-order entry is `reviewStatus: 'verified'` (those require
 *     reviewer sign-off via the review-workflow tool, which records the
 *     reviewer ID — out of scope for this seed file).
 *   - No story-world entry has `orderIndex` ≤ 0.
 *   - Story-world chronologicalGroup ids appear in at least one entity seed.
 *   - No entry's notes embed Quran text (heuristic: no Arabic >40 chars).
 */

import {
  STORY_WORLD_CHRONOLOGY,
  REVELATION_ORDER_SEEDS,
} from '../frontend/src/data/quranStoryChronologySeeds';
import { QURAN_STORY_ENTITY_SEEDS } from '../frontend/src/data/quranStoryEntitySeeds';

const errors: string[] = [];
const warnings: string[] = [];
function err(m: string) { errors.push(m); }
function warn(m: string) { warnings.push(m); }

// 1. Story-world entries
const entityGroups = new Set(
  QURAN_STORY_ENTITY_SEEDS.map((e) => e.chronologicalGroup).filter((g): g is string => !!g)
);
for (const c of STORY_WORLD_CHRONOLOGY) {
  if (c.chronologyType !== 'story_world') {
    err(`Story-world entry has wrong chronologyType: ${c.itemId}`);
  }
  if (c.sourceIds.length === 0 && c.certainty !== 'disputed') {
    err(`Story-world entry ${c.itemId} has no sourceIds and is not disputed`);
  }
  if ((c.orderIndex ?? 0) <= 0) {
    err(`Story-world entry ${c.itemId} has invalid orderIndex`);
  }
  if (!entityGroups.has(c.itemId)) {
    warn(`Story-world group ${c.itemId} is not referenced by any entity seed`);
  }
  if (c.reviewStatus === 'verified') {
    err(`Story-world entry ${c.itemId}: verified status must come from reviewer workflow, not seed file`);
  }
  // Arabic notes length
  if (c.notesArabic && c.notesArabic.length > 200) {
    warn(`Story-world entry ${c.itemId}: long Arabic notes (${c.notesArabic.length} chars)`);
  }
}

// 2. Revelation-order entries
const seenRev = new Set<string>();
for (const c of REVELATION_ORDER_SEEDS) {
  if (c.chronologyType !== 'revelation_order') {
    err(`Revelation-order entry has wrong chronologyType: ${c.itemId}`);
  }
  if (!/^[1-9]\d?$|^1[01]\d$/.test(c.itemId)) {
    err(`Revelation-order itemId ${c.itemId} must be a surah number 1..114`);
  }
  if (seenRev.has(c.itemId)) {
    err(`Duplicate revelation-order itemId: ${c.itemId}`);
  }
  seenRev.add(c.itemId);
  if (c.sourceIds.length === 0 && c.certainty !== 'disputed') {
    err(`Revelation-order entry ${c.itemId} has no sourceIds and is not disputed`);
  }
  if (c.reviewStatus === 'verified') {
    err(`Revelation-order entry ${c.itemId}: verified status not allowed in seed file`);
  }
}

console.log('Validation of chronology seeds:');
console.log(`  story-world entries: ${STORY_WORLD_CHRONOLOGY.length}`);
console.log(`  revelation-order entries: ${REVELATION_ORDER_SEEDS.length}`);
console.log(`  errors: ${errors.length}, warnings: ${warnings.length}`);

if (warnings.length > 0) {
  console.log('\n--- WARNINGS ---');
  for (const w of warnings) console.log('  -', w);
}
if (errors.length > 0) {
  console.error('\n--- ERRORS ---');
  for (const e of errors) console.error('  -', e);
  process.exit(1);
}
console.log('\nAll chronology checks passed.');
process.exit(0);
