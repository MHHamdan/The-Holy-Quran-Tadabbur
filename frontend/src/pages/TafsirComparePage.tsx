/**
 * TafsirComparePage — read one verse through every tafsir at once.
 *
 * The surface competitors do not have: al-Tabari, al-Qurtubi, Ibn Kathir,
 * al-Jalalayn and al-Muyassar on a single page, in chronological order, each
 * labelled with its author, era and method, and each citable by chunk id.
 */
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, BookOpen } from 'lucide-react';

import { TafsirComparison } from '../components/tafseer/TafsirComparison';
import { formatCount } from '../components/tafseer/licenceLabels';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { SURAH_NAMES, SURAH_VERSE_COUNTS } from '../data/surahNames';

function clampSurah(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(114, Math.max(1, Math.trunc(value)));
}

function clampAyah(surah: number, value: number): number {
  const max = SURAH_VERSE_COUNTS[surah - 1] ?? 1;
  if (!Number.isFinite(value)) return 1;
  return Math.min(max, Math.max(1, Math.trunc(value)));
}

export function TafsirComparePage() {
  const params = useParams<{ surah?: string; ayah?: string }>();
  const navigate = useNavigate();
  const { language, direction } = useLanguageStore();

  const surah = clampSurah(Number(params.surah ?? 2));
  const ayah = clampAyah(surah, Number(params.ayah ?? 255));

  // Keep the URL canonical when a param is out of range, so a shared link to
  // 2:9999 resolves to a real verse rather than a dead page.
  useEffect(() => {
    if (String(surah) !== params.surah || String(ayah) !== params.ayah) {
      navigate(`/tafsir/compare/${surah}/${ayah}`, { replace: true });
    }
  }, [surah, ayah, params.surah, params.ayah, navigate]);

  const [surahInput, setSurahInput] = useState(String(surah));
  const [ayahInput, setAyahInput] = useState(String(ayah));

  useEffect(() => {
    setSurahInput(String(surah));
    setAyahInput(String(ayah));
  }, [surah, ayah]);

  const ayahCount = SURAH_VERSE_COUNTS[surah - 1] ?? 1;
  const surahName = useMemo(() => {
    const meta = SURAH_NAMES[surah - 1];
    if (!meta) return `${surah}`;
    return language === 'ar' ? meta.ar : meta.en;
  }, [surah, language]);

  const go = (nextSurah: number, nextAyah: number) => {
    const s = clampSurah(nextSurah);
    navigate(`/tafsir/compare/${s}/${clampAyah(s, nextAyah)}`);
  };

  // In RTL the "previous" affordance points right, so the icons swap rather
  // than the labels — an arrow that points away from the reading direction
  // reads as "forward" to an Arabic reader.
  const PrevIcon = direction === 'rtl' ? ArrowRight : ArrowLeft;
  const NextIcon = direction === 'rtl' ? ArrowLeft : ArrowRight;

  return (
    <div className="mx-auto w-full min-w-0 max-w-4xl px-4 py-6">
      <header className="mb-5">
        <h1 className="flex items-center gap-2 text-xl font-bold text-stone-900">
          <BookOpen className="h-5 w-5 text-primary-600" />
          {t('tafsir_compare_title', language)}
        </h1>
        <p className="mt-1 text-sm text-stone-500">
          {t('tafsir_compare_subtitle', language)}
        </p>
      </header>

      <div className="mb-6 flex flex-wrap items-end gap-3 rounded-xl border border-stone-200 bg-white p-3">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-stone-600">
            {language === 'ar' ? 'السورة' : 'Surah'}
          </span>
          <select
            value={surahInput}
            onChange={(e) => go(Number(e.target.value), 1)}
            className="min-h-11 max-w-[60vw] rounded-md border border-stone-300 bg-white px-2 py-1.5 text-sm"
          >
            {SURAH_NAMES.map((meta, i) => (
              <option key={i + 1} value={i + 1}>
                {i + 1}. {language === 'ar' ? meta.ar : meta.en}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-stone-600">
            {language === 'ar' ? 'الآية' : 'Ayah'}
          </span>
          <input
            type="number"
            min={1}
            max={ayahCount}
            value={ayahInput}
            onChange={(e) => setAyahInput(e.target.value)}
            onBlur={() => go(surah, Number(ayahInput))}
            onKeyDown={(e) => {
              if (e.key === 'Enter') go(surah, Number(ayahInput));
            }}
            className="min-h-11 w-24 rounded-md border border-stone-300 bg-white px-2 py-1.5 text-sm tabular-nums"
            dir="ltr"
          />
        </label>

        {/* The surah name is in the UI language; the verse range is isolated
            so its digits never reorder inside an Arabic run. */}
        <span className="pb-3 text-xs text-stone-400" dir={language === 'ar' ? 'rtl' : 'ltr'}>
          <bdi>{surahName}</bdi>{language === 'ar' ? '، ' : ' · '}
          <bdi dir="ltr">{formatCount(1, language)}–{formatCount(ayahCount, language)}</bdi>
        </span>

        <div className="ms-auto flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => go(surah, ayah - 1)}
            disabled={ayah <= 1}
            aria-label={language === 'ar' ? 'الآية السابقة' : 'Previous ayah'}
            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-stone-300 bg-white text-stone-600 hover:bg-stone-50 disabled:opacity-40"
          >
            <PrevIcon className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => go(surah, ayah + 1)}
            disabled={ayah >= ayahCount}
            aria-label={language === 'ar' ? 'الآية التالية' : 'Next ayah'}
            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-stone-300 bg-white text-stone-600 hover:bg-stone-50 disabled:opacity-40"
          >
            <NextIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Source links carry long unbroken URLs (a pinned dataset revision is
          ~100 characters). Letting them wrap anywhere keeps the page inside a
          360px phone viewport, so the bottom tab bar is not pushed off screen. */}
      <div className="min-w-0 [overflow-wrap:anywhere]">
        <TafsirComparison key={`${surah}:${ayah}`} surah={surah} ayah={ayah} showHeading={false} />
      </div>
    </div>
  );
}

export default TafsirComparePage;
