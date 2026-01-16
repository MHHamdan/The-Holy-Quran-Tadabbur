/**
 * Hijri Calendar Page - FANG Best Practices Implementation
 *
 * Features:
 * - Custom hooks for calendar logic and date conversion
 * - Memoized components for optimal re-renders
 * - Keyboard navigation for calendar grid
 * - Full ARIA accessibility
 * - Error boundary protection
 * - Loading skeletons
 * - Persistent calendar position
 */

import { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Star,
  AlertCircle,
  ArrowRightLeft,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import {
  getHijriCalendarMonth,
  gregorianToHijri,
  hijriToGregorian,
  type HijriDate,
  type GregorianDate,
  toArabicNumerals,
} from '../../lib/islamicApis';
import { useAsync } from '../../hooks/useAsync';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import {
  ErrorBoundary,
  InlineError,
  SkeletonCalendar,
  LoadingSpinner,
} from '../../components/ui';
import clsx from 'clsx';

// ============================================
// Constants
// ============================================

const HIJRI_MONTHS = [
  { number: 1, en: 'Muharram', ar: 'محرم' },
  { number: 2, en: 'Safar', ar: 'صفر' },
  { number: 3, en: "Rabi' al-Awwal", ar: 'ربيع الأول' },
  { number: 4, en: "Rabi' al-Thani", ar: 'ربيع الثاني' },
  { number: 5, en: 'Jumada al-Awwal', ar: 'جمادى الأولى' },
  { number: 6, en: 'Jumada al-Thani', ar: 'جمادى الآخرة' },
  { number: 7, en: 'Rajab', ar: 'رجب' },
  { number: 8, en: "Sha'ban", ar: 'شعبان' },
  { number: 9, en: 'Ramadan', ar: 'رمضان' },
  { number: 10, en: 'Shawwal', ar: 'شوال' },
  { number: 11, en: "Dhu al-Qi'dah", ar: 'ذو القعدة' },
  { number: 12, en: 'Dhu al-Hijjah', ar: 'ذو الحجة' },
] as const;

const ISLAMIC_HOLIDAYS: Record<string, { en: string; ar: string; importance: 'high' | 'medium' }> = {
  '1-1': { en: 'Islamic New Year', ar: 'رأس السنة الهجرية', importance: 'high' },
  '1-10': { en: 'Day of Ashura', ar: 'يوم عاشوراء', importance: 'high' },
  '3-12': { en: 'Mawlid al-Nabi', ar: 'المولد النبوي', importance: 'high' },
  '7-27': { en: "Isra' and Mi'raj", ar: 'الإسراء والمعراج', importance: 'medium' },
  '8-15': { en: "Laylat al-Bara'ah", ar: 'ليلة البراءة', importance: 'medium' },
  '9-1': { en: 'First of Ramadan', ar: 'أول رمضان', importance: 'high' },
  '9-27': { en: 'Laylat al-Qadr (estimated)', ar: 'ليلة القدر (تقديرية)', importance: 'high' },
  '10-1': { en: 'Eid al-Fitr', ar: 'عيد الفطر', importance: 'high' },
  '12-8': { en: 'Day of Tarwiyah', ar: 'يوم التروية', importance: 'medium' },
  '12-9': { en: 'Day of Arafah', ar: 'يوم عرفة', importance: 'high' },
  '12-10': { en: 'Eid al-Adha', ar: 'عيد الأضحى', importance: 'high' },
};

const WEEKDAYS = {
  en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
  ar: ['أحد', 'إثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت'],
} as const;

// ============================================
// Types
// ============================================

interface CalendarDay {
  hijri: HijriDate;
  gregorian: GregorianDate;
  isToday: boolean;
  holiday?: { en: string; ar: string; importance: 'high' | 'medium' };
}

interface CalendarPosition {
  month: number;
  year: number;
}

// ============================================
// Custom Hooks
// ============================================

function useHijriToday() {
  const fetchTodayHijri = useCallback(async () => {
    const today = new Date();
    const dateStr = `${today.getDate()}-${today.getMonth() + 1}-${today.getFullYear()}`;
    return gregorianToHijri(dateStr);
  }, []);

  const result = useAsync(fetchTodayHijri);

  // Auto-execute on mount
  useEffect(() => {
    result.execute();
  }, []);

  return result;
}

function useHijriCalendar(month: number, year: number, todayHijri: HijriDate | null) {
  const fetchCalendar = useCallback(async () => {
    const data = await getHijriCalendarMonth(month, year);

    return data.map((day): CalendarDay => {
      const holidayKey = `${day.hijri.month.number}-${parseInt(day.hijri.day)}`;
      const isToday =
        todayHijri &&
        day.hijri.day === todayHijri.day &&
        day.hijri.month.number === todayHijri.month.number &&
        day.hijri.year === todayHijri.year;

      return {
        hijri: day.hijri,
        gregorian: day.gregorian,
        isToday: !!isToday,
        holiday: ISLAMIC_HOLIDAYS[holidayKey],
      };
    });
  }, [month, year, todayHijri]);

  const result = useAsync(fetchCalendar);

  // Auto-execute when todayHijri is available or when month/year changes
  useEffect(() => {
    if (todayHijri) {
      result.execute();
    }
  }, [todayHijri, month, year]);

  return result;
}

function useDateConverter() {
  const [convertingToHijri, setConvertingToHijri] = useState(false);
  const [convertingToGregorian, setConvertingToGregorian] = useState(false);
  const [result, setResult] = useState<{
    type: 'toHijri' | 'toGregorian';
    result: HijriDate | GregorianDate;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const convertToHijri = useCallback(async (gregorianDate: string) => {
    if (!gregorianDate) return;
    setConvertingToHijri(true);
    setError(null);
    try {
      const hijri = await gregorianToHijri(gregorianDate);
      setResult({ type: 'toHijri', result: hijri });
    } catch (err) {
      setError('Invalid date format. Use DD-MM-YYYY');
    } finally {
      setConvertingToHijri(false);
    }
  }, []);

  const convertToGregorian = useCallback(async (hijriDate: string) => {
    if (!hijriDate) return;
    setConvertingToGregorian(true);
    setError(null);
    try {
      const gregorian = await hijriToGregorian(hijriDate);
      setResult({ type: 'toGregorian', result: gregorian });
    } catch (err) {
      setError('Invalid date format. Use DD-MM-YYYY');
    } finally {
      setConvertingToGregorian(false);
    }
  }, []);

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    convertToHijri,
    convertToGregorian,
    clearResult,
    result,
    error,
    convertingToHijri,
    convertingToGregorian,
  };
}

// ============================================
// Memoized Components
// ============================================

interface TodayCardProps {
  todayHijri: HijriDate;
  isArabic: boolean;
}

const TodayCard = memo(function TodayCard({ todayHijri, isArabic }: TodayCardProps) {
  return (
    <div
      className="mb-6 p-4 bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-xl"
      role="region"
      aria-label={isArabic ? 'التاريخ الهجري اليوم' : "Today's Hijri date"}
    >
      <p className="text-purple-100 text-sm mb-1">{isArabic ? 'اليوم' : 'Today'}</p>
      <p className="text-2xl font-bold" aria-live="polite">
        {todayHijri.weekday.ar} - {todayHijri.day} {todayHijri.month.ar} {todayHijri.year}
      </p>
      <p className="text-purple-100">
        {todayHijri.weekday.en} - {todayHijri.day} {todayHijri.month.en} {todayHijri.year} AH
      </p>
    </div>
  );
});

interface CalendarNavigationProps {
  month: number;
  year: number;
  onPrevious: () => void;
  onNext: () => void;
  isArabic: boolean;
}

const CalendarNavigation = memo(function CalendarNavigation({
  month,
  year,
  onPrevious,
  onNext,
  isArabic,
}: CalendarNavigationProps) {
  const monthInfo = HIJRI_MONTHS.find((m) => m.number === month);

  return (
    <div className="mb-4 flex items-center justify-between" role="navigation" aria-label="Calendar navigation">
      <button
        onClick={onPrevious}
        className="p-2 text-gray-600 hover:text-purple-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        aria-label={isArabic ? 'الشهر السابق' : 'Previous month'}
      >
        <ChevronLeft className={clsx('w-5 h-5', isArabic && 'rotate-180')} aria-hidden="true" />
      </button>
      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-900" aria-live="polite">
          {isArabic ? monthInfo?.ar : monthInfo?.en}{' '}
          {isArabic ? toArabicNumerals(year) : year}
        </h2>
      </div>
      <button
        onClick={onNext}
        className="p-2 text-gray-600 hover:text-purple-600 hover:bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        aria-label={isArabic ? 'الشهر التالي' : 'Next month'}
      >
        <ChevronRight className={clsx('w-5 h-5', isArabic && 'rotate-180')} aria-hidden="true" />
      </button>
    </div>
  );
});

interface CalendarDayCellProps {
  day: CalendarDay;
  isArabic: boolean;
  onKeyDown: (e: React.KeyboardEvent, index: number) => void;
  index: number;
  tabIndex: number;
}

const CalendarDayCell = memo(function CalendarDayCell({
  day,
  isArabic,
  onKeyDown,
  index,
  tabIndex,
}: CalendarDayCellProps) {
  const displayDay = isArabic ? toArabicNumerals(day.hijri.day) : day.hijri.day;
  const gregorianDisplay = `${day.gregorian.day} ${day.gregorian.month.en.slice(0, 3)}`;

  return (
    <div
      role="gridcell"
      tabIndex={tabIndex}
      onKeyDown={(e) => onKeyDown(e, index)}
      aria-label={`${day.hijri.day} ${day.hijri.month.en}, ${gregorianDisplay}${day.holiday ? `, ${day.holiday.en}` : ''}${day.isToday ? ', Today' : ''}`}
      aria-selected={day.isToday}
      className={clsx(
        'p-2 min-h-[80px] border-t border-l border-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-inset cursor-pointer',
        day.isToday && 'bg-purple-50',
        day.holiday?.importance === 'high' && 'bg-green-50',
        day.holiday?.importance === 'medium' && 'bg-amber-50'
      )}
    >
      <div className="flex items-start justify-between">
        <span
          className={clsx(
            'text-lg font-bold',
            day.isToday ? 'text-purple-600' : 'text-gray-900'
          )}
        >
          {displayDay}
        </span>
        {day.holiday && (
          <Star
            className={clsx(
              'w-4 h-4',
              day.holiday.importance === 'high'
                ? 'text-amber-500 fill-amber-500'
                : 'text-amber-400'
            )}
            aria-hidden="true"
          />
        )}
      </div>
      <p className="text-xs text-gray-500 mt-1">{gregorianDisplay}</p>
      {day.holiday && (
        <p className="text-xs text-green-700 mt-1 font-medium truncate">
          {isArabic ? day.holiday.ar : day.holiday.en}
        </p>
      )}
    </div>
  );
});

interface CalendarGridProps {
  days: CalendarDay[];
  isArabic: boolean;
  firstDayOffset: number;
}

const CalendarGrid = memo(function CalendarGrid({
  days,
  isArabic,
  firstDayOffset,
}: CalendarGridProps) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const weekdays = isArabic ? WEEKDAYS.ar : WEEKDAYS.en;

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, index: number) => {
      let newIndex = index;

      switch (e.key) {
        case 'ArrowRight':
          newIndex = isArabic ? index - 1 : index + 1;
          break;
        case 'ArrowLeft':
          newIndex = isArabic ? index + 1 : index - 1;
          break;
        case 'ArrowDown':
          newIndex = index + 7;
          break;
        case 'ArrowUp':
          newIndex = index - 7;
          break;
        case 'Home':
          newIndex = 0;
          break;
        case 'End':
          newIndex = days.length - 1;
          break;
        default:
          return;
      }

      e.preventDefault();
      if (newIndex >= 0 && newIndex < days.length) {
        setFocusedIndex(newIndex);
        const cell = document.querySelector(`[data-day-index="${newIndex}"]`) as HTMLElement;
        cell?.focus();
      }
    },
    [days.length, isArabic]
  );

  return (
    <div
      className="mb-8 bg-white border border-gray-200 rounded-xl overflow-hidden"
      role="grid"
      aria-label={isArabic ? 'التقويم الهجري' : 'Hijri Calendar'}
    >
      <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-200" role="row">
        {weekdays.map((day) => (
          <div
            key={day}
            className="p-2 text-center text-sm font-medium text-gray-600"
            role="columnheader"
          >
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7" role="rowgroup">
        {Array.from({ length: firstDayOffset }).map((_, i) => (
          <div key={`empty-${i}`} className="p-2 min-h-[80px] bg-gray-50" role="gridcell" aria-hidden="true" />
        ))}

        {days.map((day, index) => (
          <div key={index} data-day-index={index}>
            <CalendarDayCell
              day={day}
              isArabic={isArabic}
              onKeyDown={handleKeyDown}
              index={index}
              tabIndex={index === focusedIndex ? 0 : -1}
            />
          </div>
        ))}
      </div>
    </div>
  );
});

interface DateConverterProps {
  onConvertToHijri: (date: string) => void;
  onConvertToGregorian: (date: string) => void;
  convertingToHijri: boolean;
  convertingToGregorian: boolean;
  isArabic: boolean;
}

const DateConverter = memo(function DateConverter({
  onConvertToHijri,
  onConvertToGregorian,
  convertingToHijri,
  convertingToGregorian,
  isArabic,
}: DateConverterProps) {
  const [gregorianInput, setGregorianInput] = useState('');
  const [hijriInput, setHijriInput] = useState('');

  const handleGregorianSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConvertToHijri(gregorianInput);
  };

  const handleHijriSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConvertToGregorian(hijriInput);
  };

  return (
    <div className="grid md:grid-cols-2 gap-6 mb-8">
      <form onSubmit={handleGregorianSubmit} className="card border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <ArrowRightLeft className="w-4 h-4" aria-hidden="true" />
          {isArabic ? 'تحويل من الميلادي للهجري' : 'Gregorian to Hijri'}
        </h3>
        <div className="space-y-3">
          <div>
            <label htmlFor="gregorian-input" className="sr-only">
              {isArabic ? 'التاريخ الميلادي' : 'Gregorian date'}
            </label>
            <input
              id="gregorian-input"
              type="text"
              value={gregorianInput}
              onChange={(e) => setGregorianInput(e.target.value)}
              placeholder="DD-MM-YYYY (e.g., 25-12-2024)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              aria-describedby="gregorian-format"
            />
            <p id="gregorian-format" className="text-xs text-gray-500 mt-1">
              {isArabic ? 'الصيغة: يوم-شهر-سنة' : 'Format: day-month-year'}
            </p>
          </div>
          <button
            type="submit"
            disabled={convertingToHijri || !gregorianInput}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          >
            {convertingToHijri ? (
              <LoadingSpinner size="sm" className="mx-auto" />
            ) : isArabic ? (
              'تحويل'
            ) : (
              'Convert'
            )}
          </button>
        </div>
      </form>

      <form onSubmit={handleHijriSubmit} className="card border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <ArrowRightLeft className="w-4 h-4" aria-hidden="true" />
          {isArabic ? 'تحويل من الهجري للميلادي' : 'Hijri to Gregorian'}
        </h3>
        <div className="space-y-3">
          <div>
            <label htmlFor="hijri-input" className="sr-only">
              {isArabic ? 'التاريخ الهجري' : 'Hijri date'}
            </label>
            <input
              id="hijri-input"
              type="text"
              value={hijriInput}
              onChange={(e) => setHijriInput(e.target.value)}
              placeholder="DD-MM-YYYY (e.g., 01-09-1446)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              aria-describedby="hijri-format"
            />
            <p id="hijri-format" className="text-xs text-gray-500 mt-1">
              {isArabic ? 'الصيغة: يوم-شهر-سنة' : 'Format: day-month-year'}
            </p>
          </div>
          <button
            type="submit"
            disabled={convertingToGregorian || !hijriInput}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          >
            {convertingToGregorian ? (
              <LoadingSpinner size="sm" className="mx-auto" />
            ) : isArabic ? (
              'تحويل'
            ) : (
              'Convert'
            )}
          </button>
        </div>
      </form>
    </div>
  );
});

interface ConversionResultProps {
  result: { type: 'toHijri' | 'toGregorian'; result: HijriDate | GregorianDate };
  error: string | null;
  onClear: () => void;
  isArabic: boolean;
}

const ConversionResult = memo(function ConversionResult({
  result,
  error,
  onClear,
  isArabic,
}: ConversionResultProps) {
  if (error) {
    return (
      <div
        className="mb-8 p-4 bg-red-50 border border-red-200 rounded-xl"
        role="alert"
      >
        <div className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500" aria-hidden="true" />
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div
      className="mb-8 p-4 bg-purple-50 border border-purple-200 rounded-xl"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-purple-900">
          {isArabic ? 'نتيجة التحويل' : 'Conversion Result'}
        </h4>
        <button
          onClick={onClear}
          className="text-sm text-purple-600 hover:text-purple-800 focus:outline-none focus:underline"
          aria-label={isArabic ? 'مسح النتيجة' : 'Clear result'}
        >
          {isArabic ? 'مسح' : 'Clear'}
        </button>
      </div>
      {result.type === 'toHijri' ? (
        <p className="text-purple-800 text-lg">
          {(result.result as HijriDate).day}{' '}
          {(result.result as HijriDate).month.ar} (
          {(result.result as HijriDate).month.en}){' '}
          {(result.result as HijriDate).year} AH
        </p>
      ) : (
        <p className="text-purple-800 text-lg">
          {(result.result as GregorianDate).day}{' '}
          {(result.result as GregorianDate).month.en}{' '}
          {(result.result as GregorianDate).year}
        </p>
      )}
    </div>
  );
});

interface HolidaysLegendProps {
  isArabic: boolean;
}

const HolidaysLegend = memo(function HolidaysLegend({ isArabic }: HolidaysLegendProps) {
  const holidays = useMemo(
    () =>
      Object.entries(ISLAMIC_HOLIDAYS).map(([key, holiday]) => {
        const [month, day] = key.split('-').map(Number);
        const monthInfo = HIJRI_MONTHS.find((m) => m.number === month);
        return { key, day, monthInfo, holiday };
      }),
    []
  );

  return (
    <div className="card border border-gray-200" role="complementary" aria-label={isArabic ? 'المناسبات الإسلامية' : 'Islamic Occasions'}>
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Star className="w-5 h-5 text-amber-500" aria-hidden="true" />
        {isArabic ? 'المناسبات الإسلامية' : 'Islamic Occasions'}
      </h3>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="list">
        {holidays.map(({ key, day, monthInfo, holiday }) => (
          <li key={key} className="flex items-center gap-2 text-sm">
            <Star
              className={clsx(
                'w-4 h-4 flex-shrink-0',
                holiday.importance === 'high'
                  ? 'text-amber-500 fill-amber-500'
                  : 'text-amber-400'
              )}
              aria-hidden="true"
            />
            <span className="text-gray-600">
              {day} {isArabic ? monthInfo?.ar : monthInfo?.en}:
            </span>
            <span className="font-medium text-gray-900">
              {isArabic ? holiday.ar : holiday.en}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
});

// ============================================
// Main Component
// ============================================

function HijriCalendarPageContent() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  // Persistent calendar position
  const [calendarPosition, setCalendarPosition] = useLocalStorage<CalendarPosition>(
    'hijri-calendar-position',
    { month: 1, year: 1446 }
  );

  // Fetch today's Hijri date
  const { data: todayHijri, isPending: todayLoading, error: todayError } = useHijriToday();

  // Update calendar position when today's date is loaded
  useEffect(() => {
    if (todayHijri) {
      setCalendarPosition({
        month: todayHijri.month.number,
        year: parseInt(todayHijri.year),
      });
    }
  }, [todayHijri, setCalendarPosition]);

  // Fetch calendar data
  const {
    data: calendarDays,
    isPending: calendarLoading,
    error: calendarError,
    execute: refetchCalendar,
  } = useHijriCalendar(calendarPosition.month, calendarPosition.year, todayHijri);

  // Date converter
  const {
    convertToHijri,
    convertToGregorian,
    clearResult,
    result: conversionResult,
    error: conversionError,
    convertingToHijri,
    convertingToGregorian,
  } = useDateConverter();

  // Month navigation
  const changeMonth = useCallback(
    (delta: number) => {
      setCalendarPosition((prev) => {
        let newMonth = prev.month + delta;
        let newYear = prev.year;

        if (newMonth > 12) {
          newMonth = 1;
          newYear++;
        } else if (newMonth < 1) {
          newMonth = 12;
          newYear--;
        }

        return { month: newMonth, year: newYear };
      });
    },
    [setCalendarPosition]
  );

  // Calculate first day offset for calendar grid
  const firstDayOffset = useMemo(() => {
    if (!calendarDays || calendarDays.length === 0) return 0;
    const firstDay = calendarDays[0];
    const date = new Date(firstDay.gregorian.date.split('-').reverse().join('-'));
    return date.getDay();
  }, [calendarDays]);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <header className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 focus:outline-none focus:underline"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} aria-hidden="true" />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-purple-100 rounded-lg" aria-hidden="true">
            <Calendar className="w-8 h-8 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isArabic ? 'التقويم الهجري' : 'Hijri Calendar'}
            </h1>
            <p className="text-gray-600">
              {isArabic
                ? 'التقويم الإسلامي ومحول التاريخ'
                : 'Islamic calendar and date converter'}
            </p>
          </div>
        </div>
      </header>

      {/* Today's Date */}
      {todayLoading && (
        <div className="mb-6 animate-pulse">
          <div className="h-28 bg-purple-200 rounded-xl" />
        </div>
      )}
      {todayError && (
        <InlineError
          error={isArabic ? 'فشل في تحميل التاريخ' : 'Failed to load date'}
          className="mb-6"
        />
      )}
      {todayHijri && <TodayCard todayHijri={todayHijri} isArabic={isArabic} />}

      {/* Calendar Navigation */}
      <CalendarNavigation
        month={calendarPosition.month}
        year={calendarPosition.year}
        onPrevious={() => changeMonth(-1)}
        onNext={() => changeMonth(1)}
        isArabic={isArabic}
      />

      {/* Calendar Grid */}
      {calendarLoading && <SkeletonCalendar />}
      {calendarError && (
        <div className="mb-8 p-8 bg-white border border-gray-200 rounded-xl text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" aria-hidden="true" />
          <p className="text-gray-600 mb-4">
            {isArabic ? 'فشل في تحميل التقويم' : 'Failed to load calendar'}
          </p>
          <button
            onClick={() => refetchCalendar()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          >
            {isArabic ? 'إعادة المحاولة' : 'Try again'}
          </button>
        </div>
      )}
      {calendarDays && calendarDays.length > 0 && (
        <CalendarGrid
          days={calendarDays}
          isArabic={isArabic}
          firstDayOffset={firstDayOffset}
        />
      )}

      {/* Date Converter */}
      <DateConverter
        onConvertToHijri={convertToHijri}
        onConvertToGregorian={convertToGregorian}
        convertingToHijri={convertingToHijri}
        convertingToGregorian={convertingToGregorian}
        isArabic={isArabic}
      />

      {/* Conversion Result */}
      {(conversionResult || conversionError) && (
        <ConversionResult
          result={conversionResult!}
          error={conversionError}
          onClear={clearResult}
          isArabic={isArabic}
        />
      )}

      {/* Holidays Legend */}
      <HolidaysLegend isArabic={isArabic} />

      {/* API Attribution */}
      <footer className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 text-center">
        <p>
          {isArabic ? 'البيانات مقدمة من' : 'Data provided by'}{' '}
          <a
            href="https://aladhan.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-purple-600 hover:underline focus:outline-none focus:underline"
          >
            AlAdhan API
          </a>
        </p>
      </footer>
    </div>
  );
}

// ============================================
// Export with Error Boundary
// ============================================

export function HijriCalendarPage() {
  const { language } = useLanguageStore();

  return (
    <ErrorBoundary
      fallback={
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {language === 'ar' ? 'حدث خطأ غير متوقع' : 'Something went wrong'}
          </h2>
          <p className="text-gray-600 mb-4">
            {language === 'ar'
              ? 'يرجى تحديث الصفحة والمحاولة مرة أخرى'
              : 'Please refresh the page and try again'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            {language === 'ar' ? 'تحديث الصفحة' : 'Refresh Page'}
          </button>
        </div>
      }
    >
      <HijriCalendarPageContent />
    </ErrorBoundary>
  );
}
