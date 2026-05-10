import { useLanguageStore } from '../../stores/languageStore';
import type { HealingTheme } from '../../types/therapy';
import clsx from 'clsx';

interface HealingThemeSelectorProps {
  themes: HealingTheme[];
  selectedTheme: string | null;
  onSelect: (key: string) => void;
  loading: boolean;
}

const THEME_STYLES: Record<string, { bg: string; text: string; border: string; activeBg: string }> = {
  mercy:      { bg: 'bg-rose-50',   text: 'text-rose-700',   border: 'border-rose-200',   activeBg: 'bg-rose-500' },
  patience:   { bg: 'bg-amber-50',  text: 'text-amber-700',  border: 'border-amber-200',  activeBg: 'bg-amber-500' },
  hope:       { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200', activeBg: 'bg-yellow-500' },
  forgiveness:{ bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200',  activeBg: 'bg-green-500' },
  gratitude:  { bg: 'bg-teal-50',   text: 'text-teal-700',   border: 'border-teal-200',   activeBg: 'bg-teal-500' },
  healing:    { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200',   activeBg: 'bg-blue-500' },
  trust:      { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200', activeBg: 'bg-indigo-500' },
  strength:   { bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200', activeBg: 'bg-violet-500' },
};

const THEME_EMOJI: Record<string, string> = {
  mercy: '🤲',
  patience: '⚓',
  hope: '🌅',
  forgiveness: '🕊️',
  gratitude: '⭐',
  healing: '💧',
  trust: '🛡️',
  strength: '⚡',
};

export function HealingThemeSelector({ themes, selectedTheme, onSelect, loading }: HealingThemeSelectorProps) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {themes.map(theme => {
        const style = THEME_STYLES[theme.key] ?? THEME_STYLES.mercy;
        const isActive = selectedTheme === theme.key;

        return (
          <button
            key={theme.key}
            onClick={() => !loading && onSelect(theme.key)}
            disabled={loading}
            title={isRtl ? theme.desc_ar : theme.desc_en}
            className={clsx(
              'flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all',
              'hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed',
              isActive
                ? `${style.activeBg} text-white border-transparent shadow-sm`
                : `${style.bg} ${style.text} ${style.border} hover:${style.activeBg} hover:text-white hover:border-transparent`,
            )}
          >
            <span className="text-lg leading-none">{THEME_EMOJI[theme.key] ?? '✨'}</span>
            <span className={clsx('text-xs font-semibold', isRtl && 'font-arabic')}>
              {isRtl ? theme.ar : theme.en}
            </span>
          </button>
        );
      })}
    </div>
  );
}
