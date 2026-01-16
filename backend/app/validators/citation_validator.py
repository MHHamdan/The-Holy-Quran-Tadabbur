"""
Citation validation for RAG responses.

CRITICAL: Ensures all citations in responses map to retrieved sources.
"""
import re
from typing import List, Set, Tuple
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tafseer import TafseerChunk


@dataclass
class CitationValidationResult:
    """Result of citation validation."""
    is_valid: bool
    valid_citations: List[str]
    invalid_citations: List[str]
    missing_citations: List[str]  # Paragraphs without citations
    coverage_score: float  # Percentage of text that is cited
    errors: List[str]


class CitationValidator:
    """
    Validates that citations in RAG responses:
    1. Exist in the retrieved chunks
    2. Match the claimed source
    3. Cover all major claims in the response
    """

    # Pattern to match citations like [Ibn Kathir, 2:255] or [Al-Tabari, Al-Baqarah:45]
    CITATION_PATTERN = re.compile(
        r'\[([^\],]+),\s*([^\]]+)\]',
        re.UNICODE
    )

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate(
        self,
        response_text: str,
        retrieved_chunk_ids: List[str],
    ) -> CitationValidationResult:
        """
        Validate all citations in the response.

        Args:
            response_text: The RAG-generated response
            retrieved_chunk_ids: List of chunk IDs that were retrieved

        Returns:
            CitationValidationResult with validation details
        """
        errors = []
        valid_citations = []
        invalid_citations = []

        # 1. Extract all citations from response
        found_citations = self.CITATION_PATTERN.findall(response_text)

        if not found_citations:
            return CitationValidationResult(
                is_valid=False,
                valid_citations=[],
                invalid_citations=[],
                missing_citations=["Entire response lacks citations"],
                coverage_score=0.0,
                errors=["No citations found in response"],
            )

        # 2. Get chunk metadata from database
        chunk_metadata = await self._get_chunk_metadata(retrieved_chunk_ids)

        # 3. Validate each citation
        for source_name, verse_ref in found_citations:
            citation_str = f"[{source_name}, {verse_ref}]"

            # Check if this citation matches any retrieved chunk
            is_matched = False
            for chunk_id, metadata in chunk_metadata.items():
                if self._citation_matches_chunk(source_name, verse_ref, metadata):
                    is_matched = True
                    valid_citations.append(citation_str)
                    break

            if not is_matched:
                invalid_citations.append(citation_str)
                errors.append(f"Citation {citation_str} not found in retrieved sources")

        # 4. Check paragraph coverage
        missing_citations = self._check_paragraph_coverage(response_text)

        # 5. Calculate coverage score
        total_citations = len(found_citations)
        valid_count = len(valid_citations)
        coverage_score = valid_count / total_citations if total_citations > 0 else 0.0

        # Determine if response is valid
        is_valid = (
            len(invalid_citations) == 0 and
            len(missing_citations) == 0 and
            coverage_score >= 0.8
        )

        return CitationValidationResult(
            is_valid=is_valid,
            valid_citations=valid_citations,
            invalid_citations=invalid_citations,
            missing_citations=missing_citations,
            coverage_score=coverage_score,
            errors=errors,
        )

    async def _get_chunk_metadata(
        self,
        chunk_ids: List[str],
    ) -> dict:
        """Get metadata for chunks from database."""
        if not chunk_ids:
            return {}

        result = await self.session.execute(
            select(TafseerChunk).where(TafseerChunk.chunk_id.in_(chunk_ids))
        )
        chunks = result.scalars().all()

        return {
            chunk.chunk_id: {
                "source_id": chunk.source_id,
                "sura_no": chunk.sura_no,
                "aya_start": chunk.aya_start,
                "aya_end": chunk.aya_end,
                "verse_reference": chunk.verse_reference,
            }
            for chunk in chunks
        }

    def _citation_matches_chunk(
        self,
        source_name: str,
        verse_ref: str,
        chunk_metadata: dict,
    ) -> bool:
        """
        Check if a citation matches a chunk's metadata.

        Handles variations in source naming and verse reference formats.
        """
        source_lower = source_name.lower().strip()
        source_id = chunk_metadata["source_id"].lower()

        # Check source match (flexible matching)
        source_match = (
            source_lower in source_id or
            source_id in source_lower or
            self._normalize_source_name(source_lower) == self._normalize_source_name(source_id)
        )

        if not source_match:
            return False

        # Check verse reference match
        verse_ref = verse_ref.strip()

        # Parse verse reference (could be "2:255" or "Al-Baqarah:255" or "2:255-260")
        parsed_ref = self._parse_verse_reference(verse_ref)
        if not parsed_ref:
            return False

        sura_no, aya_start, aya_end = parsed_ref

        chunk_sura = chunk_metadata["sura_no"]
        chunk_aya_start = chunk_metadata["aya_start"]
        chunk_aya_end = chunk_metadata["aya_end"]

        # Check if cited verse is within chunk's range
        if sura_no != chunk_sura:
            return False

        # Citation must be within chunk's verse range
        return (
            aya_start >= chunk_aya_start and
            aya_end <= chunk_aya_end
        )

    def _normalize_source_name(self, name: str) -> str:
        """Normalize source name for comparison."""
        # Remove common prefixes/suffixes
        name = name.lower().strip()
        for prefix in ["tafsir ", "tafseer ", "al-", "ibn ", "imam "]:
            if name.startswith(prefix):
                name = name[len(prefix):]
        return name

    def _parse_verse_reference(
        self,
        ref: str,
    ) -> Tuple[int, int, int] | None:
        """
        Parse verse reference into (sura_no, aya_start, aya_end).

        Handles formats:
        - "2:255" -> (2, 255, 255)
        - "2:255-260" -> (2, 255, 260)
        - "Al-Baqarah:255" -> (2, 255, 255) (using sura name mapping)
        """
        # Sura name to number mapping
        sura_names = {
            "al-fatiha": 1, "al-baqarah": 2, "al-imran": 3, "an-nisa": 4,
            "al-maidah": 5, "al-anam": 6, "al-araf": 7, "al-anfal": 8,
            "at-tawbah": 9, "yunus": 10, "hud": 11, "yusuf": 12,
            "ar-rad": 13, "ibrahim": 14, "al-hijr": 15, "an-nahl": 16,
            "al-isra": 17, "al-kahf": 18, "maryam": 19, "taha": 20,
            # Add more as needed...
        }

        ref = ref.strip().lower()

        # Try numeric format first: "2:255" or "2:255-260"
        numeric_match = re.match(r'(\d+):(\d+)(?:-(\d+))?', ref)
        if numeric_match:
            sura = int(numeric_match.group(1))
            aya_start = int(numeric_match.group(2))
            aya_end = int(numeric_match.group(3)) if numeric_match.group(3) else aya_start
            return (sura, aya_start, aya_end)

        # Try name format: "Al-Baqarah:255"
        name_match = re.match(r'([a-z\-]+):(\d+)(?:-(\d+))?', ref)
        if name_match:
            sura_name = name_match.group(1)
            if sura_name in sura_names:
                sura = sura_names[sura_name]
                aya_start = int(name_match.group(2))
                aya_end = int(name_match.group(3)) if name_match.group(3) else aya_start
                return (sura, aya_start, aya_end)

        return None

    def _check_paragraph_coverage(self, response_text: str) -> List[str]:
        """
        Check that each substantive paragraph has at least one citation.
        """
        missing = []

        # Split into paragraphs
        paragraphs = [p.strip() for p in response_text.split('\n\n') if p.strip()]

        for i, para in enumerate(paragraphs):
            # Skip short paragraphs (headers, transitions, etc.)
            if len(para) < 100:
                continue

            # Skip paragraphs that are just lists or formatting
            if para.startswith('-') or para.startswith('*') or para.startswith('#'):
                continue

            # Check if paragraph has a citation
            if not self.CITATION_PATTERN.search(para):
                # Truncate for error message
                preview = para[:50] + "..." if len(para) > 50 else para
                missing.append(f"Paragraph {i+1}: {preview}")

        return missing


class CitationCoverageValidator:
    """
    Validates that citations actually support the claims made.

    This is a more sophisticated validator that checks semantic
    alignment between claims and cited evidence.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_claim_support(
        self,
        claim: str,
        cited_chunk_id: str,
    ) -> Tuple[bool, float, str]:
        """
        Check if a cited chunk actually supports the claim.

        Returns:
            (is_supported, confidence, explanation)
        """
        # Get chunk content
        result = await self.session.execute(
            select(TafseerChunk).where(TafseerChunk.chunk_id == cited_chunk_id)
        )
        chunk = result.scalar_one_or_none()

        if not chunk:
            return (False, 0.0, f"Chunk {cited_chunk_id} not found")

        # For MVP, we do simple keyword overlap check
        # In production, use semantic similarity
        claim_words = set(claim.lower().split())
        content = (chunk.content_en or chunk.content_ar or "").lower()
        content_words = set(content.split())

        overlap = len(claim_words & content_words)
        overlap_ratio = overlap / len(claim_words) if claim_words else 0

        if overlap_ratio >= 0.3:
            return (True, overlap_ratio, "Claim appears to be supported by source")
        else:
            return (False, overlap_ratio, "Claim may not be fully supported by source")
