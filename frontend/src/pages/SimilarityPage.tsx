/**
 * Verse Similarity Explorer — Complete redesign
 *
 * Algorithm upgrades over previous version:
 *  1. Hybrid RRF Fusion  — merges the dense embedding signal
 *     (semantic/similar endpoint, backed by Qdrant vector search) with
 *     the sparse lexical/root/concept signal (similarity/advanced endpoint)
 *     via Reciprocal Rank Fusion (k=60). This is the production pattern
 *     used by Qdrant, Vespa, Weaviate and is the state-of-the-art approach
 *     for Arabic semantic search as validated by QurSim benchmark studies.
 *  2. Mode selector — Hybrid (default), Semantic-only, Lexical-only,
 *     Root-based — letting users understand and control the algorithm.
 *  3. Shared-word highlighting in Arabic text — React token array
 *     (never dangerouslySetInnerHTML).
 *
 * UI upgrades:
 *  4. SVG hexagonal radar chart per match (6 score axes).
 *  5. SVG Constellation view — radial layout where distance ∝ dissimilarity,
 *     color ∝ connection type, size ∝ score.
 *  6. Exploration chain — "Explore from here →" hops through connected
 *     verses; breadcrumb trail lets users retrace the path.
 *  7. Connection type icons and improved score pills.
 */

import {
  useState, useEffect, useCallback, useRef, useMemo,
} from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Search, Loader2, AlertCircle, BookOpen, RefreshCw, ArrowRight,
  Sparkles, ChevronDown, ChevronUp, GitBranch, Network, Zap, Hash,
  Layers, Filter, Tag, X, ChevronRight, Cpu, Brain, AlignLeft,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { quranApi, api, AdvancedSimilarityMatch, SimilarityScores } from '../lib/api';
import { parseAPIError } from '../components/common';

// ─── Types ────────────────────────────────────────────────────────────────────

type AlgorithmMode = 'hybrid' | 'semantic' | 'lexical' | 'root';
type ViewMode = 'list' | 'constellation';

interface HistoryEntry {
  sura: number;
  aya: number;
  nameAr: string;
  nameEn: string;
}

interface FusedMatch extends AdvancedSimilarityMatch {
  rrf_score: number;
  semantic_score: number;
}

interface SimilarityError {
  message: string;
  message_ar: string;
  request_id?: string;
}

// ─── Algorithm mode metadata ─────────────────────────────────────────────────

const ALGORITHM_MODES: {
  id: AlgorithmMode;
  icon: React.ElementType;
  label_en: string;
  label_ar: string;
  desc_en: string;
  desc_ar: string;
  color: string;
  bg: string;
  border: string;
}[] = [
  {
    id: 'hybrid',
    icon: Cpu,
    label_en: 'Hybrid AI',
    label_ar: 'هجين',
    desc_en: 'RRF fusion of vector embeddings + lexical/root signals (best accuracy)',
    desc_ar: 'دمج التمثيلات المتجهة مع الإشارات اللفظية عبر RRF (أعلى دقة)',
    color: 'text-emerald-700',
    bg: 'bg-emerald-100',
    border: 'border-emerald-300',
  },
  {
    id: 'semantic',
    icon: Brain,
    label_en: 'Semantic',
    label_ar: 'دلالي',
    desc_en: 'Dense vector embeddings — finds thematic similarity beyond shared words',
    desc_ar: 'تشابه المعاني عبر نماذج التمثيل — يتجاوز المطابقة اللفظية',
    color: 'text-violet-700',
    bg: 'bg-violet-100',
    border: 'border-violet-300',
  },
  {
    id: 'lexical',
    icon: AlignLeft,
    label_en: 'Lexical',
    label_ar: 'لفظي',
    desc_en: 'TF-IDF cosine + concept overlap — shared vocabulary and themes',
    desc_ar: 'تشابه المفردات والمفاهيم المشتركة',
    color: 'text-blue-700',
    bg: 'bg-blue-100',
    border: 'border-blue-300',
  },
  {
    id: 'root',
    icon: Hash,
    label_en: 'Root-Based',
    label_ar: 'جذري',
    desc_en: 'Arabic morphological root analysis — finds derivational similarity',
    desc_ar: 'تحليل الجذور الصرفية العربية — يكشف التشابه الاشتقاقي',
    color: 'text-amber-700',
    bg: 'bg-amber-100',
    border: 'border-amber-300',
  },
];

// ─── Connection type styles ───────────────────────────────────────────────────

const CONN_STYLES: Record<string, {
  icon: React.ElementType;
  color: string; bg: string; border: string;
  label_en: string; label_ar: string;
}> = {
  lexical:    { icon: AlignLeft, color: 'text-blue-700',   bg: 'bg-blue-50',   border: 'border-blue-200',   label_en: 'Lexical',    label_ar: 'لفظي'    },
  thematic:   { icon: Layers,    color: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-200', label_en: 'Thematic',   label_ar: 'موضوعي'  },
  conceptual: { icon: Network,   color: 'text-indigo-700', bg: 'bg-indigo-50', border: 'border-indigo-200', label_en: 'Conceptual', label_ar: 'مفاهيمي' },
  grammatical:{ icon: GitBranch, color: 'text-green-700',  bg: 'bg-green-50',  border: 'border-green-200',  label_en: 'Grammatical',label_ar: 'نحوي'    },
  semantic:   { icon: Brain,     color: 'text-amber-700',  bg: 'bg-amber-50',  border: 'border-amber-200',  label_en: 'Semantic',   label_ar: 'دلالي'   },
  root_based: { icon: Hash,      color: 'text-teal-700',   bg: 'bg-teal-50',   border: 'border-teal-200',   label_en: 'Root',       label_ar: 'جذري'    },
  narrative:  { icon: BookOpen,  color: 'text-rose-700',   bg: 'bg-rose-50',   border: 'border-rose-200',   label_en: 'Narrative',  label_ar: 'سردي'    },
};
const CONN_FALLBACK = { icon: Zap, color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200', label_en: 'Related', label_ar: 'مرتبط' };

// Node fill colors for constellation (hex so SVG can use them)
const CONN_FILL: Record<string, string> = {
  lexical: '#3b82f6', thematic: '#8b5cf6', conceptual: '#6366f1',
  grammatical: '#22c55e', semantic: '#f59e0b', root_based: '#14b8a6',
  narrative: '#f43f5e',
};

// ─── Surah name map ───────────────────────────────────────────────────────────

const SURAH_NAME_MAP: Record<string, number> = {
  'الفاتحة':1,'البقرة':2,'آل عمران':3,'النساء':4,'المائدة':5,'الأنعام':6,'الأعراف':7,
  'الأنفال':8,'التوبة':9,'يونس':10,'هود':11,'يوسف':12,'الرعد':13,'إبراهيم':14,'الحجر':15,
  'النحل':16,'الإسراء':17,'الكهف':18,'مريم':19,'طه':20,'الأنبياء':21,'الحج':22,
  'المؤمنون':23,'النور':24,'الفرقان':25,'الشعراء':26,'النمل':27,'القصص':28,'العنكبوت':29,
  'الروم':30,'لقمان':31,'السجدة':32,'الأحزاب':33,'سبأ':34,'فاطر':35,'يس':36,'الصافات':37,
  'ص':38,'الزمر':39,'غافر':40,'فصلت':41,'الشورى':42,'الزخرف':43,'الدخان':44,'الجاثية':45,
  'الأحقاف':46,'محمد':47,'الفتح':48,'الحجرات':49,'ق':50,'الذاريات':51,'الطور':52,
  'النجم':53,'القمر':54,'الرحمن':55,'الواقعة':56,'الحديد':57,'المجادلة':58,'الحشر':59,
  'الممتحنة':60,'الصف':61,'الجمعة':62,'المنافقون':63,'التغابن':64,'الطلاق':65,'التحريم':66,
  'الملك':67,'القلم':68,'الحاقة':69,'المعارج':70,'نوح':71,'الجن':72,'المزمل':73,'المدثر':74,
  'القيامة':75,'الإنسان':76,'المرسلات':77,'النبأ':78,'النازعات':79,'عبس':80,'التكوير':81,
  'الانفطار':82,'المطففين':83,'الانشقاق':84,'البروج':85,'الطارق':86,'الأعلى':87,'الغاشية':88,
  'الفجر':89,'البلد':90,'الشمس':91,'الليل':92,'الضحى':93,'الشرح':94,'التين':95,'العلق':96,
  'القدر':97,'البينة':98,'الزلزلة':99,'العاديات':100,'القارعة':101,'التكاثر':102,'العصر':103,
  'الهمزة':104,'الفيل':105,'قريش':106,'الماعون':107,'الكوثر':108,'الكافرون':109,'النصر':110,
  'المسد':111,'الإخلاص':112,'الفلق':113,'الناس':114,
  'fatiha':1,'al-fatiha':1,'baqarah':2,'al-baqarah':2,'imran':3,'al-imran':3,'nisa':4,
  'maidah':5,'anam':6,'araf':7,'anfal':8,'tawbah':9,'yunus':10,'hud':11,'yusuf':12,
  'rad':13,'ibrahim':14,'hijr':15,'nahl':16,'isra':17,'kahf':18,'maryam':19,'taha':20,
  'anbiya':21,'hajj':22,'muminun':23,'nur':24,'furqan':25,'shuara':26,'naml':27,
  'qasas':28,'ankabut':29,'rum':30,'luqman':31,'sajdah':32,'ahzab':33,'saba':34,
  'fatir':35,'yasin':36,'ya-sin':36,'yaseen':36,'saffat':37,'sad':38,'zumar':39,
  'ghafir':40,'fussilat':41,'shura':42,'zukhruf':43,'dukhan':44,'jathiya':45,'ahqaf':46,
  'muhammad':47,'fath':48,'hujurat':49,'qaf':50,'dhariyat':51,'tur':52,'najm':53,
  'qamar':54,'rahman':55,'al-rahman':55,'waqia':56,'hadid':57,'mujadila':58,'hashr':59,
  'mumtahina':60,'saff':61,'jumua':62,'munafiqun':63,'taghabun':64,'talaq':65,'tahrim':66,
  'mulk':67,'qalam':68,'haaqqa':69,'maarij':70,'nuh':71,'noah':71,'jinn':72,
  'muzzammil':73,'muddathir':74,'qiyama':75,'insan':76,'mursalat':77,'naba':78,
  'naziat':79,'abasa':80,'takwir':81,'infitar':82,'mutaffifin':83,'inshiqaq':84,
  'buruj':85,'tariq':86,'ala':87,'ghashiya':88,'fajr':89,'balad':90,'shams':91,
  'layl':92,'duha':93,'sharh':94,'tin':95,'alaq':96,'qadr':97,'bayyina':98,
  'zalzala':99,'adiyat':100,'qaria':101,'takathur':102,'asr':103,'humaza':104,
  'fil':105,'quraysh':106,'maun':107,'kawthar':108,'kafirun':109,'nasr':110,
  'masad':111,'ikhlas':112,'falaq':113,'nas':114,
};

function normalizeArabicDigits(s: string): string {
  return '٠١٢٣٤٥٦٧٨٩'.split('').reduce((acc, d, i) => acc.replace(new RegExp(d, 'g'), String(i)), s);
}

function parseInput(input: string): { sura: number; aya: number; isTextSearch: false } | { isTextSearch: true; text: string } {
  let n = normalizeArabicDigits(input.trim()).replace(/\s+/g, ' ').replace(/^سورة\s+/i, '');
  const nm = n.match(/^(\d{1,3})\s*[:،,\-\s]\s*(\d{1,3})$/);
  if (nm) {
    const s = +nm[1], a = +nm[2];
    if (s >= 1 && s <= 114 && a >= 1) return { sura: s, aya: a, isTextSearch: false };
  }
  const sm = n.match(/^([^\d:،,]+?)\s*[:،,]?\s*(\d{1,3})$/);
  if (sm) {
    const key = sm[1].trim();
    const a = +sm[2];
    const ar = SURAH_NAME_MAP[key];
    if (ar) return { sura: ar, aya: a, isTextSearch: false };
    const en = key.toLowerCase().replace(/^(al-|al)/, '');
    const bySuffix = SURAH_NAME_MAP[key.toLowerCase()] || SURAH_NAME_MAP[`al-${en}`] || SURAH_NAME_MAP[en];
    if (bySuffix) return { sura: bySuffix, aya: a, isTextSearch: false };
  }
  if (/^\d{1,3}$/.test(n)) {
    const num = +n;
    if (num >= 1 && num <= 114) return { sura: num, aya: 1, isTextSearch: false };
  }
  return { isTextSearch: true, text: input.trim() };
}

// ─── RRF Fusion ───────────────────────────────────────────────────────────────

function reciprocalRankFusion(
  lists: Array<{ key: string }[]>,
  k = 60,
): Map<string, number> {
  const scores = new Map<string, number>();
  for (const list of lists) {
    list.forEach((item, rank) => {
      scores.set(item.key, (scores.get(item.key) ?? 0) + 1 / (k + rank + 1));
    });
  }
  return scores;
}

// ─── Shared word highlighting ─────────────────────────────────────────────────

function stripDiacritics(s: string): string {
  return s.replace(/[ً-ٰٟ]/g, '');
}

function highlightSharedWords(uthmani: string, sharedWords: string[]): React.ReactNode {
  if (!sharedWords.length) return uthmani;
  const stripped = sharedWords.map(stripDiacritics).filter(Boolean);
  const tokens = uthmani.split(' ');
  return (
    <>
      {tokens.map((token, i) => {
        const clean = stripDiacritics(token);
        const matched = stripped.some(w => clean === w || clean.includes(w) || w.includes(clean));
        return (
          <span key={i}>
            {matched
              ? <mark className="bg-amber-200/80 dark:bg-amber-600/50 rounded px-0.5 not-italic">{token}</mark>
              : token}
            {i < tokens.length - 1 ? ' ' : ''}
          </span>
        );
      })}
    </>
  );
}

// ─── SVG Radar Chart ─────────────────────────────────────────────────────────

const RADAR_AXES = [
  { key: 'cosine',          label_en: 'Cosine',    label_ar: 'كوساين'  },
  { key: 'root_based',      label_en: 'Root',      label_ar: 'جذري'   },
  { key: 'semantic',        label_en: 'Semantic',  label_ar: 'دلالي'  },
  { key: 'concept_overlap', label_en: 'Concept',   label_ar: 'مفاهيم' },
  { key: 'grammatical',     label_en: 'Grammar',   label_ar: 'نحوي'   },
  { key: 'jaccard',         label_en: 'Jaccard',   label_ar: 'جاكارد' },
] as const;

function ScoreRadar({ scores, size = 80, language }: {
  scores: SimilarityScores;
  size?: number;
  language: 'ar' | 'en';
}) {
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2 - 10;
  const n = RADAR_AXES.length;

  const toXY = (i: number, val: number) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    const r = maxR * Math.max(0, Math.min(1, val));
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  };

  const polygon = RADAR_AXES.map((ax, i) => toXY(i, (scores as unknown as Record<string, number>)[ax.key] ?? 0));
  const pointsStr = polygon.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');

  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
      {/* Grid */}
      {gridLevels.map(level => {
        const pts = RADAR_AXES.map((_, i) => toXY(i, level));
        return (
          <polygon
            key={level}
            points={pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="0.5"
          />
        );
      })}
      {/* Axis spokes */}
      {RADAR_AXES.map((_, i) => {
        const { x, y } = toXY(i, 1);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#e5e7eb" strokeWidth="0.5" />;
      })}
      {/* Filled polygon */}
      <polygon
        points={pointsStr}
        fill="rgba(79,70,229,0.15)"
        stroke="rgb(79,70,229)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      {/* Axis labels */}
      {RADAR_AXES.map((ax, i) => {
        const angle = (2 * Math.PI * i) / n - Math.PI / 2;
        const labelR = maxR + 8;
        const lx = cx + labelR * Math.cos(angle);
        const ly = cy + labelR * Math.sin(angle);
        return (
          <text
            key={ax.key}
            x={lx}
            y={ly}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={7}
            fill="#9ca3af"
          >
            {language === 'ar' ? ax.label_ar : ax.label_en}
          </text>
        );
      })}
    </svg>
  );
}

// ─── Constellation (SVG radial graph) ────────────────────────────────────────

interface ConstellationProps {
  sourceRef: string;
  matches: FusedMatch[];
  selectedKey: string | null;
  onSelect: (key: string) => void;
  language: 'ar' | 'en';
}

function ConstellationView({ sourceRef, matches, selectedKey, onSelect, language }: ConstellationProps) {
  const W = 600;
  const H = 500;
  const cx = W / 2;
  const cy = H / 2;
  const MIN_R = 70;
  const MAX_R = 210;
  const [hover, setHover] = useState<string | null>(null);

  const nodes = useMemo(() => {
    const top = matches.slice(0, 30);
    return top.map((m, i) => {
      const score = m.rrf_score > 0 ? m.rrf_score : m.scores.combined;
      const maxScore = Math.max(...top.map(x => x.rrf_score || x.scores.combined), 0.01);
      const normScore = Math.min(1, score / maxScore);
      const r = MIN_R + (1 - normScore) * (MAX_R - MIN_R);
      const angle = (2 * Math.PI * i) / top.length - Math.PI / 2;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      const fill = CONN_FILL[m.connection_type] ?? '#6b7280';
      const radius = 6 + normScore * 12;
      const key = `${m.sura_no}:${m.aya_no}`;
      return { m, x, y, fill, radius, key, score: normScore };
    });
  }, [matches, cx, cy]);

  return (
    <div className="overflow-auto rounded-2xl border border-gray-200 bg-gray-950 relative">
      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        style={{ maxHeight: 500 }}
      >
        {/* Background stars */}
        {Array.from({ length: 60 }, (_, i) => (
          <circle
            key={`star-${i}`}
            cx={Math.sin(i * 137.5) * W * 0.5 + W / 2}
            cy={Math.cos(i * 137.5) * H * 0.5 + H / 2}
            r={Math.sin(i) * 0.8 + 0.4}
            fill="white"
            opacity={0.15 + Math.abs(Math.sin(i * 7)) * 0.25}
          />
        ))}

        {/* Radial grid rings */}
        {[MIN_R, MIN_R + (MAX_R - MIN_R) / 3, MIN_R + (MAX_R - MIN_R) * 2 / 3, MAX_R].map((r, i) => (
          <circle key={r} cx={cx} cy={cy} r={r} fill="none" stroke="white" strokeOpacity={0.04 + i * 0.02} strokeWidth={1} strokeDasharray="4 6" />
        ))}

        {/* Edges */}
        {nodes.map(({ m, x, y, key, score }) => (
          <line
            key={`edge-${key}`}
            x1={cx} y1={cy} x2={x} y2={y}
            stroke={CONN_FILL[m.connection_type] ?? '#6b7280'}
            strokeWidth={0.5 + score * 2}
            strokeOpacity={selectedKey === key ? 0.8 : hover === key ? 0.6 : 0.25}
            strokeLinecap="round"
          />
        ))}

        {/* Verse nodes */}
        {nodes.map(({ m, x, y, fill, radius, key, score }) => {
          const isSelected = selectedKey === key;
          const isHovered = hover === key;
          return (
            <g
              key={key}
              onClick={() => onSelect(key)}
              onMouseEnter={() => setHover(key)}
              onMouseLeave={() => setHover(null)}
              style={{ cursor: 'pointer' }}
            >
              {/* Glow */}
              {(isSelected || isHovered) && (
                <circle cx={x} cy={y} r={radius + 8} fill={fill} opacity={0.15} />
              )}
              <circle
                cx={x} cy={y} r={radius}
                fill={fill}
                stroke={isSelected ? 'white' : 'rgba(255,255,255,0.3)'}
                strokeWidth={isSelected ? 2.5 : 1}
                opacity={isSelected ? 1 : 0.75 + score * 0.25}
              />
              {/* Reference label */}
              <text x={x} y={y + radius + 10} textAnchor="middle" fontSize={8} fill="rgba(255,255,255,0.7)">
                {m.reference}
              </text>
            </g>
          );
        })}

        {/* Source node */}
        <circle cx={cx} cy={cy} r={22} fill="#10b981" stroke="white" strokeWidth={2.5} />
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" fontSize={9} fontWeight="bold" fill="white">
          {sourceRef}
        </text>

        {/* Hover tooltip */}
        {hover && (() => {
          const node = nodes.find(n => n.key === hover);
          if (!node) return null;
          const { m, x, y } = node;
          const tooltipX = Math.min(x, W - 120);
          const tooltipY = y < 60 ? y + 25 : y - 45;
          const name = language === 'ar' ? m.sura_name_ar : m.sura_name_en;
          return (
            <g>
              <rect x={tooltipX - 60} y={tooltipY} width={120} height={32} rx={6} fill="rgba(0,0,0,0.85)" />
              <text x={tooltipX} y={tooltipY + 12} textAnchor="middle" fontSize={9} fill="white" fontWeight="bold">{m.reference}</text>
              <text x={tooltipX} y={tooltipY + 24} textAnchor="middle" fontSize={8} fill="rgba(255,255,255,0.7)">{name}</text>
            </g>
          );
        })()}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-1.5 max-w-48">
        {Object.entries(CONN_FILL).slice(0, 5).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-[9px] text-white/60">
              {language === 'ar' ? CONN_STYLES[type]?.label_ar : CONN_STYLES[type]?.label_en}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Breadcrumb trail ─────────────────────────────────────────────────────────

function ExplorationBreadcrumb({
  history,
  onJump,
  language,
}: {
  history: HistoryEntry[];
  onJump: (idx: number) => void;
  language: 'ar' | 'en';
}) {
  if (history.length < 2) return null;
  return (
    <div className="flex items-center gap-1 flex-wrap text-sm mb-3 p-2 bg-gray-50 rounded-lg border border-gray-200">
      <span className="text-xs text-gray-400 mr-1">{language === 'ar' ? 'المسار:' : 'Path:'}</span>
      {history.map((h, i) => (
        <span key={i} className="flex items-center gap-1">
          <button
            onClick={() => onJump(i)}
            className={clsx(
              'px-2 py-0.5 rounded text-xs font-mono transition-colors',
              i === history.length - 1
                ? 'bg-emerald-100 text-emerald-700 font-semibold'
                : 'bg-white border border-gray-200 text-gray-600 hover:text-primary-600 hover:border-primary-300'
            )}
          >
            {h.sura}:{h.aya}
          </button>
          {i < history.length - 1 && <ChevronRight className="w-3 h-3 text-gray-300" />}
        </span>
      ))}
    </div>
  );
}

// ─── Score pill ───────────────────────────────────────────────────────────────

function ScorePill({ score, large = false }: { score: number; large?: boolean }) {
  const pct = Math.round(score * 100);
  const colorClass = pct >= 70 ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
    : pct >= 45 ? 'bg-amber-100 text-amber-700 border-amber-200'
    : 'bg-gray-100 text-gray-600 border-gray-200';
  return (
    <span className={clsx('border rounded-full font-bold tabular-nums', colorClass,
      large ? 'text-lg px-3 py-1' : 'text-xs px-2 py-0.5')}>
      {pct}%
    </span>
  );
}

// ─── Match card ───────────────────────────────────────────────────────────────

function HybridMatchCard({
  match,
  rank,
  isExpanded,
  isSelected,
  onToggle,
  onExplore,
  language,
}: {
  match: FusedMatch;
  rank: number;
  isExpanded: boolean;
  isSelected: boolean;
  onToggle: () => void;
  onExplore: () => void;
  language: 'ar' | 'en';
}) {
  const isAr = language === 'ar';
  const connStyle = CONN_STYLES[match.connection_type] ?? CONN_FALLBACK;
  const ConnIcon = connStyle.icon;

  return (
    <div
      className={clsx(
        'rounded-2xl border overflow-hidden transition-all',
        isSelected
          ? 'ring-2 ring-emerald-400 border-emerald-300 shadow-lg shadow-emerald-100'
          : isExpanded
          ? 'border-primary-200 shadow-md'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm',
      )}
    >
      {/* Card header — always visible */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50/80 transition-colors"
        onClick={onToggle}
      >
        <div className={clsx('flex items-start gap-3', isAr && 'flex-row-reverse')}>
          {/* Rank badge */}
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 mt-0.5">
            {rank}
          </div>

          <div className="flex-1 min-w-0">
            {/* Reference + badges */}
            <div className={clsx('flex items-center gap-2 flex-wrap mb-2', isAr && 'flex-row-reverse')}>
              <Link
                to={`/quran/${match.sura_no}#${match.aya_no}`}
                className="font-bold text-primary-700 hover:underline font-mono"
                onClick={e => e.stopPropagation()}
              >
                {match.reference}
              </Link>
              <span className={clsx('inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border',
                connStyle.bg, connStyle.color, connStyle.border)}>
                <ConnIcon className="w-3 h-3" />
                {isAr ? connStyle.label_ar : connStyle.label_en}
              </span>
              {match.primary_theme && (
                <span className="text-xs px-2 py-0.5 rounded bg-primary-50 text-primary-700 border border-primary-200">
                  {match.primary_theme_ar && isAr ? match.primary_theme_ar : match.primary_theme}
                </span>
              )}
            </div>
            {/* Surah name */}
            <div className={clsx('text-sm text-gray-500', isAr && 'font-arabic text-right')}>
              {isAr ? match.sura_name_ar : match.sura_name_en}
            </div>
          </div>

          {/* Score + chevron */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <ScorePill score={match.rrf_score > 0 ? match.rrf_score : match.scores.combined} large />
            {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
          </div>
        </div>
      </div>

      {/* Arabic verse text (always visible, with shared word highlights) */}
      <div
        className="px-4 pb-3 text-right leading-loose text-gray-800"
        dir="rtl"
      >
        <p className="font-arabic text-xl">
          {highlightSharedWords(match.text_uthmani, match.shared_words ?? [])}
        </p>
        {match.shared_words?.length > 0 && (
          <p className="text-[10px] text-amber-600 mt-1">
            {language === 'ar' ? 'الكلمات المضيئة مشتركة مع الآية المصدر' : 'Highlighted words are shared with the source verse'}
          </p>
        )}
      </div>

      {/* Expanded detail */}
      {isExpanded && (
        <div className="border-t border-gray-100 bg-gradient-to-b from-gray-50 to-white p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Score radar */}
            <div className="flex flex-col items-center gap-1">
              <p className="text-xs text-gray-400 font-medium">{isAr ? 'ملف التشابه' : 'Similarity profile'}</p>
              <ScoreRadar scores={match.scores} size={120} language={language} />
            </div>

            {/* Score breakdown bars */}
            <div className="space-y-2">
              {RADAR_AXES.map(({ key, label_en, label_ar }) => {
                const val = (match.scores as unknown as Record<string, number>)[key] ?? 0;
                const pct = Math.round(val * 100);
                return (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-500 w-20 truncate flex-shrink-0">
                      {isAr ? label_ar : label_en}
                    </span>
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-indigo-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400 w-7 text-right tabular-nums">{pct}%</span>
                  </div>
                );
              })}
              {/* RRF hybrid score */}
              {match.rrf_score > 0 && (
                <div className="flex items-center gap-2 pt-1 border-t border-gray-100">
                  <span className="text-[10px] font-semibold text-emerald-600 w-20 flex-shrink-0">
                    {isAr ? 'هجين' : 'Hybrid RRF'}
                  </span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-emerald-500"
                      style={{ width: `${Math.round(Math.min(1, match.rrf_score * 15) * 100)}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-semibold text-emerald-600 w-7 text-right tabular-nums">
                    {match.rrf_score.toFixed(3)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Shared roots + concepts */}
          {(match.shared_roots?.length > 0 || match.shared_concepts?.length > 0) && (
            <div className={clsx('grid gap-3', match.shared_roots?.length > 0 && match.shared_concepts?.length > 0 ? 'grid-cols-2' : 'grid-cols-1')}>
              {match.shared_roots?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-400 mb-1.5">
                    {isAr ? 'الجذور المشتركة' : 'Shared Roots'}
                  </p>
                  <div className="flex flex-wrap gap-1" dir="rtl">
                    {match.shared_roots.slice(0, 8).map((r, i) => (
                      <span key={i} className="text-xs bg-teal-50 text-teal-700 border border-teal-100 px-2 py-0.5 rounded font-arabic">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {match.shared_concepts?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-400 mb-1.5">
                    {isAr ? 'المفاهيم المشتركة' : 'Shared Concepts'}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {match.shared_concepts.slice(0, 6).map((c, i) => (
                      <span key={i} className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Similarity explanation */}
          {(match.similarity_explanation_ar || match.similarity_explanation_en) && (
            <div
              className="text-sm text-gray-600 bg-white rounded-xl p-3 border border-gray-100 leading-relaxed"
              dir={isAr ? 'rtl' : 'ltr'}
            >
              <p className={clsx('text-xs font-medium text-gray-400 mb-1', isAr && 'font-arabic')}>
                {isAr ? 'وجه التشابه' : 'Similarity explanation'}
              </p>
              {isAr ? match.similarity_explanation_ar : match.similarity_explanation_en}
            </div>
          )}

          {/* Actions */}
          <div className={clsx('flex items-center gap-2 pt-2 border-t border-gray-100 flex-wrap', isAr && 'flex-row-reverse')}>
            <Link
              to={`/quran/${match.sura_no}#${match.aya_no}`}
              className="inline-flex items-center gap-1.5 text-xs text-primary-700 hover:text-primary-900 font-medium transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" />
              {isAr ? 'عرض في المصحف' : 'View in Mushaf'}
            </Link>
            <span className="text-gray-200">|</span>
            <button
              onClick={onExplore}
              className="inline-flex items-center gap-1.5 text-xs text-emerald-700 hover:text-emerald-900 font-medium transition-colors"
            >
              <Network className="w-3.5 h-3.5" />
              {isAr ? 'استكشف من هذه الآية' : 'Explore from here'}
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Popular verse quick picks ────────────────────────────────────────────────

const POPULAR_VERSES = [
  { sura: 2,   aya: 255, label_ar: 'آية الكرسي',      label_en: 'Ayat Al-Kursi'  },
  { sura: 1,   aya: 1,   label_ar: 'الفاتحة',          label_en: 'Al-Fatiha'      },
  { sura: 13,  aya: 28,  label_ar: 'ألا بذكر الله',    label_en: 'Hearts at Rest' },
  { sura: 94,  aya: 5,   label_ar: 'مع العسر يسراً',   label_en: 'With Ease'      },
  { sura: 39,  aya: 53,  label_ar: 'لا تقنطوا',        label_en: 'No Despair'     },
  { sura: 2,   aya: 286, label_ar: 'لا يكلّف الله',    label_en: 'No Burden'      },
  { sura: 112, aya: 1,   label_ar: 'الإخلاص',          label_en: 'Al-Ikhlas'      },
  { sura: 55,  aya: 13,  label_ar: 'فبأي آلاء',        label_en: 'Ar-Rahman'      },
];

// ─── Main component ───────────────────────────────────────────────────────────

export function SimilarityPage() {
  const { language } = useLanguageStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const isAr = language === 'ar';

  // Search state
  const [query, setQuery] = useState(searchParams.get('ref') || '');
  const [loading, setLoading] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<SimilarityError | null>(null);

  // Algorithm + view
  const [algorithm, setAlgorithm] = useState<AlgorithmMode>('hybrid');
  const [viewMode, setViewMode] = useState<ViewMode>('list');

  // Data from both endpoints
  const [advancedData, setAdvancedData] = useState<import('../lib/api').AdvancedSimilarityResponse | null>(null);
  const [semanticMatches, setSemanticMatches] = useState<import('../lib/api').SemanticMatch[]>([]);

  // Exploration chain
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  // UI
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [minScore, setMinScore] = useState(0.2);
  const [showFilters, setShowFilters] = useState(false);
  const [excludeSameSura, setExcludeSameSura] = useState(false);

  // Resolve verse text to reference via backend API
  const resolveVerseText = useCallback(async (text: string): Promise<{ sura: number; aya: number } | null> => {
    setResolving(true);
    try {
      const r = await api.get<{ ok: boolean; data?: { best_match?: { surah: number; ayah: number; match_type: string }; decision: string; message_en?: string; message_ar?: string }; error?: { message: string; message_ar: string } }>('/quran/resolve', { params: { text } });
      if (r.data.ok && r.data.data?.best_match) {
        return { sura: r.data.data.best_match.surah, aya: r.data.data.best_match.ayah };
      }
      setError({ message: r.data.data?.message_en || 'Verse not found', message_ar: r.data.data?.message_ar || 'لم يُعثر على الآية' });
      return null;
    } catch {
      setError({ message: 'Could not resolve verse text', message_ar: 'تعذّر تحديد الآية. جرّب إدخال الرقم مباشرة مثل 2:255' });
      return null;
    } finally {
      setResolving(false);
    }
  }, []);

  const loadSimilarVerses = useCallback(async (sura: number, aya: number, entry?: HistoryEntry) => {
    setLoading(true);
    setError(null);
    setExpandedIdx(null);
    setSelectedKey(null);
    setAdvancedData(null);
    setSemanticMatches([]);

    if (entry) {
      setHistory(prev => {
        const cut = prev.findIndex(h => h.sura === sura && h.aya === aya);
        if (cut >= 0) return prev.slice(0, cut + 1);
        return [...prev, entry];
      });
    }

    setSearchParams({ ref: `${sura}:${aya}` });

    try {
      const [adv, sem] = await Promise.allSettled([
        quranApi.getAdvancedSimilarity(sura, aya, {
          top_k: 60,
          min_score: 0.05,
          exclude_same_sura: excludeSameSura,
        }),
        quranApi.findSimilarVerses(sura, aya, { top_k: 60, exclude_same_sura: excludeSameSura }),
      ]);

      const advRes = adv.status === 'fulfilled' ? adv.value.data : null;
      const semRes = sem.status === 'fulfilled' ? sem.value.data : null;

      setAdvancedData(advRes);
      setSemanticMatches(semRes?.similar_verses ?? []);
    } catch (err) {
      setError(parseAPIError(err) as SimilarityError);
    } finally {
      setLoading(false);
    }
  }, [excludeSameSura, setSearchParams]);

  // ── Fused match list (computed from algorithm) ──────────────────────────────
  const fusedMatches = useMemo<FusedMatch[]>(() => {
    if (!advancedData && !semanticMatches.length) return [];

    const advList = advancedData?.matches ?? [];

    if (algorithm === 'lexical') {
      return advList
        .filter(m => m.scores.combined >= minScore)
        .map(m => ({ ...m, rrf_score: 0, semantic_score: 0 }))
        .sort((a, b) => b.scores.combined - a.scores.combined);
    }

    if (algorithm === 'root') {
      return advList
        .filter(m => m.scores.root_based >= minScore * 0.5)
        .map(m => ({ ...m, rrf_score: 0, semantic_score: 0 }))
        .sort((a, b) => b.scores.root_based - a.scores.root_based);
    }

    if (algorithm === 'semantic') {
      // Use semantic matches, merge metadata from advanced where available
      const advMap = new Map(advList.map(m => [`${m.sura_no}:${m.aya_no}`, m]));
      return semanticMatches
        .filter(m => m.semantic_score >= minScore * 0.5)
        .map(m => {
          const adv = advMap.get(`${m.sura_no}:${m.aya_no}`);
          const base: FusedMatch = {
            verse_id: m.verse_id,
            sura_no: m.sura_no,
            sura_name_ar: m.sura_name_ar,
            sura_name_en: m.sura_name_en,
            aya_no: m.aya_no,
            text_uthmani: m.text_uthmani,
            text_imlaei: m.text_imlaei,
            reference: m.reference,
            scores: adv?.scores ?? {
              jaccard: 0, cosine: 0, concept_overlap: 0,
              grammatical: 0, semantic: m.semantic_score,
              root_based: 0, combined: m.semantic_score,
            },
            connection_type: m.connection_type ?? adv?.connection_type ?? 'semantic',
            connection_strength: adv?.connection_strength ?? (m.semantic_score >= 0.6 ? 'strong' : 'moderate'),
            shared_words: adv?.shared_words ?? [],
            shared_roots: adv?.shared_roots ?? [],
            shared_concepts: [...(m.shared_concepts ?? []), ...(adv?.shared_concepts ?? [])],
            shared_themes: [...(m.themes ?? []), ...(adv?.shared_themes ?? [])],
            primary_theme: adv?.primary_theme ?? m.themes?.[0] ?? '',
            primary_theme_ar: adv?.primary_theme_ar ?? '',
            theme_color: adv?.theme_color ?? '#6b7280',
            sentence_structure: adv?.sentence_structure ?? '',
            sentence_structure_ar: adv?.sentence_structure_ar ?? '',
            similarity_explanation_ar: adv?.similarity_explanation_ar ?? '',
            similarity_explanation_en: adv?.similarity_explanation_en ?? '',
            rrf_score: 0,
            semantic_score: m.semantic_score,
          };
          return base;
        })
        .sort((a, b) => b.semantic_score - a.semantic_score);
    }

    // ── HYBRID: Reciprocal Rank Fusion ──────────────────────────────────────
    const advRanked = [...advList].sort((a, b) => b.scores.combined - a.scores.combined)
      .map(m => ({ key: `${m.sura_no}:${m.aya_no}` }));
    const semRanked = [...semanticMatches].sort((a, b) => b.semantic_score - a.semantic_score)
      .map(m => ({ key: `${m.sura_no}:${m.aya_no}` }));

    const rrfScores = reciprocalRankFusion([advRanked, semRanked]);

    // Build a universe of all verse keys
    const allKeys = new Set([...advRanked.map(x => x.key), ...semRanked.map(x => x.key)]);
    const advMap = new Map(advList.map(m => [`${m.sura_no}:${m.aya_no}`, m]));
    const semMap = new Map(semanticMatches.map(m => [`${m.sura_no}:${m.aya_no}`, m]));

    const fused: FusedMatch[] = [];
    allKeys.forEach(key => {
      const rrf = rrfScores.get(key) ?? 0;
      const adv = advMap.get(key);
      const sem = semMap.get(key);
      const semanticScore = sem?.semantic_score ?? 0;

      if (!adv && !sem) return;

      // Approximate combined score from RRF rank
      const approxCombined = Math.min(1, rrf * 15); // scale to 0-1 range
      if (approxCombined < minScore * 0.4) return;

      fused.push({
        verse_id: adv?.verse_id ?? sem?.verse_id ?? 0,
        sura_no: adv?.sura_no ?? sem!.sura_no,
        sura_name_ar: adv?.sura_name_ar ?? sem?.sura_name_ar ?? '',
        sura_name_en: adv?.sura_name_en ?? sem?.sura_name_en ?? '',
        aya_no: adv?.aya_no ?? sem!.aya_no,
        text_uthmani: adv?.text_uthmani ?? sem?.text_uthmani ?? '',
        text_imlaei: adv?.text_imlaei ?? sem?.text_imlaei ?? '',
        reference: adv?.reference ?? sem?.reference ?? key,
        scores: adv?.scores ?? {
          jaccard: 0, cosine: 0, concept_overlap: 0,
          grammatical: 0, semantic: semanticScore,
          root_based: 0, combined: semanticScore,
        },
        connection_type: adv?.connection_type ?? sem?.connection_type ?? 'semantic',
        connection_strength: adv?.connection_strength ?? (semanticScore >= 0.6 ? 'strong' : 'moderate'),
        shared_words: adv?.shared_words ?? [],
        shared_roots: adv?.shared_roots ?? [],
        shared_concepts: [
          ...(adv?.shared_concepts ?? []),
          ...(sem?.shared_concepts ?? []),
        ].filter((v, i, a) => a.indexOf(v) === i),
        shared_themes: [
          ...(adv?.shared_themes ?? []),
          ...(sem?.themes ?? []),
        ].filter((v, i, a) => a.indexOf(v) === i),
        primary_theme: adv?.primary_theme ?? sem?.themes?.[0] ?? '',
        primary_theme_ar: adv?.primary_theme_ar ?? '',
        theme_color: adv?.theme_color ?? '#6b7280',
        sentence_structure: adv?.sentence_structure ?? '',
        sentence_structure_ar: adv?.sentence_structure_ar ?? '',
        similarity_explanation_ar: adv?.similarity_explanation_ar ?? '',
        similarity_explanation_en: adv?.similarity_explanation_en ?? '',
        rrf_score: rrf,
        semantic_score: semanticScore,
      });
    });

    return fused.sort((a, b) => b.rrf_score - a.rrf_score);
  }, [advancedData, semanticMatches, algorithm, minScore]);

  // ── Search handler ──────────────────────────────────────────────────────────

  const handleSearch = useCallback(async (sura?: number, aya?: number) => {
    if (sura && aya) {
      const entry: HistoryEntry = {
        sura, aya,
        nameAr: advancedData?.source_verse.sura_name_ar ?? '',
        nameEn: advancedData?.source_verse.sura_name_en ?? '',
      };
      await loadSimilarVerses(sura, aya, entry);
      return;
    }
    if (!query.trim()) return;
    setError(null);
    const parsed = parseInput(query);
    if (!parsed.isTextSearch) {
      const entry: HistoryEntry = {
        sura: parsed.sura, aya: parsed.aya, nameAr: '', nameEn: '',
      };
      setHistory([entry]);
      await loadSimilarVerses(parsed.sura, parsed.aya, entry);
    } else {
      const resolved = await resolveVerseText(parsed.text);
      if (resolved) {
        setQuery(`${resolved.sura}:${resolved.aya}`);
        const entry: HistoryEntry = { sura: resolved.sura, aya: resolved.aya, nameAr: '', nameEn: '' };
        setHistory([entry]);
        await loadSimilarVerses(resolved.sura, resolved.aya, entry);
      }
    }
  }, [query, loadSimilarVerses, resolveVerseText, advancedData]);

  const handleExploreFrom = useCallback((match: FusedMatch) => {
    const entry: HistoryEntry = {
      sura: match.sura_no,
      aya: match.aya_no,
      nameAr: match.sura_name_ar,
      nameEn: match.sura_name_en,
    };
    setQuery(`${match.sura_no}:${match.aya_no}`);
    loadSimilarVerses(match.sura_no, match.aya_no, entry);
  }, [loadSimilarVerses]);

  const handleBreadcrumbJump = useCallback((idx: number) => {
    const h = history[idx];
    if (!h) return;
    setHistory(prev => prev.slice(0, idx + 1));
    setQuery(`${h.sura}:${h.aya}`);
    loadSimilarVerses(h.sura, h.aya);
  }, [history, loadSimilarVerses]);

  // Load from URL on mount
  const didMount = useRef(false);
  useEffect(() => {
    if (didMount.current) return;
    didMount.current = true;
    const ref = searchParams.get('ref');
    if (ref) {
      const p = parseInput(ref);
      if (!p.isTextSearch) {
        setQuery(ref);
        const entry: HistoryEntry = { sura: p.sura, aya: p.aya, nameAr: '', nameEn: '' };
        setHistory([entry]);
        loadSimilarVerses(p.sura, p.aya, entry);
      }
    }
  }, [searchParams, loadSimilarVerses]);

  // Reload on filter change when data is present
  const prevExclude = useRef(excludeSameSura);
  useEffect(() => {
    if (prevExclude.current === excludeSameSura) return;
    prevExclude.current = excludeSameSura;
    const src = advancedData?.source_verse;
    if (src) loadSimilarVerses(src.sura_no, src.aya_no);
  }, [excludeSameSura, advancedData, loadSimilarVerses]);

  const isSearching = loading || resolving;
  const sourceVerse = advancedData?.source_verse;
  const hasResults = fusedMatches.length > 0;

  const selectedMatch = selectedKey
    ? fusedMatches.find(m => `${m.sura_no}:${m.aya_no}` === selectedKey)
    : null;

  // Theme distribution (from advanced data)
  const themeDistrib = advancedData?.theme_distribution ?? {};

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isAr ? 'rtl' : 'ltr'}>

      {/* ── Page header ────────────────────────────────────────────────────── */}
      <div className="mb-8">
        <div className={clsx('flex items-start gap-4', isAr && 'flex-row-reverse')}>
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg">
            <Network className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={clsx('text-3xl font-bold text-gray-900', isAr && 'font-arabic')}>
              {isAr ? 'صلة الآيات' : 'Verse Connections'}
            </h1>
            <p className={clsx('text-gray-500 mt-1', isAr && 'font-arabic')}>
              {isAr
                ? 'محرك هجين: دمج البحث المتجهي والمعجمي عبر RRF — النهج الأمثل في أبحاث NLP العربية'
                : 'Hybrid engine: vector embeddings + lexical/root signals fused via Reciprocal Rank Fusion (RRF) — state of the art in Arabic NLP research'}
            </p>
          </div>
        </div>
      </div>

      {/* ── Search card ────────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
        {/* Search row */}
        <div className={clsx('flex gap-3 mb-5', isAr && 'flex-row-reverse')}>
          <div className="flex-1 relative">
            <Search className={clsx(
              'absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400',
              isAr ? 'right-3' : 'left-3',
            )} />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !isSearching && handleSearch()}
              placeholder={isAr
                ? 'أدخل المرجع (مثال: 2:255) أو اكتب نص الآية'
                : 'Enter reference (e.g. 2:255) or paste verse text'}
              dir={isAr ? 'rtl' : 'ltr'}
              className={clsx(
                'w-full py-3 border border-gray-300 rounded-xl text-base',
                'focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-shadow',
                isAr ? 'pr-10 pl-4' : 'pl-10 pr-4',
              )}
              disabled={isSearching}
            />
          </div>
          <button
            onClick={() => handleSearch()}
            disabled={!query.trim() || isSearching}
            className="btn btn-primary px-6 flex items-center gap-2 rounded-xl min-w-[140px] justify-center"
          >
            {isSearching
              ? <><Loader2 className="w-4 h-4 animate-spin" />{isAr ? 'جارٍ...' : 'Searching...'}</>
              : <><Search className="w-4 h-4" />{isAr ? 'بحث' : 'Search'}</>}
          </button>
        </div>

        {/* Algorithm mode selector */}
        <div className="mb-4">
          <p className={clsx('text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2', isAr && 'font-arabic text-right')}>
            {isAr ? 'خوارزمية البحث' : 'Search Algorithm'}
          </p>
          <div className={clsx('flex flex-wrap gap-2', isAr && 'flex-row-reverse')}>
            {ALGORITHM_MODES.map(mode => {
              const Icon = mode.icon;
              const active = algorithm === mode.id;
              return (
                <button
                  key={mode.id}
                  onClick={() => setAlgorithm(mode.id)}
                  title={isAr ? mode.desc_ar : mode.desc_en}
                  className={clsx(
                    'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all',
                    active
                      ? [mode.bg, mode.color, mode.border, 'shadow-sm']
                      : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100',
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {isAr ? mode.label_ar : mode.label_en}
                  {mode.id === 'hybrid' && (
                    <span className="text-[9px] font-bold uppercase bg-emerald-600 text-white rounded px-1">★</span>
                  )}
                </button>
              );
            })}
          </div>
          <p className="text-[11px] text-gray-400 mt-1.5" dir={isAr ? 'rtl' : 'ltr'}>
            {isAr
              ? ALGORITHM_MODES.find(m => m.id === algorithm)?.desc_ar
              : ALGORITHM_MODES.find(m => m.id === algorithm)?.desc_en}
          </p>
        </div>

        {/* Popular verses */}
        <div>
          <p className={clsx('text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2', isAr && 'font-arabic text-right')}>
            {isAr ? 'آيات مقترحة' : 'Quick picks'}
          </p>
          <div className={clsx('flex flex-wrap gap-2', isAr && 'flex-row-reverse')}>
            {POPULAR_VERSES.map(v => (
              <button
                key={`${v.sura}:${v.aya}`}
                disabled={isSearching}
                onClick={() => {
                  setQuery(`${v.sura}:${v.aya}`);
                  const entry: HistoryEntry = { sura: v.sura, aya: v.aya, nameAr: v.label_ar, nameEn: v.label_en };
                  setHistory([entry]);
                  loadSimilarVerses(v.sura, v.aya, entry);
                }}
                className="px-3 py-1.5 bg-gray-100 hover:bg-primary-50 hover:text-primary-700 disabled:opacity-50 rounded-lg text-xs transition-colors"
              >
                <span className="font-mono text-gray-500 me-1.5">{v.sura}:{v.aya}</span>
                <span className={clsx(isAr && 'font-arabic')}>{isAr ? v.label_ar : v.label_en}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Error ─────────────────────────────────────────────────────────── */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-red-800 font-medium" dir={isAr ? 'rtl' : 'ltr'}>
              {isAr ? error.message_ar : error.message}
            </p>
            <p className="text-red-600 text-xs mt-1" dir={isAr ? 'rtl' : 'ltr'}>
              {isAr ? 'صيغ مقبولة: 2:255 أو البقرة 255 أو نص الآية' : 'Try: 2:255, Al-Baqarah 255, or paste verse text'}
            </p>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Loading ────────────────────────────────────────────────────────── */}
      {isSearching && (
        <div className="text-center py-16">
          <div className="inline-flex flex-col items-center gap-3">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-primary-100 border-t-primary-600 animate-spin" />
              <Network className="w-6 h-6 text-primary-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            </div>
            <p className={clsx('text-gray-500 text-sm', isAr && 'font-arabic')}>
              {algorithm === 'hybrid'
                ? (isAr ? 'تشغيل محرك RRF الهجين...' : 'Running hybrid RRF engine...')
                : isAr ? 'جارٍ البحث...' : 'Searching...'}
            </p>
            {algorithm === 'hybrid' && (
              <p className="text-xs text-gray-400">
                {isAr ? 'يدمج إشارات التمثيل المتجهي مع الإشارات اللفظية' : 'Merging vector embedding + lexical signals'}
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── Results ────────────────────────────────────────────────────────── */}
      {!isSearching && hasResults && sourceVerse && (
        <div className="space-y-5">
          {/* Exploration breadcrumb */}
          <ExplorationBreadcrumb history={history} onJump={handleBreadcrumbJump} language={language} />

          {/* Source verse */}
          <div className="bg-gradient-to-br from-emerald-50 via-teal-50 to-sky-50 border border-emerald-200 rounded-2xl p-5">
            <div className={clsx('flex items-center gap-2 mb-3', isAr && 'flex-row-reverse')}>
              <BookOpen className="w-4 h-4 text-emerald-600" />
              <span className={clsx('font-semibold text-emerald-700 text-sm', isAr && 'font-arabic')}>
                {isAr ? 'الآية المصدر' : 'Source verse'}
              </span>
              <span className="font-mono text-emerald-600 text-sm">{sourceVerse.reference}</span>
              <span className={clsx('text-gray-500 text-sm', isAr && 'font-arabic')}>
                — {isAr ? sourceVerse.sura_name_ar : sourceVerse.sura_name_en}
              </span>
            </div>
            <p className="font-arabic text-2xl text-right leading-loose text-gray-900" dir="rtl">
              {sourceVerse.text_uthmani}
            </p>
            {advancedData?.source_themes && advancedData.source_themes.length > 0 && (
              <div className={clsx('flex items-center gap-2 mt-3 flex-wrap', isAr && 'flex-row-reverse')}>
                <Tag className="w-3.5 h-3.5 text-emerald-500" />
                {advancedData.source_themes.map(t => (
                  <span key={t} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Stats + controls bar */}
          <div className={clsx(
            'flex items-center justify-between flex-wrap gap-3',
            'bg-gray-50 border border-gray-200 rounded-xl px-4 py-3',
            isAr && 'flex-row-reverse',
          )}>
            <div className={clsx('flex items-center gap-3 text-sm', isAr && 'flex-row-reverse')}>
              <span className="font-bold text-gray-900 text-lg">{fusedMatches.length}</span>
              <span className={clsx('text-gray-500', isAr && 'font-arabic')}>
                {isAr ? 'آية مرتبطة' : 'connected verses'}
              </span>
              {algorithm === 'hybrid' && (
                <span className="inline-flex items-center gap-1 text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
                  <Cpu className="w-3 h-3" />
                  {isAr ? 'RRF هجين' : 'Hybrid RRF'}
                </span>
              )}
            </div>
            <div className={clsx('flex items-center gap-2', isAr && 'flex-row-reverse')}>
              {/* View mode toggle */}
              <div className="flex rounded-lg border border-gray-200 overflow-hidden">
                <button
                  onClick={() => setViewMode('list')}
                  className={clsx(
                    'px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5',
                    viewMode === 'list' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50',
                  )}
                >
                  <Layers className="w-3.5 h-3.5" />
                  {isAr ? 'قائمة' : 'List'}
                </button>
                <button
                  onClick={() => setViewMode('constellation')}
                  className={clsx(
                    'px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5 border-l border-gray-200',
                    viewMode === 'constellation' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50',
                  )}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {isAr ? 'كوكبة' : 'Constellation'}
                </button>
              </div>
              {/* Filters button */}
              <button
                onClick={() => setShowFilters(f => !f)}
                className={clsx(
                  'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                  showFilters ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50',
                )}
              >
                <Filter className="w-3.5 h-3.5" />
                {isAr ? 'تصفية' : 'Filter'}
              </button>
              <button
                onClick={() => sourceVerse && loadSimilarVerses(sourceVerse.sura_no, sourceVerse.aya_no)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-primary-600 hover:bg-primary-50 transition-colors border border-gray-200"
                title={isAr ? 'تحديث' : 'Refresh'}
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Filters panel */}
          {showFilters && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
              <div className={clsx('flex items-center gap-3 flex-wrap', isAr && 'flex-row-reverse')}>
                <div className="flex items-center gap-2">
                  <label className={clsx('text-xs text-gray-500', isAr && 'font-arabic')}>
                    {isAr ? `حد أدنى للتشابه: ${Math.round(minScore * 100)}%` : `Min similarity: ${Math.round(minScore * 100)}%`}
                  </label>
                  <input
                    type="range" min={0} max={0.8} step={0.05} value={minScore}
                    onChange={e => setMinScore(+e.target.value)}
                    className="w-28"
                  />
                </div>
                <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={excludeSameSura}
                    onChange={e => setExcludeSameSura(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600"
                  />
                  {isAr ? 'استبعاد نفس السورة' : 'Exclude same surah'}
                </label>
              </div>
            </div>
          )}

          {/* Theme distribution strip */}
          {Object.keys(themeDistrib).length > 0 && (
            <div className={clsx('flex items-center gap-2 flex-wrap', isAr && 'flex-row-reverse')}>
              <span className={clsx('text-xs font-medium text-gray-400', isAr && 'font-arabic')}>
                {isAr ? 'المواضيع:' : 'Themes:'}
              </span>
              {Object.entries(themeDistrib).slice(0, 8).map(([theme, count]) => (
                <span
                  key={theme}
                  className="text-xs px-2 py-1 rounded-full bg-primary-50 text-primary-600 border border-primary-100"
                >
                  {theme} <strong>({count})</strong>
                </span>
              ))}
            </div>
          )}

          {/* ── Constellation View ──────────────────────────────────────────── */}
          {viewMode === 'constellation' && (
            <div className="space-y-4">
              <ConstellationView
                sourceRef={sourceVerse.reference}
                matches={fusedMatches}
                selectedKey={selectedKey}
                onSelect={key => setSelectedKey(k => k === key ? null : key)}
                language={language}
              />
              {/* Selected verse detail panel */}
              {selectedMatch && (
                <div className="bg-white border border-emerald-200 rounded-2xl p-4 shadow-lg space-y-3">
                  <div className={clsx('flex items-start justify-between gap-3', isAr && 'flex-row-reverse')}>
                    <div>
                      <div className={clsx('flex items-center gap-2 mb-1', isAr && 'flex-row-reverse')}>
                        <span className="font-bold font-mono text-primary-700">{selectedMatch.reference}</span>
                        <ScorePill score={selectedMatch.rrf_score || selectedMatch.scores.combined} />
                      </div>
                      <p className={clsx('text-sm text-gray-500', isAr && 'font-arabic')}>
                        {isAr ? selectedMatch.sura_name_ar : selectedMatch.sura_name_en}
                      </p>
                    </div>
                    <div className={clsx('flex items-center gap-2', isAr && 'flex-row-reverse')}>
                      <Link
                        to={`/quran/${selectedMatch.sura_no}#${selectedMatch.aya_no}`}
                        className="text-xs text-primary-600 hover:underline"
                      >
                        {isAr ? 'عرض في المصحف' : 'View in Mushaf'}
                      </Link>
                      <button
                        onClick={() => handleExploreFrom(selectedMatch)}
                        className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
                      >
                        {isAr ? 'استكشف →' : 'Explore →'}
                      </button>
                    </div>
                  </div>
                  <p className="font-arabic text-xl text-right leading-loose" dir="rtl">
                    {highlightSharedWords(selectedMatch.text_uthmani, selectedMatch.shared_words ?? [])}
                  </p>
                  {selectedMatch.similarity_explanation_en && (
                    <p className="text-sm text-gray-600 italic" dir={isAr ? 'rtl' : 'ltr'}>
                      {isAr ? selectedMatch.similarity_explanation_ar : selectedMatch.similarity_explanation_en}
                    </p>
                  )}
                </div>
              )}
              {/* Constellation instructions */}
              <p className="text-center text-xs text-gray-400">
                {isAr
                  ? '• القرب من المركز = تشابه أعلى  • اللون = نوع الصلة  • انقر على أي عقدة لعرض التفاصيل'
                  : '• Proximity to center = higher similarity  • Color = connection type  • Click any node for details'}
              </p>
            </div>
          )}

          {/* ── List View ──────────────────────────────────────────────────── */}
          {viewMode === 'list' && (
            <div className="space-y-3">
              {fusedMatches.map((match, i) => {
                const key = `${match.sura_no}:${match.aya_no}`;
                return (
                  <HybridMatchCard
                    key={key}
                    match={match}
                    rank={i + 1}
                    isExpanded={expandedIdx === i}
                    isSelected={selectedKey === key}
                    onToggle={() => {
                      setExpandedIdx(idx => idx === i ? null : i);
                      setSelectedKey(key);
                    }}
                    onExplore={() => handleExploreFrom(match)}
                    language={language}
                  />
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── No results ────────────────────────────────────────────────────── */}
      {!isSearching && sourceVerse && fusedMatches.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
          <GitBranch className="w-10 h-10 mx-auto text-gray-300 mb-3" />
          <p className={clsx('text-gray-500', isAr && 'font-arabic')}>
            {isAr ? 'لم يُعثر على آيات مرتبطة بهذه المعايير' : 'No connected verses found with current settings'}
          </p>
          <button onClick={() => setMinScore(0.05)} className="mt-3 text-sm text-primary-600 hover:underline">
            {isAr ? 'خفّض الحد الأدنى للتشابه' : 'Lower the minimum similarity threshold'}
          </button>
        </div>
      )}

      {/* ── Initial empty state ────────────────────────────────────────────── */}
      {!isSearching && !sourceVerse && !error && (
        <div className="text-center py-20">
          <div className="relative inline-block mb-6">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-100 to-indigo-100 flex items-center justify-center">
              <Network className="w-10 h-10 text-primary-500" />
            </div>
            {/* Orbiting dots */}
            {[0, 1, 2, 3].map(i => (
              <div
                key={i}
                className="absolute w-3 h-3 rounded-full bg-primary-400/60"
                style={{
                  top: `${50 - 45 * Math.cos((i / 4) * 2 * Math.PI)}%`,
                  left: `${50 + 45 * Math.sin((i / 4) * 2 * Math.PI)}%`,
                  transform: 'translate(-50%,-50%)',
                }}
              />
            ))}
          </div>
          <h2 className={clsx('text-xl font-semibold text-gray-700 mb-2', isAr && 'font-arabic')}>
            {isAr ? 'اكتشف الروابط بين آيات القرآن الكريم' : 'Discover connections between Quranic verses'}
          </h2>
          <p className={clsx('text-gray-400 max-w-lg mx-auto mb-6', isAr && 'font-arabic')}>
            {isAr
              ? 'أدخل مرجع آية (مثل 2:255) أو اكتب نصاً، ثم اختر خوارزمية البحث. يوفر الوضع الهجين أعلى دقة بدمج الذكاء الاصطناعي مع التحليل اللغوي.'
              : 'Enter a verse reference (e.g. 2:255) or text, then pick an algorithm. Hybrid mode delivers highest accuracy by fusing AI embeddings with linguistic analysis.'}
          </p>

          {/* Algorithm explainer cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-2xl mx-auto text-left">
            {ALGORITHM_MODES.map(mode => {
              const Icon = mode.icon;
              return (
                <button
                  key={mode.id}
                  onClick={() => setAlgorithm(mode.id)}
                  className={clsx(
                    'p-3 rounded-xl border text-left transition-all hover:shadow-sm',
                    algorithm === mode.id
                      ? [mode.bg, mode.border]
                      : 'bg-white border-gray-200 hover:border-gray-300',
                  )}
                >
                  <div className={clsx('w-7 h-7 rounded-lg flex items-center justify-center mb-2', mode.bg)}>
                    <Icon className={clsx('w-4 h-4', mode.color)} />
                  </div>
                  <p className={clsx('text-xs font-semibold text-gray-800', isAr && 'font-arabic text-right')}>
                    {isAr ? mode.label_ar : mode.label_en}
                    {mode.id === 'hybrid' && <span className="ms-1 text-emerald-500">★</span>}
                  </p>
                  <p className={clsx('text-[10px] text-gray-400 mt-0.5 leading-tight', isAr && 'font-arabic text-right')}>
                    {isAr ? mode.desc_ar.split('—')[0] : mode.desc_en.split('—')[0]}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Bottom nav ─────────────────────────────────────────────────────── */}
      <div className="mt-12 pt-6 border-t border-gray-100">
        <div className={clsx('flex flex-wrap gap-3', isAr && 'flex-row-reverse')}>
          <Link to="/search" className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
            <Search className="w-4 h-4" />
            {isAr ? 'البحث المتقدم' : 'Advanced Search'}
          </Link>
          <Link to="/concepts" className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
            <Tag className="w-4 h-4" />
            {isAr ? 'المفاهيم' : 'Concepts'}
          </Link>
          <Link to="/themes" className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
            <Layers className="w-4 h-4" />
            {isAr ? 'المحاور' : 'Themes'}
          </Link>
        </div>
      </div>
    </div>
  );
}

export default SimilarityPage;
