#!/usr/bin/env npx tsx
/**
 * Asmā' Allah al-Ḥusnā Atlas Builder — Phase W.
 *
 * Reads:
 *   - data/raw/quran_uthmani.json (canonical text; never written)
 *   - frontend/src/data/asmaAllahSeeds.ts
 *
 * Writes:
 *   - frontend/src/data/generated/asmaAllahAtlas.json
 *   - docs/generated/asma-allah-atlas-summary.md
 *
 * Safety rules:
 *   - Quran text is never mutated.
 *   - matchedForm is the short normalised alias (≤80 chars, no newlines).
 *   - All names + occurrences default to needs_review.
 *   - Basmalah-exclusion policy applied per docs/asma-basmalah-counting-policy.md.
 *   - No meanings are emitted (kept undefined unless reviewer-promoted via
 *     review workflow).
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';
import { ASMA_ALLAH_SEEDS } from '../frontend/src/data/asmaAllahSeeds';
import { ASMA_ALLAH_PRIMARY_REFERENCES } from '../frontend/src/data/asmaAllahQuranicReferences';
import type {
  AsmaAllahName,
  AsmaAllahSeed,
  AsmaAtlasOutput,
  AsmaCategory,
  AsmaCategoryCount,
  AsmaMatchType,
  AsmaNamePairing,
  AsmaOccurrence,
  QuranReference,
} from '../frontend/src/types/asmaAllah';

const ROOT = resolve(__dirname, '..');
const QURAN_PATH = join(ROOT, 'data/raw/quran_uthmani.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/asmaAllahAtlas.json');
const OUT_MD = join(ROOT, 'docs/generated/asma-allah-atlas-summary.md');
const VERSION = '1.1.0';

// Names that may appear inside a surah-opening basmalah and must therefore
// be excluded from the count when the match lands inside the basmalah prefix.
const BASMALAH_NAME_IDS = new Set(['allah', 'ar_rahman', 'ar_raheem']);

// Categories iterated in display order. Keep in sync with AsmaCategory union.
const CATEGORY_ORDER: AsmaCategory[] = ['dhat', 'jamal', 'jalal', 'kamal', 'afaal', 'unknown'];

// Per-surah ayah counts (mushaf totals; same table as scripts/validate-asma-allah-atlas.ts).
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

// ---------------------------------------------------------------------------
// Arabic normalisation (matches the rest of the platform exactly)
// ---------------------------------------------------------------------------

const ARABIC_DIACRITICS = /[ً-ٰٟؐ-ؚۖ-ۭـ]/g;
const ARABIC_LETTER = /[ء-ي]/;
// Arabic clitic prefixes commonly attached to nouns.
const CLITIC_PREFIXES = ['ل', 'و', 'ف', 'ب', 'ك', 'س', 'لو', 'فل', 'ول', 'وب', 'فب', 'بل', 'وك'];

function normaliseArabic(s: string): string {
  return s
    .replace(ARABIC_DIACRITICS, '')
    .replace(/[آأإٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/ء/g, '')
    .replace(/[​-‏﻿]/g, '')
    .trim();
}

const BASMALA_NORMALISED = normaliseArabic('بسم الله الرحمن الرحيم');

// ---------------------------------------------------------------------------
// Quran loader
// ---------------------------------------------------------------------------

interface RawAyah {
  sura_no: number;
  aya_no: number;
  aya_text: string;
}

function loadQuran(): RawAyah[] {
  if (!existsSync(QURAN_PATH)) throw new Error(`Missing ${QURAN_PATH}`);
  return JSON.parse(readFileSync(QURAN_PATH, 'utf-8')) as RawAyah[];
}

// ---------------------------------------------------------------------------
// Alias table
// ---------------------------------------------------------------------------

interface AliasEntry {
  nameId: string;
  alias: string;
  normalised: string;
  /** When the alias is the plain name (e.g. الله), accept clitic prefixes. */
  acceptCliticPrefix: boolean;
}

function buildAliasTable(seeds: AsmaAllahSeed[]): AliasEntry[] {
  const out: AliasEntry[] = [];
  // Dedupe by (nameId, normalised) so multiple Arabic spellings that
  // collapse to the same normalised form (e.g. الله / اللَّه / ٱللَّه) do
  // not inflate occurrence counts.
  const seen = new Set<string>();
  for (const s of seeds) {
    for (const a of s.aliasesArabic) {
      const norm = normaliseArabic(a);
      if (norm.length < 3) continue;
      const key = `${s.nameId}::${norm}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({
        nameId: s.nameId,
        alias: a,
        normalised: norm,
        // Only الله needs clitic-prefix acceptance: بالله, لله, والله, etc.
        acceptCliticPrefix: s.nameId === 'allah',
      });
    }
  }
  out.sort((a, b) => b.normalised.length - a.normalised.length);
  return out;
}

interface MatchHit {
  nameId: string;
  alias: string;
  startIndex: number;
}

/**
 * Find all occurrences of a needle in haystack with strict right-side word
 * boundary AND left-side clitic-prefix handling for "Allah".
 */
function findOccurrences(haystack: string, e: AliasEntry): MatchHit[] {
  const out: MatchHit[] = [];
  const n = e.normalised;
  if (n.length < 3) return out;
  let i = haystack.indexOf(n);
  while (i !== -1) {
    const after = i + n.length < haystack.length ? haystack[i + n.length] : ' ';
    if (!ARABIC_LETTER.test(after)) {
      // Right boundary OK. Now check left boundary:
      const left = i > 0 ? haystack[i - 1] : ' ';
      let ok = !ARABIC_LETTER.test(left);
      if (!ok && e.acceptCliticPrefix) {
        // Walk left through Arabic letters; if the prefix sequence is one of
        // the allowed clitics and is preceded by a non-letter or start, accept.
        let k = i - 1;
        while (k >= 0 && ARABIC_LETTER.test(haystack[k])) k -= 1;
        const pref = haystack.slice(k + 1, i);
        if (CLITIC_PREFIXES.includes(pref)) ok = true;
      }
      if (ok) out.push({ nameId: e.nameId, alias: e.alias, startIndex: i });
    }
    i = haystack.indexOf(n, i + 1);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Helpers (light refactor — no behavior change)
// ---------------------------------------------------------------------------

/** Returns true when the seed represents one of the 99 traditional Names. */
function isTraditional99(seed: AsmaAllahSeed | undefined): boolean {
  return seed?.inTraditional99 !== false;
}

/** Build the initial per-name accumulator entries from the seed list. */
function buildNameMap(seeds: AsmaAllahSeed[]): Map<string, AsmaAllahName> {
  const m = new Map<string, AsmaAllahName>();
  for (const s of seeds) {
    m.set(s.nameId, {
      nameId: s.nameId,
      arabicName: s.arabicName,
      transliteration: s.transliteration,
      englishName: s.englishName,
      rootArabic: s.rootArabic,
      category: s.category,
      meaningArabic: undefined,
      meaningEnglish: undefined,
      shortReflectionArabic: undefined,
      shortReflectionEnglish: undefined,
      quranOccurrences: [],
      occurrenceCount: 0,
      surahCount: 0,
      firstOccurrence: undefined,
      lastOccurrence: undefined,
      commonPairings: [],
      relatedTopics: [],
      relatedEntities: [],
      sourceIds: ['quran_uthmani_cloud'],
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [...(s.warnings ?? [])],
      primaryQuranicReferences: [],
    });
  }
  return m;
}

/**
 * Detect the surah-opening basmalah prefix (when present). Returns the
 * end-index of the prefix in the normalised ayah text, or -1 if not present.
 *
 * The canonical Quran data inlines the basmalah at the start of every surah's
 * ayah 1 (except Surah 9 At-Tawbah). Al-Fatihah 1:1 *is* the basmalah.
 */
function basmalahPrefixEnd(normAyah: string, sura: number, aya: number): number {
  if (aya !== 1 || sura === 9) return -1;
  if (normAyah === BASMALA_NORMALISED) return normAyah.length;
  if (normAyah.startsWith(BASMALA_NORMALISED + ' ')) return BASMALA_NORMALISED.length + 1;
  if (normAyah.startsWith(BASMALA_NORMALISED)) return BASMALA_NORMALISED.length;
  return -1;
}

/**
 * Classify a single hit into a typed AsmaOccurrence. Encapsulates the
 * basmalah-exclusion / clitic-prefix logic so the main loop stays readable.
 */
function classifyHit(
  hit: MatchHit,
  alias: AliasEntry,
  sura: number,
  aya: number,
  basmalahEnd: number
): AsmaOccurrence {
  const insideBasmalahPrefix =
    basmalahEnd > 0 && hit.startIndex < basmalahEnd && BASMALAH_NAME_IDS.has(alias.nameId);
  const isBasmalah = insideBasmalahPrefix;
  const matchType: AsmaMatchType = isBasmalah
    ? 'basmalah_excluded'
    : alias.acceptCliticPrefix
    ? 'definite_form'
    : 'exact_name';
  const counted = !isBasmalah;
  return {
    surahNumber: sura,
    ayahNumber: aya,
    matchedForm: alias.normalised,
    matchType,
    isBasmalah,
    counted,
    confidence: counted ? 0.95 : 0.6,
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
  };
}

function pairingKey(a: string, b: string): string {
  return a < b ? `${a}::${b}` : `${b}::${a}`;
}

/** Compute the canonical first/last/surahCount on each name's occurrences. */
function finaliseOccurrenceStats(name: AsmaAllahName): void {
  name.quranOccurrences.sort((a, b) =>
    a.surahNumber !== b.surahNumber ? a.surahNumber - b.surahNumber : a.ayahNumber - b.ayahNumber
  );
  const counted = name.quranOccurrences.filter((o) => o.counted);
  name.surahCount = new Set(counted.map((o) => o.surahNumber)).size;
  name.firstOccurrence = counted[0]
    ? { surahNumber: counted[0].surahNumber, ayahStart: counted[0].ayahNumber }
    : undefined;
  name.lastOccurrence = counted[counted.length - 1]
    ? {
        surahNumber: counted[counted.length - 1].surahNumber,
        ayahStart: counted[counted.length - 1].ayahNumber,
      }
    : undefined;
}

/**
 * Attach curated Tirmidhi-tradition primary Quranic references to each Name.
 * Validates each reference against the mushaf ayah-count table and dedupes
 * by surah:ayah so the same Name isn't cited twice for the same verse.
 *
 * Adds `tirmidhi_asma_husna_list` to the Name's sourceIds when at least one
 * reference is attached. Never modifies Quran text — only emits numbers.
 */
function attachPrimaryReferences(nameMap: Map<string, AsmaAllahName>): void {
  let invalidCount = 0;
  for (const entry of ASMA_ALLAH_PRIMARY_REFERENCES) {
    const slot = nameMap.get(entry.nameId);
    if (!slot) continue;
    const seen = new Set<string>();
    const refs: QuranReference[] = [];
    for (const r of entry.primaryReferences) {
      const maxAyah = AYAHS_PER_SURAH[r.surahNumber];
      if (!maxAyah || r.ayahNumber < 1 || r.ayahNumber > maxAyah) {
        invalidCount += 1;
        console.warn(
          `  ! invalid primary ref for ${entry.nameId}: ${r.surahNumber}:${r.ayahNumber} (skipped)`
        );
        continue;
      }
      const key = `${r.surahNumber}:${r.ayahNumber}`;
      if (seen.has(key)) continue;
      seen.add(key);
      refs.push({
        surahNumber: r.surahNumber,
        ayahStart: r.ayahNumber,
        ...(r.note ? { note: r.note } : {}),
      });
    }
    slot.primaryQuranicReferences = refs;
    if (refs.length > 0 && !slot.sourceIds.includes('tirmidhi_asma_husna_list')) {
      slot.sourceIds.push('tirmidhi_asma_husna_list');
    }
  }
  if (invalidCount > 0) {
    console.warn(`Attached primary references with ${invalidCount} invalid entries skipped.`);
  }
}

/** Tally seed-level duplicates (same nameId, or same normalised Arabic form). */
function detectSeedDuplicates(seeds: AsmaAllahSeed[]): string[] {
  const duplicates: string[] = [];
  const seenIds = new Set<string>();
  const seenNormalised = new Map<string, string>();
  for (const s of seeds) {
    if (seenIds.has(s.nameId)) {
      duplicates.push(s.nameId);
      continue;
    }
    seenIds.add(s.nameId);
    const norm = normaliseArabic(s.arabicName);
    const prior = seenNormalised.get(norm);
    if (prior && prior !== s.nameId) {
      duplicates.push(s.nameId);
    } else {
      seenNormalised.set(norm, s.nameId);
    }
  }
  return duplicates;
}

/** Build the category-counts summary for the 99-Names list. */
function aggregateCategoryCounts(traditional99: AsmaAllahName[]): AsmaCategoryCount[] {
  return CATEGORY_ORDER.map((cat) => {
    const names = traditional99.filter((n) => n.category === cat);
    return {
      category: cat,
      names: names.length,
      countedOccurrences: names.reduce((acc, n) => acc + n.occurrenceCount, 0),
    };
  });
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  console.log("Scanning Quran for Asmā' Allah occurrences...");
  const ayahs = loadQuran();
  const generatedAt = new Date().toISOString();
  const aliasTable = buildAliasTable(ASMA_ALLAH_SEEDS);

  const nameMap = buildNameMap(ASMA_ALLAH_SEEDS);
  const pairingMap = new Map<string, AsmaNamePairing>();

  let totalCounted = 0;
  let totalExcluded = 0;

  for (const a of ayahs) {
    const norm = normaliseArabic(a.aya_text ?? '');
    if (!norm) continue;

    const basmalahEnd = basmalahPrefixEnd(norm, a.sura_no, a.aya_no);
    const ayahNameIds = new Set<string>();

    for (const alias of aliasTable) {
      const slot = nameMap.get(alias.nameId);
      if (!slot) continue;
      for (const hit of findOccurrences(norm, alias)) {
        const occ = classifyHit(hit, alias, a.sura_no, a.aya_no, basmalahEnd);
        slot.quranOccurrences.push(occ);
        if (occ.counted) {
          slot.occurrenceCount += 1;
          totalCounted += 1;
          ayahNameIds.add(alias.nameId);
        } else {
          totalExcluded += 1;
        }
      }
    }

    // Pairings — only when ≥ 2 distinct (counted) names co-occur in the same
    // ayah. Skip pairings involving "allah": it would dominate every list.
    if (ayahNameIds.size >= 2) {
      const ids = Array.from(ayahNameIds).sort();
      for (let i = 0; i < ids.length; i++) {
        if (ids[i] === 'allah') continue;
        for (let j = i + 1; j < ids.length; j++) {
          if (ids[j] === 'allah') continue;
          const k = pairingKey(ids[i], ids[j]);
          let p = pairingMap.get(k);
          if (!p) {
            p = {
              firstNameId: ids[i],
              secondNameId: ids[j],
              occurrenceCount: 0,
              ayahReferences: [],
              reviewStatus: 'needs_review',
            };
            pairingMap.set(k, p);
          }
          p.occurrenceCount += 1;
          p.ayahReferences.push({ surahNumber: a.sura_no, ayahStart: a.aya_no });
        }
      }
    }
  }

  // Finalise per-name stats and attach the no-occurrence warning where needed.
  for (const n of nameMap.values()) {
    finaliseOccurrenceStats(n);
    if (n.occurrenceCount === 0) {
      n.warnings.push(
        'No explicit Quran occurrence detected for this name lemma. It is preserved in the seed list because it is part of the traditional list; reviewer must decide how to label it.'
      );
    }
  }

  // Attach the curated Tirmidhi-tradition primary Quranic references.
  attachPrimaryReferences(nameMap);

  // Attach pairings to each name (top 25 by count).
  const allPairings = Array.from(pairingMap.values()).sort(
    (a, b) => b.occurrenceCount - a.occurrenceCount
  );
  for (const p of allPairings) {
    const a = nameMap.get(p.firstNameId);
    const b = nameMap.get(p.secondNameId);
    if (a) a.commonPairings.push(p);
    if (b) b.commonPairings.push(p);
  }
  for (const n of nameMap.values()) {
    n.commonPairings.sort((a, b) => b.occurrenceCount - a.occurrenceCount);
    n.commonPairings = n.commonPairings.slice(0, 25);
  }

  // Partition the seed records into the primary 99-Names list and the
  // standalone Divine Name "Allah" (seed.inTraditional99 === false).
  const seedById = new Map<string, AsmaAllahSeed>(
    ASMA_ALLAH_SEEDS.map((s) => [s.nameId, s] as const)
  );
  const duplicateNamesRemoved = detectSeedDuplicates(ASMA_ALLAH_SEEDS);

  const allNames = Array.from(nameMap.values());
  const traditional99 = allNames.filter((n) => isTraditional99(seedById.get(n.nameId)));
  const divineNameAllah = allNames.find((n) => !isTraditional99(seedById.get(n.nameId)));

  if (traditional99.length !== 99) {
    throw new Error(
      `Asmā' atlas build: traditional 99 list must contain exactly 99 entries, got ${traditional99.length}. ` +
        `Inspect frontend/src/data/asmaAllahSeeds.ts.`
    );
  }

  const categoryCounts = aggregateCategoryCounts(traditional99);

  // Sanity: category totals must sum to exactly the 99-names count.
  const categorySum = categoryCounts.reduce((acc, c) => acc + c.names, 0);
  if (categorySum !== 99) {
    throw new Error(
      `Asmā' atlas build: category names must sum to 99 for the primary display, got ${categorySum}.`
    );
  }

  // Top names by occurrence (across the 99 — Allah is shown in the hero panel
  // and would otherwise dominate the chart).
  const top = traditional99
    .map((n) => ({
      nameId: n.nameId,
      arabicName: n.arabicName,
      occurrenceCount: n.occurrenceCount,
      surahCount: n.surahCount,
    }))
    .sort((a, b) => b.occurrenceCount - a.occurrenceCount)
    .slice(0, 25);

  const topPairings = allPairings.slice(0, 15).map((p) => ({
    firstNameId: p.firstNameId,
    secondNameId: p.secondNameId,
    occurrenceCount: p.occurrenceCount,
  }));

  const out: AsmaAtlasOutput = {
    version: VERSION,
    generatedAt,
    basmalahPolicy: {
      countBasmalaInFatihah: false,
      excludeRepeatedSurahOpeningBasmalah: true,
      notes:
        'See docs/asma-basmalah-counting-policy.md. Surah-opening basmalah occurrences are excluded from name counts; in-ayah basmalah (e.g. 27:30) is counted normally.',
    },
    totalNames: traditional99.length,
    totalCountedOccurrences: totalCounted,
    totalExcludedBasmalahOccurrences: totalExcluded,
    namesWithOccurrences: traditional99.filter((n) => n.occurrenceCount > 0).length,
    namesWithZeroOccurrences: traditional99.filter((n) => n.occurrenceCount === 0).length,
    topNamesByOccurrence: top,
    topPairings,
    categoryCounts,
    names: traditional99,
    traditionalNamesCount: traditional99.length,
    divineNameAllahIncluded: false,
    allDisplayCount: traditional99.length,
    quranEvidenceNamesCount: traditional99.filter((n) => n.occurrenceCount > 0).length,
    zeroExactOccurrenceNamesCount: traditional99.filter((n) => n.occurrenceCount === 0).length,
    duplicateNamesRemoved,
    divineNameAllah,
    warnings: [
      'All names + occurrences default to needs_review.',
      'Verified meanings are NOT included in the atlas; reviewers attach them via the review workflow.',
      'Categories carry the project default classification but remain needs_review until a verified source is attached.',
      'The Divine Name "Allah" (اسم الجلالة) is exposed via `divineNameAllah` and is NOT counted inside the 99-Names list — it is the supreme Name that the 99 describe.',
    ],
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(out, null, 2), 'utf-8');
  console.log(`Wrote ${OUT_JSON}`);

  // -------- summary md --------
  const lines: string[] = [];
  lines.push("# Asmā' Allah al-Ḥusnā Atlas — Build Summary");
  lines.push('');
  lines.push(`Generated at: ${generatedAt}`);
  lines.push(`Version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Traditional 99 Names: **${out.traditionalNamesCount}**`);
  lines.push(`- Divine Name "Allah" included in main list: **${out.divineNameAllahIncluded ? 'yes' : 'no (shown separately)'}**`);
  lines.push(`- "All" tab display count: **${out.allDisplayCount}**`);
  lines.push(`- Names with explicit Quran occurrences: **${out.quranEvidenceNamesCount}**`);
  lines.push(`- Names with zero explicit occurrences: **${out.zeroExactOccurrenceNamesCount}**`);
  lines.push(`- Total counted occurrences: **${out.totalCountedOccurrences}**`);
  lines.push(`- Total excluded surah-opening basmalah occurrences: **${out.totalExcludedBasmalahOccurrences}**`);
  if (out.divineNameAllah) {
    lines.push(
      `- Divine Name "Allah" Quran occurrences: **${out.divineNameAllah.occurrenceCount}** (shown in separate hero panel)`
    );
  }
  if (out.duplicateNamesRemoved.length) {
    lines.push(`- Duplicate nameIds detected by builder: ${out.duplicateNamesRemoved.join(', ')}`);
  }
  lines.push('');
  lines.push('## Category counts');
  lines.push('');
  lines.push('| Category | Names | Counted occurrences |');
  lines.push('|---|---:|---:|');
  for (const c of categoryCounts) {
    lines.push(`| ${c.category} | ${c.names} | ${c.countedOccurrences} |`);
  }
  lines.push('');
  lines.push('## Top 25 names by occurrence');
  lines.push('');
  lines.push('| Name | Arabic | Occurrences | Surahs |');
  lines.push('|---|---|---:|---:|');
  for (const t of top) {
    lines.push(`| ${t.nameId} | ${t.arabicName} | ${t.occurrenceCount} | ${t.surahCount} |`);
  }
  lines.push('');
  lines.push('## Top 15 name pairings');
  lines.push('');
  lines.push('| First | Second | Count |');
  lines.push('|---|---|---:|');
  for (const p of topPairings) {
    lines.push(`| ${p.firstNameId} | ${p.secondNameId} | ${p.occurrenceCount} |`);
  }
  lines.push('');
  lines.push('## Warnings');
  lines.push('');
  for (const w of out.warnings) lines.push(`- ${w}`);
  lines.push('');
  lines.push('All names + occurrences are `needs_review` and `humanReviewRequired: true`. No meanings are emitted by the pipeline.');

  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);
  console.log(
    `\nDone. traditional-99=${out.traditionalNamesCount}, allDisplayCount=${out.allDisplayCount}, ` +
      `divineNameAllahIncluded=${out.divineNameAllahIncluded}, counted=${out.totalCountedOccurrences}, ` +
      `excluded=${out.totalExcludedBasmalahOccurrences}, with-occ=${out.quranEvidenceNamesCount}, ` +
      `zero-occ=${out.zeroExactOccurrenceNamesCount}` +
      (out.divineNameAllah ? `, allah-occ=${out.divineNameAllah.occurrenceCount}` : '')
  );
}

main();
