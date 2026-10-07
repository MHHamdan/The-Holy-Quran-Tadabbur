# Runbook: Arabic Grammar Analysis (إعراب)

## Overview

The Grammar Analysis feature provides word-by-word grammatical analysis of Quranic verses. This runbook covers debugging, monitoring, and troubleshooting the feature.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │ ──▶ │   Backend   │ ──▶ │ Hugging Face│
│  Grammar UI │     │  /grammar/* │     │  chat model │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Static    │
                    │  Fallback   │
                    └─────────────┘
```

### Components

1. **Frontend (`GrammarAnalysis.tsx`)**: UI component that displays word-by-word analysis
2. **Backend (`/api/v1/grammar/*`)**: FastAPI endpoints for grammar analysis
3. **LLM Service (`grammar_llm.py`)**: LLM-based analysis via Hugging Face Inference Providers
4. **Static Fallback (`grammar_fallback.py`)**: Pre-analyzed data for common verses

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/grammar/analyze` | POST | Analyze arbitrary Arabic text |
| `/api/v1/grammar/ayah/{sura}:{ayah}` | GET | Analyze a specific verse |
| `/api/v1/grammar/labels` | GET | Get valid grammar labels |
| `/api/v1/grammar/health` | GET | Check service health |

## Health Check

```bash
# Check grammar service health
curl -s http://localhost:8000/api/v1/grammar/health | python3 -m json.tool
```

### Health Status Values

| Status | Description |
|--------|-------------|
| `ok` | HF LLM configured, full analysis working |
| `static_only` | Only pre-analyzed verses available |
| `unavailable` | No analysis possible |

## Common Issues

### Issue: "غير محدد / 0%" Cards

**Symptoms:**
- UI shows cards with "غير محدد" labels
- Confidence shows 0%
- Notes show "خدمة التحليل غير متاحة"

**Root Cause:** `HF_TOKEN` missing on the backend, HF quota exhausted, or upstream timeout

**Debug Steps:**

1. Check grammar health (`llm_available` must be `true`):
   ```bash
   curl http://localhost:8000/api/v1/grammar/health
   ```

2. Check backend logs for `Hugging Face chat failed: <kind>`:
   ```bash
   docker logs tadabbur-backend 2>&1 | grep "Hugging Face" | tail -20
   ```
   `auth`/`forbidden` → token invalid or lacks the Inference Providers permission;
   `quota` → credits exhausted or rate limited; `model_unavailable` → change
   `HF_LLM_MODEL` / `HF_LLM_PROVIDER`.

**Solutions:**

1. **Token missing/invalid:** set `HF_TOKEN` in the backend environment and restart.
2. **Quota exhausted:** add HF credits or wait; the static fallback keeps working.
3. **Model unavailable:** pick another model served by HF Inference Providers.

### Issue: Verse Not Found

**Symptoms:**
- API returns 404 for verse analysis
- Error: "لم يتم العثور على الآية"

**Debug Steps:**

1. Check verse exists in database:
   ```bash
   docker exec tadabbur-postgres psql -U tadabbur -d tadabbur \
     -c "SELECT text_uthmani FROM quran_verses WHERE sura_no = 2 AND aya_no = 255;"
   ```

2. Check database connection:
   ```bash
   docker exec tadabbur-postgres pg_isready
   ```

### Issue: Static Fallback Not Working

**Symptoms:**
- Health shows `static_only` but verses still show "غير محدد"

**Debug Steps:**

1. Check static verse availability:
   ```python
   # In Python console
   from app.services.grammar_fallback import get_available_static_verses
   print(get_available_static_verses())
   ```

2. Verify verse is in static data:
   - Static data includes: 1:1, 1:2, 2:255, 112:1, 112:2, 36:1, 55:1, 67:1

## Fallback Strategy

The grammar service uses a 2-tier fallback:

```
1. Primary: LLM analysis (Hugging Face)
   ↓ (if unavailable or timeout)
2. Fallback: Static Morphology Dataset
   ↓ (if verse not in static data)
3. Error: Return "unavailable" source
```

### Static Data Coverage

Currently includes pre-analyzed data for:
- Al-Fatiha (1:1-7)
- Ayat Al-Kursi (2:255)
- Al-Ikhlas (112:1-4)
- Ya-Sin opening (36:1)
- Ar-Rahman opening (55:1)
- Al-Mulk opening (67:1)

To add more verses, edit `app/services/grammar_fallback.py`.

## Monitoring

### Key Metrics

1. **LLM availability**: `grammar_health.llm_available`
2. **Static fallback count**: `grammar_health.static_verse_count`
3. **Source distribution**: Track `source` field in responses

### Log Patterns

```bash
# Find grammar errors
docker logs tadabbur-backend 2>&1 | grep -i "grammar"

# Find timeout issues
docker logs tadabbur-backend 2>&1 | grep -i "timeout"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | — | Hugging Face token (server side only) |
| `HF_LLM_MODEL` | `meta-llama/Llama-3.3-70B-Instruct` | Chat model for grammar analysis |
| `HF_LLM_PROVIDER` | `auto` | HF provider routing |
| `HF_TIMEOUT_SECONDS` | `60` | Request timeout in seconds |

## Quick Health Checks

```bash
# Full grammar system check
echo "1. Backend Health:"
curl -s http://localhost:8000/health

echo ""
echo "2. Grammar Health:"
curl -s http://localhost:8000/api/v1/grammar/health

echo ""
echo "3. Test Grammar Analysis (1:1):"
curl -s http://localhost:8000/api/v1/grammar/ayah/1:1 | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'Source: {d.get(\"source\")}, Tokens: {len(d.get(\"tokens\",[]))}')"
```

## API Response Format

### Success Response

```json
{
  "verse_reference": "1:1",
  "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
  "sentence_type": "شبه جملة",
  "tokens": [
    {
      "word": "بِسْمِ",
      "word_index": 0,
      "pos": "حرف جر",
      "role": "جار ومجرور",
      "case_ending": "كسرة",
      "i3rab": "جار ومجرور، الباء حرف جر...",
      "root": "س م و",
      "pattern": "فعل",
      "confidence": 0.95,
      "notes_ar": "مضاف"
    }
  ],
  "notes_ar": "جملة البسملة...",
  "overall_confidence": 0.95,
  "source": "static"
}
```

### Source Values

| Source | Description |
|--------|-------------|
| `llm` | Analyzed by the Hugging Face LLM |
| `static` | Pre-analyzed static data |
| `hybrid` | Combination of LLM + corpus |
| `unavailable` | Service unavailable |
| `error` | Analysis failed |
| `timeout` | Request timed out |

## Admin Verification Workflow

Grammar corrections must go through admin verification before being applied.

### Verification Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/grammar/verification/submit` | POST | Public | Submit correction |
| `/api/v1/grammar/verification/tasks` | GET | Admin | List pending tasks |
| `/api/v1/grammar/verification/tasks/{id}/decide` | POST | Admin | Approve/reject |
| `/api/v1/grammar/verification/stats` | GET | Admin | View statistics |

### Submit a Correction

```bash
curl -X POST http://localhost:8000/api/v1/grammar/verification/submit \
  -H "Content-Type: application/json" \
  -d '{
    "verse_reference": "1:1",
    "word_index": 0,
    "word": "بِسْمِ",
    "proposed_pos": "حرف جر",
    "proposed_role": "جار ومجرور",
    "notes": "تصحيح نحوي"
  }'
```

### Admin: List Pending Tasks

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/grammar/verification/tasks?status=pending
```

### Admin: Approve/Reject Task

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/grammar/verification/tasks/123/decide \
  -d '{"decision": "approved", "notes": "Verified by scholar"}'
```

### Verification Status Flow

```
pending → approved → (applied to static dataset)
pending → rejected → (logged, no changes)
```

## Testing

### Run Unit Tests

```bash
cd /home/mhamdan/tadabbur/backend
PYTHONPATH=. python -m pytest tests/unit/test_grammar_fallback.py -v
PYTHONPATH=. python -m pytest tests/integration/test_grammar.py -v
```

### Run E2E Tests

```bash
cd /home/mhamdan/tadabbur/frontend
npx playwright test tests/grammar.spec.ts
```

## Database Migration

The verification workflow requires tables `verification_tasks` and `verification_decisions`.

```bash
cd /home/mhamdan/tadabbur/backend
alembic upgrade head
```

## Contact

For unresolved issues:
1. Capture the request_id from X-Request-Id header
2. Check backend logs with the request_id
3. Include grammar health output (never paste HF_TOKEN)
