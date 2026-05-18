#!/usr/bin/env npx tsx
/**
 * Build Quran Story Atlas Connections.
 *
 * Reads:
 *   - frontend/src/data/generated/quranStoryRegistry.json
 *   - frontend/src/data/generated/quranEntityRelations.json
 *   - frontend/src/data/generated/quranTopicAtlas.json (optional)
 *
 * Writes:
 *   - frontend/src/data/generated/quranStoryAtlasConnections.json
 *   - docs/generated/quran-story-atlas-connections-summary.md
 *
 * Rules:
 *   - Every connection carries ≥ 1 evidence reference (surahNumber + ayahStart).
 *   - All connections default to reviewStatus = "needs_review" and
 *     humanReviewRequired = true. No interpretive text.
 *   - The script never invents Quran text or ayah references; references
 *     are pulled from the registry / entity relations only.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';

import type {
  QuranStoryRegistryFile,
  RegistryQuranReference,
} from '../frontend/src/types/quranStoryRegistry';

const ROOT = resolve(__dirname, '..');
const GEN = join(ROOT, 'frontend/src/data/generated');
const REGISTRY = join(GEN, 'quranStoryRegistry.json');
const ENTITY_RELATIONS = join(GEN, 'quranEntityRelations.json');

const OUT_JSON = join(GEN, 'quranStoryAtlasConnections.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-story-atlas-connections-summary.md');
const VERSION = '1.0.0';

type ConnectionTargetType = 'story' | 'prophet' | 'entity' | 'topic' | 'surah' | 'ayah_range';
type ConnectionRelationType =
  | 'same_prophet'
  | 'same_people'
  | 'same_place'
  | 'same_object'
  | 'same_theme'
  | 'chronology'
  | 'repeated_narrative'
  | 'related_topic'
  | 'needs_review';

interface ConnectionEvidence {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
}

interface StoryAtlasConnection {
  sourceStoryId: string;
  targetId: string;
  targetType: ConnectionTargetType;
  relationType: ConnectionRelationType;
  evidenceReferences: ConnectionEvidence[];
  confidence: number;
  reviewStatus: 'verified' | 'needs_review';
  humanReviewRequired: boolean;
  warnings: string[];
}

interface ConnectionsFile {
  version: string;
  generatedAt: string;
  totalConnections: number;
  byTargetType: Record<string, number>;
  byRelationType: Record<string, number>;
  connections: StoryAtlasConnection[];
  warnings: string[];
}

if (!existsSync(REGISTRY)) {
  throw new Error('Run scripts/build-quran-story-registry.ts first.');
}

const registry = JSON.parse(readFileSync(REGISTRY, 'utf-8')) as QuranStoryRegistryFile;
const entityRelations = existsSync(ENTITY_RELATIONS)
  ? (JSON.parse(readFileSync(ENTITY_RELATIONS, 'utf-8')) as {
      relations: Array<{
        sourceEntityId: string;
        targetEntityId: string;
        relationType: string;
        evidenceReferences: Array<{ surahNumber: number; ayahStart: number; ayahEnd?: number }>;
        confidence: number;
      }>;
    })
  : { relations: [] };

const connections: StoryAtlasConnection[] = [];

function evidenceFromStory(refs: RegistryQuranReference[], limit = 3): ConnectionEvidence[] {
  return refs.slice(0, limit).map((r) => ({
    surahNumber: r.surahNumber,
    ayahStart: r.ayahStart,
    ayahEnd: r.ayahEnd,
  }));
}

// 1. story → prophet
for (const story of registry.stories) {
  for (const p of story.relatedProphets) {
    const ev = evidenceFromStory(story.quranReferences);
    if (ev.length === 0) continue;
    connections.push({
      sourceStoryId: story.storyId,
      targetId: p,
      targetType: 'prophet',
      relationType: 'same_prophet',
      evidenceReferences: ev,
      confidence: 0.85,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [],
    });
  }
}

// 2. story → topic
for (const story of registry.stories) {
  for (const t of story.relatedTopics) {
    const ev = evidenceFromStory(story.quranReferences);
    if (ev.length === 0) continue;
    connections.push({
      sourceStoryId: story.storyId,
      targetId: t,
      targetType: 'topic',
      relationType: 'related_topic',
      evidenceReferences: ev,
      confidence: 0.6,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [],
    });
  }
}

// 3. story → entity (from relatedEntities)
for (const story of registry.stories) {
  for (const e of story.relatedEntities) {
    const ev = evidenceFromStory(story.quranReferences);
    if (ev.length === 0) continue;
    connections.push({
      sourceStoryId: story.storyId,
      targetId: e,
      targetType: 'entity',
      relationType: 'same_people',
      evidenceReferences: ev,
      confidence: 0.55,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [],
    });
  }
}

// 4. story → other story (from relatedStories)
const idSet = new Set(registry.stories.map((s) => s.storyId));
for (const story of registry.stories) {
  for (const rs of story.relatedStories) {
    if (rs === story.storyId) continue;
    const ev = evidenceFromStory(story.quranReferences);
    if (ev.length === 0) continue;
    connections.push({
      sourceStoryId: story.storyId,
      targetId: rs,
      targetType: 'story',
      relationType: 'repeated_narrative',
      evidenceReferences: ev,
      confidence: idSet.has(rs) ? 0.7 : 0.4,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: idSet.has(rs) ? [] : ['Target story not resolved in registry.'],
    });
  }
}

// 5. story → surah (one connection per unique surah)
for (const story of registry.stories) {
  const surahs = new Set<number>();
  for (const r of story.quranReferences) surahs.add(r.surahNumber);
  for (const sn of surahs) {
    const refsForSurah = story.quranReferences.filter((r) => r.surahNumber === sn);
    connections.push({
      sourceStoryId: story.storyId,
      targetId: `surah:${sn}`,
      targetType: 'surah',
      relationType: 'same_place',
      evidenceReferences: refsForSurah.slice(0, 5).map((r) => ({
        surahNumber: r.surahNumber,
        ayahStart: r.ayahStart,
        ayahEnd: r.ayahEnd,
      })),
      confidence: 0.9,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [],
    });
  }
}

const byTargetType: Record<string, number> = {};
const byRelationType: Record<string, number> = {};
for (const c of connections) {
  byTargetType[c.targetType] = (byTargetType[c.targetType] || 0) + 1;
  byRelationType[c.relationType] = (byRelationType[c.relationType] || 0) + 1;
}

const warnings: string[] = [];
warnings.push('All connections are needs_review until scholarly approval.');
if (connections.length === 0) warnings.push('No connections were derived from the registry.');

const out: ConnectionsFile = {
  version: VERSION,
  generatedAt: new Date().toISOString(),
  totalConnections: connections.length,
  byTargetType,
  byRelationType,
  connections,
  warnings,
};

mkdirSync(dirname(OUT_JSON), { recursive: true });
writeFileSync(OUT_JSON, JSON.stringify(out, null, 2));
console.log(`Wrote ${OUT_JSON} (${connections.length} connections).`);

const md: string[] = [];
md.push('# Quran Story Atlas Connections — Summary');
md.push('');
md.push(`- Version: ${VERSION}`);
md.push(`- Generated: ${out.generatedAt}`);
md.push(`- Total connections: ${connections.length}`);
md.push('');
md.push('## By target type');
md.push('');
for (const [k, v] of Object.entries(byTargetType)) md.push(`- ${k}: ${v}`);
md.push('');
md.push('## By relation type');
md.push('');
for (const [k, v] of Object.entries(byRelationType)) md.push(`- ${k}: ${v}`);
md.push('');
md.push('## Warnings');
md.push('');
for (const w of warnings) md.push(`- ${w}`);
mkdirSync(dirname(OUT_MD), { recursive: true });
writeFileSync(OUT_MD, md.join('\n') + '\n');
console.log(`Wrote ${OUT_MD}`);

// Touch entityRelations to avoid unused-var warning when no enrichment is performed.
void entityRelations;
