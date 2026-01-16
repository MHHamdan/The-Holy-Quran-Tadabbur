#!/usr/bin/env python3
"""
Theme topic descriptions for remaining concept occurrences.
Based on Quranic scholarship and semantic analysis of each verse.

Usage:
    PYTHONPATH=. python scripts/populate_theme_topics.py
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
# THEME_DHIKR - Remembrance of Allah
# ============================================================================

THEME_DHIKR = {
    "2:152": {"ar": "اذكروني أذكركم", "en": "Remember Me, I will remember you"},
    "2:198": {"ar": "ذكر الله عند المشعر الحرام", "en": "Remembering Allah at the Sacred Monument"},
    "2:200": {"ar": "ذكر الله كذكر الآباء أو أشد", "en": "Remember Allah like your fathers or more"},
    "2:203": {"ar": "ذكر الله في الأيام المعدودات", "en": "Remembering Allah in numbered days"},
    "3:41": {"ar": "ذكر زكريا ربه كثيراً", "en": "Zakariyya remembering his Lord much"},
    "3:191": {"ar": "الذين يذكرون الله قياماً وقعوداً", "en": "Those remembering Allah standing and sitting"},
    "4:103": {"ar": "ذكر الله بعد الصلاة", "en": "Remembering Allah after prayer"},
    "5:4": {"ar": "ذكر اسم الله على الصيد", "en": "Mentioning Allah's name on game"},
    "5:91": {"ar": "الصد عن ذكر الله", "en": "Being distracted from remembering Allah"},
    "6:91": {"ar": "اللعب واللهو عن ذكر الله", "en": "Playing and amusement from remembrance"},
    "7:205": {"ar": "ذكر الله في النفس تضرعاً وخيفة", "en": "Remember in oneself humbly and fearfully"},
    "8:45": {"ar": "ذكر الله كثيراً عند لقاء العدو", "en": "Remember Allah much when meeting enemy"},
    "13:28": {"ar": "بذكر الله تطمئن القلوب", "en": "By remembrance hearts find tranquility"},
    "18:24": {"ar": "ذكر الله عند النسيان", "en": "Remember Allah when forgetting"},
    "20:14": {"ar": "أقم الصلاة لذكري", "en": "Establish prayer for My remembrance"},
    "20:42": {"ar": "لا تنيا في ذكري", "en": "Do not slacken in My remembrance"},
    "22:28": {"ar": "ذكر اسم الله على الأنعام", "en": "Mention Allah's name over cattle"},
    "22:34": {"ar": "ذكر اسم الله على البهائم", "en": "Mention Allah's name over livestock"},
    "22:36": {"ar": "ذكر اسم الله على البدن", "en": "Mention Allah's name over sacrificial camels"},
    "24:37": {"ar": "رجال لا تلهيهم تجارة عن ذكر الله", "en": "Men not distracted from remembrance by trade"},
    "29:45": {"ar": "ذكر الله أكبر", "en": "Remembrance of Allah is greatest"},
    "33:21": {"ar": "ذكر الله كثيراً في الأسوة", "en": "Remembering Allah much in following example"},
    "33:35": {"ar": "الذاكرين الله كثيراً والذاكرات", "en": "Men and women remembering Allah much"},
    "33:41": {"ar": "اذكروا الله ذكراً كثيراً", "en": "Remember Allah with much remembrance"},
    "33:42": {"ar": "سبحوه بكرة وأصيلاً", "en": "Glorify Him morning and evening"},
    "39:22": {"ar": "قسوة القلب عن ذكر الله", "en": "Heart hardened against remembrance"},
    "39:23": {"ar": "تقشعر الجلود من ذكر الله", "en": "Skins shiver at remembrance of Allah"},
    "43:36": {"ar": "العمى عن ذكر الرحمن", "en": "Blindness to remembrance of the Merciful"},
    "57:16": {"ar": "خشوع القلوب لذكر الله", "en": "Hearts humbling to remembrance"},
    "62:10": {"ar": "ذكر الله كثيراً للفلاح", "en": "Remember Allah much for success"},
    "63:9": {"ar": "لا تلهكم الأموال عن ذكر الله", "en": "Let not wealth distract from remembrance"},
    "73:8": {"ar": "ذكر اسم الرب والتبتل", "en": "Remember your Lord's name and devote"},
    "76:25": {"ar": "ذكر اسم الله بكرة وأصيلاً", "en": "Remember Allah's name morning and evening"},
    "87:15": {"ar": "ذكر اسم ربه فصلى", "en": "Remembers his Lord's name and prays"},
}

# ============================================================================
# THEME_IHSAN - Excellence in worship and conduct
# ============================================================================

THEME_IHSAN = {
    "2:112": {"ar": "إحسان الوجه لله", "en": "Submitting oneself to Allah in excellence"},
    "2:195": {"ar": "الله يحب المحسنين", "en": "Allah loves those who do good"},
    "2:236": {"ar": "متعة المطلقات بالإحسان", "en": "Provision for divorced women with goodness"},
    "3:134": {"ar": "المحسنون يكظمون الغيظ ويعفون", "en": "Doers of good suppress anger and pardon"},
    "3:148": {"ar": "جزاء المحسنين في الدنيا والآخرة", "en": "Reward for doers of good in both worlds"},
    "4:36": {"ar": "الإحسان بالوالدين وذوي القربى", "en": "Excellence toward parents and relatives"},
    "4:62": {"ar": "إرادة الإحسان في الصلح", "en": "Intending goodness in reconciliation"},
    "4:125": {"ar": "أحسن ديناً ممن أسلم وجهه لله", "en": "Best religion submitting to Allah doing good"},
    "4:128": {"ar": "الصلح بالإحسان", "en": "Reconciliation with goodness"},
    "5:13": {"ar": "العفو والإحسان", "en": "Pardoning and doing good"},
    "5:85": {"ar": "جزاء المحسنين الجنات", "en": "Gardens as reward for doers of good"},
    "5:93": {"ar": "الإيمان والتقوى والإحسان", "en": "Faith, piety and excellence"},
    "6:84": {"ar": "جزاء المحسنين بالهداية", "en": "Rewarding doers of good with guidance"},
    "6:154": {"ar": "إتمام النعمة على المحسن", "en": "Completing favor upon the doer of good"},
    "7:56": {"ar": "رحمة الله قريبة من المحسنين", "en": "Allah's mercy near the doers of good"},
    "9:91": {"ar": "ليس على المحسنين سبيل", "en": "No blame upon the doers of good"},
    "9:100": {"ar": "المحسنون من السابقين", "en": "Doers of good among the forerunners"},
    "9:120": {"ar": "جزاء المحسنين على مصابهم", "en": "Reward for doers of good in hardship"},
    "11:115": {"ar": "عدم ضياع أجر المحسنين", "en": "Reward of doers of good not lost"},
    "12:22": {"ar": "إيتاء المحسنين الحكم والعلم", "en": "Giving doers of good judgment and knowledge"},
    "12:36": {"ar": "يوسف من المحسنين", "en": "Yusuf among the doers of good"},
    "12:56": {"ar": "رحمة المحسنين", "en": "Mercy upon the doers of good"},
    "12:78": {"ar": "إنا نراك من المحسنين", "en": "We see you are of the doers of good"},
    "12:90": {"ar": "جزاء التقوى والصبر للمحسنين", "en": "Reward of piety and patience for good doers"},
    "14:12": {"ar": "التوكل والصبر من الإحسان", "en": "Trust and patience as part of excellence"},
    "16:30": {"ar": "حسنة في الدنيا للمحسنين", "en": "Good in this world for doers of good"},
    "16:90": {"ar": "الأمر بالعدل والإحسان", "en": "Command for justice and excellence"},
    "16:128": {"ar": "الله مع المتقين والمحسنين", "en": "Allah with the pious and doers of good"},
    "17:7": {"ar": "الإحسان أو الإساءة للنفس", "en": "Doing good or evil to oneself"},
    "18:30": {"ar": "عدم ضياع أجر المحسنين", "en": "Reward of doers of good not wasted"},
    "22:37": {"ar": "التقوى والإحسان في الأضاحي", "en": "Piety and excellence in sacrifices"},
    "28:14": {"ar": "جزاء المحسنين بالحكم والعلم", "en": "Rewarding doers of good with wisdom"},
    "28:77": {"ar": "أحسن كما أحسن الله إليك", "en": "Do good as Allah has done good to you"},
    "29:69": {"ar": "الله مع المحسنين", "en": "Allah is with the doers of good"},
    "31:2": {"ar": "الكتاب هدى للمحسنين", "en": "The Book as guidance for doers of good"},
    "31:3": {"ar": "البشرى للمحسنين", "en": "Glad tidings for doers of good"},
    "31:22": {"ar": "إسلام الوجه لله وهو محسن", "en": "Submitting to Allah while doing good"},
    "32:7": {"ar": "إحسان كل شيء خلقه", "en": "Excellence in all creation"},
    "33:29": {"ar": "أجر المحسنات من النساء", "en": "Reward for women who do good"},
    "37:80": {"ar": "جزاء المحسنين السلام", "en": "Peace as reward for doers of good"},
    "37:105": {"ar": "جزاء المحسنين على الطاعة", "en": "Reward for doers of good in obedience"},
    "37:110": {"ar": "جزاء المحسنين", "en": "Reward for the doers of good"},
    "37:121": {"ar": "جزاء موسى وهارون المحسنين", "en": "Reward for Moses and Aaron doing good"},
    "37:131": {"ar": "جزاء إلياس المحسن", "en": "Reward for Elias the doer of good"},
    "39:10": {"ar": "للمحسنين في الدنيا حسنة", "en": "Good in this world for doers of good"},
    "39:34": {"ar": "المحسنون يحصلون ما يشاءون", "en": "Doers of good get whatever they wish"},
    "39:58": {"ar": "المحسنون يكونون من المتقين", "en": "Doers of good will be among the pious"},
    "46:12": {"ar": "بشرى للمحسنين", "en": "Good news for the doers of good"},
    "51:16": {"ar": "المحسنون في جنات وعيون", "en": "Doers of good in gardens and springs"},
    "53:31": {"ar": "جزاء المحسنين بالحسنى", "en": "Rewarding doers of good with best reward"},
    "55:60": {"ar": "جزاء الإحسان إلا الإحسان", "en": "Reward of goodness is only goodness"},
    "77:44": {"ar": "جزاء المحسنين", "en": "Reward for the doers of good"},
}

# ============================================================================
# THEME_IMAN - Faith
# ============================================================================

THEME_IMAN = {
    "2:3": {"ar": "الإيمان بالغيب", "en": "Believing in the unseen"},
    "2:4": {"ar": "الإيمان بما أنزل من قبل", "en": "Believing in previous revelations"},
    "2:62": {"ar": "الإيمان بالله واليوم الآخر", "en": "Faith in Allah and the Last Day"},
    "2:165": {"ar": "حب المؤمنين لله أشد", "en": "Believers' love for Allah most intense"},
    "2:177": {"ar": "حقيقة البر والإيمان", "en": "True righteousness and faith"},
    "2:285": {"ar": "إيمان الرسول والمؤمنين", "en": "Faith of the Messenger and believers"},
    "3:16": {"ar": "دعاء المؤمنين للمغفرة", "en": "Believers' prayer for forgiveness"},
    "3:52": {"ar": "إيمان الحواريين", "en": "Faith of the disciples"},
    "3:84": {"ar": "الإيمان بجميع الأنبياء", "en": "Faith in all the prophets"},
    "3:110": {"ar": "خير أمة تؤمن بالله", "en": "Best nation believing in Allah"},
    "3:173": {"ar": "إيمان المؤمنين يزداد", "en": "Believers' faith increases"},
    "4:59": {"ar": "الإيمان يقتضي الطاعة", "en": "Faith requires obedience"},
    "4:136": {"ar": "الأمر بالإيمان الكامل", "en": "Command for complete faith"},
    "4:162": {"ar": "الإيمان الراسخ والجزاء", "en": "Firm faith and its reward"},
    "5:1": {"ar": "إيمان المؤمنين والوفاء بالعقود", "en": "Believers' faith and fulfilling contracts"},
    "5:111": {"ar": "إيمان الحواريين بالله ورسوله", "en": "Disciples' faith in Allah and messenger"},
    "7:75": {"ar": "الإيمان عند المستكبرين والمستضعفين", "en": "Faith among arrogant and oppressed"},
    "7:87": {"ar": "الصبر حتى يحكم الله للمؤمنين", "en": "Patience until Allah judges for believers"},
    "8:2": {"ar": "صفات المؤمنين الحقيقيين", "en": "Traits of true believers"},
    "8:4": {"ar": "المؤمنون حقاً لهم درجات", "en": "True believers have ranks"},
    "9:23": {"ar": "تقديم الإيمان على القرابة", "en": "Prioritizing faith over kinship"},
    "9:71": {"ar": "المؤمنون والمؤمنات أولياء", "en": "Believing men and women are allies"},
    "10:9": {"ar": "هداية المؤمنين بإيمانهم", "en": "Believers guided by their faith"},
    "10:84": {"ar": "التوكل مع الإيمان", "en": "Trust along with faith"},
    "16:97": {"ar": "الحياة الطيبة للمؤمنين", "en": "Good life for believers"},
    "18:30": {"ar": "جزاء الإيمان والعمل الصالح", "en": "Reward for faith and good deeds"},
    "23:1": {"ar": "فلاح المؤمنين", "en": "Success of the believers"},
    "24:62": {"ar": "صفات المؤمنين الحقيقيين", "en": "Traits of true believers"},
    "29:52": {"ar": "الإيمان بالله شهيداً", "en": "Faith in Allah as witness"},
    "32:15": {"ar": "سجود المؤمنين وتسبيحهم", "en": "Believers prostrating and glorifying"},
    "33:22": {"ar": "ثبات إيمان المؤمنين", "en": "Steadfastness of believers' faith"},
    "33:35": {"ar": "صفات المؤمنين والمؤمنات", "en": "Traits of believing men and women"},
    "35:7": {"ar": "الجزاء العظيم للمؤمنين", "en": "Great reward for believers"},
    "40:12": {"ar": "شهادة الكفار بإيمانهم", "en": "Disbelievers' testimony of faith"},
    "42:52": {"ar": "الإيمان نور من الله", "en": "Faith is a light from Allah"},
    "47:2": {"ar": "الإيمان بما نزل على محمد", "en": "Faith in what was revealed to Muhammad"},
    "48:4": {"ar": "زيادة إيمان المؤمنين", "en": "Increasing believers' faith"},
    "48:26": {"ar": "كلمة التقوى للمؤمنين", "en": "Word of piety for believers"},
    "49:7": {"ar": "حبب الله الإيمان للمؤمنين", "en": "Allah endeared faith to believers"},
    "49:14": {"ar": "الفرق بين الإسلام والإيمان", "en": "Difference between Islam and faith"},
    "49:15": {"ar": "صفات المؤمنين الحقيقيين", "en": "Traits of true believers"},
    "57:8": {"ar": "الدعوة للإيمان بالله ورسوله", "en": "Call to faith in Allah and messenger"},
    "57:19": {"ar": "درجات المؤمنين والصديقين", "en": "Ranks of believers and truthful"},
    "58:22": {"ar": "إيمان المؤمنين بالله ورسوله", "en": "Believers' faith in Allah and messenger"},
    "59:10": {"ar": "دعاء المؤمنين للإخوان", "en": "Believers' prayer for brethren"},
    "60:1": {"ar": "موالاة الكفار ونقض الإيمان", "en": "Allying with disbelievers and faith"},
    "64:8": {"ar": "الإيمان بالله ورسوله والنور", "en": "Faith in Allah, messenger and light"},
    "85:8": {"ar": "إيمان المؤمنين بالله العزيز", "en": "Believers' faith in Allah the Mighty"},
}

# ============================================================================
# THEME_SHUKR - Gratitude
# ============================================================================

THEME_SHUKR = {
    "2:52": {"ar": "الشكر بعد المغفرة", "en": "Gratitude after forgiveness"},
    "2:56": {"ar": "البعث للشكر", "en": "Resurrection for gratitude"},
    "2:152": {"ar": "اشكروا لي ولا تكفرون", "en": "Be grateful to Me and do not deny"},
    "2:172": {"ar": "الشكر على الطيبات", "en": "Gratitude for good provisions"},
    "2:185": {"ar": "الشكر على الهداية", "en": "Gratitude for guidance"},
    "3:123": {"ar": "الشكر بعد النصر", "en": "Gratitude after victory"},
    "3:144": {"ar": "جزاء الشاكرين", "en": "Reward for the grateful"},
    "3:145": {"ar": "ثواب الشاكرين", "en": "Recompense for the grateful"},
    "4:147": {"ar": "لا يعذب الله الشاكرين", "en": "Allah does not punish the grateful"},
    "5:6": {"ar": "الشكر على إتمام النعمة", "en": "Gratitude for completing favor"},
    "5:89": {"ar": "الشكر على الهداية", "en": "Gratitude for guidance"},
    "7:10": {"ar": "قلة الشكر على النعم", "en": "Little gratitude for blessings"},
    "7:17": {"ar": "أكثر الناس لا يشكرون", "en": "Most people are not grateful"},
    "7:58": {"ar": "صرف الآيات للشاكرين", "en": "Signs explained for the grateful"},
    "7:144": {"ar": "الأمر بالشكر على الاصطفاء", "en": "Command to be grateful for selection"},
    "7:189": {"ar": "الشكر على الذرية", "en": "Gratitude for offspring"},
    "8:26": {"ar": "الشكر على النصر والرزق", "en": "Gratitude for victory and provision"},
    "10:22": {"ar": "نسيان الشكر في الشدة", "en": "Forgetting gratitude in hardship"},
    "10:60": {"ar": "أكثر الناس لا يشكرون", "en": "Most people are not grateful"},
    "12:38": {"ar": "الشكر على فضل الله", "en": "Gratitude for Allah's favor"},
    "14:5": {"ar": "آيات للشاكرين الصابرين", "en": "Signs for grateful and patient"},
    "14:7": {"ar": "الزيادة مع الشكر", "en": "Increase with gratitude"},
    "14:37": {"ar": "الشكر على الرزق", "en": "Gratitude for provision"},
    "16:14": {"ar": "الشكر على نعم البحر", "en": "Gratitude for blessings of the sea"},
    "16:78": {"ar": "الشكر على السمع والبصر", "en": "Gratitude for hearing and sight"},
    "16:114": {"ar": "الشكر على الحلال الطيب", "en": "Gratitude for lawful good things"},
    "16:121": {"ar": "إبراهيم شاكراً لأنعم الله", "en": "Ibrahim grateful for Allah's blessings"},
    "21:80": {"ar": "الشكر على تعليم صناعة الدروع", "en": "Gratitude for teaching armor-making"},
    "22:36": {"ar": "الشكر على الأنعام", "en": "Gratitude for the livestock"},
    "23:78": {"ar": "قلة الشكر على الحواس", "en": "Little gratitude for senses"},
    "25:62": {"ar": "آيات لمن أراد الشكر", "en": "Signs for those who want to be grateful"},
    "27:15": {"ar": "شكر داود وسليمان", "en": "Gratitude of David and Solomon"},
    "27:19": {"ar": "دعاء سليمان للشكر", "en": "Solomon's prayer for gratitude"},
    "27:40": {"ar": "الشكر اختبار من الله", "en": "Gratitude as test from Allah"},
    "28:73": {"ar": "الشكر على الليل والنهار", "en": "Gratitude for night and day"},
    "29:17": {"ar": "الشكر لله لا للأصنام", "en": "Gratitude to Allah not idols"},
    "30:46": {"ar": "الشكر على الرياح الطيبة", "en": "Gratitude for good winds"},
    "31:12": {"ar": "شكر لقمان لله", "en": "Luqman's gratitude to Allah"},
    "31:14": {"ar": "الشكر لله وللوالدين", "en": "Gratitude to Allah and parents"},
    "31:31": {"ar": "آيات لكل صبار شكور", "en": "Signs for every patient, grateful one"},
    "34:13": {"ar": "الأمر بالشكر لآل داود", "en": "Command for David's family to be grateful"},
    "34:15": {"ar": "شكر سبأ على البركات", "en": "Sheba's gratitude for blessings"},
    "34:19": {"ar": "كفران النعمة", "en": "Ingratitude for blessings"},
    "35:12": {"ar": "الشكر على نعم البحرين", "en": "Gratitude for blessings of seas"},
    "36:35": {"ar": "الشكر على ثمرات الأرض", "en": "Gratitude for fruits of earth"},
    "36:73": {"ar": "الشكر على الأنعام", "en": "Gratitude for the cattle"},
    "39:7": {"ar": "الله غني عن الشكر", "en": "Allah is free from need of gratitude"},
    "39:66": {"ar": "الأمر بعبادة الله والشكر", "en": "Command to worship Allah and be grateful"},
    "40:61": {"ar": "فضل الله وقلة الشكر", "en": "Allah's favor and little gratitude"},
    "45:12": {"ar": "الشكر على تسخير البحر", "en": "Gratitude for subjugating the sea"},
    "46:15": {"ar": "شكر الوالدين والله", "en": "Gratitude to parents and Allah"},
    "54:35": {"ar": "نعمة الله على الشاكرين", "en": "Allah's favor upon the grateful"},
    "56:70": {"ar": "الشكر على الماء العذب", "en": "Gratitude for fresh water"},
    "67:23": {"ar": "قلة الشكر على الحواس", "en": "Little gratitude for the senses"},
    "76:3": {"ar": "الشكر أو الكفر", "en": "Gratitude or ingratitude"},
}

# ============================================================================
# THEME_SABR remaining (25 verses)
# ============================================================================

THEME_SABR_REMAINING = {
    "8:65": {"ar": "صبر المؤمنين في القتال", "en": "Believers' patience in fighting"},
    "8:66": {"ar": "تخفيف الله عن المؤمنين", "en": "Allah lightening burden on believers"},
    "11:49": {"ar": "الصبر والعاقبة للمتقين", "en": "Patience and good end for pious"},
    "13:22": {"ar": "صبر ابتغاء وجه الله", "en": "Patience seeking Allah's face"},
    "13:24": {"ar": "سلام على الصابرين", "en": "Peace upon the patient"},
    "14:5": {"ar": "آيات للصبار الشكور", "en": "Signs for every patient, grateful one"},
    "18:28": {"ar": "الصبر مع الصالحين", "en": "Patience with the righteous"},
    "19:65": {"ar": "الصبر في عبادة الله", "en": "Patience in worshipping Allah"},
    "20:130": {"ar": "الصبر على ما يقولون", "en": "Patience over what they say"},
    "25:20": {"ar": "الصبر على الابتلاء", "en": "Patience in trials"},
    "28:80": {"ar": "ثواب الصابرين", "en": "Reward for the patient"},
    "30:60": {"ar": "الصبر على وعد الله", "en": "Patience on Allah's promise"},
    "33:35": {"ar": "الصابرين والصابرات", "en": "Patient men and women"},
    "40:55": {"ar": "الصبر على الأذى", "en": "Patience against harm"},
    "40:77": {"ar": "الصبر وانتظار وعد الله", "en": "Patience awaiting Allah's promise"},
    "47:31": {"ar": "اختبار المؤمنين بالصبر", "en": "Testing believers with patience"},
    "50:39": {"ar": "الصبر على ما يقولون", "en": "Patience over what they say"},
    "52:48": {"ar": "الصبر لحكم الله", "en": "Patience for Allah's judgment"},
    "68:48": {"ar": "الصبر لحكم الرب", "en": "Patience for Lord's judgment"},
    "73:10": {"ar": "الصبر على الأذى", "en": "Patience against harm"},
    "76:12": {"ar": "جزاء صبرهم جنة وحريراً", "en": "Reward for patience: garden and silk"},
    "37:102": {"ar": "صبر إسماعيل على الذبح", "en": "Ismail's patience in sacrifice"},
    "38:44": {"ar": "ثناء الله على صبر أيوب", "en": "Allah's praise of Ayyub's patience"},
    "39:10": {"ar": "أجر الصابرين بغير حساب", "en": "Reward for patient without measure"},
    "41:35": {"ar": "الصبر والحظ العظيم", "en": "Patience and great fortune"},
}

# ============================================================================
# THEME_TAQWA - Piety (Sample of 217 verses - selecting key ones)
# ============================================================================

THEME_TAQWA = {
    "2:2": {"ar": "هدى للمتقين", "en": "Guidance for the pious"},
    "2:21": {"ar": "العبادة لتحقيق التقوى", "en": "Worship to achieve piety"},
    "2:41": {"ar": "التقوى والخوف من الله", "en": "Piety and fearing Allah"},
    "2:48": {"ar": "التقوى من عذاب يوم القيامة", "en": "Piety from Day of Judgment's punishment"},
    "2:177": {"ar": "البر والتقوى الحقيقية", "en": "True righteousness and piety"},
    "2:179": {"ar": "القصاص حياة للمتقين", "en": "Retribution is life for the pious"},
    "2:183": {"ar": "الصيام لتحقيق التقوى", "en": "Fasting to achieve piety"},
    "2:189": {"ar": "البر في التقوى", "en": "Righteousness is in piety"},
    "2:194": {"ar": "اتقوا الله في القتال", "en": "Fear Allah in fighting"},
    "2:196": {"ar": "التقوى في الحج", "en": "Piety in pilgrimage"},
    "2:197": {"ar": "خير الزاد التقوى", "en": "Best provision is piety"},
    "2:203": {"ar": "التقوى خير للإنسان", "en": "Piety is better for humans"},
    "2:206": {"ar": "العزة بالإثم ضد التقوى", "en": "Pride in sin against piety"},
    "2:212": {"ar": "المتقون فوق الكفار يوم القيامة", "en": "Pious above disbelievers on Judgment Day"},
    "2:223": {"ar": "التقوى في العلاقة الزوجية", "en": "Piety in marital relations"},
    "2:231": {"ar": "التقوى في الطلاق", "en": "Piety in divorce"},
    "2:233": {"ar": "التقوى في الرضاعة", "en": "Piety in nursing"},
    "2:237": {"ar": "التقوى في المهر", "en": "Piety in dowry"},
    "2:241": {"ar": "حق المطلقات على المتقين", "en": "Divorced women's right upon pious"},
    "2:278": {"ar": "ترك الربا من التقوى", "en": "Leaving usury is from piety"},
    "2:282": {"ar": "التقوى في المعاملات", "en": "Piety in transactions"},
    "2:283": {"ar": "التقوى في الأمانات", "en": "Piety in trusts"},
    "3:15": {"ar": "الجنة للمتقين", "en": "Paradise for the pious"},
    "3:76": {"ar": "الله يحب المتقين", "en": "Allah loves the pious"},
    "3:102": {"ar": "اتقوا الله حق تقاته", "en": "Fear Allah as He should be feared"},
    "3:123": {"ar": "التقوى والشكر بعد النصر", "en": "Piety and gratitude after victory"},
    "3:125": {"ar": "نصر الله للمتقين الصابرين", "en": "Allah's help for pious and patient"},
    "3:130": {"ar": "اتقاء الربا", "en": "Avoiding usury through piety"},
    "3:131": {"ar": "اتقاء النار المعدة للكافرين", "en": "Avoiding fire prepared for disbelievers"},
    "3:133": {"ar": "الجنة للمتقين", "en": "Paradise for the pious"},
    "3:138": {"ar": "هدى وموعظة للمتقين", "en": "Guidance and admonition for pious"},
    "3:172": {"ar": "أجر المتقين المحسنين", "en": "Reward for pious good doers"},
    "3:179": {"ar": "التقوى تميز المؤمنين", "en": "Piety distinguishes believers"},
    "3:186": {"ar": "الصبر والتقوى من عزم الأمور", "en": "Patience and piety of firm resolve"},
    "3:198": {"ar": "الجنات للمتقين", "en": "Gardens for the pious"},
    "3:200": {"ar": "التقوى طريق الفلاح", "en": "Piety is path to success"},
    "4:1": {"ar": "التقوى في صلة الأرحام", "en": "Piety in maintaining kinship"},
    "4:9": {"ar": "التقوى في حفظ اليتامى", "en": "Piety in protecting orphans"},
    "4:77": {"ar": "التقوى خير من الدنيا", "en": "Piety better than worldly life"},
    "4:128": {"ar": "التقوى والإحسان", "en": "Piety and excellence"},
    "4:129": {"ar": "التقوى في تعدد الزوجات", "en": "Piety in polygamy"},
    "4:131": {"ar": "التقوى وصية الله للأولين والآخرين", "en": "Piety: Allah's command to all"},
    "5:2": {"ar": "التعاون على البر والتقوى", "en": "Cooperating in righteousness and piety"},
    "5:4": {"ar": "التقوى في الصيد", "en": "Piety in hunting"},
    "5:7": {"ar": "التقوى في الوفاء بالعهد", "en": "Piety in fulfilling covenant"},
    "5:8": {"ar": "العدل أقرب للتقوى", "en": "Justice is closest to piety"},
    "5:11": {"ar": "التقوى والتوكل", "en": "Piety and trust"},
    "5:27": {"ar": "قبول الله من المتقين", "en": "Allah accepts from the pious"},
    "5:35": {"ar": "التقوى والوسيلة إلى الله", "en": "Piety and means to Allah"},
    "5:57": {"ar": "التقوى والموالاة", "en": "Piety and allegiance"},
    "5:65": {"ar": "التقوى تكفر السيئات", "en": "Piety expiates evil deeds"},
    "5:88": {"ar": "التقوى في الأكل الحلال", "en": "Piety in eating lawful food"},
    "5:93": {"ar": "الإيمان والتقوى والإحسان", "en": "Faith, piety and excellence"},
    "5:96": {"ar": "التقوى في صيد البحر", "en": "Piety in sea hunting"},
    "5:100": {"ar": "التقوى تميز الطيب من الخبيث", "en": "Piety distinguishes good from evil"},
    "5:108": {"ar": "التقوى في الشهادة", "en": "Piety in testimony"},
    "5:112": {"ar": "التقوى في الدعاء", "en": "Piety in supplication"},
    "6:32": {"ar": "الآخرة خير للمتقين", "en": "Hereafter better for the pious"},
    "6:51": {"ar": "إنذار الذين يخافون ربهم", "en": "Warning those who fear their Lord"},
    "6:69": {"ar": "ذكرى للمتقين", "en": "Reminder for the pious"},
    "6:72": {"ar": "الأمر بالتقوى والصلاة", "en": "Command for piety and prayer"},
    "6:153": {"ar": "الصراط المستقيم طريق التقوى", "en": "Straight path is way of piety"},
    "6:155": {"ar": "القرآن مبارك للمتقين", "en": "Quran blessed for the pious"},
    "7:26": {"ar": "لباس التقوى خير", "en": "Clothing of piety is best"},
    "7:35": {"ar": "المتقون لا خوف عليهم", "en": "No fear upon the pious"},
    "7:63": {"ar": "التقوى طريق النجاة", "en": "Piety is path to salvation"},
    "7:65": {"ar": "دعوة هود للتقوى", "en": "Hud calling to piety"},
    "7:96": {"ar": "بركات السماء للمتقين", "en": "Heavenly blessings for pious"},
    "7:128": {"ar": "العاقبة للمتقين", "en": "Good end for the pious"},
    "7:156": {"ar": "رحمة الله للمتقين", "en": "Allah's mercy for the pious"},
    "7:164": {"ar": "الموعظة للمتقين", "en": "Admonition for the pious"},
    "7:169": {"ar": "الآخرة خير للمتقين", "en": "Hereafter better for pious"},
    "7:171": {"ar": "التمسك بالكتاب والتقوى", "en": "Holding Book firmly and piety"},
    "7:201": {"ar": "تذكر المتقين عند الشيطان", "en": "Pious remember when Satan whispers"},
    "8:1": {"ar": "التقوى وإصلاح ذات البين", "en": "Piety and reconciliation"},
    "8:29": {"ar": "التقوى تميز الحق من الباطل", "en": "Piety distinguishes truth from falsehood"},
    "8:34": {"ar": "أولياء المسجد الحرام هم المتقون", "en": "Guardians of Sacred Mosque are pious"},
    "8:56": {"ar": "نقض العهد ضد التقوى", "en": "Breaking covenant against piety"},
    "8:69": {"ar": "الغنائم للمتقين", "en": "War gains for the pious"},
    "9:4": {"ar": "الوفاء بالعهد للمتقين", "en": "Fulfilling covenant with the pious"},
    "9:7": {"ar": "التقوى في المعاهدات", "en": "Piety in treaties"},
    "9:36": {"ar": "قتال المشركين والتقوى", "en": "Fighting polytheists and piety"},
    "9:44": {"ar": "إذن القتال للمتقين", "en": "Permission to fight for pious"},
    "9:108": {"ar": "المسجد المؤسس على التقوى", "en": "Mosque founded on piety"},
    "9:109": {"ar": "التقوى أساس البناء", "en": "Piety as foundation of building"},
    "9:115": {"ar": "بيان الله للمتقين", "en": "Allah's clarification for pious"},
    "9:119": {"ar": "الأمر بالتقوى والصدق", "en": "Command for piety and truthfulness"},
    "9:123": {"ar": "قتال الكفار والتقوى", "en": "Fighting disbelievers with piety"},
    "10:6": {"ar": "آيات للمتقين", "en": "Signs for the pious"},
    "10:31": {"ar": "التقوى في شكر النعم", "en": "Piety in gratitude for blessings"},
    "10:63": {"ar": "أولياء الله المتقون", "en": "Allies of Allah are the pious"},
    "12:57": {"ar": "أجر الآخرة للمتقين", "en": "Reward of Hereafter for pious"},
    "12:90": {"ar": "جزاء التقوى والصبر", "en": "Reward for piety and patience"},
    "12:109": {"ar": "الآخرة خير للمتقين", "en": "Hereafter better for pious"},
    "13:35": {"ar": "جنة المتقين", "en": "Paradise of the pious"},
    "15:45": {"ar": "المتقون في جنات وعيون", "en": "Pious in gardens and springs"},
    "16:30": {"ar": "الحسنى للمتقين", "en": "Best reward for the pious"},
    "16:31": {"ar": "جنات عدن للمتقين", "en": "Gardens of Eden for pious"},
    "16:52": {"ar": "التقوى لله وحده", "en": "Piety for Allah alone"},
    "16:128": {"ar": "الله مع المتقين", "en": "Allah is with the pious"},
    "19:13": {"ar": "التقوى من صفات يحيى", "en": "Piety among Yahya's traits"},
    "19:18": {"ar": "الاستعاذة بالرحمن للمتقين", "en": "Seeking refuge in Merciful for pious"},
    "19:63": {"ar": "الجنة للمتقين", "en": "Paradise for the pious"},
    "19:72": {"ar": "نجاة المتقين من النار", "en": "Saving pious from Fire"},
    "19:85": {"ar": "حشر المتقين وفداً", "en": "Gathering pious as delegation"},
    "19:97": {"ar": "البشرى للمتقين", "en": "Good news for the pious"},
    "39:10": {"ar": "للمتقين في الدنيا حسنة", "en": "Good in this world for pious"},
    "39:20": {"ar": "غرف المتقين في الجنة", "en": "Chambers for pious in Paradise"},
    "39:33": {"ar": "المتقون هم الصادقون", "en": "The pious are the truthful"},
    "43:67": {"ar": "صداقة المتقين يوم القيامة", "en": "Friendship of pious on Judgment Day"},
    "44:51": {"ar": "المتقين في مقام أمين", "en": "Pious in secure station"},
    "47:15": {"ar": "وصف جنة المتقين", "en": "Description of pious' Paradise"},
    "47:17": {"ar": "زيادة الهدى للمتقين", "en": "Increase in guidance for pious"},
    "47:36": {"ar": "أجر المتقين", "en": "Reward for the pious"},
    "50:31": {"ar": "تقريب الجنة للمتقين", "en": "Paradise brought near for pious"},
    "51:15": {"ar": "المتقين في جنات وعيون", "en": "Pious in gardens and springs"},
    "52:17": {"ar": "المتقين في جنات ونعيم", "en": "Pious in gardens and bliss"},
    "54:54": {"ar": "المتقين في جنات ونهر", "en": "Pious in gardens and river"},
    "68:34": {"ar": "جنات النعيم للمتقين", "en": "Gardens of bliss for pious"},
    "77:41": {"ar": "المتقين في ظلال وعيون", "en": "Pious in shade and springs"},
    "78:31": {"ar": "مفاز للمتقين", "en": "Triumph for the pious"},
    "92:5": {"ar": "التيسير لليسرى للمتقين", "en": "Easing toward ease for pious"},
}


def parse_verse_ref(verse_ref: str) -> tuple[int, int]:
    """Parse verse reference like '2:87' into (sura_no, ayah_start)."""
    parts = verse_ref.split(":")
    return int(parts[0]), int(parts[1])


async def populate_topics():
    """Populate topic descriptions for theme occurrences."""

    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    all_topics = {
        "theme_dhikr": THEME_DHIKR,
        "theme_ihsan": THEME_IHSAN,
        "theme_iman": THEME_IMAN,
        "theme_shukr": THEME_SHUKR,
        "theme_sabr": THEME_SABR_REMAINING,
        "theme_taqwa": THEME_TAQWA,
    }

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
