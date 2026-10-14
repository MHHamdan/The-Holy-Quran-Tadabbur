/**
 * Verse Memorisation — spaced-repetition flashcards
 *
 * Front: the previous verse as the cue (or the surah opening for verse 1).
 * Back: the verse to recall. Grading it Again / Hard / Good / Easy schedules
 * the next review (lib/srs.ts, SM-2 family), so well-known verses come back
 * rarely and weak ones soon, as in Quran Companion and Anki.
 *
 * Two queues: "Review" (every due verse, any surah) and "Learn" (the chosen
 * surah, in order: due and new verses). Progress is device-local.
 *
 * Safety: no Qur'an text is stored here. Both sides are fetched from the
 * verified verse API at display time.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { Layers, Eye, BookOpen, CalendarClock, Sparkles, RotateCcw } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { useReaderSettingsStore, verseTextFor } from '../stores/readerSettingsStore';
import { quranApi } from '../lib/api';
import { SURAH_NAMES } from '../data/surahNames';
import { SURAH_ATLAS_DATA } from '../data/surahAtlas';
import {
  cardKey, isDue, loadDeck, newCard, parseKey, previewIntervals, review, saveDeck, today,
  type Deck, type Grade,
} from '../lib/srs';
import { QuranTextAttribution } from '../components/quran/QuranTextAttribution';

type Mode = 'review' | 'learn';

const ayahCount = (surah: number) => SURAH_ATLAS_DATA.find((s) => s.surahNumber === surah)?.ayahCount ?? 7;
const toArabicNum = (n: number) => n.toString().replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[Number(d)]);

function formatInterval(days: number, ar: boolean): string {
  if (days === 0) return ar ? 'الآن' : 'now';
  if (days < 30) return ar ? `${toArabicNum(days)} يوم` : `${days}d`;
  const months = Math.round(days / 30);
  return ar ? `${toArabicNum(months)} شهر` : `${months}mo`;
}

/** The queue for a session: keys in the order they should be shown. */
function buildQueue(deck: Deck, mode: Mode, surah: number): string[] {
  const day = today();
  if (mode === 'review') {
    return Object.entries(deck)
      .filter(([, c]) => isDue(c, day))
      .sort(([, a], [, b]) => a.due.localeCompare(b.due))
      .map(([k]) => k);
  }
  const keys: string[] = [];
  for (let a = 1; a <= ayahCount(surah); a++) {
    const k = cardKey(surah, a);
    const c = deck[k];
    if (!c || isDue(c, day)) keys.push(k);
  }
  return keys;
}

export function FlashcardsPage() {
  const { language } = useLanguageStore();
  const ar = language === 'ar';
  const { script } = useReaderSettingsStore();

  const [deck, setDeck] = useState<Deck>(loadDeck);
  const [mode, setMode] = useState<Mode>(() =>
    Object.values(loadDeck()).some((c) => isDue(c)) ? 'review' : 'learn');
  const [surah, setSurah] = useState(1);
  const [queue, setQueue] = useState<string[]>(() => buildQueue(deck, mode, surah));
  const [revealed, setRevealed] = useState(false);
  const [reviewedToday, setReviewedToday] = useState(0);

  // Rebuild the queue when the session parameters change (not after each grade).
  useEffect(() => {
    setQueue(buildQueue(loadDeck(), mode, surah));
    setRevealed(false);
  }, [mode, surah]);

  const dueCount = useMemo(() => Object.values(deck).filter((c) => isDue(c)).length, [deck]);
  const learnedInSurah = useMemo(() => {
    let n = 0;
    for (let a = 1; a <= ayahCount(surah); a++) if ((deck[cardKey(surah, a)]?.reps ?? 0) > 0) n++;
    return n;
  }, [deck, surah]);

  const current = queue[0] ? parseKey(queue[0]) : null;
  const card = current ? deck[queue[0]] ?? newCard() : null;

  // Cue verse (previous) and target verse, from the verse API.
  const { data: verses, isLoading, isError, refetch } = useQuery({
    queryKey: ['flashcard', current?.surah, current?.ayah],
    enabled: !!current,
    staleTime: Infinity,
    queryFn: async () => {
      const { surah: s, ayah: a } = current!;
      const res = await quranApi.getVerseRange(s, Math.max(1, a - 1), a);
      return res.data;
    },
  });
  const target = verses?.find((v) => v.aya_no === current?.ayah);
  const cue = current && current.ayah > 1 ? verses?.find((v) => v.aya_no === current.ayah - 1) : undefined;

  const grade = useCallback((g: Grade) => {
    if (!queue[0] || !card) return;
    const key = queue[0];
    const next = review(card, g);
    const updated = { ...deck, [key]: next };
    setDeck(updated);
    saveDeck(updated);
    setReviewedToday((n) => n + 1);
    // "Again" comes back at the end of this session; others leave the queue.
    setQueue((q) => (g === 'again' ? [...q.slice(1), key] : q.slice(1)));
    setRevealed(false);
  }, [queue, card, deck]);

  const intervals = card ? previewIntervals(card) : null;
  const surahName = (n: number) => (ar ? SURAH_NAMES[n - 1]?.ar : SURAH_NAMES[n - 1]?.en);
  const quranFont = script === 'uthmani' ? 'font-mushaf' : 'font-arabic';

  const grades: { g: Grade; ar: string; en: string; cls: string }[] = [
    { g: 'again', ar: 'نسيت', en: 'Again', cls: 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100' },
    { g: 'hard', ar: 'صعب', en: 'Hard', cls: 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100' },
    { g: 'good', ar: 'جيد', en: 'Good', cls: 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100' },
    { g: 'easy', ar: 'سهل', en: 'Easy', cls: 'bg-sky-50 text-sky-800 border-sky-200 hover:bg-sky-100' },
  ];

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 py-8" dir={ar ? 'rtl' : 'ltr'}>
      <div className="flex items-center gap-3 mb-6">
        <Layers className="w-7 h-7 text-emerald-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', ar && 'font-arabic')}>
            {ar ? 'بطاقات الحفظ' : 'Memorization Flashcards'}
          </h1>
          <p className={clsx('text-xs text-gray-500 mt-0.5', ar && 'font-arabic')}>
            {ar
              ? 'مراجعة متباعدة: تعود الآية الصعبة قريبًا والمتقنة بعد مدة أطول'
              : 'Spaced repetition: weak verses come back soon, strong ones later'}
          </p>
        </div>
      </div>

      {/* Mode */}
      <div role="tablist" className="grid grid-cols-2 gap-2 mb-4">
        {([
          ['review', <CalendarClock key="i" className="w-4 h-4" />, ar ? `مراجعة اليوم (${toArabicNum(dueCount)})` : `Review due (${dueCount})`],
          ['learn', <Sparkles key="i" className="w-4 h-4" />, ar ? 'حفظ سورة' : 'Learn a surah'],
        ] as const).map(([m, icon, label]) => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={clsx(
              'flex items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-semibold',
              mode === m ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : 'border-gray-200 text-gray-600 hover:bg-gray-50',
              ar && 'font-arabic',
            )}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>

      {mode === 'learn' && (
        <div className="mb-4">
          <label htmlFor="fc-surah" className={clsx('block text-xs font-semibold text-gray-500 mb-1', ar && 'font-arabic')}>
            {ar ? 'السورة' : 'Surah'}
          </label>
          <select
            id="fc-surah"
            value={surah}
            onChange={(e) => setSurah(Number(e.target.value))}
            className={clsx('w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-800', ar && 'font-arabic')}
          >
            {SURAH_NAMES.map((sn, i) => (
              <option key={i + 1} value={i + 1}>{i + 1}. {ar ? sn.ar : sn.en}</option>
            ))}
          </select>
          <div className="mt-2 flex justify-between text-xs text-gray-500">
            <span className={clsx(ar && 'font-arabic')}>
              {ar
                ? `${toArabicNum(learnedInSurah)} من ${toArabicNum(ayahCount(surah))} آية قيد المراجعة`
                : `${learnedInSurah} / ${ayahCount(surah)} verses in review`}
            </span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mt-1">
            <div className="h-full bg-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${Math.round((learnedInSurah / ayahCount(surah)) * 100)}%` }} />
          </div>
        </div>
      )}

      {/* Card */}
      {!current ? (
        <div className={clsx('rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center', ar && 'font-arabic')}>
          <p className="text-lg font-semibold text-emerald-800">
            {mode === 'review'
              ? (ar ? 'لا مراجعات مستحقة الآن' : 'Nothing due right now')
              : (ar ? 'أتممت هذه السورة لليوم' : 'This surah is done for today')}
          </p>
          <p className="text-sm text-emerald-700 mt-1">
            {reviewedToday > 0 && (ar ? `راجعت ${toArabicNum(reviewedToday)} بطاقة. ` : `${reviewedToday} cards reviewed. `)}
            {mode === 'review'
              ? (ar ? 'اختر «حفظ سورة» لإضافة آيات جديدة.' : 'Choose “Learn a surah” to add new verses.')
              : (ar ? 'عد غدًا، أو اختر سورة أخرى.' : 'Come back tomorrow, or pick another surah.')}
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-gray-100 bg-white p-5 min-h-[260px] flex flex-col gap-4">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span className={clsx(ar && 'font-arabic')}>
              {surahName(current.surah)} · {ar ? `الآية ${toArabicNum(current.ayah)}` : `verse ${current.ayah}`}
            </span>
            <span>{ar ? `${toArabicNum(queue.length)} متبقية` : `${queue.length} left`}</span>
          </div>

          {isLoading ? (
            <div className="h-32 animate-pulse bg-gray-100 rounded-xl" />
          ) : isError ? (
            <div className="text-center text-sm text-amber-700">
              {ar ? 'تعذّر تحميل الآية.' : 'Could not load the verse.'}{' '}
              <button onClick={() => refetch()} className="underline">{ar ? 'إعادة المحاولة' : 'Retry'}</button>
            </div>
          ) : (
            <>
              {/* Cue */}
              <div className="rounded-xl bg-gray-50 p-4" dir="rtl">
                <p className={clsx('text-xs text-gray-500 mb-2', ar ? 'font-arabic' : 'text-left')} dir={ar ? 'rtl' : 'ltr'}>
                  {cue
                    ? (ar ? 'ما الآية التي تلي:' : 'What comes after:')
                    : (ar ? `أول آية في سورة ${SURAH_NAMES[current.surah - 1]?.ar}` : `The first verse of ${SURAH_NAMES[current.surah - 1]?.en}`)}
                </p>
                {cue && (
                  <p className={clsx('text-xl leading-loose text-gray-800', quranFont)}>
                    {verseTextFor(cue, script).replace(/^\uFEFF/, '')}
                  </p>
                )}
              </div>

              {/* Answer */}
              {!revealed ? (
                <button
                  onClick={() => setRevealed(true)}
                  className={clsx('mx-auto flex items-center gap-2 px-6 py-2.5 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700', ar && 'font-arabic')}
                >
                  <Eye className="w-4 h-4" />
                  {ar ? 'أظهر الآية' : 'Show the verse'}
                </button>
              ) : target ? (
                <div className="rounded-xl border-2 border-emerald-200 p-4" dir="rtl">
                  <p className={clsx('text-2xl leading-loose text-gray-900', quranFont)}>
                    {verseTextFor(target, script).replace(/^\uFEFF/, '')}
                  </p>
                  <Link
                    to={`/quran/${current.surah}?aya=${current.ayah}`}
                    className={clsx('mt-2 inline-flex items-center gap-1 text-xs text-primary-600 hover:underline', ar && 'font-arabic')}
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    {ar ? 'افتح في القارئ' : 'Open in the reader'}
                  </Link>
                </div>
              ) : null}

              {revealed && intervals && (
                <div className="grid grid-cols-4 gap-2" role="group" aria-label={ar ? 'قيّم تذكرك' : 'Rate your recall'}>
                  {grades.map(({ g, ar: lAr, en, cls }) => (
                    <button
                      key={g}
                      onClick={() => grade(g)}
                      className={clsx('rounded-xl border px-2 py-2 text-sm font-semibold', cls, ar && 'font-arabic')}
                    >
                      {ar ? lAr : en}
                      <span className="block text-[11px] font-normal opacity-75">{formatInterval(intervals[g], ar)}</span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      <QuranTextAttribution language={language} className="mt-4 text-center" />

      {Object.keys(deck).length > 0 && (
        <div className="mt-8 p-4 bg-gray-50 rounded-2xl border border-gray-100 text-sm text-gray-600">
          <p className={clsx(ar && 'font-arabic')}>
            {ar
              ? `${toArabicNum(Object.keys(deck).length)} آية في جدول المراجعة`
              : `${Object.keys(deck).length} verses in your review schedule`}
          </p>
          <button
            onClick={() => {
              if (confirm(ar ? 'حذف كل جدول المراجعة؟' : 'Delete your whole review schedule?')) {
                saveDeck({});
                setDeck({});
                setQueue(buildQueue({}, mode, surah));
              }
            }}
            className={clsx('mt-2 inline-flex items-center gap-1 text-xs text-red-500 hover:text-red-700', ar && 'font-arabic')}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            {ar ? 'إعادة التعيين' : 'Reset'}
          </button>
        </div>
      )}
    </div>
  );
}
