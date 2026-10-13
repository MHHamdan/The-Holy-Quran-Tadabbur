/**
 * Reader Settings Store
 *
 * Preferences for the Qur'an reader that should survive a reload: Arabic
 * script, text size, which translation editions to show, and view behaviour.
 * Persisted to localStorage (device-local, like bookmarks).
 *
 * Translation editions are keys from GET /quran/translations/editions. Until
 * the reader picks some, the default follows the UI language: the English
 * default edition for English, none for Arabic.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Language } from '../i18n/translations';

/** imlaei: simplified modern spelling. uthmani: the Madinah Mushaf rasm. */
export type QuranScript = 'imlaei' | 'uthmani';
export type ReaderView = 'mushaf' | 'list';

/** The backend accepts at most this many editions per request. */
export const MAX_TRANSLATIONS = 3;

export const FONT_SCALE_MIN = 0.8;
export const FONT_SCALE_MAX = 1.8;
export const FONT_SCALE_STEP = 0.1;

const DEFAULT_TRANSLATIONS: Record<Language, string[]> = {
  en: ['english_saheeh'],
  ar: [],
};

interface ReaderSettingsState {
  script: QuranScript;
  fontScale: number;
  view: ReaderView;
  /** null until the reader chooses; then the chosen keys (possibly empty). */
  translationKeys: string[] | null;
  autoScroll: boolean;

  setScript: (script: QuranScript) => void;
  setFontScale: (scale: number) => void;
  setView: (view: ReaderView) => void;
  /** `current` is what the reader sees now (the language default until they choose). */
  toggleTranslation: (key: string, current: string[]) => void;
  clearTranslations: () => void;
  setAutoScroll: (on: boolean) => void;
}

const clampScale = (scale: number) =>
  Math.round(Math.min(FONT_SCALE_MAX, Math.max(FONT_SCALE_MIN, scale)) * 10) / 10;

export const useReaderSettingsStore = create<ReaderSettingsState>()(
  persist(
    (set) => ({
      script: 'imlaei',
      fontScale: 1,
      view: 'mushaf',
      translationKeys: null,
      autoScroll: true,

      setScript: (script) => set({ script }),
      setFontScale: (scale) => set({ fontScale: clampScale(scale) }),
      setView: (view) => set({ view }),
      toggleTranslation: (key, current) =>
        set(() => {
          if (current.includes(key)) {
            return { translationKeys: current.filter((k) => k !== key) };
          }
          // Adding past the limit drops the oldest choice.
          return { translationKeys: [...current, key].slice(-MAX_TRANSLATIONS) };
        }),
      clearTranslations: () => set({ translationKeys: [] }),
      setAutoScroll: (autoScroll) => set({ autoScroll }),
    }),
    { name: 'tadabbur-reader-settings', version: 1 },
  ),
);

/** The editions to request: the reader's choice, else the UI-language default. */
export function effectiveTranslationKeys(
  chosen: string[] | null,
  language: Language,
): string[] {
  return chosen ?? DEFAULT_TRANSLATIONS[language];
}

/** Verse text in the chosen script. */
export function verseTextFor(
  verse: { text_imlaei: string; text_uthmani: string },
  script: QuranScript,
): string {
  return script === 'uthmani' ? verse.text_uthmani : verse.text_imlaei;
}
