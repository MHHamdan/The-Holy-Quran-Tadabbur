"""
Vector-to-Graph Bridge.

Connects Qdrant vector search results to SurrealDB Knowledge Graph
for context expansion and evidence tracing.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from app.kg.client import get_kg_client, KGClient
from app.kg.models import (
    VectorHit,
    GraphPath,
    HybridEvidenceItem,
    HybridRetrievalResult,
)

logger = logging.getLogger(__name__)


@dataclass
class GraphExpansionConfig:
    """Configuration for graph expansion."""
    max_depth: int = 2
    max_neighbors_per_node: int = 5
    include_next_events: bool = True
    include_previous_events: bool = True
    include_thematic_links: bool = True
    include_persons: bool = True
    include_places: bool = True


class VectorGraphBridge:
    """
    Bridge between Qdrant vectors and SurrealDB graph.

    Workflow:
    1. Vector search returns chunk IDs with scores
    2. Bridge looks up corresponding SurrealDB records
    3. Graph expansion finds related context (events, clusters, etc.)
    4. Combined evidence is ranked and returned
    """

    def __init__(self, kg_client: KGClient = None):
        self.kg_client = kg_client or get_kg_client()

    async def lookup_chunks_in_graph(
        self,
        chunk_ids: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Look up tafsir chunks in the Knowledge Graph.

        Args:
            chunk_ids: List of chunk IDs from vector search

        Returns:
            Dict mapping chunk_id to SurrealDB record
        """
        if not chunk_ids:
            return {}

        # Build query for multiple chunks
        # SurrealDB uses chunk_id as part of record ID
        results = {}

        for chunk_id in chunk_ids:
            try:
                # Try to find by chunk_id field
                records = await self.kg_client.select(
                    "tafsir_chunk",
                    where=f'source_id + ":" + verse_reference CONTAINS "{chunk_id}" OR id = "tafsir_chunk:{chunk_id}"',
                    limit=1,
                )
                if records:
                    results[chunk_id] = records[0]
            except Exception as e:
                logger.debug(f"Chunk {chunk_id} not found in KG: {e}")

        return results

    async def expand_from_chunks(
        self,
        chunk_records: Dict[str, Dict[str, Any]],
        config: GraphExpansionConfig = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Expand graph context from tafsir chunks.

        Traverses:
        - chunk -> EXPLAINS -> ayah
        - chunk <- SUPPORTED_BY <- story_event -> cluster
        - event -> NEXT -> event (neighbors)
        - event -> THEMATIC_LINK -> event

        Args:
            chunk_records: Dict of chunk_id -> SurrealDB record
            config: Expansion configuration

        Returns:
            Dict with expansion results:
            - "ayahs": related ayahs
            - "events": related story events
            - "clusters": related story clusters
            - "neighbor_events": chronologically adjacent events
            - "thematic_events": thematically linked events
        """
        config = config or GraphExpansionConfig()
        expansion = {
            "ayahs": [],
            "events": [],
            "clusters": [],
            "neighbor_events": [],
            "thematic_events": [],
            "persons": [],
            "places": [],
        }

        seen_ids: Set[str] = set()

        for chunk_id, chunk in chunk_records.items():
            chunk_surreal_id = chunk.get("id")
            if not chunk_surreal_id:
                continue

            # 1. Find ayahs this chunk explains
            try:
                ayahs = await self.kg_client.traverse(
                    chunk_surreal_id,
                    "explains",
                    direction="out",
                    depth=1,
                )
                for ayah in ayahs:
                    if ayah.get("id") not in seen_ids:
                        expansion["ayahs"].append(ayah)
                        seen_ids.add(ayah.get("id"))
            except Exception as e:
                logger.debug(f"Error expanding ayahs for {chunk_id}: {e}")

            # 2. Find events supported by this chunk
            try:
                events = await self.kg_client.query(
                    f"SELECT in.* FROM supported_by WHERE out = {chunk_surreal_id};"
                )
                for event in events:
                    event_id = event.get("id")
                    if event_id and event_id not in seen_ids:
                        expansion["events"].append(event)
                        seen_ids.add(event_id)

                        # Get cluster for this event
                        cluster_id = event.get("cluster_id")
                        if cluster_id and cluster_id not in seen_ids:
                            cluster = await self.kg_client.get(cluster_id)
                            if cluster:
                                expansion["clusters"].append(cluster)
                                seen_ids.add(cluster_id)

                        # 3. Get neighbor events via NEXT edges
                        if config.include_next_events:
                            next_events = await self.kg_client.traverse(
                                event_id,
                                "next",
                                direction="out",
                                depth=1,
                            )
                            for ne in next_events[:config.max_neighbors_per_node]:
                                if ne.get("id") not in seen_ids:
                                    expansion["neighbor_events"].append(ne)
                                    seen_ids.add(ne.get("id"))

                        if config.include_previous_events:
                            prev_events = await self.kg_client.traverse(
                                event_id,
                                "next",
                                direction="in",
                                depth=1,
                            )
                            for pe in prev_events[:config.max_neighbors_per_node]:
                                if pe.get("id") not in seen_ids:
                                    expansion["neighbor_events"].append(pe)
                                    seen_ids.add(pe.get("id"))

                        # 4. Get thematic links
                        if config.include_thematic_links:
                            thematic = await self.kg_client.query(
                                f"""
                                SELECT out.* FROM thematic_link WHERE in = {event_id}
                                UNION
                                SELECT in.* FROM thematic_link WHERE out = {event_id};
                                """
                            )
                            for te in thematic[:config.max_neighbors_per_node]:
                                if te.get("id") not in seen_ids:
                                    expansion["thematic_events"].append(te)
                                    seen_ids.add(te.get("id"))

                        # 5. Get persons and places
                        if config.include_persons:
                            persons = await self.kg_client.traverse(
                                event_id,
                                "involves",
                                direction="out",
                                depth=1,
                            )
                            for p in persons:
                                if p.get("id") not in seen_ids:
                                    expansion["persons"].append(p)
                                    seen_ids.add(p.get("id"))

                        if config.include_places:
                            places = await self.kg_client.traverse(
                                event_id,
                                "located_in",
                                direction="out",
                                depth=1,
                            )
                            for pl in places:
                                if pl.get("id") not in seen_ids:
                                    expansion["places"].append(pl)
                                    seen_ids.add(pl.get("id"))

            except Exception as e:
                logger.debug(f"Error expanding events for {chunk_id}: {e}")

        return expansion

    def build_graph_paths(
        self,
        chunk_id: str,
        chunk_record: Dict[str, Any],
        expansion: Dict[str, List[Dict[str, Any]]],
    ) -> List[GraphPath]:
        """
        Build graph paths from chunk to story context.

        Args:
            chunk_id: Original chunk ID
            chunk_record: SurrealDB record for chunk
            expansion: Expansion results

        Returns:
            List of GraphPath objects showing traversal
        """
        paths = []

        # Find ayahs connected to this chunk
        chunk_surreal_id = chunk_record.get("id", "")
        connected_ayah_ids = []
        connected_event_ids = []
        cluster_id = None

        for ayah in expansion.get("ayahs", []):
            connected_ayah_ids.append(ayah.get("id", ""))

        for event in expansion.get("events", []):
            event_id = event.get("id", "")
            if event_id:
                connected_event_ids.append(event_id)
                if not cluster_id:
                    cluster_id = event.get("cluster_id")

        # Include neighbor events in paths
        for event in expansion.get("neighbor_events", []):
            event_id = event.get("id", "")
            if event_id and event_id not in connected_event_ids:
                connected_event_ids.append(event_id)

        if connected_ayah_ids or connected_event_ids or cluster_id:
            paths.append(GraphPath(
                chunk_id=chunk_id,
                ayah_ids=connected_ayah_ids,
                event_ids=connected_event_ids,
                cluster_id=cluster_id,
            ))

        return paths

    async def hybrid_retrieve(
        self,
        vector_hits: List[VectorHit],
        config: GraphExpansionConfig = None,
    ) -> HybridRetrievalResult:
        """
        Perform hybrid retrieval combining vector hits with graph expansion.

        Args:
            vector_hits: Results from vector search
            config: Graph expansion configuration

        Returns:
            HybridRetrievalResult with combined evidence
        """
        config = config or GraphExpansionConfig()

        # Extract chunk IDs
        chunk_ids = [hit.chunk_id for hit in vector_hits]

        # Look up chunks in graph
        chunk_records = await self.lookup_chunks_in_graph(chunk_ids)

        # Expand graph context
        expansion = await self.expand_from_chunks(chunk_records, config)

        # Build evidence items with graph paths
        final_evidence: List[HybridEvidenceItem] = []
        graph_expanded_ids: List[str] = []

        for hit in vector_hits:
            chunk_record = chunk_records.get(hit.chunk_id)

            if chunk_record:
                # Update surreal_id on hit
                hit.surreal_id = chunk_record.get("id")

                # Build graph paths
                paths = self.build_graph_paths(hit.chunk_id, chunk_record, expansion)

                # Get story context if available
                story_context = None
                if paths and paths[0].cluster_id:
                    cluster_id = paths[0].cluster_id
                    for cluster in expansion.get("clusters", []):
                        if cluster.get("id") == cluster_id:
                            story_context = {
                                "cluster_id": cluster_id,
                                "cluster_title_ar": cluster.get("title_ar"),
                                "cluster_title_en": cluster.get("title_en"),
                            }
                            if paths[0].event_ids:
                                story_context["event_id"] = paths[0].event_ids[0]
                            break

                evidence_item = HybridEvidenceItem(
                    chunk_id=hit.chunk_id,
                    source_id=chunk_record.get("source_id", ""),
                    source_name=chunk_record.get("source_name", ""),
                    source_name_ar=chunk_record.get("source_name_ar", ""),
                    verse_reference=chunk_record.get("verse_reference", ""),
                    sura_no=chunk_record.get("sura_no", 0),
                    ayah_start=chunk_record.get("ayah_start", 0),
                    ayah_end=chunk_record.get("ayah_end", 0),
                    content=chunk_record.get("text", ""),
                    content_ar=chunk_record.get("text") if chunk_record.get("lang") == "ar" else None,
                    content_en=chunk_record.get("text") if chunk_record.get("lang") == "en" else None,
                    relevance_score=hit.score,
                    vector_rank=hit.rank,
                    vector_score=hit.score,
                    graph_paths=paths,
                    story_context=story_context,
                )
                final_evidence.append(evidence_item)

        # Collect expanded IDs
        for key in ["ayahs", "events", "neighbor_events", "thematic_events"]:
            for item in expansion.get(key, []):
                item_id = item.get("id")
                if item_id:
                    graph_expanded_ids.append(item_id)

        return HybridRetrievalResult(
            vector_hits=vector_hits,
            graph_expanded_ids=graph_expanded_ids,
            final_evidence=final_evidence,
            debug_info={
                "chunks_found_in_kg": len(chunk_records),
                "ayahs_expanded": len(expansion.get("ayahs", [])),
                "events_expanded": len(expansion.get("events", [])),
                "clusters_found": len(expansion.get("clusters", [])),
                "neighbor_events": len(expansion.get("neighbor_events", [])),
                "thematic_events": len(expansion.get("thematic_events", [])),
            },
        )


# Singleton instance
_bridge: Optional[VectorGraphBridge] = None


def get_vector_graph_bridge() -> VectorGraphBridge:
    """Get or create the vector-graph bridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = VectorGraphBridge()
    return _bridge
