/**
 * Third-party notices: content sources, fonts and every npm package shipped
 * in the bundle with its licence text.
 *
 * The package list is generated at build time by rollup-plugin-license
 * (vite.config.ts) into third-party-licenses.json next to index.html, so it
 * always matches what was actually bundled. The dev server has no build
 * output; the page says so instead of showing an empty list.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { Scale } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { safeHttpUrl } from '../lib/safeUrl';

interface PackageNotice {
  name: string;
  version: string | null;
  license: string | null;
  author: string | null;
  repository: string | null;
  licenseText: string | null;
  noticeText: string | null;
}

interface NoticesFile {
  generatedAt: string;
  packages: PackageNotice[];
  fonts?: PackageNotice[];
}

type Bi = { ar: string; en: string };

interface ContentSource {
  name: string;
  url: string;
  what: Bi;
  terms: Bi;
}

/** Content sources whose terms are public. Wording describes what is used and
 *  points to the provider's own terms; it does not claim permissions beyond them. */
const CONTENT_SOURCES: ContentSource[] = [
  {
    name: 'Tanzil Project',
    url: 'https://tanzil.net',
    what: { ar: 'نص القرآن الكريم (الرسم العثماني والإملائي)', en: "Qur'an text (Uthmani and simple scripts)" },
    terms: {
      ar: 'برخصة المشاع الإبداعي CC BY 3.0، ويُعرض النص دون أي تغيير.',
      en: 'Creative Commons Attribution 3.0 (CC BY 3.0); the text is shown without any change.',
    },
  },
  {
    name: 'QuranEnc.com',
    url: 'https://quranenc.com',
    what: { ar: 'ترجمات معاني القرآن', en: "Translations of the Qur'an's meanings" },
    terms: { ar: 'وفق شروط الاستخدام المنشورة في الموقع.', en: 'Under the terms of use published on the site.' },
  },
  {
    name: 'riotu-lab/Quran-Tafseers (Hugging Face)',
    url: 'https://huggingface.co/datasets/riotu-lab/Quran-Tafseers',
    what: { ar: 'نصوص التفاسير العربية المستخدمة في التطبيق', en: 'Arabic tafsir texts used by the app' },
    terms: {
      ar: 'برخصة Apache-2.0، من مختبر RIOTU بجامعة الأمير سلطان.',
      en: 'Apache-2.0, published by the RIOTU Lab at Prince Sultan University.',
    },
  },
  {
    name: 'everyayah.com · cdn.islamic.network · quranicaudio.com · verses.quran.com',
    url: 'https://everyayah.com',
    what: { ar: 'تلاوات صوتية تُبثّ من هذه الخدمات', en: 'Recitation audio streamed from these services' },
    terms: {
      ar: 'الحقوق للقرّاء والجهات الناشرة؛ يظهر اسم القارئ في مشغّل التلاوة.',
      en: 'Rights belong to the reciters and publishers; the reciter is named in the player.',
    },
  },
];

export function LicensesPage() {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const [data, setData] = useState<NoticesFile | null>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'missing'>('loading');
  const [filter, setFilter] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetch(`${import.meta.env.BASE_URL}third-party-licenses.json`)
      .then((r) => (r.ok ? (r.json() as Promise<NoticesFile>) : Promise.reject(new Error(String(r.status)))))
      .then((json) => {
        if (cancelled) return;
        if (!Array.isArray(json.packages)) throw new Error('bad file');
        setData(json);
        setState('ready');
      })
      .catch(() => !cancelled && setState('missing'));
    return () => {
      cancelled = true;
    };
  }, []);

  const h2 = clsx('mb-3 text-lg font-semibold text-gray-900', isAr && 'font-arabic');
  const q = filter.trim().toLowerCase();
  const packages = (data?.packages ?? []).filter((p) => !q || p.name.toLowerCase().includes(q) || (p.license ?? '').toLowerCase().includes(q));

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6" dir={isAr ? 'rtl' : 'ltr'}>
      <div className="mb-2 flex items-center gap-3">
        <Scale className="h-7 w-7 text-primary-700" aria-hidden="true" />
        <h1 className={clsx('text-2xl font-bold text-gray-900', isAr && 'font-arabic')}>
          {isAr ? 'التراخيص وإشعارات الأطراف الثالثة' : 'Licences and third-party notices'}
        </h1>
      </div>
      <p className={clsx('mb-8 text-gray-600', isAr && 'font-arabic')}>
        {isAr ? 'مصادر المحتوى بالتفصيل في ' : 'Content sources are described in detail on '}
        <Link to="/sources" className="text-primary-700 underline">
          {isAr ? 'صفحة المصادر' : 'the Sources page'}
        </Link>
        {isAr ? '.' : '.'}
      </p>

      <section className="mb-8" aria-labelledby="lic-content">
        <h2 id="lic-content" className={h2}>{isAr ? 'المحتوى' : 'Content'}</h2>
        <ul className="space-y-3">
          {CONTENT_SOURCES.map((s) => (
            <li key={s.name} className="rounded-xl border border-gray-200 bg-white p-4">
              <a href={safeHttpUrl(s.url) ?? undefined} target="_blank" rel="noopener noreferrer" dir="ltr" className="font-semibold text-primary-700 underline">
                {s.name}
              </a>
              <p className={clsx('mt-1 text-sm text-gray-800', isAr && 'font-arabic')}>{isAr ? s.what.ar : s.what.en}</p>
              <p className={clsx('mt-0.5 text-sm text-gray-600', isAr && 'font-arabic')}>{isAr ? s.terms.ar : s.terms.en}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="mb-8" aria-labelledby="lic-fonts">
        <h2 id="lic-fonts" className={h2}>{isAr ? 'الخطوط' : 'Fonts'}</h2>
        <p className={clsx('mb-3 text-sm text-gray-700', isAr && 'font-arabic')}>
          {isAr
            ? 'الخطوط مضمّنة في التطبيق، وكلها برخصة SIL Open Font License 1.1.'
            : 'Fonts are bundled with the app; all are licensed under the SIL Open Font License 1.1.'}
        </p>
        {state === 'ready' && data?.fonts?.length ? (
          <NoticeList items={data.fonts} />
        ) : (
          <ul className="list-disc ps-5 text-sm text-gray-700" dir="ltr">
            <li>Scheherazade New — SIL Global</li>
            <li>Noto Naskh Arabic — The Noto Project Authors</li>
            <li>Amiri — The Amiri Project Authors</li>
            <li>Inter — The Inter Project Authors</li>
          </ul>
        )}
      </section>

      <section aria-labelledby="lic-npm">
        <h2 id="lic-npm" className={h2}>{isAr ? 'المكتبات البرمجية' : 'Software libraries'}</h2>
        {state === 'loading' && <p className="text-sm text-gray-600">{isAr ? 'جارٍ التحميل…' : 'Loading…'}</p>}
        {state === 'missing' && (
          <p className={clsx('text-sm text-gray-600', isAr && 'font-arabic')}>
            {isAr
              ? 'تُنشأ قائمة المكتبات عند بناء التطبيق، وهي غير متاحة في نسخة التطوير.'
              : 'The library list is generated when the app is built and is not available in development mode.'}
          </p>
        )}
        {state === 'ready' && data && (
          <>
            <p className={clsx('mb-3 text-sm text-gray-700', isAr && 'font-arabic')}>
              {isAr ? 'عدد الحزم: ' : 'Packages: '}
              <bdi dir="ltr">{data.packages.length}</bdi>
            </p>
            <label htmlFor="lic-filter" className={clsx('mb-1 block text-sm font-medium text-gray-700', isAr && 'font-arabic')}>
              {isAr ? 'تصفية حسب الاسم أو الرخصة' : 'Filter by name or licence'}
            </label>
            <input
              id="lic-filter"
              type="search"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              dir="ltr"
              className="input mb-4 min-h-11"
            />
            <NoticeList items={packages} />
          </>
        )}
      </section>
    </div>
  );
}

function NoticeList({ items }: { items: PackageNotice[] }) {
  return (
    <ul className="space-y-2" dir="ltr">
      {items.map((p) => {
        const repo = p.repository ? safeHttpUrl(p.repository.replace(/^git\+/, '').replace(/\.git$/, '')) : null;
        return (
          <li key={`${p.name}@${p.version}`} className="rounded-lg border border-gray-200 bg-white">
            <details>
              <summary className="flex min-h-11 cursor-pointer flex-wrap items-center gap-x-2 px-3 py-2 text-sm">
                <span className="font-medium text-gray-900">{p.name}</span>
                {p.version && <span className="text-gray-600">{p.version}</span>}
                <span className="ms-auto rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">{p.license ?? 'UNKNOWN'}</span>
              </summary>
              <div className="border-t border-gray-100 px-3 py-2 text-xs text-gray-700">
                {p.author && <p className="mb-1">{p.author}</p>}
                {repo && (
                  <p className="mb-1">
                    <a href={repo} target="_blank" rel="noopener noreferrer" className="text-primary-700 underline break-all">{repo}</a>
                  </p>
                )}
                {p.licenseText && <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] leading-snug">{p.licenseText}</pre>}
                {p.noticeText && <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] leading-snug">{p.noticeText}</pre>}
              </div>
            </details>
          </li>
        );
      })}
    </ul>
  );
}

export default LicensesPage;
