import { useState, useEffect, lazy, Suspense } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Book, Network, List, Users, Tag, ChevronDown, ChevronUp, ExternalLink, BarChart3, Lightbulb, Baby, GraduationCap, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t, translateCategory, translateTheme, translateFigure, translateAspect } from '../i18n/translations';
import { storiesApi, quranApi, StoryDetail, StoryGraph, Verse, StorySegment } from '../lib/api';
import { ThematicFlow } from '../components/stories/ThematicFlow';
import { NarrativeInsights } from '../components/stories/NarrativeInsights';
import { RelatedStories } from '../components/stories/RelatedStories';
import type { AudienceLevel, QuranStory } from '../types/quranStory';

const StoryGraphView = lazy(() =>
  import('../components/stories/StoryGraphView').then(m => ({ default: m.StoryGraphView }))
);
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { getStoryApprovalStatus } from '../utils/reviewStatus';
import { getRegistry } from '../utils/storyRegistryAdapter';
import { SUBCATEGORY_GROUP_LABELS, getSubcategoryLabel, type SubcategoryGroup } from '../types/quranStoryRegistry';
import {
  StoryOverviewCard,
  StorySummaryCard,
  KidsQuizWidget,
  AdultsReflectionPanel,
  GroupedSegmentList,
} from '../components/stories/StoryReadingPanel';
import clsx from 'clsx';

type ViewMode = 'list' | 'graph' | 'themes' | 'insights';

// Cache for fetched verses
interface SegmentVerses {
  [segmentId: string]: Verse[];
}

export function StoryDetailPage() {
  const { storyId } = useParams<{ storyId: string }>();
  const { language } = useLanguageStore();
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [graphData, setGraphData] = useState<StoryGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [audienceLevel, setAudienceLevel] = useState<AudienceLevel>('adults');
  const [segmentVerses, setSegmentVerses] = useState<SegmentVerses>({});
  const [expandedSegments, setExpandedSegments] = useState<Set<string>>(new Set());
  const [loadingVerses, setLoadingVerses] = useState<Set<string>>(new Set());

  // Rich story data from local seed (lazy-loaded)
  const [richStory, setRichStory] = useState<QuranStory | undefined>(undefined);

  useEffect(() => {
    if (storyId) {
      loadStory();
      import('../data/quranStories').then(m => setRichStory(m.getStoryById(storyId)));
    }
  }, [storyId, language]);

  async function loadStory() {
    setLoading(true);
    try {
      const [storyRes, graphRes] = await Promise.all([
        storiesApi.getStory(storyId!),
        storiesApi.getStoryGraph(storyId!, language),
      ]);
      setStory(storyRes.data);
      setGraphData(graphRes.data);
    } catch (error) {
      console.error('Failed to load story:', error);
    } finally {
      setLoading(false);
    }
  }

  async function loadVersesForSegment(segment: StorySegment) {
    if (segmentVerses[segment.id] || loadingVerses.has(segment.id)) return;

    setLoadingVerses(prev => new Set(prev).add(segment.id));

    try {
      const res = await quranApi.getVerseRange(
        segment.sura_no,
        segment.aya_start,
        segment.aya_end
      );
      setSegmentVerses(prev => ({ ...prev, [segment.id]: res.data }));
    } catch (error) {
      console.error('Failed to load verses:', error);
    } finally {
      setLoadingVerses(prev => {
        const next = new Set(prev);
        next.delete(segment.id);
        return next;
      });
    }
  }

  function toggleSegment(segment: StorySegment) {
    const newExpanded = new Set(expandedSegments);
    if (newExpanded.has(segment.id)) {
      newExpanded.delete(segment.id);
    } else {
      newExpanded.add(segment.id);
      loadVersesForSegment(segment);
    }
    setExpandedSegments(newExpanded);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!story) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-gray-500">
          {language === 'ar' ? 'القصة غير موجودة' : 'Story not found'}
        </p>
        <Link to="/stories" className="text-primary-600 hover:underline mt-4 inline-block">
          {language === 'ar' ? 'العودة للقصص' : 'Back to Stories'}
        </Link>
      </div>
    );
  }

  const name = language === 'ar' ? story.name_ar : story.name_en;
  const summary = language === 'ar' ? story.summary_ar : story.summary_en;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Back Link */}
      <Link
        to="/stories"
        className={clsx('inline-flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-6', language === 'ar' && 'font-arabic')}
      >
        <ArrowLeft className={clsx('w-4 h-4', language === 'ar' && 'rotate-180')} />
        {language === 'ar' ? 'العودة للقصص' : 'Back to Stories'}
      </Link>

      {/* Header */}
      <div className="card mb-8">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <Book className="w-7 h-7 text-primary-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className={clsx('text-2xl font-bold', language === 'ar' && 'font-arabic')}>{name}</h1>
              <span className="text-sm bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {translateCategory(story.category, language)}
              </span>
            </div>
            {summary && <p className={clsx('text-gray-600', language === 'ar' && 'font-arabic')}>{summary}</p>}
          </div>
        </div>

        {/* Meta Info */}
        <div className="flex flex-wrap gap-6 text-sm">
          {story.main_figures && story.main_figures.length > 0 && (
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">
                {story.main_figures.map(f => translateFigure(f, language)).join('، ')}
              </span>
            </div>
          )}
          {story.themes && story.themes.length > 0 && (
            <div className="flex items-center gap-2">
              <Tag className="w-4 h-4 text-gray-400" />
              <div className="flex gap-1 flex-wrap">
                {story.themes.map((theme) => (
                  <span
                    key={theme}
                    className="bg-primary-50 text-primary-700 px-2 py-0.5 rounded text-xs"
                  >
                    {translateTheme(theme, language)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <StorySubcategoryStrip storyId={storyId!} language={language} />
      </div>

      {/* Audience Level Toggle — shown when rich story data is available */}
      {richStory && (
        <div className="card mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h3 className={clsx('font-semibold text-gray-900 mb-1', language === 'ar' && 'font-arabic')}>
                {language === 'ar' ? 'مستوى العرض' : 'Reading Level'}
              </h3>
              <p className={clsx('text-sm text-gray-500', language === 'ar' && 'font-arabic')}>
                {language === 'ar'
                  ? 'اختر المستوى المناسب لك'
                  : 'Choose the level that suits you'}
              </p>
            </div>
            <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
              <button
                onClick={() => setAudienceLevel('kids')}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all',
                  audienceLevel === 'kids'
                    ? 'bg-amber-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                <Baby className="w-4 h-4" />
                {language === 'ar' ? 'للأطفال' : 'Kids'}
              </button>
              <button
                onClick={() => setAudienceLevel('adults')}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all',
                  audienceLevel === 'adults'
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                <GraduationCap className="w-4 h-4" />
                {language === 'ar' ? 'للكبار' : 'Adults'}
              </button>
            </div>
          </div>

          {/* Level description */}
          <div className={clsx(
            'mt-4 p-3 rounded-lg text-sm',
            audienceLevel === 'kids' ? 'bg-amber-50 text-amber-800' : 'bg-primary-50 text-primary-800'
          )}>
            {audienceLevel === 'kids' ? (
              language === 'ar'
                ? 'عرض مبسط للأطفال: لغة سهلة، دروس واضحة، مناسب لجميع الأعمار.'
                : 'Simple presentation for children: easy language, clear lessons, appropriate for all ages.'
            ) : (
              language === 'ar'
                ? 'عرض متعمق للكبار: سياق عبر السور، مصادر التفسير، الدروس والمواضيع.'
                : 'In-depth presentation for adults: cross-surah context, tafsir sources, lessons and themes.'
            )}
          </div>

          {/* Needs review notice */}
          {richStory.reliabilityLevel === 'supporting' && (
            <div className="mt-3 flex items-start gap-2 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
              <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-yellow-800">
                {language === 'ar'
                  ? 'هذه الشروح تحتاج إلى مراجعة علمية قبل اعتمادها. المراجع القرآنية موثقة والتفاصيل قيد المراجعة.'
                  : 'These explanations require scholarly review before full approval. Quranic references are documented; details are pending verification.'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Rich story reading panel — shown when first-batch data is available */}
      {richStory && viewMode === 'list' && (
        <div className="space-y-4 mb-8">

          {/* Story overview intro card */}
          <StoryOverviewCard story={richStory} level={audienceLevel} language={language} />

          {/* Segment header with aggregate approval status */}
          {(() => {
            const segIds = richStory.storySegments.map(s => s.segmentId);
            const storyAggregate = getStoryApprovalStatus(segIds);
            return (
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className={clsx('text-lg font-semibold text-gray-900', language === 'ar' && 'font-arabic')}>
                  {language === 'ar' ? 'مقاطع القصة' : 'Story Segments'}
                  <span className="text-sm font-normal text-gray-500 ms-2">
                    ({richStory.storySegments.length})
                  </span>
                </h2>
                {storyAggregate.status === 'approved' && (
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-green-100 text-green-700 border border-green-200">
                    <CheckCircle className="w-3.5 h-3.5" />
                    {language === 'ar' ? 'جميع المقاطع معتمدة' : 'All segments approved'}
                  </span>
                )}
                {storyAggregate.status === 'partially_reviewed' && (
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
                    <Clock className="w-3.5 h-3.5" />
                    {storyAggregate.approvedCount}/{storyAggregate.totalCount}{' '}
                    {language === 'ar' ? 'مقاطع معتمدة' : 'segments approved'}
                  </span>
                )}
              </div>
            );
          })()}

          {/* Grouped segments by section type */}
          <GroupedSegmentList story={richStory} level={audienceLevel} language={language} />

          {/* Story summary card */}
          <StorySummaryCard story={richStory} level={audienceLevel} language={language} />

          {/* Audience-specific enrichment */}
          {audienceLevel === 'kids' && (
            <KidsQuizWidget story={richStory} language={language} />
          )}
          {audienceLevel === 'adults' && (
            <AdultsReflectionPanel story={richStory} language={language} />
          )}


          {/* Rich related stories with evidence references */}
          {richStory.relatedStories.length > 0 && (
            <div className="card border border-amber-200 bg-amber-50/30">
              <div className="flex items-center gap-2 mb-3">
                <Network className="w-4 h-4 text-primary-600" />
                <h3 className="text-sm font-semibold text-gray-800">
                  {language === 'ar' ? 'القصص ذات الصلة' : 'Related Stories'}
                </h3>
                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full border border-yellow-200 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {language === 'ar' ? 'مراجعة معلقة' : 'Pending Review'}
                </span>
              </div>
              <p className="text-xs text-amber-700 mb-3 flex items-start gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                {language === 'ar'
                  ? 'صلات القصص لم تُراجع علمياً بعد. الأدلة القرآنية الموثقة مذكورة لكل صلة.'
                  : 'Story connections have not yet been reviewed. Documented Quranic references are shown for each connection.'}
              </p>
              <div className="space-y-3">
                {richStory.relatedStories.map((related) => (
                  <div key={related.storyId} className="p-3 rounded-lg bg-white border border-gray-200">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <Link
                        to={`/stories/${related.storyId}`}
                        className="text-sm font-medium text-primary-700 hover:text-primary-900 transition-colors"
                      >
                        {related.storyId}
                      </Link>
                      <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                        {related.relationType.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mb-2 leading-relaxed" dir={language === 'ar' ? 'rtl' : 'ltr'}>
                      {language === 'ar' ? related.explanationArabic : related.explanationEnglish}
                    </p>
                    {related.evidenceReferences.length > 0 ? (
                      <div className="flex flex-wrap gap-1 items-center">
                        <span className="text-xs text-gray-500">
                          {language === 'ar' ? 'الأدلة:' : 'Evidence:'}
                        </span>
                        {related.evidenceReferences.map((ev, idx) => (
                          <Link
                            key={idx}
                            to={`/quran/${ev.surahNumber}?aya=${ev.ayahStart}`}
                            className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full hover:bg-primary-100 transition-colors"
                          >
                            {ev.surahNumber}:{ev.ayahStart}{ev.ayahEnd !== ev.ayahStart ? `–${ev.ayahEnd}` : ''}
                          </Link>
                        ))}
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-xs text-orange-600">
                        <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                        {language === 'ar' ? 'لا توجد أدلة قرآنية محددة لهذه الصلة' : 'No Quranic evidence references for this connection'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sources section */}
          <div className="card bg-gray-50">
            <h3 className="font-semibold text-gray-700 mb-2 text-sm">
              {language === 'ar' ? 'المصادر المرجعية' : 'Reference Sources'}
            </h3>
            <div className="flex flex-wrap gap-2">
              {richStory.sourceIds.map((sid) => (
                <span key={sid} className="text-xs bg-white border border-gray-200 text-gray-600 px-2 py-1 rounded">
                  {sid}
                </span>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {language === 'ar'
                ? 'جميع التفاسير المذكورة تفاسير سنية معتمدة. الشروح بحاجة لمراجعة قبل النشر الكامل.'
                : 'All listed tafsirs are approved Sunni sources. Explanations require review before full production release.'}
            </p>
          </div>
        </div>
      )}

      {/* View Toggle */}
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-lg font-semibold flex-1">
          {t('story_segments', language)} ({story.segments.length})
        </h2>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('list')}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              viewMode === 'list'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <List className="w-4 h-4" />
            {t('view_list', language)}
          </button>
          <button
            onClick={() => setViewMode('graph')}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              viewMode === 'graph'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Network className="w-4 h-4" />
            {t('view_graph', language)}
          </button>
          <button
            onClick={() => setViewMode('themes')}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              viewMode === 'themes'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <BarChart3 className="w-4 h-4" />
            {language === 'ar' ? 'المواضيع' : 'Themes'}
          </button>
          <button
            onClick={() => setViewMode('insights')}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              viewMode === 'insights'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Lightbulb className="w-4 h-4" />
            {language === 'ar' ? 'تحليل' : 'Insights'}
          </button>
        </div>
      </div>

      {/* Content */}
      {viewMode === 'list' ? (
        <div className="space-y-4">
          {story.segments
            .sort((a, b) => a.narrative_order - b.narrative_order)
            .map((segment) => {
              const segSummary =
                language === 'ar' ? segment.summary_ar : segment.summary_en;

              const isExpanded = expandedSegments.has(segment.id);
              const isLoading = loadingVerses.has(segment.id);
              const verses = segmentVerses[segment.id];

              return (
                <div key={segment.id} className="card">
                  <button
                    onClick={() => toggleSegment(segment)}
                    className="w-full text-start"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                        {segment.narrative_order}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-medium">
                            {segment.verse_reference}
                          </span>
                          {segment.aspect && (
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                              {translateAspect(segment.aspect, language)}
                            </span>
                          )}
                          <span className="ms-auto text-gray-400">
                            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                          </span>
                        </div>
                        {segSummary && (
                          <p className="text-gray-600 text-sm">{segSummary}</p>
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Expanded Verse Content */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      {isLoading ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="animate-spin w-6 h-6 border-3 border-primary-600 border-t-transparent rounded-full" />
                        </div>
                      ) : verses && verses.length > 0 ? (
                        <div className="space-y-4">
                          {/* Surah Header */}
                          <div className="flex items-center justify-between bg-primary-50 rounded-lg px-4 py-2">
                            <div className="flex items-center gap-2">
                              <Book className="w-4 h-4 text-primary-600" />
                              <span className="font-semibold text-primary-800">
                                {language === 'ar' ? verses[0].sura_name_ar : verses[0].sura_name_en}
                              </span>
                              <span className="text-sm text-primary-600">
                                ({language === 'ar' ? `الآيات ${segment.aya_start}-${segment.aya_end}` : `Verses ${segment.aya_start}-${segment.aya_end}`})
                              </span>
                            </div>
                            <Link
                              to={`/quran/${segment.sura_no}?aya=${segment.aya_start}`}
                              className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-800 transition-colors"
                            >
                              {language === 'ar' ? 'عرض في المصحف' : 'View in Quran'}
                              <ExternalLink className="w-3.5 h-3.5" />
                            </Link>
                          </div>
                          {verses.map((verse) => (
                            <div key={verse.id} className="bg-gray-50 rounded-lg p-4">
                              <div className="flex items-start gap-3">
                                <Link
                                  to={`/quran/${verse.sura_no}?aya=${verse.aya_no}`}
                                  className="bg-primary-100 text-primary-700 text-xs font-medium px-2 py-1 rounded-full flex-shrink-0 hover:bg-primary-200 transition-colors"
                                  title={language === 'ar' ? `${verse.sura_name_ar} ${verse.aya_no}` : `${verse.sura_name_en} ${verse.aya_no}`}
                                >
                                  {verse.aya_no}
                                </Link>
                                <div className="flex-1">
                                  <p className="text-lg leading-loose font-arabic text-gray-900 mb-3" dir="rtl">
                                    {verse.text_uthmani}
                                  </p>
                                  {verse.translations && verse.translations.length > 0 && (
                                    <p className="text-sm text-gray-600 leading-relaxed">
                                      {verse.translations.find(t => t.language === (language === 'ar' ? 'ar' : 'en'))?.text ||
                                       verse.translations[0]?.text}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-center py-4">
                          {language === 'ar' ? 'لا توجد آيات متاحة' : 'No verses available'}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      ) : viewMode === 'graph' ? (
        <div className="card p-0 overflow-hidden" style={{ height: '700px' }}>
          {graphData && (
            <ErrorBoundary fallback={<div className="h-full flex items-center justify-center text-sm text-amber-600">Graph view unavailable</div>}>
              <Suspense fallback={<div className="h-full animate-pulse bg-gray-100" />}>
                <StoryGraphView graph={graphData} language={language} />
              </Suspense>
            </ErrorBoundary>
          )}
        </div>
      ) : viewMode === 'themes' ? (
        <ThematicFlow
          segments={story.segments}
          language={language}
          themes={story.themes || []}
        />
      ) : (
        <NarrativeInsights
          segments={story.segments}
          language={language}
          storyName={name}
        />
      )}

      {/* Related Stories Section */}
      <div className="mt-8">
        <RelatedStories
          storyId={storyId!}
          storyName={name}
          language={language}
        />
      </div>
    </div>
  );
}

function StorySubcategoryStrip({ storyId, language }: { storyId: string; language: 'ar' | 'en' }) {
  const isArabic = language === 'ar';
  const entry = getRegistry().stories.find((s) => s.storyId === storyId);
  if (!entry || !entry.subcategories || entry.subcategories.length === 0) return null;

  // Group tags by their parent group so the strip reads as
  // "Animals: Cow, Calf • Places: Egypt • Vices: Idolatry"
  const grouped = new Map<SubcategoryGroup, string[]>();
  for (const sc of entry.subcategories) {
    const group = sc.split(':')[0] as SubcategoryGroup;
    if (!grouped.has(group)) grouped.set(group, []);
    grouped.get(group)!.push(sc);
  }

  return (
    <div className="mt-4 pt-4 border-t border-gray-100 space-y-2" dir={isArabic ? 'rtl' : 'ltr'}>
      {Array.from(grouped.entries()).map(([group, tags]) => {
        const groupLabel = SUBCATEGORY_GROUP_LABELS[group];
        return (
          <div key={group} className={clsx('flex flex-wrap items-center gap-2', isArabic && 'justify-end')}>
            <span
              className={clsx(
                'text-[11px] font-semibold uppercase tracking-wide text-emerald-700',
                isArabic && 'font-arabic',
              )}
            >
              {isArabic ? groupLabel.ar : groupLabel.en}
            </span>
            <div className="flex flex-wrap gap-1">
              {tags.map((sc) => {
                const label = getSubcategoryLabel(sc);
                return (
                  <Link
                    key={sc}
                    to={`/story-atlas?subcategory=${encodeURIComponent(sc)}`}
                    className="inline-flex items-center text-xs font-medium text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded hover:bg-emerald-100"
                  >
                    {isArabic ? label.ar : label.en}
                  </Link>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
