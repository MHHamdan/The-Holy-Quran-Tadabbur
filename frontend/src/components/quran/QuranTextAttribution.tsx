/**
 * Attribution the Qur'an text's licence requires wherever it is shown:
 * Tanzil Project, CC BY 3.0, with a link to tanzil.net.
 */
import clsx from 'clsx';
import type { Language } from '../../i18n/translations';

export function QuranTextAttribution({ language, className }: { language: Language; className?: string }) {
  const ar = language === 'ar';
  return (
    <p className={clsx('text-[11px] text-gray-400', ar && 'font-arabic', className)} dir={ar ? 'rtl' : 'ltr'}>
      {ar ? 'نص القرآن الكريم: ' : 'Qur’an text: '}
      <a href="https://tanzil.net" target="_blank" rel="noopener noreferrer" className="underline hover:text-primary-600" dir="ltr">
        Tanzil Project (tanzil.net)
      </a>
      {ar ? '، رخصة المشاع الإبداعي CC BY 3.0، كما نُشر دون تعديل.' : ', CC BY 3.0, reproduced without change.'}
    </p>
  );
}
