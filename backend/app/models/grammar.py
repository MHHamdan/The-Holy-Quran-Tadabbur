"""
Arabic Grammar (إعراب) Models for Quranic Text Analysis.

This module provides:
1. Part-of-Speech (POS) tags for Arabic
2. Grammatical roles (إعراب)
3. Sentence types
4. Dependency relations

GROUNDING POLICY:
=================
Grammar analysis should be GROUNDED in:
1. Classical Arabic grammar rules (النحو والصرف)
2. Quranic Arabic corpus data when available
3. Local LLM analysis with confidence scores

OUTPUT must be in Arabic labels (not transliterations).

LABELS ARE CONSTRAINED:
- Only predefined labels from this file are allowed
- LLM must output from this label set
- Unknown/uncertain should use explicit "غير محدد" label
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


class POSTag(str, Enum):
    """
    Part-of-Speech tags in Arabic.

    Based on classical Arabic grammar (أقسام الكلام).
    """
    # Main categories (أقسام الكلام الثلاثة)
    NOUN = "اسم"         # Noun (includes pronouns, proper nouns, etc.)
    VERB = "فعل"         # Verb
    PARTICLE = "حرف"     # Particle

    # Noun subtypes
    NOUN_PROPER = "اسم علم"      # Proper noun
    NOUN_PRONOUN = "ضمير"        # Pronoun
    NOUN_DEMONSTRATIVE = "اسم إشارة"  # Demonstrative
    NOUN_RELATIVE = "اسم موصول"   # Relative pronoun
    NOUN_INTERROGATIVE = "اسم استفهام"  # Interrogative
    NOUN_MASDAR = "مصدر"         # Verbal noun

    # Verb subtypes
    VERB_PAST = "فعل ماض"        # Past tense
    VERB_PRESENT = "فعل مضارع"    # Present/future tense
    VERB_IMPERATIVE = "فعل أمر"   # Imperative

    # Particle subtypes
    PARTICLE_PREP = "حرف جر"      # Preposition
    PARTICLE_CONJ = "حرف عطف"     # Conjunction
    PARTICLE_NEG = "حرف نفي"      # Negation particle
    PARTICLE_INTERROG = "حرف استفهام"  # Interrogative particle
    PARTICLE_COND = "حرف شرط"     # Conditional particle
    PARTICLE_EXCEPT = "حرف استثناء"  # Exception particle

    # Special
    UNKNOWN = "غير محدد"


class GrammaticalRole(str, Enum):
    """
    Grammatical roles (الإعراب) in Arabic.

    These represent the syntactic function of words in a sentence.
    """
    # Nominal sentence (جملة اسمية) roles
    MUBTADA = "مبتدأ"       # Subject of nominal sentence
    KHABAR = "خبر"          # Predicate of nominal sentence

    # Verbal sentence (جملة فعلية) roles
    FAEL = "فاعل"           # Subject/doer (nominative)
    NAEB_FAEL = "نائب فاعل"  # Deputy subject (passive voice)
    MAFUL_BIH = "مفعول به"   # Direct object (accusative)
    MAFUL_LAHU = "مفعول لأجله"  # Object of purpose
    MAFUL_FIHI = "مفعول فيه"  # Adverb of time/place (ظرف)
    MAFUL_MUTLAQ = "مفعول مطلق"  # Cognate accusative
    MAFUL_MAAHU = "مفعول معه"  # Object of accompaniment

    # Adjuncts
    HAL = "حال"             # Circumstantial accusative
    TAMYIZ = "تمييز"        # Specification/distinction
    MUSTATHNA = "مستثنى"     # Exception

    # Genitive constructions
    MUDAF = "مضاف"          # First part of genitive construction
    MUDAF_ILAYH = "مضاف إليه"  # Second part (genitive)
    JARR_MAJRUR = "جار ومجرور"  # Prepositional phrase
    MAJRUR = "مجرور"        # Genitive (after preposition)

    # Attributes and apposition
    NAT = "نعت"             # Adjective/attribute
    MANUT = "منعوت"          # Modified noun
    BADAL = "بدل"           # Apposition
    ATAF = "معطوف"          # Coordinated element
    MATUF_ALAYH = "معطوف عليه"  # Element being coordinated with
    TAWKID = "توكيد"        # Emphasis

    # Vocative
    MUNADA = "منادى"        # Vocative (called person/thing)

    # Special
    KANA_KHABAR = "خبر كان"  # Predicate of كان and sisters
    INNA_ISM = "اسم إن"     # Subject of إن and sisters
    INNA_KHABAR = "خبر إن"  # Predicate of إن and sisters

    # Verb-related
    VERB_ROOT = "جذر الفعل"  # Verb root

    UNKNOWN = "غير محدد"


class SentenceType(str, Enum):
    """
    Arabic sentence types.
    """
    NOMINAL = "جملة اسمية"    # Starts with noun (مبتدأ)
    VERBAL = "جملة فعلية"     # Starts with verb
    SEMI = "شبه جملة"         # Prepositional/adverbial phrase
    UNKNOWN = "غير محدد"


class CaseEnding(str, Enum):
    """
    Grammatical case endings (علامات الإعراب).
    """
    DAMMA = "ضمة"            # Nominative (مرفوع)
    FATHA = "فتحة"           # Accusative (منصوب)
    KASRA = "كسرة"           # Genitive (مجرور)
    SUKUN = "سكون"           # For jussive verbs (مجزوم)
    WAW = "الواو"            # Nominative for 5 nouns
    ALIF = "الألف"           # Accusative for dual
    YA = "الياء"             # Genitive for dual/plural
    NONE = "مبني"            # Indeclinable
    UNKNOWN = "غير محدد"


@dataclass
class TokenAnalysis:
    """
    Analysis of a single token/word.
    """
    word: str                           # The Arabic word
    word_index: int                     # Position in verse/sentence
    pos: POSTag                         # Part of speech
    role: GrammaticalRole               # Grammatical role
    case_ending: Optional[CaseEnding] = None  # Case ending
    i3rab: str = ""                     # Full إعراب explanation in Arabic
    root: Optional[str] = None          # Root letters (جذر)
    pattern: Optional[str] = None       # Morphological pattern (وزن)
    confidence: float = 1.0             # Confidence score (0-1)
    notes_ar: str = ""                  # Additional notes in Arabic

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "word_index": self.word_index,
            "pos": self.pos.value,
            "role": self.role.value,
            "case_ending": self.case_ending.value if self.case_ending else None,
            "i3rab": self.i3rab,
            "root": self.root,
            "pattern": self.pattern,
            "confidence": self.confidence,
            "notes_ar": self.notes_ar,
        }


@dataclass
class GrammarAnalysis:
    """
    Complete grammar analysis of a verse or text span.
    """
    verse_reference: str                # e.g., "2:255"
    text: str                           # Original Arabic text
    sentence_type: SentenceType         # Type of sentence
    tokens: List[TokenAnalysis]         # Token-by-token analysis
    notes_ar: str = ""                  # Overall notes in Arabic
    overall_confidence: float = 1.0     # Overall confidence
    source: str = "llm"                 # "corpus", "llm", "hybrid"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verse_reference": self.verse_reference,
            "text": self.text,
            "sentence_type": self.sentence_type.value,
            "tokens": [t.to_dict() for t in self.tokens],
            "notes_ar": self.notes_ar,
            "overall_confidence": self.overall_confidence,
            "source": self.source,
        }


# Valid values for LLM output validation
VALID_POS_TAGS = {tag.value for tag in POSTag}
VALID_ROLES = {role.value for role in GrammaticalRole}
VALID_SENTENCE_TYPES = {st.value for st in SentenceType}
VALID_CASE_ENDINGS = {ce.value for ce in CaseEnding}


def validate_grammar_output(output: Dict[str, Any]) -> List[str]:
    """
    Validate LLM grammar output against allowed labels.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    # Validate sentence type
    sentence_type = output.get("sentence_type", "")
    if sentence_type and sentence_type not in VALID_SENTENCE_TYPES:
        errors.append(f"Invalid sentence_type: {sentence_type}")

    # Validate tokens
    for i, token in enumerate(output.get("tokens", [])):
        pos = token.get("pos", "")
        role = token.get("role", "")

        if pos and pos not in VALID_POS_TAGS:
            errors.append(f"Token {i}: Invalid pos '{pos}'")

        if role and role not in VALID_ROLES:
            errors.append(f"Token {i}: Invalid role '{role}'")

    return errors
