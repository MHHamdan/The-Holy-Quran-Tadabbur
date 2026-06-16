/**
 * Quranic Roots Explorer — trilateral Arabic roots and their word families.
 *
 * Educational tool: shows the root, its core meaning, and all major
 * derivatives with frequency counts and example references.
 *
 * No Quran text is embedded here — example refs are links to the Mushaf.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Network, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  ROOT_FAMILIES,
  ROOT_CATEGORY_META,
  type RootCategory,
} from '../data/quranicRoots';

const COLOR_MAP: Record<string, { bg: string; border: string; badge: string; bar: string; highlight: string }> = {
  emerald: { bg: 'bg-emerald-50',  border: 'border-emerald-200',  badge: 'bg-emerald-100 text-emerald-700',  bar: 'bg-emerald-400', highlight: 'text-emerald-700' },
  blue:    { bg: 'bg-blue-50',    border: 'border-blue-200',    badge: 'bg-blue-100 text-blue-700',      bar: 'bg-blue-400',    highlight: 'text-blue-700'    },
  violet:  { bg: 'bg-violet-50',  border: 'border-violet-200',  badge: 'bg-violet-100 text-violet-700',  bar: 'bg-violet-400',  highlight: 'text-violet-700'  },
  indigo:  { bg: 'bg-indigo-50',  border: 'border-indigo-200',  badge: 'bg-indigo-100 text-indigo-700',  bar: 'bg-indigo-400',  highlight: 'text-indigo-700'  },
  amber:   { bg: 'bg-amber-50',   border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-700',    bar: 'bg-amber-400',   highlight: 'text-amber-700'   },
  rose:    { bg: 'bg-rose-50',    border: 'border-rose-200',    badge: 'bg-rose-100 text-rose-700',      bar: 'bg-rose-400',    highlight: 'text-rose-700'    },
};

const CATEGORIES = Object.keys(ROOT_CATEGORY_META) as RootCategory[];
const MAX_OCC = Math.max(...ROOT_FAMILIES.map(r => r.totalOccurrences));

function parseRef(ref: string): { surah: number; ayah: number } | null {
  const parts = ref.split(':');
  if (parts.length !== 2) return null;
  const surah = parseInt(parts[0]);
  const ayah = parseInt(parts[1]);
  if (isNaN(surah) || isNaN(ayah)) return null;
  return { surah, ayah };
}

export function QuranicRootsPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [catFilter, setCatFilter] = useState<RootCategory | 'all'>('all');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');

  function toggle(id: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  const filtered = ROOT_FAMILIES.filter(r => {
    if (catFilter !== 'all' && r.category !== catFilter) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      r.rootTransliteration.toLowerCase().includes(q) ||
      r.rootArabic.includes(search) ||
      r.coreMeaningEn.toLowerCase().includes(q) ||
      r.coreMeaningAr.includes(search)
    );
  });

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-4', isRtl && 'flex-row-reverse')}>
        <Network className="w-7 h-7 text-blue-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'مستكشف الجذور القرآنية' : 'Quranic Roots Explorer'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl
              ? `${ROOT_FAMILIES.length} جذر مع عائلاتها الاشتقاقية في القرآن`
              : `${ROOT_FAMILIES.length} roots with their word families in the Quran`}
          </p>
        </div>
      </div>

      {/* Search */}
      <input
        type="text"
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder={isRtl ? 'ابحث عن جذر أو معنى…' : 'Search root or meaning…'}
        dir={isRtl ? 'rtl' : 'ltr'}
        className={clsx(
          'w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm mb-3 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
          isRtl && 'font-arabic text-right'
        )}
      />

      {/* Category filter */}
      <div className={clsx('flex flex-wrap gap-1.5 mb-5', isRtl && 'flex-row-reverse')}>
        <button
          onClick={() => setCatFilter('all')}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            catFilter === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'text-gray-500 border-gray-200 hover:bg-gray-50'
          )}
        >
          {isRtl ? 'الكل' : 'All'}
        </button>
        {CATEGORIES.map(cat => {
          const meta = ROOT_CATEGORY_META[cat];
          const styles = COLOR_MAP[meta.color] ?? COLOR_MAP.blue;
          return (
            <button
              key={cat}
              onClick={() => setCatFilter(cat === catFilter ? 'all' : cat)}
              className={clsx(
                'text-xs px-2.5 py-1 rounded-full border transition-colors',
                catFilter === cat ? `${styles.badge} border-transparent` : 'text-gray-500 border-gray-200 hover:bg-gray-50'
              )}
            >
              {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
            </button>
          );
        })}
      </div>

      {/* Root cards */}
      <div className="space-y-3">
        {filtered.map(root => {
          const meta = ROOT_CATEGORY_META[root.category];
          const styles = COLOR_MAP[meta.color] ?? COLOR_MAP.blue;
          const isExpanded = expanded.has(root.id);
          const barPct = Math.max(6, (root.totalOccurrences / MAX_OCC) * 100);

          return (
            <div
              key={root.id}
              className={clsx(
                'rounded-2xl border overflow-hidden transition-shadow hover:shadow-sm',
                isExpanded ? `${styles.bg} ${styles.border}` : 'bg-white border-gray-100'
              )}
            >
              {/* Header row — always clickable */}
              <button
                onClick={() => toggle(root.id)}
                className="w-full text-left p-4"
              >
                <div className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
                  {/* Root letters */}
                  <div className={clsx(
                    'flex-shrink-0 min-w-[72px] rounded-xl px-3 py-2 text-center border',
                    styles.bg, styles.border
                  )}>
                    <p className={clsx('text-xl font-bold font-arabic leading-tight', styles.highlight)} dir="rtl">
                      {root.rootArabic}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-0.5">{root.rootTransliteration}</p>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className={clsx('flex items-center gap-1.5 mb-0.5 flex-wrap', isRtl && 'flex-row-reverse')}>
                      <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full', styles.badge)}>
                        {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
                      </span>
                      <span className="text-[10px] text-gray-400">
                        ~{root.totalOccurrences.toLocaleString()} {isRtl ? 'وردت' : 'occurrences'}
                      </span>
                    </div>
                    <p className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic text-right')}>
                      {isRtl ? root.coreMeaningAr : root.coreMeaningEn}
                    </p>

                    {/* Frequency bar */}
                    <div className="mt-1.5 w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                      <div className={clsx('h-full rounded-full', styles.bar)} style={{ width: `${barPct}%` }} />
                    </div>
                  </div>

                  <div className="flex-shrink-0 text-gray-300">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>
              </button>

              {/* Expanded: note + derivatives table */}
              {isExpanded && (
                <div className="border-t border-gray-100 px-4 pb-4 pt-3">
                  {/* Note */}
                  <p className={clsx('text-xs text-gray-600 italic mb-4 leading-relaxed', isRtl && 'font-arabic text-right')}>
                    {isRtl ? root.noteAr : root.noteEn}
                  </p>

                  {/* Derivatives */}
                  <div className="space-y-2">
                    {root.derivatives.map((d, i) => {
                      const ref = d.exampleRef ? parseRef(d.exampleRef) : null;
                      return (
                        <div key={i} className={clsx(
                          'flex gap-3 p-3 bg-white/70 rounded-xl border border-gray-100',
                          isRtl && 'flex-row-reverse'
                        )}>
                          {/* Arabic word */}
                          <div className="flex-shrink-0 text-center min-w-[64px]">
                            <p className={clsx('text-lg font-bold font-arabic', styles.highlight)} dir="rtl">
                              {d.arabic}
                            </p>
                            <p className="text-[10px] text-gray-400">{d.transliteration}</p>
                          </div>

                          <div className="flex-1 min-w-0">
                            <p className={clsx('text-xs font-semibold text-gray-800', isRtl && 'font-arabic text-right')}>
                              {isRtl ? d.meaningAr : d.meaningEn}
                            </p>
                            <p className={clsx('text-[10px] text-gray-400 mt-0.5', isRtl && 'font-arabic text-right')}>
                              {d.partOfSpeech}
                            </p>
                          </div>

                          {/* Frequency + ref */}
                          <div className={clsx('flex-shrink-0 text-right', isRtl && 'text-left')}>
                            <p className="text-xs font-bold text-gray-600">×{d.frequencyInQuran}</p>
                            {ref && (
                              <Link
                                to={`/quran/${ref.surah}?ayah=${ref.ayah}`}
                                className={clsx('text-[10px] text-blue-500 hover:underline flex items-center gap-0.5', isRtl && 'flex-row-reverse')}
                                onClick={e => e.stopPropagation()}
                              >
                                {d.exampleRef}
                                <ExternalLink className="w-2.5 h-2.5" />
                              </Link>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'المصادر: مجموعة المتن القرآني العربي · قاموس لين · هانز فير'
          : 'Sources: Quranic Arabic Corpus · Lane\'s Lexicon · Hans Wehr Dictionary'}
      </p>
    </div>
  );
}
