/**
 * Enhanced Story Graph Visualization Component
 *
 * A pedagogically-designed graph viewer for Quranic stories that supports:
 * - Chronological mode: Vertical timeline (top to bottom)
 * - Thematic mode: Conceptual clustering
 * - Memorization mode: Step-by-step progressive reveal
 *
 * Design Philosophy:
 * - Memorization-friendly: Clear visual hierarchy
 * - Self-explanatory: Human-readable labels, not just ayah ranges
 * - Non-overwhelming: Progressive disclosure on click
 *
 * Differences from generic knowledge graphs:
 * - Respects Quranic narrative structure (thematic grouping, cause-effect)
 * - Entry/exit points clearly marked
 * - Chronological edges have different visual treatment than thematic
 * - Designed for learning, not just exploration
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape, { NodeSingular } from 'cytoscape';
import { StoryGraphNode, StoryGraphEdge } from '../../lib/api';
import { translateTag as translateTagFromI18n, Language } from '../../i18n/translations';

// =============================================================================
// TYPES
// =============================================================================

type ViewMode = 'chronological' | 'thematic' | 'memorization';

// Generic graph interface that works with both StoryGraph and AtlasGraphResponse
interface GenericGraph {
  nodes: Array<{
    id: string;
    type: string;
    label: string;
    data: Record<string, unknown>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
    label?: string | null;
    data?: Record<string, unknown>;
  }>;
}

interface StoryGraphViewProps {
  graph: GenericGraph;
  language: 'ar' | 'en';
  onNodeClick?: (node: StoryGraphNode) => void;
  onEdgeClick?: (edge: StoryGraphEdge) => void;
  initialMode?: ViewMode;
}

// Node data interface for type safety
interface NodeData {
  verse_reference?: string;
  narrative_role?: string;
  chronological_index?: number;
  total_steps?: number;
  summary?: string;
  semantic_tags?: string[];
  memorization_cue?: string;
  is_entry_point?: boolean;
  [key: string]: unknown;
}

interface NodeDetailPanelProps {
  node: StoryGraphNode | null;
  language: 'ar' | 'en';
  onClose: () => void;
}

// =============================================================================
// NARRATIVE ROLE COLORS
// =============================================================================

const NARRATIVE_ROLE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  introduction: { bg: '#f0fdf4', border: '#22c55e', text: '#166534' },
  divine_mission: { bg: '#fefce8', border: '#eab308', text: '#854d0e' },
  journey_phase: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af' },
  encounter: { bg: '#fdf4ff', border: '#a855f7', text: '#6b21a8' },
  test_or_trial: { bg: '#fff7ed', border: '#f97316', text: '#9a3412' },
  moral_decision: { bg: '#fef2f2', border: '#ef4444', text: '#991b1b' },
  divine_intervention: { bg: '#fefce8', border: '#facc15', text: '#854d0e' },
  outcome: { bg: '#f0fdfa', border: '#14b8a6', text: '#115e59' },
  reflection: { bg: '#f5f3ff', border: '#8b5cf6', text: '#5b21b6' },
  default: { bg: '#f8fafc', border: '#94a3b8', text: '#475569' },
};

// Narrative role translations
const NARRATIVE_ROLE_TRANSLATIONS: Record<string, { ar: string; en: string }> = {
  introduction: { ar: 'مقدمة', en: 'Introduction' },
  divine_mission: { ar: 'المهمة الإلهية', en: 'Divine Mission' },
  journey_phase: { ar: 'مرحلة الرحلة', en: 'Journey Phase' },
  encounter: { ar: 'اللقاء', en: 'Encounter' },
  test_or_trial: { ar: 'اختبار', en: 'Test/Trial' },
  test: { ar: 'اختبار', en: 'Test' },
  trial: { ar: 'ابتلاء', en: 'Trial' },
  moral_decision: { ar: 'قرار أخلاقي', en: 'Moral Decision' },
  divine_intervention: { ar: 'التدخل الإلهي', en: 'Divine Intervention' },
  outcome: { ar: 'النتيجة', en: 'Outcome' },
  reflection: { ar: 'تأمل', en: 'Reflection' },
  development: { ar: 'تطور', en: 'Development' },
  climax: { ar: 'الذروة', en: 'Climax' },
  resolution: { ar: 'الحل', en: 'Resolution' },
  rising_action: { ar: 'تصاعد الأحداث', en: 'Rising Action' },
  background: { ar: 'خلفية', en: 'Background' },
  conclusion: { ar: 'الخاتمة', en: 'Conclusion' },
  setup: { ar: 'التمهيد', en: 'Setup' },
  falling_action: { ar: 'تراجع الأحداث', en: 'Falling Action' },
  // Additional narrative roles for new stories
  confrontation: { ar: 'المواجهة', en: 'Confrontation' },
  rejection: { ar: 'الرفض', en: 'Rejection' },
  dawah: { ar: 'الدعوة', en: 'Call to Faith' },
  exposure: { ar: 'الانكشاف', en: 'Exposure' },
  heroism: { ar: 'البطولة', en: 'Heroism' },
  escalation: { ar: 'التصعيد', en: 'Escalation' },
  steadfastness: { ar: 'الثبات', en: 'Steadfastness' },
  correction: { ar: 'التصحيح', en: 'Correction' },
  contrast: { ar: 'التناقض', en: 'Contrast' },
  lesson: { ar: 'الدرس', en: 'Lesson' },
  description: { ar: 'الوصف', en: 'Description' },
  default: { ar: 'عام', en: 'General' },
};

// Helper function to translate narrative role
function translateNarrativeRole(role: string, language: Language): string {
  const trans = NARRATIVE_ROLE_TRANSLATIONS[role] || NARRATIVE_ROLE_TRANSLATIONS.default;
  return trans[language];
}

const EDGE_TYPE_STYLES: Record<string, { color: string; style: 'solid' | 'dashed'; arrow: boolean }> = {
  chronological_next: { color: '#22c55e', style: 'solid', arrow: true },
  continuation: { color: '#22c55e', style: 'solid', arrow: true },
  cause_effect: { color: '#3b82f6', style: 'solid', arrow: true },
  consequence: { color: '#3b82f6', style: 'solid', arrow: true },
  thematic_link: { color: '#a855f7', style: 'dashed', arrow: false },
  parallel: { color: '#eab308', style: 'dashed', arrow: false },
  contrast: { color: '#ef4444', style: 'dashed', arrow: false },
  expansion: { color: '#8b5cf6', style: 'solid', arrow: true },
  contains: { color: '#cbd5e1', style: 'dashed', arrow: false },
};


// Minimum container dimensions to prevent layout collapse
const MIN_CONTAINER_WIDTH = 300;
const MIN_CONTAINER_HEIGHT = 400;

// Zoom constraints for fit-to-view
const MIN_ZOOM = 0.3;
const MAX_ZOOM = 2.0;
const FIT_PADDING = 80;

// Node sizing for better readability
const SEGMENT_NODE_WIDTH = 160;
const SEGMENT_NODE_HEIGHT = 80;
const STORY_NODE_SIZE = 120;
const LABEL_FONT_SIZE = '14px';
const LABEL_MAX_WIDTH = '140px';

// =============================================================================
// NODE DETAIL PANEL
// =============================================================================

function NodeDetailPanel({ node, language, onClose }: NodeDetailPanelProps) {
  if (!node) return null;

  const isArabic = language === 'ar';
  const data: NodeData = (node.data || {}) as NodeData;

  // Translate semantic tag using the universal translateTag helper

  return (
    <div
      className={`absolute top-4 ${isArabic ? 'left-4' : 'right-4'} w-80 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden z-10`}
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <div className="bg-sky-50 px-4 py-3 border-b border-sky-100">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-semibold text-sky-900 text-sm">{node.label}</h3>
            {data.verse_reference && (
              <span className="text-xs text-sky-700 font-mono">{data.verse_reference}</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
        {/* Narrative Role Badge */}
        {data.narrative_role && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">{isArabic ? 'الدور:' : 'Role:'}</span>
            <span
              className="px-2 py-0.5 rounded-full text-xs font-medium"
              style={{
                backgroundColor: NARRATIVE_ROLE_COLORS[data.narrative_role]?.bg || '#f8fafc',
                color: NARRATIVE_ROLE_COLORS[data.narrative_role]?.text || '#475569',
              }}
            >
              {translateNarrativeRole(data.narrative_role as string, language)}
            </span>
          </div>
        )}

        {/* Chronological Index */}
        {data.chronological_index && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">{isArabic ? 'الترتيب:' : 'Step:'}</span>
            <span className="text-sm font-semibold text-sky-700">
              {data.chronological_index} / {data.total_steps || '?'}
            </span>
          </div>
        )}

        {/* Summary */}
        {data.summary && (
          <div>
            <h4 className="text-xs font-medium text-gray-500 mb-1">
              {isArabic ? 'الملخص' : 'Summary'}
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed">{data.summary}</p>
          </div>
        )}

        {/* Semantic Tags */}
        {data.semantic_tags && data.semantic_tags.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-gray-500 mb-1">
              {isArabic ? 'المواضيع' : 'Themes'}
            </h4>
            <div className="flex flex-wrap gap-1">
              {(data.semantic_tags as string[]).map((tag: string, i: number) => {
                const { text: translatedTag, isMissing: needsTranslation } = translateTagFromI18n(tag, language);
                return (
                  <span
                    key={i}
                    className={`px-2 py-0.5 rounded text-xs ${needsTranslation ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'}`}
                    title={needsTranslation ? 'ترجمة عربية ناقصة' : undefined}
                  >
                    {translatedTag}
                    {needsTranslation && <span className="text-amber-500 mr-1">*</span>}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Memorization Cue */}
        {data.memorization_cue && (
          <div className="bg-amber-50 rounded-lg p-2 border border-amber-200">
            <h4 className="text-xs font-medium text-amber-700 mb-1">
              {isArabic ? 'للحفظ' : 'Remember'}
            </h4>
            <p className="text-sm text-amber-900 italic">{data.memorization_cue}</p>
          </div>
        )}

        {/* Entry Point Indicator */}
        {data.is_entry_point && (
          <div className="flex items-center gap-1 text-green-600 text-xs">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
            </svg>
            {isArabic ? 'نقطة البداية' : 'Entry Point'}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function StoryGraphView({
  graph,
  language,
  onNodeClick,
  onEdgeClick: _onEdgeClick,
  initialMode = 'chronological',
}: StoryGraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const layoutTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>(initialMode);
  const [selectedNode, setSelectedNode] = useState<StoryGraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<{ node: StoryGraphNode; x: number; y: number } | null>(null);
  const [memorizationStep, setMemorizationStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [containerReady, setContainerReady] = useState(false);

  const isArabic = language === 'ar';

  // Helper: Check if container has valid dimensions
  const isContainerValid = useCallback(() => {
    if (!containerRef.current) return false;
    const rect = containerRef.current.getBoundingClientRect();
    return rect.width >= MIN_CONTAINER_WIDTH && rect.height >= MIN_CONTAINER_HEIGHT;
  }, []);

  // Helper: Safe fit-to-view with zoom constraints
  const safeFitToView = useCallback(() => {
    if (!cyRef.current || !isContainerValid()) return;

    cyRef.current.fit(undefined, FIT_PADDING);

    // Clamp zoom level
    const currentZoom = cyRef.current.zoom();
    if (currentZoom < MIN_ZOOM) {
      cyRef.current.zoom(MIN_ZOOM);
      cyRef.current.center();
    } else if (currentZoom > MAX_ZOOM) {
      cyRef.current.zoom(MAX_ZOOM);
      cyRef.current.center();
    }
  }, [isContainerValid]);

  // Get maximum chronological index for memorization mode
  useEffect(() => {
    if (!graph?.nodes) return;
    const maxIndex = Math.max(
      ...graph.nodes
        .filter(n => n.type === 'segment')
        .map(n => (n.data.chronological_index as number) || 0)
    );
    setTotalSteps(maxIndex);
  }, [graph]);

  // Build Cytoscape stylesheet
  const buildStylesheet = useCallback(() => {
    const styles: cytoscape.StylesheetStyle[] = [
      // Story root node
      {
        selector: 'node[type="story"]',
        style: {
          'background-color': '#0ea5e9',
          label: 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          color: '#fff',
          'font-size': '18px',
          'font-weight': 'bold',
          width: STORY_NODE_SIZE,
          height: STORY_NODE_SIZE,
          shape: 'ellipse',
          'border-width': 4,
          'border-color': '#0284c7',
          'text-wrap': 'wrap',
          'text-max-width': '110px',
        },
      },
      // Entry point node
      {
        selector: 'node[?is_entry_point]',
        style: {
          'border-width': 5,
          'border-color': '#16a34a',
          'border-style': 'double',
        },
      },
      // Default segment node - larger with label inside
      {
        selector: 'node[type="segment"]',
        style: {
          'background-color': '#f8fafc',
          'border-color': '#94a3b8',
          'border-width': 3,
          label: 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          color: '#1e293b',
          'font-size': LABEL_FONT_SIZE,
          'font-weight': 600,
          'text-wrap': 'wrap',
          'text-max-width': LABEL_MAX_WIDTH,
          width: SEGMENT_NODE_WIDTH,
          height: SEGMENT_NODE_HEIGHT,
          shape: 'round-rectangle',
          'padding': '12px',
        },
      },
      // Show verse reference below segment nodes
      {
        selector: 'node[type="segment"][verse_reference]',
        style: {
          'text-valign': 'center',
          'text-halign': 'center',
        },
      },
      // Hidden nodes (for memorization mode)
      {
        selector: '.hidden-node',
        style: {
          opacity: 0.15,
        },
      },
      // Highlighted nodes
      {
        selector: '.highlighted',
        style: {
          'border-width': 4,
          'border-color': '#f59e0b',
          'background-color': '#fef3c7',
        },
      },
    ];

    // Add narrative role specific styles with stronger borders
    Object.entries(NARRATIVE_ROLE_COLORS).forEach(([role, colors]) => {
      styles.push({
        selector: `node[narrative_role="${role}"]`,
        style: {
          'background-color': colors.bg,
          'border-color': colors.border,
          'border-width': 3,
          color: colors.text,
        },
      });
    });

    // Add edge styles - thicker and more visible
    styles.push({
      selector: 'edge',
      style: {
        width: 3,
        'line-color': '#cbd5e1',
        'target-arrow-color': '#cbd5e1',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 1.2,
        'curve-style': 'bezier',
        'font-size': '11px',
        color: '#475569',
      },
    });

    // Hover state for nodes
    styles.push({
      selector: 'node:active',
      style: {
        'overlay-opacity': 0.1,
        'overlay-color': '#0ea5e9',
      },
    });

    // Add specific edge type styles
    Object.entries(EDGE_TYPE_STYLES).forEach(([type, styleConfig]) => {
      styles.push({
        selector: `edge[type="${type}"]`,
        style: {
          'line-color': styleConfig.color,
          'target-arrow-color': styleConfig.color,
          'line-style': styleConfig.style,
          'target-arrow-shape': styleConfig.arrow ? 'triangle' : 'none',
        },
      });
    });

    // Hidden edges
    styles.push({
      selector: '.hidden-edge',
      style: {
        opacity: 0.1,
      },
    });

    return styles;
  }, []);

  // Get layout based on mode
  const getLayout = useCallback((mode: ViewMode) => {
    const ySpacing = 140; // Increased vertical spacing for timeline
    const radius = 280; // Increased radius for radial layout

    if (mode === 'chronological') {
      // Vertical timeline layout
      return {
        name: 'preset',
        positions: (node: NodeSingular) => {
          const data = node.data();
          if (data.type === 'story') {
            return { x: 0, y: -100 }; // Story node above timeline
          }
          const index = data.chronological_index || data.narrative_order || 1;
          return {
            x: 0,
            y: index * ySpacing,
          };
        },
        animate: true,
        animationDuration: 500,
      };
    }

    if (mode === 'thematic') {
      // Radial layout with story at center
      return {
        name: 'preset',
        positions: (node: NodeSingular) => {
          const data = node.data();
          if (data.type === 'story') {
            return { x: 0, y: 0 }; // Story node at center
          }
          const index = data.chronological_index || data.narrative_order || 1;
          const total = totalSteps || 5;
          // Distribute segments in a circle around the story
          const angle = ((index - 1) / total) * 2 * Math.PI - Math.PI / 2;
          return {
            x: Math.cos(angle) * radius,
            y: Math.sin(angle) * radius,
          };
        },
        animate: true,
        animationDuration: 500,
      };
    }

    // Memorization mode - clean vertical timeline
    return {
      name: 'preset',
      positions: (node: NodeSingular) => {
        const data = node.data();
        if (data.type === 'story') {
          return { x: 0, y: -100 };
        }
        const index = data.chronological_index || data.narrative_order || 1;
        return { x: 0, y: index * ySpacing };
      },
      animate: true,
      animationDuration: 500,
    };
  }, [totalSteps]);

  // Set up ResizeObserver to detect container size changes
  useEffect(() => {
    if (!containerRef.current) return;

    const checkContainerAndInit = () => {
      if (isContainerValid()) {
        setContainerReady(true);
      }
    };

    // Initial check
    checkContainerAndInit();

    // Set up ResizeObserver for container size changes
    resizeObserverRef.current = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;

        // Check if container now has valid dimensions
        if (width >= MIN_CONTAINER_WIDTH && height >= MIN_CONTAINER_HEIGHT) {
          setContainerReady(true);

          // Debounced resize handling
          if (layoutTimeoutRef.current) {
            clearTimeout(layoutTimeoutRef.current);
          }
          layoutTimeoutRef.current = setTimeout(() => {
            if (cyRef.current) {
              cyRef.current.resize();
              safeFitToView();
            }
          }, 100);
        }
      }
    });

    resizeObserverRef.current.observe(containerRef.current);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      if (layoutTimeoutRef.current) {
        clearTimeout(layoutTimeoutRef.current);
      }
    };
  }, [isContainerValid, safeFitToView]);

  // Initialize Cytoscape only when container is ready
  useEffect(() => {
    if (!containerRef.current || !graph || !containerReady) return;

    // Guard: Don't initialize if container has invalid dimensions
    if (!isContainerValid()) {
      console.warn('StoryGraphView: Container dimensions invalid, delaying initialization');
      return;
    }

    // Convert graph data to Cytoscape format
    const elements = [
      // Nodes
      ...graph.nodes.map((node) => ({
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          narrative_role: node.data?.narrative_role,
          chronological_index: node.data?.chronological_index,
          is_entry_point: node.data?.is_entry_point,
          ...node.data,
          total_steps: totalSteps,
        },
      })),
      // Edges
      ...graph.edges.map((edge, i) => ({
        data: {
          id: `edge-${i}`,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          label: edge.label,
          is_chronological: edge.data?.is_chronological,
        },
      })),
    ];

    // Initialize Cytoscape
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: buildStylesheet(),
      layout: getLayout(viewMode),
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      wheelSensitivity: 0.3,
    });

    // Node click handler
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      const graphNode = graph.nodes.find(n => n.id === nodeData.id);

      if (graphNode) {
        // Enhance with total_steps for display
        const enhancedNode = {
          ...graphNode,
          data: {
            ...graphNode.data,
            total_steps: totalSteps,
          },
        };
        setSelectedNode(enhancedNode);
        onNodeClick?.(enhancedNode);

        // Highlight node
        cyRef.current?.elements().removeClass('highlighted');
        node.addClass('highlighted');
      }
    });

    // Background click to deselect
    cyRef.current.on('tap', (evt) => {
      if (evt.target === cyRef.current) {
        setSelectedNode(null);
        cyRef.current?.elements().removeClass('highlighted');
      }
    });

    // Add mouseover for hover tooltip
    cyRef.current.on('mouseover', 'node', (evt) => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'pointer';
      }
      const node = evt.target;
      const nodeData = node.data();
      const graphNode = graph.nodes.find(n => n.id === nodeData.id);
      if (graphNode && containerRef.current) {
        const pos = node.renderedPosition();
        setHoveredNode({
          node: graphNode,
          x: pos.x,
          y: pos.y - 60, // Position above node
        });
      }
    });

    cyRef.current.on('mouseout', 'node', () => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'default';
      }
      setHoveredNode(null);
    });

    // Auto-fit after layout animation completes
    cyRef.current.on('layoutstop', () => {
      // Small delay to ensure layout is settled
      setTimeout(() => {
        safeFitToView();
      }, 50);
    });

    // Initial fit after layout
    setTimeout(() => {
      safeFitToView();
    }, 700);

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [graph, buildStylesheet, getLayout, viewMode, onNodeClick, totalSteps, containerReady, isContainerValid, safeFitToView]);

  // Handle mode changes
  useEffect(() => {
    if (!cyRef.current) return;

    const layout = getLayout(viewMode);
    const layoutInstance = cyRef.current.layout(layout);

    // Listen for layout completion to fit view
    layoutInstance.one('layoutstop', () => {
      setTimeout(() => {
        safeFitToView();
      }, 50);
    });

    layoutInstance.run();

    // Apply memorization mode visibility
    if (viewMode === 'memorization') {
      cyRef.current.nodes().forEach((node) => {
        const index = node.data('chronological_index') || 0;
        if (index > memorizationStep) {
          node.addClass('hidden-node');
        } else {
          node.removeClass('hidden-node');
        }
      });

      cyRef.current.edges().forEach((edge) => {
        const sourceNode = cyRef.current?.getElementById(edge.data('source'));
        const targetNode = cyRef.current?.getElementById(edge.data('target'));
        const sourceIndex = sourceNode?.data('chronological_index') || 0;
        const targetIndex = targetNode?.data('chronological_index') || 0;

        if (sourceIndex > memorizationStep || targetIndex > memorizationStep) {
          edge.addClass('hidden-edge');
        } else {
          edge.removeClass('hidden-edge');
        }
      });
    } else {
      cyRef.current.elements().removeClass('hidden-node hidden-edge');
    }
  }, [viewMode, memorizationStep, getLayout, safeFitToView]);

  // Memorization controls
  const handleNextStep = () => {
    if (memorizationStep < totalSteps) {
      setMemorizationStep(memorizationStep + 1);
    }
  };

  const handlePrevStep = () => {
    if (memorizationStep > 0) {
      setMemorizationStep(memorizationStep - 1);
    }
  };

  const handleReset = () => {
    setMemorizationStep(0);
  };

  return (
    <div
      className="relative w-full h-full bg-gray-50 rounded-lg overflow-hidden"
      style={{ minHeight: `${MIN_CONTAINER_HEIGHT}px` }}
    >
      {/* Graph Container */}
      <div
        ref={containerRef}
        className="w-full h-full"
        style={{ minWidth: `${MIN_CONTAINER_WIDTH}px`, minHeight: `${MIN_CONTAINER_HEIGHT}px` }}
      />

      {/* Hover Tooltip */}
      {hoveredNode && !selectedNode && (
        <div
          className="absolute pointer-events-none bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg max-w-[200px] z-20"
          style={{
            left: hoveredNode.x,
            top: hoveredNode.y,
            transform: 'translate(-50%, -100%)',
          }}
          dir={isArabic ? 'rtl' : 'ltr'}
        >
          <div className="font-medium truncate">{hoveredNode.node.label}</div>
          {hoveredNode.node.data?.verse_reference ? (
            <div className="text-gray-300 text-[10px] mt-0.5">
              {String(hoveredNode.node.data.verse_reference)}
            </div>
          ) : null}
          {hoveredNode.node.data?.narrative_role ? (
            <div className="text-sky-300 text-[10px] mt-0.5">
              {translateNarrativeRole(String(hoveredNode.node.data.narrative_role), language)}
            </div>
          ) : null}
          <div className="text-gray-400 text-[10px] mt-1">
            {isArabic ? 'انقر للتفاصيل' : 'Click for details'}
          </div>
        </div>
      )}

      {/* Node Detail Panel */}
      <NodeDetailPanel
        node={selectedNode}
        language={language}
        onClose={() => {
          setSelectedNode(null);
          cyRef.current?.elements().removeClass('highlighted');
        }}
      />

      {/* Mode Switcher */}
      <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md p-1 flex gap-1 z-10">
        {(['chronological', 'thematic', 'memorization'] as ViewMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => {
              setViewMode(mode);
              if (mode === 'memorization') {
                setMemorizationStep(1);
              }
            }}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              viewMode === mode
                ? 'bg-sky-500 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {mode === 'chronological' && (isArabic ? 'زمني' : 'Timeline')}
            {mode === 'thematic' && (isArabic ? 'مواضيع' : 'Thematic')}
            {mode === 'memorization' && (isArabic ? 'حفظ' : 'Learn')}
          </button>
        ))}
      </div>

      {/* Memorization Controls */}
      {viewMode === 'memorization' && (
        <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md p-3 z-10">
          <div className="text-xs text-gray-500 mb-2 text-center">
            {isArabic ? 'الخطوة' : 'Step'} {memorizationStep} / {totalSteps}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="p-1.5 text-gray-500 hover:bg-gray-100 rounded"
              title={isArabic ? 'إعادة' : 'Reset'}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button
              onClick={handlePrevStep}
              disabled={memorizationStep <= 0}
              className="p-1.5 text-gray-500 hover:bg-gray-100 rounded disabled:opacity-30"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={handleNextStep}
              disabled={memorizationStep >= totalSteps}
              className="p-1.5 bg-sky-500 text-white rounded hover:bg-sky-600 disabled:opacity-30"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Legend */}
      <div
        className={`absolute bottom-4 ${isArabic ? 'right-4' : 'left-4'} bg-white rounded-lg shadow-md p-3 text-xs z-10`}
        dir={isArabic ? 'rtl' : 'ltr'}
      >
        <div className="font-medium mb-2 text-gray-700">
          {isArabic ? 'مفتاح الألوان' : 'Legend'}
        </div>

        {/* Edge Types */}
        <div className="space-y-1.5 mb-3">
          <div className="text-[10px] text-gray-500 uppercase tracking-wide">
            {isArabic ? 'الروابط' : 'Edges'}
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-green-500" />
            <span>{isArabic ? 'تسلسل زمني' : 'Chronological'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-blue-500" />
            <span>{isArabic ? 'سبب ونتيجة' : 'Cause-Effect'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-purple-500 border-dashed border-t" />
            <span>{isArabic ? 'رابط موضوعي' : 'Thematic'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-yellow-500 border-dashed border-t" />
            <span>{isArabic ? 'تشابه' : 'Parallel'}</span>
          </div>
        </div>

        {/* Node Roles */}
        <div className="space-y-1.5">
          <div className="text-[10px] text-gray-500 uppercase tracking-wide">
            {isArabic ? 'الأدوار' : 'Roles'}
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded border-2 bg-green-50 border-green-500" />
            <span>{isArabic ? 'مقدمة' : 'Introduction'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded border-2 bg-orange-50 border-orange-500" />
            <span>{isArabic ? 'اختبار' : 'Test'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded border-2 bg-purple-50 border-purple-500" />
            <span>{isArabic ? 'تأمل' : 'Reflection'}</span>
          </div>
        </div>
      </div>

      {/* Zoom controls */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-1 z-10">
        <button
          onClick={() => {
            const cy = cyRef.current;
            if (cy) cy.zoom(cy.zoom() * 1.3);
          }}
          className="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50"
          title={isArabic ? 'تكبير' : 'Zoom in'}
        >
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m6-6H6" />
          </svg>
        </button>
        <button
          onClick={() => {
            const cy = cyRef.current;
            if (cy) cy.zoom(cy.zoom() * 0.7);
          }}
          className="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50"
          title={isArabic ? 'تصغير' : 'Zoom out'}
        >
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" />
          </svg>
        </button>
        <button
          onClick={() => safeFitToView()}
          className="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50"
          title={isArabic ? 'ملاءمة الشاشة' : 'Fit to view'}
        >
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </button>
        <button
          onClick={() => cyRef.current?.center()}
          className="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50"
          title={isArabic ? 'وسط' : 'Center'}
        >
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="3" strokeWidth={2} />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2v4m0 12v4m10-10h-4M6 12H2" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default StoryGraphView;
