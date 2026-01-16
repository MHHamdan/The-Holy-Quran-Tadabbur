/**
 * Concept Search Panel Component.
 *
 * Provides an interface for:
 * - Searching concepts by keyword
 * - Filtering by concept type
 * - Multi-concept selection for combined search
 * - Cross-language concept expansion
 * - Navigation to Quran verses with highlighting
 * - Natural language multi-concept search (e.g., "Solomon and Queen of Sheba")
 *
 * Arabic: لوحة البحث عن المفاهيم
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  multiConceptApi,
  ConceptExpansionResult,
  MultiConceptMatch,
  ConceptSuggestion
} from '../../lib/api';

interface ConceptSearchPanelProps {
  onConceptSelect?: (conceptIds: string[]) => void;
  initialQuery?: string;
  showViewInQuran?: boolean;
  enableNaturalLanguageSearch?: boolean;
}

const CONCEPT_TYPE_LABELS = {
  theme: { en: 'Theme', ar: 'موضوع', icon: '📖' },
  person: { en: 'Person', ar: 'شخصية', icon: '👤' },
  place: { en: 'Place', ar: 'مكان', icon: '📍' },
  nation: { en: 'Nation', ar: 'قوم', icon: '🏛️' },
  miracle: { en: 'Miracle', ar: 'معجزة', icon: '✨' },
  moral_pattern: { en: 'Pattern', ar: 'نمط', icon: '🔄' },
};

type SearchMode = 'concept' | 'natural';

export function ConceptSearchPanel({
  onConceptSelect,
  initialQuery = '',
  showViewInQuran = true,
  enableNaturalLanguageSearch = true,
}: ConceptSearchPanelProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<ConceptExpansionResult[]>([]);
  const [selectedConcepts, setSelectedConcepts] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [crossLanguage, setCrossLanguage] = useState<{
    arabic_terms: string[];
    english_terms: string[];
    detected_themes: string[];
  } | null>(null);

  // Natural language search state
  const [searchMode, setSearchMode] = useState<SearchMode>('natural');
  const [naturalSearchResults, setNaturalSearchResults] = useState<MultiConceptMatch[]>([]);
  const [suggestions, setSuggestions] = useState<ConceptSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [parsedQuery, setParsedQuery] = useState<{
    concepts: string[];
    connector_type: 'and' | 'or';
    is_multi_concept: boolean;
  } | null>(null);
  const [conceptDistribution, setConceptDistribution] = useState<Record<string, number>>({});
  const [searchTime, setSearchTime] = useState<number>(0);

  // Debounced search - concept mode
  useEffect(() => {
    if (searchMode !== 'concept' || !query.trim() || query.length < 2) {
      if (searchMode === 'concept') {
        setResults([]);
        setCrossLanguage(null);
      }
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await multiConceptApi.expandConceptQuery(query, {
          maxConcepts: 15,
          includeAliases: true,
        });

        if (response.data.ok) {
          setResults(response.data.matched_concepts);
          setCrossLanguage(response.data.cross_language_expansion);
        } else {
          setError('Search failed');
        }
      } catch (err) {
        setError('Failed to search concepts');
        console.error('Concept search error:', err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, searchMode]);

  // Natural language search - get suggestions as user types
  useEffect(() => {
    if (searchMode !== 'natural' || !query.trim() || query.length < 1) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const response = await multiConceptApi.getConceptSuggestions(query, 6);
        if (response.data.ok) {
          setSuggestions(response.data.suggestions);
          setShowSuggestions(response.data.suggestions.length > 0);
        }
      } catch (err) {
        console.error('Suggestion fetch error:', err);
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [query, searchMode]);

  // Execute natural language multi-concept search
  const executeNaturalSearch = useCallback(async () => {
    if (!query.trim() || query.length < 2) return;

    setLoading(true);
    setError(null);
    setShowSuggestions(false);

    try {
      const response = await multiConceptApi.searchMultiConcept(query, {
        limit: 50,
        connector: 'or',
      });

      if (response.data.ok) {
        setNaturalSearchResults(response.data.matches);
        setParsedQuery(response.data.parsed_query);
        setConceptDistribution(response.data.concept_distribution);
        setSearchTime(response.data.search_time_ms);
      } else {
        setError('Search failed');
      }
    } catch (err) {
      setError('Failed to search');
      console.error('Natural search error:', err);
    } finally {
      setLoading(false);
    }
  }, [query]);

  // Handle Enter key for natural language search
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && searchMode === 'natural') {
      executeNaturalSearch();
    }
  }, [executeNaturalSearch, searchMode]);

  // Handle suggestion click
  const handleSuggestionClick = useCallback((suggestion: ConceptSuggestion) => {
    // Add the concept to query
    const conceptLabel = suggestion.en[0] || suggestion.key;
    setQuery(prev => {
      if (prev.toLowerCase().includes(conceptLabel.toLowerCase())) {
        return prev;
      }
      return prev ? `${prev} and ${conceptLabel}` : conceptLabel;
    });
    setShowSuggestions(false);
  }, []);

  const handleConceptToggle = useCallback((conceptId: string) => {
    setSelectedConcepts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(conceptId)) {
        newSet.delete(conceptId);
      } else {
        newSet.add(conceptId);
      }

      // Notify parent
      if (onConceptSelect) {
        onConceptSelect(Array.from(newSet));
      }

      return newSet;
    });
  }, [onConceptSelect]);

  const handleViewInQuran = useCallback(() => {
    if (selectedConcepts.size === 0) return;

    const conceptIds = Array.from(selectedConcepts).join(',');
    navigate(`/quran?concepts=${encodeURIComponent(conceptIds)}`);
  }, [selectedConcepts, navigate]);

  const filteredResults = typeFilter
    ? results.filter(r => r.concept.type === typeFilter)
    : results;

  const getTypeLabel = (type: string) => {
    const labels = CONCEPT_TYPE_LABELS[type as keyof typeof CONCEPT_TYPE_LABELS];
    return labels || { en: type, ar: type, icon: '📌' };
  };

  return (
    <div className="concept-search-panel bg-white rounded-lg shadow-md p-4">
      {/* Search Mode Toggle */}
      {enableNaturalLanguageSearch && (
        <div className="mb-3 flex gap-2">
          <button
            onClick={() => setSearchMode('natural')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              searchMode === 'natural'
                ? 'bg-emerald-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🔍 Natural Search
          </button>
          <button
            onClick={() => setSearchMode('concept')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              searchMode === 'concept'
                ? 'bg-emerald-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            📚 Concept Browser
          </button>
        </div>
      )}

      {/* Search Input */}
      <div className="mb-4">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            onFocus={() => searchMode === 'natural' && suggestions.length > 0 && setShowSuggestions(true)}
            placeholder={
              searchMode === 'natural'
                ? "Try: 'Solomon and Queen of Sheba' or 'موسى و فرعون'..."
                : "Search concepts (e.g., patience, صبر, Moses)..."
            }
            className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            dir="auto"
          />
          {loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin h-5 w-5 border-2 border-emerald-500 border-t-transparent rounded-full" />
            </div>
          )}
          {searchMode === 'natural' && !loading && (
            <button
              onClick={executeNaturalSearch}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 px-2 py-1 bg-emerald-500 text-white rounded text-sm hover:bg-emerald-600"
            >
              Search
            </button>
          )}

          {/* Suggestions Dropdown */}
          {showSuggestions && searchMode === 'natural' && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
              <div className="p-2 text-xs text-gray-500 border-b">
                Click to add concepts, press Enter to search
              </div>
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion.key}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full px-3 py-2 text-left hover:bg-emerald-50 flex items-center justify-between"
                >
                  <div>
                    <span className="font-medium text-gray-800">{suggestion.en[0]}</span>
                    <span className="mx-2 text-gray-400">|</span>
                    <span className="text-gray-600" dir="rtl">{suggestion.ar[0]}</span>
                  </div>
                  <span className="text-xs text-gray-400">+</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Parsed Query Info (Natural Mode) */}
      {searchMode === 'natural' && parsedQuery && parsedQuery.is_multi_concept && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-800 mb-2">
            <span className="font-semibold">Multi-concept search:</span>
            {' '}Finding verses with {parsedQuery.connector_type === 'or' ? 'any' : 'all'} of:
          </p>
          <div className="flex flex-wrap gap-2">
            {parsedQuery.concepts.map((concept, i) => (
              <span
                key={i}
                className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm flex items-center gap-2"
              >
                {concept}
                {conceptDistribution[concept] !== undefined && (
                  <span className="text-xs bg-blue-200 px-1 rounded">
                    {conceptDistribution[concept]} matches
                  </span>
                )}
              </span>
            ))}
          </div>
          {searchTime > 0 && (
            <p className="text-xs text-blue-600 mt-2">
              Search completed in {searchTime.toFixed(0)}ms
            </p>
          )}
        </div>
      )}

      {/* Natural Search Results */}
      {searchMode === 'natural' && naturalSearchResults.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Found {naturalSearchResults.length} verses
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {naturalSearchResults.slice(0, 20).map((match) => (
              <div
                key={match.verse_id}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-emerald-300 cursor-pointer"
                onClick={() => navigate(`/quran/${match.sura_no}#${match.aya_no}`)}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-emerald-600">
                    {match.sura_name_ar} ({match.reference})
                  </span>
                  <span className="text-xs text-gray-500">
                    {Math.round(match.relevance_score * 100)}% relevant
                  </span>
                </div>
                <p className="text-sm text-gray-800 leading-relaxed" dir="rtl">
                  {match.highlighted_text || match.text_uthmani}
                </p>
                {match.matched_concepts.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {match.matched_concepts.map((mc, i) => (
                      <span
                        key={i}
                        className="px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded text-xs"
                      >
                        {mc.concept}: {mc.matched_terms.slice(0, 2).join(', ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cross-Language Expansion Info (Concept Mode) */}
      {searchMode === 'concept' && crossLanguage && crossLanguage.detected_themes.length > 0 && (
        <div className="mb-4 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
          <p className="text-sm text-emerald-800 mb-2">
            <span className="font-semibold">Cross-language expansion:</span>
          </p>
          <div className="flex flex-wrap gap-2">
            {crossLanguage.arabic_terms.slice(0, 5).map((term, i) => (
              <span
                key={`ar-${i}`}
                className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-sm"
                dir="rtl"
              >
                {term}
              </span>
            ))}
            {crossLanguage.english_terms.slice(0, 5).map((term, i) => (
              <span
                key={`en-${i}`}
                className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm"
              >
                {term}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Type Filters (Concept Mode) */}
      {searchMode === 'concept' && results.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          <button
            onClick={() => setTypeFilter(null)}
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              typeFilter === null
                ? 'bg-emerald-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          {Array.from(new Set(results.map(r => r.concept.type))).map(type => {
            const labels = getTypeLabel(type);
            return (
              <button
                key={type}
                onClick={() => setTypeFilter(type === typeFilter ? null : type)}
                className={`px-3 py-1 rounded-full text-sm transition-colors flex items-center gap-1 ${
                  typeFilter === type
                    ? 'bg-emerald-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span>{labels.icon}</span>
                <span>{labels.en}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Selected Concepts Bar */}
      {selectedConcepts.size > 0 && (
        <div className="mb-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-amber-800">
              Selected Concepts ({selectedConcepts.size}):
            </span>
            {showViewInQuran && (
              <button
                onClick={handleViewInQuran}
                className="px-3 py-1 bg-amber-500 text-white rounded-lg text-sm hover:bg-amber-600 transition-colors"
              >
                View in Quran →
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {Array.from(selectedConcepts).map(id => {
              const concept = results.find(r => r.concept.id === id)?.concept;
              return (
                <span
                  key={id}
                  className="px-2 py-1 bg-amber-200 text-amber-800 rounded text-sm flex items-center gap-1"
                >
                  {concept?.label_ar || id}
                  <button
                    onClick={() => handleConceptToggle(id)}
                    className="ml-1 text-amber-600 hover:text-amber-800"
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {/* Results List (Concept Mode) */}
      {searchMode === 'concept' && (
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {filteredResults.map(result => {
          const isSelected = selectedConcepts.has(result.concept.id);
          const typeLabels = getTypeLabel(result.concept.type);

          return (
            <div
              key={result.concept.id}
              className={`p-3 rounded-lg border transition-colors cursor-pointer ${
                isSelected
                  ? 'border-emerald-500 bg-emerald-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
              onClick={() => handleConceptToggle(result.concept.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{typeLabels.icon}</span>
                    <span className="font-semibold text-gray-800" dir="rtl">
                      {result.concept.label_ar}
                    </span>
                    <span className="text-gray-500">|</span>
                    <span className="text-gray-700">
                      {result.concept.label_en}
                    </span>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                      {typeLabels.en}
                    </span>
                  </div>

                  {/* Aliases */}
                  {(result.aliases.ar.length > 0 || result.aliases.en.length > 0) && (
                    <div className="text-sm text-gray-500 mb-2">
                      <span className="font-medium">Aliases: </span>
                      {result.aliases.ar.slice(0, 3).join('، ')}
                      {result.aliases.en.length > 0 && (
                        <span className="ml-2">
                          {result.aliases.en.slice(0, 3).join(', ')}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Related Concepts */}
                  {result.related_concepts.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {result.related_concepts.slice(0, 3).map((rel, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs"
                          title={`${rel.relation_type}: ${rel.strength.toFixed(2)}`}
                        >
                          {rel.label_ar || rel.label_en}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Selection indicator */}
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                  isSelected
                    ? 'border-emerald-500 bg-emerald-500 text-white'
                    : 'border-gray-300'
                }`}>
                  {isSelected && <span>✓</span>}
                </div>
              </div>
            </div>
          );
        })}

        {query.length >= 2 && !loading && filteredResults.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            No concepts found for "{query}"
          </div>
        )}
      </div>
      )}

      {/* No results message for natural mode */}
      {searchMode === 'natural' && query.length >= 2 && !loading && naturalSearchResults.length === 0 && parsedQuery && (
        <div className="text-center text-gray-500 py-8">
          No verses found matching your concepts. Try different terms or use "and" / "or" connectors.
        </div>
      )}
    </div>
  );
}

export default ConceptSearchPanel;
