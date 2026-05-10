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
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import clsx from 'clsx';

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
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function HomePage() {
  const { language } = useLanguageStore();
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
              className="btn-primary bg-white text-primary-700 hover:bg-primary-50 px-8 py-3 text-lg inline-flex items-center gap-2"
            >
              {t('nav_mushaf', language)}
              <ArrowRight className={clsx('w-5 h-5', isRtl && 'rotate-180')} />
            </Link>
            <Link
              to="/ask"
              className="btn-secondary border-2 border-white text-white hover:bg-white/10 px-8 py-3 text-lg"
            >
              {t('nav_ask', language)}
            </Link>
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
