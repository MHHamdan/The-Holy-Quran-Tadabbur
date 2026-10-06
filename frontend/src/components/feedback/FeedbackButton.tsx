/**
 * Phase G — Floating Feedback Button
 *
 * Renders a persistent "Report an Issue" button fixed to the bottom-right
 * corner of every page. On click it opens a modal with a category selector
 * and a message field. Submits to POST /api/v1/feedback.
 *
 * The current page URL is attached automatically as `page_url`.
 */
import { useState } from 'react';
import { Flag, X, Send, CheckCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { useLocation } from 'react-router-dom';
import { feedbackApi, FeedbackCategory } from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';

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

  const [open, setOpen] = useState(false);
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
    setOpen(false);
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

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={() => setOpen(true)}
        className={clsx(
          'fixed safe-bottom-offset z-40 flex items-center gap-2 rounded-full px-4 py-2.5',
          'bg-amber-600 hover:bg-amber-700 text-white shadow-lg',
          'text-sm font-medium transition-colors',
          isRtl ? 'left-6' : 'right-6'
        )}
        aria-label={t('feedback_button_label', language)}
      >
        <Flag className="h-4 w-4 shrink-0" />
        <span className="hidden sm:inline">{t('feedback_button_label', language)}</span>
      </button>

      {/* Modal backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-end p-4 sm:items-center sm:justify-center"
          onClick={(e) => e.target === e.currentTarget && close()}
        >
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={close} />

          {/* Dialog */}
          <div
            dir={isRtl ? 'rtl' : 'ltr'}
            className={clsx(
              'relative z-10 w-full max-w-md rounded-2xl bg-white dark:bg-zinc-900',
              'shadow-2xl border border-zinc-200 dark:border-zinc-700 p-6',
              'animate-in slide-in-from-bottom-4 duration-200'
            )}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  {t('feedback_dialog_title', language)}
                </h2>
                <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
                  {t('feedback_dialog_subtitle', language)}
                </p>
              </div>
              <button
                onClick={close}
                className="ms-4 p-1 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {result === 'success' ? (
              <div className="flex flex-col items-center gap-3 py-6 text-center">
                <CheckCircle className="h-12 w-12 text-green-500" />
                <p className="font-medium text-zinc-800 dark:text-zinc-200">
                  {t('feedback_success', language)}
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                    {t('feedback_category_label', language)}
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as FeedbackCategory)}
                    className={clsx(
                      'w-full rounded-lg border border-zinc-200 dark:border-zinc-700',
                      'bg-white dark:bg-zinc-800 px-3 py-2 text-sm',
                      'text-zinc-800 dark:text-zinc-200',
                      'focus:outline-none focus:ring-2 focus:ring-amber-500'
                    )}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {t(c.labelKey, language)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Message */}
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                    {t('feedback_message_label', language)}
                  </label>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    rows={4}
                    placeholder={t('feedback_message_placeholder', language)}
                    className={clsx(
                      'w-full rounded-lg border border-zinc-200 dark:border-zinc-700',
                      'bg-white dark:bg-zinc-800 px-3 py-2 text-sm resize-none',
                      'text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-400',
                      'focus:outline-none focus:ring-2 focus:ring-amber-500'
                    )}
                    required
                    minLength={10}
                  />
                  <p className="mt-1 text-xs text-zinc-400">
                    {message.trim().length}/2000
                  </p>
                </div>

                {result === 'error' && (
                  <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {t('feedback_error', language)}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 pt-1">
                  <button
                    type="button"
                    onClick={close}
                    className={clsx(
                      'flex-1 rounded-lg border border-zinc-200 dark:border-zinc-700 py-2',
                      'text-sm text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800',
                      'transition-colors'
                    )}
                  >
                    {t('feedback_cancel', language)}
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || message.trim().length < 10}
                    className={clsx(
                      'flex-1 flex items-center justify-center gap-2 rounded-lg py-2',
                      'bg-amber-600 hover:bg-amber-700 disabled:opacity-50',
                      'text-sm font-medium text-white transition-colors'
                    )}
                  >
                    <Send className="h-4 w-4" />
                    {submitting ? t('feedback_submitting', language) : t('feedback_submit', language)}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
