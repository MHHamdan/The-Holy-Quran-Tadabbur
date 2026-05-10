import { useEffect, useState } from 'react';
import { BarChart2, TrendingUp, TrendingDown, Minus, Heart, Star, Sprout } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { therapyApi } from '../../lib/api';
import type { InsightsResponse } from '../../types/therapy';
import { EmotionGrowthMap } from './EmotionGrowthMap';
import clsx from 'clsx';

interface InsightsDashboardProps {
  sessionIds: string[];
}

export function InsightsDashboard({ sessionIds }: InsightsDashboardProps) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionIds.length === 0) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    therapyApi.getInsights(sessionIds, language)
      .then(data => { if (!cancelled) setInsights(data); })
      .catch(() => { if (!cancelled) setError('Could not load insights'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [sessionIds, language]);

  if (sessionIds.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center gap-2 mb-4">
        <BarChart2 className="w-5 h-5 text-indigo-500" />
        <h3 className={clsx('font-semibold text-gray-800', isRtl && 'font-arabic')}>
          {t('insights_title', language)}
        </h3>
      </div>

      {loading && (
        <p className={clsx('text-sm text-gray-400 animate-pulse', isRtl && 'font-arabic text-right')}>
          {t('loading', language)}
        </p>
      )}

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}

      {insights && !loading && (
        <div className="space-y-4">
          {/* Summary stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-indigo-50 rounded-xl p-3 text-center">
              <p className="text-2xl font-bold text-indigo-700">{insights.total_sessions}</p>
              <p className={clsx('text-xs text-indigo-500 mt-0.5', isRtl && 'font-arabic')}>
                {t('insights_sessions', language)}
              </p>
            </div>
            {insights.most_visited_theme && (
              <div className="bg-emerald-50 rounded-xl p-3 text-center">
                <div className="flex justify-center mb-1">
                  <Star className="w-5 h-5 text-emerald-600" />
                </div>
                <p className={clsx('text-sm font-semibold text-emerald-700 capitalize', isRtl && 'font-arabic')}>
                  {insights.most_visited_theme}
                </p>
                <p className={clsx('text-xs text-emerald-500', isRtl && 'font-arabic')}>
                  {t('insights_top_theme', language)}
                </p>
              </div>
            )}
          </div>

          {/* Weekly wellbeing change */}
          {insights.weekly_change !== undefined && insights.weekly_change !== null && (
            <div className={clsx(
              'flex items-center gap-2 rounded-xl px-3 py-2.5',
              insights.weekly_change > 0.1
                ? 'bg-emerald-50 border border-emerald-100'
                : insights.weekly_change < -0.1
                  ? 'bg-rose-50 border border-rose-100'
                  : 'bg-gray-50 border border-gray-100',
              isRtl && 'flex-row-reverse',
            )}>
              {insights.weekly_change > 0.1
                ? <TrendingUp className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                : insights.weekly_change < -0.1
                  ? <TrendingDown className="w-4 h-4 text-rose-500 flex-shrink-0" />
                  : <Minus className="w-4 h-4 text-gray-400 flex-shrink-0" />
              }
              <div>
                <p className={clsx(
                  'text-xs font-medium',
                  insights.weekly_change > 0.1 ? 'text-emerald-700' : insights.weekly_change < -0.1 ? 'text-rose-700' : 'text-gray-600',
                  isRtl && 'font-arabic',
                )}>
                  {isRtl
                    ? insights.weekly_change > 0.1 ? 'تحسّن هذا الأسبوع' : insights.weekly_change < -0.1 ? 'يحتاج اهتماماً هذا الأسبوع' : 'مستقر هذا الأسبوع'
                    : insights.weekly_change > 0.1 ? 'Improving this week' : insights.weekly_change < -0.1 ? 'Needs support this week' : 'Stable this week'
                  }
                </p>
                <p className={clsx('text-[10px] text-gray-400', isRtl && 'font-arabic')}>
                  {isRtl ? 'مقارنةً بالأسبوع الماضي' : 'vs. last week'}
                </p>
              </div>
            </div>
          )}

          {/* Top emotion */}
          {insights.top_emotion && (
            <div className="flex items-center gap-3 bg-rose-50 rounded-xl p-3">
              <Heart className="w-5 h-5 text-rose-500 flex-shrink-0" />
              <div>
                <p className={clsx('text-sm font-medium text-rose-700', isRtl && 'font-arabic')}>
                  {isRtl ? insights.top_emotion_label_ar : insights.top_emotion_label_en}
                </p>
                <p className={clsx('text-xs text-rose-400', isRtl && 'font-arabic')}>
                  {t('insights_top_emotion', language)}
                </p>
              </div>
            </div>
          )}

          {/* Emotion distribution bars */}
          {insights.emotion_distribution.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <TrendingUp className="w-4 h-4 text-gray-400" />
                <p className={clsx('text-xs text-gray-500 font-medium uppercase tracking-wide', isRtl && 'font-arabic')}>
                  {t('insights_distribution', language)}
                </p>
              </div>
              <div className="space-y-2">
                {insights.emotion_distribution.map(item => {
                  const pct = insights.total_sessions > 0
                    ? Math.round((item.count / insights.total_sessions) * 100)
                    : 0;
                  return (
                    <div key={item.emotion}>
                      <div className="flex justify-between items-center mb-0.5">
                        <span className={clsx('text-xs text-gray-600', isRtl && 'font-arabic')}>
                          {isRtl ? item.label_ar : item.label_en}
                        </span>
                        <span className="text-xs text-gray-400 font-mono">{pct}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-400 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Growth suggestion */}
          {(insights.growth_prompt_en || insights.growth_prompt_ar) && (
            <div className="flex items-start gap-3 bg-amber-50 border border-amber-100 rounded-xl p-3">
              <Sprout className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className={clsx('text-xs font-medium text-amber-700', isRtl && 'font-arabic')}>
                  {t('insights_growth_prompt', language)}
                </p>
                <p className={clsx('text-xs text-amber-600 leading-relaxed', isRtl && 'font-arabic text-right')}>
                  {isRtl ? insights.growth_prompt_ar : insights.growth_prompt_en}
                </p>
                {insights.suggested_next_theme && (
                  <span className="inline-block mt-1 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full capitalize">
                    {insights.suggested_next_theme}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Phase T5-B — Emotional Growth Map */}
          {insights.emotion_timeline && insights.emotion_timeline.length > 0 && (
            <div className="border-t border-gray-100 pt-4">
              <EmotionGrowthMap
                timeline={insights.emotion_timeline}
                trend={insights.trend ?? 'stable'}
                streakDays={insights.streak_days ?? 0}
                lang={language as 'ar' | 'en'}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
