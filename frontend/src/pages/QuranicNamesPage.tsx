/**
 * Quranic Names Explorer — names from or rooted in the Quran.
 *
 * Searchable by name, meaning, root, or category. Gender filter.
 * Each entry links to the surah reference.
 * No AI-generated content — all meanings from classical dictionaries.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Star, Search, ChevronRight, Info, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  QURANIC_NAMES,
  type Gender, type NameCategory, type QuranicName,
} from '../data/quranicNames';

const CATEGORY_LABELS: Record<NameCategory, { en: string; ar: string; color: string }> = {
  prophet:           { en: 'Prophet',         ar: 'نبي',             color: 'emerald' },
  divine_attribute:  { en: 'Divine Quality',  ar: 'صفة إلهية',       color: 'violet'  },
  nature:            { en: 'Nature',           ar: 'طبيعة',           color: 'teal'    },
  virtue:            { en: 'Virtue',           ar: 'فضيلة',           color: 'blue'    },
  other:             { en: 'Other',            ar: 'أخرى',            color: 'gray'    },
};

const GENDER_LABELS: Record<Gender | 'all', { en: string; ar: string }> = {
  all:    { en: 'All',    ar: 'الكل' },
  male:   { en: 'Male',   ar: 'ذكر' },
  female: { en: 'Female', ar: 'أنثى' },
  unisex: { en: 'Unisex', ar: 'للجنسين' },
};

const COLOR_BADGE: Record<string, string> = {
  emerald: 'bg-emerald-100 text-emerald-700',
  violet:  'bg-violet-100 text-violet-700',
  teal:    'bg-teal-100 text-teal-700',
  blue:    'bg-blue-100 text-blue-700',
  gray:    'bg-gray-100 text-gray-600',
};

function NameCard({ name, isRtl, expanded, onToggle }: {
  name: QuranicName;
  isRtl: boolean;
  expanded: boolean;
  onToggle: () => void;
}) {
  const catMeta = CATEGORY_LABELS[name.category];
  const badgeColor = COLOR_BADGE[catMeta.color] ?? COLOR_BADGE.gray;

  return (
    <div
      className="bg-white rounded-2xl border border-gray-100 hover:shadow-sm transition-shadow cursor-pointer overflow-hidden"
      onClick={onToggle}
    >
      <div className={clsx('p-4 flex items-start gap-3', isRtl && 'flex-row-reverse')}>
        {/* Arabic name */}
        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-50 to-indigo-50 flex items-center justify-center flex-shrink-0">
          <span className="font-arabic text-xl text-violet-800 leading-none">{name.arabic}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className={clsx('flex items-center gap-2 flex-wrap mb-0.5', isRtl && 'flex-row-reverse')}>
            <h3 className="font-semibold text-gray-900 text-sm">{name.transliteration}</h3>
            {/* Gender dot */}
            <span className={clsx(
              'w-2 h-2 rounded-full flex-shrink-0',
              name.gender === 'male' ? 'bg-blue-400'
                : name.gender === 'female' ? 'bg-pink-400'
                : 'bg-purple-300'
            )} title={GENDER_LABELS[name.gender].en} />
            <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full', badgeColor)}>
              {isRtl ? catMeta.ar : catMeta.en}
            </span>
          </div>
          <p className={clsx('text-xs text-gray-500 mb-1', isRtl && 'font-arabic text-right')}>
            {isRtl ? name.meaningAr : name.meaningEn}
          </p>
          <div className={clsx('flex items-center gap-1.5 text-[10px] text-gray-400', isRtl && 'flex-row-reverse')}>
            <Link
              to={`/quran/${name.surahRef}?aya=${name.ayahRef ?? 1}`}
              onClick={e => e.stopPropagation()}
              className="hover:text-violet-500 hover:underline flex items-center gap-0.5"
            >
              <span className="font-arabic" dir="rtl">{name.surahNameAr}</span>
              <span>{name.surahRef}:{name.ayahRef ?? 1}</span>
            </Link>
            {name.root && (
              <>
                <span>·</span>
                <span>Root: <span className="font-arabic" dir="rtl">{name.root}</span></span>
              </>
            )}
          </div>
        </div>

        <Info className={clsx('w-4 h-4 text-gray-300 flex-shrink-0 transition-colors mt-0.5', expanded && 'text-violet-400')} />
      </div>

      {/* Expanded detail */}
      {expanded && (name.notesEn || name.notesAr || name.quranicCiteEn || name.hadithEn) && (
        <div className={clsx('px-4 pb-4 pt-0 border-t border-gray-50 bg-violet-50/40')}>
          {(name.notesEn || name.notesAr) && (
            <p className={clsx('text-xs text-gray-600 leading-relaxed mt-3 mb-3', isRtl && 'font-arabic text-right')}>
              {isRtl ? name.notesAr : name.notesEn}
            </p>
          )}

          {/* Quranic cite callout */}
          {(name.quranicCiteEn || name.quranicCiteAr) && (
            <div className={clsx('flex gap-2 p-2.5 rounded-xl bg-amber-50 border border-amber-100 mb-2', isRtl && 'flex-row-reverse')}>
              <BookOpen className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div className="min-w-0">
                <p className={clsx('text-[10px] font-semibold text-amber-600 mb-0.5', isRtl && 'font-arabic')}>
                  {isRtl ? 'المرجع القرآني' : 'Quranic Reference'}
                </p>
                <p className={clsx('text-xs text-amber-800 leading-relaxed', isRtl ? 'font-arabic' : 'italic')}>
                  {isRtl ? (name.quranicCiteAr ?? name.quranicCiteEn) : name.quranicCiteEn}
                </p>
              </div>
            </div>
          )}

          {/* Hadith callout */}
          {(name.hadithEn || name.hadithAr) && (
            <div className={clsx('flex gap-2 p-2.5 rounded-xl bg-teal-50 border border-teal-100 mb-2', isRtl && 'flex-row-reverse')}>
              <span className="text-teal-500 flex-shrink-0 text-sm leading-none mt-0.5">📜</span>
              <div className="min-w-0">
                <p className={clsx('text-[10px] font-semibold text-teal-600 mb-0.5', isRtl && 'font-arabic')}>
                  {isRtl ? 'حديث شريف' : 'Hadith Reference'}
                </p>
                <p className={clsx('text-xs text-teal-800 leading-relaxed', isRtl ? 'font-arabic' : 'italic')}>
                  {isRtl ? (name.hadithAr ?? name.hadithEn) : name.hadithEn}
                </p>
              </div>
            </div>
          )}

          {/* Scholarly sources */}
          {(name.scholarlySrcEn || name.scholarlySrcAr) && (
            <p className={clsx('text-[10px] text-gray-400 leading-relaxed mb-2', isRtl && 'font-arabic text-right')}>
              <span className="font-medium text-gray-500">{isRtl ? 'المصادر: ' : 'Sources: '}</span>
              {isRtl ? (name.scholarlySrcAr ?? name.scholarlySrcEn) : name.scholarlySrcEn}
            </p>
          )}

          <Link
            to={`/quran/${name.surahRef}?aya=${name.ayahRef ?? 1}`}
            onClick={e => e.stopPropagation()}
            className={clsx(
              'inline-flex items-center gap-1 text-[10px] text-violet-600 hover:underline mt-1',
              isRtl && 'flex-row-reverse'
            )}
          >
            {isRtl ? `افتح سورة ${name.surahNameAr}` : `Open ${name.surahNameEn}`}
            <ChevronRight className={clsx('w-3 h-3', isRtl && 'rotate-180')} />
          </Link>
        </div>
      )}
    </div>
  );
}

export function QuranicNamesPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [search, setSearch] = useState('');
  const [genderFilter, setGenderFilter] = useState<Gender | 'all'>('all');
  const [catFilter, setCatFilter] = useState<NameCategory | 'all'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    let result: QuranicName[] = [...QURANIC_NAMES];
    if (genderFilter !== 'all') result = result.filter(n => n.gender === genderFilter || n.gender === 'unisex');
    if (catFilter !== 'all') result = result.filter(n => n.category === catFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(n =>
        n.transliteration.toLowerCase().includes(q) ||
        n.arabic.includes(q) ||
        n.meaningEn.toLowerCase().includes(q) ||
        n.meaningAr.includes(q) ||
        (n.root?.includes(q) ?? false) ||
        n.surahNameEn.toLowerCase().includes(q)
      );
    }
    // Prophets first, then alphabetical
    result.sort((a, b) => {
      if (a.category === 'prophet' && b.category !== 'prophet') return -1;
      if (b.category === 'prophet' && a.category !== 'prophet') return 1;
      return a.transliteration.localeCompare(b.transliteration);
    });
    return result;
  }, [search, genderFilter, catFilter]);

  const categories = Object.keys(CATEGORY_LABELS) as NameCategory[];
  const genders: (Gender | 'all')[] = ['all', 'male', 'female', 'unisex'];

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-2', isRtl && 'flex-row-reverse')}>
        <Star className="w-7 h-7 text-amber-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'أسماء من القرآن الكريم' : 'Names from the Quran'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl
              ? `${QURANIC_NAMES.length} اسماً قرآنياً مع المعاني والمراجع`
              : `${QURANIC_NAMES.length} Quranic names with meanings & references`}
          </p>
        </div>
      </div>

      {/* Search */}
      <div className={clsx('flex items-center gap-2 bg-white rounded-xl border border-gray-200 px-3 py-2.5 mb-3', isRtl && 'flex-row-reverse')}>
        <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={isRtl ? 'ابحث بالاسم أو المعنى أو الجذر…' : 'Search by name, meaning, or root…'}
          className={clsx('flex-1 text-sm bg-transparent outline-none text-gray-700', isRtl && 'font-arabic text-right')}
          dir={isRtl ? 'rtl' : 'ltr'}
        />
      </div>

      {/* Gender filter */}
      <div className={clsx('flex gap-1.5 mb-2 flex-wrap', isRtl && 'flex-row-reverse')}>
        {genders.map(g => (
          <button
            key={g}
            onClick={() => setGenderFilter(g)}
            className={clsx(
              'text-xs px-2.5 py-1 rounded-full border transition-colors',
              genderFilter === g
                ? 'bg-violet-600 text-white border-violet-600'
                : 'text-gray-500 border-gray-200 hover:bg-gray-50'
            )}
          >
            {isRtl ? GENDER_LABELS[g].ar : GENDER_LABELS[g].en}
          </button>
        ))}
      </div>

      {/* Category filter */}
      <div className={clsx('flex gap-1.5 mb-5 flex-wrap', isRtl && 'flex-row-reverse')}>
        <button
          onClick={() => setCatFilter('all')}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            catFilter === 'all'
              ? 'bg-gray-700 text-white border-gray-700'
              : 'text-gray-500 border-gray-200 hover:bg-gray-50'
          )}
        >
          {isRtl ? 'الكل' : 'All'}
        </button>
        {categories.map(c => {
          const meta = CATEGORY_LABELS[c];
          const badgeColor = COLOR_BADGE[meta.color] ?? COLOR_BADGE.gray;
          return (
            <button
              key={c}
              onClick={() => setCatFilter(c === catFilter ? 'all' : c)}
              className={clsx(
                'text-xs px-2.5 py-1 rounded-full border transition-colors',
                catFilter === c ? `${badgeColor} border-transparent ring-1` : 'text-gray-500 border-gray-200 hover:bg-gray-50'
              )}
            >
              {isRtl ? meta.ar : meta.en}
            </button>
          );
        })}
      </div>

      {/* Count */}
      <p className={clsx('text-xs text-gray-400 mb-3', isRtl && 'font-arabic text-right')}>
        {filtered.length} {isRtl ? 'اسم' : filtered.length === 1 ? 'name' : 'names'}
      </p>

      {/* Name list */}
      {filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map(n => (
            <NameCard
              key={n.id}
              name={n}
              isRtl={isRtl}
              expanded={expandedId === n.id}
              onToggle={() => setExpandedId(expandedId === n.id ? null : n.id)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400">
          <Star className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className={clsx('text-sm', isRtl && 'font-arabic')}>
            {isRtl ? 'لا نتائج' : 'No names found'}
          </p>
        </div>
      )}

      {/* Attribution */}
      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'المعاني من قاموس لين ومعجم هانس فير • لا فتاوى في التسمية — استشر عالماً'
          : "Meanings: Lane's Lexicon · Hans Wehr · No rulings on naming — consult a scholar"}
      </p>
    </div>
  );
}
