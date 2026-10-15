/**
 * Surah Memory Atlas — /tools/surah-memory-atlas
 *
 * Redesigned: rich grid, linkable verses, Mushaf links, language-pure rendering,
 * intelligent factual memory clues from verified data only.
 *
 * Content policy:
 * - All ayah text comes from surahMemoryAtlas.json (built from
 *   data/raw/quran_tanzil.json) and is rendered verbatim. Tanzil verse text
 *   never contains the Bismillah (a separate field), so nothing is stripped.
 * - No ayah text is hardcoded here
 * - Makki/Madani is curated metadata; always shown with needs_review badge
 * - Memory clues are generated from verified numeric data only (no AI-generated Islamic content)
 */

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, BookOpen, Brain, X,
  ExternalLink,
  AlertTriangle, Filter, RotateCcw, LayoutGrid,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { scrollBehavior } from '../../hooks/usePrefersReducedMotion';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { Dialog } from '../../components/ui/Dialog';
import clsx from 'clsx';
import atlasData from '../../data/generated/surahMemoryAtlas.json';
import { QuranTextAttribution } from '../../components/quran/QuranTextAttribution';
import type {
  SurahMemoryItem, RevelationType, LengthCategory, QuranPosition, StoryName,
} from '../../types/surahMemoryAtlas';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ViewMode = 'grid' | 'quiz';
type FilterRevelation = 'all' | RevelationType;
type FilterLength = 'all' | LengthCategory;
type FilterPosition = 'all' | QuranPosition;

interface QuizQuestion {
  type: 'before' | 'after' | 'type' | 'length' | 'number' | 'name';
  surah: SurahMemoryItem;
  correctAnswer: string;
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const ATLAS = atlasData as {
  surahs: SurahMemoryItem[];
  storyNames: Record<string, StoryName>;
};
const SURAHS: SurahMemoryItem[] = ATLAS.surahs;
const STORY_NAMES: Record<string, StoryName> = ATLAS.storyNames ?? {};
const MAX_AYAHS = 286; // Al-Baqara — used for relative length bar
const LONGEST_AYAHS = Math.max(...SURAHS.map(s => s.ayahCount));
const SHORTEST_AYAHS = Math.min(...SURAHS.map(s => s.ayahCount));

// ---------------------------------------------------------------------------
// Theme & figure bilingual lookup maps
// ---------------------------------------------------------------------------

const THEME_LABELS: Record<string, { ar: string; en: string }> = {
  patience:            { ar: 'صبر', en: 'Patience' },
  divine_punishment:   { ar: 'عذاب', en: 'Divine Punishment' },
  arrogance:           { ar: 'كبر', en: 'Arrogance' },
  faith:               { ar: 'إيمان', en: 'Faith' },
  repentance:          { ar: 'توبة', en: 'Repentance' },
  warning:             { ar: 'تحذير', en: 'Warning' },
  "da'wah":            { ar: 'دعوة', en: 'Da\'wah' },
  dawah:               { ar: 'دعوة', en: 'Da\'wah' },
  justice:             { ar: 'عدل', en: 'Justice' },
  trial:               { ar: 'ابتلاء', en: 'Trial' },
  sacrifice:           { ar: 'تضحية', en: 'Sacrifice' },
  miracle:             { ar: 'معجزة', en: 'Miracle' },
  miracles:            { ar: 'معجزات', en: 'Miracles' },
  wisdom:              { ar: 'حكمة', en: 'Wisdom' },
  gratitude:           { ar: 'شكر', en: 'Gratitude' },
  disobedience:        { ar: 'عصيان', en: 'Disobedience' },
  destruction:         { ar: 'هلاك', en: 'Destruction' },
  obedience:           { ar: 'طاعة', en: 'Obedience' },
  monotheism:          { ar: 'توحيد', en: 'Monotheism' },
  divine_power:        { ar: 'قدرة إلهية', en: 'Divine Power' },
  rejection:           { ar: 'رفض', en: 'Rejection' },
  trust_in_allah:      { ar: 'توكل', en: 'Trust in Allah' },
  eschatology:         { ar: 'الآخرة', en: 'The Hereafter' },
  divine_plan:         { ar: 'تدبير إلهي', en: 'Divine Plan' },
  divine_planning:     { ar: 'تدبير إلهي', en: 'Divine Planning' },
  righteousness:       { ar: 'بر', en: 'Righteousness' },
  power:               { ar: 'قوة', en: 'Power' },
  courage:             { ar: 'شجاعة', en: 'Courage' },
  signs:               { ar: 'آيات', en: 'Signs' },
  humility:            { ar: 'تواضع', en: 'Humility' },
  resurrection:        { ar: 'بعث', en: 'Resurrection' },
  guidance:            { ar: 'هداية', en: 'Guidance' },
  idolatry:            { ar: 'شرك', en: 'Idolatry' },
  hereafter:           { ar: 'آخرة', en: 'Hereafter' },
  victory:             { ar: 'نصر', en: 'Victory' },
  creation:            { ar: 'خلق', en: 'Creation' },
  salvation:           { ar: 'نجاة', en: 'Salvation' },
  forgiveness:         { ar: 'مغفرة', en: 'Forgiveness' },
  devotion:            { ar: 'عبادة', en: 'Devotion' },
  punishment:          { ar: 'عقوبة', en: 'Punishment' },
  jealousy:            { ar: 'حسد', en: 'Jealousy' },
  revelation:          { ar: 'وحي', en: 'Revelation' },
  martyrdom:           { ar: 'شهادة', en: 'Martyrdom' },
  tyranny:             { ar: 'طغيان', en: 'Tyranny' },
  misguidance:         { ar: 'ضلال', en: 'Misguidance' },
  worldliness:         { ar: 'دنيا', en: 'Worldliness' },
  truth:               { ar: 'حق', en: 'Truth' },
  prophecy:            { ar: 'نبوة', en: 'Prophecy' },
  chastity:            { ar: 'عفة', en: 'Chastity' },
  miraculous_birth:    { ar: 'ولادة معجزية', en: 'Miraculous Birth' },
  purity:              { ar: 'طهارة', en: 'Purity' },
  divine_mercy:        { ar: 'رحمة إلهية', en: 'Divine Mercy' },
  divine_protection:   { ar: 'حفظ إلهي', en: 'Divine Protection' },
  protection:          { ar: 'حماية', en: 'Protection' },
  hypocrisy:           { ar: 'نفاق', en: 'Hypocrisy' },
  hope:                { ar: 'أمل', en: 'Hope' },
  covenant:            { ar: 'ميثاق', en: 'Covenant' },
  betrayal:            { ar: 'خيانة', en: 'Betrayal' },
  disbelief:           { ar: 'كفر', en: 'Disbelief' },
  divine_care:         { ar: 'رعاية إلهية', en: 'Divine Care' },
  divine_support:      { ar: 'نصر إلهي', en: 'Divine Support' },
  confronting_tyranny: { ar: 'مواجهة الطغيان', en: 'Confronting Tyranny' },
  reconciliation:      { ar: 'مصالحة', en: 'Reconciliation' },
  ascension:           { ar: 'رفع', en: 'Ascension' },
  answered_prayer:     { ar: 'استجابة دعاء', en: 'Answered Prayer' },
  kingdom:             { ar: 'ملك', en: 'Kingdom' },
  worship:             { ar: 'عبادة', en: 'Worship' },
  healing:             { ar: 'شفاء', en: 'Healing' },
  trust:               { ar: 'توكل', en: 'Trust' },
  father_of_prophets:  { ar: 'أبو الأنبياء', en: 'Father of Prophets' },
  hajj:                { ar: 'حج', en: 'Hajj' },
  liberation:          { ar: 'تحرر', en: 'Liberation' },
  divine_encounter:    { ar: 'لقاء إلهي', en: 'Divine Encounter' },
  divine_knowledge:    { ar: 'علم إلهي', en: 'Divine Knowledge' },
  perseverance:        { ar: 'مثابرة', en: 'Perseverance' },
  charity:             { ar: 'صدقة', en: 'Charity' },
  divine_kingdom:      { ar: 'ملكوت إلهي', en: 'Divine Kingdom' },
  blessings:           { ar: 'نعم', en: 'Blessings' },
  first_murder:        { ar: 'القتل الأول', en: 'The First Murder' },
  acceptance:          { ar: 'قبول', en: 'Acceptance' },
  kaaba:               { ar: 'الكعبة', en: 'The Ka\'bah' },
  building_kaaba:      { ar: 'بناء الكعبة', en: 'Building the Ka\'bah' },
  leadership:          { ar: 'قيادة', en: 'Leadership' },
  sincerity:           { ar: 'إخلاص', en: 'Sincerity' },
  prayer:              { ar: 'صلاة', en: 'Prayer' },
  migration:           { ar: 'هجرة', en: 'Migration' },
  divine_aid:          { ar: 'نصر إلهي', en: 'Divine Aid' },
  steadfastness:       { ar: 'ثبات', en: 'Steadfastness' },
  ingratitude:         { ar: 'كفر النعمة', en: 'Ingratitude' },
  flood:               { ar: 'الطوفان', en: 'The Flood' },
  magic:               { ar: 'سحر', en: 'Magic' },
  loyalty:             { ar: 'وفاء', en: 'Loyalty' },
  dream_interpretation: { ar: 'تفسير الأحلام', en: 'Dream Interpretation' },
  prophethood:         { ar: 'نبوة', en: 'Prophethood' },
  divine_admonition:   { ar: 'موعظة إلهية', en: 'Divine Admonition' },
  end_times:           { ar: 'نهاية الزمان', en: 'End Times' },
  accountability:      { ar: 'محاسبة', en: 'Accountability' },
  maternal_love:       { ar: 'حب الأم', en: 'Maternal Love' },
  divine_wisdom:       { ar: 'حكمة إلهية', en: 'Divine Wisdom' },
  hidden_knowledge:    { ar: 'علم الغيب', en: 'Hidden Knowledge' },
};

const FIGURE_LABELS: Record<string, { ar: string; en: string }> = {
  Adam: { ar: 'آدم', en: 'Adam' },
  Hawwa: { ar: 'حواء', en: 'Eve (Hawwa)' },
  Iblis: { ar: 'إبليس', en: 'Iblis' },
  Nuh: { ar: 'نوح', en: 'Prophet Nuh' },
  Ibrahim: { ar: 'إبراهيم', en: 'Prophet Ibrahim' },
  Ismail: { ar: 'إسماعيل', en: 'Prophet Ismail' },
  Ishaq: { ar: 'إسحاق', en: 'Prophet Ishaq' },
  Sara: { ar: 'سارة', en: 'Sara' },
  Hajar: { ar: 'هاجر', en: 'Hajar' },
  Namrud: { ar: 'نمرود', en: 'Nimrod' },
  Nimrod: { ar: 'نمرود', en: 'Nimrod' },
  Musa: { ar: 'موسى', en: 'Prophet Musa' },
  Harun: { ar: 'هارون', en: 'Prophet Harun' },
  "Fir'awn": { ar: 'فرعون', en: "Fir'awn" },
  Firawn: { ar: 'فرعون', en: "Fir'awn" },
  'Bani Israel': { ar: 'بنو إسرائيل', en: 'Bani Israel' },
  Asiya: { ar: 'آسية', en: 'Asiya' },
  Yusuf: { ar: 'يوسف', en: 'Prophet Yusuf' },
  Yaqub: { ar: 'يعقوب', en: 'Prophet Yaqub' },
  "Ya'qub": { ar: 'يعقوب', en: 'Prophet Yaqub' },
  Brothers: { ar: 'الإخوة', en: 'The Brothers' },
  Aziz: { ar: 'العزيز', en: 'Al-Aziz' },
  Zulaykha: { ar: 'زليخا', en: 'Zulaykha' },
  Isa: { ar: 'عيسى', en: 'Prophet Isa' },
  Maryam: { ar: 'مريم', en: 'Maryam' },
  Disciples: { ar: 'الحواريون', en: 'The Disciples' },
  Zakariyya: { ar: 'زكريا', en: 'Prophet Zakariyya' },
  Yahya: { ar: 'يحيى', en: 'Prophet Yahya' },
  'Wife of Zakariyya': { ar: 'زوجة زكريا', en: 'Wife of Zakariyya' },
  Sulayman: { ar: 'سليمان', en: 'Prophet Sulayman' },
  'Queen of Sheba': { ar: 'ملكة سبأ', en: 'Queen of Sheba' },
  Bilqis: { ar: 'بلقيس', en: 'Bilqis' },
  Jinn: { ar: 'الجن', en: 'The Jinn' },
  Hoopoe: { ar: 'الهدهد', en: 'The Hoopoe' },
  'Jalut (Goliath)': { ar: 'جالوت', en: 'Goliath' },
  'Talut (Saul)': { ar: 'طالوت', en: 'Saul' },
  Ayyub: { ar: 'أيوب', en: 'Prophet Ayyub' },
  Yunus: { ar: 'يونس', en: 'Prophet Yunus' },
  'People of Madyan': { ar: 'أهل مدين', en: 'People of Madyan' },
  Thamud: { ar: 'ثمود', en: 'Thamud' },
  'People of \'Ad': { ar: 'قوم عاد', en: 'People of \'Ad' },
  'Youth of the Cave': { ar: 'أصحاب الكهف', en: 'People of the Cave' },
  'Dhul-Qarnayn': { ar: 'ذو القرنين', en: 'Dhul-Qarnayn' },
  'Yajuj and Majuj': { ar: 'يأجوج ومأجوج', en: 'Gog and Magog' },
  Luqman: { ar: 'لقمان', en: 'Luqman' },
  Qarun: { ar: 'قارون', en: 'Qarun' },
  'Habil (Abel)': { ar: 'هابيل', en: 'Abel' },
  'Qabil (Cain)': { ar: 'قابيل', en: 'Cain' },
  Dawud: { ar: 'داود', en: 'Prophet Dawud' },
  Lut: { ar: 'لوط', en: 'Prophet Lut' },
  Salih: { ar: 'صالح', en: 'Prophet Salih' },
  Hud: { ar: 'هود', en: 'Prophet Hud' },
  Samiri: { ar: 'السامري', en: 'Al-Samiri' },
  "Shu'ayb": { ar: 'شعيب', en: "Prophet Shu'ayb" },
  Muhammad: { ar: 'محمد ﷺ', en: 'Prophet Muhammad ﷺ' },
  'Abu Bakr': { ar: 'أبو بكر', en: 'Abu Bakr' },
  Khidr: { ar: 'الخضر', en: 'Al-Khidr' },
  Idris: { ar: 'إدريس', en: 'Prophet Idris' },
  'Dhul-Kifl': { ar: 'ذو الكفل', en: 'Dhul-Kifl' },
  Ilyas: { ar: 'إلياس', en: 'Prophet Ilyas' },
  'Al-Yasa': { ar: 'اليسع', en: 'Al-Yasa\'' },
  Haman: { ar: 'هامان', en: 'Haman' },
  Jibril: { ar: 'جبريل', en: 'Jibril' },
  'Mother of Musa': { ar: 'أم موسى', en: 'Mother of Musa' },
  'Believer of Fir\'awn': { ar: 'مؤمن آل فرعون', en: "The Believer of Fir'awn" },
  'Ibn Umm Maktum': { ar: 'ابن أم مكتوم', en: 'Ibn Umm Maktum' },
  'Abu Lahab': { ar: 'أبو لهب', en: 'Abu Lahab' },
};

function themeLabel(key: string, lang: 'ar' | 'en'): string {
  const entry = THEME_LABELS[key];
  if (!entry) return key.replace(/_/g, ' ');
  return lang === 'ar' ? entry.ar : entry.en;
}

function figureLabel(name: string, lang: 'ar' | 'en'): string {
  const entry = FIGURE_LABELS[name];
  if (!entry) return name;
  return lang === 'ar' ? entry.ar : entry.en;
}

// ---------------------------------------------------------------------------
// Pure helpers (no UI)
// ---------------------------------------------------------------------------

const toArabicIndic = (n: number): string =>
  n.toString().replace(/[0-9]/g, d => '٠١٢٣٤٥٦٧٨٩'[+d]);

function displayNum(n: number, lang: 'ar' | 'en'): string {
  return lang === 'ar' ? toArabicIndic(n) : String(n);
}

function revelationGradient(type: RevelationType): string {
  if (type === 'makki') return 'from-amber-500 to-orange-400';
  if (type === 'madani') return 'from-emerald-500 to-teal-400';
  return 'from-slate-500 to-gray-400';
}

function revelationCardRing(type: RevelationType): string {
  if (type === 'makki') return 'ring-amber-400 border-amber-300 shadow-amber-100';
  if (type === 'madani') return 'ring-emerald-400 border-emerald-300 shadow-emerald-100';
  return 'ring-slate-400 border-slate-300 shadow-slate-100';
}

function revelationNumClass(type: RevelationType): string {
  if (type === 'makki') return 'bg-amber-50 text-amber-700';
  if (type === 'madani') return 'bg-emerald-50 text-emerald-700';
  return 'bg-gray-50 text-gray-600';
}

function revelationLabel(type: RevelationType, lang: 'ar' | 'en'): string {
  if (type === 'makki') return t('sma_makki', lang);
  if (type === 'madani') return t('sma_madani', lang);
  return t('sma_unknown', lang);
}

function lengthLabel(cat: LengthCategory, lang: 'ar' | 'en'): string {
  if (cat === 'short') return t('sma_short', lang);
  if (cat === 'medium') return t('sma_medium', lang);
  if (cat === 'long') return t('sma_long', lang);
  return t('sma_very_long', lang);
}

function positionLabel(pos: QuranPosition, lang: 'ar' | 'en'): string {
  if (pos === 'beginning') return t('sma_beginning', lang);
  if (pos === 'early') return t('sma_early', lang);
  if (pos === 'middle') return t('sma_middle', lang);
  if (pos === 'late') return t('sma_late', lang);
  return t('sma_ending', lang);
}

function positionBarColor(pos: QuranPosition): string {
  if (pos === 'beginning') return 'bg-teal-500';
  if (pos === 'early') return 'bg-cyan-500';
  if (pos === 'middle') return 'bg-blue-500';
  if (pos === 'late') return 'bg-indigo-500';
  return 'bg-violet-500';
}

/**
 * Generates a factual memory clue derived exclusively from verified Quran data.
 * No Islamic interpretive content is generated — only structural facts.
 */
function generateIntelligentClue(s: SurahMemoryItem, lang: 'ar' | 'en'): string | null {
  const n = s.surahNumber;

  // Only structural facts computed from the bundled Tanzil-derived data.
  // Hand-written notes about individual surahs were removed: several were
  // wrong (juz ranges, refrain counts, misattributed verses) and none had a
  // reviewed source.
  if (n === 1) {
    return lang === 'ar' ? 'أول سورة في ترتيب المصحف' : 'First surah in the order of the Mushaf';
  }
  if (n === SURAHS.length) {
    return lang === 'ar' ? 'آخر سورة في ترتيب المصحف' : 'Last surah in the order of the Mushaf';
  }
  if (s.ayahCount === LONGEST_AYAHS) {
    return lang === 'ar'
      ? `أطول سورة بعدد الآيات: ${toArabicIndic(s.ayahCount)} آية`
      : `Longest surah by ayah count: ${s.ayahCount} ayahs`;
  }
  if (s.ayahCount === SHORTEST_AYAHS) {
    return lang === 'ar'
      ? `من أقصر السور بعدد الآيات: ${toArabicIndic(s.ayahCount)} آيات`
      : `Among the shortest surahs by ayah count: ${s.ayahCount} ayahs`;
  }

  // Single-page surah (fits entirely on one Mushaf page)
  if (s.pageStart === s.pageEnd) {
    return lang === 'ar'
      ? `تقع كاملةً في صفحة ${toArabicIndic(s.pageStart)} من المصحف`
      : `Fits entirely on page ${s.pageStart} of the Mushaf`;
  }

  // Very long (spans many pages)
  const pages = s.pageEnd - s.pageStart + 1;
  if (pages >= 15) {
    return lang === 'ar'
      ? `سورة طويلة — تمتد على ${toArabicIndic(pages)} صفحة من المصحف`
      : `Long surah — spans ${pages} pages of the Mushaf`;
  }

  // Entirely within one juz
  if (s.juzStart === s.juzEnd) {
    return lang === 'ar'
      ? `ضمن الجزء ${toArabicIndic(s.juzStart)} كاملاً`
      : `Falls entirely within Juz ${s.juzStart}`;
  }

  return lang === 'ar'
    ? `تمتد من الجزء ${toArabicIndic(s.juzStart)} إلى الجزء ${toArabicIndic(s.juzEnd)} (الصفحات ${toArabicIndic(s.pageStart)}–${toArabicIndic(s.pageEnd)})`
    : `Spans Juz ${s.juzStart}–${s.juzEnd} (pages ${s.pageStart}–${s.pageEnd})`;
}

function generateQuestion(surahs: SurahMemoryItem[]): QuizQuestion {
  const types: QuizQuestion['type'][] = ['before', 'after', 'type', 'length', 'number', 'name'];
  const type = types[Math.floor(Math.random() * types.length)];
  const idx = Math.floor(Math.random() * surahs.length);
  const surah = surahs[idx];

  let correctAnswer = '';
  if (type === 'before') {
    correctAnswer = surah.surahNumber === 1
      ? 'none'
      : surahs.find(s => s.surahNumber === surah.surahNumber - 1)?.nameTransliteration ?? 'none';
  } else if (type === 'after') {
    correctAnswer = surah.surahNumber === 114
      ? 'none'
      : surahs.find(s => s.surahNumber === surah.surahNumber + 1)?.nameTransliteration ?? 'none';
  } else if (type === 'type') {
    correctAnswer = surah.revelationType;
  } else if (type === 'length') {
    correctAnswer = surah.lengthCategory;
  } else if (type === 'number') {
    correctAnswer = String(surah.surahNumber);
  } else {
    correctAnswer = surah.nameTransliteration;
  }

  return { type, surah, correctAnswer };
}

// ---------------------------------------------------------------------------
// SurahCard — grid tile
// ---------------------------------------------------------------------------

function SurahCard({
  surah, selected, onClick, language,
}: {
  surah: SurahMemoryItem;
  selected: boolean;
  onClick: () => void;
  language: 'ar' | 'en';
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      className={clsx(
        'group relative rounded-xl overflow-hidden cursor-pointer transition-all duration-200',
        'border-2 bg-white focus:outline-none',
        selected
          ? clsx('ring-2 ring-offset-1 shadow-lg', revelationCardRing(surah.revelationType))
          : 'border-gray-100 hover:border-gray-200 hover:shadow-md hover:-translate-y-0.5',
      )}
    >
      {/* Revelation color top bar */}
      <div className={clsx('h-1.5 w-full bg-gradient-to-r', revelationGradient(surah.revelationType))} />

      {/* Card body */}
      <div className="p-2.5 flex flex-col items-center text-center gap-1.5">
        {/* Surah number */}
        <span className={clsx(
          'text-xs font-bold w-7 h-7 rounded-full flex items-center justify-center shrink-0',
          revelationNumClass(surah.revelationType),
        )}>
          {displayNum(surah.surahNumber, language)}
        </span>

        {/* Arabic name */}
        <div className="font-arabic text-base leading-snug text-gray-900 w-full" dir="rtl">
          {surah.nameArabic}
        </div>

        {/* Transliteration — language pure */}
        {language === 'en' && (
          <div className="text-[10px] text-gray-500 truncate w-full" dir="ltr">
            {surah.nameTransliteration}
          </div>
        )}

        {/* Ayah count */}
        <div className="text-[10px] text-gray-400">
          {displayNum(surah.ayahCount, language)} {t('sma_ayahs_short', language)}
        </div>
      </div>

      {/* Hover overlay: first ayah preview */}
      {surah.firstAyahPreview && (
        <div
          className={clsx(
            'absolute inset-0 rounded-xl bg-gradient-to-b',
            surah.revelationType === 'makki'
              ? 'from-amber-900/80 to-amber-950/90'
              : surah.revelationType === 'madani'
                ? 'from-emerald-900/80 to-emerald-950/90'
                : 'from-slate-900/80 to-slate-950/90',
            'opacity-0 group-hover:opacity-100 transition-opacity duration-200',
            'flex flex-col items-center justify-center p-2 gap-2',
          )}
          aria-hidden="true"
        >
          <p className="font-mushaf text-white text-xs leading-relaxed text-center line-clamp-4" dir="rtl">
            {surah.firstAyahPreview}
          </p>
          <Link
            to={`/quran/${surah.surahNumber}`}
            onClick={e => e.stopPropagation()}
            className="flex items-center gap-1 text-white/80 hover:text-white text-[10px] transition-colors"
            dir="ltr"
          >
            <ExternalLink className="w-2.5 h-2.5" />
            {t('sma_read_in_quran', language)}
          </Link>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AyahBlock — single ayah display with ref and link
// ---------------------------------------------------------------------------

function AyahBlock({
  text, ref_, aya, surahNumber,
}: {
  text: string;
  ref_: string;
  aya: number;
  surahNumber: number;
}) {
  return (
    <div className="group relative">
      <div
        className="font-mushaf text-gray-800 text-base leading-loose bg-gray-50 rounded-lg px-3 pt-2 pb-6 border border-gray-100"
        dir="rtl"
      >
        {text}
      </div>
      <Link
        to={`/quran/${surahNumber}?aya=${aya}`}
        className="absolute bottom-1.5 start-2 inline-flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-700 transition-colors opacity-70 group-hover:opacity-100"
      >
        <BookOpen className="w-2.5 h-2.5" />
        {ref_}
      </Link>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SurahDetailPanel — rich info sidebar / bottom sheet
// ---------------------------------------------------------------------------

function SurahDetailPanel({
  surah, surahs, onClose, onNavigate, language,
}: {
  surah: SurahMemoryItem;
  surahs: SurahMemoryItem[];
  onClose: () => void;
  onNavigate: (n: number) => void;
  language: 'ar' | 'en';
}) {
  const prevSurah = surahs.find(s => s.surahNumber === surah.surahNumber - 1);
  const nextSurah = surahs.find(s => s.surahNumber === surah.surahNumber + 1);
  const clue = generateIntelligentClue(surah, language);
  const positionPct = ((surah.surahNumber - 1) / 113) * 100;
  const lengthPct = Math.min((surah.ayahCount / MAX_AYAHS) * 100, 100);

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className={clsx(
        'shrink-0 bg-gradient-to-br p-5 text-white relative',
        surah.revelationType === 'makki'
          ? 'from-amber-600 to-orange-500'
          : surah.revelationType === 'madani'
            ? 'from-emerald-600 to-teal-500'
            : 'from-slate-600 to-gray-500',
      )}>
        <button
          onClick={onClose}
          className="absolute top-3 end-3 p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
          aria-label={t('sma_close_panel', language)}
        >
          <X className="w-4 h-4 text-white" />
        </button>

        {/* Surah number badge */}
        <span className="inline-block bg-white/20 text-white text-xs font-bold px-2 py-0.5 rounded-full mb-2">
          {t('sma_surah_prefix', language)} {displayNum(surah.surahNumber, language)}
        </span>

        {/* Arabic name — always RTL, always font-arabic */}
        <div className="font-arabic text-3xl leading-relaxed text-white" dir="rtl">
          {surah.nameArabic}
        </div>

        {/* English/Latin name — only in English mode */}
        {language === 'en' && (
          <div className="text-white/90 text-base mt-0.5" dir="ltr">
            {surah.nameTransliteration}
            {surah.nameEnglish && (
              <span className="text-white/70 text-sm"> · {surah.nameEnglish}</span>
            )}
          </div>
        )}

        {/* Arabic transliteration label in Arabic mode */}
        {language === 'ar' && surah.nameEnglish && (
          <div className="text-white/70 text-sm mt-0.5" dir="ltr">
            {surah.nameTransliteration}
          </div>
        )}

        {/* Revelation badge */}
        <div className="flex items-center gap-2 mt-2">
          <span className="inline-flex items-center gap-1 bg-white/20 text-white text-xs px-2 py-0.5 rounded-full">
            {revelationLabel(surah.revelationType, language)}
          </span>
          <span className="flex items-center gap-1 text-white/70 text-xs">
            <AlertTriangle className="w-3 h-3" />
            {t('sma_review_required', language)}
          </span>
        </div>
      </div>

      {/* Panel body — scrollable */}
      <div className="flex-1 overflow-y-auto">
        {/* Stats grid */}
        <div className="grid grid-cols-3 divide-x divide-gray-100 border-b border-gray-100">
          {[
            { label: t('sma_ayah_count', language), value: displayNum(surah.ayahCount, language) },
            {
              label: t('sma_juz_range_lbl', language),
              value: surah.juzStart === surah.juzEnd
                ? displayNum(surah.juzStart, language)
                : `${displayNum(surah.juzStart, language)}–${displayNum(surah.juzEnd, language)}`,
            },
            {
              label: t('sma_page_lbl', language),
              value: surah.pageStart === surah.pageEnd
                ? displayNum(surah.pageStart, language)
                : `${displayNum(surah.pageStart, language)}–${displayNum(surah.pageEnd, language)}`,
            },
          ].map(({ label, value }) => (
            <div key={label} className="p-3 text-center">
              <div className="text-xs text-gray-500">{label}</div>
              <div className="text-lg font-bold text-gray-900 mt-0.5">{value}</div>
            </div>
          ))}
        </div>

        <div className="p-4 space-y-5">
          {/* Position in Quran — visual bar */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-medium text-gray-600">{t('sma_position_in_quran', language)}</span>
              <span className="text-xs text-gray-500">
                {displayNum(surah.surahNumber, language)} / {displayNum(114, language)}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', positionBarColor(surah.quranPosition))}
                style={{ width: `${positionPct}%`, minWidth: '4px' }}
              />
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {positionLabel(surah.quranPosition, language)}
            </div>
          </div>

          {/* Relative length bar */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-medium text-gray-600">{t('sma_relative_length', language)}</span>
              <span className="text-xs text-gray-500">
                {displayNum(surah.ayahCount, language)} {t('sma_ayahs_short', language)}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-400 rounded-full transition-all"
                style={{ width: `${lengthPct}%`, minWidth: '4px' }}
              />
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {lengthLabel(surah.lengthCategory, language)}
            </div>
          </div>

          {/* ── Opening verses (ayahs 1 & 2) ─────────────────────── */}
          {surah.firstAyahPreview && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {t('sma_opening_verses', language)}
              </div>
              <AyahBlock
                text={surah.firstAyahPreview ?? ''}
                ref_={surah.firstAyahRef}
                aya={1}
                surahNumber={surah.surahNumber}
              />
              {/* Mushaf link on first ayah only */}
              <Link
                to={`/mushaf?page=${surah.pageStart}`}
                className="inline-flex items-center gap-1 text-xs text-indigo-500 hover:text-indigo-700 transition-colors"
              >
                <ExternalLink className="w-3 h-3" />
                {t('sma_open_in_mushaf', language)} ({t('sma_pages_abbr', language)}{displayNum(surah.pageStart, language)})
              </Link>
              {/* Ayah 2 */}
              {surah.secondAyahPreview && (
                <AyahBlock
                  text={surah.secondAyahPreview}
                  ref_={surah.secondAyahRef ?? `${surah.surahNumber}:2`}
                  aya={2}
                  surahNumber={surah.surahNumber}
                />
              )}
            </div>
          )}

          {/* ── Middle passage (ayahs ~40% and ~60%) ──────────────── */}
          {surah.midAyah1Preview && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {t('sma_middle_passage', language)}
              </div>
              <AyahBlock
                text={surah.midAyah1Preview}
                ref_={surah.midAyah1Ref ?? ''}
                aya={parseInt((surah.midAyah1Ref ?? ':0').split(':')[1])}
                surahNumber={surah.surahNumber}
              />
              {surah.midAyah2Preview && (
                <AyahBlock
                  text={surah.midAyah2Preview}
                  ref_={surah.midAyah2Ref ?? ''}
                  aya={parseInt((surah.midAyah2Ref ?? ':0').split(':')[1])}
                  surahNumber={surah.surahNumber}
                />
              )}
            </div>
          )}

          {/* ── Closing verses (ayahs N-1 and N) ─────────────────── */}
          {surah.lastAyahPreview && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {t('sma_closing_verses', language)}
              </div>
              {surah.prevLastAyahPreview && (
                <AyahBlock
                  text={surah.prevLastAyahPreview}
                  ref_={surah.prevLastAyahRef ?? ''}
                  aya={surah.ayahCount - 1}
                  surahNumber={surah.surahNumber}
                />
              )}
              <AyahBlock
                text={surah.lastAyahPreview}
                ref_={surah.lastAyahRef}
                aya={surah.ayahCount}
                surahNumber={surah.surahNumber}
              />
            </div>
          )}
          {(surah.firstAyahPreview || surah.lastAyahPreview) && (
            <QuranTextAttribution language={language} />
          )}

          {/* ── Memory aid ────────────────────────────────────────── */}
          {clue && (
            <div className="bg-amber-50 border border-amber-100 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Brain className="w-3.5 h-3.5 text-amber-600" />
                <span className="text-xs font-medium text-amber-800">{t('sma_memory_aid', language)}</span>
              </div>
              <p
                className={clsx('text-sm text-amber-900', language === 'ar' ? 'font-arabic' : '')}
                dir={language === 'ar' ? 'rtl' : 'ltr'}
              >
                {clue}
              </p>
            </div>
          )}

          {/* ── Related stories ───────────────────────────────────── */}
          {surah.relatedStories.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {t('sma_related_stories', language)}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {surah.relatedStories.map(storyId => {
                  const name = STORY_NAMES[storyId];
                  if (!name) return null;
                  return (
                    <Link
                      key={storyId}
                      to={`/stories/${storyId}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs rounded-full border border-indigo-100 transition-colors"
                    >
                      <BookOpen className="w-2.5 h-2.5 shrink-0" />
                      <span dir={language === 'ar' ? 'rtl' : 'ltr'}>
                        {language === 'ar' ? name.ar : name.en}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Themes ────────────────────────────────────────────── */}
          {surah.relatedThemes.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {t('sma_themes', language)}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {surah.relatedThemes.map(theme => (
                  <span
                    key={theme}
                    className="inline-flex items-center px-2.5 py-0.5 bg-violet-50 text-violet-700 text-xs rounded-full border border-violet-100"
                    dir={language === 'ar' ? 'rtl' : 'ltr'}
                  >
                    {themeLabel(theme, language)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* ── Key Figures ───────────────────────────────────────── */}
          {surah.mainFigures.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {t('sma_key_figures', language)}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {surah.mainFigures.map(fig => (
                  <span
                    key={fig}
                    className="inline-flex items-center px-2.5 py-0.5 bg-sky-50 text-sky-700 text-xs rounded-full border border-sky-100"
                    dir={language === 'ar' ? 'rtl' : 'ltr'}
                  >
                    {figureLabel(fig, language)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Read full surah CTA */}
          <Link
            to={`/quran/${surah.surahNumber}`}
            className={clsx(
              'flex items-center justify-center gap-2 w-full py-2.5 rounded-lg text-sm font-medium transition-colors',
              surah.revelationType === 'makki'
                ? 'bg-amber-500 hover:bg-amber-600 text-white'
                : surah.revelationType === 'madani'
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : 'bg-slate-600 hover:bg-slate-700 text-white',
            )}
          >
            <BookOpen className="w-4 h-4" />
            {t('sma_read_full_surah', language)}
          </Link>

          {/* Before / After navigation */}
          <div className="border-t border-gray-100 pt-4">
            <div className="text-xs font-medium text-gray-500 mb-2">{t('sma_before_after', language)}</div>
            <div className="grid grid-cols-2 gap-2">
              {/* Previous */}
              <div>
                <div className="text-[10px] text-gray-400 mb-1">{t('sma_before_surah', language)}</div>
                {prevSurah ? (
                  <button
                    onClick={() => onNavigate(prevSurah.surahNumber)}
                    className="w-full text-start p-2 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all"
                  >
                    <div className="text-xs text-gray-500">
                      {displayNum(prevSurah.surahNumber, language)}
                    </div>
                    <div className="font-arabic text-sm text-gray-800 leading-snug" dir="rtl">
                      {prevSurah.nameArabic}
                    </div>
                    {language === 'en' && (
                      <div className="text-[10px] text-gray-400 truncate" dir="ltr">
                        {prevSurah.nameTransliteration}
                      </div>
                    )}
                  </button>
                ) : (
                  <div className="p-2 rounded-lg border border-dashed border-gray-100 text-center text-[10px] text-gray-300">
                    {t('sma_first_surah', language)}
                  </div>
                )}
              </div>

              {/* Next */}
              <div>
                <div className="text-[10px] text-gray-400 mb-1">{t('sma_after_surah', language)}</div>
                {nextSurah ? (
                  <button
                    onClick={() => onNavigate(nextSurah.surahNumber)}
                    className="w-full text-start p-2 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all"
                  >
                    <div className="text-xs text-gray-500">
                      {displayNum(nextSurah.surahNumber, language)}
                    </div>
                    <div className="font-arabic text-sm text-gray-800 leading-snug" dir="rtl">
                      {nextSurah.nameArabic}
                    </div>
                    {language === 'en' && (
                      <div className="text-[10px] text-gray-400 truncate" dir="ltr">
                        {nextSurah.nameTransliteration}
                      </div>
                    )}
                  </button>
                ) : (
                  <div className="p-2 rounded-lg border border-dashed border-gray-100 text-center text-[10px] text-gray-300">
                    {t('sma_last_surah', language)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Keyboard hint */}
          <div className="text-center text-[10px] text-gray-300 pb-2">
            {t('sma_keyboard_hint', language)}
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// QuizPanel
// ---------------------------------------------------------------------------

function QuizPanel({ surahs, language }: { surahs: SurahMemoryItem[]; language: 'ar' | 'en' }) {
  const [question, setQuestion] = useState<QuizQuestion>(() => generateQuestion(surahs));
  const [revealed, setRevealed] = useState(false);
  const [score, setScore] = useState({ correct: 0, total: 0 });

  const nextQuestion = useCallback(() => {
    setQuestion(generateQuestion(surahs));
    setRevealed(false);
  }, [surahs]);

  const handleCorrect = useCallback(() => {
    setScore(s => ({ correct: s.correct + 1, total: s.total + 1 }));
    nextQuestion();
  }, [nextQuestion]);

  const handleIncorrect = useCallback(() => {
    setScore(s => ({ ...s, total: s.total + 1 }));
    nextQuestion();
  }, [nextQuestion]);

  function questionText(): string {
    const { type, surah } = question;
    const name = language === 'ar' ? surah.nameArabic : surah.nameTransliteration;

    if (type === 'before') return `${t('sma_quiz_q_before', language)} "${name}"`;
    if (type === 'after') return `${t('sma_quiz_q_after', language)} "${name}"`;
    if (type === 'type') return `"${name}" — ${t('sma_quiz_q_type', language)}`;
    if (type === 'length') return `"${name}" — ${t('sma_quiz_q_length', language)}`;
    if (type === 'number') return `${t('sma_quiz_q_number', language)} "${name}"`;
    return `${t('sma_quiz_q_name', language)} ${displayNum(question.surah.surahNumber, language)}`;
  }

  function answerText(): string {
    const { type, surah, correctAnswer } = question;
    if (type === 'type') return revelationLabel(surah.revelationType, language);
    if (type === 'length') return lengthLabel(surah.lengthCategory, language);
    if (type === 'number') return displayNum(surah.surahNumber, language);
    if (correctAnswer === 'none') return language === 'ar' ? 'لا توجد' : 'None';
    if (type === 'name') {
      return language === 'ar' ? surah.nameArabic : surah.nameTransliteration;
    }
    // before/after — find the actual surah
    const targetNum = type === 'before' ? surah.surahNumber - 1 : surah.surahNumber + 1;
    const target = surahs.find(s => s.surahNumber === targetNum);
    if (!target) return language === 'ar' ? 'لا توجد' : 'None';
    return language === 'ar' ? target.nameArabic : target.nameTransliteration;
  }

  return (
    <div className="max-w-xl mx-auto py-8 px-4">
      {/* Score */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">{t('sma_test_yourself', language)}</h2>
        <div className="flex items-center gap-2 bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-sm font-medium">
          <span>{t('sma_score', language)}:</span>
          <span className="font-bold">
            {displayNum(score.correct, language)} / {displayNum(score.total, language)}
          </span>
        </div>
      </div>

      {/* Question card */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Surah header strip */}
        <div className={clsx(
          'h-1.5 w-full bg-gradient-to-r',
          revelationGradient(question.surah.revelationType),
        )} />

        <div className="p-6">
          <p
            className={clsx(
              'text-lg font-medium text-gray-800 leading-relaxed mb-6',
              language === 'ar' ? 'text-right font-arabic' : 'text-left',
            )}
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          >
            {questionText()}
          </p>

          {!revealed ? (
            <button
              onClick={() => setRevealed(true)}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors"
            >
              {t('sma_show_answer', language)}
            </button>
          ) : (
            <div className="space-y-4">
              {/* Answer display */}
              <div className="bg-gray-50 rounded-xl p-4 text-center">
                <div
                  className={clsx(
                    'text-xl font-bold text-gray-900',
                    question.type === 'before' || question.type === 'after' || question.type === 'name'
                      ? 'font-arabic'
                      : '',
                  )}
                  dir="rtl"
                >
                  {answerText()}
                </div>
              </div>

              {/* Self-report buttons */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleCorrect}
                  className="py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-medium transition-colors flex items-center justify-center gap-2"
                >
                  {t('sma_correct', language)}
                </button>
                <button
                  onClick={handleIncorrect}
                  className="py-2.5 rounded-xl bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium transition-colors flex items-center justify-center gap-2"
                >
                  {t('sma_try_again', language)}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Skip button */}
      <div className="text-center mt-4">
        <button
          onClick={nextQuestion}
          className="text-sm text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1 mx-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          {t('sma_next_question', language)}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export function SurahMemoryAtlasPage() {
  const { language } = useLanguageStore();
  const lang = language as 'ar' | 'en';
  const isRtl = lang === 'ar';

  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRevelation, setFilterRevelation] = useState<FilterRevelation>('all');
  const [filterLength, setFilterLength] = useState<FilterLength>('all');
  const [filterPosition, setFilterPosition] = useState<FilterPosition>('all');
  const [selectedNum, setSelectedNum] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Compute stats once
  const stats = useMemo(() => {
    const makki = SURAHS.filter(s => s.revelationType === 'makki').length;
    const madani = SURAHS.filter(s => s.revelationType === 'madani').length;
    return { makki, madani, unknown: SURAHS.length - makki - madani };
  }, []);

  // Filtered surahs
  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return SURAHS.filter(s => {
      if (filterRevelation !== 'all' && s.revelationType !== filterRevelation) return false;
      if (filterLength !== 'all' && s.lengthCategory !== filterLength) return false;
      if (filterPosition !== 'all' && s.quranPosition !== filterPosition) return false;
      if (!q) return true;
      const num = String(s.surahNumber);
      return (
        s.nameArabic.includes(q) ||
        s.nameTransliteration.toLowerCase().includes(q) ||
        (s.nameEnglish?.toLowerCase().includes(q) ?? false) ||
        num === q
      );
    });
  }, [searchQuery, filterRevelation, filterLength, filterPosition]);

  const selectedSurah = useMemo(
    () => (selectedNum !== null ? SURAHS.find(s => s.surahNumber === selectedNum) ?? null : null),
    [selectedNum],
  );

  const hasFilters = filterRevelation !== 'all' || filterLength !== 'all' || filterPosition !== 'all' || searchQuery !== '';

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setFilterRevelation('all');
    setFilterLength('all');
    setFilterPosition('all');
  }, []);

  const selectSurah = useCallback((num: number) => {
    setSelectedNum(prev => (prev === num ? null : num));
  }, []);

  const closePanel = useCallback(() => setSelectedNum(null), []);
  // Below the lg breakpoint the detail panel is a modal bottom sheet.
  const belowLg = useMediaQuery('(max-width: 1023.98px)');

  // Keyboard navigation inside detail panel
  useEffect(() => {
    if (selectedNum === null) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || (isRtl && e.key === 'ArrowLeft')) {
        const next = SURAHS.find(s => s.surahNumber === selectedNum + 1);
        if (next) setSelectedNum(next.surahNumber);
      } else if (e.key === 'ArrowLeft' || (isRtl && e.key === 'ArrowRight')) {
        const prev = SURAHS.find(s => s.surahNumber === selectedNum - 1);
        if (prev) setSelectedNum(prev.surahNumber);
      } else if (e.key === 'Escape') {
        setSelectedNum(null);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [selectedNum, isRtl]);

  // Scroll selected card into view
  useEffect(() => {
    if (selectedNum === null) return;
    const el = document.getElementById(`surah-card-${selectedNum}`);
    el?.scrollIntoView({ behavior: scrollBehavior(), block: 'nearest' });
  }, [selectedNum]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100" dir={isRtl ? 'rtl' : 'ltr'}>
      <div className="max-w-screen-2xl mx-auto px-3 sm:px-6 py-6">

        {/* ── Page header ─────────────────────────────────────────────── */}
        <div className="mb-5">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-indigo-600 rounded-xl text-white shrink-0">
              <LayoutGrid className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h1
                className={clsx('text-xl font-bold text-gray-900', lang === 'ar' ? 'font-arabic' : '')}
                dir={lang === 'ar' ? 'rtl' : 'ltr'}
              >
                {t('sma_title', lang)}
              </h1>
              <p className="text-sm text-gray-500 mt-0.5" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
                {t('sma_description', lang)}
              </p>
            </div>
          </div>

          {/* Stats strip */}
          <div className="flex flex-wrap gap-3 mt-3">
            <span className="text-xs bg-white border border-gray-200 px-2.5 py-1 rounded-full text-gray-600">
              {displayNum(114, lang)} {t('sma_surah_word', lang)}
            </span>
            <span className="text-xs bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full text-amber-700">
              {displayNum(stats.makki, lang)} {t('sma_makki_label', lang)}
            </span>
            <span className="text-xs bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full text-emerald-700">
              {displayNum(stats.madani, lang)} {t('sma_madani_label', lang)}
            </span>
          </div>
        </div>

        {/* ── View tabs ───────────────────────────────────────────────── */}
        <div className="flex items-center gap-1 mb-4 bg-white border border-gray-200 rounded-xl p-1 w-fit">
          {([
            { mode: 'grid' as ViewMode, label: t('sma_grid_view', lang), Icon: LayoutGrid },
            { mode: 'quiz' as ViewMode, label: t('sma_quiz_mode', lang), Icon: Brain },
          ] as const).map(({ mode, label, Icon }) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={clsx(
                'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                viewMode === mode
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50',
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Grid cards show opening ayahs on hover: the licence asks for attribution. */}
        <QuranTextAttribution language={lang} className="mb-3" />

        {/* ── Quiz view ───────────────────────────────────────────────── */}
        {viewMode === 'quiz' && <QuizPanel surahs={SURAHS} language={lang} />}

        {/* ── Grid view ───────────────────────────────────────────────── */}
        {viewMode === 'grid' && (
          <>
            {/* Search + filter bar */}
            <div className="mb-4 space-y-2">
              <div className="flex gap-2">
                {/* Search */}
                <div className="relative flex-1">
                  <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    aria-label={t('sma_search_placeholder', lang)}
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder={t('sma_search_placeholder', lang)}
                    dir={lang === 'ar' ? 'rtl' : 'ltr'}
                    className="w-full ps-9 pe-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent"
                  />
                </div>

                {/* Filter toggle */}
                <button
                  onClick={() => setShowFilters(f => !f)}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-2.5 rounded-xl border text-sm font-medium transition-colors',
                    showFilters || hasFilters
                      ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50',
                  )}
                >
                  <Filter className="w-4 h-4" />
                  {t('sma_filter_revelation', lang)}
                  {hasFilters && <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />}
                </button>

                {/* Clear */}
                {hasFilters && (
                  <button
                    onClick={clearFilters}
                    className="flex items-center gap-1 px-3 py-2.5 rounded-xl border border-gray-200 bg-white text-sm text-gray-500 hover:bg-gray-50 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    {t('sma_clear_filters', lang)}
                  </button>
                )}
              </div>

              {/* Expanded filters */}
              {showFilters && (
                <div className="bg-white border border-gray-200 rounded-xl p-3 space-y-3">
                  {/* Revelation type */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1.5">{t('sma_filter_revelation', lang)}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {([
                        ['all', t('sma_filter_all', lang)] as const,
                        ['makki', t('sma_makki', lang)] as const,
                        ['madani', t('sma_madani', lang)] as const,
                        ['unknown', t('sma_unknown', lang)] as const,
                      ] as const).map(([v, label]) => (
                        <button
                          key={v}
                          onClick={() => setFilterRevelation(v)}
                          className={clsx(
                            'px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                            filterRevelation === v
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300',
                          )}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Length */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1.5">{t('sma_filter_length', lang)}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {([
                        ['all', t('sma_filter_all', lang)] as const,
                        ['short', t('sma_short', lang)] as const,
                        ['medium', t('sma_medium', lang)] as const,
                        ['long', t('sma_long', lang)] as const,
                        ['very_long', t('sma_very_long', lang)] as const,
                      ] as const).map(([v, label]) => (
                        <button
                          key={v}
                          onClick={() => setFilterLength(v)}
                          className={clsx(
                            'px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                            filterLength === v
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300',
                          )}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Position */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1.5">{t('sma_filter_position', lang)}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {([
                        ['all', t('sma_filter_all', lang)] as const,
                        ['beginning', t('sma_beginning', lang)] as const,
                        ['early', t('sma_early', lang)] as const,
                        ['middle', t('sma_middle', lang)] as const,
                        ['late', t('sma_late', lang)] as const,
                        ['ending', t('sma_ending', lang)] as const,
                      ] as const).map(([v, label]) => (
                        <button
                          key={v}
                          onClick={() => setFilterPosition(v)}
                          className={clsx(
                            'px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                            filterPosition === v
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300',
                          )}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Result count */}
              <div className="flex items-center justify-between text-xs text-gray-400 px-0.5">
                <span>
                  {displayNum(filtered.length, lang)} {t('sma_results_count', lang)}
                  {filtered.length < SURAHS.length && (
                    <span className="ms-1 text-gray-300">
                      / {displayNum(SURAHS.length, lang)}
                    </span>
                  )}
                </span>
                {filtered.length === 0 && (
                  <span className="text-gray-400">{t('sma_no_results', lang)}</span>
                )}
              </div>
            </div>

            {/* ── Grid + Detail panel layout ─────────────────────────── */}
            <div className="flex gap-4 items-start">
              {/* Grid */}
              <div className={clsx(
                'flex-1 min-w-0 transition-all duration-300',
                selectedSurah ? 'lg:max-w-[calc(100%-400px)]' : '',
              )}>
                {filtered.length > 0 ? (
                  <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 2xl:grid-cols-10 gap-2">
                    {filtered.map(s => (
                      <div key={s.surahNumber} id={`surah-card-${s.surahNumber}`}>
                        <SurahCard
                          surah={s}
                          selected={selectedNum === s.surahNumber}
                          onClick={() => selectSurah(s.surahNumber)}
                          language={lang}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16 text-gray-400">
                    <Search className="w-8 h-8 mx-auto mb-3 opacity-40" />
                    <p className="text-sm">{t('sma_no_results', lang)}</p>
                    <button
                      onClick={clearFilters}
                      className="mt-3 text-indigo-500 hover:text-indigo-700 text-sm underline"
                    >
                      {t('sma_clear_filters', lang)}
                    </button>
                  </div>
                )}
              </div>

              {/* Desktop detail panel — sticky sidebar */}
              {selectedSurah && (
                <div
                  ref={panelRef}
                  className="hidden lg:flex flex-col w-[380px] flex-shrink-0 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden sticky top-4 max-h-[calc(100vh-5rem)]"
                >
                  <SurahDetailPanel
                    surah={selectedSurah}
                    surahs={SURAHS}
                    onClose={closePanel}
                    onNavigate={setSelectedNum}
                    language={lang}
                  />
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── Mobile bottom sheet (accessible modal: focus trap, Escape, scroll lock) ── */}
      {selectedSurah && (
        <Dialog
          open={viewMode === 'grid' && belowLg}
          onClose={closePanel}
          variant="sheet"
          ariaLabel={lang === 'ar' ? selectedSurah.nameArabic : (selectedSurah.nameEnglish || selectedSurah.nameArabic)}
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          {/* Drag handle */}
          <div className="flex justify-center pt-3 pb-1 shrink-0" aria-hidden="true">
            <div className="w-10 h-1 bg-gray-200 rounded-full" />
          </div>
          <SurahDetailPanel
            surah={selectedSurah}
            surahs={SURAHS}
            onClose={closePanel}
            onNavigate={setSelectedNum}
            language={lang}
          />
        </Dialog>
      )}
    </div>
  );
}
