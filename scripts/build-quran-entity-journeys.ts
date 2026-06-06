#!/usr/bin/env npx tsx
/**
 * Quran Entity Journey Builder — Entity-Centered GraphRAG.
 *
 * Builds four reading orders per entity:
 *   1. mushaf_order      — all mentions sorted by surah/ayah (certainty: high)
 *   2. story_world       — broad narrative bands from chronology seeds
 *                          (always needs_review)
 *   3. revelation_order  — only when a revelation-order seed exists for the
 *                          surah; otherwise marked disputed/needs_review
 *   4. thematic_order    — keyword-based grouping into stages such as
 *                          birth / glad-tidings / theological-clarification.
 *
 * Reads:
 *   - frontend/src/data/generated/quranEntityMentions.json
 *   - frontend/src/data/quranStoryChronologySeeds.ts (existing revelation seeds)
 *
 * Writes:
 *   - frontend/src/data/generated/quranEntityJourneys.json
 *   - docs/generated/quran-entity-journeys-summary.md
 *
 * Rules:
 *   - Story-world ordering is "guided reading", NEVER claimed as certain.
 *   - Revelation order journeys must show certainty=disputed/medium until
 *     reviewers confirm a citation.
 *   - Thematic stages are heuristic groupings — needs_review.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';
import {
  REVELATION_ORDER_SEEDS,
} from '../frontend/src/data/quranStoryChronologySeeds';
import type {
  ChronologyStageType,
  EntityJourney,
  EntityJourneyOutput,
  EntityJourneySection,
  EntityMentionScanOutput,
  EntityReviewStatus,
  QuranReference,
} from '../frontend/src/types/quranEntityGraph';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const MENTIONS_PATH = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranEntityJourneys.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-entity-journeys-summary.md');
const VERSION = '1.0.0';

// ---------------------------------------------------------------------------
// Maryam-specific thematic bucket assignment.
// Each bucket lists the (surah, ayahStart, ayahEnd) ranges that the bucket
// covers. The script keeps only mentions that fall inside the range, so it
// never invents thematic claims about ayahs that aren't mentioned.
// ---------------------------------------------------------------------------

interface ThematicRange {
  bucketKey: string;
  labelAr: string;
  labelEn: string;
  range: { s: number; a1: number; a2: number };
}

// Buckets are intentionally narrow and pinned to navigation categories only.
// They DO NOT pretend to be tafsir; the UI labels them as "reading sections".
const MARYAM_THEMATIC_BUCKETS: ThematicRange[] = [
  // 1. Birth, upbringing, guardianship (Aal Imran 33-44)
  {
    bucketKey: 'maryam_birth_guardianship',
    labelAr: 'مولد مريم ونشأتها وكفالة زكريا',
    labelEn: 'Birth, upbringing, and guardianship by Zakariyya',
    range: { s: 3, a1: 33, a2: 44 },
  },
  // 2. Glad tidings (Aal Imran 45-48)
  {
    bucketKey: 'maryam_glad_tidings_aal_imran',
    labelAr: 'البشارة بعيسى في آل عمران',
    labelEn: "Glad tidings of Isa's birth — Aal Imran",
    range: { s: 3, a1: 45, a2: 48 },
  },
  // 3. Glad tidings + birth (Surah Maryam 1-40)
  {
    bucketKey: 'maryam_birth_isa_surah_maryam',
    labelAr: 'سورة مريم — البشارة وولادة عيسى',
    labelEn: 'Surah Maryam — annunciation and birth of Isa',
    range: { s: 19, a1: 1, a2: 40 },
  },
  // 4. Isa speaking from the cradle, mission — Aal Imran 49-55, Maidah 110
  {
    bucketKey: 'maryam_isa_mission',
    labelAr: 'بعثة عيسى ومعجزاته',
    labelEn: "Isa's mission and miracles",
    range: { s: 3, a1: 49, a2: 55 },
  },
  // 5. Theological clarification — An-Nisa 171-172, Al-Maidah 17/72-77/116-117
  {
    bucketKey: 'maryam_theological_clarification_nisa',
    labelAr: 'البيان العقدي في النساء',
    labelEn: 'Theological clarification — An-Nisa',
    range: { s: 4, a1: 171, a2: 172 },
  },
  {
    bucketKey: 'maryam_theological_clarification_maidah_17',
    labelAr: 'الرد على ادعاء الألوهية — المائدة 17',
    labelEn: 'Refutation of divinity claim — Al-Maidah 17',
    range: { s: 5, a1: 17, a2: 17 },
  },
  {
    bucketKey: 'maryam_theological_clarification_maidah_72',
    labelAr: 'الرد على ادعاء الألوهية — المائدة 72-77',
    labelEn: 'Refutation of divinity claim — Al-Maidah 72-77',
    range: { s: 5, a1: 72, a2: 77 },
  },
  {
    bucketKey: 'maryam_table_spread',
    labelAr: 'حواري عيسى ومائدة السماء',
    labelEn: 'Disciples and table spread',
    range: { s: 5, a1: 111, a2: 115 },
  },
  {
    bucketKey: 'maryam_theological_clarification_maidah_116',
    labelAr: 'حوار يوم القيامة — المائدة 116-117',
    labelEn: 'Dialogue on the Day of Judgement — Al-Maidah 116-117',
    range: { s: 5, a1: 116, a2: 117 },
  },
  // 6. Covenant context — Al-Ahzab 7
  {
    bucketKey: 'maryam_covenant_ahzab',
    labelAr: 'الميثاق المأخوذ على الأنبياء — الأحزاب 7',
    labelEn: 'Covenant of the prophets — Al-Ahzab 7',
    range: { s: 33, a1: 7, a2: 7 },
  },
  // 7. Cross-prophet references — As-Saff 6/14, Al-Hadid 27, At-Tahrim 12
  {
    bucketKey: 'maryam_followers_hadid',
    labelAr: 'أتباع عيسى — الحديد 27',
    labelEn: 'Followers of Isa — Al-Hadid 27',
    range: { s: 57, a1: 27, a2: 27 },
  },
  {
    bucketKey: 'maryam_saff_isa',
    labelAr: 'دعوة عيسى للحواريين وبشارته بمحمد ﷺ — الصف',
    labelEn: "Isa's call and prophecy of Muhammad ﷺ — As-Saff",
    range: { s: 61, a1: 6, a2: 14 },
  },
  {
    bucketKey: 'maryam_tahrim',
    labelAr: 'مثل مريم في التحريم',
    labelEn: 'Maryam as example — At-Tahrim 12',
    range: { s: 66, a1: 12, a2: 12 },
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function joinAyahReferences(mentions: Array<{ surahNumber: number; ayahNumber: number }>): QuranReference[] {
  return mentions.map((m) => ({ surahNumber: m.surahNumber, ayahStart: m.ayahNumber }));
}

function worstStatus(a: EntityReviewStatus, b: EntityReviewStatus): EntityReviewStatus {
  // ranking: verified < needs_review < rejected — but we never auto-emit
  // verified, so the worst is always needs_review or rejected.
  if (a === 'rejected' || b === 'rejected') return 'rejected';
  if (a === 'needs_review' || b === 'needs_review') return 'needs_review';
  return 'verified';
}

// ---------------------------------------------------------------------------
// Mushaf-order journey: section per surah.
// ---------------------------------------------------------------------------

function buildMushafJourney(
  entityId: string,
  ms: Array<{ surahNumber: number; ayahNumber: number }>
): EntityJourney {
  const bySurah = new Map<number, Array<{ surahNumber: number; ayahNumber: number }>>();
  for (const m of ms) {
    if (!bySurah.has(m.surahNumber)) bySurah.set(m.surahNumber, []);
    bySurah.get(m.surahNumber)!.push(m);
  }
  const sections: EntityJourneySection[] = Array.from(bySurah.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([s, list]) => ({
      sectionId: `mushaf:${entityId}:s${s}`,
      labelArabic: `سورة رقم ${s}`,
      labelEnglish: `Surah ${s}`,
      ayahReferences: joinAyahReferences(list),
      reviewStatus: 'needs_review',
      warnings: [],
    }));
  return {
    entityId,
    stageType: 'mushaf_order',
    certainty: 'high',
    sections,
    reviewStatus: 'needs_review',
    sourceIds: ['quran_uthmani_cloud'],
    warnings: [],
  };
}

// ---------------------------------------------------------------------------
// Story-world journey: produce a single guided-reading section ordered by
// mushaf surah/ayah, BUT clearly labelled as "guided reading order", not as
// certain chronological order.
// ---------------------------------------------------------------------------

function buildStoryWorldJourney(
  entityId: string,
  ms: Array<{ surahNumber: number; ayahNumber: number }>
): EntityJourney {
  const sections: EntityJourneySection[] = [
    {
      sectionId: `story_world:${entityId}:guided`,
      labelArabic: 'ترتيب قراءة مقترح — ليس ترتيبًا تاريخيًا مؤكدًا',
      labelEnglish: 'Suggested reading order — not a confirmed historical chronology',
      ayahReferences: joinAyahReferences(
        [...ms].sort((a, b) =>
          a.surahNumber !== b.surahNumber ? a.surahNumber - b.surahNumber : a.ayahNumber - b.ayahNumber
        )
      ),
      reviewStatus: 'needs_review',
      warnings: [
        'Story-world order is a navigation aid, not a chronology claim. Verified chronology requires scholarly source.',
      ],
    },
  ];
  return {
    entityId,
    stageType: 'story_world',
    certainty: 'medium',
    sections,
    reviewStatus: 'needs_review',
    sourceIds: [],
    warnings: ['No verified story-world chronology source attached at the entity level.'],
  };
}

// ---------------------------------------------------------------------------
// Revelation-order journey: only emit if at least one of the entity's surahs
// has a revelation_order seed. Otherwise mark certainty=disputed and warn.
// ---------------------------------------------------------------------------

function buildRevelationJourney(
  entityId: string,
  ms: Array<{ surahNumber: number; ayahNumber: number }>
): EntityJourney {
  const seedBySurah = new Map<number, { orderIndex?: number; certainty: string; sourceIds: string[] }>();
  for (const seed of REVELATION_ORDER_SEEDS) {
    seedBySurah.set(Number(seed.itemId), {
      orderIndex: seed.orderIndex,
      certainty: seed.certainty,
      sourceIds: seed.sourceIds,
    });
  }
  const surahs = Array.from(new Set(ms.map((m) => m.surahNumber)));
  const known = surahs.filter((s) => seedBySurah.has(s));
  const unknown = surahs.filter((s) => !seedBySurah.has(s));
  const warnings: string[] = [];
  if (unknown.length > 0) {
    warnings.push(
      `${unknown.length} of ${surahs.length} surahs lack a verified revelation-order seed — order shown is approximate.`
    );
  }
  const sortedSurahs = [
    ...known.sort((a, b) => (seedBySurah.get(a)!.orderIndex ?? 999) - (seedBySurah.get(b)!.orderIndex ?? 999)),
    ...unknown.sort((a, b) => a - b),
  ];
  const sections: EntityJourneySection[] = sortedSurahs.map((s) => {
    const seed = seedBySurah.get(s);
    const ayahs = ms.filter((m) => m.surahNumber === s);
    const sectionWarnings: string[] = [];
    if (!seed) {
      sectionWarnings.push('No revelation-order source for this surah; placed by mushaf order as fallback.');
    } else if (seed.certainty === 'disputed' || seed.certainty === 'low') {
      sectionWarnings.push('Revelation order for this surah is disputed in scholarly tradition.');
    }
    return {
      sectionId: `revelation:${entityId}:s${s}`,
      labelArabic: seed ? `سورة رقم ${s} — ترتيب نزول مرجعي` : `سورة رقم ${s} — ترتيب نزول غير محقق`,
      labelEnglish: seed
        ? `Surah ${s} — referenced revelation order ${seed.orderIndex ?? '?'}`
        : `Surah ${s} — revelation order unreferenced`,
      ayahReferences: joinAyahReferences(ayahs),
      reviewStatus: 'needs_review',
      warnings: sectionWarnings,
    };
  });
  return {
    entityId,
    stageType: 'revelation_order',
    certainty: unknown.length > 0 ? 'disputed' : 'medium',
    sections,
    reviewStatus: 'needs_review',
    sourceIds: ['ibn_kathir'],
    warnings,
  };
}

// ---------------------------------------------------------------------------
// Thematic journey: use the Maryam-specific bucket map. For all other
// entities, fall back to a single "all-mentions" thematic section labelled
// "general reading" and marked needs_review.
// ---------------------------------------------------------------------------

function buildThematicJourney(
  entityId: string,
  ms: Array<{ surahNumber: number; ayahNumber: number }>
): EntityJourney {
  if (entityId === 'entity_person_maryam') {
    const sections: EntityJourneySection[] = [];
    for (const b of MARYAM_THEMATIC_BUCKETS) {
      const inRange = ms.filter(
        (m) => m.surahNumber === b.range.s && m.ayahNumber >= b.range.a1 && m.ayahNumber <= b.range.a2
      );
      if (inRange.length === 0) continue;
      sections.push({
        sectionId: `thematic:${entityId}:${b.bucketKey}`,
        labelArabic: b.labelAr,
        labelEnglish: b.labelEn,
        themeKey: b.bucketKey,
        ayahReferences: joinAyahReferences(inRange),
        reviewStatus: 'needs_review',
        warnings: [
          'Thematic bucket is a navigation aid; the interpretive label is not tafsir and needs scholarly review.',
        ],
      });
    }
    return {
      entityId,
      stageType: 'thematic_order',
      certainty: 'medium',
      sections,
      reviewStatus: 'needs_review',
      sourceIds: ['stories_manifest'],
      warnings: ['Thematic buckets are heuristic. No tafsir is invented.'],
    };
  }
  // Fallback: all mentions in one bucket.
  return {
    entityId,
    stageType: 'thematic_order',
    certainty: 'low',
    sections: [
      {
        sectionId: `thematic:${entityId}:all`,
        labelArabic: 'جميع ذكر الكيان',
        labelEnglish: 'All mentions',
        ayahReferences: joinAyahReferences(ms),
        reviewStatus: 'needs_review',
        warnings: ['No curated thematic buckets for this entity yet; needs review.'],
      },
    ],
    reviewStatus: 'needs_review',
    sourceIds: [],
    warnings: ['Thematic buckets only curated for Maryam in this release.'],
  };
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

  const journeys: EntityJourneyOutput['journeys'] = {};
  const byStage: Partial<Record<ChronologyStageType, number>> = {};
  let totalEntities = 0;
  const warnings: string[] = [];

  for (const e of mentions.entities) {
    if (e.mentions.length === 0) continue;
    totalEntities += 1;
    const ms = e.mentions.map((m) => ({ surahNumber: m.surahNumber, ayahNumber: m.ayahNumber }));
    const entryMap: Partial<Record<ChronologyStageType, EntityJourney>> = {};

    const mushaf = buildMushafJourney(e.entityId, ms);
    entryMap.mushaf_order = mushaf;
    byStage.mushaf_order = (byStage.mushaf_order ?? 0) + 1;

    const sw = buildStoryWorldJourney(e.entityId, ms);
    // worst-of: story_world is medium, sections needs_review
    sw.reviewStatus = worstStatus(sw.reviewStatus, 'needs_review');
    entryMap.story_world = sw;
    byStage.story_world = (byStage.story_world ?? 0) + 1;

    const rev = buildRevelationJourney(e.entityId, ms);
    entryMap.revelation_order = rev;
    byStage.revelation_order = (byStage.revelation_order ?? 0) + 1;

    const th = buildThematicJourney(e.entityId, ms);
    entryMap.thematic_order = th;
    byStage.thematic_order = (byStage.thematic_order ?? 0) + 1;

    journeys[e.entityId] = entryMap;
  }

  const output: EntityJourneyOutput = {
    version: VERSION,
    generatedAt,
    totalEntities,
    journeysByStageType: byStage,
    journeys,
    warnings: [
      'Story-world journeys are guided-reading aids, not certified chronology.',
      'Revelation-order journeys carry per-section warnings where the source is missing or disputed.',
      'Thematic buckets are heuristic and only curated for Maryam in this release.',
    ],
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(output, null, 2), 'utf-8');
  console.log(`Wrote ${OUT_JSON}`);

  // -------- summary md --------
  const lines: string[] = [];
  lines.push('# Quran Entity Journeys — Build Summary');
  lines.push('');
  lines.push(`Generated at: ${generatedAt}`);
  lines.push(`Builder version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Entities with journeys: **${totalEntities}**`);
  lines.push('');
  lines.push('| Stage | Entities |');
  lines.push('|---|---:|');
  for (const [stage, count] of Object.entries(byStage)) {
    lines.push(`| ${stage} | ${count} |`);
  }
  lines.push('');
  lines.push('## Maryam journeys');
  lines.push('');
  const maryam = journeys['entity_person_maryam'];
  if (!maryam) lines.push('_Maryam not in journey output._');
  else {
    for (const stage of ['mushaf_order', 'story_world', 'revelation_order', 'thematic_order'] as ChronologyStageType[]) {
      const j = maryam[stage];
      if (!j) continue;
      lines.push(`### ${stage}`);
      lines.push(`- certainty: ${j.certainty}`);
      lines.push(`- sections: ${j.sections.length}`);
      lines.push(`- reviewStatus: ${j.reviewStatus}`);
      if (j.warnings.length > 0) {
        lines.push('- warnings:');
        for (const w of j.warnings) lines.push(`  - ${w}`);
      }
      if (j.sections.length > 0) {
        lines.push('');
        lines.push('| Section | Ayahs |');
        lines.push('|---|---:|');
        for (const s of j.sections) {
          lines.push(`| ${s.labelEnglish} | ${s.ayahReferences.length} |`);
        }
      }
      lines.push('');
    }
  }
  lines.push('## Warnings');
  lines.push('');
  for (const w of output.warnings) lines.push(`- ${w}`);

  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);

  console.log(`\nDone. Entities with journeys: ${totalEntities}`);
}

main();
