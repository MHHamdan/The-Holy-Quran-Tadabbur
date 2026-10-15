/**
 * ErrorPanel Component
 *
 * Standardized error display with:
 * - Request ID for debugging/support
 * - Copy diagnostics button
 * - Bilingual messages (Arabic/English)
 * - Retry functionality
 * - Admin report link
 */
import { useState } from 'react';
import { AlertCircle, Copy, CheckCircle, RefreshCw, MessageSquare } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { translations } from '../../i18n/translations';
import { useFeedbackDialog } from '../feedback/feedbackStore';
import clsx from 'clsx';

/** Request ids that carry no information and are not shown. */
export function hasUsefulRequestId(id: string | undefined | null): boolean {
  return !!id && !['n/a', 'unknown', 'none', ''].includes(id.trim().toLowerCase());
}

export interface APIErrorData {
  code: string;
  message: string;
  message_ar: string;
  request_id: string;
  details?: Array<{
    field?: string;
    message: string;
    message_ar?: string;
  }>;
  data_status?: string;
}

export interface ErrorPanelProps {
  error: APIErrorData | null;
  onRetry?: () => void;
  onReport?: () => void;
  className?: string;
  compact?: boolean;
}

export function ErrorPanel({
  error,
  onRetry,
  onReport,
  className,
  compact = false,
}: ErrorPanelProps) {
  const { language } = useLanguageStore();
  const [copied, setCopied] = useState(false);
  const openFeedback = useFeedbackDialog((st) => st.openDialog);
  const isArabic = language === 'ar';

  if (!error) return null;

  const message = isArabic ? error.message_ar : error.message;

  const copyDiagnostics = async () => {
    const diagnostics = {
      request_id: error.request_id,
      error_code: error.code,
      message: error.message,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      user_agent: navigator.userAgent,
    };

    try {
      await navigator.clipboard.writeText(JSON.stringify(diagnostics, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy diagnostics:', err);
    }
  };

  if (compact) {
    return (
      <div
        className={clsx(
          'flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm',
          className
        )}
        dir={isArabic ? 'rtl' : 'ltr'}
      >
        <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
        <span className="text-red-800 flex-1">{message}</span>
        {hasUsefulRequestId(error.request_id) && (
          <span className="text-red-700 text-xs font-mono" dir="ltr">{error.request_id}</span>
        )}
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="tap hover:bg-red-100 rounded transition-colors"
            aria-label={isArabic ? 'إعادة المحاولة' : 'Retry'}
          >
            <RefreshCw className="w-4 h-4 text-red-700" aria-hidden="true" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'bg-red-50 border border-red-200 rounded-xl p-6',
        className
      )}
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="p-2 bg-red-100 rounded-lg flex-shrink-0">
          <AlertCircle className="w-6 h-6 text-red-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-red-800">
            {isArabic ? 'حدث خطأ' : 'An Error Occurred'}
          </h3>
          <p className="text-red-700 mt-1">{message}</p>

          {/* Error Details */}
          {error.details && error.details.length > 0 && (
            <ul className="mt-3 space-y-1">
              {error.details.map((detail, idx) => (
                <li key={idx} className="text-sm text-red-700">
                  {detail.field && (
                    <span className="font-mono text-red-700" dir="ltr">{detail.field}: </span>
                  )}
                  {isArabic && detail.message_ar ? detail.message_ar : detail.message}
                </li>
              ))}
            </ul>
          )}

          {/* Data Status Warning */}
          {error.data_status === 'incomplete' && (
            <div className="mt-3 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
              {isArabic
                ? 'البيانات غير مكتملة. قد لا تظهر جميع المعلومات.'
                : 'Data is incomplete. Some information may not be displayed.'}
            </div>
          )}
        </div>
      </div>

      {/* Request ID and Actions */}
      <div className="mt-4 pt-4 border-t border-red-200 flex flex-wrap items-center gap-3">
        {/* Request ID (only when the server gave one) */}
        {hasUsefulRequestId(error.request_id) && (
          <div className="flex items-center gap-2 text-sm text-red-700">
            <span className="font-medium">
              {isArabic ? 'معرّف الطلب:' : 'Request ID:'}
            </span>
            <code className="px-2 py-0.5 bg-red-100 rounded font-mono text-xs">
              {error.request_id}
            </code>
          </div>
        )}

        <div className="flex-1" />

        {/* Copy Diagnostics */}
        <button
          onClick={copyDiagnostics}
          type="button"
          className={clsx(
            'flex min-h-11 items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors',
            copied
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700 hover:bg-red-200'
          )}
        >
          {copied ? (
            <>
              <CheckCircle className="w-4 h-4" />
              {isArabic ? 'تم النسخ' : 'Copied'}
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              {isArabic ? translations.err_copy_details.ar : translations.err_copy_details.en}
            </>
          )}
        </button>

        {/* Retry Button */}
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="flex min-h-11 items-center gap-2 px-3 py-1.5 bg-red-700 text-white text-sm rounded-lg hover:bg-red-800 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            {isArabic ? 'إعادة المحاولة' : 'Try Again'}
          </button>
        )}

        {/* Report to Admin */}
        {onReport && (
          <button
            type="button"
            onClick={() => {
              onReport?.();
              openFeedback();
            }}
            className="flex min-h-11 items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-800 text-sm rounded-lg hover:bg-gray-200 transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            {isArabic ? translations.err_report_problem.ar : translations.err_report_problem.en}
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Hook to parse API error responses into ErrorPanel format
 */
export function parseAPIError(error: unknown): APIErrorData | null {
  if (!error) return null;

  // Axios error with response
  if (typeof error === 'object' && error !== null) {
    const axiosError = error as {
      response?: {
        data?: {
          ok?: boolean;
          error?: APIErrorData;
          request_id?: string;
        };
        headers?: Record<string, string>;
      };
      message?: string;
      code?: string;
    };

    if (axiosError.response?.data?.error) {
      return axiosError.response.data.error;
    }

    // Fallback for old-style errors
    if (axiosError.response?.data) {
      const data = axiosError.response.data as Record<string, unknown>;
      // FastAPI 422 puts an array of {loc, msg} objects in `detail`, which
      // React cannot render as a message.
      const detail = typeof data.detail === 'string' ? data.detail : null;
      const details = Array.isArray(data.detail)
        ? (data.detail as Array<{ loc?: unknown[]; msg?: string }>)
            .filter((d) => d && typeof d.msg === 'string')
            .map((d) => ({
              field: Array.isArray(d.loc) ? d.loc.filter((x) => x !== 'body' && x !== 'query').join('.') || undefined : undefined,
              message: d.msg as string,
            }))
        : undefined;
      const unprocessed = translations.err_request_unprocessed;
      return {
        code: (data.error_code as string) || (Array.isArray(data.detail) ? 'validation_error' : 'unknown_error'),
        message: (typeof data.message === 'string' && data.message) || detail || unprocessed.en,
        message_ar: (typeof data.message_ar === 'string' && data.message_ar) || (details ? unprocessed.ar : 'حدث خطأ'),
        request_id:
          (data.request_id as string) ||
          axiosError.response.headers?.['x-request-id'] ||
          'unknown',
        ...(details && details.length ? { details } : {}),
      };
    }

    // No response: network failure or timeout. The transport message
    // ("Network Error", "timeout of 30000ms exceeded") is not shown.
    if (axiosError.message || axiosError.code) {
      const isTimeout = axiosError.code === 'ECONNABORTED' || axiosError.code === 'ETIMEDOUT' || /timeout/i.test(axiosError.message ?? '');
      return {
        code: isTimeout ? 'timeout' : 'network_error',
        message: translations.err_network.en,
        message_ar: translations.err_network.ar,
        request_id: 'N/A',
      };
    }
  }

  // String error
  if (typeof error === 'string') {
    return {
      code: 'unknown_error',
      message: error,
      message_ar: 'خطأ غير معروف',
      request_id: 'N/A',
    };
  }

  return null;
}

/**
 * Data incomplete status component
 */
export function DataIncompleteNotice({
  message,
  messageAr,
  className,
}: {
  message?: string;
  messageAr?: string;
  className?: string;
}) {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const defaultMessage = isArabic
    ? 'البيانات غير مكتملة. بعض المعلومات قد تكون مفقودة.'
    : 'Data is incomplete. Some information may be missing.';

  return (
    <div
      className={clsx(
        'flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg',
        className
      )}
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
      <span className="text-amber-700 text-sm">
        {isArabic ? (messageAr || defaultMessage) : (message || defaultMessage)}
      </span>
    </div>
  );
}
