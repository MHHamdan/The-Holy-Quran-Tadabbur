"""
Knowledge Graph API Routes.

Endpoints for:
- Story cluster and event queries
- Graph visualization data
- Hybrid search
- Debug/trace endpoints

SECURITY:
- Admin endpoints (init-schema, import-stories) require X-Admin-Token header
- Rate limiting should be configured at reverse proxy level
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Depends

from app.kg.client import get_kg_client

# Admin token from environment (default for dev only)
ADMIN_TOKEN = os.environ.get("KG_ADMIN_TOKEN", "tadabbur-admin-dev-token")


def verify_admin_token(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """
    Verify admin token for protected endpoints.

    Required header: X-Admin-Token
    """
    if not x_admin_token:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "missing_admin_token",
                "message_ar": "مطلوب رمز المسؤول",
                "message_en": "Admin token required. Set X-Admin-Token header.",
            },
        )
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "invalid_admin_token",
                "message_ar": "رمز المسؤول غير صالح",
                "message_en": "Invalid admin token",
            },
        )
    return True
from app.kg.bridge import get_vector_graph_bridge, GraphExpansionConfig
from app.kg.models import (
    GraphNode,
    GraphEdge,
    StoryGraphResponse,
    TimelineEvent,
    TimelineResponse,
    VectorHit,
    HybridRetrievalResult,
)

router = APIRouter()


# =============================================================================
# STORY LIST ENDPOINTS
# =============================================================================

@router.get("/stories", response_model=dict)
async def list_stories(
    category: str = Query(None, description="Filter by category (prophet, nation, parable, historical, unseen, named_char)"),
    sura: int = Query(None, ge=1, le=114, description="Filter by surah"),
    lang: str = Query("ar", pattern="^(ar|en)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List all stories with optional filtering.

    Returns story clusters with basic metadata.
    """
    kg = get_kg_client()

    # Build WHERE clause
    where_parts = []
    if category:
        where_parts.append(f"category = '{category}'")
    if sura:
        where_parts.append(f"{sura} IN suras_mentioned")

    where_clause = " AND ".join(where_parts) if where_parts else None

    stories = await kg.select(
        "story_cluster",
        where=where_clause,
        order_by="title_ar",
        limit=limit,
        offset=offset,
    )

    def localize(obj: dict, field_base: str) -> str:
        ar_field = f"{field_base}_ar"
        en_field = f"{field_base}_en"
        if lang == "ar":
            return obj.get(ar_field) or obj.get(en_field) or ""
        return obj.get(en_field) or obj.get(ar_field) or ""

    return {
        "stories": [
            {
                "id": s.get("id"),
                "slug": s.get("slug"),
                "title": localize(s, "title"),
                "category": s.get("category"),
                "total_verses": s.get("total_verses"),
                "suras_mentioned": s.get("suras_mentioned", []),
                "event_count": s.get("event_count", 0),
                "is_complete": s.get("is_complete", False),
            }
            for s in stories
        ],
        "total": len(stories),
        "limit": limit,
        "offset": offset,
        "filters": {
            "category": category,
            "sura": sura,
        },
    }


@router.get("/sura/{sura_no}/stories", response_model=dict)
async def get_stories_by_sura(
    sura_no: int,
    lang: str = Query("ar", pattern="^(ar|en)$"),
):
    """
    Get all stories that mention a specific surah.

    Returns stories with their ayah spans in that surah.
    """
    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail={
            "error_code": "invalid_sura",
            "message_ar": "رقم السورة غير صالح",
            "message_en": "Invalid surah number",
        })

    kg = get_kg_client()

    # Find stories mentioning this sura
    stories = await kg.select(
        "story_cluster",
        where=f"{sura_no} IN suras_mentioned",
        order_by="title_ar",
    )

    def localize(obj: dict, field_base: str) -> str:
        ar_field = f"{field_base}_ar"
        en_field = f"{field_base}_en"
        if lang == "ar":
            return obj.get(ar_field) or obj.get(en_field) or ""
        return obj.get(en_field) or obj.get(ar_field) or ""

    # For each story, get events in this sura
    result_stories = []
    for s in stories:
        # Filter ayah_spans for this sura
        spans_in_sura = [
            span for span in s.get("ayah_spans", [])
            if span.get("sura") == sura_no
        ]

        # Get events in this sura
        cluster_id = s.get("id")
        events = await kg.select(
            "story_event",
            where=f"cluster_id = {cluster_id} AND sura_no = {sura_no}",
            order_by="chronological_index",
        )

        result_stories.append({
            "id": s.get("id"),
            "slug": s.get("slug"),
            "title": localize(s, "title"),
            "category": s.get("category"),
            "ayah_spans_in_sura": spans_in_sura,
            "events_in_sura": [
                {
                    "id": e.get("id"),
                    "title": localize(e, "title"),
                    "verse_reference": e.get("verse_reference"),
                    "chronological_index": e.get("chronological_index"),
                }
                for e in events
            ],
        })

    return {
        "sura_no": sura_no,
        "story_count": len(result_stories),
        "stories": result_stories,
    }


# =============================================================================
# STORY DETAIL ENDPOINTS
# =============================================================================

@router.get("/story/{cluster_id}", response_model=dict)
async def get_story_cluster(
    cluster_id: str,
    lang: str = Query("ar", pattern="^(ar|en)$"),
):
    """
    Get story cluster with events and timeline.

    Returns cluster metadata, events ordered chronologically,
    and NEXT edge relationships.
    """
    kg = get_kg_client()

    # Get cluster
    full_id = f"story_cluster:{cluster_id}" if ":" not in cluster_id else cluster_id
    cluster = await kg.get(full_id)

    if not cluster:
        raise HTTPException(status_code=404, detail={
            "error_code": "cluster_not_found",
            "message_ar": "لم يتم العثور على القصة",
            "message_en": "Story cluster not found",
        })

    # Get events
    events = await kg.select(
        "story_event",
        where=f'cluster_id = {full_id}',
        order_by="chronological_index",
    )

    # Get NEXT edges
    event_ids = [e.get("id") for e in events if e.get("id")]
    next_edges = []
    if event_ids:
        for event_id in event_ids:
            edges = await kg.get_edges(from_id=event_id, edge_type="next")
            next_edges.extend(edges)

    # Localize output based on language
    def localize(obj: dict, field_base: str) -> str:
        ar_field = f"{field_base}_ar"
        en_field = f"{field_base}_en"
        if lang == "ar":
            return obj.get(ar_field) or obj.get(en_field) or ""
        return obj.get(en_field) or obj.get(ar_field) or ""

    return {
        "cluster": {
            "id": cluster.get("id"),
            "slug": cluster.get("slug"),
            "title": localize(cluster, "title"),
            "short_title": localize(cluster, "short_title"),
            "category": cluster.get("category"),
            "era": cluster.get("era"),
            "main_persons": cluster.get("main_persons", []),
            "summary": localize(cluster, "summary"),
            "lessons": cluster.get(f"lessons_{lang}") or cluster.get("lessons_ar") or [],
            "ayah_spans": cluster.get("ayah_spans", []),
            "total_verses": cluster.get("total_verses"),
            "is_complete": cluster.get("is_complete", False),
            "event_count": len(events),
        },
        "events": [
            {
                "id": e.get("id"),
                "index": e.get("chronological_index"),
                "title": localize(e, "title"),
                "narrative_role": e.get("narrative_role"),
                "verse_reference": e.get("verse_reference"),
                "summary": localize(e, "summary"),
                "memorization_cue": localize(e, "memorization_cue"),
                "semantic_tags": e.get("semantic_tags", []),
                "is_entry_point": e.get("is_entry_point", False),
            }
            for e in events
        ],
        "timeline": [
            {
                "source": edge.get("in"),
                "target": edge.get("out"),
                "gap_type": edge.get("gap_type"),
            }
            for edge in next_edges
        ],
    }


@router.get("/story/{cluster_id}/graph", response_model=StoryGraphResponse)
async def get_story_graph(
    cluster_id: str,
    mode: str = Query("timeline", pattern="^(timeline|concept)$"),
    lang: str = Query("ar", pattern="^(ar|en)$"),
):
    """
    Get story as graph nodes and edges for visualization.

    Modes:
    - timeline: Chronological layout with NEXT edges
    - concept: Include thematic links for concept clustering
    """
    kg = get_kg_client()

    full_id = f"story_cluster:{cluster_id}" if ":" not in cluster_id else cluster_id

    # Get events
    events = await kg.select(
        "story_event",
        where=f'cluster_id = {full_id}',
        order_by="chronological_index",
    )

    if not events:
        raise HTTPException(status_code=404, detail={
            "error_code": "no_events",
            "message_ar": "لا توجد أحداث في هذه القصة",
            "message_en": "No events found in this story",
        })

    # Build nodes
    nodes: List[GraphNode] = []
    entry_node_id = None

    for i, event in enumerate(events):
        event_id = event.get("id", "")

        # Localize
        title = event.get(f"title_{lang}") or event.get("title_ar") or event.get("title_en") or ""
        summary = event.get(f"summary_{lang}") or event.get("summary_ar") or ""

        # Position for timeline layout
        position = None
        if mode == "timeline":
            chrono_idx = event.get("chronological_index", i + 1)
            position = {"x": 0, "y": chrono_idx * 120}

        node = GraphNode(
            id=event_id,
            type="event",
            label=title,
            data={
                "chronological_index": event.get("chronological_index"),
                "narrative_role": event.get("narrative_role"),
                "verse_reference": event.get("verse_reference"),
                "summary": summary,
                "semantic_tags": event.get("semantic_tags", []),
                "is_entry_point": event.get("is_entry_point", False),
            },
            position=position,
        )
        nodes.append(node)

        if event.get("is_entry_point") and not entry_node_id:
            entry_node_id = event_id

    if not entry_node_id and nodes:
        entry_node_id = nodes[0].id

    # Build edges
    edges: List[GraphEdge] = []
    event_ids = [n.id for n in nodes]

    # NEXT edges (chronological)
    for event_id in event_ids:
        next_edges = await kg.get_edges(from_id=event_id, edge_type="next")
        for edge in next_edges:
            target = edge.get("out")
            if target in event_ids:
                edges.append(GraphEdge(
                    source=event_id,
                    target=target,
                    type="next",
                    label=edge.get("gap_type"),
                    data={"is_chronological": True},
                ))

    # Thematic links (for concept mode)
    if mode == "concept":
        for event_id in event_ids:
            thematic_edges = await kg.get_edges(from_id=event_id, edge_type="thematic_link")
            for edge in thematic_edges:
                target = edge.get("out")
                if target in event_ids:
                    reason = edge.get(f"reason_{lang}") or edge.get("reason") or ""
                    edges.append(GraphEdge(
                        source=event_id,
                        target=target,
                        type="thematic_link",
                        label=reason[:50] if reason else None,
                        data={
                            "is_chronological": False,
                            "strength": edge.get("strength", 0.5),
                            "confidence": edge.get("confidence", 0.5),
                        },
                    ))

    # Check for DAG validity (no cycles in NEXT)
    is_valid_dag = True
    # Simple cycle detection via DFS
    visited = set()
    rec_stack = set()

    def has_cycle(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)
        for edge in edges:
            if edge.source == node_id and edge.type == "next":
                if edge.target not in visited:
                    if has_cycle(edge.target):
                        return True
                elif edge.target in rec_stack:
                    return True
        rec_stack.discard(node_id)
        return False

    for node in nodes:
        if node.id not in visited:
            if has_cycle(node.id):
                is_valid_dag = False
                break

    return StoryGraphResponse(
        cluster_id=cluster_id,
        nodes=nodes,
        edges=edges,
        entry_node_id=entry_node_id,
        is_valid_dag=is_valid_dag,
        layout_mode=mode,
    )


@router.get("/story/{cluster_id}/timeline", response_model=TimelineResponse)
async def get_story_timeline(
    cluster_id: str,
    lang: str = Query("ar", pattern="^(ar|en)$"),
):
    """
    Get linear timeline of story events.

    Returns events in chronological order with localized labels.
    """
    kg = get_kg_client()

    full_id = f"story_cluster:{cluster_id}" if ":" not in cluster_id else cluster_id

    # Get cluster for title
    cluster = await kg.get(full_id)
    if not cluster:
        raise HTTPException(status_code=404, detail={
            "error_code": "cluster_not_found",
            "message_ar": "لم يتم العثور على القصة",
            "message_en": "Story cluster not found",
        })

    # Get events
    events = await kg.select(
        "story_event",
        where=f'cluster_id = {full_id}',
        order_by="chronological_index",
    )

    timeline_events = [
        TimelineEvent(
            id=e.get("id", ""),
            index=e.get("chronological_index", 0),
            title_ar=e.get("title_ar", ""),
            title_en=e.get("title_en", ""),
            verse_reference=e.get("verse_reference", ""),
            narrative_role=e.get("narrative_role", ""),
            summary_ar=e.get("summary_ar", ""),
            summary_en=e.get("summary_en", ""),
            semantic_tags=e.get("semantic_tags", []),
            is_entry_point=e.get("is_entry_point", False),
            memorization_cue_ar=e.get("memorization_cue_ar"),
            memorization_cue_en=e.get("memorization_cue_en"),
        )
        for e in events
    ]

    return TimelineResponse(
        cluster_id=cluster_id,
        title_ar=cluster.get("title_ar", ""),
        title_en=cluster.get("title_en", ""),
        events=timeline_events,
    )


# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================

@router.get("/search")
async def hybrid_search(
    q: str = Query(..., min_length=1, description="Search query"),
    lang: str = Query("ar", pattern="^(ar|en)$"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Hybrid search across clusters, events, persons, and ayahs.

    Returns suggestions from multiple entity types.
    """
    kg = get_kg_client()
    results = {
        "clusters": [],
        "events": [],
        "persons": [],
        "concepts": [],
    }

    # Search clusters
    title_field = "title_ar" if lang == "ar" else "title_en"
    clusters = await kg.query(
        f"SELECT * FROM story_cluster WHERE {title_field} CONTAINS $q LIMIT {limit};",
    )
    # Note: SurrealDB string search - in production use full-text search
    results["clusters"] = clusters[:limit]

    # Search events
    events = await kg.query(
        f"SELECT * FROM story_event WHERE {title_field} CONTAINS $q OR summary_{lang} CONTAINS $q LIMIT {limit};",
    )
    results["events"] = events[:limit]

    # Search persons
    name_field = "name_ar" if lang == "ar" else "name_en"
    persons = await kg.query(
        f"SELECT * FROM person WHERE {name_field} CONTAINS $q LIMIT {limit};",
    )
    results["persons"] = persons[:limit]

    # Search concept tags
    label_field = "label_ar" if lang == "ar" else "label_en"
    concepts = await kg.query(
        f"SELECT * FROM concept_tag WHERE {label_field} CONTAINS $q LIMIT {limit};",
    )
    results["concepts"] = concepts[:limit]

    return results


# =============================================================================
# DEBUG ENDPOINTS
# =============================================================================

@router.get("/debug/evidence")
async def debug_evidence(
    request_id: str = Query(None, description="Request ID from RAG response"),
    chunk_ids: str = Query(None, description="Comma-separated chunk IDs"),
):
    """
    Debug endpoint showing full evidence trace.

    Returns:
    - Vector hits
    - Graph traversal paths
    - Filters applied
    - Final evidence chosen

    For troubleshooting RAG responses.
    """
    if not chunk_ids and not request_id:
        raise HTTPException(
            status_code=400,
            detail="Provide either request_id or chunk_ids",
        )

    bridge = get_vector_graph_bridge()

    if chunk_ids:
        # Parse comma-separated chunk IDs
        ids = [cid.strip() for cid in chunk_ids.split(",")]

        # Create mock vector hits
        vector_hits = [
            VectorHit(chunk_id=cid, score=1.0, rank=i + 1)
            for i, cid in enumerate(ids)
        ]

        # Run hybrid retrieval
        result = await bridge.hybrid_retrieve(
            vector_hits,
            config=GraphExpansionConfig(
                include_thematic_links=True,
                include_persons=True,
                include_places=True,
            ),
        )

        return {
            "input_chunk_ids": ids,
            "vector_hits": [h.model_dump() for h in result.vector_hits],
            "graph_expanded_ids": result.graph_expanded_ids,
            "evidence_count": len(result.final_evidence),
            "evidence": [e.model_dump() for e in result.final_evidence],
            "debug_info": result.debug_info,
        }

    # TODO: Implement request_id lookup from audit log
    return {"error": "request_id lookup not yet implemented"}


@router.get("/health")
async def kg_health():
    """
    Check Knowledge Graph health.

    Returns SurrealDB availability and schema version.
    """
    kg = get_kg_client()
    health = await kg.health_check()

    return {
        "status": health.get("status"),
        "surreal_host": health.get("host"),
        "surreal_port": health.get("port"),
        "namespace": health.get("namespace"),
        "database": health.get("database"),
        "message_ar": "قاعدة المعرفة متاحة" if health.get("status") == "ok" else "قاعدة المعرفة غير متاحة",
        "message_en": "Knowledge Graph available" if health.get("status") == "ok" else "Knowledge Graph unavailable",
    }


@router.post("/init-schema")
async def init_kg_schema(_: bool = Depends(verify_admin_token)):
    """
    Initialize Knowledge Graph schema.

    Creates all tables, indexes, and constraints.
    Should be called once during setup.

    PROTECTED: Requires X-Admin-Token header.
    """
    kg = get_kg_client()

    try:
        await kg.init_schema()
        return {
            "status": "ok",
            "message_ar": "تم تهيئة مخطط قاعدة المعرفة بنجاح",
            "message_en": "Knowledge Graph schema initialized successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "schema_init_failed",
                "message_ar": "فشل تهيئة مخطط قاعدة المعرفة",
                "message_en": f"Schema initialization failed: {str(e)}",
            },
        )


@router.post("/import-stories")
async def import_stories(_: bool = Depends(verify_admin_token)):
    """
    Import verified story registry to Knowledge Graph.

    Reads from data/manifests/stories.json and imports all stories,
    events, persons, and edges to SurrealDB.

    Idempotent: Safe to run multiple times.

    PROTECTED: Requires X-Admin-Token header.
    """
    from app.kg.story_importer import StoryImporter

    try:
        importer = StoryImporter()
        metrics = await importer.import_all()

        return {
            "status": "ok",
            "message_ar": f"تم استيراد {metrics['stories_imported']} قصة و {metrics['events_imported']} حدث",
            "message_en": f"Imported {metrics['stories_imported']} stories and {metrics['events_imported']} events",
            "metrics": metrics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "import_failed",
                "message_ar": "فشل استيراد القصص",
                "message_en": f"Story import failed: {str(e)}",
            },
        )


@router.get("/story/{cluster_id}/events", response_model=dict)
async def get_story_events(
    cluster_id: str,
    lang: str = Query("ar", pattern="^(ar|en)$"),
):
    """
    Get events for a story in chronological order.

    Returns all events with their details and evidence pointers.
    """
    kg = get_kg_client()

    full_id = f"story_cluster:{cluster_id}" if ":" not in cluster_id else cluster_id

    # Verify cluster exists
    cluster = await kg.get(full_id)
    if not cluster:
        raise HTTPException(status_code=404, detail={
            "error_code": "cluster_not_found",
            "message_ar": "لم يتم العثور على القصة",
            "message_en": "Story cluster not found",
        })

    # Get events ordered by chronological index
    events = await kg.select(
        "story_event",
        where=f'cluster_id = {full_id}',
        order_by="chronological_index",
    )

    def localize(obj: dict, field_base: str) -> str:
        ar_field = f"{field_base}_ar"
        en_field = f"{field_base}_en"
        if lang == "ar":
            return obj.get(ar_field) or obj.get(en_field) or ""
        return obj.get(en_field) or obj.get(ar_field) or ""

    return {
        "cluster_id": cluster_id,
        "cluster_title": localize(cluster, "title"),
        "event_count": len(events),
        "events": [
            {
                "id": e.get("id"),
                "slug": e.get("slug"),
                "chronological_index": e.get("chronological_index"),
                "title": localize(e, "title"),
                "narrative_role": e.get("narrative_role"),
                "verse_reference": e.get("verse_reference"),
                "sura_no": e.get("sura_no"),
                "ayah_start": e.get("ayah_start"),
                "ayah_end": e.get("ayah_end"),
                "summary": localize(e, "summary"),
                "semantic_tags": e.get("semantic_tags", []),
                "is_entry_point": e.get("is_entry_point", False),
                "evidence": e.get("evidence", []),
            }
            for e in events
        ],
    }
