import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, Search, AlertCircle, Star } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import {
  asmaApi,
  type AsmaCategoryEntry,
  type AsmaListResponse,
  type AsmaNameSummary,
} from '../lib/api';
import { AsmaAudioPlayer } from '../components/quran/AsmaAudioPlayer';
import clsx from 'clsx';

const CATEGORY_BADGE: Record<string, string> = {
  dhat: 'bg-purple-50 text-purple-700 border-purple-200',
  jamal: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  jalal: 'bg-red-50 text-red-700 border-red-200',
  kamal: 'bg-blue-50 text-blue-700 border-blue-200',
  afaal: 'bg-amber-50 text-amber-700 border-amber-200',
  unknown: 'bg-gray-50 text-gray-700 border-gray-200',
};

export function AsmaAllahPage() {
  const { language } = useLanguageStore();
  const navigate = useNavigate();
  const dir = language === 'ar' ? 'rtl' : 'ltr';

  const [data, setData] = useState<AsmaListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [query, setQuery] = useState('');
  const [withOccurrencesOnly, setWithOccurrencesOnly] = useState(true);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    setError(null);
    asmaApi
      .list({ limit: 500 })
      .then((r) => !stale && setData(r))
      .catch((e) => !stale && setError(e?.message || 'Failed to load Names of Allah'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, []);

  const categoriesWithAll: AsmaCategoryEntry[] = useMemo(() => {
    if (!data) return [];
    // The "All" tab represents the primary Asmā' learning list: the 99
    // traditional Names. The Divine Name "Allah" is shown separately in a
    // hero panel and is NOT counted here, so this must equal 99 — not 100.
    const allEntry: AsmaCategoryEntry = {
      category: 'all',
      names: data.allDisplayCount,
      countedOccurrences: data.categories.reduce((acc, c) => acc + c.countedOccurrences, 0),
      labelArabic: 'الكل',
      labelEnglish: 'All',
    };
    return [allEntry, ...data.categories];
  }, [data]);

  const visible = useMemo<AsmaNameSummary[]>(() => {
    if (!data) return [];
    return data.names.filter((n) => {
      if (activeCategory !== 'all' && n.category !== activeCategory) return false;
      if (withOccurrencesOnly && n.occurrenceCount === 0) return false;
      if (!query) return true;
      const q = query.toLowerCase();
      return (
        n.transliteration.toLowerCase().includes(q) ||
        (n.englishName ?? '').toLowerCase().includes(q) ||
        n.arabicName.includes(query) ||
        n.nameId.includes(q)
      );
    });
  }, [data, activeCategory, query, withOccurrencesOnly]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8" dir={dir}>
      {/* Hero */}
      <header className="mb-8">
        <h1
          className={clsx(
            'text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3',
            language === 'ar' && 'font-arabic'
          )}
        >
          <Star className="w-8 h-8 text-emerald-600" />
          {language === 'ar' ? 'أسماء الله الحسنى' : 'Names of Allah'}
        </h1>
        <p className={clsx('text-gray-600 max-w-3xl', language === 'ar' && 'font-arabic')}>
          {language === 'ar'
            ? 'تعرف على أسماء الله الحسنى وشواهدها القرآنية. المعاني المفصّلة بحاجة إلى مراجعة علمية، ويعتمد العدّ على سياسة استبعاد البسملة الافتتاحية.'
            : 'Explore the Names of Allah and their Quranic evidence. Detailed meanings require scholarly review, and counts follow the surah-opening basmalah exclusion policy.'}
        </p>
        {data && (
          <div className="mt-3 flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-md text-sm text-amber-800">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <p>
              {language === 'ar'
                ? `سياسة العدّ: ${
                    data.basmalahPolicy.excludeRepeatedSurahOpeningBasmalah ? 'استثناء البسملة الافتتاحية' : 'تضمين البسملة'
                  }${data.basmalahPolicy.countBasmalaInFatihah ? '' : '، استثناء بسملة الفاتحة'}.`
                : `Counting policy: ${
                    data.basmalahPolicy.excludeRepeatedSurahOpeningBasmalah ? 'surah-opening basmalah excluded' : 'basmalah included'
                  }${data.basmalahPolicy.countBasmalaInFatihah ? '' : '; Al-Fatihah 1:1 basmalah excluded'}.`}
            </p>
          </div>
        )}
      </header>

      {/* Search + filters */}
      <div className="mb-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search
            className={`absolute top-3 ${language === 'ar' ? 'right-3' : 'left-3'} w-4 h-4 text-gray-400`}
          />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={language === 'ar' ? 'ابحث عن اسم' : 'Search Names…'}
            className={`w-full ${
              language === 'ar' ? 'pr-9' : 'pl-9'
            } pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500`}
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={withOccurrencesOnly}
            onChange={(e) => setWithOccurrencesOnly(e.target.checked)}
          />
          {language === 'ar' ? 'فقط الأسماء التي وردت في القرآن' : 'Only Names with Quran occurrences'}
        </label>
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {categoriesWithAll.map((c) => (
          <button
            key={c.category}
            onClick={() => setActiveCategory(c.category)}
            className={clsx(
              'px-4 py-2 rounded-full text-sm font-medium border transition-colors flex items-center gap-2',
              activeCategory === c.category
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            )}
          >
            <span className={language === 'ar' ? 'font-arabic' : ''}>
              {language === 'ar' ? c.labelArabic : c.labelEnglish}
            </span>
            <span className="text-xs opacity-80">
              ({c.names})
            </span>
          </button>
        ))}
      </div>

      {loading && (
        <div className="py-20 flex justify-center">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-800">{error}</div>
      )}

      {!loading && !error && data && <AsmaAudioPlayer names={data.names} />}

      {!loading && !error && data && data.divineNameAllah && (
        <section
          aria-label={language === 'ar' ? 'اسم الجلالة' : 'The Divine Name'}
          className="mb-6 p-5 bg-gradient-to-br from-emerald-50 to-amber-50 border border-emerald-200 rounded-lg"
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <p className="text-xs font-medium text-emerald-700 uppercase tracking-wide" dir={dir}>
                {language === 'ar' ? data.divineNameAllah.labelArabic : data.divineNameAllah.labelEnglish}
              </p>
              <p className="font-arabic text-4xl text-gray-900 leading-tight mt-1" dir="rtl">
                {data.divineNameAllah.arabicName}
              </p>
              <p className="text-sm text-gray-700 mt-1" dir="ltr">
                {data.divineNameAllah.transliteration}
              </p>
              <p className="text-xs text-gray-600 mt-2" dir={dir}>
                {language === 'ar'
                  ? data.divineNameAllah.separateFromListNoteArabic
                  : data.divineNameAllah.separateFromListNoteEnglish}
              </p>
            </div>
            <button
              onClick={() => navigate(`/asma-allah/${encodeURIComponent(data.divineNameAllah!.nameId)}`)}
              className="self-start sm:self-center px-4 py-2 text-sm rounded-md bg-emerald-600 text-white hover:bg-emerald-700"
            >
              {language === 'ar'
                ? `${data.divineNameAllah.occurrenceCount} موضع · ${data.divineNameAllah.surahCount} سورة`
                : `${data.divineNameAllah.occurrenceCount} occurrences · ${data.divineNameAllah.surahCount} surahs`}
            </button>
          </div>
        </section>
      )}

      {!loading && !error && data && (
        <>
          <p className="text-sm text-gray-600 mb-4">
            {language === 'ar' ? `إجمالي: ${visible.length}` : `Total: ${visible.length}`}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {visible.map((n) => (
              <button
                key={n.nameId}
                onClick={() => navigate(`/asma-allah/${encodeURIComponent(n.nameId)}`)}
                className="text-start p-5 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p
                      className="font-arabic text-3xl text-gray-900 leading-tight"
                      dir="rtl"
                    >
                      {n.arabicName}
                    </p>
                    <p className="text-sm text-gray-600 mt-1" dir="ltr">
                      {n.transliteration}
                    </p>
                    {n.englishName && (
                      <p className="text-xs text-gray-500" dir="ltr">
                        {n.englishName}
                      </p>
                    )}
                  </div>
                  <span
                    className={clsx(
                      'text-[10px] px-1.5 py-0.5 rounded border',
                      CATEGORY_BADGE[n.category] ?? CATEGORY_BADGE.unknown
                    )}
                  >
                    {n.category}
                  </span>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 mt-3 text-xs">
                  <span className="text-emerald-700">
                    {language === 'ar'
                      ? `${n.occurrenceCount} موضع · ${n.surahCount} سورة`
                      : `${n.occurrenceCount} occurrences · ${n.surahCount} surahs`}
                  </span>
                  {n.warningCount > 0 && (
                    <span className="text-amber-700 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {n.warningCount}{' '}
                      {language === 'ar' ? 'تنبيه' : 'warning'}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
          {visible.length === 0 && (
            <p className="text-sm text-gray-500 py-10 text-center">
              {language === 'ar' ? 'لا توجد أسماء مطابقة.' : 'No Names match the current filters.'}
            </p>
          )}
        </>
      )}

      <div className="mt-8 flex items-start gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-md text-sm">
        <AlertCircle className="w-4 h-4 text-emerald-700 mt-0.5 flex-shrink-0" />
        <p className="text-emerald-800">
          {language === 'ar' ? (
            <>
              تابع تفاصيل كل اسم على صفحته الخاصة. المعنى المفصّل يظهر فقط عند توفّر مصدر علمي موثّق.
              راجع{' '}
              <Link to="/sources" className="underline">
                سجل المصادر
              </Link>{' '}
              لمعرفة المراجع.
            </>
          ) : (
            <>
              See full per-Name details on each Name's page. Verified meanings are only shown when a
              trusted scholarly source is attached. Check the{' '}
              <Link to="/sources" className="underline">
                source registry
              </Link>{' '}
              for references.
            </>
          )}
        </p>
      </div>
    </div>
  );
}
