"""Classification rules of scripts/index/prune_tafseer_index.py (pure, no I/O)."""
import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "index" / "prune_tafseer_index.py"
_spec = importlib.util.spec_from_file_location("prune_tafseer_index", _SCRIPT)
prune = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = prune  # dataclasses resolve their module
_spec.loader.exec_module(prune)

PLACEHOLDER = "لا يوجد تفسير لهذه الأية"
TEXT = "نص تفسير حقيقي طويل بما يكفي ليكون شرحا"


def _pt(pid, chunk_id, source_id, text=TEXT):
    return {"id": pid, "payload": {"chunk_id": chunk_id, "source_id": source_id, "content_ar": text}}


@pytest.fixture
def db():
    sources = {
        "tabari_ar": prune.SourceRow(1, 1),
        "muyassar_ar": prune.SourceRow(1, 0),
        "ibn_kathir_en": prune.SourceRow(0, 0),
    }
    chunks = {
        "t1": prune.ChunkRow(1, "tabari_ar", True, False),
        "t2": prune.ChunkRow(2, "tabari_ar", True, False),
        "t3": prune.ChunkRow(3, "tabari_ar", True, True),   # DB text itself a placeholder
        "m1": prune.ChunkRow(4, "muyassar_ar", True, False),
        "e1": prune.ChunkRow(5, "ibn_kathir_en", True, False),
    }
    return sources, chunks


def test_classification(db):
    sources, chunks = db
    plan = prune.classify([
        _pt(10, "t1", "tabari_ar"),
        _pt(11, "t1", "tabari_ar"),                 # duplicate
        _pt(12, "t2", "tabari_ar", PLACEHOLDER),    # stale placeholder vector, DB fixed
        _pt(13, "t3", "tabari_ar"),                 # DB placeholder
        _pt(14, "gone", "tabari_ar", PLACEHOLDER),  # orphan
        _pt(15, "m1", "tabari_ar"),                 # payload source mismatch
        _pt(16, "m1", "muyassar_ar"),               # unlicensed
        _pt(17, "e1", "ibn_kathir_en"),             # disabled
        _pt(18, "x", "mystery_src"),                # unknown
        {"id": 19, "payload": {"source_id": "tabari_ar"}},  # no chunk_id -> orphan
    ], sources, chunks)
    assert plan.reasons == {
        11: "duplicate", 12: "placeholder", 13: "placeholder", 14: "orphan", 15: "mismatch",
        16: "unlicensed", 17: "disabled", 18: "unknown", 19: "orphan",
    }
    assert plan.kept_chunks["tabari_ar"] == {"t1"}


def test_unlicensed_kept_unless_requested(db):
    sources, chunks = db
    plan = prune.classify([_pt(1, "m1", "muyassar_ar"), _pt(2, "e1", "ibn_kathir_en")], sources, chunks)
    assert plan.to_delete(include_unlicensed=False) == [2]
    assert sorted(plan.to_delete(include_unlicensed=True)) == [1, 2]
