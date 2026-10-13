/**
 * Structural markers shown with a verse: the start of a hizb quarter and the
 * sajdah (prostration) verses. Data: data/manifests/quran_structure_markers.json
 * (Tanzil metadata reconciled with the Madinah Mushaf).
 */
import clsx from 'clsx';
import type { Verse } from '../../lib/api';
import type { Language } from '../../i18n/translations';

const toArabicNum = (n: number) => n.toString().replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[Number(d)]);

const QUARTER_LABELS = {
  en: ['Hizb', '¼ Hizb', '½ Hizb', '¾ Hizb'],
  ar: ['الحزب', 'ربع الحزب', 'نصف الحزب', 'ثلاثة أرباع الحزب'],
};

export function VerseMarkers({
  verse,
  language,
  only,
}: {
  verse: Verse;
  language: Language;
  /** Render just one marker (the Mushaf view puts the quarter before the verse, the sajdah after). */
  only?: 'quarter' | 'sajdah';
}) {
  const ar = language === 'ar';
  const quarterStart = !!verse.quarter_start && only !== 'sajdah';
  const sajdah = !!verse.sajda_type && only !== 'quarter';
  if (!quarterStart && !sajdah) return null;
  const hizb = verse.hizb_no ?? 0;
  const position = ((verse.rub_no ?? 1) - 1) % 4;

  return (
    <span dir={ar ? 'rtl' : 'ltr'} className={clsx('inline-flex flex-wrap items-center gap-1.5', ar && 'font-arabic')}>
      {quarterStart && hizb > 0 && (
        <span
          className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[11px] font-medium text-emerald-800"
          title={ar ? 'بداية ربع حزب' : 'Start of a hizb quarter'}
        >
          <span aria-hidden="true">۞</span>
          {ar
            ? `${QUARTER_LABELS.ar[position]} ${toArabicNum(hizb)}`
            : `${QUARTER_LABELS.en[position]} ${hizb}`}
        </span>
      )}
      {sajdah && (
        <span
          className="inline-flex items-center gap-1 rounded-full bg-violet-50 border border-violet-200 px-2 py-0.5 text-[11px] font-medium text-violet-800"
          title={ar ? 'موضع سجود التلاوة' : 'Place of prostration of recitation'}
        >
          <span aria-hidden="true">۩</span>
          {ar ? 'سجدة' : 'Sajdah'}
        </span>
      )}
    </span>
  );
}
