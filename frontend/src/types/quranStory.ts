/**
 * Quran Story Data Model — Tadabbur Al-Quran
 *
 * This type system governs ALL story data displayed or validated on the platform.
 *
 * Safety rules:
 * - Every story MUST have at least one quranReference
 * - Every adult explanation MUST have at least one sourceId
 * - sourceIds MUST match entries in sourceRegistry
 * - Kids explanations are still source-grounded (same sourceIds, simpler prose)
 * - Arabic text (arabicText) is NEVER written directly — it is fetched from the Quran DB
 * - Translation text is labeled as translation, NEVER displayed as Quran text
 * - No tafsir is generated — all explanations reference verified source chunks
 */

// ---------------------------------------------------------------------------
// Audience Level
// ---------------------------------------------------------------------------

export type AudienceLevel = 'kids' | 'adults';

// ---------------------------------------------------------------------------
// Section Type — categorises each segment in the reading flow
// ---------------------------------------------------------------------------

export type SegmentSectionType = 'introduction' | 'key_event' | 'moral' | 'endnote';

export const SECTION_TYPE_META: Record<SegmentSectionType, {
  labelAr: string;
  labelEn: string;
  colorClass: string;
  bgClass: string;
}> = {
  introduction: { labelAr: 'المقدمة', labelEn: 'Introduction', colorClass: 'text-blue-700', bgClass: 'bg-blue-50 border-blue-200' },
  key_event: { labelAr: 'أحداث رئيسية', labelEn: 'Key Events', colorClass: 'text-primary-700', bgClass: 'bg-primary-50 border-primary-200' },
  moral: { labelAr: 'الدروس والعبر', labelEn: 'Morals & Lessons', colorClass: 'text-emerald-700', bgClass: 'bg-emerald-50 border-emerald-200' },
  endnote: { labelAr: 'تأمل ختامي', labelEn: 'Endnote', colorClass: 'text-amber-700', bgClass: 'bg-amber-50 border-amber-200' },
};

// ---------------------------------------------------------------------------
// Story Overview — bilingual intro + summary per audience
// ---------------------------------------------------------------------------

export interface StoryOverview {
  introKidsArabic: string;
  introKidsEnglish: string;
  introAdultsArabic: string;
  introAdultsEnglish: string;
  summaryKidsArabic: string;
  summaryKidsEnglish: string;
  summaryAdultsArabic: string;
  summaryAdultsEnglish: string;
  coreThemeArabic: string;
  coreThemeEnglish: string;
}

// ---------------------------------------------------------------------------
// Kids Quiz
// ---------------------------------------------------------------------------

export interface KidsQuizQuestion {
  questionId: string;
  questionArabic: string;
  questionEnglish: string;
  optionsArabic: string[];
  optionsEnglish: string[];
  correctOptionIndex: number;
  explanationArabic: string;
  explanationEnglish: string;
}

// ---------------------------------------------------------------------------
// Adults Reflection
// ---------------------------------------------------------------------------

export interface AdultsReflectionPrompt {
  promptId: string;
  promptArabic: string;
  promptEnglish: string;
  themeArabic: string;
  themeEnglish: string;
}

export interface AdultsReflection {
  prompts: AdultsReflectionPrompt[];
  thematicConnectionsArabic: string;
  thematicConnectionsEnglish: string;
}

// ---------------------------------------------------------------------------
// Source Validation
// ---------------------------------------------------------------------------

export type SunniReviewStatus = 'approved' | 'needs_review' | 'rejected';

export interface MatchedEvidence {
  sourceId: string;
  sourceTitle: string;
  evidenceSummary: string;
  surahNumber: number;
  ayahStart: number;
  ayahEnd: number;
}

export interface SunniReview {
  status: SunniReviewStatus;
  reviewedAgainst: string[];
  matchedEvidence: MatchedEvidence[];
  disagreementNotes: string[];
  humanReviewRequired: boolean;
}

// ---------------------------------------------------------------------------
// Quran Reference
// ---------------------------------------------------------------------------

export interface QuranReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd: number;
  referenceLabel: string;
  arabicText?: never; // Never write Arabic text as a string literal
  translationText?: string;
  translationSourceId?: string;
  tafsirSourceIds: string[];
}

// ---------------------------------------------------------------------------
// Story Segment
// ---------------------------------------------------------------------------

export interface StorySegment {
  segmentId: string;
  titleArabic: string;
  titleEnglish: string;
  surahNumber: number;
  ayahStart: number;
  ayahEnd: number;
  sequenceOrder: number;
  sectionType?: SegmentSectionType;
  summaryKidsArabic: string;
  summaryKidsEnglish: string;
  summaryAdultsArabic: string;
  summaryAdultsEnglish: string;
  lessonsArabic: string[];
  lessonsEnglish: string[];
  sourceIds: string[];
  warnings: string[];
  sunniReview: SunniReview;
}

// ---------------------------------------------------------------------------
// Related Story
// ---------------------------------------------------------------------------

export type StoryRelationType =
  | 'same_prophet'
  | 'same_theme'
  | 'same_event_pattern'
  | 'same_moral_lesson'
  | 'contrast'
  | 'chronological'
  | 'same_surah'
  | 'shared_character';

export interface EvidenceReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd: number;
  sourceIds: string[];
}

export interface RelatedStory {
  storyId: string;
  relationType: StoryRelationType;
  explanationArabic: string;
  explanationEnglish: string;
  evidenceReferences: EvidenceReference[];
}

// ---------------------------------------------------------------------------
// Story Reliability
// ---------------------------------------------------------------------------

export type StoryReliabilityLevel = 'canonical' | 'verified' | 'supporting';

// ---------------------------------------------------------------------------
// Full Quran Story
// ---------------------------------------------------------------------------

export interface QuranStory {
  storyId: string;
  slug: string;
  titleArabic: string;
  titleEnglish: string;
  mainCharacters: string[];
  prophetsMentioned?: string[];
  relatedPeople?: string[];
  relatedPlaces?: string[];
  quranReferences: QuranReference[];
  storySegments: StorySegment[];
  themes: string[];
  concepts: string[];
  relatedStories: RelatedStory[];
  audienceLevels: AudienceLevel[];
  sourceIds: string[];
  reliabilityLevel: StoryReliabilityLevel;
  lastReviewedAt: string;
  overview?: StoryOverview;
  kidsQuiz?: KidsQuizQuestion[];
  adultsReflection?: AdultsReflection;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function getSegmentSummary(
  segment: StorySegment,
  level: AudienceLevel,
  language: 'ar' | 'en'
): string {
  if (level === 'kids') {
    return language === 'ar' ? segment.summaryKidsArabic : segment.summaryKidsEnglish;
  }
  return language === 'ar' ? segment.summaryAdultsArabic : segment.summaryAdultsEnglish;
}

export function getSegmentLessons(
  segment: StorySegment,
  language: 'ar' | 'en'
): string[] {
  return language === 'ar' ? segment.lessonsArabic : segment.lessonsEnglish;
}

export function isSegmentSafeToDisplay(segment: StorySegment): boolean {
  return segment.sunniReview.status !== 'rejected';
}

export function segmentNeedsReviewWarning(segment: StorySegment): boolean {
  return segment.sunniReview.status === 'needs_review';
}
