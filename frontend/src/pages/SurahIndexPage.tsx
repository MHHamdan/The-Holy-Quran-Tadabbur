/**
 * Surah index — the reader's table of contents.
 *
 * Tabs: Surah (114 searchable rows: Arabic and English names, ayah count,
 * Makki/Madani, start page) | Juz (the juz navigator) | Page (jump to a
 * Mushaf page). Each surah row opens /quran/:n; the page number opens the
 * Mushaf at that surah. Route: /quran (and /juz -> /quran?tab=juz), added in
 * App.tsx.
 */
import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { BookOpen, CheckCircle2, Search } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_NAMES, SURAH_VERSE_COUNTS } from '../data/surahNames';
import { useReadingProgress } from '../hooks/useReadingProgress';
import {
  firstPageOfJuz, SURAH_FIRST_JUZ, SURAH_FIRST_PAGE, SURAH_REVELATION, TOTAL_MUSHAF_PAGES,
} from '../components/reader/surahNavigation';
import { JuzNavigatorContent } from './JuzNavigatorPage';

type Tab = 'surah' | 'juz' | 'page';

const arDigits = (n: number | string) => String(n).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[Number(d)]);

/** Fold case, diacritics, hyphens and apostrophes for forgiving name search. */
function foldLatin(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
}

/** Strip harakat/tatweel and unify alef/ya/ta marbuta forms for Arabic search. */
function foldArabic(s: string): string {
  return s
    .replace(/[ً-ٰٟـ]/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/\s+/g, '');
}

function matches(n: number, query: string): boolean {
  const q = query.trim();
  if (!q) return true;
  if (/^\d+$/.test(q)) return String(n) === q || String(n).startsWith(q);
  const name = SURAH_NAMES[n - 1];
  const latin = foldLatin(q);
  if (latin && foldLatin(name.en).includes(latin)) return true;
  const arabic = foldArabic(q).replace(/^ال/, '');
  return !!arabic && foldArabic(name.ar).includes(arabic);
}

export function SurahIndexPage() {
  const { language } = useLanguageStore();
  const ar = language === 'ar';
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const tab: Tab = params.get('tab') === 'juz' ? 'juz' : params.get('tab') === 'page' ? 'page' : 'surah';
  const setTab = (t: Tab) => {
    const next = new URLSearchParams(params);
    if (t === 'surah') next.delete('tab'); else next.set('tab', t);
    setParams(next, { replace: true });
  };
  const [query, setQuery] = useState('');
  const [pageInput, setPageInput] = useState('');
  const { progress } = useReadingProgress();

  const surahs = useMemo(
    () => Array.from({ length: 114 }, (_, i) => i + 1).filter((n) => matches(n, query)),
    [query],
  );

  const tabs: Array<{ id: Tab; ar: string; en: string }> = [
    { id: 'surah', ar: 'السور', en: 'Surahs' },
    { id: 'juz', ar: 'الأجزاء', en: 'Juz' },
    { id: 'page', ar: 'الصفحات', en: 'Pages' },
  ];

  const pageNo = Number(pageInput);
  const pageValid = Number.isInteger(pageNo) && pageNo >= 1 && pageNo <= TOTAL_MUSHAF_PAGES;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" dir={ar ? 'rtl' : 'ltr'}>
      <h1 className={clsx('text-2xl font-bold text-gray-900 flex items-center gap-2 mb-4', ar && 'font-arabic')}>
        <BookOpen className="w-6 h-6 text-primary-600" aria-hidden="true" />
        {ar ? 'فهرس القرآن الكريم' : 'Qur’an index'}
      </h1>

      <div role="tablist" aria-label={ar ? 'طريقة التصفح' : 'Browse by'} className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-5">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            id={`index-tab-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls={`index-panel-${t.id}`}
            onClick={() => setTab(t.id)}
            className={clsx(
              'flex-1 py-2 rounded-lg text-sm font-medium transition-colors',
              tab === t.id ? 'bg-white shadow text-primary-700' : 'text-gray-600 hover:text-gray-900',
              ar && 'font-arabic',
            )}
          >
            {ar ? t.ar : t.en}
          </button>
        ))}
      </div>

      {tab === 'surah' && (
        <section role="tabpanel" id="index-panel-surah" aria-labelledby="index-tab-surah">
          <div className="relative mb-4">
            <Search className={clsx('absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400', ar ? 'right-3' : 'left-3')} aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label={ar ? 'ابحث عن سورة بالاسم أو الرقم' : 'Search surahs by name or number'}
              placeholder={ar ? 'ابحث بالاسم أو الرقم، مثل: الكهف' : 'Search by name or number, e.g. Kahf'}
              className={clsx(
                'w-full border border-gray-200 rounded-xl py-2.5 text-sm focus:ring-2 focus:ring-primary-300 outline-none bg-white',
                ar ? 'pr-9 pl-3 font-arabic' : 'pl-9 pr-3',
              )}
            />
          </div>
          <p className="text-xs text-gray-500 mb-2" role="status">
            {ar ? `${arDigits(surahs.length)} سورة` : `${surahs.length} surahs`}
          </p>
          <ul className="divide-y divide-gray-100 bg-white border border-gray-100 rounded-2xl overflow-hidden" data-testid="surah-index">
            {surahs.map((n) => {
              const name = SURAH_NAMES[n - 1];
              const rev = SURAH_REVELATION[n];
              const read = progress.visited.has(n);
              return (
                <li key={n} className="flex items-center gap-3 px-3 sm:px-4 py-3 hover:bg-gray-50">
                  <span className="w-9 h-9 rounded-lg bg-primary-50 text-primary-700 flex items-center justify-center text-sm font-semibold flex-shrink-0">
                    {ar ? arDigits(n) : n}
                  </span>
                  <Link to={`/quran/${n}`} className="flex-1 min-w-0">
                    <span className="flex items-center justify-between gap-2">
                      <span className="font-arabic text-lg text-gray-900" dir="rtl" lang="ar">{name.ar}</span>
                      <span className="text-sm text-gray-600 truncate" dir="ltr" lang="en">{name.en}</span>
                    </span>
                    <span className={clsx('block text-xs text-gray-500 mt-0.5', ar && 'font-arabic')}>
                      {ar
                        ? `${arDigits(SURAH_VERSE_COUNTS[n - 1])} آية${rev === 'makki' ? ' · مكية' : rev === 'madani' ? ' · مدنية' : ''} · الجزء ${arDigits(SURAH_FIRST_JUZ[n - 1])}`
                        : `${SURAH_VERSE_COUNTS[n - 1]} verses${rev === 'makki' ? ' · Makki' : rev === 'madani' ? ' · Madani' : ''} · Juz ${SURAH_FIRST_JUZ[n - 1]}`}
                    </span>
                  </Link>
                  {read && (
                    <CheckCircle2
                      className="w-4 h-4 text-emerald-500 flex-shrink-0"
                      aria-label={ar ? 'مقروءة' : 'Read'}
                    />
                  )}
                  <Link
                    to={`/mushaf?page=${SURAH_FIRST_PAGE[n - 1]}`}
                    className="text-xs text-primary-700 hover:underline flex-shrink-0"
                    aria-label={ar ? `افتح ${name.ar} في المصحف، صفحة ${arDigits(SURAH_FIRST_PAGE[n - 1])}` : `Open ${name.en} in the Mushaf, page ${SURAH_FIRST_PAGE[n - 1]}`}
                  >
                    {ar ? `ص ${arDigits(SURAH_FIRST_PAGE[n - 1])}` : `p. ${SURAH_FIRST_PAGE[n - 1]}`}
                  </Link>
                </li>
              );
            })}
          </ul>
          {surahs.length === 0 && (
            <p className={clsx('text-center text-sm text-gray-500 py-8', ar && 'font-arabic')}>
              {ar ? 'لا توجد سورة بهذا الاسم.' : 'No surah matches that name.'}
            </p>
          )}
        </section>
      )}

      {tab === 'juz' && (
        <section role="tabpanel" id="index-panel-juz" aria-labelledby="index-tab-juz">
          <JuzNavigatorContent />
        </section>
      )}

      {tab === 'page' && (
        <section role="tabpanel" id="index-panel-page" aria-labelledby="index-tab-page" className="bg-white border border-gray-100 rounded-2xl p-5">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (pageValid) navigate(`/mushaf?page=${pageNo}`);
            }}
            className="flex flex-wrap items-end gap-3"
          >
            <label className={clsx('flex flex-col gap-1 text-sm text-gray-700', ar && 'font-arabic')}>
              {ar ? `رقم الصفحة (١–${arDigits(TOTAL_MUSHAF_PAGES)})` : `Page number (1–${TOTAL_MUSHAF_PAGES})`}
              <input
                type="number"
                min={1}
                max={TOTAL_MUSHAF_PAGES}
                value={pageInput}
                onChange={(e) => setPageInput(e.target.value)}
                className="w-32 border border-gray-200 rounded-lg px-3 py-2"
              />
            </label>
            <button
              type="submit"
              disabled={!pageValid}
              className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700 disabled:bg-gray-300"
            >
              {ar ? 'افتح في المصحف' : 'Open in the Mushaf'}
            </button>
          </form>
          <p className={clsx('text-xs text-gray-500 mt-4 mb-2', ar && 'font-arabic')}>
            {ar ? 'بدايات الأجزاء:' : 'Juz start pages:'}
          </p>
          <div className="grid grid-cols-5 sm:grid-cols-10 gap-1.5">
            {Array.from({ length: 30 }, (_, i) => i + 1).map((j) => {
              const first = firstPageOfJuz(j);
              return (
                <Link
                  key={j}
                  to={`/mushaf?page=${first}`}
                  className="text-center text-xs py-2 rounded-lg bg-gray-50 border border-gray-100 hover:border-primary-300"
                  aria-label={ar ? `الجزء ${arDigits(j)}، صفحة ${arDigits(first)}` : `Juz ${j}, page ${first}`}
                >
                  {ar ? arDigits(j) : j}
                </Link>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}


export default SurahIndexPage;
