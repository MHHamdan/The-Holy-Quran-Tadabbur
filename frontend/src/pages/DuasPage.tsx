/**
 * Quranic Duʿā Explorer — enhanced with occasion & prophet filters,
 * bookmarks (localStorage), daily duʿā, and share.
 *
 * Safety: all content referenced from exact surah:ayah. The Arabic is verbatim
 * Tanzil text (an excerpt is labelled and the full verse is one tap away); the
 * English is the QuranEnc Saheeh International translation and the Arabic
 * explanation is a licence-cleared tafsir (al-Baghawi, else Ibn Kathir), both
 * fetched from the API with their attribution. No AI-generated meanings.
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
import { quranApi, tafsirComparisonApi, type TafsirComparisonEntry } from '../lib/api';
import { QuranTextAttribution } from '../components/quran/QuranTextAttribution';
import { useTranslationEditions } from '../components/quran/VerseTranslations';
import { localDateStr } from '../utils/localDate';
import {
  QURANIC_DUAS, CATEGORY_META, OCCASION_META, isDisplayableNote,
  type DuaCategory, type DuaOccasion, type QuranicDua,
} from '../data/quranicDuas';
import { shareContent } from '../lib/native';
import { figureTranslations } from '../i18n/translations';

const ALL_CATEGORIES = Object.keys(CATEGORY_META) as DuaCategory[];
const ALL_OCCASIONS  = Object.keys(OCCASION_META)  as DuaOccasion[];

// Collect all distinct prophet names
const ALL_PROPHETS = Array.from(
  new Set(QURANIC_DUAS.map(d => d.prophet).filter(Boolean) as string[])
).sort();

/** Prophet names are stored in English transliteration; show them in the UI language. */
function prophetLabel(name: string, isRtl: boolean): string {
  return isRtl ? (figureTranslations[name]?.ar ?? name) : name;
}

/** One numeral style per language: Arabic-Indic digits in the Arabic UI. */
function formatCount(n: number, isRtl: boolean): string {
  return n.toLocaleString(isRtl ? 'ar-EG' : 'en-US');
}

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
  // Local calendar day (not UTC), so the duʿā changes at the reader's midnight.
  const [y, m, d] = localDateStr().split('-').map(Number);
  const dayIndex = Math.floor(Date.UTC(y, m - 1, d) / 86_400_000) % QURANIC_DUAS.length;
  return QURANIC_DUAS[dayIndex].id;
}

// ─── Reference helpers ────────────────────────────────────────────────────────

/** "1:6–7" — always rendered inside <bdi dir="ltr"> so Arabic text cannot reorder it. */
function formatAyahRef(surah: number, ayah: number, ayahEnd: number | undefined, isRtl: boolean): string {
  const n = (x: number) => formatCount(x, isRtl);
  return `${n(surah)}:${n(ayah)}${ayahEnd ? `–${n(ayahEnd)}` : ''}`;
}

/** LRI…PDI: keeps a reference left-to-right inside shared or copied plain text. */
const isolateLtr = (s: string) => `⁦${s}⁩`;

const ENGLISH_EDITION = 'english_saheeh';

// ─── Copy Button ───────────────────────────────────────────────────────────────

function CopyButton({ text, isRtl }: { text: string; isRtl: boolean }) {
  const [copied, setCopied] = useState(false);
  const handle = useCallback(async () => {
    await navigator.clipboard.writeText(text).catch(() => null);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }, [text]);
  return (
    <button
      type="button"
      onClick={handle}
      aria-label={isRtl ? 'نسخ النص' : 'Copy text'}
      className="flex min-h-8 items-center gap-1 text-xs text-gray-500 hover:text-teal-600 transition-colors px-2 py-1 rounded-lg hover:bg-teal-50"
    >
      {copied
        ? <><Check className="w-3.5 h-3.5 text-teal-500" /><span className="text-teal-500">{isRtl ? 'تم النسخ' : 'Copied'}</span></>
        : <><Copy className="w-3.5 h-3.5" /><span>{isRtl ? 'نسخ' : 'Copy'}</span></>}
    </button>
  );
}

// ─── Share Button ─────────────────────────────────────────────────────────────

function ShareButton({ title, text, isRtl }: { title: string; text: string; isRtl: boolean }) {
  const [shared, setShared] = useState(false);
  const handle = useCallback(async () => {
    await shareContent({ title, text });
    setShared(true);
    setTimeout(() => setShared(false), 1800);
  }, [title, text]);
  return (
    <button
      type="button"
      onClick={handle}
      aria-label={isRtl ? 'مشاركة' : 'Share'}
      className="flex min-h-8 items-center gap-1 text-xs text-gray-500 hover:text-violet-600 transition-colors px-2 py-1 rounded-lg hover:bg-violet-50"
    >
      {shared
        ? <><Check className="w-3.5 h-3.5 text-violet-500" /><span className="text-violet-500">{isRtl ? 'تمت' : 'Shared'}</span></>
        : <><Share2 className="w-3.5 h-3.5" /><span>{isRtl ? 'شارك' : 'Share'}</span></>}
    </button>
  );
}

// ─── Explanation: a licence-cleared tafsir from the app's library ───────────

/** al-Baghawi first (concise); Ibn Kathir where al-Baghawi has no passage. */
const DUA_TAFSIR_SOURCES = ['baghawi_ar', 'ibn_kathir_ar'];

function DuaTafsirExplanation({ dua }: { dua: QuranicDua }) {
  const last = dua.ayahEnd ?? dua.ayah;
  const ayat = Array.from({ length: last - dua.ayah + 1 }, (_, i) => dua.ayah + i);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dua-tafsir', dua.surah, dua.ayah, last],
    queryFn: async () => Promise.all(
      ayat.map(async (a) => {
        try {
          const res = await tafsirComparisonApi.compare(dua.surah, a, { sources: DUA_TAFSIR_SOURCES });
          const entries = res.data.entries;
          for (const sid of DUA_TAFSIR_SOURCES) {
            const hit = entries.find((e) => e.source_id === sid);
            if (hit) return hit;
          }
          return null;
        } catch {
          return null;
        }
      }),
    ),
    staleTime: Infinity,
  });
  if (isLoading) return <div className="h-10 rounded-lg bg-gray-100 animate-pulse" />;
  const entries = (data ?? []).filter((e): e is TafsirComparisonEntry => !!e);
  if (isError || entries.length === 0) {
    return (
      <p className="text-xs text-gray-500">
        <span className="block font-arabic text-right" dir="rtl" lang="ar">
          لا يتوفر شرح من مكتبة التفسير لهذه الآية حالياً.
        </span>
        <span className="block" dir="ltr" lang="en">
          No tafsir explanation is available for this verse yet.
        </span>
      </p>
    );
  }
  // One credit line per work actually shown (an ayah range may mix sources).
  const credited = entries.filter((e, i) => entries.findIndex((x) => x.source_id === e.source_id) === i);
  return (
    <div className="space-y-1">
      {entries.map((e) => (
        <p key={e.chunk_id} className="font-arabic text-sm text-gray-700 leading-relaxed text-right" dir="rtl" lang="ar">
          {e.text}
        </p>
      ))}
      {credited.map((e) => (
        <p key={e.source_id} className="font-arabic text-[11px] text-gray-400 text-right" dir="rtl">
          {e.name_ar} — {e.author_ar} · <bdi dir="ltr" className="font-mono">{e.source_id}</bdi>
        </p>
      ))}
    </div>
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
  const [showFull, setShowFull] = useState(false);
  const [hideTranslit, setHideTranslit] = useState(false);
  const [hideMeaning, setHideMeaning] = useState(false);
  const { data: editions } = useTranslationEditions();
  const meta = CATEGORY_META[dua.category];
  const accentClass = ACCENT[meta.color] ?? ACCENT.teal;
  const badgeClass  = BADGE[meta.color]  ?? BADGE.teal;
  const bodyId = `dua-body-${dua.id}`;

  const surahName = isRtl ? dua.surahNameAr : dua.surahNameEn;
  const ayahRef = formatAyahRef(dua.surah, dua.ayah, dua.ayahEnd, isRtl);

  const { data: liveVerses } = useQuery({
    queryKey: ['dua-verses', dua.surah, dua.ayah, dua.ayahEnd ?? null, isRtl ? 'ar' : 'en'],
    queryFn: async () => {
      const translations = isRtl ? [] : [ENGLISH_EDITION];
      if (dua.ayahEnd) {
        const res = await quranApi.getVerseRange(dua.surah, dua.ayah, dua.ayahEnd, translations);
        return res.data;
      }
      const res = await quranApi.getVerse(dua.surah, dua.ayah, translations);
      return [res.data];
    },
    enabled: expanded,
    staleTime: Infinity,
  });

  // The curated text is an excerpt whenever it is shorter than the verses.
  const fullText = liveVerses?.map(v => v.text_uthmani).join(' ۝ ');
  const isExcerpt = fullText !== undefined && fullText !== dua.ayatUthmani;
  const displayedAyat = showFull && fullText ? fullText : dua.ayatUthmani;
  const shownLabel = isExcerpt && !showFull
    ? (isRtl ? `مقتطف من ${surahName} ${isolateLtr(ayahRef)}` : `Excerpt of ${surahName} ${isolateLtr(ayahRef)}`)
    : `${surahName} ${isolateLtr(ayahRef)}`;
  // Copy and share carry exactly what is on screen, with its reference.
  const shareText = `${displayedAyat}\n— ${shownLabel}\n${isRtl ? 'نص القرآن: مشروع تنزيل tanzil.net' : "Qur'an text: Tanzil Project, tanzil.net"}`;

  const translations = (liveVerses ?? []).flatMap(v => (v.translations ?? []).filter(t => t.translator === ENGLISH_EDITION));
  const edition = editions?.find(e => e.key === ENGLISH_EDITION);
  const editionVersion = translations[0]?.edition_version ?? edition?.version;

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

      {/* ── Header: the expand control and the bookmark are sibling buttons ── */}
      <div className="px-4 pt-4 pb-3 flex gap-3 items-start">
        <button
          type="button"
          onClick={() => setExpanded(v => !v)}
          aria-expanded={expanded}
          aria-controls={bodyId}
          className="flex-1 min-w-0 flex gap-3 text-start select-none"
        >
          <span className="text-xl flex-shrink-0 mt-0.5" aria-hidden="true">{meta.emoji}</span>
          <span className="flex-1 min-w-0 block">
            <span className="flex flex-wrap items-center gap-1.5 mb-1.5">
              <span className={clsx('text-[11px] font-medium px-2 py-0.5 rounded-full', badgeClass)}>
                {isRtl ? meta.labelAr : meta.labelEn}
              </span>
              {dua.prophet && (
                <span className={clsx('text-[11px] bg-amber-50 text-amber-700 ring-1 ring-amber-200 px-2 py-0.5 rounded-full', isRtl && 'font-arabic')}>
                  {prophetLabel(dua.prophet, isRtl)}
                </span>
              )}
            </span>
            <span className={clsx('block font-semibold text-gray-800 text-sm leading-snug', isRtl && 'font-arabic')}>
              {isRtl ? dua.titleAr : dua.titleEn}
            </span>
            <span className={clsx('block text-[11px] text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
              {surahName}{isRtl ? '، ' : ' · '}<bdi dir="ltr">{ayahRef}</bdi>
            </span>
          </span>
          <span className="text-gray-300 flex-shrink-0 mt-1" aria-hidden="true">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </span>
        </button>
        <button
          type="button"
          onClick={() => onToggleFavorite(dua.id)}
          aria-pressed={isFavorite}
          aria-label={isRtl
            ? (isFavorite ? 'إزالة من المحفوظات' : 'حفظ الدعاء')
            : (isFavorite ? 'Remove bookmark' : 'Bookmark')}
          className="-m-2 inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg hover:bg-rose-50 transition-colors flex-shrink-0"
        >
          <Heart className={clsx(
            'w-4 h-4 transition-colors',
            isFavorite ? 'fill-rose-400 text-rose-400' : 'text-gray-300 hover:text-rose-300',
          )} />
        </button>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────────── */}
      {expanded && (
        <div id={bodyId} className="px-4 pb-4 space-y-3 border-t border-gray-100">

          {/* Arabic Ayat: the curated excerpt, or the full verses on request */}
          <div className="bg-white rounded-xl p-4 mt-3 border border-gray-100 shadow-inner">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
              {isExcerpt ? (
                <span className={clsx('text-[10px] px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 ring-1 ring-sky-100', isRtl && 'font-arabic')}>
                  {showFull
                    ? (isRtl ? 'الآية كاملة' : 'Full verse')
                    : (isRtl ? 'مقتطف من الآية' : 'Excerpt of')}{' '}
                  <bdi dir="ltr">{ayahRef}</bdi>
                </span>
              ) : <span />}
              <div className="flex items-center gap-1">
                {isExcerpt && (
                  <button
                    type="button"
                    onClick={() => setShowFull(v => !v)}
                    className={clsx('min-h-8 text-xs text-sky-700 hover:underline px-2 py-1', isRtl && 'font-arabic')}
                  >
                    {showFull
                      ? (isRtl ? 'عرض المقتطف' : 'Show excerpt')
                      : (isRtl ? 'عرض الآية كاملة' : 'Show full verse')}
                  </button>
                )}
                <CopyButton text={shareText} isRtl={isRtl} />
                <ShareButton title={isRtl ? dua.titleAr : dua.titleEn} text={shareText} isRtl={isRtl} />
              </div>
            </div>
            <p className="font-arabic text-xl leading-[2.2] text-gray-900 text-right" dir="rtl" lang="ar">
              {displayedAyat}
            </p>
            <QuranTextAttribution language={isRtl ? 'ar' : 'en'} className="mt-2" />
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
                    type="button"
                    onClick={() => setHideTranslit(v => !v)}
                    className="min-h-6 px-2 text-[10px] text-gray-500 hover:text-teal-600 flex items-center gap-1"
                  >
                    {hideTranslit ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                    {hideTranslit ? 'Show' : 'Hide'}
                  </button>
                )}
              </div>
              {!hideTranslit && (
                <p className="text-sm text-gray-600 italic leading-relaxed font-light tracking-wide" dir="ltr">
                  {dua.transliterationArabic}
                </p>
              )}
            </div>
          )}

          {/* Meaning: QuranEnc translation (EN) or a cleared tafsir (AR), each credited */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className={clsx('text-[10px] font-semibold uppercase tracking-wider text-gray-400', isRtl && 'font-arabic normal-case')}>
                {isRtl ? 'المعنى من مكتبة التفسير' : 'Translation of the meanings'}
              </span>
              {memorizeMode && (
                <button
                  type="button"
                  onClick={() => setHideMeaning(v => !v)}
                  className="min-h-6 px-2 text-[10px] text-gray-500 hover:text-teal-600 flex items-center gap-1"
                >
                  {hideMeaning ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                  {hideMeaning ? (isRtl ? 'إظهار' : 'Show') : (isRtl ? 'إخفاء' : 'Hide')}
                </button>
              )}
            </div>
            {!hideMeaning && (
              isRtl ? (
                <DuaTafsirExplanation dua={dua} />
              ) : translations.length > 0 ? (
                <div className="space-y-1" dir="ltr">
                  {translations.map((t, i) => (
                    <p key={i} lang="en" className="text-sm text-gray-700 leading-relaxed">{t.text}</p>
                  ))}
                  <p className="text-[11px] text-gray-400">
                    {isExcerpt ? 'Full verse. ' : ''}
                    {edition?.title ?? 'Saheeh International'}{editionVersion ? ` v${editionVersion}` : ''},{' '}
                    <a href="https://quranenc.com" target="_blank" rel="noopener noreferrer" className="underline">QuranEnc.com</a>
                  </p>
                </div>
              ) : (
                <div className="h-8 rounded-lg bg-gray-100 animate-pulse" />
              )
            )}
          </div>

          {/* Hadith: shown only with collection + number; grade only with its grader */}
          {isDisplayableNote(dua.supportingNote) && (
            <div className="rounded-xl border border-amber-100 bg-amber-50 px-3 py-2.5">
              <p className={clsx('text-[10px] font-semibold text-amber-600 mb-1', isRtl && 'font-arabic text-right')}>
                {isRtl ? 'حديث ذو صلة' : 'Related hadith'}
              </p>
              <p className="font-arabic text-xs text-amber-900 leading-relaxed text-right" dir="rtl" lang="ar">
                {dua.supportingNote.textAr}
              </p>
              <p className="font-arabic text-[11px] text-amber-700 mt-1 text-right" dir="rtl" lang="ar">
                {dua.supportingNote.collection} <bdi dir="ltr">{dua.supportingNote.number}</bdi>
                {dua.supportingNote.grade && dua.supportingNote.grader
                  ? ` · ${dua.supportingNote.grade} — ${dua.supportingNote.grader}`
                  : ''}
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
            <div className="flex flex-wrap gap-1">
              <span className={clsx('text-[10px] text-gray-400 self-center me-1', isRtl && 'font-arabic')}>
                {isRtl ? 'متى يُقال:' : 'When to recite:'}
              </span>
              {dua.occasions.map(occ => (
                <span key={occ} className="text-[10px] bg-teal-50 text-teal-600 ring-1 ring-teal-100 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                  {OCCASION_META[occ].emoji} {isRtl ? OCCASION_META[occ].labelAr : OCCASION_META[occ].labelEn}
                </span>
              ))}
            </div>
          )}

          {/* Tags are English search keywords, so they are shown in the English UI only */}
          {!isRtl && (
          <div className="flex flex-wrap gap-1">
            {dua.tags.map(tag => (
              <span key={tag} className="text-[10px] bg-gray-100 text-gray-400 px-2 py-0.5 rounded-full" dir="ltr">
                #{tag}
              </span>
            ))}
          </div>
          )}

          {/* Read in Mushaf */}
          <Link
            to={`/quran/${dua.surah}?aya=${dua.ayah}`}
            className={clsx(
              'inline-flex min-h-8 items-center gap-1.5 text-xs font-medium text-teal-700 hover:text-teal-900 transition-colors',
              isRtl && 'font-arabic',
            )}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            {isRtl ? 'اقرأ في المصحف — ' : 'Read in Muṣḥaf — '}
            {surahName} <bdi dir="ltr">{ayahRef}</bdi>
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
        (d.prophet?.toLowerCase().includes(q) ?? false) ||
        (d.prophet ? (figureTranslations[d.prophet]?.ar ?? '').includes(q) : false)
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
            ? `${formatCount(QURANIC_DUAS.length, true)} دعاءً مُرتَّبًا حسب ترتيب القرآن — بالنص العثماني والتشكيل والترجمة`
            : `${QURANIC_DUAS.length} supplications in Quranic order — Uthmanic text, transliteration & meaning`}
        </p>

        {/* Action row */}
        <div className={clsx('mt-4 flex flex-wrap items-center justify-center gap-2', isRtl && 'flex-row-reverse')}>
          <button
            onClick={() => setMemorizeMode(v => !v)}
            className={clsx(
              'inline-flex min-h-11 items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all',
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
              'inline-flex min-h-11 items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all',
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
              )}>{formatCount(favorites.size, isRtl)}</span>
            )}
          </button>

          <button
            onClick={pickRandom}
            className="inline-flex min-h-11 items-center gap-2 text-sm font-medium px-4 py-2 rounded-xl transition-all bg-white border border-gray-200 text-gray-600 hover:border-violet-300 hover:text-violet-700"
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
          aria-label={isRtl ? 'ابحث في الأدعية' : 'Search duas'}
          type="text"
          value={search}
          onChange={e => { setSearch(e.target.value); setRandomId(null); }}
          placeholder={isRtl ? 'ابحث في الأدعية أو الأنبياء أو المواضيع...' : 'Search duʿā, prophet, or topic...'}
          className={clsx(
            'w-full bg-white border border-gray-200 rounded-xl py-2.5 text-sm',
            'focus:ring-2 focus:ring-teal-300 focus:border-teal-400 outline-none transition',
            isRtl ? 'pr-9 pl-11 text-right font-arabic' : 'pl-9 pr-11',
          )}
        />
        {search && (
          <button
            type="button"
            onClick={() => setSearch('')}
            aria-label={isRtl ? 'مسح البحث' : 'Clear search'}
            className={clsx(
              'absolute top-1/2 -translate-y-1/2 inline-flex min-h-11 min-w-11 items-center justify-center text-gray-400 hover:text-gray-600',
              isRtl ? 'left-0' : 'right-0',
            )}
          ><X className="w-4 h-4" /></button>
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
            'flex-shrink-0 min-h-11 text-xs px-3 py-1.5 rounded-full border transition-all whitespace-nowrap',
            selectedCategory === 'all'
              ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
              : 'text-gray-600 border-gray-200 bg-white hover:border-teal-300',
          )}
        >
          {isRtl ? 'الكل، ' : 'All · '}{formatCount(categoryCounts.all ?? 0, isRtl)}
        </button>

        {ALL_CATEGORIES.map(cat => {
          const m = CATEGORY_META[cat];
          const active = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={clsx(
                'flex-shrink-0 min-h-11 flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all whitespace-nowrap',
                active
                  ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                  : 'text-gray-600 border-gray-200 bg-white hover:border-teal-300',
              )}
            >
              {m.emoji}
              <span>{isRtl ? m.labelAr : m.labelEn}</span>
              {categoryCounts[cat] != null && (
                <span className={clsx('text-[10px]', active ? 'text-teal-100' : 'text-gray-400')}>
                  {formatCount(categoryCounts[cat] ?? 0, isRtl)}
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
            'flex min-h-11 items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all',
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
            'flex min-h-11 items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all',
            selectedProphet
              ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
              : 'text-gray-600 border-gray-200 bg-white hover:border-emerald-300',
          )}
        >
          🕌 {isRtl ? 'الأنبياء' : 'Prophets'}
          {selectedProphet && <X className="w-3 h-3 opacity-70" onClick={e => { e.stopPropagation(); setSelectedProphet(null); }} />}
        </button>
        {activeFilterCount > 0 && (
          <button onClick={clearFilters} className="min-h-11 text-xs text-gray-500 hover:text-red-500 transition-colors px-2">
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
                  'flex min-h-9 items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-all',
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
                  'min-h-9 text-xs px-2.5 py-1 rounded-full border transition-all',
                  isRtl && 'font-arabic',
                  active
                    ? 'bg-emerald-600 text-white border-emerald-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-emerald-300',
                )}
              >
                {prophetLabel(prophet, isRtl)}
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
              <button type="button" onClick={() => setSelectedOccasion(null)} aria-label={isRtl ? 'إزالة الفلتر' : 'Remove filter'} className="inline-flex min-h-6 min-w-6 items-center justify-center hover:text-red-500">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
          {selectedProphet && (
            <span className="inline-flex items-center gap-1 text-[11px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
              🕌 {prophetLabel(selectedProphet, isRtl)}
              <button type="button" onClick={() => setSelectedProphet(null)} aria-label={isRtl ? 'إزالة الفلتر' : 'Remove filter'} className="inline-flex min-h-6 min-w-6 items-center justify-center hover:text-red-500">
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
              ? `عرض ${formatCount(filtered.length, true)} من ${formatCount(QURANIC_DUAS.length, true)} دعاءً`
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
            <button onClick={clearFilters} className="mt-3 min-h-11 px-3 text-xs text-teal-600 hover:underline">
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
            ? 'النص القرآني: مشروع تنزيل (رواية حفص) · الشرح: تفسير البغوي وتفسير ابن كثير · لا محتوى مُولَّد بالذكاء الاصطناعي'
            : "Arabic: Tanzil Project (Ḥafṣ ʿan ʿĀṣim) · English: Saheeh International via QuranEnc.com · No AI-generated content"}
        </p>
        <p className="text-[10px] text-gray-300 mt-1">
          {isRtl ? 'كل دعاء مرتبط بمرجعه القرآني الدقيق' : 'Every duʿā linked to its exact Quranic reference'}
        </p>
      </footer>
    </div>
  );
}
