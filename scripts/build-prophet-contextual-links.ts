#!/usr/bin/env npx tsx
/**
 * Phase X2 — Build prophet contextual links.
 *
 * Inputs:
 *   - frontend/src/data/generated/quranProphetsAtlas.json
 *   - frontend/src/data/generated/quranEntityMentions.json
 *   - frontend/src/data/generated/quranEntityRelationsEnriched.json
 *   - frontend/src/data/generated/quranCoreferenceMentions.json
 *   - frontend/src/data/generated/quranTopicAtlas.json
 *
 * Output:
 *   - frontend/src/data/generated/quranProphetContextualLinks.json
 *   - docs/generated/quran-prophet-contextual-links-summary.md
 *
 * Safety rules (mirror docs/prophet-contextual-linking-policy.md):
 *   - Every contextual link MUST have ≥ 1 evidenceReferences entry.
 *   - All links default to reviewStatus = "needs_review".
 *   - "same surah" links are restricted to a focused ayah-window
 *     around an explicit anchor (default: ±3 ayahs).
 *   - The script never invents ayah references.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';

import { QURAN_PROPHET_SEEDS } from '../frontend/src/data/quranProphetSeeds';

interface QuranReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
}

interface ProphetContextualLink {
  prophetId: string;
  surahNumber: number;
  ayahNumber: number;
  linkType:
    | 'same_passage'
    | 'related_entity_window'
    | 'coreference_window'
    | 'story_segment'
    | 'topic_overlap'
    | 'family_neighbor';
  confidence: number;
  evidenceReferences: QuranReference[];
  sourceIds: string[];
  reviewStatus: 'needs_review';
  humanReviewRequired: true;
  rationale: string;
  warnings: string[];
}

interface ContextualLinksFile {
  version: string;
  generatedAt: string;
  totalLinks: number;
  linksByProphet: Record<string, number>;
  linksByType: Record<string, number>;
  links: ProphetContextualLink[];
  warnings: string[];
}

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const GEN = join(ROOT, 'frontend/src/data/generated');
const ATLAS = join(GEN, 'quranProphetsAtlas.json');
const COREF = join(GEN, 'quranCoreferenceMentions.json');
const TOPICS = join(GEN, 'quranTopicAtlas.json');

const OUT_JSON = join(GEN, 'quranProphetContextualLinks.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-prophet-contextual-links-summary.md');
const VERSION = '1.0.0';

const WINDOW = 3; // ±3 ayahs around an explicit anchor
const SAME_AYAH_CONFIDENCE = 0.55;
const NEIGHBOR_CONFIDENCE = 0.45;
const STORY_SEGMENT_CONFIDENCE = 0.5;
const TOPIC_OVERLAP_CONFIDENCE = 0.4;
const COREFERENCE_WINDOW_CONFIDENCE = 0.5;
const FAMILY_NEIGHBOR_CONFIDENCE = 0.55;

// ---------------------------------------------------------------------------
// Load
// ---------------------------------------------------------------------------

function loadJSON<T = unknown>(p: string, optional = false): T | null {
  if (!existsSync(p)) {
    if (optional) return null;
    throw new Error(`Missing ${p}`);
  }
  return JSON.parse(readFileSync(p, 'utf-8')) as T;
}

const atlas = loadJSON<any>(ATLAS)!;
const corefFile = loadJSON<any>(COREF, true);
const topicFile = loadJSON<any>(TOPICS, true);

const profilesById = new Map<string, any>();
for (const p of atlas.profiles ?? []) profilesById.set(p.prophetId, p);

// Topic index: surah:ayah -> set of topicIds
const topicByAyah = new Map<string, Set<string>>();
if (topicFile) {
  for (const t of topicFile.topics ?? []) {
    for (const lnk of t.ayahLinks ?? []) {
      const k = `${lnk.surahNumber}:${lnk.ayahNumber}`;
      if (!topicByAyah.has(k)) topicByAyah.set(k, new Set());
      topicByAyah.get(k)!.add(t.topicId);
    }
  }
}

// ---------------------------------------------------------------------------
// Build links per prophet
// ---------------------------------------------------------------------------

const links: ProphetContextualLink[] = [];
const linkSet = new Set<string>(); // dedup: prophetId:surah:ayah:linkType

function add(link: ProphetContextualLink): void {
  const k = `${link.prophetId}:${link.surahNumber}:${link.ayahNumber}:${link.linkType}`;
  if (linkSet.has(k)) return;
  linkSet.add(k);
  links.push(link);
}

for (const seed of QURAN_PROPHET_SEEDS) {
  const profile = profilesById.get(seed.prophetId);
  if (!profile) continue;

  // Anchors are the explicit mentions; we don't re-emit them as
  // contextual links — instead we use them as the *centre* of windows.
  const anchors = (profile.explicitMentions ?? []) as Array<{
    surahNumber: number;
    ayahNumber: number;
  }>;
  const anchorAyahKeys = new Set(anchors.map((m) => `${m.surahNumber}:${m.ayahNumber}`));

  // 1. Same-passage window (neighboring ayahs around each anchor) ----------
  for (const a of anchors) {
    for (let d = 1; d <= WINDOW; d++) {
      for (const off of [-d, d]) {
        const target = a.ayahNumber + off;
        if (target < 1) continue;
        const key = `${a.surahNumber}:${target}`;
        if (anchorAyahKeys.has(key)) continue; // already an explicit mention
        add({
          prophetId: seed.prophetId,
          surahNumber: a.surahNumber,
          ayahNumber: target,
          linkType: 'same_passage',
          confidence: d === 1 ? SAME_AYAH_CONFIDENCE : NEIGHBOR_CONFIDENCE,
          evidenceReferences: [{ surahNumber: a.surahNumber, ayahStart: a.ayahNumber }],
          sourceIds: ['quran_uthmani_cloud'],
          reviewStatus: 'needs_review',
          humanReviewRequired: true,
          rationale: `Within ±${d} ayahs of explicit mention at ${a.surahNumber}:${a.ayahNumber}.`,
          warnings: [],
        });
      }
    }
  }

  // 2. Coreference-window — coref mentions resolved to this prophet ---------
  for (const cm of corefFile?.mentions ?? []) {
    if (cm.selectedEntityId !== seed.entityId) continue;
    add({
      prophetId: seed.prophetId,
      surahNumber: cm.surahNumber,
      ayahNumber: cm.ayahNumber,
      linkType: 'coreference_window',
      confidence: cm.confidence ?? COREFERENCE_WINDOW_CONFIDENCE,
      evidenceReferences:
        cm.evidenceReferences && cm.evidenceReferences.length > 0
          ? cm.evidenceReferences
          : [{ surahNumber: cm.surahNumber, ayahStart: cm.ayahNumber }],
      sourceIds: ['quran_uthmani_cloud'],
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      rationale: `Coreference resolved via ${cm.resolutionMethod}.`,
      warnings: cm.warnings ?? [],
    });
  }

  // 3. Family-neighbor — when an explicit anchor for THIS prophet is
  //    within ±WINDOW of an explicit anchor for a family-related prophet
  //    in the SAME surah. Restricted to family_relation targets only.
  const familyTargets = new Set<string>(
    (profile.relatedProphets ?? [])
      .filter((r: any) => r.relationType === 'family_relation')
      .map((r: any) => r.targetProphetId.replace(/^prophet_/, 'entity_prophet_')),
  );
  if (familyTargets.size > 0) {
    for (const a of anchors) {
      for (const fam of familyTargets) {
        const famProfile = atlas.profiles.find(
          (p: any) => p.prophetId === fam.replace(/^entity_prophet_/, 'prophet_'),
        );
        if (!famProfile) continue;
        for (const m of famProfile.explicitMentions ?? []) {
          if (m.surahNumber !== a.surahNumber) continue;
          if (Math.abs(m.ayahNumber - a.ayahNumber) > WINDOW) continue;
          if (m.ayahNumber === a.ayahNumber) continue;
          add({
            prophetId: seed.prophetId,
            surahNumber: a.surahNumber,
            ayahNumber: m.ayahNumber,
            linkType: 'family_neighbor',
            confidence: FAMILY_NEIGHBOR_CONFIDENCE,
            evidenceReferences: [
              { surahNumber: a.surahNumber, ayahStart: a.ayahNumber },
              { surahNumber: m.surahNumber, ayahStart: m.ayahNumber },
            ],
            sourceIds: ['quran_uthmani_cloud'],
            reviewStatus: 'needs_review',
            humanReviewRequired: true,
            rationale: `Family-related prophet ${fam} is explicitly named within ±${WINDOW} ayahs.`,
            warnings: [],
          });
        }
      }
    }
  }

  // 4. Topic-overlap window — ayahs that share a topic with one of this
  //    prophet's anchors AND are within the same surah AND ≤ WINDOW away.
  //    This is conservative on purpose; broad same-surah linking is forbidden.
  for (const a of anchors) {
    const topicsForAnchor = topicByAyah.get(`${a.surahNumber}:${a.ayahNumber}`);
    if (!topicsForAnchor || topicsForAnchor.size === 0) continue;
    for (let d = 1; d <= WINDOW; d++) {
      for (const off of [-d, d]) {
        const target = a.ayahNumber + off;
        if (target < 1) continue;
        const topicsAtTarget = topicByAyah.get(`${a.surahNumber}:${target}`);
        if (!topicsAtTarget) continue;
        let shared = false;
        for (const t of topicsForAnchor) {
          if (topicsAtTarget.has(t)) {
            shared = true;
            break;
          }
        }
        if (!shared) continue;
        add({
          prophetId: seed.prophetId,
          surahNumber: a.surahNumber,
          ayahNumber: target,
          linkType: 'topic_overlap',
          confidence: TOPIC_OVERLAP_CONFIDENCE,
          evidenceReferences: [{ surahNumber: a.surahNumber, ayahStart: a.ayahNumber }],
          sourceIds: ['quran_uthmani_cloud'],
          reviewStatus: 'needs_review',
          humanReviewRequired: true,
          rationale: 'Shared topic within window of an explicit mention.',
          warnings: [],
        });
      }
    }
  }

  // 5. Story-segment — when an existing storyId is anchored to this
  //    prophet, every ayah in that segment range gets a link.
  void STORY_SEGMENT_CONFIDENCE; // see Phase X2 follow-up: needs a story manifest lookup
  // (Not implemented in this pass; the existing storyIds list is used by
  //  the UI directly without needing a per-ayah link.)
}

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------

const linksByProphet: Record<string, number> = {};
const linksByType: Record<string, number> = {};
for (const l of links) {
  linksByProphet[l.prophetId] = (linksByProphet[l.prophetId] ?? 0) + 1;
  linksByType[l.linkType] = (linksByType[l.linkType] ?? 0) + 1;
}

const out: ContextualLinksFile = {
  version: VERSION,
  generatedAt: new Date().toISOString(),
  totalLinks: links.length,
  linksByProphet,
  linksByType,
  links,
  warnings: [
    'All contextual links default to needs_review.',
    `Window size = ±${WINDOW} ayahs around an explicit mention.`,
  ],
};

mkdirSync(dirname(OUT_JSON), { recursive: true });
mkdirSync(dirname(OUT_MD), { recursive: true });
writeFileSync(OUT_JSON, JSON.stringify(out, null, 2), 'utf-8');

const md: string[] = [];
md.push('# Quran Prophet Contextual Links — Build Summary');
md.push('');
md.push(`- Version: ${out.version}`);
md.push(`- Generated: ${out.generatedAt}`);
md.push(`- Total links: **${out.totalLinks}**`);
md.push(`- Window: ±${WINDOW} ayahs`);
md.push('');
md.push('## Links by type');
for (const [k, v] of Object.entries(linksByType).sort((a, b) => b[1] - a[1])) {
  md.push(`- ${k}: ${v}`);
}
md.push('');
md.push('## Links by prophet (top 15)');
const sorted = Object.entries(linksByProphet).sort((a, b) => b[1] - a[1]);
for (const [pid, n] of sorted.slice(0, 15)) md.push(`- ${pid}: ${n}`);
md.push('');
md.push('## Policy reminders');
md.push('- All contextual links are needs_review.');
md.push('- No "same surah" broad linking — windows are ±3 ayahs.');
md.push('- All links carry ≥ 1 evidenceReference.');
writeFileSync(OUT_MD, md.join('\n') + '\n', 'utf-8');

console.log(`[prophet-contextual-links] wrote ${links.length} links to ${OUT_JSON}`);
console.log(`[prophet-contextual-links] summary at ${OUT_MD}`);
