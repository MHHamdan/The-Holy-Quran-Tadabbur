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

HOST_IP="172.24.50.21"
BACKEND_PORT=8002
FRONTEND_PORT=3000

# All Python sub-processes must see Tadabbur's app/ before the conda .pth injects
# LEXIFORGE/backend onto sys.path.
export PYTHONPATH="$PROJECT_DIR/backend"

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

mkdir -p "$PID_DIR" "$LOG_DIR"

# ── Helpers ───────────────────────────────────────────────────────────────────

die() { printf '\n%b✗ FATAL:%b %s\n\n' "$RED" "$NC" "$*" >&2; exit 1; }

write_pid() { printf '%s\n' "$2" > "$PID_DIR/$1.pid"; }

port_pid() { lsof -ti :"$1" 2>/dev/null | head -1 || true; }

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

# Start a named Podman container.
#   • Already running  → record PID, skip.
#   • Exists but stopped (possibly with stale resource limits) → rm + recreate.
#   • Does not exist   → create fresh.
start_container() {
    local name="$1"; shift
    local short="${name#tadabbur-}"

    local status
    status=$(podman inspect --format '{{.State.Status}}' "$name" 2>/dev/null || echo "absent")

    case "$status" in
        running)
            echo -e "  ${YELLOW}~${NC} $name already running — updating PID file"
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
    printf '%b║%b  Qdrant      %bhttp://%s:6333%b                         %b║%b\n' \
        "$GREEN" "$NC" "$BLUE" "$HOST_IP" "$NC" "$GREEN" "$NC"
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
podman info >/dev/null 2>&1 || die "Podman is not running.
  Start with: systemctl --user start podman.socket
  Or enable:  systemctl --user enable --now podman.socket"

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
    -p 5432:5432 \
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
start_container tadabbur-qdrant \
    -p 6333:6333 \
    -p 6334:6334 \
    -v tadabbur_qdrant_data:/qdrant/storage \
    docker.io/qdrant/qdrant:v1.7.4

# ── Redis ──
start_container tadabbur-redis \
    -p 6379:6379 \
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
    -p 8529:8000 \
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

# ── 4. Application services ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}[4/5] Application services${NC}"

# Ollama LLM server — required for the Ask/RAG feature
existing=$(port_pid 11434)
if [[ -n "$existing" ]]; then
    echo -e "  ${YELLOW}~${NC} ollama already on :11434 (PID ${existing}) — updating PID file"
    write_pid "ollama" "$existing"
elif ! command -v ollama >/dev/null 2>&1; then
    echo -e "  ${YELLOW}~${NC} ollama not installed — Ask page will be unavailable"
else
    ollama serve >> "$LOG_DIR/ollama.log" 2>&1 &
    _pid=$!
    write_pid "ollama" "$_pid"
    echo -e "  ${GREEN}✓${NC} ollama started (PID $_pid)"
    # Brief pause so ollama socket is ready before backend connects
    sleep 2
fi

# Backend (uvicorn) — PYTHONPATH already exported
existing=$(port_pid "$BACKEND_PORT")
if [[ -n "$existing" ]]; then
    echo -e "  ${YELLOW}~${NC} backend already on :${BACKEND_PORT} (PID ${existing}) — updating PID file"
    write_pid "backend" "$existing"
else
    cd "$PROJECT_DIR/backend"
    uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" \
        >> "$LOG_DIR/backend.log" 2>&1 &
    _pid=$!
    write_pid "backend" "$_pid"
    echo -e "  ${GREEN}✓${NC} backend started (PID $_pid)"
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

# RQ worker — PYTHONPATH already exported; Redis is process-to-process (localhost ok)
existing=$(pgrep -f "rq.cli worker" 2>/dev/null | head -1 || true)
if [[ -n "$existing" ]]; then
    echo -e "  ${YELLOW}~${NC} rq-worker already running (PID ${existing}) — updating PID file"
    write_pid "rq-worker" "$existing"
else
    cd "$PROJECT_DIR/backend"
    python -m rq.cli worker --url redis://localhost:6379/0 high default low \
        >> "$LOG_DIR/rq-worker.log" 2>&1 &
    _pid=$!
    write_pid "rq-worker" "$_pid"
    echo -e "  ${GREEN}✓${NC} rq-worker started (PID $_pid)"
fi

# ── 5. Readiness checks ───────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}[5/5] Readiness checks${NC}"

backend_pid=$(cat "$PID_DIR/backend.pid" 2>/dev/null || echo "")
wait_for_port "$HOST_IP" "$BACKEND_PORT" "API (${HOST_IP}:${BACKEND_PORT})" 60 "$backend_pid" \
    || { echo -e "  ${YELLOW}  Hint — last 15 lines of logs/backend.log:${NC}";
         tail -15 "$LOG_DIR/backend.log" 2>/dev/null | sed 's/^/    /' || true; }

wait_for_port "$HOST_IP" "$FRONTEND_PORT" "Frontend (${HOST_IP}:${FRONTEND_PORT})" 45

wait_for_port "$HOST_IP" "6333" "Qdrant (${HOST_IP}:6333)" 20

print_banner
