"""Tasmee API: WebSocket input handling, session access control, abuse limits,
retention/erasure and the live accuracy figure.

Uses the shared dev database (quran_verses must be seeded). Every session a
test creates is deleted again through POST /tasmee/sessions/delete. Speech to
text is always a local stub: no test here calls Hugging Face.
"""

import json
from pathlib import Path
from typing import List

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.routes import tasmee as tasmee_routes
from app.stt.providers.base import STTResult, TranscriptionSegment, WordInfo

BASE = "/api/v1/tasmee"
WINDOW_BYTES = int(tasmee_routes.WS_WINDOW_SECONDS * tasmee_routes.SAMPLE_RATE) * 2


class StubSTT:
    """Returns pre-set word lists, one per transcribe() call."""

    def __init__(self, scripted: List[List[str]] | None = None):
        self.scripted = list(scripted or [])
        self.calls = 0

    def load_model(self):
        return None

    def unload_model(self):
        return None

    def transcribe(self, audio, word_timestamps=True, **_):
        self.calls += 1
        words = self.scripted.pop(0) if self.scripted else []
        if not words:
            return STTResult(segments=[], full_text="", duration=3.0)
        infos = [WordInfo(word=w, start_time=i * 0.4, end_time=(i + 1) * 0.4, confidence=0.9)
                 for i, w in enumerate(words)]
        seg = TranscriptionSegment(text=" ".join(words), start_time=0.0,
                                   end_time=infos[-1].end_time, words=infos)
        return STTResult(segments=[seg], full_text=seg.text, duration=3.0)


@pytest.fixture
def client():
    from app.main import app

    tasmee_routes._tasmee_limiter.reset()
    with TestClient(app) as c:
        yield c
    tasmee_routes._tasmee_limiter.reset()


@pytest.fixture
def stub(monkeypatch):
    holder = {"stt": StubSTT()}
    monkeypatch.setattr(tasmee_routes, "get_stt_provider", lambda *a, **k: holder["stt"])
    return holder


@pytest.fixture
def created(client):
    """Track sessions created by a test and delete them afterwards."""
    sessions: list = []
    yield sessions
    if sessions:
        client.post(f"{BASE}/sessions/delete",
                    json={"sessions": [{"id": s["id"], "token": s["client_token"]} for s in sessions]})


def _create(client, created, sura=112, start=1, end=4):
    r = client.post(f"{BASE}/sessions", json={"sura_no": sura, "aya_start": start, "aya_end": end})
    if r.status_code == 404:
        pytest.skip("quran_verses not seeded")
    assert r.status_code == 200, r.text
    body = r.json()
    created.append(body)
    return body


def _auth(ws, body):
    ws.send_text(json.dumps({"type": "auth", "token": body["client_token"]}))
    init = ws.receive_json()
    assert init["type"] == "init"
    return init


# ---------------------------------------------------------------------------
# P0: the WebSocket must never evaluate client text
# ---------------------------------------------------------------------------


def test_ws_eval_payload_is_not_executed(client, stub, created, tmp_path):
    body = _create(client, created)
    marker = tmp_path / "pwned"
    payloads = [
        f"__import__('pathlib').Path({str(marker)!r}).touch()",
        json.dumps(f"__import__('pathlib').Path({str(marker)!r}).touch()"),
        "[1, 2, 3]",
        "{not json",
        json.dumps({"type": "__import__('os').system('true')"}),
    ]
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        _auth(ws, body)
        for p in payloads:
            ws.send_text(p)
        # The socket is still usable after the hostile frames.
        ws.send_text(json.dumps({"type": "reveal_request", "count": 1}))
        msg = ws.receive_json()
        assert msg["type"] == "reveal_words"
        assert msg["revealed_up_to"] == 1
    assert not marker.exists()


def test_no_eval_in_backend_app():
    root = Path(tasmee_routes.__file__).resolve().parents[2]
    offenders = [
        str(p) for p in root.rglob("*.py")
        if "eval(" in p.read_text(encoding="utf-8").replace("literal_eval(", "")
        .replace(".eval(", "").replace("_eval(", "")
    ]
    assert offenders == []


def test_ws_config_update_validates_values(client, stub, created):
    body = _create(client, created)
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        _auth(ws, body)
        ws.send_text(json.dumps({"type": "config_update", "reveal_mode": "evil",
                                 "tap_reveal_count": 99, "hybrid_threshold": 7}))
        msg = ws.receive_json()
        assert msg == {"type": "config_updated", "reveal_mode": "auto",
                       "tap_reveal_count": 1, "hybrid_threshold": 0.7}
        ws.send_text(json.dumps({"type": "config_update", "reveal_mode": "smart_tap",
                                 "tap_reveal_count": 3, "hybrid_threshold": 0.5}))
        msg = ws.receive_json()
        assert msg["reveal_mode"] == "smart_tap"
        assert msg["tap_reveal_count"] == 3
        assert msg["hybrid_threshold"] == 0.5


def test_ws_reveal_count_is_clamped(client, stub, created):
    body = _create(client, created, sura=2, start=1, end=5)
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        init = _auth(ws, body)
        assert init["total_words"] > 10
        ws.send_text(json.dumps({"type": "reveal_request", "count": 100000}))
        msg = ws.receive_json()
        assert len(msg["words"]) == 10


def test_ws_requires_auth_frame(client, stub, created):
    body = _create(client, created)
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        ws.send_text(json.dumps({"type": "reveal_request"}))
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == tasmee_routes.WS_CLOSE_UNAUTHORIZED


def test_ws_wrong_token_is_not_found(client, stub, created):
    body = _create(client, created)
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        ws.send_text(json.dumps({"type": "auth", "token": "x" * 32}))
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == tasmee_routes.WS_CLOSE_NOT_FOUND


# ---------------------------------------------------------------------------
# Session access control
# ---------------------------------------------------------------------------


def test_session_routes_require_token(client, created):
    body = _create(client, created)
    sid = body["id"]
    assert len(sid) == 36 and not sid.isdigit()
    assert body["client_token"]

    assert client.get(f"{BASE}/sessions/{sid}").status_code == 401
    assert client.get(f"{BASE}/sessions/{sid}", headers={"X-Tasmee-Token": "wrong-token"}).status_code == 404
    ok = client.get(f"{BASE}/sessions/{sid}", headers={"X-Tasmee-Token": body["client_token"]})
    assert ok.status_code == 200
    assert ok.json()["id"] == sid
    assert ok.json()["client_token"] is None  # never echoed again

    assert client.get(f"{BASE}/sessions/{sid}/mistakes").status_code == 401
    assert client.post(f"{BASE}/sessions/{sid}/complete").status_code == 401
    # The old integer ids and the unfiltered listing are gone.
    assert client.get(f"{BASE}/sessions/1", headers={"X-Tasmee-Token": "t" * 32}).status_code == 404
    assert client.get(f"{BASE}/sessions").status_code in (404, 405)
    assert client.get(f"{BASE}/progress").status_code == 404


def test_session_create_is_rate_limited(client, created):
    for _ in range(10):
        _create(client, created)
    r = client.post(f"{BASE}/sessions", json={"sura_no": 112, "aya_start": 1, "aya_end": 4})
    assert r.status_code == 429


def test_transcribe_rejects_oversize_upload(client, stub, created):
    body = _create(client, created)
    big = b"\x00" * (6 * 1024 * 1024)
    r = client.post(
        f"{BASE}/transcribe",
        params={"session_id": body["id"]},
        headers={"X-Tasmee-Token": body["client_token"]},
        files={"audio": ("a.raw", big, "application/octet-stream")},
    )
    assert r.status_code == 413
    assert stub["stt"].calls == 0


def test_ws_rejects_completed_session(client, stub, created):
    body = _create(client, created)
    h = {"X-Tasmee-Token": body["client_token"]}
    assert client.post(f"{BASE}/sessions/{body['id']}/complete", headers=h).status_code == 200
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        ws.send_text(json.dumps({"type": "auth", "token": body["client_token"]}))
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == tasmee_routes.WS_CLOSE_NOT_ACTIVE


def test_ws_session_audio_cap(client, stub, created, monkeypatch):
    monkeypatch.setattr(tasmee_routes, "MAX_SESSION_AUDIO_BYTES", WINDOW_BYTES)
    body = _create(client, created)
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        _auth(ws, body)
        ws.send_bytes(b"\x00" * (WINDOW_BYTES + 2))
        msg = ws.receive_json()
        assert msg["type"] == "session_limit"
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == tasmee_routes.WS_CLOSE_SESSION_LIMIT


# ---------------------------------------------------------------------------
# Live accuracy: words_correct is maintained by the WebSocket loop
# ---------------------------------------------------------------------------


def test_ws_exact_recitation_gives_full_accuracy(client, stub, created):
    body = _create(client, created)
    words = [w["word"] for w in body["highlighted_words"]]
    # Each 3 s window recognises the next 3 words.
    stub["stt"] = StubSTT([words[i:i + 3] for i in range(0, len(words), 3)])
    windows = len(stub["stt"].scripted)
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        _auth(ws, body)
        last = None
        for _ in range(windows):
            ws.send_bytes(b"\x00\x01" * (WINDOW_BYTES // 2))
            while True:
                msg = ws.receive_json()
                assert msg["type"] != "mistake_alert", msg
                if msg["type"] == "pointer_update":
                    last = msg
                    break
        assert last["is_complete"] is True

    h = {"X-Tasmee-Token": body["client_token"]}
    done = client.post(f"{BASE}/sessions/{body['id']}/complete", headers=h).json()
    assert done["accuracy_score"] == 1.0
    assert done["words_correct"] == len(words)
    mistakes = client.get(f"{BASE}/sessions/{body['id']}/mistakes", headers=h).json()
    assert mistakes["count"] == 0


def test_ws_slips_are_persisted(client, stub, created):
    body = _create(client, created)
    words = [w["word"] for w in body["highlighted_words"]]
    # Skip the second word: one deletion.
    stub["stt"] = StubSTT([[words[0]] + words[2:]])
    with client.websocket_connect(f"{BASE}/ws/{body['id']}") as ws:
        _auth(ws, body)
        ws.send_bytes(b"\x00\x01" * (WINDOW_BYTES // 2))
        seen = []
        while not any(m["type"] == "mistake_alert" for m in seen):
            seen.append(ws.receive_json())
    h = {"X-Tasmee-Token": body["client_token"]}
    mistakes = client.get(f"{BASE}/sessions/{body['id']}/mistakes", headers=h).json()
    assert mistakes["count"] == 1
    assert mistakes["mistakes"][0]["mistake_type"] == "deletion"
    assert mistakes["mistakes"][0]["word_position"] == 1
    done = client.post(f"{BASE}/sessions/{body['id']}/complete", headers=h).json()
    assert done["words_correct"] == len(words) - 1


# ---------------------------------------------------------------------------
# Retention and erasure
# ---------------------------------------------------------------------------


def _set_created_at_days_ago(public_id: str, days: int) -> None:
    import psycopg2
    from app.core.config import settings

    url = settings.database_url.replace("+asyncpg", "")
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE tasmee_sessions SET created_at = now() - (%s || ' days')::interval "
            "WHERE public_id = %s",
            (str(days), public_id),
        )


def test_delete_endpoint_requires_token(client, created):
    body = _create(client, created)
    r = client.post(f"{BASE}/sessions/delete",
                    json={"sessions": [{"id": body["id"], "token": "wrong-token-123"}]})
    assert r.json() == {"deleted": 0}
    r = client.post(f"{BASE}/sessions/delete",
                    json={"sessions": [{"id": body["id"], "token": body["client_token"]}]})
    assert r.json() == {"deleted": 1}
    h = {"X-Tasmee-Token": body["client_token"]}
    assert client.get(f"{BASE}/sessions/{body['id']}", headers=h).status_code == 404


def test_expired_sessions_are_purged_on_create(client, created):
    old = _create(client, created)
    _set_created_at_days_ago(old["id"], tasmee_routes.TASMEE_RETENTION_DAYS + 1)
    _create(client, created)
    h = {"X-Tasmee-Token": old["client_token"]}
    assert client.get(f"{BASE}/sessions/{old['id']}", headers=h).status_code == 404
