/**
 * Tadabbur App - Route Configuration with Code Splitting
 *
 * Performance optimizations:
 * 1. React.lazy for route-based code splitting
 * 2. Suspense with loading fallbacks
 * 3. Preloading for predictive navigation
 */

import { Routes, Route, useLocation } from 'react-router-dom';
import { Suspense, lazy, useEffect, memo } from 'react';
import { Layout } from './components/layout/Layout';
import { Loader2 } from 'lucide-react';

// =============================================================================
// Loading Component - Optimized for perceived performance
// =============================================================================

const PageLoader = memo(function PageLoader() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center">
      <Loader2 className="w-10 h-10 text-emerald-600 animate-spin mb-4" />
      <p className="text-gray-600 font-arabic">جاري التحميل...</p>
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

// Stories feature
const StoriesPage = lazy(() => import('./pages/StoriesPage').then(m => ({ default: m.StoriesPage })));
const StoryDetailPage = lazy(() => import('./pages/StoryDetailPage').then(m => ({ default: m.StoryDetailPage })));
const StoryAtlasPage = lazy(() => import('./pages/StoryAtlasPage').then(m => ({ default: m.StoryAtlasPage })));
const StoryAtlasDetailPage = lazy(() => import('./pages/StoryAtlasDetailPage').then(m => ({ default: m.StoryAtlasDetailPage })));

// Concepts feature
const ConceptsPage = lazy(() => import('./pages/ConceptsPage').then(m => ({ default: m.ConceptsPage })));
const ConceptDetailPage = lazy(() => import('./pages/ConceptDetailPage').then(m => ({ default: m.ConceptDetailPage })));

// Themes feature
const ThemesPage = lazy(() => import('./pages/ThemesPage').then(m => ({ default: m.ThemesPage })));
const ThemeDetailPage = lazy(() => import('./pages/ThemeDetailPage').then(m => ({ default: m.ThemeDetailPage })));
const ThemeAdminPage = lazy(() => import('./pages/ThemeAdminPage').then(m => ({ default: m.ThemeAdminPage })));

// Other pages
const MiraclesPage = lazy(() => import('./pages/MiraclesPage').then(m => ({ default: m.MiraclesPage })));
const SimilarityPage = lazy(() => import('./pages/SimilarityPage').then(m => ({ default: m.SimilarityPage })));
const SourcesPage = lazy(() => import('./pages/SourcesPage').then(m => ({ default: m.SourcesPage })));

// Tools pages (bundled together)
const ToolsPage = lazy(() => import('./pages/ToolsPage').then(m => ({ default: m.ToolsPage })));
const ZakatCalculatorPage = lazy(() => import('./pages/tools/ZakatCalculatorPage').then(m => ({ default: m.ZakatCalculatorPage })));
const MosqueFinderPage = lazy(() => import('./pages/tools/MosqueFinderPage').then(m => ({ default: m.MosqueFinderPage })));
const IslamicVideosPage = lazy(() => import('./pages/tools/IslamicVideosPage').then(m => ({ default: m.IslamicVideosPage })));
const IslamicNewsPage = lazy(() => import('./pages/tools/IslamicNewsPage').then(m => ({ default: m.IslamicNewsPage })));
const IslamicBooksPage = lazy(() => import('./pages/tools/IslamicBooksPage').then(m => ({ default: m.IslamicBooksPage })));
const HajjUmrahGuidePage = lazy(() => import('./pages/tools/HajjUmrahGuidePage').then(m => ({ default: m.HajjUmrahGuidePage })));
const IslamicWebSearchPage = lazy(() => import('./pages/tools/IslamicWebSearchPage').then(m => ({ default: m.IslamicWebSearchPage })));
const PrayerTimesPage = lazy(() => import('./pages/tools/PrayerTimesPage').then(m => ({ default: m.PrayerTimesPage })));
const HijriCalendarPage = lazy(() => import('./pages/tools/HijriCalendarPage').then(m => ({ default: m.HijriCalendarPage })));

// =============================================================================
// Preloading - Predictive loading for common navigation paths
// =============================================================================

const preloadRoutes: Record<string, () => void> = {
  '/': () => {
    // From home, users often go to Mushaf or Ask
    import('./pages/MushafPage');
    import('./pages/AskPage');
  },
  '/mushaf': () => {
    // From Mushaf, users might search or go to Quran
    import('./pages/SearchPage');
    import('./pages/QuranPage');
  },
  '/stories': () => {
    import('./pages/StoryDetailPage');
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
};

// =============================================================================
// Route Preloader Hook
// =============================================================================

function useRoutePreloader() {
  const location = useLocation();

  useEffect(() => {
    // Preload after a short delay to not block current render
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

function App() {
  useRoutePreloader();

  return (
    <Layout>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Home */}
          <Route path="/" element={<HomePage />} />

          {/* Quran & Mushaf */}
          <Route path="/mushaf" element={<MushafPage />} />
          <Route path="/quran/:suraNo" element={<QuranPage />} />

          {/* Search & AI */}
          <Route path="/ask" element={<AskPage />} />
          <Route path="/search" element={<SearchPage />} />

          {/* Stories */}
          <Route path="/stories" element={<StoriesPage />} />
          <Route path="/stories/:storyId" element={<StoryDetailPage />} />
          <Route path="/story-atlas" element={<StoryAtlasPage />} />
          <Route path="/story-atlas/:clusterId" element={<StoryAtlasDetailPage />} />

          {/* Concepts */}
          <Route path="/concepts" element={<ConceptsPage />} />
          <Route path="/concepts/:conceptId" element={<ConceptDetailPage />} />

          {/* Themes */}
          <Route path="/themes" element={<ThemesPage />} />
          <Route path="/themes/admin" element={<ThemeAdminPage />} />
          <Route path="/themes/:themeId" element={<ThemeDetailPage />} />

          {/* Other Features */}
          <Route path="/miracles" element={<MiraclesPage />} />
          <Route path="/similarity" element={<SimilarityPage />} />
          <Route path="/sources" element={<SourcesPage />} />

          {/* Tools */}
          <Route path="/tools" element={<ToolsPage />} />
          <Route path="/tools/prayer-times" element={<PrayerTimesPage />} />
          <Route path="/tools/calendar" element={<HijriCalendarPage />} />
          <Route path="/tools/finance" element={<ZakatCalculatorPage />} />
          <Route path="/tools/maps" element={<MosqueFinderPage />} />
          <Route path="/tools/videos" element={<IslamicVideosPage />} />
          <Route path="/tools/news" element={<IslamicNewsPage />} />
          <Route path="/tools/books" element={<IslamicBooksPage />} />
          <Route path="/tools/trips" element={<HajjUmrahGuidePage />} />
          <Route path="/tools/web" element={<IslamicWebSearchPage />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}

export default App;
