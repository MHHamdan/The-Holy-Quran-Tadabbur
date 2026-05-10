import { useState } from 'react';
import { Send, Heart } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import clsx from 'clsx';

interface EmotionalInputPanelProps {
  onSubmit: (message: string) => void;
  loading: boolean;
}

const EXAMPLE_PROMPTS: { en: string; ar: string }[] = [
  { en: 'I feel overwhelmed with anxiety and worry', ar: 'أشعر بالقلق الشديد والتوتر' },
  { en: 'I am going through grief and loss', ar: 'أمر بتجربة الحزن والفقد' },
  { en: 'I feel lonely and disconnected', ar: 'أشعر بالوحدة والانقطاع' },
  { en: 'I have lost hope and feel hopeless', ar: 'فقدت الأمل وأشعر باليأس' },
  { en: 'I feel guilty about my past mistakes', ar: 'أشعر بالذنب على أخطاء الماضي' },
  { en: 'I am stressed and cannot cope', ar: 'أنا مجهد ولا أستطيع التحمل' },
];

export function EmotionalInputPanel({ onSubmit, loading }: EmotionalInputPanelProps) {
  const { language } = useLanguageStore();
  const [message, setMessage] = useState('');
  const isRtl = language === 'ar';

  const handleSubmit = () => {
    if (message.trim().length >= 3 && !loading) {
      onSubmit(message.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-rose-100 p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-full bg-rose-100 flex items-center justify-center">
          <Heart className="w-4 h-4 text-rose-500" />
        </div>
        <h3 className={clsx('font-semibold text-gray-800', isRtl && 'font-arabic')}>
          {t('therapy_share_prompt', language)}
        </h3>
      </div>

      <textarea
        value={message}
        onChange={e => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        dir={language === 'ar' ? 'rtl' : 'ltr'}
        placeholder={t('therapy_input_placeholder', language)}
        rows={4}
        className={clsx(
          'w-full rounded-xl border border-gray-200 p-4 resize-none',
          'focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-transparent',
          'text-gray-700 placeholder-gray-400 text-sm',
          isRtl && 'font-arabic text-right',
        )}
      />

      <div className="flex items-center justify-between mt-3">
        <span className={clsx('text-xs text-gray-400', isRtl && 'font-arabic')}>
          {t('therapy_ctrl_enter', language)}
        </span>
        <button
          onClick={handleSubmit}
          disabled={message.trim().length < 3 || loading}
          className={clsx(
            'flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm',
            'bg-rose-500 hover:bg-rose-600 text-white transition-colors',
            'disabled:opacity-40 disabled:cursor-not-allowed',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          <Send className="w-4 h-4" />
          {loading ? t('therapy_seeking', language) : t('therapy_seek_guidance', language)}
        </button>
      </div>

      {/* Example prompts */}
      <div className="mt-5 pt-4 border-t border-gray-100">
        <p className={clsx('text-xs text-gray-500 mb-2', isRtl && 'font-arabic text-right')}>
          {t('therapy_examples', language)}
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              onClick={() => setMessage(prompt[language])}
              className={clsx(
                'px-3 py-1.5 rounded-full text-xs border border-rose-200',
                'text-rose-600 hover:bg-rose-50 transition-colors',
                isRtl && 'font-arabic',
              )}
            >
              {prompt[language]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
