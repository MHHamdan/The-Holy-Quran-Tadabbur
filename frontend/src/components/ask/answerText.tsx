/**
 * Ask page text helpers: a safe renderer for answer text, bilingual warning
 * copy and translation-edition labels. No dangerouslySetInnerHTML — every
 * piece of API text is rendered as a React text node.
 */
import { Fragment, type ReactNode } from 'react';
import type { RAGResponse, RelatedVerse } from '../../lib/api';

type Lang = 'ar' | 'en';

/** Fields the backend returns that lib/api.ts does not type yet. */
export type AttributedRelatedVerse = RelatedVerse & {
  translation_edition?: string | null;
  translation_source_id?: string | null;
};

export type AskResponse = RAGResponse & {
  disagreement_warning_en?: string | null;
  disagreement_warning_ar?: string | null;
};

// ---------------------------------------------------------------- answer text

const ARABIC_RUN = /([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFC\uFD3E\uFD3F]+(?:\s+[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFC\uFD3E\uFD3F]+)*)/;
const LATIN_RUN = /([A-Za-z][A-Za-z'\u2019-]*(?:\s+[A-Za-z][A-Za-z'\u2019-]*)*)/;

/** Wrap runs of the other script so they get their own direction. */
function directionalRuns(text: string, language: Lang, keyPrefix: string): ReactNode[] {
  const pattern = language === 'en' ? ARABIC_RUN : LATIN_RUN;
  return text.split(pattern).map((part, i) => {
    if (!part) return null;
    if (i % 2 === 1) {
      return language === 'en' ? (
        <span key={`${keyPrefix}-${i}`} dir="rtl" lang="ar" className="font-arabic">{part}</span>
      ) : (
        <span key={`${keyPrefix}-${i}`} dir="ltr" lang="en">{part}</span>
      );
    }
    return <Fragment key={`${keyPrefix}-${i}`}>{part}</Fragment>;
  });
}

/** One paragraph: **bold** segments become <strong>, mixed scripts get spans. */
function renderInline(paragraph: string, language: Lang, key: string): ReactNode[] {
  return paragraph.split(/\*\*([^*\n]+)\*\*/).map((segment, i) =>
    i % 2 === 1 ? (
      <strong key={`${key}-b${i}`} className="font-semibold text-gray-900">
        {directionalRuns(segment, language, `${key}-b${i}`)}
      </strong>
    ) : (
      <Fragment key={`${key}-t${i}`}>{directionalRuns(segment, language, `${key}-t${i}`)}</Fragment>
    ),
  );
}

export function RichAnswerText({ text, language }: { text: string; language: Lang }) {
  const paragraphs = text.split('\n').map((p) => p.trim()).filter(Boolean);
  return (
    <>
      {paragraphs.map((para, i) => (
        <p key={i} className="mb-2 last:mb-0">
          {renderInline(para, language, `p${i}`)}
        </p>
      ))}
    </>
  );
}

// ------------------------------------------------------------------- warnings

const WARNING_COPY: Record<string, { ar: string; en: string } | null> = {
  // Rendered elsewhere (notice / caution card / the refusal text itself)
  ai_quota_exceeded: null,
  ai_unavailable: null,
  prompt_injection_refused: null,
  scientific_reflection_needs_review: null,
  ungrounded_answer_withheld: {
    en: 'The AI summary was withheld because it did not rely on the retrieved sources.',
    ar: 'حُجب الملخص الآلي لأنه لم يستند إلى المصادر المسترجعة.',
  },
  answer_withheld_by_guard: {
    en: 'The AI summary was withheld because it went beyond what the sources say.',
    ar: 'حُجب الملخص الآلي لأنه تجاوز ما تقوله المصادر.',
  },
  retrieval_degraded: {
    en: 'Meaning-based search is unavailable right now; the sources below were found by keyword and may be less relevant.',
    ar: 'البحث بالمعنى غير متاح حالياً؛ عُثر على المصادر أدناه بمطابقة الكلمات وقد تكون أقل صلة.',
  },
  unsupported_statements_removed: {
    en: 'Some statements were removed because the cited sources do not support them.',
    ar: 'حُذفت عبارات لا تدعمها المصادر المستشهد بها.',
  },
};

// Known sentence warnings from the backend, with their Arabic counterpart.
const SENTENCE_COPY: Array<{ match: RegExp; ar: string; en: string }> = [
  {
    match: /citation\(s\) could not be validated/i,
    en: 'Some citations did not match the retrieved sources and were removed.',
    ar: 'حُذفت استشهادات لم تطابق المصادر المسترجعة.',
  },
  {
    match: /quotation\(s\) were removed/i,
    en: 'Some quotations were removed because they do not match the Qur\'an or the cited sources word for word.',
    ar: 'حُذفت اقتباسات لا تطابق نص القرآن أو المصادر المستشهد بها حرفياً.',
  },
  {
    match: /lacks sufficient scholarly source support/i,
    en: 'This answer lacks sufficient support from the sources.',
    ar: 'هذه الإجابة لا تجد دعماً كافياً في المصادر.',
  },
  {
    match: /limited source support/i,
    en: 'This answer has limited support from the sources; please verify it.',
    ar: 'دعم المصادر لهذه الإجابة محدود؛ يُرجى التحقق منها.',
  },
  {
    match: /no primary scholarly sources/i,
    en: 'No primary tafsir sources were used in this answer.',
    ar: 'لم تُستخدم مصادر تفسير أصلية في هذه الإجابة.',
  },
  {
    match: /limited evidence density/i,
    en: 'Few sources were found for this question; consider checking more tafsir.',
    ar: 'عُثر على مصادر قليلة لهذا السؤال؛ يُستحسن مراجعة تفاسير أخرى.',
  },
  {
    match: /not be taken as a religious ruling \(fatwa\)/i,
    en: 'This is informational only, not a religious ruling (fatwa). Please consult qualified scholars.',
    ar: 'هذه معلومات تعليمية فقط وليست فتوى شرعية. يُرجى الرجوع إلى أهل العلم.',
  },
  {
    match: /supporting or experimental sources/i,
    en: 'All citations come from supporting sources; please verify with established tafsir.',
    ar: 'جميع الاستشهادات من مصادر مساندة؛ يُرجى التحقق من التفاسير المعتمدة.',
  },
];

const HAS_ARABIC = /[؀-ۿ]/;

/** Warnings in the UI language only: codes mapped, unknown codes hidden. */
export function localizeWarnings(warnings: string[] | undefined, language: Lang): string[] {
  const out: string[] = [];
  for (const raw of warnings ?? []) {
    const w = raw.trim();
    if (!w) continue;
    if (/^[a-z0-9_]+$/.test(w)) {
      const copy = WARNING_COPY[w];
      if (copy) out.push(copy[language]);
      continue; // unknown machine codes are never shown raw
    }
    const known = SENTENCE_COPY.find((s) => s.match.test(w));
    if (known) {
      out.push(known[language]);
    } else if (HAS_ARABIC.test(w) === (language === 'ar')) {
      out.push(w); // free text already in the UI language
    }
  }
  return Array.from(new Set(out));
}

// ----------------------------------------------------------- translations

const TRANSLATION_EDITIONS: Record<string, { en: string; ar: string }> = {
  english_saheeh: { en: 'Saheeh International (QuranEnc)', ar: 'صحيح إنترناشونال (QuranEnc)' },
  english_hilali_khan: { en: 'Hilali & Khan (QuranEnc)', ar: 'الهلالي وخان (QuranEnc)' },
  english_rwwad: { en: 'Rowwad Translation Center (QuranEnc)', ar: 'مركز رواد الترجمة (QuranEnc)' },
};

export function translationLabel(edition: string | null | undefined, language: Lang): string {
  const name = edition ? TRANSLATION_EDITIONS[edition]?.[language] : undefined;
  if (language === 'ar') return name ? `ترجمة المعاني بالإنجليزية — ${name}` : 'ترجمة المعاني بالإنجليزية';
  return name ? `English translation of the meanings — ${name}` : 'English translation of the meanings';
}

/** Single-language disagreement notice. */
export function disagreementText(response: AskResponse, language: Lang): string | null {
  return (language === 'ar' ? response.disagreement_warning_ar : response.disagreement_warning_en) || null;
}
