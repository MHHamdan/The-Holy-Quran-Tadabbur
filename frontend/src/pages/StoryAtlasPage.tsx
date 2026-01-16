import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Map, Book, Users, Clock, ArrowRight, Search } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { storyAtlasApi, StoryCluster } from '../lib/api';
import { translateTag, translateFigure, Language } from '../i18n/translations';
import clsx from 'clsx';

// Category translations
const CATEGORY_TRANSLATIONS: Record<string, { ar: string; en: string }> = {
  prophet: { ar: 'الأنبياء', en: 'Prophet' },
  named_char: { ar: 'شخصيات مسماة', en: 'Named Character' },
  nation: { ar: 'أمة', en: 'Nation' },
  parable: { ar: 'مثل', en: 'Parable' },
  historical: { ar: 'تاريخي', en: 'Historical' },
  unseen: { ar: 'الغيب', en: 'Unseen' },
  righteous: { ar: 'الصالحين', en: 'Righteous' },
};

// Helper to translate category
function translateCategory(category: string, language: Language): string {
  const trans = CATEGORY_TRANSLATIONS[category];
  return trans ? trans[language] : category.replace(/_/g, ' ');
}

const CATEGORIES = [
  { id: 'all', labelAr: 'الكل', labelEn: 'All' },
  { id: 'prophet', labelAr: 'الأنبياء', labelEn: 'Prophets' },
  { id: 'named_char', labelAr: 'شخصيات', labelEn: 'Characters' },
  { id: 'nation', labelAr: 'الأمم', labelEn: 'Nations' },
  { id: 'parable', labelAr: 'أمثال', labelEn: 'Parables' },
  { id: 'historical', labelAr: 'تاريخية', labelEn: 'Historical' },
  { id: 'unseen', labelAr: 'الغيب', labelEn: 'Unseen' },
];

const ERA_LABELS: Record<string, { ar: string; en: string }> = {
  primordial: { ar: 'البدء', en: 'Primordial' },
  ancient: { ar: 'الأنبياء الأوائل', en: 'Ancient' },
  egypt: { ar: 'عصر مصر', en: 'Egypt Era' },
  israelite: { ar: 'بني إسرائيل', en: 'Israelite' },
  pre_islamic: { ar: 'ما قبل الإسلام', en: 'Pre-Islamic' },
  unknown: { ar: 'غير محدد', en: 'Unknown' },
};

export function StoryAtlasPage() {
  const { language } = useLanguageStore();
  const [clusters, setClusters] = useState<StoryCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadClusters();
  }, [selectedCategory, searchQuery]);

  async function loadClusters() {
    setLoading(true);
    try {
      const params: Record<string, string | number | undefined> = {
        limit: 50,
      };
      if (selectedCategory !== 'all') {
        params.category = selectedCategory;
      }
      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }
      const response = await storyAtlasApi.listClusters(params);
      setClusters(response.data.clusters);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to load clusters:', error);
    } finally {
      setLoading(false);
    }
  }

  const isArabic = language === 'ar';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Map className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            {isArabic ? 'أطلس القصص القرآنية' : 'Quran Story Atlas'}
          </h1>
        </div>
        <p className="text-gray-600">
          {isArabic
            ? 'استكشف قصص القرآن الكريم مرتبة حسب الشخصيات والأماكن والأزمنة'
            : 'Explore Quranic narratives organized by persons, places, and eras'}
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder={isArabic ? 'ابحث في القصص...' : 'Search stories...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            dir={isArabic ? 'rtl' : 'ltr'}
          />
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-8">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={clsx(
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              selectedCategory === cat.id
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            {isArabic ? cat.labelAr : cat.labelEn}
          </button>
        ))}
      </div>

      {/* Results count */}
      <div className="mb-4 text-sm text-gray-500">
        {isArabic
          ? `${total} قصة متاحة`
          : `${total} stories available`}
      </div>

      {/* Stories Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">{isArabic ? 'جاري التحميل...' : 'Loading...'}</p>
        </div>
      ) : clusters.length === 0 ? (
        <div className="text-center py-12 card">
          <Map className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {isArabic
              ? 'لا توجد قصص مطابقة للبحث'
              : 'No stories match your search'}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            {isArabic
              ? 'جرب تغيير معايير البحث'
              : 'Try adjusting your filters'}
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clusters.map((cluster) => (
            <ClusterCard key={cluster.id} cluster={cluster} language={language} />
          ))}
        </div>
      )}
    </div>
  );
}

function ClusterCard({ cluster, language }: { cluster: StoryCluster; language: 'ar' | 'en' }) {
  const isArabic = language === 'ar';
  const title = isArabic ? cluster.title_ar : cluster.title_en;
  const era = cluster.era ? (ERA_LABELS[cluster.era]?.[language] || cluster.era) : null;

  // Helper to translate person name
  const translatePerson = (person: string): string => {
    return translateFigure(person, language);
  };

  return (
    <Link
      to={`/story-atlas/${cluster.id}`}
      className="card hover:shadow-lg transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
          <Book className="w-5 h-5 text-primary-600" />
        </div>
        <div className="flex gap-1">
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {translateCategory(cluster.category, language)}
          </span>
          {era && (
            <span className="text-xs font-medium text-amber-700 bg-amber-50 px-2 py-1 rounded">
              {era}
            </span>
          )}
        </div>
      </div>

      <h3 className="text-lg font-semibold mb-2 group-hover:text-primary-600 transition-colors">
        {title}
      </h3>

      {cluster.summary_en && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {cluster.summary_en}
        </p>
      )}

      {/* Main Persons */}
      {cluster.main_persons && cluster.main_persons.length > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500">
            {cluster.main_persons.slice(0, 3).map(p => translatePerson(p)).join(isArabic ? '، ' : ', ')}
            {cluster.main_persons.length > 3 && '...'}
          </span>
        </div>
      )}

      {/* Event count & Sura */}
      <div className="flex items-center gap-4 mb-4 text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          <span>{cluster.event_count} {isArabic ? 'أحداث' : 'events'}</span>
        </div>
        {cluster.primary_sura && (
          <div className="flex items-center gap-1">
            <Book className="w-4 h-4" />
            <span>{isArabic ? 'سورة' : 'Surah'} {cluster.primary_sura}</span>
          </div>
        )}
      </div>

      {/* Tags */}
      {cluster.tags && cluster.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {cluster.tags.slice(0, 3).map((tag) => {
            const { text: translatedTag } = translateTag(tag, language);
            return (
              <span
                key={tag}
                className="text-xs px-2 py-0.5 rounded bg-primary-50 text-primary-700"
              >
                {translatedTag}
              </span>
            );
          })}
        </div>
      )}

      <div className="flex items-center text-primary-600 text-sm font-medium">
        {isArabic ? 'استكشف القصة' : 'Explore Story'}
        <ArrowRight className={`w-4 h-4 ${isArabic ? 'mr-1 group-hover:-translate-x-1' : 'ml-1 group-hover:translate-x-1'} transition-transform`} />
      </div>
    </Link>
  );
}
