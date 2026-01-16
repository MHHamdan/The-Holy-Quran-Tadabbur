/**
 * Similar Verses Panel Component
 *
 * Displays advanced similarity search results with:
 * - Visual grouping by theme/connection type
 * - Color-coded theme badges
 * - Multi-layered score breakdown (Jaccard, Cosine, Concept Overlap, etc.)
 * - Connection strength indicators
 * - Arabic sentence structure analysis
 */
import { useState, useEffect, useMemo } from 'react';
import {
  GitBranch,
  Layers,
  Filter,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  BookOpen,
  BarChart3,
  Tag,
  RefreshCw,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import {
  quranApi,
  AdvancedSimilarityResponse,
  AdvancedSimilarityMatch,
  SimilarityScores,
} from '../../lib/api';
import clsx from 'clsx';

interface Props {
  suraNo: number;
  ayaNo: number;
  verseText?: string;
  onVerseSelect?: (suraNo: number, ayaNo: number) => void;
}

// Connection type colors and labels
const CONNECTION_TYPES: Record<string, { color: string; label_ar: string; label_en: string }> = {
  lexical: { color: 'bg-blue-100 text-blue-700 border-blue-200', label_ar: 'لفظي', label_en: 'Lexical' },
  thematic: { color: 'bg-purple-100 text-purple-700 border-purple-200', label_ar: 'موضوعي', label_en: 'Thematic' },
  conceptual: { color: 'bg-indigo-100 text-indigo-700 border-indigo-200', label_ar: 'مفاهيمي', label_en: 'Conceptual' },
  grammatical: { color: 'bg-green-100 text-green-700 border-green-200', label_ar: 'نحوي', label_en: 'Grammatical' },
  semantic: { color: 'bg-amber-100 text-amber-700 border-amber-200', label_ar: 'دلالي', label_en: 'Semantic' },
  root_based: { color: 'bg-teal-100 text-teal-700 border-teal-200', label_ar: 'جذري', label_en: 'Root-Based' },
};

// Theme colors mapping
const THEME_COLORS: Record<string, string> = {
  '#4f46e5': 'bg-indigo-500', // tawheed
  '#059669': 'bg-emerald-500', // mercy
  '#dc2626': 'bg-red-500', // warning
  '#7c3aed': 'bg-violet-500', // guidance
  '#ea580c': 'bg-orange-500', // nature
  '#0891b2': 'bg-cyan-500', // patience
  '#84cc16': 'bg-lime-500', // gratitude
  '#f59e0b': 'bg-amber-500', // justice
  '#64748b': 'bg-slate-500', // default
};

// Sentence structure translations
const SENTENCE_STRUCTURES: Record<string, { ar: string; en: string }> = {
  verbal: { ar: 'جملة فعلية', en: 'Verbal Sentence' },
  nominal: { ar: 'جملة اسمية', en: 'Nominal Sentence' },
  conditional: { ar: 'جملة شرطية', en: 'Conditional Sentence' },
  interrogative: { ar: 'جملة استفهامية', en: 'Interrogative Sentence' },
  imperative: { ar: 'جملة أمرية', en: 'Imperative Sentence' },
  prohibitive: { ar: 'جملة نهيية', en: 'Prohibitive Sentence' },
  exclamatory: { ar: 'جملة تعجبية', en: 'Exclamatory Sentence' },
  oath: { ar: 'جملة قسمية', en: 'Oath Sentence' },
  vocative: { ar: 'جملة ندائية', en: 'Vocative Sentence' },
  negation: { ar: 'جملة نفيية', en: 'Negation Sentence' },
  unknown: { ar: 'غير محدد', en: 'Unknown' },
};

// Score metric labels
const SCORE_LABELS: Record<keyof Omit<SimilarityScores, 'combined'>, { ar: string; en: string; color: string }> = {
  jaccard: { ar: 'جاكارد', en: 'Jaccard', color: 'bg-blue-500' },
  cosine: { ar: 'كوساين', en: 'Cosine', color: 'bg-green-500' },
  concept_overlap: { ar: 'تداخل المفاهيم', en: 'Concept Overlap', color: 'bg-purple-500' },
  grammatical: { ar: 'نحوي', en: 'Grammatical', color: 'bg-amber-500' },
  semantic: { ar: 'دلالي', en: 'Semantic', color: 'bg-indigo-500' },
  root_based: { ar: 'جذري', en: 'Root-Based', color: 'bg-teal-500' },
};

// Connection strength badge
function ConnectionStrengthBadge({ strength, language }: { strength: string; language: 'ar' | 'en' }) {
  const colors: Record<string, string> = {
    strong: 'bg-green-100 text-green-700',
    moderate: 'bg-yellow-100 text-yellow-700',
    weak: 'bg-gray-100 text-gray-600',
  };
  const labels: Record<string, { ar: string; en: string }> = {
    strong: { ar: 'قوي', en: 'Strong' },
    moderate: { ar: 'متوسط', en: 'Moderate' },
    weak: { ar: 'ضعيف', en: 'Weak' },
  };
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded-full', colors[strength] || colors.weak)}>
      {labels[strength]?.[language] || strength}
    </span>
  );
}

// Score breakdown visualization
function ScoreBreakdown({ scores, expanded, language }: { scores: SimilarityScores; expanded: boolean; language: 'ar' | 'en' }) {
  if (!expanded) return null;

  const metrics = Object.entries(SCORE_LABELS) as [keyof Omit<SimilarityScores, 'combined'>, typeof SCORE_LABELS[keyof typeof SCORE_LABELS]][];

  return (
    <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
      <div className="text-xs font-medium text-gray-500 mb-2">
        {language === 'ar' ? 'تفصيل درجات التشابه:' : 'Similarity Scores Breakdown:'}
      </div>
      {metrics.map(([key, meta]) => {
        const value = scores[key];
        const percent = Math.round(value * 100);
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="text-xs text-gray-600 w-24 truncate" title={meta[language]}>
              {meta[language]}
            </span>
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', meta.color)}
                style={{ width: `${percent}%` }}
              />
            </div>
            <span className="text-xs text-gray-500 w-10 text-right">{percent}%</span>
          </div>
        );
      })}
      <div className="flex items-center gap-2 pt-1 border-t border-gray-100">
        <span className="text-xs font-semibold text-gray-700 w-24">
          {language === 'ar' ? 'المجموع' : 'Combined'}
        </span>
        <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-primary-600 transition-all"
            style={{ width: `${Math.round(scores.combined * 100)}%` }}
          />
        </div>
        <span className="text-xs font-semibold text-primary-700 w-10 text-right">
          {Math.round(scores.combined * 100)}%
        </span>
      </div>
    </div>
  );
}

// Theme badge component
function ThemeBadge({ theme, color, language }: { theme: string; color: string; language: 'ar' | 'en' }) {
  const bgClass = THEME_COLORS[color] || 'bg-slate-500';
  // Simple theme translations
  const themeTranslations: Record<string, { ar: string; en: string }> = {
    tawheed: { ar: 'التوحيد', en: 'Monotheism' },
    mercy: { ar: 'الرحمة', en: 'Mercy' },
    guidance: { ar: 'الهداية', en: 'Guidance' },
    warning: { ar: 'التحذير', en: 'Warning' },
    patience: { ar: 'الصبر', en: 'Patience' },
    gratitude: { ar: 'الشكر', en: 'Gratitude' },
    justice: { ar: 'العدل', en: 'Justice' },
    nature: { ar: 'الطبيعة', en: 'Nature' },
  };

  const label = themeTranslations[theme]?.[language] || theme;

  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded-full text-white', bgClass)}>
      {label}
    </span>
  );
}

// Single match card
function MatchCard({
  match,
  isExpanded,
  onToggle,
  onSelect,
  language,
}: {
  match: AdvancedSimilarityMatch;
  isExpanded: boolean;
  onToggle: () => void;
  onSelect?: (suraNo: number, ayaNo: number) => void;
  language: 'ar' | 'en';
}) {
  const connectionType = CONNECTION_TYPES[match.connection_type] || CONNECTION_TYPES.semantic;
  const sentenceStructure = SENTENCE_STRUCTURES[match.sentence_structure] || SENTENCE_STRUCTURES.unknown;

  const handleClick = () => {
    if (onSelect) {
      onSelect(match.sura_no, match.aya_no);
    }
  };

  return (
    <div
      className={clsx(
        'border rounded-lg overflow-hidden transition-all',
        isExpanded ? 'ring-2 ring-primary-400 border-primary-300' : 'border-gray-200 hover:border-gray-300'
      )}
    >
      {/* Header with reference and scores */}
      <div
        className="p-3 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            {/* Reference and connection type */}
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span
                className="font-semibold text-primary-700 hover:underline cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClick();
                }}
              >
                {match.reference}
              </span>
              <span className={clsx('text-xs px-2 py-0.5 rounded border', connectionType.color)}>
                {connectionType[`label_${language}`]}
              </span>
              <ConnectionStrengthBadge strength={match.connection_strength} language={language} />
            </div>

            {/* Sura name */}
            <div className="text-sm text-gray-500">
              {language === 'ar' ? match.sura_name_ar : match.sura_name_en}
            </div>
          </div>

          {/* Combined score */}
          <div className="flex items-center gap-2">
            <div className="text-center">
              <div className="text-lg font-bold text-primary-600">
                {Math.round(match.scores.combined * 100)}%
              </div>
              <div className="text-xs text-gray-400">
                {language === 'ar' ? 'تشابه' : 'similarity'}
              </div>
            </div>
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Verse text (always visible) */}
      <div
        className="px-3 pb-3 text-right font-arabic leading-relaxed cursor-pointer hover:text-primary-700"
        dir="rtl"
        onClick={handleClick}
      >
        {match.text_uthmani}
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-100 bg-gray-50/50 p-3 space-y-3">
          {/* Themes */}
          {match.shared_themes && match.shared_themes.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <Tag className="w-4 h-4 text-gray-400" />
              {match.shared_themes.map((theme) => (
                <ThemeBadge
                  key={theme}
                  theme={theme}
                  color={match.theme_color}
                  language={language}
                />
              ))}
            </div>
          )}

          {/* Shared words and roots */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            {match.shared_words && match.shared_words.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-1">
                  {language === 'ar' ? 'كلمات مشتركة:' : 'Shared Words:'}
                </div>
                <div className="flex flex-wrap gap-1" dir="rtl">
                  {match.shared_words.slice(0, 5).map((word, i) => (
                    <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                      {word}
                    </span>
                  ))}
                  {match.shared_words.length > 5 && (
                    <span className="text-xs text-gray-400">+{match.shared_words.length - 5}</span>
                  )}
                </div>
              </div>
            )}

            {match.shared_roots && match.shared_roots.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-1">
                  {language === 'ar' ? 'جذور مشتركة:' : 'Shared Roots:'}
                </div>
                <div className="flex flex-wrap gap-1" dir="rtl">
                  {match.shared_roots.slice(0, 5).map((root, i) => (
                    <span key={i} className="text-xs bg-teal-50 text-teal-700 px-2 py-0.5 rounded">
                      {root}
                    </span>
                  ))}
                  {match.shared_roots.length > 5 && (
                    <span className="text-xs text-gray-400">+{match.shared_roots.length - 5}</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sentence structure */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">
              {language === 'ar' ? 'نوع الجملة:' : 'Sentence Type:'}
            </span>
            <span className="text-gray-700 font-medium">
              {sentenceStructure[language]}
            </span>
          </div>

          {/* Similarity explanation */}
          {(match.similarity_explanation_ar || match.similarity_explanation_en) && (
            <div className="text-sm text-gray-600 bg-white/50 rounded p-2" dir={language === 'ar' ? 'rtl' : 'ltr'}>
              {language === 'ar' ? match.similarity_explanation_ar : match.similarity_explanation_en}
            </div>
          )}

          {/* Score breakdown */}
          <ScoreBreakdown scores={match.scores} expanded={true} language={language} />
        </div>
      )}
    </div>
  );
}

// Group header for visual grouping
function GroupHeader({ title, count, color }: { title: string; count: number; color: string }) {
  return (
    <div className="flex items-center gap-2 py-2">
      <div className={clsx('w-3 h-3 rounded-full', color)} />
      <h4 className="font-semibold text-gray-700">{title}</h4>
      <span className="text-sm text-gray-400">({count})</span>
    </div>
  );
}

// Filter panel
function FilterPanel({
  themes,
  connectionTypes,
  selectedTheme,
  selectedConnectionType,
  excludeSameSura,
  onThemeChange,
  onConnectionTypeChange,
  onExcludeSameSuraChange,
  language,
}: {
  themes: string[];
  connectionTypes: { id: string; name_en: string; name_ar: string; color: string }[];
  selectedTheme: string | null;
  selectedConnectionType: string | null;
  excludeSameSura: boolean;
  onThemeChange: (theme: string | null) => void;
  onConnectionTypeChange: (type: string | null) => void;
  onExcludeSameSuraChange: (exclude: boolean) => void;
  language: 'ar' | 'en';
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
        <Filter className="w-4 h-4" />
        {language === 'ar' ? 'تصفية النتائج' : 'Filter Results'}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Theme filter */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">
            {language === 'ar' ? 'الموضوع' : 'Theme'}
          </label>
          <select
            value={selectedTheme || ''}
            onChange={(e) => onThemeChange(e.target.value || null)}
            className="w-full text-sm border-gray-200 rounded-md"
          >
            <option value="">{language === 'ar' ? 'الكل' : 'All'}</option>
            {themes.map((theme) => (
              <option key={theme} value={theme}>
                {theme}
              </option>
            ))}
          </select>
        </div>

        {/* Connection type filter */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">
            {language === 'ar' ? 'نوع الاتصال' : 'Connection Type'}
          </label>
          <select
            value={selectedConnectionType || ''}
            onChange={(e) => onConnectionTypeChange(e.target.value || null)}
            className="w-full text-sm border-gray-200 rounded-md"
          >
            <option value="">{language === 'ar' ? 'الكل' : 'All'}</option>
            {connectionTypes.map((ct) => (
              <option key={ct.id} value={ct.id}>
                {language === 'ar' ? ct.name_ar : ct.name_en}
              </option>
            ))}
          </select>
        </div>

        {/* Exclude same sura */}
        <div className="flex items-end">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={excludeSameSura}
              onChange={(e) => onExcludeSameSuraChange(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            {language === 'ar' ? 'استثناء نفس السورة' : 'Exclude same Sura'}
          </label>
        </div>
      </div>
    </div>
  );
}

// Main component
export function SimilarVersesPanel({ suraNo, ayaNo, verseText, onVerseSelect }: Props) {
  const { language } = useLanguageStore();
  const [data, setData] = useState<AdvancedSimilarityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedMatch, setExpandedMatch] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [groupBy, setGroupBy] = useState<'none' | 'theme' | 'connection'>('none');

  // Filters
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [selectedConnectionType, setSelectedConnectionType] = useState<string | null>(null);
  const [excludeSameSura, setExcludeSameSura] = useState(false);

  const isArabic = language === 'ar';

  async function loadSimilarVerses() {
    setLoading(true);
    setError(null);
    try {
      const response = await quranApi.getAdvancedSimilarity(suraNo, ayaNo, {
        top_k: 50,
        min_score: 0.2,
        theme: selectedTheme || undefined,
        exclude_same_sura: excludeSameSura,
        connection_type: selectedConnectionType || undefined,
      });
      setData(response.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(isArabic ? 'تعذّر تحميل الآيات المتشابهة' : 'Failed to load similar verses');
      console.error('Similar verses error:', message);
    } finally {
      setLoading(false);
    }
  }

  // Reload when filters change
  useEffect(() => {
    if (data) {
      loadSimilarVerses();
    }
  }, [selectedTheme, selectedConnectionType, excludeSameSura]);

  // Group matches by theme or connection type
  const groupedMatches = useMemo(() => {
    if (!data?.matches) return new Map<string, AdvancedSimilarityMatch[]>();

    const matches = data.matches;
    if (groupBy === 'none') {
      return new Map([['all', matches]]);
    }

    const groups = new Map<string, AdvancedSimilarityMatch[]>();
    matches.forEach((match) => {
      const key = groupBy === 'theme' ? (match.primary_theme || 'other') : match.connection_type;
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(match);
    });

    return groups;
  }, [data?.matches, groupBy]);

  // Get available themes and connection types for filters
  const availableThemes = useMemo(() => {
    if (!data?.theme_distribution) return [];
    return Object.keys(data.theme_distribution);
  }, [data?.theme_distribution]);

  const connectionTypesList = data?.connection_types || [];

  // Initial load button
  if (!data && !loading && !error) {
    return (
      <div className="card p-4 text-center">
        <button
          onClick={loadSimilarVerses}
          className="btn btn-primary inline-flex items-center gap-2"
        >
          <GitBranch className="w-4 h-4" />
          {isArabic ? 'البحث عن آيات متشابهة' : 'Find Similar Verses'}
        </button>
        <p className="text-sm text-gray-500 mt-2">
          {isArabic
            ? 'اكتشف الآيات ذات الصلة باستخدام تحليل التشابه المتقدم'
            : 'Discover related verses using advanced similarity analysis'}
        </p>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="card p-8 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        <p className="mt-2 text-sm text-gray-600">
          {isArabic ? 'جارٍ البحث عن الآيات المتشابهة...' : 'Finding similar verses...'}
        </p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="card p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadSimilarVerses}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              {isArabic ? 'إعادة المحاولة' : 'Try again'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="card space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold">
            {isArabic ? 'الآيات المتشابهة' : 'Similar Verses'}
          </h3>
          <span className="text-sm text-gray-500">({data.total_similar})</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={clsx(
              'btn btn-sm',
              showFilters ? 'btn-primary' : 'btn-ghost'
            )}
          >
            <Filter className="w-4 h-4" />
          </button>
          <button
            onClick={loadSimilarVerses}
            className="btn btn-sm btn-ghost"
            title={isArabic ? 'تحديث' : 'Refresh'}
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Source verse info */}
      <div className="bg-primary-50 rounded-lg p-3" dir="rtl">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="w-4 h-4 text-primary-600" />
          <span className="text-sm font-medium text-primary-700">
            {data.source_verse.reference} - {isArabic ? data.source_verse.sura_name_ar : data.source_verse.sura_name_en}
          </span>
        </div>
        <p className="font-arabic text-lg leading-relaxed text-gray-800">
          {verseText || data.source_verse.text_uthmani}
        </p>
        {data.source_themes && data.source_themes.length > 0 && (
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <Tag className="w-3 h-3 text-primary-500" />
            {data.source_themes.map((theme) => (
              <span key={theme} className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">
                {theme}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <FilterPanel
          themes={availableThemes}
          connectionTypes={connectionTypesList}
          selectedTheme={selectedTheme}
          selectedConnectionType={selectedConnectionType}
          excludeSameSura={excludeSameSura}
          onThemeChange={setSelectedTheme}
          onConnectionTypeChange={setSelectedConnectionType}
          onExcludeSameSuraChange={setExcludeSameSura}
          language={language}
        />
      )}

      {/* Grouping options */}
      <div className="flex items-center gap-2 text-sm">
        <Layers className="w-4 h-4 text-gray-400" />
        <span className="text-gray-600">
          {isArabic ? 'تجميع حسب:' : 'Group by:'}
        </span>
        <select
          value={groupBy}
          onChange={(e) => setGroupBy(e.target.value as 'none' | 'theme' | 'connection')}
          className="text-sm border-gray-200 rounded-md"
        >
          <option value="none">{isArabic ? 'بدون تجميع' : 'No grouping'}</option>
          <option value="theme">{isArabic ? 'الموضوع' : 'Theme'}</option>
          <option value="connection">{isArabic ? 'نوع الاتصال' : 'Connection Type'}</option>
        </select>
      </div>

      {/* Distribution charts */}
      {data.theme_distribution && Object.keys(data.theme_distribution).length > 0 && (
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <BarChart3 className="w-4 h-4" />
            {isArabic ? 'توزيع المواضيع' : 'Theme Distribution'}
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.theme_distribution).slice(0, 8).map(([theme, count]) => (
              <span
                key={theme}
                className="text-xs bg-white border border-gray-200 rounded px-2 py-1"
              >
                {theme}: <strong>{count}</strong>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      <div className="space-y-4">
        {Array.from(groupedMatches.entries()).map(([group, matches]) => (
          <div key={group}>
            {group !== 'all' && (
              <GroupHeader
                title={
                  groupBy === 'theme'
                    ? group
                    : CONNECTION_TYPES[group]?.[`label_${language}`] || group
                }
                count={matches.length}
                color={
                  groupBy === 'connection'
                    ? (CONNECTION_TYPES[group]?.color.split(' ')[0] || 'bg-gray-500')
                    : 'bg-primary-500'
                }
              />
            )}
            <div className="space-y-3">
              {matches.map((match) => (
                <MatchCard
                  key={`${match.sura_no}-${match.aya_no}`}
                  match={match}
                  isExpanded={expandedMatch === (match.sura_no * 1000 + match.aya_no)}
                  onToggle={() =>
                    setExpandedMatch(
                      expandedMatch === (match.sura_no * 1000 + match.aya_no)
                        ? null
                        : match.sura_no * 1000 + match.aya_no
                    )
                  }
                  onSelect={onVerseSelect}
                  language={language}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* No results */}
      {data.matches.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <GitBranch className="w-12 h-12 mx-auto text-gray-300 mb-2" />
          <p>
            {isArabic
              ? 'لم يتم العثور على آيات متشابهة بالمعايير المحددة'
              : 'No similar verses found with the selected criteria'}
          </p>
        </div>
      )}

      {/* Footer with timing info */}
      <div className="text-xs text-gray-400 flex items-center justify-between pt-2 border-t border-gray-100">
        <span>
          {isArabic ? 'وقت البحث:' : 'Search time:'} {data.search_time_ms}ms
        </span>
        <span>
          {data.source_structure && (
            <>
              {isArabic ? 'نوع الجملة المصدر:' : 'Source sentence type:'}{' '}
              {SENTENCE_STRUCTURES[data.source_structure]?.[language] || data.source_structure}
            </>
          )}
        </span>
      </div>
    </div>
  );
}

export default SimilarVersesPanel;
