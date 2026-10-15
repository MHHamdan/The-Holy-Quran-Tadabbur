/**
 * Enhanced TafsirPanel Component
 *
 * Production-grade tafsir display following FANG best practices:
 * - Multiple tafsir editions with smart fallback
 * - Collapsible sections for text, audio, and AI features
 * - LLM integration for summarization and word explanations
 * - Audio player with playback controls
 * - Responsive design with smooth animations
 *
 * Features:
 * - Smart caching via backend
 * - Circuit breaker pattern for reliability
 * - Graceful degradation when APIs fail
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiUrl } from '../../lib/config';
import {
  BookOpen,
  Volume2,
  VolumeX,
  Play,
  Pause,
  ChevronDown,
  ChevronUp,
  Loader2,
  ExternalLink,
  User,
  Sparkles,
  MessageSquare,
  BookMarked,
  Copy,
  Check,
  AlertCircle,
  Lightbulb,
  HelpCircle,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { getSourceById } from '../../data/sourceRegistry';
import clsx from 'clsx';

// =============================================================================
// Types & Interfaces
// =============================================================================

interface TafsirEdition {
  id: string;
  slug: string;
  name_ar: string;
  name_en: string;
  author_ar: string;
  author_en: string;
  language: string;
  has_audio: boolean;
  source: string;
  description_ar?: string;
  description_en?: string;
  /**
   * Id of the same work in the app's tafsir library (tafseer_chunks). The AI
   * assistant is grounded on that stored passage, loaded by the server; editions
   * without one have no AI assistant.
   */
  db_source_id?: string;
}

interface TafsirResponse {
  ok: boolean;
  verse_key: string;
  text: string;
  text_html?: string;
  source: string;
  edition: {
    id: string;
    name_ar: string;
    name_en: string;
    author_ar: string;
    author_en: string;
    language: string;
    has_audio: boolean;
  };
  audio_url?: string;
}

interface TafsirPanelProps {
  sura: number;
  ayah: number;
  /** Unused: the server loads the verse text for AI requests itself. */
  verseText?: string;
  isExpanded?: boolean;
  onToggle?: () => void;
}

interface LLMResponse {
  ok: boolean;
  result?: string;
  error?: string;
}

// =============================================================================
// Tafsir Editions Configuration
// =============================================================================

// Only editions the backend lists (TAFSIR_EDITIONS in tafsir_api.py). Al-Wasit
// (Tantawi, d. 2010) is under copyright with no recorded permission, and
// al-Mukhtasar, Ibn Juzayy, al-Suddi and al-Siraj always returned 404.
const TAFSIR_EDITIONS: TafsirEdition[] = [
  {
    id: 'muyassar',
    db_source_id: 'muyassar_ar',
    slug: 'almuyassar',
    name_ar: 'التفسير الميسر',
    name_en: 'Al-Muyassar (Simplified)',
    author_ar: 'مجمع الملك فهد لطباعة المصحف',
    author_en: 'King Fahd Complex',
    language: 'ar',
    has_audio: true,
    source: 'quran_com',
    description_ar: 'تفسير ميسر للقرآن الكريم',
    description_en: 'Simplified Quran interpretation',
  },
  {
    id: 'ibn_kathir',
    db_source_id: 'ibn_kathir_ar',
    slug: 'ibn-kathir',
    name_ar: 'تفسير ابن كثير',
    name_en: 'Tafsir Ibn Kathir',
    author_ar: 'الحافظ ابن كثير الدمشقي',
    author_en: 'Imam Ibn Kathir',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'من أشهر التفاسير بالمأثور',
    description_en: 'Famous classical tafsir based on hadith',
  },
  {
    id: 'saadi',
    slug: 'alsaadi',
    name_ar: 'تفسير السعدي',
    name_en: 'Tafsir As-Saadi',
    author_ar: 'الشيخ عبدالرحمن السعدي',
    author_en: 'Sheikh As-Saadi',
    language: 'ar',
    has_audio: true,
    source: 'quran_com',
    description_ar: 'تفسير عصري سهل العبارة',
    description_en: 'Modern tafsir with easy language',
  },
  {
    id: 'tabari',
    db_source_id: 'tabari_ar',
    slug: 'tabari',
    name_ar: 'جامع البيان - الطبري',
    name_en: 'Jami al-Bayan (At-Tabari)',
    author_ar: 'الإمام الطبري',
    author_en: 'Imam At-Tabari',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'أقدم التفاسير وأشملها',
    description_en: 'Earliest and most comprehensive tafsir',
  },
  {
    id: 'qurtubi',
    db_source_id: 'qurtubi_ar',
    slug: 'qurtubi',
    name_ar: 'الجامع لأحكام القرآن',
    name_en: 'Al-Jami (Al-Qurtubi)',
    author_ar: 'الإمام القرطبي',
    author_en: 'Imam Al-Qurtubi',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'تفسير فقهي شامل',
    description_en: 'Comprehensive fiqh-focused tafsir',
  },
  {
    id: 'baghawi',
    slug: 'baghawi',
    name_ar: 'معالم التنزيل',
    name_en: "Ma'alim at-Tanzil",
    author_ar: 'الإمام البغوي',
    author_en: 'Imam Al-Baghawi',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'تفسير وسط بين المأثور والرأي',
    description_en: 'Balanced tafsir',
  },
  {
    id: 'jalalayn',
    slug: 'aljalalayn',
    name_ar: 'تفسير الجلالين',
    name_en: 'Tafsir Al-Jalalayn',
    author_ar: 'المحلي والسيوطي',
    author_en: 'Al-Mahalli & As-Suyuti',
    language: 'ar',
    has_audio: true,
    source: 'quran_tafseer',
    description_ar: 'تفسير موجز ومختصر',
    description_en: 'Concise tafsir by two great Imams',
  },
];

// =============================================================================
// Marked text: the API keeps Quran.com emphasis as ⟨…⟩ (key terms) and 『…』
// (quoted verses). They become <mark> elements; no HTML is ever injected.
// =============================================================================

const MARKER_PAIRS: Record<string, { close: string; className: string }> = {
  '⟨': { close: '⟩', className: 'bg-transparent text-amber-800 font-semibold' },
  '『': { close: '』', className: 'bg-transparent text-emerald-800' },
};

export function TafsirMarkedText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  let buf = '';
  let i = 0;
  let key = 0;
  while (i < text.length) {
    const open = MARKER_PAIRS[text[i]];
    const end = open ? text.indexOf(open.close, i + 1) : -1;
    if (open && end > i) {
      if (buf) { parts.push(buf); buf = ''; }
      parts.push(<mark key={key++} className={open.className}>{text.slice(i + 1, end)}</mark>);
      i = end + 1;
      continue;
    }
    // Unpaired marker characters are dropped rather than shown raw.
    if (!(text[i] in MARKER_PAIRS) && text[i] !== '⟩' && text[i] !== '』') buf += text[i];
    i += 1;
  }
  if (buf) parts.push(buf);
  return <>{parts}</>;
}

// =============================================================================
// Attribution footer (exported so other tafsir views, e.g. the Mushaf sheet,
// show the same title, author, licence and source line)
// =============================================================================

const HOST_LABELS: Record<string, string> = {
  quran_com: 'Quran.com',
  quran_tafseer: 'quran-tafseer.com',
  tafsir_one: 'read.tafsir.one',
};

export interface TafsirAttributionEdition {
  id: string;
  name_ar: string;
  name_en: string;
  author_ar: string;
  author_en: string;
  db_source_id?: string;
}

export function TafsirAttributionFooter({
  edition,
  source,
  sourceUrl,
  language,
}: {
  edition: TafsirAttributionEdition;
  /** Host the text was fetched from (API `source` field). */
  source: string;
  sourceUrl?: string;
  language: 'ar' | 'en';
}) {
  const ar = language === 'ar';
  const registry = edition.db_source_id ? getSourceById(edition.db_source_id) : undefined;
  const host = HOST_LABELS[source] ?? source;
  return (
    <div
      className={clsx('pt-2 border-t border-gray-100 text-xs text-gray-500 space-y-0.5', ar && 'font-arabic')}
      dir={ar ? 'rtl' : 'ltr'}
    >
      <p>
        <span dir={ar ? 'rtl' : 'ltr'}>{ar ? edition.name_ar : edition.name_en}</span>
        {' — '}
        <span>{ar ? edition.author_ar : edition.author_en}</span>
        {' · '}
        <bdi dir="ltr" className="font-mono text-[10px]">{edition.db_source_id ?? edition.id}</bdi>
      </p>
      <p>
        {ar ? 'الترخيص: ' : 'Licence: '}
        {registry ? (
          <span dir="ltr" lang="en">{registry.licenseOrTerms}</span>
        ) : (
          <span>{ar ? 'غير موثّق بعد' : 'not yet recorded'}</span>
        )}
      </p>
      <p className="flex items-center gap-2 flex-wrap">
        <span>
          {ar ? 'المصدر: ' : 'Source: '}
          <bdi dir="ltr">{host}</bdi>
        </span>
        {sourceUrl && (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-amber-600 hover:text-amber-700 hover:underline"
          >
            <ExternalLink className="w-3 h-3" />
            {ar ? 'عرض المصدر' : 'View source'}
          </a>
        )}
      </p>
    </div>
  );
}

// =============================================================================
// Collapsible Section Component
// =============================================================================

interface CollapsibleSectionProps {
  title: string;
  titleAr: string;
  icon: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  badge?: string;
  badgeColor?: string;
}

function CollapsibleSection({
  title,
  titleAr,
  icon,
  isOpen,
  onToggle,
  children,
  badge,
  badgeColor = 'bg-gray-100 text-gray-600',
}: CollapsibleSectionProps) {
  const { language } = useLanguageStore();

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-2">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-medium text-gray-700">
            {language === 'ar' ? titleAr : title}
          </span>
          {badge && (
            <span className={clsx('px-2 py-0.5 text-xs rounded-full', badgeColor)}>
              {badge}
            </span>
          )}
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>
      {isOpen && <div className="p-3 bg-white">{children}</div>}
    </div>
  );
}

// =============================================================================
// Session cache for tafsir (avoids re-fetch when panel is re-opened)
// =============================================================================

const TAFSIR_CACHE_PREFIX = 'tafsir_panel:v2:';

function getTafsirCached(sura: number, ayah: number, editionId: string): TafsirResponse | null {
  try {
    const raw = sessionStorage.getItem(`${TAFSIR_CACHE_PREFIX}${sura}:${ayah}:${editionId}`);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function setTafsirCached(sura: number, ayah: number, editionId: string, data: TafsirResponse) {
  try {
    sessionStorage.setItem(`${TAFSIR_CACHE_PREFIX}${sura}:${ayah}:${editionId}`, JSON.stringify(data));
  } catch { /* storage unavailable or full: caching is best-effort */ }
}

// =============================================================================
// Main TafsirPanel Component
// =============================================================================

export function TafsirPanel({ sura, ayah, isExpanded = false, onToggle }: TafsirPanelProps) {
  const { language } = useLanguageStore();
  const [expanded, setExpanded] = useState(isExpanded);
  const [selectedEdition, setSelectedEdition] = useState<TafsirEdition>(TAFSIR_EDITIONS[0]);
  const [tafsirData, setTafsirData] = useState<TafsirResponse | null>(
    () => getTafsirCached(sura, ayah, TAFSIR_EDITIONS[0].id)
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Collapsible sections state
  const [showAudio, setShowAudio] = useState(false);
  const [showAI, setShowAI] = useState(false);
  const [showFullText, setShowFullText] = useState(true);

  // Audio player state
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioError, setAudioError] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  // AI/LLM state
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [wordExplanation, setWordExplanation] = useState<string | null>(null);
  const [wordExplanationLoading, setWordExplanationLoading] = useState(false);
  const [selectedWord, setSelectedWord] = useState<string>('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [answerLoading, setAnswerLoading] = useState(false);

  // Copy state
  const [copied, setCopied] = useState(false);

  // Abort in-flight requests on unmount
  useEffect(() => () => { abortRef.current?.abort(); }, []);

  // Fetch tafsir when edition or verse changes
  useEffect(() => {
    if (expanded && selectedEdition) {
      fetchTafsir();
    }
  }, [sura, ayah, selectedEdition, expanded]);

  // Reset states when edition changes
  useEffect(() => {
    setIsPlaying(false);
    setAudioError(false);
    setSummary(null);
    setWordExplanation(null);
    setAnswer(null);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, [selectedEdition]);

  // Auto-expand on first load
  useEffect(() => {
    if (isExpanded && !expanded) {
      setExpanded(true);
    }
  }, [isExpanded]);

  const fetchTafsir = useCallback(async () => {
    const cached = getTafsirCached(sura, ayah, selectedEdition.id);
    if (cached) { setTafsirData(cached); return; }

    setLoading(true);
    setError(null);
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const response = await fetch(
        apiUrl(`/api/v1/tafseer/external/verse/${sura}/${ayah}?edition=${selectedEdition.id}`),
        { signal: abortRef.current.signal }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || 'Failed to fetch tafsir');
      }

      const data: TafsirResponse = await response.json();
      setTafsirCached(sura, ayah, selectedEdition.id, data);
      setTafsirData(data);
    } catch (err) {
      if ((err as Error)?.name === 'AbortError') return;
      console.error('Error fetching tafsir:', err);
      // Never switch the reader to another scholar's tafsir on failure: keep
      // the chosen edition and offer Retry.
      setError(
        language === 'ar'
          ? 'تعذّر تحميل هذا التفسير. أعد المحاولة.'
          : 'Could not load this tafsir. Please retry.'
      );
    } finally {
      setLoading(false);
    }
  }, [sura, ayah, selectedEdition, language]);

  function handleToggle() {
    const newExpanded = !expanded;
    setExpanded(newExpanded);
    onToggle?.();
  }

  function handleEditionChange(edition: TafsirEdition) {
    setSelectedEdition(edition);
    setTafsirData(null);
    setError(null);
  }

  function togglePlayPause() {
    if (!audioRef.current || !selectedEdition.has_audio) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  }

  function handleSpeedChange() {
    const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
    const currentIndex = speeds.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % speeds.length;
    const newSpeed = speeds[nextIndex];
    setPlaybackSpeed(newSpeed);
    if (audioRef.current) {
      audioRef.current.playbackRate = newSpeed;
    }
  }

  async function handleCopyText() {
    if (!tafsirData?.text) return;
    try {
      await navigator.clipboard.writeText(tafsirData.text.replace(/[⟨⟩『』]/g, ''));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }

  // LLM requests carry identifiers only. The server loads the verse from the
  // Qur'an table and the tafsir passage from the app's library, and refuses
  // when no licensed passage exists for this source and verse.
  const aiSourceId = selectedEdition.db_source_id;

  async function postLLM(path: string, extra: Record<string, string>): Promise<LLMResponse> {
    const response = await fetch(apiUrl(`/api/v1/tafseer/llm/${path}`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sura, aya: ayah, source_id: aiSourceId, language, ...extra }),
    });
    return response.json();
  }

  // LLM: Generate Summary
  async function generateSummary() {
    if (!aiSourceId) return;
    setSummaryLoading(true);
    try {
      const data = await postLLM('summarize', {});
      if (data.ok && data.result) {
        setSummary(data.result);
      } else {
        setSummary(data.error || (language === 'ar' ? 'فشل في التلخيص' : 'Failed to summarize'));
      }
    } catch {
      setSummary(language === 'ar' ? 'خدمة الذكاء الاصطناعي غير متاحة' : 'AI service unavailable');
    } finally {
      setSummaryLoading(false);
    }
  }

  // LLM: Explain Word
  async function explainWord(word: string) {
    if (!word.trim() || !aiSourceId) return;
    setSelectedWord(word);
    setWordExplanationLoading(true);
    try {
      const data = await postLLM('explain-word', { word: word.trim().slice(0, 64) });
      if (data.ok && data.result) {
        setWordExplanation(data.result);
      } else {
        setWordExplanation(data.error || (language === 'ar' ? 'فشل في الشرح' : 'Failed to explain'));
      }
    } catch {
      setWordExplanation(language === 'ar' ? 'خدمة الذكاء الاصطناعي غير متاحة' : 'AI service unavailable');
    } finally {
      setWordExplanationLoading(false);
    }
  }

  // LLM: Answer Question
  async function askQuestion() {
    if (!question.trim() || !aiSourceId) return;
    setAnswerLoading(true);
    try {
      const data = await postLLM('answer', { question: question.trim().slice(0, 500) });
      if (data.ok && data.result) {
        setAnswer(data.result);
      } else {
        setAnswer(data.error || (language === 'ar' ? 'فشل في الإجابة' : 'Failed to answer'));
      }
    } catch {
      setAnswer(language === 'ar' ? 'خدمة الذكاء الاصطناعي غير متاحة' : 'AI service unavailable');
    } finally {
      setAnswerLoading(false);
    }
  }

  // Handle text selection for word explanation
  function handleTextSelection() {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const word = selection.toString().trim();
      if (word.length > 0 && word.length < 50) {
        explainWord(word);
      }
    }
  }

  // Build audio URL
  const audioUrl = selectedEdition.has_audio
    ? `https://read.tafsir.one/audio/${selectedEdition.slug}/${String(sura).padStart(3, '0')}.mp3`
    : null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors rounded-t-lg"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-100 rounded-lg">
            <BookOpen className="w-5 h-5 text-amber-700" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-gray-800">
              {language === 'ar' ? 'التفسير' : 'Tafsir'}
            </h3>
            <p className="text-xs text-gray-500">
              {language === 'ar' ? selectedEdition.name_ar : selectedEdition.name_en}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {selectedEdition.has_audio && (
            <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full flex items-center gap-1">
              <Volume2 className="w-3 h-3" />
              {language === 'ar' ? 'صوتي' : 'Audio'}
            </span>
          )}
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="p-4 pt-0 space-y-4">
          {/* Edition Selector */}
          <div className="flex flex-wrap gap-2 pb-3 border-b border-gray-100">
            {TAFSIR_EDITIONS.map((edition) => (
              <button
                key={edition.id}
                onClick={() => handleEditionChange(edition)}
                title={language === 'ar' ? edition.description_ar : edition.description_en}
                className={clsx(
                  'px-3 py-1.5 text-xs rounded-lg border transition-all flex items-center gap-1.5',
                  selectedEdition.id === edition.id
                    ? 'bg-amber-100 border-amber-300 text-amber-800 shadow-sm'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-amber-300 hover:bg-amber-50'
                )}
              >
                {edition.has_audio && <Volume2 className="w-3 h-3 text-green-600" />}
                <span className="font-medium">
                  {language === 'ar' ? edition.name_ar : edition.name_en}
                </span>
              </button>
            ))}
          </div>

          {/* Scholar Info */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-gray-600">
              <User className="w-4 h-4" />
              <span>{language === 'ar' ? selectedEdition.author_ar : selectedEdition.author_en}</span>
            </div>
            {tafsirData && (
              <button
                onClick={handleCopyText}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-green-600" />
                    <span className="text-green-600">{language === 'ar' ? 'تم النسخ' : 'Copied'}</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>{language === 'ar' ? 'نسخ' : 'Copy'}</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Main Tafsir Content */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
              <p className="text-sm text-gray-500">
                {language === 'ar' ? 'جاري تحميل التفسير...' : 'Loading tafsir...'}
              </p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <AlertCircle className="w-8 h-8 text-red-400" />
              <p className="text-sm text-red-500 text-center">{error}</p>
              <button
                onClick={() => fetchTafsir()}
                className="px-4 py-2 text-sm bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors"
              >
                {language === 'ar' ? 'إعادة المحاولة' : 'Retry'}
              </button>
            </div>
          ) : tafsirData ? (
            <>
              {/* Tafsir Text Section */}
              <CollapsibleSection
                title="Tafsir Text"
                titleAr="نص التفسير"
                icon={<BookMarked className="w-4 h-4 text-amber-600" />}
                isOpen={showFullText}
                onToggle={() => setShowFullText(!showFullText)}
              >
                <div
                  className="bg-amber-50 rounded-lg p-4 max-h-96 overflow-y-auto"
                  dir="rtl"
                  onMouseUp={handleTextSelection}
                >
                  <p className="text-base leading-loose font-arabic text-gray-800 whitespace-pre-wrap selection:bg-amber-200">
                    <TafsirMarkedText text={tafsirData.text} />
                  </p>
                </div>
                <p className="text-xs text-gray-400 mt-2 text-center">
                  {language === 'ar'
                    ? 'حدد كلمة للحصول على شرحها'
                    : 'Select a word to get its explanation'}
                </p>
              </CollapsibleSection>

              {/* Audio Section */}
              {selectedEdition.has_audio && audioUrl && (
                <CollapsibleSection
                  title="Audio Player"
                  titleAr="المشغل الصوتي"
                  icon={<Volume2 className="w-4 h-4 text-green-600" />}
                  isOpen={showAudio}
                  onToggle={() => setShowAudio(!showAudio)}
                  badge={language === 'ar' ? 'متاح' : 'Available'}
                  badgeColor="bg-green-100 text-green-700"
                >
                  <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                    <button
                      onClick={togglePlayPause}
                      disabled={audioLoading || audioError}
                      className={clsx(
                        'p-3 rounded-full transition-all shadow-sm',
                        audioError
                          ? 'bg-red-100 text-red-500'
                          : 'bg-green-500 text-white hover:bg-green-600'
                      )}
                    >
                      {audioLoading ? (
                        <Loader2 className="w-6 h-6 animate-spin" />
                      ) : audioError ? (
                        <VolumeX className="w-6 h-6" />
                      ) : isPlaying ? (
                        <Pause className="w-6 h-6" />
                      ) : (
                        <Play className="w-6 h-6" />
                      )}
                    </button>

                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-700">
                        {language === 'ar'
                          ? `تفسير سورة ${sura}`
                          : `Tafsir of Surah ${sura}`}
                      </p>
                      <p className="text-xs text-gray-500">
                        {language === 'ar' ? selectedEdition.author_ar : selectedEdition.author_en}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleSpeedChange}
                        className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-100 font-medium"
                      >
                        {playbackSpeed}x
                      </button>
                    </div>
                  </div>

                  <audio
                    ref={audioRef}
                    src={audioUrl}
                    onLoadStart={() => setAudioLoading(true)}
                    onCanPlay={() => setAudioLoading(false)}
                    onError={() => {
                      setAudioError(true);
                      setAudioLoading(false);
                    }}
                    onEnded={() => setIsPlaying(false)}
                    preload="none"
                  />
                </CollapsibleSection>
              )}

              {/* AI Features Section */}
              <CollapsibleSection
                title="AI Assistant"
                titleAr="المساعد الذكي"
                icon={<Sparkles className="w-4 h-4 text-purple-600" />}
                isOpen={showAI}
                onToggle={() => setShowAI(!showAI)}
                badge="Beta"
                badgeColor="bg-purple-100 text-purple-700"
              >
                <div className="space-y-4">
                  {/* Results here are model-written (ai_generated), never Qur'an or tafsir text */}
                  <p className="text-xs text-gray-500" dir={language === 'ar' ? 'rtl' : 'ltr'}>
                    {language === 'ar'
                      ? 'نصوص مولَّدة بالذكاء الاصطناعي، وليست قرآناً ولا تفسيراً. راجع المصدر أعلاه.'
                      : 'AI-generated text, not Qur\'an or tafsir. Check it against the source above.'}
                  </p>
                  {!aiSourceId ? (
                    <p className="text-sm text-gray-600" dir={language === 'ar' ? 'rtl' : 'ltr'}>
                      {language === 'ar'
                        ? 'المساعد الذكي متاح فقط للتفاسير المحفوظة في مكتبة التطبيق (الميسر، ابن كثير، الطبري، القرطبي).'
                        : 'The AI assistant works only with tafsir stored in the app library (al-Muyassar, Ibn Kathir, al-Tabari, al-Qurtubi).'}
                    </p>
                  ) : (<>
                  {/* Summary */}
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-purple-800 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4" />
                        {language === 'ar' ? 'ملخص التفسير' : 'Tafsir Summary'}
                      </h4>
                      <button
                        onClick={generateSummary}
                        disabled={summaryLoading}
                        className="px-3 py-1 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                      >
                        {summaryLoading ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          language === 'ar' ? 'توليد' : 'Generate'
                        )}
                      </button>
                    </div>
                    {summary && (
                      <p className="text-sm text-gray-700 leading-relaxed" dir={language === 'ar' ? 'rtl' : 'ltr'}>
                        {summary}
                      </p>
                    )}
                  </div>

                  {/* Word Explanation */}
                  {(selectedWord || wordExplanation) && (
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <h4 className="text-sm font-medium text-blue-800 mb-2 flex items-center gap-2">
                        <BookOpen className="w-4 h-4" />
                        {language === 'ar' ? 'شرح الكلمة' : 'Word Explanation'}
                        {selectedWord && (
                          <span className="px-2 py-0.5 bg-blue-200 rounded text-xs">{selectedWord}</span>
                        )}
                      </h4>
                      {wordExplanationLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                      ) : wordExplanation ? (
                        <p className="text-sm text-gray-700 leading-relaxed" dir={language === 'ar' ? 'rtl' : 'ltr'}>
                          {wordExplanation}
                        </p>
                      ) : null}
                    </div>
                  )}

                  {/* Q&A */}
                  <div className="p-3 bg-green-50 rounded-lg">
                    <h4 className="text-sm font-medium text-green-800 mb-2 flex items-center gap-2">
                      <HelpCircle className="w-4 h-4" />
                      {language === 'ar' ? 'اسأل عن الآية' : 'Ask About the Verse'}
                    </h4>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && askQuestion()}
                        placeholder={language === 'ar' ? 'اكتب سؤالك هنا...' : 'Type your question...'}
                        className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        dir={language === 'ar' ? 'rtl' : 'ltr'}
                      />
                      <button
                        onClick={askQuestion}
                        disabled={answerLoading || !question.trim()}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                      >
                        {answerLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <MessageSquare className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    {answer && (
                      <p className="mt-3 text-sm text-gray-700 leading-relaxed p-2 bg-white rounded" dir={language === 'ar' ? 'rtl' : 'ltr'}>
                        {answer}
                      </p>
                    )}
                  </div>
                  </>)}
                </div>
              </CollapsibleSection>

              {/* Source attribution: title, author, licence and where the text came from */}
              <TafsirAttributionFooter
                edition={selectedEdition}
                source={tafsirData.source}
                sourceUrl={
                  tafsirData.source === 'quran_com'
                    ? `https://quran.com/${sura}/${ayah}/tafsirs`
                    : tafsirData.source === 'quran_tafseer'
                    ? 'http://quran-tafseer.com'
                    : `https://read.tafsir.one/${selectedEdition.slug}`
                }
                language={language}
              />
            </>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">
                {language === 'ar' ? 'اختر تفسيراً للعرض' : 'Select a tafsir to display'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default TafsirPanel;
