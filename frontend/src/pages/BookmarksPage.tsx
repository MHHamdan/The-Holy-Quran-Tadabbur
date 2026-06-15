import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bookmark, Trash2, ExternalLink, BookmarkX, Search, X } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { useBookmarksStore } from '../stores/bookmarksStore';
import clsx from 'clsx';

function toArabicNumber(n: number): string {
  return n.toString().replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[+d]);
}

export function BookmarksPage() {
  const { language } = useLanguageStore();
  const { bookmarks, removeBookmark, clearAll } = useBookmarksStore();
  const isRtl = language === 'ar';

  const [filter, setFilter] = useState('');
  const [confirmClear, setConfirmClear] = useState(false);

  const filtered = bookmarks.filter((b) => {
    if (!filter.trim()) return true;
    const q = filter.toLowerCase();
    return (
      b.sura_name_en.toLowerCase().includes(q) ||
      b.sura_name_ar.includes(filter) ||
      `${b.sura_no}:${b.aya_no}`.includes(q)
    );
  });

  // Group by surah for display
  const bySurah = filtered.reduce<Record<number, typeof filtered>>((acc, b) => {
    if (!acc[b.sura_no]) acc[b.sura_no] = [];
    acc[b.sura_no].push(b);
    return acc;
  }, {});

  const surahNumbers = Object.keys(bySurah).map(Number).sort((a, b) => a - b);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900 flex items-center gap-2', isRtl && 'font-arabic')}>
            <Bookmark className="w-6 h-6 text-amber-500" />
            {isRtl ? 'الآيات المحفوظة' : 'Saved Verses'}
          </h1>
          <p className={clsx('text-sm text-gray-500 mt-1', isRtl && 'font-arabic')}>
            {bookmarks.length === 0
              ? (isRtl ? 'لا توجد آيات محفوظة بعد' : 'No saved verses yet')
              : isRtl
                ? `${toArabicNumber(bookmarks.length)} آية محفوظة`
                : `${bookmarks.length} verse${bookmarks.length !== 1 ? 's' : ''} saved`}
          </p>
        </div>
        {bookmarks.length > 0 && (
          <div className="flex items-center gap-2">
            {confirmClear ? (
              <>
                <span className={clsx('text-sm text-red-600', isRtl && 'font-arabic')}>
                  {isRtl ? 'هل أنت متأكد؟' : 'Are you sure?'}
                </span>
                <button
                  onClick={() => { clearAll(); setConfirmClear(false); }}
                  className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                >
                  {isRtl ? 'نعم، احذف' : 'Yes, clear'}
                </button>
                <button
                  onClick={() => setConfirmClear(false)}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors"
                >
                  {isRtl ? 'إلغاء' : 'Cancel'}
                </button>
              </>
            ) : (
              <button
                onClick={() => setConfirmClear(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
              >
                <BookmarkX className="w-4 h-4" />
                {isRtl ? 'حذف الكل' : 'Clear all'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Search filter */}
      {bookmarks.length > 3 && (
        <div className="relative mb-6">
          <Search className={clsx('absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400', isRtl ? 'right-3' : 'left-3')} />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder={isRtl ? 'ابحث في المحفوظات...' : 'Filter bookmarks...'}
            className={clsx(
              'w-full border border-gray-200 rounded-lg py-2 text-sm bg-white focus:ring-2 focus:ring-amber-300 focus:border-amber-400 outline-none',
              isRtl ? 'pr-9 pl-9 font-arabic text-right' : 'pl-9 pr-9'
            )}
            dir={isRtl ? 'rtl' : 'ltr'}
          />
          {filter && (
            <button
              onClick={() => setFilter('')}
              className={clsx('absolute top-1/2 -translate-y-1/2', isRtl ? 'left-3' : 'right-3')}
            >
              <X className="w-4 h-4 text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>
      )}

      {/* Empty state */}
      {bookmarks.length === 0 && (
        <div className="text-center py-20">
          <Bookmark className="w-16 h-16 text-gray-200 mx-auto mb-4" />
          <p className={clsx('text-gray-500 mb-2', isRtl && 'font-arabic')}>
            {isRtl ? 'لم تحفظ أي آية بعد' : "You haven't saved any verses yet"}
          </p>
          <p className={clsx('text-sm text-gray-400 mb-6', isRtl && 'font-arabic')}>
            {isRtl
              ? 'افتح أي آية في المصحف واضغط على زر "حفظ"'
              : 'Open any verse in the Mushaf and click the "Save" button'}
          </p>
          <Link
            to="/mushaf"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
          >
            {isRtl ? 'افتح المصحف' : 'Open Mushaf'}
            <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Filter empty state */}
      {bookmarks.length > 0 && filtered.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className={clsx(isRtl && 'font-arabic')}>
            {isRtl ? 'لا توجد نتائج للبحث' : 'No results match your filter'}
          </p>
        </div>
      )}

      {/* Grouped by surah */}
      <div className="space-y-6">
        {surahNumbers.map((surahNo) => {
          const group = bySurah[surahNo];
          const firstVerse = group[0];
          return (
            <div key={surahNo}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                  {surahNo}
                </div>
                <div>
                  <h2 className={clsx('font-semibold text-gray-800', isRtl ? 'font-arabic' : '')}>
                    {isRtl ? firstVerse.sura_name_ar : firstVerse.sura_name_en}
                  </h2>
                  {!isRtl && (
                    <span className="text-xs text-gray-400 font-arabic">{firstVerse.sura_name_ar}</span>
                  )}
                </div>
                <span className="ms-auto text-xs text-gray-400">
                  {group.length} {isRtl ? 'آية' : group.length === 1 ? 'verse' : 'verses'}
                </span>
              </div>
              <div className="space-y-3">
                {group.map((b) => (
                  <div
                    key={b.id}
                    className="card border border-amber-100 bg-amber-50/30 hover:border-amber-300 transition-colors group"
                  >
                    {/* Verse reference row */}
                    <div className="flex items-center justify-between mb-3">
                      <Link
                        to={`/quran/${b.sura_no}?aya=${b.aya_no}`}
                        className="flex items-center gap-2 text-sm font-medium text-primary-700 hover:text-primary-900 transition-colors"
                      >
                        <span className="bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full text-xs">
                          {b.sura_no}:{b.aya_no}
                        </span>
                        <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </Link>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">
                          {new Date(b.bookmarked_at).toLocaleDateString(
                            isRtl ? 'ar-SA' : 'en-US',
                            { year: 'numeric', month: 'short', day: 'numeric' }
                          )}
                        </span>
                        <button
                          onClick={() => removeBookmark(b.id)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors rounded"
                          title={isRtl ? 'إزالة الإشارة' : 'Remove bookmark'}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {/* Arabic verse text */}
                    <p
                      className="font-mushaf text-xl text-gray-900 leading-loose text-right mb-2"
                      dir="rtl"
                      lang="ar"
                    >
                      {b.text_uthmani}
                      {' '}
                      <span className="text-amber-600 text-lg">
                        {'﴿'}{isRtl ? toArabicNumber(b.aya_no) : b.aya_no}{'﴾'}
                      </span>
                    </p>
                    {/* Note (if any) */}
                    {b.note && (
                      <p className={clsx('text-sm text-gray-600 mt-2 pt-2 border-t border-amber-100', isRtl && 'font-arabic text-right')}>
                        {b.note}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
