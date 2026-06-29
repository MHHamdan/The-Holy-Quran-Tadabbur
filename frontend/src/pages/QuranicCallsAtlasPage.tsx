import React, { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  Megaphone, Users, BookOpen, Filter, Search,
  ChevronRight, AlertTriangle, X,
  Grid, List, BarChart2, Globe2,
  Book, Star, Heart, Zap, ArrowRight,
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
interface PagedResponse {
  items: QuranicCallItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  latency_ms: number;
}
interface Statistics {
  totalCalls: number;
  totalAyahsWithCalls: number;
  directYaCalls: number;
  supplicationCalls: number;
  needsReview: number;
  verified: number;
  byPattern: Record<string, number>;
  byAddresseeType: Record<string, number>;
  byCallerType: Record<string, number>;
  topSurahs: Array<{ surahNumber: number; surahNameEn: string; count: number }>;
  bySurah: Record<number, number>;
}

// ─── API ──────────────────────────────────────────────────────────────────────

const fetchStats = (): Promise<Statistics> =>
  axios.get(`${API}/statistics`).then(r => r.data);

const fetchCalls = (
  page: number, pageSize: number,
  callPattern?: string, addresseeType?: string,
  surah?: number, callFunction?: string,
  search?: string, directOnly?: boolean,
): Promise<PagedResponse> => {
  const params: Record<string, string | number | boolean> = { page, page_size: pageSize };
  if (callPattern) params.call_pattern = callPattern;
  if (addresseeType) params.addressee_type = addresseeType;
  if (surah) params.surah = surah;
  if (callFunction) params.call_function = callFunction;
  if (directOnly) params.direct_only = true;
  const endpoint = search ? `${API}/search` : `${API}/list`;
  if (search) params.q = search;
  return axios.get(endpoint, { params }).then(r => r.data);
};

// ─── Colour + label maps ──────────────────────────────────────────────────────

const PATTERN_CFG: Record<string, { ar: string; en: string; color: string; bg: string; border: string }> = {
  ya_ayyuhal:      { ar:'يا أيها', en:'يا أيها', color:'text-emerald-800', bg:'bg-emerald-100', border:'border-emerald-300' },
  ya_ayatuha:      { ar:'يا أيتها', en:'يا أيتها', color:'text-teal-800', bg:'bg-teal-100', border:'border-teal-300' },
  ya_bani:         { ar:'يا بني', en:'O Children of', color:'text-sky-800', bg:'bg-sky-100', border:'border-sky-300' },
  ya_qawmi:        { ar:'يا قوم', en:'O My People', color:'text-blue-800', bg:'bg-blue-100', border:'border-blue-300' },
  ya_ibadi:        { ar:'يا عبادي', en:'O My Servants', color:'text-violet-800', bg:'bg-violet-100', border:'border-violet-300' },
  ya_ahl:          { ar:'يا أهل', en:'O People of', color:'text-indigo-800', bg:'bg-indigo-100', border:'border-indigo-300' },
  ya_rabbi:        { ar:'يا رب', en:'O My Lord', color:'text-amber-800', bg:'bg-amber-100', border:'border-amber-300' },
  ya_abati:        { ar:'يا أبت', en:'O Father', color:'text-orange-800', bg:'bg-orange-100', border:'border-orange-300' },
  ya_bunayya:      { ar:'يا بني', en:'O Dear Son', color:'text-rose-800', bg:'bg-rose-100', border:'border-rose-300' },
  ya_prophet_name: { ar:'يا + اسم', en:'O [Prophet]', color:'text-purple-800', bg:'bg-purple-100', border:'border-purple-300' },
  ya_lament:       { ar:'نداء حزن', en:'Lament', color:'text-red-800', bg:'bg-red-100', border:'border-red-300' },
  ya_wish:         { ar:'يا ليت', en:'O if only', color:'text-pink-800', bg:'bg-pink-100', border:'border-pink-300' },
  ya_direct:       { ar:'يا (عام)', en:'O (generic)', color:'text-cyan-800', bg:'bg-cyan-100', border:'border-cyan-300' },
  supplication:    { ar:'ربنا / ربي', en:'Supplication', color:'text-yellow-800', bg:'bg-yellow-100', border:'border-yellow-300' },
  unknown:         { ar:'غير محدد', en:'Unknown', color:'text-gray-600', bg:'bg-gray-100', border:'border-gray-200' },
};

const FUNCTION_CFG: Record<string, { ar: string; en: string; icon: string; color: string }> = {
  command:      { ar:'أمر', en:'Command', icon:'⚡', color:'text-orange-700 bg-orange-50 border-orange-200' },
  prohibition:  { ar:'نهي', en:'Prohibition', icon:'🚫', color:'text-red-700 bg-red-50 border-red-200' },
  instruction:  { ar:'توجيه', en:'Instruction', icon:'📋', color:'text-blue-700 bg-blue-50 border-blue-200' },
  warning:      { ar:'تحذير', en:'Warning', icon:'⚠️', color:'text-red-700 bg-red-50 border-red-200' },
  reminder:     { ar:'تذكير', en:'Reminder', icon:'💡', color:'text-amber-700 bg-amber-50 border-amber-200' },
  comfort:      { ar:'تسلية', en:'Comfort', icon:'🕊️', color:'text-sky-700 bg-sky-50 border-sky-200' },
  invitation:   { ar:'دعوة', en:'Invitation', icon:'✋', color:'text-emerald-700 bg-emerald-50 border-emerald-200' },
  rebuke:       { ar:'توبيخ', en:'Rebuke', icon:'👆', color:'text-rose-700 bg-rose-50 border-rose-200' },
  question:     { ar:'سؤال', en:'Question', icon:'❓', color:'text-purple-700 bg-purple-50 border-purple-200' },
  supplication: { ar:'دعاء', en:'Supplication', icon:'🤲', color:'text-yellow-700 bg-yellow-50 border-yellow-200' },
  prohibition_1:{ ar:'نهي', en:'Prohibition', icon:'🚫', color:'text-red-700 bg-red-50 border-red-200' },
  promise:      { ar:'وعد', en:'Promise', icon:'⭐', color:'text-teal-700 bg-teal-50 border-teal-200' },
  threat:       { ar:'وعيد', en:'Threat', icon:'⚡', color:'text-orange-700 bg-orange-50 border-orange-200' },
  dialogue:     { ar:'حوار', en:'Dialogue', icon:'💬', color:'text-indigo-700 bg-indigo-50 border-indigo-200' },
  storytelling: { ar:'سرد', en:'Narrative', icon:'📖', color:'text-gray-700 bg-gray-50 border-gray-200' },
  lament:       { ar:'حزن', en:'Lament', icon:'😔', color:'text-gray-700 bg-gray-100 border-gray-300' },
  mercy:        { ar:'رحمة', en:'Mercy', icon:'💚', color:'text-green-700 bg-green-50 border-green-200' },
  needs_review: { ar:'مراجعة', en:'Review needed', icon:'👁', color:'text-gray-400 bg-gray-50 border-gray-100' },
};

const TONE_CFG: Record<string, { color: string; dot: string }> = {
  gentle:     { color:'text-emerald-700 bg-emerald-50', dot:'bg-emerald-400' },
  comforting: { color:'text-sky-700 bg-sky-50',         dot:'bg-sky-400' },
  honoring:   { color:'text-purple-700 bg-purple-50',   dot:'bg-purple-400' },
  neutral:    { color:'text-gray-600 bg-gray-50',       dot:'bg-gray-300' },
  urgent:     { color:'text-orange-700 bg-orange-50',   dot:'bg-orange-400' },
  warning:    { color:'text-red-700 bg-red-50',         dot:'bg-red-400' },
  rebuking:   { color:'text-rose-700 bg-rose-50',       dot:'bg-rose-400' },
  needs_review:{ color:'text-gray-300 bg-gray-50',      dot:'bg-gray-200' },
};

const ADDRESSEE_CFG: Record<string, { ar: string; en: string; icon: string; color: string }> = {
  believers:        { ar:'الذين آمنوا', en:'Believers',       icon:'🌙', color:'bg-emerald-100 text-emerald-800' },
  mankind:          { ar:'الناس',       en:'Mankind',          icon:'🌍', color:'bg-blue-100 text-blue-800' },
  disbelievers:     { ar:'الكافرون',    en:'Disbelievers',     icon:'⚔️', color:'bg-red-100 text-red-800' },
  people_of_book:   { ar:'أهل الكتاب', en:'People of Book',   icon:'📖', color:'bg-orange-100 text-orange-800' },
  bani_israel:      { ar:'بني إسرائيل', en:'Bani Israel',     icon:'✡️', color:'bg-amber-100 text-amber-800' },
  prophet:          { ar:'النبي',       en:'Prophet',          icon:'⭐', color:'bg-purple-100 text-purple-800' },
  specific_person:  { ar:'شخص',         en:'Specific Person',  icon:'👤', color:'bg-indigo-100 text-indigo-800' },
  people_or_nation: { ar:'قوم',         en:'People/Nation',    icon:'🏛️', color:'bg-sky-100 text-sky-800' },
  family_member:    { ar:'الأسرة',      en:'Family Member',    icon:'👨‍👩‍👦', color:'bg-rose-100 text-rose-800' },
  allah:            { ar:'الله',        en:'Allah',            icon:'☪️', color:'bg-yellow-100 text-yellow-800' },
  jinn:             { ar:'الجن',        en:'Jinn',             icon:'🌀', color:'bg-gray-100 text-gray-700' },
  unknown:          { ar:'غير محدد',    en:'Unknown',          icon:'❓', color:'bg-gray-100 text-gray-500' },
};

const CALLER_CFG: Record<string, { ar: string; en: string; icon: string; color: string }> = {
  allah:            { ar:'الله',        en:'Allah',            icon:'☪️', color:'bg-yellow-50 text-yellow-800' },
  prophet:          { ar:'نبي',         en:'Prophet',          icon:'⭐', color:'bg-purple-50 text-purple-800' },
  people_group:     { ar:'جماعة',       en:'People Group',     icon:'👥', color:'bg-sky-50 text-sky-800' },
  unknown:          { ar:'غير محدد',    en:'Unknown',          icon:'❓', color:'bg-gray-50 text-gray-600' },
  angel:            { ar:'ملك',         en:'Angel',            icon:'👼', color:'bg-blue-50 text-blue-800' },
  believer:         { ar:'مؤمن',        en:'Believer',         icon:'🙏', color:'bg-emerald-50 text-emerald-800' },
  disbeliever:      { ar:'كافر',        en:'Disbeliever',      icon:'❌', color:'bg-red-50 text-red-800' },
  family_member:    { ar:'فرد الأسرة',  en:'Family Member',    icon:'👨‍👩‍👦', color:'bg-rose-50 text-rose-800' },
  jinn:             { ar:'جني',         en:'Jinn',             icon:'🌀', color:'bg-gray-50 text-gray-700' },
  narrative_speaker:{ ar:'سردي',        en:'Narrative',        icon:'📖', color:'bg-gray-50 text-gray-600' },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function PatternChip({ pattern, isRtl }: { pattern: string; isRtl: boolean }) {
  const cfg = PATTERN_CFG[pattern] ?? PATTERN_CFG.unknown;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${cfg.color} ${cfg.bg} ${cfg.border}`}>
      {isRtl ? cfg.ar : cfg.en}
    </span>
  );
}

function FunctionChip({ fn, isRtl }: { fn: string; isRtl: boolean }) {
  const cfg = FUNCTION_CFG[fn] ?? FUNCTION_CFG.needs_review;
  if (fn === 'needs_review') return null;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${cfg.color}`}>
      {cfg.icon} {isRtl ? cfg.ar : cfg.en}
    </span>
  );
}

function ToneChip({ tone }: { tone: string }) {
  const cfg = TONE_CFG[tone] ?? TONE_CFG.needs_review;
  if (tone === 'needs_review') return null;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {tone.charAt(0).toUpperCase() + tone.slice(1)}
    </span>
  );
}

function AddresseeChip({ addresseeType, label }: { addresseeType: string; label: string }) {
  const cfg = ADDRESSEE_CFG[addresseeType] ?? ADDRESSEE_CFG.unknown;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      {cfg.icon} {label}
    </span>
  );
}

function ReviewNote({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`flex items-start gap-2 ${compact ? 'p-2' : 'p-3'} bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800`}>
      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
      <span>
        {compact
          ? 'All classifications are pattern-detected and need scholarly review.'
          : 'All caller, addressee, function, and tone classifications are pattern-detected and require scholarly review. This is a navigation atlas — not a tafsir source.'}
      </span>
    </div>
  );
}

// ─── Call card ────────────────────────────────────────────────────────────────

function CallCard({
  call, isRtl, onClick, compact = false,
}: {
  call: QuranicCallItem;
  isRtl: boolean;
  onClick: () => void;
  compact?: boolean;
}) {
  const addrLabel = isRtl ? call.addressee.labelArabic : call.addressee.labelEnglish;
  const hasFn = call.callFunction !== 'needs_review';
  const hasTone = call.tone !== 'needs_review';

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white border border-gray-200 rounded-2xl hover:border-emerald-300 hover:shadow-md transition-all group"
    >
      {/* Coloured top strip based on pattern */}
      <div className={`h-1 rounded-t-2xl ${(PATTERN_CFG[call.callPattern] ?? PATTERN_CFG.unknown).bg} border-b ${(PATTERN_CFG[call.callPattern] ?? PATTERN_CFG.unknown).border}`} />
      <div className={`p-${compact ? '3' : '4'}`}>
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              {call.ayahReference}
            </span>
            <PatternChip pattern={call.callPattern} isRtl={isRtl} />
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-emerald-500 transition-colors flex-shrink-0 mt-0.5" />
        </div>

        {/* Ayah text */}
        <div
          dir="rtl"
          className={`text-right leading-relaxed font-arabic text-gray-900 mb-2 line-clamp-2 ${compact ? 'text-base' : 'text-lg'}`}
        >
          {call.ayahTextUthmani}
        </div>

        {/* Function + Tone chips */}
        {(hasFn || hasTone) && (
          <div className="flex flex-wrap gap-1 mb-2">
            {hasFn && <FunctionChip fn={call.callFunction} isRtl={isRtl} />}
            {hasTone && <ToneChip tone={call.tone} />}
          </div>
        )}

        {/* Footer: surah name + addressee */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">{isRtl ? call.surahNameAr : call.surahNameEn}</span>
          <AddresseeChip addresseeType={call.addressee.addresseeType} label={addrLabel} />
        </div>
      </div>
    </button>
  );
}

// ─── Call detail modal ────────────────────────────────────────────────────────

function CallDetailModal({ call, isRtl, onClose }: { call: QuranicCallItem; isRtl: boolean; onClose: () => void }) {
  const addrCfg = ADDRESSEE_CFG[call.addressee.addresseeType] ?? ADDRESSEE_CFG.unknown;
  const callerCfg = CALLER_CFG[call.caller.callerType] ?? CALLER_CFG.unknown;
  const patCfg = PATTERN_CFG[call.callPattern] ?? PATTERN_CFG.unknown;
  const fnCfg = FUNCTION_CFG[call.callFunction] ?? FUNCTION_CFG.needs_review;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-2 sm:p-4">
      <div className="bg-white rounded-3xl w-full max-w-xl max-h-[92vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className={`${patCfg.bg} ${patCfg.border} border-b p-5 rounded-t-3xl`}>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-600">
                {isRtl ? call.surahNameAr : call.surahNameEn}
              </span>
              <span className="text-gray-300">·</span>
              <span className="text-xs text-gray-500">{call.ayahReference}</span>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-xl hover:bg-black/10 transition-colors"
            >
              <X className="w-4 h-4 text-gray-600" />
            </button>
          </div>
          <div className="flex gap-2 flex-wrap mt-2">
            <PatternChip pattern={call.callPattern} isRtl={isRtl} />
            <FunctionChip fn={call.callFunction} isRtl={isRtl} />
            <ToneChip tone={call.tone} />
          </div>
        </div>

        <div className="p-5 space-y-4">
          {/* Ayah text */}
          <div
            dir="rtl"
            className="text-right text-xl leading-loose font-arabic text-gray-900 bg-gray-50 rounded-2xl p-4 border border-gray-100"
          >
            {call.ayahTextUthmani}
          </div>

          {/* Call phrase highlight */}
          {call.callText && (
            <div>
              <p className="text-xs text-gray-400 mb-1">{isRtl ? 'عبارة النداء' : 'Call phrase detected'}</p>
              <div dir="rtl" className={`text-right text-base font-arabic font-semibold ${patCfg.color} ${patCfg.bg} rounded-xl px-3 py-2 border ${patCfg.border}`}>
                {call.callText}
              </div>
            </div>
          )}

          {/* Caller → Addressee */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-gray-100 p-3 bg-gray-50">
              <p className="text-xs text-gray-400 mb-1.5">{isRtl ? 'المنادِي' : 'Caller'}</p>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-medium ${callerCfg.color}`}>
                {callerCfg.icon} {isRtl ? callerCfg.ar : callerCfg.en}
              </span>
            </div>
            <div className="rounded-xl border border-gray-100 p-3 bg-gray-50">
              <p className="text-xs text-gray-400 mb-1.5">{isRtl ? 'المنادَى' : 'Addressee'}</p>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-medium ${addrCfg.color}`}>
                {addrCfg.icon} {isRtl ? addrCfg.ar : addrCfg.en}
              </span>
            </div>
          </div>

          {/* Function + Tone grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-gray-100 p-3">
              <p className="text-xs text-gray-400 mb-1">{isRtl ? 'الوظيفة' : 'Function'}</p>
              <span className={`inline-flex items-center gap-1 text-sm font-medium ${fnCfg.color} rounded-lg px-2 py-0.5 border`}>
                {fnCfg.icon} {isRtl ? fnCfg.ar : fnCfg.en}
              </span>
            </div>
            <div className="rounded-xl border border-gray-100 p-3">
              <p className="text-xs text-gray-400 mb-1">{isRtl ? 'النبرة' : 'Tone'}</p>
              <ToneChip tone={call.tone} />
            </div>
          </div>

          {/* Confidence bar */}
          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{isRtl ? 'ثقة الكشف' : 'Detection confidence'}</span>
              <span>{Math.round(call.confidence * 100)}%</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${call.confidence >= 0.8 ? 'bg-emerald-400' : call.confidence >= 0.6 ? 'bg-amber-400' : 'bg-red-300'}`}
                style={{ width: `${call.confidence * 100}%` }}
              />
            </div>
          </div>

          {/* Topics */}
          {call.relatedTopics.length > 0 && (
            <div>
              <p className="text-xs text-gray-400 mb-2">{isRtl ? 'الموضوعات' : 'Topics'}</p>
              <div className="flex flex-wrap gap-1.5" dir={isRtl ? 'rtl' : 'ltr'}>
                {call.relatedTopics.map(t => (
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
              <p className="text-xs text-gray-400 mb-2">{isRtl ? 'الأنبياء المذكورون' : 'Prophets'}</p>
              <div className="flex flex-wrap gap-1.5">
                {call.relatedProphets.map(p => (
                  <span key={p} className="text-xs px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full border border-purple-100">
                    ⭐ {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {call.warnings.length > 0 && (
            <div className="flex items-start gap-2 p-2 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
              <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>{call.warnings[0]}</span>
            </div>
          )}

          <ReviewNote compact />

          <div className="text-center text-xs text-gray-300 font-mono">{call.callId}</div>
        </div>
      </div>
    </div>
  );
}

// ─── Pattern distribution chart ────────────────────────────────────────────────

function PatternChart({ byPattern, isRtl, onSelect }: {
  byPattern: Record<string, number>;
  isRtl: boolean;
  onSelect: (p: string) => void;
}) {
  const sorted = Object.entries(byPattern)
    .filter(([, v]) => v > 0)
    .sort(([, a], [, b]) => b - a);
  const max = sorted[0]?.[1] ?? 1;

  return (
    <div className="space-y-2">
      {sorted.map(([pattern, count]) => {
        const cfg = PATTERN_CFG[pattern] ?? PATTERN_CFG.unknown;
        const pct = (count / max) * 100;
        return (
          <button
            key={pattern}
            onClick={() => onSelect(pattern)}
            className="w-full group"
          >
            <div className="flex items-center justify-between text-sm mb-0.5">
              <span className={`font-medium ${cfg.color} group-hover:opacity-80`}>
                {isRtl ? cfg.ar : cfg.en}
              </span>
              <span className="text-gray-400 text-xs">{count}</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all group-hover:opacity-80 ${cfg.bg.replace('bg-', 'bg-').replace('100', '400')}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}


// ─── 114-Surah intensity grid ─────────────────────────────────────────────────

function SurahIntensityGrid({ bySurah, isRtl, onSelect }: {
  bySurah: Record<number, number>;
  isRtl: boolean;
  onSelect: (n: number) => void;
}) {
  const counts = Object.values(bySurah);
  const maxCount = Math.max(...counts, 1);

  return (
    <div>
      <div className="grid grid-cols-10 sm:grid-cols-14 gap-0.5">
        {Array.from({ length: 114 }, (_, i) => i + 1).map(surahNum => {
          const count = bySurah[surahNum] ?? 0;
          const intensity = count / maxCount;

          return (
            <button
              key={surahNum}
              onClick={() => count > 0 && onSelect(surahNum)}
              title={`Surah ${surahNum}: ${count} calls`}
              className={`relative aspect-square rounded-sm transition-all hover:scale-110 hover:z-10 ${
                count === 0 ? 'bg-gray-100' :
                intensity >= 0.7 ? 'bg-emerald-600' :
                intensity >= 0.4 ? 'bg-emerald-500' :
                intensity >= 0.2 ? 'bg-emerald-400' :
                intensity >= 0.1 ? 'bg-emerald-300' : 'bg-emerald-200'
              }`}
              style={{ opacity: count === 0 ? 0.3 : 1 }}
            >
              {count >= 20 && (
                <span className="absolute inset-0 flex items-center justify-center text-white text-[8px] font-bold">
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
        <span>{isRtl ? 'أقل' : 'Fewer'}</span>
        <div className="flex gap-0.5">
          {['bg-gray-100','bg-emerald-200','bg-emerald-300','bg-emerald-400','bg-emerald-500','bg-emerald-600'].map((c, i) => (
            <div key={i} className={`w-4 h-4 rounded-sm ${c}`} />
          ))}
        </div>
        <span>{isRtl ? 'أكثر' : 'More'}</span>
      </div>
    </div>
  );
}

// ─── Audience card grid ───────────────────────────────────────────────────────

const AUDIENCE_ORDER = [
  'believers','mankind','prophet','people_or_nation','people_of_book',
  'bani_israel','disbelievers','family_member','specific_person','allah','jinn','unknown',
];

function AudienceGrid({ byAddresseeType, isRtl, onSelect }: {
  byAddresseeType: Record<string, number>;
  isRtl: boolean;
  onSelect: (t: string) => void;
}) {
  const total = Object.values(byAddresseeType).reduce((s, v) => s + v, 0);
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
      {AUDIENCE_ORDER.filter(t => (byAddresseeType[t] ?? 0) > 0).map(t => {
        const cfg = ADDRESSEE_CFG[t] ?? ADDRESSEE_CFG.unknown;
        const count = byAddresseeType[t] ?? 0;
        const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
        return (
          <button
            key={t}
            onClick={() => onSelect(t)}
            className={`flex flex-col items-center gap-2 p-3 rounded-2xl border-2 border-transparent ${cfg.color} hover:scale-105 hover:border-current transition-all`}
          >
            <span className="text-3xl">{cfg.icon}</span>
            <div className="text-center">
              <div className="font-semibold text-sm">{isRtl ? cfg.ar : cfg.en}</div>
              <div className="text-xs opacity-70">{count} ({pct}%)</div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ─── Browse panel ─────────────────────────────────────────────────────────────

const PATTERNS_ORDER = [
  'ya_ayyuhal','ya_ayatuha','ya_bani','ya_qawmi','ya_ibadi','ya_ahl',
  'ya_rabbi','ya_abati','ya_bunayya','ya_prophet_name','ya_lament','ya_wish','ya_direct','supplication',
];
const FUNCTIONS_ORDER = [
  'command','prohibition','instruction','warning','comfort','reminder',
  'invitation','rebuke','supplication','promise','mercy','dialogue','lament',
];
const ADDRESSEE_ORDER = [
  'believers','mankind','prophet','people_or_nation','people_of_book',
  'bani_israel','disbelievers','family_member','specific_person','allah','jinn','unknown',
];

interface Filters {
  pattern: string;
  addresseeType: string;
  callFunction: string;
  surah: string;
  directOnly: boolean;
}

function QuickFilterBar({ filters, setFilters, isRtl }: {
  filters: Filters;
  setFilters: (f: Filters) => void;
  isRtl: boolean;
}) {
  const hasFilters = !!(filters.pattern || filters.addresseeType || filters.callFunction || filters.surah || filters.directOnly);

  const quickPatterns = [
    { p: 'ya_ayyuhal', label: isRtl ? 'يا أيها' : 'يا أيها' },
    { p: 'ya_qawmi',   label: isRtl ? 'يا قوم'  : 'يا قوم' },
    { p: 'ya_prophet_name', label: isRtl ? 'يا النبي' : 'O Prophet' },
    { p: 'supplication', label: isRtl ? 'ربنا' : 'ربنا' },
    { p: 'ya_bani', label: isRtl ? 'يا بني' : 'يا بني' },
  ];

  return (
    <div className="space-y-3">
      {/* Quick pattern buttons */}
      <div className="flex flex-wrap gap-2">
        {quickPatterns.map(({ p, label }) => {
          const cfg = PATTERN_CFG[p] ?? PATTERN_CFG.unknown;
          const active = filters.pattern === p;
          return (
            <button
              key={p}
              onClick={() => setFilters({ ...filters, pattern: active ? '' : p })}
              className={`px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
                active
                  ? `${cfg.color} ${cfg.bg} ${cfg.border} ring-2 ring-offset-1 ring-current`
                  : `text-gray-600 bg-gray-50 border-gray-200 hover:${cfg.bg} hover:${cfg.color} hover:${cfg.border}`
              }`}
            >
              {label}
            </button>
          );
        })}
        {hasFilters && (
          <button
            onClick={() => setFilters({ pattern: '', addresseeType: '', callFunction: '', surah: '', directOnly: false })}
            className="px-3 py-1.5 rounded-full border text-xs font-medium text-gray-400 bg-gray-50 border-gray-200 hover:text-red-600 hover:border-red-200 flex items-center gap-1"
          >
            <X className="w-3 h-3" /> {isRtl ? 'مسح' : 'Clear'}
          </button>
        )}
      </div>

      {/* Advanced filter row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <select
          value={filters.pattern}
          onChange={e => setFilters({ ...filters, pattern: e.target.value })}
          className="text-xs border border-gray-200 rounded-xl px-2 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          <option value="">{isRtl ? 'كل الأنماط' : 'All patterns'}</option>
          {PATTERNS_ORDER.map(p => {
            const cfg = PATTERN_CFG[p] ?? PATTERN_CFG.unknown;
            return <option key={p} value={p}>{isRtl ? cfg.ar : cfg.en}</option>;
          })}
        </select>

        <select
          value={filters.addresseeType}
          onChange={e => setFilters({ ...filters, addresseeType: e.target.value })}
          className="text-xs border border-gray-200 rounded-xl px-2 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          <option value="">{isRtl ? 'كل المنادَين' : 'All addressees'}</option>
          {ADDRESSEE_ORDER.map(t => {
            const cfg = ADDRESSEE_CFG[t] ?? ADDRESSEE_CFG.unknown;
            return <option key={t} value={t}>{cfg.icon} {isRtl ? cfg.ar : cfg.en}</option>;
          })}
        </select>

        <select
          value={filters.callFunction}
          onChange={e => setFilters({ ...filters, callFunction: e.target.value })}
          className="text-xs border border-gray-200 rounded-xl px-2 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          <option value="">{isRtl ? 'كل الوظائف' : 'All functions'}</option>
          {FUNCTIONS_ORDER.map(f => {
            const cfg = FUNCTION_CFG[f] ?? FUNCTION_CFG.needs_review;
            return <option key={f} value={f}>{cfg.icon} {isRtl ? cfg.ar : cfg.en}</option>;
          })}
        </select>

        <input
          type="number"
          value={filters.surah}
          onChange={e => setFilters({ ...filters, surah: e.target.value })}
          placeholder={isRtl ? 'رقم السورة' : 'Surah no.'}
          min={1} max={114}
          className="text-xs border border-gray-200 rounded-xl px-2 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
        />
      </div>

      <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer w-fit">
        <input
          type="checkbox"
          checked={filters.directOnly}
          onChange={e => setFilters({ ...filters, directOnly: e.target.checked })}
          className="rounded"
        />
        {isRtl ? 'النداءات المباشرة (يا) فقط' : 'Direct يا calls only'}
      </label>
    </div>
  );
}

// ─── Stat pills ───────────────────────────────────────────────────────────────

function StatPill({ value, label, icon, color }: { value: number | string; label: string; icon: React.ReactNode; color: string }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-2xl ${color}`}>
      <div className="opacity-80">{icon}</div>
      <div>
        <div className="text-xl font-bold leading-tight">{value}</div>
        <div className="text-xs opacity-70">{label}</div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type Tab = 'browse' | 'audience' | 'surahs' | 'patterns' | 'overview';

export default function QuranicCallsAtlasPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [tab, setTab] = useState<Tab>('overview');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>({ pattern: '', addresseeType: '', callFunction: '', surah: '', directOnly: false });
  const [selectedCall, setSelectedCall] = useState<QuranicCallItem | null>(null);
  const [displayMode, setDisplayMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);

  const PAGE_SIZE = 18;

  const statsQuery = useQuery<Statistics>({
    queryKey: ['qcalls-stats'],
    queryFn: fetchStats,
    staleTime: 10 * 60 * 1000,
  });

  const callsQuery = useQuery<PagedResponse>({
    queryKey: ['qcalls', page, filters, search],
    queryFn: () => fetchCalls(
      page, PAGE_SIZE,
      filters.pattern || undefined,
      filters.addresseeType || undefined,
      filters.surah ? Number(filters.surah) : undefined,
      filters.callFunction || undefined,
      search || undefined,
      filters.directOnly || undefined,
    ),
    staleTime: 2 * 60 * 1000,
    enabled: tab === 'browse',
  });

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
    setPage(1);
  }, [searchInput]);

  const handleFilterChange = useCallback((f: Filters) => {
    setFilters(f);
    setPage(1);
    setTab('browse');
  }, []);

  const handleAudienceSelect = useCallback((t: string) => {
    setFilters(f => ({ ...f, addresseeType: t }));
    setPage(1);
    setTab('browse');
  }, []);

  const handleSurahSelect = useCallback((n: number) => {
    setFilters(f => ({ ...f, surah: String(n) }));
    setPage(1);
    setTab('browse');
  }, []);

  const handlePatternSelect = useCallback((p: string) => {
    setFilters(f => ({ ...f, pattern: p }));
    setPage(1);
    setTab('browse');
  }, []);

  const handleFunctionSelect = useCallback((fn: string) => {
    setFilters(f => ({ ...f, callFunction: fn }));
    setPage(1);
    setTab('browse');
  }, []);

  const stats = statsQuery.data;

  const hasFilters = !!(filters.pattern || filters.addresseeType || filters.callFunction || filters.surah || filters.directOnly || search);

  const TABS = [
    { key: 'overview', label: isRtl ? 'نظرة عامة' : 'Overview', icon: <BarChart2 className="w-4 h-4" /> },
    { key: 'browse',   label: isRtl ? 'تصفح'      : 'Browse',   icon: <List className="w-4 h-4" /> },
    { key: 'audience', label: isRtl ? 'المنادَون'  : 'Audience', icon: <Users className="w-4 h-4" /> },
    { key: 'surahs',   label: isRtl ? 'السور'      : 'Surahs',   icon: <BookOpen className="w-4 h-4" /> },
    { key: 'patterns', label: isRtl ? 'الأنماط'    : 'Patterns', icon: <Grid className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-gray-50" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* ── HERO ───────────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-br from-emerald-800 via-teal-800 to-green-900 text-white">
        <div className="max-w-6xl mx-auto px-4 py-10 md:py-14">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 bg-white/15 rounded-2xl backdrop-blur">
              <Megaphone className="w-7 h-7" />
            </div>
            <span className="text-sm font-semibold bg-white/15 px-3 py-1 rounded-full backdrop-blur">
              {isRtl ? 'القرآن الكريم' : 'Quranic Atlas — Phase Y'}
            </span>
          </div>

          <h1 className="text-3xl md:text-5xl font-bold mb-2 leading-tight" dir="rtl">
            أطلس النداءات القرآنية
          </h1>
          <p dir={isRtl ? 'rtl' : 'ltr'} className="text-white/75 text-base md:text-lg mb-6 max-w-2xl">
            {isRtl
              ? 'كل نداء وخطاب في القرآن الكريم — يا أيها الذين آمنوا، يا قوم، ربنا، يا موسى — اكتشف من نودي وكيف ولماذا'
              : 'Every call and address in the Holy Quran — يا أيها, يا قوم, ربنا, يا موسى — discover who was called, how, and why'}
          </p>

          {/* Stat pills row */}
          {stats ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatPill value={stats.totalCalls} label={isRtl ? 'نداء في القرآن' : 'Total Calls'} icon={<Megaphone className="w-5 h-5" />} color="bg-white/15 backdrop-blur" />
              <StatPill value={stats.directYaCalls} label={isRtl ? 'نداء يا مباشر' : 'Direct يا Calls'} icon={<Zap className="w-5 h-5" />} color="bg-white/15 backdrop-blur" />
              <StatPill value={stats.supplicationCalls} label={isRtl ? 'دعاء ومناجاة' : 'Supplications'} icon={<Heart className="w-5 h-5" />} color="bg-white/15 backdrop-blur" />
              <StatPill value={stats.totalAyahsWithCalls} label={isRtl ? 'آية تحتوي نداءً' : 'Ayahs with Calls'} icon={<Book className="w-5 h-5" />} color="bg-white/15 backdrop-blur" />
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-16 bg-white/10 animate-pulse rounded-2xl" />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── TABS ───────────────────────────────────────────────────────────── */}
      <div className="sticky top-16 z-30 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex gap-0 overflow-x-auto">
            {TABS.map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key as Tab)}
                className={`flex items-center gap-2 px-4 py-3.5 text-sm font-medium whitespace-nowrap border-b-2 transition-all ${
                  tab === t.key
                    ? 'border-emerald-600 text-emerald-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── CONTENT ────────────────────────────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">

        {/* Disclaimer */}
        <ReviewNote />

        {/* ── OVERVIEW ─────────────────────────────────────────────────── */}
        {tab === 'overview' && stats && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: pattern chart */}
            <div className="lg:col-span-1 space-y-5">
              <div className="bg-white rounded-2xl border border-gray-200 p-5">
                <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Grid className="w-4 h-4 text-emerald-600" />
                  {isRtl ? 'توزيع الأنماط' : 'Pattern Distribution'}
                </h3>
                <PatternChart byPattern={stats.byPattern} isRtl={isRtl} onSelect={p => { handlePatternSelect(p); }} />
              </div>
            </div>

            {/* Middle: function distribution */}
            <div className="lg:col-span-1 space-y-5">
              <div className="bg-white rounded-2xl border border-gray-200 p-5">
                <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-emerald-600" />
                  {isRtl ? 'وظائف النداء' : 'Call Functions'}
                </h3>
                <FunctionDonutFetcher isRtl={isRtl} onSelect={handleFunctionSelect} />
              </div>
            </div>

            {/* Right: top surahs */}
            <div className="lg:col-span-1 space-y-5">
              <div className="bg-white rounded-2xl border border-gray-200 p-5">
                <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Star className="w-4 h-4 text-emerald-600" />
                  {isRtl ? 'أكثر السور نداءً' : 'Most Calls by Surah'}
                </h3>
                <TopSurahList topSurahs={stats.topSurahs} onSelect={handleSurahSelect} />
              </div>
            </div>

            {/* Full-width: surah grid */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-2xl border border-gray-200 p-5">
                <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Globe2 className="w-4 h-4 text-emerald-600" />
                  {isRtl ? 'خريطة النداءات في كل سور القرآن (114 سورة)' : 'Call Intensity Map — All 114 Surahs'}
                </h3>
                <SurahIntensityGrid bySurah={stats.bySurah ?? {}} isRtl={isRtl} onSelect={handleSurahSelect} />
              </div>
            </div>
          </div>
        )}

        {/* ── AUDIENCE ─────────────────────────────────────────────────── */}
        {tab === 'audience' && stats && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900">
              {isRtl ? 'من يُخاطَب في القرآن؟' : 'Who Is Addressed in the Quran?'}
            </h2>
            <p className="text-sm text-gray-500">
              {isRtl
                ? 'اضغط على أي فئة لعرض جميع النداءات المتعلقة بها'
                : 'Click any audience group to browse all calls addressed to them'}
            </p>
            <AudienceGrid byAddresseeType={stats.byAddresseeType} isRtl={isRtl} onSelect={handleAudienceSelect} />

            {/* Caller breakdown */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5 mt-4">
              <h3 className="font-bold text-gray-800 mb-4">
                {isRtl ? 'من يُنادي في القرآن؟' : 'Who Calls in the Quran?'}
              </h3>
              <div className="flex flex-wrap gap-3">
                {Object.entries(stats.byCallerType ?? {})
                  .sort(([, a], [, b]) => b - a)
                  .map(([ct, count]) => {
                    const cfg = CALLER_CFG[ct] ?? CALLER_CFG.unknown;
                    return (
                      <button
                        key={ct}
                        onClick={() => { setFilters(f => ({ ...f })); setTab('browse'); }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-2xl ${cfg.color} hover:scale-105 transition-all`}
                      >
                        <span className="text-xl">{cfg.icon}</span>
                        <div className="text-left">
                          <div className="font-semibold text-sm">{isRtl ? cfg.ar : cfg.en}</div>
                          <div className="text-xs opacity-70">{count} {isRtl ? 'نداء' : 'calls'}</div>
                        </div>
                      </button>
                    );
                  })}
              </div>
            </div>
          </div>
        )}

        {/* ── SURAHS ───────────────────────────────────────────────────── */}
        {tab === 'surahs' && stats && (
          <div className="space-y-5">
            <div className="bg-white rounded-2xl border border-gray-200 p-5">
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                {isRtl ? 'خريطة النداءات القرآنية — 114 سورة' : 'Quranic Calls Map — 114 Surahs'}
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                {isRtl ? 'اضغط على أي خلية لتصفح نداءاتها' : 'Click any cell to browse its calls'}
              </p>
              <SurahIntensityGrid bySurah={stats.bySurah ?? {}} isRtl={isRtl} onSelect={handleSurahSelect} />
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 p-5">
              <h3 className="font-bold text-gray-800 mb-4">{isRtl ? 'أكثر 15 سورة نداءً' : 'Top 15 Surahs by Call Count'}</h3>
              <TopSurahList topSurahs={stats.topSurahs} onSelect={handleSurahSelect} showAll />
            </div>
          </div>
        )}

        {/* ── PATTERNS ─────────────────────────────────────────────────── */}
        {tab === 'patterns' && stats && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900">
              {isRtl ? 'أنماط النداء في القرآن' : 'Quranic Call Patterns'}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {PATTERNS_ORDER.filter(p => (stats.byPattern[p] ?? 0) > 0).map(p => {
                const cfg = PATTERN_CFG[p] ?? PATTERN_CFG.unknown;
                const count = stats.byPattern[p] ?? 0;
                return (
                  <button
                    key={p}
                    onClick={() => handlePatternSelect(p)}
                    className={`flex items-center gap-4 p-4 rounded-2xl border-2 ${cfg.bg} ${cfg.border} hover:scale-105 transition-all text-left`}
                  >
                    <div className={`text-3xl font-arabic font-bold ${cfg.color}`}>
                      {cfg.ar}
                    </div>
                    <div>
                      <div className={`font-semibold ${cfg.color}`}>{cfg.en}</div>
                      <div className="text-xs text-gray-500">{count} {isRtl ? 'نداء' : 'calls'}</div>
                      <div className="h-1 bg-white/60 rounded-full mt-1.5 overflow-hidden w-24">
                        <div
                          className={`h-full rounded-full ${cfg.bg.replace('100','400')}`}
                          style={{ width: `${(count / (stats.totalCalls || 1)) * 100 * 3}%`, maxWidth: '100%' }}
                        />
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* ── BROWSE ───────────────────────────────────────────────────── */}
        {tab === 'browse' && (
          <div className="space-y-4">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchInput}
                  onChange={e => setSearchInput(e.target.value)}
                  placeholder={isRtl ? 'ابحث في النداءات — Arabic or English…' : 'Search calls — Arabic or English…'}
                  className="w-full ps-9 pe-4 py-2.5 border border-gray-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
                />
              </div>
              <button type="submit" className="px-4 py-2.5 bg-emerald-700 text-white rounded-2xl text-sm hover:bg-emerald-800 transition-colors flex-shrink-0">
                {isRtl ? 'بحث' : 'Search'}
              </button>
              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center gap-1.5 px-3 py-2.5 rounded-2xl border text-sm transition-all flex-shrink-0 ${
                  showFilters || hasFilters
                    ? 'border-emerald-400 text-emerald-700 bg-emerald-50'
                    : 'border-gray-200 text-gray-600 bg-white hover:border-emerald-300'
                }`}
              >
                <Filter className="w-4 h-4" />
                {hasFilters && <span className="w-2 h-2 rounded-full bg-emerald-600" />}
              </button>
              <div className="flex gap-1 bg-white border border-gray-200 rounded-2xl p-1 flex-shrink-0">
                <button onClick={() => setDisplayMode('grid')} className={`p-1.5 rounded-xl ${displayMode === 'grid' ? 'bg-emerald-100 text-emerald-700' : 'text-gray-400'}`}>
                  <Grid className="w-4 h-4" />
                </button>
                <button onClick={() => setDisplayMode('list')} className={`p-1.5 rounded-xl ${displayMode === 'list' ? 'bg-emerald-100 text-emerald-700' : 'text-gray-400'}`}>
                  <List className="w-4 h-4" />
                </button>
              </div>
            </form>

            {/* Filter panel */}
            {showFilters && (
              <div className="bg-white border border-gray-200 rounded-2xl p-4">
                <QuickFilterBar filters={filters} setFilters={handleFilterChange} isRtl={isRtl} />
              </div>
            )}

            {/* Active filter chips */}
            {hasFilters && (
              <div className="flex flex-wrap gap-2 items-center">
                {filters.pattern && (
                  <span className={`text-xs px-2.5 py-1 rounded-full border flex items-center gap-1 ${PATTERN_CFG[filters.pattern]?.color ?? 'text-gray-600'} ${PATTERN_CFG[filters.pattern]?.bg ?? 'bg-gray-50'} ${PATTERN_CFG[filters.pattern]?.border ?? 'border-gray-200'}`}>
                    {isRtl ? (PATTERN_CFG[filters.pattern]?.ar ?? filters.pattern) : (PATTERN_CFG[filters.pattern]?.en ?? filters.pattern)}
                    <button onClick={() => setFilters({ ...filters, pattern: '' })}><X className="w-3 h-3" /></button>
                  </span>
                )}
                {filters.addresseeType && (
                  <span className={`text-xs px-2.5 py-1 rounded-full flex items-center gap-1 ${ADDRESSEE_CFG[filters.addresseeType]?.color ?? 'bg-gray-100 text-gray-600'}`}>
                    {ADDRESSEE_CFG[filters.addresseeType]?.icon} {isRtl ? (ADDRESSEE_CFG[filters.addresseeType]?.ar) : (ADDRESSEE_CFG[filters.addresseeType]?.en)}
                    <button onClick={() => setFilters({ ...filters, addresseeType: '' })}><X className="w-3 h-3" /></button>
                  </span>
                )}
                {filters.callFunction && (
                  <span className={`text-xs px-2.5 py-1 rounded-full border flex items-center gap-1 ${FUNCTION_CFG[filters.callFunction]?.color ?? 'text-gray-600 bg-gray-50 border-gray-200'}`}>
                    {FUNCTION_CFG[filters.callFunction]?.icon} {isRtl ? (FUNCTION_CFG[filters.callFunction]?.ar) : (FUNCTION_CFG[filters.callFunction]?.en)}
                    <button onClick={() => setFilters({ ...filters, callFunction: '' })}><X className="w-3 h-3" /></button>
                  </span>
                )}
                {filters.surah && (
                  <span className="text-xs px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
                    {isRtl ? 'سورة' : 'Surah'} {filters.surah}
                    <button onClick={() => setFilters({ ...filters, surah: '' })}><X className="w-3 h-3" /></button>
                  </span>
                )}
                {search && (
                  <span className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 border border-gray-200 flex items-center gap-1">
                    "{search}"
                    <button onClick={() => { setSearch(''); setSearchInput(''); }}><X className="w-3 h-3" /></button>
                  </span>
                )}
                <button
                  onClick={() => { setFilters({ pattern: '', addresseeType: '', callFunction: '', surah: '', directOnly: false }); setSearch(''); setSearchInput(''); setPage(1); }}
                  className="text-xs text-gray-400 hover:text-red-500 flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> {isRtl ? 'مسح الكل' : 'Clear all'}
                </button>
              </div>
            )}

            {/* Results */}
            {callsQuery.isLoading && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[...Array(6)].map((_, i) => <div key={i} className="h-36 bg-gray-100 animate-pulse rounded-2xl" />)}
              </div>
            )}

            {callsQuery.isError && (
              <div className="text-center py-10 text-red-500 text-sm">
                {isRtl ? 'خطأ في تحميل البيانات' : 'Failed to load data'}
              </div>
            )}

            {callsQuery.data && (
              <>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>
                    {callsQuery.data.total.toLocaleString()} {isRtl ? 'نداء' : 'calls'}
                    {callsQuery.data.totalPages > 1 && ` · ${isRtl ? 'صفحة' : 'page'} ${page}/${callsQuery.data.totalPages}`}
                  </span>
                  <span className="text-xs text-gray-300">{callsQuery.data.latency_ms}ms</span>
                </div>

                <div className={displayMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3' : 'space-y-2'}>
                  {callsQuery.data.items.map(call => (
                    <CallCard
                      key={call.callId}
                      call={call}
                      isRtl={isRtl}
                      onClick={() => setSelectedCall(call)}
                      compact={displayMode === 'list'}
                    />
                  ))}
                </div>

                {callsQuery.data.items.length === 0 && (
                  <div className="text-center py-14 text-gray-400">
                    <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p>{isRtl ? 'لا توجد نتائج' : 'No results found'}</p>
                  </div>
                )}

                {callsQuery.data.totalPages > 1 && (
                  <div className="flex items-center justify-center gap-3 pt-2">
                    <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                      className="px-4 py-2 rounded-xl border border-gray-200 text-sm disabled:opacity-30 hover:border-emerald-400 transition-colors">
                      {isRtl ? '← السابق' : '← Previous'}
                    </button>
                    <span className="text-sm text-gray-500">{page} / {callsQuery.data.totalPages}</span>
                    <button disabled={page >= callsQuery.data.totalPages} onClick={() => setPage(p => p + 1)}
                      className="px-4 py-2 rounded-xl border border-gray-200 text-sm disabled:opacity-30 hover:border-emerald-400 transition-colors">
                      {isRtl ? 'التالي →' : 'Next →'}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* ── DETAIL MODAL ─────────────────────────────────────────────────── */}
      {selectedCall && (
        <CallDetailModal call={selectedCall} isRtl={isRtl} onClose={() => setSelectedCall(null)} />
      )}
    </div>
  );
}

// ─── Helper sub-components ────────────────────────────────────────────────────

function TopSurahList({ topSurahs, onSelect, showAll = false }: {
  topSurahs: Array<{ surahNumber: number; surahNameEn: string; count: number }>;
  onSelect: (n: number) => void;
  showAll?: boolean;
}) {
  const list = showAll ? topSurahs : topSurahs.slice(0, 10);
  const max = list[0]?.count ?? 1;
  return (
    <div className="space-y-2">
      {list.map((s, i) => (
        <button key={s.surahNumber} onClick={() => onSelect(s.surahNumber)} className="w-full flex items-center gap-3 group">
          <span className="text-xs text-gray-300 w-4 text-right flex-shrink-0">{i + 1}</span>
          <div className="flex-1">
            <div className="flex items-center justify-between text-sm mb-0.5">
              <span className="font-medium text-gray-700 group-hover:text-emerald-700 transition-colors">
                {s.surahNameEn} <span className="text-gray-400 text-xs">({s.surahNumber})</span>
              </span>
              <span className="text-gray-400 text-xs">{s.count}</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full group-hover:from-emerald-600 transition-all"
                style={{ width: `${(s.count / max) * 100}%` }}
              />
            </div>
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-gray-200 group-hover:text-emerald-500 transition-colors flex-shrink-0" />
        </button>
      ))}
    </div>
  );
}

function FunctionDonutFetcher({ isRtl, onSelect }: { isRtl: boolean; onSelect: (f: string) => void }) {
  const q = useQuery({
    queryKey: ['qcalls-fn-summary'],
    queryFn: async () => {
      // Fetch per-function counts via by-function endpoint (page_size=1 for total only)
      const functions = ['command','prohibition','instruction','warning','comfort',
                         'reminder','invitation','rebuke','supplication','promise','mercy','dialogue','lament'];
      const counts: Record<string, number> = {};
      await Promise.all(functions.map(async fn => {
        const r = await axios.get(`/api/v1/quranic-calls/by-function/${fn}?page_size=1`);
        counts[fn] = r.data.total;
      }));
      return counts;
    },
    staleTime: 10 * 60 * 1000,
  });

  if (!q.data) return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => <div key={i} className="h-6 bg-gray-100 animate-pulse rounded" />)}
    </div>
  );

  const byFn = q.data;
  const sorted = Object.entries(byFn).filter(([, v]) => v > 0).sort(([, a], [, b]) => b - a).slice(0, 8);
  const total = sorted.reduce((s, [, v]) => s + v, 0);

  return (
    <div className="space-y-2">
      {sorted.map(([fn, count]) => {
        const cfg = FUNCTION_CFG[fn] ?? FUNCTION_CFG.needs_review;
        const pct = total > 0 ? (count / total) * 100 : 0;
        return (
          <button key={fn} onClick={() => onSelect(fn)} className="w-full flex items-center gap-3 group">
            <span className="text-base w-6 flex-shrink-0">{cfg.icon}</span>
            <div className="flex-1">
              <div className="flex justify-between text-xs mb-0.5">
                <span className="font-medium text-gray-700 group-hover:text-emerald-700">{isRtl ? cfg.ar : cfg.en}</span>
                <span className="text-gray-400">{count}</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-400 group-hover:bg-emerald-500 rounded-full transition-all"
                  style={{ width: `${Math.min(pct * 3.5, 100)}%` }}
                />
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
