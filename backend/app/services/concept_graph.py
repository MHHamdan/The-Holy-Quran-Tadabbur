"""
Concept Graph Service - Quran Concept Graph queries and navigation.

This service provides:
1. Concept listing with filtering by type
2. Concept detail with occurrences
3. Association discovery for Related Concepts
4. Cross-concept navigation

GROUNDING RULES:
================
- All concepts come from curated dictionary or story extraction
- Occurrences are linked to actual Quran refs (stories, segments, ayat)
- Associations have evidence_refs for scholarly grounding
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.concept import (
    Concept,
    Occurrence,
    Association,
    CONCEPT_TYPE_TRANSLATIONS,
    RELATION_TYPE_TRANSLATIONS,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ConceptSummary:
    """Summary of a concept for listing."""
    id: str
    slug: str
    label_ar: str
    label_en: str
    concept_type: str
    icon_hint: Optional[str]
    is_curated: bool
    occurrence_count: int = 0


@dataclass
class ConceptDetail:
    """Full concept detail."""
    id: str
    slug: str
    label_ar: str
    label_en: str
    concept_type: str
    aliases_ar: list[str]
    aliases_en: list[str]
    description_ar: Optional[str]
    description_en: Optional[str]
    parent_id: Optional[str]
    icon_hint: Optional[str]
    is_curated: bool
    source: Optional[str]


@dataclass
class OccurrenceInfo:
    """Occurrence information."""
    id: int
    concept_id: str
    ref_type: str
    ref_id: Optional[str]
    sura_no: Optional[int]
    ayah_start: Optional[int]
    ayah_end: Optional[int]
    verse_reference: str
    weight: float
    context_ar: Optional[str]
    context_en: Optional[str]
    has_evidence: bool
    is_verified: bool


@dataclass
class AssociationInfo:
    """Association between concepts."""
    id: int
    concept_a_id: str
    concept_b_id: str
    other_concept_id: str  # The one that isn't the current concept
    other_concept_label_ar: str
    other_concept_label_en: str
    other_concept_type: str
    relation_type: str
    relation_label_ar: str
    relation_label_en: str
    is_directional: bool
    strength: float
    explanation_ar: Optional[str]
    explanation_en: Optional[str]
    has_sufficient_evidence: bool


@dataclass
class ConceptTypeFacet:
    """Concept type with count."""
    type: str
    label_ar: str
    label_en: str
    count: int


# =============================================================================
# CONCEPT GRAPH SERVICE
# =============================================================================

class ConceptGraphService:
    """Service for Quran Concept Graph operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_concepts(
        self,
        concept_type: Optional[str] = None,
        search: Optional[str] = None,
        curated_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ConceptSummary], int]:
        """
        List concepts with optional filtering.

        Args:
            concept_type: Filter by type (person, nation, theme, etc.)
            search: Search in labels and aliases
            curated_only: Only return curated concepts
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (concepts, total_count)
        """
        logger.debug(
            "list_concepts called",
            extra={"type": concept_type, "search": search, "limit": limit, "offset": offset}
        )
        # Build query
        query = select(Concept)

        if concept_type:
            query = query.where(Concept.concept_type == concept_type)

        if curated_only:
            query = query.where(Concept.is_curated == True)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Concept.label_ar.ilike(search_pattern),
                    Concept.label_en.ilike(search_pattern),
                    Concept.slug.ilike(search_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Concept.display_order, Concept.label_en)
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        concepts = result.scalars().all()

        # Get occurrence counts
        summaries = []
        for concept in concepts:
            occ_count = await self._get_occurrence_count(concept.id)
            summaries.append(ConceptSummary(
                id=concept.id,
                slug=concept.slug,
                label_ar=concept.label_ar,
                label_en=concept.label_en,
                concept_type=concept.concept_type,
                icon_hint=concept.icon_hint,
                is_curated=concept.is_curated,
                occurrence_count=occ_count,
            ))

        return summaries, total_count

    async def get_concept(self, concept_id: str) -> Optional[ConceptDetail]:
        """Get concept detail by ID."""
        result = await self.session.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        concept = result.scalar_one_or_none()

        if not concept:
            return None

        return ConceptDetail(
            id=concept.id,
            slug=concept.slug,
            label_ar=concept.label_ar,
            label_en=concept.label_en,
            concept_type=concept.concept_type,
            aliases_ar=concept.aliases_ar or [],
            aliases_en=concept.aliases_en or [],
            description_ar=concept.description_ar,
            description_en=concept.description_en,
            parent_id=concept.parent_concept_id,
            icon_hint=concept.icon_hint,
            is_curated=concept.is_curated,
            source=concept.source,
        )

    async def get_concept_occurrences(
        self,
        concept_id: str,
        ref_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OccurrenceInfo], int]:
        """
        Get occurrences for a concept.

        Args:
            concept_id: Concept ID
            ref_type: Filter by reference type (ayah, segment, story, cluster)
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (occurrences, total_count)
        """
        query = select(Occurrence).where(Occurrence.concept_id == concept_id)

        if ref_type:
            query = query.where(Occurrence.ref_type == ref_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Occurrence.sura_no, Occurrence.ayah_start)
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        occurrences = result.scalars().all()

        infos = []
        for occ in occurrences:
            infos.append(OccurrenceInfo(
                id=occ.id,
                concept_id=occ.concept_id,
                ref_type=occ.ref_type,
                ref_id=occ.ref_id,
                sura_no=occ.sura_no,
                ayah_start=occ.ayah_start,
                ayah_end=occ.ayah_end,
                verse_reference=occ.verse_reference,
                weight=occ.weight,
                context_ar=occ.context_ar,
                context_en=occ.context_en,
                has_evidence=bool(occ.evidence_chunk_ids),
                is_verified=occ.is_verified,
            ))

        return infos, total_count

    async def get_concept_associations(
        self,
        concept_id: str,
        relation_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[AssociationInfo]:
        """
        Get associations for a concept (related concepts).

        Args:
            concept_id: Concept ID
            relation_type: Filter by relation type
            limit: Max results

        Returns:
            List of associations with related concept info
        """
        # Query associations where concept is either A or B
        query = select(Association).where(
            or_(
                Association.concept_a_id == concept_id,
                Association.concept_b_id == concept_id,
            )
        )

        if relation_type:
            query = query.where(Association.relation_type == relation_type)

        query = query.order_by(Association.strength.desc())
        query = query.limit(limit)

        result = await self.session.execute(query)
        associations = result.scalars().all()

        infos = []
        for assoc in associations:
            # Determine which concept is "other"
            if assoc.concept_a_id == concept_id:
                other_id = assoc.concept_b_id
            else:
                other_id = assoc.concept_a_id

            # Get other concept details
            other = await self.session.execute(
                select(Concept).where(Concept.id == other_id)
            )
            other_concept = other.scalar_one_or_none()

            if not other_concept:
                continue

            # Get relation type translations
            rel_trans = RELATION_TYPE_TRANSLATIONS.get(assoc.relation_type, {})

            infos.append(AssociationInfo(
                id=assoc.id,
                concept_a_id=assoc.concept_a_id,
                concept_b_id=assoc.concept_b_id,
                other_concept_id=other_id,
                other_concept_label_ar=other_concept.label_ar,
                other_concept_label_en=other_concept.label_en,
                other_concept_type=other_concept.concept_type,
                relation_type=assoc.relation_type,
                relation_label_ar=rel_trans.get("ar", assoc.relation_type),
                relation_label_en=rel_trans.get("en", assoc.relation_type),
                is_directional=assoc.is_directional,
                strength=assoc.strength,
                explanation_ar=assoc.explanation_ar,
                explanation_en=assoc.explanation_en,
                has_sufficient_evidence=assoc.has_sufficient_evidence,
            ))

        return infos

    async def get_concept_types(self) -> list[ConceptTypeFacet]:
        """Get available concept types with counts."""
        query = (
            select(
                Concept.concept_type,
                func.count(Concept.id).label("count")
            )
            .group_by(Concept.concept_type)
            .order_by(func.count(Concept.id).desc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        facets = []
        for row in rows:
            concept_type = row[0]
            count = row[1]
            trans = CONCEPT_TYPE_TRANSLATIONS.get(concept_type, {})
            facets.append(ConceptTypeFacet(
                type=concept_type,
                label_ar=trans.get("ar", concept_type),
                label_en=trans.get("en", concept_type),
                count=count,
            ))

        return facets

    async def search_concepts(
        self,
        query_text: str,
        limit: int = 20,
    ) -> list[ConceptSummary]:
        """
        Search concepts by text across labels, aliases, and descriptions.

        Args:
            query_text: Search text
            limit: Max results

        Returns:
            List of matching concepts
        """
        search_pattern = f"%{query_text}%"

        query = select(Concept).where(
            or_(
                Concept.label_ar.ilike(search_pattern),
                Concept.label_en.ilike(search_pattern),
                Concept.slug.ilike(search_pattern),
                Concept.description_ar.ilike(search_pattern),
                Concept.description_en.ilike(search_pattern),
            )
        ).limit(limit)

        result = await self.session.execute(query)
        concepts = result.scalars().all()

        summaries = []
        for concept in concepts:
            occ_count = await self._get_occurrence_count(concept.id)
            summaries.append(ConceptSummary(
                id=concept.id,
                slug=concept.slug,
                label_ar=concept.label_ar,
                label_en=concept.label_en,
                concept_type=concept.concept_type,
                icon_hint=concept.icon_hint,
                is_curated=concept.is_curated,
                occurrence_count=occ_count,
            ))

        return summaries

    async def get_concepts_by_story(self, story_id: str) -> list[ConceptSummary]:
        """Get all concepts associated with a story."""
        # Find occurrences for this story
        query = (
            select(Occurrence.concept_id)
            .where(
                Occurrence.ref_type == "story",
                Occurrence.ref_id == story_id,
            )
            .distinct()
        )

        result = await self.session.execute(query)
        concept_ids = [row[0] for row in result.all()]

        if not concept_ids:
            return []

        # Get concept details
        concepts_query = select(Concept).where(Concept.id.in_(concept_ids))
        concepts_result = await self.session.execute(concepts_query)
        concepts = concepts_result.scalars().all()

        summaries = []
        for concept in concepts:
            occ_count = await self._get_occurrence_count(concept.id)
            summaries.append(ConceptSummary(
                id=concept.id,
                slug=concept.slug,
                label_ar=concept.label_ar,
                label_en=concept.label_en,
                concept_type=concept.concept_type,
                icon_hint=concept.icon_hint,
                is_curated=concept.is_curated,
                occurrence_count=occ_count,
            ))

        return summaries

    async def _get_occurrence_count(self, concept_id: str) -> int:
        """Get count of occurrences for a concept."""
        query = select(func.count(Occurrence.id)).where(
            Occurrence.concept_id == concept_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
