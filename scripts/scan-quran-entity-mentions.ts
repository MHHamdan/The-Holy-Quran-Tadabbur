#!/usr/bin/env npx tsx
/**
 * Whole-Quran Entity Mention Scanner — Entity-Centered GraphRAG.
 *
 * Reads:
 *   - data/raw/quran_tanzil.json (canonical Quran text; never written)
 *   - frontend/src/data/quranEntitySeeds.ts (candidate dictionary)
 *
 * Writes:
 *   - frontend/src/data/generated/quranEntityMentions.json
 *   - docs/generated/quran-entity-mentions-summary.md
 *
 * Rules:
 *   - DOES NOT modify any Quran text.
 *   - DOES NOT generate tafsir, interpretation, or moral content.
 *   - DOES NOT emit ayah text into the output (only surah/ayah numbers).
 *   - Every mention defaults to reviewStatus = "needs_review" and
 *     humanReviewRequired = true.
 *   - Family/title/story_context/pronoun/tafsir contexts stay needs_review.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';
import {
  QURAN_ENTITY_SEEDS,
} from '../frontend/src/data/quranEntitySeeds';
import {
  MENTION_TYPE_CONFIDENCE,
  defaultMentionReviewStatus,
  defaultHumanReviewRequired,
  type EntityMention,
  type EntityMentionScanOutput,
  type EntityMentionType,
  type EntitySeed,
  type QuranEntityType,
} from '../frontend/src/types/quranEntityGraph';
import { STORY_ENTITY_ALIAS_SCOPES } from '../frontend/src/data/quranStoryEntitySeeds';
import {
  LEMMA_BY_ENTITY,
  QAC_PATH,
  countAliasOccurrences,
  inScope,
  loadQacProperNounIndex,
  type AyahScope,
  qacAyahsForEntity,
  tokenise,
} from './qac-proper-noun-lemmas';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const QURAN_PATH = join(ROOT, 'data/raw/quran_tanzil.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-entity-mentions-summary.md');

const TOTAL_SURAHS = 114;
const TOTAL_AYAHS = 6236;
const VERSION = '2.1.0'; // 2.1: alias ayah scopes + ta-marbuta-safe pronoun aliases

// ---------------------------------------------------------------------------
// Arabic normalisation: strip tashkeel, normalise alif/ya/hamza/ta-marbuta.
// ---------------------------------------------------------------------------

const ARABIC_DIACRITICS = /[ً-ٰٟؐ-ؚۖ-ۭـ]/g;

/**
 * `keepTaMarbuta` keeps ة distinct from ه. Pronoun-suffixed aliases need it:
 * "أمه" (his mother) must not match "أمة" (a nation), nor "زوجه" match "زوجة".
 */
function normaliseArabic(s: string, keepTaMarbuta = false): string {
  const base = s
    .replace(ARABIC_DIACRITICS, '')
    .replace(/[آأإٱ]/g, 'ا')
    .replace(/ى/g, 'ي');
  return (keepTaMarbuta ? base : base.replace(/ة/g, 'ه'))
    .replace(/ء/g, '')               // drop stand-alone hamza so إسرءيل ↔ إسرائيل
    .replace(/[​-‏﻿]/g, '')
    .trim();
}

// ---------------------------------------------------------------------------
// Quran loader
// ---------------------------------------------------------------------------

interface RawAyah {
  id?: number;
  sura_no: number;
  sura_name_ar?: string;
  sura_name_en?: string;
  aya_no: number;
  aya_text: string;
}

function loadQuran(): RawAyah[] {
  if (!existsSync(QURAN_PATH)) {
    throw new Error(`Quran file not found: ${QURAN_PATH}`);
  }
  return (JSON.parse(readFileSync(QURAN_PATH, 'utf-8')) as { verses: RawAyah[] }).verses;
}

// ---------------------------------------------------------------------------
// Alias table
// ---------------------------------------------------------------------------

interface AliasEntry {
  entityId: string;
  alias: string;
  normalised: string;
  mentionType: EntityMentionType;
  /** Generic / common-word alias → downgrade mention. */
  isGeneric: boolean;
  /** Ayah scope for ambiguous aliases (shared with the story-connections scan). */
  scope?: AyahScope;
  /** Match against the ayah normalised without ة→ه (pronoun-suffixed aliases). */
  keepTaMarbuta: boolean;
}

/**
 * Title/role-style aliases are tagged as `title`; descriptive contextual
 * aliases (مثل: أمه / يبشرك) are tagged as `family_relation` / `story_context`.
 * Single bare name aliases are tagged as `alias`. Aliases matching the exact
 * Arabic label after normalisation are tagged as `explicit_name`.
 */
function classifyAlias(seed: EntitySeed, alias: string): EntityMentionType {
  const labelNorm = normaliseArabic(seed.labelArabic.replace(/عليه السلام|عليها السلام|ﷺ/g, '').trim());
  const aliasNorm = normaliseArabic(alias);

  // explicit name = matches the label (or label without honorific)
  if (aliasNorm === labelNorm) return 'explicit_name';

  // family-relation descriptors: ابن X, ابنة X, أم X, أبو X, زوج X, آل X, امرأت X
  if (
    /^(ابن |ابنة |أم |أبو |أبي |زوج |زوجة |امرأت |امرأة )/.test(alias) ||
    /^آل /.test(alias)
  ) {
    return 'family_relation';
  }

  // pronoun-bearing descriptors that match any antecedent ("أمه" = "his mother",
  // "زوجه" = "his wife", "أبيه" = "his father", "عرشها" = "her throne")
  if (/^(أمه|زوجه|أبيه|أمها|كلبهم|عصاه|عصاك|عرشها)$/.test(alias)) {
    return 'pronoun_context';
  }

  // title-style aliases: العزيز, المسيح, ذو X, ذا X, روح القدس, ملك الموت
  if (
    /^(ذو |ذا |صاحب |أصحاب |أهل |قوم |بنو |بني )/.test(alias) ||
    alias === 'المسيح' ||
    alias === 'الفرقان' ||
    alias === 'الخليل' ||
    alias === 'كليم الله' ||
    alias === 'الروح الأمين' ||
    alias === 'روح القدس' ||
    alias === 'ملك الموت' ||
    alias === 'البلد الأمين'
  ) {
    return 'title';
  }

  // story-context descriptors like "يبشرك", "فأجاءها المخاض"
  if (/^(يبشرك|فأجاءها|فانفلق|أنزل علينا|حرقوه)/.test(alias)) {
    return 'story_context';
  }

  // default: plain alias surface form
  return 'alias';
}

function isGenericAlias(alias: string): boolean {
  const generic = new Set([
    'الذكر',
    'الكتاب',
    'الفرقان',
    'الروح',
    'الكهف',
    'البقرة',
    'الفيل',
    'النحل',
    'النمل',
    'العنكبوت',
    'البلد الأمين',
  ]);
  return generic.has(alias);
}

function buildAliasTable(seeds: EntitySeed[]): AliasEntry[] {
  const entries: AliasEntry[] = [];
  for (const s of seeds) {
    const hasLemma = !!LEMMA_BY_ENTITY[s.entityId];
    const scopes = STORY_ENTITY_ALIAS_SCOPES[s.entityId] ?? {};
    for (const a of s.aliasesArabic) {
      const mentionType = classifyAlias(s, a);
      const keepTaMarbuta = mentionType === 'pronoun_context';
      const norm = normaliseArabic(a, keepTaMarbuta);
      if (!norm) continue;
      // Aliases shorter than 3 chars after normalisation are skipped.
      if (norm.length < 3) continue;
      // Entities with a QAC proper-noun lemma get their name mentions from
      // QAC; their name-style aliases (explicit_name / alias) are dropped
      // because surface matching cannot tell "صالحا" (righteous) from the
      // prophet Salih, or "قرون" (generations) from Qarun. Pronoun aliases are
      // dropped for the same reason: "أمه" (his mother) cannot say whose
      // mother (4:11 is inheritance law, not Maryam); the named ayat already
      // come from QAC.
      if (
        hasLemma &&
        (mentionType === 'explicit_name' || mentionType === 'alias' || mentionType === 'pronoun_context')
      ) {
        continue;
      }
      entries.push({
        entityId: s.entityId,
        alias: a,
        normalised: norm,
        mentionType,
        isGeneric: isGenericAlias(a),
        scope: scopes[a] ?? scopes['*'],
        keepTaMarbuta,
      });
    }
  }
  // Longest-first so multi-word aliases win over their substrings.
  entries.sort((a, b) => b.normalised.length - a.normalised.length);
  return entries;
}

// ---------------------------------------------------------------------------
// Per-ayah detection: QAC proper-noun lemmas + whole-token alias matching.
// ---------------------------------------------------------------------------

interface AyahDetection {
  entityId: string;
  alias: string;
  mentionType: EntityMentionType;
  isGeneric: boolean;
  /** true when the detection comes from a QAC POS:PN lemma tag. */
  fromQac?: boolean;
}

const MENTION_RANK: Record<EntityMentionType, number> = {
  explicit_name: 7,
  alias: 6,
  title: 5,
  family_relation: 4,
  story_context: 3,
  tafsir_context: 2,
  pronoun_context: 1,
};

/** Confidence ceiling for anything that is not a QAC proper-noun hit. */
const ALIAS_ONLY_MAX_CONFIDENCE = 0.6;

function detectInAyah(
  normAyah: string,
  normAyahKeepTa: string,
  aliasTable: AliasEntry[],
  qacEntityIds: string[] = [],
  surah = 0,
  ayah = 0,
): AyahDetection[] {
  const bestByEntity = new Map<string, AyahDetection>();
  for (const entityId of qacEntityIds) {
    const seed = QURAN_ENTITY_SEEDS.find((s) => s.entityId === entityId);
    bestByEntity.set(entityId, {
      entityId,
      alias: seed?.aliasesArabic[0] ?? '',
      mentionType: 'explicit_name',
      isGeneric: false,
      fromQac: true,
    });
  }
  const tokens = tokenise(normAyah);
  const tokensKeepTa = tokenise(normAyahKeepTa);
  for (const entry of aliasTable) {
    if (surah > 0 && !inScope(entry.scope, surah, ayah)) continue;
    if (countAliasOccurrences(entry.keepTaMarbuta ? tokensKeepTa : tokens, entry.normalised) === 0) continue;
    const det: AyahDetection = {
      entityId: entry.entityId,
      alias: entry.alias,
      mentionType: entry.mentionType,
      isGeneric: entry.isGeneric,
    };
    const existing = bestByEntity.get(entry.entityId);
    if (!existing || (!existing.fromQac && MENTION_RANK[det.mentionType] > MENTION_RANK[existing.mentionType])) {
      bestByEntity.set(entry.entityId, det);
    }
  }
  return Array.from(bestByEntity.values());
}

/** "s:a" → entity ids whose QAC proper-noun lemma occurs in that ayah. */
function buildQacEntityIndex(seeds: EntitySeed[]): Map<string, string[]> {
  const idx = loadQacProperNounIndex();
  if (!idx) {
    throw new Error(
      `QAC morphology not found at ${QAC_PATH}. It is required to resolve proper nouns ` +
        '(see scripts/qac-proper-noun-lemmas.ts).',
    );
  }
  const out = new Map<string, string[]>();
  for (const seed of seeds) {
    const keys = qacAyahsForEntity(seed.entityId, idx);
    if (!keys) continue;
    for (const k of keys) {
      const arr = out.get(k) ?? [];
      arr.push(seed.entityId);
      out.set(k, arr);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  console.log('Scanning Quran for entity mentions...');
  const ayahs = loadQuran();
  if (ayahs.length !== TOTAL_AYAHS) {
    console.warn(`WARNING: expected ${TOTAL_AYAHS} ayahs, got ${ayahs.length}`);
  }

  const aliasTable = buildAliasTable(QURAN_ENTITY_SEEDS);
  const qacEntityIndex = buildQacEntityIndex(QURAN_ENTITY_SEEDS);
  const generatedAt = new Date().toISOString();

  // Per-entity result accumulator
  type Acc = {
    entityId: string;
    entityType: QuranEntityType;
    labelArabic: string;
    labelEnglish: string;
    mentions: EntityMention[];
  };
  const acc = new Map<string, Acc>();
  for (const s of QURAN_ENTITY_SEEDS) {
    acc.set(s.entityId, {
      entityId: s.entityId,
      entityType: s.entityType,
      labelArabic: s.labelArabic,
      labelEnglish: s.labelEnglish,
      mentions: [],
    });
  }

  const mentionsBySurah: Record<number, number> = {};
  const mentionsByEntityType: Partial<Record<QuranEntityType, number>> = {};
  let totalMentions = 0;
  const warnings: string[] = [];

  const ambiguousAliasesSet = new Map<string, { entityId: string; aliasArabic: string; reason: string }>();

  // First pass: collect candidate detections per ayah AND track surahs where
  // each entity has an explicit_name / alias match. Pronoun_context detections
  // are only kept if the surah also contains an explicit_name for that entity.
  type RawHit = {
    surahNumber: number;
    ayahNumber: number;
    detection: AyahDetection;
  };
  const rawHits: RawHit[] = [];
  const explicitSurahsByEntity = new Map<string, Set<number>>();
  for (const a of ayahs) {
    const norm = normaliseArabic(a.aya_text ?? '');
    if (!norm) continue;
    const detections = detectInAyah(
      norm,
      normaliseArabic(a.aya_text ?? '', true),
      aliasTable,
      qacEntityIndex.get(`${a.sura_no}:${a.aya_no}`) ?? [],
      a.sura_no,
      a.aya_no,
    );
    if (detections.length === 0) continue;
    for (const d of detections) {
      rawHits.push({ surahNumber: a.sura_no, ayahNumber: a.aya_no, detection: d });
      if (d.mentionType === 'explicit_name' || d.mentionType === 'alias') {
        let surahs = explicitSurahsByEntity.get(d.entityId);
        if (!surahs) {
          surahs = new Set();
          explicitSurahsByEntity.set(d.entityId, surahs);
        }
        surahs.add(a.sura_no);
      }
    }
  }

  for (const { surahNumber, ayahNumber, detection: d } of rawHits) {
    // Pronoun-context filter: require an explicit/alias mention in the same surah.
    if (d.mentionType === 'pronoun_context') {
      const surahs = explicitSurahsByEntity.get(d.entityId);
      if (!surahs || !surahs.has(surahNumber)) continue;
    }
    {
      const slot = acc.get(d.entityId);
      if (!slot) continue;
      const seed = QURAN_ENTITY_SEEDS.find((s) => s.entityId === d.entityId);
      const baseConf = MENTION_TYPE_CONFIDENCE[d.mentionType];
      const downgrade = d.isGeneric ? 0.2 : 0;
      const ceiling = d.fromQac ? 1 : ALIAS_ONLY_MAX_CONFIDENCE;
      const confidence = Math.max(0.05, Math.round((Math.min(baseConf, ceiling) - downgrade) * 100) / 100);
      const mention: EntityMention = {
        surahNumber,
        ayahNumber,
        mentionType: d.mentionType,
        confidence,
        matchedText: d.alias,
        sourceIds: d.fromQac ? ['tanzil_quran_uthmani', 'quranic_arabic_corpus'] : ['tanzil_quran_uthmani'],
        reviewStatus: defaultMentionReviewStatus(d.mentionType),
        humanReviewRequired: defaultHumanReviewRequired(d.mentionType),
      };
      slot.mentions.push(mention);
      totalMentions += 1;
      mentionsBySurah[surahNumber] = (mentionsBySurah[surahNumber] ?? 0) + 1;
      const t = slot.entityType;
      mentionsByEntityType[t] = (mentionsByEntityType[t] ?? 0) + 1;
      if (d.isGeneric && seed) {
        const key = `${d.entityId}::${d.alias}`;
        if (!ambiguousAliasesSet.has(key)) {
          ambiguousAliasesSet.set(key, {
            entityId: d.entityId,
            aliasArabic: d.alias,
            reason: 'Generic / common-word alias — confidence downgraded.',
          });
        }
      }
    }
  }

  const entities = Array.from(acc.values());
  // Sort mentions inside each entity by (surah, ayah)
  for (const e of entities) {
    e.mentions.sort((a, b) =>
      a.surahNumber !== b.surahNumber
        ? a.surahNumber - b.surahNumber
        : a.ayahNumber - b.ayahNumber
    );
  }

  const emptyEntityIds = entities.filter((e) => e.mentions.length === 0).map((e) => e.entityId);
  if (emptyEntityIds.length > 0) {
    warnings.push(
      `${emptyEntityIds.length} seeded entities had zero detections — review aliases or expected scope.`
    );
  }

  const output: EntityMentionScanOutput = {
    version: VERSION,
    generatedAt,
    scannedSurahs: TOTAL_SURAHS,
    totalEntities: entities.length,
    totalMentions,
    mentionsByEntityType,
    mentionsBySurah,
    entities,
    emptyEntityIds,
    ambiguousAliases: Array.from(ambiguousAliasesSet.values()),
    warnings,
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(output, null, 2), 'utf-8');
  console.log(`Wrote ${OUT_JSON}`);

  // ---------------- summary markdown ----------------
  mkdirSync(dirname(OUT_MD), { recursive: true });
  const maryam = entities.find((e) => e.entityId === 'entity_person_maryam');
  const lines: string[] = [];
  lines.push('# Quran Entity Mentions — Scan Summary');
  lines.push('');
  lines.push(`Generated at: ${generatedAt}`);
  lines.push(`Scanner version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Entities seeded: **${entities.length}**`);
  lines.push(`- Total mentions detected: **${totalMentions}**`);
  lines.push(`- Surahs scanned: **${TOTAL_SURAHS}** (of 114)`);
  lines.push(`- Entities with zero detections: **${emptyEntityIds.length}**`);
  lines.push('');
  lines.push('## Mentions by entity type');
  lines.push('');
  lines.push('| Type | Mentions |');
  lines.push('|---|---:|');
  for (const [type, count] of Object.entries(mentionsByEntityType)
    .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))) {
    lines.push(`| ${type} | ${count} |`);
  }
  lines.push('');
  lines.push('## Top 10 entities by mention count');
  lines.push('');
  const top = [...entities].sort((a, b) => b.mentions.length - a.mentions.length).slice(0, 10);
  lines.push('| Entity | Type | Mentions |');
  lines.push('|---|---|---:|');
  for (const e of top) {
    lines.push(`| ${e.labelEnglish} | ${e.entityType} | ${e.mentions.length} |`);
  }
  lines.push('');
  lines.push('## Maryam mention map');
  lines.push('');
  if (maryam) {
    lines.push(`- entityId: \`${maryam.entityId}\``);
    lines.push(`- Total mentions: **${maryam.mentions.length}**`);
    const surahs = new Set(maryam.mentions.map((m) => m.surahNumber));
    lines.push(`- Surahs containing Maryam mentions: **${surahs.size}** (${Array.from(surahs).sort((a, b) => a - b).join(', ')})`);
    const byType: Record<string, number> = {};
    for (const m of maryam.mentions) byType[m.mentionType] = (byType[m.mentionType] ?? 0) + 1;
    lines.push('');
    lines.push('Mention-type breakdown:');
    for (const [k, v] of Object.entries(byType)) lines.push(`- \`${k}\`: ${v}`);
    lines.push('');
    lines.push('First 25 mentions:');
    lines.push('| Surah | Ayah | Type | Conf | Matched |');
    lines.push('|---:|---:|---|---:|---|');
    for (const m of maryam.mentions.slice(0, 25)) {
      lines.push(`| ${m.surahNumber} | ${m.ayahNumber} | ${m.mentionType} | ${m.confidence} | ${m.matchedText ?? ''} |`);
    }
  } else {
    lines.push('_Maryam seed not found in dictionary._');
  }
  lines.push('');
  lines.push('## Entities with zero detections');
  lines.push('');
  if (emptyEntityIds.length === 0) lines.push('_All entities matched at least once._');
  else for (const id of emptyEntityIds) lines.push(`- \`${id}\``);
  lines.push('');
  lines.push('## Ambiguous aliases (downgraded)');
  lines.push('');
  if (ambiguousAliasesSet.size === 0) lines.push('_None._');
  else for (const a of ambiguousAliasesSet.values())
    lines.push(`- \`${a.entityId}\` — alias \`${a.aliasArabic}\` — ${a.reason}`);
  lines.push('');
  lines.push('## Warnings');
  lines.push('');
  if (warnings.length === 0) lines.push('_None._');
  else for (const w of warnings) lines.push(`- ${w}`);
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push('All mentions default to `needs_review` and `humanReviewRequired: true`. No tafsir or interpretation is generated. Quran text is not embedded in the output JSON.');
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);

  console.log('\nScan complete.');
  console.log(`  Entities: ${entities.length}, mentions: ${totalMentions}, empty: ${emptyEntityIds.length}`);
}

main();
