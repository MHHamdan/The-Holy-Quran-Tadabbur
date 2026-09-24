import clsx from 'clsx';
import { ShieldCheck, ShieldPlus, ShieldAlert, ShieldX, Clock, ExternalLink } from 'lucide-react';
import { isSourceDisplayBlocked, type ReliabilityLevel, type Source } from '../../data/sourceRegistry';
import { t } from '../../i18n/translations';

interface SourceBadgeProps {
  reliabilityLevel: ReliabilityLevel;
  compact?: boolean;
  className?: string;
  language?: 'ar' | 'en';
}

const LEVEL_CONFIG: Record<ReliabilityLevel, {
  label: string;
  labelAr: string;
  icon: typeof ShieldCheck;
  classes: string;
}> = {
  canonical: {
    // ShieldPlus, not ShieldCheck: compact mode renders the icon alone, so
    // sharing a glyph with `verified` left the two distinguishable by colour
    // only — a WCAG 1.4.1 failure, and `title` is not an accessible substitute.
    label: 'Canonical',
    labelAr: 'متواتر',
    icon: ShieldPlus,
    classes: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  verified: {
    label: 'Verified',
    labelAr: 'موثق',
    icon: ShieldCheck,
    classes: 'bg-blue-50 text-blue-700 border-blue-200',
  },
  supporting: {
    label: 'Supporting',
    labelAr: 'مساند',
    icon: ShieldAlert,
    classes: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  experimental: {
    label: 'Experimental',
    labelAr: 'تجريبي',
    icon: ShieldX,
    classes: 'bg-red-50 text-red-700 border-red-200',
  },
};

export function SourceBadge({ reliabilityLevel, compact = false, className, language = 'en' }: SourceBadgeProps) {
  const config = LEVEL_CONFIG[reliabilityLevel];
  const Icon = config.icon;
  const label = language === 'ar' ? config.labelAr : config.label;

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 border rounded-full font-medium',
        compact ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-0.5 text-xs',
        config.classes,
        className,
      )}
      title={label}
    >
      <Icon className={compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} aria-hidden="true" />
      {compact ? <span className="sr-only">{label}</span> : <span>{label}</span>}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Full source attribution card
// ---------------------------------------------------------------------------

interface SourceAttributionProps {
  source: Source;
  language?: 'ar' | 'en';
  compact?: boolean;
  className?: string;
}

export function SourceAttribution({ source, language = 'en', compact = false, className }: SourceAttributionProps) {
  const title = language === 'ar' ? source.titleArabic : source.titleEnglish;
  const isUnverified = source.lastVerifiedAt === 'unverified';
  // The title and author render in whichever script the UI language selects,
  // so they take that direction. Everything else in this card is Latin.
  const titleDir = language === 'ar' ? 'rtl' : 'ltr';

  // Licence gate. A source whose terms forbid display is withheld here rather
  // than at every call site, so the block cannot be bypassed by forgetting it.
  if (isSourceDisplayBlocked(source)) {
    return (
      <div
        className={clsx(
          'flex items-start gap-2 rounded-lg border border-stone-300 bg-stone-100 px-3 py-2 text-xs text-stone-600',
          className,
        )}
        role="note"
        dir={language === 'ar' ? 'rtl' : 'ltr'}
      >
        <ShieldX className="h-4 w-4 shrink-0 mt-0.5 text-stone-500" />
        <span>{t('source_license_blocked', language)}</span>
      </div>
    );
  }

  if (compact) {
    return (
      // No `dir` on this row: it mixes an Arabic title with Latin metadata, and
      // one direction for the whole container is what the content policy
      // forbids. Direction is set per text node instead.
      <span className={clsx('inline-flex items-center gap-1.5 text-xs text-stone-500', className)}>
        <SourceBadge reliabilityLevel={source.reliabilityLevel} compact language={language} />
        <span dir={titleDir} lang={language}>{title}</span>
        {source.author && (
          <span className="text-stone-400" dir={titleDir} lang={language}>· {source.author}</span>
        )}
      </span>
    );
  }

  return (
    <div
      className={clsx(
        'rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-xs text-stone-600',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <SourceBadge reliabilityLevel={source.reliabilityLevel} language={language} />
            <span className="font-semibold text-stone-800 truncate" dir={titleDir} lang={language}>
              {title}
            </span>
            {source.language && (
              <span className="uppercase text-stone-400 font-mono" dir="ltr">{source.language}</span>
            )}
          </div>
          {source.author && (
            <div className="mt-0.5 text-stone-500" dir={titleDir} lang={language}>
              {source.author}
            </div>
          )}
          {source.licenseOrTerms && (
            // Licence text is authored in English regardless of UI language.
            <div
              className="mt-0.5 text-stone-400 truncate"
              title={source.licenseOrTerms}
              dir="ltr"
              lang="en"
            >
              {source.licenseOrTerms.length > 80
                ? source.licenseOrTerms.slice(0, 80) + '…'
                : source.licenseOrTerms}
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {isUnverified && (
            <span
              className="inline-flex items-center gap-1 text-amber-600 font-medium"
              dir={titleDir}
              lang={language}
            >
              <Clock className="h-3 w-3" aria-hidden="true" />
              {t('source_unverified', language)}
            </span>
          )}
          {!isUnverified && (
            <span className="text-stone-400" dir="ltr">
              {t('source_verified_on', language)} {source.lastVerifiedAt}
            </span>
          )}
          {source.sourceUrl && !source.sourceUrl.startsWith('data/') && !source.sourceUrl.startsWith('assets/') && (
            <a
              href={source.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-0.5 text-blue-600 hover:text-blue-700"
            >
              {t('source_link', language)} <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Missing source warning
// ---------------------------------------------------------------------------

interface MissingSourceWarningProps {
  language?: 'ar' | 'en';
  className?: string;
}

export function MissingSourceWarning({ language = 'en', className }: MissingSourceWarningProps) {
  return (
    <div
      className={clsx(
        'flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800',
        className,
      )}
      role="note"
      dir={language === 'ar' ? 'rtl' : 'ltr'}
      lang={language}
    >
      <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" aria-hidden="true" />
      <span>{t('missing_source_warning', language)}</span>
    </div>
  );
}
