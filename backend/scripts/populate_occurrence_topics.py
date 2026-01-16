#!/usr/bin/env python3
"""
Populate topic descriptions for concept occurrences.

This script updates the context_ar and context_en fields for concept occurrences
with meaningful topic descriptions based on Quranic scholarship.

Usage:
    PYTHONPATH=. python scripts/populate_occurrence_topics.py
"""
import asyncio
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.concept import Occurrence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Topic descriptions for verses mentioning Prophet Isa (Jesus) - عيسى عليه السلام
ISA_TOPICS = {
    "2:87": {
        "ar": "تأييد عيسى بروح القدس",
        "en": "Supporting Isa with the Holy Spirit"
    },
    "2:136": {
        "ar": "الإيمان بجميع الأنبياء ومنهم عيسى",
        "en": "Believing in all prophets including Isa"
    },
    "2:253": {
        "ar": "تفضيل الرسل وذكر عيسى ابن مريم",
        "en": "Excellence of messengers and mention of Isa son of Maryam"
    },
    "3:45": {
        "ar": "البشارة بميلاد المسيح عيسى ابن مريم",
        "en": "The annunciation of the Messiah Isa son of Maryam"
    },
    "3:52": {
        "ar": "الحواريون أنصار عيسى",
        "en": "The disciples as helpers of Isa"
    },
    "3:55": {
        "ar": "رفع عيسى إلى السماء",
        "en": "Raising Isa to the heavens"
    },
    "3:59": {
        "ar": "خلق عيسى كمثل آدم",
        "en": "Creation of Isa like Adam"
    },
    "3:84": {
        "ar": "الإيمان بما أنزل على الأنبياء",
        "en": "Believing in what was revealed to prophets"
    },
    "4:157": {
        "ar": "نفي قتل عيسى وصلبه",
        "en": "Denial of Isa's crucifixion"
    },
    "4:163": {
        "ar": "الوحي إلى الأنبياء ومنهم عيسى",
        "en": "Revelation to prophets including Isa"
    },
    "4:171": {
        "ar": "عيسى كلمة الله وروح منه",
        "en": "Isa as Allah's word and spirit"
    },
    "5:46": {
        "ar": "إيتاء عيسى الإنجيل",
        "en": "Giving Isa the Gospel"
    },
    "5:72": {
        "ar": "كفر من قال إن الله هو المسيح",
        "en": "Disbelief of those who say Allah is the Messiah"
    },
    "5:75": {
        "ar": "المسيح ابن مريم رسول",
        "en": "The Messiah son of Maryam is a messenger"
    },
    "5:78": {
        "ar": "لعن الكافرين من بني إسرائيل",
        "en": "Curse on disbelievers from Children of Israel"
    },
    "5:110": {
        "ar": "معجزات عيسى عليه السلام",
        "en": "Miracles of Isa peace be upon him"
    },
    "5:112": {
        "ar": "طلب الحواريين المائدة",
        "en": "The disciples asking for a table spread"
    },
    "5:114": {
        "ar": "دعاء عيسى بإنزال المائدة",
        "en": "Isa's supplication for the table spread"
    },
    "5:116": {
        "ar": "براءة عيسى من الغلو فيه",
        "en": "Isa's disavowal of being worshipped"
    },
    "6:85": {
        "ar": "عيسى من الصالحين",
        "en": "Isa among the righteous"
    },
    "19:34": {
        "ar": "حقيقة عيسى ابن مريم",
        "en": "The truth about Isa son of Maryam"
    },
    "21:91": {
        "ar": "مريم التي أحصنت فرجها",
        "en": "Maryam who guarded her chastity"
    },
    "23:50": {
        "ar": "عيسى وأمه آية للعالمين",
        "en": "Isa and his mother as a sign"
    },
    "33:7": {
        "ar": "ميثاق النبيين",
        "en": "The covenant of the prophets"
    },
    "42:13": {
        "ar": "شرع الدين لجميع الأنبياء",
        "en": "The religion ordained for all prophets"
    },
    "43:57": {
        "ar": "عيسى ابن مريم مثلاً",
        "en": "Isa son of Maryam as an example"
    },
    "43:63": {
        "ar": "عيسى جاء بالحكمة والبينات",
        "en": "Isa came with wisdom and clear proofs"
    },
    "57:27": {
        "ar": "رهبانية أتباع عيسى",
        "en": "Monasticism of Isa's followers"
    },
    "61:6": {
        "ar": "بشارة عيسى برسول يأتي من بعده",
        "en": "Isa's glad tidings of a messenger after him"
    },
    "61:14": {
        "ar": "أنصار الله كالحواريين",
        "en": "Helpers of Allah like the disciples"
    },
}

# Topic descriptions for Prophet Musa (Moses) - موسى عليه السلام
MUSA_TOPICS = {
    "2:51": {
        "ar": "مواعدة موسى أربعين ليلة",
        "en": "Moses' appointment for forty nights"
    },
    "2:53": {
        "ar": "إيتاء موسى الكتاب والفرقان",
        "en": "Giving Moses the Scripture and criterion"
    },
    "2:54": {
        "ar": "توبة قوم موسى من عبادة العجل",
        "en": "Repentance of Moses' people from calf worship"
    },
    "2:55": {
        "ar": "طلب رؤية الله جهرة",
        "en": "Asking to see Allah openly"
    },
    "2:60": {
        "ar": "استسقاء موسى لقومه",
        "en": "Moses seeking water for his people"
    },
    "2:61": {
        "ar": "طلب قوم موسى ألوان الطعام",
        "en": "Moses' people asking for variety of food"
    },
    "2:67": {
        "ar": "قصة البقرة",
        "en": "The story of the cow"
    },
    "2:87": {
        "ar": "إيتاء موسى الكتاب",
        "en": "Giving Moses the Scripture"
    },
    "2:92": {
        "ar": "موسى جاء بالبينات",
        "en": "Moses came with clear signs"
    },
    "2:108": {
        "ar": "سؤال موسى كسؤال فرعون",
        "en": "Questioning like Pharaoh questioned Moses"
    },
    "7:103": {
        "ar": "إرسال موسى إلى فرعون",
        "en": "Sending Moses to Pharaoh"
    },
    "7:117": {
        "ar": "عصا موسى تلقف السحر",
        "en": "Moses' staff swallowing the magic"
    },
    "7:142": {
        "ar": "مواعدة موسى على الطور",
        "en": "Moses' appointment at Mount Tur"
    },
    "7:143": {
        "ar": "موسى يطلب رؤية الله",
        "en": "Moses asking to see Allah"
    },
    "7:150": {
        "ar": "غضب موسى من عبادة العجل",
        "en": "Moses' anger at calf worship"
    },
    "7:154": {
        "ar": "الألواح فيها هدى ورحمة",
        "en": "The tablets containing guidance and mercy"
    },
    "7:155": {
        "ar": "اختيار موسى سبعين رجلاً",
        "en": "Moses choosing seventy men"
    },
    "10:75": {
        "ar": "إرسال موسى وهارون إلى فرعون",
        "en": "Sending Moses and Aaron to Pharaoh"
    },
    "10:84": {
        "ar": "دعوة موسى قومه للتوكل",
        "en": "Moses calling his people to trust Allah"
    },
    "11:96": {
        "ar": "إرسال موسى بآيات الله",
        "en": "Sending Moses with Allah's signs"
    },
    "14:5": {
        "ar": "إرسال موسى بالآيات",
        "en": "Sending Moses with the signs"
    },
    "17:101": {
        "ar": "إيتاء موسى تسع آيات",
        "en": "Giving Moses nine signs"
    },
    "18:60": {
        "ar": "موسى والعبد الصالح",
        "en": "Moses and the righteous servant"
    },
    "19:51": {
        "ar": "موسى كان مخلصاً نبياً رسولاً",
        "en": "Moses was chosen, a prophet and messenger"
    },
    "20:9": {
        "ar": "قصة موسى في سورة طه",
        "en": "Story of Moses in Surah Ta-Ha"
    },
    "20:36": {
        "ar": "استجابة دعاء موسى",
        "en": "Answering Moses' supplication"
    },
    "20:77": {
        "ar": "إسراء بني إسرائيل",
        "en": "Journey of Children of Israel"
    },
    "26:10": {
        "ar": "نداء الله لموسى",
        "en": "Allah's call to Moses"
    },
    "27:7": {
        "ar": "موسى يرى النار",
        "en": "Moses seeing the fire"
    },
    "28:3": {
        "ar": "قصة موسى وفرعون بالحق",
        "en": "True story of Moses and Pharaoh"
    },
    "28:7": {
        "ar": "وحي الله لأم موسى",
        "en": "Allah's inspiration to Moses' mother"
    },
    "28:15": {
        "ar": "قتل موسى للقبطي",
        "en": "Moses killing the Copt"
    },
    "28:29": {
        "ar": "موسى يرى ناراً من جانب الطور",
        "en": "Moses seeing fire at Mount Tur"
    },
    "28:43": {
        "ar": "إيتاء موسى الكتاب",
        "en": "Giving Moses the Scripture"
    },
    "28:76": {
        "ar": "قصة قارون مع قوم موسى",
        "en": "Story of Qarun with Moses' people"
    },
    "37:114": {
        "ar": "المنة على موسى وهارون",
        "en": "Favor upon Moses and Aaron"
    },
    "40:23": {
        "ar": "إرسال موسى بالآيات والسلطان",
        "en": "Sending Moses with signs and authority"
    },
    "40:26": {
        "ar": "فرعون يريد قتل موسى",
        "en": "Pharaoh wanting to kill Moses"
    },
    "43:46": {
        "ar": "إرسال موسى إلى فرعون",
        "en": "Sending Moses to Pharaoh"
    },
    "44:17": {
        "ar": "فتنة قوم فرعون قبل موسى",
        "en": "Trial of Pharaoh's people before Moses"
    },
    "46:12": {
        "ar": "كتاب موسى إماماً ورحمة",
        "en": "Moses' book as a guide and mercy"
    },
    "51:38": {
        "ar": "إرسال موسى إلى فرعون",
        "en": "Sending Moses to Pharaoh"
    },
    "79:15": {
        "ar": "حديث موسى في سورة النازعات",
        "en": "Story of Moses in Surah An-Nazi'at"
    },
}

# Topic descriptions for Prophet Ibrahim (Abraham) - إبراهيم عليه السلام
IBRAHIM_TOPICS = {
    "2:124": {
        "ar": "إمامة إبراهيم للناس",
        "en": "Ibrahim as leader of mankind"
    },
    "2:125": {
        "ar": "البيت الحرام مثابة للناس",
        "en": "The Sacred House as a place of return"
    },
    "2:126": {
        "ar": "دعاء إبراهيم لمكة",
        "en": "Ibrahim's supplication for Makkah"
    },
    "2:127": {
        "ar": "بناء إبراهيم وإسماعيل الكعبة",
        "en": "Ibrahim and Ismail building the Kaaba"
    },
    "2:130": {
        "ar": "ملة إبراهيم الحنيفية",
        "en": "The religion of Ibrahim the upright"
    },
    "2:132": {
        "ar": "وصية إبراهيم ويعقوب",
        "en": "Testament of Ibrahim and Yaqub"
    },
    "2:135": {
        "ar": "اتباع ملة إبراهيم حنيفاً",
        "en": "Following Ibrahim's upright religion"
    },
    "2:136": {
        "ar": "الإيمان بما أنزل على إبراهيم",
        "en": "Believing in what was revealed to Ibrahim"
    },
    "2:140": {
        "ar": "إبراهيم وأبناؤه لم يكونوا يهوداً",
        "en": "Ibrahim and his sons were not Jews"
    },
    "2:258": {
        "ar": "محاجة إبراهيم للنمرود",
        "en": "Ibrahim's argument with Nimrod"
    },
    "2:260": {
        "ar": "إبراهيم يسأل عن إحياء الموتى",
        "en": "Ibrahim asking about resurrection"
    },
    "3:33": {
        "ar": "اصطفاء آل إبراهيم",
        "en": "Choosing the family of Ibrahim"
    },
    "3:65": {
        "ar": "إبراهيم لم يكن يهودياً ولا نصرانياً",
        "en": "Ibrahim was neither Jew nor Christian"
    },
    "3:67": {
        "ar": "إبراهيم كان حنيفاً مسلماً",
        "en": "Ibrahim was upright, a Muslim"
    },
    "3:68": {
        "ar": "أولى الناس بإبراهيم",
        "en": "Those closest to Ibrahim"
    },
    "3:84": {
        "ar": "الإيمان بما أنزل على إبراهيم",
        "en": "Believing in what was revealed to Ibrahim"
    },
    "3:95": {
        "ar": "اتباع ملة إبراهيم حنيفاً",
        "en": "Following Ibrahim's upright religion"
    },
    "3:97": {
        "ar": "مقام إبراهيم",
        "en": "The Station of Ibrahim"
    },
    "4:54": {
        "ar": "ما آتى الله آل إبراهيم",
        "en": "What Allah gave the family of Ibrahim"
    },
    "4:125": {
        "ar": "إبراهيم خليل الله",
        "en": "Ibrahim as Allah's friend"
    },
    "4:163": {
        "ar": "الوحي إلى إبراهيم",
        "en": "Revelation to Ibrahim"
    },
    "6:74": {
        "ar": "إبراهيم يدعو أباه للتوحيد",
        "en": "Ibrahim calling his father to monotheism"
    },
    "6:75": {
        "ar": "إبراهيم يتفكر في ملكوت السماوات",
        "en": "Ibrahim contemplating the heavens"
    },
    "6:83": {
        "ar": "حجة إبراهيم على قومه",
        "en": "Ibrahim's argument against his people"
    },
    "9:70": {
        "ar": "قوم إبراهيم",
        "en": "The people of Ibrahim"
    },
    "9:114": {
        "ar": "استغفار إبراهيم لأبيه",
        "en": "Ibrahim's prayer for his father"
    },
    "11:69": {
        "ar": "ضيف إبراهيم الملائكة",
        "en": "Ibrahim's angelic guests"
    },
    "11:74": {
        "ar": "إبراهيم يجادل في قوم لوط",
        "en": "Ibrahim arguing for Lot's people"
    },
    "11:75": {
        "ar": "صفات إبراهيم الحميدة",
        "en": "Ibrahim's praiseworthy qualities"
    },
    "14:35": {
        "ar": "دعاء إبراهيم لمكة",
        "en": "Ibrahim's supplication for Makkah"
    },
    "14:37": {
        "ar": "إبراهيم يسكن ذريته بمكة",
        "en": "Ibrahim settling his offspring in Makkah"
    },
    "14:39": {
        "ar": "شكر إبراهيم على الذرية",
        "en": "Ibrahim's gratitude for offspring"
    },
    "14:40": {
        "ar": "دعاء إبراهيم لإقامة الصلاة",
        "en": "Ibrahim's prayer for establishing prayer"
    },
    "15:51": {
        "ar": "قصة ضيف إبراهيم",
        "en": "Story of Ibrahim's guests"
    },
    "16:120": {
        "ar": "إبراهيم كان أمة قانتاً",
        "en": "Ibrahim was a nation, devoutly obedient"
    },
    "16:123": {
        "ar": "اتباع ملة إبراهيم",
        "en": "Following the religion of Ibrahim"
    },
    "19:41": {
        "ar": "إبراهيم صديقاً نبياً",
        "en": "Ibrahim as truthful prophet"
    },
    "19:46": {
        "ar": "أبو إبراهيم يهدده",
        "en": "Ibrahim's father threatening him"
    },
    "21:51": {
        "ar": "رشد إبراهيم",
        "en": "Ibrahim's right guidance"
    },
    "21:62": {
        "ar": "إبراهيم يحطم الأصنام",
        "en": "Ibrahim breaking the idols"
    },
    "21:68": {
        "ar": "إلقاء إبراهيم في النار",
        "en": "Ibrahim thrown into the fire"
    },
    "21:69": {
        "ar": "النار برداً وسلاماً",
        "en": "The fire becoming cool and safe"
    },
    "22:26": {
        "ar": "تبوئة إبراهيم مكان البيت",
        "en": "Showing Ibrahim the site of the House"
    },
    "22:43": {
        "ar": "قوم إبراهيم",
        "en": "The people of Ibrahim"
    },
    "22:78": {
        "ar": "ملة إبراهيم",
        "en": "The religion of Ibrahim"
    },
    "26:69": {
        "ar": "نبأ إبراهيم",
        "en": "The news of Ibrahim"
    },
    "29:16": {
        "ar": "إبراهيم يدعو قومه",
        "en": "Ibrahim calling his people"
    },
    "29:25": {
        "ar": "إبراهيم ينهى عن عبادة الأوثان",
        "en": "Ibrahim forbidding idol worship"
    },
    "37:83": {
        "ar": "إبراهيم من شيعة نوح",
        "en": "Ibrahim among Noah's followers"
    },
    "37:99": {
        "ar": "هجرة إبراهيم",
        "en": "Ibrahim's migration"
    },
    "37:102": {
        "ar": "ذبح إبراهيم لابنه",
        "en": "Ibrahim's sacrifice of his son"
    },
    "37:109": {
        "ar": "السلام على إبراهيم",
        "en": "Peace upon Ibrahim"
    },
    "38:45": {
        "ar": "ذكر إبراهيم وإسحاق ويعقوب",
        "en": "Mention of Ibrahim, Ishaq and Yaqub"
    },
    "42:13": {
        "ar": "شرع الدين لإبراهيم",
        "en": "Religion ordained for Ibrahim"
    },
    "43:26": {
        "ar": "براءة إبراهيم من المشركين",
        "en": "Ibrahim's disavowal of polytheists"
    },
    "51:24": {
        "ar": "حديث ضيف إبراهيم",
        "en": "Story of Ibrahim's honored guests"
    },
    "53:37": {
        "ar": "صحف إبراهيم",
        "en": "Scriptures of Ibrahim"
    },
    "57:26": {
        "ar": "النبوة في ذرية إبراهيم",
        "en": "Prophethood in Ibrahim's descendants"
    },
    "60:4": {
        "ar": "أسوة حسنة في إبراهيم",
        "en": "Good example in Ibrahim"
    },
    "87:19": {
        "ar": "صحف إبراهيم وموسى",
        "en": "Scriptures of Ibrahim and Moses"
    },
}

# Topic descriptions for places
PLACE_TOPICS = {
    # مصر (Egypt)
    "place_misr": {
        "2:61": {
            "ar": "طلب العودة إلى مصر",
            "en": "Requesting return to Egypt"
        },
        "10:87": {
            "ar": "السكنى في مصر",
            "en": "Dwelling in Egypt"
        },
        "12:21": {
            "ar": "يوسف في مصر",
            "en": "Yusuf in Egypt"
        },
        "12:99": {
            "ar": "دخول مصر بأمان",
            "en": "Entering Egypt in safety"
        },
        "43:51": {
            "ar": "فرعون ملك مصر",
            "en": "Pharaoh king of Egypt"
        },
    },
    # مكة (Makkah)
    "place_makkah": {
        "3:96": {
            "ar": "أول بيت وضع للناس ببكة",
            "en": "First house established for mankind in Bakkah"
        },
        "48:24": {
            "ar": "النصر ببطن مكة",
            "en": "Victory in the valley of Makkah"
        },
    },
}

# Map concept_id to topic mapping
CONCEPT_TOPICS = {
    "person_isa": ISA_TOPICS,
    "person_musa": MUSA_TOPICS,
    "person_ibrahim": IBRAHIM_TOPICS,
    **PLACE_TOPICS,
}


def parse_verse_ref(verse_ref: str) -> tuple[int, int]:
    """Parse verse reference like '2:87' into (sura_no, ayah_start)."""
    parts = verse_ref.split(":")
    return int(parts[0]), int(parts[1])


async def populate_topics():
    """Populate topic descriptions for all concept occurrences."""

    # Create async engine
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        total_updated = 0

        for concept_id, topics in CONCEPT_TOPICS.items():
            logger.info(f"Processing concept: {concept_id}")

            for verse_ref, descriptions in topics.items():
                # Parse verse reference into sura_no and ayah_start
                sura_no, ayah_start = parse_verse_ref(verse_ref)

                # Update occurrences for this verse
                result = await session.execute(
                    update(Occurrence)
                    .where(
                        Occurrence.concept_id == concept_id,
                        Occurrence.sura_no == sura_no,
                        Occurrence.ayah_start == ayah_start
                    )
                    .values(
                        context_ar=descriptions["ar"],
                        context_en=descriptions["en"]
                    )
                )

                if result.rowcount > 0:
                    total_updated += result.rowcount
                    logger.info(f"  Updated {verse_ref}: {descriptions['ar']}")

        await session.commit()
        logger.info(f"Total occurrences updated: {total_updated}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(populate_topics())
