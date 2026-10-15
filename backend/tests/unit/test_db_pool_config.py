"""
DB pool sizing comes from the environment and the sync engine is lazy
(WS1: backend-db-pool-oversubscription). Each case imports the module in a
fresh interpreter so the module-level engine sees the environment.
"""
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]

PROBE = (
    "import app.db.database as d, sys;"
    "p = d.async_engine.pool;"
    "lazy = d.get_sync_engine.cache_info().currsize == 0;"
    "print(p.size(), p._max_overflow, p._timeout, lazy)"
)


def _probe(**env):
    full = {k: v for k, v in os.environ.items() if not k.startswith("DB_POOL") and k != "DB_MAX_OVERFLOW"}
    full.update(env)
    out = subprocess.run([sys.executable, "-c", PROBE], cwd=BACKEND, env=full,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    return out.stdout.strip().splitlines()[-1].split()


def test_defaults_fit_two_workers_under_max_connections():
    size, overflow, timeout, lazy = _probe()
    assert (int(size), int(overflow), float(timeout)) == (10, 10, 10.0)
    assert 2 * (int(size) + int(overflow)) <= 100 - 10
    assert lazy == "True"


def test_pool_is_env_driven():
    size, overflow, timeout, _ = _probe(DB_POOL_SIZE="7", DB_MAX_OVERFLOW="3", DB_POOL_TIMEOUT="5")
    assert (int(size), int(overflow), float(timeout)) == (7, 3, 5.0)


def test_sync_session_local_still_importable_lazily():
    code = ("import app.db.database as d;"
            "assert d.get_sync_engine.cache_info().currsize == 0;"
            "from app.db.database import SyncSessionLocal;"
            "assert d.get_sync_engine.cache_info().currsize == 1;"
            "print('ok')")
    out = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env=dict(os.environ),
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0 and out.stdout.strip().endswith("ok"), out.stderr[-2000:]
