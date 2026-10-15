/**
 * ProvenanceLabel — one shared pill that says where a piece of content comes
 * from, so authored / analytical / auto-detected material is never mistaken
 * for Qur'an text or retrieved tafsir.
 *
 * kinds:
 *   quran_ref         — a Qur'an reference (verse numbers only)
 *   tafsir_retrieved  — text retrieved from a registered tafsir source
 *                       (shows that source's title + author)
 *   editorial_summary — an editorial summary written for the app (not tafsir)
 *   analytical        — an analytical link between items (not tafsir)
 *   auto_detected     — produced by an automatic pipeline, not reviewed
 *
 * The label text is rendered in the active language inside an explicit
 * <span dir>, and the explanation sits in a <details> disclosure so it works
 * on touch screens (no hover-only tooltip).
 */

import clsx from 'clsx';
import { BookOpen, FileText, GitBranch, Cpu, Library, type LucideIcon } from 'lucide-react';
import { getSourceById } from '../../data/sourceRegistry';

export type ProvenanceKind =
  | 'quran_ref'
  | 'tafsir_retrieved'
  | 'editorial_summary'
  | 'analytical'
  | 'auto_detected';

export type ProvenanceStatus = 'needs_review' | 'approved';

interface Bilingual {
  ar: string;
  en: string;
}

export const PROVENANCE_LABELS: Record<ProvenanceKind, { label: Bilingual; explain: Bilingual; icon: LucideIcon; classes: string }> = {
  quran_ref: {
    label: { ar: 'مرجع قرآني', en: "Qur'an reference" },
    explain: {
      ar: 'إحالة إلى سورة وآية. نص القرآن يُعرض من مصدره المعتمد فقط.',
      en: "A pointer to a surah and ayah. Qur'an text is only shown from its canonical source.",
    },
    icon: BookOpen,
    classes: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  },
  tafsir_retrieved: {
    label: { ar: 'من مصدر تفسير', en: 'From a tafsir source' },
    explain: {
      ar: 'نص مسترجع من مصدر تفسير مسجّل، مع ذكر المؤلف والكتاب.',
      en: 'Text retrieved from a registered tafsir source, with its author and title.',
    },
    icon: Library,
    classes: 'bg-blue-50 text-blue-800 border-blue-200',
  },
  editorial_summary: {
    label: { ar: 'ملخص تحريري — ليس تفسيرًا', en: 'Editorial summary — not tafsir' },
    explain: {
      ar: 'ملخص كتبه فريق التطبيق للتعريف فقط، وليس نقلًا عن تفسير، ويحتاج مراجعة علمية.',
      en: 'A summary written by the app team as an introduction only. It is not quoted from a tafsir and needs scholarly review.',
    },
    icon: FileText,
    classes: 'bg-gray-50 text-gray-700 border-gray-200',
  },
  analytical: {
    label: { ar: 'ربط تحليلي — ليس تفسيرًا', en: 'Analytical link — not tafsir' },
    explain: {
      ar: 'ربط بين موضوعين أو قصتين اقترحه التطبيق للتأمل والتصفح، وليس قولًا لمفسّر.',
      en: 'A connection the app suggests for reflection and browsing. It is not a statement by a mufassir.',
    },
    icon: GitBranch,
    classes: 'bg-violet-50 text-violet-800 border-violet-200',
  },
  auto_detected: {
    label: { ar: 'مُستخرج آليًا', en: 'Auto-detected' },
    explain: {
      ar: 'نتج عن معالجة آلية للنص وقد يحتوي أخطاء، ولم يراجعه مختص بعد.',
      en: 'Produced by automatic processing. It may contain errors and has not been reviewed by a specialist yet.',
    },
    icon: Cpu,
    classes: 'bg-amber-50 text-amber-800 border-amber-200',
  },
};

const STATUS_LABELS: Record<ProvenanceStatus, Bilingual> = {
  needs_review: { ar: 'بانتظار المراجعة', en: 'Awaiting review' },
  approved: { ar: 'تمت مراجعته', en: 'Reviewed' },
};

export interface ProvenanceLabelProps {
  kind: ProvenanceKind;
  language: 'ar' | 'en';
  status?: ProvenanceStatus;
  /** For tafsir_retrieved: registry sourceId whose title + author are shown. */
  sourceId?: string;
  /** Hide the explanation disclosure (e.g. inside dense lists). */
  compact?: boolean;
  className?: string;
}

export function ProvenanceLabel({ kind, language, status, sourceId, compact = false, className }: ProvenanceLabelProps) {
  const cfg = PROVENANCE_LABELS[kind];
  const Icon = cfg.icon;
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  let label = cfg.label[language];
  if (kind === 'tafsir_retrieved' && sourceId) {
    const src = getSourceById(sourceId);
    if (src) {
      label = language === 'ar' ? `${src.titleArabic} — ${src.author}` : `${src.titleEnglish} — ${src.author}`;
    }
  }

  const pill = (
    <span
      className={clsx('inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded-full border', cfg.classes)}
      data-provenance={kind}
    >
      <Icon className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
      <span dir={dir} lang={language}>{label}</span>
      {status && (
        <span dir={dir} lang={language} className="opacity-75">
          {' · '}
          {STATUS_LABELS[status][language]}
        </span>
      )}
    </span>
  );

  if (compact) return <span className={clsx('inline-flex', className)}>{pill}</span>;

  return (
    <details className={clsx('inline-block align-middle group', className)}>
      <summary className="list-none cursor-pointer [&::-webkit-details-marker]:hidden">{pill}</summary>
      <span
        dir={dir}
        lang={language}
        className="block mt-1 max-w-xs text-[11px] leading-relaxed text-gray-600 bg-white border border-gray-200 rounded-lg px-2 py-1.5 shadow-sm"
      >
        {cfg.explain[language]}
      </span>
    </details>
  );
}

export default ProvenanceLabel;
