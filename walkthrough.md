> **HISTORICAL (pre-Hugging Face migration).** This page records the original
> owner-workstation setup (local GPUs, Anthropic API key). It is not current:
> all AI now runs on Hugging Face Inference Providers with `HF_TOKEN` on the
> backend, and no GPU is required. See README.md.

# Tadabbur-AI Project Context for Claude Code

## Project Overview

**Tadabbur-AI** is a RAG-grounded Quranic knowledge platform with story connections. It provides:
- Semantic search across Quran verses and Tafseer (exegesis)
- Story connections linking related narratives across suras
- Grounded responses with citations using Claude AI

## Current State (January 3, 2026)

### Completed
- [x] Docker Compose configuration with healthchecks (postgres, qdrant, redis)
- [x] Quran data downloaded and seeded (6,236 verses from api.alquran.cloud)
- [x] Stories seeded (25 stories, 129 segments)
- [x] Database migrations configured (Alembic)
- [x] Indexing scripts updated with CPU/GPU mode support
- [x] Makefile with auto-detection of docker compose V1/V2

### In Progress
- [ ] Tafseer data download and indexing
- [ ] Production indexing on GPU (lytos server)

### Pending
- [ ] RAG pipeline verification
- [ ] API endpoint testing
- [ ] Frontend integration

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TADABBUR-AI STACK                     │
├─────────────────────────────────────────────────────────┤
│  Frontend:  React + Vite (port 3000)                    │
│  Backend:   FastAPI + Uvicorn (port 8000)               │
│  Database:  PostgreSQL 15 (port 5432)                   │
│  Vector DB: Qdrant 1.7.4 (port 6333)                    │
│  Cache:     Redis 7 (port 6379)                         │
│  Queue:     RQ Worker (background tasks)                │
└─────────────────────────────────────────────────────────┘
```

## Key Directories

```
tadabbur/
├── backend/
│   ├── app/                    # FastAPI application
│   │   ├── api/routes/         # API endpoints
│   │   ├── core/               # Config, settings
│   │   ├── db/                 # Database connection
│   │   ├── models/             # SQLAlchemy models
│   │   ├── rag/                # RAG pipeline
│   │   └── services/           # Business logic
│   ├── scripts/
│   │   ├── datasets/           # Data download scripts
│   │   │   ├── download_quran.py
│   │   │   └── download_tafseer.py
│   │   ├── ingest/             # Data seeding scripts
│   │   │   ├── seed_quran.py
│   │   │   └── seed_tafseer.py
│   │   ├── index/              # Vector indexing
│   │   │   └── index_tafseer.py
│   │   └── verify/             # Verification scripts
│   ├── alembic/                # Database migrations
│   └── pyproject.toml          # Python dependencies
├── frontend/                   # React frontend
├── data/
│   ├── manifests/              # Data source manifests
│   └── raw/                    # Downloaded raw data
├── assets/
│   └── hafs_smart_v8.json      # Quran text (6,236 verses)
├── docker-compose.yml          # Docker services
└── Makefile                    # Build commands
```

## Environment Setup on Lytos

### Known Issue: Docker Compose V1 vs V2

Lytos may have older Docker. Check and fix:

```bash
# Check docker compose version
docker --version
docker compose version  # V2 (preferred)
docker-compose --version  # V1 (legacy)

# If only V1 is available, use docker-compose instead of docker compose
docker-compose up -d postgres qdrant redis
```

### Python Environment

```bash
cd ~/tadabbur
python3 -m venv .venv
source .venv/bin/activate
cd backend && pip install -e .
```

### GPU Configuration (4x RTX 2080Ti)

Lytos has 4x RTX 2080Ti with 11GB VRAM each. For optimal GPU usage:

```bash
# Check GPU status
nvidia-smi

# For multi-GPU embedding (if needed)
export CUDA_VISIBLE_DEVICES=0,1,2,3
```

## Key Commands

### Service Management

```bash
# Start services (use docker-compose if V2 not available)
docker compose up -d postgres qdrant redis
# OR
docker-compose up -d postgres qdrant redis

# Check status
docker compose ps
# OR
docker-compose ps

# View logs
docker compose logs -f qdrant
```

### Data Pipeline

```bash
# Download tafseer data
make download-tafseer

# Seed database
make seed-quran
make seed-stories

# Index vectors (GPU mode - best for lytos)
make index-gpu

# Index vectors (CPU mode - fallback)
make index-cpu
```

### Verification

```bash
make verify-services    # Check all services healthy
make verify-db          # Check database seeded
make verify-qdrant      # Check vector index
```

## Embedding Models

| Model | Dimensions | Size | Use Case |
|-------|------------|------|----------|
| intfloat/multilingual-e5-small | 384 | ~500MB | Fast dev/testing |
| intfloat/multilingual-e5-base | 768 | ~1.1GB | Balanced |
| intfloat/multilingual-e5-large | 1024 | ~2.2GB | Production (GPU) |

Environment variables:
```bash
export EMBEDDING_MODEL=intfloat/multilingual-e5-large
export EMBEDDING_DEVICE=cuda  # or cpu
```

## Immediate Next Steps on Lytos

1. **Fix Docker Compose** - Use V1 syntax if V2 not available
2. **Start Services** - postgres, qdrant, redis
3. **Download Tafseer** - `make download-tafseer`
4. **Run GPU Indexing** - `make index-gpu` (uses RTX 2080Ti)
5. **Verify Pipeline** - `make verify`

## Troubleshooting

### Docker Compose Not Found
```bash
# Install docker-compose V1 as fallback
sudo apt-get install docker-compose

# Or install Docker Compose V2 plugin
sudo apt-get install docker-compose-plugin
```

### CUDA/GPU Issues
```bash
# Check CUDA
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# Force CPU if GPU issues
export EMBEDDING_DEVICE=cpu
```

### Qdrant Connection Issues
```bash
# Check Qdrant is running
curl http://localhost:6333/healthz

# Check container logs
docker logs tadabbur-qdrant
```

## API Keys Required

For full RAG functionality:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Contact/Notes

- Local dev machine: synchro055059 (Quadro P400, 2GB - use CPU mode)
- Production server: lytos (4x RTX 2080Ti, 44GB total - use GPU mode)
- Target deployment: Lightweight mobile app with server-side RAG
