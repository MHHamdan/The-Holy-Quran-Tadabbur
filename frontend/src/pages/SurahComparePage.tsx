/**
 * Surah Comparison Tool — compare any two surahs side-by-side.
 *
 * Data sources: SURAH_ATLAS_DATA (ayahCount, revelationType, keyConcepts, juzRefs, summary)
 *               TIMELINE_BY_SURAH (revelationOrder, period, mainTheme)
 *               SURAH_NAMES (display names)
 *
 * No Quran text displayed directly — only metadata and scholarly summaries.
 */

import { useState, useMemo } from 'react';
import { GitCompare, ChevronDown } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_ATLAS_DATA } from '../data/surahAtlas';
import { TIMELINE_BY_SURAH } from '../data/revelationTimeline';
import { SURAH_NAMES } from '../data/surahNames';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getSurahData(surahNum: number) {
  const atlas = SURAH_ATLAS_DATA.find(s => s.surahNumber === surahNum);
  const timeline = TIMELINE_BY_SURAH[surahNum];
  const name = SURAH_NAMES[surahNum - 1];
  return { atlas, timeline, name };
}

const AYAH_COUNTS: number[] = SURAH_ATLAS_DATA.map(s => s.ayahCount);
const MAX_AYAHS = Math.max(...AYAH_COUNTS);

// ---------------------------------------------------------------------------
// Comparison row types
// ---------------------------------------------------------------------------

interface CompareRow {
  labelEn: string;
  labelAr: string;
  renderA: string | null;
  renderB: string | null;
  highlight?: boolean;
}

function buildRows(
  a: ReturnType<typeof getSurahData>,
  b: ReturnType<typeof getSurahData>,
  isRtl: boolean,
): CompareRow[] {
  const rows: CompareRow[] = [];

  // Revelation type
  const revA = a.atlas?.revelationType ?? '—';
  const revB = b.atlas?.revelationType ?? '—';
  rows.push({
    labelEn: 'Revelation Type',
    labelAr: 'نوع التنزيل',
    renderA: revA === 'makki' ? (isRtl ? 'مكية' : 'Meccan') : revA === 'madani' ? (isRtl ? 'مدنية' : 'Medinan') : revA,
    renderB: revB === 'makki' ? (isRtl ? 'مكية' : 'Meccan') : revB === 'madani' ? (isRtl ? 'مدنية' : 'Medinan') : revB,
    highlight: revA !== revB,
  });

  // Revelation period
  rows.push({
    labelEn: 'Period',
    labelAr: 'الحقبة',
    renderA: a.timeline ? (isRtl ? PERIOD_AR[a.timeline.period] : PERIOD_EN[a.timeline.period]) : '—',
    renderB: b.timeline ? (isRtl ? PERIOD_AR[b.timeline.period] : PERIOD_EN[b.timeline.period]) : '—',
    highlight: a.timeline?.period !== b.timeline?.period,
  });

  // Chronological order
  rows.push({
    labelEn: 'Revelation Order',
    labelAr: 'ترتيب النزول',
    renderA: a.timeline ? `#${a.timeline.revelationOrder}` : '—',
    renderB: b.timeline ? `#${b.timeline.revelationOrder}` : '—',
    highlight: false,
  });

  // Ayah count
  rows.push({
    labelEn: 'Verse Count',
    labelAr: 'عدد الآيات',
    renderA: a.atlas ? String(a.atlas.ayahCount) : '—',
    renderB: b.atlas ? String(b.atlas.ayahCount) : '—',
    highlight: a.atlas?.ayahCount !== b.atlas?.ayahCount,
  });

  // Page range
  rows.push({
    labelEn: 'Mushaf Pages',
    labelAr: 'صفحات المصحف',
    renderA: a.atlas ? `${a.atlas.pageStart}–${a.atlas.pageEnd}` : '—',
    renderB: b.atlas ? `${b.atlas.pageStart}–${b.atlas.pageEnd}` : '—',
    highlight: false,
  });

  // Juz(es)
  rows.push({
    labelEn: 'Juz',
    labelAr: 'الجزء',
    renderA: a.atlas?.juzRefs?.join(', ') ?? '—',
    renderB: b.atlas?.juzRefs?.join(', ') ?? '—',
    highlight: JSON.stringify(a.atlas?.juzRefs) !== JSON.stringify(b.atlas?.juzRefs),
  });

  // Main theme
  rows.push({
    labelEn: 'Main Theme',
    labelAr: 'الموضوع الرئيسي',
    renderA: a.timeline ? (isRtl ? a.timeline.mainThemeAr : a.timeline.mainThemeEn) : '—',
    renderB: b.timeline ? (isRtl ? b.timeline.mainThemeAr : b.timeline.mainThemeEn) : '—',
    highlight: false,
  });

  // Key concepts
  rows.push({
    labelEn: 'Key Concepts',
    labelAr: 'المفاهيم الرئيسية',
    renderA: a.atlas?.keyConcepts?.slice(0, 4).join(', ') ?? '—',
    renderB: b.atlas?.keyConcepts?.slice(0, 4).join(', ') ?? '—',
    highlight: false,
  });

  // Prophets mentioned
  rows.push({
    labelEn: 'Prophets Mentioned',
    labelAr: 'الأنبياء المذكورون',
    renderA: a.atlas?.prophetsMentioned?.length
      ? a.atlas.prophetsMentioned.slice(0, 4).join(', ')
      : isRtl ? 'لا أحد' : 'None',
    renderB: b.atlas?.prophetsMentioned?.length
      ? b.atlas.prophetsMentioned.slice(0, 4).join(', ')
      : isRtl ? 'لا أحد' : 'None',
    highlight:
      JSON.stringify(a.atlas?.prophetsMentioned?.slice().sort()) !==
      JSON.stringify(b.atlas?.prophetsMentioned?.slice().sort()),
  });

  return rows;
}

const PERIOD_EN: Record<string, string> = {
  early_meccan: 'Early Meccan',
  middle_meccan: 'Middle Meccan',
  late_meccan: 'Late Meccan',
  early_medinan: 'Early Medinan',
  late_medinan: 'Late Medinan',
};
const PERIOD_AR: Record<string, string> = {
  early_meccan: 'مكي مبكر',
  middle_meccan: 'مكي وسط',
  late_meccan: 'مكي متأخر',
  early_medinan: 'مدني مبكر',
  late_medinan: 'مدني متأخر',
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SurahSelector({
  value,
  onChange,
  isRtl,
  label,
}: {
  value: number;
  onChange: (n: number) => void;
  isRtl: boolean;
  label: string;
}) {
  return (
    <div className="flex-1 min-w-0">
      <p className={clsx('text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide', isRtl && 'font-arabic text-right')}>
        {label}
      </p>
      <div className="relative">
        <select
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          className={clsx(
            'w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-3 pr-9 text-sm font-semibold text-gray-800 focus:outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100',
            isRtl && 'font-arabic text-right pr-4 pl-9'
          )}
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          {SURAH_NAMES.map((sn, i) => (
            <option key={i + 1} value={i + 1}>
              {i + 1}. {isRtl ? sn.ar : sn.en}
            </option>
          ))}
        </select>
        <ChevronDown className={clsx('pointer-events-none absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400', isRtl ? 'left-3' : 'right-3')} />
      </div>
    </div>
  );
}

function AyahBar({ count, maxCount }: { count: number; maxCount: number }) {
  const pct = Math.max(4, (count / maxCount) * 100);
  return (
    <div className="mt-1 w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
      <div className="h-full bg-violet-400 rounded-full" style={{ width: `${pct}%` }} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function SurahComparePage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [surahA, setSurahA] = useState(2);  // Al-Baqarah — longest
  const [surahB, setSurahB] = useState(36); // Ya-Sin — most recited

  const dataA = useMemo(() => getSurahData(surahA), [surahA]);
  const dataB = useMemo(() => getSurahData(surahB), [surahB]);
  const rows = useMemo(() => buildRows(dataA, dataB, isRtl), [dataA, dataB, isRtl]);

  const summaryA = dataA.atlas?.summary?.short?.[isRtl ? 'ar' : 'en'];
  const summaryB = dataB.atlas?.summary?.short?.[isRtl ? 'ar' : 'en'];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-6', isRtl && 'flex-row-reverse')}>
        <GitCompare className="w-7 h-7 text-violet-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'مقارنة السور' : 'Surah Comparison'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl ? 'قارن بين أي سورتين جنباً إلى جنب' : 'Compare any two surahs side by side'}
          </p>
        </div>
      </div>

      {/* Selectors */}
      <div className={clsx('flex gap-3 mb-6 items-end', isRtl && 'flex-row-reverse')}>
        <SurahSelector
          value={surahA}
          onChange={setSurahA}
          isRtl={isRtl}
          label={isRtl ? 'السورة الأولى' : 'Surah A'}
        />
        <div className="flex-shrink-0 text-gray-300 font-bold text-lg pb-3">vs</div>
        <SurahSelector
          value={surahB}
          onChange={setSurahB}
          isRtl={isRtl}
          label={isRtl ? 'السورة الثانية' : 'Surah B'}
        />
      </div>

      {/* Quick header cards */}
      <div className={clsx('grid grid-cols-2 gap-3 mb-6', isRtl && '')}>
        {[
          { num: surahA, data: dataA, color: 'violet' },
          { num: surahB, data: dataB, color: 'blue'   },
        ].map(({ num, data, color }) => (
          <div
            key={num}
            className={clsx(
              'rounded-2xl border p-4',
              color === 'violet' ? 'bg-violet-50 border-violet-200' : 'bg-blue-50 border-blue-200'
            )}
          >
            <p className={clsx(
              'text-xs font-semibold uppercase tracking-wide mb-1',
              color === 'violet' ? 'text-violet-500' : 'text-blue-500'
            )}>
              {isRtl ? `سورة ${num}` : `Surah ${num}`}
            </p>
            <p className={clsx('text-xl font-bold text-gray-900 leading-tight', isRtl && 'font-arabic')}>
              {isRtl ? data.name?.ar : data.name?.en}
            </p>
            {!isRtl && (
              <p className="text-xs text-gray-500 font-arabic mt-0.5">{data.name?.ar}</p>
            )}
            {isRtl && (
              <p className="text-xs text-gray-500 mt-0.5">{data.name?.en}</p>
            )}
            <p className={clsx('text-xs text-gray-400 mt-1', isRtl && 'font-arabic')}>
              {data.atlas?.ayahCount ?? '?'} {isRtl ? 'آية' : 'verses'}
            </p>
            {data.atlas && (
              <AyahBar count={data.atlas.ayahCount} maxCount={MAX_AYAHS} />
            )}
          </div>
        ))}
      </div>

      {/* Comparison table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden mb-6">
        <div className={clsx('grid grid-cols-3 bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wide', isRtl && 'flex-row-reverse')}>
          <div className={clsx('px-4 py-3 col-span-1', isRtl && 'text-right font-arabic')}>{isRtl ? 'المعيار' : 'Attribute'}</div>
          <div className={clsx('px-4 py-3 text-violet-600', isRtl ? 'text-right font-arabic' : 'text-center')}>
            {isRtl ? SURAH_NAMES[surahA - 1]?.ar : SURAH_NAMES[surahA - 1]?.en}
          </div>
          <div className={clsx('px-4 py-3 text-blue-600', isRtl ? 'text-right font-arabic' : 'text-center')}>
            {isRtl ? SURAH_NAMES[surahB - 1]?.ar : SURAH_NAMES[surahB - 1]?.en}
          </div>
        </div>

        {rows.map((row, i) => (
          <div
            key={i}
            className={clsx(
              'grid grid-cols-3 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors',
              row.highlight && 'bg-amber-50/40'
            )}
          >
            <div className={clsx('px-4 py-3 text-xs font-semibold text-gray-500', isRtl && 'text-right font-arabic')}>
              {isRtl ? row.labelAr : row.labelEn}
              {row.highlight && <span className="ms-1 text-amber-500">•</span>}
            </div>
            <div className={clsx('px-4 py-3 text-xs text-gray-800', isRtl ? 'text-right font-arabic' : 'text-center')}>
              {row.renderA ?? '—'}
            </div>
            <div className={clsx('px-4 py-3 text-xs text-gray-800', isRtl ? 'text-right font-arabic' : 'text-center')}>
              {row.renderB ?? '—'}
            </div>
          </div>
        ))}
      </div>

      {/* Summaries */}
      {(summaryA || summaryB) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {[
            { summary: summaryA, name: isRtl ? dataA.name?.ar : dataA.name?.en, color: 'violet' },
            { summary: summaryB, name: isRtl ? dataB.name?.ar : dataB.name?.en, color: 'blue'   },
          ].map(({ summary, name, color }) => summary ? (
            <div
              key={color}
              className={clsx(
                'rounded-2xl border p-4',
                color === 'violet' ? 'bg-violet-50/60 border-violet-100' : 'bg-blue-50/60 border-blue-100'
              )}
            >
              <p className={clsx(
                'text-xs font-bold mb-2',
                color === 'violet' ? 'text-violet-600' : 'text-blue-600',
                isRtl && 'font-arabic'
              )}>
                {name}
              </p>
              <p className={clsx('text-xs text-gray-600 leading-relaxed line-clamp-5', isRtl && 'font-arabic text-right')}>
                {summary}
              </p>
            </div>
          ) : null)}
        </div>
      )}

      <p className={clsx('text-[10px] text-gray-300 text-center', isRtl && 'font-arabic')}>
        {isRtl
          ? 'البيانات من أطلس السور · ترتيب النزول من رواية ابن عباس · سورة المصحف المصري'
          : 'Data from Surah Atlas · Revelation order per Ibn Abbas · Egyptian Standard Mushaf'}
      </p>
    </div>
  );
}
