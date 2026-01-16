import { MessageCircle, ArrowRight } from 'lucide-react';
import clsx from 'clsx';

interface FollowUpChipsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  language: 'ar' | 'en';
  disabled?: boolean;
}

export function FollowUpChips({ suggestions, onSelect, language, disabled }: FollowUpChipsProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-gray-500 flex items-center gap-1.5">
        <MessageCircle className="w-3.5 h-3.5" />
        {language === 'ar' ? 'أسئلة متابعة مقترحة' : 'Suggested follow-up questions'}
      </h4>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(suggestion)}
            disabled={disabled}
            className={clsx(
              'group inline-flex items-center gap-2 px-3 py-2 text-sm',
              'bg-white border border-gray-200 rounded-full',
              'hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700',
              'transition-all duration-200',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          >
            <span className="max-w-xs truncate">{suggestion}</span>
            <ArrowRight className={clsx(
              'w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity',
              language === 'ar' && 'rotate-180'
            )} />
          </button>
        ))}
      </div>
    </div>
  );
}
