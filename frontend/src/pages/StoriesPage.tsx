import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Book, Users, ArrowRight, Search, Crown, Globe, Scroll,
  Landmark, Eye, Heart, ChevronRight, Baby, GraduationCap,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t, translateCategory, translateTheme, translateFigure } from '../i18n/translations';
import { storiesApi, Story } from '../lib/api';
import clsx from 'clsx';

const CATEGORY_META: Record<string, {
  icon: typeof Book;
  color: string;
  bgColor: string;
  borderColor: string;
  descKey: string;
}> = {
  prophet: {
    icon: Crown,
    color: 'text-amber-700',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    descKey: 'category_prophets_desc',
  },
  parable: {
    icon: Scroll,
    color: 'text-emerald-700',
    bgColor: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    descKey: 'category_parables_desc',
  },
  nation: {
    icon: Globe,
    color: 'text-blue-700',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    descKey: 'category_nations_desc',
  },
  historical: {
    icon: Landmark,
    color: 'text-purple-700',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    descKey: 'category_historical_desc',
  },
  unseen: {
    icon: Eye,
    color: 'text-indigo-700',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    descKey: 'category_unseen_desc',
  },
  righteous: {
    icon: Heart,
    color: 'text-rose-700',
    bgColor: 'bg-rose-50',
    borderColor: 'border-rose-200',
    descKey: 'category_righteous_desc',
  },
};

const CATEGORIES = [
  { id: 'all', labelAr: 'الكل', labelEn: 'All' },
  { id: 'prophet', labelAr: 'الأنبياء', labelEn: 'Prophets' },
  { id: 'parable', labelAr: 'أمثال وعبر', labelEn: 'Parables' },
  { id: 'nation', labelAr: 'الأمم', labelEn: 'Nations' },
  { id: 'historical', labelAr: 'تاريخية', labelEn: 'Historical' },
  { id: 'unseen', labelAr: 'الغيبيات', labelEn: 'Unseen' },
  { id: 'righteous', labelAr: 'الصالحين', labelEn: 'Righteous' },
];

import type { AudienceLevel } from '../types/quranStory';

export function StoriesPage() {
  const { language } = useLanguageStore();
  const [allStories, setAllStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [audienceFilter, setAudienceFilter] = useState<AudienceLevel | 'all'>('all');
  const [richStoryIds, setRichStoryIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadAllStories();
    import('../data/quranStories').then(m =>
      setRichStoryIds(new Set(m.QURAN_STORIES_FIRST_BATCH.map((s) => s.storyId)))
    );
  }, []);

  async function loadAllStories() {
    setLoading(true);
    try {
      const response = await storiesApi.listStories();
      setAllStories(response.data);
    } catch (error) {
      console.error('Failed to load stories:', error);
    } finally {
      setLoading(false);
    }
  }

  const filteredStories = useMemo(() => {
    let stories = allStories;

    if (selectedCategory !== 'all') {
      stories = stories.filter((s) => s.category === selectedCategory);
    }

    if (audienceFilter !== 'all') {
      stories = stories.filter((s) => richStoryIds.has(s.id));
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      stories = stories.filter((s) => {
        const name = (language === 'ar' ? s.name_ar : s.name_en).toLowerCase();
        const summary = ((language === 'ar' ? s.summary_ar : s.summary_en) || '').toLowerCase();
        const figures = (s.main_figures || []).map((f) => f.toLowerCase()).join(' ');
        const figuresTranslated = (s.main_figures || []).map((f) => translateFigure(f, language).toLowerCase()).join(' ');
        return name.includes(q) || summary.includes(q) || figures.includes(q) || figuresTranslated.includes(q);
      });
    }

    return stories;
  }, [allStories, selectedCategory, audienceFilter, searchQuery, language, richStoryIds]);

  const storiesByCategory = useMemo(() => {
    const grouped: Record<string, Story[]> = {};
    for (const cat of CATEGORIES) {
      if (cat.id === 'all') continue;
      grouped[cat.id] = allStories.filter((s) => s.category === cat.id);
    }
    return grouped;
  }, [allStories]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const s of allStories) {
      counts[s.category] = (counts[s.category] || 0) + 1;
    }
    return counts;
  }, [allStories]);

  const showGroupedView = selectedCategory === 'all' && !searchQuery.trim() && audienceFilter === 'all';

  const isRtl = language === 'ar';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <h1 className={clsx('text-3xl font-bold text-gray-900 mb-2', isRtl && 'font-arabic')}>
          {t('stories_title', language)}
        </h1>
        <p className={clsx('text-gray-600', isRtl && 'font-arabic')}>
          {t('stories_subtitle', language)}
          {!loading && (
            <span className="text-gray-400 ms-2">
              ({allStories.length} {t('stories_count', language)})
            </span>
          )}
        </p>
      </div>

      {/* Search Bar */}
      <div className="relative mb-6">
        <Search className={`absolute top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 ${isRtl ? 'right-3' : 'left-3'}`} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('stories_search_placeholder', language)}
          className={`w-full py-3 border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${isRtl ? 'pr-10 pl-4' : 'pl-10 pr-4'}`}
          dir={isRtl ? 'rtl' : 'ltr'}
        />
      </div>

      {/* Audience Level Filter */}
      <div className={clsx('flex items-center gap-3 mb-4', isRtl && 'flex-row-reverse')}>
        <span className={clsx('text-sm font-medium text-gray-500', isRtl && 'font-arabic')}>
          {isRtl ? 'المستوى:' : 'Level:'}
        </span>
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          {(
            [
              { id: 'all' as const, labelAr: 'الكل', labelEn: 'All', icon: null },
              { id: 'kids' as const, labelAr: 'للأطفال', labelEn: 'Kids', icon: Baby },
              { id: 'adults' as const, labelAr: 'للكبار', labelEn: 'Adults', icon: GraduationCap },
            ] satisfies { id: AudienceLevel | 'all'; labelAr: string; labelEn: string; icon: typeof Baby | null }[]
          ).map(({ id, labelAr, labelEn, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setAudienceFilter(id)}
              className={clsx(
                'flex items-center gap-1.5 px-4 py-2 text-sm font-medium transition-all',
                audienceFilter === id
                  ? id === 'kids'
                    ? 'bg-amber-500 text-white'
                    : id === 'adults'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-800 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              )}
            >
              {Icon && <Icon className="w-4 h-4" />}
              {language === 'ar' ? labelAr : labelEn}
            </button>
          ))}
        </div>
        {audienceFilter !== 'all' && (
          <span className="text-xs text-gray-400">
            {language === 'ar'
              ? `${richStoryIds.size} قصة بمحتوى منقّح`
              : `${richStoryIds.size} stories with enriched content`}
          </span>
        )}
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-8">
        {CATEGORIES.map((cat) => {
          const meta = CATEGORY_META[cat.id];
          const count = categoryCounts[cat.id] || 0;
          const isSelected = selectedCategory === cat.id;
          const Icon = meta?.icon;

          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all',
                isSelected
                  ? cat.id === 'all'
                    ? 'bg-primary-600 text-white shadow-sm'
                    : `${meta?.bgColor} ${meta?.color} ring-2 ${meta?.borderColor} ring-offset-1`
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {Icon && <Icon className="w-4 h-4" />}
              {language === 'ar' ? cat.labelAr : cat.labelEn}
              {cat.id !== 'all' && count > 0 && (
                <span className={clsx(
                  'text-xs px-1.5 py-0.5 rounded-full',
                  isSelected ? 'bg-white/20' : 'bg-gray-200 text-gray-500'
                )}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">{t('loading', language)}</p>
        </div>
      ) : allStories.length === 0 ? (
        <div className="text-center py-12 card">
          <Book className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {language === 'ar'
              ? 'لا توجد قصص متاحة حالياً'
              : 'No stories available yet'}
          </p>
        </div>
      ) : showGroupedView ? (
        /* Grouped by Category View */
        <div className="space-y-10">
          {CATEGORIES.filter((c) => c.id !== 'all').map((cat) => {
            const stories = storiesByCategory[cat.id] || [];
            if (stories.length === 0) return null;
            const meta = CATEGORY_META[cat.id];
            const Icon = meta?.icon || Book;

            return (
              <section key={cat.id}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${meta?.bgColor} rounded-lg flex items-center justify-center`}>
                      <Icon className={`w-5 h-5 ${meta?.color}`} />
                    </div>
                    <div>
                      <h2 className={clsx('text-xl font-bold text-gray-900', isRtl && 'font-arabic')}>
                        {isRtl ? cat.labelAr : cat.labelEn}
                      </h2>
                      <p className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
                        {t(meta?.descKey || '', language)}
                        <span className="mx-1">·</span>
                        {stories.length} {t('stories_count', language)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedCategory(cat.id)}
                    className={clsx(`flex items-center gap-1 text-sm font-medium ${meta?.color} hover:underline`, isRtl && 'flex-row-reverse font-arabic')}
                  >
                    {t('stories_view_all', language)}
                    <ChevronRight className={`w-4 h-4 ${isRtl ? 'rotate-180' : ''}`} />
                  </button>
                </div>

                {/* Horizontal scroll on mobile, grid on desktop */}
                <div className="flex gap-4 overflow-x-auto pb-2 snap-x snap-mandatory md:grid md:grid-cols-3 lg:grid-cols-4 md:overflow-visible">
                  {stories.slice(0, 8).map((story) => (
                    <div key={story.id} className="min-w-[280px] snap-start md:min-w-0">
                      <StoryCard story={story} language={language} isRich={richStoryIds.has(story.id)} />
                    </div>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      ) : (
        /* Filtered Grid View */
        <>
          {filteredStories.length === 0 ? (
            <div className="text-center py-12 card">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {language === 'ar'
                  ? 'لا توجد نتائج مطابقة'
                  : 'No matching stories found'}
              </p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredStories.map((story) => (
                <StoryCard key={story.id} story={story} language={language} isRich={richStoryIds.has(story.id)} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function StoryCard({ story, language, isRich }: { story: Story; language: 'ar' | 'en'; isRich?: boolean }) {
  const isRtl = language === 'ar';
  const name = isRtl ? story.name_ar : story.name_en;
  const summary = isRtl ? story.summary_ar : story.summary_en;
  const meta = CATEGORY_META[story.category];
  const Icon = meta?.icon || Book;

  return (
    <Link
      to={`/stories/${story.id}`}
      className="card hover:shadow-lg transition-all group h-full flex flex-col"
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 ${meta?.bgColor || 'bg-primary-100'} rounded-lg flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${meta?.color || 'text-primary-600'}`} />
        </div>
        <div className="flex items-center gap-1.5">
          {isRich && (
            <span className="flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full bg-emerald-50 text-emerald-700">
              <GraduationCap className="w-3 h-3" />
              {language === 'ar' ? 'محتوى منقّح' : 'Enriched'}
            </span>
          )}
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${meta?.bgColor || 'bg-gray-100'} ${meta?.color || 'text-gray-600'}`}>
            {translateCategory(story.category, language)}
          </span>
        </div>
      </div>

      <h3 className={clsx('text-lg font-semibold mb-2 group-hover:text-primary-600 transition-colors', isRtl && 'font-arabic text-right')}>
        {name}
      </h3>

      {summary && (
        <p className={clsx('text-gray-600 text-sm mb-3 line-clamp-2 flex-grow', isRtl && 'font-arabic text-right')}>{summary}</p>
      )}

      {/* Figures */}
      {story.main_figures && story.main_figures.length > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <div className="flex flex-wrap gap-1">
            {story.main_figures.slice(0, 3).map((f) => (
              <span key={f} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                {translateFigure(f, language)}
              </span>
            ))}
            {story.main_figures.length > 3 && (
              <span className="text-xs text-gray-400">+{story.main_figures.length - 3}</span>
            )}
          </div>
        </div>
      )}

      {/* Themes */}
      {story.themes && story.themes.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {story.themes.slice(0, 3).map((theme) => (
            <span
              key={theme}
              className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded"
            >
              {translateTheme(theme, language)}
            </span>
          ))}
        </div>
      )}

      {/* Footer stats */}
      <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-100">
        {story.suras_mentioned && story.suras_mentioned.length > 0 && (
          <span className={clsx('text-xs text-gray-400', isRtl && 'font-arabic')}>
            {story.suras_mentioned.length} {t('stories_surahs', language)}
          </span>
        )}
        <div className={clsx('flex items-center text-primary-600 text-sm font-medium', isRtl && 'flex-row-reverse font-arabic')}>
          {isRtl ? 'عرض القصة' : 'View Story'}
          <ArrowRight className={clsx('w-4 h-4 ms-1 transition-transform', isRtl ? 'rotate-180 group-hover:-translate-x-1' : 'group-hover:translate-x-1')} />
        </div>
      </div>
    </Link>
  );
}
