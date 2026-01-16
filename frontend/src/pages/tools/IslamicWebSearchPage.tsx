import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Search, Globe, ExternalLink, Loader2, Filter, Shield } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

interface SearchResult {
  id: string;
  title: string;
  description: string;
  url: string;
  domain: string;
  category: string;
  isTrusted: boolean;
}

interface TrustedSite {
  domain: string;
  name_en: string;
  name_ar: string;
  category: string;
  description_en: string;
  description_ar: string;
}

// Curated list of trusted Islamic websites
const TRUSTED_SITES: TrustedSite[] = [
  {
    domain: 'islamqa.info',
    name_en: 'IslamQA',
    name_ar: 'إسلام سؤال وجواب',
    category: 'fatwa',
    description_en: 'Comprehensive Q&A on Islamic topics',
    description_ar: 'أسئلة وأجوبة شاملة في المواضيع الإسلامية',
  },
  {
    domain: 'sunnah.com',
    name_en: 'Sunnah.com',
    name_ar: 'موقع السنة',
    category: 'hadith',
    description_en: 'Searchable hadith collections',
    description_ar: 'مجموعات الحديث القابلة للبحث',
  },
  {
    domain: 'quran.com',
    name_en: 'Quran.com',
    name_ar: 'القرآن الكريم',
    category: 'quran',
    description_en: 'Quran text, translations, and audio',
    description_ar: 'نص القرآن والترجمات والتلاوات',
  },
  {
    domain: 'islamweb.net',
    name_en: 'IslamWeb',
    name_ar: 'إسلام ويب',
    category: 'general',
    description_en: 'Comprehensive Islamic portal',
    description_ar: 'بوابة إسلامية شاملة',
  },
  {
    domain: 'seekersguidance.org',
    name_en: 'SeekersGuidance',
    name_ar: 'هداية الطالبين',
    category: 'education',
    description_en: 'Free Islamic courses and answers',
    description_ar: 'دورات إسلامية مجانية وإجابات',
  },
  {
    domain: 'yaqeeninstitute.org',
    name_en: 'Yaqeen Institute',
    name_ar: 'معهد يقين',
    category: 'research',
    description_en: 'Islamic research and publications',
    description_ar: 'البحوث والمنشورات الإسلامية',
  },
  {
    domain: 'aboutislam.net',
    name_en: 'About Islam',
    name_ar: 'عن الإسلام',
    category: 'general',
    description_en: 'Islamic content and counseling',
    description_ar: 'محتوى إسلامي واستشارات',
  },
  {
    domain: 'islamicity.org',
    name_en: 'IslamiCity',
    name_ar: 'إسلامي سيتي',
    category: 'general',
    description_en: 'Islamic encyclopedia and resources',
    description_ar: 'موسوعة إسلامية ومصادر',
  },
];

const SEARCH_CATEGORIES = [
  { id: 'all', name_en: 'All Topics', name_ar: 'جميع المواضيع' },
  { id: 'quran', name_en: 'Quran & Tafsir', name_ar: 'القرآن والتفسير' },
  { id: 'hadith', name_en: 'Hadith', name_ar: 'الحديث' },
  { id: 'fatwa', name_en: 'Fatwas', name_ar: 'الفتاوى' },
  { id: 'fiqh', name_en: 'Fiqh', name_ar: 'الفقه' },
  { id: 'aqeedah', name_en: 'Aqeedah', name_ar: 'العقيدة' },
  { id: 'history', name_en: 'Islamic History', name_ar: 'التاريخ الإسلامي' },
  { id: 'education', name_en: 'Education', name_ar: 'تعليم' },
];

// Sample search results for demonstration
const SAMPLE_RESULTS: SearchResult[] = [
  {
    id: '1',
    title: 'The Five Pillars of Islam - Comprehensive Guide',
    description: 'Learn about the five fundamental acts of worship that are central to the practice of Islam: Shahada, Salah, Zakat, Sawm, and Hajj.',
    url: 'https://islamqa.info/en/answers/13569',
    domain: 'islamqa.info',
    category: 'education',
    isTrusted: true,
  },
  {
    id: '2',
    title: 'Sahih al-Bukhari - Book of Faith',
    description: 'Read the authentic hadith collection of Imam al-Bukhari, the most reliable source of prophetic traditions.',
    url: 'https://sunnah.com/bukhari/2',
    domain: 'sunnah.com',
    category: 'hadith',
    isTrusted: true,
  },
  {
    id: '3',
    title: 'Surah Al-Baqarah - Translation and Tafsir',
    description: 'Read the longest surah of the Quran with multiple translations and detailed explanations.',
    url: 'https://quran.com/2',
    domain: 'quran.com',
    category: 'quran',
    isTrusted: true,
  },
  {
    id: '4',
    title: 'Understanding Islamic Prayer Times',
    description: 'A detailed explanation of how prayer times are calculated and the significance of each prayer.',
    url: 'https://islamweb.net/en/article/prayer-times',
    domain: 'islamweb.net',
    category: 'fiqh',
    isTrusted: true,
  },
  {
    id: '5',
    title: 'Free Islamic Courses Online',
    description: 'Access free, structured Islamic education from qualified scholars on various topics.',
    url: 'https://seekersguidance.org/courses/',
    domain: 'seekersguidance.org',
    category: 'education',
    isTrusted: true,
  },
];

export function IslamicWebSearchPage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [trustedOnly, setTrustedOnly] = useState(true);

  const performSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setHasSearched(true);

    try {
      // Simulate API call - in production, use custom search API
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Filter sample results based on search and category
      let filtered = SAMPLE_RESULTS.filter((r) =>
        r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.description.toLowerCase().includes(searchQuery.toLowerCase())
      );

      if (selectedCategory !== 'all') {
        filtered = filtered.filter((r) => r.category === selectedCategory);
      }

      if (trustedOnly) {
        filtered = filtered.filter((r) => r.isTrusted);
      }

      // If no matches, show all results as demonstration
      setResults(filtered.length > 0 ? filtered : SAMPLE_RESULTS);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedCategory, trustedOnly]);

  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      performSearch();
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-indigo-100 rounded-lg">
            <Search className="w-8 h-8 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isArabic ? 'البحث الإسلامي' : 'Islamic Web Search'}
            </h1>
            <p className="text-gray-600">
              {isArabic
                ? 'ابحث في المواقع الإسلامية الموثقة'
                : 'Search trusted Islamic websites'}
            </p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search
            className={clsx(
              'absolute top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400',
              isArabic ? 'right-4' : 'left-4'
            )}
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isArabic ? 'ابحث عن مواضيع إسلامية...' : 'Search Islamic topics...'}
            className={clsx(
              'w-full py-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
              isArabic ? 'pr-12 pl-28' : 'pl-12 pr-28'
            )}
          />
          <button
            onClick={performSearch}
            disabled={loading || !searchQuery.trim()}
            className={clsx(
              'absolute top-1/2 transform -translate-y-1/2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed',
              isArabic ? 'left-2' : 'right-2'
            )}
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isArabic ? (
              'بحث'
            ) : (
              'Search'
            )}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        {/* Category Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
          >
            {SEARCH_CATEGORIES.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {isArabic ? cat.name_ar : cat.name_en}
              </option>
            ))}
          </select>
        </div>

        {/* Trusted Only Toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={trustedOnly}
            onChange={(e) => setTrustedOnly(e.target.checked)}
            className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
          />
          <span className="text-sm text-gray-700 flex items-center gap-1">
            <Shield className="w-4 h-4 text-green-600" />
            {isArabic ? 'المصادر الموثقة فقط' : 'Trusted sources only'}
          </span>
        </label>
      </div>

      {/* Results or Landing Content */}
      {!hasSearched ? (
        <>
          {/* Trusted Sites Grid */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {isArabic ? 'مواقع موثقة' : 'Trusted Islamic Websites'}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {TRUSTED_SITES.map((site) => (
                <a
                  key={site.domain}
                  href={`https://${site.domain}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card border border-gray-200 hover:border-indigo-300 transition-colors group"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-indigo-50 rounded-lg group-hover:bg-indigo-100">
                      <Globe className="w-5 h-5 text-indigo-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600">
                          {isArabic ? site.name_ar : site.name_en}
                        </h3>
                        <span title="Trusted"><Shield className="w-4 h-4 text-green-600" /></span>
                      </div>
                      <p className="text-xs text-gray-500 mb-1">{site.domain}</p>
                      <p className="text-sm text-gray-600">
                        {isArabic ? site.description_ar : site.description_en}
                      </p>
                    </div>
                    <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-indigo-600" />
                  </div>
                </a>
              ))}
            </div>
          </div>

          {/* Search Tips */}
          <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-lg">
            <h3 className="font-semibold text-indigo-900 mb-2">
              {isArabic ? 'نصائح للبحث' : 'Search Tips'}
            </h3>
            <ul className="text-sm text-indigo-800 space-y-1">
              <li>
                • {isArabic ? 'استخدم كلمات مفتاحية محددة للحصول على نتائج أفضل' : 'Use specific keywords for better results'}
              </li>
              <li>
                • {isArabic ? 'يمكنك البحث باللغتين العربية والإنجليزية' : 'You can search in both Arabic and English'}
              </li>
              <li>
                • {isArabic ? 'استخدم التصنيفات لتضييق نطاق البحث' : 'Use categories to narrow your search'}
              </li>
            </ul>
          </div>
        </>
      ) : (
        /* Search Results */
        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>{isArabic ? 'لا توجد نتائج' : 'No results found'}</p>
              <p className="text-sm mt-2">
                {isArabic ? 'جرب كلمات مفتاحية مختلفة' : 'Try different keywords'}
              </p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                {isArabic
                  ? `${results.length} نتيجة للبحث عن "${searchQuery}"`
                  : `${results.length} results for "${searchQuery}"`}
              </p>
              {results.map((result) => (
                <SearchResultCard key={result.id} result={result} language={language} />
              ))}
            </>
          )}
        </div>
      )}

      {/* Demo Notice */}
      <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
        <p>
          {isArabic
            ? 'ملاحظة: هذه نسخة تجريبية. في الإصدار الكامل، سيتم ربط البحث مباشرة بمحرك بحث مخصص للمواقع الإسلامية.'
            : 'Note: This is a demo version. In the full release, search will be connected to a custom Islamic content search engine.'}
        </p>
      </div>
    </div>
  );
}

// Search Result Card Component
interface SearchResultCardProps {
  result: SearchResult;
  language: 'ar' | 'en';
}

function SearchResultCard({ result, language }: SearchResultCardProps) {
  const isArabic = language === 'ar';

  return (
    <a
      href={result.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block card border border-gray-200 hover:border-indigo-300 transition-colors group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-indigo-600">{result.domain}</span>
            {result.isTrusted && (
              <span title={isArabic ? 'موثق' : 'Trusted'}><Shield className="w-3 h-3 text-green-600" /></span>
            )}
            <span className="text-xs text-gray-400 px-2 py-0.5 bg-gray-100 rounded-full">
              {SEARCH_CATEGORIES.find((c) => c.id === result.category)?.[
                isArabic ? 'name_ar' : 'name_en'
              ]}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 mb-1">
            {result.title}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-2">{result.description}</p>
        </div>
        <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-indigo-600 shrink-0" />
      </div>
    </a>
  );
}
