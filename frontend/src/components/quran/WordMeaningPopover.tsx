/**
 * WordMeaningPopover — hover-to-reveal morphology + meaning for any Quranic word.
 *
 * Shows: Arabic word, root (جذر), pattern (وزن), POS (نوع الكلمة),
 *        English gloss, Arabic meaning, source attribution.
 *
 * Data comes from /vocabulary/by-ref (sura:aya:word_position).
 * If the position is not yet in the DB the popover shows a safe-refusal notice.
 *
 * RTL/LTR policy:
 *   Arabic content → dir="rtl"
 *   English content → dir="ltr"
 *   Never mix in a single dir-less container.
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { BookOpen, X, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { vocabularyApi, VocabularyResponse } from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WordMeaningPopoverProps {
  /** Arabic word text (with diacritics from quran_uthmani) */
  word: string;
  /** 1-indexed surah number */
  sura: number;
  /** 1-indexed ayah number */
  aya: number;
  /** 1-indexed word position within the ayah */
  position: number;
  className?: string;
}

type PopoverState = 'idle' | 'loading' | 'found' | 'not_found' | 'error';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WordMeaningPopover({
  word,
  sura,
  aya,
  position,
  className,
}: WordMeaningPopoverProps) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [open, setOpen] = useState(false);
  const [state, setState] = useState<PopoverState>('idle');
  const [data, setData] = useState<VocabularyResponse | null>(null);

  const containerRef = useRef<HTMLSpanElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const fetchedKey = useRef<string>('');

  const key = `${sura}:${aya}:${position}`;

  const fetchMeaning = useCallback(async () => {
    if (fetchedKey.current === key) return; // already fetched
    setState('loading');
    try {
      const res = await vocabularyApi.byRef(sura, aya, position);
      fetchedKey.current = key;
      setData(res.data);
      setState(res.data.status === 'found' ? 'found' : 'not_found');
    } catch {
      setState('error');
    }
  }, [sura, aya, position, key]);

  // Open on click (touch-friendly) or hover (desktop)
  const handleOpen = useCallback(() => {
    setOpen(true);
    fetchMeaning();
  }, [fetchMeaning]);

  const handleClose = useCallback(() => setOpen(false), []);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function onOutsideClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node) &&
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node)
      ) {
        handleClose();
      }
    }
    document.addEventListener('mousedown', onOutsideClick);
    return () => document.removeEventListener('mousedown', onOutsideClick);
  }, [open, handleClose]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') handleClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, handleClose]);

  return (
    <span className="relative inline-block" ref={containerRef}>
      {/* Clickable / hoverable word */}
      <span
        role="button"
        tabIndex={0}
        aria-haspopup="true"
        aria-expanded={open}
        onClick={handleOpen}
        onMouseEnter={handleOpen}
        onMouseLeave={() => {
          // Delay close to allow moving pointer to popover
          setTimeout(() => {
            if (
              popoverRef.current &&
              !popoverRef.current.matches(':hover') &&
              containerRef.current &&
              !containerRef.current.matches(':hover')
            ) {
              handleClose();
            }
          }, 150);
        }}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleOpen(); }}
        className={clsx(
          'cursor-pointer rounded px-0.5 transition-colors duration-150',
          'hover:bg-teal-100 hover:text-teal-900',
          'focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-1',
          open && 'bg-teal-100 text-teal-900',
          className,
        )}
      >
        {word}
      </span>

      {/* Popover */}
      {open && (
        <div
          ref={popoverRef}
          role="tooltip"
          onMouseLeave={() => {
            if (
              containerRef.current &&
              !containerRef.current.matches(':hover')
            ) {
              handleClose();
            }
          }}
          className={clsx(
            'absolute z-50 w-72 rounded-xl shadow-lg border border-gray-200 bg-white',
            'top-full mt-1',
            // Position left or right depending on RTL to avoid overflow
            isRtl ? 'right-0' : 'left-0',
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-teal-50 rounded-t-xl">
            <span dir="rtl" className="font-arabic text-lg font-bold text-teal-900">
              {word}
            </span>
            <button
              onClick={handleClose}
              aria-label="Close"
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body */}
          <div className="p-4 space-y-3 text-sm">
            {state === 'loading' && (
              <div className="flex items-center justify-center py-3 text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                <span>Loading…</span>
              </div>
            )}

            {state === 'error' && (
              <p className="text-red-500 text-xs text-center">
                {isRtl ? 'حدث خطأ. حاول مجدداً.' : 'Error loading word data.'}
              </p>
            )}

            {state === 'not_found' && (
              <p className={clsx('text-gray-400 text-xs leading-relaxed', isRtl && 'text-right font-arabic')}
                 dir={isRtl ? 'rtl' : 'ltr'}>
                {isRtl
                  ? 'لا يتوفر مصدر موثوق لهذه المفردة حالياً.'
                  : 'No verified source available for this word yet.'}
              </p>
            )}

            {state === 'found' && data && (
              <>
                {/* Morphology row */}
                <div className="grid grid-cols-3 gap-2">
                  {data.root && (
                    <MorphTag label={isRtl ? 'الجذر' : 'Root'} value={data.root} arabic />
                  )}
                  {data.pattern && (
                    <MorphTag label={isRtl ? 'الوزن' : 'Pattern'} value={data.pattern} arabic />
                  )}
                  {data.pos_tag && (
                    <MorphTag label={isRtl ? 'النوع' : 'POS'} value={data.pos_tag} arabic />
                  )}
                </div>

                {/* English meaning */}
                {data.meaning_en && (
                  <div>
                    <span className="text-xs text-gray-400 uppercase tracking-wide">
                      {isRtl ? 'المعنى بالإنجليزية' : 'Meaning'}
                    </span>
                    <p dir="ltr" className="text-gray-800 font-medium mt-0.5">
                      {data.meaning_en}
                    </p>
                  </div>
                )}

                {/* Arabic meaning */}
                {data.meaning_ar && (
                  <div>
                    <span className="text-xs text-gray-400 uppercase tracking-wide" dir="ltr">
                      {isRtl ? 'المعنى العربي' : 'Arabic meaning'}
                    </span>
                    <p dir="rtl" className="font-arabic text-gray-800 font-medium mt-0.5 text-right">
                      {data.meaning_ar}
                    </p>
                  </div>
                )}

                {/* Source */}
                <div className="pt-1 border-t border-gray-100">
                  <div className="flex items-center gap-1.5 text-xs text-gray-400">
                    <BookOpen className="w-3.5 h-3.5 shrink-0" />
                    <span dir="ltr">
                      {data.source_title_en || data.source_id || 'Verified source'}
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: morphology tag chip
// ---------------------------------------------------------------------------

function MorphTag({
  label,
  value,
  arabic = false,
}: {
  label: string;
  value: string;
  arabic?: boolean;
}) {
  return (
    <div className="flex flex-col items-center bg-teal-50 border border-teal-100 rounded-lg px-2 py-1.5 min-w-0">
      <span className="text-xs text-teal-500 truncate w-full text-center">{label}</span>
      <span
        dir={arabic ? 'rtl' : 'ltr'}
        className={clsx(
          'font-semibold text-teal-800 text-sm truncate w-full text-center',
          arabic && 'font-arabic',
        )}
      >
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// VerseText — renders a verse as individually hoverable words
// ---------------------------------------------------------------------------

interface VerseTextProps {
  text: string;
  sura: number;
  aya: number;
  className?: string;
}

/**
 * Splits verse text on whitespace and wraps each word in a WordMeaningPopover.
 *
 * The end-of-verse circle marker (U+06DD ۝ and similar) is rendered as-is
 * without a popover since it is not a lexical word.
 */
export function VerseText({ text, sura, aya, className }: VerseTextProps) {
  const words = text.split(/(\s+)/).filter(Boolean);

  return (
    <span dir="rtl" className={clsx('font-arabic', className)}>
      {words.map((token, idx) => {
        // Whitespace tokens — pass through
        if (/^\s+$/.test(token)) {
          return <span key={idx}>{token}</span>;
        }
        // Verse end marker or punctuation-only tokens — no popover
        if (/^[۝؀-؅؟،؛…\s]+$/.test(token)) {
          return <span key={idx}>{token}</span>;
        }

        // Word position: count non-whitespace, non-marker tokens before this one
        const wordPosition = words
          .slice(0, idx)
          .filter(t => !/^\s+$/.test(t) && !/^[۝؀-؅؟،؛…]+$/.test(t))
          .length + 1;

        return (
          <WordMeaningPopover
            key={idx}
            word={token}
            sura={sura}
            aya={aya}
            position={wordPosition}
          />
        );
      })}
    </span>
  );
}
