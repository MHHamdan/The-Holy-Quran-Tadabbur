/**
 * Arabic Grammar Analysis (إعراب) Component
 *
 * Displays word-by-word grammatical analysis with:
 * - Part of speech (pos) with color coding
 * - Grammatical role (role)
 * - Full إعراب explanation on hover
 * - Confidence indicator
 * - Health status awareness (shows warning when degraded)
 */
import { useState, useEffect } from 'react';
import { BookOpen, AlertCircle, ChevronDown, ChevronUp, Loader2, AlertTriangle, Info } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { grammarApi, GrammarAnalysis as GrammarAnalysisType, GrammarToken, GrammarHealth } from '../../lib/api';
import clsx from 'clsx';

interface Props {
  suraNo: number;
  ayaNo: number;
  verseText?: string;
}

// Color mapping for parts of speech
const POS_COLORS: Record<string, string> = {
  // Nouns - blue shades
  'اسم': 'bg-blue-100 text-blue-800 border-blue-200',
  'اسم علم': 'bg-blue-200 text-blue-900 border-blue-300',
  'ضمير': 'bg-sky-100 text-sky-800 border-sky-200',
  'اسم إشارة': 'bg-cyan-100 text-cyan-800 border-cyan-200',
  'اسم موصول': 'bg-teal-100 text-teal-800 border-teal-200',
  'اسم استفهام': 'bg-indigo-100 text-indigo-800 border-indigo-200',
  'مصدر': 'bg-violet-100 text-violet-800 border-violet-200',
  // Verbs - green shades
  'فعل': 'bg-green-100 text-green-800 border-green-200',
  'فعل ماض': 'bg-green-200 text-green-900 border-green-300',
  'فعل مضارع': 'bg-emerald-100 text-emerald-800 border-emerald-200',
  'فعل أمر': 'bg-lime-100 text-lime-800 border-lime-200',
  // Particles - amber/orange shades
  'حرف': 'bg-amber-100 text-amber-800 border-amber-200',
  'حرف جر': 'bg-orange-100 text-orange-800 border-orange-200',
  'حرف عطف': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'حرف نفي': 'bg-red-100 text-red-800 border-red-200',
  'حرف استفهام': 'bg-rose-100 text-rose-800 border-rose-200',
  'حرف شرط': 'bg-pink-100 text-pink-800 border-pink-200',
  'حرف استثناء': 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200',
  // Unknown
  'غير محدد': 'bg-gray-100 text-gray-600 border-gray-200',
};

// Role badge colors
const ROLE_COLORS: Record<string, string> = {
  'مبتدأ': 'text-blue-700',
  'خبر': 'text-blue-600',
  'فاعل': 'text-green-700',
  'نائب فاعل': 'text-green-600',
  'مفعول به': 'text-purple-700',
  'مفعول لأجله': 'text-purple-600',
  'مفعول فيه': 'text-purple-500',
  'مفعول مطلق': 'text-purple-600',
  'مفعول معه': 'text-purple-500',
  'حال': 'text-orange-600',
  'تمييز': 'text-orange-500',
  'مستثنى': 'text-red-600',
  'مضاف': 'text-teal-600',
  'مضاف إليه': 'text-teal-700',
  'جار ومجرور': 'text-amber-600',
  'مجرور': 'text-amber-700',
  'نعت': 'text-cyan-600',
  'منعوت': 'text-cyan-700',
  'بدل': 'text-indigo-600',
  'معطوف': 'text-violet-600',
  'معطوف عليه': 'text-violet-700',
  'توكيد': 'text-pink-600',
  'منادى': 'text-rose-600',
  'خبر كان': 'text-blue-500',
  'اسم إن': 'text-blue-600',
  'خبر إن': 'text-blue-500',
  'غير محدد': 'text-gray-500',
};

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100);
  const color = confidence >= 0.8 ? 'text-green-600' : confidence >= 0.5 ? 'text-yellow-600' : 'text-red-600';
  return (
    <span className={clsx('text-xs', color)}>
      {percent}%
    </span>
  );
}

function TokenCard({ token, isExpanded, onToggle }: { token: GrammarToken; isExpanded: boolean; onToggle: () => void }) {
  const posColor = POS_COLORS[token.pos] || POS_COLORS['غير محدد'];
  const roleColor = ROLE_COLORS[token.role] || ROLE_COLORS['غير محدد'];

  return (
    <div
      className={clsx(
        'border rounded-lg overflow-hidden transition-all cursor-pointer',
        posColor,
        isExpanded && 'ring-2 ring-primary-400'
      )}
      onClick={onToggle}
    >
      {/* Word and basic info */}
      <div className="p-3">
        <div className="text-center">
          <span className="text-xl font-arabic font-bold">{token.word}</span>
        </div>
        <div className="mt-2 space-y-1 text-center">
          <div className="text-xs font-medium">{token.pos}</div>
          <div className={clsx('text-sm font-semibold', roleColor)}>{token.role}</div>
          <ConfidenceBadge confidence={token.confidence} />
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="border-t border-current/10 p-3 bg-white/50 space-y-2 text-right" dir="rtl">
          <div className="text-sm font-arabic leading-relaxed">
            <span className="font-semibold">الإعراب:</span> {token.i3rab || 'غير متوفر'}
          </div>
          {token.root && (
            <div className="text-xs">
              <span className="font-semibold">الجذر:</span> {token.root}
            </div>
          )}
          {token.pattern && (
            <div className="text-xs">
              <span className="font-semibold">الوزن:</span> {token.pattern}
            </div>
          )}
          {token.case_ending && (
            <div className="text-xs">
              <span className="font-semibold">علامة الإعراب:</span> {token.case_ending}
            </div>
          )}
          {token.notes_ar && (
            <div className="text-xs text-gray-600 italic">
              {token.notes_ar}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Legend() {
  const { language } = useLanguageStore();

  return (
    <div className="text-xs space-y-2 p-3 bg-gray-50 rounded-lg" dir="rtl">
      <div className="font-semibold text-gray-700">
        {language === 'ar' ? 'دليل الألوان:' : 'Color Legend:'}
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800">
          {language === 'ar' ? 'أسماء' : 'Nouns'}
        </span>
        <span className="px-2 py-0.5 rounded bg-green-100 text-green-800">
          {language === 'ar' ? 'أفعال' : 'Verbs'}
        </span>
        <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800">
          {language === 'ar' ? 'حروف' : 'Particles'}
        </span>
        <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-600">
          {language === 'ar' ? 'غير محدد' : 'Unknown'}
        </span>
      </div>
    </div>
  );
}

export function GrammarAnalysisView({ suraNo, ayaNo, verseText }: Props) {
  const { language } = useLanguageStore();
  const [analysis, setAnalysis] = useState<GrammarAnalysisType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedToken, setExpandedToken] = useState<number | null>(null);
  const [showLegend, setShowLegend] = useState(false);
  const [healthStatus, setHealthStatus] = useState<GrammarHealth | null>(null);
  const [_checkingHealth, _setCheckingHealth] = useState(false);

  // Check grammar service health on mount
  useEffect(() => {
    async function checkHealth() {
      try {
        const result = await grammarApi.health();
        setHealthStatus(result.data);
      } catch {
        // Ignore health check errors
      }
    }
    checkHealth();
  }, []);

  async function loadAnalysis() {
    setLoading(true);
    setError(null);
    try {
      const verseRef = `${suraNo}:${ayaNo}`;
      let result;

      // If we have verse text, analyze it directly
      if (verseText) {
        result = await grammarApi.analyzeText(verseText, verseRef);
      } else {
        // Otherwise use the ayah endpoint
        result = await grammarApi.analyzeAyah(verseRef);
      }

      setAnalysis(result.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(language === 'ar'
        ? 'تعذّر تحميل الإعراب. يُرجى المحاولة لاحقاً.'
        : 'Failed to load grammar analysis. Please try again later.'
      );
      console.error('Grammar analysis error:', message);
    } finally {
      setLoading(false);
    }
  }

  // If not loaded yet, show load button
  if (!analysis && !loading && !error) {
    const isUnavailable = healthStatus?.status === 'unavailable';
    const isStaticOnly = healthStatus?.status === 'static_only';

    return (
      <div className="p-4 text-center space-y-3">
        {/* Health status warning */}
        {isUnavailable && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2 text-left" dir={language === 'ar' ? 'rtl' : 'ltr'}>
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="text-amber-800 font-medium">
                {language === 'ar' ? healthStatus?.message_ar : healthStatus?.message_en}
              </p>
            </div>
          </div>
        )}
        {isStaticOnly && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2 text-left" dir={language === 'ar' ? 'rtl' : 'ltr'}>
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="text-blue-800">
                {language === 'ar' ? healthStatus?.message_ar : healthStatus?.message_en}
              </p>
            </div>
          </div>
        )}

        <button
          onClick={loadAnalysis}
          disabled={isUnavailable}
          className={clsx(
            "btn inline-flex items-center gap-2",
            isUnavailable ? "btn-ghost cursor-not-allowed opacity-50" : "btn-primary"
          )}
        >
          <BookOpen className="w-4 h-4" />
          {language === 'ar' ? 'تحليل إعراب الآية' : 'Analyze Grammar'}
        </button>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        <p className="mt-2 text-sm text-gray-600">
          {language === 'ar' ? 'جارٍ التحليل النحوي...' : 'Analyzing grammar...'}
        </p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-4" dir="rtl">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">
              {language === 'ar' ? 'حدث خطأ' : 'Error'}
            </p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={loadAnalysis}
              className="mt-3 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-800 rounded-lg transition-colors font-medium text-sm"
            >
              {language === 'ar' ? 'إعادة المحاولة' : 'Try again'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  // Check if analysis has no meaningful data (unavailable/error source)
  const isUnavailableResult = analysis.source === 'unavailable' || analysis.source === 'error';
  const hasNoTokens = !analysis.tokens || analysis.tokens.length === 0;

  // Show warning for unavailable/error results with no tokens
  if (isUnavailableResult && hasNoTokens) {
    return (
      <div className="space-y-4" dir="rtl">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-amber-800 font-medium">
              {language === 'ar' ? 'خدمة الإعراب غير متاحة' : 'Grammar service unavailable'}
            </p>
            <p className="text-sm text-amber-700 mt-1">
              {language === 'ar'
                ? 'خدمة التحليل النحوي غير متاحة حالياً. يُرجى المحاولة لاحقاً.'
                : 'The grammar analysis service is currently unavailable. Please try again later.'}
            </p>
            <button
              onClick={loadAnalysis}
              className="mt-3 px-4 py-2 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-lg transition-colors font-medium text-sm"
            >
              {language === 'ar' ? 'إعادة المحاولة' : 'Try again'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Source badge color
  const sourceColors: Record<string, string> = {
    llm: 'bg-green-100 text-green-700',
    static: 'bg-blue-100 text-blue-700',
    hybrid: 'bg-purple-100 text-purple-700',
    fallback: 'bg-gray-100 text-gray-600',
  };

  const sourceLabels: Record<string, { ar: string; en: string }> = {
    llm: { ar: 'تحليل ذكي', en: 'AI Analysis' },
    static: { ar: 'بيانات ثابتة', en: 'Static Data' },
    hybrid: { ar: 'مختلط', en: 'Hybrid' },
    fallback: { ar: 'احتياطي', en: 'Fallback' },
  };

  return (
    <div className="space-y-4" dir="rtl">
      {/* Header with sentence type */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">
            {language === 'ar' ? 'إعراب الآية' : 'Grammatical Analysis'}
          </h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm px-2 py-1 bg-primary-100 text-primary-700 rounded">
            {analysis.sentence_type}
          </span>
          {analysis.overall_confidence > 0 && (
            <ConfidenceBadge confidence={analysis.overall_confidence} />
          )}
        </div>
      </div>

      {/* Static data notice */}
      {analysis.source === 'static' && (
        <div className="text-sm bg-blue-50 border border-blue-200 rounded-lg p-2 flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-600" />
          <span className="text-blue-700">
            {language === 'ar'
              ? 'تم استخدام البيانات المحفوظة مسبقاً'
              : 'Using pre-analyzed static data'}
          </span>
        </div>
      )}

      {/* Token grid */}
      {analysis.tokens.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {analysis.tokens.map((token, idx) => (
            <TokenCard
              key={idx}
              token={token}
              isExpanded={expandedToken === idx}
              onToggle={() => setExpandedToken(expandedToken === idx ? null : idx)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-6 text-gray-500">
          <BookOpen className="w-8 h-8 mx-auto text-gray-300 mb-2" />
          <p className="font-medium">
            {language === 'ar' ? 'لا تتوفر بيانات إعراب لهذه الآية' : 'No grammar analysis available for this verse'}
          </p>
        </div>
      )}

      {/* Notes */}
      {analysis.notes_ar && (
        <div className="text-sm bg-amber-50 border border-amber-200 rounded-lg p-3">
          <span className="font-semibold">ملاحظات:</span> {analysis.notes_ar}
        </div>
      )}

      {/* Legend toggle */}
      {analysis.tokens.length > 0 && (
        <div>
          <button
            onClick={() => setShowLegend(!showLegend)}
            className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
          >
            {showLegend ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            {language === 'ar' ? 'دليل الألوان' : 'Color Legend'}
          </button>
          {showLegend && <Legend />}
        </div>
      )}

      {/* Source indicator */}
      <div className="text-xs text-gray-500 flex items-center justify-between">
        <span className={clsx('px-2 py-0.5 rounded', sourceColors[analysis.source] || 'bg-gray-100')}>
          {sourceLabels[analysis.source]?.[language] || analysis.source}
        </span>
        <span>
          {analysis.verse_reference}
        </span>
      </div>
    </div>
  );
}

export default GrammarAnalysisView;
