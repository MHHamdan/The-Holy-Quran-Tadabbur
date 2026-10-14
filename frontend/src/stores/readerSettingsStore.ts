/**
 * Reader Settings Store
 *
 * Preferences for the Qur'an reader that should survive a reload: Arabic
 * script, text size, which translation editions to show, view behaviour, and
 * recitation (reciter, speed, how often each verse repeats).
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
export type ReaderTheme = 'light' | 'sepia' | 'night';

/** The backend accepts at most this many editions per request. */
export const MAX_TRANSLATIONS = 3;

export const FONT_SCALE_MIN = 0.8;
export const FONT_SCALE_MAX = 1.8;
export const FONT_SCALE_STEP = 0.1;

export const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5] as const;
/** How many times each verse plays before the next (memorisation aid). */
export const VERSE_REPEATS = [1, 2, 3, 5, 10] as const;

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
  theme: ReaderTheme;
  reciterId: string;
  playbackRate: number;
  verseRepeat: number;

  setScript: (script: QuranScript) => void;
  setFontScale: (scale: number) => void;
  setView: (view: ReaderView) => void;
  /** `current` is what the reader sees now (the language default until they choose). */
  toggleTranslation: (key: string, current: string[]) => void;
  clearTranslations: () => void;
  setAutoScroll: (on: boolean) => void;
  setTheme: (theme: ReaderTheme) => void;
  setReciterId: (id: string) => void;
  setPlaybackRate: (rate: number) => void;
  setVerseRepeat: (times: number) => void;
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
      theme: 'light',
      reciterId: 'mishary_afasy',
      playbackRate: 1,
      verseRepeat: 1,

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
      setTheme: (theme) => set({ theme }),
      setReciterId: (reciterId) => set({ reciterId }),
      setPlaybackRate: (playbackRate) => set({ playbackRate }),
      setVerseRepeat: (verseRepeat) => set({ verseRepeat }),
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

/**
 * The surah's opening Bismillah in the chosen script: set on verse 1 of
 * every surah except Al-Fatiha (where it is verse 1 itself) and At-Tawbah.
 * It comes from the API, never from the verse text.
 */
export function bismillahFor(
  verse: { bismillah_uthmani?: string | null; bismillah_imlaei?: string | null },
  script: QuranScript,
): string | null {
  return (script === 'uthmani' ? verse.bismillah_uthmani : verse.bismillah_imlaei) ?? null;
}

/** Verse text in the chosen script. */
export function verseTextFor(
  verse: { text_imlaei: string; text_uthmani: string },
  script: QuranScript,
): string {
  return script === 'uthmani' ? verse.text_uthmani : verse.text_imlaei;
}

/**
 * Apply the reading theme to the page background while a reader is mounted.
 * Returns the cleanup that restores the default.
 */
export function applyReaderThemeToDocument(theme: ReaderTheme): () => void {
  const root = document.documentElement;
  if (theme === 'light') delete root.dataset.readerTheme;
  else root.dataset.readerTheme = theme;
  return () => {
    delete root.dataset.readerTheme;
  };
}
