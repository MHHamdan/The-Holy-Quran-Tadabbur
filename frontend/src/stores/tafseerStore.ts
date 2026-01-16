/**
 * Tafseer Preferences Store
 *
 * Manages user preferences for tafseer display:
 * - Preferred tafseer editions
 * - Language preferences
 * - Display settings
 *
 * Persisted to localStorage for persistence across sessions.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Available tafseer editions from alquran.cloud
 */
export type TafseerEdition =
  // Arabic Tafsir
  | 'ar.muyassar'    // التفسير الميسر
  | 'ar.jalalayn'    // تفسير الجلالين
  | 'ar.ibnkathir'   // تفسير ابن كثير
  | 'ar.qurtubi'     // تفسير القرطبي
  | 'ar.tabari'      // تفسير الطبري
  | 'ar.baghawi'     // تفسير البغوي
  // English Translations
  | 'en.sahih'       // Sahih International
  | 'en.pickthall'   // Pickthall
  | 'en.yusufali'    // Yusuf Ali
  | 'en.hilali';     // Hilali & Khan

/**
 * Edition metadata for display
 */
export const EDITION_METADATA: Record<TafseerEdition, {
  nameAr: string;
  nameEn: string;
  authorAr: string;
  authorEn: string;
  language: 'ar' | 'en';
  type: 'tafsir' | 'translation';
}> = {
  'ar.muyassar': {
    nameAr: 'التفسير الميسر',
    nameEn: 'Al-Muyassar (Simplified)',
    authorAr: 'مجمع الملك فهد',
    authorEn: 'King Fahd Complex',
    language: 'ar',
    type: 'tafsir',
  },
  'ar.jalalayn': {
    nameAr: 'تفسير الجلالين',
    nameEn: 'Tafsir Al-Jalalayn',
    authorAr: 'جلال الدين المحلي وجلال الدين السيوطي',
    authorEn: 'Al-Mahalli & As-Suyuti',
    language: 'ar',
    type: 'tafsir',
  },
  'ar.ibnkathir': {
    nameAr: 'تفسير ابن كثير',
    nameEn: 'Tafsir Ibn Kathir',
    authorAr: 'ابن كثير',
    authorEn: 'Ibn Kathir',
    language: 'ar',
    type: 'tafsir',
  },
  'ar.qurtubi': {
    nameAr: 'تفسير القرطبي',
    nameEn: 'Tafsir Al-Qurtubi',
    authorAr: 'القرطبي',
    authorEn: 'Al-Qurtubi',
    language: 'ar',
    type: 'tafsir',
  },
  'ar.tabari': {
    nameAr: 'تفسير الطبري',
    nameEn: 'Tafsir At-Tabari',
    authorAr: 'الطبري',
    authorEn: 'At-Tabari',
    language: 'ar',
    type: 'tafsir',
  },
  'ar.baghawi': {
    nameAr: 'تفسير البغوي',
    nameEn: 'Tafsir Al-Baghawi',
    authorAr: 'البغوي',
    authorEn: 'Al-Baghawi',
    language: 'ar',
    type: 'tafsir',
  },
  'en.sahih': {
    nameAr: 'الترجمة الصحيحة',
    nameEn: 'Sahih International',
    authorAr: 'صحيح انترناشيونال',
    authorEn: 'Sahih International',
    language: 'en',
    type: 'translation',
  },
  'en.pickthall': {
    nameAr: 'ترجمة بيكثال',
    nameEn: 'Pickthall Translation',
    authorAr: 'محمد مارمادوك بيكثال',
    authorEn: 'Muhammad M. Pickthall',
    language: 'en',
    type: 'translation',
  },
  'en.yusufali': {
    nameAr: 'ترجمة يوسف علي',
    nameEn: 'Yusuf Ali Translation',
    authorAr: 'عبد الله يوسف علي',
    authorEn: 'Abdullah Yusuf Ali',
    language: 'en',
    type: 'translation',
  },
  'en.hilali': {
    nameAr: 'ترجمة الهلالي وخان',
    nameEn: 'Hilali & Khan',
    authorAr: 'تقي الدين الهلالي ومحسن خان',
    authorEn: 'Hilali & Muhsin Khan',
    language: 'en',
    type: 'translation',
  },
};

/**
 * Default editions for bilingual display
 */
export const DEFAULT_EDITIONS: TafseerEdition[] = ['ar.muyassar', 'en.sahih'];

interface TafseerState {
  // User preferences
  preferredEditions: TafseerEdition[];
  preferredLanguage: 'ar' | 'en' | 'both';
  showTransliteration: boolean;

  // Actions
  setPreferredEditions: (editions: TafseerEdition[]) => void;
  addEdition: (edition: TafseerEdition) => void;
  removeEdition: (edition: TafseerEdition) => void;
  setPreferredLanguage: (lang: 'ar' | 'en' | 'both') => void;
  toggleTransliteration: () => void;
  resetToDefaults: () => void;
}

export const useTafseerStore = create<TafseerState>()(
  persist(
    (set) => ({
      // Default preferences
      preferredEditions: DEFAULT_EDITIONS,
      preferredLanguage: 'both',
      showTransliteration: false,

      setPreferredEditions: (editions: TafseerEdition[]) => {
        set({ preferredEditions: editions });
      },

      addEdition: (edition: TafseerEdition) => {
        set((state) => {
          if (state.preferredEditions.includes(edition)) {
            return state;
          }
          return { preferredEditions: [...state.preferredEditions, edition] };
        });
      },

      removeEdition: (edition: TafseerEdition) => {
        set((state) => ({
          preferredEditions: state.preferredEditions.filter((e) => e !== edition),
        }));
      },

      setPreferredLanguage: (lang: 'ar' | 'en' | 'both') => {
        set({ preferredLanguage: lang });
      },

      toggleTransliteration: () => {
        set((state) => ({ showTransliteration: !state.showTransliteration }));
      },

      resetToDefaults: () => {
        set({
          preferredEditions: DEFAULT_EDITIONS,
          preferredLanguage: 'both',
          showTransliteration: false,
        });
      },
    }),
    {
      name: 'tadabbur-tafseer',
    }
  )
);

/**
 * Get edition display name based on current language
 */
export function getEditionName(edition: TafseerEdition, lang: 'ar' | 'en'): string {
  const meta = EDITION_METADATA[edition];
  return lang === 'ar' ? meta.nameAr : meta.nameEn;
}

/**
 * Get edition author based on current language
 */
export function getEditionAuthor(edition: TafseerEdition, lang: 'ar' | 'en'): string {
  const meta = EDITION_METADATA[edition];
  return lang === 'ar' ? meta.authorAr : meta.authorEn;
}

/**
 * Filter editions by language
 */
export function getEditionsByLanguage(lang: 'ar' | 'en'): TafseerEdition[] {
  return (Object.keys(EDITION_METADATA) as TafseerEdition[]).filter(
    (edition) => EDITION_METADATA[edition].language === lang
  );
}

/**
 * Get tafsir-only editions (excludes translations)
 */
export function getTafsirEditions(): TafseerEdition[] {
  return (Object.keys(EDITION_METADATA) as TafseerEdition[]).filter(
    (edition) => EDITION_METADATA[edition].type === 'tafsir'
  );
}
