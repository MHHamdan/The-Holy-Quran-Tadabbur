/**
 * Tadabbur App - Route Configuration with Code Splitting
 *
 * Performance optimizations:
 * 1. React.lazy for route-based code splitting
 * 2. Suspense with loading fallbacks
 * 3. Preloading for predictive navigation
 */

import { Routes, Route, Navigate, useParams, useLocation, useNavigate } from 'react-router-dom';
import { Suspense, lazy, useEffect, useRef, memo } from 'react';
import { Layout } from './components/layout/Layout';
import { AppUpdateBanner, NativeConnectivityBanner } from './components/pwa/AppUpdateBanner';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { initNativeShell, isNativeApp } from './lib/native';
import { OnboardingModal } from './components/onboarding/OnboardingModal';
import { usePersonaStore } from './stores/personaStore';
import { Loader2 } from 'lucide-react';
import { useLanguageStore } from './stores/languageStore';
import { t } from './i18n/translations';
import { continueReadingPath } from './hooks/useReadingProgress';

// =============================================================================
// Loading Component - Optimized for perceived performance
// =============================================================================

const PageLoader = memo(function PageLoader() {
  const { language } = useLanguageStore();
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center">
      <Loader2 className="w-10 h-10 text-emerald-600 animate-spin mb-4" />
      <p className={`text-gray-600 ${language === 'ar' ? 'font-arabic' : ''}`}>
        {t('loading', language)}
      </p>
    </div>
  );
});

// =============================================================================
// Lazy-loaded Pages - Code splitting for optimal bundle sizes
// =============================================================================

// Core pages (frequently accessed)
const HomePage = lazy(() => import('./pages/HomePage').then(m => ({ default: m.HomePage })));

// Quran & Mushaf (heavy pages - separate chunks)
const QuranPage = lazy(() => import('./pages/QuranPage').then(m => ({ default: m.QuranPage })));
const MushafPage = lazy(() => import('./pages/MushafPage').then(m => ({ default: m.MushafPage })));

// Search & Ask (AI-powered features)
const AskPage = lazy(() => import('./pages/AskPage').then(m => ({ default: m.AskPage })));
const SearchPage = lazy(() => import('./pages/SearchPage').then(m => ({ default: m.SearchPage })));

// Stories — canonical list + detail (StoryAtlasPage is the single authoritative browse experience)
const StoryAtlasPage = lazy(() => import('./pages/StoryAtlasPage').then(m => ({ default: m.StoryAtlasPage })));
const StoryDetailPage = lazy(() => import('./pages/StoryDetailPage').then(m => ({ default: m.StoryDetailPage })));
const StoryAtlasDetailPage = lazy(() => import('./pages/StoryAtlasDetailPage').then(m => ({ default: m.StoryAtlasDetailPage })));

// Concepts feature
const ConceptsPage = lazy(() => import('./pages/ConceptsPage').then(m => ({ default: m.ConceptsPage })));
const ConceptDetailPage = lazy(() => import('./pages/ConceptDetailPage').then(m => ({ default: m.ConceptDetailPage })));

// Themes feature
const ThemesPage = lazy(() => import('./pages/ThemesPage').then(m => ({ default: m.ThemesPage })));
const ThemeDetailPage = lazy(() => import('./pages/ThemeDetailPage').then(m => ({ default: m.ThemeDetailPage })));

// Other pages
const MiraclesPage = lazy(() => import('./pages/MiraclesPage').then(m => ({ default: m.MiraclesPage })));
const SimilarityPage = lazy(() => import('./pages/SimilarityPage').then(m => ({ default: m.SimilarityPage })));
const SourcesPage = lazy(() => import('./pages/SourcesPage').then(m => ({ default: m.SourcesPage })));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage').then(m => ({ default: m.PrivacyPage })));
const TafsirComparePage = lazy(() => import('./pages/TafsirComparePage').then(m => ({ default: m.TafsirComparePage })));

// Tasmeeʿ (Memorization) - Audio recording with STT
const TasmeePage = lazy(() => import('./pages/TasmeePage'));

// Surah Atlas Intelligence
const SurahAtlasPage = lazy(() => import('./pages/SurahAtlasPage'));
const SurahAtlasDetailPage = lazy(() => import('./pages/SurahAtlasDetailPage'));

// Memorization Intelligence
const MemorizationLinksPage = lazy(() => import('./pages/MemorizationLinksPage'));

// Tools pages (bundled together)
const ToolsPage = lazy(() => import('./pages/ToolsPage').then(m => ({ default: m.ToolsPage })));
const ZakatCalculatorPage = lazy(() => import('./pages/tools/ZakatCalculatorPage').then(m => ({ default: m.ZakatCalculatorPage })));
const MosqueFinderPage = lazy(() => import('./pages/tools/MosqueFinderPage').then(m => ({ default: m.MosqueFinderPage })));
const IslamicVideosPage = lazy(() => import('./pages/tools/IslamicVideosPage').then(m => ({ default: m.IslamicVideosPage })));
const IslamicBooksPage = lazy(() => import('./pages/tools/IslamicBooksPage').then(m => ({ default: m.IslamicBooksPage })));
const HajjUmrahGuidePage = lazy(() => import('./pages/tools/HajjUmrahGuidePage').then(m => ({ default: m.HajjUmrahGuidePage })));
const IslamicWebSearchPage = lazy(() => import('./pages/tools/IslamicWebSearchPage').then(m => ({ default: m.IslamicWebSearchPage })));
const PrayerTimesPage = lazy(() => import('./pages/tools/PrayerTimesPage').then(m => ({ default: m.PrayerTimesPage })));
const HijriCalendarPage = lazy(() => import('./pages/tools/HijriCalendarPage').then(m => ({ default: m.HijriCalendarPage })));
const VocabularyPage = lazy(() => import('./pages/tools/VocabularyPage').then(m => ({ default: m.VocabularyPage })));
const PromptGuidePage = lazy(() => import('./pages/tools/PromptGuidePage').then(m => ({ default: m.PromptGuidePage })));
const SurahMemoryAtlasPage = lazy(() => import('./pages/tools/SurahMemoryAtlasPage').then(m => ({ default: m.SurahMemoryAtlasPage })));

// Bookmarks
const BookmarksPage = lazy(() => import('./pages/BookmarksPage').then(m => ({ default: m.BookmarksPage })));

// Daily Challenge
const DailyChallengePage = lazy(() => import('./pages/DailyChallengePage').then(m => ({ default: m.DailyChallengePage })));

// Reading Plan (Khatmah planner)
const ReadingPlanPage = lazy(() => import('./pages/ReadingPlanPage').then(m => ({ default: m.ReadingPlanPage })));

// Quranic Duʿā Explorer
const DuasPage = lazy(() => import('./pages/DuasPage').then(m => ({ default: m.DuasPage })));

// Quranic Calls Atlas
const QuranicCallsAtlasPage = lazy(() => import('./pages/QuranicCallsAtlasPage'));

// Juz Navigator
const SurahIndexPage = lazy(() => import('./pages/SurahIndexPage').then(m => ({ default: m.SurahIndexPage })));

// Learning Paths
const LearnPage = lazy(() => import('./pages/LearnPage').then(m => ({ default: m.LearnPage })));

// Asma Allah (99 Names of Allah)
const AsmaAllahPage = lazy(() => import('./pages/AsmaAllahPage').then(m => ({ default: m.AsmaAllahPage })));
const AsmaAllahDetailPage = lazy(() => import('./pages/AsmaAllahDetailPage').then(m => ({ default: m.AsmaAllahDetailPage })));

// Admin and developer pages (/status, /admin/*, /themes/admin) are only
// registered in development or when VITE_ENABLE_ADMIN=true is set at build
// time. In other builds the condition is a constant false, so the bundler
// drops these imports and the pages are not shipped to users at all.
const ADMIN_ENABLED = import.meta.env.DEV || import.meta.env.VITE_ENABLE_ADMIN === 'true';
const StatusDashboardPage = ADMIN_ENABLED
  ? lazy(() => import('./pages/admin/StatusDashboardPage').then(m => ({ default: m.StatusDashboardPage })))
  : null;
const ReviewDashboardPage = ADMIN_ENABLED
  ? lazy(() => import('./pages/admin/ReviewDashboardPage').then(m => ({ default: m.ReviewDashboardPage })))
  : null;
const AdminFeedbackPage = ADMIN_ENABLED
  ? lazy(() => import('./pages/admin/AdminFeedbackPage').then(m => ({ default: m.AdminFeedbackPage })))
  : null;
// Story connection explorer: a developer view of the raw entity graph
// (auto-detected links, raw ids). Linked from /status, not from user navigation.
const StoryAtlasConnectionsPage = ADMIN_ENABLED
  ? lazy(() => import('./pages/StoryAtlasConnectionsPage').then(m => ({ default: m.StoryAtlasConnectionsPage })))
  : null;
const ThemeAdminPage = ADMIN_ENABLED
  ? lazy(() => import('./pages/ThemeAdminPage').then(m => ({ default: m.ThemeAdminPage })))
  : null;

// App shell: hubs, about, licences, not found
const ExploreHubPage = lazy(() => import('./pages/ExploreHubPage'));
const MemoriseHubPage = lazy(() => import('./pages/MemoriseHubPage'));
const MorePage = lazy(() => import('./pages/MorePage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const LicensesPage = lazy(() => import('./pages/LicensesPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

// Spiritual Guidance / Heart Care (Phase T)
const TherapyPage = lazy(() => import('./pages/TherapyPage').then(m => ({ default: m.TherapyPage })));

// Emotional Guidance — "What the Quran says when you feel…"
const EmotionalGuidancePage = lazy(() => import('./pages/EmotionalGuidancePage').then(m => ({ default: m.EmotionalGuidancePage })));

// Reading Stats Dashboard
const ReadingStatsPage = lazy(() => import('./pages/ReadingStatsPage').then(m => ({ default: m.ReadingStatsPage })));

// Verse Reflection Journal
const JournalPage = lazy(() => import('./pages/JournalPage').then(m => ({ default: m.JournalPage })));

// Quranic Names Explorer
const QuranicNamesPage = lazy(() => import('./pages/QuranicNamesPage').then(m => ({ default: m.QuranicNamesPage })));

// Daily Dhikr Counter
const DhikrPage = lazy(() => import('./pages/DhikrPage').then(m => ({ default: m.DhikrPage })));

// Asbab al-Nuzul — Occasions of Revelation
const AsbabAlNuzulPage = lazy(() => import('./pages/AsbabAlNuzulPage').then(m => ({ default: m.AsbabAlNuzulPage })));

// Revelation Timeline
const RevelationTimelinePage = lazy(() => import('./pages/RevelationTimelinePage').then(m => ({ default: m.RevelationTimelinePage })));

// Quranic Trivia Quiz
const QuizPage = lazy(() => import('./pages/QuizPage').then(m => ({ default: m.QuizPage })));

// Surah Comparison Tool
const SurahComparePage = lazy(() => import('./pages/SurahComparePage').then(m => ({ default: m.SurahComparePage })));

// Memorization Flashcards
const FlashcardsPage = lazy(() => import('./pages/FlashcardsPage').then(m => ({ default: m.FlashcardsPage })));

// Quranic Roots Explorer
const QuranicRootsPage = lazy(() => import('./pages/QuranicRootsPage').then(m => ({ default: m.QuranicRootsPage })));

// Prophets Atlas
const ProphetsPage = lazy(() => import('./pages/ProphetsPage').then(m => ({ default: m.ProphetsPage })));
const ProphetDetailPage = lazy(() => import('./pages/ProphetDetailPage').then(m => ({ default: m.ProphetDetailPage })));
const ProphetJourneyPage = lazy(() => import('./pages/ProphetJourneyPage').then(m => ({ default: m.ProphetJourneyPage })));

// =============================================================================
// Param-forwarding redirect helpers (for legacy / aliased routes)
// =============================================================================

function AsmaThemeRedirect() {
  const { nameId } = useParams<{ nameId: string }>();
  return <Navigate to={`/asma-allah/${nameId ?? ''}`} replace />;
}

/** /story-atlas?person=… → /stories?person=… (keeps the filters). */
function StoryAtlasRedirect() {
  const { search } = useLocation();
  return <Navigate to={`/stories${search}`} replace />;
}

// =============================================================================
// Preloading - Predictive loading for common navigation paths
// =============================================================================

const preloadRoutes: Record<string, () => void> = {
  '/': () => {
    import('./pages/MushafPage');
    import('./pages/AskPage');
  },
  '/mushaf': () => {
    import('./pages/SearchPage');
    import('./pages/QuranPage');
  },
  '/stories': () => {
    import('./pages/StoryDetailPage');
    import('./pages/StoryAtlasDetailPage');
  },
  '/concepts': () => {
    import('./pages/ConceptDetailPage');
  },
  '/themes': () => {
    import('./pages/ThemeDetailPage');
  },
  '/tools': () => {
    import('./pages/tools/PrayerTimesPage');
    import('./pages/tools/HijriCalendarPage');
  },
  '/prophets': () => {
    import('./pages/ProphetDetailPage');
  },
};

// =============================================================================
// Route Preloader Hook
// =============================================================================

function useRoutePreloader() {
  const location = useLocation();

  useEffect(() => {
    const timer = setTimeout(() => {
      const preloader = preloadRoutes[location.pathname];
      if (preloader) {
        preloader();
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [location.pathname]);
}

// =============================================================================
// Main App Component
// =============================================================================

function ContinueReading() {
  return <Navigate to={continueReadingPath()} replace />;
}

function App() {
  useRoutePreloader();
  const { hasChosen } = usePersonaStore();
  const navigate = useNavigate();

  // Android/iOS shell: status bar, splash, back button, deep links and
  // notification taps (no-op on web). Registered once: navigate changes
  // identity on every route change, so it is read through a ref.
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;
  useEffect(() => {
    initNativeShell(
      () => navigateRef.current(-1),
      (path) => navigateRef.current(path),
    ).catch(() => undefined);
  }, []);

  return (
    <Layout>
      {!hasChosen && <OnboardingModal />}
      {isNativeApp ? <NativeConnectivityBanner /> : <AppUpdateBanner />}
      <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Home */}
          <Route path="/" element={<HomePage />} />

          {/* Quran & Mushaf */}
          <Route path="/mushaf" element={<MushafPage />} />
          {/* Surah / juz index. Interim: the juz navigator, until the
              SurahIndexPage (Surah | Juz | Page tabs) replaces it here. */}
          <Route path="/quran" element={<SurahIndexPage />} />
          <Route path="/quran/:suraNo" element={<QuranPage />} />

          {/* Hubs (five-tab navigation) */}
          <Route path="/explore" element={<ExploreHubPage />} />
          <Route path="/memorise" element={<MemoriseHubPage />} />
          <Route path="/more" element={<MorePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/licenses" element={<LicensesPage />} />

          {/* Search & AI */}
          <Route path="/ask" element={<AskPage />} />
          <Route path="/search" element={<SearchPage />} />

          {/* Stories — /stories is the single entry point (rich atlas view) */}
          <Route path="/stories" element={<StoryAtlasPage />} />
          <Route path="/stories/:storyId" element={<StoryDetailPage />} />

          {/* Story Atlas cluster detail + connections (deep-linked, not in nav) */}
          {StoryAtlasConnectionsPage
            ? <Route path="/story-atlas/connections" element={<StoryAtlasConnectionsPage />} />
            : <Route path="/story-atlas/connections" element={<Navigate to="/stories" replace />} />}
          <Route path="/story-atlas/:clusterId" element={<StoryAtlasDetailPage />} />

          {/* Concepts */}
          <Route path="/concepts" element={<ConceptsPage />} />
          <Route path="/concepts/:conceptId" element={<ConceptDetailPage />} />

          {/* Themes */}
          <Route path="/themes" element={<ThemesPage />} />
          {ThemeAdminPage && <Route path="/themes/admin" element={<ThemeAdminPage />} />}
          <Route path="/themes/:themeId" element={<ThemeDetailPage />} />

          {/* Other Features */}
          <Route path="/miracles" element={<MiraclesPage />} />
          <Route path="/similarity" element={<SimilarityPage />} />
          <Route path="/sources" element={<SourcesPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/tafsir/compare" element={<TafsirComparePage />} />
          <Route path="/tafsir/compare/:surah/:ayah" element={<TafsirComparePage />} />

          {/* Surah Atlas */}
          <Route path="/surah-atlas" element={<SurahAtlasPage />} />
          <Route path="/surah-atlas/:surahNumber" element={<SurahAtlasDetailPage />} />

          {/* Memorization */}
          <Route path="/memorization" element={<MemorizationLinksPage />} />
          <Route path="/tasmee" element={<TasmeePage />} />

          {/* Tools */}
          <Route path="/tools" element={<ToolsPage />} />
          <Route path="/tools/prayer-times" element={<PrayerTimesPage />} />
          <Route path="/tools/calendar" element={<HijriCalendarPage />} />
          <Route path="/tools/finance" element={<ZakatCalculatorPage />} />
          <Route path="/tools/maps" element={<MosqueFinderPage />} />
          <Route path="/tools/videos" element={<IslamicVideosPage />} />
          <Route path="/tools/books" element={<IslamicBooksPage />} />
          <Route path="/tools/trips" element={<HajjUmrahGuidePage />} />
          <Route path="/tools/web" element={<IslamicWebSearchPage />} />
          <Route path="/tools/vocabulary" element={<VocabularyPage />} />
          <Route path="/tools/prompt-guide" element={<PromptGuidePage />} />
          <Route path="/tools/surah-memory-atlas" element={<SurahMemoryAtlasPage />} />

          {/* Admin / developer pages (development or VITE_ENABLE_ADMIN builds only) */}
          {StatusDashboardPage && <Route path="/status" element={<StatusDashboardPage />} />}
          {ReviewDashboardPage && <Route path="/admin/review" element={<ReviewDashboardPage />} />}
          {AdminFeedbackPage && <Route path="/admin/feedback" element={<AdminFeedbackPage />} />}

          {/* Spiritual Guidance / Heart Care */}
          <Route path="/therapy" element={<TherapyPage />} />

          {/* Emotional Guidance */}
          <Route path="/guidance" element={<EmotionalGuidancePage />} />

          {/* Reading Stats Dashboard */}
          <Route path="/stats" element={<ReadingStatsPage />} />

          {/* Verse Reflection Journal */}
          <Route path="/journal" element={<JournalPage />} />

          {/* Quranic Names Explorer */}
          <Route path="/names" element={<QuranicNamesPage />} />

          {/* Daily Dhikr Counter */}
          <Route path="/dhikr" element={<DhikrPage />} />

          {/* Revelation Timeline */}
          <Route path="/timeline" element={<RevelationTimelinePage />} />

          {/* Quranic Trivia Quiz */}
          <Route path="/quiz" element={<QuizPage />} />

          {/* /wonders duplicated /miracles; its cards are withheld until an
              editor approves them (owner review), so the old URL lands on the
              single Signs and Miracles page. */}
          <Route path="/wonders" element={<Navigate to="/miracles" replace />} />

          {/* Surah Comparison Tool */}
          <Route path="/compare" element={<SurahComparePage />} />

          {/* Memorization Flashcards */}
          <Route path="/flashcards" element={<FlashcardsPage />} />

          {/* Quranic Roots Explorer */}
          <Route path="/roots" element={<QuranicRootsPage />} />

          {/* Prophets Atlas */}
          <Route path="/prophets" element={<ProphetsPage />} />
          <Route path="/prophets/:prophetId" element={<ProphetDetailPage />} />
          <Route path="/prophets/:prophetId/journey" element={<ProphetJourneyPage />} />

          {/* Bookmarks */}
          <Route path="/bookmarks" element={<BookmarksPage />} />

          {/* Daily Challenge */}
          <Route path="/challenge" element={<DailyChallengePage />} />

          {/* Reading Plan / Khatmah planner */}
          <Route path="/reading-plan" element={<ReadingPlanPage />} />
          {/* Target of reading-reminder taps and tadabbur://continue */}
          <Route path="/continue" element={<ContinueReading />} />

          {/* Quranic Duʿā Explorer */}
          <Route path="/duas" element={<DuasPage />} />

          {/* Quranic Calls Atlas */}
          <Route path="/quranic-calls" element={<QuranicCallsAtlasPage />} />

          {/* Juz Navigator — now the Juz tab of the /quran index */}
          <Route path="/juz" element={<Navigate to="/quran?tab=juz" replace />} />

          {/* Learning Paths */}
          <Route path="/learn" element={<LearnPage />} />

          {/* Asma Allah — 99 Names */}
          <Route path="/asma-allah" element={<AsmaAllahPage />} />
          <Route path="/asma-allah/:nameId" element={<AsmaAllahDetailPage />} />

          {/* Asbab al-Nuzul */}
          <Route path="/asbab" element={<AsbabAlNuzulPage />} />

          {/* Legacy / aliased routes — redirect to canonical paths */}
          <Route path="/story-atlas" element={<StoryAtlasRedirect />} />
          {/* The news tool was removed (its feed proxy failed on every request). */}
          <Route path="/tools/news" element={<Navigate to="/tools" replace />} />
          <Route path="/themes/asma" element={<Navigate to="/asma-allah" replace />} />
          <Route path="/themes/asma/:nameId" element={<AsmaThemeRedirect />} />

          {/* Anything else */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
      </ErrorBoundary>
    </Layout>
  );
}

export default App;
