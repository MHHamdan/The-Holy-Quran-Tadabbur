import React, { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  Megaphone, Users, BookOpen, Filter, Search,
  ChevronDown, ChevronRight, AlertTriangle,
  Grid, List,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';

const API = '/api/v1/quranic-calls';

// ─── Types ────────────────────────────────────────────────────────────────────

interface CallerInfo {
  callerType: string;
  labelArabic?: string;
  labelEnglish?: string;
  confidence: number;
  reviewStatus: string;
}

interface AddresseeInfo {
  addresseeType: string;
  labelArabic: string;
  labelEnglish: string;
  confidence: number;
  reviewStatus: string;
}

interface QuranicCallItem {
  callId: string;
  surahNumber: number;
  ayahNumber: number;
  ayahReference: string;
  surahNameAr: string;
  surahNameEn: string;
  ayahTextUthmani: string;
  callText?: string;
  callPattern: string;
  caller: CallerInfo;
  addressee: AddresseeInfo;
  callFunction: string;
  tone: string;
  relatedTopics: string[];
  relatedProphets: string[];
  confidence: number;
  reviewStatus: string;
  humanReviewRequired: boolean;
  warnings: string[];
  classificationMethod?: string;
}

interface PagedCallsResponse {
  items: QuranicCallItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  latency_ms: number;
}

interface StatisticsResponse {
  totalCalls: number;
  totalAyahsWithCalls: number;
  directYaCalls: number;
  supplicationCalls: number;
  indirectCalls: number;
  needsReview: number;
  verified: number;
  byPattern: Record<string, number>;
  byAddresseeType: Record<string, number>;
  byCallerType: Record<string, number>;
  topSurahs: Array<{ surahNumber: number; surahNameEn: string; count: number }>;
}

// ─── API fetchers ─────────────────────────────────────────────────────────────

const fetchStats = (): Promise<StatisticsResponse> =>
  axios.get(`${API}/statistics`).then((r) => r.data);

const fetchCalls = (
  page: number,
  pageSize: number,
  callPattern?: string,
  addresseeType?: string,
  surah?: number,
  search?: string,
  directOnly?: boolean,
): Promise<PagedCallsResponse> => {
  const params: Record<string, string | number | boolean> = { page, page_size: pageSize };
  if (callPattern) params.call_pattern = callPattern;
  if (addresseeType) params.addressee_type = addresseeType;
  if (surah) params.surah = surah;
  if (directOnly) params.direct_only = true;
  const endpoint = search ? `${API}/search` : `${API}/list`;
  if (search) params.q = search;
  return axios.get(endpoint, { params }).then((r) => r.data);
};

// ─── Colour maps ──────────────────────────────────────────────────────────────

const PATTERN_COLORS: Record<string, string> = {
  ya_ayyuhal:      'bg-emerald-100 text-emerald-800 border-emerald-200',
  ya_ayatuha:      'bg-teal-100 text-teal-800 border-teal-200',
  ya_bani:         'bg-sky-100 text-sky-800 border-sky-200',
  ya_qawmi:        'bg-blue-100 text-blue-800 border-blue-200',
  ya_ibadi:        'bg-violet-100 text-violet-800 border-violet-200',
  ya_ahl:          'bg-indigo-100 text-indigo-800 border-indigo-200',
  ya_rabbi:        'bg-amber-100 text-amber-800 border-amber-200',
  ya_abati:        'bg-orange-100 text-orange-800 border-orange-200',
  ya_bunayya:      'bg-rose-100 text-rose-800 border-rose-200',
  ya_prophet_name: 'bg-purple-100 text-purple-800 border-purple-200',
  ya_lament:       'bg-red-100 text-red-800 border-red-200',
  ya_wish:         'bg-pink-100 text-pink-800 border-pink-200',
  ya_direct:       'bg-cyan-100 text-cyan-800 border-cyan-200',
  supplication:    'bg-yellow-100 text-yellow-800 border-yellow-200',
  unknown:         'bg-gray-100 text-gray-600 border-gray-200',
};

const ADDRESSEE_COLORS: Record<string, string> = {
  believers:        'bg-emerald-50 text-emerald-700',
  mankind:          'bg-blue-50 text-blue-700',
  disbelievers:     'bg-red-50 text-red-700',
  people_of_book:   'bg-orange-50 text-orange-700',
  bani_israel:      'bg-amber-50 text-amber-700',
  prophet:          'bg-purple-50 text-purple-700',
  specific_person:  'bg-indigo-50 text-indigo-700',
  people_or_nation: 'bg-sky-50 text-sky-700',
  family_member:    'bg-rose-50 text-rose-700',
  allah:            'bg-yellow-50 text-yellow-700',
  jinn:             'bg-gray-50 text-gray-700',
  unknown:          'bg-gray-50 text-gray-500',
};

const TONE_COLORS: Record<string, string> = {
  gentle:     'text-emerald-700 bg-emerald-50',
  comforting: 'text-sky-700 bg-sky-50',
  honoring:   'text-purple-700 bg-purple-50',
  neutral:    'text-gray-600 bg-gray-50',
  urgent:     'text-orange-700 bg-orange-50',
  warning:    'text-red-700 bg-red-50',
  rebuking:   'text-rose-700 bg-rose-50',
  needs_review: 'text-gray-400 bg-gray-50',
};

// ─── Pattern label maps ───────────────────────────────────────────────────────

const PATTERN_LABEL_AR: Record<string, string> = {
  ya_ayyuhal: 'يا أيها',
  ya_ayatuha: 'يا أيتها',
  ya_bani: 'يا بني',
  ya_qawmi: 'يا قوم',
  ya_ibadi: 'يا عبادي',
  ya_ahl: 'يا أهل',
  ya_rabbi: 'يا رب',
  ya_abati: 'يا أبت',
  ya_bunayya: 'يا بني (للابن)',
  ya_prophet_name: 'يا + اسم النبي',
  ya_lament: 'نداء الحزن',
  ya_wish: 'نداء التمني',
  ya_direct: 'يا (عام)',
  supplication: 'ربنا / ربي',
  unknown: 'غير محدد',
};

const PATTERN_LABEL_EN: Record<string, string> = {
  ya_ayyuhal: 'يا أيها (m.)',
  ya_ayatuha: 'يا أيتها (f.)',
  ya_bani: 'O Children of',
  ya_qawmi: 'O My People',
  ya_ibadi: 'O My Servants',
  ya_ahl: 'O People of',
  ya_rabbi: 'O My Lord',
  ya_abati: 'O My Father',
  ya_bunayya: 'O Dear Son',
  ya_prophet_name: 'O [Prophet]',
  ya_lament: 'Lament cry',
  ya_wish: 'Wish / Regret',
  ya_direct: 'O (generic)',
  supplication: 'Our/My Lord…',
  unknown: 'Unknown',
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function PatternBadge({ pattern, isRtl }: { pattern: string; isRtl: boolean }) {
  const cls = PATTERN_COLORS[pattern] ?? PATTERN_COLORS.unknown;
  const label = isRtl ? (PATTERN_LABEL_AR[pattern] ?? pattern) : (PATTERN_LABEL_EN[pattern] ?? pattern);
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full border text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}

function ToneBadge({ tone }: { tone: string }) {
  const cls = TONE_COLORS[tone] ?? TONE_COLORS.needs_review;
  const label = tone === 'needs_review' ? '—' : tone.charAt(0).toUpperCase() + tone.slice(1);
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}

function AddresseeBadge({ addresseeType, label }: { addresseeType: string; label: string }) {
  const cls = ADDRESSEE_COLORS[addresseeType] ?? ADDRESSEE_COLORS.unknown;
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}

function ReviewNote() {
  return (
    <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
      <span>
        All caller, addressee, and function classifications are pattern-detected and require scholarly review.
        This atlas is a navigation tool — not a tafsir source.
      </span>
    </div>
  );
}

function CallCard({ call, isRtl, onClick }: { call: QuranicCallItem; isRtl: boolean; onClick: () => void }) {
  const addresseeLabel = isRtl ? call.addressee.labelArabic : call.addressee.labelEnglish;
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white border border-gray-200 rounded-2xl p-4 hover:border-emerald-300 hover:shadow-md transition-all group"
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
            {call.ayahReference}
          </span>
          <PatternBadge pattern={call.callPattern} isRtl={isRtl} />
          {call.tone !== 'needs_review' && <ToneBadge tone={call.tone} />}
        </div>
        <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-emerald-500 transition-colors flex-shrink-0 mt-0.5" />
      </div>

      {/* Ayah text */}
      <div
        dir="rtl"
        className="text-right text-lg leading-relaxed font-arabic text-gray-900 mb-3 line-clamp-2"
      >
        {call.ayahTextUthmani}
      </div>

      {/* Surah name + addressee */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">{isRtl ? call.surahNameAr : call.surahNameEn}</span>
        <AddresseeBadge addresseeType={call.addressee.addresseeType} label={addresseeLabel} />
      </div>
    </button>
  );
}

function CallDetail({ call, isRtl, onClose }: { call: QuranicCallItem; isRtl: boolean; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center p-4">
      <div className="bg-white rounded-3xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="sticky top-0 bg-gradient-to-r from-emerald-700 to-teal-700 text-white p-5 rounded-t-3xl">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium opacity-80">
              {isRtl ? call.surahNameAr : call.surahNameEn}
            </span>
            <button onClick={onClose} className="text-white/80 hover:text-white text-xl leading-none">×</button>
          </div>
          <div className="text-2xl font-bold">{call.ayahReference}</div>
          <div className="flex gap-2 mt-2 flex-wrap">
            <PatternBadge pattern={call.callPattern} isRtl={isRtl} />
            {call.tone !== 'needs_review' && <ToneBadge tone={call.tone} />}
          </div>
        </div>

        <div className="p-5 space-y-4">
          {/* Ayah text */}
          <div
            dir="rtl"
            className="text-right text-xl leading-loose font-arabic text-gray-900 bg-emerald-50 rounded-2xl p-4 border border-emerald-100"
          >
            {call.ayahTextUthmani}
          </div>

          {/* Call phrase */}
          {call.callText && (
            <div>
              <div className="text-xs text-gray-500 mb-1">{isRtl ? 'عبارة النداء' : 'Call phrase'}</div>
              <div dir="rtl" className="text-right text-base font-arabic text-emerald-800 bg-emerald-50 rounded-xl px-3 py-2">
                {call.callText}
              </div>
            </div>
          )}

          {/* Addressee / Caller */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-xl p-3">
              <div className="text-xs text-gray-500 mb-1">{isRtl ? 'المنادَى' : 'Addressee'}</div>
              <AddresseeBadge
                addresseeType={call.addressee.addresseeType}
                label={isRtl ? call.addressee.labelArabic : call.addressee.labelEnglish}
              />
            </div>
            <div className="bg-gray-50 rounded-xl p-3">
              <div className="text-xs text-gray-500 mb-1">{isRtl ? 'المنادِي' : 'Caller'}</div>
              <span className="text-sm font-medium text-gray-700">
                {isRtl
                  ? (call.caller.labelArabic ?? call.caller.callerType)
                  : (call.caller.labelEnglish ?? call.caller.callerType)}
              </span>
            </div>
          </div>

          {/* Function + Tone */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-xl p-3">
              <div className="text-xs text-gray-500 mb-1">{isRtl ? 'وظيفة النداء' : 'Function'}</div>
              <span className="text-sm capitalize text-gray-700">{call.callFunction.replace(/_/g, ' ')}</span>
            </div>
            <div className="bg-gray-50 rounded-xl p-3">
              <div className="text-xs text-gray-500 mb-1">{isRtl ? 'النبرة' : 'Tone'}</div>
              <ToneBadge tone={call.tone} />
            </div>
          </div>

          {/* Topics */}
          {call.relatedTopics.length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-2">{isRtl ? 'الموضوعات' : 'Topics'}</div>
              <div className="flex flex-wrap gap-1" dir={isRtl ? 'rtl' : 'ltr'}>
                {call.relatedTopics.map((t) => (
                  <span key={t} className="text-xs px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-100">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Prophets */}
          {call.relatedProphets.length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-2">{isRtl ? 'الأنبياء' : 'Prophets'}</div>
              <div className="flex flex-wrap gap-1">
                {call.relatedProphets.map((p) => (
                  <span key={p} className="text-xs px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full border border-purple-100">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Warnings */}
          {call.warnings.length > 0 && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                {call.warnings.map((w, i) => <div key={i}>{w}</div>)}
              </div>
            </div>
          )}

          <ReviewNote />

          <div className="text-xs text-gray-400 text-center">
            {isRtl ? 'معرّف النداء' : 'Call ID'}: {call.callId}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Audience Journey component ───────────────────────────────────────────────

const AUDIENCE_TYPES = [
  { type: 'believers', arLabel: 'الذين آمنوا', enLabel: 'Believers', icon: '🌙', color: 'bg-emerald-100 border-emerald-300' },
  { type: 'mankind', arLabel: 'الناس', enLabel: 'Mankind', icon: '🌍', color: 'bg-blue-100 border-blue-300' },
  { type: 'disbelievers', arLabel: 'الكافرون', enLabel: 'Disbelievers', icon: '⚠️', color: 'bg-red-100 border-red-300' },
  { type: 'people_of_book', arLabel: 'أهل الكتاب', enLabel: 'People of Book', icon: '📖', color: 'bg-orange-100 border-orange-300' },
  { type: 'bani_israel', arLabel: 'بني إسرائيل', enLabel: 'Bani Israel', icon: '✡️', color: 'bg-amber-100 border-amber-300' },
  { type: 'prophet', arLabel: 'النبي', enLabel: 'Prophet', icon: '⭐', color: 'bg-purple-100 border-purple-300' },
  { type: 'allah', arLabel: 'الله', enLabel: 'Allah', icon: '☪️', color: 'bg-yellow-100 border-yellow-300' },
  { type: 'people_or_nation', arLabel: 'قوم', enLabel: 'People/Nation', icon: '🏛️', color: 'bg-sky-100 border-sky-300' },
  { type: 'family_member', arLabel: 'الأسرة', enLabel: 'Family', icon: '👨‍👩‍👦', color: 'bg-rose-100 border-rose-300' },
];

function AudienceJourney({ stats, isRtl, onSelect }: {
  stats: StatisticsResponse;
  isRtl: boolean;
  onSelect: (type: string) => void;
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-bold text-gray-900">
        {isRtl ? 'رحلة المنادَى — من يُخاطَب في القرآن؟' : 'Audience Journey — Who Is Addressed in the Quran?'}
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {AUDIENCE_TYPES.map((a) => {
          const count = stats.byAddresseeType[a.type] ?? 0;
          if (count === 0) return null;
          return (
            <button
              key={a.type}
              onClick={() => onSelect(a.type)}
              className={`flex items-center gap-3 p-3 rounded-2xl border-2 ${a.color} hover:shadow-md transition-all text-left`}
            >
              <span className="text-2xl">{a.icon}</span>
              <div>
                <div className="font-semibold text-sm text-gray-900">
                  {isRtl ? a.arLabel : a.enLabel}
                </div>
                <div className="text-xs text-gray-500">{count} {isRtl ? 'نداء' : 'calls'}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Top Surahs component ─────────────────────────────────────────────────────

function TopSurahsChart({ topSurahs, isRtl, onSelect }: {
  topSurahs: Array<{ surahNumber: number; surahNameEn: string; count: number }>;
  isRtl: boolean;
  onSelect: (n: number) => void;
}) {
  const max = topSurahs[0]?.count ?? 1;
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-bold text-gray-900">
        {isRtl ? 'السور الأكثر نداءً' : 'Surahs with Most Calls'}
      </h3>
      <div className="space-y-2">
        {topSurahs.slice(0, 10).map((s, i) => (
          <button
            key={s.surahNumber}
            onClick={() => onSelect(s.surahNumber)}
            className="w-full flex items-center gap-3 text-left group hover:opacity-90"
          >
            <span className="text-xs text-gray-400 w-5 text-right">{i + 1}</span>
            <div className="flex-1">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="font-medium text-gray-800 group-hover:text-emerald-700">
                  {s.surahNameEn} ({s.surahNumber})
                </span>
                <span className="text-gray-500">{s.count}</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all"
                  style={{ width: `${(s.count / max) * 100}%` }}
                />
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Filter panel ─────────────────────────────────────────────────────────────

const ALL_PATTERNS = [
  'ya_ayyuhal', 'ya_ayatuha', 'ya_bani', 'ya_qawmi', 'ya_ibadi',
  'ya_ahl', 'ya_rabbi', 'ya_abati', 'ya_bunayya', 'ya_prophet_name',
  'ya_lament', 'ya_wish', 'ya_direct', 'supplication',
];

const ALL_ADDRESSEE_TYPES = [
  'believers', 'mankind', 'disbelievers', 'people_of_book', 'bani_israel',
  'prophet', 'specific_person', 'people_or_nation', 'family_member',
  'allah', 'jinn', 'unknown',
];

function FilterPanel({
  isRtl,
  callPattern, setCallPattern,
  addresseeType, setAddresseeType,
  surah, setSurah,
  directOnly, setDirectOnly,
  onClear,
}: {
  isRtl: boolean;
  callPattern: string;
  setCallPattern: (v: string) => void;
  addresseeType: string;
  setAddresseeType: (v: string) => void;
  surah: string;
  setSurah: (v: string) => void;
  directOnly: boolean;
  setDirectOnly: (v: boolean) => void;
  onClear: () => void;
}) {
  const hasFilters = !!(callPattern || addresseeType || surah || directOnly);
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
          <Filter className="w-4 h-4" />
          {isRtl ? 'تصفية' : 'Filter'}
        </div>
        {hasFilters && (
          <button onClick={onClear} className="text-xs text-emerald-600 hover:text-emerald-800">
            {isRtl ? 'مسح' : 'Clear'}
          </button>
        )}
      </div>

      <select
        value={callPattern}
        onChange={(e) => setCallPattern(e.target.value)}
        className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        <option value="">{isRtl ? 'كل الأنماط' : 'All patterns'}</option>
        {ALL_PATTERNS.map((p) => (
          <option key={p} value={p}>{isRtl ? (PATTERN_LABEL_AR[p] ?? p) : (PATTERN_LABEL_EN[p] ?? p)}</option>
        ))}
      </select>

      <select
        value={addresseeType}
        onChange={(e) => setAddresseeType(e.target.value)}
        className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        <option value="">{isRtl ? 'كل المنادَين' : 'All addressees'}</option>
        {ALL_ADDRESSEE_TYPES.map((t) => (
          <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
        ))}
      </select>

      <input
        type="number"
        value={surah}
        onChange={(e) => setSurah(e.target.value)}
        placeholder={isRtl ? 'رقم السورة (1-114)' : 'Surah number (1-114)'}
        min={1}
        max={114}
        className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
      />

      <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
        <input
          type="checkbox"
          checked={directOnly}
          onChange={(e) => setDirectOnly(e.target.checked)}
          className="rounded"
        />
        {isRtl ? 'النداءات المباشرة فقط (يا)' : 'Direct يا calls only'}
      </label>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

type ViewMode = 'browse' | 'audience' | 'surahs';

export default function QuranicCallsAtlasPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [view, setView] = useState<ViewMode>('browse');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [callPattern, setCallPattern] = useState('');
  const [addresseeType, setAddresseeType] = useState('');
  const [surah, setSurah] = useState('');
  const [directOnly, setDirectOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCall, setSelectedCall] = useState<QuranicCallItem | null>(null);
  const [displayMode, setDisplayMode] = useState<'grid' | 'list'>('grid');

  const PAGE_SIZE = 20;

  const statsQuery = useQuery<StatisticsResponse>({
    queryKey: ['quranic-calls-stats'],
    queryFn: fetchStats,
    staleTime: 5 * 60 * 1000,
  });

  const callsQuery = useQuery<PagedCallsResponse>({
    queryKey: ['quranic-calls', page, callPattern, addresseeType, surah, directOnly, search],
    queryFn: () => fetchCalls(
      page, PAGE_SIZE,
      callPattern || undefined,
      addresseeType || undefined,
      surah ? Number(surah) : undefined,
      search || undefined,
      directOnly || undefined,
    ),
    staleTime: 2 * 60 * 1000,
  });

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
    setPage(1);
  }, [searchInput]);

  const clearFilters = useCallback(() => {
    setCallPattern(''); setAddresseeType(''); setSurah(''); setDirectOnly(false);
    setSearch(''); setSearchInput(''); setPage(1);
  }, []);

  const hasFilters = !!(callPattern || addresseeType || surah || directOnly || search);

  const stats = statsQuery.data;

  const heroBgClass = 'bg-gradient-to-br from-emerald-700 via-teal-700 to-green-800';

  return (
    <div className="min-h-screen bg-gray-50" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Hero */}
      <div className={`${heroBgClass} text-white`}>
        <div className="max-w-5xl mx-auto px-4 py-10 md:py-14">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 bg-white/20 rounded-2xl">
              <Megaphone className="w-7 h-7" />
            </div>
            <span className="text-sm font-medium bg-white/20 px-3 py-1 rounded-full">
              {isRtl ? 'القرآن الكريم' : 'Quranic Atlas'}
            </span>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold mb-2" dir="rtl">
            أطلس النداءات القرآنية
          </h1>
          <p className="text-white/80 text-base mb-6" dir={isRtl ? 'rtl' : 'ltr'}>
            {isRtl
              ? 'كل نداء وخطاب في القرآن الكريم — اكتشف من نودي وكيف'
              : 'Every call and address in the Quran — discover who was called and how'}
          </p>

          {/* Stat pills */}
          {stats && (
            <div className="flex flex-wrap gap-3">
              {[
                { val: stats.totalCalls, label: isRtl ? 'نداء' : 'Total calls' },
                { val: stats.directYaCalls, label: isRtl ? 'نداء يا' : 'Direct يا' },
                { val: stats.supplicationCalls, label: isRtl ? 'دعاء' : 'Supplications' },
                { val: stats.totalAyahsWithCalls, label: isRtl ? 'آية' : 'Ayahs' },
              ].map((pill) => (
                <div key={pill.label} className="bg-white/15 backdrop-blur rounded-2xl px-4 py-2">
                  <span className="font-bold text-lg">{pill.val}</span>
                  <span className="text-white/70 text-sm ms-1.5">{pill.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {/* Disclaimer */}
        <ReviewNote />

        {/* View mode tabs */}
        <div className="flex gap-2 flex-wrap">
          {[
            { key: 'browse', label: isRtl ? 'تصفح' : 'Browse', icon: <List className="w-4 h-4" /> },
            { key: 'audience', label: isRtl ? 'المنادَون' : 'Audience', icon: <Users className="w-4 h-4" /> },
            { key: 'surahs', label: isRtl ? 'السور' : 'By Surah', icon: <BookOpen className="w-4 h-4" /> },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setView(tab.key as ViewMode)}
              className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-sm font-medium transition-all ${
                view === tab.key
                  ? 'bg-emerald-700 text-white shadow'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-emerald-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Audience view */}
        {view === 'audience' && stats && (
          <div className="bg-white border border-gray-200 rounded-2xl p-5">
            <AudienceJourney
              stats={stats}
              isRtl={isRtl}
              onSelect={(type) => {
                setAddresseeType(type);
                setView('browse');
                setPage(1);
              }}
            />
          </div>
        )}

        {/* Surahs view */}
        {view === 'surahs' && stats && (
          <div className="bg-white border border-gray-200 rounded-2xl p-5">
            <TopSurahsChart
              topSurahs={stats.topSurahs}
              isRtl={isRtl}
              onSelect={(n) => {
                setSurah(String(n));
                setView('browse');
                setPage(1);
              }}
            />
          </div>
        )}

        {/* Browse view */}
        {view === 'browse' && (
          <div className="space-y-4">
            {/* Search + filter toggle */}
            <div className="flex gap-3">
              <form onSubmit={handleSearch} className="flex-1 flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder={isRtl ? 'ابحث في النداءات…' : 'Search calls…'}
                    className="w-full ps-9 pe-4 py-2.5 border border-gray-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
                  />
                </div>
                <button type="submit" className="px-4 py-2 bg-emerald-700 text-white rounded-2xl text-sm hover:bg-emerald-800">
                  {isRtl ? 'بحث' : 'Search'}
                </button>
              </form>

              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl border text-sm transition-all ${
                  showFilters || hasFilters
                    ? 'border-emerald-400 text-emerald-700 bg-emerald-50'
                    : 'border-gray-200 text-gray-600 bg-white hover:border-emerald-300'
                }`}
              >
                <Filter className="w-4 h-4" />
                {hasFilters && <span className="w-2 h-2 rounded-full bg-emerald-600" />}
                {showFilters ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              </button>

              <div className="flex gap-1 bg-white border border-gray-200 rounded-2xl p-1">
                <button
                  onClick={() => setDisplayMode('grid')}
                  className={`p-1.5 rounded-xl ${displayMode === 'grid' ? 'bg-emerald-100 text-emerald-700' : 'text-gray-400'}`}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setDisplayMode('list')}
                  className={`p-1.5 rounded-xl ${displayMode === 'list' ? 'bg-emerald-100 text-emerald-700' : 'text-gray-400'}`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Active filters display */}
            {hasFilters && (
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-xs text-gray-500">{isRtl ? 'فلاتر نشطة:' : 'Active filters:'}</span>
                {callPattern && (
                  <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
                    {PATTERN_LABEL_EN[callPattern] ?? callPattern}
                    <button onClick={() => setCallPattern('')} className="ms-1 opacity-60 hover:opacity-100">×</button>
                  </span>
                )}
                {addresseeType && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                    {addresseeType.replace(/_/g, ' ')}
                    <button onClick={() => setAddresseeType('')} className="ms-1 opacity-60 hover:opacity-100">×</button>
                  </span>
                )}
                {surah && (
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                    {isRtl ? 'سورة' : 'Surah'} {surah}
                    <button onClick={() => setSurah('')} className="ms-1 opacity-60 hover:opacity-100">×</button>
                  </span>
                )}
                {directOnly && (
                  <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                    يا only
                    <button onClick={() => setDirectOnly(false)} className="ms-1 opacity-60 hover:opacity-100">×</button>
                  </span>
                )}
                {search && (
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                    "{search}"
                    <button onClick={() => { setSearch(''); setSearchInput(''); }} className="ms-1 opacity-60 hover:opacity-100">×</button>
                  </span>
                )}
              </div>
            )}

            {/* Filter panel */}
            {showFilters && (
              <FilterPanel
                isRtl={isRtl}
                callPattern={callPattern} setCallPattern={(v) => { setCallPattern(v); setPage(1); }}
                addresseeType={addresseeType} setAddresseeType={(v) => { setAddresseeType(v); setPage(1); }}
                surah={surah} setSurah={(v) => { setSurah(v); setPage(1); }}
                directOnly={directOnly} setDirectOnly={(v) => { setDirectOnly(v); setPage(1); }}
                onClear={clearFilters}
              />
            )}

            {/* Results */}
            {callsQuery.isLoading && (
              <div className="text-center py-12 text-gray-400">
                {isRtl ? 'جاري التحميل…' : 'Loading…'}
              </div>
            )}

            {callsQuery.isError && (
              <div className="text-center py-8 text-red-500">
                {isRtl ? 'خطأ في تحميل البيانات' : 'Failed to load data'}
              </div>
            )}

            {callsQuery.data && (
              <>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>
                    {callsQuery.data.total} {isRtl ? 'نداء' : 'calls'}
                    {callsQuery.data.totalPages > 1 && ` — ${isRtl ? 'صفحة' : 'Page'} ${callsQuery.data.page}/${callsQuery.data.totalPages}`}
                  </span>
                  <span className="text-xs text-gray-300">{callsQuery.data.latency_ms}ms</span>
                </div>

                <div className={
                  displayMode === 'grid'
                    ? 'grid grid-cols-1 sm:grid-cols-2 gap-3'
                    : 'space-y-2'
                }>
                  {callsQuery.data.items.map((call) => (
                    <CallCard
                      key={call.callId}
                      call={call}
                      isRtl={isRtl}
                      onClick={() => setSelectedCall(call)}
                    />
                  ))}
                </div>

                {callsQuery.data.items.length === 0 && (
                  <div className="text-center py-12 text-gray-400">
                    {isRtl ? 'لا توجد نتائج' : 'No results found'}
                  </div>
                )}

                {/* Pagination */}
                {callsQuery.data.totalPages > 1 && (
                  <div className="flex items-center justify-center gap-3 pt-2">
                    <button
                      disabled={page <= 1}
                      onClick={() => setPage(page - 1)}
                      className="px-4 py-2 rounded-xl border border-gray-200 text-sm disabled:opacity-40 hover:border-emerald-400"
                    >
                      {isRtl ? 'السابق' : 'Previous'}
                    </button>
                    <span className="text-sm text-gray-600">
                      {page} / {callsQuery.data.totalPages}
                    </span>
                    <button
                      disabled={page >= callsQuery.data.totalPages}
                      onClick={() => setPage(page + 1)}
                      className="px-4 py-2 rounded-xl border border-gray-200 text-sm disabled:opacity-40 hover:border-emerald-400"
                    >
                      {isRtl ? 'التالي' : 'Next'}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedCall && (
        <CallDetail
          call={selectedCall}
          isRtl={isRtl}
          onClose={() => setSelectedCall(null)}
        />
      )}
    </div>
  );
}
