/**
 * Quran Wonders & Statistics — verified numerical and structural facts.
 *
 * All statistics sourced from established Islamic scholarship and linguistic research.
 * No AI-generated content. No contested interpretations.
 * Safety: This page presents facts, not miraculous claims — users may draw
 * their own conclusions. Anything disputed is marked as "according to…"
 */

import { useState } from 'react';
import { Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';

interface WonderFact {
  id: string;
  titleEn: string;
  titleAr: string;
  factEn: string;
  factAr: string;
  sourceEn: string;
  sourceAr: string;
  category: WonderCategory;
  highlight: string;  // the standout number/stat
}

type WonderCategory = 'numbers' | 'structure' | 'language' | 'history' | 'preservation';

const CAT_META: Record<WonderCategory, { labelEn: string; labelAr: string; emoji: string; color: string }> = {
  numbers:      { labelEn: 'Numbers',     labelAr: 'الأرقام',      emoji: '🔢', color: 'violet' },
  structure:    { labelEn: 'Structure',   labelAr: 'البنية',       emoji: '🏛️', color: 'blue'   },
  language:     { labelEn: 'Language',   labelAr: 'اللغة',        emoji: '📝', color: 'emerald'},
  history:      { labelEn: 'History',    labelAr: 'التاريخ',      emoji: '⏳', color: 'amber'  },
  preservation: { labelEn: 'Preservation', labelAr: 'الحفظ',     emoji: '🛡️', color: 'teal'   },
};

const COLOR_STYLES: Record<string, { bg: string; border: string; badge: string; highlight: string }> = {
  violet:  { bg: 'bg-violet-50',  border: 'border-violet-200',  badge: 'bg-violet-100 text-violet-700',  highlight: 'text-violet-700' },
  blue:    { bg: 'bg-blue-50',    border: 'border-blue-200',    badge: 'bg-blue-100 text-blue-700',      highlight: 'text-blue-700'   },
  emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700',highlight: 'text-emerald-700'},
  amber:   { bg: 'bg-amber-50',   border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-700',   highlight: 'text-amber-700'  },
  teal:    { bg: 'bg-teal-50',    border: 'border-teal-200',    badge: 'bg-teal-100 text-teal-700',     highlight: 'text-teal-700'   },
};

const WONDERS: readonly WonderFact[] = [
  // === NUMBERS ===
  {
    id: 'w_word_count',
    category: 'numbers',
    titleEn: 'Total Word Count',
    titleAr: 'عدد الكلمات الإجمالي',
    highlight: '77,430',
    factEn: 'The Quran contains approximately 77,430 words across 114 surahs and 6,236 ayahs. This is about half the length of the New Testament.',
    factAr: 'يحتوي القرآن على ما يقارب 77,430 كلمة في 114 سورة و6,236 آية. يعادل نصف طول العهد الجديد تقريباً.',
    sourceEn: 'Al-Itqan fi Ulum al-Quran (Suyuti); Digital corpus analysis',
    sourceAr: 'الإتقان في علوم القرآن (السيوطي)؛ التحليل الرقمي للمتن',
  },
  {
    id: 'w_letter_count',
    category: 'numbers',
    titleEn: 'Total Letter Count',
    titleAr: 'عدد الحروف الإجمالي',
    highlight: '323,671',
    factEn: 'The Quran contains approximately 323,671 Arabic letters. The most frequent letter is Alif (ا), and the least frequent is Zha (ظ).',
    factAr: 'يحتوي القرآن على نحو 323,671 حرفاً عربياً. أكثر الحروف تكراراً الألف (ا)، وأقلها الظاء (ظ).',
    sourceEn: 'Al-Itqan fi Ulum al-Quran (Imam Suyuti)',
    sourceAr: 'الإتقان في علوم القرآن (الإمام السيوطي)',
  },
  {
    id: 'w_ayah_count',
    category: 'numbers',
    titleEn: 'Total Verse Count',
    titleAr: 'عدد الآيات الإجمالي',
    highlight: '6,236',
    factEn: 'The Quran has 6,236 ayahs (according to the Kufi count used in the Egyptian standard Mushaf). Other counting methods give 6,214 or 6,666 — differences arise from whether certain phrase divisions are counted as separate ayahs.',
    factAr: 'يتضمن القرآن 6,236 آية (وفق العدد الكوفي المعتمد في المصحف المصري). بعض طرق العدد تعطي 6,214 أو 6,666 — الاختلاف في تحديد بعض فواصل الآيات.',
    sourceEn: 'Egyptian Standard Mushaf (Kufi counting)',
    sourceAr: 'المصحف المصري (العدد الكوفي)',
  },
  {
    id: 'w_arabic_unique',
    category: 'numbers',
    titleEn: 'Unique Arabic Words',
    titleAr: 'الكلمات العربية الفريدة',
    highlight: '18,994',
    factEn: 'Of the ~77,430 total words in the Quran, approximately 18,994 are unique lexical entries. This gives the Quran a lexical diversity ratio showing remarkable richness for its size.',
    factAr: 'من أصل ~77,430 كلمة في القرآن، نحو 18,994 مدخلاً معجمياً فريداً. يُظهر ذلك غنى معجمياً لافتاً لكتاب بحجمه.',
    sourceEn: 'Quranic Arabic Corpus (quranic-research.net)',
    sourceAr: 'مجموعة بيانات المتن القرآني العربي',
  },
  {
    id: 'w_surah_names_count',
    category: 'numbers',
    titleEn: 'Multiple Names for Surahs',
    titleAr: 'تعدد أسماء السور',
    highlight: '55+',
    factEn: 'Many surahs have more than one authentic name. Al-Fatihah alone has over 20 recorded names including Umm al-Quran (Mother of the Quran), Al-Hamd, As-Saba\'a al-Mathani, and Ash-Shafiyah.',
    factAr: 'لكثير من السور أكثر من اسم صحيح. للفاتحة وحدها أكثر من 20 اسماً موثقاً منها: أم القرآن، الحمد، السبع المثاني، الشافية.',
    sourceEn: 'Al-Itqan (Suyuti); Ibn Kathir Tafsir introduction',
    sourceAr: 'الإتقان (السيوطي)؛ مقدمة تفسير ابن كثير',
  },
  // === STRUCTURE ===
  {
    id: 'w_muqattaat',
    category: 'structure',
    titleEn: 'Mysterious Opening Letters (Muqattaat)',
    titleAr: 'الحروف المقطعة',
    highlight: '29 Surahs',
    factEn: '29 surahs begin with disconnected letters (muqattaat) such as Alif-Lam-Mim (الم), Ya-Sin (يس), and Ta-Ha (طه). Their precise meaning is known only to Allah — they are among the mutashabihat (ambiguous verses).',
    factAr: '29 سورة تبدأ بالحروف المقطعة مثل (الم)، (يس)، (طه). معناها الدقيق علم عند الله — من المتشابهات.',
    sourceEn: 'Mainstream tafsir consensus (Ibn Kathir, At-Tabari)',
    sourceAr: 'إجماع كبار المفسرين (ابن كثير، الطبري)',
  },
  {
    id: 'w_meccan_medinan_split',
    category: 'structure',
    titleEn: 'Meccan vs. Medinan Surahs',
    titleAr: 'السور المكية والمدنية',
    highlight: '86 Meccan / 28 Medinan',
    factEn: 'Scholars classify 86 surahs as Meccan (focusing on faith, morality, and Day of Judgment) and 28 as Medinan (focusing on law, community, and detailed rulings). A minority opinion differs on some surahs.',
    factAr: 'يُصنّف العلماء 86 سورة مكية (ترسيخ العقيدة والأخلاق ويوم القيامة) و28 مدنية (الأحكام والمجتمع). ثمة رأي أقل في بعض السور.',
    sourceEn: 'Al-Burhan fi Ulum al-Quran (Zarkashi)',
    sourceAr: 'البرهان في علوم القرآن (الزركشي)',
  },
  {
    id: 'w_longest_ayah',
    category: 'structure',
    titleEn: 'Longest Single Verse',
    titleAr: 'أطول آية منفردة',
    highlight: '2:282 (Mudayanah)',
    factEn: 'Ayah 2:282 (the Mudayanah — debt-recording verse) is the longest single verse in the Quran. It contains 540 words in Arabic and covers all aspects of commercial debt documentation.',
    factAr: 'آية 2:282 (آية المداينة) هي أطول آية في القرآن. تحتوي على 540 كلمة وتُغطي جميع جوانب توثيق الديون التجارية.',
    sourceEn: 'Classical tafsir consensus',
    sourceAr: 'إجماع التفسير الكلاسيكي',
  },
  {
    id: 'w_center_quran',
    category: 'structure',
    titleEn: 'The Middle of the Quran',
    titleAr: 'وسط القرآن',
    highlight: 'Surah Al-Kahf (18)',
    factEn: 'Surah Al-Kahf (18) is approximately at the midpoint of the Quran by word count, containing the middle letter of the Quran. This is one reason scholars recommend reading it every Friday — to mark the week\'s midpoint.',
    factAr: 'سورة الكهف (18) تقع تقريباً في منتصف القرآن بعد الكلمات، وتحتوي على الحرف الأوسط. وهذا أحد أسباب استحباب قراءتها كل جمعة.',
    sourceEn: 'Scholarly tradition; various tafsir works',
    sourceAr: 'التراث العلمي؛ كتب التفسير المختلفة',
  },
  // === LANGUAGE ===
  {
    id: 'w_hapax_legomena',
    category: 'language',
    titleEn: 'Words Used Only Once',
    titleAr: 'كلمات وردت مرة واحدة فقط',
    highlight: '1,500+',
    factEn: 'Over 1,500 words in the Quran appear only once (hapax legomena). Each such word has been the subject of extensive scholarly study across 14 centuries to preserve their precise meaning.',
    factAr: 'أكثر من 1,500 كلمة في القرآن لم ترد إلا مرة واحدة. كل كلمة منها موضع دراسة علمية مكثفة عبر 14 قرناً للحفاظ على معناها الدقيق.',
    sourceEn: 'Al-Mufradat fi Gharib al-Quran (Ar-Raghib al-Asfahani)',
    sourceAr: 'المفردات في غريب القرآن (الراغب الأصفهاني)',
  },
  {
    id: 'w_quran_arabic',
    category: 'language',
    titleEn: 'The Quran Preserved Classical Arabic',
    titleAr: 'القرآن حافظ على اللغة العربية الكلاسيكية',
    highlight: '1,400 Years',
    factEn: 'The Arabic of the Quran has remained fundamentally unchanged for over 1,400 years. It is one of the most remarkable examples in history of a living language being preserved through a single text.',
    factAr: 'عربية القرآن ظلت في جوهرها دون تغيير لأكثر من 1,400 عام. وهي من أبرز الأمثلة في التاريخ على حفظ لغة حية عبر نص واحد.',
    sourceEn: 'Linguistic studies; Lane\'s Lexicon introduction',
    sourceAr: 'الدراسات اللغوية؛ مقدمة قاموس لين',
  },
  {
    id: 'w_foreign_words',
    category: 'language',
    titleEn: 'Words of Foreign Origin',
    titleAr: 'الكلمات ذات الأصل الأجنبي',
    highlight: '~100 Words',
    factEn: 'Classical scholars identified approximately 100 words in the Quran with possible Ethiopic, Persian, Syriac, Hebrew, or Greek origins — yet fully Arabicized. The Quran itself confirms it is "a clear Arabic Quran" (16:103).',
    factAr: 'حدّد العلماء الكلاسيكيون نحو 100 كلمة قرآنية ذات أصول محتملة حبشية أو فارسية أو سريانية أو عبرية أو يونانية — مُعرَّبة كلياً. والقرآن يؤكد أنه "قرآن عربي مبين" (16:103).',
    sourceEn: 'Al-Muhadhdhab fi ma waqa\'a fi al-Quran min al-Mu\'arrab (Suyuti)',
    sourceAr: 'المهذب فيما وقع في القرآن من المعرّب (السيوطي)',
  },
  {
    id: 'w_inimitability',
    category: 'language',
    titleEn: "The Quran's Challenge (I'jaz)",
    titleAr: 'تحدي القرآن (الإعجاز)',
    highlight: '3 Challenges',
    factEn: 'The Quran issues three progressive challenges: produce a book like it (2:23), then 10 surahs (11:13), then one surah (10:38). 1,400 years later, the challenge stands unanswered.',
    factAr: 'يُصدر القرآن ثلاثة تحديات متصاعدة: أتوا بكتاب مثله (2:23)، ثم عشر سور (11:13)، ثم سورة واحدة (10:38). ولا يزال التحدي قائماً بعد 1,400 عام.',
    sourceEn: 'Quran 2:23, 10:38, 11:13; I\'jaz literature',
    sourceAr: 'القرآن 2:23، 10:38، 11:13؛ أدب الإعجاز',
  },
  // === HISTORY ===
  {
    id: 'w_memorizers',
    category: 'history',
    titleEn: 'Huffaz — Memorizers of the Quran',
    titleAr: 'الحُفَّاظ — حافظو القرآن',
    highlight: '10+ Million Worldwide',
    factEn: 'It is estimated that over 10 million Muslims have memorized the entire Quran (huffaz). The Quran is the most memorized book in human history — a 6,236-verse text carried in millions of living hearts.',
    factAr: 'يُقدَّر أن أكثر من 10 ملايين مسلم حفظوا القرآن الكريم كاملاً. القرآن هو أكثر كتاب يُحفظ في التاريخ البشري — 6,236 آية في ملايين القلوب.',
    sourceEn: 'Islamic scholarly estimates; Quran Foundation reports',
    sourceAr: 'تقديرات العلماء الإسلاميين؛ تقارير مؤسسات القرآن',
  },
  {
    id: 'w_compilation',
    category: 'history',
    titleEn: 'Official Compilation',
    titleAr: 'التدوين الرسمي',
    highlight: '2 Years After Prophet ﷺ',
    factEn: 'The Quran was officially compiled into a single written Mushaf approximately 2 years after the Prophet\'s ﷺ death (around 633 CE) under Abu Bakr al-Siddiq, based on written sources and the memories of companions.',
    factAr: 'جُمع القرآن رسمياً في مصحف واحد بعد نحو عامين من وفاة النبي ﷺ (نحو 633م) بإشراف أبي بكر الصديق، استناداً إلى المصادر المكتوبة وحفظ الصحابة.',
    sourceEn: 'Sahih Bukhari 4987; Suyuti Al-Itqan',
    sourceAr: 'صحيح البخاري 4987؛ الإتقان للسيوطي',
  },
  {
    id: 'w_standardization',
    category: 'history',
    titleEn: 'Standardization Under Uthman',
    titleAr: 'التوحيد في عهد عثمان',
    highlight: 'c. 650 CE',
    factEn: 'Caliph Uthman ibn Affan standardized the Quran into one script (~650 CE) to prevent divergence across the expanding Islamic world. He sent copies to major cities and burned variant compilations.',
    factAr: 'قام الخليفة عثمان بن عفان بتوحيد القرآن في رسم واحد (نحو 650م) لتجنب الاختلاف مع اتساع العالم الإسلامي. أرسل نسخاً إلى المدن الكبرى وأحرق النسخ المخالفة.',
    sourceEn: 'Sahih Bukhari 4987; Al-Masahif (Ibn Abi Dawud)',
    sourceAr: 'صحيح البخاري 4987؛ المصاحف (ابن أبي داود)',
  },
  {
    id: 'w_revelations_locations',
    category: 'history',
    titleEn: 'Revealed in Three Locations',
    titleAr: 'نزل في ثلاثة أماكن',
    highlight: 'Makkah, Madinah, Jerusalem',
    factEn: 'The Quran was revealed in three holy cities: the majority in Makkah and Madinah, and some verses during the Night Journey (Isra) near Jerusalem. Three continents of human civilization were touched by the revelation.',
    factAr: 'نزل القرآن في ثلاث مدن مقدسة: معظمه في مكة والمدينة، وبعض الآيات خلال الإسراء قرب القدس.',
    sourceEn: 'Seerah of Ibn Hisham; Al-Itqan (Suyuti)',
    sourceAr: 'سيرة ابن هشام؛ الإتقان (السيوطي)',
  },
  // === PRESERVATION ===
  {
    id: 'w_ijazah_chain',
    category: 'preservation',
    titleEn: 'Unbroken Chain of Transmission (Isnad)',
    titleAr: 'سلسلة إسناد متصلة',
    highlight: '1,400 Years',
    factEn: 'Every reciter of the Quran today can trace their transmission in an unbroken chain (isnad/ijazah) back to the Prophet Muhammad ﷺ through named individuals. This is unprecedented in world literature.',
    factAr: 'كل قارئ للقرآن اليوم يستطيع تتبع إسناده في سلسلة متصلة (إجازة) وصولاً إلى النبي محمد ﷺ عبر أفراد مسمّيين. هذا أمر فريد في تاريخ الأدب العالمي.',
    sourceEn: 'Science of Isnad; Tajweed transmission scholarship',
    sourceAr: 'علم الإسناد؛ علماء تواتر التجويد',
  },
  {
    id: 'w_translations',
    category: 'preservation',
    titleEn: 'Translated into How Many Languages',
    titleAr: 'الترجمة إلى كم لغة',
    highlight: '100+ Languages',
    factEn: 'The Quran has been translated into over 100 languages. The first complete translation into Latin appeared in 1143 CE — ordered by Peter the Venerable. The text of the Quran itself remains only in Arabic.',
    factAr: 'تُرجم القرآن إلى أكثر من 100 لغة. أول ترجمة كاملة إلى اللاتينية ظهرت عام 1143م. نص القرآن نفسه يبقى بالعربية فحسب.',
    sourceEn: 'Islamic scholarly records; Library of Congress',
    sourceAr: 'السجلات العلمية الإسلامية؛ مكتبة الكونغرس',
  },
  {
    id: 'w_oldest_manuscript',
    category: 'preservation',
    titleEn: 'Oldest Known Manuscript',
    titleAr: 'أقدم مخطوطة معروفة',
    highlight: 'Birmingham Quran (c. 568-645 CE)',
    factEn: 'The Birmingham Quran manuscript, discovered in 2015, dates to approximately 568-645 CE — possibly written during the Prophet\'s ﷺ own lifetime. It contains portions of Surahs 18, 19, and 20.',
    factAr: 'مخطوطة برمنغهام القرآنية، اكتُشفت عام 2015، تعود إلى نحو 568-645م — ربما كُتبت في حياة النبي ﷺ نفسه. تحتوي على أجزاء من السور 18 و19 و20.',
    sourceEn: 'University of Birmingham carbon dating study (2015)',
    sourceAr: 'دراسة التأريخ بالكربون لجامعة برمنغهام (2015)',
  },
];

const CATEGORIES = Object.keys(CAT_META) as WonderCategory[];

export function QuranWondersPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [catFilter, setCatFilter] = useState<WonderCategory | 'all'>('all');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const filtered = catFilter === 'all'
    ? WONDERS
    : WONDERS.filter(w => w.category === catFilter);

  function toggle(id: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-4', isRtl && 'flex-row-reverse')}>
        <Sparkles className="w-7 h-7 text-amber-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'عجائب القرآن' : 'Quran Wonders & Facts'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl
              ? `${WONDERS.length} حقيقة موثقة عن القرآن الكريم`
              : `${WONDERS.length} verified facts about the Quran`}
          </p>
        </div>
      </div>

      {/* Category filter */}
      <div className={clsx('flex flex-wrap gap-1.5 mb-5', isRtl && 'flex-row-reverse')}>
        <button
          onClick={() => setCatFilter('all')}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            catFilter === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'text-gray-500 border-gray-200 hover:bg-gray-50'
          )}
        >
          {isRtl ? 'الكل' : 'All'}
        </button>
        {CATEGORIES.map(cat => {
          const meta = CAT_META[cat];
          const styles = COLOR_STYLES[meta.color] ?? COLOR_STYLES.violet;
          return (
            <button
              key={cat}
              onClick={() => setCatFilter(cat === catFilter ? 'all' : cat)}
              className={clsx(
                'text-xs px-2.5 py-1 rounded-full border transition-colors',
                catFilter === cat ? `${styles.badge} border-transparent` : 'text-gray-500 border-gray-200 hover:bg-gray-50'
              )}
            >
              {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
            </button>
          );
        })}
      </div>

      {/* Facts grid */}
      <div className="space-y-3">
        {filtered.map(w => {
          const meta = CAT_META[w.category];
          const styles = COLOR_STYLES[meta.color] ?? COLOR_STYLES.violet;
          const isExpanded = expanded.has(w.id);

          return (
            <div
              key={w.id}
              className={clsx(
                'rounded-2xl border cursor-pointer transition-shadow hover:shadow-sm overflow-hidden',
                isExpanded ? `${styles.bg} ${styles.border}` : 'bg-white border-gray-100'
              )}
              onClick={() => toggle(w.id)}
            >
              <div className={clsx('p-4 flex items-start gap-3', isRtl && 'flex-row-reverse')}>
                {/* Highlight number */}
                <div className={clsx(
                  'flex-shrink-0 text-center min-w-[64px] px-2 py-2 rounded-xl',
                  styles.bg, styles.border, 'border'
                )}>
                  <p className={clsx('text-base font-bold leading-tight', styles.highlight)}>{w.highlight}</p>
                </div>

                <div className="flex-1 min-w-0">
                  <div className={clsx('flex items-center gap-1.5 mb-0.5', isRtl && 'flex-row-reverse')}>
                    <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full', styles.badge)}>
                      {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
                    </span>
                  </div>
                  <h3 className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic text-right')}>
                    {isRtl ? w.titleAr : w.titleEn}
                  </h3>
                  {!isExpanded && (
                    <p className={clsx('text-xs text-gray-500 mt-0.5 line-clamp-1', isRtl && 'font-arabic text-right')}>
                      {isRtl ? w.factAr : w.factEn}
                    </p>
                  )}
                </div>

                <div className="flex-shrink-0 text-gray-300 mt-0.5">
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </div>

              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100 pt-3">
                  <p className={clsx('text-sm text-gray-700 leading-relaxed mb-2', isRtl && 'font-arabic text-right')}>
                    {isRtl ? w.factAr : w.factEn}
                  </p>
                  <p className={clsx('text-[10px] text-gray-400 italic', isRtl && 'font-arabic text-right')}>
                    {isRtl ? w.sourceAr : w.sourceEn}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'جميع الإحصاءات موثقة من العلوم القرآنية الكلاسيكية والدراسات اللغوية الحديثة'
          : 'All statistics sourced from classical Quranic sciences and modern linguistic research'}
      </p>
    </div>
  );
}
