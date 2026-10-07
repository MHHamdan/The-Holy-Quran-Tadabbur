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
import { apiUrl } from '../lib/config';
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Book, ChevronLeft, ChevronRight, BookOpen,
  Languages, GitBranch, FileText, Headphones, Bookmark, BookmarkCheck,
  Copy, Check, Share2, Search,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi, grammarApi, Verse, conceptHighlightsApi, multiConceptApi } from '../lib/api';
import { useBookmarksStore } from '../stores/bookmarksStore';
import { recordSurahVisit } from '../hooks/useReadingProgress';
import { VerseText } from '../components/quran/WordMeaningPopover';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { ErrorPanel, parseAPIError, type APIErrorData } from '../components/common/ErrorPanel';
import clsx from 'clsx';

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

type ViewMode = 'mushaf' | 'list' | 'page';
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

// Bismillah detection patterns for exclusion from highlighting
const BISMILLAH_PATTERNS = [
  'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
  'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
  'بسم الله الرحمن الرحيم',
];

// Split the Bismillah prefix from an Imlaei-script verse.
// The Bismillah is always the first 4 words of verse 1 for surahs that carry it.
// Callers already gate on aya_no===1 and sura_no not in {1, 9}, so we just count words.
// No Arabic string literals — text is extracted directly from the verse data.
function splitBismillahImlaei(text: string): { bismillah: string; verseText: string } | null {
  const clean = text.replace(/^\uFEFF/, ''); // strip BOM (present only on 1:1)
  const words = clean.split(/\s+/);
  if (words.length <= 4) return null; // guard: whole verse is just the Bismillah
  const bismillah = words.slice(0, 4).join(' ');
  const verseText = words.slice(4).join(' ');
  return verseText ? { bismillah, verseText } : null;
}

/**
 * Check if a verse is primarily the Bismillah phrase.
 * Used to exclude from concept highlighting to avoid redundant matches.
 */
const isBismillahVerse = (text: string): boolean => {
  if (!text) return false;
  const normalized = text.replace(/[\u064B-\u065F\u0670]/g, '').trim();
  return BISMILLAH_PATTERNS.some(pattern => {
    const normPattern = pattern.replace(/[\u064B-\u065F\u0670]/g, '').trim();
    // Check if verse is essentially just Bismillah (allowing minor variations)
    return normalized === normPattern ||
           normalized.replace(/\s+/g, '') === normPattern.replace(/\s+/g, '');
  });
};


export function QuranPage() {
  const { suraNo } = useParams<{ suraNo: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const highlightAya = searchParams.get('aya');
  const pageParam = searchParams.get('page');
  const conceptParam = searchParams.get('concept');  // Single concept ID for highlighting
  const conceptsParam = searchParams.get('concepts'); // Multiple concept IDs (comma-separated)

  const { language } = useLanguageStore();
  const [verses, setVerses] = useState<Verse[]>([]);
  const [suras, setSuras] = useState<SuraInfo[]>([]);
  const [loading, setLoading] = useState(true);
  // Verse text comes from the backend; a failed load must not look like an empty surah.
  const [loadError, setLoadError] = useState<APIErrorData | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('mushaf');
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

  const copyVerse = useCallback((verse: Verse, displayText: string) => {
    const ref = `(${verse.sura_name_ar} ${toArabicNum(verse.aya_no)})`;
    const full = `${displayText} ${ref}`;
    navigator.clipboard.writeText(full).then(() => {
      setCopiedVerseId(verse.id);
      setTimeout(() => setCopiedVerseId(null), 2000);
    }).catch(() => {});
  }, []);

  const shareVerse = useCallback((verse: Verse) => {
    const url = `${window.location.origin}/quran/${verse.sura_no}?aya=${verse.aya_no}`;
    if (navigator.share) {
      navigator.share({ url, title: `${verse.sura_name_ar} ${verse.aya_no}` }).catch(() => {});
    } else {
      navigator.clipboard.writeText(url).catch(() => {});
    }
  }, []);

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

  const currentSura = parseInt(suraNo || '1', 10);

  // Load metadata
  useEffect(() => {
    async function loadMetadata() {
      try {
        const metaRes = await fetch(apiUrl('/api/v1/quran/metadata'));
        const meta = await metaRes.json();
        setSuras(meta.suras || []);
      } catch (error) {
        console.error('Failed to load metadata:', error);
      }
    }
    loadMetadata();
  }, []);

  // Load content based on navigation mode
  useEffect(() => {
    if (navMode === 'page' && currentPage >= 1 && currentPage <= 604) {
      loadPage(currentPage);
    } else if (currentSura >= 1 && currentSura <= 114) {
      loadSura(currentSura);
    }
  }, [currentSura, navMode, currentPage]);

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
        highlightRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    }
  }, [loading, highlightAya]);

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

  async function loadSura(suraNo: number) {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await quranApi.getSuraVerses(suraNo);
      setVerses(res.data);
      // Set current page from first verse
      if (res.data.length > 0) {
        setCurrentPage(res.data[0].page_no);
      }
    } catch (error) {
      console.error('Failed to load sura:', error);
      setVerses([]);
      setLoadError(parseAPIError(error));
    } finally {
      setLoading(false);
    }
  }

  async function loadPage(pageNo: number) {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await quranApi.getPageVerses(pageNo);
      setVerses(res.data);
    } catch (error) {
      console.error('Failed to load page:', error);
      setVerses([]);
      setLoadError(parseAPIError(error));
    } finally {
      setLoading(false);
    }
  }

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

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Back Link */}
      <Link
        to="/stories"
        className={clsx('inline-flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-6', language === 'ar' && 'font-arabic')}
      >
        <ArrowLeft className={clsx('w-4 h-4', language === 'ar' && 'rotate-180')} />
        {language === 'ar' ? 'العودة للقصص' : 'Back to Stories'}
      </Link>

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
                    value={currentPage}
                    onChange={(e) => navigateToPage(parseInt(e.target.value, 10))}
                    className="input py-1 px-2 w-20 text-center text-sm"
                  />
                  <span className="text-sm text-gray-500">/ 604</span>
                  <button
                    onClick={() => navigateToPage(currentPage + 1)}
                    disabled={currentPage >= 604}
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
                    className={clsx(
                      'p-2 rounded-lg hover:bg-gray-100 transition-colors',
                      currentSura <= 1 && 'opacity-50 pointer-events-none'
                    )}
                  >
                    {language === 'ar' ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                  </Link>
                  <select
                    value={currentSura}
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

      {/* Audio Player */}
      {showAudioPlayer && (
        <div className="mb-6">
          <ErrorBoundary fallback={<div className="h-16 flex items-center justify-center text-sm text-amber-600 bg-amber-50 rounded-lg border border-amber-200">Audio player unavailable</div>}>
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
      ) : loadError ? (
        <ErrorPanel
          error={loadError}
          onRetry={() => (navMode === 'page' ? loadPage(currentPage) : loadSura(currentSura))}
        />
      ) : viewMode === 'mushaf' ? (
        /* Mushaf Style View */
        <div className="rounded-2xl bg-[#fefcf3] border-2 border-amber-200 shadow-lg overflow-hidden">
          {/* Decorative Header */}
          <div className="bg-gradient-to-r from-amber-800 via-amber-700 to-amber-800 text-center py-4 px-6">
            <h2 className="text-2xl font-bold font-arabic text-amber-50 tracking-widest">
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
          <div className="text-center leading-[3] font-arabic text-2xl text-gray-900" dir="rtl">
            {verses.map((verse, idx) => {
              const verseKey = `${verse.sura_no}:${verse.aya_no}`;
              // Exclude Bismillah verses from concept highlighting to avoid redundant matches
              const isConceptHighlighted = conceptHighlights.has(verseKey) &&
                                           !isBismillahVerse(verse.text_imlaei);
              // Highlight specific verse: check both aya_no AND sura_no to avoid cross-sura false matches on same page
              const isHighlighted = (highlightAya &&
                                    parseInt(highlightAya, 10) === verse.aya_no &&
                                    verse.sura_no === currentSura) ||
                                   (currentPlayingAya === verse.aya_no && verse.sura_no === currentSura);

              // Extract Bismillah from verse 1 for surahs that have it as a prefix
              const isFirstVerse = verse.aya_no === 1;
              const hasBismillahPrefix = isFirstVerse && verse.sura_no !== 1 && verse.sura_no !== 9;
              const bismillahSplit = hasBismillahPrefix ? splitBismillahImlaei(verse.text_imlaei) : null;
              // Strip BOM (appears only on 1:1 in source data) and Bismillah prefix for display
              const displayText = bismillahSplit
                ? bismillahSplit.verseText
                : verse.text_imlaei.replace(/^\uFEFF/, '');
              // Show Bismillah block for: page mode (when surah starts on page) or surah mode
              const showBismillahBlock = bismillahSplit !== null && (
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
                  {showBismillahBlock && bismillahSplit && (
                    <div className="block text-center mb-4" dir="rtl">
                      <span className="text-xl font-arabic text-amber-800">{bismillahSplit.bismillah}</span>
                    </div>
                  )}
                  <span
                    ref={isHighlighted ? highlightRef : null}
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
        </div>
      ) : (
        /* List View with Translations */
        <div className="space-y-3">
          {verses.map((verse, verseIdx) => {
            const verseKey = `${verse.sura_no}:${verse.aya_no}`;
            const isConceptHighlighted = conceptHighlights.has(verseKey) &&
                                         !isBismillahVerse(verse.text_imlaei);
            const isHighlighted = (highlightAya &&
                                  parseInt(highlightAya, 10) === verse.aya_no &&
                                  verse.sura_no === currentSura) ||
                                 (currentPlayingAya === verse.aya_no && verse.sura_no === currentSura);
            const showGrammar = grammarVerseNo === verse.aya_no;
            const showSimilar = similarVerseNo === verse.aya_no;
            const showTafsir = tafsirVerseNo === verse.aya_no;

            const hasBismillahPrefixList = verse.aya_no === 1 && verse.sura_no !== 1 && verse.sura_no !== 9;
            const listBismillahSplit = hasBismillahPrefixList ? splitBismillahImlaei(verse.text_imlaei) : null;
            const listDisplayText = listBismillahSplit
              ? listBismillahSplit.verseText
              : verse.text_imlaei.replace(/^\uFEFF/, '');

            const translation = verse.translations?.find(
              t => t.language === (language === 'ar' ? 'ar' : 'en')
            )?.text || verse.translations?.[0]?.text;

            const isCopied = copiedVerseId === verse.id;

            return (
              <div
                key={verse.id}
                className={clsx(
                  'rounded-2xl border transition-all duration-300 overflow-hidden',
                  isHighlighted
                    ? 'border-primary-300 bg-primary-50 shadow-sm'
                    : isConceptHighlighted
                    ? 'border-amber-300 bg-amber-50 shadow-sm'
                    : 'border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm',
                )}
              >
                {/* Bismillah banner */}
                {listBismillahSplit && (
                  <div className="bg-amber-50 border-b border-amber-100 py-3 px-5 text-center" dir="rtl">
                    <span className="text-lg font-arabic text-amber-800 tracking-wide">
                      {listBismillahSplit.bismillah}
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
                      <span className="text-xs text-gray-400">{verse.sura_name_ar}</span>
                    )}
                  </div>
                  <span className="text-xs text-gray-300">
                    {verseIdx + 1} / {verses.length}
                  </span>
                </div>

                {/* Arabic text */}
                <div className="px-5 pt-2 pb-3" dir="rtl">
                  <p className="text-2xl leading-[2.2] font-arabic text-gray-900">
                    <VerseText text={listDisplayText} sura={verse.sura_no} aya={verse.aya_no} />
                  </p>
                </div>

                {/* Translation */}
                {translation && (
                  <div
                    className="mx-5 mb-3 px-4 py-3 bg-gray-50 rounded-xl border-l-4 border-primary-200 text-sm text-gray-600 leading-relaxed"
                    dir={language === 'ar' ? 'rtl' : 'ltr'}
                  >
                    {translation}
                  </div>
                )}

                {/* Action bar */}
                <div className="flex items-center gap-1 px-4 pb-3 flex-wrap">
                  <button
                    onClick={() => setGrammarVerseNo(showGrammar ? null : verse.aya_no)}
                    onMouseEnter={() => prefetchGrammar(verse.sura_no, verse.aya_no)}
                    title={language === 'ar' ? 'إعراب' : 'Grammar'}
                    className={clsx(
                      'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg font-medium transition-colors',
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
                      'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg font-medium transition-colors',
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
                      'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg font-medium transition-colors',
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
                      className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      {isCopied
                        ? <Check className="w-3.5 h-3.5 text-green-500" />
                        : <Copy className="w-3.5 h-3.5" />
                      }
                    </button>
                    <button
                      onClick={() => shareVerse(verse)}
                      title={language === 'ar' ? 'مشاركة' : 'Share'}
                      className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
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
                            text_uthmani: verse.text_imlaei,
                          });
                        }
                      }}
                      title={isBookmarked(verse.id)
                        ? (language === 'ar' ? 'إزالة الإشارة' : 'Remove bookmark')
                        : (language === 'ar' ? 'حفظ' : 'Bookmark')}
                      className={clsx(
                        'p-1.5 rounded-lg transition-colors',
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
                      className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
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
                        <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">Grammar analysis unavailable</div>}>
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
                        <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">Similar verses unavailable</div>}>
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
                        <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">Tafsir unavailable</div>}>
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
        </div>
      )}
    </div>
  );
}
