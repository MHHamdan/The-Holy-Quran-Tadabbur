/**
 * Thematic Journey Component
 *
 * Visualizes a journey through Quranic themes across stories.
 * Shows how a theme (like patience, faith, trust) manifests
 * in different stories and contexts.
 *
 * Features:
 * - Timeline-style visualization of theme occurrences
 * - Story cards with theme highlights
 * - Navigation between related stories
 * - Bilingual support (Arabic/English)
 */
import { useState, useEffect, useCallback } from 'react';
import { graphApi, GraphSearchHit } from '../../lib/api';
import { Language } from '../../i18n/translations';

// =============================================================================
// TYPES
// =============================================================================

interface ThematicJourneyProps {
  theme: string;
  language: Language;
  onStorySelect?: (storyId: string) => void;
}

interface JourneyStop {
  type: string;
  id: string;
  title_ar: string;
  title_en: string;
  description: string;
}

interface JourneyData {
  theme: string;
  stops: JourneyStop[];
}

// =============================================================================
// THEME COLORS
// =============================================================================

const THEME_COLORS: Record<string, { bg: string; border: string; accent: string }> = {
  patience: { bg: '#fef3c7', border: '#f59e0b', accent: '#d97706' },
  faith: { bg: '#dbeafe', border: '#3b82f6', accent: '#2563eb' },
  trust: { bg: '#d1fae5', border: '#10b981', accent: '#059669' },
  repentance: { bg: '#fce7f3', border: '#ec4899', accent: '#db2777' },
  mercy: { bg: '#ede9fe', border: '#8b5cf6', accent: '#7c3aed' },
  default: { bg: '#f3f4f6', border: '#6b7280', accent: '#4b5563' },
};

// =============================================================================
// COMPONENT
// =============================================================================

export function ThematicJourney({
  theme,
  language,
  onStorySelect,
}: ThematicJourneyProps) {
  const [journey, setJourney] = useState<JourneyData | null>(null);
  const [relatedHits, setRelatedHits] = useState<GraphSearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStop, setSelectedStop] = useState<number | null>(null);

  const isRTL = language === 'ar';
  const themeColors = THEME_COLORS[theme.toLowerCase()] || THEME_COLORS.default;

  // Load journey data
  const loadJourney = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch thematic journey
      const journeyResponse = await graphApi.getThematicJourney(theme, {
        lang: language,
        limit: 10,
      });
      setJourney(journeyResponse.data);

      // Also fetch related search results for more context
      const searchResponse = await graphApi.semanticSearch(theme, {
        lang: language,
        limit: 10,
      });
      setRelatedHits(searchResponse.data.hits.filter(h => h.type === 'story'));
    } catch (err) {
      console.error('Failed to load thematic journey:', err);
      setError(language === 'ar'
        ? 'حدث خطأ أثناء تحميل الرحلة'
        : 'Failed to load journey');
    } finally {
      setLoading(false);
    }
  }, [theme, language]);

  useEffect(() => {
    loadJourney();
  }, [loadJourney]);

  // Handle stop click
  const handleStopClick = (index: number, stop: JourneyStop) => {
    setSelectedStop(index);
    if (stop.type === 'story' && onStorySelect) {
      onStorySelect(stop.id);
    }
  };

  if (loading) {
    return (
      <div className="thematic-journey loading">
        <div className="loading-spinner" />
        <span>{language === 'ar' ? 'جاري التحميل...' : 'Loading...'}</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="thematic-journey error">
        <span>{error}</span>
        <button onClick={loadJourney}>
          {language === 'ar' ? 'إعادة المحاولة' : 'Retry'}
        </button>
      </div>
    );
  }

  return (
    <div
      className={`thematic-journey ${isRTL ? 'rtl' : 'ltr'}`}
      dir={isRTL ? 'rtl' : 'ltr'}
      style={{
        '--theme-bg': themeColors.bg,
        '--theme-border': themeColors.border,
        '--theme-accent': themeColors.accent,
      } as React.CSSProperties}
    >
      {/* Header */}
      <div className="journey-header">
        <div className="theme-badge">
          <span className="theme-icon">🏷️</span>
          <span className="theme-name">{theme}</span>
        </div>
        <h2>
          {language === 'ar'
            ? 'رحلة عبر القصص'
            : 'Journey Through Stories'}
        </h2>
      </div>

      {/* Journey Timeline */}
      {journey && journey.stops.length > 0 && (
        <div className="journey-timeline">
          {journey.stops.map((stop, index) => (
            <div
              key={stop.id}
              className={`journey-stop ${selectedStop === index ? 'selected' : ''}`}
              onClick={() => handleStopClick(index, stop)}
            >
              <div className="stop-connector">
                <div className="connector-line" />
                <div className="connector-dot" />
              </div>
              <div className="stop-content">
                <div className="stop-type">
                  {stop.type === 'story' ? '📖' : '📍'}
                </div>
                <div className="stop-details">
                  <h3 className="stop-title">
                    {language === 'ar' ? stop.title_ar : stop.title_en}
                  </h3>
                  {stop.description && (
                    <p className="stop-description">{stop.description}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Fallback: Show related stories if no journey stops */}
      {(!journey || journey.stops.length === 0) && relatedHits.length > 0 && (
        <div className="related-stories">
          <h3>{language === 'ar' ? 'قصص ذات صلة' : 'Related Stories'}</h3>
          <div className="stories-grid">
            {relatedHits.map((hit) => (
              <div
                key={hit.id}
                className="story-card"
                onClick={() => onStorySelect?.(hit.id)}
              >
                <h4>{language === 'ar' ? hit.title_ar : hit.title}</h4>
                <p>{language === 'ar' ? hit.content_ar : hit.content}</p>
                <div className="story-confidence">
                  {Math.round(hit.confidence * 100)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!journey || journey.stops.length === 0) && relatedHits.length === 0 && (
        <div className="empty-state">
          <span className="empty-icon">🔍</span>
          <p>
            {language === 'ar'
              ? 'لم يتم العثور على قصص متعلقة بهذا الموضوع'
              : 'No stories found for this theme'}
          </p>
        </div>
      )}

      {/* Styles */}
      <style>{`
        .thematic-journey {
          font-family: var(--font-family, 'Noto Sans Arabic', 'Noto Sans', sans-serif);
          padding: 1.5rem;
          background: white;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .thematic-journey.loading,
        .thematic-journey.error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 1rem;
          min-height: 200px;
        }

        .loading-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #e2e8f0;
          border-top-color: var(--theme-accent, #3b82f6);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .journey-header {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1.5rem;
          flex-wrap: wrap;
        }

        .theme-badge {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: var(--theme-bg);
          border: 2px solid var(--theme-border);
          border-radius: 20px;
        }

        .theme-icon {
          font-size: 1.25rem;
        }

        .theme-name {
          font-weight: 600;
          color: var(--theme-accent);
          text-transform: capitalize;
        }

        .journey-header h2 {
          margin: 0;
          font-size: 1.25rem;
          color: #374151;
        }

        .journey-timeline {
          display: flex;
          flex-direction: column;
          gap: 0;
        }

        .journey-stop {
          display: flex;
          gap: 1rem;
          cursor: pointer;
          padding: 0.5rem;
          border-radius: 8px;
          transition: background 0.2s;
        }

        .journey-stop:hover {
          background: #f8fafc;
        }

        .journey-stop.selected {
          background: var(--theme-bg);
        }

        .stop-connector {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 20px;
        }

        .connector-line {
          width: 2px;
          flex: 1;
          background: #e2e8f0;
          min-height: 20px;
        }

        .journey-stop:first-child .connector-line {
          background: transparent;
        }

        .connector-dot {
          width: 12px;
          height: 12px;
          background: var(--theme-border);
          border-radius: 50%;
          flex-shrink: 0;
        }

        .journey-stop.selected .connector-dot {
          background: var(--theme-accent);
          box-shadow: 0 0 0 4px var(--theme-bg);
        }

        .stop-content {
          flex: 1;
          display: flex;
          gap: 0.75rem;
          padding-bottom: 1rem;
        }

        .stop-type {
          font-size: 1.5rem;
        }

        .stop-details {
          flex: 1;
        }

        .stop-title {
          margin: 0 0 0.25rem 0;
          font-size: 1rem;
          color: #1f2937;
        }

        .stop-description {
          margin: 0;
          font-size: 0.875rem;
          color: #6b7280;
          line-height: 1.5;
        }

        .related-stories h3 {
          margin: 0 0 1rem 0;
          font-size: 1rem;
          color: #374151;
        }

        .stories-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 1rem;
        }

        .story-card {
          padding: 1rem;
          background: #f8fafc;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid #e2e8f0;
          position: relative;
        }

        .story-card:hover {
          background: var(--theme-bg);
          border-color: var(--theme-border);
        }

        .story-card h4 {
          margin: 0 0 0.5rem 0;
          font-size: 1rem;
          color: #1f2937;
        }

        .story-card p {
          margin: 0;
          font-size: 0.875rem;
          color: #6b7280;
          line-height: 1.5;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .story-confidence {
          position: absolute;
          top: 0.5rem;
          right: 0.5rem;
          font-size: 0.75rem;
          padding: 0.125rem 0.375rem;
          background: #dcfce7;
          color: #166534;
          border-radius: 4px;
        }

        .rtl .story-confidence {
          right: auto;
          left: 0.5rem;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 3rem;
          text-align: center;
        }

        .empty-icon {
          font-size: 3rem;
          opacity: 0.5;
        }

        .empty-state p {
          margin: 0;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
}

export default ThematicJourney;
