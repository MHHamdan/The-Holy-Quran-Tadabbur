"""
Entity-mention false positives (served by /api/v1/quran/entities/{id}).

- "أمه" (his mother) must not match "أمة" (a nation) after ة→ه
  normalisation; Maryam's named ayat come from QAC proper-noun lemmas.
- "الفلك" / "السفينة" are any ship: entity_object_ark keeps only the ayat
  that describe Nuh's ark (STORY_ENTITY_ALIAS_SCOPES, shared with the
  story-connections scan).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MENTIONS = ROOT / "frontend" / "src" / "data" / "generated" / "quranEntityMentions.json"

# Nuh's ark ranges, mirrored from STORY_ENTITY_ALIAS_SCOPES.entity_object_ark.
ARK_RANGES = [(7, 64, 64), (10, 73, 73), (11, 37, 44), (23, 27, 28), (26, 119, 119), (29, 15, 15), (54, 13, 13)]


def _entity(entity_id: str) -> dict:
    data = json.loads(MENTIONS.read_text(encoding="utf-8"))
    return next(e for e in data["entities"] if e["entityId"] == entity_id)


def test_maryam_has_no_umma_pronoun_matches():
    maryam = _entity("entity_person_maryam")
    pronoun = [(m["surahNumber"], m["ayahNumber"]) for m in maryam["mentions"] if m["mentionType"] == "pronoun_context"]
    assert pronoun == [], f"pronoun-only Maryam mentions: {pronoun}"
    refs = {(m["surahNumber"], m["ayahNumber"]) for m in maryam["mentions"]}
    for umma_ayah in [(2, 128), (2, 134), (2, 143), (3, 104), (3, 110), (4, 11)]:
        assert umma_ayah not in refs


def test_ark_mentions_stay_in_nuh_passages():
    ark = _entity("entity_object_ark")
    refs = {(m["surahNumber"], m["ayahNumber"]) for m in ark["mentions"]}
    assert refs, "ark has no mentions"
    for s, a in refs:
        assert any(s == rs and ra <= a <= rb for rs, ra, rb in ARK_RANGES), f"ark at {s}:{a} is a generic ship"
    for generic in [(2, 164), (10, 22), (14, 32), (16, 14), (18, 71), (18, 79), (30, 46), (37, 140)]:
        assert generic not in refs
    assert (7, 64) in refs and (10, 73) in refs


def test_scanner_uses_scopes_and_ta_marbuta_safe_pronouns():
    src = (ROOT / "scripts" / "scan-quran-entity-mentions.ts").read_text(encoding="utf-8")
    assert "STORY_ENTITY_ALIAS_SCOPES" in src
    assert "keepTaMarbuta" in src
