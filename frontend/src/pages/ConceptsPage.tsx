import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  User,
  Users,
  MapPin,
  Zap,
  Heart,
  TrendingUp,
  Search,
  ArrowRight,
  Sparkles,
  BookMarked,
  Compass,
  Globe,
  ChevronRight,
  Eye,
  X
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { conceptsApi, ConceptSummary, ConceptTypeFacet } from '../lib/api';
import clsx from 'clsx';

// Enhanced type configuration with better Arabic support
const TYPE_CONFIG: Record<string, {
  icon: React.ReactNode;
  gradient: string;
  bgGradient: string;
  lightBg: string;
  color: string;
  borderColor: string;
  label: { ar: string; en: string };
  description: { ar: string; en: string };
}> = {
  person: {
    icon: <User className="w-5 h-5" />,
    gradient: 'from-blue-500 to-indigo-600',
    bgGradient: 'from-blue-50 to-indigo-50',
    lightBg: 'bg-blue-50',
    color: 'text-blue-600',
    borderColor: 'border-blue-200',
    label: { ar: 'شخصيات', en: 'Persons' },
    description: { ar: 'الأنبياء والصحابة وأهل الكتاب', en: 'Prophets, companions, and figures' },
  },
  nation: {
    icon: <Users className="w-5 h-5" />,
    gradient: 'from-purple-500 to-pink-600',
    bgGradient: 'from-purple-50 to-pink-50',
    lightBg: 'bg-purple-50',
    color: 'text-purple-600',
    borderColor: 'border-purple-200',
    label: { ar: 'أمم وأقوام', en: 'Nations' },
    description: { ar: 'الأمم السابقة وقصصهم', en: 'Past nations and their stories' },
  },
  place: {
    icon: <MapPin className="w-5 h-5" />,
    gradient: 'from-emerald-500 to-teal-600',
    bgGradient: 'from-emerald-50 to-teal-50',
    lightBg: 'bg-emerald-50',
    color: 'text-emerald-600',
    borderColor: 'border-emerald-200',
    label: { ar: 'أماكن', en: 'Places' },
    description: { ar: 'المواقع الجغرافية المذكورة', en: 'Geographic locations mentioned' },
  },
  miracle: {
    icon: <Zap className="w-5 h-5" />,
    gradient: 'from-amber-500 to-orange-600',
    bgGradient: 'from-amber-50 to-orange-50',
    lightBg: 'bg-amber-50',
    color: 'text-amber-600',
    borderColor: 'border-amber-200',
    label: { ar: 'معجزات', en: 'Miracles' },
    description: { ar: 'الآيات والمعجزات الربانية', en: 'Divine signs and miracles' },
  },
  theme: {
    icon: <Heart className="w-5 h-5" />,
    gradient: 'from-rose-500 to-red-600',
    bgGradient: 'from-rose-50 to-red-50',
    lightBg: 'bg-rose-50',
    color: 'text-rose-600',
    borderColor: 'border-rose-200',
    label: { ar: 'موضوعات', en: 'Themes' },
    description: { ar: 'المواضيع القرآنية الرئيسية', en: 'Major Quranic themes' },
  },
  moral_pattern: {
    icon: <TrendingUp className="w-5 h-5" />,
    gradient: 'from-indigo-500 to-violet-600',
    bgGradient: 'from-indigo-50 to-violet-50',
    lightBg: 'bg-indigo-50',
    color: 'text-indigo-600',
    borderColor: 'border-indigo-200',
    label: { ar: 'سنن إلهية', en: 'Divine Patterns' },
    description: { ar: 'السنن الإلهية والأنماط', en: 'Divine patterns and laws' },
  },
  rhetorical: {
    icon: <BookOpen className="w-5 h-5" />,
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-50 to-teal-50',
    lightBg: 'bg-cyan-50',
    color: 'text-cyan-600',
    borderColor: 'border-cyan-200',
    label: { ar: 'بلاغة', en: 'Rhetorical' },
    description: { ar: 'الأساليب البلاغية القرآنية', en: 'Quranic rhetorical devices' },
  },
};

export function ConceptsPage() {
  const { language } = useLanguageStore();
  const [concepts, setConcepts] = useState<ConceptSummary[]>([]);
  const [typeFacets, setTypeFacets] = useState<ConceptTypeFacet[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [curatedConcepts, setCuratedConcepts] = useState<ConceptSummary[]>([]);

  const isArabic = language === 'ar';

  useEffect(() => {
    loadTypeFacets();
    loadCuratedConcepts();
  }, []);

  useEffect(() => {
    loadConcepts();
  }, [selectedType, searchQuery]);

  async function loadTypeFacets() {
    try {
      const response = await conceptsApi.getConceptTypes();
      setTypeFacets(response.data);
    } catch (error) {
      console.error('Failed to load concept types:', error);
    }
  }

  async function loadCuratedConcepts() {
    try {
      const response = await conceptsApi.listConcepts({ curated_only: true, limit: 12 });
      setCuratedConcepts(response.data.concepts);
    } catch (error) {
      console.error('Failed to load curated concepts:', error);
    }
  }

  async function loadConcepts() {
    setLoading(true);
    try {
      const params: Record<string, string | number | boolean | undefined> = {
        limit: 100,
      };
      if (selectedType) {
        params.type = selectedType;
      }
      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }
      const response = await conceptsApi.listConcepts(params);
      setConcepts(response.data.concepts);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to load concepts:', error);
    } finally {
      setLoading(false);
    }
  }

  // Group concepts by type for display
  const groupedConcepts = concepts.reduce((acc, concept) => {
    const type = concept.type;
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(concept);
    return acc;
  }, {} as Record<string, ConceptSummary[]>);

  // Calculate total stats
  const totalStats = typeFacets.reduce(
    (acc, facet) => {
      acc.total += facet.count;
      return acc;
    },
    { total: 0 }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedType(null);
  };

  return (
    <div className="min-h-screen bg-gray-50" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700">
        {/* Decorative Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23fff' fill-opacity='1'%3E%3Cpath d='M20 20h-4v-4h4v4zm4-4h-4v-4h4v4zm-8 8h-4v-4h4v4z'/%3E%3C/g%3E%3C/svg%3E")`,
          }} />
        </div>

        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
          <div className="text-center text-white">
            {/* Icon */}
            <div className="inline-flex p-3 bg-white/20 rounded-2xl backdrop-blur-sm mb-4">
              <Compass className="w-8 h-8 sm:w-10 sm:h-10" />
            </div>

            {/* Title */}
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3">
              {isArabic ? 'مستكشف المفاهيم القرآنية' : 'Quranic Concept Explorer'}
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-emerald-100 max-w-2xl mx-auto mb-6 sm:mb-8 px-4">
              {isArabic
                ? 'استكشف الشخصيات والأمم والأماكن والمعجزات والموضوعات في القرآن الكريم'
                : 'Explore persons, nations, places, miracles, and themes in the Holy Quran'}
            </p>

            {/* Search Box */}
            <form onSubmit={handleSearch} className="max-w-lg mx-auto px-4">
              <div className="relative">
                <Search className={clsx(
                  "absolute top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400",
                  isArabic ? "right-4" : "left-4"
                )} />
                <input
                  type="text"
                  placeholder={isArabic ? 'ابحث عن مفهوم...' : 'Search concepts...'}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={clsx(
                    "w-full py-3.5 sm:py-4 text-gray-900 bg-white rounded-xl sm:rounded-2xl shadow-lg",
                    "focus:ring-4 focus:ring-white/30 focus:outline-none text-base sm:text-lg",
                    isArabic ? "pr-12 pl-4" : "pl-12 pr-4"
                  )}
                  dir={isArabic ? 'rtl' : 'ltr'}
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => setSearchQuery('')}
                    className={clsx(
                      "absolute top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100",
                      isArabic ? "left-3" : "right-3"
                    )}
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                )}
              </div>
            </form>

            {/* Stats */}
            <div className="flex justify-center gap-6 sm:gap-10 mt-6 sm:mt-8">
              <div className="text-center">
                <div className="text-2xl sm:text-3xl font-bold">{totalStats.total}</div>
                <div className="text-emerald-200 text-xs sm:text-sm">
                  {isArabic ? 'مفهوم' : 'Concepts'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl sm:text-3xl font-bold">{typeFacets.length}</div>
                <div className="text-emerald-200 text-xs sm:text-sm">
                  {isArabic ? 'تصنيف' : 'Categories'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl sm:text-3xl font-bold">{curatedConcepts.length}+</div>
                <div className="text-emerald-200 text-xs sm:text-sm">
                  {isArabic ? 'محقق' : 'Verified'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Category Filter - Scrollable on mobile */}
        <section className="mb-8 -mt-6 sm:-mt-8">
          <div className="flex gap-2 sm:gap-3 overflow-x-auto pb-2 scrollbar-hide sm:grid sm:grid-cols-4 lg:grid-cols-8 sm:overflow-visible">
            {/* All Button */}
            <button
              onClick={() => setSelectedType(null)}
              className={clsx(
                'flex-shrink-0 sm:flex-shrink flex flex-col items-center p-3 sm:p-4 rounded-xl transition-all duration-200',
                'min-w-[80px] sm:min-w-0',
                !selectedType
                  ? 'bg-gray-900 text-white shadow-lg'
                  : 'bg-white text-gray-700 shadow hover:shadow-md'
              )}
            >
              <div className={clsx(
                'w-9 h-9 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center mb-1.5',
                !selectedType ? 'bg-white/20' : 'bg-gray-100'
              )}>
                <Globe className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
              <span className="font-medium text-xs sm:text-sm">{isArabic ? 'الكل' : 'All'}</span>
              <span className="text-[10px] sm:text-xs opacity-60">{totalStats.total}</span>
            </button>

            {/* Category Buttons */}
            {typeFacets.map((facet) => {
              const config = TYPE_CONFIG[facet.type];
              if (!config) return null;

              const isSelected = selectedType === facet.type;
              return (
                <button
                  key={facet.type}
                  onClick={() => setSelectedType(isSelected ? null : facet.type)}
                  className={clsx(
                    'flex-shrink-0 sm:flex-shrink flex flex-col items-center p-3 sm:p-4 rounded-xl transition-all duration-200',
                    'min-w-[80px] sm:min-w-0',
                    isSelected
                      ? `bg-gradient-to-br ${config.gradient} text-white shadow-lg`
                      : `bg-white ${config.color} shadow hover:shadow-md`
                  )}
                >
                  <div className={clsx(
                    'w-9 h-9 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center mb-1.5',
                    isSelected ? 'bg-white/20' : config.lightBg
                  )}>
                    {config.icon}
                  </div>
                  <span className="font-medium text-xs sm:text-sm whitespace-nowrap">
                    {isArabic ? config.label.ar : config.label.en}
                  </span>
                  <span className="text-[10px] sm:text-xs opacity-60">{facet.count}</span>
                </button>
              );
            })}
          </div>
        </section>

        {/* Quick Links */}
        <section className="mb-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <Link
              to="/miracles"
              className="flex items-center gap-3 sm:gap-4 p-4 sm:p-5 bg-gradient-to-r from-amber-50 to-orange-50
                         rounded-xl border border-amber-200/50 hover:shadow-lg hover:border-amber-300
                         transition-all group"
            >
              <div className="p-2.5 sm:p-3 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl text-white">
                <Sparkles className="w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-amber-900 text-sm sm:text-base">
                  {isArabic ? 'عدسة المعجزات' : 'Miracles Lens'}
                </h3>
                <p className="text-xs sm:text-sm text-amber-700 truncate">
                  {isArabic ? 'استكشف الآيات والمعجزات' : 'Explore divine signs'}
                </p>
              </div>
              <ArrowRight className={clsx(
                "w-5 h-5 text-amber-500 group-hover:translate-x-1 transition-transform",
                isArabic && "rotate-180 group-hover:-translate-x-1"
              )} />
            </Link>

            <Link
              to="/stories"
              className="flex items-center gap-3 sm:gap-4 p-4 sm:p-5 bg-gradient-to-r from-purple-50 to-pink-50
                         rounded-xl border border-purple-200/50 hover:shadow-lg hover:border-purple-300
                         transition-all group"
            >
              <div className="p-2.5 sm:p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl text-white">
                <BookMarked className="w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-purple-900 text-sm sm:text-base">
                  {isArabic ? 'قصص الأنبياء' : 'Prophet Stories'}
                </h3>
                <p className="text-xs sm:text-sm text-purple-700 truncate">
                  {isArabic ? 'تصفح قصص الأنبياء والأمم' : 'Browse prophets & nations'}
                </p>
              </div>
              <ArrowRight className={clsx(
                "w-5 h-5 text-purple-500 group-hover:translate-x-1 transition-transform",
                isArabic && "rotate-180 group-hover:-translate-x-1"
              )} />
            </Link>
          </div>
        </section>

        {/* Featured Concepts - Only when no filters */}
        {!selectedType && !searchQuery && curatedConcepts.length > 0 && (
          <section className="mb-10">
            <div className="flex items-center justify-between mb-4 sm:mb-5">
              <h2 className={clsx(
                "text-lg sm:text-xl font-bold text-gray-900",
                isArabic && "font-arabic"
              )}>
                {isArabic ? 'مفاهيم مميزة' : 'Featured Concepts'}
              </h2>
              <span className={clsx(
                "text-xs sm:text-sm text-gray-500",
                isArabic && "font-arabic"
              )}>
                {isArabic ? 'محتوى موثّق' : 'Verified content'}
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
              {curatedConcepts.slice(0, 8).map((concept) => (
                <ConceptCard key={concept.id} concept={concept} language={language} featured />
              ))}
            </div>
          </section>
        )}

        {/* Results Section */}
        <section>
          {/* Results Header */}
          <div className="flex items-center justify-between mb-4 sm:mb-5">
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-gray-900">
                {selectedType
                  ? (isArabic ? TYPE_CONFIG[selectedType]?.label.ar : TYPE_CONFIG[selectedType]?.label.en)
                  : searchQuery
                    ? (isArabic ? 'نتائج البحث' : 'Search Results')
                    : (isArabic ? 'جميع المفاهيم' : 'All Concepts')}
              </h2>
              <p className="text-xs sm:text-sm text-gray-500 mt-0.5">
                {isArabic ? `${total} مفهوم` : `${total} concepts`}
              </p>
            </div>
            {(selectedType || searchQuery) && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1.5 text-xs sm:text-sm text-emerald-600 hover:text-emerald-700
                           font-medium px-3 py-1.5 rounded-lg hover:bg-emerald-50 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                {isArabic ? 'مسح' : 'Clear'}
              </button>
            )}
          </div>

          {/* Loading State */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-gray-500 text-sm">{isArabic ? 'جاري التحميل...' : 'Loading...'}</p>
            </div>
          ) : concepts.length === 0 ? (
            /* Empty State */
            <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
              <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2">
                {isArabic ? 'لا توجد نتائج' : 'No results found'}
              </h3>
              <p className="text-sm text-gray-500 mb-4 px-4">
                {isArabic ? 'جرب البحث بكلمات مختلفة' : 'Try different search terms'}
              </p>
              <button
                onClick={clearFilters}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-emerald-600
                           hover:bg-emerald-50 rounded-lg transition-colors"
              >
                {isArabic ? 'مسح البحث' : 'Clear search'}
              </button>
            </div>
          ) : selectedType || searchQuery ? (
            /* Filtered View - Flat Grid */
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
              {concepts.map((concept) => (
                <ConceptCard key={concept.id} concept={concept} language={language} />
              ))}
            </div>
          ) : (
            /* Grouped View - By Category */
            <div className="space-y-10">
              {Object.entries(groupedConcepts).map(([type, typeConcepts]) => {
                const config = TYPE_CONFIG[type];
                if (!config) return null;

                return (
                  <div key={type}>
                    {/* Category Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={clsx(
                          'p-2 rounded-lg bg-gradient-to-br text-white',
                          config.gradient
                        )}>
                          {config.icon}
                        </div>
                        <div>
                          <h3 className="text-base sm:text-lg font-bold text-gray-900">
                            {isArabic ? config.label.ar : config.label.en}
                          </h3>
                          <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">
                            {isArabic ? config.description.ar : config.description.en}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => setSelectedType(type)}
                        className={clsx(
                          'flex items-center gap-1 text-xs sm:text-sm font-medium px-2.5 py-1.5 rounded-lg',
                          'transition-colors',
                          config.color,
                          config.lightBg,
                          'hover:opacity-80'
                        )}
                      >
                        {isArabic ? 'عرض الكل' : 'View all'}
                        <span className="opacity-60">({typeConcepts.length})</span>
                        <ChevronRight className={clsx("w-4 h-4", isArabic && "rotate-180")} />
                      </button>
                    </div>

                    {/* Category Cards Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
                      {typeConcepts.slice(0, 8).map((concept) => (
                        <ConceptCard key={concept.id} concept={concept} language={language} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

// Clean, Minimalist Concept Card - Pure language mode (no mixed content)
function ConceptCard({
  concept,
  language,
  featured = false
}: {
  concept: ConceptSummary;
  language: 'ar' | 'en';
  featured?: boolean;
}) {
  const isArabic = language === 'ar';
  const config = TYPE_CONFIG[concept.type];

  // Get the appropriate label based on language - use primary language only
  const primaryLabel = isArabic ? concept.label_ar : concept.label_en;
  // Fallback if primary label is empty
  const displayLabel = primaryLabel || (isArabic ? concept.label_en : concept.label_ar);

  return (
    <Link
      to={`/concepts/${concept.id}`}
      className={clsx(
        'group block rounded-xl transition-all duration-200',
        'bg-white border hover:shadow-md hover:-translate-y-0.5',
        featured ? 'border-gray-200 p-4' : 'border-gray-100 p-3 sm:p-4'
      )}
    >
      {/* Icon & Title Row */}
      <div className="flex items-start gap-2.5 sm:gap-3">
        <div className={clsx(
          'flex-shrink-0 p-2 rounded-lg',
          config?.lightBg || 'bg-gray-100',
          config?.color || 'text-gray-600'
        )}>
          {config?.icon || <BookOpen className="w-4 h-4" />}
        </div>
        <div className="flex-1 min-w-0">
          {/* Primary Label - Single language only */}
          <h3 className={clsx(
            'font-semibold text-gray-900 group-hover:text-emerald-600 transition-colors truncate',
            featured ? 'text-base' : 'text-sm sm:text-base',
            isArabic && 'font-arabic'
          )}>
            {displayLabel}
          </h3>
        </div>
      </div>

      {/* Footer: Type Badge & Occurrence Count */}
      <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-gray-50">
        <span className={clsx(
          'text-[10px] sm:text-xs font-medium px-2 py-0.5 rounded-full',
          config?.lightBg || 'bg-gray-100',
          config?.color || 'text-gray-600'
        )}>
          {isArabic ? config?.label.ar : config?.label.en}
        </span>
        {concept.occurrence_count > 0 && (
          <div className="flex items-center gap-1 text-gray-400">
            <Eye className="w-3 h-3" />
            <span className="text-[10px] sm:text-xs">{concept.occurrence_count}</span>
          </div>
        )}
      </div>
    </Link>
  );
}
