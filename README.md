# Tadabbur-AI

RAG-grounded Quranic knowledge platform with story connections.

## Overview

Tadabbur-AI is a scholarly Quranic knowledge platform that:
- Provides **grounded answers** with mandatory citations from authenticated tafseer sources
- Maps **Quranic stories** and their connections across different surahs
- Supports **bilingual interface** (Arabic/English) with RTL support
- Uses **RAG (Retrieval-Augmented Generation)** to avoid AI hallucinations

## Safety Rules

1. **NEVER** invent tafseer - LLM may ONLY summarize retrieved evidence
2. Every paragraph **MUST** include at least one citation referencing a retrieved `chunk_id`
3. Citations are **validated** - cited chunks must exist in retrieved set
4. For insufficient evidence: "This requires further scholarly consultation"
5. For fiqh/rulings: informational summary only, no fatwa language

## Quick Start

### Prerequisites
- Docker & Docker Compose V2 (uses `docker compose`, not `docker-compose`)
- Python 3.11+
- Node.js 20+
- Make

### Setup

1. **Clone and configure:**
   ```bash
   cd tadabbur
   cp .env.example .env
   # Edit .env and add ANTHROPIC_API_KEY
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e "./backend[dev]"
   ```

3. **Run the full pipeline:**
   ```bash
   make pipeline
   ```

   This will:
   - Check Docker is running
   - Start all services (postgres, qdrant, redis)
   - Wait for services to be healthy
   - Run database migrations
   - Seed Quran verses and stories
   - Verify all components
   - Run tests

4. **Access the application:**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:3000 (if started)

## Makefile Commands

### Quick Reference

```bash
# ONE COMMAND TO RULE THEM ALL
make pipeline        # Full setup from scratch (starts services, seeds data, verifies)

# Docker Services
make up              # Start all services
make down            # Stop all services
make ps              # Show running containers
make logs            # View all logs (follow mode)
make logs-service SERVICE=postgres   # View specific service logs
make restart         # Restart all services
make ensure-services # Auto-start services if not running

# Database
make migrate         # Run migrations
make seed            # Seed all data (quran + stories)
make seed-quran      # Seed Quran verses only
make seed-stories    # Seed stories only

# Verification
make verify          # Run ALL verifications (auto-starts services)
make verify-services # Check services health with diagnostics
make verify-db       # Check database seeding + story manifest
make verify-qdrant   # Check vector database
make verify-rag      # Check RAG pipeline
make verify-security # Check metrics endpoint security
make verify-e2e      # Run Docker E2E verification

# Tafseer Pipeline
make download-tafseer     # Download tafseer from APIs
make ingest-tafseer       # Ingest tafseer into DB + Qdrant
make index-tafseer        # Index tafseer vectors
make tafseer-pipeline     # Full tafseer pipeline

# Development
make dev-backend     # Run backend in dev mode
make dev-frontend    # Run frontend in dev mode
make test            # Run all tests
make test-quick      # Run tests (no verbose)

# Diagnostics
make status          # Show full system status
make check-ports     # Check if required ports are available
```

### Example Workflows

**Fresh Setup:**
```bash
make pipeline
```

**Just Start Services:**
```bash
make up
```

**Services Already Running, Run Verification:**
```bash
make verify
```

**Troubleshoot Service Issues:**
```bash
make status
make logs-service SERVICE=postgres
```

## Troubleshooting

### Docker Not Running
```bash
# Check Docker status
sudo systemctl status docker

# Start Docker
sudo systemctl start docker

# Verify Docker is working
docker ps
```

### Port Conflicts
```bash
# Check which ports are in use
make check-ports

# Common ports:
# 5432 - PostgreSQL
# 6333 - Qdrant
# 6379 - Redis

# Find what's using a port
lsof -i :5432
```

### Services Won't Start
```bash
# View service logs
make logs-service SERVICE=postgres
make logs-service SERVICE=qdrant
make logs-service SERVICE=redis

# Restart everything
make restart

# Nuclear option: remove volumes and start fresh
make clean-all
make up
```

### Database Connection Refused
```bash
# Ensure services are healthy
make ensure-services

# Check container status
docker inspect tadabbur-postgres --format='{{.State.Health.Status}}'
```

## Project Structure

```
tadabbur/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── core/             # Configuration
│   │   ├── db/               # Database setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── rag/              # RAG pipeline
│   │   ├── services/         # Business logic
│   │   └── validators/       # Citation validators
│   ├── alembic/              # Database migrations
│   ├── scripts/
│   │   ├── datasets/         # Data download scripts
│   │   ├── verify/           # Verification scripts
│   │   ├── ingest/           # Data seeding scripts
│   │   └── index/            # Vector indexing scripts
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/       # React components
│       ├── pages/            # Page components
│       ├── i18n/             # Translations
│       ├── lib/              # API client
│       └── stores/           # State management
├── data/
│   ├── raw/                  # Raw downloaded data
│   ├── processed/            # Processed data
│   └── manifests/            # Dataset manifests
├── docker-compose.yml
├── Makefile
└── README.md
```

## API Endpoints

### Quran
- `GET /api/v1/quran/suras/{sura_no}` - Get verses for a sura
- `GET /api/v1/quran/verses/{sura}/{aya}` - Get specific verse
- `GET /api/v1/quran/tafseer/{sura}/{aya}` - Get tafseer for verse

### Stories
- `GET /api/v1/stories` - List all stories
- `GET /api/v1/stories/{id}` - Get story with segments
- `GET /api/v1/stories/{id}/graph` - Get story graph data

### RAG
- `POST /api/v1/rag/ask` - Ask a question
  ```json
  {
    "question": "What is the meaning of Ayat al-Kursi?",
    "language": "en",
    "include_scholarly_debate": true,
    "preferred_sources": []
  }
  ```

  Response includes:
  - `answer`: Grounded response with citations
  - `citations`: List of source citations
  - `confidence`: Confidence score (0-1)
  - `evidence`: Raw evidence chunks for transparency
  - `evidence_density`: Count of chunks and sources used
  - `api_version`: API version for compatibility checking

### Sources
- `GET /api/v1/rag/sources` - Get available tafseer sources (enabled only)
- `GET /api/v1/rag/admin/sources` - Get all sources (requires admin token)
- `PUT /api/v1/rag/admin/sources/{id}/toggle` - Enable/disable source (requires admin token)

### Health
- `GET /health` - Basic health check (public)
- `GET /ready` - Readiness check (public)
- `GET /health/detailed` - Detailed health (protected in production)
- `GET /metrics` - Application metrics (protected in production)

## Adding Data Sources

### Adding Tafseer Sources

1. Edit `data/manifests/tafseer_sources.json`
2. Add source with URL and license information
3. Run `make tafseer-pipeline`

### Adding Stories

1. Edit `data/manifests/stories.json`
2. Add story with segments and verse references
3. Ensure minimum 25 total connections (to prevent regression to "catalog only")
4. Run `make seed-stories`

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic v2
- **Database:** PostgreSQL 15
- **Vector DB:** Qdrant
- **Cache:** Redis 7
- **Frontend:** React, TypeScript, Tailwind CSS
- **Visualization:** Cytoscape.js
- **LLM:** Anthropic Claude

## Environment Variables

```env
# Required
DATABASE_URL=postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur

# LLM Provider (choose one)
LLM_PROVIDER=ollama                        # Use local Ollama (default, free)
# LLM_PROVIDER=claude                      # Use Anthropic Claude (API, paid)
# ANTHROPIC_API_KEY=your_key_here          # Required if LLM_PROVIDER=claude

# Ollama Configuration (if LLM_PROVIDER=ollama)
OLLAMA_MODEL=qwen2.5:32b
OLLAMA_BASE_URL=http://localhost:11434

# Optional
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379/0
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# Production (for protected endpoints)
ENVIRONMENT=production
METRICS_SECRET=your_secret_here            # Required for /metrics, /health/detailed
ADMIN_TOKEN=your_admin_token_here          # Required for admin source management
```

## Production Deployment

### Security Notes

**Metrics Endpoints** (in production, `ENVIRONMENT=production`):
- `/health/detailed`, `/health/data`, `/health/rag`, `/metrics` require `X-Metrics-Secret` header
- Set `METRICS_SECRET` environment variable
- Secrets are never logged (constant-time comparison used)
- Endpoints return 503 if `METRICS_SECRET` not configured

**Admin Mode** (source management):
- Admin endpoints (`/api/v1/rag/admin/*`) require `X-Admin-Token` header
- Set `ADMIN_TOKEN` environment variable
- Token is sent via header only (never in query parameters - prevents log exposure)
- Frontend stores admin token in localStorage (never in URL)
- Used for enabling/disabling tafseer sources

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only (fast, no external dependencies)
cd backend && pytest -m "unit" -v

# Run acceptance tests
cd backend && pytest tests/test_acceptance.py -v
```

## License

This project respects all source licenses. Quran text is public domain.
Tafseer sources must be verified for license compliance before use.
