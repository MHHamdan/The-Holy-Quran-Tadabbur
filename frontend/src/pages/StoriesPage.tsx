import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Book, Users, ArrowRight } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t, translateCategory, translateTheme, translateFigure } from '../i18n/translations';
import { storiesApi, Story } from '../lib/api';
import clsx from 'clsx';

const CATEGORIES = [
  { id: 'all', labelAr: 'الكل', labelEn: 'All' },
  { id: 'prophet', labelAr: 'قصص الأنبياء', labelEn: 'Prophets' },
  { id: 'nation', labelAr: 'قصص الأمم', labelEn: 'Nations' },
  { id: 'righteous', labelAr: 'الصالحين', labelEn: 'Righteous' },
  { id: 'parable', labelAr: 'الأمثال', labelEn: 'Parables' },
  { id: 'historical', labelAr: 'تاريخية', labelEn: 'Historical' },
];

export function StoriesPage() {
  const { language } = useLanguageStore();
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    loadStories();
  }, [selectedCategory]);

  async function loadStories() {
    setLoading(true);
    try {
      const category = selectedCategory === 'all' ? undefined : selectedCategory;
      const response = await storiesApi.listStories(category);
      setStories(response.data);
    } catch (error) {
      console.error('Failed to load stories:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {t('stories_title', language)}
        </h1>
        <p className="text-gray-600">{t('stories_subtitle', language)}</p>
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
            {language === 'ar' ? cat.labelAr : cat.labelEn}
          </button>
        ))}
      </div>

      {/* Stories Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">{t('loading', language)}</p>
        </div>
      ) : stories.length === 0 ? (
        <div className="text-center py-12 card">
          <Book className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {language === 'ar'
              ? 'لا توجد قصص متاحة حالياً'
              : 'No stories available yet'}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            {language === 'ar'
              ? 'قم بتشغيل seed_stories.py لإضافة البيانات'
              : 'Run seed_stories.py to add data'}
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stories.map((story) => (
            <StoryCard key={story.id} story={story} language={language} />
          ))}
        </div>
      )}
    </div>
  );
}

function StoryCard({ story, language }: { story: Story; language: 'ar' | 'en' }) {
  const name = language === 'ar' ? story.name_ar : story.name_en;
  const summary = language === 'ar' ? story.summary_ar : story.summary_en;

  return (
    <Link
      to={`/stories/${story.id}`}
      className="card hover:shadow-lg transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
          <Book className="w-5 h-5 text-primary-600" />
        </div>
        <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
          {translateCategory(story.category, language)}
        </span>
      </div>

      <h3 className="text-lg font-semibold mb-2 group-hover:text-primary-600 transition-colors">
        {name}
      </h3>

      {summary && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">{summary}</p>
      )}

      {/* Figures */}
      {story.main_figures && story.main_figures.length > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500">
            {story.main_figures.slice(0, 3).map(f => translateFigure(f, language)).join(language === 'ar' ? '، ' : ', ')}
            {story.main_figures.length > 3 && '...'}
          </span>
        </div>
      )}

      {/* Themes */}
      {story.themes && story.themes.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
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

      <div className="flex items-center text-primary-600 text-sm font-medium">
        {language === 'ar' ? 'عرض القصة' : 'View Story'}
        <ArrowRight className={`w-4 h-4 ${language === 'ar' ? 'mr-1 group-hover:-translate-x-1' : 'ml-1 group-hover:translate-x-1'} transition-transform`} />
      </div>
    </Link>
  );
}
