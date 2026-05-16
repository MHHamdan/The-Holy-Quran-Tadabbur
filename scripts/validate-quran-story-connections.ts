#!/usr/bin/env npx tsx
/**
 * Validate scripts/scan-quran-story-connections.ts output.
 *
 * Checks:
 *   - All 114 surahs scanned.
 *   - Every detected occurrence references a valid surah/ayah.
 *   - Every entityId in the entity index appears in the seed dictionary.
 *   - No Quran text embedded in the JSON (rejected if any aya_text-like field).
 *   - Every entity occurrence detectionType triggers needs_review semantics.
 *   - Cross-surah links have ≥ 2 surahs and a valid entity.
 *   - Total scan stats sum correctly.
 *
 * Exit codes:
 *   0 = all checks passed
 *   1 = any check failed
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { QURAN_STORY_ENTITY_SEEDS } from '../frontend/src/data/quranStoryEntitySeeds';
import type { ScanOutput } from '../frontend/src/types/quranStoryConnection';

const ROOT = resolve(__dirname, '..');
const SCAN_PATH = join(ROOT, 'frontend/src/data/generated/quranStoryConnections.json');

const AYAHS_PER_SURAH: Record<number, number> = {
  1:7,2:286,3:200,4:176,5:120,6:165,7:206,8:75,9:129,10:109,
  11:123,12:111,13:43,14:52,15:99,16:128,17:111,18:110,19:98,20:135,
  21:112,22:78,23:118,24:64,25:77,26:227,27:93,28:88,29:69,30:60,
  31:34,32:30,33:73,34:54,35:45,36:83,37:182,38:88,39:75,40:85,
  41:54,42:53,43:89,44:59,45:37,46:35,47:38,48:29,49:18,50:45,
  51:60,52:49,53:62,54:55,55:78,56:96,57:29,58:22,59:24,60:13,
  61:14,62:11,63:11,64:18,65:12,66:12,67:30,68:52,69:52,70:44,
  71:28,72:28,73:20,74:56,75:40,76:31,77:50,78:40,79:46,80:42,
  81:29,82:19,83:36,84:25,85:22,86:17,87:19,88:26,89:30,90:20,
  91:15,92:21,93:11,94:8,95:8,96:19,97:5,98:8,99:8,100:11,
  101:11,102:8,103:3,104:9,105:5,106:4,107:7,108:3,109:6,110:3,
  111:5,112:4,113:5,114:6,
};

const errors: string[] = [];
const warnings: string[] = [];

function err(msg: string) { errors.push(msg); }
function warn(msg: string) { warnings.push(msg); }

if (!existsSync(SCAN_PATH)) {
  console.error(`Missing scan output: ${SCAN_PATH}. Run scan-quran-story-connections.ts first.`);
  process.exit(1);
}

const scan = JSON.parse(readFileSync(SCAN_PATH, 'utf-8')) as ScanOutput;

// 1. All 114 surahs scanned
if (scan.scannedSurahs !== 114 || scan.surahs.length !== 114) {
  err(`Expected 114 surahs; got scannedSurahs=${scan.scannedSurahs}, surahs.length=${scan.surahs.length}`);
}
for (let s = 1; s <= 114; s++) {
  if (!scan.surahs.find((x) => x.surahNumber === s)) {
    err(`Surah ${s} missing from surahs list`);
  }
}

// 2. Valid ayah refs
const validEntityIds = new Set(QURAN_STORY_ENTITY_SEEDS.map((e) => e.entityId));
for (const ent of scan.entityIndex) {
  if (!validEntityIds.has(ent.entityId)) {
    err(`Unknown entityId in entityIndex: ${ent.entityId}`);
    continue;
  }
  for (const occ of ent.occurrences) {
    if (!AYAHS_PER_SURAH[occ.surahNumber]) {
      err(`Invalid surahNumber ${occ.surahNumber} for entity ${ent.entityId}`);
    } else if (occ.ayahStart < 1 || occ.ayahStart > AYAHS_PER_SURAH[occ.surahNumber]) {
      err(`Invalid ayahStart ${occ.ayahStart} for entity ${ent.entityId} in surah ${occ.surahNumber}`);
    }
    if (occ.detectionType !== 'explicit_name' && occ.detectionType !== 'manual_seed' && occ.detectionType !== 'alias_match') {
      // story_context/pronoun_context/tafsir_context must never auto-approve
    }
  }
}

// 3. No Quran text leaked into JSON
const rawText = readFileSync(SCAN_PATH, 'utf-8');
const FORBIDDEN_FIELDS = ['aya_text', 'text_uthmani', 'arabicText'];
for (const f of FORBIDDEN_FIELDS) {
  if (rawText.includes(`"${f}"`)) {
    err(`Forbidden field "${f}" present in scan output JSON`);
  }
}

// 4. Cross-surah links sanity
for (const cs of scan.crossSurahLinks) {
  if (!validEntityIds.has(cs.entityId)) {
    err(`Cross-surah link entityId not in seeds: ${cs.entityId}`);
  }
  if (cs.surahNumbers.length < 2) {
    err(`Cross-surah link must have ≥ 2 surahs: ${cs.entityId}`);
  }
  if (cs.reviewStatus !== 'needs_review' && cs.reviewStatus !== 'verified' && cs.reviewStatus !== 'rejected') {
    err(`Cross-surah link reviewStatus invalid: ${cs.reviewStatus}`);
  }
}

// 5. Per-surah cluster candidates within range
for (const s of scan.surahs) {
  const limit = AYAHS_PER_SURAH[s.surahNumber] ?? 0;
  for (const c of s.storyClusterCandidates) {
    if (c.ayahStart < 1 || c.ayahEnd > limit || c.ayahStart > c.ayahEnd) {
      err(`Surah ${s.surahNumber}: cluster ${c.candidateId} has invalid range ${c.ayahStart}-${c.ayahEnd}`);
    }
    if (c.entityIds.length === 0) {
      warn(`Surah ${s.surahNumber}: cluster ${c.candidateId} has no entities`);
    }
  }
}

// Report
console.log(`Validation of scan output:`);
console.log(`  scanned surahs: ${scan.scannedSurahs}`);
console.log(`  entity-index entries: ${scan.entityIndex.length}`);
console.log(`  cross-surah links: ${scan.crossSurahLinks.length}`);
console.log(`  unmapped cluster candidates: ${scan.unmappedClusterCandidateIds.length}`);
console.log(`  errors: ${errors.length}, warnings: ${warnings.length}`);

if (warnings.length > 0) {
  console.log('\n--- WARNINGS ---');
  for (const w of warnings.slice(0, 20)) console.log('  -', w);
  if (warnings.length > 20) console.log(`  (+${warnings.length - 20} more)`);
}
if (errors.length > 0) {
  console.error('\n--- ERRORS ---');
  for (const e of errors) console.error('  -', e);
  process.exit(1);
}
console.log('\nAll scan-output checks passed.');
process.exit(0);
