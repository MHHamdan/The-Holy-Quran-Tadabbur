import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, AlertCircle, BookOpen, GitBranch, Tag } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import {
  topicsApi,
  type TopicAyahLinkOut,
  type TopicDetailResponse,
  type TopicRelatedResponse,
} from '../lib/api';

function ReviewBadge({ status }: { status: string }) {
  const { language } = useLanguageStore();
  const meta =
    status === 'verified'
      ? { ar: 'موثق', en: 'verified', cls: 'bg-emerald-50 text-emerald-800 border-emerald-200' }
      : status === 'rejected'
      ? { ar: 'مرفوض', en: 'rejected', cls: 'bg-red-50 text-red-800 border-red-200' }
      : { ar: 'بانتظار مراجعة', en: 'needs review', cls: 'bg-amber-50 text-amber-800 border-amber-200' };
  return <span className={`text-xs px-2 py-0.5 rounded border ${meta.cls}`}>{meta[language]}</span>;
}

export function TopicDetailPage() {
  const { topicId = '' } = useParams<{ topicId: string }>();
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const [detail, setDetail] = useState<TopicDetailResponse | null>(null);
  const [links, setLinks] = useState<TopicAyahLinkOut[]>([]);
  const [related, setRelated] = useState<TopicRelatedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [linkTypeFilter, setLinkTypeFilter] = useState<string>('');

  useEffect(() => {
    let stale = false;
    setLoading(true);
    setError(null);
    Promise.all([
      topicsApi.get(topicId),
      topicsApi.ayahs(topicId, { limit: 2000 }),
      topicsApi.related(topicId),
    ])
      .then(([d, a, r]) => {
        if (stale) return;
        setDetail(d);
        setLinks(a.links);
        setRelated(r);
      })
      .catch((e) => !stale && setError(e?.message || 'Failed to load topic'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [topicId]);

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

  const linkTypes = Array.from(new Set(links.map((l) => l.linkType))).sort();
  const visibleLinks = linkTypeFilter ? links.filter((l) => l.linkType === linkTypeFilter) : links;
  const linksBySurah = new Map<number, TopicAyahLinkOut[]>();
  for (const l of visibleLinks) {
    if (!linksBySurah.has(l.surahNumber)) linksBySurah.set(l.surahNumber, []);
    linksBySurah.get(l.surahNumber)!.push(l);
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6" dir={dir}>
      <Link to="/topics" className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900 mb-3">
        <ArrowLeft className="w-4 h-4" />
        {language === 'ar' ? 'كل المواضيع' : 'All topics'}
      </Link>

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
              <code className="text-xs">{detail.topicId}</code> · {detail.topicType}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <ReviewBadge status={detail.reviewStatus} />
            <Link
              to={`/topics/${encodeURIComponent(topicId)}/journey`}
              className="px-3 py-1.5 rounded-md bg-emerald-600 text-white text-sm hover:bg-emerald-700 flex items-center gap-1"
            >
              <BookOpen className="w-4 h-4" />
              {language === 'ar' ? 'افتح الرحلة' : 'Open journey'}
            </Link>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
          <div className="bg-gray-50 rounded p-3">
            <div className="font-semibold text-gray-900">{detail.ayahCount}</div>
            <div className="text-xs text-gray-500">{language === 'ar' ? 'آيات' : 'Ayah links'}</div>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <div className="font-semibold text-gray-900">{detail.surahCount}</div>
            <div className="text-xs text-gray-500">{language === 'ar' ? 'سور' : 'Surahs'}</div>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <div className="font-semibold text-gray-900">{related?.relatedTopicIds.length ?? 0}</div>
            <div className="text-xs text-gray-500">{language === 'ar' ? 'مواضيع مرتبطة' : 'Related topics'}</div>
          </div>
        </div>
        {detail.warnings.length > 0 && (
          <div className="mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
            {detail.warnings[0]}
          </div>
        )}
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="p-4 bg-white border border-gray-200 rounded-lg">
          <h2 className="font-semibold mb-3 flex items-center gap-1">
            <Tag className="w-4 h-4" />
            {language === 'ar' ? 'الروابط بالآيات' : 'Ayah links'}
          </h2>
          <div className="flex flex-wrap gap-1.5 mb-3 text-xs">
            <button
              onClick={() => setLinkTypeFilter('')}
              className={`px-2 py-0.5 rounded border ${
                linkTypeFilter === ''
                  ? 'bg-emerald-600 text-white border-emerald-700'
                  : 'bg-white border-gray-300'
              }`}
            >
              {language === 'ar' ? 'الكل' : 'all'}
            </button>
            {linkTypes.map((lt) => (
              <button
                key={lt}
                onClick={() => setLinkTypeFilter(lt)}
                className={`px-2 py-0.5 rounded border ${
                  linkTypeFilter === lt
                    ? 'bg-emerald-600 text-white border-emerald-700'
                    : 'bg-white border-gray-300'
                }`}
              >
                {lt}
              </button>
            ))}
          </div>
          <div className="max-h-[60vh] overflow-y-auto divide-y">
            {Array.from(linksBySurah.entries())
              .sort((a, b) => a[0] - b[0])
              .map(([s, ls]) => (
                <div key={s} className="py-2">
                  <div className="font-medium text-sm text-gray-800 mb-1">
                    {language === 'ar' ? `سورة ${s}` : `Surah ${s}`}{' '}
                    <span className="text-xs text-gray-500">({ls.length})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {ls.map((l, i) => (
                      <Link
                        key={`${l.surahNumber}:${l.ayahNumber}:${i}`}
                        to={`/quran/${l.surahNumber}`}
                        title={`${l.linkType} · conf ${l.confidence}`}
                        className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100"
                      >
                        {l.surahNumber}:{l.ayahNumber}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </section>

        <section className="p-4 bg-white border border-gray-200 rounded-lg">
          <h2 className="font-semibold mb-3 flex items-center gap-1">
            <GitBranch className="w-4 h-4" />
            {language === 'ar' ? 'الروابط المتقاطعة' : 'Cross-links'}
          </h2>
          {related && (
            <div className="space-y-3 text-sm">
              <div>
                <h3 className="font-medium text-gray-800 mb-1">
                  {language === 'ar' ? 'مواضيع مرتبطة' : 'Related topics'}
                </h3>
                {related.relatedTopicIds.length === 0 && (
                  <p className="text-xs text-gray-500">
                    {language === 'ar' ? 'لا يوجد.' : 'None.'}
                  </p>
                )}
                <div className="flex flex-wrap gap-1.5">
                  {related.relatedTopicIds.slice(0, 30).map((tid) => (
                    <Link
                      key={tid}
                      to={`/topics/${encodeURIComponent(tid)}`}
                      className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100"
                    >
                      {tid.replace(/^topic_/, '')}
                    </Link>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-medium text-gray-800 mb-1">
                  {language === 'ar' ? 'كيانات مشتركة' : 'Shared entities'}
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {related.sharedEntityIds.length === 0 && (
                    <p className="text-xs text-gray-500">
                      {language === 'ar' ? 'لا يوجد.' : 'None.'}
                    </p>
                  )}
                  {related.sharedEntityIds.slice(0, 20).map((eid) => (
                    <Link
                      key={eid}
                      to={`/entities/${encodeURIComponent(eid)}`}
                      className="text-xs px-2 py-0.5 rounded bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100"
                    >
                      {eid.replace(/^entity_/, '')}
                    </Link>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-medium text-gray-800 mb-1">
                  {language === 'ar' ? 'قصص مشتركة' : 'Shared stories'}
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {related.sharedStoryIds.length === 0 && (
                    <p className="text-xs text-gray-500">
                      {language === 'ar' ? 'لا يوجد.' : 'None.'}
                    </p>
                  )}
                  {related.sharedStoryIds.slice(0, 20).map((sid) => (
                    <span
                      key={sid}
                      className="text-xs px-2 py-0.5 rounded bg-gray-50 text-gray-700 border border-gray-200"
                    >
                      {sid.replace(/^story_/, '')}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-medium text-gray-800 mb-1">
                  {language === 'ar' ? 'مشاعر مرتبطة' : 'Related emotions'}
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {related.sharedEmotionIds.length === 0 && (
                    <p className="text-xs text-gray-500">
                      {language === 'ar' ? 'لا يوجد.' : 'None.'}
                    </p>
                  )}
                  {related.sharedEmotionIds.slice(0, 20).map((eid) => (
                    <span
                      key={eid}
                      className="text-xs px-2 py-0.5 rounded bg-violet-50 text-violet-800 border border-violet-200"
                    >
                      {eid.replace(/^emotion_/, '')}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
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
