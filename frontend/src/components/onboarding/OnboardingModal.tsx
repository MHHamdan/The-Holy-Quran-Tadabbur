import { useState } from 'react';
import { X, ChevronRight } from 'lucide-react';
import { usePersonaStore, PERSONA_META, type Persona } from '../../stores/personaStore';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { Dialog } from '../ui/Dialog';
import { LanguageSegmented } from '../layout/MoreContent';
import clsx from 'clsx';

/** First-run dialog: language choice, a one-line description of the app,
 *  and an optional persona. Escape, the close button or "Later" skip it. */
export function OnboardingModal() {
  const { language } = useLanguageStore();
  const { setPersona, skipOnboarding } = usePersonaStore();
  const [selected, setSelected] = useState<Persona | null>(null);
  const isRtl = language === 'ar';

  const personas = Object.entries(PERSONA_META) as [Persona, typeof PERSONA_META[Persona]][];

  function handleConfirm() {
    if (selected) setPersona(selected);
    else skipOnboarding();
  }

  return (
    <Dialog
      open
      onClose={skipOnboarding}
      labelledBy="onboarding-title"
      dir={isRtl ? 'rtl' : 'ltr'}
      className="max-w-lg max-h-[90vh] overflow-y-auto"
    >
      {/* Header */}
      <div className="relative bg-gradient-to-br from-primary-700 to-primary-900 text-white px-6 py-6 rounded-t-2xl">
        <button
          type="button"
          onClick={skipOnboarding}
          className="tap absolute top-2 end-2 rounded-full hover:bg-white/20 transition-colors"
          aria-label={isRtl ? 'تخطَّ' : 'Skip'}
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </button>
        <h2 id="onboarding-title" className={clsx('text-xl font-bold mb-1 pe-10', isRtl && 'font-arabic')}>
          {isRtl ? 'مرحباً بك في تدبّر' : 'Welcome to Tadabbur'}
        </h2>
        <p className={clsx('text-primary-100 text-sm', isRtl && 'font-arabic')}>{t('onboarding_intro', language)}</p>
      </div>

      <div className="p-5">
        {/* Language */}
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <span className={clsx('text-sm font-medium text-gray-700', isRtl && 'font-arabic')}>
            {t('onboarding_language', language)}
          </span>
          <LanguageSegmented />
        </div>

        {/* Persona grid */}
        <p className={clsx('text-sm text-gray-700 mb-3 font-medium', isRtl && 'font-arabic')}>
          {isRtl ? 'أخبرنا عن نفسك لنقترح عليك البداية المناسبة (اختياري)' : 'Tell us about yourself so we can suggest where to start (optional)'}
        </p>
        <div className="grid grid-cols-2 gap-3">
          {personas.map(([key, meta]) => (
            <button
              key={key}
              type="button"
              onClick={() => setSelected(key)}
              aria-pressed={selected === key}
              className={clsx(
                'flex flex-col items-start gap-1 p-3.5 rounded-xl border-2 transition-all text-start',
                selected === key
                  ? 'border-primary-500 bg-primary-50 shadow-sm'
                  : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
              )}
            >
              <span className="text-2xl" aria-hidden="true">{meta.emoji}</span>
              <span className={clsx('font-semibold text-sm text-gray-800', isRtl && 'font-arabic')}>
                {isRtl ? meta.labelAr : meta.labelEn}
              </span>
              <span className={clsx('text-xs text-gray-600 leading-tight', isRtl && 'font-arabic')}>
                {isRtl ? meta.descAr : meta.descEn}
              </span>
            </button>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-5 flex flex-col gap-2">
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!selected}
            className={clsx(
              'w-full min-h-11 flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all',
              isRtl && 'font-arabic',
              selected
                ? 'bg-primary-700 hover:bg-primary-800 text-white shadow-sm'
                : 'bg-gray-100 text-gray-500 cursor-not-allowed'
            )}
          >
            {isRtl ? 'ابدأ رحلتك' : 'Start my journey'}
            <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={skipOnboarding}
            className={clsx('min-h-11 text-sm text-gray-600 hover:text-gray-800 transition-colors', isRtl && 'font-arabic')}
          >
            {isRtl ? 'لاحقاً' : 'Later'}
          </button>
        </div>
      </div>
    </Dialog>
  );
}
