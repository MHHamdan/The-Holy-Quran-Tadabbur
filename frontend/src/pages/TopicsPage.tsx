import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Search, AlertCircle } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { topicsApi, type TopicSummary } from '../lib/api';

const TYPE_LABELS: Record<string, { ar: string; en: string }> = {
  faith: { ar: 'العقيدة والإيمان', en: 'Faith & creed' },
  worship: { ar: 'العبادات', en: 'Worship' },
  ethics: { ar: 'الأخلاق', en: 'Ethics' },
  story_theme: { ar: 'مواضيع قصصية', en: 'Story themes' },
  legal_theme: { ar: 'مواضيع تشريعية', en: 'Legal themes' },
  social_theme: { ar: 'الحياة الاجتماعية', en: 'Social life' },
  emotional_theme: { ar: 'وجدانية وروحية', en: 'Emotional / spiritual' },
  divine_attribute: { ar: 'صفات الله', en: 'Divine attributes' },
  hereafter: { ar: 'الآخرة', en: 'Hereafter' },
  creation_sign: { ar: 'آيات الكون والخلق', en: 'Creation & signs' },
  warning: { ar: 'الإنذارات', en: 'Warnings' },
  promise: { ar: 'الوعود', en: 'Promises' },
  command: { ar: 'الأوامر', en: 'Commands' },
  prohibition: { ar: 'النواهي', en: 'Prohibitions' },
  concept_cluster: { ar: 'مجموعة مفاهيم', en: 'Concept cluster' },
  discovered_candidate: { ar: 'مرشّح مكتشف', en: 'Discovered candidate' },
};

export function TopicsPage() {
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => {
    let stale = false;
    setLoading(true);
    topicsApi
      .list({ limit: 500 })
      .then((r) => !stale && setTopics(r.topics))
      .catch((e) => !stale && setError(e?.message || 'Failed to load topics'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, []);

  const visible = useMemo(
    () =>
      topics.filter((t) => {
        if (typeFilter && t.topicType !== typeFilter) return false;
        if (!query) return true;
        const q = query.toLowerCase();
        return (
          t.labelEnglish.toLowerCase().includes(q) ||
          t.labelArabic.includes(query) ||
          t.topicId.toLowerCase().includes(q)
        );
      }),
    [topics, query, typeFilter]
  );

  const types = useMemo(() => Array.from(new Set(topics.map((t) => t.topicType))).sort(), [topics]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8" dir={dir}>
      <header className="mb-6">
        <h1 className={`text-3xl font-bold text-gray-900 mb-2 ${language === 'ar' ? 'font-arabic' : ''}`}>
          {language === 'ar' ? 'أطلس مواضيع القرآن' : 'Quranic Topic Discovery Atlas'}
        </h1>
        <p className={`text-gray-600 ${language === 'ar' ? 'font-arabic' : ''}`}>
          {language === 'ar'
            ? 'استكشف المواضيع الكبرى للقرآن عبر السور والآيات والقصص والكيانات. كل ربط هنا هو ملاحظ فقط.'
            : 'Discover the major topics of the Quran across surahs, ayahs, stories and entities. Every link here is observational only.'}
        </p>
        <div className="mt-3 flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
          <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-amber-800">
            {language === 'ar'
              ? 'جميع الروابط في أطلس المواضيع تحتاج إلى مراجعة علمية. لا يوجد تفسير مولّد.'
              : 'All topic links here are pending scholarly review. No AI-generated tafsir is shown.'}
          </p>
        </div>
      </header>

      <div className="mb-6 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search
            className={`absolute top-3 ${language === 'ar' ? 'right-3' : 'left-3'} w-4 h-4 text-gray-400`}
          />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={language === 'ar' ? 'ابحث في المواضيع' : 'Search topics…'}
            className={`w-full ${language === 'ar' ? 'pr-9' : 'pl-9'} pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500`}
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md bg-white"
        >
          <option value="">{language === 'ar' ? 'كل الأنواع' : 'All types'}</option>
          {types.map((t) => (
            <option key={t} value={t}>
              {TYPE_LABELS[t]?.[language] ?? t}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="py-20 flex justify-center">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-800">{error}</div>
      )}

      {!loading && !error && (
        <>
          <p className="text-sm text-gray-600 mb-4">
            {language === 'ar' ? `إجمالي: ${visible.length}` : `Total: ${visible.length}`}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {visible.map((t) => (
              <Link
                key={t.topicId}
                to={`/topics/${encodeURIComponent(t.topicId)}`}
                className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-1.5">
                  <h2 className="font-semibold text-gray-900" dir="ltr">
                    {t.labelEnglish}
                  </h2>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {TYPE_LABELS[t.topicType]?.[language] ?? t.topicType}
                  </span>
                </div>
                <p className="font-arabic text-lg text-gray-800 mb-2" dir="rtl">
                  {t.labelArabic}
                </p>
                <p className="text-xs text-gray-500">
                  {language === 'ar'
                    ? `${t.ayahCount} آية · ${t.surahCount} سورة`
                    : `${t.ayahCount} ayahs · ${t.surahCount} surahs`}
                </p>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
