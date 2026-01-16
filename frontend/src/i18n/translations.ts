export type Language = 'ar' | 'en';

export interface Translations {
  [key: string]: {
    ar: string;
    en: string;
  };
}

export const translations: Translations = {
  // Navigation
  nav_home: {
    ar: 'الرئيسية',
    en: 'Home',
  },
  nav_stories: {
    ar: 'قصص القرآن',
    en: 'Quran Stories',
  },
  nav_ask: {
    ar: 'اسأل',
    en: 'Ask',
  },
  nav_sources: {
    ar: 'المصادر',
    en: 'Sources',
  },
  nav_tools: {
    ar: 'الأدوات',
    en: 'Tools',
  },
  nav_explorer: {
    ar: 'المستكشف',
    en: 'Explorer',
  },
  nav_atlas: {
    ar: 'الأطلس',
    en: 'Atlas',
  },
  nav_concepts: {
    ar: 'المفاهيم',
    en: 'Concepts',
  },
  nav_themes: {
    ar: 'المحاور',
    en: 'Themes',
  },
  nav_miracles: {
    ar: 'الآيات',
    en: 'Miracles',
  },
  nav_similarity: {
    ar: 'صلة الآيات',
    en: 'Verse Links',
  },
  nav_mushaf: {
    ar: 'المصحف',
    en: 'Mushaf',
  },

  // Common
  app_title: {
    ar: 'تدبر',
    en: 'Tadabbur-AI',
  },
  app_subtitle: {
    ar: 'منصة معرفة قرآنية مبنية على المصادر',
    en: 'RAG-Grounded Quranic Knowledge Platform',
  },
  loading: {
    ar: 'جاري التحميل...',
    en: 'Loading...',
  },
  error: {
    ar: 'حدث خطأ',
    en: 'An error occurred',
  },
  search: {
    ar: 'بحث',
    en: 'Search',
  },
  close: {
    ar: 'إغلاق',
    en: 'Close',
  },

  // Search page
  nav_search: {
    ar: 'البحث',
    en: 'Search',
  },
  search_title: {
    ar: 'البحث في القرآن الكريم',
    en: 'Search the Holy Quran',
  },
  search_subtitle: {
    ar: 'ابحث عن الكلمات والعبارات مع التحليل الدلالي والنحوي',
    en: 'Search for words and phrases with semantic and grammatical analysis',
  },
  search_placeholder: {
    ar: 'اكتب كلمة أو عبارة للبحث...',
    en: 'Type a word or phrase to search...',
  },
  search_button: {
    ar: 'ابحث',
    en: 'Search',
  },
  search_results: {
    ar: 'نتائج البحث',
    en: 'Search Results',
  },
  search_total_matches: {
    ar: 'إجمالي النتائج',
    en: 'Total Matches',
  },
  search_no_results: {
    ar: 'لم يتم العثور على نتائج',
    en: 'No results found',
  },
  search_try_different: {
    ar: 'جرب كلمة مختلفة أو تحقق من الإملاء',
    en: 'Try a different word or check the spelling',
  },
  search_analytics: {
    ar: 'تحليلات الكلمة',
    en: 'Word Analytics',
  },
  search_distribution: {
    ar: 'التوزيع',
    en: 'Distribution',
  },
  search_by_sura: {
    ar: 'حسب السورة',
    en: 'By Sura',
  },
  search_by_juz: {
    ar: 'حسب الجزء',
    en: 'By Juz',
  },
  search_semantic: {
    ar: 'البحث الدلالي',
    en: 'Semantic Search',
  },
  search_semantic_desc: {
    ar: 'تضمين المصطلحات ذات الصلة في البحث',
    en: 'Include related terms in search',
  },
  search_related_terms: {
    ar: 'المصطلحات المرتبطة',
    en: 'Related Terms',
  },
  search_exact_match: {
    ar: 'تطابق تام',
    en: 'Exact Match',
  },
  search_partial_match: {
    ar: 'تطابق جزئي',
    en: 'Partial Match',
  },
  search_relevance: {
    ar: 'الصلة',
    en: 'Relevance',
  },
  search_occurrences: {
    ar: 'مرة',
    en: 'occurrences',
  },
  search_sample_words: {
    ar: 'كلمات مقترحة',
    en: 'Sample Words',
  },
  search_load_more: {
    ar: 'تحميل المزيد',
    en: 'Load More',
  },
  search_filter_sura: {
    ar: 'تصفية حسب السورة',
    en: 'Filter by Sura',
  },
  search_all_suras: {
    ar: 'جميع السور',
    en: 'All Suras',
  },

  // Stories
  stories_title: {
    ar: 'قصص القرآن الكريم',
    en: 'Stories of the Holy Quran',
  },
  stories_subtitle: {
    ar: 'استكشف القصص القرآنية وترابطها عبر السور',
    en: 'Explore Quranic narratives and their connections across surahs',
  },
  story_segments: {
    ar: 'المقاطع',
    en: 'Segments',
  },
  story_connections: {
    ar: 'الروابط',
    en: 'Connections',
  },
  story_themes: {
    ar: 'المواضيع',
    en: 'Themes',
  },
  story_figures: {
    ar: 'الشخصيات',
    en: 'Figures',
  },
  view_graph: {
    ar: 'عرض الرسم البياني',
    en: 'View Graph',
  },
  view_list: {
    ar: 'عرض القائمة',
    en: 'View List',
  },

  // Categories
  category_prophet: {
    ar: 'قصص الأنبياء',
    en: 'Prophet Stories',
  },
  category_nation: {
    ar: 'قصص الأمم',
    en: 'Nation Stories',
  },
  category_parable: {
    ar: 'الأمثال',
    en: 'Parables',
  },
  category_historical: {
    ar: 'الأحداث التاريخية',
    en: 'Historical Events',
  },

  // Ask/RAG
  ask_title: {
    ar: 'اسأل عن القرآن',
    en: 'Ask About the Quran',
  },
  ask_subtitle: {
    ar: 'احصل على إجابات مستندة إلى المصادر العلمية',
    en: 'Get answers grounded in scholarly sources',
  },
  ask_placeholder: {
    ar: 'اكتب سؤالك هنا...',
    en: 'Type your question here...',
  },
  ask_button: {
    ar: 'اسأل',
    en: 'Ask',
  },
  citations: {
    ar: 'المصادر',
    en: 'Citations',
  },
  confidence: {
    ar: 'الثقة',
    en: 'Confidence',
  },
  scholarly_consensus: {
    ar: 'إجماع العلماء',
    en: 'Scholarly Consensus',
  },

  // Tafseer
  tafseer: {
    ar: 'التفسير',
    en: 'Tafseer',
  },
  tafseer_sources: {
    ar: 'مصادر التفسير',
    en: 'Tafseer Sources',
  },
  view_tafseer: {
    ar: 'عرض التفسير',
    en: 'View Tafseer',
  },

  // Verse
  verse: {
    ar: 'آية',
    en: 'Verse',
  },
  surah: {
    ar: 'سورة',
    en: 'Surah',
  },
  juz: {
    ar: 'جزء',
    en: 'Juz',
  },
  page: {
    ar: 'صفحة',
    en: 'Page',
  },

  // Warnings
  warning_fiqh: {
    ar: 'ملاحظة: هذه المعلومات للأغراض التعليمية فقط وليست فتوى',
    en: 'Note: This is informational only, not a religious ruling (fatwa)',
  },
  warning_no_sources: {
    ar: 'يتطلب هذا استشارة علمية إضافية',
    en: 'This requires further scholarly consultation',
  },

  // Footer
  footer_disclaimer: {
    ar: 'جميع الإجابات مستندة إلى مصادر تفسيرية موثقة',
    en: 'All answers are grounded in authenticated tafseer sources',
  },

  // Sample questions
  sample_questions: {
    ar: 'أسئلة مقترحة',
    en: 'Sample Questions',
  },

  // Error messages
  error_processing: {
    ar: 'حدث خطأ أثناء معالجة السؤال',
    en: 'An error occurred while processing the question',
  },

  // Similarity page
  similarity_title: {
    ar: 'صلة الآيات',
    en: 'Verse Connections',
  },
  similarity_subtitle: {
    ar: 'اكتشف الآيات المتشابهة حسب الموضوع والمعنى والجذور اللغوية',
    en: 'Discover similar verses by theme, meaning, and linguistic roots',
  },
  similarity_search_placeholder: {
    ar: 'أدخل رقم السورة:الآية (مثل 2:255) أو نص الآية...',
    en: 'Enter sura:verse (e.g., 2:255) or verse text...',
  },
  similarity_search_button: {
    ar: 'ابحث عن المتشابهات',
    en: 'Find Similar',
  },
  similarity_no_results: {
    ar: 'لم يتم العثور على آيات متشابهة',
    en: 'No similar verses found',
  },
  similarity_results_count: {
    ar: 'آية متشابهة',
    en: 'similar verses',
  },
  similarity_connection_type: {
    ar: 'نوع الصلة',
    en: 'Connection Type',
  },
  similarity_filter_theme: {
    ar: 'تصفية حسب الموضوع',
    en: 'Filter by Theme',
  },
  similarity_min_score: {
    ar: 'الحد الأدنى للتشابه',
    en: 'Minimum Similarity',
  },
  similarity_exclude_same_sura: {
    ar: 'استثناء نفس السورة',
    en: 'Exclude Same Sura',
  },
  similarity_popular_verses: {
    ar: 'آيات شائعة للبحث',
    en: 'Popular Verses to Explore',
  },
};

// Story categories translation map
export const categoryTranslations: Record<string, { ar: string; en: string }> = {
  prophet: { ar: 'قصص الأنبياء', en: 'Prophet' },
  nation: { ar: 'قصص الأمم', en: 'Nation' },
  parable: { ar: 'أمثال', en: 'Parable' },
  historical: { ar: 'تاريخية', en: 'Historical' },
  righteous: { ar: 'الصالحين', en: 'Righteous' },
};

// Theme translations - comprehensive list covering ALL semantic tags in data
export const themeTranslations: Record<string, { ar: string; en: string }> = {
  // Core themes
  patience: { ar: 'الصبر', en: 'patience' },
  obedience: { ar: 'الطاعة', en: 'obedience' },
  repentance: { ar: 'التوبة', en: 'repentance' },
  creation: { ar: 'الخلق', en: 'creation' },
  arrogance: { ar: 'الكبر', en: 'arrogance' },
  faith: { ar: 'الإيمان', en: 'faith' },
  trust: { ar: 'التوكل', en: 'trust' },
  justice: { ar: 'العدل', en: 'justice' },
  mercy: { ar: 'الرحمة', en: 'mercy' },
  gratitude: { ar: 'الشكر', en: 'gratitude' },
  forgiveness: { ar: 'المغفرة', en: 'forgiveness' },
  sacrifice: { ar: 'التضحية', en: 'sacrifice' },
  wisdom: { ar: 'الحكمة', en: 'wisdom' },
  guidance: { ar: 'الهداية', en: 'guidance' },
  monotheism: { ar: 'التوحيد', en: 'monotheism' },
  prophethood: { ar: 'النبوة', en: 'prophethood' },
  resurrection: { ar: 'البعث', en: 'resurrection' },
  punishment: { ar: 'العذاب', en: 'punishment' },
  deliverance: { ar: 'النجاة', en: 'deliverance' },
  trial: { ar: 'الابتلاء', en: 'trial' },
  family: { ar: 'الأسرة', en: 'family' },
  brotherhood: { ar: 'الأخوة', en: 'brotherhood' },
  jealousy: { ar: 'الحسد', en: 'jealousy' },
  dreams: { ar: 'الأحلام', en: 'dreams' },
  power: { ar: 'القوة', en: 'power' },
  protection: { ar: 'الحماية', en: 'protection' },
  travel: { ar: 'السفر', en: 'travel' },
  wealth: { ar: 'المال', en: 'wealth' },
  knowledge: { ar: 'العلم', en: 'knowledge' },
  miracle: { ar: 'المعجزة', en: 'miracle' },
  miracles: { ar: 'المعجزات', en: 'miracles' },
  leadership: { ar: 'القيادة', en: 'leadership' },
  dawah: { ar: 'الدعوة', en: 'dawah' },
  perseverance: { ar: 'الثبات', en: 'perseverance' },
  submission: { ar: 'الاستسلام', en: 'submission' },
  healing: { ar: 'الشفاء', en: 'healing' },
  worship: { ar: 'العبادة', en: 'worship' },
  // Additional themes from database
  acceptance: { ar: 'القبول', en: 'acceptance' },
  answered_prayer: { ar: 'استجابة الدعاء', en: 'answered_prayer' },
  ascension: { ar: 'الصعود', en: 'ascension' },
  chastity: { ar: 'العفة', en: 'chastity' },
  confronting_tyranny: { ar: 'مواجهة الطغيان', en: 'confronting_tyranny' },
  courage: { ar: 'الشجاعة', en: 'courage' },
  destruction: { ar: 'الهلاك', en: 'destruction' },
  devotion: { ar: 'الإخلاص', en: 'devotion' },
  disobedience: { ar: 'العصيان', en: 'disobedience' },
  divine_mercy: { ar: 'الرحمة الإلهية', en: 'divine_mercy' },
  divine_planning: { ar: 'التدبير الإلهي', en: 'divine_planning' },
  divine_power: { ar: 'القدرة الإلهية', en: 'divine_power' },
  divine_protection: { ar: 'الحماية الإلهية', en: 'divine_protection' },
  divine_punishment: { ar: 'العقاب الإلهي', en: 'divine_punishment' },
  divine_support: { ar: 'التأييد الإلهي', en: 'divine_support' },
  father_of_prophets: { ar: 'أبو الأنبياء', en: 'father_of_prophets' },
  first_murder: { ar: 'أول جريمة قتل', en: 'first_murder' },
  hajj: { ar: 'الحج', en: 'hajj' },
  honesty: { ar: 'الصدق', en: 'honesty' },
  humility: { ar: 'التواضع', en: 'humility' },
  kaaba: { ar: 'الكعبة', en: 'kaaba' },
  kingdom: { ar: 'الملك', en: 'kingdom' },
  liberation: { ar: 'التحرير', en: 'liberation' },
  miraculous_birth: { ar: 'الولادة المعجزة', en: 'miraculous_birth' },
  morality: { ar: 'الأخلاق', en: 'morality' },
  parenting: { ar: 'التربية', en: 'parenting' },
  purity: { ar: 'الطهارة', en: 'purity' },
  questioning: { ar: 'التساؤل', en: 'questioning' },
  reconciliation: { ar: 'المصالحة', en: 'reconciliation' },
  righteousness: { ar: 'الصلاح', en: 'righteousness' },
  salvation: { ar: 'الخلاص', en: 'salvation' },
  signs: { ar: 'الآيات', en: 'signs' },
  time: { ar: 'الزمن', en: 'time' },
  trade_ethics: { ar: 'أخلاق التجارة', en: 'trade_ethics' },
  transformation: { ar: 'التحول', en: 'transformation' },
  trickery: { ar: 'المكر', en: 'trickery' },

  // Missing themes from manifest (Phase 10 fix)
  belief: { ar: 'الاعتقاد', en: 'Belief' },
  trade: { ar: 'التجارة', en: 'Trade' },
  unseen: { ar: 'الغيب', en: 'The Unseen' },
  end_times: { ar: 'آخر الزمان', en: 'End Times' },
  idolatry: { ar: 'عبادة الأصنام', en: 'Idolatry' },
  weakness: { ar: 'الضعف', en: 'Weakness' },
  logic: { ar: 'المنطق', en: 'Logic' },
  rejection: { ar: 'الرفض', en: 'Rejection' },

  // ============================================================
  // COMPREHENSIVE SEMANTIC TAGS FROM STORY DATA (dhul_qarnayn_enhanced.json etc.)
  // ============================================================

  // Revelation and inquiry tags
  revelation: { ar: 'الوحي', en: 'revelation' },
  question: { ar: 'السؤال', en: 'question' },
  historical_inquiry: { ar: 'التساؤل التاريخي', en: 'historical_inquiry' },

  // Divine empowerment tags
  divine_empowerment: { ar: 'التمكين الإلهي', en: 'divine_empowerment' },
  tamkeen: { ar: 'التمكين', en: 'tamkeen' },
  authority: { ar: 'السلطة', en: 'authority' },
  resources: { ar: 'الموارد', en: 'resources' },

  // Journey and direction tags
  west: { ar: 'الغرب', en: 'west' },
  east: { ar: 'الشرق', en: 'east' },
  sun_setting: { ar: 'غروب الشمس', en: 'sun_setting' },
  sun_rising: { ar: 'شروق الشمس', en: 'sun_rising' },
  exploration: { ar: 'الاستكشاف', en: 'exploration' },
  primitive_people: { ar: 'شعوب بدائية', en: 'primitive_people' },

  // Test and moral decision tags
  test: { ar: 'الاختبار', en: 'test' },
  test_of_prophet: { ar: 'اختبار النبي', en: 'test_of_prophet' },
  moral_decision: { ar: 'قرار أخلاقي', en: 'moral_decision' },
  moral_choice: { ar: 'الاختيار الأخلاقي', en: 'moral_choice' },
  restraint: { ar: 'ضبط النفس', en: 'restraint' },
  self_control: { ar: 'التحكم بالنفس', en: 'self_control' },

  // Service and generosity tags
  tawakkul: { ar: 'التوكل', en: 'tawakkul' },
  generosity: { ar: 'الكرم', en: 'generosity' },
  selfless_service: { ar: 'الخدمة بإخلاص', en: 'selfless_service' },
  refusing_payment: { ar: 'رفض الأجر', en: 'refusing_payment' },
  tribute: { ar: 'الخراج', en: 'tribute' },
  offer: { ar: 'العرض', en: 'offer' },
  service: { ar: 'الخدمة', en: 'service' },

  // Engineering and construction tags
  engineering: { ar: 'الهندسة', en: 'engineering' },
  construction: { ar: 'البناء', en: 'construction' },
  iron: { ar: 'الحديد', en: 'iron' },
  copper: { ar: 'النحاس', en: 'copper' },
  teamwork: { ar: 'العمل الجماعي', en: 'teamwork' },
  technology: { ar: 'التقنية', en: 'technology' },

  // Encounter and conflict tags
  encounter: { ar: 'اللقاء', en: 'encounter' },
  oppressed: { ar: 'المستضعفين', en: 'oppressed' },
  vulnerable_people: { ar: 'المستضعفون', en: 'vulnerable_people' },
  yajuj_majuj: { ar: 'يأجوج ومأجوج', en: 'yajuj_majuj' },
  corruption: { ar: 'الفساد', en: 'corruption' },
  plea_for_help: { ar: 'طلب النجدة', en: 'plea_for_help' },

  // Eschatology and divine tags
  eschatology: { ar: 'علم الآخرة', en: 'eschatology' },
  impermanence: { ar: 'الزوال', en: 'impermanence' },
  attribution_to_allah: { ar: 'نسب الفضل لله', en: 'attribution_to_allah' },
  divine_promise: { ar: 'الوعد الإلهي', en: 'divine_promise' },

  // Battle and conflict tags (Uhud, Badr, etc.)
  battle: { ar: 'المعركة', en: 'battle' },
  warfare: { ar: 'الحرب', en: 'warfare' },
  military: { ar: 'عسكري', en: 'military' },
  victory: { ar: 'النصر', en: 'victory' },
  defeat: { ar: 'الهزيمة', en: 'defeat' },
  martyrdom: { ar: 'الشهادة', en: 'martyrdom' },
  jihad: { ar: 'الجهاد', en: 'jihad' },
  defense: { ar: 'الدفاع', en: 'defense' },
  retreat: { ar: 'الانسحاب', en: 'retreat' },
  archers: { ar: 'الرماة', en: 'archers' },
  disobedience_battle: { ar: 'العصيان في المعركة', en: 'disobedience_battle' },

  // Hypocrisy and character tags
  hypocrisy: { ar: 'النفاق', en: 'hypocrisy' },
  munafiqun: { ar: 'المنافقون', en: 'munafiqun' },
  betrayal: { ar: 'الخيانة', en: 'betrayal' },
  cowardice: { ar: 'الجبن', en: 'cowardice' },
  treachery: { ar: 'الغدر', en: 'treachery' },
  doubt: { ar: 'الشك', en: 'doubt' },
  sincere_believers: { ar: 'المؤمنين الصادقين', en: 'sincere_believers' },

  // Lessons and reflection tags
  lessons: { ar: 'الدروس', en: 'lessons' },
  reflection: { ar: 'التأمل', en: 'reflection' },
  contemplation: { ar: 'التدبر', en: 'contemplation' },
  reminder: { ar: 'التذكير', en: 'reminder' },
  warning: { ar: 'التحذير', en: 'warning' },

  // Additional Islamic concepts
  taqwa: { ar: 'التقوى', en: 'taqwa' },
  iman: { ar: 'الإيمان', en: 'iman' },
  ihsan: { ar: 'الإحسان', en: 'ihsan' },
  shukr: { ar: 'الشكر', en: 'shukr' },
  sabr: { ar: 'الصبر', en: 'sabr' },
  tawbah: { ar: 'التوبة', en: 'tawbah' },
  istighfar: { ar: 'الاستغفار', en: 'istighfar' },
  dua: { ar: 'الدعاء', en: 'dua' },
  dhikr: { ar: 'الذكر', en: 'dhikr' },
  tawhid: { ar: 'التوحيد', en: 'tawhid' },
  shirk: { ar: 'الشرك', en: 'shirk' },
  kufr: { ar: 'الكفر', en: 'kufr' },
  nifaq: { ar: 'النفاق', en: 'nifaq' },

  // Place-related tags
  makkah: { ar: 'مكة', en: 'makkah' },
  madinah: { ar: 'المدينة', en: 'madinah' },
  uhud: { ar: 'أحد', en: 'uhud' },
  badr: { ar: 'بدر', en: 'badr' },
  jerusalem: { ar: 'القدس', en: 'jerusalem' },
  egypt: { ar: 'مصر', en: 'egypt' },
  sinai: { ar: 'سيناء', en: 'sinai' },

  // Prophetic mission tags
  risalah: { ar: 'الرسالة', en: 'risalah' },
  tabligh: { ar: 'التبليغ', en: 'tabligh' },
  hidayah: { ar: 'الهداية', en: 'hidayah' },
  inzar: { ar: 'الإنذار', en: 'inzar' },
  bashirah: { ar: 'البشارة', en: 'bashirah' },
  prophetic: { ar: 'نبوي', en: 'Prophetic' },

  // Angels and divine beings
  angels: { ar: 'الملائكة', en: 'angels' },
  angel: { ar: 'ملك', en: 'angel' },
  jibril: { ar: 'جبريل', en: 'Jibril' },

  // Idolatry and related
  idols: { ar: 'الأصنام', en: 'idols' },
  idol_worship: { ar: 'عبادة الأصنام', en: 'idol_worship' },
  breaking_idols: { ar: 'تحطيم الأصنام', en: 'breaking_idols' },
  forbidden_tree: { ar: 'الشجرة المحرمة', en: 'forbidden_tree' },
  khalifah: { ar: 'الخليفة', en: 'khalifah' },
  prostration: { ar: 'السجود', en: 'prostration' },

  // Divine help and intervention
  divine_help: { ar: 'النصر الإلهي', en: 'divine_help' },
  divine_victory: { ar: 'الفتح الإلهي', en: 'divine_victory' },

  // Peace and related
  peace: { ar: 'السلام', en: 'peace' },
  forgive: { ar: 'العفو', en: 'forgive' },

  // Story-specific tags
  sleep: { ar: 'النوم', en: 'sleep' },
  persecution: { ar: 'الاضطهاد', en: 'persecution' },
  lesson: { ar: 'العبرة', en: 'lesson' },
  hidden_wisdom: { ar: 'الحكمة الخفية', en: 'hidden_wisdom' },
  learning: { ar: 'التعلم', en: 'learning' },
  barrier: { ar: 'السد', en: 'barrier' },
  family_test: { ar: 'اختبار الأسرة', en: 'family_test' },
  arguing_with_idolaters: { ar: 'محاجة المشركين', en: 'arguing_with_idolaters' },
  miracle_birth: { ar: 'الولادة المعجزة', en: 'miracle_birth' },
  table: { ar: 'المائدة', en: 'table' },
  iram: { ar: 'إرم', en: 'iram' },
  rock_dwellings: { ar: 'البيوت الصخرية', en: 'rock_dwellings' },
  rain_of_stones: { ar: 'مطر الحجارة', en: 'rain_of_stones' },
  sheba: { ar: 'سبأ', en: 'sheba' },
  sea_parting: { ar: 'شق البحر', en: 'sea_parting' },
  exodus: { ar: 'الخروج', en: 'exodus' },
  tyrant: { ar: 'الطاغية', en: 'tyrant' },
  birds: { ar: 'الطيور', en: 'birds' },
  ants: { ar: 'النمل', en: 'ants' },
  miracle_child: { ar: 'الطفل المعجزة', en: 'miracle_child' },
  old_age: { ar: 'الشيخوخة', en: 'old_age' },
  fahisha: { ar: 'الفاحشة', en: 'fahisha' },
  homosexuality: { ar: 'اللواط', en: 'homosexuality' },
  she_camel: { ar: 'الناقة', en: 'she_camel' },
  whale: { ar: 'الحوت', en: 'whale' },
  darkness: { ar: 'الظلمات', en: 'darkness' },
  illness: { ar: 'المرض', en: 'illness' },
  fraud: { ar: 'الغش', en: 'fraud' },
  weights_measures: { ar: 'الكيل والميزان', en: 'weights_measures' },
  business: { ar: 'التجارة', en: 'business' },
  crow: { ar: 'الغراب', en: 'crow' },
  regret: { ar: 'الندم', en: 'regret' },
  hundred_years: { ar: 'مئة عام', en: 'hundred_years' },
  donkey: { ar: 'الحمار', en: 'donkey' },
  kingship: { ar: 'الملوكية', en: 'kingship' },
  river_test: { ar: 'اختبار النهر', en: 'river_test' },
  goliath: { ar: 'جالوت', en: 'goliath' },
  zabur: { ar: 'الزبور', en: 'zabur' },
  psalms: { ar: 'المزامير', en: 'psalms' },
  fishing: { ar: 'الصيد', en: 'fishing' },
  apes: { ar: 'القردة', en: 'apes' },
  throne: { ar: 'العرش', en: 'throne' },
  speed: { ar: 'السرعة', en: 'speed' },
  elevated: { ar: 'الرفعة', en: 'elevated' },

  // Battle of Badr tags
  departure: { ar: 'الخروج', en: 'departure' },
  reluctance: { ar: 'التردد', en: 'reluctance' },
  divine_plan: { ar: 'التدبير الإلهي', en: 'divine_plan' },
  choice: { ar: 'الاختيار', en: 'choice' },
  reinforcement: { ar: 'الإمداد', en: 'reinforcement' },
  tranquility: { ar: 'السكينة', en: 'tranquility' },
  divine_action: { ar: 'الفعل الإلهي', en: 'divine_action' },
  tyrant_death: { ar: 'مقتل الطاغية', en: 'tyrant_death' },
  furqan: { ar: 'الفرقان', en: 'furqan' },

  // Isra and Miraj tags
  glorification: { ar: 'التسبيح', en: 'glorification' },
  aqsa: { ar: 'الأقصى', en: 'aqsa' },
  holiness: { ar: 'القدسية', en: 'holiness' },
  divine_wisdom: { ar: 'الحكمة الإلهية', en: 'divine_wisdom' },
  hearing: { ar: 'السمع', en: 'hearing' },
  seeing: { ar: 'البصر', en: 'seeing' },

  // Conquest of Mecca tags
  conquest: { ar: 'الفتح', en: 'conquest' },
  divine_gift: { ar: 'العطاء الإلهي', en: 'divine_gift' },
  increase: { ar: 'الزيادة', en: 'increase' },
  fulfillment: { ar: 'التحقق', en: 'fulfillment' },
  safety: { ar: 'الأمان', en: 'safety' },
  islam: { ar: 'الإسلام', en: 'islam' },
  truth: { ar: 'الحق', en: 'truth' },

  // Ifk (Slander) tags
  slander: { ar: 'الإفك', en: 'slander' },
  falsehood: { ar: 'الباطل', en: 'falsehood' },
  good_opinion: { ar: 'حسن الظن', en: 'good_opinion' },
  innocence: { ar: 'البراءة', en: 'innocence' },
  vindication: { ar: 'التبرئة', en: 'vindication' },

  // Hudaybiyyah tags
  treaty: { ar: 'المعاهدة', en: 'treaty' },
  pledge: { ar: 'البيعة', en: 'pledge' },
  ridwan: { ar: 'الرضوان', en: 'ridwan' },
  tree: { ar: 'الشجرة', en: 'tree' },
  satisfaction: { ar: 'الرضا', en: 'satisfaction' },
  hearts: { ar: 'القلوب', en: 'hearts' },
  spoils: { ar: 'الغنائم', en: 'spoils' },

  // Idris tags
  mention: { ar: 'الذكر', en: 'mention' },
  station: { ar: 'المكانة', en: 'station' },

  // Additional story tags
  caravan: { ar: 'القافلة', en: 'caravan' },
  slavery: { ar: 'العبودية', en: 'slavery' },
  resistance: { ar: 'المقاومة', en: 'resistance' },
  abandonment: { ar: 'التخلي', en: 'abandonment' },
  cup: { ar: 'الصواع', en: 'cup' },
  brother: { ar: 'الأخ', en: 'brother' },
  dream_fulfilled: { ar: 'تحقق الرؤيا', en: 'dream_fulfilled' },
  youth: { ar: 'الشباب', en: 'youth' },
  escape: { ar: 'الهروب', en: 'escape' },
  wonder: { ar: 'العجب', en: 'wonder' },
  discovery: { ar: 'الاكتشاف', en: 'discovery' },
  mashallah: { ar: 'ما شاء الله', en: 'mashallah' },
  denial: { ar: 'الإنكار', en: 'denial' },
  fate: { ar: 'القدر', en: 'fate' },
  orphans: { ar: 'اليتامى', en: 'orphans' },
  wisdom_revealed: { ar: 'الحكمة المكشوفة', en: 'wisdom_revealed' },
  special_knowledge: { ar: 'العلم اللدني', en: 'special_knowledge' },
  knowledge_seeking: { ar: 'طلب العلم', en: 'knowledge_seeking' },
  ship: { ar: 'السفينة', en: 'ship' },
  means: { ar: 'الأسباب', en: 'means' },
  new_beginning: { ar: 'البداية الجديدة', en: 'new_beginning' },
  judi: { ar: 'الجودي', en: 'judi' },
  methods: { ar: 'الأساليب', en: 'methods' },
  persistence: { ar: 'الإصرار', en: 'persistence' },
  finality: { ar: 'النهائية', en: 'finality' },
  preparation: { ar: 'الاستعداد', en: 'preparation' },
  reasoning: { ar: 'الاستدلال', en: 'reasoning' },
  stars: { ar: 'النجوم', en: 'stars' },
  challenge: { ar: 'التحدي', en: 'challenge' },
  proof: { ar: 'الحجة', en: 'proof' },
  blessed_land: { ar: 'الأرض المباركة', en: 'blessed_land' },
  covenant: { ar: 'الميثاق', en: 'covenant' },

  // Community and society tags
  ummah: { ar: 'الأمة', en: 'ummah' },
  jamaat: { ar: 'الجماعة', en: 'jamaat' },
  shura: { ar: 'الشورى', en: 'shura' },
  unity: { ar: 'الوحدة', en: 'unity' },
  division: { ar: 'الفرقة', en: 'division' },
  community: { ar: 'المجتمع', en: 'community' },

  // Additional moral qualities
  truthfulness: { ar: 'الصدق', en: 'truthfulness' },
  trustworthiness: { ar: 'الأمانة', en: 'trustworthiness' },
  sincerity: { ar: 'الإخلاص', en: 'sincerity' },
  modesty: { ar: 'الحياء', en: 'modesty' },
  kindness: { ar: 'اللطف', en: 'kindness' },
  compassion: { ar: 'الشفقة', en: 'compassion' },
  respect: { ar: 'الاحترام', en: 'respect' },
  honor: { ar: 'الشرف', en: 'honor' },

  // Timeline/narrative tags
  introduction: { ar: 'المقدمة', en: 'introduction' },
  development: { ar: 'التطور', en: 'development' },
  climax: { ar: 'الذروة', en: 'climax' },
  resolution: { ar: 'الحل', en: 'resolution' },
  conclusion: { ar: 'الخاتمة', en: 'conclusion' },

  // ============================================================
  // NEW STORY TAGS - Prophet Ilyas, Al-Yasa, Dhul-Kifl, Ahzab, Ya-Sin Town, etc.
  // ============================================================

  // Prophet Ilyas tags
  baal: { ar: 'بعل', en: 'Baal' },
  baal_worship: { ar: 'عبادة بعل', en: 'baal_worship' },
  mission: { ar: 'الرسالة', en: 'mission' },
  sending: { ar: 'الإرسال', en: 'sending' },
  legacy: { ar: 'الإرث', en: 'legacy' },
  bani_israil: { ar: 'بني إسرائيل', en: 'bani_israil' },

  // Prophet Al-Yasa and Dhul-Kifl tags
  chosen: { ar: 'المصطفى', en: 'chosen' },
  outstanding: { ar: 'الأخيار', en: 'outstanding' },

  // Battle of Ahzab/Khandaq tags
  siege: { ar: 'الحصار', en: 'siege' },
  confederates: { ar: 'الأحزاب', en: 'confederates' },
  armies: { ar: 'الجيوش', en: 'armies' },
  trench: { ar: 'الخندق', en: 'trench' },
  fear: { ar: 'الخوف', en: 'fear' },
  shaking: { ar: 'الزلزلة', en: 'shaking' },
  steadfastness: { ar: 'الثبات', en: 'steadfastness' },
  enemy_retreat: { ar: 'انسحاب العدو', en: 'enemy_retreat' },
  judgment: { ar: 'الحكم', en: 'judgment' },

  // People of the Town (Ya-Sin) tags
  town: { ar: 'القرية', en: 'town' },
  messengers: { ar: 'الرسل', en: 'messengers' },
  escalation: { ar: 'التصعيد', en: 'escalation' },
  believer: { ar: 'المؤمن', en: 'believer' },
  heroism: { ar: 'البطولة', en: 'heroism' },
  wish: { ar: 'الأمنية', en: 'wish' },
  blast: { ar: 'الصيحة', en: 'blast' },
  stoning: { ar: 'الرجم', en: 'stoning' },
  threat: { ar: 'التهديد', en: 'threat' },
  extinguished: { ar: 'الخمود', en: 'extinguished' },

  // People of the Rass and Tubba tags
  nations: { ar: 'الأمم', en: 'nations' },
  destroyed_nations: { ar: 'الأمم الهالكة', en: 'destroyed_nations' },
  examples: { ar: 'الأمثال', en: 'examples' },
  unknown_identity: { ar: 'هوية مجهولة', en: 'unknown_identity' },
  yemen: { ar: 'اليمن', en: 'yemen' },
  kings: { ar: 'الملوك', en: 'kings' },
  criminals: { ar: 'المجرمون', en: 'criminals' },
  comparison: { ar: 'المقارنة', en: 'comparison' },
  deniers: { ar: 'المكذبون', en: 'deniers' },

  // 'Abasa (Blind Man) story tags
  correction: { ar: 'العتاب', en: 'correction' },
  blind_man: { ar: 'الأعمى', en: 'blind_man' },
  purification: { ar: 'التزكية', en: 'purification' },
  benefit: { ar: 'النفع', en: 'benefit' },
  priorities: { ar: 'الأولويات', en: 'priorities' },
  self_sufficient: { ar: 'المستغني', en: 'self_sufficient' },
  responsibility: { ar: 'المسؤولية', en: 'responsibility' },
  seeker: { ar: 'الساعي', en: 'seeker' },
  fear_of_allah: { ar: 'الخشية', en: 'fear_of_allah' },
  distracted: { ar: 'التلهي', en: 'distracted' },

  // Bani Nadir expulsion tags
  expulsion: { ar: 'الإجلاء', en: 'expulsion' },
  jews: { ar: 'اليهود', en: 'jews' },
  first_gathering: { ar: 'أول الحشر', en: 'first_gathering' },
  fortresses: { ar: 'الحصون', en: 'fortresses' },
  surprise: { ar: 'المفاجأة', en: 'surprise' },
  divine_decree: { ar: 'القضاء الإلهي', en: 'divine_decree' },
  terror: { ar: 'الرعب', en: 'terror' },
  lies: { ar: 'الكذب', en: 'lies' },

  // People of Aiyka tags
  aiyka: { ar: 'الأيكة', en: 'aiyka' },
  forest: { ar: 'الغابة', en: 'forest' },
  shadow: { ar: 'الظلة', en: 'shadow' },
  shadow_day: { ar: 'يوم الظلة', en: 'shadow_day' },
  accusation: { ar: 'الاتهام', en: 'accusation' },
};

// Main figures translations
export const figureTranslations: Record<string, { ar: string; en: string }> = {
  // Prophets
  Adam: { ar: 'آدم', en: 'Adam' },
  Nuh: { ar: 'نوح', en: 'Nuh' },
  Ibrahim: { ar: 'إبراهيم', en: 'Ibrahim' },
  Ismail: { ar: 'إسماعيل', en: 'Ismail' },
  Ishaq: { ar: 'إسحاق', en: 'Ishaq' },
  Yaqub: { ar: 'يعقوب', en: 'Yaqub' },
  Yusuf: { ar: 'يوسف', en: 'Yusuf' },
  Musa: { ar: 'موسى', en: 'Musa' },
  Harun: { ar: 'هارون', en: 'Harun' },
  Dawud: { ar: 'داود', en: 'Dawud' },
  Sulayman: { ar: 'سليمان', en: 'Sulayman' },
  Isa: { ar: 'عيسى', en: 'Isa' },
  Zakariyya: { ar: 'زكريا', en: 'Zakariyya' },
  Yahya: { ar: 'يحيى', en: 'Yahya' },
  Lut: { ar: 'لوط', en: 'Lut' },
  Hud: { ar: 'هود', en: 'Hud' },
  Salih: { ar: 'صالح', en: 'Salih' },
  "Shu'ayb": { ar: 'شعيب', en: "Shu'ayb" },
  Ayyub: { ar: 'أيوب', en: 'Ayyub' },
  Yunus: { ar: 'يونس', en: 'Yunus' },
  Idris: { ar: 'إدريس', en: 'Idris' },
  // Prophet Muhammad ﷺ
  Muhammad: { ar: 'محمد ﷺ', en: 'Muhammad ﷺ' },
  'Prophet Muhammad': { ar: 'النبي محمد ﷺ', en: 'Prophet Muhammad ﷺ' },
  // Righteous people
  Luqman: { ar: 'لقمان', en: 'Luqman' },
  'Dhul-Qarnayn': { ar: 'ذو القرنين', en: 'Dhul-Qarnayn' },
  Uzair: { ar: 'عزير', en: 'Uzair' },
  Maryam: { ar: 'مريم', en: 'Maryam' },
  // Family members
  Hawwa: { ar: 'حواء', en: 'Hawwa' },
  Sara: { ar: 'سارة', en: 'Sara' },
  Hajar: { ar: 'هاجر', en: 'Hajar' },
  Asiya: { ar: 'آسية', en: 'Asiya' },
  Zulaykha: { ar: 'زليخا', en: 'Zulaykha' },
  'Wife of Zakariyya': { ar: 'زوجة زكريا', en: 'Wife of Zakariyya' },
  // Villains/opponents
  Iblis: { ar: 'إبليس', en: 'Iblis' },
  Firawn: { ar: 'فرعون', en: 'Firawn' },
  Qarun: { ar: 'قارون', en: 'Qarun' },
  Namrud: { ar: 'نمرود', en: 'Namrud' },
  Abraha: { ar: 'أبرهة', en: 'Abraha' },
  'Jalut (Goliath)': { ar: 'جالوت', en: 'Jalut (Goliath)' },
  // Sons/relatives
  'Habil (Abel)': { ar: 'هابيل', en: 'Habil (Abel)' },
  'Qabil (Cain)': { ar: 'قابيل', en: 'Qabil (Cain)' },
  Brothers: { ar: 'الإخوة', en: 'Brothers' },
  'His son': { ar: 'ابنه', en: 'His son' },
  'His wife': { ar: 'زوجته', en: 'His wife' },
  'His daughters': { ar: 'بناته', en: 'His daughters' },
  'His people': { ar: 'قومه', en: 'His people' },
  'His army': { ar: 'جيشه', en: 'His army' },
  'His donkey': { ar: 'حماره', en: 'His donkey' },
  // Groups and nations
  'Bani Israel': { ar: 'بني إسرائيل', en: 'Bani Israel' },
  Disciples: { ar: 'الحواريون', en: 'Disciples' },
  Thamud: { ar: 'ثمود', en: 'Thamud' },
  "People of 'Ad": { ar: 'قوم عاد', en: "People of 'Ad" },
  'People of Madyan': { ar: 'أهل مدين', en: 'People of Madyan' },
  'Villagers by the sea': { ar: 'أصحاب القرية', en: 'Villagers by the sea' },
  'Youth of the Cave': { ar: 'أصحاب الكهف', en: 'Youth of the Cave' },
  // Creatures
  Jinn: { ar: 'الجن', en: 'Jinn' },
  Hoopoe: { ar: 'الهدهد', en: 'Hoopoe' },
  Elephant: { ar: 'الفيل', en: 'Elephant' },
  'The She-camel': { ar: 'الناقة', en: 'The She-camel' },
  'Their dog': { ar: 'كلبهم', en: 'Their dog' },
  // Others
  'Talut (Saul)': { ar: 'طالوت', en: 'Talut (Saul)' },
  'Queen of Sheba': { ar: 'ملكة سبأ', en: 'Queen of Sheba' },
  'The murdered man': { ar: 'القتيل', en: 'The murdered man' },
  Aziz: { ar: 'العزيز', en: 'Aziz' },
  'Yajuj and Majuj': { ar: 'يأجوج ومأجوج', en: 'Yajuj and Majuj' },
  // Prophetic era figures
  'Abu Jahl': { ar: 'أبو جهل', en: 'Abu Jahl' },
  'Abu Lahab': { ar: 'أبو لهب', en: 'Abu Lahab' },
  'Abu Sufyan': { ar: 'أبو سفيان', en: 'Abu Sufyan' },
  'Abu Bakr': { ar: 'أبو بكر', en: 'Abu Bakr' },
  'Umar': { ar: 'عمر', en: 'Umar' },
  'Uthman': { ar: 'عثمان', en: 'Uthman' },
  'Ali': { ar: 'علي', en: 'Ali' },
  'Khadijah': { ar: 'خديجة', en: 'Khadijah' },
  'Aisha': { ar: 'عائشة', en: 'Aisha' },
  'Fatimah': { ar: 'فاطمة', en: 'Fatimah' },
  'Hamza': { ar: 'حمزة', en: 'Hamza' },
  'Bilal': { ar: 'بلال', en: 'Bilal' },
  // Groups
  Believers: { ar: 'المؤمنون', en: 'Believers' },
  Companions: { ar: 'الصحابة', en: 'Companions' },
  Muslims: { ar: 'المسلمون', en: 'Muslims' },
  Quraysh: { ar: 'قريش', en: 'Quraysh' },
  Hypocrites: { ar: 'المنافقون', en: 'Hypocrites' },
  Angels: { ar: 'الملائكة', en: 'Angels' },
  Prophets: { ar: 'الأنبياء', en: 'Prophets' },
  'Young Believers': { ar: 'الفتية المؤمنون', en: 'Young Believers' },
  'Rich Man': { ar: 'الرجل الغني', en: 'Rich Man' },
  'Poor Believer': { ar: 'المؤمن الفقير', en: 'Poor Believer' },
  'Al-Khidr': { ar: 'الخضر', en: 'Al-Khidr' },
  'Aziz of Egypt': { ar: 'عزيز مصر', en: 'Aziz of Egypt' },
  'Wife of Aziz': { ar: 'امرأة العزيز', en: 'Wife of Aziz' },
  King: { ar: 'الملك', en: 'King' },
  'Son of Nuh': { ar: 'ابن نوح', en: 'Son of Nuh' },
  'Wife of Nuh': { ar: 'امرأة نوح', en: 'Wife of Nuh' },
  'People of Nuh': { ar: 'قوم نوح', en: 'People of Nuh' },
  Egyptians: { ar: 'المصريون', en: 'Egyptians' },
  'Firawn (Pharaoh)': { ar: 'فرعون', en: 'Firawn (Pharaoh)' },
  'Hawariyyun': { ar: 'الحواريون', en: 'Disciples' },
  'Disciples (Hawariyyun)': { ar: 'الحواريون', en: 'Disciples' },
  "ʿĀd": { ar: 'عاد', en: "ʿĀd" },
  'People of Lut': { ar: 'قوم لوط', en: 'People of Lut' },
  'Wife of Lut': { ar: 'امرأة لوط', en: 'Wife of Lut' },
  'Thamūd': { ar: 'ثمود', en: 'Thamūd' },
  'Ashab al-Aykah': { ar: 'أصحاب الأيكة', en: 'Ashab al-Aykah' },
  'People of Yunus': { ar: 'قوم يونس', en: 'People of Yunus' },
  'Yajuj wa Majuj': { ar: 'يأجوج ومأجوج', en: 'Yajuj wa Majuj' },
  'Abyssinian Army': { ar: 'جيش الحبشة', en: 'Abyssinian Army' },
  'The Boy': { ar: 'الغلام', en: 'The Boy' },
  'The King': { ar: 'الملك', en: 'The King' },
  'The Sorcerer': { ar: 'الساحر', en: 'The Sorcerer' },
  'The Monk': { ar: 'الراهب', en: 'The Monk' },
  'Garden Owners': { ar: 'أصحاب الجنة', en: 'Garden Owners' },
  'Village by the Sea': { ar: 'أهل القرية الساحلية', en: 'Village by the Sea' },
  'Queen of Sheba (Bilqis)': { ar: 'ملكة سبأ (بلقيس)', en: 'Queen of Sheba (Bilqis)' },
  Ifrit: { ar: 'العفريت', en: 'Ifrit' },
  'One with Knowledge': { ar: 'الذي عنده علم من الكتاب', en: 'One with Knowledge' },
  "Luqman's Son": { ar: 'ابن لقمان', en: "Luqman's Son" },
  هابيل: { ar: 'هابيل', en: 'Habil (Abel)' },
  قابيل: { ar: 'قابيل', en: 'Qabil (Cain)' },
  ذو_القرنين: { ar: 'ذو القرنين', en: 'Dhul-Qarnayn' },
  لقمان: { ar: 'لقمان', en: 'Luqman' },

  // ============================================================
  // NEW STORY FIGURES - Ilyas, Al-Yasa, Dhul-Kifl, Ya-Sin Town, etc.
  // ============================================================

  // Prophet Ilyas and Al-Yasa
  Ilyas: { ar: 'إلياس', en: 'Ilyas (Elijah)' },
  'Al-Yasa': { ar: 'اليسع', en: 'Al-Yasa (Elisha)' },
  'Dhul-Kifl': { ar: 'ذو الكفل', en: 'Dhul-Kifl' },

  // People of the Town (Ya-Sin)
  'Three Messengers': { ar: 'الرسل الثلاثة', en: 'Three Messengers' },
  'Believing Man': { ar: 'الرجل المؤمن', en: 'Believing Man' },
  'Town Dwellers': { ar: 'أهل القرية', en: 'Town Dwellers' },

  // People of the Rass and Tubba
  'People of the Rass': { ar: 'أصحاب الرس', en: 'People of the Rass' },
  Tubba: { ar: 'تُبَّع', en: 'Tubba' },
  'People of Tubba': { ar: 'قوم تُبَّع', en: 'People of Tubba' },
  Himyarites: { ar: 'حمير', en: 'Himyarites' },

  // 'Abasa story
  'Ibn Umm Maktum': { ar: 'عبد الله بن أم مكتوم', en: 'Ibn Umm Maktum' },
  'Quraysh Leaders': { ar: 'سادة قريش', en: 'Quraysh Leaders' },

  // Battle of Ahzab
  Confederates: { ar: 'الأحزاب', en: 'Confederates' },
  'Banu Qurayza': { ar: 'بني قريظة', en: 'Banu Qurayza' },
  'Jews of Banu Qurayza': { ar: 'يهود بني قريظة', en: 'Jews of Banu Qurayza' },
  Ghatafan: { ar: 'غطفان', en: 'Ghatafan' },

  // Bani Nadir
  'Bani Nadir': { ar: 'بني النضير', en: 'Bani Nadir' },
  'Bani Nadir Jews': { ar: 'يهود بني النضير', en: 'Bani Nadir Jews' },

  // People of Aiyka
  'People of Aiyka': { ar: 'أصحاب الأيكة', en: 'People of Aiyka' },
  Shuayb: { ar: 'شعيب', en: "Shu'ayb" },
};

// Segment aspect/type translations
export const aspectTranslations: Record<string, { ar: string; en: string }> = {
  // Adam story aspects
  creation: { ar: 'الخلق', en: 'creation' },
  knowledge: { ar: 'العلم', en: 'knowledge' },
  iblis_refusal: { ar: 'رفض إبليس', en: 'iblis_refusal' },
  iblis_dialogue: { ar: 'حوار إبليس', en: 'iblis_dialogue' },
  iblis_arrogance: { ar: 'كبر إبليس', en: 'iblis_arrogance' },
  test_in_paradise: { ar: 'الاختبار في الجنة', en: 'test_in_paradise' },
  fall: { ar: 'الهبوط', en: 'fall' },
  repentance: { ar: 'التوبة', en: 'repentance' },
  // General aspects
  calling: { ar: 'الدعوة', en: 'calling' },
  rejection: { ar: 'الرفض', en: 'rejection' },
  deliverance: { ar: 'النجاة', en: 'deliverance' },
  punishment: { ar: 'العذاب', en: 'punishment' },
  trial: { ar: 'الابتلاء', en: 'trial' },
  miracle: { ar: 'المعجزة', en: 'miracle' },
  miracles: { ar: 'المعجزات', en: 'miracles' },
  dialogue: { ar: 'الحوار', en: 'dialogue' },
  confrontation: { ar: 'المواجهة', en: 'confrontation' },
  victory: { ar: 'النصر', en: 'victory' },
  journey: { ar: 'الرحلة', en: 'journey' },
  meeting: { ar: 'اللقاء', en: 'meeting' },
  revelation: { ar: 'الوحي', en: 'revelation' },
  command: { ar: 'الأمر', en: 'command' },
  sacrifice: { ar: 'التضحية', en: 'sacrifice' },
  blessing: { ar: 'البركة', en: 'blessing' },
  wisdom: { ar: 'الحكمة', en: 'wisdom' },
  advice: { ar: 'النصيحة', en: 'advice' },
  kingdom: { ar: 'الملك', en: 'kingdom' },
  destruction: { ar: 'الهلاك', en: 'destruction' },
  birth: { ar: 'الولادة', en: 'birth' },
  annunciation: { ar: 'البشارة', en: 'annunciation' },
  prayer: { ar: 'الدعاء', en: 'prayer' },
  healing: { ar: 'الشفاء', en: 'healing' },
  dream: { ar: 'الرؤيا', en: 'dream' },
  betrayal: { ar: 'الخيانة', en: 'betrayal' },
  temptation: { ar: 'الفتنة', en: 'temptation' },
  prison: { ar: 'السجن', en: 'prison' },
  interpretation: { ar: 'التفسير', en: 'interpretation' },
  reunion: { ar: 'اللقاء', en: 'reunion' },
  forgiveness: { ar: 'المغفرة', en: 'forgiveness' },
  building: { ar: 'البناء', en: 'building' },
  protection: { ar: 'الحماية', en: 'protection' },
  // Luqman story aspects
  given_wisdom: { ar: 'الحكمة المعطاة', en: 'given_wisdom' },
  avoid_shirk: { ar: 'اجتناب الشرك', en: 'avoid_shirk' },
  parents: { ar: 'الوالدين', en: 'parents' },
  accountability: { ar: 'المحاسبة', en: 'accountability' },
  prayer_character: { ar: 'الصلاة والأخلاق', en: 'prayer_character' },
  // Additional aspects
  warning: { ar: 'التحذير', en: 'warning' },
  promise: { ar: 'الوعد', en: 'promise' },
  guidance: { ar: 'الهداية', en: 'guidance' },
  patience: { ar: 'الصبر', en: 'patience' },
  gratitude: { ar: 'الشكر', en: 'gratitude' },
  trust: { ar: 'التوكل', en: 'trust' },
  salvation: { ar: 'الإنقاذ', en: 'salvation' },
  death: { ar: 'الموت', en: 'death' },
  resurrection: { ar: 'البعث', en: 'resurrection' },
  worship: { ar: 'العبادة', en: 'worship' },
  obedience: { ar: 'الطاعة', en: 'obedience' },
  disobedience: { ar: 'العصيان', en: 'disobedience' },
  ark: { ar: 'السفينة', en: 'ark' },
  flood: { ar: 'الطوفان', en: 'flood' },
  fire: { ar: 'النار', en: 'fire' },
  migration: { ar: 'الهجرة', en: 'migration' },
  test: { ar: 'الاختبار', en: 'test' },
  covenant: { ar: 'العهد', en: 'covenant' },
  // Extended aspects from all stories
  '100_years': { ar: 'مئة عام', en: '100_years' },
  advice_given: { ar: 'النصيحة المقدمة', en: 'advice_given' },
  angel_visit: { ar: 'زيارة الملاك', en: 'angel_visit' },
  angels_visit: { ar: 'زيارة الملائكة', en: 'angels_visit' },
  answer: { ar: 'الإجابة', en: 'answer' },
  ant_valley: { ar: 'وادي النمل', en: 'ant_valley' },
  arrogant_response: { ar: 'الرد المتكبر', en: 'arrogant_response' },
  awakening: { ar: 'الاستيقاظ', en: 'awakening' },
  becomes_minister: { ar: 'يصبح وزيرًا', en: 'becomes_minister' },
  believers_saved: { ar: 'نجاة المؤمنين', en: 'believers_saved' },
  birth_and_rescue: { ar: 'الولادة والإنقاذ', en: 'birth_and_rescue' },
  birth_narrative: { ar: 'قصة الولادة', en: 'birth_narrative' },
  breaking_idols: { ar: 'تحطيم الأصنام', en: 'breaking_idols' },
  brothers_return: { ar: 'عودة الإخوة', en: 'brothers_return' },
  building_ark: { ar: 'بناء السفينة', en: 'building_ark' },
  building_barrier: { ar: 'بناء السد', en: 'building_barrier' },
  building_kaaba: { ar: 'بناء الكعبة', en: 'building_kaaba' },
  burial: { ar: 'الدفن', en: 'burial' },
  calling_father: { ar: 'دعوة الأب', en: 'calling_father' },
  calling_to_hajj: { ar: 'الدعوة للحج', en: 'calling_to_hajj' },
  calling_to_lord: { ar: 'الدعاء إلى الله', en: 'calling_to_lord' },
  camel_killed: { ar: 'قتل الناقة', en: 'camel_killed' },
  childhood_dream: { ar: 'رؤيا الطفولة', en: 'childhood_dream' },
  chosen_purified: { ar: 'الاصطفاء والتطهير', en: 'chosen_purified' },
  complete_story: { ar: 'القصة الكاملة', en: 'complete_story' },
  confronting_firawn: { ar: 'مواجهة فرعون', en: 'confronting_firawn' },
  crossing_sea: { ar: 'عبور البحر', en: 'crossing_sea' },
  dawah: { ar: 'الدعوة', en: 'dawah' },
  departure: { ar: 'المغادرة', en: 'departure' },
  divine_gifts: { ar: 'الهبات الإلهية', en: 'divine_gifts' },
  faith: { ar: 'الإيمان', en: 'faith' },
  given_kingdom: { ar: 'إعطاء الملك', en: 'given_kingdom' },
  given_wealth: { ar: 'إعطاء المال', en: 'given_wealth' },
  giving_birth: { ar: 'الولادة', en: 'giving_birth' },
  golden_calf: { ar: 'العجل الذهبي', en: 'golden_calf' },
  habil_response: { ar: 'رد هابيل', en: 'habil_response' },
  hoopoe_news: { ar: 'خبر الهدهد', en: 'hoopoe_news' },
  humility: { ar: 'التواضع', en: 'humility' },
  introduction: { ar: 'المقدمة', en: 'introduction' },
  iron_gift: { ar: 'تليين الحديد', en: 'iron_gift' },
  journey_east: { ar: 'الرحلة شرقًا', en: 'journey_east' },
  journey_west: { ar: 'الرحلة غربًا', en: 'journey_west' },
  journey_with_khidr: { ar: 'الرحلة مع الخضر', en: 'journey_with_khidr' },
  landing: { ar: 'الرسو', en: 'landing' },
  lessons: { ar: 'الدروس', en: 'lessons' },
  magicians_convert: { ar: 'إسلام السحرة', en: 'magicians_convert' },
  miraculous_birth: { ar: 'الولادة المعجزة', en: 'miraculous_birth' },
  mother_vow: { ar: 'نذر الأم', en: 'mother_vow' },
  mount_sinai: { ar: 'جبل الطور', en: 'mount_sinai' },
  mountains_praise: { ar: 'تسبيح الجبال', en: 'mountains_praise' },
  murder: { ar: 'القتل', en: 'murder' },
  not_crucified: { ar: 'لم يُصلب', en: 'not_crucified' },
  offerings: { ar: 'القرابين', en: 'offerings' },
  passing_by: { ar: 'المرور', en: 'passing_by' },
  people_believe: { ar: 'إيمان القوم', en: 'people_believe' },
  praised: { ar: 'الثناء', en: 'praised' },
  queen_of_sheba: { ar: 'ملكة سبأ', en: 'queen_of_sheba' },
  questions: { ar: 'الأسئلة', en: 'questions' },
  receiving_prophethood: { ar: 'تلقي النبوة', en: 'receiving_prophethood' },
  rejected: { ar: 'الرفض', en: 'rejected' },
  reluctant_obedience: { ar: 'الطاعة المترددة', en: 'reluctant_obedience' },
  rescued: { ar: 'الإنقاذ', en: 'rescued' },
  returning_to_people: { ar: 'العودة للقوم', en: 'returning_to_people' },
  sacrifice_test: { ar: 'اختبار الذبح', en: 'sacrifice_test' },
  secret_prayer: { ar: 'الدعاء السري', en: 'secret_prayer' },
  seeking_truth: { ar: 'البحث عن الحق', en: 'seeking_truth' },
  she_camel: { ar: 'الناقة', en: 'she_camel' },
  showing_off: { ar: 'التفاخر', en: 'showing_off' },
  signs: { ar: 'الآيات', en: 'signs' },
  sleep: { ar: 'النوم', en: 'sleep' },
  sold_to_egypt: { ar: 'البيع إلى مصر', en: 'sold_to_egypt' },
  son_drowns: { ar: 'غرق الابن', en: 'son_drowns' },
  speaking_in_cradle: { ar: 'الكلام في المهد', en: 'speaking_in_cradle' },
  swallowed: { ar: 'الابتلاع', en: 'swallowed' },
  table_from_heaven: { ar: 'المائدة من السماء', en: 'table_from_heaven' },
  teaching_tawhid: { ar: 'تعليم التوحيد', en: 'teaching_tawhid' },
  the_test: { ar: 'الاختبار', en: 'the_test' },
  threat: { ar: 'التهديد', en: 'threat' },
  three_groups: { ar: 'الفرق الثلاث', en: 'three_groups' },
  throne_test: { ar: 'اختبار العرش', en: 'throne_test' },
  transformation: { ar: 'التحول', en: 'transformation' },
  transgression: { ar: 'العدوان', en: 'transgression' },
  upbringing: { ar: 'التنشئة', en: 'upbringing' },
  warning_people: { ar: 'تحذير القوم', en: 'warning_people' },
  wife_left_behind: { ar: 'ترك الزوجة', en: 'wife_left_behind' },
  with_talut: { ar: 'مع طالوت', en: 'with_talut' },
  yahya_qualities: { ar: 'صفات يحيى', en: 'yahya_qualities' },
  youth_and_exile: { ar: 'الشباب والنفي', en: 'youth_and_exile' },
  test_of_chastity: { ar: 'اختبار العفة', en: 'test_of_chastity' },
  // Uhud/Munafiqun story tags
  strategy: { ar: 'الإستراتيجية', en: 'strategy' },
  exposure: { ar: 'الانكشاف', en: 'exposure' },
  superiority: { ar: 'التفوق', en: 'superiority' },
  mortality: { ar: 'الفناء', en: 'mortality' },
  consultation: { ar: 'المشاورة', en: 'consultation' },
  joy: { ar: 'الفرح', en: 'joy' },
  messenger: { ar: 'الرسول', en: 'messenger' },
  divine_help: { ar: 'العون الإلهي', en: 'divine_help' },
  greed: { ar: 'الطمع', en: 'greed' },
  encouragement: { ar: 'التشجيع', en: 'encouragement' },
  afterlife: { ar: 'الآخرة', en: 'afterlife' },
  honor: { ar: 'الشرف', en: 'honor' },

  // =============================================================================
  // Grammar Analysis (إعراب)
  // =============================================================================
  grammar_title: { ar: 'الإعراب', en: 'Grammar Analysis' },
  grammar_analyze: { ar: 'تحليل الإعراب', en: 'Analyze Grammar' },
  grammar_loading: { ar: 'جارٍ التحليل النحوي...', en: 'Analyzing grammar...' },
  grammar_error: { ar: 'تعذّر تحميل الإعراب', en: 'Failed to load grammar analysis' },
  grammar_unavailable: { ar: 'خدمة الإعراب غير متاحة', en: 'Grammar service unavailable' },
  grammar_no_data: { ar: 'لا تتوفر بيانات إعراب لهذه الآية', en: 'No grammar data available for this verse' },
  grammar_retry: { ar: 'إعادة المحاولة', en: 'Try again' },
  grammar_confidence: { ar: 'الثقة', en: 'Confidence' },
  grammar_provider: { ar: 'المصدر', en: 'Provider' },
  grammar_root: { ar: 'الجذر', en: 'Root' },
  grammar_pattern: { ar: 'الوزن', en: 'Pattern' },
  grammar_case: { ar: 'علامة الإعراب', en: 'Case Ending' },
  grammar_legend: { ar: 'دليل الألوان', en: 'Color Legend' },

  // Part of Speech Tags
  grammar_pos_noun: { ar: 'اسم', en: 'Noun' },
  grammar_pos_proper_noun: { ar: 'اسم علم', en: 'Proper Noun' },
  grammar_pos_pronoun: { ar: 'ضمير', en: 'Pronoun' },
  grammar_pos_demonstrative: { ar: 'اسم إشارة', en: 'Demonstrative' },
  grammar_pos_relative: { ar: 'اسم موصول', en: 'Relative Pronoun' },
  grammar_pos_interrogative_noun: { ar: 'اسم استفهام', en: 'Interrogative Noun' },
  grammar_pos_masdar: { ar: 'مصدر', en: 'Verbal Noun' },
  grammar_pos_verb: { ar: 'فعل', en: 'Verb' },
  grammar_pos_past_verb: { ar: 'فعل ماض', en: 'Past Verb' },
  grammar_pos_present_verb: { ar: 'فعل مضارع', en: 'Present Verb' },
  grammar_pos_imperative_verb: { ar: 'فعل أمر', en: 'Imperative' },
  grammar_pos_particle: { ar: 'حرف', en: 'Particle' },
  grammar_pos_preposition: { ar: 'حرف جر', en: 'Preposition' },
  grammar_pos_conjunction: { ar: 'حرف عطف', en: 'Conjunction' },
  grammar_pos_negation: { ar: 'حرف نفي', en: 'Negation' },
  grammar_pos_interrogative: { ar: 'حرف استفهام', en: 'Interrogative' },
  grammar_pos_conditional: { ar: 'حرف شرط', en: 'Conditional' },
  grammar_pos_exception: { ar: 'حرف استثناء', en: 'Exception' },
  grammar_pos_adjective: { ar: 'صفة', en: 'Adjective' },
  grammar_pos_adverb: { ar: 'ظرف', en: 'Adverb' },
  grammar_pos_unknown: { ar: 'غير محدد', en: 'Unknown' },

  // Grammatical Roles
  grammar_role_subject: { ar: 'مبتدأ', en: 'Subject' },
  grammar_role_predicate: { ar: 'خبر', en: 'Predicate' },
  grammar_role_doer: { ar: 'فاعل', en: 'Doer/Agent' },
  grammar_role_deputy_doer: { ar: 'نائب فاعل', en: 'Deputy Doer' },
  grammar_role_object: { ar: 'مفعول به', en: 'Object' },
  grammar_role_object_for: { ar: 'مفعول لأجله', en: 'Object For' },
  grammar_role_object_in: { ar: 'مفعول فيه', en: 'Object In' },
  grammar_role_absolute_object: { ar: 'مفعول مطلق', en: 'Absolute Object' },
  grammar_role_object_with: { ar: 'مفعول معه', en: 'Object With' },
  grammar_role_circumstantial: { ar: 'حال', en: 'Circumstantial' },
  grammar_role_specification: { ar: 'تمييز', en: 'Specification' },
  grammar_role_excepted: { ar: 'مستثنى', en: 'Excepted' },
  grammar_role_possessor: { ar: 'مضاف', en: 'Possessor' },
  grammar_role_possessed: { ar: 'مضاف إليه', en: 'Possessed' },
  grammar_role_prepositional: { ar: 'جار ومجرور', en: 'Prepositional Phrase' },
  grammar_role_genitive: { ar: 'مجرور', en: 'Genitive' },
  grammar_role_adjective: { ar: 'نعت', en: 'Adjective' },
  grammar_role_substitute: { ar: 'بدل', en: 'Substitute' },
  grammar_role_conjunction: { ar: 'معطوف', en: 'Conjoined' },
  grammar_role_emphasis: { ar: 'توكيد', en: 'Emphasis' },
  grammar_role_vocative: { ar: 'منادى', en: 'Vocative' },
  grammar_role_unknown: { ar: 'غير محدد', en: 'Unknown' },

  // Sentence Types
  grammar_sentence_nominal: { ar: 'جملة اسمية', en: 'Nominal Sentence' },
  grammar_sentence_verbal: { ar: 'جملة فعلية', en: 'Verbal Sentence' },
  grammar_sentence_prepositional: { ar: 'شبه جملة', en: 'Prepositional Phrase' },

  // Provider Labels
  grammar_provider_farasa: { ar: 'فرسا', en: 'Farasa' },
  grammar_provider_camel: { ar: 'كاميل', en: 'CAMeL Tools' },
  grammar_provider_stanza: { ar: 'ستانزا', en: 'Stanza' },
  grammar_provider_llm: { ar: 'تحليل ذكي', en: 'AI Analysis' },
  grammar_provider_static: { ar: 'بيانات ثابتة', en: 'Static Data' },

  // =============================================================================
  // Tafseer (التفسير)
  // =============================================================================
  tafseer_title: { ar: 'التفسير', en: 'Tafseer' },
  tafseer_select_edition: { ar: 'اختر التفسير', en: 'Select Tafseer' },
  tafseer_loading: { ar: 'جارٍ تحميل التفسير...', en: 'Loading tafseer...' },
  tafseer_error: { ar: 'تعذّر تحميل التفسير', en: 'Failed to load tafseer' },
  tafseer_unavailable: { ar: 'خدمة التفسير غير متاحة', en: 'Tafseer service unavailable' },
  tafseer_no_data: { ar: 'لا يتوفر تفسير لهذه الآية', en: 'No tafseer available for this verse' },
  tafseer_source: { ar: 'المصدر', en: 'Source' },
  tafseer_author: { ar: 'المؤلف', en: 'Author' },
  tafseer_language: { ar: 'اللغة', en: 'Language' },
  tafseer_preferences: { ar: 'إعدادات التفسير', en: 'Tafseer Preferences' },
  tafseer_show_translation: { ar: 'إظهار الترجمة', en: 'Show Translation' },
  tafseer_show_arabic: { ar: 'إظهار العربية', en: 'Show Arabic' },
  tafseer_show_both: { ar: 'إظهار الاثنين', en: 'Show Both' },

  // Tafseer Edition Names
  tafseer_muyassar: { ar: 'التفسير الميسر', en: 'Al-Muyassar (Simplified)' },
  tafseer_jalalayn: { ar: 'تفسير الجلالين', en: 'Tafsir Al-Jalalayn' },
  tafseer_ibn_kathir: { ar: 'تفسير ابن كثير', en: 'Tafsir Ibn Kathir' },
  tafseer_qurtubi: { ar: 'تفسير القرطبي', en: 'Tafsir Al-Qurtubi' },
  tafseer_tabari: { ar: 'تفسير الطبري', en: 'Tafsir At-Tabari' },
  tafseer_baghawi: { ar: 'تفسير البغوي', en: 'Tafsir Al-Baghawi' },
  tafseer_saadi: { ar: 'تفسير السعدي', en: 'Tafsir As-Saadi' },
  tafseer_sahih: { ar: 'الترجمة الصحيحة', en: 'Sahih International' },
  tafseer_pickthall: { ar: 'ترجمة بيكثال', en: 'Pickthall Translation' },
  tafseer_yusufali: { ar: 'ترجمة يوسف علي', en: 'Yusuf Ali Translation' },
  tafseer_hilali: { ar: 'ترجمة الهلالي وخان', en: 'Hilali & Khan' },

  // Madhab Names
  madhab_shafii: { ar: 'الشافعي', en: "Shafi'i" },
  madhab_maliki: { ar: 'المالكي', en: 'Maliki' },
  madhab_hanafi: { ar: 'الحنفي', en: 'Hanafi' },
  madhab_hanbali: { ar: 'الحنبلي', en: 'Hanbali' },
  madhab_general: { ar: 'عام', en: 'General' },

  // =============================================================================
  // Admin/Verification
  // =============================================================================
  admin_verification: { ar: 'التحقق', en: 'Verification' },
  admin_approve: { ar: 'موافقة', en: 'Approve' },
  admin_reject: { ar: 'رفض', en: 'Reject' },
  admin_pending: { ar: 'قيد الانتظار', en: 'Pending' },
  admin_reviewed: { ar: 'تمت المراجعة', en: 'Reviewed' },
  admin_flag: { ar: 'إبلاغ', en: 'Flag' },
  admin_flag_reason: { ar: 'سبب الإبلاغ', en: 'Flag Reason' },

  // =============================================================================
  // Mushaf Page - المصحف
  // =============================================================================
  mushaf_title: { ar: 'المصحف الشريف', en: 'Holy Mushaf' },
  mushaf_page: { ar: 'صفحة', en: 'Page' },
  mushaf_juz: { ar: 'الجزء', en: 'Juz' },
  mushaf_next_page: { ar: 'الصفحة التالية', en: 'Next Page' },
  mushaf_prev_page: { ar: 'الصفحة السابقة', en: 'Previous Page' },
  mushaf_zoom_in: { ar: 'تكبير', en: 'Zoom In' },
  mushaf_zoom_out: { ar: 'تصغير', en: 'Zoom Out' },
  mushaf_settings: { ar: 'الإعدادات', en: 'Settings' },
  mushaf_tafsir: { ar: 'التفسير', en: 'Tafsir' },
  mushaf_reciter: { ar: 'القارئ', en: 'Reciter' },
  mushaf_listen: { ar: 'استماع', en: 'Listen' },
  mushaf_pause: { ar: 'إيقاف', en: 'Pause' },
  mushaf_stop: { ar: 'إيقاف', en: 'Stop' },
  mushaf_verses: { ar: 'الآيات', en: 'Verses' },
  mushaf_verses_range: { ar: 'الآيات من {start} إلى {end}', en: 'Verses {start} to {end}' },
  mushaf_load_failed: { ar: 'فشل في تحميل الصفحة', en: 'Failed to load page' },
  mushaf_retry: { ar: 'إعادة المحاولة', en: 'Retry' },

  // =============================================================================
  // AI Assistant - المساعد الذكي
  // =============================================================================
  ai_assistant: { ar: 'المساعد الذكي', en: 'AI Assistant' },
  ai_summary: { ar: 'ملخص', en: 'Summary' },
  ai_explain: { ar: 'شرح', en: 'Explain' },
  ai_qa: { ar: 'سؤال وجواب', en: 'Q&A' },
  ai_generate_summary: { ar: 'إنشاء ملخص التفسير', en: 'Generate Tafsir Summary' },
  ai_select_verse: { ar: 'اختر آية للبدء', en: 'Select a verse to start' },
  ai_select_word: { ar: 'حدد كلمة للشرح', en: 'Select a word to explain' },
  ai_select_word_hint: { ar: 'حدد كلمة من الآية أعلاه أو اكتب كلمة للشرح', en: 'Select a word from the verse above or type a word to explain' },
  ai_enter_word: { ar: 'أدخل كلمة...', en: 'Enter a word...' },
  ai_explanation_of: { ar: 'شرح "{word}"', en: 'Explanation of "{word}"' },
  ai_ask_question: { ar: 'اسأل سؤالاً عن الآية...', en: 'Ask a question about the verse...' },
  ai_suggested_questions: { ar: 'أسئلة مقترحة:', en: 'Suggested questions:' },
  ai_question_revelation: { ar: 'ما سبب نزول هذه الآية؟', en: 'What is the reason for revelation?' },
  ai_question_lessons: { ar: 'ما الدروس المستفادة؟', en: 'What are the lessons learned?' },
  ai_question_context: { ar: 'ما علاقة الآية بما قبلها؟', en: 'How does this relate to previous verses?' },
  ai_unavailable: { ar: 'خدمة الذكاء الاصطناعي غير متاحة', en: 'AI service unavailable' },
  ai_timeout: { ar: 'انتهت مهلة الطلب', en: 'Request timeout' },
  ai_open_tafsir_first: { ar: 'افتح التفسير أولاً', en: 'Open tafsir first' },

  // =============================================================================
  // Tafsir Audio - التفسير الصوتي
  // =============================================================================
  tafsir_listen: { ar: 'استماع للتفسير', en: 'Listen to Tafsir' },
  tafsir_audio_available: { ar: 'التفسير الصوتي متاح', en: 'Audio tafsir available' },
  tafsir_no_audio: { ar: 'لا يوجد صوت للتفسير', en: 'No audio available for this tafsir' },
  tafsir_failed: { ar: 'فشل في تحميل التفسير', en: 'Failed to load tafsir' },

  // =============================================================================
  // Quran Page - صفحة القرآن
  // =============================================================================
  quran_surah: { ar: 'السورة', en: 'Surah' },
  quran_page: { ar: 'الصفحة', en: 'Page' },
  quran_juz: { ar: 'الجزء', en: 'Juz' },
  quran_view_surah: { ar: 'سورة', en: 'Surah' },
  quran_view_page: { ar: 'صفحة', en: 'Page' },
  quran_view_mushaf: { ar: 'المصحف', en: 'Mushaf' },
  quran_view_list: { ar: 'قائمة', en: 'List' },
  quran_grammar: { ar: 'إعراب', en: 'Grammar' },
  quran_similar: { ar: 'آيات متشابهة', en: 'Similar Verses' },
  quran_back_stories: { ar: 'العودة للقصص', en: 'Back to Stories' },
  quran_bismillah: { ar: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ', en: 'In the name of Allah, the Most Gracious, the Most Merciful' },

  // =============================================================================
  // Ask Page - صفحة اسأل
  // =============================================================================
  ask_clear_chat: { ar: 'مسح المحادثة', en: 'Clear chat' },
  ask_tafsir_sources: { ar: 'مصادر التفسير', en: 'Tafsir Sources' },
  ask_select_all: { ar: 'اختر الكل', en: 'Select All' },
  ask_clear_all: { ar: 'إلغاء الكل', en: 'Clear All' },
  ask_searching: { ar: 'جاري البحث...', en: 'Searching...' },
  ask_followup: { ar: 'اطرح سؤال متابعة...', en: 'Ask a follow-up question...' },
  ask_navigate: { ar: 'للتنقل', en: 'to navigate' },
  ask_select: { ar: 'للاختيار', en: 'to select' },
  ask_close_hint: { ar: 'للإغلاق', en: 'to close' },
  ask_select_source: { ar: 'يرجى اختيار مصدر تفسير واحد على الأقل', en: 'Please select at least one tafsir source' },

  // =============================================================================
  // Stories Page - صفحة القصص
  // =============================================================================
  stories_category_all: { ar: 'الكل', en: 'All' },
  stories_category_prophet: { ar: 'قصص الأنبياء', en: 'Prophets Stories' },
  stories_category_people: { ar: 'قصص الأقوام', en: 'People Stories' },
  stories_category_event: { ar: 'الأحداث', en: 'Events' },
  stories_no_stories: { ar: 'لا توجد قصص متاحة حالياً', en: 'No stories available yet' },
  stories_run_seed: { ar: 'قم بتشغيل seed_stories.py لإضافة البيانات', en: 'Run seed_stories.py to add data' },
  stories_view_story: { ar: 'عرض القصة', en: 'View Story' },

  // =============================================================================
  // Common Actions - الإجراءات الشائعة
  // =============================================================================
  action_copy: { ar: 'نسخ', en: 'Copy' },
  action_copied: { ar: 'تم النسخ', en: 'Copied' },
  action_cancel: { ar: 'إلغاء', en: 'Cancel' },
  action_confirm: { ar: 'تأكيد', en: 'Confirm' },
  action_save: { ar: 'حفظ', en: 'Save' },
  action_delete: { ar: 'حذف', en: 'Delete' },
  action_edit: { ar: 'تعديل', en: 'Edit' },
  action_view: { ar: 'عرض', en: 'View' },
  action_back: { ar: 'رجوع', en: 'Back' },
  action_next: { ar: 'التالي', en: 'Next' },
  action_previous: { ar: 'السابق', en: 'Previous' },
  action_refresh: { ar: 'تحديث', en: 'Refresh' },
  to: { ar: 'إلى', en: 'to' },
  from: { ar: 'من', en: 'from' },

  // =============================================================================
  // Language Toggle
  // =============================================================================
  lang_toggle_ar: { ar: 'العربية', en: 'العربية' },
  lang_toggle_en: { ar: 'English', en: 'English' },

  // =============================================================================
  // English Tafsir Editions
  // =============================================================================
  tafseer_ibn_kathir_en: { ar: 'تفسير ابن كثير (إنجليزي)', en: 'Ibn Kathir (English)' },
  tafseer_maarif: { ar: 'معارف القرآن', en: "Ma'arif al-Qur'an" },
  tafseer_tazkirul: { ar: 'تذكير القرآن', en: 'Tazkirul Quran' },

  // =============================================================================
  // Reciter Names
  // =============================================================================
  reciter_mishary: { ar: 'مشاري العفاسي', en: 'Mishary Al-Afasy' },
  reciter_abdul_basit: { ar: 'عبد الباسط عبد الصمد', en: 'Abdul Basit' },
  reciter_husary: { ar: 'محمود خليل الحصري', en: 'Al-Husary' },
  reciter_maher: { ar: 'ماهر المعيقلي', en: 'Maher Al-Muaiqly' },
  reciter_shuraim: { ar: 'سعود الشريم', en: 'Saud Al-Shuraim' },

  // =============================================================================
  // Concepts Page - صفحة المفاهيم
  // =============================================================================
  concepts_back: { ar: 'العودة للمفاهيم', en: 'Back to Concepts' },
  concepts_click_details: { ar: 'اضغط للتفاصيل', en: 'Click for details' },

  // =============================================================================
  // Tools Page - صفحة الأدوات
  // =============================================================================
  tools_prayer_times: { ar: 'مواقيت الصلاة', en: 'Prayer Times' },
  tools_hijri_calendar: { ar: 'التقويم الهجري', en: 'Hijri Calendar' },
  tools_zakat: { ar: 'حاسبة الزكاة', en: 'Zakat Calculator' },
  tools_mosque_finder: { ar: 'البحث عن المساجد', en: 'Mosque Finder' },
  tools_videos: { ar: 'فيديوهات إسلامية', en: 'Islamic Videos' },
  tools_news: { ar: 'أخبار إسلامية', en: 'Islamic News' },
  tools_books: { ar: 'كتب إسلامية', en: 'Islamic Books' },
  tools_hajj: { ar: 'دليل الحج والعمرة', en: 'Hajj & Umrah Guide' },
  tools_search: { ar: 'البحث الإسلامي', en: 'Islamic Web Search' },
};

export function t(key: string, language: Language): string {
  const translation = translations[key];
  if (!translation) {
    console.warn(`Missing translation for key: ${key}`);
    return key;
  }
  return translation[language];
}

// Helper function to translate category
export function translateCategory(category: string, language: Language): string {
  const trans = categoryTranslations[category];
  return trans ? trans[language] : category;
}

// Helper function to translate theme
export function translateTheme(theme: string, language: Language): string {
  const trans = themeTranslations[theme.toLowerCase()];
  return trans ? trans[language] : theme;
}

// Helper function to translate figure name
export function translateFigure(figure: string, language: Language): string {
  const trans = figureTranslations[figure];
  return trans ? trans[language] : figure;
}

// Helper function to translate aspect
export function translateAspect(aspect: string, language: Language): string {
  const trans = aspectTranslations[aspect.toLowerCase()];
  return trans ? trans[language] : aspect;
}

/**
 * Universal tag translation function.
 * Tries theme translation first, then aspect translation, then returns original with warning.
 * Returns: { text: string, isMissing: boolean }
 */
export function translateTag(tag: string, language: Language): { text: string; isMissing: boolean } {
  const normalized = tag.toLowerCase().replace(/\s+/g, '_');

  // Try theme translation first
  const themeResult = themeTranslations[normalized];
  if (themeResult) {
    return { text: themeResult[language], isMissing: false };
  }

  // Try aspect translation
  const aspectResult = aspectTranslations[normalized];
  if (aspectResult) {
    return { text: aspectResult[language], isMissing: false };
  }

  // If Arabic mode and tag has no Arabic translation, it's missing
  if (language === 'ar') {
    // Check if the tag itself is already Arabic (contains Arabic characters)
    const hasArabic = /[\u0600-\u06FF]/.test(tag);
    if (hasArabic) {
      return { text: tag, isMissing: false };
    }
    // Log warning for missing Arabic translation
    console.warn(`[i18n] Missing Arabic translation for tag: "${tag}"`);
    return { text: tag, isMissing: true };
  }

  // English mode - just return as-is (formatted)
  return { text: tag.replace(/_/g, ' '), isMissing: false };
}

/**
 * Simple tag translation that returns just the text (for simpler use cases).
 * Falls back to original tag if no translation found.
 */
export function translateTagSimple(tag: string, language: Language): string {
  const { text } = translateTag(tag, language);
  return text;
}
