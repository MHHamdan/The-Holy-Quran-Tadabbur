/**
 * Accessible modal dialog.
 *
 * - role="dialog" aria-modal="true", labelled by the caller's heading id
 * - moves focus into the dialog on open (first focusable, or the panel)
 * - traps Tab / Shift+Tab inside the panel
 * - closes on Escape and on a backdrop click
 * - restores focus to the element that was focused before opening
 * - locks body scroll while open
 *
 * `variant="sheet"` docks the panel to the bottom on phones (bottom sheet) and
 * centres it from the sm breakpoint up.
 */
import { ReactNode, useEffect, useRef } from 'react';
import clsx from 'clsx';

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  /** id of the element that names the dialog (usually its <h2>) */
  labelledBy?: string;
  /** used when there is no visible heading */
  ariaLabel?: string;
  dir?: 'rtl' | 'ltr';
  variant?: 'center' | 'sheet';
  className?: string;
  children: ReactNode;
}

export function Dialog({
  open,
  onClose,
  labelledBy,
  ariaLabel,
  dir,
  variant = 'center',
  className,
  children,
}: DialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;

    const first = panel?.querySelector<HTMLElement>('[data-autofocus]') ?? panel?.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? panel)?.focus();

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onCloseRef.current();
        return;
      }
      if (e.key !== 'Tab' || !panel) return;
      const nodes = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
        (n) => n.offsetParent !== null || n === document.activeElement,
      );
      if (nodes.length === 0) {
        e.preventDefault();
        panel.focus();
        return;
      }
      const firstNode = nodes[0];
      const lastNode = nodes[nodes.length - 1];
      if (e.shiftKey && (document.activeElement === firstNode || document.activeElement === panel)) {
        e.preventDefault();
        lastNode.focus();
      } else if (!e.shiftKey && document.activeElement === lastNode) {
        e.preventDefault();
        firstNode.focus();
      }
    }

    document.addEventListener('keydown', onKeyDown, true);
    return () => {
      document.removeEventListener('keydown', onKeyDown, true);
      document.body.style.overflow = previousOverflow;
      if (opener && document.contains(opener)) opener.focus();
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className={clsx(
        'fixed inset-0 z-[60] flex p-0 sm:p-4',
        variant === 'sheet' ? 'items-end justify-center sm:items-center' : 'items-end justify-center p-4 sm:items-center',
      )}
    >
      <div className="fixed inset-0 bg-black/40" aria-hidden="true" onClick={onClose} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-label={labelledBy ? undefined : ariaLabel}
        tabIndex={-1}
        dir={dir}
        className={clsx(
          'relative z-10 w-full bg-white shadow-2xl outline-none',
          variant === 'sheet'
            ? 'max-h-[85vh] overflow-y-auto rounded-t-2xl sm:max-w-2xl sm:rounded-2xl safe-area-bottom'
            : 'max-w-md rounded-2xl',
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}
