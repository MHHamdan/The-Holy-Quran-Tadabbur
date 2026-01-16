#!/usr/bin/env python3
"""
Add Missing Quranic Stories to Story Atlas.

This script adds stories that are mentioned in the Quran but not yet in the database.

Stories to add:
1. Prophet Ilyas (Elijah) - 6:85, 37:123-132
2. Prophet Al-Yasa (Elisha) - 6:86, 38:48
3. Prophet Dhul-Kifl - 21:85, 38:48
4. Battle of Ahzab (Khandaq/Trench) - Surah 33:9-27
5. People of the Town (Ya-Sin) - 36:13-29
6. People of the Rass - 25:38, 50:12
7. People of Tubba - 44:37, 50:14
8. The Blind Man ('Abasa) - 80:1-10
9. People of the Trench (Al-Buruj) - already as cluster_ukhdud
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"
)

NEW_STORY_CLUSTERS = [
    # =========================================================================
    # PROPHET ILYAS (ELIJAH) - Surah 37:123-132, 6:85
    # =========================================================================
    {
        "id": "cluster_ilyas",
        "title_ar": "قصة إلياس",
        "title_en": "Prophet Ilyas (Elijah)",
        "short_title_ar": "إلياس",
        "short_title_en": "Ilyas",
        "category": "prophet",
        "main_persons": ["Ilyas"],
        "groups": ["Bani Israil"],
        "tags": ["prophet", "monotheism", "baal_worship", "rejection"],
        "places": [],
        "era": "bani_israil",
        "era_basis": "inferred",
        "time_description_en": "Era of Bani Israil, after Sulayman",
        "ayah_spans": [
            {"sura": 37, "start": 123, "end": 132},
            {"sura": 6, "start": 85, "end": 85}
        ],
        "primary_sura": 37,
        "summary_ar": "نبي من أنبياء بني إسرائيل أُرسل ليدعو قومه لترك عبادة بعل والعودة لعبادة الله",
        "summary_en": "A prophet sent to call his people to abandon Baal worship and return to worshipping Allah alone.",
        "lessons_ar": ["التوحيد أساس الدين", "الصبر على الدعوة", "الأنبياء قدوة"],
        "lessons_en": ["Monotheism is the foundation of religion", "Patience in calling to truth", "Prophets as role models"],
    },
    # =========================================================================
    # PROPHET AL-YASA (ELISHA) - 6:86, 38:48
    # =========================================================================
    {
        "id": "cluster_alyasa",
        "title_ar": "قصة اليسع",
        "title_en": "Prophet Al-Yasa (Elisha)",
        "short_title_ar": "اليسع",
        "short_title_en": "Al-Yasa",
        "category": "prophet",
        "main_persons": ["Al-Yasa"],
        "groups": ["Bani Israil"],
        "tags": ["prophet", "righteousness", "chosen"],
        "places": [],
        "era": "bani_israil",
        "era_basis": "inferred",
        "time_description_en": "Era of Bani Israil, successor to Ilyas",
        "ayah_spans": [
            {"sura": 6, "start": 86, "end": 86},
            {"sura": 38, "start": 48, "end": 48}
        ],
        "primary_sura": 38,
        "summary_ar": "نبي من الأخيار، ذُكر ضمن أفضل الأنبياء والمختارين من عباد الله",
        "summary_en": "A prophet mentioned among the best and chosen servants of Allah.",
        "lessons_ar": ["الاصطفاء الإلهي", "الأنبياء من خير الخلق"],
        "lessons_en": ["Divine selection", "Prophets are among the best of creation"],
    },
    # =========================================================================
    # PROPHET DHUL-KIFL - 21:85, 38:48
    # =========================================================================
    {
        "id": "cluster_dhulkifl",
        "title_ar": "ذو الكفل",
        "title_en": "Dhul-Kifl",
        "short_title_ar": "ذو الكفل",
        "short_title_en": "Dhul-Kifl",
        "category": "prophet",
        "main_persons": ["Dhul-Kifl"],
        "groups": [],
        "tags": ["prophet", "patience", "righteousness", "chosen"],
        "places": [],
        "era": "bani_israil",
        "era_basis": "inferred",
        "time_description_en": "Identity debated - possibly Ezekiel or Elijah's successor",
        "ayah_spans": [
            {"sura": 21, "start": 85, "end": 86},
            {"sura": 38, "start": 48, "end": 48}
        ],
        "primary_sura": 21,
        "summary_ar": "ذُكر مع إسماعيل وإدريس ووُصف بالصبر، اختلف العلماء في هويته",
        "summary_en": "Mentioned with Ismail and Idris, described as patient. Scholars differ on his identity.",
        "lessons_ar": ["الصبر صفة الأنبياء", "العلم عند الله"],
        "lessons_en": ["Patience is a quality of prophets", "Knowledge is with Allah"],
    },
    # =========================================================================
    # BATTLE OF AHZAB (KHANDAQ/TRENCH) - Surah 33
    # =========================================================================
    {
        "id": "cluster_ahzab",
        "title_ar": "غزوة الأحزاب (الخندق)",
        "title_en": "Battle of Ahzab (The Trench)",
        "short_title_ar": "الأحزاب",
        "short_title_en": "Ahzab",
        "category": "prophetic_sira",
        "main_persons": ["Muhammad", "Companions"],
        "groups": ["Muslims", "Quraysh", "Jews of Banu Qurayza", "Confederates"],
        "tags": ["prophetic", "battle", "siege", "hypocrites", "divine_help", "wind"],
        "places": [{"name": "Madinah", "name_ar": "المدينة", "basis": "explicit"}],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "5 AH - Confederate armies besieged Madinah",
        "ayah_spans": [{"sura": 33, "start": 9, "end": 27}],
        "primary_sura": 33,
        "summary_ar": "حصار الأحزاب للمدينة وحفر الخندق، ونصر الله بالريح والملائكة",
        "summary_en": "The confederate armies besieged Madinah, Muslims dug a trench, and Allah sent wind and angels for victory.",
        "lessons_ar": ["التوكل على الله", "الصبر في الشدائد", "فضح المنافقين"],
        "lessons_en": ["Reliance on Allah", "Patience in hardship", "Exposing hypocrites"],
    },
    # =========================================================================
    # PEOPLE OF THE TOWN (YA-SIN) - 36:13-29
    # =========================================================================
    {
        "id": "cluster_yasin_town",
        "title_ar": "أصحاب القرية",
        "title_en": "People of the Town (Ya-Sin)",
        "short_title_ar": "أصحاب القرية",
        "short_title_en": "Town Dwellers",
        "category": "historical",
        "main_persons": ["Three Messengers", "Believing Man"],
        "groups": ["Town Dwellers"],
        "tags": ["messengers", "rejection", "believer", "martyrdom", "paradise"],
        "places": [{"name": "Antioch (debated)", "name_ar": "أنطاكية (محتمل)", "basis": "inferred"}],
        "era": "unknown",
        "era_basis": "unknown",
        "time_description_en": "Era unknown - possibly early Christian period",
        "ayah_spans": [{"sura": 36, "start": 13, "end": 29}],
        "primary_sura": 36,
        "summary_ar": "قرية أرسل إليها رسولان ثم ثالث، وجاء مؤمن من أقصى المدينة ناصحاً قومه فقُتل ودخل الجنة",
        "summary_en": "A town sent two messengers, then a third. A believing man came running from the city's edge to support them, was martyred, and entered Paradise.",
        "lessons_ar": ["الإيمان شجاعة", "الشهادة في سبيل الله", "عاقبة التكذيب"],
        "lessons_en": ["Faith requires courage", "Martyrdom for Allah's sake", "Consequences of denial"],
    },
    # =========================================================================
    # PEOPLE OF THE RASS - 25:38, 50:12
    # =========================================================================
    {
        "id": "cluster_rass",
        "title_ar": "أصحاب الرس",
        "title_en": "People of the Rass",
        "short_title_ar": "أصحاب الرس",
        "short_title_en": "Rass",
        "category": "historical",
        "main_persons": [],
        "groups": ["People of the Rass"],
        "tags": ["destruction", "denial", "unknown_identity"],
        "places": [{"name": "The Rass (Well)", "name_ar": "الرس", "basis": "explicit"}],
        "era": "unknown",
        "era_basis": "unknown",
        "time_description_en": "Era and identity unknown - mentioned among destroyed nations",
        "ayah_spans": [
            {"sura": 25, "start": 38, "end": 39},
            {"sura": 50, "start": 12, "end": 14}
        ],
        "primary_sura": 25,
        "summary_ar": "قوم مذكورون مع عاد وثمود، اختلف المفسرون في هويتهم، أُهلكوا بسبب تكذيبهم",
        "summary_en": "A people mentioned with Aad and Thamud, their identity debated by scholars, destroyed for their denial.",
        "lessons_ar": ["عاقبة التكذيب", "الأمم السابقة عبرة"],
        "lessons_en": ["Consequence of denial", "Previous nations as lessons"],
    },
    # =========================================================================
    # PEOPLE OF TUBBA - 44:37, 50:14
    # =========================================================================
    {
        "id": "cluster_tubba",
        "title_ar": "قوم تُبَّع",
        "title_en": "People of Tubba",
        "short_title_ar": "قوم تُبَّع",
        "short_title_en": "Tubba",
        "category": "historical",
        "main_persons": ["Tubba"],
        "groups": ["People of Tubba", "Himyarites"],
        "tags": ["yemen", "destruction", "denial", "kings"],
        "places": [{"name": "Yemen", "name_ar": "اليمن", "basis": "inferred"}],
        "era": "pre_islamic",
        "era_basis": "inferred",
        "time_description_en": "Pre-Islamic Yemen - Tubba' was a title for Himyarite kings",
        "ayah_spans": [
            {"sura": 44, "start": 37, "end": 37},
            {"sura": 50, "start": 14, "end": 14}
        ],
        "primary_sura": 44,
        "summary_ar": "قوم ملوك اليمن (تُبَّع)، ذُكروا ضمن الأمم المُهلَكة",
        "summary_en": "People of the Yemeni kings (Tubba'), mentioned among destroyed nations.",
        "lessons_ar": ["الملك لا ينفع مع الكفر", "العبرة من الأمم السابقة"],
        "lessons_en": ["Kingship is useless with disbelief", "Lessons from previous nations"],
    },
    # =========================================================================
    # THE BLIND MAN ('ABASA) - 80:1-10
    # =========================================================================
    {
        "id": "cluster_abasa",
        "title_ar": "عبس وتولى",
        "title_en": "The Blind Man ('Abasa)",
        "short_title_ar": "الأعمى",
        "short_title_en": "'Abasa",
        "category": "prophetic_sira",
        "main_persons": ["Muhammad", "Ibn Umm Maktum"],
        "groups": ["Quraysh Leaders"],
        "tags": ["prophetic", "guidance", "priorities", "equality", "lesson"],
        "places": [{"name": "Makkah", "name_ar": "مكة", "basis": "inferred"}],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "Meccan period - when Ibn Umm Maktum came seeking guidance",
        "ayah_spans": [{"sura": 80, "start": 1, "end": 10}],
        "primary_sura": 80,
        "summary_ar": "عتاب للنبي ﷺ حين أعرض عن الأعمى عبد الله بن أم مكتوم وهو مشغول بدعوة سادة قريش",
        "summary_en": "Divine correction to the Prophet ﷺ when he turned away from the blind man Ibn Umm Maktum while busy calling Quraysh leaders.",
        "lessons_ar": ["المساواة في الدعوة", "من طلب الهداية أولى", "التربية النبوية"],
        "lessons_en": ["Equality in calling to Islam", "Those seeking guidance have priority", "Prophetic education"],
    },
    # =========================================================================
    # BANI NADIR EXPULSION - Surah 59
    # =========================================================================
    {
        "id": "cluster_bani_nadir",
        "title_ar": "إجلاء بني النضير",
        "title_en": "Expulsion of Bani Nadir",
        "short_title_ar": "بني النضير",
        "short_title_en": "Bani Nadir",
        "category": "prophetic_sira",
        "main_persons": ["Muhammad"],
        "groups": ["Muslims", "Bani Nadir Jews", "Hypocrites"],
        "tags": ["prophetic", "expulsion", "treachery", "divine_help"],
        "places": [{"name": "Madinah", "name_ar": "المدينة", "basis": "explicit"}],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "4 AH - After Bani Nadir's treachery",
        "ayah_spans": [{"sura": 59, "start": 2, "end": 17}],
        "primary_sura": 59,
        "summary_ar": "إجلاء يهود بني النضير من المدينة بعد خيانتهم للعهد ومحاولتهم قتل النبي ﷺ",
        "summary_en": "Expulsion of Bani Nadir Jews from Madinah after they broke their treaty and plotted to kill the Prophet ﷺ.",
        "lessons_ar": ["عاقبة الخيانة", "نصر الله للمؤمنين", "فضح المنافقين"],
        "lessons_en": ["Consequence of treachery", "Allah's victory for believers", "Exposing hypocrites"],
    },
    # =========================================================================
    # PEOPLE OF AIYKA - 15:78, 26:176-191
    # =========================================================================
    {
        "id": "cluster_aiyka",
        "title_ar": "أصحاب الأيكة",
        "title_en": "People of Aiyka",
        "short_title_ar": "أصحاب الأيكة",
        "short_title_en": "Aiyka",
        "category": "historical",
        "main_persons": ["Shuayb"],
        "groups": ["People of Aiyka"],
        "tags": ["prophet", "rejection", "destruction", "shadow_day"],
        "places": [{"name": "Aiyka (Forest)", "name_ar": "الأيكة", "basis": "explicit"}],
        "era": "pre_islamic",
        "era_basis": "inferred",
        "time_description_en": "Contemporary with or near Shu'ayb's time",
        "ayah_spans": [
            {"sura": 15, "start": 78, "end": 79},
            {"sura": 26, "start": 176, "end": 191},
            {"sura": 38, "start": 13, "end": 13},
            {"sura": 50, "start": 14, "end": 14}
        ],
        "primary_sura": 26,
        "summary_ar": "قوم عاشوا في الأيكة (الغابة)، كذبوا الرسل فأهلكهم الله بعذاب يوم الظُلة",
        "summary_en": "People who lived in Aiyka (the forest), they denied the messengers and were destroyed by the punishment of the Day of Shadow.",
        "lessons_ar": ["عاقبة التكذيب", "أنواع العذاب الإلهي"],
        "lessons_en": ["Consequence of denial", "Types of divine punishment"],
    },
]

NEW_STORY_EVENTS = {
    # =========================================================================
    # ILYAS EVENTS
    # =========================================================================
    "cluster_ilyas": [
        {
            "id": "cluster_ilyas:mission",
            "title_ar": "بعثة إلياس",
            "title_en": "Mission of Ilyas",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 37,
            "aya_start": 123,
            "aya_end": 124,
            "is_entry_point": True,
            "summary_ar": "إرسال إلياس رسولاً إلى قومه",
            "summary_en": "Ilyas was sent as a messenger to his people.",
            "semantic_tags": ["prophet", "mission", "sending"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "37:123",
                    "snippet": "Ilyas was one of the prophets of Bani Israil sent to call them back to the worship of Allah."
                }
            ],
        },
        {
            "id": "cluster_ilyas:baal_worship",
            "title_ar": "دعوة ترك عبادة بعل",
            "title_en": "Call to Abandon Baal",
            "narrative_role": "confrontation",
            "chronological_index": 2,
            "sura_no": 37,
            "aya_start": 125,
            "aya_end": 126,
            "is_entry_point": False,
            "summary_ar": "دعا قومه لترك عبادة بعل والعودة لعبادة الله أحسن الخالقين",
            "summary_en": "He called his people to abandon Baal worship and return to Allah, the Best of creators.",
            "semantic_tags": ["baal", "idols", "monotheism", "dawah"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "37:125-126",
                    "snippet": "Do you call upon Baal and leave the Best of creators? Allah is your Lord and the Lord of your forefathers."
                }
            ],
        },
        {
            "id": "cluster_ilyas:rejection",
            "title_ar": "تكذيب قومه له",
            "title_en": "Rejection by His People",
            "narrative_role": "rejection",
            "chronological_index": 3,
            "sura_no": 37,
            "aya_start": 127,
            "aya_end": 127,
            "is_entry_point": False,
            "summary_ar": "كذبه قومه وسيُحضرون للحساب إلا عباد الله المخلصين",
            "summary_en": "His people denied him and will be brought to account, except the sincere servants of Allah.",
            "semantic_tags": ["rejection", "denial", "judgment"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "37:127",
                    "snippet": "They denied him, so they will certainly be brought for punishment, except the chosen servants of Allah."
                }
            ],
        },
        {
            "id": "cluster_ilyas:honor",
            "title_ar": "تكريم إلياس",
            "title_en": "Honor of Ilyas",
            "narrative_role": "outcome",
            "chronological_index": 4,
            "sura_no": 37,
            "aya_start": 129,
            "aya_end": 132,
            "is_entry_point": False,
            "summary_ar": "ترك الله له ثناءً حسناً في الآخرين، وسلام عليه في العالمين",
            "summary_en": "Allah left for him honorable mention among later generations. Peace be upon Ilyas.",
            "semantic_tags": ["honor", "peace", "legacy"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "37:129-130",
                    "snippet": "Peace be upon Ilyas. Indeed, We thus reward the doers of good."
                }
            ],
        },
    ],
    # =========================================================================
    # AL-YASA EVENTS
    # =========================================================================
    "cluster_alyasa": [
        {
            "id": "cluster_alyasa:mention_righteous",
            "title_ar": "ذكره مع الأنبياء",
            "title_en": "Mentioned Among Prophets",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 6,
            "aya_start": 86,
            "aya_end": 86,
            "is_entry_point": True,
            "summary_ar": "ذُكر اليسع مع إسماعيل ويونس ولوط، كلهم فُضلوا على العالمين",
            "summary_en": "Al-Yasa was mentioned with Ismail, Yunus, and Lut - all favored above the worlds.",
            "semantic_tags": ["prophet", "honor", "chosen"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "6:86",
                    "snippet": "And Ismail and Alyasa and Yunus and Lut - all We preferred over the worlds."
                }
            ],
        },
        {
            "id": "cluster_alyasa:among_chosen",
            "title_ar": "من الأخيار",
            "title_en": "Among the Chosen",
            "narrative_role": "reflection",
            "chronological_index": 2,
            "sura_no": 38,
            "aya_start": 48,
            "aya_end": 48,
            "is_entry_point": False,
            "summary_ar": "ذُكر مع إسماعيل وذي الكفل، وكلهم من الأخيار",
            "summary_en": "Mentioned with Ismail and Dhul-Kifl - all of them among the outstanding.",
            "semantic_tags": ["prophet", "chosen", "outstanding"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "38:48",
                    "snippet": "And remember Ismail and Alyasa and Dhul-Kifl, and all are among the outstanding."
                }
            ],
        },
    ],
    # =========================================================================
    # DHUL-KIFL EVENTS
    # =========================================================================
    "cluster_dhulkifl": [
        {
            "id": "cluster_dhulkifl:patience",
            "title_ar": "وصفه بالصبر",
            "title_en": "Described as Patient",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 21,
            "aya_start": 85,
            "aya_end": 86,
            "is_entry_point": True,
            "summary_ar": "ذُكر مع إسماعيل وإدريس، كلهم من الصابرين، وأدخلهم الله في رحمته",
            "summary_en": "Mentioned with Ismail and Idris - all were patient. Allah admitted them into His mercy.",
            "semantic_tags": ["patience", "mercy", "prophet"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "21:85-86",
                    "snippet": "And Ismail and Idris and Dhul-Kifl - all were of the patient. And We admitted them into Our mercy."
                }
            ],
        },
        {
            "id": "cluster_dhulkifl:among_chosen",
            "title_ar": "من الأخيار",
            "title_en": "Among the Outstanding",
            "narrative_role": "reflection",
            "chronological_index": 2,
            "sura_no": 38,
            "aya_start": 48,
            "aya_end": 48,
            "is_entry_point": False,
            "summary_ar": "ذُكر ضمن الأخيار مع إسماعيل واليسع",
            "summary_en": "Mentioned among the outstanding with Ismail and Al-Yasa.",
            "semantic_tags": ["chosen", "outstanding", "honor"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "38:48",
                    "snippet": "All are among the outstanding - meaning they were from the best of people in their time."
                }
            ],
        },
    ],
    # =========================================================================
    # BATTLE OF AHZAB EVENTS
    # =========================================================================
    "cluster_ahzab": [
        {
            "id": "cluster_ahzab:armies_come",
            "title_ar": "قدوم الأحزاب",
            "title_en": "Confederates Arrive",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 33,
            "aya_start": 9,
            "aya_end": 9,
            "is_entry_point": True,
            "summary_ar": "جاءت جنود الأحزاب من قريش وغطفان ويهود لحصار المدينة",
            "summary_en": "Confederate armies from Quraysh, Ghatafan, and Jews came to besiege Madinah.",
            "semantic_tags": ["siege", "armies", "confederates"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "33:9",
                    "snippet": "O you who believe, remember Allah's favor upon you when armies came to you."
                }
            ],
        },
        {
            "id": "cluster_ahzab:wind_angels",
            "title_ar": "الريح والملائكة",
            "title_en": "Wind and Angels Sent",
            "narrative_role": "divine_intervention",
            "chronological_index": 2,
            "sura_no": 33,
            "aya_start": 9,
            "aya_end": 9,
            "is_entry_point": False,
            "summary_ar": "أرسل الله ريحاً وجنوداً من الملائكة لم يرها المسلمون",
            "summary_en": "Allah sent a wind and armies (of angels) they did not see.",
            "semantic_tags": ["wind", "angels", "divine_help"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "33:9",
                    "snippet": "We sent upon them a wind and armies you did not see."
                }
            ],
        },
        {
            "id": "cluster_ahzab:hearts_throats",
            "title_ar": "بلوغ القلوب الحناجر",
            "title_en": "Hearts Reaching Throats",
            "narrative_role": "trial",
            "chronological_index": 3,
            "sura_no": 33,
            "aya_start": 10,
            "aya_end": 11,
            "is_entry_point": False,
            "summary_ar": "بلغت القلوب الحناجر من شدة الخوف، وزُلزل المسلمون زلزالاً شديداً",
            "summary_en": "Hearts reached throats from fear, and believers were shaken with a severe shaking.",
            "semantic_tags": ["fear", "trial", "shaking"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "33:10-11",
                    "snippet": "When eyes shifted and hearts reached throats, and you assumed about Allah assumptions."
                }
            ],
        },
        {
            "id": "cluster_ahzab:hypocrites_exposed",
            "title_ar": "انكشاف المنافقين",
            "title_en": "Hypocrites Exposed",
            "narrative_role": "confrontation",
            "chronological_index": 4,
            "sura_no": 33,
            "aya_start": 12,
            "aya_end": 13,
            "is_entry_point": False,
            "summary_ar": "قال المنافقون: ما وعدنا الله ورسوله إلا غروراً، وطلبوا الإذن بالفرار",
            "summary_en": "Hypocrites said: Allah and His Messenger promised us nothing but delusion, and sought permission to flee.",
            "semantic_tags": ["hypocrites", "doubt", "cowardice"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "33:12-13",
                    "snippet": "The hypocrites said: Allah and His Messenger did not promise us except delusion."
                }
            ],
        },
        {
            "id": "cluster_ahzab:believers_firm",
            "title_ar": "ثبات المؤمنين",
            "title_en": "Believers Stand Firm",
            "narrative_role": "steadfastness",
            "chronological_index": 5,
            "sura_no": 33,
            "aya_start": 22,
            "aya_end": 23,
            "is_entry_point": False,
            "summary_ar": "المؤمنون قالوا: هذا ما وعدنا الله ورسوله، وما زادهم إلا إيماناً وتسليماً",
            "summary_en": "Believers said: This is what Allah and His Messenger promised us. It only increased them in faith and submission.",
            "semantic_tags": ["faith", "steadfastness", "trust"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "33:22",
                    "snippet": "And when the believers saw the confederates, they said: This is what Allah and His Messenger promised us."
                }
            ],
        },
        {
            "id": "cluster_ahzab:enemy_retreat",
            "title_ar": "رد الأعداء خائبين",
            "title_en": "Enemies Retreat",
            "narrative_role": "outcome",
            "chronological_index": 6,
            "sura_no": 33,
            "aya_start": 25,
            "aya_end": 25,
            "is_entry_point": False,
            "summary_ar": "رد الله الذين كفروا بغيظهم لم ينالوا خيراً، وكفى الله المؤمنين القتال",
            "summary_en": "Allah turned back the disbelievers in their rage, having gained nothing. Allah sufficed the believers in battle.",
            "semantic_tags": ["victory", "retreat", "divine_help"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "33:25",
                    "snippet": "And Allah repelled those who disbelieved, in their rage, not having obtained any good."
                }
            ],
        },
        {
            "id": "cluster_ahzab:banu_qurayza",
            "title_ar": "جزاء بني قريظة",
            "title_en": "Banu Qurayza's Fate",
            "narrative_role": "outcome",
            "chronological_index": 7,
            "sura_no": 33,
            "aya_start": 26,
            "aya_end": 27,
            "is_entry_point": False,
            "summary_ar": "أنزل الله الذين ظاهروهم من أهل الكتاب من صياصيهم وقذف في قلوبهم الرعب",
            "summary_en": "Allah brought down those who supported them from the People of the Book from their fortresses and cast terror in their hearts.",
            "semantic_tags": ["judgment", "treachery", "consequence"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "33:26-27",
                    "snippet": "He brought down those who supported them among the People of the Book from their fortresses."
                }
            ],
        },
    ],
    # =========================================================================
    # PEOPLE OF THE TOWN (YA-SIN) EVENTS
    # =========================================================================
    "cluster_yasin_town": [
        {
            "id": "cluster_yasin_town:two_messengers",
            "title_ar": "إرسال رسولين",
            "title_en": "Two Messengers Sent",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 36,
            "aya_start": 13,
            "aya_end": 14,
            "is_entry_point": True,
            "summary_ar": "أرسل الله إلى القرية رسولين اثنين فكذبوهما",
            "summary_en": "Allah sent two messengers to the town, but they denied them.",
            "semantic_tags": ["messengers", "denial", "town"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "36:13-14",
                    "snippet": "And set forth to them an example of the companions of the city, when the messengers came to it."
                }
            ],
        },
        {
            "id": "cluster_yasin_town:third_messenger",
            "title_ar": "تعزيز بثالث",
            "title_en": "Third Messenger Sent",
            "narrative_role": "escalation",
            "chronological_index": 2,
            "sura_no": 36,
            "aya_start": 14,
            "aya_end": 14,
            "is_entry_point": False,
            "summary_ar": "عززهم الله بثالث فقالوا إنا إليكم مرسلون",
            "summary_en": "Allah reinforced them with a third, and they said: Indeed, we are messengers to you.",
            "semantic_tags": ["reinforcement", "mission", "messengers"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "36:14",
                    "snippet": "When We sent to them two but they denied them, so We strengthened them with a third."
                }
            ],
        },
        {
            "id": "cluster_yasin_town:rejection",
            "title_ar": "رفض أهل القرية",
            "title_en": "Town's Rejection",
            "narrative_role": "rejection",
            "chronological_index": 3,
            "sura_no": 36,
            "aya_start": 15,
            "aya_end": 19,
            "is_entry_point": False,
            "summary_ar": "قال أهل القرية: ما أنتم إلا بشر مثلنا، وتوعدوهم بالرجم",
            "summary_en": "Town dwellers said: You are but humans like us, and threatened to stone them.",
            "semantic_tags": ["rejection", "threat", "stoning"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "36:15-18",
                    "snippet": "They said: You are not but human beings like us, and the Most Merciful has not revealed a thing."
                }
            ],
        },
        {
            "id": "cluster_yasin_town:believing_man",
            "title_ar": "الرجل المؤمن",
            "title_en": "The Believing Man",
            "narrative_role": "heroism",
            "chronological_index": 4,
            "sura_no": 36,
            "aya_start": 20,
            "aya_end": 25,
            "is_entry_point": False,
            "summary_ar": "جاء رجل من أقصى المدينة يسعى، دعا قومه لاتباع المرسلين",
            "summary_en": "A man came running from the farthest end of the city, calling his people to follow the messengers.",
            "semantic_tags": ["believer", "courage", "dawah"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "36:20",
                    "snippet": "And there came from the farthest end of the city a man running. He said: O my people, follow the messengers."
                }
            ],
        },
        {
            "id": "cluster_yasin_town:martyrdom_paradise",
            "title_ar": "استشهاده ودخوله الجنة",
            "title_en": "Martyrdom and Paradise",
            "narrative_role": "outcome",
            "chronological_index": 5,
            "sura_no": 36,
            "aya_start": 26,
            "aya_end": 27,
            "is_entry_point": False,
            "summary_ar": "قُتل الرجل المؤمن ودخل الجنة، قال: يا ليت قومي يعلمون",
            "summary_en": "The believing man was killed and entered Paradise. He wished his people knew of his honor.",
            "semantic_tags": ["martyrdom", "paradise", "wish"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "36:26-27",
                    "snippet": "It was said: Enter Paradise. He said: I wish my people could know of how my Lord has forgiven me."
                }
            ],
        },
        {
            "id": "cluster_yasin_town:destruction",
            "title_ar": "هلاك القرية",
            "title_en": "Town's Destruction",
            "narrative_role": "outcome",
            "chronological_index": 6,
            "sura_no": 36,
            "aya_start": 28,
            "aya_end": 29,
            "is_entry_point": False,
            "summary_ar": "أُهلك أهل القرية بصيحة واحدة فإذا هم خامدون",
            "summary_en": "The town was destroyed with a single blast - they became extinguished.",
            "semantic_tags": ["destruction", "blast", "punishment"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "36:29",
                    "snippet": "It was not but one shout, and immediately they were extinguished."
                }
            ],
        },
    ],
    # =========================================================================
    # PEOPLE OF THE RASS EVENTS
    # =========================================================================
    "cluster_rass": [
        {
            "id": "cluster_rass:mention_aad_thamud",
            "title_ar": "ذكرهم مع عاد وثمود",
            "title_en": "Mentioned with Aad and Thamud",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 25,
            "aya_start": 38,
            "aya_end": 39,
            "is_entry_point": True,
            "summary_ar": "ذُكر أصحاب الرس مع عاد وثمود وقروناً بين ذلك كثيراً",
            "summary_en": "People of the Rass mentioned with Aad and Thamud, and many generations between them.",
            "semantic_tags": ["destruction", "nations", "warning"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "25:38",
                    "snippet": "And Aad and Thamud and the people of the Rass and many generations between them."
                }
            ],
        },
        {
            "id": "cluster_rass:examples_warnings",
            "title_ar": "ضرب الأمثال",
            "title_en": "Examples and Warnings",
            "narrative_role": "reflection",
            "chronological_index": 2,
            "sura_no": 25,
            "aya_start": 39,
            "aya_end": 39,
            "is_entry_point": False,
            "summary_ar": "ضرب الله لهم الأمثال وتبَّر كلاً تتبيراً",
            "summary_en": "Allah presented examples for all of them, and destroyed each completely.",
            "semantic_tags": ["examples", "destruction", "warning"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "25:39",
                    "snippet": "And for each We presented examples, and each We destroyed with destruction."
                }
            ],
        },
        {
            "id": "cluster_rass:second_mention",
            "title_ar": "الذكر الثاني",
            "title_en": "Second Mention",
            "narrative_role": "reflection",
            "chronological_index": 3,
            "sura_no": 50,
            "aya_start": 12,
            "aya_end": 14,
            "is_entry_point": False,
            "summary_ar": "ذُكروا مع قوم نوح وعاد وثمود وفرعون ولوط وأصحاب الأيكة وقوم تُبَّع",
            "summary_en": "Mentioned with the people of Nuh, Aad, Thamud, Fir'awn, Lut, Aiyka, and Tubba.",
            "semantic_tags": ["destroyed_nations", "denial"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "50:12-14",
                    "snippet": "The people of Nuh denied before them, and the people of the Rass and Thamud."
                }
            ],
        },
    ],
    # =========================================================================
    # PEOPLE OF TUBBA EVENTS
    # =========================================================================
    "cluster_tubba": [
        {
            "id": "cluster_tubba:comparison_quraysh",
            "title_ar": "المقارنة بقريش",
            "title_en": "Comparison with Quraysh",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 44,
            "aya_start": 37,
            "aya_end": 37,
            "is_entry_point": True,
            "summary_ar": "أهم خير أم قوم تُبَّع والذين من قبلهم؟ أهلكناهم إنهم كانوا مجرمين",
            "summary_en": "Are they better or the people of Tubba' and those before them? We destroyed them - they were criminals.",
            "semantic_tags": ["comparison", "destruction", "criminals"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "44:37",
                    "snippet": "Are they better or the people of Tubba and those before them? We destroyed them - they were criminals."
                }
            ],
        },
        {
            "id": "cluster_tubba:among_deniers",
            "title_ar": "من المكذبين",
            "title_en": "Among the Deniers",
            "narrative_role": "reflection",
            "chronological_index": 2,
            "sura_no": 50,
            "aya_start": 14,
            "aya_end": 14,
            "is_entry_point": False,
            "summary_ar": "ذُكر قوم تُبَّع ضمن الأمم المكذبة للرسل",
            "summary_en": "People of Tubba mentioned among nations that denied messengers.",
            "semantic_tags": ["denial", "nations", "warning"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "50:14",
                    "snippet": "And the people of Aiyka and the people of Tubba. All denied the messengers, so My threat was fulfilled."
                }
            ],
        },
    ],
    # =========================================================================
    # 'ABASA EVENTS
    # =========================================================================
    "cluster_abasa": [
        {
            "id": "cluster_abasa:turning_away",
            "title_ar": "الإعراض عن الأعمى",
            "title_en": "Turning Away from the Blind Man",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 80,
            "aya_start": 1,
            "aya_end": 2,
            "is_entry_point": True,
            "summary_ar": "عبس وتولى أن جاءه الأعمى - عتاب للنبي ﷺ",
            "summary_en": "He frowned and turned away because there came to him the blind man - a divine correction.",
            "semantic_tags": ["correction", "blind_man", "prophet"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "80:1-2",
                    "snippet": "He frowned and turned away because there came to him the blind man."
                }
            ],
        },
        {
            "id": "cluster_abasa:reason",
            "title_ar": "لعله يزكى",
            "title_en": "Perhaps He Seeks Purification",
            "narrative_role": "correction",
            "chronological_index": 2,
            "sura_no": 80,
            "aya_start": 3,
            "aya_end": 4,
            "is_entry_point": False,
            "summary_ar": "وما يدريك لعله يزكى أو يذكر فتنفعه الذكرى",
            "summary_en": "What would make you know - perhaps he might purify himself, or remember and benefit from the reminder.",
            "semantic_tags": ["purification", "reminder", "benefit"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "80:3-4",
                    "snippet": "What would make you know - perhaps he might be purified or be reminded and the reminder benefit him."
                }
            ],
        },
        {
            "id": "cluster_abasa:self_sufficient",
            "title_ar": "المستغني عن الهداية",
            "title_en": "The Self-Sufficient One",
            "narrative_role": "contrast",
            "chronological_index": 3,
            "sura_no": 80,
            "aya_start": 5,
            "aya_end": 7,
            "is_entry_point": False,
            "summary_ar": "أما من استغنى فأنت له تصدى، وما عليك ألا يزكى",
            "summary_en": "As for the one who thinks himself self-sufficient, you gave him attention, but you are not responsible if he doesn't purify.",
            "semantic_tags": ["priorities", "self_sufficient", "responsibility"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "80:5-7",
                    "snippet": "As for he who thinks himself without need, to him you gave attention. And not upon you is blame if he will not be purified."
                }
            ],
        },
        {
            "id": "cluster_abasa:seeker_priority",
            "title_ar": "أولوية الساعي للهداية",
            "title_en": "Priority of the Seeker",
            "narrative_role": "lesson",
            "chronological_index": 4,
            "sura_no": 80,
            "aya_start": 8,
            "aya_end": 10,
            "is_entry_point": False,
            "summary_ar": "وأما من جاءك يسعى وهو يخشى فأنت عنه تلهى - الأولى بالاهتمام",
            "summary_en": "But as for one who came to you striving while he fears Allah, from him you are distracted - he deserves priority.",
            "semantic_tags": ["seeker", "priority", "fear_of_allah"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "80:8-10",
                    "snippet": "But as for he who came to you striving while he fears Allah, from him you are distracted."
                }
            ],
        },
    ],
    # =========================================================================
    # BANI NADIR EVENTS
    # =========================================================================
    "cluster_bani_nadir": [
        {
            "id": "cluster_bani_nadir:expulsion",
            "title_ar": "الإخراج الأول",
            "title_en": "First Expulsion",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 59,
            "aya_start": 2,
            "aya_end": 2,
            "is_entry_point": True,
            "summary_ar": "هو الذي أخرج الذين كفروا من أهل الكتاب من ديارهم لأول الحشر",
            "summary_en": "It is He who expelled those who disbelieved among the People of the Book from their homes at the first gathering.",
            "semantic_tags": ["expulsion", "jews", "first_gathering"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "59:2",
                    "snippet": "He expelled those who disbelieved among the People of the Book from their homes at the first gathering."
                }
            ],
        },
        {
            "id": "cluster_bani_nadir:unexpected",
            "title_ar": "عدم توقع الخروج",
            "title_en": "Unexpected Outcome",
            "narrative_role": "description",
            "chronological_index": 2,
            "sura_no": 59,
            "aya_start": 2,
            "aya_end": 3,
            "is_entry_point": False,
            "summary_ar": "ما ظننتم أن يخرجوا وظنوا أن حصونهم مانعتهم من الله",
            "summary_en": "You did not think they would leave, and they thought their fortresses would protect them from Allah.",
            "semantic_tags": ["fortresses", "surprise", "divine_decree"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "59:2",
                    "snippet": "You did not think they would leave, and they thought their fortresses would protect them from Allah."
                }
            ],
        },
        {
            "id": "cluster_bani_nadir:terror",
            "title_ar": "قذف الرعب",
            "title_en": "Terror Cast",
            "narrative_role": "divine_intervention",
            "chronological_index": 3,
            "sura_no": 59,
            "aya_start": 2,
            "aya_end": 2,
            "is_entry_point": False,
            "summary_ar": "فأتاهم الله من حيث لم يحتسبوا وقذف في قلوبهم الرعب",
            "summary_en": "But Allah came at them from where they did not expect and cast terror into their hearts.",
            "semantic_tags": ["terror", "divine_intervention", "unexpected"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "59:2",
                    "snippet": "Allah came to them from where they did not expect and cast terror into their hearts."
                }
            ],
        },
        {
            "id": "cluster_bani_nadir:destruction_homes",
            "title_ar": "تخريب البيوت",
            "title_en": "Destroying Their Homes",
            "narrative_role": "outcome",
            "chronological_index": 4,
            "sura_no": 59,
            "aya_start": 2,
            "aya_end": 2,
            "is_entry_point": False,
            "summary_ar": "يخربون بيوتهم بأيديهم وأيدي المؤمنين فاعتبروا يا أولي الأبصار",
            "summary_en": "They destroyed their houses with their own hands and the hands of believers. So take warning, O people of vision.",
            "semantic_tags": ["destruction", "warning", "lesson"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "59:2",
                    "snippet": "They destroyed their houses with their own hands and the hands of believers."
                }
            ],
        },
        {
            "id": "cluster_bani_nadir:hypocrites_promise",
            "title_ar": "وعود المنافقين الكاذبة",
            "title_en": "Hypocrites' False Promises",
            "narrative_role": "exposure",
            "chronological_index": 5,
            "sura_no": 59,
            "aya_start": 11,
            "aya_end": 12,
            "is_entry_point": False,
            "summary_ar": "المنافقون وعدوا بني النضير بالنصرة لكنهم كذبوا",
            "summary_en": "Hypocrites promised Bani Nadir support but lied - they would not help them.",
            "semantic_tags": ["hypocrites", "lies", "abandonment"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "59:11-12",
                    "snippet": "Those who are hypocrites say to their brothers who disbelieved: If you are expelled, we will surely leave with you."
                }
            ],
        },
    ],
    # =========================================================================
    # PEOPLE OF AIYKA EVENTS
    # =========================================================================
    "cluster_aiyka": [
        {
            "id": "cluster_aiyka:shuayb_sent",
            "title_ar": "إرسال شعيب",
            "title_en": "Shu'ayb Sent to Them",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 26,
            "aya_start": 176,
            "aya_end": 177,
            "is_entry_point": True,
            "summary_ar": "كذب أصحاب الأيكة المرسلين، إذ قال لهم شعيب ألا تتقون",
            "summary_en": "The people of Aiyka denied the messengers when Shu'ayb said to them: Will you not fear Allah?",
            "semantic_tags": ["prophet", "denial", "warning"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "26:176-177",
                    "snippet": "The companions of the thicket denied the messengers when Shu'ayb said to them: Will you not fear Allah?"
                }
            ],
        },
        {
            "id": "cluster_aiyka:message",
            "title_ar": "رسالة شعيب",
            "title_en": "Shu'ayb's Message",
            "narrative_role": "dawah",
            "chronological_index": 2,
            "sura_no": 26,
            "aya_start": 178,
            "aya_end": 184,
            "is_entry_point": False,
            "summary_ar": "دعاهم لتقوى الله والوفاء بالكيل والميزان وعدم البخس",
            "summary_en": "He called them to fear Allah, give full measure, and not deprive people of their due.",
            "semantic_tags": ["justice", "honesty", "weights_measures"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "26:181-183",
                    "snippet": "Give full measure and do not be of those who cause loss. And weigh with an even balance."
                }
            ],
        },
        {
            "id": "cluster_aiyka:rejection",
            "title_ar": "تكذيبهم لشعيب",
            "title_en": "Their Rejection",
            "narrative_role": "rejection",
            "chronological_index": 3,
            "sura_no": 26,
            "aya_start": 185,
            "aya_end": 188,
            "is_entry_point": False,
            "summary_ar": "قالوا إنما أنت من المسحرين وما أنت إلا بشر مثلنا",
            "summary_en": "They said: You are only of those affected by magic, and you are but a man like ourselves.",
            "semantic_tags": ["rejection", "accusation", "denial"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "26:185-186",
                    "snippet": "They said: You are only of those affected by magic, and you are but a man like ourselves."
                }
            ],
        },
        {
            "id": "cluster_aiyka:shadow_day",
            "title_ar": "عذاب يوم الظُلة",
            "title_en": "Day of the Shadow Punishment",
            "narrative_role": "outcome",
            "chronological_index": 4,
            "sura_no": 26,
            "aya_start": 189,
            "aya_end": 191,
            "is_entry_point": False,
            "summary_ar": "كذبوه فأخذهم عذاب يوم الظُلة، إنه كان عذاب يوم عظيم",
            "summary_en": "They denied him, so the punishment of the day of the shadow seized them. It was the punishment of a terrible day.",
            "semantic_tags": ["punishment", "shadow", "destruction"],
            "evidence": [
                {
                    "source_id": "ibn_kathir_en",
                    "reference": "26:189-190",
                    "snippet": "They denied him, so the punishment of the day of the black cloud seized them. Indeed, it was the punishment of a terrible day."
                }
            ],
        },
    ],
}


def to_pg_array(items: list) -> str:
    """Convert Python list to PostgreSQL array literal."""
    if not items:
        return "{}"
    # Escape single quotes and wrap each item
    escaped = [item.replace("'", "''").replace('"', '\\"') for item in items]
    return "{" + ",".join(f'"{item}"' for item in escaped) + "}"


def main():
    """Add new stories and events to the database."""
    import json

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check existing stories
        existing = session.execute(
            text("SELECT id FROM story_clusters")
        ).fetchall()
        existing_ids = {row[0] for row in existing}

        print(f"Found {len(existing_ids)} existing stories")

        # Add new story clusters
        added_stories = 0
        for cluster in NEW_STORY_CLUSTERS:
            if cluster["id"] in existing_ids:
                print(f"  Skipping existing: {cluster['id']}")
                continue

            session.execute(
                text("""
                    INSERT INTO story_clusters (
                        id, title_ar, title_en, short_title_ar, short_title_en,
                        category, main_persons, groups, tags, places,
                        era, era_basis, time_description_en, ayah_spans,
                        primary_sura, summary_ar, summary_en, lessons_ar, lessons_en,
                        created_at, updated_at
                    ) VALUES (
                        :id, :title_ar, :title_en, :short_title_ar, :short_title_en,
                        :category, :main_persons, :groups, :tags, :places,
                        :era, :era_basis, :time_description_en, :ayah_spans,
                        :primary_sura, :summary_ar, :summary_en, :lessons_ar, :lessons_en,
                        NOW(), NOW()
                    )
                """),
                {
                    "id": cluster["id"],
                    "title_ar": cluster["title_ar"],
                    "title_en": cluster["title_en"],
                    "short_title_ar": cluster["short_title_ar"],
                    "short_title_en": cluster["short_title_en"],
                    "category": cluster["category"],
                    "main_persons": to_pg_array(cluster["main_persons"]),
                    "groups": to_pg_array(cluster["groups"]),
                    "tags": to_pg_array(cluster["tags"]),
                    "places": json.dumps(cluster["places"]),  # JSONB
                    "era": cluster["era"],
                    "era_basis": cluster["era_basis"],
                    "time_description_en": cluster["time_description_en"],
                    "ayah_spans": json.dumps(cluster["ayah_spans"]),  # JSONB
                    "primary_sura": cluster["primary_sura"],
                    "summary_ar": cluster["summary_ar"],
                    "summary_en": cluster["summary_en"],
                    "lessons_ar": to_pg_array(cluster["lessons_ar"]),
                    "lessons_en": to_pg_array(cluster["lessons_en"]),
                }
            )
            print(f"  Added story: {cluster['title_en']}")
            added_stories += 1

        print(f"\nAdded {added_stories} new stories")

        # Add events for new stories
        added_events = 0
        for cluster_id, events in NEW_STORY_EVENTS.items():
            for event in events:
                # Check if event already exists
                existing_event = session.execute(
                    text("SELECT id FROM story_events WHERE id = :id"),
                    {"id": event["id"]}
                ).fetchone()

                if existing_event:
                    print(f"  Skipping existing event: {event['id']}")
                    continue

                session.execute(
                    text("""
                        INSERT INTO story_events (
                            id, cluster_id, title_ar, title_en, narrative_role,
                            chronological_index, sura_no, aya_start, aya_end,
                            is_entry_point, summary_ar, summary_en, semantic_tags,
                            evidence, created_at, updated_at
                        ) VALUES (
                            :id, :cluster_id, :title_ar, :title_en, :narrative_role,
                            :chronological_index, :sura_no, :aya_start, :aya_end,
                            :is_entry_point, :summary_ar, :summary_en, :semantic_tags,
                            :evidence, NOW(), NOW()
                        )
                    """),
                    {
                        "id": event["id"],
                        "cluster_id": cluster_id,
                        "title_ar": event["title_ar"],
                        "title_en": event["title_en"],
                        "narrative_role": event["narrative_role"],
                        "chronological_index": event["chronological_index"],
                        "sura_no": event["sura_no"],
                        "aya_start": event["aya_start"],
                        "aya_end": event["aya_end"],
                        "is_entry_point": event["is_entry_point"],
                        "summary_ar": event["summary_ar"],
                        "summary_en": event["summary_en"],
                        "semantic_tags": to_pg_array(event["semantic_tags"]),
                        "evidence": json.dumps(event["evidence"]),  # JSONB
                    }
                )
                added_events += 1

        print(f"Added {added_events} new events")

        session.commit()
        print("\n✅ Successfully added new stories and events!")

        # Show final counts
        result = session.execute(
            text("SELECT COUNT(*) FROM story_clusters")
        ).fetchone()
        print(f"\nTotal stories: {result[0]}")

        result = session.execute(
            text("SELECT COUNT(*) FROM story_events")
        ).fetchone()
        print(f"Total events: {result[0]}")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
