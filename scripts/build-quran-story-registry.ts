#!/usr/bin/env npx tsx
/**
 * Build the canonical Quran Story Registry.
 *
 * Merges:
 *   - data/manifests/stories.json                                 (authored 122-story manifest)
 *   - frontend/src/data/generated/quranProphetStoryPages.json     (prophet story pages)
 *   - frontend/src/data/generated/quranProphetsAtlas.json         (prophet metadata)
 *   - frontend/src/data/generated/quranEntityMentions.json        (entity index)
 *   - frontend/src/data/generated/quranEntityRelations.json       (entity relations)
 *   - frontend/src/data/generated/quranEntityRelationsEnriched.json (enriched relations, optional)
 *   - frontend/src/data/generated/quranTopicAtlas.json            (topic atlas)
 *   - frontend/src/data/generated/quranKnowledgeGraph.json        (KG)
 *
 * Output:
 *   - frontend/src/data/generated/quranStoryRegistry.json
 *   - docs/generated/quran-story-registry-summary.md
 *
 * Safety:
 *   - No Quran text embedded.
 *   - Every registry entry has ≥ 1 quranReferences entry, except entries
 *     explicitly flagged as missing_metadata.
 *   - Generated entries default to reviewStatus = "needs_review" and
 *     humanReviewRequired = true.
 *   - Categories are mapped through REGISTRY_CATEGORY_ALIASES so the UI
 *     enum matches the registry exactly.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';

import type {
  RegistryStoryEntry,
  RegistryStoryCategory,
  RegistryQuranReference,
  RegistryQuranReferenceLinkType,
  QuranStoryRegistryFile,
  RegistryCoverageSummary,
} from '../frontend/src/types/quranStoryRegistry';
import {
  REGISTRY_CATEGORY_ALIASES,
  REGISTRY_CATEGORY_ORDER,
} from '../frontend/src/types/quranStoryRegistry';

const ROOT = resolve(__dirname, '..');
const MANIFEST = join(ROOT, 'data/manifests/stories.json');
const GEN = join(ROOT, 'frontend/src/data/generated');
const PROPHET_PAGES = join(GEN, 'quranProphetStoryPages.json');
const PROPHETS_ATLAS = join(GEN, 'quranProphetsAtlas.json');
const ENTITY_MENTIONS = join(GEN, 'quranEntityMentions.json');
const ENTITY_RELATIONS = join(GEN, 'quranEntityRelations.json');
const TOPIC_ATLAS = join(GEN, 'quranTopicAtlas.json');
const KG = join(GEN, 'quranKnowledgeGraph.json');
// Cross-references file is optional — registry can be built without it.
// When present, neighboursByStory injects the strongest N peer storyIds.
const CROSS_REFS = join(GEN, 'quranStoryCrossReferences.json');

const OUT_JSON = join(GEN, 'quranStoryRegistry.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-story-registry-summary.md');
const VERSION = '1.0.0';

function loadJSON<T = unknown>(p: string, optional = false): T | null {
  if (!existsSync(p)) {
    if (optional) return null;
    throw new Error(`Required input not found: ${p}`);
  }
  return JSON.parse(readFileSync(p, 'utf-8')) as T;
}

// ---------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------

interface ManifestSegment {
  id: string;
  sura_no?: number;
  aya_start?: number;
  aya_end?: number;
}
interface ManifestStory {
  id: string;
  name_ar: string;
  name_en: string;
  category: string;
  main_figures?: string[];
  themes?: string[];
  summary_ar?: string;
  summary_en?: string;
  suras_mentioned?: number[];
  segments?: ManifestSegment[];
  connections?: Array<{ source: string; target: string; type?: string }>;
}
interface ManifestFile {
  stories: ManifestStory[];
}

interface ProphetPagesFile {
  pages: Array<{
    storyPageId: string;
    prophetId: string;
    titleArabic: string;
    titleEnglish: string;
    pageType: string;
    quranReferences: Array<{ surahNumber: number; ayahStart: number; ayahEnd?: number; linkType: string }>;
    storySections: Array<{ sectionId: string; ayahReferences: Array<{ surahNumber: number; ayahStart: number; ayahEnd?: number }> }>;
    relatedProphets?: string[];
    relatedFigures?: string[];
    relatedPlaces?: string[];
    relatedNations?: string[];
    relatedObjects?: string[];
    relatedTopics?: string[];
    sourceIds?: string[];
    reviewStatus: string;
    humanReviewRequired: boolean;
    warnings?: string[];
  }>;
}

interface ProphetsAtlasFile {
  profiles: Array<{
    prophetId: string;
    nameArabic: string;
    nameEnglish: string;
    storyIds?: string[];
    relatedProphets?: Array<{ targetProphetId: string }>;
    relatedTopics?: Array<{ topicId: string }>;
  }>;
}

interface EntityMentionsFile {
  entities: Array<{ entityId: string; entityType: string }>;
}

interface EntityRelationsFile {
  relations: Array<{ sourceEntityId: string; targetEntityId: string; relationType: string }>;
}

interface TopicAtlasFile {
  topTopicsByCoverage: Array<{ topicId: string }>;
}

interface KGFile {
  nodes: Array<{ id: string; type: string; storyId?: string }>;
}

const manifest = loadJSON<ManifestFile>(MANIFEST)!;
const prophetPages = loadJSON<ProphetPagesFile>(PROPHET_PAGES, true);
const prophetsAtlas = loadJSON<ProphetsAtlasFile>(PROPHETS_ATLAS, true);
const entityMentions = loadJSON<EntityMentionsFile>(ENTITY_MENTIONS, true);
const entityRelations = loadJSON<EntityRelationsFile>(ENTITY_RELATIONS, true);
const topicAtlas = loadJSON<TopicAtlasFile>(TOPIC_ATLAS, true);
const kg = loadJSON<KGFile>(KG, true);

interface CrossRefsFile {
  neighboursByStory?: Record<string, Array<{ storyId: string; score: number }>>;
}
const crossRefs = loadJSON<CrossRefsFile>(CROSS_REFS, true);

// ---------------------------------------------------------------------------
// Indexes
// ---------------------------------------------------------------------------

const prophetIdByStoryId = new Map<string, string>();
const storyIdsByProphetId = new Map<string, Set<string>>();
if (prophetsAtlas) {
  for (const p of prophetsAtlas.profiles) {
    for (const sid of p.storyIds || []) {
      prophetIdByStoryId.set(sid, p.prophetId);
      if (!storyIdsByProphetId.has(p.prophetId)) storyIdsByProphetId.set(p.prophetId, new Set());
      storyIdsByProphetId.get(p.prophetId)!.add(sid);
    }
  }
}

const entityIdsByType = new Map<string, Set<string>>();
if (entityMentions) {
  for (const e of entityMentions.entities) {
    if (!entityIdsByType.has(e.entityType)) entityIdsByType.set(e.entityType, new Set());
    entityIdsByType.get(e.entityType)!.add(e.entityId);
  }
}

const storyIdsInKG = new Set<string>();
if (kg) {
  for (const node of kg.nodes) {
    if (node.type === 'story' && node.storyId) storyIdsInKG.add(node.storyId);
  }
}

// ---------------------------------------------------------------------------
// Builders
// ---------------------------------------------------------------------------

function mapCategory(raw: string): RegistryStoryCategory {
  const k = (raw || '').toLowerCase().trim();
  return REGISTRY_CATEGORY_ALIASES[k] || 'needs_review';
}

function uniq<T>(xs: T[]): T[] {
  return Array.from(new Set(xs));
}

function fromManifest(story: ManifestStory): RegistryStoryEntry {
  const refs: RegistryQuranReference[] = (story.segments || [])
    .filter((s) => typeof s.sura_no === 'number' && typeof s.aya_start === 'number')
    .map((s) => ({
      surahNumber: s.sura_no!,
      ayahStart: s.aya_start!,
      ayahEnd: s.aya_end,
      linkType: 'story_segment' as RegistryQuranReferenceLinkType,
      reviewStatus: 'needs_review' as const,
    }));

  const surahCount = new Set(refs.map((r) => r.surahNumber)).size || (story.suras_mentioned?.length ?? 0);
  const warnings: string[] = [];
  if (refs.length === 0 && (story.suras_mentioned?.length ?? 0) === 0) {
    warnings.push('No verse references present; manual review required.');
  }

  const reviewStatus: 'verified' | 'needs_review' | 'missing_metadata' =
    refs.length === 0 ? 'missing_metadata' : 'needs_review';

  const relatedStories = (story.connections || [])
    .map((c) => (c.target === story.id ? c.source : c.target))
    .filter((id) => !!id && id !== story.id);

  return {
    storyId: story.id,
    titleArabic: story.name_ar,
    titleEnglish: story.name_en,
    category: mapCategory(story.category),
    sourceType: 'authored_story',
    quranReferences: refs,
    relatedProphets: prophetIdByStoryId.has(story.id) ? [prophetIdByStoryId.get(story.id)!] : [],
    relatedEntities: [],
    relatedTopics: [],
    relatedStories: uniq(relatedStories),
    segmentCount: story.segments?.length ?? 0,
    surahCount,
    ayahRangeCount: refs.length,
    hasDetailPage: true,
    detailRoute: `/stories/${story.id}`,
    reviewStatus,
    humanReviewRequired: true,
    warnings,
  };
}

function fromProphetPage(page: ProphetPagesFile['pages'][number]): RegistryStoryEntry {
  const allRefs: RegistryQuranReference[] = [];
  const surahSet = new Set<number>();

  for (const ref of page.quranReferences || []) {
    const linkType: RegistryQuranReferenceLinkType =
      ref.linkType === 'explicit_name'
        ? 'explicit'
        : ref.linkType === 'coreference'
          ? 'coreference'
          : 'contextual';
    allRefs.push({
      surahNumber: ref.surahNumber,
      ayahStart: ref.ayahStart,
      ayahEnd: ref.ayahEnd,
      linkType,
      reviewStatus: 'needs_review',
    });
    surahSet.add(ref.surahNumber);
  }
  for (const section of page.storySections || []) {
    for (const r of section.ayahReferences || []) {
      surahSet.add(r.surahNumber);
    }
  }

  const category: RegistryStoryCategory =
    page.pageType === 'compact_profile'
      ? 'compact_profile'
      : page.pageType === 'mission_summary'
        ? 'prophetic_sirah'
        : 'prophet';

  const warnings = [...(page.warnings || [])];

  return {
    storyId: page.storyPageId,
    titleArabic: page.titleArabic,
    titleEnglish: page.titleEnglish,
    category,
    sourceType: 'prophet_story_page',
    quranReferences: allRefs,
    relatedProphets: uniq([page.prophetId, ...(page.relatedProphets || [])]),
    relatedEntities: uniq([
      ...(page.relatedFigures || []),
      ...(page.relatedPlaces || []),
      ...(page.relatedNations || []),
      ...(page.relatedObjects || []),
    ]),
    relatedTopics: page.relatedTopics || [],
    relatedStories: [],
    segmentCount: page.storySections?.length ?? 0,
    surahCount: surahSet.size,
    ayahRangeCount: allRefs.length,
    hasDetailPage: true,
    detailRoute: `/prophets/${page.prophetId}`,
    reviewStatus: page.reviewStatus === 'verified' ? 'verified' : 'needs_review',
    humanReviewRequired: page.humanReviewRequired !== false,
    warnings,
  };
}

// ---------------------------------------------------------------------------
// Merge
// ---------------------------------------------------------------------------

const entries: RegistryStoryEntry[] = [];
const byId = new Map<string, RegistryStoryEntry>();

// 1. Authored stories (manifest is primary)
for (const story of manifest.stories) {
  const entry = fromManifest(story);
  entries.push(entry);
  byId.set(entry.storyId, entry);
}

// 2. Prophet story pages — add only if not already covered by a story with the same prophet
const linkedStoryIdsForPages = new Set<string>();
if (prophetPages) {
  for (const page of prophetPages.pages) {
    // Try to attach the prophet page to an authored story that shares the same prophet
    const linkedStories = Array.from(storyIdsByProphetId.get(page.prophetId) || []);
    let attachedToExisting = false;
    for (const sid of linkedStories) {
      const existing = byId.get(sid);
      if (existing) {
        existing.relatedProphets = uniq([...existing.relatedProphets, page.prophetId]);
        existing.warnings = uniq([...existing.warnings, ...(page.warnings || [])]);
        linkedStoryIdsForPages.add(page.storyPageId);
        attachedToExisting = true;
      }
    }
    // Always add the prophet page as its own registry entry (for /prophets navigation)
    const pageEntry = fromProphetPage(page);
    if (attachedToExisting) {
      pageEntry.relatedStories = uniq([...pageEntry.relatedStories, ...linkedStories]);
    }
    entries.push(pageEntry);
    byId.set(pageEntry.storyId, pageEntry);
  }
}

// 3. Enrich every entry with entity/topic links (best-effort, from KG / mentions)
for (const entry of entries) {
  if (entityMentions && entry.sourceType === 'authored_story') {
    // No strong story→entity mapping in manifest; rely on prophets & relatedStories only
    // and leave entity enrichment to backend service when DB is available.
  }
}

// 4. Inject cross-reference neighbours so each story has a meaningful
// relatedStories array. We merge with whatever was already in
// `relatedStories` (from the manifest's `connections` field) so authored
// links remain authoritative; cross-refs are appended.
if (crossRefs?.neighboursByStory) {
  for (const entry of entries) {
    const peers = crossRefs.neighboursByStory[entry.storyId] || [];
    if (peers.length === 0) continue;
    const merged = new Set<string>(entry.relatedStories);
    for (const p of peers) {
      if (p.storyId !== entry.storyId) merged.add(p.storyId);
    }
    entry.relatedStories = Array.from(merged);
  }
}

// ---------------------------------------------------------------------------
// Coverage summary
// ---------------------------------------------------------------------------

const allSurahs = new Set<number>();
const allAyahRanges: Array<string> = [];
const allProphets = new Set<string>();
let authoredCount = 0;
let prophetProfileCount = 0;
let generatedCount = 0;
let missingMetadataCount = 0;
let reviewPending = 0;

for (const e of entries) {
  if (e.sourceType === 'authored_story') authoredCount++;
  else if (e.sourceType === 'prophet_story_page') prophetProfileCount++;
  else generatedCount++;
  if (e.reviewStatus === 'missing_metadata') missingMetadataCount++;
  if (e.reviewStatus === 'needs_review') reviewPending++;
  for (const r of e.quranReferences) {
    allSurahs.add(r.surahNumber);
    allAyahRanges.push(`${r.surahNumber}:${r.ayahStart}-${r.ayahEnd ?? r.ayahStart}`);
  }
  for (const p of e.relatedProphets) allProphets.add(p);
}

const coverage: RegistryCoverageSummary = {
  totalStories: entries.length,
  authoredStories: authoredCount,
  prophetProfiles: prophetProfileCount,
  generatedCandidates: generatedCount,
  missingMetadataCount,
  surahsCovered: allSurahs.size,
  prophetsCovered: allProphets.size,
  ayahRangesLinked: new Set(allAyahRanges).size,
  reviewPendingCount: reviewPending,
};

const warnings: string[] = [];
if (coverage.totalStories === 0) warnings.push('Registry is empty — atlas will not render.');
if (missingMetadataCount > 0) {
  warnings.push(`${missingMetadataCount} stories have no Quran references — flagged as missing_metadata.`);
}
if (prophetPages) {
  const expected = prophetPages.pages.length;
  if (prophetProfileCount < expected) {
    warnings.push(`Expected ${expected} prophet story pages; merged only ${prophetProfileCount}.`);
  }
}
warnings.push('Generated and contextual links are needs_review until scholarly approval.');

// ---------------------------------------------------------------------------
// Write
// ---------------------------------------------------------------------------

const out: QuranStoryRegistryFile = {
  version: VERSION,
  generatedAt: new Date().toISOString(),
  categories: REGISTRY_CATEGORY_ORDER,
  coverage,
  stories: entries,
  warnings,
};

mkdirSync(dirname(OUT_JSON), { recursive: true });
writeFileSync(OUT_JSON, JSON.stringify(out, null, 2));
console.log(`Wrote ${OUT_JSON} (${entries.length} stories).`);

const md: string[] = [];
md.push('# Quran Story Registry — Summary');
md.push('');
md.push(`- Version: ${VERSION}`);
md.push(`- Generated: ${out.generatedAt}`);
md.push(`- Total stories: ${coverage.totalStories}`);
md.push(`- Authored stories: ${coverage.authoredStories}`);
md.push(`- Prophet profiles: ${coverage.prophetProfiles}`);
md.push(`- Generated candidates: ${coverage.generatedCandidates}`);
md.push(`- Missing metadata: ${coverage.missingMetadataCount}`);
md.push(`- Surahs covered: ${coverage.surahsCovered}`);
md.push(`- Prophets covered: ${coverage.prophetsCovered}`);
md.push(`- Ayah ranges linked: ${coverage.ayahRangesLinked}`);
md.push(`- Review pending: ${coverage.reviewPendingCount}`);
md.push('');
md.push('## Categories used');
md.push('');
const catCounts: Record<string, number> = {};
for (const e of entries) catCounts[e.category] = (catCounts[e.category] || 0) + 1;
for (const c of REGISTRY_CATEGORY_ORDER) {
  md.push(`- ${c}: ${catCounts[c] || 0}`);
}
md.push('');
md.push('## Warnings');
md.push('');
for (const w of warnings) md.push(`- ${w}`);
mkdirSync(dirname(OUT_MD), { recursive: true });
writeFileSync(OUT_MD, md.join('\n') + '\n');
console.log(`Wrote ${OUT_MD}`);
