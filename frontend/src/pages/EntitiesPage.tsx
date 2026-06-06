import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Search, AlertCircle } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { entitiesApi, type EntitySummary } from '../lib/api';

const ENTITY_TYPE_LABELS: Record<string, { ar: string; en: string }> = {
  prophet: { ar: 'الأنبياء', en: 'Prophets' },
  person: { ar: 'شخصيات', en: 'Persons' },
  woman: { ar: 'النساء', en: 'Women' },
  people_or_nation: { ar: 'الأمم والأقوام', en: 'Peoples & Nations' },
  place: { ar: 'الأماكن', en: 'Places' },
  animal: { ar: 'الحيوانات', en: 'Animals' },
  object: { ar: 'الأشياء', en: 'Objects' },
  event: { ar: 'الأحداث', en: 'Events' },
  angel: { ar: 'الملائكة', en: 'Angels' },
  jinn: { ar: 'الجن', en: 'Jinn' },
  scripture: { ar: 'الكتب السماوية', en: 'Scriptures' },
  family_relation: { ar: 'صلات القرابة', en: 'Family Relations' },
};

export function EntitiesPage() {
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const [entities, setEntities] = useState<EntitySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  useEffect(() => {
    let stale = false;
    setLoading(true);
    setError(null);
    entitiesApi
      .list({ limit: 500 })
      .then((r) => {
        if (stale) return;
        setEntities(r.entities);
      })
      .catch((e) => {
        if (stale) return;
        setError(e?.message || 'Failed to load entities');
      })
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, []);

  const visible = entities.filter((e) => {
    if (typeFilter && e.entityType !== typeFilter) return false;
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      e.labelEnglish.toLowerCase().includes(q) ||
      e.labelArabic.includes(query) ||
      e.entityId.toLowerCase().includes(q)
    );
  });

  const types = Array.from(new Set(entities.map((e) => e.entityType))).sort();

  return (
    <div className="max-w-7xl mx-auto px-4 py-8" dir={dir}>
      <header className="mb-8">
        <h1 className={`text-3xl font-bold text-gray-900 mb-2 ${language === 'ar' ? 'font-arabic' : ''}`}>
          <span dir="ltr" className="inline-block">{language === 'ar' ? 'رحلات الذوات في القرآن' : 'Entity-Centered Quran Journeys'}</span>
        </h1>
        <p className={`text-gray-600 ${language === 'ar' ? 'font-arabic' : ''}`}>
          {language === 'ar'
            ? 'استكشف كيف ترتبط الذوات — الأنبياء والأقوام والأماكن والأحداث — عبر سور القرآن الكريم.'
            : 'Explore how prophets, peoples, places, and events are connected across the surahs of the Quran.'}
        </p>
        <div className="mt-4 flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
          <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-amber-800">
            {language === 'ar'
              ? 'كل الروابط هنا تحتاج إلى مراجعة علمية. لا يوجد تفسير مولّد آليًا.'
              : 'All connections here are pending scholarly review. No AI-generated tafsir is shown.'}
          </p>
        </div>
      </header>

      <div className="mb-6 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className={`absolute top-3 ${language === 'ar' ? 'right-3' : 'left-3'} w-4 h-4 text-gray-400`} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={language === 'ar' ? 'ابحث باسم الذات' : 'Search entities…'}
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
              {ENTITY_TYPE_LABELS[t]?.[language] ?? t}
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
            {visible.map((e) => (
              <Link
                key={e.entityId}
                to={`/entities/${encodeURIComponent(e.entityId)}`}
                className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <h2 className="font-semibold text-gray-900" dir="ltr">{e.labelEnglish}</h2>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {ENTITY_TYPE_LABELS[e.entityType]?.[language] ?? e.entityType}
                  </span>
                </div>
                <p className="font-arabic text-lg text-gray-800 mb-2" dir="rtl">
                  {e.labelArabic}
                </p>
                <p className="text-xs text-gray-500">
                  {language === 'ar' ? `${e.mentionCount} ذكر` : `${e.mentionCount} mentions`}
                </p>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
