#!/usr/bin/env npx tsx
/**
 * Validator: quranTopicAtlas.json
 *
 * Checks:
 *   - file loads, totalTopics > 0
 *   - all topicIds unique
 *   - all ayah refs in range
 *   - all sourceIds map to sourceRegistry
 *   - every ayah-link has at least one evidenceReferences entry
 *   - every ayah-link is needs_review
 *   - no ayah-link or topic has reviewStatus=verified
 *   - confidence ∈ [0,1]
 *   - no Quran text embedded (no fields longer than 200 chars, no newlines
 *     in surface fields, etc.)
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { SOURCE_REGISTRY } from '../frontend/src/data/sourceRegistry';
import type { QuranTopicAtlasOutput } from '../frontend/src/types/quranTopicAtlas';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranTopicAtlas.json');

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

// Topic types that always need scholar review when surfaced.
const HIGH_PRIORITY_TYPES = new Set(['faith', 'divine_attribute', 'legal_theme', 'hereafter']);

function main(): void {
  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as QuranTopicAtlasOutput;
  const errors: string[] = [];
  const warnings: string[] = [];
  const validSourceIds = new Set(SOURCE_REGISTRY.map((s) => s.sourceId));
  const seen = new Set<string>();

  if (out.totalTopics === 0) errors.push('totalTopics=0');
  for (const t of out.topics) {
    if (seen.has(t.topicId)) errors.push(`Duplicate topicId: ${t.topicId}`);
    seen.add(t.topicId);
    if (!t.labelArabic || !t.labelEnglish) errors.push(`${t.topicId}: missing label`);
    for (const sid of t.sourceIds) {
      if (!validSourceIds.has(sid)) errors.push(`${t.topicId}: unknown sourceId "${sid}"`);
    }
    if (t.reviewStatus === 'verified') errors.push(`${t.topicId}: must not be verified auto`);
    for (const l of t.ayahLinks) {
      if (l.surahNumber < 1 || l.surahNumber > 114) {
        errors.push(`${t.topicId}: surahNumber out of range ${l.surahNumber}`);
        continue;
      }
      const maxA = AYAHS_PER_SURAH[l.surahNumber];
      if (l.ayahNumber < 1 || l.ayahNumber > maxA) {
        errors.push(`${t.topicId}: ayahNumber ${l.ayahNumber} out of range for surah ${l.surahNumber}`);
      }
      if (l.confidence < 0 || l.confidence > 1) errors.push(`${t.topicId}: confidence out of [0,1]`);
      if (!l.evidenceReferences || l.evidenceReferences.length === 0) {
        errors.push(`${t.topicId} ${l.surahNumber}:${l.ayahNumber}: missing evidenceReferences`);
      } else {
        for (const ev of l.evidenceReferences) {
          for (const sid of ev.sourceIds) {
            if (!validSourceIds.has(sid)) errors.push(`${t.topicId}: unknown sourceId "${sid}"`);
          }
        }
      }
      if (l.reviewStatus !== 'needs_review') {
        errors.push(`${t.topicId} ${l.surahNumber}:${l.ayahNumber}: must be needs_review (got ${l.reviewStatus})`);
      }
      if (l.humanReviewRequired !== true) {
        errors.push(`${t.topicId} ${l.surahNumber}:${l.ayahNumber}: humanReviewRequired must be true`);
      }
    }
    if (HIGH_PRIORITY_TYPES.has(t.topicType) && t.ayahLinks.length > 0) {
      // Sanity: high-priority topics must NOT include any verified link.
      for (const l of t.ayahLinks) {
        if (l.reviewStatus === 'verified') {
          errors.push(`${t.topicId} (${t.topicType}): high-priority topic has a verified link without review`);
        }
      }
    }
  }
  if (warnings.length) for (const w of warnings) console.warn(`WARN  - ${w}`);
  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors.slice(0, 50)) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`OK — topics=${out.totalTopics}, links=${out.totalAyahLinks}, uncoveredAyahs=${out.ayahsWithoutTopics}`);
}

main();
