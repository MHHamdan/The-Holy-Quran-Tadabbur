/**
 * Mushaf Page - المصحف الشريف
 *
 * Traditional King Fahad Mushaf style display with:
 * - Flowing text layout (verses displayed together, not separately)
 * - Inline verse number markers (۝)
 * - Surah headers with Bismillah
 * - Click to select verse for tafseer/audio
 *
 * Performance Optimizations:
 * - React Query for data fetching and caching
 * - Prefetching for smooth navigation
 * - Memoized components
 */

import { useState, useCallback, useRef, memo, useTransition, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Loader2,
  ZoomIn,
  ZoomOut,
  Play,
  Pause,
  Settings,
  Sparkles,
  MessageSquare,
  Lightbulb,
  HelpCircle,
  X,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  Quote,
  Bookmark,
  BookmarkCheck,
  Share2,
} from 'lucide-react';
import { useBookmarksStore } from '../stores/bookmarksStore';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi, Verse, api, verseAskAiApi } from '../lib/api';
import type { VerseAskAiResponse, Citation } from '../lib/api';
import { queryKeys, staleTimes } from '../lib/queryClient';
import { shareContent } from '../lib/native';
import { getReadingProgress, recordReadingPosition } from '../hooks/useReadingProgress';
import { useReaderSettingsStore, verseTextFor, bismillahFor, applyReaderThemeToDocument } from '../stores/readerSettingsStore';
import { ReaderThemePicker } from '../components/quran/ReaderThemePicker';
import { QuranTextAttribution } from '../components/quran/QuranTextAttribution';
import { surahVerseCount } from '../data/surahVerseCounts';
import { SURAH_NAMES } from '../data/surahNames';
import { TafsirSourceFooter, type TafsirEditionMeta } from '../components/reader/TafsirSourceFooter';
import {
  firstPageOfJuz, firstPageOfSurah, surahOnPage, SURAH_REVELATION, TOTAL_MUSHAF_PAGES,
} from '../components/reader/surahNavigation';
import { playableUrl } from '../lib/offlineAudio';

// =============================================================================
// Types & Interfaces
// =============================================================================

interface TafsirEdition {
  id: string;
  translationKey: string;
}

interface TafsirData {
  text: string;
  /** Provider the text was retrieved from (quran_com, quran_tafseer). */
  source: string;
  /** Edition metadata from the API: title, author, language. */
  edition: TafsirEditionMeta;
}

interface ReciterOption {
  id: string;
  translationKey: string;
}

// =============================================================================
// Constants
// =============================================================================

const TOTAL_PAGES = TOTAL_MUSHAF_PAGES;

// Arabic tafsir editions, shown in both UI languages (always right-to-left).
// No English tafsir is offered: the English editions previously listed here
// (Ibn Kathir EN, Ma'arif al-Qur'an, Tazkirul Quran) have no confirmed licence
// and are awaiting owner review. Tafsir audio stays off until its terms are
// confirmed.
const TAFSIR_EDITIONS: TafsirEdition[] = [
  { id: 'muyassar', translationKey: 'tafseer_muyassar' },
  { id: 'ibn_kathir', translationKey: 'tafseer_ibn_kathir' },
  { id: 'tabari', translationKey: 'tafseer_tabari' },
  { id: 'qurtubi', translationKey: 'tafseer_qurtubi' },
  { id: 'jalalayn', translationKey: 'tafseer_jalalayn' },
  { id: 'saadi', translationKey: 'tafseer_saadi' },
  { id: 'baghawi', translationKey: 'tafseer_baghawi' },
];

const RECITERS: ReciterOption[] = [
  { id: 'mishary_afasy', translationKey: 'reciter_mishary' },
  { id: 'abdul_basit', translationKey: 'reciter_abdul_basit' },
  { id: 'husary', translationKey: 'reciter_husary' },
  { id: 'maher_muaiqly', translationKey: 'reciter_maher' },
  { id: 'saud_shuraim', translationKey: 'reciter_shuraim' },
];

const ARABIC_NUMS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];



// =============================================================================
// Typed page items — surah header OR verse
// =============================================================================

interface SurahHeaderItem {
  type: 'header';
  suraNo: number;
  suraNameAr: string;   // from quran_uthmani.json — already has سُورَةُ prefix
  suraNameEn: string;
  ayahCount: number;
  bismillahText: string | null; // extracted from text_imlaei — never hardcoded
  revelationType: 'makki' | 'madani' | 'unknown';
}

interface VerseItem {
  type: 'verse';
  verse: Verse;
  displayText: string;  // text_imlaei with Bismillah prefix stripped for ayah 1
}

type PageItem = SurahHeaderItem | VerseItem;

// =============================================================================
// Utility Functions
// =============================================================================

function toArabicNumber(num: number): string {
  return num.toString().split('').map(d => ARABIC_NUMS[parseInt(d)]).join('');
}




// =============================================================================
// Custom Hooks
// =============================================================================

function usePageVerses(pageNo: number) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.quran.page(pageNo),
    queryFn: async () => {
      const response = await quranApi.getPageVerses(pageNo);
      return response.data as Verse[];
    },
    staleTime: staleTimes.quranText,
    enabled: pageNo >= 1 && pageNo <= TOTAL_PAGES,
  });

  const prefetchAdjacent = useCallback(() => {
    if (pageNo > 1) {
      queryClient.prefetchQuery({
        queryKey: queryKeys.quran.page(pageNo - 1),
        queryFn: () => quranApi.getPageVerses(pageNo - 1).then(r => r.data),
        staleTime: staleTimes.quranText,
      });
    }
    if (pageNo < TOTAL_PAGES) {
      queryClient.prefetchQuery({
        queryKey: queryKeys.quran.page(pageNo + 1),
        queryFn: () => quranApi.getPageVerses(pageNo + 1).then(r => r.data),
        staleTime: staleTimes.quranText,
      });
    }
  }, [pageNo, queryClient]);

  return { ...query, prefetchAdjacent };
}

function useTafsir(
  suraNo: number,
  ayaNo: number,
  edition: string,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.tafsir.verse(suraNo, ayaNo, edition),
    queryFn: async (): Promise<TafsirData> => {
      const response = await api.get(`/tafseer/external/verse/${suraNo}/${ayaNo}`, {
        params: { edition }
      });
      return {
        text: response.data.text || '',
        source: response.data.source || '',
        // Keep the edition metadata: the excerpt is never shown without it.
        edition: { id: edition, language: 'ar', ...(response.data.edition ?? {}) },
      };
    },
    staleTime: staleTimes.tafsir,
    enabled: enabled && !!edition && suraNo > 0 && ayaNo > 0,
  });
}

// =============================================================================
// Surah Header Component (for when a new surah starts on the page)
// =============================================================================

const SurahHeader = memo(function SurahHeader({
  suraNameAr, suraNameEn, ayahCount, bismillahText, revelationType,
}: SurahHeaderItem) {
  const typeLabel = revelationType === 'makki' ? 'مكية' : revelationType === 'madani' ? 'مدنية' : '';

  return (
    <div className="ksu-surah-header" dir="rtl">
      {/* Ornamental name banner */}
      <div className="ksu-surah-box">
        <div className="ksu-surah-deco">❧</div>
        <div className="ksu-surah-name">{suraNameAr}</div>
        <div className="ksu-surah-meta">
          {typeLabel && <span>{typeLabel}</span>}
          {typeLabel && <span className="ksu-dot">·</span>}
          <span dir="ltr">{suraNameEn}</span>
          <span className="ksu-dot">·</span>
          <span>{toArabicNumber(ayahCount)} آية</span>
        </div>
        <div className="ksu-surah-deco">❧</div>
      </div>

      {/* Bismillah — extracted from verified text_imlaei, never hardcoded */}
      {bismillahText && (
        <div className="ksu-bismillah">{bismillahText}</div>
      )}
    </div>
  );
});

// =============================================================================
// Verse Panel Component (shows when a verse is selected)
// =============================================================================

interface VersePanelProps {
  verse: Verse;
  edition: TafsirEdition | undefined;
  language: 'ar' | 'en';
  isPlaying: boolean;
  audioError: boolean;
  onPlayAudio: () => void;
  onOpenAI: () => void;
  onClose: () => void;
}

const VersePanel = memo(function VersePanel({
  verse,
  edition,
  language,
  isPlaying,
  audioError,
  onPlayAudio,
  onOpenAI,
  onClose,
}: VersePanelProps) {
  const { t } = useLanguageStore();
  const { addBookmark, removeBookmark, isBookmarked } = useBookmarksStore();
  const [showTafsir, setShowTafsir] = useState(true);
  const [copiedVerse, setCopiedVerse] = useState(false);
  const bookmarked = isBookmarked(verse.id);

  const toggleBookmark = useCallback(() => {
    if (bookmarked) {
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
  }, [bookmarked, verse, addBookmark, removeBookmark]);

  const shareVerse = useCallback(async () => {
    const ref = `${verse.sura_name_en} (${verse.sura_no}:${verse.aya_no})`;
    await shareContent({
      title: ref,
      text: `${verse.text_uthmani}\n— ${ref}`,
      path: `/quran/${verse.sura_no}?aya=${verse.aya_no}`,
    });
  }, [verse]);

  const copyVerseWithAttribution = useCallback(() => {
    const ref = `${verse.sura_name_en} (${verse.sura_no}:${verse.aya_no})`;
    const text = `${verse.text_uthmani}\n— ${ref}\n[Qur'an text: Tanzil Project, tanzil.net, CC BY 3.0]`;
    navigator.clipboard.writeText(text).catch(console.error);
    setCopiedVerse(true);
    setTimeout(() => setCopiedVerse(false), 2000);
  }, [verse]);

  const { data: tafsirData, isLoading: tafsirLoading } = useTafsir(
    verse.sura_no,
    verse.aya_no,
    edition?.id ?? '',
    showTafsir,
  );
  const tafsirLang = tafsirData?.edition.language === 'en' ? 'en' : 'ar';
  const ar = language === 'ar';
  const actionBtn = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors min-h-[36px]';

  return (
    <div
      className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-amber-400 shadow-2xl z-50 max-h-[50vh] overflow-y-auto overflow-x-hidden safe-area-bottom"
      dir={ar ? 'rtl' : 'ltr'}
      role="dialog"
      aria-label={ar ? 'الآية المحددة' : 'Selected verse'}
    >
      {/* Header: reference + close on the first row, actions wrap below */}
      <div className="sticky top-0 bg-gradient-to-r from-emerald-700 to-emerald-600 text-white px-4 py-3 space-y-2">
        <div className="flex items-center gap-3 min-w-0">
          <span className="font-mushaf text-lg truncate" dir="rtl" lang="ar">
            {verse.sura_name_ar} : {toArabicNumber(verse.aya_no)}
          </span>
          <span className="text-sm text-white/70 truncate" dir="ltr" lang="en">
            ({verse.sura_name_en} {verse.sura_no}:{verse.aya_no})
          </span>
          <button
            onClick={onClose}
            className="ms-auto p-2 rounded-lg hover:bg-white/20 transition-colors flex-shrink-0"
            aria-label={ar ? 'إغلاق' : 'Close'}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={onPlayAudio}
            className={clsx(actionBtn, isPlaying ? 'bg-red-500 hover:bg-red-600' : 'bg-white/20 hover:bg-white/30')}
            aria-pressed={isPlaying}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? t('mushaf_pause') : t('mushaf_listen')}
          </button>
          <button
            onClick={copyVerseWithAttribution}
            className={clsx(actionBtn, 'bg-white/20 hover:bg-white/30')}
            aria-label={ar ? 'نسخ الآية مع المصدر' : 'Copy verse with attribution'}
            title={ar ? 'نسخ الآية مع المصدر' : 'Copy verse with attribution'}
          >
            {copiedVerse ? <Check className="w-4 h-4 text-green-300" /> : <Copy className="w-4 h-4" />}
            <span className="hidden sm:inline">{copiedVerse ? (ar ? 'تم النسخ' : 'Copied') : (ar ? 'نسخ' : 'Copy')}</span>
          </button>
          <button
            onClick={toggleBookmark}
            className={clsx(actionBtn, bookmarked ? 'bg-amber-400 hover:bg-amber-500 text-white' : 'bg-white/20 hover:bg-white/30')}
            aria-pressed={bookmarked}
            aria-label={ar ? (bookmarked ? 'إزالة الإشارة' : 'حفظ الآية') : (bookmarked ? 'Remove bookmark' : 'Bookmark verse')}
            title={ar ? (bookmarked ? 'إزالة الإشارة' : 'حفظ الآية') : (bookmarked ? 'Remove bookmark' : 'Bookmark verse')}
          >
            {bookmarked ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
            <span className="hidden sm:inline">{bookmarked ? (ar ? 'محفوظة' : 'Saved') : (ar ? 'حفظ' : 'Save')}</span>
          </button>
          <button
            onClick={shareVerse}
            className={clsx(actionBtn, 'bg-white/20 hover:bg-white/30')}
            aria-label={ar ? 'مشاركة الآية' : 'Share verse'}
            title={ar ? 'مشاركة الآية' : 'Share verse'}
          >
            <Share2 className="w-4 h-4" />
            <span className="hidden sm:inline">{ar ? 'مشاركة' : 'Share'}</span>
          </button>
          <button
            onClick={onOpenAI}
            className={clsx(actionBtn, 'bg-purple-500 hover:bg-purple-600')}
          >
            <Sparkles className="w-4 h-4" />
            {t('ai_assistant')}
          </button>
        </div>
      </div>

      {audioError && (
        <p role="status" className="px-4 py-2 text-sm bg-red-50 text-red-700 border-b border-red-200">
          {ar ? 'تعذّر تشغيل التلاوة' : 'Could not play recitation'}
        </p>
      )}

      {/* Selected Verse Text */}
      <div className="px-6 py-4 bg-amber-50 border-b border-amber-200">
        <p className="font-mushaf text-xl text-gray-900 leading-loose text-center" dir="rtl" lang="ar">
          {verse.text_imlaei}
        </p>
      </div>

      {/* Tafsir Section */}
      {!edition ? (
        <div className="px-6 py-4">
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600 space-y-2">
            <p dir="ltr" className="text-left">
              No licensed English tafsir is available yet. Switch the app language to Arabic to read the Arabic tafsir.
            </p>
            <p dir="rtl" className="text-right font-arabic">
              لا يتوفر حالياً تفسير مرخّص باللغة الإنجليزية. بدّل لغة التطبيق إلى العربية لقراءة التفاسير العربية.
            </p>
          </div>
        </div>
      ) : (
      <div className="px-6 py-4">
        <button
          onClick={() => setShowTafsir(!showTafsir)}
          className="flex items-center gap-2 text-emerald-700 font-medium mb-3"
          aria-expanded={showTafsir}
        >
          <BookOpen className="w-5 h-5" />
          {t(edition.translationKey)}
          {showTafsir ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {!ar && (
          <p className="text-xs text-gray-500 mb-2" dir="ltr" lang="en">
            No licensed English tafsir is available yet; the Arabic text is shown.
          </p>
        )}

        {showTafsir && (
          <div className="bg-gray-50 rounded-lg p-4">
            {tafsirLoading ? (
              <div className="flex items-center justify-center py-4 text-gray-500">
                <Loader2 className="w-5 h-5 animate-spin me-2" />
                {t('tafseer_loading')}
              </div>
            ) : tafsirData?.text ? (
              <>
                <p
                  className={clsx('text-gray-800 leading-relaxed', tafsirLang === 'ar' && 'font-arabic text-lg')}
                  dir={tafsirLang === 'ar' ? 'rtl' : 'ltr'}
                  lang={tafsirLang}
                >
                  {tafsirData.text}
                </p>
                <TafsirSourceFooter edition={tafsirData.edition} provider={tafsirData.source} language={language} />
              </>
            ) : (
              <p className="text-gray-500 text-center">{t('tafseer_not_found')}</p>
            )}
          </div>
        )}
      </div>
      )}
    </div>
  );
});

// =============================================================================
// Grounded Answer Card — renders RAG output with citations + status + safe-refusal
// =============================================================================

interface GroundedAnswerCardProps {
  response: VerseAskAiResponse;
  language: 'ar' | 'en';
  isRTL: boolean;
  copied: boolean;
  onCopy: (text: string) => void;
  t: (key: string) => string;
  title?: string;
}

const GroundedAnswerCard = memo(function GroundedAnswerCard({
  response,
  language,
  isRTL,
  copied,
  onCopy,
  t,
  title,
}: GroundedAnswerCardProps) {
  const hasCitations = response.citations && response.citations.length > 0;
  const isAiUnavailable = response.status === 'ai_unavailable';
  const isRefusal = !isAiUnavailable && (response.status === 'no_verified_source' || !hasCitations);
  const confidencePct = Math.round((response.confidence ?? 0) * 100);
  const dir = isRTL ? 'rtl' : 'ltr';

  return (
    <div className="space-y-3">
      {/* Status banner */}
      {isAiUnavailable ? (
        <div role="status" className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className={clsx('flex-1', isRTL && 'text-right')} dir={dir}>
            <p className="font-medium">
              {response.error_code === 'ai_quota_exceeded' || response.warnings?.includes('ai_quota_exceeded')
                ? (language === 'ar' ? 'تم بلوغ حدّ خدمة الذكاء الاصطناعي مؤقتاً.' : 'AI usage limit reached for now.')
                : (language === 'ar' ? 'خدمة الذكاء الاصطناعي غير متاحة حالياً.' : 'The AI service is temporarily unavailable.')}
            </p>
            <p className="text-xs mt-1 opacity-80">
              {language === 'ar' ? 'حاول مرة أخرى لاحقاً.' : 'Please try again later.'}
            </p>
          </div>
        </div>
      ) : isRefusal ? (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className={clsx('flex-1', isRTL && 'text-right')} dir={dir}>
            <p className="font-medium">
              {language === 'ar'
                ? 'لا توجد مصادر موثوقة كافية للإجابة على هذا السؤال.'
                : 'No verified sources are available to answer this question.'}
            </p>
            <p className="text-xs mt-1 opacity-80">
              {language === 'ar'
                ? 'جرّب أحد الأسئلة المقترحة أدناه.'
                : 'Try one of the suggested questions below.'}
            </p>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between text-xs">
          <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-1 rounded">
            <Check className="w-3 h-3" />
            {language === 'ar'
              ? `${response.citations.length} مصدر · ثقة ${confidencePct}٪`
              : `${response.citations.length} sources · ${confidencePct}% confidence`}
          </span>
          {response.cached && (
            <span className="text-gray-400">{language === 'ar' ? 'محفوظ' : 'cached'}</span>
          )}
        </div>
      )}

      {/* AI disclaimer (grounded but still AI-assisted) */}
      {response.ai_summary_disclaimer !== false && !isRefusal && !isAiUnavailable && (
        <p className={clsx('text-xs text-gray-500 italic', isRTL && 'text-right')} dir={dir}>
          {t('rag_ai_disclaimer')}
        </p>
      )}

      {/* Optional title (used by Explain tab) */}
      {title && (
        <p
          className={clsx(
            'font-bold text-emerald-700 text-lg',
            isRTL ? 'text-right font-arabic' : '',
          )}
          dir={dir}
        >
          {title}
        </p>
      )}

      {/* Answer body */}
      {response.answer && (
        <div className="bg-gray-50 rounded-lg p-4 relative group border border-gray-200">
          <button
            onClick={() => onCopy(response.answer)}
            className={clsx(
              'absolute top-2 p-1.5 bg-white rounded-lg shadow-sm opacity-0 group-hover:opacity-100 transition-opacity border',
              isRTL ? 'left-2' : 'right-2'
            )}
            title={language === 'ar' ? 'نسخ' : 'Copy'}
          >
            {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4 text-gray-500" />}
          </button>
          <p
            className={clsx(
              'text-gray-800 leading-loose text-lg whitespace-pre-wrap',
              isRTL ? 'font-arabic text-right' : '',
            )}
            dir={dir}
          >
            {response.answer}
          </p>
        </div>
      )}

      {/* Citations */}
      {hasCitations && (
        <div className="space-y-2">
          <p className={clsx('text-xs font-medium text-gray-500 flex items-center gap-1', isRTL && 'flex-row-reverse')}>
            <Quote className="w-3 h-3" />
            {language === 'ar' ? 'المصادر:' : 'Sources:'}
          </p>
          <div className="space-y-2">
            {response.citations.map((c: Citation) => (
              <div
                key={c.chunk_id}
                className="bg-white border border-gray-200 rounded-lg p-3 text-sm"
                dir={dir}
              >
                <div className={clsx('flex items-center justify-between mb-1', isRTL && 'flex-row-reverse')}>
                  <span className={clsx('font-medium text-emerald-700', isRTL && 'font-arabic')}>
                    {language === 'ar' ? c.source_name_ar : c.source_name}
                  </span>
                  <span className="text-xs text-gray-400">{c.verse_reference}</span>
                </div>
                {c.author && (
                  <p className="text-xs text-gray-500">{c.author}</p>
                )}
                {(c.quoted_evidence || c.excerpt) && (
                  <p
                    className={clsx(
                      'text-gray-700 mt-1 line-clamp-3',
                      isRTL && language === 'ar' && 'font-arabic text-right',
                    )}
                    dir={dir}
                  >
                    {c.quoted_evidence || c.excerpt}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggested questions when refused */}
      {isRefusal && response.suggested_questions && response.suggested_questions.length > 0 && (
        <div className="space-y-2 pt-2">
          <p className={clsx('text-xs font-medium text-gray-500', isRTL && 'text-right')}>
            {t('ai_suggested_questions')}
          </p>
          {response.suggested_questions.map((q) => (
            <div
              key={q.id}
              className={clsx('text-sm text-emerald-700 p-2 rounded-lg border border-gray-200 bg-white', isRTL && 'text-right')}
              dir={dir}
            >
              {q.text}
            </div>
          ))}
        </div>
      )}

      {/* Warnings */}
      {response.warnings && response.warnings.length > 0 && (
        <ul className={clsx('text-xs text-amber-700 space-y-1', isRTL && 'text-right')} dir={dir}>
          {response.warnings.slice(0, 3).map((w, i) => (
            <li key={i}>⚠ {w}</li>
          ))}
        </ul>
      )}
    </div>
  );
});

// =============================================================================
// AI Assistant Sidebar
// =============================================================================

interface AIAssistantProps {
  verse: Verse | null;
  /** Retained for backwards compatibility with callers; the grounded
   *  endpoints retrieve their own context from the tafseer corpus. */
  tafsirText?: string;
  language: 'ar' | 'en';
  isOpen: boolean;
  onClose: () => void;
}

const AIAssistant = memo(function AIAssistant({
  verse,
  language,
  isOpen,
  onClose,
}: AIAssistantProps) {
  const { t } = useLanguageStore();
  const [activeTab, setActiveTab] = useState<'summary' | 'explain' | 'qa'>('summary');
  const [selectedWord, setSelectedWord] = useState('');
  const [question, setQuestion] = useState('');
  const [copied, setCopied] = useState(false);

  const summaryMutation = useMutation<VerseAskAiResponse>({
    mutationFn: async () => {
      if (!verse) throw new Error('verse_required');
      const response = await verseAskAiApi.summarize({
        surah: verse.sura_no,
        ayahStart: verse.aya_no,
        language,
      });
      return response.data;
    },
  });

  const explainMutation = useMutation<VerseAskAiResponse, unknown, string>({
    mutationFn: async (word: string) => {
      if (!verse) throw new Error('verse_required');
      const response = await verseAskAiApi.explainWord({
        surah: verse.sura_no,
        ayahStart: verse.aya_no,
        word: word.trim(),
        language,
      });
      return response.data;
    },
  });

  const answerMutation = useMutation<VerseAskAiResponse, unknown, string>({
    mutationFn: async (q: string) => {
      if (!verse) throw new Error('verse_required');
      const response = await verseAskAiApi.ask({
        surah: verse.sura_no,
        ayahStart: verse.aya_no,
        question: q.trim(),
        language,
      });
      return response.data;
    },
  });

  // Suggested questions (live from backend so they can be extended per-verse)
  const { data: suggestedQuestionsData } = useQuery({
    queryKey: ['verse-ask-ai-suggested', verse?.sura_no, verse?.aya_no, language],
    queryFn: async () => {
      if (!verse) return null;
      const r = await verseAskAiApi.suggestedQuestions({
        surah: verse.sura_no,
        ayahStart: verse.aya_no,
        language,
      });
      return r.data;
    },
    enabled: !!verse,
    staleTime: 60 * 60 * 1000,
  });

  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, []);

  const suggestedQuestions = useMemo(() => {
    const fromBackend = suggestedQuestionsData?.questions?.map((q) => q.text);
    if (fromBackend && fromBackend.length > 0) return fromBackend;
    return [
      t('ai_question_revelation'),
      t('ai_question_lessons'),
      t('ai_question_context'),
    ];
  }, [suggestedQuestionsData, t]);

  const isRTL = language === 'ar';

  if (!isOpen) return null;

  return (
    <div
      className={clsx(
        'fixed inset-y-0 w-full sm:w-96 bg-white shadow-2xl z-50 flex flex-col',
        isRTL ? 'left-0 border-r border-gray-200' : 'right-0 border-l border-gray-200'
      )}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-700 to-emerald-600 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          <span className="font-bold text-lg">{t('ai_assistant')}</span>
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-white/20 rounded-lg transition-colors" aria-label={isRTL ? 'إغلاق' : 'Close'}>
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Selected Verse */}
      {verse && (
        <div className="p-4 bg-emerald-50 border-b border-emerald-200">
          <p className="text-sm text-emerald-700 font-semibold mb-2">
            {verse.sura_name_ar} : {verse.aya_no}
          </p>
          <p className="font-mushaf text-gray-800 leading-relaxed text-lg" dir="rtl" lang="ar">
            {verse.text_imlaei}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {[
          { key: 'summary', icon: Lightbulb, labelKey: 'ai_summary' },
          { key: 'explain', icon: BookOpen, labelKey: 'ai_explain' },
          { key: 'qa', icon: HelpCircle, labelKey: 'ai_qa' },
        ].map(({ key, icon: Icon, labelKey }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as typeof activeTab)}
            className={clsx(
              'flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors',
              activeTab === key
                ? 'text-emerald-700 border-b-2 border-emerald-600 bg-emerald-50'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            )}
          >
            <Icon className="w-4 h-4" />
            <span>{t(labelKey)}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!verse ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <BookOpen className="w-16 h-16 mb-4 text-gray-300" />
            <p className="text-lg">{t('ai_select_verse')}</p>
          </div>
        ) : (
          <>
            {/* Summary Tab */}
            {activeTab === 'summary' && (
              <div className="space-y-4">
                <button
                  onClick={() => summaryMutation.mutate()}
                  disabled={summaryMutation.isPending}
                  className="w-full py-3 bg-emerald-600 text-white rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {summaryMutation.isPending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Lightbulb className="w-5 h-5" />
                  )}
                  {t('ai_generate_summary')}
                </button>

                {summaryMutation.data && (
                  <GroundedAnswerCard
                    response={summaryMutation.data}
                    language={language}
                    isRTL={isRTL}
                    copied={copied}
                    onCopy={handleCopy}
                    t={t}
                  />
                )}
              </div>
            )}

            {/* Explain Tab */}
            {activeTab === 'explain' && (
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-700">{t('ai_select_word_hint')}</p>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={selectedWord}
                    onChange={(e) => setSelectedWord(e.target.value)}
                    placeholder={t('ai_enter_word')}
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 font-arabic text-lg"
                    dir="rtl"
                  />
                  <button
                    onClick={() => explainMutation.mutate(selectedWord)}
                    disabled={explainMutation.isPending || !selectedWord.trim()}
                    className="px-4 py-2.5 bg-emerald-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-emerald-700 transition-colors font-medium"
                  >
                    {explainMutation.isPending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      t('ai_explain')
                    )}
                  </button>
                </div>

                {explainMutation.data && (
                  <GroundedAnswerCard
                    response={explainMutation.data}
                    language={language}
                    isRTL={isRTL}
                    copied={copied}
                    onCopy={handleCopy}
                    t={t}
                    title={t('ai_explanation_of').replace('{word}', selectedWord)}
                  />
                )}
              </div>
            )}

            {/* Q&A Tab */}
            {activeTab === 'qa' && (
              <div className="space-y-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !answerMutation.isPending && question.trim() && answerMutation.mutate(question)}
                    placeholder={t('ai_ask_question')}
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    dir={isRTL ? 'rtl' : 'ltr'}
                  />
                  <button
                    onClick={() => answerMutation.mutate(question)}
                    disabled={answerMutation.isPending || !question.trim()}
                    className="px-4 py-2.5 bg-emerald-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-emerald-700 transition-colors"
                  >
                    {answerMutation.isPending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <MessageSquare className="w-5 h-5" />
                    )}
                  </button>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-gray-500 font-medium">{t('ai_suggested_questions')}</p>
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setQuestion(q)}
                      className="block w-full text-sm text-emerald-700 hover:bg-emerald-50 p-3 rounded-lg border border-gray-200 hover:border-emerald-300 transition-colors"
                      dir={isRTL ? 'rtl' : 'ltr'}
                    >
                      {q}
                    </button>
                  ))}
                </div>

                {answerMutation.data && (
                  <GroundedAnswerCard
                    response={answerMutation.data}
                    language={language}
                    isRTL={isRTL}
                    copied={copied}
                    onCopy={handleCopy}
                    t={t}
                  />
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
});

// =============================================================================
// Line-by-line Mushaf renderer (King Fahd Madinah exact layout)
// =============================================================================

// =============================================================================
// Main Mushaf Page Component
// =============================================================================

export function MushafPage() {
  const { language, t } = useLanguageStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const tafsirEditions = TAFSIR_EDITIONS;

  // State
  // Opens at ?page=, else where the reader left off, else page 1.
  const [currentPage, setCurrentPage] = useState(() => {
    const page = searchParams.get('page');
    return page ? parseInt(page, 10) : getReadingProgress().lastRead?.page ?? 1;
  });
  const [selectedVerse, setSelectedVerse] = useState<Verse | null>(null);
  const {
    fontScale, setFontScale, script, reciterId: selectedReciter, setReciterId: setSelectedReciter, theme,
  } = useReaderSettingsStore();
  useEffect(() => applyReaderThemeToDocument(theme), [theme]);
  const fontSize = Math.round(28 * fontScale);
  const [selectedTafsir, setSelectedTafsir] = useState('muyassar');
  const [showSettings, setShowSettings] = useState(false);
  const [showAI, setShowAI] = useState(false);
  const [playingVerseId, setPlayingVerseId] = useState<number | null>(null);
  const [audioError, setAudioError] = useState(false);
  const [currentTafsirText, setCurrentTafsirText] = useState('');
  // Same-verse, same-reciter alternatives for the verse now loaded.
  const audioFallbacksRef = useRef<string[]>([]);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Data Fetching
  const { data: verses = [], isLoading, error, prefetchAdjacent } = usePageVerses(currentPage);

  // Reset the selection when the language changes
  useEffect(() => {
    setSelectedVerse(null);
    setCurrentTafsirText('');
  }, [language]);

  // Prefetch adjacent pages
  useEffect(() => {
    if (verses.length > 0) {
      prefetchAdjacent();
    }
  }, [verses.length, prefetchAdjacent]);

  // Update URL
  useEffect(() => {
    setSearchParams({ page: currentPage.toString() });
  }, [currentPage, setSearchParams]);

  // Remember the page (and its first verse) for "continue reading"
  useEffect(() => {
    const first = verses[0];
    if (!first) return;
    // Every surah on the page is read up to its last verse here (a surah whose
    // last verse is on this page counts as read); the page start is recorded
    // last so "continue reading" reopens this page.
    const lastOnPage = new Map<number, Verse>();
    for (const v of verses) lastOnPage.set(v.sura_no, v);
    for (const v of lastOnPage.values()) {
      recordReadingPosition({
        surah: v.sura_no, aya: v.aya_no, nameAr: v.sura_name_ar, nameEn: v.sura_name_en, page: currentPage,
      });
    }
    recordReadingPosition({
      surah: first.sura_no, aya: first.aya_no,
      nameAr: first.sura_name_ar, nameEn: first.sura_name_en, page: currentPage,
    });
  }, [verses, currentPage]);

  // Navigate pages
  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= TOTAL_PAGES) {
      // The verse being recited is no longer on screen: stop it.
      audioRef.current?.pause();
      setAudioError(false);
      startTransition(() => {
        setCurrentPage(page);
        setSelectedVerse(null);
        setPlayingVerseId(null);
        setCurrentTafsirText('');
      });
    }
  }, []);

  // Play verse audio
  const playVerse = useCallback(async (verse: Verse) => {
    if (playingVerseId === verse.id) {
      audioRef.current?.pause();
      setPlayingVerseId(null);
      return;
    }

    setAudioError(false);
    try {
      const response = await api.get(`/quran/audio/verse/${verse.sura_no}/${verse.aya_no}`, {
        params: { reciter: selectedReciter }
      });
      const primary: string | undefined = response.data.audio_url;
      const audio = audioRef.current;
      if (!audio || !primary) throw new Error('no_audio');
      const alternatives: string[] = [
        ...(response.data.fallback_urls ?? []),
        ...(response.data.fallback_url ? [response.data.fallback_url] : []),
      ];
      audioFallbacksRef.current = alternatives.filter((u, i) => !!u && u !== primary && alternatives.indexOf(u) === i);
      // Prefer the offline copy when this surah was saved for this reciter.
      audio.src = await playableUrl(selectedReciter, verse.sura_no, primary);
      setPlayingVerseId(verse.id);
      await audio.play().catch(() => undefined);
    } catch {
      setPlayingVerseId(null);
      setAudioError(true);
    }
  }, [playingVerseId, selectedReciter]);

  // A source failed: try this verse's next alternative, else say so.
  const handleAudioError = useCallback(() => {
    const audio = audioRef.current;
    if (!audio || !audio.getAttribute('src')) return;
    const next = audioFallbacksRef.current.shift();
    if (next) {
      audio.src = next;
      audio.play().catch(() => undefined);
      return;
    }
    setPlayingVerseId(null);
    setAudioError(true);
  }, []);

  // Handle verse click
  const handleVerseClick = useCallback((verse: Verse) => {
    setSelectedVerse(prev => prev?.id === verse.id ? null : verse);
  }, []);

  // Open AI Assistant
  const handleOpenAI = useCallback(() => {
    setShowAI(true);
  }, []);

  // Get selected edition
  const selectedEdition = useMemo(
    () => tafsirEditions.find(e => e.id === selectedTafsir) || tafsirEditions[0],
    [selectedTafsir, tafsirEditions]
  );

  // Build typed page items: surah headers + verses
  const pageItems = useMemo((): PageItem[] => {
    const items: PageItem[] = [];

    let lastSuraNo = 0;

    for (const verse of verses) {
      // Insert surah header when a new surah's first ayah appears on this page
      if (verse.sura_no !== lastSuraNo && verse.aya_no === 1) {
        // Opening Bismillah comes with verse 1, separately from its text
        const bismillahText = bismillahFor(verse, script);

        items.push({
          type: 'header',
          suraNo: verse.sura_no,
          suraNameAr: verse.sura_name_ar,   // "سورة <name>" from the API
          suraNameEn: verse.sura_name_en,
          ayahCount: surahVerseCount(verse.sura_no),
          bismillahText,
          revelationType: SURAH_REVELATION[verse.sura_no] ?? 'unknown',
        });
        lastSuraNo = verse.sura_no;
      }

      const displayText = verseTextFor(verse, script);

      items.push({ type: 'verse', verse, displayText });
    }

    return items;
  }, [verses, script]);

  // Current surah info
  const currentSura = useMemo(() => verses.length > 0 ? verses[0] : null, [verses]);

  return (
    <div
      className="mushaf-root reader-surface min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50"
      data-theme={theme}
    >
      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        onEnded={() => setPlayingVerseId(null)}
        onError={handleAudioError}
      />

      {/* Navigation Bar */}
      <nav
        className="sticky top-[var(--app-header-h,0px)] z-40 bg-gradient-to-r from-emerald-800 to-emerald-700 text-white shadow-lg"
        aria-label={language === 'ar' ? 'التنقل في المصحف' : 'Mushaf navigation'}
      >
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between flex-wrap gap-2">
          {/* Page Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage >= TOTAL_PAGES || isPending}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-40 transition-colors"
              title={t('mushaf_next_page')}
              aria-label={t('mushaf_next_page')}
            >
              <ChevronRight className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-1 px-3 py-1 bg-white/10 rounded-lg">
              <input
                type="number"
                aria-label={language === 'ar' ? 'رقم الصفحة' : 'Page number'}
                value={currentPage}
                onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
                min={1}
                max={TOTAL_PAGES}
                className="w-14 bg-transparent text-center font-bold outline-none"
              />
              <span className="text-white/70">/ {TOTAL_PAGES}</span>
            </div>

            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage <= 1 || isPending}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-40 transition-colors"
              title={t('mushaf_prev_page')}
              aria-label={t('mushaf_prev_page')}
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>

          {/* Sura Title */}
          <div className="text-center">
            {currentSura && (
              <h1 className={clsx('text-xl font-bold', language === 'ar' && 'font-arabic')}>
                {language === 'ar' ? currentSura.sura_name_ar : currentSura.sura_name_en}
              </h1>
            )}
          </div>

          {/* Surah Jump Selector */}
          <div className="flex items-center gap-1.5">
            <label htmlFor="mushaf-surah" className="text-white/70 text-xs hidden sm:block">
              {language === 'ar' ? 'سورة' : 'Surah'}
            </label>
            <select
              id="mushaf-surah"
              value={surahOnPage(currentPage)}
              onChange={(e) => goToPage(firstPageOfSurah(parseInt(e.target.value, 10)))}
              className="max-w-[9rem] px-2 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm border border-white/20 outline-none cursor-pointer"
              aria-label={language === 'ar' ? 'انتقل إلى السورة' : 'Jump to surah'}
            >
              {SURAH_NAMES.map((s, i) => (
                <option key={i + 1} value={i + 1} className="bg-emerald-800">
                  {i + 1}. {language === 'ar' ? s.ar : s.en}
                </option>
              ))}
            </select>
          </div>

          {/* Juz Jump Selector */}
          <div className="flex items-center gap-1.5">
            <label htmlFor="mushaf-juz" className="text-white/70 text-xs hidden sm:block">
              {language === 'ar' ? 'جزء' : 'Juz'}
            </label>
            <select
              id="mushaf-juz"
              aria-label={language === 'ar' ? 'انتقل إلى الجزء' : 'Jump to Juz'}
              value={verses[0]?.juz_no ?? 1}
              onChange={(e) => goToPage(firstPageOfJuz(parseInt(e.target.value, 10)))}
              className="px-2 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm border border-white/20 outline-none cursor-pointer"
              title={language === 'ar' ? 'انتقل إلى الجزء' : 'Jump to Juz'}
            >
              {Array.from({ length: 30 }, (_, i) => i + 1).map(j => (
                <option key={j} value={j} className="bg-emerald-800">
                  {language === 'ar' ? `الجزء ${toArabicNumber(j)}` : `Juz ${j}`}
                </option>
              ))}
            </select>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFontScale(fontScale - 0.1)}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              title={t('mushaf_zoom_out')}
              aria-label={t('mushaf_zoom_out')}
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            <span className="text-sm min-w-[2rem] text-center">{fontSize}</span>
            <button
              onClick={() => setFontScale(fontScale + 0.1)}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              title={t('mushaf_zoom_in')}
              aria-label={t('mushaf_zoom_in')}
            >
              <ZoomIn className="w-5 h-5" />
            </button>

            <div className="w-px h-6 bg-white/30 mx-1" />

            <button
              onClick={() => setShowAI(!showAI)}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                showAI ? 'bg-purple-500' : 'bg-white/10 hover:bg-white/20'
              )}
              title={t('ai_assistant')}
              aria-label={t('ai_assistant')}
              aria-pressed={showAI}
            >
              <Sparkles className="w-5 h-5" />
            </button>

            <button
              onClick={() => setShowSettings(!showSettings)}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                showSettings ? 'bg-amber-500' : 'bg-white/10 hover:bg-white/20'
              )}
              title={t('mushaf_settings')}
              aria-label={t('mushaf_settings')}
              aria-expanded={showSettings}
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="bg-emerald-700/50 px-4 py-3 flex flex-wrap gap-4">
            {tafsirEditions.length > 0 && (
            <div className="flex items-center gap-2">
              <label htmlFor="mushaf-tafsir" className={clsx('text-sm text-white/80', language === 'ar' && 'font-arabic')}>{t('mushaf_tafsir')}:</label>
              <select
                id="mushaf-tafsir"
                value={selectedTafsir}
                onChange={(e) => setSelectedTafsir(e.target.value)}
                className="px-3 py-1.5 rounded bg-white/15 text-white text-sm border border-white/20"
              >
                {tafsirEditions.map(ed => (
                  <option key={ed.id} value={ed.id} className="bg-emerald-800">
                    {t(ed.translationKey)}
                  </option>
                ))}
              </select>
            </div>
            )}

            <div className="flex items-center gap-2">
              <label htmlFor="mushaf-reciter" className={clsx('text-sm text-white/80', language === 'ar' && 'font-arabic')}>{t('mushaf_reciter')}:</label>
              <select
                id="mushaf-reciter"
                value={selectedReciter}
                onChange={(e) => setSelectedReciter(e.target.value)}
                className="px-3 py-1.5 rounded bg-white/15 text-white text-sm border border-white/20"
              >
                {RECITERS.map(r => (
                  <option key={r.id} value={r.id} className="bg-emerald-800">
                    {t(r.translationKey)}
                  </option>
                ))}
              </select>
            </div>

            <ReaderThemePicker language={language} compact />
          </div>
        )}
      </nav>

      {/* Qur'an text attribution (Tanzil licence) */}
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-1.5 flex items-center justify-center gap-2 text-amber-800 text-xs">
        <BookOpen className="w-3.5 h-3.5 flex-shrink-0" />
        <QuranTextAttribution language={language} className="!text-amber-800 !text-xs" />
      </div>

      {/* Main Content */}
      <div className={clsx(
        'transition-all duration-300 pb-16',
        showAI && language === 'ar' ? 'sm:ml-96' : '',
        showAI && language === 'en' ? 'sm:mr-96' : '',
        selectedVerse ? 'pb-72' : ''
      )}>
        <div className="max-w-4xl mx-auto px-4 py-6">
          {/* Mushaf Frame */}
          <div className="mushaf-border rounded-xl overflow-hidden">
            {/* Ornamental Header */}
            <div className="bg-gradient-to-r from-amber-100 via-amber-50 to-amber-100 px-6 py-4 border-b-2 border-amber-400 flex justify-between items-center">
              <div className="text-center">
                <span className="font-mushaf text-amber-800 text-lg font-semibold">
                  {t('mushaf_juz')} {toArabicNumber(verses[0]?.juz_no || 1)}
                </span>
              </div>
              <div className="text-center">
                <span className="font-mushaf text-2xl text-amber-700">۞</span>
              </div>
              <div className="text-center">
                <span className="font-mushaf text-amber-800 text-lg font-semibold">
                  {toArabicNumber(currentPage)}
                </span>
              </div>
            </div>

            {/* Mushaf Page Content - Flowing Text */}
            <div className="p-8 min-h-[70vh] mushaf-page">
              {isLoading || isPending ? (
                <div className="flex flex-col items-center justify-center h-96 text-amber-700">
                  <Loader2 className="w-10 h-10 animate-spin mb-4" />
                  <span className="text-lg">{t('tafseer_loading')}</span>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center h-96 text-red-600">
                  <span className="text-lg mb-4">{t('mushaf_load_failed')}</span>
                  <button
                    onClick={() => goToPage(currentPage)}
                    className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                  >
                    {t('mushaf_retry')}
                  </button>
                </div>
              ) : (
                // ── KSU-style flowing text — all verses of the page as one paragraph ──
                <div className="ksu-quran-page" dir="rtl" lang="ar">
                  {pageItems.map((item) => {
                    if (item.type === 'header') {
                      return (
                        <SurahHeader
                          key={`header-${item.suraNo}`}
                          {...item}
                        />
                      );
                    }

                    const { verse, displayText } = item;
                    const isSelected = selectedVerse?.id === verse.id;
                    const isPlaying = playingVerseId === verse.id;

                    return (
                      <span
                        key={verse.id}
                        onClick={() => handleVerseClick(verse)}
                        className={clsx(
                          'ksu-verse',
                          isSelected && 'ksu-verse--selected',
                          isPlaying  && 'ksu-verse--playing',
                        )}
                      >
                        <span
                          className={clsx('ksu-verse-text', script === 'uthmani' && 'ksu-uthmani')}
                          style={{ fontSize: `${fontSize}px` }}
                        >
                          {displayText}
                        </span>
                        <span
                          className="ksu-aya-marker"
                          style={{ fontSize: `${fontSize * 0.78}px` }}
                        >
                          <span className="ksu-aya-num">{toArabicNumber(verse.aya_no)}</span>
                        </span>
                      </span>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Ornamental Footer */}
            <div className="bg-gradient-to-r from-amber-100 via-amber-50 to-amber-100 px-6 py-4 border-t-2 border-amber-400">
              <div className="flex justify-between items-center">
                <span className="font-mushaf text-amber-800 text-sm">
                  {verses.length > 0 && `${t('mushaf_verses')} ${toArabicNumber(verses[0].aya_no)} - ${toArabicNumber(verses[verses.length - 1].aya_no)}`}
                </span>
                <span className="font-mushaf text-amber-900 text-lg font-semibold">
                  {verses.length > 0 && (language === 'ar' ? verses[0].sura_name_ar : verses[0].sura_name_en)}
                </span>
                <span className="font-mushaf text-amber-800 text-sm">
                  ﴿ {verses.length} {language === 'ar' ? 'آيات' : 'verses'} ﴾
                </span>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <p className={clsx('text-center text-sm text-gray-500 mt-4', language === 'ar' && 'font-arabic')}>
            {t('mushaf_click_verse_hint') || 'Click on any verse to view tafseer and listen to recitation'}
          </p>
        </div>
      </div>

      {/* Selected Verse Panel */}
      {selectedVerse && (
        <VersePanel
          verse={selectedVerse}
          edition={selectedEdition}
          language={language}
          isPlaying={playingVerseId === selectedVerse.id}
          audioError={audioError}
          onPlayAudio={() => playVerse(selectedVerse)}
          onOpenAI={handleOpenAI}
          onClose={() => setSelectedVerse(null)}
        />
      )}

      {/* AI Assistant Sidebar */}
      <AIAssistant
        verse={selectedVerse}
        tafsirText={currentTafsirText}
        language={language}
        isOpen={showAI}
        onClose={() => setShowAI(false)}
      />
    </div>
  );
}

export default MushafPage;
