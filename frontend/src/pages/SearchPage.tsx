import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, ExternalLink, BarChart3, BookOpen, Hash, CheckCircle, AlertCircle,
  ChevronDown, ChevronUp, Filter, BookMarked, Sparkles, Languages, Info,
  GitBranch, TrendingUp, Layers, X, Loader2
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { useSearchHistoryStore } from '../stores/searchHistoryStore';
import { t } from '../i18n/translations';
import {
  quranApi, EnhancedSearchResponse, SearchMatch, WordAnalyticsResponse,
  SimilarVersesResponse, ConceptEvolutionResponse,
  ThemeInfo
} from '../lib/api';
import clsx from 'clsx';

// =============================================================================
// TYPES
// =============================================================================

interface SuraInfo {
  sura_no: number;
  name_ar: string;
  name_en: string;
  total_verses: number;
}

interface SearchError {
  code: string;
  message_ar: string;
  message_en: string;
}

// =============================================================================
// ERROR CODES
// =============================================================================

const ERROR_CODES: Record<string, SearchError> = {
  NO_RESULTS: {
    code: 'NO_RESULTS',
    message_ar: 'لم يتم العثور على نتائج لهذا البحث',
    message_en: 'No results found for this search',
  },
  INVALID_QUERY: {
    code: 'INVALID_QUERY',
    message_ar: 'صيغة البحث غير صالحة. يرجى إدخال كلمة عربية صحيحة',
    message_en: 'Invalid query format. Please enter a valid Arabic word',
  },
  QUERY_TOO_SHORT: {
    code: 'QUERY_TOO_SHORT',
    message_ar: 'كلمة البحث قصيرة جداً. يرجى إدخال كلمتين على الأقل',
    message_en: 'Search query too short. Please enter at least 2 characters',
  },
  SERVER_ERROR: {
    code: 'SERVER_ERROR',
    message_ar: 'خطأ في الخادم. يرجى المحاولة مرة أخرى لاحقاً',
    message_en: 'Server error. Please try again later',
  },
  NETWORK_ERROR: {
    code: 'NETWORK_ERROR',
    message_ar: 'خطأ في الاتصال. تحقق من اتصالك بالإنترنت',
    message_en: 'Network error. Please check your internet connection',
  },
  SURA_NOT_FOUND: {
    code: 'SURA_NOT_FOUND',
    message_ar: 'السورة المحددة غير موجودة',
    message_en: 'Selected sura not found',
  },
};

// =============================================================================
// AUTOCOMPLETE SUGGESTIONS - Expanded Categories
// =============================================================================

const AUTOCOMPLETE_SUGGESTIONS = [
  // Names of Allah (أسماء الله الحسنى)
  { word: 'الله', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الرحمن', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الرحيم', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الملك', category: 'names', category_ar: 'أسماء الله' },
  { word: 'القدوس', category: 'names', category_ar: 'أسماء الله' },
  { word: 'السلام', category: 'names', category_ar: 'أسماء الله' },
  { word: 'المؤمن', category: 'names', category_ar: 'أسماء الله' },
  { word: 'العزيز', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الجبار', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الخالق', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الغفور', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الرزاق', category: 'names', category_ar: 'أسماء الله' },
  { word: 'السميع', category: 'names', category_ar: 'أسماء الله' },
  { word: 'البصير', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الحكيم', category: 'names', category_ar: 'أسماء الله' },
  { word: 'العليم', category: 'names', category_ar: 'أسماء الله' },
  { word: 'الودود', category: 'names', category_ar: 'أسماء الله' },
  { word: 'التواب', category: 'names', category_ar: 'أسماء الله' },

  // Prophets (الأنبياء)
  { word: 'محمد', category: 'prophet', category_ar: 'نبي' },
  { word: 'موسى', category: 'prophet', category_ar: 'نبي' },
  { word: 'عيسى', category: 'prophet', category_ar: 'نبي' },
  { word: 'إبراهيم', category: 'prophet', category_ar: 'نبي' },
  { word: 'نوح', category: 'prophet', category_ar: 'نبي' },
  { word: 'يوسف', category: 'prophet', category_ar: 'نبي' },
  { word: 'آدم', category: 'prophet', category_ar: 'نبي' },
  { word: 'داود', category: 'prophet', category_ar: 'نبي' },
  { word: 'سليمان', category: 'prophet', category_ar: 'نبي' },
  { word: 'يعقوب', category: 'prophet', category_ar: 'نبي' },
  { word: 'إسحاق', category: 'prophet', category_ar: 'نبي' },
  { word: 'إسماعيل', category: 'prophet', category_ar: 'نبي' },
  { word: 'أيوب', category: 'prophet', category_ar: 'نبي' },
  { word: 'يونس', category: 'prophet', category_ar: 'نبي' },
  { word: 'زكريا', category: 'prophet', category_ar: 'نبي' },
  { word: 'يحيى', category: 'prophet', category_ar: 'نبي' },
  { word: 'هارون', category: 'prophet', category_ar: 'نبي' },
  { word: 'لوط', category: 'prophet', category_ar: 'نبي' },
  { word: 'شعيب', category: 'prophet', category_ar: 'نبي' },
  { word: 'صالح', category: 'prophet', category_ar: 'نبي' },
  { word: 'هود', category: 'prophet', category_ar: 'نبي' },

  // Themes (موضوعات قرآنية)
  { word: 'رحمة', category: 'theme', category_ar: 'موضوع' },
  { word: 'صبر', category: 'theme', category_ar: 'موضوع' },
  { word: 'إيمان', category: 'theme', category_ar: 'موضوع' },
  { word: 'توبة', category: 'theme', category_ar: 'موضوع' },
  { word: 'هدى', category: 'theme', category_ar: 'موضوع' },
  { word: 'تقوى', category: 'theme', category_ar: 'موضوع' },
  { word: 'شكر', category: 'theme', category_ar: 'موضوع' },
  { word: 'عدل', category: 'theme', category_ar: 'موضوع' },
  { word: 'توكل', category: 'theme', category_ar: 'موضوع' },
  { word: 'يقين', category: 'theme', category_ar: 'موضوع' },
  { word: 'خشوع', category: 'theme', category_ar: 'موضوع' },
  { word: 'تواضع', category: 'theme', category_ar: 'موضوع' },
  { word: 'إحسان', category: 'theme', category_ar: 'موضوع' },
  { word: 'عبادة', category: 'theme', category_ar: 'موضوع' },
  { word: 'ذكر', category: 'theme', category_ar: 'موضوع' },
  { word: 'استغفار', category: 'theme', category_ar: 'موضوع' },
  { word: 'رزق', category: 'theme', category_ar: 'موضوع' },
  { word: 'قدر', category: 'theme', category_ar: 'موضوع' },
  { word: 'نصر', category: 'theme', category_ar: 'موضوع' },
  { word: 'فتنة', category: 'theme', category_ar: 'موضوع' },

  // Historical Events (أحداث تاريخية)
  { word: 'بدر', category: 'event', category_ar: 'حدث' },
  { word: 'أحد', category: 'event', category_ar: 'حدث' },
  { word: 'الأحزاب', category: 'event', category_ar: 'حدث' },
  { word: 'الفتح', category: 'event', category_ar: 'حدث' },
  { word: 'حنين', category: 'event', category_ar: 'حدث' },
  { word: 'الهجرة', category: 'event', category_ar: 'حدث' },
  { word: 'الإسراء', category: 'event', category_ar: 'حدث' },
  { word: 'المعراج', category: 'event', category_ar: 'حدث' },
  { word: 'الطوفان', category: 'event', category_ar: 'حدث' },
  { word: 'غرق فرعون', category: 'event', category_ar: 'حدث' },

  // Miracles (معجزات)
  { word: 'معجزة', category: 'miracle', category_ar: 'معجزة' },
  { word: 'آية', category: 'miracle', category_ar: 'معجزة' },
  { word: 'عصا موسى', category: 'miracle', category_ar: 'معجزة' },
  { word: 'انشقاق البحر', category: 'miracle', category_ar: 'معجزة' },
  { word: 'ناقة صالح', category: 'miracle', category_ar: 'معجزة' },
  { word: 'إحياء الموتى', category: 'miracle', category_ar: 'معجزة' },
  { word: 'مائدة عيسى', category: 'miracle', category_ar: 'معجزة' },
  { word: 'انشقاق القمر', category: 'miracle', category_ar: 'معجزة' },

  // Places (أماكن)
  { word: 'جنة', category: 'place', category_ar: 'مكان' },
  { word: 'نار', category: 'place', category_ar: 'مكان' },
  { word: 'أرض', category: 'place', category_ar: 'مكان' },
  { word: 'سماء', category: 'place', category_ar: 'مكان' },
  { word: 'مكة', category: 'place', category_ar: 'مكان' },
  { word: 'المدينة', category: 'place', category_ar: 'مكان' },
  { word: 'بيت المقدس', category: 'place', category_ar: 'مكان' },
  { word: 'الكعبة', category: 'place', category_ar: 'مكان' },
  { word: 'مصر', category: 'place', category_ar: 'مكان' },
  { word: 'طور سيناء', category: 'place', category_ar: 'مكان' },
  { word: 'البحر', category: 'place', category_ar: 'مكان' },
  { word: 'الجبل', category: 'place', category_ar: 'مكان' },

  // Acts of Worship (العبادات)
  { word: 'صلاة', category: 'action', category_ar: 'عبادة' },
  { word: 'زكاة', category: 'action', category_ar: 'عبادة' },
  { word: 'صيام', category: 'action', category_ar: 'عبادة' },
  { word: 'حج', category: 'action', category_ar: 'عبادة' },
  { word: 'دعاء', category: 'action', category_ar: 'عبادة' },
  { word: 'قراءة', category: 'action', category_ar: 'عبادة' },
  { word: 'سجود', category: 'action', category_ar: 'عبادة' },
  { word: 'ركوع', category: 'action', category_ar: 'عبادة' },
  { word: 'تسبيح', category: 'action', category_ar: 'عبادة' },

  // Quranic Figures (شخصيات قرآنية)
  { word: 'فرعون', category: 'figure', category_ar: 'شخصية' },
  { word: 'قارون', category: 'figure', category_ar: 'شخصية' },
  { word: 'هامان', category: 'figure', category_ar: 'شخصية' },
  { word: 'إبليس', category: 'figure', category_ar: 'شخصية' },
  { word: 'مريم', category: 'figure', category_ar: 'شخصية' },
  { word: 'آسية', category: 'figure', category_ar: 'شخصية' },
  { word: 'لقمان', category: 'figure', category_ar: 'شخصية' },
  { word: 'ذو القرنين', category: 'figure', category_ar: 'شخصية' },
  { word: 'أصحاب الكهف', category: 'figure', category_ar: 'شخصية' },
  { word: 'أصحاب الفيل', category: 'figure', category_ar: 'شخصية' },

  // Nations & Peoples (الأمم والأقوام)
  { word: 'بني إسرائيل', category: 'nation', category_ar: 'أمة' },
  { word: 'قوم نوح', category: 'nation', category_ar: 'أمة' },
  { word: 'قوم عاد', category: 'nation', category_ar: 'أمة' },
  { word: 'قوم ثمود', category: 'nation', category_ar: 'أمة' },
  { word: 'قوم لوط', category: 'nation', category_ar: 'أمة' },
  { word: 'أصحاب مدين', category: 'nation', category_ar: 'أمة' },
  { word: 'المنافقون', category: 'nation', category_ar: 'أمة' },
  { word: 'المشركون', category: 'nation', category_ar: 'أمة' },
  { word: 'أهل الكتاب', category: 'nation', category_ar: 'أمة' },

  // Afterlife Concepts (مفاهيم الآخرة)
  { word: 'يوم القيامة', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'البعث', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'الحساب', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'الميزان', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'الصراط', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'الشفاعة', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'الحور العين', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'النعيم', category: 'afterlife', category_ar: 'الآخرة' },
  { word: 'العذاب', category: 'afterlife', category_ar: 'الآخرة' },
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function SearchPage() {
  const { language } = useLanguageStore();
  const { recordSearch, recordVerseClick: _recordVerseClick } = useSearchHistoryStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EnhancedSearchResponse | null>(null);
  const [analytics, setAnalytics] = useState<WordAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<SearchError | null>(null);

  // Sura metadata
  const [suras, setSuras] = useState<SuraInfo[]>([]);
  const [loadingSuras, setLoadingSuras] = useState(true);

  // Search options
  const [includeSemantic, setIncludeSemantic] = useState(true);
  const [selectedSura, setSelectedSura] = useState<number | undefined>(undefined);
  const [selectedTheme, setSelectedTheme] = useState<string | undefined>(undefined);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Semantic search features
  const [similarVerses, setSimilarVerses] = useState<SimilarVersesResponse | null>(null);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [selectedVerseForSimilar, setSelectedVerseForSimilar] = useState<{ sura: number; aya: number } | null>(null);
  const [conceptEvolution, setConceptEvolution] = useState<ConceptEvolutionResponse | null>(null);
  const [loadingEvolution, setLoadingEvolution] = useState(false);
  const [showEvolution, setShowEvolution] = useState(false);
  const [availableThemes, setAvailableThemes] = useState<ThemeInfo[]>([]);

  // Autocomplete
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompleteResults, setAutocompleteResults] = useState<typeof AUTOCOMPLETE_SUGGESTIONS>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const autocompleteRef = useRef<HTMLDivElement>(null);

  // Pagination
  const [offset, setOffset] = useState(0);
  const limit = 20;

  // Load sura metadata and themes on mount
  useEffect(() => {
    async function loadSuraMetadata() {
      try {
        const res = await fetch('/api/v1/quran/metadata');
        const data = await res.json();
        setSuras(data.suras || []);
      } catch (err) {
        console.error('Failed to load sura metadata:', err);
      } finally {
        setLoadingSuras(false);
      }
    }
    async function loadThemes() {
      try {
        const res = await quranApi.getAvailableThemes();
        setAvailableThemes(res.data.themes || []);
      } catch (err) {
        console.error('Failed to load themes:', err);
      }
    }
    loadSuraMetadata();
    loadThemes();
  }, []);

  // Find similar verses
  const findSimilarVerses = async (suraNo: number, ayaNo: number) => {
    setLoadingSimilar(true);
    setSelectedVerseForSimilar({ sura: suraNo, aya: ayaNo });
    setSimilarVerses(null);
    try {
      const res = await quranApi.findSimilarVerses(suraNo, ayaNo, { top_k: 10 });
      setSimilarVerses(res.data);
    } catch (err) {
      console.error('Failed to find similar verses:', err);
    } finally {
      setLoadingSimilar(false);
    }
  };

  // Get concept evolution
  const getConceptEvolution = async (concept: string) => {
    setLoadingEvolution(true);
    setShowEvolution(true);
    setConceptEvolution(null);
    try {
      const res = await quranApi.getConceptEvolution(concept, true);
      setConceptEvolution(res.data);
    } catch (err) {
      console.error('Failed to get concept evolution:', err);
    } finally {
      setLoadingEvolution(false);
    }
  };

  // Handle click outside autocomplete
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        autocompleteRef.current &&
        !autocompleteRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowAutocomplete(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter autocomplete suggestions
  const handleQueryChange = useCallback((value: string) => {
    setQuery(value);
    if (value.trim().length >= 1) {
      const filtered = AUTOCOMPLETE_SUGGESTIONS.filter(
        (s) => s.word.includes(value) || value.includes(s.word)
      ).slice(0, 8);
      setAutocompleteResults(filtered);
      setShowAutocomplete(filtered.length > 0);
    } else {
      setShowAutocomplete(false);
    }
  }, []);

  // Select autocomplete suggestion
  const selectSuggestion = (word: string) => {
    setQuery(word);
    setShowAutocomplete(false);
    // Trigger search
    setTimeout(() => handleSearch(undefined, 0), 100);
  };

  // Parse error response
  const parseError = (err: unknown): SearchError => {
    if (err && typeof err === 'object') {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } }; message?: string };

      if (axiosErr.response?.status === 404) {
        return ERROR_CODES.NO_RESULTS;
      }
      if (axiosErr.response?.status === 400) {
        return ERROR_CODES.INVALID_QUERY;
      }
      if (axiosErr.response?.status === 500) {
        return ERROR_CODES.SERVER_ERROR;
      }
      if (axiosErr.message?.includes('Network')) {
        return ERROR_CODES.NETWORK_ERROR;
      }
    }
    return ERROR_CODES.SERVER_ERROR;
  };

  // Validate query
  const validateQuery = (q: string): SearchError | null => {
    if (q.trim().length < 2) {
      return ERROR_CODES.QUERY_TOO_SHORT;
    }
    // Check if contains Arabic characters
    if (!/[\u0600-\u06FF]/.test(q)) {
      return ERROR_CODES.INVALID_QUERY;
    }
    return null;
  };

  async function handleSearch(e?: React.FormEvent, newOffset: number = 0) {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    // Validate query
    const validationError = validateQuery(query);
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setOffset(newOffset);
    setShowAutocomplete(false);

    try {
      const searchResult = await quranApi.enhancedSearch(query, {
        limit,
        offset: newOffset,
        sura: selectedSura,
        include_semantic: includeSemantic,
        theme: selectedTheme,
      });

      // Check for no results
      if (searchResult.data.total_matches === 0) {
        setError(ERROR_CODES.NO_RESULTS);
        setResults(null);
        setAnalytics(null);
        return;
      }

      // Fetch analytics only on first search
      let analyticsResult = null;
      if (newOffset === 0) {
        try {
          analyticsResult = await quranApi.getWordAnalytics(query);
        } catch {
          console.warn('Could not fetch analytics');
        }
      }

      if (newOffset === 0) {
        setResults(searchResult.data);
        if (analyticsResult) {
          setAnalytics(analyticsResult.data);
        }
        // Record search in history
        recordSearch(query, 'text', searchResult.data.total_matches);
      } else {
        setResults(prev => prev ? {
          ...searchResult.data,
          matches: [...prev.matches, ...searchResult.data.matches],
        } : searchResult.data);
      }
    } catch (err) {
      console.error('Search error:', err);
      setError(parseError(err));
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  function handleLoadMore() {
    handleSearch(undefined, offset + limit);
  }

  // Get sura name by number
  const getSuraName = (suraNo: number): { ar: string; en: string } => {
    const sura = suras.find(s => s.sura_no === suraNo);
    return sura ? { ar: sura.name_ar, en: sura.name_en } : { ar: `سورة ${suraNo}`, en: `Sura ${suraNo}` };
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {t('search_title', language)}
        </h1>
        <p className="text-gray-600">{t('search_subtitle', language)}</p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="card mb-6">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => handleQueryChange(e.target.value)}
              onFocus={() => query.length >= 1 && autocompleteResults.length > 0 && setShowAutocomplete(true)}
              placeholder={t('search_placeholder', language)}
              className="input pl-10 w-full"
              dir="rtl"
              autoComplete="off"
            />

            {/* Autocomplete Dropdown */}
            {showAutocomplete && (
              <div
                ref={autocompleteRef}
                className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto"
              >
                {autocompleteResults.map((suggestion, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => selectSuggestion(suggestion.word)}
                    className="w-full px-4 py-2 text-right hover:bg-primary-50 flex items-center justify-between"
                    dir="rtl"
                  >
                    <span className="font-arabic text-lg">{suggestion.word}</span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                      {language === 'ar' ? suggestion.category_ar : suggestion.category}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className={clsx(
              'btn-primary flex items-center gap-2',
              (loading || !query.trim()) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {loading ? (
              <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            {t('search_button', language)}
          </button>
        </div>

        {/* Search Options */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <Filter className="w-4 h-4" />
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            <span>{language === 'ar' ? 'خيارات البحث' : 'Search Options'}</span>
          </button>

          {showFilters && (
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {/* Semantic Search Toggle */}
              <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={includeSemantic}
                  onChange={(e) => setIncludeSemantic(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div>
                  <div className="font-medium text-sm flex items-center gap-1">
                    <Sparkles className="w-4 h-4 text-primary-500" />
                    {t('search_semantic', language)}
                  </div>
                  <div className="text-xs text-gray-500">{t('search_semantic_desc', language)}</div>
                </div>
              </label>

              {/* Sura Filter with Names */}
              <div className="p-3 rounded-lg border border-gray-200">
                <label className="block text-sm font-medium mb-2">{t('search_filter_sura', language)}</label>
                <select
                  value={selectedSura || ''}
                  onChange={(e) => setSelectedSura(e.target.value ? Number(e.target.value) : undefined)}
                  className="input w-full text-sm"
                  dir={language === 'ar' ? 'rtl' : 'ltr'}
                >
                  <option value="">{t('search_all_suras', language)}</option>
                  {loadingSuras ? (
                    <option disabled>{language === 'ar' ? 'جاري التحميل...' : 'Loading...'}</option>
                  ) : (
                    suras.map((sura) => (
                      <option key={sura.sura_no} value={sura.sura_no}>
                        {sura.sura_no}. {language === 'ar' ? sura.name_ar : sura.name_en}
                      </option>
                    ))
                  )}
                </select>
              </div>

              {/* Theme Filter */}
              <div className="p-3 rounded-lg border border-gray-200">
                <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                  <Layers className="w-4 h-4 text-indigo-500" />
                  {language === 'ar' ? 'تصفية حسب الموضوع' : 'Filter by Theme'}
                </label>
                <select
                  value={selectedTheme || ''}
                  onChange={(e) => setSelectedTheme(e.target.value || undefined)}
                  className="input w-full text-sm"
                  dir={language === 'ar' ? 'rtl' : 'ltr'}
                >
                  <option value="">{language === 'ar' ? 'جميع المواضيع' : 'All Themes'}</option>
                  {availableThemes.map((theme) => (
                    <option key={theme.id} value={theme.id}>
                      {language === 'ar' ? theme.name_ar : theme.name_en}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      </form>

      {/* Error with Suggestions */}
      {error && (
        <div className="mb-6">
          {/* Error Message */}
          <div className={clsx(
            "rounded-lg p-4 border",
            error.code === 'NO_RESULTS'
              ? "bg-amber-50 border-amber-200"
              : "bg-red-50 border-red-200"
          )}>
            <div className="flex items-start gap-3">
              <AlertCircle className={clsx(
                "w-5 h-5 flex-shrink-0 mt-0.5",
                error.code === 'NO_RESULTS' ? "text-amber-500" : "text-red-500"
              )} />
              <div className="flex-1">
                <p className={clsx(
                  "font-medium",
                  error.code === 'NO_RESULTS' ? "text-amber-700" : "text-red-700"
                )}>
                  {language === 'ar' ? error.message_ar : error.message_en}
                </p>
                <p className={clsx(
                  "text-xs mt-1",
                  error.code === 'NO_RESULTS' ? "text-amber-500" : "text-red-500"
                )}>
                  {language === 'ar' ? 'رمز الخطأ' : 'Error Code'}: {error.code}
                </p>
              </div>
            </div>
          </div>

          {/* No Results Suggestions */}
          {error.code === 'NO_RESULTS' && (
            <NoResultsFeedback
              query={query}
              language={language}
              selectedSura={selectedSura}
              selectedTheme={selectedTheme}
              onSelectWord={(word) => {
                setQuery(word);
                setTimeout(() => handleSearch(undefined, 0), 100);
              }}
              onClearFilters={() => {
                setSelectedSura(undefined);
                setSelectedTheme(undefined);
                setTimeout(() => handleSearch(undefined, 0), 100);
              }}
            />
          )}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Results Summary */}
          <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg p-4 border border-primary-100">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Hash className="w-4 h-4 text-primary-600" />
                  <span className="text-sm">
                    <span className="font-semibold">{results.total_matches}</span>{' '}
                    {t('search_occurrences', language)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-600" />
                  <span className="text-sm">
                    <span className="font-semibold">{Object.keys(results.sura_distribution).length}</span>{' '}
                    {language === 'ar' ? 'سورة' : 'suras'}
                  </span>
                </div>
                {results.search_time_ms && (
                  <span className="text-xs text-gray-500">
                    {results.search_time_ms.toFixed(0)}ms
                  </span>
                )}
              </div>

              <button
                onClick={() => setShowAnalytics(!showAnalytics)}
                className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
              >
                <BarChart3 className="w-4 h-4" />
                {t('search_analytics', language)}
                {showAnalytics ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>

            {/* Related Terms */}
            {results.related_terms && results.related_terms.length > 0 && (
              <div className="mt-3 pt-3 border-t border-primary-100">
                <span className="text-xs text-gray-500 mr-2 flex items-center gap-1 inline-flex">
                  <Sparkles className="w-3 h-3" />
                  {t('search_related_terms', language)}:
                </span>
                <div className="inline-flex flex-wrap gap-1 mt-1">
                  {results.related_terms.map((term, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setQuery(term);
                        setTimeout(() => handleSearch(undefined, 0), 0);
                      }}
                      className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded hover:bg-primary-200 transition-colors"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Analytics Panel */}
          {showAnalytics && analytics && (
            <AnalyticsPanel
              analytics={analytics}
              language={language}
              suras={suras}
              onExploreEvolution={() => getConceptEvolution(query)}
            />
          )}

          {/* Similar Verses Panel */}
          {(similarVerses || loadingSimilar) && (
            <SimilarVersesPanel
              data={similarVerses}
              loading={loadingSimilar}
              language={language}
              onClose={() => {
                setSimilarVerses(null);
                setSelectedVerseForSimilar(null);
              }}
            />
          )}

          {/* Concept Evolution Panel */}
          {showEvolution && (
            <ConceptEvolutionPanel
              data={conceptEvolution}
              loading={loadingEvolution}
              language={language}
              onClose={() => {
                setShowEvolution(false);
                setConceptEvolution(null);
              }}
            />
          )}

          {/* Search Results */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-primary-600" />
              {t('search_results', language)}
            </h2>

            <div className="space-y-4">
              {results.matches.map((match) => (
                <SearchMatchCard
                  key={`${match.sura_no}-${match.aya_no}`}
                  match={match}
                  language={language}
                  getSuraName={getSuraName}
                  onFindSimilar={() => findSimilarVerses(match.sura_no, match.aya_no)}
                  isLoadingSimilar={loadingSimilar && selectedVerseForSimilar?.sura === match.sura_no && selectedVerseForSimilar?.aya === match.aya_no}
                />
              ))}
            </div>

            {/* Load More */}
            {results.matches.length < results.total_matches && (
              <div className="mt-6 text-center">
                <button
                  onClick={handleLoadMore}
                  disabled={loading}
                  className="btn-secondary"
                >
                  {loading ? (
                    <div className="animate-spin w-5 h-5 border-2 border-primary-600 border-t-transparent rounded-full mx-auto" />
                  ) : (
                    <>
                      {t('search_load_more', language)}
                      <span className="text-xs text-gray-500 ml-2">
                        ({results.matches.length}/{results.total_matches})
                      </span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sample Words (when no results) */}
      {!results && !loading && !error && (
        <SampleWordsPanel
          language={language}
          onSelectWord={(word) => {
            setQuery(word);
            setTimeout(() => handleSearch(undefined, 0), 100);
          }}
        />
      )}
    </div>
  );
}

// =============================================================================
// SEARCH MATCH CARD
// =============================================================================

function SearchMatchCard({
  match,
  language,
  getSuraName,
  onFindSimilar,
  isLoadingSimilar
}: {
  match: SearchMatch;
  language: 'ar' | 'en';
  getSuraName: (suraNo: number) => { ar: string; en: string };
  onFindSimilar: () => void;
  isLoadingSimilar: boolean;
}) {
  const [showTafsirLink, setShowTafsirLink] = useState(false);
  const suraName = getSuraName(match.sura_no);

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-100 hover:border-primary-200 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-primary-700">
            {language === 'ar' ? suraName.ar : suraName.en}
          </span>
          <Link
            to={`/quran/${match.sura_no}?aya=${match.aya_no}`}
            className="inline-flex items-center gap-1 text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded hover:bg-primary-200 transition-colors"
          >
            {language === 'ar' ? `الآية ${match.aya_no}` : `Ayah ${match.aya_no}`}
            <ExternalLink className="w-3 h-3" />
          </Link>
          {/* Tafsir Link */}
          <button
            onClick={() => setShowTafsirLink(!showTafsirLink)}
            className="inline-flex items-center gap-1 text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded hover:bg-amber-200 transition-colors"
          >
            <BookMarked className="w-3 h-3" />
            {language === 'ar' ? 'التفسير' : 'Tafsir'}
          </button>
          {/* Find Similar Button */}
          <button
            onClick={onFindSimilar}
            disabled={isLoadingSimilar}
            className="inline-flex items-center gap-1 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded hover:bg-purple-200 transition-colors disabled:opacity-50"
          >
            {isLoadingSimilar ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <GitBranch className="w-3 h-3" />
            )}
            {language === 'ar' ? 'آيات مشابهة' : 'Find Similar'}
          </button>
        </div>
        <div className="flex items-center gap-2">
          {match.exact_match ? (
            <span className="inline-flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
              <CheckCircle className="w-3 h-3" />
              {language === 'ar' ? 'تطابق تام' : 'Exact'}
            </span>
          ) : (
            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">
              {language === 'ar' ? 'دلالي' : 'Semantic'}
            </span>
          )}
          <span className="text-xs text-gray-500" title={language === 'ar' ? 'درجة الصلة' : 'Relevance Score'}>
            {Math.round(match.relevance_score * 100)}%
          </span>
        </div>
      </div>

      {/* Tafsir Links Panel */}
      {showTafsirLink && (
        <div className="mb-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
          <p className="text-sm font-medium text-amber-800 mb-2">
            {language === 'ar' ? 'روابط التفسير:' : 'Tafsir Links:'}
          </p>
          <div className="flex flex-wrap gap-2">
            <a
              href={`https://quran.com/${match.sura_no}/${match.aya_no}/tafsirs`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs bg-white text-amber-700 px-2 py-1 rounded border border-amber-200 hover:bg-amber-100 inline-flex items-center gap-1"
            >
              Quran.com <ExternalLink className="w-3 h-3" />
            </a>
            <a
              href={`https://www.altafsir.com/Tafasir.asp?tMadhNo=0&tTafsirNo=0&tSoession=0&tAession=${match.aya_no}&tSSession=${match.sura_no}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs bg-white text-amber-700 px-2 py-1 rounded border border-amber-200 hover:bg-amber-100 inline-flex items-center gap-1"
            >
              Altafsir.com <ExternalLink className="w-3 h-3" />
            </a>
            <Link
              to={`/quran/${match.sura_no}?aya=${match.aya_no}&tafsir=true`}
              className="text-xs bg-white text-amber-700 px-2 py-1 rounded border border-amber-200 hover:bg-amber-100 inline-flex items-center gap-1"
            >
              {language === 'ar' ? 'التفسير المدمج' : 'Built-in Tafsir'} <BookOpen className="w-3 h-3" />
            </Link>
          </div>
        </div>
      )}

      {/* Context Before (if available) */}
      {match.context_before && (
        <p className="text-sm text-gray-500 mb-1 font-arabic" dir="rtl">
          ...{match.context_before}
        </p>
      )}

      {/* Verse Text with Highlighting */}
      <p
        className="text-lg leading-loose font-arabic text-gray-800"
        dir="rtl"
        dangerouslySetInnerHTML={{
          __html: match.highlighted_text
            .replace(/【/g, '<mark class="bg-yellow-200 px-1 rounded font-semibold">')
            .replace(/】/g, '</mark>')
        }}
      />

      {/* Context After (if available) */}
      {match.context_after && (
        <p className="text-sm text-gray-500 mt-1 font-arabic" dir="rtl">
          {match.context_after}...
        </p>
      )}

      {/* Grammatical Analysis */}
      {(match.word_role_ar || match.sentence_type_ar) && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Languages className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-medium text-gray-600">
              {language === 'ar' ? 'التحليل النحوي' : 'Grammatical Analysis'}
            </span>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            {match.word_role_ar && (
              <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded flex items-center gap-1">
                <span className="text-blue-500">{language === 'ar' ? 'الدور:' : 'Role:'}</span>
                {language === 'ar' ? match.word_role_ar : match.word_role}
              </span>
            )}
            {match.sentence_type_ar && (
              <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded flex items-center gap-1">
                <span className="text-purple-500">{language === 'ar' ? 'الجملة:' : 'Sentence:'}</span>
                {language === 'ar' ? match.sentence_type_ar : match.sentence_type}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-500">
        <span>{language === 'ar' ? 'الصفحة' : 'Page'}: {match.page_no}</span>
        <span>{language === 'ar' ? 'الجزء' : 'Juz'}: {match.juz_no}</span>
        {match.tfidf_score > 0 && (
          <span className="flex items-center gap-1" title="TF-IDF Score">
            <Info className="w-3 h-3" />
            TF-IDF: {match.tfidf_score.toFixed(3)}
          </span>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// ANALYTICS PANEL
// =============================================================================

function AnalyticsPanel({
  analytics,
  language,
  suras,
  onExploreEvolution
}: {
  analytics: WordAnalyticsResponse;
  language: 'ar' | 'en';
  suras: SuraInfo[];
  onExploreEvolution: () => void;
}) {
  const sortedSuras = Object.entries(analytics.by_sura)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 10);

  const getSuraNameById = (suraNo: string) => {
    const sura = suras.find(s => s.sura_no === parseInt(suraNo));
    return sura ? (language === 'ar' ? sura.name_ar : sura.name_en) : suraNo;
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary-600" />
          {t('search_analytics', language)}: <span className="text-primary-600">{analytics.word}</span>
          <span className="text-sm font-normal text-gray-500">
            ({analytics.total_occurrences} {language === 'ar' ? 'مرة' : 'occurrences'})
          </span>
        </h3>
        <button
          onClick={onExploreEvolution}
          className="flex items-center gap-2 text-sm bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-3 py-1.5 rounded-lg hover:from-purple-600 hover:to-indigo-600 transition-all shadow-sm"
        >
          <TrendingUp className="w-4 h-4" />
          {language === 'ar' ? 'تتبع التطور' : 'Explore Evolution'}
        </button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* By Sura Distribution */}
        <div>
          <h4 className="font-medium text-sm mb-3 text-gray-700">{t('search_by_sura', language)}</h4>
          <div className="space-y-2">
            {sortedSuras.map(([suraNo, data]) => (
              <div key={suraNo} className="flex items-center gap-2">
                <Link
                  to={`/quran/${suraNo}`}
                  className="text-sm text-primary-600 hover:underline min-w-[120px] truncate"
                  title={getSuraNameById(suraNo)}
                >
                  {getSuraNameById(suraNo)}
                </Link>
                <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full transition-all"
                    style={{ width: `${Math.min(data.percentage * 2, 100)}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 min-w-[60px] text-right">
                  {data.count} ({data.percentage.toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* By Juz Distribution */}
        <div>
          <h4 className="font-medium text-sm mb-3 text-gray-700">{t('search_by_juz', language)}</h4>
          <div className="grid grid-cols-6 gap-1">
            {Object.entries(analytics.by_juz).map(([juz, count]) => {
              const counts = Object.values(analytics.by_juz);
              const maxCount = Math.max(...counts, 1);
              const intensity = (count as number) / maxCount;
              return (
                <div
                  key={juz}
                  className="aspect-square rounded flex items-center justify-center text-xs font-medium cursor-default"
                  style={{
                    backgroundColor: `rgba(59, 130, 246, ${0.1 + intensity * 0.7})`,
                    color: intensity > 0.5 ? 'white' : 'rgb(59, 130, 246)',
                  }}
                  title={`${language === 'ar' ? 'الجزء' : 'Juz'} ${juz}: ${count} ${language === 'ar' ? 'مرة' : 'times'}`}
                >
                  {juz}
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            {language === 'ar' ? 'الجزء 1-30 (اللون أغمق = المزيد)' : 'Juz 1-30 (darker = more occurrences)'}
          </p>
        </div>
      </div>

      {/* Co-occurring Words */}
      {analytics.co_occurring_words && analytics.co_occurring_words.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <h4 className="font-medium text-sm mb-3 text-gray-700">
            {language === 'ar' ? 'الكلمات المصاحبة' : 'Co-occurring Words'}
          </h4>
          <div className="flex flex-wrap gap-2">
            {analytics.co_occurring_words.slice(0, 15).map((item, i) => (
              <span
                key={i}
                className="text-sm bg-gray-100 text-gray-700 px-2 py-1 rounded"
                title={`${item.count} ${language === 'ar' ? 'مرة' : 'times'}`}
              >
                {item.word} <span className="text-xs text-gray-400">({item.count})</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// NO RESULTS FEEDBACK
// =============================================================================

function NoResultsFeedback({
  query,
  language,
  selectedSura,
  selectedTheme,
  onSelectWord,
  onClearFilters
}: {
  query: string;
  language: 'ar' | 'en';
  selectedSura?: number;
  selectedTheme?: string;
  onSelectWord: (word: string) => void;
  onClearFilters: () => void;
}) {
  // Find similar suggestions from autocomplete
  const getSuggestions = () => {
    // Find related words from autocomplete
    const related = AUTOCOMPLETE_SUGGESTIONS.filter(s => {
      const queryNorm = query.toLowerCase();
      const wordNorm = s.word.toLowerCase();
      // Check for partial match or same category
      return (
        wordNorm.includes(queryNorm) ||
        queryNorm.includes(wordNorm) ||
        s.category === 'theme' || // Always suggest themes
        s.category === 'prophet' // Always suggest prophets
      );
    }).slice(0, 6);

    // If no matches, return popular words
    if (related.length < 3) {
      return AUTOCOMPLETE_SUGGESTIONS.filter(s =>
        ['الله', 'رحمة', 'صبر', 'موسى', 'جنة', 'صلاة'].includes(s.word)
      );
    }
    return related;
  };

  const suggestions = getSuggestions();
  const hasFilters = selectedSura !== undefined || selectedTheme !== undefined;

  return (
    <div className="mt-4 card border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50">
      <h4 className="font-semibold text-amber-800 mb-3 flex items-center gap-2">
        <Sparkles className="w-4 h-4" />
        {language === 'ar' ? 'اقتراحات للبحث' : 'Search Suggestions'}
      </h4>

      {/* Tips Section */}
      <div className="mb-4 text-sm text-amber-700 space-y-2">
        <p className="flex items-start gap-2">
          <span className="text-amber-500">•</span>
          {language === 'ar'
            ? 'حاول استخدام كلمات مفردة بدون تشكيل (مثل: "الله" بدلاً من "اللَّهِ")'
            : 'Try using single words without diacritics (e.g., "الله" instead of "اللَّهِ")'}
        </p>
        <p className="flex items-start gap-2">
          <span className="text-amber-500">•</span>
          {language === 'ar'
            ? 'جرب البحث بالجذر الثلاثي للكلمة (مثل: "رحم" للبحث عن "الرحمة"، "الرحيم")'
            : 'Try searching with the root letters (e.g., "رحم" to find "رحمة", "رحيم")'}
        </p>
        {hasFilters && (
          <p className="flex items-start gap-2">
            <span className="text-amber-500">•</span>
            {language === 'ar'
              ? 'لديك فلاتر نشطة - جرب إزالتها للحصول على نتائج أكثر'
              : 'You have active filters - try removing them for more results'}
          </p>
        )}
      </div>

      {/* Clear Filters Button */}
      {hasFilters && (
        <button
          onClick={onClearFilters}
          className="mb-4 px-4 py-2 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <X className="w-4 h-4" />
          {language === 'ar' ? 'إزالة الفلاتر وإعادة البحث' : 'Clear filters and search again'}
        </button>
      )}

      {/* Suggested Words */}
      <div className="mb-2">
        <p className="text-sm font-medium text-amber-700 mb-2">
          {language === 'ar' ? 'جرب البحث عن:' : 'Try searching for:'}
        </p>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => onSelectWord(s.word)}
              className="px-3 py-1.5 bg-white hover:bg-amber-100 border border-amber-200 rounded-lg text-base font-arabic transition-colors flex items-center gap-2"
              dir="rtl"
            >
              <span>{s.word}</span>
              <span className="text-xs text-amber-500">
                ({language === 'ar' ? s.category_ar : s.category})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Quick Categories */}
      <div className="mt-4 pt-4 border-t border-amber-200">
        <p className="text-sm font-medium text-amber-700 mb-2">
          {language === 'ar' ? 'استكشف حسب الموضوع:' : 'Explore by topic:'}
        </p>
        <div className="flex flex-wrap gap-2">
          {[
            { word: 'إيمان', label_ar: 'الإيمان', label_en: 'Faith' },
            { word: 'توبة', label_ar: 'التوبة', label_en: 'Repentance' },
            { word: 'جنة', label_ar: 'الجنة', label_en: 'Paradise' },
            { word: 'نار', label_ar: 'النار', label_en: 'Hellfire' },
            { word: 'قيامة', label_ar: 'القيامة', label_en: 'Judgment Day' },
          ].map((topic, idx) => (
            <button
              key={idx}
              onClick={() => onSelectWord(topic.word)}
              className="px-3 py-1.5 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-full text-sm transition-colors"
            >
              {language === 'ar' ? topic.label_ar : topic.label_en}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// SAMPLE WORDS PANEL
// =============================================================================

function SampleWordsPanel({
  language,
  onSelectWord
}: {
  language: 'ar' | 'en';
  onSelectWord: (word: string) => void;
}) {
  const categories = [
    {
      title_ar: 'أسماء الله الحسنى',
      title_en: 'Names of Allah',
      words: ['الله', 'الرحمن', 'الرحيم', 'الملك', 'القدوس'],
    },
    {
      title_ar: 'مواضيع قرآنية',
      title_en: 'Quranic Themes',
      words: ['رحمة', 'صبر', 'إيمان', 'توبة', 'هدى', 'تقوى'],
    },
    {
      title_ar: 'الأنبياء',
      title_en: 'Prophets',
      words: ['محمد', 'موسى', 'عيسى', 'إبراهيم', 'نوح', 'يوسف'],
    },
    {
      title_ar: 'العبادات',
      title_en: 'Acts of Worship',
      words: ['صلاة', 'زكاة', 'صيام', 'حج', 'دعاء'],
    },
  ];

  return (
    <div className="card">
      <h3 className="font-semibold mb-4">{t('search_sample_words', language)}</h3>
      <div className="space-y-4">
        {categories.map((cat, idx) => (
          <div key={idx}>
            <h4 className="text-sm font-medium text-gray-600 mb-2">
              {language === 'ar' ? cat.title_ar : cat.title_en}
            </h4>
            <div className="flex flex-wrap gap-2">
              {cat.words.map((word) => (
                <button
                  key={word}
                  onClick={() => onSelectWord(word)}
                  className="px-4 py-2 bg-gray-100 hover:bg-primary-100 hover:text-primary-700 rounded-lg text-lg font-arabic transition-colors"
                  dir="rtl"
                >
                  {word}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// SIMILAR VERSES PANEL
// =============================================================================

function SimilarVersesPanel({
  data,
  loading,
  language,
  onClose
}: {
  data: SimilarVersesResponse | null;
  loading: boolean;
  language: 'ar' | 'en';
  onClose: () => void;
}) {
  return (
    <div className="card border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2 text-purple-800">
          <GitBranch className="w-5 h-5" />
          {language === 'ar' ? 'آيات مشابهة معنوياً' : 'Semantically Similar Verses'}
        </h3>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-purple-200 text-purple-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
            <span className="text-sm text-purple-600">
              {language === 'ar' ? 'جاري البحث عن آيات مشابهة...' : 'Finding similar verses...'}
            </span>
          </div>
        </div>
      ) : data ? (
        <div className="space-y-4">
          {/* Source Verse */}
          <div className="p-3 bg-white rounded-lg border border-purple-200">
            <div className="text-xs text-purple-600 mb-1 flex items-center gap-1">
              <Layers className="w-3 h-3" />
              {language === 'ar' ? 'الآية المرجعية' : 'Source Verse'}
            </div>
            <div className="font-semibold text-sm text-gray-700">
              {data.source_verse.reference} - {language === 'ar' ? data.source_verse.sura_name_ar : data.source_verse.sura_name_en}
            </div>
            <p className="text-lg font-arabic mt-2 text-gray-800" dir="rtl">
              {data.source_verse.text_uthmani}
            </p>
          </div>

          {/* Similar Verses */}
          <div className="space-y-3">
            <div className="text-sm font-medium text-gray-700">
              {language === 'ar' ? `${data.total_found} آية مشابهة` : `${data.total_found} similar verses found`}
            </div>
            {data.similar_verses.map((verse) => (
              <div
                key={`${verse.sura_no}-${verse.aya_no}`}
                className="p-3 bg-white rounded-lg border border-gray-200 hover:border-purple-300 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <Link
                    to={`/quran/${verse.sura_no}?aya=${verse.aya_no}`}
                    className="text-sm font-semibold text-purple-700 hover:underline flex items-center gap-1"
                  >
                    {verse.reference} - {language === 'ar' ? verse.sura_name_ar : verse.sura_name_en}
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                    {Math.round(verse.semantic_score * 100)}% {language === 'ar' ? 'تشابه' : 'similar'}
                  </span>
                </div>
                <p className="text-base font-arabic text-gray-800 leading-relaxed" dir="rtl">
                  {verse.text_uthmani}
                </p>
                {/* Shared Concepts */}
                {verse.shared_concepts && verse.shared_concepts.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {verse.shared_concepts.slice(0, 5).map((concept, i) => (
                      <span key={i} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                        {concept}
                      </span>
                    ))}
                  </div>
                )}
                {/* Themes */}
                {verse.themes && verse.themes.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {verse.themes.map((theme, i) => (
                      <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                        #{theme}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

// =============================================================================
// CONCEPT EVOLUTION PANEL
// =============================================================================

function ConceptEvolutionPanel({
  data,
  loading,
  language,
  onClose
}: {
  data: ConceptEvolutionResponse | null;
  loading: boolean;
  language: 'ar' | 'en';
  onClose: () => void;
}) {
  return (
    <div className="card border-2 border-indigo-200 bg-gradient-to-br from-indigo-50 to-blue-50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2 text-indigo-800">
          <TrendingUp className="w-5 h-5" />
          {language === 'ar' ? 'تطور المفهوم عبر القرآن' : 'Concept Evolution Across Quran'}
        </h3>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-indigo-200 text-indigo-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            <span className="text-sm text-indigo-600">
              {language === 'ar' ? 'جاري تتبع تطور المفهوم...' : 'Tracking concept evolution...'}
            </span>
          </div>
        </div>
      ) : data ? (
        <div className="space-y-4">
          {/* Concept Header */}
          <div className="p-3 bg-white rounded-lg border border-indigo-200">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xl font-arabic font-bold text-indigo-700">{data.concept}</span>
                {data.concept_normalized !== data.concept && (
                  <span className="text-sm text-gray-500 mr-2">({data.concept_normalized})</span>
                )}
              </div>
              <span className="text-sm bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full">
                {data.total_occurrences} {language === 'ar' ? 'ورود' : 'occurrences'}
              </span>
            </div>

            {/* Related Concepts */}
            {data.related_concepts && data.related_concepts.length > 0 && (
              <div className="mt-3 pt-3 border-t border-indigo-100">
                <div className="text-xs text-gray-500 mb-2">
                  {language === 'ar' ? 'مفاهيم مرتبطة:' : 'Related Concepts:'}
                </div>
                <div className="flex flex-wrap gap-2">
                  {data.related_concepts.map((concept, i) => (
                    <span
                      key={i}
                      className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded font-arabic"
                    >
                      {concept}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700 mb-3">
              {language === 'ar' ? 'التسلسل في القرآن (حسب ترتيب المصحف)' : 'Quranic Sequence (Mushaf Order)'}
            </div>
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-indigo-200" />

              {data.chronological_order.slice(0, 15).map((item, idx) => (
                <div key={idx} className="relative flex items-start gap-4 mb-4">
                  {/* Timeline dot */}
                  <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center text-xs font-bold z-10 flex-shrink-0">
                    {idx + 1}
                  </div>

                  {/* Content */}
                  <div className="flex-1 p-3 bg-white rounded-lg border border-gray-200 hover:border-indigo-300 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <Link
                        to={`/quran/${item.reference.split(':')[0]}?aya=${item.reference.split(':')[1]}`}
                        className="text-sm font-semibold text-indigo-700 hover:underline flex items-center gap-1"
                      >
                        {item.reference} - {language === 'ar' ? item.sura_name_ar : item.sura_name_en}
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                      <span className="text-xs text-gray-500">
                        {language === 'ar' ? 'الجزء' : 'Juz'} {item.juz_no}
                      </span>
                    </div>
                    <p className="text-base font-arabic text-gray-800 leading-relaxed" dir="rtl">
                      {item.text_snippet}
                    </p>
                    {/* Themes */}
                    {item.themes && item.themes.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {item.themes.map((theme, i) => (
                          <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                            #{theme}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {data.chronological_order.length > 15 && (
                <div className="text-center text-sm text-gray-500 mt-4">
                  {language === 'ar'
                    ? `و ${data.chronological_order.length - 15} آية أخرى...`
                    : `And ${data.chronological_order.length - 15} more verses...`}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
