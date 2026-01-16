"""
Madhab Validation Service

Strict validation to ensure only 4 Sunni madhabs are used for tafsir evidence.
This is a core security/correctness requirement.

ALLOWED MADHABS:
1. Hanafi - Abu Hanifa and his school
2. Maliki - Malik ibn Anas and his school
3. Shafi'i - al-Shafi'i and his school
4. Hanbali - Ahmad ibn Hanbal and his school

Any other madhab/source classification is REJECTED.
"""
from typing import List, Optional, Set, Dict, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidMadhab(str, Enum):
    """Valid Sunni madhabs only."""
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"


# Mapping from source_id to validated madhab
# Only sources that can be definitively attributed to one of 4 madhabs
APPROVED_SOURCES: Dict[str, ValidMadhab] = {
    # Shafi'i madhab scholars
    "ibn_kathir_ar": ValidMadhab.SHAFII,
    "ibn_kathir_en": ValidMadhab.SHAFII,

    # Maliki madhab scholars
    "qurtubi_ar": ValidMadhab.MALIKI,

    # Hanafi madhab scholars
    "nasafi_ar": ValidMadhab.HANAFI,

    # Hanbali madhab scholars
    "shinqiti_ar": ValidMadhab.HANBALI,
}

# Sources that are excluded because they don't fit 4 madhab classification
EXCLUDED_SOURCES = {
    "jalalayn_en",  # Combined (Shafi'i + Shafi'i but marketed as combined)
    "tabari_ar",    # Pre-madhab classical scholar
    "muyassar_ar",  # Modern simplified, no specific madhab
}

# Scholars approved per madhab with their source IDs
APPROVED_SCHOLARS: Dict[ValidMadhab, List[Dict[str, str]]] = {
    ValidMadhab.HANAFI: [
        {"id": "nasafi", "name_ar": "الإمام النسفي", "name_en": "Imam al-Nasafi", "book": "مدارك التنزيل"},
    ],
    ValidMadhab.MALIKI: [
        {"id": "qurtubi", "name_ar": "الإمام القرطبي", "name_en": "Imam al-Qurtubi", "book": "الجامع لأحكام القرآن"},
    ],
    ValidMadhab.SHAFII: [
        {"id": "ibn_kathir", "name_ar": "ابن كثير", "name_en": "Ibn Kathir", "book": "تفسير ابن كثير"},
    ],
    ValidMadhab.HANBALI: [
        {"id": "shinqiti", "name_ar": "الشنقيطي", "name_en": "al-Shinqiti", "book": "أضواء البيان"},
    ],
}


def is_valid_madhab(madhab: str) -> bool:
    """Check if a madhab string is one of the 4 valid Sunni madhabs."""
    if not madhab:
        return False
    madhab_lower = madhab.lower().strip()
    return madhab_lower in {m.value for m in ValidMadhab}


def validate_source(source_id: str) -> Tuple[bool, Optional[ValidMadhab]]:
    """
    Validate a tafsir source and return its madhab if approved.

    Returns:
        (is_valid, madhab) - madhab is None if source is not approved
    """
    if source_id in EXCLUDED_SOURCES:
        logger.debug(f"Source {source_id} is excluded from 4-madhab requirement")
        return False, None

    if source_id in APPROVED_SOURCES:
        return True, APPROVED_SOURCES[source_id]

    logger.warning(f"Unknown source {source_id} - not in approved list")
    return False, None


def get_approved_source_ids() -> Set[str]:
    """Get set of approved source IDs for querying."""
    return set(APPROVED_SOURCES.keys())


def get_approved_source_ids_list() -> List[str]:
    """Get list of approved source IDs for SQL queries."""
    return list(APPROVED_SOURCES.keys())


def filter_evidence_by_madhab(
    evidence_chunks: List[dict],
    source_id_field: str = "source_id"
) -> List[dict]:
    """
    Filter a list of evidence chunks to only include those from approved sources.

    Args:
        evidence_chunks: List of evidence dicts
        source_id_field: Field name containing source_id

    Returns:
        Filtered list with only approved madhab sources
    """
    filtered = []
    for chunk in evidence_chunks:
        source_id = chunk.get(source_id_field)
        is_valid, madhab = validate_source(source_id)
        if is_valid:
            # Add validated madhab to the chunk
            chunk["validated_madhab"] = madhab.value
            filtered.append(chunk)
        else:
            logger.debug(f"Filtered out evidence from source: {source_id}")

    return filtered


def get_madhabs_present(evidence_chunks: List[dict]) -> List[str]:
    """Get list of madhabs present in evidence chunks."""
    madhabs = set()
    for chunk in evidence_chunks:
        madhab = chunk.get("validated_madhab") or chunk.get("madhab")
        if madhab and is_valid_madhab(madhab):
            madhabs.add(madhab.lower())
    return sorted(list(madhabs))


def get_madhabs_missing(evidence_chunks: List[dict]) -> List[str]:
    """Get list of madhabs NOT present in evidence chunks."""
    present = set(get_madhabs_present(evidence_chunks))
    all_madhabs = {m.value for m in ValidMadhab}
    return sorted(list(all_madhabs - present))


def get_scholar_info(source_id: str) -> Optional[Dict[str, str]]:
    """Get scholar information for a source."""
    is_valid, madhab = validate_source(source_id)
    if not is_valid or not madhab:
        return None

    scholars = APPROVED_SCHOLARS.get(madhab, [])
    for scholar in scholars:
        if source_id.startswith(scholar["id"]):
            return {
                "scholar_name_ar": scholar["name_ar"],
                "scholar_name_en": scholar["name_en"],
                "book_name_ar": scholar["book"],
                "madhab": madhab.value,
            }
    return None


class MadhabValidator:
    """
    Service for validating madhab constraints.

    Usage:
        validator = MadhabValidator()
        if not validator.validate_evidence(evidence_list):
            raise APIError(...)
    """

    def __init__(self):
        self.approved_sources = APPROVED_SOURCES
        self.excluded_sources = EXCLUDED_SOURCES

    def validate_madhab(self, madhab: str) -> bool:
        """Validate a single madhab string."""
        return is_valid_madhab(madhab)

    def validate_source(self, source_id: str) -> bool:
        """Validate a source is from approved 4 madhabs."""
        is_valid, _ = validate_source(source_id)
        return is_valid

    def get_approved_sql_filter(self) -> str:
        """Get SQL IN clause for approved sources."""
        sources = get_approved_source_ids_list()
        quoted = [f"'{s}'" for s in sources]
        return f"({', '.join(quoted)})"

    def filter_and_enrich_evidence(self, evidence: List[dict]) -> List[dict]:
        """Filter evidence and add scholar metadata."""
        filtered = filter_evidence_by_madhab(evidence)

        # Enrich with scholar info
        for item in filtered:
            source_id = item.get("source_id")
            if source_id:
                scholar_info = get_scholar_info(source_id)
                if scholar_info:
                    item.update(scholar_info)

        return filtered

    def get_coverage_report(self, evidence: List[dict]) -> dict:
        """Get madhab coverage report for evidence."""
        present = get_madhabs_present(evidence)
        missing = get_madhabs_missing(evidence)

        return {
            "madhabs_present": present,
            "madhabs_missing": missing,
            "coverage_percentage": len(present) / len(ValidMadhab) * 100,
            "has_all_madhabs": len(missing) == 0,
        }


# Singleton instance
madhab_validator = MadhabValidator()
