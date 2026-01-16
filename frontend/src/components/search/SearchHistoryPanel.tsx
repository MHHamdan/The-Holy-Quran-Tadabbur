/**
 * Search History Panel Component
 *
 * Displays:
 * - Recent search history
 * - Personalized search suggestions
 * - Verse recommendations based on interests
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History,
  Search,
  BookOpen,
  Sparkles,
  Clock,
  ChevronRight,
  Trash2,
  Loader2,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { useSearchHistoryStore } from '../../stores/searchHistoryStore';
import clsx from 'clsx';

interface Props {
  onSearchSelect?: (query: string) => void;
  onVerseSelect?: (suraNo: number, ayaNo: number) => void;
  compact?: boolean;
}

// Format relative time
function formatRelativeTime(timestamp: string, language: 'ar' | 'en'): string {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (language === 'ar') {
    if (diffMins < 1) return 'الآن';
    if (diffMins < 60) return `منذ ${diffMins} دقيقة`;
    if (diffHours < 24) return `منذ ${diffHours} ساعة`;
    return `منذ ${diffDays} يوم`;
  } else {
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  }
}

// Query type badge
function QueryTypeBadge({ type, language }: { type: string; language: 'ar' | 'en' }) {
  const labels: Record<string, { ar: string; en: string; color: string }> = {
    text: { ar: 'نص', en: 'Text', color: 'bg-blue-100 text-blue-700' },
    verse: { ar: 'آية', en: 'Verse', color: 'bg-green-100 text-green-700' },
    semantic: { ar: 'دلالي', en: 'Semantic', color: 'bg-purple-100 text-purple-700' },
    similar: { ar: 'متشابه', en: 'Similar', color: 'bg-amber-100 text-amber-700' },
  };

  const meta = labels[type] || { ar: type, en: type, color: 'bg-gray-100 text-gray-600' };

  return (
    <span className={clsx('text-xs px-1.5 py-0.5 rounded', meta.color)}>
      {meta[language]}
    </span>
  );
}

export function SearchHistoryPanel({ onSearchSelect, onVerseSelect, compact = false }: Props) {
  const { language } = useLanguageStore();
  const navigate = useNavigate();
  const {
    recentSearches,
    suggestions,
    recommendations,
    isLoadingHistory,
    isLoadingRecommendations,
    loadHistory,
    loadSuggestions,
    loadRecommendations,
    clearHistory,
    recordVerseClick,
  } = useSearchHistoryStore();

  const [activeTab, setActiveTab] = useState<'history' | 'suggestions' | 'recommendations'>('history');
  const isArabic = language === 'ar';

  useEffect(() => {
    // Load data on mount
    loadHistory(20);
    loadSuggestions(undefined, 10);
    loadRecommendations(10);
  }, []);

  const handleSearchClick = (query: string) => {
    if (onSearchSelect) {
      onSearchSelect(query);
    } else {
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleVerseClick = async (suraNo: number, ayaNo: number) => {
    await recordVerseClick(suraNo, ayaNo, 'recommendation');
    if (onVerseSelect) {
      onVerseSelect(suraNo, ayaNo);
    } else {
      navigate(`/quran/${suraNo}?aya=${ayaNo}`);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm(isArabic ? 'هل تريد مسح سجل البحث؟' : 'Clear search history?')) {
      await clearHistory();
    }
  };

  if (compact) {
    // Compact mode: just show recent searches
    return (
      <div className="space-y-2">
        {recentSearches.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-2">
            {isArabic ? 'لا يوجد سجل بحث' : 'No search history'}
          </p>
        ) : (
          recentSearches.slice(0, 5).map((entry, idx) => (
            <button
              key={idx}
              onClick={() => handleSearchClick(entry.query)}
              className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 text-left transition-colors"
            >
              <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className="flex-1 truncate text-sm">{entry.query}</span>
              <ChevronRight className={clsx('w-4 h-4 text-gray-400', isArabic && 'rotate-180')} />
            </button>
          ))
        )}
      </div>
    );
  }

  return (
    <div className="card">
      {/* Header with tabs */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('history')}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
              activeTab === 'history'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <History className="w-4 h-4" />
            {isArabic ? 'السجل' : 'History'}
          </button>
          <button
            onClick={() => setActiveTab('suggestions')}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
              activeTab === 'suggestions'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Search className="w-4 h-4" />
            {isArabic ? 'اقتراحات' : 'Suggestions'}
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
              activeTab === 'recommendations'
                ? 'bg-white shadow text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Sparkles className="w-4 h-4" />
            {isArabic ? 'مقترحات' : 'For You'}
          </button>
        </div>

        {activeTab === 'history' && recentSearches.length > 0 && (
          <button
            onClick={handleClearHistory}
            className="btn btn-sm btn-ghost text-gray-500 hover:text-red-600"
            title={isArabic ? 'مسح السجل' : 'Clear history'}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Content */}
      {activeTab === 'history' && (
        <div className="space-y-2">
          {isLoadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
            </div>
          ) : recentSearches.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <History className="w-12 h-12 mx-auto text-gray-300 mb-2" />
              <p>{isArabic ? 'لا يوجد سجل بحث بعد' : 'No search history yet'}</p>
              <p className="text-sm mt-1">
                {isArabic ? 'ابدأ البحث لرؤية سجلك هنا' : 'Start searching to see your history here'}
              </p>
            </div>
          ) : (
            recentSearches.map((entry, idx) => (
              <button
                key={idx}
                onClick={() => handleSearchClick(entry.query)}
                className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 text-left transition-colors group"
              >
                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                  <Clock className="w-4 h-4 text-gray-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{entry.query}</span>
                    <QueryTypeBadge type={entry.query_type} language={language} />
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>{formatRelativeTime(entry.timestamp, language)}</span>
                    {entry.result_count > 0 && (
                      <>
                        <span>•</span>
                        <span>
                          {entry.result_count} {isArabic ? 'نتيجة' : 'results'}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                <ChevronRight className={clsx(
                  'w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors',
                  isArabic && 'rotate-180'
                )} />
              </button>
            ))
          )}
        </div>
      )}

      {activeTab === 'suggestions' && (
        <div className="space-y-2">
          {suggestions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Search className="w-12 h-12 mx-auto text-gray-300 mb-2" />
              <p>{isArabic ? 'لا توجد اقتراحات بعد' : 'No suggestions yet'}</p>
              <p className="text-sm mt-1">
                {isArabic ? 'ابحث أكثر للحصول على اقتراحات مخصصة' : 'Search more to get personalized suggestions'}
              </p>
            </div>
          ) : (
            suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSearchClick(suggestion.query)}
                className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 text-left transition-colors group"
              >
                <div className="w-8 h-8 rounded-full bg-primary-50 flex items-center justify-center flex-shrink-0">
                  <Search className="w-4 h-4 text-primary-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="font-medium">{suggestion.query}</span>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>
                      {isArabic ? `${suggestion.frequency} مرة` : `${suggestion.frequency}x searched`}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: `${suggestion.relevance_score * 100}%` }}
                    />
                  </div>
                  <ChevronRight className={clsx(
                    'w-5 h-5 text-gray-400 group-hover:text-primary-600',
                    isArabic && 'rotate-180'
                  )} />
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {activeTab === 'recommendations' && (
        <div className="space-y-2">
          {isLoadingRecommendations ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
            </div>
          ) : recommendations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Sparkles className="w-12 h-12 mx-auto text-gray-300 mb-2" />
              <p>{isArabic ? 'لا توجد توصيات بعد' : 'No recommendations yet'}</p>
              <p className="text-sm mt-1">
                {isArabic
                  ? 'تصفح وابحث لتحصل على آيات مقترحة لك'
                  : 'Browse and search to get personalized verse recommendations'}
              </p>
            </div>
          ) : (
            recommendations.map((rec, idx) => (
              <button
                key={idx}
                onClick={() => handleVerseClick(rec.sura_no, rec.aya_no)}
                className="w-full p-3 rounded-lg hover:bg-gray-50 text-left transition-colors group"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center flex-shrink-0">
                    <BookOpen className="w-4 h-4 text-amber-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-primary-700">{rec.reference}</span>
                      <span className="text-sm text-gray-500">
                        {isArabic ? rec.sura_name_ar : rec.sura_name_en}
                      </span>
                    </div>
                    <p className="text-sm font-arabic leading-relaxed text-gray-800 line-clamp-2" dir="rtl">
                      {rec.text_uthmani}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Sparkles className="w-3 h-3 text-amber-500" />
                      <span className="text-xs text-gray-500">
                        {isArabic ? rec.reason_ar : rec.reason}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className={clsx(
                    'w-5 h-5 text-gray-400 group-hover:text-primary-600 flex-shrink-0',
                    isArabic && 'rotate-180'
                  )} />
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default SearchHistoryPanel;
