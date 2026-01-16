import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, AlertTriangle, BookOpen, LogIn, LogOut } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import clsx from 'clsx';

// Admin auth helper
const ADMIN_TOKEN_KEY = 'admin_token';

function getAdminToken(): string | null {
  return localStorage.getItem(ADMIN_TOKEN_KEY);
}

function setAdminToken(token: string): void {
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
}

function clearAdminToken(): void {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
}

function getAuthHeaders(): Record<string, string> {
  const token = getAdminToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

// Types
interface ThemeSuggestion {
  id: number;
  theme_id: string;
  theme_title_ar: string | null;
  theme_title_en: string | null;
  sura_no: number;
  ayah_start: number;
  ayah_end: number;
  verse_reference: string;
  match_type: string;
  confidence: number;
  reasons_ar: string;
  reasons_en: string | null;
  evidence_sources: Array<{ source_id: string; snippet?: string }>;
  evidence_count: number;
  status: string;
  status_label_ar: string;
  status_label_en: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  source: string;
  batch_id: string | null;
  created_at: string;
  // Approval workflow fields
  origin: string;
  origin_label_ar: string;
  origin_label_en: string;
  is_auto_discovery: boolean;
  meets_approval_requirements: boolean;
  approval_blockers: string[];
  has_proper_attribution: boolean;
}

interface AdminStats {
  total_suggestions: number;
  pending_suggestions: number;
  approved_suggestions: number;
  rejected_suggestions: number;
  total_segments: number;
  discovered_segments: number;
  manual_segments: number;
  by_theme: Array<{ theme_id: string; title_ar: string; pending: number; total: number }>;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function ThemeAdminPage() {
  const { language } = useLanguageStore();
  const [suggestions, setSuggestions] = useState<ThemeSuggestion[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!getAdminToken());
  const [authError, setAuthError] = useState<string | null>(null);
  const [tokenInput, setTokenInput] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      loadStats();
      loadSuggestions();
    }
  }, [statusFilter, isAuthenticated]);

  function handleLogin() {
    if (tokenInput.trim()) {
      setAdminToken(tokenInput.trim());
      setIsAuthenticated(true);
      setAuthError(null);
      setTokenInput('');
    }
  }

  function handleLogout() {
    clearAdminToken();
    setIsAuthenticated(false);
    setSuggestions([]);
    setStats(null);
  }

  async function loadStats() {
    try {
      const response = await fetch(`${API_BASE}/api/v1/themes/admin/stats`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
        setAuthError(null);
      } else if (response.status === 401) {
        setAuthError(language === 'ar' ? 'رمز غير صالح' : 'Invalid token');
        handleLogout();
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }

  async function loadSuggestions() {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: '50',
        ...(statusFilter !== 'all' ? { status: statusFilter } : {}),
      });
      const response = await fetch(`${API_BASE}/api/v1/themes/admin/suggestions?${params}`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
        setAuthError(null);
      } else if (response.status === 401) {
        setAuthError(language === 'ar' ? 'رمز غير صالح' : 'Invalid token');
        handleLogout();
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(id: number, force: boolean = false) {
    setActionLoading(id);
    try {
      const url = `${API_BASE}/api/v1/themes/admin/suggestions/${id}/approve${force ? '?force=true' : ''}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          reviewer: 'admin',
          is_core: true,
        }),
      });

      if (response.ok) {
        await loadSuggestions();
        await loadStats();
      } else if (response.status === 401) {
        setAuthError(language === 'ar' ? 'رمز غير صالح' : 'Invalid token');
        handleLogout();
      } else {
        const error = await response.json();
        // Handle structured error response
        if (error.detail && typeof error.detail === 'object') {
          const msg = language === 'ar' ? error.detail.error : error.detail.error_en;
          const blockers = error.detail.blockers?.join('\n- ') || '';
          alert(`${msg}\n\n- ${blockers}`);
        } else {
          alert(language === 'ar' ? 'فشل الموافقة' : `Approval failed: ${error.detail}`);
        }
      }
    } catch (error) {
      console.error('Failed to approve:', error);
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReject(id: number) {
    const reason = prompt(
      language === 'ar' ? 'سبب الرفض:' : 'Rejection reason:'
    );
    if (!reason) return;

    setActionLoading(id);
    try {
      const response = await fetch(`${API_BASE}/api/v1/themes/admin/suggestions/${id}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          reviewer: 'admin',
          reason,
        }),
      });

      if (response.ok) {
        await loadSuggestions();
        await loadStats();
      } else if (response.status === 401) {
        setAuthError(language === 'ar' ? 'رمز غير صالح' : 'Invalid token');
        handleLogout();
      } else {
        const error = await response.json();
        alert(language === 'ar' ? 'فشل الرفض' : `Rejection failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to reject:', error);
    } finally {
      setActionLoading(null);
    }
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  };

  const matchTypeColors: Record<string, string> = {
    lexical: 'bg-blue-100 text-blue-700',
    root: 'bg-purple-100 text-purple-700',
    semantic: 'bg-cyan-100 text-cyan-700',
    mixed: 'bg-indigo-100 text-indigo-700',
  };

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto px-4 py-16">
        <div className="card">
          <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            {language === 'ar' ? 'تسجيل دخول المشرف' : 'Admin Login'}
          </h1>
          {authError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {authError}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'ar' ? 'رمز المشرف' : 'Admin Token'}
              </label>
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                placeholder={language === 'ar' ? 'أدخل رمز المشرف' : 'Enter admin token'}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <button
              onClick={handleLogin}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <LogIn className="w-5 h-5" />
              {language === 'ar' ? 'دخول' : 'Login'}
            </button>
          </div>
          <p className="mt-4 text-xs text-gray-500 text-center">
            {language === 'ar'
              ? 'يتطلب رمز المشرف المحدد في متغير البيئة ADMIN_TOKEN'
              : 'Requires ADMIN_TOKEN environment variable'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header with Logout */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {language === 'ar' ? 'لوحة مراجعة المحاور' : 'Theme Review Panel'}
          </h1>
          <p className="text-gray-600">
            {language === 'ar'
              ? 'مراجعة الاقتراحات المكتشفة آلياً والموافقة عليها أو رفضها'
              : 'Review auto-discovered suggestions and approve or reject them'}
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          {language === 'ar' ? 'خروج' : 'Logout'}
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card bg-amber-50 border-amber-200">
            <div className="flex items-center gap-3">
              <Clock className="w-8 h-8 text-amber-600" />
              <div>
                <div className="text-2xl font-bold text-amber-700">{stats.pending_suggestions}</div>
                <div className="text-sm text-amber-600">
                  {language === 'ar' ? 'قيد المراجعة' : 'Pending'}
                </div>
              </div>
            </div>
          </div>
          <div className="card bg-green-50 border-green-200">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <div>
                <div className="text-2xl font-bold text-green-700">{stats.approved_suggestions}</div>
                <div className="text-sm text-green-600">
                  {language === 'ar' ? 'موافق عليها' : 'Approved'}
                </div>
              </div>
            </div>
          </div>
          <div className="card bg-red-50 border-red-200">
            <div className="flex items-center gap-3">
              <XCircle className="w-8 h-8 text-red-600" />
              <div>
                <div className="text-2xl font-bold text-red-700">{stats.rejected_suggestions}</div>
                <div className="text-sm text-red-600">
                  {language === 'ar' ? 'مرفوضة' : 'Rejected'}
                </div>
              </div>
            </div>
          </div>
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center gap-3">
              <BookOpen className="w-8 h-8 text-blue-600" />
              <div>
                <div className="text-2xl font-bold text-blue-700">{stats.total_segments}</div>
                <div className="text-sm text-blue-600">
                  {language === 'ar' ? 'إجمالي المقاطع' : 'Total Segments'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        {['all', 'pending', 'approved', 'rejected'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              statusFilter === status
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            {status === 'all'
              ? language === 'ar' ? 'الكل' : 'All'
              : status === 'pending'
              ? language === 'ar' ? 'قيد المراجعة' : 'Pending'
              : status === 'approved'
              ? language === 'ar' ? 'موافق عليها' : 'Approved'
              : language === 'ar' ? 'مرفوضة' : 'Rejected'}
          </button>
        ))}
      </div>

      {/* Suggestions List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">{language === 'ar' ? 'جاري التحميل...' : 'Loading...'}</p>
        </div>
      ) : suggestions.length === 0 ? (
        <div className="text-center py-12 card">
          <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {language === 'ar'
              ? 'لا توجد اقتراحات في هذه الفئة'
              : 'No suggestions in this category'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {suggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className={clsx(
                'card border-2 transition-all',
                suggestion.status === 'pending' && 'border-amber-200 hover:border-amber-300',
                suggestion.status === 'approved' && 'border-green-200',
                suggestion.status === 'rejected' && 'border-red-200'
              )}
            >
              {/* Header Row */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setExpandedId(expandedId === suggestion.id ? null : suggestion.id)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    {expandedId === suggestion.id ? (
                      <ChevronUp className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    )}
                  </button>
                  <div>
                    <div className="font-semibold text-lg">
                      {language === 'ar' ? suggestion.theme_title_ar : suggestion.theme_title_en}
                    </div>
                    <div className="text-sm text-gray-500">
                      {suggestion.verse_reference} • {suggestion.match_type}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {/* Auto-discovery badge */}
                  {suggestion.is_auto_discovery && suggestion.status === 'pending' && (
                    <span className="text-xs px-2 py-1 rounded bg-orange-100 text-orange-700 border border-orange-300">
                      {language === 'ar' ? 'اقتراح آلي - يحتاج مراجعة' : 'Auto-suggestion - Needs Review'}
                    </span>
                  )}
                  <span className={clsx('text-xs px-2 py-1 rounded', matchTypeColors[suggestion.match_type] || 'bg-gray-100')}>
                    {suggestion.match_type}
                  </span>
                  <span className={clsx('text-xs px-2 py-1 rounded', statusColors[suggestion.status])}>
                    {language === 'ar' ? suggestion.status_label_ar : suggestion.status_label_en}
                  </span>
                  <span className="text-sm font-medium text-gray-600">
                    {(suggestion.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Reasons Preview */}
              <div className="mt-3 text-sm text-gray-700 line-clamp-2">
                {suggestion.reasons_ar}
              </div>

              {/* Expanded Details */}
              {expandedId === suggestion.id && (
                <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                  {/* Full Reasons */}
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">
                      {language === 'ar' ? 'سبب الربط:' : 'Reasons:'}
                    </h4>
                    <p className="text-gray-600 whitespace-pre-wrap">{suggestion.reasons_ar}</p>
                  </div>

                  {/* Evidence Sources */}
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">
                      {language === 'ar' ? 'المصادر:' : 'Evidence Sources:'} ({suggestion.evidence_count})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {suggestion.evidence_sources.slice(0, 5).map((source, idx) => (
                        <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                          {source.source_id}
                        </span>
                      ))}
                      {suggestion.evidence_sources.length > 5 && (
                        <span className="text-xs text-gray-400">
                          +{suggestion.evidence_sources.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Rejection Reason (if rejected) */}
                  {suggestion.rejection_reason && (
                    <div className="bg-red-50 p-3 rounded">
                      <h4 className="font-medium text-red-700 mb-1">
                        {language === 'ar' ? 'سبب الرفض:' : 'Rejection Reason:'}
                      </h4>
                      <p className="text-red-600">{suggestion.rejection_reason}</p>
                    </div>
                  )}

                  {/* Approval Blockers Warning */}
                  {suggestion.status === 'pending' && suggestion.is_auto_discovery && !suggestion.meets_approval_requirements && (
                    <div className="bg-amber-50 border border-amber-200 p-3 rounded">
                      <h4 className="font-medium text-amber-700 mb-2 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        {language === 'ar' ? 'لم تستوفِ متطلبات الموافقة:' : 'Approval requirements not met:'}
                      </h4>
                      <ul className="text-sm text-amber-600 list-disc list-inside space-y-1">
                        {suggestion.approval_blockers.map((blocker, idx) => (
                          <li key={idx}>{blocker}</li>
                        ))}
                      </ul>
                      <p className="text-xs text-amber-500 mt-2">
                        {language === 'ar'
                          ? 'يمكن للمشرف الموافقة بالإجبار إذا لزم الأمر'
                          : 'Admin can force approve if necessary'}
                      </p>
                    </div>
                  )}

                  {/* Actions */}
                  {suggestion.status === 'pending' && (
                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={() => handleApprove(suggestion.id, !suggestion.meets_approval_requirements)}
                        disabled={actionLoading === suggestion.id}
                        className={clsx(
                          'flex items-center gap-2 px-4 py-2 rounded-lg disabled:opacity-50 transition-colors',
                          suggestion.meets_approval_requirements
                            ? 'bg-green-600 text-white hover:bg-green-700'
                            : 'bg-amber-600 text-white hover:bg-amber-700'
                        )}
                      >
                        <CheckCircle className="w-4 h-4" />
                        {actionLoading === suggestion.id
                          ? language === 'ar' ? 'جاري...' : 'Processing...'
                          : !suggestion.meets_approval_requirements
                          ? language === 'ar' ? 'موافقة (إجبار)' : 'Force Approve'
                          : language === 'ar' ? 'موافقة' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleReject(suggestion.id)}
                        disabled={actionLoading === suggestion.id}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                      >
                        <XCircle className="w-4 h-4" />
                        {language === 'ar' ? 'رفض' : 'Reject'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
