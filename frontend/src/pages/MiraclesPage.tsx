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
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { conceptsApi, MiracleWithAssociations, ConceptSummary } from '../lib/api';
import { ErrorPanel, parseAPIError, APIErrorData, MiracleGridSkeleton } from '../components/common';
import clsx from 'clsx';

export function MiraclesPage() {
  const { language } = useLanguageStore();
  const [miracles, setMiracles] = useState<MiracleWithAssociations[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIErrorData | null>(null);
  const [expandedMiracle, setExpandedMiracle] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const isArabic = language === 'ar';

  const loadMiracles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await conceptsApi.getAllMiracles();
      setMiracles(response.data);
    } catch (err) {
      console.error('Failed to load miracles:', err);
      const parsedError = parseAPIError(err);
      setError(parsedError);

      // Auto-retry once on network errors with exponential backoff
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

  const handleReport = () => {
    console.log('Report issue with request_id:', error?.request_id);
  };

  // Group miracles by whether they have related persons
  const miraclesWithPersons = miracles.filter(m => m.related_persons.length > 0);
  const otherMiracles = miracles.filter(m => m.related_persons.length === 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-amber-100 rounded-lg">
            <Sparkles className="w-8 h-8 text-amber-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {isArabic ? 'الآيات والمعجزات' : 'Signs & Miracles'}
            </h1>
            <p className="text-gray-500 text-sm">
              {isArabic ? 'آيات القرآن الكريم' : 'Quranic Signs (Ayat)'}
            </p>
          </div>
        </div>
        <p className="text-gray-600 mt-3 max-w-3xl">
          {isArabic
            ? 'استكشف الآيات والمعجزات المذكورة في القرآن الكريم، من معجزات الأنبياء إلى الآيات الكونية. كل آية موثقة بمراجع قرآنية.'
            : 'Explore the signs and miracles mentioned in the Holy Quran, from prophetic miracles to cosmic signs. Each is grounded in Quranic references.'}
        </p>
      </div>

      {/* Stats Bar */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 mb-8 border border-amber-200">
        <div className="flex flex-wrap gap-6 justify-center text-center">
          <div>
            <div className="text-2xl font-bold text-amber-700">{miracles.length}</div>
            <div className="text-sm text-gray-600">
              {isArabic ? 'آية ومعجزة' : 'Signs & Miracles'}
            </div>
          </div>
          <div className="border-l border-amber-200 pl-6">
            <div className="text-2xl font-bold text-amber-700">{miraclesWithPersons.length}</div>
            <div className="text-sm text-gray-600">
              {isArabic ? 'معجزات مرتبطة بأنبياء' : 'Prophet-linked Miracles'}
            </div>
          </div>
          <div className="border-l border-amber-200 pl-6">
            <div className="text-2xl font-bold text-amber-700">
              {miracles.reduce((sum, m) => sum + m.occurrence_count, 0)}
            </div>
            <div className="text-sm text-gray-600">
              {isArabic ? 'إجمالي المواضع' : 'Total Occurrences'}
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <MiracleGridSkeleton count={6} />
      ) : error ? (
        <ErrorPanel
          error={error}
          onRetry={handleRetry}
          onReport={handleReport}
        />
      ) : miracles.length === 0 ? (
        <div className="text-center py-12 card">
          <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {isArabic
              ? 'لم يتم العثور على آيات. يرجى تشغيل سكريبت بذر المفاهيم.'
              : 'No miracles found. Please run the concept seeding script.'}
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Miracles with Prophet Links */}
          {miraclesWithPersons.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                {isArabic ? 'معجزات الأنبياء' : 'Prophetic Miracles'}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {miraclesWithPersons.map((miracle) => (
                  <MiracleCard
                    key={miracle.id}
                    miracle={miracle}
                    language={language}
                    expanded={expandedMiracle === miracle.id}
                    onToggle={() => setExpandedMiracle(
                      expandedMiracle === miracle.id ? null : miracle.id
                    )}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Other Signs */}
          {otherMiracles.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-600" />
                {isArabic ? 'آيات أخرى' : 'Other Signs'}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {otherMiracles.map((miracle) => (
                  <MiracleCard
                    key={miracle.id}
                    miracle={miracle}
                    language={language}
                    expanded={expandedMiracle === miracle.id}
                    onToggle={() => setExpandedMiracle(
                      expandedMiracle === miracle.id ? null : miracle.id
                    )}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {/* Navigation links */}
      <div className="mt-12 pt-8 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {isArabic ? 'استكشف المزيد' : 'Explore More'}
        </h3>
        <div className="flex flex-wrap gap-4">
          <Link
            to="/concepts"
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <BookOpen className="w-4 h-4" />
            {isArabic ? 'جميع المفاهيم' : 'All Concepts'}
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/story-atlas"
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <MapPin className="w-4 h-4" />
            {isArabic ? 'أطلس القصص' : 'Story Atlas'}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

// Miracle Card Component
function MiracleCard({
  miracle,
  language,
  expanded,
  onToggle,
}: {
  miracle: MiracleWithAssociations;
  language: 'ar' | 'en';
  expanded: boolean;
  onToggle: () => void;
}) {
  const isArabic = language === 'ar';

  return (
    <div
      className={clsx(
        'bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 overflow-hidden transition-all duration-300',
        expanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'
      )}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-200 rounded-lg">
              <Zap className="w-5 h-5 text-amber-700" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">
                {isArabic ? miracle.label_ar : miracle.label_en}
              </h3>
              {!isArabic && miracle.label_ar && (
                <p className="text-sm text-gray-500 font-arabic" dir="rtl">
                  {miracle.label_ar}
                </p>
              )}
            </div>
          </div>
          <ChevronRight
            className={clsx(
              'w-5 h-5 text-gray-400 transition-transform',
              expanded && 'rotate-90'
            )}
          />
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
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
              {miracle.occurrence_count} {isArabic ? 'موضع' : 'refs'}
            </span>
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-amber-200 pt-4 space-y-4">
          {/* Description */}
          {(miracle.description_en || miracle.description_ar) && (
            <p className="text-sm text-gray-700">
              {isArabic
                ? miracle.description_ar || miracle.description_en
                : miracle.description_en || miracle.description_ar}
            </p>
          )}

          {/* Related Persons */}
          {miracle.related_persons.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {isArabic ? 'الشخصيات المرتبطة' : 'Related Figures'}
              </h4>
              <div className="flex flex-wrap gap-2">
                {miracle.related_persons.map((person: ConceptSummary) => (
                  <Link
                    key={person.id}
                    to={`/concepts/${person.id}`}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition-colors"
                  >
                    <User className="w-3 h-3" />
                    {isArabic ? person.label_ar : person.label_en}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Related Stories */}
          {miracle.related_stories.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {isArabic ? 'القصص المرتبطة' : 'Related Stories'}
              </h4>
              <div className="flex flex-wrap gap-2">
                {miracle.related_stories.map((storyId: string) => (
                  <Link
                    key={storyId}
                    to={`/stories/${storyId}`}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm hover:bg-green-200 transition-colors"
                  >
                    <BookOpen className="w-3 h-3" />
                    {storyId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* View Related Prophet Link - only if has related persons */}
          {miracle.related_persons.length > 0 && (
            <Link
              to={`/concepts/${miracle.related_persons[0].id}`}
              className="inline-flex items-center gap-2 text-amber-700 hover:text-amber-800 text-sm font-medium"
            >
              {isArabic ? 'عرض النبي المرتبط' : 'View Related Prophet'}
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
