# Phase 11: Secret hygiene

## Git history

- **Scope:** all 214 commits on all refs of a full (non-shallow) clone.
- **Pattern scan** (`git log --all -p`) for:
  - Hugging Face tokens (`hf_…`)
  - Anthropic keys (`sk-ant-…`)
  - OpenAI-style `sk-…` keys
  - AWS access keys
  - GitHub tokens
  - private-key blocks
  - non-placeholder assignments to `ANTHROPIC_API_KEY`, `ADMIN_API_KEY`, `ADMIN_TOKEN`, `METRICS_SECRET`, `HF_TOKEN`
- **Tracked tree:** `detect-secrets` scan.

**Result: no real credential has ever been committed. No revocation is required (no P0).**

The only findings are development placeholders: `tadabbur_dev` database URLs, `test_admin_token_dev`, Alembic revision hashes and test fixtures. One public default, `tadabbur-admin-dev-token`, was more than a placeholder because the code actually accepted it (see below).

## Fixed

| Issue | Fix |
|---|---|
| `KG_ADMIN_TOKEN` fell back to the public string `tadabbur-admin-dev-token`, so KG admin endpoints (e.g. `POST /kg/import-stories`) were open on any deployment that did not set it | No default; the check fails closed (503 when not configured). The tests that asserted the default now assert the fail-closed behaviour. |
| `VITE_ADMIN_API_KEY` compiled the backend admin key into the public JS bundle | Removed. The admin enters the key at runtime; it is kept in `sessionStorage` for the tab and sent only as `X-Admin-API-Key`. The only remaining `VITE_*` variable is `VITE_API_URL`. |
| `.gitignore` covered `.env` but not `.env.*` | Now ignores `.env`, `.env.*` and their nested variants (except `*.env.example`), plus `*.pem`, `*.key`, `*.p12`, `*.jks`, `*.keystore`, `google-services.json`, `GoogleService-Info.plist` |
| `docker-compose.prod.yml` fell back to weak credentials (`tadabbur_prod`, `change_this_in_production`, SurrealDB `root/root`) | Production compose now **requires** `POSTGRES_PASSWORD`, `SURREAL_PASS`, `ADMIN_TOKEN`, `ADMIN_API_KEY`, `KG_ADMIN_TOKEN`, `CORS_ORIGINS` and `HF_TOKEN`, and refuses to start without them |
| `settings.debug` defaulted to on, which returns raw exception text | Defaults to off and is forced off in production (Phase 6) |
| `sanity_check.py` defaulted to a hard-coded admin token | Reads `ADMIN_TOKEN` from the environment |

## HF_TOKEN stays on the server

- Read only from the backend environment (`HF_TOKEN`, alias `HUGGINGFACE_TOKEN`) into a pydantic `SecretStr`; it never appears in `repr()`/`model_dump()`.
- Error messages from HF calls carry only the error kind and HTTP status, never the token or upstream body (unit-tested).
- Verified this session: the token value appears in **0** server logs, test outputs, tracked files, frontend sources and built bundles.
- `tests/unit/test_secret_hygiene.py` fails CI if:
  - any `VITE_*KEY|TOKEN|SECRET|PASSWORD` variable appears in the frontend
  - any HF credential or HF endpoint appears in the frontend
  - any env file other than a template is tracked
  - the template carries a token value
