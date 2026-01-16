"""
Enhanced Cross-School Tafsir Comparison Service

Provides advanced tafsir comparison features across the four Sunni madhabs:
- Detailed methodology comparison between schools
- Footnotes and references from classical works
- Scholar selection within each madhab
- Thematic comparison across tafsir interpretations
- School of thought filtering based on user preferences
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from datetime import datetime


class ComparisonType(Enum):
    """Types of tafsir comparison"""
    VERSE = "verse"  # Compare interpretations of a single verse
    THEME = "theme"  # Compare thematic interpretations across verses
    METHODOLOGY = "methodology"  # Compare methodological approaches
    FIQHI = "fiqhi"  # Compare legal rulings derived


class MethodologyAspect(Enum):
    """Aspects of tafsir methodology to compare"""
    LINGUISTIC = "linguistic"
    THEOLOGICAL = "theological"
    JURISPRUDENTIAL = "jurisprudential"
    HISTORICAL = "historical"
    SPIRITUAL = "spiritual"


@dataclass
class ScholarReference:
    """A reference to a classical scholarly work"""
    scholar_id: str
    work_title: str
    work_title_arabic: str
    volume: Optional[int]
    page: Optional[int]
    chapter: Optional[str]
    quote: Optional[str]
    quote_arabic: Optional[str]


@dataclass
class Footnote:
    """A footnote providing additional context"""
    id: str
    content: str
    content_arabic: Optional[str]
    references: List[ScholarReference]
    footnote_type: str  # explanation, source, disagreement, consensus


@dataclass
class MethodologyAnalysis:
    """Analysis of tafsir methodology"""
    school: str
    approach: str
    key_principles: List[str]
    sources_used: List[str]
    strengths: List[str]
    considerations: List[str]


@dataclass
class ThematicComparison:
    """Comparison of thematic interpretation"""
    theme: str
    theme_arabic: str
    interpretations_by_school: Dict[str, List[Dict[str, Any]]]
    common_understanding: Optional[str]
    points_of_divergence: List[str]
    scholarly_consensus: Optional[str]


class EnhancedTafsirComparisonService:
    """
    Enhanced service for cross-school tafsir comparison.
    Integrates with the base tafsir_service for data.
    """

    def __init__(self):
        self.methodology_descriptions: Dict[str, MethodologyAnalysis] = {}
        self.footnotes_db: Dict[str, List[Footnote]] = {}
        self.thematic_mappings: Dict[str, List[str]] = {}
        self._initialize_methodology_descriptions()
        self._initialize_footnotes()
        self._initialize_thematic_mappings()

    def _initialize_methodology_descriptions(self):
        """Initialize detailed methodology descriptions for each school"""
        self.methodology_descriptions = {
            "hanafi": MethodologyAnalysis(
                school="hanafi",
                approach="Emphasizes reason (ra'y) alongside narration, with strong focus on legal rulings",
                key_principles=[
                    "Extensive use of analogical reasoning (qiyas)",
                    "Consideration of juristic preference (istihsan)",
                    "Priority to widespread practice of Madinah scholars",
                    "Emphasis on practical legal application"
                ],
                sources_used=[
                    "Quran", "Sunnah", "Consensus (Ijma)", "Analogical Reasoning (Qiyas)",
                    "Juristic Preference (Istihsan)", "Custom (Urf)"
                ],
                strengths=[
                    "Comprehensive legal framework",
                    "Flexibility in application",
                    "Strong reasoning methodology"
                ],
                considerations=[
                    "May prioritize legal aspects over linguistic analysis",
                    "Strong emphasis on Hanafi legal positions"
                ]
            ),
            "maliki": MethodologyAnalysis(
                school="maliki",
                approach="Balances narration with the practice of Madinah people, comprehensive legal analysis",
                key_principles=[
                    "Practice of Madinah people as authoritative source",
                    "Consideration of public interest (maslaha)",
                    "Blocking the means to harm (sadd al-dhara'i)",
                    "Strong connection to Prophetic city traditions"
                ],
                sources_used=[
                    "Quran", "Sunnah", "Practice of Madinah", "Consensus (Ijma)",
                    "Analogical Reasoning (Qiyas)", "Public Interest (Maslaha)"
                ],
                strengths=[
                    "Connection to Prophetic city practice",
                    "Practical wisdom approach",
                    "Comprehensive fiqhi analysis"
                ],
                considerations=[
                    "Heavy reliance on Madinah practice",
                    "May differ from other schools on some rulings"
                ]
            ),
            "shafii": MethodologyAnalysis(
                school="shafii",
                approach="Systematic methodology balancing text and reason, emphasis on hadith verification",
                key_principles=[
                    "Systematic usul al-fiqh methodology",
                    "Strong emphasis on authentic hadith",
                    "Clear hierarchy of sources",
                    "Linguistic analysis of Quranic text"
                ],
                sources_used=[
                    "Quran", "Sunnah", "Consensus (Ijma)", "Analogical Reasoning (Qiyas)",
                    "Linguistic Analysis"
                ],
                strengths=[
                    "Rigorous hadith methodology",
                    "Systematic approach",
                    "Excellent linguistic analysis"
                ],
                considerations=[
                    "May be stricter in accepting certain practices",
                    "Strong emphasis on textual evidence"
                ]
            ),
            "hanbali": MethodologyAnalysis(
                school="hanbali",
                approach="Prioritizes textual evidence from Quran and Sunnah, minimizes rational speculation",
                key_principles=[
                    "Strict adherence to Quran and Sunnah texts",
                    "Preference for narrations over reason",
                    "Acceptance of weak hadith over qiyas in some cases",
                    "Emphasis on statements of Companions"
                ],
                sources_used=[
                    "Quran", "Sunnah", "Statements of Companions", "Consensus (Ijma)",
                    "Analogical Reasoning (Qiyas) - limited"
                ],
                strengths=[
                    "Strong textual foundation",
                    "Clear and straightforward rulings",
                    "Preservation of early scholarly opinions"
                ],
                considerations=[
                    "May be seen as more literalist",
                    "Less use of rational speculation"
                ]
            )
        }

    def _initialize_footnotes(self):
        """Initialize scholarly footnotes and references"""
        # Sample footnotes for verses
        self.footnotes_db["1:1"] = [
            Footnote(
                id="fn_1_1_1",
                content="The four schools agree that saying Bismillah before beginning acts of worship and daily activities is recommended (mustahabb).",
                content_arabic="اتفق الفقهاء الأربعة على استحباب البسملة قبل العبادات والأعمال اليومية",
                references=[
                    ScholarReference(
                        scholar_id="qurtubi",
                        work_title="Al-Jami li-Ahkam al-Quran",
                        work_title_arabic="الجامع لأحكام القرآن",
                        volume=1,
                        page=92,
                        chapter="Tafsir al-Basmalah",
                        quote="The scholars are unanimous on its recommendation before all good deeds",
                        quote_arabic="أجمع العلماء على استحبابها قبل كل عمل صالح"
                    ),
                    ScholarReference(
                        scholar_id="ibn_kathir",
                        work_title="Tafsir al-Quran al-Azim",
                        work_title_arabic="تفسير القرآن العظيم",
                        volume=1,
                        page=15,
                        chapter="Introduction to Al-Fatiha",
                        quote="It is established to begin with the name of Allah",
                        quote_arabic="ثبت الابتداء باسم الله"
                    )
                ],
                footnote_type="consensus"
            ),
            Footnote(
                id="fn_1_1_2",
                content="The schools differ on whether Bismillah is a verse of Al-Fatiha. Shafi'i school considers it a verse, while Hanafi and Maliki schools do not.",
                content_arabic="اختلفت المذاهب في كون البسملة آية من الفاتحة. يعتبرها الشافعية آية، بينما لا يعتبرها الحنفية والمالكية",
                references=[
                    ScholarReference(
                        scholar_id="jassas",
                        work_title="Ahkam al-Quran",
                        work_title_arabic="أحكام القرآن",
                        volume=1,
                        page=8,
                        chapter="Bismillah",
                        quote="The Basmalah is not a verse of Al-Fatiha according to our school",
                        quote_arabic="البسملة ليست آية من الفاتحة عندنا"
                    )
                ],
                footnote_type="disagreement"
            ),
            Footnote(
                id="fn_1_1_3",
                content="Al-Rahman and Al-Raheem both derive from the root r-h-m (mercy). Al-Rahman indicates the vastness of mercy encompassing all creation, while Al-Raheem indicates the special mercy for believers.",
                content_arabic="الرحمن والرحيم كلاهما من جذر ر-ح-م. الرحمن يدل على سعة الرحمة الشاملة لكل المخلوقات، بينما الرحيم يدل على الرحمة الخاصة بالمؤمنين",
                references=[
                    ScholarReference(
                        scholar_id="tabari",
                        work_title="Jami al-Bayan",
                        work_title_arabic="جامع البيان",
                        volume=1,
                        page=44,
                        chapter="Al-Rahman Al-Raheem",
                        quote="Al-Rahman is more intensive than Al-Raheem",
                        quote_arabic="الرحمن أشد مبالغة من الرحيم"
                    )
                ],
                footnote_type="explanation"
            )
        ]

        self.footnotes_db["2:255"] = [
            Footnote(
                id="fn_2_255_1",
                content="All four schools agree this is the greatest verse in the Quran, as established by authentic hadith.",
                content_arabic="اتفقت المذاهب الأربعة على أن هذه أعظم آية في القرآن، كما ثبت في الحديث الصحيح",
                references=[
                    ScholarReference(
                        scholar_id="ibn_kathir",
                        work_title="Tafsir al-Quran al-Azim",
                        work_title_arabic="تفسير القرآن العظيم",
                        volume=1,
                        page=310,
                        chapter="Ayat al-Kursi",
                        quote="The Prophet asked Ubayy: Which verse is the greatest? He said: Ayat al-Kursi",
                        quote_arabic="سأل النبي أبياً: أي آية أعظم؟ قال: آية الكرسي"
                    )
                ],
                footnote_type="consensus"
            ),
            Footnote(
                id="fn_2_255_2",
                content="Al-Hayy (Ever-Living) and Al-Qayyum (Self-Subsisting) are considered by many scholars to be part of Allah's greatest name (Ism al-A'zam).",
                content_arabic="الحي القيوم يعتبرهما كثير من العلماء من أسماء الله العظمى",
                references=[
                    ScholarReference(
                        scholar_id="qurtubi",
                        work_title="Al-Jami li-Ahkam al-Quran",
                        work_title_arabic="الجامع لأحكام القرآن",
                        volume=3,
                        page=271,
                        chapter="Ayat al-Kursi",
                        quote="Some scholars said the greatest name is Al-Hayy Al-Qayyum",
                        quote_arabic="قال بعض العلماء إن الاسم الأعظم هو الحي القيوم"
                    )
                ],
                footnote_type="explanation"
            )
        ]

    def _initialize_thematic_mappings(self):
        """Initialize thematic mappings for cross-tafsir comparison"""
        self.thematic_mappings = {
            "mercy": ["1:1", "6:54", "21:107", "39:53"],
            "patience": ["2:153", "2:155", "3:200", "39:10"],
            "justice": ["4:135", "5:8", "16:90"],
            "guidance": ["1:6", "2:2", "6:125"],
            "tawhid": ["112:1", "2:163", "2:255"],
            "prayer": ["2:43", "2:153", "29:45"],
            "forgiveness": ["3:135", "4:110", "39:53"],
            "gratitude": ["14:7", "31:12", "2:152"],
            "trust": ["3:159", "8:2", "65:3"],
            "knowledge": ["96:1", "20:114", "58:11"]
        }

    def compare_verse_across_schools(
            self,
            surah: int,
            ayah: int,
            schools: Optional[List[str]] = None,
            include_footnotes: bool = True,
            include_methodology: bool = True
    ) -> Dict[str, Any]:
        """
        Compare tafsir interpretations of a verse across schools.

        Args:
            surah: Surah number
            ayah: Ayah number
            schools: List of schools to include (default: all four)
            include_footnotes: Include scholarly footnotes
            include_methodology: Include methodology analysis
        """
        from app.services.tafsir_service import tafsir_service

        if schools is None:
            schools = ["hanafi", "maliki", "shafii", "hanbali"]

        verse_key = f"{surah}:{ayah}"

        # Get tafsir entries from base service
        all_entries = tafsir_service.get_tafsir_for_verse(surah, ayah)

        # Filter by requested schools
        entries_by_school: Dict[str, List[Dict]] = {school: [] for school in schools}

        for entry in all_entries:
            school = entry.get("scholar", {}).get("school", "")
            if school in schools:
                entries_by_school[school].append(entry)

        # Build comparison result
        result = {
            "verse": verse_key,
            "surah": surah,
            "ayah": ayah,
            "schools_compared": schools,
            "interpretations_by_school": entries_by_school,
            "total_interpretations": sum(len(v) for v in entries_by_school.values())
        }

        # Add methodology comparison
        if include_methodology:
            result["methodology_comparison"] = {
                school: self._get_methodology_summary(school)
                for school in schools
            }

        # Add footnotes
        if include_footnotes:
            result["footnotes"] = self._get_verse_footnotes(verse_key)

        # Extract common themes and differences
        result["analysis"] = self._analyze_interpretations(entries_by_school)

        return result

    def compare_theme_across_schools(
            self,
            theme: str,
            schools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare how different schools interpret a specific theme.
        """
        from app.services.tafsir_service import tafsir_service

        if schools is None:
            schools = ["hanafi", "maliki", "shafii", "hanbali"]

        # Get verses related to this theme
        theme_verses = self.thematic_mappings.get(theme.lower(), [])

        if not theme_verses:
            return {
                "error": f"Theme '{theme}' not found in thematic mappings",
                "available_themes": list(self.thematic_mappings.keys())
            }

        interpretations_by_school: Dict[str, List[Dict]] = {school: [] for school in schools}

        for verse_key in theme_verses:
            parts = verse_key.split(":")
            if len(parts) == 2:
                surah, ayah = int(parts[0]), int(parts[1])
                entries = tafsir_service.get_tafsir_for_verse(surah, ayah)

                for entry in entries:
                    school = entry.get("scholar", {}).get("school", "")
                    if school in schools:
                        entry["verse_reference"] = verse_key
                        interpretations_by_school[school].append(entry)

        return {
            "theme": theme,
            "verses_analyzed": theme_verses,
            "schools_compared": schools,
            "interpretations_by_school": interpretations_by_school,
            "common_understanding": self._extract_common_understanding(interpretations_by_school),
            "points_of_divergence": self._extract_divergences(interpretations_by_school)
        }

    def get_methodology_comparison(self, schools: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get detailed methodology comparison between schools.
        """
        if schools is None:
            schools = ["hanafi", "maliki", "shafii", "hanbali"]

        comparisons = {}
        for school in schools:
            if school in self.methodology_descriptions:
                methodology = self.methodology_descriptions[school]
                comparisons[school] = {
                    "approach": methodology.approach,
                    "key_principles": methodology.key_principles,
                    "sources_used": methodology.sources_used,
                    "strengths": methodology.strengths,
                    "considerations": methodology.considerations
                }

        return {
            "schools": schools,
            "methodology_comparison": comparisons,
            "summary": self._generate_methodology_summary(comparisons)
        }

    def get_scholar_selection_by_madhab(self, madhab: str) -> Dict[str, Any]:
        """
        Get available scholars within a specific madhab for selection.
        """
        from app.services.tafsir_service import tafsir_service

        scholars = tafsir_service.get_scholars_by_school(madhab)

        return {
            "madhab": madhab,
            "scholars": scholars,
            "total": len(scholars),
            "methodology": self.methodology_descriptions.get(madhab.lower())
        }

    def get_verse_with_references(self, surah: int, ayah: int) -> Dict[str, Any]:
        """
        Get verse interpretation with detailed scholarly references.
        """
        from app.services.tafsir_service import tafsir_service

        verse_key = f"{surah}:{ayah}"
        entries = tafsir_service.get_tafsir_for_verse(surah, ayah)
        footnotes = self._get_verse_footnotes(verse_key)

        # Organize by school
        by_school = {}
        for entry in entries:
            school = entry.get("scholar", {}).get("school", "")
            if school not in by_school:
                by_school[school] = []
            by_school[school].append(entry)

        return {
            "verse": verse_key,
            "interpretations_by_school": by_school,
            "footnotes": footnotes,
            "scholarly_references": self._extract_references(footnotes),
            "methodology_notes": {
                school: self._get_methodology_summary(school)
                for school in by_school.keys()
            }
        }

    def filter_tafsir_by_preference(
            self,
            surah: int,
            ayah: int,
            preferred_schools: List[str],
            preferred_scholars: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get tafsir filtered by user's school and scholar preferences.
        """
        from app.services.tafsir_service import tafsir_service

        all_entries = tafsir_service.get_tafsir_for_verse(surah, ayah)

        filtered_entries = []
        for entry in all_entries:
            school = entry.get("scholar", {}).get("school", "")
            scholar_id = entry.get("scholar", {}).get("id", "")

            # Check school preference
            if school not in preferred_schools:
                continue

            # Check scholar preference if specified
            if preferred_scholars and scholar_id not in preferred_scholars:
                continue

            filtered_entries.append(entry)

        return {
            "verse": f"{surah}:{ayah}",
            "filters_applied": {
                "schools": preferred_schools,
                "scholars": preferred_scholars
            },
            "results": filtered_entries,
            "total": len(filtered_entries)
        }

    def _get_methodology_summary(self, school: str) -> Dict[str, Any]:
        """Get summary of school's methodology"""
        if school not in self.methodology_descriptions:
            return {"error": f"Methodology not found for {school}"}

        m = self.methodology_descriptions[school]
        return {
            "approach": m.approach,
            "key_principles": m.key_principles[:3],
            "primary_sources": m.sources_used[:4]
        }

    def _get_verse_footnotes(self, verse_key: str) -> List[Dict[str, Any]]:
        """Get footnotes for a verse"""
        footnotes = self.footnotes_db.get(verse_key, [])
        return [
            {
                "id": fn.id,
                "content": fn.content,
                "content_arabic": fn.content_arabic,
                "type": fn.footnote_type,
                "references": [
                    {
                        "scholar": ref.scholar_id,
                        "work": ref.work_title,
                        "work_arabic": ref.work_title_arabic,
                        "location": f"Vol. {ref.volume}, p. {ref.page}" if ref.volume else None,
                        "quote": ref.quote
                    }
                    for ref in fn.references
                ]
            }
            for fn in footnotes
        ]

    def _extract_references(self, footnotes: List[Dict]) -> List[Dict[str, Any]]:
        """Extract all unique references from footnotes"""
        references = []
        seen = set()

        for fn in footnotes:
            for ref in fn.get("references", []):
                key = (ref.get("scholar"), ref.get("work"))
                if key not in seen:
                    seen.add(key)
                    references.append(ref)

        return references

    def _analyze_interpretations(self, entries_by_school: Dict[str, List]) -> Dict[str, Any]:
        """Analyze interpretations to find common themes and differences"""
        all_themes = []
        all_rulings = []

        for school, entries in entries_by_school.items():
            for entry in entries:
                all_themes.extend(entry.get("themes", []))
                all_rulings.extend(entry.get("fiqhi_rulings", []))

        # Find common themes
        from collections import Counter
        theme_counts = Counter(all_themes)
        common_themes = [t for t, c in theme_counts.items() if c > 1]

        return {
            "common_themes": common_themes,
            "total_themes_found": len(set(all_themes)),
            "schools_with_fiqhi_rulings": [
                school for school, entries in entries_by_school.items()
                if any(e.get("fiqhi_rulings") for e in entries)
            ]
        }

    def _extract_common_understanding(self, interpretations: Dict[str, List]) -> str:
        """Extract points where all schools agree"""
        # Simplified - in production would use NLP for semantic similarity
        return "All four schools agree on the fundamental meaning and significance of these verses within the Islamic tradition."

    def _extract_divergences(self, interpretations: Dict[str, List]) -> List[str]:
        """Extract points of divergence between schools"""
        divergences = [
            "Methodological approach to deriving rulings",
            "Weight given to different types of evidence",
            "Specific legal applications may vary"
        ]
        return divergences

    def _generate_methodology_summary(self, comparisons: Dict[str, Any]) -> str:
        """Generate a summary comparing methodologies"""
        return (
            "The four madhabs share common foundations in Quran and Sunnah but differ in "
            "their approach to secondary sources and the weight given to reason (ra'y) versus "
            "transmitted evidence (naql). Hanafi and Maliki schools allow more room for "
            "juristic reasoning, while Shafi'i and Hanbali schools emphasize textual evidence."
        )

    def get_available_themes(self) -> Dict[str, Any]:
        """Get all available themes for thematic comparison"""
        return {
            "themes": list(self.thematic_mappings.keys()),
            "theme_verse_counts": {
                theme: len(verses)
                for theme, verses in self.thematic_mappings.items()
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "schools_supported": list(self.methodology_descriptions.keys()),
            "total_footnotes": sum(len(fns) for fns in self.footnotes_db.values()),
            "verses_with_footnotes": len(self.footnotes_db),
            "themes_available": len(self.thematic_mappings),
            "methodology_descriptions": len(self.methodology_descriptions)
        }


# Create singleton instance
enhanced_tafsir_comparison_service = EnhancedTafsirComparisonService()
