/**
 * Sources & licences — every source the app shows text or data from.
 *
 * Sections are built from SOURCE_REGISTRY (frontend/src/data/sourceRegistry.ts),
 * so a source cannot be used without appearing here; blocked sources and
 * entries no longer used at runtime are left out. The tafsir section keeps the
 * live list from /rag/sources. No numeric "reliability" score is shown to
 * readers: ranking classical scholars by percentage is not something the app
 * can source. Admin mode (enable/disable sources) only appears with ?admin=1
 * or an admin token already in this tab.
 */
import { useState, useEffect } from 'react';
import { BookOpen, Shield, CheckCircle, AlertCircle, ChevronDown, ChevronUp, ToggleLeft, ToggleRight, Lock, X, Key, ExternalLink } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { ragApi, TafseerSource } from '../lib/api';
import clsx from 'clsx';
import { SourceBadge } from '../components/common/SourceBadge';
import {
  SOURCE_REGISTRY,
  isSourceDisplayBlocked,
  type ReliabilityLevel,
  type Source,
  type SourceType,
} from '../data/sourceRegistry';

function scoreToReliability(score: number): ReliabilityLevel {
  if (score >= 0.97) return 'canonical';
  if (score >= 0.85) return 'verified';
  if (score >= 0.60) return 'supporting';
  return 'experimental';
}

const ADMIN_TOKEN_KEY = 'tadabbur_admin_token';

/** Registry entries kept for provenance but not used at runtime. */
function isRetired(source: Source): boolean {
  const notes = source.notes.trimStart();
  return notes.startsWith('NOT SERVED') || notes.startsWith('Not used at runtime');
}

/** Sources listed to readers: neither blocked nor retired. */
function listedSources(types: SourceType[]): Source[] {
  return SOURCE_REGISTRY.filter(
    (s) => types.includes(s.type) && !isSourceDisplayBlocked(s) && !isRetired(s),
  );
}

const REGISTRY_SECTIONS: { key: string; types: SourceType[]; ar: string; en: string }[] = [
  { key: 'quran', types: ['quran_text'], ar: 'نص القرآن الكريم', en: 'Qur’an text' },
  { key: 'translations', types: ['translation'], ar: 'الترجمات', en: 'Translations' },
  { key: 'lexicons', types: ['lexicon'], ar: 'المعاجم والمفردات', en: 'Lexicons and vocabulary' },
  { key: 'audio', types: ['audio'], ar: 'التلاوات الصوتية', en: 'Recitations' },
  { key: 'services', types: ['service'], ar: 'خدمات أخرى', en: 'Other services' },
];

const HOW_WE_USE_SOURCES = {
  en: 'The Qur’an text is shown exactly as published by the Tanzil Project. Translations come from QuranEnc. When you ask a question, the app first finds passages from the tafsir books listed below, then an AI model summarises only those passages and cites them. If no passage answers the question, the app says so instead of guessing. AI summaries are not tafsir and not fatwa.',
  ar: 'يُعرض نص القرآن الكريم كما نشره مشروع تنزيل دون تغيير، والترجمات من موقع QuranEnc. عند طرح سؤال يبحث التطبيق أولاً عن مقاطع من كتب التفسير المذكورة أدناه، ثم يلخّصها نموذج ذكاء اصطناعي مع ذكر مصدر كل مقطع. وإذا لم يجد ما يجيب عن السؤال صرّح بذلك ولم يخمّن. ملخصات الذكاء الاصطناعي ليست تفسيراً ولا فتوى.',
};

function licenceStatusLabel(source: Source, ar: boolean): string | null {
  switch (source.licenseStatus) {
    case 'cleared':
      return null;
    case 'restricted':
      return ar ? 'استخدام مقيَّد' : 'Restricted use';
    case 'unverified':
      return ar ? 'الترخيص قيد التحقق' : 'Licence under review';
    default:
      return null;
  }
}

function RegistrySourceCard({ source, language }: { source: Source; language: 'ar' | 'en' }) {
  const ar = language === 'ar';
  const status = licenceStatusLabel(source, ar);
  return (
    <li className="card p-4" dir={ar ? 'rtl' : 'ltr'}>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className={clsx('font-semibold text-gray-900', ar && 'font-arabic')}>
          {ar ? source.titleArabic : source.titleEnglish}
        </h3>
        {status && (
          <span className={clsx('text-[11px] px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200', ar && 'font-arabic')}>
            {status}
          </span>
        )}
      </div>
      <p className="mt-1 text-sm text-gray-600" dir="ltr" lang="en">{source.author}</p>
      <p className={clsx('mt-2 text-xs text-gray-600', ar && 'font-arabic')}>
        <span className="font-medium">{ar ? 'الترخيص والشروط: ' : 'Licence and terms: '}</span>
        {/* Registry terms are recorded in English. */}
        <span dir="ltr" lang="en">{source.licenseOrTerms}</span>
      </p>
      {source.sourceUrl.startsWith('http') && (
        <a
          href={source.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-flex items-center gap-1 text-xs text-primary-700 hover:underline"
          dir="ltr"
        >
          <ExternalLink className="w-3 h-3" />
          {source.sourceUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')}
        </a>
      )}
    </li>
  );
}

function RegistrySection({ title, sources, language }: { title: string; sources: Source[]; language: 'ar' | 'en' }) {
  if (sources.length === 0) return null;
  const ar = language === 'ar';
  return (
    <section className="mb-8">
      <h2 className={clsx('text-xl font-semibold text-gray-900 mb-3', ar && 'font-arabic')}>{title}</h2>
      <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sources.map((s) => (
          <RegistrySourceCard key={s.sourceId} source={s} language={language} />
        ))}
      </ul>
    </section>
  );
}

interface SourcesResponse {
  sources: TafseerSource[];
  count: number;
  provenance_verified: number;
}

export function SourcesPage() {
  const { language } = useLanguageStore();

  // Admin mode state - token kept in sessionStorage for this tab only (never the URL or localStorage)
  const [adminToken, setAdminToken] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem(ADMIN_TOKEN_KEY);
    }
    return null;
  });
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [tokenInput, setTokenInput] = useState('');
  const [adminError, setAdminError] = useState<string | null>(null);
  const isAdminMode = !!adminToken;
  const adminRequested =
    typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('admin') === '1';

  const [sources, setSources] = useState<TafseerSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [provenanceVerified, setProvenanceVerified] = useState(0);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [togglingSource, setTogglingSource] = useState<string | null>(null);

  // Load sources
  useEffect(() => {
    async function loadSources() {
      setLoading(true);
      setError(null);
      try {
        let response;
        if (isAdminMode && adminToken) {
          response = await ragApi.getAdminSources(adminToken);
        } else {
          response = await ragApi.getSources();
        }
        const data = response.data as unknown as SourcesResponse;
        setSources(data.sources);
        setProvenanceVerified(data.provenance_verified || 0);
      } catch (err: any) {
        console.error('Failed to load sources:', err);
        const status = err.response?.status;
        if (status === 401 || status === 403 || status === 422) {
          // Invalid (or missing) token — clear it and prompt re-entry.
          handleExitAdminMode();
          setError(
            language === 'ar'
              ? 'رمز المسؤول غير صالح - تم إلغاء وضع المسؤول'
              : 'Invalid admin token - admin mode disabled'
          );
        } else {
          setError(
            language === 'ar'
              ? 'فشل في تحميل المصادر'
              : 'Failed to load sources'
          );
        }
      } finally {
        setLoading(false);
      }
    }
    loadSources();
  }, [language, isAdminMode, adminToken]);

  async function handleEnterAdminMode() {
    if (!tokenInput.trim()) return;
    setAdminError(null);

    // Test the token by making an admin request
    try {
      await ragApi.getAdminSources(tokenInput);
      // Token is valid
      sessionStorage.setItem(ADMIN_TOKEN_KEY, tokenInput);
      setAdminToken(tokenInput);
      setShowAdminModal(false);
      setTokenInput('');
    } catch (err: any) {
      // Backend returns 403 for wrong token, 422 when header is missing or
      // empty (FastAPI validation), and 401 only via the newer admin_auth
      // middleware. All three are user-fixable "wrong token" — distinguish
      // from genuine network errors where err.response is undefined.
      const status = err.response?.status;
      if (status === 401 || status === 403 || status === 422) {
        setAdminError(language === 'ar' ? 'رمز غير صالح' : 'Invalid token');
      } else {
        setAdminError(language === 'ar' ? 'خطأ في الاتصال' : 'Connection error');
      }
    }
  }

  function handleExitAdminMode() {
    sessionStorage.removeItem(ADMIN_TOKEN_KEY);
    setAdminToken(null);
  }

  async function handleToggleSource(sourceId: string, currentEnabled: boolean) {
    if (!adminToken) return;
    setTogglingSource(sourceId);
    try {
      await ragApi.toggleSource(sourceId, !currentEnabled, adminToken);
      setSources(prev => prev.map(s =>
        s.id === sourceId ? { ...s, is_enabled: !currentEnabled } : s
      ));
    } catch (err) {
      console.error('Failed to toggle source:', err);
    } finally {
      setTogglingSource(null);
    }
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-3" />
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  const isRtl = language === 'ar';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Admin Mode Controls */}
      <div className={clsx('mb-4 flex items-center justify-between', isRtl && 'flex-row-reverse')}>
        {isAdminMode ? (
          <div className={clsx('flex-1 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between', isRtl && 'flex-row-reverse')}>
            <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
              <Lock className="w-5 h-5 text-amber-600" />
              <span className={clsx('text-sm text-amber-800 font-medium', isRtl && 'font-arabic')}>
                {isRtl ? 'وضع المسؤول - يمكنك تفعيل/تعطيل المصادر' : 'Admin Mode - You can enable/disable sources'}
              </span>
            </div>
            <button
              onClick={handleExitAdminMode}
              className={clsx('text-sm text-amber-700 hover:text-amber-900 flex items-center gap-1', isRtl && 'flex-row-reverse font-arabic')}
            >
              <X className="w-4 h-4" />
              {isRtl ? 'خروج' : 'Exit'}
            </button>
          </div>
        ) : adminRequested ? (
          <button
            onClick={() => setShowAdminModal(true)}
            className={clsx('text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1', isRtl && 'flex-row-reverse font-arabic')}
          >
            <Key className="w-4 h-4" />
            {isRtl ? 'وضع المسؤول' : 'Admin Mode'}
          </button>
        ) : null}
      </div>

      {/* Admin Token Modal */}
      {showAdminModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl" dir={isRtl ? 'rtl' : 'ltr'}>
            <div className={clsx('flex items-center justify-between mb-4', isRtl && 'flex-row-reverse')}>
              <h3 className={clsx('text-lg font-semibold text-gray-900', isRtl && 'font-arabic')}>
                {isRtl ? 'دخول وضع المسؤول' : 'Enter Admin Mode'}
              </h3>
              <button
                onClick={() => { setShowAdminModal(false); setTokenInput(''); setAdminError(null); }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className={clsx('text-sm text-gray-600 mb-4', isRtl && 'font-arabic text-right')}>
              {isRtl
                ? 'أدخل رمز المسؤول لتفعيل/تعطيل المصادر'
                : 'Enter admin token to enable/disable sources'}
            </p>
            <input
              type="password"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleEnterAdminMode()}
              placeholder={language === 'ar' ? 'رمز المسؤول' : 'Admin token'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              autoFocus
            />
            {adminError && (
              <p className="text-sm text-red-600 mt-2">{adminError}</p>
            )}
            <div className={clsx('flex gap-2 mt-4', isRtl ? 'justify-start flex-row-reverse' : 'justify-end')}>
              <button
                onClick={() => { setShowAdminModal(false); setTokenInput(''); setAdminError(null); }}
                className={clsx('px-4 py-2 text-sm text-gray-600 hover:text-gray-800', isRtl && 'font-arabic')}
              >
                {isRtl ? 'إلغاء' : 'Cancel'}
              </button>
              <button
                onClick={handleEnterAdminMode}
                disabled={!tokenInput.trim()}
                className={clsx('px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50', isRtl && 'font-arabic')}
              >
                {isRtl ? 'دخول' : 'Enter'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <h1 className={clsx('text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3', isRtl && 'font-arabic flex-row-reverse')}>
          <BookOpen className="w-8 h-8 text-primary-600" />
          {isRtl ? 'المصادر والتراخيص' : 'Sources & licences'}
        </h1>
        <p className={clsx('text-gray-600', isRtl && 'font-arabic text-right')}>
          {isRtl
            ? 'كل مصدر يعرض التطبيق نصّه أو بياناته، مع ترخيصه ورابطه.'
            : 'Every source whose text or data the app shows, with its licence and a link.'}
        </p>
      </div>

      {/* How we use sources */}
      <section className="mb-8 p-4 bg-primary-50 border border-primary-100 rounded-lg">
        <h2 className={clsx('font-semibold text-primary-900 mb-1', isRtl && 'font-arabic')}>
          {isRtl ? 'كيف نستخدم المصادر' : 'How we use sources'}
        </h2>
        <p className={clsx('text-sm text-primary-900 leading-relaxed', isRtl && 'font-arabic')} dir={isRtl ? 'rtl' : 'ltr'}>
          {isRtl ? HOW_WE_USE_SOURCES.ar : HOW_WE_USE_SOURCES.en}
        </p>
      </section>

      {REGISTRY_SECTIONS.slice(0, 2).map((sec) => (
        <RegistrySection
          key={sec.key}
          title={isRtl ? sec.ar : sec.en}
          sources={listedSources(sec.types)}
          language={language}
        />
      ))}

      <h2 className={clsx('text-xl font-semibold text-gray-900 mb-3', isRtl && 'font-arabic')}>
        {isRtl ? 'التفاسير' : 'Tafsir'}
      </h2>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">{sources.length}</div>
          <div className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
            {isRtl ? 'مصادر متاحة' : 'Available Sources'}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-green-600">{provenanceVerified}</div>
          <div className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
            {isRtl ? 'تم التحقق' : 'Verified Provenance'}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-amber-600">
            {sources.filter(s => s.era === 'classical').length}
          </div>
          <div className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
            {isRtl ? 'تفاسير تراثية' : 'Classical Tafseers'}
          </div>
        </div>
      </div>

      {/* Source List */}
      <div className="space-y-4">
        {sources.map((source) => (
          <SourceCard
            key={source.id}
            source={source}
            language={language}
            isExpanded={expandedSource === source.id}
            onToggle={() => setExpandedSource(
              expandedSource === source.id ? null : source.id
            )}
            isAdminMode={isAdminMode}
            isToggling={togglingSource === source.id}
            onToggleEnabled={() => handleToggleSource(source.id, source.is_enabled)}
          />
        ))}
      </div>

      <div className="mt-8">
        {REGISTRY_SECTIONS.slice(2).map((sec) => (
          <RegistrySection
            key={sec.key}
            title={isRtl ? sec.ar : sec.en}
            sources={listedSources(sec.types)}
            language={language}
          />
        ))}
      </div>

      {/* Provenance Notice */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
          <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className={clsx('font-medium text-blue-900 mb-1', isRtl && 'font-arabic text-right')}>
              {isRtl ? 'حول التحقق من المصادر' : 'About Source Verification'}
            </h3>
            <p className={clsx('text-sm text-blue-700', isRtl && 'font-arabic text-right')}
               dir={isRtl ? 'rtl' : 'ltr'}>
              {isRtl
                ? 'نحن ملتزمون بالشفافية الكاملة حول مصادر بياناتنا. كل مصدر مدرج أدناه يتضمن معلومات حول أصله وترخيصه وحالة التحقق منه. المصادر التي تم التحقق منها قد تمت مراجعتها للتأكد من دقتها وصحة ترخيصها.'
                : 'We are committed to full transparency about our data sources. Each source listed below includes information about its origin, license, and verification status. Verified sources have been reviewed for accuracy and proper licensing.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface SourceCardProps {
  source: TafseerSource;
  language: 'ar' | 'en';
  isExpanded: boolean;
  onToggle: () => void;
  isAdminMode?: boolean;
  isToggling?: boolean;
  onToggleEnabled?: () => void;
}

function SourceCard({ source, language, isExpanded, onToggle, isAdminMode, isToggling, onToggleEnabled }: SourceCardProps) {
  const name = language === 'ar' ? source.name_ar : source.name_en;
  const author = language === 'ar' ? source.author_ar : source.author_en;
  const hasProvenance = (source as any).has_valid_provenance;
  const licenseVerified = (source as any).license_verified;
  const isEnabled = source.is_enabled !== false;

  return (
    <div
      className={clsx(
        'card overflow-hidden transition-all',
        !isEnabled && 'opacity-60',
        hasProvenance ? 'border-green-200' : 'border-gray-200'
      )}
      dir={language === 'ar' ? 'rtl' : 'ltr'}
    >
      <div className="flex items-start justify-between gap-4">
        <button
          onClick={onToggle}
          className="flex-1 text-start flex items-start justify-between gap-4"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className={clsx(
                'text-lg font-semibold',
                isEnabled ? 'text-gray-900' : 'text-gray-500',
                language === 'ar' && 'font-arabic'
              )}>{name}</h3>
              {isAdminMode && (
                <SourceBadge reliabilityLevel={scoreToReliability(source.reliability_score)} compact />
              )}
              {!isEnabled && (
                <span className="flex items-center gap-1 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                  {language === 'ar' ? 'معطل' : 'Disabled'}
                </span>
              )}
              {hasProvenance && isEnabled && (
                <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                  <CheckCircle className="w-3 h-3" />
                  {language === 'ar' ? 'تم التحقق' : 'Verified'}
                </span>
              )}
            </div>
          <p className="text-sm text-gray-600">{author}</p>
          {((source as any).license || (source as any).license_type) && (
            <p className={clsx('text-xs text-gray-500 mt-1', language === 'ar' && 'font-arabic')}>
              {language === 'ar' ? 'الترخيص: ' : 'Licence: '}
              <span dir="ltr" lang="en">{(source as any).license || (source as any).license_type}</span>
              {!licenseVerified && (language === 'ar' ? ' (قيد التحقق)' : ' (under review)')}
            </p>
          )}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className={clsx(
              'text-xs px-2 py-0.5 rounded',
              source.era === 'classical'
                ? 'bg-amber-100 text-amber-700'
                : 'bg-blue-100 text-blue-700'
            )}>
              {source.era === 'classical'
                ? (language === 'ar' ? 'تراثي' : 'Classical')
                : (language === 'ar' ? 'معاصر' : 'Modern')}
            </span>
            <span className="text-xs text-gray-500">
              {source.language.toUpperCase()}
            </span>
            {source.methodology && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {source.methodology === 'bil_mathur'
                  ? (language === 'ar' ? 'بالمأثور' : 'Traditional')
                  : source.methodology === 'bil_rai'
                  ? (language === 'ar' ? 'بالرأي' : 'Rational')
                  : source.methodology}
              </span>
            )}
            {(source as any).death_year_hijri && (
              <span className="text-xs text-gray-500">
                {language === 'ar' ? 'ت. ' : 'd. '}
                <bdi>{(source as any).death_year_hijri}</bdi>
                {language === 'ar' ? 'هـ' : ' AH'}
              </span>
            )}
            {/* Admin-only: an internal retrieval weight, not a judgement of the scholar. */}
            {isAdminMode && (
              <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                {language === 'ar' ? 'وزن الاسترجاع' : 'Retrieval weight'}: <bdi>{source.reliability_score.toFixed(2)}</bdi>
              </span>
            )}
          </div>
        </div>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
          )}
        </button>

        {/* Admin Toggle */}
        {isAdminMode && onToggleEnabled && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleEnabled();
            }}
            disabled={isToggling}
            className={clsx(
              'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors flex-shrink-0',
              isEnabled
                ? 'bg-green-100 hover:bg-green-200 text-green-700'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
            )}
          >
            {isToggling ? (
              <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
            ) : isEnabled ? (
              <ToggleRight className="w-5 h-5" />
            ) : (
              <ToggleLeft className="w-5 h-5" />
            )}
            <span className="text-xs font-medium">
              {isEnabled
                ? (language === 'ar' ? 'مفعل' : 'Enabled')
                : (language === 'ar' ? 'معطل' : 'Disabled')
              }
            </span>
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100 space-y-4">
          {/* Provenance Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ProvenanceField
              label={language === 'ar' ? 'معرف المصدر' : 'Source ID'}
              value={source.id}
            />
            <ProvenanceField
              label={language === 'ar' ? 'نسخة' : 'Version'}
              value={(source as any).version_tag || '-'}
            />
            <ProvenanceField
              label={language === 'ar' ? 'الترخيص' : 'License'}
              value={(source as any).license || (source as any).license_type || '-'}
              verified={licenseVerified}
            />
            <ProvenanceField
              label={language === 'ar' ? 'عدد الآيات' : 'Ayah Count'}
              value={(source as any).ayah_count?.toLocaleString() || '-'}
            />
          </div>

          {/* Primary Source Indicator */}
          {source.is_primary_source && (
            <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 p-2 rounded">
              <CheckCircle className="w-4 h-4" />
              {language === 'ar'
                ? 'هذا مصدر أولي موثوق للتفسير'
                : 'This is a verified primary source for tafseer'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ProvenanceField({ label, value, verified }: { label: string; value: string; verified?: boolean }) {
  return (
    <div className="text-sm">
      <span className="text-gray-500">{label}:</span>{' '}
      <span className="font-medium text-gray-900 flex items-center gap-1 inline-flex">
        {value}
        {verified && <CheckCircle className="w-3 h-3 text-green-500" />}
      </span>
    </div>
  );
}
