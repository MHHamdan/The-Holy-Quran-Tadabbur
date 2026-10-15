import { useId } from 'react';
import clsx from 'clsx';
import { X } from 'lucide-react';
import { Dialog } from '../ui/Dialog';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { MoreContent } from './MoreContent';

/** "More" menu: a bottom sheet on phones, a centred panel on larger screens. */
export function MoreSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const titleId = useId();

  return (
    <Dialog open={open} onClose={onClose} labelledBy={titleId} dir={isAr ? 'rtl' : 'ltr'} variant="sheet">
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-100 bg-white px-4 py-2">
        <h2 id={titleId} className={clsx('text-base font-bold text-gray-900', isAr && 'font-arabic')}>
          {t('nav_more_dialog_label', language)}
        </h2>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={onClose}
            aria-label={t('close', language)}
            className="tap rounded-lg text-gray-600 hover:bg-gray-100"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
      <div className="px-4 py-4">
        <MoreContent onNavigate={onClose} compact />
      </div>
    </Dialog>
  );
}
