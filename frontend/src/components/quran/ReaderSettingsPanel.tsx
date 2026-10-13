/**
 * Reader settings: Arabic script, text size, translation editions, auto-scroll.
 *
 * Every choice persists through useReaderSettingsStore.
 */
import { useMemo } from 'react';
import clsx from 'clsx';
import { Minus, Plus, X } from 'lucide-react';
import {
  useReaderSettingsStore,
  effectiveTranslationKeys,
  MAX_TRANSLATIONS,
  FONT_SCALE_MIN,
  FONT_SCALE_MAX,
  FONT_SCALE_STEP,
  type QuranScript,
} from '../../stores/readerSettingsStore';
import { useTranslationEditions, languageName } from './VerseTranslations';
import type { TranslationEdition } from '../../lib/api';
import type { Language } from '../../i18n/translations';
import { ReaderThemePicker } from './ReaderThemePicker';

interface ReaderSettingsPanelProps {
  language: Language;
  onClose: () => void;
}

export function ReaderSettingsPanel({ language, onClose }: ReaderSettingsPanelProps) {
  const ar = language === 'ar';
  const {
    script, setScript, fontScale, setFontScale, translationKeys,
    toggleTranslation, clearTranslations, autoScroll, setAutoScroll,
  } = useReaderSettingsStore();
  const selected = effectiveTranslationKeys(translationKeys, language);
  const { data: editions, isLoading, isError } = useTranslationEditions();

  // Group by language: the UI language first, then English, then alphabetical.
  const groups = useMemo(() => {
    const byLang = new Map<string, TranslationEdition[]>();
    for (const e of editions ?? []) {
      byLang.set(e.language, [...(byLang.get(e.language) ?? []), e]);
    }
    const rank = (code: string) => (code === language ? 0 : code === 'en' ? 1 : 2);
    return [...byLang.entries()].sort(
      ([a], [b]) => rank(a) - rank(b) || languageName(a, 'en').localeCompare(languageName(b, 'en')),
    );
  }, [editions, language]);

  const scripts: { id: QuranScript; ar: string; en: string; hint: { ar: string; en: string } }[] = [
    { id: 'imlaei', ar: 'إملائي', en: 'Imla\'i', hint: { ar: 'الرسم الإملائي الحديث', en: 'Modern simplified spelling' } },
    { id: 'uthmani', ar: 'عثماني', en: 'Uthmani', hint: { ar: 'رسم مصحف المدينة', en: 'Madinah Mushaf script' } },
  ];

  return (
    <section
      aria-label={ar ? 'إعدادات القراءة' : 'Reader settings'}
      dir={ar ? 'rtl' : 'ltr'}
      className={clsx('card mb-6 space-y-5', ar && 'font-arabic')}
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{ar ? 'إعدادات القراءة' : 'Reader settings'}</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label={ar ? 'إغلاق' : 'Close'}
          className="p-2 rounded-lg text-gray-500 hover:bg-gray-100"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Theme */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">{ar ? 'سمة القراءة' : 'Reading theme'}</h3>
        <ReaderThemePicker language={language} />
      </div>

      {/* Script */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">{ar ? 'الرسم' : 'Script'}</h3>
        <div className="grid grid-cols-2 gap-2" role="radiogroup">
          {scripts.map((s) => (
            <button
              key={s.id}
              type="button"
              role="radio"
              aria-checked={script === s.id}
              onClick={() => setScript(s.id)}
              className={clsx(
                'rounded-xl border px-3 py-2 text-start transition-colors',
                script === s.id
                  ? 'border-primary-500 bg-primary-50 text-primary-800'
                  : 'border-gray-200 hover:border-gray-300',
              )}
            >
              <span className="block text-sm font-semibold">{ar ? s.ar : s.en}</span>
              <span className="block text-xs text-gray-500">{ar ? s.hint.ar : s.hint.en}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Text size */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">{ar ? 'حجم الخط' : 'Arabic text size'}</h3>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setFontScale(fontScale - FONT_SCALE_STEP)}
            disabled={fontScale <= FONT_SCALE_MIN}
            aria-label={ar ? 'تصغير الخط' : 'Smaller text'}
            className="p-2 rounded-lg border border-gray-200 disabled:opacity-40"
          >
            <Minus className="w-4 h-4" />
          </button>
          <input
            type="range"
            min={FONT_SCALE_MIN}
            max={FONT_SCALE_MAX}
            step={FONT_SCALE_STEP}
            value={fontScale}
            onChange={(e) => setFontScale(parseFloat(e.target.value))}
            aria-label={ar ? 'حجم الخط' : 'Arabic text size'}
            className="flex-1 accent-primary-600"
          />
          <button
            type="button"
            onClick={() => setFontScale(fontScale + FONT_SCALE_STEP)}
            disabled={fontScale >= FONT_SCALE_MAX}
            aria-label={ar ? 'تكبير الخط' : 'Larger text'}
            className="p-2 rounded-lg border border-gray-200 disabled:opacity-40"
          >
            <Plus className="w-4 h-4" />
          </button>
          <span className="w-12 text-center text-sm tabular-nums" dir="ltr">
            {Math.round(fontScale * 100)}%
          </span>
        </div>
      </div>

      {/* Auto-scroll */}
      <label className="flex items-center justify-between gap-3 cursor-pointer">
        <span className="text-sm font-medium text-gray-700">
          {ar ? 'متابعة الآية المتلوة تلقائيًا' : 'Follow the verse being recited'}
        </span>
        <input
          type="checkbox"
          checked={autoScroll}
          onChange={(e) => setAutoScroll(e.target.checked)}
          className="w-5 h-5 accent-primary-600"
        />
      </label>

      {/* Translations */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-700">
            {ar ? 'ترجمة المعاني' : 'Translations'}{' '}
            <span className="text-xs text-gray-400" dir="ltr">
              ({selected.length}/{MAX_TRANSLATIONS})
            </span>
          </h3>
          {selected.length > 0 && (
            <button type="button" onClick={clearTranslations} className="text-xs text-primary-600 hover:underline">
              {ar ? 'العربية فقط' : 'Arabic only'}
            </button>
          )}
        </div>
        <p className="text-xs text-gray-500 mb-3">
          {ar
            ? 'تظهر الترجمات في عرض القائمة. المصدر: QuranEnc.com، تُعرض كما نُشرت دون تعديل.'
            : 'Shown in List view. Source: QuranEnc.com, displayed exactly as published.'}
        </p>

        {isLoading && <div className="h-24 animate-pulse bg-gray-100 rounded-xl" />}
        {isError && (
          <p className="text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
            {ar ? 'تعذّر تحميل قائمة الترجمات.' : 'Could not load the translation list.'}
          </p>
        )}
        {!isLoading && !isError && groups.length === 0 && (
          <p className="text-sm text-gray-500">{ar ? 'لا توجد ترجمات متاحة.' : 'No translations available.'}</p>
        )}

        <div className="max-h-72 overflow-y-auto space-y-3 pe-1">
          {groups.map(([lang, list]) => (
            <fieldset key={lang}>
              <legend className="text-xs font-semibold text-gray-500 mb-1">{languageName(lang, language)}</legend>
              <div className="space-y-1">
                {list.map((e) => {
                  const checked = selected.includes(e.key);
                  return (
                    <label
                      key={e.key}
                      className={clsx(
                        'flex items-start gap-2 rounded-lg px-2 py-1.5 cursor-pointer',
                        checked ? 'bg-primary-50' : 'hover:bg-gray-50',
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleTranslation(e.key, selected)}
                        className="mt-1 w-4 h-4 accent-primary-600"
                      />
                      <span className="text-sm" dir="ltr">
                        {e.translator_name ?? e.title}
                        <span className="block text-[11px] text-gray-400">
                          {e.title} · v{e.version}
                        </span>
                      </span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          ))}
        </div>
      </div>
    </section>
  );
}
