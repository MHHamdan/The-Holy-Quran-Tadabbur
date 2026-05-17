#!/usr/bin/env npx tsx
/**
 * Validator: asmaAllahAtlas.json
 *
 * Checks:
 *   - file loads
 *   - all seed names represented (no missing seed)
 *   - all ayah references in range
 *   - occurrenceCount equals number of counted occurrences
 *   - every basmalah-excluded occurrence has counted=false, isBasmalah=true
 *   - no basmalah-excluded occurrence contributes to occurrenceCount
 *   - all sourceIds map to sourceRegistry
 *   - no meaning is set (meaningArabic/English) while reviewStatus != "verified"
 *   - no category is set to "verified" without sourceIds AND review
 *   - confidence ∈ [0, 1]
 *   - common pairings reference existing nameIds
 *   - category counts are non-zero where the data has names of that category
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { SOURCE_REGISTRY } from '../frontend/src/data/sourceRegistry';
import { ASMA_ALLAH_SEEDS } from '../frontend/src/data/asmaAllahSeeds';
import type { AsmaAtlasOutput } from '../frontend/src/types/asmaAllah';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/asmaAllahAtlas.json');

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

// Normalisation matches the rest of the pipeline.
const ARABIC_DIACRITICS = /[ً-ٰٟؐ-ؚۖ-ۭـ]/g;
function normaliseArabic(s: string): string {
  return s
    .replace(ARABIC_DIACRITICS, '')
    .replace(/[آأإٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/ء/g, '')
    .trim();
}

function main(): void {
  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as AsmaAtlasOutput;
  const errors: string[] = [];
  const seedIds = new Set(ASMA_ALLAH_SEEDS.map((s) => s.nameId));
  const atlasIds = new Set(out.names.map((n) => n.nameId));
  if (out.divineNameAllah) atlasIds.add(out.divineNameAllah.nameId);
  const validSourceIds = new Set(SOURCE_REGISTRY.map((s) => s.sourceId));

  // All seeds represented (either in the 99 list or as the standalone Divine Name).
  for (const sid of seedIds) {
    if (!atlasIds.has(sid)) errors.push(`Seed nameId missing from atlas: ${sid}`);
  }

  // ---- Count + uniqueness contracts for the 99-Names list ----
  if (out.traditionalNamesCount !== 99) {
    errors.push(
      `traditionalNamesCount must equal 99; got ${out.traditionalNamesCount}.`
    );
  }
  if (out.names.length !== out.traditionalNamesCount) {
    errors.push(
      `atlas.names length (${out.names.length}) must equal traditionalNamesCount (${out.traditionalNamesCount}).`
    );
  }
  if (out.allDisplayCount !== out.traditionalNamesCount + (out.divineNameAllahIncluded ? 0 : 0)) {
    // allDisplayCount must equal the count rendered in the main "All" tab.
    // When Allah is separate, it must equal traditionalNamesCount (99).
    // When Allah is bundled, the policy ALSO sets it to 99 (Allah replaces
    // one slot rather than adding a 100th).
    if (out.allDisplayCount !== 99) {
      errors.push(
        `allDisplayCount must equal 99 for the primary Asmā' tab; got ${out.allDisplayCount}.`
      );
    }
  }
  if (out.allDisplayCount === 100) {
    errors.push(
      'allDisplayCount must NEVER equal 100. The Asmā\' tab must show 99 — Allah is shown separately.'
    );
  }
  // The Divine Name "Allah" must NOT appear inside the 99-Names list when
  // divineNameAllahIncluded is false (the default policy).
  if (!out.divineNameAllahIncluded) {
    const allahInsideList = out.names.find((n) => n.nameId === 'allah');
    if (allahInsideList) {
      errors.push(
        '"allah" must not appear in the 99-Names list when divineNameAllahIncluded is false; ' +
          'expose it via the divineNameAllah field instead.'
      );
    }
    if (!out.divineNameAllah) {
      errors.push(
        'divineNameAllahIncluded is false but divineNameAllah payload is missing.'
      );
    }
  } else {
    // If the policy ever bundles Allah inside the list, it must appear at most once.
    const allahCount = out.names.filter((n) => n.nameId === 'allah').length;
    if (allahCount !== 1) {
      errors.push(
        `"allah" must appear exactly once when divineNameAllahIncluded is true; got ${allahCount}.`
      );
    }
  }

  // No duplicate nameIds inside the 99-Names list.
  const idCounts = new Map<string, number>();
  for (const n of out.names) idCounts.set(n.nameId, (idCounts.get(n.nameId) ?? 0) + 1);
  for (const [id, c] of idCounts.entries()) {
    if (c > 1) errors.push(`Duplicate nameId in 99-Names list: ${id} (count=${c})`);
  }

  // No duplicate normalised Arabic name (aliases must not be counted as
  // separate entries).
  const normalisedNames = new Map<string, string>();
  for (const n of out.names) {
    const norm = normaliseArabic(n.arabicName);
    const prior = normalisedNames.get(norm);
    if (prior && prior !== n.nameId) {
      errors.push(
        `Duplicate normalised Arabic name "${norm}" appears as both "${prior}" and "${n.nameId}". ` +
          'Alternate forms must be aliases, not separate names.'
      );
    } else {
      normalisedNames.set(norm, n.nameId);
    }
  }

  // Category totals must sum to the 99-Names count exactly.
  const categorySum = out.categoryCounts.reduce((acc, c) => acc + c.names, 0);
  if (categorySum !== out.traditionalNamesCount) {
    errors.push(
      `Category names sum (${categorySum}) must equal traditionalNamesCount (${out.traditionalNamesCount}).`
    );
  }

  // ---- Primary Quranic references (Tirmidhi tradition) ----
  for (const n of out.names) {
    const refs = n.primaryQuranicReferences ?? [];
    if (refs.length === 0) {
      errors.push(`${n.nameId}: missing primaryQuranicReferences — every traditional Name must cite at least one verse.`);
    }
    // No duplicate surah:ayah inside the same Name's references.
    const seen = new Set<string>();
    for (const r of refs) {
      if (typeof r.surahNumber !== 'number' || typeof r.ayahStart !== 'number') {
        errors.push(`${n.nameId}: primary reference has non-numeric surah/ayah`);
        continue;
      }
      if (r.surahNumber < 1 || r.surahNumber > 114) {
        errors.push(`${n.nameId}: primary ref has invalid surah ${r.surahNumber}`);
        continue;
      }
      const maxA = AYAHS_PER_SURAH[r.surahNumber];
      if (r.ayahStart < 1 || r.ayahStart > maxA) {
        errors.push(
          `${n.nameId}: primary ref ${r.surahNumber}:${r.ayahStart} out of range (max ayah=${maxA})`
        );
      }
      const key = `${r.surahNumber}:${r.ayahStart}`;
      if (seen.has(key)) {
        errors.push(`${n.nameId}: duplicate primary reference ${key}`);
      }
      seen.add(key);
      // Notes must be short and free of newlines.
      if (typeof r.note === 'string' && (r.note.length > 250 || r.note.includes('\n'))) {
        errors.push(`${n.nameId}: primary ref note violates length/newline constraints`);
      }
    }
    // When refs are attached, the Tirmidhi source must be on the Name.
    if (refs.length > 0 && !n.sourceIds.includes('tirmidhi_asma_husna_list')) {
      errors.push(`${n.nameId}: has primary refs but missing sourceId "tirmidhi_asma_husna_list"`);
    }
  }

  // Per-name checks
  for (const n of out.names) {
    // Source IDs
    for (const sid of n.sourceIds) {
      if (!validSourceIds.has(sid)) errors.push(`${n.nameId}: unknown sourceId "${sid}"`);
    }
    // Meaning must be undefined unless reviewStatus is verified
    if ((n.meaningArabic || n.meaningEnglish) && n.reviewStatus !== 'verified') {
      errors.push(`${n.nameId}: meaning set without reviewStatus=verified`);
    }
    // Category must be needs_review unless attached to a source (we treat the
    // atlas reviewStatus as authoritative; any verified record must also have
    // sourceIds beyond the canonical Quran text — we keep this rule lenient
    // for the auto-build but reject auto-emitted "verified" rows).
    if (n.reviewStatus === 'verified' && n.sourceIds.every((s) => s === 'quran_uthmani_cloud')) {
      errors.push(`${n.nameId}: reviewStatus=verified must have a non-Quran source attached`);
    }
    // Counted = occurrenceCount
    const countedOccs = n.quranOccurrences.filter((o) => o.counted);
    if (countedOccs.length !== n.occurrenceCount) {
      errors.push(
        `${n.nameId}: occurrenceCount=${n.occurrenceCount} but counted occurrences=${countedOccs.length}`
      );
    }
    // Per-occurrence checks
    for (const o of n.quranOccurrences) {
      if (o.surahNumber < 1 || o.surahNumber > 114) {
        errors.push(`${n.nameId}: invalid surahNumber=${o.surahNumber}`);
        continue;
      }
      const maxA = AYAHS_PER_SURAH[o.surahNumber];
      if (o.ayahNumber < 1 || o.ayahNumber > maxA) {
        errors.push(`${n.nameId}: invalid ayahNumber=${o.ayahNumber} for surah ${o.surahNumber}`);
      }
      if (o.confidence < 0 || o.confidence > 1) {
        errors.push(`${n.nameId}: confidence out of [0,1]`);
      }
      // Basmalah-excluded must have counted=false AND isBasmalah=true
      if (o.matchType === 'basmalah_excluded') {
        if (o.counted !== false) errors.push(`${n.nameId}: basmalah_excluded but counted=true`);
        if (o.isBasmalah !== true) errors.push(`${n.nameId}: basmalah_excluded but isBasmalah=false`);
      } else {
        if (o.isBasmalah === true && o.counted === true) {
          errors.push(`${n.nameId}: isBasmalah=true must have counted=false`);
        }
      }
      // Source IDs
      for (const sid of o.sourceIds) {
        if (!validSourceIds.has(sid)) errors.push(`${n.nameId}: occurrence has unknown sourceId "${sid}"`);
      }
      // matchedForm length
      if (o.matchedForm && (o.matchedForm.length > 80 || o.matchedForm.includes('\n'))) {
        errors.push(`${n.nameId}: matchedForm violates length/newline constraints`);
      }
    }
    // Pairings
    for (const p of n.commonPairings) {
      if (!atlasIds.has(p.firstNameId)) errors.push(`${n.nameId}: pairing references unknown nameId ${p.firstNameId}`);
      if (!atlasIds.has(p.secondNameId)) errors.push(`${n.nameId}: pairing references unknown nameId ${p.secondNameId}`);
    }
  }

  // Category counts non-zero when matching names exist
  for (const c of out.categoryCounts) {
    const namesInCat = out.names.filter((n) => n.category === c.category);
    if (namesInCat.length !== c.names) {
      errors.push(`Category ${c.category}: names count mismatch (atlas=${namesInCat.length}, summary=${c.names})`);
    }
  }
  // UI safety: at least one category with names must have a non-zero
  // countedOccurrences (so the page never renders all-zero by definition).
  const anyNonZero = out.categoryCounts.some((c) => c.countedOccurrences > 0);
  if (!anyNonZero) errors.push('All category counts are zero — UI would render 0 across all tabs.');

  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors.slice(0, 50)) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(
    `OK — names=${out.totalNames}, counted=${out.totalCountedOccurrences}, excluded=${out.totalExcludedBasmalahOccurrences}, with-occ=${out.namesWithOccurrences}, zero-occ=${out.namesWithZeroOccurrences}`
  );
}

main();
