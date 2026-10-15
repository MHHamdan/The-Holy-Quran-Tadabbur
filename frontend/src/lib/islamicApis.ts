/**
 * Islamic APIs Service
 * Centralized service for all free Islamic APIs
 *
 * Available APIs:
 * - AlAdhan API: Prayer times, Hijri calendar, Qibla direction
 * - AlQuran.cloud: Quran text and translations
 * - EveryAyah: Quran audio files
 * - MP3Quran.net: Reciters and audio
 * - Internet Archive: Islamic books search
 * - Nominatim/OSM: Geocoding and place search
 *
 * Location privacy: coordinates are rounded with coarsen() (2 decimals,
 * about 1.1 km) before they leave the device. Full precision is used only
 * on the device itself (Qibla bearing).
 */

import axios from 'axios';

export { safeHttpUrl } from './safeUrl';

/** Round a latitude/longitude to 2 decimals (~1.1 km) before it is sent to
 *  any third-party service. */
export function coarsen(value: number): number {
  return Math.round(value * 100) / 100;
}

// ============================================
// ALADHAN API - Prayer Times & Islamic Calendar
// https://aladhan.com/prayer-times-api
// ============================================

export interface PrayerTimes {
  Fajr: string;
  Sunrise: string;
  Dhuhr: string;
  Asr: string;
  Sunset: string;
  Maghrib: string;
  Isha: string;
  Imsak: string;
  Midnight: string;
  Firstthird: string;
  Lastthird: string;
}

export interface HijriDate {
  date: string;
  format: string;
  day: string;
  weekday: { en: string; ar: string };
  month: { number: number; en: string; ar: string };
  year: string;
  designation: { abbreviated: string; expanded: string };
  holidays: string[];
}

export interface GregorianDate {
  date: string;
  format: string;
  day: string;
  weekday: { en: string };
  month: { number: number; en: string };
  year: string;
}

export interface PrayerTimesResponse {
  timings: PrayerTimes;
  date: {
    readable: string;
    timestamp: string;
    hijri: HijriDate;
    gregorian: GregorianDate;
  };
  meta: {
    latitude: number;
    longitude: number;
    timezone: string;
    method: {
      id: number;
      name: string;
      params: { Fajr: number; Isha: number };
    };
  };
}

// Prayer time calculation methods
export const PRAYER_METHODS = {
  0: { name: 'Shia Ithna-Ashari', name_ar: 'الشيعة الإثني عشرية' },
  1: { name: 'University of Islamic Sciences, Karachi', name_ar: 'جامعة العلوم الإسلامية، كراتشي' },
  2: { name: 'Islamic Society of North America (ISNA)', name_ar: 'الجمعية الإسلامية لأمريكا الشمالية' },
  3: { name: 'Muslim World League', name_ar: 'رابطة العالم الإسلامي' },
  4: { name: 'Umm Al-Qura University, Makkah', name_ar: 'جامعة أم القرى، مكة' },
  5: { name: 'Egyptian General Authority of Survey', name_ar: 'الهيئة المصرية العامة للمساحة' },
  7: { name: 'Institute of Geophysics, University of Tehran', name_ar: 'معهد الجيوفيزياء، جامعة طهران' },
  8: { name: 'Gulf Region', name_ar: 'منطقة الخليج' },
  9: { name: 'Kuwait', name_ar: 'الكويت' },
  10: { name: 'Qatar', name_ar: 'قطر' },
  11: { name: 'Majlis Ugama Islam Singapura, Singapore', name_ar: 'مجلس الشؤون الإسلامية، سنغافورة' },
  12: { name: 'Union Organization Islamic de France', name_ar: 'اتحاد المنظمات الإسلامية في فرنسا' },
  13: { name: 'Diyanet İşleri Başkanlığı, Turkey', name_ar: 'رئاسة الشؤون الدينية، تركيا' },
  14: { name: 'Spiritual Administration of Muslims of Russia', name_ar: 'الإدارة الروحية لمسلمي روسيا' },
  15: { name: 'Moonsighting Committee Worldwide', name_ar: 'لجنة رؤية الهلال العالمية' },
  16: { name: 'Dubai', name_ar: 'دبي' },
} as const;

export async function getPrayerTimes(
  latitude: number,
  longitude: number,
  method: number = 2, // ISNA default
  date?: Date
): Promise<PrayerTimesResponse> {
  const d = date || new Date();
  const dateStr = `${d.getDate()}-${d.getMonth() + 1}-${d.getFullYear()}`;

  const response = await axios.get(
    `https://api.aladhan.com/v1/timings/${dateStr}`,
    {
      params: {
        latitude: coarsen(latitude),
        longitude: coarsen(longitude),
        method,
      },
    }
  );

  return response.data.data;
}

export async function getPrayerTimesForMonth(
  latitude: number,
  longitude: number,
  month: number,
  year: number,
  method: number = 2
): Promise<PrayerTimesResponse[]> {
  const response = await axios.get(
    `https://api.aladhan.com/v1/calendar/${year}/${month}`,
    {
      params: {
        latitude: coarsen(latitude),
        longitude: coarsen(longitude),
        method,
      },
    }
  );

  return response.data.data;
}

// Hijri Calendar Conversion
export async function gregorianToHijri(
  date: string // DD-MM-YYYY format
): Promise<HijriDate> {
  const response = await axios.get(
    `https://api.aladhan.com/v1/gToH/${date}`
  );

  return response.data.data.hijri;
}

export async function hijriToGregorian(
  date: string // DD-MM-YYYY format
): Promise<GregorianDate> {
  const response = await axios.get(
    `https://api.aladhan.com/v1/hToG/${date}`
  );

  return response.data.data.gregorian;
}

export async function getHijriCalendarMonth(
  month: number,
  year: number
): Promise<Array<{ hijri: HijriDate; gregorian: GregorianDate }>> {
  const response = await axios.get(
    `https://api.aladhan.com/v1/hToGCalendar/${month}/${year}`
  );

  return response.data.data;
}

export async function getIslamicHolidays(year: number): Promise<Array<{
  date: string;
  hijriDate: HijriDate;
  holidays: string[];
}>> {
  const response = await axios.get(
    `https://api.aladhan.com/v1/hijriCalendar/${year}`
  );

  // Filter only days with holidays
  return response.data.data
    .filter((day: any) => day.hijri.holidays && day.hijri.holidays.length > 0)
    .map((day: any) => ({
      date: day.gregorian.date,
      hijriDate: day.hijri,
      holidays: day.hijri.holidays,
    }));
}

// ============================================
// GOLD & SILVER PRICES
// ============================================
//
// There is no live price source: the previous client-side call used a public
// demo token that the provider rejects (403), and a real key cannot ship in
// the app. The calculator therefore asks the user for today's price per gram.
// A server-side proxy whose key stays on the server can return live prices
// here later (source !== 'unavailable').

export interface MetalPrices {
  gold: number; // USD per troy ounce
  silver: number; // USD per troy ounce
  goldPerGram: number;
  silverPerGram: number;
  /** ISO date the prices refer to */
  timestamp: string;
  /** 'unavailable' when no live source answered; prices are then 0 */
  source: string;
}

export const TROY_OZ_TO_GRAMS = 31.1035;

export const NO_LIVE_PRICES: MetalPrices = {
  gold: 0,
  silver: 0,
  goldPerGram: 0,
  silverPerGram: 0,
  timestamp: '',
  source: 'unavailable',
};

export async function getMetalPrices(): Promise<MetalPrices> {
  return NO_LIVE_PRICES;
}

/** Prices built from what the user typed (per gram, in their currency). */
export function manualMetalPrices(goldPerGram: number, silverPerGram: number): MetalPrices {
  return {
    gold: goldPerGram * TROY_OZ_TO_GRAMS,
    silver: silverPerGram * TROY_OZ_TO_GRAMS,
    goldPerGram,
    silverPerGram,
    timestamp: new Date().toISOString(),
    source: 'manual',
  };
}

// Nisab calculation helpers
const GOLD_NISAB_GRAMS = 85; // 85 grams of gold
const SILVER_NISAB_GRAMS = 595; // 595 grams of silver

export function calculateNisab(prices: MetalPrices): {
  goldNisab: number;
  silverNisab: number;
  recommendedNisab: number; // Lower of the two (more conservative)
} {
  const goldNisab = GOLD_NISAB_GRAMS * prices.goldPerGram;
  const silverNisab = SILVER_NISAB_GRAMS * prices.silverPerGram;

  return {
    goldNisab,
    silverNisab,
    recommendedNisab: Math.min(goldNisab, silverNisab),
  };
}

// ============================================
// INTERNET ARCHIVE API - Islamic Books
// https://archive.org/advancedsearch.php
// ============================================

export interface ArchiveBook {
  identifier: string;
  title: string;
  creator?: string;
  description?: string;
  date?: string;
  language?: string;
  mediatype: string;
  downloads?: number;
  subjects?: string[];
  imageUrl: string;
  detailsUrl: string;
  readUrl: string;
  downloadUrl?: string;
}

/** archive.org links for an item; the identifier comes from the API and is
 *  URL-encoded so it can only ever form a path segment. */
function archiveUrls(identifier: unknown) {
  const id = encodeURIComponent(String(identifier ?? ''));
  return {
    imageUrl: `https://archive.org/services/img/${id}`,
    detailsUrl: `https://archive.org/details/${id}`,
    readUrl: `https://archive.org/details/${id}`,
    downloadUrl: `https://archive.org/download/${id}`,
  };
}

export async function searchIslamicBooks(
  query: string,
  options: {
    language?: string;
    rows?: number;
    page?: number;
    sort?: 'downloads desc' | 'date desc' | 'titleSorter asc';
  } = {}
): Promise<{ books: ArchiveBook[]; totalResults: number }> {
  const { language, rows = 20, page = 1, sort = 'downloads desc' } = options;

  // Build search query for Islamic books
  let searchQuery = `(${query}) AND (subject:(islam OR islamic OR quran OR hadith OR muslim))`;
  if (language) {
    searchQuery += ` AND language:${language}`;
  }

  const response = await axios.get('https://archive.org/advancedsearch.php', {
    params: {
      q: searchQuery,
      fl: ['identifier', 'title', 'creator', 'description', 'date', 'language', 'mediatype', 'downloads', 'subject'].join(','),
      sort,
      rows,
      page,
      output: 'json',
    },
  });

  const books: ArchiveBook[] = response.data.response.docs.map((doc: any) => ({
    identifier: doc.identifier,
    title: doc.title,
    creator: doc.creator,
    description: Array.isArray(doc.description) ? doc.description[0] : doc.description,
    date: doc.date,
    language: doc.language,
    mediatype: doc.mediatype,
    downloads: doc.downloads,
    subjects: Array.isArray(doc.subject) ? doc.subject : doc.subject ? [doc.subject] : [],
    ...archiveUrls(doc.identifier),
  }));

  return {
    books,
    totalResults: response.data.response.numFound,
  };
}

// Pre-defined Islamic book collections on Internet Archive
export const ISLAMIC_COLLECTIONS = [
  { id: 'CollectionOfIslamicBooks', name_en: 'Collection of Islamic Books', name_ar: 'مجموعة الكتب الإسلامية' },
  { id: 'islamicbookscollection_201907', name_en: 'Largest Islamic Books Collection', name_ar: 'أكبر مجموعة كتب إسلامية' },
  { id: 'islamicbooksfromkalamullahcollection', name_en: 'Kalamullah Collection', name_ar: 'مجموعة كلام الله' },
  { id: 'FreeIslamicBooks-QuranAndSunnahSalaf', name_en: 'Quran & Sunnah Salaf', name_ar: 'القرآن والسنة - السلف' },
] as const;

export async function getCollectionBooks(
  collectionId: string,
  rows: number = 20
): Promise<ArchiveBook[]> {
  const response = await axios.get('https://archive.org/advancedsearch.php', {
    params: {
      q: `collection:${collectionId}`,
      fl: ['identifier', 'title', 'creator', 'description', 'date', 'language', 'mediatype', 'downloads'].join(','),
      sort: 'downloads desc',
      rows,
      output: 'json',
    },
  });

  return response.data.response.docs.map((doc: any) => ({
    identifier: doc.identifier,
    title: doc.title,
    creator: doc.creator,
    description: Array.isArray(doc.description) ? doc.description[0] : doc.description,
    date: doc.date,
    language: doc.language,
    mediatype: doc.mediatype,
    downloads: doc.downloads,
    subjects: [],
    ...archiveUrls(doc.identifier),
  }));
}

// ============================================
// NOMINATIM / OSM API - Geocoding & Places
// https://nominatim.openstreetmap.org
// ============================================

export interface GeoLocation {
  latitude: number;
  longitude: number;
  displayName: string;
  city?: string;
  country?: string;
}

export async function geocodeAddress(address: string): Promise<GeoLocation | null> {
  try {
    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        q: address,
        format: 'json',
        limit: 1,
        addressdetails: 1,
      },
      headers: {
        'User-Agent': 'TadabburApp/1.0',
      },
    });

    if (response.data.length === 0) return null;

    const result = response.data[0];
    return {
      latitude: parseFloat(result.lat),
      longitude: parseFloat(result.lon),
      displayName: result.display_name,
      city: result.address?.city || result.address?.town || result.address?.village,
      country: result.address?.country,
    };
  } catch (error) {
    console.error('Geocoding failed:', error);
    return null;
  }
}

export async function reverseGeocode(
  latitude: number,
  longitude: number
): Promise<GeoLocation | null> {
  try {
    const response = await axios.get('https://nominatim.openstreetmap.org/reverse', {
      params: {
        lat: coarsen(latitude),
        lon: coarsen(longitude),
        format: 'json',
        addressdetails: 1,
      },
      headers: {
        'User-Agent': 'TadabburApp/1.0',
      },
    });

    return {
      latitude,
      longitude,
      displayName: response.data.display_name,
      city: response.data.address?.city || response.data.address?.town || response.data.address?.village,
      country: response.data.address?.country,
    };
  } catch (error) {
    console.error('Reverse geocoding failed:', error);
    return null;
  }
}

// ============================================
// HELPER FUNCTIONS
// ============================================

// Arabic number conversion
export function toArabicNumerals(num: number | string): string {
  const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
  return String(num).replace(/[0-9]/g, (d) => arabicNumerals[parseInt(d)]);
}

/**
 * Format an AlAdhan "HH:mm" (optionally followed by " (TZ)") time for display.
 * Arabic uses Arabic-Indic digits and ص/م (e.g. "٥:١٥ ص"); English uses
 * "5:15 AM". The time is rendered as a wall-clock value (UTC formatting of a
 * fixed date), so the device time zone never shifts it.
 */
export function formatPrayerTime(time: string, is24Hour: boolean = false, language: 'ar' | 'en' = 'en'): string {
  const match = /^(\d{1,2}):(\d{2})/.exec(time.trim());
  if (!match) return time;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  const locale = language === 'ar' ? 'ar-SA-u-nu-arab' : 'en-US';
  try {
    return new Intl.DateTimeFormat(locale, {
      hour: 'numeric',
      minute: '2-digit',
      hour12: !is24Hour,
      timeZone: 'UTC',
    }).format(new Date(Date.UTC(2000, 0, 1, hours, minutes)));
  } catch {
    if (is24Hour) return `${match[1]}:${match[2]}`;
    const hour12 = hours % 12 || 12;
    return `${hour12}:${match[2]} ${hours >= 12 ? 'PM' : 'AM'}`;
  }
}
