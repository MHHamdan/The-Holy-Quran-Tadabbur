import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, AlertCircle, BookOpen, Layers } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import {
  asmaApi,
  type AsmaDetailResponse,
  type AsmaOccurrencesResponse,
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

export function AsmaAllahDetailPage() {
  const { nameId = '' } = useParams<{ nameId: string }>();
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';

  const [detail, setDetail] = useState<AsmaDetailResponse | null>(null);
  const [occs, setOccs] = useState<AsmaOccurrencesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [includeExcluded, setIncludeExcluded] = useState(false);
  const [surahFilter, setSurahFilter] = useState<number | ''>('');

  useEffect(() => {
    let stale = false;
    setLoading(true);
    setError(null);
    Promise.all([
      asmaApi.get(nameId),
      asmaApi.occurrences(nameId, { include_excluded: true, limit: 1000 }),
    ])
      .then(([d, o]) => {
        if (stale) return;
        setDetail(d);
        setOccs(o);
      })
      .catch((e) => !stale && setError(e?.message || 'Failed to load Name'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [nameId]);

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

  const filteredOccs =
    occs?.occurrences.filter((o) => {
      if (!includeExcluded && !o.counted) return false;
      if (surahFilter && o.surahNumber !== Number(surahFilter)) return false;
      return true;
    }) ?? [];

  const surahsInData = Array.from(new Set((occs?.occurrences ?? []).map((o) => o.surahNumber))).sort(
    (a, b) => a - b
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-6" dir={dir}>
      <Link to="/themes/asma" className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900 mb-3">
        <ArrowLeft className="w-4 h-4" />
        {language === 'ar' ? 'كل الأسماء' : 'All Names'}
      </Link>

      {/* Header card */}
      <header className="p-8 bg-gradient-to-br from-emerald-50 to-white border border-emerald-200 rounded-xl mb-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <p className="font-arabic text-5xl text-gray-900 leading-tight mb-2" dir="rtl">
              {detail.arabicName}
            </p>
            <p className="text-lg text-gray-700" dir="ltr">
              {detail.transliteration}
            </p>
            {detail.englishName && (
              <p className="text-sm text-gray-500 mt-1" dir="ltr">
                {detail.englishName}
              </p>
            )}
            <p className="text-xs text-gray-400 mt-2">
              <code>{detail.nameId}</code> · {detail.category}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <ReviewBadge status={detail.reviewStatus} />
            <div className="text-right">
              <div className="text-2xl font-semibold text-emerald-700">{detail.occurrenceCount}</div>
              <div className="text-xs text-gray-500">
                {language === 'ar' ? `موضع · ${detail.surahCount} سورة` : `occurrences · ${detail.surahCount} surahs`}
              </div>
            </div>
          </div>
        </div>

        {/* Meaning — verified-only */}
        <div className="mt-6">
          {detail.meaningArabic || detail.meaningEnglish ? (
            <div className="p-3 bg-white border border-emerald-200 rounded-md">
              {detail.meaningArabic && (
                <p className="font-arabic text-gray-900 text-base" dir="rtl">
                  {detail.meaningArabic}
                </p>
              )}
              {detail.meaningEnglish && (
                <p className="text-gray-800 text-sm mt-1" dir="ltr">
                  {detail.meaningEnglish}
                </p>
              )}
            </div>
          ) : (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-md flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-amber-800">
                {language === 'ar' ? detail.missingMeaningMessage.ar : detail.missingMeaningMessage.en}
              </p>
            </div>
          )}
        </div>

        {/* Warnings */}
        {detail.warnings.length > 0 && (
          <ul className="mt-3 text-xs text-amber-800 list-disc list-inside space-y-0.5">
            {detail.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        )}
      </header>

      {/* First / Last occurrence + basmalah policy */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div className="p-3 bg-white border border-gray-200 rounded">
          <div className="text-xs text-gray-500 mb-1">
            {language === 'ar' ? 'أول موضع' : 'First occurrence'}
          </div>
          <div className="font-mono text-sm">
            {detail.firstOccurrence
              ? `${detail.firstOccurrence.surahNumber}:${detail.firstOccurrence.ayahStart}`
              : '—'}
          </div>
        </div>
        <div className="p-3 bg-white border border-gray-200 rounded">
          <div className="text-xs text-gray-500 mb-1">
            {language === 'ar' ? 'آخر موضع' : 'Last occurrence'}
          </div>
          <div className="font-mono text-sm">
            {detail.lastOccurrence
              ? `${detail.lastOccurrence.surahNumber}:${detail.lastOccurrence.ayahStart}`
              : '—'}
          </div>
        </div>
        <div className="p-3 bg-white border border-gray-200 rounded">
          <div className="text-xs text-gray-500 mb-1">
            {language === 'ar' ? 'استثناءات البسملة' : 'Excluded basmalah'}
          </div>
          <div className="font-mono text-sm">
            {occs?.excludedBasmalahCount ?? 0}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quran evidence */}
        <section className="lg:col-span-2 p-4 bg-white border border-gray-200 rounded-lg">
          <h2 className="font-semibold mb-3 flex items-center gap-1">
            <BookOpen className="w-4 h-4" />
            {language === 'ar' ? 'الشواهد القرآنية' : 'Quran evidence'}
          </h2>
          <div className="flex flex-wrap items-center gap-3 mb-3 text-xs">
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={includeExcluded}
                onChange={(e) => setIncludeExcluded(e.target.checked)}
              />
              {language === 'ar' ? 'تضمين المستثنى' : 'Include excluded basmalah'}
            </label>
            <select
              value={surahFilter}
              onChange={(e) => setSurahFilter(e.target.value === '' ? '' : Number(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded bg-white"
            >
              <option value="">
                {language === 'ar' ? 'كل السور' : 'All surahs'}
              </option>
              {surahsInData.map((s) => (
                <option key={s} value={s}>
                  {language === 'ar' ? `سورة ${s}` : `Surah ${s}`}
                </option>
              ))}
            </select>
          </div>
          {filteredOccs.length === 0 && (
            <p className="text-sm text-gray-500">
              {language === 'ar' ? 'لا شواهد مطابقة.' : 'No occurrences match the current filter.'}
            </p>
          )}
          <ul className="space-y-1 max-h-[60vh] overflow-y-auto">
            {filteredOccs.map((o, i) => (
              <li
                key={`${o.surahNumber}:${o.ayahNumber}:${i}`}
                className="text-sm py-1.5 border-b last:border-b-0 flex items-start justify-between gap-2"
              >
                <div className="flex-1">
                  <Link
                    to={`/quran/${o.surahNumber}`}
                    className="font-mono text-emerald-700 hover:text-emerald-900"
                  >
                    {o.surahNumber}:{o.ayahNumber}
                  </Link>
                  <span className="mx-1.5 text-gray-400">·</span>
                  <span className="text-xs text-gray-700">{o.matchType}</span>
                  {o.matchedForm && (
                    <>
                      <span className="mx-1.5 text-gray-400">·</span>
                      <span className="font-arabic text-base text-gray-900" dir="rtl">
                        {o.matchedForm}
                      </span>
                    </>
                  )}
                </div>
                {!o.counted && (
                  <span className="text-xs px-1.5 py-0.5 rounded border bg-amber-50 text-amber-800 border-amber-200">
                    {language === 'ar' ? 'مستثناة من العدّ' : 'excluded from count'}
                  </span>
                )}
              </li>
            ))}
          </ul>
          {/* Basmalah policy note */}
          <p className="text-xs text-gray-500 mt-3">
            {language === 'ar'
              ? 'تذكير: المواضع المستثناة تندرج ضمن البسملة الافتتاحية للسور وتُعرض هنا للمراجعة فقط، ولا تُحتسب في إجمالي العدّ.'
              : 'Reminder: excluded occurrences belong to repeated surah-opening basmalah; they are shown for transparency only and do not contribute to the count.'}
          </p>
        </section>

        {/* Pairings + related */}
        <aside className="p-4 bg-white border border-gray-200 rounded-lg">
          <h2 className="font-semibold mb-3 flex items-center gap-1">
            <Layers className="w-4 h-4" />
            {language === 'ar' ? 'الاقترانات الشائعة' : 'Common pairings'}
          </h2>
          {detail.commonPairings.length === 0 && (
            <p className="text-xs text-gray-500">
              {language === 'ar' ? 'لا توجد اقترانات مع أسماء أخرى.' : 'No pairings with other Names.'}
            </p>
          )}
          <ul className="space-y-1.5">
            {detail.commonPairings.slice(0, 20).map((p, i) => {
              const otherId = p.firstNameId === detail.nameId ? p.secondNameId : p.firstNameId;
              return (
                <li
                  key={`${p.firstNameId}::${p.secondNameId}::${i}`}
                  className="text-sm flex items-center justify-between py-1 border-b last:border-b-0"
                >
                  <Link
                    to={`/themes/asma/${encodeURIComponent(otherId)}`}
                    className="text-emerald-700 hover:text-emerald-900"
                  >
                    {otherId}
                  </Link>
                  <span className="text-xs text-gray-500">
                    ×{p.occurrenceCount}
                  </span>
                </li>
              );
            })}
          </ul>
          {detail.relatedTopics.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium mb-1">
                {language === 'ar' ? 'مواضيع مرتبطة' : 'Related topics'}
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {detail.relatedTopics.map((tid) => (
                  <Link
                    key={tid}
                    to={`/topics/${encodeURIComponent(tid)}`}
                    className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200"
                  >
                    {tid}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>

      <div className="mt-6 flex items-start gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-md text-sm">
        <AlertCircle className="w-4 h-4 text-emerald-700 mt-0.5 flex-shrink-0" />
        <p className="text-emerald-800">
          {language === 'ar'
            ? 'الشواهد القرآنية مستخرجة من نص المصحف. تفسير المعاني يحتاج إلى مصادر موثّقة ومراجعة علمية.'
            : 'Quran evidence is extracted from the canonical Quran text. Interpretation of meanings requires verified sources and scholarly review.'}
        </p>
      </div>
    </div>
  );
}
