import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Persona =
  | 'new_muslim'
  | 'student'
  | 'researcher'
  | 'parent'
  | 'arabic_learner'
  | 'memorizer';

export const PERSONA_META: Record<
  Persona,
  { labelAr: string; labelEn: string; descAr: string; descEn: string; emoji: string }
> = {
  new_muslim: {
    emoji: '🌙',
    labelAr: 'مسلم جديد',
    labelEn: 'New Muslim',
    descAr: 'أريد تعلّم القرآن والإسلام من البداية',
    descEn: 'I am learning the Quran and Islam from the beginning',
  },
  student: {
    emoji: '📖',
    labelAr: 'طالب علم',
    labelEn: 'Student',
    descAr: 'أدرس علوم القرآن والتفسير',
    descEn: 'I study Quranic sciences and tafsir',
  },
  researcher: {
    emoji: '🔬',
    labelAr: 'باحث أكاديمي',
    labelEn: 'Researcher',
    descAr: 'أبحث في الدراسات القرآنية أكاديمياً',
    descEn: 'I conduct academic research in Quranic studies',
  },
  parent: {
    emoji: '👨‍👩‍👧',
    labelAr: 'ولي أمر',
    labelEn: 'Parent',
    descAr: 'أريد تعليم أطفالي القرآن الكريم',
    descEn: 'I want to teach my children the Quran',
  },
  arabic_learner: {
    emoji: '🗣️',
    labelAr: 'متعلّم اللغة العربية',
    labelEn: 'Arabic Learner',
    descAr: 'أتعلّم اللغة العربية من خلال القرآن',
    descEn: 'I am learning Arabic through the Quran',
  },
  memorizer: {
    emoji: '🧠',
    labelAr: 'حافظ القرآن',
    labelEn: 'Memorizer',
    descAr: 'أحفظ القرآن الكريم أو أراجعه',
    descEn: 'I am memorizing or reviewing the Quran',
  },
};

interface PersonaState {
  persona: Persona | null;
  hasChosen: boolean;
  setPersona: (p: Persona) => void;
  skipOnboarding: () => void;
  clearPersona: () => void;
}

export const usePersonaStore = create<PersonaState>()(
  persist(
    (set) => ({
      persona: null,
      hasChosen: false,

      setPersona: (p) => set({ persona: p, hasChosen: true }),

      skipOnboarding: () => set({ hasChosen: true }),

      clearPersona: () => set({ persona: null, hasChosen: false }),
    }),
    { name: 'tadabbur-persona' }
  )
);
