import { useState, useCallback } from 'react';
import { User, Bot, Clock, AlertTriangle, CheckCircle, Sparkles, Info, BookOpen, ExternalLink, Copy, Check, Share2, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { RAGResponse } from '../../lib/api';
import { VersesSection } from './VersesSection';
import { TafsirAccordion } from './TafsirAccordion';
import { FollowUpChips } from './FollowUpChips';

export interface ChatMessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  // Assistant-specific fields
  response?: RAGResponse;
  isLoading?: boolean;
  error?: string;
}

interface ChatMessageProps {
  message: ChatMessageData;
  language: 'ar' | 'en';
  onFollowUp?: (question: string) => void;
  isLatest?: boolean;
}

export function ChatMessage({ message, language, onFollowUp, isLatest }: ChatMessageProps) {
  if (message.role === 'user') {
    return <UserMessage content={message.content} language={language} />;
  }

  return (
    <AssistantMessage
      message={message}
      language={language}
      onFollowUp={onFollowUp}
      isLatest={isLatest}
    />
  );
}

function UserMessage({ content, language }: { content: string; language: 'ar' | 'en' }) {
  return (
    <div className="flex gap-2 sm:gap-3 justify-end animate-chat-bubble" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <div className="max-w-[85%] sm:max-w-[80%] bg-primary-600 text-white rounded-2xl rounded-tr-sm px-3 sm:px-4 py-2.5 sm:py-3 shadow-sm">
        <p className="text-sm leading-relaxed">{content}</p>
      </div>
      <div className="flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary-100 flex items-center justify-center">
        <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary-600" />
      </div>
    </div>
  );
}

function AssistantMessage({
  message,
  language,
  onFollowUp,
  isLatest
}: {
  message: ChatMessageData;
  language: 'ar' | 'en';
  onFollowUp?: (question: string) => void;
  isLatest?: boolean;
}) {
  const { response, isLoading, error } = message;

  // Check if we have meaningful data
  const hasVerses = response?.related_verses && response.related_verses.length > 0;
  const hasTafsir = response?.tafsir_by_source && Object.keys(response.tafsir_by_source).length > 0;
  const hasCitations = response?.citations && response.citations.length > 0;
  const hasEvidenceData = hasVerses || hasTafsir || hasCitations;
  const isLowConfidence = response && response.confidence < 0.3;

  return (
    <div className="flex gap-2 sm:gap-3 animate-chat-bubble" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <div className="flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-emerald-100 flex items-center justify-center">
        <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" />
      </div>
      <div className="flex-1 max-w-[95%] sm:max-w-[90%] space-y-3 sm:space-y-4">
        {/* Loading state */}
        {isLoading && <LoadingIndicator language={language} />}

        {/* Error state */}
        {error && <ErrorDisplay error={error} language={language} />}

        {/* Response content */}
        {response && (
          <>
            {/* Warnings */}
            {response.warnings && response.warnings.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                {response.warnings.map((warning, i) => (
                  <p key={i} className="text-amber-800 text-sm flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    {warning}
                  </p>
                ))}
              </div>
            )}

            {/* No Data Notice - Show when retrieval returned nothing */}
            {!hasEvidenceData && isLowConfidence && (
              <NoDataNotice language={language} />
            )}

            {/* Related verses - displayed first */}
            {hasVerses && (
              <VersesSection verses={response.related_verses!} language={language} />
            )}

            {/* Tafsir explanations - accordion */}
            {hasTafsir && (
              <TafsirAccordion tafsirBySources={response.tafsir_by_source!} language={language} />
            )}

            {/* Main answer */}
            <AnswerCard response={response} language={language} />

            {/* Citations summary (when we have them) */}
            {hasCitations && (
              <CitationsSummary
                citations={response.citations}
                language={language}
              />
            )}

            {/* Processing info */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {response.processing_time_ms < 1000
                  ? `${response.processing_time_ms}ms`
                  : `${(response.processing_time_ms / 1000).toFixed(1)}s`}
              </span>
              {hasCitations && (
                <span>
                  {response.citations.length} {language === 'ar' ? 'مصدر' : 'citation'}
                  {response.citations.length > 1 && (language === 'ar' ? '' : 's')}
                </span>
              )}
              {response.evidence_density && (
                <span>
                  {response.evidence_density.source_count} {language === 'ar' ? 'تفسير' : 'tafsir'}
                </span>
              )}
            </div>

            {/* Follow-up suggestions - only for latest message */}
            {isLatest && response.follow_up_suggestions && response.follow_up_suggestions.length > 0 && onFollowUp && (
              <FollowUpChips
                suggestions={response.follow_up_suggestions}
                onSelect={onFollowUp}
                language={language}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

/** Enhanced typing indicator with progress stages */
function LoadingIndicator({ language }: { language: 'ar' | 'en' }) {
  const [stage, setStage] = useState(0);

  // Cycle through stages for visual interest
  useState(() => {
    const interval = setInterval(() => {
      setStage((s) => (s + 1) % 3);
    }, 2000);
    return () => clearInterval(interval);
  });

  const stages = language === 'ar'
    ? ['جاري البحث في التفاسير...', 'تحليل الآيات ذات الصلة...', 'إعداد الإجابة...']
    : ['Searching tafsir sources...', 'Analyzing related verses...', 'Preparing response...'];

  return (
    <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-3 sm:p-5 border border-gray-100 shadow-sm">
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Animated typing indicator */}
        <div className="relative w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center flex-shrink-0">
          <div className="absolute inset-0 bg-primary-100 rounded-full animate-ping opacity-20" />
          <div className="relative flex gap-1">
            <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-primary-500 rounded-full typing-dot" />
            <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-primary-500 rounded-full typing-dot" />
            <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-primary-500 rounded-full typing-dot" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <span className="text-xs sm:text-sm font-medium text-gray-700 block truncate">
            {stages[stage]}
          </span>
          {/* Progress bar */}
          <div className="mt-1.5 sm:mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full transition-all duration-1000"
              style={{ width: `${(stage + 1) * 33}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function ErrorDisplay({ error, language }: { error: string; language: 'ar' | 'en' }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-medium text-red-800 mb-1">
            {language === 'ar' ? 'حدث خطأ' : 'An Error Occurred'}
          </h4>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    </div>
  );
}

function NoDataNotice({ language }: { language: 'ar' | 'en' }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
      <div className="flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-medium text-blue-800 mb-1">
            {language === 'ar' ? 'ملاحظة' : 'Note'}
          </h4>
          <p className="text-sm text-blue-700 mb-2">
            {language === 'ar'
              ? 'لم يتم العثور على مصادر تفسير كافية لهذا السؤال. الإجابة المعروضة قد لا تكون مدعومة بالأدلة الكاملة.'
              : 'Insufficient tafsir sources were found for this question. The answer shown may not be fully supported by evidence.'}
          </p>
          <p className="text-xs text-blue-600">
            {language === 'ar'
              ? 'نصيحة: حاول إعادة صياغة السؤال أو اختيار مصادر تفسير مختلفة.'
              : 'Tip: Try rephrasing your question or selecting different tafsir sources.'}
          </p>
        </div>
      </div>
    </div>
  );
}

function CitationsSummary({ citations, language }: { citations: RAGResponse['citations']; language: 'ar' | 'en' }) {
  // Group citations by source
  const sourceMap = new Map<string, typeof citations>();
  citations.forEach(c => {
    const existing = sourceMap.get(c.source_name) || [];
    existing.push(c);
    sourceMap.set(c.source_name, existing);
  });

  const sources = Array.from(sourceMap.entries());

  if (sources.length === 0) return null;

  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
      <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-primary-600" />
        {language === 'ar' ? 'المصادر المستخدمة' : 'Sources Used'}
      </h4>
      <div className="flex flex-wrap gap-2">
        {sources.map(([sourceName, sourceCitations]) => {
          const firstCitation = sourceCitations[0];
          const verseRef = firstCitation.verse_reference;
          const [sura, aya] = verseRef.split(':');

          return (
            <Link
              key={sourceName}
              to={`/quran/${sura}?aya=${aya}&highlight=true`}
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors text-sm"
            >
              <span className="font-medium text-gray-900">
                {language === 'ar' ? firstCitation.source_name_ar || sourceName : sourceName}
              </span>
              <span className="text-primary-600 text-xs">
                ({sourceCitations.length})
              </span>
              <ExternalLink className="w-3 h-3 text-gray-400" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}

/** Answer card with copy/share actions */
function AnswerCard({ response, language }: { response: RAGResponse; language: 'ar' | 'en' }) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(response.answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [response.answer]);

  const handleShare = useCallback(async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: language === 'ar' ? 'إجابة من تدبُّر' : 'Answer from Tadabbur',
          text: response.answer,
        });
      } catch (err) {
        // User cancelled or share failed
        console.error('Share failed:', err);
      }
    }
  }, [response.answer, language]);

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-3 sm:px-4 py-2.5 sm:py-3 bg-gradient-to-r from-primary-50 to-blue-50 border-b border-gray-100 flex items-center justify-between gap-2">
        <h4 className="text-xs sm:text-sm font-semibold text-gray-700 flex items-center gap-1.5 sm:gap-2">
          <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary-500" />
          {language === 'ar' ? 'ملخص الإجابة' : 'Answer Summary'}
        </h4>
        <ConfidenceBadge confidence={response.confidence} language={language} />
      </div>

      {/* Content */}
      <div className="p-3 sm:p-4">
        <div
          className="prose prose-sm max-w-none text-gray-700 leading-relaxed text-sm"
          dir={language === 'ar' ? 'rtl' : 'ltr'}
        >
          {response.answer.split('\n').map((para, i) => (
            para.trim() && <p key={i} className="mb-2 last:mb-0">{para}</p>
          ))}
        </div>

        {response.scholarly_consensus && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <span className="inline-flex items-center gap-1.5 text-xs text-green-700 bg-green-50 px-2 py-1 rounded-lg">
              <CheckCircle className="w-3.5 h-3.5" />
              {response.scholarly_consensus}
            </span>
          </div>
        )}
      </div>

      {/* Actions Footer */}
      <div className="px-3 sm:px-4 py-2.5 sm:py-3 bg-gray-50 border-t border-gray-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className={clsx(
              'inline-flex items-center gap-1.5 px-3 py-2 min-h-[40px] text-xs font-medium rounded-lg transition-all duration-200',
              copied
                ? 'bg-green-100 text-green-700'
                : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-100 hover:text-gray-900 active:scale-95'
            )}
          >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            {copied
              ? (language === 'ar' ? 'تم النسخ!' : 'Copied!')
              : (language === 'ar' ? 'نسخ' : 'Copy')}
          </button>
          {typeof navigator.share === 'function' && (
            <button
              onClick={handleShare}
              className="inline-flex items-center gap-1.5 px-3 py-2 min-h-[40px] text-xs font-medium bg-white border border-gray-200 text-gray-600 hover:bg-gray-100 hover:text-gray-900 active:scale-95 rounded-lg transition-all duration-200"
            >
              <Share2 className="w-3.5 h-3.5" />
              {language === 'ar' ? 'مشاركة' : 'Share'}
            </button>
          )}
        </div>

        {/* Feedback buttons */}
        <div className="flex items-center gap-1 w-full sm:w-auto justify-between sm:justify-end">
          <span className="text-xs text-gray-400 mr-1 sm:mr-2">
            {language === 'ar' ? 'مفيدة؟' : 'Helpful?'}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
              className={clsx(
                'p-2 min-w-[40px] min-h-[40px] rounded-lg transition-colors flex items-center justify-center',
                feedback === 'up'
                  ? 'bg-green-100 text-green-600'
                  : 'hover:bg-gray-200 text-gray-400 hover:text-gray-600 active:scale-95'
              )}
              aria-label="Helpful"
            >
              <ThumbsUp className="w-4 h-4" />
            </button>
            <button
              onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
              className={clsx(
                'p-2 min-w-[40px] min-h-[40px] rounded-lg transition-colors flex items-center justify-center',
                feedback === 'down'
                  ? 'bg-red-100 text-red-600'
                  : 'hover:bg-gray-200 text-gray-400 hover:text-gray-600 active:scale-95'
              )}
              aria-label="Not helpful"
            >
              <ThumbsDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ConfidenceBadge({ confidence, language }: { confidence: number; language: 'ar' | 'en' }) {
  const percent = Math.round(confidence * 100);
  const colorScheme = confidence >= 0.7
    ? 'bg-green-100 text-green-700 border-green-200'
    : confidence >= 0.4
    ? 'bg-yellow-100 text-yellow-700 border-yellow-200'
    : 'bg-red-100 text-red-700 border-red-200';

  const label = confidence >= 0.7
    ? (language === 'ar' ? 'ممتاز' : 'High')
    : confidence >= 0.4
    ? (language === 'ar' ? 'متوسط' : 'Medium')
    : (language === 'ar' ? 'منخفض' : 'Low');

  return (
    <span className={clsx('text-[10px] sm:text-xs font-medium px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg border whitespace-nowrap', colorScheme)}>
      {percent}% <span className="hidden xs:inline">{language === 'ar' ? 'ثقة' : 'confidence'}</span> ({label})
    </span>
  );
}
