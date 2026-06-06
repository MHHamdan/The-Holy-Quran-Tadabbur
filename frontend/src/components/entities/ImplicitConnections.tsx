/**
 * Phase U — Implicit-connection panel.
 *
 * Renders three sections for an entity:
 *   - implicit mentions (pronoun/title/family/role/context)
 *   - coreference chains (local_passage / surah_level / cross_surah_candidate)
 *   - implicit (coreference-derived) entity links
 *
 * Every record displays its reviewStatus badge + warnings. Clicking "Explain
 * this link" opens the explainer for that mention.
 */

import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, EyeOff, Loader2, GitBranch, MessageSquare } from 'lucide-react';
import {
  entitiesApi,
  type CoreferenceChainOut,
  type CoreferenceMentionOut,
  type ImplicitLinkOut,
  type ResolveCoreferenceResponse,
} from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';

type ConfidenceFilter = 'all' | 'high' | 'low';
type SurfaceFilter = 'all' | 'pronoun' | 'family' | 'title' | 'role' | 'context';

const SURFACE_LABEL: Record<string, { ar: string; en: string }> = {
  pronoun: { ar: 'ضمير', en: 'pronoun' },
  possessive_pronoun: { ar: 'ضمير ملكية', en: 'possessive pronoun' },
  title: { ar: 'لقب', en: 'title' },
  family_reference: { ar: 'إحالة عائلية', en: 'family reference' },
  role_reference: { ar: 'إحالة بدور', en: 'role reference' },
  demonstrative: { ar: 'اسم إشارة', en: 'demonstrative' },
  implicit_context: { ar: 'سياق ضمني', en: 'implicit context' },
  explicit_name: { ar: 'اسم صريح', en: 'explicit name' },
};

const EDGE_TYPE_LABEL: Record<string, { ar: string; en: string }> = {
  IMPLICITLY_REFERS_TO: { ar: 'يشير إليه ضمنًا', en: 'implicitly refers to' },
  PRONOUN_REFERS_TO: { ar: 'إحالة بضمير', en: 'pronoun refers to' },
  TITLE_REFERS_TO: { ar: 'إحالة بلقب', en: 'title refers to' },
  FAMILY_REFERENCE_TO: { ar: 'إحالة عائلية', en: 'family reference to' },
  CONTEXTUAL_ENTITY_LINK: { ar: 'رابط سياقي', en: 'contextual link' },
  STORY_OBJECT_LINK: { ar: 'رابط بالشيء/الحيوان', en: 'story-object link' },
};

function ReviewBadge({ status }: { status: string }) {
  const { language } = useLanguageStore();
  const meta =
    status === 'verified'
      ? { ar: 'موثقة', en: 'verified', cls: 'bg-emerald-50 text-emerald-800 border-emerald-200' }
      : status === 'rejected'
      ? { ar: 'مرفوضة', en: 'rejected', cls: 'bg-red-50 text-red-800 border-red-200' }
      : { ar: 'بانتظار مراجعة', en: 'needs review', cls: 'bg-amber-50 text-amber-800 border-amber-200' };
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${meta.cls}`}>{meta[language]}</span>
  );
}

export function ImplicitConnections({ entityId }: { entityId: string }) {
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';

  const [mentions, setMentions] = useState<CoreferenceMentionOut[]>([]);
  const [chains, setChains] = useState<CoreferenceChainOut[]>([]);
  const [links, setLinks] = useState<ImplicitLinkOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [surfaceFilter, setSurfaceFilter] = useState<SurfaceFilter>('all');
  const [confFilter, setConfFilter] = useState<ConfidenceFilter>('all');
  const [reviewFilter, setReviewFilter] = useState<'all' | 'needs_review' | 'verified'>('all');

  // explain panel state
  const [explainFor, setExplainFor] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<ResolveCoreferenceResponse | null>(null);
  const [explainLoading, setExplainLoading] = useState(false);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    setError(null);
    Promise.all([
      entitiesApi.coreference(entityId, { min_confidence: 0 }),
      entitiesApi.coreferenceChains(entityId),
      entitiesApi.implicitLinks(entityId),
    ])
      .then(([m, c, l]) => {
        if (stale) return;
        setMentions(m.mentions);
        setChains(c.chains);
        setLinks(l.links);
      })
      .catch((e) => !stale && setError(e?.message || 'Failed to load implicit links'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [entityId]);

  const visibleMentions = useMemo(() => {
    return mentions.filter((m) => {
      if (reviewFilter !== 'all' && m.reviewStatus !== reviewFilter) return false;
      if (confFilter === 'high' && m.confidence < 0.7) return false;
      if (confFilter === 'low' && m.confidence >= 0.7) return false;
      if (surfaceFilter !== 'all') {
        switch (surfaceFilter) {
          case 'pronoun':
            if (m.surfaceType !== 'pronoun' && m.surfaceType !== 'possessive_pronoun') return false;
            break;
          case 'family':
            if (m.surfaceType !== 'family_reference') return false;
            break;
          case 'title':
            if (m.surfaceType !== 'title') return false;
            break;
          case 'role':
            if (m.surfaceType !== 'role_reference') return false;
            break;
          case 'context':
            if (m.surfaceType !== 'implicit_context' && m.surfaceType !== 'demonstrative') return false;
            break;
        }
      }
      return true;
    });
  }, [mentions, surfaceFilter, confFilter, reviewFilter]);

  async function openExplain(mentionId: string) {
    setExplainFor(mentionId);
    setExplanation(null);
    setExplainLoading(true);
    try {
      const r = await entitiesApi.resolveCoreferenceExplanation({
        entityId,
        mentionId,
        language,
        sourceIds: [],
      });
      setExplanation(r);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load explanation';
      setExplanation({
        explanationArabic: msg,
        explanationEnglish: msg,
        candidateEntityId: entityId,
        method: 'rule_pattern',
        confidence: 0,
        surfaceType: '',
        evidenceReferences: [],
        sourceIds: [],
        warnings: [msg],
        reviewStatus: 'needs_review',
      });
    } finally {
      setExplainLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex justify-center">
        <Loader2 className="w-5 h-5 text-emerald-600 animate-spin" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">{error}</div>
    );
  }

  const hasAny = mentions.length + chains.length + links.length > 0;

  return (
    <section className="p-4 bg-white border border-gray-200 rounded-lg" dir={dir}>
      <div className="flex items-center gap-2 mb-2">
        <EyeOff className="w-4 h-4 text-amber-700" />
        <h2 className="font-semibold text-gray-900">
          {language === 'ar' ? 'صلات ضمنية' : 'Implicit connections'}
        </h2>
        {hasAny && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
            {language === 'ar' ? 'تحتاج إلى مراجعة' : 'require review'}
          </span>
        )}
      </div>
      <p className="text-xs text-gray-500 mb-3">
        {language === 'ar'
          ? 'لا يقدّم النظام تفسيرًا. كل ربط ضمني (ضمائر، ألقاب، إحالات عائلية، سياق قصص) يُعرض بصفته اقتراحًا للمراجعة العلمية.'
          : 'No tafsir is generated. Each implicit link (pronouns, titles, family references, story context) is shown as a scholar-review candidate, not as a finding.'}
      </p>

      {/* Reviewer-mode filters */}
      <div className="flex flex-wrap gap-2 mb-4 text-xs">
        <select
          value={surfaceFilter}
          onChange={(e) => setSurfaceFilter(e.target.value as SurfaceFilter)}
          className="px-2 py-1 border border-gray-300 rounded bg-white"
        >
          <option value="all">{language === 'ar' ? 'كل الأنواع' : 'all surfaces'}</option>
          <option value="pronoun">pronoun</option>
          <option value="family">family</option>
          <option value="title">title</option>
          <option value="role">role</option>
          <option value="context">context</option>
        </select>
        <select
          value={confFilter}
          onChange={(e) => setConfFilter(e.target.value as ConfidenceFilter)}
          className="px-2 py-1 border border-gray-300 rounded bg-white"
        >
          <option value="all">{language === 'ar' ? 'كل الثقة' : 'all confidence'}</option>
          <option value="high">high (≥0.7)</option>
          <option value="low">low (&lt;0.7)</option>
        </select>
        <select
          value={reviewFilter}
          onChange={(e) => setReviewFilter(e.target.value as 'all' | 'needs_review' | 'verified')}
          className="px-2 py-1 border border-gray-300 rounded bg-white"
        >
          <option value="all">{language === 'ar' ? 'كل الحالات' : 'all statuses'}</option>
          <option value="needs_review">needs_review</option>
          <option value="verified">verified</option>
        </select>
      </div>

      {/* Implicit mentions */}
      <div className="mb-5">
        <h3 className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
          <MessageSquare className="w-3.5 h-3.5" />
          {language === 'ar' ? 'إحالات ضمنية' : 'Implicit mentions'} ({visibleMentions.length})
        </h3>
        {visibleMentions.length === 0 && (
          <p className="text-xs text-gray-500">
            {language === 'ar' ? 'لا توجد إحالات ضمنية مطابقة.' : 'No implicit mentions matching the filters.'}
          </p>
        )}
        <ul className="space-y-1">
          {visibleMentions.slice(0, 100).map((m) => (
            <li
              key={m.mentionId}
              className="text-sm py-1.5 border-b last:border-b-0 flex items-start justify-between gap-2"
            >
              <div className="flex-1">
                <span className="font-mono text-xs text-gray-700">
                  {m.surahNumber}:{m.ayahNumber}
                </span>
                <span className="mx-1.5 text-gray-400">·</span>
                <span className="text-xs">
                  {SURFACE_LABEL[m.surfaceType]?.[language] ?? m.surfaceType}
                </span>
                {m.surfaceText && (
                  <span className="mx-1.5 text-gray-400">·</span>
                )}
                {m.surfaceText && (
                  <span className="font-arabic text-base text-gray-900" dir="rtl">
                    {m.surfaceText}
                  </span>
                )}
                <span className="mx-1.5 text-gray-400">·</span>
                <span className="text-xs text-gray-600">conf {m.confidence}</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => openExplain(m.mentionId)}
                  className="text-xs text-emerald-700 hover:text-emerald-900"
                >
                  {language === 'ar' ? 'لماذا؟' : 'explain'}
                </button>
                <ReviewBadge status={m.reviewStatus} />
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Coreference chains */}
      <div className="mb-5">
        <h3 className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
          <GitBranch className="w-3.5 h-3.5" />
          {language === 'ar' ? 'سلاسل الإحالة' : 'Coreference chains'} ({chains.length})
        </h3>
        {chains.length === 0 && (
          <p className="text-xs text-gray-500">
            {language === 'ar' ? 'لا توجد سلاسل.' : 'No coreference chains yet.'}
          </p>
        )}
        <ul className="space-y-1.5">
          {chains.map((c) => (
            <li key={c.chainId} className="text-sm py-1.5 border-b last:border-b-0">
              <div className="flex items-center justify-between gap-2">
                <div className="flex-1">
                  <span className="text-xs font-mono text-gray-700">{c.chainType}</span>
                  <span className="mx-1.5 text-gray-400">·</span>
                  <span className="text-xs">
                    {c.ayahRangeStart} → {c.ayahRangeEnd}
                  </span>
                  <span className="mx-1.5 text-gray-400">·</span>
                  <span className="text-xs text-gray-600">
                    {c.mentions.length} {language === 'ar' ? 'إحالة' : 'mentions'}
                  </span>
                </div>
                <ReviewBadge status={c.reviewStatus} />
              </div>
              {c.warnings.length > 0 && (
                <p className="text-xs text-amber-700 mt-0.5">{c.warnings[0]}</p>
              )}
            </li>
          ))}
        </ul>
      </div>

      {/* Implicit entity links */}
      <div>
        <h3 className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
          <AlertCircle className="w-3.5 h-3.5" />
          {language === 'ar' ? 'روابط ضمنية بين الكيانات' : 'Implicit entity links'} ({links.length})
        </h3>
        {links.length === 0 && (
          <p className="text-xs text-gray-500">
            {language === 'ar' ? 'لا توجد روابط ضمنية.' : 'No implicit entity links derived yet.'}
          </p>
        )}
        <ul className="space-y-1">
          {links.map((l, i) => (
            <li
              key={`${l.sourceEntityId}::${l.edgeType}::${l.targetEntityId}::${i}`}
              className="text-sm py-1 border-b last:border-b-0 flex items-start justify-between gap-2"
            >
              <div className="flex-1">
                <code className="text-xs text-gray-700">{l.sourceEntityId}</code>
                <span className="mx-1.5 text-gray-400">→</span>
                <span className="text-xs text-emerald-700">
                  {EDGE_TYPE_LABEL[l.edgeType]?.[language] ?? l.edgeType}
                </span>
                <span className="mx-1.5 text-gray-400">→</span>
                <code className="text-xs text-gray-700">{l.targetEntityId}</code>
                <span className="mx-1.5 text-gray-400">·</span>
                <span className="text-xs text-gray-600">
                  {l.evidenceReferences.length} {language === 'ar' ? 'دليل' : 'evidence'}
                </span>
              </div>
              <ReviewBadge status={l.reviewStatus} />
            </li>
          ))}
        </ul>
      </div>

      {/* Explain modal-ish panel */}
      {explainFor && (
        <div className="mt-5 p-3 bg-emerald-50/40 border border-emerald-200 rounded">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold">
              {language === 'ar' ? 'لماذا اقتُرح هذا الربط؟' : 'Why was this link suggested?'}
            </h4>
            <button
              type="button"
              onClick={() => {
                setExplainFor(null);
                setExplanation(null);
              }}
              className="text-xs text-gray-500"
            >
              {language === 'ar' ? 'إغلاق' : 'close'}
            </button>
          </div>
          {explainLoading && (
            <Loader2 className="w-4 h-4 animate-spin text-emerald-700" />
          )}
          {explanation && (
            <div className="space-y-2">
              <p dir="rtl" className="font-arabic text-gray-800 text-sm">
                {explanation.explanationArabic}
              </p>
              <p dir="ltr" className="text-gray-800 text-sm">
                {explanation.explanationEnglish}
              </p>
              {explanation.warnings.length > 0 && (
                <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2">
                  <ul className="list-disc list-inside space-y-0.5">
                    {explanation.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
              {explanation.evidenceReferences.length > 0 && (
                <p className="text-xs text-gray-600">
                  {language === 'ar' ? 'الأدلة' : 'Evidence'}:{' '}
                  {explanation.evidenceReferences.map(
                    (e) => `${e.surahNumber}:${e.ayahStart}`
                  ).join(' • ')}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
