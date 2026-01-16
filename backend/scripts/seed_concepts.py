#!/usr/bin/env python3
"""
Seed Quranic Concepts from Existing Data

This script populates the concepts table with:
1. Prophets (from stories/NER data)
2. Places (from stories/NER data)
3. Nations (from stories)
4. Miracles (from MiraclesService)
5. Themes (from existing theme data)

All concepts are grounded in Quranic text with verse references.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from sqlalchemy import text
from app.db.database import get_async_session_context


# ============================================================================
# PROPHETS DATA (Quranic Prophets with Arabic names and verse occurrences)
# ============================================================================
PROPHETS = [
    {
        "id": "person_adam",
        "slug": "adam",
        "label_ar": "آدم عليه السلام",
        "label_en": "Adam (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["آدم", "أبو البشر"],
        "aliases_en": ["Adam", "Father of Mankind"],
        "description_ar": "أول البشر وأول الأنبياء، خلقه الله من طين وأسكنه الجنة",
        "description_en": "The first human and first prophet, created by Allah from clay",
        "icon_hint": "user",
        "verses": [(2, 31), (2, 34), (2, 35), (2, 37), (3, 33), (7, 11), (7, 19), (17, 61), (18, 50), (20, 115), (20, 117), (20, 121)]
    },
    {
        "id": "person_nuh",
        "slug": "nuh",
        "label_ar": "نوح عليه السلام",
        "label_en": "Noah (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["نوح", "شيخ المرسلين"],
        "aliases_en": ["Noah", "Nuh"],
        "description_ar": "نبي أرسله الله إلى قومه فدعاهم ألف سنة إلا خمسين عاماً",
        "description_en": "Prophet sent to his people, called them for 950 years",
        "icon_hint": "user",
        "verses": [(7, 59), (7, 64), (10, 71), (11, 25), (11, 32), (11, 36), (11, 42), (11, 45), (11, 48), (21, 76), (23, 23), (26, 105), (26, 116), (29, 14), (37, 75), (54, 9), (71, 1), (71, 21), (71, 26)]
    },
    {
        "id": "person_ibrahim",
        "slug": "ibrahim",
        "label_ar": "إبراهيم عليه السلام",
        "label_en": "Abraham (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["إبراهيم", "الخليل", "أبو الأنبياء"],
        "aliases_en": ["Abraham", "Ibrahim", "The Friend of Allah"],
        "description_ar": "خليل الله، أبو الأنبياء، بنى الكعبة مع ابنه إسماعيل",
        "description_en": "The Friend of Allah, Father of Prophets, built the Kaaba",
        "icon_hint": "user",
        "verses": [(2, 124), (2, 125), (2, 127), (2, 130), (2, 135), (2, 258), (2, 260), (3, 33), (3, 65), (3, 67), (4, 125), (6, 74), (6, 75), (6, 83), (9, 114), (11, 69), (11, 74), (14, 35), (15, 51), (19, 41), (21, 51), (21, 60), (21, 68), (22, 26), (26, 69), (29, 16), (37, 83), (37, 99), (37, 109), (43, 26), (51, 24), (60, 4)]
    },
    {
        "id": "person_musa",
        "slug": "musa",
        "label_ar": "موسى عليه السلام",
        "label_en": "Moses (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["موسى", "كليم الله"],
        "aliases_en": ["Moses", "Musa", "The one who spoke to Allah"],
        "description_ar": "كليم الله، أرسله الله إلى فرعون وبني إسرائيل، أنزلت عليه التوراة",
        "description_en": "The one who spoke to Allah, sent to Pharaoh and Children of Israel",
        "icon_hint": "user",
        "verses": [(2, 51), (2, 53), (2, 60), (2, 67), (2, 87), (2, 92), (2, 108), (2, 136), (4, 153), (4, 164), (5, 20), (5, 22), (5, 24), (6, 84), (6, 154), (7, 103), (7, 117), (7, 127), (7, 128), (7, 138), (7, 142), (7, 143), (7, 150), (7, 154), (7, 159), (10, 75), (10, 77), (10, 84), (11, 17), (11, 96), (11, 110), (14, 5), (17, 2), (17, 101), (18, 60), (19, 51), (20, 9), (20, 17), (20, 36), (20, 40), (20, 49), (20, 77), (20, 83), (20, 88), (23, 45), (25, 35), (26, 10), (26, 43), (26, 52), (26, 61), (27, 7), (27, 10), (28, 3), (28, 7), (28, 10), (28, 15), (28, 18), (28, 20), (28, 29), (28, 30), (28, 36), (28, 43), (28, 48), (28, 76), (29, 39), (32, 23), (33, 7), (33, 69), (37, 114), (37, 120), (40, 23), (40, 27), (40, 53), (41, 45), (42, 13), (43, 46), (44, 17), (46, 12), (46, 30), (51, 38), (53, 36), (61, 5), (73, 15), (79, 15), (87, 19)]
    },
    {
        "id": "person_isa",
        "slug": "isa",
        "label_ar": "عيسى عليه السلام",
        "label_en": "Jesus (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["عيسى", "المسيح", "ابن مريم", "روح الله", "كلمة الله"],
        "aliases_en": ["Jesus", "Isa", "The Messiah", "Son of Mary"],
        "description_ar": "المسيح ابن مريم، كلمة الله وروح منه، أيده الله بالمعجزات",
        "description_en": "The Messiah, son of Mary, Word of Allah and Spirit from Him",
        "icon_hint": "user",
        "verses": [(2, 87), (2, 136), (2, 253), (3, 45), (3, 52), (3, 55), (3, 59), (3, 84), (4, 157), (4, 163), (4, 171), (5, 46), (5, 72), (5, 75), (5, 78), (5, 110), (5, 112), (5, 114), (5, 116), (6, 85), (19, 34), (21, 91), (23, 50), (33, 7), (42, 13), (43, 57), (43, 63), (57, 27), (61, 6), (61, 14)]
    },
    {
        "id": "person_muhammad",
        "slug": "muhammad",
        "label_ar": "محمد صلى الله عليه وسلم",
        "label_en": "Muhammad (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["محمد", "أحمد", "الرسول", "النبي", "خاتم النبيين"],
        "aliases_en": ["Muhammad", "Ahmad", "The Messenger", "The Prophet", "Seal of Prophets"],
        "description_ar": "خاتم النبيين والمرسلين، أرسله الله رحمة للعالمين",
        "description_en": "The Seal of the Prophets, sent as a mercy to all worlds",
        "icon_hint": "user",
        "verses": [(3, 144), (33, 40), (47, 2), (48, 29), (61, 6)]
    },
    {
        "id": "person_yusuf",
        "slug": "yusuf",
        "label_ar": "يوسف عليه السلام",
        "label_en": "Joseph (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["يوسف", "الصديق"],
        "aliases_en": ["Joseph", "Yusuf", "The Truthful"],
        "description_ar": "نبي الله يوسف، أعطاه الله الحكمة والجمال وتأويل الأحاديث",
        "description_en": "Prophet of Allah, given wisdom, beauty, and dream interpretation",
        "icon_hint": "user",
        "verses": [(6, 84), (12, 4), (12, 7), (12, 8), (12, 9), (12, 10), (12, 11), (12, 16), (12, 17), (12, 21), (12, 29), (12, 36), (12, 46), (12, 51), (12, 56), (12, 58), (12, 69), (12, 77), (12, 84), (12, 87), (12, 90), (12, 94), (12, 99), (12, 100), (40, 34)]
    },
    {
        "id": "person_dawud",
        "slug": "dawud",
        "label_ar": "داود عليه السلام",
        "label_en": "David (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["داود"],
        "aliases_en": ["David", "Dawud"],
        "description_ar": "نبي الله داود، آتاه الله الزبور وألان له الحديد",
        "description_en": "Prophet of Allah, given the Psalms and softened iron for him",
        "icon_hint": "user",
        "verses": [(2, 251), (4, 163), (5, 78), (6, 84), (17, 55), (21, 78), (21, 79), (27, 15), (27, 16), (34, 10), (34, 13), (38, 17), (38, 22), (38, 24), (38, 26), (38, 30)]
    },
    {
        "id": "person_sulayman",
        "slug": "sulayman",
        "label_ar": "سليمان عليه السلام",
        "label_en": "Solomon (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["سليمان"],
        "aliases_en": ["Solomon", "Sulayman"],
        "description_ar": "نبي الله سليمان، ورث داود وسخر الله له الجن والريح",
        "description_en": "Prophet of Allah, inherited David, given control over jinn and wind",
        "icon_hint": "user",
        "verses": [(2, 102), (4, 163), (6, 84), (21, 78), (21, 79), (21, 81), (27, 15), (27, 16), (27, 17), (27, 18), (27, 30), (27, 36), (27, 44), (34, 12), (34, 14), (38, 30), (38, 34), (38, 36)]
    },
    {
        "id": "person_yunus",
        "slug": "yunus",
        "label_ar": "يونس عليه السلام",
        "label_en": "Jonah (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["يونس", "ذو النون", "صاحب الحوت"],
        "aliases_en": ["Jonah", "Yunus", "The one of the whale"],
        "description_ar": "نبي الله يونس، التقمه الحوت ثم نجاه الله",
        "description_en": "Prophet of Allah, swallowed by the whale then saved by Allah",
        "icon_hint": "user",
        "verses": [(4, 163), (6, 86), (10, 98), (21, 87), (37, 139), (37, 142), (37, 145), (68, 48)]
    },
    {
        "id": "person_ayyub",
        "slug": "ayyub",
        "label_ar": "أيوب عليه السلام",
        "label_en": "Job (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["أيوب"],
        "aliases_en": ["Job", "Ayyub"],
        "description_ar": "نبي الله أيوب، ضرب المثل في الصبر على البلاء",
        "description_en": "Prophet of Allah, exemplar of patience in affliction",
        "icon_hint": "user",
        "verses": [(4, 163), (6, 84), (21, 83), (21, 84), (38, 41), (38, 42), (38, 44)]
    },
    {
        "id": "person_ismail",
        "slug": "ismail",
        "label_ar": "إسماعيل عليه السلام",
        "label_en": "Ishmael (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["إسماعيل", "الذبيح"],
        "aliases_en": ["Ishmael", "Ismail"],
        "description_ar": "ابن إبراهيم، ساعد أباه في بناء الكعبة، الذبيح",
        "description_en": "Son of Abraham, helped build the Kaaba, the sacrificed one",
        "icon_hint": "user",
        "verses": [(2, 125), (2, 127), (2, 133), (2, 136), (3, 84), (4, 163), (6, 86), (14, 39), (19, 54), (21, 85), (37, 102), (38, 48)]
    },
    {
        "id": "person_ishaq",
        "slug": "ishaq",
        "label_ar": "إسحاق عليه السلام",
        "label_en": "Isaac (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["إسحاق"],
        "aliases_en": ["Isaac", "Ishaq"],
        "description_ar": "ابن إبراهيم من سارة، والد يعقوب",
        "description_en": "Son of Abraham from Sarah, father of Jacob",
        "icon_hint": "user",
        "verses": [(2, 133), (2, 136), (3, 84), (4, 163), (6, 84), (11, 71), (12, 6), (14, 39), (19, 49), (21, 72), (29, 27), (37, 112), (38, 45)]
    },
    {
        "id": "person_yaqub",
        "slug": "yaqub",
        "label_ar": "يعقوب عليه السلام",
        "label_en": "Jacob (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["يعقوب", "إسرائيل"],
        "aliases_en": ["Jacob", "Yaqub", "Israel"],
        "description_ar": "ابن إسحاق، والد يوسف والأسباط، إسرائيل",
        "description_en": "Son of Isaac, father of Joseph and the tribes",
        "icon_hint": "user",
        "verses": [(2, 132), (2, 133), (2, 136), (3, 84), (4, 163), (6, 84), (11, 71), (12, 4), (12, 6), (12, 38), (12, 68), (12, 84), (12, 93), (19, 6), (19, 49), (21, 72), (29, 27), (38, 45)]
    },
    {
        "id": "person_harun",
        "slug": "harun",
        "label_ar": "هارون عليه السلام",
        "label_en": "Aaron (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["هارون"],
        "aliases_en": ["Aaron", "Harun"],
        "description_ar": "أخو موسى ووزيره، أرسله الله معه إلى فرعون",
        "description_en": "Brother and helper of Moses, sent to Pharaoh",
        "icon_hint": "user",
        "verses": [(4, 163), (6, 84), (7, 122), (7, 142), (7, 150), (10, 75), (19, 28), (19, 53), (20, 30), (20, 70), (20, 90), (20, 92), (21, 48), (23, 45), (25, 35), (26, 13), (26, 48), (28, 34), (37, 114), (37, 120)]
    },
    {
        "id": "person_zakariyya",
        "slug": "zakariyya",
        "label_ar": "زكريا عليه السلام",
        "label_en": "Zechariah (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["زكريا"],
        "aliases_en": ["Zechariah", "Zakariyya"],
        "description_ar": "نبي الله زكريا، كفل مريم ودعا ربه للولد",
        "description_en": "Prophet of Allah, guardian of Mary, prayed for a child",
        "icon_hint": "user",
        "verses": [(3, 37), (3, 38), (6, 85), (19, 2), (19, 7), (21, 89), (21, 90)]
    },
    {
        "id": "person_yahya",
        "slug": "yahya",
        "label_ar": "يحيى عليه السلام",
        "label_en": "John (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["يحيى"],
        "aliases_en": ["John", "Yahya", "John the Baptist"],
        "description_ar": "ابن زكريا، مصدقاً بكلمة من الله حصوراً",
        "description_en": "Son of Zechariah, confirmer of a Word from Allah",
        "icon_hint": "user",
        "verses": [(3, 39), (6, 85), (19, 7), (19, 12), (21, 90)]
    },
    {
        "id": "person_salih",
        "slug": "salih",
        "label_ar": "صالح عليه السلام",
        "label_en": "Salih (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["صالح"],
        "aliases_en": ["Salih"],
        "description_ar": "نبي أرسله الله إلى ثمود وآتاه الناقة آية",
        "description_en": "Prophet sent to Thamud, given the she-camel as a sign",
        "icon_hint": "user",
        "verses": [(7, 73), (7, 77), (7, 79), (11, 61), (11, 62), (11, 66), (11, 89), (26, 141), (26, 142), (27, 45), (27, 48)]
    },
    {
        "id": "person_hud",
        "slug": "hud",
        "label_ar": "هود عليه السلام",
        "label_en": "Hud (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["هود"],
        "aliases_en": ["Hud"],
        "description_ar": "نبي أرسله الله إلى قوم عاد",
        "description_en": "Prophet sent to the people of Aad",
        "icon_hint": "user",
        "verses": [(7, 65), (7, 67), (7, 72), (11, 50), (11, 53), (11, 58), (11, 60), (11, 89), (26, 124), (26, 125), (46, 21)]
    },
    {
        "id": "person_shuayb",
        "slug": "shuayb",
        "label_ar": "شعيب عليه السلام",
        "label_en": "Shuayb (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["شعيب", "خطيب الأنبياء"],
        "aliases_en": ["Shuayb", "Jethro"],
        "description_ar": "نبي أرسله الله إلى أهل مدين وأصحاب الأيكة",
        "description_en": "Prophet sent to the people of Madyan",
        "icon_hint": "user",
        "verses": [(7, 85), (7, 88), (7, 90), (7, 92), (11, 84), (11, 87), (11, 91), (11, 94), (26, 177), (28, 23), (29, 36)]
    },
    {
        "id": "person_lut",
        "slug": "lut",
        "label_ar": "لوط عليه السلام",
        "label_en": "Lot (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["لوط"],
        "aliases_en": ["Lot", "Lut"],
        "description_ar": "نبي أرسله الله إلى قومه الذين كانوا يأتون الفاحشة",
        "description_en": "Prophet sent to his people who committed immorality",
        "icon_hint": "user",
        "verses": [(6, 86), (7, 80), (7, 83), (11, 70), (11, 74), (11, 77), (11, 81), (11, 89), (15, 59), (15, 61), (21, 71), (21, 74), (22, 43), (26, 160), (27, 54), (27, 56), (29, 26), (29, 28), (29, 33), (37, 133), (38, 13), (50, 13), (51, 32), (54, 33), (54, 34), (66, 10)]
    },
    {
        "id": "person_idris",
        "slug": "idris",
        "label_ar": "إدريس عليه السلام",
        "label_en": "Idris (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["إدريس"],
        "aliases_en": ["Idris", "Enoch"],
        "description_ar": "نبي ذكره الله في القرآن ورفعه مكاناً علياً",
        "description_en": "Prophet mentioned in the Quran, raised to a high station",
        "icon_hint": "user",
        "verses": [(19, 56), (21, 85)]
    },
    {
        "id": "person_dhulkifl",
        "slug": "dhulkifl",
        "label_ar": "ذو الكفل عليه السلام",
        "label_en": "Dhul-Kifl (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["ذو الكفل"],
        "aliases_en": ["Dhul-Kifl"],
        "description_ar": "نبي ذكره الله مع الصابرين",
        "description_en": "Prophet mentioned among the patient ones",
        "icon_hint": "user",
        "verses": [(21, 85), (38, 48)]
    },
    {
        "id": "person_alyasa",
        "slug": "alyasa",
        "label_ar": "اليسع عليه السلام",
        "label_en": "Elisha (peace be upon him)",
        "concept_type": "person",
        "aliases_ar": ["اليسع"],
        "aliases_en": ["Elisha", "Al-Yasa"],
        "description_ar": "نبي ذكره الله من الأخيار",
        "description_en": "Prophet mentioned among the chosen ones",
        "icon_hint": "user",
        "verses": [(6, 86), (38, 48)]
    },
]

# ============================================================================
# PLACES DATA
# ============================================================================
PLACES = [
    {
        "id": "place_makkah",
        "slug": "makkah",
        "label_ar": "مكة المكرمة",
        "label_en": "Makkah",
        "concept_type": "place",
        "aliases_ar": ["مكة", "بكة", "أم القرى", "البلد الأمين"],
        "aliases_en": ["Mecca", "Makkah", "Bakkah"],
        "description_ar": "أقدس بقعة على وجه الأرض، فيها الكعبة المشرفة",
        "description_en": "The holiest place on earth, location of the Sacred Kaaba",
        "icon_hint": "map-pin",
        "verses": [(3, 96), (48, 24), (95, 3)]
    },
    {
        "id": "place_madinah",
        "slug": "madinah",
        "label_ar": "المدينة المنورة",
        "label_en": "Madinah",
        "concept_type": "place",
        "aliases_ar": ["المدينة", "يثرب", "طيبة"],
        "aliases_en": ["Medina", "Madinah", "Yathrib"],
        "description_ar": "مدينة رسول الله وموضع مسجده وقبره الشريف",
        "description_en": "City of the Prophet, location of his mosque and blessed grave",
        "icon_hint": "map-pin",
        "verses": [(9, 101), (9, 120), (33, 60), (63, 8)]
    },
    {
        "id": "place_misr",
        "slug": "misr",
        "label_ar": "مصر",
        "label_en": "Egypt",
        "concept_type": "place",
        "aliases_ar": ["مصر"],
        "aliases_en": ["Egypt", "Misr"],
        "description_ar": "أرض الأنبياء، مكان قصص يوسف وموسى وفرعون",
        "description_en": "Land of the Prophets, setting for Joseph and Moses stories",
        "icon_hint": "map-pin",
        "verses": [(2, 61), (10, 87), (12, 21), (12, 99), (43, 51)]
    },
    {
        "id": "place_baytulmaqdis",
        "slug": "baytulmaqdis",
        "label_ar": "بيت المقدس",
        "label_en": "Jerusalem",
        "concept_type": "place",
        "aliases_ar": ["بيت المقدس", "الأرض المقدسة", "المسجد الأقصى"],
        "aliases_en": ["Jerusalem", "Al-Quds", "Al-Aqsa"],
        "description_ar": "الأرض المباركة وقبلة الأنبياء الأولى",
        "description_en": "The blessed land and first qiblah of the prophets",
        "icon_hint": "map-pin",
        "verses": [(17, 1), (5, 21), (21, 71), (21, 81)]
    },
    {
        "id": "place_sinai",
        "slug": "sinai",
        "label_ar": "سيناء",
        "label_en": "Sinai",
        "concept_type": "place",
        "aliases_ar": ["سيناء", "طور سينين", "الطور"],
        "aliases_en": ["Sinai", "Mount Sinai", "Tur"],
        "description_ar": "الجبل الذي كلم الله عليه موسى",
        "description_en": "The mountain where Allah spoke to Moses",
        "icon_hint": "map-pin",
        "verses": [(7, 143), (19, 52), (20, 80), (23, 20), (28, 29), (28, 46), (52, 1), (95, 2)]
    },
]

# ============================================================================
# NATIONS DATA
# ============================================================================
NATIONS = [
    {
        "id": "nation_bani_israil",
        "slug": "bani-israil",
        "label_ar": "بنو إسرائيل",
        "label_en": "Children of Israel",
        "concept_type": "nation",
        "aliases_ar": ["بنو إسرائيل", "اليهود"],
        "aliases_en": ["Children of Israel", "Israelites", "Bani Israel"],
        "description_ar": "ذرية يعقوب عليه السلام، أنعم الله عليهم ثم عصوا",
        "description_en": "Descendants of Jacob, blessed by Allah then disobeyed",
        "icon_hint": "users",
        "verses": [(2, 40), (2, 47), (2, 83), (2, 122), (3, 49), (5, 12), (5, 70), (7, 105), (7, 134), (10, 90), (17, 2), (17, 4), (20, 47), (26, 17), (26, 59), (27, 76), (32, 23), (40, 53), (44, 30), (45, 16), (46, 10)]
    },
    {
        "id": "nation_qawm_nuh",
        "slug": "qawm-nuh",
        "label_ar": "قوم نوح",
        "label_en": "People of Noah",
        "concept_type": "nation",
        "aliases_ar": ["قوم نوح"],
        "aliases_en": ["People of Noah"],
        "description_ar": "أول أمة أشركت بالله وأغرقها بالطوفان",
        "description_en": "First nation to commit shirk, drowned in the flood",
        "icon_hint": "users",
        "verses": [(7, 64), (10, 71), (11, 25), (23, 23), (25, 37), (26, 105), (29, 14), (37, 75), (50, 12), (53, 52), (54, 9), (71, 1)]
    },
    {
        "id": "nation_aad",
        "slug": "aad",
        "label_ar": "عاد",
        "label_en": "Aad",
        "concept_type": "nation",
        "aliases_ar": ["عاد", "قوم هود"],
        "aliases_en": ["Aad", "People of Hud"],
        "description_ar": "قوم هود، أهلكهم الله بالريح العقيم",
        "description_en": "People of Hud, destroyed by a barren wind",
        "icon_hint": "users",
        "verses": [(7, 65), (7, 74), (9, 70), (11, 50), (11, 59), (14, 9), (22, 42), (25, 38), (26, 123), (29, 38), (38, 12), (40, 31), (41, 13), (41, 15), (46, 21), (50, 13), (51, 41), (53, 50), (54, 18), (69, 4), (69, 6), (89, 6)]
    },
    {
        "id": "nation_thamud",
        "slug": "thamud",
        "label_ar": "ثمود",
        "label_en": "Thamud",
        "concept_type": "nation",
        "aliases_ar": ["ثمود", "قوم صالح"],
        "aliases_en": ["Thamud", "People of Salih"],
        "description_ar": "قوم صالح، عقروا الناقة فأهلكهم الله بالصيحة",
        "description_en": "People of Salih, killed the she-camel and were destroyed",
        "icon_hint": "users",
        "verses": [(7, 73), (7, 78), (9, 70), (11, 61), (11, 68), (11, 95), (14, 9), (17, 59), (22, 42), (25, 38), (26, 141), (27, 45), (29, 38), (38, 13), (40, 31), (41, 13), (41, 17), (50, 12), (51, 43), (53, 51), (54, 23), (69, 4), (69, 5), (85, 18), (89, 9), (91, 11)]
    },
    {
        "id": "nation_qawm_lut",
        "slug": "qawm-lut",
        "label_ar": "قوم لوط",
        "label_en": "People of Lot",
        "concept_type": "nation",
        "aliases_ar": ["قوم لوط"],
        "aliases_en": ["People of Lot"],
        "description_ar": "قوم لوط الذين أتوا الفاحشة وأهلكهم الله",
        "description_en": "People of Lot who committed immorality, destroyed by Allah",
        "icon_hint": "users",
        "verses": [(7, 80), (11, 70), (11, 77), (11, 89), (15, 59), (15, 67), (21, 74), (26, 160), (27, 54), (27, 56), (29, 28), (29, 33), (37, 133), (38, 13), (50, 13), (54, 33), (54, 34)]
    },
    {
        "id": "nation_qawm_firaun",
        "slug": "qawm-firaun",
        "label_ar": "آل فرعون",
        "label_en": "People of Pharaoh",
        "concept_type": "nation",
        "aliases_ar": ["آل فرعون", "قوم فرعون"],
        "aliases_en": ["People of Pharaoh", "Aal Firaun"],
        "description_ar": "قوم فرعون الذين استكبروا فأغرقهم الله",
        "description_en": "People of Pharaoh who were arrogant, drowned by Allah",
        "icon_hint": "users",
        "verses": [(2, 49), (3, 11), (7, 103), (7, 130), (7, 141), (8, 52), (8, 54), (10, 75), (10, 83), (11, 97), (14, 6), (20, 24), (23, 46), (27, 12), (28, 3), (28, 32), (28, 38), (29, 39), (40, 28), (40, 46), (44, 17), (50, 13), (51, 38), (54, 41), (66, 11), (69, 9), (73, 15), (79, 17), (85, 18)]
    },
]

# ============================================================================
# THEMES DATA
# ============================================================================
THEMES = [
    {
        "id": "theme_sabr",
        "slug": "sabr",
        "label_ar": "الصبر",
        "label_en": "Patience",
        "concept_type": "theme",
        "aliases_ar": ["الصبر", "الصابرين", "التصبر"],
        "aliases_en": ["Patience", "Perseverance", "Steadfastness"],
        "description_ar": "الصبر على البلاء والمصائب طاعة لله",
        "description_en": "Patience in trials and tribulations as obedience to Allah",
        "icon_hint": "heart",
        "verses": [(2, 45), (2, 153), (2, 155), (2, 177), (3, 17), (3, 125), (3, 146), (3, 186), (3, 200), (7, 128), (7, 137), (8, 46), (8, 65), (8, 66), (11, 11), (11, 49), (11, 115), (13, 22), (13, 24), (14, 5), (14, 12), (16, 42), (16, 96), (16, 110), (16, 126), (16, 127), (18, 28), (19, 65), (20, 130), (21, 85), (23, 111), (25, 20), (28, 80), (29, 58), (29, 59), (30, 60), (31, 17), (31, 31), (32, 24), (33, 35), (37, 102), (38, 44), (39, 10), (40, 55), (40, 77), (41, 35), (42, 43), (46, 35), (47, 31), (50, 39), (52, 48), (68, 48), (70, 5), (73, 10), (76, 12), (90, 17), (103, 3)]
    },
    {
        "id": "theme_tawbah",
        "slug": "tawbah",
        "label_ar": "التوبة",
        "label_en": "Repentance",
        "concept_type": "theme",
        "aliases_ar": ["التوبة", "الإنابة", "الرجوع إلى الله"],
        "aliases_en": ["Repentance", "Returning to Allah", "Tawbah"],
        "description_ar": "الرجوع إلى الله والإقلاع عن الذنوب",
        "description_en": "Returning to Allah and abandoning sins",
        "icon_hint": "heart",
        "verses": [(2, 37), (2, 54), (2, 128), (2, 160), (2, 222), (3, 89), (3, 90), (4, 17), (4, 18), (4, 146), (5, 39), (5, 74), (6, 54), (7, 153), (9, 3), (9, 5), (9, 11), (9, 102), (9, 104), (9, 117), (9, 118), (11, 3), (11, 52), (11, 61), (11, 90), (13, 27), (16, 119), (19, 60), (20, 82), (24, 5), (24, 31), (25, 70), (25, 71), (28, 67), (39, 54), (42, 25), (46, 15), (50, 32), (66, 8)]
    },
    {
        "id": "theme_tawakkul",
        "slug": "tawakkul",
        "label_ar": "التوكل",
        "label_en": "Trust in Allah",
        "concept_type": "theme",
        "aliases_ar": ["التوكل", "التوكل على الله"],
        "aliases_en": ["Trust in Allah", "Reliance on Allah", "Tawakkul"],
        "description_ar": "الاعتماد على الله في كل الأمور",
        "description_en": "Relying on Allah in all matters",
        "icon_hint": "heart",
        "verses": [(3, 122), (3, 159), (3, 160), (4, 81), (5, 11), (5, 23), (7, 89), (8, 49), (8, 61), (9, 51), (9, 129), (10, 71), (10, 84), (10, 85), (11, 56), (11, 88), (11, 123), (12, 67), (13, 30), (14, 11), (14, 12), (16, 42), (16, 99), (25, 58), (26, 217), (27, 79), (29, 59), (33, 3), (33, 48), (39, 38), (42, 10), (42, 36), (58, 10), (60, 4), (64, 13), (65, 3)]
    },
    {
        "id": "theme_shukr",
        "slug": "shukr",
        "label_ar": "الشكر",
        "label_en": "Gratitude",
        "concept_type": "theme",
        "aliases_ar": ["الشكر", "الحمد"],
        "aliases_en": ["Gratitude", "Thankfulness", "Shukr"],
        "description_ar": "شكر الله على نعمه الظاهرة والباطنة",
        "description_en": "Being grateful to Allah for His blessings",
        "icon_hint": "heart",
        "verses": [(2, 52), (2, 56), (2, 152), (2, 172), (2, 185), (3, 123), (3, 144), (3, 145), (4, 147), (5, 6), (5, 89), (7, 10), (7, 17), (7, 58), (7, 144), (7, 189), (8, 26), (10, 22), (10, 60), (12, 38), (14, 5), (14, 7), (14, 37), (16, 14), (16, 78), (16, 114), (16, 121), (21, 80), (22, 36), (23, 78), (25, 62), (27, 15), (27, 19), (27, 40), (28, 73), (29, 17), (30, 46), (31, 12), (31, 14), (31, 31), (34, 13), (34, 15), (34, 19), (35, 12), (36, 35), (36, 73), (39, 7), (39, 66), (40, 61), (45, 12), (46, 15), (54, 35), (56, 70), (67, 23), (76, 3)]
    },
    {
        "id": "theme_iman",
        "slug": "iman",
        "label_ar": "الإيمان",
        "label_en": "Faith",
        "concept_type": "theme",
        "aliases_ar": ["الإيمان", "التصديق"],
        "aliases_en": ["Faith", "Belief", "Iman"],
        "description_ar": "التصديق بالله وملائكته وكتبه ورسله واليوم الآخر",
        "description_en": "Belief in Allah, His angels, books, messengers, and Last Day",
        "icon_hint": "heart",
        "verses": [(2, 3), (2, 4), (2, 62), (2, 165), (2, 177), (2, 285), (3, 16), (3, 52), (3, 84), (3, 110), (3, 173), (4, 59), (4, 136), (4, 162), (5, 1), (5, 111), (7, 75), (7, 87), (8, 2), (8, 4), (9, 23), (9, 71), (10, 9), (10, 84), (16, 97), (18, 30), (23, 1), (24, 62), (29, 52), (32, 15), (33, 22), (33, 35), (35, 7), (40, 12), (42, 52), (47, 2), (48, 4), (48, 26), (49, 7), (49, 14), (49, 15), (57, 8), (57, 19), (58, 22), (59, 10), (60, 1), (64, 8), (85, 8)]
    },
    {
        "id": "theme_dhikr",
        "slug": "dhikr",
        "label_ar": "الذكر",
        "label_en": "Remembrance of Allah",
        "concept_type": "theme",
        "aliases_ar": ["الذكر", "ذكر الله"],
        "aliases_en": ["Remembrance", "Dhikr", "Remembrance of Allah"],
        "description_ar": "ذكر الله بالقلب واللسان والجوارح",
        "description_en": "Remembering Allah with heart, tongue, and actions",
        "icon_hint": "heart",
        "verses": [(2, 152), (2, 198), (2, 200), (2, 203), (3, 41), (3, 191), (4, 103), (5, 4), (5, 91), (6, 91), (7, 205), (8, 45), (13, 28), (18, 24), (20, 14), (20, 42), (22, 28), (22, 34), (22, 36), (24, 37), (29, 45), (33, 21), (33, 35), (33, 41), (33, 42), (39, 22), (39, 23), (43, 36), (57, 16), (62, 10), (63, 9), (73, 8), (76, 25), (87, 15)]
    },
    {
        "id": "theme_taqwa",
        "slug": "taqwa",
        "label_ar": "التقوى",
        "label_en": "God-consciousness",
        "concept_type": "theme",
        "aliases_ar": ["التقوى", "خشية الله", "الخوف من الله"],
        "aliases_en": ["Taqwa", "God-consciousness", "Piety"],
        "description_ar": "الخوف من الله وطاعته واجتناب معاصيه",
        "description_en": "Fearing Allah, obeying Him, and avoiding sins",
        "icon_hint": "heart",
        "verses": [(2, 2), (2, 21), (2, 41), (2, 48), (2, 177), (2, 179), (2, 183), (2, 189), (2, 194), (2, 196), (2, 197), (2, 203), (2, 206), (2, 212), (2, 223), (2, 231), (2, 233), (2, 237), (2, 241), (2, 278), (2, 282), (2, 283), (3, 15), (3, 76), (3, 102), (3, 123), (3, 125), (3, 130), (3, 131), (3, 133), (3, 138), (3, 172), (3, 179), (3, 186), (3, 198), (3, 200), (4, 1), (4, 9), (4, 77), (4, 128), (4, 129), (4, 131), (5, 2), (5, 4), (5, 7), (5, 8), (5, 11), (5, 27), (5, 35), (5, 57), (5, 65), (5, 88), (5, 93), (5, 96), (5, 100), (5, 108), (5, 112), (6, 32), (6, 51), (6, 69), (6, 72), (6, 153), (6, 155), (7, 26), (7, 35), (7, 63), (7, 65), (7, 96), (7, 128), (7, 156), (7, 164), (7, 169), (7, 171), (7, 201), (8, 1), (8, 29), (8, 34), (8, 56), (8, 69), (9, 4), (9, 7), (9, 36), (9, 44), (9, 108), (9, 109), (9, 115), (9, 119), (9, 123), (10, 6), (10, 31), (10, 63), (11, 49), (11, 78), (12, 57), (12, 90), (12, 109), (13, 35), (14, 16), (14, 26), (15, 45), (16, 30), (16, 31), (16, 52), (16, 128), (17, 59), (19, 13), (19, 18), (19, 63), (19, 72), (19, 85), (19, 97), (20, 113), (20, 132), (21, 48), (21, 49), (22, 1), (22, 32), (22, 37), (23, 23), (23, 32), (23, 49), (23, 52), (23, 87), (24, 52), (25, 15), (25, 74), (26, 11), (26, 90), (26, 108), (26, 110), (26, 124), (26, 126), (26, 131), (26, 132), (26, 142), (26, 144), (26, 150), (26, 161), (26, 163), (26, 177), (26, 179), (26, 184), (27, 53), (28, 83), (29, 16), (31, 33), (32, 16), (33, 1), (33, 32), (33, 37), (33, 55), (33, 70), (35, 18), (35, 28), (36, 11), (37, 124), (38, 28), (39, 10), (39, 13), (39, 16), (39, 20), (39, 24), (39, 28), (39, 33), (39, 57), (39, 61), (39, 73), (40, 9), (41, 18), (43, 35), (43, 63), (43, 67), (44, 51), (45, 19), (47, 15), (47, 17), (47, 36), (48, 5), (48, 26), (49, 1), (49, 3), (49, 10), (49, 12), (50, 31), (51, 15), (52, 17), (53, 32), (54, 15), (54, 54), (57, 21), (57, 28), (58, 9), (59, 7), (59, 18), (60, 11), (64, 16), (65, 1), (65, 2), (65, 4), (65, 5), (65, 10), (66, 6), (68, 34), (69, 48), (71, 3), (72, 13), (73, 17), (74, 56), (76, 10), (76, 11), (77, 41), (78, 31), (79, 40), (91, 8), (92, 5), (96, 12), (98, 8)]
    },
    {
        "id": "theme_adl",
        "slug": "adl",
        "label_ar": "العدل",
        "label_en": "Justice",
        "concept_type": "theme",
        "aliases_ar": ["العدل", "القسط", "الإنصاف"],
        "aliases_en": ["Justice", "Fairness", "Equity"],
        "description_ar": "العدل في الحكم بين الناس وإعطاء كل ذي حق حقه",
        "description_en": "Being just in judgments and giving everyone their rights",
        "icon_hint": "heart",
        "verses": [(4, 58), (4, 135), (5, 8), (5, 42), (6, 152), (16, 90), (38, 26), (42, 15), (49, 9), (57, 25), (60, 8)]
    },
    {
        "id": "theme_ihsan",
        "slug": "ihsan",
        "label_ar": "الإحسان",
        "label_en": "Excellence",
        "concept_type": "theme",
        "aliases_ar": ["الإحسان", "حسن العبادة"],
        "aliases_en": ["Ihsan", "Excellence", "Perfection"],
        "description_ar": "أن تعبد الله كأنك تراه، فإن لم تكن تراه فإنه يراك",
        "description_en": "To worship Allah as if you see Him",
        "icon_hint": "heart",
        "verses": [(2, 112), (2, 195), (2, 236), (3, 134), (3, 148), (4, 36), (4, 62), (4, 125), (4, 128), (5, 13), (5, 85), (5, 93), (6, 84), (6, 154), (7, 56), (9, 91), (9, 100), (9, 120), (11, 115), (12, 22), (12, 36), (12, 56), (12, 78), (12, 90), (14, 12), (16, 30), (16, 90), (16, 128), (17, 7), (18, 30), (22, 37), (28, 14), (28, 77), (29, 69), (31, 2), (31, 3), (31, 22), (32, 7), (33, 29), (37, 80), (37, 105), (37, 110), (37, 121), (37, 131), (39, 10), (39, 34), (39, 58), (46, 12), (51, 16), (53, 31), (55, 60), (77, 44)]
    },
]


async def seed_concepts():
    """Seed concepts into the database."""
    print("\n" + "="*60)
    print("Seeding Quranic Concepts")
    print("="*60 + "\n")

    async with get_async_session_context() as session:
        all_data = PROPHETS + PLACES + NATIONS + THEMES

        inserted = 0
        skipped = 0

        for concept in all_data:
            # Check if exists
            result = await session.execute(
                text("SELECT id FROM concepts WHERE id = :id"),
                {"id": concept["id"]}
            )
            if result.fetchone():
                skipped += 1
                continue

            # Insert concept
            await session.execute(
                text("""
                INSERT INTO concepts (id, slug, label_ar, label_en, concept_type,
                    aliases_ar, aliases_en, description_ar, description_en,
                    icon_hint, is_curated, source, created_at, updated_at)
                VALUES (:id, :slug, :label_ar, :label_en, :concept_type,
                    :aliases_ar, :aliases_en, :description_ar, :description_en,
                    :icon_hint, true, 'quran_seed', NOW(), NOW())
                """),
                {
                    "id": concept["id"],
                    "slug": concept["slug"],
                    "label_ar": concept["label_ar"],
                    "label_en": concept["label_en"],
                    "concept_type": concept["concept_type"],
                    "aliases_ar": concept.get("aliases_ar", []),
                    "aliases_en": concept.get("aliases_en", []),
                    "description_ar": concept.get("description_ar", ""),
                    "description_en": concept.get("description_en", ""),
                    "icon_hint": concept.get("icon_hint", ""),
                }
            )

            # Insert verse occurrences
            for sura_no, aya_no in concept.get("verses", []):
                await session.execute(
                    text("""
                    INSERT INTO occurrences (concept_id, ref_type, sura_no, ayah_start, ayah_end,
                        is_verified, created_at)
                    VALUES (:concept_id, 'ayah', :sura_no, :ayah_start, :ayah_end, true, NOW())
                    """),
                    {
                        "concept_id": concept["id"],
                        "sura_no": sura_no,
                        "ayah_start": aya_no,
                        "ayah_end": aya_no,
                    }
                )

            inserted += 1
            print(f"  ✓ {concept['label_en']} ({concept['concept_type']}) - {len(concept.get('verses', []))} verses")

        await session.commit()

        # Count totals
        result = await session.execute(text("SELECT COUNT(*) FROM concepts"))
        total_concepts = result.scalar()

        result = await session.execute(text("SELECT COUNT(*) FROM occurrences"))
        total_occurrences = result.scalar()

        print("\n" + "="*60)
        print(f"Results: {inserted} inserted, {skipped} skipped")
        print(f"Total concepts: {total_concepts}")
        print(f"Total verse occurrences: {total_occurrences}")
        print("="*60 + "\n")

        return inserted > 0 or total_concepts > 0


if __name__ == "__main__":
    success = asyncio.run(seed_concepts())
    exit(0 if success else 1)
