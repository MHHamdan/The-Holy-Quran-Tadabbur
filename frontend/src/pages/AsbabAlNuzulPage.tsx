/**
 * Asbab al-Nuzul (أسباب النزول) — Occasions of Revelation
 *
 * Inspired by Tafsir MCP's offline-first approach: data is fetched once,
 * cached 24 h via HTTP headers + React Query, then available offline.
 * Source: al-Wahidi (d. 468 AH) via alquran.cloud ar.wahidi edition.
 */

import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BookOpen, ChevronDown, ExternalLink, Search, X,
  AlertCircle, BookMarked, Info,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi } from '../lib/api';
import { SURAH_NAMES } from '../data/surahNames';

const SURAH_OPTIONS = SURAH_NAMES.map((s, i) => ({
  value: i + 1,
  labelAr: `${i + 1}. ${s.ar}`,
  labelEn: `${i + 1}. ${s.en}`,
}));

// ─── Surah Selector ────────────────────────────────────────────────────────────

function SurahSelector({
  selected,
  onChange,
  lang,
}: {
  selected: number;
  onChange: (n: number) => void;
  lang: 'ar' | 'en';
}) {
  return (
    <div className="relative">
      <select
        value={selected}
        onChange={(e) => onChange(Number(e.target.value))}
        dir={lang === 'ar' ? 'rtl' : 'ltr'}
        className="w-full appearance-none rounded-xl border border-emerald-200 bg-white px-4 py-3 pr-10 text-sm font-medium text-gray-800 shadow-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
      >
        {SURAH_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {lang === 'ar' ? o.labelAr : o.labelEn}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
    </div>
  );
}

// ─── Verse Card ────────────────────────────────────────────────────────────────

function AsbabCard({
  surah,
  ayah,
  text,
  highlight,
}: {
  surah: number;
  ayah: number;
  text: string;
  highlight: string;
}) {
  const ref = `${surah}:${ayah}`;
  const surahName = SURAH_NAMES[surah - 1];

  const highlighted = useMemo(() => {
    if (!highlight.trim()) return text;
    const escaped = highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
    return parts.map((p) =>
      new RegExp(escaped, 'i').test(p)
        ? `<mark class="bg-yellow-200 text-yellow-900 rounded px-0.5">${p}</mark>`
        : p
    ).join('');
  }, [text, highlight]);

  return (
    <div className="rounded-2xl border border-emerald-100 bg-white shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-emerald-50 border-b border-emerald-100">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-emerald-600 text-white text-xs font-bold">
            {ayah}
          </span>
          <div dir="rtl">
            <p className="text-sm font-semibold text-emerald-800">{surahName?.ar}</p>
            <p className="text-xs text-emerald-600">{surahName?.en} · {ref}</p>
          </div>
        </div>
        <Link
          to={`/quran/${surah}?aya=${ayah}`}
          className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-800 transition-colors"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          <span>الآية</span>
        </Link>
      </div>

      {/* Asbab text */}
      <div className="p-4">
        <p
          dir="rtl"
          className="text-base leading-loose text-gray-800 font-arabic text-right"
          dangerouslySetInnerHTML={{ __html: highlighted }}
        />
      </div>
    </div>
  );
}

// ─── Loading Skeleton ──────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="space-y-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="rounded-2xl border border-gray-100 overflow-hidden animate-pulse">
          <div className="h-14 bg-gray-100" />
          <div className="p-4 space-y-2">
            <div className="h-4 bg-gray-100 rounded w-full" />
            <div className="h-4 bg-gray-100 rounded w-5/6" />
            <div className="h-4 bg-gray-100 rounded w-4/6" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export function AsbabAlNuzulPage() {
  const { language } = useLanguageStore();
  const lang = language as 'ar' | 'en';

  const [selectedSurah, setSelectedSurah] = useState(2); // Al-Baqarah (richest in asbab)
  const [search, setSearch] = useState('');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['asbab', selectedSurah],
    queryFn: () => quranApi.getAsbab(selectedSurah).then((r) => r.data),
    staleTime: 1000 * 60 * 60 * 24, // 24 h — content is immutable classical text
    gcTime: 1000 * 60 * 60 * 48,
    retry: 2,
  });

  const filtered = useMemo(() => {
    if (!data) return [];
    if (!search.trim()) return data.verses;
    const q = search.trim().toLowerCase();
    return data.verses.filter((v) => v.text.toLowerCase().includes(q));
  }, [data, search]);

  const clearSearch = useCallback(() => setSearch(''), []);

  const surahNameAr = SURAH_NAMES[selectedSurah - 1]?.ar ?? '';
  const surahNameEn = SURAH_NAMES[selectedSurah - 1]?.en ?? '';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Page header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-4 py-1.5 text-sm font-medium text-emerald-700">
          <BookMarked className="h-4 w-4" />
          {lang === 'ar' ? 'أسباب النزول' : 'Occasions of Revelation'}
        </div>
        <h1 className="text-2xl font-bold text-gray-900" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
          {lang === 'ar' ? 'أسباب نزول الآيات القرآنية' : 'Why Were These Verses Revealed?'}
        </h1>
        <p className="text-sm text-gray-500" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
          {lang === 'ar'
            ? 'من كتاب أسباب النزول للإمام الواحدي (ت 468 هـ)'
            : 'From Asbab al-Nuzul by Imam al-Wahidi (d. 468 AH)'}
        </p>
      </div>

      {/* Source attribution banner */}
      <div className="flex items-start gap-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-sm text-amber-800">
        <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
        <p dir={lang === 'ar' ? 'rtl' : 'ltr'}>
          {lang === 'ar'
            ? 'النصوص المعروضة مستخرجة من مصدر قديم موثوق. الآيات التي لا توجد لها سبب نزول محدد لا تُعرض.'
            : 'Texts are sourced from a verified classical source. Verses with no recorded occasion are omitted.'}
        </p>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <SurahSelector selected={selectedSurah} onChange={setSelectedSurah} lang={lang} />

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={lang === 'ar' ? 'ابحث في النصوص...' : 'Search occasions...'}
            dir={lang === 'ar' ? 'rtl' : 'ltr'}
            className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-9 py-3 text-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
          />
          {search && (
            <button
              onClick={clearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Result count */}
      {data && !isLoading && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span dir={lang === 'ar' ? 'rtl' : 'ltr'}>
            {lang === 'ar'
              ? `سورة ${surahNameAr} — ${filtered.length} آية لها سبب نزول`
              : `${surahNameEn} — ${filtered.length} verse${filtered.length !== 1 ? 's' : ''} with recorded occasion`}
          </span>
          {search && (
            <span className="text-xs bg-yellow-100 text-yellow-700 rounded-full px-2 py-0.5">
              {lang === 'ar' ? `نتائج البحث: ${filtered.length}` : `${filtered.length} match${filtered.length !== 1 ? 'es' : ''}`}
            </span>
          )}
        </div>
      )}

      {/* Content */}
      {isLoading && <Skeleton />}

      {isError && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <AlertCircle className="h-10 w-10 text-red-400" />
          <p className="text-red-600 font-medium">
            {lang === 'ar' ? 'تعذّر تحميل البيانات' : 'Failed to load asbab data'}
          </p>
          <p className="text-sm text-gray-500">
            {lang === 'ar'
              ? 'يُرجى التحقق من اتصالك بالإنترنت والمحاولة مجدداً'
              : 'Check your internet connection and try again'}
          </p>
        </div>
      )}

      {!isLoading && !isError && filtered.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <BookOpen className="h-10 w-10 text-gray-300" />
          <p className="text-gray-500">
            {search
              ? (lang === 'ar' ? 'لا توجد نتائج للبحث' : 'No matching results')
              : (lang === 'ar' ? 'لا توجد أسباب نزول مسجّلة لهذه السورة' : 'No recorded occasions for this surah')}
          </p>
        </div>
      )}

      <div className="space-y-4">
        {filtered.map((v) => (
          <AsbabCard
            key={`${v.surah}:${v.ayah}`}
            surah={v.surah}
            ayah={v.ayah}
            text={v.text}
            highlight={search}
          />
        ))}
      </div>
    </div>
  );
}
