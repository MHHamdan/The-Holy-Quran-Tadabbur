import type { ReactNode } from 'react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';

/** Common frame for the hub pages (/explore, /memorise, /more). */
export function HubPage({ titleKey, subtitleKey, children }: { titleKey: string; subtitleKey: string; children: ReactNode }) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8" dir={isAr ? 'rtl' : 'ltr'}>
      <h1 className={clsx('text-2xl font-bold text-gray-900', isAr && 'font-arabic')}>{t(titleKey, language)}</h1>
      <p className={clsx('mb-6 mt-1 text-gray-600', isAr && 'font-arabic')}>{t(subtitleKey, language)}</p>
      {children}
    </div>
  );
}
