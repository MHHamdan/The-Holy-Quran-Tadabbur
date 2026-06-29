/**
 * Quranic Calls Atlas — Classification Script
 *
 * Reads quranicCallsAtlas.json and applies:
 *   1. Rule-based function classification (topic signal words)
 *   2. Entity-signal classification (prophet names, groups)
 *   3. Tone heuristics (gentle / warning / honoring / etc.)
 *
 * IMPORTANT:
 *   - All output classifications remain needs_review = true
 *   - humanReviewRequired = true always
 *   - No Quran text is modified
 *   - Inferred classifications are signals, not ground truth
 *
 * Outputs:
 *   frontend/src/data/generated/quranicCallsClassified.json
 *
 * Usage:
 *   npx tsx scripts/classify-quranic-call-functions.ts
 */

import { readFileSync, writeFileSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const IN_JSON = join(ROOT, 'frontend/src/data/generated/quranicCallsAtlas.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranicCallsClassified.json');

interface QuranicCall {
  callId: string;
  surahNumber: number;
  ayahNumber: number;
  ayahReference: string;
  surahNameAr: string;
  surahNameEn: string;
  ayahTextUthmani: string;
  callText?: string;
  callPattern: string;
  caller: { callerType: string; confidence: number; reviewStatus: string; labelArabic?: string; labelEnglish?: string };
  addressee: { addresseeType: string; labelArabic: string; labelEnglish: string; confidence: number; reviewStatus: string };
  callFunction: string;
  tone: string;
  relatedTopics: string[];
  relatedEntities: string[];
  relatedStories: string[];
  relatedProphets: string[];
  evidenceReferences: unknown[];
  confidence: number;
  reviewStatus: string;
  humanReviewRequired: boolean;
  warnings: string[];
}

interface Atlas { version: string; generatedAt: string; totalCalls: number; statistics: Record<string, unknown>; calls: QuranicCall[] }

// ─── Topic-signal classification rules ───────────────────────────────────────

interface SignalRule {
  signals: string[];   // stripped Arabic words/phrases to match in ayah text
  callFunction: string;
  tone: string;
  topics: string[];
  weight: number;
}

const SIGNAL_RULES: SignalRule[] = [
  // Supplication-pattern rules (highest weight)
  { signals: ['ربنا آتنا', 'ربنا اغفر', 'ربنا تقبل', 'ربنا لا تجعل', 'ربنا هب لنا', 'ربنا آمنا', 'ربنا لا تؤاخذ', 'ربنا افتح', 'ربنا اكشف', 'ربنا بصرنا', 'ربنا لا تزغ', 'ربنا انك جامع'], callFunction: 'supplication', tone: 'gentle', topics: ['دعاء', 'تضرع'], weight: 10 },
  // Commands / obligation
  { signals: ['آمنوا', 'أقيموا الصلاة', 'آتوا الزكاة', 'اتقوا الله', 'أطيعوا الله', 'أطيعوا الرسول', 'استعينوا', 'استجيبوا', 'أنفقوا', 'جاهدوا', 'توبوا'], callFunction: 'command', tone: 'urgent', topics: ['تشريع', 'طاعة'], weight: 8 },
  // Prohibition / warning
  { signals: ['لا تتخذوا', 'لا تتبعوا', 'لا تقنطوا', 'لا تكونوا', 'لا تفسدوا', 'لا تقربوا', 'لا تأكلوا', 'لا تقولوا', 'احذروا', 'لا تكفروا'], callFunction: 'prohibition', tone: 'warning', topics: ['نهي', 'تحذير'], weight: 8 },
  // Warning / threat
  { signals: ['عذاب', 'العذاب', 'جهنم', 'النار', 'وعيد', 'خزي', 'الغضب', 'الهاوية', 'لعنة', 'أليم شديد', 'إن لم'], callFunction: 'warning', tone: 'warning', topics: ['تحذير', 'عقوبة'], weight: 7 },
  // Invitation / dawah
  { signals: ['آمنوا بالله', 'فاؤمنوا', 'ادعوا', 'ادخلوا في السلم', 'هلموا', 'تعالوا'], callFunction: 'invitation', tone: 'gentle', topics: ['دعوة', 'إيمان'], weight: 7 },
  // Comfort / reassurance
  { signals: ['لا تخف', 'لا تحزن', 'لا تخافوا', 'طمأن', 'إن الله معكم', 'إن الله مع', 'سلام عليكم', 'بشرى'], callFunction: 'comfort', tone: 'comforting', topics: ['تسلية', 'أمان'], weight: 9 },
  // Reminder / instruction about faith
  { signals: ['اذكروا', 'تذكرون', 'تتفكرون', 'أفلا', 'ألم تروا', 'ألم تعلم', 'اعتبروا'], callFunction: 'reminder', tone: 'gentle', topics: ['تذكر', 'تدبر'], weight: 6 },
  // Rhetorical question
  { signals: ['أفلا تعقلون', 'أفلا تذكرون', 'أفلا تتقون', 'أفلا تبصرون', 'هل أتاك', 'أين شركاؤكم', 'كيف كان'], callFunction: 'question', tone: 'rebuking', topics: ['توبيخ', 'تساؤل'], weight: 7 },
  // Rebuke
  { signals: ['لماذا', 'كيف تكفرون', 'وكنتم', 'أنى يؤفكون', 'سفهاء', 'ظلمتم', 'عصيتم', 'بدلتم'], callFunction: 'rebuke', tone: 'rebuking', topics: ['توبيخ', 'انتقاد'], weight: 7 },
  // Promise / glad tidings
  { signals: ['بشارة', 'أجر عظيم', 'جنات', 'فوز', 'رضوان الله', 'يدخلهم', 'يكفر', 'يغفر لهم'], callFunction: 'promise', tone: 'gentle', topics: ['بشرى', 'وعد'], weight: 6 },
  // Honoring / dignified address
  { signals: ['يا أيها النبي', 'يا أيها الرسول', 'اصطفاك', 'اجتباك', 'النبوة', 'الرسالة'], callFunction: 'instruction', tone: 'honoring', topics: ['النبوة', 'الرسالة'], weight: 9 },
  // Lament markers
  { signals: ['يا ويلتى', 'يا ويلنا', 'يا حسرة', 'يا أسفى', 'يا ليتني'], callFunction: 'lament', tone: 'warning', topics: ['حزن', 'ندم'], weight: 10 },
  // Story / dialogue
  { signals: ['قال يا', 'فقال يا', 'فقالوا يا', 'نادى', 'نادينا', 'ناداه'], callFunction: 'dialogue', tone: 'neutral', topics: ['قصص', 'حوار'], weight: 5 },
  // Mercy / forgiveness
  { signals: ['يغفر', 'اغفر لي', 'تب علينا', 'ارحمنا', 'الرحمة', 'رحيم'], callFunction: 'mercy', tone: 'gentle', topics: ['رحمة', 'مغفرة'], weight: 6 },
];

// ─── Tone overrides for specific pattern types ────────────────────────────────

const PATTERN_TONE_MAP: Record<string, string> = {
  ya_prophet_name: 'honoring',
  ya_ayyuhal:      'neutral',
  ya_lament:       'warning',
  ya_wish:         'warning',
  ya_bunayya:      'gentle',
  ya_abati:        'gentle',
  supplication:    'gentle',
};

// ─── Topic tag dictionaries ───────────────────────────────────────────────────

const SURAH_THEMES: Record<number, string[]> = {
  1:  ['فاتحة', 'دعاء'],
  2:  ['تشريع', 'تاريخ', 'عقيدة'],
  3:  ['أهل الكتاب', 'عقيدة', 'مريم'],
  4:  ['تشريع', 'أسرة'],
  5:  ['أهل الكتاب', 'تشريع'],
  6:  ['توحيد', 'رسالة'],
  7:  ['قصص الأنبياء', 'تحذير'],
  9:  ['جهاد', 'منافقون'],
  11: ['قصص الأنبياء'],
  12: ['يوسف', 'صبر'],
  18: ['قصص', 'إيمان'],
  19: ['مريم', 'زكريا', 'يحيى', 'عيسى'],
  20: ['موسى', 'قصص'],
  26: ['قصص الأنبياء'],
  27: ['داود', 'سليمان'],
  28: ['موسى', 'قصص'],
  36: ['قرآن', 'قيامة'],
  59: ['نصيحة'],
  66: ['النساء', 'تشريع'],
};

function stripDiacritics(text: string): string {
  return text.replace(/[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۤۧۨ-ۭ]/g, '');
}

function classify(call: QuranicCall): {
  callFunction: string;
  tone: string;
  relatedTopics: string[];
  method: string;
  signals: string[];
} {
  // Supplication callPattern → always supplication function
  if (call.callPattern === 'supplication' || call.callPattern === 'ya_rabbi') {
    return { callFunction: 'supplication', tone: 'gentle', relatedTopics: ['دعاء', 'تضرع'], method: 'rule_based', signals: [call.callPattern] };
  }
  if (call.callPattern === 'ya_lament' || call.callPattern === 'ya_wish') {
    return { callFunction: 'lament', tone: 'warning', relatedTopics: ['حزن', 'ندم'], method: 'rule_based', signals: [call.callPattern] };
  }

  const stripped = stripDiacritics(call.ayahTextUthmani);

  // Apply signal rules
  let bestScore = 0;
  let bestCallFunction = 'needs_review';
  let bestTone: string = PATTERN_TONE_MAP[call.callPattern] ?? 'needs_review';
  let bestTopics: string[] = SURAH_THEMES[call.surahNumber] ?? [];
  let bestMethod = 'unclassified';
  let matchedSignals: string[] = [];

  for (const rule of SIGNAL_RULES) {
    for (const signal of rule.signals) {
      if (stripped.includes(signal)) {
        const score = rule.weight;
        if (score > bestScore) {
          bestScore = score;
          bestCallFunction = rule.callFunction;
          bestTone = rule.tone;
          bestTopics = [...rule.topics, ...(SURAH_THEMES[call.surahNumber] ?? [])];
          bestMethod = 'topic_signal';
          matchedSignals = [signal];
        } else if (score === bestScore) {
          matchedSignals.push(signal);
        }
      }
    }
  }

  // Pattern tone override takes precedence on tone only if no strong signal
  if (bestMethod === 'unclassified' && PATTERN_TONE_MAP[call.callPattern]) {
    bestTone = PATTERN_TONE_MAP[call.callPattern];
  }

  // Prophet/entity signal for topic enrichment
  const relatedProphets = call.relatedProphets;
  if (relatedProphets.length > 0) {
    const prophetTopics = relatedProphets.map((p) => `قصص ${p}`);
    bestTopics = [...new Set([...bestTopics, ...prophetTopics])];
    if (bestMethod === 'unclassified') bestMethod = 'entity_signal';
  }

  return {
    callFunction: bestCallFunction,
    tone: bestTone,
    relatedTopics: [...new Set(bestTopics)].slice(0, 6),
    method: bestMethod,
    signals: matchedSignals,
  };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

console.log('Loading atlas data...');
const atlas: Atlas = JSON.parse(readFileSync(IN_JSON, 'utf-8'));
console.log(`Loaded ${atlas.calls.length} calls`);

const classifiedCalls = atlas.calls.map((call) => {
  const result = classify(call);
  return {
    ...call,
    callFunction: result.callFunction,
    tone: result.tone,
    relatedTopics: result.relatedTopics.length > 0 ? result.relatedTopics : call.relatedTopics,
    reviewStatus: 'needs_review' as const,
    humanReviewRequired: true,
    classifiedAt: new Date().toISOString(),
    classificationMethod: result.method,
    classificationSignals: result.signals,
  };
});

// Build summary
const byFunction: Record<string, number> = {};
const byTone: Record<string, number> = {};
let unclassified = 0;
let highConfidence = 0;
let lowConfidence = 0;

for (const c of classifiedCalls) {
  byFunction[c.callFunction] = (byFunction[c.callFunction] ?? 0) + 1;
  byTone[c.tone] = (byTone[c.tone] ?? 0) + 1;
  if (c.classificationMethod === 'unclassified') unclassified++;
  if (c.confidence > 0.7) highConfidence++;
  if (c.confidence <= 0.4) lowConfidence++;
}

const output = {
  version: '1.0.0-phase-y',
  classifiedAt: new Date().toISOString(),
  totalClassified: classifiedCalls.length,
  calls: classifiedCalls,
  classificationSummary: { byFunction, byTone, unclassified, highConfidence, lowConfidence },
};

writeFileSync(OUT_JSON, JSON.stringify(output, null, 2), 'utf-8');
console.log(`\n✓ Written: ${OUT_JSON}`);

console.log('\n' + '='.repeat(60));
console.log('CLASSIFICATION COMPLETE');
console.log('='.repeat(60));
console.log(`Total classified    : ${classifiedCalls.length}`);
console.log(`Unclassified        : ${unclassified}`);
console.log(`High confidence (>0.7) : ${highConfidence}`);
console.log(`Low confidence (≤0.4)  : ${lowConfidence}`);
console.log('\nBy Call Function:');
Object.entries(byFunction).sort(([,a],[,b])=>b-a).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
console.log('\nBy Tone:');
Object.entries(byTone).sort(([,a],[,b])=>b-a).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
console.log('='.repeat(60));
