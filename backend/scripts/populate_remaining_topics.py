"""
Populate remaining topic names for theme_sabr (5) and theme_taqwa (95) occurrences.
This completes the 100% coverage goal.
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update
from app.models.concept import Occurrence
from app.core.config import settings


# =============================================================================
# REMAINING theme_sabr (5 verses)
# =============================================================================
THEME_SABR_REMAINING = {
    "14:12": {"ar": "صبر الأنبياء على أذى قومهم", "en": "Prophets' patience with their people's harm"},
    "16:42": {"ar": "الذين صبروا وتوكلوا على ربهم", "en": "Those who patiently persevere and trust in their Lord"},
    "16:110": {"ar": "الصبر بعد الفتنة والجهاد", "en": "Patience after trial and striving"},
    "29:58": {"ar": "أجر الصابرين المتوكلين", "en": "Reward for patient believers"},
    "31:31": {"ar": "الصبر من عزم الأمور", "en": "Patience is from determination in affairs"},
}


# =============================================================================
# REMAINING theme_taqwa (95 verses)
# =============================================================================
THEME_TAQWA_REMAINING = {
    # Surah 11 - Hud
    "11:49": {"ar": "العاقبة للمتقين", "en": "The final outcome is for the pious"},
    "11:78": {"ar": "اتقوا الله في ضيفي", "en": "Fear Allah regarding my guests"},

    # Surah 14 - Ibrahim
    "14:16": {"ar": "شراب العذاب لمن أعرض", "en": "Drink of torment for those who turn away"},
    "14:26": {"ar": "الكلمة الخبيثة كشجرة خبيثة", "en": "Evil word like an evil tree"},

    # Surah 17 - Al-Isra
    "17:59": {"ar": "آيات التخويف والتقوى", "en": "Signs of warning and piety"},

    # Surah 20 - Taha
    "20:113": {"ar": "قرآن عربي لعلهم يتقون", "en": "Arabic Quran that they may become pious"},
    "20:132": {"ar": "أمر الأهل بالصلاة والتقوى", "en": "Commanding family to prayer and piety"},

    # Surah 21 - Al-Anbiya
    "21:48": {"ar": "التوراة والفرقان للمتقين", "en": "Torah and criterion for the pious"},
    "21:49": {"ar": "الذين يخشون ربهم بالغيب", "en": "Those who fear their Lord unseen"},

    # Surah 22 - Al-Hajj
    "22:1": {"ar": "يا أيها الناس اتقوا ربكم", "en": "O mankind, fear your Lord"},
    "22:32": {"ar": "تعظيم شعائر الله من تقوى القلوب", "en": "Honoring Allah's rites is from hearts' piety"},
    "22:37": {"ar": "لن ينال الله لحومها ولكن يناله التقوى", "en": "Allah receives not meat but piety"},

    # Surah 23 - Al-Mu'minun
    "23:23": {"ar": "نوح يدعو قومه لعبادة الله", "en": "Noah calls his people to worship Allah"},
    "23:32": {"ar": "رسول من أنفسهم يدعو للتقوى", "en": "A messenger from among them calling to piety"},
    "23:49": {"ar": "كتاب موسى لعلهم يهتدون", "en": "Moses' book that they may be guided"},
    "23:52": {"ar": "أمتكم أمة واحدة فاتقون", "en": "Your nation is one nation, so fear Me"},
    "23:87": {"ar": "اعتراف بربوبية الله", "en": "Acknowledgment of Allah's lordship"},

    # Surah 24 - An-Nur
    "24:52": {"ar": "من يطع الله ورسوله ويتق فأولئك الفائزون", "en": "Who obeys Allah and fears Him succeeds"},

    # Surah 25 - Al-Furqan
    "25:15": {"ar": "جنة الخلد للمتقين", "en": "Eternal paradise for the pious"},
    "25:74": {"ar": "دعاء المتقين بالذرية الصالحة", "en": "Pious pray for righteous offspring"},

    # Surah 26 - Ash-Shu'ara
    "26:11": {"ar": "قوم فرعون ألا يتقون", "en": "Pharaoh's people - will they not fear?"},
    "26:90": {"ar": "الجنة أزلفت للمتقين", "en": "Paradise brought near for the pious"},
    "26:108": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:110": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:124": {"ar": "هود يدعو قومه للتقوى", "en": "Hud calls his people to piety"},
    "26:126": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:131": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:132": {"ar": "واتقوا الذي أمدكم بما تعلمون", "en": "Fear Him who provided you with what you know"},
    "26:142": {"ar": "صالح يدعو ثمود للتقوى", "en": "Salih calls Thamud to piety"},
    "26:144": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:150": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:161": {"ar": "لوط يدعو قومه للتقوى", "en": "Lot calls his people to piety"},
    "26:163": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:177": {"ar": "شعيب يدعو أصحاب الأيكة", "en": "Shuayb calls the companions of the thicket"},
    "26:179": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},
    "26:184": {"ar": "واتقوا الذي خلقكم والجبلة الأولين", "en": "Fear Him who created you and former generations"},

    # Surah 27 - An-Naml
    "27:53": {"ar": "أنجينا الذين آمنوا وكانوا يتقون", "en": "We saved those who believed and were pious"},

    # Surah 28 - Al-Qasas
    "28:83": {"ar": "الدار الآخرة للذين لا يريدون علوا", "en": "Hereafter for those not seeking dominance"},

    # Surah 29 - Al-Ankabut
    "29:16": {"ar": "إبراهيم يدعو قومه لعبادة الله", "en": "Ibrahim calls his people to worship Allah"},

    # Surah 31 - Luqman
    "31:33": {"ar": "يا أيها الناس اتقوا ربكم", "en": "O mankind, fear your Lord"},

    # Surah 32 - As-Sajdah
    "32:16": {"ar": "تتجافى جنوبهم عن المضاجع خوفا وطمعا", "en": "Their sides forsake beds in fear and hope"},

    # Surah 33 - Al-Ahzab
    "33:1": {"ar": "يا أيها النبي اتق الله", "en": "O Prophet, fear Allah"},
    "33:32": {"ar": "نساء النبي والتقوى في القول", "en": "Prophet's wives and piety in speech"},
    "33:37": {"ar": "تخشى الناس والله أحق أن تخشاه", "en": "Fearing people when Allah deserves more fear"},
    "33:55": {"ar": "لا جناح في القرابة", "en": "No blame regarding relatives"},
    "33:70": {"ar": "يا أيها الذين آمنوا اتقوا الله", "en": "O believers, fear Allah"},

    # Surah 35 - Fatir
    "35:18": {"ar": "إنما تنذر الذين يخشون ربهم بالغيب", "en": "You only warn those who fear their Lord unseen"},
    "35:28": {"ar": "إنما يخشى الله من عباده العلماء", "en": "Only the knowledgeable truly fear Allah"},

    # Surah 36 - Ya-Sin
    "36:11": {"ar": "إنما تنذر من اتبع الذكر", "en": "You only warn who follows the reminder"},

    # Surah 37 - As-Saffat
    "37:124": {"ar": "إلياس يدعو قومه ألا يتقون", "en": "Elias asks his people - will you not fear?"},

    # Surah 38 - Sad
    "38:28": {"ar": "لا نجعل المتقين كالفجار", "en": "We do not make pious like wicked"},

    # Surah 39 - Az-Zumar
    "39:13": {"ar": "إني أخاف إن عصيت ربي عذاب يوم عظيم", "en": "I fear punishment of a tremendous day"},
    "39:16": {"ar": "ظلل من النار من فوقهم ومن تحتهم", "en": "Canopies of fire above and below"},
    "39:24": {"ar": "من يتقي بوجهه سوء العذاب", "en": "Who shields his face from evil punishment"},
    "39:28": {"ar": "قرآنا عربيا لعلهم يتقون", "en": "Arabic Quran that they may be pious"},
    "39:57": {"ar": "حسرة يوم القيامة", "en": "Regret on the Day of Resurrection"},
    "39:61": {"ar": "وينجي الله الذين اتقوا بمفازتهم", "en": "Allah saves the pious by their success"},
    "39:73": {"ar": "وسيق الذين اتقوا ربهم إلى الجنة زمرا", "en": "The pious driven to paradise in groups"},

    # Surah 40 - Ghafir
    "40:9": {"ar": "وقهم السيئات ذلك الفوز العظيم", "en": "Protect them from evils - the great success"},

    # Surah 41 - Fussilat
    "41:18": {"ar": "نجينا الذين آمنوا وكانوا يتقون", "en": "We saved those who believed and were pious"},

    # Surah 43 - Az-Zukhruf
    "43:35": {"ar": "وزخرفا وإن كل ذلك لما متاع الدنيا", "en": "Adornment - all is but worldly provision"},
    "43:63": {"ar": "فاتقوا الله وأطيعون", "en": "Fear Allah and obey me"},

    # Surah 45 - Al-Jathiyah
    "45:19": {"ar": "إنهم لن يغنوا عنك من الله شيئا", "en": "They will not avail you against Allah"},

    # Surah 48 - Al-Fath
    "48:5": {"ar": "جنات تجري من تحتها الأنهار للمؤمنين", "en": "Gardens with rivers flowing for believers"},
    "48:26": {"ar": "كلمة التقوى وكانوا أحق بها", "en": "Word of piety - they were most worthy"},

    # Surah 49 - Al-Hujurat
    "49:1": {"ar": "لا تقدموا بين يدي الله ورسوله واتقوا الله", "en": "Do not put forward before Allah and His messenger"},
    "49:3": {"ar": "الذين يغضون أصواتهم عند رسول الله", "en": "Those who lower voices before Allah's messenger"},
    "49:10": {"ar": "إنما المؤمنون إخوة فاتقوا الله", "en": "Believers are brothers - so fear Allah"},
    "49:12": {"ar": "اجتنبوا كثيرا من الظن واتقوا الله", "en": "Avoid much suspicion and fear Allah"},

    # Surah 53 - An-Najm
    "53:32": {"ar": "فلا تزكوا أنفسكم هو أعلم بمن اتقى", "en": "Do not claim purity - He knows the pious"},

    # Surah 54 - Al-Qamar
    "54:15": {"ar": "ولقد تركناها آية فهل من مدكر", "en": "We left it as a sign - any who remember?"},

    # Surah 57 - Al-Hadid
    "57:21": {"ar": "سابقوا إلى مغفرة من ربكم وجنة", "en": "Race to forgiveness and paradise"},
    "57:28": {"ar": "يا أيها الذين آمنوا اتقوا الله", "en": "O believers, fear Allah"},

    # Surah 58 - Al-Mujadilah
    "58:9": {"ar": "تناجوا بالبر والتقوى", "en": "Converse in righteousness and piety"},

    # Surah 59 - Al-Hashr
    "59:7": {"ar": "واتقوا الله إن الله شديد العقاب", "en": "Fear Allah - severe in punishment"},
    "59:18": {"ar": "يا أيها الذين آمنوا اتقوا الله", "en": "O believers, fear Allah"},

    # Surah 60 - Al-Mumtahanah
    "60:11": {"ar": "واتقوا الله الذي أنتم به مؤمنون", "en": "Fear Allah in whom you believe"},

    # Surah 64 - At-Taghabun
    "64:16": {"ar": "فاتقوا الله ما استطعتم", "en": "Fear Allah as much as you can"},

    # Surah 65 - At-Talaq
    "65:1": {"ar": "يا أيها النبي إذا طلقتم النساء", "en": "O Prophet, regarding divorce of women"},
    "65:2": {"ar": "ومن يتق الله يجعل له مخرجا", "en": "Whoever fears Allah - He makes a way out"},
    "65:4": {"ar": "ومن يتق الله يجعل له من أمره يسرا", "en": "Whoever fears Allah - He makes ease"},
    "65:5": {"ar": "ومن يتق الله يكفر عنه سيئاته", "en": "Whoever fears Allah - He removes sins"},
    "65:10": {"ar": "أعد الله لهم عذابا شديدا فاتقوا الله", "en": "Allah prepared severe punishment - so fear Him"},

    # Surah 66 - At-Tahrim
    "66:6": {"ar": "قوا أنفسكم وأهليكم نارا", "en": "Protect yourselves and families from fire"},

    # Surah 69 - Al-Haqqah
    "69:48": {"ar": "وإنه لتذكرة للمتقين", "en": "It is a reminder for the pious"},

    # Surah 71 - Nuh
    "71:3": {"ar": "اعبدوا الله واتقوه وأطيعون", "en": "Worship Allah, fear Him, and obey me"},

    # Surah 72 - Al-Jinn
    "72:13": {"ar": "فمن يؤمن بربه فلا يخاف بخسا ولا رهقا", "en": "Who believes in Lord fears no deprivation"},

    # Surah 73 - Al-Muzzammil
    "73:17": {"ar": "فكيف تتقون إن كفرتم يوما", "en": "How will you fear if you disbelieve?"},

    # Surah 74 - Al-Muddaththir
    "74:56": {"ar": "هو أهل التقوى وأهل المغفرة", "en": "He is worthy of fear and forgiveness"},

    # Surah 76 - Al-Insan
    "76:10": {"ar": "إنا نخاف من ربنا يوما عبوسا قمطريرا", "en": "We fear from our Lord a distressful day"},
    "76:11": {"ar": "فوقاهم الله شر ذلك اليوم", "en": "Allah protected them from that day's evil"},

    # Surah 79 - An-Nazi'at
    "79:40": {"ar": "وأما من خاف مقام ربه ونهى النفس", "en": "Who feared standing before Lord and restrained self"},

    # Surah 91 - Ash-Shams
    "91:8": {"ar": "فألهمها فجورها وتقواها", "en": "Inspired it with wickedness and piety"},

    # Surah 96 - Al-Alaq
    "96:12": {"ar": "أو أمر بالتقوى", "en": "Or enjoined piety"},

    # Surah 98 - Al-Bayyinah
    "98:8": {"ar": "ذلك لمن خشي ربه", "en": "That is for whoever feared his Lord"},
}


def parse_verse_ref(ref: str) -> tuple[int, int]:
    """Parse '2:31' into (2, 31)."""
    sura, ayah = ref.split(":")
    return int(sura), int(ayah)


async def populate_remaining_topics():
    """Populate remaining topic names."""
    # Create async engine
    db_url = settings.database_url
    if "postgresql://" in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated_sabr = 0
    updated_taqwa = 0

    async with async_session() as session:
        # Update theme_sabr
        print("Updating theme_sabr topics...")
        for verse_ref, topics in THEME_SABR_REMAINING.items():
            sura_no, ayah_start = parse_verse_ref(verse_ref)
            result = await session.execute(
                update(Occurrence)
                .where(
                    Occurrence.concept_id == "theme_sabr",
                    Occurrence.sura_no == sura_no,
                    Occurrence.ayah_start == ayah_start
                )
                .values(
                    context_ar=topics["ar"],
                    context_en=topics["en"]
                )
            )
            if result.rowcount > 0:
                updated_sabr += result.rowcount
                print(f"  ✓ {verse_ref}: {topics['en']}")

        # Update theme_taqwa
        print("\nUpdating theme_taqwa topics...")
        for verse_ref, topics in THEME_TAQWA_REMAINING.items():
            sura_no, ayah_start = parse_verse_ref(verse_ref)
            result = await session.execute(
                update(Occurrence)
                .where(
                    Occurrence.concept_id == "theme_taqwa",
                    Occurrence.sura_no == sura_no,
                    Occurrence.ayah_start == ayah_start
                )
                .values(
                    context_ar=topics["ar"],
                    context_en=topics["en"]
                )
            )
            if result.rowcount > 0:
                updated_taqwa += result.rowcount
                print(f"  ✓ {verse_ref}: {topics['en']}")

        await session.commit()

    await engine.dispose()

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  theme_sabr:  {updated_sabr} occurrences updated")
    print(f"  theme_taqwa: {updated_taqwa} occurrences updated")
    print(f"  TOTAL:       {updated_sabr + updated_taqwa} occurrences updated")


if __name__ == "__main__":
    asyncio.run(populate_remaining_topics())
