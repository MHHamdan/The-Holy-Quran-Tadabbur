import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, AlertCircle } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { topicsApi, type SurahTopicsResponse } from '../lib/api';

export function SurahTopicsPage() {
  const { surahNo: rawSurah = '1' } = useParams<{ surahNo: string }>();
  const surahNo = useMemo(() => {
    const n = Number(rawSurah);
    if (!Number.isFinite(n) || n < 1 || n > 114) return 1;
    return n;
  }, [rawSurah]);
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';

  const [data, setData] = useState<SurahTopicsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    setError(null);
    topicsApi
      .surahTopics(surahNo)
      .then((r) => !stale && setData(r))
      .catch((e) => !stale && setError(e?.message || 'Failed to load surah topics'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [surahNo]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-6" dir={dir}>
      <Link to="/topics" className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900 mb-3">
        <ArrowLeft className="w-4 h-4" />
        {language === 'ar' ? 'كل المواضيع' : 'All topics'}
      </Link>

      <header className="mb-5">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          {language === 'ar' ? `مواضيع سورة ${surahNo}` : `Topics in Surah ${surahNo}`}
        </h1>
        <p className="text-sm text-gray-500">
          {language === 'ar'
            ? 'الروابط بين الموضوعات والآيات لهذه السورة. كل ربط بحاجة إلى مراجعة علمية.'
            : 'Candidate topic links for this surah. Every link needs scholarly review.'}
        </p>
      </header>

      {/* Surah picker */}
      <div className="mb-5 flex flex-wrap gap-1">
        {Array.from({ length: 114 }, (_, i) => i + 1).map((n) => (
          <Link
            key={n}
            to={`/surah-topics/${n}`}
            className={`text-xs px-2 py-0.5 rounded border ${
              n === surahNo
                ? 'bg-emerald-600 text-white border-emerald-700'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {n}
          </Link>
        ))}
      </div>

      {loading && (
        <div className="py-20 flex justify-center">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
        </div>
      )}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-800">{error}</div>
      )}

      {!loading && !error && data && (
        <>
          <p className="text-sm text-gray-600 mb-4">
            {language === 'ar'
              ? `إجمالي المواضيع: ${data.totalTopics}`
              : `Total topics: ${data.totalTopics}`}
          </p>
          {data.topics.length === 0 && (
            <p className="text-sm text-gray-500">
              {language === 'ar' ? 'لا توجد مواضيع في هذه السورة بعد.' : 'No topic links for this surah yet.'}
            </p>
          )}
          <ul className="space-y-2">
            {data.topics.map((t) => (
              <li key={t.topicId} className="p-3 bg-white border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <Link
                    to={`/topics/${encodeURIComponent(t.topicId)}`}
                    className="font-semibold text-gray-900 hover:text-emerald-700"
                  >
                    {language === 'ar' ? t.labelArabic : t.labelEnglish}
                  </Link>
                  <span className="text-xs text-gray-500">
                    {t.ayahCount} {language === 'ar' ? 'آية' : 'ayahs'}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {t.ayahs.slice(0, 60).map((a) => (
                    <span
                      key={a}
                      className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200"
                    >
                      {surahNo}:{a}
                    </span>
                  ))}
                  {t.ayahs.length > 60 && (
                    <span className="text-xs text-gray-500">
                      {language === 'ar' ? `+${t.ayahs.length - 60}` : `+${t.ayahs.length - 60} more`}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

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
