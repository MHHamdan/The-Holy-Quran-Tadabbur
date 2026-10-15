"""
Hadith shown in the frontend must carry structured provenance.

quranicDuas.ts held 26 free-text 'Prophetic Notes' with no hadith numbers; six
were not hadith at all (tafsir or later scholars' sayings), five had suspect
attributions, and grades appeared without the scholar who gave them. The data
now uses SupportingNote {kind, collection, number, narrator, grade, grader},
and the UI shows a note only via isDisplayableNote (hadith + collection +
number). These checks read the TypeScript sources directly.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DUAS = ROOT / "frontend" / "src" / "data" / "quranicDuas.ts"
DUAS_PAGE = ROOT / "frontend" / "src" / "pages" / "DuasPage.tsx"
PROPHETIC = ROOT / "frontend" / "src" / "components" / "therapy" / "PropheticDuasPanel.tsx"

REMOVED = {
    "dua_zakariyya_child", "dua_musa_guidance", "dua_furqan_family",
    "dua_imran_sovereignty", "dua_sorcerers_faith", "dua_musa_need",
    "dua_nur_knowledge", "dua_ibrahim_kaabah", "dua_hasbiyallah",
    "dua_sulayman_unique", "dua_isra_entry_exit",
}


def _notes():
    """(dua_id, {field: value}) for every supportingNote block."""
    text = DUAS.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"id: '(dua_[a-z0-9_]+)'(.*?)(?=\n  \{\n    id: '|\Z)", text, re.S):
        block = re.search(r"supportingNote: \{(.*?)\n    \},", m.group(2), re.S)
        if block:
            # Single-quoted or template literals (Qur'anic words inside a
            # hadith text are rendered with ${quranExcerpt(...)}).
            pairs = re.findall(r"(\w+): (?:'((?:[^'\\]|\\.)*)'|`((?:[^`\\]|\\.)*)`)", block.group(1))
            fields = {k: a or b for k, a, b in pairs}
            out.append((m.group(1), fields))
    return out


def test_free_text_hadith_field_is_gone():
    assert "hadithAr" not in DUAS.read_text(encoding="utf-8")


def test_unsourced_and_suspect_notes_removed():
    ids = {i for i, _ in _notes()}
    assert not (ids & REMOVED)
    assert len(ids) == 15


def test_every_note_is_structured():
    for dua_id, f in _notes():
        assert f.get("kind") in {"hadith", "athar", "tafsir"}, dua_id
        assert f.get("textAr"), dua_id
        assert f.get("collection"), dua_id
        if f.get("grade"):
            assert f.get("grader"), f"{dua_id}: grade without a named grader"


def test_ui_gates_on_collection_and_number():
    src = DUAS.read_text(encoding="utf-8")
    assert "note.kind === 'hadith' && !!note.collection && !!note.number" in src
    page = DUAS_PAGE.read_text(encoding="utf-8")
    assert "isDisplayableNote(dua.supportingNote)" in page
    assert "dua.supportingNote.grade && dua.supportingNote.grader" in page
    panel = PROPHETIC.read_text(encoding="utf-8")
    assert "isDisplayableNote(d.hadith)" in panel


def test_no_note_shown_without_a_number():
    """No hadith number has been verified yet, so nothing is displayable."""
    for dua_id, f in _notes():
        assert not f.get("number"), (
            f"{dua_id}: a number was added; make sure a reviewer verified it, "
            "then update this test"
        )
