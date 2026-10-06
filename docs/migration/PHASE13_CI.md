# Phase 13: Continuous integration

`.github/workflows/ci.yml` runs on every `push` and `pull_request` (plus manual dispatch). It has 4 jobs.

| Job | What it gates |
|---|---|
| **backend** | <ul><li>Install `.[dev]`; fail if torch, transformers, sentence-transformers, faster-whisper or ctranslate2 got installed</li><li>`ruff` for syntax errors and undefined names (E9/F63/F7/F82) over `app tests scripts alembic`</li><li>Strict `ruff` (E4/E7/E9/F) + `black --check` on the Hugging Face modules</li><li>`mypy app/ai`</li><li>Alembic: single head, `upgrade head`, `downgrade -1`, `upgrade head` on fresh Postgres 16</li><li>Seed the reference data that is committed (Qur'an text, stories, story atlas and graphs, concepts, themes, rhetoric)</li><li>`pytest -m "not live_hf"` with Postgres, Redis and Qdrant service containers</li></ul> |
| **frontend** | `npm ci`, `typecheck`, `lint` (max warnings 0), `build`; the built bundle must contain no loopback API URL and no HF token or endpoint |
| **images** | Builds the production backend and web images (BuildKit, GHA cache, no push); checks they run non-root and contain no ML runtime or weight files; `docker compose -f docker-compose.prod.yml config` |
| **security** | `gitleaks` over the full git history; `pip-audit` over the backend's resolved dependencies; `npm audit --omit=dev --audit-level=high` |

`.github/workflows/theme-audit.yml` was fixed:
- It installed `backend/requirements.txt`, which does not exist, so it could never pass. It now installs from `pyproject.toml`.
- It seeds the Qur'an before themes.
- Its permissions are now read-only.

## Secrets and untrusted PRs

- No workflow references a secret.
- `HF_TOKEN` / `HUGGINGFACE_TOKEN` are set to empty strings at workflow level. `tests/conftest.py` additionally clears the token for every non-`live_hf` test.
- **Trigger:** `pull_request` only, never `pull_request_target`. Fork PRs therefore run with a read-only `GITHUB_TOKEN` and no secrets.
- **Token scope:** `permissions: contents: read` on both workflows.
- **Live tests:** `live_hf` tests are not run in CI. Run them by hand with `pytest -m live_hf` and a real token.

## Tests that need external data

40 tests assert on data that is ingested from external sources and not committed:
- the tafsir corpora
- the Quranic Arabic Corpus vocabulary, fetched from `api.qurancdn.com`
- the verse vector index, built with HF embeddings

On a CI database seeded only from committed data they failed on empty tables. They were also 15 of the 15 "data-bundle" failures in the dev environment.

Each test now declares exactly what it needs, e.g. `@pytest.mark.requires_data("tafsir:2:255")` or `"tafsir_en:2:255"`, `"vocabulary"`, `"verse_vector:112:1"`. `tests/conftest.py` checks for those rows before the test runs:

- **Missing data:** the test skips, with the missing key as the reason.
- **Unreachable database:** the test runs and fails visibly; the check never hides an outage.
- **Full data bundle:** `REQUIRE_DATA_BUNDLE=1` turns missing data into a failure (verified: the 15 dev-environment cases fail again).

No assertion was changed or weakened.

## Results (local runs of the same commands)

| Check | Result |
|---|---|
| Backend tests, CI-like DB (fresh migrate + committed seeds, empty Qdrant) | **2551 passed, 0 failed**, 62 skipped (40 `requires_data`, others pre-existing), 11 deselected `live_hf` |
| Backend tests, dev DB (with ingested tafsir) | **2576 passed, 0 failed**, 37 skipped |
| `ruff` critical rules, whole tree | 0 |
| `ruff` + `black`, HF modules | 0 / 9 files unchanged |
| `mypy app/ai` | 0 issues (fixed a real bug: L2 normalisation upcast embeddings to float64) |
| Alembic | 1 head; upgrade → downgrade -1 → upgrade OK |
| Frontend from a clean `npm ci` | typecheck 0, lint 0, build OK, bundle clean |
| `actionlint` | 0 findings |
| gitleaks, 218 commits | 0 after reviewing 2 false positives (a localStorage key name and a deliberately wrong test key), allow-listed by fingerprint in `.gitleaksignore` and inline |
| pip-audit | no known vulnerabilities |
| npm audit (shipped deps) | 0 high/critical. `npm audit fix` raised axios 1.18 → 1.20 to fix a high-severity prototype-pollution issue. 2 moderate remain (react-router open redirect via backslash URLs); the only fix is a major upgrade to v7 |

## Known debt, not gated

- **Full ruff default rules:** 834 findings across the legacy tree, mostly unused imports (518) and f-strings without placeholders.
- **black:** 192 legacy files would be reformatted. Reformatting them in this branch would bury the migration diff.
- **Dev-only npm advisories:** 11 high, in the eslint/tailwind toolchain, which never ships to users.
- **react-router v7 upgrade** to clear the 2 moderate advisories.
