/**
 * Phase G — Feedback ("Report a problem")
 *
 * A floating button opens a dialog with a category selector and a message
 * field, submitted to POST /api/v1/feedback with the current page URL.
 *
 * The floating button is hidden on reading and chat surfaces (/mushaf,
 * /quran/*, /tasmee, /ask), where it covered Quran text and the composer;
 * there the same dialog opens from "Report a problem" in the More sheet.
 * On phones it sits above the bottom tab bar.
 */
import { useId, useState } from 'react';
import { Flag, X, Send, CheckCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { useLocation } from 'react-router-dom';
import { feedbackApi, FeedbackCategory } from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { Dialog } from '../ui/Dialog';
import { isReaderRoute } from '../layout/navConfig';
import { useFeedbackDialog } from './feedbackStore';

const CATEGORIES: { value: FeedbackCategory; labelKey: string }[] = [
  { value: 'translation_issue', labelKey: 'feedback_cat_translation_issue' },
  { value: 'source_missing', labelKey: 'feedback_cat_source_missing' },
  { value: 'tafsir_error', labelKey: 'feedback_cat_tafsir_error' },
  { value: 'quran_ref_error', labelKey: 'feedback_cat_quran_ref_error' },
  { value: 'ui_feedback', labelKey: 'feedback_cat_ui_feedback' },
  { value: 'inappropriate', labelKey: 'feedback_cat_inappropriate' },
  { value: 'other', labelKey: 'feedback_cat_other' },
];

export function FeedbackButton() {
  const { language } = useLanguageStore();
  const location = useLocation();
  const isRtl = language === 'ar';
  const { open, openDialog, closeDialog } = useFeedbackDialog();
  const ids = useId();
  const titleId = `${ids}-title`;
  const categoryId = `${ids}-category`;
  const messageId = `${ids}-message`;

  const [category, setCategory] = useState<FeedbackCategory>('other');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<'success' | 'error' | null>(null);

  function reset() {
    setCategory('other');
    setMessage('');
    setResult(null);
    setSubmitting(false);
  }

  function close() {
    closeDialog();
    setTimeout(reset, 300);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (message.trim().length < 10) return;
    setSubmitting(true);
    try {
      await feedbackApi.submit({
        category,
        message: message.trim(),
        page_url: location.pathname + location.search,
      });
      setResult('success');
      setTimeout(close, 2200);
    } catch {
      setResult('error');
    } finally {
      setSubmitting(false);
    }
  }

  const showFab = !isReaderRoute(location.pathname);

  return (
    <>
      {showFab && (
        <button
          type="button"
          onClick={openDialog}
          className={clsx(
            'fixed fab-offset z-40 flex min-h-11 min-w-11 items-center justify-center gap-2 rounded-full px-3 sm:px-4',
            'bg-amber-700 hover:bg-amber-800 text-white shadow-lg',
            'text-sm font-medium transition-colors',
            'end-4 sm:end-6',
          )}
          aria-label={t('feedback_button_label', language)}
        >
          <Flag className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span className="hidden sm:inline">{t('feedback_button_label', language)}</span>
        </button>
      )}

      <Dialog open={open} onClose={close} labelledBy={titleId} dir={isRtl ? 'rtl' : 'ltr'} className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 id={titleId} className={clsx('text-lg font-semibold text-zinc-900', isRtl && 'font-arabic')}>
              {t('feedback_dialog_title', language)}
            </h2>
            <p className={clsx('mt-0.5 text-sm text-zinc-600', isRtl && 'font-arabic')}>
              {t('feedback_dialog_subtitle', language)}
            </p>
          </div>
          <button
            type="button"
            onClick={close}
            aria-label={t('close', language)}
            className="tap ms-4 rounded-lg hover:bg-zinc-100 text-zinc-500"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {result === 'success' ? (
          <div role="status" className="flex flex-col items-center gap-3 py-6 text-center">
            <CheckCircle className="h-12 w-12 text-green-600" aria-hidden="true" />
            <p className="font-medium text-zinc-800">{t('feedback_success', language)}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor={categoryId} className="block text-sm font-medium text-zinc-700 mb-1.5">
                {t('feedback_category_label', language)}
              </label>
              <select
                id={categoryId}
                value={category}
                onChange={(e) => setCategory(e.target.value as FeedbackCategory)}
                className="w-full min-h-11 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {t(c.labelKey, language)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor={messageId} className="block text-sm font-medium text-zinc-700 mb-1.5">
                {t('feedback_message_label', language)}
              </label>
              <textarea
                id={messageId}
                data-autofocus
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={4}
                placeholder={t('feedback_message_placeholder', language)}
                aria-describedby={`${messageId}-count`}
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm resize-none text-zinc-800 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
                required
                minLength={10}
                maxLength={2000}
              />
              <p id={`${messageId}-count`} className="mt-1 text-xs text-zinc-600">
                <bdi dir="ltr">{message.trim().length}/2000</bdi>
              </p>
            </div>

            {result === 'error' && (
              <div role="alert" className="flex items-center gap-2 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                {t('feedback_error', language)}
              </div>
            )}

            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={close}
                className="flex-1 min-h-11 rounded-lg border border-zinc-300 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors"
              >
                {t('feedback_cancel', language)}
              </button>
              <button
                type="submit"
                disabled={submitting || message.trim().length < 10}
                className="flex-1 min-h-11 flex items-center justify-center gap-2 rounded-lg py-2 bg-amber-700 hover:bg-amber-800 disabled:opacity-50 text-sm font-medium text-white transition-colors"
              >
                <Send className="h-4 w-4" aria-hidden="true" />
                {submitting ? t('feedback_submitting', language) : t('feedback_submit', language)}
              </button>
            </div>
          </form>
        )}
      </Dialog>
    </>
  );
}
