import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Tag, ArrowRight, Layers, BookMarked } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { themesApi, QuranicTheme, ThemeCategory } from '../lib/api';
import clsx from 'clsx';

export function ThemesPage() {
  const { language } = useLanguageStore();
  const [themes, setThemes] = useState<QuranicTheme[]>([]);
  const [categories, setCategories] = useState<ThemeCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadThemes();
  }, [selectedCategory]);

  async function loadCategories() {
    try {
      const response = await themesApi.getCategories();
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  }

  async function loadThemes() {
    setLoading(true);
    try {
      const params = selectedCategory === 'all'
        ? { parent_only: true }
        : { category: selectedCategory };
      const response = await themesApi.listThemes(params);
      setThemes(response.data.themes);
    } catch (error) {
      console.error('Failed to load themes:', error);
    } finally {
      setLoading(false);
    }
  }

  const allCategory = {
    category: 'all',
    label_ar: 'الكل',
    label_en: 'All',
    theme_count: categories.reduce((acc, c) => acc + c.theme_count, 0),
    order: 0,
  };

  const allCategories = [allCategory, ...categories];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {language === 'ar' ? 'المحاور القرآنية' : 'Quranic Themes'}
        </h1>
        <p className="text-gray-600">
          {language === 'ar'
            ? 'استكشف الموضوعات الأساسية في القرآن الكريم - مصنفة وفق المنهج السني'
            : 'Explore the foundational themes of the Quran - classified following Sunni methodology'}
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-8">
        {allCategories.map((cat) => (
          <button
            key={cat.category}
            onClick={() => setSelectedCategory(cat.category)}
            className={clsx(
              'px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2',
              selectedCategory === cat.category
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            <span>{language === 'ar' ? cat.label_ar : cat.label_en}</span>
            <span className="text-xs opacity-75">({cat.theme_count})</span>
          </button>
        ))}
      </div>

      {/* Themes Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">{t('loading', language)}</p>
        </div>
      ) : themes.length === 0 ? (
        <div className="text-center py-12 card">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {language === 'ar'
              ? 'لا توجد محاور متاحة حالياً'
              : 'No themes available yet'}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            {language === 'ar'
              ? 'قم بتشغيل seed_themes.py لإضافة البيانات'
              : 'Run seed_themes.py to add data'}
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {themes.map((theme) => (
            <ThemeCard key={theme.id} theme={theme} language={language} />
          ))}
        </div>
      )}
    </div>
  );
}

function ThemeCard({ theme, language }: { theme: QuranicTheme; language: 'ar' | 'en' }) {
  const title = language === 'ar' ? theme.title_ar : theme.title_en;
  const categoryLabel = language === 'ar' ? theme.category_label_ar : theme.category_label_en;

  // Category colors
  const categoryColors: Record<string, string> = {
    aqidah: 'bg-purple-100 text-purple-700',
    iman: 'bg-blue-100 text-blue-700',
    ibadat: 'bg-green-100 text-green-700',
    akhlaq_fardi: 'bg-amber-100 text-amber-700',
    akhlaq_ijtima: 'bg-orange-100 text-orange-700',
    muharramat: 'bg-red-100 text-red-700',
    sunan_ilahiyyah: 'bg-indigo-100 text-indigo-700',
  };

  const colorClass = categoryColors[theme.category] || 'bg-gray-100 text-gray-700';

  return (
    <Link
      to={`/themes/${theme.id}`}
      className="card hover:shadow-lg transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
          <BookOpen className="w-5 h-5 text-primary-600" />
        </div>
        <span className={clsx('text-xs font-medium px-2 py-1 rounded', colorClass)}>
          {categoryLabel}
        </span>
      </div>

      <h3 className="text-lg font-semibold mb-2 group-hover:text-primary-600 transition-colors">
        {title}
      </h3>

      {/* Key Concepts */}
      {theme.key_concepts && theme.key_concepts.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {theme.key_concepts.slice(0, 4).map((concept) => (
            <span
              key={concept}
              className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
            >
              {concept}
            </span>
          ))}
          {theme.key_concepts.length > 4 && (
            <span className="text-xs text-gray-400">+{theme.key_concepts.length - 4}</span>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
        <div className="flex items-center gap-1">
          <Layers className="w-4 h-4" />
          <span>{theme.segment_count} {language === 'ar' ? 'مقطع' : 'segments'}</span>
        </div>
        <div className="flex items-center gap-1">
          <BookMarked className="w-4 h-4" />
          <span>{theme.total_verses} {language === 'ar' ? 'آية' : 'verses'}</span>
        </div>
      </div>

      {/* Consequences indicator */}
      {theme.has_consequences && (
        <div className="flex items-center gap-1 text-xs text-amber-600 mb-3">
          <Tag className="w-3 h-3" />
          <span>{language === 'ar' ? 'الجزاء والعاقبة' : 'Rewards & Consequences'}</span>
        </div>
      )}

      <div className="flex items-center text-primary-600 text-sm font-medium">
        {language === 'ar' ? 'استكشاف المحور' : 'Explore Theme'}
        <ArrowRight className={`w-4 h-4 ${language === 'ar' ? 'mr-1 group-hover:-translate-x-1' : 'ml-1 group-hover:translate-x-1'} transition-transform`} />
      </div>
    </Link>
  );
}
