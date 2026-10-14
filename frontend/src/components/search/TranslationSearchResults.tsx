/**
 * "Found in translation": verses whose translation of the meanings contains
 * every word of the query (QuranEnc editions, word-start match). Runs beside
 * the concept search, so plain-language queries ("orphans", "Moses
 * Pharaoh") find verses even when no concept matches.
 */
import { Fragment, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { Languages } from 'lucide-react';
import { quranApi } from '../../lib/api';
import { useReaderSettingsStore, effectiveTranslationKeys } from '../../stores/readerSettingsStore';
import { isRtlLanguage, useTranslationEditions } from '../quran/VerseTranslations';
import type { Language } from '../../i18n/translations';
import { QuranTextAttribution } from '../quran/QuranTextAttribution';

const PAGE = 10;

/** Wrap query terms in <mark> (React elements, never HTML strings). */
function highlight(text: string, terms: string[]) {
  if (terms.length === 0) return text;
  const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const folded = fold(text);
  if (folded.length !== text.length) return text; // offsets would not line up
  const marks: [number, number][] = [];
  for (const t of terms) {
    let i = folded.indexOf(t);
    while (i !== -1) {
      if (i === 0 || !/\p{L}/u.test(folded[i - 1])) marks.push([i, i + t.length]);
      i = folded.indexOf(t, i + 1);
    }
  }
  if (marks.length === 0) return text;
  marks.sort((a, b) => a[0] - b[0]);
  const out: React.ReactNode[] = [];
  let pos = 0;
  marks.forEach(([s, e], k) => {
    if (s < pos) return;
    out.push(<Fragment key={`t${k}`}>{text.slice(pos, s)}</Fragment>);
    out.push(<mark key={`m${k}`} className="bg-amber-100 rounded px-0.5">{text.slice(s, e)}</mark>);
    pos = e;
  });
  out.push(<Fragment key="end">{text.slice(pos)}</Fragment>);
  return out;
}

export function TranslationSearchResults({ query, language }: { query: string; language: Language }) {
  const ar = language === 'ar';
  const { translationKeys } = useReaderSettingsStore();
  const { data: editions } = useTranslationEditions();
  // The reader's first chosen edition, else the English default.
  const keys = effectiveTranslationKeys(translationKeys, language);
  const edition = keys[0] ?? 'english_saheeh';
  const [shown, setShown] = useState(PAGE);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['translation-search', query, edition, shown],
    enabled: query.trim().length >= 2,
    placeholderData: (prev) => prev,
    queryFn: () =>
      quranApi.searchTranslations(query, { translations: [edition], limit: shown }).then((r) => r.data),
  });

  if (isLoading || isError || !data || data.total === 0) return null;
  const title = editions?.find((e) => e.key === edition)?.title ?? edition;

  return (
    <section className="mb-6 card" aria-label={ar ? 'نتائج في ترجمة المعاني' : 'Found in translation'}>
      <h2 className={clsx('flex items-center gap-2 text-lg font-semibold mb-1', ar && 'font-arabic')}>
        <Languages className="w-5 h-5 text-primary-600" />
        {ar ? `في ترجمة المعاني (${data.total})` : `Found in translation (${data.total})`}
      </h2>
      <p className="text-xs text-gray-500 mb-4" dir="ltr">{title} · QuranEnc.com</p>
      <ol className="space-y-3">
        {data.hits.map((h) => {
          const rtl = isRtlLanguage(h.translation.language);
          return (
            <li key={`${h.verse_id}-${h.translation.translator}`} className="rounded-xl border border-gray-100 p-3">
              <Link
                to={`/quran/${h.sura_no}?aya=${h.aya_no}`}
                className={clsx('text-xs font-semibold text-primary-700 hover:underline', ar && 'font-arabic')}
              >
                {ar ? h.sura_name_ar : h.sura_name_en} {h.sura_no}:{h.aya_no}
              </Link>
              <p dir="rtl" className="mt-1 font-arabic text-lg leading-loose text-gray-900">
                {h.text_imlaei.replace(/^\uFEFF/, '')}
              </p>
              <p dir={rtl ? 'rtl' : 'ltr'} lang={h.translation.language} className="mt-1 text-sm text-gray-700 leading-relaxed">
                {highlight(h.translation.text, data.terms)}
              </p>
            </li>
          );
        })}
      </ol>
      <QuranTextAttribution language={language} className="mt-3" />
      {data.total > data.hits.length && (
        <button
          type="button"
          onClick={() => setShown((n) => n + PAGE)}
          className={clsx('mt-4 text-sm font-medium text-primary-600 hover:underline', ar && 'font-arabic')}
        >
          {ar ? 'عرض المزيد' : 'Show more'}
        </button>
      )}
    </section>
  );
}
