import { useState, useEffect } from 'react';
import { BookOpen, Shield, CheckCircle, AlertCircle, ChevronDown, ChevronUp, ToggleLeft, ToggleRight, Lock, X, Key } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { ragApi, TafseerSource } from '../lib/api';
import clsx from 'clsx';

const ADMIN_TOKEN_KEY = 'tadabbur_admin_token';

interface SourcesResponse {
  sources: TafseerSource[];
  count: number;
  provenance_verified: number;
}

export function SourcesPage() {
  const { language } = useLanguageStore();

  // Admin mode state - token stored in localStorage (not URL for security)
  const [adminToken, setAdminToken] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(ADMIN_TOKEN_KEY);
    }
    return null;
  });
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [tokenInput, setTokenInput] = useState('');
  const [adminError, setAdminError] = useState<string | null>(null);
  const isAdminMode = !!adminToken;

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
        if (err.response?.status === 401) {
          // Invalid token - clear it
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
      localStorage.setItem(ADMIN_TOKEN_KEY, tokenInput);
      setAdminToken(tokenInput);
      setShowAdminModal(false);
      setTokenInput('');
    } catch (err: any) {
      if (err.response?.status === 401) {
        setAdminError(language === 'ar' ? 'رمز غير صالح' : 'Invalid token');
      } else {
        setAdminError(language === 'ar' ? 'خطأ في الاتصال' : 'Connection error');
      }
    }
  }

  function handleExitAdminMode() {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
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

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Admin Mode Controls */}
      <div className="mb-4 flex items-center justify-between">
        {isAdminMode ? (
          <div className="flex-1 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-amber-600" />
              <span className="text-sm text-amber-800 font-medium">
                {language === 'ar' ? 'وضع المسؤول - يمكنك تفعيل/تعطيل المصادر' : 'Admin Mode - You can enable/disable sources'}
              </span>
            </div>
            <button
              onClick={handleExitAdminMode}
              className="text-sm text-amber-700 hover:text-amber-900 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              {language === 'ar' ? 'خروج' : 'Exit'}
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowAdminModal(true)}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <Key className="w-4 h-4" />
            {language === 'ar' ? 'وضع المسؤول' : 'Admin Mode'}
          </button>
        )}
      </div>

      {/* Admin Token Modal */}
      {showAdminModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {language === 'ar' ? 'دخول وضع المسؤول' : 'Enter Admin Mode'}
              </h3>
              <button
                onClick={() => { setShowAdminModal(false); setTokenInput(''); setAdminError(null); }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              {language === 'ar'
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
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => { setShowAdminModal(false); setTokenInput(''); setAdminError(null); }}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                {language === 'ar' ? 'إلغاء' : 'Cancel'}
              </button>
              <button
                onClick={handleEnterAdminMode}
                disabled={!tokenInput.trim()}
                className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {language === 'ar' ? 'دخول' : 'Enter'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <BookOpen className="w-8 h-8 text-primary-600" />
          {language === 'ar' ? 'مصادر التفسير' : 'Tafseer Sources'}
        </h1>
        <p className="text-gray-600">
          {language === 'ar'
            ? 'المصادر المتاحة للتفسير القرآني مع بيانات المصدر والتحقق'
            : 'Available sources for Quranic tafseer with provenance data and verification status'}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600">{sources.length}</div>
          <div className="text-sm text-gray-500">
            {language === 'ar' ? 'مصادر متاحة' : 'Available Sources'}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-green-600">{provenanceVerified}</div>
          <div className="text-sm text-gray-500">
            {language === 'ar' ? 'تم التحقق' : 'Verified Provenance'}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-amber-600">
            {sources.filter(s => s.era === 'classical').length}
          </div>
          <div className="text-sm text-gray-500">
            {language === 'ar' ? 'تفاسير تراثية' : 'Classical Tafseers'}
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

      {/* Provenance Notice */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-900 mb-1">
              {language === 'ar' ? 'حول التحقق من المصادر' : 'About Source Verification'}
            </h3>
            <p className="text-sm text-blue-700">
              {language === 'ar'
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
          className="flex-1 text-left flex items-start justify-between gap-4"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className={clsx(
                "text-lg font-semibold",
                isEnabled ? "text-gray-900" : "text-gray-500"
              )}>{name}</h3>
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
            <span className={clsx(
              'text-xs px-2 py-0.5 rounded',
              source.reliability_score >= 0.9 ? 'bg-green-100 text-green-700' :
              source.reliability_score >= 0.7 ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'
            )}>
              {language === 'ar' ? 'موثوقية' : 'Reliability'}: {Math.round(source.reliability_score * 100)}%
            </span>
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
