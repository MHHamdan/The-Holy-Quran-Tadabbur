import { useState, useEffect } from 'react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { api } from '../../lib/api';
import clsx from 'clsx';
import {
  Monitor,
  Server,
  Database,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Globe,
  Layers,
  Route,
  Package,
  HardDrive,
  Table,
  GitBranch,
  Activity,
  Wifi,
  WifiOff,
  RefreshCw,
} from 'lucide-react';

type StatusTab = 'frontend' | 'backend' | 'database';

// ============================================================================
// Status types
// ============================================================================

interface HealthStatus {
  status: string;
  database?: string;
  redis?: string;
  qdrant?: string;
  surrealdb?: string;
  uptime?: number;
  version?: string;
}

interface EndpointCheck {
  name: string;
  path: string;
  status: 'ok' | 'error' | 'checking';
  latencyMs?: number;
  error?: string;
}

// ============================================================================
// Main Component
// ============================================================================

export function StatusDashboardPage() {
  const { language } = useLanguageStore();
  const [activeTab, setActiveTab] = useState<StatusTab>('frontend');

  const tabs: Array<{ key: StatusTab; label: string; icon: typeof Monitor }> = [
    { key: 'frontend', label: language === 'ar' ? 'الواجهة الأمامية' : 'Frontend', icon: Monitor },
    { key: 'backend', label: language === 'ar' ? 'الخادم الخلفي' : 'Backend', icon: Server },
    { key: 'database', label: language === 'ar' ? 'قواعد البيانات' : 'Database', icon: Database },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-8">
        <h1 className={clsx('text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3', language === 'ar' && 'font-arabic')}>
          <Activity className="w-8 h-8 text-primary-600" />
          {language === 'ar' ? 'لوحة حالة المنصة' : 'Platform Status Dashboard'}
        </h1>
        <p className={clsx('text-gray-600', language === 'ar' && 'font-arabic')}>
          {language === 'ar'
            ? 'نظرة شاملة على حالة جميع مكونات منصة تدبر'
            : 'Comprehensive overview of all Tadabbur platform components'}
        </p>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-2 mb-8 border-b border-gray-200">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={clsx(
              'px-6 py-3 text-lg font-semibold transition-colors border-b-2 -mb-px flex items-center gap-2',
              activeTab === key
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700',
              language === 'ar' && 'font-arabic'
            )}
          >
            <Icon className="w-5 h-5" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'frontend' && <FrontendScreen language={language} />}
      {activeTab === 'backend' && <BackendScreen language={language} />}
      {activeTab === 'database' && <DatabaseScreen language={language} />}
    </div>
  );
}

// ============================================================================
// Status Badge
// ============================================================================

function StatusBadge({ status, language = 'en' }: { status: 'ok' | 'error' | 'checking' | 'warning'; language?: 'ar' | 'en' }) {
  const config = {
    ok: { icon: CheckCircle, color: 'text-green-600 bg-green-50', key: 'status_active' as const },
    error: { icon: XCircle, color: 'text-red-600 bg-red-50', key: 'status_error' as const },
    checking: { icon: Clock, color: 'text-yellow-600 bg-yellow-50', key: 'status_checking' as const },
    warning: { icon: AlertTriangle, color: 'text-amber-600 bg-amber-50', key: 'status_warning' as const },
  };
  const { icon: Icon, color, key } = config[status];
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium', color)}>
      <Icon className="w-3.5 h-3.5" />
      {t(key, language)}
    </span>
  );
}

// ============================================================================
// Section Card
// ============================================================================

function SectionCard({ title, icon: Icon, children, count }: {
  title: string;
  icon: typeof Monitor;
  children: React.ReactNode;
  count?: number;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        {count !== undefined && (
          <span className="bg-primary-100 text-primary-700 text-sm font-medium px-3 py-1 rounded-full">
            {count}
          </span>
        )}
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

// ============================================================================
// FRONTEND SCREEN
// ============================================================================

function FrontendScreen({ language }: { language: 'ar' | 'en' }) {
  const pages = [
    { name: 'Home', nameAr: 'الرئيسية', route: '/', status: 'ok' as const },
    { name: 'Mushaf', nameAr: 'المصحف', route: '/mushaf', status: 'ok' as const },
    { name: 'Quran Explorer', nameAr: 'مستكشف القرآن', route: '/quran/:suraNo', status: 'ok' as const },
    { name: 'Search', nameAr: 'البحث', route: '/search', status: 'ok' as const },
    { name: 'Ask (RAG)', nameAr: 'اسأل', route: '/ask', status: 'ok' as const },
    { name: 'Stories', nameAr: 'القصص', route: '/stories', status: 'ok' as const },
    { name: 'Story Detail', nameAr: 'تفاصيل القصة', route: '/stories/:storyId', status: 'ok' as const },
    { name: 'Concepts', nameAr: 'المفاهيم', route: '/concepts', status: 'ok' as const },
    { name: 'Concept Detail', nameAr: 'تفاصيل المفهوم', route: '/concepts/:conceptId', status: 'ok' as const },
    { name: 'Themes + Names of Allah', nameAr: 'المحاور + أسماء الله الحسنى', route: '/themes', status: 'ok' as const },
    { name: 'Theme Detail', nameAr: 'تفاصيل المحور', route: '/themes/:themeId', status: 'ok' as const },
    { name: 'Theme Admin', nameAr: 'إدارة المحاور', route: '/themes/admin', status: 'ok' as const },
    { name: 'Miracles', nameAr: 'الإعجاز', route: '/miracles', status: 'ok' as const },
    { name: 'Verse Similarity', nameAr: 'صلة الآيات', route: '/similarity', status: 'ok' as const },
    { name: 'Sources', nameAr: 'المصادر', route: '/sources', status: 'ok' as const },
    { name: 'Tasmee (Memorization)', nameAr: 'التسميع', route: '/tasmee', status: 'ok' as const },
    { name: 'Tools Hub', nameAr: 'الأدوات', route: '/tools', status: 'ok' as const },
    { name: 'Prayer Times', nameAr: 'مواقيت الصلاة', route: '/tools/prayer-times', status: 'ok' as const },
    { name: 'Hijri Calendar', nameAr: 'التقويم الهجري', route: '/tools/calendar', status: 'ok' as const },
    { name: 'Zakat Calculator', nameAr: 'حاسبة الزكاة', route: '/tools/finance', status: 'ok' as const },
  ];

  const features = [
    { name: 'Code Splitting', nameAr: 'تقسيم الشيفرة', status: 'ok' as const, detail: 'React.lazy + Suspense' },
    { name: 'RTL Support', nameAr: 'دعم RTL', status: 'ok' as const, detail: 'Arabic / English' },
    { name: 'Bilingual i18n', nameAr: 'ثنائي اللغة', status: 'ok' as const, detail: '300+ translation keys' },
    { name: 'Responsive Design', nameAr: 'تصميم متجاوب', status: 'ok' as const, detail: 'Mobile + Desktop' },
    { name: 'State Management', nameAr: 'إدارة الحالة', status: 'ok' as const, detail: 'Zustand' },
    { name: 'API Client', nameAr: 'عميل API', status: 'ok' as const, detail: 'Axios + TypeScript' },
    { name: 'Route Preloading', nameAr: 'تحميل مسبق', status: 'ok' as const, detail: 'Predictive navigation' },
    { name: 'WebSocket Support', nameAr: 'دعم WebSocket', status: 'ok' as const, detail: 'Tasmee real-time' },
  ];

  const techStack = [
    { name: 'React', version: '18.x', category: 'UI Framework' },
    { name: 'TypeScript', version: '5.x', category: 'Language' },
    { name: 'Vite', version: '5.x', category: 'Build Tool' },
    { name: 'React Router', version: '6.x', category: 'Routing' },
    { name: 'Zustand', version: 'latest', category: 'State' },
    { name: 'Axios', version: 'latest', category: 'HTTP' },
    { name: 'Tailwind CSS', version: '3.x', category: 'Styling' },
    { name: 'Lucide React', version: 'latest', category: 'Icons' },
    { name: 'Cytoscape.js', version: 'latest', category: 'Graph Viz' },
  ];

  return (
    <div className="space-y-8">
      {/* Network Access Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-3">
          <Globe className="w-6 h-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-blue-900">
            {language === 'ar' ? 'الوصول عبر الشبكة' : 'Network Access'}
          </h3>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4 border border-blue-100">
            <p className="text-sm text-gray-500 mb-1">Local URL</p>
            <code className="text-blue-700 font-mono text-sm">http://localhost:3000</code>
          </div>
          <div className="bg-white rounded-lg p-4 border border-blue-100">
            <p className="text-sm text-gray-500 mb-1">LAN URL</p>
            <code className="text-blue-700 font-mono text-sm">{`http://${window.location.hostname}:3000`}</code>
          </div>
          <div className="bg-white rounded-lg p-4 border border-blue-100">
            <p className="text-sm text-gray-500 mb-1">Vite Host</p>
            <code className="text-blue-700 font-mono text-sm">0.0.0.0 (all interfaces)</code>
          </div>
          <div className="bg-white rounded-lg p-4 border border-blue-100">
            <p className="text-sm text-gray-500 mb-1">API Proxy</p>
            <code className="text-blue-700 font-mono text-sm">/api/* → localhost:8002</code>
          </div>
        </div>
      </div>

      {/* Pages */}
      <SectionCard
        title={language === 'ar' ? 'الصفحات والمسارات' : 'Pages & Routes'}
        icon={Route}
        count={pages.length}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-start py-2 px-3 font-semibold text-gray-600">
                  {language === 'ar' ? 'الصفحة' : 'Page'}
                </th>
                <th className="text-start py-2 px-3 font-semibold text-gray-600">
                  {language === 'ar' ? 'المسار' : 'Route'}
                </th>
                <th className="text-start py-2 px-3 font-semibold text-gray-600">
                  {language === 'ar' ? 'الحالة' : 'Status'}
                </th>
              </tr>
            </thead>
            <tbody>
              {pages.map((page, idx) => (
                <tr key={idx} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2.5 px-3 font-medium text-gray-900">
                    {language === 'ar' ? page.nameAr : page.name}
                  </td>
                  <td className="py-2.5 px-3">
                    <code className="text-primary-600 bg-primary-50 px-2 py-0.5 rounded text-xs">
                      {page.route}
                    </code>
                  </td>
                  <td className="py-2.5 px-3">
                    <StatusBadge status={page.status} language={language} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* Features */}
      <SectionCard
        title={language === 'ar' ? 'الميزات' : 'Features'}
        icon={Package}
        count={features.length}
      >
        <div className="grid md:grid-cols-2 gap-3">
          {features.map((feat, idx) => (
            <div key={idx} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
              <div>
                <p className="font-medium text-gray-900 text-sm">
                  {language === 'ar' ? feat.nameAr : feat.name}
                </p>
                <p className="text-xs text-gray-500">{feat.detail}</p>
              </div>
              <StatusBadge status={feat.status} language={language} />
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Tech Stack */}
      <SectionCard
        title={language === 'ar' ? 'التقنيات المستخدمة' : 'Tech Stack'}
        icon={Layers}
        count={techStack.length}
      >
        <div className="grid md:grid-cols-3 gap-3">
          {techStack.map((tech, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <p className="font-medium text-gray-900 text-sm">{tech.name}</p>
                <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                  {tech.version}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">{tech.category}</p>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

// ============================================================================
// BACKEND SCREEN
// ============================================================================

function BackendScreen({ language }: { language: 'ar' | 'en' }) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [endpoints, setEndpoints] = useState<EndpointCheck[]>([]);
  const [checking, setChecking] = useState(false);

  const apiRoutes = [
    { group: 'Quran', groupAr: 'القرآن', prefix: '/api/v1/quran', endpoints: [
      'GET /suras/:suraNo', 'GET /verses/:sura/:aya', 'GET /page/:pageNo',
      'GET /tafseer/:sura/:aya', 'GET /search/enhanced/:word',
      'GET /search/intelligent', 'GET /search/semantic', 'GET /search/multi-concept',
      'GET /allah-names', 'GET /audio/verse/:sura/:aya', 'GET /audio/page/:pageNo',
      'GET /similarity/advanced/:sura/:aya', 'GET /highlights/concept/:id',
    ]},
    { group: 'Themes', groupAr: 'المحاور', prefix: '/api/v1/themes', endpoints: [
      'GET /', 'GET /categories', 'GET /:themeId', 'GET /:themeId/segments',
      'GET /:themeId/coverage', 'GET /:themeId/graph', 'GET /:themeId/consequences',
    ]},
    { group: 'Stories', groupAr: 'القصص', prefix: '/api/v1/stories', endpoints: [
      'GET /', 'GET /:storyId', 'GET /:storyId/graph', 'GET /categories',
    ]},
    { group: 'Story Atlas', groupAr: 'الأطلس', prefix: '/api/v1/story-atlas', endpoints: [
      'GET /', 'GET /:clusterId', 'GET /:clusterId/graph', 'GET /:clusterId/timeline',
      'GET /facets', 'GET /categories',
    ]},
    { group: 'Concepts', groupAr: 'المفاهيم', prefix: '/api/v1/concepts', endpoints: [
      'GET /', 'GET /types', 'GET /search', 'GET /:conceptId',
      'GET /:conceptId/occurrences', 'GET /:conceptId/associations', 'GET /miracles/all',
    ]},
    { group: 'RAG (Ask)', groupAr: 'اسأل (RAG)', prefix: '/api/v1/rag', endpoints: [
      'POST /ask', 'POST /ask/followup', 'POST /ask/expand',
      'GET /sources', 'GET /sample-questions', 'GET /suggestions',
    ]},
    { group: 'Grammar', groupAr: 'الإعراب', prefix: '/api/v1/grammar', endpoints: [
      'POST /analyze', 'GET /ayah/:suraAyah', 'GET /labels', 'GET /health',
    ]},
    { group: 'Knowledge Graph', groupAr: 'الرسم المعرفي', prefix: '/api/v1/kg', endpoints: [
      'GET /story/:clusterId', 'GET /story/:clusterId/graph',
      'GET /search', 'GET /health',
    ]},
    { group: 'Graph Explorer', groupAr: 'مستكشف الرسم', prefix: '/api/v1/graph', endpoints: [
      'GET /search/semantic', 'GET /stats', 'GET /overview',
      'GET /entity/:id', 'GET /explore/bfs', 'GET /explore/dfs',
    ]},
    { group: 'Rhetoric', groupAr: 'البلاغة', prefix: '/api/v1/rhetoric', endpoints: [
      'GET /analyze/:sura/:aya', 'GET /figures', 'GET /health',
    ]},
    { group: 'Tasmee', groupAr: 'التسميع', prefix: '/api/v1/tasmee', endpoints: [
      'POST /session/start', 'POST /session/:id/evaluate', 'WS /ws/:sessionId',
    ]},
    { group: 'Admin', groupAr: 'الإدارة', prefix: '/api/v1/admin', endpoints: [
      'GET /health', 'GET /stats',
    ]},
  ];

  const services = [
    { name: 'FastAPI Server', nameAr: 'خادم FastAPI', port: 8002, status: health ? 'ok' as const : 'checking' as const },
    { name: 'Ollama LLM', nameAr: 'Ollama LLM', port: 11434, detail: 'qwen2.5:32b / 14b' },
    { name: 'Embedding Model', nameAr: 'نموذج التضمين', port: null, detail: 'intfloat/multilingual-e5-large' },
    { name: 'Faster-Whisper STT', nameAr: 'تحويل صوت لنص', port: null, detail: 'Arabic speech recognition' },
  ];

  useEffect(() => {
    checkHealth();
  }, []);

  async function checkHealth() {
    setChecking(true);
    try {
      const response = await api.get('/health');
      setHealth(response.data);
    } catch {
      setHealth({ status: 'error' });
    }

    // Check key endpoints
    const checks: EndpointCheck[] = [];
    const endpointsToCheck = [
      { name: 'Health', path: '/health' },
      { name: 'Quran Verses', path: '/quran/suras/1' },
      { name: 'Allah Names', path: '/quran/allah-names?lang=ar&max_verses_per_name=1' },
      { name: 'Themes', path: '/themes?parent_only=true' },
      { name: 'Stories', path: '/stories/' },
      { name: 'Concepts', path: '/concepts?limit=1' },
    ];

    for (const ep of endpointsToCheck) {
      const start = performance.now();
      try {
        await api.get(ep.path);
        checks.push({ name: ep.name, path: ep.path, status: 'ok', latencyMs: Math.round(performance.now() - start) });
      } catch (err: unknown) {
        checks.push({ name: ep.name, path: ep.path, status: 'error', error: err instanceof Error ? err.message : 'Unknown error' });
      }
    }
    setEndpoints(checks);
    setChecking(false);
  }

  const totalEndpoints = apiRoutes.reduce((acc, g) => acc + g.endpoints.length, 0);

  return (
    <div className="space-y-8">
      {/* Health Overview */}
      <div className={clsx(
        'rounded-xl p-6 border',
        health?.status === 'healthy' || health?.status === 'ok'
          ? 'bg-green-50 border-green-200'
          : health?.status === 'error'
            ? 'bg-red-50 border-red-200'
            : 'bg-yellow-50 border-yellow-200'
      )}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {health?.status === 'healthy' || health?.status === 'ok' ? (
              <Wifi className="w-6 h-6 text-green-600" />
            ) : health?.status === 'error' ? (
              <WifiOff className="w-6 h-6 text-red-600" />
            ) : (
              <Clock className="w-6 h-6 text-yellow-600" />
            )}
            <h3 className="text-lg font-semibold">
              {language === 'ar' ? 'حالة الخادم' : 'Server Health'}
            </h3>
          </div>
          <button
            onClick={checkHealth}
            disabled={checking}
            className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-300 text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={clsx('w-4 h-4', checking && 'animate-spin')} />
            {language === 'ar' ? 'تحديث' : 'Refresh'}
          </button>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 border">
            <p className="text-sm text-gray-500 mb-1">Status</p>
            <p className="font-semibold text-lg">
              {health?.status === 'healthy' || health?.status === 'ok' ? 'Healthy' : health?.status || 'Checking...'}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4 border">
            <p className="text-sm text-gray-500 mb-1">Backend Port</p>
            <p className="font-semibold text-lg font-mono">8002</p>
          </div>
          <div className="bg-white rounded-lg p-4 border">
            <p className="text-sm text-gray-500 mb-1">Framework</p>
            <p className="font-semibold text-lg">FastAPI (Python)</p>
          </div>
        </div>
      </div>

      {/* Live Endpoint Checks */}
      {endpoints.length > 0 && (
        <SectionCard
          title={language === 'ar' ? 'فحص نقاط النهاية المباشر' : 'Live Endpoint Checks'}
          icon={Activity}
          count={endpoints.length}
        >
          <div className="space-y-2">
            {endpoints.map((ep, idx) => (
              <div key={idx} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                <div className="flex items-center gap-3">
                  <StatusBadge status={ep.status} language={language} />
                  <div>
                    <p className="font-medium text-sm text-gray-900">{ep.name}</p>
                    <code className="text-xs text-gray-500">{ep.path}</code>
                  </div>
                </div>
                {ep.latencyMs !== undefined && (
                  <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded font-mono">
                    {ep.latencyMs}ms
                  </span>
                )}
                {ep.error && (
                  <span className="text-xs text-red-600">{ep.error}</span>
                )}
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* API Routes */}
      <SectionCard
        title={language === 'ar' ? 'مسارات API' : 'API Routes'}
        icon={Route}
        count={totalEndpoints}
      >
        <div className="space-y-6">
          {apiRoutes.map((group, gIdx) => (
            <div key={gIdx}>
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-semibold text-gray-900">
                  {language === 'ar' ? group.groupAr : group.group}
                </h4>
                <code className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                  {group.prefix}
                </code>
                <span className="text-xs text-gray-400">({group.endpoints.length})</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {group.endpoints.map((ep, eIdx) => {
                  const method = ep.split(' ')[0];
                  const path = ep.split(' ').slice(1).join(' ');
                  const methodColor = {
                    GET: 'bg-green-100 text-green-700',
                    POST: 'bg-blue-100 text-blue-700',
                    PUT: 'bg-amber-100 text-amber-700',
                    DELETE: 'bg-red-100 text-red-700',
                    WS: 'bg-purple-100 text-purple-700',
                  }[method] || 'bg-gray-100 text-gray-700';

                  return (
                    <div key={eIdx} className="flex items-center gap-1 bg-gray-50 rounded px-2 py-1">
                      <span className={clsx('text-xs font-bold px-1.5 py-0.5 rounded', methodColor)}>
                        {method}
                      </span>
                      <code className="text-xs text-gray-700">{path}</code>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Backend Services */}
      <SectionCard
        title={language === 'ar' ? 'الخدمات' : 'Services'}
        icon={Server}
        count={services.length}
      >
        <div className="grid md:grid-cols-2 gap-3">
          {services.map((svc, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="font-medium text-gray-900">
                  {language === 'ar' ? svc.nameAr : svc.name}
                </p>
                {svc.port && (
                  <code className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                    :{svc.port}
                  </code>
                )}
              </div>
              {svc.detail && <p className="text-xs text-gray-500">{svc.detail}</p>}
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Backend Config */}
      <SectionCard
        title={language === 'ar' ? 'إعدادات CORS' : 'CORS Configuration'}
        icon={Globe}
      >
        <div className="space-y-2">
          {[
            'http://localhost:3000',
            'http://localhost:5173',
            'http://localhost:5174',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:5174',
          ].map((origin, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <code className="text-sm text-gray-700">{origin}</code>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

// ============================================================================
// DATABASE SCREEN
// ============================================================================

function DatabaseScreen({ language }: { language: 'ar' | 'en' }) {
  const models = [
    { name: 'QuranVerse', nameAr: 'آيات القرآن', table: 'quran_verses', rows: '6,236', category: 'Core' },
    { name: 'Translation', nameAr: 'الترجمات', table: 'translations', rows: '~18,000+', category: 'Core' },
    { name: 'TafseerSource', nameAr: 'مصادر التفسير', table: 'tafseer_sources', rows: '10+', category: 'Tafseer' },
    { name: 'TafseerChunk', nameAr: 'أجزاء التفسير', table: 'tafseer_chunks', rows: '~100,000+', category: 'Tafseer' },
    { name: 'Story', nameAr: 'القصص', table: 'stories', rows: '30+', category: 'Content' },
    { name: 'StorySegment', nameAr: 'أجزاء القصة', table: 'story_segments', rows: '200+', category: 'Content' },
    { name: 'Concept', nameAr: 'المفاهيم', table: 'concepts', rows: '500+', category: 'Knowledge' },
    { name: 'ConceptOccurrence', nameAr: 'ظهورات المفهوم', table: 'concept_occurrences', rows: '5,000+', category: 'Knowledge' },
    { name: 'ConceptAssociation', nameAr: 'روابط المفاهيم', table: 'concept_associations', rows: '1,000+', category: 'Knowledge' },
    { name: 'QuranTheme', nameAr: 'المحاور القرآنية', table: 'quran_themes', rows: '50+', category: 'Themes' },
    { name: 'ThemeSegment', nameAr: 'أجزاء المحور', table: 'theme_segments', rows: '500+', category: 'Themes' },
    { name: 'ThemeConnection', nameAr: 'روابط المحاور', table: 'theme_connections', rows: '200+', category: 'Themes' },
    { name: 'ThemeConsequence', nameAr: 'ثمرات المحور', table: 'theme_consequences', rows: '100+', category: 'Themes' },
    { name: 'ThemeSuggestion', nameAr: 'اقتراحات المحاور', table: 'theme_suggestions', rows: 'varies', category: 'Themes' },
    { name: 'TasmeeSession', nameAr: 'جلسات التسميع', table: 'tasmee_sessions', rows: 'varies', category: 'Tasmee' },
    { name: 'TasmeeMistake', nameAr: 'أخطاء التسميع', table: 'tasmee_mistakes', rows: 'varies', category: 'Tasmee' },
    { name: 'TasmeeProgress', nameAr: 'تقدم التسميع', table: 'tasmee_progress', rows: 'varies', category: 'Tasmee' },
    { name: 'TasmeeEvent', nameAr: 'أحداث التسميع', table: 'tasmee_events', rows: 'varies', category: 'Tasmee' },
  ];

  const migrations = [
    { id: '001', name: 'Initial Schema', date: 'Jan 2025', tables: 'verses, translations, tafseer' },
    { id: '8c16', name: 'Story Atlas Tables', date: 'Jan 2025', tables: 'story_clusters, story_events' },
    { id: '4fdb', name: 'Tafseer Source Toggle', date: 'Jan 2025', tables: 'tafseer_sources.is_enabled' },
    { id: 'ce5e', name: 'Story Graph Enhanced', date: 'Jan 2025', tables: 'story graph fields' },
    { id: 'f796', name: 'Provenance & Audit', date: 'Jan 2025', tables: 'audit_log, provenance' },
    { id: 'a1b2', name: 'Concept Graph Tables', date: 'Jan 2025', tables: 'concepts, associations' },
    { id: 'b7c8', name: 'Verification Workflow', date: 'Jan 2025', tables: 'verification tables' },
    { id: 'c2d3', name: 'Verification Queue', date: 'Jan 2025', tables: 'verification_queue' },
    { id: 'd3e4', name: 'Rhetorical Discourse', date: 'Jan 2025', tables: 'rhetoric tables' },
    { id: 'e4f5', name: 'Quranic Themes', date: 'Jan 2025', tables: 'themes, segments, connections' },
    { id: 'f5g6', name: 'Theme Discovery Fields', date: 'Jan 2025', tables: 'segment discovery columns' },
    { id: 'g6h7', name: 'Theme Compound Indexes', date: 'Jan 2025', tables: 'performance indexes' },
    { id: 'h7i8', name: 'Theme Suggestions', date: 'Jan 2025', tables: 'theme_suggestions' },
    { id: 'i8j9', name: 'Tasmee Tables', date: 'Jan 2025', tables: 'sessions, mistakes, events' },
    { id: 'j9k0', name: 'Trigram Search Index', date: 'Jan 2025', tables: 'pg_trgm index' },
  ];

  const databases = [
    {
      name: 'PostgreSQL',
      nameAr: 'قاعدة البيانات الرئيسية',
      type: 'Relational (SQL)',
      purpose: 'Core data: verses, translations, tafseer, stories, themes, concepts',
      purposeAr: 'البيانات الأساسية: الآيات، الترجمات، التفسير، القصص، المحاور',
      connection: 'postgresql://localhost:5432/tadabbur',
      status: 'ok' as const,
    },
    {
      name: 'Qdrant',
      nameAr: 'بحث المتجهات',
      type: 'Vector Database',
      purpose: 'Semantic search: verse embeddings, tafseer chunk embeddings',
      purposeAr: 'البحث الدلالي: تضمينات الآيات والتفسير',
      connection: 'localhost:6333',
      status: 'ok' as const,
    },
    {
      name: 'Redis',
      nameAr: 'ذاكرة التخزين المؤقت',
      type: 'Cache (Key-Value)',
      purpose: 'Caching: API responses, search results, sessions',
      purposeAr: 'التخزين المؤقت: استجابات API، نتائج البحث، الجلسات',
      connection: 'redis://localhost:6379/0',
      status: 'ok' as const,
    },
    {
      name: 'SurrealDB',
      nameAr: 'الرسم المعرفي',
      type: 'Graph Database',
      purpose: 'Knowledge graph: story connections, concept relationships',
      purposeAr: 'الرسم المعرفي: روابط القصص وعلاقات المفاهيم',
      connection: 'localhost:8529',
      status: 'ok' as const,
    },
  ];

  const dataFiles = [
    { name: 'Allah Names (99)', nameAr: 'أسماء الله الحسنى (99)', file: 'allah_names.py', records: '99', category: 'Static Data' },
    { name: 'Quran Verses', nameAr: 'آيات القرآن', file: 'PostgreSQL', records: '6,236', category: 'Core' },
    { name: 'Tafseer Chunks', nameAr: 'أجزاء التفسير', file: 'PostgreSQL + Qdrant', records: '100,000+', category: 'Knowledge' },
    { name: 'Verse Embeddings', nameAr: 'تضمينات الآيات', file: 'Qdrant', records: '6,236', category: 'Vector' },
  ];

  const categoryColors: Record<string, string> = {
    Core: 'bg-blue-100 text-blue-700',
    Tafseer: 'bg-purple-100 text-purple-700',
    Content: 'bg-green-100 text-green-700',
    Knowledge: 'bg-amber-100 text-amber-700',
    Themes: 'bg-emerald-100 text-emerald-700',
    Tasmee: 'bg-indigo-100 text-indigo-700',
  };

  return (
    <div className="space-y-8">
      {/* Database Systems */}
      <SectionCard
        title={language === 'ar' ? 'أنظمة قواعد البيانات' : 'Database Systems'}
        icon={HardDrive}
        count={databases.length}
      >
        <div className="grid md:grid-cols-2 gap-4">
          {databases.map((db, idx) => (
            <div key={idx} className="bg-gray-50 rounded-xl p-5 border border-gray-100">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-900 text-lg">{db.name}</h4>
                <StatusBadge status={db.status} language={language} />
              </div>
              <span className="inline-block text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded mb-3">
                {db.type}
              </span>
              <p className="text-sm text-gray-600 mb-3">
                {language === 'ar' ? db.purposeAr : db.purpose}
              </p>
              <code className="text-xs text-gray-500 block bg-white rounded p-2 border border-gray-100">
                {db.connection}
              </code>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Models / Tables */}
      <SectionCard
        title={language === 'ar' ? 'الجداول والنماذج' : 'Models & Tables'}
        icon={Table}
        count={models.length}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-start py-2 px-3 font-semibold text-gray-600">
                  {language === 'ar' ? 'النموذج' : 'Model'}
                </th>
                <th className="text-start py-2 px-3 font-semibold text-gray-600">
                  {language === 'ar' ? 'الجدول' : 'Table'}
                </th>
                <th className="text-start py-2 px-3 font-semibold text-gray-600">
                  {language === 'ar' ? 'السجلات' : 'Records'}
                </th>
                <th className="text-start py-2 px-3 font-semibold text-gray-600">
                  {language === 'ar' ? 'الفئة' : 'Category'}
                </th>
              </tr>
            </thead>
            <tbody>
              {models.map((model, idx) => (
                <tr key={idx} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2.5 px-3 font-medium text-gray-900">
                    {language === 'ar' ? model.nameAr : model.name}
                  </td>
                  <td className="py-2.5 px-3">
                    <code className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                      {model.table}
                    </code>
                  </td>
                  <td className="py-2.5 px-3 text-gray-600 font-mono text-xs">
                    {model.rows}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={clsx(
                      'text-xs font-medium px-2 py-0.5 rounded',
                      categoryColors[model.category] || 'bg-gray-100 text-gray-700'
                    )}>
                      {model.category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* Data Sources */}
      <SectionCard
        title={language === 'ar' ? 'مصادر البيانات' : 'Data Sources'}
        icon={Database}
        count={dataFiles.length}
      >
        <div className="grid md:grid-cols-2 gap-3">
          {dataFiles.map((df, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="font-medium text-gray-900 text-sm">
                  {language === 'ar' ? df.nameAr : df.name}
                </p>
                <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded font-mono">
                  {df.records}
                </span>
              </div>
              <p className="text-xs text-gray-500">{df.file} | {df.category}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Migrations */}
      <SectionCard
        title={language === 'ar' ? 'ترحيلات قاعدة البيانات' : 'Database Migrations (Alembic)'}
        icon={GitBranch}
        count={migrations.length}
      >
        <div className="space-y-2">
          {migrations.map((mig, idx) => (
            <div key={idx} className="flex items-center gap-4 bg-gray-50 rounded-lg p-3">
              <span className="text-xs font-mono bg-gray-200 text-gray-600 px-2 py-0.5 rounded w-12 text-center">
                {mig.id}
              </span>
              <div className="flex-1">
                <p className="font-medium text-sm text-gray-900">{mig.name}</p>
                <p className="text-xs text-gray-500">{mig.tables}</p>
              </div>
              <span className="text-xs text-gray-400">{mig.date}</span>
              <CheckCircle className="w-4 h-4 text-green-500" />
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
