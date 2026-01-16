import { Link } from 'react-router-dom';
import { Video, Newspaper, Globe, BookOpen, Map, Plane, DollarSign, Clock, Calendar } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import clsx from 'clsx';

interface ToolModule {
  id: string;
  name_en: string;
  name_ar: string;
  description_en: string;
  description_ar: string;
  icon: React.ElementType;
  path: string;
  color: string;
}

const TOOL_MODULES: ToolModule[] = [
  {
    id: 'prayer-times',
    name_en: 'Prayer Times',
    name_ar: 'مواقيت الصلاة',
    description_en: 'Accurate prayer times based on your location with Qibla direction and multiple calculation methods',
    description_ar: 'مواقيت صلاة دقيقة حسب موقعك مع اتجاه القبلة وطرق حساب متعددة',
    icon: Clock,
    path: '/tools/prayer-times',
    color: 'green',
  },
  {
    id: 'calendar',
    name_en: 'Hijri Calendar',
    name_ar: 'التقويم الهجري',
    description_en: 'Islamic Hijri calendar with date converter and Islamic holidays',
    description_ar: 'التقويم الإسلامي الهجري مع محول التواريخ والمناسبات الإسلامية',
    icon: Calendar,
    path: '/tools/calendar',
    color: 'cyan',
  },
  {
    id: 'finance',
    name_en: 'Zakat Calculator',
    name_ar: 'حاسبة الزكاة',
    description_en: 'Calculate your Zakat with live gold/silver prices and comprehensive asset categories',
    description_ar: 'احسب زكاتك بأسعار الذهب والفضة الحية وفئات الأصول الشاملة',
    icon: DollarSign,
    path: '/tools/finance',
    color: 'emerald',
  },
  {
    id: 'maps',
    name_en: 'Mosque Finder',
    name_ar: 'البحث عن المساجد',
    description_en: 'Find mosques, halal restaurants, and Islamic centers near you with Qibla direction',
    description_ar: 'ابحث عن المساجد والمطاعم الحلال والمراكز الإسلامية مع اتجاه القبلة',
    icon: Map,
    path: '/tools/maps',
    color: 'teal',
  },
  {
    id: 'videos',
    name_en: 'Islamic Videos',
    name_ar: 'الفيديوهات الإسلامية',
    description_en: 'Educational videos and lectures from trusted Islamic scholars and institutions',
    description_ar: 'فيديوهات ومحاضرات تعليمية من علماء ومؤسسات إسلامية موثقة',
    icon: Video,
    path: '/tools/videos',
    color: 'red',
  },
  {
    id: 'news',
    name_en: 'Islamic News',
    name_ar: 'الأخبار الإسلامية',
    description_en: 'Curated news from trusted Islamic sources and Muslim communities worldwide',
    description_ar: 'أخبار منتقاة من مصادر إسلامية موثقة ومجتمعات مسلمة حول العالم',
    icon: Newspaper,
    path: '/tools/news',
    color: 'blue',
  },
  {
    id: 'books',
    name_en: 'Islamic Books',
    name_ar: 'الكتب الإسلامية',
    description_en: 'Access Islamic books, manuscripts, and scholarly publications from the Internet Archive',
    description_ar: 'الوصول إلى الكتب الإسلامية والمخطوطات والمنشورات العلمية',
    icon: BookOpen,
    path: '/tools/books',
    color: 'amber',
  },
  {
    id: 'trips',
    name_en: 'Hajj & Umrah Guide',
    name_ar: 'دليل الحج والعمرة',
    description_en: 'Complete guide to Hajj and Umrah rituals with step-by-step instructions and duas',
    description_ar: 'دليل شامل لمناسك الحج والعمرة مع التعليمات والأدعية خطوة بخطوة',
    icon: Plane,
    path: '/tools/trips',
    color: 'purple',
  },
  {
    id: 'web',
    name_en: 'Islamic Web Search',
    name_ar: 'البحث الإسلامي',
    description_en: 'Search verified Islamic websites and scholarly resources from trusted sources',
    description_ar: 'البحث في المواقع الإسلامية الموثقة والموارد العلمية من مصادر موثوقة',
    icon: Globe,
    path: '/tools/web',
    color: 'indigo',
  },
];

export function ToolsPage() {
  const { language } = useLanguageStore();

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {language === 'ar' ? 'الأدوات الإسلامية' : 'Islamic Tools'}
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          {language === 'ar'
            ? 'مجموعة من الأدوات المفيدة للمسلمين - حاسبة الزكاة، البحث عن المساجد، والمزيد'
            : 'A collection of helpful tools for Muslims - Zakat calculator, mosque finder, and more'}
        </p>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {TOOL_MODULES.map((tool) => (
          <ToolCard key={tool.id} tool={tool} language={language} />
        ))}
      </div>
    </div>
  );
}

interface ToolCardProps {
  tool: ToolModule;
  language: 'ar' | 'en';
}

function ToolCard({ tool, language }: ToolCardProps) {
  const Icon = tool.icon;
  const name = language === 'ar' ? tool.name_ar : tool.name_en;
  const description = language === 'ar' ? tool.description_ar : tool.description_en;

  const colorClasses: Record<string, { bg: string; icon: string; border: string; hover: string }> = {
    red: { bg: 'bg-red-50', icon: 'text-red-600', border: 'border-red-200', hover: 'hover:border-red-400' },
    blue: { bg: 'bg-blue-50', icon: 'text-blue-600', border: 'border-blue-200', hover: 'hover:border-blue-400' },
    green: { bg: 'bg-green-50', icon: 'text-green-600', border: 'border-green-200', hover: 'hover:border-green-400' },
    amber: { bg: 'bg-amber-50', icon: 'text-amber-600', border: 'border-amber-200', hover: 'hover:border-amber-400' },
    teal: { bg: 'bg-teal-50', icon: 'text-teal-600', border: 'border-teal-200', hover: 'hover:border-teal-400' },
    purple: { bg: 'bg-purple-50', icon: 'text-purple-600', border: 'border-purple-200', hover: 'hover:border-purple-400' },
    emerald: { bg: 'bg-emerald-50', icon: 'text-emerald-600', border: 'border-emerald-200', hover: 'hover:border-emerald-400' },
    indigo: { bg: 'bg-indigo-50', icon: 'text-indigo-600', border: 'border-indigo-200', hover: 'hover:border-indigo-400' },
    cyan: { bg: 'bg-cyan-50', icon: 'text-cyan-600', border: 'border-cyan-200', hover: 'hover:border-cyan-400' },
  };

  const colors = colorClasses[tool.color] || colorClasses.blue;

  return (
    <Link
      to={tool.path}
      className={clsx(
        'card border-2 transition-all hover:shadow-lg group',
        colors.border,
        colors.hover
      )}
      dir={language === 'ar' ? 'rtl' : 'ltr'}
    >
      <div className="flex items-start gap-4">
        <div className={clsx('p-3 rounded-lg transition-colors group-hover:scale-110', colors.bg)}>
          <Icon className={clsx('w-6 h-6', colors.icon)} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 mb-1">
            {name}
          </h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
    </Link>
  );
}
