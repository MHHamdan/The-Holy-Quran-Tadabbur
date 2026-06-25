import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Tag, ArrowRight, Layers, BookMarked, Star, ChevronDown, ChevronUp, Play, Pause, SkipBack, SkipForward, Volume2 } from 'lucide-react';
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
    let cancelled = false;
    setLoading(true);
    const params = selectedCategory === 'all'
      ? { parent_only: true }
      : { category: selectedCategory };
    themesApi.listThemes(params)
      .then(r => { if (!cancelled) setThemes(r.data.themes); })
      .catch(error => console.error('Failed to load themes:', error))
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [selectedCategory]);

  async function loadCategories() {
    try {
      const response = await themesApi.getCategories();
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories:', error);
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
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedName, setExpandedName] = useState<number | null>(null);

  const {
    data: liteData,
    isLoading: liteLoading,
  } = useQuery({
    queryKey: ['allah-names-lite', language],
    queryFn: () =>
      quranApi
        .getAllahNames({ lang: language, include_verses: false })
        .then((r) => r.data),
    staleTime: 60 * 60 * 1000,
    gcTime: 4 * 60 * 60 * 1000,
  });

  const names = liteData?.names ?? [];

  const filteredNames = useMemo(
    () =>
      selectedCategory === 'all'
        ? names
        : names.filter((n) => n.category === selectedCategory),
    [names, selectedCategory],
  );

  const categories: Array<{ key: string; label: string }> = [
    { key: 'all', label: language === 'ar' ? 'الكل' : 'All' },
    ...Object.entries(ALLAH_NAME_CATEGORIES).map(([key, labels]) => ({
      key,
      label: language === 'ar' ? labels.ar : labels.en,
    })),
  ];

  const categoryColors: Record<string, string> = {
    dhat: 'bg-purple-100 text-purple-700 border-purple-200',
    jamal: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    jalal: 'bg-red-100 text-red-700 border-red-200',
    kamal: 'bg-blue-100 text-blue-700 border-blue-200',
    "af'al": 'bg-amber-100 text-amber-700 border-amber-200',
  };

  return (
    <>
      <div className="mb-8">
        <h1 className={clsx('text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3', language === 'ar' && 'font-arabic')}>
          <Star className="w-8 h-8 text-primary-600" />
          {t('allah_names_title', language)}
        </h1>
        <p className={clsx('text-gray-600', language === 'ar' && 'font-arabic')}>
          {t('allah_names_subtitle', language)}
        </p>
      </div>

      {/* Audio player — shown once names are loaded */}
      {names.length > 0 && (
        <AllahNamesAudioPlayer names={names} language={language} />
      )}

      <div className="flex flex-wrap gap-2 mb-8">
        {categories.map((cat) => {
          const count =
            cat.key === 'all'
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

      {liteLoading ? (
        <AllahNamesSkeleton />
      ) : filteredNames.length === 0 ? (
        <div className="text-center py-12 card">
          <Star className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">{t('allah_names_no_results', language)}</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredNames.map((name) => (
            <AllahNameCard
              key={name.number}
              name={name}
              language={language}
              isExpanded={expandedName === name.number}
              onToggle={() =>
                setExpandedName(expandedName === name.number ? null : name.number)
              }
              categoryColor={categoryColors[name.category] || 'bg-gray-100 text-gray-700'}
            />
          ))}
        </div>
      )}
    </>
  );
}

// =============================================================================
// 99 Names Audio Player
// =============================================================================

interface AllahNamesAudioPlayerProps {
  names: AllahNameResponse[];
  language: 'ar' | 'en';
}

function AllahNamesAudioPlayer({ names, language }: AllahNamesAudioPlayerProps) {
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const [index, setIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasTts, setHasTts] = useState(false);
  const [noArVoice, setNoArVoice] = useState(false);

  // All mutable playback state lives in refs so closures never capture stale values
  const indexRef = useRef(0);
  const activeRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const namesRef = useRef(names);
  useEffect(() => { namesRef.current = names; }, [names]);

  const current = names[index];

  // Detect TTS support and wait for voice list (Chrome loads voices async)
  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    setHasTts(true);
    const checkVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) setNoArVoice(!voices.some((v) => v.lang.startsWith('ar')));
    };
    checkVoices();
    window.speechSynthesis.addEventListener('voiceschanged', checkVoices);
    return () => window.speechSynthesis.removeEventListener('voiceschanged', checkVoices);
  }, []);

  const getBestArVoice = (): SpeechSynthesisVoice | null => {
    const voices = window.speechSynthesis.getVoices();
    return (
      voices.find((v) => v.lang === 'ar-SA') ??
      voices.find((v) => v.lang === 'ar') ??
      voices.find((v) => v.lang.startsWith('ar')) ??
      null
    );
  };

  const stopAll = useCallback(() => {
    activeRef.current = false;
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; }
    if (typeof window !== 'undefined' && window.speechSynthesis) window.speechSynthesis.cancel();
    setIsPlaying(false);
  }, []);

  // speakIndex reads from refs only — safe to call from any async closure
  const speakIndex = useCallback((i: number) => {
    const list = namesRef.current;
    if (!activeRef.current || i < 0 || i >= list.length) {
      activeRef.current = false;
      setIsPlaying(false);
      return;
    }

    window.speechSynthesis.cancel();

    const utt = new SpeechSynthesisUtterance(list[i].name_ar);
    utt.lang = 'ar-SA';
    utt.rate = 0.8;
    utt.pitch = 1.0;
    const voice = getBestArVoice();
    if (voice) utt.voice = voice;

    utt.onend = () => {
      if (!activeRef.current) return;
      if (i < list.length - 1) {
        const next = i + 1;
        indexRef.current = next;
        setIndex(next);
        // 400ms natural pause between names
        timerRef.current = setTimeout(() => speakIndex(next), 400);
      } else {
        activeRef.current = false;
        setIsPlaying(false);
      }
    };

    utt.onerror = (e) => {
      if (e.error === 'canceled') return;
      activeRef.current = false;
      setIsPlaying(false);
    };

    window.speechSynthesis.speak(utt);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onTogglePlay = useCallback(() => {
    if (activeRef.current) {
      stopAll();
    } else {
      activeRef.current = true;
      setIsPlaying(true);
      speakIndex(indexRef.current);
    }
  }, [speakIndex, stopAll]);

  const onPrev = useCallback(() => {
    stopAll();
    const next = Math.max(0, indexRef.current - 1);
    indexRef.current = next;
    setIndex(next);
  }, [stopAll]);

  const onNext = useCallback(() => {
    stopAll();
    const next = Math.min(namesRef.current.length - 1, indexRef.current + 1);
    indexRef.current = next;
    setIndex(next);
  }, [stopAll]);

  useEffect(() => () => stopAll(), [stopAll]);

  if (!hasTts || names.length === 0) return null;

  return (
    <div
      className="mb-6 p-4 bg-gradient-to-r from-emerald-50 to-amber-50 border border-emerald-200 rounded-xl shadow-sm"
      dir={dir}
    >
      <div className="flex items-center gap-2 mb-3">
        <Volume2 className="w-5 h-5 text-emerald-700 flex-shrink-0" />
        <h2 className={clsx('text-sm font-semibold text-emerald-800', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? 'استمع لأسماء الله الحسنى' : 'Listen to the 99 Names of Allah'}
        </h2>
        <span className="ms-auto text-xs text-gray-500 tabular-nums" dir="ltr">
          {index + 1} / {names.length}
        </span>
      </div>

      {noArVoice && (
        <p className="mb-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
          {language === 'ar'
            ? 'لا يوجد صوت عربي في متصفحك — قد يكون النطق غير عربي.'
            : 'No Arabic voice found in your browser — pronunciation may not be in Arabic.'}
        </p>
      )}

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onPrev}
          disabled={index === 0}
          className="p-2 rounded-full text-gray-600 hover:bg-emerald-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label={language === 'ar' ? 'السابق' : 'Previous'}
        >
          <SkipBack className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={onTogglePlay}
          className="p-3 rounded-full bg-emerald-600 text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-400 transition-colors"
          aria-label={isPlaying ? (language === 'ar' ? 'إيقاف' : 'Pause') : (language === 'ar' ? 'تشغيل' : 'Play')}
        >
          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
        </button>

        <button
          type="button"
          onClick={onNext}
          disabled={index >= names.length - 1}
          className="p-2 rounded-full text-gray-600 hover:bg-emerald-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label={language === 'ar' ? 'التالي' : 'Next'}
        >
          <SkipForward className="w-4 h-4" />
        </button>

        {current && (
          <div className="flex-1 min-w-0 ms-2">
            <p className="font-arabic text-2xl text-gray-900 leading-tight truncate" dir="rtl" lang="ar">
              {current.name_ar}
            </p>
            <p className="text-xs text-gray-600 truncate mt-0.5" dir="ltr">
              {current.transliteration}
              {' · '}
              {language === 'ar' ? current.meaning_ar : current.meaning_en}
            </p>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400 mt-3">
        {language === 'ar'
          ? 'النطق العربي عبر متصفحك · يعمل بدون إنترنت'
          : 'Arabic pronunciation via your browser · works offline'}
      </p>
    </div>
  );
}

// Skeleton grid shown while the lite list is loading. Lite payload is
// already small (~66KB, <100ms warm), so users almost never see this on
// repeat visits — the React Query cache short-circuits the fetch.
function AllahNamesSkeleton() {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4" aria-hidden="true">
      {Array.from({ length: 9 }).map((_, i) => (
        <div
          key={i}
          className="card animate-pulse"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-200" />
              <div>
                <div className="h-6 w-24 bg-gray-200 rounded mb-1" />
                <div className="h-3 w-20 bg-gray-100 rounded" />
              </div>
            </div>
            <div className="h-5 w-12 bg-gray-100 rounded" />
          </div>
          <div className="h-3 w-3/4 bg-gray-100 rounded" />
        </div>
      ))}
    </div>
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

      <p className="text-gray-600 text-sm mb-2">
        <span className="font-semibold">{t('allah_names_meaning', language)}:</span> {meaning}
      </p>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100" onClick={(e) => e.stopPropagation()}>
          <h4 className="font-semibold text-gray-900 mb-2">{t('allah_names_description', language)}</h4>
          <p className="text-gray-700 leading-relaxed">{description}</p>
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
