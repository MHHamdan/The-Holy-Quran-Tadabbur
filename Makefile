# Tadabbur-AI Makefile
# Automated pipeline for development and deployment
#
# STANDARD: Uses `docker compose` (V2) everywhere - NOT `docker-compose` (V1)

.PHONY: help up down ps logs logs-service restart ensure-services \
        migrate migrate-down migrate-create \
        seed seed-quran seed-stories \
        download-tafseer ingest-tafseer index index-tafseer \
        verify verify-services verify-downloads verify-db verify-qdrant \
        verify-rag verify-tafseer-api verify-chunking verify-translation \
        verify-security verify-e2e \
        test test-cov \
        dev-backend dev-frontend install-backend install-frontend \
        lint format pipeline clean clean-all

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m

# Configuration
COMPOSE_FILE := docker-compose.yml
HEALTH_TIMEOUT := 60
HEALTH_INTERVAL := 2

# Auto-detect docker compose command (V2 plugin or V1 standalone)
DOCKER_COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

help: ## Show this help
	@echo "$(BLUE)Tadabbur-AI - Makefile Commands$(NC)"
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-22s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  make pipeline        # Full setup from scratch"
	@echo "  make up              # Start services only"
	@echo "  make verify          # Run all verifications"
	@echo ""
	@echo "$(BLUE)Service Logs:$(NC)"
	@echo "  make logs            # All services"
	@echo "  make logs-service SERVICE=postgres"

# =============================================================================
# Docker Commands (uses `docker compose` V2)
# =============================================================================

.PHONY: check-docker
check-docker:
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)ERROR: Docker not installed$(NC)"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "$(RED)ERROR: Docker daemon not running. Start with: sudo systemctl start docker$(NC)"; exit 1; }
	@(docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1) || { echo "$(RED)ERROR: Neither 'docker compose' nor 'docker-compose' available$(NC)"; exit 1; }
	@echo "  Using: $(DOCKER_COMPOSE)"

up: check-docker ## Start all services
	@echo "$(GREEN)Starting services...$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)Waiting for services to be healthy...$(NC)"
	@$(MAKE) wait-healthy
	@echo "$(GREEN)Services started successfully$(NC)"
	@$(MAKE) ps

down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down
	@echo "$(GREEN)Services stopped$(NC)"

ps: ## Show running containers
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps

logs: ## View logs for all services (follow mode)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

logs-service: ## View logs for specific service (usage: make logs-service SERVICE=postgres)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f $(SERVICE)

restart: down up ## Restart all services

# Self-healing service management
ensure-services: check-docker ## Ensure services are running and healthy (starts if needed)
	@echo "$(GREEN)Ensuring services are running...$(NC)"
	@if ! $(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps --status running 2>/dev/null | grep -q "running"; then \
		echo "$(YELLOW)Services not running, starting...$(NC)"; \
		$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d; \
	fi
	@$(MAKE) wait-healthy
	@echo "$(GREEN)All services ready$(NC)"
	@$(MAKE) ps

.PHONY: wait-healthy
wait-healthy:
	@echo "$(BLUE)Waiting for services to become healthy (timeout: $(HEALTH_TIMEOUT)s)...$(NC)"
	@elapsed=0; \
	while [ $$elapsed -lt $(HEALTH_TIMEOUT) ]; do \
		all_healthy=true; \
		for service in postgres qdrant redis; do \
			status=$$($(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps --format json 2>/dev/null | grep -o '"Health":"[^"]*"' | head -1 || echo ""); \
			container_status=$$(docker inspect --format='{{.State.Health.Status}}' tadabbur-$$service 2>/dev/null || echo "starting"); \
			if [ "$$container_status" != "healthy" ]; then \
				all_healthy=false; \
				break; \
			fi; \
		done; \
		if [ "$$all_healthy" = "true" ]; then \
			echo "$(GREEN)All services healthy$(NC)"; \
			exit 0; \
		fi; \
		echo "  Waiting... ($$elapsed/$(HEALTH_TIMEOUT)s)"; \
		sleep $(HEALTH_INTERVAL); \
		elapsed=$$((elapsed + $(HEALTH_INTERVAL))); \
	done; \
	echo "$(RED)Timeout waiting for services. Check logs:$(NC)"; \
	echo "  make logs-service SERVICE=postgres"; \
	echo "  make logs-service SERVICE=qdrant"; \
	echo "  make logs-service SERVICE=redis"; \
	exit 1

.PHONY: check-ports
check-ports: ## Check if required ports are available
	@echo "$(BLUE)Checking port availability...$(NC)"
	@for port in 5432 6333 6379; do \
		if lsof -i :$$port >/dev/null 2>&1; then \
			echo "$(YELLOW)WARNING: Port $$port is in use$(NC)"; \
			lsof -i :$$port | head -2; \
		else \
			echo "  Port $$port: $(GREEN)available$(NC)"; \
		fi; \
	done

# =============================================================================
# Database Commands
# =============================================================================

migrate: ensure-services ## Run database migrations
	@echo "$(GREEN)Running migrations...$(NC)"
	cd backend && alembic upgrade head
	@echo "$(GREEN)Migrations complete$(NC)"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

# =============================================================================
# Data Seeding Commands
# =============================================================================

seed: seed-quran seed-stories ## Seed all data

seed-quran: ensure-services ## Seed Quran verses
	@echo "$(GREEN)Seeding Quran verses...$(NC)"
	cd backend && python scripts/ingest/seed_quran.py

seed-stories: ensure-services ## Seed stories data
	@echo "$(GREEN)Seeding stories...$(NC)"
	cd backend && python scripts/ingest/seed_stories.py

# =============================================================================
# Tafseer Commands
# =============================================================================

download-tafseer: ## Download tafseer from APIs (rate-limited, cached)
	@echo "$(GREEN)Downloading tafseer sources...$(NC)"
	cd backend && python scripts/datasets/download_tafseer.py

download-tafseer-source: ## Download specific tafseer (usage: make download-tafseer-source SRC=ibn_kathir_en)
	@echo "$(GREEN)Downloading tafseer: $(SRC)...$(NC)"
	cd backend && python scripts/datasets/download_tafseer.py $(SRC)

ingest-tafseer: ensure-services ## Ingest downloaded tafseer into DB and Qdrant
	@echo "$(GREEN)Ingesting tafseer...$(NC)"
	cd backend && python scripts/ingest/ingest_tafseer.py

ingest-tafseer-source: ensure-services ## Ingest specific tafseer (usage: make ingest-tafseer-source SRC=ibn_kathir_en)
	@echo "$(GREEN)Ingesting tafseer: $(SRC)...$(NC)"
	cd backend && python scripts/ingest/ingest_tafseer.py $(SRC)

tafseer-pipeline: download-tafseer ingest-tafseer ## Full tafseer pipeline (download + ingest)
	@echo "$(GREEN)Tafseer pipeline complete$(NC)"

# =============================================================================
# Indexing Commands
# =============================================================================

index: index-tafseer ## Index all vectors

index-tafseer: ensure-services ## Index tafseer into Qdrant
	@echo "$(GREEN)Indexing tafseer chunks...$(NC)"
	cd backend && python scripts/index/index_tafseer.py

index-cpu: ensure-services ## Index using CPU only (for low-memory systems)
	@echo "$(GREEN)Indexing tafseer chunks (CPU mode)...$(NC)"
	cd backend && EMBEDDING_DEVICE=cpu python scripts/index/index_tafseer.py

index-small: ensure-services ## Index using small model (fastest, 384 dim)
	@echo "$(GREEN)Indexing tafseer chunks (small model, CPU)...$(NC)"
	cd backend && EMBEDDING_DEVICE=cpu EMBEDDING_MODEL=intfloat/multilingual-e5-small python scripts/index/index_tafseer.py

index-gpu: ensure-services ## Index using GPU with large model (best quality, needs 3GB+ VRAM)
	@echo "$(GREEN)Indexing tafseer chunks (GPU mode, large model)...$(NC)"
	cd backend && EMBEDDING_DEVICE=cuda EMBEDDING_MODEL=intfloat/multilingual-e5-large python scripts/index/index_tafseer.py

# =============================================================================
# Verification Commands
# =============================================================================

verify: ensure-services verify-services verify-downloads verify-db verify-qdrant verify-rag verify-chunking verify-translation verify-security ## Run all verifications
	@echo "$(GREEN)All verifications complete$(NC)"

verify-services: ## Verify all services are running (with diagnostics)
	@echo "$(GREEN)Verifying services...$(NC)"
	cd backend && python scripts/verify/verify_services.py

verify-downloads: ## Verify dataset downloads
	@echo "$(GREEN)Verifying downloads...$(NC)"
	cd backend && python scripts/verify/verify_downloads.py

verify-db: ## Verify database is seeded (includes story validation)
	@echo "$(GREEN)Verifying database and stories...$(NC)"
	cd backend && python scripts/verify/verify_db_seed.py

verify-qdrant: ## Verify Qdrant index
	@echo "$(GREEN)Verifying Qdrant...$(NC)"
	cd backend && python scripts/verify/verify_qdrant_index.py

verify-rag: ## Verify RAG pipeline
	@echo "$(GREEN)Verifying RAG...$(NC)"
	cd backend && python scripts/verify/verify_rag_response.py

verify-tafseer-api: ## Verify tafseer API endpoints and schema
	@echo "$(GREEN)Verifying tafseer APIs...$(NC)"
	cd backend && python scripts/verify/verify_tafseer_api.py

verify-chunking: ## Verify ayah-anchored chunking invariants
	@echo "$(GREEN)Verifying chunking...$(NC)"
	cd backend && python scripts/verify/verify_chunking.py

verify-translation: ## Verify translation service configuration
	@echo "$(GREEN)Verifying translation...$(NC)"
	cd backend && python scripts/verify/verify_translation.py

verify-security: ## Verify metrics/health endpoint security
	@echo "$(GREEN)Verifying security...$(NC)"
	cd backend && python scripts/verify/verify_metrics_security.py

verify-e2e: ## Run full Docker E2E verification
	@echo "$(GREEN)Running Docker E2E verification...$(NC)"
	cd backend && python scripts/verify/verify_e2e_docker.py --skip-startup

verify-e2e-full: ## Run full Docker E2E verification (includes startup)
	@echo "$(GREEN)Running full Docker E2E verification...$(NC)"
	cd backend && python scripts/verify/verify_e2e_docker.py --full --keep-running

# =============================================================================
# Testing Commands
# =============================================================================

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	cd backend && pytest tests/ -v

test-cov: ## Run tests with coverage
	cd backend && pytest tests/ -v --cov=app --cov-report=html

test-quick: ## Run tests quickly (no verbose)
	cd backend && pytest tests/ -q

# =============================================================================
# Development Commands
# =============================================================================

dev-backend: ensure-services ## Run backend in development mode
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend: ## Run frontend in development mode
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
# Full Pipeline Command
# =============================================================================

pipeline: ## Run the complete pipeline end-to-end (starts services if needed)
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(BLUE)TADABBUR-AI FULL PIPELINE$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "$(GREEN)[Step 1/9] Checking Docker...$(NC)"
	@$(MAKE) check-docker
	@echo ""
	@echo "$(GREEN)[Step 2/9] Ensuring services are running...$(NC)"
	@$(MAKE) ensure-services
	@echo ""
	@echo "$(GREEN)[Step 3/9] Verifying services...$(NC)"
	@$(MAKE) verify-services || { echo "$(RED)FAIL: Services not ready$(NC)"; exit 1; }
	@echo ""
	@echo "$(GREEN)[Step 4/9] Verifying downloads...$(NC)"
	@$(MAKE) verify-downloads || echo "$(YELLOW)WARN: Some downloads need attention$(NC)"
	@echo ""
	@echo "$(GREEN)[Step 5/9] Running migrations...$(NC)"
	@$(MAKE) migrate
	@echo ""
	@echo "$(GREEN)[Step 6/9] Seeding Quran data...$(NC)"
	@$(MAKE) seed-quran || echo "$(YELLOW)WARN: Quran already seeded$(NC)"
	@echo ""
	@echo "$(GREEN)[Step 7/9] Seeding stories...$(NC)"
	@$(MAKE) seed-stories || echo "$(YELLOW)WARN: Stories already seeded$(NC)"
	@echo ""
	@echo "$(GREEN)[Step 8/9] Verifying database...$(NC)"
	@$(MAKE) verify-db || { echo "$(RED)FAIL: Database not seeded correctly$(NC)"; exit 1; }
	@echo ""
	@echo "$(GREEN)[Step 9/9] Running tests...$(NC)"
	@$(MAKE) test-quick
	@echo ""
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)PIPELINE COMPLETE$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "$(BLUE)Services running:$(NC)"
	@$(MAKE) ps
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Set ANTHROPIC_API_KEY in .env for RAG"
	@echo "  2. Run 'make tafseer-pipeline' to download/ingest tafseer"
	@echo "  3. Run 'make index' after adding tafseer"
	@echo "  4. Access API at http://localhost:8000/docs"
	@echo "  5. Run 'make verify' to run all verifications"

# =============================================================================
# Cleanup Commands
# =============================================================================

clean: ## Clean up generated files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: clean ## Clean up everything including Docker volumes
	@echo "$(RED)WARNING: This will delete all data volumes$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v
	@echo "$(GREEN)Complete cleanup done$(NC)"

# =============================================================================
# Diagnostic Commands
# =============================================================================

status: ## Show full system status
	@echo "$(BLUE)=== Docker Status ===$(NC)"
	@docker info --format '{{.ServerVersion}}' 2>/dev/null && echo "Docker: $(GREEN)running$(NC)" || echo "Docker: $(RED)not running$(NC)"
	@echo ""
	@echo "$(BLUE)=== Container Status ===$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps 2>/dev/null || echo "No containers running"
	@echo ""
	@echo "$(BLUE)=== Port Usage ===$(NC)"
	@$(MAKE) check-ports 2>/dev/null || true
