#!/usr/bin/env python3
"""
Seed Quran Concept Graph from existing story assets and curated dictionary.

STAGED APPROACH:
================
Stage A (this script): Seed from existing story assets
  - Load curated concepts dictionary (persons, nations, places, miracles, themes, patterns)
  - Extract concepts from stories (main_figures, themes)
  - Create Concept entries
  - Create Occurrence entries linking concepts to stories/segments
  - Create Association entries based on shared themes

Stage B (future): Ontology enrichment from tafsir extraction
Stage C (future): ML-assisted concept discovery

EPISTEMIC RULES:
================
1. NO novel tafsir generation - only link existing data
2. Occurrences are linked to actual story/segment refs
3. Associations require evidence refs (at minimum, story co-occurrence)
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.concept import Concept, Occurrence, Association
from app.models.story import Story, StorySegment
from app.models.audit import AuditLog

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent

# Path resolution for container vs host
if Path("/app/data/concepts").exists():
    CONCEPTS_DIR = Path("/app/data/concepts")
else:
    CONCEPTS_DIR = PROJECT_ROOT / "data" / "concepts"


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def load_curated_concepts() -> dict:
    """Load curated concepts dictionary."""
    concepts_path = CONCEPTS_DIR / "curated_concepts.json"
    with open(concepts_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
# CONCEPT NAME NORMALIZATION
# =============================================================================

# Map story figure names to concept IDs
FIGURE_TO_CONCEPT = {
    # English names
    "adam": "person_adam",
    "hawwa": "person_adam",  # Linked to Adam's story
    "nuh": "person_nuh",
    "noah": "person_nuh",
    "ibrahim": "person_ibrahim",
    "abraham": "person_ibrahim",
    "musa": "person_musa",
    "moses": "person_musa",
    "harun": "person_musa",  # Often appears with Musa
    "isa": "person_isa",
    "jesus": "person_isa",
    "yusuf": "person_yusuf",
    "joseph": "person_yusuf",
    "yaqub": "person_yusuf",  # Father in Yusuf's story
    "dawud": "person_dawud",
    "david": "person_dawud",
    "sulayman": "person_sulayman",
    "solomon": "person_sulayman",
    "ayyub": "person_ayyub",
    "job": "person_ayyub",
    "yunus": "person_yunus",
    "jonah": "person_yunus",
    "lut": "person_lut",
    "lot": "person_lut",
    "hud": "person_hud",
    "salih": "person_salih",
    "shuayb": "person_shuayb",
    "maryam": "person_maryam",
    "mary": "person_maryam",
    "luqman": "person_luqman",
    "firawn": "person_firawn",
    "pharaoh": "person_firawn",
    "iblis": "person_iblis",
    "satan": "person_iblis",
    "dhul-qarnayn": "person_dhulqarnayn",
    "dhulqarnayn": "person_dhulqarnayn",
    "qarun": "person_qarun",
    "korah": "person_qarun",
    # Nations
    "bani israel": "nation_bani_israel",
    "banu israel": "nation_bani_israel",
    "quraysh": "nation_quraysh",
    "aad": "nation_aad",
    "ad": "nation_aad",
    "thamud": "nation_thamud",
}

# Map theme names to concept IDs
THEME_TO_CONCEPT = {
    "patience": "theme_patience",
    "sabr": "theme_patience",
    "obedience": "theme_obedience",
    "repentance": "theme_repentance",
    "tawbah": "theme_repentance",
    "trust": "theme_trust",
    "tawakkul": "theme_trust",
    "justice": "theme_justice",
    "gratitude": "theme_gratitude",
    "shukr": "theme_gratitude",
    "arrogance": "theme_arrogance",
    "kibr": "theme_arrogance",
    "divine_punishment": "theme_divine_punishment",
    "punishment": "theme_divine_punishment",
    "salvation": "theme_salvation",
    "test": "theme_test_trial",
    "trial": "theme_test_trial",
    "test_trial": "theme_test_trial",
    "monotheism": "theme_monotheism",
    "tawhid": "theme_monotheism",
    "sacrifice": "theme_sacrifice",
    # Additional themes from stories
    "creation": "theme_monotheism",  # Creation points to monotheism
    "dawah": "theme_obedience",
    "liberation": "theme_salvation",
    "miracles": "theme_monotheism",  # Miracles point to divine power
    "divine_support": "theme_trust",
    "confronting_tyranny": "theme_justice",
    "forgiveness": "theme_repentance",
    "divine_planning": "theme_trust",
    "chastity": "theme_obedience",
    "reconciliation": "theme_repentance",
    "father_of_prophets": "theme_monotheism",
    "hajj": "theme_obedience",
}


def normalize_figure(name: str) -> str | None:
    """Normalize a figure name to a concept ID."""
    normalized = name.lower().strip()
    return FIGURE_TO_CONCEPT.get(normalized)


def normalize_theme(name: str) -> str | None:
    """Normalize a theme name to a concept ID."""
    normalized = name.lower().strip().replace(" ", "_")
    return THEME_TO_CONCEPT.get(normalized)


# =============================================================================
# SEEDING FUNCTIONS
# =============================================================================

def seed_curated_concepts(session: Session, curated: dict) -> int:
    """Seed concepts from curated dictionary."""
    count = 0

    # Seed persons
    for person in curated.get("persons", []):
        concept = Concept(
            id=person["id"],
            slug=person["slug"],
            label_ar=person["label_ar"],
            label_en=person["label_en"],
            concept_type="person",
            aliases_ar=person.get("aliases_ar"),
            aliases_en=person.get("aliases_en"),
            description_ar=person.get("description_ar"),
            description_en=person.get("description_en"),
            icon_hint=person.get("icon_hint", "user"),
            is_curated=True,
            source="curated_dict",
            display_order=count,
        )
        session.merge(concept)
        count += 1

    # Seed nations
    for nation in curated.get("nations", []):
        concept = Concept(
            id=nation["id"],
            slug=nation["slug"],
            label_ar=nation["label_ar"],
            label_en=nation["label_en"],
            concept_type="nation",
            aliases_ar=nation.get("aliases_ar"),
            aliases_en=nation.get("aliases_en"),
            description_ar=nation.get("description_ar"),
            description_en=nation.get("description_en"),
            icon_hint=nation.get("icon_hint", "users"),
            is_curated=True,
            source="curated_dict",
            display_order=count,
        )
        session.merge(concept)
        count += 1

    # Seed places
    for place in curated.get("places", []):
        concept = Concept(
            id=place["id"],
            slug=place["slug"],
            label_ar=place["label_ar"],
            label_en=place["label_en"],
            concept_type="place",
            aliases_ar=place.get("aliases_ar"),
            aliases_en=place.get("aliases_en"),
            description_ar=place.get("description_ar"),
            description_en=place.get("description_en"),
            icon_hint=place.get("icon_hint", "map-pin"),
            is_curated=True,
            source="curated_dict",
            display_order=count,
        )
        session.merge(concept)
        count += 1

    # Seed miracles
    for miracle in curated.get("miracles", []):
        concept = Concept(
            id=miracle["id"],
            slug=miracle["slug"],
            label_ar=miracle["label_ar"],
            label_en=miracle["label_en"],
            concept_type="miracle",
            description_ar=miracle.get("description_ar"),
            description_en=miracle.get("description_en"),
            icon_hint=miracle.get("icon_hint", "zap"),
            is_curated=True,
            source="curated_dict",
            display_order=count,
        )
        session.merge(concept)
        count += 1

    # Seed themes
    for theme in curated.get("themes", []):
        concept = Concept(
            id=theme["id"],
            slug=theme["slug"],
            label_ar=theme["label_ar"],
            label_en=theme["label_en"],
            concept_type="theme",
            aliases_ar=theme.get("aliases_ar"),
            aliases_en=theme.get("aliases_en"),
            icon_hint=theme.get("icon_hint", "heart"),
            is_curated=True,
            source="curated_dict",
            display_order=count,
        )
        session.merge(concept)
        count += 1

    # Seed moral patterns
    for pattern in curated.get("moral_patterns", []):
        concept = Concept(
            id=pattern["id"],
            slug=pattern["slug"],
            label_ar=pattern["label_ar"],
            label_en=pattern["label_en"],
            concept_type="moral_pattern",
            description_ar=pattern.get("description_ar"),
            description_en=pattern.get("description_en"),
            icon_hint=pattern.get("icon_hint", "trending-up"),
            is_curated=True,
            source="curated_dict",
            display_order=count,
        )
        session.merge(concept)
        count += 1

    session.commit()
    return count


def extract_concepts_from_stories(session: Session) -> Tuple[Set[str], Dict[str, List[str]]]:
    """
    Extract concept references from stories.
    Returns: (set of concept IDs found, dict mapping story_id -> list of concept_ids)
    """
    found_concepts: Set[str] = set()
    story_concepts: Dict[str, List[str]] = defaultdict(list)

    stories = session.execute(select(Story)).scalars().all()

    for story in stories:
        concepts_for_story: Set[str] = set()

        # Extract from main_figures
        if story.main_figures:
            for figure in story.main_figures:
                concept_id = normalize_figure(figure)
                if concept_id:
                    found_concepts.add(concept_id)
                    concepts_for_story.add(concept_id)

        # Extract from themes
        if story.themes:
            for theme in story.themes:
                concept_id = normalize_theme(theme)
                if concept_id:
                    found_concepts.add(concept_id)
                    concepts_for_story.add(concept_id)

        story_concepts[story.id] = list(concepts_for_story)

    return found_concepts, story_concepts


def create_story_occurrences(
    session: Session,
    story_concepts: Dict[str, List[str]]
) -> int:
    """Create occurrences linking concepts to stories."""
    count = 0

    for story_id, concept_ids in story_concepts.items():
        # Get story for verse info
        story = session.execute(
            select(Story).where(Story.id == story_id)
        ).scalar_one_or_none()

        if not story:
            continue

        for concept_id in concept_ids:
            # Check if concept exists
            concept = session.execute(
                select(Concept).where(Concept.id == concept_id)
            ).scalar_one_or_none()

            if not concept:
                continue

            # Create occurrence for story-level link
            occurrence = Occurrence(
                concept_id=concept_id,
                ref_type="story",
                ref_id=story_id,
                weight=1.0,
                is_verified=True,
            )
            session.add(occurrence)
            count += 1

    session.commit()
    return count


def create_segment_occurrences(session: Session) -> int:
    """Create occurrences linking concepts to segments via semantic_tags."""
    count = 0

    segments = session.execute(select(StorySegment)).scalars().all()

    for segment in segments:
        if not segment.semantic_tags:
            continue

        for tag in segment.semantic_tags:
            # Try to find matching concept
            concept_id = normalize_theme(tag) or normalize_figure(tag)

            if not concept_id:
                continue

            # Check if concept exists
            concept = session.execute(
                select(Concept).where(Concept.id == concept_id)
            ).scalar_one_or_none()

            if not concept:
                continue

            # Create occurrence for segment-level link
            occurrence = Occurrence(
                concept_id=concept_id,
                ref_type="segment",
                ref_id=segment.id,
                sura_no=segment.sura_no,
                ayah_start=segment.aya_start,
                ayah_end=segment.aya_end,
                weight=0.8,
                is_verified=False,  # Semantic tags are less verified
            )
            session.add(occurrence)
            count += 1

    session.commit()
    return count


def create_concept_associations(
    session: Session,
    story_concepts: Dict[str, List[str]]
) -> int:
    """
    Create associations between concepts that co-occur in stories.

    Evidence grounding: Co-occurrence in same story provides evidence.
    """
    count = 0

    # Build co-occurrence map
    concept_pairs: Dict[Tuple[str, str], List[str]] = defaultdict(list)

    for story_id, concept_ids in story_concepts.items():
        # Generate all pairs
        for i, concept_a in enumerate(concept_ids):
            for concept_b in concept_ids[i + 1:]:
                # Sort to ensure consistent ordering
                pair = tuple(sorted([concept_a, concept_b]))
                concept_pairs[pair].append(story_id)

    # Create associations for pairs that appear in multiple stories
    for (concept_a, concept_b), story_ids in concept_pairs.items():
        # Only create association if they appear together in at least one story
        if len(story_ids) < 1:
            continue

        # Check both concepts exist
        ca = session.execute(select(Concept).where(Concept.id == concept_a)).scalar_one_or_none()
        cb = session.execute(select(Concept).where(Concept.id == concept_b)).scalar_one_or_none()

        if not ca or not cb:
            continue

        # Determine relationship type based on concept types
        relation_type = determine_relation_type(ca.concept_type, cb.concept_type)

        # Calculate strength based on co-occurrence count
        strength = min(0.3 + (len(story_ids) * 0.1), 1.0)

        # Build evidence refs
        evidence_refs = {
            "ayah_refs": [],
            "story_refs": story_ids[:5],  # Limit to 5 stories
            "source": "story_cooccurrence"
        }

        association = Association(
            concept_a_id=concept_a,
            concept_b_id=concept_b,
            relation_type=relation_type,
            is_directional=False,
            strength=strength,
            evidence_refs=evidence_refs,
            has_sufficient_evidence=len(story_ids) >= 2,
            source="story_themes",
        )

        try:
            session.merge(association)
            count += 1
        except Exception:
            # Skip if duplicate
            session.rollback()
            continue

    session.commit()
    return count


def determine_relation_type(type_a: str, type_b: str) -> str:
    """Determine the relationship type between two concepts."""
    # Person + Person -> related
    if type_a == "person" and type_b == "person":
        return "related"

    # Person + Theme -> attribute_of
    if (type_a == "person" and type_b == "theme") or (type_a == "theme" and type_b == "person"):
        return "attribute_of"

    # Person + Miracle -> cause_effect (prophet caused miracle)
    if (type_a == "person" and type_b == "miracle") or (type_a == "miracle" and type_b == "person"):
        return "cause_effect"

    # Person + Nation -> related
    if (type_a == "person" and type_b == "nation") or (type_a == "nation" and type_b == "person"):
        return "related"

    # Theme + Theme -> similarity
    if type_a == "theme" and type_b == "theme":
        return "similarity"

    # Default to related
    return "related"


def link_miracles_to_persons(session: Session, curated: dict) -> int:
    """Create associations between miracles and their related persons."""
    count = 0

    for miracle in curated.get("miracles", []):
        miracle_id = miracle["id"]

        # Check if miracle concept exists
        miracle_concept = session.execute(
            select(Concept).where(Concept.id == miracle_id)
        ).scalar_one_or_none()

        if not miracle_concept:
            continue

        # Link to related persons
        for person_id in miracle.get("related_persons", []):
            person_concept = session.execute(
                select(Concept).where(Concept.id == person_id)
            ).scalar_one_or_none()

            if not person_concept:
                continue

            # Create association
            association = Association(
                concept_a_id=person_id,
                concept_b_id=miracle_id,
                relation_type="cause_effect",
                is_directional=True,
                strength=0.9,
                explanation_ar=f"معجزة {miracle_concept.label_ar}",
                explanation_en=f"Miracle of {miracle_concept.label_en}",
                evidence_refs={
                    "ayah_refs": [],
                    "source": "curated_dict"
                },
                has_sufficient_evidence=True,
                source="curated_dict",
            )

            try:
                session.merge(association)
                count += 1
            except Exception:
                session.rollback()
                continue

        # Link to related nations
        for nation_id in miracle.get("related_nations", []):
            nation_concept = session.execute(
                select(Concept).where(Concept.id == nation_id)
            ).scalar_one_or_none()

            if not nation_concept:
                continue

            association = Association(
                concept_a_id=miracle_id,
                concept_b_id=nation_id,
                relation_type="cause_effect",
                is_directional=True,
                strength=0.9,
                explanation_ar=f"عذاب {nation_concept.label_ar}",
                explanation_en=f"Punishment of {nation_concept.label_en}",
                evidence_refs={
                    "ayah_refs": [],
                    "source": "curated_dict"
                },
                has_sufficient_evidence=True,
                source="curated_dict",
            )

            try:
                session.merge(association)
                count += 1
            except Exception:
                session.rollback()
                continue

    session.commit()
    return count


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Seed Quran Concept Graph")
    parser.add_argument("--curated-only", action="store_true",
                       help="Only seed curated concepts, skip story extraction")
    parser.add_argument("--skip-associations", action="store_true",
                       help="Skip creating associations")
    parser.add_argument("--clear", action="store_true",
                       help="Clear existing concept data before seeding")
    args = parser.parse_args()

    print("=" * 60)
    print("QURAN CONCEPT GRAPH SEEDING")
    print("=" * 60)

    start_time = datetime.now()

    try:
        print("\n[1/6] Loading curated concepts...")
        curated = load_curated_concepts()
        print(f"  Loaded {len(curated.get('persons', []))} persons")
        print(f"  Loaded {len(curated.get('nations', []))} nations")
        print(f"  Loaded {len(curated.get('places', []))} places")
        print(f"  Loaded {len(curated.get('miracles', []))} miracles")
        print(f"  Loaded {len(curated.get('themes', []))} themes")
        print(f"  Loaded {len(curated.get('moral_patterns', []))} patterns")

        print("\n[2/6] Connecting to database...")
        engine = create_engine(get_db_url())

        with Session(engine) as session:
            # Optionally clear existing data
            if args.clear:
                print("\n  Clearing existing concept data...")
                session.execute(Association.__table__.delete())
                session.execute(Occurrence.__table__.delete())
                session.execute(Concept.__table__.delete())
                session.commit()
                print("  Cleared.")

            # Seed curated concepts
            print("\n[3/6] Seeding curated concepts...")
            concept_count = seed_curated_concepts(session, curated)
            print(f"  Seeded {concept_count} curated concepts")

            if not args.curated_only:
                # Extract concepts from stories
                print("\n[4/6] Extracting concepts from stories...")
                found_concepts, story_concepts = extract_concepts_from_stories(session)
                print(f"  Found {len(found_concepts)} unique concepts in stories")
                print(f"  Mapped concepts for {len(story_concepts)} stories")

                # Create story occurrences
                print("\n[5/6] Creating occurrences...")
                story_occ_count = create_story_occurrences(session, story_concepts)
                print(f"  Created {story_occ_count} story occurrences")

                segment_occ_count = create_segment_occurrences(session)
                print(f"  Created {segment_occ_count} segment occurrences")

                if not args.skip_associations:
                    # Create associations
                    print("\n[6/6] Creating associations...")
                    assoc_count = create_concept_associations(session, story_concepts)
                    print(f"  Created {assoc_count} concept associations")

                    # Link miracles to persons
                    miracle_link_count = link_miracles_to_persons(session, curated)
                    print(f"  Created {miracle_link_count} miracle-person associations")
                else:
                    print("\n[6/6] Skipping associations (--skip-associations)")
            else:
                print("\n[4-6/6] Skipping story extraction (--curated-only)")

            # Audit log
            AuditLog.log(
                session,
                action="data_import",
                actor="pipeline",
                entity_type="concept",
                message=f"Seeded {concept_count} concepts",
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )
            session.commit()

        duration = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print(f"SUCCESS: Concept seeding complete in {duration:.2f}s")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
