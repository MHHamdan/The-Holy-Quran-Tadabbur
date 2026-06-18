/**
 * Verse Reflection Journal — personal Quran study notebook.
 *
 * Private, offline-capable. Each entry links to a surah:ayah.
 * No backend, no auth — purely localStorage via Zustand persist.
 *
 * Improvements v2:
 * - Word count per entry + total words written in header
 * - Export to .txt (one click)
 * - Sort: newest / oldest / surah order
 * - Category count badges in filter chips
 * - Writing prompts to inspire reflection (rotated by entry count)
 * - Arabic surah names in Arabic UI mode
 * - Stats summary bar: entries, words, top category, top surah
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpenCheck, Plus, Trash2, Edit3, Save, X,
  ChevronRight, Search, Filter, Download, ArrowUpDown,
  Lightbulb, BarChart2,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  useJournalStore, CATEGORY_META,
  type JournalCategory, type JournalEntry,
} from '../stores/journalStore';
import { SURAH_NAMES } from '../data/surahNames';

const CATEGORIES = Object.keys(CATEGORY_META) as JournalCategory[];

const COLOR_CLASSES: Record<string, { badge: string; ring: string }> = {
  violet:  { badge: 'bg-violet-100 text-violet-700', ring: 'ring-violet-300' },
  blue:    { badge: 'bg-blue-100 text-blue-700',     ring: 'ring-blue-300'   },
  amber:   { badge: 'bg-amber-100 text-amber-700',   ring: 'ring-amber-300'  },
  emerald: { badge: 'bg-emerald-100 text-emerald-700', ring: 'ring-emerald-300'},
  green:   { badge: 'bg-green-100 text-green-700',   ring: 'ring-green-300'  },
  gray:    { badge: 'bg-gray-100 text-gray-600',     ring: 'ring-gray-300'   },
};

// Writing prompts — rotate by entry count so each new entry gets a fresh prompt
const PROMPTS_EN = [
  'What does this verse teach you about your relationship with Allah?',
  'How does this verse apply to something in your life right now?',
  'What is one action you can take because of this verse?',
  'What word or phrase in this verse stood out most to you? Why?',
  'How does this verse connect to other verses you know?',
  'What question does this verse raise in your mind?',
  'How would you explain the lesson of this verse to a child?',
  'What does this verse say about human nature?',
  'How does this verse bring you comfort or guidance?',
  'What would change in your daily life if you truly lived by this verse?',
];
const PROMPTS_AR = [
  'ماذا تعلّمك هذه الآية عن علاقتك بالله؟',
  'كيف تنطبق هذه الآية على شيء في حياتك الآن؟',
  'ما الخطوة العملية التي يمكنك اتخاذها بسبب هذه الآية؟',
  'أي كلمة أو عبارة في هذه الآية لفتت انتباهك أكثر؟ ولماذا؟',
  'كيف ترتبط هذه الآية بآيات أخرى تعرفها؟',
  'ما السؤال الذي تثيره هذه الآية في ذهنك؟',
  'كيف تشرح درس هذه الآية لطفل صغير؟',
  'ماذا تقول هذه الآية عن الطبيعة البشرية؟',
  'كيف تمنحك هذه الآية الطمأنينة أو التوجيه؟',
  'ما الذي سيتغير في يومك لو طبّقت هذه الآية فعلاً؟',
];

function wordCount(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function formatDate(iso: string, isRtl: boolean): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(isRtl ? 'ar-SA' : 'en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
    });
  } catch { return iso.slice(0, 10); }
}

// ---------------------------------------------------------------------------
// Export helper
// ---------------------------------------------------------------------------

function exportEntries(entries: JournalEntry[], isRtl: boolean) {
  const lines: string[] = [
    isRtl ? '=== مذكرة التأمل القرآني ===' : '=== Quranic Reflection Journal ===',
    isRtl ? `تاريخ التصدير: ${new Date().toLocaleDateString('ar-SA')}` : `Exported: ${new Date().toLocaleDateString('en-GB')}`,
    '',
  ];
  for (const e of entries) {
    lines.push(`${e.surahNameEn} (${e.surahNameAr}) ${e.surah}:${e.ayah}`);
    lines.push(isRtl ? `النوع: ${CATEGORY_META[e.category].labelAr}` : `Category: ${CATEGORY_META[e.category].labelEn}`);
    lines.push(isRtl ? `التاريخ: ${formatDate(e.createdAt, isRtl)}` : `Date: ${formatDate(e.createdAt, isRtl)}`);
    lines.push('');
    lines.push(e.note);
    lines.push('─'.repeat(50));
    lines.push('');
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `tadabbur-journal-${new Date().toISOString().slice(0, 10)}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Type for sort mode
// ---------------------------------------------------------------------------

type SortMode = 'newest' | 'oldest' | 'surah';

const SORT_LABELS: Record<SortMode, { en: string; ar: string }> = {
  newest: { en: 'Newest first', ar: 'الأحدث أولاً' },
  oldest: { en: 'Oldest first', ar: 'الأقدم أولاً' },
  surah:  { en: 'By surah',     ar: 'ترتيب السور'  },
};

// ---------------------------------------------------------------------------
// EntryForm
// ---------------------------------------------------------------------------

interface EntryFormData {
  surah: number;
  ayah: number;
  category: JournalCategory;
  note: string;
}

function EntryForm({
  initial, onSave, onCancel, isRtl, promptIndex,
}: {
  initial?: Partial<EntryFormData>;
  onSave: (data: EntryFormData) => void;
  onCancel: () => void;
  isRtl: boolean;
  promptIndex: number;
}) {
  const [surah, setSurah] = useState(initial?.surah ?? 1);
  const [ayah, setAyah] = useState(initial?.ayah ?? 1);
  const [category, setCategory] = useState<JournalCategory>(initial?.category ?? 'reflection');
  const [note, setNote] = useState(initial?.note ?? '');
  const [showPrompt, setShowPrompt] = useState(false);

  const surahName = SURAH_NAMES[surah - 1];
  const prompt = isRtl ? PROMPTS_AR[promptIndex % PROMPTS_AR.length] : PROMPTS_EN[promptIndex % PROMPTS_EN.length];
  const wc = wordCount(note);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!note.trim()) return;
    onSave({ surah, ayah, category, note: note.trim() });
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
      <div className={clsx('flex items-center justify-between mb-4', isRtl && 'flex-row-reverse')}>
        <h3 className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic')}>
          {isRtl ? 'إضافة تأمل جديد' : 'New Reflection'}
        </h3>
        <button
          type="button"
          onClick={() => setShowPrompt(v => !v)}
          className={clsx(
            'flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg border transition-colors',
            showPrompt ? 'bg-amber-100 text-amber-700 border-amber-200' : 'text-gray-400 border-gray-200 hover:border-amber-300'
          )}
        >
          <Lightbulb className="w-3 h-3" />
          {isRtl ? 'سؤال تأملي' : 'Reflection prompt'}
        </button>
      </div>

      {/* Prompt */}
      {showPrompt && (
        <div className={clsx('bg-amber-50 border border-amber-100 rounded-xl px-3 py-2.5 mb-4 text-xs text-amber-800 italic', isRtl && 'font-arabic text-right')}>
          {prompt}
        </div>
      )}

      {/* Surah + Ayah */}
      <div className={clsx('flex gap-3 mb-4', isRtl && 'flex-row-reverse')}>
        <div className="flex-1">
          <label className={clsx('block text-xs text-gray-500 mb-1', isRtl && 'font-arabic text-right')}>
            {isRtl ? 'السورة' : 'Surah'}
          </label>
          <select
            value={surah}
            onChange={e => setSurah(Number(e.target.value))}
            className={clsx(
              'w-full rounded-lg border border-gray-200 text-sm p-2 bg-white focus:outline-none focus:ring-2 focus:ring-violet-300',
              isRtl && 'font-arabic text-right'
            )}
            dir={isRtl ? 'rtl' : 'ltr'}
          >
            {SURAH_NAMES.map((n, i) => (
              <option key={i + 1} value={i + 1}>
                {i + 1}. {isRtl ? n.ar : n.en}
              </option>
            ))}
          </select>
        </div>
        <div className="w-24">
          <label className={clsx('block text-xs text-gray-500 mb-1', isRtl && 'font-arabic text-right')}>
            {isRtl ? 'الآية' : 'Ayah'}
          </label>
          <input
            type="number"
            min={1}
            max={286}
            value={ayah}
            onChange={e => setAyah(Math.max(1, Number(e.target.value)))}
            className="w-full rounded-lg border border-gray-200 text-sm p-2 focus:outline-none focus:ring-2 focus:ring-violet-300"
          />
        </div>
      </div>

      {/* Verse reference preview */}
      <div className={clsx('flex items-center gap-1.5 text-xs text-gray-400 mb-4', isRtl && 'flex-row-reverse')}>
        <BookOpenCheck className="w-3.5 h-3.5" />
        <span dir="rtl" className="font-arabic">{surahName?.ar}</span>
        <span>·</span>
        <span>{surahName?.en} {surah}:{ayah}</span>
        <Link
          to={`/quran/${surah}`}
          target="_blank"
          className="ms-1 text-violet-500 hover:underline"
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Category */}
      <div className="mb-4">
        <label className={clsx('block text-xs text-gray-500 mb-2', isRtl && 'font-arabic text-right')}>
          {isRtl ? 'النوع' : 'Category'}
        </label>
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map(c => {
            const meta = CATEGORY_META[c];
            const colors = COLOR_CLASSES[meta.color] ?? COLOR_CLASSES.gray;
            return (
              <button
                key={c}
                type="button"
                onClick={() => setCategory(c)}
                className={clsx(
                  'flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border transition-all',
                  category === c
                    ? `${colors.badge} ring-1 ${colors.ring}`
                    : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'
                )}
              >
                <span>{meta.emoji}</span>
                <span className={isRtl ? 'font-arabic' : ''}>{isRtl ? meta.labelAr : meta.labelEn}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Note textarea */}
      <div className="mb-4">
        <div className={clsx('flex items-center justify-between mb-1', isRtl && 'flex-row-reverse')}>
          <label className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>
            {isRtl ? 'ملاحظتك' : 'Your reflection'}
          </label>
          {wc > 0 && (
            <span className="text-[10px] text-gray-300">
              {isRtl ? `${wc} كلمة` : `${wc} word${wc === 1 ? '' : 's'}`}
            </span>
          )}
        </div>
        <textarea
          value={note}
          onChange={e => setNote(e.target.value)}
          placeholder={isRtl ? 'اكتب تأملك أو ملاحظتك هنا…' : 'Write your reflection here…'}
          rows={4}
          dir={isRtl ? 'rtl' : 'ltr'}
          className={clsx(
            'w-full rounded-xl border border-gray-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300 resize-none',
            isRtl && 'font-arabic text-right'
          )}
        />
      </div>

      {/* Actions */}
      <div className={clsx('flex gap-2 justify-end', isRtl && 'flex-row-reverse')}>
        <button
          type="button"
          onClick={onCancel}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
          {isRtl ? 'إلغاء' : 'Cancel'}
        </button>
        <button
          type="submit"
          disabled={!note.trim()}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-40 transition-colors"
        >
          <Save className="w-3.5 h-3.5" />
          {isRtl ? 'حفظ' : 'Save'}
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// EntryCard
// ---------------------------------------------------------------------------

function EntryCard({
  entry, isRtl, onDelete, onUpdate,
}: {
  entry: JournalEntry;
  isRtl: boolean;
  onDelete: () => void;
  onUpdate: (patch: Partial<Pick<JournalEntry, 'note' | 'category'>>) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editNote, setEditNote] = useState(entry.note);
  const [editCategory, setEditCategory] = useState<JournalCategory>(entry.category);
  const meta = CATEGORY_META[entry.category];
  const colors = COLOR_CLASSES[meta.color] ?? COLOR_CLASSES.gray;
  const wc = wordCount(entry.note);

  function saveEdit() {
    if (!editNote.trim()) return;
    onUpdate({ note: editNote.trim(), category: editCategory });
    setEditing(false);
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-4 hover:shadow-sm transition-shadow">
      {/* Top row */}
      <div className={clsx('flex items-start gap-2 mb-3', isRtl && 'flex-row-reverse')}>
        <Link
          to={`/quran/${entry.surah}`}
          className={clsx(
            'flex items-center gap-1.5 text-xs text-violet-600 hover:underline flex-shrink-0',
            isRtl && 'flex-row-reverse'
          )}
        >
          <BookOpenCheck className="w-3.5 h-3.5" />
          <span className="font-arabic" dir="rtl">{entry.surahNameAr}</span>
          <span className="text-gray-400">·</span>
          <span>{entry.surahNameEn} {entry.surah}:{entry.ayah}</span>
        </Link>
        <div className={clsx('ms-auto flex items-center gap-1.5 flex-shrink-0', isRtl && 'me-auto ms-0')}>
          <span className={clsx('text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap', colors.badge)}>
            {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
          </span>
          <button
            onClick={() => { setEditing(!editing); setEditNote(entry.note); setEditCategory(entry.category); }}
            className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-violet-500 transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-red-500 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {editing ? (
        <div>
          {/* Category picker */}
          <div className="flex flex-wrap gap-1.5 mb-2">
            {CATEGORIES.map(c => {
              const m = CATEGORY_META[c];
              const cl = COLOR_CLASSES[m.color] ?? COLOR_CLASSES.gray;
              return (
                <button
                  key={c}
                  onClick={() => setEditCategory(c)}
                  className={clsx(
                    'flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] border transition-all',
                    editCategory === c ? `${cl.badge} ring-1 ${cl.ring}` : 'bg-gray-50 text-gray-500 border-gray-200'
                  )}
                >
                  {m.emoji} {isRtl ? m.labelAr : m.labelEn}
                </button>
              );
            })}
          </div>
          <textarea
            value={editNote}
            onChange={e => setEditNote(e.target.value)}
            rows={3}
            dir={isRtl ? 'rtl' : 'ltr'}
            className={clsx(
              'w-full rounded-xl border border-violet-300 p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300 resize-none mb-2',
              isRtl && 'font-arabic text-right'
            )}
          />
          <div className={clsx('flex gap-2 justify-end', isRtl && 'flex-row-reverse')}>
            <button onClick={() => setEditing(false)} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded-lg">
              {isRtl ? 'إلغاء' : 'Cancel'}
            </button>
            <button onClick={saveEdit} className="text-xs text-white bg-violet-600 hover:bg-violet-700 px-3 py-1 rounded-lg font-medium">
              {isRtl ? 'حفظ' : 'Save'}
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className={clsx('text-sm text-gray-700 leading-relaxed whitespace-pre-wrap', isRtl && 'font-arabic text-right')}>
            {entry.note}
          </p>
          <div className={clsx('flex items-center gap-2 mt-2', isRtl && 'flex-row-reverse')}>
            <p className="text-[10px] text-gray-300">
              {formatDate(entry.updatedAt, isRtl)}
              {entry.updatedAt !== entry.createdAt && ` · ${isRtl ? 'معدّل' : 'edited'}`}
            </p>
            <span className="text-[10px] text-gray-200">·</span>
            <span className="text-[10px] text-gray-300">
              {isRtl ? `${wc} كلمة` : `${wc} word${wc === 1 ? '' : 's'}`}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stats bar
// ---------------------------------------------------------------------------

function StatsBar({ entries, isRtl }: { entries: JournalEntry[]; isRtl: boolean }) {
  if (entries.length < 3) return null;

  const totalWords = entries.reduce((s, e) => s + wordCount(e.note), 0);

  // Top category
  const catCounts: Record<string, number> = {};
  for (const e of entries) catCounts[e.category] = (catCounts[e.category] ?? 0) + 1;
  const topCat = Object.entries(catCounts).sort((a, b) => b[1] - a[1])[0];
  const topCatMeta = topCat ? CATEGORY_META[topCat[0] as JournalCategory] : null;

  // Top surah
  const surahCounts: Record<number, number> = {};
  for (const e of entries) surahCounts[e.surah] = (surahCounts[e.surah] ?? 0) + 1;
  const topSurahNum = Number(Object.entries(surahCounts).sort((a, b) => b[1] - a[1])[0]?.[0]);
  const topSurahName = topSurahNum ? SURAH_NAMES[topSurahNum - 1] : null;

  return (
    <div className="bg-violet-50/60 rounded-2xl border border-violet-100 p-4 mb-5">
      <div className={clsx('flex items-center gap-1.5 mb-3', isRtl && 'flex-row-reverse')}>
        <BarChart2 className="w-3.5 h-3.5 text-violet-500" />
        <span className={clsx('text-xs font-semibold text-violet-700', isRtl && 'font-arabic')}>
          {isRtl ? 'ملخص تأملاتك' : 'Your journal at a glance'}
        </span>
      </div>
      <div className={clsx('grid grid-cols-3 gap-3', isRtl && 'text-right')}>
        <div>
          <p className="text-xl font-bold text-gray-900">{totalWords.toLocaleString()}</p>
          <p className={clsx('text-[10px] text-gray-400', isRtl && 'font-arabic')}>
            {isRtl ? 'كلمة مكتوبة' : 'words written'}
          </p>
        </div>
        {topCatMeta && (
          <div>
            <p className="text-xl">{topCatMeta.emoji}</p>
            <p className={clsx('text-[10px] text-gray-400', isRtl && 'font-arabic')}>
              {isRtl ? `أكثر فئة: ${topCatMeta.labelAr}` : `Most: ${topCatMeta.labelEn}`}
            </p>
          </div>
        )}
        {topSurahName && (
          <div>
            <p className={clsx('text-sm font-bold text-gray-900', isRtl && 'font-arabic')}>
              {isRtl ? topSurahName.ar : topSurahName.en}
            </p>
            <p className={clsx('text-[10px] text-gray-400', isRtl && 'font-arabic')}>
              {isRtl ? 'أكثر سورة تأملاً' : 'most reflected on'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function JournalPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const { entries, addEntry, updateEntry, deleteEntry } = useJournalStore();

  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState<JournalCategory | 'all'>('all');
  const [sortMode, setSortMode] = useState<SortMode>('newest');
  const [showSort, setShowSort] = useState(false);

  // Category counts
  const catCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of entries) counts[e.category] = (counts[e.category] ?? 0) + 1;
    return counts;
  }, [entries]);

  const filtered = useMemo(() => {
    let result = entries;
    if (filterCat !== 'all') result = result.filter(e => e.category === filterCat);
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(e =>
        e.note.toLowerCase().includes(q) ||
        e.surahNameEn.toLowerCase().includes(q) ||
        e.surahNameAr.includes(q)
      );
    }
    // Sort
    result = [...result];
    if (sortMode === 'newest') result.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
    else if (sortMode === 'oldest') result.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
    else if (sortMode === 'surah') result.sort((a, b) => a.surah - b.surah || a.ayah - b.ayah);
    return result;
  }, [entries, filterCat, search, sortMode]);

  const totalWords = useMemo(() => entries.reduce((s, e) => s + wordCount(e.note), 0), [entries]);

  function handleSave(data: { surah: number; ayah: number; category: JournalCategory; note: string }) {
    const name = SURAH_NAMES[data.surah - 1];
    addEntry({
      ...data,
      surahNameEn: name?.en ?? '',
      surahNameAr: name?.ar ?? '',
    });
    setShowForm(false);
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* Header */}
      <div className={clsx('flex items-center justify-between mb-6', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <BookOpenCheck className="w-6 h-6 text-violet-600" />
          <div>
            <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
              {isRtl ? 'مذكرة التأمل' : 'Reflection Journal'}
            </h1>
            <p className={clsx('text-xs text-gray-400', isRtl && 'font-arabic')}>
              {entries.length === 0
                ? (isRtl ? 'لا تأملات بعد' : 'No entries yet')
                : isRtl
                  ? `${entries.length} تأمل · ${totalWords.toLocaleString()} كلمة`
                  : `${entries.length} ${entries.length === 1 ? 'entry' : 'entries'} · ${totalWords.toLocaleString()} words`}
            </p>
          </div>
        </div>

        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          {/* Export button */}
          {entries.length > 0 && (
            <button
              onClick={() => exportEntries(entries, isRtl)}
              title={isRtl ? 'تصدير المذكرة' : 'Export journal'}
              className="p-2 rounded-xl border border-gray-200 text-gray-400 hover:text-violet-600 hover:border-violet-300 transition-colors"
            >
              <Download className="w-4 h-4" />
            </button>
          )}

          {/* New entry button */}
          <button
            onClick={() => setShowForm(v => !v)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors',
              showForm
                ? 'bg-gray-100 text-gray-600'
                : 'bg-violet-600 text-white hover:bg-violet-700'
            )}
          >
            {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            <span className={isRtl ? 'font-arabic' : ''}>
              {isRtl ? (showForm ? 'إلغاء' : 'إضافة تأمل') : (showForm ? 'Cancel' : 'New Entry')}
            </span>
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <StatsBar entries={entries} isRtl={isRtl} />

      {/* New entry form */}
      {showForm && (
        <div className="mb-6">
          <EntryForm
            onSave={handleSave}
            onCancel={() => setShowForm(false)}
            isRtl={isRtl}
            promptIndex={entries.length}
          />
        </div>
      )}

      {/* Search + filter + sort */}
      {entries.length > 0 && (
        <div className="mb-4 space-y-2">
          {/* Search row */}
          <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
            <div className={clsx('flex-1 flex items-center gap-2 bg-white rounded-xl border border-gray-200 px-3 py-2', isRtl && 'flex-row-reverse')}>
              <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder={isRtl ? 'ابحث في تأملاتك…' : 'Search your reflections…'}
                className={clsx('flex-1 text-sm bg-transparent outline-none text-gray-700', isRtl && 'font-arabic text-right')}
                dir={isRtl ? 'rtl' : 'ltr'}
              />
              {search && (
                <button onClick={() => setSearch('')} className="text-gray-300 hover:text-gray-500">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            {/* Sort button */}
            <div className="relative">
              <button
                onClick={() => setShowSort(v => !v)}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs transition-colors whitespace-nowrap',
                  showSort ? 'bg-violet-50 border-violet-300 text-violet-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'
                )}
              >
                <ArrowUpDown className="w-3.5 h-3.5" />
                {isRtl ? SORT_LABELS[sortMode].ar : SORT_LABELS[sortMode].en}
              </button>
              {showSort && (
                <div className={clsx(
                  'absolute top-full mt-1 z-10 bg-white rounded-xl border border-gray-100 shadow-lg py-1 min-w-[140px]',
                  isRtl ? 'right-0' : 'right-0'
                )}>
                  {(Object.entries(SORT_LABELS) as [SortMode, { en: string; ar: string }][]).map(([mode, label]) => (
                    <button
                      key={mode}
                      onClick={() => { setSortMode(mode); setShowSort(false); }}
                      className={clsx(
                        'w-full text-left px-4 py-2 text-xs hover:bg-gray-50 transition-colors',
                        sortMode === mode ? 'text-violet-600 font-medium' : 'text-gray-600',
                        isRtl && 'font-arabic text-right'
                      )}
                    >
                      {isRtl ? label.ar : label.en}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Category filter chips */}
          <div className={clsx('flex items-center gap-1.5 flex-wrap', isRtl && 'flex-row-reverse')}>
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <button
              onClick={() => setFilterCat('all')}
              className={clsx(
                'text-xs px-2.5 py-0.5 rounded-full border transition-colors',
                filterCat === 'all'
                  ? 'bg-violet-100 text-violet-700 border-violet-200'
                  : 'text-gray-500 border-gray-200 hover:bg-gray-50'
              )}
            >
              {isRtl ? `الكل (${entries.length})` : `All (${entries.length})`}
            </button>
            {CATEGORIES.map(c => {
              const meta = CATEGORY_META[c];
              const count = catCounts[c] ?? 0;
              if (count === 0) return null;
              return (
                <button
                  key={c}
                  onClick={() => setFilterCat(c === filterCat ? 'all' : c)}
                  className={clsx(
                    'text-xs px-2.5 py-0.5 rounded-full border transition-colors',
                    filterCat === c
                      ? `${COLOR_CLASSES[meta.color]?.badge ?? ''} border-transparent`
                      : 'text-gray-500 border-gray-200 hover:bg-gray-50'
                  )}
                >
                  {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
                  {count > 0 && <span className="ms-1 opacity-60">({count})</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Entries */}
      {filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map(e => (
            <EntryCard
              key={e.id}
              entry={e}
              isRtl={isRtl}
              onDelete={() => {
                if (window.confirm(isRtl ? 'حذف هذا التأمل؟' : 'Delete this entry?')) {
                  deleteEntry(e.id);
                }
              }}
              onUpdate={patch => updateEntry(e.id, patch)}
            />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <div className="text-center py-16">
          <BookOpenCheck className="w-12 h-12 text-violet-200 mx-auto mb-4" />
          <p className={clsx('text-gray-500 text-sm mb-2', isRtl && 'font-arabic')}>
            {isRtl ? 'لا تأملات بعد' : 'No reflections yet'}
          </p>
          <p className={clsx('text-gray-400 text-xs mb-2 max-w-xs mx-auto', isRtl && 'font-arabic')}>
            {isRtl
              ? 'اضغط "إضافة تأمل" لتدوين أفكارك حول آيات القرآن الكريم'
              : 'Tap "New Entry" to record your thoughts on Quranic verses'}
          </p>
          <p className={clsx('text-gray-300 text-xs italic mb-6 max-w-xs mx-auto', isRtl && 'font-arabic')}>
            {isRtl ? PROMPTS_AR[0] : PROMPTS_EN[0]}
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            {isRtl ? 'ابدأ الآن' : 'Start Now'}
          </button>
        </div>
      ) : (
        <p className={clsx('text-center text-sm text-gray-400 py-8', isRtl && 'font-arabic')}>
          {isRtl ? 'لا نتائج للبحث' : 'No matching entries'}
        </p>
      )}

      {/* Privacy note */}
      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'تأملاتك محفوظة محلياً على جهازك فقط — لا تُرفع إلى أي خادم'
          : 'Your journal is stored locally on your device only — never uploaded'}
      </p>
    </div>
  );
}
