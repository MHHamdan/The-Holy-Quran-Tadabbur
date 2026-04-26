"""
Alignment and Mistake Detection for Tasmeeʿ (Memorization) feature.

This module provides word-level alignment between transcribed speech and
expected Quran text, along with mistake detection and classification.

Mistake Types:
1. SUBSTITUTION: Wrong word recited
2. DELETION: Word(s) skipped
3. INSERTION: Extra word(s) added
4. REPETITION: Word repeated (special case of insertion)
5. HESITATION: Long pause or filler

Algorithm Overview:
1. Maintain expected word pointer
2. Compare recognized tokens to expected tokens with normalization
3. Use edit distance for fuzzy matching
4. Require N consistent updates before firing alert (debouncing)
5. Track confidence and timing for each detection

References:
- Levenshtein distance for word matching
- Dynamic Time Warping concepts for sequence alignment
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .arabic_normalizer import (
    NormalizedWord,
    normalize_for_matching,
    tokenize_with_positions,
    word_similarity,
)
from .providers.base import TranscriptionSegment, WordInfo

logger = logging.getLogger(__name__)


class MistakeType(str, Enum):
    """Types of recitation mistakes."""

    SUBSTITUTION = "substitution"  # Wrong word
    DELETION = "deletion"  # Skipped word(s)
    INSERTION = "insertion"  # Extra word(s)
    REPETITION = "repetition"  # Repeated word
    HESITATION = "hesitation"  # Long pause / filler
    MISPRONUNCIATION = "mispronunciation"  # Partial match (fuzzy)


class MistakeSeverity(str, Enum):
    """Severity levels for mistakes."""

    MINOR = "minor"  # Small pronunciation variation
    MODERATE = "moderate"  # Wrong word but similar
    MAJOR = "major"  # Completely wrong or skipped


@dataclass
class Mistake:
    """Represents a detected recitation mistake."""

    type: MistakeType
    severity: MistakeSeverity
    position: int  # Word position in expected text
    expected_word: str  # What should have been recited
    expected_normalized: str  # Normalized form
    actual_word: Optional[str]  # What was recited (None for deletion)
    actual_normalized: Optional[str]  # Normalized form
    timestamp: float  # When the mistake occurred (seconds)
    confidence: float  # Detection confidence (0.0-1.0)
    context_before: List[str] = field(default_factory=list)  # Previous words
    context_after: List[str] = field(default_factory=list)  # Next words

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "position": self.position,
            "expected_word": self.expected_word,
            "expected_normalized": self.expected_normalized,
            "actual_word": self.actual_word,
            "actual_normalized": self.actual_normalized,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


@dataclass
class AlignmentState:
    """Current state of the alignment process."""

    expected_words: List[NormalizedWord]  # Full expected text
    current_position: int = 0  # Current word pointer
    recognized_words: List[str] = field(default_factory=list)  # All recognized
    mistakes: List[Mistake] = field(default_factory=list)  # Detected mistakes
    last_match_time: float = 0.0  # Time of last successful match
    pending_deletions: List[int] = field(default_factory=list)  # Potential skips

    # Debouncing state
    consecutive_mismatches: int = 0
    mismatch_buffer: List[Tuple[int, str, float]] = field(default_factory=list)

    @property
    def progress(self) -> float:
        """Progress through the expected text (0.0-1.0)."""
        if not self.expected_words:
            return 1.0
        return self.current_position / len(self.expected_words)

    @property
    def is_complete(self) -> bool:
        """Whether we've reached the end of expected text."""
        return self.current_position >= len(self.expected_words)

    @property
    def current_word(self) -> Optional[NormalizedWord]:
        """Get current expected word."""
        if self.is_complete:
            return None
        return self.expected_words[self.current_position]

    def get_window(self, size: int = 5) -> List[NormalizedWord]:
        """Get a window of expected words from current position."""
        end = min(self.current_position + size, len(self.expected_words))
        return self.expected_words[self.current_position:end]


@dataclass
class AlignmentResult:
    """Result of aligning a transcription segment."""

    matched: bool  # Whether transcription matched expected
    position: int  # Current position after alignment
    words_matched: int  # Number of words matched
    mistakes: List[Mistake]  # New mistakes detected
    confidence: float  # Overall confidence
    had_jump: bool = False  # Whether 2+ words were skipped
    skipped_positions: List[int] = field(default_factory=list)  # Positions that were skipped


class RecitationAligner:
    """
    Aligns transcribed speech with expected Quran text.

    This class maintains state between transcription updates and
    detects mistakes as they occur.
    """

    def __init__(
        self,
        expected_text: str,
        match_threshold: float = 0.75,
        deletion_patience: int = 3,
        mismatch_patience: int = 2,
        lookahead_window: int = 5,
    ):
        """
        Initialize the aligner with expected Quran text.

        Args:
            expected_text: Full expected recitation text (with diacritics)
            match_threshold: Minimum similarity for word match (0.0-1.0)
            deletion_patience: Updates to wait before confirming deletion
            mismatch_patience: Consecutive mismatches before alerting
            lookahead_window: Words to look ahead for alignment
        """
        self.match_threshold = match_threshold
        self.deletion_patience = deletion_patience
        self.mismatch_patience = mismatch_patience
        self.lookahead_window = lookahead_window

        # Initialize state
        expected_words = tokenize_with_positions(expected_text)
        self.state = AlignmentState(expected_words=expected_words)

        # Track original text for context
        self.original_text = expected_text

    def reset(self, expected_text: Optional[str] = None) -> None:
        """
        Reset alignment state.

        Args:
            expected_text: New expected text (or reuse existing)
        """
        if expected_text:
            expected_words = tokenize_with_positions(expected_text)
            self.original_text = expected_text
        else:
            expected_words = self.state.expected_words

        self.state = AlignmentState(expected_words=expected_words)

    def process_segment(
        self,
        segment: TranscriptionSegment,
    ) -> AlignmentResult:
        """
        Process a transcription segment and update alignment.

        Args:
            segment: Transcription segment from STT

        Returns:
            AlignmentResult with match status and any mistakes
        """
        if not segment.words:
            # No words in segment - might be silence
            return AlignmentResult(
                matched=True,
                position=self.state.current_position,
                words_matched=0,
                mistakes=[],
                confidence=0.5,
                had_jump=False,
                skipped_positions=[],
            )

        mistakes = []
        words_matched = 0
        had_jump = False
        all_skipped_positions = []

        for word_info in segment.words:
            if self.state.is_complete:
                # Past expected text - insertion
                mistake = self._create_insertion_mistake(word_info)
                mistakes.append(mistake)
                continue

            # Normalize recognized word
            recognized_normalized = normalize_for_matching(word_info.word)
            if not recognized_normalized:
                continue

            self.state.recognized_words.append(recognized_normalized)

            # Try to match
            match_result = self._try_match(recognized_normalized, word_info)

            if match_result["matched"]:
                words_matched += match_result["words_skipped"] + 1
                self.state.consecutive_mismatches = 0
                self.state.mismatch_buffer.clear()

                # Track jump detection
                if match_result.get("is_jump"):
                    had_jump = True
                    all_skipped_positions.extend(match_result["skipped_positions"])

                # Check for deletions (skipped words)
                if match_result["words_skipped"] > 0:
                    deletion_mistakes = self._create_deletion_mistakes(
                        match_result["skipped_positions"],
                        word_info.start_time,
                    )
                    mistakes.extend(deletion_mistakes)

                # Advance position
                self.state.current_position = match_result["new_position"]
                self.state.last_match_time = word_info.end_time

            else:
                # No match - potential mistake
                self.state.consecutive_mismatches += 1
                self.state.mismatch_buffer.append(
                    (self.state.current_position, recognized_normalized, word_info.start_time)
                )

                # Check if we should fire mistake alert
                if self.state.consecutive_mismatches >= self.mismatch_patience:
                    mistake = self._confirm_mistake(word_info)
                    if mistake:
                        mistakes.append(mistake)
                        self.state.consecutive_mismatches = 0
                        self.state.mismatch_buffer.clear()

        # Update state with mistakes
        self.state.mistakes.extend(mistakes)

        return AlignmentResult(
            matched=len(mistakes) == 0,
            position=self.state.current_position,
            words_matched=words_matched,
            mistakes=mistakes,
            confidence=self._calculate_confidence(),
            had_jump=had_jump,
            skipped_positions=all_skipped_positions,
        )

    def _try_match(
        self,
        recognized: str,
        word_info: WordInfo,
    ) -> Dict:
        """
        Try to match recognized word against expected words.

        Uses lookahead window to handle minor timing issues.
        Detects jumps (skipping 2+ words) for progressive reveal.

        Args:
            recognized: Normalized recognized word
            word_info: Full word info from transcription

        Returns:
            Dict with match status and details:
            - matched: Whether a match was found
            - new_position: Position after matching
            - words_skipped: Number of words skipped
            - skipped_positions: List of skipped word positions
            - similarity: Match similarity score
            - is_jump: True if 2+ words were skipped (for UI alerts)
        """
        result = {
            "matched": False,
            "new_position": self.state.current_position,
            "words_skipped": 0,
            "skipped_positions": [],
            "similarity": 0.0,
            "is_jump": False,
        }

        window = self.state.get_window(self.lookahead_window)
        if not window:
            return result

        # Check each word in window
        for i, expected_word in enumerate(window):
            similarity = word_similarity(recognized, expected_word.normalized)

            if similarity >= self.match_threshold:
                result["matched"] = True
                result["similarity"] = similarity
                result["words_skipped"] = i
                result["new_position"] = self.state.current_position + i + 1

                if i > 0:
                    # Record skipped positions for deletion detection
                    result["skipped_positions"] = list(
                        range(self.state.current_position, self.state.current_position + i)
                    )
                    # Mark as jump if 2+ words were skipped
                    if i >= 2:
                        result["is_jump"] = True

                return result

        return result

    def _create_deletion_mistakes(
        self,
        positions: List[int],
        timestamp: float,
    ) -> List[Mistake]:
        """Create mistakes for skipped words."""
        mistakes = []

        for pos in positions:
            expected = self.state.expected_words[pos]

            # Get context
            context_before = [
                self.state.expected_words[p].original
                for p in range(max(0, pos - 2), pos)
            ]
            context_after = [
                self.state.expected_words[p].original
                for p in range(pos + 1, min(len(self.state.expected_words), pos + 3))
            ]

            mistake = Mistake(
                type=MistakeType.DELETION,
                severity=MistakeSeverity.MAJOR,
                position=pos,
                expected_word=expected.original,
                expected_normalized=expected.normalized,
                actual_word=None,
                actual_normalized=None,
                timestamp=timestamp,
                confidence=0.9,  # High confidence for clear skips
                context_before=context_before,
                context_after=context_after,
            )
            mistakes.append(mistake)

        return mistakes

    def _create_insertion_mistake(self, word_info: WordInfo) -> Mistake:
        """Create mistake for extra word."""
        normalized = normalize_for_matching(word_info.word)

        # Check if it's a repetition
        if self.state.recognized_words and len(self.state.recognized_words) > 1:
            prev_word = self.state.recognized_words[-2]
            if word_similarity(normalized, prev_word) > 0.9:
                mistake_type = MistakeType.REPETITION
                severity = MistakeSeverity.MINOR
            else:
                mistake_type = MistakeType.INSERTION
                severity = MistakeSeverity.MODERATE
        else:
            mistake_type = MistakeType.INSERTION
            severity = MistakeSeverity.MODERATE

        return Mistake(
            type=mistake_type,
            severity=severity,
            position=self.state.current_position,
            expected_word="(none)",
            expected_normalized="",
            actual_word=word_info.word,
            actual_normalized=normalized,
            timestamp=word_info.start_time,
            confidence=0.8,
            context_before=[],
            context_after=[],
        )

    def _confirm_mistake(self, word_info: WordInfo) -> Optional[Mistake]:
        """
        Confirm and classify a mistake after patience threshold.

        This implements debouncing - we wait for consistent mismatches
        before reporting.
        """
        if not self.state.mismatch_buffer:
            return None

        # Get the first mismatch in buffer
        pos, recognized, timestamp = self.state.mismatch_buffer[0]

        if pos >= len(self.state.expected_words):
            return None

        expected = self.state.expected_words[pos]

        # Calculate similarity to determine severity
        similarity = word_similarity(recognized, expected.normalized)

        # Classify mistake
        if similarity >= 0.5:
            # Partial match - mispronunciation
            mistake_type = MistakeType.MISPRONUNCIATION
            severity = MistakeSeverity.MINOR
        else:
            # No match - substitution
            mistake_type = MistakeType.SUBSTITUTION
            severity = MistakeSeverity.MAJOR if similarity < 0.3 else MistakeSeverity.MODERATE

        # Get context
        context_before = [
            self.state.expected_words[p].original
            for p in range(max(0, pos - 2), pos)
        ]
        context_after = [
            self.state.expected_words[p].original
            for p in range(pos + 1, min(len(self.state.expected_words), pos + 3))
        ]

        mistake = Mistake(
            type=mistake_type,
            severity=severity,
            position=pos,
            expected_word=expected.original,
            expected_normalized=expected.normalized,
            actual_word=word_info.word,
            actual_normalized=recognized,
            timestamp=timestamp,
            confidence=0.7 + (0.3 * (1 - similarity)),  # Higher confidence for clearer mistakes
            context_before=context_before,
            context_after=context_after,
        )

        # Advance position past the mistake
        self.state.current_position = pos + 1

        return mistake

    def _calculate_confidence(self) -> float:
        """Calculate overall alignment confidence."""
        if not self.state.recognized_words:
            return 1.0

        total_expected = len(self.state.expected_words)
        mistakes = len(self.state.mistakes)

        if total_expected == 0:
            return 1.0

        # Base confidence on mistake rate
        mistake_rate = mistakes / max(1, len(self.state.recognized_words))
        base_confidence = max(0.0, 1.0 - mistake_rate)

        # Adjust for progress
        progress_factor = self.state.progress

        return base_confidence * (0.5 + 0.5 * progress_factor)

    def get_state(self) -> Dict:
        """Get current alignment state for UI."""
        return {
            "current_position": self.state.current_position,
            "total_words": len(self.state.expected_words),
            "progress": self.state.progress,
            "is_complete": self.state.is_complete,
            "current_word": (
                self.state.current_word.original
                if self.state.current_word
                else None
            ),
            "mistakes_count": len(self.state.mistakes),
            "confidence": self._calculate_confidence(),
        }

    def get_mistakes(self) -> List[Dict]:
        """Get all detected mistakes."""
        return [m.to_dict() for m in self.state.mistakes]

    def get_highlighted_text(self) -> List[Dict]:
        """
        Get text with word-by-word status for highlighting.

        Returns list of dicts with:
        - word: Original word text
        - status: 'completed' | 'current' | 'pending' | 'error'
        - mistake_type: Optional mistake type if error
        """
        result = []
        mistake_positions = {m.position for m in self.state.mistakes}

        for i, word in enumerate(self.state.expected_words):
            if i < self.state.current_position:
                if i in mistake_positions:
                    mistake = next(m for m in self.state.mistakes if m.position == i)
                    status = "error"
                    mistake_type = mistake.type.value
                else:
                    status = "completed"
                    mistake_type = None
            elif i == self.state.current_position:
                status = "current"
                mistake_type = None
            else:
                status = "pending"
                mistake_type = None

            result.append({
                "word": word.original,
                "normalized": word.normalized,
                "position": i,
                "status": status,
                "mistake_type": mistake_type,
            })

        return result


def align_transcription(
    expected_text: str,
    transcription_segments: List[TranscriptionSegment],
    match_threshold: float = 0.75,
) -> Tuple[List[Mistake], Dict]:
    """
    One-shot alignment of complete transcription.

    Useful for batch processing recorded recitations.

    Args:
        expected_text: Expected Quran text
        transcription_segments: All transcription segments
        match_threshold: Minimum similarity for matching

    Returns:
        Tuple of (mistakes list, alignment statistics)
    """
    aligner = RecitationAligner(expected_text, match_threshold=match_threshold)

    for segment in transcription_segments:
        aligner.process_segment(segment)

    stats = {
        "total_words": len(aligner.state.expected_words),
        "words_recognized": len(aligner.state.recognized_words),
        "words_matched": aligner.state.current_position,
        "mistakes": len(aligner.state.mistakes),
        "progress": aligner.state.progress,
        "is_complete": aligner.state.is_complete,
    }

    return aligner.state.mistakes, stats
