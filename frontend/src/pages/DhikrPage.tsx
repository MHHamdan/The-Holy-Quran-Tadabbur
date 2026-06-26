/**
 * Dhikr Page — immersive remembrance tracker with focus mode, timer,
 * auto-play, TTS audio, and streak rewards.
 *
 * Counts persist per day in localStorage.
 * Session stats are optionally sent to /api/v1/dhikr/sessions (anonymous).
 * No auth required. Fully functional offline.
 */

import {
  useState, useCallback, useEffect, useRef, useMemo,
} from 'react';
import {
  RotateCcw, ChevronDown, ChevronUp, Info, Play, Pause,
  Volume2, VolumeX, Timer, X, ChevronLeft, ChevronRight, Trophy, Flame,
  Star, Check, Sun, Moon, Search, Infinity as InfinityIcon, BedDouble,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  ADHKAR, CATEGORY_META, MORNING_IDS, EVENING_IDS, SLEEP_IDS,
  type DhikrCategory, type DhikrEntry,
} from '../data/adhkar';

// ── Constants ─────────────────────────────────────────────────────────────────

const STORAGE_KEY    = 'tadabbur_dhikr_v1';
const REWARDS_KEY    = 'tadabbur_dhikr_rewards_v1';
const TODAY          = new Date().toISOString().slice(0, 10);
const API_BASE       = '/api/v1/dhikr';

type CountRecord = Record<string, { count: number; date: string }>;

interface RewardsData {
  streak: number;
  lastActiveDate: string;
  totalXP: number;
  todayXP: number;
  todayDate: string;
  achievements: string[];
  totalSessions: number;
}

interface Achievement {
  id: string;
  emoji: string;
  labelEn: string;
  labelAr: string;
  xp: number;
}

const ACHIEVEMENTS: Record<string, Achievement> = {
  first_dhikr:      { id: 'first_dhikr',      emoji: '⭐', labelEn: 'First Dhikr',        labelAr: 'أول ذكر',              xp: 10  },
  morning_complete: { id: 'morning_complete',  emoji: '🌅', labelEn: 'Morning Complete',   labelAr: 'أذكار الصباح مكتملة', xp: 50  },
  evening_complete: { id: 'evening_complete',  emoji: '🌙', labelEn: 'Evening Complete',   labelAr: 'أذكار المساء مكتملة', xp: 50  },
  sleep_complete:   { id: 'sleep_complete',    emoji: '😴', labelEn: 'Sleep Adhkar Done',  labelAr: 'أذكار النوم مكتملة',  xp: 40  },
  centurion:        { id: 'centurion',         emoji: '💯', labelEn: 'Centurion',          labelAr: 'المئة',               xp: 25  },
  streak_7:         { id: 'streak_7',          emoji: '🔥', labelEn: '7-Day Streak',       labelAr: '٧ أيام متواصلة',      xp: 100 },
  streak_30:        { id: 'streak_30',         emoji: '💎', labelEn: '30-Day Streak',      labelAr: '٣٠ يوم متواصل',       xp: 500 },
  full_set:         { id: 'full_set',          emoji: '🏆', labelEn: 'Full Day Complete',  labelAr: 'يوم كامل من الذكر',   xp: 200 },
};

const TIMER_OPTIONS  = [5, 10, 15, 30] as const;
// Seconds between each auto-count
const PACE_OPTIONS   = [1, 2, 3, 5, 7, 10, 15, 20] as const;
const PACE_DEFAULT   = 5;

const CATS_ORDER: DhikrCategory[] = ['after_salah', 'quranic', 'any_time', 'morning', 'evening', 'sleep', 'travel'];

// ── Focus-mode gradient themes ────────────────────────────────────────────────

const FOCUS_THEME: Record<DhikrCategory, {
  bg: string; text: string; subText: string; ring: string; ringFg: string;
  badge: string; btn: string; btnText: string; dark: boolean;
}> = {
  morning:     { bg: 'bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-100', text: 'text-amber-900', subText: 'text-amber-700/70', ring: 'text-amber-200', ringFg: 'text-amber-500', badge: 'bg-amber-100/80 text-amber-800', btn: 'bg-amber-500 hover:bg-amber-600', btnText: 'text-white', dark: false },
  evening:     { bg: 'bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950', text: 'text-white', subText: 'text-indigo-300/80', ring: 'text-white/15', ringFg: 'text-indigo-400', badge: 'bg-indigo-900/80 text-indigo-200', btn: 'bg-indigo-500 hover:bg-indigo-400', btnText: 'text-white', dark: true },
  after_salah: { bg: 'bg-gradient-to-br from-emerald-50 via-green-50 to-teal-100', text: 'text-emerald-900', subText: 'text-emerald-700/70', ring: 'text-emerald-200', ringFg: 'text-emerald-500', badge: 'bg-emerald-100/80 text-emerald-800', btn: 'bg-emerald-500 hover:bg-emerald-600', btnText: 'text-white', dark: false },
  any_time:    { bg: 'bg-gradient-to-br from-violet-50 via-purple-50 to-indigo-100', text: 'text-violet-900', subText: 'text-violet-700/70', ring: 'text-violet-200', ringFg: 'text-violet-500', badge: 'bg-violet-100/80 text-violet-800', btn: 'bg-violet-500 hover:bg-violet-600', btnText: 'text-white', dark: false },
  quranic:     { bg: 'bg-gradient-to-br from-teal-50 via-cyan-50 to-sky-100', text: 'text-teal-900', subText: 'text-teal-700/70', ring: 'text-teal-200', ringFg: 'text-teal-500', badge: 'bg-teal-100/80 text-teal-800', btn: 'bg-teal-500 hover:bg-teal-600', btnText: 'text-white', dark: false },
  sleep:       { bg: 'bg-gradient-to-br from-slate-900 via-purple-950 to-indigo-950', text: 'text-white', subText: 'text-purple-300/80', ring: 'text-white/15', ringFg: 'text-purple-400', badge: 'bg-purple-900/80 text-purple-200', btn: 'bg-purple-500 hover:bg-purple-400', btnText: 'text-white', dark: true },
  travel:      { bg: 'bg-gradient-to-br from-sky-50 via-cyan-50 to-blue-100', text: 'text-sky-900', subText: 'text-sky-700/70', ring: 'text-sky-200', ringFg: 'text-sky-500', badge: 'bg-sky-100/80 text-sky-800', btn: 'bg-sky-500 hover:bg-sky-600', btnText: 'text-white', dark: false },
};

const BROWSE_COLORS: Record<string, { bg: string; ring: string; button: string; progress: string; badge: string }> = {
  amber:   { bg: 'bg-amber-50',   ring: 'ring-amber-300',   button: 'bg-amber-500 hover:bg-amber-600 active:bg-amber-700',     progress: 'bg-amber-400',   badge: 'bg-amber-100 text-amber-700'  },
  indigo:  { bg: 'bg-indigo-50',  ring: 'ring-indigo-300',  button: 'bg-indigo-500 hover:bg-indigo-600 active:bg-indigo-700',   progress: 'bg-indigo-400',  badge: 'bg-indigo-100 text-indigo-700' },
  emerald: { bg: 'bg-emerald-50', ring: 'ring-emerald-300', button: 'bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700', progress: 'bg-emerald-400', badge: 'bg-emerald-100 text-emerald-700' },
  violet:  { bg: 'bg-violet-50',  ring: 'ring-violet-300',  button: 'bg-violet-500 hover:bg-violet-600 active:bg-violet-700',   progress: 'bg-violet-400',  badge: 'bg-violet-100 text-violet-700' },
  teal:    { bg: 'bg-teal-50',    ring: 'ring-teal-300',    button: 'bg-teal-500 hover:bg-teal-600 active:bg-teal-700',         progress: 'bg-teal-400',    badge: 'bg-teal-100 text-teal-700'    },
  purple:  { bg: 'bg-purple-50',  ring: 'ring-purple-300',  button: 'bg-purple-500 hover:bg-purple-600 active:bg-purple-700',   progress: 'bg-purple-400',  badge: 'bg-purple-100 text-purple-700' },
  sky:     { bg: 'bg-sky-50',     ring: 'ring-sky-300',     button: 'bg-sky-500 hover:bg-sky-600 active:bg-sky-700',            progress: 'bg-sky-400',     badge: 'bg-sky-100 text-sky-700'      },
};

// ── localStorage helpers ──────────────────────────────────────────────────────

function loadCounts(): CountRecord {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}'); }
  catch { return {}; }
}

function saveCounts(r: CountRecord) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(r)); } catch { /**/ }
}

function getCount(r: CountRecord, id: string): number {
  const e = r[id];
  return e?.date === TODAY ? e.count : 0;
}

function loadRewards(): RewardsData {
  try {
    const raw = localStorage.getItem(REWARDS_KEY);
    if (raw) {
      const r = JSON.parse(raw) as RewardsData;
      // Reset today XP if it's a new day
      if (r.todayDate !== TODAY) return { ...r, todayXP: 0, todayDate: TODAY };
      return r;
    }
  } catch { /**/ }
  return { streak: 0, lastActiveDate: '', totalXP: 0, todayXP: 0, todayDate: TODAY, achievements: [], totalSessions: 0 };
}

function saveRewards(r: RewardsData) {
  try { localStorage.setItem(REWARDS_KEY, JSON.stringify(r)); } catch { /**/ }
}

function vibrate() {
  try { navigator.vibrate?.(12); } catch { /**/ }
}

// ── TTS via Web Speech API ────────────────────────────────────────────────────

let ttsSupported: boolean | null = null;

function speakArabic(text: string) {
  if (ttsSupported === null) ttsSupported = 'speechSynthesis' in window;
  if (!ttsSupported) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'ar-SA';
  u.rate = 0.82;
  u.pitch = 1.0;
  window.speechSynthesis.speak(u);
}

// ── Circular progress ring ────────────────────────────────────────────────────

const RING = 120;
const STROKE = 10;
const R = (RING - STROKE) / 2;
const C = 2 * Math.PI * R;

function ProgressRing({ pct, count, done, themeClass }: {
  pct: number; count: number; done: boolean; themeClass: { ring: string; ringFg: string; text: string };
}) {
  const offset = C * (1 - Math.min(pct, 1));
  return (
    <div className="relative flex items-center justify-center" style={{ width: RING, height: RING }}>
      <svg width={RING} height={RING} className="-rotate-90 absolute inset-0">
        <circle cx={RING / 2} cy={RING / 2} r={R} fill="none" strokeWidth={STROKE}
          className={clsx('transition-colors', themeClass.ring)}
          stroke="currentColor" />
        <circle cx={RING / 2} cy={RING / 2} r={R} fill="none" strokeWidth={STROKE}
          strokeDasharray={C} strokeDashoffset={offset} strokeLinecap="round"
          className={clsx('transition-all duration-300', done ? 'text-emerald-400' : themeClass.ringFg)}
          stroke="currentColor" />
      </svg>
      <span className={clsx(
        'relative text-4xl font-bold tabular-nums transition-transform',
        done ? 'text-emerald-400' : themeClass.text,
        done && 'scale-110',
      )}>
        {done ? <Check className="w-10 h-10" /> : count}
      </span>
    </div>
  );
}

// ── Achievement toast ─────────────────────────────────────────────────────────

function AchievementToast({ achievement, isRtl, onDone }: {
  achievement: Achievement; isRtl: boolean; onDone: () => void;
}) {
  useEffect(() => {
    const t = setTimeout(onDone, 3500);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[60] animate-bounce-in">
      <div className="flex items-center gap-3 bg-white/95 backdrop-blur-sm border border-amber-200 shadow-xl rounded-2xl px-5 py-3">
        <span className="text-3xl">{achievement.emoji}</span>
        <div>
          <p className="text-xs text-amber-600 font-medium">
            {isRtl ? 'إنجاز جديد!' : 'Achievement Unlocked!'}
          </p>
          <p className={clsx('text-sm font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? achievement.labelAr : achievement.labelEn}
          </p>
          <p className="text-xs text-amber-500">+{achievement.xp} XP</p>
        </div>
      </div>
    </div>
  );
}

// ── Misbaha (infinite counter) overlay ───────────────────────────────────────

const MISBAHA_MILESTONES = new Set([33, 66, 99, 100, 200, 300, 500, 1000]);

function MisbahaView({ dhikr, isRtl, onClose }: {
  dhikr: DhikrEntry; isRtl: boolean; onClose: () => void;
}) {
  const [count, setCount]   = useState(0);
  const [flash, setFlash]   = useState(false);
  const [milestone, setMilestone] = useState<number | null>(null);

  const tap = useCallback(() => {
    setCount(prev => {
      const next = prev + 1;
      if (MISBAHA_MILESTONES.has(next)) {
        setFlash(true);
        setMilestone(next);
        setTimeout(() => { setFlash(false); setMilestone(null); }, 1000);
      }
      try { navigator.vibrate?.(next % 33 === 0 ? 40 : 12); } catch { /**/ }
      return next;
    });
  }, []);

  const reset = () => { setCount(0); setFlash(false); setMilestone(null); };

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col select-none bg-gradient-to-br from-slate-950 via-purple-950 to-indigo-950"
      onClick={tap}
    >
      {/* Top bar */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-white/10 flex-shrink-0">
        <button
          onClick={e => { e.stopPropagation(); onClose(); }}
          className="p-2 rounded-xl hover:bg-white/10 transition-colors"
        >
          <X className="w-5 h-5 text-white" />
        </button>
        <span className="text-white/60 text-xs font-medium">
          {isRtl ? 'المسبحة الرقمية' : 'Digital Misbaha'}
        </span>
        <button
          onClick={e => { e.stopPropagation(); reset(); }}
          className="p-2 rounded-xl hover:bg-white/10 transition-colors"
        >
          <RotateCcw className="w-4 h-4 text-white/50" />
        </button>
      </div>

      {/* Main counter */}
      <div className="flex-1 flex flex-col items-center justify-center gap-6 px-6">
        <p
          className={clsx(
            'font-arabic text-center leading-relaxed text-white transition-transform duration-150',
            flash && 'scale-105',
          )}
          style={{ fontSize: dhikr.arabicPhrase.length > 60 ? '1.4rem' : '1.8rem' }}
          dir="rtl"
        >
          {dhikr.arabicPhrase}
        </p>
        <p className="text-white/50 text-sm text-center">{dhikr.transliteration}</p>

        {/* Big counter */}
        <div className={clsx(
          'flex items-center justify-center w-48 h-48 rounded-full border-4 transition-all duration-200',
          flash ? 'border-yellow-400 bg-yellow-400/10 scale-105' : 'border-purple-500/40 bg-white/5',
        )}>
          <span className={clsx(
            'text-7xl font-bold tabular-nums transition-colors',
            flash ? 'text-yellow-300' : 'text-white',
          )}>
            {count}
          </span>
        </div>

        {milestone && (
          <div className="animate-bounce text-yellow-300 text-lg font-bold">
            ✨ {milestone}!
          </div>
        )}

        <p className="text-white/30 text-xs">
          {isRtl ? 'اضغط في أي مكان للعدّ' : 'Tap anywhere to count'}
        </p>

        {/* Sub-count helper (show 33/66/99 markers) */}
        <div className="flex items-center gap-3">
          {[33, 66, 99].map(m => (
            <div
              key={m}
              className={clsx(
                'flex flex-col items-center gap-0.5 opacity-40',
                count >= m && 'opacity-100',
              )}
            >
              <div className={clsx(
                'w-2 h-2 rounded-full',
                count >= m ? 'bg-yellow-400' : 'bg-white/20',
              )} />
              <span className="text-[10px] text-white/60">{m}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Source */}
      <div className="px-5 pb-8 pt-2 text-center flex-shrink-0">
        <p className="text-white/30 text-[10px] italic">
          {isRtl ? dhikr.sourceRefAr : dhikr.sourceRef}
        </p>
      </div>
    </div>
  );
}

// ── Browse card ───────────────────────────────────────────────────────────────

function DhikrBrowseCard({ dhikr, count, isRtl, onIncrement, onReset, onMisbaha }: {
  dhikr: DhikrEntry; count: number; isRtl: boolean;
  onIncrement: () => void; onReset: () => void; onMisbaha: () => void;
}) {
  const [showInfo, setShowInfo] = useState(false);
  const meta   = CATEGORY_META[dhikr.category];
  const colors = BROWSE_COLORS[meta.color] ?? BROWSE_COLORS.violet;
  const done   = count >= dhikr.targetCount;
  const pct    = Math.min((count / dhikr.targetCount) * 100, 100);

  return (
    <div className={clsx('rounded-2xl border border-gray-100 overflow-hidden shadow-sm transition-opacity', done && 'opacity-75')}>
      <div
        className={clsx('p-4 cursor-pointer select-none active:brightness-95 transition-all', colors.bg)}
        onClick={() => { if (!done) { onIncrement(); vibrate(); } }}
      >
        <div className={clsx('flex items-center justify-between mb-3', isRtl && 'flex-row-reverse')}>
          <span className={clsx('text-[10px] px-2 py-0.5 rounded-full font-medium', colors.badge)}>
            {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
          </span>
          <div className={clsx('flex items-center gap-1', isRtl && 'flex-row-reverse')}>
            {count > 0 && !done && (
              <button
                onClick={e => { e.stopPropagation(); onReset(); }}
                className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-white/60 transition-colors"
                title={isRtl ? 'إعادة تعيين' : 'Reset'}
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={e => { e.stopPropagation(); onMisbaha(); }}
              className="p-1.5 rounded-lg text-gray-400 hover:text-purple-500 hover:bg-white/60 transition-colors"
              title={isRtl ? 'مسبحة' : 'Misbaha counter'}
            >
              <InfinityIcon className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={e => { e.stopPropagation(); setShowInfo(v => !v); }}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-white/60 transition-colors"
            >
              <Info className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <p className="font-arabic text-2xl text-gray-900 leading-loose text-center mb-1" dir="rtl">
          {dhikr.arabicPhrase}
        </p>
        <p className="text-xs text-gray-500 text-center mb-3">{dhikr.transliteration}</p>

        <div className="w-full h-1.5 bg-white/60 rounded-full overflow-hidden mb-2">
          <div className={clsx('h-full rounded-full transition-all duration-300', colors.progress)} style={{ width: `${pct}%` }} />
        </div>

        <div className={clsx('flex items-center justify-between', isRtl && 'flex-row-reverse')}>
          <span className={clsx('text-3xl font-bold tabular-nums', done ? 'text-emerald-600' : 'text-gray-800')}>
            {count}
          </span>
          <span className="text-xs text-gray-400">
            {done ? (isRtl ? '✅ مكتمل' : '✅ Done') : `/${dhikr.targetCount}`}
          </span>
        </div>
      </div>

      {!done && (
        <button
          onClick={() => { onIncrement(); vibrate(); }}
          className={clsx('w-full flex items-center justify-center py-2.5 transition-opacity active:opacity-70', colors.button)}
        >
          <span className="text-white text-sm font-medium">
            {isRtl ? 'اضغط للتسبيح' : 'Tap to count'}
          </span>
        </button>
      )}

      {showInfo && (
        <div className="bg-white px-4 py-3 border-t border-gray-100">
          <p className={clsx('text-xs text-gray-700 mb-1.5', isRtl && 'font-arabic text-right')} dir={isRtl ? 'rtl' : 'ltr'}>
            {isRtl ? dhikr.meaningAr : dhikr.meaningEn}
          </p>
          <p className={clsx('text-xs text-gray-500 mb-1', isRtl && 'font-arabic text-right')} dir={isRtl ? 'rtl' : 'ltr'}>
            {isRtl ? dhikr.benefitAr : dhikr.benefitEn}
          </p>
          <p className="text-[10px] text-gray-400 italic">
            {isRtl ? dhikr.sourceRefAr : dhikr.sourceRef}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Focus mode view ───────────────────────────────────────────────────────────

function FocusView({
  items, index, counts, isRtl, audioEnabled, autoPlay, autoPlayInterval,
  timerSec, timerRunning,
  onIncrement, onPrev, onNext, onClose, onToggleAudio, onToggleAutoPlay,
  onChangeInterval, onStartTimer, onStopTimer,
}: {
  items: DhikrEntry[];
  index: number;
  counts: CountRecord;
  isRtl: boolean;
  audioEnabled: boolean;
  autoPlay: boolean;
  autoPlayInterval: number;
  timerSec: number;
  timerRunning: boolean;
  onIncrement: () => void;
  onPrev: () => void;
  onNext: () => void;
  onClose: () => void;
  onToggleAudio: () => void;
  onToggleAutoPlay: () => void;
  onChangeInterval: (s: number) => void;
  onStartTimer: (mins: number) => void;
  onStopTimer: () => void;
}) {
  const [showTimerMenu, setShowTimerMenu] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [beatPct, setBeatPct] = useState(0);   // 0..1 sweep for the auto-count bar
  const timerMenuRef = useRef<HTMLDivElement>(null);

  const dhikr = items[index];
  if (!dhikr) return null;

  const theme = FOCUS_THEME[dhikr.category];
  const count = getCount(counts, dhikr.id);
  const done  = count >= dhikr.targetCount;
  const pct   = count / dhikr.targetCount;

  const timerMins = Math.floor(timerSec / 60);
  const timerSecs = timerSec % 60;

  function formatTimer() {
    return `${timerMins}:${String(timerSecs).padStart(2, '0')}`;
  }

  // Flash when complete
  useEffect(() => {
    if (done) {
      setCompleting(true);
      const t = setTimeout(() => setCompleting(false), 800);
      return () => clearTimeout(t);
    }
  }, [done]);

  // ── Auto-count ticker ───────────────────────────────────────────────────────
  // When auto-play is ON and the current dhikr is not yet complete, fire
  // onIncrement every autoPlayInterval seconds.  A 100 ms sub-interval drives
  // the beat progress bar so the user can see the countdown visually.
  useEffect(() => {
    if (!autoPlay || done) {
      setBeatPct(0);
      return;
    }

    const stepMs      = 100;                            // visual refresh rate
    const totalSteps  = (autoPlayInterval * 1000) / stepMs;
    let step          = 0;

    const id = setInterval(() => {
      step += 1;
      setBeatPct(Math.min(step / totalSteps, 1));

      if (step >= totalSteps) {
        step = 0;
        setBeatPct(0);
        onIncrement();
        vibrate();
      }
    }, stepMs);

    return () => {
      clearInterval(id);
      setBeatPct(0);
    };
    // onIncrement identity changes when focusIndex changes — intentional so
    // the ticker restarts cleanly when advancing to a new dhikr.
  }, [autoPlay, done, autoPlayInterval, onIncrement]);

  return (
    <div className={clsx(
      'fixed inset-0 z-50 flex flex-col select-none overflow-hidden',
      theme.bg,
    )}>
      {/* Top bar */}
      <div className={clsx(
        'flex items-center justify-between px-5 pt-safe pt-5 pb-3 flex-shrink-0',
        theme.dark ? 'border-b border-white/10' : 'border-b border-black/5',
      )}>
        <button onClick={onClose} className={clsx('p-2 rounded-xl transition-colors', theme.dark ? 'hover:bg-white/10' : 'hover:bg-black/5')}>
          <X className={clsx('w-5 h-5', theme.text)} />
        </button>

        {/* Session progress */}
        <div className="flex flex-col items-center gap-0.5">
          <span className={clsx('text-sm font-semibold', theme.text)}>
            {index + 1} / {items.length}
          </span>
          <div className={clsx('h-1 rounded-full w-24 overflow-hidden', theme.dark ? 'bg-white/10' : 'bg-black/10')}>
            <div
              className={clsx('h-full rounded-full transition-all', theme.dark ? 'bg-indigo-400' : 'bg-current')}
              style={{ width: `${((index + 1) / items.length) * 100}%`, color: 'inherit' }}
            />
          </div>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-1">
          {/* Timer */}
          <div className="relative" ref={timerMenuRef}>
            <button
              onClick={() => timerRunning ? onStopTimer() : setShowTimerMenu(v => !v)}
              className={clsx('px-2.5 py-1.5 rounded-xl text-xs font-mono font-medium flex items-center gap-1 transition-colors',
                timerRunning
                  ? (theme.dark ? 'bg-white/20 text-white' : 'bg-black/10 text-gray-800')
                  : (theme.dark ? 'hover:bg-white/10 text-white/60' : 'hover:bg-black/5 text-gray-500'),
              )}
            >
              <Timer className="w-3.5 h-3.5" />
              {timerRunning ? formatTimer() : null}
            </button>
            {showTimerMenu && !timerRunning && (
              <div className={clsx(
                'absolute top-full right-0 mt-1 rounded-xl shadow-lg overflow-hidden border z-10 min-w-[120px]',
                theme.dark ? 'bg-slate-800 border-white/10' : 'bg-white border-gray-100',
              )}>
                {TIMER_OPTIONS.map(m => (
                  <button
                    key={m}
                    onClick={() => { onStartTimer(m); setShowTimerMenu(false); }}
                    className={clsx(
                      'w-full text-left px-4 py-2 text-sm transition-colors',
                      theme.dark ? 'text-white hover:bg-white/10' : 'text-gray-700 hover:bg-gray-50',
                    )}
                  >
                    {m} {isRtl ? 'دقيقة' : 'min'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Audio */}
          <button
            onClick={onToggleAudio}
            className={clsx('p-2 rounded-xl transition-colors', theme.dark ? 'hover:bg-white/10' : 'hover:bg-black/5')}
          >
            {audioEnabled
              ? <Volume2 className={clsx('w-4.5 h-4.5', theme.text)} />
              : <VolumeX className={clsx('w-4.5 h-4.5', theme.dark ? 'text-white/40' : 'text-gray-400')} />}
          </button>
        </div>
      </div>

      {/* Timer finished banner */}
      {timerRunning && timerSec === 0 && (
        <div className={clsx(
          'mx-4 mt-2 px-4 py-2 rounded-xl text-center text-sm font-medium',
          theme.dark ? 'bg-emerald-900/60 text-emerald-300' : 'bg-emerald-100 text-emerald-700',
        )}>
          {isRtl ? '⏰ انتهت الجلسة — جزاك الله خيراً' : '⏰ Session complete — Jazakallahu Khairan'}
        </div>
      )}

      {/* Main tappable area */}
      <div
        className="flex-1 flex flex-col items-center justify-center px-6 gap-5 cursor-pointer"
        onClick={() => { if (!done) { onIncrement(); vibrate(); } }}
      >
        {/* Category badge */}
        <span className={clsx('text-xs px-3 py-1 rounded-full font-medium', theme.badge)}>
          {CATEGORY_META[dhikr.category].emoji} {isRtl ? CATEGORY_META[dhikr.category].labelAr : CATEGORY_META[dhikr.category].labelEn}
        </span>

        {/* Arabic text */}
        <div className={clsx(
          'text-center transition-transform duration-150',
          completing && 'scale-105',
        )}>
          <p
            className={clsx('font-arabic leading-relaxed text-center', theme.text)}
            style={{ fontSize: dhikr.arabicPhrase.length > 100 ? '1.3rem' : dhikr.arabicPhrase.length > 50 ? '1.6rem' : '2rem' }}
            dir="rtl"
          >
            {dhikr.arabicPhrase}
          </p>
          <p className={clsx('text-sm mt-2', theme.subText)}>
            {dhikr.transliteration}
          </p>
        </div>

        {/* Circular ring counter */}
        <ProgressRing
          pct={pct}
          count={count}
          done={done}
          themeClass={{ ring: theme.ring, ringFg: theme.ringFg, text: theme.text }}
        />

        {/* Beat countdown bar — visible only when auto-play is running */}
        {autoPlay && !done && (
          <div className="w-full max-w-[200px] space-y-1">
            <div className={clsx(
              'h-1 rounded-full overflow-hidden',
              theme.dark ? 'bg-white/10' : 'bg-black/8',
            )}>
              <div
                className={clsx(
                  'h-full rounded-full transition-none',
                  theme.dark ? 'bg-indigo-400' : 'bg-gray-700',
                )}
                style={{ width: `${beatPct * 100}%` }}
              />
            </div>
            <p className={clsx('text-[10px] text-center tabular-nums', theme.subText)}>
              {isRtl
                ? `عدّ تلقائي كل ${autoPlayInterval}ث`
                : `Auto-counting every ${autoPlayInterval}s`}
            </p>
          </div>
        )}

        <p className={clsx('text-xs', theme.subText)}>
          {done
            ? (isRtl ? 'مكتمل ✓' : 'Complete ✓')
            : autoPlay
              ? (isRtl ? 'أو اضغط للعدّ يدوياً' : 'or tap to count manually')
              : (isRtl ? 'اضغط للعد' : 'Tap anywhere to count')}
        </p>

        {/* Info toggle */}
        <button
          onClick={e => { e.stopPropagation(); setShowInfo(v => !v); }}
          className={clsx('text-xs underline underline-offset-2 opacity-60', theme.text)}
        >
          {showInfo ? (isRtl ? 'إخفاء المعنى' : 'Hide meaning') : (isRtl ? 'عرض المعنى والمصدر' : 'Meaning & source')}
        </button>

        {showInfo && (
          <div
            className={clsx(
              'max-w-xs text-center rounded-2xl px-4 py-3 space-y-1 cursor-default',
              theme.dark ? 'bg-white/5' : 'bg-black/5',
            )}
            onClick={e => e.stopPropagation()}
          >
            <p className={clsx('text-sm', theme.text)} dir={isRtl ? 'rtl' : 'ltr'}>
              {isRtl ? dhikr.meaningAr : dhikr.meaningEn}
            </p>
            <p className={clsx('text-xs', theme.subText)} dir={isRtl ? 'rtl' : 'ltr'}>
              {isRtl ? dhikr.benefitAr : dhikr.benefitEn}
            </p>
            <p className={clsx('text-[10px] opacity-50 italic', theme.text)}>
              {isRtl ? dhikr.sourceRefAr : dhikr.sourceRef}
            </p>
          </div>
        )}
      </div>

      {/* Bottom controls */}
      <div className={clsx(
        'flex items-center justify-between px-6 py-5 pb-safe flex-shrink-0',
        theme.dark ? 'border-t border-white/10' : 'border-t border-black/5',
      )}>
        <button
          onClick={onPrev}
          disabled={index === 0}
          className={clsx(
            'p-3 rounded-2xl transition-colors',
            index === 0
              ? (theme.dark ? 'text-white/20' : 'text-gray-200')
              : (theme.dark ? 'hover:bg-white/10 text-white/70' : 'hover:bg-black/5 text-gray-600'),
          )}
        >
          <ChevronLeft className="w-6 h-6" />
        </button>

        {/* Auto-play toggle + pace selector */}
        <div className="flex flex-col items-center gap-1.5">
          {/* Speed pills — only visible when auto-play is ON */}
          {autoPlay && (
            <div className={clsx('flex items-center gap-1', isRtl && 'flex-row-reverse')}>
              {PACE_OPTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => onChangeInterval(s)}
                  className={clsx(
                    'px-2 py-0.5 rounded-full text-[10px] font-medium transition-colors',
                    autoPlayInterval === s
                      ? (theme.dark ? 'bg-white text-slate-900' : 'bg-gray-900 text-white')
                      : (theme.dark ? 'bg-white/10 text-white/50 hover:bg-white/20' : 'bg-black/5 text-gray-400 hover:bg-black/10'),
                  )}
                >
                  {s}s
                </button>
              ))}
            </div>
          )}

          <button
            onClick={onToggleAutoPlay}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-2xl text-sm font-medium transition-colors',
              autoPlay
                ? (theme.dark ? 'bg-indigo-500 text-white' : 'bg-gray-800 text-white')
                : (theme.dark ? 'bg-white/10 text-white/70' : 'bg-gray-100 text-gray-600'),
            )}
          >
            {autoPlay ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>
              {autoPlay
                ? (isRtl ? `تلقائي · ${autoPlayInterval}ث` : `Auto · ${autoPlayInterval}s`)
                : (isRtl ? 'تشغيل تلقائي' : 'Auto-play')}
            </span>
          </button>
        </div>

        <button
          onClick={onNext}
          disabled={index === items.length - 1}
          className={clsx(
            'p-3 rounded-2xl transition-colors',
            index === items.length - 1
              ? (theme.dark ? 'text-white/20' : 'text-gray-200')
              : (theme.dark ? 'hover:bg-white/10 text-white/70' : 'hover:bg-black/5 text-gray-600'),
          )}
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function DhikrPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  // Counts
  const [counts, setCounts]       = useState<CountRecord>(loadCounts);
  const [activeCategory, setActiveCategory] = useState<DhikrCategory | 'all'>('all');
  const [collapsedCats, setCollapsedCats]   = useState<Set<string>>(new Set());
  const [search, setSearch]                 = useState('');
  const [misbahaEntry, setMisbahaEntry]     = useState<DhikrEntry | null>(null);

  // Focus mode
  const [focusMode, setFocusMode]       = useState(false);
  const [focusCategory, setFocusCategory] = useState<DhikrCategory | 'all'>('all');
  const [focusIndex, setFocusIndex]     = useState(0);

  // Timer (seconds remaining; 0 = idle)
  const [timerSec, setTimerSec]         = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);

  // Auto-play & audio
  const [autoPlay, setAutoPlay]             = useState(false);
  const [autoPlayInterval, setAutoPlayInterval] = useState<number>(PACE_DEFAULT);
  const [audioEnabled, setAudioEnabled]     = useState(false);

  // Rewards
  const [rewards, setRewards]           = useState<RewardsData>(loadRewards);
  const [newAchievement, setNewAchievement] = useState<Achievement | null>(null);
  const [showRewards, setShowRewards]   = useState(false);

  // Derived focus list
  const focusItems = useMemo(() =>
    focusCategory === 'all'
      ? ADHKAR.slice()
      : ADHKAR.filter(d => d.category === focusCategory),
    [focusCategory],
  );

  // ── Timer tick ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!timerRunning) return;
    if (timerSec <= 0) { setTimerRunning(false); return; }
    const id = setInterval(() => setTimerSec(s => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [timerRunning, timerSec]);

  // ── Auto-play advance ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!autoPlay || !focusMode) return;
    const dhikr = focusItems[focusIndex];
    if (!dhikr) return;
    const count = getCount(counts, dhikr.id);
    if (count < dhikr.targetCount) return;

    const id = setTimeout(() => {
      if (focusIndex < focusItems.length - 1) {
        const next = focusIndex + 1;
        setFocusIndex(next);
        if (audioEnabled) speakArabic(focusItems[next]?.arabicPhrase ?? '');
      } else {
        // Session finished — record it
        recordSession();
      }
    }, 1600);
    return () => clearTimeout(id);
  }, [autoPlay, focusMode, counts, focusIndex, focusItems, audioEnabled]);

  // ── Rewards helpers ─────────────────────────────────────────────────────────

  function unlockAchievement(id: string, r: RewardsData): RewardsData {
    if (r.achievements.includes(id)) return r;
    const a = ACHIEVEMENTS[id];
    if (!a) return r;
    const next: RewardsData = {
      ...r,
      achievements: [...r.achievements, id],
      totalXP: r.totalXP + a.xp,
      todayXP: r.todayXP + a.xp,
    };
    setNewAchievement(a);
    return next;
  }

  function refreshStreak(r: RewardsData): RewardsData {
    const yesterday = new Date(Date.now() - 86_400_000).toISOString().slice(0, 10);
    if (r.lastActiveDate === TODAY) return r;
    const newStreak = r.lastActiveDate === yesterday ? r.streak + 1 : 1;
    let next: RewardsData = { ...r, streak: newStreak, lastActiveDate: TODAY };
    if (newStreak >= 7)  next = unlockAchievement('streak_7',  next);
    if (newStreak >= 30) next = unlockAchievement('streak_30', next);
    return next;
  }

  // ── Increment ───────────────────────────────────────────────────────────────
  const increment = useCallback((id: string) => {
    setCounts(prev => {
      const current = getCount(prev, id);
      const dhikr   = ADHKAR.find(d => d.id === id);
      if (!dhikr || current >= dhikr.targetCount) return prev;
      const next = { ...prev, [id]: { count: current + 1, date: TODAY } };
      saveCounts(next);
      return next;
    });

    setRewards(prev => {
      const dhikr   = ADHKAR.find(d => d.id === id);
      const current = getCount(counts, id);
      const newCount = current + 1;
      let r = { ...prev, totalXP: prev.totalXP + 1, todayXP: prev.todayXP + 1 };
      r = refreshStreak(r);

      // First ever dhikr
      if (!r.achievements.includes('first_dhikr')) r = unlockAchievement('first_dhikr', r);

      // Centurion — single dhikr count of 100
      if (newCount === 100) r = unlockAchievement('centurion', r);

      // Morning complete
      if (dhikr && MORNING_IDS.has(id) && newCount >= dhikr.targetCount) {
        const morningDone = ADHKAR.filter(d => MORNING_IDS.has(d.id)).every(d => {
          if (d.id === id) return true;
          return getCount(counts, d.id) >= d.targetCount;
        });
        if (morningDone) r = unlockAchievement('morning_complete', r);
      }

      // Evening complete
      if (dhikr && EVENING_IDS.has(id) && newCount >= dhikr.targetCount) {
        const eveningDone = ADHKAR.filter(d => EVENING_IDS.has(d.id)).every(d => {
          if (d.id === id) return true;
          return getCount(counts, d.id) >= d.targetCount;
        });
        if (eveningDone) r = unlockAchievement('evening_complete', r);
      }

      // Sleep complete
      if (dhikr && SLEEP_IDS.has(id) && newCount >= dhikr.targetCount) {
        const sleepDone = ADHKAR.filter(d => SLEEP_IDS.has(d.id)).every(d => {
          if (d.id === id) return true;
          return getCount(counts, d.id) >= d.targetCount;
        });
        if (sleepDone) r = unlockAchievement('sleep_complete', r);
      }

      // Full set
      const allDone = ADHKAR.every(d => {
        if (d.id === id) return newCount >= d.targetCount;
        return getCount(counts, d.id) >= d.targetCount;
      });
      if (allDone) r = unlockAchievement('full_set', r);

      saveRewards(r);
      return r;
    });
  }, [counts]);

  const reset = useCallback((id: string) => {
    setCounts(prev => {
      const next = { ...prev, [id]: { count: 0, date: TODAY } };
      saveCounts(next);
      return next;
    });
  }, []);

  // Stable increment callback for the active focus dhikr.
  // Changes identity when focusIndex/focusCategory changes — this is intentional
  // so the beat ticker in FocusView restarts on dhikr switch.
  const focusIncrement = useCallback(() => {
    const d = focusItems[focusIndex];
    if (d) increment(d.id);
  }, [focusItems, focusIndex, increment]);

  const resetAll = () => {
    const next: CountRecord = {};
    ADHKAR.forEach(d => { next[d.id] = { count: 0, date: TODAY }; });
    saveCounts(next);
    setCounts(next);
  };

  function toggleCat(cat: string) {
    setCollapsedCats(prev => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  }

  function startFocusSession(cat: DhikrCategory | 'all') {
    setFocusCategory(cat);
    setFocusIndex(0);
    setFocusMode(true);
    if (audioEnabled) {
      const first = cat === 'all' ? ADHKAR[0] : ADHKAR.find(d => d.category === cat);
      if (first) speakArabic(first.arabicPhrase);
    }
  }

  function recordSession() {
    const total = ADHKAR.reduce((sum, d) => sum + getCount(counts, d.id), 0);
    const done  = ADHKAR.filter(d => getCount(counts, d.id) >= d.targetCount).length;
    const cat   = focusCategory === 'all' ? undefined : focusCategory;

    setRewards(prev => {
      const r = { ...prev, totalSessions: prev.totalSessions + 1 };
      saveRewards(r);
      return r;
    });

    fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_date: TODAY,
        category: cat ?? null,
        total_dhikr_completed: done,
        total_count: total,
      }),
    }).catch(() => { /* offline — silent */ });
  }

  // ── Browse view derived data ─────────────────────────────────────────────────

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    const byCat = activeCategory === 'all' ? ADHKAR : ADHKAR.filter(d => d.category === activeCategory);
    if (!q) return byCat;
    return byCat.filter(d =>
      d.arabicPhrase.includes(q) ||
      d.transliteration.toLowerCase().includes(q) ||
      d.meaningEn.toLowerCase().includes(q) ||
      d.meaningAr.includes(q) ||
      d.benefitEn.toLowerCase().includes(q) ||
      d.sourceRef.toLowerCase().includes(q)
    );
  }, [activeCategory, search]);

  const totalDone = ADHKAR.filter(d => getCount(counts, d.id) >= d.targetCount).length;

  const grouped: Record<DhikrCategory, DhikrEntry[]> = {
    after_salah: [], quranic: [], any_time: [], morning: [], evening: [], sleep: [], travel: [],
  };
  filtered.forEach(d => grouped[d.category].push(d));

  const morningDone = ADHKAR.filter(d => MORNING_IDS.has(d.id) && getCount(counts, d.id) >= d.targetCount).length;
  const eveningDone = ADHKAR.filter(d => EVENING_IDS.has(d.id) && getCount(counts, d.id) >= d.targetCount).length;
  const sleepDone   = ADHKAR.filter(d => SLEEP_IDS.has(d.id)   && getCount(counts, d.id) >= d.targetCount).length;

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <>
      {/* Misbaha overlay */}
      {misbahaEntry && (
        <MisbahaView
          dhikr={misbahaEntry}
          isRtl={isRtl}
          onClose={() => setMisbahaEntry(null)}
        />
      )}

      {/* Focus mode overlay */}
      {focusMode && (
        <FocusView
          items={focusItems}
          index={focusIndex}
          counts={counts}
          isRtl={isRtl}
          audioEnabled={audioEnabled}
          autoPlay={autoPlay}
          autoPlayInterval={autoPlayInterval}
          timerSec={timerSec}
          timerRunning={timerRunning}
          onIncrement={focusIncrement}
          onPrev={() => setFocusIndex(i => Math.max(0, i - 1))}
          onNext={() => {
            const next = Math.min(focusItems.length - 1, focusIndex + 1);
            setFocusIndex(next);
            if (audioEnabled) speakArabic(focusItems[next]?.arabicPhrase ?? '');
          }}
          onClose={() => { setFocusMode(false); recordSession(); }}
          onToggleAudio={() => setAudioEnabled(v => !v)}
          onToggleAutoPlay={() => setAutoPlay(v => !v)}
          onChangeInterval={setAutoPlayInterval}
          onStartTimer={(mins) => { setTimerSec(mins * 60); setTimerRunning(true); }}
          onStopTimer={() => { setTimerRunning(false); setTimerSec(0); }}
        />
      )}

      {/* Achievement toast */}
      {newAchievement && (
        <AchievementToast
          achievement={newAchievement}
          isRtl={isRtl}
          onDone={() => setNewAchievement(null)}
        />
      )}

      {/* Browse page */}
      <div className="max-w-xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>

        {/* ── Header ── */}
        <div className={clsx('flex items-start justify-between mb-4', isRtl && 'flex-row-reverse')}>
          <div>
            <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
              {isRtl ? 'التسبيح اليومي' : 'Daily Dhikr'}
            </h1>
            <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
              {totalDone}/{ADHKAR.length} {isRtl ? 'مكتمل اليوم' : 'complete today'}
            </p>
          </div>
          <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
            {/* Rewards button */}
            <button
              onClick={() => setShowRewards(v => !v)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors',
                showRewards ? 'bg-amber-50 border-amber-200 text-amber-700' : 'border-gray-200 text-gray-500 hover:bg-gray-50',
              )}
            >
              <Trophy className="w-3.5 h-3.5" />
              {isRtl ? 'الجوائز' : 'Rewards'}
            </button>
            {totalDone > 0 && (
              <button
                onClick={() => { if (window.confirm(isRtl ? 'إعادة تعيين اليوم؟' : 'Reset today?')) resetAll(); }}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-400 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* ── Overall progress bar ── */}
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-5">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all"
            style={{ width: `${ADHKAR.length ? (totalDone / ADHKAR.length) * 100 : 0}%` }}
          />
        </div>

        {/* ── Rewards panel ── */}
        {showRewards && (
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100 rounded-2xl p-4 mb-5 space-y-3">
            <div className={clsx('flex items-center justify-between', isRtl && 'flex-row-reverse')}>
              <h2 className={clsx('text-sm font-bold text-amber-900', isRtl && 'font-arabic')}>
                {isRtl ? 'إنجازاتي' : 'My Progress'}
              </h2>
              <div className={clsx('flex items-center gap-3', isRtl && 'flex-row-reverse')}>
                <span className="flex items-center gap-1 text-xs text-orange-600 font-bold">
                  <Flame className="w-3.5 h-3.5" />
                  {rewards.streak} {isRtl ? 'يوم' : 'day streak'}
                </span>
                <span className="flex items-center gap-1 text-xs text-amber-600 font-bold">
                  <Star className="w-3.5 h-3.5" />
                  {rewards.todayXP} XP {isRtl ? 'اليوم' : 'today'}
                </span>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.values(ACHIEVEMENTS).map(a => {
                const unlocked = rewards.achievements.includes(a.id);
                return (
                  <div
                    key={a.id}
                    className={clsx(
                      'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs transition-all',
                      unlocked ? 'bg-amber-200 text-amber-900 font-medium' : 'bg-gray-100 text-gray-400',
                    )}
                    title={`+${a.xp} XP`}
                  >
                    <span className={unlocked ? '' : 'grayscale opacity-50'}>{a.emoji}</span>
                    {isRtl ? a.labelAr : a.labelEn}
                  </div>
                );
              })}
            </div>
            <p className="text-[10px] text-amber-700/60">
              {isRtl
                ? `${rewards.totalSessions} جلسة إجمالية · ${rewards.totalXP} XP إجمالي`
                : `${rewards.totalSessions} total sessions · ${rewards.totalXP} total XP`}
            </p>
          </div>
        )}

        {/* ── Quick-start program cards ── */}
        <div className={clsx('grid grid-cols-3 gap-2.5 mb-5', isRtl && 'dir-rtl')}>
          <button
            onClick={() => startFocusSession('morning')}
            className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 p-3 text-left shadow-sm hover:shadow-md active:scale-[0.98] transition-all"
          >
            <Sun className="w-5 h-5 text-white/80 mb-1.5" />
            <p className={clsx('text-white font-bold text-xs leading-tight', isRtl && 'font-arabic text-right')}>
              {isRtl ? 'أذكار الصباح' : 'Morning'}
            </p>
            <p className="text-white/70 text-[10px] mt-0.5">
              {morningDone}/{ADHKAR.filter(d => MORNING_IDS.has(d.id)).length}
            </p>
            {morningDone === ADHKAR.filter(d => MORNING_IDS.has(d.id)).length && (
              <div className="absolute top-2 right-2 w-5 h-5 bg-white/20 rounded-full flex items-center justify-center">
                <Check className="w-3 h-3 text-white" />
              </div>
            )}
          </button>
          <button
            onClick={() => startFocusSession('evening')}
            className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-700 p-3 text-left shadow-sm hover:shadow-md active:scale-[0.98] transition-all"
          >
            <Moon className="w-5 h-5 text-white/80 mb-1.5" />
            <p className={clsx('text-white font-bold text-xs leading-tight', isRtl && 'font-arabic text-right')}>
              {isRtl ? 'أذكار المساء' : 'Evening'}
            </p>
            <p className="text-white/70 text-[10px] mt-0.5">
              {eveningDone}/{ADHKAR.filter(d => EVENING_IDS.has(d.id)).length}
            </p>
            {eveningDone === ADHKAR.filter(d => EVENING_IDS.has(d.id)).length && (
              <div className="absolute top-2 right-2 w-5 h-5 bg-white/20 rounded-full flex items-center justify-center">
                <Check className="w-3 h-3 text-white" />
              </div>
            )}
          </button>
          <button
            onClick={() => startFocusSession('sleep')}
            className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-700 to-purple-900 p-3 text-left shadow-sm hover:shadow-md active:scale-[0.98] transition-all"
          >
            <BedDouble className="w-5 h-5 text-white/80 mb-1.5" />
            <p className={clsx('text-white font-bold text-xs leading-tight', isRtl && 'font-arabic text-right')}>
              {isRtl ? 'أذكار النوم' : 'Sleep'}
            </p>
            <p className="text-white/70 text-[10px] mt-0.5">
              {sleepDone}/{ADHKAR.filter(d => SLEEP_IDS.has(d.id)).length}
            </p>
            {sleepDone === ADHKAR.filter(d => SLEEP_IDS.has(d.id)).length && (
              <div className="absolute top-2 right-2 w-5 h-5 bg-white/20 rounded-full flex items-center justify-center">
                <Check className="w-3 h-3 text-white" />
              </div>
            )}
          </button>
        </div>

        {/* Start full focus session */}
        <button
          onClick={() => startFocusSession('all')}
          className={clsx(
            'w-full flex items-center justify-center gap-2 py-3 rounded-2xl text-sm font-medium mb-5 transition-all',
            'bg-gray-900 text-white hover:bg-gray-800 active:scale-[0.98] shadow-sm',
          )}
        >
          <Play className="w-4 h-4" />
          {isRtl ? 'بدء جلسة التركيز الكاملة' : 'Start Full Focus Session'}
        </button>

        {/* ── Search ── */}
        <div className="relative mb-3">
          <Search className={clsx(
            'absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400',
            isRtl ? 'right-3' : 'left-3',
          )} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={isRtl ? 'ابحث في الأذكار...' : 'Search adhkar...'}
            className={clsx(
              'w-full bg-white border border-gray-200 rounded-xl py-2.5 text-sm',
              'focus:ring-2 focus:ring-teal-300 focus:border-teal-400 outline-none transition',
              isRtl ? 'pr-9 pl-3 text-right font-arabic' : 'pl-9 pr-3',
            )}
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className={clsx(
                'absolute top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600',
                isRtl ? 'left-3' : 'right-3',
              )}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* ── Category filter tabs ── */}
        <div className={clsx('flex flex-wrap gap-1.5 mb-5', isRtl && 'flex-row-reverse')}>
          <button
            onClick={() => setActiveCategory('all')}
            className={clsx(
              'text-xs px-2.5 py-1 rounded-full border transition-colors',
              activeCategory === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'text-gray-500 border-gray-200 hover:bg-gray-50',
            )}
          >
            {isRtl ? 'الكل' : 'All'}
          </button>
          {CATS_ORDER.map(cat => {
            const meta   = CATEGORY_META[cat];
            const colors = BROWSE_COLORS[meta.color] ?? BROWSE_COLORS.violet;
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat === activeCategory ? 'all' : cat)}
                className={clsx(
                  'text-xs px-2.5 py-1 rounded-full border transition-colors',
                  activeCategory === cat ? `${colors.badge} border-transparent` : 'text-gray-500 border-gray-200 hover:bg-gray-50',
                )}
              >
                {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
              </button>
            );
          })}
        </div>

        {/* ── Grouped or flat list ── */}
        {activeCategory === 'all' ? (
          <div className="space-y-6">
            {CATS_ORDER.map(cat => {
              const items = grouped[cat];
              if (!items.length) return null;
              const meta      = CATEGORY_META[cat];
              const collapsed = collapsedCats.has(cat);
              const catDone   = items.filter(d => getCount(counts, d.id) >= d.targetCount).length;
              return (
                <div key={cat}>
                  <button
                    onClick={() => toggleCat(cat)}
                    className={clsx('flex items-center gap-2 mb-3 w-full text-start', isRtl && 'flex-row-reverse')}
                  >
                    <span className="text-sm font-semibold text-gray-700">
                      {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
                    </span>
                    <span className="text-xs text-gray-400">({catDone}/{items.length})</span>
                    <span className={clsx('text-gray-400', isRtl ? 'me-auto' : 'ms-auto')}>
                      {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                    </span>
                    {/* Focus session for this category */}
                    <button
                      onClick={e => { e.stopPropagation(); startFocusSession(cat); }}
                      className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-500 transition-colors"
                    >
                      <Play className="w-2.5 h-2.5" />
                      {isRtl ? 'تركيز' : 'Focus'}
                    </button>
                  </button>
                  {!collapsed && (
                    <div className="space-y-3">
                      {items.map(d => (
                        <DhikrBrowseCard
                          key={d.id}
                          dhikr={d}
                          count={getCount(counts, d.id)}
                          isRtl={isRtl}
                          onIncrement={() => increment(d.id)}
                          onReset={() => reset(d.id)}
                          onMisbaha={() => setMisbahaEntry(d)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map(d => (
              <DhikrBrowseCard
                key={d.id}
                dhikr={d}
                count={getCount(counts, d.id)}
                isRtl={isRtl}
                onIncrement={() => increment(d.id)}
                onReset={() => reset(d.id)}
                onMisbaha={() => setMisbahaEntry(d)}
              />
            ))}
          </div>
        )}

        <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
          {isRtl
            ? 'يُعاد التعيين تلقائياً كل يوم · لا يُرفع أي بيانات شخصية'
            : 'Auto-resets daily · No personal data uploaded'}
        </p>
      </div>
    </>
  );
}
