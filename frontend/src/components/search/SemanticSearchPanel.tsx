/**
 * Semantic Search Panel Component
 *
 * A comprehensive search interface for exploring:
 * - Stories
 * - Themes and concepts
 * - Prophets and figures
 *
 * Features:
 * - Bilingual support (Arabic/English)
 * - Query expansion with related terms
 * - Result filtering by type
 * - Related concepts suggestions
 */
import { useState, useCallback, useEffect } from 'react';
import { graphApi, GraphSearchHit, SemanticSearchResponse } from '../../lib/api';
import { Language } from '../../i18n/translations';

// =============================================================================
// TYPES
// =============================================================================

interface SemanticSearchPanelProps {
  language: Language;
  onResultSelect?: (hit: GraphSearchHit) => void;
  initialQuery?: string;
}

type ResultType = 'all' | 'theme' | 'story' | 'person';

// =============================================================================
// ICONS
// =============================================================================

const RESULT_TYPE_ICONS: Record<string, string> = {
  theme: '🏷️',
  story: '📖',
  person: '👤',
  event: '📍',
};

const RESULT_TYPE_LABELS = {
  ar: {
    all: 'الكل',
    theme: 'المواضيع',
    story: 'القصص',
    person: 'الشخصيات',
  },
  en: {
    all: 'All',
    theme: 'Themes',
    story: 'Stories',
    person: 'Persons',
  },
};

// =============================================================================
// COMPONENT
// =============================================================================

export function SemanticSearchPanel({
  language,
  onResultSelect,
  initialQuery = '',
}: SemanticSearchPanelProps) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SemanticSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<ResultType>('all');

  const isRTL = language === 'ar';

  // Perform search
  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await graphApi.semanticSearch(searchQuery, {
        lang: language,
        expand: true,
        limit: 20,
        min_confidence: 0.3,
      });
      setResults(response.data);
    } catch (err) {
      console.error('Semantic search error:', err);
      setError(language === 'ar'
        ? 'حدث خطأ أثناء البحث'
        : 'An error occurred during search');
    } finally {
      setLoading(false);
    }
  }, [language]);

  // Handle search submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    performSearch(suggestion);
  };

  // Handle related concept click
  const handleRelatedConceptClick = (concept: { id: string; label_ar: string; label_en: string }) => {
    const label = language === 'ar' ? concept.label_ar : concept.label_en;
    setQuery(label);
    performSearch(label);
  };

  // Filter results by type
  const filteredHits = results?.hits.filter(hit =>
    filterType === 'all' || hit.type === filterType
  ) || [];

  // Initial search if query provided
  useEffect(() => {
    if (initialQuery) {
      performSearch(initialQuery);
    }
  }, [initialQuery, performSearch]);

  return (
    <div className={`semantic-search-panel ${isRTL ? 'rtl' : 'ltr'}`} dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Search Form */}
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-wrapper">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={language === 'ar'
              ? 'ابحث عن موضوع أو قصة أو شخصية...'
              : 'Search for a theme, story, or person...'}
            className="search-input"
          />
          <button
            type="submit"
            className="search-button"
            disabled={loading || !query.trim()}
          >
            {loading ? '...' : '🔍'}
          </button>
        </div>
      </form>

      {/* Query Expansion Info */}
      {results?.expanded_query && results.expanded_query !== results.query && (
        <div className="query-expansion">
          <span className="expansion-label">
            {language === 'ar' ? 'بحث موسع:' : 'Expanded:'}
          </span>
          <span className="expanded-terms">
            {results.expanded_query}
          </span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Results Section */}
      {results && (
        <div className="results-section">
          {/* Results Header */}
          <div className="results-header">
            <span className="results-count">
              {language === 'ar'
                ? `${results.total_found} نتيجة`
                : `${results.total_found} results`}
              {results.search_time_ms && (
                <span className="search-time"> ({results.search_time_ms}ms)</span>
              )}
            </span>

            {/* Type Filter */}
            <div className="type-filters">
              {(['all', 'theme', 'story', 'person'] as ResultType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setFilterType(type)}
                  className={`filter-btn ${filterType === type ? 'active' : ''}`}
                >
                  {type !== 'all' && RESULT_TYPE_ICONS[type]} {RESULT_TYPE_LABELS[language][type]}
                </button>
              ))}
            </div>
          </div>

          {/* Results List */}
          <div className="results-list">
            {filteredHits.length === 0 ? (
              <div className="no-results">
                {language === 'ar'
                  ? 'لا توجد نتائج'
                  : 'No results found'}
              </div>
            ) : (
              filteredHits.map((hit) => (
                <div
                  key={hit.id}
                  className="result-item"
                  onClick={() => onResultSelect?.(hit)}
                >
                  <div className="result-header">
                    <span className="result-type-icon">{RESULT_TYPE_ICONS[hit.type]}</span>
                    <span className="result-title">
                      {language === 'ar' ? hit.title_ar : hit.title}
                    </span>
                    <span className="result-confidence">
                      {Math.round(hit.confidence * 100)}%
                    </span>
                  </div>
                  {(hit.content || hit.content_ar) && (
                    <div className="result-content">
                      {language === 'ar' ? hit.content_ar : hit.content}
                    </div>
                  )}
                  {hit.metadata?.category ? (
                    <div className="result-meta">
                      <span className="category-badge">
                        {String(hit.metadata.category)}
                      </span>
                      {hit.metadata.matched_via ? (
                        <span className="match-type">
                          via {String(hit.metadata.matched_via)}
                        </span>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ))
            )}
          </div>

          {/* Related Concepts */}
          {results.related_concepts.length > 0 && (
            <div className="related-concepts">
              <h4>
                {language === 'ar' ? 'مفاهيم ذات صلة' : 'Related Concepts'}
              </h4>
              <div className="concepts-list">
                {results.related_concepts.map((concept) => (
                  <button
                    key={concept.id}
                    className="concept-chip"
                    onClick={() => handleRelatedConceptClick(concept)}
                  >
                    {language === 'ar' ? concept.label_ar : concept.label_en}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Suggested Queries */}
          {results.suggested_queries.length > 0 && (
            <div className="suggested-queries">
              <h4>
                {language === 'ar' ? 'اقتراحات' : 'Suggestions'}
              </h4>
              <div className="suggestions-list">
                {results.suggested_queries.map((suggestion) => (
                  <button
                    key={suggestion}
                    className="suggestion-chip"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Styles */}
      <style>{`
        .semantic-search-panel {
          font-family: var(--font-family, 'Noto Sans Arabic', 'Noto Sans', sans-serif);
          max-width: 800px;
          margin: 0 auto;
          padding: 1rem;
        }

        .search-form {
          margin-bottom: 1rem;
        }

        .search-input-wrapper {
          display: flex;
          gap: 0.5rem;
        }

        .search-input {
          flex: 1;
          padding: 0.75rem 1rem;
          font-size: 1rem;
          border: 2px solid #e2e8f0;
          border-radius: 8px;
          outline: none;
          transition: border-color 0.2s;
        }

        .search-input:focus {
          border-color: #3b82f6;
        }

        .rtl .search-input {
          text-align: right;
        }

        .search-button {
          padding: 0.75rem 1.25rem;
          font-size: 1.25rem;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .search-button:hover:not(:disabled) {
          background: #2563eb;
        }

        .search-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .query-expansion {
          padding: 0.5rem 1rem;
          background: #f0f9ff;
          border-radius: 6px;
          font-size: 0.875rem;
          color: #1e40af;
          margin-bottom: 1rem;
        }

        .expansion-label {
          font-weight: 600;
          margin-inline-end: 0.5rem;
        }

        .error-message {
          padding: 0.75rem 1rem;
          background: #fef2f2;
          color: #991b1b;
          border-radius: 6px;
          margin-bottom: 1rem;
        }

        .results-section {
          background: white;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          overflow: hidden;
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          border-bottom: 1px solid #e2e8f0;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .results-count {
          font-weight: 600;
          color: #374151;
        }

        .search-time {
          font-weight: 400;
          color: #6b7280;
          font-size: 0.875rem;
        }

        .type-filters {
          display: flex;
          gap: 0.25rem;
        }

        .filter-btn {
          padding: 0.375rem 0.75rem;
          font-size: 0.875rem;
          border: 1px solid #e2e8f0;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .filter-btn:hover {
          background: #f8fafc;
        }

        .filter-btn.active {
          background: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }

        .results-list {
          max-height: 400px;
          overflow-y: auto;
        }

        .result-item {
          padding: 1rem;
          border-bottom: 1px solid #f1f5f9;
          cursor: pointer;
          transition: background 0.2s;
        }

        .result-item:hover {
          background: #f8fafc;
        }

        .result-item:last-child {
          border-bottom: none;
        }

        .result-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.5rem;
        }

        .result-type-icon {
          font-size: 1.25rem;
        }

        .result-title {
          font-weight: 600;
          color: #1f2937;
          flex: 1;
        }

        .result-confidence {
          font-size: 0.75rem;
          padding: 0.125rem 0.375rem;
          background: #dcfce7;
          color: #166534;
          border-radius: 4px;
        }

        .result-content {
          font-size: 0.875rem;
          color: #6b7280;
          line-height: 1.5;
          margin-bottom: 0.5rem;
        }

        .result-meta {
          display: flex;
          gap: 0.5rem;
          font-size: 0.75rem;
        }

        .category-badge {
          padding: 0.125rem 0.375rem;
          background: #e0e7ff;
          color: #3730a3;
          border-radius: 4px;
        }

        .match-type {
          color: #9ca3af;
        }

        .no-results {
          padding: 2rem;
          text-align: center;
          color: #6b7280;
        }

        .related-concepts,
        .suggested-queries {
          padding: 1rem;
          border-top: 1px solid #e2e8f0;
          background: #fafafa;
        }

        .related-concepts h4,
        .suggested-queries h4 {
          margin: 0 0 0.75rem 0;
          font-size: 0.875rem;
          font-weight: 600;
          color: #374151;
        }

        .concepts-list,
        .suggestions-list {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .concept-chip,
        .suggestion-chip {
          padding: 0.375rem 0.75rem;
          font-size: 0.875rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .concept-chip:hover,
        .suggestion-chip:hover {
          background: #eff6ff;
          border-color: #3b82f6;
          color: #1d4ed8;
        }
      `}</style>
    </div>
  );
}

export default SemanticSearchPanel;
