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
  Compass,
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
  getQiblaDirection,
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
import { LocationDenied } from '../../components/ui/EmptyState';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import clsx from 'clsx';

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

const MAKKAH_LOCATION: Location = {
  lat: 21.4225,
  lng: 39.8262,
  name: 'Makkah',
};

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

    const [prayerResponse, qiblaResponse] = await Promise.all([
      getPrayerTimes(location.lat, location.lng, method, date),
      getQiblaDirection(location.lat, location.lng),
    ]);

    return { prayerData: prayerResponse, qiblaDirection: qiblaResponse.direction };
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

const NextPrayerCard = memo(function NextPrayerCard({
  prayerData,
  currentTime,
  use24Hour,
  isArabic,
}: NextPrayerCardProps) {
  const nextPrayer = useMemo(() => {
    const currentMinutes = currentTime.getHours() * 60 + currentTime.getMinutes();

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
          remaining: h > 0
            ? isArabic ? `${h} ساعة و ${m} دقيقة` : `${h}h ${m}m`
            : isArabic ? `${m} دقيقة` : `${m}m`,
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
      remaining: isArabic ? `${h} ساعة و ${m} دقيقة` : `${h}h ${m}m`,
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
          <p className="text-xl" aria-label={`Time: ${formatPrayerTime(nextPrayer.time, use24Hour)}`}>
            {formatPrayerTime(nextPrayer.time, use24Hour)}
          </p>
        </div>
        <div className="text-right">
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

interface QiblaCardProps {
  direction: number;
  isArabic: boolean;
}

const QiblaCard = memo(function QiblaCard({ direction, isArabic }: QiblaCardProps) {
  return (
    <section
      aria-label={isArabic ? 'اتجاه القبلة' : 'Qibla Direction'}
      className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-100 rounded-lg" aria-hidden="true">
            <Compass className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <p className="font-semibold text-emerald-900">
              {isArabic ? 'اتجاه القبلة' : 'Qibla Direction'}
            </p>
            <p className="text-sm text-emerald-700">
              {isArabic
                ? `${toArabicNumerals(direction.toFixed(1))}° من الشمال`
                : `${direction.toFixed(1)}° from North`}
            </p>
          </div>
        </div>
        <div
          className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center transition-transform"
          style={{ transform: `rotate(${direction}deg)` }}
          role="img"
          aria-label={`Qibla compass pointing ${direction.toFixed(0)} degrees`}
        >
          <div className="w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-b-[16px] border-b-emerald-600" />
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
      aria-label={`${isArabic ? prayer.name_ar : prayer.name_en}: ${formatPrayerTime(time, use24Hour)}`}
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
            {isArabic
              ? toArabicNumerals(formatPrayerTime(time, use24Hour))
              : formatPrayerTime(time, use24Hour)}
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
    const currentMinutes = currentTime.getHours() * 60 + currentTime.getMinutes();

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
              {formatPrayerTime(timings[key as keyof typeof timings], use24Hour)}
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
        <div className="flex gap-2">
          <input
            id="location-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isArabic ? 'ابحث عن مدينة...' : 'Search for a city...'}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            aria-describedby="location-search-hint"
          />
          <button
            onClick={handleSearch}
            disabled={searchLoading || !searchQuery.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
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
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          {Object.entries(PRAYER_METHODS).map(([id, method]) => (
            <option key={id} value={id}>
              {isArabic ? method.name_ar : method.name}
            </option>
          ))}
        </select>
      </div>

      {/* 24-hour format toggle */}
      <div className="flex items-center">
        <input
          id="use-24-hour"
          type="checkbox"
          checked={settings.use24Hour}
          onChange={(e) =>
            onSettingsChange({ ...settings, use24Hour: e.target.checked })
          }
          className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
        />
        <label
          htmlFor="use-24-hour"
          className="ml-2 text-sm text-gray-700 cursor-pointer"
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
        className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label={isArabic ? 'اليوم السابق' : 'Previous day'}
      >
        <ChevronLeft className={clsx('w-5 h-5', isArabic && 'rotate-180')} aria-hidden="true" />
      </button>
      <div className="text-center min-w-[200px]">
        <p className="font-semibold text-gray-900">
          {date.toLocaleDateString(isArabic ? 'ar-SA' : 'en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>
        {hijriDate && (
          <p className="text-sm text-gray-500">
            {hijriDate.day} {hijriDate.month.ar} {hijriDate.year}
          </p>
        )}
      </div>
      <button
        onClick={() => onDateChange(1)}
        className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
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

  // State
  const [location, setLocation] = useState<Location | null>(null);
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [showSettings, setShowSettings] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Current time (updates every minute)
  const currentTime = useCurrentTime(60000);

  // Geolocation
  const { state: geoState, getCurrentPosition } = useGeolocation({
    enableHighAccuracy: true,
    timeout: 10000,
  });

  // Initialize location from geolocation
  useEffect(() => {
    if (geoState.coords && !location) {
      reverseGeocode(geoState.coords.latitude, geoState.coords.longitude).then(
        (locationInfo) => {
          setLocation({
            lat: geoState.coords!.latitude,
            lng: geoState.coords!.longitude,
            name: locationInfo?.city
              ? `${locationInfo.city}, ${locationInfo.country}`
              : `${geoState.coords!.latitude.toFixed(2)}, ${geoState.coords!.longitude.toFixed(2)}`,
          });
        }
      );
    }
  }, [geoState.coords, location]);

  // Set default location if geolocation fails
  useEffect(() => {
    if (geoState.error && !location) {
      setLocation({
        ...MAKKAH_LOCATION,
        name: isArabic ? 'مكة المكرمة' : 'Makkah',
      });
    }
  }, [geoState.error, location, isArabic]);

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
          setLocation({
            lat: result.latitude,
            lng: result.longitude,
            name: result.city
              ? `${result.city}, ${result.country}`
              : result.displayName.split(',').slice(0, 2).join(','),
          });
        } else {
          setSearchError(isArabic ? 'لم يتم العثور على الموقع' : 'Location not found');
        }
      } catch {
        setSearchError(isArabic ? 'فشل في البحث عن الموقع' : 'Failed to search location');
      } finally {
        setSearchLoading(false);
      }
    },
    [isArabic]
  );

  // Date change handler
  const handleDateChange = useCallback((days: number) => {
    setSelectedDate((prev) => {
      const newDate = new Date(prev);
      newDate.setDate(newDate.getDate() + days);
      return newDate;
    });
  }, []);

  // Request location on mount if not cached
  useEffect(() => {
    if (!geoState.coords && !geoState.loading && !geoState.error) {
      getCurrentPosition();
    }
  }, [geoState.coords, geoState.loading, geoState.error, getCurrentPosition]);

  return (
    <main
      className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <header className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 focus:outline-none focus:underline"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} aria-hidden="true" />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary-100 rounded-lg" aria-hidden="true">
              <Clock className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isArabic ? 'أوقات الصلاة' : 'Prayer Times'}
              </h1>
              <p className="text-gray-600 flex items-center gap-1">
                <MapPin className="w-4 h-4" aria-hidden="true" />
                <span>
                  {location?.name ||
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
            className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
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

      {/* Location Permission Denied */}
      {geoState.error && !location && (
        <LocationDenied
          onManualEntry={() => setShowSettings(true)}
          className="mb-6"
        />
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
            <QiblaCard direction={qiblaDirection} isArabic={isArabic} />
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
            className="text-primary-600 hover:underline focus:underline focus:outline-none"
          >
            AlAdhan API
          </a>
        </p>
      </footer>
    </main>
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
