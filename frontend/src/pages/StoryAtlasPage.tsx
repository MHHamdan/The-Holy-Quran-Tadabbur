import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Map,
  Book,
  Search,
  AlertTriangle,
  Users,
  Layers,
  ArrowRight,
  Network,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import clsx from 'clsx';
import { ConnectedStoriesPanel } from '../components/stories/ConnectedStoriesPanel';

import {
  getRegistry,
  getStoriesByCategory,
  getStoriesBySubcategory,
  getStoriesByPerson,
  getSubcategoryFacets,
  getPeopleFacets,
  getPerson,
  searchStories,
  isRegistryHealthy,
} from '../utils/storyRegistryAdapter';
import {
  REGISTRY_CATEGORY_LABELS,
  REGISTRY_CATEGORY_ORDER,
  SUBCATEGORY_GROUP_LABELS,
  PERSON_ROLE_LABELS,
  getSubcategoryLabel,
} from '../types/quranStoryRegistry';
import type {
  RegistryStoryCategory,
  RegistryStoryEntry,
  SubcategoryGroup,
} from '../types/quranStoryRegistry';

type CategoryFilter = RegistryStoryCategory | 'all';

const CATEGORY_FILTERS: { id: CategoryFilter; labelAr: string; labelEn: string }[] = [
  { id: 'all', labelAr: 'الكل', labelEn: 'All' },
  ...REGISTRY_CATEGORY_ORDER.map((id) => ({
    id,
    labelAr: REGISTRY_CATEGORY_LABELS[id].ar,
    labelEn: REGISTRY_CATEGORY_LABELS[id].en,
  })),
];

const ATLAS_REVIEW_WARNING_AR =
  'هذا الأطلس قيد المراجعة العلمية، وبعض الروابط مرشحة وليست معتمدة بعد.';
const ATLAS_REVIEW_WARNING_EN =
  'This atlas is under scholarly review. Some links are candidates and are not approved yet.';

const REGISTRY_MISSING_AR =
  'تعذر تحميل سجل القصص. يرجى تشغيل مولد سجل القصص.';
const REGISTRY_MISSING_EN =
  'Story registry could not be loaded. Please run the story registry generator.';

export function StoryAtlasPage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [searchParams, setSearchParams] = useSearchParams();

  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  // Selected subcategory filter — either "all", a parent group ("animal"),
  // or a full "group:tag" string ("animal:cow"). Synced with the URL via
  // ?subcategory= so StoryDetailPage chips can deep-link into the atlas.
  const [selectedSubcategory, setSelectedSubcategory] = useState<string>(
    searchParams.get('subcategory') || 'all',
  );
  // People filter — either "all", a role ("prophet" / "antagonist"), or
  // a canonical personId ("person_firawn" / "prophet_musa").
  const [selectedPerson, setSelectedPerson] = useState<string>(
    searchParams.get('person') || 'all',
  );

  useEffect(() => {
    const next = new URLSearchParams(searchParams);
    if (selectedSubcategory === 'all') {
      next.delete('subcategory');
    } else {
      next.set('subcategory', selectedSubcategory);
    }
    if (selectedPerson === 'all') {
      next.delete('person');
    } else {
      next.set('person', selectedPerson);
    }
    // Avoid pushing a new history entry if nothing changed.
    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSubcategory, selectedPerson]);

  const registry = getRegistry();
  const healthy = isRegistryHealthy();
  const subcategoryFacets = useMemo(
    () => (healthy ? getSubcategoryFacets() : []),
    [healthy],
  );
  const peopleFacets = useMemo(
    () => (healthy ? getPeopleFacets() : []),
    [healthy],
  );

  const filtered: RegistryStoryEntry[] = useMemo(() => {
    if (!healthy) return [];
    let base = getStoriesByCategory(selectedCategory);
    if (selectedSubcategory !== 'all') {
      const subSet = new Set(
        getStoriesBySubcategory(selectedSubcategory).map((s) => s.storyId),
      );
      base = base.filter((s) => subSet.has(s.storyId));
    }
    if (selectedPerson !== 'all') {
      const personSet = new Set(
        getStoriesByPerson(selectedPerson).map((s) => s.storyId),
      );
      base = base.filter((s) => personSet.has(s.storyId));
    }
    if (!searchQuery.trim()) return base;
    const matches = new Set(searchStories(searchQuery).map((s) => s.storyId));
    return base.filter((s) => matches.has(s.storyId));
  }, [selectedCategory, selectedSubcategory, selectedPerson, searchQuery, healthy]);

  const counts = useMemo(() => {
    const byCategory: Record<string, number> = {};
    for (const s of registry.stories) {
      byCategory[s.category] = (byCategory[s.category] || 0) + 1;
    }
    return byCategory;
  }, [registry.stories]);

  return (
    <div
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <div className="mb-6">
        <div className={clsx('flex items-center gap-3 mb-2', isArabic && 'flex-row-reverse')}>
          <Map className="w-8 h-8 text-primary-600" />
          <h1 className={clsx('text-3xl font-bold text-gray-900', isArabic && 'font-arabic')}>
            {isArabic ? 'أطلس القصص القرآنية' : 'Quran Story Atlas'}
          </h1>
        </div>
        <p className={clsx('text-gray-600', isArabic && 'font-arabic text-right')}>
          {isArabic
            ? 'استكشف قصص القرآن الكريم مرتبة حسب الشخصيات والأماكن والأزمنة'
            : 'Explore Quran stories by people, places, timelines, and themes'}
        </p>
      </div>

      {/* Review warning */}
      <div
        className="mb-6 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"
        role="status"
      >
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <p className={clsx(isArabic && 'font-arabic text-right flex-1')}>
          {isArabic ? ATLAS_REVIEW_WARNING_AR : ATLAS_REVIEW_WARNING_EN}
        </p>
      </div>

      {/* Coverage dashboard */}
      <CoverageDashboard isArabic={isArabic} />

      {!healthy ? (
        <div className="text-center py-12 card border border-red-200 bg-red-50">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className={clsx('text-red-800 font-medium', isArabic && 'font-arabic')}>
            {isArabic ? REGISTRY_MISSING_AR : REGISTRY_MISSING_EN}
          </p>
          <p className="text-xs text-red-700 mt-2 font-mono">
            npx tsx scripts/build-quran-story-registry.ts
          </p>
        </div>
      ) : (
        <>
          {/* Search */}
          <div className="mb-6">
            <div className="relative max-w-md">
              <Search
                className={clsx(
                  'absolute top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400',
                  isArabic ? 'right-3' : 'left-3',
                )}
              />
              <input
                type="text"
                placeholder={
                  isArabic
                    ? 'بحث (عنوان، نبي، كيان، سورة، معرّف القصة)…'
                    : 'Search (title, prophet, entity, surah, story id)…'
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={clsx(
                  'w-full py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                  isArabic ? 'pr-10 pl-4' : 'pl-10 pr-4',
                )}
                dir={isArabic ? 'rtl' : 'ltr'}
              />
            </div>
          </div>

          {/* Category filters */}
          <div className="flex flex-wrap gap-2 mb-6">
            {CATEGORY_FILTERS.map((cat) => {
              const count = cat.id === 'all' ? registry.stories.length : counts[cat.id] || 0;
              const isSelected = selectedCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={clsx(
                    'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors',
                    isSelected
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
                  )}
                >
                  {isArabic ? cat.labelAr : cat.labelEn}
                  <span
                    className={clsx(
                      'text-xs px-1.5 py-0.5 rounded-full',
                      isSelected ? 'bg-white/20' : 'bg-gray-200 text-gray-500',
                    )}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Subcategory facets */}
          <SubcategoryFacets
            facets={subcategoryFacets}
            selected={selectedSubcategory}
            onSelect={setSelectedSubcategory}
            isArabic={isArabic}
          />

          {/* People facets */}
          <PeopleFacets
            facets={peopleFacets}
            selected={selectedPerson}
            onSelect={setSelectedPerson}
            isArabic={isArabic}
          />

          {/* Counts */}
          <div className="mb-4 flex flex-wrap items-center gap-4 text-sm text-gray-500">
            <span>
              {isArabic
                ? `${filtered.length} من ${registry.stories.length} قصة`
                : `${filtered.length} of ${registry.stories.length} stories`}
            </span>
            <span className="text-gray-300">·</span>
            <span>
              {isArabic
                ? `${registry.coverage.generatedCandidates} مرشحة`
                : `${registry.coverage.generatedCandidates} candidates`}
            </span>
            <span className="text-gray-300">·</span>
            <span>
              {isArabic
                ? `${registry.coverage.missingMetadataCount} ناقصة البيانات`
                : `${registry.coverage.missingMetadataCount} missing metadata`}
            </span>
          </div>

          {/* Results grid */}
          {filtered.length === 0 ? (
            <div className="text-center py-12 card">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className={clsx('text-gray-500', isArabic && 'font-arabic')}>
                {isArabic
                  ? 'لا توجد نتائج مطابقة للبحث الحالي'
                  : 'No stories match the current filters'}
              </p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filtered.map((story) => (
                <RegistryStoryCard key={story.storyId} story={story} isArabic={isArabic} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function CoverageDashboard({ isArabic }: { isArabic: boolean }) {
  const registry = getRegistry();
  const c = registry.coverage;

  const stats = [
    {
      labelAr: 'إجمالي القصص',
      labelEn: 'Total stories',
      value: c.totalStories,
      icon: Book,
    },
    {
      labelAr: 'قصص محرّرة',
      labelEn: 'Authored',
      value: c.authoredStories,
      icon: Layers,
    },
    {
      labelAr: 'صفحات الأنبياء',
      labelEn: 'Prophet profiles',
      value: c.prophetProfiles,
      icon: Users,
    },
    {
      labelAr: 'مرشحة',
      labelEn: 'Candidates',
      value: c.generatedCandidates,
      icon: Layers,
    },
    {
      labelAr: 'سور مغطاة',
      labelEn: 'Surahs covered',
      value: c.surahsCovered,
      icon: Book,
    },
    {
      labelAr: 'أنبياء مغطاة',
      labelEn: 'Prophets covered',
      value: c.prophetsCovered,
      icon: Users,
    },
    {
      labelAr: 'مدى آيات',
      labelEn: 'Ayah ranges',
      value: c.ayahRangesLinked,
      icon: Book,
    },
    {
      labelAr: 'بانتظار المراجعة',
      labelEn: 'Review pending',
      value: c.reviewPendingCount,
      icon: AlertTriangle,
    },
  ];

  return (
    <div className="mb-6 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
      {stats.map((s) => (
        <div
          key={s.labelEn}
          className="rounded-lg border border-gray-200 bg-white p-3 text-center"
        >
          <s.icon className="w-4 h-4 mx-auto mb-1 text-primary-600" />
          <div className="text-lg font-semibold text-gray-900">{s.value}</div>
          <div
            className={clsx(
              'text-xs text-gray-500 leading-tight',
              isArabic && 'font-arabic',
            )}
          >
            {isArabic ? s.labelAr : s.labelEn}
          </div>
        </div>
      ))}
    </div>
  );
}

function RegistryStoryCard({
  story,
  isArabic,
}: {
  story: RegistryStoryEntry;
  isArabic: boolean;
}) {
  const [showConnections, setShowConnections] = useState(false);
  const title = isArabic ? story.titleArabic : story.titleEnglish;
  const catLabel = REGISTRY_CATEGORY_LABELS[story.category];
  const needsReview = story.reviewStatus !== 'verified';
  const sourceLabel =
    story.sourceType === 'authored_story'
      ? isArabic ? 'قصة محرّرة' : 'Authored'
      : story.sourceType === 'prophet_story_page'
        ? isArabic ? 'صفحة نبي' : 'Prophet page'
        : story.sourceType === 'entity_story_cluster'
          ? isArabic ? 'عنقود كيان' : 'Entity cluster'
          : isArabic ? 'مرشحة' : 'Candidate';

  const detail = story.detailRoute || `/stories/${story.storyId}`;

  return (
    <div className="card hover:shadow-lg transition-all group flex flex-col h-full" dir={isArabic ? 'rtl' : 'ltr'}>
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
          <Book className="w-5 h-5 text-primary-600" />
        </div>
        <div className={clsx('flex gap-1 flex-wrap', isArabic ? 'justify-start' : 'justify-end')}>
          <span className="text-xs font-medium text-primary-700 bg-primary-50 px-2 py-1 rounded">
            {isArabic ? catLabel.ar : catLabel.en}
          </span>
          <span className="text-xs font-medium text-gray-600 bg-gray-100 px-2 py-1 rounded">
            {sourceLabel}
          </span>
          {needsReview && (
            <span className="text-xs font-medium text-amber-700 bg-amber-50 px-2 py-1 rounded">
              {isArabic ? 'تحتاج مراجعة' : 'Needs review'}
            </span>
          )}
        </div>
      </div>

      <h3
        className={clsx(
          'text-lg font-semibold mb-2 group-hover:text-primary-600 transition-colors',
          isArabic && 'font-arabic text-right',
        )}
      >
        {title}
      </h3>

      <div className="text-xs text-gray-500 mb-3 flex flex-wrap gap-3">
        <span>
          {isArabic
            ? `${story.ayahRangeCount} مقاطع آيات`
            : `${story.ayahRangeCount} ayah ranges`}
        </span>
        <span>
          {isArabic
            ? `${story.surahCount} سور`
            : `${story.surahCount} surahs`}
        </span>
        <span>
          {isArabic
            ? `${story.segmentCount} مقطع`
            : `${story.segmentCount} segments`}
        </span>
      </div>

      {(story.relatedProphets.length > 0 || story.relatedEntities.length > 0 || story.relatedTopics.length > 0) && (
        <div className="text-xs text-gray-500 mb-3 flex flex-wrap gap-3">
          {story.relatedProphets.length > 0 && (
            <span>
              {isArabic
                ? `${story.relatedProphets.length} نبي`
                : `${story.relatedProphets.length} prophets`}
            </span>
          )}
          {story.relatedEntities.length > 0 && (
            <span>
              {isArabic
                ? `${story.relatedEntities.length} كيان`
                : `${story.relatedEntities.length} entities`}
            </span>
          )}
          {story.relatedTopics.length > 0 && (
            <span>
              {isArabic
                ? `${story.relatedTopics.length} موضوع`
                : `${story.relatedTopics.length} topics`}
            </span>
          )}
        </div>
      )}

      {story.subcategories && story.subcategories.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1">
          {story.subcategories.slice(0, 6).map((sc) => {
            const label = getSubcategoryLabel(sc);
            const group = sc.split(':')[0] as SubcategoryGroup;
            const groupLabel = SUBCATEGORY_GROUP_LABELS[group];
            const title = isArabic
              ? `${groupLabel?.ar ?? group}: ${label.ar}`
              : `${groupLabel?.en ?? group}: ${label.en}`;
            return (
              <span
                key={sc}
                title={title}
                className="inline-flex items-center text-[11px] font-medium text-emerald-800 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded"
              >
                {isArabic ? label.ar : label.en}
              </span>
            );
          })}
          {story.subcategories.length > 6 && (
            <span className="text-[11px] text-gray-500">
              +{story.subcategories.length - 6}
            </span>
          )}
        </div>
      )}

      {story.peopleIds && story.peopleIds.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {story.peopleIds.slice(0, 5).map((pid) => {
            const p = getPerson(pid);
            if (!p) return null;
            const roleLabel = PERSON_ROLE_LABELS[p.role];
            const title = isArabic
              ? `${roleLabel?.ar ?? p.role}: ${p.nameArabic}`
              : `${roleLabel?.en ?? p.role}: ${p.nameEnglish}`;
            const tone =
              p.role === 'prophet'
                ? 'text-indigo-800 bg-indigo-50 border-indigo-200'
                : p.role === 'antagonist'
                  ? 'text-rose-800 bg-rose-50 border-rose-200'
                  : 'text-sky-800 bg-sky-50 border-sky-200';
            return (
              <span
                key={pid}
                title={title}
                className={clsx(
                  'inline-flex items-center text-[11px] font-medium border px-1.5 py-0.5 rounded',
                  tone,
                )}
              >
                {isArabic ? p.nameArabic : p.nameEnglish}
              </span>
            );
          })}
          {story.peopleIds.length > 5 && (
            <span className="text-[11px] text-gray-500">
              +{story.peopleIds.length - 5}
            </span>
          )}
        </div>
      )}

      {story.warnings.length > 0 && (
        <div className="text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded mb-3" dir={isArabic ? 'rtl' : 'ltr'}>
          {story.warnings[0]}
        </div>
      )}

      <div className="mt-auto pt-3 flex items-center justify-between border-t border-gray-100">
        <Link
          to={detail}
          className={clsx(
            'flex items-center text-primary-600 text-sm font-medium hover:underline',
            isArabic && 'flex-row-reverse',
          )}
        >
          {isArabic ? 'فتح القصة' : 'Open story'}
          <ArrowRight
            className={clsx('w-4 h-4 ms-1 transition-transform', isArabic ? 'rotate-180' : '')}
          />
        </Link>
        <button
          type="button"
          onClick={() => setShowConnections(s => !s)}
          aria-expanded={showConnections}
          className={clsx(
            'flex items-center gap-1 text-xs text-gray-600 hover:text-primary-600 transition-colors',
            isArabic && 'flex-row-reverse font-arabic',
          )}
        >
          <Network className="w-3 h-3" />
          {isArabic ? 'الروابط' : 'Connections'}
          {showConnections
            ? <ChevronUp className="w-3 h-3" />
            : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {showConnections && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <ConnectedStoriesPanel
            storyId={story.storyId}
            language={isArabic ? 'ar' : 'en'}
          />
        </div>
      )}
    </div>
  );
}

function SubcategoryFacets({
  facets,
  selected,
  onSelect,
  isArabic,
}: {
  facets: ReturnType<typeof getSubcategoryFacets>;
  selected: string;
  onSelect: (next: string) => void;
  isArabic: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  if (facets.length === 0) return null;

  return (
    <div className="mb-6 rounded-lg border border-emerald-100 bg-emerald-50/40 p-3">
      <div className={clsx('mb-2 flex items-center justify-between gap-2', isArabic && 'flex-row-reverse')}>
        <div className={clsx('text-sm font-semibold text-emerald-900', isArabic && 'font-arabic')}>
          {isArabic ? 'تصنيفات فرعية' : 'Subcategories'}
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-emerald-700 hover:underline"
        >
          {expanded
            ? (isArabic ? 'إخفاء' : 'Hide')
            : (isArabic ? 'عرض الكل' : 'Show all')}
        </button>
      </div>
      <div className="space-y-2">
        <div className={clsx('flex flex-wrap gap-1.5', isArabic && 'justify-end')}>
          <button
            type="button"
            onClick={() => onSelect('all')}
            className={clsx(
              'text-xs font-medium px-2 py-1 rounded-full',
              selected === 'all'
                ? 'bg-emerald-700 text-white'
                : 'bg-white text-emerald-800 border border-emerald-200 hover:bg-emerald-100',
            )}
          >
            {isArabic ? 'الكل' : 'All'}
          </button>
          {facets.map((f) => {
            const label = SUBCATEGORY_GROUP_LABELS[f.group];
            const isSelectedGroup = selected === f.group;
            return (
              <button
                key={f.group}
                type="button"
                onClick={() => onSelect(isSelectedGroup ? 'all' : f.group)}
                className={clsx(
                  'text-xs font-medium px-2 py-1 rounded-full inline-flex items-center gap-1',
                  isSelectedGroup
                    ? 'bg-emerald-700 text-white'
                    : 'bg-white text-emerald-800 border border-emerald-200 hover:bg-emerald-100',
                )}
                title={isArabic ? `${f.totalStoryCount} قصة` : `${f.totalStoryCount} stories`}
              >
                <span>{isArabic ? label.ar : label.en}</span>
                <span
                  className={clsx(
                    'text-[10px] px-1 rounded-full',
                    isSelectedGroup ? 'bg-white/20' : 'bg-emerald-100 text-emerald-900',
                  )}
                >
                  {f.totalStoryCount}
                </span>
              </button>
            );
          })}
        </div>
        {expanded && (
          <div className="pt-2 mt-2 border-t border-emerald-100">
            {facets.map((f) => (
              <div key={f.group} className="mb-2">
                <div
                  className={clsx(
                    'text-[11px] uppercase tracking-wide text-emerald-700 mb-1',
                    isArabic && 'text-right font-arabic',
                  )}
                >
                  {isArabic ? SUBCATEGORY_GROUP_LABELS[f.group].ar : SUBCATEGORY_GROUP_LABELS[f.group].en}
                </div>
                <div className={clsx('flex flex-wrap gap-1', isArabic && 'justify-end')}>
                  {f.tags.map((t) => {
                    const isSelectedTag = selected === t.tag;
                    const tagLabel = getSubcategoryLabel(t.tag);
                    return (
                      <button
                        key={t.tag}
                        type="button"
                        onClick={() => onSelect(isSelectedTag ? 'all' : t.tag)}
                        className={clsx(
                          'text-[11px] px-1.5 py-0.5 rounded-full inline-flex items-center gap-1',
                          isSelectedTag
                            ? 'bg-emerald-700 text-white'
                            : 'bg-white text-emerald-800 border border-emerald-200 hover:bg-emerald-100',
                        )}
                      >
                        <span>{isArabic ? tagLabel.ar : tagLabel.en}</span>
                        <span
                          className={clsx(
                            'text-[10px] px-1 rounded-full',
                            isSelectedTag ? 'bg-white/20' : 'bg-emerald-100 text-emerald-900',
                          )}
                        >
                          {t.storyCount}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PeopleFacets({
  facets,
  selected,
  onSelect,
  isArabic,
}: {
  facets: ReturnType<typeof getPeopleFacets>;
  selected: string;
  onSelect: (next: string) => void;
  isArabic: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  if (facets.length === 0) return null;

  return (
    <div className="mb-6 rounded-lg border border-indigo-100 bg-indigo-50/40 p-3">
      <div className={clsx('mb-2 flex items-center justify-between gap-2', isArabic && 'flex-row-reverse')}>
        <div className={clsx('text-sm font-semibold text-indigo-900', isArabic && 'font-arabic')}>
          {isArabic ? 'الشخصيات' : 'People'}
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-indigo-700 hover:underline"
        >
          {expanded
            ? (isArabic ? 'إخفاء' : 'Hide')
            : (isArabic ? 'عرض الكل' : 'Show all')}
        </button>
      </div>
      <div className="space-y-2">
        {/* Top-level role chips — always visible */}
        <div className={clsx('flex flex-wrap gap-1.5', isArabic && 'justify-end')}>
          <button
            type="button"
            onClick={() => onSelect('all')}
            className={clsx(
              'text-xs font-medium px-2 py-1 rounded-full',
              selected === 'all'
                ? 'bg-indigo-700 text-white'
                : 'bg-white text-indigo-800 border border-indigo-200 hover:bg-indigo-100',
            )}
          >
            {isArabic ? 'الكل' : 'All'}
          </button>
          {facets.map((f) => {
            const label = PERSON_ROLE_LABELS[f.role];
            const isSelectedRole = selected === f.role;
            return (
              <button
                key={f.role}
                type="button"
                onClick={() => onSelect(isSelectedRole ? 'all' : f.role)}
                className={clsx(
                  'text-xs font-medium px-2 py-1 rounded-full inline-flex items-center gap-1',
                  isSelectedRole
                    ? 'bg-indigo-700 text-white'
                    : 'bg-white text-indigo-800 border border-indigo-200 hover:bg-indigo-100',
                )}
                title={isArabic ? `${f.totalStoryCount} قصة` : `${f.totalStoryCount} stories`}
              >
                <span>{isArabic ? label.ar : label.en}</span>
                <span
                  className={clsx(
                    'text-[10px] px-1 rounded-full',
                    isSelectedRole ? 'bg-white/20' : 'bg-indigo-100 text-indigo-900',
                  )}
                >
                  {f.totalStoryCount}
                </span>
              </button>
            );
          })}
        </div>

        {/* Per-person chips — expanded view */}
        {expanded && (
          <div className="pt-2 mt-2 border-t border-indigo-100">
            {facets.map((f) => (
              <div key={f.role} className="mb-3">
                <div
                  className={clsx(
                    'text-[11px] uppercase tracking-wide text-indigo-700 mb-1',
                    isArabic && 'text-right font-arabic',
                  )}
                >
                  {isArabic ? PERSON_ROLE_LABELS[f.role].ar : PERSON_ROLE_LABELS[f.role].en}
                </div>
                <div className={clsx('flex flex-wrap gap-1', isArabic && 'justify-end')}>
                  {f.people.map((p) => {
                    const isSelectedPerson = selected === p.personId;
                    return (
                      <button
                        key={p.personId}
                        type="button"
                        onClick={() => onSelect(isSelectedPerson ? 'all' : p.personId)}
                        className={clsx(
                          'text-[11px] px-1.5 py-0.5 rounded-full inline-flex items-center gap-1',
                          isSelectedPerson
                            ? 'bg-indigo-700 text-white'
                            : 'bg-white text-indigo-800 border border-indigo-200 hover:bg-indigo-100',
                        )}
                      >
                        <span>{isArabic ? p.nameArabic : p.nameEnglish}</span>
                        <span
                          className={clsx(
                            'text-[10px] px-1 rounded-full',
                            isSelectedPerson ? 'bg-white/20' : 'bg-indigo-100 text-indigo-900',
                          )}
                        >
                          {p.storyCount}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
