/**
 * Shown when the device location is denied, unavailable or timed out.
 *
 * The page never substitutes a location on its own: the user either retries
 * the device location, searches for a city (OpenStreetMap Nominatim, only the
 * typed text is sent), or, where the page offers it, explicitly chooses
 * Makkah as a stand-in.
 */
import { memo, useCallback, useState } from 'react';
import { AlertCircle, Loader2, MapPin, Navigation, Search } from 'lucide-react';
import { geocodeAddress } from '../../lib/islamicApis';

export interface ChosenLocation {
  lat: number;
  lng: number;
  name: string;
}

/** Why the device location could not be read (W3C GeolocationPositionError codes). */
export type LocationProblem = 'denied' | 'unavailable' | 'timeout' | 'unsupported';

export function locationProblemOf(error: unknown): LocationProblem {
  const code = (error as { code?: number } | null)?.code;
  if (code === 1) return 'denied';
  if (code === 2) return 'unavailable';
  if (code === 3) return 'timeout';
  return 'unsupported';
}

const PROBLEM_TEXT: Record<LocationProblem, { ar: string; en: string }> = {
  denied: {
    ar: 'لم يُسمح بالوصول إلى موقعك. يمكنك تفعيل إذن الموقع من إعدادات المتصفح أو الجهاز، أو البحث عن مدينتك.',
    en: 'Location access was denied. You can allow it in your browser or device settings, or search for your city.',
  },
  unavailable: {
    ar: 'تعذّر تحديد موقعك الآن. أعد المحاولة أو ابحث عن مدينتك.',
    en: 'Your location could not be determined right now. Try again or search for your city.',
  },
  timeout: {
    ar: 'استغرق تحديد الموقع وقتاً طويلاً. أعد المحاولة أو ابحث عن مدينتك.',
    en: 'Finding your location took too long. Try again or search for your city.',
  },
  unsupported: {
    ar: 'تحديد الموقع غير متاح على هذا الجهاز. ابحث عن مدينتك.',
    en: 'Location is not available on this device. Search for your city instead.',
  },
};

interface LocationFallbackProps {
  isArabic: boolean;
  problem: LocationProblem;
  /** What the location is needed for, shown under the title. */
  purpose: { ar: string; en: string };
  onChoose: (loc: ChosenLocation) => void;
  onRetry?: () => void;
  /** Offer an explicit "use Makkah for now" choice (never applied automatically). */
  onUseMakkah?: () => void;
  className?: string;
}

export const LocationFallback = memo(function LocationFallback({
  isArabic,
  problem,
  purpose,
  onChoose,
  onRetry,
  onUseMakkah,
  className,
}: LocationFallbackProps) {
  const [query, setQuery] = useState('');
  const [busy, setBusy] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const L = (ar: string, en: string) => (isArabic ? ar : en);

  const search = useCallback(async () => {
    const q = query.trim();
    if (!q) return;
    setBusy(true);
    setSearchError(null);
    try {
      const r = await geocodeAddress(q);
      if (r) {
        onChoose({
          lat: r.latitude,
          lng: r.longitude,
          name: r.city
            ? [r.city, r.country].filter(Boolean).join(', ')
            : r.displayName.split(',').slice(0, 2).join(','),
        });
      } else {
        setSearchError(isArabic ? 'لم نعثر على هذه المدينة. جرّب اسماً آخر.' : 'City not found. Try another name.');
      }
    } catch {
      setSearchError(isArabic ? 'تعذّر البحث الآن. تحقّق من الاتصال وأعد المحاولة.' : 'Search failed. Check your connection and try again.');
    } finally {
      setBusy(false);
    }
  }, [query, onChoose, isArabic]);

  return (
    <section
      role="region"
      aria-labelledby="location-fallback-title"
      data-testid="location-fallback"
      className={`p-4 bg-amber-50 border border-amber-200 rounded-xl ${className ?? ''}`}
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      <div className="flex items-start gap-3 mb-3">
        <AlertCircle className="w-5 h-5 text-amber-700 mt-0.5 shrink-0" aria-hidden="true" />
        <div className="min-w-0">
          <h2 id="location-fallback-title" className="font-semibold text-gray-900">
            {L('اختر موقعك', 'Choose your location')}
          </h2>
          <p className="text-sm text-gray-700 mt-1">{isArabic ? PROBLEM_TEXT[problem].ar : PROBLEM_TEXT[problem].en}</p>
          <p className="text-sm text-gray-600 mt-1">{isArabic ? purpose.ar : purpose.en}</p>
        </div>
      </div>

      <form
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void search();
        }}
      >
        <label htmlFor="location-fallback-city" className="sr-only">
          {L('اسم المدينة', 'City name')}
        </label>
        <input
          id="location-fallback-city"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={L('ابحث عن مدينة...', 'Search for a city...')}
          className="min-w-0 flex-1 basis-40 min-h-11 px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          autoComplete="address-level2"
        />
        <button
          type="submit"
          disabled={busy || !query.trim()}
          aria-busy={busy}
          className="shrink-0 min-h-11 px-4 py-2 bg-primary-700 text-white rounded-lg hover:bg-primary-800 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
        >
          {busy ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Search className="w-4 h-4" aria-hidden="true" />}
          <span>{L('بحث', 'Search')}</span>
        </button>
      </form>
      {searchError && (
        <p role="alert" className="mt-2 text-sm text-red-700">
          {searchError}
        </p>
      )}

      {(onRetry || onUseMakkah) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="min-h-11 px-4 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg hover:bg-gray-50 inline-flex items-center gap-2"
            >
              <Navigation className="w-4 h-4" aria-hidden="true" />
              {L('أعد محاولة تحديد موقعي', 'Try my location again')}
            </button>
          )}
          {onUseMakkah && (
            <button
              type="button"
              onClick={onUseMakkah}
              className="min-h-11 px-4 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg hover:bg-gray-50 inline-flex items-center gap-2"
            >
              <MapPin className="w-4 h-4" aria-hidden="true" />
              {L('استخدم مكة المكرمة مؤقتاً', 'Use Makkah for now')}
            </button>
          )}
        </div>
      )}
    </section>
  );
});
