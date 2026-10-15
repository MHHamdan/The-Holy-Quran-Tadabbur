import clsx from 'clsx';
import { Flag, Languages } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t, type Language } from '../../i18n/translations';
import { useFeedbackDialog } from '../feedback/feedbackStore';
import { EXTERNAL_ITEMS, MORE_SECTIONS } from './navConfig';
import { HubGrid } from './HubGrid';

/** Language switch as a two-option segmented control. Each option is labelled
 *  in its own language. */
export function LanguageSegmented({ className }: { className?: string }) {
  const { language, setLanguage } = useLanguageStore();
  const options: { value: Language; label: string }[] = [
    { value: 'ar', label: 'العربية' },
    { value: 'en', label: 'English' },
  ];
  return (
    <div
      role="radiogroup"
      aria-label={t('more_language', language)}
      className={clsx('inline-flex rounded-lg border border-gray-300 bg-white p-1', className)}
    >
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={language === o.value}
          lang={o.value}
          dir={o.value === 'ar' ? 'rtl' : 'ltr'}
          onClick={() => setLanguage(o.value)}
          className={clsx(
            'min-h-11 min-w-[6rem] rounded-md px-4 text-sm font-medium transition-colors',
            o.value === 'ar' && 'font-arabic',
            language === o.value ? 'bg-primary-700 text-white' : 'text-gray-700 hover:bg-gray-100',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Body of the More sheet and the /more page. */
export function MoreContent({ onNavigate, compact = false }: { onNavigate?: () => void; compact?: boolean }) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const openFeedback = useFeedbackDialog((s) => s.openDialog);
  const headingClass = clsx('mb-2 text-sm font-bold text-gray-700', isAr && 'font-arabic');

  return (
    <div className="space-y-6">
      {MORE_SECTIONS.map((section) => (
        <section key={section.id} aria-labelledby={`more-${section.id}`}>
          <h3 id={`more-${section.id}`} className={headingClass}>
            {t(section.titleKey, language)}
          </h3>
          <HubGrid items={section.items} language={language} compact={compact} onNavigate={onNavigate} />
        </section>
      ))}

      <section aria-labelledby="more-settings">
        <h3 id="more-settings" className={headingClass}>
          {t('more_section_settings', language)}
        </h3>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Languages className="h-5 w-5 text-gray-600" aria-hidden="true" />
            <span className={clsx('text-sm text-gray-800', isAr && 'font-arabic')}>{t('more_language', language)}</span>
            <LanguageSegmented />
          </div>
          <button
            type="button"
            onClick={() => {
              onNavigate?.();
              openFeedback();
            }}
            className={clsx(
              'inline-flex min-h-11 items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 text-sm font-medium text-amber-900 hover:bg-amber-100',
              isAr && 'font-arabic',
            )}
          >
            <Flag className="h-4 w-4" aria-hidden="true" />
            {t('more_report_issue', language)}
          </button>
        </div>
      </section>

      <section aria-labelledby="more-external">
        <h3 id="more-external" className={headingClass}>
          {t('more_section_external', language)}
        </h3>
        <p className={clsx('mb-2 text-xs text-gray-600', isAr && 'font-arabic')}>{t('more_external_note', language)}</p>
        <HubGrid items={EXTERNAL_ITEMS} language={language} compact onNavigate={onNavigate} />
      </section>
    </div>
  );
}
