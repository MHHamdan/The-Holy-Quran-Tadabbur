"""
Situation atlas and topic knowledge: no filler hadith, no Qur'an text in code.

- 23 of 25 situations used to cite Bukhari 5017 (reciting the Mu'awwidhat
  before sleep) as their evidence, including loss of a child or spouse.
- DUA_BANK held 21:87 and part of 9:129 as Arabic literals although its header
  said no Qur'anic text was duplicated there.
- Topic hadith carried grades with no named grader and no hadith numbers.
"""
import json
import re
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.situation_atlas import DUA_BANK, SITUATION_ATLAS
from app.services.topic_knowledge_service import (
    _TOPIC_KNOWLEDGE,
    get_all_topic_keys,
    get_topic_resources,
)

ROOT = Path(__file__).resolve().parents[3]
_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def _skeleton_words(text: str) -> list[str]:
    text = _DIACRITICS.sub("", text)
    text = re.sub("[آأإٱ]", "ا", text).replace("ى", "ي").replace("ة", "ه")
    return re.findall(r"[ء-ي]+", text)


@pytest.fixture(scope="module")
def quran_5grams():
    data = json.loads((ROOT / "data" / "raw" / "quran_tanzil.json").read_text(encoding="utf-8"))
    grams = set()
    for v in data["verses"]:
        w = _skeleton_words(v["aya_text_emlaey"])
        grams.update(tuple(w[i:i + 5]) for i in range(len(w) - 4))
    return grams


def test_filler_reference_is_gone():
    for s in SITUATION_ATLAS:
        assert all(h.number != "5017" for h in s.hadith_refs), s.key


def test_no_hadith_reused_as_filler():
    uses = Counter(f"{h.collection}:{h.number}" for s in SITUATION_ATLAS for h in s.hadith_refs)
    assert all(n <= 3 for n in uses.values()), uses


def test_dua_bank_holds_no_quran_text(quran_5grams):
    for key, d in DUA_BANK.items():
        for field in ("arabic", "translation_ar"):
            words = _skeleton_words(d.get(field, ""))
            hits = [g for g in (tuple(words[i:i + 5]) for i in range(len(words) - 4)) if g in quran_5grams]
            assert not hits, f"DUA_BANK[{key}].{field} contains Qur'an text: {hits[:1]}"


def test_quranic_duas_are_references():
    assert DUA_BANK["la_ilaha_distress"]["quran_ref"] == "21:87"
    assert DUA_BANK["hasbi_allah"]["quran_ref"] == "9:129"


def test_loss_of_child_has_no_unrelated_hadith():
    with TestClient(app) as client:
        r = client.get("/api/v1/therapy/situations/loss_of_child")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "5017" not in json.dumps(body)
    assert not body.get("hadith_refs")
    assert body["disclaimer_en"] and body["disclaimer_ar"]


def test_situation_quranic_dua_is_served_by_reference():
    with TestClient(app) as client:
        r = client.get("/api/v1/therapy/situations/caring_for_sick_loved_one")
    duas = {d["key"]: d for d in r.json()["duas"]}
    assert duas["hasbi_allah"]["quran_ref"] == "9:129"
    assert duas["hasbi_allah"]["arabic"] is None


class TestTopicHadith:
    def test_unverified_hadith_are_withheld(self):
        for key in get_all_topic_keys():
            block = get_topic_resources(key)
            for h in block["hadith"]:
                assert h.get("collection") and h.get("number"), key
                if h.get("grade"):
                    assert h.get("grader"), f"{key}: grade without grader"

    def test_store_is_not_mutated(self):
        before = sum(len(b["hadith"]) for b in _TOPIC_KNOWLEDGE.values())
        for key in get_all_topic_keys():
            get_topic_resources(key)
        assert sum(len(b["hadith"]) for b in _TOPIC_KNOWLEDGE.values()) == before

    def test_wise_phrases_still_served(self):
        assert get_topic_resources("patience")["wise_phrases"]
