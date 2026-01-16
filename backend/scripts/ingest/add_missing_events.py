#!/usr/bin/env python3
"""
Add missing story events to the database.
Stories with 0 events: Badr, Idris, Ifk, Isra/Miraj, Hudaybiyyah, Fath Mecca
"""
import json
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

# =============================================================================
# NEW STORY EVENTS
# =============================================================================

NEW_EVENTS = {
    # =========================================================================
    # BATTLE OF BADR (8:5-19, 41-44)
    # =========================================================================
    "cluster_badr": [
        {
            "id": "cluster_badr:departure",
            "title_ar": "خروج المسلمين",
            "title_en": "Muslims' Departure",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 8, "aya_start": 5, "aya_end": 6,
            "is_entry_point": True,
            "summary_ar": "خرج المسلمون من المدينة وبعضهم كاره للقتال",
            "summary_en": "Muslims departed from Madinah, some reluctant about fighting.",
            "semantic_tags": ["departure", "reluctance", "faith"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "8:5", "snippet": "As your Lord caused you to go out from your home in truth, and verily a party among the believers disliked it."}],
        },
        {
            "id": "cluster_badr:promise_of_victory",
            "title_ar": "وعد النصر",
            "title_en": "Promise of Victory",
            "narrative_role": "prophecy",
            "chronological_index": 2,
            "sura_no": 8, "aya_start": 7, "aya_end": 8,
            "is_entry_point": False,
            "summary_ar": "وعد الله المسلمين بإحدى الطائفتين: العير أو النفير",
            "summary_en": "Allah promised Muslims one of two groups: the caravan or the army.",
            "semantic_tags": ["promise", "choice", "divine_plan"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "8:7", "snippet": "And when Allah promised you one of the two parties that it should be yours."}],
        },
        {
            "id": "cluster_badr:dua_and_angels",
            "title_ar": "الدعاء ونزول الملائكة",
            "title_en": "Supplication and Angels Descend",
            "narrative_role": "divine_intervention",
            "chronological_index": 3,
            "sura_no": 8, "aya_start": 9, "aya_end": 12,
            "is_entry_point": False,
            "summary_ar": "استغاثة المسلمين وإمداد الله لهم بألف من الملائكة",
            "summary_en": "Muslims called for help, Allah reinforced them with a thousand angels.",
            "semantic_tags": ["dua", "angels", "divine_help", "reinforcement"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "8:9", "snippet": "When you sought help of your Lord, and He answered you: I will help you with a thousand of the angels following one another."}],
        },
        {
            "id": "cluster_badr:rain_and_sleep",
            "title_ar": "المطر والنعاس",
            "title_en": "Rain and Sleep",
            "narrative_role": "miracle",
            "chronological_index": 4,
            "sura_no": 8, "aya_start": 11, "aya_end": 11,
            "is_entry_point": False,
            "summary_ar": "أنزل الله المطر والنعاس أمانةً من عنده",
            "summary_en": "Allah sent rain and drowsiness as security from Him.",
            "semantic_tags": ["rain", "sleep", "tranquility", "miracle"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "8:11", "snippet": "He covered you with drowsiness as a security from Him, and He sent down water from the sky."}],
        },
        {
            "id": "cluster_badr:battle",
            "title_ar": "المعركة",
            "title_en": "The Battle",
            "narrative_role": "confrontation",
            "chronological_index": 5,
            "sura_no": 8, "aya_start": 17, "aya_end": 19,
            "is_entry_point": False,
            "summary_ar": "فما قتلتموهم ولكن الله قتلهم، وما رميت إذ رميت ولكن الله رمى",
            "summary_en": "You did not kill them, but Allah killed them. You did not throw when you threw, but Allah threw.",
            "semantic_tags": ["battle", "victory", "divine_action"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "8:17", "snippet": "You killed them not, but Allah killed them. And you threw not when you threw, but Allah threw."}],
        },
        {
            "id": "cluster_badr:abu_jahl_death",
            "title_ar": "مقتل أبي جهل",
            "title_en": "Death of Abu Jahl",
            "narrative_role": "outcome",
            "chronological_index": 6,
            "sura_no": 8, "aya_start": 48, "aya_end": 48,
            "is_entry_point": False,
            "summary_ar": "قُتل فرعون هذه الأمة أبو جهل في المعركة",
            "summary_en": "The Pharaoh of this Ummah, Abu Jahl, was killed in the battle.",
            "semantic_tags": ["victory", "tyrant_death", "outcome"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "8:48", "snippet": "When Satan made their deeds attractive to them, and said: None of mankind can overcome you today."}],
        },
        {
            "id": "cluster_badr:victory_lessons",
            "title_ar": "دروس النصر",
            "title_en": "Lessons of Victory",
            "narrative_role": "reflection",
            "chronological_index": 7,
            "sura_no": 8, "aya_start": 41, "aya_end": 44,
            "is_entry_point": False,
            "summary_ar": "يوم الفرقان يوم التقى الجمعان، والنصر من عند الله",
            "summary_en": "Day of Criterion when the two armies met; victory is from Allah.",
            "semantic_tags": ["furqan", "lesson", "gratitude", "victory"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "8:41", "snippet": "And what you have captured, a fifth of it is for Allah and for the Messenger."}],
        },
    ],

    # =========================================================================
    # ISRA AND MIRAJ (17:1)
    # =========================================================================
    "cluster_isra_miraj": [
        {
            "id": "cluster_isra_miraj:glorification",
            "title_ar": "سبحان الذي أسرى",
            "title_en": "Glory to Him Who Made Journey",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 17, "aya_start": 1, "aya_end": 1,
            "is_entry_point": True,
            "summary_ar": "سبحان الذي أسرى بعبده ليلاً من المسجد الحرام إلى المسجد الأقصى",
            "summary_en": "Glory to Him who took His servant by night from Masjid al-Haram to Masjid al-Aqsa.",
            "semantic_tags": ["glorification", "miracle", "journey"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "17:1", "snippet": "Exalted is He who took His Servant by night from al-Masjid al-Haram to al-Masjid al-Aqsa."}],
        },
        {
            "id": "cluster_isra_miraj:blessed_surroundings",
            "title_ar": "الأرض المباركة",
            "title_en": "Blessed Surroundings",
            "narrative_role": "miracle",
            "chronological_index": 2,
            "sura_no": 17, "aya_start": 1, "aya_end": 1,
            "is_entry_point": False,
            "summary_ar": "المسجد الأقصى الذي باركنا حوله",
            "summary_en": "Al-Aqsa Mosque whose surroundings We have blessed.",
            "semantic_tags": ["blessing", "aqsa", "holiness"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "17:1", "snippet": "To al-Masjid al-Aqsa, whose surroundings We have blessed."}],
        },
        {
            "id": "cluster_isra_miraj:show_signs",
            "title_ar": "إظهار الآيات",
            "title_en": "Showing Signs",
            "narrative_role": "outcome",
            "chronological_index": 3,
            "sura_no": 17, "aya_start": 1, "aya_end": 1,
            "is_entry_point": False,
            "summary_ar": "لنريه من آياتنا إنه هو السميع البصير",
            "summary_en": "To show him of Our signs. Indeed, He is the Hearing, the Seeing.",
            "semantic_tags": ["signs", "divine_wisdom", "hearing", "seeing"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "17:1", "snippet": "To show him of Our signs. Indeed, He is the Hearing, the Seeing."}],
        },
    ],

    # =========================================================================
    # CONQUEST OF MECCA (48:1-29)
    # =========================================================================
    "cluster_fath_mecca": [
        {
            "id": "cluster_fath_mecca:clear_victory",
            "title_ar": "الفتح المبين",
            "title_en": "Clear Victory",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 48, "aya_start": 1, "aya_end": 3,
            "is_entry_point": True,
            "summary_ar": "إنا فتحنا لك فتحاً مبيناً",
            "summary_en": "Indeed, We have given you a clear conquest.",
            "semantic_tags": ["victory", "conquest", "divine_gift"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:1", "snippet": "Indeed, We have given you a clear conquest."}],
        },
        {
            "id": "cluster_fath_mecca:forgiveness_past_future",
            "title_ar": "مغفرة الذنوب",
            "title_en": "Forgiveness of Sins",
            "narrative_role": "divine_intervention",
            "chronological_index": 2,
            "sura_no": 48, "aya_start": 2, "aya_end": 2,
            "is_entry_point": False,
            "summary_ar": "ليغفر لك الله ما تقدم من ذنبك وما تأخر",
            "summary_en": "That Allah may forgive you your sins of the past and future.",
            "semantic_tags": ["forgiveness", "blessing", "honor"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:2", "snippet": "That Allah may forgive for you what preceded of your sin and what will follow."}],
        },
        {
            "id": "cluster_fath_mecca:tranquility",
            "title_ar": "السكينة في قلوب المؤمنين",
            "title_en": "Tranquility in Believers' Hearts",
            "narrative_role": "miracle",
            "chronological_index": 3,
            "sura_no": 48, "aya_start": 4, "aya_end": 4,
            "is_entry_point": False,
            "summary_ar": "هو الذي أنزل السكينة في قلوب المؤمنين",
            "summary_en": "It is He who sent down tranquility into the hearts of the believers.",
            "semantic_tags": ["tranquility", "faith", "increase"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:4", "snippet": "It is He who sent down tranquility into the hearts of the believers."}],
        },
        {
            "id": "cluster_fath_mecca:entry",
            "title_ar": "دخول مكة",
            "title_en": "Entering Mecca",
            "narrative_role": "outcome",
            "chronological_index": 4,
            "sura_no": 48, "aya_start": 27, "aya_end": 27,
            "is_entry_point": False,
            "summary_ar": "لتدخلن المسجد الحرام إن شاء الله آمنين",
            "summary_en": "You will surely enter al-Masjid al-Haram, if Allah wills, in safety.",
            "semantic_tags": ["entry", "safety", "fulfillment"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:27", "snippet": "You will surely enter al-Masjid al-Haram, if Allah wills, in safety."}],
        },
        {
            "id": "cluster_fath_mecca:islam_prevails",
            "title_ar": "ظهور الإسلام",
            "title_en": "Islam Prevails",
            "narrative_role": "reflection",
            "chronological_index": 5,
            "sura_no": 48, "aya_start": 28, "aya_end": 29,
            "is_entry_point": False,
            "summary_ar": "هو الذي أرسل رسوله بالهدى ودين الحق ليظهره على الدين كله",
            "summary_en": "It is He who sent His Messenger with guidance and the religion of truth to manifest it over all religion.",
            "semantic_tags": ["islam", "truth", "victory", "prophecy"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:28", "snippet": "It is He who sent His Messenger with guidance and the religion of truth to manifest it over all religion."}],
        },
    ],

    # =========================================================================
    # IDRIS (19:56-57, 21:85)
    # =========================================================================
    "cluster_idris": [
        {
            "id": "cluster_idris:truthful_prophet",
            "title_ar": "صديقاً نبياً",
            "title_en": "Truthful Prophet",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 19, "aya_start": 56, "aya_end": 56,
            "is_entry_point": True,
            "summary_ar": "واذكر في الكتاب إدريس إنه كان صديقاً نبياً",
            "summary_en": "Mention in the Book, Idris. Indeed, he was a man of truth and a prophet.",
            "semantic_tags": ["prophet", "truthfulness", "mention"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "19:56", "snippet": "And mention in the Book, Idris. Indeed, he was a man of truth and a prophet."}],
        },
        {
            "id": "cluster_idris:elevated",
            "title_ar": "الرفعة العلية",
            "title_en": "Raised to High Station",
            "narrative_role": "outcome",
            "chronological_index": 2,
            "sura_no": 19, "aya_start": 57, "aya_end": 57,
            "is_entry_point": False,
            "summary_ar": "ورفعناه مكاناً علياً",
            "summary_en": "And We raised him to a high station.",
            "semantic_tags": ["elevation", "honor", "station"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "19:57", "snippet": "And We raised him to a high station."}],
        },
        {
            "id": "cluster_idris:among_patient",
            "title_ar": "من الصابرين",
            "title_en": "Among the Patient",
            "narrative_role": "reflection",
            "chronological_index": 3,
            "sura_no": 21, "aya_start": 85, "aya_end": 85,
            "is_entry_point": False,
            "summary_ar": "وإسماعيل وإدريس وذا الكفل كل من الصابرين",
            "summary_en": "And Ismail and Idris and Dhul-Kifl - all were of the patient.",
            "semantic_tags": ["patience", "righteousness", "mention"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "21:85", "snippet": "And Ismail and Idris and Dhul-Kifl - all were of the patient."}],
        },
    ],

    # =========================================================================
    # IFK - THE SLANDER (24:11-26)
    # =========================================================================
    "cluster_ifk": [
        {
            "id": "cluster_ifk:group_of_slanderers",
            "title_ar": "عصبة من المنافقين",
            "title_en": "Group of Slanderers",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 24, "aya_start": 11, "aya_end": 11,
            "is_entry_point": True,
            "summary_ar": "إن الذين جاءوا بالإفك عصبة منكم",
            "summary_en": "Indeed, those who came with falsehood are a group among you.",
            "semantic_tags": ["slander", "hypocrites", "falsehood"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "24:11", "snippet": "Indeed, those who came with falsehood are a group among you."}],
        },
        {
            "id": "cluster_ifk:good_in_it",
            "title_ar": "خير للمؤمنين",
            "title_en": "Good for Believers",
            "narrative_role": "reflection",
            "chronological_index": 2,
            "sura_no": 24, "aya_start": 11, "aya_end": 11,
            "is_entry_point": False,
            "summary_ar": "لا تحسبوه شراً لكم بل هو خير لكم",
            "summary_en": "Do not think it bad for you; rather it is good for you.",
            "semantic_tags": ["wisdom", "good", "lesson"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "24:11", "snippet": "Do not think it bad for you; rather it is good for you."}],
        },
        {
            "id": "cluster_ifk:why_not_good_opinion",
            "title_ar": "لولا ظنوا خيراً",
            "title_en": "Why Not Think Good",
            "narrative_role": "warning",
            "chronological_index": 3,
            "sura_no": 24, "aya_start": 12, "aya_end": 13,
            "is_entry_point": False,
            "summary_ar": "لولا إذ سمعتموه ظن المؤمنون والمؤمنات بأنفسهم خيراً",
            "summary_en": "Why did the believing men and women not think good of their own people?",
            "semantic_tags": ["good_opinion", "believers", "lesson"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "24:12", "snippet": "Why, when you heard it, did not the believing men and believing women think good of one another?"}],
        },
        {
            "id": "cluster_ifk:innocence_revealed",
            "title_ar": "البراءة من السماء",
            "title_en": "Innocence from Heaven",
            "narrative_role": "divine_intervention",
            "chronological_index": 4,
            "sura_no": 24, "aya_start": 26, "aya_end": 26,
            "is_entry_point": False,
            "summary_ar": "الطيبات للطيبين والطيبون للطيبات أولئك مبرءون مما يقولون",
            "summary_en": "Good women are for good men; those are declared innocent of what the slanderers say.",
            "semantic_tags": ["innocence", "purity", "vindication"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "24:26", "snippet": "Good women are for good men, and good men are for good women. Those are declared innocent of what the slanderers say."}],
        },
    ],

    # =========================================================================
    # HUDAYBIYYAH (48:1-29) - Treaty aspects
    # =========================================================================
    "cluster_hudaybiyyah": [
        {
            "id": "cluster_hudaybiyyah:clear_victory",
            "title_ar": "الفتح المبين",
            "title_en": "Clear Victory",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 48, "aya_start": 1, "aya_end": 1,
            "is_entry_point": True,
            "summary_ar": "إنا فتحنا لك فتحاً مبيناً - صلح الحديبية",
            "summary_en": "Indeed, We have given you a clear victory - Treaty of Hudaybiyyah.",
            "semantic_tags": ["treaty", "victory", "wisdom"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:1", "snippet": "Indeed, We have given you a clear conquest."}],
        },
        {
            "id": "cluster_hudaybiyyah:pledge_tree",
            "title_ar": "بيعة الشجرة",
            "title_en": "Pledge Under the Tree",
            "narrative_role": "covenant",
            "chronological_index": 2,
            "sura_no": 48, "aya_start": 18, "aya_end": 18,
            "is_entry_point": False,
            "summary_ar": "لقد رضي الله عن المؤمنين إذ يبايعونك تحت الشجرة",
            "summary_en": "Allah was pleased with the believers when they pledged allegiance under the tree.",
            "semantic_tags": ["pledge", "ridwan", "tree", "satisfaction"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:18", "snippet": "Certainly was Allah pleased with the believers when they pledged allegiance to you under the tree."}],
        },
        {
            "id": "cluster_hudaybiyyah:tranquility",
            "title_ar": "السكينة",
            "title_en": "Tranquility Sent Down",
            "narrative_role": "miracle",
            "chronological_index": 3,
            "sura_no": 48, "aya_start": 18, "aya_end": 18,
            "is_entry_point": False,
            "summary_ar": "فعلم ما في قلوبهم فأنزل السكينة عليهم",
            "summary_en": "He knew what was in their hearts and sent down tranquility upon them.",
            "semantic_tags": ["tranquility", "knowledge", "hearts"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:18", "snippet": "And He knew what was in their hearts, so He sent down tranquility upon them."}],
        },
        {
            "id": "cluster_hudaybiyyah:victory_soon",
            "title_ar": "الفتح القريب",
            "title_en": "Near Victory",
            "narrative_role": "prophecy",
            "chronological_index": 4,
            "sura_no": 48, "aya_start": 18, "aya_end": 18,
            "is_entry_point": False,
            "summary_ar": "وأثابهم فتحاً قريباً",
            "summary_en": "And rewarded them with an imminent conquest.",
            "semantic_tags": ["conquest", "reward", "prophecy"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:18", "snippet": "And rewarded them with an imminent conquest."}],
        },
        {
            "id": "cluster_hudaybiyyah:spoils_plenty",
            "title_ar": "مغانم كثيرة",
            "title_en": "Many Gains",
            "narrative_role": "outcome",
            "chronological_index": 5,
            "sura_no": 48, "aya_start": 19, "aya_end": 20,
            "is_entry_point": False,
            "summary_ar": "ومغانم كثيرة يأخذونها وكان الله عزيزاً حكيماً",
            "summary_en": "And much war booty they will take. Allah is Mighty and Wise.",
            "semantic_tags": ["spoils", "blessing", "wisdom"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "48:19", "snippet": "And much war booty which they will take. And ever is Allah Exalted in Might and Wise."}],
        },
    ],
}


def seed_events(session):
    """Seed missing story events."""
    print("\nSeeding Missing Story Events...")

    for cluster_id, events in NEW_EVENTS.items():
        print(f"\n  Cluster: {cluster_id}")
        for event in events:
            event_id = event["id"]

            # Check if exists
            result = session.execute(
                text("SELECT id FROM story_events WHERE id = :id"),
                {"id": event_id}
            )
            exists = result.fetchone()

            if exists:
                print(f"    [EXISTS] {event_id}")
                continue

            # Insert new event
            insert_sql = text("""
                INSERT INTO story_events (
                    id, cluster_id, title_ar, title_en,
                    narrative_role, chronological_index,
                    sura_no, aya_start, aya_end,
                    is_entry_point, summary_ar, summary_en,
                    semantic_tags, evidence,
                    created_at, updated_at
                ) VALUES (
                    :id, :cluster_id, :title_ar, :title_en,
                    :narrative_role, :chronological_index,
                    :sura_no, :aya_start, :aya_end,
                    :is_entry_point, :summary_ar, :summary_en,
                    :semantic_tags, :evidence,
                    :created_at, :updated_at
                )
            """)
            session.execute(insert_sql, {
                "id": event_id,
                "cluster_id": cluster_id,
                "title_ar": event["title_ar"],
                "title_en": event["title_en"],
                "narrative_role": event["narrative_role"],
                "chronological_index": event["chronological_index"],
                "sura_no": event["sura_no"],
                "aya_start": event["aya_start"],
                "aya_end": event["aya_end"],
                "is_entry_point": event.get("is_entry_point", False),
                "summary_ar": event.get("summary_ar"),
                "summary_en": event.get("summary_en"),
                "semantic_tags": event.get("semantic_tags", []),
                "evidence": json.dumps(event.get("evidence", [])),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            print(f"    [ADDED] {event_id}")

    session.commit()
    print("\n  Done!")


def main():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        seed_events(session)
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
