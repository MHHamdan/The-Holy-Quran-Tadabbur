/**
 * DisagreementCard — M4 visualization of scholarly disagreement.
 *
 * Renders structured DisagreementObject data from the agentic /ask/agentic
 * API endpoint. Shows both scholarly positions side-by-side with equal
 * attribution; never endorses either view.
 *
 * Safety rules (mirrors agent_specs.md §3):
 * - adjudication field is always displayed as-is ("NOT_ADJUDICATED")
 * - Both positions shown in equal-weight UI (same card size, same colour)
 * - No "winner" or "majority" visual treatment on the disagreement itself
 */

import { useState } from 'react';
import { Scale, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

export interface DisagreementPosition {
  source_id: string;
  source_name: string;
  claim_summary: string;
}

export interface DisagreementData {
  disagreement_type: string;
  position_a: DisagreementPosition;
  position_b: DisagreementPosition;
  adjudication: string;
  resolution_status: string;
}

export interface ConsensusData {
  consensus_level: string;
  majority_position: DisagreementPosition | null;
  disagreements: DisagreementData[];
  display_warning: string | null;
  sources_analysed: number;
}

interface Props {
  consensus: ConsensusData;
  className?: string;
}

const CONSENSUS_LABELS: Record<string, { ar: string; en: string; color: string }> = {
  strong_consensus: {
    ar: 'إجماع قوي',
    en: 'Strong Consensus',
    color: 'text-emerald-700 bg-emerald-50 border-emerald-200',
  },
  partial_consensus: {
    ar: 'شبه إجماع',
    en: 'Partial Consensus',
    color: 'text-amber-700 bg-amber-50 border-amber-200',
  },
  significant_disagreement: {
    ar: 'خلاف علمي معتبر',
    en: 'Significant Disagreement',
    color: 'text-red-700 bg-red-50 border-red-200',
  },
  single_source_only: {
    ar: 'مصدر واحد',
    en: 'Single Source',
    color: 'text-gray-700 bg-gray-50 border-gray-200',
  },
};

const DISAGREEMENT_TYPE_LABELS: Record<string, { ar: string; en: string }> = {
  lexical: { ar: 'خلاف لغوي', en: 'Lexical Disagreement' },
  grammatical: { ar: 'خلاف نحوي', en: 'Grammatical Disagreement' },
  jurisprudential: { ar: 'خلاف فقهي', en: 'Jurisprudential Disagreement' },
  narrative: { ar: 'خلاف في الرواية', en: 'Narrative Disagreement' },
  theological: { ar: 'خلاف عقدي', en: 'Theological Disagreement' },
  variant_reading: { ar: 'خلاف قراءات', en: 'Variant Reading' },
};

export function DisagreementCard({ consensus, className }: Props) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [expanded, setExpanded] = useState(false);

  if (!consensus || consensus.consensus_level === 'single_source_only' || consensus.disagreements.length === 0) {
    return null;
  }

  const levelMeta = CONSENSUS_LABELS[consensus.consensus_level] ?? CONSENSUS_LABELS.partial_consensus;

  return (
    <div
      className={clsx('rounded-xl border overflow-hidden', className)}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:bg-gray-50 transition-colors text-start"
      >
        <Scale className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={clsx('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border', levelMeta.color)}>
              {isRtl ? levelMeta.ar : levelMeta.en}
            </span>
            <span className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>
              {isRtl
                ? `${consensus.sources_analysed} مصادر مقارَنة`
                : `${consensus.sources_analysed} sources compared`}
            </span>
          </div>
          {consensus.display_warning && (
            <p className={clsx('text-xs text-amber-700 mt-0.5 truncate', isRtl && 'font-arabic')}>
              {isRtl
                ? 'اختلف العلماء في هذه المسألة — انظر التفاصيل'
                : 'Scholars have differing views — see details'}
            </p>
          )}
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>

      {/* Expanded disagreement details */}
      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50 px-4 py-4 space-y-4">
          {consensus.disagreements.map((d, i) => {
            const typeMeta = DISAGREEMENT_TYPE_LABELS[d.disagreement_type] ?? { ar: d.disagreement_type, en: d.disagreement_type };
            return (
              <div key={i} className="space-y-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                  <span className={clsx('text-xs font-semibold text-amber-700', isRtl && 'font-arabic')}>
                    {isRtl ? typeMeta.ar : typeMeta.en}
                  </span>
                </div>

                {/* Two positions side-by-side */}
                <div className="grid grid-cols-2 gap-3">
                  {[d.position_a, d.position_b].map((pos, pi) => (
                    <div key={pi} className="bg-white rounded-lg border border-gray-200 p-3">
                      <div className={clsx('text-xs font-semibold text-gray-700 mb-1.5', isRtl && 'font-arabic')}>
                        {pos.source_name}
                      </div>
                      <p className={clsx('text-xs text-gray-600 leading-relaxed', isRtl && 'font-arabic')}>
                        {pos.claim_summary}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Adjudication notice */}
                <p className="text-[10px] text-gray-400 italic text-center">
                  {isRtl
                    ? 'المنصة تعرض كلا الرأيين دون ترجيح'
                    : 'Platform presents both views without adjudication'}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
