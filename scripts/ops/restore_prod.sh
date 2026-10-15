#!/usr/bin/env bash
# =============================================================================
# restore_prod.sh — restore a backup made by backup_prod.sh into the
# production stack (docker-compose.prod.yml).
#
#   scripts/ops/restore_prod.sh /var/backups/tadabbur/daily/20261014T031500Z --yes
#
# Restores Postgres (pg_restore --clean), every Qdrant snapshot present and,
# when the backup has one and the `kg` profile is running, the SurrealDB
# export. Checksums in MANIFEST.json are verified first. Without --yes it only
# verifies and prints what it would do: a restore REPLACES current data.
#
# Typical disaster recovery:
#   docker compose -f docker-compose.prod.yml up -d postgres qdrant redis
#   docker compose -f docker-compose.prod.yml run --rm migrate   # empty schema
#   docker compose -f docker-compose.prod.yml up -d backend
#   scripts/ops/restore_prod.sh <backup dir> --yes
#   docker compose -f docker-compose.prod.yml up -d
# =============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE="${COMPOSE:-docker compose -f $PROJECT_DIR/docker-compose.prod.yml}"
SRC="${1:-}"
CONFIRM="${2:-}"

say()  { printf '==> %s\n' "$*"; }
warn() { printf '  ! %s\n' "$*" >&2; }
die()  { printf '  x %s\n' "$*" >&2; exit 1; }
# shellcheck disable=SC2086
dc() { $COMPOSE "$@"; }

[ -n "$SRC" ] && [ -f "$SRC/MANIFEST.json" ] || die "usage: $0 <backup dir containing MANIFEST.json> [--yes]"

say "Verifying checksums"
python3 - "$SRC" <<'PY'
import hashlib, json, os, sys
src = sys.argv[1]
manifest = json.load(open(os.path.join(src, "MANIFEST.json")))
bad = []
for rel, meta in manifest["members"].items():
    h = hashlib.sha256()
    with open(os.path.join(src, rel), "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    if h.hexdigest() != meta["sha256"]:
        bad.append(rel)
if bad:
    sys.exit("checksum mismatch: " + ", ".join(bad))
print(f"  {len(manifest['members'])} files ok, created {manifest['created_utc']}, alembic {manifest.get('alembic_revision') or '?'}")
PY

if [ "$CONFIRM" != "--yes" ]; then
  say "Dry run: pass --yes to replace the current Postgres/Qdrant/SurrealDB data with this backup"
  exit 0
fi

RUNNING="$(dc ps --status running --services)"
grep -qx postgres <<<"$RUNNING" || die "postgres is not running"

# --- Postgres ----------------------------------------------------------------
say "Postgres: pg_restore --clean"
dc exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-acl' \
  < "$SRC/postgres.dump" 2>&1 | grep -vE '^pg_restore: (dropping|creating|processing|implied)' || true
ROWS="$(dc exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COALESCE(SUM(n_live_tup),0) FROM pg_stat_user_tables"' | tr -d '[:space:]')"
say "  restored (~${ROWS} live rows)"

# --- Qdrant ------------------------------------------------------------------
if compgen -G "$SRC/qdrant/*.snapshot" >/dev/null; then
  grep -qx backend <<<"$RUNNING" || die "backend must be running to restore Qdrant (it reaches qdrant:6333)"
  for snap in "$SRC"/qdrant/*.snapshot; do
    col="$(basename "$snap" .snapshot)"
    say "Qdrant: restoring $col"
    dc exec -T backend python -c '
import json, os, sys, urllib.request, uuid
col = sys.argv[1]
base = "http://%s:%s" % (os.environ.get("QDRANT_HOST", "qdrant"), os.environ.get("QDRANT_PORT", "6333"))
data = sys.stdin.buffer.read()
boundary = uuid.uuid4().hex
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"snapshot\"; filename=\"{col}.snapshot\"\r\n"
        "Content-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(f"{base}/collections/{col}/snapshots/upload?priority=snapshot", data=body,
                             method="POST", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
urllib.request.urlopen(req, timeout=1800).read()
info = json.load(urllib.request.urlopen(f"{base}/collections/{col}"))
print("  %s: %s points" % (col, info["result"]["points_count"]))
' "$col" < "$snap" || die "Qdrant restore failed for $col"
  done
fi

# --- SurrealDB ---------------------------------------------------------------
if [ -s "$SRC/surreal.surql" ]; then
  if grep -qx surrealdb <<<"$RUNNING"; then
    say "SurrealDB: import"
    dc exec -T backend python -c '
import base64, os, sys, urllib.request
url = "http://%s:%s/import" % (os.environ.get("SURREAL_HOST", "surrealdb"), os.environ.get("SURREAL_PORT", "8000"))
auth = base64.b64encode(("%s:%s" % (os.environ["SURREAL_USER"], os.environ["SURREAL_PASS"])).encode()).decode()
req = urllib.request.Request(url, data=sys.stdin.buffer.read(), method="POST", headers={
    "Authorization": "Basic " + auth, "Accept": "application/json",
    "NS": os.environ.get("SURREAL_NAMESPACE", "tadabbur"), "DB": os.environ.get("SURREAL_DATABASE", "quran_kg")})
urllib.request.urlopen(req, timeout=1800).read()
' < "$SRC/surreal.surql" || die "SurrealDB import failed"
  else
    warn "backup has a SurrealDB export but the kg profile is not running: skipped"
  fi
fi

say "Restore complete. Check: curl -s localhost:\${WEB_PORT:-8080}/api/v1/tafseer/compare/2/255 | head -c 300"
