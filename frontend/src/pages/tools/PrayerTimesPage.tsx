/**
 * PrayerTimesPage - FANG-level production component
 *
 * Features:
 * - Custom hooks for geolocation and async state
 * - Proper error boundaries and loading states
 * - Full accessibility (ARIA, keyboard navigation)
 * - Memoized components for performance
 * - Local storage persistence for settings
 */

import { memo, useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  MapPin,
  Sun,
  Moon,
  Sunrise,
  Sunset,
  ChevronLeft,
  ChevronRight,
  Settings,
  Search,
  type LucideIcon,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import {
  getPrayerTimes,
  geocodeAddress,
  reverseGeocode,
  PRAYER_METHODS,
  type PrayerTimesResponse,
  formatPrayerTime,
  toArabicNumerals,
} from '../../lib/islamicApis';
import { useGeolocation } from '../../hooks/useGeolocation';
import { useAsync } from '../../hooks/useAsync';
import { useLocalStorage } from '../../hooks/useLocalStorage';
// useDebouncedCallback available from '../../hooks/useDebounce' if needed
import { ErrorBoundary, InlineError } from '../../components/ui/ErrorBoundary';
import { SkeletonPrayerTimes } from '../../components/ui/Skeleton';
import { LocationFallback, locationProblemOf } from './LocationFallback';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import clsx from 'clsx';
import { qiblaBearing } from '../../lib/qibla';
import { QiblaCompass } from '../../components/tools/QiblaCompass';

// ============================================
// Types
// ============================================

interface PrayerInfo {
  name_en: string;
  name_ar: string;
  icon: LucideIcon;
  color: string;
}

interface Location {
  lat: number;
  lng: number;
  name: string;
  /** device: from geolocation; manual: a city the user searched; makkah: the user chose Makkah as a stand-in. */
  source?: 'device' | 'manual' | 'makkah';
}

interface PrayerSettings {
  method: number;
  use24Hour: boolean;
}

// ============================================
// Constants
// ============================================

const PRAYERS: Record<string, PrayerInfo> = {
  Fajr: { name_en: 'Fajr', name_ar: 'الفجر', icon: Moon, color: 'indigo' },
  Sunrise: { name_en: 'Sunrise', name_ar: 'الشروق', icon: Sunrise, color: 'orange' },
  Dhuhr: { name_en: 'Dhuhr', name_ar: 'الظهر', icon: Sun, color: 'yellow' },
  Asr: { name_en: 'Asr', name_ar: 'العصر', icon: Sun, color: 'amber' },
  Maghrib: { name_en: 'Maghrib', name_ar: 'المغرب', icon: Sunset, color: 'orange' },
  Isha: { name_en: 'Isha', name_ar: 'العشاء', icon: Moon, color: 'purple' },
} as const;

const MAIN_PRAYERS = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'] as const;

const DEFAULT_SETTINGS: PrayerSettings = {
  method: 2, // ISNA
  use24Hour: false,
};

/** Offered only as an explicit user choice when the device location is unavailable. */
const MAKKAH_LOCATION: Location = {
  lat: 21.4225,
  lng: 39.8262,
  name: 'Makkah',
  source: 'makkah',
};

/** Minutes since local midnight at the prayer-times location (falls back to device time). */
export function minutesInTimeZone(now: Date, timeZone: string | undefined): number {
  if (timeZone) {
    try {
      const parts = new Intl.DateTimeFormat('en-GB', {
        timeZone,
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
      }).formatToParts(now);
      const h = Number(parts.find((p) => p.type === 'hour')?.value);
      const m = Number(parts.find((p) => p.type === 'minute')?.value);
      if (Number.isFinite(h) && Number.isFinite(m)) return (h % 24) * 60 + m;
    } catch {
      // Unknown time zone id: use the device clock.
    }
  }
  return now.getHours() * 60 + now.getMinutes();
}

// ============================================
// Custom Hook: usePrayerTimes
// ============================================

function usePrayerTimes(
  location: Location | null,
  method: number,
  date: Date
) {
  const fetchPrayerData = useCallback(async () => {
    if (!location) throw new Error('No location available');

    const prayerResponse = await getPrayerTimes(location.lat, location.lng, method, date);
    // Computed locally: no network round trip, and it works offline.
    return { prayerData: prayerResponse, qiblaDirection: qiblaBearing(location.lat, location.lng) };
  }, [location, method, date]);

  const { execute, isPending, isError, data, error, reset } = useAsync(fetchPrayerData, {
    retryCount: 2,
    keepPreviousData: true,
  });

  useEffect(() => {
    if (location) {
      execute();
    }
  }, [location, execute]);

  return {
    prayerData: data?.prayerData ?? null,
    qiblaDirection: data?.qiblaDirection ?? null,
    loading: isPending,
    error: isError ? error : null,
    refetch: execute,
    reset,
  };
}

// ============================================
// Custom Hook: useCurrentTime
// ============================================

function useCurrentTime(intervalMs = 60000) {
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs]);

  return currentTime;
}

// ============================================
// Sub-Components
// ============================================

interface NextPrayerCardProps {
  prayerData: PrayerTimesResponse;
  currentTime: Date;
  use24Hour: boolean;
  isArabic: boolean;
}

/** "2 hours 5 minutes" in English, or the Arabic form with the right
 *  plural (ساعة / ساعتان / ساعات) and Arabic-Indic digits. */
export function formatRemaining(h: number, m: number, isArabic: boolean): string {
  if (!isArabic) return h > 0 ? `${h}h ${m}m` : `${m}m`;
  const nf = new Intl.NumberFormat('ar-SA-u-nu-arab');
  const pr = new Intl.PluralRules('ar');
  const unit = (n: number, one: string, two: string, few: string, many: string) => {
    switch (pr.select(n)) {
      case 'one': return one;
      case 'two': return two;
      case 'few': return `${nf.format(n)} ${few}`;
      default: return `${nf.format(n)} ${many}`;
    }
  };
  const hours = unit(h, 'ساعة', 'ساعتان', 'ساعات', 'ساعة');
  const minutes = unit(m, 'دقيقة', 'دقيقتان', 'دقائق', 'دقيقة');
  if (h > 0 && m > 0) return `${hours} و${minutes}`;
  if (h > 0) return hours;
  return minutes;
}

const NextPrayerCard = memo(function NextPrayerCard({
  prayerData,
  currentTime,
  use24Hour,
  isArabic,
}: NextPrayerCardProps) {
  const nextPrayer = useMemo(() => {
    const currentMinutes = minutesInTimeZone(currentTime, prayerData.meta?.timezone);

    for (const prayerName of MAIN_PRAYERS) {
      const timeStr = prayerData.timings[prayerName as keyof typeof prayerData.timings];
      if (!timeStr) continue;

      const [hours, minutes] = timeStr.split(':').map(Number);
      const prayerMinutes = hours * 60 + minutes;

      if (prayerMinutes > currentMinutes) {
        const remainingMinutes = prayerMinutes - currentMinutes;
        const h = Math.floor(remainingMinutes / 60);
        const m = remainingMinutes % 60;

        return {
          name: prayerName,
          time: timeStr,
          remaining: formatRemaining(h, m, isArabic),
        };
      }
    }

    // All prayers passed, next is Fajr tomorrow
    const fajrTime = prayerData.timings.Fajr;
    const [fajrH, fajrM] = fajrTime.split(':').map(Number);
    const fajrMinutes = fajrH * 60 + fajrM;
    const remainingMinutes = 24 * 60 - currentMinutes + fajrMinutes;
    const h = Math.floor(remainingMinutes / 60);
    const m = remainingMinutes % 60;

    return {
      name: 'Fajr',
      time: fajrTime,
      remaining: formatRemaining(h, m, isArabic),
    };
  }, [prayerData, currentTime, isArabic]);

  if (!nextPrayer) return null;

  return (
    <section
      aria-label={isArabic ? 'الصلاة القادمة' : 'Next Prayer'}
      className="mb-6 p-6 bg-gradient-to-br from-primary-600 to-primary-700 text-white rounded-xl shadow-lg"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-primary-100 text-sm mb-1">
            {isArabic ? 'الصلاة القادمة' : 'Next Prayer'}
          </p>
          <h2 className="text-3xl font-bold mb-1">
            {isArabic ? PRAYERS[nextPrayer.name]?.name_ar : nextPrayer.name}
          </h2>
          <p className="text-xl tabular-nums">
            {formatPrayerTime(nextPrayer.time, use24Hour, isArabic ? 'ar' : 'en')}
          </p>
        </div>
        <div className="text-end">
          <p className="text-primary-100 text-sm mb-1">
            {isArabic ? 'الوقت المتبقي' : 'Time Remaining'}
          </p>
          <p className="text-2xl font-bold" role="timer" aria-live="polite">
            {nextPrayer.remaining}
          </p>
        </div>
      </div>
    </section>
  );
});

interface PrayerCardProps {
  prayerKey: string;
  prayer: PrayerInfo;
  time: string;
  isNext: boolean;
  use24Hour: boolean;
  isArabic: boolean;
}

const PrayerCard = memo(function PrayerCard({
  prayerKey: _prayerKey,
  prayer,
  time,
  isNext,
  use24Hour,
  isArabic,
}: PrayerCardProps) {
  void _prayerKey; // Reserved for future use (e.g., analytics)
  const Icon = prayer.icon;

  return (
    <article
      className={clsx(
        'card border-2 transition-all focus-within:ring-2 focus-within:ring-primary-500',
        isNext
          ? 'border-primary-500 bg-primary-50 shadow-md'
          : 'border-gray-200 hover:border-gray-300'
      )}
      aria-label={`${isArabic ? prayer.name_ar : prayer.name_en}: ${formatPrayerTime(time, use24Hour, isArabic ? 'ar' : 'en')}`}
    >
      <div className="flex items-center gap-3">
        <div
          className={clsx(
            'p-3 rounded-lg',
            isNext ? 'bg-primary-100' : 'bg-gray-100'
          )}
          aria-hidden="true"
        >
          <Icon
            className={clsx(
              'w-6 h-6',
              isNext ? 'text-primary-600' : 'text-gray-600'
            )}
          />
        </div>
        <div className="flex-1 min-w-0">
          <h3
            className={clsx(
              'font-semibold',
              isNext ? 'text-primary-900' : 'text-gray-900'
            )}
          >
            {isArabic ? prayer.name_ar : prayer.name_en}
          </h3>
          <p
            className={clsx(
              'text-lg font-bold tabular-nums',
              isNext ? 'text-primary-600' : 'text-gray-700'
            )}
          >
            {formatPrayerTime(time, use24Hour, isArabic ? 'ar' : 'en')}
          </p>
        </div>
        {isNext && (
          <span className="px-2 py-1 bg-primary-600 text-white text-xs rounded-full font-medium">
            {isArabic ? 'التالي' : 'Next'}
          </span>
        )}
      </div>
    </article>
  );
});

interface PrayerTimesGridProps {
  prayerData: PrayerTimesResponse;
  currentTime: Date;
  use24Hour: boolean;
  isArabic: boolean;
}

const PrayerTimesGrid = memo(function PrayerTimesGrid({
  prayerData,
  currentTime,
  use24Hour,
  isArabic,
}: PrayerTimesGridProps) {
  const nextPrayerName = useMemo(() => {
    const currentMinutes = minutesInTimeZone(currentTime, prayerData.meta?.timezone);

    for (const prayerName of MAIN_PRAYERS) {
      const timeStr = prayerData.timings[prayerName as keyof typeof prayerData.timings];
      if (!timeStr) continue;

      const [hours, minutes] = timeStr.split(':').map(Number);
      if (hours * 60 + minutes > currentMinutes) {
        return prayerName;
      }
    }

    return 'Fajr';
  }, [prayerData, currentTime]);

  return (
    <div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
      role="list"
      aria-label={isArabic ? 'أوقات الصلاة' : 'Prayer Times'}
    >
      {Object.entries(PRAYERS).map(([key, prayer]) => {
        const time = prayerData.timings[key as keyof typeof prayerData.timings];
        if (!time) return null;

        return (
          <div key={key} role="listitem">
            <PrayerCard
              prayerKey={key}
              prayer={prayer}
              time={time}
              isNext={nextPrayerName === key}
              use24Hour={use24Hour}
              isArabic={isArabic}
            />
          </div>
        );
      })}
    </div>
  );
});

interface AdditionalTimesProps {
  timings: PrayerTimesResponse['timings'];
  use24Hour: boolean;
  isArabic: boolean;
}

const AdditionalTimes = memo(function AdditionalTimes({
  timings,
  use24Hour,
  isArabic,
}: AdditionalTimesProps) {
  const additionalTimes = [
    { key: 'Imsak', label_en: 'Imsak', label_ar: 'الإمساك' },
    { key: 'Midnight', label_en: 'Midnight', label_ar: 'منتصف الليل' },
    { key: 'Firstthird', label_en: 'First Third', label_ar: 'الثلث الأول' },
    { key: 'Lastthird', label_en: 'Last Third', label_ar: 'الثلث الأخير' },
  ] as const;

  return (
    <section
      aria-label={isArabic ? 'أوقات إضافية' : 'Additional Times'}
      className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-xl"
    >
      <h3 className="font-semibold text-gray-900 mb-3">
        {isArabic ? 'أوقات إضافية' : 'Additional Times'}
      </h3>
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        {additionalTimes.map(({ key, label_en, label_ar }) => (
          <div key={key}>
            <dt className="text-gray-500">{isArabic ? label_ar : label_en}</dt>
            <dd className="font-semibold tabular-nums">
              {formatPrayerTime(timings[key as keyof typeof timings], use24Hour, isArabic ? 'ar' : 'en')}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
});

interface SettingsPanelProps {
  settings: PrayerSettings;
  onSettingsChange: (settings: PrayerSettings) => void;
  onLocationSearch: (query: string) => Promise<void>;
  searchLoading: boolean;
  isArabic: boolean;
}

const SettingsPanel = memo(function SettingsPanel({
  settings,
  onSettingsChange,
  onLocationSearch,
  searchLoading,
  isArabic,
}: SettingsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = useCallback(() => {
    if (searchQuery.trim()) {
      onLocationSearch(searchQuery);
      setSearchQuery('');
    }
  }, [searchQuery, onLocationSearch]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleSearch();
      }
    },
    [handleSearch]
  );

  return (
    <div
      className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-4"
      role="region"
      aria-label={isArabic ? 'الإعدادات' : 'Settings'}
    >
      <h3 className="font-semibold text-gray-900">
        {isArabic ? 'الإعدادات' : 'Settings'}
      </h3>

      {/* Location Search */}
      <div>
        <label
          htmlFor="location-search"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {isArabic ? 'تغيير الموقع' : 'Change Location'}
        </label>
        <div className="flex flex-wrap gap-2">
          <input
            id="location-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isArabic ? 'ابحث عن مدينة...' : 'Search for a city...'}
            className="min-w-0 flex-1 basis-40 min-h-11 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            aria-describedby="location-search-hint"
          />
          <button
            onClick={handleSearch}
            disabled={searchLoading || !searchQuery.trim()}
            className="shrink-0 min-h-11 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
            aria-busy={searchLoading}
          >
            {searchLoading ? (
              <LoadingSpinner size="sm" variant="white" />
            ) : (
              <Search className="w-4 h-4" aria-hidden="true" />
            )}
            <span>{isArabic ? 'بحث' : 'Search'}</span>
          </button>
        </div>
        <p id="location-search-hint" className="sr-only">
          {isArabic ? 'اضغط Enter للبحث' : 'Press Enter to search'}
        </p>
      </div>

      {/* Calculation Method */}
      <div>
        <label
          htmlFor="calculation-method"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {isArabic ? 'طريقة الحساب' : 'Calculation Method'}
        </label>
        <select
          id="calculation-method"
          value={settings.method}
          onChange={(e) =>
            onSettingsChange({ ...settings, method: Number(e.target.value) })
          }
          className="w-full min-w-0 min-h-11 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          {Object.entries(PRAYER_METHODS).map(([id, method]) => (
            <option key={id} value={id}>
              {isArabic ? method.name_ar : method.name}
            </option>
          ))}
        </select>
      </div>

      {/* 24-hour format toggle */}
      <div className="flex items-center min-h-11">
        <input
          id="use-24-hour"
          type="checkbox"
          checked={settings.use24Hour}
          onChange={(e) =>
            onSettingsChange({ ...settings, use24Hour: e.target.checked })
          }
          className="w-5 h-5 text-primary-600 rounded focus:ring-primary-500"
        />
        <label
          htmlFor="use-24-hour"
          className="ms-2 py-2 flex-1 text-sm text-gray-700 cursor-pointer"
        >
          {isArabic ? 'صيغة 24 ساعة' : '24-hour format'}
        </label>
      </div>
    </div>
  );
});

interface DateNavigatorProps {
  date: Date;
  hijriDate?: PrayerTimesResponse['date']['hijri'];
  onDateChange: (days: number) => void;
  isArabic: boolean;
}

const DateNavigator = memo(function DateNavigator({
  date,
  hijriDate,
  onDateChange,
  isArabic,
}: DateNavigatorProps) {
  return (
    <nav
      aria-label={isArabic ? 'التنقل بين التواريخ' : 'Date Navigation'}
      className="mb-6 flex items-center justify-center gap-4"
    >
      <button
        onClick={() => onDateChange(-1)}
        className="tap text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label={isArabic ? 'اليوم السابق' : 'Previous day'}
      >
        <ChevronLeft className={clsx('w-5 h-5', isArabic && 'rotate-180')} aria-hidden="true" />
      </button>
      <div className="text-center min-w-0 flex-1 max-w-xs">
        <p className="font-semibold text-gray-900">
          {date.toLocaleDateString(isArabic ? 'ar-SA-u-ca-gregory-nu-arab' : 'en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>
        {hijriDate && (
          <p className="text-sm text-gray-600">
            {isArabic
              ? `${toArabicNumerals(hijriDate.day)} ${hijriDate.month.ar} ${toArabicNumerals(hijriDate.year)}`
              : `${hijriDate.day} ${hijriDate.month.en} ${hijriDate.year} AH`}
          </p>
        )}
      </div>
      <button
        onClick={() => onDateChange(1)}
        className="tap text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label={isArabic ? 'اليوم التالي' : 'Next day'}
      >
        <ChevronRight className={clsx('w-5 h-5', isArabic && 'rotate-180')} aria-hidden="true" />
      </button>
    </nav>
  );
});

// ============================================
// Main Component
// ============================================

function PrayerTimesPageContent() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  // Persistent settings
  const [settings, setSettings] = useLocalStorage<PrayerSettings>(
    'prayer_settings',
    DEFAULT_SETTINGS
  );

  // A city the user picked (search, or Makkah chosen explicitly) is kept on
  // this device so the next visit does not ask again.
  const [savedLocation, setSavedLocation] = useLocalStorage<Location | null>(
    'prayer_manual_location',
    null
  );

  // State
  const [location, setLocationState] = useState<Location | null>(savedLocation);
  const chooseLocation = useCallback(
    (loc: Location) => {
      setLocationState(loc);
      if (loc.source === 'manual' || loc.source === 'makkah') setSavedLocation(loc);
    },
    [setSavedLocation]
  );
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [showSettings, setShowSettings] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Current time (updates every minute)
  const currentTime = useCurrentTime(60000);

  // Geolocation
  const { state: geoState, getCurrentPosition } = useGeolocation({
    enableHighAccuracy: false, // coarse is enough; only ~1 km precision is sent anyway
    timeout: 10000,
  });

  // Initialize location from geolocation (only when the user has not picked one).
  useEffect(() => {
    if (geoState.coords && !location) {
      const { latitude, longitude } = geoState.coords;
      reverseGeocode(latitude, longitude).then((locationInfo) => {
        setLocationState((current) =>
          current ?? {
            lat: latitude,
            lng: longitude,
            name: locationInfo?.city
              ? [locationInfo.city, locationInfo.country].filter(Boolean).join(', ')
              : `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`,
            source: 'device',
          }
        );
      });
    }
  }, [geoState.coords, location]);

  // No silent fallback: when geolocation fails the page asks the user to
  // search for a city (or to choose Makkah explicitly) via LocationFallback.
  const retryDeviceLocation = useCallback(() => {
    setSavedLocation(null);
    setLocationState(null);
    getCurrentPosition();
  }, [getCurrentPosition, setSavedLocation]);

  // Prayer times data
  const { prayerData, qiblaDirection, loading, error, refetch } = usePrayerTimes(
    location,
    settings.method,
    selectedDate
  );

  // Location search handler
  const handleLocationSearch = useCallback(
    async (query: string) => {
      setSearchLoading(true);
      setSearchError(null);

      try {
        const result = await geocodeAddress(query);
        if (result) {
          chooseLocation({
            lat: result.latitude,
            lng: result.longitude,
            name: result.city
              ? [result.city, result.country].filter(Boolean).join(', ')
              : result.displayName.split(',').slice(0, 2).join(','),
            source: 'manual',
          });
          setShowSettings(false);
        } else {
          setSearchError(isArabic ? 'لم يتم العثور على الموقع' : 'Location not found');
        }
      } catch {
        setSearchError(isArabic ? 'فشل في البحث عن الموقع' : 'Failed to search location');
      } finally {
        setSearchLoading(false);
      }
    },
    [isArabic, chooseLocation]
  );

  // Date change handler
  const handleDateChange = useCallback((days: number) => {
    setSelectedDate((prev) => {
      const newDate = new Date(prev);
      newDate.setDate(newDate.getDate() + days);
      return newDate;
    });
  }, []);

  // Request the device location on mount unless a city is already chosen.
  // Runs once: a failure must not trigger an automatic retry loop.
  const [askedDevice, setAskedDevice] = useState(false);
  useEffect(() => {
    if (askedDevice || savedLocation) return;
    setAskedDevice(true);
    if (!geoState.coords) getCurrentPosition();
  }, [askedDevice, savedLocation, geoState.coords, getCurrentPosition]);

  const locationLabel =
    location?.source === 'makkah'
      ? isArabic
        ? 'مكة المكرمة'
        : 'Makkah'
      : location?.name;

  return (
    <div
      className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <header className="mb-6">
        <Link
          to="/tools"
          className="inline-flex min-h-11 items-center gap-2 text-primary-600 hover:text-primary-700 mb-2 focus:outline-none focus:underline"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} aria-hidden="true" />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-3 bg-primary-100 rounded-lg shrink-0" aria-hidden="true">
              <Clock className="w-8 h-8 text-primary-600" />
            </div>
            <div className="min-w-0">
              <h1 className={clsx('text-2xl font-bold text-gray-900', isArabic && 'font-arabic')}>
                {isArabic ? 'أوقات الصلاة' : 'Prayer Times'}
              </h1>
              <p className="text-gray-600 flex items-center gap-1">
                <MapPin className="w-4 h-4" aria-hidden="true" />
                <span>
                  {locationLabel ||
                    (geoState.loading
                      ? isArabic
                        ? 'جاري تحديد الموقع...'
                        : 'Detecting location...'
                      : isArabic
                      ? 'الموقع غير متاح'
                      : 'Location unavailable')}
                </span>
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="tap shrink-0 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-expanded={showSettings}
            aria-controls="settings-panel"
            aria-label={isArabic ? 'الإعدادات' : 'Settings'}
          >
            <Settings className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div id="settings-panel">
          <SettingsPanel
            settings={settings}
            onSettingsChange={setSettings}
            onLocationSearch={handleLocationSearch}
            searchLoading={searchLoading}
            isArabic={isArabic}
          />
          {searchError && (
            <InlineError
              error={searchError}
              onRetry={() => setSearchError(null)}
              className="mb-4"
            />
          )}
        </div>
      )}

      {/* Device location denied / unavailable: ask, never substitute silently. */}
      {geoState.error && !location && (
        <LocationFallback
          isArabic={isArabic}
          problem={locationProblemOf(geoState.error)}
          purpose={{
            ar: 'نحتاج إلى مدينتك لحساب أوقات الصلاة واتجاه القبلة.',
            en: 'Prayer times and the Qibla direction are calculated for your city.',
          }}
          onChoose={(loc) => chooseLocation({ ...loc, source: 'manual' })}
          onRetry={retryDeviceLocation}
          onUseMakkah={() => chooseLocation(MAKKAH_LOCATION)}
          className="mb-6"
        />
      )}

      {/* Makkah is shown only because the user chose it; say so plainly. */}
      {location?.source === 'makkah' && (
        <div
          role="status"
          data-testid="makkah-stand-in"
          className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-xl flex flex-wrap items-center gap-2"
        >
          <p className="text-sm text-gray-800 flex-1 basis-48">
            {isArabic
              ? 'تُعرض أوقات مكة المكرمة واتجاه القبلة منها إلى أن تختار موقعك.'
              : 'Showing Makkah times until you choose your location.'}
          </p>
          <button
            type="button"
            onClick={() => setShowSettings(true)}
            className="min-h-11 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-800 hover:bg-gray-50"
          >
            {isArabic ? 'اختر مدينتك' : 'Choose your city'}
          </button>
          <button
            type="button"
            onClick={retryDeviceLocation}
            className="min-h-11 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-800 hover:bg-gray-50"
          >
            {isArabic ? 'استخدم موقعي' : 'Use my location'}
          </button>
        </div>
      )}

      {/* Date Navigation */}
      <DateNavigator
        date={selectedDate}
        hijriDate={prayerData?.date.hijri}
        onDateChange={handleDateChange}
        isArabic={isArabic}
      />

      {/* Main Content */}
      {loading && !prayerData ? (
        <SkeletonPrayerTimes />
      ) : error && !prayerData ? (
        <InlineError error={error} onRetry={refetch} />
      ) : prayerData ? (
        <>
          {/* Next Prayer Card */}
          <NextPrayerCard
            prayerData={prayerData}
            currentTime={currentTime}
            use24Hour={settings.use24Hour}
            isArabic={isArabic}
          />

          {/* Qibla Direction */}
          {qiblaDirection !== null && (
            <QiblaCompass bearing={qiblaDirection} isArabic={isArabic} />
          )}

          {/* Prayer Times Grid */}
          <PrayerTimesGrid
            prayerData={prayerData}
            currentTime={currentTime}
            use24Hour={settings.use24Hour}
            isArabic={isArabic}
          />

          {/* Additional Times */}
          <AdditionalTimes
            timings={prayerData.timings}
            use24Hour={settings.use24Hour}
            isArabic={isArabic}
          />
        </>
      ) : null}

      {/* API Attribution */}
      <footer className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 text-center">
        <p>
          {isArabic ? 'البيانات مقدمة من' : 'Data provided by'}{' '}
          <a
            href="https://aladhan.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-700 underline focus:outline-none"
          >
            AlAdhan API
          </a>
        </p>
      </footer>
    </div>
  );
}

// Export with Error Boundary
export function PrayerTimesPage() {
  return (
    <ErrorBoundary>
      <PrayerTimesPageContent />
    </ErrorBoundary>
  );
}
