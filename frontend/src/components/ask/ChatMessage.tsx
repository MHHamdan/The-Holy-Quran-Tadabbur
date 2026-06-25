import { useState, useCallback, useEffect } from 'react';
import { User, Bot, Clock, AlertTriangle, CheckCircle, Sparkles, Info, BookOpen, ExternalLink, Copy, Check, Share2, ThumbsUp, ThumbsDown, HelpCircle, ShieldCheck, ShieldAlert, ShieldX, Scale, FileText, GitCompare, BookMarked, Layers, GraduationCap, FlaskConical } from 'lucide-react';
import { getSurahName } from '../../data/surahNames';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { t } from '../../i18n/translations';
import type { RAGAnswerMode } from '../../lib/api';
import { RAGResponse, Citation, feedbackApi } from '../../lib/api';
import { VersesSection } from './VersesSection';
import { TafsirAccordion } from './TafsirAccordion';
import { FollowUpChips } from './FollowUpChips';
import { MissingSourceWarning } from '../common/SourceBadge';
import { DisagreementCard } from './DisagreementCard';

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

  // Status-based routing (Phase 2)
  const status = response?.status ?? (response?.citations?.length ? 'answered' : 'no_verified_source');
  const isNoSource = status === 'no_verified_source';
  const isNeedsClarity = status === 'needs_clarification';

  // Phase K — scientific miracle safety detection
  const isScientificMiracle =
    response?.intent === 'scientific_miracle_claim' ||
    response?.required_labels?.includes('scientific_reflection_needs_review') ||
    response?.required_labels?.includes('needs_scholarly_and_scientific_review') ||
    false;

  // Warnings: split scientific caution out so generic amber box doesn't duplicate it
  const SCIENTIFIC_CAUTION_MARKER = 'specialized scholarly and scientific review';
  const scientificWarnings = response?.warnings?.filter(w => w.includes(SCIENTIFIC_CAUTION_MARKER)) ?? [];
  const otherWarnings = response?.warnings?.filter(w => !w.includes(SCIENTIFIC_CAUTION_MARKER)) ?? [];

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
            {/* Needs clarification notice */}
            {isNeedsClarity && (
              <NeedsClarificationNotice language={language} />
            )}

            {/* Phase K — scientific miracle caution card (always visible, distinct from generic warnings) */}
            {(isScientificMiracle || scientificWarnings.length > 0) && (
              <ScientificCautionCard language={language} />
            )}

            {/* Generic warnings (excluding scientific caution) */}
            {otherWarnings.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 space-y-1">
                {otherWarnings.map((warning, i) => (
                  <p key={i} className="text-amber-800 text-sm flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    {warning}
                  </p>
                ))}
              </div>
            )}

            {/* No Data Notice - Show when retrieval returned nothing (legacy fallback) */}
            {!hasEvidenceData && isLowConfidence && !isNoSource && (
              <NoDataNotice language={language} />
            )}

            {/* Main answer — always show first (safe refusal text when no_verified_source) */}
            <AnswerCard response={response} language={language} />

            {/* Related verses - supporting evidence */}
            {hasVerses && !isNoSource && (
              <VersesSection verses={response.related_verses!} language={language} />
            )}

            {/* Tafsir explanations - accordion */}
            {hasTafsir && !isNoSource && (
              <TafsirAccordion tafsirBySources={response.tafsir_by_source!} language={language} />
            )}

            {/* M4 — Structured disagreement card (agentic endpoint) */}
            {response.agentic?.consensus && response.agentic.consensus.disagreements.length > 0 && (
              <DisagreementCard consensus={response.agentic.consensus} className="mb-2" />
            )}

            {/* Phase E — scholarly disagreement warning (legacy / non-agentic) */}
            {response.disagreement_warning && !response.agentic?.consensus && (
              <DisagreementWarning warning={response.disagreement_warning} language={language} />
            )}

            {/* Citation cards (Phase 2: richer display) */}
            {hasCitations && !isNoSource && (
              <CitationCards citations={response.citations} language={language} />
            )}

            {/* Missing source warning — driven by status */}
            {(isNoSource || (!hasCitations && !isLoading && !error)) && (
              <MissingSourceWarning language={language} />
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

            {/* Related topic chips — expansion terms from the query expander */}
            {isLatest && response.related_queries && response.related_queries.length > 0 && onFollowUp && (
              <div className="space-y-1.5">
                <h4 className="text-xs font-medium text-gray-400 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5" />
                  {language === 'ar' ? 'مواضيع ذات صلة' : 'Related topics'}
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {response.related_queries.slice(0, 6).map((term, idx) => (
                    <button
                      key={idx}
                      onClick={() => onFollowUp(term)}
                      className="inline-flex items-center px-2.5 py-1 text-xs bg-gray-50 border border-gray-200 rounded-full text-gray-600 hover:bg-primary-50 hover:border-primary-200 hover:text-primary-700 transition-colors"
                      dir="auto"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
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

  useEffect(() => {
    const interval = setInterval(() => {
      setStage((s) => (s + 1) % 3);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

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

function NeedsClarificationNotice({ language }: { language: 'ar' | 'en' }) {
  return (
    <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
      <div className="flex items-start gap-3">
        <HelpCircle className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-medium text-indigo-800 mb-1">
            {language === 'ar' ? 'يحتاج إلى توضيح' : 'Needs Clarification'}
          </h4>
          <p className="text-sm text-indigo-700">
            {language === 'ar'
              ? 'يرجى تحديد رقم الآية أو اسم السورة أو الموضوع حتى أتمكن من البحث في المصادر المناسبة.'
              : 'Please specify a verse reference, surah name, or topic so I can find relevant sources.'}
          </p>
        </div>
      </div>
    </div>
  );
}

const RELIABILITY_CONFIG = {
  canonical: { label: 'Canonical', labelAr: 'متواتر', Icon: ShieldCheck, classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  verified: { label: 'Verified', labelAr: 'موثق', Icon: ShieldCheck, classes: 'bg-blue-50 text-blue-700 border-blue-200' },
  supporting: { label: 'Supporting', labelAr: 'مساند', Icon: ShieldAlert, classes: 'bg-amber-50 text-amber-700 border-amber-200' },
  experimental: { label: 'Experimental', labelAr: 'تجريبي', Icon: ShieldX, classes: 'bg-red-50 text-red-700 border-red-200' },
};

function CitationCard({ citation, language }: { citation: Citation; language: 'ar' | 'en' }) {
  const [expanded, setExpanded] = useState(false);
  const level = citation.reliability_level ?? 'verified';
  const cfg = RELIABILITY_CONFIG[level as keyof typeof RELIABILITY_CONFIG] ?? RELIABILITY_CONFIG.verified;
  const Icon = cfg.Icon;

  const sourceName = language === 'ar' ? (citation.source_name_ar || citation.source_name) : citation.source_name;
  const [sura, aya] = citation.verse_reference.split(':');

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden text-sm">
      {/* Card header */}
      <div className="flex items-start gap-2 px-3 py-2.5">
        <span className={clsx('inline-flex items-center gap-1 border rounded-full px-1.5 py-0.5 text-xs font-medium shrink-0 mt-0.5', cfg.classes)}>
          <Icon className="w-3 h-3" />
          {language === 'ar' ? cfg.labelAr : cfg.label}
        </span>
        <div className="flex-1 min-w-0">
          <Link
            to={`/quran/${sura}?aya=${aya}&highlight=true`}
            className="font-semibold text-gray-900 hover:text-primary-600 transition-colors truncate block"
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          >
            {sourceName}
          </Link>
          {citation.author && (
            <span className="text-xs text-gray-500" dir={language === 'ar' ? 'rtl' : 'ltr'}>
              {citation.author}
            </span>
          )}
        </div>
        <Link
          to={`/quran/${sura}?aya=${aya}&highlight=true`}
          className="shrink-0 flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium"
        >
          <span className="font-arabic" dir="rtl">{getSurahName(Number(sura))[language === 'ar' ? 'ar' : 'en']}</span>
          {' '}{citation.verse_reference}
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      {/* Excerpt */}
      {citation.excerpt && (
        <div className="px-3 pb-2">
          <p
            className="text-xs text-gray-600 leading-relaxed line-clamp-2"
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          >
            {citation.excerpt}
          </p>
          {citation.quoted_evidence && citation.quoted_evidence !== citation.excerpt && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-primary-600 hover:underline mt-1"
            >
              {expanded
                ? (language === 'ar' ? 'إخفاء' : 'Show less')
                : (language === 'ar' ? 'عرض المزيد' : 'Show more')}
            </button>
          )}
          {expanded && citation.quoted_evidence && (
            <p
              className="text-xs text-gray-600 leading-relaxed mt-1 border-t border-gray-100 pt-1"
              dir={language === 'ar' ? 'rtl' : 'ltr'}
            >
              {citation.quoted_evidence}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function CitationCards({ citations, language }: { citations: Citation[]; language: 'ar' | 'en' }) {
  if (citations.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-primary-600" />
        {language === 'ar' ? 'المصادر المستخدمة' : 'Sources Used'}
        <span className="text-xs text-gray-400 font-normal">({citations.length})</span>
      </h4>
      <div className="space-y-2">
        {citations.map((c) => (
          <CitationCard key={c.chunk_id} citation={c} language={language} />
        ))}
      </div>
    </div>
  );
}

/** Answer card with copy/share actions */
function AnswerCard({ response, language }: { response: RAGResponse; language: 'ar' | 'en' }) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const [feedbackSent, setFeedbackSent] = useState(false);

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
        <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
          <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary-500 flex-shrink-0" />
          <h4 className="text-xs sm:text-sm font-semibold text-gray-700 truncate">
            {language === 'ar' ? 'الإجابة' : 'Answer'}
          </h4>
          {response.answer_mode && (
            <AnswerModeBadge mode={response.answer_mode} language={language} />
          )}
        </div>
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

        {/* Phase E — AI summary disclaimer (always shown for RAG answers) */}
        {response.ai_summary_disclaimer !== false && (
          <AISummaryDisclaimer language={language} />
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
          <span className="text-xs text-gray-400 me-1 sm:me-2">
            {language === 'ar' ? 'مفيدة؟' : 'Helpful?'}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => {
                const next = feedback === 'up' ? null : 'up';
                setFeedback(next);
                if (next === 'up' && !feedbackSent) {
                  setFeedbackSent(true);
                  feedbackApi.submit({
                    category: 'ui_feedback',
                    message: `[helpful] intent=${response.intent} confidence=${Math.round(response.confidence * 100)}%`,
                    page_url: window.location.pathname,
                  }).catch(() => {/* fire-and-forget */});
                }
              }}
              className={clsx(
                'p-2 min-w-[40px] min-h-[40px] rounded-lg transition-colors flex items-center justify-center',
                feedback === 'up'
                  ? 'bg-green-100 text-green-600'
                  : 'hover:bg-gray-200 text-gray-400 hover:text-gray-600 active:scale-95'
              )}
              aria-label={language === 'ar' ? 'مفيد' : 'Helpful'}
            >
              <ThumbsUp className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                const next = feedback === 'down' ? null : 'down';
                setFeedback(next);
                if (next === 'down' && !feedbackSent) {
                  setFeedbackSent(true);
                  feedbackApi.submit({
                    category: 'ui_feedback',
                    message: `[not helpful] intent=${response.intent} confidence=${Math.round(response.confidence * 100)}%`,
                    page_url: window.location.pathname,
                  }).catch(() => {/* fire-and-forget */});
                }
              }}
              className={clsx(
                'p-2 min-w-[40px] min-h-[40px] rounded-lg transition-colors flex items-center justify-center',
                feedback === 'down'
                  ? 'bg-red-100 text-red-600'
                  : 'hover:bg-gray-200 text-gray-400 hover:text-gray-600 active:scale-95'
              )}
              aria-label={language === 'ar' ? 'غير مفيد' : 'Not helpful'}
            >
              <ThumbsDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Phase E — Tafsir Assistant UI components
// ---------------------------------------------------------------------------

const MODE_CONFIG: Record<string, { Icon: React.ElementType; colorClass: string; }> = {
  simple_explanation:  { Icon: FileText,    colorClass: 'bg-gray-100 text-gray-600' },
  tafsir_summary:      { Icon: BookMarked,  colorClass: 'bg-blue-50 text-blue-600' },
  tafsir_comparison:   { Icon: GitCompare,  colorClass: 'bg-indigo-50 text-indigo-600' },
  vocabulary:          { Icon: BookOpen,    colorClass: 'bg-emerald-50 text-emerald-600' },
  thematic:            { Icon: Layers,      colorClass: 'bg-violet-50 text-violet-600' },
  needs_scholar_review:{ Icon: GraduationCap, colorClass: 'bg-amber-50 text-amber-600' },
};

const MODE_TRANSLATION_KEY: Record<string, string> = {
  simple_explanation:   'rag_mode_simple_explanation',
  tafsir_summary:       'rag_mode_tafsir_summary',
  tafsir_comparison:    'rag_mode_tafsir_comparison',
  vocabulary:           'rag_mode_vocabulary',
  thematic:             'rag_mode_thematic',
  needs_scholar_review: 'rag_mode_needs_scholar_review',
};

function AnswerModeBadge({ mode, language }: { mode: RAGAnswerMode; language: 'ar' | 'en' }) {
  const cfg = MODE_CONFIG[mode] ?? MODE_CONFIG.simple_explanation;
  const Icon = cfg.Icon;
  const label = t(MODE_TRANSLATION_KEY[mode] ?? 'rag_mode_tafsir_summary', language);
  return (
    <span className={clsx('inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-medium flex-shrink-0', cfg.colorClass)}>
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
}

function AISummaryDisclaimer({ language }: { language: 'ar' | 'en' }) {
  return (
    <div
      className="mt-3 pt-3 border-t border-gray-100 flex items-start gap-1.5"
      dir={language === 'ar' ? 'rtl' : 'ltr'}
    >
      <Info className="w-3.5 h-3.5 text-gray-400 flex-shrink-0 mt-0.5" />
      <p className="text-[11px] text-gray-400 leading-relaxed">
        {t('rag_ai_disclaimer', language)}
      </p>
    </div>
  );
}

function DisagreementWarning({ warning, language }: { warning: string; language: 'ar' | 'en' }) {
  // The warning string contains both EN and AR parts separated by " — "
  const parts = warning.split(' — ');
  const displayText = language === 'ar' && parts.length > 1 ? parts[1] : parts[0];
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <div className="flex items-start gap-2">
        <Scale className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-amber-800 mb-0.5">
            {t('rag_disagreement_title', language)}
          </p>
          <p className="text-xs text-amber-700">{displayText}</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Phase K — Scientific Miracle Caution Card
// Always visible, cannot be collapsed. Per platform policy: asserting a
// definitive link between a verse and a modern scientific theory requires
// specialized scholarly and scientific review.
// ---------------------------------------------------------------------------

function ScientificCautionCard({ language }: { language: 'ar' | 'en' }) {
  return (
    <div
      className="bg-orange-50 border-2 border-orange-300 rounded-xl p-4"
      dir={language === 'ar' ? 'rtl' : 'ltr'}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <FlaskConical className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-orange-800 text-sm">
            {t('scientific_caution_title', language)}
          </p>
          <p className="text-orange-700 text-sm mt-1 leading-relaxed">
            {t('scientific_caution_body', language)}
          </p>
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
