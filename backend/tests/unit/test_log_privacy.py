"""
Logs carry no client IP and no search text (WS1: store-privacy-policy-vs-logs,
security-log-user-text). The privacy page promises both.
"""
import logging
import pathlib
import re
from types import SimpleNamespace

from fastapi.testclient import TestClient
from starlette.requests import Request

from app.main import _loggable_path, app

ROOT = pathlib.Path(__file__).resolve().parents[3]


def _req(path, route_path=None):
    scope = {"type": "http", "method": "GET", "path": path, "query_string": b"", "headers": []}
    if route_path:
        scope["route"] = SimpleNamespace(path=route_path)
    return Request(scope)


def test_search_paths_are_logged_as_route_templates():
    assert _loggable_path(_req("/api/v1/quran/search/analytics/صبر", "/api/v1/quran/search/analytics/{word}")) \
        == "/api/v1/quran/search/analytics/{word}"
    assert _loggable_path(_req("/api/v1/search/private-text")) == "/[search]"


def test_other_paths_are_logged_unchanged():
    assert _loggable_path(_req("/api/v1/quran/suras/2")) == "/api/v1/quran/suras/2"
    # "research" is not a search segment.
    assert _loggable_path(_req("/api/v1/research/x")) == "/api/v1/research/x"


def test_request_log_omits_search_text(caplog):
    with caplog.at_level(logging.INFO, logger="app.main"):
        TestClient(app).get("/api/v1/search/zz-private-term/nonexistent?q=zz-private-query")
    text = " ".join(r.getMessage() for r in caplog.records)
    assert "/[search]" in text
    assert "zz-private" not in text


def test_matched_search_route_logs_its_template(caplog):
    with caplog.at_level(logging.INFO, logger="app.main"):
        TestClient(app, raise_server_exceptions=False).get("/api/v1/quran/search/sura/987/frequency")
    text = " ".join(r.getMessage() for r in caplog.records)
    assert "/api/v1/quran/search/sura/{sura_no}/frequency" in text
    assert "/sura/987/" not in text


def test_no_ip_in_backend_log_format_strings():
    offenders = []
    for path in (ROOT / "backend" / "app" / "core").rglob("*.py"):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"logger\.\w+\(.*\bIP %s", line):
                offenders.append(f"{path.name}:{n}")
    assert not offenders, offenders


def test_nginx_access_log_has_no_query_string_or_client_address():
    conf = (ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    fmt = conf[conf.index("log_format main"):conf.index(";", conf.index("log_format main"))]
    assert "$uri" in fmt
    for banned in ("$request ", '$request"', "$args", "$query_string", "$remote_addr",
                   "$http_x_forwarded_for", "$request_uri"):
        assert banned not in fmt, banned
