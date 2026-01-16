import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, BookOpen, User, Scroll, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { TafsirExplanation } from '../../lib/api';

interface TafsirAccordionProps {
  tafsirBySources: Record<string, TafsirExplanation[]>;
  language: 'ar' | 'en';
}

export function TafsirAccordion({ tafsirBySources, language }: TafsirAccordionProps) {
  const sourceIds = Object.keys(tafsirBySources);

  // Auto-expand first source on mount
  const [expandedSource, setExpandedSource] = useState<string | null>(
    sourceIds.length > 0 ? sourceIds[0] : null
  );

  // Update expanded source if sources change
  useEffect(() => {
    if (sourceIds.length > 0 && !expandedSource) {
      setExpandedSource(sourceIds[0]);
    }
  }, [sourceIds, expandedSource]);

  if (sourceIds.length === 0) return null;

  const toggleSource = (sourceId: string) => {
    setExpandedSource(prev => prev === sourceId ? null : sourceId);
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <Scroll className="w-4 h-4 text-amber-600" />
        {language === 'ar' ? 'شروحات التفسير' : 'Tafsir Explanations'}
        <span className="text-xs font-normal text-gray-500">
          ({sourceIds.length} {language === 'ar' ? 'مصادر' : 'sources'})
        </span>
      </h3>

      <div className="space-y-2">
        {sourceIds.map((sourceId, index) => {
          const explanations = tafsirBySources[sourceId];
          const firstExplanation = explanations[0];
          const isExpanded = expandedSource === sourceId;
          const sourceName = language === 'ar'
            ? firstExplanation.source_name_ar
            : firstExplanation.source_name;

          return (
            <div
              key={sourceId}
              className={clsx(
                'rounded-xl border-2 transition-all duration-300 overflow-hidden',
                isExpanded
                  ? 'border-amber-300 bg-gradient-to-br from-amber-50 to-orange-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-amber-200 hover:shadow-sm'
              )}
            >
              {/* Header - always visible */}
              <button
                onClick={() => toggleSource(sourceId)}
                className="w-full px-4 py-3 flex items-center justify-between text-left"
              >
                <div className="flex items-center gap-3">
                  {/* Source icon with number */}
                  <div className={clsx(
                    'relative w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                    isExpanded ? 'bg-amber-200' : 'bg-gray-100'
                  )}>
                    <BookOpen className={clsx(
                      'w-5 h-5',
                      isExpanded ? 'text-amber-700' : 'text-gray-500'
                    )} />
                    <span className={clsx(
                      'absolute -top-1 -right-1 w-5 h-5 rounded-full text-xs font-bold flex items-center justify-center',
                      isExpanded ? 'bg-amber-500 text-white' : 'bg-gray-300 text-gray-700'
                    )}>
                      {index + 1}
                    </span>
                  </div>

                  <div className="min-w-0">
                    <span className={clsx(
                      'font-semibold block text-base truncate',
                      isExpanded ? 'text-amber-900' : 'text-gray-900'
                    )}>
                      {sourceName}
                    </span>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {firstExplanation.author_name && (
                        <span className="text-xs text-gray-500 flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {language === 'ar'
                            ? firstExplanation.author_name_ar || firstExplanation.author_name
                            : firstExplanation.author_name}
                        </span>
                      )}
                      <span className={clsx(
                        'text-xs px-2 py-0.5 rounded-full font-medium',
                        firstExplanation.era === 'classical'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-blue-100 text-blue-800'
                      )}>
                        {firstExplanation.era === 'classical'
                          ? (language === 'ar' ? 'تراثي' : 'Classical')
                          : (language === 'ar' ? 'معاصر' : 'Modern')}
                      </span>
                      {firstExplanation.methodology && (
                        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                          {firstExplanation.methodology}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 hidden sm:block">
                    {explanations.length} {language === 'ar' ? 'تفسير' : 'explanation'}
                    {explanations.length > 1 && (language === 'ar' ? 'ات' : 's')}
                  </span>
                  <div className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center transition-colors',
                    isExpanded ? 'bg-amber-200' : 'bg-gray-100'
                  )}>
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-amber-600" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-4 border-t border-amber-200">
                  {explanations.map((explanation, idx) => (
                    <div
                      key={idx}
                      className="pt-4"
                      dir={language === 'ar' ? 'rtl' : 'ltr'}
                    >
                      {/* Verse reference header */}
                      {explanation.verse_reference && (
                        <div className="flex items-center justify-between mb-3">
                          <Link
                            to={`/quran/${explanation.verse_reference.split(':')[0]}?aya=${explanation.verse_reference.split(':')[1]}&highlight=true`}
                            className="inline-flex items-center gap-2 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 px-3 py-1.5 rounded-lg transition-colors"
                          >
                            <BookOpen className="w-4 h-4" />
                            {language === 'ar' ? 'الآية' : 'Verse'} {explanation.verse_reference}
                            <ExternalLink className="w-3 h-3" />
                          </Link>
                        </div>
                      )}

                      {/* Tafsir content */}
                      <div className="bg-white rounded-lg p-4 border border-amber-100 shadow-inner">
                        <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap font-['Amiri',_serif]">
                          {explanation.explanation}
                        </p>
                      </div>

                      {/* Separator between explanations */}
                      {idx < explanations.length - 1 && (
                        <hr className="mt-4 border-amber-100" />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Hint to expand more */}
      {sourceIds.length > 1 && (
        <p className="text-xs text-gray-500 text-center mt-2">
          {language === 'ar'
            ? 'اضغط على أي مصدر للاطلاع على التفسير الكامل'
            : 'Click on any source to view the full explanation'}
        </p>
      )}
    </div>
  );
}
