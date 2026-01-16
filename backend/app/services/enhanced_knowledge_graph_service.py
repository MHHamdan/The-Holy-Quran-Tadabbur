"""
Enhanced Knowledge Graph Service

Provides comprehensive knowledge graph functionality with:
- Entity Relationship Mapping (prophets, companions, places, divine names, concepts)
- Family ties, prophet-place connections, divine themes
- BFS pathfinding for thematic journeys
- Interactive graph visualization data
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from collections import deque
import math


class EntityType(Enum):
    """Types of entities in the knowledge graph"""
    PROPHET = "prophet"
    COMPANION = "companion"
    PLACE = "place"
    DIVINE_NAME = "divine_name"
    CONCEPT = "concept"
    EVENT = "event"
    TRIBE = "tribe"
    BOOK = "book"
    ANGEL = "angel"


class RelationshipType(Enum):
    """Types of relationships between entities"""
    FATHER_OF = "father_of"
    SON_OF = "son_of"
    WIFE_OF = "wife_of"
    HUSBAND_OF = "husband_of"
    BROTHER_OF = "brother_of"
    SISTER_OF = "sister_of"
    DESCENDANT_OF = "descendant_of"
    ANCESTOR_OF = "ancestor_of"
    LIVED_IN = "lived_in"
    BORN_IN = "born_in"
    DIED_IN = "died_in"
    MIGRATED_TO = "migrated_to"
    SENT_TO = "sent_to"
    REVEALED_TO = "revealed_to"
    RELATED_TO = "related_to"
    THEME_OF = "theme_of"
    MENTIONED_IN = "mentioned_in"
    CONTEMPORARY_OF = "contemporary_of"
    FOLLOWER_OF = "follower_of"
    ENEMY_OF = "enemy_of"


@dataclass
class Entity:
    """Represents an entity in the knowledge graph"""
    id: str
    name_english: str
    name_arabic: str
    entity_type: EntityType
    description: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    quranic_references: List[str] = field(default_factory=list)
    related_themes: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    """Represents a relationship between two entities"""
    id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    description: Optional[str] = None
    weight: float = 1.0
    quranic_reference: Optional[str] = None
    bidirectional: bool = False


@dataclass
class PathResult:
    """Result of a path search"""
    source: str
    target: str
    path: List[str]
    relationships: List[Dict[str, Any]]
    total_weight: float
    path_length: int


class EnhancedKnowledgeGraphService:
    """
    Enhanced Knowledge Graph service with comprehensive entity relationships
    and BFS pathfinding for Quranic exploration.
    """

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.adjacency_list: Dict[str, List[Tuple[str, str, float]]] = {}  # node_id -> [(neighbor_id, rel_id, weight)]
        self._initialize_entities()
        self._initialize_relationships()
        self._build_adjacency_list()

    def _initialize_entities(self):
        """Initialize comprehensive entities database"""
        # Prophets
        prophets = [
            Entity(
                id="adam",
                name_english="Adam",
                name_arabic="آدم",
                entity_type=EntityType.PROPHET,
                description="The first human and first prophet, created by Allah from clay",
                attributes={"title": "Abul Bashar (Father of Humanity)", "mentioned_times": 25},
                quranic_references=["2:30-39", "7:11-25", "15:26-44", "20:115-123"],
                related_themes=["creation", "forgiveness", "obedience"]
            ),
            Entity(
                id="nuh",
                name_english="Noah",
                name_arabic="نوح",
                entity_type=EntityType.PROPHET,
                description="Prophet who built the Ark and preached for 950 years",
                attributes={"title": "Najiyullah (Saved by Allah)", "mentioned_times": 43, "preaching_years": 950},
                quranic_references=["11:25-49", "23:23-30", "71:1-28"],
                related_themes=["patience", "perseverance", "divine_punishment"]
            ),
            Entity(
                id="ibrahim",
                name_english="Abraham",
                name_arabic="إبراهيم",
                entity_type=EntityType.PROPHET,
                description="Father of the prophets, known for his unwavering faith",
                attributes={"title": "Khalilullah (Friend of Allah)", "mentioned_times": 69},
                quranic_references=["2:124-141", "6:74-83", "14:35-41", "21:51-73", "37:83-113"],
                related_themes=["monotheism", "sacrifice", "trust", "guidance"]
            ),
            Entity(
                id="ismail",
                name_english="Ishmael",
                name_arabic="إسماعيل",
                entity_type=EntityType.PROPHET,
                description="Son of Ibrahim, helped build the Kaaba",
                attributes={"title": "Dhabih (The Sacrificed)", "mentioned_times": 12},
                quranic_references=["2:125-129", "14:39", "37:101-107"],
                related_themes=["sacrifice", "obedience", "patience"]
            ),
            Entity(
                id="ishaq",
                name_english="Isaac",
                name_arabic="إسحاق",
                entity_type=EntityType.PROPHET,
                description="Son of Ibrahim and Sarah, father of Yaqub",
                attributes={"mentioned_times": 17},
                quranic_references=["6:84", "11:71", "21:72", "37:112-113"],
                related_themes=["blessing", "lineage"]
            ),
            Entity(
                id="yaqub",
                name_english="Jacob",
                name_arabic="يعقوب",
                entity_type=EntityType.PROPHET,
                description="Son of Ishaq, also known as Israel, father of Yusuf",
                attributes={"title": "Israel", "mentioned_times": 16},
                quranic_references=["2:132-133", "12:4-100", "19:49"],
                related_themes=["patience", "trust", "family"]
            ),
            Entity(
                id="yusuf",
                name_english="Joseph",
                name_arabic="يوسف",
                entity_type=EntityType.PROPHET,
                description="Son of Yaqub, known for his beauty and the trial of the well",
                attributes={"title": "Al-Siddiq (The Truthful)", "mentioned_times": 27},
                quranic_references=["12:1-111"],
                related_themes=["patience", "trust", "forgiveness", "trials"]
            ),
            Entity(
                id="musa",
                name_english="Moses",
                name_arabic="موسى",
                entity_type=EntityType.PROPHET,
                description="Prophet who received the Torah and confronted Pharaoh",
                attributes={"title": "Kalimullah (One who spoke to Allah)", "mentioned_times": 136},
                quranic_references=["2:51-61", "7:103-162", "20:9-99", "28:3-46"],
                related_themes=["liberation", "guidance", "miracles", "patience"]
            ),
            Entity(
                id="harun",
                name_english="Aaron",
                name_arabic="هارون",
                entity_type=EntityType.PROPHET,
                description="Brother of Musa, assisted him in his mission",
                attributes={"mentioned_times": 20},
                quranic_references=["7:142", "20:29-36", "28:34"],
                related_themes=["support", "brotherhood"]
            ),
            Entity(
                id="dawud",
                name_english="David",
                name_arabic="داود",
                entity_type=EntityType.PROPHET,
                description="King and prophet who received the Zabur (Psalms)",
                attributes={"title": "Khalifatullah (Representative of Allah)", "mentioned_times": 16},
                quranic_references=["2:251", "21:78-80", "34:10-11", "38:17-26"],
                related_themes=["kingship", "worship", "justice"]
            ),
            Entity(
                id="sulaiman",
                name_english="Solomon",
                name_arabic="سليمان",
                entity_type=EntityType.PROPHET,
                description="Son of Dawud, known for his wisdom and kingdom over jinn and animals",
                attributes={"mentioned_times": 17},
                quranic_references=["21:81-82", "27:15-44", "34:12-14", "38:30-40"],
                related_themes=["wisdom", "kingship", "gratitude"]
            ),
            Entity(
                id="ayyub",
                name_english="Job",
                name_arabic="أيوب",
                entity_type=EntityType.PROPHET,
                description="Known for his extraordinary patience during severe trials",
                attributes={"title": "Exemplar of Patience", "mentioned_times": 4},
                quranic_references=["21:83-84", "38:41-44"],
                related_themes=["patience", "trials", "trust"]
            ),
            Entity(
                id="yunus",
                name_english="Jonah",
                name_arabic="يونس",
                entity_type=EntityType.PROPHET,
                description="Prophet who was swallowed by a whale",
                attributes={"title": "Dhun-Nun (Companion of the Fish)", "mentioned_times": 4},
                quranic_references=["10:98", "21:87-88", "37:139-148", "68:48-50"],
                related_themes=["repentance", "patience", "mercy"]
            ),
            Entity(
                id="zakariyya",
                name_english="Zechariah",
                name_arabic="زكريا",
                entity_type=EntityType.PROPHET,
                description="Guardian of Maryam, father of Yahya",
                attributes={"mentioned_times": 7},
                quranic_references=["3:37-41", "19:2-11", "21:89-90"],
                related_themes=["prayer", "trust", "blessing"]
            ),
            Entity(
                id="yahya",
                name_english="John",
                name_arabic="يحيى",
                entity_type=EntityType.PROPHET,
                description="Son of Zakariyya, herald of Isa",
                attributes={"mentioned_times": 5},
                quranic_references=["3:39", "19:12-15", "21:90"],
                related_themes=["piety", "wisdom"]
            ),
            Entity(
                id="isa",
                name_english="Jesus",
                name_arabic="عيسى",
                entity_type=EntityType.PROPHET,
                description="Born miraculously to Maryam, performed miracles by Allah's permission",
                attributes={"title": "Ruhullah (Spirit of Allah), Masih (Messiah)", "mentioned_times": 25},
                quranic_references=["3:45-59", "5:110-118", "19:16-35", "43:57-65"],
                related_themes=["miracles", "monotheism", "mercy"]
            ),
            Entity(
                id="muhammad",
                name_english="Muhammad",
                name_arabic="محمد",
                entity_type=EntityType.PROPHET,
                description="The final messenger and seal of the prophets",
                attributes={"title": "Khatam an-Nabiyyin (Seal of Prophets), Rahmat lil-Alameen (Mercy to the Worlds)", "mentioned_times": 4},
                quranic_references=["3:144", "33:40", "47:2", "48:29"],
                related_themes=["mercy", "guidance", "final_message"]
            ),
        ]

        # Places
        places = [
            Entity(
                id="makkah",
                name_english="Makkah",
                name_arabic="مكة",
                entity_type=EntityType.PLACE,
                description="The holiest city in Islam, location of the Kaaba",
                attributes={"other_names": ["Bakkah", "Umm al-Qura"]},
                quranic_references=["3:96", "48:24"],
                related_themes=["pilgrimage", "worship", "monotheism"]
            ),
            Entity(
                id="madinah",
                name_english="Madinah",
                name_arabic="المدينة",
                entity_type=EntityType.PLACE,
                description="City of the Prophet, destination of the Hijrah",
                attributes={"other_names": ["Yathrib", "Taybah"]},
                quranic_references=["9:101", "9:120", "33:60"],
                related_themes=["migration", "community", "brotherhood"]
            ),
            Entity(
                id="jerusalem",
                name_english="Jerusalem",
                name_arabic="القدس",
                entity_type=EntityType.PLACE,
                description="The holy city, direction of first Qibla",
                attributes={"other_names": ["Bayt al-Maqdis", "al-Quds"]},
                quranic_references=["17:1"],
                related_themes=["night_journey", "prophets", "worship"]
            ),
            Entity(
                id="egypt",
                name_english="Egypt",
                name_arabic="مصر",
                entity_type=EntityType.PLACE,
                description="Land where Musa confronted Pharaoh and Yusuf became minister",
                quranic_references=["2:61", "10:87", "12:21", "12:99"],
                related_themes=["liberation", "trials", "patience"]
            ),
            Entity(
                id="mount_sinai",
                name_english="Mount Sinai",
                name_arabic="طور سيناء",
                entity_type=EntityType.PLACE,
                description="Mountain where Musa received the Torah",
                quranic_references=["2:63", "7:143", "19:52", "20:80"],
                related_themes=["revelation", "covenant"]
            ),
            Entity(
                id="cave_hira",
                name_english="Cave of Hira",
                name_arabic="غار حراء",
                entity_type=EntityType.PLACE,
                description="Cave where Muhammad received the first revelation",
                quranic_references=["96:1-5"],
                related_themes=["revelation", "guidance"]
            ),
        ]

        # Divine Names
        divine_names = [
            Entity(
                id="ar_rahman",
                name_english="The Most Gracious",
                name_arabic="الرحمن",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His all-encompassing mercy",
                quranic_references=["1:1", "55:1", "67:3"],
                related_themes=["mercy", "creation", "sustenance"]
            ),
            Entity(
                id="ar_raheem",
                name_english="The Most Merciful",
                name_arabic="الرحيم",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His special mercy for believers",
                quranic_references=["1:1", "2:37", "9:117"],
                related_themes=["mercy", "forgiveness", "believers"]
            ),
            Entity(
                id="al_malik",
                name_english="The King",
                name_arabic="الملك",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His absolute sovereignty",
                quranic_references=["20:114", "23:116", "59:23"],
                related_themes=["sovereignty", "power", "judgment"]
            ),
            Entity(
                id="al_quddus",
                name_english="The Holy",
                name_arabic="القدوس",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His absolute purity",
                quranic_references=["59:23", "62:1"],
                related_themes=["purity", "transcendence"]
            ),
            Entity(
                id="al_aleem",
                name_english="The All-Knowing",
                name_arabic="العليم",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His complete knowledge",
                quranic_references=["2:29", "2:32", "6:13"],
                related_themes=["knowledge", "wisdom"]
            ),
            Entity(
                id="al_hakeem",
                name_english="The All-Wise",
                name_arabic="الحكيم",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His perfect wisdom",
                quranic_references=["2:32", "2:129", "6:18"],
                related_themes=["wisdom", "purpose"]
            ),
            Entity(
                id="al_ghafoor",
                name_english="The Oft-Forgiving",
                name_arabic="الغفور",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His forgiveness",
                quranic_references=["2:173", "4:23", "5:74"],
                related_themes=["forgiveness", "mercy", "repentance"]
            ),
            Entity(
                id="al_wadud",
                name_english="The Loving",
                name_arabic="الودود",
                entity_type=EntityType.DIVINE_NAME,
                description="Name of Allah indicating His love for creation",
                quranic_references=["11:90", "85:14"],
                related_themes=["love", "mercy", "compassion"]
            ),
        ]

        # Concepts
        concepts = [
            Entity(
                id="tawhid",
                name_english="Monotheism",
                name_arabic="التوحيد",
                entity_type=EntityType.CONCEPT,
                description="The oneness of Allah, the core concept of Islam",
                quranic_references=["112:1-4", "2:163", "21:25"],
                related_themes=["faith", "worship", "divine_unity"]
            ),
            Entity(
                id="sabr",
                name_english="Patience",
                name_arabic="الصبر",
                entity_type=EntityType.CONCEPT,
                description="Patience and perseverance in the face of trials",
                quranic_references=["2:153", "2:155", "3:200"],
                related_themes=["trials", "reward", "trust"]
            ),
            Entity(
                id="tawakkul",
                name_english="Trust in Allah",
                name_arabic="التوكل",
                entity_type=EntityType.CONCEPT,
                description="Complete reliance and trust in Allah",
                quranic_references=["3:159", "65:3", "8:2"],
                related_themes=["faith", "certainty", "submission"]
            ),
            Entity(
                id="taqwa",
                name_english="God-consciousness",
                name_arabic="التقوى",
                entity_type=EntityType.CONCEPT,
                description="Awareness and fear of Allah leading to righteousness",
                quranic_references=["2:197", "3:102", "49:13"],
                related_themes=["piety", "righteousness", "obedience"]
            ),
            Entity(
                id="rahma",
                name_english="Mercy",
                name_arabic="الرحمة",
                entity_type=EntityType.CONCEPT,
                description="Divine mercy that encompasses all creation",
                quranic_references=["6:54", "21:107", "39:53"],
                related_themes=["forgiveness", "compassion", "blessing"]
            ),
            Entity(
                id="hidaya",
                name_english="Guidance",
                name_arabic="الهداية",
                entity_type=EntityType.CONCEPT,
                description="Divine guidance to the straight path",
                quranic_references=["1:6", "2:2", "6:125"],
                related_themes=["truth", "light", "path"]
            ),
        ]

        # Events
        events = [
            Entity(
                id="creation_adam",
                name_english="Creation of Adam",
                name_arabic="خلق آدم",
                entity_type=EntityType.EVENT,
                description="Allah created Adam from clay and breathed His spirit into him",
                quranic_references=["2:30-34", "15:26-29", "38:71-76"],
                related_themes=["creation", "honor", "beginning"]
            ),
            Entity(
                id="flood_nuh",
                name_english="The Great Flood",
                name_arabic="طوفان نوح",
                entity_type=EntityType.EVENT,
                description="The flood that destroyed Nuh's disbelieving people",
                quranic_references=["11:36-48", "23:27", "54:11-15"],
                related_themes=["punishment", "salvation", "faith"]
            ),
            Entity(
                id="sacrifice_ismail",
                name_english="Sacrifice of Ismail",
                name_arabic="ذبح إسماعيل",
                entity_type=EntityType.EVENT,
                description="Ibrahim's willingness to sacrifice his son Ismail",
                quranic_references=["37:102-107"],
                related_themes=["sacrifice", "obedience", "trust"]
            ),
            Entity(
                id="exodus",
                name_english="Exodus from Egypt",
                name_arabic="خروج بني إسرائيل",
                entity_type=EntityType.EVENT,
                description="Musa leading Bani Israel out of Egypt",
                quranic_references=["7:137-138", "20:77-80", "26:52-66"],
                related_themes=["liberation", "miracles", "faith"]
            ),
            Entity(
                id="night_journey",
                name_english="Night Journey (Isra and Miraj)",
                name_arabic="الإسراء والمعراج",
                entity_type=EntityType.EVENT,
                description="Prophet Muhammad's miraculous night journey to Jerusalem and ascension to heavens",
                quranic_references=["17:1", "53:1-18"],
                related_themes=["miracles", "prayer", "honor"]
            ),
            Entity(
                id="hijrah",
                name_english="Migration to Madinah",
                name_arabic="الهجرة",
                entity_type=EntityType.EVENT,
                description="The migration of Prophet Muhammad from Makkah to Madinah",
                quranic_references=["9:40", "8:30"],
                related_themes=["migration", "trust", "new_beginning"]
            ),
        ]

        # Add all entities
        for entity in prophets + places + divine_names + concepts + events:
            self.entities[entity.id] = entity

    def _initialize_relationships(self):
        """Initialize comprehensive relationships between entities"""
        relationships_data = [
            # Prophet Lineage
            Relationship("r1", "adam", "nuh", RelationshipType.ANCESTOR_OF, "Nuh is a descendant of Adam"),
            Relationship("r2", "nuh", "ibrahim", RelationshipType.ANCESTOR_OF, "Ibrahim is a descendant of Nuh"),
            Relationship("r3", "ibrahim", "ismail", RelationshipType.FATHER_OF, "Ibrahim is the father of Ismail"),
            Relationship("r4", "ibrahim", "ishaq", RelationshipType.FATHER_OF, "Ibrahim is the father of Ishaq"),
            Relationship("r5", "ishaq", "yaqub", RelationshipType.FATHER_OF, "Ishaq is the father of Yaqub"),
            Relationship("r6", "yaqub", "yusuf", RelationshipType.FATHER_OF, "Yaqub is the father of Yusuf"),
            Relationship("r7", "dawud", "sulaiman", RelationshipType.FATHER_OF, "Dawud is the father of Sulaiman"),
            Relationship("r8", "zakariyya", "yahya", RelationshipType.FATHER_OF, "Zakariyya is the father of Yahya"),
            Relationship("r9", "musa", "harun", RelationshipType.BROTHER_OF, "Musa and Harun are brothers", bidirectional=True),
            Relationship("r10", "ismail", "muhammad", RelationshipType.ANCESTOR_OF, "Muhammad is a descendant of Ismail"),

            # Prophet-Place Relationships
            Relationship("r11", "ibrahim", "makkah", RelationshipType.LIVED_IN, "Ibrahim lived in Makkah"),
            Relationship("r12", "ismail", "makkah", RelationshipType.LIVED_IN, "Ismail lived in Makkah"),
            Relationship("r13", "muhammad", "makkah", RelationshipType.BORN_IN, "Muhammad was born in Makkah"),
            Relationship("r14", "muhammad", "madinah", RelationshipType.MIGRATED_TO, "Muhammad migrated to Madinah"),
            Relationship("r15", "musa", "egypt", RelationshipType.LIVED_IN, "Musa lived in Egypt"),
            Relationship("r16", "yusuf", "egypt", RelationshipType.LIVED_IN, "Yusuf lived in Egypt"),
            Relationship("r17", "musa", "mount_sinai", RelationshipType.RELATED_TO, "Musa received revelation at Mount Sinai"),
            Relationship("r18", "muhammad", "cave_hira", RelationshipType.RELATED_TO, "Muhammad received first revelation in Cave Hira"),
            Relationship("r19", "isa", "jerusalem", RelationshipType.RELATED_TO, "Isa's mission was centered around Jerusalem"),
            Relationship("r20", "muhammad", "jerusalem", RelationshipType.RELATED_TO, "Muhammad's night journey to Jerusalem"),

            # Prophet-Concept Relationships
            Relationship("r21", "ibrahim", "tawhid", RelationshipType.THEME_OF, "Ibrahim exemplified Tawhid"),
            Relationship("r22", "ayyub", "sabr", RelationshipType.THEME_OF, "Ayyub exemplified patience"),
            Relationship("r23", "yaqub", "sabr", RelationshipType.THEME_OF, "Yaqub exemplified patience"),
            Relationship("r24", "yusuf", "sabr", RelationshipType.THEME_OF, "Yusuf exemplified patience"),
            Relationship("r25", "muhammad", "rahma", RelationshipType.THEME_OF, "Muhammad was sent as mercy"),
            Relationship("r26", "nuh", "sabr", RelationshipType.THEME_OF, "Nuh exemplified patience (950 years)"),

            # Prophet-Event Relationships
            Relationship("r27", "adam", "creation_adam", RelationshipType.RELATED_TO, "Adam's creation"),
            Relationship("r28", "nuh", "flood_nuh", RelationshipType.RELATED_TO, "Nuh and the great flood"),
            Relationship("r29", "ibrahim", "sacrifice_ismail", RelationshipType.RELATED_TO, "Ibrahim's sacrifice"),
            Relationship("r30", "ismail", "sacrifice_ismail", RelationshipType.RELATED_TO, "Ismail's sacrifice"),
            Relationship("r31", "musa", "exodus", RelationshipType.RELATED_TO, "Musa led the exodus"),
            Relationship("r32", "muhammad", "night_journey", RelationshipType.RELATED_TO, "Muhammad's night journey"),
            Relationship("r33", "muhammad", "hijrah", RelationshipType.RELATED_TO, "Muhammad's migration"),

            # Divine Name Relationships
            Relationship("r34", "ar_rahman", "rahma", RelationshipType.THEME_OF, "Al-Rahman represents mercy"),
            Relationship("r35", "ar_raheem", "rahma", RelationshipType.THEME_OF, "Al-Raheem represents mercy"),
            Relationship("r36", "al_ghafoor", "rahma", RelationshipType.THEME_OF, "Al-Ghafoor represents mercy through forgiveness"),
            Relationship("r37", "al_hakeem", "hidaya", RelationshipType.THEME_OF, "Al-Hakeem's wisdom guides"),
            Relationship("r38", "al_aleem", "hidaya", RelationshipType.THEME_OF, "Al-Aleem's knowledge guides"),

            # Concept Relationships
            Relationship("r39", "sabr", "tawakkul", RelationshipType.RELATED_TO, "Patience requires trust"),
            Relationship("r40", "taqwa", "hidaya", RelationshipType.RELATED_TO, "Taqwa leads to guidance"),
            Relationship("r41", "tawhid", "taqwa", RelationshipType.RELATED_TO, "Tawhid is foundation of Taqwa"),

            # Event-Place Relationships
            Relationship("r42", "exodus", "egypt", RelationshipType.RELATED_TO, "Exodus from Egypt"),
            Relationship("r43", "night_journey", "jerusalem", RelationshipType.RELATED_TO, "Night journey to Jerusalem"),
            Relationship("r44", "hijrah", "madinah", RelationshipType.RELATED_TO, "Hijrah to Madinah"),
            Relationship("r45", "flood_nuh", "mount_sinai", RelationshipType.RELATED_TO, "Ark settled near mountains"),

            # Contemporary Prophets
            Relationship("r46", "musa", "harun", RelationshipType.CONTEMPORARY_OF, "Musa and Harun lived together", bidirectional=True),
            Relationship("r47", "yahya", "isa", RelationshipType.CONTEMPORARY_OF, "Yahya and Isa were contemporaries", bidirectional=True),
            Relationship("r48", "ibrahim", "lut", RelationshipType.CONTEMPORARY_OF, "Ibrahim and Lut were contemporaries"),
        ]

        for rel in relationships_data:
            self.relationships[rel.id] = rel

    def _build_adjacency_list(self):
        """Build adjacency list for graph traversal"""
        self.adjacency_list = {entity_id: [] for entity_id in self.entities}

        for rel in self.relationships.values():
            # Add forward edge
            if rel.source_id in self.adjacency_list:
                self.adjacency_list[rel.source_id].append((rel.target_id, rel.id, rel.weight))

            # Add backward edge if bidirectional
            if rel.bidirectional and rel.target_id in self.adjacency_list:
                self.adjacency_list[rel.target_id].append((rel.source_id, rel.id, rel.weight))

    # BFS Pathfinding
    def find_path_bfs(self, source_id: str, target_id: str, max_depth: int = 10) -> Optional[Dict[str, Any]]:
        """
        Find shortest path between two entities using BFS.

        Args:
            source_id: Starting entity ID
            target_id: Target entity ID
            max_depth: Maximum search depth

        Returns:
            Path information or None if no path found
        """
        if source_id not in self.entities or target_id not in self.entities:
            return None

        if source_id == target_id:
            return {
                "source": source_id,
                "target": target_id,
                "path": [source_id],
                "relationships": [],
                "path_length": 0
            }

        # BFS with path tracking
        queue = deque([(source_id, [source_id], [], 0)])  # (current, path, relationships, depth)
        visited = {source_id}

        while queue:
            current, path, rels, depth = queue.popleft()

            if depth >= max_depth:
                continue

            for neighbor_id, rel_id, weight in self.adjacency_list.get(current, []):
                if neighbor_id == target_id:
                    # Found target
                    rel = self.relationships[rel_id]
                    final_path = path + [neighbor_id]
                    final_rels = rels + [{
                        "relationship_id": rel_id,
                        "type": rel.relationship_type.value,
                        "description": rel.description,
                        "from": current,
                        "to": neighbor_id
                    }]
                    return {
                        "source": source_id,
                        "target": target_id,
                        "source_name": self.entities[source_id].name_english,
                        "target_name": self.entities[target_id].name_english,
                        "path": final_path,
                        "path_names": [self.entities[e].name_english for e in final_path],
                        "relationships": final_rels,
                        "path_length": len(final_rels)
                    }

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    rel = self.relationships[rel_id]
                    new_rels = rels + [{
                        "relationship_id": rel_id,
                        "type": rel.relationship_type.value,
                        "description": rel.description,
                        "from": current,
                        "to": neighbor_id
                    }]
                    queue.append((neighbor_id, path + [neighbor_id], new_rels, depth + 1))

        return None

    def find_all_paths(self, source_id: str, target_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Find all paths between two entities up to max_depth"""
        if source_id not in self.entities or target_id not in self.entities:
            return []

        all_paths = []

        def dfs(current: str, path: List[str], rels: List[Dict], visited: Set[str], depth: int):
            if depth > max_depth:
                return

            if current == target_id:
                all_paths.append({
                    "path": path.copy(),
                    "path_names": [self.entities[e].name_english for e in path],
                    "relationships": rels.copy(),
                    "path_length": len(rels)
                })
                return

            for neighbor_id, rel_id, weight in self.adjacency_list.get(current, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    rel = self.relationships[rel_id]
                    path.append(neighbor_id)
                    rels.append({
                        "relationship_id": rel_id,
                        "type": rel.relationship_type.value,
                        "from": current,
                        "to": neighbor_id
                    })
                    dfs(neighbor_id, path, rels, visited, depth + 1)
                    path.pop()
                    rels.pop()
                    visited.remove(neighbor_id)

        dfs(source_id, [source_id], [], {source_id}, 0)
        return all_paths

    # Entity Operations
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed entity information"""
        if entity_id not in self.entities:
            return None

        entity = self.entities[entity_id]
        relationships = self._get_entity_relationships(entity_id)

        return {
            "id": entity.id,
            "name_english": entity.name_english,
            "name_arabic": entity.name_arabic,
            "entity_type": entity.entity_type.value,
            "description": entity.description,
            "attributes": entity.attributes,
            "quranic_references": entity.quranic_references,
            "related_themes": entity.related_themes,
            "relationships": relationships
        }

    def _get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        relationships = []

        for rel in self.relationships.values():
            if rel.source_id == entity_id:
                target = self.entities.get(rel.target_id)
                relationships.append({
                    "type": rel.relationship_type.value,
                    "direction": "outgoing",
                    "entity_id": rel.target_id,
                    "entity_name": target.name_english if target else rel.target_id,
                    "description": rel.description
                })
            elif rel.target_id == entity_id or (rel.bidirectional and rel.target_id == entity_id):
                source = self.entities.get(rel.source_id)
                relationships.append({
                    "type": rel.relationship_type.value,
                    "direction": "incoming",
                    "entity_id": rel.source_id,
                    "entity_name": source.name_english if source else rel.source_id,
                    "description": rel.description
                })

        return relationships

    def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get all entities of a specific type"""
        try:
            type_enum = EntityType(entity_type)
        except ValueError:
            return []

        return [
            {
                "id": e.id,
                "name_english": e.name_english,
                "name_arabic": e.name_arabic,
                "description": e.description[:100] + "..." if len(e.description) > 100 else e.description,
                "related_themes": e.related_themes
            }
            for e in self.entities.values()
            if e.entity_type == type_enum
        ]

    def get_entities_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """Get all entities related to a specific theme"""
        theme_lower = theme.lower()
        return [
            {
                "id": e.id,
                "name_english": e.name_english,
                "name_arabic": e.name_arabic,
                "entity_type": e.entity_type.value,
                "description": e.description
            }
            for e in self.entities.values()
            if theme_lower in [t.lower() for t in e.related_themes]
        ]

    def explore_from_entity(self, entity_id: str, depth: int = 2) -> Dict[str, Any]:
        """Explore the graph from a starting entity"""
        if entity_id not in self.entities:
            return {"error": f"Entity '{entity_id}' not found"}

        explored = {entity_id: 0}
        nodes = [{
            "id": entity_id,
            "name": self.entities[entity_id].name_english,
            "type": self.entities[entity_id].entity_type.value,
            "depth": 0
        }]
        edges = []

        queue = deque([(entity_id, 0)])

        while queue:
            current, current_depth = queue.popleft()

            if current_depth >= depth:
                continue

            for neighbor_id, rel_id, weight in self.adjacency_list.get(current, []):
                rel = self.relationships[rel_id]

                # Add edge
                edges.append({
                    "source": current,
                    "target": neighbor_id,
                    "type": rel.relationship_type.value,
                    "description": rel.description
                })

                if neighbor_id not in explored:
                    explored[neighbor_id] = current_depth + 1
                    neighbor = self.entities.get(neighbor_id)
                    if neighbor:
                        nodes.append({
                            "id": neighbor_id,
                            "name": neighbor.name_english,
                            "type": neighbor.entity_type.value,
                            "depth": current_depth + 1
                        })
                        queue.append((neighbor_id, current_depth + 1))

        return {
            "center_entity": entity_id,
            "depth": depth,
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    def get_thematic_journey(self, theme: str) -> Dict[str, Any]:
        """Create a thematic journey through related entities"""
        entities = self.get_entities_by_theme(theme)

        if not entities:
            return {"error": f"No entities found for theme '{theme}'"}

        # Build connections between theme entities
        journey_nodes = []
        journey_edges = []

        entity_ids = [e["id"] for e in entities]

        for entity in entities:
            journey_nodes.append({
                "id": entity["id"],
                "name": entity["name_english"],
                "name_arabic": entity["name_arabic"],
                "type": entity["entity_type"]
            })

        # Find connections between theme entities
        for i, eid1 in enumerate(entity_ids):
            for eid2 in entity_ids[i + 1:]:
                path = self.find_path_bfs(eid1, eid2, max_depth=3)
                if path and path["path_length"] <= 2:
                    journey_edges.append({
                        "source": eid1,
                        "target": eid2,
                        "path_length": path["path_length"],
                        "connection": path["relationships"][0]["type"] if path["relationships"] else "related"
                    })

        return {
            "theme": theme,
            "journey_nodes": journey_nodes,
            "journey_edges": journey_edges,
            "total_entities": len(journey_nodes),
            "connections": len(journey_edges)
        }

    def get_prophet_lineage(self, prophet_id: str) -> Dict[str, Any]:
        """Get the lineage (ancestors and descendants) of a prophet"""
        if prophet_id not in self.entities:
            return {"error": f"Prophet '{prophet_id}' not found"}

        prophet = self.entities[prophet_id]
        if prophet.entity_type != EntityType.PROPHET:
            return {"error": f"'{prophet_id}' is not a prophet"}

        ancestors = []
        descendants = []

        # Find ancestors
        for rel in self.relationships.values():
            if rel.target_id == prophet_id and rel.relationship_type in [RelationshipType.FATHER_OF, RelationshipType.ANCESTOR_OF]:
                source = self.entities.get(rel.source_id)
                if source:
                    ancestors.append({
                        "id": source.id,
                        "name_english": source.name_english,
                        "name_arabic": source.name_arabic,
                        "relationship": rel.relationship_type.value
                    })
            elif rel.source_id == prophet_id and rel.relationship_type in [RelationshipType.SON_OF, RelationshipType.DESCENDANT_OF]:
                target = self.entities.get(rel.target_id)
                if target:
                    ancestors.append({
                        "id": target.id,
                        "name_english": target.name_english,
                        "name_arabic": target.name_arabic,
                        "relationship": rel.relationship_type.value
                    })

        # Find descendants
        for rel in self.relationships.values():
            if rel.source_id == prophet_id and rel.relationship_type in [RelationshipType.FATHER_OF, RelationshipType.ANCESTOR_OF]:
                target = self.entities.get(rel.target_id)
                if target:
                    descendants.append({
                        "id": target.id,
                        "name_english": target.name_english,
                        "name_arabic": target.name_arabic,
                        "relationship": rel.relationship_type.value
                    })

        return {
            "prophet": {
                "id": prophet.id,
                "name_english": prophet.name_english,
                "name_arabic": prophet.name_arabic
            },
            "ancestors": ancestors,
            "descendants": descendants
        }

    def get_graph_visualization_data(self) -> Dict[str, Any]:
        """Get data formatted for graph visualization"""
        nodes = [
            {
                "id": e.id,
                "label": e.name_english,
                "label_arabic": e.name_arabic,
                "type": e.entity_type.value,
                "size": len(self.adjacency_list.get(e.id, [])) + 1
            }
            for e in self.entities.values()
        ]

        edges = [
            {
                "id": r.id,
                "source": r.source_id,
                "target": r.target_id,
                "type": r.relationship_type.value,
                "label": r.relationship_type.value.replace("_", " "),
                "bidirectional": r.bidirectional
            }
            for r in self.relationships.values()
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entity_types": [t.value for t in EntityType],
            "relationship_types": [t.value for t in RelationshipType]
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        type_counts = {}
        for e in self.entities.values():
            type_name = e.entity_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        rel_counts = {}
        for r in self.relationships.values():
            rel_name = r.relationship_type.value
            rel_counts[rel_name] = rel_counts.get(rel_name, 0) + 1

        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entities_by_type": type_counts,
            "relationships_by_type": rel_counts,
            "entity_types": [t.value for t in EntityType],
            "relationship_types": [t.value for t in RelationshipType]
        }


# Create singleton instance
enhanced_knowledge_graph_service = EnhancedKnowledgeGraphService()
