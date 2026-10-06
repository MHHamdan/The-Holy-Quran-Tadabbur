"""
Secret hygiene guards (Phase 11).

- The Hugging Face token and other privileged secrets must never reach the
  frontend/mobile bundle: no VITE_* variable may carry a key/token/secret, and
  frontend source must not reference HF credentials or call HF directly.
- No env file other than the templates may be tracked by git.
- Known historical default credentials must not reappear.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
FRONTEND = REPO / "frontend"

_SECRET_VITE = re.compile(r"VITE_[A-Z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)
_HF_IN_FRONTEND = re.compile(
    r"HF_TOKEN|HUGGINGFACE_TOKEN|router\.huggingface\.co|api-inference\.huggingface\.co"
)


def _frontend_files():
    roots = [FRONTEND / "src", FRONTEND / "index.html", FRONTEND / "vite.config.ts"]
    for root in roots:
        if root.is_file():
            yield root
        elif root.is_dir():
            yield from (
                p
                for p in root.rglob("*")
                if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".html", ".json"}
            )
    for extra in ("capacitor.config.ts", "capacitor.config.json"):
        if (FRONTEND / extra).exists():
            yield FRONTEND / extra


def test_no_secret_bearing_vite_variables_or_hf_access_in_frontend():
    offenders = []
    for path in _frontend_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in (_SECRET_VITE, _HF_IN_FRONTEND):
            for m in pattern.finditer(text):
                offenders.append(f"{path.relative_to(REPO)}: {m.group(0)}")
    assert not offenders, offenders


_PERSISTED_SECRET = re.compile(
    r"localStorage\.(?:setItem|getItem)\(\s*[A-Za-z_'\"]*(?:TOKEN|ADMIN|SECRET|API_KEY)",
    re.IGNORECASE,
)


def test_admin_credentials_are_not_persisted_in_local_storage():
    """Admin tokens typed into the UI live in sessionStorage (this tab only)."""
    offenders = []
    for path in _frontend_files():
        for m in _PERSISTED_SECRET.finditer(path.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(f"{path.relative_to(REPO)}: {m.group(0)}")
    assert not offenders, offenders


def test_env_example_has_no_secret_vite_variable_or_value():
    text = (REPO / ".env.example").read_text(encoding="utf-8")
    assert not _SECRET_VITE.search(text)
    hf_line = next(line for line in text.splitlines() if line.startswith("HF_TOKEN="))
    assert hf_line.strip() == "HF_TOKEN=", "the template must not carry a token value"


def _git_ls_files():
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git not available")
    return out.stdout.splitlines()


def test_only_env_templates_are_tracked():
    tracked_env = [f for f in _git_ls_files() if re.search(r"(^|/)\.env(\.|$)", f)]
    assert all(f.endswith(".env.example") for f in tracked_env), tracked_env


def test_public_default_admin_token_is_gone():
    hits = []
    for f in _git_ls_files():
        if not f.endswith((".py", ".ts", ".tsx", ".yml", ".yaml", ".toml", ".sh", ".env.example")):
            continue
        if "/tests/" in f:  # regression tests assert the old token is rejected
            continue
        path = REPO / f
        if path.is_file() and "tadabbur-admin-dev-token" in path.read_text(
            encoding="utf-8", errors="ignore"
        ):
            hits.append(f)
    # Only the explanatory comment in kg.py may mention it.
    assert hits in ([], ["backend/app/api/routes/kg.py"]), hits
