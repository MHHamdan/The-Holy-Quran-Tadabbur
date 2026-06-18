/**
 * Surah Comparison Tool — compare any two surahs side-by-side.
 *
 * Data sources: SURAH_ATLAS_DATA · TIMELINE_BY_SURAH · SURAH_NAMES
 * No Quran text displayed — only metadata and scholarly summaries.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { GitCompare, ChevronDown, BookOpen, Users, Landmark, Clock, Layers, BookOpenText, Share2 } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_ATLAS_DATA } from '../data/surahAtlas';
import { TIMELINE_BY_SURAH } from '../data/revelationTimeline';
import { SURAH_NAMES } from '../data/surahNames';

// ---------------------------------------------------------------------------
// Prophet name map (EN → AR)
// ---------------------------------------------------------------------------

const PROPHET_AR: Record<string, string> = {
  Adam: 'آدم', Ibrahim: 'إبراهيم', Ismail: 'إسماعيل', Ishaq: 'إسحاق',
  Yaqub: 'يعقوب', Yusuf: 'يوسف', Musa: 'موسى', Harun: 'هارون',
  Dawud: 'داود', Sulayman: 'سليمان', Isa: 'عيسى', Yahya: 'يحيى',
  Zakariyya: 'زكريا', Nuh: 'نوح', Hud: 'هود', Salih: 'صالح',
  Lut: 'لوط', Shuayb: 'شعيب', Idris: 'إدريس', Yunus: 'يونس',
  Ilyas: 'إلياس', Alyasa: 'اليسع', Dhulkifl: 'ذو الكفل', Ayyub: 'أيوب',
  Luqman: 'لقمان', Khidr: 'الخضر', Maryam: 'مريم',
};

// ---------------------------------------------------------------------------
// Story title map
// ---------------------------------------------------------------------------

const STORY_TITLES: Record<string, { en: string; ar: string }> = {
  story_kahf:                  { en: 'People of the Cave',            ar: 'أصحاب الكهف' },
  story_two_gardens:           { en: 'Owner of Two Gardens',          ar: 'صاحب الجنتين' },
  story_khidr:                 { en: 'Musa and Khidr',                ar: 'موسى والخضر' },
  story_khidr_musa:            { en: 'Musa and Khidr',                ar: 'موسى والخضر' },
  story_dhulqarnayn:           { en: 'Dhul-Qarnayn',                  ar: 'ذو القرنين' },
  story_musa:                  { en: 'Prophet Musa',                  ar: 'نبي موسى' },
  story_adam:                  { en: 'Prophet Adam',                  ar: 'نبي آدم' },
  story_ibrahim:               { en: 'Prophet Ibrahim',               ar: 'نبي إبراهيم' },
  story_nuh:                   { en: 'Prophet Nuh',                   ar: 'نبي نوح' },
  story_isa:                   { en: 'Prophet Isa',                   ar: 'نبي عيسى' },
  story_dawud:                 { en: 'Prophet Dawud',                 ar: 'نبي داود' },
  story_sulayman:              { en: 'Prophet Sulayman',              ar: 'نبي سليمان' },
  story_yusuf:                 { en: 'Prophet Yusuf',                 ar: 'نبي يوسف' },
  story_ayyub:                 { en: 'Prophet Ayyub',                 ar: 'نبي أيوب' },
  story_yunus:                 { en: 'Prophet Yunus',                 ar: 'نبي يونس' },
  story_hud:                   { en: 'Prophet Hud',                   ar: 'نبي هود' },
  story_salih:                 { en: 'Prophet Salih',                 ar: 'نبي صالح' },
  story_lut:                   { en: 'Prophet Lut',                   ar: 'نبي لوط' },
  story_shuayb:                { en: 'Prophet Shuayb',                ar: 'نبي شعيب' },
  story_idris:                 { en: 'Prophet Idris',                 ar: 'نبي إدريس' },
  story_ismail:                { en: 'Prophet Ismail',                ar: 'نبي إسماعيل' },
  story_zakariyya_yahya:       { en: 'Zakariyya and Yahya',           ar: 'زكريا ويحيى' },
  story_maryam:                { en: 'Maryam',                        ar: 'مريم' },
  story_luqman:                { en: 'Luqman the Wise',               ar: 'لقمان الحكيم' },
  story_bilqis:                { en: 'Bilqis & Sulayman',             ar: 'بلقيس وسليمان' },
  story_yajuj_majuj:           { en: 'Yajuj and Majuj',               ar: 'يأجوج ومأجوج' },
  story_iblis_refusal:         { en: 'Iblis Refuses to Bow',          ar: 'إباء إبليس السجود' },
  story_angels_prostration:    { en: 'Angels Prostrate to Adam',      ar: 'سجود الملائكة لآدم' },
  story_talut_jalut:           { en: 'Talut, Jalut and Dawud',        ar: 'طالوت وجالوت وداود' },
  story_qarun:                 { en: 'Qarun the Arrogant',            ar: 'قارون المتكبر' },
  story_garden_owners:         { en: 'Owners of the Garden',          ar: 'أصحاب الجنة' },
  story_sabbath_breakers:      { en: 'Sabbath Breakers',              ar: 'أصحاب السبت' },
  story_elephant:              { en: 'People of the Elephant',        ar: 'أصحاب الفيل' },
  story_baqarah_cow:           { en: 'The Cow of Bani Israel',        ar: 'بقرة بني إسرائيل' },
  story_table_spread:          { en: 'Table Spread from Heaven',      ar: 'المائدة المنزلة من السماء' },
  story_habil_qabil:           { en: 'Habil and Qabil',               ar: 'هابيل وقابيل' },
  story_ukhdud:                { en: 'People of the Trench',          ar: 'أصحاب الأخدود' },
  story_qarya:                 { en: 'People of the Town',            ar: 'أصحاب القرية' },
  story_rain_parable:          { en: 'Parable of Rain',               ar: 'مثل الغيث' },
  story_creation_heavens_earth:{ en: 'Creation of Heavens & Earth',   ar: 'خلق السماوات والأرض' },
  story_bani_israel:           { en: 'Bani Israel',                   ar: 'بنو إسرائيل' },
  story_golden_calf:           { en: 'Golden Calf',                   ar: 'العجل الذهبي' },
  story_harut_marut:           { en: 'Harut and Marut',               ar: 'هاروت وماروت' },
  story_ibrahim_nimrod:        { en: 'Ibrahim and Nimrod',            ar: 'إبراهيم ونمرود' },
  story_ibrahim_birds:         { en: 'Ibrahim and the Birds',         ar: 'إبراهيم والطيور' },
  story_uzair:                 { en: 'Uzair Raised after Death',      ar: 'عزير بعد الموت' },
  story_miraj:                 { en: "The Prophet's Night Journey",   ar: 'الإسراء والمعراج' },
};

function storyTitle(storyId: string, isRtl: boolean): string {
  const e = STORY_TITLES[storyId];
  if (e) return isRtl ? e.ar : e.en;
  return storyId.replace('story_', '').replace(/_/g, ' ');
}

// ---------------------------------------------------------------------------
// Data helpers
// ---------------------------------------------------------------------------

function getSurahData(n: number) {
  const atlas    = SURAH_ATLAS_DATA.find(s => s.surahNumber === n);
  const timeline = TIMELINE_BY_SURAH[n];
  const name     = SURAH_NAMES[n - 1];
  return { atlas, timeline, name };
}

type SurahData = ReturnType<typeof getSurahData>;
type StoryRef  = { storyId: string; coverage: string; ayahRange?: { display: string } };

const AYAH_COUNTS = SURAH_ATLAS_DATA.map(s => s.ayahCount);
const MAX_AYAHS   = Math.max(...AYAH_COUNTS);

// ---------------------------------------------------------------------------
// Comparison table rows
// ---------------------------------------------------------------------------

interface CompareRow {
  labelEn:   string;
  labelAr:   string;
  renderA:   string | null;
  renderB:   string | null;
  highlight?: boolean;
  icon?:     React.ElementType;
}

const PERIOD_EN: Record<string, string> = {
  early_meccan:  'Early Meccan',
  middle_meccan: 'Middle Meccan',
  late_meccan:   'Late Meccan',
  early_medinan: 'Early Medinan',
  late_medinan:  'Late Medinan',
};
const PERIOD_AR: Record<string, string> = {
  early_meccan:  'مكي مبكر',
  middle_meccan: 'مكي وسط',
  late_meccan:   'مكي متأخر',
  early_medinan: 'مدني مبكر',
  late_medinan:  'مدني متأخر',
};

function buildRows(a: SurahData, b: SurahData, isRtl: boolean): CompareRow[] {
  const sep = isRtl ? '، ' : ', ';

  const revType = (atlas: SurahData['atlas']) => {
    const v = atlas?.revelationType ?? '—';
    return v === 'makki' ? (isRtl ? 'مكية' : 'Meccan')
         : v === 'madani' ? (isRtl ? 'مدنية' : 'Medinan') : v;
  };

  const prophets = (atlas: SurahData['atlas']) => {
    const list = atlas?.prophetsMentioned ?? [];
    if (!list.length) return isRtl ? 'لا أحد' : 'None';
    return list.slice(0, 5).map(p => isRtl ? (PROPHET_AR[p] ?? p) : p).join(sep);
  };

  const nations = (atlas: SurahData['atlas']) => {
    const list = (atlas as any)?.nationsMentioned ?? [];
    if (!list.length) return '—';
    return list.slice(0, 3).join(sep);
  };

  const concepts = (atlas: SurahData['atlas']) =>
    (isRtl
      ? (atlas?.keyConceptsAr?.slice(0, 4) ?? atlas?.keyConcepts?.slice(0, 4) ?? [])
      : (atlas?.keyConcepts?.slice(0, 4) ?? [])
    ).join(sep) || '—';

  return [
    {
      labelEn: 'Revelation Type', labelAr: 'نوع التنزيل', icon: Landmark,
      renderA: revType(a.atlas), renderB: revType(b.atlas),
      highlight: a.atlas?.revelationType !== b.atlas?.revelationType,
    },
    {
      labelEn: 'Period', labelAr: 'الحقبة', icon: Clock,
      renderA: a.timeline ? (isRtl ? PERIOD_AR[a.timeline.period] : PERIOD_EN[a.timeline.period]) : '—',
      renderB: b.timeline ? (isRtl ? PERIOD_AR[b.timeline.period] : PERIOD_EN[b.timeline.period]) : '—',
      highlight: a.timeline?.period !== b.timeline?.period,
    },
    {
      labelEn: 'Revelation Order', labelAr: 'ترتيب النزول',
      renderA: a.timeline ? `#${a.timeline.revelationOrder}` : '—',
      renderB: b.timeline ? `#${b.timeline.revelationOrder}` : '—',
    },
    {
      labelEn: 'Verse Count', labelAr: 'عدد الآيات',
      renderA: a.atlas ? String(a.atlas.ayahCount) : '—',
      renderB: b.atlas ? String(b.atlas.ayahCount) : '—',
      highlight: a.atlas?.ayahCount !== b.atlas?.ayahCount,
    },
    {
      labelEn: 'Mushaf Pages', labelAr: 'صفحات المصحف',
      renderA: a.atlas ? `${a.atlas.pageStart}–${a.atlas.pageEnd}` : '—',
      renderB: b.atlas ? `${b.atlas.pageStart}–${b.atlas.pageEnd}` : '—',
    },
    {
      labelEn: 'Juz', labelAr: 'الجزء',
      renderA: a.atlas?.juzRefs?.join(', ') ?? '—',
      renderB: b.atlas?.juzRefs?.join(', ') ?? '—',
      highlight: JSON.stringify(a.atlas?.juzRefs) !== JSON.stringify(b.atlas?.juzRefs),
    },
    {
      labelEn: 'Main Theme', labelAr: 'الموضوع الرئيسي',
      renderA: a.timeline ? (isRtl ? a.timeline.mainThemeAr : a.timeline.mainThemeEn) : '—',
      renderB: b.timeline ? (isRtl ? b.timeline.mainThemeAr : b.timeline.mainThemeEn) : '—',
    },
    {
      labelEn: 'Key Concepts', labelAr: 'المفاهيم الرئيسية',
      renderA: concepts(a.atlas), renderB: concepts(b.atlas),
    },
    {
      labelEn: 'Prophets Mentioned', labelAr: 'الأنبياء المذكورون', icon: Users,
      renderA: prophets(a.atlas), renderB: prophets(b.atlas),
      highlight:
        JSON.stringify((a.atlas?.prophetsMentioned ?? []).slice().sort()) !==
        JSON.stringify((b.atlas?.prophetsMentioned ?? []).slice().sort()),
    },
    {
      labelEn: 'Nations / Peoples', labelAr: 'الأمم المذكورة',
      renderA: nations(a.atlas), renderB: nations(b.atlas),
    },
  ];
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SurahSelector({ value, onChange, isRtl, label }: {
  value: number; onChange: (n: number) => void; isRtl: boolean; label: string;
}) {
  return (
    <div className="flex-1 min-w-0">
      <p className={clsx('text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide', isRtl && 'font-arabic text-right')}>
        {label}
      </p>
      <div className="relative">
        <select
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          className={clsx(
            'w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-800 focus:outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100',
            isRtl ? 'font-arabic text-right pr-4 pl-9' : 'pr-9'
          )}
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          {SURAH_NAMES.map((sn, i) => (
            <option key={i + 1} value={i + 1}>
              {i + 1}. {isRtl ? sn.ar : sn.en}
            </option>
          ))}
        </select>
        <ChevronDown className={clsx('pointer-events-none absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400', isRtl ? 'left-3' : 'right-3')} />
      </div>
    </div>
  );
}

function AyahBar({ count, maxCount }: { count: number; maxCount: number }) {
  return (
    <div className="mt-1 w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
      <div className="h-full bg-violet-400 rounded-full" style={{ width: `${Math.max(4, (count / maxCount) * 100)}%` }} />
    </div>
  );
}

// Size visualization — page spans
function PageBar({ start, end, color }: { start: number; end: number; color: 'violet' | 'blue' }) {
  const TOTAL_PAGES = 604;
  const left  = ((start - 1) / TOTAL_PAGES) * 100;
  const width = Math.max(0.5, ((end - start + 1) / TOTAL_PAGES) * 100);
  return (
    <div className="relative w-full h-2 bg-gray-100 rounded-full overflow-hidden mt-1">
      <div
        className={clsx('absolute h-full rounded-full', color === 'violet' ? 'bg-violet-400' : 'bg-blue-400')}
        style={{ left: `${left}%`, width: `${width}%` }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Revelation context cards
// ---------------------------------------------------------------------------

function RevealContextSection({ dataA, dataB, surahA, surahB, isRtl }: {
  dataA: SurahData; dataB: SurahData; surahA: number; surahB: number; isRtl: boolean;
}) {
  const ctxA = dataA.timeline ? (isRtl ? dataA.timeline.contextAr : dataA.timeline.contextEn) : null;
  const ctxB = dataB.timeline ? (isRtl ? dataB.timeline.contextAr : dataB.timeline.contextEn) : null;
  if (!ctxA && !ctxB) return null;

  return (
    <div className="mb-6">
      <h3 className={clsx('text-sm font-bold text-gray-700 mb-3 flex items-center gap-1.5', isRtl && 'flex-row-reverse font-arabic')}>
        <Clock className="w-4 h-4 text-gray-400" />
        {isRtl ? 'سياق النزول' : 'Revelation Context'}
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[
          { ctx: ctxA, num: surahA, data: dataA, color: 'violet' },
          { ctx: ctxB, num: surahB, data: dataB, color: 'blue' },
        ].map(({ ctx, num, data, color }) => ctx ? (
          <div key={num} className={clsx(
            'rounded-2xl border p-4',
            color === 'violet' ? 'bg-violet-50/60 border-violet-100' : 'bg-blue-50/60 border-blue-100'
          )}>
            <div className={clsx('flex items-center gap-1.5 mb-2', isRtl && 'flex-row-reverse')}>
              <span className={clsx('text-xs font-bold', color === 'violet' ? 'text-violet-600' : 'text-blue-600', isRtl && 'font-arabic')}>
                {isRtl ? data.name?.ar : data.name?.en}
              </span>
              {data.timeline && (
                <span className="text-[10px] text-gray-400">
                  {isRtl
                    ? (data.timeline.hijraYear ? `${data.timeline.hijraYear}هـ` : `السنة ${data.timeline.propheticYear} للبعثة`)
                    : (data.timeline.hijraYear ? `AH ${data.timeline.hijraYear}` : `Year ${data.timeline.propheticYear} BH`)}
                </span>
              )}
            </div>
            <p className={clsx('text-xs text-gray-600 leading-relaxed', isRtl && 'font-arabic text-right')}>
              {ctx}
            </p>
          </div>
        ) : null)}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stories section — includes shared-stories detection
// ---------------------------------------------------------------------------

const COVERAGE_AR: Record<string, string>    = { complete: 'كاملة', partial: 'جزئية', mention_only: 'إشارة' };
const COVERAGE_COLOR: Record<string, string> = {
  complete: 'bg-emerald-100 text-emerald-700',
  partial:  'bg-amber-100 text-amber-700',
  mention_only: 'bg-gray-100 text-gray-500',
};

function StoryLink({ ref: sr, isRtl, color }: { ref: StoryRef; isRtl: boolean; color: 'violet' | 'blue' | 'purple' }) {
  return (
    <Link
      to={`/stories/${sr.storyId}`}
      className={clsx(
        'flex items-start gap-2 rounded-lg px-3 py-2 text-xs transition-colors group hover:bg-white/80',
        isRtl && 'flex-row-reverse text-right',
      )}
    >
      <BookOpen className={clsx('w-3.5 h-3.5 mt-0.5 shrink-0',
        color === 'violet' ? 'text-violet-400 group-hover:text-violet-600'
        : color === 'blue' ? 'text-blue-400 group-hover:text-blue-600'
        : 'text-purple-400 group-hover:text-purple-600'
      )} />
      <span className={clsx('flex-1 font-medium text-gray-700 group-hover:text-gray-900', isRtl && 'font-arabic')}>
        {storyTitle(sr.storyId, isRtl)}
      </span>
      {sr.coverage && (
        <span className={clsx('shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium',
          COVERAGE_COLOR[sr.coverage] ?? 'bg-gray-100 text-gray-400'
        )}>
          {isRtl ? (COVERAGE_AR[sr.coverage] ?? sr.coverage) : sr.coverage.replace('_', ' ')}
        </span>
      )}
    </Link>
  );
}

function StoriesSection({ dataA, dataB, surahA, surahB, isRtl }: {
  dataA: SurahData; dataB: SurahData; surahA: number; surahB: number; isRtl: boolean;
}) {
  const storiesA: StoryRef[] = (dataA.atlas as any)?.storiesMentioned ?? [];
  const storiesB: StoryRef[] = (dataB.atlas as any)?.storiesMentioned ?? [];
  if (!storiesA.length && !storiesB.length) return null;

  const idsA = new Set(storiesA.map(s => s.storyId));
  const idsB = new Set(storiesB.map(s => s.storyId));
  const shared = storiesA.filter(s => idsB.has(s.storyId));
  const onlyA  = storiesA.filter(s => !idsB.has(s.storyId));
  const onlyB  = storiesB.filter(s => !idsA.has(s.storyId));

  return (
    <div className="mb-6">
      <h3 className={clsx('text-sm font-bold text-gray-700 mb-3 flex items-center gap-1.5', isRtl && 'flex-row-reverse font-arabic')}>
        <BookOpenText className="w-4 h-4 text-gray-400" />
        {isRtl ? 'القصص المذكورة في السورتين' : 'Stories in each surah'}
      </h3>

      {/* Shared stories */}
      {shared.length > 0 && (
        <div className="rounded-2xl border border-purple-200 bg-purple-50/60 p-4 mb-3">
          <p className={clsx('text-xs font-bold text-purple-700 mb-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? `قصص مشتركة بين السورتين (${shared.length})` : `Shared stories (${shared.length})`}
          </p>
          <ul className="space-y-1">
            {shared.map(sr => <li key={sr.storyId}><StoryLink ref={sr} isRtl={isRtl} color="purple" /></li>)}
          </ul>
        </div>
      )}

      {/* Per-surah lists */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="rounded-2xl border border-violet-100 bg-violet-50/50 p-4">
          <p className={clsx('text-xs font-bold text-violet-600 mb-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? `${SURAH_NAMES[surahA - 1]?.ar} — مستقلة (${onlyA.length})` : `${SURAH_NAMES[surahA - 1]?.en} only (${onlyA.length})`}
          </p>
          {onlyA.length ? (
            <ul className="space-y-1">{onlyA.map(sr => <li key={sr.storyId}><StoryLink ref={sr} isRtl={isRtl} color="violet" /></li>)}</ul>
          ) : (
            <p className={clsx('text-xs text-gray-400 italic', isRtl && 'font-arabic')}>
              {isRtl ? 'كل القصص مشتركة' : 'All stories shared'}
            </p>
          )}
        </div>
        <div className="rounded-2xl border border-blue-100 bg-blue-50/50 p-4">
          <p className={clsx('text-xs font-bold text-blue-600 mb-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? `${SURAH_NAMES[surahB - 1]?.ar} — مستقلة (${onlyB.length})` : `${SURAH_NAMES[surahB - 1]?.en} only (${onlyB.length})`}
          </p>
          {onlyB.length ? (
            <ul className="space-y-1">{onlyB.map(sr => <li key={sr.storyId}><StoryLink ref={sr} isRtl={isRtl} color="blue" /></li>)}</ul>
          ) : (
            <p className={clsx('text-xs text-gray-400 italic', isRtl && 'font-arabic')}>
              {isRtl ? 'كل القصص مشتركة' : 'All stories shared'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quick-insight chips
// ---------------------------------------------------------------------------

function InsightsSection({ dataA, dataB, isRtl }: {
  dataA: SurahData; dataB: SurahData; isRtl: boolean;
}) {
  const insights: { ar: string; en: string }[] = [];

  // Same period?
  if (dataA.timeline && dataB.timeline && dataA.timeline.period === dataB.timeline.period) {
    const p = isRtl ? PERIOD_AR[dataA.timeline.period] : PERIOD_EN[dataA.timeline.period];
    insights.push({ ar: `كلتا السورتين ${p}`, en: `Both surahs are ${p}` });
  }

  // Shared prophets
  const prophA = new Set(dataA.atlas?.prophetsMentioned ?? []);
  const prophB = new Set(dataB.atlas?.prophetsMentioned ?? []);
  const shared = [...prophA].filter(p => prophB.has(p));
  if (shared.length) {
    const names = shared.map(p => isRtl ? (PROPHET_AR[p] ?? p) : p).join(isRtl ? '، ' : ', ');
    insights.push({
      ar: `الأنبياء المشتركون: ${names}`,
      en: `Shared prophets: ${names}`,
    });
  }

  // Revelation order gap
  if (dataA.timeline && dataB.timeline) {
    const gap = Math.abs(dataA.timeline.revelationOrder - dataB.timeline.revelationOrder);
    const earlier = dataA.timeline.revelationOrder < dataB.timeline.revelationOrder
      ? (isRtl ? dataA.name?.ar : dataA.name?.en)
      : (isRtl ? dataB.name?.ar : dataB.name?.en);
    if (gap > 0) {
      insights.push({
        ar: `${earlier} أُنزلت قبل ${gap} سورةً بترتيب النزول`,
        en: `${earlier} was revealed ${gap} surahs earlier chronologically`,
      });
    }
  }

  // Ayah ratio
  if (dataA.atlas && dataB.atlas) {
    const bigger = dataA.atlas.ayahCount > dataB.atlas.ayahCount
      ? (isRtl ? dataA.name?.ar : dataA.name?.en)
      : (isRtl ? dataB.name?.ar : dataB.name?.en);
    const ratio = Math.max(dataA.atlas.ayahCount, dataB.atlas.ayahCount) /
                  Math.min(dataA.atlas.ayahCount, dataB.atlas.ayahCount);
    if (ratio > 1.5) {
      insights.push({
        ar: `${bigger} أطول ${ratio.toFixed(1)} مرة`,
        en: `${bigger} is ${ratio.toFixed(1)}× longer`,
      });
    }
  }

  if (!insights.length) return null;

  return (
    <div className="mb-6">
      <h3 className={clsx('text-sm font-bold text-gray-700 mb-3 flex items-center gap-1.5', isRtl && 'flex-row-reverse font-arabic')}>
        <Layers className="w-4 h-4 text-gray-400" />
        {isRtl ? 'ملاحظات سريعة' : 'Quick insights'}
      </h3>
      <div className="flex flex-wrap gap-2">
        {insights.map((ins, i) => (
          <span key={i} className={clsx(
            'inline-block rounded-xl bg-gray-100 px-3 py-1.5 text-xs text-gray-700',
            isRtl && 'font-arabic'
          )}>
            {isRtl ? ins.ar : ins.en}
          </span>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Mushaf position visualiser
// ---------------------------------------------------------------------------

function MushafPositionSection({ dataA, dataB, surahA, surahB, isRtl }: {
  dataA: SurahData; dataB: SurahData; surahA: number; surahB: number; isRtl: boolean;
}) {
  if (!dataA.atlas || !dataB.atlas) return null;
  if (!dataA.atlas.pageStart || !dataB.atlas.pageStart) return null;
  return (
    <div className="mb-6">
      <h3 className={clsx('text-sm font-bold text-gray-700 mb-3', isRtl && 'font-arabic text-right')}>
        {isRtl ? 'موضع السورتين في المصحف (604 صفحة)' : 'Surah position in the Mushaf (604 pages)'}
      </h3>
      <div className="space-y-3 bg-gray-50 rounded-2xl border border-gray-100 p-4">
        {[
          { data: dataA, num: surahA, color: 'violet' as const },
          { data: dataB, num: surahB, color: 'blue' as const },
        ].map(({ data, num, color }) => data.atlas?.pageStart && data.atlas?.pageEnd ? (
          <div key={num}>
            <div className={clsx('flex items-center justify-between text-xs mb-1', isRtl && 'flex-row-reverse')}>
              <span className={clsx('font-semibold', color === 'violet' ? 'text-violet-600' : 'text-blue-600', isRtl && 'font-arabic')}>
                {isRtl ? data.name?.ar : data.name?.en}
              </span>
              <span className="text-gray-400">
                {isRtl ? `ص ${data.atlas.pageStart}–${data.atlas.pageEnd}` : `p. ${data.atlas.pageStart}–${data.atlas.pageEnd}`}
              </span>
            </div>
            <PageBar start={data.atlas.pageStart} end={data.atlas.pageEnd} color={color} />
          </div>
        ) : null)}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function SurahComparePage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [surahA, setSurahA] = useState(18);  // Al-Kahf
  const [surahB, setSurahB] = useState(57);  // Al-Hadid

  const dataA = useMemo(() => getSurahData(surahA), [surahA]);
  const dataB = useMemo(() => getSurahData(surahB), [surahB]);
  const rows  = useMemo(() => buildRows(dataA, dataB, isRtl), [dataA, dataB, isRtl]);

  const summaryA = dataA.atlas?.summary?.short?.[isRtl ? 'ar' : 'en'];
  const summaryB = dataB.atlas?.summary?.short?.[isRtl ? 'ar' : 'en'];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-6', isRtl && 'flex-row-reverse')}>
        <GitCompare className="w-7 h-7 text-violet-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'مقارنة السور' : 'Surah Comparison'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl ? 'قارن بين أي سورتين جنباً إلى جنب' : 'Compare any two surahs side by side'}
          </p>
        </div>
      </div>

      {/* Selectors */}
      <div className={clsx('flex gap-3 mb-6 items-end', isRtl && 'flex-row-reverse')}>
        <SurahSelector value={surahA} onChange={setSurahA} isRtl={isRtl} label={isRtl ? 'السورة الأولى' : 'Surah A'} />
        <div className="flex-shrink-0 text-gray-300 font-bold text-lg pb-3">vs</div>
        <SurahSelector value={surahB} onChange={setSurahB} isRtl={isRtl} label={isRtl ? 'السورة الثانية' : 'Surah B'} />
      </div>

      {/* Header cards */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {([
          { num: surahA, data: dataA, color: 'violet' },
          { num: surahB, data: dataB, color: 'blue' },
        ] as const).map(({ num, data, color }) => (
          <div key={num} className={clsx(
            'rounded-2xl border p-4',
            color === 'violet' ? 'bg-violet-50 border-violet-200' : 'bg-blue-50 border-blue-200'
          )}>
            <p className={clsx('text-xs font-semibold uppercase tracking-wide mb-1',
              color === 'violet' ? 'text-violet-500' : 'text-blue-500',
              isRtl && 'font-arabic text-right'
            )}>
              {isRtl ? `سورة ${num}` : `Surah ${num}`}
            </p>
            <p className={clsx('text-xl font-bold text-gray-900 leading-tight', isRtl ? 'font-arabic text-right' : '')}>
              {isRtl ? data.name?.ar : data.name?.en}
            </p>
            {!isRtl && <p className="text-xs text-gray-500 font-arabic mt-0.5">{data.name?.ar}</p>}
            {isRtl  && <p className="text-xs text-gray-500 mt-0.5">{data.name?.en}</p>}
            <p className={clsx('text-xs text-gray-400 mt-1', isRtl && 'font-arabic text-right')}>
              {data.atlas?.ayahCount ?? '?'} {isRtl ? 'آية' : 'verses'}
            </p>
            {data.atlas && <AyahBar count={data.atlas.ayahCount} maxCount={MAX_AYAHS} />}
          </div>
        ))}
      </div>

      {/* Comparison table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden mb-6">
        <div className="grid grid-cols-3 bg-gray-50 border-b border-gray-100">
          <div className={clsx('px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide', isRtl && 'text-right font-arabic')}>
            {isRtl ? 'المعيار' : 'Attribute'}
          </div>
          <div className={clsx('px-4 py-3 text-xs font-semibold uppercase tracking-wide text-violet-600', isRtl ? 'text-right font-arabic' : 'text-center')}>
            {isRtl ? SURAH_NAMES[surahA - 1]?.ar : SURAH_NAMES[surahA - 1]?.en}
          </div>
          <div className={clsx('px-4 py-3 text-xs font-semibold uppercase tracking-wide text-blue-600', isRtl ? 'text-right font-arabic' : 'text-center')}>
            {isRtl ? SURAH_NAMES[surahB - 1]?.ar : SURAH_NAMES[surahB - 1]?.en}
          </div>
        </div>
        {rows.map((row, i) => (
          <div key={i} className={clsx(
            'grid grid-cols-3 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors',
            row.highlight && 'bg-amber-50/40'
          )}>
            <div className={clsx('px-4 py-3 text-xs font-semibold text-gray-500 flex items-center gap-1', isRtl && 'text-right font-arabic justify-end')}>
              {!isRtl && row.icon && <row.icon className="w-3 h-3 text-gray-300 shrink-0" />}
              {isRtl ? row.labelAr : row.labelEn}
              {row.highlight && <span className="ms-1 text-amber-500">•</span>}
              {isRtl && row.icon && <row.icon className="w-3 h-3 text-gray-300 shrink-0" />}
            </div>
            <div className={clsx('px-4 py-3 text-xs text-gray-800', isRtl ? 'text-right font-arabic' : 'text-center')}>
              {row.renderA ?? '—'}
            </div>
            <div className={clsx('px-4 py-3 text-xs text-gray-800', isRtl ? 'text-right font-arabic' : 'text-center')}>
              {row.renderB ?? '—'}
            </div>
          </div>
        ))}
      </div>

      {/* Mushaf position visualiser */}
      <MushafPositionSection dataA={dataA} dataB={dataB} surahA={surahA} surahB={surahB} isRtl={isRtl} />

      {/* Quick insights */}
      <InsightsSection dataA={dataA} dataB={dataB} isRtl={isRtl} />

      {/* Revelation context */}
      <RevealContextSection dataA={dataA} dataB={dataB} surahA={surahA} surahB={surahB} isRtl={isRtl} />

      {/* Stories section */}
      <StoriesSection dataA={dataA} dataB={dataB} surahA={surahA} surahB={surahB} isRtl={isRtl} />

      {/* Summaries */}
      {(summaryA || summaryB) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {([
            { summary: summaryA, name: isRtl ? dataA.name?.ar : dataA.name?.en, color: 'violet' },
            { summary: summaryB, name: isRtl ? dataB.name?.ar : dataB.name?.en, color: 'blue' },
          ] as const).map(({ summary, name, color }) => summary ? (
            <div key={color} className={clsx(
              'rounded-2xl border p-4',
              color === 'violet' ? 'bg-violet-50/60 border-violet-100' : 'bg-blue-50/60 border-blue-100'
            )}>
              <p className={clsx('text-xs font-bold mb-2',
                color === 'violet' ? 'text-violet-600' : 'text-blue-600',
                isRtl && 'font-arabic text-right'
              )}>
                {name}
              </p>
              <p className={clsx('text-xs text-gray-600 leading-relaxed line-clamp-6', isRtl && 'font-arabic text-right')}>
                {summary}
              </p>
            </div>
          ) : null)}
        </div>
      )}

      {/* Share */}
      <div className={clsx('flex mb-6', isRtl ? 'justify-start' : 'justify-end')}>
        <button
          onClick={() => {
            const url = `${window.location.origin}/compare?a=${surahA}&b=${surahB}`;
            navigator.clipboard?.writeText(url).catch(() => {});
          }}
          className={clsx(
            'flex items-center gap-1.5 rounded-xl border border-gray-200 px-4 py-2 text-xs text-gray-500 hover:border-violet-300 hover:text-violet-600 transition-colors',
            isRtl && 'flex-row-reverse font-arabic'
          )}
        >
          <Share2 className="w-3.5 h-3.5" />
          {isRtl ? 'نسخ رابط المقارنة' : 'Copy comparison link'}
        </button>
      </div>

      <p className={clsx('text-[10px] text-gray-300 text-center', isRtl && 'font-arabic')}>
        {isRtl
          ? 'البيانات من أطلس السور · ترتيب النزول من رواية ابن عباس · سورة المصحف المصري'
          : 'Data from Surah Atlas · Revelation order per Ibn Abbas · Egyptian Standard Mushaf'}
      </p>
    </div>
  );
}
