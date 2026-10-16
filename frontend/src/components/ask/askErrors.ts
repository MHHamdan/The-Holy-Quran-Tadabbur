/**
 * Classify a failed /rag/ask request so the chat shows the specific, bilingual
 * reason (AI service down, quota, rate limit, offline) instead of a generic
 * "An error occurred".
 *
 * The API's AI failures use one envelope (backend/app/core/ai_errors.py):
 *   503 {error: {code: "service_unavailable"}}  or  429 {error: {code: "ai_quota_exceeded"}}
 * A gateway in front of the API may answer 502/504 with no JSON body at all,
 * and a dropped connection has no response.
 */

export type AskErrorKind = 'ai_unavailable' | 'ai_quota' | 'rate_limited' | 'network' | 'generic';

interface ErrorLike {
  code?: unknown;
  request?: unknown;
  response?: {
    status?: number;
    data?: unknown;
  };
}

function bodyCode(data: unknown): string | undefined {
  if (!data || typeof data !== 'object') return undefined;
  const d = data as { error?: unknown; error_code?: unknown; code?: unknown };
  if (d.error && typeof d.error === 'object') {
    const code = (d.error as { code?: unknown }).code;
    if (typeof code === 'string') return code;
  }
  if (typeof d.error_code === 'string') return d.error_code;
  if (typeof d.code === 'string') return d.code;
  return undefined;
}

/** Kind of failure for a structured `{ok: false, ...}` body (HTTP 200 or error status). */
export function classifyAskErrorBody(data: unknown, status?: number): AskErrorKind {
  const code = bodyCode(data);
  if (code === 'ai_quota_exceeded') return 'ai_quota';
  if (code === 'service_unavailable' || code === 'ai_unavailable') return 'ai_unavailable';
  if (code === 'rate_limited' || code === 'rate_limit_exceeded' || status === 429) return 'rate_limited';
  if (status === 502 || status === 503 || status === 504) return 'ai_unavailable';
  return 'generic';
}

/** Kind of failure for a thrown request error (axios or fetch-like). */
export function classifyAskError(err: unknown): AskErrorKind {
  if (!err || typeof err !== 'object') return 'generic';
  const e = err as ErrorLike;
  if (e.response) return classifyAskErrorBody(e.response.data, e.response.status);
  // A request that went out but got no response: offline, DNS, CORS, abort.
  if (e.code === 'ERR_NETWORK' || e.code === 'ECONNABORTED' || e.request) return 'network';
  return 'generic';
}

export interface AskErrorCopy {
  title: string;
  body: string;
}

/** Fixed bilingual copy for each specific failure; null for a generic error. */
export function askErrorCopy(kind: AskErrorKind, language: 'ar' | 'en'): AskErrorCopy | null {
  const ar = language === 'ar';
  switch (kind) {
    case 'ai_unavailable':
      return ar
        ? {
            title: 'خدمة الذكاء الاصطناعي غير متاحة مؤقتاً',
            body: 'تعذّرت الإجابة عن سؤالك الآن. ما زال بإمكانك قراءة تفسير أي آية في المصحف أو في صفحة مقارنة التفاسير. حاول مرة أخرى لاحقاً.',
          }
        : {
            title: 'The AI service is temporarily unavailable',
            body: 'Your question could not be answered right now. You can still read the tafsir of any verse in the reader or on the Compare Tafsir page. Please try again later.',
          };
    case 'ai_quota':
      return ar
        ? {
            title: 'بلغت خدمة الذكاء الاصطناعي حدّ الاستخدام',
            body: 'بلغت الخدمة حدّ الاستخدام مؤقتاً. حاول مرة أخرى لاحقاً.',
          }
        : {
            title: 'The AI service has reached its usage limit',
            body: 'The service has reached its usage limit for now. Please try again later.',
          };
    case 'rate_limited':
      return ar
        ? {
            title: 'أسئلة كثيرة في وقت قصير',
            body: 'انتظر دقيقة ثم أعد إرسال سؤالك.',
          }
        : {
            title: 'Too many questions in a short time',
            body: 'Please wait a minute, then send your question again.',
          };
    case 'network':
      return ar
        ? {
            title: 'تعذّر الاتصال بالخادم',
            body: 'تحقّق من اتصالك بالإنترنت ثم حاول مرة أخرى.',
          }
        : {
            title: 'Could not reach the server',
            body: 'Check your internet connection and try again.',
          };
    default:
      return null;
  }
}
