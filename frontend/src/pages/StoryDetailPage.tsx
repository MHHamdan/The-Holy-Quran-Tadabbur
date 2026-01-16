import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Book, Network, List, Users, Tag, ChevronDown, ChevronUp, ExternalLink, BarChart3, Lightbulb } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t, translateCategory, translateTheme, translateFigure, translateAspect } from '../i18n/translations';
import { storiesApi, quranApi, StoryDetail, StoryGraph, Verse, StorySegment } from '../lib/api';
import { StoryGraphView } from '../components/stories/StoryGraphView';
import { ThematicFlow } from '../components/stories/ThematicFlow';
import { NarrativeInsights } from '../components/stories/NarrativeInsights';
import { RelatedStories } from '../components/stories/RelatedStories';
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
  const [segmentVerses, setSegmentVerses] = useState<SegmentVerses>({});
  const [expandedSegments, setExpandedSegments] = useState<Set<string>>(new Set());
  const [loadingVerses, setLoadingVerses] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (storyId) {
      loadStory();
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link */}
      <Link
        to="/stories"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
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
              <h1 className="text-2xl font-bold">{name}</h1>
              <span className="text-sm bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {translateCategory(story.category, language)}
              </span>
            </div>
            {summary && <p className="text-gray-600">{summary}</p>}
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
      </div>

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
          {graphData && <StoryGraphView graph={graphData} language={language} />}
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
