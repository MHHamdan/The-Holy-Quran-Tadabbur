/**
 * Quranic Duʿā Explorer — enhanced with occasion & prophet filters,
 * bookmarks (localStorage), daily duʿā, and share.
 *
 * Safety: all content referenced from exact surah:ayah.
 * No AI-generated meanings. Sources: Saheeh International / Hafs ʿan ʿĀṣim.
 */

import { useState, useMemo, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BookOpen, Search, ExternalLink, ChevronDown, ChevronUp,
  Heart, Copy, Check, Eye, EyeOff, BookMarked, Share2, Shuffle,
  Star, X,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi } from '../lib/api';
import {
  QURANIC_DUAS, CATEGORY_META, OCCASION_META,
  type DuaCategory, type DuaOccasion, type QuranicDua,
} from '../data/quranicDuas';

const ALL_CATEGORIES = Object.keys(CATEGORY_META) as DuaCategory[];
const ALL_OCCASIONS  = Object.keys(OCCASION_META)  as DuaOccasion[];

// Collect all distinct prophet names
const ALL_PROPHETS = Array.from(
  new Set(QURANIC_DUAS.map(d => d.prophet).filter(Boolean) as string[])
).sort();

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

const LS_KEY = 'tadabbur_dua_favorites';

function loadFavorites(): Set<string> {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? new Set(JSON.parse(raw) as string[]) : new Set();
  } catch { return new Set(); }
}

function saveFavorites(ids: Set<string>) {
  localStorage.setItem(LS_KEY, JSON.stringify([...ids]));
}

function getDailyDuaId(): string {
  const dayIndex = Math.floor(Date.now() / 86_400_000) % QURANIC_DUAS.length;
  return QURANIC_DUAS[dayIndex].id;
}

// ─── Copy Button ───────────────────────────────────────────────────────────────

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

// ─── Share Button ─────────────────────────────────────────────────────────────

function ShareButton({ dua, isRtl }: { dua: QuranicDua; isRtl: boolean }) {
  const [shared, setShared] = useState(false);
  const ayahRef = `${dua.surah}:${dua.ayah}${dua.ayahEnd ? `–${dua.ayahEnd}` : ''}`;
  const handle = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    const text = [
      isRtl ? dua.titleAr : dua.titleEn,
      '',
      dua.ayatUthmani,
      '',
      isRtl ? dua.meaningAr : `"${dua.meaningEn}"`,
      '',
      `— ${isRtl ? dua.surahNameAr : dua.surahNameEn} ${ayahRef}`,
    ].join('\n');
    if (navigator.share) {
      await navigator.share({ text }).catch(() => null);
    } else {
      await navigator.clipboard.writeText(text).catch(() => null);
    }
    setShared(true);
    setTimeout(() => setShared(false), 1800);
  }, [dua, isRtl, ayahRef]);
  return (
    <button
      onClick={handle}
      title={isRtl ? 'مشاركة' : 'Share'}
      className="flex items-center gap-1 text-xs text-gray-400 hover:text-violet-600 transition-colors px-2 py-1 rounded-lg hover:bg-violet-50"
    >
      {shared
        ? <><Check className="w-3.5 h-3.5 text-violet-500" /><span className="text-violet-500">{isRtl ? 'تمت' : 'Shared'}</span></>
        : <><Share2 className="w-3.5 h-3.5" /><span>{isRtl ? 'شارك' : 'Share'}</span></>}
    </button>
  );
}

// ─── DuaCard ─────────────────────────────────────────────────────────────────

function DuaCard({
  dua, isRtl, memorizeMode, autoExpand, isFavorite, onToggleFavorite, isDaily,
}: {
  dua: QuranicDua;
  isRtl: boolean;
  memorizeMode: boolean;
  autoExpand: boolean;
  isFavorite: boolean;
  onToggleFavorite: (id: string) => void;
  isDaily?: boolean;
}) {
  const [expanded, setExpanded] = useState(autoExpand);
  const [hideTranslit, setHideTranslit] = useState(false);
  const [hideMeaning, setHideMeaning] = useState(false);
  const meta = CATEGORY_META[dua.category];
  const accentClass = ACCENT[meta.color] ?? ACCENT.teal;
  const badgeClass  = BADGE[meta.color]  ?? BADGE.teal;

  const ref = isRtl ? dua.surahNameAr : dua.surahNameEn;
  const ayahRef = `${dua.surah}:${dua.ayah}${dua.ayahEnd ? `–${dua.ayahEnd}` : ''}`;

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
      'rounded-2xl border overflow-hidden shadow-sm hover:shadow-md transition-all duration-200',
      isDaily && !expanded && 'ring-2 ring-amber-300 ring-offset-1',
      expanded ? `border-l-4 ${accentClass} border-gray-100` : 'bg-white border-gray-100',
    )}>
      {isDaily && (
        <div className="px-3 py-1 bg-amber-50 border-b border-amber-100 flex items-center gap-1.5">
          <Star className="w-3 h-3 text-amber-500 fill-amber-400" />
          <span className="text-[10px] font-medium text-amber-700">
            {isRtl ? 'دعاء اليوم' : "Today's Duʿā"}
          </span>
        </div>
      )}

      {/* ── Header ─────────────────────────────────────────────────────────── */}
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
        <span className="text-xl flex-shrink-0 mt-0.5">{meta.emoji}</span>

        <div className="flex-1 min-w-0">
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
          <h3 className={clsx(
            'font-semibold text-gray-800 text-sm leading-snug',
            isRtl && 'font-arabic text-right',
          )}>
            {isRtl ? dua.titleAr : dua.titleEn}
          </h3>
          <p className={clsx('text-[11px] text-gray-400 mt-0.5', isRtl && 'font-arabic text-right')}>
            {ref} · {ayahRef}
          </p>
        </div>

        {/* Favorite + Chevron */}
        <div className="flex-shrink-0 flex items-center gap-1 mt-1">
          <button
            onClick={e => { e.stopPropagation(); onToggleFavorite(dua.id); }}
            title={isFavorite ? 'Remove bookmark' : 'Bookmark'}
            className="p-1 rounded-lg hover:bg-rose-50 transition-colors"
          >
            <Heart className={clsx(
              'w-3.5 h-3.5 transition-colors',
              isFavorite ? 'fill-rose-400 text-rose-400' : 'text-gray-300 hover:text-rose-300',
            )} />
          </button>
          <span className="text-gray-300">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </span>
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────────── */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100">

          {/* Arabic Ayat */}
          <div className="bg-white rounded-xl p-4 mt-3 border border-gray-100 shadow-inner">
            <div className={clsx('flex justify-end gap-2 mb-2', isRtl && 'flex-row-reverse justify-start')}>
              <CopyButton text={displayedAyat} />
              <ShareButton dua={dua} isRtl={isRtl} />
            </div>
            <p
              className="font-arabic text-xl leading-[2.2] text-gray-900 text-right"
              dir="rtl"
              lang="ar"
            >
              {displayedAyat}
            </p>
          </div>

          {/* Transliteration */}
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

          {/* Meaning */}
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

          {/* Hadith */}
          {isRtl && dua.hadithAr && (
            <div className="rounded-xl border border-amber-100 bg-amber-50 px-3 py-2.5">
              <p className="text-[10px] font-semibold text-amber-600 mb-1 text-right font-arabic">شاهد من السنة</p>
              <p className="font-arabic text-xs text-amber-900 leading-relaxed text-right" dir="rtl">
                {dua.hadithAr}
              </p>
            </div>
          )}
          {!isRtl && dua.hadithAr && (
            <div className="rounded-xl border border-amber-100 bg-amber-50 px-3 py-2.5">
              <p className="text-[10px] font-semibold text-amber-600 mb-1">Prophetic Note</p>
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

          {/* Occasions */}
          {dua.occasions.length > 0 && (
            <div className={clsx('flex flex-wrap gap-1', isRtl && 'flex-row-reverse')}>
              <span className="text-[10px] text-gray-400 self-center mr-1">
                {isRtl ? 'متى يُقال:' : 'When to recite:'}
              </span>
              {dua.occasions.map(occ => (
                <span key={occ} className="text-[10px] bg-teal-50 text-teal-600 ring-1 ring-teal-100 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                  {OCCASION_META[occ].emoji} {isRtl ? OCCASION_META[occ].labelAr : OCCASION_META[occ].labelEn}
                </span>
              ))}
            </div>
          )}

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

// ─── Page ─────────────────────────────────────────────────────────────────────

export function DuasPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [search, setSearch]                   = useState('');
  const [selectedCategory, setSelectedCategory] = useState<DuaCategory | 'all'>('all');
  const [selectedOccasion, setSelectedOccasion] = useState<DuaOccasion | null>(null);
  const [selectedProphet, setSelectedProphet]   = useState<string | null>(null);
  const [memorizeMode, setMemorizeMode]         = useState(false);
  const [favoritesOnly, setFavoritesOnly]       = useState(false);
  const [favorites, setFavorites]               = useState<Set<string>>(loadFavorites);
  const [showOccasions, setShowOccasions]       = useState(false);
  const [showProphets, setShowProphets]         = useState(false);
  const [randomId, setRandomId]                 = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const dailyDuaId = useMemo(() => getDailyDuaId(), []);

  const toggleFavorite = useCallback((id: string) => {
    setFavorites(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      saveFavorites(next);
      return next;
    });
  }, []);

  const pickRandom = useCallback(() => {
    const pool = QURANIC_DUAS.filter(d => d.id !== randomId);
    const picked = pool[Math.floor(Math.random() * pool.length)];
    setRandomId(picked.id);
    // clear other filters so it shows
    setSearch('');
    setSelectedCategory('all');
    setSelectedOccasion(null);
    setSelectedProphet(null);
    setFavoritesOnly(false);
  }, [randomId]);

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
      if (favoritesOnly && !favorites.has(d.id)) return false;
      if (randomId && d.id !== randomId) return false;
      const matchCat  = selectedCategory === 'all' || d.category === selectedCategory;
      const matchOcc  = !selectedOccasion || d.occasions.includes(selectedOccasion);
      const matchProp = !selectedProphet || d.prophet === selectedProphet;
      if (!matchCat || !matchOcc || !matchProp) return false;
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
  }, [search, selectedCategory, selectedOccasion, selectedProphet, favoritesOnly, favorites, randomId]);

  const activeFilterCount = [
    selectedCategory !== 'all',
    !!selectedOccasion,
    !!selectedProphet,
    favoritesOnly,
  ].filter(Boolean).length;

  const clearFilters = () => {
    setSelectedCategory('all');
    setSelectedOccasion(null);
    setSelectedProphet(null);
    setFavoritesOnly(false);
    setRandomId(null);
    setSearch('');
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 pb-16" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* ── Hero ────────────────────────────────────────────────────────────── */}
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

        {/* Action row */}
        <div className={clsx('mt-4 flex flex-wrap items-center justify-center gap-2', isRtl && 'flex-row-reverse')}>
          <button
            onClick={() => setMemorizeMode(v => !v)}
            className={clsx(
              'inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all',
              memorizeMode
                ? 'bg-teal-600 text-white shadow-md shadow-teal-200'
                : 'bg-white border border-gray-200 text-gray-600 hover:border-teal-300 hover:text-teal-700',
            )}
          >
            <BookMarked className="w-4 h-4" />
            {memorizeMode
              ? (isRtl ? 'وضع الحفظ مفعّل' : 'Memorize ON')
              : (isRtl ? 'وضع الحفظ' : 'Memorize')}
          </button>

          <button
            onClick={() => { setFavoritesOnly(v => !v); setRandomId(null); }}
            className={clsx(
              'inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all',
              favoritesOnly
                ? 'bg-rose-500 text-white shadow-md shadow-rose-200'
                : 'bg-white border border-gray-200 text-gray-600 hover:border-rose-300 hover:text-rose-600',
            )}
          >
            <Heart className={clsx('w-4 h-4', favoritesOnly && 'fill-white')} />
            {isRtl ? 'المحفوظات' : 'Bookmarks'}
            {favorites.size > 0 && (
              <span className={clsx(
                'text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[1.2rem] text-center',
                favoritesOnly ? 'bg-white text-rose-500' : 'bg-rose-100 text-rose-600',
              )}>{favorites.size}</span>
            )}
          </button>

          <button
            onClick={pickRandom}
            className="inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all bg-white border border-gray-200 text-gray-600 hover:border-violet-300 hover:text-violet-700"
          >
            <Shuffle className="w-4 h-4" />
            {isRtl ? 'دعاء عشوائي' : 'Random'}
          </button>
        </div>

        {memorizeMode && (
          <p className="text-xs text-teal-600 mt-2">
            {isRtl ? 'اضغط 👁️ لإخفاء أو إظهار التشكيل والترجمة' : 'Use the 👁️ buttons to hide/reveal transliteration & meaning'}
          </p>
        )}
      </div>

      {/* ── Search ──────────────────────────────────────────────────────────── */}
      <div className="relative mb-4">
        <Search className={clsx(
          'absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400',
          isRtl ? 'right-3' : 'left-3',
        )} />
        <input
          type="text"
          value={search}
          onChange={e => { setSearch(e.target.value); setRandomId(null); }}
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
          ><X className="w-3.5 h-3.5" /></button>
        )}
      </div>

      {/* ── Category pills ──────────────────────────────────────────────────── */}
      <div
        ref={scrollRef}
        className={clsx('flex gap-2 overflow-x-auto pb-2 mb-2 scrollbar-hide', isRtl && 'flex-row-reverse')}
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
          const m = CATEGORY_META[cat];
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
              {m.emoji}
              <span>{isRtl ? m.labelAr : m.labelEn}</span>
              {categoryCounts[cat] != null && (
                <span className={clsx('text-[10px]', active ? 'text-teal-100' : 'text-gray-400')}>
                  {categoryCounts[cat]}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Occasion & Prophet toggles ───────────────────────────────────────── */}
      <div className={clsx('flex gap-2 mb-2', isRtl && 'flex-row-reverse')}>
        <button
          onClick={() => setShowOccasions(v => !v)}
          className={clsx(
            'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all',
            selectedOccasion
              ? 'bg-violet-600 text-white border-violet-600 shadow-sm'
              : 'text-gray-600 border-gray-200 bg-white hover:border-violet-300',
          )}
        >
          ⛈️ {isRtl ? 'المواقف' : 'Situations'}
          {selectedOccasion && <X className="w-3 h-3 opacity-70" onClick={e => { e.stopPropagation(); setSelectedOccasion(null); }} />}
        </button>
        <button
          onClick={() => setShowProphets(v => !v)}
          className={clsx(
            'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all',
            selectedProphet
              ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
              : 'text-gray-600 border-gray-200 bg-white hover:border-emerald-300',
          )}
        >
          🕌 {isRtl ? 'الأنبياء' : 'Prophets'}
          {selectedProphet && <X className="w-3 h-3 opacity-70" onClick={e => { e.stopPropagation(); setSelectedProphet(null); }} />}
        </button>
        {activeFilterCount > 0 && (
          <button onClick={clearFilters} className="text-xs text-gray-400 hover:text-red-500 transition-colors px-2">
            {isRtl ? 'مسح الكل' : 'Clear all'}
          </button>
        )}
      </div>

      {/* Occasions drawer */}
      {showOccasions && (
        <div className={clsx('flex flex-wrap gap-1.5 mb-3 p-3 bg-violet-50 rounded-xl border border-violet-100', isRtl && 'flex-row-reverse')}>
          {ALL_OCCASIONS.map(occ => {
            const m = OCCASION_META[occ];
            const active = selectedOccasion === occ;
            return (
              <button
                key={occ}
                onClick={() => { setSelectedOccasion(active ? null : occ); setShowOccasions(false); }}
                className={clsx(
                  'flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-all',
                  active
                    ? 'bg-violet-600 text-white border-violet-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-violet-300',
                )}
              >
                {m.emoji} {isRtl ? m.labelAr : m.labelEn}
              </button>
            );
          })}
        </div>
      )}

      {/* Prophets drawer */}
      {showProphets && (
        <div className={clsx('flex flex-wrap gap-1.5 mb-3 p-3 bg-emerald-50 rounded-xl border border-emerald-100', isRtl && 'flex-row-reverse')}>
          {ALL_PROPHETS.map(prophet => {
            const active = selectedProphet === prophet;
            return (
              <button
                key={prophet}
                onClick={() => { setSelectedProphet(active ? null : prophet); setShowProphets(false); }}
                className={clsx(
                  'text-xs px-2.5 py-1 rounded-full border transition-all',
                  active
                    ? 'bg-emerald-600 text-white border-emerald-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-emerald-300',
                )}
              >
                {prophet}
              </button>
            );
          })}
        </div>
      )}

      {/* Active filter indicators */}
      {(selectedOccasion || selectedProphet) && (
        <div className={clsx('flex flex-wrap gap-1.5 mb-3', isRtl && 'flex-row-reverse')}>
          {selectedOccasion && (
            <span className="inline-flex items-center gap-1 text-[11px] bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full">
              {OCCASION_META[selectedOccasion].emoji} {isRtl ? OCCASION_META[selectedOccasion].labelAr : OCCASION_META[selectedOccasion].labelEn}
              <button onClick={() => setSelectedOccasion(null)} className="hover:text-red-500">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
          {selectedProphet && (
            <span className="inline-flex items-center gap-1 text-[11px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
              🕌 {selectedProphet}
              <button onClick={() => setSelectedProphet(null)} className="hover:text-red-500">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
        </div>
      )}

      {/* ── Result count ────────────────────────────────────────────────────── */}
      <p className={clsx('text-xs text-gray-400 mb-3', isRtl && 'font-arabic text-right')}>
        {randomId
          ? (isRtl ? 'دعاء عشوائي' : 'Random pick')
          : (isRtl
              ? `عرض ${filtered.length} من ${QURANIC_DUAS.length} دعاء`
              : `Showing ${filtered.length} of ${QURANIC_DUAS.length} duʿā`)}
        {search && ` · "${search}"`}
      </p>

      {/* ── Dua list ────────────────────────────────────────────────────────── */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-300">
          <BookOpen className="w-12 h-12 mx-auto mb-3" />
          <p className={clsx('text-sm', isRtl && 'font-arabic')}>
            {isRtl ? 'لا توجد نتائج' : 'No results found'}
          </p>
          {activeFilterCount > 0 && (
            <button onClick={clearFilters} className="mt-3 text-xs text-teal-600 hover:underline">
              {isRtl ? 'مسح الفلاتر' : 'Clear filters'}
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(dua => (
            <DuaCard
              key={dua.id}
              dua={dua}
              isRtl={isRtl}
              memorizeMode={memorizeMode}
              autoExpand={dua.id === randomId}
              isFavorite={favorites.has(dua.id)}
              onToggleFavorite={toggleFavorite}
              isDaily={dua.id === dailyDuaId && !randomId && selectedCategory === 'all' && !selectedOccasion && !selectedProphet && !search && !favoritesOnly}
            />
          ))}
        </div>
      )}

      {/* ── Attribution ─────────────────────────────────────────────────────── */}
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
