import { Link } from 'react-router-dom';
import { ArrowLeft, Globe, ExternalLink, Info } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

/**
 * A plain directory of outside Islamic websites, linked by their home page.
 *
 * There is no search here: the earlier "search" filtered a hardcoded list of
 * sample results and showed them as if they answered the query. We do not
 * review these sites, so the page says so and makes no trust claim.
 */

interface ExternalSite {
  domain: string;
  name_en: string;
  name_ar: string;
  description_en: string;
  description_ar: string;
}

const EXTERNAL_SITES: ExternalSite[] = [
  {
    domain: 'quran.com',
    name_en: 'Quran.com',
    name_ar: 'Quran.com',
    description_en: 'Quran text, translations and recitations',
    description_ar: 'نص القرآن والترجمات والتلاوات',
  },
  {
    domain: 'sunnah.com',
    name_en: 'Sunnah.com',
    name_ar: 'Sunnah.com',
    description_en: 'Hadith collections',
    description_ar: 'مجموعات الحديث',
  },
  {
    domain: 'islamqa.info',
    name_en: 'IslamQA',
    name_ar: 'الإسلام سؤال وجواب',
    description_en: 'Questions and answers on Islamic topics',
    description_ar: 'أسئلة وأجوبة في موضوعات إسلامية',
  },
  {
    domain: 'islamweb.net',
    name_en: 'IslamWeb',
    name_ar: 'إسلام ويب',
    description_en: 'General Islamic portal',
    description_ar: 'بوابة إسلامية عامة',
  },
  {
    domain: 'seekersguidance.org',
    name_en: 'SeekersGuidance',
    name_ar: 'SeekersGuidance',
    description_en: 'Online Islamic courses',
    description_ar: 'دورات إسلامية عبر الإنترنت',
  },
  {
    domain: 'yaqeeninstitute.org',
    name_en: 'Yaqeen Institute',
    name_ar: 'معهد يقين',
    description_en: 'Islamic research and articles',
    description_ar: 'بحوث ومقالات إسلامية',
  },
  {
    domain: 'aboutislam.net',
    name_en: 'About Islam',
    name_ar: 'About Islam',
    description_en: 'Articles and counselling columns',
    description_ar: 'مقالات وأبواب استشارية',
  },
  {
    domain: 'islamicity.org',
    name_en: 'IslamiCity',
    name_ar: 'IslamiCity',
    description_en: 'Islamic articles and resources',
    description_ar: 'مقالات ومصادر إسلامية',
  },
];

export function IslamicWebSearchPage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      <div className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} aria-hidden="true" />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-indigo-100 rounded-lg">
            <Globe className="w-8 h-8 text-indigo-600" aria-hidden="true" />
          </div>
          <div>
            <h1 className={clsx('text-2xl font-bold text-gray-900', isArabic && 'font-arabic')}>
              {isArabic ? 'مواقع إسلامية خارجية' : 'Outside Islamic websites'}
            </h1>
            <p className={clsx('text-gray-600', isArabic && 'font-arabic')}>
              {isArabic ? 'قائمة روابط إلى الصفحات الرئيسية لمواقع أخرى' : 'A list of links to the home pages of other websites'}
            </p>
          </div>
        </div>
      </div>

      <div className="mb-6 flex items-start gap-2 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
        <Info className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
        <p className={clsx(isArabic && 'font-arabic')}>
          {isArabic
            ? 'هذه المواقع ليست تابعة لتدبّر، ولا نراجع محتواها. تفتح الروابط خارج التطبيق.'
            : 'These sites are not part of Tadabbur and we do not review their content. Links open outside the app.'}
        </p>
      </div>

      <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {EXTERNAL_SITES.map((site) => {
          const name = isArabic ? site.name_ar : site.name_en;
          const latinName = /^[\x20-\x7E]+$/.test(name);
          return (
            <li key={site.domain}>
              <a
                href={`https://${site.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="card flex h-full items-start gap-3 border border-gray-200 hover:border-indigo-300 transition-colors group"
              >
                <div className="p-2 bg-indigo-50 rounded-lg group-hover:bg-indigo-100">
                  <Globe className="w-5 h-5 text-indigo-600" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className={clsx('font-semibold text-gray-900 group-hover:text-indigo-600', isArabic && !latinName && 'font-arabic')}>
                    {latinName ? <span dir="ltr">{name}</span> : name}
                  </h2>
                  <p className="text-xs text-gray-500 mb-1" dir="ltr">{site.domain}</p>
                  <p className={clsx('text-sm text-gray-600', isArabic && 'font-arabic')}>
                    {isArabic ? site.description_ar : site.description_en}
                  </p>
                </div>
                <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-indigo-600 shrink-0" aria-hidden="true" />
                <span className="sr-only">{isArabic ? '(يفتح موقعًا خارجيًا)' : '(opens an outside website)'}</span>
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
