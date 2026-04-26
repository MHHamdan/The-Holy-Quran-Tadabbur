"""
Arabic Text Normalization for Tasmeeʿ (Memorization) feature.

This module provides comprehensive Arabic text normalization for matching
spoken transcriptions against Quran text. The normalization removes
diacritics, standardizes letter variants, and handles common variations.

Key Normalizations:
1. Remove diacritics (tashkeel): fatḥa, kasra, ḍamma, sukun, shadda, etc.
2. Normalize alef variants: أ إ آ ا -> ا
3. Normalize yaa/alif-maqsura: ى -> ي
4. Normalize ta marbuta: ة -> ه (for matching purposes)
5. Remove tatweel (kashida): ـ
6. Remove non-Arabic characters
7. Normalize whitespace

References:
- Unicode Arabic block: U+0600–U+06FF
- Arabic Presentation Forms-A: U+FB50–U+FDFF
- Arabic Presentation Forms-B: U+FE70–U+FEFF
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Tuple


# Arabic Unicode ranges and character sets
ARABIC_DIACRITICS = (
    "\u064B"  # FATHATAN
    "\u064C"  # DAMMATAN
    "\u064D"  # KASRATAN
    "\u064E"  # FATHA
    "\u064F"  # DAMMA
    "\u0650"  # KASRA
    "\u0651"  # SHADDA
    "\u0652"  # SUKUN
    "\u0653"  # MADDAH ABOVE
    "\u0654"  # HAMZA ABOVE
    "\u0655"  # HAMZA BELOW
    "\u0656"  # SUBSCRIPT ALEF
    "\u0657"  # INVERTED DAMMA
    "\u0658"  # NOON GHUNNA
    "\u0659"  # ZWARAKAY
    "\u065A"  # VOWEL SIGN SMALL V ABOVE
    "\u065B"  # VOWEL SIGN INVERTED SMALL V ABOVE
    "\u065C"  # VOWEL SIGN DOT BELOW
    "\u065D"  # VOWEL SIGN REVERSED DAMMA
    "\u065E"  # VOWEL SIGN FATHA WITH TWO DOTS
    "\u065F"  # WAVY HAMZA BELOW
    "\u0670"  # SUPERSCRIPT ALEF
    "\u06D6"  # SMALL HIGH LIGATURE SAD WITH LAM WITH ALEF MAKSURA
    "\u06D7"  # SMALL HIGH LIGATURE QAF WITH LAM WITH ALEF MAKSURA
    "\u06D8"  # SMALL HIGH MEEM INITIAL FORM
    "\u06D9"  # SMALL HIGH LAM ALEF
    "\u06DA"  # SMALL HIGH JEEM
    "\u06DB"  # SMALL HIGH THREE DOTS
    "\u06DC"  # SMALL HIGH SEEN
    "\u06DF"  # SMALL HIGH ROUNDED ZERO
    "\u06E0"  # SMALL HIGH UPRIGHT RECTANGULAR ZERO
    "\u06E1"  # SMALL HIGH DOTLESS HEAD OF KHAH
    "\u06E2"  # SMALL HIGH MEEM ISOLATED FORM
    "\u06E3"  # SMALL LOW SEEN
    "\u06E4"  # SMALL HIGH MADDA
    "\u06E7"  # SMALL HIGH YEH
    "\u06E8"  # SMALL HIGH NOON
    "\u06EA"  # EMPTY CENTRE LOW STOP
    "\u06EB"  # EMPTY CENTRE HIGH STOP
    "\u06EC"  # ROUNDED HIGH STOP WITH FILLED CENTRE
    "\u06ED"  # SMALL LOW MEEM
)

# Alef variants to normalize
ALEF_VARIANTS = {
    "\u0622": "\u0627",  # ALEF WITH MADDA ABOVE -> ALEF
    "\u0623": "\u0627",  # ALEF WITH HAMZA ABOVE -> ALEF
    "\u0625": "\u0627",  # ALEF WITH HAMZA BELOW -> ALEF
    "\u0671": "\u0627",  # ALEF WASLA -> ALEF
    "\u0672": "\u0627",  # ALEF WITH WAVY HAMZA ABOVE -> ALEF
    "\u0673": "\u0627",  # ALEF WITH WAVY HAMZA BELOW -> ALEF
    "\u0675": "\u0627",  # HIGH HAMZA ALEF -> ALEF
}

# Yaa variants
YAA_VARIANTS = {
    "\u0649": "\u064A",  # ALEF MAKSURA -> YEH
    "\u06CC": "\u064A",  # FARSI YEH -> YEH
    "\u06CD": "\u064A",  # YEH WITH TAIL -> YEH
    "\u06D0": "\u064A",  # E -> YEH
    "\u06D1": "\u064A",  # YEH WITH THREE DOTS BELOW -> YEH
}

# Ta marbuta
TA_MARBUTA = "\u0629"  # ة
HA = "\u0647"  # ه

# Tatweel (kashida)
TATWEEL = "\u0640"

# Hamza variants
HAMZA_VARIANTS = {
    "\u0621": "",  # HAMZA (isolated) - remove
    "\u0624": "\u0648",  # WAW WITH HAMZA ABOVE -> WAW
    "\u0626": "\u064A",  # YEH WITH HAMZA ABOVE -> YEH
}

# Compile regex patterns
DIACRITICS_PATTERN = re.compile(f"[{ARABIC_DIACRITICS}]")
# Allows Arabic letters but excludes Arabic punctuation (commas, semicolons, etc.)
NON_ARABIC_PATTERN = re.compile(r"[^\u0621-\u063A\u0641-\u064A\u0660-\u0669\u0671-\u06D3\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\s]")
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass
class NormalizedWord:
    """A word with its original and normalized forms."""

    original: str
    normalized: str
    position: int  # Position in original text

    def __eq__(self, other):
        if isinstance(other, NormalizedWord):
            return self.normalized == other.normalized
        if isinstance(other, str):
            return self.normalized == other
        return False

    def __hash__(self):
        return hash(self.normalized)


def remove_diacritics(text: str) -> str:
    """
    Remove Arabic diacritics (tashkeel) from text.

    Args:
        text: Arabic text with diacritics

    Returns:
        Text without diacritics
    """
    return DIACRITICS_PATTERN.sub("", text)


def normalize_alef(text: str) -> str:
    """
    Normalize alef variants to plain alef.

    أ إ آ ا -> ا
    """
    for variant, replacement in ALEF_VARIANTS.items():
        text = text.replace(variant, replacement)
    return text


def normalize_yaa(text: str) -> str:
    """
    Normalize yaa variants and alif maqsura to plain yaa.

    ى -> ي
    """
    for variant, replacement in YAA_VARIANTS.items():
        text = text.replace(variant, replacement)
    return text


def normalize_ta_marbuta(text: str) -> str:
    """
    Normalize ta marbuta to ha for matching purposes.

    ة -> ه

    Note: This is for fuzzy matching. In strict mode, keep them separate.
    """
    return text.replace(TA_MARBUTA, HA)


def normalize_hamza(text: str) -> str:
    """
    Normalize hamza variants.

    Hamza on carriers -> base letter
    Isolated hamza -> removed
    """
    for variant, replacement in HAMZA_VARIANTS.items():
        text = text.replace(variant, replacement)
    return text


def remove_tatweel(text: str) -> str:
    """
    Remove tatweel (kashida) character.

    ـ -> (removed)
    """
    return text.replace(TATWEEL, "")


def remove_non_arabic(text: str) -> str:
    """
    Remove non-Arabic characters except whitespace.

    Keeps: Arabic letters, Arabic-Indic digits, whitespace
    Removes: Latin letters, punctuation, other scripts
    """
    return NON_ARABIC_PATTERN.sub("", text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace: multiple spaces -> single space, trim.
    """
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def normalize_arabic(
    text: str,
    remove_diacritics_flag: bool = True,
    normalize_alef_flag: bool = True,
    normalize_yaa_flag: bool = True,
    normalize_ta_marbuta_flag: bool = False,  # Off by default - can affect meaning
    normalize_hamza_flag: bool = True,
    remove_tatweel_flag: bool = True,
    remove_non_arabic_flag: bool = True,
    normalize_whitespace_flag: bool = True,
) -> str:
    """
    Apply full Arabic normalization pipeline.

    Args:
        text: Arabic text to normalize
        remove_diacritics_flag: Remove tashkeel
        normalize_alef_flag: Normalize alef variants
        normalize_yaa_flag: Normalize yaa variants
        normalize_ta_marbuta_flag: Convert ta marbuta to ha
        normalize_hamza_flag: Normalize hamza variants
        remove_tatweel_flag: Remove kashida
        remove_non_arabic_flag: Remove non-Arabic characters
        normalize_whitespace_flag: Normalize spaces

    Returns:
        Normalized Arabic text
    """
    if remove_tatweel_flag:
        text = remove_tatweel(text)

    if remove_diacritics_flag:
        text = remove_diacritics(text)

    if normalize_alef_flag:
        text = normalize_alef(text)

    if normalize_yaa_flag:
        text = normalize_yaa(text)

    if normalize_ta_marbuta_flag:
        text = normalize_ta_marbuta(text)

    if normalize_hamza_flag:
        text = normalize_hamza(text)

    if remove_non_arabic_flag:
        text = remove_non_arabic(text)

    if normalize_whitespace_flag:
        text = normalize_whitespace(text)

    return text


def tokenize_arabic(text: str, normalize: bool = True) -> List[str]:
    """
    Tokenize Arabic text into words.

    Args:
        text: Arabic text
        normalize: Whether to normalize each token

    Returns:
        List of words (tokens)
    """
    # First normalize whitespace
    text = normalize_whitespace(text)

    # Split on whitespace
    words = text.split()

    if normalize:
        words = [normalize_arabic(w) for w in words]

    # Filter empty strings
    return [w for w in words if w]


def tokenize_with_positions(text: str) -> List[NormalizedWord]:
    """
    Tokenize Arabic text with original and normalized forms.

    Args:
        text: Arabic text (potentially with diacritics)

    Returns:
        List of NormalizedWord objects with position info
    """
    words = []
    current_pos = 0

    for word in text.split():
        if word.strip():
            normalized = normalize_arabic(word)
            if normalized:  # Only add if normalization produces content
                words.append(
                    NormalizedWord(
                        original=word,
                        normalized=normalized,
                        position=current_pos,
                    )
                )
        current_pos += 1

    return words


def normalize_for_matching(text: str) -> str:
    """
    Normalize text specifically for matching transcription to Quran.

    This is a strict normalization that maximizes matching flexibility
    while preserving word boundaries.

    Args:
        text: Text to normalize (transcription or Quran text)

    Returns:
        Normalized text ready for matching
    """
    return normalize_arabic(
        text,
        remove_diacritics_flag=True,
        normalize_alef_flag=True,
        normalize_yaa_flag=True,
        normalize_ta_marbuta_flag=True,  # Enable for matching
        normalize_hamza_flag=True,
        remove_tatweel_flag=True,
        remove_non_arabic_flag=True,
        normalize_whitespace_flag=True,
    )


def word_similarity(word1: str, word2: str) -> float:
    """
    Calculate similarity between two Arabic words.

    Uses Levenshtein distance normalized by max length.

    Args:
        word1: First word (normalized)
        word2: Second word (normalized)

    Returns:
        Similarity score 0.0 to 1.0
    """
    if word1 == word2:
        return 1.0

    if not word1 or not word2:
        return 0.0

    # Calculate Levenshtein distance
    len1, len2 = len(word1), len(word2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if word1[i - 1] == word2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    distance = dp[len1][len2]
    max_len = max(len1, len2)

    return 1.0 - (distance / max_len)


def find_best_match(
    word: str,
    candidates: List[str],
    threshold: float = 0.7,
) -> Tuple[Optional[int], float]:
    """
    Find the best matching word from candidates.

    Args:
        word: Word to match (normalized)
        candidates: List of candidate words (normalized)
        threshold: Minimum similarity threshold

    Returns:
        Tuple of (best_index, similarity_score) or (None, 0.0) if no match
    """
    best_idx = None
    best_score = 0.0

    for i, candidate in enumerate(candidates):
        score = word_similarity(word, candidate)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_score >= threshold:
        return best_idx, best_score

    return None, 0.0


def get_quran_words(
    text: str, include_bismillah: bool = False
) -> List[NormalizedWord]:
    """
    Extract and normalize words from Quran text.

    Args:
        text: Quran verse text (with diacritics)
        include_bismillah: Whether to include Bismillah if present

    Returns:
        List of NormalizedWord objects
    """
    # Optionally remove Bismillah
    if not include_bismillah:
        bismillah = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        bismillah_normalized = normalize_for_matching(bismillah)
        text_normalized = normalize_for_matching(text)

        if text_normalized.startswith(bismillah_normalized):
            # Find where bismillah ends in original text
            # This is approximate - find the position after "الرحيم"
            raheem_pos = text.find("الرَّحِيمِ")
            if raheem_pos != -1:
                text = text[raheem_pos + len("الرَّحِيمِ"):].strip()

    return tokenize_with_positions(text)


class ArabicNormalizer:
    """
    Class-based normalizer with configurable options.

    Useful when you need consistent normalization across multiple calls
    with the same settings.
    """

    def __init__(
        self,
        remove_diacritics: bool = True,
        normalize_alef: bool = True,
        normalize_yaa: bool = True,
        normalize_ta_marbuta: bool = False,
        normalize_hamza: bool = True,
        remove_tatweel: bool = True,
        remove_non_arabic: bool = True,
        normalize_whitespace: bool = True,
    ):
        self.remove_diacritics = remove_diacritics
        self.normalize_alef = normalize_alef
        self.normalize_yaa = normalize_yaa
        self.normalize_ta_marbuta = normalize_ta_marbuta
        self.normalize_hamza = normalize_hamza
        self.remove_tatweel = remove_tatweel
        self.remove_non_arabic = remove_non_arabic
        self.normalize_whitespace = normalize_whitespace

    def normalize(self, text: str) -> str:
        """Normalize text with configured options."""
        return normalize_arabic(
            text,
            remove_diacritics_flag=self.remove_diacritics,
            normalize_alef_flag=self.normalize_alef,
            normalize_yaa_flag=self.normalize_yaa,
            normalize_ta_marbuta_flag=self.normalize_ta_marbuta,
            normalize_hamza_flag=self.normalize_hamza,
            remove_tatweel_flag=self.remove_tatweel,
            remove_non_arabic_flag=self.remove_non_arabic,
            normalize_whitespace_flag=self.normalize_whitespace,
        )

    def tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text."""
        return tokenize_arabic(text, normalize=True)

    def tokenize_with_info(self, text: str) -> List[NormalizedWord]:
        """Tokenize with position information."""
        return tokenize_with_positions(text)
