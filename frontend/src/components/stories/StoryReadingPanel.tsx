import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen, Star, Trophy, RotateCcw, CheckCircle, XCircle,
  ChevronRight, Lightbulb, Network, AlertTriangle, Clock, ExternalLink, Book,
} from 'lucide-react';
import clsx from 'clsx';
import type {
  QuranStory, StorySegment, AudienceLevel, SegmentSectionType,
} from '../../types/quranStory';
import { SECTION_TYPE_META, getSegmentSummary, getSegmentLessons, isSegmentSafeToDisplay } from '../../types/quranStory';
import {
  getReviewStatus, getApprovalMetadata, mergeBaseStatusWithOverlay,
} from '../../utils/reviewStatus';

// ---------------------------------------------------------------------------
// Story Overview Card
// ---------------------------------------------------------------------------

export function StoryOverviewCard({
  story, level, language,
}: {
  story: QuranStory;
  level: AudienceLevel;
  language: 'ar' | 'en';
}) {
  if (!story.overview) return null;
  const { overview } = story;
  const intro = level === 'kids'
    ? (language === 'ar' ? overview.introKidsArabic : overview.introKidsEnglish)
    : (language === 'ar' ? overview.introAdultsArabic : overview.introAdultsEnglish);
  const theme = language === 'ar' ? overview.coreThemeArabic : overview.coreThemeEnglish;

  return (
    <div className={clsx(
      'rounded-xl border-2 p-5 mb-6',
      level === 'kids' ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'
    )}>
      <div className="flex items-center gap-2 mb-3">
        <BookOpen className={`w-5 h-5 ${level === 'kids' ? 'text-amber-600' : 'text-blue-600'}`} />
        <h3 className={`font-semibold text-sm uppercase tracking-wide ${level === 'kids' ? 'text-amber-700' : 'text-blue-700'}${language === 'ar' ? ' font-arabic' : ''}`}>
          {language === 'ar' ? 'نظرة عامة على القصة' : 'Story Overview'}
        </h3>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${level === 'kids' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
          {theme}
        </span>
      </div>
      <p className={`text-gray-800 leading-relaxed${language === 'ar' ? ' font-arabic' : ''}`} dir={language === 'ar' ? 'rtl' : 'ltr'}>
        {intro}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Story Summary Card
// ---------------------------------------------------------------------------

export function StorySummaryCard({
  story, level, language,
}: {
  story: QuranStory;
  level: AudienceLevel;
  language: 'ar' | 'en';
}) {
  if (!story.overview) return null;
  const { overview } = story;
  const summary = level === 'kids'
    ? (language === 'ar' ? overview.summaryKidsArabic : overview.summaryKidsEnglish)
    : (language === 'ar' ? overview.summaryAdultsArabic : overview.summaryAdultsEnglish);

  return (
    <div className={clsx(
      'rounded-xl border-2 p-5 mt-6',
      level === 'kids' ? 'bg-emerald-50 border-emerald-200' : 'bg-primary-50 border-primary-200'
    )}>
      <div className="flex items-center gap-2 mb-3">
        <Star className={`w-5 h-5 ${level === 'kids' ? 'text-emerald-600' : 'text-primary-600'}`} />
        <h3 className={`font-semibold text-sm uppercase tracking-wide ${level === 'kids' ? 'text-emerald-700' : 'text-primary-700'}${language === 'ar' ? ' font-arabic' : ''}`}>
          {language === 'ar' ? 'خلاصة القصة' : 'Story Summary'}
        </h3>
      </div>
      <p className={`text-gray-800 leading-relaxed${language === 'ar' ? ' font-arabic' : ''}`} dir={language === 'ar' ? 'rtl' : 'ltr'}>
        {summary}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section Header — groups segments by type
// ---------------------------------------------------------------------------

function SectionHeader({
  sectionType, language,
}: {
  sectionType: SegmentSectionType;
  language: 'ar' | 'en';
}) {
  const meta = SECTION_TYPE_META[sectionType];
  return (
    <div className={`flex items-center gap-3 py-2 px-4 rounded-lg border ${meta.bgClass} mb-3 mt-5`}>
      <div className={`w-2 h-2 rounded-full ${meta.colorClass.replace('text-', 'bg-')}`} />
      <span className={`text-sm font-semibold uppercase tracking-wide ${meta.colorClass}`}>
        {language === 'ar' ? meta.labelAr : meta.labelEn}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Segment Card — single story segment
// ---------------------------------------------------------------------------

function SegmentCard({
  segment, level, language,
}: {
  segment: StorySegment;
  level: AudienceLevel;
  language: 'ar' | 'en';
}) {
  const baseStatus = segment.sunniReview.status;
  // Safety gate: status === 'rejected' segments never render
  const isRejected = baseStatus === 'rejected';
  const needsReview = baseStatus === 'needs_review';
  const humanReviewReq = segment.sunniReview.humanReviewRequired;
  const missingEvidence = (needsReview || humanReviewReq) && segment.sunniReview.matchedEvidence.length === 0;

  if (isRejected) return null;

  const summary = getSegmentSummary(segment, level, language);
  const lessons = getSegmentLessons(segment, language);
  const ref = `${segment.surahNumber}:${segment.ayahStart}${segment.ayahEnd !== segment.ayahStart ? `–${segment.ayahEnd}` : ''}`;

  const overlayStatus = getReviewStatus('story_segment', segment.segmentId);
  const effectiveStatus = mergeBaseStatusWithOverlay(baseStatus, overlayStatus);
  const isApproved = effectiveStatus === 'approved';
  const isPartiallyReviewed = effectiveStatus === 'partially_reviewed';
  const approvalMeta = isApproved ? getApprovalMetadata('story_segment', segment.segmentId) : null;

  return (
    <div className={clsx(
      'card border-l-4',
      isApproved ? 'border-l-green-500' :
      isPartiallyReviewed ? 'border-l-blue-400' :
      (needsReview || humanReviewReq) ? 'border-l-yellow-400' : 'border-l-primary-500'
    )}>
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="w-7 h-7 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
          {segment.sequenceOrder}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-gray-900">
              {language === 'ar' ? segment.titleArabic : segment.titleEnglish}
            </h3>
            <Link
              to={`/quran/${segment.surahNumber}?aya=${segment.ayahStart}`}
              className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full hover:bg-primary-100 transition-colors"
            >
              {ref}
            </Link>
            {isApproved && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200">
                <CheckCircle className="w-3 h-3" />
                {language === 'ar' ? 'معتمد' : 'Approved'}
              </span>
            )}
            {isPartiallyReviewed && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
                <Clock className="w-3 h-3" />
                {language === 'ar' ? 'مراجعة جزئية' : 'Partially Reviewed'}
              </span>
            )}
          </div>
          {approvalMeta && (
            <div className="flex items-center gap-3 text-xs text-green-700 mt-1">
              <span dir={language === 'ar' ? 'rtl' : 'ltr'}>
                {language === 'ar' ? 'راجعه:' : 'Reviewed by:'}{' '}
                <span className="font-medium">{approvalMeta.reviewerName}</span>
              </span>
              <span>{new Date(approvalMeta.reviewedAt).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
            </div>
          )}
        </div>
      </div>

      {/* Review warning */}
      {(needsReview || humanReviewReq) && !isApproved && (
        <div
          role="alert"
          aria-label={language === 'ar' ? 'تحذير: مراجعة معلقة' : 'Warning: Pending Review'}
          className="flex items-start gap-2 p-3 bg-yellow-50 rounded-lg border-2 border-yellow-300 mb-3"
        >
          <AlertTriangle className="w-4 h-4 text-yellow-700 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-bold text-yellow-900 mb-0.5">
              {language === 'ar' ? 'بانتظار المراجعة العلمية' : 'Pending Scholarly Review'}
            </p>
            <p className="text-xs text-yellow-800">
              {language === 'ar'
                ? 'هذا الشرح لم يُراجَع علمياً بعد ولا يُعدّ محتوىً معتمداً.'
                : 'This explanation has not been scholarly reviewed and is not approved content.'}
            </p>
            {humanReviewReq && (
              <p className="text-xs text-yellow-700 mt-1 font-medium">
                {language === 'ar' ? '⚠ مطلوب مراجعة بشرية قبل النشر' : '⚠ Human review required before publishing'}
              </p>
            )}
          </div>
        </div>
      )}

      {missingEvidence && (
        <div className="flex items-center gap-2 p-2 bg-orange-50 rounded border border-orange-200 mb-3">
          <AlertTriangle className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
          <p className="text-xs text-orange-700">
            {language === 'ar' ? 'لم تُربط الأدلة المصدرية بعد.' : 'Source evidence not yet linked.'}
          </p>
        </div>
      )}

      {/* Summary */}
      <p
        className={clsx(
          'text-gray-700 leading-relaxed mb-3',
          level === 'kids' ? 'text-base' : 'text-sm'
        )}
        dir={language === 'ar' ? 'rtl' : 'ltr'}
      >
        {summary}
      </p>

      {/* Lessons */}
      {lessons.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            {language === 'ar' ? 'الدروس المستفادة' : 'Lessons'}
          </p>
          <ul className="space-y-1">
            {lessons.map((lesson, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <CheckCircle className="w-4 h-4 text-primary-500 flex-shrink-0 mt-0.5" />
                <span dir={language === 'ar' ? 'rtl' : 'ltr'}>{lesson}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Source attribution */}
      {segment.sourceIds.length > 0 ? (
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2 flex-wrap">
          <Book className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs text-gray-500">
            {language === 'ar' ? 'المصادر: ' : 'Sources: '}
            {segment.sourceIds.join(', ')}
          </span>
          {segment.sunniReview.disagreementNotes.length > 0 && (
            <span className="text-xs text-orange-600 ml-2">
              ⚠ {language === 'ar' ? 'خلاف علمي' : 'Scholarly disagreement noted'}
            </span>
          )}
        </div>
      ) : (
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-orange-400 flex-shrink-0" />
          <span className="text-xs text-orange-600">
            {language === 'ar' ? 'لم تُحدَّد مصادر لهذا المقطع بعد' : 'No sources identified for this segment yet'}
          </span>
        </div>
      )}

      <div className="mt-2">
        <Link
          to={`/quran/${segment.surahNumber}?aya=${segment.ayahStart}`}
          className="inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-800 transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          {language === 'ar' ? 'عرض في المصحف' : 'View in Quran'}
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Kids Quiz Widget
// ---------------------------------------------------------------------------

type QuizState = 'idle' | 'answered' | 'complete';

export function KidsQuizWidget({
  story, language,
}: {
  story: QuranStory;
  language: 'ar' | 'en';
}) {
  const [currentQ, setCurrentQ] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [quizState, setQuizState] = useState<QuizState>('idle');

  if (!story.kidsQuiz || story.kidsQuiz.length === 0) return null;
  const quiz = story.kidsQuiz;
  const question = quiz[currentQ];
  const options = language === 'ar' ? question.optionsArabic : question.optionsEnglish;
  const isAnswered = selectedAnswer !== null;
  const isCorrect = selectedAnswer === question.correctOptionIndex;

  function handleAnswer(idx: number) {
    if (isAnswered) return;
    setSelectedAnswer(idx);
    setQuizState('answered');
  }

  function handleNext() {
    const newAnswers = [...answers, selectedAnswer];
    setAnswers(newAnswers);
    if (currentQ + 1 < quiz.length) {
      setCurrentQ(currentQ + 1);
      setSelectedAnswer(null);
      setQuizState('idle');
    } else {
      setQuizState('complete');
    }
  }

  function handleReset() {
    setCurrentQ(0);
    setSelectedAnswer(null);
    setAnswers([]);
    setQuizState('idle');
  }

  if (quizState === 'complete') {
    const finalScore = [...answers, selectedAnswer].filter((a, i) => a === quiz[i]?.correctOptionIndex).length;
    const total = quiz.length;
    return (
      <div className="card bg-amber-50 border border-amber-200 text-center">
        <Trophy className="w-12 h-12 text-amber-500 mx-auto mb-3" />
        <h3 className="text-xl font-bold text-amber-800 mb-2">
          {language === 'ar' ? 'أحسنت!' : 'Well done!'}
        </h3>
        <p className="text-amber-700 mb-4">
          {language === 'ar'
            ? `حصلت على ${finalScore} من ${total}`
            : `You scored ${finalScore} out of ${total}`}
        </p>
        <div className="flex justify-center gap-2 mb-4">
          {quiz.map((_, i) => {
            const ans = i < quiz.length - 1 ? answers[i] : selectedAnswer;
            return (
              <div
                key={i}
                className={`w-8 h-8 rounded-full flex items-center justify-center ${ans === quiz[i].correctOptionIndex ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}
              >
                {ans === quiz[i].correctOptionIndex
                  ? <CheckCircle className="w-4 h-4" />
                  : <XCircle className="w-4 h-4" />}
              </div>
            );
          })}
        </div>
        <button
          onClick={handleReset}
          className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium"
        >
          <RotateCcw className="w-4 h-4" />
          {language === 'ar' ? 'أعد المحاولة' : 'Try Again'}
        </button>
      </div>
    );
  }

  return (
    <div className="card border border-amber-200 bg-amber-50/50">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Star className="w-5 h-5 text-amber-500" />
          <h3 className="font-semibold text-amber-800">
            {language === 'ar' ? 'اختبر نفسك!' : 'Quiz Time!'}
          </h3>
        </div>
        <span className="text-xs text-amber-600 font-medium">
          {currentQ + 1} / {quiz.length}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-amber-100 rounded-full h-1.5 mb-4">
        <div
          className="bg-amber-500 h-1.5 rounded-full transition-all"
          style={{ width: `${((currentQ) / quiz.length) * 100}%` }}
        />
      </div>

      <p
        className="text-gray-800 font-medium mb-4 text-base"
        dir={language === 'ar' ? 'rtl' : 'ltr'}
      >
        {language === 'ar' ? question.questionArabic : question.questionEnglish}
      </p>

      <div className="space-y-2 mb-4">
        {options.map((option, idx) => (
          <button
            key={idx}
            onClick={() => handleAnswer(idx)}
            disabled={isAnswered}
            className={clsx(
              'w-full text-start px-4 py-3 rounded-lg border-2 text-sm font-medium transition-all',
              !isAnswered && 'hover:bg-amber-100 border-amber-200 bg-white text-gray-700',
              isAnswered && idx === question.correctOptionIndex && 'border-green-400 bg-green-50 text-green-800',
              isAnswered && idx === selectedAnswer && idx !== question.correctOptionIndex && 'border-red-300 bg-red-50 text-red-700',
              isAnswered && idx !== selectedAnswer && idx !== question.correctOptionIndex && 'border-gray-200 bg-gray-50 text-gray-500 opacity-60',
            )}
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          >
            <span className="flex items-center gap-2">
              {isAnswered && idx === question.correctOptionIndex && <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />}
              {isAnswered && idx === selectedAnswer && idx !== question.correctOptionIndex && <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />}
              {option}
            </span>
          </button>
        ))}
      </div>

      {/* Explanation after answering */}
      {isAnswered && (
        <div className={clsx(
          'p-3 rounded-lg border text-sm mb-4',
          isCorrect ? 'bg-green-50 border-green-200 text-green-800' : 'bg-orange-50 border-orange-200 text-orange-800'
        )}>
          <p className="font-medium mb-1">
            {isCorrect
              ? (language === 'ar' ? '✓ أحسنت!' : '✓ Correct!')
              : (language === 'ar' ? '✗ الجواب الصحيح:' : '✗ The correct answer:')
            }
          </p>
          <p dir={language === 'ar' ? 'rtl' : 'ltr'}>
            {language === 'ar' ? question.explanationArabic : question.explanationEnglish}
          </p>
        </div>
      )}

      {isAnswered && (
        <button
          onClick={handleNext}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium"
        >
          {currentQ + 1 < quiz.length
            ? (language === 'ar' ? 'السؤال التالي' : 'Next Question')
            : (language === 'ar' ? 'عرض النتيجة' : 'See Results')}
          <ChevronRight className={`w-4 h-4 ${language === 'ar' ? 'rotate-180' : ''}`} />
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Adults Reflection Panel
// ---------------------------------------------------------------------------

export function AdultsReflectionPanel({
  story, language,
}: {
  story: QuranStory;
  language: 'ar' | 'en';
}) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  if (!story.adultsReflection) return null;
  const { prompts, thematicConnectionsArabic, thematicConnectionsEnglish } = story.adultsReflection;
  const connections = language === 'ar' ? thematicConnectionsArabic : thematicConnectionsEnglish;

  return (
    <div className="card border border-primary-200 bg-primary-50/30">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="w-5 h-5 text-primary-600" />
        <h3 className="font-semibold text-primary-900">
          {language === 'ar' ? 'للتأمل والتدبر' : 'For Reflection and Contemplation'}
        </h3>
      </div>

      <div className="space-y-3 mb-4">
        {prompts.map((prompt) => {
          const isOpen = expanded.has(prompt.promptId);
          const promptText = language === 'ar' ? prompt.promptArabic : prompt.promptEnglish;
          const theme = language === 'ar' ? prompt.themeArabic : prompt.themeEnglish;

          return (
            <div
              key={prompt.promptId}
              className="bg-white rounded-lg border border-primary-100 overflow-hidden"
            >
              <button
                onClick={() => {
                  const next = new Set(expanded);
                  isOpen ? next.delete(prompt.promptId) : next.add(prompt.promptId);
                  setExpanded(next);
                }}
                className="w-full flex items-start gap-3 p-4 text-start hover:bg-primary-50 transition-colors"
              >
                <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs text-primary-700">?</span>
                </div>
                <div className="flex-1">
                  <span className="text-xs font-medium text-primary-600 block mb-1">{theme}</span>
                  <span
                    className="text-sm text-gray-800 font-medium"
                    dir={language === 'ar' ? 'rtl' : 'ltr'}
                  >
                    {promptText}
                  </span>
                </div>
                <ChevronRight className={`w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Thematic connections */}
      <div className="border-t border-primary-100 pt-4">
        <div className="flex items-start gap-2">
          <Network className="w-4 h-4 text-primary-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-primary-700 mb-1">
              {language === 'ar' ? 'الصلات الموضوعية مع قصص أخرى' : 'Thematic Connections to Other Stories'}
            </p>
            <p className="text-xs text-gray-600" dir={language === 'ar' ? 'rtl' : 'ltr'}>
              {connections}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Grouped Segment List
// ---------------------------------------------------------------------------

const SECTION_ORDER: SegmentSectionType[] = ['introduction', 'key_event', 'moral', 'endnote'];

export function GroupedSegmentList({
  story, level, language,
}: {
  story: QuranStory;
  level: AudienceLevel;
  language: 'ar' | 'en';
}) {
  const sorted = [...story.storySegments]
    .filter(isSegmentSafeToDisplay)
    .sort((a, b) => a.sequenceOrder - b.sequenceOrder);

  // Group by sectionType
  const grouped = new Map<SegmentSectionType | 'ungrouped', StorySegment[]>();
  for (const seg of sorted) {
    const key = seg.sectionType ?? 'ungrouped';
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(seg);
  }

  const orderedKeys: (SegmentSectionType | 'ungrouped')[] = [
    ...SECTION_ORDER.filter((k) => grouped.has(k)),
    ...(grouped.has('ungrouped') ? ['ungrouped' as const] : []),
  ];

  return (
    <div className="space-y-1">
      {orderedKeys.map((sectionType) => {
        const segments = grouped.get(sectionType) ?? [];
        return (
          <div key={sectionType}>
            {sectionType !== 'ungrouped' && (
              <SectionHeader sectionType={sectionType} language={language} />
            )}
            <div className="space-y-4">
              {segments.map((segment) => (
                <SegmentCard
                  key={segment.segmentId}
                  segment={segment}
                  level={level}
                  language={language}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
