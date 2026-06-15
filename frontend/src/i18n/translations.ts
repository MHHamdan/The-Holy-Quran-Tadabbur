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
  nav_bookmarks: {
    ar: 'المحفوظات',
    en: 'Bookmarks',
  },
  nav_asma_allah: {
    ar: 'أسماء الله',
    en: 'Asma Allah',
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
  nav_status: {
    ar: 'حالة المنصة',
    en: 'Status',
  },
  nav_surah_atlas: {
    ar: 'أطلس السور',
    en: 'Surah Atlas',
  },
  nav_memorization: {
    ar: 'ذكاء الحفظ',
    en: 'Memorization',
  },

  // Common
  app_title: {
    ar: 'تدبر القرآن',
    en: 'Taddabur Al-Quran',
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
  stories_search_placeholder: {
    ar: 'ابحث عن قصة أو شخصية...',
    en: 'Search stories or figures...',
  },
  stories_view_all: {
    ar: 'عرض الكل',
    en: 'View All',
  },
  stories_count: {
    ar: 'قصة',
    en: 'stories',
  },
  stories_verses: {
    ar: 'آيات',
    en: 'verses',
  },
  stories_surahs: {
    ar: 'سور',
    en: 'surahs',
  },
  category_prophets_desc: {
    ar: 'قصص الأنبياء والمرسلين عليهم السلام',
    en: 'Stories of the prophets and messengers',
  },
  category_parables_desc: {
    ar: 'أمثال وعبر من القرآن الكريم',
    en: 'Parables and moral lessons from the Quran',
  },
  category_nations_desc: {
    ar: 'قصص الأمم والحضارات السابقة',
    en: 'Stories of past nations and civilizations',
  },
  category_historical_desc: {
    ar: 'أحداث تاريخية ذكرت في القرآن',
    en: 'Historical events mentioned in the Quran',
  },
  category_righteous_desc: {
    ar: 'قصص الصالحين والصالحات',
    en: 'Stories of the righteous men and women',
  },
  category_unseen_desc: {
    ar: 'عالم الغيب والآخرة والخلق',
    en: 'The unseen realm, afterlife, and creation',
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

  // Themes Page
  themes_title: {
    ar: 'المحاور القرآنية',
    en: 'Quranic Themes',
  },
  themes_subtitle: {
    ar: 'استكشف الموضوعات الأساسية في القرآن الكريم - مصنفة وفق المنهج السني',
    en: 'Explore the foundational themes of the Quran - classified following Sunni methodology',
  },
  themes_no_results: {
    ar: 'لا توجد محاور متاحة حالياً',
    en: 'No themes available yet',
  },
  themes_run_seed: {
    ar: 'قم بتشغيل seed_themes.py لإضافة البيانات',
    en: 'Run seed_themes.py to add data',
  },
  themes_explore: {
    ar: 'استكشاف المحور',
    en: 'Explore Theme',
  },
  themes_segments: {
    ar: 'مقطع',
    en: 'segments',
  },
  themes_verses: {
    ar: 'آية',
    en: 'verses',
  },
  themes_rewards: {
    ar: 'الجزاء والعاقبة',
    en: 'Rewards & Consequences',
  },
  themes_tab: {
    ar: 'المواضيع',
    en: 'Themes',
  },

  // Allah Names (أسماء الله الحسنى)
  allah_names_tab: {
    ar: 'أسماء الله الحسنى',
    en: 'Names of Allah',
  },
  allah_names_title: {
    ar: 'أسماء الله الحسنى',
    en: 'The 99 Beautiful Names of Allah',
  },
  allah_names_subtitle: {
    ar: 'تعرف على أسماء الله الحسنى ومعانيها وشواهدها القرآنية',
    en: 'Discover the Beautiful Names of Allah with their meanings and Quranic references',
  },
  allah_names_meaning: {
    ar: 'المعنى',
    en: 'Meaning',
  },
  allah_names_description: {
    ar: 'التفسير',
    en: 'Description',
  },
  allah_names_verses: {
    ar: 'الآيات القرآنية',
    en: 'Quranic Verses',
  },
  allah_names_tafseer: {
    ar: 'التفسير',
    en: 'Tafseer',
  },
  allah_names_no_results: {
    ar: 'لا توجد أسماء متاحة حالياً',
    en: 'No names available yet',
  },
  view_in_mushaf: {
    ar: 'عرض في المصحف',
    en: 'View in Mushaf',
  },

  // Story Atlas Page
  atlas_title: {
    ar: 'أطلس القصص القرآنية',
    en: 'Quran Story Atlas',
  },
  atlas_subtitle: {
    ar: 'استكشف قصص القرآن الكريم مرتبة حسب الشخصيات والأماكن والأزمنة',
    en: 'Explore Quranic narratives organized by persons, places, and eras',
  },
  atlas_search: {
    ar: 'ابحث في القصص...',
    en: 'Search stories...',
  },
  atlas_stories_available: {
    ar: 'قصة متاحة',
    en: 'stories available',
  },
  atlas_no_results: {
    ar: 'لا توجد قصص مطابقة للبحث',
    en: 'No stories match your search',
  },
  atlas_try_adjusting: {
    ar: 'جرب تغيير معايير البحث',
    en: 'Try adjusting your filters',
  },
  atlas_events: {
    ar: 'أحداث',
    en: 'events',
  },
  atlas_surah: {
    ar: 'سورة',
    en: 'Surah',
  },
  atlas_explore: {
    ar: 'استكشف القصة',
    en: 'Explore Story',
  },
  atlas_back: {
    ar: 'العودة للأطلس',
    en: 'Back to Atlas',
  },
  atlas_related: {
    ar: 'قصص متصلة',
    en: 'Related Stories',
  },
  atlas_timeline: {
    ar: 'الجدول الزمني',
    en: 'Timeline',
  },
  atlas_graph: {
    ar: 'الرسم البياني',
    en: 'Graph',
  },
  atlas_lessons: {
    ar: 'الدروس والعبر',
    en: 'Lessons',
  },
  atlas_no_events: {
    ar: 'لا توجد أحداث متاحة بعد',
    en: 'No events available yet',
  },
  atlas_loading_graph: {
    ar: 'جاري تحميل الرسم البياني...',
    en: 'Loading graph...',
  },
  atlas_no_graph: {
    ar: 'لا توجد بيانات للرسم البياني',
    en: 'No graph data available',
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

  // Phase 5.5 – KG Similarity safety & display keys
  similarity_kg_title: {
    ar: 'الروابط المعرفية',
    en: 'Knowledge Graph Relations',
  },
  similarity_kg_subtitle: {
    ar: 'صلات مستخرجة من القصص والمفاهيم القرآنية',
    en: 'Relations derived from Quranic stories and concepts',
  },
  similarity_enter_reference: {
    ar: 'أدخل مرجع الآية (مثال: 2:255)',
    en: 'Enter ayah reference (e.g., 2:255)',
  },
  similarity_invalid_ayah: {
    ar: 'مرجع الآية غير صحيح. أدخل على شكل سورة:آية مثل 2:255',
    en: 'Invalid ayah reference. Use format sura:aya like 2:255',
  },
  similarity_needs_review: {
    ar: 'قيد المراجعة',
    en: 'Needs Review',
  },
  similarity_human_review_required: {
    ar: 'يتطلب مراجعة علمية',
    en: 'Human Review Required',
  },
  similarity_experimental: {
    ar: 'تجريبي',
    en: 'Experimental',
  },
  similarity_approved: {
    ar: 'معتمد',
    en: 'Approved',
  },
  similarity_show_experimental: {
    ar: 'إظهار العلاقات التجريبية',
    en: 'Show experimental relations',
  },
  similarity_experimental_warning: {
    ar: 'العلاقات التجريبية مقترحات آلية وليست تفسيراً معتمداً.',
    en: 'Experimental relations are automated suggestions, not approved tafsir.',
  },
  similarity_no_verified_ayahs: {
    ar: 'لا توجد صلات موثوقة متاحة لهذه الآية حالياً.',
    en: 'No verified related ayahs are available for this ayah yet.',
  },
  similarity_open_in_mushaf: {
    ar: 'عرض في المصحف',
    en: 'Open in Mushaf',
  },
  similarity_evidence: {
    ar: 'الأدلة والمصادر',
    en: 'Evidence & Sources',
  },
  similarity_path_explanation: {
    ar: 'مسار الصلة',
    en: 'Path Explanation',
  },
  similarity_path_via: {
    ar: 'عبر',
    en: 'via',
  },
  similarity_path_node_ayah: {
    ar: 'آية',
    en: 'Ayah',
  },
  similarity_path_node_story: {
    ar: 'القصة',
    en: 'Story',
  },
  similarity_path_node_story_segment: {
    ar: 'مقطع القصة',
    en: 'Story Segment',
  },
  similarity_path_node_concept: {
    ar: 'مفهوم',
    en: 'Concept',
  },
  similarity_path_node_theme: {
    ar: 'موضوع',
    en: 'Theme',
  },
  similarity_path_pending_review: {
    ar: 'قيد المراجعة',
    en: 'Pending Review',
  },
  similarity_relation_type: {
    ar: 'نوع الصلة',
    en: 'Relation Type',
  },
  similarity_kg_pending_notice_title: {
    ar: 'جميع الروابط المعرفية قيد المراجعة العلمية',
    en: 'All knowledge graph relations are pending scholarly review',
  },
  similarity_kg_pending_notice_body: {
    ar: 'هذه الروابط مستخرجة من القصص والمفاهيم القرآنية المتاحة. لا ينبغي الاعتماد عليها دون تحقق علمي.',
    en: 'These relations are derived from available Quranic stories and concepts. Do not rely on them without scholarly verification.',
  },
  similarity_kg_human_review_detail: {
    ar: 'هذه الصلة تتطلب مراجعة علمية قبل الاعتماد عليها.',
    en: 'This relation requires scholarly review before it can be relied upon.',
  },
  similarity_kg_needs_review_detail: {
    ar: 'هذه الصلات مقترحة من البيانات المتاحة وتنتظر المراجعة العلمية.',
    en: 'These relations are suggested from available data and await scholarly review.',
  },
  similarity_kg_experimental_detail: {
    ar: 'بعض هذه الصلات تجريبية مبنية على التشابه الدلالي فقط.',
    en: 'Some relations are experimental, based on semantic similarity only.',
  },
  similarity_kg_searching: {
    ar: 'جاري البحث في الرسم المعرفي...',
    en: 'Searching knowledge graph...',
  },
  similarity_kg_load_error: {
    ar: 'تعذّر تحميل الروابط المعرفية',
    en: 'Failed to load knowledge graph relations',
  },
  similarity_kg_relation_count: {
    ar: 'صلة',
    en: 'relations',
  },
  // Relation type labels
  similarity_rt_same_story_segment: {
    ar: 'نفس مقطع القصة',
    en: 'Same Story Segment',
  },
  similarity_rt_same_story: {
    ar: 'نفس القصة',
    en: 'Same Story',
  },
  similarity_rt_same_prophet: {
    ar: 'نفس النبي / الشخص',
    en: 'Same Prophet/Person',
  },
  similarity_rt_same_theme: {
    ar: 'نفس الموضوع',
    en: 'Same Theme',
  },
  similarity_rt_same_concept: {
    ar: 'نفس المفهوم',
    en: 'Same Concept',
  },
  similarity_rt_shared_moral: {
    ar: 'درس أخلاقي مشترك',
    en: 'Shared Moral Lesson',
  },
  similarity_rt_parallel_event: {
    ar: 'نمط حدث متوازٍ',
    en: 'Parallel Event Pattern',
  },
  similarity_rt_semantic: {
    ar: 'تشابه دلالي',
    en: 'Semantic Similarity',
  },
  similarity_rt_tafsir_supported: {
    ar: 'تفسير يؤكد الصلة',
    en: 'Tafsir-Supported',
  },
  // Under review label
  similarity_under_review: {
    ar: 'تحت المراجعة',
    en: 'Under Review',
  },
  similarity_relation_label: {
    ar: 'ارتباط',
    en: 'relation',
  },
  // Evidence detail labels
  similarity_evidence_story: {
    ar: 'القصة',
    en: 'Story',
  },
  similarity_evidence_concept: {
    ar: 'المفهوم',
    en: 'Concept',
  },
  similarity_evidence_theme: {
    ar: 'الموضوع',
    en: 'Theme',
  },
  similarity_evidence_tafsir_ref: {
    ar: 'مرجع التفسير',
    en: 'Tafsir Ref',
  },

  // =============================================================================
  // Tasmeeʿ (Memorization) Page - صفحة التسميع
  // =============================================================================
  nav_prophets: { ar: 'الأنبياء', en: 'Prophets' },
  nav_tasmee: { ar: 'التسميع', en: 'Memorize' },
  tasmee_title: { ar: 'التسميع', en: 'Tasmeeʿ' },
  tasmee_subtitle: { ar: 'تدرب على حفظ القرآن الكريم مع التصحيح الفوري', en: 'Practice Quran memorization with real-time feedback' },
  tasmee_select_range: { ar: 'اختر نطاق الآيات', en: 'Select Verse Range' },
  tasmee_surah: { ar: 'السورة', en: 'Surah' },
  tasmee_aya_start: { ar: 'من الآية', en: 'From Ayah' },
  tasmee_aya_end: { ar: 'إلى الآية', en: 'To Ayah' },
  tasmee_start_session: { ar: 'ابدأ التسميع', en: 'Start Session' },
  tasmee_verses: { ar: 'الآيات', en: 'Verses' },
  tasmee_progress: { ar: 'التقدم', en: 'Progress' },
  tasmee_mistakes: { ar: 'الأخطاء', en: 'Mistakes' },
  tasmee_time: { ar: 'الوقت', en: 'Time' },
  tasmee_recording: { ar: 'جاري التسجيل...', en: 'Recording...' },
  tasmee_paused: { ar: 'متوقف مؤقتاً', en: 'Paused' },
  tasmee_tap_to_start: { ar: 'اضغط للبدء', en: 'Tap to start recording' },
  tasmee_expected: { ar: 'المتوقع', en: 'Expected' },
  tasmee_heard: { ar: 'المسموع', en: 'Heard' },
  tasmee_reset: { ar: 'إعادة', en: 'Reset' },
  tasmee_complete: { ar: 'إنهاء', en: 'Complete' },
  tasmee_completed: { ar: 'أحسنت! لقد أكملت التسميع', en: 'Well done! Session completed' },
  tasmee_accuracy: { ar: 'الدقة', en: 'Accuracy' },
  tasmee_total_words: { ar: 'الكلمات', en: 'Words' },
  tasmee_try_again: { ar: 'حاول مرة أخرى', en: 'Try Again' },
  tasmee_mistakes_list: { ar: 'قائمة الأخطاء', en: 'Mistakes List' },
  tasmee_mic_error: { ar: 'فشل الوصول للميكروفون. تأكد من السماح بالوصول.', en: 'Failed to access microphone. Please allow access.' },

  // Reveal mode translations (progressive reveal feature)
  reveal_mode: { ar: 'وضع الكشف', en: 'Reveal Mode' },
  reveal_auto: { ar: 'تلقائي', en: 'Auto' },
  reveal_tap: { ar: 'بالنقر', en: 'Smart Tap' },
  reveal_hybrid: { ar: 'مختلط', en: 'Hybrid' },
  words_per_tap: { ar: 'كلمات لكل نقرة', en: 'Words per tap' },
  tap_to_reveal: { ar: 'انقر للكشف', en: 'Tap to reveal' },
  hybrid_threshold: { ar: 'عتبة التحول', en: 'Switch threshold' },
  show_full_text: { ar: 'إظهار النص الكامل', en: 'Show full text' },

  // Status badges (platform status dashboard)
  status_active: { ar: 'نشط', en: 'Active' },
  status_error: { ar: 'خطأ', en: 'Error' },
  status_checking: { ar: 'جارٍ التحقق', en: 'Checking' },
  status_warning: { ar: 'تحذير', en: 'Warning' },

  // Source attribution labels
  source_unverified: { ar: 'غير موثق', en: 'Unverified' },
  source_verified_on: { ar: 'موثق بتاريخ', en: 'Verified' },
  source_link: { ar: 'المصدر', en: 'Source' },

  // Accessibility / ARIA labels
  aria_helpful: { ar: 'مفيد', en: 'Helpful' },
  aria_not_helpful: { ar: 'غير مفيد', en: 'Not helpful' },

  // Common inline labels
  tafsir_explanations_header: { ar: 'شروحات التفسير', en: 'Tafsir Explanations' },
  tafsir_sources_count: { ar: 'مصادر', en: 'sources' },
  citation_sources_used: { ar: 'المصادر المستخدمة', en: 'Sources Used' },
  answer_summary: { ar: 'ملخص الإجابة', en: 'Answer Summary' },
  missing_source_warning: {
    ar: 'لا يوجد مصدر موثق متاح لهذه الإجابة.',
    en: 'No verified source available for this answer.',
  },

  // Search result type and match type labels
  search_result_type_quran: { ar: 'نص قرآني', en: 'Quran Text' },
  search_match_exact: { ar: 'تطابق تام', en: 'Exact Match' },
  search_match_normalized: { ar: 'نص قرآني', en: 'Quran Text' },
  search_match_root: { ar: 'مرتبط', en: 'Related' },
  search_match_semantic: { ar: 'دلالي', en: 'Semantic' },
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
  mushaf_click_verse_hint: { ar: 'اضغط على أي آية لعرض التفسير والاستماع للتلاوة', en: 'Click on any verse to view tafseer and listen to recitation' },
  tafseer_not_found: { ar: 'لم يتم العثور على التفسير', en: 'Tafseer not found' },

  // =============================================================================
  // AI Assistant - المساعد الذكي
  // =============================================================================
  ai_assistant: { ar: 'اسأل الذكاء الاصطناعي', en: 'Ask AI' },
  ai_summary: { ar: 'التلخيص', en: 'Summary' },
  // Phase E — answer mode labels
  rag_mode_simple_explanation: { ar: 'شرح مبسَّط', en: 'Simple Explanation' },
  rag_mode_tafsir_summary: { ar: 'ملخص تفسيري', en: 'Tafsir Summary' },
  rag_mode_tafsir_comparison: { ar: 'مقارنة التفاسير', en: 'Comparing Tafsir Sources' },
  rag_mode_vocabulary: { ar: 'شرح مفردة', en: 'Vocabulary' },
  rag_mode_thematic: { ar: 'تفسير موضوعي', en: 'Thematic' },
  rag_mode_needs_scholar_review: { ar: 'يحتاج مراجعة علمية', en: 'Needs Scholar Review' },
  // Phase E — disclaimer and disagreement
  rag_ai_disclaimer: {
    ar: 'ملخص بمساعدة الذكاء الاصطناعي من المصادر الموثوقة — وليس تفسيراً مستقلاً',
    en: 'AI-assisted summary from verified sources — not independent tafsir',
  },
  rag_disagreement_title: { ar: 'تنبيه: خلاف علمي', en: 'Note: Scholarly Disagreement' },
  ai_explain: { ar: 'الشرح', en: 'Explain' },
  ai_qa: { ar: 'سؤال وجواب', en: 'Q&A' },
  ai_generate_summary: { ar: 'لخّص التفسير', en: 'Summarize Tafsir' },
  ai_select_verse: { ar: 'اختر آية للبدء', en: 'Select a verse to start' },
  ai_select_word: { ar: 'حدد كلمة للشرح', en: 'Select a word to explain' },
  ai_select_word_hint: { ar: 'اختر كلمة من الآية أو اكتبها هنا', en: 'Select a word from the verse or type it here' },
  ai_enter_word: { ar: 'اكتب الكلمة...', en: 'Enter a word...' },
  ai_explanation_of: { ar: 'معنى كلمة: {word}', en: 'Meaning of: {word}' },
  ai_ask_question: { ar: 'اكتب سؤالك هنا...', en: 'Type your question here...' },
  ai_suggested_questions: { ar: 'أسئلة مقترحة:', en: 'Suggested questions:' },
  ai_question_revelation: { ar: 'ما سبب نزول هذه الآية؟', en: 'What is the reason for revelation?' },
  ai_question_lessons: { ar: 'ما الدروس والعبر المستفادة من هذه الآية؟', en: 'What lessons can we learn from this verse?' },
  ai_question_context: { ar: 'ما علاقة هذه الآية بما قبلها وما بعدها؟', en: 'How does this verse relate to its context?' },
  ai_unavailable: { ar: 'الخدمة غير متاحة حالياً', en: 'Service unavailable' },
  ai_timeout: { ar: 'انتهت مهلة الطلب، حاول مرة أخرى', en: 'Request timeout, please try again' },
  ai_open_tafsir_first: { ar: 'اختر آية أولاً لعرض التفسير', en: 'Select a verse first to view tafsir' },

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

  // =============================================================================
  // Phase 6 — Review Workflow (لوحة مراجعة المحتوى)
  // =============================================================================

  // Dashboard
  review_dashboard_title: { ar: 'لوحة مراجعة المحتوى القرآني', en: 'Quran Content Review Dashboard' },
  review_dashboard_subtitle: { ar: 'مراجعة وإقرار المحتوى القرآني الحساس', en: 'Review and approve Quran-sensitive content' },
  review_not_approved_notice: {
    ar: 'لا يعتمد هذا المحتوى إلا بعد مراجعة علمية موثقة.',
    en: 'This content is not approved until documented scholarly review is completed.',
  },

  // Status labels
  review_status_pending: { ar: 'قيد الانتظار', en: 'Pending' },
  review_status_approved: { ar: 'معتمد', en: 'Approved' },
  review_status_rejected: { ar: 'مرفوض', en: 'Rejected' },
  review_status_changes_requested: { ar: 'يحتاج تعديلات', en: 'Changes Requested' },

  // Content types
  review_type_story_segment: { ar: 'مقطع القصة', en: 'Story Segment' },
  review_type_related_story: { ar: 'قصة مرتبطة', en: 'Related Story' },
  review_type_kg_relation: { ar: 'صلة المعرفة', en: 'KG Relation' },
  review_type_source_evidence: { ar: 'دليل المصدر', en: 'Source Evidence' },
  review_type_disagreement_note: { ar: 'ملاحظة خلاف علمي', en: 'Disagreement Note' },

  // Priority
  review_priority_high: { ar: 'أولوية عالية', en: 'High Priority' },
  review_priority_medium: { ar: 'أولوية متوسطة', en: 'Medium Priority' },
  review_priority_low: { ar: 'أولوية منخفضة', en: 'Low Priority' },

  // Decision form
  review_decision_approve: { ar: 'اعتماد', en: 'Approve' },
  review_decision_reject: { ar: 'رفض', en: 'Reject' },
  review_decision_request_changes: { ar: 'طلب تعديلات', en: 'Request Changes' },
  review_reviewer_id: { ar: 'معرّف المراجع', en: 'Reviewer ID' },
  review_reviewer_name: { ar: 'اسم المراجع', en: 'Reviewer Name' },
  review_decision_notes: { ar: 'ملاحظات القرار', en: 'Decision Notes' },
  review_decision_notes_required: { ar: 'ملاحظات القرار مطلوبة', en: 'Decision notes are required' },
  review_decision_notes_placeholder: {
    ar: 'أدخل ملاحظات المراجعة (10 أحرف كحد أدنى)...',
    en: 'Enter review notes (min 10 characters)...',
  },
  review_submit_decision: { ar: 'تقديم القرار', en: 'Submit Decision' },
  review_submitting: { ar: 'جارٍ التقديم...', en: 'Submitting…' },
  review_decision_submitted: { ar: 'تم تقديم القرار بنجاح', en: 'Decision submitted successfully' },

  // Task list
  review_tasks: { ar: 'مهام المراجعة', en: 'Review Tasks' },
  review_task_detail: { ar: 'تفاصيل المهمة', en: 'Task Detail' },
  review_content_id: { ar: 'معرّف المحتوى', en: 'Content ID' },
  review_content_type: { ar: 'نوع المحتوى', en: 'Content Type' },
  review_quran_references: { ar: 'المراجع القرآنية', en: 'Quran References' },
  review_source_ids: { ar: 'معرّفات المصادر', en: 'Source IDs' },
  review_source_evidence: { ar: 'دليل المصدر', en: 'Source Evidence' },
  review_warnings: { ar: 'تحذيرات', en: 'Warnings' },
  review_disagreement_notes: { ar: 'ملاحظات الخلاف العلمي', en: 'Scholarly Disagreement Notes' },
  review_human_review_required: { ar: 'يتطلب مراجعة بشرية', en: 'Human Review Required' },
  review_reviewer: { ar: 'المراجع', en: 'Reviewer' },
  review_reviewed_at: { ar: 'تمت المراجعة في', en: 'Reviewed At' },
  review_no_tasks_found: { ar: 'لا توجد مهام مراجعة', en: 'No review tasks found' },
  review_load_error: { ar: 'تعذر تحميل مهام المراجعة', en: 'Failed to load review tasks' },
  review_task_not_found: { ar: 'المهمة غير موجودة', en: 'Task not found' },

  // Filters
  review_filter_status: { ar: 'تصفية حسب الحالة', en: 'Filter by Status' },
  review_filter_type: { ar: 'تصفية حسب النوع', en: 'Filter by Content Type' },
  review_filter_priority: { ar: 'تصفية حسب الأولوية', en: 'Filter by Priority' },
  review_filter_source: { ar: 'تصفية حسب المصدر', en: 'Filter by Source' },
  review_filter_disagreement: { ar: 'ملاحظات الخلاف فقط', en: 'Disagreement Notes Only' },
  review_filter_human_review: { ar: 'يتطلب مراجعة بشرية فقط', en: 'Requires Human Review Only' },
  review_all_statuses: { ar: 'جميع الحالات', en: 'All Statuses' },
  review_all_types: { ar: 'جميع الأنواع', en: 'All Types' },
  review_all_priorities: { ar: 'جميع الأولويات', en: 'All Priorities' },

  // Stats
  review_stats_total: { ar: 'إجمالي المهام', en: 'Total Tasks' },
  review_stats_pending: { ar: 'قيد الانتظار', en: 'Pending' },
  review_stats_approved: { ar: 'معتمد', en: 'Approved' },
  review_stats_rejected: { ar: 'مرفوض', en: 'Rejected' },
  review_stats_high_priority: { ar: 'أولوية عالية', en: 'High Priority' },
  review_stats_disagreement: { ar: 'خلاف علمي', en: 'Scholarly Disagreements' },
  review_stats_human_review: { ar: 'مراجعة بشرية', en: 'Requires Human Review' },

  // Phase Security — Admin authentication errors
  admin_auth_required_title: {
    ar: 'يتطلب صلاحية إدارية',
    en: 'Admin Authorization Required',
  },
  admin_auth_required_body: {
    ar: 'يتطلب الوصول إلى لوحة المراجعة صلاحية إدارية.',
    en: 'Access to the review dashboard requires admin authorization.',
  },
  admin_auth_not_configured: {
    ar: 'لم يتم تهيئة مفتاح المصادقة الإدارية. تواصل مع مسؤول النظام.',
    en: 'Admin API key is not configured. Set the VITE_ADMIN_API_KEY environment variable.',
  },
  admin_auth_invalid_key: {
    ar: 'مفتاح المصادقة الإدارية غير صالح. تواصل مع مسؤول النظام.',
    en: 'Invalid admin API key. Check the VITE_ADMIN_API_KEY value.',
  },
  admin_auth_retry: { ar: 'إعادة المحاولة', en: 'Retry' },

  // Miracles page
  miracles_page_title: { ar: 'الآيات والمعجزات', en: 'Signs & Miracles' },
  miracles_page_subtitle: { ar: 'آيات القرآن الكريم', en: 'Quranic Signs (Ayāt)' },
  miracles_page_description: {
    ar: 'استكشف الآيات والمعجزات المذكورة في القرآن الكريم — من معجزات الأنبياء إلى الآيات الكونية. كل آية موثقة بمراجع قرآنية.',
    en: 'Explore the signs and miracles mentioned in the Holy Quran — from prophetic miracles to cosmic signs. Each is grounded in Quranic verse references.',
  },
  miracles_stat_total: { ar: 'آية ومعجزة', en: 'Signs & Miracles' },
  miracles_stat_prophetic: { ar: 'معجزات مرتبطة بأنبياء', en: 'Prophet-linked Miracles' },
  miracles_stat_occurrences: { ar: 'إجمالي المواضع', en: 'Total Occurrences' },
  miracles_section_prophetic: { ar: 'معجزات الأنبياء', en: 'Prophetic Miracles' },
  miracles_section_other: { ar: 'آيات أخرى', en: 'Other Signs' },
  miracles_empty: {
    ar: 'لم يتم العثور على آيات. يرجى تشغيل سكريبت بذر المفاهيم.',
    en: 'No miracles found. Please run the concept seeding script.',
  },
  miracles_related_figures: { ar: 'الشخصيات المرتبطة', en: 'Related Figures' },
  miracles_related_stories: { ar: 'القصص المرتبطة', en: 'Related Stories' },
  miracles_view_prophet: { ar: 'عرض النبي المرتبط', en: 'View Related Prophet' },
  miracles_explore_more: { ar: 'استكشف المزيد', en: 'Explore More' },
  miracles_all_concepts: { ar: 'جميع المفاهيم', en: 'All Concepts' },
  miracles_story_atlas: { ar: 'أطلس القصص', en: 'Story Atlas' },
  miracles_refs_label: { ar: 'موضع', en: 'refs' },
  miracles_safety_title: {
    ar: 'ملاحظة: الآيات القرآنية والادعاءات العلمية',
    en: 'Note: Quranic Signs vs. Scientific Miracle Claims',
  },
  miracles_safety_body: {
    ar: 'هذه الصفحة تعرض الآيات والمعجزات المذكورة صراحةً في القرآن الكريم (معجزات الأنبياء، والآيات الكونية). أما ربط الآيات بالنظريات العلمية الحديثة فيحتاج إلى مراجعة علمية وشرعية متخصصة — ولا يُعرض هنا كتفسير معتمد.',
    en: 'This page shows signs and miracles explicitly mentioned in the Quran (prophetic miracles, cosmic signs). Linking verses to modern scientific theories requires specialized scholarly and scientific review — it is not presented here as approved tafsir.',
  },
  miracles_safety_label: {
    ar: 'سياسة الآيات العلمية',
    en: 'Scientific-Claims Policy',
  },

  // Phase F — Vocabulary module
  vocab_page_title: { ar: 'غريب القرآن', en: 'Quranic Vocabulary' },
  vocab_page_subtitle: {
    ar: 'ابحث في معاني مفردات القرآن الكريم من أمهات المعاجم العربية الكلاسيكية',
    en: 'Look up Quranic word meanings from the great classical Arabic lexicons',
  },
  vocab_about_gharib: {
    ar: 'علم «غريب القرآن» يُعنى بشرح الكلمات النادرة والدقيقة في القرآن الكريم التي تحتاج إلى الرجوع إلى المعاجم العربية الكلاسيكية الموثوقة — لا يُولَّد المعنى من الذكاء الاصطناعي وحده.',
    en: '"Gharib Al-Quran" (غريب القرآن) is the classical science of explaining rare and precise Quranic words. Every meaning must be traced to a verified classical lexicon — never AI-generated alone.',
  },
  vocab_search_placeholder: {
    ar: 'أدخل كلمة قرآنية، مثل: رحمة، صمد، تقوى...',
    en: 'Enter a Quranic word, e.g. رحمة, صمد, تقوى...',
  },
  vocab_search_button: { ar: 'بحث', en: 'Search' },
  vocab_try_examples: { ar: 'جرّب هذه الكلمات:', en: 'Try these words:' },
  vocab_no_source_title: { ar: 'لا يتوفر مصدر موثوق لهذه المفردة بعد', en: 'No Verified Source Available Yet' },
  vocab_planned_label: { ar: 'قيد التطوير — قريبًا', en: 'Under Development — Coming Soon' },
  vocab_planned_sources_label: {
    ar: 'المصادر الموثوقة المخطط دمجها:',
    en: 'Verified classical sources to be integrated:',
  },
  vocab_sources_classical_ar_label: {
    ar: 'المعاجم العربية الكلاسيكية',
    en: 'Classical Arabic Lexicons',
  },
  vocab_sources_english_digital_label: {
    ar: 'المعاجم الإنجليزية والرقمية',
    en: 'English & Digital Lexicons',
  },
  vocab_source_era_label: { ar: 'العصر:', en: 'Era:' },
  vocab_source_focus_label: { ar: 'التخصص:', en: 'Focus:' },
  vocab_source_volumes_label: { ar: 'الأجزاء:', en: 'Vols.' },
  vocab_source_status_planned: { ar: 'مخطط للتكامل', en: 'Planned' },
  vocab_refusal_try_tafsir: {
    ar: 'للاستفسار عن معنى الآية، يمكنك استخدام مساعد التدبر.',
    en: "To explore a verse's meaning, try the Tafsir Assistant.",
  },
  vocab_policy_note: {
    ar: 'لا يُولَّد معنى المفردة من الذكاء الاصطناعي وحده — يجب أن يصدر كل شرح من مصدر موثوق.',
    en: 'Word meanings are never AI-generated alone — every entry must come from a verified classical source.',
  },
  vocab_tool_name: { ar: 'غريب القرآن', en: 'Quranic Vocabulary' },
  vocab_tool_description: {
    ar: 'ابحث في معاني مفردات القرآن الكريم من أمهات المعاجم العربية الكلاسيكية الموثوقة',
    en: 'Look up Quranic word meanings from the great verified classical Arabic lexicons',
  },

  // Phase 6.5 – Review status propagation overlay
  review_overlay_approved: { ar: 'معتمد', en: 'Approved' },
  review_overlay_partially_reviewed: { ar: 'مراجعة جزئية', en: 'Partially Reviewed' },
  review_overlay_needs_review: { ar: 'بانتظار المراجعة', en: 'Needs Review' },
  review_overlay_changes_requested: { ar: 'يحتاج تعديلات', en: 'Changes Requested' },
  review_overlay_rejected: { ar: 'مرفوض', en: 'Rejected' },
  review_overlay_reviewed_by: { ar: 'راجعه:', en: 'Reviewed by:' },
  review_overlay_reviewed_at: { ar: 'تاريخ المراجعة:', en: 'Reviewed:' },
  review_overlay_notes_summary: { ar: 'ملاحظات المراجع:', en: 'Reviewer notes:' },
  review_overlay_partial_segments: { ar: 'مقاطع تمت مراجعتها', en: 'segments reviewed' },
  review_overlay_freshness_label: { ar: 'آخر تحديث للطبقة:', en: 'Overlay last updated:' },
  review_overlay_stale_warning: { ar: 'طبقة الحالة قد تكون قديمة — أعِد التوليد بعد القرارات الجديدة.', en: 'Status overlay may be stale — regenerate after new decisions.' },
  review_overlay_not_generated: { ar: 'طبقة الحالة غير موجودة — أعِد تشغيل سكريبت التوليد', en: 'Status overlay not generated — run propagate-review-status.ts' },
  review_overlay_all_pending: { ar: 'جميع المهام قيد الانتظار — لا توجد قرارات بعد.', en: 'All tasks pending — no decisions submitted yet.' },

  // Phase K — Scientific miracle safety caution card
  scientific_caution_title: {
    ar: 'تنبيه: ادعاء علمي يحتاج إلى مراجعة',
    en: 'Note: Scientific Claim Requires Review',
  },
  scientific_caution_body: {
    ar: 'تنبيه: الربط بين الآيات والنظريات العلمية يحتاج إلى مراجعة علمية وشرعية متخصصة، ولا يُعرض هنا كتفسير معتمد.',
    en: 'Note: Connecting ayahs to scientific theories requires specialized scholarly and scientific review. It is not shown here as approved tafsir.',
  },
  scientific_caution_reflection_label: {
    ar: 'تأمل معاصر — ليس تفسيرًا معتمدًا',
    en: 'Contemporary reflection — not approved tafsir',
  },

  // Phase L — Safe Quran AI Prompting Guide
  prompt_guide_tool_name: {
    ar: 'دليل الأسئلة الآمنة',
    en: 'Safe Prompting Guide',
  },
  prompt_guide_tool_description: {
    ar: 'تعرّف على كيفية طرح أسئلة آمنة ودقيقة حول القرآن الكريم في هذه المنصة',
    en: 'Learn how to ask safe, precise Quranic questions on this AI-assisted platform',
  },
  prompt_guide_title: {
    ar: 'دليل الأسئلة الآمنة للذكاء الاصطناعي القرآني',
    en: 'Safe Quran AI Prompting Guide',
  },
  prompt_guide_subtitle: {
    ar: 'كيفية طرح أسئلة آمنة ودقيقة حول القرآن الكريم في منصة مدعومة بالذكاء الاصطناعي',
    en: 'How to ask safe, precise Quranic questions on an AI-assisted platform',
  },
  prompt_guide_purpose_title: { ar: 'الهدف', en: 'Purpose' },
  prompt_guide_purpose_body: {
    ar: 'الذكاء الاصطناعي مساعد، ليس عالمًا. هذا الدليل يساعدك على طرح أسئلة دقيقة موثوقة المصدر تحترم ضوابط العلم الشرعي.',
    en: 'AI is a helper, not a scholar. This guide helps you ask precise, source-backed questions that respect the discipline of Quranic scholarship.',
  },
  prompt_guide_principles_title: { ar: 'المبادئ الأساسية', en: 'Core Principles' },
  prompt_guide_good_examples_title: { ar: 'أمثلة على الأسئلة الجيدة', en: 'Good Prompt Examples' },
  prompt_guide_unsafe_examples_title: { ar: 'أمثلة على الأسئلة غير الآمنة', en: 'Unsafe Prompt Examples' },
  prompt_guide_protection_title: { ar: 'كيف تحميك المنصة', en: 'How the Platform Protects You' },
  prompt_guide_ask_sources: {
    ar: 'اطلب المصادر — دائمًا اسأل عن المصدر والمؤلف',
    en: 'Ask for sources — always request the source and author',
  },
  prompt_guide_ask_ayah: {
    ar: 'اذكر الآية — حدد رقم السورة والآية بدقة',
    en: 'Specify the ayah — include surah and ayah number',
  },
  prompt_guide_ask_tafsir_source: {
    ar: 'اذكر كتاب التفسير — مثلاً: ابن كثير، الطبري، السعدي',
    en: 'Name the tafsir — e.g. Ibn Kathir, Al-Tabari, Al-Saadi',
  },
  prompt_guide_ask_comparison: {
    ar: 'اطلب المقارنة عند الخلاف — قل: ما الذي قاله العلماء في هذه المسألة؟',
    en: 'Ask for comparison when scholars differ — say: what do scholars say?',
  },
  prompt_guide_no_unsourced: {
    ar: 'لا تطلب تفسيرًا بدون مصادر',
    en: 'Do not ask for tafsir without sources',
  },
  prompt_guide_no_fatwa: {
    ar: 'لا تطلب فتوى — الذكاء الاصطناعي لا يُفتي',
    en: 'Do not ask for a fatwa — AI does not issue religious rulings',
  },
  prompt_guide_no_prove_science: {
    ar: 'لا تطلب إثبات نظريات علمية من القرآن',
    en: 'Do not ask AI to prove scientific theories from the Quran',
  },
  prompt_guide_no_hidden_meaning: {
    ar: 'لا تطلب المعنى الخفي أو الباطني للآيات',
    en: 'Do not ask for hidden or esoteric meanings of verses',
  },
  prompt_guide_consult_scholars: {
    ar: 'ارجع إلى العلماء للأحكام الشرعية',
    en: 'Consult qualified scholars for religious rulings',
  },
  prompt_guide_ai_not_scholar: {
    ar: 'الذكاء الاصطناعي مساعد، ليس عالمًا',
    en: 'AI is an assistant, not a scholar',
  },
  prompt_guide_fatwa_warning: {
    ar: 'تحذير: المنصة لا تصدر فتاوى — يُرجى الرجوع إلى عالم مؤهل',
    en: 'Warning: This platform does not issue fatwas — please consult a qualified scholar',
  },
  prompt_guide_scientific_warning: {
    ar: 'تحذير: الربط بين الآيات والنظريات العلمية يحتاج إلى مراجعة علمية وشرعية متخصصة',
    en: 'Warning: Connecting ayahs to scientific theories requires specialized scholarly and scientific review',
  },
  prompt_guide_no_verified_source: {
    ar: 'لا يوجد مصدر موثوق متاح لهذه الإجابة.',
    en: 'No verified source available for this answer.',
  },

  // Feedback system (Phase G)
  feedback_button_label: { ar: 'أبلغ عن مشكلة', en: 'Report an Issue' },
  feedback_dialog_title: { ar: 'أبلِغنا عن مشكلة', en: 'Report an Issue' },
  feedback_dialog_subtitle: {
    ar: 'ساعدنا في تحسين جودة المحتوى من خلال الإبلاغ عن أي أخطاء أو مشكلات.',
    en: 'Help us improve content quality by reporting errors or issues.',
  },
  feedback_category_label: { ar: 'نوع المشكلة', en: 'Issue Type' },
  feedback_message_label: { ar: 'تفاصيل المشكلة', en: 'Issue Details' },
  feedback_message_placeholder: {
    ar: 'صِف المشكلة بإيجاز (10 أحرف على الأقل)…',
    en: 'Describe the issue briefly (at least 10 characters)…',
  },
  feedback_submit: { ar: 'إرسال', en: 'Submit' },
  feedback_submitting: { ar: 'جارٍ الإرسال…', en: 'Submitting…' },
  feedback_success: { ar: 'شكراً! تم استلام تقريرك.', en: 'Thank you! Your report has been received.' },
  feedback_error: { ar: 'حدث خطأ. يرجى المحاولة مجدداً.', en: 'Something went wrong. Please try again.' },
  feedback_cancel: { ar: 'إلغاء', en: 'Cancel' },
  feedback_cat_translation_issue: { ar: 'مشكلة في الترجمة', en: 'Translation Issue' },
  feedback_cat_source_missing: { ar: 'مصدر مفقود', en: 'Source Missing' },
  feedback_cat_tafsir_error: { ar: 'خطأ في التفسير', en: 'Tafsir Error' },
  feedback_cat_quran_ref_error: { ar: 'خطأ في المرجع القرآني', en: 'Quran Reference Error' },
  feedback_cat_ui_feedback: { ar: 'ملاحظة على الواجهة', en: 'UI / UX Feedback' },
  feedback_cat_inappropriate: { ar: 'محتوى غير لائق', en: 'Inappropriate Content' },
  feedback_cat_other: { ar: 'أخرى', en: 'Other' },

  // Admin feedback dashboard (Phase G)
  admin_feedback_title: { ar: 'لوحة تقارير المستخدمين', en: 'User Feedback Dashboard' },
  admin_feedback_total: { ar: 'إجمالي التقارير', en: 'Total Reports' },
  admin_feedback_open_high: { ar: 'ذات أولوية عالية', en: 'High Priority Open' },
  admin_feedback_status_open: { ar: 'مفتوح', en: 'Open' },
  admin_feedback_status_in_review: { ar: 'قيد المراجعة', en: 'In Review' },
  admin_feedback_status_resolved: { ar: 'محلول', en: 'Resolved' },
  admin_feedback_status_dismissed: { ar: 'مُغلق', en: 'Dismissed' },
  admin_feedback_notes_label: { ar: 'ملاحظات المراجع', en: 'Admin Notes' },
  admin_feedback_save: { ar: 'حفظ', en: 'Save' },
  admin_feedback_no_items: { ar: 'لا توجد تقارير حالياً.', en: 'No feedback reports yet.' },
  admin_feedback_filter_all: { ar: 'الكل', en: 'All' },

  // Phase I — Thematic Tafsir tab
  theme_tafsir_tab: { ar: 'التفسير الموضوعي', en: 'Tafsir' },
  theme_stories_tab: { ar: 'القصص المرتبطة', en: 'Related Stories' },
  theme_tafsir_loading: { ar: 'جارٍ تحميل التفسير…', en: 'Loading tafsir…' },
  theme_tafsir_empty: { ar: 'لا يوجد تفسير متاح لهذا المحور', en: 'No tafsir available for this theme' },
  theme_stories_empty: { ar: 'لا توجد قصص مرتبطة بهذا المحور', en: 'No related stories found' },
  theme_tafsir_sources_used: { ar: 'المصادر المستخدمة', en: 'Sources used' },
  theme_tafsir_source_backed: { ar: 'موثق بالمصادر', en: 'Source-backed' },
  theme_tafsir_partial_coverage: { ar: 'تغطية جزئية', en: 'Partial coverage' },
  theme_tafsir_needs_review: { ar: 'يحتاج مراجعة', en: 'Needs review' },
  theme_tafsir_verified: { ar: 'موثق', en: 'Verified' },
  theme_tafsir_show_tafsir: { ar: 'عرض التفسير', en: 'Show tafsir' },
  theme_tafsir_hide_tafsir: { ar: 'إخفاء التفسير', en: 'Hide tafsir' },
  theme_tafsir_filter_source: { ar: 'تصفية حسب المصدر', en: 'Filter by source' },
  theme_tafsir_filter_verified: { ar: 'المقاطع الموثقة فقط', en: 'Verified segments only' },
  theme_stories_shared_themes: { ar: 'المحاور المشتركة', en: 'Shared themes' },
  theme_stories_view: { ar: 'عرض القصة', en: 'View story' },

  // Surah Memory Atlas (Phase SMA)
  sma_title: { ar: 'تذكّر ترتيب السور', en: 'Surah Memory Atlas' },
  sma_description: {
    ar: 'تعلّم أسماء السور الـ١١٤ وترتيبها ومعلوماتها الأساسية — أداة تفاعلية للحفظ والمراجعة',
    en: 'Learn all 114 surah names, their order, and key facts — an interactive tool for memorization and review',
  },
  sma_search_placeholder: { ar: 'ابحث بالاسم أو الرقم…', en: 'Search by name or number…' },
  sma_filter_revelation: { ar: 'نوع الوحي', en: 'Revelation Type' },
  sma_filter_length: { ar: 'الطول', en: 'Length' },
  sma_filter_position: { ar: 'الموضع', en: 'Position' },
  sma_filter_all: { ar: 'الكل', en: 'All' },
  sma_makki: { ar: 'مكي', en: 'Makki' },
  sma_madani: { ar: 'مدني', en: 'Madani' },
  sma_unknown: { ar: 'غير محدد', en: 'Unknown' },
  sma_short: { ar: 'قصيرة (١–٢٠)', en: 'Short (1–20)' },
  sma_medium: { ar: 'متوسطة (٢١–٨٠)', en: 'Medium (21–80)' },
  sma_long: { ar: 'طويلة (٨١–١٨٠)', en: 'Long (81–180)' },
  sma_very_long: { ar: 'طويلة جداً (١٨١+)', en: 'Very Long (181+)' },
  sma_beginning: { ar: 'البداية (١–١٠)', en: 'Beginning (1–10)' },
  sma_early: { ar: 'أوائل (١١–٣٠)', en: 'Early (11–30)' },
  sma_middle: { ar: 'وسط (٣١–٧٠)', en: 'Middle (31–70)' },
  sma_late: { ar: 'أواخر (٧١–١٠٠)', en: 'Late (71–100)' },
  sma_ending: { ar: 'الخواتيم (١٠١–١١٤)', en: 'Ending (101–114)' },
  sma_ayah_count: { ar: 'عدد الآيات', en: 'Ayah Count' },
  sma_length: { ar: 'الطول', en: 'Length' },
  sma_quran_position: { ar: 'الموضع في القرآن', en: 'Quran Position' },
  sma_juz: { ar: 'الجزء', en: 'Juz' },
  sma_page_range: { ar: 'نطاق الصفحات', en: 'Page Range' },
  sma_first_ayah: { ar: 'أول آية', en: 'First Ayah' },
  sma_last_ayah: { ar: 'آخر آية', en: 'Last Ayah' },
  sma_main_topics: { ar: 'المحاور الرئيسية', en: 'Main Topics' },
  sma_memory_clue: { ar: 'مفتاح الحفظ', en: 'Memory Clue' },
  sma_previous_surah: { ar: 'السورة السابقة', en: 'Previous Surah' },
  sma_next_surah: { ar: 'السورة التالية', en: 'Next Surah' },
  sma_test_yourself: { ar: 'اختبر نفسك', en: 'Test Yourself' },
  sma_show_answer: { ar: 'أظهر الجواب', en: 'Show Answer' },
  sma_correct: { ar: 'صحيح!', en: 'Correct!' },
  sma_try_again: { ar: 'حاول مجدداً', en: 'Try Again' },
  sma_metadata_unavailable: {
    ar: 'بعض بيانات هذه السورة غير متوفرة من مصدر موثوق حالياً.',
    en: 'Some metadata for this surah is not available from a verified source yet.',
  },
  sma_needs_review: {
    ar: 'هذه المعلومة تحتاج إلى مراجعة قبل اعتمادها.',
    en: 'This information requires review before approval.',
  },
  sma_verified: { ar: 'موثق', en: 'Verified' },
  sma_review_required: { ar: 'يحتاج مراجعة', en: 'Needs Review' },
  sma_data_missing: { ar: 'غير متوفر', en: 'Unavailable' },
  sma_select_surah_prompt: {
    ar: 'اختر سورة لعرض تفاصيلها',
    en: 'Select a surah to view its details',
  },
  sma_surah_number: { ar: 'رقم السورة', en: 'Surah Number' },
  sma_arabic_name: { ar: 'الاسم العربي', en: 'Arabic Name' },
  sma_english_name: { ar: 'المعنى بالإنجليزية', en: 'English Meaning' },
  sma_transliteration: { ar: 'النطق بالحروف اللاتينية', en: 'Transliteration' },
  sma_revelation_type: { ar: 'نوع الوحي', en: 'Revelation Type' },
  sma_position_clue: { ar: 'دليل الموضع', en: 'Position Clue' },
  sma_length_clue: { ar: 'دليل الطول', en: 'Length Clue' },
  sma_topic_clue: { ar: 'دليل الموضوع', en: 'Topic Clue' },
  sma_before_after: { ar: 'قبلها وبعدها', en: 'Before & After' },
  sma_quiz_q_before: { ar: 'ما السورة التي قبلها؟', en: 'What surah comes before?' },
  sma_quiz_q_after: { ar: 'ما السورة التي بعدها؟', en: 'What surah comes after?' },
  sma_quiz_q_type: { ar: 'هل هي مكية أم مدنية؟', en: 'Is it Makki or Madani?' },
  sma_quiz_q_length: { ar: 'ما تقريب عدد آياتها؟', en: 'How many ayahs approximately?' },
  sma_quiz_q_number: { ar: 'ما رقم هذه السورة في القرآن؟', en: 'What is the number of this surah?' },
  sma_quiz_q_name: { ar: 'ما اسم السورة رقم', en: 'What is the name of surah number' },
  sma_visual_map_title: { ar: 'خريطة السور', en: 'Surah Visual Map' },
  sma_results_count: { ar: 'نتيجة', en: 'result(s)' },
  sma_no_results: { ar: 'لا توجد نتائج للبحث', en: 'No surahs found' },
  sma_clear_filters: { ar: 'مسح الفلاتر', en: 'Clear Filters' },
  sma_page: { ar: 'صفحة', en: 'Page' },
  sma_to: { ar: 'إلى', en: 'to' },
  sma_quiz_mode: { ar: 'وضع الاختبار', en: 'Quiz Mode' },
  sma_map_view: { ar: 'عرض الخريطة', en: 'Map View' },
  sma_list_view: { ar: 'عرض القائمة', en: 'List View' },
  sma_detail_panel: { ar: 'تفاصيل السورة', en: 'Surah Details' },
  sma_next_question: { ar: 'السؤال التالي', en: 'Next Question' },
  sma_score: { ar: 'النتيجة', en: 'Score' },
  sma_of: { ar: 'من', en: 'of' },
  sma_grid_view: { ar: 'الشبكة', en: 'Grid' },
  sma_read_in_quran: { ar: 'اقرأ في القرآن', en: 'Read in Quran' },
  sma_open_in_mushaf: { ar: 'افتح المصحف', en: 'Open in Mushaf' },
  sma_close_panel: { ar: 'إغلاق', en: 'Close' },
  sma_ayahs_short: { ar: 'آيات', en: 'ayahs' },
  sma_pages_abbr: { ar: 'ص', en: 'p.' },
  sma_first_preview: { ar: 'مطلع السورة', en: 'Opening Verse' },
  sma_last_preview: { ar: 'خاتمة السورة', en: 'Closing Verse' },
  sma_read_full_surah: { ar: 'اقرأ السورة كاملة', en: 'Read full surah' },
  sma_read_verse: { ar: 'اقرأ الآية', en: 'Read verse' },
  sma_in_mushaf: { ar: 'في المصحف', en: 'in Mushaf' },
  sma_memory_aid: { ar: 'مساعد الحفظ', en: 'Memory Aid' },
  sma_position_in_quran: { ar: 'الموضع في المصحف', en: 'Position in Quran' },
  sma_relative_length: { ar: 'الطول النسبي', en: 'Relative Length' },
  sma_makki_label: { ar: 'مكية', en: 'Makki' },
  sma_madani_label: { ar: 'مدنية', en: 'Madani' },
  sma_juz_range_lbl: { ar: 'الأجزاء', en: 'Juz' },
  sma_page_lbl: { ar: 'الصفحات', en: 'Pages' },
  sma_keyboard_hint: {
    ar: 'اضغط ← → للتنقل بين السور',
    en: 'Press ← → to navigate between surahs',
  },
  sma_all_114: { ar: 'جميع السور الـ١١٤', en: 'All 114 Surahs' },
  sma_overview_stats: { ar: 'إحصائيات المصحف', en: 'Quran Statistics' },
  sma_surah_prefix: { ar: 'سورة', en: 'Surah' },
  sma_before_surah: { ar: 'قبلها', en: 'Before' },
  sma_after_surah: { ar: 'بعدها', en: 'After' },
  sma_first_surah: { ar: 'أول سورة', en: 'First surah' },
  sma_last_surah: { ar: 'آخر سورة', en: 'Last surah' },
  sma_opening_verses: { ar: 'مطلع السورة', en: 'Opening Verses' },
  sma_middle_passage: { ar: 'من وسط السورة', en: 'Middle Passage' },
  sma_closing_verses: { ar: 'خاتمة السورة', en: 'Closing Verses' },
  sma_related_stories: { ar: 'قصص مرتبطة', en: 'Related Stories' },
  sma_view_story: { ar: 'اقرأ القصة', en: 'Read Story' },
  sma_story_in_surah: { ar: 'تتضمن السورة', en: 'This surah contains' },
  sma_themes: { ar: 'الموضوعات', en: 'Themes' },
  sma_key_figures: { ar: 'الشخصيات', en: 'Key Figures' },
  sma_surah_word: { ar: 'سورة', en: 'Surahs' },

  // Spiritual Guidance / Emotional Support — Phase T
  // ============================================================
  nav_therapy: { ar: 'رعاية القلب', en: 'Heart Care' },
  therapy_title: { ar: 'رعاية القلب', en: 'Heart Care' },
  therapy_subtitle: {
    ar: 'دعم روحاني قرآني لكل حالة يمر بها القلب — تأمّل، اسأل، واشفَ',
    en: 'Quranic spiritual support for every state of the heart',
  },
  therapy_themes_title: { ar: 'مواضيع الشفاء', en: 'Healing Themes' },
  therapy_themes_subtitle: {
    ar: 'استكشف مواضيع القرآن العلاجية أو شارك ما تشعر به',
    en: 'Explore Quranic healing themes or share what you feel',
  },
  therapy_share_prompt: {
    ar: 'شارك ما يعتمل في قلبك',
    en: 'Share what is in your heart',
  },
  therapy_input_placeholder: {
    ar: 'صِف ما تشعر به... القرآن يتحدث إلى كل حالة',
    en: 'Describe what you are feeling… The Quran speaks to every state',
  },
  therapy_ctrl_enter: {
    ar: 'اضغط للإرسال',
    en: 'Ctrl + Enter to send',
  },
  therapy_seek_guidance: { ar: 'اطلب التوجيه', en: 'Seek Guidance' },
  therapy_seeking: { ar: 'جارٍ البحث...', en: 'Seeking…' },
  therapy_examples: { ar: 'أمثلة للمشاعر:', en: 'Example feelings:' },
  therapy_guidance_title: { ar: 'توجيه روحي', en: 'Spiritual Guidance' },
  therapy_emotion_detected: { ar: 'الحالة المشعورة:', en: 'Emotion detected:' },
  therapy_verse: { ar: 'الآية الكريمة', en: 'Quranic Verse' },
  therapy_lesson: { ar: 'الدرس والمعنى', en: 'Lesson & Meaning' },
  therapy_reflection: { ar: 'تأمل واستفسر', en: 'Reflect & Explore' },
  therapy_dua_suggested: { ar: 'دعاء مقترح', en: "Suggested Du'a" },
  therapy_follow_up: { ar: 'لمزيد من التدبر', en: 'Explore Further' },
  therapy_recommended_themes: { ar: 'مواضيع مقترحة لحالتك', en: 'Recommended themes for you' },
  therapy_explore_theme: { ar: 'استكشف الموضوع', en: 'Explore theme' },
  therapy_disclaimer_title: { ar: 'تنبيه مهم', en: 'Important Note' },
  therapy_reflection_log: { ar: 'سجل التأمل', en: 'Reflection Log' },
  therapy_write_reflection: { ar: 'دوّن تأملك حول هذه الجلسة:', en: 'Write your reflection on this session:' },
  therapy_reflection_placeholder: {
    ar: 'ما الذي لفت انتباهك؟ كيف أثّرت فيك الآيات؟',
    en: 'What stood out to you? How did the verses affect you?',
  },
  therapy_save_reflection: { ar: 'حفظ التأمل', en: 'Save Reflection' },
  therapy_saving: { ar: 'جارٍ الحفظ...', en: 'Saving…' },
  therapy_no_reflections: { ar: 'لا توجد تأملات محفوظة بعد', en: 'No saved reflections yet' },
  therapy_session_saved: { ar: 'تم حفظ الجلسة', en: 'Session saved' },
  therapy_no_cards: {
    ar: 'لا توجد آيات متاحة حالياً. يرجى التحقق من قاعدة البيانات.',
    en: 'No verses available right now. Please check the database.',
  },
  therapy_cards_count: { ar: 'توجيهات قرآنية', en: 'Quranic Guidances' },
  therapy_theme_page_title: { ar: 'استكشاف الموضوع', en: 'Theme Exploration' },
  therapy_back: { ar: 'العودة', en: 'Back' },
  therapy_reinforcement: { ar: 'تشجيع', en: 'Encouragement' },
  therapy_chat_mode: { ar: 'نمط المحادثة', en: 'Chat Mode' },
  therapy_guidance_mode: { ar: 'نمط التوجيه', en: 'Guidance Mode' },
  therapy_chat_tab: { ar: 'محادثة القرآن', en: 'QuranGPT Chat' },
  therapy_guidance_tab: { ar: 'بطاقات التوجيه', en: 'Guidance Cards' },
  therapy_insights_tab: { ar: 'رحلتي', en: 'My Journey' },
  therapy_ruqyah_tab:   { ar: 'رقية وذكر', en: 'Ruqyah & Dhikr' },
  therapy_duas_tab:     { ar: 'أدعية نبوية', en: "Prophetic Du'as" },
  therapy_daily_tab:    { ar: 'ممارسات يومية', en: 'Daily Practices' },
  therapy_intro_title:  { ar: 'القرآن شفاء للقلوب', en: 'The Quran — Healing for the Heart' },
  therapy_intro_verse:  { ar: 'القرآن شفاءٌ ورحمةٌ للمؤمنين', en: '"We send down of the Quran what is a healing and a mercy to those who believe"' },
  therapy_intro_ref:    { ar: 'سورة الإسراء، الآية ٨٢', en: 'Al-Isra 17:82' },
  // Chat UI
  chat_intro: { ar: 'شاركني ما تشعر به وسأرشدك بالقرآن الكريم.', en: 'Share what you are feeling and I will guide you with the Quran.' },
  chat_placeholder: { ar: 'اكتب رسالتك هنا...', en: 'Type your message here…' },
  chat_error: { ar: 'حدث خطأ. يُرجى المحاولة مرة أخرى.', en: 'Something went wrong. Please try again.' },
  // Insights
  insights_title: { ar: 'رحلتي العاطفية', en: 'My Emotional Journey' },
  insights_sessions: { ar: 'جلسات', en: 'Sessions' },
  insights_top_theme: { ar: 'الموضوع الأكثر زيارة', en: 'Top Theme' },
  insights_top_emotion: { ar: 'أكثر المشاعر حضوراً', en: 'Most Present Emotion' },
  insights_distribution: { ar: 'توزيع المشاعر', en: 'Emotion Distribution' },
  insights_growth_prompt: { ar: 'اقتراح للنمو', en: 'Growth Suggestion' },
  therapy_suggested_theme: { ar: 'موضوع مقترح:', en: 'Suggested theme:' },
  // Adaptive tone profile labels
  tone_gentle:      { ar: 'لطيف',    en: 'Gentle' },
  tone_supportive:  { ar: 'داعم',    en: 'Supportive' },
  tone_celebratory: { ar: 'احتفالي', en: 'Celebratory' },
  tone_welcoming:   { ar: 'مرحّب',   en: 'Welcoming' },
};

// Story categories translation map
export const categoryTranslations: Record<string, { ar: string; en: string }> = {
  prophet: { ar: 'قصص الأنبياء', en: 'Prophets' },
  nation: { ar: 'قصص الأمم', en: 'Nations' },
  parable: { ar: 'أمثال وعبر', en: 'Parables' },
  historical: { ar: 'أحداث تاريخية', en: 'Historical' },
  righteous: { ar: 'الصالحين', en: 'Righteous' },
  unseen: { ar: 'الغيبيات', en: 'Unseen' },
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
  // Therapy healing themes
  strength: { ar: 'القوة', en: 'strength' },
  ruqyah: { ar: 'الرقية الشرعية', en: 'ruqyah' },
  contentment: { ar: 'القناعة', en: 'contentment' },
  // Additional themes from database
  acceptance: { ar: 'القبول', en: 'acceptance' },
  answered_prayer: { ar: 'استجابة الدعاء', en: 'Answered Prayer' },
  ascension: { ar: 'الصعود', en: 'ascension' },
  chastity: { ar: 'العفة', en: 'chastity' },
  confronting_tyranny: { ar: 'مواجهة الطغيان', en: 'Confronting Tyranny' },
  courage: { ar: 'الشجاعة', en: 'courage' },
  destruction: { ar: 'الهلاك', en: 'destruction' },
  devotion: { ar: 'الإخلاص', en: 'devotion' },
  disobedience: { ar: 'العصيان', en: 'disobedience' },
  divine_mercy: { ar: 'الرحمة الإلهية', en: 'Divine Mercy' },
  divine_planning: { ar: 'التدبير الإلهي', en: 'Divine Planning' },
  divine_power: { ar: 'القدرة الإلهية', en: 'Divine Power' },
  divine_protection: { ar: 'الحماية الإلهية', en: 'Divine Protection' },
  divine_punishment: { ar: 'العقاب الإلهي', en: 'Divine Punishment' },
  divine_support: { ar: 'التأييد الإلهي', en: 'Divine Support' },
  father_of_prophets: { ar: 'أبو الأنبياء', en: 'Father of Prophets' },
  first_murder: { ar: 'أول جريمة قتل', en: 'First Murder' },
  hajj: { ar: 'الحج', en: 'hajj' },
  honesty: { ar: 'الصدق', en: 'honesty' },
  humility: { ar: 'التواضع', en: 'humility' },
  kaaba: { ar: 'الكعبة', en: 'kaaba' },
  kingdom: { ar: 'الملك', en: 'kingdom' },
  liberation: { ar: 'التحرير', en: 'liberation' },
  miraculous_birth: { ar: 'الولادة المعجزة', en: 'Miraculous Birth' },
  morality: { ar: 'الأخلاق', en: 'morality' },
  parenting: { ar: 'التربية', en: 'parenting' },
  purity: { ar: 'الطهارة', en: 'purity' },
  questioning: { ar: 'التساؤل', en: 'questioning' },
  reconciliation: { ar: 'المصالحة', en: 'reconciliation' },
  righteousness: { ar: 'الصلاح', en: 'righteousness' },
  salvation: { ar: 'الخلاص', en: 'salvation' },
  signs: { ar: 'الآيات', en: 'signs' },
  time: { ar: 'الزمن', en: 'time' },
  trade_ethics: { ar: 'أخلاق التجارة', en: 'Trade Ethics' },
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
  historical_inquiry: { ar: 'التساؤل التاريخي', en: 'Historical Inquiry' },

  // Divine empowerment tags
  divine_empowerment: { ar: 'التمكين الإلهي', en: 'Divine Empowerment' },
  tamkeen: { ar: 'التمكين', en: 'tamkeen' },
  authority: { ar: 'السلطة', en: 'authority' },
  resources: { ar: 'الموارد', en: 'resources' },

  // Journey and direction tags
  west: { ar: 'الغرب', en: 'west' },
  east: { ar: 'الشرق', en: 'east' },
  sun_setting: { ar: 'غروب الشمس', en: 'Sunset Direction' },
  sun_rising: { ar: 'شروق الشمس', en: 'Sunrise Direction' },
  exploration: { ar: 'الاستكشاف', en: 'exploration' },
  primitive_people: { ar: 'شعوب بدائية', en: 'Primitive Peoples' },

  // Test and moral decision tags
  test: { ar: 'الاختبار', en: 'test' },
  test_of_prophet: { ar: 'اختبار النبي', en: 'Trial of the Prophet' },
  moral_decision: { ar: 'قرار أخلاقي', en: 'Moral Decision' },
  moral_choice: { ar: 'الاختيار الأخلاقي', en: 'Moral Choice' },
  restraint: { ar: 'ضبط النفس', en: 'restraint' },
  self_control: { ar: 'التحكم بالنفس', en: 'Self-Control' },

  // Service and generosity tags
  tawakkul: { ar: 'التوكل', en: 'tawakkul' },
  generosity: { ar: 'الكرم', en: 'generosity' },
  selfless_service: { ar: 'الخدمة بإخلاص', en: 'Selfless Service' },
  refusing_payment: { ar: 'رفض الأجر', en: 'Refusing Payment' },
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
  vulnerable_people: { ar: 'المستضعفون', en: 'Vulnerable People' },
  yajuj_majuj: { ar: 'يأجوج ومأجوج', en: 'Yajooj and Majooj' },
  corruption: { ar: 'الفساد', en: 'corruption' },
  plea_for_help: { ar: 'طلب النجدة', en: 'Plea For Help' },

  // Eschatology and divine tags
  eschatology: { ar: 'علم الآخرة', en: 'eschatology' },
  impermanence: { ar: 'الزوال', en: 'impermanence' },
  attribution_to_allah: { ar: 'نسب الفضل لله', en: 'Attributing Merit to Allah' },
  divine_promise: { ar: 'الوعد الإلهي', en: 'Divine Promise' },

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
  disobedience_battle: { ar: 'العصيان في المعركة', en: 'Disobedience in Battle' },

  // Hypocrisy and character tags
  hypocrisy: { ar: 'النفاق', en: 'hypocrisy' },
  munafiqun: { ar: 'المنافقون', en: 'munafiqun' },
  betrayal: { ar: 'الخيانة', en: 'betrayal' },
  cowardice: { ar: 'الجبن', en: 'cowardice' },
  treachery: { ar: 'الغدر', en: 'treachery' },
  doubt: { ar: 'الشك', en: 'doubt' },
  sincere_believers: { ar: 'المؤمنين الصادقين', en: 'Sincere Believers' },

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
  idol_worship: { ar: 'عبادة الأصنام', en: 'Idol Worship' },
  breaking_idols: { ar: 'تحطيم الأصنام', en: 'Breaking Idols' },
  forbidden_tree: { ar: 'الشجرة المحرمة', en: 'The Forbidden Tree' },
  khalifah: { ar: 'الخليفة', en: 'khalifah' },
  prostration: { ar: 'السجود', en: 'prostration' },

  // Divine help and intervention
  divine_help: { ar: 'النصر الإلهي', en: 'Divine Help' },
  divine_victory: { ar: 'الفتح الإلهي', en: 'Divine Victory' },

  // Peace and related
  peace: { ar: 'السلام', en: 'peace' },
  forgive: { ar: 'العفو', en: 'forgive' },

  // Story-specific tags
  sleep: { ar: 'النوم', en: 'sleep' },
  persecution: { ar: 'الاضطهاد', en: 'persecution' },
  lesson: { ar: 'العبرة', en: 'lesson' },
  hidden_wisdom: { ar: 'الحكمة الخفية', en: 'Hidden Wisdom' },
  learning: { ar: 'التعلم', en: 'learning' },
  barrier: { ar: 'السد', en: 'barrier' },
  family_test: { ar: 'اختبار الأسرة', en: 'Family Trial' },
  arguing_with_idolaters: { ar: 'محاجة المشركين', en: 'Arguing With Idolaters' },
  miracle_birth: { ar: 'الولادة المعجزة', en: 'Miraculous Birth' },
  table: { ar: 'المائدة', en: 'table' },
  iram: { ar: 'إرم', en: 'iram' },
  rock_dwellings: { ar: 'البيوت الصخرية', en: 'Rock Dwellings' },
  rain_of_stones: { ar: 'مطر الحجارة', en: 'Rain Of Stones' },
  sheba: { ar: 'سبأ', en: 'sheba' },
  sea_parting: { ar: 'شق البحر', en: 'Parting of the Sea' },
  exodus: { ar: 'الخروج', en: 'exodus' },
  tyrant: { ar: 'الطاغية', en: 'tyrant' },
  birds: { ar: 'الطيور', en: 'birds' },
  ants: { ar: 'النمل', en: 'ants' },
  miracle_child: { ar: 'الطفل المعجزة', en: 'Miraculous Child' },
  old_age: { ar: 'الشيخوخة', en: 'Old Age' },
  fahisha: { ar: 'الفاحشة', en: 'fahisha' },
  homosexuality: { ar: 'اللواط', en: 'homosexuality' },
  she_camel: { ar: 'الناقة', en: 'The She-Camel' },
  whale: { ar: 'الحوت', en: 'whale' },
  darkness: { ar: 'الظلمات', en: 'darkness' },
  illness: { ar: 'المرض', en: 'illness' },
  fraud: { ar: 'الغش', en: 'fraud' },
  weights_measures: { ar: 'الكيل والميزان', en: 'Weights and Measures' },
  business: { ar: 'التجارة', en: 'business' },
  crow: { ar: 'الغراب', en: 'crow' },
  regret: { ar: 'الندم', en: 'regret' },
  hundred_years: { ar: 'مئة عام', en: 'Hundred Years' },
  donkey: { ar: 'الحمار', en: 'donkey' },
  kingship: { ar: 'الملوكية', en: 'kingship' },
  river_test: { ar: 'اختبار النهر', en: 'River Test' },
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
  divine_plan: { ar: 'التدبير الإلهي', en: 'Divine Plan' },
  choice: { ar: 'الاختيار', en: 'choice' },
  reinforcement: { ar: 'الإمداد', en: 'reinforcement' },
  tranquility: { ar: 'السكينة', en: 'tranquility' },
  divine_action: { ar: 'الفعل الإلهي', en: 'Divine Action' },
  tyrant_death: { ar: 'مقتل الطاغية', en: 'Death of the Tyrant' },
  furqan: { ar: 'الفرقان', en: 'furqan' },

  // Isra and Miraj tags
  glorification: { ar: 'التسبيح', en: 'glorification' },
  aqsa: { ar: 'الأقصى', en: 'aqsa' },
  holiness: { ar: 'القدسية', en: 'holiness' },
  divine_wisdom: { ar: 'الحكمة الإلهية', en: 'Divine Wisdom' },
  hearing: { ar: 'السمع', en: 'hearing' },
  seeing: { ar: 'البصر', en: 'seeing' },

  // Conquest of Mecca tags
  conquest: { ar: 'الفتح', en: 'conquest' },
  divine_gift: { ar: 'العطاء الإلهي', en: 'Divine Gift' },
  increase: { ar: 'الزيادة', en: 'increase' },
  fulfillment: { ar: 'التحقق', en: 'fulfillment' },
  safety: { ar: 'الأمان', en: 'safety' },
  islam: { ar: 'الإسلام', en: 'islam' },
  truth: { ar: 'الحق', en: 'truth' },

  // Ifk (Slander) tags
  slander: { ar: 'الإفك', en: 'slander' },
  falsehood: { ar: 'الباطل', en: 'falsehood' },
  good_opinion: { ar: 'حسن الظن', en: 'Good Opinion' },
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
  dream_fulfilled: { ar: 'تحقق الرؤيا', en: 'Dream Fulfilled' },
  youth: { ar: 'الشباب', en: 'youth' },
  escape: { ar: 'الهروب', en: 'escape' },
  wonder: { ar: 'العجب', en: 'wonder' },
  discovery: { ar: 'الاكتشاف', en: 'discovery' },
  mashallah: { ar: 'ما شاء الله', en: 'mashallah' },
  denial: { ar: 'الإنكار', en: 'denial' },
  fate: { ar: 'القدر', en: 'fate' },
  orphans: { ar: 'اليتامى', en: 'orphans' },
  wisdom_revealed: { ar: 'الحكمة المكشوفة', en: 'Wisdom Revealed' },
  special_knowledge: { ar: 'العلم اللدني', en: 'Special Knowledge' },
  knowledge_seeking: { ar: 'طلب العلم', en: 'Knowledge Seeking' },
  ship: { ar: 'السفينة', en: 'ship' },
  means: { ar: 'الأسباب', en: 'means' },
  new_beginning: { ar: 'البداية الجديدة', en: 'New Beginning' },
  judi: { ar: 'الجودي', en: 'judi' },
  methods: { ar: 'الأساليب', en: 'methods' },
  persistence: { ar: 'الإصرار', en: 'persistence' },
  finality: { ar: 'النهائية', en: 'finality' },
  preparation: { ar: 'الاستعداد', en: 'preparation' },
  reasoning: { ar: 'الاستدلال', en: 'reasoning' },
  stars: { ar: 'النجوم', en: 'stars' },
  challenge: { ar: 'التحدي', en: 'challenge' },
  proof: { ar: 'الحجة', en: 'proof' },
  blessed_land: { ar: 'الأرض المباركة', en: 'Blessed Land' },
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
  baal_worship: { ar: 'عبادة بعل', en: 'Baal Worship' },
  mission: { ar: 'الرسالة', en: 'mission' },
  sending: { ar: 'الإرسال', en: 'sending' },
  legacy: { ar: 'الإرث', en: 'legacy' },
  bani_israil: { ar: 'بني إسرائيل', en: 'Bani Israil' },

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
  enemy_retreat: { ar: 'انسحاب العدو', en: 'Enemy Retreat' },
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
  destroyed_nations: { ar: 'الأمم الهالكة', en: 'Destroyed Nations' },
  examples: { ar: 'الأمثال', en: 'examples' },
  unknown_identity: { ar: 'هوية مجهولة', en: 'Unknown Identity' },
  yemen: { ar: 'اليمن', en: 'yemen' },
  kings: { ar: 'الملوك', en: 'kings' },
  criminals: { ar: 'المجرمون', en: 'criminals' },
  comparison: { ar: 'المقارنة', en: 'comparison' },
  deniers: { ar: 'المكذبون', en: 'deniers' },

  // 'Abasa (Blind Man) story tags
  correction: { ar: 'العتاب', en: 'correction' },
  blind_man: { ar: 'الأعمى', en: 'Blind Man' },
  purification: { ar: 'التزكية', en: 'purification' },
  benefit: { ar: 'النفع', en: 'benefit' },
  priorities: { ar: 'الأولويات', en: 'priorities' },
  self_sufficient: { ar: 'المستغني', en: 'Self Sufficient' },
  responsibility: { ar: 'المسؤولية', en: 'responsibility' },
  seeker: { ar: 'الساعي', en: 'seeker' },
  fear_of_allah: { ar: 'الخشية', en: 'Fear Of Allah' },
  distracted: { ar: 'التلهي', en: 'distracted' },

  // Bani Nadir expulsion tags
  expulsion: { ar: 'الإجلاء', en: 'expulsion' },
  jews: { ar: 'اليهود', en: 'jews' },
  first_gathering: { ar: 'أول الحشر', en: 'First Gathering' },
  fortresses: { ar: 'الحصون', en: 'fortresses' },
  surprise: { ar: 'المفاجأة', en: 'surprise' },
  divine_decree: { ar: 'القضاء الإلهي', en: 'Divine Decree' },
  terror: { ar: 'الرعب', en: 'terror' },
  lies: { ar: 'الكذب', en: 'lies' },

  // People of Aiyka tags
  aiyka: { ar: 'الأيكة', en: 'aiyka' },
  forest: { ar: 'الغابة', en: 'forest' },
  shadow: { ar: 'الظلة', en: 'shadow' },
  shadow_day: { ar: 'يوم الظلة', en: 'Shadow Day' },
  accusation: { ar: 'الاتهام', en: 'accusation' },

  // New story themes
  elevation: { ar: 'الرفعة', en: 'elevation' },
  building_kaaba: { ar: 'بناء الكعبة', en: 'building the Ka\'bah' },
  preference: { ar: 'التفضيل', en: 'preference' },
  charity: { ar: 'الصدقة', en: 'charity' },
  multiplication: { ar: 'المضاعفة', en: 'multiplication' },
  tyranny: { ar: 'الطغيان', en: 'tyranny' },
  transience: { ar: 'زوال الدنيا', en: 'transience' },
  worldliness: { ar: 'الدنيا', en: 'worldliness' },
  contrast: { ar: 'المقابلة', en: 'contrast' },
  misguidance: { ar: 'الضلال', en: 'misguidance' },
  divine_light: { ar: 'النور الإلهي', en: 'Divine Light' },
  light: { ar: 'النور', en: 'light' },
  divine_attributes: { ar: 'الصفات الإلهية', en: 'Divine Attributes' },
  hereafter: { ar: 'الآخرة', en: 'hereafter' },
  limbo: { ar: 'الأعراف', en: 'the heights' },
  paradise: { ar: 'الجنة', en: 'paradise' },
  eternal_bliss: { ar: 'النعيم الأبدي', en: 'eternal bliss' },
  reward: { ar: 'الثواب', en: 'reward' },
  accountability: { ar: 'المحاسبة', en: 'accountability' },
  enmity: { ar: 'العداوة', en: 'enmity' },
  fitrah: { ar: 'الفطرة', en: 'fitrah' },
  hope: { ar: 'الرجاء', en: 'hope' },
  concealment: { ar: 'الكتمان', en: 'concealment' },
  hidden_knowledge: { ar: 'العلم الخفي', en: 'hidden knowledge' },
  divine_kingdom: { ar: 'الملك الإلهي', en: 'divine kingdom' },
  temptation: { ar: 'الفتنة', en: 'temptation' },
  maternal_love: { ar: 'حنان الأم', en: 'maternal love' },
  identity: { ar: 'الهوية', en: 'identity' },
  divine_command: { ar: 'الأمر الإلهي', en: 'divine command' },
  migration: { ar: 'الهجرة', en: 'migration' },
  trust_in_allah: { ar: 'التوكل على الله', en: 'trust in Allah' },
  divine_aid: { ar: 'المدد الإلهي', en: 'divine aid' },
  mubahala: { ar: 'المباهلة', en: 'mubahala' },
  dialogue: { ar: 'الحوار', en: 'dialogue' },
  prophecy: { ar: 'النبوءة', en: 'prophecy' },
  divine_knowledge: { ar: 'العلم الإلهي', en: 'divine knowledge' },
  preservation: { ar: 'الحفظ', en: 'preservation' },
  ingratitude: { ar: 'الجحود', en: 'ingratitude' },
  blessings: { ar: 'النعم', en: 'blessings' },
  defiance: { ar: 'التحدي', en: 'defiance' },
  'she-camel': { ar: 'الناقة', en: 'she-camel' },
  flood: { ar: 'الطوفان', en: 'flood' },
  sabbath: { ar: 'السبت', en: 'sabbath' },
  magic: { ar: 'السحر', en: 'magic' },
  dream_interpretation: { ar: 'تفسير الأحلام', en: 'dream interpretation' },
  chivalry: { ar: 'المروءة', en: 'chivalry' },
  exile: { ar: 'المنفى', en: 'exile' },
  divine_encounter: { ar: 'اللقاء الإلهي', en: 'divine encounter' },
  companionship: { ar: 'الصحبة', en: 'companionship' },
  divine_care: { ar: 'العناية الإلهية', en: 'divine care' },
  truth_vs_falsehood: { ar: 'الحق والباطل', en: 'truth vs falsehood' },
  subjugation: { ar: 'التسخير', en: 'subjugation' },
  debate: { ar: 'المناظرة', en: 'debate' },
  unseen_knowledge: { ar: 'علم الغيب', en: 'unseen knowledge' },
  divine_admonition: { ar: 'العتاب الإلهي', en: 'divine admonition' },
  equality: { ar: 'المساواة', en: 'equality' },
  certainty: { ar: 'اليقين', en: 'certainty' },
  loyalty: { ar: 'الوفاء', en: 'loyalty' },
  "da'wah": { ar: 'الدعوة', en: "da'wah" },
  grief: { ar: 'الحزن', en: 'grief' },
  trials: { ar: 'الابتلاءات', en: 'trials' },
  anger: { ar: 'الغضب', en: 'anger' },
  disbelief: { ar: 'الكفر', en: 'disbelief' },

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

  // New story figures
  "Fir'awn": { ar: 'فرعون', en: 'Pharaoh' },
  Haman: { ar: 'هامان', en: 'Haman' },
  Samiri: { ar: 'السامري', en: 'As-Samiri' },
  Khidr: { ar: 'الخضر', en: 'Al-Khidr' },
  Bilqis: { ar: 'بلقيس', en: 'Bilqis' },
  Jibril: { ar: 'جبريل', en: 'Jibril' },
  Israfil: { ar: 'إسرافيل', en: 'Israfil' },
  Nimrod: { ar: 'النمرود', en: 'Nimrod' },
  Harut: { ar: 'هاروت', en: 'Harut' },
  Marut: { ar: 'ماروت', en: 'Marut' },
  "Ya'qub": { ar: 'يعقوب', en: "Ya'qub" },
  'Mother of Musa': { ar: 'أم موسى', en: 'Mother of Musa' },
  "Believer of Fir'awn": { ar: 'مؤمن آل فرعون', en: "Believer of Pharaoh's Family" },
  "Bal'am ibn Ba'ura": { ar: 'بلعام بن باعوراء', en: "Bal'am ibn Ba'ura" },
  "Imran's wife": { ar: 'امرأة عمران', en: "Wife of Imran" },
};

// Segment aspect/type translations
export const aspectTranslations: Record<string, { ar: string; en: string }> = {
  // Adam story aspects
  creation: { ar: 'الخلق', en: 'creation' },
  knowledge: { ar: 'العلم', en: 'knowledge' },
  iblis_refusal: { ar: 'رفض إبليس', en: 'Iblis Refusal' },
  iblis_dialogue: { ar: 'حوار إبليس', en: 'Iblis Dialogue' },
  iblis_arrogance: { ar: 'كبر إبليس', en: 'Iblis Arrogance' },
  test_in_paradise: { ar: 'الاختبار في الجنة', en: 'Test In Paradise' },
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
  given_wisdom: { ar: 'الحكمة المعطاة', en: 'Given Wisdom' },
  avoid_shirk: { ar: 'اجتناب الشرك', en: 'Avoid Shirk' },
  parents: { ar: 'الوالدين', en: 'parents' },
  accountability: { ar: 'المحاسبة', en: 'accountability' },
  prayer_character: { ar: 'الصلاة والأخلاق', en: 'Prayer Character' },
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
  advice_given: { ar: 'النصيحة المقدمة', en: 'Advice Given' },
  angel_visit: { ar: 'زيارة الملاك', en: 'Angel Visit' },
  angels_visit: { ar: 'زيارة الملائكة', en: 'Angels Visit' },
  answer: { ar: 'الإجابة', en: 'answer' },
  ant_valley: { ar: 'وادي النمل', en: 'Ant Valley' },
  arrogant_response: { ar: 'الرد المتكبر', en: 'Arrogant Response' },
  awakening: { ar: 'الاستيقاظ', en: 'awakening' },
  becomes_minister: { ar: 'يصبح وزيرًا', en: 'Becomes Minister' },
  believers_saved: { ar: 'نجاة المؤمنين', en: 'Believers Saved' },
  birth_and_rescue: { ar: 'الولادة والإنقاذ', en: 'Birth And Rescue' },
  birth_narrative: { ar: 'قصة الولادة', en: 'Birth Narrative' },
  breaking_idols: { ar: 'تحطيم الأصنام', en: 'Breaking Idols' },
  brothers_return: { ar: 'عودة الإخوة', en: 'Brothers Return' },
  building_ark: { ar: 'بناء السفينة', en: 'Building Ark' },
  building_barrier: { ar: 'بناء السد', en: 'Building Barrier' },
  building_kaaba: { ar: 'بناء الكعبة', en: 'Building Kaaba' },
  burial: { ar: 'الدفن', en: 'burial' },
  calling_father: { ar: 'دعوة الأب', en: 'Calling Father' },
  calling_to_hajj: { ar: 'الدعوة للحج', en: 'Calling To Hajj' },
  calling_to_lord: { ar: 'الدعاء إلى الله', en: 'Calling To Lord' },
  camel_killed: { ar: 'قتل الناقة', en: 'Camel Killed' },
  childhood_dream: { ar: 'رؤيا الطفولة', en: 'Childhood Dream' },
  chosen_purified: { ar: 'الاصطفاء والتطهير', en: 'Chosen Purified' },
  complete_story: { ar: 'القصة الكاملة', en: 'Complete Story' },
  confronting_firawn: { ar: 'مواجهة فرعون', en: 'Confronting Firawn' },
  crossing_sea: { ar: 'عبور البحر', en: 'Crossing Sea' },
  dawah: { ar: 'الدعوة', en: 'dawah' },
  departure: { ar: 'المغادرة', en: 'departure' },
  divine_gifts: { ar: 'الهبات الإلهية', en: 'Divine Gifts' },
  faith: { ar: 'الإيمان', en: 'faith' },
  given_kingdom: { ar: 'إعطاء الملك', en: 'Given Kingdom' },
  given_wealth: { ar: 'إعطاء المال', en: 'Given Wealth' },
  giving_birth: { ar: 'الولادة', en: 'Giving Birth' },
  golden_calf: { ar: 'العجل الذهبي', en: 'The Golden Calf' },
  habil_response: { ar: 'رد هابيل', en: 'Habil Response' },
  hoopoe_news: { ar: 'خبر الهدهد', en: 'Hoopoe News' },
  humility: { ar: 'التواضع', en: 'humility' },
  introduction: { ar: 'المقدمة', en: 'introduction' },
  iron_gift: { ar: 'تليين الحديد', en: 'Iron Gift' },
  journey_east: { ar: 'الرحلة شرقًا', en: 'Journey East' },
  journey_west: { ar: 'الرحلة غربًا', en: 'Journey West' },
  journey_with_khidr: { ar: 'الرحلة مع الخضر', en: 'Journey With Khidr' },
  landing: { ar: 'الرسو', en: 'landing' },
  lessons: { ar: 'الدروس', en: 'lessons' },
  magicians_convert: { ar: 'إسلام السحرة', en: 'Magicians Convert' },
  miraculous_birth: { ar: 'الولادة المعجزة', en: 'Miraculous Birth' },
  mother_vow: { ar: 'نذر الأم', en: 'Mother Vow' },
  mount_sinai: { ar: 'جبل الطور', en: 'Mount Sinai' },
  mountains_praise: { ar: 'تسبيح الجبال', en: 'Mountains Praise' },
  murder: { ar: 'القتل', en: 'murder' },
  not_crucified: { ar: 'لم يُصلب', en: 'Not Crucified' },
  offerings: { ar: 'القرابين', en: 'offerings' },
  passing_by: { ar: 'المرور', en: 'Passing By' },
  people_believe: { ar: 'إيمان القوم', en: 'People Believe' },
  praised: { ar: 'الثناء', en: 'praised' },
  queen_of_sheba: { ar: 'ملكة سبأ', en: 'Queen Of Sheba' },
  questions: { ar: 'الأسئلة', en: 'questions' },
  receiving_prophethood: { ar: 'تلقي النبوة', en: 'Receiving Prophethood' },
  rejected: { ar: 'الرفض', en: 'rejected' },
  reluctant_obedience: { ar: 'الطاعة المترددة', en: 'Reluctant Obedience' },
  rescued: { ar: 'الإنقاذ', en: 'rescued' },
  returning_to_people: { ar: 'العودة للقوم', en: 'Returning To People' },
  sacrifice_test: { ar: 'اختبار الذبح', en: 'Sacrifice Test' },
  secret_prayer: { ar: 'الدعاء السري', en: 'Secret Prayer' },
  seeking_truth: { ar: 'البحث عن الحق', en: 'Seeking Truth' },
  she_camel: { ar: 'الناقة', en: 'The She-Camel' },
  showing_off: { ar: 'التفاخر', en: 'Showing Off' },
  signs: { ar: 'الآيات', en: 'signs' },
  sleep: { ar: 'النوم', en: 'sleep' },
  sold_to_egypt: { ar: 'البيع إلى مصر', en: 'Sold To Egypt' },
  son_drowns: { ar: 'غرق الابن', en: 'Son Drowns' },
  speaking_in_cradle: { ar: 'الكلام في المهد', en: 'Speaking In Cradle' },
  swallowed: { ar: 'الابتلاع', en: 'swallowed' },
  table_from_heaven: { ar: 'المائدة من السماء', en: 'Table From Heaven' },
  teaching_tawhid: { ar: 'تعليم التوحيد', en: 'Teaching Tawhid' },
  the_test: { ar: 'الاختبار', en: 'The Test' },
  threat: { ar: 'التهديد', en: 'threat' },
  three_groups: { ar: 'الفرق الثلاث', en: 'Three Groups' },
  throne_test: { ar: 'اختبار العرش', en: 'Throne Test' },
  transformation: { ar: 'التحول', en: 'transformation' },
  transgression: { ar: 'العدوان', en: 'transgression' },
  upbringing: { ar: 'التنشئة', en: 'upbringing' },
  warning_people: { ar: 'تحذير القوم', en: 'Warning People' },
  wife_left_behind: { ar: 'ترك الزوجة', en: 'Wife Left Behind' },
  with_talut: { ar: 'مع طالوت', en: 'With Talut' },
  yahya_qualities: { ar: 'صفات يحيى', en: 'Qualities of Yahya' },
  youth_and_exile: { ar: 'الشباب والنفي', en: 'Youth And Exile' },
  test_of_chastity: { ar: 'اختبار العفة', en: 'Test of Chastity' },
  // Uhud/Munafiqun story tags
  strategy: { ar: 'الإستراتيجية', en: 'strategy' },
  exposure: { ar: 'الانكشاف', en: 'exposure' },
  superiority: { ar: 'التفوق', en: 'superiority' },
  mortality: { ar: 'الفناء', en: 'mortality' },
  consultation: { ar: 'المشاورة', en: 'consultation' },
  joy: { ar: 'الفرح', en: 'joy' },
  messenger: { ar: 'الرسول', en: 'messenger' },
  divine_help: { ar: 'العون الإلهي', en: 'Divine Help' },
  greed: { ar: 'الطمع', en: 'greed' },
  encouragement: { ar: 'التشجيع', en: 'encouragement' },
  afterlife: { ar: 'الآخرة', en: 'afterlife' },
  honor: { ar: 'الشرف', en: 'honor' },
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
