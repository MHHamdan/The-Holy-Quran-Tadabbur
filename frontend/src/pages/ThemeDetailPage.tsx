import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BookOpen, ArrowLeft, Tag, Layers, BookMarked, CheckCircle,
  AlertCircle, ChevronRight, ExternalLink, Moon, Sun, Filter,
  BarChart3, HelpCircle, X
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { themesApi, quranApi, ThemeDetail, ThemeSegment, ThemeConsequence, QuranicTheme, ThemeCoverage, SegmentEvidence, Verse } from '../lib/api';
import clsx from 'clsx';

// Sura names mapping (Arabic)
const SURA_NAMES_AR: Record<number, string> = {
  1: 'الفاتحة', 2: 'البقرة', 3: 'آل عمران', 4: 'النساء', 5: 'المائدة',
  6: 'الأنعام', 7: 'الأعراف', 8: 'الأنفال', 9: 'التوبة', 10: 'يونس',
  11: 'هود', 12: 'يوسف', 13: 'الرعد', 14: 'إبراهيم', 15: 'الحجر',
  16: 'النحل', 17: 'الإسراء', 18: 'الكهف', 19: 'مريم', 20: 'طه',
  21: 'الأنبياء', 22: 'الحج', 23: 'المؤمنون', 24: 'النور', 25: 'الفرقان',
  26: 'الشعراء', 27: 'النمل', 28: 'القصص', 29: 'العنكبوت', 30: 'الروم',
  31: 'لقمان', 32: 'السجدة', 33: 'الأحزاب', 34: 'سبأ', 35: 'فاطر',
  36: 'يس', 37: 'الصافات', 38: 'ص', 39: 'الزمر', 40: 'غافر',
  41: 'فصلت', 42: 'الشورى', 43: 'الزخرف', 44: 'الدخان', 45: 'الجاثية',
  46: 'الأحقاف', 47: 'محمد', 48: 'الفتح', 49: 'الحجرات', 50: 'ق',
  51: 'الذاريات', 52: 'الطور', 53: 'النجم', 54: 'القمر', 55: 'الرحمن',
  56: 'الواقعة', 57: 'الحديد', 58: 'المجادلة', 59: 'الحشر', 60: 'الممتحنة',
  61: 'الصف', 62: 'الجمعة', 63: 'المنافقون', 64: 'التغابن', 65: 'الطلاق',
  66: 'التحريم', 67: 'الملك', 68: 'القلم', 69: 'الحاقة', 70: 'المعارج',
  71: 'نوح', 72: 'الجن', 73: 'المزمل', 74: 'المدثر', 75: 'القيامة',
  76: 'الإنسان', 77: 'المرسلات', 78: 'النبأ', 79: 'النازعات', 80: 'عبس',
  81: 'التكوير', 82: 'الانفطار', 83: 'المطففين', 84: 'الانشقاق', 85: 'البروج',
  86: 'الطارق', 87: 'الأعلى', 88: 'الغاشية', 89: 'الفجر', 90: 'البلد',
  91: 'الشمس', 92: 'الليل', 93: 'الضحى', 94: 'الشرح', 95: 'التين',
  96: 'العلق', 97: 'القدر', 98: 'البينة', 99: 'الزلزلة', 100: 'العاديات',
  101: 'القارعة', 102: 'التكاثر', 103: 'العصر', 104: 'الهمزة', 105: 'الفيل',
  106: 'قريش', 107: 'الماعون', 108: 'الكوثر', 109: 'الكافرون', 110: 'النصر',
  111: 'المسد', 112: 'الإخلاص', 113: 'الفلق', 114: 'الناس',
};

// Sura names mapping (English)
const SURA_NAMES_EN: Record<number, string> = {
  1: 'Al-Fatiha', 2: 'Al-Baqara', 3: 'Aal-Imran', 4: 'An-Nisa', 5: 'Al-Maida',
  6: 'Al-Anam', 7: 'Al-Araf', 8: 'Al-Anfal', 9: 'At-Tawba', 10: 'Yunus',
  11: 'Hud', 12: 'Yusuf', 13: 'Ar-Rad', 14: 'Ibrahim', 15: 'Al-Hijr',
  16: 'An-Nahl', 17: 'Al-Isra', 18: 'Al-Kahf', 19: 'Maryam', 20: 'Ta-Ha',
  21: 'Al-Anbiya', 22: 'Al-Hajj', 23: 'Al-Muminun', 24: 'An-Nur', 25: 'Al-Furqan',
  26: 'Ash-Shuara', 27: 'An-Naml', 28: 'Al-Qasas', 29: 'Al-Ankabut', 30: 'Ar-Rum',
  31: 'Luqman', 32: 'As-Sajda', 33: 'Al-Ahzab', 34: 'Saba', 35: 'Fatir',
  36: 'Ya-Sin', 37: 'As-Saffat', 38: 'Sad', 39: 'Az-Zumar', 40: 'Ghafir',
  41: 'Fussilat', 42: 'Ash-Shura', 43: 'Az-Zukhruf', 44: 'Ad-Dukhan', 45: 'Al-Jathiya',
  46: 'Al-Ahqaf', 47: 'Muhammad', 48: 'Al-Fath', 49: 'Al-Hujurat', 50: 'Qaf',
  51: 'Adh-Dhariyat', 52: 'At-Tur', 53: 'An-Najm', 54: 'Al-Qamar', 55: 'Ar-Rahman',
  56: 'Al-Waqia', 57: 'Al-Hadid', 58: 'Al-Mujadila', 59: 'Al-Hashr', 60: 'Al-Mumtahina',
  61: 'As-Saff', 62: 'Al-Jumua', 63: 'Al-Munafiqun', 64: 'At-Taghabun', 65: 'At-Talaq',
  66: 'At-Tahrim', 67: 'Al-Mulk', 68: 'Al-Qalam', 69: 'Al-Haqqa', 70: 'Al-Maarij',
  71: 'Nuh', 72: 'Al-Jinn', 73: 'Al-Muzzammil', 74: 'Al-Muddaththir', 75: 'Al-Qiyama',
  76: 'Al-Insan', 77: 'Al-Mursalat', 78: 'An-Naba', 79: 'An-Naziat', 80: 'Abasa',
  81: 'At-Takwir', 82: 'Al-Infitar', 83: 'Al-Mutaffifin', 84: 'Al-Inshiqaq', 85: 'Al-Buruj',
  86: 'At-Tariq', 87: 'Al-Ala', 88: 'Al-Ghashiya', 89: 'Al-Fajr', 90: 'Al-Balad',
  91: 'Ash-Shams', 92: 'Al-Layl', 93: 'Ad-Duha', 94: 'Ash-Sharh', 95: 'At-Tin',
  96: 'Al-Alaq', 97: 'Al-Qadr', 98: 'Al-Bayyina', 99: 'Az-Zalzala', 100: 'Al-Adiyat',
  101: 'Al-Qaria', 102: 'At-Takathur', 103: 'Al-Asr', 104: 'Al-Humaza', 105: 'Al-Fil',
  106: 'Quraysh', 107: 'Al-Maun', 108: 'Al-Kawthar', 109: 'Al-Kafirun', 110: 'An-Nasr',
  111: 'Al-Masad', 112: 'Al-Ikhlas', 113: 'Al-Falaq', 114: 'An-Nas',
};

/**
 * Replace sura number with sura name in text.
 * Converts "سورة 2" to "سورة البقرة" (Arabic) or "Surah 2" to "Surah Al-Baqara" (English)
 */
function replaceSuraNumberWithName(text: string, language: 'ar' | 'en'): string {
  if (!text) return text;

  if (language === 'ar') {
    // Replace Arabic pattern: "سورة X" -> "سورة [name]"
    return text.replace(/سورة\s+(\d+)/g, (_, num) => {
      const suraNo = parseInt(num, 10);
      const name = SURA_NAMES_AR[suraNo];
      return name ? `سورة ${name}` : `سورة ${num}`;
    });
  } else {
    // Replace English pattern: "Surah X" -> "Surah [name]"
    return text.replace(/Surah\s+(\d+)/gi, (_, num) => {
      const suraNo = parseInt(num, 10);
      const name = SURA_NAMES_EN[suraNo];
      return name ? `Surah ${name}` : `Surah ${num}`;
    });
  }
}

export function ThemeDetailPage() {
  const { themeId } = useParams<{ themeId: string }>();
  const { language } = useLanguageStore();

  const [theme, setTheme] = useState<ThemeDetail | null>(null);
  const [segments, setSegments] = useState<ThemeSegment[]>([]);
  const [consequences, setConsequences] = useState<ThemeConsequence[]>([]);
  const [relatedThemes, setRelatedThemes] = useState<QuranicTheme[]>([]);
  const [coverage, setCoverage] = useState<ThemeCoverage | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'segments' | 'consequences' | 'related'>('segments');

  // Verse texts map: segment_id -> verse text(s)
  const [verseTexts, setVerseTexts] = useState<Map<string, string>>(new Map());

  // Segment filters
  const [matchTypeFilter, setMatchTypeFilter] = useState<string | undefined>();
  const [confidenceFilter, setConfidenceFilter] = useState<string | undefined>();
  const [coreFilter, setCoreFilter] = useState<boolean | undefined>();
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (themeId) {
      loadTheme(themeId);
    }
  }, [themeId]);

  useEffect(() => {
    if (themeId) {
      loadSegments(themeId);
    }
  }, [themeId, matchTypeFilter, confidenceFilter, coreFilter]);

  async function loadTheme(id: string) {
    setLoading(true);
    try {
      const [themeRes, segmentsRes, consequencesRes, relatedRes, coverageRes] = await Promise.all([
        themesApi.getTheme(id),
        themesApi.getSegments(id),
        themesApi.getConsequences(id),
        themesApi.getRelated(id),
        themesApi.getCoverage(id),
      ]);

      setTheme(themeRes.data);
      setSegments(segmentsRes.data.segments);
      // Backend returns array directly, not {consequences: [...]}
      const consequencesData = consequencesRes.data as unknown;
      setConsequences(Array.isArray(consequencesData) ? consequencesData as ThemeConsequence[] : (consequencesData as { consequences?: ThemeConsequence[] })?.consequences || []);
      // Backend returns array directly, not {themes: [...]}
      const relatedData = relatedRes.data as unknown;
      setRelatedThemes(Array.isArray(relatedData) ? relatedData as QuranicTheme[] : (relatedData as { themes?: QuranicTheme[] })?.themes || []);
      setCoverage(coverageRes.data);
    } catch (error) {
      console.error('Failed to load theme:', error);
    } finally {
      setLoading(false);
    }
  }

  async function loadSegments(id: string) {
    try {
      const params: Record<string, unknown> = {};
      if (matchTypeFilter) params.match_type = matchTypeFilter;
      if (confidenceFilter === 'high') params.min_confidence = 0.8;
      if (confidenceFilter === 'medium') params.min_confidence = 0.5;
      if (coreFilter !== undefined) params.is_core = coreFilter;

      const res = await themesApi.getSegments(id, params);
      setSegments(res.data.segments);
    } catch (error) {
      console.error('Failed to load segments:', error);
    }
  }

  // Fetch verse texts for all segments
  async function loadVerseTexts(segs: ThemeSegment[]) {
    if (segs.length === 0) return;

    const textsMap = new Map<string, string>();

    // Process segments in batches to avoid too many parallel requests
    const batchSize = 10;
    for (let i = 0; i < segs.length; i += batchSize) {
      const batch = segs.slice(i, i + batchSize);
      const promises = batch.map(async (seg) => {
        try {
          if (seg.ayah_start === seg.ayah_end) {
            // Single verse
            const res = await quranApi.getVerse(seg.sura_no, seg.ayah_start);
            textsMap.set(seg.id, res.data.text_uthmani);
          } else {
            // Verse range
            const res = await quranApi.getVerseRange(seg.sura_no, seg.ayah_start, seg.ayah_end);
            const combinedText = res.data.map((v: Verse) => v.text_uthmani).join(' ۝ ');
            textsMap.set(seg.id, combinedText);
          }
        } catch (err) {
          console.error(`Failed to load verses for segment ${seg.id}:`, err);
        }
      });
      await Promise.all(promises);
    }

    setVerseTexts(new Map(textsMap));
  }

  // Load verse texts when segments change
  useEffect(() => {
    if (segments.length > 0) {
      loadVerseTexts(segments);
    }
  }, [segments]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">{t('loading', language)}</p>
        </div>
      </div>
    );
  }

  if (!theme) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-700 mb-2">
          {language === 'ar' ? 'المحور غير موجود' : 'Theme not found'}
        </h2>
        <Link to="/themes" className="text-primary-600 hover:underline">
          {language === 'ar' ? 'العودة للمحاور' : 'Back to Themes'}
        </Link>
      </div>
    );
  }

  const title = language === 'ar' ? theme.title_ar : theme.title_en;
  const description = language === 'ar' ? theme.description_ar : theme.description_en;
  const categoryLabel = language === 'ar' ? theme.category_label_ar : theme.category_label_en;

  // Category colors
  const categoryColors: Record<string, string> = {
    aqidah: 'bg-purple-100 text-purple-700 border-purple-200',
    iman: 'bg-blue-100 text-blue-700 border-blue-200',
    ibadat: 'bg-green-100 text-green-700 border-green-200',
    akhlaq_fardi: 'bg-amber-100 text-amber-700 border-amber-200',
    akhlaq_ijtima: 'bg-orange-100 text-orange-700 border-orange-200',
    muharramat: 'bg-red-100 text-red-700 border-red-200',
    sunan_ilahiyyah: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  };

  const colorClass = categoryColors[theme.category] || 'bg-gray-100 text-gray-700 border-gray-200';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link */}
      <Link
        to="/themes"
        className="inline-flex items-center text-gray-600 hover:text-primary-600 mb-6"
      >
        <ArrowLeft className={`w-4 h-4 ${language === 'ar' ? 'ml-2' : 'mr-2'}`} />
        {language === 'ar' ? 'العودة للمحاور' : 'Back to Themes'}
      </Link>

      {/* Header */}
      <div className="card mb-8">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
          <div>
            <div className={clsx('inline-block text-sm font-medium px-3 py-1 rounded-full mb-3 border', colorClass)}>
              {categoryLabel}
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{title}</h1>
            {description && (
              <p className="text-gray-600 text-lg">{description}</p>
            )}
          </div>

          {/* Stats */}
          <div className="flex flex-wrap gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">{coverage?.total_segments || theme.segment_count}</div>
              <div className="text-sm text-gray-500">{language === 'ar' ? 'مقطع' : 'Segments'}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">{coverage?.total_verses || theme.total_verses}</div>
              <div className="text-sm text-gray-500">{language === 'ar' ? 'آية' : 'Verses'}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">{theme.suras_mentioned?.length || 0}</div>
              <div className="text-sm text-gray-500">{language === 'ar' ? 'سورة' : 'Suras'}</div>
            </div>
            {coverage && coverage.avg_confidence > 0 && (
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{(coverage.avg_confidence * 100).toFixed(0)}%</div>
                <div className="text-sm text-gray-500">{language === 'ar' ? 'الثقة' : 'Confidence'}</div>
              </div>
            )}
          </div>
        </div>

        {/* Coverage Stats */}
        {coverage && coverage.discovered_segments > 0 && (
          <div className="mt-6 pt-6 border-t">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-4 h-4 text-gray-500" />
              <h3 className="text-sm font-medium text-gray-700">
                {language === 'ar' ? 'إحصائيات التغطية' : 'Coverage Statistics'}
              </h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="text-blue-700 font-semibold">{coverage.manual_segments}</div>
                <div className="text-blue-600 text-xs">{language === 'ar' ? 'يدوي' : 'Manual'}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <div className="text-green-700 font-semibold">{coverage.discovered_segments}</div>
                <div className="text-green-600 text-xs">{language === 'ar' ? 'مكتشف' : 'Discovered'}</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="text-purple-700 font-semibold">{coverage.core_segments}</div>
                <div className="text-purple-600 text-xs">{language === 'ar' ? 'أساسي' : 'Core'}</div>
              </div>
              <div className="bg-amber-50 rounded-lg p-3">
                <div className="text-amber-700 font-semibold">{coverage.quran_coverage_percentage.toFixed(2)}%</div>
                <div className="text-amber-600 text-xs">{language === 'ar' ? 'من القرآن' : 'of Quran'}</div>
              </div>
            </div>

            {/* Match Type Distribution */}
            {coverage.by_match_type && Object.keys(coverage.by_match_type).length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-600 mb-2">
                  {language === 'ar' ? 'طريقة الاكتشاف' : 'Discovery Method'}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(coverage.by_match_type).map(([type, count]) => {
                    const typeLabels: Record<string, { ar: string; en: string; color: string }> = {
                      manual: { ar: 'يدوي', en: 'Manual', color: 'bg-gray-200 text-gray-700' },
                      lexical: { ar: 'لفظي', en: 'Lexical', color: 'bg-blue-200 text-blue-700' },
                      root: { ar: 'جذري', en: 'Root', color: 'bg-purple-200 text-purple-700' },
                      semantic: { ar: 'دلالي', en: 'Semantic', color: 'bg-green-200 text-green-700' },
                      mixed: { ar: 'مختلط', en: 'Mixed', color: 'bg-amber-200 text-amber-700' },
                    };
                    const info = typeLabels[type] || { ar: type, en: type, color: 'bg-gray-200 text-gray-700' };
                    if (count === 0) return null;
                    return (
                      <span key={type} className={clsx('px-2 py-1 rounded text-xs font-medium', info.color)}>
                        {language === 'ar' ? info.ar : info.en}: {count}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Confidence Distribution */}
            {coverage.by_confidence_band && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-600 mb-2">
                  {language === 'ar' ? 'توزيع الثقة' : 'Confidence Distribution'}
                </h4>
                <div className="flex gap-1 h-4 rounded-full overflow-hidden bg-gray-100">
                  {coverage.by_confidence_band.high > 0 && (
                    <div
                      className="bg-green-500 h-full"
                      style={{ width: `${(coverage.by_confidence_band.high / coverage.total_segments) * 100}%` }}
                      title={`${language === 'ar' ? 'عالي' : 'High'}: ${coverage.by_confidence_band.high}`}
                    />
                  )}
                  {coverage.by_confidence_band.medium > 0 && (
                    <div
                      className="bg-amber-500 h-full"
                      style={{ width: `${(coverage.by_confidence_band.medium / coverage.total_segments) * 100}%` }}
                      title={`${language === 'ar' ? 'متوسط' : 'Medium'}: ${coverage.by_confidence_band.medium}`}
                    />
                  )}
                  {coverage.by_confidence_band.low > 0 && (
                    <div
                      className="bg-red-500 h-full"
                      style={{ width: `${(coverage.by_confidence_band.low / coverage.total_segments) * 100}%` }}
                      title={`${language === 'ar' ? 'منخفض' : 'Low'}: ${coverage.by_confidence_band.low}`}
                    />
                  )}
                </div>
                <div className="flex justify-between text-xs mt-1 text-gray-500">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    {language === 'ar' ? 'عالي' : 'High'} ({coverage.by_confidence_band.high || 0})
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                    {language === 'ar' ? 'متوسط' : 'Medium'} ({coverage.by_confidence_band.medium || 0})
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-red-500"></span>
                    {language === 'ar' ? 'منخفض' : 'Low'} ({coverage.by_confidence_band.low || 0})
                  </span>
                </div>
              </div>
            )}

            {/* Tafsir Sources Used in Discovery */}
            {coverage.tafsir_sources_used && coverage.tafsir_sources_used.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-gray-600 mb-2">
                  {language === 'ar' ? 'مصادر التفسير المستخدمة' : 'Tafsir Sources Used'}
                </h4>
                <div className="flex flex-wrap gap-1">
                  {coverage.tafsir_sources_used.map((source) => {
                    const name = source.replace('_ar', '').replace('_', ' ');
                    return (
                      <span key={source} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                        {name}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Key Concepts */}
        {theme.key_concepts && theme.key_concepts.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              {language === 'ar' ? 'المفاهيم الأساسية' : 'Key Concepts'}
            </h3>
            <div className="flex flex-wrap gap-2">
              {theme.key_concepts.map((concept) => (
                <span
                  key={concept}
                  className="bg-primary-50 text-primary-700 px-3 py-1 rounded-full text-sm"
                >
                  {concept}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Tafsir Sources */}
        {theme.tafsir_sources && theme.tafsir_sources.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              {language === 'ar' ? 'مصادر التفسير' : 'Tafsir Sources'}
            </h3>
            <div className="flex flex-wrap gap-2">
              {theme.tafsir_sources.map((source) => {
                const sourceLabels: Record<string, { ar: string; en: string; color: string }> = {
                  'ibn_kathir_ar': { ar: 'ابن كثير', en: 'Ibn Kathir', color: 'bg-emerald-100 text-emerald-700' },
                  'tabari_ar': { ar: 'الطبري', en: 'Al-Tabari', color: 'bg-blue-100 text-blue-700' },
                  'qurtubi_ar': { ar: 'القرطبي', en: 'Al-Qurtubi', color: 'bg-purple-100 text-purple-700' },
                  'baghawi_ar': { ar: 'البغوي', en: 'Al-Baghawi', color: 'bg-amber-100 text-amber-700' },
                  'muyassar_ar': { ar: 'الميسر', en: 'Al-Muyassar', color: 'bg-teal-100 text-teal-700' },
                  'saadi_ar': { ar: 'السعدي', en: 'Al-Saadi', color: 'bg-indigo-100 text-indigo-700' },
                  'jalalayn_ar': { ar: 'الجلالين', en: 'Al-Jalalayn', color: 'bg-rose-100 text-rose-700' },
                };
                const info = sourceLabels[source] || { ar: source, en: source, color: 'bg-gray-100 text-gray-700' };
                return (
                  <span
                    key={source}
                    className={clsx('px-3 py-1 rounded-full text-sm font-medium', info.color)}
                  >
                    {language === 'ar' ? info.ar : info.en}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Theme Status Badges */}
        <div className="flex flex-wrap gap-2 mb-4">
          {theme.is_complete && (
            <span className="inline-flex items-center gap-1 bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              {language === 'ar' ? 'مكتمل' : 'Complete'}
            </span>
          )}
          {!theme.is_complete && (
            <span className="inline-flex items-center gap-1 bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-sm font-medium">
              <AlertCircle className="w-4 h-4" />
              {language === 'ar' ? 'قيد التطوير' : 'In Progress'}
            </span>
          )}
          {theme.parent_id && (
            <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm">
              <Layers className="w-4 h-4" />
              {language === 'ar' ? 'محور فرعي' : 'Sub-theme'}
            </span>
          )}
        </div>

        {/* Makki/Madani Distribution */}
        {(theme.makki_percentage > 0 || theme.madani_percentage > 0) && (
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Moon className="w-4 h-4 text-indigo-500" />
              <span className="text-gray-600">{language === 'ar' ? 'مكي' : 'Makki'}: {theme.makki_percentage.toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <Sun className="w-4 h-4 text-amber-500" />
              <span className="text-gray-600">{language === 'ar' ? 'مدني' : 'Madani'}: {theme.madani_percentage.toFixed(0)}%</span>
            </div>
          </div>
        )}

        {/* Children Themes */}
        {theme.children && theme.children.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              {language === 'ar' ? 'المحاور الفرعية' : 'Sub-themes'}
            </h3>
            <div className="flex flex-wrap gap-2">
              {theme.children.map((child) => (
                <Link
                  key={child.id}
                  to={`/themes/${child.id}`}
                  className="inline-flex items-center gap-1 bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded-lg text-sm transition-colors"
                >
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                  {language === 'ar' ? child.title_ar : child.title_en}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab('segments')}
          className={clsx(
            'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
            activeTab === 'segments'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          )}
        >
          <Layers className="w-4 h-4 inline-block mr-1" />
          {language === 'ar' ? 'المقاطع' : 'Segments'} ({segments.length})
        </button>
        <button
          onClick={() => setActiveTab('consequences')}
          className={clsx(
            'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
            activeTab === 'consequences'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          )}
        >
          <Tag className="w-4 h-4 inline-block mr-1" />
          {language === 'ar' ? 'الجزاء والعاقبة' : 'Consequences'} ({consequences.length})
        </button>
        <button
          onClick={() => setActiveTab('related')}
          className={clsx(
            'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
            activeTab === 'related'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          )}
        >
          <BookOpen className="w-4 h-4 inline-block mr-1" />
          {language === 'ar' ? 'محاور متصلة' : 'Related'} ({relatedThemes.length})
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'segments' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={clsx(
                'inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors',
                showFilters ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              <Filter className="w-4 h-4" />
              {language === 'ar' ? 'تصفية' : 'Filter'}
            </button>

            {/* Active filters display */}
            {matchTypeFilter && (
              <span className="inline-flex items-center gap-1 bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                {matchTypeFilter}
                <button onClick={() => setMatchTypeFilter(undefined)}><X className="w-3 h-3" /></button>
              </span>
            )}
            {confidenceFilter && (
              <span className="inline-flex items-center gap-1 bg-green-100 text-green-700 px-2 py-1 rounded text-xs">
                {confidenceFilter}
                <button onClick={() => setConfidenceFilter(undefined)}><X className="w-3 h-3" /></button>
              </span>
            )}
            {coreFilter !== undefined && (
              <span className="inline-flex items-center gap-1 bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">
                {coreFilter ? (language === 'ar' ? 'أساسي' : 'Core') : (language === 'ar' ? 'داعم' : 'Supporting')}
                <button onClick={() => setCoreFilter(undefined)}><X className="w-3 h-3" /></button>
              </span>
            )}
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {language === 'ar' ? 'نوع المطابقة' : 'Match Type'}
                </label>
                <select
                  value={matchTypeFilter || ''}
                  onChange={(e) => setMatchTypeFilter(e.target.value || undefined)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">{language === 'ar' ? 'الكل' : 'All'}</option>
                  <option value="manual">{language === 'ar' ? 'يدوي' : 'Manual'}</option>
                  <option value="lexical">{language === 'ar' ? 'لفظي' : 'Lexical'}</option>
                  <option value="root">{language === 'ar' ? 'جذري' : 'Root-based'}</option>
                  <option value="semantic">{language === 'ar' ? 'دلالي' : 'Semantic'}</option>
                  <option value="mixed">{language === 'ar' ? 'مختلط' : 'Mixed'}</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {language === 'ar' ? 'مستوى الثقة' : 'Confidence Level'}
                </label>
                <select
                  value={confidenceFilter || ''}
                  onChange={(e) => setConfidenceFilter(e.target.value || undefined)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">{language === 'ar' ? 'الكل' : 'All'}</option>
                  <option value="high">{language === 'ar' ? 'عالي (≥80%)' : 'High (≥80%)'}</option>
                  <option value="medium">{language === 'ar' ? 'متوسط (≥50%)' : 'Medium (≥50%)'}</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {language === 'ar' ? 'نوع الآية' : 'Verse Type'}
                </label>
                <select
                  value={coreFilter === undefined ? '' : coreFilter ? 'core' : 'supporting'}
                  onChange={(e) => {
                    if (e.target.value === '') setCoreFilter(undefined);
                    else setCoreFilter(e.target.value === 'core');
                  }}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">{language === 'ar' ? 'الكل' : 'All'}</option>
                  <option value="core">{language === 'ar' ? 'أساسي' : 'Core'}</option>
                  <option value="supporting">{language === 'ar' ? 'داعم' : 'Supporting'}</option>
                </select>
              </div>
            </div>
          )}

          {segments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {language === 'ar' ? 'لا توجد مقاطع بعد' : 'No segments yet'}
            </div>
          ) : (
            segments.map((segment) => (
              <SegmentCard key={segment.id} segment={segment} language={language} themeId={themeId || ''} verseText={verseTexts.get(segment.id)} />
            ))
          )}
        </div>
      )}

      {activeTab === 'consequences' && (
        <div className="space-y-4">
          {consequences.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {language === 'ar' ? 'لا يوجد جزاء مسجل' : 'No consequences recorded'}
            </div>
          ) : (
            consequences.map((consequence) => (
              <ConsequenceCard key={consequence.id} consequence={consequence} language={language} />
            ))
          )}
        </div>
      )}

      {activeTab === 'related' && (
        <div className="grid md:grid-cols-2 gap-4">
          {relatedThemes.length === 0 ? (
            <div className="text-center py-8 text-gray-500 col-span-2">
              {language === 'ar' ? 'لا توجد محاور متصلة' : 'No related themes'}
            </div>
          ) : (
            relatedThemes.map((related) => (
              <Link
                key={related.id}
                to={`/themes/${related.id}`}
                className="card hover:shadow-md transition-shadow flex items-center gap-4"
              >
                <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <BookOpen className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <div className="font-medium">
                    {language === 'ar' ? related.title_ar : related.title_en}
                  </div>
                  <div className="text-sm text-gray-500">
                    {language === 'ar' ? related.category_label_ar : related.category_label_en}
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function SegmentCard({ segment, language, themeId, verseText }: { segment: ThemeSegment; language: 'ar' | 'en'; themeId: string; verseText?: string }) {
  const [showEvidence, setShowEvidence] = useState(false);
  const [evidence, setEvidence] = useState<SegmentEvidence | null>(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);

  const title = language === 'ar' ? segment.title_ar : segment.title_en;
  const summary = language === 'ar' ? segment.summary_ar : segment.summary_en;
  const reasons = language === 'ar' ? segment.reasons_ar : segment.reasons_en;

  const matchTypeLabels: Record<string, { ar: string; en: string; color: string }> = {
    manual: { ar: 'يدوي', en: 'Manual', color: 'bg-gray-100 text-gray-600' },
    lexical: { ar: 'لفظي', en: 'Lexical', color: 'bg-blue-100 text-blue-600' },
    root: { ar: 'جذري', en: 'Root', color: 'bg-purple-100 text-purple-600' },
    semantic: { ar: 'دلالي', en: 'Semantic', color: 'bg-green-100 text-green-600' },
    mixed: { ar: 'مختلط', en: 'Mixed', color: 'bg-amber-100 text-amber-600' },
  };

  const matchInfo = matchTypeLabels[segment.match_type || 'manual'];

  async function loadEvidence() {
    if (evidence) {
      setShowEvidence(!showEvidence);
      return;
    }
    setLoadingEvidence(true);
    try {
      const res = await themesApi.getSegmentEvidence(themeId, segment.id);
      setEvidence(res.data);
      setShowEvidence(true);
    } catch (error) {
      console.error('Failed to load evidence:', error);
    } finally {
      setLoadingEvidence(false);
    }
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Match type badge */}
          <span className={clsx('text-xs px-2 py-0.5 rounded', matchInfo.color)}>
            {language === 'ar' ? matchInfo.ar : matchInfo.en}
          </span>

          {/* Confidence badge */}
          {segment.confidence !== null && segment.confidence !== undefined && segment.match_type !== 'manual' && (
            <span className={clsx(
              'text-xs px-2 py-0.5 rounded',
              segment.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
              segment.confidence >= 0.5 ? 'bg-amber-100 text-amber-700' :
              'bg-red-100 text-red-700'
            )}>
              {(segment.confidence * 100).toFixed(0)}%
            </span>
          )}

          {/* 3-Tier Quality badge (CORE/RECOMMENDED/SUPPORTING) */}
          {(() => {
            // Classify segment into tier based on confidence and match type
            const confidence = segment.confidence || 0;
            const matchType = (segment.match_type || '').toLowerCase();
            const isManual = matchType === 'manual' || matchType === '';
            const isDirectMatch = ['direct', 'exact', 'root', 'lexical', 'manual', ''].includes(matchType);
            const isWeakMatch = ['weak', 'semantic_low'].includes(matchType);

            let tier: 'core' | 'recommended' | 'supporting';
            if (isManual) {
              tier = 'core';
            } else if ((confidence >= 0.82 && isDirectMatch) || (confidence >= 0.74)) {
              tier = 'core';
            } else if ((confidence >= 0.70 && !isWeakMatch) || confidence >= 0.65) {
              tier = 'recommended';
            } else {
              tier = 'supporting';
            }

            const tierConfig = {
              core: { ar: 'أساسي', en: 'Core', color: 'bg-purple-100 text-purple-700', icon: '★' },
              recommended: { ar: 'موصى به', en: 'Recommended', color: 'bg-blue-100 text-blue-700', icon: '◆' },
              supporting: { ar: 'داعم', en: 'Supporting', color: 'bg-gray-100 text-gray-600', icon: '○' },
            };

            const config = tierConfig[tier];
            return (
              <span className={clsx('text-xs px-2 py-0.5 rounded inline-flex items-center gap-1', config.color)}>
                <span>{config.icon}</span>
                {language === 'ar' ? config.ar : config.en}
              </span>
            );
          })()}

          {segment.is_entry_point && (
            <span className="bg-primary-100 text-primary-700 text-xs px-2 py-0.5 rounded">
              {language === 'ar' ? 'نقطة الدخول' : 'Entry Point'}
            </span>
          )}
          {segment.is_verified ? (
            <span className="flex items-center gap-1 text-green-600 text-xs">
              <CheckCircle className="w-3 h-3" />
              {language === 'ar' ? 'موثق' : 'Verified'}
            </span>
          ) : null}
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          {/* Chronological Index */}
          {segment.chronological_index && (
            <span className="flex items-center gap-1 bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded text-xs">
              <span className="font-medium">#{segment.chronological_index}</span>
              <span className="text-indigo-400">{language === 'ar' ? 'ترتيب النزول' : 'Revelation'}</span>
            </span>
          )}
          {/* Revelation Context */}
          {segment.revelation_context && (
            <span className="flex items-center gap-1">
              {segment.revelation_context === 'makki' ? (
                <Moon className="w-3 h-3 text-indigo-500" />
              ) : (
                <Sun className="w-3 h-3 text-amber-500" />
              )}
              {segment.revelation_context === 'makki'
                ? (language === 'ar' ? 'مكي' : 'Makki')
                : (language === 'ar' ? 'مدني' : 'Madani')}
            </span>
          )}
          {/* Segment Order */}
          <span className="text-xs text-gray-400">
            #{segment.segment_order}
          </span>
        </div>
      </div>

      {title && <h4 className="font-semibold mb-2">{title}</h4>}

      <div className="flex items-center gap-2 mb-2">
        <Link
          to={`/quran/${segment.sura_no}?aya=${segment.ayah_start}`}
          className="inline-flex items-center gap-1 text-primary-600 hover:underline text-sm font-medium"
        >
          <BookMarked className="w-4 h-4" />
          {segment.verse_reference}
          <ExternalLink className="w-3 h-3" />
        </Link>

        {/* Why this verse button */}
        {segment.match_type && segment.match_type !== 'manual' && (
          <button
            onClick={loadEvidence}
            disabled={loadingEvidence}
            className="inline-flex items-center gap-1 text-gray-500 hover:text-primary-600 text-xs transition-colors"
          >
            <HelpCircle className="w-3 h-3" />
            {language === 'ar' ? 'لماذا هذه الآية؟' : 'Why this verse?'}
          </button>
        )}
      </div>

      {/* Quranic Verse Text */}
      {verseText ? (
        <div className="my-4 p-4 bg-amber-50 rounded-lg border border-amber-200" dir="rtl">
          <p className="text-xl leading-loose font-arabic text-gray-900 text-center">
            {verseText}
          </p>
        </div>
      ) : (
        <div className="my-4 p-4 bg-gray-50 rounded-lg animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-3/4 mx-auto"></div>
        </div>
      )}

      <p className="text-gray-600 text-sm">{replaceSuraNumberWithName(summary, language)}</p>

      {/* Reasons (from discovery) */}
      {reasons && reasons !== summary && (
        <p className="text-gray-500 text-xs mt-2 italic">{replaceSuraNumberWithName(reasons, language)}</p>
      )}

      {/* Evidence panel */}
      {showEvidence && evidence && (
        <div className="mt-4 pt-4 border-t bg-gray-50 rounded-lg p-4">
          <h5 className="font-medium text-sm mb-2">
            {language === 'ar' ? 'لماذا ينتمي هذا النص للمحور؟' : 'Why does this verse belong to this theme?'}
          </h5>
          <p className="text-sm text-gray-700 mb-3 font-arabic">{evidence.reasons_ar}</p>
          {evidence.evidence_sources && evidence.evidence_sources.length > 0 && (
            <div className="space-y-2">
              <h6 className="text-xs font-medium text-gray-500">
                {language === 'ar' ? 'دليل التفسير:' : 'Tafsir Evidence:'}
              </h6>
              {evidence.evidence_sources.slice(0, 2).map((ev, i) => (
                <div key={i} className="text-xs bg-white rounded p-2 border">
                  <span className="font-medium text-primary-600">{ev.source_id.replace('_ar', '')}</span>
                  <p className="text-gray-600 mt-1 font-arabic line-clamp-2">{ev.snippet}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {segment.semantic_tags && segment.semantic_tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {segment.semantic_tags.map((tag) => (
            <span
              key={tag}
              className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ConsequenceCard({ consequence, language }: { consequence: ThemeConsequence; language: 'ar' | 'en' }) {
  const description = language === 'ar' ? consequence.description_ar : consequence.description_en;
  const typeLabel = language === 'ar' ? consequence.type_label_ar : consequence.type_label_en;

  // Type colors
  const typeColors: Record<string, string> = {
    reward: 'bg-green-100 text-green-700 border-green-200',
    blessing: 'bg-blue-100 text-blue-700 border-blue-200',
    promise: 'bg-purple-100 text-purple-700 border-purple-200',
    punishment: 'bg-red-100 text-red-700 border-red-200',
    warning: 'bg-amber-100 text-amber-700 border-amber-200',
  };

  const colorClass = typeColors[consequence.consequence_type] || 'bg-gray-100 text-gray-700';

  return (
    <div className="card">
      <div className="flex items-start gap-3">
        <div className={clsx('px-3 py-1 rounded-full text-sm font-medium border', colorClass)}>
          {typeLabel}
        </div>
        <div className="flex-1">
          <p className="text-gray-800 font-arabic text-lg leading-relaxed mb-3">{description}</p>
          {consequence.supporting_verses && consequence.supporting_verses.length > 0 && (
            <div className="text-sm text-gray-500">
              <span className="font-medium">{language === 'ar' ? 'الدليل:' : 'Evidence:'}</span>
              {' '}
              {consequence.supporting_verses.map((v, i) => (
                <span key={i}>
                  {i > 0 && ', '}
                  <Link
                    to={`/quran/${v.sura}?aya=${v.ayah}`}
                    className="text-primary-600 hover:underline"
                  >
                    {v.sura}:{v.ayah}
                  </Link>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
