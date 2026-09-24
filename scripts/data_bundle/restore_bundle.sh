#!/usr/bin/env bash
# =============================================================================
# restore_bundle.sh — restore a Tadabbur data bundle into empty datastores.
#
# Designed to run as a one-shot init job next to the app containers: it is safe
# to invoke on every boot, because by default it refuses to touch a Postgres
# that already holds data. Pass --force to overwrite.
#
# Usage: scripts/data_bundle/restore_bundle.sh BUNDLE.tar.zst [--force]
# =============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUNDLE="${1:-}"
FORCE="${2:-}"
[ -n "$BUNDLE" ] && [ -f "$BUNDLE" ] || { echo "usage: $0 BUNDLE.tar.zst [--force]" >&2; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# shellcheck disable=SC1091
[ -f "$PROJECT_DIR/.env" ] && { set -a; . "$PROJECT_DIR/.env"; set +a; }

PG_CONTAINER="${PG_CONTAINER:-tadabbur-postgres}"
PG_USER="${POSTGRES_USER:-tadabbur}"
PG_DB="${POSTGRES_DB:-tadabbur}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
SURREAL_URL="${SURREAL_URL:-http://localhost:8529}"
SURREAL_NS="${SURREAL_NAMESPACE:-tadabbur}"
SURREAL_DB="${SURREAL_DATABASE:-quran_kg}"
SURREAL_AUTH="${SURREAL_AUTH:-root:root}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; NC='\033[0m'
say()  { printf '%b==>%b %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%b  ! %b %s\n' "$YEL" "$NC" "$*"; }
die()  { printf '%b  x %b %s\n' "$RED" "$NC" "$*" >&2; exit 1; }

say "Unpacking $(basename "$BUNDLE")"
tar -C "$STAGE" -xf "$BUNDLE"
[ -f "$STAGE/BUNDLE.json" ] || die "BUNDLE.json missing — not a Tadabbur bundle"

say "Verifying checksums"
python3 "$PROJECT_DIR/scripts/data_bundle/verify_bundle.py" "$STAGE" || die "bundle failed verification"

# --- Postgres ----------------------------------------------------------------
EXISTING="$(podman exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
  "SELECT COALESCE(SUM(n_live_tup),0) FROM pg_stat_user_tables" 2>/dev/null | tr -d '[:space:]' || echo 0)"
if [ "${EXISTING:-0}" -gt 0 ] && [ "$FORCE" != "--force" ]; then
  warn "Postgres already holds ${EXISTING} rows — skipping restore (pass --force to overwrite)"
else
  say "Postgres: restoring"
  podman exec -i "$PG_CONTAINER" pg_restore -U "$PG_USER" -d "$PG_DB" --clean --if-exists --no-owner --no-acl \
    < "$STAGE/postgres.dump" 2>&1 | grep -vE "^pg_restore: (dropping|creating|processing|implied)" || true
  n="$(podman exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
    "SELECT COALESCE(SUM(n_live_tup),0) FROM pg_stat_user_tables" | tr -d '[:space:]')"
  say "  restored, ${n} rows"
fi

# --- Qdrant ------------------------------------------------------------------
if [ -d "$STAGE/qdrant" ]; then
  for snap in "$STAGE"/qdrant/*.snapshot; do
    [ -e "$snap" ] || continue
    col="$(basename "$snap" .snapshot)"
    say "Qdrant: restoring $col"
    curl -sf -X DELETE "$QDRANT_URL/collections/$col" >/dev/null 2>&1 || true
    curl -sf -X POST "$QDRANT_URL/collections/$col/snapshots/upload?priority=snapshot" \
      -H 'Content-Type: multipart/form-data' -F "snapshot=@${snap}" >/dev/null \
      || die "Qdrant restore failed for $col"
    pts="$(curl -sf "$QDRANT_URL/collections/$col" \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['points_count'])")"
    say "  $col: $pts points"
  done
fi

# --- SurrealDB ---------------------------------------------------------------
# The KG container runs an in-memory store, so this must re-run after every
# restart of tadabbur-surrealdb, not only on first deploy.
if [ -f "$STAGE/surreal.surql" ]; then
  say "SurrealDB: importing knowledge graph"
  curl -sf -u "$SURREAL_AUTH" -H "NS: $SURREAL_NS" -H "DB: $SURREAL_DB" -H "Accept: application/json" \
    -X POST "$SURREAL_URL/import" --data-binary "@$STAGE/surreal.surql" >/dev/null \
    || die "SurrealDB import failed"
  say "  imported"
fi

# --- Seeder inputs -----------------------------------------------------------
if [ -d "$STAGE/corpora" ]; then
  say "Corpora: installing into data/"
  mkdir -p "$PROJECT_DIR/data"
  for d in "$STAGE"/corpora/*; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    rm -rf "$PROJECT_DIR/data/$name"
    cp -r "$d" "$PROJECT_DIR/data/$name"
    say "  data/$name: $(du -sh "$PROJECT_DIR/data/$name" | cut -f1)"
  done
fi

say "Restore complete"
