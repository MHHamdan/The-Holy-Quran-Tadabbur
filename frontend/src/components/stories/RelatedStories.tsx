/**
 * Related Stories Component
 *
 * Shows stories connected to the current story via:
 * - Shared themes
 * - Shared figures
 * - Narrative continuation
 *
 * Inspired by Connected Papers - shows semantic similarity between stories.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Network, ArrowRight, Users, Tag } from 'lucide-react';
import { storiesApi, CrossStoryConnection, Story } from '../../lib/api';
import { Language, translateTheme, translateFigure } from '../../i18n/translations';

interface RelatedStoriesProps {
  storyId: string;
  storyName: string;
  language: Language;
}

// Connection type translations
const CONNECTION_TYPE_TRANSLATIONS: Record<string, { ar: string; en: string }> = {
  continuation: { ar: 'استمرار', en: 'Continuation' },
  thematic: { ar: 'موضوعي', en: 'Thematic' },
  shared_figure: { ar: 'شخصية مشتركة', en: 'Shared Figure' },
  shared_theme: { ar: 'موضوع مشترك', en: 'Shared Theme' },
  prophetic_chain: { ar: 'سلسلة الأنبياء', en: 'Prophetic Chain' },
  parallel: { ar: 'متوازي', en: 'Parallel' },
};

function translateConnectionType(type: string, language: Language): string {
  const trans = CONNECTION_TYPE_TRANSLATIONS[type];
  if (trans) return trans[language];
  // Fallback: show type as-is, but mark as untranslated in Arabic mode
  const formatted = type.replace(/_/g, ' ');
  return language === 'ar' ? `[${formatted}]` : formatted;
}

export function RelatedStories({ storyId, storyName, language }: RelatedStoriesProps) {
  const [connections, setConnections] = useState<CrossStoryConnection[]>([]);
  const [relatedStories, setRelatedStories] = useState<Map<string, Story>>(new Map());
  const [loading, setLoading] = useState(true);

  const isArabic = language === 'ar';

  useEffect(() => {
    loadRelatedStories();
  }, [storyId]);

  async function loadRelatedStories() {
    setLoading(true);
    try {
      // Get cross-connections
      const connectionsRes = await storiesApi.getCrossConnections(storyId);
      setConnections(connectionsRes.data);

      // Get unique related story IDs (exclude the current story)
      const relatedIds = new Set<string>();
      connectionsRes.data.forEach(conn => {
        if (conn.source_story_id !== storyId) relatedIds.add(conn.source_story_id);
        if (conn.target_story_id !== storyId) relatedIds.add(conn.target_story_id);
      });

      // Fetch story details for related stories
      const storyMap = new Map<string, Story>();
      const storyPromises = Array.from(relatedIds).map(async (id) => {
        try {
          const res = await storiesApi.getStory(id);
          storyMap.set(id, res.data);
        } catch (e) {
          console.error(`Failed to load story ${id}:`, e);
        }
      });
      await Promise.all(storyPromises);
      setRelatedStories(storyMap);
    } catch (error) {
      console.error('Failed to load related stories:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Network className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold">
            {isArabic ? 'قصص متصلة' : 'Related Stories'}
          </h3>
        </div>
        <div className="flex justify-center py-6">
          <div className="animate-spin w-6 h-6 border-3 border-primary-600 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  if (connections.length === 0) {
    return null; // Don't show section if no connections
  }

  // Group connections by related story
  const storyConnections = new Map<string, CrossStoryConnection[]>();
  connections.forEach(conn => {
    const relatedId = conn.source_story_id === storyId
      ? conn.target_story_id
      : conn.source_story_id;

    if (!storyConnections.has(relatedId)) {
      storyConnections.set(relatedId, []);
    }
    storyConnections.get(relatedId)!.push(conn);
  });

  // Sort by strongest connection
  const sortedStories = Array.from(storyConnections.entries()).sort((a, b) => {
    const maxA = Math.max(...a[1].map(c => c.strength));
    const maxB = Math.max(...b[1].map(c => c.strength));
    return maxB - maxA;
  });

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Network className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold">
          {isArabic ? 'قصص متصلة' : 'Related Stories'}
        </h3>
        <span className="text-sm text-gray-500">
          ({sortedStories.length})
        </span>
      </div>

      <p className="text-sm text-gray-500 mb-4">
        {isArabic
          ? `قصص مرتبطة بـ "${storyName}" من خلال المواضيع أو الشخصيات المشتركة`
          : `Stories connected to "${storyName}" through shared themes or figures`}
      </p>

      <div className="space-y-3">
        {sortedStories.map(([relatedStoryId, conns]) => {
          const story = relatedStories.get(relatedStoryId);
          if (!story) return null;

          const storyLabel = isArabic ? story.name_ar : story.name_en;
          const strongestConn = conns.reduce((a, b) =>
            a.strength > b.strength ? a : b
          );

          // Gather all shared themes and figures
          const allThemes = new Set<string>();
          const allFigures = new Set<string>();
          conns.forEach(conn => {
            conn.shared_themes?.forEach(t => allThemes.add(t));
            conn.shared_figures?.forEach(f => allFigures.add(f));
          });

          return (
            <Link
              key={relatedStoryId}
              to={`/stories/${relatedStoryId}`}
              className="block p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50/50 transition-all group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-gray-900 group-hover:text-primary-700">
                      {storyLabel}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        strongestConn.connection_type === 'continuation'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-purple-100 text-purple-700'
                      }`}
                    >
                      {translateConnectionType(strongestConn.connection_type, language)}
                    </span>
                  </div>

                  {/* Connection explanation */}
                  {(isArabic ? strongestConn.label_ar : strongestConn.label_en) && (
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {isArabic ? strongestConn.label_ar : strongestConn.label_en}
                    </p>
                  )}

                  {/* Shared themes */}
                  {allThemes.size > 0 && (
                    <div className="flex items-center gap-1 mb-1">
                      <Tag className="w-3 h-3 text-gray-400" />
                      <div className="flex flex-wrap gap-1">
                        {Array.from(allThemes).slice(0, 3).map(theme => (
                          <span
                            key={theme}
                            className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded"
                          >
                            {translateTheme(theme, language)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Shared figures */}
                  {allFigures.size > 0 && (
                    <div className="flex items-center gap-1">
                      <Users className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {Array.from(allFigures).slice(0, 3).map(f => translateFigure(f, language)).join(isArabic ? '، ' : ', ')}
                      </span>
                    </div>
                  )}
                </div>

                <ArrowRight className={`w-5 h-5 text-gray-400 group-hover:text-primary-600 flex-shrink-0 ${
                  isArabic ? 'rotate-180' : ''
                }`} />
              </div>

              {/* Strength indicator */}
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full transition-all"
                    style={{ width: `${strongestConn.strength * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-400">
                  {Math.round(strongestConn.strength * 100)}%
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      {/* View all connections link */}
      <div className="mt-4 pt-4 border-t border-gray-100 text-center">
        <span className="text-sm text-gray-500">
          {isArabic
            ? 'استكشف المزيد من الروابط في أطلس القصص'
            : 'Explore more connections in Story Atlas'}
        </span>
      </div>
    </div>
  );
}

export default RelatedStories;
