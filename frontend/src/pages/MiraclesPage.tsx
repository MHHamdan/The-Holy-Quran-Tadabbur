import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Zap,
  User,
  BookOpen,
  MapPin,
  ArrowRight,
  Sparkles,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { conceptsApi, MiracleWithAssociations, ConceptSummary } from '../lib/api';
import { ErrorPanel, parseAPIError, APIErrorData, MiracleGridSkeleton } from '../components/common';
import clsx from 'clsx';

export function MiraclesPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [miracles, setMiracles] = useState<MiracleWithAssociations[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIErrorData | null>(null);
  const [expandedMiracle, setExpandedMiracle] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const loadMiracles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await conceptsApi.getAllMiracles();
      setMiracles(response.data);
    } catch (err) {
      const parsedError = parseAPIError(err);
      setError(parsedError);
      if (retryCount < 2 && parsedError?.code === 'network_error') {
        setRetryCount((c) => c + 1);
        const delay = Math.pow(2, retryCount) * 1000;
        setTimeout(() => loadMiracles(), delay);
      }
    } finally {
      setLoading(false);
    }
  }, [retryCount]);

  useEffect(() => {
    loadMiracles();
  }, []);

  const handleRetry = () => {
    setRetryCount(0);
    loadMiracles();
  };

  const miraclesWithPersons = miracles.filter((m) => m.related_persons.length > 0);
  const otherMiracles = miracles.filter((m) => m.related_persons.length === 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* Header */}
      <div className="mb-6">
        <div className={clsx('flex items-center gap-3 mb-2', isRtl && 'flex-row-reverse')}>
          <div className="p-2 bg-amber-100 rounded-lg">
            <Sparkles className="w-8 h-8 text-amber-600" />
          </div>
          <div>
            <h1 className={clsx('text-3xl font-bold text-gray-900', isRtl && 'font-arabic')}>
              {t('miracles_page_title', language)}
            </h1>
            <p className={clsx('text-gray-500 text-sm', isRtl && 'font-arabic')}>
              {t('miracles_page_subtitle', language)}
            </p>
          </div>
        </div>
        <p className={clsx('text-gray-600 mt-3 max-w-3xl', isRtl && 'text-right font-arabic')}
           dir={isRtl ? 'rtl' : 'ltr'}>
          {t('miracles_page_description', language)}
        </p>
      </div>

      {/* Phase K — Scientific safety notice */}
      <div className={clsx(
        'rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 mb-6 flex gap-3',
        isRtl && 'flex-row-reverse'
      )}>
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className={clsx('text-sm font-semibold text-amber-900 mb-1', isRtl && 'text-right font-arabic')}>
            {t('miracles_safety_title', language)}
          </p>
          <p className={clsx('text-sm text-amber-800 leading-relaxed', isRtl && 'text-right font-arabic')}
             dir={isRtl ? 'rtl' : 'ltr'}>
            {t('miracles_safety_body', language)}
          </p>
          <Link
            to="/ask"
            className={clsx(
              'mt-2 inline-flex items-center gap-1 text-xs font-medium text-amber-700',
              'hover:text-amber-900 transition-colors',
              isRtl && 'flex-row-reverse font-arabic'
            )}
          >
            {t('miracles_safety_label', language)}
            <ArrowRight className={clsx('w-3.5 h-3.5', isRtl && 'rotate-180')} />
          </Link>
        </div>
      </div>

      {/* Stats Bar */}
      {!loading && !error && miracles.length > 0 && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 mb-8 border border-amber-200">
          <div className="flex flex-wrap gap-6 justify-center text-center">
            <div>
              <div className="text-2xl font-bold text-amber-700">{miracles.length}</div>
              <div className={clsx('text-sm text-gray-600', isRtl && 'font-arabic')}>
                {t('miracles_stat_total', language)}
              </div>
            </div>
            <div className="border-l border-amber-200 pl-6">
              <div className="text-2xl font-bold text-amber-700">{miraclesWithPersons.length}</div>
              <div className={clsx('text-sm text-gray-600', isRtl && 'font-arabic')}>
                {t('miracles_stat_prophetic', language)}
              </div>
            </div>
            <div className="border-l border-amber-200 pl-6">
              <div className="text-2xl font-bold text-amber-700">
                {miracles.reduce((sum, m) => sum + m.occurrence_count, 0)}
              </div>
              <div className={clsx('text-sm text-gray-600', isRtl && 'font-arabic')}>
                {t('miracles_stat_occurrences', language)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading / Error / Empty */}
      {loading ? (
        <MiracleGridSkeleton count={6} />
      ) : error ? (
        <ErrorPanel error={error} onRetry={handleRetry} onReport={() => {}} />
      ) : miracles.length === 0 ? (
        <div className="text-center py-12 card">
          <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className={clsx('text-gray-500', isRtl && 'font-arabic')}>
            {t('miracles_empty', language)}
          </p>
        </div>
      ) : (
        <div className="space-y-8">

          {/* Prophetic Miracles */}
          {miraclesWithPersons.length > 0 && (
            <section>
              <h2 className={clsx(
                'text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2',
                isRtl && 'flex-row-reverse font-arabic'
              )}>
                <User className="w-5 h-5 text-blue-600 shrink-0" />
                {t('miracles_section_prophetic', language)}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {miraclesWithPersons.map((miracle) => (
                  <MiracleCard
                    key={miracle.id}
                    miracle={miracle}
                    language={language}
                    isRtl={isRtl}
                    expanded={expandedMiracle === miracle.id}
                    onToggle={() =>
                      setExpandedMiracle(expandedMiracle === miracle.id ? null : miracle.id)
                    }
                  />
                ))}
              </div>
            </section>
          )}

          {/* Other Signs */}
          {otherMiracles.length > 0 && (
            <section>
              <h2 className={clsx(
                'text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2',
                isRtl && 'flex-row-reverse font-arabic'
              )}>
                <Sparkles className="w-5 h-5 text-amber-600 shrink-0" />
                {t('miracles_section_other', language)}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {otherMiracles.map((miracle) => (
                  <MiracleCard
                    key={miracle.id}
                    miracle={miracle}
                    language={language}
                    isRtl={isRtl}
                    expanded={expandedMiracle === miracle.id}
                    onToggle={() =>
                      setExpandedMiracle(expandedMiracle === miracle.id ? null : miracle.id)
                    }
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {/* Navigation links */}
      <div className="mt-12 pt-8 border-t border-gray-200">
        <h3 className={clsx('text-lg font-semibold text-gray-900 mb-4', isRtl && 'text-right font-arabic')}>
          {t('miracles_explore_more', language)}
        </h3>
        <div className={clsx('flex flex-wrap gap-4', isRtl && 'flex-row-reverse')}>
          <Link
            to="/concepts"
            className={clsx(
              'flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors',
              isRtl && 'flex-row-reverse font-arabic'
            )}
          >
            <BookOpen className="w-4 h-4" />
            {t('miracles_all_concepts', language)}
            <ArrowRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
          </Link>
          <Link
            to="/story-atlas"
            className={clsx(
              'flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors',
              isRtl && 'flex-row-reverse font-arabic'
            )}
          >
            <MapPin className="w-4 h-4" />
            {t('miracles_story_atlas', language)}
            <ArrowRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
          </Link>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Miracle Card
// ---------------------------------------------------------------------------

function MiracleCard({
  miracle,
  language,
  isRtl,
  expanded,
  onToggle,
}: {
  miracle: MiracleWithAssociations;
  language: 'ar' | 'en';
  isRtl: boolean;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      className={clsx(
        'bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 overflow-hidden transition-all duration-300',
        expanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {/* Card header — clickable */}
      <div className="p-4 cursor-pointer" onClick={onToggle}>
        <div className={clsx('flex items-start justify-between', isRtl && 'flex-row-reverse')}>
          <div className={clsx('flex items-center gap-3', isRtl && 'flex-row-reverse')}>
            <div className="p-2 bg-amber-200 rounded-lg shrink-0">
              <Zap className="w-5 h-5 text-amber-700" />
            </div>
            <div>
              <h3 className={clsx('font-semibold text-gray-900', isRtl && 'font-arabic text-right')}>
                {isRtl ? miracle.label_ar : miracle.label_en}
              </h3>
              {!isRtl && miracle.label_ar && (
                <p className="text-sm text-gray-500 font-arabic" dir="rtl">
                  {miracle.label_ar}
                </p>
              )}
            </div>
          </div>
          <ChevronRight
            className={clsx(
              'w-5 h-5 text-gray-400 shrink-0 transition-transform',
              expanded && 'rotate-90',
              isRtl && 'rotate-180'
            )}
          />
        </div>

        {/* Quick Stats */}
        <div className={clsx('flex items-center gap-4 mt-3 text-sm text-gray-600', isRtl && 'flex-row-reverse')}>
          {miracle.related_persons.length > 0 && (
            <span className="flex items-center gap-1">
              <User className="w-4 h-4" />
              {miracle.related_persons.length}
            </span>
          )}
          {miracle.related_stories.length > 0 && (
            <span className="flex items-center gap-1">
              <BookOpen className="w-4 h-4" />
              {miracle.related_stories.length}
            </span>
          )}
          {miracle.occurrence_count > 0 && (
            <span className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {miracle.occurrence_count}{' '}
              <span className={isRtl ? 'font-arabic' : ''}>
                {t('miracles_refs_label', language)}
              </span>
            </span>
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-amber-200 pt-4 space-y-4">
          {/* Description */}
          {(miracle.description_en || miracle.description_ar) && (
            <p className={clsx('text-sm text-gray-700', isRtl && 'text-right font-arabic')}
               dir={isRtl ? 'rtl' : 'ltr'}>
              {isRtl
                ? miracle.description_ar || miracle.description_en
                : miracle.description_en || miracle.description_ar}
            </p>
          )}

          {/* Related Figures */}
          {miracle.related_persons.length > 0 && (
            <div>
              <h4 className={clsx('text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2', isRtl && 'text-right font-arabic')}>
                {t('miracles_related_figures', language)}
              </h4>
              <div className={clsx('flex flex-wrap gap-2', isRtl && 'flex-row-reverse')}>
                {miracle.related_persons.map((person: ConceptSummary) => (
                  <Link
                    key={person.id}
                    to={`/concepts/${person.id}`}
                    className={clsx(
                      'inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition-colors',
                      isRtl && 'flex-row-reverse font-arabic'
                    )}
                  >
                    <User className="w-3 h-3 shrink-0" />
                    {isRtl ? person.label_ar : person.label_en}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Related Stories */}
          {miracle.related_stories.length > 0 && (
            <div>
              <h4 className={clsx('text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2', isRtl && 'text-right font-arabic')}>
                {t('miracles_related_stories', language)}
              </h4>
              <div className={clsx('flex flex-wrap gap-2', isRtl && 'flex-row-reverse')}>
                {miracle.related_stories.map((storyId: string) => (
                  <Link
                    key={storyId}
                    to={`/stories/${storyId}`}
                    className={clsx(
                      'inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm hover:bg-green-200 transition-colors',
                      isRtl && 'flex-row-reverse'
                    )}
                  >
                    <BookOpen className="w-3 h-3 shrink-0" />
                    {storyId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* View related prophet */}
          {miracle.related_persons.length > 0 && (
            <Link
              to={`/concepts/${miracle.related_persons[0].id}`}
              className={clsx(
                'inline-flex items-center gap-2 text-amber-700 hover:text-amber-800 text-sm font-medium',
                isRtl && 'flex-row-reverse font-arabic'
              )}
            >
              {t('miracles_view_prophet', language)}
              <ArrowRight className={clsx('w-4 h-4 shrink-0', isRtl && 'rotate-180')} />
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
