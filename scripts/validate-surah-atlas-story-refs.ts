#!/usr/bin/env npx tsx
/**
 * Validate Surah Atlas `mention_only` story references.
 *
 * A `coverage: 'mention_only'` reference claims that the story's prophet /
 * nation is named in the cited ayah range. This validator checks that claim
 * against Quranic Arabic Corpus proper-noun (POS:PN) lemma tags:
 *
 *   - QAC morphology present (data/raw/quranic-corpus-morphology.txt,
 *     untracked) → use QAC directly.
 *   - otherwise → fall back to the QAC-derived explicit_name mentions in
 *     frontend/src/data/generated/quranEntityMentions.json.
 *
 * Fails (exit 1) when a mention_only ref has no matching lemma in
 * [start, end], when its storyId has no entity mapping, or when its range is
 * missing.
 *
 * Usage: npx tsx scripts/validate-surah-atlas-story-refs.ts [--list]
 */

import { readFileSync } from 'fs';
import { join, resolve } from 'path';
import { SURAH_ATLAS_DATA } from '../frontend/src/data/surahAtlas';
import { loadQacProperNounIndex, qacAyahsForEntity } from './qac-proper-noun-lemmas';

const ROOT = resolve(__dirname, '..');
const MENTIONS_PATH = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');

/** storyId → entities whose being named in the range supports a mention_only ref. */
export const STORY_ENTITY_MAP: Record<string, string[]> = {
  story_adam: ['entity_prophet_adam'],
  story_nuh: ['entity_prophet_nuh'],
  story_hud: ['entity_prophet_hud', 'entity_people_aad'],
  story_ad: ['entity_people_aad', 'entity_prophet_hud'],
  story_salih: ['entity_prophet_salih', 'entity_people_thamud'],
  story_thamud: ['entity_people_thamud', 'entity_prophet_salih'],
  story_ibrahim: ['entity_prophet_ibrahim'],
  story_lut: ['entity_prophet_lut'],
  story_ismail: ['entity_prophet_ismail'],
  story_shuayb: ['entity_prophet_shuayb', 'entity_people_madyan'],
  story_musa: ['entity_prophet_musa'],
  story_dawud: ['entity_prophet_dawud'],
  story_sulayman: ['entity_prophet_sulayman'],
  story_ayyub: ['entity_prophet_ayyub'],
  story_yunus: ['entity_prophet_yunus'],
  story_zakariyya_yahya: ['entity_prophet_zakariyya', 'entity_prophet_yahya'],
  story_isa: ['entity_prophet_isa'],
  story_ancient_egypt: ['entity_person_firawn', 'entity_place_egypt'],
};

type AyahSetLookup = (entityId: string) => Set<string> | null;

function buildLookup(): { lookup: AyahSetLookup; source: string } {
  const qac = loadQacProperNounIndex();
  if (qac) return { lookup: (id) => qacAyahsForEntity(id, qac), source: 'QAC morphology' };
  const mentions = JSON.parse(readFileSync(MENTIONS_PATH, 'utf-8')) as {
    entities: Array<{
      entityId: string;
      mentions: Array<{ surahNumber: number; ayahNumber: number; mentionType: string; sourceIds: string[] }>;
    }>;
  };
  const byId = new Map<string, Set<string>>();
  for (const e of mentions.entities) {
    const set = new Set<string>();
    for (const m of e.mentions) {
      if (m.mentionType === 'explicit_name' && m.sourceIds.includes('quranic_arabic_corpus')) {
        set.add(`${m.surahNumber}:${m.ayahNumber}`);
      }
    }
    byId.set(e.entityId, set);
  }
  return { lookup: (id) => byId.get(id) ?? null, source: 'quranEntityMentions.json (QAC-derived)' };
}

export interface RefFailure {
  surahNumber: number;
  storyId: string;
  display: string;
  reason: string;
}

export function checkSurahAtlasStoryRefs(lookup: AyahSetLookup): { checked: number; failures: RefFailure[] } {
  const failures: RefFailure[] = [];
  let checked = 0;
  for (const entry of SURAH_ATLAS_DATA) {
    for (const ref of entry.storiesMentioned ?? []) {
      if (ref.coverage !== 'mention_only') continue;
      checked++;
      const base = { surahNumber: entry.surahNumber, storyId: ref.storyId, display: ref.ayahRange.display };
      const entities = STORY_ENTITY_MAP[ref.storyId];
      if (!entities) {
        failures.push({ ...base, reason: 'storyId has no entity mapping — cannot verify a mention_only ref' });
        continue;
      }
      const { start, end } = ref.ayahRange;
      if (typeof start !== 'number' || typeof end !== 'number') {
        failures.push({ ...base, reason: 'mention_only ref without numeric ayah range' });
        continue;
      }
      let found = false;
      for (const id of entities) {
        const set = lookup(id);
        if (!set) continue;
        for (let a = start; a <= end && !found; a++) {
          if (set.has(`${entry.surahNumber}:${a}`)) found = true;
        }
        if (found) break;
      }
      if (!found) failures.push({ ...base, reason: `none of ${entities.join(', ')} is named in ${entry.surahNumber}:${start}-${end}` });
    }
  }
  return { checked, failures };
}

function main(): void {
  const { lookup, source } = buildLookup();
  const { checked, failures } = checkSurahAtlasStoryRefs(lookup);
  console.log(`Surah Atlas mention_only refs checked: ${checked} (source: ${source})`);
  if (failures.length > 0) {
    console.error(`FAILED: ${failures.length} unsupported mention_only refs`);
    for (const f of failures) console.error(`  - surah ${f.surahNumber} ${f.storyId} ${f.display}: ${f.reason}`);
    process.exit(1);
  }
  console.log('All mention_only refs are supported by a proper-noun mention in range.');
}

main();
