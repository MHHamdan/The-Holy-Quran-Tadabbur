import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, AlertCircle, BookOpen, GitBranch } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import {
  entitiesApi,
  type EntityDetail,
  type EntityMentionOut,
  type EntityRelationOut,
} from '../lib/api';
import { ImplicitConnections } from '../components/entities/ImplicitConnections';

const REVIEW_BADGE: Record<string, { ar: string; en: string; className: string }> = {
  needs_review: {
    ar: 'بانتظار مراجعة',
    en: 'needs review',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  },
  verified: {
    ar: 'موثقة',
    en: 'verified',
    className: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  },
  rejected: {
    ar: 'مرفوضة',
    en: 'rejected',
    className: 'bg-red-50 text-red-800 border-red-200',
  },
};

function StatusBadge({ status }: { status: string }) {
  const meta = REVIEW_BADGE[status] ?? REVIEW_BADGE.needs_review;
  const { language } = useLanguageStore();
  return (
    <span
      className={`inline-block text-xs px-2 py-0.5 rounded border ${meta.className}`}
      title={meta[language]}
    >
      {meta[language]}
    </span>
  );
}

export function EntityDetailPage() {
  const { entityId = '' } = useParams<{ entityId: string }>();
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const [detail, setDetail] = useState<EntityDetail | null>(null);
  const [relations, setRelations] = useState<EntityRelationOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    setError(null);
    Promise.all([entitiesApi.get(entityId), entitiesApi.relations(entityId)])
      .then(([d, r]) => {
        if (stale) return;
        setDetail(d);
        setRelations(r.relations);
      })
      .catch((e) => !stale && setError(e?.message || 'Failed to load entity'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [entityId]);

  if (loading) {
    return (
      <div className="py-20 flex justify-center">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="max-w-3xl mx-auto py-10 px-4">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-800">{error}</div>
      </div>
    );
  }
  if (!detail) return null;

  const mentionsBySurah = new Map<number, EntityMentionOut[]>();
  for (const m of detail.mentions) {
    if (!mentionsBySurah.has(m.surahNumber)) mentionsBySurah.set(m.surahNumber, []);
    mentionsBySurah.get(m.surahNumber)!.push(m);
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6" dir={dir}>
      <Link
        to="/entities"
        className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {language === 'ar' ? 'كل الذوات' : 'All entities'}
      </Link>

      {/* Profile header */}
      <header className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm mb-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-1" dir="ltr">
              {detail.labelEnglish}
            </h1>
            <p className="text-2xl font-arabic text-gray-800" dir="rtl">
              {detail.labelArabic}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              <code className="text-xs">{detail.entityId}</code> • {detail.entityType}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <StatusBadge status={detail.reviewStatus} />
            <Link
              to={`/entities/${encodeURIComponent(entityId)}/journey`}
              className="px-3 py-1.5 rounded-md bg-emerald-600 text-white text-sm hover:bg-emerald-700 flex items-center gap-1"
            >
              <BookOpen className="w-4 h-4" />
              {language === 'ar' ? 'افتح الرحلة القرآنية' : 'Open Quran journey'}
            </Link>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
          <div className="bg-gray-50 rounded p-3">
            <div className="font-semibold text-gray-900">{detail.mentionCount}</div>
            <div className="text-xs text-gray-500">
              {language === 'ar' ? 'إجمالي الذكر' : 'Total mentions'}
            </div>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <div className="font-semibold text-gray-900">{detail.surahCount}</div>
            <div className="text-xs text-gray-500">
              {language === 'ar' ? 'سور تذكره' : 'Surahs mentioning'}
            </div>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <div className="font-semibold text-gray-900">{detail.relatedEntityIds.length}</div>
            <div className="text-xs text-gray-500">
              {language === 'ar' ? 'ذوات مرتبطة' : 'Related entities'}
            </div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mention map */}
        <section className="p-4 bg-white border border-gray-200 rounded-lg">
          <h2 className="font-semibold mb-3 flex items-center gap-1">
            <BookOpen className="w-4 h-4" />
            {language === 'ar' ? 'خريطة الذكر' : 'Mention map'}
          </h2>
          <p className="text-xs text-gray-500 mb-3">
            {language === 'ar'
              ? 'كل ذكر هنا غير مؤكد التفسير ويحتاج إلى مراجعة.'
              : 'Every mention is observational and needs scholarly review.'}
          </p>
          <div className="max-h-[60vh] overflow-y-auto divide-y">
            {Array.from(mentionsBySurah.entries())
              .sort((a, b) => a[0] - b[0])
              .map(([surahNumber, ms]) => (
                <div key={surahNumber} className="py-2">
                  <div className="font-medium text-sm text-gray-800 mb-1">
                    {language === 'ar' ? `سورة ${surahNumber}` : `Surah ${surahNumber}`}{' '}
                    <span className="text-xs text-gray-500">({ms.length})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {ms.map((m, i) => (
                      <Link
                        key={`${m.surahNumber}:${m.ayahNumber}:${i}`}
                        to={`/quran?surah=${m.surahNumber}&ayah=${m.ayahNumber}`}
                        title={`${m.mentionType} (conf ${m.confidence})`}
                        className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100"
                      >
                        {m.surahNumber}:{m.ayahNumber}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </section>

        {/* Related entities */}
        <section className="p-4 bg-white border border-gray-200 rounded-lg">
          <h2 className="font-semibold mb-3 flex items-center gap-1">
            <GitBranch className="w-4 h-4" />
            {language === 'ar' ? 'الذوات المرتبطة' : 'Connected entities'}
          </h2>
          <p className="text-xs text-gray-500 mb-3">
            {language === 'ar'
              ? 'الروابط مأخوذة من قواعد الذكر المشترك ومعجم الكيانات. كلها بانتظار مراجعة.'
              : 'Edges derive from co-mention and the seed dictionary. All needs_review.'}
          </p>
          <div className="max-h-[60vh] overflow-y-auto">
            {relations.length === 0 && (
              <p className="text-sm text-gray-500">
                {language === 'ar' ? 'لا توجد روابط بعد.' : 'No relations available yet.'}
              </p>
            )}
            <ul className="space-y-1">
              {relations.slice(0, 200).map((r, i) => (
                <li
                  key={`${r.sourceEntityId}::${r.relationType}::${r.targetEntityId}::${i}`}
                  className="text-sm py-1.5 border-b last:border-b-0 flex items-start justify-between gap-2"
                >
                  <div className="flex-1">
                    <Link
                      to={`/entities/${encodeURIComponent(r.targetEntityId)}`}
                      className="text-emerald-700 hover:text-emerald-900 font-medium"
                    >
                      {r.targetEntityId.replace(/^entity_/, '')}
                    </Link>
                    <span className="text-xs text-gray-500 mx-1.5">·</span>
                    <code className="text-xs text-gray-700">{r.relationType}</code>
                    <span className="text-xs text-gray-500 mx-1.5">·</span>
                    <span className="text-xs text-gray-500">
                      {r.evidenceReferences.length}{' '}
                      {language === 'ar' ? 'دليل' : 'evidence'}
                    </span>
                  </div>
                  <StatusBadge status={r.reviewStatus} />
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>

      <div className="mt-6">
        <ImplicitConnections entityId={entityId} />
      </div>

      <div className="mt-6 flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
        <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-amber-800">
          {language === 'ar'
            ? 'الروابط هنا للملاحظة فقط. لا تستنتج معاني تفسيرية بدون مصادر معتمدة.'
            : 'These connections are observational. Do not infer tafsir meanings without verified sources.'}
        </p>
      </div>
    </div>
  );
}
