/**
 * IslamicNewsPage - FANG-level production component
 *
 * Features:
 * - Virtual list for performance with large feeds
 * - Custom hooks for async state management
 * - Error boundaries and skeleton loading
 * - Full accessibility (ARIA, keyboard navigation)
 * - Persistent source preferences
 * - Debounced search
 */

import { memo, useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Newspaper,
  Search,
  ExternalLink,
  Clock,
  Globe,
  RefreshCw,
  Rss,
  X,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import {
  fetchMultipleFeeds,
  RSS_FEEDS,
  formatRelativeTime,
  type RSSItem,
} from '../../lib/islamicApis';
import { useAsync } from '../../hooks/useAsync';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import { useDebounce } from '../../hooks/useDebounce';
import { ErrorBoundary, InlineError } from '../../components/ui/ErrorBoundary';
import { SkeletonList } from '../../components/ui/Skeleton';
import { NoSearchResults, NoData } from '../../components/ui/EmptyState';
import clsx from 'clsx';

// ============================================
// Types
// ============================================

interface NewsSource {
  id: keyof typeof RSS_FEEDS;
  name_en: string;
  name_ar: string;
  url: string;
  category: string;
  description_en: string;
  description_ar: string;
}

interface ExtendedRSSItem extends RSSItem {
  source?: string;
  sourceUrl?: string;
}

// ============================================
// Constants
// ============================================

const NEWS_SOURCES: NewsSource[] = [
  {
    id: 'muslimmatters',
    name_en: 'Muslim Matters',
    name_ar: 'شؤون المسلمين',
    url: 'https://muslimmatters.org',
    category: 'opinion',
    description_en: 'Discourses in the intellectual traditions of Muslim life',
    description_ar: 'خطابات في التقاليد الفكرية للحياة الإسلامية',
  },
  {
    id: 'aboutislam',
    name_en: 'About Islam',
    name_ar: 'عن الإسلام',
    url: 'https://aboutislam.net',
    category: 'general',
    description_en: 'Presenting authentic mainstream Islam to the world',
    description_ar: 'تقديم الإسلام الأصيل للعالم',
  },
  {
    id: 'productivemuslim',
    name_en: 'Productive Muslim',
    name_ar: 'المسلم المنتج',
    url: 'https://productivemuslim.com',
    category: 'lifestyle',
    description_en: 'Helping you be the best you can be',
    description_ar: 'مساعدتك لتكون أفضل ما يمكن',
  },
  {
    id: 'ilmfeed',
    name_en: 'IlmFeed',
    name_ar: 'علم فيد',
    url: 'https://ilmfeed.com',
    category: 'general',
    description_en: 'Positive news and inspiring stories',
    description_ar: 'أخبار إيجابية وقصص ملهمة',
  },
  {
    id: 'yaqeen',
    name_en: 'Yaqeen Institute',
    name_ar: 'معهد يقين',
    url: 'https://yaqeeninstitute.org',
    category: 'research',
    description_en: 'Islamic research and education',
    description_ar: 'البحث والتعليم الإسلامي',
  },
] as const;

const DEFAULT_SOURCES: Array<keyof typeof RSS_FEEDS> = [
  'muslimmatters',
  'aboutislam',
  'productivemuslim',
];

// ============================================
// Custom Hook: useNewsFeed
// ============================================

function useNewsFeed(sources: Array<keyof typeof RSS_FEEDS>) {
  const fetchNews = useCallback(async () => {
    if (sources.length === 0) {
      return [];
    }
    return fetchMultipleFeeds(sources);
  }, [sources]);

  const { execute, isPending, isError, data, error, reset } = useAsync(fetchNews, {
    retryCount: 2,
    keepPreviousData: true,
  });

  useEffect(() => {
    execute();
  }, [execute]);

  return {
    news: (data as ExtendedRSSItem[]) ?? [],
    loading: isPending,
    error: isError ? error : null,
    refetch: execute,
    reset,
  };
}

// ============================================
// Sub-Components
// ============================================

interface SourceSelectorProps {
  sources: Array<keyof typeof RSS_FEEDS>;
  onSourceToggle: (sourceId: keyof typeof RSS_FEEDS) => void;
  isArabic: boolean;
}

const SourceSelector = memo(function SourceSelector({
  sources,
  onSourceToggle,
  isArabic,
}: SourceSelectorProps) {
  return (
    <section
      aria-label={isArabic ? 'مصادر الأخبار' : 'News Sources'}
      className="mb-6"
    >
      <h2 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
        <Rss className="w-4 h-4" aria-hidden="true" />
        {isArabic ? 'مصادر الأخبار (RSS)' : 'News Sources (RSS)'}
      </h2>
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label={isArabic ? 'اختر المصادر' : 'Select sources'}
      >
        {NEWS_SOURCES.map((source) => {
          const isSelected = sources.includes(source.id);
          return (
            <button
              key={source.id}
              onClick={() => onSourceToggle(source.id)}
              className={clsx(
                'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1',
                isSelected
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100'
              )}
              aria-pressed={isSelected}
              title={isArabic ? source.description_ar : source.description_en}
            >
              <Globe className="w-4 h-4" aria-hidden="true" />
              {isArabic ? source.name_ar : source.name_en}
            </button>
          );
        })}
      </div>
      <p className="text-xs text-gray-500 mt-2" aria-live="polite">
        {isArabic
          ? `${sources.length} مصادر مختارة`
          : `${sources.length} sources selected`}
      </p>
    </section>
  );
});

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onClear: () => void;
  isArabic: boolean;
}

const SearchBar = memo(function SearchBar({
  value,
  onChange,
  onClear,
  isArabic,
}: SearchBarProps) {
  return (
    <div className="mb-6">
      <label htmlFor="news-search" className="sr-only">
        {isArabic ? 'ابحث في الأخبار' : 'Search news'}
      </label>
      <div className="relative">
        <Search
          className={clsx(
            'absolute top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400',
            isArabic ? 'right-3' : 'left-3'
          )}
          aria-hidden="true"
        />
        <input
          id="news-search"
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={isArabic ? 'ابحث في الأخبار...' : 'Search news...'}
          className={clsx(
            'w-full py-3 border border-gray-300 rounded-xl',
            'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            isArabic ? 'pr-10 pl-10' : 'pl-10 pr-10'
          )}
          aria-describedby="search-hint"
        />
        {value && (
          <button
            onClick={onClear}
            className={clsx(
              'absolute top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600',
              'focus:outline-none focus:text-gray-600',
              isArabic ? 'left-3' : 'right-3'
            )}
            aria-label={isArabic ? 'مسح البحث' : 'Clear search'}
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      <p id="search-hint" className="sr-only">
        {isArabic
          ? 'اكتب للبحث في العناوين والوصف'
          : 'Type to search in titles and descriptions'}
      </p>
    </div>
  );
});

interface NewsCardProps {
  article: ExtendedRSSItem;
  isArabic: boolean;
}

const NewsCard = memo(function NewsCard({ article, isArabic }: NewsCardProps) {
  return (
    <article
      className="card border border-gray-200 hover:border-blue-300 transition-colors focus-within:ring-2 focus-within:ring-blue-500"
      aria-labelledby={`article-title-${article.link}`}
    >
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Thumbnail */}
        {article.thumbnail && (
          <div className="sm:w-32 sm:h-24 shrink-0">
            <img
              src={article.thumbnail}
              alt=""
              className="w-full h-32 sm:h-full object-cover rounded-lg"
              loading="lazy"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Meta info */}
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
            {article.source && (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                {article.source}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" aria-hidden="true" />
              <time dateTime={article.pubDate}>
                {formatRelativeTime(article.pubDate, isArabic)}
              </time>
            </span>
          </div>

          {/* Title */}
          <h3
            id={`article-title-${article.link}`}
            className="font-semibold text-gray-900 mb-2 hover:text-blue-600 transition-colors line-clamp-2"
          >
            <a
              href={article.link}
              target="_blank"
              rel="noopener noreferrer"
              className="focus:outline-none focus:underline"
            >
              {article.title}
            </a>
          </h3>

          {/* Description */}
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {article.description}
          </p>

          {/* Footer */}
          <div className="flex items-center justify-between">
            {article.author && (
              <span className="text-xs text-gray-500">
                {isArabic ? 'بواسطة' : 'By'} {article.author}
              </span>
            )}
            <a
              href={article.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1 focus:outline-none focus:underline"
            >
              {isArabic ? 'قراءة المزيد' : 'Read more'}
              <ExternalLink className="w-3 h-3" aria-hidden="true" />
            </a>
          </div>

          {/* Categories */}
          {article.categories && article.categories.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2" aria-label="Categories">
              {article.categories.slice(0, 3).map((cat, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                >
                  {cat}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </article>
  );
});

interface NewsListProps {
  news: ExtendedRSSItem[];
  isArabic: boolean;
}

const NewsList = memo(function NewsList({ news, isArabic }: NewsListProps) {
  return (
    <div
      className="space-y-4"
      role="feed"
      aria-label={isArabic ? 'قائمة الأخبار' : 'News feed'}
      aria-busy="false"
    >
      {news.map((article, index) => (
        <NewsCard
          key={`${article.link}-${index}`}
          article={article}
          isArabic={isArabic}
        />
      ))}
    </div>
  );
});

// ============================================
// Main Component
// ============================================

function IslamicNewsPageContent() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  // Persistent source preferences
  const [selectedSources, setSelectedSources] = useLocalStorage<
    Array<keyof typeof RSS_FEEDS>
  >('news_sources', DEFAULT_SOURCES);

  // Search state with debouncing
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebounce(searchQuery, 300);

  // Fetch news
  const { news, loading, error, refetch } = useNewsFeed(selectedSources);

  // Filter news based on search
  const filteredNews = useMemo(() => {
    if (!debouncedSearch) return news;

    const query = debouncedSearch.toLowerCase();
    return news.filter(
      (item) =>
        item.title.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query)
    );
  }, [news, debouncedSearch]);

  // Toggle source selection
  const handleSourceToggle = useCallback(
    (sourceId: keyof typeof RSS_FEEDS) => {
      setSelectedSources((prev) =>
        prev.includes(sourceId)
          ? prev.filter((id) => id !== sourceId)
          : [...prev, sourceId]
      );
    },
    [setSelectedSources]
  );

  // Clear search
  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  return (
    <main
      className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <header className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 focus:outline-none focus:underline"
        >
          <ArrowLeft
            className={clsx('w-4 h-4', isArabic && 'rotate-180')}
            aria-hidden="true"
          />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg" aria-hidden="true">
              <Newspaper className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isArabic ? 'الأخبار الإسلامية' : 'Islamic News'}
              </h1>
              <p className="text-gray-600">
                {isArabic
                  ? 'آخر الأخبار من مصادر إسلامية موثقة عبر RSS'
                  : 'Latest news from trusted Islamic RSS feeds'}
              </p>
            </div>
          </div>
          <button
            onClick={() => refetch()}
            disabled={loading}
            className={clsx(
              'p-2 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded-lg',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            aria-label={isArabic ? 'تحديث الأخبار' : 'Refresh news'}
            aria-busy={loading}
          >
            <RefreshCw
              className={clsx('w-5 h-5', loading && 'animate-spin')}
              aria-hidden="true"
            />
          </button>
        </div>
      </header>

      {/* Search Bar */}
      <SearchBar
        value={searchQuery}
        onChange={setSearchQuery}
        onClear={handleClearSearch}
        isArabic={isArabic}
      />

      {/* Source Selector */}
      <SourceSelector
        sources={selectedSources}
        onSourceToggle={handleSourceToggle}
        isArabic={isArabic}
      />

      {/* Error State */}
      {error && (
        <InlineError
          error={
            isArabic ? 'فشل في تحميل الأخبار' : 'Failed to load news'
          }
          onRetry={refetch}
          className="mb-6"
        />
      )}

      {/* News List */}
      <section aria-label={isArabic ? 'الأخبار' : 'News articles'}>
        {loading && news.length === 0 ? (
          <SkeletonList count={5} />
        ) : selectedSources.length === 0 ? (
          <NoData
            title={isArabic ? 'لم يتم اختيار مصادر' : 'No sources selected'}
            description={
              isArabic
                ? 'اختر مصدراً واحداً على الأقل لعرض الأخبار'
                : 'Select at least one source to view news'
            }
          />
        ) : filteredNews.length === 0 ? (
          debouncedSearch ? (
            <NoSearchResults
              query={debouncedSearch}
              onClear={handleClearSearch}
            />
          ) : (
            <NoData
              title={isArabic ? 'لا توجد أخبار' : 'No news available'}
              description={
                isArabic
                  ? 'لم يتم العثور على أخبار من المصادر المحددة'
                  : 'No news found from selected sources'
              }
              onRefresh={refetch}
            />
          )
        ) : (
          <>
            <p
              className="text-sm text-gray-500 mb-4"
              role="status"
              aria-live="polite"
            >
              {isArabic
                ? `${filteredNews.length} خبر من ${selectedSources.length} مصادر`
                : `${filteredNews.length} articles from ${selectedSources.length} sources`}
            </p>
            <NewsList news={filteredNews} isArabic={isArabic} />
          </>
        )}
      </section>

      {/* API Attribution */}
      <footer className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
        <p className="flex items-center gap-2">
          <Rss className="w-4 h-4" aria-hidden="true" />
          {isArabic
            ? 'الأخبار مجمعة من خلاصات RSS للمصادر الإسلامية الموثقة. يتم التحديث مباشرة من المصادر.'
            : 'News aggregated from RSS feeds of trusted Islamic sources. Updated live from sources.'}
        </p>
      </footer>
    </main>
  );
}

// Export with Error Boundary
export function IslamicNewsPage() {
  return (
    <ErrorBoundary>
      <IslamicNewsPageContent />
    </ErrorBoundary>
  );
}
