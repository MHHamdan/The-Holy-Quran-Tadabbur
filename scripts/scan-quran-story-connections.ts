#!/usr/bin/env npx tsx
/**
 * Surah-by-surah Story Connection Scanner.
 *
 * Reads:
 *   - data/raw/quran_uthmani.json (canonical Quran text; never written)
 *   - frontend/src/data/quranStoryEntitySeeds.ts (candidate dictionary)
 *   - frontend/src/data/quranStories.ts (existing curated stories)
 *
 * Writes:
 *   - frontend/src/data/generated/quranStoryConnections.json
 *   - docs/generated/quran-story-connections-summary.md
 *
 * Rules:
 *   - DOES NOT modify any Quran text.
 *   - DOES NOT generate tafsir, interpretation, or moral content.
 *   - DOES NOT emit ayah text into the output (only surah/ayah numbers).
 *   - Every detected occurrence defaults to reviewStatus = needs_review and
 *     humanReviewRequired = true.
 *   - Cluster candidates and cross-surah links inherit needs_review.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';
import {
  QURAN_STORY_ENTITY_SEEDS,
} from '../frontend/src/data/quranStoryEntitySeeds';
import { QURAN_STORIES_FIRST_BATCH } from '../frontend/src/data/quranStories';
import {
  DETECTION_CONFIDENCE,
  DETECTION_REVIEW_STATUS,
  defaultHumanReviewRequired,
  type CrossSurahLink,
  type DetectionType,
  type EntitySurahIndexEntry,
  type QuranEntityReference,
  type QuranStoryEntity,
  type ScanOutput,
  type ScanSurahEntry,
  type StoryClusterCandidate,
} from '../frontend/src/types/quranStoryConnection';

const ROOT = resolve(__dirname, '..');
const QURAN_PATH = join(ROOT, 'data/raw/quran_uthmani.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranStoryConnections.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-story-connections-summary.md');

const TOTAL_SURAHS = 114;
const TOTAL_AYAHS = 6236;

// ---------------------------------------------------------------------------
// Arabic normalisation: strip tashkeel, normalise alif/ya/hamza forms.
// ---------------------------------------------------------------------------

// U+064B..U+065F = tashkeel, U+0670 = dagger alif, U+0610..U+061A = small high marks,
// U+06D6..U+06ED = recitation marks. U+0640 = tatweel.
const ARABIC_DIACRITICS = /[ً-ٰٟؐ-ؚۖ-ۭـ]/g;

function normaliseArabic(s: string): string {
  return s
    .replace(ARABIC_DIACRITICS, '')
    .replace(/[آأإٱ]/g, 'ا') // أ إ آ ٱ (alef-wasla) -> ا
    .replace(/ى/g, 'ي')                 // ى -> ي
    .replace(/ة/g, 'ه')                 // ة -> ه (loose matching)
    .replace(/[​-‏﻿]/g, '') // BOM + zero-width
    .trim();
}

// ---------------------------------------------------------------------------
// Quran data loader
// ---------------------------------------------------------------------------

interface RawAyah {
  id?: number;
  sura_no: number;
  sura_name_ar?: string;
  sura_name_en?: string;
  aya_no: number;
  aya_text: string;
  aya_text_emlaey?: string;
}

function loadQuran(): RawAyah[] {
  if (!existsSync(QURAN_PATH)) {
    throw new Error(`Quran file not found: ${QURAN_PATH}`);
  }
  return JSON.parse(readFileSync(QURAN_PATH, 'utf-8')) as RawAyah[];
}

// ---------------------------------------------------------------------------
// Detection
// ---------------------------------------------------------------------------

interface AliasEntry {
  entityId: string;
  alias: string;
  normalised: string;
  detectionType: DetectionType;
  warningBoostSurahs?: number[];
}

function buildAliasTable(seeds: QuranStoryEntity[]): AliasEntry[] {
  const entries: AliasEntry[] = [];
  for (const seed of seeds) {
    for (const alias of seed.aliasesArabic) {
      const norm = normaliseArabic(alias);
      if (!norm) continue;
      // Aliases >= 4 chars are treated as alias_match; very short aliases
      // (<= 3) are downgraded — e.g. "سبأ" — still scanned but flagged.
      const dt: DetectionType = 'alias_match';
      entries.push({
        entityId: seed.entityId,
        alias,
        normalised: norm,
        detectionType: dt,
      });
    }
  }
  // Sort longest-first so multi-word aliases win over substrings.
  entries.sort((a, b) => b.normalised.length - a.normalised.length);
  return entries;
}

function detectInAyah(
  normAyah: string,
  aliasTable: AliasEntry[]
): Array<{ entityId: string; alias: string; detectionType: DetectionType }> {
  const found: Array<{ entityId: string; alias: string; detectionType: DetectionType }> = [];
  const seenEntityIds = new Set<string>();
  for (const entry of aliasTable) {
    if (entry.normalised.length < 3) continue; // skip too-short candidates
    if (!normAyah.includes(entry.normalised)) continue;
    // Word-boundary check. The alias must end at a word boundary so that
    // "الرس" does not match inside "الرسول". On the leading side we accept
    // attachment because Arabic clitic prefixes (و، ف، ل، ب، ك) are common.
    const idx = normAyah.indexOf(entry.normalised);
    const after = idx + entry.normalised.length < normAyah.length
      ? normAyah[idx + entry.normalised.length]
      : ' ';
    const arabicLetter = /[ء-ي]/;
    if (arabicLetter.test(after)) continue;
    if (!seenEntityIds.has(entry.entityId)) {
      found.push({
        entityId: entry.entityId,
        alias: entry.alias,
        detectionType: entry.detectionType,
      });
      seenEntityIds.add(entry.entityId);
    }
  }
  return found;
}

// ---------------------------------------------------------------------------
// Cluster grouping (adjacent ayahs with overlapping entity sets)
// ---------------------------------------------------------------------------

function groupClusters(
  surahNumber: number,
  occurrences: Array<{ ayahNumber: number; entityIds: string[] }>
): StoryClusterCandidate[] {
  if (occurrences.length === 0) return [];
  const clusters: StoryClusterCandidate[] = [];
  let cur: StoryClusterCandidate | null = null;
  const MAX_GAP = 3;
  for (const occ of occurrences) {
    if (!cur) {
      cur = {
        candidateId: `${surahNumber}:${occ.ayahNumber}`,
        surahNumber,
        ayahStart: occ.ayahNumber,
        ayahEnd: occ.ayahNumber,
        entityIds: [...occ.entityIds],
        reviewStatus: 'needs_review',
        warnings: ['Auto-clustered from adjacent entity hits; requires review.'],
      };
      continue;
    }
    if (occ.ayahNumber - cur.ayahEnd <= MAX_GAP) {
      cur.ayahEnd = occ.ayahNumber;
      for (const eid of occ.entityIds) {
        if (!cur.entityIds.includes(eid)) cur.entityIds.push(eid);
      }
    } else {
      clusters.push(cur);
      cur = {
        candidateId: `${surahNumber}:${occ.ayahNumber}`,
        surahNumber,
        ayahStart: occ.ayahNumber,
        ayahEnd: occ.ayahNumber,
        entityIds: [...occ.entityIds],
        reviewStatus: 'needs_review',
        warnings: ['Auto-clustered from adjacent entity hits; requires review.'],
      };
    }
  }
  if (cur) clusters.push(cur);
  return clusters;
}

// ---------------------------------------------------------------------------
// Existing stories → surah map (for linkedStoryId enrichment)
// ---------------------------------------------------------------------------

interface StorySurahCoverage {
  storyId: string;
  surahNumber: number;
  ayahStart: number;
  ayahEnd: number;
}

function indexExistingStories(): StorySurahCoverage[] {
  const out: StorySurahCoverage[] = [];
  for (const story of QURAN_STORIES_FIRST_BATCH) {
    for (const seg of story.storySegments) {
      out.push({
        storyId: story.storyId,
        surahNumber: seg.surahNumber,
        ayahStart: seg.ayahStart,
        ayahEnd: seg.ayahEnd,
      });
    }
  }
  return out;
}

function findLinkedStoryId(
  surahNumber: number,
  ayahStart: number,
  ayahEnd: number,
  coverage: StorySurahCoverage[]
): string | undefined {
  for (const c of coverage) {
    if (c.surahNumber !== surahNumber) continue;
    if (!(c.ayahEnd < ayahStart || c.ayahStart > ayahEnd)) {
      return c.storyId;
    }
  }
  return undefined;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  const startedAt = new Date().toISOString();
  console.log('Scanning Quran for story-connection entities...');
  const ayahs = loadQuran();
  if (ayahs.length !== TOTAL_AYAHS) {
    console.warn(`WARNING: expected ${TOTAL_AYAHS} ayahs, got ${ayahs.length}`);
  }

  const aliasTable = buildAliasTable(QURAN_STORY_ENTITY_SEEDS);
  const storyCoverage = indexExistingStories();

  // Group ayahs by surah
  const bySurah = new Map<number, RawAyah[]>();
  for (const a of ayahs) {
    if (!bySurah.has(a.sura_no)) bySurah.set(a.sura_no, []);
    bySurah.get(a.sura_no)!.push(a);
  }

  const surahs: ScanSurahEntry[] = [];
  const entityIndexMap = new Map<string, EntitySurahIndexEntry>();
  const warnings: string[] = [];
  let totalDetections = 0;
  const entityTypeCounts: Record<string, number> = {};

  for (let s = 1; s <= TOTAL_SURAHS; s++) {
    const surahAyahs = bySurah.get(s) ?? [];
    if (surahAyahs.length === 0) {
      warnings.push(`Surah ${s} not found in quran data.`);
      continue;
    }
    const detectedEntityIds = new Set<string>();
    const ayahOccurrences: Array<{ ayahNumber: number; entityIds: string[] }> = [];

    for (const a of surahAyahs) {
      const norm = normaliseArabic(a.aya_text ?? '');
      const matches = detectInAyah(norm, aliasTable);
      if (matches.length === 0) continue;
      const idsInAyah: string[] = [];
      for (const m of matches) {
        detectedEntityIds.add(m.entityId);
        idsInAyah.push(m.entityId);
        // entity index
        const slot = entityIndexMap.get(m.entityId) ?? {
          entityId: m.entityId,
          occurrences: [],
        };
        slot.occurrences.push({
          surahNumber: s,
          ayahStart: a.aya_no,
          ayahEnd: a.aya_no,
          detectionType: m.detectionType,
          matchedAliasArabic: m.alias,
        });
        entityIndexMap.set(m.entityId, slot);
        // entity type counts
        const seed = QURAN_STORY_ENTITY_SEEDS.find((e) => e.entityId === m.entityId);
        if (seed) {
          entityTypeCounts[seed.type] = (entityTypeCounts[seed.type] ?? 0) + 1;
        }
        totalDetections++;
      }
      ayahOccurrences.push({ ayahNumber: a.aya_no, entityIds: idsInAyah });
    }

    const clusterCandidates = groupClusters(s, ayahOccurrences);
    for (const c of clusterCandidates) {
      c.linkedStoryId = findLinkedStoryId(s, c.ayahStart, c.ayahEnd, storyCoverage);
    }

    // mapped storyIds: any story whose segment is in this surah
    const mappedStoryIds = Array.from(
      new Set(storyCoverage.filter((c) => c.surahNumber === s).map((c) => c.storyId))
    );

    surahs.push({
      surahNumber: s,
      surahNameArabic: surahAyahs[0].sura_name_ar,
      surahNameEnglish: surahAyahs[0].sura_name_en,
      detectedEntityIds: Array.from(detectedEntityIds),
      storyClusterCandidates: clusterCandidates,
      mappedStoryIds,
      warnings: [],
    });
  }

  // cross-surah links
  const crossSurahLinks: CrossSurahLink[] = [];
  for (const ent of entityIndexMap.values()) {
    const surahSet = new Set(ent.occurrences.map((o) => o.surahNumber));
    if (surahSet.size < 2) continue;
    const seed = QURAN_STORY_ENTITY_SEEDS.find((e) => e.entityId === ent.entityId);
    const repeatedNarrative = !!seed && seed.relatedStories.length > 0;
    crossSurahLinks.push({
      entityId: ent.entityId,
      surahNumbers: Array.from(surahSet).sort((a, b) => a - b),
      occurrenceCount: ent.occurrences.length,
      edgeType: repeatedNarrative ? 'REPEATED_NARRATIVE' : 'SAME_ENTITY',
      reviewStatus: 'needs_review',
    });
  }

  // unmapped cluster candidates
  const unmapped: string[] = [];
  for (const su of surahs) {
    for (const c of su.storyClusterCandidates) {
      if (!c.linkedStoryId) unmapped.push(c.candidateId);
    }
  }

  const scan: ScanOutput = {
    version: '1.0.0',
    generatedAt: startedAt,
    scannedSurahs: TOTAL_SURAHS,
    totalEntitiesDetected: totalDetections,
    entityTypeCounts,
    surahs,
    entityIndex: Array.from(entityIndexMap.values()).sort((a, b) =>
      a.entityId.localeCompare(b.entityId)
    ),
    crossSurahLinks: crossSurahLinks.sort((a, b) => b.occurrenceCount - a.occurrenceCount),
    unmappedClusterCandidateIds: unmapped,
    warnings,
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(scan, null, 2));
  console.log(`Wrote ${OUT_JSON}`);

  const md = buildSummaryMd(scan);
  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, md);
  console.log(`Wrote ${OUT_MD}`);

  // We DO NOT call process.exit; allow downstream tooling to chain.
}

function buildSummaryMd(scan: ScanOutput): string {
  const lines: string[] = [];
  lines.push('# Quran Story Connection Scan — Summary');
  lines.push('');
  lines.push(`Generated: ${scan.generatedAt}`);
  lines.push('');
  lines.push(`- Scanned surahs: **${scan.scannedSurahs}** / 114`);
  lines.push(`- Total entity detections: **${scan.totalEntitiesDetected}**`);
  lines.push(`- Distinct entities detected: **${scan.entityIndex.length}**`);
  lines.push(`- Cross-surah links: **${scan.crossSurahLinks.length}**`);
  lines.push(`- Unmapped cluster candidates: **${scan.unmappedClusterCandidateIds.length}**`);
  lines.push('');
  lines.push('## Entity-type counts');
  lines.push('');
  for (const [t, c] of Object.entries(scan.entityTypeCounts).sort()) {
    lines.push(`- ${t}: ${c}`);
  }
  lines.push('');
  lines.push('## Top 25 entities by occurrence');
  lines.push('');
  const top = [...scan.entityIndex]
    .sort((a, b) => b.occurrences.length - a.occurrences.length)
    .slice(0, 25);
  for (const e of top) {
    const surahs = new Set(e.occurrences.map((o) => o.surahNumber));
    lines.push(`- \`${e.entityId}\` — ${e.occurrences.length} occurrences across ${surahs.size} surahs`);
  }
  lines.push('');
  lines.push('## Surahs with zero detections');
  lines.push('');
  const zero = scan.surahs.filter((s) => s.detectedEntityIds.length === 0).map((s) => s.surahNumber);
  lines.push(zero.length === 0 ? '_None._' : zero.join(', '));
  lines.push('');
  lines.push('## Notes');
  lines.push('- All detected entities default to `needs_review` and `humanReviewRequired = true`.');
  lines.push('- This summary is generated; do not edit by hand.');
  return lines.join('\n');
}

// Re-export helpers for tests / other tools.
export {
  normaliseArabic,
  detectInAyah,
  groupClusters,
  buildAliasTable,
  DETECTION_CONFIDENCE,
  DETECTION_REVIEW_STATUS,
  defaultHumanReviewRequired,
};
export type { QuranEntityReference, ScanOutput };

main();
