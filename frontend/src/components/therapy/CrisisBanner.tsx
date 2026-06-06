import { ShieldAlert, ExternalLink, Phone } from 'lucide-react';
import clsx from 'clsx';
import type { CrisisHotlineOut } from '../../types/therapy';

interface CrisisBannerProps {
  level: 'none' | 'elevated' | 'crisis' | undefined;
  bannerEn?: string | null;
  bannerAr?: string | null;
  hotlines?: CrisisHotlineOut[];
  language: 'ar' | 'en';
}

/**
 * Crisis-safety banner shown ABOVE any guidance content whenever the
 * backend `classify_crisis` returns a non-`none` level.
 *
 * - `crisis`: red banner + full hotline list.
 * - `elevated`: amber banner + condensed hotline list.
 * - `none`: renders nothing.
 *
 * Errs on the side of being shown — this component should never be
 * suppressed by other state.
 */
export function CrisisBanner({
  level,
  bannerEn,
  bannerAr,
  hotlines,
  language,
}: CrisisBannerProps) {
  if (!level || level === 'none' || !(bannerEn || bannerAr)) return null;

  const isCrisis = level === 'crisis';
  const isRtl = language === 'ar';
  const dir = isRtl ? 'rtl' : 'ltr';
  const text = isRtl ? bannerAr : bannerEn;

  const bg = isCrisis ? 'bg-red-50' : 'bg-amber-50';
  const border = isCrisis ? 'border-red-300' : 'border-amber-300';
  const titleColor = isCrisis ? 'text-red-800' : 'text-amber-900';
  const subColor = isCrisis ? 'text-red-700' : 'text-amber-800';
  const iconColor = isCrisis ? 'text-red-500' : 'text-amber-500';

  return (
    <section
      role="alert"
      aria-live="assertive"
      className={clsx('rounded-2xl border p-4 space-y-3', bg, border)}
      dir={dir}
    >
      <div className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
        <ShieldAlert className={clsx('w-6 h-6 flex-shrink-0 mt-0.5', iconColor)} />
        <div className="flex-1 space-y-1">
          <p
            className={clsx(
              'font-semibold leading-snug',
              titleColor,
              isRtl && 'font-arabic text-right',
            )}
          >
            {isCrisis
              ? isRtl
                ? 'سلامتك أولاً — اطلب المساعدة الآن'
                : 'Your safety comes first — please reach out now'
              : isRtl
                ? 'يبدو أنك تحتاج دعماً'
                : 'It sounds like you could use support'}
          </p>
          <p
            className={clsx(
              'text-sm leading-relaxed',
              subColor,
              isRtl && 'font-arabic text-right',
            )}
          >
            {text}
          </p>
        </div>
      </div>

      {hotlines && hotlines.length > 0 && (
        <ul className="space-y-2">
          {hotlines.map(h => (
            <li
              key={`${h.region_code}-${h.number}`}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg bg-white border',
                border,
                isRtl && 'flex-row-reverse text-right',
              )}
              dir={dir}
            >
              <Phone className={clsx('w-4 h-4 flex-shrink-0', iconColor)} />
              <div className="flex-1 min-w-0">
                <p
                  className={clsx(
                    'text-sm font-medium text-gray-900',
                    isRtl && 'font-arabic',
                  )}
                >
                  {isRtl ? h.region_name_ar : h.region_name_en}
                  {h.is_muslim_specific && (
                    <span
                      className={clsx(
                        'ms-2 text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700',
                        isRtl && 'font-arabic',
                      )}
                    >
                      {isRtl ? 'مختص للمسلمين' : 'Muslim-integrated'}
                    </span>
                  )}
                </p>
                <p className={clsx('text-xs text-gray-600 truncate', isRtl && 'font-arabic')}>
                  {isRtl ? h.organisation_ar : h.organisation_en}
                </p>
              </div>
              <span className="font-mono text-sm font-semibold text-gray-900 tabular-nums">
                {h.number}
              </span>
              <a
                href={h.url}
                target="_blank"
                rel="noopener noreferrer"
                className={clsx(
                  'text-xs underline flex items-center gap-1 hover:opacity-80',
                  subColor,
                )}
                aria-label={isRtl ? 'فتح الموقع' : 'Open website'}
              >
                {isRtl ? 'الموقع' : 'site'}
                <ExternalLink className="w-3 h-3" />
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
