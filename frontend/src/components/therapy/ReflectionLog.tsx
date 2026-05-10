import { useState } from 'react';
import { BookMarked, ChevronDown, ChevronUp, Clock, Trash2, Save } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import type { ReflectionEntry } from '../../types/therapy';
import clsx from 'clsx';

interface ReflectionLogProps {
  entries: ReflectionEntry[];
  currentSessionId: string | null;
  onSaveReflection: (sessionId: string, text: string) => Promise<void>;
  onDeleteEntry: (sessionId: string) => void;
}

function formatRelativeTime(timestamp: number, language: string): string {
  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (language === 'ar') {
    if (minutes < 2) return 'الآن';
    if (minutes < 60) return `منذ ${minutes} دقيقة`;
    if (hours < 24) return `منذ ${hours} ساعة`;
    return `منذ ${days} يوم`;
  }
  if (minutes < 2) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

const EMOTION_LABEL_MAP: Record<string, { en: string; ar: string }> = {
  anxiety:     { en: 'Anxiety', ar: 'قلق' },
  sadness:     { en: 'Sadness', ar: 'حزن' },
  grief:       { en: 'Grief', ar: 'حزن شديد' },
  fear:        { en: 'Fear', ar: 'خوف' },
  loneliness:  { en: 'Loneliness', ar: 'وحدة' },
  hopelessness:{ en: 'Hopelessness', ar: 'يأس' },
  anger:       { en: 'Anger', ar: 'غضب' },
  stress:      { en: 'Stress', ar: 'ضغط' },
  guilt:       { en: 'Guilt', ar: 'ذنب' },
  doubt:       { en: 'Doubt', ar: 'شك' },
  gratitude:   { en: 'Gratitude', ar: 'شكر' },
  general:     { en: 'General', ar: 'عام' },
};

export function ReflectionLog({
  entries,
  currentSessionId,
  onSaveReflection,
  onDeleteEntry,
}: ReflectionLogProps) {
  const { language } = useLanguageStore();
  const [open, setOpen] = useState(false);
  const [draftText, setDraftText] = useState('');
  const [saving, setSaving] = useState(false);
  const isRtl = language === 'ar';

  const handleSave = async () => {
    if (!currentSessionId || draftText.trim().length < 1 || saving) return;
    setSaving(true);
    try {
      await onSaveReflection(currentSessionId, draftText.trim());
      setDraftText('');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
      >
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <BookMarked className="w-4 h-4 text-emerald-500" />
          <span className={clsx('font-semibold text-gray-700 text-sm', isRtl && 'font-arabic')}>
            {t('therapy_reflection_log', language)}
          </span>
          {entries.length > 0 && (
            <span className="text-xs bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded-full font-medium">
              {entries.length}
            </span>
          )}
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>

      {open && (
        <div className="border-t border-gray-100 px-5 py-4 space-y-4">
          {/* Write reflection for current session */}
          {currentSessionId && (
            <div>
              <p className={clsx('text-xs text-gray-500 mb-2', isRtl && 'font-arabic text-right')}>
                {t('therapy_write_reflection', language)}
              </p>
              <textarea
                value={draftText}
                onChange={e => setDraftText(e.target.value)}
                dir={isRtl ? 'rtl' : 'ltr'}
                placeholder={t('therapy_reflection_placeholder', language)}
                rows={3}
                className={clsx(
                  'w-full rounded-xl border border-gray-200 p-3 text-sm resize-none',
                  'focus:outline-none focus:ring-2 focus:ring-emerald-300',
                  'text-gray-700 placeholder-gray-400',
                  isRtl && 'font-arabic text-right',
                )}
              />
              <button
                onClick={handleSave}
                disabled={draftText.trim().length < 1 || saving}
                className={clsx(
                  'mt-2 flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium',
                  'bg-emerald-500 hover:bg-emerald-600 text-white transition-colors',
                  'disabled:opacity-40 disabled:cursor-not-allowed',
                  isRtl && 'flex-row-reverse font-arabic',
                )}
              >
                <Save className="w-3.5 h-3.5" />
                {saving ? t('therapy_saving', language) : t('therapy_save_reflection', language)}
              </button>
            </div>
          )}

          {/* Past entries */}
          {entries.length === 0 ? (
            <p className={clsx('text-xs text-gray-400 text-center py-2', isRtl && 'font-arabic')}>
              {t('therapy_no_reflections', language)}
            </p>
          ) : (
            <div className="space-y-3">
              {entries.map(entry => {
                const label = EMOTION_LABEL_MAP[entry.emotion] ?? { en: entry.emotion, ar: entry.emotion };
                return (
                  <div
                    key={entry.session_id}
                    className="p-3 bg-gray-50 rounded-xl border border-gray-100"
                  >
                    <div className={clsx('flex items-center justify-between mb-2', isRtl && 'flex-row-reverse')}>
                      <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
                        <span className="text-xs bg-rose-100 text-rose-600 px-2 py-0.5 rounded-full font-medium">
                          {isRtl ? label.ar : label.en}
                        </span>
                        {entry.verses.length > 0 && (
                          <span className="text-xs text-gray-400 font-mono">
                            {entry.verses.slice(0, 2).join(', ')}
                          </span>
                        )}
                      </div>
                      <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <Clock className="w-3 h-3" />
                          {formatRelativeTime(entry.timestamp, language)}
                        </span>
                        <button
                          onClick={() => onDeleteEntry(entry.session_id)}
                          className="text-gray-300 hover:text-red-400 transition-colors"
                          title="Remove entry"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    {entry.reflection && (
                      <p className={clsx('text-sm text-gray-600 leading-relaxed', isRtl && 'font-arabic text-right')}>
                        {entry.reflection}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
