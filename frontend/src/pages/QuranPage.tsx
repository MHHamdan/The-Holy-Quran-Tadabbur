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
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Book, ChevronLeft, ChevronRight, BookOpen,
  Languages, GitBranch, FileText, Headphones, Bookmark, BookmarkCheck
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi, Verse, conceptHighlightsApi, multiConceptApi } from '../lib/api';
import { useBookmarksStore } from '../stores/bookmarksStore';
import { recordSurahVisit } from '../hooks/useReadingProgress';
import { VerseText } from '../components/quran/WordMeaningPopover';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
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

/**
 * Splits the Bismillah prefix from text_uthmani for display.
 * Surahs 2–114 (except At-Tawba, 9) store the Bismillah as a prefix on verse 1.
 * Al-Fatiha (1): Bismillah IS verse 1:1 — caller should never strip it.
 * Uses 3-Alef-Wasla scan to avoid depending on diacritic character order.
 */
function splitBismillah(text: string): { bismillah: string; verseText: string } | null {
  const ALEF_WASLA = 'ٱ'; // U+0671
  const MIM = 'م';        // U+0645
  let count = 0;
  let pos = 0;
  for (let i = 0; i < text.length; i++) {
    if (text[i] === ALEF_WASLA) {
      // If first ٱ is too far in, text doesn't start with Bismillah
      if (count === 0 && i > 15) return null;
      count++;
      if (count === 3) { pos = i; break; }
    }
  }
  if (count < 3) return null; // At-Tawba (9) or no Bismillah
  pos++;
  while (pos < text.length) {
    if (text[pos] === MIM) {
      pos++;
      while (pos < text.length) {
        const cp = text.codePointAt(pos)!;
        if (cp >= 0x064B && cp <= 0x065F) pos++;
        else break;
      }
      break;
    }
    pos++;
  }
  const bismillah = text.slice(0, pos).trim();
  const verseText = text.slice(pos).trimStart();
  if (!verseText) return null;
  return { bismillah, verseText };
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

  const currentSura = parseInt(suraNo || '1', 10);

  // Load metadata
  useEffect(() => {
    async function loadMetadata() {
      try {
        const metaRes = await fetch('/api/v1/quran/metadata');
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
    try {
      const res = await quranApi.getSuraVerses(suraNo);
      setVerses(res.data);
      // Set current page from first verse
      if (res.data.length > 0) {
        setCurrentPage(res.data[0].page_no);
      }
    } catch (error) {
      console.error('Failed to load sura:', error);
    } finally {
      setLoading(false);
    }
  }

  async function loadPage(pageNo: number) {
    setLoading(true);
    try {
      const res = await quranApi.getPageVerses(pageNo);
      setVerses(res.data);
    } catch (error) {
      console.error('Failed to load page:', error);
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
      ) : viewMode === 'mushaf' ? (
        /* Mushaf Style View */
        <div className="card bg-[#fefcf3] border-2 border-amber-200 shadow-lg">
          {/* Page Navigation Header */}
          {navMode === 'page' && Object.keys(versesBySura).length > 1 && (
            <div className="text-center mb-4 text-sm text-amber-700">
              {Object.entries(versesBySura).map(([suraNo, suraVerses], idx) => (
                <span key={suraNo}>
                  {idx > 0 && ' | '}
                  {language === 'ar' ? suraVerses[0].sura_name_ar : suraVerses[0].sura_name_en}
                </span>
              ))}
            </div>
          )}

          {/* Decorative Header */}
          <div className="text-center mb-6 pb-4 border-b-2 border-amber-300">
            <div className="inline-block px-8 py-2 bg-gradient-to-r from-amber-100 via-amber-50 to-amber-100 rounded-lg border border-amber-300">
              <h2 className="text-2xl font-bold font-arabic text-amber-900">
                {navMode === 'surah'
                  ? verses[0]?.sura_name_ar
                  : language === 'ar' ? `صفحة ${toArabicNum(currentPage)}` : `Page ${currentPage}`}
              </h2>
            </div>
          </div>

          {/* Verses in Mushaf Style */}
          <div className="text-center leading-[3] font-arabic text-2xl text-gray-900" dir="rtl">
            {verses.map((verse, idx) => {
              const verseKey = `${verse.sura_no}:${verse.aya_no}`;
              // Exclude Bismillah verses from concept highlighting to avoid redundant matches
              const isConceptHighlighted = conceptHighlights.has(verseKey) &&
                                           !isBismillahVerse(verse.text_uthmani);
              // Highlight specific verse: check both aya_no AND sura_no to avoid cross-sura false matches on same page
              const isHighlighted = (highlightAya &&
                                    parseInt(highlightAya, 10) === verse.aya_no &&
                                    verse.sura_no === currentSura) ||
                                   (currentPlayingAya === verse.aya_no && verse.sura_no === currentSura);

              // Extract Bismillah from verse 1 for surahs that have it as a prefix
              const isFirstVerse = verse.aya_no === 1;
              const hasBismillahPrefix = isFirstVerse && verse.sura_no !== 1 && verse.sura_no !== 9;
              const bismillahSplit = hasBismillahPrefix ? splitBismillah(verse.text_uthmani) : null;
              // Strip BOM (appears only on 1:1 in source data) and Bismillah prefix for display
              const displayText = bismillahSplit
                ? bismillahSplit.verseText
                : verse.text_uthmani.replace(/^﻿/, '');
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
          <div className={clsx('mt-6 pt-4 border-t-2 border-amber-300 flex justify-center gap-4 text-sm text-amber-700', language === 'ar' && 'font-arabic')}>
            <span>{language === 'ar' ? 'الصفحة' : 'Page'}: {toArabicNum(firstVerse?.page_no || currentPage)}</span>
            <span>•</span>
            <span>{language === 'ar' ? 'الجزء' : 'Juz'}: {toArabicNum(firstVerse?.juz_no || 1)}</span>
          </div>
        </div>
      ) : (
        /* List View with Translations */
        <div className="card">
          <div className="space-y-6">
            {verses.map((verse) => {
              const verseKey = `${verse.sura_no}:${verse.aya_no}`;
              // Exclude Bismillah verses from concept highlighting to avoid redundant matches
              const isConceptHighlighted = conceptHighlights.has(verseKey) &&
                                           !isBismillahVerse(verse.text_uthmani);
              // Highlight specific verse: check both aya_no AND sura_no to avoid cross-sura false matches on same page
              const isHighlighted = (highlightAya &&
                                    parseInt(highlightAya, 10) === verse.aya_no &&
                                    verse.sura_no === currentSura) ||
                                   (currentPlayingAya === verse.aya_no && verse.sura_no === currentSura);
              const showGrammar = grammarVerseNo === verse.aya_no;
              const showSimilar = similarVerseNo === verse.aya_no;
              const showTafsir = tafsirVerseNo === verse.aya_no;

              // Strip Bismillah prefix from verse 1 (surahs 2-114 except 9)
              const hasBismillahPrefixList = verse.aya_no === 1 && verse.sura_no !== 1 && verse.sura_no !== 9;
              const listBismillahSplit = hasBismillahPrefixList ? splitBismillah(verse.text_uthmani) : null;
              const listDisplayText = listBismillahSplit
                ? listBismillahSplit.verseText
                : verse.text_uthmani.replace(/^﻿/, '');

              return (
                <div
                  key={verse.id}
                  className={clsx(
                    'p-4 rounded-lg transition-all duration-300',
                    isHighlighted ? 'bg-primary-50 ring-2 ring-primary-300' :
                    isConceptHighlighted ? 'bg-amber-50 ring-2 ring-amber-300' : 'hover:bg-gray-50'
                  )}
                >
                  {/* Bismillah header for verse 1 — text from verse data, never hardcoded */}
                  {listBismillahSplit && (
                    <div className="text-center mb-3 py-2 border-y border-amber-200" dir="rtl">
                      <span className="text-xl font-arabic text-amber-800">{listBismillahSplit.bismillah}</span>
                    </div>
                  )}
                  <div className="flex items-start gap-4" dir="rtl">
                    <span
                      ref={isHighlighted ? highlightRef : null}
                      className={clsx(
                        'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm',
                        isHighlighted ? 'bg-primary-600 text-white' :
                        isConceptHighlighted ? 'bg-amber-500 text-white' : 'bg-gray-100 text-gray-700'
                      )}
                    >
                      {toArabicNum(verse.aya_no)}
                    </span>
                    <div className="flex-1">
                      <p className="text-xl leading-loose font-arabic text-gray-900 mb-3">
                        <VerseText text={listDisplayText} sura={verse.sura_no} aya={verse.aya_no} />
                      </p>
                      {verse.translations && verse.translations.length > 0 && (
                        <p className={clsx('text-sm text-gray-600 leading-relaxed', language === 'ar' && 'font-arabic')} dir={language === 'ar' ? 'rtl' : 'ltr'}>
                          {verse.translations.find(t => t.language === (language === 'ar' ? 'ar' : 'en'))?.text ||
                           verse.translations[0]?.text}
                        </p>
                      )}
                      {/* Analysis toggle buttons */}
                      <div className="mt-3 flex items-center gap-2">
                        <button
                          onClick={() => setGrammarVerseNo(showGrammar ? null : verse.aya_no)}
                          className={clsx(
                            'inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors',
                            showGrammar
                              ? 'bg-primary-100 text-primary-700 hover:bg-primary-200'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                            language === 'ar' && 'font-arabic'
                          )}
                        >
                          <Languages className="w-4 h-4" />
                          {language === 'ar' ? 'إعراب' : 'Grammar'}
                        </button>
                        <button
                          onClick={() => setSimilarVerseNo(showSimilar ? null : verse.aya_no)}
                          className={clsx(
                            'inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors',
                            showSimilar
                              ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                            language === 'ar' && 'font-arabic'
                          )}
                        >
                          <GitBranch className="w-4 h-4" />
                          {language === 'ar' ? 'آيات متشابهة' : 'Similar'}
                        </button>
                        <button
                          onClick={() => setTafsirVerseNo(showTafsir ? null : verse.aya_no)}
                          className={clsx(
                            'inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors',
                            showTafsir
                              ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                            language === 'ar' && 'font-arabic'
                          )}
                        >
                          <BookOpen className="w-4 h-4" />
                          {language === 'ar' ? 'التفسير' : 'Tafsir'}
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
                          className={clsx(
                            'inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors',
                            isBookmarked(verse.id)
                              ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                            language === 'ar' && 'font-arabic'
                          )}
                          title={isBookmarked(verse.id) ? (language === 'ar' ? 'إزالة الإشارة' : 'Remove bookmark') : (language === 'ar' ? 'حفظ الآية' : 'Bookmark')}
                        >
                          {isBookmarked(verse.id)
                            ? <BookmarkCheck className="w-4 h-4" />
                            : <Bookmark className="w-4 h-4" />}
                          {language === 'ar'
                            ? (isBookmarked(verse.id) ? 'محفوظة' : 'حفظ')
                            : (isBookmarked(verse.id) ? 'Saved' : 'Save')}
                        </button>
                      </div>
                      {/* Grammar analysis panel */}
                      {showGrammar && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                          <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">Grammar analysis unavailable</div>}>
                            <Suspense fallback={<div className="h-24 animate-pulse bg-gray-100 rounded-lg" />}>
                              <GrammarAnalysisView
                                suraNo={verse.sura_no}
                                ayaNo={verse.aya_no}
                                verseText={verse.text_uthmani}
                              />
                            </Suspense>
                          </ErrorBoundary>
                        </div>
                      )}
                      {/* Similar verses panel */}
                      {showSimilar && (
                        <div className="mt-4">
                          <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">Similar verses unavailable</div>}>
                            <Suspense fallback={<div className="h-32 animate-pulse bg-gray-100 rounded-lg" />}>
                              <SimilarVersesPanel
                                suraNo={verse.sura_no}
                                ayaNo={verse.aya_no}
                                verseText={verse.text_uthmani}
                                onVerseSelect={(sura, aya) => {
                                  navigate(`/quran/${sura}?aya=${aya}`);
                                }}
                              />
                            </Suspense>
                          </ErrorBoundary>
                        </div>
                      )}
                      {/* Tafsir panel */}
                      {showTafsir && (
                        <div className="mt-4">
                          <ErrorBoundary fallback={<div className="text-sm text-amber-600 p-2">Tafsir unavailable</div>}>
                            <Suspense fallback={<div className="h-48 animate-pulse bg-gray-100 rounded-lg" />}>
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
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
