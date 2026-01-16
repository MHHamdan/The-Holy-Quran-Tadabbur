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
import clsx from 'clsx';

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
        <span className="text-red-700 flex-1">{message}</span>
        <span className="text-red-400 text-xs font-mono">{error.request_id}</span>
        {onRetry && (
          <button
            onClick={onRetry}
            className="p-1 hover:bg-red-100 rounded transition-colors"
            title={isArabic ? 'إعادة المحاولة' : 'Retry'}
          >
            <RefreshCw className="w-4 h-4 text-red-600" />
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
                <li key={idx} className="text-sm text-red-600">
                  {detail.field && (
                    <span className="font-mono text-red-500">{detail.field}: </span>
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
        {/* Request ID */}
        <div className="flex items-center gap-2 text-sm text-red-500">
          <span className="font-medium">
            {isArabic ? 'معرف الطلب:' : 'Request ID:'}
          </span>
          <code className="px-2 py-0.5 bg-red-100 rounded font-mono text-xs">
            {error.request_id}
          </code>
        </div>

        <div className="flex-1" />

        {/* Copy Diagnostics */}
        <button
          onClick={copyDiagnostics}
          className={clsx(
            'flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors',
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
              {isArabic ? 'نسخ التشخيص' : 'Copy Diagnostics'}
            </>
          )}
        </button>

        {/* Retry Button */}
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            {isArabic ? 'إعادة المحاولة' : 'Try Again'}
          </button>
        )}

        {/* Report to Admin */}
        {onReport && (
          <button
            onClick={onReport}
            className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            {isArabic ? 'إبلاغ المشرف' : 'Report to Admin'}
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
    };

    if (axiosError.response?.data?.error) {
      return axiosError.response.data.error;
    }

    // Fallback for old-style errors
    if (axiosError.response?.data) {
      const data = axiosError.response.data as Record<string, unknown>;
      return {
        code: (data.error_code as string) || 'unknown_error',
        message: (data.message as string) || (data.detail as string) || 'An error occurred',
        message_ar: (data.message_ar as string) || 'حدث خطأ',
        request_id:
          (data.request_id as string) ||
          axiosError.response.headers?.['x-request-id'] ||
          'unknown',
      };
    }

    // Network error
    if (axiosError.message) {
      return {
        code: 'network_error',
        message: axiosError.message,
        message_ar: 'خطأ في الاتصال بالخادم',
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
