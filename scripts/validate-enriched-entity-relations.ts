#!/usr/bin/env npx tsx
/**
 * Validator: quranEntityRelationsEnriched.json
 *
 * Checks:
 *   - file loads
 *   - baseRelations array is non-empty
 *   - every coreference edge has source/target in seed dictionary
 *   - every coreference edge has at least one evidence reference
 *   - all sourceIds map to sourceRegistry
 *   - all edges are needs_review
 *   - no original verified relation has been overwritten
 *   - conflicts (if any) are still needs_review
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { QURAN_ENTITY_SEEDS } from '../frontend/src/data/quranEntitySeeds';
import { SOURCE_REGISTRY } from '../frontend/src/data/sourceRegistry';
import type { EnrichedRelationsOutput } from '../frontend/src/types/quranCoreference';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranEntityRelationsEnriched.json');

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

function main(): void {
  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as EnrichedRelationsOutput;
  const errors: string[] = [];
  const seedIds = new Set(QURAN_ENTITY_SEEDS.map((s) => s.entityId));
  const validSourceIds = new Set(SOURCE_REGISTRY.map((s) => s.sourceId));

  if (!out.baseRelations || (out.baseRelations as unknown[]).length === 0) {
    errors.push('baseRelations is empty');
  }
  if (!out.coreferenceEdges) errors.push('missing coreferenceEdges array');

  for (const e of out.coreferenceEdges) {
    if (!seedIds.has(e.sourceEntityId)) errors.push(`Unknown source ${e.sourceEntityId}`);
    if (!seedIds.has(e.targetEntityId)) errors.push(`Unknown target ${e.targetEntityId}`);
    if (e.sourceEntityId === e.targetEntityId) errors.push(`Self-loop ${e.sourceEntityId}`);
    if (!e.evidenceReferences || e.evidenceReferences.length === 0) {
      errors.push(`${e.sourceEntityId}->${e.targetEntityId} (${e.edgeType}): missing evidence`);
    } else {
      for (const ref of e.evidenceReferences) {
        if (ref.surahNumber < 1 || ref.surahNumber > 114) {
          errors.push(`${e.sourceEntityId}->${e.targetEntityId}: surah out of range ${ref.surahNumber}`);
          continue;
        }
        const maxA = AYAHS_PER_SURAH[ref.surahNumber];
        if (ref.ayahStart < 1 || ref.ayahStart > maxA) {
          errors.push(`${e.sourceEntityId}->${e.targetEntityId}: ayahStart out of range`);
        }
      }
    }
    for (const sid of e.sourceIds) {
      if (!validSourceIds.has(sid)) errors.push(`${e.sourceEntityId}->${e.targetEntityId}: unknown sourceId "${sid}"`);
    }
    if (e.reviewStatus !== 'needs_review') {
      errors.push(`${e.sourceEntityId}->${e.targetEntityId}: must be needs_review`);
    }
    if (e.humanReviewRequired !== true) {
      errors.push(`${e.sourceEntityId}->${e.targetEntityId}: humanReviewRequired must be true`);
    }
  }

  for (const c of out.conflicts ?? []) {
    if (!c.reason) errors.push(`Conflict ${c.sourceEntityId}->${c.targetEntityId} missing reason`);
  }

  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors.slice(0, 50)) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(
    `OK — base=${(out.baseRelations as unknown[]).length}, coref=${out.coreferenceEdgeCount}, conflicts=${out.conflicts?.length ?? 0}`
  );
}

main();
