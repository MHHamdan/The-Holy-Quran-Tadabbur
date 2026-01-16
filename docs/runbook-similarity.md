# Runbook: Similarity Search (صلة الآيات)

## Overview

The Similarity Search feature allows users to find thematically, lexically, and semantically related verses across the Quran. Users can search by verse reference or by typing verse text directly.

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│      Frontend       │ ──▶ │      Backend        │ ──▶ │    PostgreSQL       │
│   SimilarityPage    │     │  /quran/similarity  │     │   quran_verses      │
│   Input Parsing     │     │  /quran/resolve     │     │   verse_concepts    │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

### Components

1. **Frontend (`SimilarityPage.tsx`)**: UI for verse search and results display
2. **Input Parser**: Normalizes Arabic digits, handles surah names, detects text vs reference
3. **Verse Resolver (`/api/v1/quran/resolve`)**: Resolves verse text to sura:aya reference
4. **Similarity API (`/api/v1/quran/similarity/advanced/{sura}/{aya}`)**: Multi-layered similarity search

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/quran/resolve` | GET | Resolve verse text to sura:aya reference |
| `/api/v1/quran/similarity/advanced/{sura}/{aya}` | GET | Advanced multi-layered similarity search |
| `/api/v1/quran/similarity/cross-sura/{sura}/{aya}` | GET | Cross-surah similarity |
| `/api/v1/quran/similarity/theme/{theme}` | GET | Theme-based similarity |
| `/api/v1/quran/similarity/semantic/{sura}/{aya}` | GET | Semantic embedding similarity |

## Input Format Support

The frontend supports multiple input formats:

### Reference Formats
| Format | Example | Result |
|--------|---------|--------|
| Standard colon | `2:255` | 2:255 |
| Space separated | `2 255` | 2:255 |
| Arabic colon | `2،255` | 2:255 |
| Dash/hyphen | `2-255` | 2:255 |
| Arabic digits | `٢:٢٥٥` | 2:255 |

### Surah Name Formats
| Format | Example | Result |
|--------|---------|--------|
| Arabic name | `البقرة 255` | 2:255 |
| With سورة prefix | `سورة البقرة 255` | 2:255 |
| English name | `al-baqarah 255` | 2:255 |
| Case insensitive | `BAQARAH 255` | 2:255 |

### Text Search
| Format | Example | Result |
|--------|---------|--------|
| Verse text | `قل هو الله أحد` | Resolves to 112:1 |
| With diacritics | `بِسْمِ اللَّهِ` | Resolves to 1:1 |
| Partial text | `الله لا إله إلا هو` | Resolves to 2:255 |

## Health Check

```bash
# Check similarity API health
curl -s "http://localhost:8000/api/v1/quran/similarity/advanced/2/255" | python3 -m json.tool | head -20

# Check resolve endpoint
curl -s "http://localhost:8000/api/v1/quran/resolve?text=قل%20هو%20الله%20أحد" | python3 -m json.tool
```

## Common Issues

### Issue: Search Button Does Nothing

**Symptoms:**
- User types in input box, clicks search, nothing happens
- No API request visible in network tab

**Root Cause:** Input not matching any parseable format

**Debug Steps:**

1. Check browser console for errors:
   ```
   Open DevTools → Console tab
   ```

2. Verify input is being parsed:
   - Open React DevTools
   - Check `SimilarityPage` component state for `parseResult`

3. Test input parsing manually:
   ```javascript
   // In browser console
   parseInput("2:255")  // Should return { sura: 2, aya: 255, isTextSearch: false }
   parseInput("البقرة 255")  // Should return { sura: 2, aya: 255, isTextSearch: false }
   ```

**Solutions:**

1. Ensure input format matches supported formats (see table above)
2. For Arabic text, ensure it contains actual Arabic characters (not transliteration)

### Issue: "لم يتم العثور على آية" (Verse Not Found)

**Symptoms:**
- Error message shows verse not found
- Works for some verses but not others

**Debug Steps:**

1. Check verse exists in database:
   ```bash
   docker exec tadabbur-postgres psql -U tadabbur -d tadabbur \
     -c "SELECT sura_no, aya_no, text_uthmani FROM quran_verses WHERE sura_no = 2 AND aya_no = 255;"
   ```

2. Check resolve endpoint directly:
   ```bash
   curl -s "http://localhost:8000/api/v1/quran/resolve?text=your+text+here" | python3 -m json.tool
   ```

3. Verify confidence threshold (default 0.60):
   - If confidence < 0.60, no match is returned
   - Check `match_type` in response for debugging

### Issue: No Similar Verses Found

**Symptoms:**
- Search completes but returns 0 matches
- Or returns very few matches

**Debug Steps:**

1. Check similarity API response:
   ```bash
   curl -s "http://localhost:8000/api/v1/quran/similarity/advanced/2/255?min_score=0.1" | python3 -m json.tool
   ```

2. Lower `min_score` parameter to see more results

3. Check verse has concepts in database:
   ```bash
   docker exec tadabbur-postgres psql -U tadabbur -d tadabbur \
     -c "SELECT * FROM verse_concepts WHERE sura_no = 2 AND aya_no = 255 LIMIT 10;"
   ```

### Issue: Arabic Digits Not Recognized

**Symptoms:**
- Input like `٢:٢٥٥` doesn't work
- Only Latin digits work

**Debug Steps:**

1. Verify normalization function:
   ```javascript
   // In browser console
   normalizeArabicDigits("٢:٢٥٥")  // Should return "2:255"
   ```

2. Check for encoding issues in input

**Solutions:**

1. Frontend should normalize Arabic digits automatically
2. If not working, check browser input encoding

### Issue: Candidate Selection Modal Not Appearing

**Symptoms:**
- Text search shows fuzzy warning but no modal to select candidates
- Short input auto-selects wrong verse

**Debug Steps:**

1. Check resolve API response:
   ```bash
   curl -s "http://localhost:8000/api/v1/quran/resolve?text=بسم%20الله" | python3 -m json.tool
   ```

2. Verify `decision` field in response:
   - `auto`: Modal should NOT appear
   - `needs_user_choice`: Modal SHOULD appear
   - `not_found`: Error message should appear

3. Check browser console for errors in modal rendering

**Solutions:**

1. If `decision` is `needs_user_choice` but no modal appears, check frontend console for errors
2. Verify the `SimilarityPage` component is handling the `candidates` array properly

### Issue: Input Too Short Error

**Symptoms:**
- Error message when entering short Arabic text
- "النص قصير جداً" or "Text is too short" message

**Root Cause:** Minimum input constraint (3 characters after normalization)

**Debug Steps:**

1. Check normalized text length:
   ```bash
   # Input must be >= 3 characters after removing diacritics and whitespace
   curl -s "http://localhost:8000/api/v1/quran/resolve?text=اب"
   # Should return 400 error
   ```

**Solutions:**

1. Inform user to provide longer input text
2. Minimum requirements: 3 characters after normalization
3. For `auto` decision: >= 8 characters AND >= 2 tokens

## Input Constraints

| Constraint | Minimum | Description |
|------------|---------|-------------|
| Input length | 3 chars | After normalization (diacritics removed) |
| Auto decision | 8 chars + 2 tokens | Both required for automatic resolution |
| Candidates | Max 5 | Top 5 candidates returned |

## API Response Format

### Resolve Endpoint

The resolve endpoint returns a `decision` field that determines how the frontend should proceed:

| Decision | Description | Frontend Action |
|----------|-------------|-----------------|
| `auto` | High confidence match, proceed automatically | Use `best_match` directly |
| `needs_user_choice` | Ambiguous match, user should choose | Show candidate selection modal |
| `not_found` | No matching verse found | Show error message |

#### Decision Rules

1. **Exact Match**: If normalized query matches normalized verse exactly → `auto`
2. **Short Input**: If input is < 8 chars OR < 2 tokens → `needs_user_choice` (never auto)
3. **High Confidence**: If confidence >= 0.85 AND margin >= 0.08 → `auto`
4. **Moderate Confidence**: If confidence 0.70-0.85 → `needs_user_choice`
5. **Low Confidence**: If confidence < 0.70 → `not_found`

#### Response Example (auto decision)

```json
{
  "ok": true,
  "data": {
    "decision": "auto",
    "best_match": {
      "surah": 112,
      "ayah": 1,
      "text": "قُلْ هُوَ اللَّهُ أَحَدٌ",
      "confidence": 0.95,
      "match_type": "exact"
    },
    "candidates": [
      {
        "surah": 112,
        "ayah": 1,
        "text": "قُلْ هُوَ اللَّهُ أَحَدٌ",
        "confidence": 0.95,
        "match_type": "exact"
      }
    ],
    "sura_no": 112,
    "aya_no": 1,
    "confidence": 0.95,
    "match_type": "exact"
  },
  "request_id": "abc123"
}
```

#### Response Example (needs_user_choice decision)

```json
{
  "ok": true,
  "data": {
    "decision": "needs_user_choice",
    "best_match": {
      "surah": 1,
      "ayah": 1,
      "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
      "confidence": 0.78,
      "match_type": "fuzzy"
    },
    "candidates": [
      {
        "surah": 1,
        "ayah": 1,
        "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "confidence": 0.78,
        "match_type": "fuzzy"
      },
      {
        "surah": 27,
        "ayah": 30,
        "text": "إِنَّهُ مِن سُلَيْمَانَ وَإِنَّهُ بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "confidence": 0.72,
        "match_type": "partial"
      }
    ],
    "sura_no": 1,
    "aya_no": 1,
    "confidence": 0.78,
    "match_type": "fuzzy"
  },
  "request_id": "abc123"
}
```

#### Response Example (not_found decision)

```json
{
  "ok": true,
  "data": {
    "decision": "not_found",
    "best_match": null,
    "candidates": [],
    "sura_no": null,
    "aya_no": null,
    "confidence": 0.0,
    "match_type": null
  },
  "request_id": "abc123"
}
```

### Similarity Endpoint

```json
{
  "source_verse": {
    "verse_id": 262,
    "sura_no": 2,
    "aya_no": 255,
    "text_uthmani": "...",
    "reference": "2:255"
  },
  "source_themes": ["tawheed", "divine_knowledge"],
  "total_similar": 54,
  "matches": [
    {
      "verse_id": 295,
      "sura_no": 3,
      "aya_no": 2,
      "scores": {
        "jaccard": 0.15,
        "cosine": 0.34,
        "concept_overlap": 0.45,
        "combined": 0.33
      },
      "connection_type": "thematic",
      "connection_strength": "moderate",
      "shared_concepts": ["الله", "التوحيد"]
    }
  ]
}
```

### Error Response

```json
{
  "ok": false,
  "error": {
    "code": "VERSE_NOT_FOUND",
    "message": "Could not find a matching verse",
    "message_ar": "لم يتم العثور على آية مطابقة"
  },
  "request_id": "def456"
}
```

## Monitoring

### Key Metrics

1. **Resolve success rate**: Track 200 vs 404 responses
2. **Decision distribution**: Track auto vs needs_user_choice vs not_found
3. **Confidence distribution**: Monitor `confidence` values
4. **Match type distribution**: Track exact vs fuzzy vs partial
5. **User choice rate**: How often users select non-best candidate

### Log Patterns

```bash
# Find resolve errors
docker logs tadabbur-backend 2>&1 | grep "resolve" | grep -i error

# Track decision distribution
docker logs tadabbur-backend 2>&1 | grep "resolve" | grep -E "decision=(auto|needs_user_choice|not_found)"

# Find similarity search issues
docker logs tadabbur-backend 2>&1 | grep "similarity" | grep -i error

# Check response times
docker logs tadabbur-backend 2>&1 | grep "resolve" | grep -E "took [0-9]+ms"

# Track rate limiting
docker logs tadabbur-backend 2>&1 | grep "resolve" | grep "rate_limit"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SIMILARITY_MIN_SCORE` | `0.25` | Default minimum similarity threshold |
| `RESOLVE_MIN_CONFIDENCE` | `0.60` | Minimum confidence for verse resolution |
| `SIMILARITY_MAX_RESULTS` | `100` | Maximum results per query |

## Testing

### Run Unit Tests

```bash
cd /home/mhamdan/tadabbur/backend
PYTHONPATH=. python -m pytest tests/unit/test_quran_resolve.py -v
```

### Run E2E Tests

```bash
cd /home/mhamdan/tadabbur/frontend
npx playwright test e2e/tests/similarity.spec.ts
```

### Manual API Testing

```bash
# Test resolve endpoint
curl -s "http://localhost:8000/api/v1/quran/resolve?text=قل%20هو%20الله%20أحد" | python3 -m json.tool

# Test similarity with filters
curl -s "http://localhost:8000/api/v1/quran/similarity/advanced/2/255?min_score=0.3&limit=10" | python3 -m json.tool

# Test with Arabic digits (URL encoded)
curl -s "http://localhost:8000/api/v1/quran/resolve?text=%D9%A2:%D9%A2%D9%A5%D9%A5" | python3 -m json.tool
```

## Quick Troubleshooting

```bash
# Full similarity system check
echo "1. Backend Health:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "2. Resolve API Test - Auto Decision (قل هو الله أحد):"
curl -s "http://localhost:8000/api/v1/quran/resolve?text=%D9%82%D9%84%20%D9%87%D9%88%20%D8%A7%D9%84%D9%84%D9%87%20%D8%A3%D8%AD%D8%AF" | python3 -c \
  "import sys,json; d=json.load(sys.stdin)['data']; print(f'Decision: {d.get(\"decision\")} | Match: {d.get(\"best_match\",{}).get(\"surah\")}:{d.get(\"best_match\",{}).get(\"ayah\")} | Confidence: {d.get(\"confidence\")}')"

echo ""
echo "3. Resolve API Test - Ambiguous Input (بسم الله):"
curl -s "http://localhost:8000/api/v1/quran/resolve?text=%D8%A8%D8%B3%D9%85%20%D8%A7%D9%84%D9%84%D9%87" | python3 -c \
  "import sys,json; d=json.load(sys.stdin)['data']; print(f'Decision: {d.get(\"decision\")} | Candidates: {len(d.get(\"candidates\",[]))} | Best: {d.get(\"best_match\",{}).get(\"surah\")}:{d.get(\"best_match\",{}).get(\"ayah\")}')"

echo ""
echo "4. Similarity API Test (2:255):"
curl -s "http://localhost:8000/api/v1/quran/similarity/advanced/2/255?limit=5" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'Found {len(d.get(\"matches\",[]))} matches for {d.get(\"source_verse\",{}).get(\"reference\")}')"

echo ""
echo "5. Resolve API Test - Not Found:"
curl -s "http://localhost:8000/api/v1/quran/resolve?text=random%20english%20text" | python3 -c \
  "import sys,json; d=json.load(sys.stdin)['data']; print(f'Decision: {d.get(\"decision\")} (expected: not_found)')"
```

## Contact

For unresolved issues:
1. Capture the `request_id` from API response
2. Check backend logs with the `request_id`
3. Include input format used and expected behavior
