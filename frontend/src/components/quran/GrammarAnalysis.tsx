/**
 * Arabic Grammar Analysis (إعراب) Component
 *
 * Priority:
 *   1. QAC `/grammar/irab/` — scholar-verified corpus data
 *   2. Static fallback for common verses
 *   3. AI analysis via the backend (Hugging Face), when configured
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  BookOpen, AlertCircle, ChevronDown, ChevronUp, Loader2,
  AlertTriangle, Info, BookOpenCheck, RefreshCw,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import {
  grammarApi, GrammarAnalysis as GrammarAnalysisType, GrammarToken,
  GrammarHealth, vocabularyApi, VocabularyResponse,
} from '../../lib/api';
import clsx from 'clsx';

interface Props {
  suraNo: number;
  ayaNo: number;
  verseText?: string;
}

// Color mapping for parts of speech
const POS_COLORS: Record<string, { card: string; badge: string }> = {
  'اسم':           { card: 'bg-blue-50 border-blue-200',   badge: 'bg-blue-100 text-blue-800' },
  'اسم علم':       { card: 'bg-blue-100 border-blue-300',  badge: 'bg-blue-200 text-blue-900' },
  'ضمير':          { card: 'bg-sky-50 border-sky-200',     badge: 'bg-sky-100 text-sky-800' },
  'اسم إشارة':     { card: 'bg-cyan-50 border-cyan-200',   badge: 'bg-cyan-100 text-cyan-800' },
  'اسم موصول':     { card: 'bg-teal-50 border-teal-200',   badge: 'bg-teal-100 text-teal-800' },
  'اسم استفهام':   { card: 'bg-indigo-50 border-indigo-200',badge: 'bg-indigo-100 text-indigo-800' },
  'مصدر':          { card: 'bg-violet-50 border-violet-200',badge: 'bg-violet-100 text-violet-800' },
  'صفة':           { card: 'bg-blue-50 border-blue-200',   badge: 'bg-blue-100 text-blue-700' },
  'فعل':           { card: 'bg-green-50 border-green-200', badge: 'bg-green-100 text-green-800' },
  'فعل ماض':       { card: 'bg-green-100 border-green-300',badge: 'bg-green-200 text-green-900' },
  'فعل مضارع':     { card: 'bg-emerald-50 border-emerald-200',badge: 'bg-emerald-100 text-emerald-800' },
  'فعل أمر':       { card: 'bg-lime-50 border-lime-200',   badge: 'bg-lime-100 text-lime-800' },
  'حرف':           { card: 'bg-amber-50 border-amber-200', badge: 'bg-amber-100 text-amber-800' },
  'حرف جر':        { card: 'bg-orange-50 border-orange-200',badge: 'bg-orange-100 text-orange-800' },
  'حرف عطف':       { card: 'bg-yellow-50 border-yellow-200',badge: 'bg-yellow-100 text-yellow-800' },
  'حرف نفي':       { card: 'bg-red-50 border-red-200',     badge: 'bg-red-100 text-red-800' },
  'حرف استفهام':   { card: 'bg-rose-50 border-rose-200',   badge: 'bg-rose-100 text-rose-800' },
  'حرف شرط':       { card: 'bg-pink-50 border-pink-200',   badge: 'bg-pink-100 text-pink-800' },
  'حرف استثناء':   { card: 'bg-fuchsia-50 border-fuchsia-200',badge: 'bg-fuchsia-100 text-fuchsia-800' },
  'غير محدد':      { card: 'bg-gray-50 border-gray-200',   badge: 'bg-gray-100 text-gray-600' },
};

const DEFAULT_COLORS = { card: 'bg-gray-50 border-gray-200', badge: 'bg-gray-100 text-gray-600' };

function getPosColors(pos: string) {
  return POS_COLORS[pos] || DEFAULT_COLORS;
}

function ConfidenceDot({ confidence }: { confidence: number }) {
  const color = confidence >= 0.8 ? 'bg-green-500' : confidence >= 0.5 ? 'bg-yellow-400' : 'bg-red-400';
  const label = Math.round(confidence * 100);
  return (
    <span className="inline-flex items-center gap-1 text-xs text-gray-400">
      <span className={clsx('w-2 h-2 rounded-full inline-block', color)} />
      {label}%
    </span>
  );
}

function TokenCard({ token, isExpanded, onToggle }: {
  token: GrammarToken; isExpanded: boolean; onToggle: () => void;
}) {
  const colors = getPosColors(token.pos);
  const hasRole = token.role && token.role !== 'غير محدد';
  const hasIrab = token.i3rab && token.i3rab.length > 2;

  return (
    <div
      className={clsx(
        'border rounded-xl overflow-hidden transition-all cursor-pointer hover:shadow-md',
        colors.card,
        isExpanded && 'ring-2 ring-primary-400 shadow-md',
      )}
      onClick={onToggle}
      dir="rtl"
    >
      {/* Word header */}
      <div className="px-3 pt-3 pb-2 text-center">
        <div className="text-2xl font-arabic font-bold text-gray-900 leading-tight mb-2">
          {token.word}
        </div>
        <span className={clsx('inline-block text-xs font-medium px-2 py-0.5 rounded-full', colors.badge)}>
          {token.pos}
        </span>
        {hasRole && (
          <div className="mt-1 text-xs text-gray-600 font-medium">{token.role}</div>
        )}
      </div>

      {/* I'rab preview (first line) when collapsed */}
      {!isExpanded && hasIrab && (
        <div className="px-3 pb-2 text-xs text-gray-500 text-right leading-relaxed line-clamp-2">
          {token.i3rab}
        </div>
      )}

      {/* Expanded details */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-white/70 p-3 space-y-2 text-right" dir="rtl">
          {hasIrab && (
            <div className="text-sm text-gray-800 font-arabic leading-relaxed">
              <span className="font-bold text-gray-900 text-xs block mb-0.5">الإعراب:</span>
              {token.i3rab}
            </div>
          )}
          {token.root && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-500">الجذر:</span>
              <span className="font-arabic font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                {token.root}
              </span>
            </div>
          )}
          {token.pattern && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-500">الوزن:</span>
              <span className="font-arabic text-violet-700">{token.pattern}</span>
            </div>
          )}
          {token.case_ending && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-500">علامة الإعراب:</span>
              <span className="font-arabic text-amber-700">{token.case_ending}</span>
            </div>
          )}
          {token.notes_ar && (
            <div className="text-xs text-gray-500 italic border-t border-gray-100 pt-2">
              {token.notes_ar}
            </div>
          )}
          <ConfidenceDot confidence={token.confidence} />
        </div>
      )}

      {/* Expand/collapse cue */}
      <div className="flex justify-center pb-1.5">
        {isExpanded
          ? <ChevronUp className="w-3.5 h-3.5 text-gray-400" />
          : <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
        }
      </div>
    </div>
  );
}

function SourceBadge({ source }: { source: string }) {
  const map: Record<string, { label: string; style: string }> = {
    corpus:     { label: 'موثق علمياً',   style: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    static:     { label: 'بيانات ثابتة', style: 'bg-blue-100 text-blue-700 border-blue-200' },
    llm:        { label: 'تحليل ذكي',    style: 'bg-purple-100 text-purple-700 border-purple-200' },
    hybrid:     { label: 'مختلط',        style: 'bg-indigo-100 text-indigo-700 border-indigo-200' },
    fallback:   { label: 'احتياطي',      style: 'bg-gray-100 text-gray-600 border-gray-200' },
    unavailable:{ label: 'غير متاح',    style: 'bg-amber-100 text-amber-700 border-amber-200' },
    error:      { label: 'خطأ',          style: 'bg-red-100 text-red-700 border-red-200' },
  };
  const cfg = map[source] || { label: source, style: 'bg-gray-100 text-gray-600 border-gray-200' };
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded border font-medium', cfg.style)}>
      {cfg.label}
    </span>
  );
}

const SESSION_CACHE_PREFIX = 'grammar_irab:';

function getCached(key: string): GrammarAnalysisType | null {
  try {
    const raw = sessionStorage.getItem(SESSION_CACHE_PREFIX + key);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function setCached(key: string, data: GrammarAnalysisType) {
  try { sessionStorage.setItem(SESSION_CACHE_PREFIX + key, JSON.stringify(data)); } catch {}
}

export function GrammarAnalysisView({ suraNo, ayaNo, verseText }: Props) {
  const { language } = useLanguageStore();
  const verseRef = `${suraNo}:${ayaNo}`;
  const [analysis, setAnalysis] = useState<GrammarAnalysisType | null>(() => getCached(verseRef));
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedToken, setExpandedToken] = useState<number | null>(null);
  const [showLegend, setShowLegend] = useState(false);
  const [healthStatus, setHealthStatus] = useState<GrammarHealth | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    grammarApi.health().then(r => setHealthStatus(r.data)).catch(() => {});
  }, []);

  useEffect(() => () => { abortRef.current?.abort(); }, []);

  const loadAnalysis = useCallback(async () => {
    const cached = getCached(verseRef);
    if (cached) { setAnalysis(cached); return; }

    setLoading(true);
    setError(null);
    setExpandedToken(null);
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      // QAC / static path — fast (< 50ms), no LLM call
      const irabResult = await grammarApi.analyzeIrab(verseRef);
      const data = irabResult.data;
      setCached(verseRef, data);
      setAnalysis(data);
    } catch (err: unknown) {
      if ((err as Error)?.name !== 'CanceledError') {
        setError(
          language === 'ar'
            ? 'تعذّر تحميل الإعراب. يُرجى المحاولة لاحقاً.'
            : 'Failed to load grammar analysis. Please try again later.',
        );
      }
    } finally {
      setLoading(false);
    }
  }, [verseRef, language]);

  const loadAiAnalysis = useCallback(async () => {
    setAiLoading(true);
    setError(null);
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const result = verseText
        ? await grammarApi.analyzeText(verseText, verseRef)
        : await grammarApi.analyzeAyah(verseRef);
      const data = result.data;
      setCached(verseRef, data);
      setAnalysis(data);
    } catch (err: unknown) {
      if ((err as Error)?.name !== 'CanceledError') {
        setError(
          language === 'ar'
            ? 'تعذّر تحميل الإعراب بالذكاء الاصطناعي.'
            : 'AI analysis failed. Please try again.',
        );
      }
    } finally {
      setAiLoading(false);
    }
  }, [verseRef, verseText, language]);

  // ── Initial "load" button state ─────────────────────────────────────────────
  if (!analysis && !loading && !error) {
    const isUnavailable = healthStatus?.status === 'unavailable';
    const isStaticOnly  = healthStatus?.status === 'static_only';

    return (
      <div className="p-5 space-y-3">
        {isStaticOnly && (
          <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm" dir={language === 'ar' ? 'rtl' : 'ltr'}>
            <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
            <span className="text-blue-800">
              {language === 'ar' ? healthStatus?.message_ar : healthStatus?.message_en}
            </span>
          </div>
        )}
        {isUnavailable && (
          <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm" dir={language === 'ar' ? 'rtl' : 'ltr'}>
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <span className="text-amber-800">
              {language === 'ar' ? healthStatus?.message_ar : healthStatus?.message_en}
            </span>
          </div>
        )}
        <div className="text-center">
          <button
            onClick={loadAnalysis}
            disabled={isUnavailable}
            className={clsx(
              'inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all',
              isUnavailable
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-primary-600 hover:bg-primary-700 text-white shadow-sm hover:shadow-md',
              language === 'ar' && 'font-arabic',
            )}
          >
            <BookOpen className="w-4 h-4" />
            {language === 'ar' ? 'تحليل إعراب الآية' : 'Analyze Grammar'}
          </button>
          <p className="mt-2 text-xs text-gray-400">
            {language === 'ar'
              ? 'يستخدم بيانات الهيئة القرآنية + بيانات ثابتة محققة'
              : 'Uses QAC corpus data + verified static data'}
          </p>
        </div>
      </div>
    );
  }

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-8 flex flex-col items-center gap-3 text-center">
        <Loader2 className="w-7 h-7 animate-spin text-primary-500" />
        <p className="text-sm text-gray-500">
          {language === 'ar' ? 'جارٍ تحليل الإعراب…' : 'Analyzing grammar…'}
        </p>
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="p-4 space-y-3" dir="rtl">
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">{language === 'ar' ? 'حدث خطأ' : 'Error'}</p>
            <p className="text-xs text-red-600 mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={loadAnalysis}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-200 hover:bg-gray-50 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          {language === 'ar' ? 'إعادة المحاولة' : 'Try again'}
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  const isUnavailableResult = analysis.source === 'unavailable' || analysis.source === 'error';
  const hasNoTokens = !analysis.tokens || analysis.tokens.length === 0;

  // ── No data available — offer AI analysis ───────────────────────────────────
  if (isUnavailableResult && hasNoTokens) {
    const aiReady = healthStatus?.llm_available;
    return (
      <div className="p-4 space-y-3" dir={language === 'ar' ? 'rtl' : 'ltr'}>
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className={clsx('text-sm font-medium text-amber-800', language === 'ar' && 'font-arabic')}>
              {language === 'ar' ? 'بيانات الإعراب غير متاحة لهذه الآية' : 'Grammar data unavailable for this verse'}
            </p>
            <p className="text-xs text-amber-600 mt-1">
              {language === 'ar'
                ? 'الإعراب الموثق متاح للآيات الأكثر شهرةً.'
                : 'Verified grammar data covers the most common verses.'}
            </p>
          </div>
        </div>
        {aiReady && (
          <button
            onClick={loadAiAnalysis}
            disabled={aiLoading}
            className={clsx(
              'inline-flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-all font-medium',
              aiLoading
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-primary-600 hover:bg-primary-700 text-white shadow-sm',
              language === 'ar' && 'font-arabic',
            )}
          >
            {aiLoading
              ? <><Loader2 className="w-4 h-4 animate-spin" />{language === 'ar' ? 'جارٍ التحليل…' : 'Analyzing…'}</>
              : <><BookOpenCheck className="w-4 h-4" />{language === 'ar' ? 'تحليل بالذكاء الاصطناعي' : 'Analyze with AI'}</>
            }
          </button>
        )}
        {aiLoading && (
          <p className="text-xs text-gray-400">
            {language === 'ar' ? 'قد يستغرق التحليل دقيقة…' : 'Analysis may take a moment…'}
          </p>
        )}
      </div>
    );
  }

  // ── Main analysis display ────────────────────────────────────────────────────
  return (
    <div className="space-y-4" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary-600" />
          <h3 className={clsx('font-semibold text-gray-900', language === 'ar' && 'font-arabic')}>
            {language === 'ar' ? 'الإعراب التفصيلي' : 'Grammatical Analysis'}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {analysis.sentence_type && analysis.sentence_type !== 'غير محدد' && (
            <span className="text-xs px-2 py-0.5 bg-primary-50 text-primary-700 rounded-full border border-primary-200">
              {analysis.sentence_type}
            </span>
          )}
          <SourceBadge source={analysis.source} />
        </div>
      </div>

      {/* Notes */}
      {analysis.notes_ar && !analysis.notes_ar.includes('تعذّر') && (
        <div className="text-sm bg-amber-50 border border-amber-200 rounded-xl p-3 text-right leading-relaxed font-arabic text-amber-900">
          {analysis.notes_ar}
        </div>
      )}

      {/* Token grid */}
      {analysis.tokens.length > 0 ? (
        <>
          <p className="text-xs text-gray-400 text-right">
            {language === 'ar' ? 'اضغط على أي كلمة لتفاصيل إعرابها' : 'Tap any word for detailed analysis'}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {analysis.tokens.map((token, idx) => (
              <TokenCard
                key={idx}
                token={token}
                isExpanded={expandedToken === idx}
                onToggle={() => setExpandedToken(expandedToken === idx ? null : idx)}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-6 text-gray-400">
          <BookOpen className="w-8 h-8 mx-auto text-gray-200 mb-2" />
          <p className="text-sm">{language === 'ar' ? 'لا تتوفر بيانات إعراب' : 'No grammar data available'}</p>
        </div>
      )}

      {/* Color legend toggle */}
      {analysis.tokens.length > 0 && (
        <div>
          <button
            onClick={() => setShowLegend(!showLegend)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
          >
            {showLegend ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            {language === 'ar' ? 'دليل الألوان' : 'Color Legend'}
          </button>
          {showLegend && (
            <div className="mt-2 flex flex-wrap gap-2 p-3 bg-gray-50 rounded-xl border border-gray-100">
              {[
                { label: language === 'ar' ? 'أسماء' : 'Nouns',     style: 'bg-blue-100 text-blue-800' },
                { label: language === 'ar' ? 'أفعال' : 'Verbs',     style: 'bg-green-100 text-green-800' },
                { label: language === 'ar' ? 'حروف' : 'Particles',  style: 'bg-amber-100 text-amber-800' },
                { label: language === 'ar' ? 'غير محدد' : 'Unknown', style: 'bg-gray-100 text-gray-600' },
              ].map(item => (
                <span key={item.label} className={clsx('text-xs px-2.5 py-1 rounded-full', item.style)}>
                  {item.label}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer with source + ref */}
      <div className="flex items-center justify-between text-xs text-gray-400 pt-1 border-t border-gray-100" dir="ltr">
        <span>{analysis.verse_reference}</span>
        {analysis.overall_confidence > 0 && (
          <ConfidenceDot confidence={analysis.overall_confidence} />
        )}
      </div>

      {/* Word Meanings Section */}
      <WordMeaningsSection suraNo={suraNo} ayaNo={ayaNo} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// WordMeaningsSection — معنى الكلمات (QAC + Mufradat Al-Raghib)
// ─────────────────────────────────────────────────────────────────────────────

type MeaningState = 'idle' | 'loading' | 'loaded' | 'empty' | 'error';

function WordMeaningsSection({ suraNo, ayaNo }: { suraNo: number; ayaNo: number }) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [state, setState] = useState<MeaningState>('idle');
  const [words, setWords] = useState<VocabularyResponse[]>([]);
  const [open, setOpen] = useState(false);

  const loadMeanings = useCallback(async () => {
    if (state === 'loading' || state === 'loaded') return;
    setState('loading');
    try {
      const res = await vocabularyApi.verseWords(suraNo, ayaNo);
      const meaningful = res.data.words.filter(w => w.status === 'found');
      setWords(meaningful);
      setState(meaningful.length > 0 ? 'loaded' : 'empty');
    } catch {
      setState('error');
    }
  }, [suraNo, ayaNo, state]);

  const handleToggle = () => {
    if (!open) loadMeanings();
    setOpen(o => !o);
  };

  return (
    <div className="border-t border-gray-100 pt-3 mt-1" dir="rtl">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between text-sm font-medium text-gray-600 hover:text-teal-700 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BookOpenCheck className="w-4 h-4 text-teal-500" />
          <span>{isRtl ? 'معنى الكلمات' : 'Word Meanings'}</span>
          {state === 'loaded' && (
            <span className="text-xs bg-teal-50 text-teal-600 px-1.5 py-0.5 rounded-full">
              {words.length}
            </span>
          )}
        </div>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {open && (
        <div className="mt-3 space-y-2">
          {state === 'loading' && (
            <div className="flex items-center justify-center py-4 gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">{isRtl ? 'جارٍ التحميل…' : 'Loading…'}</span>
            </div>
          )}
          {state === 'error' && (
            <p className="text-sm text-red-400 text-center py-2">
              {isRtl ? 'حدث خطأ في تحميل المعاني.' : 'Failed to load word meanings.'}
            </p>
          )}
          {state === 'empty' && (
            <div className="text-center py-3 text-gray-400">
              <p className="text-sm">{isRtl ? 'لا تتوفر معاني في قاعدة البيانات حالياً.' : 'No word meanings in database yet.'}</p>
            </div>
          )}
          {state === 'loaded' && words.length > 0 && (
            <>
              <div className="flex flex-wrap gap-2">
                {words.map((w, i) => <WordMeaningCard key={i} word={w} isRtl={isRtl} />)}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-400 pt-1" dir="ltr">
                <BookOpen className="w-3.5 h-3.5 shrink-0" />
                Quranic Arabic Corpus · Mufradat Al-Raghib Al-Isfahani (d. 502 AH)
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function WordMeaningCard({ word }: { word: VocabularyResponse; isRtl: boolean }) {
  const hasMeaningAr = Boolean(word.meaning_ar);
  const hasMeaningEn = Boolean(word.meaning_en);

  return (
    <div
      dir="rtl"
      className="flex-shrink-0 rounded-xl border px-3 py-2 min-w-[7rem] max-w-[14rem] bg-gradient-to-br from-teal-50 to-white border-teal-100 text-right"
    >
      <div className="font-arabic text-base font-bold text-teal-900 leading-snug mb-1">{word.word}</div>
      {hasMeaningAr && (
        <p className="text-xs text-gray-700 font-arabic leading-relaxed">{word.meaning_ar}</p>
      )}
      {hasMeaningEn && (
        <p dir="ltr" className={clsx('text-xs leading-snug', hasMeaningAr ? 'text-gray-400 mt-0.5' : 'text-gray-600 font-medium')}>
          {word.meaning_en}
        </p>
      )}
      {(word.root || word.pos_tag) && (
        <div className="flex flex-wrap gap-1 mt-1.5" dir="rtl">
          {word.root && <span className="text-xs bg-teal-100 text-teal-700 px-1.5 py-0.5 rounded font-arabic">{word.root}</span>}
          {word.pos_tag && <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded font-arabic">{word.pos_tag}</span>}
        </div>
      )}
    </div>
  );
}

export default GrammarAnalysisView;
