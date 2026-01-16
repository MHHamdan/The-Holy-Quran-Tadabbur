/**
 * Optimized Mushaf Page - المصحف الشريف
 *
 * FAANG-level Performance Optimizations:
 * 1. React Query for data fetching and caching
 * 2. React.memo for component memoization
 * 3. useCallback/useMemo for function stability
 * 4. useTransition for non-blocking UI updates
 * 5. Virtualization-ready architecture
 * 6. Prefetching for smooth navigation
 * 7. Full i18n support with translation keys
 */

import { useState, useCallback, useRef, memo, useTransition, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Loader2,
  ZoomIn,
  ZoomOut,
  Play,
  Pause,
  Settings,
  Volume2,
  Sparkles,
  MessageSquare,
  Lightbulb,
  HelpCircle,
  X,
  Copy,
  Check,
  RefreshCw,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi, Verse, api } from '../lib/api';
import { queryKeys, staleTimes } from '../lib/queryClient';

// =============================================================================
// Types & Interfaces
// =============================================================================

interface TafsirEdition {
  id: string;
  translationKey: string;
  has_audio: boolean;
  quran_com_id?: number; // For English tafsirs from Quran.com API
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
// Constants (Moved outside component to prevent recreation)
// =============================================================================

const TOTAL_PAGES = 604;

// Arabic tafsir editions
const ARABIC_TAFSIR_EDITIONS: TafsirEdition[] = [
  { id: 'muyassar', translationKey: 'tafseer_muyassar', has_audio: true },
  { id: 'ibn_kathir', translationKey: 'tafseer_ibn_kathir', has_audio: false },
  { id: 'tabari', translationKey: 'tafseer_tabari', has_audio: false },
  { id: 'qurtubi', translationKey: 'tafseer_qurtubi', has_audio: false },
  { id: 'jalalayn', translationKey: 'tafseer_jalalayn', has_audio: false },
  { id: 'saadi', translationKey: 'tafseer_saadi', has_audio: false },
  { id: 'baghawi', translationKey: 'tafseer_baghawi', has_audio: false },
];

// English tafsir editions (from Quran.com API v4)
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

// =============================================================================
// Utility Functions (Pure functions outside component)
// =============================================================================

function toArabicNumber(num: number): string {
  return num.toString().split('').map(d => ARABIC_NUMS[parseInt(d)]).join('');
}

// =============================================================================
// Custom Hooks for Data Fetching
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

  // Prefetch adjacent pages
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
      // Use Quran.com API for English tafsirs
      if (quranComId) {
        const response = await api.get(`/tafseer/quran-com/verse/${suraNo}/${ayaNo}`, {
          params: { tafsir_id: quranComId }
        });
        return {
          text: response.data.text || '',
          source: response.data.source || '',
        };
      }
      // Use existing API for Arabic tafsirs
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
// AI Assistant Component (Memoized)
// =============================================================================

interface AIAssistantProps {
  verse: Verse | null;
  tafsirText: string;
  language: 'ar' | 'en';
  isOpen: boolean;
  onClose: () => void;
}

const AIAssistant = memo(function AIAssistant({
  verse,
  tafsirText,
  language,
  isOpen,
  onClose,
}: AIAssistantProps) {
  const { t } = useLanguageStore();
  const [activeTab, setActiveTab] = useState<'summary' | 'explain' | 'qa'>('summary');
  const [selectedWord, setSelectedWord] = useState('');
  const [question, setQuestion] = useState('');
  const [copied, setCopied] = useState(false);

  // AI Mutations
  const summaryMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/tafseer/llm/summarize', {
        tafsir_text: tafsirText,
        verse_text: verse?.text_uthmani || '',
        language,
      });
      return response.data;
    },
  });

  const explainMutation = useMutation({
    mutationFn: async (word: string) => {
      const response = await api.post('/tafseer/llm/explain-word', {
        word: word.trim(),
        verse_text: verse?.text_uthmani || '',
        context: tafsirText || '',
        language,
      });
      return response.data;
    },
  });

  const answerMutation = useMutation({
    mutationFn: async (q: string) => {
      const response = await api.post('/tafseer/llm/answer', {
        question: q.trim(),
        verse_text: verse?.text_uthmani || '',
        tafsir_text: tafsirText || '',
        language,
      });
      return response.data;
    },
  });

  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, []);

  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const word = selection.toString().trim();
      setActiveTab('explain');
      setSelectedWord(word);
      explainMutation.mutate(word);
    }
  }, [explainMutation]);

  const suggestedQuestions = useMemo(() => [
    t('ai_question_revelation'),
    t('ai_question_lessons'),
    t('ai_question_context'),
  ], [t]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl z-50 flex flex-col border-l border-gray-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          <span className="font-bold">{t('ai_assistant')}</span>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-white/20 rounded">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Current Verse */}
      {verse && (
        <div className="p-3 bg-purple-50 border-b">
          <p className="text-sm text-purple-700 font-medium mb-1">
            {verse.sura_name_ar} : {verse.aya_no}
          </p>
          <p
            className="text-sm text-gray-700 font-arabic line-clamp-2 cursor-pointer"
            dir="rtl"
            onMouseUp={handleTextSelection}
            title={t('ai_select_word')}
          >
            {verse.text_uthmani}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b">
        {[
          { key: 'summary', icon: Lightbulb, labelKey: 'ai_summary' },
          { key: 'explain', icon: BookOpen, labelKey: 'ai_explain' },
          { key: 'qa', icon: HelpCircle, labelKey: 'ai_qa' },
        ].map(({ key, icon: Icon, labelKey }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as typeof activeTab)}
            className={clsx(
              'flex-1 py-3 text-sm font-medium flex items-center justify-center gap-1',
              activeTab === key ? 'text-purple-600 border-b-2 border-purple-600' : 'text-gray-500'
            )}
          >
            <Icon className="w-4 h-4" />
            {t(labelKey)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!verse ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <BookOpen className="w-12 h-12 mb-4" />
            <p>{t('ai_select_verse')}</p>
          </div>
        ) : (
          <>
            {/* Summary Tab */}
            {activeTab === 'summary' && (
              <div className="space-y-4">
                <button
                  onClick={() => summaryMutation.mutate()}
                  disabled={summaryMutation.isPending || !tafsirText}
                  className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {summaryMutation.isPending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Lightbulb className="w-5 h-5" />
                  )}
                  {t('ai_generate_summary')}
                </button>

                {!tafsirText && (
                  <p className="text-sm text-amber-600 text-center">
                    {t('ai_open_tafsir_first')}
                  </p>
                )}

                {summaryMutation.data?.result && (
                  <div className="bg-gray-50 rounded-lg p-4 relative group">
                    <button
                      onClick={() => handleCopy(summaryMutation.data.result)}
                      className="absolute top-2 left-2 p-1 bg-white rounded shadow opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4 text-gray-500" />}
                    </button>
                    <p className="font-arabic text-gray-800 leading-relaxed" dir="rtl">
                      {summaryMutation.data.result}
                    </p>
                  </div>
                )}

                {summaryMutation.error && (
                  <p className="text-sm text-red-500 text-center">
                    {t('ai_unavailable')}
                  </p>
                )}
              </div>
            )}

            {/* Explain Tab */}
            {activeTab === 'explain' && (
              <div className="space-y-4">
                <div className="bg-blue-50 rounded-lg p-3 text-sm text-blue-700">
                  {t('ai_select_word_hint')}
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={selectedWord}
                    onChange={(e) => setSelectedWord(e.target.value)}
                    placeholder={t('ai_enter_word')}
                    className="flex-1 px-3 py-2 border rounded-lg text-right"
                    dir="rtl"
                  />
                  <button
                    onClick={() => explainMutation.mutate(selectedWord)}
                    disabled={explainMutation.isPending || !selectedWord.trim()}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:bg-gray-300"
                  >
                    {explainMutation.isPending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      t('ai_explain')
                    )}
                  </button>
                </div>

                {explainMutation.data?.result && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="font-bold text-purple-700 mb-2" dir="rtl">
                      {t('ai_explanation_of').replace('{word}', selectedWord)}
                    </p>
                    <p className="font-arabic text-gray-800 leading-relaxed" dir="rtl">
                      {explainMutation.data.result}
                    </p>
                  </div>
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
                    onKeyDown={(e) => e.key === 'Enter' && answerMutation.mutate(question)}
                    placeholder={t('ai_ask_question')}
                    className="flex-1 px-3 py-2 border rounded-lg"
                    dir={language === 'ar' ? 'rtl' : 'ltr'}
                  />
                  <button
                    onClick={() => answerMutation.mutate(question)}
                    disabled={answerMutation.isPending || !question.trim()}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:bg-gray-300"
                  >
                    {answerMutation.isPending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <MessageSquare className="w-5 h-5" />
                    )}
                  </button>
                </div>

                <div className="space-y-2">
                  <p className="text-xs text-gray-500 font-medium">
                    {t('ai_suggested_questions')}
                  </p>
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setQuestion(q)}
                      className="block w-full text-left text-sm text-purple-600 hover:bg-purple-50 p-2 rounded"
                      dir={language === 'ar' ? 'rtl' : 'ltr'}
                    >
                      {q}
                    </button>
                  ))}
                </div>

                {answerMutation.data?.result && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="font-arabic text-gray-800 leading-relaxed" dir="rtl">
                      {answerMutation.data.result}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Global Error */}
            {(summaryMutation.error || explainMutation.error || answerMutation.error) && (
              <div className="mt-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm flex items-center gap-2">
                <RefreshCw className="w-4 h-4" />
                {t('ai_unavailable')}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
});

// =============================================================================
// Tafsir Card Component (Memoized)
// =============================================================================

interface TafsirCardProps {
  verse: Verse;
  edition: TafsirEdition;
  language: 'ar' | 'en';
  isExpanded: boolean;
  onToggle: () => void;
  onTafsirLoaded: (text: string) => void;
}

const TafsirCard = memo(function TafsirCard({
  verse,
  edition,
  language,
  isExpanded,
  onToggle,
  onTafsirLoaded,
}: TafsirCardProps) {
  const { t } = useLanguageStore();
  const { data: tafsirData, isLoading, error } = useTafsir(
    verse.sura_no,
    verse.aya_no,
    edition.id,
    isExpanded,
    edition.quran_com_id
  );

  const [audioPlaying, setAudioPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Notify parent when tafsir is loaded
  if (tafsirData?.text && isExpanded) {
    onTafsirLoaded(tafsirData.text);
  }

  const toggleAudio = useCallback(() => {
    if (!audioRef.current || !tafsirData?.audio_url) return;

    if (audioPlaying) {
      audioRef.current.pause();
      setAudioPlaying(false);
    } else {
      audioRef.current.src = tafsirData.audio_url;
      audioRef.current.play().catch(console.error);
      setAudioPlaying(true);
    }
  }, [audioPlaying, tafsirData?.audio_url]);

  return (
    <div className="mt-4">
      <button
        onClick={onToggle}
        className={clsx(
          'w-full flex items-center justify-between p-3 rounded-lg transition-colors',
          isExpanded ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        )}
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          <span className="font-medium">{t(edition.translationKey)}</span>
          {edition.has_audio && <Volume2 className="w-4 h-4 text-emerald-600" />}
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isExpanded && (
        <div className="mt-2 p-4 bg-white rounded-lg border border-emerald-200 shadow-sm">
          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span>{t('tafseer_loading')}</span>
            </div>
          ) : error ? (
            <div className="text-center py-4 text-red-500">
              {t('tafseer_error')}
            </div>
          ) : (
            <>
              {tafsirData?.audio_url && (
                <div className="mb-4 flex items-center gap-3 p-3 bg-emerald-50 rounded-lg">
                  <button
                    onClick={toggleAudio}
                    className={clsx(
                      'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
                      audioPlaying
                        ? 'bg-red-500 text-white hover:bg-red-600'
                        : 'bg-emerald-600 text-white hover:bg-emerald-700'
                    )}
                  >
                    {audioPlaying ? (
                      <>
                        <Pause className="w-4 h-4" />
                        <span>{t('mushaf_stop')}</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-4 h-4" />
                        <span>{t('tafsir_listen')}</span>
                      </>
                    )}
                  </button>
                  <span className="text-sm text-emerald-700">
                    {t('tafsir_audio_available')}
                  </span>
                </div>
              )}

              <p
                className={clsx(
                  'text-gray-800 leading-loose text-lg',
                  language === 'ar' ? 'font-arabic' : ''
                )}
                dir={language === 'ar' ? 'rtl' : 'ltr'}
              >
                {tafsirData?.text}
              </p>

              <audio
                ref={audioRef}
                onEnded={() => setAudioPlaying(false)}
                onError={() => setAudioPlaying(false)}
              />
            </>
          )}
        </div>
      )}
    </div>
  );
});

// =============================================================================
// Verse Card Component (Memoized)
// =============================================================================

interface VerseCardProps {
  verse: Verse;
  fontSize: number;
  isSelected: boolean;
  isPlaying: boolean;
  expandedTafsir: number | null;
  selectedEdition: TafsirEdition;
  language: 'ar' | 'en';
  onSelect: (verse: Verse) => void;
  onPlayAudio: (verse: Verse) => void;
  onOpenAI: (verse: Verse) => void;
  onToggleTafsir: (verseId: number) => void;
  onTafsirLoaded: (text: string) => void;
}

const VerseCard = memo(function VerseCard({
  verse,
  fontSize,
  isSelected,
  isPlaying,
  expandedTafsir,
  selectedEdition,
  language,
  onSelect,
  onPlayAudio,
  onOpenAI,
  onToggleTafsir,
  onTafsirLoaded,
}: VerseCardProps) {
  const { t } = useLanguageStore();
  const handleClick = useCallback(() => onSelect(verse), [onSelect, verse]);
  const handlePlay = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onPlayAudio(verse);
  }, [onPlayAudio, verse]);
  const handleAI = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onOpenAI(verse);
  }, [onOpenAI, verse]);
  const handleTafsirToggle = useCallback(() => onToggleTafsir(verse.id), [onToggleTafsir, verse.id]);

  return (
    <div
      className={clsx(
        'relative p-5 rounded-xl border-2 transition-all cursor-pointer',
        isSelected
          ? 'bg-amber-100 border-amber-500 shadow-md'
          : 'bg-white/60 border-transparent hover:border-amber-300 hover:bg-amber-50'
      )}
      onClick={handleClick}
    >
      {/* Verse Number Badge */}
      <div className="absolute left-4 top-4 w-10 h-10 flex items-center justify-center bg-gradient-to-br from-amber-400 to-amber-500 rounded-full border-2 border-amber-600 shadow">
        <span className="font-arabic text-sm font-bold text-amber-900">
          {toArabicNumber(verse.aya_no)}
        </span>
      </div>

      {/* Verse Text */}
      <p
        className="font-arabic leading-loose text-gray-900 pr-0 pl-14 text-right"
        style={{ fontSize: `${fontSize}px`, lineHeight: 2.2 }}
        dir="rtl"
      >
        {verse.text_uthmani}
      </p>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2 mt-4 pl-14">
        <button
          onClick={handlePlay}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
            isPlaying
              ? 'bg-emerald-600 text-white shadow-md'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          )}
        >
          {isPlaying ? (
            <><Pause className="w-4 h-4" />{t('mushaf_pause')}</>
          ) : (
            <><Play className="w-4 h-4" />{t('mushaf_listen')}</>
          )}
        </button>

        <button
          onClick={handleAI}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-purple-100 text-purple-700 hover:bg-purple-200 transition-colors"
        >
          <Sparkles className="w-4 h-4" />
          {t('ai_assistant')}
        </button>
      </div>

      {/* Tafsir Section */}
      <TafsirCard
        verse={verse}
        edition={selectedEdition}
        language={language}
        isExpanded={expandedTafsir === verse.id}
        onToggle={handleTafsirToggle}
        onTafsirLoaded={onTafsirLoaded}
      />
    </div>
  );
}, (prev, next) => {
  // Custom comparison for better performance
  return (
    prev.verse.id === next.verse.id &&
    prev.fontSize === next.fontSize &&
    prev.isSelected === next.isSelected &&
    prev.isPlaying === next.isPlaying &&
    prev.expandedTafsir === next.expandedTafsir &&
    prev.selectedEdition.id === next.selectedEdition.id &&
    prev.language === next.language
  );
});

// =============================================================================
// Main Component
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

  // Page State
  const [currentPage, setCurrentPage] = useState(() => {
    const page = searchParams.get('page');
    return page ? parseInt(page, 10) : 1;
  });

  // Selection State
  const [selectedVerse, setSelectedVerse] = useState<Verse | null>(null);
  const [expandedTafsir, setExpandedTafsir] = useState<number | null>(null);
  const [currentTafsirText, setCurrentTafsirText] = useState('');

  // Settings State
  const [fontSize, setFontSize] = useState(28);
  const [selectedTafsir, setSelectedTafsir] = useState(() =>
    language === 'ar' ? 'muyassar' : 'en_ibn_kathir'
  );
  const [selectedReciter, setSelectedReciter] = useState('mishary_afasy');
  const [showSettings, setShowSettings] = useState(false);
  const [showAI, setShowAI] = useState(false);

  // Audio State
  const [playingVerseId, setPlayingVerseId] = useState<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Data Fetching with React Query
  const { data: verses = [], isLoading, error, prefetchAdjacent } = usePageVerses(currentPage);

  // Reset selected tafsir when language changes
  useEffect(() => {
    setSelectedTafsir(language === 'ar' ? 'muyassar' : 'en_ibn_kathir');
    setExpandedTafsir(null);
    setCurrentTafsirText('');
  }, [language]);

  // Prefetch adjacent pages when current page loads
  useEffect(() => {
    if (verses.length > 0) {
      prefetchAdjacent();
    }
  }, [verses.length, prefetchAdjacent]);

  // Update URL when page changes
  useEffect(() => {
    setSearchParams({ page: currentPage.toString() });
  }, [currentPage, setSearchParams]);

  // Navigate pages with transition for smooth UI
  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= TOTAL_PAGES) {
      startTransition(() => {
        setCurrentPage(page);
        setExpandedTafsir(null);
        setPlayingVerseId(null);
        setSelectedVerse(null);
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

  // Handle verse selection
  const handleVerseSelect = useCallback((verse: Verse) => {
    setSelectedVerse(verse);
  }, []);

  // Open AI for verse
  const handleOpenAI = useCallback((verse: Verse) => {
    setSelectedVerse(verse);
    setShowAI(true);
  }, []);

  // Toggle tafsir with transition
  const toggleTafsir = useCallback((verseId: number) => {
    startTransition(() => {
      setExpandedTafsir(prev => prev === verseId ? null : verseId);
      if (expandedTafsir !== verseId) {
        setCurrentTafsirText('');
      }
    });
  }, [expandedTafsir]);

  // Handle tafsir loaded
  const handleTafsirLoaded = useCallback((text: string) => {
    setCurrentTafsirText(text);
  }, []);

  // Memoized values
  const currentSura = useMemo(() => verses.length > 0 ? verses[0] : null, [verses]);
  const selectedEdition = useMemo(
    () => tafsirEditions.find(e => e.id === selectedTafsir) || tafsirEditions[0],
    [selectedTafsir, tafsirEditions]
  );

  // Settings handlers
  const handleFontDecrease = useCallback(() => setFontSize(prev => Math.max(18, prev - 2)), []);
  const handleFontIncrease = useCallback(() => setFontSize(prev => Math.min(48, prev + 2)), []);
  const handleTafsirChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTafsir(e.target.value);
    setExpandedTafsir(null);
    setCurrentTafsirText('');
  }, []);
  const handleReciterChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedReciter(e.target.value);
  }, []);

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
              <h1 className="font-arabic text-xl font-bold">
                {language === 'ar' ? currentSura.sura_name_ar : currentSura.sura_name_en}
                {language === 'ar' && (
                  <span className="text-sm font-normal text-white/70 ml-2">
                    {currentSura.sura_name_en}
                  </span>
                )}
              </h1>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleFontDecrease}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              title={t('mushaf_zoom_out')}
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            <span className="text-sm min-w-[2rem] text-center">{fontSize}</span>
            <button
              onClick={handleFontIncrease}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              title={t('mushaf_zoom_in')}
            >
              <ZoomIn className="w-5 h-5" />
            </button>

            <div className="w-px h-6 bg-white/30 mx-1" />

            <button
              onClick={() => setShowAI(!showAI)}
              className={clsx(
                'p-2 rounded-lg transition-colors flex items-center gap-1',
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
              <label className="text-sm text-white/80">
                {t('mushaf_tafsir')}:
              </label>
              <select
                value={selectedTafsir}
                onChange={handleTafsirChange}
                className="px-3 py-1.5 rounded bg-white/15 text-white text-sm border border-white/20"
              >
                {tafsirEditions.map(ed => (
                  <option key={ed.id} value={ed.id} className="bg-emerald-800">
                    {t(ed.translationKey)}
                    {ed.has_audio ? ' 🔊' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-white/80">
                {t('mushaf_reciter')}:
              </label>
              <select
                value={selectedReciter}
                onChange={handleReciterChange}
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
      <main className={clsx('transition-all duration-300', showAI ? 'mr-96' : '')}>
        <div className="max-w-4xl mx-auto px-4 py-6">
          {/* Mushaf Frame */}
          <div className="bg-amber-50 rounded-2xl border-4 border-amber-600 shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-amber-200 to-amber-100 px-6 py-3 border-b-2 border-amber-600 flex justify-between items-center">
              <span className="font-arabic text-amber-900 font-medium">
                {t('mushaf_juz')} {verses[0]?.juz_no || 1}
              </span>
              <span className="font-arabic text-amber-900 font-medium">
                {t('mushaf_page')} {currentPage}
              </span>
            </div>

            {/* Verses */}
            <div className="p-6 min-h-[60vh]">
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
                <div className="space-y-6">
                  {verses.map((verse) => (
                    <VerseCard
                      key={verse.id}
                      verse={verse}
                      fontSize={fontSize}
                      isSelected={selectedVerse?.id === verse.id}
                      isPlaying={playingVerseId === verse.id}
                      expandedTafsir={expandedTafsir}
                      selectedEdition={selectedEdition}
                      language={language}
                      onSelect={handleVerseSelect}
                      onPlayAudio={playVerse}
                      onOpenAI={handleOpenAI}
                      onToggleTafsir={toggleTafsir}
                      onTafsirLoaded={handleTafsirLoaded}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gradient-to-r from-amber-200 to-amber-100 px-6 py-3 border-t-2 border-amber-600 text-center">
              <span className="font-arabic text-amber-900 text-sm">
                {verses.length > 0 && (
                  language === 'ar'
                    ? `${verses[0].sura_name_ar} - ${t('mushaf_verses')} ${verses[0].aya_no} ${t('to') || 'إلى'} ${verses[verses.length - 1].aya_no}`
                    : `${verses[0].sura_name_en} - ${t('mushaf_verses')} ${verses[0].aya_no} to ${verses[verses.length - 1].aya_no}`
                )}
              </span>
            </div>
          </div>
        </div>
      </main>

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
