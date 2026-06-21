/**
 * Quranic Duʿā Explorer
 *
 * Curated supplications from the Quran — Uthmanic Arabic text, transliteration,
 * meaning, context. Sorted by Quran order. Memorization mode included.
 *
 * Safety: all content referenced from exact surah:ayah.
 * No AI-generated meanings. Sources: Saheeh International / Hafs ʿan ʿĀṣim.
 */

import { useState, useMemo, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BookOpen, Search, ExternalLink, ChevronDown, ChevronUp,
  Heart, Copy, Check, Eye, EyeOff, BookMarked,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi } from '../lib/api';
import {
  QURANIC_DUAS, CATEGORY_META, type DuaCategory, type QuranicDua,
} from '../data/quranicDuas';

const ALL_CATEGORIES = Object.keys(CATEGORY_META) as DuaCategory[];

const ACCENT: Record<string, string> = {
  emerald: 'border-l-emerald-500 bg-emerald-50',
  amber:   'border-l-amber-500 bg-amber-50',
  violet:  'border-l-violet-500 bg-violet-50',
  rose:    'border-l-rose-500 bg-rose-50',
  blue:    'border-l-blue-500 bg-blue-50',
  orange:  'border-l-orange-500 bg-orange-50',
  yellow:  'border-l-yellow-500 bg-yellow-50',
  teal:    'border-l-teal-500 bg-teal-50',
  indigo:  'border-l-indigo-500 bg-indigo-50',
};

const BADGE: Record<string, string> = {
  emerald: 'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-200',
  amber:   'bg-amber-100 text-amber-700 ring-1 ring-amber-200',
  violet:  'bg-violet-100 text-violet-700 ring-1 ring-violet-200',
  rose:    'bg-rose-100 text-rose-700 ring-1 ring-rose-200',
  blue:    'bg-blue-100 text-blue-700 ring-1 ring-blue-200',
  orange:  'bg-orange-100 text-orange-700 ring-1 ring-orange-200',
  yellow:  'bg-yellow-100 text-yellow-700 ring-1 ring-yellow-200',
  teal:    'bg-teal-100 text-teal-700 ring-1 ring-teal-200',
  indigo:  'bg-indigo-100 text-indigo-700 ring-1 ring-indigo-200',
};

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handle = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(text).catch(() => null);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }, [text]);

  return (
    <button
      onClick={handle}
      title="Copy Arabic text"
      className="flex items-center gap-1 text-xs text-gray-400 hover:text-teal-600 transition-colors px-2 py-1 rounded-lg hover:bg-teal-50"
    >
      {copied
        ? <><Check className="w-3.5 h-3.5 text-teal-500" /><span className="text-teal-500">Copied</span></>
        : <><Copy className="w-3.5 h-3.5" /><span>Copy</span></>}
    </button>
  );
}

function DuaCard({
  dua, isRtl, memorizeMode, autoExpand,
}: {
  dua: QuranicDua;
  isRtl: boolean;
  memorizeMode: boolean;
  autoExpand: boolean;
}) {
  const [expanded, setExpanded] = useState(autoExpand);
  const [hideTranslit, setHideTranslit] = useState(false);
  const [hideMeaning, setHideMeaning] = useState(false);
  const meta = CATEGORY_META[dua.category];
  const accentClass = ACCENT[meta.color] ?? ACCENT.teal;
  const badgeClass  = BADGE[meta.color]  ?? BADGE.teal;

  const ref = isRtl ? dua.surahNameAr : dua.surahNameEn;
  const ayahRef = `${dua.surah}:${dua.ayah}${dua.ayahEnd ? `–${dua.ayahEnd}` : ''}`;

  // Fetch authoritative text_uthmani from backend (King Fahd / quran_uthmani.json)
  const { data: liveVerses } = useQuery({
    queryKey: ['dua-verses', dua.surah, dua.ayah, dua.ayahEnd ?? null],
    queryFn: async () => {
      if (dua.ayahEnd) {
        const res = await quranApi.getVerseRange(dua.surah, dua.ayah, dua.ayahEnd);
        return res.data;
      }
      const res = await quranApi.getVerse(dua.surah, dua.ayah);
      return [res.data];
    },
    enabled: expanded,
    staleTime: Infinity,
  });

  const displayedAyat = liveVerses
    ? liveVerses.map(v => v.text_imlaei).join(' ۝ ')
    : dua.ayatUthmani;

  return (
    <article className={clsx(
      'rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition-all duration-200',
      expanded ? `border-l-4 ${accentClass}` : 'bg-white',
    )}>
      {/* ── Header (always visible) ───────────────────────────────────────── */}
      <div
        role="button"
        tabIndex={0}
        className={clsx(
          'px-4 pt-4 pb-3 cursor-pointer select-none flex gap-3',
          isRtl ? 'flex-row-reverse' : 'flex-row',
        )}
        onClick={() => setExpanded(v => !v)}
        onKeyDown={e => e.key === 'Enter' && setExpanded(v => !v)}
      >
        {/* Emoji */}
        <span className="text-xl flex-shrink-0 mt-0.5">{meta.emoji}</span>

        {/* Title block */}
        <div className="flex-1 min-w-0">
          {/* Badges row */}
          <div className={clsx('flex flex-wrap items-center gap-1.5 mb-1.5', isRtl && 'flex-row-reverse')}>
            <span className={clsx('text-[11px] font-medium px-2 py-0.5 rounded-full', badgeClass)}>
              {isRtl ? meta.labelAr : meta.labelEn}
            </span>
            {dua.prophet && (
              <span className="text-[11px] bg-amber-50 text-amber-700 ring-1 ring-amber-200 px-2 py-0.5 rounded-full">
                {dua.prophet}
              </span>
            )}
          </div>
          {/* Title */}
          <h3 className={clsx(
            'font-semibold text-gray-800 text-sm leading-snug',
            isRtl && 'font-arabic text-right',
          )}>
            {isRtl ? dua.titleAr : dua.titleEn}
          </h3>
          {/* Reference */}
          <p className={clsx('text-[11px] text-gray-400 mt-0.5', isRtl && 'font-arabic text-right')}>
            {ref} · {ayahRef}
          </p>
        </div>

        {/* Chevron */}
        <span className="flex-shrink-0 mt-1 text-gray-300">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </span>
      </div>

      {/* ── Body (expanded) ───────────────────────────────────────────────── */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100">

          {/* Arabic Ayat — prominent, fetched from King Fahd / quran_uthmani.json */}
          <div className="bg-white rounded-xl p-4 mt-3 border border-gray-100 shadow-inner">
            <div className={clsx('flex justify-end gap-2 mb-2', isRtl && 'flex-row-reverse justify-start')}>
              <CopyButton text={displayedAyat} />
            </div>
            <p
              className="font-arabic text-xl leading-[2.2] text-gray-900 text-right"
              dir="rtl"
              lang="ar"
            >
              {displayedAyat}
            </p>
          </div>

          {/* Transliteration — hidden in Arabic mode */}
          {!isRtl && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                  Transliteration
                </span>
                {memorizeMode && (
                  <button
                    onClick={() => setHideTranslit(v => !v)}
                    className="text-[10px] text-gray-400 hover:text-teal-600 flex items-center gap-1"
                  >
                    {hideTranslit ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                    {hideTranslit ? 'Show' : 'Hide'}
                  </button>
                )}
              </div>
              {!hideTranslit && (
                <p className="text-sm text-gray-600 italic leading-relaxed font-light tracking-wide">
                  {dua.transliterationArabic}
                </p>
              )}
            </div>
          )}

          {/* Meaning / Arabic explanation */}
          <div className="space-y-1">
            <div className={clsx('flex items-center justify-between', isRtl && 'flex-row-reverse')}>
              <span className={clsx('text-[10px] font-semibold uppercase tracking-wider text-gray-400', isRtl && 'font-arabic normal-case')}>
                {isRtl ? 'الشرح' : 'Meaning'}
              </span>
              {memorizeMode && (
                <button
                  onClick={() => setHideMeaning(v => !v)}
                  className="text-[10px] text-gray-400 hover:text-teal-600 flex items-center gap-1"
                >
                  {hideMeaning ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                  {hideMeaning ? (isRtl ? 'إظهار' : 'Show') : (isRtl ? 'إخفاء' : 'Hide')}
                </button>
              )}
            </div>
            {!hideMeaning && (
              isRtl ? (
                <p className="font-arabic text-sm text-gray-700 leading-relaxed text-right" dir="rtl">
                  {dua.meaningAr}
                </p>
              ) : (
                <p className="text-sm text-gray-700 leading-relaxed">
                  <span className="text-gray-400">"</span>
                  {dua.meaningEn}
                  <span className="text-gray-400">"</span>
                </p>
              )
            )}
          </div>

          {/* Hadith support — Arabic mode only */}
          {isRtl && dua.hadithAr && (
            <div className="rounded-xl border border-amber-100 bg-amber-50 px-3 py-2.5">
              <p className="text-[10px] font-semibold text-amber-600 mb-1 text-right font-arabic">شاهد من السنة</p>
              <p className="font-arabic text-xs text-amber-900 leading-relaxed text-right" dir="rtl">
                {dua.hadithAr}
              </p>
            </div>
          )}

          {/* Context */}
          <div className={clsx('rounded-xl px-3 py-2.5', ACCENT[meta.color] ?? ACCENT.teal)}>
            <p className={clsx('text-xs text-gray-700 leading-relaxed', isRtl && 'font-arabic text-right')}>
              {isRtl ? dua.contextAr : dua.contextEn}
            </p>
          </div>

          {/* Tags */}
          <div className={clsx('flex flex-wrap gap-1', isRtl && 'flex-row-reverse')}>
            {dua.tags.map(tag => (
              <span key={tag} className="text-[10px] bg-gray-100 text-gray-400 px-2 py-0.5 rounded-full">
                #{tag}
              </span>
            ))}
          </div>

          {/* Read in Mushaf */}
          <Link
            to={`/quran/${dua.surah}?aya=${dua.ayah}`}
            className={clsx(
              'inline-flex items-center gap-1.5 text-xs font-medium text-teal-700 hover:text-teal-900 transition-colors',
              isRtl && 'flex-row-reverse',
            )}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            {isRtl
              ? `اقرأ في المصحف — ${dua.surahNameAr} ${ayahRef}`
              : `Read in Muṣḥaf — ${dua.surahNameEn} ${ayahRef}`}
          </Link>
        </div>
      )}
    </article>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────────

export function DuasPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<DuaCategory | 'all'>('all');
  const [memorizeMode, setMemorizeMode] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Category counts
  const categoryCounts = useMemo(() => {
    const counts: Partial<Record<DuaCategory | 'all', number>> = { all: QURANIC_DUAS.length };
    for (const d of QURANIC_DUAS) {
      counts[d.category] = (counts[d.category] ?? 0) + 1;
    }
    return counts;
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    return QURANIC_DUAS.filter(d => {
      const matchCat = selectedCategory === 'all' || d.category === selectedCategory;
      if (!matchCat) return false;
      if (!q) return true;
      return (
        d.titleEn.toLowerCase().includes(q) ||
        d.titleAr.includes(q) ||
        d.meaningEn.toLowerCase().includes(q) ||
        d.transliterationArabic.toLowerCase().includes(q) ||
        d.tags.some(t => t.includes(q)) ||
        d.surahNameEn.toLowerCase().includes(q) ||
        d.surahNameAr.includes(q) ||
        (d.prophet?.toLowerCase().includes(q) ?? false)
      );
    });
  }, [search, selectedCategory]);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 pb-16" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div className="mb-6 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 shadow-lg mb-4">
          <BookOpen className="w-7 h-7 text-white" />
        </div>
        <h1 className={clsx('text-2xl font-bold text-gray-900 mb-1', isRtl && 'font-arabic')}>
          {isRtl ? 'أدعية القرآن الكريم' : 'Quranic Duʿā'}
        </h1>
        <p className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
          {isRtl
            ? `${QURANIC_DUAS.length} دعاء مُرتَّب حسب ترتيب القرآن — بالنص العثماني والتشكيل والترجمة`
            : `${QURANIC_DUAS.length} supplications in Quranic order — Uthmanic text, transliteration & meaning`}
        </p>

        {/* Memorize Mode toggle */}
        <button
          onClick={() => setMemorizeMode(v => !v)}
          className={clsx(
            'mt-4 inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all',
            memorizeMode
              ? 'bg-teal-600 text-white shadow-md shadow-teal-200'
              : 'bg-white border border-gray-200 text-gray-600 hover:border-teal-300 hover:text-teal-700',
          )}
        >
          <BookMarked className="w-4 h-4" />
          {memorizeMode
            ? (isRtl ? 'وضع الحفظ مفعّل' : 'Memorize Mode ON')
            : (isRtl ? 'وضع الحفظ' : 'Memorize Mode')}
        </button>
        {memorizeMode && (
          <p className="text-xs text-teal-600 mt-1.5">
            {isRtl ? 'اضغط 👁️ لإخفاء أو إظهار التشكيل والترجمة' : 'Use the 👁️ buttons to hide/reveal transliteration & meaning'}
          </p>
        )}
      </div>

      {/* ── Search ───────────────────────────────────────────────────────── */}
      <div className="relative mb-4">
        <Search className={clsx(
          'absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400',
          isRtl ? 'right-3' : 'left-3',
        )} />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={isRtl ? 'ابحث في الأدعية أو الأنبياء أو المواضيع...' : 'Search duʿā, prophet, or topic...'}
          className={clsx(
            'w-full bg-white border border-gray-200 rounded-xl py-2.5 text-sm',
            'focus:ring-2 focus:ring-teal-300 focus:border-teal-400 outline-none transition',
            isRtl ? 'pr-9 pl-3 text-right font-arabic' : 'pl-9 pr-3',
          )}
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className={clsx(
              'absolute top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600',
              isRtl ? 'left-3' : 'right-3',
            )}
          >
            ✕
          </button>
        )}
      </div>

      {/* ── Category pills (horizontal scroll) ───────────────────────────── */}
      <div
        ref={scrollRef}
        className={clsx(
          'flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-hide',
          isRtl && 'flex-row-reverse',
        )}
      >
        <button
          onClick={() => setSelectedCategory('all')}
          className={clsx(
            'flex-shrink-0 text-xs px-3 py-1.5 rounded-full border transition-all whitespace-nowrap',
            selectedCategory === 'all'
              ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
              : 'text-gray-600 border-gray-200 bg-white hover:border-teal-300',
          )}
        >
          {isRtl ? 'الكل' : 'All'} · {categoryCounts.all}
        </button>

        {ALL_CATEGORIES.map(cat => {
          const meta = CATEGORY_META[cat];
          const active = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={clsx(
                'flex-shrink-0 flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all whitespace-nowrap',
                active
                  ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                  : 'text-gray-600 border-gray-200 bg-white hover:border-teal-300',
              )}
            >
              {meta.emoji}
              <span>{isRtl ? meta.labelAr : meta.labelEn}</span>
              {categoryCounts[cat] != null && (
                <span className={clsx('text-[10px]', active ? 'text-teal-100' : 'text-gray-400')}>
                  {categoryCounts[cat]}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Result count ─────────────────────────────────────────────────── */}
      <p className={clsx('text-xs text-gray-400 mb-3', isRtl && 'font-arabic text-right')}>
        {isRtl
          ? `عرض ${filtered.length} من ${QURANIC_DUAS.length} دعاء`
          : `Showing ${filtered.length} of ${QURANIC_DUAS.length} duʿā`}
        {search && ` · "${search}"`}
      </p>

      {/* ── Dua list ─────────────────────────────────────────────────────── */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-300">
          <BookOpen className="w-12 h-12 mx-auto mb-3" />
          <p className={clsx('text-sm', isRtl && 'font-arabic')}>
            {isRtl ? 'لا توجد نتائج' : 'No results found'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(dua => (
            <DuaCard
              key={dua.id}
              dua={dua}
              isRtl={isRtl}
              memorizeMode={memorizeMode}
              autoExpand={false}
            />
          ))}
        </div>
      )}

      {/* ── Attribution ──────────────────────────────────────────────────── */}
      <footer className={clsx('mt-10 text-center', isRtl && 'font-arabic')}>
        <p className="text-xs text-gray-300 flex items-center justify-center gap-1.5">
          <Heart className="w-3.5 h-3.5 text-rose-300" />
          {isRtl
            ? 'النص القرآني: حفص عن عاصم · الترجمة: صحيح إنترناشيونال · لا محتوى مُولَّد بالذكاء الاصطناعي'
            : "Arabic: Ḥafṣ ʿan ʿĀṣim · English: Saheeh International · No AI-generated content"}
        </p>
        <p className="text-[10px] text-gray-300 mt-1">
          {isRtl ? 'كل دعاء مرتبط بمرجعه القرآني الدقيق' : 'Every duʿā linked to its exact Quranic reference'}
        </p>
      </footer>
    </div>
  );
}
