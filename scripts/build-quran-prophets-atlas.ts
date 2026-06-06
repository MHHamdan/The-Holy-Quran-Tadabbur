#!/usr/bin/env npx tsx
/**
 * Phase X — Build the Quran Prophets Atlas.
 *
 * Reads:
 *   - frontend/src/data/quranProphetSeeds.ts            (canonical 25 prophets)
 *   - frontend/src/data/quranProphetRelatedFigures.ts   (non-prophet figures)
 *   - frontend/src/data/generated/quranEntityMentions.json
 *   - frontend/src/data/generated/quranEntityRelations.json
 *   - frontend/src/data/generated/quranEntityRelationsEnriched.json
 *   - frontend/src/data/generated/quranEntityJourneys.json
 *   - frontend/src/data/generated/quranCoreferenceMentions.json
 *   - frontend/src/data/generated/quranTopicAtlas.json
 *   - frontend/src/data/quranStories.ts (via stories.json manifest if available)
 *
 * Writes:
 *   - frontend/src/data/generated/quranProphetsAtlas.json
 *   - docs/generated/quran-prophets-atlas-summary.md
 *
 * Safety rules:
 *   - Never embed Quran text. Only surah/ayah references.
 *   - Never auto-promote storytelling to verified.
 *   - All journey stages must have ≥ 1 ayahReference.
 *   - The atlas MUST have exactly 25 prophets.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';

import {
  QURAN_PROPHET_SEEDS,
  QURAN_PROPHET_COUNT_CANONICAL,
  QURAN_PROPHET_ENTITY_IDS,
} from '../frontend/src/data/quranProphetSeeds';
import { QURAN_PROPHET_RELATED_FIGURES } from '../frontend/src/data/quranProphetRelatedFigures';

import type {
  ProphetAyahLink,
  ProphetAyahLinkType,
  ProphetJourney,
  ProphetJourneyStage,
  ProphetJourneyType,
  ProphetJourneyCertainty,
  ProphetRelation,
  ProphetRelationType,
  QuranProphetProfile,
  QuranProphetsAtlas,
  ProphetAtlasSummary,
  QuranReference,
} from '../frontend/src/types/quranProphetAtlas';
import { PROPHET_LINK_CONFIDENCE } from '../frontend/src/types/quranProphetAtlas';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');
const GEN = join(ROOT, 'frontend/src/data/generated');
const MENTIONS_PATH = join(GEN, 'quranEntityMentions.json');
const RELATIONS_PATH = join(GEN, 'quranEntityRelations.json');
const RELATIONS_ENRICHED_PATH = join(GEN, 'quranEntityRelationsEnriched.json');
const JOURNEYS_PATH = join(GEN, 'quranEntityJourneys.json');
const COREF_PATH = join(GEN, 'quranCoreferenceMentions.json');
const TOPIC_ATLAS_PATH = join(GEN, 'quranTopicAtlas.json');
const STORIES_MANIFEST_PATH = join(ROOT, 'data/manifests/stories.json');

const OUT_JSON = join(GEN, 'quranProphetsAtlas.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-prophets-atlas-summary.md');

const VERSION = '1.0.0';

// ---------------------------------------------------------------------------
// Loaders
// ---------------------------------------------------------------------------

function loadJSON<T = unknown>(p: string, optional = false): T | null {
  if (!existsSync(p)) {
    if (optional) return null;
    throw new Error(`Required input not found: ${p}`);
  }
  return JSON.parse(readFileSync(p, 'utf-8')) as T;
}

interface EntityMentionsFile {
  entities: Array<{
    entityId: string;
    entityType: string;
    labelArabic: string;
    labelEnglish: string;
    mentions: Array<{
      surahNumber: number;
      ayahNumber: number;
      mentionType: string;
      confidence: number;
      sourceIds: string[];
      reviewStatus: string;
      humanReviewRequired: boolean;
    }>;
  }>;
}

interface EntityRelation {
  sourceEntityId: string;
  targetEntityId: string;
  relationType: string;
  evidenceReferences: QuranReference[];
  confidence: number;
  sourceIds: string[];
  explanationArabic?: string;
  explanationEnglish?: string;
  reviewStatus: string;
  humanReviewRequired: boolean;
  warnings: string[];
}

interface EntityRelationsFile {
  relations: EntityRelation[];
}

interface EntityJourneysFile {
  journeys: Record<string, Record<string, {
    entityId: string;
    stageType: string;
    certainty: string;
    sections: Array<{
      sectionId: string;
      labelArabic: string;
      labelEnglish: string;
      ayahReferences: QuranReference[];
      reviewStatus: string;
      sourceIds?: string[];
      warnings: string[];
    }>;
    reviewStatus: string;
    sourceIds: string[];
    warnings: string[];
  }>>;
}

interface CoreferenceFile {
  mentions: Array<{
    mentionId: string;
    surahNumber: number;
    ayahNumber: number;
    candidateEntityIds: string[];
    selectedEntityId?: string;
    confidence: number;
    resolutionMethod: string;
    evidenceReferences: QuranReference[];
    reviewStatus: string;
    humanReviewRequired: boolean;
    warnings: string[];
  }>;
}

interface TopicAtlasFile {
  topics: Array<{
    topicId: string;
    labelEnglish: string;
    ayahLinks: Array<{
      surahNumber: number;
      ayahNumber: number;
      linkType: string;
    }>;
  }>;
}

interface StoriesManifest {
  stories?: Array<{
    id: string;
    name_en?: string;
    name_ar?: string;
    main_characters?: string[];
    prophets_mentioned?: string[];
    related_people?: string[];
    related_places?: string[];
    segments?: Array<{
      id: string;
      sura_no?: number;
      aya_start?: number;
      aya_end?: number;
    }>;
  }>;
}

const mentionsFile = loadJSON<EntityMentionsFile>(MENTIONS_PATH)!;
const relationsFile = loadJSON<EntityRelationsFile>(RELATIONS_PATH)!;
const enrichedRelations = loadJSON<EntityRelationsFile>(RELATIONS_ENRICHED_PATH, true);
const journeysFile = loadJSON<EntityJourneysFile>(JOURNEYS_PATH)!;
const corefFile = loadJSON<CoreferenceFile>(COREF_PATH, true);
const topicFile = loadJSON<TopicAtlasFile>(TOPIC_ATLAS_PATH, true);
const storiesManifest = loadJSON<StoriesManifest>(STORIES_MANIFEST_PATH, true);

// ---------------------------------------------------------------------------
// Index builders
// ---------------------------------------------------------------------------

const entityIndex = new Map<string, EntityMentionsFile['entities'][number]>();
for (const e of mentionsFile.entities) entityIndex.set(e.entityId, e);

const allRelations: EntityRelation[] = [
  ...(enrichedRelations?.relations ?? []),
  ...relationsFile.relations,
];

const storyById = new Map<string, NonNullable<StoriesManifest['stories']>[number]>();
for (const s of storiesManifest?.stories ?? []) storyById.set(s.id, s);

// Topic-by-ayah index: surah:ayah -> topicId[]
const topicByAyah = new Map<string, Set<string>>();
if (topicFile) {
  for (const topic of topicFile.topics) {
    for (const lnk of topic.ayahLinks ?? []) {
      const k = `${lnk.surahNumber}:${lnk.ayahNumber}`;
      if (!topicByAyah.has(k)) topicByAyah.set(k, new Set());
      topicByAyah.get(k)!.add(topic.topicId);
    }
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function entityType(eid: string): string {
  return entityIndex.get(eid)?.entityType ?? 'unknown';
}

function linkFromMention(
  m: { surahNumber: number; ayahNumber: number; mentionType: string; sourceIds: string[] },
  linkType: ProphetAyahLinkType,
): ProphetAyahLink {
  return {
    surahNumber: m.surahNumber,
    ayahNumber: m.ayahNumber,
    linkType,
    confidence: PROPHET_LINK_CONFIDENCE[linkType],
    sourceIds: m.sourceIds && m.sourceIds.length > 0 ? m.sourceIds : ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings: [],
  };
}

function dedupeLinks(links: ProphetAyahLink[]): ProphetAyahLink[] {
  const seen = new Map<string, ProphetAyahLink>();
  for (const l of links) {
    const k = `${l.surahNumber}:${l.ayahNumber}:${l.linkType}`;
    if (!seen.has(k)) seen.set(k, l);
  }
  return Array.from(seen.values()).sort(
    (a, b) => a.surahNumber - b.surahNumber || a.ayahNumber - b.ayahNumber,
  );
}

function uniq<T>(xs: T[]): T[] {
  return Array.from(new Set(xs));
}

// ---------------------------------------------------------------------------
// Build profile for one prophet
// ---------------------------------------------------------------------------

function buildProfile(seed: typeof QURAN_PROPHET_SEEDS[number]): QuranProphetProfile {
  const warnings: string[] = [];
  const ent = entityIndex.get(seed.entityId);

  // 1. Mentions ----------------------------------------------------------
  const explicit: ProphetAyahLink[] = [];
  const contextual: ProphetAyahLink[] = [];
  if (!ent) {
    warnings.push(
      `entity_not_indexed: ${seed.entityId} is not present in quranEntityMentions.json — re-run scan-quran-entity-mentions.`,
    );
  } else {
    for (const m of ent.mentions) {
      if (m.mentionType === 'explicit_name') {
        explicit.push(linkFromMention(m, 'explicit_name'));
      } else if (m.mentionType === 'alias' || m.mentionType === 'title') {
        explicit.push(linkFromMention(m, 'alias'));
      } else if (
        m.mentionType === 'story_context' ||
        m.mentionType === 'family_relation' ||
        m.mentionType === 'tafsir_context'
      ) {
        contextual.push(linkFromMention(m, 'story_context'));
      } else if (m.mentionType === 'pronoun_context') {
        contextual.push(linkFromMention(m, 'coreference'));
      } else {
        contextual.push(linkFromMention(m, 'related_entity'));
      }
    }
  }

  // 2. Coreference mentions ----------------------------------------------
  const corefLinks: ProphetAyahLink[] = [];
  for (const cm of corefFile?.mentions ?? []) {
    if (cm.selectedEntityId !== seed.entityId) continue;
    corefLinks.push({
      surahNumber: cm.surahNumber,
      ayahNumber: cm.ayahNumber,
      linkType: 'coreference',
      confidence: cm.confidence ?? PROPHET_LINK_CONFIDENCE.coreference,
      sourceIds: ['quran_uthmani_cloud'],
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: cm.warnings ?? [],
    });
  }

  // 3. Related entities --------------------------------------------------
  const relatedEntitiesSet = new Set<string>();
  const relatedPeople: string[] = [];
  const relatedPlaces: string[] = [];
  const relatedAnimals: string[] = [];
  const relatedObjects: string[] = [];
  const relatedEvents: string[] = [];

  const relevant = allRelations.filter(
    (r) => r.sourceEntityId === seed.entityId || r.targetEntityId === seed.entityId,
  );
  for (const r of relevant) {
    const other = r.sourceEntityId === seed.entityId ? r.targetEntityId : r.sourceEntityId;
    if (other === seed.entityId) continue;
    relatedEntitiesSet.add(other);
    const t = entityType(other);
    if (t === 'people_or_nation' || t === 'person' || t === 'woman') relatedPeople.push(other);
    else if (t === 'place') relatedPlaces.push(other);
    else if (t === 'animal') relatedAnimals.push(other);
    else if (t === 'object') relatedObjects.push(other);
    else if (t === 'event') relatedEvents.push(other);
  }

  // 4. Related topics ---------------------------------------------------
  const allAyahKeys = new Set<string>();
  for (const lnk of [...explicit, ...contextual, ...corefLinks]) {
    allAyahKeys.add(`${lnk.surahNumber}:${lnk.ayahNumber}`);
  }
  const topicCount = new Map<string, number>();
  for (const k of allAyahKeys) {
    const tids = topicByAyah.get(k);
    if (!tids) continue;
    for (const t of tids) topicCount.set(t, (topicCount.get(t) ?? 0) + 1);
  }
  const relatedTopics = Array.from(topicCount.entries())
    .filter(([, c]) => c >= 2) // require at least 2 ayah co-occurrences
    .sort((a, b) => b[1] - a[1])
    .map(([t]) => t)
    .slice(0, 30);

  // 5. Story IDs --------------------------------------------------------
  const storyIds = new Set<string>(seed.knownRelatedStoryIds);
  // Augment with stories that name this prophet in main_characters or prophets_mentioned
  for (const s of storiesManifest?.stories ?? []) {
    const idStem = seed.prophetId.replace(/^prophet_/, '');
    const inCharacters = (s.main_characters ?? []).some((c) =>
      c.toLowerCase().includes(idStem) || c.toLowerCase().includes(seed.transliteration.toLowerCase()),
    );
    const inProphets = (s.prophets_mentioned ?? []).some((p) => p.toLowerCase().includes(idStem));
    if (inCharacters || inProphets) storyIds.add(s.id);
  }

  // 6. Related prophets (relations) -------------------------------------
  const relatedProphets: ProphetRelation[] = [];
  for (const r of relevant) {
    const other = r.sourceEntityId === seed.entityId ? r.targetEntityId : r.sourceEntityId;
    if (!QURAN_PROPHET_ENTITY_IDS.has(other)) continue;
    const targetProphetId = other.replace(/^entity_prophet_/, 'prophet_');
    let relationType: ProphetRelationType = 'mentioned_together';
    if (
      r.relationType === 'father_of' ||
      r.relationType === 'mother_of' ||
      r.relationType === 'son_of' ||
      r.relationType === 'daughter_of' ||
      r.relationType === 'brother_of' ||
      r.relationType === 'sister_of' ||
      r.relationType === 'wife_of' ||
      r.relationType === 'husband_of' ||
      r.relationType === 'family_of' ||
      r.relationType === 'guardian_of'
    ) {
      relationType = 'family_relation';
    } else if (r.relationType === 'same_event' || r.relationType === 'same_story') {
      relationType = 'similar_trial';
    } else if (r.relationType === 'related_theme') {
      relationType = 'shared_theme';
    } else if (
      r.relationType === 'chronological_before' ||
      r.relationType === 'chronological_after'
    ) {
      relationType = 'chronological_sequence';
    } else if (r.relationType === 'same_surah_context') {
      relationType = 'mentioned_together';
    }
    relatedProphets.push({
      sourceProphetId: seed.prophetId,
      targetProphetId,
      relationType,
      evidenceReferences: r.evidenceReferences ?? [],
      explanationArabic: r.explanationArabic,
      explanationEnglish: r.explanationEnglish,
      confidence: r.confidence ?? 0.5,
      sourceIds: r.sourceIds ?? ['quran_uthmani_cloud'],
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: r.warnings ?? [],
    });
  }

  // 7. Journeys ---------------------------------------------------------
  const journeys: ProphetJourney[] = [];
  const entityJourneys = journeysFile.journeys[seed.entityId] ?? {};

  function buildJourney(
    journeyType: ProphetJourneyType,
    sourceStageKey: string,
    titleAr: string,
    titleEn: string,
    certainty: ProphetJourneyCertainty,
  ): ProphetJourney | null {
    const source = entityJourneys[sourceStageKey];
    if (!source) return null;
    const stages: ProphetJourneyStage[] = (source.sections ?? []).map((sec, idx) => ({
      stageId: `${journeyType}:${seed.prophetId}:${idx + 1}`,
      orderIndex: idx + 1,
      labelArabic: sec.labelArabic,
      labelEnglish: sec.labelEnglish,
      ayahReferences: sec.ayahReferences,
      relatedEntities: [],
      relatedTopics: [],
      sourceIds: sec.sourceIds ?? ['quran_uthmani_cloud'],
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: sec.warnings ?? [],
    }));
    return {
      journeyId: `${journeyType}:${seed.prophetId}`,
      prophetId: seed.prophetId,
      journeyType,
      titleArabic: titleAr,
      titleEnglish: titleEn,
      stages,
      certainty,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: source.warnings ?? [],
    };
  }

  const mushafJ = buildJourney(
    'mushaf_order',
    'mushaf_order',
    'الترتيب المصحفي',
    'Mushaf Order',
    'high',
  );
  const storyWorldJ = buildJourney(
    'story_world_order',
    'story_world',
    'الترتيب القصصي (قراءة إرشادية)',
    'Story-world Order (guided reading)',
    'low',
  );
  const revelationJ = buildJourney(
    'revelation_order',
    'revelation_order',
    'الترتيب النزولي',
    'Revelation Order',
    'medium',
  );
  const thematicJ = buildJourney(
    'thematic_order',
    'thematic_order',
    'الترتيب الموضوعي',
    'Thematic Order',
    'medium',
  );
  if (mushafJ) journeys.push(mushafJ);
  if (storyWorldJ) journeys.push(storyWorldJ);
  if (revelationJ) journeys.push(revelationJ);
  if (thematicJ) journeys.push(thematicJ);

  // Learning order — a small curated sequence: explicit-name ayahs only,
  // collapsed to the first per surah, ordered by surah number (deterministic,
  // safe, navigation-only).
  const learningStages: ProphetJourneyStage[] = [];
  const seenSurah = new Set<number>();
  const explicitSorted = explicit
    .slice()
    .sort((a, b) => a.surahNumber - b.surahNumber || a.ayahNumber - b.ayahNumber);
  for (const lnk of explicitSorted) {
    if (seenSurah.has(lnk.surahNumber)) continue;
    seenSurah.add(lnk.surahNumber);
    learningStages.push({
      stageId: `learning_order:${seed.prophetId}:${learningStages.length + 1}`,
      orderIndex: learningStages.length + 1,
      labelArabic: `سورة ${lnk.surahNumber}`,
      labelEnglish: `Surah ${lnk.surahNumber}`,
      ayahReferences: [{ surahNumber: lnk.surahNumber, ayahStart: lnk.ayahNumber }],
      relatedEntities: [],
      relatedTopics: Array.from(topicByAyah.get(`${lnk.surahNumber}:${lnk.ayahNumber}`) ?? []),
      sourceIds: ['quran_uthmani_cloud'],
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [],
    });
    if (learningStages.length >= 12) break;
  }
  if (learningStages.length > 0) {
    journeys.push({
      journeyId: `learning_order:${seed.prophetId}`,
      prophetId: seed.prophetId,
      journeyType: 'learning_order',
      titleArabic: 'ترتيب تعلّمي',
      titleEnglish: 'Learning Order',
      stages: learningStages,
      certainty: 'medium',
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [],
    });
  } else {
    warnings.push('learning_order_skipped: no explicit-name mentions to build a learning order.');
  }

  // 8. Warnings ---------------------------------------------------------
  if (storyIds.size === 0) warnings.push('missing_story_page: no curated story page references this prophet.');
  if (explicit.length === 0) warnings.push('no_explicit_mentions: no explicit-name mentions detected in scan output.');
  if (storyWorldJ) {
    storyWorldJ.warnings.push(
      'Story-world order is a guided reading sequence, not a definitive historical chronology.',
    );
  }
  if (seed.prophetId === 'prophet_muhammad') {
    warnings.push(
      'seerah_deferred: detailed biography of the Prophet Muhammad ﷺ is deferred to a separate module.',
    );
  }

  const profile: QuranProphetProfile = {
    prophetId: seed.prophetId,
    nameArabic: seed.nameArabic,
    nameEnglish: seed.nameEnglish,
    transliteration: seed.transliteration,
    aliasesArabic: seed.aliasesArabic,
    aliasesEnglish: seed.aliasesEnglish,
    quranMentionCount: explicit.length + contextual.length,
    surahCount: new Set([...explicit, ...contextual].map((l) => l.surahNumber)).size,
    explicitMentions: dedupeLinks(explicit),
    contextualMentions: dedupeLinks(contextual),
    coreferenceMentions: dedupeLinks(corefLinks),
    storyIds: Array.from(storyIds).sort(),
    relatedEntities: Array.from(relatedEntitiesSet).sort(),
    relatedPeopleOrNations: uniq(relatedPeople).sort(),
    relatedPlaces: uniq(relatedPlaces).sort(),
    relatedAnimals: uniq(relatedAnimals).sort(),
    relatedObjects: uniq(relatedObjects).sort(),
    relatedEvents: uniq(relatedEvents).sort(),
    relatedTopics,
    relatedProphets,
    journeys,
    sourceIds: ['quran_uthmani_cloud'],
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    warnings,
  };
  return profile;
}

// ---------------------------------------------------------------------------
// Build atlas
// ---------------------------------------------------------------------------

const profiles: QuranProphetProfile[] = QURAN_PROPHET_SEEDS.map(buildProfile);

if (profiles.length !== QURAN_PROPHET_COUNT_CANONICAL) {
  throw new Error(
    `Prophet count mismatch: expected ${QURAN_PROPHET_COUNT_CANONICAL}, got ${profiles.length}`,
  );
}

// Summary -------------------------------------------------------------------

const totalExplicit = profiles.reduce((acc, p) => acc + p.explicitMentions.length, 0);
const totalContextual = profiles.reduce((acc, p) => acc + p.contextualMentions.length, 0);
const totalCoreference = profiles.reduce((acc, p) => acc + p.coreferenceMentions.length, 0);
const totalRelations = profiles.reduce((acc, p) => acc + p.relatedProphets.length, 0);
const totalJourneys = profiles.reduce((acc, p) => acc + p.journeys.length, 0);
const totalAyahLinks =
  totalExplicit + totalContextual + totalCoreference;

const prophetsWithStory = profiles.filter((p) => p.storyIds.length > 0).length;
const prophetsMissingStoryPages = profiles
  .filter((p) => p.storyIds.length === 0)
  .map((p) => p.prophetId);
const prophetsWeakData = profiles
  .filter((p) => p.explicitMentions.length === 0 || p.relatedEntities.length === 0)
  .map((p) => p.prophetId);

const pairCount = new Map<string, number>();
for (const p of profiles) {
  for (const rel of p.relatedProphets) {
    const key = [rel.sourceProphetId, rel.targetProphetId].sort().join('::');
    pairCount.set(key, (pairCount.get(key) ?? 0) + 1);
  }
}
const topRelatedProphets = Array.from(pairCount.entries())
  .sort((a, b) => b[1] - a[1])
  .slice(0, 10)
  .map(([k, count]) => {
    const [a, b] = k.split('::');
    return { sourceProphetId: a, targetProphetId: b, count };
  });

const reviewWarnings: string[] = [];
for (const p of profiles) for (const w of p.warnings) reviewWarnings.push(`${p.prophetId}: ${w}`);

const summary: ProphetAtlasSummary = {
  totalProphets: profiles.length,
  totalExplicitMentions: totalExplicit,
  totalContextualMentions: totalContextual,
  totalCoreferenceMentions: totalCoreference,
  totalRelations,
  totalJourneys,
  totalAyahLinks,
  prophetsWithStoryPages: prophetsWithStory,
  prophetsMissingStoryPages,
  prophetsWeakData,
  topRelatedProphets,
  reviewWarnings,
};

const atlas: QuranProphetsAtlas = {
  version: VERSION,
  generatedAt: new Date().toISOString(),
  profiles,
  relatedFigures: QURAN_PROPHET_RELATED_FIGURES,
  summary,
  warnings: [
    'All storytelling and chronology entries are needs_review until reviewed by a scholar.',
    'Story-world order is a guided reading sequence, not a definitive historical chronology.',
  ],
};

// Write outputs -------------------------------------------------------------

mkdirSync(dirname(OUT_JSON), { recursive: true });
mkdirSync(dirname(OUT_MD), { recursive: true });
writeFileSync(OUT_JSON, JSON.stringify(atlas, null, 2), 'utf-8');

// Markdown summary ----------------------------------------------------------

function md(): string {
  const lines: string[] = [];
  lines.push('# Quran Prophets Atlas — Build Summary');
  lines.push('');
  lines.push(`- Version: ${atlas.version}`);
  lines.push(`- Generated: ${atlas.generatedAt}`);
  lines.push(`- Prophets represented: **${summary.totalProphets}** (canonical: ${QURAN_PROPHET_COUNT_CANONICAL})`);
  lines.push(`- Total explicit mentions: **${summary.totalExplicitMentions}**`);
  lines.push(`- Total contextual mentions: **${summary.totalContextualMentions}**`);
  lines.push(`- Total coreference mentions: **${summary.totalCoreferenceMentions}**`);
  lines.push(`- Total prophet-to-prophet relations: **${summary.totalRelations}**`);
  lines.push(`- Total journeys: **${summary.totalJourneys}**`);
  lines.push(`- Total ayah links: **${summary.totalAyahLinks}**`);
  lines.push('');
  lines.push('## Per-prophet snapshot');
  lines.push('');
  lines.push('| Prophet | Explicit | Contextual | Coref | Surahs | Topics | Stories | Relations |');
  lines.push('|---|---:|---:|---:|---:|---:|---:|---:|');
  for (const p of profiles) {
    lines.push(
      `| ${p.nameEnglish} | ${p.explicitMentions.length} | ${p.contextualMentions.length} | ${p.coreferenceMentions.length} | ${p.surahCount} | ${p.relatedTopics.length} | ${p.storyIds.length} | ${p.relatedProphets.length} |`,
    );
  }
  lines.push('');
  lines.push('## Prophets missing a curated story page');
  if (prophetsMissingStoryPages.length === 0) lines.push('_None._');
  else lines.push(prophetsMissingStoryPages.map((p) => `- ${p}`).join('\n'));
  lines.push('');
  lines.push('## Prophets with weak data (no explicit mentions or no related entities)');
  if (prophetsWeakData.length === 0) lines.push('_None._');
  else lines.push(prophetsWeakData.map((p) => `- ${p}`).join('\n'));
  lines.push('');
  lines.push('## Top related-prophet pairs');
  for (const t of topRelatedProphets) {
    lines.push(`- ${t.sourceProphetId} ↔ ${t.targetProphetId}: ${t.count}`);
  }
  lines.push('');
  lines.push(`## Review warnings (${reviewWarnings.length})`);
  for (const w of reviewWarnings.slice(0, 100)) lines.push(`- ${w}`);
  if (reviewWarnings.length > 100) lines.push(`… and ${reviewWarnings.length - 100} more.`);
  return lines.join('\n') + '\n';
}

writeFileSync(OUT_MD, md(), 'utf-8');

console.log(`[prophets-atlas] wrote ${OUT_JSON} (${profiles.length} profiles)`);
console.log(`[prophets-atlas] wrote ${OUT_MD}`);
