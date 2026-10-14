/**
 * Islamic APIs Service
 * Centralized service for all free Islamic APIs
 *
 * Available APIs:
 * - AlAdhan API: Prayer times, Hijri calendar, Qibla direction
 * - AlQuran.cloud: Quran text and translations
 * - EveryAyah: Quran audio files
 * - MP3Quran.net: Reciters and audio
 * - FreeGoldAPI: Gold/Silver prices
 * - Internet Archive: Islamic books search
 * - Nominatim/OSM: Geocoding and place search
 */

import axios from 'axios';

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
        latitude,
        longitude,
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
        latitude,
        longitude,
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
// GOLD & SILVER PRICES API
// https://freegoldapi.com (No API key required)
// ============================================

export interface MetalPrices {
  gold: number; // USD per troy ounce
  silver: number; // USD per troy ounce
  goldPerGram: number;
  silverPerGram: number;
  timestamp: string;
  source: string;
}

// Fallback to static prices if API fails (updated periodically)
const FALLBACK_PRICES: MetalPrices = {
  gold: 2650, // ~$2650/oz as of late 2024
  silver: 31, // ~$31/oz
  goldPerGram: 85.2,
  silverPerGram: 1.0,
  timestamp: new Date().toISOString(),
  source: 'fallback',
};

export async function getMetalPrices(): Promise<MetalPrices> {
  try {
    // Try Gold-API.com free endpoint first
    const response = await axios.get('https://www.goldapi.io/api/XAU/USD', {
      headers: {
        'x-access-token': 'goldapi-demo', // Demo key
      },
      timeout: 5000,
    });

    const goldPricePerOz = response.data.price;

    // Get silver price
    const silverResponse = await axios.get('https://www.goldapi.io/api/XAG/USD', {
      headers: {
        'x-access-token': 'goldapi-demo',
      },
      timeout: 5000,
    });

    const silverPricePerOz = silverResponse.data.price;

    // Convert to grams (1 troy oz = 31.1035 grams)
    const TROY_OZ_TO_GRAMS = 31.1035;

    return {
      gold: goldPricePerOz,
      silver: silverPricePerOz,
      goldPerGram: goldPricePerOz / TROY_OZ_TO_GRAMS,
      silverPerGram: silverPricePerOz / TROY_OZ_TO_GRAMS,
      timestamp: new Date().toISOString(),
      source: 'goldapi.io',
    };
  } catch (error) {
    console.warn('Failed to fetch metal prices, using fallback:', error);
    return FALLBACK_PRICES;
  }
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
    imageUrl: `https://archive.org/services/img/${doc.identifier}`,
    detailsUrl: `https://archive.org/details/${doc.identifier}`,
    readUrl: `https://archive.org/details/${doc.identifier}`,
    downloadUrl: `https://archive.org/download/${doc.identifier}`,
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
    imageUrl: `https://archive.org/services/img/${doc.identifier}`,
    detailsUrl: `https://archive.org/details/${doc.identifier}`,
    readUrl: `https://archive.org/details/${doc.identifier}`,
    downloadUrl: `https://archive.org/download/${doc.identifier}`,
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
        lat: latitude,
        lon: longitude,
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
// RSS FEED PROXY (for CORS)
// Using rss2json.com free tier or allorigins.win
// ============================================

export interface RSSItem {
  title: string;
  link: string;
  description: string;
  pubDate: string;
  author?: string;
  thumbnail?: string;
  categories?: string[];
}

export interface RSSFeed {
  title: string;
  link: string;
  description: string;
  items: RSSItem[];
}

const RSS_FEEDS = {
  muslimmatters: 'https://muslimmatters.org/feed/',
  aboutislam: 'https://aboutislam.net/blog/feed/',
  productivemuslim: 'https://productivemuslim.com/feed/',
  ilmfeed: 'https://ilmfeed.com/feed/',
  yaqeen: 'https://yaqeeninstitute.org/feed/',
} as const;

export async function fetchRSSFeed(feedUrl: string): Promise<RSSFeed | null> {
  try {
    // Use rss2json.com as a CORS proxy (free tier: 10,000 requests/day)
    const response = await axios.get('https://api.rss2json.com/v1/api.json', {
      params: {
        rss_url: feedUrl,
      },
      timeout: 10000,
    });

    if (response.data.status !== 'ok') {
      throw new Error('Failed to parse RSS feed');
    }

    return {
      title: response.data.feed.title,
      link: response.data.feed.link,
      description: response.data.feed.description,
      items: response.data.items.map((item: any) => ({
        title: item.title,
        link: item.link,
        description: item.description?.replace(/<[^>]*>/g, '').slice(0, 300) || '',
        pubDate: item.pubDate,
        author: item.author,
        thumbnail: item.thumbnail || item.enclosure?.link,
        categories: item.categories,
      })),
    };
  } catch (error) {
    console.error('Failed to fetch RSS feed:', error);
    return null;
  }
}

export async function fetchMultipleFeeds(
  sources: Array<keyof typeof RSS_FEEDS>
): Promise<RSSItem[]> {
  const feeds = await Promise.all(
    sources.map((source) => fetchRSSFeed(RSS_FEEDS[source]))
  );

  // Combine and sort by date
  const allItems = feeds
    .filter((feed): feed is RSSFeed => feed !== null)
    .flatMap((feed) =>
      feed.items.map((item) => ({
        ...item,
        source: feed.title,
        sourceUrl: feed.link,
      }))
    );

  return allItems.sort(
    (a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime()
  );
}

export { RSS_FEEDS };

// ============================================
// HELPER FUNCTIONS
// ============================================

// Format relative time
export function formatRelativeTime(dateStr: string, isArabic: boolean): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 60) {
    return isArabic ? `منذ ${diffMins} دقيقة` : `${diffMins} minutes ago`;
  } else if (diffHours < 24) {
    return isArabic ? `منذ ${diffHours} ساعة` : `${diffHours} hours ago`;
  } else if (diffDays < 7) {
    return isArabic ? `منذ ${diffDays} يوم` : `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString(isArabic ? 'ar-SA' : 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}

// Arabic number conversion
export function toArabicNumerals(num: number | string): string {
  const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
  return String(num).replace(/[0-9]/g, (d) => arabicNumerals[parseInt(d)]);
}

// Format prayer time
export function formatPrayerTime(time: string, is24Hour: boolean = false): string {
  if (is24Hour) return time;

  const [hours, minutes] = time.split(':').map(Number);
  const period = hours >= 12 ? 'PM' : 'AM';
  const hour12 = hours % 12 || 12;

  return `${hour12}:${minutes.toString().padStart(2, '0')} ${period}`;
}
