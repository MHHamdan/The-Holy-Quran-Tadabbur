/**
 * Quranic Duʿā Explorer
 *
 * A curated, filterable collection of supplications directly from
 * the Quran — with transliteration, meaning, context, and direct
 * links to the verse in the Mushaf.
 *
 * Safety: all content is referenced from specific surah:ayah.
 * No AI-generated meanings. Sources: Saheeh International translation.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen, Search, Filter, ExternalLink, ChevronDown, ChevronUp, Heart,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  QURANIC_DUAS, CATEGORY_META, type DuaCategory, type QuranicDua,
} from '../data/quranicDuas';

const ALL_CATEGORIES = Object.keys(CATEGORY_META) as DuaCategory[];

const COLOR_MAP: Record<string, string> = {
  emerald: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  amber:   'bg-amber-100 text-amber-700 border-amber-200',
  violet:  'bg-violet-100 text-violet-700 border-violet-200',
  rose:    'bg-rose-100 text-rose-700 border-rose-200',
  blue:    'bg-blue-100 text-blue-700 border-blue-200',
  orange:  'bg-orange-100 text-orange-700 border-orange-200',
  yellow:  'bg-yellow-100 text-yellow-700 border-yellow-200',
  teal:    'bg-teal-100 text-teal-700 border-teal-200',
};

function DuaCard({ dua, isRtl }: { dua: QuranicDua; isRtl: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const [showArabic, setShowArabic] = useState(true);
  const meta = CATEGORY_META[dua.category];
  const colorClass = COLOR_MAP[meta.color] ?? COLOR_MAP.teal;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {/* Card header */}
      <div
        className={clsx('p-4 cursor-pointer flex items-start gap-3', isRtl && 'flex-row-reverse')}
        onClick={() => setExpanded(v => !v)}
      >
        <span className="text-2xl flex-shrink-0 mt-0.5">{meta.emoji}</span>
        <div className="flex-1 min-w-0">
          <div className={clsx('flex items-center gap-2 flex-wrap mb-1', isRtl && 'flex-row-reverse')}>
            <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full border', colorClass)}>
              {isRtl ? meta.labelAr : meta.labelEn}
            </span>
            {dua.prophet && (
              <span className="text-xs text-gray-400 font-arabic">{dua.prophet}</span>
            )}
          </div>
          <h3 className={clsx('font-semibold text-gray-800 text-sm leading-snug', isRtl && 'font-arabic text-right')}>
            {isRtl ? dua.titleAr : dua.titleEn}
          </h3>
          <p className={clsx('text-[11px] text-gray-400 mt-0.5', isRtl && 'font-arabic text-right')}>
            {isRtl ? dua.surahNameAr : dua.surahNameEn} {dua.surah}:{dua.ayah}{dua.ayahEnd ? `–${dua.ayahEnd}` : ''}
          </p>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0 mt-1" />
          : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0 mt-1" />
        }
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-gray-50 px-4 pb-4 space-y-3">
          {/* Language toggle */}
          <div className={clsx('flex gap-2 pt-3', isRtl && 'flex-row-reverse')}>
            <button
              onClick={() => setShowArabic(true)}
              className={clsx(
                'text-xs px-3 py-1 rounded-lg border transition-colors',
                showArabic ? 'bg-teal-600 text-white border-teal-600' : 'text-gray-500 border-gray-200 hover:border-teal-300'
              )}
            >
              العربية
            </button>
            <button
              onClick={() => setShowArabic(false)}
              className={clsx(
                'text-xs px-3 py-1 rounded-lg border transition-colors',
                !showArabic ? 'bg-teal-600 text-white border-teal-600' : 'text-gray-500 border-gray-200 hover:border-teal-300'
              )}
            >
              English
            </button>
          </div>

          {/* Arabic text / meaning */}
          {showArabic ? (
            <div className="bg-teal-50 rounded-xl p-4 text-right" dir="rtl">
              <p className="font-arabic text-lg text-teal-900 leading-loose">
                {dua.meaningAr}
              </p>
              <p className="text-xs text-teal-600 mt-2 italic text-left" dir="ltr">
                {dua.transliterationArabic}
              </p>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-sm text-gray-700 leading-relaxed italic">
                "{dua.meaningEn}"
              </p>
            </div>
          )}

          {/* Context */}
          <div className="bg-amber-50 rounded-lg px-3 py-2">
            <p className={clsx('text-xs text-amber-800 leading-relaxed', isRtl && 'font-arabic text-right')}>
              {isRtl ? dua.contextAr : dua.contextEn}
            </p>
          </div>

          {/* Tags */}
          <div className={clsx('flex flex-wrap gap-1.5', isRtl && 'flex-row-reverse')}>
            {dua.tags.map(tag => (
              <span key={tag} className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                #{tag}
              </span>
            ))}
          </div>

          {/* Link to verse */}
          <Link
            to={`/quran/${dua.surah}`}
            className={clsx(
              'flex items-center gap-2 text-xs text-teal-700 hover:text-teal-900 transition-colors font-medium',
              isRtl && 'flex-row-reverse'
            )}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            {isRtl
              ? `اقرأ الآية في المصحف — ${dua.surahNameAr} ${dua.surah}:${dua.ayah}`
              : `Read in Mushaf — ${dua.surahNameEn} ${dua.surah}:${dua.ayah}`}
          </Link>
        </div>
      )}
    </div>
  );
}

export function DuasPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<DuaCategory | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);

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
        d.tags.some(t => t.includes(q)) ||
        d.surahNameEn.toLowerCase().includes(q) ||
        d.surahNameAr.includes(q) ||
        (d.prophet?.toLowerCase().includes(q) ?? false)
      );
    });
  }, [search, selectedCategory]);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <h1 className={clsx('text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1', isRtl && 'font-arabic flex-row-reverse')}>
          <BookOpen className="w-6 h-6 text-teal-600" />
          {isRtl ? 'أدعية القرآن الكريم' : 'Quranic Duʿā'}
        </h1>
        <p className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
          {isRtl
            ? `${QURANIC_DUAS.length} دعاء مستقى من القرآن الكريم — بالتشكيل والترجمة والسياق`
            : `${QURANIC_DUAS.length} supplications directly from the Quran — with transliteration, meaning & context`}
        </p>
      </div>

      {/* Search + Filter */}
      <div className="mb-5 space-y-3">
        <div className="relative">
          <Search className={clsx('absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400', isRtl ? 'right-3' : 'left-3')} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={isRtl ? 'ابحث عن دعاء أو نبي أو موضوع...' : 'Search duʿā, prophet, or topic...'}
            className={clsx(
              'w-full border border-gray-200 rounded-xl py-2.5 text-sm focus:ring-2 focus:ring-teal-300 focus:border-teal-400 outline-none bg-white',
              isRtl ? 'pr-9 pl-3 text-right font-arabic' : 'pl-9 pr-3'
            )}
          />
        </div>

        <div className={clsx('flex items-center gap-2 flex-wrap', isRtl && 'flex-row-reverse')}>
          <button
            onClick={() => setShowFilters(v => !v)}
            className={clsx(
              'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors',
              showFilters ? 'bg-teal-600 text-white border-teal-600' : 'text-gray-600 border-gray-200 hover:border-teal-300'
            )}
          >
            <Filter className="w-3.5 h-3.5" />
            {isRtl ? 'تصفية' : 'Filter'}
          </button>
          <span className="text-xs text-gray-400">
            {isRtl ? `${filtered.length} من ${QURANIC_DUAS.length}` : `${filtered.length} of ${QURANIC_DUAS.length}`}
          </span>
        </div>

        {showFilters && (
          <div className={clsx('flex flex-wrap gap-2', isRtl && 'flex-row-reverse')}>
            <button
              onClick={() => setSelectedCategory('all')}
              className={clsx(
                'text-xs px-3 py-1.5 rounded-lg border transition-colors',
                selectedCategory === 'all'
                  ? 'bg-teal-600 text-white border-teal-600'
                  : 'text-gray-600 border-gray-200 hover:border-teal-300'
              )}
            >
              {isRtl ? 'الكل' : 'All'}
            </button>
            {ALL_CATEGORIES.map(cat => {
              const meta = CATEGORY_META[cat];
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={clsx(
                    'text-xs px-3 py-1.5 rounded-lg border transition-colors flex items-center gap-1',
                    selectedCategory === cat
                      ? 'bg-teal-600 text-white border-teal-600'
                      : 'text-gray-600 border-gray-200 hover:border-teal-300'
                  )}
                >
                  {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <BookOpen className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className={clsx('text-sm', isRtl && 'font-arabic')}>
            {isRtl ? 'لا توجد نتائج للبحث' : 'No results found'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(dua => (
            <DuaCard key={dua.id} dua={dua} isRtl={isRtl} />
          ))}
        </div>
      )}

      {/* Attribution footer */}
      <div className={clsx('mt-8 p-4 bg-gray-50 rounded-xl text-center', isRtl && 'font-arabic')}>
        <p className="text-xs text-gray-400 flex items-center justify-center gap-1.5">
          <Heart className="w-3.5 h-3.5 text-rose-400" />
          {isRtl
            ? 'المعاني من ترجمة صحيح إنترناشيونال • الجذور من مكتبة لين • لا محتوى مُولَّد بالذكاء الاصطناعي'
            : "Meanings: Saheeh International · Roots: Lane's Lexicon · No AI-generated content"}
        </p>
        <p className={clsx('text-[10px] text-gray-300 mt-1', isRtl && 'font-arabic')}>
          {isRtl ? 'كل دعاء مرتبط بمرجعه القرآني الدقيق' : 'Every duʿā linked to its exact Quranic reference'}
        </p>
      </div>
    </div>
  );
}
