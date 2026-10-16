/**
 * Enhanced Quran Page Component
 *
 * Features:
 * - Mushaf-style page navigation (604 pages)
 * - Surah-based navigation
 * - Verse highlighting with context
 * - Audio recitation with multiple reciters
 * - Bilingual support (Arabic/English)
 *
 * Arabic: صفحة القرآن الكريم المحسنة
 */
import { useState, useEffect, useRef, useCallback, lazy, Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiUrl } from '../lib/config';
import { useParams, useSearchParams, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowLeft, Book, ChevronLeft, ChevronRight, BookOpen,
  Languages, GitBranch, FileText, Headphones, Bookmark, BookmarkCheck,
  Copy, Check, Share2, Search, SlidersHorizontal, Image as ImageIcon,
  CheckCircle2, WifiOff,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { api, quranApi, grammarApi, Verse, conceptHighlightsApi, multiConceptApi } from '../lib/api';
import { queryKeys, staleTimes } from '../lib/queryClient';
import { loadOfflinePage, loadOfflineSurah, offlineQuranKey } from '../lib/offlineQuran';
import { SURAH_NAMES, SURAH_VERSE_COUNTS } from '../data/surahNames';
import { useBookmarksStore } from '../stores/bookmarksStore';
import {
  recordSurahVisit, recordReadingPosition, markSurahRead, getReadingProgress,
} from '../hooks/useReadingProgress';
import { OfflineReaderSection } from '../components/reader/OfflineReaderSection';
import { VerseText } from '../components/quran/WordMeaningPopover';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { ErrorPanel, parseAPIError, type APIErrorData } from '../components/common/ErrorPanel';
import { VerseTranslations, useTranslationEditions } from '../components/quran/VerseTranslations';
import { scrollBehavior } from '../hooks/usePrefersReducedMotion';
import { ReaderSettingsPanel } from '../components/quran/ReaderSettingsPanel';
import { VerseMarkers } from '../components/quran/VerseMarkers';
import {
  useReaderSettingsStore,
  effectiveTranslationKeys,
  verseTextFor,
  bismillahFor,
  applyReaderThemeToDocument,
} from '../stores/readerSettingsStore';
import clsx from 'clsx';
import { shareContent } from '../lib/native';
import { QuranTextAttribution } from '../components/quran/QuranTextAttribution';
import { shareVerseImage } from '../lib/verseImage';

const GrammarAnalysisView = lazy(() =>
  import('../components/quran/GrammarAnalysis').then(m => ({ default: m.GrammarAnalysisView }))
);
const SimilarVersesPanel = lazy(() =>
  import('../components/quran/SimilarVersesPanel').then(m => ({ default: m.SimilarVersesPanel }))
);
const QuranAudioPlayer = lazy(() => import('../components/quran/QuranAudioPlayer'));
const TafsirPanel = lazy(() =>
  import('../components/quran/TafsirPanel').then(m => ({ default: m.TafsirPanel }))
);

type NavigationMode = 'surah' | 'page';

interface SuraInfo {
  sura_no: number;
  name_ar: string;
  name_en: string;
  total_verses: number;
}

// Convert number to Arabic-Indic numerals
const toArabicNum = (num: number): string => {
  const arabicNums = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
  return num.toString().split('').map(d => arabicNums[parseInt(d)]).join('');
};

/**
 * The only ayah that consists of the Basmala is Al-Fatiha 1:1 (elsewhere it is
 * an opening shown apart from the ayah). Decided structurally, never by
 * matching typed Qur'an text. Used to keep 1:1 out of concept highlighting.
 */
const isBismillahVerse = (verse: Pick<Verse, 'sura_no' | 'aya_no'>): boolean =>
  verse.sura_no === 1 && verse.aya_no === 1;


export function QuranPage() {
  const { suraNo } = useParams<{ suraNo: string }>();
  const currentSura = Number(suraNo ?? '1');
  const validSura = Number.isInteger(currentSura) && currentSura >= 1 && currentSura <= 114;
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const highlightAya = searchParams.get('aya');
  const pageParam = searchParams.get('page');
  const conceptParam = searchParams.get('concept');  // Single concept ID for highlighting
  const conceptsParam = searchParams.get('concepts'); // Multiple concept IDs (comma-separated)

  const { language } = useLanguageStore();
  const location = useLocation();
  const {
    view: viewMode, setView: setViewMode, script, fontScale, translationKeys, autoScroll, theme,
  } = useReaderSettingsStore();
  useEffect(() => applyReaderThemeToDocument(theme), [theme]);
  const activeTranslations = effectiveTranslationKeys(translationKeys, language);
  const translationsKey = activeTranslations.join(',');
  const { data: translationEditions } = useTranslationEditions();
  const [showSettings, setShowSettings] = useState(false);
  const arabicFontSize = { fontSize: `${1.5 * fontScale}rem` };
  const quranFont = script === 'uthmani' ? 'font-mushaf' : 'font-arabic';
  const [navMode, setNavMode] = useState<NavigationMode>(pageParam ? 'page' : 'surah');
  const [currentPage, setCurrentPage] = useState<number>(pageParam ? parseInt(pageParam, 10) : 1);
  const [grammarVerseNo, setGrammarVerseNo] = useState<number | null>(null);
  const [similarVerseNo, setSimilarVerseNo] = useState<number | null>(null);
  const [tafsirVerseNo, setTafsirVerseNo] = useState<number | null>(null);
  // Auto-show audio player when coming from concepts page with highlighted verse
  const [showAudioPlayer, setShowAudioPlayer] = useState(!!highlightAya && !!conceptParam);
  const [currentPlayingAya, setCurrentPlayingAya] = useState<number | null>(null);

  // Concept-based highlighting (supports single or multiple concepts)
  const [conceptHighlights, setConceptHighlights] = useState<Set<string>>(new Set());
  const [_conceptLabels, setConceptLabels] = useState<string[]>([]);
  const [_multiConceptMatches, setMultiConceptMatches] = useState<Map<string, string[]>>(new Map()); // verse -> matched concepts

  const { addBookmark, removeBookmark, isBookmarked } = useBookmarksStore();
  const highlightRef = useRef<HTMLSpanElement>(null);
  const [copiedVerseId, setCopiedVerseId] = useState<number | null>(null);
  const [markedRead, setMarkedRead] = useState(false);
  useEffect(() => setMarkedRead(false), [currentSura]);

  const copyVerse = useCallback((verse: Verse, displayText: string) => {
    const ref = `(${verse.sura_name_ar} ${toArabicNum(verse.aya_no)})`;
    const full = `${displayText} ${ref}`;
    navigator.clipboard.writeText(full).then(() => {
      setCopiedVerseId(verse.id);
      setTimeout(() => setCopiedVerseId(null), 2000);
    }).catch(() => {});
  }, []);

  const shareVerse = useCallback((verse: Verse, displayText: string) => {
    const ref = `${verse.sura_name_ar} ${toArabicNum(verse.aya_no)}`;
    const translation = verse.translations?.[0]?.text;
    void shareContent({
      title: ref,
      text: [displayText, `(${ref})`, translation].filter(Boolean).join('\n'),
      path: `/quran/${verse.sura_no}?aya=${verse.aya_no}`,
    });
  }, []);

  const [imageBusyId, setImageBusyId] = useState<number | null>(null);
  const shareImage = useCallback(async (verse: Verse, displayText: string) => {
    setImageBusyId(verse.id);
    const first = verse.translations?.[0];
    const edition = first ? translationEditions?.find((e) => e.key === first.translator) : undefined;
    await shareVerseImage({
      arabic: displayText,
      reference: language === 'ar'
        ? `${verse.sura_name_ar} · ${toArabicNum(verse.aya_no)}`
        : `${verse.sura_name_en} ${verse.sura_no}:${verse.aya_no}`,
      translation: first?.text,
      translationSource: edition ? `${edition.title} · v${edition.version} · QuranEnc.com` : undefined,
      arabicFont: script === 'uthmani' ? 'Scheherazade New' : 'Noto Naskh Arabic',
    }, `tadabbur-${verse.sura_no}-${verse.aya_no}.png`);
    setImageBusyId(null);
  }, [language, script, translationEditions]);

  // Prefetch on button hover so panel opens instantly
  const prefetchGrammar = useCallback((suraNo: number, ayaNo: number) => {
    const key = `grammar_irab:${suraNo}:${ayaNo}`;
    if (sessionStorage.getItem(key)) return;
    grammarApi.analyzeIrab(`${suraNo}:${ayaNo}`).then(r => {
      try { sessionStorage.setItem(key, JSON.stringify(r.data)); } catch { /* storage unavailable or full: caching is best-effort */ }
    }).catch(() => {});
  }, []);

  const prefetchSimilar = useCallback((suraNo: number, ayaNo: number) => {
    const key = `sim_verses:${suraNo}:${ayaNo}`;
    if (sessionStorage.getItem(key)) return;
    quranApi.getAdvancedSimilarity(suraNo, ayaNo, { top_k: 50, min_score: 0.2 }).then(r => {
      try { sessionStorage.setItem(key, JSON.stringify(r.data)); } catch { /* storage unavailable or full: caching is best-effort */ }
    }).catch(() => {});
  }, []);

  const prefetchTafsir = useCallback((suraNo: number, ayaNo: number) => {
    const key = `tafsir_panel:${suraNo}:${ayaNo}:muyassar`;
    if (sessionStorage.getItem(key)) return;
    fetch(apiUrl(`/api/v1/tafseer/external/verse/${suraNo}/${ayaNo}?edition=muyassar`))
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) try { sessionStorage.setItem(key, JSON.stringify(data)); } catch { /* storage unavailable or full: caching is best-effort */ } })
      .catch(() => {});
  }, []);

  // Data: React Query, persisted to IndexedDB for canonical keys, so a surah
  // or page read once (or saved with "Save Qur'an offline") opens offline.
  const metadataQuery = useQuery({
    queryKey: queryKeys.quran.metadata(),
    queryFn: async () => (await api.get<{ suras?: SuraInfo[] }>('/quran/metadata')).data,
    staleTime: staleTimes.quranText,
    networkMode: 'offlineFirst',
  });
  // Offline with no saved metadata: the bundled surah names keep the selector usable.
  const suras: SuraInfo[] = metadataQuery.data?.suras ?? SURAH_NAMES.map((n, i) => ({
    sura_no: i + 1, name_ar: n.ar, name_en: n.en, total_verses: SURAH_VERSE_COUNTS[i],
  }));

  const pageMode = navMode === 'page' && currentPage >= 1 && currentPage <= 604;
  const versesQuery = useQuery({
    queryKey: pageMode
      ? queryKeys.quran.pageWithTranslations(currentPage, translationsKey)
      : queryKeys.quran.suraWithTranslations(currentSura, translationsKey),
    queryFn: async () => (pageMode
      ? await quranApi.getPageVerses(currentPage, activeTranslations)
      : await quranApi.getSuraVerses(currentSura, activeTranslations)).data,
    enabled: pageMode || validSura,
    staleTime: staleTimes.quranText,
    networkMode: 'offlineFirst',
    placeholderData: undefined,
  });
  // The API could not be reached (first failure, paused offline, or error):
  // read the Arabic text bundled with the app (verbatim Tanzil, no translations).
  const apiUnreachable = !versesQuery.data && (pageMode || validSura) &&
    (versesQuery.fetchStatus === 'paused' || versesQuery.isError || versesQuery.failureCount > 0);
  const bundleQuery = useQuery({
    queryKey: offlineQuranKey(pageMode ? 'page' : 'sura', pageMode ? currentPage : currentSura),
    queryFn: () => (pageMode ? loadOfflinePage(currentPage) : loadOfflineSurah(currentSura)),
    enabled: apiUnreachable,
    staleTime: Infinity,
    networkMode: 'always',
    retry: false,
    placeholderData: undefined,
  });
  const fromBundle = !versesQuery.data && !!bundleQuery.data;
  const verses: Verse[] = versesQuery.data ?? bundleQuery.data ?? [];
  // No data and no connection: the request is paused (offlineFirst) or failed offline.
  const offline = !versesQuery.data && !fromBundle && !bundleQuery.isFetching && (versesQuery.fetchStatus === 'paused' ||
    (versesQuery.isError && typeof navigator !== 'undefined' && navigator.onLine === false));
  // Verse text comes from the backend; a failed load must not look like an empty surah.
  const loadError: APIErrorData | null = versesQuery.isError && !versesQuery.data && !fromBundle && !bundleQuery.isFetching ? parseAPIError(versesQuery.error) : null;
  // Still waiting: the API request (or its retries) or the bundled fallback is in flight.
  const loading = (pageMode || validSura) && !versesQuery.data && !fromBundle && !offline && !loadError &&
    (versesQuery.isPending || versesQuery.isFetching || bundleQuery.isFetching);
  const retryLoad = () => { void versesQuery.refetch(); };

  // In surah mode, follow the surah's first page for page navigation.
  useEffect(() => {
    if (navMode === 'surah' && versesQuery.data && versesQuery.data.length > 0) {
      setCurrentPage(versesQuery.data[0].page_no);
    }
  }, [navMode, versesQuery.data]);

  // Record surah visit for reading progress tracking
  useEffect(() => {
    if (navMode !== 'surah' || currentSura < 1 || currentSura > 114) return;
    const meta = suras.find(s => s.sura_no === currentSura);
    if (meta) {
      recordSurahVisit(currentSura, meta.name_ar, meta.name_en);
    }
  }, [currentSura, navMode, suras]);

  // Scroll to highlighted verse
  useEffect(() => {
    if (highlightRef.current && !loading) {
      setTimeout(() => {
        highlightRef.current?.scrollIntoView({ behavior: scrollBehavior(), block: 'center' });
      }, 100);
    }
  }, [loading, highlightAya]);

  // Remember the verse in view (topmost visible), so "continue reading" and the
  // reading reminder reopen at that verse rather than at the top of the surah.
  useEffect(() => {
    if (loading || verses.length === 0 || !('IntersectionObserver' in window)) return;
    const byKey = new Map(verses.map((v) => [`${v.sura_no}:${v.aya_no}`, v]));
    const visible = new Set<string>();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const observer = new IntersectionObserver((entries) => {
      for (const e of entries) {
        const key = (e.target as HTMLElement).dataset.verseKey;
        if (!key) continue;
        if (e.isIntersecting) visible.add(key); else visible.delete(key);
      }
      clearTimeout(timer);
      timer = setTimeout(() => {
        // Reaching the surah's last verse completes it in the khatmah plan.
        const last = verses[verses.length - 1];
        const lastInView = navMode === 'surah' && last && visible.has(`${last.sura_no}:${last.aya_no}`);
        const top = lastInView ? last : verses.find((v) => visible.has(`${v.sura_no}:${v.aya_no}`));
        if (top) {
          recordReadingPosition({
            surah: top.sura_no, aya: top.aya_no, nameAr: top.sura_name_ar, nameEn: top.sura_name_en,
          });
        }
      }, 1500);
    }, { rootMargin: '-20% 0px -50% 0px' });
    document.querySelectorAll<HTMLElement>('[data-verse-key]').forEach((el) => {
      if (byKey.has(el.dataset.verseKey ?? '')) observer.observe(el);
    });
    return () => {
      clearTimeout(timer);
      observer.disconnect();
    };
  }, [loading, verses, viewMode, navMode]);

  // Follow the verse being recited
  useEffect(() => {
    if (!autoScroll || currentPlayingAya === null) return;
    const el = document.querySelector<HTMLElement>(
      `[data-verse-key="${currentSura}:${currentPlayingAya}"]`,
    );
    el?.scrollIntoView({ behavior: scrollBehavior(), block: 'center' });
  }, [autoScroll, currentPlayingAya, currentSura]);

  // Load concept highlights when concept or concepts param is present
  useEffect(() => {
    async function loadConceptHighlights() {
      // Check for multi-concept search first
      if (conceptsParam) {
        const conceptIds = conceptsParam.split(',').map(c => c.trim()).filter(Boolean);
        if (conceptIds.length === 0) {
          setConceptHighlights(new Set());
          setConceptLabels([]);
          setMultiConceptMatches(new Map());
          return;
        }

        try {
          const response = await multiConceptApi.getMultiConceptHighlights(
            conceptIds,
            {
              pageNo: navMode === 'page' ? currentPage : undefined,
              suraNo: navMode === 'surah' ? currentSura : undefined,
              expandRelated: true,
            }
          );
          if (response.data.ok) {
            const highlightSet = new Set(
              response.data.highlights.map(h => `${h.sura_no}:${h.aya_no}`)
            );
            const matchesMap = new Map<string, string[]>();
            response.data.highlights.forEach(h => {
              matchesMap.set(`${h.sura_no}:${h.aya_no}`, h.matched_concepts);
            });
            setConceptHighlights(highlightSet);
            setConceptLabels(conceptIds);
            setMultiConceptMatches(matchesMap);
          }
        } catch (err) {
          console.error('Failed to load multi-concept highlights:', err);
          setConceptHighlights(new Set());
          setConceptLabels([]);
          setMultiConceptMatches(new Map());
        }
        return;
      }

      // Single concept fallback
      if (!conceptParam) {
        setConceptHighlights(new Set());
        setConceptLabels([]);
        setMultiConceptMatches(new Map());
        return;
      }

      try {
        const response = await conceptHighlightsApi.getConceptHighlights(
          conceptParam,
          navMode === 'page' ? { pageNo: currentPage } : { suraNo: currentSura }
        );
        if (response.data.ok) {
          const highlightSet = new Set(
            response.data.highlights.map(h => `${h.sura_no}:${h.aya_no}`)
          );
          setConceptHighlights(highlightSet);
          setConceptLabels([conceptParam]);
          setMultiConceptMatches(new Map());
        }
      } catch (err) {
        console.error('Failed to load concept highlights:', err);
        setConceptHighlights(new Set());
      }
    }
    loadConceptHighlights();
  }, [conceptParam, conceptsParam, navMode, currentPage, currentSura]);

  // Update URL when page changes
  useEffect(() => {
    if (navMode === 'page') {
      const params = new URLSearchParams(searchParams);
      params.set('page', currentPage.toString());
      setSearchParams(params, { replace: true });
    }
  }, [currentPage, navMode]);

  // Navigation functions
  const navigateToPage = (page: number) => {
    if (page >= 1 && page <= 604) {
      setCurrentPage(page);
      setNavMode('page');
    }
  };

  const navigateToSura = (sura: number) => {
    if (sura >= 1 && sura <= 114) {
      navigate(`/quran/${sura}`);
      setNavMode('surah');
    }
  };

  // Handle verse audio change
  const handleVerseChange = useCallback((_suraNo: number, ayaNo: number) => {
    setCurrentPlayingAya(ayaNo);
  }, []);

  // Get sura info
  const suraName = verses.length > 0
    ? (language === 'ar' ? verses[0].sura_name_ar : verses[0].sura_name_en)
    : '';

  const firstVerse = verses[0];
  const pageInfo = firstVerse ? { page: firstVerse.page_no, juz: firstVerse.juz_no } : null;

  // Group verses by sura for page view
  const versesBySura = verses.reduce((acc, verse) => {
    const key = verse.sura_no;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(verse);
    return acc;
  }, {} as Record<number, Verse[]>);

  const isAr = language === 'ar';
  // Came here from another screen of the app: go back there; opened directly
  // (deep link, notification, new tab): offer the Mushaf.
  const cameFromApp = location.key !== 'default';
  const backLink = cameFromApp ? (
    <button
      type="button"
      onClick={() => navigate(-1)}
      className={clsx('inline-flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-6', isAr && 'font-arabic')}
    >
      <ArrowLeft className={clsx('w-4 h-4', isAr && 'rotate-180')} aria-hidden="true" />
      {isAr ? 'رجوع' : 'Back'}
    </button>
  ) : (
    <Link
      to="/mushaf"
      className={clsx('inline-flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-6', isAr && 'font-arabic')}
    >
      <ArrowLeft className={clsx('w-4 h-4', isAr && 'rotate-180')} aria-hidden="true" />
      {isAr ? 'المصحف' : 'Mushaf'}
    </Link>
  );

  if (navMode === 'surah' && !validSura) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center" dir={isAr ? 'rtl' : 'ltr'}>
        <div className="card">
          <Book className="w-10 h-10 text-gray-300 mx-auto mb-3" aria-hidden="true" />
          <h1 className={clsx('text-xl font-bold mb-2', isAr && 'font-arabic')}>
            {isAr ? 'السورة غير موجودة' : 'Surah not found'}
          </h1>
          <p className={clsx('text-sm text-gray-500 mb-5', isAr && 'font-arabic')}>
            {isAr ? 'أرقام السور من ١ إلى ١١٤.' : 'Surah numbers run from 1 to 114.'}
          </p>
          <div className="flex justify-center gap-3 flex-wrap">
            <Link to="/quran/1" className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700">
              {isAr ? 'سورة الفاتحة' : 'Al-Fatiha'}
            </Link>
            <Link to="/mushaf" className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 text-sm hover:bg-gray-200">
              {isAr ? 'المصحف' : 'Mushaf'}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const readComplete = navMode === 'surah' && getReadingProgress().visited.has(currentSura);
  const markReadBlock = navMode === 'surah' && verses.length > 0 && (
    <div className="flex justify-center my-6">
      {readComplete || markedRead ? (
        <span className={clsx('inline-flex items-center gap-2 text-sm text-emerald-700', isAr && 'font-arabic')} role="status">
          <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
          {isAr ? 'السورة مقروءة في خطة الختمة' : 'Surah marked as read in your khatmah plan'}
        </span>
      ) : (
        <button
          type="button"
          onClick={() => {
            markSurahRead(currentSura, verses[0].sura_name_ar, verses[0].sura_name_en);
            setMarkedRead(true);
          }}
          className={clsx('inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-emerald-300 text-emerald-700 text-sm hover:bg-emerald-50', isAr && 'font-arabic')}
        >
          <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
          {isAr ? 'تعليم السورة كمقروءة' : 'Mark surah as read'}
        </button>
      )}
    </div>
  );

  return (
    <div
      className="reader-surface max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      data-theme={theme}
      dir={isAr ? 'rtl' : 'ltr'}
    >
      {backLink}

      {/* Header */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
              <Book className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              {navMode === 'surah' ? (
                <>
                  <h1 className={clsx('text-2xl font-bold', language === 'ar' && 'font-arabic')}>{suraName}</h1>
                  <p className={clsx('text-sm text-gray-500', language === 'ar' && 'font-arabic')}>
                    {language === 'ar' ? `السورة ${toArabicNum(currentSura)}` : `Surah ${currentSura}`}
                    {' - '}
                    {language === 'ar' ? `${toArabicNum(verses.length)} آية` : `${verses.length} verses`}
                  </p>
                </>
              ) : (
                <>
                  <h1 className={clsx('text-2xl font-bold', language === 'ar' && 'font-arabic')}>
                    {language === 'ar' ? `الصفحة ${toArabicNum(currentPage)}` : `Page ${currentPage}`}
                  </h1>
                  <p className={clsx('text-sm text-gray-500', language === 'ar' && 'font-arabic')}>
                    {language === 'ar' ? `الجزء ${toArabicNum(pageInfo?.juz || 1)}` : `Juz ${pageInfo?.juz || 1}`}
                  </p>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 flex-wrap">
            {/* Navigation Mode Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setNavMode('surah')}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  navMode === 'surah'
                    ? 'bg-white shadow text-primary-600'
                    : 'text-gray-600 hover:text-gray-900',
                  language === 'ar' && 'font-arabic'
                )}
              >
                <FileText className="w-4 h-4" />
                {language === 'ar' ? 'سورة' : 'Surah'}
              </button>
              <button
                onClick={() => setNavMode('page')}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  navMode === 'page'
                    ? 'bg-white shadow text-primary-600'
                    : 'text-gray-600 hover:text-gray-900',
                  language === 'ar' && 'font-arabic'
                )}
              >
                <BookOpen className="w-4 h-4" />
                {language === 'ar' ? 'صفحة' : 'Page'}
              </button>
            </div>

            {/* View Mode Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('mushaf')}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  viewMode === 'mushaf'
                    ? 'bg-white shadow text-primary-600'
                    : 'text-gray-600 hover:text-gray-900',
                  language === 'ar' && 'font-arabic'
                )}
              >
                {language === 'ar' ? 'المصحف' : 'Mushaf'}
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  viewMode === 'list'
                    ? 'bg-white shadow text-primary-600'
                    : 'text-gray-600 hover:text-gray-900',
                  language === 'ar' && 'font-arabic'
                )}
              >
                {language === 'ar' ? 'قائمة' : 'List'}
              </button>
            </div>

            {/* Reader settings */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              aria-expanded={showSettings}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
                showSettings
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-600 hover:text-gray-900',
                language === 'ar' && 'font-arabic'
              )}
            >
              <SlidersHorizontal className="w-5 h-5" />
              {language === 'ar' ? 'الإعدادات' : 'Settings'}
            </button>

            {/* Audio Toggle */}
            <button
              onClick={() => setShowAudioPlayer(!showAudioPlayer)}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
                showAudioPlayer
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-600 hover:text-gray-900',
                language === 'ar' && 'font-arabic'
              )}
            >
              <Headphones className="w-5 h-5" />
              {language === 'ar' ? 'استماع' : 'Listen'}
            </button>

            {/* Navigation Controls */}
            <div className="flex items-center gap-2">
              {navMode === 'page' ? (
                <>
                  <button
                    onClick={() => navigateToPage(currentPage - 1)}
                    disabled={currentPage <= 1}
                    aria-label={isAr ? 'الصفحة السابقة' : 'Previous page'}
                    className={clsx(
                      'p-2 rounded-lg hover:bg-gray-100 transition-colors',
                      currentPage <= 1 && 'opacity-50 pointer-events-none'
                    )}
                  >
                    {language === 'ar' ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                  </button>
                  <input
                    type="number"
                    min="1"
                    max="604"
                    aria-label={isAr ? 'رقم الصفحة' : 'Page number'}
                    value={currentPage}
                    onChange={(e) => navigateToPage(parseInt(e.target.value, 10))}
                    className="input py-1 px-2 w-20 text-center text-sm"
                  />
                  <span className="text-sm text-gray-500">/ 604</span>
                  <button
                    onClick={() => navigateToPage(currentPage + 1)}
                    disabled={currentPage >= 604}
                    aria-label={isAr ? 'الصفحة التالية' : 'Next page'}
                    className={clsx(
                      'p-2 rounded-lg hover:bg-gray-100 transition-colors',
                      currentPage >= 604 && 'opacity-50 pointer-events-none'
                    )}
                  >
                    {language === 'ar' ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to={`/quran/${Math.max(1, currentSura - 1)}`}
                    aria-label={isAr ? 'السورة السابقة' : 'Previous surah'}
                    aria-disabled={currentSura <= 1 || undefined}
                    tabIndex={currentSura <= 1 ? -1 : undefined}
                    className={clsx(
                      'p-2 rounded-lg hover:bg-gray-100 transition-colors',
                      currentSura <= 1 && 'opacity-50 pointer-events-none'
                    )}
                  >
                    {language === 'ar' ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                  </Link>
                  <select
                    value={currentSura}
                    aria-label={isAr ? 'اختر السورة' : 'Choose surah'}
                    onChange={(e) => navigateToSura(parseInt(e.target.value, 10))}
                    className="input py-1 px-2 w-auto text-sm"
                  >
                    {suras.map((s) => (
                      <option key={s.sura_no} value={s.sura_no}>
                        {s.sura_no}. {language === 'ar' ? s.name_ar : s.name_en}
                      </option>
                    ))}
                  </select>
                  <Link
                    to={`/quran/${Math.min(114, currentSura + 1)}`}
                    aria-label={isAr ? 'السورة التالية' : 'Next surah'}
                    aria-disabled={currentSura >= 114 || undefined}
                    tabIndex={currentSura >= 114 ? -1 : undefined}
                    className={clsx(
                      'p-2 rounded-lg hover:bg-gray-100 transition-colors',
                      currentSura >= 114 && 'opacity-50 pointer-events-none'
                    )}
                  >
                    {language === 'ar' ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {showSettings && (
        <>
          <ReaderSettingsPanel language={language} onClose={() => setShowSettings(false)} />
          <OfflineReaderSection language={language} translations={activeTranslations} />
        </>
      )}

      {/* Audio Player */}
      {showAudioPlayer && (
        <div className="mb-6">
          <ErrorBoundary fallback={<div className="h-16 flex items-center justify-center text-sm text-amber-600 bg-amber-50 rounded-lg border border-amber-200">{isAr ? 'مشغّل التلاوة غير متاح' : 'Audio player unavailable'}</div>}>
            <Suspense fallback={<div className="h-16 animate-pulse bg-gray-100 rounded-lg" />}>
              <QuranAudioPlayer
                mode={navMode === 'page' ? 'page' : 'surah'}
                suraNo={navMode === 'surah' ? currentSura : undefined}
                pageNo={navMode === 'page' ? currentPage : undefined}
                language={language}
                onVerseChange={handleVerseChange}
                startFromAya={highlightAya ? parseInt(highlightAya, 10) : undefined}
                startFromSura={highlightAya ? currentSura : undefined}
                autoPlay={!!highlightAya && !!conceptParam}
              />
            </Suspense>
          </ErrorBoundary>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
        </div>
      ) : offline ? (
        <div className="card text-center py-10" role="status">
          <WifiOff className="w-10 h-10 text-gray-300 mx-auto mb-3" aria-hidden="true" />
          <h2 className={clsx('text-lg font-semibold mb-1', isAr && 'font-arabic')}>
            {isAr ? 'لا يوجد اتصال' : 'You are offline'}
          </h2>
          <p className={clsx('text-sm text-gray-500 mb-4', isAr && 'font-arabic')}>
            {isAr
              ? 'هذه السورة غير محفوظة على الجهاز بعد. اتصل بالإنترنت ثم احفظ القرآن للقراءة دون اتصال من الإعدادات.'
              : 'This surah is not saved on this device yet. Connect, then save the Qur’an for offline reading from Settings.'}
          </p>
          <button onClick={retryLoad} className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700">
            {isAr ? 'حاول مجددًا' : 'Try again'}
          </button>
        </div>
      ) : loadError ? (
        <ErrorPanel error={loadError} onRetry={retryLoad} />
      ) : (<>
      {fromBundle && (
        <div
          className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
          role="status"
          data-testid="offline-quran-notice"
        >
          <WifiOff className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <span className={clsx('flex-1', isAr && 'font-arabic')} dir={isAr ? 'rtl' : 'ltr'}>
            {isAr
              ? 'دون اتصال: النص العربي فقط (نسخة مضمّنة في التطبيق). الترجمات والتفسير والتلاوة تحتاج إلى اتصال.'
              : 'Offline: Arabic text only (copy bundled with the app). Translations, tafsir and recitation need a connection.'}
          </span>
          <button onClick={retryLoad} className="text-xs underline flex-shrink-0">
            {isAr ? 'حاول مجددًا' : 'Try again'}
          </button>
        </div>
      )}
      {viewMode === 'mushaf' ? (
        /* Mushaf Style View */
        <div className="reader-mushaf rounded-2xl bg-[#fefcf3] border-2 border-amber-200 shadow-lg overflow-hidden">
          {/* Decorative Header */}
          <div className="bg-gradient-to-r from-amber-800 via-amber-700 to-amber-800 text-center py-4 px-6">
            <h2 className="text-2xl font-bold font-arabic text-amber-50 tracking-widest" lang={navMode === 'surah' || isAr ? 'ar' : 'en'}>
              {navMode === 'surah'
                ? verses[0]?.sura_name_ar
                : language === 'ar' ? `صفحة ${toArabicNum(currentPage)}` : `Page ${currentPage}`}
            </h2>
            {navMode === 'page' && Object.keys(versesBySura).length > 1 && (
              <p className="text-xs text-amber-200 mt-1">
                {Object.entries(versesBySura).map(([suraNo, suraVerses], idx) => (
                  <span key={suraNo}>
                    {idx > 0 && ' · '}
                    {language === 'ar' ? suraVerses[0].sura_name_ar : suraVerses[0].sura_name_en}
                  </span>
                ))}
              </p>
            )}
          </div>
          <div className="p-6">

          {/* Verses in Mushaf Style */}
          <div className={clsx('reader-arabic text-center leading-[3] text-gray-900', quranFont)} style={arabicFontSize} dir="rtl" lang="ar">
            {verses.map((verse, idx) => {
              const verseKey = `${verse.sura_no}:${verse.aya_no}`;
              // Exclude Bismillah verses from concept highlighting to avoid redundant matches
              const isConceptHighlighted = conceptHighlights.has(verseKey) &&
                                           !isBismillahVerse(verse);
              // Highlight specific verse: check both aya_no AND sura_no to avoid cross-sura false matches on same page
              const isHighlighted = (highlightAya &&
                                    parseInt(highlightAya, 10) === verse.aya_no &&
                                    verse.sura_no === currentSura) ||
                                   (currentPlayingAya === verse.aya_no && verse.sura_no === currentSura);

              const isFirstVerse = verse.aya_no === 1;
              // The surah's opening Bismillah comes with verse 1 (separately from its text)
              const bismillah = bismillahFor(verse, script);
              const displayText = verseTextFor(verse, script);
              // Show Bismillah block for: page mode (when surah starts on page) or surah mode
              const showBismillahBlock = bismillah !== null && (
                navMode === 'surah' ||
                (navMode === 'page' && (idx === 0 || verses[idx - 1]?.sura_no !== verse.sura_no))
              );

              return (
                <span key={verse.id}>
                  {/* Surah header for page view */}
                  {navMode === 'page' && isFirstVerse && (idx === 0 || verses[idx - 1]?.sura_no !== verse.sura_no) && (
                    <div className="block text-center my-4 py-2 border-y border-amber-300">
                      <span className="text-lg text-amber-900 font-bold">{verse.sura_name_ar}</span>
                    </div>
                  )}
                  {/* Bismillah — text extracted from verse 1, never hardcoded */}
                  {showBismillahBlock && (
                    <div className="block text-center mb-4" dir="rtl">
                      <span className={clsx('text-xl text-amber-800', quranFont)}>{bismillah}</span>
                    </div>
                  )}
                  {verse.quarter_start && (
                    <span className="inline-block align-middle mx-1" style={{ fontSize: '1rem', lineHeight: 1.5 }}>
                      <VerseMarkers verse={verse} language={language} only="quarter" />
                    </span>
                  )}
                  <span
                    ref={isHighlighted ? highlightRef : null}
                    data-verse-key={verseKey}
                    className={clsx(
                      'inline transition-all duration-300',
                      isHighlighted && 'bg-primary-200 rounded px-1 py-0.5',
                      isConceptHighlighted && !isHighlighted && 'bg-amber-100 rounded px-1 py-0.5 border-b-2 border-amber-400'
                    )}
                  >
                    <VerseText text={displayText} sura={verse.sura_no} aya={verse.aya_no} />
                  </span>
                  <span className="inline-flex items-center justify-center w-8 h-8 mx-1 text-sm bg-amber-100 text-amber-800 rounded-full border border-amber-300 font-semibold">
                    {toArabicNum(verse.aya_no)}
                  </span>
                  {verse.sajda_type && (
                    <span className="inline-block align-middle mx-1" style={{ fontSize: '1rem', lineHeight: 1.5 }}>
                      <VerseMarkers verse={verse} language={language} only="sajdah" />
                    </span>
                  )}
                  {idx < verses.length - 1 && ' '}
                </span>
              );
            })}
          </div>

          {/* Decorative Footer */}
          <div className={clsx('mt-6 pt-4 border-t-2 border-amber-200 flex justify-center gap-6 text-sm text-amber-700', language === 'ar' && 'font-arabic')}>
            <span className="flex items-center gap-1">
              <span className="text-amber-400 text-xs">{language === 'ar' ? 'ص' : 'P'}</span>
              {toArabicNum(firstVerse?.page_no || currentPage)}
            </span>
            <span className="text-amber-300">|</span>
            <span className="flex items-center gap-1">
              <span className="text-amber-400 text-xs">{language === 'ar' ? 'ج' : 'J'}</span>
              {toArabicNum(firstVerse?.juz_no || 1)}
            </span>
            <span className="text-amber-300">|</span>
            <span className="flex items-center gap-1">
              <span className="text-amber-400 text-xs">{language === 'ar' ? 'آية' : 'V'}</span>
              {toArabicNum(verses.length)}
            </span>
          </div>
          </div>
          {markReadBlock}
          <QuranTextAttribution language={language} className="mt-3 text-center" />
        </div>
      ) : (
        /* List View with Translations */
        <div className="space-y-3">
          {verses.map((verse, verseIdx) => {
            const verseKey = `${verse.sura_no}:${verse.aya_no}`;
            const isConceptHighlighted = conceptHighlights.has(verseKey) &&
                                         !isBismillahVerse(verse);
            const isHighlighted = (highlightAya &&
                                  parseInt(highlightAya, 10) === verse.aya_no &&
                                  verse.sura_no === currentSura) ||
                                 (currentPlayingAya === verse.aya_no && verse.sura_no === currentSura);
            const showGrammar = grammarVerseNo === verse.aya_no;
            const showSimilar = similarVerseNo === verse.aya_no;
            const showTafsir = tafsirVerseNo === verse.aya_no;

            const listBismillah = bismillahFor(verse, script);
            const listDisplayText = verseTextFor(verse, script);

            const isCopied = copiedVerseId === verse.id;

            return (
              <div
                key={verse.id}
                data-verse-key={verseKey}
                className={clsx(
                  'rounded-2xl border transition-all duration-300 overflow-hidden',
                  isHighlighted
                    ? 'border-primary-300 bg-primary-50 shadow-sm'
                    : isConceptHighlighted
                    ? 'border-amber-300 bg-amber-50 shadow-sm'
                    : 'reader-card border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm',
                )}
              >
                {/* Bismillah banner */}
                {listBismillah && (
                  <div className="bg-amber-50 border-b border-amber-100 py-3 px-5 text-center" dir="rtl" lang="ar">
                    <span className={clsx('text-lg text-amber-800 tracking-wide', quranFont)}>
                      {listBismillah}
                    </span>
                  </div>
                )}

                {/* Verse number + index indicator */}
                <div className="flex items-center justify-between px-4 pt-3 pb-1">
                  <div className="flex items-center gap-2">
                    <span
                      ref={isHighlighted ? highlightRef : null}
                      className={clsx(
                        'w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold font-arabic',
                        isHighlighted
                          ? 'bg-primary-600 text-white'
                          : isConceptHighlighted
                          ? 'bg-amber-500 text-white'
                          : 'bg-gray-100 text-gray-600',
                      )}
                    >
                      {toArabicNum(verse.aya_no)}
                    </span>
                    {navMode === 'page' && (
                      <span className="text-xs text-gray-400" dir="rtl" lang="ar">{verse.sura_name_ar}</span>
                    )}
                    <VerseMarkers verse={verse} language={language} />
                  </div>
                  <span className="text-xs text-gray-300">
                    {verseIdx + 1} / {verses.length}
                  </span>
                </div>

                {/* Arabic text */}
                <div className="px-5 pt-2 pb-3" dir="rtl" lang="ar">
                  <p className={clsx('reader-arabic leading-[2.2] text-gray-900', quranFont)} style={arabicFontSize}>
                    <VerseText text={listDisplayText} sura={verse.sura_no} aya={verse.aya_no} />
                  </p>
                </div>

                {/* Translations of the meanings */}
                <VerseTranslations
                  translations={verse.translations ?? []}
                  editions={translationEditions}
                  language={language}
                />

                {/* Action bar */}
                <div className="flex items-center gap-1 px-4 pb-3 flex-wrap">
                  <button
                    onClick={() => setGrammarVerseNo(showGrammar ? null : verse.aya_no)}
                    onMouseEnter={() => prefetchGrammar(verse.sura_no, verse.aya_no)}
                    title={language === 'ar' ? 'إعراب' : 'Grammar'}
                    className={clsx(
                      'inline-flex items-center gap-1.5 px-3 py-1.5 min-h-11 text-xs rounded-lg font-medium transition-colors',
                      showGrammar
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-500 hover:bg-gray-100',
                      language === 'ar' && 'font-arabic',
                    )}
                  >
                    <Languages className="w-3.5 h-3.5" />
                    {language === 'ar' ? 'إعراب' : 'Grammar'}
                  </button>
                  <button
                    onClick={() => setSimilarVerseNo(showSimilar ? null : verse.aya_no)}
                    onMouseEnter={() => prefetchSimilar(verse.sura_no, verse.aya_no)}
                    title={language === 'ar' ? 'آيات متشابهة' : 'Similar verses'}
                    className={clsx(
                      'inline-flex items-center gap-1.5 px-3 py-1.5 min-h-11 text-xs rounded-lg font-medium transition-colors',
                      showSimilar
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'text-gray-500 hover:bg-gray-100',
                      language === 'ar' && 'font-arabic',
                    )}
                  >
                    <GitBranch className="w-3.5 h-3.5" />
                    {language === 'ar' ? 'متشابهة' : 'Similar'}
                  </button>
                  <button
                    onClick={() => setTafsirVerseNo(showTafsir ? null : verse.aya_no)}
                    onMouseEnter={() => prefetchTafsir(verse.sura_no, verse.aya_no)}
                    title={language === 'ar' ? 'التفسير' : 'Tafsir'}
                    className={clsx(
                      'inline-flex items-center gap-1.5 px-3 py-1.5 min-h-11 text-xs rounded-lg font-medium transition-colors',
                      showTafsir
                        ? 'bg-amber-100 text-amber-700'
                        : 'text-gray-500 hover:bg-gray-100',
                      language === 'ar' && 'font-arabic',
                    )}
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    {language === 'ar' ? 'تفسير' : 'Tafsir'}
                  </button>

                  {/* Right-side utilities */}
                  <div className="flex items-center gap-1 ml-auto">
                    <button
                      onClick={() => copyVerse(verse, listDisplayText)}
                      title={language === 'ar' ? 'نسخ الآية' : 'Copy verse'}
                      className="inline-flex items-center justify-center min-h-11 min-w-11 p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      {isCopied
                        ? <Check className="w-3.5 h-3.5 text-green-500" />
                        : <Copy className="w-3.5 h-3.5" />
                      }
                    </button>
                    <button
                      onClick={() => shareImage(verse, listDisplayText)}
                      disabled={imageBusyId === verse.id}
                      title={language === 'ar' ? 'مشاركة كصورة' : 'Share as image'}
                      aria-label={language === 'ar' ? 'مشاركة كصورة' : 'Share as image'}
                      className="inline-flex items-center justify-center min-h-11 min-w-11 p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40"
                    >
                      <ImageIcon className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => shareVerse(verse, listDisplayText)}
                      title={language === 'ar' ? 'مشاركة' : 'Share'}
                      className="inline-flex items-center justify-center min-h-11 min-w-11 p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <Share2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        if (isBookmarked(verse.id)) {
                          removeBookmark(verse.id);
                        } else {
                          addBookmark({
                            id: verse.id,
                            sura_no: verse.sura_no,
                            sura_name_ar: verse.sura_name_ar,
                            sura_name_en: verse.sura_name_en,
                            aya_no: verse.aya_no,
                            text_uthmani: verse.text_uthmani,
                          });
                        }
                      }}
                      title={isBookmarked(verse.id)
                        ? (language === 'ar' ? 'إزالة الإشارة' : 'Remove bookmark')
                        : (language === 'ar' ? 'حفظ' : 'Bookmark')}
                      className={clsx(
                        'inline-flex items-center justify-center min-h-11 min-w-11 p-1.5 rounded-lg transition-colors',
                        isBookmarked(verse.id)
                          ? 'text-amber-500 hover:bg-amber-50'
                          : 'text-gray-400 hover:text-amber-500 hover:bg-amber-50',
                      )}
                    >
                      {isBookmarked(verse.id)
                        ? <BookmarkCheck className="w-3.5 h-3.5" />
                        : <Bookmark className="w-3.5 h-3.5" />
                      }
                    </button>
                    <Link
                      to={`/search?q=${encodeURIComponent(verse.sura_name_ar + ' ' + verse.aya_no)}`}
                      title={language === 'ar' ? 'بحث' : 'Search'}
                      className="inline-flex items-center justify-center min-h-11 min-w-11 p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <Search className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>

                {/* Expandable panels */}
                {(showGrammar || showSimilar || showTafsir) && (
                  <div className="border-t border-gray-100">
                    {showGrammar && (
                      <div className="p-4 bg-gray-50/50">
                        <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">{isAr ? 'الإعراب غير متاح' : 'Grammar analysis unavailable'}</div>}>
                          <Suspense fallback={<div className="h-24 animate-pulse bg-gray-100 rounded-xl" />}>
                            <GrammarAnalysisView
                              suraNo={verse.sura_no}
                              ayaNo={verse.aya_no}
                              verseText={verse.text_uthmani}
                            />
                          </Suspense>
                        </ErrorBoundary>
                      </div>
                    )}
                    {showSimilar && (
                      <div className="p-4 bg-gray-50/50">
                        <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">{isAr ? 'الآيات المتشابهة غير متاحة' : 'Similar verses unavailable'}</div>}>
                          <Suspense fallback={<div className="h-32 animate-pulse bg-gray-100 rounded-xl" />}>
                            <SimilarVersesPanel
                              suraNo={verse.sura_no}
                              ayaNo={verse.aya_no}
                              verseText={verse.text_imlaei}
                              onVerseSelect={(sura, aya) => navigate(`/quran/${sura}?aya=${aya}`)}
                            />
                          </Suspense>
                        </ErrorBoundary>
                      </div>
                    )}
                    {showTafsir && (
                      <div className="p-4 bg-gray-50/50">
                        <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">{isAr ? 'التفسير غير متاح' : 'Tafsir unavailable'}</div>}>
                          <Suspense fallback={<div className="h-48 animate-pulse bg-gray-100 rounded-xl" />}>
                            <TafsirPanel
                              sura={verse.sura_no}
                              ayah={verse.aya_no}
                              verseText={verse.text_uthmani}
                              isExpanded={true}
                            />
                          </Suspense>
                        </ErrorBoundary>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          {markReadBlock}
          <QuranTextAttribution language={language} className="text-center pt-2" />
        </div>
      )}
      </>)}
    </div>
  );
}
