/**
 * Phase L — Safe Quran AI Prompting Guide
 *
 * Teaches users how to ask precise, source-backed Quranic questions.
 * Reference: "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي"
 *            Prof. Dr. Abdulrahman Al-Shehri
 *
 * Safety rules:
 * - No Quran text generated or displayed here
 * - No tafsir generated here
 * - No fatwa content
 * - Examples are prompts only, not answers
 */
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  BookOpen,
  GraduationCap,
  FlaskConical,
  Scale,
  Info,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import clsx from 'clsx';

// ---------------------------------------------------------------------------
// Good prompt examples
// ---------------------------------------------------------------------------

const GOOD_PROMPTS_EN = [
  'Summarize Tafsir Ibn Kathir on 2:255 with citations.',
  'Compare what Ibn Kathir and Al-Saadi say about Surah Al-Ikhlas.',
  'Show ayahs about patience and group them by theme.',
  'Explain the word غاسق using verified vocabulary sources.',
  'Show related ayahs to 12:18 and explain the relation path.',
  'What did classical scholars say about the meaning of تقوى in 2:2?',
];

const GOOD_PROMPTS_AR = [
  'لخّص تفسير ابن كثير للآية 2:255 مع ذكر المصادر.',
  'قارن بين تفسير ابن كثير والسعدي لسورة الإخلاص.',
  'أرِني آيات الصبر وصنّفها حسب الموضوع.',
  'اشرح كلمة "غاسق" من مصادر اللغة والتفسير الموثوقة.',
  'أرِني الآيات المرتبطة بـ 12:18 واشرح مسار العلاقة.',
  'ماذا قال العلماء الكلاسيكيون عن معنى التقوى في 2:2؟',
];

// ---------------------------------------------------------------------------
// Unsafe prompt examples
// ---------------------------------------------------------------------------

const UNSAFE_PROMPTS_EN = [
  { text: 'Give me a fatwa on this matter.', reason: 'prompt_guide_no_fatwa' },
  { text: 'Interpret this verse without using any sources.', reason: 'prompt_guide_no_unsourced' },
  { text: 'Prove the Big Bang from this ayah.', reason: 'prompt_guide_no_prove_science' },
  { text: 'Tell me the hidden or esoteric meaning of this verse.', reason: 'prompt_guide_no_hidden_meaning' },
  { text: 'Give me any ayah that supports my idea.', reason: 'prompt_guide_no_unsourced' },
];

const UNSAFE_PROMPTS_AR = [
  { text: 'أعطني فتوى في هذه المسألة.', reason: 'prompt_guide_no_fatwa' },
  { text: 'فسّر هذه الآية بدون مصادر.', reason: 'prompt_guide_no_unsourced' },
  { text: 'أثبت نظرية الانفجار الكبير من هذه الآية.', reason: 'prompt_guide_no_prove_science' },
  { text: 'أخبرني بالمعنى الخفي أو الباطني لهذه الآية.', reason: 'prompt_guide_no_hidden_meaning' },
  { text: 'أعطني أي آية تدعم فكرتي.', reason: 'prompt_guide_no_unsourced' },
];

// ---------------------------------------------------------------------------
// Protection features
// ---------------------------------------------------------------------------

const PROTECTIONS: Array<{ icon: React.ElementType; key_ar: string; key_en: string }> = [
  { icon: ShieldCheck, key_ar: 'التحقق من المصادر', key_en: 'Source validation' },
  { icon: FlaskConical, key_ar: 'حارس الإجابة القرآنية (QuranAnswerGuard)', key_en: 'QuranAnswerGuard (post-generation check)' },
  { icon: Scale, key_ar: 'مصنّف الأسئلة (pre-generation)', key_en: 'Question classifier (pre-generation gate)' },
  { icon: GraduationCap, key_ar: 'سير عمل المراجعة العلمية', key_en: 'Scholarly review workflow' },
  { icon: AlertTriangle, key_ar: 'تحذيرات needs_review على المحتوى غير المراجَع', key_en: 'needs_review warnings on unreviewed content' },
  { icon: XCircle, key_ar: 'رفض آمن عند غياب المصدر', key_en: 'Safe refusal when no verified source exists' },
];

// ---------------------------------------------------------------------------
// Core principles
// ---------------------------------------------------------------------------

const PRINCIPLES_KEYS = [
  'prompt_guide_ask_sources',
  'prompt_guide_ask_ayah',
  'prompt_guide_ask_tafsir_source',
  'prompt_guide_ask_comparison',
  'prompt_guide_no_unsourced',
  'prompt_guide_no_fatwa',
  'prompt_guide_no_prove_science',
  'prompt_guide_no_hidden_meaning',
  'prompt_guide_consult_scholars',
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function PromptGuidePage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const goodPrompts = isArabic ? GOOD_PROMPTS_AR : GOOD_PROMPTS_EN;
  const unsafePrompts = isArabic ? UNSAFE_PROMPTS_AR : UNSAFE_PROMPTS_EN;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">

      {/* Header */}
      <div className="text-center space-y-2" dir={isArabic ? 'rtl' : 'ltr'}>
        <div className="flex justify-center mb-4">
          <div className="p-4 rounded-full bg-emerald-100">
            <ShieldCheck className="w-8 h-8 text-emerald-600" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900">
          {t('prompt_guide_title', language)}
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto text-sm leading-relaxed">
          {t('prompt_guide_subtitle', language)}
        </p>
      </div>

      {/* AI disclaimer banner */}
      <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl" dir={isArabic ? 'rtl' : 'ltr'}>
        <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-amber-800 text-sm">{t('prompt_guide_ai_not_scholar', language)}</p>
          <p className="text-amber-700 text-sm mt-1">{t('prompt_guide_purpose_body', language)}</p>
        </div>
      </div>

      {/* Core principles */}
      <Section title={t('prompt_guide_principles_title', language)} isArabic={isArabic}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {PRINCIPLES_KEYS.map((key) => {
            const isUnsafe = key.startsWith('prompt_guide_no_') || key === 'prompt_guide_fatwa_warning';
            return (
              <div
                key={key}
                className={clsx(
                  'flex items-start gap-2 p-3 rounded-lg border text-sm',
                  isUnsafe
                    ? 'bg-red-50 border-red-200 text-red-800'
                    : 'bg-green-50 border-green-200 text-green-800'
                )}
                dir={isArabic ? 'rtl' : 'ltr'}
              >
                {isUnsafe
                  ? <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
                  : <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5 text-green-600" />
                }
                <span>{t(key, language)}</span>
              </div>
            );
          })}
        </div>
      </Section>

      {/* Good prompt examples */}
      <Section title={t('prompt_guide_good_examples_title', language)} isArabic={isArabic}>
        <div className="space-y-2">
          {goodPrompts.map((prompt, i) => (
            <div
              key={i}
              className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg"
              dir={isArabic ? 'rtl' : 'ltr'}
            >
              <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-green-900 font-medium">{prompt}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Unsafe prompt examples */}
      <Section title={t('prompt_guide_unsafe_examples_title', language)} isArabic={isArabic}>
        <div className="space-y-2">
          {unsafePrompts.map((item, i) => (
            <div
              key={i}
              className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg"
              dir={isArabic ? 'rtl' : 'ltr'}
            >
              <XCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-red-800 font-medium">{item.text}</p>
                <p className="text-xs text-red-600 mt-0.5">{t(item.reason, language)}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Scientific miracle warning */}
      <div className="flex items-start gap-3 p-4 bg-orange-50 border-2 border-orange-200 rounded-xl" dir={isArabic ? 'rtl' : 'ltr'}>
        <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-orange-800 text-sm">{t('prompt_guide_scientific_warning', language)}</p>
          <p className="text-orange-700 text-xs mt-1">
            {isArabic
              ? 'الربط القطعي بين الآية والنظريات العلمية ممنوع على هذه المنصة بدون مراجعة علمية وشرعية متخصصة.'
              : 'Asserting a definitive link between a verse and a modern scientific theory is blocked by this platform without specialized scholarly and scientific review.'}
          </p>
        </div>
      </div>

      {/* Fatwa warning */}
      <div className="flex items-start gap-3 p-4 bg-red-50 border-2 border-red-200 rounded-xl" dir={isArabic ? 'rtl' : 'ltr'}>
        <Scale className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-red-800 font-medium">{t('prompt_guide_fatwa_warning', language)}</p>
      </div>

      {/* How the platform protects you */}
      <Section title={t('prompt_guide_protection_title', language)} isArabic={isArabic}>
        <div className="space-y-2">
          {PROTECTIONS.map((p, i) => {
            const Icon = p.icon;
            return (
              <div
                key={i}
                className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-100 rounded-lg"
                dir={isArabic ? 'rtl' : 'ltr'}
              >
                <Icon className="w-4 h-4 text-blue-600 flex-shrink-0" />
                <span className="text-sm text-blue-800">{isArabic ? p.key_ar : p.key_en}</span>
              </div>
            );
          })}
        </div>
      </Section>

      {/* No verified source message */}
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl flex items-start gap-2" dir={isArabic ? 'rtl' : 'ltr'}>
        <BookOpen className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-gray-600">{t('prompt_guide_no_verified_source', language)}</p>
      </div>

    </div>
  );
}

function Section({
  title,
  children,
  isArabic,
}: {
  title: string;
  children: React.ReactNode;
  isArabic: boolean;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-bold text-gray-800" dir={isArabic ? 'rtl' : 'ltr'}>
        {title}
      </h2>
      {children}
    </section>
  );
}

export default PromptGuidePage;
