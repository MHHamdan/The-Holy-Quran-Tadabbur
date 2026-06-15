import { useState } from 'react';
import { X, ChevronRight } from 'lucide-react';
import { usePersonaStore, PERSONA_META, type Persona } from '../../stores/personaStore';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        {/* Header */}
        <div className="relative bg-gradient-to-br from-primary-700 to-primary-900 text-white px-6 py-7 rounded-t-2xl">
          <button
            onClick={skipOnboarding}
            className="absolute top-4 end-4 p-1 rounded-full hover:bg-white/20 transition-colors"
            aria-label="Skip"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="text-3xl mb-2">📿</div>
          <h2 className={clsx('text-xl font-bold mb-1', isRtl && 'font-arabic')}>
            {isRtl ? 'مرحباً بك في تدبّر' : 'Welcome to Tadabbur'}
          </h2>
          <p className={clsx('text-primary-200 text-sm', isRtl && 'font-arabic')}>
            {isRtl
              ? 'أخبرنا عن نفسك حتى نهيّئ لك تجربة مناسبة'
              : 'Tell us about yourself so we can tailor your experience'}
          </p>
        </div>

        {/* Persona grid */}
        <div className="p-5">
          <p className={clsx('text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide', isRtl && 'font-arabic text-right')}>
            {isRtl ? 'من أنت؟' : 'Who are you?'}
          </p>
          <div className="grid grid-cols-2 gap-3">
            {personas.map(([key, meta]) => (
              <button
                key={key}
                onClick={() => setSelected(key)}
                className={clsx(
                  'flex flex-col items-start gap-1 p-3.5 rounded-xl border-2 transition-all text-start',
                  selected === key
                    ? 'border-primary-500 bg-primary-50 shadow-sm'
                    : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
                )}
              >
                <span className="text-2xl">{meta.emoji}</span>
                <span className={clsx('font-semibold text-sm text-gray-800', isRtl && 'font-arabic')}>
                  {isRtl ? meta.labelAr : meta.labelEn}
                </span>
                <span className={clsx('text-xs text-gray-500 leading-tight', isRtl && 'font-arabic')}>
                  {isRtl ? meta.descAr : meta.descEn}
                </span>
              </button>
            ))}
          </div>

          {/* CTA */}
          <div className="mt-5 flex flex-col gap-2">
            <button
              onClick={handleConfirm}
              disabled={!selected}
              className={clsx(
                'w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all',
                selected
                  ? 'bg-primary-700 hover:bg-primary-800 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              )}
            >
              {isRtl ? 'ابدأ رحلتك' : 'Start my journey'}
              <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
            </button>
            <button
              onClick={skipOnboarding}
              className={clsx('text-xs text-gray-400 hover:text-gray-600 transition-colors py-1', isRtl && 'font-arabic')}
            >
              {isRtl ? 'تخطي في الوقت الحالي' : 'Skip for now'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
