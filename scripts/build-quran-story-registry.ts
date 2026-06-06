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
  SubcategoryGroup,
} from '../frontend/src/types/quranStoryRegistry';
import {
  REGISTRY_CATEGORY_ALIASES,
  REGISTRY_CATEGORY_ORDER,
  SUBCATEGORY_GROUP_ORDER,
  parseSubcategory,
} from '../frontend/src/types/quranStoryRegistry';
import { STORY_SUBCATEGORY_MAP } from './storySubcategoryMap';
import {
  QURAN_PEOPLE_INDEX,
  PERSON_ALIASES,
  STORY_EXTRA_PEOPLE,
} from './quranPeopleIndex';
import {
  QURAN_PLACES_INDEX,
  SUBCATEGORY_TO_PLACE,
  STORY_EXTRA_PLACES,
} from './quranPlacesIndex';
import type {
  PersonIndexEntry,
  PersonRole,
  PlaceIndexEntry,
  PlaceType,
} from '../frontend/src/types/quranStoryRegistry';
import {
  PERSON_ROLE_ORDER,
  PLACE_TYPE_ORDER,
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
const OUT_PEOPLE_JSON = join(GEN, 'quranPeopleIndex.json');
const OUT_PLACES_JSON = join(GEN, 'quranPlacesIndex.json');
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

// ---------------------------------------------------------------------------
// People resolution
// ---------------------------------------------------------------------------

const knownPersonIds = new Set<string>(QURAN_PEOPLE_INDEX.map((p) => p.personId));
const knownProphetIds = new Set<string>(
  (prophetsAtlas?.profiles || []).map((p) => p.prophetId),
);

/**
 * Normalise raw alias strings before lookup. Lowercases, strips
 * apostrophes/back-ticks, collapses whitespace. Returns the canonical
 * personId for a known alias, or null if the alias is unknown.
 */
function normaliseAlias(raw: string): string {
  return raw.toLowerCase().replace(/['`’]/g, '').replace(/\s+/g, ' ').trim();
}
const NORMALISED_ALIASES: Record<string, string> = (() => {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(PERSON_ALIASES)) {
    out[normaliseAlias(k)] = v;
  }
  return out;
})();

function resolveAlias(raw: string): string | null {
  // Prophet IDs and person IDs pass through verbatim when already canonical.
  if (knownProphetIds.has(raw) || knownPersonIds.has(raw)) return raw;
  const n = normaliseAlias(raw);
  return NORMALISED_ALIASES[n] ?? null;
}

/**
 * Resolve the canonical peopleIds for a given storyId from:
 *   1. raw mainFigures strings (via PERSON_ALIASES)
 *   2. the story's relatedProphets (prophet IDs pass straight through)
 *   3. the storyId-keyed STORY_EXTRA_PEOPLE map
 *
 * Deduplicated. Sorted by PERSON_ROLE_ORDER then alphabetically so the
 * UI sees a stable presentation order.
 */
function resolvePeople(
  storyId: string,
  mainFigures: string[],
  relatedProphets: string[],
): string[] {
  const out = new Set<string>();
  for (const f of mainFigures) {
    const id = resolveAlias(f);
    if (id) out.add(id);
  }
  for (const p of relatedProphets) {
    if (knownProphetIds.has(p)) out.add(p);
  }
  for (const extra of STORY_EXTRA_PEOPLE[storyId] || []) {
    if (knownPersonIds.has(extra) || knownProphetIds.has(extra)) out.add(extra);
  }
  return Array.from(out).sort((a, b) => {
    const ra = roleOf(a);
    const rb = roleOf(b);
    const ri = ra ? PERSON_ROLE_ORDER.indexOf(ra) : 99;
    const rj = rb ? PERSON_ROLE_ORDER.indexOf(rb) : 99;
    if (ri !== rj) return ri - rj;
    return a.localeCompare(b);
  });
}

function roleOf(id: string): PersonRole | null {
  if (knownProphetIds.has(id)) return 'prophet';
  const entry = QURAN_PEOPLE_INDEX.find((p) => p.personId === id);
  return entry?.role ?? null;
}

// ---------------------------------------------------------------------------
// Places resolution
// ---------------------------------------------------------------------------

const knownPlaceIds = new Set<string>(QURAN_PLACES_INDEX.map((p) => p.placeId));

/**
 * Resolve placeIds for a given story from:
 *   1. its subcategories — every `place:*` tag is looked up in
 *      SUBCATEGORY_TO_PLACE and expanded to one or more placeIds.
 *   2. relatedPlaces from the prophet-page input (already canonical
 *      entity IDs prefixed with `entity_place_` — we keep those as
 *      hints but only emit them if they match a known placeId).
 *   3. STORY_EXTRA_PLACES — hand-authored extras the subcategory tags
 *      don't cover (e.g. Cave of Hira for the Muhammad story).
 *
 * Output is deduplicated and sorted by PLACE_TYPE_ORDER then by placeId.
 */
function resolvePlaces(
  storyId: string,
  subcategories: string[],
  relatedPlaces: string[],
): string[] {
  const out = new Set<string>();
  for (const sc of subcategories) {
    const mapped = SUBCATEGORY_TO_PLACE[sc];
    if (!mapped) continue;
    for (const pid of mapped) {
      if (knownPlaceIds.has(pid)) out.add(pid);
    }
  }
  for (const rp of relatedPlaces) {
    // Prophet-page relatedPlaces use entity-graph IDs like
    // "entity_place_sinai" — try a trivial normalisation, then trust
    // the storyId extras to cover misses.
    const normalised = rp.replace(/^entity_place_/, 'place_');
    if (knownPlaceIds.has(normalised)) out.add(normalised);
  }
  for (const extra of STORY_EXTRA_PLACES[storyId] || []) {
    if (knownPlaceIds.has(extra)) out.add(extra);
  }
  return Array.from(out).sort((a, b) => {
    const ta = typeOf(a);
    const tb = typeOf(b);
    const ti = ta ? PLACE_TYPE_ORDER.indexOf(ta) : 99;
    const tj = tb ? PLACE_TYPE_ORDER.indexOf(tb) : 99;
    if (ti !== tj) return ti - tj;
    return a.localeCompare(b);
  });
}

function typeOf(id: string): PlaceType | null {
  const entry = QURAN_PLACES_INDEX.find((p) => p.placeId === id);
  return entry?.type ?? null;
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
    themes: uniq(story.themes || []),
    mainFigures: uniq(story.main_figures || []),
    subcategories: resolveSubcategories(story.id),
    peopleIds: resolvePeople(
      story.id,
      story.main_figures || [],
      prophetIdByStoryId.has(story.id) ? [prophetIdByStoryId.get(story.id)!] : [],
    ),
    placeIds: resolvePlaces(story.id, resolveSubcategories(story.id), []),
  };
}

/**
 * Resolve and normalise the subcategory tags for a given storyId.
 *
 * Rules:
 *   - Drops malformed entries (no colon, unknown group).
 *   - Deduplicates while preserving the order from the map.
 *   - Groups are emitted in SUBCATEGORY_GROUP_ORDER so the UI sees a
 *     predictable layout.
 */
function resolveSubcategories(storyId: string): string[] {
  const raw = STORY_SUBCATEGORY_MAP[storyId] || [];
  const seen = new Set<string>();
  const buckets = new Map<SubcategoryGroup, string[]>();
  for (const s of raw) {
    if (seen.has(s)) continue;
    const parsed = parseSubcategory(s);
    if (!parsed) continue;
    seen.add(s);
    if (!buckets.has(parsed.group)) buckets.set(parsed.group, []);
    buckets.get(parsed.group)!.push(s);
  }
  const ordered: string[] = [];
  for (const g of SUBCATEGORY_GROUP_ORDER) {
    for (const s of buckets.get(g) || []) ordered.push(s);
  }
  return ordered;
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

  // Prophet pages always carry the "role:prophet" subcategory; mission
  // summaries also pick up "event:revelation" so users can find the sirah
  // entry from the events facet. Any storyId already present in the
  // hand-authored map overrides this.
  const inherited =
    category === 'prophetic_sirah'
      ? ['role:prophet', 'role:messenger', 'event:revelation']
      : ['role:prophet'];
  const subcats = STORY_SUBCATEGORY_MAP[page.storyPageId]
    ? resolveSubcategories(page.storyPageId)
    : resolveSubcategoriesFromList(inherited);

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
    themes: [],
    mainFigures: [page.prophetId, ...(page.relatedFigures || [])],
    subcategories: subcats,
    peopleIds: resolvePeople(
      page.storyPageId,
      page.relatedFigures || [],
      uniq([page.prophetId, ...(page.relatedProphets || [])]),
    ),
    placeIds: resolvePlaces(page.storyPageId, subcats, page.relatedPlaces || []),
  };
}

/**
 * Variant of resolveSubcategories that takes an arbitrary list of raw
 * "group:tag" strings instead of looking up by storyId. Used for inherited
 * defaults (e.g. every prophet page gets "role:prophet").
 */
function resolveSubcategoriesFromList(raw: string[]): string[] {
  const seen = new Set<string>();
  const buckets = new Map<SubcategoryGroup, string[]>();
  for (const s of raw) {
    if (seen.has(s)) continue;
    const parsed = parseSubcategory(s);
    if (!parsed) continue;
    seen.add(s);
    if (!buckets.has(parsed.group)) buckets.set(parsed.group, []);
    buckets.get(parsed.group)!.push(s);
  }
  const ordered: string[] = [];
  for (const g of SUBCATEGORY_GROUP_ORDER) {
    for (const s of buckets.get(g) || []) ordered.push(s);
  }
  return ordered;
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

// Subcategory facet histogram so reviewers can spot under-tagged groups
// at a glance.
md.push('## Subcategory coverage');
md.push('');
const groupStoryIds = new Map<string, Set<string>>();
const tagStoryIds = new Map<string, Set<string>>();
for (const e of entries) {
  for (const sc of e.subcategories || []) {
    const idx = sc.indexOf(':');
    if (idx <= 0) continue;
    const group = sc.slice(0, idx);
    if (!groupStoryIds.has(group)) groupStoryIds.set(group, new Set());
    groupStoryIds.get(group)!.add(e.storyId);
    if (!tagStoryIds.has(sc)) tagStoryIds.set(sc, new Set());
    tagStoryIds.get(sc)!.add(e.storyId);
  }
}
for (const g of SUBCATEGORY_GROUP_ORDER) {
  const storyIds = groupStoryIds.get(g);
  if (!storyIds || storyIds.size === 0) continue;
  md.push(`- **${g}** — ${storyIds.size} stories`);
  const tags = Array.from(tagStoryIds.entries())
    .filter(([k]) => k.startsWith(`${g}:`))
    .sort((a, b) => b[1].size - a[1].size || a[0].localeCompare(b[0]));
  for (const [tag, ids] of tags) {
    md.push(`  - ${tag} (${ids.size})`);
  }
}
md.push('');
// Places coverage histogram.
md.push('## Places coverage');
md.push('');
const typeStoryIds = new Map<PlaceType, Set<string>>();
const placeStoryIds = new Map<string, Set<string>>();
for (const e of entries) {
  for (const pid of e.placeIds || []) {
    const t = typeOf(pid);
    if (!t) continue;
    if (!typeStoryIds.has(t)) typeStoryIds.set(t, new Set());
    typeStoryIds.get(t)!.add(e.storyId);
    if (!placeStoryIds.has(pid)) placeStoryIds.set(pid, new Set());
    placeStoryIds.get(pid)!.add(e.storyId);
  }
}
for (const t of PLACE_TYPE_ORDER) {
  const sids = typeStoryIds.get(t);
  if (!sids || sids.size === 0) continue;
  md.push(`- **${t}** — ${sids.size} stories`);
  const places = Array.from(placeStoryIds.entries())
    .filter(([pid]) => typeOf(pid) === t)
    .sort((a, b) => b[1].size - a[1].size || a[0].localeCompare(b[0]));
  for (const [pid, ids] of places) md.push(`  - ${pid} (${ids.size})`);
}
md.push('');

// People coverage histogram (similar shape to subcategory facets).
md.push('## People coverage');
md.push('');
const roleStoryIds = new Map<PersonRole, Set<string>>();
const personStoryIds = new Map<string, Set<string>>();
for (const e of entries) {
  for (const pid of e.peopleIds || []) {
    const r = roleOf(pid);
    if (!r) continue;
    if (!roleStoryIds.has(r)) roleStoryIds.set(r, new Set());
    roleStoryIds.get(r)!.add(e.storyId);
    if (!personStoryIds.has(pid)) personStoryIds.set(pid, new Set());
    personStoryIds.get(pid)!.add(e.storyId);
  }
}
for (const r of PERSON_ROLE_ORDER) {
  const sids = roleStoryIds.get(r);
  if (!sids || sids.size === 0) continue;
  md.push(`- **${r}** — ${sids.size} stories`);
  const peers = Array.from(personStoryIds.entries())
    .filter(([pid]) => roleOf(pid) === r)
    .sort((a, b) => b[1].size - a[1].size || a[0].localeCompare(b[0]));
  for (const [pid, ids] of peers) md.push(`  - ${pid} (${ids.size})`);
}
md.push('');
md.push('## Warnings');
md.push('');
for (const w of warnings) md.push(`- ${w}`);
mkdirSync(dirname(OUT_MD), { recursive: true });
writeFileSync(OUT_MD, md.join('\n') + '\n');
console.log(`Wrote ${OUT_MD}`);

// Emit the people index as its own JSON so the frontend can load
// canonical names / roles / notes without bundling the alias map. The
// build script is the single source of truth for the published index.
const peopleOut = {
  version: VERSION,
  generatedAt: out.generatedAt,
  people: QURAN_PEOPLE_INDEX as PersonIndexEntry[],
  // Include the prophet IDs so the frontend can build a unified people
  // list (prophet + non-prophet) without having to read prophetsAtlas
  // separately on the static-loading path.
  prophets: (prophetsAtlas?.profiles || []).map((p) => ({
    personId: p.prophetId,
    nameArabic: (p as { nameArabic?: string }).nameArabic ?? p.prophetId,
    nameEnglish: (p as { nameEnglish?: string }).nameEnglish ?? p.prophetId,
    role: 'prophet' as PersonRole,
  })),
};
writeFileSync(OUT_PEOPLE_JSON, JSON.stringify(peopleOut, null, 2));
console.log(`Wrote ${OUT_PEOPLE_JSON}`);

const placesOut = {
  version: VERSION,
  generatedAt: out.generatedAt,
  places: QURAN_PLACES_INDEX as PlaceIndexEntry[],
};
writeFileSync(OUT_PLACES_JSON, JSON.stringify(placesOut, null, 2));
console.log(`Wrote ${OUT_PLACES_JSON}`);
