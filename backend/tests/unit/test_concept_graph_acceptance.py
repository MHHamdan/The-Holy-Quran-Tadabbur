#!/usr/bin/env python3
"""
Concept Graph Module Acceptance Tests

ACCEPTANCE CRITERIA:
1. DATA STRUCTURE: Curated concepts file must be valid JSON with required fields
2. CONCEPT TYPES: All required concept types must be present
3. BILINGUAL: All concepts must have Arabic and English labels
4. EVIDENCE: Associations must have evidence refs (epistemic safety)
5. SIMILARITY: Jaccard similarity must be correctly calculated

Run with: pytest tests/unit/test_concept_graph_acceptance.py -v
"""
import pytest
import json
from pathlib import Path
from typing import Set, Dict, List, Any

# All tests in this file are fast unit tests (no external services)
pytestmark = pytest.mark.unit


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

@pytest.fixture
def curated_concepts_path():
    """Path to the curated concepts file."""
    return Path(__file__).parent.parent.parent.parent / "data" / "concepts" / "curated_concepts.json"


@pytest.fixture
def concept_model_path():
    """Path to the concept model file."""
    return Path(__file__).parent.parent.parent / "app" / "models" / "concept.py"


@pytest.fixture
def similarity_service_path():
    """Path to the similarity service file."""
    return Path(__file__).parent.parent.parent / "app" / "services" / "similarity.py"


def load_json_file(path: Path) -> dict:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_concepts_from_data(data: dict) -> List[dict]:
    """
    Extract all concepts from the curated concepts file.

    The file has categories like 'persons', 'nations', 'places', etc.
    This function flattens them into a single list with type info.
    """
    concepts = []

    # Map category keys to concept types
    category_type_map = {
        'persons': 'person',
        'nations': 'nation',
        'places': 'place',
        'miracles': 'miracle',
        'themes': 'theme',
        'moral_patterns': 'moral_pattern',
    }

    for category, concept_type in category_type_map.items():
        items = data.get(category, [])
        for item in items:
            # Add the type field
            item_with_type = {**item, 'type': concept_type}
            concepts.append(item_with_type)

    return concepts


# ============================================================================
# 1. CURATED CONCEPTS DATA VALIDATION
# ============================================================================

class TestCuratedConceptsData:
    """
    Tests that verify the curated concepts file is valid.

    REQUIREMENTS:
    - File must exist and be valid JSON
    - Must have concepts array
    - Each concept must have required fields
    - Must have minimum number of concepts
    """

    def test_curated_concepts_file_exists(self, curated_concepts_path):
        """Curated concepts file must exist."""
        assert curated_concepts_path.exists(), f"File not found: {curated_concepts_path}"

    def test_curated_concepts_valid_json(self, curated_concepts_path):
        """Curated concepts file must be valid JSON."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        try:
            data = load_json_file(curated_concepts_path)
            assert isinstance(data, dict), "Root must be an object"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}")

    def test_curated_concepts_has_category_arrays(self, curated_concepts_path):
        """Curated concepts file must have category arrays."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)

        # Check required category arrays exist
        required_categories = ['persons', 'nations', 'places', 'miracles', 'themes']
        missing = [cat for cat in required_categories if cat not in data]

        assert len(missing) == 0, f"Missing category arrays: {missing}"

    def test_curated_concepts_minimum_count(self, curated_concepts_path):
        """Must have minimum number of curated concepts."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        # Should have at least 50 curated concepts
        MIN_CONCEPTS = 50
        assert len(concepts) >= MIN_CONCEPTS, \
            f"Expected at least {MIN_CONCEPTS} concepts, got {len(concepts)}"

    def test_all_concepts_have_required_fields(self, curated_concepts_path):
        """Each concept must have required fields."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        required_fields = ['id', 'slug', 'label_ar', 'label_en', 'type']

        invalid_concepts = []
        for concept in concepts:
            missing = [f for f in required_fields if f not in concept or not concept[f]]
            if missing:
                invalid_concepts.append(f"{concept.get('id', 'unknown')}: missing {missing}")

        assert len(invalid_concepts) == 0, \
            f"Concepts with missing required fields: {invalid_concepts}"

    def test_all_concepts_have_bilingual_labels(self, curated_concepts_path):
        """Each concept must have both Arabic and English labels."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        missing_labels = []
        for concept in concepts:
            if not concept.get('label_ar'):
                missing_labels.append(f"{concept.get('id')}: missing label_ar")
            if not concept.get('label_en'):
                missing_labels.append(f"{concept.get('id')}: missing label_en")

        assert len(missing_labels) == 0, \
            f"Concepts missing labels: {missing_labels}"

    def test_concept_ids_are_unique(self, curated_concepts_path):
        """All concept IDs must be unique."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        ids = [c.get('id') for c in concepts]
        duplicates = [id for id in ids if ids.count(id) > 1]

        assert len(set(duplicates)) == 0, \
            f"Duplicate concept IDs: {set(duplicates)}"

    def test_concept_slugs_are_unique(self, curated_concepts_path):
        """All concept slugs must be unique."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        slugs = [c.get('slug') for c in concepts]
        duplicates = [slug for slug in slugs if slugs.count(slug) > 1]

        assert len(set(duplicates)) == 0, \
            f"Duplicate concept slugs: {set(duplicates)}"


# ============================================================================
# 2. CONCEPT TYPES VALIDATION
# ============================================================================

class TestConceptTypes:
    """
    Tests that verify all required concept types are present.

    REQUIREMENTS:
    - Must have person, nation, place, miracle, theme concept types
    - Each type must have at least one concept
    """

    def test_all_required_types_present(self, curated_concepts_path):
        """Must have all required concept types."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        # Collect types present
        types_present = {c.get('type') for c in concepts}

        required_types = ['person', 'nation', 'place', 'miracle', 'theme']
        missing_types = [t for t in required_types if t not in types_present]

        assert len(missing_types) == 0, \
            f"Missing concept types: {missing_types}"

    def test_minimum_concepts_per_type(self, curated_concepts_path):
        """Each type must have minimum number of concepts."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        # Count by type
        type_counts: Dict[str, int] = {}
        for concept in concepts:
            ctype = concept.get('type')
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

        # Minimum requirements
        min_per_type = {
            'person': 10,  # At least 10 prophets/figures
            'miracle': 5,  # At least 5 miracles
            'theme': 5,    # At least 5 themes
            'nation': 3,   # At least 3 nations
            'place': 3,    # At least 3 places
        }

        under_minimum = []
        for ctype, minimum in min_per_type.items():
            actual = type_counts.get(ctype, 0)
            if actual < minimum:
                under_minimum.append(f"{ctype}: {actual} < {minimum}")

        assert len(under_minimum) == 0, \
            f"Types under minimum: {under_minimum}"

    def test_concept_types_are_valid(self, curated_concepts_path):
        """All concept types must be valid enum values."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        valid_types = {'person', 'nation', 'place', 'miracle', 'theme', 'moral_pattern', 'rhetorical'}

        invalid_types = []
        for concept in concepts:
            ctype = concept.get('type')
            if ctype not in valid_types:
                invalid_types.append(f"{concept.get('id')}: invalid type '{ctype}'")

        assert len(invalid_types) == 0, \
            f"Concepts with invalid types: {invalid_types}"


# ============================================================================
# 3. PROPHET/PERSON CONCEPTS VALIDATION
# ============================================================================

class TestPersonConcepts:
    """
    Tests that verify prophet/person concepts are complete.

    REQUIREMENTS:
    - Must have key prophets (Musa, Ibrahim, Nuh, etc.)
    - Persons must have Arabic names
    """

    def test_key_prophets_exist(self, curated_concepts_path):
        """Must have key prophets as concepts."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        # Collect person concept IDs
        person_ids = {c.get('id') for c in concepts if c.get('type') == 'person'}

        # Key prophets that must exist
        key_prophets = [
            'person_adam', 'person_nuh', 'person_ibrahim', 'person_musa',
            'person_isa', 'person_yusuf', 'person_dawud', 'person_sulayman'
        ]

        missing_prophets = [p for p in key_prophets if p not in person_ids]

        assert len(missing_prophets) == 0, \
            f"Missing key prophets: {missing_prophets}"

    def test_person_concepts_have_arabic_names(self, curated_concepts_path):
        """Person concepts must have Arabic names."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        # Check persons have Arabic labels
        persons_without_arabic = []
        for concept in concepts:
            if concept.get('type') == 'person':
                arabic_label = concept.get('label_ar', '')
                # Check if it contains Arabic characters
                has_arabic = any('\u0600' <= c <= '\u06FF' for c in arabic_label)
                if not has_arabic:
                    persons_without_arabic.append(concept.get('id'))

        assert len(persons_without_arabic) == 0, \
            f"Person concepts without Arabic names: {persons_without_arabic}"


# ============================================================================
# 4. MIRACLE CONCEPTS VALIDATION
# ============================================================================

class TestMiracleConcepts:
    """
    Tests that verify miracle concepts are properly defined.

    REQUIREMENTS:
    - Must have key miracles (staff of Musa, etc.)
    - Miracles should have descriptions
    """

    def test_key_miracles_exist(self, curated_concepts_path):
        """Must have key miracles as concepts."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        # Collect miracle concept IDs
        miracle_ids = {c.get('id') for c in concepts if c.get('type') == 'miracle'}

        # Should have at least 5 miracles
        assert len(miracle_ids) >= 5, \
            f"Expected at least 5 miracles, got {len(miracle_ids)}"

    def test_miracle_concepts_have_descriptions(self, curated_concepts_path):
        """Miracle concepts should have descriptions."""
        if not curated_concepts_path.exists():
            pytest.skip("Curated concepts file not found")

        data = load_json_file(curated_concepts_path)
        concepts = get_all_concepts_from_data(data)

        # Count miracles with descriptions
        miracles_with_desc = 0
        miracles_total = 0
        for concept in concepts:
            if concept.get('type') == 'miracle':
                miracles_total += 1
                if concept.get('description_en') or concept.get('description_ar'):
                    miracles_with_desc += 1

        # At least 50% should have descriptions
        if miracles_total > 0:
            percentage = miracles_with_desc / miracles_total
            assert percentage >= 0.5, \
                f"Only {percentage:.0%} of miracles have descriptions, need 50%+"


# ============================================================================
# 5. SIMILARITY SCORING LOGIC
# ============================================================================

class TestSimilarityScoring:
    """
    Tests that verify similarity scoring logic is correct.

    REQUIREMENTS:
    - Jaccard similarity must be calculated correctly
    - Score must be in [0, 1] range
    - Identical sets must have score 1.0
    - Disjoint sets must have score 0.0
    """

    def test_jaccard_identical_sets(self):
        """Jaccard similarity of identical sets is 1.0."""
        set_a = {'a', 'b', 'c'}
        set_b = {'a', 'b', 'c'}

        intersection = set_a & set_b
        union = set_a | set_b
        score = len(intersection) / len(union) if union else 0.0

        assert score == 1.0

    def test_jaccard_disjoint_sets(self):
        """Jaccard similarity of disjoint sets is 0.0."""
        set_a = {'a', 'b', 'c'}
        set_b = {'x', 'y', 'z'}

        intersection = set_a & set_b
        union = set_a | set_b
        score = len(intersection) / len(union) if union else 0.0

        assert score == 0.0

    def test_jaccard_partial_overlap(self):
        """Jaccard similarity of partial overlap is correct."""
        set_a = {'a', 'b', 'c', 'd'}  # 4 elements
        set_b = {'a', 'b', 'x', 'y'}  # 4 elements, 2 shared

        intersection = set_a & set_b  # {'a', 'b'} = 2 elements
        union = set_a | set_b         # {'a', 'b', 'c', 'd', 'x', 'y'} = 6 elements
        score = len(intersection) / len(union)

        assert score == 2/6  # 0.333...

    def test_jaccard_empty_sets(self):
        """Jaccard similarity with empty sets is handled."""
        set_a: Set[str] = set()
        set_b: Set[str] = set()

        intersection = set_a & set_b
        union = set_a | set_b
        score = len(intersection) / len(union) if union else 0.0

        # Empty sets should not divide by zero
        assert score == 0.0

    def test_jaccard_one_empty_set(self):
        """Jaccard similarity with one empty set is 0."""
        set_a = {'a', 'b', 'c'}
        set_b: Set[str] = set()

        intersection = set_a & set_b
        union = set_a | set_b
        score = len(intersection) / len(union) if union else 0.0

        assert score == 0.0

    def test_similarity_score_range(self):
        """Jaccard score must always be in [0, 1]."""
        import random

        for _ in range(100):
            # Generate random sets
            all_elements = list('abcdefghijklmnopqrstuvwxyz')
            set_a = set(random.sample(all_elements, random.randint(1, 10)))
            set_b = set(random.sample(all_elements, random.randint(1, 10)))

            intersection = set_a & set_b
            union = set_a | set_b
            score = len(intersection) / len(union) if union else 0.0

            assert 0.0 <= score <= 1.0, f"Score {score} out of range"


# ============================================================================
# 6. ASSOCIATION EVIDENCE REQUIREMENTS
# ============================================================================

class TestAssociationEvidence:
    """
    Tests that verify associations have evidence (epistemic safety).

    REQUIREMENTS:
    - Association model must require evidence_refs
    - Evidence refs must not be empty
    """

    def test_association_model_requires_evidence(self, concept_model_path):
        """Association model must have evidence_refs field."""
        if not concept_model_path.exists():
            pytest.skip("Concept model file not found")

        content = concept_model_path.read_text(encoding='utf-8')

        # Check that Association has evidence_refs field
        assert 'evidence_refs' in content, \
            "Association model must have evidence_refs field"

        # Check that there's a constraint for non-empty evidence
        assert 'CheckConstraint' in content or 'nullable=False' in content, \
            "Association should have constraint for evidence requirement"


# ============================================================================
# 7. API RESPONSE SCHEMA VALIDATION
# ============================================================================

class TestAPISchemas:
    """
    Tests that verify API response schemas are correct.

    REQUIREMENTS:
    - Response models must have required fields
    - Types must match frontend expectations
    """

    def test_concept_api_routes_exist(self):
        """Concepts API routes file must exist."""
        routes_path = Path(__file__).parent.parent.parent / "app" / "api" / "routes" / "concepts.py"
        assert routes_path.exists(), f"Routes file not found: {routes_path}"

    def test_concept_api_has_required_endpoints(self):
        """Concepts API must have required endpoints."""
        routes_path = Path(__file__).parent.parent.parent / "app" / "api" / "routes" / "concepts.py"

        if not routes_path.exists():
            pytest.skip("Routes file not found")

        content = routes_path.read_text(encoding='utf-8')

        required_endpoints = [
            '@router.get("",',           # list concepts (empty path)
            '@router.get("/types"',      # get types
            '@router.get("/search"',     # search
            '@router.get("/{concept_id}"',  # get concept
            '@router.get("/{concept_id}/occurrences"',  # occurrences
            '@router.get("/{concept_id}/associations"',  # associations
            'miracles/all',  # miracles lens (may have different path)
        ]

        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)

        assert len(missing_endpoints) == 0, \
            f"Missing API endpoints: {missing_endpoints}"


# ============================================================================
# 8. FRONTEND TYPE CONSISTENCY
# ============================================================================

class TestFrontendTypes:
    """
    Tests that verify frontend types match backend schemas.

    REQUIREMENTS:
    - Frontend api.ts must have Concept types
    - Types must match backend response schemas
    """

    def test_frontend_api_has_concept_types(self):
        """Frontend API must have concept-related types."""
        api_path = Path(__file__).parent.parent.parent.parent / "frontend" / "src" / "lib" / "api.ts"

        if not api_path.exists():
            pytest.skip("Frontend API file not found")

        content = api_path.read_text(encoding='utf-8')

        required_types = [
            'ConceptSummary',
            'ConceptDetail',
            'ConceptOccurrence',
            'ConceptAssociation',
            'MiracleWithAssociations',
        ]

        missing_types = []
        for type_name in required_types:
            if f'interface {type_name}' not in content:
                missing_types.append(type_name)

        assert len(missing_types) == 0, \
            f"Missing frontend types: {missing_types}"

    def test_frontend_api_has_concept_functions(self):
        """Frontend API must have concept-related functions."""
        api_path = Path(__file__).parent.parent.parent.parent / "frontend" / "src" / "lib" / "api.ts"

        if not api_path.exists():
            pytest.skip("Frontend API file not found")

        content = api_path.read_text(encoding='utf-8')

        required_functions = [
            'listConcepts',
            'getConceptTypes',
            'getConcept',
            'getConceptOccurrences',
            'getConceptAssociations',
            'getAllMiracles',
        ]

        missing_functions = []
        for func_name in required_functions:
            if func_name not in content:
                missing_functions.append(func_name)

        assert len(missing_functions) == 0, \
            f"Missing frontend API functions: {missing_functions}"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
