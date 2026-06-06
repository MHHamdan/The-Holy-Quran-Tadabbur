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
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi, Verse, api, verseAskAiApi } from '../lib/api';
import type { VerseAskAiResponse, Citation } from '../lib/api';
import { queryKeys, staleTimes } from '../lib/queryClient';

// =============================================================================
// Types & Interfaces
// =============================================================================

interface TafsirEdition {
  id: string;
  translationKey: string;
  has_audio: boolean;
  quran_com_id?: number;
}

interface TafsirData {
  text: string;
  audio_url?: string;
  source: string;
}

interface ReciterOption {
  id: string;
  translationKey: string;
}

// =============================================================================
// Constants
// =============================================================================

const TOTAL_PAGES = 604;

const ARABIC_TAFSIR_EDITIONS: TafsirEdition[] = [
  { id: 'muyassar', translationKey: 'tafseer_muyassar', has_audio: true },
  { id: 'ibn_kathir', translationKey: 'tafseer_ibn_kathir', has_audio: false },
  { id: 'tabari', translationKey: 'tafseer_tabari', has_audio: false },
  { id: 'qurtubi', translationKey: 'tafseer_qurtubi', has_audio: false },
  { id: 'jalalayn', translationKey: 'tafseer_jalalayn', has_audio: false },
  { id: 'saadi', translationKey: 'tafseer_saadi', has_audio: false },
  { id: 'baghawi', translationKey: 'tafseer_baghawi', has_audio: false },
];

const ENGLISH_TAFSIR_EDITIONS: TafsirEdition[] = [
  { id: 'en_ibn_kathir', translationKey: 'tafseer_ibn_kathir_en', has_audio: false, quran_com_id: 169 },
  { id: 'en_maarif', translationKey: 'tafseer_maarif', has_audio: false, quran_com_id: 168 },
  { id: 'en_tazkirul', translationKey: 'tafseer_tazkirul', has_audio: false, quran_com_id: 817 },
];

const RECITERS: ReciterOption[] = [
  { id: 'mishary_afasy', translationKey: 'reciter_mishary' },
  { id: 'abdul_basit', translationKey: 'reciter_abdul_basit' },
  { id: 'husary', translationKey: 'reciter_husary' },
  { id: 'maher_muaiqly', translationKey: 'reciter_maher' },
  { id: 'saud_shuraim', translationKey: 'reciter_shuraim' },
];

const ARABIC_NUMS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];

// Surah 1: ayah 1:1 IS the Bismillah itself — no separate Bismillah header
// Surah 9: has no Bismillah at all
const SURAHS_WITHOUT_BISMILLAH_HEADER = new Set([1, 9]);

// Curated Makki/Madani classification — scholarly consensus (Al-Suyuti).
// This is structural UI metadata, not Quran text.
const REVELATION_TYPE: Record<number, 'makki' | 'madani' | 'unknown'> = {
  1:'makki',2:'madani',3:'madani',4:'madani',5:'madani',6:'makki',7:'makki',
  8:'madani',9:'madani',10:'makki',11:'makki',12:'makki',13:'unknown',14:'makki',
  15:'makki',16:'makki',17:'makki',18:'makki',19:'makki',20:'makki',21:'makki',
  22:'unknown',23:'makki',24:'madani',25:'makki',26:'makki',27:'makki',28:'makki',
  29:'unknown',30:'makki',31:'makki',32:'makki',33:'madani',34:'makki',35:'makki',
  36:'makki',37:'makki',38:'makki',39:'makki',40:'makki',41:'makki',42:'makki',
  43:'makki',44:'makki',45:'makki',46:'makki',47:'madani',48:'madani',49:'madani',
  50:'makki',51:'makki',52:'makki',53:'makki',54:'makki',55:'unknown',56:'makki',
  57:'madani',58:'madani',59:'madani',60:'madani',61:'madani',62:'madani',63:'madani',
  64:'madani',65:'madani',66:'madani',67:'makki',68:'makki',69:'makki',70:'makki',
  71:'makki',72:'makki',73:'makki',74:'makki',75:'makki',76:'unknown',77:'makki',
  78:'makki',79:'makki',80:'makki',81:'makki',82:'makki',83:'makki',84:'makki',
  85:'makki',86:'makki',87:'makki',88:'makki',89:'makki',90:'makki',91:'makki',
  92:'makki',93:'makki',94:'makki',95:'makki',96:'makki',97:'unknown',98:'madani',
  99:'unknown',100:'makki',101:'makki',102:'makki',103:'makki',104:'makki',105:'makki',
  106:'makki',107:'makki',108:'makki',109:'makki',110:'madani',111:'makki',112:'makki',
  113:'makki',114:'makki',
};

// =============================================================================
// Typed page items — surah header OR verse
// =============================================================================

interface SurahHeaderItem {
  type: 'header';
  suraNo: number;
  suraNameAr: string;   // from quran_uthmani.json — already has سُورَةُ prefix
  suraNameEn: string;
  ayahCount: number;
  bismillahText: string | null; // extracted from text_uthmani — never hardcoded
  revelationType: 'makki' | 'madani' | 'unknown';
}

interface VerseItem {
  type: 'verse';
  verse: Verse;
  displayText: string;  // text_uthmani with Bismillah prefix stripped for ayah 1
}

type PageItem = SurahHeaderItem | VerseItem;

// =============================================================================
// Utility Functions
// =============================================================================

function toArabicNumber(num: number): string {
  return num.toString().split('').map(d => ARABIC_NUMS[parseInt(d)]).join('');
}

/**
 * Splits the Bismillah prefix from text_uthmani.
 * quran_uthmani.json stores Bismillah concatenated at the start of ayah 1
 * for surahs 2–114 (except surah 9 which has none).
 * Uses the Alef Wasla form ٱ (U+0671) in ٱلرَّحِيمِ as the split marker.
 * All text comes from the verified data file — nothing is hardcoded.
 */
function splitBismillah(text: string): { bismillah: string; verseText: string } | null {
  // The Bismillah ends with ٱلرَّحِيمِ — find the last occurrence of ٱ (U+0671)
  // followed by ل to locate the start of ٱلرَّحِيمِ
  const ALEF_WASLA = 'ٱ'; // ٱ — Alef Wasla, distinctive to Uthmani script
  const MIM = 'م';        // م — final character base of ٱلرَّحِيمِ

  // Walk forward to find the Bismillah boundary: last kasra after the last م in الرحيم
  // Simpler: find second occurrence of ٱل (there are two: ٱللَّهِ and ٱلرَّحْمَٰنِ and ٱلرَّحِيمِ)
  // Most reliable: find the index right after the third ٱ
  const indices: number[] = [];
  for (let i = 0; i < text.length; i++) {
    if (text[i] === ALEF_WASLA) indices.push(i);
  }
  // Expect 3 Alef Wasla chars: ٱللَّهِ, ٱلرَّحْمَٰنِ, ٱلرَّحِيمِ
  // The Bismillah ends after the last م + its diacritics
  if (indices.length < 3) return null;

  // After the 3rd ٱ (start of ٱلرَّحِيمِ), scan forward to find end of that word
  let pos = indices[2];
  // Advance past ل ر ّ ح ِ ي م ِ — stop when we hit a space or a non-diacritic Arabic letter
  // that is NOT part of الرحيم
  pos++; // skip ٱ itself
  // Find the next letter after the diacritics cluster following the 3rd ٱل... word
  // Easiest: find first space or BMP Arabic letter that breaks the Bismillah word
  while (pos < text.length) {
    const c = text[pos];
    if (c === MIM) {
      // Consume م and following diacritics (kasra etc.)
      pos++;
      while (pos < text.length && text.codePointAt(pos)! >= 0x064B && text.codePointAt(pos)! <= 0x065F) {
        pos++;
      }
      break;
    }
    pos++;
  }

  const bismillah = text.slice(0, pos).trim();
  const verseText = text.slice(pos).trimStart();
  if (!verseText) return null; // guard: shouldn't happen for real verse content
  return { bismillah, verseText };
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
  quranComId?: number
) {
  return useQuery({
    queryKey: queryKeys.tafsir.verse(suraNo, ayaNo, edition),
    queryFn: async (): Promise<TafsirData> => {
      if (quranComId) {
        const response = await api.get(`/tafseer/quran-com/verse/${suraNo}/${ayaNo}`, {
          params: { tafsir_id: quranComId }
        });
        return {
          text: response.data.text || '',
          source: response.data.source || '',
        };
      }
      const response = await api.get(`/tafseer/external/verse/${suraNo}/${ayaNo}`, {
        params: { edition }
      });
      return {
        text: response.data.text || '',
        audio_url: response.data.audio_url,
        source: response.data.source || '',
      };
    },
    staleTime: staleTimes.tafsir,
    enabled: enabled && suraNo > 0 && ayaNo > 0,
  });
}

// =============================================================================
// Surah Header Component (for when a new surah starts on the page)
// =============================================================================

const SurahHeader = memo(function SurahHeader({
  suraNameAr, suraNameEn, ayahCount, bismillahText, revelationType,
}: SurahHeaderItem) {
  const typeLabel = revelationType === 'makki' ? 'مكية' : revelationType === 'madani' ? 'مدنية' : 'غير محدد';
  const typeColor = revelationType === 'makki'
    ? 'text-amber-700' : revelationType === 'madani' ? 'text-emerald-700' : 'text-gray-500';

  return (
    <div className="my-8 text-center select-none" dir="rtl">
      {/* Ornamental surah name banner — suraNameAr already has سُورَةُ prefix from quran_uthmani.json */}
      <div className="inline-flex flex-col items-center bg-gradient-to-r from-amber-200 via-amber-50 to-amber-200 border-y-2 border-amber-500 px-10 py-3 w-full max-w-lg">
        <div className="font-mushaf text-2xl text-amber-900 font-bold tracking-wide">
          {suraNameAr}
        </div>
        <div className="flex items-center gap-3 mt-1 text-xs">
          <span className={typeColor}>{typeLabel}</span>
          <span className="text-amber-400">•</span>
          <span className="text-amber-700" dir="ltr">{suraNameEn}</span>
          <span className="text-amber-400">•</span>
          <span className="text-amber-700">{toArabicNumber(ayahCount)} آية</span>
        </div>
      </div>

      {/* Bismillah — text extracted from verified text_uthmani, NEVER hardcoded.
          Only shown for surahs 2–114 except At-Tawba (9). */}
      {bismillahText && (
        <div className="mt-5 mb-1 font-mushaf text-2xl text-gray-800 leading-loose">
          {bismillahText}
        </div>
      )}
    </div>
  );
});

// =============================================================================
// Verse Panel Component (shows when a verse is selected)
// =============================================================================

interface VersePanelProps {
  verse: Verse;
  edition: TafsirEdition;
  language: 'ar' | 'en';
  isPlaying: boolean;
  onPlayAudio: () => void;
  onOpenAI: () => void;
  onClose: () => void;
}

const VersePanel = memo(function VersePanel({
  verse,
  edition,
  language,
  isPlaying,
  onPlayAudio,
  onOpenAI,
  onClose,
}: VersePanelProps) {
  const { t } = useLanguageStore();
  const [showTafsir, setShowTafsir] = useState(true);

  const { data: tafsirData, isLoading: tafsirLoading } = useTafsir(
    verse.sura_no,
    verse.aya_no,
    edition.id,
    showTafsir,
    edition.quran_com_id
  );

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-amber-400 shadow-2xl z-50 max-h-[50vh] overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-gradient-to-r from-emerald-700 to-emerald-600 text-white px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-mushaf text-lg">
            {verse.sura_name_ar} : {toArabicNumber(verse.aya_no)}
          </span>
          <span className="text-sm text-white/70">
            ({verse.sura_name_en} {verse.sura_no}:{verse.aya_no})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onPlayAudio}
            className={clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
              isPlaying ? 'bg-red-500 hover:bg-red-600' : 'bg-white/20 hover:bg-white/30'
            )}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? t('mushaf_pause') : t('mushaf_listen')}
          </button>
          <button
            onClick={onOpenAI}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium bg-purple-500 hover:bg-purple-600 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            {t('ai_assistant')}
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/20 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Selected Verse Text */}
      <div className="px-6 py-4 bg-amber-50 border-b border-amber-200">
        <p className="font-mushaf text-xl text-gray-900 leading-loose text-center" dir="rtl">
          {verse.text_uthmani}
        </p>
      </div>

      {/* Tafsir Section */}
      <div className="px-6 py-4">
        <button
          onClick={() => setShowTafsir(!showTafsir)}
          className="flex items-center gap-2 text-emerald-700 font-medium mb-3"
        >
          <BookOpen className="w-5 h-5" />
          {t(edition.translationKey)}
          {showTafsir ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showTafsir && (
          <div className="bg-gray-50 rounded-lg p-4">
            {tafsirLoading ? (
              <div className="flex items-center justify-center py-4 text-gray-500">
                <Loader2 className="w-5 h-5 animate-spin me-2" />
                {t('tafseer_loading')}
              </div>
            ) : tafsirData?.text ? (
              <p
                className={clsx(
                  'text-gray-800 leading-relaxed',
                  language === 'ar' ? 'font-arabic text-lg' : ''
                )}
                dir={language === 'ar' ? 'rtl' : 'ltr'}
              >
                {tafsirData.text}
              </p>
            ) : (
              <p className="text-gray-500 text-center">{t('tafseer_not_found')}</p>
            )}
          </div>
        )}
      </div>
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
  const isRefusal = response.status === 'no_verified_source' || !hasCitations;
  const confidencePct = Math.round((response.confidence ?? 0) * 100);
  const dir = isRTL ? 'rtl' : 'ltr';

  return (
    <div className="space-y-3">
      {/* Status banner */}
      {isRefusal ? (
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
      {response.ai_summary_disclaimer !== false && !isRefusal && (
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
        'fixed inset-y-0 w-96 bg-white shadow-2xl z-50 flex flex-col',
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
        <button onClick={onClose} className="p-1.5 hover:bg-white/20 rounded-lg transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Selected Verse */}
      {verse && (
        <div className="p-4 bg-emerald-50 border-b border-emerald-200">
          <p className="text-sm text-emerald-700 font-semibold mb-2">
            {verse.sura_name_ar} : {verse.aya_no}
          </p>
          <p className="font-mushaf text-gray-800 leading-relaxed text-lg" dir="rtl">
            {verse.text_uthmani}
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
// Main Mushaf Page Component
// =============================================================================

export function MushafPage() {
  const { language, t } = useLanguageStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isPending, startTransition] = useTransition();

  // Get tafsir editions based on language
  const tafsirEditions = useMemo(
    () => language === 'ar' ? ARABIC_TAFSIR_EDITIONS : ENGLISH_TAFSIR_EDITIONS,
    [language]
  );

  // State
  const [currentPage, setCurrentPage] = useState(() => {
    const page = searchParams.get('page');
    return page ? parseInt(page, 10) : 1;
  });
  const [selectedVerse, setSelectedVerse] = useState<Verse | null>(null);
  const [fontSize, setFontSize] = useState(28);
  const [selectedTafsir, setSelectedTafsir] = useState(() =>
    language === 'ar' ? 'muyassar' : 'en_ibn_kathir'
  );
  const [selectedReciter, setSelectedReciter] = useState('mishary_afasy');
  const [showSettings, setShowSettings] = useState(false);
  const [showAI, setShowAI] = useState(false);
  const [playingVerseId, setPlayingVerseId] = useState<number | null>(null);
  const [currentTafsirText, setCurrentTafsirText] = useState('');

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Data Fetching
  const { data: verses = [], isLoading, error, prefetchAdjacent } = usePageVerses(currentPage);

  // Reset tafsir when language changes
  useEffect(() => {
    setSelectedTafsir(language === 'ar' ? 'muyassar' : 'en_ibn_kathir');
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

  // Navigate pages
  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= TOTAL_PAGES) {
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

    try {
      const response = await api.get(`/quran/audio/verse/${verse.sura_no}/${verse.aya_no}`, {
        params: { reciter: selectedReciter }
      });
      if (audioRef.current && response.data.audio_url) {
        audioRef.current.src = response.data.audio_url;
        audioRef.current.play().catch(console.error);
        setPlayingVerseId(verse.id);
      }
    } catch (err) {
      console.error('Failed to play audio:', err);
    }
  }, [playingVerseId, selectedReciter]);

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
    // Count ayahs per surah from the current page's verse list
    const ayahCounts: Record<number, number> = {};
    for (const v of verses) {
      ayahCounts[v.sura_no] = Math.max(ayahCounts[v.sura_no] ?? 0, v.aya_no);
    }

    let lastSuraNo = 0;

    for (const verse of verses) {
      // Insert surah header when a new surah's first ayah appears on this page
      if (verse.sura_no !== lastSuraNo && verse.aya_no === 1) {
        const needsBismillah = !SURAHS_WITHOUT_BISMILLAH_HEADER.has(verse.sura_no);
        let bismillahText: string | null = null;

        if (needsBismillah) {
          // Extract Bismillah from the verified text_uthmani — never hardcoded
          const split = splitBismillah(verse.text_uthmani);
          bismillahText = split?.bismillah ?? null;
        }

        items.push({
          type: 'header',
          suraNo: verse.sura_no,
          suraNameAr: verse.sura_name_ar,   // already has سُورَةُ prefix from quran_uthmani.json
          suraNameEn: verse.sura_name_en,
          ayahCount: ayahCounts[verse.sura_no] ?? verse.aya_no,
          bismillahText,
          revelationType: REVELATION_TYPE[verse.sura_no] ?? 'unknown',
        });
        lastSuraNo = verse.sura_no;
      }

      // Ayah 1 of surahs that have a Bismillah header: strip it from the flowing text
      const shouldStrip = verse.aya_no === 1 && !SURAHS_WITHOUT_BISMILLAH_HEADER.has(verse.sura_no);
      let displayText = verse.text_uthmani.replace(/^﻿/, ''); // strip BOM (only 1:1 has it)
      if (shouldStrip) {
        const split = splitBismillah(verse.text_uthmani);
        if (split) displayText = split.verseText;
      }

      items.push({ type: 'verse', verse, displayText });
    }

    return items;
  }, [verses]);

  // Current surah info
  const currentSura = useMemo(() => verses.length > 0 ? verses[0] : null, [verses]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50">
      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        onEnded={() => setPlayingVerseId(null)}
        onError={() => setPlayingVerseId(null)}
      />

      {/* Navigation Bar */}
      <nav className="sticky top-0 z-40 bg-gradient-to-r from-emerald-800 to-emerald-700 text-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between flex-wrap gap-2">
          {/* Page Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage >= TOTAL_PAGES || isPending}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-40 transition-colors"
              title={t('mushaf_next_page')}
            >
              <ChevronRight className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-1 px-3 py-1 bg-white/10 rounded-lg">
              <input
                type="number"
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

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFontSize(prev => Math.max(20, prev - 2))}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              title={t('mushaf_zoom_out')}
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            <span className="text-sm min-w-[2rem] text-center">{fontSize}</span>
            <button
              onClick={() => setFontSize(prev => Math.min(48, prev + 2))}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              title={t('mushaf_zoom_in')}
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
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="bg-emerald-700/50 px-4 py-3 flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <label className={clsx('text-sm text-white/80', language === 'ar' && 'font-arabic')}>{t('mushaf_tafsir')}:</label>
              <select
                value={selectedTafsir}
                onChange={(e) => setSelectedTafsir(e.target.value)}
                className="px-3 py-1.5 rounded bg-white/15 text-white text-sm border border-white/20"
              >
                {tafsirEditions.map(ed => (
                  <option key={ed.id} value={ed.id} className="bg-emerald-800">
                    {t(ed.translationKey)} {ed.has_audio ? '🔊' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className={clsx('text-sm text-white/80', language === 'ar' && 'font-arabic')}>{t('mushaf_reciter')}:</label>
              <select
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
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className={clsx(
        'transition-all duration-300 pb-16',
        showAI && language === 'ar' ? 'ml-96' : '',
        showAI && language === 'en' ? 'mr-96' : '',
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
                <div className="text-center" dir="rtl">
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
                          'cursor-pointer transition-all duration-200 inline',
                          isSelected && 'bg-amber-200 rounded px-1',
                          isPlaying && 'bg-emerald-200 rounded px-1',
                          !isSelected && !isPlaying && 'hover:bg-amber-100 rounded'
                        )}
                      >
                        <span
                          className="font-mushaf"
                          style={{
                            fontSize: `${fontSize}px`,
                            lineHeight: 2.2,
                            letterSpacing: '0.01em',
                          }}
                        >
                          {displayText}
                        </span>
                        <span
                          className="inline-flex items-center justify-center mx-1 text-amber-700 font-mushaf"
                          style={{ fontSize: `${fontSize * 0.7}px` }}
                        >
                          ﴿{toArabicNumber(verse.aya_no)}﴾
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
      </main>

      {/* Selected Verse Panel */}
      {selectedVerse && (
        <VersePanel
          verse={selectedVerse}
          edition={selectedEdition}
          language={language}
          isPlaying={playingVerseId === selectedVerse.id}
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
