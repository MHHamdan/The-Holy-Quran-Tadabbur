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
import { Network, ArrowRight, Users, Tag, BookOpen } from 'lucide-react';
import { storiesApi, CrossStoryConnection, Story } from '../../lib/api';
import { Language, translateTheme, translateFigure } from '../../i18n/translations';
import { ProvenanceLabel } from '../common/ProvenanceLabel';

/** API also returns the verse refs the connection cites ("S:A-B"). */
type ConnectionWithRefs = CrossStoryConnection & { verse_refs?: string[] };

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
  return language === 'ar' ? 'صلة' : 'Related';
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

  // Keep the API order; strength is a seeded constant (0.6/0.8), not a
  // measured score, so it is neither shown nor used for ranking.
  const sortedStories = Array.from(storyConnections.entries());

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <Network className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold">
          {isArabic ? 'قصص متصلة' : 'Related Stories'}
        </h3>
        <span className="text-sm text-gray-500">
          ({sortedStories.length})
        </span>
        <ProvenanceLabel kind="analytical" status="needs_review" language={language} />
      </div>

      <p className="text-sm text-gray-500 mb-4">
        {isArabic
          ? `قصص مرتبطة بـ "${storyName}" من خلال المواضيع أو الشخصيات المشتركة. هذه الروابط اقتراحات للتأمل وليست تفسيرًا.`
          : `Stories connected to "${storyName}" through shared themes or figures. These links are suggestions for reflection, not tafsir.`}
      </p>

      <div className="space-y-3">
        {sortedStories.map(([relatedStoryId, conns]) => {
          const story = relatedStories.get(relatedStoryId);
          if (!story) return null;

          const storyLabel = isArabic ? story.name_ar : story.name_en;
          const primary = conns[0];

          // Gather all shared themes, figures and cited verse references
          const allThemes = new Set<string>();
          const allFigures = new Set<string>();
          const verseRefs = new Set<string>();
          conns.forEach(conn => {
            conn.shared_themes?.forEach(t => allThemes.add(t));
            conn.shared_figures?.forEach(f => allFigures.add(f));
            (conn as ConnectionWithRefs).verse_refs?.forEach(r => verseRefs.add(r));
          });
          const label = isArabic ? primary.label_ar : primary.label_en;

          return (
            <div
              key={relatedStoryId}
              className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <Link
                      to={`/stories/${relatedStoryId}`}
                      className="font-semibold text-gray-900 hover:text-primary-700"
                    >
                      {storyLabel}
                    </Link>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        primary.connection_type === 'continuation'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-purple-100 text-purple-700'
                      }`}
                    >
                      {translateConnectionType(primary.connection_type, language)}
                    </span>
                  </div>

                  {/* Connection explanation */}
                  {label && (
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2" dir={isArabic ? 'rtl' : 'ltr'}>
                      {label}
                    </p>
                  )}

                  {/* Cited verses */}
                  {verseRefs.size > 0 && (
                    <div className="flex flex-wrap items-center gap-1 mb-1">
                      <BookOpen className="w-3 h-3 text-gray-400" />
                      {Array.from(verseRefs).map((ref) => {
                        const [s, range] = ref.split(':');
                        const a = (range || '').split('-')[0];
                        return (
                          <Link
                            key={ref}
                            to={`/quran/${s}?aya=${a}`}
                            className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full hover:bg-primary-100"
                            dir="ltr"
                          >
                            {ref}
                          </Link>
                        );
                      })}
                    </div>
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

                <Link to={`/stories/${relatedStoryId}`} aria-label={storyLabel}>
                  <ArrowRight className={`w-5 h-5 text-gray-400 hover:text-primary-600 flex-shrink-0 ${
                    isArabic ? 'rotate-180' : ''
                  }`} />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default RelatedStories;
