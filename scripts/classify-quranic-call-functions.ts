/**
 * Quranic Calls Atlas — Classification Script (v2)
 *
 * Uses ayahTextEmlaei (standard alef/hamza forms) for signal matching
 * so signal words like "استعينوا" match the ayah text correctly.
 *
 * Coverage improved: rules tuned per addressee type + pattern type.
 * All output classifications remain: reviewStatus=needs_review, humanReviewRequired=true.
 *
 * Outputs: frontend/src/data/generated/quranicCallsClassified.json
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
  ayahTextEmlaei?: string;
  callText?: string;
  callPattern: string;
  caller: { callerType: string; labelArabic?: string; labelEnglish?: string; confidence: number; reviewStatus: string };
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

// ─── Normalised text for matching ─────────────────────────────────────────────
// Use emlaei text (standard alef/hamza) so signal word lists work correctly.

function matchText(call: QuranicCall): string {
  return (call.ayahTextEmlaei ?? call.ayahTextUthmani ?? '').replace(/[ًٌٍَُِّْٰ]/g, '');
}

// ─── Signal rules ─────────────────────────────────────────────────────────────

interface Rule {
  signals: string[];
  fn: string;
  tone: string;
  topics: string[];
  weight: number;
}

const RULES: Rule[] = [
  // ── Supplication (in text) ───────────────────────────────────────────────────
  { signals: ['ربنا آتنا','ربنا اغفر','ربنا تقبل','ربنا لا تجعل','ربنا هب لنا',
               'ربنا لا تؤاخذ','ربنا افتح','ربنا لا تزغ','ربنا إنك جامع',
               'ربنا آمنا','ربنا ظلمنا','اغفر لي','ارحمني','تب علي',
               'ارزقنا','ألقي إلي','رب أنزلني'],
    fn: 'supplication', tone: 'gentle', topics: ['دعاء','تضرع','مناجاة'], weight: 10 },

  // ── Prohibition / Negation commands ─────────────────────────────────────────
  { signals: ['لا تتخذوا','لا تتبعوا','لا تقنطوا','لا تكونوا','لا تفسدوا',
               'لا تقربوا','لا تأكلوا','لا تقولوا','لا تطيعوا','لا تكفروا',
               'لا تنافقوا','لا تخونوا','لا تجعلوا','لا تبطلوا','لا تتولوا',
               'لا تحبطوا','لا تمشوا','لا تسرفوا','لا تؤمنوا','لا تنهروا',
               'لا تشركوا','لا تجادلوا','لا توالوا','لا تلبسوا',
               'لا تغلوا','لا تعتدوا','لا تقتلوا','لا يحزن','لا يغرنك'],
    fn: 'prohibition', tone: 'urgent', topics: ['نهي','تحذير','تشريع'], weight: 9 },

  // ── Direct commands / obligations ───────────────────────────────────────────
  { signals: ['آمنوا بالله','آمنوا بالله ورسوله','اتقوا الله','اتقوا ربكم',
               'أقيموا الصلاة','آتوا الزكاة','أطيعوا الله','أطيعوا الرسول',
               'استعينوا','استجيبوا','أنفقوا','جاهدوا','توبوا','اعتصموا',
               'ادخلوا','احفظوا','استغفروا','أكملوا','اتبعوا','كونوا',
               'ادعوا','اسجدوا','اركعوا','اسمعوا','أوفوا','اعدلوا',
               'اشكروا','افعلوا ما تؤمرون','انفذوا','ابتغوا'],
    fn: 'command', tone: 'urgent', topics: ['أمر','تشريع','طاعة'], weight: 8 },

  // ── Warning / threat ─────────────────────────────────────────────────────────
  { signals: ['عذاب أليم','العذاب الشديد','النار','جهنم','الخزي','وعيد','خسارة',
               'غضب الله','سخط','فاحذروا','احذروا','وعيد شديد','العذاب الكبير',
               'خاسرون','ظالمون','كافرون','هم الفاسقون','وبال'],
    fn: 'warning', tone: 'warning', topics: ['تحذير','عقوبة','وعيد'], weight: 8 },

  // ── Comfort / reassurance ────────────────────────────────────────────────────
  { signals: ['لا تخف','لا تحزن','لا تخافوا','لا تحزنوا','طمأنينة','بشرى',
               'سلام عليكم','فلا خوف','ولا هم يحزنون','رحمة من ربك',
               'إن الله معكم','الله معنا','ولا تيأسوا','لن نضيع',
               'الله وليكم','ليس عليك','لا بأس'],
    fn: 'comfort', tone: 'comforting', topics: ['طمأنينة','رحمة','أمان'], weight: 9 },

  // ── Promise / glad tidings ───────────────────────────────────────────────────
  { signals: ['أجر عظيم','جنات تجري','فوز','رضوان الله','يكفر','يغفر لكم',
               'يدخلهم','الفوز العظيم','لهم أجر','مضاعفاً','نعيم مقيم',
               'يبشرهم','سعادة','خير وأوفر','ثواب'],
    fn: 'promise', tone: 'gentle', topics: ['وعد','بشرى','الجنة'], weight: 7 },

  // ── Invitation / dawah ───────────────────────────────────────────────────────
  { signals: ['تعالوا إلى','هلموا','أسلموا','ادخلوا في السلم','فادعوا',
               'ادعوا ربكم','تدعوا الله','فاؤمنوا','أسلم وجهك','أخلصوا'],
    fn: 'invitation', tone: 'gentle', topics: ['دعوة','إيمان','توحيد'], weight: 7 },

  // ── Reminder / reflection ────────────────────────────────────────────────────
  { signals: ['اذكروا','تذكرون','تتفكرون','تتدبرون','ألم تر','ألم تعلم',
               'ألم تروا','أفلا تعقلون','أفلا تتقون','أفلا تذكرون',
               'اعتبروا','فاعتبروا','انظروا','تأملوا','فكروا','تبصرون'],
    fn: 'reminder', tone: 'gentle', topics: ['تذكر','تدبر','عبرة'], weight: 7 },

  // ── Rhetorical question / rebuke ────────────────────────────────────────────
  { signals: ['أفلا تعقلون','أفلا تتقون','أفلا تبصرون','كيف تكفرون',
               'أنى يؤفكون','هل من ظالم','ما لكم','أين شركاؤكم',
               'لماذا','أتعبدون','تزعمون','كنتم تكذبون','كنتم تعتدون',
               'بم تستكبرون'],
    fn: 'rebuke', tone: 'rebuking', topics: ['توبيخ','انتقاد','تساؤل'], weight: 8 },

  // ── Honoring the Prophet ─────────────────────────────────────────────────────
  { signals: ['يا أيها النبي','يا أيها الرسول','بلغ ما أنزل','لا يحزنك',
               'ليس عليك هداهم','قل للذين','ما عليك إلا البلاغ','جاهد'],
    fn: 'instruction', tone: 'honoring', topics: ['النبوة','الرسالة','تكريم'], weight: 9 },

  // ── Lament / grief ───────────────────────────────────────────────────────────
  { signals: ['يا ويلتى','يا ويلنا','يا حسرة','يا أسفى','يا ليتني',
               'يا ليتنا','يا ليت لنا','يا ليت قومي','وا حسرتا'],
    fn: 'lament', tone: 'warning', topics: ['حزن','ندم','مصيبة'], weight: 10 },

  // ── Dialogue / story context ─────────────────────────────────────────────────
  { signals: ['قال يا','قالت يا','قالوا يا','فقال يا','نادى','نادينا',
               'ناداه','ناداها','نادى ربه','ناداه ربه'],
    fn: 'dialogue', tone: 'neutral', topics: ['قصص','حوار','سرد'], weight: 5 },

  // ── Mercy / forgiveness ─────────────────────────────────────────────────────
  { signals: ['فاغفر لنا','اغفر لنا','ارحمنا','آتنا رحمتك','وسعت كل شيء رحمة',
               'هو الغفور الرحيم','توب علينا','ارحم الراحمين','تب إلينا'],
    fn: 'mercy', tone: 'gentle', topics: ['رحمة','مغفرة','دعاء'], weight: 8 },
];

// ─── Pattern → function defaults (when no signal matches) ─────────────────────

const PATTERN_DEFAULT: Record<string, { fn: string; tone: string; topics: string[] }> = {
  supplication:    { fn: 'supplication', tone: 'gentle',    topics: ['دعاء','تضرع'] },
  ya_rabbi:        { fn: 'supplication', tone: 'gentle',    topics: ['دعاء','تضرع'] },
  ya_lament:       { fn: 'lament',       tone: 'warning',   topics: ['حزن','ندم'] },
  ya_wish:         { fn: 'lament',       tone: 'warning',   topics: ['تمني','ندم'] },
  ya_bunayya:      { fn: 'instruction',  tone: 'gentle',    topics: ['وصية','أسرة'] },
  ya_abati:        { fn: 'dialogue',     tone: 'gentle',    topics: ['قصص','أسرة'] },
  ya_prophet_name: { fn: 'instruction',  tone: 'honoring',  topics: ['النبوة','قصص'] },
};

// ─── Addressee → caller inference ─────────────────────────────────────────────

function inferCaller(call: QuranicCall, text: string): { callerType: string; labelArabic: string; labelEnglish: string } {
  const pt = call.callPattern;
  const at = call.addressee.addresseeType;

  // Explicit Allah addresses — ya_ayyuhal + believers/mankind/prophets
  if (['ya_ayyuhal','ya_ayatuha','ya_bani','ya_ibadi','ya_ahl'].includes(pt)) {
    if (['believers','mankind','disbelievers','bani_israel','people_of_book','jinn'].includes(at))
      return { callerType: 'allah', labelArabic: 'الله سبحانه وتعالى', labelEnglish: 'Allah' };
    if (at === 'prophet')
      return { callerType: 'allah', labelArabic: 'الله سبحانه وتعالى', labelEnglish: 'Allah' };
  }
  if (pt === 'ya_prophet_name') {
    // Allah calls prophets most often; occasionally angels or people
    if (['allah'].includes(call.caller.callerType)) return { callerType: 'allah', labelArabic: 'الله سبحانه وتعالى', labelEnglish: 'Allah' };
    return { callerType: 'allah', labelArabic: 'الله سبحانه وتعالى', labelEnglish: 'Allah' };
  }
  // Prophet calls to his people
  if (pt === 'ya_qawmi') {
    return { callerType: 'prophet', labelArabic: 'نبي', labelEnglish: 'Prophet' };
  }
  // Family calls are context-dependent
  if (['ya_abati','ya_bunayya'].includes(pt)) {
    return { callerType: 'unknown', labelArabic: 'غير محدد', labelEnglish: 'Unknown' };
  }
  // Supplication → human calling Allah
  if (['supplication','ya_rabbi'].includes(pt)) {
    return { callerType: 'unknown', labelArabic: 'مؤمن / نبي', labelEnglish: 'Believer / Prophet' };
  }

  return { callerType: call.caller.callerType, labelArabic: call.caller.labelArabic ?? '', labelEnglish: call.caller.labelEnglish ?? '' };
}

// ─── Surah themes for topic enrichment ───────────────────────────────────────

const SURAH_THEMES: Record<number, string[]> = {
  2:['تشريع','عقيدة'],3:['عيسى','مريم','أهل الكتاب'],4:['تشريع','أسرة'],
  5:['أهل الكتاب','تشريع'],6:['توحيد'],7:['قصص الأنبياء'],9:['جهاد'],
  10:['توحيد'],11:['قصص الأنبياء','نوح','هود','صالح','شعيب','لوط'],
  12:['يوسف','صبر'],14:['إبراهيم'],16:['توحيد','نعم'],18:['الكهف','قصص'],
  19:['مريم','زكريا','يحيى','عيسى','إبراهيم'],20:['موسى'],21:['قصص الأنبياء'],
  22:['حج'],24:['تشريع','أسرة'],26:['موسى','إبراهيم','نوح','شعيب'],
  27:['سليمان','هدهد'],28:['موسى','فرعون'],33:['تشريع','النبي'],
  36:['توحيد','قيامة'],37:['إبراهيم','إسماعيل','يونس'],38:['داود','سليمان','أيوب'],
  40:['مؤمن آل فرعون'],46:['الأحقاف'],49:['آداب'],57:['إيمان','إنفاق'],
  58:['تشريع'],59:['جهاد'],60:['تشريع'],61:['جهاد'],64:['إيمان','إنفاق'],
  65:['تشريع','طلاق'],66:['تشريع','أسرة'],109:['الكافرون'],
};

// ─── Main ─────────────────────────────────────────────────────────────────────

console.log('Loading atlas...');
const atlas: Atlas = JSON.parse(readFileSync(IN_JSON, 'utf-8'));
console.log(`Loaded ${atlas.calls.length} calls`);

let classified = 0;
let unclassified = 0;

const classifiedCalls = atlas.calls.map((call) => {
  const text = matchText(call);

  // Pattern-based defaults first
  const patDef = PATTERN_DEFAULT[call.callPattern];

  // Apply signal rules (use emlaei text for matching)
  let bestScore = 0;
  let bestFn = patDef?.fn ?? 'needs_review';
  let bestTone = patDef?.tone ?? 'needs_review';
  let bestTopics: string[] = [...(patDef?.topics ?? []), ...(SURAH_THEMES[call.surahNumber] ?? [])];
  let method = patDef ? 'rule_based' : 'unclassified';
  let matchedSignals: string[] = [];

  for (const rule of RULES) {
    for (const sig of rule.signals) {
      if (text.includes(sig)) {
        if (rule.weight > bestScore) {
          bestScore = rule.weight;
          bestFn = rule.fn;
          bestTone = rule.tone;
          bestTopics = [...rule.topics, ...(SURAH_THEMES[call.surahNumber] ?? [])];
          method = 'topic_signal';
          matchedSignals = [sig];
        } else if (rule.weight === bestScore) {
          matchedSignals.push(sig);
        }
      }
    }
  }

  // Infer caller
  const callerInferred = inferCaller(call, text);
  const callerType = callerInferred.callerType !== call.caller.callerType
    ? callerInferred.callerType : call.caller.callerType;
  const callerLabelAr = callerInferred.labelArabic || call.caller.labelArabic;
  const callerLabelEn = callerInferred.labelEnglish || call.caller.labelEnglish;

  if (bestFn !== 'needs_review') classified++;
  else unclassified++;

  return {
    ...call,
    callFunction: bestFn,
    tone: bestTone,
    relatedTopics: [...new Set(bestTopics)].slice(0, 6),
    caller: {
      ...call.caller,
      callerType,
      labelArabic: callerLabelAr,
      labelEnglish: callerLabelEn,
    },
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    classifiedAt: new Date().toISOString(),
    classificationMethod: method,
    classificationSignals: matchedSignals,
  };
});

// Summary
const byFunction: Record<string, number> = {};
const byTone: Record<string, number> = {};
const byCallerType: Record<string, number> = {};
let highConf = 0;
let lowConf = 0;

for (const c of classifiedCalls) {
  byFunction[c.callFunction] = (byFunction[c.callFunction] ?? 0) + 1;
  byTone[c.tone] = (byTone[c.tone] ?? 0) + 1;
  byCallerType[c.caller.callerType] = (byCallerType[c.caller.callerType] ?? 0) + 1;
  if (c.confidence > 0.7) highConf++;
  if (c.confidence <= 0.4) lowConf++;
}

const output = {
  version: '2.0.0-phase-y',
  classifiedAt: new Date().toISOString(),
  totalClassified: classifiedCalls.length,
  calls: classifiedCalls,
  classificationSummary: { byFunction, byTone, byCallerType, unclassified, highConfidence: highConf, lowConfidence: lowConf },
};

writeFileSync(OUT_JSON, JSON.stringify(output, null, 2), 'utf-8');
console.log(`\n✓ Written: ${OUT_JSON}`);

console.log('\n' + '='.repeat(60));
console.log('CLASSIFICATION v2 COMPLETE');
console.log('='.repeat(60));
console.log(`Total: ${classifiedCalls.length} | Classified: ${classified} | Unclassified: ${unclassified}`);
console.log(`Coverage: ${((classified / classifiedCalls.length) * 100).toFixed(1)}%`);
console.log('\nBy Function:');
Object.entries(byFunction).sort(([,a],[,b])=>b-a).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
console.log('\nBy Tone:');
Object.entries(byTone).sort(([,a],[,b])=>b-a).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
console.log('\nBy Caller:');
Object.entries(byCallerType).sort(([,a],[,b])=>b-a).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
console.log('='.repeat(60));
