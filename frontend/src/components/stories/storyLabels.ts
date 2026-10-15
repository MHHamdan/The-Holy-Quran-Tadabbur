/**
 * Display labels for ids that must never reach users raw: story ids,
 * relation types, connection types and tafsir source ids.
 */
import { getRegistry } from '../../utils/storyRegistryAdapter';
import { getSourceById } from '../../data/sourceRegistry';
import { getTopicSeedById } from '../../data/quranTopicSeeds';

/** Topic label from the topic seed dictionary, or null when unknown. */
export function topicLabel(topicId: string, language: 'ar' | 'en'): string | null {
  const t = getTopicSeedById(topicId);
  if (!t) return null;
  return language === 'ar' ? t.labelArabic : t.labelEnglish;
}

type Lang = 'ar' | 'en';
interface Bilingual {
  ar: string;
  en: string;
}

/** Story title from the generated registry; falls back to a humanised id (EN) or a generic label (AR). */
export function storyTitle(storyId: string, language: Lang): string {
  const entry = getRegistry().stories.find((s) => s.storyId === storyId);
  if (entry) return language === 'ar' ? entry.titleArabic : entry.titleEnglish;
  if (language === 'ar') return 'قصة قرآنية';
  return storyId.replace(/^story_/, '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export const RELATION_TYPE_LABELS: Record<string, Bilingual> = {
  same_prophet: { ar: 'النبي نفسه', en: 'Same prophet' },
  same_theme: { ar: 'موضوع مشترك', en: 'Shared theme' },
  same_event_pattern: { ar: 'نمط أحداث متشابه', en: 'Similar pattern of events' },
  same_moral_lesson: { ar: 'عبرة مشتركة', en: 'Shared lesson' },
  contrast: { ar: 'مقابلة', en: 'Contrast' },
  chronological: { ar: 'تسلسل زمني', en: 'Chronological' },
  same_surah: { ar: 'في السورة نفسها', en: 'Same surah' },
  shared_character: { ar: 'شخصية مشتركة', en: 'Shared figure' },
  // cross_story_connections.connection_type
  thematic: { ar: 'ربط موضوعي', en: 'Thematic link' },
  continuation: { ar: 'امتداد للقصة', en: 'Continuation' },
  parallel: { ar: 'تشابه', en: 'Parallel' },
  prophetic_chain: { ar: 'سلسلة الأنبياء', en: 'Line of prophets' },
  shared_figure: { ar: 'شخصية مشتركة', en: 'Shared figure' },
};

export function relationTypeLabel(type: string | undefined, language: Lang): string {
  if (!type) return '';
  const l = RELATION_TYPE_LABELS[type];
  if (l) return l[language];
  return language === 'ar' ? 'صلة' : 'Related';
}

/**
 * Classical tafsir works referenced by legacy short ids in the story data
 * (ibn_kathir, tabari, ...). Names only — no content is attributed here.
 */
const LEGACY_TAFSIR_LABELS: Record<string, Bilingual> = {
  ibn_kathir: { ar: 'تفسير ابن كثير', en: 'Tafsir Ibn Kathir' },
  tabari: { ar: 'تفسير الطبري', en: 'Tafsir al-Tabari' },
  tabari_ar: { ar: 'تفسير الطبري', en: 'Tafsir al-Tabari' },
  qurtubi: { ar: 'تفسير القرطبي', en: 'Tafsir al-Qurtubi' },
  qurtubi_ar: { ar: 'تفسير القرطبي', en: 'Tafsir al-Qurtubi' },
  saadi: { ar: 'تفسير السعدي', en: "Tafsir al-Sa'di" },
  baghawi: { ar: 'تفسير البغوي', en: 'Tafsir al-Baghawi' },
  muyassar: { ar: 'التفسير الميسر', en: 'Al-Tafsir al-Muyassar' },
  muyassar_ar: { ar: 'التفسير الميسر', en: 'Al-Tafsir al-Muyassar' },
  jalalayn_en: { ar: 'تفسير الجلالين', en: 'Tafsir al-Jalalayn' },
  qac_corpus: { ar: 'مدوّنة القرآن العربية', en: 'Quranic Arabic Corpus' },
  lane_lexicon: { ar: 'معجم لين', en: "Lane's Lexicon" },
};

/**
 * Human-readable title for a tafsir / reference source id, or null when the
 * id is unknown (callers hide unknown ids instead of printing them).
 */
export function sourceLabel(sourceId: string, language: Lang): string | null {
  const legacy = LEGACY_TAFSIR_LABELS[sourceId];
  if (legacy) return legacy[language];
  const reg = getSourceById(sourceId);
  if (reg) return language === 'ar' ? reg.titleArabic : reg.titleEnglish;
  return null;
}
