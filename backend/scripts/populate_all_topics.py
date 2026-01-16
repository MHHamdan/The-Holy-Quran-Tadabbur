#!/usr/bin/env python3
"""
Comprehensive topic descriptions for ALL concept occurrences.
Based on Quranic scholarship and semantic analysis of each verse.

Usage:
    PYTHONPATH=. python scripts/populate_all_topics.py
"""
import asyncio
import logging
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.concept import Occurrence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# MIRACLE TOPICS
# ============================================================================

MIRACLE_TOPICS = {
    "miracle_ibrahim_fire": {
        "21:68": {"ar": "نجاة إبراهيم من النار", "en": "Ibrahim's salvation from the fire"},
    },
    "miracle_isa_blind": {
        "3:49": {"ar": "إبراء الأكمه والأبرص", "en": "Healing the blind and leper"},
        "5:110": {"ar": "شفاء الأكمه بإذن الله", "en": "Healing the blind by Allah's permission"},
    },
    "miracle_isa_cradle": {
        "3:46": {"ar": "كلام عيسى في المهد", "en": "Isa speaking in the cradle"},
        "5:110": {"ar": "تكليم الناس في المهد", "en": "Speaking to people in infancy"},
        "19:29": {"ar": "كلام المسيح رضيعاً", "en": "The infant Messiah speaking"},
    },
    "miracle_isa_dead": {
        "3:49": {"ar": "إحياء الموتى بإذن الله", "en": "Raising the dead by Allah's permission"},
        "5:110": {"ar": "إخراج الموتى من القبور", "en": "Bringing forth the dead"},
    },
    "miracle_moon_split": {
        "54:1": {"ar": "انشقاق القمر آية للنبي", "en": "The splitting of the moon as a sign"},
    },
    "miracle_musa_hand": {
        "7:108": {"ar": "يد موسى البيضاء", "en": "Moses' radiant white hand"},
        "20:22": {"ar": "آية اليد البيضاء", "en": "The sign of the white hand"},
        "26:33": {"ar": "إخراج اليد بيضاء للناظرين", "en": "The hand emerging white for observers"},
        "27:12": {"ar": "اليد البيضاء من غير سوء", "en": "The white hand without disease"},
        "28:32": {"ar": "اليد تخرج بيضاء من الجيب", "en": "The hand emerging white from the cloak"},
    },
    "miracle_musa_sea": {
        "20:77": {"ar": "شق البحر طريقاً يبساً", "en": "Striking a dry path through the sea"},
        "26:63": {"ar": "انفلاق البحر كالطود العظيم", "en": "The sea parting like great mountains"},
    },
    "miracle_musa_staff": {
        "7:107": {"ar": "عصا موسى تتحول ثعباناً", "en": "Moses' staff becoming a serpent"},
        "20:20": {"ar": "العصا تسعى حية", "en": "The staff moving as a snake"},
        "26:32": {"ar": "الثعبان المبين", "en": "The manifest serpent"},
        "27:10": {"ar": "العصا كأنها جان", "en": "The staff like a swift serpent"},
        "28:31": {"ar": "تحول العصا حية", "en": "The staff transforming into a snake"},
    },
    "miracle_quran": {
        "2:23": {"ar": "تحدي الإتيان بسورة مثله", "en": "Challenge to produce a similar surah"},
        "11:13": {"ar": "تحدي الإتيان بعشر سور", "en": "Challenge to produce ten surahs"},
        "17:88": {"ar": "عجز الإنس والجن عن مثله", "en": "Mankind and jinn unable to produce its like"},
    },
    "miracle_yunus_whale": {
        "21:87": {"ar": "نداء يونس في ظلمات البحر", "en": "Yunus calling from the darkness"},
        "37:139": {"ar": "التقام الحوت ليونس", "en": "The whale swallowing Yunus"},
    },
}

# ============================================================================
# NATION TOPICS
# ============================================================================

NATION_TOPICS = {
    "nation_aad": {
        "7:65": {"ar": "دعوة هود لقوم عاد", "en": "Hud's call to the people of Aad"},
        "7:74": {"ar": "التذكير بنعم الله على عاد", "en": "Reminder of Allah's blessings on Aad"},
        "9:70": {"ar": "خبر الأمم السابقة ومنها عاد", "en": "News of previous nations including Aad"},
        "11:50": {"ar": "إرسال هود إلى عاد", "en": "Hud sent to Aad"},
        "11:59": {"ar": "جحود عاد بآيات ربهم", "en": "Aad's rejection of their Lord's signs"},
        "14:9": {"ar": "نبأ قوم نوح وعاد وثمود", "en": "News of Noah's, Aad's and Thamud's people"},
        "22:42": {"ar": "تكذيب عاد لأنبيائها", "en": "Aad's denial of their prophets"},
        "25:38": {"ar": "هلاك عاد وثمود", "en": "Destruction of Aad and Thamud"},
        "26:123": {"ar": "تكذيب عاد للمرسلين", "en": "Aad's rejection of the messengers"},
        "29:38": {"ar": "إغواء الشيطان لعاد وثمود", "en": "Satan's deception of Aad and Thamud"},
        "38:12": {"ar": "ذكر قوم عاد في الجبابرة", "en": "Mentioning Aad among the mighty"},
        "40:31": {"ar": "عاد كمثل قوم نوح وفرعون", "en": "Aad like Noah's people and Pharaoh"},
        "41:13": {"ar": "صاعقة كصاعقة عاد وثمود", "en": "A thunderbolt like that of Aad and Thamud"},
        "41:15": {"ar": "استكبار قوم عاد", "en": "Arrogance of the people of Aad"},
        "46:21": {"ar": "قصة هود مع عاد", "en": "Story of Hud with Aad"},
        "50:13": {"ar": "ذكر عاد مع المكذبين", "en": "Mentioning Aad among the deniers"},
        "51:41": {"ar": "الريح العقيم على عاد", "en": "The barren wind upon Aad"},
        "53:50": {"ar": "إهلاك عاد الأولى", "en": "Destruction of the ancient Aad"},
        "54:18": {"ar": "تكذيب عاد للنذر", "en": "Aad's denial of the warnings"},
        "69:4": {"ar": "هلاك ثمود وعاد بالطاغية", "en": "Thamud and Aad destroyed by catastrophe"},
        "69:6": {"ar": "إهلاك عاد بريح صرصر", "en": "Aad destroyed by a screaming wind"},
        "89:6": {"ar": "إرم ذات العماد في عاد", "en": "Iram of the pillars in Aad"},
    },
    "nation_bani_israil": {
        "2:40": {"ar": "نداء بني إسرائيل للوفاء", "en": "Calling Children of Israel to fulfill covenant"},
        "2:47": {"ar": "تفضيل بني إسرائيل على العالمين", "en": "Favor of Children of Israel over nations"},
        "2:83": {"ar": "ميثاق بني إسرائيل", "en": "Covenant of Children of Israel"},
        "2:122": {"ar": "التذكير بالتفضيل", "en": "Reminder of the favor granted"},
        "3:49": {"ar": "رسالة عيسى لبني إسرائيل", "en": "Isa's message to Children of Israel"},
        "5:12": {"ar": "ميثاق الله مع بني إسرائيل", "en": "Allah's covenant with Children of Israel"},
        "5:70": {"ar": "عهود بني إسرائيل وتكذيبهم", "en": "Covenants and denials of Children of Israel"},
        "7:105": {"ar": "رسالة موسى لبني إسرائيل", "en": "Moses' mission for Children of Israel"},
        "7:134": {"ar": "استغاثة بني إسرائيل", "en": "Children of Israel seeking help"},
        "10:90": {"ar": "نجاة بني إسرائيل من فرعون", "en": "Saving Children of Israel from Pharaoh"},
        "17:2": {"ar": "إيتاء موسى الكتاب هدى لبني إسرائيل", "en": "Giving Moses the Book as guidance"},
        "17:4": {"ar": "قضاء الله على بني إسرائيل", "en": "Allah's decree concerning Children of Israel"},
        "20:47": {"ar": "دعوة موسى لإرسال بني إسرائيل", "en": "Moses calling for release of Israelites"},
        "26:17": {"ar": "المطالبة بإرسال بني إسرائيل", "en": "Demanding release of Children of Israel"},
        "26:59": {"ar": "توريث بني إسرائيل الأرض", "en": "Inheriting the land to Children of Israel"},
        "27:76": {"ar": "القرآن يبين لبني إسرائيل", "en": "Quran clarifying for Children of Israel"},
        "32:23": {"ar": "إيتاء موسى الكتاب هدى", "en": "Giving Moses the Book as guidance"},
        "40:53": {"ar": "وراثة بني إسرائيل الكتاب", "en": "Children of Israel inheriting the Book"},
        "44:30": {"ar": "نجاة بني إسرائيل من العذاب", "en": "Saving Children of Israel from torment"},
        "45:16": {"ar": "الكتاب والحكم والنبوة لبني إسرائيل", "en": "Book, wisdom and prophethood for Israelites"},
        "46:10": {"ar": "شاهد من بني إسرائيل", "en": "A witness from Children of Israel"},
    },
    "nation_qawm_firaun": {
        "2:49": {"ar": "إنجاء بني إسرائيل من آل فرعون", "en": "Saving Israelites from Pharaoh's people"},
        "3:11": {"ar": "دأب آل فرعون في التكذيب", "en": "Pharaoh's people's habit of denial"},
        "7:103": {"ar": "إرسال موسى لفرعون وملئه", "en": "Moses sent to Pharaoh and his chiefs"},
        "7:130": {"ar": "ابتلاء آل فرعون بالسنين", "en": "Testing Pharaoh's people with famine"},
        "7:141": {"ar": "إنجاء بني إسرائيل من فرعون", "en": "Delivering Israelites from Pharaoh"},
        "8:52": {"ar": "عاقبة آل فرعون كعادة المكذبين", "en": "Pharaoh's fate like previous deniers"},
        "8:54": {"ar": "تكذيب آل فرعون بالآيات", "en": "Pharaoh's people denying the signs"},
        "10:75": {"ar": "استكبار فرعون وملئه", "en": "Arrogance of Pharaoh and his chiefs"},
        "10:83": {"ar": "خوف بني إسرائيل من فرعون", "en": "Israelites fearing Pharaoh"},
        "11:97": {"ar": "اتباع قوم فرعون أمر فرعون", "en": "Pharaoh's people following his command"},
        "14:6": {"ar": "إنجاء بني إسرائيل من آل فرعون", "en": "Saving Israelites from Pharaoh's tyranny"},
        "20:24": {"ar": "أمر موسى بالذهاب إلى فرعون", "en": "Moses commanded to go to Pharaoh"},
        "23:46": {"ar": "إرسال موسى وهارون لفرعون", "en": "Moses and Aaron sent to Pharaoh"},
        "27:12": {"ar": "موسى أمام فرعون بالآيات", "en": "Moses before Pharaoh with signs"},
        "28:3": {"ar": "قصة موسى وفرعون بالحق", "en": "True story of Moses and Pharaoh"},
        "28:32": {"ar": "موسى يدعو فرعون بالآيات", "en": "Moses calling Pharaoh with signs"},
        "28:38": {"ar": "استكبار فرعون وادعاء الربوبية", "en": "Pharaoh's arrogance claiming divinity"},
        "29:39": {"ar": "هلاك قارون وفرعون وهامان", "en": "Destruction of Qarun, Pharaoh and Haman"},
        "40:28": {"ar": "رجل من آل فرعون يكتم إيمانه", "en": "A believing man hiding his faith"},
        "40:46": {"ar": "عرض آل فرعون على النار", "en": "Pharaoh's people exposed to Fire"},
        "44:17": {"ar": "فتنة فرعون قبل موسى", "en": "Pharaoh's trial before Moses"},
        "50:13": {"ar": "ذكر آل فرعون مع المكذبين", "en": "Pharaoh's people among deniers"},
        "51:38": {"ar": "إرسال موسى لفرعون", "en": "Moses sent to Pharaoh"},
        "54:41": {"ar": "النذر التي جاءت آل فرعون", "en": "Warnings that came to Pharaoh's people"},
        "66:11": {"ar": "امرأة فرعون المؤمنة", "en": "Pharaoh's believing wife"},
        "69:9": {"ar": "جريمة فرعون ومن قبله", "en": "Crime of Pharaoh and predecessors"},
        "73:15": {"ar": "رسول إلى فرعون كموسى", "en": "A messenger to Pharaoh like Moses"},
        "79:17": {"ar": "أمر موسى بالذهاب لفرعون", "en": "Moses commanded to go to Pharaoh"},
        "85:18": {"ar": "جنود فرعون المهلكون", "en": "Pharaoh's destroyed forces"},
    },
    "nation_qawm_lut": {
        "7:80": {"ar": "فاحشة قوم لوط", "en": "The abomination of Lot's people"},
        "11:70": {"ar": "الملائكة ضيوف إبراهيم يخبرون عن لوط", "en": "Angels inform Ibrahim about Lot"},
        "11:77": {"ar": "مجيء الملائكة لقوم لوط", "en": "Angels coming to Lot's people"},
        "11:89": {"ar": "تحذير لوط قومه من مصير الأمم", "en": "Lot warning his people of nations' fate"},
        "15:59": {"ar": "نجاة آل لوط إلا امرأته", "en": "Saving Lot's family except his wife"},
        "15:67": {"ar": "استبشار قوم لوط بالضيوف", "en": "Lot's people excited about guests"},
        "21:74": {"ar": "حكم لوط وعلمه", "en": "Lot's judgment and knowledge"},
        "26:160": {"ar": "تكذيب قوم لوط للمرسلين", "en": "Lot's people denying the messengers"},
        "27:54": {"ar": "إتيان قوم لوط الفاحشة", "en": "Lot's people committing abomination"},
        "27:56": {"ar": "إخراج آل لوط المتطهرين", "en": "Expelling Lot's purified family"},
        "29:28": {"ar": "فاحشة قوم لوط السابقة", "en": "Unprecedented sin of Lot's people"},
        "29:33": {"ar": "خوف لوط على ضيوفه", "en": "Lot's fear for his guests"},
        "37:133": {"ar": "لوط من المرسلين", "en": "Lot among the messengers"},
        "38:13": {"ar": "قوم لوط مع الأحزاب المكذبة", "en": "Lot's people among denying factions"},
        "50:13": {"ar": "إخوان لوط من المكذبين", "en": "Brothers of Lot among deniers"},
        "54:33": {"ar": "تكذيب قوم لوط بالنذر", "en": "Lot's people denying warnings"},
        "54:34": {"ar": "حاصب على قوم لوط", "en": "Storm of stones upon Lot's people"},
    },
    "nation_qawm_nuh": {
        "7:64": {"ar": "تكذيب قوم نوح وإغراقهم", "en": "Noah's people's denial and drowning"},
        "10:71": {"ar": "قصة نوح مع قومه", "en": "Story of Noah with his people"},
        "11:25": {"ar": "إرسال نوح نذيراً لقومه", "en": "Noah sent as warner to his people"},
        "23:23": {"ar": "دعوة نوح قومه للتوحيد", "en": "Noah calling his people to monotheism"},
        "25:37": {"ar": "إغراق قوم نوح", "en": "Drowning of Noah's people"},
        "26:105": {"ar": "تكذيب قوم نوح للمرسلين", "en": "Noah's people denying messengers"},
        "29:14": {"ar": "نوح في قومه ألف سنة", "en": "Noah among his people a thousand years"},
        "37:75": {"ar": "نداء نوح ربه", "en": "Noah calling upon his Lord"},
        "50:12": {"ar": "تكذيب قوم نوح قبلهم", "en": "Noah's people denied before them"},
        "53:52": {"ar": "إهلاك قوم نوح الظالمين", "en": "Destroying Noah's wrongdoing people"},
        "54:9": {"ar": "تكذيب قوم نوح لعبدنا", "en": "Noah's people denying Our servant"},
        "71:1": {"ar": "إرسال نوح لقومه", "en": "Noah sent to his people"},
    },
    "nation_thamud": {
        "7:73": {"ar": "إرسال صالح لثمود", "en": "Salih sent to Thamud"},
        "7:78": {"ar": "الرجفة تأخذ ثمود", "en": "The earthquake seizing Thamud"},
        "9:70": {"ar": "ثمود مع الأمم المكذبة", "en": "Thamud among denying nations"},
        "11:61": {"ar": "دعوة صالح ثمود للتوحيد", "en": "Salih calling Thamud to monotheism"},
        "11:68": {"ar": "كأن ثمود لم يغنوا فيها", "en": "As if Thamud never dwelt there"},
        "11:95": {"ar": "لعن ثمود كمدين", "en": "Thamud cursed like Midian"},
        "14:9": {"ar": "نبأ ثمود مع عاد ونوح", "en": "News of Thamud with Aad and Noah"},
        "17:59": {"ar": "الناقة آية لثمود", "en": "The she-camel as sign for Thamud"},
        "22:42": {"ar": "تكذيب ثمود لنبيهم", "en": "Thamud denying their prophet"},
        "25:38": {"ar": "هلاك عاد وثمود", "en": "Destruction of Aad and Thamud"},
        "26:141": {"ar": "تكذيب ثمود للمرسلين", "en": "Thamud denying the messengers"},
        "27:45": {"ar": "إرسال صالح لثمود", "en": "Sending Salih to Thamud"},
        "29:38": {"ar": "ثمود مع عاد في الضلال", "en": "Thamud with Aad in misguidance"},
        "38:13": {"ar": "ثمود مع الأحزاب", "en": "Thamud among the factions"},
        "40:31": {"ar": "مصير ثمود كقوم نوح", "en": "Thamud's fate like Noah's people"},
        "41:13": {"ar": "صاعقة ثمود وعاد", "en": "Thunderbolt of Thamud and Aad"},
        "41:17": {"ar": "هداية ثمود ورفضهم", "en": "Thamud guided but they refused"},
        "50:12": {"ar": "ثمود من المكذبين السابقين", "en": "Thamud among previous deniers"},
        "51:43": {"ar": "عتو ثمود عن أمر ربهم", "en": "Thamud's defiance of their Lord"},
        "53:51": {"ar": "إهلاك ثمود فما أبقى", "en": "Destroying Thamud completely"},
        "54:23": {"ar": "تكذيب ثمود بالنذر", "en": "Thamud denying the warnings"},
        "69:4": {"ar": "إهلاك ثمود بالطاغية", "en": "Thamud destroyed by catastrophe"},
        "69:5": {"ar": "ثمود أهلكوا بالطاغية", "en": "Thamud destroyed by the overwhelming"},
        "85:18": {"ar": "ثمود مع فرعون المكذبين", "en": "Thamud with Pharaoh among deniers"},
        "89:9": {"ar": "ثمود الذين جابوا الصخر", "en": "Thamud who carved rocks"},
        "91:11": {"ar": "تكذيب ثمود بطغواها", "en": "Thamud's denial in their transgression"},
    },
}

# ============================================================================
# PERSON TOPICS (PROPHETS AND RIGHTEOUS)
# ============================================================================

PERSON_TOPICS = {
    "person_adam": {
        "2:31": {"ar": "تعليم آدم الأسماء كلها", "en": "Teaching Adam all the names"},
        "2:34": {"ar": "أمر الملائكة بالسجود لآدم", "en": "Angels commanded to prostrate to Adam"},
        "2:35": {"ar": "سكنى آدم وزوجه الجنة", "en": "Adam and his wife dwelling in Paradise"},
        "2:37": {"ar": "توبة آدم وقبول الله", "en": "Adam's repentance and Allah's acceptance"},
        "3:33": {"ar": "اصطفاء آدم على العالمين", "en": "Choosing Adam above the worlds"},
        "7:11": {"ar": "خلق آدم وأمر السجود", "en": "Creating Adam and command to prostrate"},
        "7:19": {"ar": "آدم وزوجه في الجنة", "en": "Adam and his wife in Paradise"},
        "17:61": {"ar": "رفض إبليس السجود لآدم", "en": "Iblis refusing to prostrate to Adam"},
        "18:50": {"ar": "إبليس يرفض السجود لآدم", "en": "Iblis refusing prostration to Adam"},
        "20:115": {"ar": "عهد آدم ونسيانه", "en": "Adam's covenant and forgetfulness"},
        "20:117": {"ar": "تحذير آدم من إبليس", "en": "Warning Adam against Iblis"},
        "20:121": {"ar": "أكل آدم من الشجرة", "en": "Adam eating from the tree"},
    },
    "person_alyasa": {
        "6:86": {"ar": "اليسع من المفضلين", "en": "Elisha among the favored"},
        "38:48": {"ar": "ذكر اليسع وذا الكفل", "en": "Mentioning Elisha and Dhul-Kifl"},
    },
    "person_ayyub": {
        "4:163": {"ar": "الوحي إلى أيوب", "en": "Revelation to Ayyub"},
        "6:84": {"ar": "هداية أيوب", "en": "Guidance of Ayyub"},
        "21:83": {"ar": "دعاء أيوب في البلاء", "en": "Ayyub's supplication in affliction"},
        "21:84": {"ar": "استجابة الله لأيوب", "en": "Allah answering Ayyub"},
        "38:41": {"ar": "ابتلاء أيوب وصبره", "en": "Ayyub's trial and patience"},
        "38:42": {"ar": "شفاء أيوب من البلاء", "en": "Ayyub healed from affliction"},
        "38:44": {"ar": "ثناء الله على أيوب", "en": "Allah's praise for Ayyub"},
    },
    "person_dawud": {
        "2:251": {"ar": "قتل داود جالوت", "en": "David killing Goliath"},
        "4:163": {"ar": "إيتاء داود زبوراً", "en": "Giving David the Psalms"},
        "5:78": {"ar": "لعن الكافرين على لسان داود", "en": "Disbelievers cursed by David"},
        "6:84": {"ar": "هداية داود", "en": "Guidance of David"},
        "17:55": {"ar": "تفضيل داود بالزبور", "en": "Favoring David with Psalms"},
        "21:78": {"ar": "حكم داود في الحرث", "en": "David's judgment in the field"},
        "21:79": {"ar": "تسبيح الجبال مع داود", "en": "Mountains glorifying with David"},
        "27:15": {"ar": "علم داود وشكره", "en": "David's knowledge and gratitude"},
        "27:16": {"ar": "وراثة سليمان لداود", "en": "Solomon inheriting from David"},
        "34:10": {"ar": "تسخير الجبال والطير لداود", "en": "Mountains and birds subjected to David"},
        "34:13": {"ar": "عمل آل داود شكراً", "en": "David's family working in gratitude"},
        "38:17": {"ar": "صبر داود ذي الأيد", "en": "Patience of David the strong"},
        "38:22": {"ar": "الخصم يحتكمون إلى داود", "en": "Disputants coming to David"},
        "38:24": {"ar": "استغفار داود وتوبته", "en": "David's seeking forgiveness"},
        "38:26": {"ar": "خلافة داود في الأرض", "en": "David's vicegerency on earth"},
        "38:30": {"ar": "هبة سليمان لداود", "en": "Solomon gifted to David"},
    },
    "person_dhulkifl": {
        "21:85": {"ar": "ذو الكفل من الصابرين", "en": "Dhul-Kifl among the patient"},
        "38:48": {"ar": "ذكر ذي الكفل واليسع", "en": "Mentioning Dhul-Kifl and Elisha"},
    },
    "person_harun": {
        "4:163": {"ar": "الوحي إلى هارون", "en": "Revelation to Aaron"},
        "6:84": {"ar": "هداية هارون", "en": "Guidance of Aaron"},
        "7:122": {"ar": "إيمان السحرة برب هارون وموسى", "en": "Magicians believing in Lord of Moses and Aaron"},
        "7:142": {"ar": "هارون خليفة موسى", "en": "Aaron as Moses' successor"},
        "7:150": {"ar": "غضب موسى على هارون", "en": "Moses' anger at Aaron"},
        "10:75": {"ar": "إرسال موسى وهارون لفرعون", "en": "Moses and Aaron sent to Pharaoh"},
        "19:28": {"ar": "أخت هارون مريم", "en": "Mary as sister of Aaron"},
        "19:53": {"ar": "هبة هارون نبياً لموسى", "en": "Aaron gifted as prophet to Moses"},
        "20:30": {"ar": "طلب موسى وزيراً من أهله", "en": "Moses asking for helper from family"},
        "20:70": {"ar": "سجود السحرة لرب هارون وموسى", "en": "Magicians prostrating to Lord of Aaron"},
        "20:90": {"ar": "تحذير هارون من عبادة العجل", "en": "Aaron warning against calf worship"},
        "20:92": {"ar": "موسى يسأل هارون عن العجل", "en": "Moses questioning Aaron about calf"},
        "21:48": {"ar": "الفرقان لموسى وهارون", "en": "Criterion for Moses and Aaron"},
        "23:45": {"ar": "إرسال موسى وهارون بآياتنا", "en": "Moses and Aaron sent with Our signs"},
        "25:35": {"ar": "موسى والكتاب وهارون الوزير", "en": "Moses with Book and Aaron as minister"},
        "26:13": {"ar": "ضيق صدر موسى وطلب هارون", "en": "Moses' chest tightening, asking for Aaron"},
        "26:48": {"ar": "رب موسى وهارون", "en": "Lord of Moses and Aaron"},
        "28:34": {"ar": "هارون أفصح لساناً", "en": "Aaron more eloquent in speech"},
        "37:114": {"ar": "نعمة الله على موسى وهارون", "en": "Allah's favor on Moses and Aaron"},
        "37:120": {"ar": "سلام على موسى وهارون", "en": "Peace upon Moses and Aaron"},
    },
    "person_hud": {
        "7:65": {"ar": "دعوة هود قومه للتوحيد", "en": "Hud calling his people to monotheism"},
        "7:67": {"ar": "رد قوم هود عليه", "en": "Hud's people responding to him"},
        "7:72": {"ar": "نجاة هود ومن معه", "en": "Saving Hud and those with him"},
        "11:50": {"ar": "هود يدعو عاداً للتوحيد", "en": "Hud calling Aad to monotheism"},
        "11:53": {"ar": "تكذيب قوم عاد لهود", "en": "Aad denying Hud"},
        "11:58": {"ar": "نجاة هود ومن آمن معه", "en": "Saving Hud and believers with him"},
        "11:60": {"ar": "لعنة عاد في الدنيا والآخرة", "en": "Aad cursed in this world and Hereafter"},
        "11:89": {"ar": "تحذير هود قومه من مصير الأمم", "en": "Hud warning his people of nations' fate"},
        "26:124": {"ar": "دعوة هود قومه للتقوى", "en": "Hud calling his people to piety"},
        "26:125": {"ar": "أمر هود قومه بالتقوى", "en": "Hud commanding his people to fear Allah"},
        "46:21": {"ar": "ذكر أخ عاد هود", "en": "Mentioning Hud brother of Aad"},
    },
    "person_ibrahim": {
        "21:60": {"ar": "إبراهيم يحطم الأصنام", "en": "Ibrahim breaking the idols"},
    },
    "person_idris": {
        "19:56": {"ar": "إدريس صديقاً نبياً", "en": "Idris the truthful prophet"},
        "21:85": {"ar": "إدريس من الصابرين", "en": "Idris among the patient"},
    },
    "person_ishaq": {
        "2:133": {"ar": "يعقوب يوصي بعبادة إله إسحاق", "en": "Jacob advising worship of Isaac's God"},
        "2:136": {"ar": "الإيمان بما أنزل على إسحاق", "en": "Believing in what was revealed to Isaac"},
        "3:84": {"ar": "إسحاق من الأنبياء المرسلين", "en": "Isaac among the prophets sent"},
        "4:163": {"ar": "الوحي إلى إسحاق", "en": "Revelation to Isaac"},
        "6:84": {"ar": "هداية إسحاق", "en": "Guidance of Isaac"},
        "11:71": {"ar": "البشارة بإسحاق ويعقوب", "en": "Glad tidings of Isaac and Jacob"},
        "12:6": {"ar": "نعمة الله على آل يعقوب كإسحاق", "en": "Allah's favor on Jacob's family like Isaac"},
        "14:39": {"ar": "شكر إبراهيم على إسماعيل وإسحاق", "en": "Ibrahim grateful for Ismail and Isaac"},
        "19:49": {"ar": "هبة إسحاق ويعقوب لإبراهيم", "en": "Isaac and Jacob gifted to Ibrahim"},
        "21:72": {"ar": "هبة إسحاق ويعقوب نافلة", "en": "Isaac and Jacob as extra gift"},
        "29:27": {"ar": "النبوة في ذرية إسحاق", "en": "Prophethood in Isaac's descendants"},
        "37:112": {"ar": "البشارة بإسحاق نبياً صالحاً", "en": "Glad tidings of Isaac as righteous prophet"},
        "38:45": {"ar": "ذكر إسحاق مع إبراهيم ويعقوب", "en": "Mentioning Isaac with Ibrahim and Jacob"},
    },
    "person_ismail": {
        "2:125": {"ar": "عهد إبراهيم وإسماعيل بتطهير البيت", "en": "Ibrahim and Ismail covenanting to purify House"},
        "2:127": {"ar": "رفع إبراهيم وإسماعيل قواعد البيت", "en": "Ibrahim and Ismail raising foundations of House"},
        "2:133": {"ar": "يعقوب يوصي بعبادة إله إسماعيل", "en": "Jacob advising worship of Ismail's God"},
        "2:136": {"ar": "الإيمان بما أنزل على إسماعيل", "en": "Believing in what was revealed to Ismail"},
        "3:84": {"ar": "إسماعيل من الأنبياء المرسلين", "en": "Ismail among the prophets sent"},
        "4:163": {"ar": "الوحي إلى إسماعيل", "en": "Revelation to Ismail"},
        "6:86": {"ar": "إسماعيل من المفضلين", "en": "Ismail among the favored"},
        "14:39": {"ar": "شكر إبراهيم على إسماعيل", "en": "Ibrahim grateful for Ismail"},
        "19:54": {"ar": "إسماعيل صادق الوعد نبياً", "en": "Ismail true to promise, a prophet"},
        "21:85": {"ar": "إسماعيل من الصابرين", "en": "Ismail among the patient"},
        "37:102": {"ar": "رؤيا إبراهيم بذبح إسماعيل", "en": "Ibrahim's vision of sacrificing Ismail"},
        "38:48": {"ar": "ذكر إسماعيل واليسع وذي الكفل", "en": "Mentioning Ismail, Elisha and Dhul-Kifl"},
    },
    "person_lut": {
        "6:86": {"ar": "لوط من المفضلين", "en": "Lot among the favored"},
        "7:80": {"ar": "إنكار لوط فاحشة قومه", "en": "Lot condemning his people's abomination"},
        "7:83": {"ar": "نجاة لوط وأهله", "en": "Saving Lot and his family"},
        "11:70": {"ar": "الملائكة يخبرون عن هلاك قوم لوط", "en": "Angels informing about Lot's people"},
        "11:74": {"ar": "إبراهيم يجادل في قوم لوط", "en": "Ibrahim arguing for Lot's people"},
        "11:77": {"ar": "مجيء الملائكة للوط", "en": "Angels coming to Lot"},
        "11:81": {"ar": "أمر الملائكة للوط بالخروج ليلاً", "en": "Angels commanding Lot to leave at night"},
        "11:89": {"ar": "تذكير لوط قومه بمصير الأمم", "en": "Lot reminding his people of nations' fate"},
        "15:59": {"ar": "نجاة آل لوط", "en": "Saving Lot's family"},
        "15:61": {"ar": "مجيء المرسلين للوط", "en": "Messengers coming to Lot"},
        "21:71": {"ar": "نجاة لوط إلى الأرض المباركة", "en": "Saving Lot to the blessed land"},
        "21:74": {"ar": "إيتاء لوط حكماً وعلماً", "en": "Giving Lot judgment and knowledge"},
        "22:43": {"ar": "تكذيب قوم لوط كالسابقين", "en": "Lot's people denying like predecessors"},
        "26:160": {"ar": "تكذيب قوم لوط للمرسلين", "en": "Lot's people denying messengers"},
        "27:54": {"ar": "لوط ينهى قومه عن الفاحشة", "en": "Lot forbidding his people from sin"},
        "27:56": {"ar": "إخراج قوم لوط لآله", "en": "Lot's people expelling his family"},
        "29:26": {"ar": "إيمان لوط بإبراهيم", "en": "Lot believing in Ibrahim"},
        "29:28": {"ar": "تذكير لوط قومه بفاحشتهم", "en": "Lot reminding his people of their sin"},
        "29:33": {"ar": "إنذار الملائكة للوط", "en": "Angels warning Lot"},
        "37:133": {"ar": "لوط من المرسلين", "en": "Lot among the messengers"},
        "38:13": {"ar": "قوم لوط من الأحزاب", "en": "Lot's people among the factions"},
        "50:13": {"ar": "إخوان لوط من المكذبين", "en": "Brothers of Lot among deniers"},
        "51:32": {"ar": "إرسال الملائكة لقوم لوط", "en": "Angels sent to Lot's people"},
        "54:33": {"ar": "تكذيب آل لوط بالنذر", "en": "Lot's people denying warnings"},
        "54:34": {"ar": "الحاصب على آل لوط", "en": "Storm upon Lot's people"},
        "66:10": {"ar": "مثل امرأة لوط الخائنة", "en": "Example of Lot's treacherous wife"},
    },
    "person_muhammad": {
        "3:144": {"ar": "محمد رسول قد خلت من قبله الرسل", "en": "Muhammad a messenger preceded by messengers"},
        "33:40": {"ar": "محمد خاتم النبيين", "en": "Muhammad seal of the prophets"},
        "47:2": {"ar": "الإيمان بما نزل على محمد", "en": "Believing in what was revealed to Muhammad"},
        "48:29": {"ar": "محمد رسول الله وصفة أصحابه", "en": "Muhammad messenger of Allah and his companions"},
        "61:6": {"ar": "بشارة عيسى بأحمد", "en": "Isa's glad tidings of Ahmad"},
    },
    "person_nuh": {
        "7:59": {"ar": "دعوة نوح قومه للتوحيد", "en": "Noah calling his people to monotheism"},
        "7:64": {"ar": "تكذيب قوم نوح وإغراقهم", "en": "Noah's people's denial and drowning"},
        "10:71": {"ar": "نوح يذكر قومه", "en": "Noah reminding his people"},
        "11:25": {"ar": "إرسال نوح نذيراً مبيناً", "en": "Noah sent as clear warner"},
        "11:32": {"ar": "جدال قوم نوح معه", "en": "Noah's people arguing with him"},
        "11:36": {"ar": "وحي الله لنوح عن قومه", "en": "Allah's revelation to Noah about his people"},
        "11:42": {"ar": "نوح ينادي ابنه", "en": "Noah calling his son"},
        "11:45": {"ar": "دعاء نوح لابنه", "en": "Noah's supplication for his son"},
        "11:48": {"ar": "السلام على نوح", "en": "Peace upon Noah"},
        "21:76": {"ar": "نجاة نوح من الكرب العظيم", "en": "Saving Noah from great distress"},
        "23:23": {"ar": "نوح يدعو قومه للتقوى", "en": "Noah calling his people to piety"},
        "26:105": {"ar": "تكذيب قوم نوح للمرسلين", "en": "Noah's people denying messengers"},
        "26:116": {"ar": "تهديد قوم نوح له بالرجم", "en": "Noah's people threatening him"},
        "29:14": {"ar": "نوح في قومه ألف سنة", "en": "Noah among his people a thousand years"},
        "37:75": {"ar": "نداء نوح واستجابة الله", "en": "Noah's call and Allah's response"},
        "54:9": {"ar": "تكذيب قوم نوح لعبدنا", "en": "Noah's people denying Our servant"},
        "71:1": {"ar": "إرسال نوح لينذر قومه", "en": "Noah sent to warn his people"},
        "71:21": {"ar": "شكوى نوح من قومه", "en": "Noah's complaint about his people"},
        "71:26": {"ar": "دعاء نوح على الكافرين", "en": "Noah's supplication against disbelievers"},
    },
    "person_salih": {
        "7:73": {"ar": "صالح يدعو ثمود للتوحيد", "en": "Salih calling Thamud to monotheism"},
        "7:77": {"ar": "عقر قوم صالح الناقة", "en": "Salih's people slaughtering the she-camel"},
        "7:79": {"ar": "حسرة صالح على قومه", "en": "Salih's grief for his people"},
        "11:61": {"ar": "دعوة صالح ثمود", "en": "Salih calling Thamud"},
        "11:62": {"ar": "شك ثمود في صالح", "en": "Thamud's doubt about Salih"},
        "11:66": {"ar": "نجاة صالح ومن آمن معه", "en": "Saving Salih and believers with him"},
        "11:89": {"ar": "تحذير صالح قومه", "en": "Salih warning his people"},
        "26:141": {"ar": "تكذيب ثمود للمرسلين", "en": "Thamud denying the messengers"},
        "26:142": {"ar": "صالح يأمر ثمود بالتقوى", "en": "Salih commanding Thamud to fear Allah"},
        "27:45": {"ar": "إرسال صالح لثمود", "en": "Salih sent to Thamud"},
        "27:48": {"ar": "تآمر الفاسدين على صالح", "en": "Evildoers plotting against Salih"},
    },
    "person_shuayb": {
        "7:85": {"ar": "دعوة شعيب مدين للتوحيد", "en": "Shuayb calling Midian to monotheism"},
        "7:88": {"ar": "تهديد قوم شعيب له بالإخراج", "en": "Shuayb's people threatening expulsion"},
        "7:90": {"ar": "استكبار الملأ على شعيب", "en": "Chiefs' arrogance against Shuayb"},
        "7:92": {"ar": "هلاك مكذبي شعيب", "en": "Destruction of Shuayb's deniers"},
        "11:84": {"ar": "شعيب يدعو مدين", "en": "Shuayb calling Midian"},
        "11:87": {"ar": "استهزاء قوم شعيب به", "en": "Shuayb's people mocking him"},
        "11:91": {"ar": "تهديد قوم شعيب له بالرجم", "en": "Shuayb's people threatening to stone him"},
        "11:94": {"ar": "هلاك قوم شعيب بالصيحة", "en": "Shuayb's people destroyed by the cry"},
        "26:177": {"ar": "إرسال شعيب لأصحاب الأيكة", "en": "Shuayb sent to people of the forest"},
        "28:23": {"ar": "موسى يلقى بنتي شعيب", "en": "Moses meeting Shuayb's daughters"},
        "29:36": {"ar": "شعيب يدعو قومه للإيمان", "en": "Shuayb calling his people to faith"},
    },
    "person_sulayman": {
        "2:102": {"ar": "براءة سليمان من السحر", "en": "Solomon's innocence from magic"},
        "4:163": {"ar": "الوحي إلى سليمان", "en": "Revelation to Solomon"},
        "6:84": {"ar": "هداية سليمان", "en": "Guidance of Solomon"},
        "21:78": {"ar": "حكم سليمان في الحرث", "en": "Solomon's judgment in the field"},
        "21:79": {"ar": "تفهيم سليمان الحكمة", "en": "Solomon granted understanding"},
        "21:81": {"ar": "تسخير الريح لسليمان", "en": "Wind subjected to Solomon"},
        "27:15": {"ar": "علم داود وسليمان", "en": "Knowledge of David and Solomon"},
        "27:16": {"ar": "وراثة سليمان داود", "en": "Solomon inheriting from David"},
        "27:17": {"ar": "جنود سليمان من الجن والإنس", "en": "Solomon's armies of jinn and men"},
        "27:18": {"ar": "سليمان والنملة", "en": "Solomon and the ant"},
        "27:30": {"ar": "كتاب سليمان لبلقيس", "en": "Solomon's letter to Bilqis"},
        "27:36": {"ar": "رد سليمان على هدية بلقيس", "en": "Solomon's response to Bilqis' gift"},
        "27:44": {"ar": "إسلام بلقيس مع سليمان", "en": "Bilqis submitting with Solomon"},
        "34:12": {"ar": "تسخير الريح والجن لسليمان", "en": "Wind and jinn subjected to Solomon"},
        "34:14": {"ar": "موت سليمان", "en": "Death of Solomon"},
        "38:30": {"ar": "هبة سليمان لداود", "en": "Solomon gifted to David"},
        "38:34": {"ar": "فتنة سليمان", "en": "Solomon's trial"},
        "38:36": {"ar": "تسخير الريح لسليمان", "en": "Wind subjected to Solomon"},
    },
    "person_yahya": {
        "3:39": {"ar": "بشارة يحيى مصدقاً بكلمة", "en": "Glad tidings of Yahya confirming a Word"},
        "6:85": {"ar": "يحيى من الصالحين", "en": "Yahya among the righteous"},
        "19:7": {"ar": "بشارة زكريا بيحيى", "en": "Zakariyya given glad tidings of Yahya"},
        "19:12": {"ar": "إيتاء يحيى الحكم صبياً", "en": "Yahya given wisdom as a child"},
        "21:90": {"ar": "استجابة دعاء زكريا بيحيى", "en": "Answering Zakariyya's prayer with Yahya"},
    },
    "person_yaqub": {
        "2:132": {"ar": "وصية يعقوب لبنيه", "en": "Jacob's advice to his sons"},
        "2:133": {"ar": "يعقوب يسأل بنيه عمن يعبدون", "en": "Jacob asking his sons whom they worship"},
        "2:136": {"ar": "الإيمان بما أنزل على يعقوب", "en": "Believing in what was revealed to Jacob"},
        "3:84": {"ar": "يعقوب من الأنبياء المرسلين", "en": "Jacob among the prophets sent"},
        "4:163": {"ar": "الوحي إلى يعقوب", "en": "Revelation to Jacob"},
        "6:84": {"ar": "هداية يعقوب", "en": "Guidance of Jacob"},
        "11:71": {"ar": "البشارة بيعقوب من وراء إسحاق", "en": "Glad tidings of Jacob after Isaac"},
        "12:4": {"ar": "رؤيا يوسف ويعقوب", "en": "Joseph's vision and Jacob"},
        "12:6": {"ar": "نعمة الله على آل يعقوب", "en": "Allah's favor on Jacob's family"},
        "12:38": {"ar": "ملة إبراهيم وإسحاق ويعقوب", "en": "Religion of Ibrahim, Isaac and Jacob"},
        "12:68": {"ar": "وصية يعقوب لأبنائه", "en": "Jacob's advice to his sons"},
        "12:84": {"ar": "حزن يعقوب على يوسف", "en": "Jacob's grief for Joseph"},
        "12:93": {"ar": "قميص يوسف يرد بصر يعقوب", "en": "Joseph's shirt restoring Jacob's sight"},
        "19:6": {"ar": "يعقوب من آل إسرائيل", "en": "Jacob from the family of Israel"},
        "19:49": {"ar": "هبة إسحاق ويعقوب لإبراهيم", "en": "Isaac and Jacob gifted to Ibrahim"},
        "21:72": {"ar": "هبة يعقوب نافلة", "en": "Jacob as an extra gift"},
        "29:27": {"ar": "النبوة في ذرية يعقوب", "en": "Prophethood in Jacob's descendants"},
        "38:45": {"ar": "ذكر إبراهيم وإسحاق ويعقوب", "en": "Mentioning Ibrahim, Isaac and Jacob"},
    },
    "person_yunus": {
        "4:163": {"ar": "الوحي إلى يونس", "en": "Revelation to Yunus"},
        "6:86": {"ar": "يونس من المفضلين", "en": "Yunus among the favored"},
        "10:98": {"ar": "إيمان قوم يونس ونجاتهم", "en": "Yunus' people believing and saved"},
        "21:87": {"ar": "نداء ذي النون في الظلمات", "en": "Dhul-Nun calling from the darkness"},
        "37:139": {"ar": "يونس من المرسلين", "en": "Yunus among the messengers"},
        "37:142": {"ar": "التقام الحوت ليونس", "en": "The whale swallowing Yunus"},
        "37:145": {"ar": "نبذ يونس على الساحل", "en": "Yunus cast onto the shore"},
        "68:48": {"ar": "صبر النبي كصاحب الحوت", "en": "Prophet's patience like companion of whale"},
    },
    "person_yusuf": {
        "6:84": {"ar": "هداية يوسف", "en": "Guidance of Joseph"},
        "12:4": {"ar": "رؤيا يوسف الصادقة", "en": "Joseph's true vision"},
        "12:7": {"ar": "آيات في قصة يوسف", "en": "Signs in the story of Joseph"},
        "12:8": {"ar": "حسد إخوة يوسف", "en": "Joseph's brothers' jealousy"},
        "12:9": {"ar": "تآمر إخوة يوسف عليه", "en": "Joseph's brothers plotting against him"},
        "12:10": {"ar": "إلقاء يوسف في الجب", "en": "Joseph thrown into the well"},
        "12:11": {"ar": "إخوة يوسف يطلبون إرساله", "en": "Brothers asking to send Joseph"},
        "12:16": {"ar": "إخوة يوسف يبكون كذباً", "en": "Brothers weeping falsely"},
        "12:17": {"ar": "ادعاء أكل الذئب ليوسف", "en": "Claiming wolf ate Joseph"},
        "12:21": {"ar": "بيع يوسف في مصر", "en": "Joseph sold in Egypt"},
        "12:29": {"ar": "براءة يوسف من امرأة العزيز", "en": "Joseph's innocence from Aziz's wife"},
        "12:36": {"ar": "يوسف يعبر الرؤى في السجن", "en": "Joseph interpreting visions in prison"},
        "12:46": {"ar": "استفتاء الملك يوسف", "en": "King consulting Joseph"},
        "12:51": {"ar": "اعتراف امرأة العزيز ببراءة يوسف", "en": "Aziz's wife confessing Joseph's innocence"},
        "12:56": {"ar": "تمكين يوسف في الأرض", "en": "Joseph established in the land"},
        "12:58": {"ar": "إخوة يوسف يأتون إليه", "en": "Joseph's brothers coming to him"},
        "12:69": {"ar": "يوسف يأوي أخاه بنيامين", "en": "Joseph sheltering his brother Benjamin"},
        "12:77": {"ar": "سرقة بنيامين المزعومة", "en": "Alleged theft of Benjamin"},
        "12:84": {"ar": "حزن يعقوب على يوسف", "en": "Jacob's grief for Joseph"},
        "12:87": {"ar": "البحث عن يوسف وأخيه", "en": "Searching for Joseph and his brother"},
        "12:90": {"ar": "تعارف يوسف مع إخوته", "en": "Joseph revealing himself to brothers"},
        "12:94": {"ar": "ريح يوسف يجدها يعقوب", "en": "Jacob sensing Joseph's scent"},
        "12:99": {"ar": "دخول أبوي يوسف مصر", "en": "Joseph's parents entering Egypt"},
        "12:100": {"ar": "رفع يوسف أبويه على العرش", "en": "Joseph raising his parents on the throne"},
        "40:34": {"ar": "يوسف جاء بالبينات من قبل", "en": "Joseph came with clear proofs before"},
    },
    "person_zakariyya": {
        "3:37": {"ar": "كفالة زكريا لمريم", "en": "Zakariyya's guardianship of Maryam"},
        "3:38": {"ar": "دعاء زكريا لذرية طيبة", "en": "Zakariyya's prayer for good offspring"},
        "6:85": {"ar": "زكريا من الصالحين", "en": "Zakariyya among the righteous"},
        "19:2": {"ar": "ذكر رحمة الله لزكريا", "en": "Remembering Allah's mercy to Zakariyya"},
        "19:7": {"ar": "بشارة زكريا بيحيى", "en": "Zakariyya given glad tidings of Yahya"},
        "21:89": {"ar": "دعاء زكريا لعدم الوحدة", "en": "Zakariyya's prayer not to be left alone"},
        "21:90": {"ar": "استجابة دعاء زكريا", "en": "Answering Zakariyya's prayer"},
    },
}

# ============================================================================
# REMAINING MUSA TOPICS (To complete the 47 missing)
# ============================================================================

MUSA_REMAINING = {
    "person_musa": {
        "2:136": {"ar": "الإيمان بما أنزل على موسى", "en": "Believing in what was revealed to Moses"},
        "4:153": {"ar": "سؤال أهل الكتاب لموسى", "en": "People of Book asking Moses"},
        "4:164": {"ar": "تكليم الله موسى تكليماً", "en": "Allah speaking directly to Moses"},
        "5:20": {"ar": "موسى يذكر قومه بنعم الله", "en": "Moses reminding his people of blessings"},
        "5:22": {"ar": "خوف قوم موسى من الجبارين", "en": "Moses' people fearing the mighty"},
        "5:24": {"ar": "رفض قوم موسى القتال", "en": "Moses' people refusing to fight"},
        "6:84": {"ar": "هداية موسى", "en": "Guidance of Moses"},
        "6:154": {"ar": "إيتاء موسى الكتاب تماماً", "en": "Giving Moses the complete Book"},
        "7:127": {"ar": "ملأ فرعون يشكون موسى", "en": "Pharaoh's chiefs complaining about Moses"},
        "7:128": {"ar": "صبر موسى ووعده قومه", "en": "Moses' patience and promise to his people"},
        "7:138": {"ar": "جواز بني إسرائيل البحر", "en": "Israelites crossing the sea"},
        "7:159": {"ar": "أمة من قوم موسى يهدون بالحق", "en": "A nation of Moses' people guiding with truth"},
        "10:77": {"ar": "اتهام فرعون موسى بالسحر", "en": "Pharaoh accusing Moses of magic"},
        "11:17": {"ar": "كتاب موسى شاهداً", "en": "Moses' Book as witness"},
        "11:110": {"ar": "الاختلاف في كتاب موسى", "en": "Disagreement about Moses' Book"},
        "17:2": {"ar": "إيتاء موسى الكتاب هدى", "en": "Giving Moses the Book as guidance"},
        "20:17": {"ar": "سؤال الله موسى عن العصا", "en": "Allah asking Moses about the staff"},
        "20:40": {"ar": "حفظ الله لموسى منذ الصغر", "en": "Allah protecting Moses from childhood"},
        "20:49": {"ar": "سؤال فرعون عن رب موسى", "en": "Pharaoh asking about Moses' Lord"},
        "20:83": {"ar": "سؤال الله موسى عن قومه", "en": "Allah asking Moses about his people"},
        "20:88": {"ar": "السامري يصنع العجل", "en": "Samiri making the calf"},
        "23:45": {"ar": "إرسال موسى وهارون", "en": "Sending Moses and Aaron"},
        "25:35": {"ar": "إيتاء موسى الكتاب وهارون وزيراً", "en": "Giving Moses the Book with Aaron as helper"},
        "26:43": {"ar": "موسى يتحدى السحرة", "en": "Moses challenging the magicians"},
        "26:52": {"ar": "أمر الله موسى بالخروج ليلاً", "en": "Allah commanding Moses to leave at night"},
        "26:61": {"ar": "ثقة موسى بربه عند البحر", "en": "Moses' trust in his Lord at the sea"},
        "27:10": {"ar": "موسى يرى العصا كأنها جان", "en": "Moses seeing staff like a serpent"},
        "28:10": {"ar": "فؤاد أم موسى فارغاً", "en": "Moses' mother's heart becoming empty"},
        "28:18": {"ar": "موسى خائفاً يترقب", "en": "Moses fearful and watchful"},
        "28:20": {"ar": "رجل ينصح موسى بالخروج", "en": "A man advising Moses to leave"},
        "28:30": {"ar": "نداء الله لموسى من الشجرة", "en": "Allah calling Moses from the tree"},
        "28:36": {"ar": "اتهام فرعون موسى بالسحر", "en": "Pharaoh accusing Moses of sorcery"},
        "28:48": {"ar": "كفار قريش يكذبون كفرعون", "en": "Quraysh disbelieving like Pharaoh"},
        "29:39": {"ar": "هلاك فرعون وقارون", "en": "Destruction of Pharaoh and Qarun"},
        "32:23": {"ar": "إيتاء موسى الكتاب", "en": "Giving Moses the Book"},
        "33:7": {"ar": "ميثاق النبيين ومنهم موسى", "en": "Covenant of prophets including Moses"},
        "33:69": {"ar": "براءة موسى مما قالوا", "en": "Moses innocent of what they said"},
        "37:120": {"ar": "سلام على موسى وهارون", "en": "Peace upon Moses and Aaron"},
        "40:27": {"ar": "موسى يستعيذ من المتكبرين", "en": "Moses seeking refuge from the arrogant"},
        "40:53": {"ar": "وراثة بني إسرائيل الهدى", "en": "Israelites inheriting guidance"},
        "41:45": {"ar": "الاختلاف في كتاب موسى", "en": "Disagreement about Moses' Book"},
        "42:13": {"ar": "الدين المشترك لنوح وموسى", "en": "Common religion of Noah and Moses"},
        "46:30": {"ar": "الجن يستمعون للقرآن كموسى", "en": "Jinn listening to Quran like Moses"},
        "53:36": {"ar": "ما في صحف موسى", "en": "What is in Moses' scriptures"},
        "61:5": {"ar": "موسى يقول لقومه لم تؤذونني", "en": "Moses asking why they hurt him"},
        "73:15": {"ar": "رسول كموسى لفرعون", "en": "A messenger like Moses to Pharaoh"},
        "87:19": {"ar": "صحف موسى", "en": "Scriptures of Moses"},
    },
}

# ============================================================================
# PLACE TOPICS
# ============================================================================

PLACE_TOPICS = {
    "place_baytulmaqdis": {
        "5:21": {"ar": "الأرض المقدسة التي كتب الله", "en": "The holy land Allah prescribed"},
        "17:1": {"ar": "الإسراء إلى المسجد الأقصى", "en": "Night journey to Al-Aqsa Mosque"},
        "21:71": {"ar": "نجاة إبراهيم للأرض المباركة", "en": "Ibrahim saved to the blessed land"},
        "21:81": {"ar": "الريح تجري للأرض المباركة", "en": "Wind flowing to the blessed land"},
    },
    "place_madinah": {
        "9:101": {"ar": "منافقو المدينة", "en": "Hypocrites of Madinah"},
        "9:120": {"ar": "أهل المدينة ومن حولهم", "en": "People of Madinah and surroundings"},
        "33:60": {"ar": "المرجفون في المدينة", "en": "Those spreading rumors in Madinah"},
        "63:8": {"ar": "العزة لله ولرسوله وللمؤمنين", "en": "Honor belongs to Allah and His messenger"},
    },
    "place_makkah": {
        "95:3": {"ar": "البلد الأمين مكة", "en": "The secure city of Makkah"},
    },
    "place_sinai": {
        "7:143": {"ar": "تجلي الله للجبل", "en": "Allah manifesting to the mountain"},
        "19:52": {"ar": "نداء موسى من جانب الطور", "en": "Calling Moses from the side of Mount"},
        "20:80": {"ar": "مواعدة بني إسرائيل جانب الطور", "en": "Israelites' appointment at Mount side"},
        "23:20": {"ar": "شجرة تخرج من طور سيناء", "en": "Tree growing from Mount Sinai"},
        "28:29": {"ar": "موسى يرى ناراً من جانب الطور", "en": "Moses seeing fire from Mount side"},
        "28:46": {"ar": "موسى لم يكن بجانب الطور", "en": "Moses was not at Mount side then"},
        "52:1": {"ar": "القسم بالطور", "en": "Swearing by the Mount"},
        "95:2": {"ar": "طور سينين", "en": "Mount Sinai"},
    },
}

# ============================================================================
# THEME TOPICS (Sample - abbreviated for core themes)
# ============================================================================

THEME_TOPICS = {
    "theme_adl": {
        "4:58": {"ar": "الأمر بالعدل في الحكم", "en": "Command to judge with justice"},
        "4:135": {"ar": "القيام بالقسط شهداء لله", "en": "Standing firmly for justice as witnesses"},
        "5:8": {"ar": "العدل أقرب للتقوى", "en": "Justice is closest to piety"},
        "5:42": {"ar": "الحكم بينهم بالقسط", "en": "Judging between them with equity"},
        "6:152": {"ar": "الوزن والكيل بالقسط", "en": "Weighing and measuring with justice"},
        "16:90": {"ar": "إن الله يأمر بالعدل والإحسان", "en": "Allah commands justice and excellence"},
        "38:26": {"ar": "الحكم بين الناس بالحق", "en": "Judging between people with truth"},
        "42:15": {"ar": "العدل بين أهل الكتاب", "en": "Justice between People of the Book"},
        "49:9": {"ar": "الإصلاح بين المؤمنين بالعدل", "en": "Reconciling believers with justice"},
        "57:25": {"ar": "إرسال الرسل بالميزان للعدل", "en": "Sending messengers with balance for justice"},
        "60:8": {"ar": "القسط مع غير المحاربين", "en": "Justice with non-combatants"},
    },
    "theme_tawbah": {
        "2:37": {"ar": "توبة آدم وقبول الله", "en": "Adam's repentance and Allah's acceptance"},
        "2:54": {"ar": "توبة بني إسرائيل من العجل", "en": "Israelites repenting from calf worship"},
        "2:128": {"ar": "دعاء إبراهيم للتوبة", "en": "Ibrahim's prayer for repentance"},
        "2:160": {"ar": "قبول توبة التائبين", "en": "Accepting repentance of the penitent"},
        "2:222": {"ar": "الله يحب التوابين", "en": "Allah loves those who repent"},
        "3:89": {"ar": "التوبة والإصلاح", "en": "Repentance and reformation"},
        "3:90": {"ar": "عدم قبول توبة المرتدين", "en": "Rejection of apostates' repentance"},
        "4:17": {"ar": "التوبة على الله للجاهلين", "en": "Repentance accepted for the ignorant"},
        "4:18": {"ar": "التوبة عند حضور الموت", "en": "Repentance at death's approach"},
        "4:146": {"ar": "التوبة والإصلاح والاعتصام", "en": "Repentance, reform and holding fast"},
        "5:39": {"ar": "التوبة بعد الظلم", "en": "Repentance after wrongdoing"},
        "5:74": {"ar": "التوبة والاستغفار", "en": "Repentance and seeking forgiveness"},
        "6:54": {"ar": "رحمة الله للتائبين", "en": "Allah's mercy for the penitent"},
        "7:153": {"ar": "المغفرة والرحمة للتائبين", "en": "Forgiveness and mercy for the penitent"},
        "9:3": {"ar": "فرصة التوبة للمشركين", "en": "Opportunity for polytheists to repent"},
        "9:5": {"ar": "قبول توبة المشركين", "en": "Accepting polytheists' repentance"},
        "9:11": {"ar": "التوبة تجعلهم إخواناً", "en": "Repentance making them brothers"},
        "9:102": {"ar": "اعتراف التائبين بذنوبهم", "en": "Penitents acknowledging their sins"},
        "9:104": {"ar": "الله يقبل التوبة عن عباده", "en": "Allah accepts repentance from servants"},
        "9:117": {"ar": "توبة الله على النبي والمهاجرين", "en": "Allah's turning to Prophet and emigrants"},
        "9:118": {"ar": "توبة الثلاثة المتخلفين", "en": "Repentance of the three who stayed behind"},
        "11:3": {"ar": "الاستغفار والتوبة", "en": "Seeking forgiveness and repentance"},
        "11:52": {"ar": "دعوة هود للاستغفار", "en": "Hud calling to seek forgiveness"},
        "11:61": {"ar": "دعوة صالح للاستغفار", "en": "Salih calling to seek forgiveness"},
        "11:90": {"ar": "دعوة شعيب للاستغفار", "en": "Shuayb calling to seek forgiveness"},
        "13:27": {"ar": "الله يهدي من يتوب", "en": "Allah guides those who repent"},
        "16:119": {"ar": "التوبة والإصلاح بعد الجهل", "en": "Repentance and reform after ignorance"},
        "19:60": {"ar": "استثناء التائبين من العقاب", "en": "Exception for the penitent from punishment"},
        "20:82": {"ar": "المغفرة للتائب المؤمن", "en": "Forgiveness for believing penitent"},
        "24:5": {"ar": "التوبة والإصلاح للقاذفين", "en": "Repentance and reform for slanderers"},
        "24:31": {"ar": "التوبة للمؤمنين", "en": "Repentance for the believers"},
        "25:70": {"ar": "تبديل السيئات حسنات للتائبين", "en": "Evil deeds replaced with good for penitent"},
        "25:71": {"ar": "رجوع التائب إلى الله", "en": "The penitent returning to Allah"},
        "28:67": {"ar": "التوبة والإيمان والعمل الصالح", "en": "Repentance, faith and good deeds"},
        "39:54": {"ar": "الإنابة قبل العذاب", "en": "Turning back before punishment"},
        "42:25": {"ar": "قبول التوبة ومغفرة الذنوب", "en": "Accepting repentance and forgiving sins"},
        "46:15": {"ar": "توبة الإنسان عند الأربعين", "en": "Human repentance at forty"},
        "50:32": {"ar": "الجنة للأوابين الحافظين", "en": "Paradise for the oft-returning, mindful"},
        "66:8": {"ar": "التوبة النصوح", "en": "Sincere repentance"},
    },
    "theme_tawakkul": {
        "3:122": {"ar": "التوكل بعد الهم بالفشل", "en": "Trust after thinking of retreat"},
        "3:159": {"ar": "التوكل بعد الشورى", "en": "Trust after consultation"},
        "3:160": {"ar": "نصر الله للمتوكلين", "en": "Allah's help for those who trust"},
        "4:81": {"ar": "التوكل على الله وكفايته", "en": "Trust in Allah as sufficient"},
        "5:11": {"ar": "التوكل عند مكر الأعداء", "en": "Trust when enemies plot"},
        "5:23": {"ar": "دعوة للتوكل عند مواجهة الجبارين", "en": "Call to trust when facing mighty"},
        "7:89": {"ar": "توكل شعيب على الله", "en": "Shuayb's trust in Allah"},
        "8:49": {"ar": "التوكل في مواجهة العدو", "en": "Trust when facing the enemy"},
        "8:61": {"ar": "التوكل عند السلم", "en": "Trust during peace"},
        "9:51": {"ar": "التوكل على ما كتب الله", "en": "Trust in what Allah decreed"},
        "9:129": {"ar": "التوكل على رب العرش", "en": "Trust in Lord of the Throne"},
        "10:71": {"ar": "توكل نوح على الله", "en": "Noah's trust in Allah"},
        "10:84": {"ar": "دعوة موسى للتوكل", "en": "Moses calling to trust"},
        "10:85": {"ar": "توكل المؤمنين مع موسى", "en": "Believers' trust with Moses"},
        "11:56": {"ar": "توكل هود على ربه", "en": "Hud's trust in his Lord"},
        "11:88": {"ar": "توكل شعيب على الله", "en": "Shuayb's trust in Allah"},
        "11:123": {"ar": "الأمر بعبادة الله والتوكل", "en": "Command to worship and trust"},
        "12:67": {"ar": "توكل يعقوب على الله", "en": "Jacob's trust in Allah"},
        "13:30": {"ar": "التوكل على الرحمن", "en": "Trust in the Most Merciful"},
        "14:11": {"ar": "توكل الرسل على الله", "en": "Messengers' trust in Allah"},
        "14:12": {"ar": "توكل المؤمنين على الله", "en": "Believers' trust in Allah"},
        "16:42": {"ar": "جزاء المتوكلين الصابرين", "en": "Reward of patient trusting ones"},
        "16:99": {"ar": "سلطان الشيطان دون المتوكلين", "en": "Satan's authority not over trusting"},
        "25:58": {"ar": "التوكل على الحي الذي لا يموت", "en": "Trust in the Ever-Living"},
        "26:217": {"ar": "التوكل على العزيز الرحيم", "en": "Trust in the Mighty, Merciful"},
        "27:79": {"ar": "التوكل على الله في الهداية", "en": "Trust in Allah for guidance"},
        "29:59": {"ar": "صبر وتوكل المؤمنين", "en": "Patience and trust of believers"},
        "33:3": {"ar": "التوكل على الله وكفايته", "en": "Trust in Allah as sufficient"},
        "33:48": {"ar": "التوكل وعدم طاعة الكافرين", "en": "Trust and not obeying disbelievers"},
        "39:38": {"ar": "التوكل على الله الكافي", "en": "Trust in Allah the Sufficient"},
        "42:10": {"ar": "التوكل على الله في الخلاف", "en": "Trust in Allah during disagreement"},
        "42:36": {"ar": "جزاء المتوكلين", "en": "Reward of those who trust"},
        "58:10": {"ar": "التوكل في مواجهة النجوى", "en": "Trust against secret counsels"},
        "60:4": {"ar": "توكل إبراهيم والمؤمنين", "en": "Trust of Ibrahim and believers"},
        "64:13": {"ar": "التوكل على الله وحده", "en": "Trust in Allah alone"},
        "65:3": {"ar": "كفاية الله للمتوكلين", "en": "Allah sufficient for trusting ones"},
    },
}

# Note: theme_sabr, theme_shukr, theme_dhikr, theme_ihsan, theme_iman, theme_taqwa
# have many verses - creating abbreviated versions for key verses

THEME_SABR_SAMPLE = {
    "theme_sabr": {
        "2:45": {"ar": "الاستعانة بالصبر والصلاة", "en": "Seeking help through patience and prayer"},
        "2:153": {"ar": "الله مع الصابرين", "en": "Allah is with the patient"},
        "2:155": {"ar": "الابتلاء بالخوف والجوع", "en": "Testing with fear and hunger"},
        "2:177": {"ar": "الصابرين في البأساء", "en": "The patient in hardship"},
        "3:17": {"ar": "الصابرين من صفات المتقين", "en": "Patience as trait of the pious"},
        "3:125": {"ar": "الصبر والتقوى في المعركة", "en": "Patience and piety in battle"},
        "3:146": {"ar": "صبر الربانيين مع الأنبياء", "en": "Patience of devoted ones with prophets"},
        "3:186": {"ar": "الصبر على الأذى", "en": "Patience with harm"},
        "3:200": {"ar": "الصبر والمصابرة والرباط", "en": "Patience, endurance and vigilance"},
        "7:128": {"ar": "الاستعانة بالله والصبر", "en": "Seeking Allah's help and patience"},
        "7:137": {"ar": "صبر بني إسرائيل والتمكين", "en": "Israelites' patience and empowerment"},
        "8:46": {"ar": "الصبر عند لقاء العدو", "en": "Patience when meeting enemy"},
        "11:11": {"ar": "استثناء الصابرين من الجزع", "en": "Except the patient from anxiety"},
        "11:115": {"ar": "الصبر وعدم ضياع أجر المحسنين", "en": "Patience and doers' reward not lost"},
        "16:96": {"ar": "أجر الصابرين بأحسن أعمالهم", "en": "Rewarding patient by best deeds"},
        "16:126": {"ar": "الصبر خير للصابرين", "en": "Patience is better for the patient"},
        "16:127": {"ar": "الصبر بالله لا بالنفس", "en": "Patience is through Allah"},
        "21:85": {"ar": "صبر إسماعيل وإدريس وذي الكفل", "en": "Patience of Ismail, Idris, Dhul-Kifl"},
        "23:111": {"ar": "جزاء صبر المؤمنين", "en": "Reward for believers' patience"},
        "29:59": {"ar": "صبر المتوكلين على الله", "en": "Patience of those trusting Allah"},
        "31:17": {"ar": "الصبر من عزم الأمور", "en": "Patience is of firm resolve"},
        "32:24": {"ar": "أئمة يهدون بالصبر", "en": "Leaders guiding through patience"},
        "37:102": {"ar": "صبر إسماعيل على الذبح", "en": "Ismail's patience with sacrifice"},
        "38:44": {"ar": "ثناء الله على صبر أيوب", "en": "Allah praising Ayyub's patience"},
        "39:10": {"ar": "أجر الصابرين بغير حساب", "en": "Patient ones rewarded without measure"},
        "41:35": {"ar": "الصبر من الحظ العظيم", "en": "Patience is of great fortune"},
        "42:43": {"ar": "الصبر والمغفرة من عزم الأمور", "en": "Patience and forgiveness of firm resolve"},
        "46:35": {"ar": "صبر أولي العزم من الرسل", "en": "Patience of resolute messengers"},
        "47:31": {"ar": "اختبار المؤمنين بالجهاد والصبر", "en": "Testing believers with struggle and patience"},
        "70:5": {"ar": "الصبر الجميل", "en": "Beautiful patience"},
        "90:17": {"ar": "التواصي بالصبر والمرحمة", "en": "Advising each other to patience and mercy"},
        "103:3": {"ar": "التواصي بالصبر", "en": "Advising each other to patience"},
    },
}


def parse_verse_ref(verse_ref: str) -> tuple[int, int]:
    """Parse verse reference like '2:87' into (sura_no, ayah_start)."""
    parts = verse_ref.split(":")
    return int(parts[0]), int(parts[1])


async def populate_topics():
    """Populate topic descriptions for all concept occurrences."""

    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Combine all topic dictionaries
    all_topics = {}

    # Add miracle topics
    for concept_id, topics in MIRACLE_TOPICS.items():
        all_topics[concept_id] = topics

    # Add nation topics
    for concept_id, topics in NATION_TOPICS.items():
        all_topics[concept_id] = topics

    # Add person topics
    for concept_id, topics in PERSON_TOPICS.items():
        if concept_id in all_topics:
            all_topics[concept_id].update(topics)
        else:
            all_topics[concept_id] = topics

    # Add remaining Musa topics
    for concept_id, topics in MUSA_REMAINING.items():
        if concept_id in all_topics:
            all_topics[concept_id].update(topics)
        else:
            all_topics[concept_id] = topics

    # Add place topics
    for concept_id, topics in PLACE_TOPICS.items():
        all_topics[concept_id] = topics

    # Add theme topics
    for concept_id, topics in THEME_TOPICS.items():
        all_topics[concept_id] = topics

    # Add sabr sample
    for concept_id, topics in THEME_SABR_SAMPLE.items():
        all_topics[concept_id] = topics

    async with async_session() as session:
        total_updated = 0

        for concept_id, topics in all_topics.items():
            logger.info(f"Processing concept: {concept_id}")

            for verse_ref, descriptions in topics.items():
                sura_no, ayah_start = parse_verse_ref(verse_ref)

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
