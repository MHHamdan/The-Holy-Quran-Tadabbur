import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Language, t as translateFn } from '../i18n/translations';

function detectDefaultLanguage(): Language {
  try {
    const langs = navigator.languages ?? [navigator.language];
    for (const lang of langs) {
      if (lang.startsWith('ar')) return 'ar';
    }
  } catch {
    // ignore
  }
  return 'en';
}

interface LanguageState {
  language: Language;
  direction: 'ltr' | 'rtl';
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  t: (key: string) => string;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set, get) => ({
      language: detectDefaultLanguage(),
      direction: detectDefaultLanguage() === 'ar' ? 'rtl' : 'ltr',

      t: (key: string) => translateFn(key, get().language),

      setLanguage: (lang: Language) => {
        const dir = lang === 'ar' ? 'rtl' : 'ltr';
        document.documentElement.dir = dir;
        document.documentElement.lang = lang;
        set({ language: lang, direction: dir });
      },

      toggleLanguage: () => {
        set((state) => {
          const newLang = state.language === 'en' ? 'ar' : 'en';
          const dir = newLang === 'ar' ? 'rtl' : 'ltr';
          document.documentElement.dir = dir;
          document.documentElement.lang = newLang;
          return { language: newLang, direction: dir };
        });
      },
    }),
    {
      name: 'tadabbur-language',
      onRehydrateStorage: () => (state) => {
        if (state) {
          document.documentElement.dir = state.direction;
          document.documentElement.lang = state.language;
        } else {
          // No stored preference — apply detected language to DOM
          const detected = detectDefaultLanguage();
          document.documentElement.dir = detected === 'ar' ? 'rtl' : 'ltr';
          document.documentElement.lang = detected;
        }
      },
    }
  )
);
