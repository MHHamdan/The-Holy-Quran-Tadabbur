/**
 * Segment Tafsir Panel
 *
 * Shows the seeded classical tafsir for the opening verse of a story segment,
 * with full source attribution.
 *
 * Per the content policy, nothing here is generated: every word of commentary
 * is retrieved from the tafseer corpus and rendered beside the source id,
 * author, era and licence it came from. Loading is on demand so opening a
 * story does not fan out one tafsir request per segment.
 */
import { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, AlertTriangle, ShieldCheck } from 'lucide-react';
import {
  tafsirComparisonApi,
  type TafsirComparisonEntry,
  type TafsirComparisonResponse,
} from '../../lib/api';
import clsx from 'clsx';

interface Props {
  suraNo: number;
  ayaStart: number;
  ayaEnd: number;
  language: 'ar' | 'en';
}

/** Reader's language first, then by scholarly reliability. */
function orderForReader(
  entries: TafsirComparisonEntry[],
  language: 'ar' | 'en',
): TafsirComparisonEntry[] {
  return [...entries].sort((a, b) => {
    if (a.language !== b.language) return a.language === language ? -1 : 1;
    return (b.reliability_score ?? 0) - (a.reliability_score ?? 0);
  });
}

export function SegmentTafsirPanel({ suraNo, ayaStart, ayaEnd, language }: Props) {
  const isAr = language === 'ar';
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<TafsirComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (!next || data || loading) return;

    setLoading(true);
    setFailed(false);
    try {
      // No `language` filter: the API would hard-filter rather than reorder,
      // which would hide Tabari and Qurtubi from an English reader entirely.
      // Every source is fetched and `orderForReader` puts theirs first.
      const res = await tafsirComparisonApi.compare(suraNo, ayaStart);
      setData(res.data);
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }

  const entries = data ? orderForReader(data.entries, language) : [];
  // A segment usually spans several verses; the corpus is keyed per verse, so
  // the opening verse is fetched and the reader is told that is what they see.
  const spansRange = ayaEnd > ayaStart;
  const openingRef = `${suraNo}:${ayaStart}`;
  const fullRef = spansRange ? `${suraNo}:${ayaStart}-${ayaEnd}` : openingRef;

  return (
    <div className="mt-4 pt-4 border-t border-gray-100">
      <button
        onClick={toggle}
        aria-expanded={open}
        className={clsx(
          'flex items-center gap-2 text-sm font-medium text-primary-700 hover:text-primary-800 transition-colors',
          isAr && 'font-arabic',
        )}
      >
        <BookOpen className="w-4 h-4" />
        {isAr ? 'التفسير من المصادر المعتمدة' : 'Tafsir from established sources'}
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {open && (
        <div className="mt-3">
          {loading && (
            <div className="flex items-center justify-center py-6">
              <div className="animate-spin w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full" />
            </div>
          )}

          {failed && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className={clsx('text-sm text-amber-800', isAr && 'font-arabic')}>
                {isAr
                  ? 'تعذّر تحميل التفسير لهذا الموضع. حاول مرة أخرى.'
                  : 'Tafsir for this passage could not be loaded. Please try again.'}
              </p>
            </div>
          )}

          {!loading && !failed && data && entries.length === 0 && (
            <p className={clsx('text-sm text-gray-500 py-3', isAr && 'font-arabic')}>
              {isAr
                ? 'لا يوجد تفسير مُفهرس لهذا الموضع في المصادر المتاحة.'
                : 'No indexed tafsir is available for this passage in the seeded sources.'}
            </p>
          )}

          {!loading && !failed && data && entries.length > 0 && (
            <div className="space-y-3">
              <p className={clsx('text-xs text-gray-500', isAr && 'font-arabic')}>
                {spansRange ? (
                  isAr ? (
                    <>
                      التفسير معروض عند الآية{' '}
                      <span dir="ltr">{openingRef}</span>، وهي مطلع المقطع{' '}
                      <span dir="ltr">{fullRef}</span>.
                    </>
                  ) : (
                    <>
                      Tafsir shown for <span dir="ltr">{openingRef}</span>, the opening
                      verse of this passage (<span dir="ltr">{fullRef}</span>).
                    </>
                  )
                ) : isAr ? (
                  <>
                    التفسير معروض عند الآية <span dir="ltr">{openingRef}</span>.
                  </>
                ) : (
                  <>
                    Tafsir shown for <span dir="ltr">{openingRef}</span>.
                  </>
                )}
              </p>

              {entries.map((entry) => (
                <TafsirEntryCard key={entry.chunk_id} entry={entry} language={language} />
              ))}

              <p
                className={clsx(
                  'text-[11px] text-gray-400 leading-relaxed pt-1',
                  isAr && 'font-arabic',
                )}
              >
                {isAr ? data.comparison.disclaimer_ar : data.comparison.disclaimer_en}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TafsirEntryCard({
  entry,
  language,
}: {
  entry: TafsirComparisonEntry;
  language: 'ar' | 'en';
}) {
  const isAr = language === 'ar';
  const [expanded, setExpanded] = useState(false);

  // The commentary's own direction, which is independent of the UI language.
  const textIsArabic = entry.language === 'ar';
  const title = isAr ? entry.name_ar : entry.name_en;
  const author = isAr ? entry.author_ar : entry.author_en;
  const era = isAr ? entry.era_label_ar : entry.era_label_en;
  const methodology = isAr ? entry.methodology_label_ar : entry.methodology_label_en;

  const LONG = 420;
  const isLong = entry.text.length > LONG;
  const shown = expanded || !isLong ? entry.text : `${entry.text.slice(0, LONG).trimEnd()}…`;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
      <div className="flex items-start justify-between flex-wrap gap-2 mb-2">
        <div>
          <h4 className={clsx('text-sm font-semibold text-gray-900', isAr && 'font-arabic')}>
            {title}
          </h4>
          {author && (
            <p className={clsx('text-xs text-gray-500', isAr && 'font-arabic')}>
              {author}
              {entry.death_year_hijri != null && (
                <span className="text-gray-400">
                  {' · '}
                  <span dir="ltr" className="tabular-nums">
                    {isAr
                      ? `ت. ${entry.death_year_hijri} هـ`
                      : `d. ${entry.death_year_hijri} AH`}
                  </span>
                </span>
              )}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {era && (
            <span
              className={clsx(
                'text-[11px] bg-white text-gray-600 border border-gray-200 rounded-full px-2 py-0.5',
                isAr && 'font-arabic',
              )}
            >
              {era}
            </span>
          )}
          {methodology && (
            <span
              className={clsx(
                'text-[11px] bg-primary-50 text-primary-700 border border-primary-100 rounded-full px-2 py-0.5',
                isAr && 'font-arabic',
              )}
            >
              {methodology}
            </span>
          )}
        </div>
      </div>

      <p
        dir={textIsArabic ? 'rtl' : 'ltr'}
        lang={entry.language}
        className={clsx(
          'text-sm text-gray-700 leading-relaxed whitespace-pre-line',
          textIsArabic && 'font-arabic',
        )}
      >
        {shown}
      </p>

      {isLong && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className={clsx(
            'mt-2 text-xs font-medium text-primary-600 hover:text-primary-700',
            isAr && 'font-arabic',
          )}
        >
          {expanded
            ? isAr
              ? 'عرض أقل'
              : 'Show less'
            : isAr
              ? 'قراءة النص كاملاً'
              : 'Read the full text'}
        </button>
      )}

      {/* Attribution is required for every displayed tafsir entry. */}
      <div className="mt-3 pt-2 border-t border-gray-200 flex items-center gap-1.5 flex-wrap">
        {entry.license_verified && (
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
        )}
        <span className="text-[11px] text-gray-500" dir="ltr">
          {entry.source_id}
        </span>
        {entry.license_type && (
          <span className="text-[11px] text-gray-400" dir="ltr">
            · {entry.license_type.replace(/_/g, ' ')}
          </span>
        )}
      </div>
    </div>
  );
}
