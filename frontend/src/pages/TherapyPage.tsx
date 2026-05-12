import { useState, useEffect, useCallback } from 'react';
import { Heart, AlertTriangle, ArrowLeft, Loader2, Sparkles, BookOpen } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { therapyApi } from '../lib/api';
import {
  EmotionalInputPanel,
  SpiritualGuidanceCard,
  HealingThemeSelector,
  ReflectionLog,
  TherapyChat,
  InsightsDashboard,
  RuqyahGuide,
  PropheticDuasPanel,
  DailyPracticesPanel,
  TopicKnowledgePanel,
} from '../components/therapy';
import type {
  SpiritualGuidanceResponse,
  HealingTheme,
  ThemeDetailResponse,
  ReflectionEntry,
} from '../types/therapy';
import clsx from 'clsx';

// ---------------------------------------------------------------------------
// Local-storage keys
// ---------------------------------------------------------------------------
const STORAGE_KEY = 'tadabbur_reflections';
const PERSONALIZATION_KEY = 'tadabbur_personalization';

interface PersonalizationContext {
  previous_emotion?: string;
  previous_theme?: string;
  reinforcement_index: number;
}

function loadPersonalization(): PersonalizationContext {
  try {
    const raw = localStorage.getItem(PERSONALIZATION_KEY);
    return raw ? (JSON.parse(raw) as PersonalizationContext) : { reinforcement_index: 0 };
  } catch {
    return { reinforcement_index: 0 };
  }
}

function savePersonalization(ctx: PersonalizationContext): void {
  try {
    localStorage.setItem(PERSONALIZATION_KEY, JSON.stringify(ctx));
  } catch {
    // ignore storage errors
  }
}

function loadReflections(): ReflectionEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ReflectionEntry[]) : [];
  } catch {
    return [];
  }
}

function saveReflections(entries: ReflectionEntry[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, 50)));
  } catch {
    // ignore storage errors
  }
}

type TabKey = 'guidance' | 'chat' | 'insights' | 'ruqyah';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TherapyPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [activeTab, setActiveTab] = useState<TabKey>('guidance');

  const [themes, setThemes] = useState<HealingTheme[]>([]);
  const [themesLoading, setThemesLoading] = useState(true);

  const [asking, setAsking] = useState(false);
  const [guidance, setGuidance] = useState<SpiritualGuidanceResponse | null>(null);
  const [askError, setAskError] = useState<string | null>(null);
  const [showReinforcement, setShowReinforcement] = useState(false);

  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [themeData, setThemeData] = useState<ThemeDetailResponse | null>(null);
  const [themeLoading, setThemeLoading] = useState(false);

  const [reflections, setReflections] = useState<ReflectionEntry[]>(loadReflections);
  const [chatSessionIds, setChatSessionIds] = useState<string[]>([]);
  const [personalization, setPersonalization] = useState<PersonalizationContext>(loadPersonalization);

  // Load healing themes on mount
  useEffect(() => {
    therapyApi.getThemes()
      .then(data => setThemes(data.themes))
      .catch(() => {})
      .finally(() => setThemesLoading(false));
  }, []);

  const handleAsk = useCallback(async (message: string) => {
    setAsking(true);
    setAskError(null);
    setGuidance(null);
    setThemeData(null);
    setSelectedTheme(null);
    setShowReinforcement(false);

    try {
      const result = await therapyApi.ask({
        message,
        language,
        previous_emotion: personalization.previous_emotion,
        previous_theme: personalization.previous_theme,
        reinforcement_index: personalization.reinforcement_index,
      });
      setGuidance(result);
      // Show reinforcement briefly after cards appear
      setTimeout(() => setShowReinforcement(true), 600);

      // Persist personalization context for next session
      const nextPersonalization: PersonalizationContext = {
        previous_emotion: result.emotion,
        previous_theme: result.suggested_theme ?? personalization.previous_theme,
        reinforcement_index: (personalization.reinforcement_index + 1) % 10,
      };
      setPersonalization(nextPersonalization);
      savePersonalization(nextPersonalization);

      const entry: ReflectionEntry = {
        session_id: result.session_id,
        reflection: '',
        timestamp: Date.now(),
        emotion: result.emotion,
        verses: result.cards.map(c => c.reference),
      };
      setReflections(prev => {
        const updated = [entry, ...prev.filter(e => e.session_id !== entry.session_id)];
        saveReflections(updated);
        return updated;
      });
    } catch {
      setAskError(
        language === 'ar'
          ? 'حدث خطأ أثناء البحث عن التوجيه. يرجى المحاولة مرة أخرى.'
          : 'An error occurred while seeking guidance. Please try again.'
      );
    } finally {
      setAsking(false);
    }
  }, [language]);

  const handleThemeSelect = useCallback(async (key: string) => {
    if (key === selectedTheme) {
      setSelectedTheme(null);
      setThemeData(null);
      return;
    }
    setSelectedTheme(key);
    setThemeLoading(true);
    setGuidance(null);
    setAskError(null);
    setShowReinforcement(false);

    try {
      const data = await therapyApi.getTheme(key);
      setThemeData(data);
    } catch {
      setThemeData(null);
    } finally {
      setThemeLoading(false);
    }
  }, [selectedTheme]);

  const handleSaveReflection = useCallback(async (sessionId: string, text: string) => {
    await therapyApi.saveReflection({ session_id: sessionId, reflection: text });
    setReflections(prev => {
      const updated = prev.map(e =>
        e.session_id === sessionId ? { ...e, reflection: text } : e
      );
      saveReflections(updated);
      return updated;
    });
  }, []);

  const handleDeleteReflection = useCallback((sessionId: string) => {
    setReflections(prev => {
      const updated = prev.filter(e => e.session_id !== sessionId);
      saveReflections(updated);
      return updated;
    });
  }, []);

  const handleChatSessionCreated = useCallback((id: string) => {
    setChatSessionIds(prev => prev.includes(id) ? prev : [id, ...prev]);
  }, []);

  const currentGuidance = guidance ?? themeData;
  const activeCards = guidance?.cards ?? themeData?.cards ?? [];
  const activeDisclaimer = guidance?.disclaimer_en ?? themeData?.disclaimer_en;

  // All session IDs for insights (guidance + chat)
  const allSessionIds = [
    ...reflections.map(r => r.session_id),
    ...chatSessionIds,
  ];

  const tabs: Array<{ key: TabKey; label: string }> = [
    { key: 'guidance', label: t('therapy_guidance_tab', language) },
    { key: 'ruqyah',   label: t('therapy_ruqyah_tab', language) },
    { key: 'chat',     label: t('therapy_chat_tab', language) },
    { key: 'insights', label: t('therapy_insights_tab', language) },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-rose-100 mb-4">
          <Heart className="w-7 h-7 text-rose-500" />
        </div>
        <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
          {t('therapy_title', language)}
        </h1>
        <p className={clsx('mt-1 text-gray-500 text-sm', isRtl && 'font-arabic')}>
          {t('therapy_subtitle', language)}
        </p>
      </div>

      {/* Islamic intro banner — key healing verse */}
      <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl border border-emerald-100">
        <div className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
          <BookOpen className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p
              dir={isRtl ? 'rtl' : 'ltr'}
              className={clsx('text-base leading-loose text-emerald-900 font-medium', isRtl ? 'font-arabic text-right' : 'text-left')}
            >
              {t('therapy_intro_verse', language)}
            </p>
            <p dir={isRtl ? 'rtl' : 'ltr'} className={clsx('text-xs text-emerald-600', isRtl && 'text-right font-arabic')}>
              {t('therapy_intro_ref', language)}
            </p>
          </div>
        </div>
      </div>

      {/* Mode tabs */}
      <div className={clsx('flex rounded-xl overflow-hidden border border-gray-200 bg-gray-50', isRtl && 'flex-row-reverse')}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={clsx(
              'flex-1 py-2.5 text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700',
              isRtl && 'font-arabic',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ================================================================ */}
      {/* TAB: Guidance Cards                                               */}
      {/* ================================================================ */}
      {activeTab === 'guidance' && (
        <>
          {/* Healing Theme Selector */}
          <div>
            <div className={clsx('flex items-center justify-between mb-3', isRtl && 'flex-row-reverse')}>
              <div>
                <h2 className={clsx('font-semibold text-gray-700 text-sm', isRtl && 'font-arabic')}>
                  {t('therapy_themes_title', language)}
                </h2>
                <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic text-right')}>
                  {t('therapy_themes_subtitle', language)}
                </p>
              </div>
              {selectedTheme && (
                <button
                  onClick={() => { setSelectedTheme(null); setThemeData(null); }}
                  className={clsx('flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700', isRtl && 'flex-row-reverse font-arabic')}
                >
                  <ArrowLeft className={clsx('w-3 h-3', isRtl && 'rotate-180')} />
                  {t('therapy_back', language)}
                </button>
              )}
            </div>
            {themesLoading ? (
              <div className="flex justify-center py-4">
                <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
              </div>
            ) : (
              <HealingThemeSelector
                themes={themes}
                selectedTheme={selectedTheme}
                onSelect={handleThemeSelect}
                loading={themeLoading}
              />
            )}
          </div>

          {/* Emotional Input Panel */}
          <EmotionalInputPanel onSubmit={handleAsk} loading={asking} />

          {/* Loading state */}
          {(asking || themeLoading) && (
            <div className="flex flex-col items-center gap-3 py-8">
              <Loader2 className="w-8 h-8 text-rose-400 animate-spin" />
              <p className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
                {t('therapy_seeking', language)}
              </p>
            </div>
          )}

          {/* Error */}
          {askError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className={clsx('text-sm text-red-700', isRtl && 'font-arabic')}>{askError}</p>
            </div>
          )}

          {/* Empathy message */}
          {guidance && !asking && (
            <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl">
              <div className={clsx('flex items-center gap-2 mb-2', isRtl && 'flex-row-reverse')}>
                <span className="text-xs font-medium bg-rose-100 text-rose-600 px-2 py-0.5 rounded-full">
                  {isRtl ? guidance.emotion_label_ar : guidance.emotion_label_en}
                </span>
              </div>
              <p className={clsx('text-sm text-rose-800 leading-relaxed', isRtl && 'font-arabic text-right')}>
                {isRtl ? guidance.empathy_ar : guidance.empathy_en}
              </p>
            </div>
          )}

          {/* Personalization note (returning with same emotion) */}
          {guidance && !asking && (guidance.personalization_note_en || guidance.personalization_note_ar) && (
            <div className={clsx('px-4 py-2.5 bg-violet-50 border border-violet-100 rounded-xl flex items-start gap-2', isRtl && 'flex-row-reverse')}>
              <span className="text-violet-400 text-sm">✦</span>
              <p className={clsx('text-xs text-violet-700 leading-relaxed', isRtl && 'font-arabic text-right')}>
                {isRtl ? guidance.personalization_note_ar : guidance.personalization_note_en}
              </p>
            </div>
          )}

          {/* Theme detail header */}
          {themeData && !themeLoading && (
            <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-2xl">
              <div className={clsx('flex items-center gap-2 mb-1', isRtl && 'flex-row-reverse')}>
                <span className="text-xs font-medium bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full">
                  {isRtl ? themeData.theme.ar : themeData.theme.en}
                </span>
              </div>
              <p className={clsx('text-sm text-indigo-800', isRtl && 'font-arabic text-right')}>
                {isRtl ? themeData.theme.desc_ar : themeData.theme.desc_en}
              </p>
            </div>
          )}

          {/* Guidance Cards */}
          {activeCards.length > 0 && !asking && !themeLoading && (
            <div className="space-y-4">
              <h2 className={clsx('font-semibold text-gray-700 text-sm', isRtl && 'font-arabic')}>
                {t('therapy_guidance_title', language)}
                <span className={clsx('text-xs text-gray-400 font-normal', isRtl ? 'mr-2' : 'ml-2')}>
                  ({activeCards.length} {t('therapy_cards_count', language)})
                </span>
              </h2>
              {activeCards.map((card, i) => (
                <SpiritualGuidanceCard key={card.reference} card={card} index={i} />
              ))}
            </div>
          )}

          {/* No cards */}
          {currentGuidance && activeCards.length === 0 && !asking && !themeLoading && (
            <p className={clsx('text-center text-sm text-gray-400 py-4', isRtl && 'font-arabic')}>
              {t('therapy_no_cards', language)}
            </p>
          )}

          {/* Positive reinforcement banner */}
          {guidance && showReinforcement && !asking && (
            <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className={clsx('text-sm text-emerald-800 leading-relaxed', isRtl && 'font-arabic text-right')}>
                {isRtl ? guidance.reinforcement_ar : guidance.reinforcement_en}
              </p>
            </div>
          )}

          {/* Follow-up prompts */}
          {guidance && guidance.follow_up_prompts_en.length > 0 && !asking && (
            <div>
              <p className={clsx('text-xs text-gray-500 mb-2', isRtl && 'font-arabic text-right')}>
                {t('therapy_follow_up', language)}
              </p>
              <div className="flex flex-col gap-1.5">
                {(isRtl ? guidance.follow_up_prompts_ar : guidance.follow_up_prompts_en).map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleAsk(prompt)}
                    disabled={asking}
                    className={clsx(
                      'text-left px-4 py-2.5 text-sm rounded-xl border border-gray-200',
                      'bg-gray-50 hover:bg-rose-50 hover:border-rose-200 hover:text-rose-700',
                      'transition-colors text-gray-600 disabled:opacity-40',
                      isRtl && 'font-arabic text-right',
                    )}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Recommended themes */}
          {guidance && guidance.recommended_themes.length > 0 && !asking && themes.length > 0 && (
            <div>
              <p className={clsx('text-xs text-gray-500 mb-2', isRtl && 'font-arabic text-right')}>
                {t('therapy_recommended_themes', language)}
              </p>
              <div className={clsx('flex flex-wrap gap-2', isRtl && 'flex-row-reverse')}>
                {guidance.recommended_themes.map(key => {
                  const theme = themes.find(th => th.key === key);
                  if (!theme) return null;
                  return (
                    <button
                      key={key}
                      onClick={() => handleThemeSelect(key)}
                      className={clsx(
                        'px-3 py-1.5 text-xs rounded-full border transition-colors',
                        'border-indigo-200 bg-indigo-50 text-indigo-600 hover:bg-indigo-100',
                        isRtl && 'font-arabic',
                      )}
                    >
                      {isRtl ? theme.ar : theme.en}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Suggested theme nudge */}
          {guidance && !asking && guidance.suggested_theme && guidance.suggested_theme_reason_en && (
            <div className={clsx('flex items-start gap-3 p-3 bg-sky-50 border border-sky-100 rounded-xl', isRtl && 'flex-row-reverse')}>
              <span className="text-sky-400 text-base flex-shrink-0">→</span>
              <div>
                <p className={clsx('text-xs font-medium text-sky-700 mb-0.5', isRtl && 'font-arabic')}>
                  {t('therapy_suggested_theme', language)}
                  <span className={clsx('px-1.5 py-0.5 bg-sky-100 rounded text-sky-600', isRtl ? 'mr-1.5 font-arabic' : 'ml-1.5 capitalize')}>
                    {isRtl
                      ? (themes.find(th => th.key === guidance.suggested_theme)?.ar ?? guidance.suggested_theme)
                      : (themes.find(th => th.key === guidance.suggested_theme)?.en ?? guidance.suggested_theme)}
                  </span>
                </p>
                <p className={clsx('text-xs text-sky-600 leading-relaxed', isRtl && 'font-arabic text-right')}>
                  {isRtl ? guidance.suggested_theme_reason_ar : guidance.suggested_theme_reason_en}
                </p>
              </div>
            </div>
          )}

          {/* Disclaimer */}
          {activeDisclaimer && !asking && !themeLoading && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <p className={clsx('text-xs text-amber-700 leading-relaxed', isRtl && 'font-arabic text-right')}>
                {isRtl ? (guidance?.disclaimer_ar ?? themeData?.disclaimer_ar) : activeDisclaimer}
              </p>
            </div>
          )}

          {/* Prophetic Du'as — shown when guidance was returned */}
          {guidance && !asking && (
            <PropheticDuasPanel emotion={guidance.emotion} />
          )}

          {/* Topic Knowledge — adaptive hadith + wise phrases based on detected emotion */}
          {guidance && !asking && (
            <TopicKnowledgePanel topicKey={guidance.emotion} />
          )}

          {/* Daily Practices — always shown at bottom of guidance tab */}
          <DailyPracticesPanel />

          {/* Reflection Log */}
          <ReflectionLog
            entries={reflections}
            currentSessionId={guidance?.session_id ?? null}
            onSaveReflection={handleSaveReflection}
            onDeleteEntry={handleDeleteReflection}
            reflectionPrompt={
              guidance
                ? (isRtl ? guidance.reflection_prompt_ar : guidance.reflection_prompt_en)
                : undefined
            }
            allSessionIds={allSessionIds}
          />
        </>
      )}

      {/* ================================================================ */}
      {/* TAB: Ruqyah & Dhikr                                              */}
      {/* ================================================================ */}
      {activeTab === 'ruqyah' && (
        <div className="space-y-4">
          <RuqyahGuide />
        </div>
      )}

      {/* ================================================================ */}
      {/* TAB: QuranGPT Chat                                                */}
      {/* ================================================================ */}
      {activeTab === 'chat' && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 min-h-[560px] flex flex-col">
          <TherapyChat onSessionCreated={handleChatSessionCreated} />
        </div>
      )}

      {/* ================================================================ */}
      {/* TAB: My Journey (Insights)                                        */}
      {/* ================================================================ */}
      {activeTab === 'insights' && (
        <InsightsDashboard sessionIds={allSessionIds} />
      )}
    </div>
  );
}
