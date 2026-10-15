/**
 * Map internal pipeline warnings to short bilingual user-facing notices.
 *
 * Generated data carries developer-oriented warnings such as
 * "From cluster_000012 (graph_community); needs_review." or
 * "Low-confidence pattern match (0.55). Context review required." — English
 * strings with internal tokens that were rendered verbatim, including in the
 * Arabic UI. Pages must render warnings through `toUserWarnings`, which:
 *   - classifies each warning into a small set of user-facing codes,
 *   - returns each code once, in the active language,
 *   - drops warnings it cannot classify (shown raw only in development).
 */

export type UserWarningCode =
  | 'pending_review'
  | 'inferred_link'
  | 'approx_order'
  | 'compact_profile'
  | 'evidence_only'
  | 'not_quran_name'
  | 'ambiguous_word'
  | 'no_occurrence';

export interface UserWarning {
  code: UserWarningCode | 'raw';
  text: string;
}

export const USER_WARNING_TEXT: Record<UserWarningCode, { ar: string; en: string }> = {
  pending_review: {
    ar: 'هذا المحتوى بانتظار مراجعة علمية',
    en: 'This content is awaiting scholarly review',
  },
  inferred_link: {
    ar: 'هذا الربط مستنتج آليًا وقد لا يكون دقيقًا',
    en: 'This link was inferred automatically and may be inaccurate',
  },
  approx_order: {
    ar: 'الترتيب تقريبي للتصفّح فقط',
    en: 'Order is approximate, for browsing only',
  },
  compact_profile: {
    ar: 'القرآن لا يفصّل قصة هذا النبي؛ هذا ملف موجز',
    en: 'The Quran does not narrate this prophet in detail; this is a compact profile',
  },
  evidence_only: {
    ar: 'تعرض هذه الصفحة الشواهد القرآنية فقط وليست سيرة كاملة',
    en: 'This page presents Quranic evidence only and is not a full biography',
  },
  not_quran_name: {
    ar: 'لم يرد هذا الاسم بلفظه اسمًا لله في القرآن',
    en: 'This name is not stated in the Quran as a divine name',
  },
  ambiguous_word: {
    ar: 'لهذه الكلمة معانٍ أخرى في القرآن، فليست كل مواضعها اسمًا لله',
    en: 'This word has other meanings in the Quran, so not every occurrence is a divine name',
  },
  no_occurrence: {
    ar: 'لم يُرصد هذا الاسم بلفظه في نص القرآن',
    en: 'No explicit occurrence of this name was detected in the Quran text',
  },
};

// Ordered: the first matching rule wins.
const RULES: Array<[RegExp, UserWarningCode]> = [
  [/does not narrate this prophet|لا يفصّل قصة/i, 'compact_profile'],
  [/Quranic evidence only|الشواهد القرآنية فقط|seerah_deferred/i, 'evidence_only'],
  [/No explicit Quran occurrence/i, 'no_occurrence'],
  [/Not in Quran as an explicit|from hadith traditions/i, 'not_quran_name'],
  [/also means|most commonly|also a personal|rarely used|Highest-frequency lemma|displayed separately/i, 'ambiguous_word'],
  [/order|chronolog|navigation aid|guided reading sequence|succession/i, 'approx_order'],
  [
    /inferred|co-mention|co-occurrence|graph_community|derived from|generic alias|downgraded|pattern match|low-confidence|triggered by pattern|auto-clustered|shared \d+ ayahs|anchored to|title-style|refers to|seed-taxonomy|not resolved/i,
    'inferred_link',
  ],
  [/review|sign-off|verify|needs_review|requires|pending|مراجعة/i, 'pending_review'],
];

/** Developer notes with no user-facing meaning; always dropped. */
const INTERNAL_ONLY: RegExp[] = [
  /only curated for .* in this release/i,
  /^missing_story_page:/i,
  /deferred to a future scan/i,
  /exposed via `divineNameAllah`/i,
];

export function isInternalWarning(warning: string): boolean {
  return INTERNAL_ONLY.some((re) => re.test(warning));
}

export function classifyWarning(warning: string): UserWarningCode | null {
  if (isInternalWarning(warning)) return null;
  for (const [re, code] of RULES) if (re.test(warning)) return code;
  return null;
}

export function toUserWarnings(
  warnings: readonly string[] | null | undefined,
  language: 'ar' | 'en',
  { showUnmatched = import.meta.env?.DEV ?? false }: { showUnmatched?: boolean } = {},
): UserWarning[] {
  const out: UserWarning[] = [];
  const seen = new Set<string>();
  for (const w of warnings ?? []) {
    const code = classifyWarning(w);
    if (code) {
      if (seen.has(code)) continue;
      seen.add(code);
      out.push({ code, text: USER_WARNING_TEXT[code][language] });
    } else if (showUnmatched && !seen.has(w)) {
      seen.add(w);
      out.push({ code: 'raw', text: w });
    }
  }
  return out;
}
