"""
Multi-School Tafsir Interpretation Comparison Service.

Provides comparison of Quranic interpretations across different scholarly schools:
1. Classical Sunni Schools (Hanafi, Maliki, Shafi'i, Hanbali)
2. Theological Schools (Ash'ari, Maturidi, Athari)
3. Methodological Approaches (Linguistic, Narration-based, Rational)
4. Sufi/Mystical interpretations
5. Contemporary scholarly perspectives

Arabic: خدمة مقارنة تفاسير المذاهب المتعددة
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# TAFSIR SCHOOLS CONFIGURATION
# =============================================================================

class TafsirSchool(str, Enum):
    """Major schools of Tafsir."""
    SUNNI_TRADITIONAL = "sunni_traditional"
    SUNNI_LINGUISTIC = "sunni_linguistic"
    SUNNI_RATIONAL = "sunni_rational"
    SHIA_TWELVER = "shia_twelver"
    SUFI_MYSTICAL = "sufi_mystical"
    CONTEMPORARY = "contemporary"
    SALAFI = "salafi"
    REFORMIST = "reformist"


class TheologicalSchool(str, Enum):
    """Major theological schools (Aqeedah)."""
    ASHARI = "ashari"
    MATURIDI = "maturidi"
    ATHARI = "athari"
    MUTAZILI = "mutazili"
    SHIA_IMAMI = "shia_imami"


class FiqhSchool(str, Enum):
    """Major jurisprudence schools."""
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"
    JAFARI = "jafari"  # Shia
    ZAHIRI = "zahiri"


# Scholar profiles with their schools and methodologies
SCHOLARS_BY_SCHOOL = {
    TafsirSchool.SUNNI_TRADITIONAL: [
        {
            "id": "ibn_kathir",
            "name_ar": "ابن كثير",
            "name_en": "Ibn Kathir",
            "years": "1301-1373 CE",
            "tafsir": "تفسير القرآن العظيم",
            "methodology": "narration_based",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير بالمأثور، يعتمد على الأحاديث والآثار",
            "description_en": "Narration-based Tafsir relying on hadith and reports",
            "strengths": ["hadith_verification", "chain_analysis", "historical_context"],
        },
        {
            "id": "tabari",
            "name_ar": "الطبري",
            "name_en": "Al-Tabari",
            "years": "839-923 CE",
            "tafsir": "جامع البيان",
            "methodology": "comprehensive",
            "theological_school": TheologicalSchool.ATHARI,
            "description_ar": "أشمل التفاسير، يجمع الأقوال ويناقشها",
            "description_en": "Most comprehensive, collects and discusses various opinions",
            "strengths": ["comprehensive", "scholarly_opinions", "linguistic_analysis"],
        },
        {
            "id": "baghawi",
            "name_ar": "البغوي",
            "name_en": "Al-Baghawi",
            "years": "1044-1122 CE",
            "tafsir": "معالم التنزيل",
            "methodology": "narration_based",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير مختصر معتدل",
            "description_en": "Concise and moderate interpretation",
            "strengths": ["accessibility", "clarity", "balanced_approach"],
        },
    ],
    TafsirSchool.SUNNI_LINGUISTIC: [
        {
            "id": "zamakhshari",
            "name_ar": "الزمخشري",
            "name_en": "Al-Zamakhshari",
            "years": "1075-1144 CE",
            "tafsir": "الكشاف",
            "methodology": "linguistic",
            "theological_school": TheologicalSchool.MUTAZILI,
            "description_ar": "تفسير بلاغي لغوي متميز",
            "description_en": "Distinguished linguistic and rhetorical interpretation",
            "strengths": ["arabic_rhetoric", "linguistic_analysis", "literary_style"],
            "caution_ar": "له اعتزالات في العقيدة",
            "caution_en": "Contains Mutazili theological positions",
        },
        {
            "id": "abu_hayyan",
            "name_ar": "أبو حيان الأندلسي",
            "name_en": "Abu Hayyan al-Andalusi",
            "years": "1256-1344 CE",
            "tafsir": "البحر المحيط",
            "methodology": "linguistic",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير نحوي لغوي موسوعي",
            "description_en": "Encyclopedic grammatical and linguistic Tafsir",
            "strengths": ["grammar", "syntax", "linguistic_variations"],
        },
    ],
    TafsirSchool.SUNNI_RATIONAL: [
        {
            "id": "razi",
            "name_ar": "الفخر الرازي",
            "name_en": "Fakhr al-Din al-Razi",
            "years": "1149-1210 CE",
            "tafsir": "مفاتيح الغيب",
            "methodology": "rational",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير فلسفي عقلي موسوعي",
            "description_en": "Philosophical and rational encyclopedic Tafsir",
            "strengths": ["philosophical_depth", "theological_arguments", "scientific_connections"],
        },
        {
            "id": "alusi",
            "name_ar": "الألوسي",
            "name_en": "Al-Alusi",
            "years": "1802-1854 CE",
            "tafsir": "روح المعاني",
            "methodology": "comprehensive",
            "theological_school": TheologicalSchool.MATURIDI,
            "description_ar": "تفسير جامع يوازن بين المنقول والمعقول",
            "description_en": "Comprehensive Tafsir balancing narration and reason",
            "strengths": ["balance", "synthesis", "sufi_insights"],
        },
    ],
    TafsirSchool.SUFI_MYSTICAL: [
        {
            "id": "qushayri",
            "name_ar": "القشيري",
            "name_en": "Al-Qushayri",
            "years": "986-1072 CE",
            "tafsir": "لطائف الإشارات",
            "methodology": "mystical",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير إشاري صوفي",
            "description_en": "Mystical and allegorical Tafsir",
            "strengths": ["spiritual_insights", "inner_meanings", "heart_purification"],
        },
        {
            "id": "ibn_arabi",
            "name_ar": "ابن عربي",
            "name_en": "Ibn Arabi",
            "years": "1165-1240 CE",
            "tafsir": "تفسير ابن عربي",
            "methodology": "mystical",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير صوفي عميق",
            "description_en": "Deep mystical Tafsir",
            "strengths": ["esoteric_meanings", "unity_of_being", "divine_love"],
            "caution_ar": "يحتاج لفهم عميق للتصوف",
            "caution_en": "Requires deep understanding of Sufism",
        },
    ],
    TafsirSchool.SHIA_TWELVER: [
        {
            "id": "tabrisi",
            "name_ar": "الطبرسي",
            "name_en": "Al-Tabrisi",
            "years": "1073-1154 CE",
            "tafsir": "مجمع البيان",
            "methodology": "comprehensive",
            "theological_school": TheologicalSchool.SHIA_IMAMI,
            "description_ar": "تفسير شيعي شامل",
            "description_en": "Comprehensive Shia Tafsir",
            "strengths": ["linguistic_analysis", "imam_teachings", "sectarian_balance"],
        },
        {
            "id": "tabatabai",
            "name_ar": "الطباطبائي",
            "name_en": "Allamah Tabatabai",
            "years": "1904-1981 CE",
            "tafsir": "الميزان في تفسير القرآن",
            "methodology": "rational",
            "theological_school": TheologicalSchool.SHIA_IMAMI,
            "description_ar": "تفسير شيعي معاصر عقلاني",
            "description_en": "Contemporary rational Shia Tafsir",
            "strengths": ["philosophical_depth", "modern_relevance", "cross_referencing"],
        },
    ],
    TafsirSchool.CONTEMPORARY: [
        {
            "id": "fi_zilal",
            "name_ar": "سيد قطب",
            "name_en": "Sayyid Qutb",
            "years": "1906-1966 CE",
            "tafsir": "في ظلال القرآن",
            "methodology": "social",
            "theological_school": TheologicalSchool.ATHARI,
            "description_ar": "تفسير أدبي اجتماعي",
            "description_en": "Literary and social Tafsir",
            "strengths": ["literary_style", "social_application", "emotional_impact"],
        },
        {
            "id": "sha'rawi",
            "name_ar": "الشعراوي",
            "name_en": "Al-Sha'rawi",
            "years": "1911-1998 CE",
            "tafsir": "تفسير الشعراوي",
            "methodology": "popular",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير شعبي ميسر",
            "description_en": "Popular accessible Tafsir",
            "strengths": ["accessibility", "contemporary_examples", "practical_guidance"],
        },
        {
            "id": "tantawi",
            "name_ar": "محمد سيد طنطاوي",
            "name_en": "Muhammad Sayyid Tantawi",
            "years": "1928-2010 CE",
            "tafsir": "التفسير الوسيط",
            "methodology": "moderate",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير وسطي معتدل",
            "description_en": "Moderate and balanced Tafsir",
            "strengths": ["moderation", "clarity", "contemporary_issues"],
        },
    ],
    TafsirSchool.SALAFI: [
        {
            "id": "ibn_taymiyyah",
            "name_ar": "ابن تيمية",
            "name_en": "Ibn Taymiyyah",
            "years": "1263-1328 CE",
            "tafsir": "مجموع الفتاوى (التفسير)",
            "methodology": "textual",
            "theological_school": TheologicalSchool.ATHARI,
            "description_ar": "تفسير أثري نصي",
            "description_en": "Textual and traditional Tafsir",
            "strengths": ["textual_analysis", "hadith_priority", "refuting_innovations"],
        },
        {
            "id": "sadi",
            "name_ar": "السعدي",
            "name_en": "Al-Sa'di",
            "years": "1889-1956 CE",
            "tafsir": "تيسير الكريم الرحمن",
            "methodology": "textual",
            "theological_school": TheologicalSchool.ATHARI,
            "description_ar": "تفسير مختصر واضح",
            "description_en": "Concise and clear Tafsir",
            "strengths": ["simplicity", "practical_guidance", "spiritual_benefit"],
        },
    ],
    TafsirSchool.REFORMIST: [
        {
            "id": "muhammad_abduh",
            "name_ar": "محمد عبده",
            "name_en": "Muhammad Abduh",
            "years": "1849-1905 CE",
            "tafsir": "تفسير المنار",
            "methodology": "reformist",
            "theological_school": TheologicalSchool.ASHARI,
            "description_ar": "تفسير إصلاحي عقلاني",
            "description_en": "Reformist and rational Tafsir",
            "strengths": ["modern_interpretation", "social_reform", "scientific_approach"],
        },
        {
            "id": "rashid_rida",
            "name_ar": "رشيد رضا",
            "name_en": "Rashid Rida",
            "years": "1865-1935 CE",
            "tafsir": "تفسير المنار (تكملة)",
            "methodology": "reformist",
            "theological_school": TheologicalSchool.ATHARI,
            "description_ar": "تفسير إصلاحي سلفي",
            "description_en": "Reformist Salafi Tafsir",
            "strengths": ["reform_agenda", "hadith_criticism", "modern_challenges"],
        },
    ],
}

# Key theological topics that differ between schools
COMPARATIVE_TOPICS = {
    "divine_attributes": {
        "ar": "صفات الله",
        "en": "Divine Attributes",
        "key_verses": ["2:255", "112:1-4", "42:11", "7:54"],
        "differences": {
            TheologicalSchool.ASHARI: "Affirms attributes with metaphorical interpretation (ta'wil)",
            TheologicalSchool.MATURIDI: "Similar to Ash'ari with some differences in details",
            TheologicalSchool.ATHARI: "Affirms attributes literally without asking 'how' (bila kayf)",
            TheologicalSchool.MUTAZILI: "Denies real attributes to preserve divine unity",
        },
    },
    "free_will_predestination": {
        "ar": "القضاء والقدر",
        "en": "Free Will and Predestination",
        "key_verses": ["18:29", "76:30", "81:29", "37:96"],
        "differences": {
            TheologicalSchool.ASHARI: "Acquisition (kasb) - humans acquire acts God creates",
            TheologicalSchool.MATURIDI: "Similar to Ash'ari but emphasizes human choice more",
            TheologicalSchool.ATHARI: "Affirms both divine decree and human responsibility",
            TheologicalSchool.MUTAZILI: "Emphasizes human free will and moral responsibility",
        },
    },
    "seeing_allah": {
        "ar": "رؤية الله",
        "en": "Seeing Allah",
        "key_verses": ["75:22-23", "6:103", "7:143"],
        "differences": {
            TheologicalSchool.ASHARI: "Believers will see Allah in the Hereafter",
            TheologicalSchool.MATURIDI: "Same as Ash'ari",
            TheologicalSchool.ATHARI: "Affirms vision without asking 'how'",
            TheologicalSchool.MUTAZILI: "Denies physical vision",
        },
    },
    "intercession": {
        "ar": "الشفاعة",
        "en": "Intercession",
        "key_verses": ["2:255", "21:28", "20:109"],
        "differences": {
            TheologicalSchool.ASHARI: "Accepts intercession with Allah's permission",
            TheologicalSchool.ATHARI: "Same, emphasizes hadith evidence",
            TheologicalSchool.SHIA_IMAMI: "Strong emphasis on intercession of Imams",
        },
    },
    "imamate": {
        "ar": "الإمامة",
        "en": "Leadership/Imamate",
        "key_verses": ["4:59", "5:55", "33:33"],
        "differences": {
            "sunni": "Leadership by consultation (shura) and consensus",
            "shia": "Leadership by divine appointment through the Prophet's family",
        },
    },
}


# =============================================================================
# TAFSIR SCHOOLS SERVICE
# =============================================================================

class TafsirSchoolsService:
    """
    Multi-school Tafsir comparison service.

    Provides:
    - School-based Tafsir browsing
    - Cross-school comparison for specific verses
    - Theological topic comparisons
    - Scholar profiles and methodologies
    """

    def __init__(self):
        self._scholars_by_school = SCHOLARS_BY_SCHOOL
        self._comparative_topics = COMPARATIVE_TOPICS

    def get_all_schools(self) -> List[Dict[str, Any]]:
        """Get all Tafsir schools with descriptions."""
        schools = []

        for school in TafsirSchool:
            scholars = self._scholars_by_school.get(school, [])
            schools.append({
                "id": school.value,
                "name_ar": self._get_school_name_ar(school),
                "name_en": self._get_school_name_en(school),
                "scholars_count": len(scholars),
                "scholars": [s["name_en"] for s in scholars],
                "description_ar": self._get_school_description_ar(school),
                "description_en": self._get_school_description_en(school),
            })

        return schools

    def _get_school_name_ar(self, school: TafsirSchool) -> str:
        """Get Arabic name for school."""
        names = {
            TafsirSchool.SUNNI_TRADITIONAL: "المدرسة السنية التقليدية",
            TafsirSchool.SUNNI_LINGUISTIC: "المدرسة اللغوية",
            TafsirSchool.SUNNI_RATIONAL: "المدرسة العقلية",
            TafsirSchool.SHIA_TWELVER: "المدرسة الشيعية الإمامية",
            TafsirSchool.SUFI_MYSTICAL: "المدرسة الصوفية الإشارية",
            TafsirSchool.CONTEMPORARY: "المدرسة المعاصرة",
            TafsirSchool.SALAFI: "المدرسة السلفية",
            TafsirSchool.REFORMIST: "المدرسة الإصلاحية",
        }
        return names.get(school, school.value)

    def _get_school_name_en(self, school: TafsirSchool) -> str:
        """Get English name for school."""
        names = {
            TafsirSchool.SUNNI_TRADITIONAL: "Sunni Traditional School",
            TafsirSchool.SUNNI_LINGUISTIC: "Linguistic School",
            TafsirSchool.SUNNI_RATIONAL: "Rational School",
            TafsirSchool.SHIA_TWELVER: "Shia Twelver School",
            TafsirSchool.SUFI_MYSTICAL: "Sufi Mystical School",
            TafsirSchool.CONTEMPORARY: "Contemporary School",
            TafsirSchool.SALAFI: "Salafi School",
            TafsirSchool.REFORMIST: "Reformist School",
        }
        return names.get(school, school.value)

    def _get_school_description_ar(self, school: TafsirSchool) -> str:
        """Get Arabic description for school."""
        descriptions = {
            TafsirSchool.SUNNI_TRADITIONAL: "تفسير يعتمد على الحديث والآثار والإجماع",
            TafsirSchool.SUNNI_LINGUISTIC: "تفسير يركز على البلاغة والنحو والصرف",
            TafsirSchool.SUNNI_RATIONAL: "تفسير يوازن بين النقل والعقل والفلسفة",
            TafsirSchool.SHIA_TWELVER: "تفسير يعتمد على روايات أهل البيت",
            TafsirSchool.SUFI_MYSTICAL: "تفسير يبحث في المعاني الباطنية والإشارات",
            TafsirSchool.CONTEMPORARY: "تفسير يربط القرآن بالواقع المعاصر",
            TafsirSchool.SALAFI: "تفسير يلتزم بفهم السلف الصالح",
            TafsirSchool.REFORMIST: "تفسير يسعى للإصلاح والتجديد",
        }
        return descriptions.get(school, "")

    def _get_school_description_en(self, school: TafsirSchool) -> str:
        """Get English description for school."""
        descriptions = {
            TafsirSchool.SUNNI_TRADITIONAL: "Interpretation based on hadith, reports, and consensus",
            TafsirSchool.SUNNI_LINGUISTIC: "Focus on rhetoric, grammar, and morphology",
            TafsirSchool.SUNNI_RATIONAL: "Balances narration with reason and philosophy",
            TafsirSchool.SHIA_TWELVER: "Based on teachings of the Prophet's household (Ahl al-Bayt)",
            TafsirSchool.SUFI_MYSTICAL: "Explores inner meanings and spiritual insights",
            TafsirSchool.CONTEMPORARY: "Connects Quran to modern life and challenges",
            TafsirSchool.SALAFI: "Adheres to understanding of early Muslims (Salaf)",
            TafsirSchool.REFORMIST: "Seeks reform and renewal in interpretation",
        }
        return descriptions.get(school, "")

    def get_scholars_by_school(self, school: str) -> List[Dict[str, Any]]:
        """Get all scholars belonging to a specific school."""
        try:
            school_enum = TafsirSchool(school)
        except ValueError:
            return []

        return self._scholars_by_school.get(school_enum, [])

    def get_scholar_details(self, scholar_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a scholar."""
        for school, scholars in self._scholars_by_school.items():
            for scholar in scholars:
                if scholar["id"] == scholar_id:
                    return {
                        **scholar,
                        "school": school.value,
                        "school_name_ar": self._get_school_name_ar(school),
                        "school_name_en": self._get_school_name_en(school),
                    }
        return None

    def compare_schools_on_verse(
        self,
        sura_no: int,
        aya_no: int,
        schools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare interpretations from different schools on a specific verse.

        Arabic: مقارنة تفاسير المذاهب المختلفة لآية معينة
        """
        verse_ref = f"{sura_no}:{aya_no}"

        # Select schools to compare
        if schools:
            selected_schools = []
            for s in schools:
                try:
                    selected_schools.append(TafsirSchool(s))
                except ValueError:
                    pass
        else:
            # Default: one from each major category
            selected_schools = [
                TafsirSchool.SUNNI_TRADITIONAL,
                TafsirSchool.SUNNI_LINGUISTIC,
                TafsirSchool.SUFI_MYSTICAL,
                TafsirSchool.CONTEMPORARY,
            ]

        comparisons = []
        for school in selected_schools:
            scholars = self._scholars_by_school.get(school, [])
            if scholars:
                # Take first scholar from each school for comparison
                scholar = scholars[0]
                comparisons.append({
                    "school": school.value,
                    "school_name_ar": self._get_school_name_ar(school),
                    "school_name_en": self._get_school_name_en(school),
                    "scholar": {
                        "id": scholar["id"],
                        "name_ar": scholar["name_ar"],
                        "name_en": scholar["name_en"],
                    },
                    "methodology": scholar.get("methodology", ""),
                    "strengths": scholar.get("strengths", []),
                    # Placeholder - actual tafsir content would come from database
                    "interpretation_ar": f"تفسير {scholar['name_ar']} للآية {verse_ref}",
                    "interpretation_en": f"{scholar['name_en']}'s interpretation of verse {verse_ref}",
                })

        return {
            "verse_reference": verse_ref,
            "schools_compared": len(comparisons),
            "comparisons": comparisons,
            "guidance_ar": "قارن بين المناهج المختلفة لفهم أعمق للآية",
            "guidance_en": "Compare different methodologies for deeper understanding",
        }

    def get_theological_topics(self) -> List[Dict[str, Any]]:
        """Get all comparative theological topics."""
        topics = []

        for topic_id, topic_data in self._comparative_topics.items():
            topics.append({
                "id": topic_id,
                "name_ar": topic_data["ar"],
                "name_en": topic_data["en"],
                "key_verses": topic_data["key_verses"],
                "schools_with_differences": list(topic_data.get("differences", {}).keys()),
            })

        return topics

    def get_topic_comparison(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed comparison of schools on a theological topic."""
        topic = self._comparative_topics.get(topic_id)

        if not topic:
            return None

        differences = []
        for school, position in topic.get("differences", {}).items():
            if isinstance(school, TheologicalSchool):
                school_name = school.value
            else:
                school_name = str(school)

            differences.append({
                "school": school_name,
                "position": position,
            })

        return {
            "topic_id": topic_id,
            "name_ar": topic["ar"],
            "name_en": topic["en"],
            "key_verses": topic["key_verses"],
            "differences": differences,
            "note_ar": "هذه خلافات فكرية تاريخية، وكل مسلم يتبع ما اقتنع به",
            "note_en": "These are historical theological differences; each Muslim follows their conviction",
        }

    def get_methodologies(self) -> List[Dict[str, Any]]:
        """Get all Tafsir methodologies with descriptions."""
        methodologies = {
            "narration_based": {
                "ar": "التفسير بالمأثور",
                "en": "Narration-based (Tafsir bil-Ma'thur)",
                "description_ar": "يعتمد على الأحاديث والآثار عن الصحابة والتابعين",
                "description_en": "Relies on hadith and reports from Companions and their followers",
                "examples": ["ابن كثير", "الطبري"],
            },
            "rational": {
                "ar": "التفسير بالرأي",
                "en": "Rational Interpretation (Tafsir bil-Ra'y)",
                "description_ar": "يستخدم العقل والاجتهاد مع ضوابط شرعية",
                "description_en": "Uses reason and ijtihad within religious guidelines",
                "examples": ["الرازي", "الألوسي"],
            },
            "linguistic": {
                "ar": "التفسير اللغوي",
                "en": "Linguistic Interpretation",
                "description_ar": "يركز على البلاغة والنحو والصرف",
                "description_en": "Focuses on rhetoric, grammar, and morphology",
                "examples": ["الزمخشري", "أبو حيان"],
            },
            "mystical": {
                "ar": "التفسير الإشاري",
                "en": "Mystical/Allegorical Interpretation",
                "description_ar": "يبحث في المعاني الباطنية والإشارات الروحية",
                "description_en": "Explores inner meanings and spiritual allusions",
                "examples": ["القشيري", "ابن عربي"],
            },
            "comprehensive": {
                "ar": "التفسير الشامل",
                "en": "Comprehensive Interpretation",
                "description_ar": "يجمع بين المنقول والمعقول واللغة",
                "description_en": "Combines narration, reason, and linguistics",
                "examples": ["الطبري", "الألوسي"],
            },
            "social": {
                "ar": "التفسير الاجتماعي",
                "en": "Social Interpretation",
                "description_ar": "يربط القرآن بالواقع الاجتماعي والسياسي",
                "description_en": "Connects Quran to social and political reality",
                "examples": ["سيد قطب", "محمد عبده"],
            },
        }

        return [
            {"id": k, **v}
            for k, v in methodologies.items()
        ]

    def recommend_tafsir_for_goal(self, goal: str) -> List[Dict[str, Any]]:
        """Recommend Tafsir sources based on study goal."""
        recommendations = {
            "beginner": {
                "ar": "للمبتدئين",
                "en": "For beginners",
                "scholars": ["sadi", "baghawi", "sha'rawi"],
                "reason_ar": "تفاسير واضحة ومختصرة ومناسبة للبداية",
                "reason_en": "Clear, concise, and suitable for beginners",
            },
            "linguistic": {
                "ar": "للدراسة اللغوية",
                "en": "For linguistic study",
                "scholars": ["zamakhshari", "abu_hayyan"],
                "reason_ar": "تفاسير تركز على البلاغة والنحو",
                "reason_en": "Tafsirs focusing on rhetoric and grammar",
            },
            "hadith": {
                "ar": "لفهم الحديث",
                "en": "For hadith understanding",
                "scholars": ["ibn_kathir", "tabari"],
                "reason_ar": "تفاسير غنية بالأحاديث والآثار",
                "reason_en": "Tafsirs rich in hadith and reports",
            },
            "philosophical": {
                "ar": "للدراسة الفلسفية",
                "en": "For philosophical study",
                "scholars": ["razi", "tabatabai"],
                "reason_ar": "تفاسير عميقة فلسفياً وعقلياً",
                "reason_en": "Philosophically deep Tafsirs",
            },
            "spiritual": {
                "ar": "للتزكية الروحية",
                "en": "For spiritual growth",
                "scholars": ["qushayri", "fi_zilal"],
                "reason_ar": "تفاسير تركز على الجانب الروحي والتربوي",
                "reason_en": "Tafsirs focusing on spiritual and educational aspects",
            },
            "contemporary": {
                "ar": "للفهم المعاصر",
                "en": "For contemporary understanding",
                "scholars": ["fi_zilal", "tantawi", "sha'rawi"],
                "reason_ar": "تفاسير تربط القرآن بالعصر الحديث",
                "reason_en": "Tafsirs connecting Quran to modern times",
            },
        }

        goal_lower = goal.lower()

        # Find matching goal
        for goal_id, rec in recommendations.items():
            if goal_lower in goal_id or goal_lower in rec["en"].lower():
                scholars_details = []
                for scholar_id in rec["scholars"]:
                    scholar = self.get_scholar_details(scholar_id)
                    if scholar:
                        scholars_details.append(scholar)

                return {
                    "goal": goal,
                    "category": goal_id,
                    "reason_ar": rec["reason_ar"],
                    "reason_en": rec["reason_en"],
                    "recommended_scholars": scholars_details,
                }

        # Default recommendations
        return {
            "goal": goal,
            "category": "general",
            "reason_ar": "تفاسير شاملة ومتنوعة",
            "reason_en": "Comprehensive and diverse Tafsirs",
            "recommended_scholars": [
                self.get_scholar_details("ibn_kathir"),
                self.get_scholar_details("fi_zilal"),
            ],
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

tafsir_schools_service = TafsirSchoolsService()
