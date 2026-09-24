#!/usr/bin/env bash
# =============================================================================
# export_bundle.sh — build a self-contained Tadabbur data bundle.
#
# Captures every datastore the app needs to boot with real content, so a
# deployment can restore state without reaching this machine or any third-party
# API. Output is a single tarball plus a checksum manifest.
#
# Members:
#   postgres.dump    pg_dump -Fc of the seeded database
#   qdrant/*.snapshot  one Qdrant snapshot per collection
#   surreal.surql    SurrealDB export (its store is in-memory, so the export is
#                    the ONLY durable copy of the knowledge graph)
#   corpora/         data/raw, data/manifests, data/concepts — the seeder inputs
#                    that .gitignore keeps out of the repo
#   BUNDLE.json      versions, row counts, point counts and SHA-256 per member
#
# Usage: scripts/data_bundle/export_bundle.sh [OUTPUT_DIR]
# =============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${1:-$PROJECT_DIR/dist/bundle}"
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

BUNDLE_VERSION="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_SHA="$(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo unknown)"
mkdir -p "$STAGE/qdrant" "$STAGE/corpora"

# --- 1. Postgres -------------------------------------------------------------
say "Postgres: dumping $PG_DB"
podman exec "$PG_CONTAINER" pg_dump -U "$PG_USER" -d "$PG_DB" -Fc --no-owner --no-acl \
  > "$STAGE/postgres.dump" || die "pg_dump failed"
PG_ROWS="$(podman exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
  "SELECT COALESCE(SUM(n_live_tup),0) FROM pg_stat_user_tables" | tr -d '[:space:]')"
ALEMBIC_REV="$(podman exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
  "SELECT version_num FROM alembic_version" | tr -d '[:space:]')"
say "  $(du -h "$STAGE/postgres.dump" | cut -f1), ${PG_ROWS} rows, alembic @ ${ALEMBIC_REV}"

# --- 2. Qdrant ---------------------------------------------------------------
say "Qdrant: snapshotting collections"
COLLECTIONS="$(curl -sf "$QDRANT_URL/collections" \
  | python3 -c "import sys,json;print(' '.join(c['name'] for c in json.load(sys.stdin)['result']['collections']))")"
[ -n "$COLLECTIONS" ] || warn "no Qdrant collections found"
QDRANT_POINTS=0
for col in $COLLECTIONS; do
  pts="$(curl -sf "$QDRANT_URL/collections/$col" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['points_count'])")"
  snap="$(curl -sf -X POST "$QDRANT_URL/collections/$col/snapshots" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['name'])")" \
    || die "snapshot failed for $col"
  curl -sf "$QDRANT_URL/collections/$col/snapshots/$snap" -o "$STAGE/qdrant/${col}.snapshot" \
    || die "snapshot download failed for $col"
  # Qdrant keeps snapshots on the server until deleted; drop it so repeated
  # exports do not grow the container's storage volume without bound.
  curl -sf -X DELETE "$QDRANT_URL/collections/$col/snapshots/$snap" >/dev/null || true
  QDRANT_POINTS=$((QDRANT_POINTS + pts))
  say "  $col: $pts points, $(du -h "$STAGE/qdrant/${col}.snapshot" | cut -f1)"
done

# --- 3. SurrealDB ------------------------------------------------------------
# The container runs `start ... memory`, so this export is the only durable
# copy of the KG. Losing it means re-running init_surreal + import_stories.
say "SurrealDB: exporting $SURREAL_NS/$SURREAL_DB"
curl -sf -u "$SURREAL_AUTH" -H "NS: $SURREAL_NS" -H "DB: $SURREAL_DB" -H "Accept: application/json" \
  "$SURREAL_URL/export" -o "$STAGE/surreal.surql" || die "SurrealDB export failed"
SURREAL_RECORDS="$(grep -c '^INSERT\|^UPDATE\|^CREATE' "$STAGE/surreal.surql" 2>/dev/null || echo 0)"
say "  $(du -h "$STAGE/surreal.surql" | cut -f1), ${SURREAL_RECORDS} statements"

# --- 4. Seeder inputs --------------------------------------------------------
# .gitignore excludes data/, so these never reach a fresh clone. Without them
# the mandated integrity validator cannot run and nothing can be re-seeded.
say "Corpora: copying seeder inputs"
for d in raw manifests concepts; do
  [ -d "$PROJECT_DIR/data/$d" ] || { warn "data/$d missing, skipping"; continue; }
  cp -r "$PROJECT_DIR/data/$d" "$STAGE/corpora/$d"
  say "  data/$d: $(du -sh "$STAGE/corpora/$d" | cut -f1)"
done

# --- 5. Manifest -------------------------------------------------------------
say "Writing BUNDLE.json"
python3 - "$STAGE" "$BUNDLE_VERSION" "$GIT_SHA" "$PG_ROWS" "$ALEMBIC_REV" "$QDRANT_POINTS" "$SURREAL_RECORDS" <<'PY'
import hashlib, json, os, sys
stage, version, git_sha, pg_rows, alembic_rev, qpoints, srecords = sys.argv[1:8]

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

members = {}
for root, _, files in os.walk(stage):
    for name in files:
        full = os.path.join(root, name)
        rel = os.path.relpath(full, stage)
        if rel == 'BUNDLE.json':
            continue
        members[rel] = {'sha256': sha256(full), 'bytes': os.path.getsize(full)}

manifest = {
    'bundle_version': version,
    'git_sha': git_sha,
    'alembic_revision': alembic_rev,
    'counts': {
        'postgres_rows': int(pg_rows or 0),
        'qdrant_points': int(qpoints or 0),
        'surreal_statements': int(srecords or 0),
    },
    'members': dict(sorted(members.items())),
    'total_bytes': sum(m['bytes'] for m in members.values()),
}
with open(os.path.join(stage, 'BUNDLE.json'), 'w') as fh:
    json.dump(manifest, fh, indent=2)
    fh.write('\n')
print(f"  {len(members)} members, {manifest['total_bytes'] / 1e6:.1f} MB uncompressed")
PY

# --- 6. Pack -----------------------------------------------------------------
mkdir -p "$OUT_DIR"
TARBALL="$OUT_DIR/tadabbur-data-${BUNDLE_VERSION}.tar.zst"
say "Packing $TARBALL"
if command -v zstd >/dev/null 2>&1; then
  tar -C "$STAGE" -cf - . | zstd -T0 -19 -q -o "$TARBALL"
else
  TARBALL="${TARBALL%.zst}.gz"
  warn "zstd not found, falling back to gzip"
  tar -C "$STAGE" -czf "$TARBALL" .
fi

cp "$STAGE/BUNDLE.json" "$OUT_DIR/BUNDLE.json"
TAR_SHA="$(sha256sum "$TARBALL" | cut -d' ' -f1)"
python3 - "$OUT_DIR/BUNDLE.json" "$(basename "$TARBALL")" "$TAR_SHA" "$(stat -c %s "$TARBALL")" <<'PY'
import json, sys
path, name, sha, size = sys.argv[1:5]
with open(path) as fh:
    m = json.load(fh)
m['tarball'] = {'name': name, 'sha256': sha, 'bytes': int(size)}
with open(path, 'w') as fh:
    json.dump(m, fh, indent=2); fh.write('\n')
PY

say "Done"
printf '  tarball : %s (%s)\n' "$TARBALL" "$(du -h "$TARBALL" | cut -f1)"
printf '  sha256  : %s\n' "$TAR_SHA"
printf '  manifest: %s\n' "$OUT_DIR/BUNDLE.json"
