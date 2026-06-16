/**
 * Daily Dhikr Counter — tally-based remembrance tracker.
 *
 * Counts persist per day in localStorage.
 * Haptic feedback on count if supported.
 * No backend — fully offline.
 */

import { useState, useCallback } from 'react';
import { RotateCcw, ChevronDown, ChevronUp, Info } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { ADHKAR, CATEGORY_META, type DhikrCategory, type DhikrEntry } from '../data/adhkar';

const STORAGE_KEY = 'tadabbur_dhikr_v1';
const TODAY = new Date().toISOString().slice(0, 10);

type CountRecord = Record<string, { count: number; date: string }>;

function loadCounts(): CountRecord {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as CountRecord) : {};
  } catch { return {}; }
}

function saveCounts(record: CountRecord) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(record));
  } catch { /* ignore */ }
}

function getCount(record: CountRecord, id: string): number {
  const entry = record[id];
  if (!entry || entry.date !== TODAY) return 0;
  return entry.count;
}

function vibrate() {
  try {
    if (navigator.vibrate) navigator.vibrate(15);
  } catch { /* ignore */ }
}

const COLOR_CLASSES: Record<string, { bg: string; ring: string; button: string; progress: string; badge: string }> = {
  amber:   { bg: 'bg-amber-50',   ring: 'ring-amber-300',   button: 'bg-amber-500 hover:bg-amber-600 active:bg-amber-700',   progress: 'bg-amber-400',   badge: 'bg-amber-100 text-amber-700' },
  indigo:  { bg: 'bg-indigo-50',  ring: 'ring-indigo-300',  button: 'bg-indigo-500 hover:bg-indigo-600 active:bg-indigo-700', progress: 'bg-indigo-400',  badge: 'bg-indigo-100 text-indigo-700' },
  emerald: { bg: 'bg-emerald-50', ring: 'ring-emerald-300', button: 'bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700', progress: 'bg-emerald-400', badge: 'bg-emerald-100 text-emerald-700' },
  violet:  { bg: 'bg-violet-50',  ring: 'ring-violet-300',  button: 'bg-violet-500 hover:bg-violet-600 active:bg-violet-700', progress: 'bg-violet-400',  badge: 'bg-violet-100 text-violet-700' },
  teal:    { bg: 'bg-teal-50',    ring: 'ring-teal-300',    button: 'bg-teal-500 hover:bg-teal-600 active:bg-teal-700',   progress: 'bg-teal-400',    badge: 'bg-teal-100 text-teal-700' },
};

function DhikrCard({
  dhikr,
  count,
  isRtl,
  onIncrement,
  onReset,
}: {
  dhikr: DhikrEntry;
  count: number;
  isRtl: boolean;
  onIncrement: () => void;
  onReset: () => void;
}) {
  const [showInfo, setShowInfo] = useState(false);
  const catMeta = CATEGORY_META[dhikr.category];
  const colors = COLOR_CLASSES[catMeta.color] ?? COLOR_CLASSES.violet;
  const done = count >= dhikr.targetCount;
  const pct = Math.min((count / dhikr.targetCount) * 100, 100);

  return (
    <div className={clsx('rounded-2xl border border-gray-100 overflow-hidden', done && 'opacity-80')}>
      {/* Top section — tap to count */}
      <div
        className={clsx('p-4 cursor-pointer select-none', colors.bg)}
        onClick={() => {
          if (!done) { onIncrement(); vibrate(); }
        }}
      >
        {/* Category badge */}
        <div className={clsx('flex items-center justify-between mb-3', isRtl && 'flex-row-reverse')}>
          <span className={clsx('text-[10px] px-2 py-0.5 rounded-full font-medium', colors.badge)}>
            {catMeta.emoji} {isRtl ? catMeta.labelAr : catMeta.labelEn}
          </span>
          <div className={clsx('flex items-center gap-1.5', isRtl && 'flex-row-reverse')}>
            {count > 0 && !done && (
              <button
                onClick={e => { e.stopPropagation(); onReset(); }}
                className="p-1 rounded-lg text-gray-400 hover:text-red-400 hover:bg-white/60 transition-colors"
                title={isRtl ? 'إعادة تعيين' : 'Reset'}
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={e => { e.stopPropagation(); setShowInfo(v => !v); }}
              className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-white/60 transition-colors"
            >
              <Info className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Arabic phrase */}
        <p className="font-arabic text-2xl text-gray-900 leading-loose text-center mb-1 dir-rtl" dir="rtl">
          {dhikr.arabicPhrase}
        </p>
        <p className="text-xs text-gray-500 text-center mb-3">{dhikr.transliteration}</p>

        {/* Progress */}
        <div className="w-full h-2 bg-white/60 rounded-full overflow-hidden mb-2">
          <div
            className={clsx('h-full rounded-full transition-all duration-200', colors.progress)}
            style={{ width: `${pct}%` }}
          />
        </div>

        {/* Count display */}
        <div className={clsx('flex items-center justify-between', isRtl && 'flex-row-reverse')}>
          <span className={clsx('text-3xl font-bold tabular-nums', done ? 'text-emerald-600' : 'text-gray-800')}>
            {count}
          </span>
          <span className="text-xs text-gray-400">
            {done
              ? (isRtl ? '✅ مكتمل' : '✅ Done')
              : `/${dhikr.targetCount}`
            }
          </span>
        </div>
      </div>

      {/* Tap hint */}
      {!done && (
        <div className={clsx(
          'flex items-center justify-center py-2.5 cursor-pointer select-none transition-opacity active:opacity-70',
          colors.button
        )} onClick={() => { onIncrement(); vibrate(); }}>
          <span className="text-white text-sm font-medium">
            {isRtl ? 'اضغط للتسبيح' : 'Tap to count'}
          </span>
        </div>
      )}

      {/* Expandable info */}
      {showInfo && (
        <div className="bg-white px-4 py-3 border-t border-gray-100">
          <p className={clsx('text-xs text-gray-700 mb-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? dhikr.meaningAr : dhikr.meaningEn}
          </p>
          <p className={clsx('text-xs text-gray-500 mb-1', isRtl && 'font-arabic text-right')}>
            {isRtl ? dhikr.benefitAr : dhikr.benefitEn}
          </p>
          <p className="text-[10px] text-gray-400 italic">
            {isRtl ? dhikr.sourceRefAr : dhikr.sourceRef}
          </p>
        </div>
      )}
    </div>
  );
}

const CATS_ORDER: DhikrCategory[] = ['after_salah', 'quranic', 'any_time', 'morning', 'evening'];

export function DhikrPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [counts, setCounts] = useState<CountRecord>(loadCounts);
  const [activeCategory, setActiveCategory] = useState<DhikrCategory | 'all'>('all');
  const [collapsedCats, setCollapsedCats] = useState<Set<string>>(new Set());

  const increment = useCallback((id: string) => {
    setCounts(prev => {
      const current = getCount(prev, id);
      const next = { ...prev, [id]: { count: current + 1, date: TODAY } };
      saveCounts(next);
      return next;
    });
  }, []);

  const reset = useCallback((id: string) => {
    setCounts(prev => {
      const next = { ...prev, [id]: { count: 0, date: TODAY } };
      saveCounts(next);
      return next;
    });
  }, []);

  const resetAll = () => {
    const next: CountRecord = {};
    ADHKAR.forEach(d => { next[d.id] = { count: 0, date: TODAY }; });
    saveCounts(next);
    setCounts(next);
  };

  function toggleCat(cat: string) {
    setCollapsedCats(prev => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  }

  const filtered = activeCategory === 'all'
    ? ADHKAR
    : ADHKAR.filter(d => d.category === activeCategory);

  const totalDone = ADHKAR.filter(d => getCount(counts, d.id) >= d.targetCount).length;

  const grouped: Record<DhikrCategory, DhikrEntry[]> = {
    after_salah: [], quranic: [], any_time: [], morning: [], evening: [],
  };
  filtered.forEach(d => grouped[d.category].push(d));

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center justify-between mb-4', isRtl && 'flex-row-reverse')}>
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'التسبيح اليومي' : 'Daily Dhikr'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {totalDone}/{ADHKAR.length} {isRtl ? 'مكتمل اليوم' : 'complete today'}
          </p>
        </div>
        {totalDone > 0 && (
          <button
            onClick={() => { if (window.confirm(isRtl ? 'إعادة تعيين اليوم؟' : 'Reset today?')) resetAll(); }}
            className={clsx('flex items-center gap-1.5 text-xs text-gray-400 hover:text-red-400 transition-colors', isRtl && 'flex-row-reverse')}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            {isRtl ? 'إعادة' : 'Reset'}
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-5">
        <div
          className="h-full bg-emerald-500 rounded-full transition-all"
          style={{ width: `${ADHKAR.length > 0 ? (totalDone / ADHKAR.length) * 100 : 0}%` }}
        />
      </div>

      {/* Category filter */}
      <div className={clsx('flex flex-wrap gap-1.5 mb-5', isRtl && 'flex-row-reverse')}>
        <button
          onClick={() => setActiveCategory('all')}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            activeCategory === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'text-gray-500 border-gray-200 hover:bg-gray-50'
          )}
        >
          {isRtl ? 'الكل' : 'All'}
        </button>
        {CATS_ORDER.map(cat => {
          const meta = CATEGORY_META[cat];
          const colors = COLOR_CLASSES[meta.color] ?? COLOR_CLASSES.violet;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat === activeCategory ? 'all' : cat)}
              className={clsx(
                'text-xs px-2.5 py-1 rounded-full border transition-colors',
                activeCategory === cat ? `${colors.badge} border-transparent` : 'text-gray-500 border-gray-200 hover:bg-gray-50'
              )}
            >
              {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
            </button>
          );
        })}
      </div>

      {/* Grouped dhikr cards */}
      {activeCategory === 'all' ? (
        <div className="space-y-6">
          {CATS_ORDER.map(cat => {
            const items = grouped[cat];
            if (!items.length) return null;
            const meta = CATEGORY_META[cat];
            const collapsed = collapsedCats.has(cat);
            return (
              <div key={cat}>
                <button
                  onClick={() => toggleCat(cat)}
                  className={clsx('flex items-center gap-2 mb-3 w-full', isRtl && 'flex-row-reverse')}
                >
                  <span className="text-sm font-semibold text-gray-700">
                    {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
                  </span>
                  <span className="text-xs text-gray-400">({items.length})</span>
                  <span className={clsx('ms-auto text-gray-400', isRtl && 'me-auto ms-0')}>
                    {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                  </span>
                </button>
                {!collapsed && (
                  <div className="space-y-3">
                    {items.map(d => (
                      <DhikrCard
                        key={d.id}
                        dhikr={d}
                        count={getCount(counts, d.id)}
                        isRtl={isRtl}
                        onIncrement={() => increment(d.id)}
                        onReset={() => reset(d.id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(d => (
            <DhikrCard
              key={d.id}
              dhikr={d}
              count={getCount(counts, d.id)}
              isRtl={isRtl}
              onIncrement={() => increment(d.id)}
              onReset={() => reset(d.id)}
            />
          ))}
        </div>
      )}

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'يُعاد التعيين تلقائياً كل يوم • لا يُرفع إلى أي خادم'
          : 'Auto-resets each day · Never uploaded anywhere'}
      </p>
    </div>
  );
}
