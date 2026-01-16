/**
 * Similarity Page - صلة الآيات
 *
 * Dedicated page for exploring verse similarities across the Quran.
 * Features:
 * - Search by verse reference (e.g., 2:255, ٢:٢٥٥, 2 255) or text
 * - Surah name support (البقرة 255, Al-Baqarah 255)
 * - Verse text search with fuzzy matching
 * - Popular verses suggestions
 * - Multi-layered similarity analysis (lexical, thematic, semantic, etc.)
 * - Filters for theme, connection type, minimum score
 * - Results grouped by connection type or theme
 */
import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Link2,
  Search,
  Filter,
  Layers,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  BookOpen,
  BarChart3,
  Tag,
  RefreshCw,
  ArrowRight,
  Sparkles,
  GitBranch,
  HelpCircle,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import {
  quranApi,
  api,
  AdvancedSimilarityResponse,
  AdvancedSimilarityMatch,
  SimilarityScores,
} from '../lib/api';
import { parseAPIError } from '../components/common';

// Local error type for similarity page
interface SimilarityError {
  message: string;
  message_ar: string;
  request_id?: string;
}
import clsx from 'clsx';

// =============================================================================
// Surah Name Mapping (Arabic and English to Number)
// =============================================================================
const SURAH_NAME_MAP: Record<string, number> = {
  // Arabic names
  'الفاتحة': 1, 'البقرة': 2, 'آل عمران': 3, 'النساء': 4, 'المائدة': 5,
  'الأنعام': 6, 'الأعراف': 7, 'الأنفال': 8, 'التوبة': 9, 'يونس': 10,
  'هود': 11, 'يوسف': 12, 'الرعد': 13, 'إبراهيم': 14, 'الحجر': 15,
  'النحل': 16, 'الإسراء': 17, 'الكهف': 18, 'مريم': 19, 'طه': 20,
  'الأنبياء': 21, 'الحج': 22, 'المؤمنون': 23, 'النور': 24, 'الفرقان': 25,
  'الشعراء': 26, 'النمل': 27, 'القصص': 28, 'العنكبوت': 29, 'الروم': 30,
  'لقمان': 31, 'السجدة': 32, 'الأحزاب': 33, 'سبأ': 34, 'فاطر': 35,
  'يس': 36, 'الصافات': 37, 'ص': 38, 'الزمر': 39, 'غافر': 40,
  'فصلت': 41, 'الشورى': 42, 'الزخرف': 43, 'الدخان': 44, 'الجاثية': 45,
  'الأحقاف': 46, 'محمد': 47, 'الفتح': 48, 'الحجرات': 49, 'ق': 50,
  'الذاريات': 51, 'الطور': 52, 'النجم': 53, 'القمر': 54, 'الرحمن': 55,
  'الواقعة': 56, 'الحديد': 57, 'المجادلة': 58, 'الحشر': 59, 'الممتحنة': 60,
  'الصف': 61, 'الجمعة': 62, 'المنافقون': 63, 'التغابن': 64, 'الطلاق': 65,
  'التحريم': 66, 'الملك': 67, 'القلم': 68, 'الحاقة': 69, 'المعارج': 70,
  'نوح': 71, 'الجن': 72, 'المزمل': 73, 'المدثر': 74, 'القيامة': 75,
  'الإنسان': 76, 'المرسلات': 77, 'النبأ': 78, 'النازعات': 79, 'عبس': 80,
  'التكوير': 81, 'الانفطار': 82, 'المطففين': 83, 'الانشقاق': 84, 'البروج': 85,
  'الطارق': 86, 'الأعلى': 87, 'الغاشية': 88, 'الفجر': 89, 'البلد': 90,
  'الشمس': 91, 'الليل': 92, 'الضحى': 93, 'الشرح': 94, 'التين': 95,
  'العلق': 96, 'القدر': 97, 'البينة': 98, 'الزلزلة': 99, 'العاديات': 100,
  'القارعة': 101, 'التكاثر': 102, 'العصر': 103, 'الهمزة': 104, 'الفيل': 105,
  'قريش': 106, 'الماعون': 107, 'الكوثر': 108, 'الكافرون': 109, 'النصر': 110,
  'المسد': 111, 'الإخلاص': 112, 'الفلق': 113, 'الناس': 114,
  // English names (lowercase)
  'fatiha': 1, 'al-fatiha': 1, 'alfatiha': 1,
  'baqarah': 2, 'al-baqarah': 2, 'albaqarah': 2, 'baqara': 2,
  'imran': 3, 'al-imran': 3, 'ali-imran': 3,
  'nisa': 4, 'al-nisa': 4, 'alnisa': 4,
  'maidah': 5, 'al-maidah': 5,
  'anam': 6, 'al-anam': 6,
  'araf': 7, 'al-araf': 7,
  'anfal': 8, 'al-anfal': 8,
  'tawbah': 9, 'al-tawbah': 9, 'taubah': 9,
  'yunus': 10,
  'hud': 11,
  'yusuf': 12, 'joseph': 12,
  'rad': 13, 'al-rad': 13,
  'ibrahim': 14,
  'hijr': 15, 'al-hijr': 15,
  'nahl': 16, 'al-nahl': 16,
  'isra': 17, 'al-isra': 17,
  'kahf': 18, 'al-kahf': 18, 'alkahf': 18,
  'maryam': 19,
  'taha': 20, 'ta-ha': 20,
  'anbiya': 21, 'al-anbiya': 21,
  'hajj': 22, 'al-hajj': 22,
  'muminun': 23, 'al-muminun': 23,
  'nur': 24, 'al-nur': 24,
  'furqan': 25, 'al-furqan': 25,
  'shuara': 26, 'al-shuara': 26,
  'naml': 27, 'al-naml': 27,
  'qasas': 28, 'al-qasas': 28,
  'ankabut': 29, 'al-ankabut': 29,
  'rum': 30, 'al-rum': 30,
  'luqman': 31,
  'sajdah': 32, 'al-sajdah': 32,
  'ahzab': 33, 'al-ahzab': 33,
  'saba': 34,
  'fatir': 35,
  'yasin': 36, 'ya-sin': 36, 'yaseen': 36,
  'saffat': 37, 'al-saffat': 37,
  'sad': 38,
  'zumar': 39, 'al-zumar': 39,
  'ghafir': 40,
  'fussilat': 41,
  'shura': 42, 'al-shura': 42,
  'zukhruf': 43, 'al-zukhruf': 43,
  'dukhan': 44, 'al-dukhan': 44,
  'jathiya': 45, 'al-jathiya': 45,
  'ahqaf': 46, 'al-ahqaf': 46,
  'muhammad': 47,
  'fath': 48, 'al-fath': 48,
  'hujurat': 49, 'al-hujurat': 49,
  'qaf': 50,
  'dhariyat': 51, 'al-dhariyat': 51,
  'tur': 52, 'al-tur': 52,
  'najm': 53, 'al-najm': 53,
  'qamar': 54, 'al-qamar': 54,
  'rahman': 55, 'al-rahman': 55, 'ar-rahman': 55,
  'waqia': 56, 'al-waqia': 56, 'waqiah': 56,
  'hadid': 57, 'al-hadid': 57,
  'mujadila': 58, 'al-mujadila': 58,
  'hashr': 59, 'al-hashr': 59,
  'mumtahina': 60, 'al-mumtahina': 60,
  'saff': 61, 'al-saff': 61,
  'jumua': 62, 'al-jumua': 62, 'jumuah': 62,
  'munafiqun': 63, 'al-munafiqun': 63,
  'taghabun': 64, 'al-taghabun': 64,
  'talaq': 65, 'al-talaq': 65,
  'tahrim': 66, 'al-tahrim': 66,
  'mulk': 67, 'al-mulk': 67,
  'qalam': 68, 'al-qalam': 68,
  'haaqqa': 69, 'al-haaqqa': 69, 'haqqa': 69,
  'maarij': 70, 'al-maarij': 70,
  'nuh': 71, 'noah': 71,
  'jinn': 72, 'al-jinn': 72,
  'muzzammil': 73, 'al-muzzammil': 73,
  'muddathir': 74, 'al-muddathir': 74,
  'qiyama': 75, 'al-qiyama': 75, 'qiyamah': 75,
  'insan': 76, 'al-insan': 76,
  'mursalat': 77, 'al-mursalat': 77,
  'naba': 78, 'al-naba': 78,
  'naziat': 79, 'al-naziat': 79,
  'abasa': 80,
  'takwir': 81, 'al-takwir': 81,
  'infitar': 82, 'al-infitar': 82,
  'mutaffifin': 83, 'al-mutaffifin': 83,
  'inshiqaq': 84, 'al-inshiqaq': 84,
  'buruj': 85, 'al-buruj': 85,
  'tariq': 86, 'al-tariq': 86,
  'ala': 87, 'al-ala': 87,
  'ghashiya': 88, 'al-ghashiya': 88, 'ghashiyah': 88,
  'fajr': 89, 'al-fajr': 89,
  'balad': 90, 'al-balad': 90,
  'shams': 91, 'al-shams': 91,
  'layl': 92, 'al-layl': 92,
  'duha': 93, 'al-duha': 93,
  'sharh': 94, 'al-sharh': 94, 'inshirah': 94,
  'tin': 95, 'al-tin': 95,
  'alaq': 96, 'al-alaq': 96,
  'qadr': 97, 'al-qadr': 97,
  'bayyina': 98, 'al-bayyina': 98, 'bayyinah': 98,
  'zalzala': 99, 'al-zalzala': 99, 'zilzal': 99,
  'adiyat': 100, 'al-adiyat': 100,
  'qaria': 101, 'al-qaria': 101, 'qariah': 101,
  'takathur': 102, 'al-takathur': 102,
  'asr': 103, 'al-asr': 103,
  'humaza': 104, 'al-humaza': 104, 'humazah': 104,
  'fil': 105, 'al-fil': 105,
  'quraysh': 106, 'quraish': 106,
  'maun': 107, 'al-maun': 107,
  'kawthar': 108, 'al-kawthar': 108, 'kausar': 108,
  'kafirun': 109, 'al-kafirun': 109, 'kafiroon': 109,
  'nasr': 110, 'al-nasr': 110,
  'masad': 111, 'al-masad': 111, 'lahab': 111,
  'ikhlas': 112, 'al-ikhlas': 112,
  'falaq': 113, 'al-falaq': 113,
  'nas': 114, 'al-nas': 114,
};

// =============================================================================
// Input Parsing Utilities
// =============================================================================

/**
 * Normalize Arabic digits to Latin digits.
 */
function normalizeArabicDigits(input: string): string {
  const arabicDigits = '٠١٢٣٤٥٦٧٨٩';
  let result = input;
  for (let i = 0; i < arabicDigits.length; i++) {
    result = result.replace(new RegExp(arabicDigits[i], 'g'), String(i));
  }
  return result;
}


/**
 * Parse input to extract surah and ayah numbers.
 * Supports:
 * - "2:255", "2 255", "2,255"
 * - "٢:٢٥٥" (Arabic digits)
 * - "البقرة 255", "البقرة:255"
 * - "Al-Baqarah 255", "baqarah 255"
 * - "سورة البقرة 255"
 *
 * Returns { sura, aya, isTextSearch: false } if reference detected,
 * or { isTextSearch: true, text } if should search by text.
 */
interface ParsedReference {
  sura: number;
  aya: number;
  isTextSearch: false;
}

interface ParsedTextSearch {
  isTextSearch: true;
  text: string;
}

type ParseResult = ParsedReference | ParsedTextSearch;

function parseInput(input: string): ParseResult {
  // Normalize: trim, normalize Arabic digits, collapse whitespace
  let normalized = input.trim();
  normalized = normalizeArabicDigits(normalized);
  normalized = normalized.replace(/\s+/g, ' ');

  // Remove "سورة" prefix if present
  normalized = normalized.replace(/^سورة\s+/i, '');

  // Pattern 1: Direct numeric reference (2:255, 2 255, 2,255, 2-255)
  const numericPattern = /^(\d{1,3})\s*[:،,\-\s]\s*(\d{1,3})$/;
  const numMatch = normalized.match(numericPattern);
  if (numMatch) {
    const sura = parseInt(numMatch[1], 10);
    const aya = parseInt(numMatch[2], 10);
    if (sura >= 1 && sura <= 114 && aya >= 1) {
      return { sura, aya, isTextSearch: false };
    }
  }

  // Pattern 2: Surah name + ayah number
  // Match: "name 255" or "name:255" or "name،255"
  const surahNamePattern = /^([^\d:،,]+?)\s*[:،,]?\s*(\d{1,3})$/;
  const nameMatch = normalized.match(surahNamePattern);
  if (nameMatch) {
    const surahName = nameMatch[1].trim().toLowerCase();
    const aya = parseInt(nameMatch[2], 10);

    // Try Arabic name first (exact match)
    const arabicName = nameMatch[1].trim();
    if (SURAH_NAME_MAP[arabicName]) {
      return { sura: SURAH_NAME_MAP[arabicName], aya, isTextSearch: false };
    }

    // Try English name lookup
    const englishKey = surahName.replace(/^(al-|al)/, '');
    if (SURAH_NAME_MAP[surahName]) {
      return { sura: SURAH_NAME_MAP[surahName], aya, isTextSearch: false };
    }
    if (SURAH_NAME_MAP[englishKey]) {
      return { sura: SURAH_NAME_MAP[englishKey], aya, isTextSearch: false };
    }
    if (SURAH_NAME_MAP[`al-${englishKey}`]) {
      return { sura: SURAH_NAME_MAP[`al-${englishKey}`], aya, isTextSearch: false };
    }
  }

  // Pattern 3: Just a number (might be surah number for ayah 1)
  if (/^\d{1,3}$/.test(normalized)) {
    const num = parseInt(normalized, 10);
    if (num >= 1 && num <= 114) {
      // Ambiguous: could be surah or ayah. Treat as surah:1
      return { sura: num, aya: 1, isTextSearch: false };
    }
  }

  // If input contains Arabic letters and no clear reference pattern, treat as text search
  const hasArabic = /[\u0600-\u06FF]/.test(input);
  if (hasArabic) {
    return { isTextSearch: true, text: input.trim() };
  }

  // Fallback: treat as text search
  return { isTextSearch: true, text: input.trim() };
}

// =============================================================================
// Verse Resolver API Response (Multi-Candidate with Decision Logic)
// =============================================================================
interface ResolveCandidate {
  surah: number;
  ayah: number;
  text_ar: string;
  confidence: number;
  match_type: 'exact' | 'fuzzy' | 'partial';
  highlight_spans: [number, number][];
}

interface ResolveBestMatch {
  surah: number;
  ayah: number;
  text_ar: string;
  confidence: number;
  match_type: 'exact' | 'fuzzy' | 'partial';
}

interface ResolveData {
  query_original: string;
  query_normalized: string;
  mode_detected: 'text';
  best_match: ResolveBestMatch | null;
  candidates: ResolveCandidate[];
  decision: 'auto' | 'needs_user_choice' | 'not_found';
  message_ar?: string;
  message_en?: string;
  warning_ar?: string;
}

interface ResolveResponse {
  ok: boolean;
  data?: ResolveData;
  error?: {
    message: string;
    message_ar: string;
  };
  request_id?: string;
}

// =============================================================================
// Components
// =============================================================================

// Popular verses to explore
const POPULAR_VERSES = [
  { sura: 2, aya: 255, label_ar: 'آية الكرسي', label_en: 'Ayat Al-Kursi' },
  { sura: 1, aya: 1, label_ar: 'الفاتحة', label_en: 'Al-Fatiha' },
  { sura: 36, aya: 1, label_ar: 'يس', label_en: 'Ya-Sin' },
  { sura: 55, aya: 1, label_ar: 'الرحمن', label_en: 'Ar-Rahman' },
  { sura: 112, aya: 1, label_ar: 'الإخلاص', label_en: 'Al-Ikhlas' },
  { sura: 67, aya: 1, label_ar: 'الملك', label_en: 'Al-Mulk' },
  { sura: 18, aya: 1, label_ar: 'الكهف', label_en: 'Al-Kahf' },
  { sura: 2, aya: 286, label_ar: 'آخر البقرة', label_en: 'End of Al-Baqarah' },
];

// Connection type colors and labels
const CONNECTION_TYPES: Record<string, { color: string; label_ar: string; label_en: string }> = {
  lexical: { color: 'bg-blue-100 text-blue-700 border-blue-200', label_ar: 'لفظي', label_en: 'Lexical' },
  thematic: { color: 'bg-purple-100 text-purple-700 border-purple-200', label_ar: 'موضوعي', label_en: 'Thematic' },
  conceptual: { color: 'bg-indigo-100 text-indigo-700 border-indigo-200', label_ar: 'مفاهيمي', label_en: 'Conceptual' },
  grammatical: { color: 'bg-green-100 text-green-700 border-green-200', label_ar: 'نحوي', label_en: 'Grammatical' },
  semantic: { color: 'bg-amber-100 text-amber-700 border-amber-200', label_ar: 'دلالي', label_en: 'Semantic' },
  root_based: { color: 'bg-teal-100 text-teal-700 border-teal-200', label_ar: 'جذري', label_en: 'Root-Based' },
};

// Sentence structure translations
const SENTENCE_STRUCTURES: Record<string, { ar: string; en: string }> = {
  verbal: { ar: 'جملة فعلية', en: 'Verbal Sentence' },
  nominal: { ar: 'جملة اسمية', en: 'Nominal Sentence' },
  conditional: { ar: 'جملة شرطية', en: 'Conditional Sentence' },
  interrogative: { ar: 'جملة استفهامية', en: 'Interrogative Sentence' },
  imperative: { ar: 'جملة أمرية', en: 'Imperative Sentence' },
  unknown: { ar: 'غير محدد', en: 'Unknown' },
};

// Score metric labels
const SCORE_LABELS: Record<keyof Omit<SimilarityScores, 'combined'>, { ar: string; en: string; color: string }> = {
  jaccard: { ar: 'جاكارد', en: 'Jaccard', color: 'bg-blue-500' },
  cosine: { ar: 'كوساين', en: 'Cosine', color: 'bg-green-500' },
  concept_overlap: { ar: 'تداخل المفاهيم', en: 'Concept Overlap', color: 'bg-purple-500' },
  grammatical: { ar: 'نحوي', en: 'Grammatical', color: 'bg-amber-500' },
  semantic: { ar: 'دلالي', en: 'Semantic', color: 'bg-indigo-500' },
  root_based: { ar: 'جذري', en: 'Root-Based', color: 'bg-teal-500' },
};

// Connection strength badge
function ConnectionStrengthBadge({ strength, language }: { strength: string; language: 'ar' | 'en' }) {
  const colors: Record<string, string> = {
    strong: 'bg-green-100 text-green-700',
    moderate: 'bg-yellow-100 text-yellow-700',
    weak: 'bg-gray-100 text-gray-600',
  };
  const labels: Record<string, { ar: string; en: string }> = {
    strong: { ar: 'قوي', en: 'Strong' },
    moderate: { ar: 'متوسط', en: 'Moderate' },
    weak: { ar: 'ضعيف', en: 'Weak' },
  };
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded-full', colors[strength] || colors.weak)}>
      {labels[strength]?.[language] || strength}
    </span>
  );
}

// Score breakdown visualization
function ScoreBreakdown({ scores, language }: { scores: SimilarityScores; language: 'ar' | 'en' }) {
  const metrics = Object.entries(SCORE_LABELS) as [keyof Omit<SimilarityScores, 'combined'>, typeof SCORE_LABELS[keyof typeof SCORE_LABELS]][];

  return (
    <div className="space-y-2">
      {metrics.map(([key, meta]) => {
        const value = scores[key];
        const percent = Math.round(value * 100);
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="text-xs text-gray-600 w-28 truncate" title={meta[language]}>
              {meta[language]}
            </span>
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', meta.color)}
                style={{ width: `${percent}%` }}
              />
            </div>
            <span className="text-xs text-gray-500 w-10 text-right">{percent}%</span>
          </div>
        );
      })}
      <div className="flex items-center gap-2 pt-1 border-t border-gray-100">
        <span className="text-xs font-semibold text-gray-700 w-28">
          {language === 'ar' ? 'المجموع' : 'Combined'}
        </span>
        <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-primary-600 transition-all"
            style={{ width: `${Math.round(scores.combined * 100)}%` }}
          />
        </div>
        <span className="text-xs font-semibold text-primary-700 w-10 text-right">
          {Math.round(scores.combined * 100)}%
        </span>
      </div>
    </div>
  );
}

// Single match card
function MatchCard({
  match,
  isExpanded,
  onToggle,
  language,
}: {
  match: AdvancedSimilarityMatch;
  isExpanded: boolean;
  onToggle: () => void;
  language: 'ar' | 'en';
}) {
  const connectionType = CONNECTION_TYPES[match.connection_type] || CONNECTION_TYPES.semantic;
  const sentenceStructure = SENTENCE_STRUCTURES[match.sentence_structure] || SENTENCE_STRUCTURES.unknown;

  return (
    <div
      className={clsx(
        'border rounded-xl overflow-hidden transition-all',
        isExpanded ? 'ring-2 ring-primary-400 border-primary-300 shadow-lg' : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
      )}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {/* Reference and connection type */}
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <Link
                to={`/quran/${match.sura_no}#${match.aya_no}`}
                className="font-semibold text-primary-700 hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                {match.reference}
              </Link>
              <span className={clsx('text-xs px-2 py-0.5 rounded border', connectionType.color)}>
                {connectionType[`label_${language}`]}
              </span>
              <ConnectionStrengthBadge strength={match.connection_strength} language={language} />
            </div>

            {/* Sura name */}
            <div className="text-sm text-gray-500">
              {language === 'ar' ? match.sura_name_ar : match.sura_name_en}
            </div>
          </div>

          {/* Combined score */}
          <div className="flex items-center gap-3">
            <div className="text-center">
              <div className="text-xl font-bold text-primary-600">
                {Math.round(match.scores.combined * 100)}%
              </div>
              <div className="text-xs text-gray-400">
                {language === 'ar' ? 'تشابه' : 'match'}
              </div>
            </div>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Verse text */}
      <div
        className="px-4 pb-4 text-right font-arabic text-lg leading-relaxed text-gray-800"
        dir="rtl"
      >
        {match.text_uthmani}
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-100 bg-gray-50/50 p-4 space-y-4">
          {/* Shared themes */}
          {match.shared_themes && match.shared_themes.length > 0 && (
            <div>
              <div className="text-xs font-medium text-gray-500 mb-2">
                {language === 'ar' ? 'المواضيع المشتركة:' : 'Shared Themes:'}
              </div>
              <div className="flex flex-wrap gap-2">
                {match.shared_themes.map((theme) => (
                  <span
                    key={theme}
                    className="text-xs px-2 py-1 rounded-full bg-primary-100 text-primary-700"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Shared words and roots */}
          <div className="grid grid-cols-2 gap-4">
            {match.shared_words && match.shared_words.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-2">
                  {language === 'ar' ? 'كلمات مشتركة:' : 'Shared Words:'}
                </div>
                <div className="flex flex-wrap gap-1" dir="rtl">
                  {match.shared_words.slice(0, 6).map((word, i) => (
                    <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                      {word}
                    </span>
                  ))}
                  {match.shared_words.length > 6 && (
                    <span className="text-xs text-gray-400">+{match.shared_words.length - 6}</span>
                  )}
                </div>
              </div>
            )}

            {match.shared_roots && match.shared_roots.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-2">
                  {language === 'ar' ? 'جذور مشتركة:' : 'Shared Roots:'}
                </div>
                <div className="flex flex-wrap gap-1" dir="rtl">
                  {match.shared_roots.slice(0, 6).map((root, i) => (
                    <span key={i} className="text-xs bg-teal-50 text-teal-700 px-2 py-0.5 rounded">
                      {root}
                    </span>
                  ))}
                  {match.shared_roots.length > 6 && (
                    <span className="text-xs text-gray-400">+{match.shared_roots.length - 6}</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sentence structure */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">
              {language === 'ar' ? 'نوع الجملة:' : 'Sentence Type:'}
            </span>
            <span className="text-gray-700 font-medium">
              {sentenceStructure[language]}
            </span>
          </div>

          {/* Similarity explanation */}
          {(match.similarity_explanation_ar || match.similarity_explanation_en) && (
            <div className="text-sm text-gray-600 bg-white rounded-lg p-3 border border-gray-100" dir={language === 'ar' ? 'rtl' : 'ltr'}>
              {language === 'ar' ? match.similarity_explanation_ar : match.similarity_explanation_en}
            </div>
          )}

          {/* Score breakdown */}
          <div className="bg-white rounded-lg p-3 border border-gray-100">
            <div className="text-xs font-medium text-gray-500 mb-3">
              {language === 'ar' ? 'تفصيل درجات التشابه:' : 'Similarity Breakdown:'}
            </div>
            <ScoreBreakdown scores={match.scores} language={language} />
          </div>

          {/* View verse button */}
          <Link
            to={`/quran/${match.sura_no}#${match.aya_no}`}
            className="inline-flex items-center gap-2 text-primary-700 hover:text-primary-800 text-sm font-medium"
          >
            {language === 'ar' ? 'عرض الآية في سياقها' : 'View Verse in Context'}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Candidate Selection Modal
// =============================================================================
function CandidateSelectionModal({
  candidates,
  onSelect,
  onClose,
  language,
  warningAr,
}: {
  candidates: ResolveCandidate[];
  onSelect: (candidate: ResolveCandidate) => void;
  onClose: () => void;
  language: 'ar' | 'en';
  warningAr?: string;
}) {
  const isArabic = language === 'ar';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
        dir={isArabic ? 'rtl' : 'ltr'}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-amber-50 to-yellow-50">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {isArabic ? 'اختر الآية الصحيحة' : 'Select the Correct Verse'}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {isArabic
                  ? 'تم العثور على عدة آيات محتملة. يرجى اختيار الآية المطلوبة.'
                  : 'Multiple possible verses found. Please select the intended verse.'}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-light"
            >
              ×
            </button>
          </div>

          {/* Warning banner for fuzzy matches */}
          {warningAr && (
            <div className="mt-4 p-3 bg-amber-100 border border-amber-300 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-amber-800" dir="rtl">
                  {warningAr}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Candidates list */}
        <div className="overflow-y-auto max-h-[50vh] p-4 space-y-3">
          {candidates.map((candidate, idx) => (
            <button
              key={`${candidate.surah}:${candidate.ayah}`}
              onClick={() => onSelect(candidate)}
              className={clsx(
                'w-full text-start p-4 rounded-xl border-2 transition-all',
                'hover:border-primary-400 hover:bg-primary-50 hover:shadow-md',
                idx === 0
                  ? 'border-primary-300 bg-primary-50/50'
                  : 'border-gray-200 bg-white'
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-primary-700 text-lg">
                    {candidate.surah}:{candidate.ayah}
                  </span>
                  <span
                    className={clsx(
                      'text-xs px-2 py-0.5 rounded-full',
                      candidate.match_type === 'exact'
                        ? 'bg-green-100 text-green-700'
                        : candidate.match_type === 'partial'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-amber-100 text-amber-700'
                    )}
                  >
                    {candidate.match_type === 'exact'
                      ? (isArabic ? 'تطابق تام' : 'Exact')
                      : candidate.match_type === 'partial'
                      ? (isArabic ? 'جزئي' : 'Partial')
                      : (isArabic ? 'تقريبي' : 'Fuzzy')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-primary-600">
                    {Math.round(candidate.confidence * 100)}%
                  </span>
                  <span className="text-xs text-gray-400">
                    {isArabic ? 'ثقة' : 'confidence'}
                  </span>
                </div>
              </div>
              <p
                className="font-arabic text-lg leading-relaxed text-gray-800 line-clamp-2"
                dir="rtl"
              >
                {candidate.text_ar}
              </p>
              {idx === 0 && (
                <div className="mt-2 text-xs text-primary-600 font-medium">
                  {isArabic ? '(مُوصى به)' : '(Recommended)'}
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="btn btn-ghost w-full"
          >
            {isArabic ? 'إلغاء' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Fuzzy Match Warning Banner
// =============================================================================
function FuzzyMatchWarning({ language: _language }: { language: 'ar' | 'en' }) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
      <div className="flex items-start gap-2">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-amber-800" dir="rtl">
          تنبيه: تم مطابقة نص الآية بطريقة تقريبية. يُرجى التأكد من المرجع قبل الاعتماد.
        </p>
      </div>
    </div>
  );
}

// Input format help tooltip
function InputFormatHelp({ language }: { language: 'ar' | 'en' }) {
  const [showHelp, setShowHelp] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={() => setShowHelp(!showHelp)}
        className="text-gray-400 hover:text-gray-600 transition-colors"
        title={language === 'ar' ? 'صيغ الإدخال المدعومة' : 'Supported input formats'}
      >
        <HelpCircle className="w-5 h-5" />
      </button>
      {showHelp && (
        <div
          className="absolute z-50 top-full mt-2 p-4 bg-white rounded-lg shadow-xl border border-gray-200 w-80"
          style={{ [language === 'ar' ? 'right' : 'left']: 0 }}
          dir={language === 'ar' ? 'rtl' : 'ltr'}
        >
          <h4 className="font-semibold text-gray-800 mb-2">
            {language === 'ar' ? 'صيغ الإدخال المدعومة:' : 'Supported Input Formats:'}
          </h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li className="font-mono text-primary-700">2:255</li>
            <li className="font-mono text-primary-700">٢:٢٥٥</li>
            <li className="font-mono text-primary-700">2 255</li>
            <li className="font-mono text-primary-700">البقرة 255</li>
            <li className="font-mono text-primary-700">Al-Baqarah 255</li>
            <li className="text-gray-500 italic">
              {language === 'ar' ? 'أو نص الآية مباشرة' : 'Or verse text directly'}
            </li>
          </ul>
          <button
            onClick={() => setShowHelp(false)}
            className="mt-3 text-xs text-gray-400 hover:text-gray-600"
          >
            {language === 'ar' ? 'إغلاق' : 'Close'}
          </button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function SimilarityPage() {
  const { language } = useLanguageStore();
  const [searchParams, setSearchParams] = useSearchParams();

  const [query, setQuery] = useState(searchParams.get('ref') || '');
  const [suraNo, setSuraNo] = useState<number | null>(null);
  const [ayaNo, setAyaNo] = useState<number | null>(null);
  const [data, setData] = useState<AdvancedSimilarityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<SimilarityError | null>(null);
  const [expandedMatch, setExpandedMatch] = useState<number | null>(null);

  // Candidate selection state
  const [showCandidates, setShowCandidates] = useState(false);
  const [candidates, setCandidates] = useState<ResolveCandidate[]>([]);
  const [candidateWarning, setCandidateWarning] = useState<string | undefined>();
  const [fuzzyWarningShown, setFuzzyWarningShown] = useState(false);

  // Filters
  const [showFilters, setShowFilters] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [selectedConnectionType, setSelectedConnectionType] = useState<string | null>(null);
  const [excludeSameSura, setExcludeSameSura] = useState(false);
  const [minScore, setMinScore] = useState(0.2);
  const [groupBy, setGroupBy] = useState<'none' | 'theme' | 'connection'>('none');

  const isArabic = language === 'ar';

  // Resolve verse text to reference using backend API with decision handling
  const resolveVerseText = useCallback(async (text: string): Promise<{ sura: number; aya: number } | null> => {
    setResolving(true);
    setFuzzyWarningShown(false);

    try {
      const response = await api.get<ResolveResponse>('/quran/resolve', {
        params: { text: text }
      });

      if (response.data.ok && response.data.data) {
        const resolveData = response.data.data;

        // Handle decision logic
        switch (resolveData.decision) {
          case 'auto':
            // Auto-resolve: use best match directly
            if (resolveData.best_match) {
              // Show warning if not exact match
              if (resolveData.best_match.match_type !== 'exact' && resolveData.warning_ar) {
                setFuzzyWarningShown(true);
              }
              return {
                sura: resolveData.best_match.surah,
                aya: resolveData.best_match.ayah
              };
            }
            break;

          case 'needs_user_choice':
            // Show candidate selection modal
            setCandidates(resolveData.candidates);
            setCandidateWarning(resolveData.warning_ar);
            setShowCandidates(true);
            return null; // Don't proceed until user selects

          case 'not_found':
          default:
            // Show error with guidance
            setError({
              message: resolveData.message_en || 'No matching verse found',
              message_ar: resolveData.message_ar || 'لم يتم العثور على آية مطابقة. جرّب إدخال رقم السورة والآية مثل 2:255',
              request_id: response.data.request_id,
            });
            return null;
        }
      }

      // Fallback error
      setError({
        message: response.data.error?.message || 'Verse not found',
        message_ar: response.data.error?.message_ar || 'لم يتم العثور على الآية',
        request_id: response.data.request_id,
      });
      return null;
    } catch (err: unknown) {
      console.error('Failed to resolve verse:', err);
      const axiosError = err as { response?: { data?: { error?: { message?: string; message_ar?: string }; request_id?: string } } };
      setError({
        message: axiosError.response?.data?.error?.message || 'Failed to resolve verse text',
        message_ar: axiosError.response?.data?.error?.message_ar || 'لم يتم العثور على الآية، جرّب إدخال رقم السورة والآية مثل 2:255',
        request_id: axiosError.response?.data?.request_id,
      });
      return null;
    } finally {
      setResolving(false);
    }
  }, []);

  // Load similar verses
  const loadSimilarVerses = useCallback(async (sura: number, aya: number) => {
    setLoading(true);
    setError(null);
    setExpandedMatch(null);

    try {
      const response = await quranApi.getAdvancedSimilarity(sura, aya, {
        top_k: 50,
        min_score: minScore,
        theme: selectedTheme || undefined,
        exclude_same_sura: excludeSameSura,
        connection_type: selectedConnectionType || undefined,
      });
      setData(response.data);
      setSuraNo(sura);
      setAyaNo(aya);
      setSearchParams({ ref: `${sura}:${aya}` });
    } catch (err) {
      console.error('Failed to load similar verses:', err);
      const parsedError = parseAPIError(err);
      setError(parsedError);
    } finally {
      setLoading(false);
    }
  }, [minScore, selectedTheme, excludeSameSura, selectedConnectionType, setSearchParams]);

  // Handle candidate selection from modal
  const handleCandidateSelect = useCallback((candidate: ResolveCandidate) => {
    setShowCandidates(false);
    setCandidates([]);
    setQuery(`${candidate.surah}:${candidate.ayah}`);

    // Show fuzzy warning if not exact match
    if (candidate.match_type !== 'exact') {
      setFuzzyWarningShown(true);
    }

    loadSimilarVerses(candidate.surah, candidate.ayah);
  }, [loadSimilarVerses]);

  // Handle search
  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setError(null);

    const parsed = parseInput(query);

    if (!parsed.isTextSearch) {
      // Direct reference - validate and search
      if (parsed.sura < 1 || parsed.sura > 114) {
        setError({
          message: `Invalid surah number: ${parsed.sura}. Must be 1-114.`,
          message_ar: `رقم السورة غير صحيح: ${parsed.sura}. يجب أن يكون بين 1 و 114.`,
        });
        return;
      }
      loadSimilarVerses(parsed.sura, parsed.aya);
    } else {
      // Text search - resolve first
      const resolved = await resolveVerseText(parsed.text);
      if (resolved) {
        setQuery(`${resolved.sura}:${resolved.aya}`);
        loadSimilarVerses(resolved.sura, resolved.aya);
      }
    }
  }, [query, loadSimilarVerses, resolveVerseText]);

  // Handle popular verse click
  const handlePopularVerseClick = (sura: number, aya: number) => {
    setQuery(`${sura}:${aya}`);
    loadSimilarVerses(sura, aya);
  };

  // Reload when filters change (if already have data)
  useEffect(() => {
    if (suraNo && ayaNo && data) {
      loadSimilarVerses(suraNo, ayaNo);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTheme, selectedConnectionType, excludeSameSura, minScore]);

  // Load from URL params on mount
  useEffect(() => {
    const ref = searchParams.get('ref');
    if (ref) {
      const parsed = parseInput(ref);
      if (!parsed.isTextSearch) {
        setQuery(ref);
        loadSimilarVerses(parsed.sura, parsed.aya);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Group matches
  const groupedMatches = data?.matches ? (() => {
    const matches = data.matches;
    if (groupBy === 'none') {
      return new Map([['all', matches]]);
    }

    const groups = new Map<string, AdvancedSimilarityMatch[]>();
    matches.forEach((match) => {
      const key = groupBy === 'theme' ? (match.primary_theme || 'other') : match.connection_type;
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(match);
    });

    return groups;
  })() : new Map<string, AdvancedSimilarityMatch[]>();

  // Get available themes and connection types
  const availableThemes = data?.theme_distribution ? Object.keys(data.theme_distribution) : [];
  const connectionTypesList = data?.connection_types || [];

  const isSearching = loading || resolving;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Candidate Selection Modal */}
      {showCandidates && candidates.length > 0 && (
        <CandidateSelectionModal
          candidates={candidates}
          onSelect={handleCandidateSelect}
          onClose={() => {
            setShowCandidates(false);
            setCandidates([]);
          }}
          language={language}
          warningAr={candidateWarning}
        />
      )}

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Link2 className="w-8 h-8 text-primary-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {t('similarity_title', language)}
            </h1>
            <p className="text-gray-500 text-sm">
              {t('similarity_subtitle', language)}
            </p>
          </div>
        </div>
      </div>

      {/* Search Box */}
      <div className="card p-6 mb-8">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isSearching && handleSearch()}
              placeholder={isArabic
                ? 'أدخل رقم السورة والآية (مثال: 2:255) أو اكتب نص الآية'
                : 'Enter sura:ayah (e.g., 2:255) or paste verse text'
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-lg pr-10"
              dir={isArabic ? 'rtl' : 'ltr'}
              disabled={isSearching}
            />
            <div className="absolute inset-y-0 right-3 flex items-center">
              <InputFormatHelp language={language} />
            </div>
          </div>
          <button
            onClick={handleSearch}
            disabled={!query.trim() || isSearching}
            className="btn btn-primary px-6 flex items-center gap-2 min-w-[180px] justify-center"
          >
            {isSearching ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {resolving
                  ? (isArabic ? 'جاري البحث عن الآية...' : 'Finding verse...')
                  : (isArabic ? 'جاري البحث...' : 'Searching...')
                }
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                {t('similarity_search_button', language)}
              </>
            )}
          </button>
        </div>

        {/* Popular verses */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-500 mb-3">
            {t('similarity_popular_verses', language)}
          </h3>
          <div className="flex flex-wrap gap-2">
            {POPULAR_VERSES.map((verse) => (
              <button
                key={`${verse.sura}:${verse.aya}`}
                onClick={() => handlePopularVerseClick(verse.sura, verse.aya)}
                disabled={isSearching}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm transition-colors"
              >
                <span className="font-medium">{verse.sura}:{verse.aya}</span>
                <span className="text-gray-500 ml-2">
                  {isArabic ? verse.label_ar : verse.label_en}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6">
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-red-800 font-medium" dir={isArabic ? 'rtl' : 'ltr'}>
                  {isArabic ? error.message_ar : error.message}
                </p>
                {error.request_id && (
                  <p className="text-red-600 text-sm mt-1">
                    Request ID: {error.request_id}
                  </p>
                )}
                <p className="text-red-600 text-sm mt-2" dir={isArabic ? 'rtl' : 'ltr'}>
                  {isArabic
                    ? 'الصيغ المدعومة: 2:255، ٢:٢٥٥، البقرة 255، أو نص الآية'
                    : 'Supported formats: 2:255, 2 255, Al-Baqarah 255, or verse text'
                  }
                </p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-400 hover:text-red-600"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fuzzy Match Warning */}
      {fuzzyWarningShown && data && !error && (
        <FuzzyMatchWarning language={language} />
      )}

      {/* Results */}
      {data && !loading && !error && (
        <div className="space-y-6">
          {/* Source verse info */}
          <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
            <div className="p-4" dir="rtl">
              <div className="flex items-center gap-2 mb-3">
                <BookOpen className="w-5 h-5 text-primary-600" />
                <span className="font-semibold text-primary-700">
                  {data.source_verse.reference} - {isArabic ? data.source_verse.sura_name_ar : data.source_verse.sura_name_en}
                </span>
              </div>
              <p className="font-arabic text-xl leading-relaxed text-gray-800">
                {data.source_verse.text_uthmani}
              </p>
              {data.source_themes && data.source_themes.length > 0 && (
                <div className="flex items-center gap-2 mt-3 flex-wrap">
                  <Tag className="w-4 h-4 text-primary-500" />
                  {data.source_themes.map((theme) => (
                    <span key={theme} className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">
                      {theme}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Stats bar */}
          <div className="flex items-center justify-between bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-primary-600" />
                <span className="text-lg font-bold text-gray-900">{data.total_similar}</span>
                <span className="text-gray-500">{t('similarity_results_count', language)}</span>
              </div>
              <span className="text-sm text-gray-400">|</span>
              <span className="text-sm text-gray-500">
                {isArabic ? 'وقت البحث:' : 'Search time:'} {data.search_time_ms}ms
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={clsx(
                  'btn btn-sm flex items-center gap-2',
                  showFilters ? 'btn-primary' : 'btn-ghost'
                )}
              >
                <Filter className="w-4 h-4" />
                {isArabic ? 'تصفية' : 'Filters'}
              </button>
              <button
                onClick={() => suraNo && ayaNo && loadSimilarVerses(suraNo, ayaNo)}
                className="btn btn-sm btn-ghost"
                title={isArabic ? 'تحديث' : 'Refresh'}
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Filters panel */}
          {showFilters && (
            <div className="card p-4 space-y-4">
              <h4 className="font-medium text-gray-700 flex items-center gap-2">
                <Filter className="w-4 h-4" />
                {isArabic ? 'خيارات التصفية' : 'Filter Options'}
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Theme filter */}
                <div>
                  <label className="text-xs text-gray-500 block mb-1">
                    {t('similarity_filter_theme', language)}
                  </label>
                  <select
                    value={selectedTheme || ''}
                    onChange={(e) => setSelectedTheme(e.target.value || null)}
                    className="w-full text-sm border-gray-200 rounded-md"
                  >
                    <option value="">{isArabic ? 'الكل' : 'All'}</option>
                    {availableThemes.map((theme) => (
                      <option key={theme} value={theme}>
                        {theme}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Connection type filter */}
                <div>
                  <label className="text-xs text-gray-500 block mb-1">
                    {t('similarity_connection_type', language)}
                  </label>
                  <select
                    value={selectedConnectionType || ''}
                    onChange={(e) => setSelectedConnectionType(e.target.value || null)}
                    className="w-full text-sm border-gray-200 rounded-md"
                  >
                    <option value="">{isArabic ? 'الكل' : 'All'}</option>
                    {connectionTypesList.map((ct) => (
                      <option key={ct.id} value={ct.id}>
                        {isArabic ? ct.name_ar : ct.name_en}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Min score */}
                <div>
                  <label className="text-xs text-gray-500 block mb-1">
                    {t('similarity_min_score', language)}: {Math.round(minScore * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="0.8"
                    step="0.1"
                    value={minScore}
                    onChange={(e) => setMinScore(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                {/* Exclude same sura */}
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={excludeSameSura}
                      onChange={(e) => setExcludeSameSura(e.target.checked)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    {t('similarity_exclude_same_sura', language)}
                  </label>
                </div>
              </div>

              {/* Grouping options */}
              <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
                <Layers className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {isArabic ? 'تجميع حسب:' : 'Group by:'}
                </span>
                <select
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value as 'none' | 'theme' | 'connection')}
                  className="text-sm border-gray-200 rounded-md"
                >
                  <option value="none">{isArabic ? 'بدون تجميع' : 'No grouping'}</option>
                  <option value="theme">{isArabic ? 'الموضوع' : 'Theme'}</option>
                  <option value="connection">{isArabic ? 'نوع الصلة' : 'Connection Type'}</option>
                </select>
              </div>
            </div>
          )}

          {/* Theme distribution */}
          {data.theme_distribution && Object.keys(data.theme_distribution).length > 0 && (
            <div className="card p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                <BarChart3 className="w-4 h-4" />
                {isArabic ? 'توزيع المواضيع' : 'Theme Distribution'}
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(data.theme_distribution).slice(0, 10).map(([theme, count]) => (
                  <button
                    key={theme}
                    onClick={() => setSelectedTheme(selectedTheme === theme ? null : theme)}
                    className={clsx(
                      'text-xs rounded-full px-3 py-1 transition-colors',
                      selectedTheme === theme
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                    )}
                  >
                    {theme}: <strong>{count}</strong>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results list */}
          <div className="space-y-4">
            {Array.from(groupedMatches.entries()).map(([group, matches]) => (
              <div key={group}>
                {group !== 'all' && (
                  <div className="flex items-center gap-2 py-3">
                    <div className={clsx(
                      'w-3 h-3 rounded-full',
                      groupBy === 'connection'
                        ? (CONNECTION_TYPES[group]?.color.split(' ')[0] || 'bg-gray-500')
                        : 'bg-primary-500'
                    )} />
                    <h3 className="font-semibold text-gray-700">
                      {groupBy === 'theme'
                        ? group
                        : CONNECTION_TYPES[group]?.[`label_${language}`] || group}
                    </h3>
                    <span className="text-sm text-gray-400">({matches.length})</span>
                  </div>
                )}
                <div className="space-y-4">
                  {matches.map((match) => (
                    <MatchCard
                      key={`${match.sura_no}-${match.aya_no}`}
                      match={match}
                      isExpanded={expandedMatch === (match.sura_no * 1000 + match.aya_no)}
                      onToggle={() =>
                        setExpandedMatch(
                          expandedMatch === (match.sura_no * 1000 + match.aya_no)
                            ? null
                            : match.sura_no * 1000 + match.aya_no
                        )
                      }
                      language={language}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* No results */}
          {data.matches.length === 0 && (
            <div className="text-center py-12 card">
              <GitBranch className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">
                {t('similarity_no_results', language)}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Initial state */}
      {!data && !loading && !error && (
        <div className="text-center py-16 card">
          <Sparkles className="w-16 h-16 mx-auto text-primary-300 mb-6" />
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            {isArabic ? 'اكتشف الروابط بين آيات القرآن' : 'Discover Connections Between Quran Verses'}
          </h2>
          <p className="text-gray-500 max-w-md mx-auto">
            {isArabic
              ? 'أدخل رقم السورة والآية (مثل 2:255) أو اكتب نص الآية لاكتشاف الآيات المتشابهة'
              : 'Enter a sura:verse reference (e.g., 2:255) or paste verse text to discover similar verses'}
          </p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-center py-16 card">
          <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary-600 mb-4" />
          <p className="text-gray-500">
            {isArabic ? 'جارٍ البحث عن الآيات المتشابهة...' : 'Finding similar verses...'}
          </p>
        </div>
      )}

      {/* Navigation links */}
      <div className="mt-12 pt-8 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {isArabic ? 'استكشف المزيد' : 'Explore More'}
        </h3>
        <div className="flex flex-wrap gap-4">
          <Link
            to="/search"
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Search className="w-4 h-4" />
            {isArabic ? 'البحث' : 'Search'}
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/concepts"
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Tag className="w-4 h-4" />
            {isArabic ? 'المفاهيم' : 'Concepts'}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

export default SimilarityPage;
