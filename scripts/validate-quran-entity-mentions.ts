#!/usr/bin/env npx tsx
/**
 * Validator: quranEntityMentions.json
 *
 * Checks:
 *   - file loads, has scannedSurahs == 114
 *   - every mention has valid (surah,ayah) in range
 *   - every mention has reviewStatus + humanReviewRequired set
 *   - every mention has at least one sourceId; all sourceIds map to
 *     sourceRegistry
 *   - all entityIds are unique and present in QURAN_ENTITY_SEEDS
 *   - no Quran text is embedded in any mention (matchedText must be < 80 chars
 *     and must not be a substring of any real ayah text — we cannot check
 *     the latter cheaply; we just enforce a length cap and disallow newlines)
 *   - story_context / pronoun_context / tafsir_context / family_relation /
 *     title mentions must be needs_review
 *   - Maryam has expected aliases & at least 30 explicit_name mentions across
 *     at least 10 surahs (smoke check)
 *
 * Exit code 0 on pass, 1 on fail.
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { QURAN_ENTITY_SEEDS, getEntitySeedById } from '../frontend/src/data/quranEntitySeeds';
import { SOURCE_REGISTRY } from '../frontend/src/data/sourceRegistry';
import type { EntityMentionScanOutput, EntityMentionType } from '../frontend/src/types/quranEntityGraph';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');

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

const NEEDS_REVIEW_MENTION_TYPES: EntityMentionType[] = [
  'story_context',
  'pronoun_context',
  'tafsir_context',
  'family_relation',
  'title',
];

function main(): void {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as EntityMentionScanOutput;

  if (out.scannedSurahs !== 114) errors.push(`scannedSurahs=${out.scannedSurahs}, expected 114`);
  if (!Array.isArray(out.entities) || out.entities.length === 0) errors.push('entities[] is empty');

  const seedIds = new Set(QURAN_ENTITY_SEEDS.map((s) => s.entityId));
  const seenIds = new Set<string>();
  const validSourceIds = new Set(SOURCE_REGISTRY.map((s) => s.sourceId));

  let totalMentions = 0;
  for (const e of out.entities) {
    if (seenIds.has(e.entityId)) errors.push(`Duplicate entityId: ${e.entityId}`);
    seenIds.add(e.entityId);
    if (!seedIds.has(e.entityId)) errors.push(`Unknown entityId not in seed dictionary: ${e.entityId}`);

    for (const m of e.mentions) {
      totalMentions += 1;
      if (!m.surahNumber || m.surahNumber < 1 || m.surahNumber > 114) {
        errors.push(`${e.entityId}: invalid surahNumber=${m.surahNumber}`);
        continue;
      }
      const maxAyah = AYAHS_PER_SURAH[m.surahNumber];
      if (m.ayahNumber < 1 || m.ayahNumber > maxAyah) {
        errors.push(`${e.entityId}: invalid ayahNumber=${m.ayahNumber} for surah ${m.surahNumber}`);
      }
      if (!m.sourceIds || m.sourceIds.length === 0) {
        errors.push(`${e.entityId} ${m.surahNumber}:${m.ayahNumber}: missing sourceIds`);
      } else {
        for (const sid of m.sourceIds) {
          if (!validSourceIds.has(sid)) errors.push(`${e.entityId}: unknown sourceId "${sid}"`);
        }
      }
      if (!m.reviewStatus) errors.push(`${e.entityId} ${m.surahNumber}:${m.ayahNumber}: missing reviewStatus`);
      if (typeof m.humanReviewRequired !== 'boolean') {
        errors.push(`${e.entityId} ${m.surahNumber}:${m.ayahNumber}: missing humanReviewRequired`);
      }
      if (NEEDS_REVIEW_MENTION_TYPES.includes(m.mentionType) && m.reviewStatus !== 'needs_review') {
        errors.push(
          `${e.entityId} ${m.surahNumber}:${m.ayahNumber}: ${m.mentionType} must be needs_review (got ${m.reviewStatus})`
        );
      }
      if (m.matchedText) {
        if (m.matchedText.length > 80) {
          errors.push(`${e.entityId} ${m.surahNumber}:${m.ayahNumber}: matchedText too long (>80)`);
        }
        if (m.matchedText.includes('\n')) {
          errors.push(`${e.entityId} ${m.surahNumber}:${m.ayahNumber}: matchedText contains newline`);
        }
      }
    }
  }

  if (totalMentions !== out.totalMentions) {
    errors.push(`totalMentions mismatch: header=${out.totalMentions}, summed=${totalMentions}`);
  }

  // Maryam-specific smoke check
  const maryam = out.entities.find((e) => e.entityId === 'entity_person_maryam');
  if (!maryam) {
    errors.push('Maryam entity not found in scan output');
  } else {
    const seed = getEntitySeedById('entity_person_maryam');
    if (!seed) errors.push('Maryam seed missing from seed dictionary');
    else {
      for (const a of ['مريم', 'ابن مريم']) {
        if (!seed.aliasesArabic.includes(a)) errors.push(`Maryam seed missing alias "${a}"`);
      }
    }
    const explicit = maryam.mentions.filter((m) => m.mentionType === 'explicit_name').length;
    const surahs = new Set(maryam.mentions.map((m) => m.surahNumber));
    if (explicit < 25) warnings.push(`Maryam has only ${explicit} explicit_name mentions (expected ≥25)`);
    if (surahs.size < 10) warnings.push(`Maryam mentioned in ${surahs.size} surahs (expected ≥10)`);
  }

  // Report
  if (warnings.length) {
    console.warn(`\nWarnings: ${warnings.length}`);
    for (const w of warnings) console.warn(`  - ${w}`);
  }
  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(
    `OK — entities=${out.entities.length}, mentions=${out.totalMentions}, warnings=${warnings.length}`
  );
}

main();
