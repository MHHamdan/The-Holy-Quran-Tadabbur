#!/usr/bin/env python3
"""
Fetch five Arabic tafsir works from the Hugging Face dataset
``riotu-lab/Quran-Tafseers`` (Apache-2.0) and write them as
``data/raw/<source_id>.json`` for ``scripts/ingest/seed_tafseer.py``.

This is the reproducible tafsir input path: the dataset revision is pinned,
the downloaded file's SHA-256 is verified against the pinned value, and each
output gets a ``<source_id>.provenance.json`` sidecar that the seeder records
in the audit log instead of the CDN URL.

Works produced (verse-anchored, Arabic):
    muyassar_ar     التفسير الميسر   (modern, King Fahd Complex — see licence note)
    ibn_kathir_ar   تفسير ابن كثير   (classical)
    tabari_ar       تفسير الطبري     (classical)
    qurtubi_ar      تفسير القرطبي    (classical)
    baghawi_ar      تفسير البغوي     (classical)

Licence note: the dataset is Apache-2.0 and the four classical works are public
domain by age. Al-Muyassar is a modern work of the King Fahd Complex; the
repository's source manifest marks its licence as pending verification. Pass
``--exclude muyassar_ar`` until the owner has confirmed it may be used.

Usage:
    python scripts/datasets/fetch_hf_tafseers.py [--exclude muyassar_ar] [--out ../data/raw]
Downloads go through huggingface_hub (public dataset; no token required).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

DATASET = "riotu-lab/Quran-Tafseers"
REVISION = "9ddbdeec22bfabd9821b14c6584ad9587ed7bffa"  # pinned dataset commit
FILENAME = "Tafseer.json"
DATASET_LICENSE = "apache-2.0"
# SHA-256 of Tafseer.json at REVISION (verified 2026-10-06). Change both together.
EXPECTED_SHA256 = "0e4172d4a80f662363029b291b186ab7228e55d6786b9ec1a8dde7a4aa0ce878"
WORKS = {
    "التفسير الميسر": "muyassar_ar",
    "تفسير ابن كثير": "ibn_kathir_ar",
    "تفسير الطبري": "tabari_ar",
    "تفسير القرطبي": "qurtubi_ar",
    "تفسير البغوي": "baghawi_ar",
}
REPO_ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "raw")
    ap.add_argument("--exclude", nargs="*", default=[], help="source ids to skip")
    ap.add_argument("--expect-sha256", default=EXPECTED_SHA256, help="expected SHA-256 of the download")
    args = ap.parse_args()

    from huggingface_hub import hf_hub_download

    path = Path(hf_hub_download(DATASET, FILENAME, repo_type="dataset", revision=REVISION))
    digest = sha256(path)
    print(f"{DATASET}@{REVISION[:12]}/{FILENAME}: sha256 {digest}")
    if digest != args.expect_sha256:
        print("SHA-256 mismatch; refusing to continue", file=sys.stderr)
        return 1

    rows = json.loads(path.read_text(encoding="utf-8"))
    out = {sid: [] for name, sid in WORKS.items() if sid not in args.exclude}
    for r in rows:
        sid = WORKS.get(r.get("tafsir_name"))
        text = (r.get("tafsir") or "").strip()
        if sid in out and text:
            out[sid].append({"surah": int(r["sura_number"]), "ayah": int(r["ayah_number"]), "text": text})

    args.out.mkdir(parents=True, exist_ok=True)
    for sid, items in out.items():
        items.sort(key=lambda x: (x["surah"], x["ayah"]))
        (args.out / f"{sid}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        (args.out / f"{sid}.provenance.json").write_text(json.dumps({
            "dataset": DATASET,
            "dataset_license": DATASET_LICENSE,
            "revision": REVISION,
            "file": FILENAME,
            "file_sha256": digest,
            "source_url": f"https://huggingface.co/datasets/{DATASET}/blob/{REVISION}/{FILENAME}",
            "entries": len(items),
        }, indent=2), encoding="utf-8")
        print(f"  {sid}: {len(items)} verse entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
