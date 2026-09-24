/**
 * TafsirComparison — every stored tafsir for one verse, side by side.
 *
 * Reads the local corpus via /tafseer/compare, so each passage carries a
 * chunk_id and real provenance rather than coming from a third-party API.
 *
 * Layout is a stacked list, not parallel columns. Median length across the six
 * seeded sources spans 33 words (al-Muyassar) to 761 (Ibn Kathir EN) and peaks
 * above 11,000, so columns would be mostly whitespace and unusable at phone
 * width. Each entry instead gets a full-width card with a scholarly header,
 * and long prose collapses behind a toggle.
 *
 * Entries arrive oldest-author-first from the API. That ordering is the point:
 * reading al-Tabari (310H) before Ibn Kathir (774H) before al-Muyassar (modern)
 * shows how the tradition builds on itself.
 */
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Layers,
  AlertCircle,
  Languages,
} from 'lucide-react';

import {
  tafsirComparisonApi,
  type TafsirComparisonEntry,
  type TafsirComparisonResponse,
} from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';

interface Props {
  surah: number;
  ayah: number;
  className?: string;
}

type LanguageFilter = 'all' | 'ar' | 'en';

/** Characters shown before a long passage collapses. */
const COLLAPSE_THRESHOLD = 700;

/** Tint per methodology so the reader can scan for approach, not just author. */
const METHODOLOGY_STYLES: Record<string, string> = {
  bil_mathur: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  bil_ray: 'bg-sky-50 text-sky-800 border-sky-200',
  comprehensive: 'bg-indigo-50 text-indigo-800 border-indigo-200',
  fiqh_focused: 'bg-violet-50 text-violet-800 border-violet-200',
  fiqhi: 'bg-violet-50 text-violet-800 border-violet-200',
  concise: 'bg-amber-50 text-amber-800 border-amber-200',
  simplified: 'bg-teal-50 text-teal-800 border-teal-200',
  linguistic: 'bg-rose-50 text-rose-800 border-rose-200',
};

function methodologyClass(methodology: string | null): string {
  return (
    (methodology && METHODOLOGY_STYLES[methodology]) ||
    'bg-stone-100 text-stone-700 border-stone-200'
  );
}

// ---------------------------------------------------------------------------
// Source header
// ---------------------------------------------------------------------------

function SourceHeader({
  entry,
  uiLanguage,
}: {
  entry: TafsirComparisonEntry;
  uiLanguage: 'ar' | 'en';
}) {
  const title = uiLanguage === 'ar' ? entry.name_ar : entry.name_en;
  const author = uiLanguage === 'ar' ? entry.author_ar : entry.author_en;
  const methodLabel =
    uiLanguage === 'ar' ? entry.methodology_label_ar : entry.methodology_label_en;
  const eraLabel = uiLanguage === 'ar' ? entry.era_label_ar : entry.era_label_en;

  return (
    <div className="flex flex-wrap items-start justify-between gap-2">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          {/* The source title follows the script it is written in, not the UI
              language, so an Arabic tafsir name never renders left-to-right. */}
          <span
            className={clsx(
              'font-semibold text-stone-900',
              uiLanguage === 'ar' && 'font-arabic text-lg',
            )}
            dir={uiLanguage === 'ar' ? 'rtl' : 'ltr'}
          >
            {title}
          </span>
          <span
            className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wide bg-stone-100 text-stone-500"
            dir="ltr"
          >
            {entry.language}
          </span>
        </div>
        {author && (
          <div
            className={clsx(
              'mt-0.5 text-sm text-stone-600 truncate',
              uiLanguage === 'ar' && 'font-arabic',
            )}
            dir={uiLanguage === 'ar' ? 'rtl' : 'ltr'}
          >
            {author}
            {entry.death_year_hijri != null && (
              <span className="text-stone-400" dir="ltr">
                {' · '}
                {t('tafsir_compare_died', uiLanguage)}{' '}
                {entry.death_year_hijri} {t('tafsir_compare_hijri', uiLanguage)}
                {entry.death_year_ce != null && ` / ${entry.death_year_ce} CE`}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-1.5 shrink-0">
        {methodLabel && (
          <span
            className={clsx(
              'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
              methodologyClass(entry.methodology),
            )}
          >
            {methodLabel}
          </span>
        )}
        {eraLabel && (
          <span className="inline-flex items-center rounded-full border border-stone-200 bg-white px-2 py-0.5 text-xs text-stone-600">
            {eraLabel}
          </span>
        )}
        <span className="text-xs text-stone-400 tabular-nums" dir="ltr">
          {entry.word_count.toLocaleString()} {t('tafsir_compare_words', uiLanguage)}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// One source's passage
// ---------------------------------------------------------------------------

function TafsirEntryCard({
  entry,
  uiLanguage,
}: {
  entry: TafsirComparisonEntry;
  uiLanguage: 'ar' | 'en';
}) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const isLong = entry.text.length > COLLAPSE_THRESHOLD;
  const shown = expanded || !isLong ? entry.text : entry.text.slice(0, COLLAPSE_THRESHOLD);
  const isArabic = entry.language === 'ar';

  const copyCitation = async () => {
    const name = isArabic ? entry.name_ar : entry.name_en;
    const citation = `${name} — ${entry.covers_ayat} [${entry.chunk_id}]`;
    try {
      await navigator.clipboard.writeText(citation);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard can be unavailable (insecure context, denied permission).
      // Failing silently is right here — the citation is visible on screen.
    }
  };

  return (
    <article className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <SourceHeader entry={entry} uiLanguage={uiLanguage} />

      {/* The passage takes the direction of the text itself, never the UI's —
          an Arabic tafsir inside an English interface must still be RTL. */}
      <div
        className={clsx(
          'mt-3 border-t border-stone-100 pt-3 text-stone-800 whitespace-pre-wrap',
          isArabic
            ? 'font-arabic text-[1.05rem] leading-loose'
            : 'text-sm leading-relaxed',
        )}
        dir={isArabic ? 'rtl' : 'ltr'}
        lang={entry.language}
      >
        {shown}
        {isLong && !expanded && <span className="text-stone-400">…</span>}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        {isLong ? (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-primary-700 hover:bg-primary-50"
          >
            {expanded ? (
              <>
                <ChevronUp className="h-3.5 w-3.5" />
                {t('tafsir_compare_show_less', uiLanguage)}
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5" />
                {t('tafsir_compare_show_more', uiLanguage)}
              </>
            )}
          </button>
        ) : (
          <span />
        )}

        <button
          type="button"
          onClick={copyCitation}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-stone-500 hover:bg-stone-100 hover:text-stone-700"
          title={entry.chunk_id}
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-600" />
              {t('tafsir_compare_citation_copied', uiLanguage)}
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              {t('tafsir_compare_copy_citation', uiLanguage)}
            </>
          )}
        </button>
      </div>
    </article>
  );
}

// ---------------------------------------------------------------------------
// Descriptive statistics
// ---------------------------------------------------------------------------

function ComparisonStats({
  data,
  uiLanguage,
}: {
  data: TafsirComparisonResponse;
  uiLanguage: 'ar' | 'en';
}) {
  const { comparison, entries } = data;
  const nameOf = (id: string) => {
    const entry = entries.find((e) => e.source_id === id);
    if (!entry) return id;
    return uiLanguage === 'ar' ? entry.name_ar : entry.name_en;
  };

  // Only the strongest few pairs are informative; the full matrix is noise.
  const topOverlap = comparison.lexical_overlap.slice(0, 3);
  const disclaimer =
    uiLanguage === 'ar' ? comparison.disclaimer_ar : comparison.disclaimer_en;

  return (
    <section className="rounded-xl border border-stone-200 bg-stone-50 p-4">
      <h3 className="flex items-center gap-1.5 text-sm font-semibold text-stone-800">
        <Layers className="h-4 w-4 text-stone-500" />
        {t('tafsir_compare_overlap_title', uiLanguage)}
      </h3>

      {topOverlap.length > 0 && (
        <ul className="mt-2 space-y-1.5">
          {topOverlap.map((pair) => (
            <li
              key={`${pair.a}-${pair.b}`}
              className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-stone-600"
            >
              <span className="font-medium text-stone-800">{nameOf(pair.a)}</span>
              <span className="text-stone-400">·</span>
              <span className="font-medium text-stone-800">{nameOf(pair.b)}</span>
              <span
                className="ms-auto tabular-nums rounded bg-white border border-stone-200 px-1.5 py-0.5"
                dir="ltr"
              >
                {Math.round(pair.jaccard * 100)}%
              </span>
            </li>
          ))}
        </ul>
      )}

      {/* The API ships this wording; it is a content-policy requirement that an
          overlap figure never appears without it. Render it verbatim. */}
      <p className="mt-3 flex items-start gap-1.5 text-[11px] leading-relaxed text-stone-500">
        <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-px text-stone-400" />
        <span>{disclaimer}</span>
      </p>

      {comparison.length.longest_source_id && (
        <dl className="mt-3 grid grid-cols-2 gap-2 border-t border-stone-200 pt-3 text-xs">
          <div>
            <dt className="text-stone-500">{t('tafsir_compare_shortest', uiLanguage)}</dt>
            <dd className="mt-0.5 font-medium text-stone-800">
              {nameOf(comparison.length.shortest_source_id!)}{' '}
              <span className="text-stone-400 tabular-nums" dir="ltr">
                ({comparison.length.shortest_word_count?.toLocaleString()})
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-stone-500">{t('tafsir_compare_longest', uiLanguage)}</dt>
            <dd className="mt-0.5 font-medium text-stone-800">
              {nameOf(comparison.length.longest_source_id)}{' '}
              <span className="text-stone-400 tabular-nums" dir="ltr">
                ({comparison.length.longest_word_count?.toLocaleString()})
              </span>
            </dd>
          </div>
        </dl>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function TafsirComparison({ surah, ayah, className }: Props) {
  const { language } = useLanguageStore();
  const [languageFilter, setLanguageFilter] = useState<LanguageFilter>('all');
  const [activeSource, setActiveSource] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['tafsir-comparison', surah, ayah],
    queryFn: async () => {
      const res = await tafsirComparisonApi.compare(surah, ayah);
      return res.data;
    },
    // Seeded tafsir is immutable once ingested, so there is nothing to refetch.
    staleTime: Infinity,
    gcTime: 30 * 60 * 1000,
  });

  const visible = useMemo(() => {
    if (!data) return [];
    return data.entries.filter((entry) => {
      if (languageFilter !== 'all' && entry.language !== languageFilter) return false;
      if (activeSource && entry.source_id !== activeSource) return false;
      return true;
    });
  }, [data, languageFilter, activeSource]);

  if (isLoading) {
    return (
      <div className={clsx('space-y-3', className)} aria-busy="true">
        <p className="text-sm text-stone-500">{t('tafsir_compare_loading', language)}</p>
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-28 animate-pulse rounded-xl bg-stone-100" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div
        className={clsx(
          'rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800',
          className,
        )}
        role="alert"
      >
        <p>{t('tafsir_compare_error', language)}</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-2 rounded-md border border-amber-300 bg-white px-2 py-1 text-xs font-medium hover:bg-amber-100"
        >
          {t('tafsir_compare_retry', language)}
        </button>
      </div>
    );
  }

  if (data.entries.length === 0) {
    return (
      <p className={clsx('text-sm text-stone-500', className)}>
        {t('tafsir_compare_empty', language)}
      </p>
    );
  }

  return (
    <div className={clsx('space-y-4', className)}>
      <header>
        <h2 className="flex items-center gap-2 text-base font-semibold text-stone-900">
          <BookOpen className="h-4.5 w-4.5 text-primary-600" />
          {t('tafsir_compare_title', language)}
          <span className="text-sm font-normal text-stone-400 tabular-nums" dir="ltr">
            ({data.sources_returned} {t('tafsir_compare_sources_count', language)})
          </span>
        </h2>
        <p className="mt-0.5 text-xs text-stone-500">
          {t('tafsir_compare_subtitle', language)}
        </p>
      </header>

      {/* Filters. Sources are listed in the same chronological order as the
          entries so the control and the list stay legible against each other. */}
      <div className="flex flex-wrap items-center gap-1.5">
        <Languages className="h-3.5 w-3.5 text-stone-400" />
        {(
          [
            ['all', t('tafsir_compare_all_languages', language)],
            ['ar', t('tafsir_compare_arabic_only', language)],
            ['en', t('tafsir_compare_english_only', language)],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            onClick={() => setLanguageFilter(value as LanguageFilter)}
            aria-pressed={languageFilter === value}
            className={clsx(
              'rounded-full border px-2.5 py-1 text-xs font-medium transition-colors',
              languageFilter === value
                ? 'border-primary-300 bg-primary-50 text-primary-800'
                : 'border-stone-200 bg-white text-stone-600 hover:bg-stone-50',
            )}
          >
            {label}
          </button>
        ))}

        <span className="mx-1 h-4 w-px bg-stone-200" aria-hidden="true" />

        <button
          type="button"
          onClick={() => setActiveSource(null)}
          aria-pressed={activeSource === null}
          className={clsx(
            'rounded-full border px-2.5 py-1 text-xs font-medium transition-colors',
            activeSource === null
              ? 'border-primary-300 bg-primary-50 text-primary-800'
              : 'border-stone-200 bg-white text-stone-600 hover:bg-stone-50',
          )}
        >
          {t('tafsir_compare_filter_all', language)}
        </button>
        {data.entries.map((entry) => (
          <button
            key={entry.source_id}
            type="button"
            onClick={() =>
              setActiveSource((cur) => (cur === entry.source_id ? null : entry.source_id))
            }
            aria-pressed={activeSource === entry.source_id}
            className={clsx(
              'rounded-full border px-2.5 py-1 text-xs font-medium transition-colors',
              activeSource === entry.source_id
                ? 'border-primary-300 bg-primary-50 text-primary-800'
                : 'border-stone-200 bg-white text-stone-600 hover:bg-stone-50',
            )}
          >
            <span dir={entry.language === 'ar' ? 'rtl' : 'ltr'}>
              {language === 'ar' ? entry.name_ar : entry.name_en}
            </span>
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {visible.map((entry) => (
          <TafsirEntryCard key={entry.chunk_id} entry={entry} uiLanguage={language} />
        ))}
      </div>

      {visible.length > 1 && <ComparisonStats data={data} uiLanguage={language} />}
    </div>
  );
}

export default TafsirComparison;
