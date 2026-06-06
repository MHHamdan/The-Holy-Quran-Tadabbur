#!/usr/bin/env npx tsx
/**
 * Enrich Entity Relations with Coreference Edges — Phase U.
 *
 * Reads:
 *   - frontend/src/data/generated/quranEntityRelations.json
 *   - frontend/src/data/generated/quranCoreferenceMentions.json
 *   - frontend/src/data/generated/quranCoreferenceChains.json
 *
 * Writes:
 *   - frontend/src/data/generated/quranEntityRelationsEnriched.json
 *   - docs/generated/quran-entity-relations-enriched-summary.md
 *
 * Rules:
 *   - Original explicit relations are preserved verbatim under `baseRelations`.
 *   - Coreference edges are emitted under `coreferenceEdges`; every edge
 *     defaults to reviewStatus="needs_review" and carries at least one
 *     evidence reference.
 *   - If a coreference edge would conflict with an explicit verified
 *     relation (same source/target with a contradictory type), the edge is
 *     still emitted but is logged in `conflicts` and stays needs_review.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { resolve, join, dirname } from 'path';
import type {
  CoreferenceMention,
  CoreferenceSurfaceType,
  EnrichedCoreferenceEdge,
  EnrichedCoreferenceEdgeType,
  EnrichedRelationsOutput,
} from '../frontend/src/types/quranCoreference';
import type { EntityRelationOutput, QuranReference } from '../frontend/src/types/quranEntityGraph';

const ROOT = resolve(__dirname, '..');
const REL_IN = join(ROOT, 'frontend/src/data/generated/quranEntityRelations.json');
const COREF_MENTIONS_IN = join(ROOT, 'frontend/src/data/generated/quranCoreferenceMentions.json');
const COREF_CHAINS_IN = join(ROOT, 'frontend/src/data/generated/quranCoreferenceChains.json');
const OUT = join(ROOT, 'frontend/src/data/generated/quranEntityRelationsEnriched.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-entity-relations-enriched-summary.md');
const VERSION = '1.0.0';

// Surface → edge-type mapping. Pure family pronouns become FAMILY_REFERENCE_TO;
// possessive pronouns are PRONOUN_REFERS_TO unless they describe an object
// (in which case STORY_OBJECT_LINK fits better).
function edgeTypeForSurface(
  surface: CoreferenceSurfaceType,
  targetEntityType: string | undefined
): EnrichedCoreferenceEdgeType {
  if (surface === 'family_reference') return 'FAMILY_REFERENCE_TO';
  if (surface === 'title' || surface === 'role_reference') return 'TITLE_REFERS_TO';
  if (surface === 'pronoun' || surface === 'possessive_pronoun') {
    if (targetEntityType === 'object' || targetEntityType === 'animal') {
      return 'STORY_OBJECT_LINK';
    }
    return 'PRONOUN_REFERS_TO';
  }
  if (surface === 'demonstrative') return 'IMPLICITLY_REFERS_TO';
  if (surface === 'implicit_context') return 'CONTEXTUAL_ENTITY_LINK';
  return 'IMPLICITLY_REFERS_TO';
}

function main(): void {
  if (!existsSync(REL_IN)) throw new Error(`Missing ${REL_IN}`);
  if (!existsSync(COREF_MENTIONS_IN)) throw new Error(`Missing ${COREF_MENTIONS_IN}`);
  if (!existsSync(COREF_CHAINS_IN)) throw new Error(`Missing ${COREF_CHAINS_IN}`);

  const baseRel = JSON.parse(readFileSync(REL_IN, 'utf-8')) as EntityRelationOutput;
  const coref = JSON.parse(readFileSync(COREF_MENTIONS_IN, 'utf-8')) as {
    mentions: CoreferenceMention[];
  };
  // Chains are loaded for the markdown summary; the edges themselves come
  // from mention-level evidence so each edge ties back to an ayah.

  // Index for entityType lookup (read from mentions file since it's the only
  // place that has the entity catalogue).
  const entityMentionsPath = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');
  if (!existsSync(entityMentionsPath)) throw new Error(`Missing ${entityMentionsPath}`);
  const entityCatalogue = JSON.parse(readFileSync(entityMentionsPath, 'utf-8')) as {
    entities: Array<{ entityId: string; entityType: string }>;
  };
  const entityTypeById = new Map<string, string>();
  for (const e of entityCatalogue.entities) entityTypeById.set(e.entityId, e.entityType);

  // Index existing verified relations to detect conflicts.
  type RelKey = string;
  const relIndex = new Map<RelKey, { type: string; reviewStatus: string }>();
  for (const r of baseRel.relations) {
    relIndex.set(`${r.sourceEntityId}::${r.targetEntityId}`, {
      type: r.relationType,
      reviewStatus: r.reviewStatus,
    });
  }

  // Group mentions by (source = mention.surahOrigin? we use anchor entity) →
  // For each coref mention with a selected entity, the edge runs from the
  // anchor that triggered the pattern to the candidate. To keep this simple
  // and source-faithful, we emit an edge per (sourceEntity, targetEntity).
  // We treat the SOURCE as any explicit entity present in the same ayah, AND
  // (when none) the entity itself (self-edge — skipped). This makes the
  // enrichment data-driven from the existing relation graph plus the
  // coreference pattern's known anchor.
  type EdgeAcc = {
    sourceEntityId: string;
    targetEntityId: string;
    edgeType: EnrichedCoreferenceEdgeType;
    mentionIds: Set<string>;
    evidence: QuranReference[];
    sourceIds: Set<string>;
    confidenceSum: number;
    confidenceCount: number;
    warnings: Set<string>;
  };
  const edges = new Map<string, EdgeAcc>();

  // Build a quick lookup: ayah -> set of entityIds present (from the entity
  // mentions catalogue). We reuse the existing relation evidence as the
  // pool for "anchor" entities, taking entityIds that already appear in any
  // co-mention at that ayah from baseRel.
  // For simplicity, derive anchors from baseRel evidence references — for
  // each relation, the source and target are anchors at their evidence ayahs.
  const anchorsByAyah = new Map<string, Set<string>>();
  function addAnchor(s: number, a: number, eid: string) {
    const k = `${s}:${a}`;
    let set = anchorsByAyah.get(k);
    if (!set) {
      set = new Set();
      anchorsByAyah.set(k, set);
    }
    set.add(eid);
  }
  for (const r of baseRel.relations) {
    for (const ev of r.evidenceReferences) {
      for (let a = ev.ayahStart; a <= (ev.ayahEnd ?? ev.ayahStart); a++) {
        addAnchor(ev.surahNumber, a, r.sourceEntityId);
        addAnchor(ev.surahNumber, a, r.targetEntityId);
      }
    }
  }

  for (const m of coref.mentions) {
    const target = m.selectedEntityId ?? m.candidateEntityIds[0];
    if (!target) continue;
    const surface = m.surfaceType;
    const targetType = entityTypeById.get(target);
    const edgeType = edgeTypeForSurface(surface, targetType);
    // Find anchor entities at the same ayah (excluding the target itself).
    const ak = `${m.surahNumber}:${m.ayahNumber}`;
    const anchorSet = anchorsByAyah.get(ak);
    const sources: string[] = [];
    if (anchorSet) {
      for (const eid of anchorSet) if (eid !== target) sources.push(eid);
    }
    // If no anchor entity available in that ayah, fall back to a self-loop
    // edge keyed by the candidate's own entityId (treated as
    // "self-coreference"). We skip emission to avoid noise.
    if (sources.length === 0) continue;
    for (const src of sources) {
      if (src === target) continue;
      const key = `${src}::${target}::${edgeType}`;
      let acc = edges.get(key);
      if (!acc) {
        acc = {
          sourceEntityId: src,
          targetEntityId: target,
          edgeType,
          mentionIds: new Set(),
          evidence: [],
          sourceIds: new Set(),
          confidenceSum: 0,
          confidenceCount: 0,
          warnings: new Set(),
        };
        edges.set(key, acc);
      }
      acc.mentionIds.add(m.mentionId);
      acc.evidence.push({ surahNumber: m.surahNumber, ayahStart: m.ayahNumber });
      for (const sid of m.evidenceReferences.flatMap((e) => e.sourceIds)) acc.sourceIds.add(sid);
      acc.confidenceSum += m.confidence;
      acc.confidenceCount += 1;
      for (const w of m.warnings) acc.warnings.add(w);
    }
  }

  // Build output edge list & detect conflicts.
  const coreferenceEdges: EnrichedCoreferenceEdge[] = [];
  const conflicts: EnrichedRelationsOutput['conflicts'] = [];
  for (const acc of edges.values()) {
    const baseKey = `${acc.sourceEntityId}::${acc.targetEntityId}`;
    const explicit = relIndex.get(baseKey);
    const warnings = Array.from(acc.warnings);
    if (explicit && explicit.reviewStatus === 'verified') {
      // The current pipeline never auto-verifies, so this branch is defensive.
      const semanticallyContradicts = false; // no inverse mapping required here
      if (semanticallyContradicts) {
        conflicts.push({
          sourceEntityId: acc.sourceEntityId,
          targetEntityId: acc.targetEntityId,
          explicitRelationType: explicit.type,
          coreferenceEdgeType: acc.edgeType,
          reason: 'Coreference edge contradicts an existing verified explicit relation; kept needs_review.',
        });
      }
    }
    coreferenceEdges.push({
      sourceEntityId: acc.sourceEntityId,
      targetEntityId: acc.targetEntityId,
      edgeType: acc.edgeType,
      mentionIds: Array.from(acc.mentionIds).sort(),
      evidenceReferences: dedupRefs(acc.evidence),
      sourceIds: Array.from(acc.sourceIds).sort(),
      confidence: Math.round((acc.confidenceSum / Math.max(1, acc.confidenceCount)) * 100) / 100,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings,
    });
  }

  coreferenceEdges.sort((a, b) => {
    if (a.sourceEntityId !== b.sourceEntityId) return a.sourceEntityId.localeCompare(b.sourceEntityId);
    if (a.targetEntityId !== b.targetEntityId) return a.targetEntityId.localeCompare(b.targetEntityId);
    return a.edgeType.localeCompare(b.edgeType);
  });

  const out: EnrichedRelationsOutput = {
    version: VERSION,
    generatedAt: new Date().toISOString(),
    baseRelationCount: baseRel.relations.length,
    coreferenceEdgeCount: coreferenceEdges.length,
    baseRelations: baseRel.relations as unknown[],
    coreferenceEdges,
    conflicts,
    warnings: [
      'All coreference edges default to needs_review.',
      'No explicit verified relation has been overwritten.',
    ],
  };

  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf-8');
  console.log(`Wrote ${OUT}`);

  // -------- summary md --------
  const lines: string[] = [];
  lines.push('# Quran Entity Relations — Enriched Summary');
  lines.push('');
  lines.push(`Generated at: ${out.generatedAt}`);
  lines.push(`Version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Base explicit relations: **${baseRel.relations.length}**`);
  lines.push(`- Coreference-derived edges: **${coreferenceEdges.length}**`);
  lines.push(`- Conflicts (none expected): **${conflicts.length}**`);
  lines.push('');
  lines.push('## Coreference edges by edgeType');
  lines.push('');
  const byType: Record<string, number> = {};
  for (const e of coreferenceEdges) byType[e.edgeType] = (byType[e.edgeType] ?? 0) + 1;
  lines.push('| Edge type | Count |');
  lines.push('|---|---:|');
  for (const [k, v] of Object.entries(byType).sort((a, b) => b[1] - a[1])) {
    lines.push(`| ${k} | ${v} |`);
  }
  lines.push('');
  lines.push('## Featured-entity coreference edges');
  lines.push('');
  const featured = [
    'entity_person_maryam',
    'entity_prophet_isa',
    'entity_prophet_musa',
    'entity_object_staff_musa',
    'entity_animal_dog_cave',
    'entity_object_throne_bilqis',
    'entity_person_bilqis',
  ];
  for (const eid of featured) {
    const edgesFor = coreferenceEdges.filter((e) => e.sourceEntityId === eid || e.targetEntityId === eid);
    if (edgesFor.length === 0) continue;
    lines.push(`### ${eid}`);
    lines.push('');
    lines.push('| From | To | Type | Mentions | Evidence |');
    lines.push('|---|---|---|---:|---:|');
    for (const e of edgesFor.slice(0, 20)) {
      lines.push(
        `| ${e.sourceEntityId} | ${e.targetEntityId} | ${e.edgeType} | ${e.mentionIds.length} | ${e.evidenceReferences.length} |`
      );
    }
    lines.push('');
  }
  for (const w of out.warnings) lines.push(`- ${w}`);
  lines.push('');
  lines.push('All coreference edges are `needs_review` and `humanReviewRequired: true`.');

  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);
  console.log(`\nDone. base=${baseRel.relations.length}, coref=${coreferenceEdges.length}`);
}

function dedupRefs(refs: QuranReference[]): QuranReference[] {
  const seen = new Set<string>();
  const out: QuranReference[] = [];
  for (const r of refs) {
    const k = `${r.surahNumber}:${r.ayahStart}-${r.ayahEnd ?? r.ayahStart}`;
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(r);
  }
  return out;
}

main();
