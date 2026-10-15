/**
 * Label for theme and concept pages: their summaries, relations and
 * classifications are app-authored analysis, not tafsir. Sources are shown
 * where a statement cites one; statements without a verified source are
 * withheld by the API (see backend/app/api/routes/themes.py "Evidence gate").
 *
 * One language per render, with its own dir, so Arabic and English never
 * share a container direction.
 */
import clsx from 'clsx';
import { Info } from 'lucide-react';
import type { Language } from '../../i18n/translations';

const COPY: Record<Language, { title: string; body: string }> = {
  ar: {
    title: 'أداة دراسة تحليلية، وليست تفسيرًا',
    body: 'التصنيفات والملخصات هنا من إعداد التطبيق. تُذكر المصادر حيث تتوفر، ويُحجب كل ملخص لا يستند إلى مصدر تفسير موثّق، فارجع إلى كتب التفسير وأهل العلم.',
  },
  en: {
    title: 'Analytical study aid, not tafsir',
    body: 'The groupings and summaries here are prepared by the app. Sources are shown where available, and any summary without a verified tafsir source is withheld. Refer to the works of tafsir and to scholars.',
  },
};

export function AnalyticalStudyAidNotice({
  language,
  variant = 'light',
  className,
}: {
  language: Language;
  /** 'dark' for use on a coloured hero background. */
  variant?: 'light' | 'dark';
  className?: string;
}) {
  const ar = language === 'ar';
  const copy = COPY[ar ? 'ar' : 'en'];
  return (
    <div
      role="note"
      data-testid="analytical-study-aid"
      dir={ar ? 'rtl' : 'ltr'}
      lang={ar ? 'ar' : 'en'}
      className={clsx(
        'flex items-start gap-2 rounded-lg border px-3 py-2 text-sm',
        variant === 'dark'
          ? 'border-white/30 bg-white/10 text-white'
          : 'border-amber-200 bg-amber-50 text-amber-900',
        ar && 'font-arabic',
        className,
      )}
    >
      <Info className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
      <p className={ar ? 'text-right' : 'text-left'}>
        <strong className="font-semibold">{copy.title}.</strong> {copy.body}
      </p>
    </div>
  );
}
