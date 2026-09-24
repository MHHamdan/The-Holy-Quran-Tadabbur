#!/usr/bin/env python3
"""Verify an unpacked Tadabbur data bundle against its BUNDLE.json manifest.

Usage: verify_bundle.py UNPACKED_DIR

Exits 0 when every member is present and its SHA-256 matches, 1 otherwise.
Shared by restore_bundle.sh and `make bundle-verify` so the integrity rule
lives in exactly one place.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    stage = Path(argv[1])
    manifest_path = stage / "BUNDLE.json"
    if not manifest_path.is_file():
        print("  BUNDLE.json missing — not a Tadabbur bundle", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())
    problems: list[str] = []
    for rel, meta in manifest["members"].items():
        member = stage / rel
        if not member.is_file():
            problems.append(f"{rel}: missing")
        elif sha256(member) != meta["sha256"]:
            problems.append(f"{rel}: checksum mismatch")

    if problems:
        print("  CORRUPT BUNDLE:", *problems, sep="\n    ", file=sys.stderr)
        return 1

    counts = manifest.get("counts", {})
    print(
        f"  {len(manifest['members'])} members OK — "
        f"bundle {manifest['bundle_version']}, "
        f"alembic {manifest['alembic_revision']}, "
        f"{counts.get('postgres_rows', 0):,} rows, "
        f"{counts.get('qdrant_points', 0):,} vectors, "
        f"{counts.get('surreal_statements', 0):,} KG statements"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
