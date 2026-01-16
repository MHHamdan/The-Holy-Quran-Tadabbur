"""
Expanded Knowledge Graph Service with Islamic History and Dynamic Exploration.

Features:
1. Comprehensive Islamic history timeline
2. Dynamic entity exploration
3. Graph-based connections
4. Historical era mapping
5. Event causality chains
6. Visualization data generation

Arabic: خدمة الرسم البياني المعرفي الموسع مع التاريخ الإسلامي والاستكشاف الديناميكي
"""

import logging
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class HistoricalEra(str, Enum):
    """Historical eras in Islamic history."""
    PRE_PROPHETIC = "pre_prophetic"          # Before Prophet Muhammad
    MAKKAN = "makkan"                        # Makkan period
    MADINAN = "madinan"                      # Madinan period
    KHULAFA_RASHIDUN = "khulafa_rashidun"    # Rightly guided caliphs
    UMAYYAD = "umayyad"                      # Umayyad dynasty
    ABBASID = "abbasid"                      # Abbasid dynasty
    SUBSEQUENT = "subsequent"                # Later periods


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    PROPHET = "prophet"
    COMPANION = "companion"
    SCHOLAR = "scholar"
    PLACE = "place"
    EVENT = "event"
    CONCEPT = "concept"
    REVELATION = "revelation"
    NATION = "nation"
    DYNASTY = "dynasty"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    FATHER_OF = "father_of"
    SON_OF = "son_of"
    WIFE_OF = "wife_of"
    HUSBAND_OF = "husband_of"
    TEACHER_OF = "teacher_of"
    STUDENT_OF = "student_of"
    COMPANION_OF = "companion_of"
    PRECEDED = "preceded"
    SUCCEEDED = "succeeded"
    OCCURRED_AT = "occurred_at"
    REVEALED_IN = "revealed_in"
    RELATED_TO = "related_to"
    CAUSED = "caused"
    RESULTED_FROM = "resulted_from"
    CONTEMPORARY_OF = "contemporary_of"
    OPPOSED = "opposed"


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    node_id: str
    name_ar: str
    name_en: str
    entity_type: EntityType
    era: Optional[HistoricalEra]
    attributes: Dict[str, Any]
    quranic_references: List[str]


@dataclass
class GraphEdge:
    """An edge connecting two nodes."""
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float
    evidence: List[str]


# =============================================================================
# KNOWLEDGE GRAPH DATA
# =============================================================================

HISTORICAL_TIMELINE = {
    "pre_prophetic": {
        "era_name_ar": "ما قبل البعثة",
        "era_name_en": "Pre-Prophetic Era",
        "date_range": "Creation - 610 CE",
        "events": [
            {
                "event_id": "creation_adam",
                "name_ar": "خلق آدم",
                "name_en": "Creation of Adam",
                "description": "Allah created Adam as the first human and prophet",
                "quranic_refs": ["2:30-39", "7:11-25", "15:28-44"],
                "key_figures": ["آدم"],
            },
            {
                "event_id": "flood_nuh",
                "name_ar": "طوفان نوح",
                "name_en": "The Great Flood",
                "description": "The flood that destroyed disbelievers in time of Nuh",
                "quranic_refs": ["11:25-49", "71:1-28", "54:9-17"],
                "key_figures": ["نوح"],
            },
            {
                "event_id": "ibrahim_migration",
                "name_ar": "هجرة إبراهيم",
                "name_en": "Ibrahim's Migration",
                "description": "Ibrahim's migration from Mesopotamia to Canaan",
                "quranic_refs": ["29:26", "21:71"],
                "key_figures": ["إبراهيم"],
            },
            {
                "event_id": "kaaba_construction",
                "name_ar": "بناء الكعبة",
                "name_en": "Building of the Kaaba",
                "description": "Ibrahim and Ismail building the Kaaba",
                "quranic_refs": ["2:125-129"],
                "key_figures": ["إبراهيم", "إسماعيل"],
            },
            {
                "event_id": "exodus",
                "name_ar": "خروج بني إسرائيل من مصر",
                "name_en": "Exodus from Egypt",
                "description": "Musa leading Bani Israel out of Egypt",
                "quranic_refs": ["26:52-68", "7:136-141"],
                "key_figures": ["موسى", "فرعون"],
            },
            {
                "event_id": "dawud_kingdom",
                "name_ar": "مملكة داود",
                "name_en": "Kingdom of Dawud",
                "description": "Dawud's reign and the zabur",
                "quranic_refs": ["38:17-26", "21:78-80"],
                "key_figures": ["داود"],
            },
            {
                "event_id": "sulayman_kingdom",
                "name_ar": "مملكة سليمان",
                "name_en": "Kingdom of Sulayman",
                "description": "Sulayman's reign with control over jinn and animals",
                "quranic_refs": ["27:15-44", "38:30-40"],
                "key_figures": ["سليمان"],
            },
            {
                "event_id": "isa_mission",
                "name_ar": "رسالة عيسى",
                "name_en": "Mission of Isa",
                "description": "Isa's prophethood to Bani Israel",
                "quranic_refs": ["3:45-60", "5:110-120"],
                "key_figures": ["عيسى", "مريم"],
            },
            {
                "event_id": "year_elephant",
                "name_ar": "عام الفيل",
                "name_en": "Year of the Elephant",
                "description": "Abraha's failed attack on Kaaba, year of Prophet's birth",
                "quranic_refs": ["105:1-5"],
                "key_figures": [],
            },
        ],
    },
    "makkan": {
        "era_name_ar": "العهد المكي",
        "era_name_en": "Makkan Period",
        "date_range": "610 - 622 CE",
        "events": [
            {
                "event_id": "first_revelation",
                "name_ar": "نزول الوحي",
                "name_en": "First Revelation",
                "description": "First revelation to Prophet Muhammad in Cave Hira",
                "quranic_refs": ["96:1-5"],
                "key_figures": ["محمد ﷺ", "جبريل"],
            },
            {
                "event_id": "isra_miraj",
                "name_ar": "الإسراء والمعراج",
                "name_en": "The Night Journey",
                "description": "Journey from Makkah to Jerusalem and ascension to heavens",
                "quranic_refs": ["17:1", "53:1-18"],
                "key_figures": ["محمد ﷺ", "جبريل"],
            },
            {
                "event_id": "first_hijra",
                "name_ar": "الهجرة إلى الحبشة",
                "name_en": "Migration to Abyssinia",
                "description": "First migration of Muslims to escape persecution",
                "quranic_refs": [],
                "key_figures": ["جعفر بن أبي طالب"],
            },
            {
                "event_id": "boycott",
                "name_ar": "حصار شعب بني هاشم",
                "name_en": "Boycott of Banu Hashim",
                "description": "Three-year boycott against Muslims",
                "quranic_refs": [],
                "key_figures": ["محمد ﷺ", "أبو طالب"],
            },
            {
                "event_id": "year_of_sorrow",
                "name_ar": "عام الحزن",
                "name_en": "Year of Sorrow",
                "description": "Deaths of Khadijah and Abu Talib",
                "quranic_refs": [],
                "key_figures": ["خديجة", "أبو طالب"],
            },
            {
                "event_id": "pledges_aqaba",
                "name_ar": "بيعة العقبة",
                "name_en": "Pledges of Aqaba",
                "description": "Muslims from Madinah pledge allegiance",
                "quranic_refs": [],
                "key_figures": ["الأنصار"],
            },
        ],
    },
    "madinan": {
        "era_name_ar": "العهد المدني",
        "era_name_en": "Madinan Period",
        "date_range": "622 - 632 CE",
        "events": [
            {
                "event_id": "hijra",
                "name_ar": "الهجرة النبوية",
                "name_en": "The Hijra",
                "description": "Prophet's migration from Makkah to Madinah",
                "quranic_refs": ["9:40"],
                "key_figures": ["محمد ﷺ", "أبو بكر"],
            },
            {
                "event_id": "brotherhood",
                "name_ar": "المؤاخاة",
                "name_en": "Brotherhood of Emigrants and Helpers",
                "description": "Pairing of Muhajirun and Ansar",
                "quranic_refs": ["8:72-75"],
                "key_figures": ["المهاجرون", "الأنصار"],
            },
            {
                "event_id": "battle_badr",
                "name_ar": "غزوة بدر",
                "name_en": "Battle of Badr",
                "description": "First major battle, Muslim victory",
                "quranic_refs": ["8:5-19", "3:123-127"],
                "key_figures": ["محمد ﷺ"],
            },
            {
                "event_id": "battle_uhud",
                "name_ar": "غزوة أحد",
                "name_en": "Battle of Uhud",
                "description": "Second major battle with partial defeat",
                "quranic_refs": ["3:121-175"],
                "key_figures": ["محمد ﷺ", "حمزة"],
            },
            {
                "event_id": "battle_khandaq",
                "name_ar": "غزوة الخندق",
                "name_en": "Battle of the Trench",
                "description": "Siege of Madinah by Quraysh coalition",
                "quranic_refs": ["33:9-27"],
                "key_figures": ["محمد ﷺ", "سلمان الفارسي"],
            },
            {
                "event_id": "hudaybiyyah",
                "name_ar": "صلح الحديبية",
                "name_en": "Treaty of Hudaybiyyah",
                "description": "Peace treaty with Quraysh",
                "quranic_refs": ["48:1-29"],
                "key_figures": ["محمد ﷺ"],
            },
            {
                "event_id": "conquest_makkah",
                "name_ar": "فتح مكة",
                "name_en": "Conquest of Makkah",
                "description": "Peaceful conquest of Makkah",
                "quranic_refs": ["110:1-3"],
                "key_figures": ["محمد ﷺ"],
            },
            {
                "event_id": "farewell_pilgrimage",
                "name_ar": "حجة الوداع",
                "name_en": "Farewell Pilgrimage",
                "description": "Prophet's final Hajj and sermon",
                "quranic_refs": ["5:3"],
                "key_figures": ["محمد ﷺ"],
            },
            {
                "event_id": "prophet_death",
                "name_ar": "وفاة النبي",
                "name_en": "Death of the Prophet",
                "description": "Prophet Muhammad's passing",
                "quranic_refs": ["3:144"],
                "key_figures": ["محمد ﷺ"],
            },
        ],
    },
    "khulafa_rashidun": {
        "era_name_ar": "عهد الخلفاء الراشدين",
        "era_name_en": "Era of Rightly Guided Caliphs",
        "date_range": "632 - 661 CE",
        "events": [
            {
                "event_id": "abu_bakr_khilafa",
                "name_ar": "خلافة أبي بكر",
                "name_en": "Caliphate of Abu Bakr",
                "description": "First caliph, Ridda wars, Quran compilation begun",
                "quranic_refs": [],
                "key_figures": ["أبو بكر"],
            },
            {
                "event_id": "umar_khilafa",
                "name_ar": "خلافة عمر",
                "name_en": "Caliphate of Umar",
                "description": "Major conquests, administrative systems established",
                "quranic_refs": [],
                "key_figures": ["عمر بن الخطاب"],
            },
            {
                "event_id": "uthman_khilafa",
                "name_ar": "خلافة عثمان",
                "name_en": "Caliphate of Uthman",
                "description": "Quran standardization, maritime expansion",
                "quranic_refs": [],
                "key_figures": ["عثمان بن عفان"],
            },
            {
                "event_id": "quran_compilation",
                "name_ar": "جمع القرآن",
                "name_en": "Compilation of the Quran",
                "description": "Standardization of the Quranic text",
                "quranic_refs": [],
                "key_figures": ["عثمان بن عفان", "زيد بن ثابت"],
            },
            {
                "event_id": "ali_khilafa",
                "name_ar": "خلافة علي",
                "name_en": "Caliphate of Ali",
                "description": "Fourth caliph, civil strife period",
                "quranic_refs": [],
                "key_figures": ["علي بن أبي طالب"],
            },
        ],
    },
}

# Entity nodes for the knowledge graph
GRAPH_NODES = {
    # Prophets
    "adam": {
        "name_ar": "آدم",
        "name_en": "Adam",
        "type": EntityType.PROPHET,
        "era": HistoricalEra.PRE_PROPHETIC,
        "attributes": {
            "title": "Father of Humanity",
            "lifespan": "Unspecified",
            "miracles": ["Creation without parents", "Knowledge of names"],
        },
        "quranic_refs": ["2:30-39", "7:11-25", "20:115-123"],
    },
    "nuh": {
        "name_ar": "نوح",
        "name_en": "Noah (Nuh)",
        "type": EntityType.PROPHET,
        "era": HistoricalEra.PRE_PROPHETIC,
        "attributes": {
            "title": "Saved from the Flood",
            "dawah_years": 950,
            "miracles": ["Building the Ark"],
        },
        "quranic_refs": ["11:25-49", "71:1-28", "23:23-30"],
    },
    "ibrahim": {
        "name_ar": "إبراهيم",
        "name_en": "Abraham (Ibrahim)",
        "type": EntityType.PROPHET,
        "era": HistoricalEra.PRE_PROPHETIC,
        "attributes": {
            "title": "Friend of Allah (Khalilullah)",
            "origin": "Mesopotamia",
            "miracles": ["Saved from fire", "Birds demonstration"],
        },
        "quranic_refs": ["2:124-141", "6:74-83", "21:51-73", "37:83-113"],
    },
    "musa": {
        "name_ar": "موسى",
        "name_en": "Moses (Musa)",
        "type": EntityType.PROPHET,
        "era": HistoricalEra.PRE_PROPHETIC,
        "attributes": {
            "title": "Kalimullah (The one Allah spoke to directly)",
            "origin": "Egypt",
            "miracles": ["Staff", "Hand", "Parting of the sea"],
        },
        "quranic_refs": ["2:49-74", "7:103-171", "20:9-98", "28:3-43"],
    },
    "isa": {
        "name_ar": "عيسى",
        "name_en": "Jesus (Isa)",
        "type": EntityType.PROPHET,
        "era": HistoricalEra.PRE_PROPHETIC,
        "attributes": {
            "title": "Ruhullah (Spirit of Allah)",
            "origin": "Palestine",
            "miracles": ["Speaking in cradle", "Healing", "Raising dead"],
        },
        "quranic_refs": ["3:45-60", "5:110-120", "19:16-40"],
    },
    "muhammad": {
        "name_ar": "محمد ﷺ",
        "name_en": "Muhammad (peace be upon him)",
        "type": EntityType.PROPHET,
        "era": HistoricalEra.MAKKAN,
        "attributes": {
            "title": "Seal of the Prophets",
            "birth": "570 CE",
            "death": "632 CE",
            "miracles": ["Quran", "Isra & Miraj"],
        },
        "quranic_refs": ["33:40", "48:29", "3:144"],
    },
    # Companions
    "abu_bakr": {
        "name_ar": "أبو بكر الصديق",
        "name_en": "Abu Bakr As-Siddiq",
        "type": EntityType.COMPANION,
        "era": HistoricalEra.MAKKAN,
        "attributes": {
            "title": "As-Siddiq (The Truthful)",
            "caliphate": "632-634 CE",
        },
        "quranic_refs": ["9:40"],
    },
    "umar": {
        "name_ar": "عمر بن الخطاب",
        "name_en": "Umar ibn Al-Khattab",
        "type": EntityType.COMPANION,
        "era": HistoricalEra.MAKKAN,
        "attributes": {
            "title": "Al-Faruq (The Distinguisher)",
            "caliphate": "634-644 CE",
        },
        "quranic_refs": [],
    },
    "uthman": {
        "name_ar": "عثمان بن عفان",
        "name_en": "Uthman ibn Affan",
        "type": EntityType.COMPANION,
        "era": HistoricalEra.MAKKAN,
        "attributes": {
            "title": "Dhun-Nurayn (Possessor of Two Lights)",
            "caliphate": "644-656 CE",
        },
        "quranic_refs": [],
    },
    "ali": {
        "name_ar": "علي بن أبي طالب",
        "name_en": "Ali ibn Abi Talib",
        "type": EntityType.COMPANION,
        "era": HistoricalEra.MAKKAN,
        "attributes": {
            "title": "Asadullah (Lion of Allah)",
            "caliphate": "656-661 CE",
        },
        "quranic_refs": [],
    },
    # Places
    "makkah": {
        "name_ar": "مكة المكرمة",
        "name_en": "Makkah",
        "type": EntityType.PLACE,
        "era": None,
        "attributes": {
            "significance": "Birthplace of Prophet, location of Kaaba",
            "other_names": ["Bakkah", "Ummul-Qura"],
        },
        "quranic_refs": ["3:96", "48:24"],
    },
    "madinah": {
        "name_ar": "المدينة المنورة",
        "name_en": "Madinah",
        "type": EntityType.PLACE,
        "era": None,
        "attributes": {
            "significance": "Prophet's migration destination",
            "old_name": "Yathrib",
        },
        "quranic_refs": ["9:101", "9:120"],
    },
    "jerusalem": {
        "name_ar": "القدس",
        "name_en": "Jerusalem",
        "type": EntityType.PLACE,
        "era": None,
        "attributes": {
            "significance": "Al-Aqsa Mosque, first qibla",
            "other_names": ["Al-Quds", "Bayt al-Maqdis"],
        },
        "quranic_refs": ["17:1"],
    },
    # Concepts
    "tawhid": {
        "name_ar": "التوحيد",
        "name_en": "Tawhid (Monotheism)",
        "type": EntityType.CONCEPT,
        "era": None,
        "attributes": {
            "definition": "Absolute oneness of Allah",
            "branches": ["Rububiyyah", "Uluhiyyah", "Asma wa Sifat"],
        },
        "quranic_refs": ["112:1-4", "2:163", "21:25"],
    },
    "akhirah": {
        "name_ar": "الآخرة",
        "name_en": "The Hereafter",
        "type": EntityType.CONCEPT,
        "era": None,
        "attributes": {
            "components": ["Death", "Grave", "Resurrection", "Judgment", "Paradise/Hell"],
        },
        "quranic_refs": ["2:4", "81:1-14", "82:1-19"],
    },
}

# Graph edges (relationships)
GRAPH_EDGES = [
    # Prophet lineage
    {"source": "adam", "target": "nuh", "relation": RelationType.PRECEDED, "weight": 1.0},
    {"source": "nuh", "target": "ibrahim", "relation": RelationType.PRECEDED, "weight": 1.0},
    {"source": "ibrahim", "target": "musa", "relation": RelationType.PRECEDED, "weight": 1.0},
    {"source": "musa", "target": "isa", "relation": RelationType.PRECEDED, "weight": 1.0},
    {"source": "isa", "target": "muhammad", "relation": RelationType.PRECEDED, "weight": 1.0},
    # Prophet-Place connections
    {"source": "ibrahim", "target": "makkah", "relation": RelationType.OCCURRED_AT, "weight": 0.9},
    {"source": "muhammad", "target": "makkah", "relation": RelationType.OCCURRED_AT, "weight": 1.0},
    {"source": "muhammad", "target": "madinah", "relation": RelationType.OCCURRED_AT, "weight": 1.0},
    {"source": "isa", "target": "jerusalem", "relation": RelationType.OCCURRED_AT, "weight": 0.9},
    {"source": "musa", "target": "jerusalem", "relation": RelationType.OCCURRED_AT, "weight": 0.7},
    # Companion relationships
    {"source": "muhammad", "target": "abu_bakr", "relation": RelationType.COMPANION_OF, "weight": 1.0},
    {"source": "muhammad", "target": "umar", "relation": RelationType.COMPANION_OF, "weight": 1.0},
    {"source": "muhammad", "target": "uthman", "relation": RelationType.COMPANION_OF, "weight": 1.0},
    {"source": "muhammad", "target": "ali", "relation": RelationType.COMPANION_OF, "weight": 1.0},
    # Caliphate succession
    {"source": "abu_bakr", "target": "umar", "relation": RelationType.PRECEDED, "weight": 1.0},
    {"source": "umar", "target": "uthman", "relation": RelationType.PRECEDED, "weight": 1.0},
    {"source": "uthman", "target": "ali", "relation": RelationType.PRECEDED, "weight": 1.0},
    # Prophet-Concept connections
    {"source": "ibrahim", "target": "tawhid", "relation": RelationType.RELATED_TO, "weight": 1.0},
    {"source": "muhammad", "target": "tawhid", "relation": RelationType.RELATED_TO, "weight": 1.0},
]


# =============================================================================
# KNOWLEDGE GRAPH SERVICE
# =============================================================================

class KnowledgeGraphService:
    """
    Expanded Knowledge Graph with Islamic history and dynamic exploration.

    Features:
    - Comprehensive timeline
    - Entity relationships
    - Path finding
    - Graph visualization data
    - Dynamic exploration

    Arabic: الرسم البياني المعرفي الموسع مع التاريخ الإسلامي
    """

    def __init__(self):
        self._timeline = HISTORICAL_TIMELINE
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[str]] = defaultdict(list)

        self._build_graph()

    def _build_graph(self):
        """Build the knowledge graph from data."""
        # Build nodes
        for node_id, data in GRAPH_NODES.items():
            self._nodes[node_id] = GraphNode(
                node_id=node_id,
                name_ar=data["name_ar"],
                name_en=data["name_en"],
                entity_type=data["type"],
                era=data.get("era"),
                attributes=data.get("attributes", {}),
                quranic_references=data.get("quranic_refs", []),
            )

        # Build edges
        for edge_data in GRAPH_EDGES:
            edge = GraphEdge(
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                relation_type=edge_data["relation"],
                weight=edge_data.get("weight", 1.0),
                evidence=edge_data.get("evidence", []),
            )
            self._edges.append(edge)

            # Build adjacency list
            self._adjacency[edge_data["source"]].append(edge_data["target"])
            self._adjacency[edge_data["target"]].append(edge_data["source"])

    # ==========================================================================
    # TIMELINE METHODS
    # ==========================================================================

    def get_all_eras(self) -> List[Dict[str, Any]]:
        """Get all historical eras."""
        return [
            {
                "era_id": era_id,
                "era_name_ar": data["era_name_ar"],
                "era_name_en": data["era_name_en"],
                "date_range": data["date_range"],
                "event_count": len(data["events"]),
            }
            for era_id, data in self._timeline.items()
        ]

    def get_era_details(self, era_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an era."""
        if era_id not in self._timeline:
            return None

        data = self._timeline[era_id]

        return {
            "era_id": era_id,
            "era_name_ar": data["era_name_ar"],
            "era_name_en": data["era_name_en"],
            "date_range": data["date_range"],
            "events": data["events"],
            "event_count": len(data["events"]),
        }

    def get_complete_timeline(self) -> List[Dict[str, Any]]:
        """Get complete timeline of events across all eras."""
        timeline = []

        for era_id, era_data in self._timeline.items():
            for event in era_data["events"]:
                timeline.append({
                    "era_id": era_id,
                    "era_name_en": era_data["era_name_en"],
                    **event,
                })

        return timeline

    def search_timeline(self, query: str) -> List[Dict[str, Any]]:
        """Search timeline for events matching query."""
        results = []
        query_lower = query.lower()

        for era_id, era_data in self._timeline.items():
            for event in era_data["events"]:
                if (query_lower in event["name_en"].lower() or
                    query_lower in event.get("description", "").lower() or
                    any(query_lower in fig.lower() for fig in event.get("key_figures", []))):
                    results.append({
                        "era_id": era_id,
                        "era_name_en": era_data["era_name_en"],
                        **event,
                    })

        return results

    def get_events_by_figure(self, figure_name: str) -> List[Dict[str, Any]]:
        """Get all events involving a specific figure."""
        results = []

        for era_id, era_data in self._timeline.items():
            for event in era_data["events"]:
                if figure_name in event.get("key_figures", []):
                    results.append({
                        "era_id": era_id,
                        "era_name_en": era_data["era_name_en"],
                        **event,
                    })

        return results

    # ==========================================================================
    # GRAPH EXPLORATION METHODS
    # ==========================================================================

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID."""
        if node_id not in self._nodes:
            return None

        node = self._nodes[node_id]
        return {
            "node_id": node.node_id,
            "name_ar": node.name_ar,
            "name_en": node.name_en,
            "entity_type": node.entity_type.value,
            "era": node.era.value if node.era else None,
            "attributes": node.attributes,
            "quranic_references": node.quranic_references,
        }

    def get_all_nodes(
        self,
        entity_type: Optional[str] = None,
        era: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all nodes, optionally filtered."""
        results = []

        for node in self._nodes.values():
            if entity_type and node.entity_type.value != entity_type:
                continue
            if era and (not node.era or node.era.value != era):
                continue

            results.append({
                "node_id": node.node_id,
                "name_ar": node.name_ar,
                "name_en": node.name_en,
                "entity_type": node.entity_type.value,
                "era": node.era.value if node.era else None,
            })

        return results

    def get_node_connections(self, node_id: str) -> Dict[str, Any]:
        """Get all connections for a node."""
        if node_id not in self._nodes:
            return {"error": "Node not found"}

        node = self._nodes[node_id]
        connections = []

        for edge in self._edges:
            if edge.source_id == node_id:
                target = self._nodes.get(edge.target_id)
                if target:
                    connections.append({
                        "target_id": edge.target_id,
                        "target_name_en": target.name_en,
                        "relation": edge.relation_type.value,
                        "direction": "outgoing",
                        "weight": edge.weight,
                    })
            elif edge.target_id == node_id:
                source = self._nodes.get(edge.source_id)
                if source:
                    connections.append({
                        "target_id": edge.source_id,
                        "target_name_en": source.name_en,
                        "relation": edge.relation_type.value,
                        "direction": "incoming",
                        "weight": edge.weight,
                    })

        return {
            "node_id": node_id,
            "node_name_en": node.name_en,
            "connections": connections,
            "connection_count": len(connections),
        }

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Find path between two nodes using BFS."""
        if start_id not in self._nodes or end_id not in self._nodes:
            return None

        if start_id == end_id:
            return {"path": [start_id], "length": 0}

        visited = {start_id}
        queue = [(start_id, [start_id])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for neighbor in self._adjacency[current]:
                if neighbor == end_id:
                    full_path = path + [end_id]
                    return {
                        "path": full_path,
                        "length": len(full_path) - 1,
                        "path_details": [
                            {
                                "node_id": nid,
                                "node_name_en": self._nodes[nid].name_en,
                            }
                            for nid in full_path
                        ],
                    }

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def explore_from_node(
        self,
        node_id: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """Explore the graph from a starting node to a given depth."""
        if node_id not in self._nodes:
            return {"error": "Node not found"}

        explored_nodes = {node_id}
        explored_edges = []
        current_level = [node_id]

        for _ in range(depth):
            next_level = []

            for current in current_level:
                for edge in self._edges:
                    target = None
                    if edge.source_id == current and edge.target_id not in explored_nodes:
                        target = edge.target_id
                    elif edge.target_id == current and edge.source_id not in explored_nodes:
                        target = edge.source_id

                    if target:
                        explored_nodes.add(target)
                        next_level.append(target)
                        explored_edges.append({
                            "source": edge.source_id,
                            "target": edge.target_id,
                            "relation": edge.relation_type.value,
                        })

            current_level = next_level

        return {
            "start_node": node_id,
            "depth": depth,
            "nodes": [
                {
                    "node_id": nid,
                    "name_en": self._nodes[nid].name_en,
                    "entity_type": self._nodes[nid].entity_type.value,
                }
                for nid in explored_nodes
            ],
            "edges": explored_edges,
            "node_count": len(explored_nodes),
            "edge_count": len(explored_edges),
        }

    # ==========================================================================
    # VISUALIZATION DATA
    # ==========================================================================

    def get_graph_visualization_data(self) -> Dict[str, Any]:
        """Get data formatted for graph visualization."""
        nodes = [
            {
                "id": node.node_id,
                "label": node.name_en,
                "label_ar": node.name_ar,
                "group": node.entity_type.value,
                "era": node.era.value if node.era else None,
            }
            for node in self._nodes.values()
        ]

        edges = [
            {
                "source": edge.source_id,
                "target": edge.target_id,
                "label": edge.relation_type.value,
                "weight": edge.weight,
            }
            for edge in self._edges
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def get_entity_types(self) -> List[Dict[str, str]]:
        """Get all entity types."""
        return [
            {"id": t.value, "name_en": t.value.replace("_", " ").title()}
            for t in EntityType
        ]

    def get_relation_types(self) -> List[Dict[str, str]]:
        """Get all relation types."""
        return [
            {"id": r.value, "name_en": r.value.replace("_", " ").title()}
            for r in RelationType
        ]

    # ==========================================================================
    # STATISTICS
    # ==========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        type_counts = defaultdict(int)
        era_counts = defaultdict(int)

        for node in self._nodes.values():
            type_counts[node.entity_type.value] += 1
            if node.era:
                era_counts[node.era.value] += 1

        relation_counts = defaultdict(int)
        for edge in self._edges:
            relation_counts[edge.relation_type.value] += 1

        total_events = sum(
            len(era["events"]) for era in self._timeline.values()
        )

        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "total_timeline_events": total_events,
            "historical_eras": len(self._timeline),
            "entity_type_distribution": dict(type_counts),
            "era_distribution": dict(era_counts),
            "relation_distribution": dict(relation_counts),
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

knowledge_graph_service = KnowledgeGraphService()
