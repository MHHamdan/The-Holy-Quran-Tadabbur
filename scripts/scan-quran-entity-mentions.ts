#!/usr/bin/env npx tsx
/**
 * Whole-Quran Entity Mention Scanner — Entity-Centered GraphRAG.
 *
 * Reads:
 *   - data/raw/quran_uthmani.json (canonical Quran text; never written)
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

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const QURAN_PATH = join(ROOT, 'data/raw/quran_uthmani.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranEntityMentions.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-entity-mentions-summary.md');

const TOTAL_SURAHS = 114;
const TOTAL_AYAHS = 6236;
const VERSION = '1.0.0';

// ---------------------------------------------------------------------------
// Arabic normalisation: strip tashkeel, normalise alif/ya/hamza/ta-marbuta.
// ---------------------------------------------------------------------------

const ARABIC_DIACRITICS = /[ً-ٰٟؐ-ؚۖ-ۭـ]/g;

function normaliseArabic(s: string): string {
  return s
    .replace(ARABIC_DIACRITICS, '')
    .replace(/[آأإٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
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
  return JSON.parse(readFileSync(QURAN_PATH, 'utf-8')) as RawAyah[];
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
    for (const a of s.aliasesArabic) {
      const norm = normaliseArabic(a);
      if (!norm) continue;
      // Aliases shorter than 3 chars after normalisation are skipped (handled
      // again at detection time, but skipping here avoids them entirely).
      if (norm.length < 3) continue;
      entries.push({
        entityId: s.entityId,
        alias: a,
        normalised: norm,
        mentionType: classifyAlias(s, a),
        isGeneric: isGenericAlias(a),
      });
    }
  }
  // Longest-first so multi-word aliases win over their substrings.
  entries.sort((a, b) => b.normalised.length - a.normalised.length);
  return entries;
}

// ---------------------------------------------------------------------------
// Per-ayah detection with word-boundary check.
// ---------------------------------------------------------------------------

const ARABIC_LETTER = /[ء-ي]/;

interface AyahDetection {
  entityId: string;
  alias: string;
  mentionType: EntityMentionType;
  isGeneric: boolean;
}

function detectInAyah(normAyah: string, aliasTable: AliasEntry[]): AyahDetection[] {
  const out: AyahDetection[] = [];
  // Track each entityId once per ayah — choose the strongest mention type seen.
  const bestByEntity = new Map<string, AyahDetection>();
  for (const entry of aliasTable) {
    if (entry.normalised.length < 3) continue;

    let idx = normAyah.indexOf(entry.normalised);
    while (idx !== -1) {
      const after = idx + entry.normalised.length < normAyah.length
        ? normAyah[idx + entry.normalised.length]
        : ' ';
      if (!ARABIC_LETTER.test(after)) {
        const det: AyahDetection = {
          entityId: entry.entityId,
          alias: entry.alias,
          mentionType: entry.mentionType,
          isGeneric: entry.isGeneric,
        };
        const existing = bestByEntity.get(entry.entityId);
        if (!existing) {
          bestByEntity.set(entry.entityId, det);
        } else {
          // Prefer strongest mention type (explicit > alias > title > family > story > pronoun > tafsir)
          const rank: Record<EntityMentionType, number> = {
            explicit_name: 7,
            alias: 6,
            title: 5,
            family_relation: 4,
            story_context: 3,
            tafsir_context: 2,
            pronoun_context: 1,
          };
          if (rank[det.mentionType] > rank[existing.mentionType]) {
            bestByEntity.set(entry.entityId, det);
          }
        }
        break; // one occurrence per alias per ayah is enough
      }
      idx = normAyah.indexOf(entry.normalised, idx + 1);
    }
  }
  for (const det of bestByEntity.values()) out.push(det);
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
    const detections = detectInAyah(norm, aliasTable);
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
      const confidence = Math.max(0.05, Math.round((baseConf - downgrade) * 100) / 100);
      const mention: EntityMention = {
        surahNumber,
        ayahNumber,
        mentionType: d.mentionType,
        confidence,
        matchedText: d.alias,
        sourceIds: ['quran_uthmani_cloud'],
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
