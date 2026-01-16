import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  BookOpen,
  User,
  Users,
  MapPin,
  Zap,
  Heart,
  TrendingUp,
  ArrowLeft,
  ExternalLink,
  Link2,
  ChevronRight,
  ChevronDown,
  CheckCircle,
  Search,
  Book,
  FileText,
  Layers,
  Eye,
  Share2,
  Bookmark,
  Globe,
  Filter,
  X,
  SortAsc,
  SortDesc
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import {
  conceptsApi,
  ConceptDetail,
  ConceptOccurrence,
  ConceptAssociation
} from '../lib/api';
import { ErrorPanel, parseAPIError, DataIncompleteNotice, APIErrorData, ConceptDetailSkeleton } from '../components/common';
import clsx from 'clsx';

// Enhanced type configuration with gradients
const TYPE_CONFIG: Record<string, {
  icon: React.ReactNode;
  gradient: string;
  bgGradient: string;
  lightGradient: string;
  color: string;
  label: { ar: string; en: string };
  description: { ar: string; en: string };
}> = {
  person: {
    icon: <User className="w-6 h-6" />,
    gradient: 'from-blue-500 to-indigo-600',
    bgGradient: 'from-blue-50 to-indigo-50',
    lightGradient: 'from-blue-100/50 to-indigo-100/50',
    color: 'text-blue-700',
    label: { ar: 'شخصية', en: 'Person' },
    description: { ar: 'شخصية قرآنية', en: 'Quranic figure' },
  },
  nation: {
    icon: <Users className="w-6 h-6" />,
    gradient: 'from-purple-500 to-pink-600',
    bgGradient: 'from-purple-50 to-pink-50',
    lightGradient: 'from-purple-100/50 to-pink-100/50',
    color: 'text-purple-700',
    label: { ar: 'قوم', en: 'Nation' },
    description: { ar: 'أمة أو قوم', en: 'Nation or people' },
  },
  place: {
    icon: <MapPin className="w-6 h-6" />,
    gradient: 'from-green-500 to-emerald-600',
    bgGradient: 'from-green-50 to-emerald-50',
    lightGradient: 'from-green-100/50 to-emerald-100/50',
    color: 'text-green-700',
    label: { ar: 'مكان', en: 'Place' },
    description: { ar: 'موقع جغرافي', en: 'Geographic location' },
  },
  miracle: {
    icon: <Zap className="w-6 h-6" />,
    gradient: 'from-amber-500 to-orange-600',
    bgGradient: 'from-amber-50 to-orange-50',
    lightGradient: 'from-amber-100/50 to-orange-100/50',
    color: 'text-amber-700',
    label: { ar: 'معجزة', en: 'Miracle' },
    description: { ar: 'آية ربانية', en: 'Divine sign' },
  },
  theme: {
    icon: <Heart className="w-6 h-6" />,
    gradient: 'from-rose-500 to-red-600',
    bgGradient: 'from-rose-50 to-red-50',
    lightGradient: 'from-rose-100/50 to-red-100/50',
    color: 'text-rose-700',
    label: { ar: 'موضوع', en: 'Theme' },
    description: { ar: 'موضوع قرآني', en: 'Quranic theme' },
  },
  moral_pattern: {
    icon: <TrendingUp className="w-6 h-6" />,
    gradient: 'from-indigo-500 to-violet-600',
    bgGradient: 'from-indigo-50 to-violet-50',
    lightGradient: 'from-indigo-100/50 to-violet-100/50',
    color: 'text-indigo-700',
    label: { ar: 'نمط سنني', en: 'Pattern' },
    description: { ar: 'سنة إلهية', en: 'Divine pattern' },
  },
  rhetorical: {
    icon: <BookOpen className="w-6 h-6" />,
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-50 to-teal-50',
    lightGradient: 'from-cyan-100/50 to-teal-100/50',
    color: 'text-cyan-700',
    label: { ar: 'أسلوب بلاغي', en: 'Rhetorical' },
    description: { ar: 'بلاغة قرآنية', en: 'Quranic rhetoric' },
  },
};

// Reference type configuration
const REF_TYPE_CONFIG: Record<string, {
  icon: React.ReactNode;
  label: { ar: string; en: string };
  color: string;
}> = {
  story: {
    icon: <Book className="w-4 h-4" />,
    label: { ar: 'القصص', en: 'Stories' },
    color: 'text-purple-600 bg-purple-50',
  },
  segment: {
    icon: <Layers className="w-4 h-4" />,
    label: { ar: 'مقاطع', en: 'Segments' },
    color: 'text-blue-600 bg-blue-50',
  },
  cluster: {
    icon: <Share2 className="w-4 h-4" />,
    label: { ar: 'مجموعات', en: 'Clusters' },
    color: 'text-emerald-600 bg-emerald-50',
  },
  ayah: {
    icon: <FileText className="w-4 h-4" />,
    label: { ar: 'آيات', en: 'Verses' },
    color: 'text-amber-600 bg-amber-50',
  },
};

export function ConceptDetailPage() {
  const { conceptId } = useParams<{ conceptId: string }>();
  const navigate = useNavigate();
  const { language } = useLanguageStore();
  const [concept, setConcept] = useState<ConceptDetail | null>(null);
  const [occurrences, setOccurrences] = useState<ConceptOccurrence[]>([]);
  const [associations, setAssociations] = useState<ConceptAssociation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIErrorData | null>(null);
  const [dataStatus, setDataStatus] = useState<string>('complete');
  const [retryCount, setRetryCount] = useState(0);
  const [activeTab, setActiveTab] = useState<'occurrences' | 'associations'>('occurrences');

  const isArabic = language === 'ar';

  const loadConceptData = useCallback(async () => {
    if (!conceptId) return;

    setLoading(true);
    setError(null);

    try {
      const [conceptRes, occurrencesRes, associationsRes] = await Promise.all([
        conceptsApi.getConcept(conceptId),
        conceptsApi.getConceptOccurrences(conceptId, { limit: 50 }),
        conceptsApi.getConceptAssociations(conceptId, { limit: 50 }),
      ]);

      setConcept(conceptRes.data);
      setOccurrences(occurrencesRes.data.occurrences);
      setAssociations(associationsRes.data);

      // Check for data_status in response
      const responseData = conceptRes.data as unknown as Record<string, unknown>;
      if (responseData.data_status) {
        setDataStatus(responseData.data_status as string);
      }
    } catch (err) {
      console.error('Failed to load concept:', err);
      const parsedError = parseAPIError(err);
      setError(parsedError);

      // Auto-retry once on network errors
      if (retryCount < 1 && parsedError?.code === 'network_error') {
        setRetryCount((c) => c + 1);
        setTimeout(() => loadConceptData(), 1000);
      }
    } finally {
      setLoading(false);
    }
  }, [conceptId, retryCount]);

  useEffect(() => {
    loadConceptData();
  }, [loadConceptData]);

  const handleRetry = () => {
    setRetryCount(0);
    loadConceptData();
  };

  const handleReport = () => {
    // TODO: Create verification task / bug report
    console.log('Report issue with request_id:', error?.request_id);
  };

  const handleSearchInQuran = () => {
    if (concept) {
      const searchTerm = isArabic ? concept.label_ar : concept.label_en;
      navigate(`/search?q=${encodeURIComponent(searchTerm)}&type=concept`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link
            to="/concepts"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-emerald-600 mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {isArabic ? 'العودة للمفاهيم' : 'Back to Concepts'}
          </Link>
          <ConceptDetailSkeleton />
        </div>
      </div>
    );
  }

  // Error state with ErrorPanel
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link
            to="/concepts"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-emerald-600 mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {isArabic ? 'العودة للمفاهيم' : 'Back to Concepts'}
          </Link>
          <ErrorPanel
            error={error}
            onRetry={handleRetry}
            onReport={handleReport}
          />
        </div>
      </div>
    );
  }

  if (!concept) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-16 bg-white rounded-2xl shadow-sm">
            <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">
              {isArabic ? 'المفهوم غير موجود' : 'Concept not found'}
            </h2>
            <p className="text-gray-500 mb-6">
              {isArabic ? 'قد يكون تم نقل هذا المفهوم أو حذفه' : 'This concept may have been moved or deleted'}
            </p>
            <Link
              to="/concepts"
              className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              {isArabic ? 'تصفح المفاهيم' : 'Browse Concepts'}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const config = TYPE_CONFIG[concept.type] || TYPE_CONFIG.theme;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Header with Gradient */}
      <div className={clsx('relative overflow-hidden bg-gradient-to-br', config.gradient)}>
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }} />
        </div>

        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
          {/* Back Link */}
          <Link
            to="/concepts"
            className="inline-flex items-center gap-2 text-white/80 hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {isArabic ? 'العودة للمفاهيم' : 'Back to Concepts'}
          </Link>

          {/* Main Header Content */}
          <div className="flex flex-col md:flex-row md:items-start gap-6">
            {/* Icon */}
            <div className="p-4 bg-white/20 rounded-2xl backdrop-blur-sm">
              {config.icon}
            </div>

            {/* Title and Info */}
            <div className="flex-1 text-white">
              <div className="flex items-center flex-wrap gap-3 mb-2">
                <h1 className="text-3xl md:text-4xl font-bold">
                  {isArabic ? concept.label_ar : concept.label_en}
                </h1>
              </div>

              {/* Type description in current language only - Pure language mode */}
              <p className="text-xl text-white/80 mb-4">
                {isArabic ? config.description.ar : config.description.en}
              </p>

              {/* Type Badge */}
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 rounded-full text-sm">
                {isArabic ? config.label.ar : config.label.en}
              </span>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-2">
              <button
                onClick={handleSearchInQuran}
                className="flex items-center gap-2 px-4 py-2.5 bg-white text-gray-800 rounded-xl hover:bg-white/90 transition-colors font-medium shadow-lg"
              >
                <Search className="w-4 h-4" />
                {isArabic ? 'بحث في القرآن' : 'Search in Quran'}
              </button>
              <button
                className="flex items-center gap-2 px-4 py-2.5 bg-white/20 text-white rounded-xl hover:bg-white/30 transition-colors"
              >
                <Bookmark className="w-4 h-4" />
                {isArabic ? 'حفظ' : 'Bookmark'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Data Incomplete Notice */}
        {dataStatus === 'incomplete' && (
          <DataIncompleteNotice
            message="Some information for this concept is still being verified."
            messageAr="بعض المعلومات لهذا المفهوم لا تزال قيد التحقق."
            className="mb-6"
          />
        )}

        {/* Stats and Description Card */}
        <div className={clsx('rounded-2xl p-6 mb-8 border', `bg-gradient-to-br ${config.lightGradient}`, 'border-gray-100')}>
          <div className="grid grid-cols-3 gap-6 mb-6">
            {/* Stats */}
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{occurrences.length}</div>
              <div className="text-sm text-gray-500">{isArabic ? 'مواضع' : 'Occurrences'}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{associations.length}</div>
              <div className="text-sm text-gray-500">{isArabic ? 'مفاهيم مرتبطة' : 'Related'}</div>
            </div>
            <div className="text-center">
              <div className={clsx('inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium', config.color, config.bgGradient)}>
                {isArabic ? config.label.ar : config.label.en}
              </div>
              <div className="text-sm text-gray-500 mt-1">{isArabic ? 'التصنيف' : 'Category'}</div>
            </div>
          </div>

          {/* Description */}
          {(concept.description_ar || concept.description_en) && (
            <div className="border-t border-gray-200/50 pt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                {isArabic ? 'الوصف' : 'Description'}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {isArabic ? concept.description_ar : concept.description_en}
              </p>
            </div>
          )}

          {/* Aliases */}
          {((isArabic && concept.aliases_ar?.length) || (!isArabic && concept.aliases_en?.length)) && (
            <div className="border-t border-gray-200/50 pt-4 mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                {isArabic ? 'أسماء أخرى' : 'Also known as'}
              </h3>
              <div className="flex flex-wrap gap-2">
                {(isArabic ? concept.aliases_ar : concept.aliases_en)?.map((alias, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-white rounded-full text-sm text-gray-700 border border-gray-200"
                  >
                    {alias}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="border-b border-gray-100">
            <div className="flex">
              <button
                onClick={() => setActiveTab('occurrences')}
                className={clsx(
                  'flex-1 px-6 py-4 font-medium transition-colors flex items-center justify-center gap-2',
                  activeTab === 'occurrences'
                    ? `${config.color} border-b-2 border-current bg-gradient-to-t ${config.lightGradient}`
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                )}
              >
                <Eye className="w-4 h-4" />
                {isArabic ? `المواضع (${occurrences.length})` : `Occurrences (${occurrences.length})`}
              </button>
              <button
                onClick={() => setActiveTab('associations')}
                className={clsx(
                  'flex-1 px-6 py-4 font-medium transition-colors flex items-center justify-center gap-2',
                  activeTab === 'associations'
                    ? `${config.color} border-b-2 border-current bg-gradient-to-t ${config.lightGradient}`
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                )}
              >
                <Link2 className="w-4 h-4" />
                {isArabic ? `المفاهيم المرتبطة (${associations.length})` : `Related Concepts (${associations.length})`}
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'occurrences' ? (
              <OccurrencesTab
                occurrences={occurrences}
                language={language}
                conceptId={conceptId}
              />
            ) : (
              <AssociationsTab associations={associations} language={language} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Sort options
type SortOption = 'sura' | 'sura_desc' | 'type';

// Occurrences Tab Component with enhanced UI/UX
function OccurrencesTab({
  occurrences,
  language,
  conceptId
}: {
  occurrences: ConceptOccurrence[];
  language: 'ar' | 'en';
  conceptId?: string;
}) {
  const isArabic = language === 'ar';
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('sura');
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [filterRefType, setFilterRefType] = useState<string | null>(null);

  // Toggle expanded state for an occurrence
  const toggleExpanded = useCallback((id: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setExpandedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  // Get unique ref types for filter
  const refTypes = useMemo(() => {
    const types = new Set(occurrences.map(o => o.ref_type));
    return Array.from(types);
  }, [occurrences]);

  // Filter and sort occurrences
  const filteredOccurrences = useMemo(() => {
    let filtered = [...occurrences];

    // Apply ref_type filter
    if (filterRefType) {
      filtered = filtered.filter(o => o.ref_type === filterRefType);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(o => {
        const contextAr = o.context_ar?.toLowerCase() || '';
        const contextEn = o.context_en?.toLowerCase() || '';
        const verseRef = o.verse_reference?.toLowerCase() || '';
        const refId = o.ref_id?.toLowerCase() || '';
        return contextAr.includes(query) || contextEn.includes(query) ||
               verseRef.includes(query) || refId.includes(query);
      });
    }

    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'sura') {
        const suraA = a.sura_no || 999;
        const suraB = b.sura_no || 999;
        if (suraA !== suraB) return suraA - suraB;
        return (a.ayah_start || 0) - (b.ayah_start || 0);
      } else if (sortBy === 'sura_desc') {
        const suraA = a.sura_no || 0;
        const suraB = b.sura_no || 0;
        if (suraA !== suraB) return suraB - suraA;
        return (b.ayah_start || 0) - (a.ayah_start || 0);
      } else {
        return a.ref_type.localeCompare(b.ref_type);
      }
    });

    return filtered;
  }, [occurrences, searchQuery, sortBy, filterRefType]);

  // Group occurrences by ref_type
  const grouped = useMemo(() => {
    return filteredOccurrences.reduce((acc, occ) => {
      if (!acc[occ.ref_type]) {
        acc[occ.ref_type] = [];
      }
      acc[occ.ref_type].push(occ);
      return acc;
    }, {} as Record<string, ConceptOccurrence[]>);
  }, [filteredOccurrences]);

  if (occurrences.length === 0) {
    return (
      <div className="text-center py-12">
        <Eye className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-700 mb-2">
          {isArabic ? 'لا توجد مواضع مسجلة' : 'No occurrences recorded'}
        </h3>
        <p className="text-gray-500">
          {isArabic
            ? 'لم يتم تسجيل مواضع ذكر هذا المفهوم بعد'
            : 'Occurrences for this concept have not been recorded yet'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search & Filter Bar */}
      <div className={clsx(
        "flex flex-col sm:flex-row gap-3 p-4 bg-gray-50 rounded-xl border border-gray-100",
        isArabic && "sm:flex-row-reverse"
      )}>
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className={clsx(
            "absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400",
            isArabic ? "right-3" : "left-3"
          )} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={isArabic ? 'ابحث في المواضع...' : 'Search occurrences...'}
            className={clsx(
              "w-full py-2.5 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm",
              isArabic ? "pr-10 pl-3 text-right" : "pl-10 pr-3"
            )}
            dir={isArabic ? 'rtl' : 'ltr'}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className={clsx(
                "absolute top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600",
                isArabic ? "left-2" : "right-2"
              )}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Filter by Type */}
        <div className="relative">
          <select
            value={filterRefType || ''}
            onChange={(e) => setFilterRefType(e.target.value || null)}
            className={clsx(
              "py-2.5 px-4 border border-gray-200 rounded-lg bg-white text-sm appearance-none cursor-pointer min-w-[140px]",
              isArabic && "text-right"
            )}
            dir={isArabic ? 'rtl' : 'ltr'}
          >
            <option value="">{isArabic ? 'كل الأنواع' : 'All types'}</option>
            {refTypes.map(type => {
              const config = REF_TYPE_CONFIG[type];
              return (
                <option key={type} value={type}>
                  {config?.label[isArabic ? 'ar' : 'en'] || type}
                </option>
              );
            })}
          </select>
          <Filter className={clsx(
            "absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none",
            isArabic ? "left-3" : "right-3"
          )} />
        </div>

        {/* Sort Button */}
        <button
          onClick={() => setSortBy(prev => prev === 'sura' ? 'sura_desc' : prev === 'sura_desc' ? 'type' : 'sura')}
          className={clsx(
            "flex items-center gap-2 py-2.5 px-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 text-sm transition-colors",
            isArabic && "flex-row-reverse"
          )}
        >
          {sortBy === 'sura_desc' ? <SortDesc className="w-4 h-4 text-emerald-600" /> : <SortAsc className="w-4 h-4 text-emerald-600" />}
          <span className="text-gray-600">
            {sortBy === 'sura' ? (isArabic ? 'سورة ↑' : 'Sura ↑') :
             sortBy === 'sura_desc' ? (isArabic ? 'سورة ↓' : 'Sura ↓') :
             (isArabic ? 'النوع' : 'Type')}
          </span>
        </button>
      </div>

      {/* Results Count */}
      <div className={clsx(
        "flex items-center gap-2 text-sm text-gray-500",
        isArabic && "flex-row-reverse"
      )}>
        <span>
          {isArabic
            ? `عرض ${filteredOccurrences.length} من ${occurrences.length} موضع`
            : `Showing ${filteredOccurrences.length} of ${occurrences.length} occurrences`}
        </span>
        {(searchQuery || filterRefType) && (
          <button
            onClick={() => { setSearchQuery(''); setFilterRefType(null); }}
            className="text-emerald-600 hover:text-emerald-700 font-medium"
          >
            {isArabic ? 'مسح الفلتر' : 'Clear filters'}
          </button>
        )}
      </div>

      {/* No Results */}
      {filteredOccurrences.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Search className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p>{isArabic ? 'لا توجد نتائج مطابقة' : 'No matching results'}</p>
        </div>
      )}

      {/* Grouped Occurrences with Zebra Striping */}
      <div className="space-y-8">
        {Object.entries(grouped).map(([refType, items]) => {
          const refConfig = REF_TYPE_CONFIG[refType];
          return (
            <div key={refType}>
              <div className={clsx(
                "flex items-center gap-3 mb-4",
                isArabic && "flex-row-reverse"
              )}>
                <div className={clsx('p-2 rounded-lg', refConfig?.color || 'text-gray-600 bg-gray-50')}>
                  {refConfig?.icon || <FileText className="w-4 h-4" />}
                </div>
                <h3 className="font-semibold text-gray-900">
                  {refConfig?.label[isArabic ? 'ar' : 'en'] || refType}
                </h3>
                <span className="text-sm text-gray-400">({items.length})</span>
              </div>

              {/* List with Zebra Striping */}
              <div className="rounded-xl border border-gray-200 overflow-hidden">
                {items.map((occ, index) => (
                  <OccurrenceItem
                    key={occ.id}
                    occurrence={occ}
                    language={language}
                    conceptId={conceptId}
                    isExpanded={expandedIds.has(occ.id)}
                    onToggleExpand={(e) => toggleExpanded(occ.id, e)}
                    isEven={index % 2 === 0}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function OccurrenceItem({
  occurrence,
  language,
  conceptId,
  isExpanded,
  onToggleExpand,
  isEven
}: {
  occurrence: ConceptOccurrence;
  language: 'ar' | 'en';
  conceptId?: string;
  isExpanded: boolean;
  onToggleExpand: (e: React.MouseEvent) => void;
  isEven: boolean;
}) {
  const isArabic = language === 'ar';

  // Determine link based on ref_type
  let link: string | null = null;
  if (occurrence.ref_type === 'story' && occurrence.ref_id) {
    link = `/stories/${occurrence.ref_id}`;
  } else if (occurrence.ref_type === 'cluster' && occurrence.ref_id) {
    link = `/story-atlas/${occurrence.ref_id}`;
  } else if (occurrence.sura_no && occurrence.ayah_start) {
    const params = new URLSearchParams();
    if (occurrence.page_no) {
      params.set('page', occurrence.page_no.toString());
    }
    params.set('aya', occurrence.ayah_start.toString());
    if (conceptId) {
      params.set('concept', conceptId);
    }
    link = `/quran/${occurrence.sura_no}?${params.toString()}`;
  } else if (occurrence.sura_no) {
    link = `/quran/${occurrence.sura_no}`;
  }

  // Get context text (verse snippet)
  const contextText = isArabic ? occurrence.context_ar : occurrence.context_en;
  const hasExpandableContent = contextText && contextText.length > 100;

  return (
    <div
      className={clsx(
        "border-b border-gray-100 last:border-b-0 transition-colors",
        // Zebra striping
        isEven ? "bg-white" : "bg-gray-50/50",
        // Hover state
        "hover:bg-emerald-50/50"
      )}
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Main Row */}
      <div className={clsx(
        "flex items-center gap-3 p-4",
        isArabic && "flex-row-reverse"
      )}>
        {/* Expand Button (if expandable content) */}
        <button
          onClick={onToggleExpand}
          className={clsx(
            "flex-shrink-0 p-1.5 rounded-lg transition-all",
            hasExpandableContent
              ? "hover:bg-gray-200 text-gray-500 hover:text-gray-700 cursor-pointer"
              : "text-transparent cursor-default"
          )}
          disabled={!hasExpandableContent}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          <ChevronDown className={clsx(
            "w-4 h-4 transition-transform duration-200",
            isExpanded && "rotate-180"
          )} />
        </button>

        {/* Verse Reference Badge */}
        <div className={clsx(
          "flex-shrink-0 text-sm font-bold px-3 py-1.5 rounded-lg min-w-[70px] text-center",
          "bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-700 border border-emerald-100"
        )}>
          {occurrence.verse_reference || occurrence.ref_id || '-'}
        </div>

        {/* Content Area */}
        <div className={clsx(
          "flex-1 min-w-0",
          isArabic ? "text-right" : "text-left"
        )}>
          {/* Verse Text Snippet - Truncated */}
          {contextText ? (
            <p className={clsx(
              "text-gray-700 leading-relaxed",
              isArabic ? "font-arabic text-base" : "text-sm",
              !isExpanded && "line-clamp-1"
            )}>
              {contextText}
            </p>
          ) : (
            <p className="text-sm text-gray-400 italic">
              {isArabic ? 'اضغط للتفاصيل' : 'Click for details'}
            </p>
          )}
        </div>

        {/* Link Arrow */}
        {link && (
          <Link
            to={link}
            className={clsx(
              "flex-shrink-0 p-2 rounded-lg bg-emerald-100 text-emerald-700 hover:bg-emerald-200 transition-colors",
              isArabic && "rotate-180"
            )}
            onClick={(e) => e.stopPropagation()}
          >
            <ChevronRight className="w-4 h-4" />
          </Link>
        )}
      </div>

      {/* Expanded Details Panel */}
      {isExpanded && contextText && (
        <div className={clsx(
          "px-4 pb-4 pt-0",
          isArabic ? "pr-14" : "pl-14"
        )}>
          <div className={clsx(
            "p-4 rounded-xl border border-gray-100",
            "bg-gradient-to-br from-white to-gray-50"
          )}>
            {/* Full Verse Text */}
            <p className={clsx(
              "text-gray-800 leading-relaxed mb-4",
              isArabic ? "font-arabic text-lg" : "text-sm"
            )}>
              {contextText}
            </p>

            {/* Metadata Row */}
            <div className={clsx(
              "flex flex-wrap gap-3 pt-3 border-t border-gray-100",
              isArabic && "flex-row-reverse"
            )}>
              {occurrence.sura_no && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {isArabic ? `سورة ${occurrence.sura_no}` : `Sura ${occurrence.sura_no}`}
                </span>
              )}
              {occurrence.ayah_start && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {isArabic ? `آية ${occurrence.ayah_start}` : `Ayah ${occurrence.ayah_start}`}
                </span>
              )}
              {occurrence.page_no && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {isArabic ? `صفحة ${occurrence.page_no}` : `Page ${occurrence.page_no}`}
                </span>
              )}

              {/* Read Full Verse Link */}
              {link && (
                <Link
                  to={link}
                  className={clsx(
                    "flex items-center gap-1.5 text-xs text-emerald-600 hover:text-emerald-700 font-medium",
                    isArabic && "flex-row-reverse mr-auto"
                  )}
                >
                  <ExternalLink className="w-3 h-3" />
                  {isArabic ? 'قراءة الآية كاملة' : 'Read full verse'}
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Associations Tab Component
function AssociationsTab({
  associations,
  language
}: {
  associations: ConceptAssociation[];
  language: 'ar' | 'en';
}) {
  const isArabic = language === 'ar';

  if (associations.length === 0) {
    return (
      <div className="text-center py-12">
        <Link2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-700 mb-2">
          {isArabic ? 'لا توجد مفاهيم مرتبطة' : 'No related concepts'}
        </h3>
        <p className="text-gray-500">
          {isArabic
            ? 'لم يتم ربط هذا المفهوم بمفاهيم أخرى بعد'
            : 'This concept has not been linked to other concepts yet'}
        </p>
      </div>
    );
  }

  // Group by relation type
  const grouped = associations.reduce((acc, assoc) => {
    if (!acc[assoc.relation_type]) {
      acc[assoc.relation_type] = [];
    }
    acc[assoc.relation_type].push(assoc);
    return acc;
  }, {} as Record<string, ConceptAssociation[]>);

  return (
    <div className="space-y-8">
      {Object.entries(grouped).map(([relationType, items]) => (
        <div key={relationType}>
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Globe className="w-4 h-4 text-gray-400" />
            {items[0] ? (isArabic ? items[0].relation_label_ar : items[0].relation_label_en) : relationType}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((assoc) => {
              const config = TYPE_CONFIG[assoc.other_concept_type];
              return (
                <Link
                  key={assoc.id}
                  to={`/concepts/${assoc.other_concept_id}`}
                  className={clsx(
                    'p-4 rounded-xl border transition-all hover:shadow-lg hover:-translate-y-1 flex items-center gap-4 group',
                    `bg-gradient-to-br ${config?.lightGradient || 'from-gray-50 to-gray-100'}`,
                    'border-gray-100 hover:border-gray-200'
                  )}
                >
                  <div className={clsx(
                    'p-2 rounded-lg bg-gradient-to-br text-white',
                    config?.gradient || 'from-gray-500 to-gray-600'
                  )}>
                    {config?.icon || <BookOpen className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    {/* Primary label only - Pure language mode */}
                    <p className={clsx(
                      "font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors truncate",
                      isArabic && "font-arabic"
                    )}>
                      {isArabic
                        ? (assoc.other_concept_label_ar || assoc.other_concept_label_en)
                        : (assoc.other_concept_label_en || assoc.other_concept_label_ar)}
                    </p>
                    {/* Type badge instead of secondary language */}
                    <p className="text-xs text-gray-500 truncate mt-0.5">
                      {isArabic
                        ? (TYPE_CONFIG[assoc.other_concept_type]?.label.ar || assoc.other_concept_type)
                        : (TYPE_CONFIG[assoc.other_concept_type]?.label.en || assoc.other_concept_type)}
                    </p>
                  </div>
                  {assoc.has_sufficient_evidence && (
                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
