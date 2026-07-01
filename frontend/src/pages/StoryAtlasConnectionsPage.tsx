/**
 * StoryAtlasConnectionsPage — Whole-Quran story-connection atlas.
 *
 * 5 sections (per docs/whole-quran-story-connection-implementation.md):
 *   1. Surah-by-surah explorer
 *   2. Entity explorer
 *   3. Story connection graph (filtered + read-only)
 *   4. Repeated narrative comparison
 *   5. Chronology view
 *
 * Data is fully static — loaded from generated JSON; the page is a pure
 * read-only navigation layer over the scan + graph outputs.
 *
 * Safety:
 *   - No Quran text rendered (only references). The page intentionally
 *     does not embed any ayah string.
 *   - Every inferred connection shows its review status.
 */

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Book,
  Eye,
  Filter,
  Layers,
  Map as MapIcon,
  Search,
  Users,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import connectionScan from '../data/generated/quranStoryConnections.json';
import connectionGraph from '../data/generated/quranStoryConnectionGraph.json';
import { QURAN_STORY_ENTITY_SEEDS } from '../data/quranStoryEntitySeeds';
import {
  STORY_WORLD_CHRONOLOGY,
  REVELATION_ORDER_SEEDS,
  REVELATION_ORDER_DISPUTED_NOTE_AR,
  REVELATION_ORDER_DISPUTED_NOTE_EN,
} from '../data/quranStoryChronologySeeds';
import type {
  ConnectionGraph,
  ScanOutput,
  QuranStoryEntity,
  ConnectionNode,
  ConnectionEdge,
} from '../types/quranStoryConnection';

const scan = connectionScan as ScanOutput;
const graph = connectionGraph as ConnectionGraph;

type TabId = 'surahs' | 'entities' | 'graph' | 'repeated' | 'chronology';

const TAB_META: Array<{
  id: TabId;
  labelAr: string;
  labelEn: string;
  icon: typeof MapIcon;
}> = [
  { id: 'surahs', labelAr: 'تصفح السور', labelEn: 'Surah Explorer', icon: Book },
  { id: 'entities', labelAr: 'تصفح الكيانات', labelEn: 'Entity Explorer', icon: Users },
  { id: 'graph', labelAr: 'رسم الروابط', labelEn: 'Connection Graph', icon: Layers },
  { id: 'repeated', labelAr: 'القصص المتكررة', labelEn: 'Repeated Narrative', icon: Eye },
  { id: 'chronology', labelAr: 'الترتيب الزمني', labelEn: 'Chronology', icon: Filter },
];

const ENTITY_TYPE_META: Record<QuranStoryEntity['type'], { ar: string; en: string; color: string }> = {
  prophet: { ar: 'الأنبياء', en: 'Prophets', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  person: { ar: 'الأشخاص', en: 'Persons', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  people_or_nation: { ar: 'الأمم', en: 'Peoples', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  place: { ar: 'الأماكن', en: 'Places', color: 'bg-rose-100 text-rose-800 border-rose-200' },
  animal: { ar: 'الحيوانات', en: 'Animals', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  object: { ar: 'الأشياء', en: 'Objects', color: 'bg-violet-100 text-violet-800 border-violet-200' },
  event: { ar: 'الأحداث', en: 'Events', color: 'bg-cyan-100 text-cyan-800 border-cyan-200' },
  angel: { ar: 'الملائكة', en: 'Angels', color: 'bg-sky-100 text-sky-800 border-sky-200' },
  jinn: { ar: 'الجن', en: 'Jinn', color: 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200' },
  title_or_role: { ar: 'الألقاب', en: 'Titles', color: 'bg-gray-100 text-gray-800 border-gray-200' },
  family_relation: { ar: 'الأقارب', en: 'Relations', color: 'bg-stone-100 text-stone-800 border-stone-200' },
  abstract_concept: { ar: 'المفاهيم', en: 'Concepts', color: 'bg-pink-100 text-pink-800 border-pink-200' },
  unknown: { ar: 'غير محدد', en: 'Unknown', color: 'bg-gray-100 text-gray-700 border-gray-200' },
};

const REVIEW_BADGE: Record<string, { ar: string; en: string; color: string }> = {
  needs_review: { ar: 'بحاجة للمراجعة', en: 'Needs review', color: 'bg-amber-100 text-amber-800' },
  verified: { ar: 'موثّق', en: 'Verified', color: 'bg-emerald-100 text-emerald-800' },
  rejected: { ar: 'مرفوض', en: 'Rejected', color: 'bg-red-100 text-red-800' },
};

function entityById(id: string): QuranStoryEntity | undefined {
  return QURAN_STORY_ENTITY_SEEDS.find((e) => e.entityId === id);
}

function ReviewBadge({ status }: { status: string }) {
  const { language } = useLanguageStore();
  const meta = REVIEW_BADGE[status] ?? REVIEW_BADGE.needs_review;
  return (
    <span className={clsx('inline-block text-xs px-2 py-0.5 rounded-full', meta.color)}>
      {language === 'ar' ? meta.ar : meta.en}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Section 1: Surah explorer
// ---------------------------------------------------------------------------

function SurahExplorer() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';
  const [selectedSurah, setSelectedSurah] = useState<number | null>(null);

  const surahs = useMemo(() => scan.surahs, []);
  const selected = useMemo(
    () => (selectedSurah ? surahs.find((s) => s.surahNumber === selectedSurah) : null),
    [selectedSurah, surahs]
  );

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="md:col-span-1">
        <div className="bg-white rounded-lg border border-gray-200 max-h-[70vh] overflow-y-auto">
          {surahs.map((s) => (
            <button
              key={s.surahNumber}
              onClick={() => setSelectedSurah(s.surahNumber)}
              className={clsx(
                'w-full text-left px-3 py-2 border-b border-gray-100 hover:bg-emerald-50',
                selectedSurah === s.surahNumber && 'bg-emerald-50'
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium">
                  {s.surahNumber}. {isArabic ? s.surahNameArabic : s.surahNameEnglish ?? s.surahNameArabic}
                </span>
                <span className="text-xs text-gray-500">
                  {s.detectedEntityIds.length} {isArabic ? 'كيان' : 'entities'}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
      <div className="md:col-span-2">
        {!selected ? (
          <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
            {isArabic ? 'اختر سورة من القائمة' : 'Pick a surah from the list.'}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className={clsx('text-xl font-bold mb-2', isArabic && 'font-arabic')}>
              {isArabic ? selected.surahNameArabic : selected.surahNameEnglish ?? selected.surahNameArabic}
            </h3>
            <div className="text-sm text-gray-600 mb-4">
              {isArabic ? 'سورة رقم' : 'Surah'} {selected.surahNumber} —
              {' '}{selected.detectedEntityIds.length} {isArabic ? 'كيانًا مرشّحًا' : 'candidate entities'}
            </div>

            <div className="mb-4">
              <h4 className="font-semibold mb-2 text-sm">
                {isArabic ? 'الكيانات المرشّحة' : 'Candidate entities'}
              </h4>
              <div className="flex flex-wrap gap-2">
                {selected.detectedEntityIds.map((eid) => {
                  const ent = entityById(eid);
                  const meta = ent ? ENTITY_TYPE_META[ent.type] : null;
                  return (
                    <span
                      key={eid}
                      className={clsx(
                        'inline-block text-xs px-2 py-1 rounded-md border',
                        meta?.color ?? 'bg-gray-100 text-gray-700 border-gray-200'
                      )}
                      title={ent?.labelArabic + ' / ' + ent?.labelEnglish}
                    >
                      {isArabic ? ent?.labelArabic ?? eid : ent?.labelEnglish ?? eid}
                    </span>
                  );
                })}
                {selected.detectedEntityIds.length === 0 && (
                  <span className="text-sm text-gray-500">
                    {isArabic ? 'لا توجد كيانات مرشّحة.' : 'No candidate entities.'}
                  </span>
                )}
              </div>
            </div>

            <div className="mb-4">
              <h4 className="font-semibold mb-2 text-sm">
                {isArabic ? 'قصص مرتبطة' : 'Linked stories'}
              </h4>
              {selected.mappedStoryIds.length === 0 ? (
                <span className="text-sm text-gray-500">
                  {isArabic ? 'لا قصص موثقة بعد.' : 'No documented stories yet.'}
                </span>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {selected.mappedStoryIds.map((sid) => (
                    <Link
                      key={sid}
                      to={`/stories/${sid}`}
                      className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-1 rounded-md hover:bg-emerald-100"
                    >
                      {sid}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h4 className="font-semibold mb-2 text-sm flex items-center gap-2">
                {isArabic ? 'مرشحات قصص ضمن السورة' : 'Cluster candidates'}
                <ReviewBadge status="needs_review" />
              </h4>
              <div className="space-y-2">
                {selected.storyClusterCandidates.map((c) => (
                  <div
                    key={c.candidateId}
                    className="border border-gray-200 rounded-md p-2 text-sm flex items-center justify-between"
                  >
                    <div>
                      <Link
                        to={`/quran/${selected.surahNumber}?aya=${c.ayahStart}`}
                        className="font-medium text-emerald-700 hover:text-emerald-900 hover:underline"
                      >
                        {selected.surahNumber}:{c.ayahStart}-{c.ayahEnd}
                      </Link>
                      <span className="text-gray-500 ml-2">
                        {c.entityIds.length} {isArabic ? 'كيان' : 'entities'}
                      </span>
                    </div>
                    {c.linkedStoryId ? (
                      <Link to={`/stories/${c.linkedStoryId}`} className="text-xs text-emerald-700 hover:underline">
                        {c.linkedStoryId}
                      </Link>
                    ) : (
                      <span className="text-xs text-amber-700">
                        {isArabic ? 'لا قصة مرتبطة بعد' : 'no linked story yet'}
                      </span>
                    )}
                  </div>
                ))}
                {selected.storyClusterCandidates.length === 0 && (
                  <span className="text-sm text-gray-500">
                    {isArabic ? 'لا مرشحات.' : 'No candidate clusters.'}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 2: Entity explorer
// ---------------------------------------------------------------------------

function EntityExplorer() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<QuranStoryEntity['type'] | 'all'>('all');
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);

  const filteredSeeds = useMemo(() => {
    const q = query.trim().toLowerCase();
    return QURAN_STORY_ENTITY_SEEDS.filter((e) => {
      if (typeFilter !== 'all' && e.type !== typeFilter) return false;
      if (!q) return true;
      return (
        e.labelArabic.toLowerCase().includes(q) ||
        e.labelEnglish.toLowerCase().includes(q) ||
        e.aliasesArabic.some((a) => a.toLowerCase().includes(q)) ||
        e.aliasesEnglish.some((a) => a.toLowerCase().includes(q)) ||
        (e.transliterations ?? []).some((t) => t.toLowerCase().includes(q))
      );
    });
  }, [query, typeFilter]);

  const selected = useMemo(
    () => (selectedEntityId ? entityById(selectedEntityId) : null),
    [selectedEntityId]
  );
  const selectedOccurrences = useMemo(() => {
    if (!selectedEntityId) return null;
    return scan.entityIndex.find((e) => e.entityId === selectedEntityId) ?? null;
  }, [selectedEntityId]);

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="md:col-span-1 space-y-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder={isArabic ? 'بحث' : 'Search'}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-md text-sm"
          />
        </div>
        <select
          className="w-full text-sm border border-gray-200 rounded-md py-2 px-2"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as QuranStoryEntity['type'] | 'all')}
        >
          <option value="all">{isArabic ? 'كل الأنواع' : 'All types'}</option>
          {Object.entries(ENTITY_TYPE_META).map(([k, v]) => (
            <option key={k} value={k}>{isArabic ? v.ar : v.en}</option>
          ))}
        </select>
        <div className="bg-white rounded-lg border border-gray-200 max-h-[60vh] overflow-y-auto">
          {filteredSeeds.map((ent) => {
            const occCount = scan.entityIndex.find((e) => e.entityId === ent.entityId)?.occurrences.length ?? 0;
            return (
              <button
                key={ent.entityId}
                onClick={() => setSelectedEntityId(ent.entityId)}
                className={clsx(
                  'w-full text-left px-3 py-2 border-b border-gray-100 hover:bg-emerald-50',
                  selectedEntityId === ent.entityId && 'bg-emerald-50'
                )}
              >
                <div className="text-sm font-medium">{isArabic ? ent.labelArabic : ent.labelEnglish}</div>
                <div className="text-xs text-gray-500">{occCount} {isArabic ? 'ورود' : 'occurrences'}</div>
              </button>
            );
          })}
          {filteredSeeds.length === 0 && (
            <div className="p-4 text-sm text-gray-500">
              {isArabic ? 'لا نتائج.' : 'No results.'}
            </div>
          )}
        </div>
      </div>
      <div className="md:col-span-2">
        {!selected ? (
          <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
            {isArabic ? 'اختر كيانًا.' : 'Pick an entity.'}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className={clsx('text-xl font-bold mb-1', isArabic && 'font-arabic')}>
              {isArabic ? selected.labelArabic : selected.labelEnglish}
            </h3>
            <div className="flex flex-wrap gap-2 mb-4">
              <span className={clsx('text-xs px-2 py-0.5 rounded-md border', ENTITY_TYPE_META[selected.type].color)}>
                {isArabic ? ENTITY_TYPE_META[selected.type].ar : ENTITY_TYPE_META[selected.type].en}
              </span>
              <ReviewBadge status={selected.reviewedDictionary ? 'verified' : 'needs_review'} />
              {selected.chronologicalGroup && (
                <span className="text-xs px-2 py-0.5 rounded-md bg-gray-100 text-gray-700">
                  {selected.chronologicalGroup}
                </span>
              )}
            </div>

            <div className="mb-3 text-sm">
              <strong>{isArabic ? 'أسماء عربية:' : 'Arabic aliases:'}</strong> {selected.aliasesArabic.join('، ')}
            </div>
            <div className="mb-4 text-sm">
              <strong>{isArabic ? 'بالإنجليزية:' : 'English aliases:'}</strong> {selected.aliasesEnglish.join(', ')}
            </div>

            <h4 className="font-semibold text-sm mb-2">
              {isArabic ? 'مواضع الورود في المصحف' : 'Occurrences in the mushaf'}
            </h4>
            {!selectedOccurrences ? (
              <span className="text-sm text-gray-500">
                {isArabic ? 'لا توجد مواضع مرصودة بعد.' : 'No detected occurrences yet.'}
              </span>
            ) : (
              <div className="max-h-[40vh] overflow-y-auto border border-gray-100 rounded">
                {selectedOccurrences.occurrences.map((o, idx) => (
                  <div key={idx} className="border-b border-gray-100 px-3 py-1.5 text-sm flex items-center justify-between">
                    <span>
                      {o.surahNumber}:{o.ayahStart}
                      {o.ayahEnd && o.ayahEnd !== o.ayahStart ? `-${o.ayahEnd}` : ''}
                    </span>
                    <span className="text-xs text-gray-500">{o.detectionType}</span>
                  </div>
                ))}
              </div>
            )}

            {selected.relatedStories.length > 0 && (
              <div className="mt-4">
                <h4 className="font-semibold text-sm mb-2">{isArabic ? 'قصص مرتبطة' : 'Related stories'}</h4>
                <div className="flex flex-wrap gap-2">
                  {selected.relatedStories.map((sid) => (
                    <Link key={sid} to={`/stories/${sid}`} className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded">
                      {sid}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {selected.warnings.length > 0 && (
              <div className="mt-4 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
                {selected.warnings.join(' / ')}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 3: Graph (table-only, filterable)
// ---------------------------------------------------------------------------

function ConnectionGraphView() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';
  const [edgeTypeFilter, setEdgeTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'needs_review' | 'verified'>('all');

  const edgeTypes = useMemo(() => {
    const set = new Set<string>();
    for (const e of graph.edges) set.add(e.edgeType);
    return ['all', ...Array.from(set).sort()];
  }, []);

  const filtered = useMemo(() => {
    return graph.edges.filter((e) => {
      if (edgeTypeFilter !== 'all' && e.edgeType !== edgeTypeFilter) return false;
      if (statusFilter !== 'all' && e.reviewStatus !== statusFilter) return false;
      return true;
    }).slice(0, 200);
  }, [edgeTypeFilter, statusFilter]);

  const nodeLabel = (id: string): string => {
    const n = graph.nodes.find((x) => x.id === id);
    if (!n) return id;
    return (isArabic ? n.labelArabic : n.labelEnglish) ?? id;
  };

  return (
    <div>
      <div className="flex gap-2 flex-wrap mb-4">
        <select
          className="text-sm border border-gray-200 rounded-md py-1.5 px-2"
          value={edgeTypeFilter}
          onChange={(e) => setEdgeTypeFilter(e.target.value)}
        >
          {edgeTypes.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          className="text-sm border border-gray-200 rounded-md py-1.5 px-2"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as 'all' | 'needs_review' | 'verified')}
        >
          <option value="all">{isArabic ? 'كل الحالات' : 'All statuses'}</option>
          <option value="needs_review">{isArabic ? 'بحاجة للمراجعة' : 'needs_review'}</option>
          <option value="verified">{isArabic ? 'موثّقة' : 'verified'}</option>
        </select>
      </div>
      <div className="text-xs text-gray-500 mb-2">
        {isArabic ? 'عرض' : 'Showing'} {filtered.length} / {graph.edges.length} {isArabic ? 'علاقة' : 'edges'}
      </div>
      <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
        <table className="text-sm w-full">
          <thead className="bg-gray-50 text-xs uppercase text-gray-600">
            <tr>
              <th className="px-3 py-2 text-left">{isArabic ? 'من' : 'From'}</th>
              <th className="px-3 py-2 text-left">{isArabic ? 'النوع' : 'Edge'}</th>
              <th className="px-3 py-2 text-left">{isArabic ? 'إلى' : 'To'}</th>
              <th className="px-3 py-2 text-left">{isArabic ? 'الحالة' : 'Status'}</th>
              <th className="px-3 py-2 text-left">{isArabic ? 'الثقة' : 'Conf.'}</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <tr key={e.edgeId} className="border-t border-gray-100">
                <td className="px-3 py-1.5">{nodeLabel(e.sourceNodeId)}</td>
                <td className="px-3 py-1.5 text-xs text-gray-500">{e.edgeType}</td>
                <td className="px-3 py-1.5">{nodeLabel(e.targetNodeId)}</td>
                <td className="px-3 py-1.5"><ReviewBadge status={e.reviewStatus} /></td>
                <td className="px-3 py-1.5">{e.confidence.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 4: Repeated narrative comparison
// ---------------------------------------------------------------------------

function RepeatedNarrative() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';
  const [entityId, setEntityId] = useState<string>(scan.crossSurahLinks[0]?.entityId ?? '');

  const cross = useMemo(
    () => scan.crossSurahLinks.find((c) => c.entityId === entityId) ?? null,
    [entityId]
  );
  const entityOccs = useMemo(
    () => scan.entityIndex.find((e) => e.entityId === entityId) ?? null,
    [entityId]
  );

  return (
    <div>
      <div className="mb-3 max-w-md">
        <select
          className="w-full text-sm border border-gray-200 rounded-md py-2 px-2"
          value={entityId}
          onChange={(e) => setEntityId(e.target.value)}
        >
          {scan.crossSurahLinks.map((c) => {
            const ent = entityById(c.entityId);
            return (
              <option key={c.entityId} value={c.entityId}>
                {isArabic ? ent?.labelArabic ?? c.entityId : ent?.labelEnglish ?? c.entityId}
                {' '}— {c.occurrenceCount} {isArabic ? 'ورود في' : 'occurrences across'} {c.surahNumbers.length} {isArabic ? 'سورة' : 'surahs'}
              </option>
            );
          })}
        </select>
      </div>
      {!cross || !entityOccs ? (
        <div className="text-gray-500 text-sm">
          {isArabic ? 'لا روابط مرصودة بعد.' : 'No cross-surah links detected.'}
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {cross.surahNumbers.map((s) => {
            const surahOcc = entityOccs.occurrences.filter((o) => o.surahNumber === s);
            const surahName = scan.surahs.find((x) => x.surahNumber === s);
            return (
              <div key={s} className="bg-white rounded-lg border border-gray-200 p-3">
                <div className="font-semibold mb-2">
                  {s}. {isArabic ? surahName?.surahNameArabic : surahName?.surahNameEnglish ?? surahName?.surahNameArabic}
                </div>
                <div className="text-sm text-gray-700 mb-2">
                  {surahOcc.length} {isArabic ? 'ورود' : 'occurrences'}
                </div>
                <div className="text-xs text-gray-500">
                  {surahOcc.slice(0, 8).map((o, i) => (
                    <span key={i} className="inline-block mr-1.5">{s}:{o.ayahStart}</span>
                  ))}
                  {surahOcc.length > 8 && <span>… +{surahOcc.length - 8}</span>}
                </div>
                <ReviewBadge status={cross.reviewStatus} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 5: Chronology view
// ---------------------------------------------------------------------------

function ChronologyView() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';
  return (
    <div className="space-y-6">
      <div className="bg-amber-50 border border-amber-200 rounded-md p-3 text-sm">
        {isArabic ? REVELATION_ORDER_DISPUTED_NOTE_AR : REVELATION_ORDER_DISPUTED_NOTE_EN}
      </div>

      <section>
        <h3 className="text-lg font-semibold mb-2">
          {isArabic ? 'الترتيب القصصي' : 'Story-world chronology'}
        </h3>
        <ol className="space-y-2">
          {[...STORY_WORLD_CHRONOLOGY].sort((a, b) => (a.orderIndex ?? 0) - (b.orderIndex ?? 0)).map((c) => (
            <li key={c.itemId} className="bg-white border border-gray-200 rounded p-3 flex items-start justify-between gap-4">
              <div>
                <div className="font-medium">{c.orderIndex}. {c.itemId}</div>
                <div className="text-sm text-gray-700 mt-1">{isArabic ? c.notesArabic : c.notesEnglish}</div>
              </div>
              <div className="text-xs flex flex-col items-end gap-1">
                <ReviewBadge status={c.reviewStatus} />
                <span className="text-gray-500">{isArabic ? 'دقة' : 'certainty'}: {c.certainty}</span>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h3 className="text-lg font-semibold mb-2">
          {isArabic ? 'ترتيب النزول (محل خلاف)' : 'Revelation order (disputed)'}
        </h3>
        <ol className="space-y-2">
          {[...REVELATION_ORDER_SEEDS].sort((a, b) => (a.orderIndex ?? 0) - (b.orderIndex ?? 0)).map((c) => (
            <li key={c.itemId} className="bg-white border border-gray-200 rounded p-3 flex items-start justify-between gap-4">
              <div>
                <div className="font-medium">#{c.orderIndex} — {isArabic ? 'سورة' : 'Surah'} {c.itemId}</div>
                <div className="text-sm text-gray-700 mt-1">{isArabic ? c.notesArabic : c.notesEnglish}</div>
              </div>
              <div className="text-xs flex flex-col items-end gap-1">
                <ReviewBadge status={c.reviewStatus} />
                <span className="text-gray-500">{c.certainty}</span>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page shell
// ---------------------------------------------------------------------------

export function StoryAtlasConnectionsPage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';
  const [tab, setTab] = useState<TabId>('surahs');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      <Link to="/story-atlas" className="inline-flex items-center text-sm text-emerald-700 mb-4 hover:underline">
        <ArrowLeft className="w-4 h-4 mr-1" />
        {isArabic ? 'العودة إلى أطلس القصص' : 'Back to Story Atlas'}
      </Link>
      <header className="mb-6">
        <div className="flex items-center gap-3">
          <MapIcon className="w-7 h-7 text-emerald-600" />
          <h1 className={clsx('text-2xl font-bold text-gray-900', isArabic && 'font-arabic')}>
            {isArabic ? 'أطلس روابط القصص في القرآن' : 'Whole-Quran Story Connection Atlas'}
          </h1>
        </div>
        <p className={clsx('text-gray-600 mt-1', isArabic && 'font-arabic')}>
          {isArabic
            ? 'كل الروابط هنا مرشّحات تتطلب مراجعة علمية. لا يوجد نص قرآني داخل البيانات؛ المراجع فقط بأرقام السورة والآية.'
            : 'All links are candidate inferences pending scholarly review. No Quran text is embedded in the data — references only.'}
        </p>
      </header>

      <nav className="flex flex-wrap gap-2 mb-4">
        {TAB_META.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm border',
                tab === t.id
                  ? 'bg-emerald-600 text-white border-emerald-600'
                  : 'bg-white text-gray-700 border-gray-200 hover:bg-emerald-50'
              )}
            >
              <Icon className="w-4 h-4" />
              {isArabic ? t.labelAr : t.labelEn}
            </button>
          );
        })}
      </nav>

      <main>
        {tab === 'surahs' && <SurahExplorer />}
        {tab === 'entities' && <EntityExplorer />}
        {tab === 'graph' && <ConnectionGraphView />}
        {tab === 'repeated' && <RepeatedNarrative />}
        {tab === 'chronology' && <ChronologyView />}
      </main>
    </div>
  );
}

export default StoryAtlasConnectionsPage;

export type { ConnectionGraph, ConnectionNode, ConnectionEdge };
