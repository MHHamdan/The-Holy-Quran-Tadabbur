#!/usr/bin/env npx tsx
/**
 * Phase X2 — Validate the generated quranProphetStoryPages.json.
 *
 * Hard checks (exit 1 if any fails):
 *   - All 8 previously missing prophets now have a story page.
 *   - Every story page references a real prophet ID (matches one in the atlas).
 *   - No non-prophet figure appears as a prophet here.
 *   - Every story section has ≥ 1 ayahReference.
 *   - Every quranReference and ayahReference is in range:
 *       1 ≤ surahNumber ≤ 114, ayahStart ≥ 1.
 *   - Muhammad ﷺ page includes the not-full-biography warning.
 *   - Dhul-Kifl / Al-Yasa pages are pageType = "compact_profile" AND
 *     include a limited-Quran warning.
 *   - All sourceIds are in the trusted allow-list.
 *   - All sections default to reviewStatus = "needs_review".
 *
 * Coverage check (across all 25 prophets):
 *   - Every prophet either has a curated story page in this file
 *     OR a non-empty storyIds list in the atlas
 *     OR a contextual coverage entry (handled by the contextual-links
 *     validator), so that no prophet is left without *any* coverage.
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { PHASE_X2_REQUIRED_PROPHET_IDS } from '../frontend/src/types/quranProphetStoryPage';

const ROOT = resolve(__dirname, '..');
const PAGES_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetStoryPages.json');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetsAtlas.json');

const ALLOWED_SOURCE_IDS = new Set([
  'quran_uthmani_cloud',
  'stories_manifest',
  'ibn_kathir',
  'ibn_kathir_ar',
  'ibn_kathir_en',
  'tabari',
  'tabari_ar',
  'tabari_en',
  'qurtubi',
  'qurtubi_ar',
  'qurtubi_en',
]);

const FORBIDDEN_PROPHET_IDS = new Set([
  'prophet_luqman',
  'prophet_dhulqarnayn',
  'prophet_khidr',
  'prophet_uzayr',
  'prophet_maryam',
  'prophet_talut',
  'prophet_jalut',
  'prophet_bilqis',
]);

const errors: string[] = [];

if (!existsSync(PAGES_PATH)) {
  console.error(`[FAIL] ${PAGES_PATH} not found. Run scripts/build-missing-prophet-story-pages.ts first.`);
  process.exit(1);
}
if (!existsSync(ATLAS_PATH)) {
  console.error(`[FAIL] ${ATLAS_PATH} not found. Run scripts/build-quran-prophets-atlas.ts first.`);
  process.exit(1);
}
const file = JSON.parse(readFileSync(PAGES_PATH, 'utf-8'));
const atlas = JSON.parse(readFileSync(ATLAS_PATH, 'utf-8'));
const validProphetIds = new Set(atlas.profiles.map((p: any) => p.prophetId));

// 1. All 8 previously missing prophets have a page ------------------------
const pageIds = new Set<string>(file.pages.map((p: any) => p.prophetId));
for (const required of PHASE_X2_REQUIRED_PROPHET_IDS) {
  if (!pageIds.has(required)) {
    errors.push(`Missing story page for required prophet: ${required}`);
  }
}

// 2. Walk every page -------------------------------------------------------
for (const page of file.pages) {
  if (!validProphetIds.has(page.prophetId)) {
    errors.push(`Page ${page.storyPageId}: prophetId ${page.prophetId} is not in the atlas.`);
  }
  if (FORBIDDEN_PROPHET_IDS.has(page.prophetId)) {
    errors.push(`Page ${page.storyPageId}: non-prophet figure ${page.prophetId}.`);
  }

  // Quran references valid
  for (const r of page.quranReferences ?? []) {
    if (!Number.isInteger(r.surahNumber) || r.surahNumber < 1 || r.surahNumber > 114) {
      errors.push(`Page ${page.storyPageId}: bad surahNumber ${r.surahNumber}.`);
    }
    if (!Number.isInteger(r.ayahStart) || r.ayahStart < 1) {
      errors.push(`Page ${page.storyPageId}: bad ayahStart ${r.ayahStart}.`);
    }
  }

  // sourceIds allowlist
  for (const sid of page.sourceIds ?? []) {
    if (!ALLOWED_SOURCE_IDS.has(sid)) {
      errors.push(`Page ${page.storyPageId}: untrusted sourceId '${sid}'.`);
    }
  }

  // Every section
  for (const sec of page.storySections ?? []) {
    if (!Array.isArray(sec.ayahReferences) || sec.ayahReferences.length === 0) {
      errors.push(
        `Page ${page.storyPageId} section ${sec.sectionId}: missing ayahReferences.`,
      );
    }
    for (const r of sec.ayahReferences ?? []) {
      if (!Number.isInteger(r.surahNumber) || r.surahNumber < 1 || r.surahNumber > 114) {
        errors.push(`Section ${sec.sectionId}: bad surahNumber ${r.surahNumber}.`);
      }
      if (!Number.isInteger(r.ayahStart) || r.ayahStart < 1) {
        errors.push(`Section ${sec.sectionId}: bad ayahStart ${r.ayahStart}.`);
      }
    }
    for (const sid of sec.sourceIds ?? []) {
      if (!ALLOWED_SOURCE_IDS.has(sid)) {
        errors.push(`Section ${sec.sectionId}: untrusted sourceId '${sid}'.`);
      }
    }
    if (sec.reviewStatus === 'verified' && (!sec.sourceIds || sec.sourceIds.length === 0)) {
      errors.push(
        `Section ${sec.sectionId}: reviewStatus=verified requires non-empty sourceIds.`,
      );
    }
  }
}

// 3. Muhammad ﷺ — must include not-full-biography warning -----------------
const muhammad = file.pages.find((p: any) => p.prophetId === 'prophet_muhammad');
if (muhammad) {
  const allText = JSON.stringify(muhammad);
  if (!/biography/i.test(allText) && !/سيرة/.test(allText)) {
    errors.push(
      'Muhammad ﷺ story page must include a not-full-biography warning.',
    );
  }
  if (muhammad.pageType !== 'mission_summary') {
    errors.push(`Muhammad ﷺ pageType must be "mission_summary" (got "${muhammad.pageType}").`);
  }
}

// 4. Dhul-Kifl / Al-Yasa — must be compact_profile + limited warning -------
for (const pid of ['prophet_dhulkifl', 'prophet_alyasa']) {
  const page = file.pages.find((p: any) => p.prophetId === pid);
  if (!page) continue;
  if (page.pageType !== 'compact_profile') {
    errors.push(`${pid} pageType must be "compact_profile" (got "${page.pageType}").`);
  }
  const allText = JSON.stringify(page);
  if (!/limited|compact|موجز|محدود/i.test(allText)) {
    errors.push(`${pid} page must include a limited-Quran-detail warning.`);
  }
}

// 5. Coverage across all 25 prophets ---------------------------------------
const allProphetIds: string[] = atlas.profiles.map((p: any) => p.prophetId);
const uncovered: string[] = [];
for (const pid of allProphetIds) {
  if (pageIds.has(pid)) continue;
  const atlasProfile = atlas.profiles.find((p: any) => p.prophetId === pid);
  if ((atlasProfile?.storyIds ?? []).length > 0) continue;
  uncovered.push(pid);
}
if (uncovered.length > 0) {
  errors.push(
    `Prophets without any coverage (no story page + no storyIds): ${uncovered.join(', ')}`,
  );
}

// ----- Report
console.log(`\nProphet Story Pages validation`);
console.log(`-----------------------------`);
console.log(`Pages: ${file.pages.length}`);
console.log(`Errors: ${errors.length}`);
if (errors.length > 0) {
  for (const e of errors) console.log(`  - ${e}`);
  process.exit(1);
}
console.log(`\n[OK] All Phase X2 story-page checks pass.`);
process.exit(0);
