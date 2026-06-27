import { Link } from 'react-router-dom';
import {
  Book,
  MessageCircle,
  Network,
  ArrowRight,
  BookOpenCheck,
  Search,
  Link2,
  Compass,
  Sparkles,
  Map,
  Mic,
  BookOpen,
  Wrench,
  ShieldCheck,
  Star,
  Users,
  Layers,
  Heart,
  Bookmark,
  Flame,
  CalendarCheck,
  HandHeart,
  Smile,
  BarChart2,
  PenLine,
  Baby,
  Wind,
  AlarmClock,
  BookCopy,
  GraduationCap,
  Trophy,
  GitCompare,
  FlipHorizontal2,
  Sigma,
  Scroll,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import clsx from 'clsx';
import { VerseOfDayCard } from '../components/home/VerseOfDayCard';
import { ReadingProgressCard } from '../components/home/ReadingProgressCard';
import { WordOfDayCard } from '../components/home/WordOfDayCard';
import { usePersonaStore } from '../stores/personaStore';

// ---------------------------------------------------------------------------
// Feature sections
// ---------------------------------------------------------------------------

interface Feature {
  icon: React.ElementType;
  titleAr: string;
  titleEn: string;
  descAr: string;
  descEn: string;
  link: string;
  color: string;
  iconBg: string;
}

const CORE_FEATURES: Feature[] = [
  {
    icon: BookOpenCheck,
    titleAr: 'المصحف الشريف',
    titleEn: 'Mushaf',
    descAr: 'تصفح القرآن الكريم آية بآية مع التحليل النحوي والصرفي والتشابه بين الآيات',
    descEn: 'Browse the Quran verse by verse with grammar analysis, tafsir, and verse similarity',
    link: '/mushaf',
    color: 'text-emerald-700',
    iconBg: 'bg-emerald-100',
  },
  {
    icon: MessageCircle,
    titleAr: 'مساعد التدبر',
    titleEn: 'Tafsir Assistant',
    descAr: 'احصل على إجابات مستندة إلى التفاسير الموثقة — ابن كثير وغيره',
    descEn: 'Get answers grounded in authenticated tafsir sources — Ibn Kathir and others',
    link: '/ask',
    color: 'text-blue-700',
    iconBg: 'bg-blue-100',
  },
  {
    icon: Search,
    titleAr: 'البحث في القرآن',
    titleEn: 'Quran Search',
    descAr: 'بحث دلالي ونحوي متقدم في نصوص القرآن والتفاسير',
    descEn: 'Advanced semantic and grammatical search across Quran text and tafsir',
    link: '/search',
    color: 'text-violet-700',
    iconBg: 'bg-violet-100',
  },
];

const KNOWLEDGE_FEATURES: Feature[] = [
  {
    icon: Book,
    titleAr: 'قصص القرآن',
    titleEn: 'Quran Stories',
    descAr: 'استكشف قصص القرآن الكريم وترابطها عبر السور',
    descEn: 'Explore Quranic stories and their connections across surahs',
    link: '/stories',
    color: 'text-amber-700',
    iconBg: 'bg-amber-100',
  },
  {
    icon: Map,
    titleAr: 'أطلس القصص',
    titleEn: 'Story Atlas',
    descAr: 'خرائط سردية تربط الأحداث والشخصيات والأزمنة القرآنية',
    descEn: 'Narrative maps connecting Quranic events, figures, and eras',
    link: '/story-atlas',
    color: 'text-teal-700',
    iconBg: 'bg-teal-100',
  },
  {
    icon: Network,
    titleAr: 'المفاهيم القرآنية',
    titleEn: 'Quranic Concepts',
    descAr: 'استعرض الأشخاص والأماكن والأحداث القرآنية بصلاتها المتبادلة',
    descEn: 'Browse Quranic persons, places and events with their cross-connections',
    link: '/concepts',
    color: 'text-indigo-700',
    iconBg: 'bg-indigo-100',
  },
  {
    icon: Compass,
    titleAr: 'محاور القرآن',
    titleEn: 'Quranic Themes',
    descAr: 'تصنيف هرمي للمحاور القرآنية مستند إلى المنهج السني',
    descEn: 'Hierarchical taxonomy of Quranic themes grounded in Sunni methodology',
    link: '/themes',
    color: 'text-cyan-700',
    iconBg: 'bg-cyan-100',
  },
  {
    icon: Sparkles,
    titleAr: 'الآيات والمعجزات',
    titleEn: 'Signs & Miracles',
    descAr: 'الآيات والمعجزات المذكورة في القرآن — من معجزات الأنبياء إلى الآيات الكونية',
    descEn: 'Signs and miracles explicitly mentioned in the Quran — prophetic and cosmic',
    link: '/miracles',
    color: 'text-orange-700',
    iconBg: 'bg-orange-100',
  },
  {
    icon: Link2,
    titleAr: 'صلة الآيات',
    titleEn: 'Verse Similarity',
    descAr: 'اكتشف التشابه الدلالي والموضوعي بين آيات القرآن الكريم',
    descEn: 'Discover semantic and thematic similarities between Quranic verses',
    link: '/similarity',
    color: 'text-rose-700',
    iconBg: 'bg-rose-100',
  },
  {
    icon: Star,
    titleAr: 'أسماء الله الحسنى',
    titleEn: '99 Names of Allah',
    descAr: 'تصفح أسماء الله الحسنى مع المعاني والشواهد القرآنية والتلاوة الصوتية',
    descEn: 'Explore the 99 Names of Allah with meanings, Quranic references, and audio recitation',
    link: '/asma-allah',
    color: 'text-yellow-700',
    iconBg: 'bg-yellow-100',
  },
  {
    icon: Users,
    titleAr: 'أطلس الأنبياء',
    titleEn: 'Prophets Atlas',
    descAr: 'تتبع رحلات الأنبياء ومسيرتهم في القرآن الكريم مع الشواهد القرآنية',
    descEn: "Trace the journeys and life stages of Quranic prophets with verified references",
    link: '/prophets',
    color: 'text-green-700',
    iconBg: 'bg-green-100',
  },
  {
    icon: Layers,
    titleAr: 'أطلس السور',
    titleEn: 'Surah Atlas',
    descAr: 'خرائط تفصيلية لكل سورة تربطها بالقصص والأنبياء والمواضيع القرآنية',
    descEn: 'Detailed maps for each surah connecting stories, prophets, and Quranic themes',
    link: '/surah-atlas',
    color: 'text-purple-700',
    iconBg: 'bg-purple-100',
  },
  {
    icon: Scroll,
    titleAr: 'أسباب النزول',
    titleEn: 'Occasions of Revelation',
    descAr: 'تعرّف على سياق نزول الآيات القرآنية — من كتاب الواحدي (ت 468 هـ)',
    descEn: 'Discover the historical context of each verse — from al-Wahidi\'s classical Asbab al-Nuzul',
    link: '/asbab',
    color: 'text-amber-700',
    iconBg: 'bg-amber-100',
  },
];

const TOOLS_FEATURES: Feature[] = [
  {
    icon: Mic,
    titleAr: 'تسميع القرآن',
    titleEn: 'Memorization (Tasmeeʿ)',
    descAr: 'راجع حفظك بالتسميع مع التصحيح الفوري بالذكاء الاصطناعي',
    descEn: 'Test your memorization with AI-powered real-time correction',
    link: '/tasmee',
    color: 'text-pink-700',
    iconBg: 'bg-pink-100',
  },
  {
    icon: Wrench,
    titleAr: 'الأدوات الإسلامية',
    titleEn: 'Islamic Tools',
    descAr: 'مواقيت الصلاة، التقويم الهجري، حاسبة الزكاة، اتجاه القبلة والمزيد',
    descEn: 'Prayer times, Hijri calendar, Zakat calculator, Qibla direction and more',
    link: '/tools',
    color: 'text-gray-700',
    iconBg: 'bg-gray-100',
  },
  {
    icon: BookOpen,
    titleAr: 'المصادر والمراجع',
    titleEn: 'Sources Registry',
    descAr: 'مرجع كامل لجميع المصادر المستخدمة في المنصة مع تقييم الموثوقية',
    descEn: 'Complete registry of all sources used on the platform with reliability ratings',
    link: '/sources',
    color: 'text-slate-700',
    iconBg: 'bg-slate-100',
  },
  {
    icon: ShieldCheck,
    titleAr: 'دليل الأسئلة الآمنة',
    titleEn: 'Safe AI Prompting Guide',
    descAr: 'تعلّم كيف تسأل أسئلة قرآنية دقيقة ومستندة على هذه المنصة',
    descEn: 'Learn how to ask precise, source-backed Quranic questions on this platform',
    link: '/tools/prompt-guide',
    color: 'text-emerald-700',
    iconBg: 'bg-emerald-100',
  },
  {
    icon: Heart,
    titleAr: 'التوجيه الروحي',
    titleEn: 'Spiritual Guidance',
    descAr: 'توجيه روحي قرآني لدعم الصحة النفسية والوجدانية — مستند إلى التفسير',
    descEn: 'Quran-grounded spiritual guidance for emotional and mental wellbeing',
    link: '/therapy',
    color: 'text-rose-700',
    iconBg: 'bg-rose-100',
  },
  {
    icon: Bookmark,
    titleAr: 'الآيات المحفوظة',
    titleEn: 'Saved Verses',
    descAr: 'الوصول السريع إلى الآيات التي حفظتها من المصحف والبحث',
    descEn: 'Quick access to verses you have bookmarked from the Mushaf and search',
    link: '/bookmarks',
    color: 'text-amber-700',
    iconBg: 'bg-amber-100',
  },
  {
    icon: Flame,
    titleAr: 'تحدي اليوم',
    titleEn: 'Daily Challenge',
    descAr: 'سؤال يومي من قصص القرآن — اختبر معلوماتك وتابع سلسلتك',
    descEn: 'One Quranic question per day — test your knowledge and track your streak',
    link: '/challenge',
    color: 'text-orange-700',
    iconBg: 'bg-orange-100',
  },
  {
    icon: CalendarCheck,
    titleAr: 'خطة الختمة',
    titleEn: 'Khatmah Reading Plan',
    descAr: 'تتبع تقدمك في قراءة القرآن وحدد هدفاً لإكمال الختمة',
    descEn: 'Track your Quran reading progress and set a target date to complete Khatmah',
    link: '/reading-plan',
    color: 'text-violet-700',
    iconBg: 'bg-violet-100',
  },
  {
    icon: HandHeart,
    titleAr: 'أدعية القرآن',
    titleEn: 'Quranic Duʿā',
    descAr: 'أدعية الأنبياء والمؤمنين من القرآن الكريم — مع التشكيل والمعنى والسياق',
    descEn: "Supplications from the Quran — prophets' prayers, daily duʿā, with transliteration and meaning",
    link: '/duas',
    color: 'text-teal-700',
    iconBg: 'bg-teal-100',
  },
  {
    icon: Smile,
    titleAr: 'الإرشاد العاطفي',
    titleEn: 'Emotional Guidance',
    descAr: 'ما يقوله القرآن حين تشعر بالقلق أو الحزن أو الأمل — توجيه بلا تفسيرات مولّدة',
    descEn: 'What the Quran says when you feel anxious, sad, or hopeful — no AI-generated rulings',
    link: '/guidance',
    color: 'text-pink-700',
    iconBg: 'bg-pink-100',
  },
  {
    icon: BarChart2,
    titleAr: 'إحصائيات القراءة',
    titleEn: 'Reading Stats',
    descAr: 'لوحة تحليلية لقراءتك — خريطة السور والأجزاء ومؤشرات الختمة',
    descEn: 'Personal dashboard — surah coverage map, juz progress, and streak visualization',
    link: '/stats',
    color: 'text-violet-700',
    iconBg: 'bg-violet-100',
  },
  {
    icon: PenLine,
    titleAr: 'مذكرة التأمل',
    titleEn: 'Reflection Journal',
    descAr: 'دوّن تأملاتك وملاحظاتك على الآيات القرآنية — محلياً وخاصاً تماماً',
    descEn: 'Write private notes on Quranic verses — local storage only, never uploaded',
    link: '/journal',
    color: 'text-indigo-700',
    iconBg: 'bg-indigo-100',
  },
  {
    icon: Baby,
    titleAr: 'أسماء من القرآن',
    titleEn: 'Quranic Names',
    descAr: '60+ اسماً قرآنياً مع المعاني والجذور والمراجع — للذكر والأنثى',
    descEn: '60+ names from the Quran with meanings, roots, and references',
    link: '/names',
    color: 'text-amber-700',
    iconBg: 'bg-amber-100',
  },
  {
    icon: Wind,
    titleAr: 'التسبيح اليومي',
    titleEn: 'Daily Dhikr',
    descAr: 'عداد التسبيح اليومي مع الشواهد القرآنية والتوضيح — يُعاد يومياً',
    descEn: 'Tally counter for daily remembrance with Quranic references — auto-resets daily',
    link: '/dhikr',
    color: 'text-emerald-700',
    iconBg: 'bg-emerald-100',
  },
  {
    icon: AlarmClock,
    titleAr: 'ترتيب النزول',
    titleEn: 'Revelation Timeline',
    descAr: 'السور بترتيبها الزمني للنزول مع السياق التاريخي والحقبة',
    descEn: 'Surahs in chronological revelation order with historical context and period',
    link: '/timeline',
    color: 'text-rose-700',
    iconBg: 'bg-rose-100',
  },
  {
    icon: BookCopy,
    titleAr: 'مستكشف الأجزاء',
    titleEn: 'Juz Navigator',
    descAr: 'تصفح الأجزاء الثلاثين مع المواضيع والآية المميزة وتقدم القراءة',
    descEn: 'Browse all 30 juz with themes, featured verses, and reading progress overlay',
    link: '/juz',
    color: 'text-teal-700',
    iconBg: 'bg-teal-100',
  },
  {
    icon: GraduationCap,
    titleAr: 'مسار التعلم',
    titleEn: 'Learning Path',
    descAr: 'مسار تعليمي شخصي حسب وضعك — مسلم جديد، طالب، باحث، حافظ…',
    descEn: 'Personalized curriculum based on your persona — new Muslim, student, researcher, memorizer…',
    link: '/learn',
    color: 'text-purple-700',
    iconBg: 'bg-purple-100',
  },
  {
    icon: Trophy,
    titleAr: 'اختبار قرآني + ذكاء اصطناعي',
    titleEn: 'Quranic Quiz + AI',
    descAr: '44 سؤالاً موثقاً في 6 فئات + توليد أسئلة بالذكاء الاصطناعي لكل سورة — مستند إلى التفسير',
    descEn: '44 verified questions across 6 categories + AI-generated MCQs for any surah — grounded in tafsir',
    link: '/quiz',
    color: 'text-violet-700',
    iconBg: 'bg-violet-100',
  },
  {
    icon: Sparkles,
    titleAr: 'عجائب القرآن',
    titleEn: 'Quran Wonders',
    descAr: '20+ حقيقة موثقة عن القرآن — الأعداد والبنية والتاريخ والحفاظ',
    descEn: '20+ verified facts about the Quran — numbers, structure, history, and preservation',
    link: '/wonders',
    color: 'text-amber-700',
    iconBg: 'bg-amber-100',
  },
  {
    icon: GitCompare,
    titleAr: 'مقارنة السور',
    titleEn: 'Surah Comparison',
    descAr: 'قارن بين أي سورتين جنباً إلى جنب — الآيات والترتيب والحقب والمفاهيم',
    descEn: 'Compare any two surahs — verses, revelation order, period, and key concepts',
    link: '/compare',
    color: 'text-violet-700',
    iconBg: 'bg-violet-100',
  },
  {
    icon: FlipHorizontal2,
    titleAr: 'بطاقات الحفظ',
    titleEn: 'Memorization Flashcards',
    descAr: 'ممارسة الاسترجاع النشط للآيات — تقدمك محفوظ محلياً لكل سورة',
    descEn: 'Practice active recall verse-by-verse — progress tracked locally per surah',
    link: '/flashcards',
    color: 'text-emerald-700',
    iconBg: 'bg-emerald-100',
  },
  {
    icon: Sigma,
    titleAr: 'الجذور القرآنية',
    titleEn: 'Quranic Roots',
    descAr: '10 جذور ثلاثية أساسية مع عائلاتها الاشتقاقية ومعانيها الكلاسيكية',
    descEn: '10 core trilateral roots with their word families and classical meanings',
    link: '/roots',
    color: 'text-blue-700',
    iconBg: 'bg-blue-100',
  },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function HomePage() {
  const { language } = useLanguageStore();
  const { persona } = usePersonaStore();
  const isRtl = language === 'ar';

  return (
    <div className="min-h-[calc(100vh-4rem)]" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-600 to-primary-800 text-white py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className={clsx('text-4xl md:text-5xl font-bold mb-4', isRtl && 'font-arabic')}>
            {t('app_title', language)}
          </h1>
          <p className={clsx('text-xl md:text-2xl text-primary-100 mb-8 max-w-3xl mx-auto', isRtl && 'font-arabic')}>
            {t('app_subtitle', language)}
          </p>
          <div className={clsx('flex flex-col sm:flex-row gap-4 justify-center', isRtl && 'sm:flex-row-reverse')}>
            <Link
              to="/mushaf"
              className={clsx('btn-primary bg-white text-primary-700 hover:bg-primary-50 px-8 py-3 text-lg inline-flex items-center gap-2', isRtl && 'font-arabic')}
            >
              {t('nav_mushaf', language)}
              <ArrowRight className={clsx('w-5 h-5', isRtl && 'rotate-180')} />
            </Link>
            <Link
              to="/ask"
              className={clsx('btn-secondary border-2 border-white text-white hover:bg-white/10 px-8 py-3 text-lg', isRtl && 'font-arabic')}
            >
              {t('nav_ask', language)}
            </Link>
          </div>
        </div>
      </section>

      {/* Daily Widgets: Verse of the Day + Reading Progress */}
      <section className="py-8 bg-gray-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Daily challenge shortcut — visible only when persona is set */}
          {persona && (
            <div className={clsx('flex items-center mb-4', isRtl ? 'justify-start' : 'justify-end')}>
              <Link to="/challenge" className="flex items-center gap-1.5 text-sm text-orange-600 hover:text-orange-800 font-medium transition-colors">
                <Flame className="w-4 h-4" />
                {isRtl ? 'تحدي اليوم' : "Today's Challenge"}
              </Link>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            <VerseOfDayCard />
            <ReadingProgressCard />
            <WordOfDayCard />
          </div>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-12 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader
            titleAr="المميزات الرئيسية"
            titleEn="Core Features"
            isRtl={isRtl}
          />
          <div className="grid md:grid-cols-3 gap-6">
            {CORE_FEATURES.map((f) => (
              <FeatureCard key={f.link} feature={f} language={language} isRtl={isRtl} large />
            ))}
          </div>
        </div>
      </section>

      {/* Knowledge Features */}
      <section className="py-12 bg-gray-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader
            titleAr="المعرفة القرآنية"
            titleEn="Quranic Knowledge"
            isRtl={isRtl}
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {KNOWLEDGE_FEATURES.map((f) => (
              <FeatureCard key={f.link} feature={f} language={language} isRtl={isRtl} />
            ))}
          </div>
        </div>
      </section>

      {/* Tools */}
      <section className="py-12 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader
            titleAr="الأدوات والموارد"
            titleEn="Tools & Resources"
            isRtl={isRtl}
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {TOOLS_FEATURES.map((f) => (
              <FeatureCard key={f.link} feature={f} language={language} isRtl={isRtl} />
            ))}
          </div>
        </div>
      </section>

      {/* Safety Notice */}
      <section className="py-10 bg-amber-50 border-t border-amber-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className={clsx('text-base font-semibold text-amber-800 mb-2', isRtl && 'font-arabic')}>
            {isRtl ? 'ملاحظة مهمة' : 'Important Notice'}
          </h2>
          <p className={clsx('text-amber-700 text-sm leading-relaxed max-w-2xl mx-auto', isRtl && 'font-arabic')}>
            {isRtl
              ? 'جميع الإجابات في هذه المنصة مستندة إلى مصادر تفسيرية موثقة. لا يقوم النظام بتوليد تفسيرات من تلقاء نفسه — كل شرح مقرون بمصدره.'
              : 'All answers on this platform are grounded in authenticated tafsir sources. The system never generates interpretations on its own — every explanation is tied to its source.'}
          </p>
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section header
// ---------------------------------------------------------------------------

function SectionHeader({
  titleAr,
  titleEn,
  isRtl,
}: {
  titleAr: string;
  titleEn: string;
  isRtl: boolean;
}) {
  return (
    <h2 className={clsx(
      'text-xl font-bold text-gray-800 mb-6',
      isRtl ? 'text-right font-arabic' : ''
    )}>
      {isRtl ? titleAr : titleEn}
    </h2>
  );
}

// ---------------------------------------------------------------------------
// Feature card
// ---------------------------------------------------------------------------

function FeatureCard({
  feature,
  isRtl,
  large = false,
}: {
  feature: Feature;
  language: 'ar' | 'en';
  isRtl: boolean;
  large?: boolean;
}) {
  const Icon = feature.icon;
  const title = isRtl ? feature.titleAr : feature.titleEn;
  const desc = isRtl ? feature.descAr : feature.descEn;

  return (
    <Link
      to={feature.link}
      className={clsx(
        'card border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group',
        large && 'p-6'
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      <div className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
        <div className={clsx('p-2.5 rounded-lg shrink-0 group-hover:scale-110 transition-transform', feature.iconBg)}>
          <Icon className={clsx(large ? 'w-6 h-6' : 'w-5 h-5', feature.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={clsx(
            'font-semibold text-gray-900 group-hover:text-primary-600 transition-colors mb-1',
            large ? 'text-lg' : 'text-base',
            isRtl && 'font-arabic text-right'
          )}>
            {title}
          </h3>
          <p className={clsx('text-sm text-gray-500 leading-relaxed', isRtl && 'font-arabic text-right')}>
            {desc}
          </p>
        </div>
      </div>
    </Link>
  );
}
