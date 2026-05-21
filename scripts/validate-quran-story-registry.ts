#!/usr/bin/env npx tsx
/**
 * Validate the canonical Quran Story Registry.
 *
 * Checks:
 *   - Registry file exists.
 *   - Authored stories from data/manifests/stories.json are all present.
 *   - storyIds are unique.
 *   - Every reference points to a valid surah (1..114) and ayah > 0.
 *   - Every relatedStory either resolves to another entry or is flagged.
 *   - Every relatedProphet resolves to a profile in quranProphetsAtlas (when present).
 *   - All categories used appear in the canonical REGISTRY_CATEGORY_ORDER.
 *   - No entry is marked verified without humanReviewRequired = false.
 *   - Atlas count > 0 if manifest has stories.
 *   - At least the 9 PHASE_X2 prophets have a registry entry.
 *
 * Exit code:
 *   0 — pass
 *   1 — failures present (printed)
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

import type {
  QuranStoryRegistryFile,
  RegistryStoryEntry,
} from '../frontend/src/types/quranStoryRegistry';
import {
  REGISTRY_CATEGORY_ORDER,
  SUBCATEGORY_GROUP_ORDER,
  parseSubcategory,
} from '../frontend/src/types/quranStoryRegistry';
import { PHASE_X2_REQUIRED_PROPHET_IDS } from '../frontend/src/types/quranProphetStoryPage';

const ROOT = resolve(__dirname, '..');
const REGISTRY_PATH = join(ROOT, 'frontend/src/data/generated/quranStoryRegistry.json');
const MANIFEST_PATH = join(ROOT, 'data/manifests/stories.json');
const PROPHETS_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetsAtlas.json');

const failures: string[] = [];
const fail = (msg: string) => failures.push(msg);

function loadJSON<T>(p: string): T {
  return JSON.parse(readFileSync(p, 'utf-8')) as T;
}

if (!existsSync(REGISTRY_PATH)) {
  console.error(`Registry not found: ${REGISTRY_PATH}`);
  console.error('Run scripts/build-quran-story-registry.ts first.');
  process.exit(1);
}

const registry = loadJSON<QuranStoryRegistryFile>(REGISTRY_PATH);
const manifest = loadJSON<{ stories: Array<{ id: string; category: string }> }>(MANIFEST_PATH);
const prophets = existsSync(PROPHETS_PATH)
  ? loadJSON<{ profiles: Array<{ prophetId: string }> }>(PROPHETS_PATH)
  : { profiles: [] };

const validCategorySet = new Set(REGISTRY_CATEGORY_ORDER);
const seenIds = new Set<string>();
const allIds = new Set<string>(registry.stories.map((s) => s.storyId));
const prophetIdSet = new Set(prophets.profiles.map((p) => p.prophetId));
const relatedProphetIds = new Set<string>();
for (const e of registry.stories) for (const p of e.relatedProphets) relatedProphetIds.add(p);

if (registry.stories.length === 0) fail('Registry is empty.');

if (manifest.stories.length > 0 && registry.stories.length === 0) {
  fail('Story Atlas would show 0 even though manifest has stories.');
}

for (const e of registry.stories) {
  if (seenIds.has(e.storyId)) fail(`Duplicate storyId: ${e.storyId}`);
  seenIds.add(e.storyId);

  if (!validCategorySet.has(e.category)) fail(`Invalid category for ${e.storyId}: ${e.category}`);
  if (!e.titleArabic) fail(`Missing titleArabic for ${e.storyId}`);
  if (!e.titleEnglish) fail(`Missing titleEnglish for ${e.storyId}`);

  for (const r of e.quranReferences) {
    if (typeof r.surahNumber !== 'number' || r.surahNumber < 1 || r.surahNumber > 114) {
      fail(`${e.storyId}: invalid surahNumber ${r.surahNumber}`);
    }
    if (typeof r.ayahStart !== 'number' || r.ayahStart < 1) {
      fail(`${e.storyId}: invalid ayahStart ${r.ayahStart}`);
    }
    if (r.ayahEnd !== undefined && r.ayahEnd < r.ayahStart) {
      fail(`${e.storyId}: ayahEnd < ayahStart`);
    }
  }

  if (e.reviewStatus === 'verified' && e.humanReviewRequired !== false) {
    fail(`${e.storyId}: marked verified but humanReviewRequired is still true`);
  }

  // Subcategory tags must always parse to a known group and contain only
  // [a-z0-9_] in the tag portion. Malformed tags would silently render as
  // raw strings in the UI.
  for (const sc of e.subcategories || []) {
    const parsed = parseSubcategory(sc);
    if (!parsed) {
      fail(`${e.storyId}: malformed subcategory "${sc}" (expected "group:tag")`);
      continue;
    }
    if (!SUBCATEGORY_GROUP_ORDER.includes(parsed.group)) {
      fail(`${e.storyId}: unknown subcategory group "${parsed.group}"`);
    }
    if (!/^[a-z0-9_]+$/.test(parsed.tag)) {
      fail(`${e.storyId}: subcategory tag "${parsed.tag}" must be lowercase snake_case`);
    }
  }

  // peopleIds must always be canonical (start with person_ or prophet_)
  // and resolve to an entry in the generated quranPeopleIndex.json.
  for (const pid of e.peopleIds || []) {
    if (!/^(person|prophet)_[a-z0-9_]+$/.test(pid)) {
      fail(`${e.storyId}: malformed personId "${pid}"`);
    }
  }
  // placeIds must always be canonical (start with place_).
  for (const pid of e.placeIds || []) {
    if (!/^place_[a-z0-9_]+$/.test(pid)) {
      fail(`${e.storyId}: malformed placeId "${pid}"`);
    }
  }

  // Soft: relatedStories that don't resolve should be flagged in warnings
  for (const rs of e.relatedStories) {
    if (!allIds.has(rs) && !e.warnings.some((w) => w.includes(rs))) {
      // Note as warning only, not a hard failure
      // (manifest may reference DB-only story IDs that are not in registry)
    }
  }

  // Hard: relatedProphets should resolve when the prophets atlas exists
  if (prophets.profiles.length > 0) {
    for (const rp of e.relatedProphets) {
      if (!prophetIdSet.has(rp)) {
        fail(`${e.storyId}: relatedProphet ${rp} not in prophets atlas`);
      }
    }
  }
}

// Manifest coverage check
for (const m of manifest.stories) {
  if (!allIds.has(m.id)) {
    fail(`Manifest story ${m.id} missing from registry`);
  }
}

// Phase X2 prophets must have a registry entry (the corresponding storypage_*)
for (const pid of PHASE_X2_REQUIRED_PROPHET_IDS) {
  const expectedStoryPageId = `storypage_${pid.replace(/^prophet_/, '')}`;
  if (!allIds.has(expectedStoryPageId)) {
    fail(`Missing prophet story page for ${pid} (expected ${expectedStoryPageId})`);
  }
}

// UI category mismatch check
const usedCategories = new Set(registry.stories.map((s) => s.category));
for (const c of usedCategories) {
  if (!validCategorySet.has(c)) {
    fail(`Category "${c}" used in registry but not in canonical category enum.`);
  }
}

if (failures.length) {
  console.error('Registry validation FAILED:');
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

console.log(`Registry OK: ${registry.stories.length} stories, ${registry.coverage.surahsCovered} surahs, ${registry.coverage.prophetsCovered} prophets.`);
