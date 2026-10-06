#!/usr/bin/env bash
# =============================================================================
# scripts/start_all.sh – Start all Tadabbur-AI services (pure Podman, no compose)
#
# Fix notes:
#   PYTHONPATH  – LEXIFORGE is installed editably in the conda env via
#                 _lexiforge_backend.pth, so "import app" silently finds
#                 LEXIFORGE's app package first.  Every Python call here
#                 exports PYTHONPATH="$PROJECT_DIR/backend" so Tadabbur's
#                 app/ is resolved first.
#   stale ctrs  – Containers from old podman-compose runs may have embedded
#                 CPU-limit settings that prevent restart.  Stopped containers
#                 are removed before (re)creation.
#   CNI network – tadabbur_default was created with CNI spec 1.0.0 which the
#                 firewall plugin no longer supports.  We remove the network +
#                 conflist file on every run so Podman recreates them cleanly.
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_DIR="$PROJECT_DIR/.pids"
LOG_DIR="$PROJECT_DIR/logs"

# Primary LAN address, detected rather than hardcoded. This used to be pinned
# to 172.24.50.21; the host now answers on 172.24.50.31, so every readiness
# probe dialled an address that does not exist here and reported the API and
# frontend as "not ready" however healthy they were, while the banner printed
# URLs nobody could open. Export TADABBUR_HOST_IP to override.
detect_host_ip() {
    local ip
    ip="$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || true)"
    [[ -z "$ip" ]] && ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
    printf '%s' "${ip:-127.0.0.1}"
}

HOST_IP="${TADABBUR_HOST_IP:-$(detect_host_ip)}"

# Ports come from one file so the Makefile, this script and .env cannot drift.
# See the header of scripts/ports.env for why this block was chosen.
# shellcheck source=./ports.env
source "$SCRIPT_DIR/ports.env"

BACKEND_PORT="$TADABBUR_BACKEND_PORT"
FRONTEND_PORT="$TADABBUR_FRONTEND_PORT"
POSTGRES_PORT="$TADABBUR_POSTGRES_PORT"
QDRANT_HTTP_PORT="$TADABBUR_QDRANT_HTTP_PORT"
QDRANT_GRPC_PORT="$TADABBUR_QDRANT_GRPC_PORT"
REDIS_PORT="$TADABBUR_REDIS_PORT"
SURREAL_PORT="$TADABBUR_SURREAL_PORT"

# Datastore URLs every child process inherits, built from the ports above so a
# stale default in config.py or a service module can never point a Tadabbur
# process at another platform's database.
export DATABASE_URL="postgresql://tadabbur:tadabbur_dev@localhost:${POSTGRES_PORT}/tadabbur"
export QDRANT_HOST="localhost"
export QDRANT_PORT="$QDRANT_HTTP_PORT"
export QDRANT_URL="http://localhost:${QDRANT_HTTP_PORT}"
export REDIS_URL="redis://localhost:${REDIS_PORT}/0"
export SURREAL_HOST="localhost"
export SURREAL_PORT="$SURREAL_PORT"
export SURREAL_URL="http://localhost:${SURREAL_PORT}"

# All Python sub-processes must see Tadabbur's app/ before the conda .pth injects
# LEXIFORGE/backend onto sys.path.
export PYTHONPATH="$PROJECT_DIR/backend"

# ── AI models ────────────────────────────────────────────────────────────────
# All model inference (chat, embeddings, reranking, STT, classification) runs on
# Hugging Face Inference Providers. Nothing here needs a GPU or local model
# files; the backend only needs HF_TOKEN in its environment (backend/.env).
if [[ -z "${HF_TOKEN:-}${HUGGINGFACE_TOKEN:-}" ]] && ! grep -qs '^HF_TOKEN=.\+' "$PROJECT_DIR/backend/.env" "$PROJECT_DIR/.env"; then
    _HF_MSG="HF_TOKEN not set — AI answers will be unavailable (sources still shown)"
else
    _HF_MSG="HF_TOKEN configured (value not shown)"
fi

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

mkdir -p "$PID_DIR" "$LOG_DIR"

# ── Helpers ───────────────────────────────────────────────────────────────────

die() { printf '\n%b✗ FATAL:%b %s\n\n' "$RED" "$NC" "$*" >&2; exit 1; }

write_pid() { printf '%s\n' "$2" > "$PID_DIR/$1.pid"; }

# PID of the process LISTENING on a port.
#
# -sTCP:LISTEN is essential: a bare `lsof -ti :PORT` also matches processes that
# merely hold a client connection to it, which would record (and later kill) an
# unrelated service. Only the listener counts.
port_pid() { lsof -ti :"$1" -sTCP:LISTEN 2>/dev/null | head -1 || true; }

# Wait until host:port accepts TCP, or timeout.
# Optional 5th arg: a PID to watch — exits early if the process dies.
wait_for_port() {
    local host="$1" port="$2" label="$3" timeout="${4:-30}" watch_pid="${5:-}"
    local i=0
    printf '  Waiting for %s...' "$label"
    while ! nc -z "$host" "$port" 2>/dev/null; do
        i=$((i + 1))
        # If the watched process has already died, no point waiting further
        if [[ -n "$watch_pid" ]] && ! kill -0 "$watch_pid" 2>/dev/null; then
            printf '\n  %b✗%b %s — process (PID %s) died\n' "$RED" "$NC" "$label" "$watch_pid"
            return 1
        fi
        if [[ $i -ge $timeout ]]; then
            printf '\n  %b✗%b %s not ready after %ss\n' "$RED" "$NC" "$label" "$timeout"
            return 1
        fi
        sleep 1
    done
    printf ' %bready%b\n' "$GREEN" "$NC"
}

# True when the running container already publishes every host port that this
# invocation's -p arguments ask for.
container_ports_match() {
    local name="$1"; shift
    local published arg want

    published="$(podman inspect \
        --format '{{range $p, $c := .NetworkSettings.Ports}}{{range $c}}{{.HostPort}} {{end}}{{end}}' \
        "$name" 2>/dev/null || true)"

    while [[ $# -gt 0 ]]; do
        if [[ "$1" == "-p" ]]; then
            # Accepts "host:ctr" and "0.0.0.0:host:ctr".
            arg="${2//\"/}"
            want="$(printf '%s' "$arg" | awk -F: '{print $(NF-1)}')"
            if [[ -n "$want" ]] && ! grep -qw "$want" <<<"$published"; then
                return 1
            fi
            shift 2
            continue
        fi
        shift
    done
    return 0
}

# Start a named Podman container.
#   • Already running  → record PID, skip.
#   • Exists but stopped (possibly with stale resource limits) → rm + recreate.
#   • Does not exist   → create fresh.
#
# A running container is only reused when it already publishes the host ports
# this run expects. Without that check, editing scripts/ports.env would appear
# to work while every datastore stayed on its old, possibly contended port,
# because "already running" skipped the remap.
start_container() {
    local name="$1"; shift
    local short="${name#tadabbur-}"

    local status
    status=$(podman inspect --format '{{.State.Status}}' "$name" 2>/dev/null || echo "absent")

    if [[ "$status" == "running" ]] && ! container_ports_match "$name" "$@"; then
        echo -e "  ${YELLOW}~${NC} $name is on stale ports — recreating to match ports.env"
        podman rm -f "$name" >/dev/null 2>&1 || true
        status="absent"
    fi

    case "$status" in
        running)
            echo -e "  ${YELLOW}~${NC} $name already running on the expected ports"
            ;;
        absent)
            if ! podman run -d --name "$name" "$@" >> "$LOG_DIR/podman.log" 2>&1; then
                echo -e "  ${RED}✗${NC} $name failed to create — last log lines:"
                tail -10 "$LOG_DIR/podman.log" >&2; return 1
            fi
            echo -e "  ${GREEN}✓${NC} $name started"
            ;;
        *)
            # exited / created / configured — may have stale resource limits; remove first
            echo -e "  ${YELLOW}~${NC} removing stale $name (was: $status)"
            podman rm -f "$name" >/dev/null 2>&1 || true
            if ! podman run -d --name "$name" "$@" >> "$LOG_DIR/podman.log" 2>&1; then
                echo -e "  ${RED}✗${NC} $name failed to recreate — last log lines:"
                tail -10 "$LOG_DIR/podman.log" >&2; return 1
            fi
            echo -e "  ${GREEN}✓${NC} $name recreated"
            ;;
    esac

    # Write PID file: real container init PID when available, sentinel otherwise
    local ctr_pid
    ctr_pid=$(podman inspect --format '{{.State.Pid}}' "$name" 2>/dev/null || echo "")
    if [[ -n "$ctr_pid" && "$ctr_pid" != "0" ]]; then
        write_pid "container-$short" "$ctr_pid"
    else
        printf 'container:%s\n' "$name" > "$PID_DIR/container-$short.pid"
    fi
}

print_banner() {
    echo ""
    printf '%b╔══════════════════════════════════════════════════════════╗%b\n' "$GREEN" "$NC"
    printf '%b║  Tadabbur-AI is running                                  ║%b\n' "$GREEN" "$NC"
    printf '%b╠══════════════════════════════════════════════════════════╣%b\n' "$GREEN" "$NC"
    printf '%b║%b  Frontend    %bhttp://%s:%s%b                      %b║%b\n' \
        "$GREEN" "$NC" "$BLUE" "$HOST_IP" "$FRONTEND_PORT" "$NC" "$GREEN" "$NC"
    printf '%b║%b  API         %bhttp://%s:%s%b                      %b║%b\n' \
        "$GREEN" "$NC" "$BLUE" "$HOST_IP" "$BACKEND_PORT"  "$NC" "$GREEN" "$NC"
    printf '%b║%b  API Docs    %bhttp://%s:%s/docs%b                 %b║%b\n' \
        "$GREEN" "$NC" "$BLUE" "$HOST_IP" "$BACKEND_PORT"  "$NC" "$GREEN" "$NC"
    printf '%b║%b  Qdrant      %bhttp://localhost:%s%b                       %b║%b\n' \
        "$GREEN" "$NC" "$BLUE" "$QDRANT_HTTP_PORT" "$NC" "$GREEN" "$NC"
    printf '%b╚══════════════════════════════════════════════════════════╝%b\n' "$GREEN" "$NC"
    echo ""
}

# ── Preamble ──────────────────────────────────────────────────────────────────
echo ""
printf '%b╔══════════════════════════════════════════════════════════╗%b\n' "$BLUE" "$NC"
printf '%b║       Starting Tadabbur-AI Services                      ║%b\n' "$BLUE" "$NC"
printf '%b╚══════════════════════════════════════════════════════════╝%b\n' "$BLUE" "$NC"
echo ""

command -v podman >/dev/null 2>&1 || die "podman not found — install podman first"
printf '  %b⚙%b  %s\n' "$BLUE" "$NC" "$_HF_MSG"
echo ""
podman info >/dev/null 2>&1 || die "Podman is not running.
  Start with: systemctl --user start podman.socket
  Or enable:  systemctl --user enable --now podman.socket"

# ── 0. Port preflight ─────────────────────────────────────────────────────────
# Several unrelated platforms share this machine. Before touching anything,
# check that nothing other than Tadabbur itself holds a port we are about to
# bind, and say exactly who does. Previously a taken port surfaced as an opaque
# "rootlessport bind: address already in use" from deep inside Podman, or worse,
# as a readiness timeout after the run had already half-reconfigured things.
preflight_ports() {
    local conflicts=0 entry port label pid owner

    for entry in \
        "$FRONTEND_PORT:frontend" \
        "$BACKEND_PORT:backend API" \
        "$POSTGRES_PORT:postgres" \
        "$QDRANT_HTTP_PORT:qdrant HTTP" \
        "$QDRANT_GRPC_PORT:qdrant gRPC" \
        "$REDIS_PORT:redis" \
        "$SURREAL_PORT:surrealdb"
    do
        port="${entry%%:*}"; label="${entry#*:}"
        pid="$(port_pid "$port")"
        [[ -z "$pid" ]] && continue

        owner="$(ps -p "$pid" -o comm= 2>/dev/null || echo unknown)"

        # Ours already, or Podman's published-port shim for our own container.
        if is_own_process "$pid" "$owner"; then
            continue
        fi

        printf '  %b✗%b %s port %s is held by %s (PID %s) — not a Tadabbur process\n' \
            "$RED" "$NC" "$label" "$port" "$owner" "$pid"
        conflicts=$((conflicts + 1))
    done

    if [[ $conflicts -gt 0 ]]; then
        die "$conflicts port(s) are owned by another platform.
  Tadabbur's ports are defined in scripts/ports.env — change the value there,
  or export e.g. TADABBUR_BACKEND_PORT=19801 before running make start.
  Nothing was started, so no other platform was disturbed."
    fi

    printf '  %b✓%b  all 7 Tadabbur ports clear (%s)\n' "$GREEN" "$NC" \
        "frontend ${FRONTEND_PORT}, api ${BACKEND_PORT}, pg ${POSTGRES_PORT}, qdrant ${QDRANT_HTTP_PORT}/${QDRANT_GRPC_PORT}, redis ${REDIS_PORT}, surreal ${SURREAL_PORT}"
}

# True when the PID on one of our ports is Tadabbur's own.
#
# The listener is often a child of what we recorded — `npm run dev` is the PID
# in frontend.pid, but the socket belongs to the node process it spawns — so
# the parent chain is walked, not just the PID itself. Podman's published-port
# shims front our own containers and count as ours too.
is_own_process() {
    local pid="$1" owner="$2" pidfile recorded cursor depth

    if [[ "$owner" == "rootlessport" || "$owner" == "pasta" || "$owner" == "slirp4netns" ]]; then
        return 0
    fi

    for pidfile in "$PID_DIR"/*.pid; do
        [[ -f "$pidfile" ]] || continue
        recorded="$(head -1 "$pidfile" 2>/dev/null || true)"
        [[ "$recorded" =~ ^[0-9]+$ ]] || continue

        cursor="$pid"
        depth=0
        while [[ "$cursor" =~ ^[0-9]+$ ]] && [[ "$cursor" -gt 1 ]] && [[ $depth -lt 8 ]]; do
            [[ "$cursor" == "$recorded" ]] && return 0
            cursor="$(ps -o ppid= -p "$cursor" 2>/dev/null | tr -d ' ')"
            depth=$((depth + 1))
        done
    done
    return 1
}

echo -e "${GREEN}[0/5] Port preflight${NC}"
preflight_ports
echo ""

# ── 1. Volumes ────────────────────────────────────────────────────────────────
echo -e "${GREEN}[1/5] Volumes${NC}"
for vol in tadabbur_postgres_data tadabbur_qdrant_data \
           tadabbur_redis_data tadabbur_surrealdb_data; do
    if podman volume exists "$vol" 2>/dev/null; then
        echo -e "  ${YELLOW}~${NC} $vol (exists)"
    else
        podman volume create "$vol" >/dev/null \
            && echo -e "  ${GREEN}✓${NC} $vol (created)" \
            || echo -e "  ${RED}✗${NC} $vol (create failed)"
    fi
done

# ── 2. Infrastructure containers ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}[2/5] Infrastructure containers${NC}"

# Remove stale CNI network (version 1.0.0 — firewall plugin incompatibility)
# and its conflist file so Podman recreates them with the current plugin version.
podman network rm tadabbur_default >/dev/null 2>&1 \
    && echo -e "  ${YELLOW}~${NC} removed stale CNI network tadabbur_default" || true
rm -f "${HOME}/.config/cni/net.d/tadabbur_default.conflist"

# ── Postgres ──
start_container tadabbur-postgres \
    -e POSTGRES_USER=tadabbur \
    -e POSTGRES_PASSWORD=tadabbur_dev \
    -e POSTGRES_DB=tadabbur \
    -e POSTGRES_INITDB_ARGS="--encoding=UTF8" \
    -p "0.0.0.0:${POSTGRES_PORT}:5432" \
    -v tadabbur_postgres_data:/var/lib/postgresql/data \
    docker.io/library/postgres:15-alpine \
    postgres \
      -c shared_buffers=256MB \
      -c effective_cache_size=768MB \
      -c work_mem=16MB \
      -c maintenance_work_mem=64MB \
      -c random_page_cost=1.1 \
      -c effective_io_concurrency=200 \
      -c max_connections=100

# ── Qdrant ──
# Publish explicitly to 0.0.0.0 so the port is reachable on all interfaces,
# not just loopback (Podman's rootless default is 127.0.0.1-only).
start_container tadabbur-qdrant \
    -p "0.0.0.0:${QDRANT_HTTP_PORT}:6333" \
    -p "0.0.0.0:${QDRANT_GRPC_PORT}:6334" \
    -v tadabbur_qdrant_data:/qdrant/storage \
    docker.io/qdrant/qdrant:v1.7.4

# ── Redis ──
start_container tadabbur-redis \
    -p "0.0.0.0:${REDIS_PORT}:6379" \
    -v tadabbur_redis_data:/data \
    docker.io/library/redis:7-alpine \
    redis-server \
      --maxmemory 256mb \
      --maxmemory-policy allkeys-lru \
      --appendonly yes \
      --appendfsync everysec \
      --tcp-keepalive 300

# ── SurrealDB ──
start_container tadabbur-surrealdb \
    --user root \
    -p "0.0.0.0:${SURREAL_PORT}:8000" \
    docker.io/surrealdb/surrealdb:v1.5.0 \
    start --log trace --user root --pass root memory

# Wait for Postgres (internal — localhost ok)
printf '  Waiting for Postgres...'
postgres_ready=0
for i in $(seq 1 30); do
    if podman exec tadabbur-postgres pg_isready -U tadabbur -q 2>/dev/null; then
        printf ' %bready%b\n' "$GREEN" "$NC"
        postgres_ready=1; break
    fi
    sleep 1
done
[[ $postgres_ready -eq 0 ]] && \
    printf '\n  %bWARN: Postgres not ready after 30s — check: podman logs tadabbur-postgres%b\n' \
        "$YELLOW" "$NC"

# ── 3. DB migrations ──────────────────────────────────────────────────────────
# PYTHONPATH already exported at top; using python -m alembic also ensures
# the current directory (backend/) is on sys.path before site-packages.
echo ""
echo -e "${GREEN}[3/5] DB migrations${NC}"
cd "$PROJECT_DIR/backend"
if python -m alembic upgrade head 2>&1 | tee -a "$LOG_DIR/migrations.log"; then
    echo -e "  ${GREEN}✓${NC} Migrations applied"
else
    echo -e "  ${YELLOW}~${NC} Migration step returned non-zero (see logs/migrations.log)"
fi

# ── 3b. Auto-seed (only when quran_verses is empty) ──────────────────────────
# Runs after migrations so the schema exists. Skipped on subsequent starts.
_verse_count=$(podman exec tadabbur-postgres \
    psql -U tadabbur tadabbur -t -c "SELECT COUNT(*) FROM quran_verses;" \
    2>/dev/null | tr -d '[:space:]' || echo "0")

if [[ "$_verse_count" == "0" ]]; then
    echo ""
    printf '  %b~%b  quran_verses is empty — running initial seed...\n' "$YELLOW" "$NC"
    cd "$PROJECT_DIR"

    # 1. Verses
    python backend/scripts/ingest/seed_quran.py >> "$LOG_DIR/migrations.log" 2>&1 \
        && printf '  %b✓%b  Quran verses seeded\n' "$GREEN" "$NC" \
        || printf '  %b✗%b  seed_quran.py failed — check logs/migrations.log\n' "$RED" "$NC"

    # 2. Normalize text for search
    python -c "
import os, re, sys; sys.path.insert(0,'backend')
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
def norm(t):
    t=t.replace('﻿','').replace('ـ','')
    t=re.sub(r'[ً-ٰٟ]','',t)
    t=re.sub(r'[آأإٱ]','ا',t)
    return t.replace('ة','ه').replace('ى','ي').strip()
e=create_engine(os.environ['DATABASE_URL'])
s=Session(e)
rows=s.execute(text('SELECT id,text_uthmani FROM quran_verses')).all()
s.execute(text('UPDATE quran_verses SET text_normalized=:n WHERE id=:i'),[{'i':r,'n':norm(t or '')} for r,t in rows])
s.commit()
print(f'Normalized {len(rows)} verses')
" >> "$LOG_DIR/migrations.log" 2>&1 \
        && printf '  %b✓%b  text_normalized populated\n' "$GREEN" "$NC" \
        || printf '  %b✗%b  normalize step failed — check logs/migrations.log\n' "$RED" "$NC"

    # 3. Vocabulary (77,430 words from qurancdn.com)
    printf '  %b~%b  Seeding vocabulary (~77k words, ~30s)...\n' "$YELLOW" "$NC"
    python backend/scripts/seed_vocabulary_complete.py >> "$LOG_DIR/migrations.log" 2>&1 \
        && printf '  %b✓%b  Vocabulary seeded\n' "$GREEN" "$NC" \
        || printf '  %b✗%b  seed_vocabulary_complete.py failed — check logs/migrations.log\n' "$RED" "$NC"

    # 4. Mushaf word layout (604-page line assignments for King Fahd rendering)
    printf '  %b~%b  Seeding Mushaf word layout (~77k words across 604 pages, ~90s)...\n' "$YELLOW" "$NC"
    python backend/scripts/ingest/seed_mushaf_words.py >> "$LOG_DIR/migrations.log" 2>&1 \
        && printf '  %b✓%b  Mushaf word layout seeded\n' "$GREEN" "$NC" \
        || printf '  %b✗%b  seed_mushaf_words.py failed — check logs/migrations.log\n' "$RED" "$NC"
fi

# ── 4. Application services ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}[4/5] Application services${NC}"

# Backend (uvicorn) — PYTHONPATH already exported.
#
# A process holding the port is not the same as a working API: a half-dead or
# wedged uvicorn keeps the socket bound, and simply recording its PID used to
# make the run "succeed" here and then fail the readiness check 60s later. The
# port holder is asked for /health first, and only a real answer counts as up.
start_backend() {
    cd "$PROJECT_DIR/backend"
    uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" \
        >> "$LOG_DIR/backend.log" 2>&1 &
    local pid=$!
    write_pid "backend" "$pid"
    echo -e "  ${GREEN}✓${NC} backend started (PID $pid)"
}

existing=$(port_pid "$BACKEND_PORT")
if [[ -z "$existing" ]]; then
    start_backend
elif curl -fsS -m 5 "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    echo -e "  ${YELLOW}~${NC} backend already healthy on :${BACKEND_PORT} (PID ${existing}) — updating PID file"
    write_pid "backend" "$existing"
else
    echo -e "  ${YELLOW}~${NC} backend on :${BACKEND_PORT} (PID ${existing}) is not answering /health — replacing it"
    kill "$existing" 2>/dev/null || true
    sleep 2
    kill -9 "$existing" 2>/dev/null || true
    sleep 1
    start_backend
fi

# Frontend (Vite dev server) — always kill stale process and start fresh
# so that every 'make start' delivers the latest code, not a cached version.
existing=$(port_pid "$FRONTEND_PORT")
if [[ -n "$existing" ]]; then
    echo -e "  ${YELLOW}~${NC} killing stale frontend on :${FRONTEND_PORT} (PID ${existing})"
    kill "$existing" 2>/dev/null || true
    sleep 1
    kill -9 "$existing" 2>/dev/null || true
fi
# Wipe Vite's module-transform cache so the browser gets genuinely new assets.
rm -rf "$PROJECT_DIR/frontend/node_modules/.vite"
cd "$PROJECT_DIR/frontend"
npm run dev >> "$LOG_DIR/frontend.log" 2>&1 &
_pid=$!
write_pid "frontend" "$_pid"
echo -e "  ${GREEN}✓${NC} frontend started fresh (PID $_pid)"

# RQ worker.
#
# Matched on our own Redis URL, not on "rq.cli worker" alone: that pattern also
# matches another platform's worker on this host, and it let a worker still
# attached to the old shared Redis on 6379 survive a port change and keep
# consuming from a queue that is no longer ours.
_rq_url="redis://localhost:${REDIS_PORT}/0"
existing=$(pgrep -f "rq.cli worker --url ${_rq_url}" 2>/dev/null | head -1 || true)
_rq_stale=$(pgrep -f "rq.cli worker" 2>/dev/null \
    | grep -v "^${existing:-0}$" | head -1 || true)

if [[ -n "$_rq_stale" ]] \
   && tr '\0' ' ' < "/proc/$_rq_stale/cmdline" 2>/dev/null | grep -q "$PROJECT_DIR\|rq.cli worker" \
   && ! tr '\0' ' ' < "/proc/$_rq_stale/cmdline" 2>/dev/null | grep -q "$_rq_url"; then
    echo -e "  ${YELLOW}~${NC} rq-worker (PID ${_rq_stale}) is on a stale Redis — replacing it"
    kill "$_rq_stale" 2>/dev/null || true
    sleep 1
    kill -9 "$_rq_stale" 2>/dev/null || true
    existing=""
fi

if [[ -n "$existing" ]]; then
    echo -e "  ${YELLOW}~${NC} rq-worker already on ${_rq_url} (PID ${existing})"
    write_pid "rq-worker" "$existing"
else
    # `python` on PATH here is miniconda's, which has no rq; the package lives
    # in the project venv. Pick the first interpreter that can actually import
    # it rather than spawning a worker that exits on ModuleNotFoundError.
    _rq_python=""
    for _candidate in "$PROJECT_DIR/.venv/bin/python" "$(command -v python || true)"; do
        [[ -x "$_candidate" ]] || continue
        if "$_candidate" -c "import rq" >/dev/null 2>&1; then
            _rq_python="$_candidate"; break
        fi
    done

    if [[ -z "$_rq_python" ]]; then
        echo -e "  ${YELLOW}~${NC} rq not installed in any interpreter — background jobs unavailable"
    else
        cd "$PROJECT_DIR/backend"
        "$_rq_python" -m rq.cli worker --url "$_rq_url" high default low \
            >> "$LOG_DIR/rq-worker.log" 2>&1 &
        _pid=$!
        write_pid "rq-worker" "$_pid"
        echo -e "  ${GREEN}✓${NC} rq-worker started on ${_rq_url} (PID $_pid)"
    fi
fi

# ── 5. Readiness checks ───────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}[5/5] Readiness checks${NC}"

backend_pid=$(cat "$PID_DIR/backend.pid" 2>/dev/null || echo "")
wait_for_port "$HOST_IP" "$BACKEND_PORT" "API (${HOST_IP}:${BACKEND_PORT})" 60 "$backend_pid" \
    || { echo -e "  ${YELLOW}  Hint — last 15 lines of logs/backend.log:${NC}";
         tail -15 "$LOG_DIR/backend.log" 2>/dev/null | sed 's/^/    /' || true; }

wait_for_port "$HOST_IP" "$FRONTEND_PORT" "Frontend (${HOST_IP}:${FRONTEND_PORT})" 45

wait_for_port "localhost" "$QDRANT_HTTP_PORT" "Qdrant (localhost:${QDRANT_HTTP_PORT})" 20

print_banner
