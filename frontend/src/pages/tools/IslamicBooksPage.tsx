/**
 * Islamic Books Page - FANG Best Practices Implementation
 *
 * Features:
 * - Custom hooks for book search and filter management
 * - Memoized components for optimal re-renders
 * - Debounced search to reduce API calls
 * - Persistent filter preferences
 * - Error boundary protection
 * - Loading skeletons
 * - Full ARIA accessibility
 * - Infinite scroll ready
 */

import { useState, useCallback, memo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  Search,
  Download,
  ExternalLink,
  Filter,
  User,
  Calendar,
  Library,
  Eye,
  AlertCircle,
  X,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import {
  searchIslamicBooks,
  getCollectionBooks,
  ISLAMIC_COLLECTIONS,
  type ArchiveBook,
} from '../../lib/islamicApis';
import { useAsync } from '../../hooks/useAsync';
import { useDebounce } from '../../hooks/useDebounce';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import {
  ErrorBoundary,
  InlineError,
  SkeletonCard,
  LoadingSpinner,
  NoSearchResults,
} from '../../components/ui';
import clsx from 'clsx';

// ============================================
// Constants
// ============================================

const CATEGORIES = [
  { id: 'all', name_en: 'All Books', name_ar: 'كل الكتب', query: '' },
  { id: 'quran', name_en: 'Quran & Tafsir', name_ar: 'القرآن والتفسير', query: 'quran OR tafsir OR تفسير' },
  { id: 'hadith', name_en: 'Hadith', name_ar: 'الحديث', query: 'hadith OR حديث OR bukhari OR muslim' },
  { id: 'fiqh', name_en: 'Fiqh', name_ar: 'الفقه', query: 'fiqh OR فقه OR jurisprudence' },
  { id: 'aqeedah', name_en: 'Aqeedah', name_ar: 'العقيدة', query: 'aqeedah OR عقيدة OR creed OR belief' },
  { id: 'seerah', name_en: 'Seerah', name_ar: 'السيرة', query: 'seerah OR سيرة OR prophet biography' },
  { id: 'history', name_en: 'Islamic History', name_ar: 'التاريخ الإسلامي', query: 'islamic history OR تاريخ' },
  { id: 'spirituality', name_en: 'Spirituality', name_ar: 'التزكية', query: 'spirituality OR تزكية OR ihya' },
] as const;

const LANGUAGES = [
  { id: 'all', name_en: 'All Languages', name_ar: 'كل اللغات', code: '' },
  { id: 'arabic', name_en: 'Arabic', name_ar: 'العربية', code: 'ara' },
  { id: 'english', name_en: 'English', name_ar: 'الإنجليزية', code: 'eng' },
  { id: 'urdu', name_en: 'Urdu', name_ar: 'الأردية', code: 'urd' },
  { id: 'french', name_en: 'French', name_ar: 'الفرنسية', code: 'fre' },
  { id: 'indonesian', name_en: 'Indonesian', name_ar: 'الإندونيسية', code: 'ind' },
] as const;

const SORT_OPTIONS = [
  { id: 'downloads desc', name_en: 'Most Popular', name_ar: 'الأكثر تحميلاً' },
  { id: 'date desc', name_en: 'Newest', name_ar: 'الأحدث' },
  { id: 'titleSorter asc', name_en: 'Title (A-Z)', name_ar: 'العنوان (أ-ي)' },
] as const;

const BOOKS_PER_PAGE = 24;

// ============================================
// Types
// ============================================

interface BookFilters {
  category: string;
  language: string;
  sort: string;
}

interface SearchState {
  books: ArchiveBook[];
  totalResults: number;
  selectedCollection: string | null;
}

// ============================================
// Custom Hooks
// ============================================

function useBookFilters() {
  const [filters, setFilters] = useLocalStorage<BookFilters>('islamic-books-filters', {
    category: 'all',
    language: 'all',
    sort: 'downloads desc',
  });

  const updateFilter = useCallback(
    <K extends keyof BookFilters>(key: K, value: BookFilters[K]) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
    },
    [setFilters]
  );

  const resetFilters = useCallback(() => {
    setFilters({
      category: 'all',
      language: 'all',
      sort: 'downloads desc',
    });
  }, [setFilters]);

  return { filters, updateFilter, resetFilters };
}

function useBookSearch(filters: BookFilters, searchQuery: string) {
  const [state, setState] = useState<SearchState>({
    books: [],
    totalResults: 0,
    selectedCollection: null,
  });

  const searchBooks = useCallback(async (): Promise<SearchState> => {
    const categoryQuery = CATEGORIES.find((c) => c.id === filters.category)?.query || '';
    const languageCode = LANGUAGES.find((l) => l.id === filters.language)?.code;
    const query = searchQuery || categoryQuery || 'islamic';

    const result = await searchIslamicBooks(query, {
      language: languageCode,
      rows: BOOKS_PER_PAGE,
      sort: filters.sort as 'downloads desc' | 'date desc' | 'titleSorter asc',
    });

    return {
      books: result.books,
      totalResults: result.totalResults,
      selectedCollection: null,
    };
  }, [filters, searchQuery]);

  const {
    isPending,
    error,
    execute: executeSearch,
  } = useAsync(searchBooks, {
    onSuccess: (data) => setState(data),
  });

  const loadCollection = useCallback(
    async (collectionId: string) => {
      const collectionBooks = await getCollectionBooks(collectionId, BOOKS_PER_PAGE);
      setState({
        books: collectionBooks,
        totalResults: collectionBooks.length,
        selectedCollection: collectionId,
      });
    },
    []
  );

  const {
    isPending: loadingCollection,
    error: collectionError,
    execute: executeLoadCollection,
  } = useAsync(loadCollection);

  // Load popular books on mount
  useEffect(() => {
    executeSearch();
  }, []);

  return {
    ...state,
    isLoading: isPending || loadingCollection,
    error: error || collectionError,
    search: executeSearch,
    loadCollection: executeLoadCollection,
  };
}

// ============================================
// Utility Functions
// ============================================

function formatDownloads(count?: number): string {
  if (!count) return '';
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
  return count.toString();
}

// ============================================
// Memoized Components
// ============================================

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  isLoading: boolean;
  isArabic: boolean;
}

const SearchBar = memo(function SearchBar({
  value,
  onChange,
  onSearch,
  isLoading,
  isArabic,
}: SearchBarProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onSearch();
    }
  };

  return (
    <div className="mb-6">
      <label htmlFor="book-search" className="sr-only">
        {isArabic ? 'البحث عن كتب' : 'Search for books'}
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
          id="book-search"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isArabic ? 'ابحث عن كتب في Internet Archive...' : 'Search books on Internet Archive...'}
          className={clsx(
            'w-full py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
            isArabic ? 'pr-10 pl-24' : 'pl-10 pr-24'
          )}
          aria-describedby="search-hint"
        />
        <button
          onClick={onSearch}
          disabled={isLoading}
          className={clsx(
            'absolute top-1/2 transform -translate-y-1/2 px-4 py-1.5 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2',
            isArabic ? 'left-2' : 'right-2'
          )}
          aria-label={isArabic ? 'بحث' : 'Search'}
        >
          {isLoading ? <LoadingSpinner size="sm" /> : isArabic ? 'بحث' : 'Search'}
        </button>
      </div>
      <p id="search-hint" className="sr-only">
        {isArabic ? 'اضغط Enter للبحث' : 'Press Enter to search'}
      </p>
    </div>
  );
});

interface FiltersRowProps {
  filters: BookFilters;
  onFilterChange: <K extends keyof BookFilters>(key: K, value: BookFilters[K]) => void;
  onApply: () => void;
  onReset: () => void;
  isArabic: boolean;
}

const FiltersRow = memo(function FiltersRow({
  filters,
  onFilterChange,
  onApply,
  onReset,
  isArabic,
}: FiltersRowProps) {
  const hasActiveFilters = filters.category !== 'all' || filters.language !== 'all';

  return (
    <div
      className="mb-6 flex flex-wrap items-center gap-4"
      role="group"
      aria-label={isArabic ? 'فلاتر البحث' : 'Search filters'}
    >
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-500" aria-hidden="true" />
        <label htmlFor="category-filter" className="sr-only">
          {isArabic ? 'التصنيف' : 'Category'}
        </label>
        <select
          id="category-filter"
          value={filters.category}
          onChange={(e) => onFilterChange('category', e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {isArabic ? cat.name_ar : cat.name_en}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="language-filter" className="sr-only">
          {isArabic ? 'اللغة' : 'Language'}
        </label>
        <select
          id="language-filter"
          value={filters.language}
          onChange={(e) => onFilterChange('language', e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.id} value={lang.id}>
              {isArabic ? lang.name_ar : lang.name_en}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="sort-filter" className="sr-only">
          {isArabic ? 'الترتيب' : 'Sort by'}
        </label>
        <select
          id="sort-filter"
          value={filters.sort}
          onChange={(e) => onFilterChange('sort', e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {isArabic ? opt.name_ar : opt.name_en}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={onApply}
        className="px-4 py-1.5 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-amber-500"
      >
        {isArabic ? 'تطبيق' : 'Apply'}
      </button>

      {hasActiveFilters && (
        <button
          onClick={onReset}
          className="px-3 py-1.5 text-gray-600 hover:text-gray-800 text-sm flex items-center gap-1 focus:outline-none focus:underline"
          aria-label={isArabic ? 'إعادة ضبط الفلاتر' : 'Reset filters'}
        >
          <X className="w-4 h-4" aria-hidden="true" />
          {isArabic ? 'إعادة ضبط' : 'Reset'}
        </button>
      )}
    </div>
  );
});

interface CollectionSelectorProps {
  selectedCollection: string | null;
  onSelect: (collectionId: string) => void;
  isArabic: boolean;
}

const CollectionSelector = memo(function CollectionSelector({
  selectedCollection,
  onSelect,
  isArabic,
}: CollectionSelectorProps) {
  return (
    <div className="mb-8" role="group" aria-label={isArabic ? 'مجموعات مميزة' : 'Featured Collections'}>
      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <Library className="w-5 h-5" aria-hidden="true" />
        {isArabic ? 'مجموعات مميزة' : 'Featured Collections'}
      </h3>
      <div className="flex flex-wrap gap-2" role="radiogroup">
        {ISLAMIC_COLLECTIONS.map((collection) => (
          <button
            key={collection.id}
            onClick={() => onSelect(collection.id)}
            role="radio"
            aria-checked={selectedCollection === collection.id}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500',
              selectedCollection === collection.id
                ? 'bg-amber-600 text-white'
                : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
            )}
          >
            {isArabic ? collection.name_ar : collection.name_en}
          </button>
        ))}
      </div>
    </div>
  );
});

interface BookCardProps {
  book: ArchiveBook;
  isArabic: boolean;
}

const BookCard = memo(function BookCard({ book, isArabic }: BookCardProps) {
  const [imageError, setImageError] = useState(false);

  return (
    <article
      className="card border border-gray-200 hover:border-amber-300 transition-colors group"
      aria-label={book.title}
    >
      {/* Thumbnail */}
      <div className="relative -mx-6 -mt-6 mb-4 aspect-[4/3] bg-gray-100 overflow-hidden">
        {!imageError ? (
          <img
            src={book.imageUrl}
            alt=""
            aria-hidden="true"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
            onError={() => setImageError(true)}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-amber-50">
            <BookOpen className="w-16 h-16 text-amber-300" aria-hidden="true" />
          </div>
        )}
        {book.downloads && (
          <div
            className="absolute bottom-2 right-2 px-2 py-1 bg-black/70 text-white text-xs rounded-full flex items-center gap-1"
            aria-label={`${formatDownloads(book.downloads)} downloads`}
          >
            <Download className="w-3 h-3" aria-hidden="true" />
            {formatDownloads(book.downloads)}
          </div>
        )}
      </div>

      {/* Book Info */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2 group-hover:text-amber-600 transition-colors">
          {book.title}
        </h3>
        {book.creator && (
          <p className="text-sm text-gray-500 flex items-center gap-1 mb-2">
            <User className="w-3 h-3" aria-hidden="true" />
            <span className="truncate">{book.creator}</span>
          </p>
        )}
        {book.description && (
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">{book.description}</p>
        )}

        {/* Meta Info */}
        <div className="flex flex-wrap gap-2 mb-4 text-xs">
          {book.date && (
            <span className="flex items-center gap-1 text-gray-500">
              <Calendar className="w-3 h-3" aria-hidden="true" />
              <time dateTime={book.date.slice(0, 4)}>{book.date.slice(0, 4)}</time>
            </span>
          )}
          {book.language && (
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
              {book.language}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <a
            href={book.readUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            aria-label={`${isArabic ? 'قراءة' : 'Read'} ${book.title}`}
          >
            <Eye className="w-4 h-4" aria-hidden="true" />
            {isArabic ? 'قراءة' : 'Read'}
          </a>
          {book.downloadUrl && (
            <a
              href={book.downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              aria-label={`${isArabic ? 'تحميل' : 'Download'} ${book.title}`}
            >
              <Download className="w-4 h-4" aria-hidden="true" />
            </a>
          )}
        </div>
      </div>
    </article>
  );
});

interface BooksGridProps {
  books: ArchiveBook[];
  isLoading: boolean;
  isArabic: boolean;
}

const BooksGrid = memo(function BooksGrid({ books, isLoading, isArabic }: BooksGridProps) {
  if (isLoading) {
    return (
      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        aria-busy="true"
        aria-label={isArabic ? 'جاري التحميل' : 'Loading'}
      >
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (books.length === 0) {
    return <NoSearchResults className="my-8" />;
  }

  return (
    <div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      role="feed"
      aria-label={isArabic ? 'قائمة الكتب' : 'Books list'}
    >
      {books.map((book) => (
        <BookCard key={book.identifier} book={book} isArabic={isArabic} />
      ))}
    </div>
  );
});

interface ResultsInfoProps {
  totalResults: number;
  isArabic: boolean;
}

const ResultsInfo = memo(function ResultsInfo({ totalResults, isArabic }: ResultsInfoProps) {
  if (totalResults === 0) return null;

  return (
    <p className="text-sm text-gray-500 mb-4" aria-live="polite">
      {isArabic
        ? `${totalResults.toLocaleString('ar-EG')} كتاب متاح`
        : `${totalResults.toLocaleString()} books available`}
    </p>
  );
});

// ============================================
// Main Component
// ============================================

function IslamicBooksPageContent() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  // Search query with debounce
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearchQuery = useDebounce(searchInput, 300);

  // Filters
  const { filters, updateFilter, resetFilters } = useBookFilters();

  // Book search
  const { books, totalResults, selectedCollection, isLoading, error, search, loadCollection } =
    useBookSearch(filters, debouncedSearchQuery);

  // Handle search
  const handleSearch = useCallback(() => {
    search();
  }, [search]);

  // Handle collection selection
  const handleCollectionSelect = useCallback(
    (collectionId: string) => {
      setSearchInput('');
      loadCollection(collectionId);
    },
    [loadCollection]
  );

  // Handle filter reset
  const handleResetFilters = useCallback(() => {
    resetFilters();
    setSearchInput('');
    search();
  }, [resetFilters, search]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <header className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 focus:outline-none focus:underline"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} aria-hidden="true" />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-amber-100 rounded-lg" aria-hidden="true">
            <BookOpen className="w-8 h-8 text-amber-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isArabic ? 'الكتب الإسلامية' : 'Islamic Books'}
            </h1>
            <p className="text-gray-600">
              {isArabic
                ? 'مكتبة رقمية مجانية من Internet Archive'
                : 'Free digital library from Internet Archive'}
            </p>
          </div>
        </div>
      </header>

      {/* Search Bar */}
      <SearchBar
        value={searchInput}
        onChange={setSearchInput}
        onSearch={handleSearch}
        isLoading={isLoading}
        isArabic={isArabic}
      />

      {/* Filters Row */}
      <FiltersRow
        filters={filters}
        onFilterChange={updateFilter}
        onApply={handleSearch}
        onReset={handleResetFilters}
        isArabic={isArabic}
      />

      {/* Featured Collections */}
      <CollectionSelector
        selectedCollection={selectedCollection}
        onSelect={handleCollectionSelect}
        isArabic={isArabic}
      />

      {/* Results Info */}
      {!isLoading && <ResultsInfo totalResults={totalResults} isArabic={isArabic} />}

      {/* Error State */}
      {error && (
        <div className="mb-6">
          <InlineError
            error={isArabic ? 'فشل في تحميل الكتب' : 'Failed to load books'}
            onRetry={handleSearch}
          />
        </div>
      )}

      {/* Books Grid */}
      <BooksGrid books={books} isLoading={isLoading} isArabic={isArabic} />

      {/* Internet Archive Attribution */}
      <footer className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <Library className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          <p>
            {isArabic
              ? 'الكتب مقدمة مجاناً من Internet Archive. جميع الكتب في المجال العام أو برخص مفتوحة.'
              : 'Books provided free by Internet Archive. All books are public domain or openly licensed.'}
          </p>
        </div>
        <a
          href="https://archive.org"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 mt-2 text-amber-600 hover:underline focus:outline-none focus:underline"
        >
          archive.org <ExternalLink className="w-3 h-3" aria-hidden="true" />
        </a>
      </footer>
    </div>
  );
}

// ============================================
// Export with Error Boundary
// ============================================

export function IslamicBooksPage() {
  const { language } = useLanguageStore();

  return (
    <ErrorBoundary
      fallback={
        <div className="max-w-6xl mx-auto px-4 py-16 text-center">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {language === 'ar' ? 'حدث خطأ غير متوقع' : 'Something went wrong'}
          </h2>
          <p className="text-gray-600 mb-4">
            {language === 'ar'
              ? 'يرجى تحديث الصفحة والمحاولة مرة أخرى'
              : 'Please refresh the page and try again'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
          >
            {language === 'ar' ? 'تحديث الصفحة' : 'Refresh Page'}
          </button>
        </div>
      }
    >
      <IslamicBooksPageContent />
    </ErrorBoundary>
  );
}
