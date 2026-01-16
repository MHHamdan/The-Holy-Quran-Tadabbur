/**
 * Narrative Insights Component
 *
 * Provides semantic analysis of story narratives:
 * - Narrative arc visualization (5-act structure)
 * - Key turning points identification
 * - Divine intervention patterns
 * - Moral lessons extraction
 */
import { useMemo } from 'react';
import { StorySegment } from '../../lib/api';
import { Language } from '../../i18n/translations';
import { Lightbulb, TrendingUp, Star, AlertTriangle, CheckCircle } from 'lucide-react';

interface NarrativeInsightsProps {
  segments: StorySegment[];
  language: Language;
  storyName: string;
}

// Narrative arc phases
const NARRATIVE_PHASES = [
  { id: 'setup', roles: ['introduction', 'background', 'setup'], icon: '1' },
  { id: 'rising', roles: ['rising_action', 'journey_phase', 'development', 'encounter'], icon: '2' },
  { id: 'climax', roles: ['climax', 'test', 'trial', 'test_or_trial', 'divine_intervention'], icon: '3' },
  { id: 'falling', roles: ['falling_action', 'outcome', 'moral_decision'], icon: '4' },
  { id: 'resolution', roles: ['resolution', 'reflection', 'conclusion'], icon: '5' },
];

export function NarrativeInsights({ segments, language, storyName: _storyName }: NarrativeInsightsProps) {
  const isArabic = language === 'ar';

  // Analyze narrative structure
  const narrativeAnalysis = useMemo(() => {
    const phases: Record<string, StorySegment[]> = {
      setup: [],
      rising: [],
      climax: [],
      falling: [],
      resolution: [],
    };

    // Categorize segments by narrative phase
    segments.forEach(segment => {
      const role = segment.narrative_role || 'unknown';
      for (const phase of NARRATIVE_PHASES) {
        if (phase.roles.includes(role)) {
          phases[phase.id].push(segment);
          break;
        }
      }
    });

    // Identify key moments
    const divineInterventions = segments.filter(s =>
      s.narrative_role === 'divine_intervention' || s.narrative_role === 'divine_mission'
    );

    const trials = segments.filter(s =>
      ['test', 'trial', 'test_or_trial'].includes(s.narrative_role || '')
    );

    const climaxMoments = segments.filter(s => s.narrative_role === 'climax');

    return {
      phases,
      divineInterventions,
      trials,
      climaxMoments,
      hasCompleteArc: Object.values(phases).every(p => p.length > 0),
    };
  }, [segments]);

  // Extract key themes and lessons
  const keyInsights = useMemo(() => {
    // Count theme occurrences
    const themeCounts = new Map<string, number>();
    segments.forEach(segment => {
      (segment.semantic_tags || []).forEach(tag => {
        themeCounts.set(tag, (themeCounts.get(tag) || 0) + 1);
      });
    });

    // Get top themes
    const topThemes = Array.from(themeCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([theme]) => theme);

    // Identify entry point
    const entryPoint = segments.find(s => s.is_entry_point) || segments[0];

    // Find resolution/reflection segments for lessons
    const reflections = segments.filter(s =>
      ['reflection', 'resolution', 'conclusion'].includes(s.narrative_role || '')
    );

    return {
      topThemes,
      entryPoint,
      reflections,
    };
  }, [segments]);

  return (
    <div className="space-y-6">
      {/* Narrative Arc Visualization */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary-600" />
          {isArabic ? 'القوس السردي' : 'Narrative Arc'}
        </h3>
        <p className="text-sm text-gray-500 mb-6">
          {isArabic
            ? 'تحليل بنية القصة وفقاً للنموذج السردي الخماسي'
            : 'Story structure analysis following the five-act narrative model'}
        </p>

        {/* Arc visualization */}
        <div className="relative">
          {/* Arc line */}
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-200 -translate-y-1/2" />

          {/* Arc curve SVG */}
          <svg className="absolute inset-0 w-full h-32" viewBox="0 0 100 40" preserveAspectRatio="none">
            <path
              d="M 0,35 Q 25,35 35,20 Q 50,0 65,20 Q 75,35 100,35"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-primary-300"
            />
          </svg>

          {/* Phase markers */}
          <div className="relative flex justify-between items-end h-32 px-4">
            {NARRATIVE_PHASES.map((phase, index) => {
              const phaseSegments = narrativeAnalysis.phases[phase.id];
              const hasContent = phaseSegments.length > 0;
              const yPosition = index === 2 ? 'top-0' : index === 0 || index === 4 ? 'bottom-0' : 'top-1/3';

              return (
                <div
                  key={phase.id}
                  className={`flex flex-col items-center ${yPosition === 'top-0' ? 'justify-start' : yPosition === 'bottom-0' ? 'justify-end' : 'justify-center'}`}
                  style={{ height: '100%' }}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                      hasContent
                        ? 'bg-primary-600 text-white shadow-lg'
                        : 'bg-gray-200 text-gray-400'
                    }`}
                    title={`${phaseSegments.length} ${isArabic ? 'مقاطع' : 'segments'}`}
                  >
                    {phase.icon}
                  </div>
                  <span className="text-xs text-gray-600 mt-2 text-center max-w-[80px]">
                    {translatePhase(phase.id, language)}
                  </span>
                  <span className="text-xs text-gray-400">
                    ({phaseSegments.length})
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {!narrativeAnalysis.hasCompleteArc && (
          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-700">
              <AlertTriangle className="w-4 h-4 inline mr-1" />
              {isArabic
                ? 'هذه القصة لا تتبع البنية السردية الكاملة - وهذا أمر طبيعي في القرآن حيث تُقدم القصص للعبرة لا للترفيه'
                : 'This story doesn\'t follow the complete narrative arc - this is normal in the Quran where stories serve lessons, not entertainment'}
            </p>
          </div>
        )}
      </div>

      {/* Key Moments */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Divine Interventions */}
        <div className="card bg-gradient-to-br from-yellow-50 to-amber-50 border-amber-200">
          <div className="flex items-center gap-2 mb-3">
            <Star className="w-5 h-5 text-amber-600" />
            <h4 className="font-semibold text-amber-900">
              {isArabic ? 'التدخلات الإلهية' : 'Divine Interventions'}
            </h4>
          </div>
          <p className="text-2xl font-bold text-amber-700 mb-2">
            {narrativeAnalysis.divineInterventions.length}
          </p>
          {narrativeAnalysis.divineInterventions.slice(0, 2).map((seg, i) => (
            <p key={i} className="text-xs text-amber-600 truncate">
              {seg.verse_reference}
            </p>
          ))}
        </div>

        {/* Trials/Tests */}
        <div className="card bg-gradient-to-br from-orange-50 to-red-50 border-orange-200">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <h4 className="font-semibold text-orange-900">
              {isArabic ? 'الاختبارات والابتلاءات' : 'Trials & Tests'}
            </h4>
          </div>
          <p className="text-2xl font-bold text-orange-700 mb-2">
            {narrativeAnalysis.trials.length}
          </p>
          {narrativeAnalysis.trials.slice(0, 2).map((seg, i) => (
            <p key={i} className="text-xs text-orange-600 truncate">
              {seg.verse_reference}
            </p>
          ))}
        </div>

        {/* Climax Moments */}
        <div className="card bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-5 h-5 text-purple-600" />
            <h4 className="font-semibold text-purple-900">
              {isArabic ? 'لحظات الذروة' : 'Climax Moments'}
            </h4>
          </div>
          <p className="text-2xl font-bold text-purple-700 mb-2">
            {narrativeAnalysis.climaxMoments.length}
          </p>
          {narrativeAnalysis.climaxMoments.slice(0, 2).map((seg, i) => (
            <p key={i} className="text-xs text-purple-600 truncate">
              {seg.verse_reference}
            </p>
          ))}
        </div>
      </div>

      {/* Key Lessons */}
      {keyInsights.reflections.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-primary-600" />
            {isArabic ? 'العبر والدروس المستفادة' : 'Key Lessons & Reflections'}
          </h3>
          <div className="space-y-3">
            {keyInsights.reflections.map((reflection, i) => {
              const summary = isArabic ? reflection.summary_ar : reflection.summary_en;
              return (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-gray-700">
                      {summary || reflection.verse_reference}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {reflection.verse_reference}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Story Entry Point */}
      {keyInsights.entryPoint && (
        <div className="card border-l-4 border-l-primary-500">
          <h4 className="font-semibold mb-2 flex items-center gap-2">
            <span className="w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-xs">
              1
            </span>
            {isArabic ? 'نقطة البداية المقترحة' : 'Suggested Starting Point'}
          </h4>
          <p className="text-sm text-gray-600 mb-2">
            {isArabic ? keyInsights.entryPoint.summary_ar : keyInsights.entryPoint.summary_en}
          </p>
          <p className="text-xs text-primary-600 font-medium">
            {keyInsights.entryPoint.verse_reference}
          </p>
        </div>
      )}

      {/* Top Themes */}
      {keyInsights.topThemes.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">
            {isArabic ? 'الموضوعات الرئيسية' : 'Primary Themes'}
          </h3>
          <div className="flex flex-wrap gap-2">
            {keyInsights.topThemes.map((theme) => (
              <span
                key={theme}
                className="bg-primary-100 text-primary-800 px-3 py-1.5 rounded-full text-sm font-medium"
              >
                {translateThemeName(theme, language)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Helper translations
function translatePhase(phase: string, language: Language): string {
  const translations: Record<string, { ar: string; en: string }> = {
    setup: { ar: 'التمهيد', en: 'Setup' },
    rising: { ar: 'الصعود', en: 'Rising' },
    climax: { ar: 'الذروة', en: 'Climax' },
    falling: { ar: 'الهبوط', en: 'Falling' },
    resolution: { ar: 'الحل', en: 'Resolution' },
  };
  return translations[phase]?.[language] || phase;
}

function translateThemeName(theme: string, language: Language): string {
  // Simplified theme translations
  const translations: Record<string, { ar: string; en: string }> = {
    patience: { ar: 'الصبر', en: 'Patience' },
    faith: { ar: 'الإيمان', en: 'Faith' },
    trust_in_allah: { ar: 'التوكل على الله', en: 'Trust in Allah' },
    forgiveness: { ar: 'المغفرة', en: 'Forgiveness' },
    mercy: { ar: 'الرحمة', en: 'Mercy' },
    justice: { ar: 'العدل', en: 'Justice' },
    obedience: { ar: 'الطاعة', en: 'Obedience' },
    repentance: { ar: 'التوبة', en: 'Repentance' },
    gratitude: { ar: 'الشكر', en: 'Gratitude' },
    humility: { ar: 'التواضع', en: 'Humility' },
    perseverance: { ar: 'المثابرة', en: 'Perseverance' },
    wisdom: { ar: 'الحكمة', en: 'Wisdom' },
    sacrifice: { ar: 'التضحية', en: 'Sacrifice' },
    miracles: { ar: 'المعجزات', en: 'Miracles' },
    prophethood: { ar: 'النبوة', en: 'Prophethood' },
  };
  return translations[theme]?.[language] || theme.replace(/_/g, ' ');
}

export default NarrativeInsights;
