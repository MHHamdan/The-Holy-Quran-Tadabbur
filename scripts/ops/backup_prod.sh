#!/usr/bin/env bash
# =============================================================================
# backup_prod.sh — back up the production stack (docker-compose.prod.yml).
#
# Captures, through `docker compose exec` (no datastore publishes a port):
#   postgres.dump          pg_dump -Fc: Qur'an/tafsir data AND user data
#                          (feedback, therapy reflections, tasmee sessions)
#   qdrant/<c>.snapshot    one snapshot per collection (vectors cost HF credit)
#   surreal.surql          SurrealDB export, only when the `kg` profile runs
#   MANIFEST.json          UTC time, git SHA, alembic revision, SHA-256 per file
#
# Retention (run daily from cron):
#   daily/   the 7 newest backups
#   weekly/  one backup per ISO week, the 4 newest weeks
#   Anything older than 180 days is deleted, matching the therapy-data
#   retention promised in the privacy policy. Off-host copies are the
#   operator's choice (e.g. rclone/restic the BACKUP_DIR after this script);
#   they must apply the same 180-day limit.
#
# Usage:   scripts/ops/backup_prod.sh
# Cron:    15 3 * * *  cd /srv/tadabbur && scripts/ops/backup_prod.sh >>/var/log/tadabbur-backup.log 2>&1
# Env:     BACKUP_DIR (default /var/backups/tadabbur)
#          COMPOSE    (default "docker compose -f <repo>/docker-compose.prod.yml")
#          KEEP_DAILY (7)  KEEP_WEEKLY (4)  MAX_AGE_DAYS (180)
# Restore: scripts/ops/restore_prod.sh <backup dir>
# =============================================================================
set -euo pipefail
umask 077  # backups contain user data

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE="${COMPOSE:-docker compose -f $PROJECT_DIR/docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/tadabbur}"
KEEP_DAILY="${KEEP_DAILY:-7}"
KEEP_WEEKLY="${KEEP_WEEKLY:-4}"
MAX_AGE_DAYS="${MAX_AGE_DAYS:-180}"

say()  { printf '==> %s\n' "$*"; }
warn() { printf '  ! %s\n' "$*" >&2; }
die()  { printf '  x %s\n' "$*" >&2; exit 1; }

# shellcheck disable=SC2086
dc() { $COMPOSE "$@"; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK="$BACKUP_DIR/.incomplete-$STAMP"
DEST="$BACKUP_DIR/daily/$STAMP"
mkdir -p "$WORK/qdrant" "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly"
trap 'rm -rf "$WORK"' EXIT

dc ps --status running --services >/dev/null 2>&1 || die "compose stack not reachable ($COMPOSE)"
RUNNING="$(dc ps --status running --services)"
grep -qx postgres <<<"$RUNNING" || die "postgres is not running"

# --- 1. Postgres --------------------------------------------------------------
say "Postgres: pg_dump"
dc exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl' \
  > "$WORK/postgres.dump" || die "pg_dump failed"
ALEMBIC_REV="$(dc exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT version_num FROM alembic_version"' | tr -d '[:space:]' || true)"
say "  $(du -h "$WORK/postgres.dump" | cut -f1), alembic @ ${ALEMBIC_REV:-unknown}"

# --- 2. Qdrant (through the backend container; qdrant has no shell tools) -----
if grep -qx qdrant <<<"$RUNNING" && grep -qx backend <<<"$RUNNING"; then
  say "Qdrant: snapshots"
  COLLECTIONS="$(dc exec -T backend python -c '
import json, os, urllib.request
base = "http://%s:%s" % (os.environ.get("QDRANT_HOST", "qdrant"), os.environ.get("QDRANT_PORT", "6333"))
print(" ".join(c["name"] for c in json.load(urllib.request.urlopen(base + "/collections"))["result"]["collections"]))
')"
  for col in $COLLECTIONS; do
    # Create a snapshot, stream it to stdout, then delete it from the server
    # so repeated backups do not fill the qdrant volume.
    dc exec -T backend python -c '
import json, os, shutil, sys, urllib.request
col = sys.argv[1]
base = "http://%s:%s" % (os.environ.get("QDRANT_HOST", "qdrant"), os.environ.get("QDRANT_PORT", "6333"))
req = urllib.request.Request(f"{base}/collections/{col}/snapshots", method="POST")
name = json.load(urllib.request.urlopen(req, timeout=600))["result"]["name"]
try:
    with urllib.request.urlopen(f"{base}/collections/{col}/snapshots/{name}", timeout=600) as r:
        shutil.copyfileobj(r, sys.stdout.buffer)
finally:
    urllib.request.urlopen(urllib.request.Request(f"{base}/collections/{col}/snapshots/{name}", method="DELETE"))
' "$col" > "$WORK/qdrant/$col.snapshot" || die "snapshot failed for $col"
    say "  $col: $(du -h "$WORK/qdrant/$col.snapshot" | cut -f1)"
  done
else
  warn "qdrant or backend not running: no vector snapshot in this backup"
fi

# --- 3. SurrealDB (optional `kg` profile) -------------------------------------
if grep -qx surrealdb <<<"$RUNNING"; then
  say "SurrealDB: export"
  # Credentials stay in the backend container's environment (never in argv).
  dc exec -T backend python -c '
import base64, os, shutil, sys, urllib.request
url = "http://%s:%s/export" % (os.environ.get("SURREAL_HOST", "surrealdb"), os.environ.get("SURREAL_PORT", "8000"))
auth = base64.b64encode(("%s:%s" % (os.environ["SURREAL_USER"], os.environ["SURREAL_PASS"])).encode()).decode()
req = urllib.request.Request(url, headers={
    "Authorization": "Basic " + auth, "Accept": "application/json",
    "NS": os.environ.get("SURREAL_NAMESPACE", "tadabbur"), "DB": os.environ.get("SURREAL_DATABASE", "quran_kg")})
with urllib.request.urlopen(req, timeout=600) as r:
    shutil.copyfileobj(r, sys.stdout.buffer)
' > "$WORK/surreal.surql" || die "SurrealDB export failed"
  say "  $(du -h "$WORK/surreal.surql" | cut -f1)"
fi

# --- 4. Manifest --------------------------------------------------------------
GIT_SHA="$(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo unknown)"
python3 - "$WORK" "$STAMP" "$GIT_SHA" "${ALEMBIC_REV:-}" <<'PY'
import hashlib, json, os, sys
work, stamp, sha, rev = sys.argv[1:5]
members = {}
for root, _, files in os.walk(work):
    for name in files:
        full = os.path.join(root, name)
        h = hashlib.sha256()
        with open(full, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        members[os.path.relpath(full, work)] = {"sha256": h.hexdigest(), "bytes": os.path.getsize(full)}
with open(os.path.join(work, "MANIFEST.json"), "w") as fh:
    json.dump({"created_utc": stamp, "git_sha": sha, "alembic_revision": rev,
               "members": dict(sorted(members.items()))}, fh, indent=2)
    fh.write("\n")
PY

mv "$WORK" "$DEST"
trap - EXIT
say "Backup written: $DEST"

# --- 5. Rotation --------------------------------------------------------------
WEEK="$(date -u +%G-W%V)"
if [ ! -e "$BACKUP_DIR/weekly/$WEEK" ]; then
  cp -al "$DEST" "$BACKUP_DIR/weekly/$WEEK" 2>/dev/null || cp -a "$DEST" "$BACKUP_DIR/weekly/$WEEK"
  say "Weekly copy: weekly/$WEEK"
fi

prune_keep_newest() {  # dir keep
  local dir="$1" keep="$2"
  # Names sort chronologically (UTC stamps / ISO weeks).
  find "$dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -r | tail -n +"$((keep + 1))" |
    while read -r old; do rm -rf "${dir:?}/$old"; say "  pruned $(basename "$dir")/$old"; done
}
prune_keep_newest "$BACKUP_DIR/daily" "$KEEP_DAILY"
prune_keep_newest "$BACKUP_DIR/weekly" "$KEEP_WEEKLY"

# Hard limit: nothing older than MAX_AGE_DAYS survives (therapy retention).
find "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" -mindepth 1 -maxdepth 1 -type d -mtime +"$MAX_AGE_DAYS" \
  -exec rm -rf {} + -print | sed 's/^/  expired /'
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -name '.incomplete-*' -mmin +1440 -exec rm -rf {} +

say "Done"
