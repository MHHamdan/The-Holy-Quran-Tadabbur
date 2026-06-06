#!/usr/bin/env npx tsx
/**
 * Validator: quranEntityRelations.json
 *
 * Checks:
 *   - file loads, totalRelations > 0
 *   - every relation has evidenceReferences with at least 1 entry
 *   - every evidence ayah is in range
 *   - every relation has source/target entityIds that exist in seed dictionary
 *   - every relation has a known relationType
 *   - every relation has reviewStatus + humanReviewRequired
 *   - theological_discussion relations are needs_review
 *   - Maryam–Isa relation exists with at least mother_of and theological_discussion
 *   - Maryam–Zakariyya relation exists with family_of or guardian_of
 *   - all sourceIds map to sourceRegistry
 *
 * Exit code 0 on pass, 1 on fail.
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { QURAN_ENTITY_SEEDS } from '../frontend/src/data/quranEntitySeeds';
import { SOURCE_REGISTRY } from '../frontend/src/data/sourceRegistry';
import type { EntityRelationOutput, EntityRelationType } from '../frontend/src/types/quranEntityGraph';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranEntityRelations.json');

const AYAHS_PER_SURAH: Record<number, number> = {
  1:7,2:286,3:200,4:176,5:120,6:165,7:206,8:75,9:129,10:109,11:123,12:111,13:43,14:52,15:99,
  16:128,17:111,18:110,19:98,20:135,21:112,22:78,23:118,24:64,25:77,26:227,27:93,28:88,29:69,30:60,
  31:34,32:30,33:73,34:54,35:45,36:83,37:182,38:88,39:75,40:85,41:54,42:53,43:89,44:59,45:37,46:35,
  47:38,48:29,49:18,50:45,51:60,52:49,53:62,54:55,55:78,56:96,57:29,58:22,59:24,60:13,61:14,62:11,
  63:11,64:18,65:12,66:12,67:30,68:52,69:52,70:44,71:28,72:28,73:20,74:56,75:40,76:31,77:50,78:40,
  79:46,80:42,81:29,82:19,83:36,84:25,85:22,86:17,87:19,88:26,89:30,90:20,91:15,92:21,93:11,94:8,
  95:8,96:19,97:5,98:8,99:8,100:11,101:11,102:8,103:3,104:9,105:5,106:4,107:7,108:3,109:6,110:3,
  111:5,112:4,113:5,114:6,
};

const VALID_RELATION_TYPES: ReadonlyArray<EntityRelationType> = [
  'mother_of','son_of','father_of','daughter_of','wife_of','husband_of',
  'brother_of','sister_of','guardian_of','family_of','same_story','same_event',
  'same_surah_context','theological_discussion','chronological_before',
  'chronological_after','related_theme','related_tafsir','mentioned_with',
];

function main(): void {
  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as EntityRelationOutput;
  const errors: string[] = [];
  const warnings: string[] = [];

  if (out.totalRelations === 0) errors.push('totalRelations=0');
  if (!Array.isArray(out.relations) || out.relations.length === 0) errors.push('relations[] is empty');

  const seedIds = new Set(QURAN_ENTITY_SEEDS.map((s) => s.entityId));
  const validSourceIds = new Set(SOURCE_REGISTRY.map((s) => s.sourceId));
  const validRelTypes = new Set<string>(VALID_RELATION_TYPES);

  for (const r of out.relations) {
    if (!seedIds.has(r.sourceEntityId)) errors.push(`Unknown source entityId: ${r.sourceEntityId}`);
    if (!seedIds.has(r.targetEntityId)) errors.push(`Unknown target entityId: ${r.targetEntityId}`);
    if (r.sourceEntityId === r.targetEntityId) errors.push(`Self-loop: ${r.sourceEntityId}`);
    if (!validRelTypes.has(r.relationType)) errors.push(`Unknown relationType: ${r.relationType}`);
    if (!Array.isArray(r.evidenceReferences) || r.evidenceReferences.length === 0) {
      errors.push(`${r.sourceEntityId}->${r.targetEntityId} (${r.relationType}): missing evidenceReferences`);
    } else {
      for (const ev of r.evidenceReferences) {
        if (ev.surahNumber < 1 || ev.surahNumber > 114) {
          errors.push(`Evidence surah out of range: ${ev.surahNumber}`);
          continue;
        }
        const maxA = AYAHS_PER_SURAH[ev.surahNumber];
        if (ev.ayahStart < 1 || ev.ayahStart > maxA) {
          errors.push(`Evidence ayahStart=${ev.ayahStart} out of range for surah ${ev.surahNumber}`);
        }
        if (ev.ayahEnd && (ev.ayahEnd < ev.ayahStart || ev.ayahEnd > maxA)) {
          errors.push(`Evidence ayahEnd=${ev.ayahEnd} out of range for surah ${ev.surahNumber}`);
        }
      }
    }
    if (!r.reviewStatus) errors.push(`Missing reviewStatus on ${r.sourceEntityId}->${r.targetEntityId}`);
    if (typeof r.humanReviewRequired !== 'boolean') {
      errors.push(`Missing humanReviewRequired on ${r.sourceEntityId}->${r.targetEntityId}`);
    }
    if (r.relationType === 'theological_discussion' && r.reviewStatus !== 'needs_review') {
      errors.push(`theological_discussion must be needs_review: ${r.sourceEntityId}->${r.targetEntityId}`);
    }
    for (const sid of r.sourceIds) {
      if (!validSourceIds.has(sid)) errors.push(`Unknown sourceId "${sid}" on ${r.sourceEntityId}->${r.targetEntityId}`);
    }
  }

  // Maryam-specific checks
  const maryamIsa = out.relations.filter(
    (r) =>
      (r.sourceEntityId === 'entity_person_maryam' && r.targetEntityId === 'entity_prophet_isa') ||
      (r.sourceEntityId === 'entity_prophet_isa' && r.targetEntityId === 'entity_person_maryam')
  );
  const hasMother = maryamIsa.some((r) => r.relationType === 'mother_of' || r.relationType === 'son_of');
  const hasTheo = maryamIsa.some((r) => r.relationType === 'theological_discussion');
  if (!hasMother) errors.push('Missing Maryam–Isa mother_of/son_of relation');
  if (!hasTheo) errors.push('Missing Maryam–Isa theological_discussion relation');

  const maryamZak = out.relations.filter(
    (r) =>
      (r.sourceEntityId === 'entity_person_maryam' && r.targetEntityId === 'entity_prophet_zakariyya') ||
      (r.sourceEntityId === 'entity_prophet_zakariyya' && r.targetEntityId === 'entity_person_maryam')
  );
  const hasFamilyOrGuardian = maryamZak.some(
    (r) => r.relationType === 'family_of' || r.relationType === 'guardian_of'
  );
  if (!hasFamilyOrGuardian) errors.push('Missing Maryam–Zakariyya family_of/guardian_of relation');

  if (warnings.length) for (const w of warnings) console.warn(`WARN  - ${w}`);
  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`OK — relations=${out.totalRelations}, entities=${out.totalEntitiesInvolved}`);
}

main();
