# Quran Topic Relation Graph — Build Summary

Generated at: 2026-05-17T12:57:01.386Z
Version: 1.0.0

## Totals

- Nodes: **3437**
- Edges: **8130**

## Nodes by type

| Type | Count |
|---|---:|
| ayah | 3246 |
| surah | 114 |
| topic | 70 |
| emotion | 7 |

## Edges by type

| Type | Count |
|---|---:|
| TOPIC_IN_AYAH | 5307 |
| TOPIC_IN_SURAH | 1576 |
| SEMANTIC_CLUSTER | 990 |
| SHARED_AYAH | 123 |
| TOPIC_RELATED_TO_TOPIC | 123 |
| TOPIC_RELATED_TO_EMOTION | 11 |

## Warnings

- All edges default to needs_review.
- Topic↔Topic SHARED_AYAH edges are observational; reviewers may collapse near-duplicates.
- SEMANTIC_CLUSTER edges derive from graph_community clusters and inherit their needs_review status.