# Runbook: Debugging Empty Pages in Tadabbur

## Overview

This runbook helps debug issues where pages show empty data or navigation fails.

## Prerequisites

- Access to browser developer tools
- Access to backend logs (`docker logs tadabbur-backend`)
- Admin token for verification endpoints (if needed)

## Step 1: Get the Request ID

Every API response includes a `request_id` in:
- Response headers: `X-Request-Id`
- Error response body: `error.request_id`

**In Browser:**
1. Open Developer Tools (F12)
2. Go to Network tab
3. Find the failed API request
4. Look for `X-Request-Id` header or in response body

**Using ErrorPanel:**
The ErrorPanel component displays the request_id and has a "Copy Diagnostics" button.

## Step 2: Check Backend Logs

```bash
# Get recent logs
docker logs tadabbur-backend --tail 100 2>&1 | grep <request_id>

# Get all logs for the request
docker logs tadabbur-backend 2>&1 | grep -A 5 <request_id>
```

Log format:
```
[<request_id>] <METHOD> <PATH> -> <STATUS> (<time>s)
```

## Step 3: Common Issues and Solutions

### Issue: Concepts Page Empty

**Symptoms:**
- `/concepts` shows no data
- API returns `{"concepts": [], "total": 0}`

**Debug Steps:**
1. Check database:
   ```bash
   docker exec tadabbur-postgres psql -U tadabbur -d tadabbur \
     -c "SELECT COUNT(*) FROM concepts;"
   ```

2. Check API response:
   ```bash
   curl -s http://localhost:8000/api/v1/concepts | python3 -m json.tool
   ```

3. If database has data but API returns empty, check for:
   - Filter parameters in the request
   - Database connection issues

### Issue: Miracles Page Empty

**Symptoms:**
- `/miracles` shows no data
- API returns empty array

**Debug Steps:**
1. Check miracles in database:
   ```bash
   docker exec tadabbur-postgres psql -U tadabbur -d tadabbur \
     -c "SELECT id, label_en FROM concepts WHERE concept_type = 'miracle';"
   ```

2. Check API:
   ```bash
   curl -s http://localhost:8000/api/v1/concepts/miracles/all | python3 -m json.tool
   ```

3. Check associations:
   ```bash
   docker exec tadabbur-postgres psql -U tadabbur -d tadabbur \
     -c "SELECT * FROM associations WHERE concept_a_id LIKE 'miracle_%';"
   ```

### Issue: Concept Detail 404

**Symptoms:**
- Clicking concept navigates to `/concepts/<id>`
- Page shows "Concept not found"

**Debug Steps:**
1. Verify concept ID exists:
   ```bash
   curl -s http://localhost:8000/api/v1/concepts/<concept_id> | python3 -m json.tool
   ```

2. Check the error response includes request_id
3. Look up request_id in backend logs

### Issue: "Random Quran Page" Navigation

**Root Cause:** Links pointing to non-existent concept IDs

**Solution Applied:**
- Miracles page now links to related prophet instead of miracle ID
- File: `frontend/src/pages/MiraclesPage.tsx:329-337`

### Issue: Arabic Mode Shows English Tags

**Debug Steps:**
1. Check localStorage for language setting:
   ```javascript
   // In browser console
   localStorage.getItem('language')
   ```

2. Verify component uses correct language prop

## Step 4: Error Response Format

All errors follow this format:
```json
{
  "ok": false,
  "error": {
    "code": "concept_not_found",
    "message": "Concept 'xyz' not found",
    "message_ar": "المفهوم 'xyz' غير موجود",
    "request_id": "abc-123-def"
  },
  "request_id": "abc-123-def"
}
```

Error codes:
- `concept_not_found`: Concept ID doesn't exist
- `occurrence_not_found`: Occurrence ID invalid
- `unauthorized`: Missing or invalid Bearer token
- `validation_error`: Request validation failed
- `internal_error`: Server error (check logs)

## Step 5: Admin Verification Tasks

If content is missing or incorrect, create a verification task:

```bash
# Create task (public endpoint)
curl -X POST http://localhost:8000/api/v1/concepts/verification/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "concept",
    "entity_id": "<concept_id>",
    "proposed_change": {"action": "investigate_missing_data"},
    "priority": 5
  }'

# Check pending tasks (admin only)
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/v1/concepts/verification/tasks?status=pending
```

## Step 6: Quick Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database connection
docker exec tadabbur-postgres pg_isready

# Concepts count
curl -s http://localhost:8000/api/v1/concepts | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'Concepts: {d[\"total\"]}')"

# Miracles count
curl -s http://localhost:8000/api/v1/concepts/miracles/all | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'Miracles: {len(d)}')"
```

## Contact

For unresolved issues:
1. Capture the request_id
2. Note the exact steps to reproduce
3. Include browser console errors
4. Check if issue is consistent across browsers
