"""
Situation Atlas — curated mapping of common life situations to:

  - the closest emotion category (uses existing spiritual_guidance_service
    verse bank so we don't duplicate verse data)
  - a prophetic du'a or two with sunnah.com citation
  - the relevant healing theme(s)
  - a "see a professional" flag (set wherever clinical care is the
    primary need, with Quran as supportive companion)

Every entry:
  - has `review_status = "needs_review"` until scholarly review
  - cites real sunnah.com URLs (no invented hadith)
  - paired with the mandatory bilingual disclaimer at response time

Citations are documented in docs/therapy-source-research.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.models.therapy import EmotionCategory


@dataclass
class HadithRef:
    collection: str        # e.g. "bukhari"
    number: str            # e.g. "5743"
    narrator_en: str
    narrator_ar: str
    note_en: str
    note_ar: str

    @property
    def url(self) -> str:
        return f"https://sunnah.com/{self.collection}:{self.number}"


# ---------------------------------------------------------------------------
# Authenticated prophetic du'as (each cites a sunnah.com URL).
# Arabic du'a text appears in well-known canonical form; no Quranic ayah text
# is duplicated here.
# ---------------------------------------------------------------------------

DUA_BANK: Dict[str, Dict[str, str]] = {
    "rabban_naas_shifa": {
        "arabic": "اللَّهُمَّ رَبَّ النَّاسِ، مُذْهِبَ الْبَأْسِ، اشْفِ أَنْتَ الشَّافِي، لَا شَافِيَ إِلَّا أَنْتَ، شِفَاءً لَا يُغَادِرُ سَقَمًا",
        "transliteration": "Allahumma Rabban-naas, mudh-hibal ba's, ishfi Antash-Shafi, la Shafiya illa anta, shifaa'al-la yughadiru saqama.",
        "translation_en": "O Allah, Lord of mankind, Remover of harm. Cure — You are the Healer. There is no cure except Yours, a healing that leaves no illness behind.",
        "translation_ar": "اللهم رب الناس، أذهب الألم، واشفِ — فأنت الشافي، لا شفاء إلا شفاؤك، شفاءً لا يترك بعده مرضاً.",
    },
    "la_ilaha_distress": {
        "arabic": "لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ",
        "transliteration": "La ilaha illa anta, subhanaka, inni kuntu min adh-dhalimeen.",
        "translation_en": "There is no deity except You; glory be to You. Indeed, I have been among the wrongdoers.",
        "translation_ar": "لا إله إلا أنت سبحانك إني كنت من الظالمين — دعاء يونس عليه السلام عند الكرب.",
    },
    "hasbi_allah": {
        "arabic": "حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ",
        "transliteration": "Hasbiyallahu la ilaha illa Huwa, alayhi tawakkaltu wa Huwa Rabbul-Arshil-Adheem.",
        "translation_en": "Allah is sufficient for me. There is no deity except Him. Upon Him I rely, and He is the Lord of the Mighty Throne.",
        "translation_ar": "الله حسبي، لا إله إلا هو عليه توكلت وهو رب العرش العظيم.",
    },
}


# ---------------------------------------------------------------------------
# Situation entries
# ---------------------------------------------------------------------------

@dataclass
class SituationEntry:
    """One named life situation."""

    key: str                          # canonical slug
    label_en: str
    label_ar: str
    description_en: str
    description_ar: str
    # Emotion this maps onto — used to pull verses from the existing bank.
    primary_emotion: str
    healing_themes: List[str]         # subset of HEALING_THEMES keys
    # Du'a + hadith citations (every entry has ≥1 hadith ref).
    dua_keys: List[str] = field(default_factory=list)
    hadith_refs: List[HadithRef] = field(default_factory=list)
    # Whether the user should be encouraged to see a medical / mental-health
    # professional in addition to the spiritual content.
    refer_to_professional: bool = False
    # Audit
    review_status: str = "needs_review"
    human_review_required: bool = True


_BUKHARI_RUQYAH_FATIHAH = HadithRef(
    collection="bukhari",
    number="2276",
    narrator_en="Abu Saʿid al-Khudri",
    narrator_ar="أبو سعيد الخدري",
    note_en="Companions recited Surah al-Fatihah as a ruqyah on a tribal chief; the Prophet ﷺ approved.",
    note_ar="رقى الصحابة سيد القوم بفاتحة الكتاب وأقرّ النبي ﷺ ذلك.",
)
_BUKHARI_MUAWWIDHAT = HadithRef(
    collection="bukhari",
    number="5735",
    narrator_en="ʿĀʾisha",
    narrator_ar="عائشة رضي الله عنها",
    note_en="The Prophet ﷺ would recite the Mu'awwidhat (al-Falaq + an-Nas) during illness and blow on himself.",
    note_ar="كان النبي ﷺ يقرأ المعوذتين عند المرض وينفث على جسده.",
)
_BUKHARI_NIGHT_RECITATION = HadithRef(
    collection="bukhari",
    number="5017",
    narrator_en="ʿĀʾisha",
    narrator_ar="عائشة رضي الله عنها",
    note_en="The Prophet ﷺ recited al-Ikhlas + al-Falaq + an-Nas before sleep and wiped his body.",
    note_ar="كان النبي ﷺ يقرأ الإخلاص والمعوذتين قبل النوم ويمسح بدنه.",
)
_BUKHARI_SHIFA_DUA = HadithRef(
    collection="bukhari",
    number="5743",
    narrator_en="Anas ibn Malik",
    narrator_ar="أنس بن مالك",
    note_en="The Prophetic ruqyah du'a: 'O Allah, Lord of mankind, Remover of harm…'",
    note_ar="رقية النبي ﷺ: 'اللهم رب الناس، أذهب البأس، اشف…'",
)


SITUATION_ATLAS: List[SituationEntry] = [
    SituationEntry(
        key="physical_illness",
        label_en="Physical illness or chronic pain",
        label_ar="مرض جسدي أو ألم مزمن",
        description_en="Seeking spiritual companionship through illness alongside medical care.",
        description_ar="رفقة روحية أثناء المرض إلى جانب الرعاية الطبية.",
        primary_emotion=EmotionCategory.SADNESS,
        healing_themes=["healing", "patience", "ruqyah"],
        dua_keys=["rabban_naas_shifa"],
        hadith_refs=[_BUKHARI_SHIFA_DUA, _BUKHARI_MUAWWIDHAT],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="caring_for_sick_loved_one",
        label_en="Caring for a sick loved one",
        label_ar="رعاية مريض من الأهل",
        description_en="Supporting another while carrying your own weight of worry.",
        description_ar="دعم مريض وأنت تحمل همّك الخاص.",
        primary_emotion=EmotionCategory.ANXIETY,
        healing_themes=["patience", "trust", "ruqyah"],
        dua_keys=["rabban_naas_shifa", "hasbi_allah"],
        hadith_refs=[_BUKHARI_SHIFA_DUA],
        refer_to_professional=False,
    ),
    SituationEntry(
        key="parental_loss",
        label_en="Loss of a parent",
        label_ar="فقد أحد الوالدين",
        description_en="Grief that comes from losing the one who raised you.",
        description_ar="حزن فقد من ربّاك.",
        primary_emotion=EmotionCategory.GRIEF,
        healing_themes=["patience", "mercy", "trust"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="loss_of_child",
        label_en="Loss of a child",
        label_ar="فقد طفل",
        description_en="The deepest grief a parent can carry — one Allah does not waste.",
        description_ar="فقد لا يضيع أجره عند الله.",
        primary_emotion=EmotionCategory.GRIEF,
        healing_themes=["patience", "mercy", "hope"],
        dua_keys=["hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="loss_of_spouse",
        label_en="Loss of a spouse",
        label_ar="فقد الزوج/الزوجة",
        description_en="Grief that reshapes daily life.",
        description_ar="حزن يعيد تشكيل الحياة اليومية.",
        primary_emotion=EmotionCategory.GRIEF,
        healing_themes=["patience", "mercy", "trust"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="miscarriage",
        label_en="Miscarriage or pregnancy loss",
        label_ar="إجهاض أو فقد حمل",
        description_en="A loss that often goes unseen but is heavy.",
        description_ar="فقد قد لا يُرى ولكنه ثقيل.",
        primary_emotion=EmotionCategory.GRIEF,
        healing_themes=["mercy", "patience", "hope"],
        dua_keys=["hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="infertility",
        label_en="Struggling with infertility",
        label_ar="مواجهة العقم",
        description_en="The wait for a child Allah may yet grant.",
        description_ar="انتظار رزقٍ قد يهبه الله بعد حين.",
        primary_emotion=EmotionCategory.HOPELESSNESS,
        healing_themes=["hope", "trust", "patience"],
        dua_keys=["hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="marriage_strain",
        label_en="Strain in marriage",
        label_ar="ضائقة زوجية",
        description_en="Carrying tension at home and asking for softness.",
        description_ar="حمل التوتر في البيت وسؤال الله الرفق.",
        primary_emotion=EmotionCategory.ANXIETY,
        healing_themes=["mercy", "patience", "dhikr"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="divorce",
        label_en="Divorce or separation",
        label_ar="الطلاق أو الانفصال",
        description_en="A turning page that often carries grief and shame.",
        description_ar="فصلٌ في الحياة كثيراً ما يحمل حزناً وخجلاً.",
        primary_emotion=EmotionCategory.GRIEF,
        healing_themes=["mercy", "forgiveness", "hope"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="financial_fear",
        label_en="Financial fear or hardship",
        label_ar="ضيق وخوف من جهة المال",
        description_en="Worry over rizq when the door of provision feels closed.",
        description_ar="هَمّ الرزق حين يبدو الباب موصداً.",
        primary_emotion=EmotionCategory.FEAR,
        healing_themes=["trust", "hope", "dhikr"],
        dua_keys=["hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="unemployment",
        label_en="Unemployment or job loss",
        label_ar="بطالة أو فقد عمل",
        description_en="Walking the road of seeking with patience.",
        description_ar="سيرٌ في طريق الطلب بالصبر.",
        primary_emotion=EmotionCategory.FEAR,
        healing_themes=["trust", "patience", "hope"],
        dua_keys=["hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="exam_anxiety",
        label_en="Exam or academic anxiety",
        label_ar="قلق امتحان أو دراسة",
        description_en="Asking Allah for ease and clarity.",
        description_ar="سؤال الله التيسير والوضوح.",
        primary_emotion=EmotionCategory.ANXIETY,
        healing_themes=["trust", "patience", "strength"],
        dua_keys=["hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="insomnia",
        label_en="Insomnia or restless sleep",
        label_ar="أرق أو نوم متقطع",
        description_en="When the heart will not settle at night.",
        description_ar="حين لا يهدأ القلب في الليل.",
        primary_emotion=EmotionCategory.ANXIETY,
        healing_themes=["dhikr", "ruqyah", "trust"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=False,
    ),
    SituationEntry(
        key="anxiety_general",
        label_en="Generalised anxiety",
        label_ar="قلق عام",
        description_en="A heart that races without a single named cause.",
        description_ar="قلب يتسارع نبضه دون سبب واحد واضح.",
        primary_emotion=EmotionCategory.ANXIETY,
        healing_themes=["trust", "dhikr", "hope"],
        dua_keys=["hasbi_allah", "la_ilaha_distress"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="depression_episode",
        label_en="Depressive episode",
        label_ar="نوبة اكتئاب",
        description_en="A weight that asks for both spiritual and clinical care.",
        description_ar="ثِقَلٌ يحتاج لدعمٍ روحي وسريري معاً.",
        primary_emotion=EmotionCategory.SADNESS,
        healing_themes=["mercy", "hope", "ruqyah"],
        dua_keys=["la_ilaha_distress", "hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="loneliness",
        label_en="Loneliness",
        label_ar="وحدة",
        description_en="Feeling unseen while Allah sees everything.",
        description_ar="شعور بألا أحد يراك وقد رآك الله.",
        primary_emotion=EmotionCategory.SADNESS,
        healing_themes=["mercy", "dhikr", "trust"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="anger_management",
        label_en="Anger you cannot calm",
        label_ar="غضب لا يهدأ",
        description_en="When the fire rises and you ask Allah to soften it.",
        description_ar="حين يشتد الغضب وتسأل الله أن يلطّفه.",
        primary_emotion=EmotionCategory.ANGER,
        healing_themes=["patience", "forgiveness", "dhikr"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="guilt_after_sin",
        label_en="Guilt after a sin",
        label_ar="ندم بعد ذنب",
        description_en="The door of tawbah opens wider than any sin.",
        description_ar="باب التوبة أوسع من أي ذنب.",
        primary_emotion=EmotionCategory.GUILT,
        healing_themes=["forgiveness", "tawbah", "mercy"],
        dua_keys=["la_ilaha_distress"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="religious_doubt",
        label_en="Religious doubts or shaken faith",
        label_ar="شك ديني أو تذبذب إيمان",
        description_en="Questions are part of the journey — Allah meets the seeker.",
        description_ar="الأسئلة جزء من الطريق — والله يعين السائل.",
        primary_emotion=EmotionCategory.DOUBT,
        healing_themes=["trust", "dhikr", "healing"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="abuse_or_harm",
        label_en="Experiencing abuse or harm",
        label_ar="تعرّض لإيذاء",
        description_en="You deserve safety. Please reach out to a professional.",
        description_ar="أنت تستحق الأمان — يرجى التواصل مع جهة مختصة.",
        primary_emotion=EmotionCategory.FEAR,
        healing_themes=["mercy", "trust", "strength"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="addiction_recovery",
        label_en="Working through addiction or recovery",
        label_ar="مواجهة إدمان أو تعافٍ",
        description_en="One step at a time. Allah turns to those who turn.",
        description_ar="خطوة في كل مرة — والله يقبل من يعود إليه.",
        primary_emotion=EmotionCategory.GUILT,
        healing_themes=["forgiveness", "tawbah", "strength"],
        dua_keys=["la_ilaha_distress"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="caring_for_aging_parent",
        label_en="Caring for an aging parent",
        label_ar="رعاية والد كبير في السن",
        description_en="A heavy daily duty that Allah promises to reward.",
        description_ar="مسؤولية يومية ثقيلة وعدها الله بالأجر.",
        primary_emotion=EmotionCategory.ANXIETY,
        healing_themes=["patience", "mercy", "dhikr"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="estranged_family",
        label_en="Estranged family relationships",
        label_ar="قطيعة عائلية",
        description_en="The pain of bonds that have frayed.",
        description_ar="ألم الروابط التي وهنت.",
        primary_emotion=EmotionCategory.SADNESS,
        healing_themes=["mercy", "forgiveness", "patience"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
    SituationEntry(
        key="immigration_displacement",
        label_en="Displacement, war, or refugee experience",
        label_ar="نزوح أو حرب أو لجوء",
        description_en="A grief many in the Ummah carry today.",
        description_ar="حزن يحمله كثيرون في الأمة اليوم.",
        primary_emotion=EmotionCategory.GRIEF,
        healing_themes=["mercy", "patience", "trust"],
        dua_keys=["hasbi_allah"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
        refer_to_professional=True,
    ),
    SituationEntry(
        key="gratitude_in_ease",
        label_en="Gratitude for a blessing",
        label_ar="شكر على نعمة",
        description_en="Naming the gift to deepen its taste.",
        description_ar="ذكر النعمة لتزداد حلاوتها.",
        primary_emotion=EmotionCategory.GRATITUDE,
        healing_themes=["gratitude", "dhikr", "mercy"],
        hadith_refs=[_BUKHARI_NIGHT_RECITATION],
    ),
]


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------


def list_situations() -> List[SituationEntry]:
    return list(SITUATION_ATLAS)


def get_situation(key: str) -> Optional[SituationEntry]:
    for s in SITUATION_ATLAS:
        if s.key == key:
            return s
    return None
