import { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus, Flame, Calendar } from 'lucide-react';
import type { EmotionPoint } from '../../types/therapy';
import clsx from 'clsx';

type Lang = 'ar' | 'en';

// ---------------------------------------------------------------------------
// Emotion → colour mapping (Tailwind utility classes)
// ---------------------------------------------------------------------------

const EMOTION_COLOR: Record<string, string> = {
  hopelessness: 'bg-rose-600 text-white',
  grief:        'bg-rose-400 text-white',
  fear:         'bg-orange-400 text-white',
  anger:        'bg-red-500 text-white',
  guilt:        'bg-purple-400 text-white',
  loneliness:   'bg-purple-300 text-white',
  sadness:      'bg-blue-400 text-white',
  stress:       'bg-orange-300 text-white',
  anxiety:      'bg-amber-400 text-white',
  doubt:        'bg-slate-400 text-white',
  general:      'bg-gray-300 text-gray-700',
  gratitude:    'bg-emerald-500 text-white',
};

const EMOTION_DOT_COLOR: Record<string, string> = {
  hopelessness: '#e11d48',
  grief:        '#fb7185',
  fear:         '#fb923c',
  anger:        '#ef4444',
  guilt:        '#a855f7',
  loneliness:   '#c084fc',
  sadness:      '#60a5fa',
  stress:       '#fdba74',
  anxiety:      '#fbbf24',
  doubt:        '#94a3b8',
  general:      '#d1d5db',
  gratitude:    '#10b981',
};

// ---------------------------------------------------------------------------
// Helper — group timeline by calendar day
// ---------------------------------------------------------------------------

function groupByDay(timeline: EmotionPoint[]): Map<string, EmotionPoint[]> {
  const map = new Map<string, EmotionPoint[]>();
  for (const pt of timeline) {
    const day = pt.timestamp.slice(0, 10); // "YYYY-MM-DD"
    const existing = map.get(day) ?? [];
    existing.push(pt);
    map.set(day, existing);
  }
  return map;
}

function last7Days(): string[] {
  const days: string[] = [];
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().slice(0, 10));
  }
  return days;
}

function dominantEmotion(points: EmotionPoint[]): string | null {
  if (!points.length) return null;
  const counts: Record<string, number> = {};
  for (const p of points) counts[p.emotion] = (counts[p.emotion] ?? 0) + 1;
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
}

function formatDay(iso: string): string {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('en', { weekday: 'short' }).slice(0, 2);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TrendBadge({ trend, lang }: { trend: string; lang: Lang }) {
  const isRtl = lang === 'ar';
  const cfg = {
    improving:   { Icon: TrendingUp,   cls: 'text-emerald-600 bg-emerald-50 border-emerald-200', label: { en: 'Improving', ar: 'في تحسّن' } },
    challenging: { Icon: TrendingDown, cls: 'text-rose-600 bg-rose-50 border-rose-200',          label: { en: 'Needs support', ar: 'يحتاج دعماً' } },
    stable:      { Icon: Minus,        cls: 'text-amber-600 bg-amber-50 border-amber-200',        label: { en: 'Stable', ar: 'مستقر' } },
  }[trend] ?? {
    Icon: Minus, cls: 'text-amber-600 bg-amber-50 border-amber-200', label: { en: 'Stable', ar: 'مستقر' },
  };
  const { Icon } = cfg;
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border',
      cfg.cls,
      isRtl && 'font-arabic flex-row-reverse',
    )}>
      <Icon className="w-3.5 h-3.5" />
      {cfg.label[lang]}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface EmotionGrowthMapProps {
  timeline: EmotionPoint[];
  trend: string;
  streakDays: number;
  lang: Lang;
}

export function EmotionGrowthMap({ timeline, trend, streakDays, lang }: EmotionGrowthMapProps) {
  const isRtl = lang === 'ar';
  const byDay = useMemo(() => groupByDay(timeline), [timeline]);
  const week = useMemo(() => last7Days(), []);

  if (timeline.length === 0) return null;

  return (
    <div className="space-y-4">
      {/* Header row: trend + streak */}
      <div className={clsx('flex items-center justify-between', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-1.5 text-xs text-gray-500', isRtl && 'flex-row-reverse font-arabic')}>
          <span className={clsx('font-medium text-gray-700', isRtl && 'font-arabic')}>
            {isRtl ? 'مسار النمو' : 'Growth Map'}
          </span>
        </div>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          {streakDays > 0 && (
            <span className="inline-flex items-center gap-1 text-xs text-orange-600 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded-full">
              <Flame className="w-3 h-3" />
              {streakDays}{isRtl ? ' يوم متواصل' : ' day streak'}
            </span>
          )}
          <TrendBadge trend={trend} lang={lang} />
        </div>
      </div>

      {/* 7-day calendar grid */}
      <div>
        <div className={clsx('flex items-center gap-1 mb-1.5', isRtl && 'flex-row-reverse')}>
          <Calendar className="w-3.5 h-3.5 text-gray-400" />
          <span className={clsx('text-xs text-gray-400 uppercase tracking-wide font-medium', isRtl && 'font-arabic')}>
            {isRtl ? 'آخر ٧ أيام' : 'Last 7 days'}
          </span>
        </div>
        <div className={clsx('grid grid-cols-7 gap-1', isRtl && 'direction-rtl')}>
          {week.map(day => {
            const pts = byDay.get(day) ?? [];
            const dom = dominantEmotion(pts);
            const dot = dom ? EMOTION_DOT_COLOR[dom] : undefined;
            return (
              <div key={day} className="flex flex-col items-center gap-0.5">
                <span className="text-[9px] text-gray-400 font-medium">{formatDay(day)}</span>
                <div
                  className={clsx(
                    'w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold',
                    dot ? 'shadow-sm' : 'bg-gray-100 text-gray-300',
                  )}
                  style={dot ? { backgroundColor: dot + '33', border: `2px solid ${dot}`, color: dot } : undefined}
                  title={dom ?? 'no session'}
                >
                  {pts.length > 0 ? pts.length : '·'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Emotion journey lane — horizontal scroll */}
      <div>
        <p className={clsx('text-xs text-gray-400 uppercase tracking-wide font-medium mb-1.5', isRtl && 'font-arabic text-right')}>
          {isRtl ? 'رحلتك العاطفية' : 'Emotional journey'}
        </p>
        <div
          className={clsx('flex gap-1.5 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-gray-200', isRtl && 'flex-row-reverse')}
          style={{ scrollbarWidth: 'thin' }}
        >
          {timeline.map((pt, i) => (
            <div
              key={pt.session_id}
              className="flex flex-col items-center gap-0.5 flex-shrink-0"
              title={`${isRtl ? pt.label_ar : pt.label_en}${pt.theme ? ` · ${pt.theme}` : ''}`}
            >
              <div
                className={clsx(
                  'w-7 h-7 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0 shadow-sm',
                  EMOTION_COLOR[pt.emotion] ?? 'bg-gray-200 text-gray-600',
                )}
              >
                {i + 1}
              </div>
            </div>
          ))}
        </div>
        {/* Legend — first 6 unique emotions shown */}
        <div className={clsx('flex flex-wrap gap-x-3 gap-y-1 mt-2', isRtl && 'flex-row-reverse')}>
          {Array.from(new Set(timeline.map(p => p.emotion))).slice(0, 6).map(em => {
            const lbl = timeline.find(p => p.emotion === em);
            return (
              <span key={em} className={clsx('flex items-center gap-1 text-[10px] text-gray-500', isRtl && 'flex-row-reverse')}>
                <span
                  className="w-2 h-2 rounded-full inline-block flex-shrink-0"
                  style={{ backgroundColor: EMOTION_DOT_COLOR[em] ?? '#ccc' }}
                />
                {isRtl ? lbl?.label_ar : lbl?.label_en}
              </span>
            );
          })}
        </div>
      </div>

      {/* Simple SVG sparkline of wellbeing over time */}
      {timeline.length >= 3 && (
        <WellbeingSparkline timeline={timeline} lang={lang} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SVG sparkline — wellbeing score over sessions
// ---------------------------------------------------------------------------

const SCORE: Record<string, number> = {
  hopelessness: 0, grief: 1, fear: 1.5, anger: 2, guilt: 2, loneliness: 2,
  sadness: 2, stress: 2.5, anxiety: 2.5, doubt: 3, general: 3.5, gratitude: 5,
};

function WellbeingSparkline({ timeline, lang }: { timeline: EmotionPoint[]; lang: Lang }) {
  const isRtl = lang === 'ar';
  const scores = timeline.map(p => SCORE[p.emotion] ?? 3);
  const W = 260;
  const H = 40;
  const pad = 4;
  const max = 5;
  const step = (W - pad * 2) / (scores.length - 1);

  const points = scores.map((s, i) => {
    const x = pad + i * step;
    const y = H - pad - ((s / max) * (H - pad * 2));
    return `${x},${y}`;
  });
  const polyline = points.join(' ');

  // gradient from rose to emerald based on trend
  const lastScore = scores[scores.length - 1];
  const color = lastScore >= 3.5 ? '#10b981' : lastScore >= 2 ? '#f59e0b' : '#f43f5e';

  return (
    <div>
      <p className={clsx('text-xs text-gray-400 uppercase tracking-wide font-medium mb-1', isRtl && 'font-arabic text-right')}>
        {isRtl ? 'مؤشر العافية' : 'Wellbeing indicator'}
      </p>
      <div className="bg-gray-50 rounded-xl px-3 py-2">
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-10">
          {/* Zero line */}
          <line x1={pad} y1={H - pad} x2={W - pad} y2={H - pad} stroke="#e5e7eb" strokeWidth="1" />
          {/* Top line */}
          <line x1={pad} y1={pad} x2={W - pad} y2={pad} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="4 3" />
          {/* Sparkline */}
          <polyline
            points={polyline}
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {/* Last point dot */}
          {points.length > 0 && (() => {
            const [lx, ly] = points[points.length - 1].split(',').map(Number);
            return <circle cx={lx} cy={ly} r="3" fill={color} />;
          })()}
        </svg>
        <div className={clsx('flex justify-between text-[9px] text-gray-400 mt-0.5', isRtl && 'flex-row-reverse font-arabic')}>
          <span>{isRtl ? 'بداية' : 'Start'}</span>
          <span>{isRtl ? 'الآن' : 'Now'}</span>
        </div>
      </div>
    </div>
  );
}
