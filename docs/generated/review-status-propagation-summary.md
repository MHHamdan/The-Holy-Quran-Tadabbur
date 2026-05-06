# Review Status Propagation Summary
_Generated: 2026-05-06T04:51:27.779Z_

## Overview

| Metric | Count |
|---|---|
| Total review tasks | 914 |
| Pending (omitted from overlay) | 914 |
| Approved | 0 |
| Rejected | 0 |
| Changes Requested | 0 |
| Partially Reviewed (compound) | 0 |
| Invalid / fallback to needs_review | 0 |

## Overlay Entries by Content Type

| Content Type | Entries in Overlay |
|---|---|
| story_segment | 0 |
| related_story | 0 |
| kg_relation | 0 |
| source_evidence | 0 |
| disagreement_note | 0 |
| **Total** | **0** |

## Safety Notes

- No Quran text is embedded in overlay entries — only review metadata
- All approved entries required: reviewerId, reviewedAt, notes ≥ 10 chars
- Rejected entries are never marked approved
- Pending tasks omitted — frontend defaults to needs_review for all missing entries
- Compound rule enforced: story_segment approved only if disagreement_note and source_evidence also approved (where applicable)

## Overlay File

Output: `frontend/src/data/generated/reviewStatusOverlay.json`

To regenerate after new decisions: `npx tsx scripts/propagate-review-status.ts`
Then run: `npx tsx scripts/validate-review-status-overlay.ts`
