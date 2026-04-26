import clsx from 'clsx';
import { ShieldCheck, ShieldAlert, ShieldX, Clock, ExternalLink } from 'lucide-react';
import { type ReliabilityLevel, type Source } from '../../data/sourceRegistry';
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
    label: 'Canonical',
    labelAr: 'متواتر',
    icon: ShieldCheck,
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
      <Icon className={compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
      {!compact && <span>{label}</span>}
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

  if (compact) {
    return (
      <span className={clsx('inline-flex items-center gap-1.5 text-xs text-stone-500', className)}>
        <SourceBadge reliabilityLevel={source.reliabilityLevel} compact language={language} />
        <span>{title}</span>
        {source.author && <span className="text-stone-400">· {source.author}</span>}
      </span>
    );
  }

  return (
    <div
      className={clsx(
        'rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-xs text-stone-600',
        className,
      )}
      dir={language === 'ar' ? 'rtl' : 'ltr'}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <SourceBadge reliabilityLevel={source.reliabilityLevel} language={language} />
            <span className="font-semibold text-stone-800 truncate">{title}</span>
            {source.language && (
              <span className="uppercase text-stone-400 font-mono" dir="ltr">{source.language}</span>
            )}
          </div>
          {source.author && (
            <div className="mt-0.5 text-stone-500">{source.author}</div>
          )}
          {source.licenseOrTerms && (
            <div className="mt-0.5 text-stone-400 truncate" title={source.licenseOrTerms}>
              {source.licenseOrTerms.length > 80
                ? source.licenseOrTerms.slice(0, 80) + '…'
                : source.licenseOrTerms}
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {isUnverified && (
            <span className="inline-flex items-center gap-1 text-amber-600 font-medium">
              <Clock className="h-3 w-3" />
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
      role="alert"
      dir={language === 'ar' ? 'rtl' : 'ltr'}
    >
      <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" />
      <span>{t('missing_source_warning', language)}</span>
    </div>
  );
}
