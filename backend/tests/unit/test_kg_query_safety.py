"""The KG schema splitter must not drop statements that follow comment headers."""

import re

from app.kg.schema import get_schema_sql, iter_schema_statements


def test_every_define_in_the_schema_is_executed():
    sql = get_schema_sql()
    statements = list(iter_schema_statements(sql))
    expected = len(re.findall(r"^\s*DEFINE\s", sql, re.M))
    defines = [s for s in statements if s.startswith("DEFINE")]
    assert len(defines) == expected
    assert not any(line.strip().startswith("--") for s in statements for line in s.splitlines())


def test_analyzers_and_tables_used_by_search_indexes_are_defined():
    statements = list(iter_schema_statements(get_schema_sql()))
    analyzers = {
        m.group(1)
        for s in statements
        for m in [re.match(r"DEFINE ANALYZER (?:IF NOT EXISTS )?(\w+)", s)]
        if m
    }
    used = {m for s in statements for m in re.findall(r"SEARCH ANALYZER (\w+)", s)}
    assert used <= analyzers, f"indexes use undefined analyzers: {used - analyzers}"
    tables = {m.group(1) for s in statements for m in [re.match(r"DEFINE TABLE (\w+)", s)] if m}
    assert {"story_cluster", "story_event", "person", "place", "concept_tag", "ayah"} <= tables


async def test_create_edge_sets_fields_without_replacing_in_and_out():
    """RELATE ... CONTENT wipes `in`/`out` on typed relation tables; SET keeps them."""
    from unittest.mock import AsyncMock

    import pytest

    from app.kg.client import KGClient

    kg = KGClient.__new__(KGClient)
    kg.query = AsyncMock(return_value=[{"id": "has_event:1"}])
    await kg.create_edge(
        "has_event", "story_cluster:a", "story_event:b", {"order": 3, "weight": 0.5}
    )
    sql, params = kg.query.await_args.args
    assert sql == "RELATE story_cluster:a->has_event->story_event:b SET order = $p0, weight = $p1;"
    assert params == {"p0": 3, "p1": 0.5} and "CONTENT" not in sql

    await kg.create_edge("next", "story_event:a", "story_event:b")
    assert kg.query.await_args.args[0] == "RELATE story_event:a->next->story_event:b;"

    with pytest.raises(ValueError):
        await kg.create_edge("next", "story_event:a", "story_event:b", {"x; DELETE person": 1})


# --------------------------------------------------------------------------
# SurrealQL injection (public /graph/thematic/* and /kg/* routes used to
# interpolate query-string / path values into statements run with the KG's
# owner credentials).
# --------------------------------------------------------------------------
INJECTIONS = [
    "x'; CREATE injection_probe:1 SET a = 1; --",
    "story_cluster:musa; DELETE person",
    "story_cluster:musa WHERE true",
    "story_cluster:musa`",
    "musa) OR (true",
]


def test_record_id_validation_rejects_injection_and_accepts_real_ids():
    import pytest

    from app.kg.client import KGInvalidIdentifier, check_ident, check_record_id

    for good in (
        "story_cluster:musa",
        "story_event:yusuf_well",
        "ayah:18:83",
        "tafsir_chunk:a1b2c3",
        "x:⟨2:255⟩",
    ):
        assert check_record_id(good) == good
    for bad in INJECTIONS + ["", "story_cluster:", ":x", "story cluster:x"]:
        with pytest.raises(KGInvalidIdentifier):
            check_record_id(bad)
    for bad in ("has_event; DELETE person", "a b", ""):
        with pytest.raises(KGInvalidIdentifier):
            check_ident(bad)


async def test_thematic_theme_values_are_parameters_not_sql():
    from unittest.mock import AsyncMock, MagicMock

    from app.services.thematic_mapper import ThematicMapper

    mapper = ThematicMapper.__new__(ThematicMapper)
    mapper.kg = MagicMock()
    mapper.kg.query = AsyncMock(return_value=[])
    await mapper.find_theme_connections(theme_key=INJECTIONS[0])
    sql, params = mapper.kg.query.await_args.args
    assert INJECTIONS[0] not in sql and "$key" in sql and params == {"key": INJECTIONS[0]}


async def test_cross_story_ids_are_validated_before_use():
    from unittest.mock import AsyncMock, MagicMock

    import pytest

    from app.kg.client import KGInvalidIdentifier
    from app.services.thematic_mapper import ThematicMapper

    mapper = ThematicMapper.__new__(ThematicMapper)
    mapper.kg = MagicMock()
    mapper.kg.select = AsyncMock(return_value=[])
    with pytest.raises(KGInvalidIdentifier):
        await mapper.get_cross_story_themes(story_ids=["musa", INJECTIONS[1]])
    assert all(INJECTIONS[1] not in str(c) for c in mapper.kg.select.await_args_list)


async def test_kg_client_refuses_unsafe_ids_before_sending_anything():
    from unittest.mock import AsyncMock

    import pytest

    from app.kg.client import KGClient, KGInvalidIdentifier

    kg = KGClient.__new__(KGClient)
    kg.query = AsyncMock(return_value=[])
    for call in (
        lambda: kg.get(INJECTIONS[1]),
        lambda: kg.delete(INJECTIONS[1]),
        lambda: kg.update(INJECTIONS[2], {}),
        lambda: kg.upsert("story_event", "x; DELETE person", {}),
        lambda: kg.get_neighbors(INJECTIONS[3]),
        lambda: kg.traverse(INJECTIONS[4], "next"),
        lambda: kg.select("story_event; DELETE person"),
    ):
        with pytest.raises(KGInvalidIdentifier):
            await call()
    kg.query.assert_not_awaited()


def test_entity_endpoint_answers_400_for_unsafe_id():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        r = client.get("/api/v1/graph/entity/story_cluster:musa;DELETE person")
        assert r.status_code == 400, r.text
        assert r.json()["error"]["code"] == "invalid_identifier"


async def test_parameter_substitution_does_not_mix_up_prefixed_names():
    from unittest.mock import AsyncMock, MagicMock

    from app.kg.client import KGClient

    response = MagicMock()
    response.json.return_value = [{"status": "OK", "result": []}]
    http = MagicMock()
    http.post = AsyncMock(return_value=response)

    class _Client(KGClient):  # local subclass: never patch KGClient itself
        client = http

    kg = _Client.__new__(_Client)
    await kg.query("SELECT * FROM t WHERE a = $p1 AND b = $p10;", {"p1": "one", "p10": "ten"})
    sent = http.post.await_args.kwargs["content"]
    assert sent == "SELECT * FROM t WHERE a = s'one' AND b = s'ten';"
