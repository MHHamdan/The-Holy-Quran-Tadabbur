#!/usr/bin/env npx tsx
/**
 * Quran Entity Relation Extractor — Entity-Centered GraphRAG.
 *
 * Reads:
 *   - frontend/src/data/generated/quranEntityMentions.json (scan output)
 *   - frontend/src/data/quranEntitySeeds.ts (seed knownRelatives)
 *
 * Writes:
 *   - frontend/src/data/generated/quranEntityRelations.json
 *   - docs/generated/quran-entity-relations-summary.md
 *
 * Rules:
 *   - Every relation MUST carry at least one evidenceReferences entry.
 *   - All relations default to reviewStatus = "needs_review" and
 *     humanReviewRequired = true.
 *   - Explanations are generic and source-aware; the script never invents
 *     tafsir.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';
import { QURAN_ENTITY_SEEDS } from '../frontend/src/data/quranEntitySeeds';
import type {
  EntityMention,
  EntityMentionScanOutput,
  EntityRelation,
  EntityRelationOutput,
  EntityRelationType,
  QuranReference,
} from '../frontend/src/types/quranEntityGraph';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const MENTIONS_PATH = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranEntityRelations.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-entity-relations-summary.md');
const VERSION = '1.0.0';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const GENERIC_EXPLANATION_AR =
  'ترتبط هذه الآيات لأنها تذكر هاتين الذاتين في سياق قرآني واحد، ويحتاج التفصيل إلى مراجعة تفسيرية.';
const GENERIC_EXPLANATION_EN =
  'These ayahs are linked because both entities appear in the same Quranic context. Detailed interpretation requires tafsir review.';

function refKey(r: QuranReference): string {
  return `${r.surahNumber}:${r.ayahStart}-${r.ayahEnd ?? r.ayahStart}`;
}

function relationKey(a: string, b: string, type: EntityRelationType): string {
  return `${a}::${type}::${b}`;
}

// Map family-relation types to their inverse for symmetric emission.
const INVERSE: Partial<Record<EntityRelationType, EntityRelationType>> = {
  mother_of: 'son_of',
  son_of: 'mother_of',
  father_of: 'son_of',
  daughter_of: 'mother_of',
  wife_of: 'husband_of',
  husband_of: 'wife_of',
  brother_of: 'brother_of',
  sister_of: 'sister_of',
  guardian_of: 'family_of',
  family_of: 'family_of',
  same_story: 'same_story',
  same_event: 'same_event',
  same_surah_context: 'same_surah_context',
  theological_discussion: 'theological_discussion',
  chronological_before: 'chronological_after',
  chronological_after: 'chronological_before',
  related_theme: 'related_theme',
  related_tafsir: 'related_tafsir',
  mentioned_with: 'mentioned_with',
};

// ---------------------------------------------------------------------------
// Relation builder
// ---------------------------------------------------------------------------

class RelationBuilder {
  // keyed by `${entityA}::${type}::${entityB}` for de-duplication
  private map = new Map<string, EntityRelation>();

  add(opts: {
    source: string;
    target: string;
    type: EntityRelationType;
    evidence: QuranReference;
    sourceIds: string[];
    confidence: number;
    explanationAr?: string;
    explanationEn?: string;
    warnings?: string[];
    // emit the symmetric/inverse relation as well
    symmetric?: boolean;
  }): void {
    this.upsert(
      opts.source,
      opts.target,
      opts.type,
      opts.evidence,
      opts.sourceIds,
      opts.confidence,
      opts.explanationAr,
      opts.explanationEn,
      opts.warnings ?? []
    );
    if (opts.symmetric) {
      const inv = INVERSE[opts.type];
      if (inv) {
        this.upsert(
          opts.target,
          opts.source,
          inv,
          opts.evidence,
          opts.sourceIds,
          opts.confidence,
          opts.explanationAr,
          opts.explanationEn,
          opts.warnings ?? []
        );
      }
    }
  }

  private upsert(
    source: string,
    target: string,
    type: EntityRelationType,
    evidence: QuranReference,
    sourceIds: string[],
    confidence: number,
    explanationAr: string | undefined,
    explanationEn: string | undefined,
    warnings: string[]
  ): void {
    if (source === target) return;
    const key = relationKey(source, target, type);
    const existing = this.map.get(key);
    if (existing) {
      const evKeys = new Set(existing.evidenceReferences.map(refKey));
      if (!evKeys.has(refKey(evidence))) existing.evidenceReferences.push(evidence);
      for (const sid of sourceIds) {
        if (!existing.sourceIds.includes(sid)) existing.sourceIds.push(sid);
      }
      existing.confidence = Math.max(existing.confidence, confidence);
      for (const w of warnings) if (!existing.warnings.includes(w)) existing.warnings.push(w);
      return;
    }
    this.map.set(key, {
      sourceEntityId: source,
      targetEntityId: target,
      relationType: type,
      evidenceReferences: [evidence],
      sourceIds: [...sourceIds],
      confidence,
      explanationArabic: explanationAr ?? GENERIC_EXPLANATION_AR,
      explanationEnglish: explanationEn ?? GENERIC_EXPLANATION_EN,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [...warnings],
    });
  }

  toList(): EntityRelation[] {
    return Array.from(this.map.values()).sort((a, b) => {
      if (a.sourceEntityId !== b.sourceEntityId) return a.sourceEntityId.localeCompare(b.sourceEntityId);
      if (a.targetEntityId !== b.targetEntityId) return a.targetEntityId.localeCompare(b.targetEntityId);
      return a.relationType.localeCompare(b.relationType);
    });
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  if (!existsSync(MENTIONS_PATH)) {
    throw new Error(
      `Mentions file not found: ${MENTIONS_PATH}. Run scan-quran-entity-mentions.ts first.`
    );
  }
  const mentions = JSON.parse(readFileSync(MENTIONS_PATH, 'utf-8')) as EntityMentionScanOutput;
  const generatedAt = new Date().toISOString();
  const builder = new RelationBuilder();

  // Index mentions: per-(surah,ayah) entity sets, and per-surah entity sets.
  const ayahKey = (s: number, a: number) => `${s}:${a}`;
  const entitiesByAyah = new Map<string, Set<string>>();
  const entitiesBySurah = new Map<number, Set<string>>();
  const surahsByEntity = new Map<string, Set<number>>();
  // mention list per entity to allow neighbour scans
  const mentionsByEntity = new Map<string, EntityMention[]>();

  for (const e of mentions.entities) {
    mentionsByEntity.set(e.entityId, e.mentions);
    for (const m of e.mentions) {
      const ak = ayahKey(m.surahNumber, m.ayahNumber);
      let setA = entitiesByAyah.get(ak);
      if (!setA) {
        setA = new Set();
        entitiesByAyah.set(ak, setA);
      }
      setA.add(e.entityId);
      let setS = entitiesBySurah.get(m.surahNumber);
      if (!setS) {
        setS = new Set();
        entitiesBySurah.set(m.surahNumber, setS);
      }
      setS.add(e.entityId);
      let surahsE = surahsByEntity.get(e.entityId);
      if (!surahsE) {
        surahsE = new Set();
        surahsByEntity.set(e.entityId, surahsE);
      }
      surahsE.add(m.surahNumber);
    }
  }

  // ---------- Rule 1: same-ayah co-mention (mentioned_with, symmetric) ----------
  for (const [ak, ids] of entitiesByAyah.entries()) {
    if (ids.size < 2) continue;
    const [sStr, aStr] = ak.split(':');
    const surahNumber = Number(sStr);
    const ayahNumber = Number(aStr);
    const ref: QuranReference = { surahNumber, ayahStart: ayahNumber };
    const arr = Array.from(ids).sort();
    for (let i = 0; i < arr.length; i++) {
      for (let j = i + 1; j < arr.length; j++) {
        builder.add({
          source: arr[i],
          target: arr[j],
          type: 'mentioned_with',
          evidence: ref,
          sourceIds: ['quran_uthmani_cloud'],
          confidence: 0.7,
          symmetric: true,
        });
      }
    }
  }

  // ---------- Rule 2: hard family/title patterns from seed knownRelatives ----------
  // These edges piggyback on co-mention evidence to satisfy the
  // "every relation needs evidenceReferences" rule.
  for (const seed of QURAN_ENTITY_SEEDS) {
    if (!seed.knownRelatives) continue;
    for (const rel of seed.knownRelatives) {
      // Find at least one ayah where both seed.entityId and rel.entityId appear.
      const sourceMentions = mentionsByEntity.get(seed.entityId) ?? [];
      let evidence: QuranReference | null = null;
      for (const m of sourceMentions) {
        const ak = ayahKey(m.surahNumber, m.ayahNumber);
        const ids = entitiesByAyah.get(ak);
        if (ids?.has(rel.entityId)) {
          evidence = { surahNumber: m.surahNumber, ayahStart: m.ayahNumber };
          break;
        }
      }
      // Otherwise pick the first surah where both appear (passage-level evidence).
      if (!evidence) {
        const sourceSurahs = surahsByEntity.get(seed.entityId);
        const targetSurahs = surahsByEntity.get(rel.entityId);
        if (sourceSurahs && targetSurahs) {
          for (const s of sourceSurahs) {
            if (targetSurahs.has(s)) {
              const m = sourceMentions.find((mm) => mm.surahNumber === s);
              if (m) {
                evidence = { surahNumber: s, ayahStart: m.ayahNumber };
                break;
              }
            }
          }
        }
      }
      if (!evidence) continue;
      builder.add({
        source: seed.entityId,
        target: rel.entityId,
        type: rel.relationType,
        evidence,
        sourceIds: ['quran_uthmani_cloud'],
        confidence: 0.85,
        warnings: ['Family/title relation derived from seed dictionary; needs reviewer sign-off.'],
        symmetric: true,
      });
    }
  }

  // ---------- Rule 3: same-passage neighbours (window = 3 ayahs) ----------
  for (const [surahNumber, ids] of entitiesBySurah.entries()) {
    if (ids.size < 2) continue;
    // Gather (entityId, ayah) pairs in surah-order.
    const list: Array<{ entityId: string; ayah: number }> = [];
    for (const eid of ids) {
      const ms = mentionsByEntity.get(eid) ?? [];
      for (const m of ms) {
        if (m.surahNumber === surahNumber) list.push({ entityId: eid, ayah: m.ayahNumber });
      }
    }
    list.sort((a, b) => a.ayah - b.ayah);
    const WINDOW = 3;
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i];
        const b = list[j];
        if (b.ayah - a.ayah > WINDOW) break;
        if (a.entityId === b.entityId) continue;
        builder.add({
          source: a.entityId,
          target: b.entityId,
          type: 'same_surah_context',
          evidence: { surahNumber, ayahStart: a.ayah, ayahEnd: b.ayah },
          sourceIds: ['quran_uthmani_cloud'],
          confidence: 0.55,
          warnings: [
            'Inferred from co-mention within a 3-ayah window; verify with tafsir before promoting.',
          ],
          symmetric: true,
        });
      }
    }
  }

  // ---------- Rule 4: same-story from seed relatedStories ----------
  // Group entities by storyId.
  const entitiesByStory = new Map<string, string[]>();
  for (const seed of QURAN_ENTITY_SEEDS) {
    if (!seed.relatedStories) continue;
    for (const sid of seed.relatedStories) {
      let arr = entitiesByStory.get(sid);
      if (!arr) {
        arr = [];
        entitiesByStory.set(sid, arr);
      }
      if (!arr.includes(seed.entityId)) arr.push(seed.entityId);
    }
  }
  for (const [, ids] of entitiesByStory.entries()) {
    if (ids.length < 2) continue;
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const a = ids[i];
        const b = ids[j];
        // Need at least one ayah-level evidence: pick first surah where both appear.
        const sourceMentions = mentionsByEntity.get(a) ?? [];
        let evidence: QuranReference | null = null;
        for (const m of sourceMentions) {
          const ak = ayahKey(m.surahNumber, m.ayahNumber);
          if (entitiesByAyah.get(ak)?.has(b)) {
            evidence = { surahNumber: m.surahNumber, ayahStart: m.ayahNumber };
            break;
          }
        }
        if (!evidence) {
          const aSurahs = surahsByEntity.get(a);
          const bSurahs = surahsByEntity.get(b);
          if (aSurahs && bSurahs) {
            for (const s of aSurahs) {
              if (bSurahs.has(s)) {
                const m = sourceMentions.find((mm) => mm.surahNumber === s);
                if (m) {
                  evidence = { surahNumber: s, ayahStart: m.ayahNumber };
                  break;
                }
              }
            }
          }
        }
        if (!evidence) continue;
        builder.add({
          source: a,
          target: b,
          type: 'same_story',
          evidence,
          sourceIds: ['stories_manifest'],
          confidence: 0.7,
          warnings: ['Inferred from shared seed storyId; story attribution requires reviewer sign-off.'],
          symmetric: true,
        });
      }
    }
  }

  // ---------- Rule 5: theological_discussion — Maryam ↔ Isa in specific ayahs ----------
  // Carefully scoped: only ayahs in 4:171, 5:17, 5:72-77, 5:116-117 (well-known
  // theological clarification passages). The relation is needs_review and the
  // explanation is generic.
  const THEOLOGICAL_PASSAGES: Array<{ s: number; a1: number; a2: number }> = [
    { s: 4, a1: 171, a2: 171 },
    { s: 5, a1: 17, a2: 17 },
    { s: 5, a1: 72, a2: 77 },
    { s: 5, a1: 116, a2: 117 },
  ];
  for (const p of THEOLOGICAL_PASSAGES) {
    // Confirm at least one ayah in range has BOTH Maryam and Isa mentions.
    let hit = false;
    for (let a = p.a1; a <= p.a2; a++) {
      const ids = entitiesByAyah.get(ayahKey(p.s, a));
      if (ids && ids.has('entity_person_maryam') && ids.has('entity_prophet_isa')) {
        hit = true;
        break;
      }
    }
    if (!hit) continue;
    const ref: QuranReference = { surahNumber: p.s, ayahStart: p.a1, ayahEnd: p.a2 };
    builder.add({
      source: 'entity_person_maryam',
      target: 'entity_prophet_isa',
      type: 'theological_discussion',
      evidence: ref,
      sourceIds: ['quran_uthmani_cloud'],
      confidence: 0.55,
      warnings: [
        'Marked as theological-clarification passage; interpretation must be deferred to verified tafsir.',
      ],
      symmetric: true,
    });
  }

  // ---------- Emit ----------
  const relations = builder.toList();
  const involved = new Set<string>();
  const byType: Partial<Record<EntityRelationType, number>> = {};
  for (const r of relations) {
    involved.add(r.sourceEntityId);
    involved.add(r.targetEntityId);
    byType[r.relationType] = (byType[r.relationType] ?? 0) + 1;
  }
  const output: EntityRelationOutput = {
    version: VERSION,
    generatedAt,
    totalRelations: relations.length,
    totalEntitiesInvolved: involved.size,
    relationsByType: byType,
    relations,
    warnings: [
      'All relations default to reviewStatus=needs_review. No relation is auto-verified.',
      'Same-ayah co-mention edges are observational, not interpretive.',
      'Family/title edges depend on the seed dictionary, which is reviewedDictionary=false until a specialist signs off.',
    ],
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(output, null, 2), 'utf-8');
  console.log(`Wrote ${OUT_JSON}`);

  // -------- summary md --------
  const lines: string[] = [];
  lines.push('# Quran Entity Relations — Build Summary');
  lines.push('');
  lines.push(`Generated at: ${generatedAt}`);
  lines.push(`Builder version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Total relations: **${relations.length}**`);
  lines.push(`- Entities involved: **${involved.size}**`);
  lines.push('');
  lines.push('## Relations by type');
  lines.push('');
  lines.push('| Type | Count |');
  lines.push('|---|---:|');
  for (const [t, c] of Object.entries(byType).sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))) {
    lines.push(`| ${t} | ${c} |`);
  }
  lines.push('');
  lines.push('## Maryam–Isa connections');
  lines.push('');
  const maryamIsaRels = relations.filter(
    (r) =>
      (r.sourceEntityId === 'entity_person_maryam' && r.targetEntityId === 'entity_prophet_isa') ||
      (r.sourceEntityId === 'entity_prophet_isa' && r.targetEntityId === 'entity_person_maryam')
  );
  if (maryamIsaRels.length === 0) lines.push('_No Maryam–Isa relations emitted._');
  else {
    lines.push('| Source | Target | Type | Conf | Evidence count | Review |');
    lines.push('|---|---|---|---:|---:|---|');
    for (const r of maryamIsaRels) {
      lines.push(
        `| ${r.sourceEntityId} | ${r.targetEntityId} | ${r.relationType} | ${r.confidence} | ${r.evidenceReferences.length} | ${r.reviewStatus} |`
      );
    }
  }
  lines.push('');
  lines.push('## Maryam–Zakariyya connections');
  lines.push('');
  const maryamZak = relations.filter(
    (r) =>
      (r.sourceEntityId === 'entity_person_maryam' && r.targetEntityId === 'entity_prophet_zakariyya') ||
      (r.sourceEntityId === 'entity_prophet_zakariyya' && r.targetEntityId === 'entity_person_maryam')
  );
  if (maryamZak.length === 0) lines.push('_No Maryam–Zakariyya relations emitted._');
  else {
    lines.push('| Source | Target | Type | Conf | Evidence count |');
    lines.push('|---|---|---|---:|---:|');
    for (const r of maryamZak) {
      lines.push(
        `| ${r.sourceEntityId} | ${r.targetEntityId} | ${r.relationType} | ${r.confidence} | ${r.evidenceReferences.length} |`
      );
    }
  }
  lines.push('');
  lines.push('## Warnings');
  lines.push('');
  for (const w of output.warnings) lines.push(`- ${w}`);
  lines.push('');
  lines.push('All edges are `needs_review` and `humanReviewRequired: true`.');

  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);

  console.log(`\nDone. Relations: ${relations.length}, entities involved: ${involved.size}`);
}

main();
