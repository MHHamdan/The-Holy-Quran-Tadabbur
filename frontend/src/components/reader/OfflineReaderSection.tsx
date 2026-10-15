/**
 * Offline reading and listening, shown with the reader settings:
 * - Save the whole Qur'an text (all 114 surahs, as the API returns them) to
 *   this device so the reader opens without a connection.
 * - List the recitations saved for offline listening, with their size, and
 *   delete one or all of them.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Download, HardDrive, Trash2 } from 'lucide-react';
import { quranApi } from '../../lib/api';
import { clearPersistedQueries, countPersistedSurahs, queryKeys, staleTimes } from '../../lib/queryClient';
import { clearAll, listSaved, offlineAudioSupported, removeSurah, type SavedSurahRow } from '../../lib/offlineAudio';
import { SURAH_NAMES } from '../../data/surahNames';

const RECITER_NAMES: Record<string, { ar: string; en: string }> = {
  mishary_afasy: { ar: 'مشاري العفاسي', en: 'Mishary Al-Afasy' },
  saud_shuraim: { ar: 'سعود الشريم', en: 'Saud Al-Shuraim' },
  maher_muaiqly: { ar: 'ماهر المعيقلي', en: 'Maher Al-Muaiqly' },
  abdul_basit: { ar: 'عبد الباسط عبد الصمد', en: 'Abdul Basit Abdul Samad' },
  husary: { ar: 'محمود خليل الحصري', en: 'Mahmoud Khalil Al-Husary' },
  minshawi: { ar: 'محمد صديق المنشاوي', en: 'Muhammad Siddiq Al-Minshawi' },
};

const mb = (bytes: number) => (bytes / 1048576).toFixed(1);
const arDigits = (n: number | string) => String(n).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[Number(d)]);

export function OfflineReaderSection({
  language,
  translations,
}: {
  language: 'ar' | 'en';
  /** Translation keys shown in the reader (saved with the text). */
  translations: string[];
}) {
  const ar = language === 'ar';
  const queryClient = useQueryClient();
  const translationsKey = translations.join(',');

  // ── Qur'an text ──
  const [stored, setStored] = useState<number | null>(null);
  const [progress, setProgress] = useState<{ done: number; failed: number } | null>(null);
  const abortRef = useRef(false);

  const refreshCount = useCallback(() => {
    void countPersistedSurahs().then(setStored);
  }, []);
  useEffect(() => {
    refreshCount();
    return () => { abortRef.current = true; };
  }, [refreshCount]);

  const saveText = async () => {
    abortRef.current = false;
    let done = 0;
    let failed = 0;
    setProgress({ done, failed });
    const surahs = Array.from({ length: 114 }, (_, i) => i + 1);
    const worker = async () => {
      for (let s = surahs.shift(); s; s = surahs.shift()) {
        if (abortRef.current) return;
        try {
          await queryClient.fetchQuery({
            queryKey: queryKeys.quran.suraWithTranslations(s, translationsKey),
            queryFn: () => quranApi.getSuraVerses(s, translations).then((r) => r.data),
            staleTime: staleTimes.quranText,
          });
          done += 1;
        } catch {
          failed += 1;
        }
        setProgress({ done, failed });
      }
    };
    await Promise.all([worker(), worker(), worker()]);
    if (failed === 0) {
      setStored(114);
      setProgress(null);
    }
    // Re-read the device count once the IndexedDB writes have settled.
    setTimeout(refreshCount, 1500);
  };

  const removeText = async () => {
    await clearPersistedQueries(queryClient);
    refreshCount();
    setProgress(null);
  };

  // ── Recitations ──
  const [rows, setRows] = useState<SavedSurahRow[]>(() => listSaved());
  const totalBytes = rows.reduce((sum, r) => sum + r.bytes, 0);
  const removeRow = async (row: SavedSurahRow) => {
    await removeSurah(row.reciter, row.sura);
    setRows(listSaved());
  };
  const removeAll = async () => {
    if (!window.confirm(ar ? 'حذف كل التلاوات المحفوظة من هذا الجهاز؟' : 'Delete all saved recitations from this device?')) return;
    await clearAll();
    setRows(listSaved());
  };

  return (
    <section
      className="card mb-6 space-y-5"
      dir={ar ? 'rtl' : 'ltr'}
      lang={language}
      aria-labelledby="offline-reader-heading"
    >
      <h2 id="offline-reader-heading" className={`text-lg font-semibold flex items-center gap-2 ${ar ? 'font-arabic' : ''}`}>
        <HardDrive className="w-5 h-5 text-primary-600" aria-hidden="true" />
        {ar ? 'القراءة والاستماع دون اتصال' : 'Offline reading and listening'}
      </h2>

      {/* Qur'an text */}
      <div>
        <p className="text-sm text-gray-600 mb-2">
          {ar
            ? 'احفظ نص القرآن الكريم كاملًا (١١٤ سورة) على هذا الجهاز ليفتح القارئ دون اتصال.'
            : 'Save the full Qur’an text (114 surahs) on this device so the reader opens without a connection.'}
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => void saveText()}
            disabled={!!progress && progress.done + progress.failed < 114}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700 disabled:bg-gray-400"
          >
            <Download className="w-4 h-4" aria-hidden="true" />
            {ar ? 'حفظ القرآن للقراءة دون اتصال' : 'Save Qur’an for offline reading'}
          </button>
          {stored !== null && stored > 0 && (
            <button onClick={() => void removeText()} className="text-sm text-red-600 hover:underline">
              {ar ? 'حذف النسخة المحفوظة' : 'Remove offline copy'}
            </button>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-2" role="status">
          {progress
            ? (ar
              ? `جارٍ الحفظ: ${arDigits(progress.done)} من ١١٤${progress.failed ? `، تعذّر ${arDigits(progress.failed)}` : ''}`
              : `Saving: ${progress.done} of 114${progress.failed ? `, ${progress.failed} failed` : ''}`)
            : stored !== null && stored > 0
              ? (ar ? `محفوظ على هذا الجهاز: ${arDigits(stored)} من ١١٤ سورة` : `Saved on this device: ${stored} of 114 surahs`)
              : ''}
        </p>
      </div>

      {/* Recitations */}
      {offlineAudioSupported && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            {ar ? 'التلاوات المحفوظة' : 'Saved recitations'}
          </h3>
          {rows.length === 0 ? (
            <p className="text-sm text-gray-500">
              {ar
                ? 'لا توجد تلاوات محفوظة. استخدم زر الحفظ في مشغّل التلاوة لحفظ سورة.'
                : 'No saved recitations. Use the save button in the recitation player to save a surah.'}
            </p>
          ) : (
            <>
              <ul className="divide-y divide-gray-100 border border-gray-100 rounded-lg">
                {rows.map((row) => {
                  const name = SURAH_NAMES[row.sura - 1];
                  const reciter = RECITER_NAMES[row.reciter];
                  return (
                    <li key={`${row.reciter}:${row.sura}`} className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
                      <span className="flex items-center gap-2 min-w-0">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" aria-hidden="true" />
                        <span className="truncate">
                          {row.sura}. {name ? (ar ? name.ar : name.en) : ''}
                          {' · '}
                          {reciter ? (ar ? reciter.ar : reciter.en) : row.reciter}
                          {' · '}
                          {ar ? `${row.verses} آية، ${mb(row.bytes)} م.ب` : `${row.verses} verses, ${mb(row.bytes)} MB`}
                        </span>
                      </span>
                      <button
                        onClick={() => void removeRow(row)}
                        className="p-1.5 rounded hover:bg-red-50 text-red-600 flex-shrink-0"
                        aria-label={ar ? `حذف سورة ${name?.ar ?? row.sura}` : `Delete surah ${name?.en ?? row.sura}`}
                      >
                        <Trash2 className="w-4 h-4" aria-hidden="true" />
                      </button>
                    </li>
                  );
                })}
              </ul>
              <div className="flex items-center justify-between mt-2 text-sm">
                <span className="text-gray-600">
                  {ar ? `المجموع: ${mb(totalBytes)} م.ب` : `Total: ${mb(totalBytes)} MB`}
                </span>
                <button onClick={() => void removeAll()} className="text-red-600 hover:underline">
                  {ar ? 'حذف الكل' : 'Delete all'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

export default OfflineReaderSection;
