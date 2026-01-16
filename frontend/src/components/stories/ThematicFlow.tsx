/**
 * Thematic Flow Visualization Component
 *
 * Shows how themes flow through story segments, helping users understand:
 * - Which themes appear most frequently
 * - Where in the narrative specific themes emerge
 * - Theme clustering and progression
 */
import { useMemo } from 'react';
import { StorySegment } from '../../lib/api';
import { translateTheme, Language } from '../../i18n/translations';

interface ThematicFlowProps {
  segments: StorySegment[];
  language: Language;
  themes: string[];
}

// Theme color palette
const THEME_COLORS = [
  '#22c55e', // green
  '#3b82f6', // blue
  '#a855f7', // purple
  '#f97316', // orange
  '#eab308', // yellow
  '#ef4444', // red
  '#14b8a6', // teal
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
];

function getThemeColor(index: number): string {
  return THEME_COLORS[index % THEME_COLORS.length];
}

export function ThematicFlow({ segments, language, themes }: ThematicFlowProps) {
  const isArabic = language === 'ar';

  // Calculate theme occurrences across segments
  const themeData = useMemo(() => {
    const allThemes = new Map<string, number[]>();

    // Initialize all story themes
    themes.forEach(theme => {
      allThemes.set(theme, []);
    });

    // Track where each theme appears
    segments.forEach((segment, segIndex) => {
      const segmentThemes = segment.semantic_tags || [];
      segmentThemes.forEach((theme: string) => {
        if (!allThemes.has(theme)) {
          allThemes.set(theme, []);
        }
        allThemes.get(theme)!.push(segIndex);
      });
    });

    // Convert to array and sort by frequency
    return Array.from(allThemes.entries())
      .filter(([_, indices]) => indices.length > 0)
      .sort((a, b) => b[1].length - a[1].length);
  }, [segments, themes]);

  // Calculate narrative role distribution
  const roleDistribution = useMemo(() => {
    const roles = new Map<string, number>();
    segments.forEach(segment => {
      const role = segment.narrative_role || 'unknown';
      roles.set(role, (roles.get(role) || 0) + 1);
    });
    return Array.from(roles.entries()).sort((a, b) => b[1] - a[1]);
  }, [segments]);

  if (segments.length === 0) {
    return (
      <div className="card text-center py-8">
        <p className="text-gray-500">
          {isArabic ? 'لا توجد مقاطع للتحليل' : 'No segments to analyze'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Theme Flow Matrix */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">
          {isArabic ? 'تدفق المواضيع عبر القصة' : 'Theme Flow Across Story'}
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          {isArabic
            ? 'يوضح متى تظهر كل موضوع في مقاطع القصة'
            : 'Shows when each theme appears in story segments'}
        </p>

        <div className="overflow-x-auto">
          <div className="min-w-[500px]">
            {/* Header - Segment numbers */}
            <div className="flex items-center mb-2">
              <div className="w-32 text-xs text-gray-500 flex-shrink-0">
                {isArabic ? 'الموضوع' : 'Theme'}
              </div>
              <div className="flex gap-1 flex-1">
                {segments.map((_, i) => (
                  <div
                    key={i}
                    className="w-8 h-6 flex items-center justify-center text-xs text-gray-400"
                    title={`${isArabic ? 'مقطع' : 'Segment'} ${i + 1}`}
                  >
                    {i + 1}
                  </div>
                ))}
              </div>
            </div>

            {/* Theme rows */}
            {themeData.slice(0, 10).map(([theme, indices], themeIndex) => (
              <div key={theme} className="flex items-center mb-1.5">
                <div
                  className="w-32 text-xs font-medium truncate flex-shrink-0"
                  style={{ color: getThemeColor(themeIndex) }}
                  title={translateTheme(theme, language)}
                >
                  {translateTheme(theme, language)}
                </div>
                <div className="flex gap-1 flex-1">
                  {segments.map((_, segIndex) => {
                    const isPresent = indices.includes(segIndex);
                    return (
                      <div
                        key={segIndex}
                        className={`w-8 h-5 rounded-sm transition-colors ${
                          isPresent ? 'opacity-100' : 'opacity-10'
                        }`}
                        style={{
                          backgroundColor: getThemeColor(themeIndex),
                        }}
                        title={isPresent
                          ? `${translateTheme(theme, language)} - ${isArabic ? 'مقطع' : 'Segment'} ${segIndex + 1}`
                          : undefined
                        }
                      />
                    );
                  })}
                </div>
                <div className="w-8 text-xs text-gray-500 text-right flex-shrink-0">
                  {indices.length}
                </div>
              </div>
            ))}
          </div>
        </div>

        {themeData.length > 10 && (
          <p className="text-xs text-gray-400 mt-3">
            {isArabic
              ? `و ${themeData.length - 10} مواضيع أخرى...`
              : `And ${themeData.length - 10} more themes...`}
          </p>
        )}
      </div>

      {/* Theme Frequency Bar Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">
          {isArabic ? 'تكرار المواضيع' : 'Theme Frequency'}
        </h3>
        <div className="space-y-2">
          {themeData.slice(0, 8).map(([theme, indices], i) => {
            const percentage = (indices.length / segments.length) * 100;
            return (
              <div key={theme} className="flex items-center gap-3">
                <div className="w-24 text-xs font-medium truncate">
                  {translateTheme(theme, language)}
                </div>
                <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: getThemeColor(i),
                    }}
                  />
                </div>
                <div className="w-12 text-xs text-gray-500 text-right">
                  {indices.length}/{segments.length}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Narrative Role Distribution */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">
          {isArabic ? 'توزيع الأدوار السردية' : 'Narrative Role Distribution'}
        </h3>
        <div className="flex flex-wrap gap-3">
          {roleDistribution.map(([role, count]) => (
            <div
              key={role}
              className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2"
            >
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getRoleColor(role) }}
              />
              <span className="text-sm font-medium">
                {translateRole(role, language)}
              </span>
              <span className="text-xs text-gray-500">
                ({count})
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Theme Co-occurrence */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">
          {isArabic ? 'المواضيع المتزامنة' : 'Co-occurring Themes'}
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          {isArabic
            ? 'المواضيع التي تظهر معًا في نفس المقاطع'
            : 'Themes that appear together in the same segments'}
        </p>
        <div className="flex flex-wrap gap-2">
          {getCoOccurringThemes(segments, language).slice(0, 6).map(([pair, count]) => (
            <div
              key={pair}
              className="bg-gradient-to-r from-primary-50 to-sky-50 border border-primary-100 rounded-lg px-3 py-2"
            >
              <div className="text-xs font-medium text-primary-800">
                {pair}
              </div>
              <div className="text-xs text-gray-500">
                {count} {isArabic ? 'مقاطع' : 'segments'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Role color mapping
function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    introduction: '#22c55e',
    divine_mission: '#eab308',
    journey_phase: '#3b82f6',
    encounter: '#a855f7',
    test_or_trial: '#f97316',
    test: '#f97316',
    trial: '#f97316',
    moral_decision: '#ef4444',
    divine_intervention: '#facc15',
    outcome: '#14b8a6',
    reflection: '#8b5cf6',
    development: '#06b6d4',
    climax: '#ef4444',
    resolution: '#22c55e',
    rising_action: '#3b82f6',
    background: '#94a3b8',
  };
  return colors[role] || '#94a3b8';
}

// Role translation
function translateRole(role: string, language: Language): string {
  const translations: Record<string, { ar: string; en: string }> = {
    introduction: { ar: 'مقدمة', en: 'Introduction' },
    divine_mission: { ar: 'المهمة الإلهية', en: 'Divine Mission' },
    journey_phase: { ar: 'مرحلة الرحلة', en: 'Journey Phase' },
    encounter: { ar: 'اللقاء', en: 'Encounter' },
    test_or_trial: { ar: 'اختبار', en: 'Test/Trial' },
    test: { ar: 'اختبار', en: 'Test' },
    trial: { ar: 'ابتلاء', en: 'Trial' },
    moral_decision: { ar: 'قرار أخلاقي', en: 'Moral Decision' },
    divine_intervention: { ar: 'التدخل الإلهي', en: 'Divine Intervention' },
    outcome: { ar: 'النتيجة', en: 'Outcome' },
    reflection: { ar: 'تأمل', en: 'Reflection' },
    development: { ar: 'تطور', en: 'Development' },
    climax: { ar: 'الذروة', en: 'Climax' },
    resolution: { ar: 'الحل', en: 'Resolution' },
    rising_action: { ar: 'تصاعد الأحداث', en: 'Rising Action' },
    background: { ar: 'خلفية', en: 'Background' },
  };
  return translations[role]?.[language] || role.replace(/_/g, ' ');
}

// Calculate co-occurring themes
function getCoOccurringThemes(
  segments: StorySegment[],
  language: Language
): [string, number][] {
  const coOccurrences = new Map<string, number>();

  segments.forEach(segment => {
    const themes = segment.semantic_tags || [];
    // Generate pairs
    for (let i = 0; i < themes.length; i++) {
      for (let j = i + 1; j < themes.length; j++) {
        const pair = [themes[i], themes[j]].sort().map(t => translateTheme(t, language)).join(' + ');
        coOccurrences.set(pair, (coOccurrences.get(pair) || 0) + 1);
      }
    }
  });

  return Array.from(coOccurrences.entries())
    .filter(([_, count]) => count >= 2)
    .sort((a, b) => b[1] - a[1]);
}

export default ThematicFlow;
