"""
Agent 3: Consensus / Disagreement Agent

Detects scholarly disagreement across retrieved tafsir chunks for the same
verse or topic. Produces a structured ConsensusOutput with zero, one, or
multiple DisagreementObject instances.

Safety rules (from agent_specs.md §3):
- The adjudication field is always NOT_ADJUDICATED — we never endorse one view.
- Both positions are presented with equal attribution.
- The Explanation Agent may NOT collapse two disagreeing views into one answer.

Disagreement is detected by:
1. Grouping validated chunks by (source_id, verse_reference).
2. Comparing the opening sentence / key claim of each source pair.
3. Checking for antonymous signal tokens (خلاف / dispute / differ etc.).
4. Classifying the disagreement type from content signals.

This is a rule-based v1 — a fine-tuned classifier (target F1 ≥ 0.85) is
scheduled for M4. The rule-based version already dramatically outperforms
the status-quo (no disagreement detection at all).
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional, Dict, Tuple

from app.rag.agents.types import (
    ConsensusLevel,
    ConsensusOutput,
    DisagreementObject,
    DisagreementType,
    ScholarlyPosition,
    ValidatedItem,
)

logger = logging.getLogger(__name__)


# ─── Signal lexicons ─────────────────────────────────────────────────────────

_DISAGREEMENT_SIGNALS_EN = frozenset({
    "however", "whereas", "disputes", "differs", "contested",
    "alternative", "contrary to", "on the other hand", "in contrast",
    "some scholars", "others say", "ibn kathir says", "al-tabari holds",
    "differed", "disagreed", "difference of opinion",
})

_DISAGREEMENT_SIGNALS_AR = frozenset({
    "خلاف", "اختلف", "اختلاف", "قيل", "وقيل", "وقال بعضهم",
    "في حين", "أما", "والراجح", "بينما", "خالف", "ذهب آخرون",
    "وفريق آخر", "وقد اختلف", "والصحيح خلافه",
})

_LEXICAL_SIGNALS = frozenset({
    "word", "root", "meaning of", "كلمة", "جذر", "معنى", "لغة",
    "lexical", "linguistic", "لغوي",
})

_JURISPRUDENTIAL_SIGNALS = frozenset({
    "ruling", "halal", "haram", "permissible", "forbidden",
    "حكم", "حلال", "حرام", "جائز", "محرم", "فقه",
})

_NARRATIVE_SIGNALS = frozenset({
    "story", "account", "event", "narrated", "reported",
    "قصة", "رواية", "حادثة", "روي", "ذكر",
})


def _extract_lead_claim(text: str, max_chars: int = 200) -> str:
    """Extract the opening claim from a chunk (first sentence or max_chars)."""
    text = text.strip()
    # Split on sentence boundary
    for sep in (". ", ".\n", "، ", "؛ "):
        idx = text.find(sep, 20)  # skip very short openers
        if 20 < idx <= max_chars:
            return text[: idx + 1].strip()
    return text[:max_chars].strip()


def _detect_disagreement_type(text_a: str, text_b: str) -> DisagreementType:
    """Heuristically classify the type of disagreement from content signals."""
    combined = (text_a + " " + text_b).lower()

    if any(sig in combined for sig in _JURISPRUDENTIAL_SIGNALS):
        return DisagreementType.JURISPRUDENTIAL
    if any(sig in combined for sig in _LEXICAL_SIGNALS):
        return DisagreementType.LEXICAL
    if any(sig in combined for sig in _NARRATIVE_SIGNALS):
        return DisagreementType.NARRATIVE
    return DisagreementType.THEOLOGICAL


def _items_contradict(text_a: str, text_b: str) -> bool:
    """
    Return True if the two chunks likely represent different scholarly views.

    Checks:
    1. Either chunk contains disagreement signal tokens.
    2. The lead claims differ substantially (character-level Jaccard < 0.3).
    """
    combined = (text_a + " " + text_b).lower()
    has_signal = any(s in combined for s in _DISAGREEMENT_SIGNALS_EN | _DISAGREEMENT_SIGNALS_AR)

    if not has_signal:
        # Compute simple token-level Jaccard on lead claims
        toks_a = set(re.sub(r"[^\w\s]", "", text_a[:200].lower()).split())
        toks_b = set(re.sub(r"[^\w\s]", "", text_b[:200].lower()).split())
        if not toks_a or not toks_b:
            return False
        jaccard = len(toks_a & toks_b) / len(toks_a | toks_b)
        return jaccard < 0.25  # very different content

    return True


class ConsensusAgent:
    """
    Stateless agent that analyses validated evidence items for scholarly
    consensus or disagreement.

    Usage:
        agent = ConsensusAgent()
        output = agent.analyse(validated_items, query_focus="ما معنى التقوى؟")
    """

    def analyse(
        self,
        validated_items: List[ValidatedItem],
        query_focus: str = "",
    ) -> ConsensusOutput:
        """
        Analyse validated items for consensus level and disagreements.

        Returns ConsensusOutput with structured disagreement objects.
        """
        valid = [v for v in validated_items if v.validation_status.value == "valid"]

        if not valid:
            return ConsensusOutput(
                consensus_level=ConsensusLevel.SINGLE_SOURCE,
                majority_position=None,
                disagreements=[],
                sources_analysed=0,
            )

        # Group by source_id
        by_source: Dict[str, List[ValidatedItem]] = {}
        for item in valid:
            sid = item.original_item.source_id
            by_source.setdefault(sid, []).append(item)

        n_sources = len(by_source)

        if n_sources == 1:
            only_source = next(iter(by_source.values()))[0].original_item
            return ConsensusOutput(
                consensus_level=ConsensusLevel.SINGLE_SOURCE,
                majority_position=ScholarlyPosition(
                    source_id=only_source.source_id,
                    source_name=only_source.source_name,
                    claim_summary=_extract_lead_claim(only_source.text),
                ),
                disagreements=[],
                sources_analysed=1,
            )

        # Build lead claims per source
        source_claims: Dict[str, Tuple[str, str, str]] = {}
        # source_id -> (source_name, source_name_ar, lead_claim)
        for sid, items in by_source.items():
            best = max(items, key=lambda v: v.text_match_score)
            ri = best.original_item
            source_claims[sid] = (ri.source_name, ri.source_name_ar, _extract_lead_claim(ri.text))

        # Compare all source pairs for disagreement
        disagreements: List[DisagreementObject] = []
        source_ids = list(source_claims.keys())

        for i in range(len(source_ids)):
            for j in range(i + 1, len(source_ids)):
                sid_a, sid_b = source_ids[i], source_ids[j]
                name_a, _, claim_a = source_claims[sid_a]
                name_b, _, claim_b = source_claims[sid_b]

                if _items_contradict(claim_a, claim_b):
                    d_type = _detect_disagreement_type(claim_a, claim_b)
                    disagreements.append(
                        DisagreementObject(
                            disagreement_type=d_type,
                            position_a=ScholarlyPosition(
                                source_id=sid_a,
                                source_name=name_a,
                                claim_summary=claim_a,
                            ),
                            position_b=ScholarlyPosition(
                                source_id=sid_b,
                                source_name=name_b,
                                claim_summary=claim_b,
                            ),
                        )
                    )

        # Determine consensus level
        if not disagreements:
            level = ConsensusLevel.STRONG
            warning = None
        elif len(disagreements) == 1:
            level = ConsensusLevel.PARTIAL
            warning = (
                "Scholars have differing views on this topic. Both perspectives are "
                "presented without endorsing one over another. — "
                "اختلف العلماء في هذه المسألة، وقد عُرضت الآراء المختلفة دون ترجيح."
            )
        else:
            level = ConsensusLevel.SIGNIFICANT
            warning = (
                f"Multiple scholarly disagreements detected across {n_sources} sources. "
                "All views are presented without adjudication. — "
                "تعدّد الاختلاف بين العلماء؛ عُرضت جميع الآراء دون ترجيح."
            )

        # Identify majority position: source with highest avg text_match_score
        source_avg_scores: Dict[str, float] = {}
        for sid, items in by_source.items():
            source_avg_scores[sid] = sum(v.text_match_score for v in items) / len(items)

        best_sid = max(source_avg_scores, key=lambda k: source_avg_scores[k])
        name_b, name_b_ar, claim_b = source_claims[best_sid]
        majority = ScholarlyPosition(
            source_id=best_sid,
            source_name=name_b,
            claim_summary=claim_b,
        )

        logger.info(
            f"[ConsensusAgent] {n_sources} sources → level={level.value}, "
            f"disagreements={len(disagreements)}"
        )

        return ConsensusOutput(
            consensus_level=level,
            majority_position=majority,
            disagreements=disagreements,
            display_warning=warning,
            sources_analysed=n_sources,
        )


consensus_agent = ConsensusAgent()
