/**
 * Quranic Calls Atlas — Whole-Quran Scan Script
 *
 * Scans all 6,236 ayahs in the Quran and detects:
 *   1. Direct يا vocatives
 *   2. Specific audience patterns (يا أيها الذين آمنوا, يا بني إسرائيل, etc.)
 *   3. Supplication forms (ربنا, ربي)
 *   4. Prophet-name calls (يا موسى, يا عيسى, etc.)
 *   5. Family calls (يا أبت, يا بني)
 *   6. Lament/wish forms (يا ويلتى, يا ليت)
 *
 * Outputs:
 *   frontend/src/data/generated/quranicCallsAtlas.json
 *   docs/generated/quranic-calls-atlas-summary.md
 *
 * IMPORTANT:
 *   - Does NOT modify Quran text.
 *   - All caller/addressee/function classifications → needs_review.
 *   - Only pattern confidence is set — NOT theological confidence.
 *   - humanReviewRequired = true for all inferred classifications.
 *
 * Usage:
 *   npx tsx scripts/scan-quranic-calls.ts
 *   npx tsx scripts/scan-quranic-calls.ts --verbose
 */

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { resolve, join, dirname } from 'path';

const args = process.argv.slice(2);
const VERBOSE = args.includes('--verbose');

const ROOT = resolve(__dirname, '..');
const GEN = join(ROOT, 'frontend/src/data/generated');
const OUT_JSON = join(GEN, 'quranicCallsAtlas.json');
const OUT_MD = join(ROOT, 'docs/generated/quranic-calls-atlas-summary.md');
const QURAN_JSON = join(ROOT, 'data/raw/quran_uthmani.json');

// ─── Types (inline to avoid import issues in script context) ──────────────────

interface QuranAyah {
  id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  aya_text: string;        // Uthmani — never modified
  aya_text_emlaey: string; // Emla'i — used for search
  page: number;
  jozz: number;
}

interface EvidenceReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  sourceIds: string[];
  evidenceType: string;
}

interface CallerInfo {
  callerType: string;
  callerEntityId?: string;
  labelArabic?: string;
  labelEnglish?: string;
  confidence: number;
  reviewStatus: string;
}

interface AddresseeInfo {
  addresseeType: string;
  entityId?: string;
  labelArabic: string;
  labelEnglish: string;
  confidence: number;
  reviewStatus: string;
}

interface QuranicCall {
  callId: string;
  surahNumber: number;
  ayahNumber: number;
  ayahReference: string;
  surahNameAr: string;
  surahNameEn: string;
  ayahTextUthmani: string;
  callText?: string;
  callTextUthmani?: string;
  callPattern: string;
  caller: CallerInfo;
  addressee: AddresseeInfo;
  callFunction: string;
  tone: string;
  relatedTopics: string[];
  relatedEntities: string[];
  relatedStories: string[];
  relatedProphets: string[];
  evidenceReferences: EvidenceReference[];
  confidence: number;
  reviewStatus: string;
  humanReviewRequired: boolean;
  warnings: string[];
}

// ─── Diacritic stripping ──────────────────────────────────────────────────────

function stripDiacritics(text: string): string {
  // Remove Arabic tashkeel (vowel marks, shadda, sukun, etc.)
  return text.replace(/[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۤۧۨ-ۭ]/g, '');
}

// ─── Pattern seeds ────────────────────────────────────────────────────────────

interface PatternSeed {
  patternId: string;
  pattern: string;       // stripped form
  callPattern: string;
  addresseeType: string;
  addresseeAr: string;
  addresseeEn: string;
  callerType: string;
  confidence: number;
  isLament?: boolean;
  isSupplication?: boolean;
}

const PATTERNS: PatternSeed[] = [
  // Specific يا أيها patterns (most specific first)
  { patternId: 'p_believers', pattern: 'يا أيها الذين آمنوا', callPattern: 'ya_ayyuhal', addresseeType: 'believers', addresseeAr: 'الذين آمنوا', addresseeEn: 'Believers', callerType: 'allah', confidence: 0.92 },
  { patternId: 'p_people', pattern: 'يا أيها الناس', callPattern: 'ya_ayyuhal', addresseeType: 'mankind', addresseeAr: 'الناس', addresseeEn: 'Mankind', callerType: 'allah', confidence: 0.90 },
  { patternId: 'p_nabi', pattern: 'يا أيها النبي', callPattern: 'ya_ayyuhal', addresseeType: 'prophet', addresseeAr: 'النبي ﷺ', addresseeEn: 'The Prophet ﷺ', callerType: 'allah', confidence: 0.95 },
  { patternId: 'p_rasool', pattern: 'يا أيها الرسول', callPattern: 'ya_ayyuhal', addresseeType: 'prophet', addresseeAr: 'الرسول ﷺ', addresseeEn: 'The Messenger ﷺ', callerType: 'allah', confidence: 0.95 },
  { patternId: 'p_kafiroon', pattern: 'يا أيها الكافرون', callPattern: 'ya_ayyuhal', addresseeType: 'disbelievers', addresseeAr: 'الكافرون', addresseeEn: 'The Disbelievers', callerType: 'allah', confidence: 0.92 },
  { patternId: 'p_muzzammil', pattern: 'يا أيها المزمل', callPattern: 'ya_ayyuhal', addresseeType: 'prophet', addresseeAr: 'المزمل', addresseeEn: 'The Enwrapped (Prophet ﷺ)', callerType: 'allah', confidence: 0.95 },
  { patternId: 'p_muddaththir', pattern: 'يا أيها المدثر', callPattern: 'ya_ayyuhal', addresseeType: 'prophet', addresseeAr: 'المدثر', addresseeEn: 'The Enveloped (Prophet ﷺ)', callerType: 'allah', confidence: 0.95 },
  // يا بني
  { patternId: 'p_bani_israel', pattern: 'يا بني إسرائيل', callPattern: 'ya_bani', addresseeType: 'bani_israel', addresseeAr: 'بني إسرائيل', addresseeEn: 'Children of Israel', callerType: 'allah', confidence: 0.92 },
  { patternId: 'p_bani_adam', pattern: 'يا بني آدم', callPattern: 'ya_bani', addresseeType: 'mankind', addresseeAr: 'بني آدم', addresseeEn: "Children of Adam", callerType: 'allah', confidence: 0.90 },
  // يا أهل
  { patternId: 'p_ahl_kitab', pattern: 'يا أهل الكتاب', callPattern: 'ya_ahl', addresseeType: 'people_of_book', addresseeAr: 'أهل الكتاب', addresseeEn: 'People of the Book', callerType: 'allah', confidence: 0.90 },
  { patternId: 'p_ahl_yathrib', pattern: 'يا أهل يثرب', callPattern: 'ya_ahl', addresseeType: 'people_or_nation', addresseeAr: 'أهل يثرب', addresseeEn: 'People of Yathrib', callerType: 'people_group', confidence: 0.88 },
  // يا عباد
  { patternId: 'p_ibadi', pattern: 'يا عبادي', callPattern: 'ya_ibadi', addresseeType: 'believers', addresseeAr: 'عبادي', addresseeEn: 'My Servants', callerType: 'allah', confidence: 0.90 },
  { patternId: 'p_ibad', pattern: 'يا عباد', callPattern: 'ya_ibadi', addresseeType: 'believers', addresseeAr: 'عباد الله', addresseeEn: 'Servants of Allah', callerType: 'allah', confidence: 0.80 },
  // يا معشر
  { patternId: 'p_mashar_jinn', pattern: 'يا معشر الجن', callPattern: 'ya_ayyuhal', addresseeType: 'jinn', addresseeAr: 'معشر الجن والإنس', addresseeEn: 'Company of Jinn and Mankind', callerType: 'allah', confidence: 0.88 },
  { patternId: 'p_nisaa_nabi', pattern: 'يا نساء النبي', callPattern: 'ya_ayyuhal', addresseeType: 'family_member', addresseeAr: 'نساء النبي', addresseeEn: 'Wives of the Prophet ﷺ', callerType: 'allah', confidence: 0.92 },
  // Prophet names
  { patternId: 'p_musa', pattern: 'يا موسى', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'موسى عليه السلام', addresseeEn: 'Moses ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_isa', pattern: 'يا عيسى', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'عيسى عليه السلام', addresseeEn: 'Jesus ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_maryam', pattern: 'يا مريم', callPattern: 'ya_prophet_name', addresseeType: 'specific_person', addresseeAr: 'مريم عليها السلام', addresseeEn: 'Mary ﷺ', callerType: 'unknown', confidence: 0.85 },
  { patternId: 'p_ibrahim', pattern: 'يا إبراهيم', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'إبراهيم عليه السلام', addresseeEn: 'Abraham ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_nuh', pattern: 'يا نوح', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'نوح عليه السلام', addresseeEn: 'Noah ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_dawud', pattern: 'يا داود', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'داود عليه السلام', addresseeEn: 'David ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_zakariyya', pattern: 'يا زكريا', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'زكريا عليه السلام', addresseeEn: 'Zachariah ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_yahya', pattern: 'يا يحيى', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'يحيى عليه السلام', addresseeEn: 'John ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_adam', pattern: 'يا آدم', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'آدم عليه السلام', addresseeEn: 'Adam ﷺ', callerType: 'allah', confidence: 0.85 },
  { patternId: 'p_yusuf', pattern: 'يا يوسف', callPattern: 'ya_prophet_name', addresseeType: 'prophet', addresseeAr: 'يوسف عليه السلام', addresseeEn: 'Joseph ﷺ', callerType: 'unknown', confidence: 0.80 },
  // Family
  { patternId: 'p_abati', pattern: 'يا أبت', callPattern: 'ya_abati', addresseeType: 'family_member', addresseeAr: 'الأب', addresseeEn: 'Father', callerType: 'unknown', confidence: 0.85 },
  { patternId: 'p_bunayya', pattern: 'يا بني', callPattern: 'ya_bunayya', addresseeType: 'family_member', addresseeAr: 'الابن', addresseeEn: 'Dear Son', callerType: 'unknown', confidence: 0.78 },
  // قوم
  { patternId: 'p_qawmana', pattern: 'يا قومنا', callPattern: 'ya_qawmi', addresseeType: 'people_or_nation', addresseeAr: 'قومنا', addresseeEn: 'Our People', callerType: 'people_group', confidence: 0.78 },
  { patternId: 'p_qawmi', pattern: 'يا قوم', callPattern: 'ya_qawmi', addresseeType: 'people_or_nation', addresseeAr: 'القوم', addresseeEn: 'My People', callerType: 'prophet', confidence: 0.78 },
  // Prison companions
  { patternId: 'p_sahib_sijn', pattern: 'يا صاحبي السجن', callPattern: 'ya_direct', addresseeType: 'specific_person', addresseeAr: 'صاحبا السجن', addresseeEn: 'Prison Companions', callerType: 'prophet', confidence: 0.90 },
  // Lament / wish
  { patternId: 'p_wayla', pattern: 'يا ويلتى', callPattern: 'ya_lament', addresseeType: 'unknown', addresseeAr: 'نداء حزن', addresseeEn: 'Lament', callerType: 'unknown', confidence: 0.88, isLament: true },
  { patternId: 'p_wayla2', pattern: 'يا ويلنا', callPattern: 'ya_lament', addresseeType: 'unknown', addresseeAr: 'نداء حزن', addresseeEn: 'Lament', callerType: 'unknown', confidence: 0.88, isLament: true },
  { patternId: 'p_hasra', pattern: 'يا حسرة', callPattern: 'ya_lament', addresseeType: 'unknown', addresseeAr: 'نداء أسف', addresseeEn: 'Regret', callerType: 'unknown', confidence: 0.88, isLament: true },
  { patternId: 'p_asafa', pattern: 'يا أسفى', callPattern: 'ya_lament', addresseeType: 'unknown', addresseeAr: 'نداء حزن', addresseeEn: 'Grief', callerType: 'unknown', confidence: 0.88, isLament: true },
  { patternId: 'p_layta', pattern: 'يا ليت', callPattern: 'ya_wish', addresseeType: 'unknown', addresseeAr: 'تمنّ', addresseeEn: 'Wish/Regret', callerType: 'unknown', confidence: 0.85, isLament: true },
  // يا + rabbi forms
  { patternId: 'p_ya_rabbi', pattern: 'يا رب', callPattern: 'ya_rabbi', addresseeType: 'allah', addresseeAr: 'الله', addresseeEn: 'Allah (O Lord)', callerType: 'unknown', confidence: 0.82, isSupplication: true },
  // يا أيها (generic — after all specific ones)
  { patternId: 'p_ya_ayyuha', pattern: 'يا أيها', callPattern: 'ya_ayyuhal', addresseeType: 'unknown', addresseeAr: 'غير محدد', addresseeEn: 'Unknown — Context Required', callerType: 'unknown', confidence: 0.65 },
  { patternId: 'p_ya_ayyatuha', pattern: 'يا أيتها', callPattern: 'ya_ayatuha', addresseeType: 'unknown', addresseeAr: 'غير محدد', addresseeEn: 'Unknown — Context Required', callerType: 'unknown', confidence: 0.65 },
  // Supplication forms
  { patternId: 'p_rabbana', pattern: 'ربنا', callPattern: 'supplication', addresseeType: 'allah', addresseeAr: 'الله', addresseeEn: 'Allah (Our Lord)', callerType: 'unknown', confidence: 0.85, isSupplication: true },
  { patternId: 'p_rabbi', pattern: 'ربي', callPattern: 'supplication', addresseeType: 'allah', addresseeAr: 'الله', addresseeEn: 'Allah (My Lord)', callerType: 'unknown', confidence: 0.82, isSupplication: true },
  // Generic يا (lowest priority — catch-all)
  { patternId: 'p_ya_generic', pattern: 'يا ', callPattern: 'ya_direct', addresseeType: 'unknown', addresseeAr: 'غير محدد', addresseeEn: 'Unknown', callerType: 'unknown', confidence: 0.55 },
];

// Sort by pattern length descending (most specific first)
const PATTERNS_SORTED = [...PATTERNS].sort((a, b) => b.pattern.length - a.pattern.length);

// ─── Known prophets for entity linking ───────────────────────────────────────

const PROPHET_NAME_MAP: Record<string, string> = {
  'موسى': 'musa',
  'عيسى': 'isa',
  'مريم': 'maryam',
  'إبراهيم': 'ibrahim',
  'نوح': 'nuh',
  'داود': 'dawud',
  'زكريا': 'zakariyya',
  'يحيى': 'yahya',
  'آدم': 'adam',
  'يوسف': 'yusuf',
  'لوط': 'lut',
  'هود': 'hud',
  'صالح': 'salih',
  'شعيب': 'shuayb',
  'يونس': 'yunus',
  'سليمان': 'sulayman',
  'إسماعيل': 'ismail',
  'إسحاق': 'ishaq',
  'يعقوب': 'yaqub',
  'محمد': 'muhammad',
};

// ─── Main scan logic ──────────────────────────────────────────────────────────

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Find a pattern in stripped Quranic text.
 *
 * For يا-starting patterns we require يا to be a standalone WORD START —
 * it must be preceded by start-of-string, whitespace, or Arabic punctuation.
 * This prevents false positives where يا appears as a suffix in words like
 * "الدنيا" ("الدنيا على" → substring "يا على" would otherwise match).
 *
 * ربنا / ربي patterns do not need this check because they cannot appear as
 * word suffixes in Arabic orthography.
 */
function findMatchInAyah(
  strippedText: string,
  pattern: PatternSeed,
): { found: boolean; matchedPhrase: string } {
  const pat = pattern.pattern;
  let idx = -1;

  if (pat.startsWith('يا')) {
    // Word-boundary check: يا must be preceded by string start, space, or Arabic punctuation
    const re = new RegExp('(?:^|[\\s،؛ۖۗۚۙۛ۩])' + escapeRegex(pat));
    const m = re.exec(strippedText);
    if (m) {
      // m[0] may include a leading boundary char — advance past it
      idx = m.index + (m[0].length - pat.length);
    }
  } else {
    idx = strippedText.indexOf(pat);
  }

  if (idx === -1) return { found: false, matchedPhrase: '' };

  const after = strippedText.slice(idx);
  const sepIdx = after.search(/[،,؛;]/);
  const end = Math.min(sepIdx > 0 ? sepIdx : 50, 50);
  return { found: true, matchedPhrase: after.slice(0, end).trim() };
}

function detectRelatedProphets(strippedText: string): string[] {
  const found: string[] = [];
  for (const [nameAr, nameId] of Object.entries(PROPHET_NAME_MAP)) {
    if (strippedText.includes(nameAr)) found.push(nameId);
  }
  return found;
}

function inferCallFunction(pattern: PatternSeed, strippedText: string): string {
  if (pattern.isSupplication) return 'supplication';
  if (pattern.isLament) return 'lament';
  // Basic signal detection — all need review
  const warningSignals = ['عذاب', 'النار', 'جهنم', 'ويل', 'تخافوا', 'خسر', 'اتقوا'];
  const commandSignals = ['آمنوا', 'اتبعوا', 'أقيموا', 'أطيعوا', 'افعلوا', 'انفقوا'];
  const comfortSignals = ['لا تخف', 'لا تحزن', 'إن الله', 'رحمة', 'غفور'];
  const questionSignals = ['أفلا', 'أتعلمون', 'كيف', 'أين', 'هل'];

  for (const s of warningSignals) { if (strippedText.includes(s)) return 'needs_review'; }
  for (const s of commandSignals) { if (strippedText.includes(s)) return 'needs_review'; }
  for (const s of comfortSignals) { if (strippedText.includes(s)) return 'needs_review'; }
  for (const s of questionSignals) { if (strippedText.includes(s)) return 'needs_review'; }
  return 'needs_review';
}

log('Loading Quran data...');
const quranData: QuranAyah[] = JSON.parse(readFileSync(QURAN_JSON, 'utf-8'));
log(`Loaded ${quranData.length} ayahs across 114 surahs`);

const calls: QuranicCall[] = [];
const warnings: string[] = [];
const ayahCallCount = new Map<string, number>();

for (const ayah of quranData) {
  // Use aya_text_emlaey for pattern matching — it uses standard Arabic alef (ا)
  // instead of Uthmani alef wasla (ٱ), so our plain-text patterns work correctly.
  // aya_text (Uthmani) is preserved unmodified in all output fields.
  const stripped = stripDiacritics(ayah.aya_text_emlaey);
  const ayahKey = `${ayah.sura_no}:${ayah.aya_no}`;
  let callIndexInAyah = 0;

  // Track which patterns have been matched in this ayah to avoid duplicates
  const matchedPatternIds = new Set<string>();

  for (const pattern of PATTERNS_SORTED) {
    // Use the same word-boundary-aware finder for both detection and phrase extraction
    const matchResult = findMatchInAyah(stripped, pattern);
    if (!matchResult.found) continue;

    // Avoid matching sub-patterns of already-matched specific patterns
    const alreadyMatchedMoreSpecific = [...matchedPatternIds].some((pid) => {
      const matched = PATTERNS_SORTED.find((p) => p.patternId === pid);
      return matched && matched.pattern.includes(pattern.pattern) && matched.patternId !== pattern.patternId;
    });
    if (alreadyMatchedMoreSpecific) continue;

    matchedPatternIds.add(pattern.patternId);

    const { matchedPhrase } = matchResult;
    const callId = `call_${ayah.sura_no}_${ayah.aya_no}_${callIndexInAyah}`;
    callIndexInAyah++;

    const relatedProphets = detectRelatedProphets(stripped);
    const callFunction = inferCallFunction(pattern, stripped);

    const call: QuranicCall = {
      callId,
      surahNumber: ayah.sura_no,
      ayahNumber: ayah.aya_no,
      ayahReference: ayahKey,
      surahNameAr: ayah.sura_name_ar,
      surahNameEn: ayah.sura_name_en,
      ayahTextUthmani: ayah.aya_text,  // Original — never modified
      ayahTextEmlaei: ayah.aya_text_emlaey, // Emla'i form — used for signal matching in classify
      callText: matchedPhrase,
      callPattern: pattern.callPattern,
      caller: {
        callerType: pattern.callerType,
        confidence: pattern.callerType === 'unknown' ? 0.3 : pattern.confidence * 0.8,
        reviewStatus: 'needs_review',
        labelArabic: pattern.callerType === 'allah' ? 'الله سبحانه وتعالى' :
                     pattern.callerType === 'prophet' ? 'نبي' : undefined,
        labelEnglish: pattern.callerType === 'allah' ? 'Allah' :
                      pattern.callerType === 'prophet' ? 'Prophet' : undefined,
      },
      addressee: {
        addresseeType: pattern.addresseeType,
        labelArabic: pattern.addresseeAr,
        labelEnglish: pattern.addresseeEn,
        confidence: pattern.confidence,
        reviewStatus: 'needs_review',
      },
      callFunction,
      tone: 'needs_review',
      relatedTopics: [],
      relatedEntities: [],
      relatedStories: [],
      relatedProphets,
      evidenceReferences: [
        {
          surahNumber: ayah.sura_no,
          ayahStart: ayah.aya_no,
          sourceIds: ['quran_text'],
          evidenceType: 'quran_text_pattern',
        },
      ],
      confidence: pattern.confidence,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: pattern.confidence < 0.65
        ? [`Low-confidence pattern match (${pattern.confidence.toFixed(2)}). Context review required.`]
        : [],
    };

    calls.push(call);
    if (VERBOSE) {
      console.log(`  [${ayahKey}] ${pattern.callPattern} → "${matchedPhrase.slice(0, 40)}" (${pattern.addresseeEn})`);
    }
  }

  const count = callIndexInAyah;
  if (count > 0) ayahCallCount.set(ayahKey, count);
}

// ─── Build statistics ─────────────────────────────────────────────────────────

const byPattern: Record<string, number> = {};
const byAddresseeType: Record<string, number> = {};
const byCallerType: Record<string, number> = {};
const bySurah: Record<number, number> = {};

for (const call of calls) {
  byPattern[call.callPattern] = (byPattern[call.callPattern] ?? 0) + 1;
  byAddresseeType[call.addressee.addresseeType] = (byAddresseeType[call.addressee.addresseeType] ?? 0) + 1;
  byCallerType[call.caller.callerType] = (byCallerType[call.caller.callerType] ?? 0) + 1;
  bySurah[call.surahNumber] = (bySurah[call.surahNumber] ?? 0) + 1;
}

const topSurahs = Object.entries(bySurah)
  .sort(([, a], [, b]) => b - a)
  .slice(0, 15)
  .map(([sn, count]) => {
    const surahNum = Number(sn);
    const ayah = quranData.find((a) => a.sura_no === surahNum);
    return { surahNumber: surahNum, surahNameEn: ayah?.sura_name_en ?? '', count };
  });

const directYaCalls = calls.filter((c) =>
  ['ya_direct', 'ya_ayyuhal', 'ya_ayatuha', 'ya_bani', 'ya_qawmi', 'ya_ibadi', 'ya_ahl',
   'ya_rabbi', 'ya_abati', 'ya_bunayya', 'ya_prophet_name', 'ya_lament', 'ya_wish'].includes(c.callPattern)
).length;

const supplicationCalls = calls.filter((c) => c.callPattern === 'supplication').length;
const indirectCalls = calls.filter((c) => ['indirect_address', 'dialogue_address'].includes(c.callPattern)).length;
const needsReview = calls.filter((c) => c.reviewStatus === 'needs_review').length;

const statistics = {
  byPattern,
  byAddresseeType,
  byCallerType,
  byCallFunction: { needs_review: calls.length } as Record<string, number>,
  bySurah,
  topSurahs,
  directYaCalls,
  supplicationCalls,
  indirectCalls,
  needsReview,
  verified: 0,
  totalWarnings: calls.reduce((n, c) => n + c.warnings.length, 0),
};

const atlas = {
  version: '1.0.0-phase-y',
  generatedAt: new Date().toISOString(),
  totalCalls: calls.length,
  totalAyahsWithCalls: ayahCallCount.size,
  statistics,
  calls,
};

// ─── Write outputs ────────────────────────────────────────────────────────────

mkdirSync(GEN, { recursive: true });
mkdirSync(dirname(OUT_MD), { recursive: true });

writeFileSync(OUT_JSON, JSON.stringify(atlas, null, 2), 'utf-8');
log(`\n✓ Written: ${OUT_JSON}`);

// ─── Markdown summary ─────────────────────────────────────────────────────────

const md = `# Quranic Calls Atlas — Scan Summary

Generated: ${atlas.generatedAt}
Version: ${atlas.version}

## Overview

| Metric | Count |
|--------|-------|
| Total call instances | ${atlas.totalCalls} |
| Total ayahs with calls | ${atlas.totalAyahsWithCalls} |
| Direct يا calls | ${directYaCalls} |
| Supplication calls (ربنا/ربي) | ${supplicationCalls} |
| Indirect address candidates | ${indirectCalls} |
| Needs review | ${needsReview} |
| Verified | 0 |
| Warnings | ${statistics.totalWarnings} |

## By Call Pattern

${Object.entries(byPattern).sort(([,a],[,b])=>b-a).map(([k,v]) => `- **${k}**: ${v}`).join('\n')}

## By Addressee Type

${Object.entries(byAddresseeType).sort(([,a],[,b])=>b-a).map(([k,v]) => `- **${k}**: ${v}`).join('\n')}

## By Caller Type

${Object.entries(byCallerType).sort(([,a],[,b])=>b-a).map(([k,v]) => `- **${k}**: ${v}`).join('\n')}

## Top Surahs by Call Count

${topSurahs.map((s, i) => `${i+1}. **${s.surahNameEn}** (${s.surahNumber}): ${s.count} calls`).join('\n')}

## Important Notes

- All caller/addressee/function/tone classifications are \`needs_review\`.
- Only pattern-match confidence is set — NOT theological confidence.
- humanReviewRequired = true for every call.
- No Quran text was modified.
- This is a navigation atlas, NOT a tafsir source.
`;

writeFileSync(OUT_MD, md, 'utf-8');
log(`✓ Written: ${OUT_MD}`);

// ─── Console summary ──────────────────────────────────────────────────────────

console.log('\n' + '='.repeat(60));
console.log('QURANIC CALLS ATLAS — SCAN COMPLETE');
console.log('='.repeat(60));
console.log(`Total calls detected   : ${atlas.totalCalls}`);
console.log(`Ayahs with calls       : ${atlas.totalAyahsWithCalls}`);
console.log(`Direct يا calls        : ${directYaCalls}`);
console.log(`Supplication calls     : ${supplicationCalls}`);
console.log(`Indirect candidates    : ${indirectCalls}`);
console.log(`Needs review           : ${needsReview} (100%)`);
console.log(`Verified               : 0`);
console.log('');
console.log('Top 5 surahs by calls:');
topSurahs.slice(0, 5).forEach((s, i) => {
  console.log(`  ${i+1}. ${s.surahNameEn} (${s.surahNumber}): ${s.count}`);
});
console.log('='.repeat(60));

function log(msg: string) { console.log(msg); }
