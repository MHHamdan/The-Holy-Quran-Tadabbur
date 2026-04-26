# Tadabbur-AI Makefile
# Uses pure Podman (podman run/stop/rm) — no docker, no compose

.PHONY: help list start stop restart doctor \
        ps logs logs-container \
        check-podman check-ports ensure-services \
        migrate migrate-down migrate-create \
        seed seed-quran seed-stories \
        download-tafseer download-tafseer-source \
        ingest-tafseer ingest-tafseer-source tafseer-pipeline \
        index index-tafseer index-cpu index-small index-gpu \
        verify verify-services verify-downloads verify-db verify-qdrant \
        verify-rag verify-tafseer-api verify-chunking verify-translation \
        verify-security verify-e2e verify-e2e-full \
        test test-cov test-quick \
        dev dev-backend dev-frontend \
        install-backend install-frontend \
        lint format pipeline \
        clean clean-all status

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
BLUE   := \033[0;34m
NC     := \033[0m

# ── Configuration ─────────────────────────────────────────────────────────────
HOST_IP      := 172.24.50.21
BACKEND_PORT := 8002

# =============================================================================
# Help
# =============================================================================

list: help ## Alias for help

help: ## Show this help
	@echo "$(BLUE)Tadabbur-AI — Makefile targets$(NC)"
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-22s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Quick start:$(NC)"
	@echo "  make start           # Pull images & start everything"
	@echo "  make stop            # Stop everything"
	@echo "  make restart         # stop + start"
	@echo "  make doctor          # Health-check all services"
	@echo "  make logs            # Tail process log files"
	@echo "  make logs-container  # Follow a container's log (SERVICE=postgres)"
	@echo ""
	@echo "$(BLUE)Access URLs:$(NC)"
	@echo "  Frontend : http://$(HOST_IP):3000"
	@echo "  Backend  : http://$(HOST_IP):$(BACKEND_PORT)/docs"

# =============================================================================
# Core lifecycle (backed by scripts/)
# =============================================================================

start: check-podman ## Start all services via scripts/start_all.sh
	@bash scripts/start_all.sh

stop: ## Stop all services via scripts/stop_all.sh
	@bash scripts/stop_all.sh

restart: stop start ## Restart all services

# =============================================================================
# Diagnostics
# =============================================================================

doctor: ## Health-check all services
	@echo "$(BLUE)╔══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║         Tadabbur-AI Doctor                               ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BLUE)── PID files ──────────────────────────────────────────────$(NC)"
	@for svc in backend frontend rq-worker \
	            container-postgres container-qdrant container-redis container-surrealdb; do \
		f=".pids/$$svc.pid"; \
		if [ -f "$$f" ]; then \
			pid=$$(cat "$$f"); \
			case "$$pid" in \
				container:*) printf '  %b✓%b  %-30s %s\n' "$(GREEN)" "$(NC)" "$$svc" "(podman-managed: $$pid)" ;; \
				*) kill -0 "$$pid" 2>/dev/null \
					&& printf '  %b✓%b  %-30s PID %s running\n'  "$(GREEN)" "$(NC)" "$$svc" "$$pid" \
					|| printf '  %b✗%b  %-30s PID %s DEAD (stale)\n' "$(RED)"   "$(NC)" "$$svc" "$$pid" ;; \
			esac; \
		else \
			printf '  %b~%b  %-30s no PID file\n' "$(YELLOW)" "$(NC)" "$$svc"; \
		fi; \
	done
	@echo ""
	@echo "$(BLUE)── User-facing ports ($(HOST_IP)) ────────────────────────$(NC)"
	@for pair in "API:$(HOST_IP):$(BACKEND_PORT)" "Frontend:$(HOST_IP):3000" "Qdrant:$(HOST_IP):6333"; do \
		label=$$(echo "$$pair" | cut -d: -f1); \
		host=$$(echo  "$$pair" | cut -d: -f2); \
		port=$$(echo  "$$pair" | cut -d: -f3); \
		nc -z "$$host" "$$port" 2>/dev/null \
			&& printf '  %b✓%b  %-12s http://%s:%s\n'      "$(GREEN)" "$(NC)" "$$label" "$$host" "$$port" \
			|| printf '  %b✗%b  %-12s http://%s:%s  UNREACHABLE\n' "$(RED)"   "$(NC)" "$$label" "$$host" "$$port"; \
	done
	@echo ""
	@echo "$(BLUE)── Internal ports (localhost — process-to-process) ────────$(NC)"
	@for pair in "Postgres:5432" "Redis:6379" "SurrealDB:8529"; do \
		label=$$(echo "$$pair" | cut -d: -f1); \
		port=$$(echo  "$$pair" | cut -d: -f2); \
		nc -z localhost "$$port" 2>/dev/null \
			&& printf '  %b✓%b  %-12s localhost:%s\n'  "$(GREEN)" "$(NC)" "$$label" "$$port" \
			|| printf '  %b✗%b  %-12s localhost:%s  UNREACHABLE\n' "$(RED)" "$(NC)" "$$label" "$$port"; \
	done
	@echo ""
	@echo "$(BLUE)── Podman containers ──────────────────────────────────────$(NC)"
	@for c in tadabbur-postgres tadabbur-qdrant tadabbur-redis tadabbur-surrealdb; do \
		st=$$(podman inspect --format '{{.State.Status}}' "$$c" 2>/dev/null || echo "absent"); \
		case "$$st" in \
			running) printf '  %b✓%b  %-26s %s\n' "$(GREEN)" "$(NC)" "$$c" "$$st" ;; \
			absent)  printf '  %b~%b  %-26s %s\n' "$(YELLOW)" "$(NC)" "$$c" "not found" ;; \
			*)       printf '  %b✗%b  %-26s %s\n' "$(RED)"   "$(NC)" "$$c" "$$st" ;; \
		esac; \
	done
	@echo ""
	@echo "$(BLUE)── Log files ──────────────────────────────────────────────$(NC)"
	@for f in backend frontend rq-worker migrations podman; do \
		lf="logs/$$f.log"; \
		[ -f "$$lf" ] \
			&& printf '  %b✓%b  %-18s (%s lines)\n'   "$(GREEN)" "$(NC)" "$$f" "$$(wc -l < $$lf)" \
			|| printf '  %b~%b  %-18s (no log yet)\n' "$(YELLOW)" "$(NC)" "$$f"; \
	done
	@echo ""

ps: ## List Tadabbur containers
	@podman ps --filter 'name=tadabbur' \
		--format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

logs: ## Tail process log files (SERVICE=backend to filter one)
	@if [ -n "$(SERVICE)" ]; then \
		echo "$(BLUE)Tailing logs/$(SERVICE).log$(NC)"; \
		tail -f "logs/$(SERVICE).log"; \
	else \
		echo "$(BLUE)Tailing backend / frontend / rq-worker logs (Ctrl-C to stop)$(NC)"; \
		tail -f logs/backend.log logs/frontend.log logs/rq-worker.log 2>/dev/null \
		|| tail -f logs/*.log 2>/dev/null \
		|| echo "$(YELLOW)No log files yet — run: make start$(NC)"; \
	fi

logs-container: ## Follow a container's podman log (SERVICE=postgres)
	@podman logs -f "tadabbur-$(SERVICE)"

status: ## Show full system status
	@echo "$(BLUE)=== Podman $(shell podman --version 2>/dev/null) ===$(NC)"
	@podman info >/dev/null 2>&1 && echo "  Podman: $(GREEN)running$(NC)" || echo "  Podman: $(RED)not running$(NC)"
	@echo ""
	@$(MAKE) --no-print-directory ps
	@echo ""
	@$(MAKE) --no-print-directory check-ports

# =============================================================================
# Podman checks
# =============================================================================

check-podman:
	@command -v podman >/dev/null 2>&1 \
		|| { echo "$(RED)ERROR: podman not installed$(NC)"; exit 1; }
	@podman info >/dev/null 2>&1 \
		|| { echo "$(RED)ERROR: Podman not running.$(NC)"; \
		     echo "  Try: systemctl --user start podman.socket"; exit 1; }

check-ports: ## Check if Tadabbur ports are free
	@echo "$(BLUE)Checking port availability...$(NC)"
	@for port in 5432 6333 6379 8529 $(BACKEND_PORT) 3000; do \
		pid=$$(lsof -ti :$$port 2>/dev/null | head -1 || true); \
		if [ -n "$$pid" ]; then \
			echo "  $(YELLOW)BUSY$(NC)  :$$port  →  PID $$pid"; \
		else \
			echo "  $(GREEN)free$(NC)  :$$port"; \
		fi; \
	done

ensure-services: ## Ensure all infra containers are running (starts if needed)
	@echo "$(GREEN)Ensuring infrastructure containers are running...$(NC)"
	@for svc in postgres qdrant redis surrealdb; do \
		st=$$(podman inspect --format '{{.State.Status}}' "tadabbur-$$svc" 2>/dev/null || echo "absent"); \
		if [ "$$st" != "running" ]; then \
			echo "  $(YELLOW)~$(NC)  tadabbur-$$svc not running (status: $$st) — run 'make start'"; \
		else \
			echo "  $(GREEN)✓$(NC)  tadabbur-$$svc running"; \
		fi; \
	done

# =============================================================================
# Database
# =============================================================================

migrate: ensure-services ## Run database migrations
	@echo "$(GREEN)Running migrations...$(NC)"
	cd backend && alembic upgrade head
	@echo "$(GREEN)Migrations complete$(NC)"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

migrate-create: ## Create a new migration (MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

# =============================================================================
# Data seeding
# =============================================================================

seed: seed-quran seed-tafseer seed-stories seed-concepts seed-themes seed-rhetorical seed-story-atlas ## Seed ALL data (run after migrate)
	@echo "$(GREEN)All data seeded successfully$(NC)"

seed-quran: ensure-services ## Seed Quran verses + populate text_normalized
	@echo "$(GREEN)Seeding Quran verses...$(NC)"
	PYTHONPATH=backend python backend/scripts/ingest/seed_quran.py
	@echo "$(GREEN)Populating text_normalized for search...$(NC)"
	PYTHONPATH=backend python -c "\
import re, sys; sys.path.insert(0,'backend'); \
from sqlalchemy import create_engine, text; from sqlalchemy.orm import Session; \
def norm(t): \
    t=t.replace('\ufeff','').replace('\u0640',''); \
    t=re.sub(r'[\u064b-\u065f\u0670]','',t); \
    t=re.sub(r'[\u0622\u0623\u0625\u0671]','\u0627',t); \
    return t.replace('\u0629','\u0647').replace('\u0649','\u064a').strip(); \
e=create_engine('postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur'); \
s=Session(e); rows=s.execute(text('SELECT id,text_uthmani FROM quran_verses')).all(); \
s.execute(text('UPDATE quran_verses SET text_normalized=:n WHERE id=:i'),[{'i':r,'n':norm(t or '')} for r,t in rows]); \
s.commit(); print(f'Normalized {len(rows)} verses')"

seed-tafseer: ensure-services ## Seed all 6 tafseer sources
	@echo "$(GREEN)Seeding tafseer (6 sources × 6236 verses)...$(NC)"
	PYTHONPATH=backend python backend/scripts/ingest/seed_tafseer.py

seed-stories: ensure-services ## Seed stories, story atlas, and story graphs
	@echo "$(GREEN)Seeding stories...$(NC)"
	PYTHONPATH=backend python backend/scripts/ingest/seed_stories.py
	PYTHONPATH=backend python backend/scripts/ingest/seed_story_atlas.py
	PYTHONPATH=backend python backend/scripts/ingest/seed_story_graphs.py

seed-concepts: ensure-services ## Seed concepts and occurrences
	@echo "$(GREEN)Seeding concepts...$(NC)"
	PYTHONPATH=backend python backend/scripts/ingest/seed_concepts.py

seed-themes: ensure-services ## Seed Quranic themes
	@echo "$(GREEN)Seeding themes...$(NC)"
	PYTHONPATH=backend python backend/scripts/ingest/seed_themes.py

seed-rhetorical: ensure-services ## Seed rhetorical devices
	@echo "$(GREEN)Seeding rhetorical devices...$(NC)"
	PYTHONPATH=backend python backend/scripts/ingest/seed_rhetorical_devices.py

seed-story-atlas: ensure-services ## Seed story atlas clusters and graphs
	@echo "$(GREEN)Seeding story atlas...$(NC)"
	PYTHONPATH=backend python backend/scripts/ingest/seed_story_atlas.py
	PYTHONPATH=backend python backend/scripts/ingest/seed_story_graphs.py

# =============================================================================
# Tafseer
# =============================================================================

download-tafseer: ## Download tafseer from APIs (rate-limited, cached)
	@echo "$(GREEN)Downloading tafseer sources...$(NC)"
	cd backend && python scripts/datasets/download_tafseer.py

download-tafseer-source: ## Download specific tafseer (SRC=ibn_kathir_en)
	@echo "$(GREEN)Downloading tafseer: $(SRC)...$(NC)"
	cd backend && python scripts/datasets/download_tafseer.py $(SRC)

ingest-tafseer: ensure-services ## Ingest downloaded tafseer into DB and Qdrant
	@echo "$(GREEN)Ingesting tafseer...$(NC)"
	cd backend && python scripts/ingest/ingest_tafseer.py

ingest-tafseer-source: ensure-services ## Ingest specific tafseer (SRC=ibn_kathir_en)
	@echo "$(GREEN)Ingesting tafseer: $(SRC)...$(NC)"
	cd backend && python scripts/ingest/ingest_tafseer.py $(SRC)

tafseer-pipeline: download-tafseer ingest-tafseer ## Full tafseer pipeline
	@echo "$(GREEN)Tafseer pipeline complete$(NC)"

# =============================================================================
# Indexing
# =============================================================================

index: index-tafseer ## Index all vectors

index-tafseer: ensure-services ## Index tafseer into Qdrant
	@echo "$(GREEN)Indexing tafseer chunks...$(NC)"
	cd backend && python scripts/index/index_tafseer.py

index-cpu: ensure-services ## Index using CPU only
	@echo "$(GREEN)Indexing (CPU mode)...$(NC)"
	cd backend && EMBEDDING_DEVICE=cpu python scripts/index/index_tafseer.py

index-small: ensure-services ## Index using small model (fastest)
	@echo "$(GREEN)Indexing (small model, CPU)...$(NC)"
	cd backend && EMBEDDING_DEVICE=cpu EMBEDDING_MODEL=intfloat/multilingual-e5-small python scripts/index/index_tafseer.py

index-gpu: ensure-services ## Index using GPU + large model
	@echo "$(GREEN)Indexing (GPU, large model)...$(NC)"
	cd backend && EMBEDDING_DEVICE=cuda EMBEDDING_MODEL=intfloat/multilingual-e5-large python scripts/index/index_tafseer.py

# =============================================================================
# Verification
# =============================================================================

verify: ensure-services verify-services verify-downloads verify-db verify-qdrant \
        verify-rag verify-chunking verify-translation verify-security ## Run all verifications
	@echo "$(GREEN)All verifications complete$(NC)"

verify-services: ## Verify all services are running
	@echo "$(GREEN)Verifying services...$(NC)"
	cd backend && python scripts/verify/verify_services.py

verify-downloads: ## Verify dataset downloads
	@echo "$(GREEN)Verifying downloads...$(NC)"
	cd backend && python scripts/verify/verify_downloads.py

verify-db: ## Verify database is seeded
	@echo "$(GREEN)Verifying database...$(NC)"
	cd backend && python scripts/verify/verify_db_seed.py

verify-qdrant: ## Verify Qdrant index
	@echo "$(GREEN)Verifying Qdrant...$(NC)"
	cd backend && python scripts/verify/verify_qdrant_index.py

verify-rag: ## Verify RAG pipeline
	@echo "$(GREEN)Verifying RAG...$(NC)"
	cd backend && python scripts/verify/verify_rag_response.py

verify-tafseer-api: ## Verify tafseer API endpoints
	@echo "$(GREEN)Verifying tafseer APIs...$(NC)"
	cd backend && python scripts/verify/verify_tafseer_api.py

verify-chunking: ## Verify ayah-anchored chunking invariants
	@echo "$(GREEN)Verifying chunking...$(NC)"
	cd backend && python scripts/verify/verify_chunking.py

verify-translation: ## Verify translation service
	@echo "$(GREEN)Verifying translation...$(NC)"
	cd backend && python scripts/verify/verify_translation.py

verify-security: ## Verify metrics/health endpoint security
	@echo "$(GREEN)Verifying security...$(NC)"
	cd backend && python scripts/verify/verify_metrics_security.py

verify-e2e: ## Run E2E verification (skip startup)
	@echo "$(GREEN)Running E2E verification...$(NC)"
	cd backend && python scripts/verify/verify_e2e_docker.py --skip-startup

verify-e2e-full: ## Run full E2E verification (includes startup)
	@echo "$(GREEN)Running full E2E verification...$(NC)"
	cd backend && python scripts/verify/verify_e2e_docker.py --full --keep-running

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	cd backend && pytest tests/ -v

test-cov: ## Run tests with coverage
	cd backend && pytest tests/ -v --cov=app --cov-report=html

test-quick: ## Run tests (no verbose)
	cd backend && pytest tests/ -q

# =============================================================================
# Development
# =============================================================================

dev: check-podman ## Start infra containers then run backend & frontend locally
	@echo "$(GREEN)Starting infra containers...$(NC)"
	@for svc in postgres qdrant redis surrealdb; do \
		st=$$(podman inspect --format '{{.State.Status}}' "tadabbur-$$svc" 2>/dev/null || echo "absent"); \
		[ "$$st" = "running" ] \
			&& echo "  $(YELLOW)~$(NC)  tadabbur-$$svc already running" \
			|| podman start "tadabbur-$$svc" 2>/dev/null \
			|| echo "  $(RED)✗$(NC)  tadabbur-$$svc not found — run 'make start' first"; \
	done
	@echo "$(BLUE)  Backend : http://$(HOST_IP):$(BACKEND_PORT)/docs$(NC)"
	@echo "$(BLUE)  Frontend: http://$(HOST_IP):3000$(NC)"
	@trap 'kill 0' INT; \
	(cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)) & \
	(cd frontend && npm run dev) & \
	wait

dev-backend: ensure-services ## Run backend dev server only
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

dev-frontend: ## Run frontend dev server only
	cd frontend && npm run dev

install-backend: ## Install backend dependencies
	cd backend && pip install -e ".[dev]"

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

lint: ## Run linters
	cd backend && ruff check app/
	cd backend && black --check app/

format: ## Format code
	cd backend && black app/
	cd backend && ruff check --fix app/

# =============================================================================
# Full pipeline
# =============================================================================

pipeline: ## End-to-end setup from scratch
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(BLUE)  TADABBUR-AI FULL PIPELINE             $(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "$(GREEN)[1/7] Checking Podman...$(NC)"
	@$(MAKE) --no-print-directory check-podman
	@echo ""
	@echo "$(GREEN)[2/7] Starting services...$(NC)"
	@bash scripts/start_all.sh
	@echo ""
	@echo "$(GREEN)[3/7] Verifying services...$(NC)"
	@$(MAKE) --no-print-directory verify-services \
		|| { echo "$(RED)FAIL: services not ready$(NC)"; exit 1; }
	@echo ""
	@echo "$(GREEN)[4/7] Verifying downloads...$(NC)"
	@$(MAKE) --no-print-directory verify-downloads \
		|| echo "$(YELLOW)WARN: some downloads need attention$(NC)"
	@echo ""
	@echo "$(GREEN)[5/7] Seeding data...$(NC)"
	@$(MAKE) --no-print-directory seed || echo "$(YELLOW)WARN: Some seed steps may have been skipped (data may already exist)$(NC)"
	@echo ""
	@echo "$(GREEN)[6/7] Verifying database...$(NC)"
	@$(MAKE) --no-print-directory verify-db \
		|| { echo "$(RED)FAIL: database not seeded$(NC)"; exit 1; }
	@echo ""
	@echo "$(GREEN)[7/7] Running tests...$(NC)"
	@$(MAKE) --no-print-directory test-quick
	@echo ""
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)  PIPELINE COMPLETE                     $(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "  Frontend : http://$(HOST_IP):3000"
	@echo "  Backend  : http://$(HOST_IP):$(BACKEND_PORT)/docs"

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove generated files (__pycache__, .pyc, etc.)
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache"   -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

clean-all: stop clean ## DESTRUCTIVE: stop services and delete all data volumes
	@echo "$(RED)WARNING: This will permanently delete all Podman data volumes.$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	@for vol in tadabbur_postgres_data tadabbur_qdrant_data \
	            tadabbur_redis_data tadabbur_surrealdb_data; do \
		podman volume rm "$$vol" 2>/dev/null \
			&& echo "  $(GREEN)✓$(NC)  $$vol removed" \
			|| echo "  $(YELLOW)~$(NC)  $$vol not found"; \
	done
	@for ctr in tadabbur-postgres tadabbur-qdrant tadabbur-redis tadabbur-surrealdb; do \
		podman rm -f "$$ctr" 2>/dev/null \
			&& echo "  $(GREEN)✓$(NC)  $$ctr removed" \
			|| echo "  $(YELLOW)~$(NC)  $$ctr not found"; \
	done
	@echo "$(GREEN)Complete cleanup done$(NC)"
