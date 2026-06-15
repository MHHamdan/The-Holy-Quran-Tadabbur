/**
 * Persona-based Learning Paths for Quranic study.
 *
 * Each path is a curated, structured curriculum tailored to a
 * specific persona type. Content references real platform routes.
 *
 * All thematic descriptions are general/educational, not tafsir.
 * No Quran text generated here — only references to verses.
 */

import type { Persona } from '../stores/personaStore';

export interface LearningMilestone {
  id: string;
  titleEn: string;
  titleAr: string;
  descEn: string;
  descAr: string;
  estimatedDaysEn: string;
  estimatedDaysAr: string;
  steps: LearningStep[];
}

export interface LearningStep {
  id: string;
  labelEn: string;
  labelAr: string;
  route: string;
  type: 'read' | 'explore' | 'practice' | 'reflect' | 'memorize';
}

export interface LearningPath {
  persona: Persona;
  taglineEn: string;
  taglineAr: string;
  color: string;
  milestones: LearningMilestone[];
  featuredSurahs: number[];
  featuredDuaIds: string[];
  suggestedJuz: number[];
}

export const LEARNING_PATHS: Record<Persona, LearningPath> = {
  new_muslim: {
    persona: 'new_muslim',
    taglineEn: 'Your gentle entry into the Quran — one chapter at a time',
    taglineAr: 'مدخلك اللطيف إلى القرآن — خطوة بخطوة',
    color: 'emerald',
    milestones: [
      {
        id: 'nm_m1',
        titleEn: 'The Essentials (Week 1)',
        titleAr: 'الأساسيات (الأسبوع الأول)',
        descEn: 'Start with the most recited surah and explore the six pillars of faith.',
        descAr: 'ابدأ بأكثر السور تكراراً واستعرض أركان الإيمان الستة.',
        estimatedDaysEn: '7 days',
        estimatedDaysAr: '٧ أيام',
        steps: [
          { id: 'nm_m1_1', labelEn: 'Read Al-Fatihah (the Opening)', labelAr: 'اقرأ الفاتحة', route: '/quran/1', type: 'read' },
          { id: 'nm_m1_2', labelEn: 'Explore Al-Ikhlas (Pure Monotheism)', labelAr: 'استكشف سورة الإخلاص', route: '/quran/112', type: 'read' },
          { id: 'nm_m1_3', labelEn: 'Learn the Quranic duʿā for guidance', labelAr: 'تعلم دعاء الاهتداء القرآني', route: '/duas', type: 'reflect' },
          { id: 'nm_m1_4', labelEn: 'Read about the Quran\'s purpose & sources', labelAr: 'اقرأ عن غرض القرآن ومصادر تفسيره', route: '/sources', type: 'explore' },
        ],
      },
      {
        id: 'nm_m2',
        titleEn: 'Short Surahs of Juz 30 (Week 2–3)',
        titleAr: 'سور جزء عم (الأسبوع ٢–٣)',
        descEn: 'The final Juz contains short, powerful surahs — perfect for beginners.',
        descAr: 'جزء عم يحتوي على سور قصيرة ومؤثرة — مثالية للمبتدئين.',
        estimatedDaysEn: '14 days',
        estimatedDaysAr: '١٤ يوماً',
        steps: [
          { id: 'nm_m2_1', labelEn: 'Browse Juz 30 overview', labelAr: 'استعرض نظرة على الجزء الثلاثين', route: '/juz', type: 'explore' },
          { id: 'nm_m2_2', labelEn: 'Read An-Nas & Al-Falaq (protection)', labelAr: 'اقرأ الناس والفلق', route: '/quran/113', type: 'read' },
          { id: 'nm_m2_3', labelEn: 'Read Al-Asr (time)', labelAr: 'اقرأ سورة العصر', route: '/quran/103', type: 'read' },
          { id: 'nm_m2_4', labelEn: 'Start tracking your reading progress', labelAr: 'ابدأ تتبع تقدمك في القراءة', route: '/reading-plan', type: 'practice' },
          { id: 'nm_m2_5', labelEn: 'Try the daily quiz', labelAr: 'جرّب اختبار اليوم', route: '/challenge', type: 'practice' },
        ],
      },
      {
        id: 'nm_m3',
        titleEn: 'Key Stories (Month 2)',
        titleAr: 'القصص الكبرى (الشهر الثاني)',
        descEn: 'Quranic stories of prophets provide the clearest path to Islamic values.',
        descAr: 'قصص الأنبياء توضح القيم الإسلامية بأجلى صورة.',
        estimatedDaysEn: '30 days',
        estimatedDaysAr: '٣٠ يوماً',
        steps: [
          { id: 'nm_m3_1', labelEn: 'Explore story of Musa (Exodus & Faith)', labelAr: 'استكشف قصة موسى', route: '/stories', type: 'explore' },
          { id: 'nm_m3_2', labelEn: 'Read story of Yusuf (Surah 12)', labelAr: 'اقرأ قصة يوسف (السورة ١٢)', route: '/quran/12', type: 'read' },
          { id: 'nm_m3_3', labelEn: 'Explore prophets\' supplications', labelAr: 'استكشف أدعية الأنبياء', route: '/duas', type: 'reflect' },
          { id: 'nm_m3_4', labelEn: 'Explore the Prophets Atlas', labelAr: 'استكشف أطلس الأنبياء', route: '/prophets', type: 'explore' },
        ],
      },
    ],
    featuredSurahs: [1, 112, 113, 114, 103, 112, 36, 12],
    featuredDuaIds: ['dua_fatiha_guidance', 'dua_baqarah_good_world_akhira', 'dua_kahf_mercy_guidance'],
    suggestedJuz: [30, 29, 1],
  },

  student: {
    persona: 'student',
    taglineEn: 'Systematic Quranic knowledge with scholarly depth',
    taglineAr: 'معرفة قرآنية منهجية بعمق علمي',
    color: 'blue',
    milestones: [
      {
        id: 'stu_m1',
        titleEn: 'Tafsir Methodology (Week 1)',
        titleAr: 'منهجية التفسير (الأسبوع الأول)',
        descEn: 'Understand how classical tafsir scholars approached the Quran.',
        descAr: 'افهم كيف تعامل علماء التفسير الكلاسيكيون مع القرآن.',
        estimatedDaysEn: '7 days',
        estimatedDaysAr: '٧ أيام',
        steps: [
          { id: 'stu_m1_1', labelEn: 'Review the sources registry', labelAr: 'راجع سجل المصادر', route: '/sources', type: 'explore' },
          { id: 'stu_m1_2', labelEn: 'Ask the AI tafsir assistant about a verse', labelAr: 'اسأل مساعد التفسير عن آية', route: '/ask', type: 'explore' },
          { id: 'stu_m1_3', labelEn: 'Explore thematic Quranic themes', labelAr: 'استكشف المحاور القرآنية', route: '/themes', type: 'explore' },
          { id: 'stu_m1_4', labelEn: 'Try the safe AI prompting guide', labelAr: 'جرّب دليل الأسئلة الآمنة', route: '/tools/prompt-guide', type: 'practice' },
        ],
      },
      {
        id: 'stu_m2',
        titleEn: 'Verse Similarity & Concepts (Week 2–3)',
        titleAr: 'تشابه الآيات والمفاهيم (الأسبوع ٢–٣)',
        descEn: 'Discover intra-Quranic connections — how verses illuminate each other.',
        descAr: 'اكتشف الروابط الداخلية في القرآن — كيف تفسر الآيات بعضها.',
        estimatedDaysEn: '14 days',
        estimatedDaysAr: '١٤ يوماً',
        steps: [
          { id: 'stu_m2_1', labelEn: 'Explore verse similarity engine', labelAr: 'استكشف محرك تشابه الآيات', route: '/similarity', type: 'explore' },
          { id: 'stu_m2_2', labelEn: 'Browse Quranic concepts & entities', labelAr: 'تصفح مفاهيم القرآن وكياناته', route: '/concepts', type: 'explore' },
          { id: 'stu_m2_3', labelEn: 'Read Al-Baqarah (legislative depth)', labelAr: 'اقرأ البقرة (العمق التشريعي)', route: '/quran/2', type: 'read' },
          { id: 'stu_m2_4', labelEn: 'Search for a legal/theological term', labelAr: 'ابحث عن مصطلح فقهي أو عقدي', route: '/search', type: 'practice' },
        ],
      },
      {
        id: 'stu_m3',
        titleEn: 'Deep Story Analysis (Month 2)',
        titleAr: 'التحليل العميق للقصص (الشهر الثاني)',
        descEn: 'Study story structure, cross-surah occurrences, and scholarly commentary.',
        descAr: 'ادرس بنية القصص وتكرارها عبر السور والتعليق العلمي.',
        estimatedDaysEn: '30 days',
        estimatedDaysAr: '٣٠ يوماً',
        steps: [
          { id: 'stu_m3_1', labelEn: 'Explore the Story Atlas cluster view', labelAr: 'استكشف خريطة قصص القرآن', route: '/stories', type: 'explore' },
          { id: 'stu_m3_2', labelEn: 'Read a story in full (with kids quiz & reflection)', labelAr: 'اقرأ قصة كاملة (مع الاختبار والتأمل)', route: '/stories', type: 'reflect' },
          { id: 'stu_m3_3', labelEn: 'Explore Surah Atlas for 2-3 surahs', labelAr: 'استكشف أطلس سورتين أو ثلاث', route: '/surah-atlas', type: 'explore' },
          { id: 'stu_m3_4', labelEn: 'Test knowledge with daily challenge', labelAr: 'اختبر المعلومات بتحدي اليوم', route: '/challenge', type: 'practice' },
        ],
      },
    ],
    featuredSurahs: [2, 3, 4, 12, 18, 36],
    featuredDuaIds: ['dua_nur_knowledge', 'dua_baqarah_forgiveness', 'dua_imran_comprehensive'],
    suggestedJuz: [1, 2, 3, 12, 13],
  },

  researcher: {
    persona: 'researcher',
    taglineEn: 'Academic rigor meets classical scholarship',
    taglineAr: 'الصرامة الأكاديمية تلتقي بالتراث الكلاسيكي',
    color: 'violet',
    milestones: [
      {
        id: 'res_m1',
        titleEn: 'Source & Citation Framework',
        titleAr: 'إطار المصادر والاستشهاد',
        descEn: 'Understand the scholarly lineage behind every answer on this platform.',
        descAr: 'افهم السلسلة العلمية وراء كل إجابة على هذه المنصة.',
        estimatedDaysEn: '3 days',
        estimatedDaysAr: '٣ أيام',
        steps: [
          { id: 'res_m1_1', labelEn: 'Review all tafsir sources & reliability ratings', labelAr: 'راجع جميع مصادر التفسير وتقييمات الموثوقية', route: '/sources', type: 'explore' },
          { id: 'res_m1_2', labelEn: 'Test the AI on a complex theological question', labelAr: 'اختبر الذكاء الاصطناعي في سؤال لاهوتي معقد', route: '/ask', type: 'explore' },
          { id: 'res_m1_3', labelEn: 'Observe scholarly disagreement cards', labelAr: 'لاحظ بطاقات الخلاف العلمي', route: '/ask', type: 'reflect' },
        ],
      },
      {
        id: 'res_m2',
        titleEn: 'Intertextual Analysis',
        titleAr: 'التحليل التناصي',
        descEn: 'Map conceptual connections, verse similarities, and cross-references.',
        descAr: 'خريطة الروابط المفاهيمية وتشابه الآيات والإحالات المتقاطعة.',
        estimatedDaysEn: '7 days',
        estimatedDaysAr: '٧ أيام',
        steps: [
          { id: 'res_m2_1', labelEn: 'Explore the verse similarity engine (RRF hybrid)', labelAr: 'استكشف محرك تشابه الآيات (هجين RRF)', route: '/similarity', type: 'explore' },
          { id: 'res_m2_2', labelEn: 'Map concepts across multiple surahs', labelAr: 'خرّط مفاهيم عبر سور متعددة', route: '/concepts', type: 'explore' },
          { id: 'res_m2_3', labelEn: 'Search semantically for a theological term', labelAr: 'ابحث دلالياً عن مصطلح عقدي', route: '/search', type: 'practice' },
          { id: 'res_m2_4', labelEn: 'Read the story atlas connections graph', labelAr: 'اقرأ مخطط روابط أطلس القصص', route: '/story-atlas/connections', type: 'explore' },
        ],
      },
      {
        id: 'res_m3',
        titleEn: 'Thematic Deep Dive',
        titleAr: 'الغوص العميق في الموضوعات',
        descEn: 'Comprehensive analysis of a single Quranic theme across the corpus.',
        descAr: 'تحليل شامل لموضوع قرآني واحد عبر المصحف كله.',
        estimatedDaysEn: '14 days',
        estimatedDaysAr: '١٤ يوماً',
        steps: [
          { id: 'res_m3_1', labelEn: 'Select a theme and explore all surah appearances', labelAr: 'اختر موضوعاً واستكشف ظهوره في السور', route: '/themes', type: 'explore' },
          { id: 'res_m3_2', labelEn: 'Cross-reference with Prophets Atlas', labelAr: 'قاطعه مع أطلس الأنبياء', route: '/prophets', type: 'explore' },
          { id: 'res_m3_3', labelEn: 'Ask the agentic AI for multi-source analysis', labelAr: 'اسأل الذكاء الاصطناعي العامل عن تحليل متعدد المصادر', route: '/ask', type: 'reflect' },
        ],
      },
    ],
    featuredSurahs: [2, 4, 6, 12, 17, 18, 33, 36],
    featuredDuaIds: ['dua_nur_knowledge', 'dua_imran_forgiveness', 'dua_sulayman_gratitude'],
    suggestedJuz: [1, 2, 3, 13, 15, 22],
  },

  parent: {
    persona: 'parent',
    taglineEn: 'Raise Quran-literate children with stories, vocabulary & interactive tools',
    taglineAr: 'ربّ أبناء مرتبطين بالقرآن بالقصص والمفردات والأدوات التفاعلية',
    color: 'orange',
    milestones: [
      {
        id: 'par_m1',
        titleEn: 'Stories to Tell Your Children (Week 1)',
        titleAr: 'قصص تحكيها لأطفالك (الأسبوع الأول)',
        descEn: 'Start with the most beloved Quranic stories — complete with quizzes for kids.',
        descAr: 'ابدأ بأحب القصص القرآنية — مع اختبارات للأطفال.',
        estimatedDaysEn: '7 days',
        estimatedDaysAr: '٧ أيام',
        steps: [
          { id: 'par_m1_1', labelEn: 'Read Story of Musa with kids quiz', labelAr: 'اقرأ قصة موسى مع اختبار الأطفال', route: '/stories', type: 'read' },
          { id: 'par_m1_2', labelEn: 'Read Story of Yusuf (best of stories)', labelAr: 'اقرأ قصة يوسف (أحسن القصص)', route: '/stories', type: 'read' },
          { id: 'par_m1_3', labelEn: 'Try the daily quiz with your children', labelAr: 'جرّب تحدي اليوم مع أطفالك', route: '/challenge', type: 'practice' },
        ],
      },
      {
        id: 'par_m2',
        titleEn: 'Family Duʿā (Week 2)',
        titleAr: 'أدعية الأسرة (الأسبوع الثاني)',
        descEn: "Teach your children the prophets' supplications — a family practice.",
        descAr: 'علّم أطفالك أدعية الأنبياء — ممارسة أسرية.',
        estimatedDaysEn: '7 days',
        estimatedDaysAr: '٧ أيام',
        steps: [
          { id: 'par_m2_1', labelEn: 'Explore family & children duʿā', labelAr: 'استكشف أدعية الأسرة والأبناء', route: '/duas', type: 'reflect' },
          { id: 'par_m2_2', labelEn: 'Prayer for righteous family (Al-Furqan 74)', labelAr: 'دعاء الذرية الصالحة (الفرقان 74)', route: '/quran/25', type: 'read' },
          { id: 'par_m2_3', labelEn: 'Read Luqman\'s advice to his son (31:12-19)', labelAr: 'اقرأ نصائح لقمان لابنه (31:12-19)', route: '/quran/31', type: 'read' },
        ],
      },
      {
        id: 'par_m3',
        titleEn: 'Word of the Day Together (Ongoing)',
        titleAr: 'كلمة اليوم معاً (مستمر)',
        descEn: 'A shared daily vocabulary ritual — one Quranic word learned as a family.',
        descAr: 'طقس يومي مشترك لتعلم مفردة قرآنية كأسرة.',
        estimatedDaysEn: 'Daily habit',
        estimatedDaysAr: 'عادة يومية',
        steps: [
          { id: 'par_m3_1', labelEn: 'Check today\'s word of the day on home page', labelAr: 'تحقق من كلمة اليوم في الصفحة الرئيسية', route: '/', type: 'practice' },
          { id: 'par_m3_2', labelEn: 'Set a Khatmah reading goal', labelAr: 'حدد هدفاً لختمة القرآن', route: '/reading-plan', type: 'practice' },
          { id: 'par_m3_3', labelEn: 'Explore 99 Names of Allah with children', labelAr: 'استكشف أسماء الله الحسنى مع الأطفال', route: '/asma-allah', type: 'explore' },
        ],
      },
    ],
    featuredSurahs: [12, 18, 19, 25, 31, 37],
    featuredDuaIds: ['dua_furqan_family', 'dua_ibrahim_parents', 'dua_isra_parents_mercy', 'dua_zakariyya_child'],
    suggestedJuz: [30, 16, 17, 21],
  },

  arabic_learner: {
    persona: 'arabic_learner',
    taglineEn: 'Learn Quranic Arabic through roots, vocabulary & grammar analysis',
    taglineAr: 'تعلم عربية القرآن من خلال الجذور والمفردات والتحليل النحوي',
    color: 'teal',
    milestones: [
      {
        id: 'ar_m1',
        titleEn: 'Root System & Core Vocabulary (Week 1)',
        titleAr: 'نظام الجذور والمفردات الأساسية (الأسبوع الأول)',
        descEn: 'Quranic Arabic is built on 3-letter roots — master the pattern, not the word.',
        descAr: 'عربية القرآن تقوم على الجذور الثلاثية — أتقن النمط لا الكلمة.',
        estimatedDaysEn: '7 days',
        estimatedDaysAr: '٧ أيام',
        steps: [
          { id: 'ar_m1_1', labelEn: 'Study word of the day (root + meaning)', labelAr: 'ادرس كلمة اليوم (الجذر والمعنى)', route: '/', type: 'practice' },
          { id: 'ar_m1_2', labelEn: 'Explore vocabulary list', labelAr: 'استكشف قائمة المفردات', route: '/tools/vocabulary', type: 'explore' },
          { id: 'ar_m1_3', labelEn: 'Hover over words in the Quran for meanings', labelAr: 'مرّر على الكلمات في القرآن لرؤية المعاني', route: '/mushaf', type: 'practice' },
          { id: 'ar_m1_4', labelEn: 'Read Al-Fatihah in morphological view', labelAr: 'اقرأ الفاتحة مع التحليل الصرفي', route: '/quran/1', type: 'read' },
        ],
      },
      {
        id: 'ar_m2',
        titleEn: 'Grammar Analysis in Context (Week 2–3)',
        titleAr: 'التحليل النحوي في السياق (الأسبوع ٢–٣)',
        descEn: 'See Quranic Arabic grammar in action — POS tags, verb forms, and patterns.',
        descAr: 'شاهد نحو عربية القرآن بالعمل — علامات التشكيل وأوزان الأفعال والأنماط.',
        estimatedDaysEn: '14 days',
        estimatedDaysAr: '١٤ يوماً',
        steps: [
          { id: 'ar_m2_1', labelEn: 'Use the morphological analysis in QuranPage', labelAr: 'استخدم التحليل الصرفي في صفحة القرآن', route: '/quran/2', type: 'practice' },
          { id: 'ar_m2_2', labelEn: 'Search for a root pattern across the Quran', labelAr: 'ابحث عن نمط جذر عبر القرآن', route: '/search', type: 'practice' },
          { id: 'ar_m2_3', labelEn: 'Study duʿā with transliteration', labelAr: 'ادرس الأدعية مع الترجمة الصوتية', route: '/duas', type: 'practice' },
          { id: 'ar_m2_4', labelEn: 'Explore short surahs (Juz 30) word by word', labelAr: 'استكشف سور قصيرة (جزء عم) كلمة بكلمة', route: '/juz', type: 'explore' },
        ],
      },
      {
        id: 'ar_m3',
        titleEn: 'Reading Fluency (Month 2)',
        titleAr: 'طلاقة القراءة (الشهر الثاني)',
        descEn: 'Build reading speed with graduated surah complexity.',
        descAr: 'ابنِ سرعة القراءة بالسور المتدرجة في الصعوبة.',
        estimatedDaysEn: '30 days',
        estimatedDaysAr: '٣٠ يوماً',
        steps: [
          { id: 'ar_m3_1', labelEn: 'Complete Juz 30 reading in Mushaf', labelAr: 'أكمل قراءة الجزء الثلاثين في المصحف', route: '/mushaf', type: 'read' },
          { id: 'ar_m3_2', labelEn: 'Practice Tasmeeʿ (oral recitation check)', labelAr: 'مارس التسميع (فحص التلاوة الشفهية)', route: '/tasmee', type: 'memorize' },
          { id: 'ar_m3_3', labelEn: 'Try the memorization tools', labelAr: 'جرّب أدوات التحفيظ', route: '/memorization', type: 'memorize' },
        ],
      },
    ],
    featuredSurahs: [1, 2, 12, 36, 67, 78, 103, 112],
    featuredDuaIds: ['dua_nur_knowledge', 'dua_musa_guidance', 'dua_fatiha_guidance'],
    suggestedJuz: [30, 1, 12],
  },

  memorizer: {
    persona: 'memorizer',
    taglineEn: 'Systematic hifz with AI-powered recall tools',
    taglineAr: 'حفظ منهجي مع أدوات مراجعة مدعومة بالذكاء الاصطناعي',
    color: 'purple',
    milestones: [
      {
        id: 'mem_m1',
        titleEn: 'Set Your Memorization Foundation',
        titleAr: 'ضع أسس حفظك',
        descEn: 'Build the habit first — then scale the pace.',
        descAr: 'ابنِ العادة أولاً — ثم وسّع الوتيرة.',
        estimatedDaysEn: '7 days',
        estimatedDaysAr: '٧ أيام',
        steps: [
          { id: 'mem_m1_1', labelEn: 'Set a Khatmah or memorization target date', labelAr: 'حدد تاريخاً لختمة القرآن أو الحفظ', route: '/reading-plan', type: 'practice' },
          { id: 'mem_m1_2', labelEn: 'Explore the Memorization Intelligence tools', labelAr: 'استكشف أدوات ذكاء الحفظ', route: '/memorization', type: 'explore' },
          { id: 'mem_m1_3', labelEn: 'Try Tasmeeʿ (recite & get corrected by AI)', labelAr: 'جرّب التسميع (تلاوة مع تصحيح الذكاء)', route: '/tasmee', type: 'memorize' },
          { id: 'mem_m1_4', labelEn: 'Build your reading streak', labelAr: 'ابنِ سلسلتك اليومية', route: '/', type: 'practice' },
        ],
      },
      {
        id: 'mem_m2',
        titleEn: 'Understanding What You Memorize',
        titleAr: 'فهم ما تحفظه',
        descEn: "Hifz without understanding is prone to mistakes — context helps retention.",
        descAr: 'الحفظ بلا فهم عرضة للخطأ — السياق يساعد على الاحتفاظ.',
        estimatedDaysEn: '14 days',
        estimatedDaysAr: '١٤ يوماً',
        steps: [
          { id: 'mem_m2_1', labelEn: 'Read tafsir for verses you\'re memorizing', labelAr: 'اقرأ تفسير ما تحفظه', route: '/ask', type: 'reflect' },
          { id: 'mem_m2_2', labelEn: 'Explore connections between memorized verses', labelAr: 'استكشف الروابط بين الآيات المحفوظة', route: '/similarity', type: 'explore' },
          { id: 'mem_m2_3', labelEn: 'Explore surah structure in Surah Atlas', labelAr: 'استكشف بنية السورة في أطلس السور', route: '/surah-atlas', type: 'explore' },
          { id: 'mem_m2_4', labelEn: 'Bookmark difficult verses for review', labelAr: 'ضع إشارات على الآيات الصعبة للمراجعة', route: '/mushaf', type: 'practice' },
        ],
      },
      {
        id: 'mem_m3',
        titleEn: 'Systematic Review Cycle',
        titleAr: 'دورة المراجعة المنهجية',
        descEn: 'Regular testing and review is the key to long-term retention.',
        descAr: 'الاختبار المنتظم والمراجعة هما مفتاح الحفظ الدائم.',
        estimatedDaysEn: 'Ongoing',
        estimatedDaysAr: 'مستمر',
        steps: [
          { id: 'mem_m3_1', labelEn: 'Daily: Tasmeeʿ review session', labelAr: 'يومياً: جلسة مراجعة بالتسميع', route: '/tasmee', type: 'memorize' },
          { id: 'mem_m3_2', labelEn: 'Weekly: Daily challenge quiz', labelAr: 'أسبوعياً: اختبار تحدي اليوم', route: '/challenge', type: 'practice' },
          { id: 'mem_m3_3', labelEn: 'Review bookmarked verses', labelAr: 'راجع الآيات المحفوظة', route: '/bookmarks', type: 'reflect' },
          { id: 'mem_m3_4', labelEn: 'Track juz completion in Juz Navigator', labelAr: 'تتبع إتمام الأجزاء في مستكشف الأجزاء', route: '/juz', type: 'practice' },
        ],
      },
    ],
    featuredSurahs: [2, 3, 18, 36, 55, 67, 78],
    featuredDuaIds: ['dua_musa_guidance', 'dua_nur_knowledge', 'dua_baqarah_burden'],
    suggestedJuz: [30, 29, 28, 1],
  },
};

export const STEP_TYPE_ICONS: Record<LearningStep['type'], string> = {
  read: '📖',
  explore: '🔍',
  practice: '✏️',
  reflect: '🤲',
  memorize: '🧠',
};

export const STEP_TYPE_LABELS: Record<LearningStep['type'], { en: string; ar: string }> = {
  read:     { en: 'Read', ar: 'اقرأ' },
  explore:  { en: 'Explore', ar: 'استكشف' },
  practice: { en: 'Practice', ar: 'تدرّب' },
  reflect:  { en: 'Reflect', ar: 'تدبّر' },
  memorize: { en: 'Memorize', ar: 'احفظ' },
};
