#!/usr/bin/env npx tsx
/**
 * Quran Coreference Scanner — Phase U.
 *
 * Reads:
 *   - data/raw/quran_uthmani.json (canonical Quran text; never written)
 *   - frontend/src/data/quranCoreferencePatterns.ts (deterministic rules)
 *   - frontend/src/data/generated/quranEntityMentions.json (explicit anchors)
 *
 * Writes:
 *   - frontend/src/data/generated/quranCoreferenceMentions.json
 *   - frontend/src/data/generated/quranCoreferenceChains.json
 *   - docs/generated/quran-coreference-summary.md
 *
 * Safety rules:
 *   - Does not modify Quran text.
 *   - Does not emit ayah text in the output — only surah/ayah numbers and
 *     a short normalised `surfaceText` token.
 *   - All emitted mentions default to reviewStatus="needs_review" and
 *     humanReviewRequired=true.
 *   - cross_surah_candidate chains are always needs_review.
 *   - Pattern rule fires only if its surah/story/anchor constraints are
 *     satisfied.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';
import { QURAN_COREFERENCE_PATTERNS } from '../frontend/src/data/quranCoreferencePatterns';
import type {
  CoreferenceChain,
  CoreferenceChainType,
  CoreferenceChainsOutput,
  CoreferenceMention,
  CoreferencePattern,
  CoreferenceResolutionMethod,
  CoreferenceScanOutput,
  CoreferenceSurfaceType,
} from '../frontend/src/types/quranCoreference';
import type { EntityMentionScanOutput } from '../frontend/src/types/quranEntityGraph';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const QURAN_PATH = join(ROOT, 'data/raw/quran_uthmani.json');
const ENTITY_MENTIONS_PATH = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');
const OUT_MENTIONS = join(ROOT, 'frontend/src/data/generated/quranCoreferenceMentions.json');
const OUT_CHAINS = join(ROOT, 'frontend/src/data/generated/quranCoreferenceChains.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-coreference-summary.md');
const VERSION = '1.0.0';

// ---------------------------------------------------------------------------
// Arabic normalisation (mirrors the entity scanner exactly).
// ---------------------------------------------------------------------------

const ARABIC_DIACRITICS = /[ً-ٰٟؐ-ؚۖ-ۭـ]/g;

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

const ARABIC_LETTER = /[ء-ي]/;

// ---------------------------------------------------------------------------
// Loaders
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

function loadEntityMentions(): EntityMentionScanOutput {
  if (!existsSync(ENTITY_MENTIONS_PATH))
    throw new Error(`Missing ${ENTITY_MENTIONS_PATH}; run scan-quran-entity-mentions.ts first`);
  return JSON.parse(readFileSync(ENTITY_MENTIONS_PATH, 'utf-8')) as EntityMentionScanOutput;
}

// ---------------------------------------------------------------------------
// Detection
// ---------------------------------------------------------------------------

interface DetectedHit {
  pattern: CoreferencePattern;
  matchedSurface: string;
  surahNumber: number;
  ayahNumber: number;
}

function inAnyStoryRange(
  p: CoreferencePattern,
  surahNumber: number,
  ayahNumber: number
): boolean {
  if (!p.allowedStoryRanges || p.allowedStoryRanges.length === 0) return true;
  for (const r of p.allowedStoryRanges) {
    if (
      r.surahNumber === surahNumber &&
      ayahNumber >= r.ayahStart &&
      ayahNumber <= r.ayahEnd
    ) {
      return true;
    }
  }
  return false;
}

function passesSurahAllowlist(p: CoreferencePattern, surahNumber: number): boolean {
  if (!p.allowedSurahs || p.allowedSurahs.length === 0) return true;
  return p.allowedSurahs.includes(surahNumber);
}

function passesAnchor(
  p: CoreferencePattern,
  surahNumber: number,
  surahEntityIndex: Map<number, Set<string>>
): boolean {
  if (!p.requiresEntityAnchorInSurah || p.requiresEntityAnchorInSurah.length === 0) return true;
  const present = surahEntityIndex.get(surahNumber);
  if (!present) return false;
  return p.requiresEntityAnchorInSurah.some((id) => present.has(id));
}

function findSurfaceOccurrences(haystack: string, needle: string): number[] {
  const out: number[] = [];
  if (!needle || needle.length < 3) return out;
  let i = haystack.indexOf(needle);
  while (i !== -1) {
    const after = i + needle.length < haystack.length ? haystack[i + needle.length] : ' ';
    if (!ARABIC_LETTER.test(after)) out.push(i);
    i = haystack.indexOf(needle, i + 1);
  }
  return out;
}

/** Pre-normalise pattern surfaces so a pattern author can write "أمه" and
 *  have it match the post-normalisation ayah form "امه". */
function normalisePatterns(patterns: CoreferencePattern[]): CoreferencePattern[] {
  return patterns.map((p) => ({
    ...p,
    surfaceArabicNormalised: normaliseArabic(p.surfaceArabicNormalised),
  }));
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  console.log('Scanning Quran for coreference candidates...');
  const ayahs = loadQuran();
  const entities = loadEntityMentions();

  // Build per-surah index of explicit entityIds that appear there (explicit or alias).
  const surahEntityIndex = new Map<number, Set<string>>();
  // entityId → list of "S:A" strings for explicit mentions (for chain anchors).
  const explicitMentionsByEntity = new Map<
    string,
    Array<{ surahNumber: number; ayahNumber: number; mentionType: string; mentionId: string }>
  >();
  // Track entities that had ZERO explicit mentions before this scan.
  const zeroMatchEntityIds = new Set<string>();

  for (const e of entities.entities) {
    if (e.mentions.length === 0) zeroMatchEntityIds.add(e.entityId);
    const arr: Array<{ surahNumber: number; ayahNumber: number; mentionType: string; mentionId: string }> = [];
    for (const m of e.mentions) {
      const id = `em:${e.entityId}:${m.surahNumber}:${m.ayahNumber}:${m.mentionType}`;
      arr.push({
        surahNumber: m.surahNumber,
        ayahNumber: m.ayahNumber,
        mentionType: m.mentionType,
        mentionId: id,
      });
      if (m.mentionType === 'explicit_name' || m.mentionType === 'alias') {
        let s = surahEntityIndex.get(m.surahNumber);
        if (!s) {
          s = new Set();
          surahEntityIndex.set(m.surahNumber, s);
        }
        s.add(e.entityId);
      }
    }
    explicitMentionsByEntity.set(e.entityId, arr);
  }

  // ---------------- Detect ----------------
  const mentions: CoreferenceMention[] = [];
  const mentionsBySurface: Partial<Record<CoreferenceSurfaceType, number>> = {};
  const mentionsByMethod: Partial<Record<CoreferenceResolutionMethod, number>> = {};
  const warnings: string[] = [];

  // Per-pattern hit counters (used for the markdown summary).
  const patternHitCounts = new Map<string, number>();

  let nextId = 1;
  const patterns = normalisePatterns(QURAN_COREFERENCE_PATTERNS);
  for (const a of ayahs) {
    const norm = normaliseArabic(a.aya_text ?? '');
    if (!norm) continue;
    for (const p of patterns) {
      if (!passesSurahAllowlist(p, a.sura_no)) continue;
      if (!inAnyStoryRange(p, a.sura_no, a.aya_no)) continue;
      const occs = findSurfaceOccurrences(norm, p.surfaceArabicNormalised);
      if (occs.length === 0) continue;
      if (!passesAnchor(p, a.sura_no, surahEntityIndex)) continue;
      // Emit ONE mention per (pattern, ayah). Multiple occurrences in the same
      // ayah collapse to a single record (we keep phraseStart of the first).
      const phraseStart = occs[0];
      const m: CoreferenceMention = {
        mentionId: `cm_${String(nextId).padStart(6, '0')}`,
        surfaceType: p.surfaceType,
        surfaceText: p.surfaceArabicNormalised,
        surahNumber: a.sura_no,
        ayahNumber: a.aya_no,
        tokenIndex: undefined,
        phraseStart,
        phraseEnd: phraseStart + p.surfaceArabicNormalised.length,
        candidateEntityIds: [p.candidateEntityId],
        selectedEntityId: p.candidateEntityId,
        confidence: p.baseConfidence,
        resolutionMethod: p.resolutionMethod,
        evidenceReferences: [
          {
            surahNumber: a.sura_no,
            ayahStart: a.aya_no,
            sourceIds: p.sourceIds,
            evidenceType: p.resolutionMethod === 'tafsir_source' ? 'tafsir_source' : 'quran_text_pattern',
          },
        ],
        reviewStatus: 'needs_review',
        humanReviewRequired: true,
        warnings: [...(p.warnings ?? []), `Triggered by pattern \`${p.patternId}\`.`],
      };
      nextId += 1;
      mentions.push(m);
      mentionsBySurface[p.surfaceType] = (mentionsBySurface[p.surfaceType] ?? 0) + 1;
      mentionsByMethod[p.resolutionMethod] = (mentionsByMethod[p.resolutionMethod] ?? 0) + 1;
      patternHitCounts.set(p.patternId, (patternHitCounts.get(p.patternId) ?? 0) + 1);
    }
  }

  // ---------------- Same-ayah-nearest-entity ----------------
  // For every ayah with >=2 distinct explicit entities, emit IMPLICIT_CONTEXT
  // candidate links between the prophet/person entities. These are useful to
  // surface in the chain view but they are HEAVILY downgraded.
  // We do not duplicate the work already done by the existing relation builder.
  // Instead, emit one synthetic mention per (ayah, secondary entity) pointing
  // to the nearest primary entity as the candidate.
  // (Skipped to avoid noise; the relation enricher uses pattern-derived edges.)

  // ---------------- Chains ----------------
  // Group mentions by entityId. A chain is built per (entity, surah-cluster).
  // We additionally include explicit-name mentions from the entity layer as
  // anchor members so chains read as: anchor → pronoun → title.
  const chains: CoreferenceChain[] = [];
  const chainsByType: Partial<Record<CoreferenceChainType, number>> = {};
  let chainCounter = 1;

  // Group coreference mentions by entityId then by surah.
  const corefByEntity = new Map<string, CoreferenceMention[]>();
  for (const m of mentions) {
    const eid = m.selectedEntityId ?? m.candidateEntityIds[0];
    if (!eid) continue;
    let arr = corefByEntity.get(eid);
    if (!arr) {
      arr = [];
      corefByEntity.set(eid, arr);
    }
    arr.push(m);
  }

  for (const [entityId, corefMentions] of corefByEntity.entries()) {
    // Bucket by surah.
    const bySurah = new Map<number, CoreferenceMention[]>();
    for (const m of corefMentions) {
      if (!bySurah.has(m.surahNumber)) bySurah.set(m.surahNumber, []);
      bySurah.get(m.surahNumber)!.push(m);
    }

    // Per-surah chains.
    for (const [surah, list] of bySurah.entries()) {
      // Include explicit anchors that fall in the same surah.
      const explicit = (explicitMentionsByEntity.get(entityId) ?? []).filter(
        (em) => em.surahNumber === surah && em.mentionType === 'explicit_name'
      );
      const mentionIds = [
        ...explicit.map((em) => em.mentionId),
        ...list.map((cm) => cm.mentionId),
      ];
      if (mentionIds.length < 2) continue; // chains require >=2 mentions
      // ayah range (over both explicit + coref)
      const allAyahs = [
        ...explicit.map((em) => em.ayahNumber),
        ...list.map((cm) => cm.ayahNumber),
      ].sort((a, b) => a - b);
      const ayahStart = allAyahs[0];
      const ayahEnd = allAyahs[allAyahs.length - 1];
      // chainType: local_passage if the ayah window <=10, else surah_level.
      const chainType: CoreferenceChainType =
        ayahEnd - ayahStart <= 10 ? 'local_passage' : 'surah_level';
      const confidence =
        list.reduce((acc, m) => acc + m.confidence, 0) / list.length;
      chains.push({
        chainId: `chain_${String(chainCounter).padStart(6, '0')}`,
        entityId,
        mentions: mentionIds,
        surahScope: [surah],
        ayahRangeStart: `${surah}:${ayahStart}`,
        ayahRangeEnd: `${surah}:${ayahEnd}`,
        chainType,
        confidence: Math.round(confidence * 100) / 100,
        reviewStatus: 'needs_review',
        humanReviewRequired: true,
        warnings: [],
      });
      chainCounter += 1;
      chainsByType[chainType] = (chainsByType[chainType] ?? 0) + 1;
    }

    // Cross-surah candidate chain (always needs_review).
    const surahs = Array.from(bySurah.keys()).sort((a, b) => a - b);
    if (surahs.length >= 2) {
      const ayahs = corefMentions
        .map((m) => ({ s: m.surahNumber, a: m.ayahNumber }))
        .sort((a, b) => (a.s !== b.s ? a.s - b.s : a.a - b.a));
      const start = ayahs[0];
      const end = ayahs[ayahs.length - 1];
      chains.push({
        chainId: `chain_${String(chainCounter).padStart(6, '0')}`,
        entityId,
        mentions: corefMentions.map((m) => m.mentionId),
        surahScope: surahs,
        ayahRangeStart: `${start.s}:${start.a}`,
        ayahRangeEnd: `${end.s}:${end.a}`,
        chainType: 'cross_surah_candidate',
        confidence: 0.5,
        reviewStatus: 'needs_review',
        humanReviewRequired: true,
        warnings: [
          'Cross-surah candidate chain — needs scholar review before promotion.',
        ],
      });
      chainCounter += 1;
      chainsByType.cross_surah_candidate = (chainsByType.cross_surah_candidate ?? 0) + 1;
    }
  }

  // ---------------- Zero-match improvement tracking ----------------
  const improved = new Set<string>();
  for (const m of mentions) {
    for (const cid of m.candidateEntityIds) {
      if (zeroMatchEntityIds.has(cid)) improved.add(cid);
    }
  }

  // ---------------- Emit ----------------
  const generatedAt = new Date().toISOString();
  const mentionsOut: CoreferenceScanOutput = {
    version: VERSION,
    generatedAt,
    totalMentions: mentions.length,
    totalChains: chains.length,
    mentionsBySurfaceType: mentionsBySurface,
    mentionsByResolutionMethod: mentionsByMethod,
    zeroMatchEntitiesImproved: Array.from(improved).sort(),
    mentions,
    warnings: [
      'All coreference mentions default to needs_review.',
      'Cross-surah chains are always needs_review.',
      'No Quran text is embedded; only short normalised surface tokens are kept.',
    ],
  };
  const chainsOut: CoreferenceChainsOutput = {
    version: VERSION,
    generatedAt,
    totalChains: chains.length,
    chainsByType,
    chains,
    warnings: [
      'Chains are observational. No identity is asserted unless a reviewer promotes the chain.',
    ],
  };

  mkdirSync(dirname(OUT_MENTIONS), { recursive: true });
  writeFileSync(OUT_MENTIONS, JSON.stringify(mentionsOut, null, 2), 'utf-8');
  writeFileSync(OUT_CHAINS, JSON.stringify(chainsOut, null, 2), 'utf-8');
  console.log(`Wrote ${OUT_MENTIONS}`);
  console.log(`Wrote ${OUT_CHAINS}`);

  // ---------------- Summary md ----------------
  const lines: string[] = [];
  lines.push('# Quran Coreference — Scan Summary');
  lines.push('');
  lines.push(`Generated at: ${generatedAt}`);
  lines.push(`Scanner version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Coreference mention candidates: **${mentions.length}**`);
  lines.push(`- Coreference chains: **${chains.length}**`);
  lines.push(`- Zero-match entities improved by implicit candidates: **${improved.size}**`);
  lines.push('');
  lines.push('## Mentions by surfaceType');
  lines.push('');
  lines.push('| Surface | Count |');
  lines.push('|---|---:|');
  for (const [k, v] of Object.entries(mentionsBySurface).sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))) {
    lines.push(`| ${k} | ${v} |`);
  }
  lines.push('');
  lines.push('## Mentions by resolutionMethod');
  lines.push('');
  lines.push('| Method | Count |');
  lines.push('|---|---:|');
  for (const [k, v] of Object.entries(mentionsByMethod).sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))) {
    lines.push(`| ${k} | ${v} |`);
  }
  lines.push('');
  lines.push('## Patterns triggered');
  lines.push('');
  lines.push('| Pattern | Hits |');
  lines.push('|---|---:|');
  for (const p of patterns) {
    lines.push(`| \`${p.patternId}\` | ${patternHitCounts.get(p.patternId) ?? 0} |`);
  }
  lines.push('');
  lines.push('## Chains by type');
  lines.push('');
  lines.push('| Type | Count |');
  lines.push('|---|---:|');
  for (const [k, v] of Object.entries(chainsByType)) {
    lines.push(`| ${k} | ${v} |`);
  }
  lines.push('');
  // Per-entity highlights
  const featured: Array<{ entityId: string; label: string }> = [
    { entityId: 'entity_person_maryam', label: 'Maryam' },
    { entityId: 'entity_prophet_musa', label: 'Musa' },
    { entityId: 'entity_people_ashab_kahf', label: 'People of the Cave' },
    { entityId: 'entity_animal_dog_cave', label: 'Dog of the Cave' },
    { entityId: 'entity_object_staff_musa', label: 'Staff of Musa' },
    { entityId: 'entity_object_throne_bilqis', label: 'Throne of Bilqis' },
    { entityId: 'entity_person_bilqis', label: 'Bilqis' },
    { entityId: 'entity_person_hawwa', label: 'Hawwa' },
  ];
  lines.push('## Featured-entity coreference summary');
  lines.push('');
  lines.push('| Entity | Coreference mentions | Chains |');
  lines.push('|---|---:|---:|');
  for (const f of featured) {
    const m = mentions.filter((mm) => (mm.selectedEntityId ?? '') === f.entityId).length;
    const c = chains.filter((ch) => ch.entityId === f.entityId).length;
    lines.push(`| ${f.label} | ${m} | ${c} |`);
  }
  lines.push('');
  lines.push('## Warnings');
  lines.push('');
  for (const w of mentionsOut.warnings) lines.push(`- ${w}`);
  lines.push('');
  lines.push('All implicit links default to `needs_review` and `humanReviewRequired: true`. No tafsir is generated.');

  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);
  console.log(`\nDone. mentions=${mentions.length}, chains=${chains.length}, improved=${improved.size}`);
  if (warnings.length > 0) {
    console.warn(`Warnings: ${warnings.length}`);
    for (const w of warnings) console.warn(`  - ${w}`);
  }
}

main();
