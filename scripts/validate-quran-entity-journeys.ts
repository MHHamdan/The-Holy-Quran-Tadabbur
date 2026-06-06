#!/usr/bin/env npx tsx
/**
 * Validator: quranEntityJourneys.json
 *
 * Checks:
 *   - file loads, totalEntities > 0
 *   - every entity has all four stages (mushaf, story_world, revelation,
 *     thematic) OR has a reason warning
 *   - story_world certainty is not "high" unless a verified source attached
 *   - revelation_order journeys with no source must warn
 *   - every section has at least one ayahReference
 *   - every ayahReference is in range
 *   - thematic_order for Maryam has at least 5 sections (deep journey)
 *
 * Exit code 0 on pass, 1 on fail.
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import type { EntityJourneyOutput } from '../frontend/src/types/quranEntityGraph';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranEntityJourneys.json');

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
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as EntityJourneyOutput;
  const errors: string[] = [];
  const warnings: string[] = [];

  if (out.totalEntities === 0) errors.push('totalEntities=0');

  for (const [entityId, stages] of Object.entries(out.journeys)) {
    for (const stage of ['mushaf_order', 'story_world', 'revelation_order', 'thematic_order'] as const) {
      const j = stages?.[stage];
      if (!j) {
        warnings.push(`${entityId} missing stage ${stage}`);
        continue;
      }
      if (stage === 'story_world' && j.certainty === 'high') {
        errors.push(`${entityId} story_world cannot be certainty=high without verified source`);
      }
      if (stage === 'revelation_order') {
        if (j.sourceIds.length === 0 && j.warnings.length === 0) {
          errors.push(`${entityId} revelation_order has no sourceIds and no warnings`);
        }
      }
      for (const sec of j.sections) {
        if (sec.ayahReferences.length === 0) {
          errors.push(`${entityId}/${stage}/${sec.sectionId}: empty ayahReferences`);
        }
        for (const ref of sec.ayahReferences) {
          if (ref.surahNumber < 1 || ref.surahNumber > 114) {
            errors.push(`${sec.sectionId}: surah out of range ${ref.surahNumber}`);
            continue;
          }
          const maxA = AYAHS_PER_SURAH[ref.surahNumber];
          if (ref.ayahStart < 1 || ref.ayahStart > maxA) {
            errors.push(`${sec.sectionId}: ayahStart=${ref.ayahStart} out of range`);
          }
        }
      }
    }
  }

  // Maryam thematic deep journey
  const maryam = out.journeys['entity_person_maryam'];
  if (maryam) {
    const th = maryam.thematic_order;
    if (!th || th.sections.length < 5) {
      errors.push(`Maryam thematic_order must have ≥5 sections (got ${th?.sections.length ?? 0})`);
    }
  }

  if (warnings.length) for (const w of warnings) console.warn(`WARN  - ${w}`);
  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`OK — entities=${out.totalEntities}`);
}

main();
