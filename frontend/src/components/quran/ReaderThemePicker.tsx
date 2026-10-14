/**
 * Light / sepia / night reading theme swatches (persisted in reader settings).
 */
import clsx from 'clsx';
import { useReaderSettingsStore, type ReaderTheme } from '../../stores/readerSettingsStore';
import type { Language } from '../../i18n/translations';

const THEMES: { id: ReaderTheme; ar: string; en: string; swatch: string }[] = [
  { id: 'light', ar: 'فاتح', en: 'Light', swatch: 'bg-white border-gray-300 text-gray-900' },
  { id: 'sepia', ar: 'ورقي', en: 'Sepia', swatch: 'bg-[#f4ecd8] border-[#d9c7a0] text-[#3b2f1e]' },
  { id: 'night', ar: 'ليلي', en: 'Night', swatch: 'bg-[#0b1220] border-[#334155] text-slate-100' },
];

export function ReaderThemePicker({ language, compact = false }: { language: Language; compact?: boolean }) {
  const { theme, setTheme } = useReaderSettingsStore();
  const ar = language === 'ar';
  return (
    <div role="radiogroup" aria-label={ar ? 'سمة القراءة' : 'Reading theme'} className="flex gap-2">
      {THEMES.map((t) => (
        <button
          key={t.id}
          type="button"
          role="radio"
          aria-checked={theme === t.id}
          onClick={() => setTheme(t.id)}
          className={clsx(
            'rounded-xl border-2 font-semibold transition-shadow',
            compact ? 'px-2.5 py-1 text-xs' : 'flex-1 px-3 py-2 text-sm',
            t.swatch,
            theme === t.id && 'ring-2 ring-primary-500 ring-offset-1',
            ar && 'font-arabic',
          )}
        >
          {ar ? t.ar : t.en}
        </button>
      ))}
    </div>
  );
}
