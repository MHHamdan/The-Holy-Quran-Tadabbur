import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Tag, ArrowRight, Layers, BookMarked, Star, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { themesApi, quranApi, QuranicTheme, ThemeCategory, AllahNameResponse, ALLAH_NAME_CATEGORIES } from '../lib/api';
import clsx from 'clsx';

type ActiveTab = 'themes' | 'allah-names';

export function ThemesPage() {
  const { language } = useLanguageStore();
  const [activeTab, setActiveTab] = useState<ActiveTab>('themes');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Tab Bar */}
      <div className="flex gap-2 mb-8 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('themes')}
          className={clsx(
            'px-6 py-3 text-lg font-semibold transition-colors border-b-2 -mb-px',
            activeTab === 'themes'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700',
            language === 'ar' && 'font-arabic'
          )}
        >
          {t('themes_tab', language)}
        </button>
        <button
          onClick={() => setActiveTab('allah-names')}
          className={clsx(
            'px-6 py-3 text-lg font-semibold transition-colors border-b-2 -mb-px flex items-center gap-2',
            activeTab === 'allah-names'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700',
            language === 'ar' && 'font-arabic'
          )}
        >
          <Star className="w-5 h-5" />
          {t('allah_names_tab', language)}
        </button>
      </div>

      {activeTab === 'themes' ? (
        <ThemesTab language={language} />
      ) : (
        <AllahNamesTab language={language} />
      )}
    </div>
  );
}

// =============================================================================
// Themes Tab (existing functionality)
// =============================================================================

function ThemesTab({ language }: { language: 'ar' | 'en' }) {
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
    <>
      {/* Header */}
      <div className="mb-8">
        <h1 className={clsx('text-3xl font-bold text-gray-900 mb-2', language === 'ar' && 'font-arabic')}>
          {t('themes_title', language)}
        </h1>
        <p className={clsx('text-gray-600', language === 'ar' && 'font-arabic')}>
          {t('themes_subtitle', language)}
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
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
              language === 'ar' && 'font-arabic'
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
            {t('themes_no_results', language)}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            {t('themes_run_seed', language)}
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {themes.map((theme) => (
            <ThemeCard key={theme.id} theme={theme} language={language} />
          ))}
        </div>
      )}
    </>
  );
}

// =============================================================================
// Allah Names Tab
// =============================================================================

function AllahNamesTab({ language }: { language: 'ar' | 'en' }) {
  const [names, setNames] = useState<AllahNameResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedName, setExpandedName] = useState<number | null>(null);

  useEffect(() => {
    loadNames();
  }, [language]);

  async function loadNames() {
    setLoading(true);
    try {
      const response = await quranApi.getAllahNames({
        lang: language,
        include_verses: true,
        max_verses_per_name: 5,
      });
      setNames(response.data.names);
    } catch (error) {
      console.error('Failed to load Allah names:', error);
    } finally {
      setLoading(false);
    }
  }

  const filteredNames = selectedCategory === 'all'
    ? names
    : names.filter((n) => n.category === selectedCategory);

  const categories: Array<{ key: string; label: string }> = [
    { key: 'all', label: language === 'ar' ? 'الكل' : 'All' },
    ...Object.entries(ALLAH_NAME_CATEGORIES).map(([key, labels]) => ({
      key,
      label: language === 'ar' ? labels.ar : labels.en,
    })),
  ];

  // Category colors
  const categoryColors: Record<string, string> = {
    dhat: 'bg-purple-100 text-purple-700 border-purple-200',
    jamal: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    jalal: 'bg-red-100 text-red-700 border-red-200',
    kamal: 'bg-blue-100 text-blue-700 border-blue-200',
    "af'al": 'bg-amber-100 text-amber-700 border-amber-200',
  };

  return (
    <>
      {/* Header */}
      <div className="mb-8">
        <h1 className={clsx('text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3', language === 'ar' && 'font-arabic')}>
          <Star className="w-8 h-8 text-primary-600" />
          {t('allah_names_title', language)}
        </h1>
        <p className={clsx('text-gray-600', language === 'ar' && 'font-arabic')}>
          {t('allah_names_subtitle', language)}
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-8">
        {categories.map((cat) => {
          const count = cat.key === 'all'
            ? names.length
            : names.filter((n) => n.category === cat.key).length;
          return (
            <button
              key={cat.key}
              onClick={() => setSelectedCategory(cat.key)}
              className={clsx(
                'px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2',
                selectedCategory === cat.key
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
                language === 'ar' && 'font-arabic'
              )}
            >
              <span>{cat.label}</span>
              <span className="text-xs opacity-75">({count})</span>
            </button>
          );
        })}
      </div>

      {/* Names Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">{t('loading', language)}</p>
        </div>
      ) : filteredNames.length === 0 ? (
        <div className="text-center py-12 card">
          <Star className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {t('allah_names_no_results', language)}
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredNames.map((name) => (
            <AllahNameCard
              key={name.number}
              name={name}
              language={language}
              isExpanded={expandedName === name.number}
              onToggle={() => setExpandedName(expandedName === name.number ? null : name.number)}
              categoryColor={categoryColors[name.category] || 'bg-gray-100 text-gray-700'}
            />
          ))}
        </div>
      )}
    </>
  );
}

// =============================================================================
// Allah Name Card Component
// =============================================================================

interface AllahNameCardProps {
  name: AllahNameResponse;
  language: 'ar' | 'en';
  isExpanded: boolean;
  onToggle: () => void;
  categoryColor: string;
}

function AllahNameCard({ name, language, isExpanded, onToggle, categoryColor }: AllahNameCardProps) {
  const meaning = language === 'ar' ? name.meaning_ar : name.meaning_en;
  const description = language === 'ar' ? name.description_ar : name.description_en;
  const categoryLabel = language === 'ar' ? name.category_label_ar : name.category_label_en;

  return (
    <div
      className={clsx(
        'card transition-all cursor-pointer hover:shadow-md',
        isExpanded && 'col-span-1 md:col-span-2 lg:col-span-3'
      )}
      onClick={onToggle}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-bold">
            {name.number}
          </span>
          <div>
            <h3 className="text-2xl font-arabic font-bold text-gray-900">
              {name.name_ar}
            </h3>
            <p className="text-sm text-gray-500">{name.transliteration}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx('text-xs font-medium px-2 py-1 rounded', categoryColor)}>
            {categoryLabel}
          </span>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Short Meaning */}
      <p className="text-gray-600 text-sm mb-2">
        <span className="font-semibold">{t('allah_names_meaning', language)}:</span> {meaning}
      </p>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100" onClick={(e) => e.stopPropagation()}>
          {/* Description */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-2">{t('allah_names_description', language)}</h4>
            <p className="text-gray-700 leading-relaxed">{description}</p>
          </div>

          {/* Verses */}
          {name.verses && name.verses.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                {t('allah_names_verses', language)} ({name.verses.length})
              </h4>
              <div className="space-y-4">
                {name.verses.map((verse, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-primary-600">
                        {verse.reference}
                      </span>
                      <Link
                        to={`/mushaf?page=${Math.ceil((verse.sura_no * 10 + verse.aya_no) / 15)}`}
                        className="text-xs text-primary-600 hover:underline flex items-center gap-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {t('view_in_mushaf', language)}
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </div>
                    <p
                      className="text-lg font-arabic leading-loose text-gray-900 mb-2"
                      dir="rtl"
                      dangerouslySetInnerHTML={{
                        __html: verse.highlighted_text
                          .replace(/【/g, '<mark class="bg-yellow-200 px-0.5 rounded">')
                          .replace(/】/g, '</mark>'),
                      }}
                    />
                    {verse.tafseer_snippet && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs font-semibold text-gray-500 mb-1">
                          {t('allah_names_tafseer', language)}:
                        </p>
                        <p className="text-sm text-gray-600">{verse.tafseer_snippet}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Theme Card Component (existing)
// =============================================================================

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

      <h3 className={clsx('text-lg font-semibold mb-2 group-hover:text-primary-600 transition-colors', language === 'ar' && 'font-arabic')}>
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
          <span>{theme.segment_count} {t('themes_segments', language)}</span>
        </div>
        <div className="flex items-center gap-1">
          <BookMarked className="w-4 h-4" />
          <span>{theme.total_verses} {t('themes_verses', language)}</span>
        </div>
      </div>

      {/* Consequences indicator */}
      {theme.has_consequences && (
        <div className="flex items-center gap-1 text-xs text-amber-600 mb-3">
          <Tag className="w-3 h-3" />
          <span>{t('themes_rewards', language)}</span>
        </div>
      )}

      <div className={clsx('flex items-center text-primary-600 text-sm font-medium', language === 'ar' && 'font-arabic')}>
        {t('themes_explore', language)}
        <ArrowRight className={clsx('w-4 h-4 transition-transform', language === 'ar' ? 'ms-1 rotate-180 group-hover:-translate-x-1' : 'ms-1 group-hover:translate-x-1')} />
      </div>
    </Link>
  );
}
