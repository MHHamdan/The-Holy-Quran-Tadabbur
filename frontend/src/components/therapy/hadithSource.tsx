/**
 * Display rule for hadith in the guidance and Heart Care views.
 *
 * A hadith is shown only when a reviewer has recorded a structured source with
 * at least the collection and the hadith number. A grade is shown only with
 * the scholar who graded it. Free-text hadith ("— Bukhari 69", "(Bukhari &
 * Muslim)") has no such record, so it stays hidden until a scholar verifies
 * the text, number, narrator and grade. Never fill these fields from memory.
 */
import clsx from 'clsx';

export interface HadithSource {
  collection: string;
  /** Hadith number in the named collection (edition-specific). */
  number: string | number;
  narrator?: string;
  grade?: string;
  grader?: string;
  url?: string;
}

/** True when the hadith carries enough provenance to be shown to readers. */
export function hasVerifiableHadithSource(
  src: Partial<HadithSource> | null | undefined,
): src is HadithSource {
  if (!src || typeof src.collection !== 'string' || src.collection.trim() === '') return false;
  const n: unknown = src.number;
  return (typeof n === 'string' && n.trim() !== '') || (typeof n === 'number' && Number.isFinite(n));
}

/** "Collection 123 · grade — grader" (grade only when its grader is named). */
export function hadithSourceLine(src: HadithSource): string {
  const grade = src.grade && src.grader ? ` · ${src.grade} — ${src.grader}` : '';
  return `${src.collection} ${src.number}${grade}`;
}

/** Small note shown in place of hidden, unverified hadith. */
export function HadithPendingReviewNote({ isRtl, className }: { isRtl: boolean; className?: string }) {
  return (
    <p
      className={clsx('text-xs text-gray-600 leading-relaxed', isRtl && 'font-arabic text-right', className)}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {isRtl
        ? 'الأحاديث المتعلقة بهذا الموضوع مخفية حتى يتحقق منها أهل الاختصاص (النص والرقم والدرجة).'
        : 'Related hadith are hidden until a scholar verifies them (text, number and grade).'}
    </p>
  );
}
