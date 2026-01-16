#!/usr/bin/env python3
"""
Registry Expansion Pipeline - Propose new story entries for missing suras.

PR4: Systematically expands registry coverage from 35 → 50 → 80 → 114 suras.

METHODOLOGY:
============
1. Identify missing suras (not covered by any story)
2. For each missing sura, detect narrative signals
3. Generate draft story entries for human review
4. Output to staging file for approval before promotion

OUTPUT:
=======
- data/registry/stories_staging.json - draft entries for review
- reports/expansion/candidates_{date}.md - Markdown report

Usage:
    python scripts/verify/expansion_pipeline.py [--dry-run] [--verbose]
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple
from dataclasses import dataclass

# Quran surah metadata (name_ar, ayah_count)
SURAH_METADATA = {
    1: ("الفاتحة", 7), 2: ("البقرة", 286), 3: ("آل عمران", 200), 4: ("النساء", 176),
    5: ("المائدة", 120), 6: ("الأنعام", 165), 7: ("الأعراف", 206), 8: ("الأنفال", 75),
    9: ("التوبة", 129), 10: ("يونس", 109), 11: ("هود", 123), 12: ("يوسف", 111),
    13: ("الرعد", 43), 14: ("إبراهيم", 52), 15: ("الحجر", 99), 16: ("النحل", 128),
    17: ("الإسراء", 111), 18: ("الكهف", 110), 19: ("مريم", 98), 20: ("طه", 135),
    21: ("الأنبياء", 112), 22: ("الحج", 78), 23: ("المؤمنون", 118), 24: ("النور", 64),
    25: ("الفرقان", 77), 26: ("الشعراء", 227), 27: ("النمل", 93), 28: ("القصص", 88),
    29: ("العنكبوت", 69), 30: ("الروم", 60), 31: ("لقمان", 34), 32: ("السجدة", 30),
    33: ("الأحزاب", 73), 34: ("سبأ", 54), 35: ("فاطر", 45), 36: ("يس", 83),
    37: ("الصافات", 182), 38: ("ص", 88), 39: ("الزمر", 75), 40: ("غافر", 85),
    41: ("فصلت", 54), 42: ("الشورى", 53), 43: ("الزخرف", 89), 44: ("الدخان", 59),
    45: ("الجاثية", 37), 46: ("الأحقاف", 35), 47: ("محمد", 38), 48: ("الفتح", 29),
    49: ("الحجرات", 18), 50: ("ق", 45), 51: ("الذاريات", 60), 52: ("الطور", 49),
    53: ("النجم", 62), 54: ("القمر", 55), 55: ("الرحمن", 78), 56: ("الواقعة", 96),
    57: ("الحديد", 29), 58: ("المجادلة", 22), 59: ("الحشر", 24), 60: ("الممتحنة", 13),
    61: ("الصف", 14), 62: ("الجمعة", 11), 63: ("المنافقون", 11), 64: ("التغابن", 18),
    65: ("الطلاق", 12), 66: ("التحريم", 12), 67: ("الملك", 30), 68: ("القلم", 52),
    69: ("الحاقة", 52), 70: ("المعارج", 44), 71: ("نوح", 28), 72: ("الجن", 28),
    73: ("المزمل", 20), 74: ("المدثر", 56), 75: ("القيامة", 40), 76: ("الإنسان", 31),
    77: ("المرسلات", 50), 78: ("النبأ", 40), 79: ("النازعات", 46), 80: ("عبس", 42),
    81: ("التكوير", 29), 82: ("الانفطار", 19), 83: ("المطففين", 36), 84: ("الانشقاق", 25),
    85: ("البروج", 22), 86: ("الطارق", 17), 87: ("الأعلى", 19), 88: ("الغاشية", 26),
    89: ("الفجر", 30), 90: ("البلد", 20), 91: ("الشمس", 15), 92: ("الليل", 21),
    93: ("الضحى", 11), 94: ("الشرح", 8), 95: ("التين", 8), 96: ("العلق", 19),
    97: ("القدر", 5), 98: ("البينة", 8), 99: ("الزلزلة", 8), 100: ("العاديات", 11),
    101: ("القارعة", 11), 102: ("التكاثر", 8), 103: ("العصر", 3), 104: ("الهمزة", 9),
    105: ("الفيل", 5), 106: ("قريش", 4), 107: ("الماعون", 7), 108: ("الكوثر", 3),
    109: ("الكافرون", 6), 110: ("النصر", 3), 111: ("المسد", 5), 112: ("الإخلاص", 4),
    113: ("الفلق", 5), 114: ("الناس", 6),
}

# Known narrative suras with proposed stories
# This is curated based on Quran scholarship - not guessing
NARRATIVE_PROPOSALS = {
    33: {
        "title_ar": "غزوة الأحزاب",
        "title_en": "Battle of the Confederates",
        "category": "historical",
        "ayah_range": (9, 27),
        "confidence": 0.8,
    },
    34: {
        "title_ar": "قصة سبأ",
        "title_en": "Story of Sheba",
        "category": "nation",
        "ayah_range": (15, 21),
        "confidence": 0.8,
    },
    36: {
        "title_ar": "أصحاب القرية",
        "title_en": "People of the City",
        "category": "parable",
        "ayah_range": (13, 32),
        "confidence": 0.8,
    },
    37: {
        "title_ar": "قصص الأنبياء في الصافات",
        "title_en": "Prophet Stories in As-Saffat",
        "category": "prophet",
        "ayah_range": (75, 148),
        "confidence": 0.7,
    },
    40: {
        "title_ar": "مؤمن آل فرعون",
        "title_en": "The Believer from Pharaoh's People",
        "category": "historical",
        "ayah_range": (28, 45),
        "confidence": 0.9,
    },
    51: {
        "title_ar": "ضيف إبراهيم المكرمين",
        "title_en": "Abraham's Honored Guests",
        "category": "prophet",
        "ayah_range": (24, 37),
        "confidence": 0.8,
    },
    54: {
        "title_ar": "قصص الأمم في القمر",
        "title_en": "Nation Stories in Al-Qamar",
        "category": "nation",
        "ayah_range": (9, 42),
        "confidence": 0.8,
    },
    66: {
        "title_ar": "نساء النبي",
        "title_en": "The Prophet's Wives",
        "category": "historical",
        "ayah_range": (1, 5),
        "confidence": 0.7,
    },
    79: {
        "title_ar": "موسى في النازعات",
        "title_en": "Moses in An-Nazi'at",
        "category": "prophet",
        "ayah_range": (15, 26),
        "confidence": 0.8,
    },
    85: {
        "title_ar": "أصحاب الأخدود",
        "title_en": "People of the Trench",
        "category": "historical",
        "ayah_range": (4, 9),
        "confidence": 0.9,
    },
    89: {
        "title_ar": "عاد وثمود في الفجر",
        "title_en": "Aad and Thamud in Al-Fajr",
        "category": "nation",
        "ayah_range": (6, 14),
        "confidence": 0.8,
    },
    91: {
        "title_ar": "ناقة ثمود",
        "title_en": "The She-Camel of Thamud",
        "category": "nation",
        "ayah_range": (11, 15),
        "confidence": 0.9,
    },
}


@dataclass
class CandidateStory:
    """A candidate story entry for review."""
    sura: int
    ayah_start: int
    ayah_end: int
    suggested_category: str
    suggested_id: str
    suggested_title_ar: str
    suggested_title_en: str
    confidence: float
    needs_review: bool = True


def find_manifest() -> Path:
    """Find the stories.json manifest file."""
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json",
        Path(__file__).parent.parent.parent / "data" / "manifests" / "stories.json",
        Path("/home/mhamdan/tadabbur/data/manifests/stories.json"),
    ]
    for path in possible_paths:
        if path.exists():
            return path
    raise FileNotFoundError("Could not find stories.json manifest")


def get_covered_suras(manifest_path: Path) -> Set[int]:
    """Get set of suras already covered by stories."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    covered = set()
    for story in data.get('stories', []):
        for seg in story.get('segments', []):
            covered.add(seg.get('sura_no'))
        covered.update(story.get('suras_mentioned', []))

    return covered


def propose_candidates(
    missing_suras: List[int],
    existing_ids: Set[str]
) -> List[CandidateStory]:
    """Propose candidate stories for missing suras based on scholarship."""
    candidates = []

    for sura in missing_suras:
        if sura in NARRATIVE_PROPOSALS:
            proposal = NARRATIVE_PROPOSALS[sura]
            sura_name = SURAH_METADATA.get(sura, ("Unknown", 0))[0]

            # Generate unique ID
            base_id = f"story_{sura_name.replace(' ', '_').lower()}"
            candidate_id = base_id
            counter = 1
            while candidate_id in existing_ids:
                candidate_id = f"{base_id}_{counter}"
                counter += 1
            existing_ids.add(candidate_id)

            ayah_start, ayah_end = proposal["ayah_range"]
            candidates.append(CandidateStory(
                sura=sura,
                ayah_start=ayah_start,
                ayah_end=ayah_end,
                suggested_category=proposal["category"],
                suggested_id=candidate_id,
                suggested_title_ar=proposal["title_ar"],
                suggested_title_en=proposal["title_en"],
                confidence=proposal["confidence"],
            ))

    return candidates


def generate_staging_manifest(
    candidates: List[CandidateStory],
    output_path: Path
) -> None:
    """Generate staging manifest JSON for review."""
    stories = []

    for c in candidates:
        stories.append({
            "id": c.suggested_id,
            "name_ar": c.suggested_title_ar,
            "name_en": c.suggested_title_en,
            "category": c.suggested_category,
            "summary_ar": f"[مسودة] {c.suggested_title_ar} - يحتاج مراجعة",
            "summary_en": f"[Draft] {c.suggested_title_en} - needs review",
            "main_figures": [],
            "themes": [],
            "suras_mentioned": [c.sura],
            "segments": [
                {
                    "id": f"{c.suggested_id}_seg1",
                    "sura_no": c.sura,
                    "aya_start": c.ayah_start,
                    "aya_end": c.ayah_end,
                    "summary_ar": c.suggested_title_ar,
                    "summary_en": c.suggested_title_en,
                    "narrative_order": 1,
                    "aspect": "narrative",
                }
            ],
            "_staging": {
                "confidence": c.confidence,
                "needs_review": c.needs_review,
                "proposed_at": datetime.utcnow().isoformat(),
            }
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"stories": stories, "version": "staging"}, f, ensure_ascii=False, indent=2)


def generate_markdown_report(
    candidates: List[CandidateStory],
    covered_suras: Set[int],
    missing_suras: List[int],
    output_path: Path
) -> None:
    """Generate Markdown report of expansion candidates."""
    report_lines = [
        "# تقرير توسيع سجل القصص",
        "# Registry Expansion Report",
        "",
        f"**تاريخ التوليد:** {datetime.utcnow().isoformat()}",
        "",
        "## ملخص التغطية | Coverage Summary",
        "",
        f"| المقياس | القيمة |",
        f"|---------|--------|",
        f"| السور المغطاة | {len(covered_suras)}/114 |",
        f"| السور الناقصة | {len(missing_suras)} |",
        f"| المرشحين المقترحين | {len(candidates)} |",
        "",
        "## السور الناقصة | Missing Suras",
        "",
    ]

    for sura in missing_suras[:30]:
        sura_name = SURAH_METADATA.get(sura, ("Unknown", 0))[0]
        has_proposal = "✓" if sura in NARRATIVE_PROPOSALS else ""
        report_lines.append(f"- {sura}. {sura_name} {has_proposal}")

    if len(missing_suras) > 30:
        report_lines.append(f"- ... و {len(missing_suras) - 30} سور أخرى")

    report_lines.extend([
        "",
        "## المرشحين المقترحين | Proposed Candidates",
        "",
    ])

    for c in candidates:
        sura_name = SURAH_METADATA.get(c.sura, ("Unknown", 0))[0]
        report_lines.extend([
            f"### {c.suggested_title_ar} ({c.suggested_title_en})",
            f"- **السورة:** {c.sura} ({sura_name})",
            f"- **الآيات:** {c.ayah_start}-{c.ayah_end}",
            f"- **التصنيف:** {c.suggested_category}",
            f"- **الثقة:** {c.confidence * 100:.0f}%",
            "",
        ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))


def main():
    parser = argparse.ArgumentParser(description='Registry expansion pipeline')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    print("📈 Registry Expansion Pipeline (PR4)")
    print("=" * 50)

    manifest_path = find_manifest()
    print(f"📂 Manifest: {manifest_path}")

    covered_suras = get_covered_suras(manifest_path)
    all_suras = set(range(1, 115))
    missing_suras = sorted(all_suras - covered_suras)

    print(f"📊 Current: {len(covered_suras)}/114 suras ({len(covered_suras)/114*100:.1f}%)")
    print(f"📉 Missing: {len(missing_suras)} suras")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    existing_ids = {s['id'] for s in data.get('stories', [])}

    candidates = propose_candidates(missing_suras, existing_ids)
    print(f"📝 Proposed: {len(candidates)} new stories")

    if args.verbose:
        for c in candidates:
            print(f"  ✓ {c.suggested_id}: {c.suggested_title_ar}")

    if args.dry_run:
        print("\n🔍 Dry run - no files written")
        return 0

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    staging_path = Path("data/registry/stories_staging.json")
    report_path = Path(f"reports/expansion/candidates_{timestamp}.md")

    generate_staging_manifest(candidates, staging_path)
    print(f"✅ Staging: {staging_path}")

    generate_markdown_report(candidates, covered_suras, missing_suras, report_path)
    print(f"✅ Report: {report_path}")

    projected = len(covered_suras) + len(candidates)
    print(f"\n📊 Projected coverage: {projected}/114 suras ({projected/114*100:.1f}%)")

    return 0


if __name__ == '__main__':
    exit(main())
