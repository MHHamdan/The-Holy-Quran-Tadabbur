"""
Semantic Search Service with Embedding-Based Similarity.

Provides advanced semantic search capabilities using vector embeddings
for contextual understanding of queries beyond keyword matching.

Features:
1. Semantic similarity scoring
2. Multi-dimensional thematic matching
3. Cross-lingual Arabic-English understanding
4. Context-aware query expansion
5. Theme clustering and discovery

Arabic: خدمة البحث الدلالي مع التشابه القائم على التضمين
"""

import logging
import math
import re
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# SEMANTIC EMBEDDINGS (Simplified TF-IDF + Theme Vectors)
# =============================================================================

class SemanticDimension(str, Enum):
    """Semantic dimensions for multi-dimensional matching."""
    THEMATIC = "thematic"           # Theme-based similarity
    MORAL = "moral"                 # Moral lesson similarity
    NARRATIVE = "narrative"         # Story structure similarity
    TEMPORAL = "temporal"           # Time-period relevance
    LINGUISTIC = "linguistic"       # Language pattern similarity
    CONTEXTUAL = "contextual"       # Contextual meaning similarity


@dataclass
class SemanticVector:
    """Semantic embedding vector for a text."""
    text_id: str
    theme_scores: Dict[str, float]
    concept_scores: Dict[str, float]
    moral_scores: Dict[str, float]
    entity_mentions: List[str]
    linguistic_features: Dict[str, float]


# Theme vocabulary with Arabic and English terms
THEME_VOCABULARY = {
    "patience": {
        "ar": ["صبر", "صابر", "اصبر", "الصابرين", "صبرا"],
        "en": ["patience", "patient", "endure", "persevere", "steadfast"],
        "related_concepts": ["trust", "hope", "gratitude"],
        "weight": 1.0,
    },
    "gratitude": {
        "ar": ["شكر", "شاكر", "شكور", "الشاكرين", "حمد"],
        "en": ["gratitude", "grateful", "thankful", "appreciate", "praise"],
        "related_concepts": ["patience", "worship", "contentment"],
        "weight": 1.0,
    },
    "trust_in_allah": {
        "ar": ["توكل", "متوكل", "وكيل", "التوكل"],
        "en": ["trust", "rely", "depend", "tawakkul", "reliance"],
        "related_concepts": ["faith", "patience", "submission"],
        "weight": 1.0,
    },
    "mercy": {
        "ar": ["رحمة", "رحيم", "رحمن", "الرحمة", "ارحم"],
        "en": ["mercy", "merciful", "compassion", "kindness", "clemency"],
        "related_concepts": ["forgiveness", "love", "kindness"],
        "weight": 1.0,
    },
    "forgiveness": {
        "ar": ["مغفرة", "غفور", "استغفر", "غفران", "عفو"],
        "en": ["forgiveness", "pardon", "forgive", "repent", "absolution"],
        "related_concepts": ["mercy", "repentance", "hope"],
        "weight": 1.0,
    },
    "justice": {
        "ar": ["عدل", "قسط", "ميزان", "العدل", "إنصاف"],
        "en": ["justice", "fair", "equity", "balance", "righteous"],
        "related_concepts": ["truth", "judgment", "accountability"],
        "weight": 1.0,
    },
    "faith": {
        "ar": ["إيمان", "مؤمن", "آمن", "الإيمان", "تقوى"],
        "en": ["faith", "belief", "believe", "faithful", "piety"],
        "related_concepts": ["trust", "worship", "submission"],
        "weight": 1.0,
    },
    "repentance": {
        "ar": ["توبة", "تائب", "تاب", "التوبة", "أناب"],
        "en": ["repentance", "repent", "return", "remorse", "tawbah"],
        "related_concepts": ["forgiveness", "hope", "mercy"],
        "weight": 1.0,
    },
    "guidance": {
        "ar": ["هداية", "هدى", "اهدنا", "مهتدي", "رشد"],
        "en": ["guidance", "guide", "path", "direction", "lead"],
        "related_concepts": ["light", "truth", "knowledge"],
        "weight": 1.0,
    },
    "knowledge": {
        "ar": ["علم", "عالم", "يعلم", "العلم", "حكمة"],
        "en": ["knowledge", "wisdom", "learn", "understand", "intellect"],
        "related_concepts": ["guidance", "light", "truth"],
        "weight": 1.0,
    },
    "worship": {
        "ar": ["عبادة", "عبد", "اعبد", "العبادة", "سجد"],
        "en": ["worship", "devotion", "prayer", "prostrate", "serve"],
        "related_concepts": ["faith", "submission", "obedience"],
        "weight": 1.0,
    },
    "submission": {
        "ar": ["إسلام", "مسلم", "أسلم", "الإسلام", "خضوع"],
        "en": ["submission", "surrender", "islam", "submit", "yield"],
        "related_concepts": ["worship", "faith", "obedience"],
        "weight": 1.0,
    },
    "truth": {
        "ar": ["حق", "صدق", "الحق", "صادق", "يقين"],
        "en": ["truth", "true", "reality", "honest", "certainty"],
        "related_concepts": ["justice", "guidance", "knowledge"],
        "weight": 1.0,
    },
    "hope": {
        "ar": ["رجاء", "أمل", "رجا", "الرجاء", "طمع"],
        "en": ["hope", "aspiration", "expectation", "optimism", "wish"],
        "related_concepts": ["mercy", "patience", "trust"],
        "weight": 1.0,
    },
    "fear_of_allah": {
        "ar": ["تقوى", "خوف", "خشية", "اتقوا", "المتقين"],
        "en": ["fear", "awe", "taqwa", "reverence", "consciousness"],
        "related_concepts": ["worship", "obedience", "accountability"],
        "weight": 1.0,
    },
    "love": {
        "ar": ["حب", "محبة", "ود", "الحب", "يحب"],
        "en": ["love", "affection", "devotion", "beloved", "cherish"],
        "related_concepts": ["mercy", "kindness", "faith"],
        "weight": 1.0,
    },
    "sacrifice": {
        "ar": ["تضحية", "أضحى", "فداء", "ضحى", "بذل"],
        "en": ["sacrifice", "offering", "give", "dedicate", "ransom"],
        "related_concepts": ["faith", "submission", "love"],
        "weight": 1.0,
    },
    "liberation": {
        "ar": ["تحرير", "حرية", "نجاة", "خلاص", "إنقاذ"],
        "en": ["liberation", "freedom", "salvation", "rescue", "deliverance"],
        "related_concepts": ["justice", "victory", "guidance"],
        "weight": 1.0,
    },
    "victory": {
        "ar": ["نصر", "فتح", "ظفر", "النصر", "غلبة"],
        "en": ["victory", "triumph", "conquest", "success", "win"],
        "related_concepts": ["patience", "faith", "liberation"],
        "weight": 1.0,
    },
    "punishment": {
        "ar": ["عذاب", "عقاب", "نقمة", "العذاب", "بأس"],
        "en": ["punishment", "retribution", "torment", "penalty", "chastisement"],
        "related_concepts": ["justice", "accountability", "warning"],
        "weight": 1.0,
    },
}

# Moral lesson vocabulary
MORAL_VOCABULARY = {
    "patience_rewarded": {
        "keywords": ["patience", "reward", "relief", "after hardship", "صبر", "فرج", "أجر"],
        "related_morals": ["trust_in_plan", "gratitude_after_trial"],
    },
    "trust_in_plan": {
        "keywords": ["plan", "decree", "trust", "divine", "قدر", "توكل", "تدبير"],
        "related_morals": ["patience_rewarded", "submission_to_will"],
    },
    "forgiveness_virtue": {
        "keywords": ["forgive", "pardon", "better", "virtue", "عفو", "مغفرة", "فضيلة"],
        "related_morals": ["mercy_over_revenge", "patience_rewarded"],
    },
    "justice_prevails": {
        "keywords": ["justice", "truth", "prevail", "victory", "عدل", "حق", "نصر"],
        "related_morals": ["patience_rewarded", "accountability"],
    },
    "humility_before_allah": {
        "keywords": ["humble", "arrogance", "pride", "تواضع", "كبر", "خشوع"],
        "related_morals": ["worship_sincerity", "fear_of_allah"],
    },
}

# Prophet story embeddings
PROPHET_STORY_EMBEDDINGS = {
    "musa": {
        "primary_themes": ["liberation", "patience", "faith", "justice"],
        "moral_lessons": ["patience_rewarded", "justice_prevails", "trust_in_plan"],
        "narrative_elements": ["confrontation", "exodus", "miracles", "leadership"],
        "temporal_context": "ancient_egypt",
    },
    "ibrahim": {
        "primary_themes": ["sacrifice", "faith", "submission", "truth"],
        "moral_lessons": ["trust_in_plan", "submission_to_will", "courage_for_truth"],
        "narrative_elements": ["rejection_of_idols", "sacrifice_test", "migration", "building_kaaba"],
        "temporal_context": "mesopotamia_canaan",
    },
    "yusuf": {
        "primary_themes": ["patience", "forgiveness", "trust_in_allah", "truth"],
        "moral_lessons": ["patience_rewarded", "forgiveness_virtue", "trust_in_plan"],
        "narrative_elements": ["betrayal", "temptation", "imprisonment", "elevation", "reconciliation"],
        "temporal_context": "ancient_egypt",
    },
    "nuh": {
        "primary_themes": ["patience", "faith", "warning", "salvation"],
        "moral_lessons": ["patience_rewarded", "faith_over_family", "persistence_in_dawah"],
        "narrative_elements": ["long_dawah", "ark_building", "flood", "new_beginning"],
        "temporal_context": "antediluvian",
    },
    "isa": {
        "primary_themes": ["mercy", "truth", "faith", "miracles"],
        "moral_lessons": ["humility_before_allah", "truth_over_falsehood"],
        "narrative_elements": ["miraculous_birth", "healing", "opposition", "ascension"],
        "temporal_context": "roman_palestine",
    },
    "muhammad": {
        "primary_themes": ["mercy", "guidance", "faith", "justice", "patience"],
        "moral_lessons": ["patience_rewarded", "mercy_to_all", "justice_prevails"],
        "narrative_elements": ["revelation", "persecution", "migration", "victories", "final_message"],
        "temporal_context": "7th_century_arabia",
    },
}


# =============================================================================
# SEMANTIC SEARCH SERVICE
# =============================================================================

class SemanticSearchService:
    """
    Advanced semantic search with embedding-based similarity.

    Features:
    - Multi-dimensional semantic matching
    - Theme-based similarity scoring
    - Cross-lingual understanding
    - Context-aware query expansion
    - Narrative structure matching
    """

    def __init__(self):
        self._theme_vocab = THEME_VOCABULARY
        self._moral_vocab = MORAL_VOCABULARY
        self._prophet_embeddings = PROPHET_STORY_EMBEDDINGS
        self._search_cache: Dict[str, Dict[str, Any]] = {}
        self._user_search_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def _compute_text_embedding(self, text: str) -> SemanticVector:
        """Compute semantic embedding for a text."""
        text_lower = text.lower()
        text_id = hashlib.md5(text.encode()).hexdigest()[:12]

        # Compute theme scores
        theme_scores = {}
        for theme_id, theme_data in self._theme_vocab.items():
            score = 0.0
            # Check Arabic terms
            for term in theme_data["ar"]:
                if term in text:
                    score += 1.0
            # Check English terms
            for term in theme_data["en"]:
                if term in text_lower:
                    score += 1.0
            if score > 0:
                theme_scores[theme_id] = min(1.0, score / 3.0)  # Normalize

        # Compute concept scores (related themes)
        concept_scores = {}
        for theme_id, score in theme_scores.items():
            related = self._theme_vocab[theme_id].get("related_concepts", [])
            for concept in related:
                if concept in concept_scores:
                    concept_scores[concept] = max(concept_scores[concept], score * 0.5)
                else:
                    concept_scores[concept] = score * 0.5

        # Compute moral scores
        moral_scores = {}
        for moral_id, moral_data in self._moral_vocab.items():
            score = 0.0
            for kw in moral_data["keywords"]:
                if kw.lower() in text_lower or kw in text:
                    score += 1.0
            if score > 0:
                moral_scores[moral_id] = min(1.0, score / len(moral_data["keywords"]))

        # Extract entity mentions
        entity_mentions = []
        prophet_names_ar = ["موسى", "إبراهيم", "يوسف", "نوح", "عيسى", "محمد", "آدم", "داود", "سليمان"]
        prophet_names_en = ["moses", "abraham", "joseph", "noah", "jesus", "muhammad", "adam", "david", "solomon"]
        for name in prophet_names_ar + prophet_names_en:
            if name.lower() in text_lower or name in text:
                entity_mentions.append(name)

        # Linguistic features
        linguistic_features = {
            "word_count": len(text.split()),
            "arabic_ratio": len(re.findall(r'[\u0600-\u06FF]', text)) / max(1, len(text)),
            "question_form": 1.0 if "?" in text or "؟" in text else 0.0,
        }

        return SemanticVector(
            text_id=text_id,
            theme_scores=theme_scores,
            concept_scores=concept_scores,
            moral_scores=moral_scores,
            entity_mentions=entity_mentions,
            linguistic_features=linguistic_features,
        )

    def _compute_similarity(
        self,
        vec1: SemanticVector,
        vec2: SemanticVector,
        dimensions: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Compute multi-dimensional similarity between two vectors."""
        if dimensions is None:
            dimensions = ["thematic", "moral", "conceptual", "entity"]

        scores = {}

        # Thematic similarity
        if "thematic" in dimensions:
            common_themes = set(vec1.theme_scores.keys()) & set(vec2.theme_scores.keys())
            if common_themes:
                theme_sim = sum(
                    min(vec1.theme_scores[t], vec2.theme_scores[t])
                    for t in common_themes
                ) / max(len(vec1.theme_scores), len(vec2.theme_scores), 1)
            else:
                theme_sim = 0.0
            scores["thematic"] = theme_sim

        # Moral similarity
        if "moral" in dimensions:
            common_morals = set(vec1.moral_scores.keys()) & set(vec2.moral_scores.keys())
            if common_morals:
                moral_sim = sum(
                    min(vec1.moral_scores[m], vec2.moral_scores[m])
                    for m in common_morals
                ) / max(len(vec1.moral_scores), len(vec2.moral_scores), 1)
            else:
                moral_sim = 0.0
            scores["moral"] = moral_sim

        # Conceptual similarity
        if "conceptual" in dimensions:
            all_concepts = set(vec1.concept_scores.keys()) | set(vec2.concept_scores.keys())
            if all_concepts:
                concept_sim = sum(
                    min(vec1.concept_scores.get(c, 0), vec2.concept_scores.get(c, 0))
                    for c in all_concepts
                ) / len(all_concepts)
            else:
                concept_sim = 0.0
            scores["conceptual"] = concept_sim

        # Entity overlap
        if "entity" in dimensions:
            common_entities = set(vec1.entity_mentions) & set(vec2.entity_mentions)
            all_entities = set(vec1.entity_mentions) | set(vec2.entity_mentions)
            entity_sim = len(common_entities) / max(len(all_entities), 1)
            scores["entity"] = entity_sim

        # Overall similarity (weighted average)
        weights = {"thematic": 0.4, "moral": 0.25, "conceptual": 0.2, "entity": 0.15}
        overall = sum(scores.get(d, 0) * weights.get(d, 0.25) for d in dimensions)
        scores["overall"] = overall

        return scores

    def semantic_search(
        self,
        query: str,
        content_items: List[Dict[str, Any]],
        dimensions: Optional[List[str]] = None,
        min_score: float = 0.1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Perform semantic search across content items.

        Args:
            query: Search query
            content_items: List of items with 'id' and 'text' keys
            dimensions: Which dimensions to consider
            min_score: Minimum similarity score threshold
            limit: Maximum results to return
        """
        query_vector = self._compute_text_embedding(query)

        results = []
        for item in content_items:
            item_vector = self._compute_text_embedding(item.get("text", ""))
            similarity = self._compute_similarity(query_vector, item_vector, dimensions)

            if similarity["overall"] >= min_score:
                results.append({
                    "item_id": item.get("id"),
                    "text_preview": item.get("text", "")[:200],
                    "similarity_scores": similarity,
                    "overall_score": similarity["overall"],
                    "matched_themes": list(
                        set(query_vector.theme_scores.keys()) &
                        set(item_vector.theme_scores.keys())
                    ),
                    "matched_entities": list(
                        set(query_vector.entity_mentions) &
                        set(item_vector.entity_mentions)
                    ),
                })

        # Sort by overall score
        results.sort(key=lambda x: x["overall_score"], reverse=True)

        return {
            "query": query,
            "query_analysis": {
                "detected_themes": list(query_vector.theme_scores.keys()),
                "detected_morals": list(query_vector.moral_scores.keys()),
                "detected_entities": query_vector.entity_mentions,
            },
            "results": results[:limit],
            "total_matches": len(results),
        }

    def find_similar_themes(
        self,
        theme: str,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find themes semantically similar to the given theme."""
        if theme not in self._theme_vocab:
            # Try to find by partial match
            matching = [t for t in self._theme_vocab if theme.lower() in t.lower()]
            if matching:
                theme = matching[0]
            else:
                return []

        base_theme = self._theme_vocab[theme]
        related = base_theme.get("related_concepts", [])

        results = []
        for related_theme in related:
            if related_theme in self._theme_vocab:
                results.append({
                    "theme_id": related_theme,
                    "theme_data": self._theme_vocab[related_theme],
                    "relationship": "directly_related",
                    "strength": 0.8,
                })

        # Find themes with overlapping related concepts
        for other_theme, other_data in self._theme_vocab.items():
            if other_theme == theme:
                continue
            other_related = set(other_data.get("related_concepts", []))
            overlap = set(related) & other_related
            if overlap and other_theme not in [r["theme_id"] for r in results]:
                results.append({
                    "theme_id": other_theme,
                    "theme_data": other_data,
                    "relationship": "concept_overlap",
                    "shared_concepts": list(overlap),
                    "strength": len(overlap) * 0.3,
                })

        # Sort by strength
        results.sort(key=lambda x: x["strength"], reverse=True)
        return results[:top_n]

    def find_similar_prophet_stories(
        self,
        prophet: str,
        similarity_type: str = "all",  # all, thematic, moral, narrative
    ) -> List[Dict[str, Any]]:
        """Find prophet stories similar to the given prophet's story."""
        prophet_lower = prophet.lower()

        # Map Arabic names to keys
        name_mapping = {
            "موسى": "musa", "musa": "musa", "moses": "musa",
            "إبراهيم": "ibrahim", "ibrahim": "ibrahim", "abraham": "ibrahim",
            "يوسف": "yusuf", "yusuf": "yusuf", "joseph": "yusuf",
            "نوح": "nuh", "nuh": "nuh", "noah": "nuh",
            "عيسى": "isa", "isa": "isa", "jesus": "isa",
            "محمد": "muhammad", "muhammad": "muhammad",
        }

        prophet_key = name_mapping.get(prophet_lower)
        if not prophet_key or prophet_key not in self._prophet_embeddings:
            return []

        base_story = self._prophet_embeddings[prophet_key]
        results = []

        for other_key, other_story in self._prophet_embeddings.items():
            if other_key == prophet_key:
                continue

            similarity = {}

            # Thematic similarity
            if similarity_type in ["all", "thematic"]:
                common_themes = set(base_story["primary_themes"]) & set(other_story["primary_themes"])
                all_themes = set(base_story["primary_themes"]) | set(other_story["primary_themes"])
                similarity["thematic"] = len(common_themes) / len(all_themes) if all_themes else 0

            # Moral similarity
            if similarity_type in ["all", "moral"]:
                common_morals = set(base_story["moral_lessons"]) & set(other_story["moral_lessons"])
                all_morals = set(base_story["moral_lessons"]) | set(other_story["moral_lessons"])
                similarity["moral"] = len(common_morals) / len(all_morals) if all_morals else 0

            # Narrative similarity
            if similarity_type in ["all", "narrative"]:
                common_elements = set(base_story["narrative_elements"]) & set(other_story["narrative_elements"])
                all_elements = set(base_story["narrative_elements"]) | set(other_story["narrative_elements"])
                similarity["narrative"] = len(common_elements) / len(all_elements) if all_elements else 0

            # Overall
            if similarity:
                overall = sum(similarity.values()) / len(similarity)
                results.append({
                    "prophet": other_key,
                    "similarity_scores": similarity,
                    "overall_similarity": overall,
                    "shared_themes": list(set(base_story["primary_themes"]) & set(other_story["primary_themes"])),
                    "shared_morals": list(set(base_story["moral_lessons"]) & set(other_story["moral_lessons"])),
                    "shared_narrative_elements": list(
                        set(base_story["narrative_elements"]) & set(other_story["narrative_elements"])
                    ),
                })

        results.sort(key=lambda x: x["overall_similarity"], reverse=True)
        return results

    def expand_query(
        self,
        query: str,
        expansion_type: str = "semantic",  # semantic, synonym, thematic
    ) -> Dict[str, Any]:
        """Expand query with semantically related terms."""
        query_vector = self._compute_text_embedding(query)

        expansions = {
            "original_query": query,
            "detected_themes": list(query_vector.theme_scores.keys()),
            "theme_expansions": [],
            "related_terms_ar": [],
            "related_terms_en": [],
            "suggested_queries": [],
        }

        # Expand based on detected themes
        for theme in query_vector.theme_scores.keys():
            theme_data = self._theme_vocab.get(theme, {})
            expansions["related_terms_ar"].extend(theme_data.get("ar", []))
            expansions["related_terms_en"].extend(theme_data.get("en", []))

            # Add related themes
            for related in theme_data.get("related_concepts", []):
                if related in self._theme_vocab:
                    expansions["theme_expansions"].append({
                        "theme": related,
                        "terms_ar": self._theme_vocab[related].get("ar", [])[:3],
                        "terms_en": self._theme_vocab[related].get("en", [])[:3],
                    })

        # Generate suggested queries
        if query_vector.theme_scores:
            top_theme = max(query_vector.theme_scores, key=query_vector.theme_scores.get)
            expansions["suggested_queries"] = [
                f"{query} in Quran",
                f"Prophet stories about {top_theme}",
                f"Lessons of {top_theme} from Quran",
            ]

        # Deduplicate
        expansions["related_terms_ar"] = list(set(expansions["related_terms_ar"]))
        expansions["related_terms_en"] = list(set(expansions["related_terms_en"]))

        return expansions

    def cluster_themes(
        self,
        themes: List[str],
    ) -> Dict[str, List[str]]:
        """Cluster themes based on semantic similarity."""
        if not themes:
            return {}

        # Build theme graph based on relationships
        theme_clusters = defaultdict(list)

        for theme in themes:
            if theme not in self._theme_vocab:
                continue

            # Assign to cluster based on related concepts
            related = self._theme_vocab[theme].get("related_concepts", [])

            # Find best cluster
            best_cluster = None
            best_overlap = 0

            for cluster_name, cluster_themes in theme_clusters.items():
                cluster_related = set()
                for ct in cluster_themes:
                    cluster_related.update(self._theme_vocab.get(ct, {}).get("related_concepts", []))

                overlap = len(set(related) & cluster_related)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_cluster = cluster_name

            if best_cluster and best_overlap >= 1:
                theme_clusters[best_cluster].append(theme)
            else:
                # Create new cluster
                cluster_name = f"cluster_{theme}"
                theme_clusters[cluster_name].append(theme)

        return dict(theme_clusters)

    def record_search(
        self,
        user_id: str,
        query: str,
        results_count: int,
    ) -> None:
        """Record a user's search for personalization."""
        query_vector = self._compute_text_embedding(query)

        self._user_search_history[user_id].append({
            "query": query,
            "detected_themes": list(query_vector.theme_scores.keys()),
            "detected_morals": list(query_vector.moral_scores.keys()),
            "detected_entities": query_vector.entity_mentions,
            "results_count": results_count,
            "timestamp": datetime.now().isoformat(),
        })

        # Keep only last 100 searches
        if len(self._user_search_history[user_id]) > 100:
            self._user_search_history[user_id] = self._user_search_history[user_id][-100:]

    def get_user_theme_preferences(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get user's theme preferences based on search history."""
        if user_id not in self._user_search_history:
            return {"user_id": user_id, "has_history": False}

        history = self._user_search_history[user_id]

        # Aggregate theme frequencies
        theme_freq = defaultdict(int)
        moral_freq = defaultdict(int)
        entity_freq = defaultdict(int)

        for search in history:
            for theme in search.get("detected_themes", []):
                theme_freq[theme] += 1
            for moral in search.get("detected_morals", []):
                moral_freq[moral] += 1
            for entity in search.get("detected_entities", []):
                entity_freq[entity] += 1

        return {
            "user_id": user_id,
            "has_history": True,
            "search_count": len(history),
            "top_themes": sorted(theme_freq.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_morals": sorted(moral_freq.items(), key=lambda x: x[1], reverse=True)[:3],
            "top_entities": sorted(entity_freq.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Get all available themes with their vocabulary."""
        return [
            {
                "theme_id": theme_id,
                "terms_ar": data["ar"][:3],
                "terms_en": data["en"][:3],
                "related_concepts": data.get("related_concepts", []),
            }
            for theme_id, data in self._theme_vocab.items()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "total_themes": len(self._theme_vocab),
            "total_morals": len(self._moral_vocab),
            "prophet_embeddings": len(self._prophet_embeddings),
            "cached_searches": len(self._search_cache),
            "users_with_history": len(self._user_search_history),
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

semantic_search_service = SemanticSearchService()
