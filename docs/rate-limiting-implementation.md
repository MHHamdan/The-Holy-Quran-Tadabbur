# Rate Limiting Implementation

**Platform:** Tadabbur Al-Quran  
**Implemented:** Phase S (2026-05-07)  
**Module:** `backend/app/core/rate_limit.py`

---

## Overview

Rate limiting prevents abuse of compute-intensive and write endpoints. The implementation is:

- **Algorithm:** Sliding window (per client IP)
- **Scope:** Per-process, in-memory
- **Thread-safety:** Yes (`threading.Lock`)
- **Response:** HTTP 429 with `Retry-After` header and bilingual message

---

## Endpoint Limits

| Endpoint | Dependency | Limit | Rationale |
|---|---|---|---|
| `POST /api/v1/rag/ask` | `rag_rate_limit` | 20/min | LLM call — expensive, abuse-prone |
| `POST /api/v1/rag/ask/followup` | `rag_rate_limit` | 20/min | LLM call |
| `POST /api/v1/rag/ask/expand` | `rag_rate_limit` | 20/min | LLM call |
| `POST /api/v1/admin/review/tasks/{id}/decision` | `admin_decision_rate_limit` | 10/min | Write operation, Quran-sensitive |
| `GET /api/v1/vocabulary/lookup` | `vocab_rate_limit` | 60/min | Safe-refusal, lenient |
| `GET /api/v1/quran/resolve` | (inline) | 30/min | Pre-existing |

`search_rate_limit` (60/min) is exported but not yet applied to search endpoints.

---

## Client IP Detection

The `_get_client_ip()` helper extracts the real client IP:

1. If `X-Forwarded-For` is present, take the leftmost (original client) IP
2. Otherwise, use `request.client.host`
3. Fall back to `"unknown"` if no client info

**Security note:** Only trust `X-Forwarded-For` if the deployment is behind a verified trusted proxy (nginx, AWS ALB, Cloudflare). A malicious client can spoof this header if the proxy doesn't strip/rewrite it.

---

## HTTP 429 Response Format

```json
{
  "detail": {
    "error": "rate_limited",
    "message_en": "Too many requests. Please wait before trying again. Retry after 60 seconds.",
    "message_ar": "تم تجاوز حد الطلبات المسموح به. يرجى الانتظار 60 ثانية ثم المحاولة مجدداً.",
    "retry_after_seconds": 60
  }
}
```

Response headers include:
```
Retry-After: 60
```

---

## Using in Tests

**Override for unit tests** (prevents rate limit interference in existing tests):

```python
from app.core.rate_limit import rag_rate_limit
from app.main import app

# Install a no-op override (no rate limiting in this test)
async def no_limit():
    pass

app.dependency_overrides[rag_rate_limit] = no_limit

# ... run tests ...

app.dependency_overrides.pop(rag_rate_limit, None)
```

**Override with tight limit for rate limiting tests:**

```python
from app.core.rate_limit import InMemoryRateLimiter, rag_rate_limit
from fastapi import HTTPException

tight = InMemoryRateLimiter(max_requests=2, window_seconds=60)

async def tight_limit():
    allowed, _ = tight.is_allowed("test-ip")
    if not allowed:
        raise HTTPException(status_code=429, detail={"error": "rate_limited"})

app.dependency_overrides[rag_rate_limit] = tight_limit
```

**Important:** Override functions must be parameterless (or have FastAPI-typed parameters) to avoid FastAPI treating parameters as query params.

---

## Production Upgrade Path

The current implementation is single-process only. For production:

### Option 1: Redis + fastapi-limiter

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

@app.on_event("startup")
async def startup():
    r = redis.from_url(settings.redis_url)
    await FastAPILimiter.init(r)

@router.post("/rag/ask")
async def ask(
    _: None = Depends(RateLimiter(times=20, seconds=60))
):
    ...
```

### Option 2: Gateway-level rate limiting

- **AWS API Gateway**: Throttling settings per route (requests/sec, burst)
- **Cloudflare**: Rate Limiting rules by path + IP
- **nginx**: `limit_req_zone` + `limit_req` directives

Gateway-level is preferred for production because it's enforced before requests reach the application server, protecting against connection exhaustion.

---

## Monitoring

Rate limit events are logged:
```
WARNING  app.core.rate_limit - RAG rate limit exceeded for IP 203.0.113.7
WARNING  app.core.rate_limit - Admin decision rate limit exceeded for IP 203.0.113.7
```

For production alerting, create a log-based metric on `"rate limit exceeded"` and alert when the count exceeds a threshold (e.g., >100 events/5min from a single IP suggests active abuse).
