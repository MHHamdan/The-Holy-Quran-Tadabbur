import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Book, Users, MapPin, Clock, Network, List, Tag, ChevronDown, ChevronUp, Database, Lightbulb } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { storyAtlasApi, kgApi, StoryClusterDetail, StoryAtlasEvent, AtlasGraphResponse, RelatedCluster, KGClusterResponse, KGStoryGraphResponse, KGEventSummary } from '../lib/api';
import { translateTag, translateFigure, Language } from '../i18n/translations';
import { StoryGraphView } from '../components/stories/StoryGraphView';
import clsx from 'clsx';

// Narrative role translations
const NARRATIVE_ROLE_TRANSLATIONS: Record<string, { ar: string; en: string }> = {
  introduction: { ar: 'مقدمة', en: 'Introduction' },
  divine_mission: { ar: 'المهمة الإلهية', en: 'Divine Mission' },
  journey_phase: { ar: 'مرحلة الرحلة', en: 'Journey Phase' },
  encounter: { ar: 'اللقاء', en: 'Encounter' },
  test_or_trial: { ar: 'اختبار', en: 'Test/Trial' },
  test: { ar: 'اختبار', en: 'Test' },
  trial: { ar: 'ابتلاء', en: 'Trial' },
  moral_decision: { ar: 'قرار أخلاقي', en: 'Moral Decision' },
  divine_intervention: { ar: 'التدخل الإلهي', en: 'Divine Intervention' },
  outcome: { ar: 'النتيجة', en: 'Outcome' },
  reflection: { ar: 'تأمل', en: 'Reflection' },
  development: { ar: 'تطور', en: 'Development' },
  climax: { ar: 'الذروة', en: 'Climax' },
  resolution: { ar: 'الحل', en: 'Resolution' },
  rising_action: { ar: 'تصاعد الأحداث', en: 'Rising Action' },
  background: { ar: 'خلفية', en: 'Background' },
  conclusion: { ar: 'الخاتمة', en: 'Conclusion' },
  setup: { ar: 'التمهيد', en: 'Setup' },
  falling_action: { ar: 'تراجع الأحداث', en: 'Falling Action' },
  // Additional narrative roles for new stories
  confrontation: { ar: 'المواجهة', en: 'Confrontation' },
  rejection: { ar: 'الرفض', en: 'Rejection' },
  dawah: { ar: 'الدعوة', en: 'Call to Faith' },
  exposure: { ar: 'الانكشاف', en: 'Exposure' },
  heroism: { ar: 'البطولة', en: 'Heroism' },
  escalation: { ar: 'التصعيد', en: 'Escalation' },
  steadfastness: { ar: 'الثبات', en: 'Steadfastness' },
  correction: { ar: 'التصحيح', en: 'Correction' },
  contrast: { ar: 'التناقض', en: 'Contrast' },
  lesson: { ar: 'الدرس', en: 'Lesson' },
  description: { ar: 'الوصف', en: 'Description' },
};

// Helper function to translate narrative role
function translateNarrativeRole(role: string, language: Language): string {
  const trans = NARRATIVE_ROLE_TRANSLATIONS[role];
  if (trans) return trans[language];
  // Fallback: mark untranslated in Arabic mode
  const formatted = role.replace(/_/g, ' ');
  return language === 'ar' ? `[${formatted}]` : formatted;
}

// Category translations
const CATEGORY_TRANSLATIONS: Record<string, { ar: string; en: string }> = {
  prophet: { ar: 'الأنبياء', en: 'Prophet' },
  named_char: { ar: 'شخصيات مسماة', en: 'Named Character' },
  nation: { ar: 'أمة', en: 'Nation' },
  parable: { ar: 'مثل', en: 'Parable' },
  historical: { ar: 'تاريخي', en: 'Historical' },
  unseen: { ar: 'الغيب', en: 'Unseen' },
  righteous: { ar: 'الصالحين', en: 'Righteous' },
  prophetic_sira: { ar: 'السيرة النبوية', en: 'Prophetic Era' },
};

function translateCategory(category: string, language: Language): string {
  const trans = CATEGORY_TRANSLATIONS[category];
  if (trans) return trans[language];
  const formatted = category.replace(/_/g, ' ');
  return language === 'ar' ? `[${formatted}]` : formatted;
}

// Era translations
const ERA_TRANSLATIONS: Record<string, { ar: string; en: string }> = {
  primordial: { ar: 'البدء', en: 'Primordial' },
  ancient: { ar: 'الأنبياء الأوائل', en: 'Ancient' },
  egypt: { ar: 'عصر مصر', en: 'Egypt Era' },
  israelite: { ar: 'بني إسرائيل', en: 'Israelite' },
  bani_israil: { ar: 'بني إسرائيل', en: 'Bani Israil Era' },
  pre_islamic: { ar: 'ما قبل الإسلام', en: 'Pre-Islamic' },
  prophetic: { ar: 'العصر النبوي', en: 'Prophetic Era' },
  unknown: { ar: 'غير محدد', en: 'Unknown' },
};

function translateEra(era: string, language: Language): string {
  const trans = ERA_TRANSLATIONS[era];
  if (trans) return trans[language];
  const formatted = era.replace(/_/g, ' ');
  return language === 'ar' ? `[${formatted}]` : formatted;
}

type ViewMode = 'timeline' | 'graph';

const ROLE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  introduction: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  divine_mission: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  journey_phase: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  encounter: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  trial: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  test: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  outcome: { bg: 'bg-teal-50', text: 'text-teal-700', border: 'border-teal-200' },
  reflection: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  development: { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200' },
  climax: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  default: { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' },
};

export function StoryAtlasDetailPage() {
  const { clusterId } = useParams<{ clusterId: string }>();
  const { language } = useLanguageStore();
  const [cluster, setCluster] = useState<StoryClusterDetail | null>(null);
  const [kgCluster, setKgCluster] = useState<KGClusterResponse | null>(null);
  const [graphData, setGraphData] = useState<AtlasGraphResponse | null>(null);
  const [kgGraphData, setKgGraphData] = useState<KGStoryGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [graphLoading, setGraphLoading] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [relatedClusters, setRelatedClusters] = useState<RelatedCluster[]>([]);
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [useKG, setUseKG] = useState(false);
  const [kgAvailable, setKgAvailable] = useState<boolean | null>(null);

  const isArabic = language === 'ar';

  // Check if KG is available on mount
  useEffect(() => {
    kgApi.health()
      .then(res => setKgAvailable(res.data.status === 'ok'))
      .catch(() => setKgAvailable(false));
  }, []);

  useEffect(() => {
    if (clusterId) {
      loadCluster();
    }
  }, [clusterId, useKG, language]);

  useEffect(() => {
    if (clusterId && viewMode === 'graph') {
      loadGraph();
    }
  }, [clusterId, viewMode, language, useKG]);

  async function loadCluster() {
    setLoading(true);
    try {
      if (useKG) {
        // Use Knowledge Graph API
        const kgRes = await kgApi.getStoryCluster(clusterId!, language);
        setKgCluster(kgRes.data);
        setCluster(null);
        setRelatedClusters([]);
      } else {
        // Use legacy API
        const [clusterRes, relatedRes] = await Promise.all([
          storyAtlasApi.getCluster(clusterId!),
          storyAtlasApi.getRelatedClusters(clusterId!).catch(() => ({ data: [] })),
        ]);
        setCluster(clusterRes.data);
        setKgCluster(null);
        setRelatedClusters(relatedRes.data || []);
      }
    } catch (error) {
      console.error('Failed to load cluster:', error);
    } finally {
      setLoading(false);
    }
  }

  async function loadGraph() {
    setGraphLoading(true);
    try {
      if (useKG) {
        // Use Knowledge Graph API
        const response = await kgApi.getStoryGraph(clusterId!, 'timeline', language);
        setKgGraphData(response.data);
        setGraphData(null);
      } else {
        // Use legacy API
        const response = await storyAtlasApi.getClusterGraph(clusterId!, language, 'timeline');
        setGraphData(response.data);
        setKgGraphData(null);
      }
    } catch (error) {
      console.error('Failed to load graph:', error);
    } finally {
      setGraphLoading(false);
    }
  }

  function toggleEvent(eventId: string) {
    const newExpanded = new Set(expandedEvents);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedEvents(newExpanded);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!cluster && !kgCluster) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-gray-500">{isArabic ? 'القصة غير موجودة' : 'Story not found'}</p>
        <Link to="/story-atlas" className="text-primary-600 hover:underline mt-4 inline-block">
          {isArabic ? 'العودة للأطلس' : 'Back to Atlas'}
        </Link>
      </div>
    );
  }

  // Normalize data from either source
  const title = useKG && kgCluster
    ? kgCluster.cluster.title
    : (isArabic ? cluster?.title_ar : cluster?.title_en);
  const summary = useKG && kgCluster
    ? kgCluster.cluster.summary
    : (isArabic ? cluster?.summary_ar : cluster?.summary_en);
  const lessons = useKG && kgCluster
    ? kgCluster.cluster.lessons
    : (isArabic ? cluster?.lessons_ar : cluster?.lessons_en);
  const category = useKG && kgCluster ? kgCluster.cluster.category : cluster?.category;
  const era = useKG && kgCluster ? kgCluster.cluster.era : cluster?.era;
  const mainPersons = useKG && kgCluster ? kgCluster.cluster.main_persons : cluster?.main_persons;
  const eventCount = useKG && kgCluster ? kgCluster.cluster.event_count : cluster?.event_count;
  const events = useKG && kgCluster ? kgCluster.events : cluster?.events;
  const places = cluster?.places || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link and KG Toggle */}
      <div className="flex items-center justify-between mb-6">
        <Link
          to="/story-atlas"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-primary-600"
        >
          <ArrowLeft className="w-4 h-4" />
          {isArabic ? 'العودة للأطلس' : 'Back to Atlas'}
        </Link>

        {/* Knowledge Graph Toggle */}
        {kgAvailable && (
          <button
            onClick={() => setUseKG(!useKG)}
            className={clsx(
              'inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
              useKG
                ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
            title={isArabic ? 'استخدم قاعدة المعرفة' : 'Use Knowledge Graph'}
          >
            <Database className="w-4 h-4" />
            {useKG ? (isArabic ? 'قاعدة المعرفة' : 'KG Mode') : (isArabic ? 'الوضع العادي' : 'Legacy')}
          </button>
        )}
      </div>

      {/* Header */}
      <div className="card mb-8">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <Book className="w-7 h-7 text-primary-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <h1 className="text-2xl font-bold">{title}</h1>
              {category && (
                <span className="text-sm bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {translateCategory(category, language)}
                </span>
              )}
              {era && (
                <span className="text-sm bg-amber-50 text-amber-700 px-2 py-1 rounded">
                  {translateEra(era, language)}
                </span>
              )}
              {useKG && (
                <span className="text-xs bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full">
                  <Database className="w-3 h-3 inline mr-1" />
                  KG
                </span>
              )}
            </div>
            {summary && <p className="text-gray-600">{summary}</p>}
          </div>
        </div>

        {/* Meta Info */}
        <div className="flex flex-wrap gap-6 text-sm">
          {mainPersons && mainPersons.length > 0 && (
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">
                {mainPersons.map(p => translateFigure(p, language)).join(isArabic ? '، ' : ', ')}
              </span>
            </div>
          )}
          {places && places.length > 0 && (
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">
                {places.map((p: any) =>
                  isArabic
                    ? (p.name_ar || p.name || 'غير معروف')
                    : (p.name || p.name_ar || 'Unknown')
                ).join(isArabic ? '، ' : ', ')}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600">
              {eventCount || 0} {isArabic ? 'أحداث' : 'events'}
            </span>
          </div>
        </div>

        {/* Lessons */}
        {lessons && lessons.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-100">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              {isArabic ? 'الدروس والعبر' : 'Lessons'}
            </h3>
            <ul className="space-y-1">
              {lessons.map((lesson, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-primary-500">•</span>
                  {lesson}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* View Toggle */}
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-lg font-semibold flex-1">
          {isArabic ? 'الأحداث' : 'Events'} ({events?.length || 0})
        </h2>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('timeline')}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              viewMode === 'timeline'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <List className="w-4 h-4" />
            {isArabic ? 'الجدول الزمني' : 'Timeline'}
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
            {isArabic ? 'الرسم البياني' : 'Graph'}
          </button>
        </div>
      </div>

      {/* Content */}
      {viewMode === 'timeline' ? (
        <div className="space-y-4">
          {useKG && kgCluster ? (
            // KG Events
            kgCluster.events
              .sort((a, b) => a.index - b.index)
              .map((event) => (
                <KGEventCard
                  key={event.id}
                  event={event}
                  language={language}
                  isExpanded={expandedEvents.has(event.id)}
                  onToggle={() => toggleEvent(event.id)}
                />
              ))
          ) : (
            // Legacy Events
            cluster?.events
              ?.sort((a, b) => a.chronological_index - b.chronological_index)
              .map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  language={language}
                  isExpanded={expandedEvents.has(event.id)}
                  onToggle={() => toggleEvent(event.id)}
                />
              ))
          )}

          {(!events || events.length === 0) && (
            <div className="card text-center py-8">
              <Clock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">
                {isArabic ? 'لا توجد أحداث متاحة بعد' : 'No events available yet'}
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="card p-0 overflow-hidden" style={{ height: '700px' }}>
          {graphLoading ? (
            <div className="flex items-center justify-center h-full bg-gray-50">
              <div className="text-center">
                <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
                <p className="text-gray-500">{isArabic ? 'جاري تحميل الرسم البياني...' : 'Loading graph...'}</p>
              </div>
            </div>
          ) : (graphData || kgGraphData) ? (
            <StoryGraphView graph={(useKG ? kgGraphData : graphData) as AtlasGraphResponse} language={language} />
          ) : (
            <div className="flex items-center justify-center h-full bg-gray-50">
              <div className="text-center">
                <Network className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500 mb-2">
                  {isArabic ? 'لا توجد بيانات للرسم البياني' : 'No graph data available'}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Related Clusters Section */}
      {relatedClusters.length > 0 && (
        <div className="mt-8">
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Network className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold">
                {isArabic ? 'قصص متصلة' : 'Related Stories'}
              </h3>
              <span className="text-sm text-gray-500">({relatedClusters.length})</span>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              {isArabic
                ? `قصص مرتبطة من خلال الشخصيات أو الأماكن أو المواضيع المشتركة`
                : `Stories connected through shared persons, places, or themes`}
            </p>

            <div className="space-y-3">
              {relatedClusters.map((related) => {
                const title = isArabic ? related.title_ar : related.title_en;

                return (
                  <Link
                    key={related.cluster_id}
                    to={`/story-atlas/${related.cluster_id}`}
                    className="block p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50/50 transition-all group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-gray-900 group-hover:text-primary-700">
                            {title}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                            {related.connection_type.replace(/_/g, ' ')}
                          </span>
                        </div>

                        {/* Shared Persons */}
                        {related.shared_persons.length > 0 && (
                          <div className="flex items-center gap-1 mb-1">
                            <Users className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-500">
                              {related.shared_persons.slice(0, 3).map(p => translateFigure(p, language)).join(isArabic ? '، ' : ', ')}
                            </span>
                          </div>
                        )}

                        {/* Shared Themes */}
                        {related.shared_themes.length > 0 && (
                          <div className="flex items-center gap-1">
                            <Tag className="w-3 h-3 text-gray-400" />
                            <div className="flex flex-wrap gap-1">
                              {related.shared_themes.slice(0, 3).map((theme, i) => {
                                const { text: translatedTheme } = translateTag(theme, language);
                                return (
                                  <span key={i} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                                    {translatedTheme}
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Shared Places */}
                        {related.shared_places.length > 0 && (
                          <div className="flex items-center gap-1 mt-1">
                            <MapPin className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-500">
                              {related.shared_places.slice(0, 2).join(isArabic ? '، ' : ', ')}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className={`text-gray-400 group-hover:text-primary-600 ${isArabic ? 'rotate-180' : ''}`}>
                        →
                      </div>
                    </div>

                    {/* Strength indicator */}
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-500 rounded-full"
                          style={{ width: `${related.strength * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">
                        {Math.round(related.strength * 100)}%
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EventCard({
  event,
  language,
  isExpanded,
  onToggle,
}: {
  event: StoryAtlasEvent;
  language: 'ar' | 'en';
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const isArabic = language === 'ar';
  const title = isArabic ? event.title_ar : event.title_en;
  const summary = isArabic ? event.summary_ar : event.summary_en;
  const roleColors = ROLE_COLORS[event.narrative_role] || ROLE_COLORS.default;

  return (
    <div className={`card border ${roleColors.border}`}>
      <button onClick={onToggle} className="w-full text-start">
        <div className="flex items-start gap-4">
          <div className={`w-10 h-10 ${roleColors.bg} ${roleColors.text} rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0`}>
            {event.chronological_index}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <span className="font-medium">{title}</span>
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {event.verse_reference}
              </span>
              <span className={`text-xs ${roleColors.bg} ${roleColors.text} px-2 py-0.5 rounded`}>
                {translateNarrativeRole(event.narrative_role, language)}
              </span>
              {event.is_entry_point && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                  {isArabic ? 'نقطة البداية' : 'Entry Point'}
                </span>
              )}
              <span className="ms-auto text-gray-400">
                {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </span>
            </div>
            {summary && (
              <p className="text-gray-600 text-sm line-clamp-2">{summary}</p>
            )}
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          {summary && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-1">
                {isArabic ? 'الملخص' : 'Summary'}
              </h4>
              <p className="text-sm text-gray-600">{summary}</p>
            </div>
          )}

          {/* Semantic Tags */}
          {event.semantic_tags && event.semantic_tags.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-1">
                {isArabic ? 'المواضيع' : 'Themes'}
              </h4>
              <div className="flex flex-wrap gap-1">
                {event.semantic_tags.map((tag, i) => {
                  const { text: translatedTag } = translateTag(tag, language);
                  return (
                    <span
                      key={i}
                      className="text-xs px-2 py-0.5 rounded bg-primary-50 text-primary-700"
                    >
                      {translatedTag}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Evidence */}
          {event.evidence && event.evidence.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">
                {isArabic ? 'المصادر' : 'Evidence'}
              </h4>
              <div className="space-y-2">
                {event.evidence.slice(0, 2).map((ev: any, i: number) => (
                  <div key={i} className="text-xs bg-gray-50 p-2 rounded">
                    <span className="font-medium text-gray-700">{ev.source_id || (isArabic ? 'مصدر' : 'Source')}</span>
                    {ev.snippet && (
                      <p className="text-gray-600 mt-1 line-clamp-2">{ev.snippet}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Link to Quran */}
          <div className="mt-4">
            <Link
              to={`/quran/${event.sura_no}?aya=${event.aya_start}`}
              className="text-sm text-primary-600 hover:text-primary-800 font-medium"
            >
              {isArabic ? 'اقرأ في المصحف' : 'Read in Quran'} →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * KGEventCard - Event card for Knowledge Graph data.
 * Uses KGEventSummary which is already localized by the API.
 */
function KGEventCard({
  event,
  language,
  isExpanded,
  onToggle,
}: {
  event: KGEventSummary;
  language: 'ar' | 'en';
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const isArabic = language === 'ar';
  const roleColors = ROLE_COLORS[event.narrative_role] || ROLE_COLORS.default;

  // Parse verse reference to extract sura:aya for linking
  const parseVerseRef = (ref: string) => {
    const match = ref.match(/(\d+):(\d+)/);
    if (match) return { sura: parseInt(match[1]), aya: parseInt(match[2]) };
    return null;
  };
  const verseLink = parseVerseRef(event.verse_reference);

  return (
    <div className={`card border ${roleColors.border}`}>
      <button onClick={onToggle} className="w-full text-start">
        <div className="flex items-start gap-4">
          <div className={`w-10 h-10 ${roleColors.bg} ${roleColors.text} rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0`}>
            {event.index}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <span className="font-medium">{event.title}</span>
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {event.verse_reference}
              </span>
              <span className={`text-xs ${roleColors.bg} ${roleColors.text} px-2 py-0.5 rounded`}>
                {translateNarrativeRole(event.narrative_role, language)}
              </span>
              {event.is_entry_point && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                  {isArabic ? 'نقطة البداية' : 'Entry Point'}
                </span>
              )}
              <span className="text-xs bg-emerald-50 text-emerald-600 px-1.5 py-0.5 rounded-full">
                <Database className="w-3 h-3 inline" />
              </span>
              <span className="ms-auto text-gray-400">
                {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </span>
            </div>
            {event.summary && (
              <p className="text-gray-600 text-sm line-clamp-2">{event.summary}</p>
            )}
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          {event.summary && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-1">
                {isArabic ? 'الملخص' : 'Summary'}
              </h4>
              <p className="text-sm text-gray-600">{event.summary}</p>
            </div>
          )}

          {/* Memorization Cue */}
          {event.memorization_cue && (
            <div className="mb-4 bg-amber-50 p-3 rounded-lg border border-amber-200">
              <h4 className="text-sm font-medium text-amber-800 mb-1 flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                {isArabic ? 'تلميح للحفظ' : 'Memorization Cue'}
              </h4>
              <p className="text-sm text-amber-700">{event.memorization_cue}</p>
            </div>
          )}

          {/* Semantic Tags */}
          {event.semantic_tags && event.semantic_tags.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-1">
                {isArabic ? 'المواضيع' : 'Themes'}
              </h4>
              <div className="flex flex-wrap gap-1">
                {event.semantic_tags.map((tag, i) => {
                  const { text: translatedTag } = translateTag(tag, language);
                  return (
                    <span
                      key={i}
                      className="text-xs px-2 py-0.5 rounded bg-primary-50 text-primary-700"
                    >
                      {translatedTag}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Link to Quran */}
          {verseLink && (
            <div className="mt-4">
              <Link
                to={`/quran/${verseLink.sura}?aya=${verseLink.aya}`}
                className="text-sm text-primary-600 hover:text-primary-800 font-medium"
              >
                {isArabic ? 'اقرأ في المصحف' : 'Read in Quran'} →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
