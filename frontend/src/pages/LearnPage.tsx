/**
 * Learning Paths — Persona-adaptive Quranic study curriculum.
 *
 * Shows a structured learning path based on the user's selected persona,
 * with milestones, steps, featured surahs, and recommended duʿā.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  GraduationCap, ChevronRight, CheckSquare, Square,
  RefreshCw, BookOpen, ExternalLink,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { usePersonaStore, PERSONA_META, type Persona } from '../stores/personaStore';
import { LEARNING_PATHS, STEP_TYPE_ICONS, STEP_TYPE_LABELS, type LearningStep } from '../data/learningPaths';
import { SURAH_NAMES } from '../data/surahNames';

const PERSONA_ORDER: Persona[] = ['new_muslim', 'student', 'researcher', 'parent', 'arabic_learner', 'memorizer'];

const COLOR_CLASSES: Record<string, { bg: string; border: string; badge: string; text: string }> = {
  emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700', text: 'text-emerald-700' },
  blue:    { bg: 'bg-blue-50',    border: 'border-blue-200',    badge: 'bg-blue-100 text-blue-700',    text: 'text-blue-700' },
  violet:  { bg: 'bg-violet-50',  border: 'border-violet-200',  badge: 'bg-violet-100 text-violet-700',text: 'text-violet-700' },
  orange:  { bg: 'bg-orange-50',  border: 'border-orange-200',  badge: 'bg-orange-100 text-orange-700',text: 'text-orange-700' },
  teal:    { bg: 'bg-teal-50',    border: 'border-teal-200',    badge: 'bg-teal-100 text-teal-700',    text: 'text-teal-700' },
  purple:  { bg: 'bg-purple-50',  border: 'border-purple-200',  badge: 'bg-purple-100 text-purple-700',text: 'text-purple-700' },
};

const CHECKED_KEY = 'tadabbur_learn_checked_v1';

function loadChecked(): Set<string> {
  try {
    const raw = localStorage.getItem(CHECKED_KEY);
    return raw ? new Set<string>(JSON.parse(raw)) : new Set();
  } catch { return new Set(); }
}

function saveChecked(set: Set<string>) {
  localStorage.setItem(CHECKED_KEY, JSON.stringify([...set]));
}

function StepRow({ step, isRtl, checked, onToggle }: {
  step: LearningStep;
  isRtl: boolean;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <div className={clsx(
      'flex items-center gap-3 py-2 px-3 rounded-lg transition-colors cursor-pointer hover:bg-gray-50',
      isRtl && 'flex-row-reverse'
    )} onClick={onToggle}>
      {checked
        ? <CheckSquare className="w-4 h-4 text-emerald-500 flex-shrink-0" />
        : <Square className="w-4 h-4 text-gray-300 flex-shrink-0" />
      }
      <span className="text-lg flex-shrink-0">{STEP_TYPE_ICONS[step.type]}</span>
      <div className="flex-1 min-w-0">
        <span className={clsx(
          'text-sm',
          checked ? 'line-through text-gray-400' : 'text-gray-700',
          isRtl && 'font-arabic'
        )}>
          {isRtl ? step.labelAr : step.labelEn}
        </span>
        <span className={clsx('ms-2 text-[10px] text-gray-400', isRtl && 'font-arabic')}>
          {isRtl ? STEP_TYPE_LABELS[step.type].ar : STEP_TYPE_LABELS[step.type].en}
        </span>
      </div>
      <Link
        to={step.route}
        onClick={e => e.stopPropagation()}
        className="flex-shrink-0 p-1.5 rounded-lg hover:bg-violet-50 transition-colors"
        title={step.route}
      >
        <ExternalLink className="w-3.5 h-3.5 text-gray-400 hover:text-violet-500" />
      </Link>
    </div>
  );
}

export function LearnPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const { persona, setPersona } = usePersonaStore();
  const [checked, setChecked] = useState<Set<string>>(loadChecked);
  const [showPersonaPicker, setShowPersonaPicker] = useState(!persona);

  const activePath = persona ? LEARNING_PATHS[persona] : null;
  const colors = activePath ? COLOR_CLASSES[activePath.color] ?? COLOR_CLASSES.teal : null;

  function toggleStep(stepId: string) {
    setChecked(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) next.delete(stepId);
      else next.add(stepId);
      saveChecked(next);
      return next;
    });
  }

  function totalSteps(path: typeof activePath) {
    if (!path) return 0;
    return path.milestones.reduce((sum, m) => sum + m.steps.length, 0);
  }

  const doneCount = activePath
    ? activePath.milestones.reduce((sum, m) => sum + m.steps.filter(s => checked.has(s.id)).length, 0)
    : 0;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center justify-between mb-6 flex-wrap gap-3', isRtl && 'flex-row-reverse')}>
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900 flex items-center gap-2', isRtl && 'font-arabic flex-row-reverse')}>
            <GraduationCap className="w-6 h-6 text-violet-600" />
            {isRtl ? 'مسار التعلم الشخصي' : 'Your Learning Path'}
          </h1>
          {activePath && (
            <p className={clsx('text-sm text-gray-500 mt-1', isRtl && 'font-arabic')}>
              {isRtl ? activePath.taglineAr : activePath.taglineEn}
            </p>
          )}
        </div>
        <button
          onClick={() => setShowPersonaPicker(v => !v)}
          className={clsx(
            'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors',
            showPersonaPicker ? 'bg-violet-600 text-white border-violet-600' : 'text-gray-600 border-gray-200 hover:border-violet-300'
          )}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {isRtl ? 'تغيير الوضع' : 'Change Mode'}
        </button>
      </div>

      {/* Persona picker */}
      {showPersonaPicker && (
        <div className="mb-6 bg-white rounded-2xl border border-gray-100 p-4">
          <p className={clsx('text-sm font-semibold text-gray-700 mb-3', isRtl && 'font-arabic')}>
            {isRtl ? 'اختر وضع التعلم المناسب لك' : 'Choose your learning mode'}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {PERSONA_ORDER.map(p => {
              const meta = PERSONA_META[p];
              const isActive = persona === p;
              return (
                <button
                  key={p}
                  onClick={() => { setPersona(p); setShowPersonaPicker(false); }}
                  className={clsx(
                    'flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all text-center',
                    isActive
                      ? 'bg-violet-600 text-white border-violet-600'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-violet-300 hover:bg-violet-50'
                  )}
                >
                  <span className="text-2xl">{meta.emoji}</span>
                  <span className={clsx('text-xs font-medium leading-tight', isRtl && 'font-arabic')}>
                    {isRtl ? meta.labelAr : meta.labelEn}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* No persona selected */}
      {!persona && (
        <div className="text-center py-12 text-gray-400">
          <GraduationCap className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className={clsx('text-sm', isRtl && 'font-arabic')}>
            {isRtl ? 'اختر وضعاً لعرض مسار التعلم المناسب لك' : 'Select a mode above to see your personalized path'}
          </p>
        </div>
      )}

      {/* Learning path */}
      {activePath && colors && (
        <div className="space-y-5">
          {/* Progress summary */}
          <div className={clsx('rounded-xl border p-4', colors.bg, colors.border)}>
            <div className={clsx('flex items-center justify-between mb-2', isRtl && 'flex-row-reverse')}>
              <span className={clsx('text-sm font-semibold', colors.text, isRtl && 'font-arabic')}>
                {PERSONA_META[activePath.persona].emoji} {isRtl ? PERSONA_META[activePath.persona].labelAr : PERSONA_META[activePath.persona].labelEn}
              </span>
              <span className="text-xs text-gray-500">
                {doneCount}/{totalSteps(activePath)} {isRtl ? 'خطوة' : 'steps'}
              </span>
            </div>
            <div className="w-full h-2 bg-white/60 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', `bg-${activePath.color}-500`)}
                style={{ width: `${totalSteps(activePath) > 0 ? (doneCount / totalSteps(activePath)) * 100 : 0}%` }}
              />
            </div>
          </div>

          {/* Milestones */}
          {activePath.milestones.map((milestone) => {
            const milestoneDone = milestone.steps.every(s => checked.has(s.id));
            const milestonePct = Math.round((milestone.steps.filter(s => checked.has(s.id)).length / milestone.steps.length) * 100);
            return (
              <div key={milestone.id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                <div className="px-4 pt-4 pb-2">
                  <div className={clsx('flex items-start gap-2 mb-1', isRtl && 'flex-row-reverse')}>
                    <span className={clsx(
                      'w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] font-bold mt-0.5',
                      milestoneDone ? 'bg-emerald-100 text-emerald-700' : `${colors.badge}`
                    )}>
                      {milestoneDone ? '✓' : milestone.id.split('_m')[1]}
                    </span>
                    <div className="flex-1 min-w-0">
                      <h3 className={clsx('font-semibold text-gray-800 text-sm', isRtl && 'font-arabic')}>
                        {isRtl ? milestone.titleAr : milestone.titleEn}
                      </h3>
                      <p className={clsx('text-xs text-gray-500 mt-0.5', isRtl && 'font-arabic')}>
                        {isRtl ? milestone.descAr : milestone.descEn}
                      </p>
                    </div>
                    <span className={clsx('text-[10px] px-2 py-0.5 rounded-full flex-shrink-0', colors.badge)}>
                      {isRtl ? milestone.estimatedDaysAr : milestone.estimatedDaysEn}
                    </span>
                  </div>
                  {milestonePct > 0 && (
                    <div className="mt-2 w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                      <div className={clsx('h-full rounded-full', `bg-${activePath.color}-400`)}
                        style={{ width: `${milestonePct}%` }} />
                    </div>
                  )}
                </div>
                <div className="px-2 pb-3 divide-y divide-gray-50">
                  {milestone.steps.map(step => (
                    <StepRow
                      key={step.id}
                      step={step}
                      isRtl={isRtl}
                      checked={checked.has(step.id)}
                      onToggle={() => toggleStep(step.id)}
                    />
                  ))}
                </div>
              </div>
            );
          })}

          {/* Featured Surahs */}
          <div className="bg-white rounded-2xl border border-gray-100 p-4">
            <h3 className={clsx('text-sm font-semibold text-gray-700 mb-3', isRtl && 'font-arabic flex-row-reverse flex items-center gap-2')}>
              <BookOpen className="w-4 h-4 text-violet-500 inline me-1" />
              {isRtl ? 'السور المُوصى بها' : 'Featured Surahs'}
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {[...new Set(activePath.featuredSurahs)].map(s => {
                const name = SURAH_NAMES[s - 1];
                return (
                  <Link
                    key={s}
                    to={`/quran/${s}`}
                    className={clsx(
                      'flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border transition-colors',
                      colors.badge, colors.border, 'hover:opacity-80'
                    )}
                  >
                    <span className="font-semibold">{s}</span>
                    <span className={isRtl ? 'font-arabic' : ''}>{isRtl ? name.ar : name.en}</span>
                    <ChevronRight className={clsx('w-3 h-3', isRtl && 'rotate-180')} />
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Suggested Juz */}
          <div className="bg-white rounded-2xl border border-gray-100 p-4">
            <h3 className={clsx('text-sm font-semibold text-gray-700 mb-3', isRtl && 'font-arabic flex-row-reverse flex items-center gap-2')}>
              {isRtl ? 'الأجزاء المُوصى بها' : 'Suggested Juz'}
            </h3>
            <div className="flex flex-wrap gap-2">
              {activePath.suggestedJuz.map(j => (
                <Link
                  key={j}
                  to="/juz"
                  className={clsx('text-xs px-3 py-1.5 rounded-lg border font-semibold transition-colors', colors.badge, colors.border, 'hover:opacity-80')}
                >
                  {isRtl ? `الجزء ${j}` : `Juz ${j}`}
                </Link>
              ))}
            </div>
          </div>

          {/* Reset progress */}
          {doneCount > 0 && (
            <div className="text-center pt-2">
              <button
                onClick={() => {
                  if (window.confirm(isRtl ? 'إعادة تعيين تقدم التعلم؟' : 'Reset learning progress?')) {
                    const next = new Set<string>();
                    saveChecked(next);
                    setChecked(next);
                  }
                }}
                className="text-xs text-gray-400 hover:text-red-500 transition-colors"
              >
                {isRtl ? 'إعادة تعيين التقدم' : 'Reset progress'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
