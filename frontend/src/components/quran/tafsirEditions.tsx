/**
 * Tafsir editions offered by the readers and the attribution line shown under
 * every displayed tafsir excerpt (title, author, source id, licence, host).
 * Kept apart from TafsirPanel so the Mushaf reader can share it without
 * loading the whole panel.
 */
import clsx from 'clsx';
import { ExternalLink } from 'lucide-react';
import { getSourceById } from '../../data/sourceRegistry';

export interface TafsirEdition {
  id: string;
  slug: string;
  name_ar: string;
  name_en: string;
  author_ar: string;
  author_en: string;
  language: string;
  has_audio: boolean;
  source: string;
  description_ar?: string;
  description_en?: string;
  /**
   * Id of the same work in the app's tafsir library (tafseer_chunks). The AI
   * assistant is grounded on that stored passage, loaded by the server; editions
   * without one have no AI assistant.
   */
  db_source_id?: string;
}

// =============================================================================
// Tafsir Editions Configuration
// =============================================================================

// Only editions the backend lists (TAFSIR_EDITIONS in tafsir_api.py), and
// every one names its licensed library source in db_source_id: the server
// serves that stored passage first (source "tadabbur_library"). Al-Wasit
// (Tantawi, d. 2010) is under copyright with no recorded permission, and
// al-Mukhtasar, Ibn Juzayy, al-Suddi and al-Siraj always returned 404.
// Tafsir as-Sa'di and the Arabic al-Jalalayn were removed 2026-10-14: neither
// has a recorded licence in data/manifests/tafseer_sources.json.
// Al-Muyassar is not offered while its King Fahd Complex terms await owner
// confirmation (manifest licence_hold_ids; license_verified=0, so the server
// refuses it with EDITION_NOT_LICENSED). The first edition is the readers'
// default: Tafsir al-Baghawi, a cleared classical source.
// has_audio stays false for every edition until the owner confirms the
// read.tafsir.one tafsir-audio terms (owner review: tafsir-audio-unverified).
export const TAFSIR_EDITIONS: TafsirEdition[] = [
  {
    id: 'baghawi',
    db_source_id: 'baghawi_ar',
    slug: 'baghawi',
    name_ar: 'معالم التنزيل',
    name_en: "Ma'alim at-Tanzil",
    author_ar: 'الإمام البغوي',
    author_en: 'Imam Al-Baghawi',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'تفسير وسط بين المأثور والرأي',
    description_en: 'Balanced tafsir',
  },
  {
    id: 'ibn_kathir',
    db_source_id: 'ibn_kathir_ar',
    slug: 'ibn-kathir',
    name_ar: 'تفسير ابن كثير',
    name_en: 'Tafsir Ibn Kathir',
    author_ar: 'الحافظ ابن كثير الدمشقي',
    author_en: 'Imam Ibn Kathir',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'من أشهر التفاسير بالمأثور',
    description_en: 'Famous classical tafsir based on hadith',
  },
  {
    id: 'tabari',
    db_source_id: 'tabari_ar',
    slug: 'tabari',
    name_ar: 'جامع البيان - الطبري',
    name_en: 'Jami al-Bayan (At-Tabari)',
    author_ar: 'الإمام الطبري',
    author_en: 'Imam At-Tabari',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'أقدم التفاسير وأشملها',
    description_en: 'Earliest and most comprehensive tafsir',
  },
  {
    id: 'qurtubi',
    db_source_id: 'qurtubi_ar',
    slug: 'qurtubi',
    name_ar: 'الجامع لأحكام القرآن',
    name_en: 'Al-Jami (Al-Qurtubi)',
    author_ar: 'الإمام القرطبي',
    author_en: 'Imam Al-Qurtubi',
    language: 'ar',
    has_audio: false,
    source: 'quran_com',
    description_ar: 'تفسير فقهي شامل',
    description_en: 'Comprehensive fiqh-focused tafsir',
  },
];

/** The readers' default edition (TafsirPanel, Mushaf sheet, Qur'an page prefetch). */
export const DEFAULT_TAFSIR_EDITION_ID = TAFSIR_EDITIONS[0].id;

// =============================================================================
// Attribution footer (exported so other tafsir views, e.g. the Mushaf sheet,
// show the same title, author, licence and source line)
// =============================================================================

/** `source` value for passages served from the app's own licensed library. */
export const LOCAL_LIBRARY_SOURCE = 'tadabbur_library';

const HOST_LABELS: Record<string, string> = {
  quran_com: 'Quran.com',
  quran_tafseer: 'quran-tafseer.com',
  tafsir_one: 'read.tafsir.one',
};

export interface TafsirAttributionEdition {
  id: string;
  name_ar: string;
  name_en: string;
  author_ar: string;
  author_en: string;
  db_source_id?: string;
}

export function TafsirAttributionFooter({
  edition,
  source,
  sourceUrl,
  language,
}: {
  edition: TafsirAttributionEdition;
  /** Host the text was fetched from (API `source` field). */
  source: string;
  sourceUrl?: string;
  language: 'ar' | 'en';
}) {
  const ar = language === 'ar';
  const registry = edition.db_source_id ? getSourceById(edition.db_source_id) : undefined;
  const fromLibrary = source === LOCAL_LIBRARY_SOURCE;
  return (
    <div
      className={clsx('pt-2 border-t border-gray-100 text-xs text-gray-500 space-y-0.5', ar && 'font-arabic')}
      data-testid="tafsir-attribution"
      dir={ar ? 'rtl' : 'ltr'}
    >
      <p>
        <span dir={ar ? 'rtl' : 'ltr'}>{ar ? edition.name_ar : edition.name_en}</span>
        {' — '}
        <span>{ar ? edition.author_ar : edition.author_en}</span>
        {' · '}
        <bdi dir="ltr" className="font-mono text-[10px]">{edition.db_source_id ?? edition.id}</bdi>
      </p>
      <p>
        {ar ? 'الترخيص: ' : 'Licence: '}
        {registry ? (
          <span dir="ltr" lang="en">{registry.licenseOrTerms}</span>
        ) : (
          <span>{ar ? 'غير موثّق بعد' : 'not yet recorded'}</span>
        )}
      </p>
      <p className="flex items-center gap-2 flex-wrap">
        <span>
          {ar ? 'المصدر: ' : 'Source: '}
          {fromLibrary ? (
            <span>{ar ? 'نسخة مخزّنة في مكتبة تدبّر' : 'Copy stored in the Tadabbur library'}</span>
          ) : (
            <bdi dir="ltr">{HOST_LABELS[source] ?? source}</bdi>
          )}
        </span>
        {sourceUrl && (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-amber-600 hover:text-amber-700 hover:underline"
          >
            <ExternalLink className="w-3 h-3" />
            {ar ? 'عرض المصدر' : 'View source'}
          </a>
        )}
      </p>
    </div>
  );
}


/**
 * Public page for the excerpt on the host it was fetched from, or the
 * registry's source page for a passage served from the local library.
 */
export function tafsirSourceUrl(
  source: string,
  sura: number,
  ayah: number,
  slug?: string,
  dbSourceId?: string,
): string | undefined {
  if (source === LOCAL_LIBRARY_SOURCE) {
    return dbSourceId ? getSourceById(dbSourceId)?.sourceUrl : undefined;
  }
  if (source === 'quran_com') return `https://quran.com/${sura}/${ayah}/tafsirs`;
  if (source === 'quran_tafseer') return 'http://quran-tafseer.com';
  return `https://read.tafsir.one/${slug ?? ''}`;
}

export function getTafsirEdition(id: string): TafsirEdition | undefined {
  return TAFSIR_EDITIONS.find((e) => e.id === id);
}
