#!/usr/bin/env bash
# =============================================================================
# scripts/stop_all.sh – Stop all Tadabbur-AI services (pure Podman, no compose)
#
# Strategy (per service):
#   1. Read .pids/<name>.pid
#      a. "container:<name>" sentinel → podman stop
#      b. numeric PID                → kill
#   2. No PID file → pgrep -f <pattern> fallback, then podman stop
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_DIR="$PROJECT_DIR/.pids"

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

# kill_service <display-name> <pgrep-fallback-pattern>
kill_service() {
    local name="$1" pattern="$2"
    local pid_file="$PID_DIR/$name.pid"

    if [[ -f "$pid_file" ]]; then
        local content; content=$(cat "$pid_file")

        if [[ "$content" == container:* ]]; then
            local container="${content#container:}"
            podman stop "$container" >/dev/null 2>&1 \
                && echo -e "  ${GREEN}✓${NC} $name stopped (podman)" \
                || echo -e "  ${YELLOW}~${NC} $name container not running"
        else
            local pid="$content"
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                sleep 1
                kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
                echo -e "  ${GREEN}✓${NC} $name stopped (PID $pid)"
            else
                echo -e "  ${YELLOW}~${NC} $name PID $pid not running (stale PID file)"
            fi
        fi
        rm -f "$pid_file"
    else
        # No PID file — try pgrep first, then direct podman stop
        local pids
        pids=$(pgrep -f "$pattern" 2>/dev/null | tr '\n' ' ' || true)
        if [[ -n "${pids// /}" ]]; then
            # shellcheck disable=SC2086
            kill $pids 2>/dev/null || true
            sleep 1
            # shellcheck disable=SC2086
            kill -9 $pids 2>/dev/null || true
            echo -e "  ${GREEN}✓${NC} $name stopped (pgrep fallback)"
        else
            echo -e "  ${YELLOW}~${NC} $name not found (no PID file, no matching process)"
        fi
    fi
}

# stop_container <short-name>  e.g. "postgres"
stop_container() {
    local short="$1"
    local name="tadabbur-$short"
    local pid_file="$PID_DIR/container-$short.pid"

    if [[ -f "$pid_file" ]]; then
        local content; content=$(cat "$pid_file")
        if [[ "$content" == container:* ]]; then
            local container="${content#container:}"
            podman stop "$container" >/dev/null 2>&1 \
                && echo -e "  ${GREEN}✓${NC} $short stopped" \
                || echo -e "  ${YELLOW}~${NC} $short already stopped"
        else
            # Numeric PID (container init PID on host)
            kill "$content" 2>/dev/null || true
            podman stop "$name" >/dev/null 2>&1 || true
            echo -e "  ${GREEN}✓${NC} $short stopped (PID $content)"
        fi
        rm -f "$pid_file"
    else
        # No PID file — try podman stop directly
        if podman stop "$name" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $short stopped (direct podman stop)"
        else
            echo -e "  ${YELLOW}~${NC} $short not running"
        fi
    fi
}

# ── Preamble ──────────────────────────────────────────────────────────────────
echo ""
printf '%b╔══════════════════════════════════════════════════════════╗%b\n' "$BLUE" "$NC"
printf '%b║       Stopping Tadabbur-AI Services                      ║%b\n' "$BLUE" "$NC"
printf '%b╚══════════════════════════════════════════════════════════╝%b\n' "$BLUE" "$NC"
echo ""

# ── Application processes ─────────────────────────────────────────────────────
echo -e "${YELLOW}[1/2] Application processes${NC}"
kill_service "rq-worker" "rq.cli worker"
kill_service "frontend"  "vite"
kill_service "backend"   "uvicorn app.main:app"
kill_service "ollama"    "ollama serve"

# ── Infrastructure containers ─────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/2] Infrastructure containers${NC}"
stop_container surrealdb
stop_container redis
stop_container qdrant
stop_container postgres

echo ""
echo -e "${GREEN}All Tadabbur-AI services stopped.${NC}"
echo ""
