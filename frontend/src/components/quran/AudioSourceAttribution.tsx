/**
 * Credit line for recitation audio: the site the verse file was streamed (or
 * downloaded for offline use) from. Sources mirror backend audio_service.py:
 * everyayah.com first, cdn.islamic.network (alquran.cloud) as the fallback.
 */
import clsx from 'clsx';
import type { Language } from '../../i18n/translations';

const AUDIO_SOURCE_SITES: Record<string, { label: string; href: string }> = {
  'everyayah.com': { label: 'everyayah.com', href: 'https://everyayah.com' },
  'cdn.islamic.network': { label: 'islamic.network (alquran.cloud)', href: 'https://alquran.cloud/cdn' },
};

/** Host of a recitation URL, or null for a non-http source. */
export function audioHost(url: string | undefined | null): string | null {
  if (!url) return null;
  try {
    const u = new URL(url);
    return u.protocol.startsWith('http') ? u.hostname : null;
  } catch {
    return null;
  }
}

export function AudioSourceAttribution({
  host,
  language,
  className,
}: {
  /** Host of the file now loaded; null before anything loads (primary source shown). */
  host: string | null;
  language: Language;
  className?: string;
}) {
  const ar = language === 'ar';
  const key = host ?? 'everyayah.com';
  const site = AUDIO_SOURCE_SITES[key];
  return (
    <p
      className={clsx('text-[11px] text-gray-500', ar && 'font-arabic', className)}
      dir={ar ? 'rtl' : 'ltr'}
      lang={language}
      data-testid="audio-attribution"
    >
      {ar ? 'مصدر التلاوة: ' : 'Recitation audio: '}
      {site ? (
        <a href={site.href} target="_blank" rel="noopener noreferrer" dir="ltr" className="underline hover:text-primary-600">
          {site.label}
        </a>
      ) : (
        <bdi dir="ltr">{key}</bdi>
      )}
    </p>
  );
}
