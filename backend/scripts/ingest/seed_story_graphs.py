#!/usr/bin/env python3
"""
Seed script for enhanced story graph data.

This script populates the story_segments and story_connections tables
with real, grounded data for Quranic stories.

Each segment has:
- title_ar/en: Human-readable event label
- narrative_role: Semantic role in the story
- chronological_index: Position in timeline
- semantic_tags: Thematic keywords
- evidence_sources: Tafsir citations with snippets

Each connection has:
- edge_type: Relationship type
- is_chronological: Whether it's a temporal edge
- justification: Why this connection exists
- evidence_chunk_ids: Tafsir grounding

Usage:
    python scripts/ingest/seed_story_graphs.py
"""
import asyncio
import os
import sys
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"
)

# =============================================================================
# DHUL-QARNAYN STORY DATA (Surah 18:83-98)
# =============================================================================

DHUL_QARNAYN_SEGMENTS = [
    {
        "id": "dhulqarnayn_intro",
        "title_ar": "السؤال عن ذي القرنين",
        "title_en": "The Question About Dhul-Qarnayn",
        "narrative_role": "introduction",
        "chronological_index": 1,
        "semantic_tags": ["revelation", "question", "test_of_prophet"],
        "summary_ar": "يُسأل النبي ﷺ عن ذي القرنين، وهذا يدل على شهرته وأهمية قصته في توضيح القوة العادلة",
        "summary_en": "The Prophet (PBUH) is asked about Dhul-Qarnayn, indicating his fame among People of the Book and the importance of his story in illustrating righteous power.",
        "is_entry_point": True,
        "memorization_cue_en": "They asked to test - Allah answered to teach",
        "memorization_cue_ar": "سألوا ليمتحنوا - أجاب الله ليعلّم",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:83",
                "snippet": "They ask you about Dhul-Qarnayn. The Jews asked the Prophet about him, as a test, having been advised by the rabbis."
            }
        ],
        # Update ayah range to match correct split
        "aya_start": 83,
        "aya_end": 83,
    },
    {
        "id": "dhulqarnayn_empowerment",
        "title_ar": "التمكين الإلهي",
        "title_en": "Divine Empowerment",
        "narrative_role": "divine_mission",
        "chronological_index": 2,
        "semantic_tags": ["divine_empowerment", "tamkeen", "authority", "resources"],
        "summary_ar": "مكّن الله ذا القرنين في الأرض وآتاه من كل شيء سبباً - أي العلم والقوة والموارد لتحقيق العدل",
        "summary_en": "Allah established Dhul-Qarnayn on earth and gave him the means to everything - knowledge, power, and resources to establish justice.",
        "is_entry_point": False,
        "memorization_cue_en": "Tamkeen (establishment) + Sabab (means) = Righteous power",
        "memorization_cue_ar": "تمكين + أسباب = قوة صالحة",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:84",
                "snippet": "We established him in the earth, and We gave him the means to everything. This means: knowledge of how to reach his goals."
            },
            {
                "source_id": "tabari_ar",
                "reference": "18:84",
                "snippet": "وآتيناه من كل شيء سبباً: أي علماً بالطرق والوسائل التي يتوصل بها إلى ما يريد"
            }
        ],
        "aya_start": 84,
        "aya_end": 84,
    },
    {
        "id": "dhulqarnayn_west",
        "title_ar": "الرحلة إلى الغرب - اختبار العدل",
        "title_en": "Journey West - The Justice Test",
        "narrative_role": "test_or_trial",
        "chronological_index": 3,
        "semantic_tags": ["travel", "west", "justice", "punishment", "mercy", "moral_choice"],
        "summary_ar": "رحل غرباً حتى وصل مغرب الشمس ووجد قوماً. خُيّر بين العقاب والإحسان فاختار العدل: يُعذّب الظالم ويُحسن للمؤمن",
        "summary_en": "He traveled west until he reached the setting sun and found a people. Given a choice between punishment and kindness, he chose justice: punish the oppressor, be good to the believer.",
        "is_entry_point": False,
        "memorization_cue_en": "TEST 1: Punish wrongdoer, reward believer",
        "memorization_cue_ar": "الاختبار ١: عذّب الظالم، أكرم المؤمن",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:86-87",
                "snippet": "We said: O Dhul-Qarnayn! Either punish them, or treat them with kindness. He said: As for him who wrongs, we shall punish him."
            },
            {
                "source_id": "qurtubi_ar",
                "reference": "18:86",
                "snippet": "هذا تخيير بين القتال والدعوة، وهو اختبار لعدله وحكمه في الناس"
            }
        ],
        "aya_start": 85,
        "aya_end": 88,
    },
    {
        "id": "dhulqarnayn_east",
        "title_ar": "الرحلة إلى الشرق - اختبار ضبط النفس",
        "title_en": "Journey East - The Restraint Test",
        "narrative_role": "moral_decision",
        "chronological_index": 4,
        "semantic_tags": ["travel", "east", "restraint", "vulnerable_people", "self_control"],
        "summary_ar": "رحل شرقاً فوجد قوماً لا ستر لهم من الشمس - قوم ضعفاء. كذلك - أي عاملهم بالعدل ولم يستغل ضعفهم",
        "summary_en": "He traveled east and found a people with no shelter from the sun - vulnerable people. 'Kadhalika' (Thus) - he treated them justly and did not exploit their weakness.",
        "is_entry_point": False,
        "memorization_cue_en": "TEST 2: Power over weak, chose restraint",
        "memorization_cue_ar": "الاختبار ٢: قوة على الضعفاء، اختار العدل",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:90-91",
                "snippet": "A people for whom We had not made any shelter against it (the sun). So it was - he dealt with them as he had dealt with the former people."
            },
            {
                "source_id": "tabari_ar",
                "reference": "18:91",
                "snippet": "كذلك: أي كما فعل بأهل المغرب من العدل والإنصاف، فعل بأهل المشرق مثل ذلك"
            }
        ],
        "aya_start": 89,
        "aya_end": 91,
    },
    {
        "id": "dhulqarnayn_barrier_encounter",
        "title_ar": "لقاء المستضعفين بين السدين",
        "title_en": "Encounter with the Oppressed",
        "narrative_role": "encounter",
        "chronological_index": 5,
        "semantic_tags": ["encounter", "oppressed", "yajuj_majuj", "plea_for_help"],
        "summary_ar": "وجد قوماً بين جبلين لا يكادون يفقهون قولاً، يشكون من إفساد يأجوج ومأجوج في الأرض",
        "summary_en": "He found a people between two mountains who could barely understand speech, suffering from the corruption of Yajuj and Majuj in the land.",
        "is_entry_point": False,
        "memorization_cue_en": "Between two mountains: oppressed people seek help",
        "memorization_cue_ar": "بين السدين: مظلومون يطلبون العون",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:93-94",
                "snippet": "He found a people who could scarcely understand speech. They said: O Dhul-Qarnayn! Verily Yajuj and Majuj are doing great mischief in the land."
            },
            {
                "source_id": "qurtubi_ar",
                "reference": "18:94",
                "snippet": "يأجوج ومأجوج أمتان عظيمتان من ذرية يافث بن نوح، يفسدون في الأرض"
            }
        ],
        "aya_start": 92,
        "aya_end": 94,
    },
    {
        "id": "dhulqarnayn_refuses_tribute",
        "title_ar": "رفض الخراج - التوكل على الله",
        "title_en": "Refusing Tribute - Trust in Allah",
        "narrative_role": "moral_decision",
        "chronological_index": 6,
        "semantic_tags": ["tawakkul", "generosity", "selfless_service", "refusing_payment"],
        "summary_ar": "عرضوا عليه جزية لبناء السد فرفض قائلاً: ما مكني فيه ربي خير. فقط أعينوني بقوة أجعل بينكم وبينهم ردماً",
        "summary_en": "They offered tribute for building a barrier. He refused: 'What my Lord has established me in is better.' Just help me with labor and I will make a barrier.",
        "is_entry_point": False,
        "memorization_cue_en": "TEST 3 PASSED: 'Allah's blessing is enough'",
        "memorization_cue_ar": "الاختبار ٣: ما مكني فيه ربي خير",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:95",
                "snippet": "He said: That in which my Lord has established me is better. So help me with strength (labor), I will erect between you and them a barrier."
            },
            {
                "source_id": "tabari_ar",
                "reference": "18:95",
                "snippet": "ما مكني فيه ربي خير من خرجكم: أي ما أعطاني الله من الملك والقدرة خير مما تعطونني"
            }
        ],
        "aya_start": 95,
        "aya_end": 95,
    },
    {
        "id": "dhulqarnayn_barrier",
        "title_ar": "بناء السد - الهندسة والقيادة",
        "title_en": "Building the Barrier - Engineering & Leadership",
        "narrative_role": "outcome",
        "chronological_index": 7,
        "semantic_tags": ["construction", "iron", "copper", "engineering", "teamwork", "protection"],
        "summary_ar": "أمرهم بإحضار زبر الحديد حتى ساوى بين الجبلين، ثم أوقدوا النار ونفخوا وصب عليه القطر، فما استطاعوا أن يظهروه ولا ينقبوه",
        "summary_en": "He commanded them to bring iron blocks, filled the gap between mountains, heated it with fire, and poured molten copper. They could neither climb over nor dig through it.",
        "is_entry_point": False,
        "memorization_cue_en": "Iron blocks + fire + copper = impenetrable barrier",
        "memorization_cue_ar": "زبر الحديد + نار + قطر = سد لا يُخترق",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:96",
                "snippet": "Bring me blocks of iron - until he had filled up the gap between the two mountain-sides. He said: Blow! - till he made it (red as) fire. He said: Bring me molten copper to pour over it."
            },
            {
                "source_id": "qurtubi_ar",
                "reference": "18:96",
                "snippet": "زبر الحديد: قطع الحديد الكبيرة. والقطر: النحاس المذاب. وهذا دليل على علمه بالصناعات"
            }
        ],
        "aya_start": 96,
        "aya_end": 97,
    },
    {
        "id": "dhulqarnayn_humility",
        "title_ar": "التواضع والإرجاع لله",
        "title_en": "Humility - This is Mercy from my Lord",
        "narrative_role": "reflection",
        "chronological_index": 8,
        "semantic_tags": ["humility", "tawakkul", "mercy", "eschatology", "gratitude", "impermanence"],
        "summary_ar": "قال: هذا رحمة من ربي. فإذا جاء وعد ربي جعله دكاء، وكان وعد ربي حقاً. نسب الفضل لله وأقر بزوال كل شيء إلا وعده",
        "summary_en": "He said: 'This is mercy from my Lord. When my Lord's promise comes, He will level it to the ground.' He attributed success to Allah and acknowledged the impermanence of all things except Allah's promise.",
        "is_entry_point": False,
        "memorization_cue_en": "After success: 'This is mercy from my Lord'",
        "memorization_cue_ar": "بعد النجاح: هذا رحمة من ربي",
        "evidence_sources": [
            {
                "source_id": "ibn_kathir_en",
                "reference": "18:98",
                "snippet": "He said: This is a mercy from my Lord, but when the Promise of my Lord comes, He shall level it to the ground. And the Promise of my Lord is ever true."
            },
            {
                "source_id": "tabari_ar",
                "reference": "18:98",
                "snippet": "هذا رحمة من ربي: أي هذا السد توفيق من الله ورحمة منه بعباده. فإذا جاء وعد ربي: يعني يوم القيامة"
            }
        ],
        "aya_start": 98,
        "aya_end": 98,
    },
]

# Chronological connections (segment to segment)
DHUL_QARNAYN_CONNECTIONS = [
    {
        "source": "dhulqarnayn_intro",
        "target": "dhulqarnayn_empowerment",
        "edge_type": "chronological_next",
        "is_chronological": True,
        "strength": 1.0,
        "justification_en": "The question (83) is immediately followed by Allah's description of His empowerment (84)",
        "evidence_chunk_ids": ["ibn_kathir_en:18:83-84"],
    },
    {
        "source": "dhulqarnayn_empowerment",
        "target": "dhulqarnayn_west",
        "edge_type": "cause_effect",
        "is_chronological": True,
        "strength": 1.0,
        "justification_en": "Divine empowerment enabled his journeys - 'fa atba'a sababan' (he followed a means) references the means given in 84",
        "evidence_chunk_ids": ["ibn_kathir_en:18:84-85"],
    },
    {
        "source": "dhulqarnayn_west",
        "target": "dhulqarnayn_east",
        "edge_type": "chronological_next",
        "is_chronological": True,
        "strength": 1.0,
        "justification_en": "'Thumma atba'a sababan' (Then he followed another means) - clear temporal sequence",
        "evidence_chunk_ids": ["ibn_kathir_en:18:89"],
    },
    {
        "source": "dhulqarnayn_east",
        "target": "dhulqarnayn_barrier_encounter",
        "edge_type": "chronological_next",
        "is_chronological": True,
        "strength": 1.0,
        "justification_en": "'Thumma atba'a sababan' again (92) - third journey to the barrier region",
        "evidence_chunk_ids": ["ibn_kathir_en:18:92"],
    },
    {
        "source": "dhulqarnayn_barrier_encounter",
        "target": "dhulqarnayn_refuses_tribute",
        "edge_type": "chronological_next",
        "is_chronological": True,
        "strength": 1.0,
        "justification_en": "The people's plea (94) leads directly to his response (95)",
        "evidence_chunk_ids": ["ibn_kathir_en:18:94-95"],
    },
    {
        "source": "dhulqarnayn_refuses_tribute",
        "target": "dhulqarnayn_barrier",
        "edge_type": "cause_effect",
        "is_chronological": True,
        "strength": 1.0,
        "justification_en": "His decision to help without payment (95) leads to the construction (96-97)",
        "evidence_chunk_ids": ["ibn_kathir_en:18:95-97"],
    },
    {
        "source": "dhulqarnayn_barrier",
        "target": "dhulqarnayn_humility",
        "edge_type": "cause_effect",
        "is_chronological": True,
        "strength": 1.0,
        "justification_en": "Upon completing the great work (97), he immediately attributes it to Allah's mercy (98)",
        "evidence_chunk_ids": ["ibn_kathir_en:18:97-98"],
    },
    # Thematic connections
    {
        "source": "dhulqarnayn_west",
        "target": "dhulqarnayn_east",
        "edge_type": "parallel",
        "is_chronological": False,
        "strength": 0.9,
        "justification_en": "Both are tests of character when given power over people - 'kadhalika' (91) explicitly links them",
        "evidence_chunk_ids": ["tabari_ar:18:91"],
    },
    {
        "source": "dhulqarnayn_empowerment",
        "target": "dhulqarnayn_humility",
        "edge_type": "contrast",
        "is_chronological": False,
        "strength": 0.85,
        "justification_en": "Arc of righteous leadership: given everything (84) yet attributes all to Allah (98)",
        "evidence_chunk_ids": ["ibn_kathir_en:18:84", "ibn_kathir_en:18:98"],
    },
    {
        "source": "dhulqarnayn_refuses_tribute",
        "target": "dhulqarnayn_humility",
        "edge_type": "thematic_link",
        "is_chronological": False,
        "strength": 0.8,
        "justification_en": "Both show tawakkul: 'ma makkani fihi rabbi' (95) echoes 'hadha rahmah min rabbi' (98)",
        "evidence_chunk_ids": ["ibn_kathir_en:18:95", "ibn_kathir_en:18:98"],
    },
]


def main():
    """Run the seed script."""
    print("=" * 60)
    print("SEEDING STORY GRAPH DATA")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Update segments with new data
        print("\n1. Updating Dhul-Qarnayn segments...")
        updated_count = 0

        for seg_data in DHUL_QARNAYN_SEGMENTS:
            seg_id = seg_data["id"]

            # Check if segment exists
            result = session.execute(
                text("SELECT id FROM story_segments WHERE id = :id"),
                {"id": seg_id}
            )
            exists = result.fetchone()

            if exists:
                # Update existing segment
                update_sql = text("""
                    UPDATE story_segments SET
                        title_ar = :title_ar,
                        title_en = :title_en,
                        narrative_role = :narrative_role,
                        chronological_index = :chronological_index,
                        semantic_tags = :semantic_tags,
                        summary_ar = :summary_ar,
                        summary_en = :summary_en,
                        is_entry_point = :is_entry_point,
                        memorization_cue_ar = :memorization_cue_ar,
                        memorization_cue_en = :memorization_cue_en,
                        evidence_sources = :evidence_sources,
                        aya_start = :aya_start,
                        aya_end = :aya_end,
                        updated_at = :updated_at
                    WHERE id = :id
                """)

                session.execute(update_sql, {
                    "id": seg_id,
                    "title_ar": seg_data.get("title_ar"),
                    "title_en": seg_data.get("title_en"),
                    "narrative_role": seg_data.get("narrative_role"),
                    "chronological_index": seg_data.get("chronological_index"),
                    "semantic_tags": seg_data.get("semantic_tags"),
                    "summary_ar": seg_data.get("summary_ar"),
                    "summary_en": seg_data.get("summary_en"),
                    "is_entry_point": seg_data.get("is_entry_point", False),
                    "memorization_cue_ar": seg_data.get("memorization_cue_ar"),
                    "memorization_cue_en": seg_data.get("memorization_cue_en"),
                    "evidence_sources": str(seg_data.get("evidence_sources", [])).replace("'", '"'),
                    "aya_start": seg_data.get("aya_start"),
                    "aya_end": seg_data.get("aya_end"),
                    "updated_at": datetime.utcnow(),
                })
                print(f"   Updated: {seg_id}")
                updated_count += 1
            else:
                # Insert new segment
                print(f"   Creating new segment: {seg_id}")
                insert_sql = text("""
                    INSERT INTO story_segments (
                        id, story_id, narrative_order, sura_no, aya_start, aya_end,
                        title_ar, title_en, narrative_role, chronological_index,
                        semantic_tags, summary_ar, summary_en, is_entry_point,
                        memorization_cue_ar, memorization_cue_en, evidence_sources,
                        created_at, updated_at
                    ) VALUES (
                        :id, 'story_dhulqarnayn', :narrative_order, 18, :aya_start, :aya_end,
                        :title_ar, :title_en, :narrative_role, :chronological_index,
                        :semantic_tags, :summary_ar, :summary_en, :is_entry_point,
                        :memorization_cue_ar, :memorization_cue_en, :evidence_sources,
                        :created_at, :updated_at
                    )
                """)
                session.execute(insert_sql, {
                    "id": seg_id,
                    "narrative_order": seg_data.get("chronological_index", 1),
                    "aya_start": seg_data.get("aya_start"),
                    "aya_end": seg_data.get("aya_end"),
                    "title_ar": seg_data.get("title_ar"),
                    "title_en": seg_data.get("title_en"),
                    "narrative_role": seg_data.get("narrative_role"),
                    "chronological_index": seg_data.get("chronological_index"),
                    "semantic_tags": seg_data.get("semantic_tags"),
                    "summary_ar": seg_data.get("summary_ar"),
                    "summary_en": seg_data.get("summary_en"),
                    "is_entry_point": seg_data.get("is_entry_point", False),
                    "memorization_cue_ar": seg_data.get("memorization_cue_ar"),
                    "memorization_cue_en": seg_data.get("memorization_cue_en"),
                    "evidence_sources": str(seg_data.get("evidence_sources", [])).replace("'", '"'),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                })
                updated_count += 1

        print(f"\n   Segments updated/created: {updated_count}")

        # 2. Clear existing connections for this story and add new ones
        print("\n2. Updating story connections...")

        # Get all segment IDs for this story
        seg_ids = [s["id"] for s in DHUL_QARNAYN_SEGMENTS]

        # Delete existing connections
        session.execute(
            text("""
                DELETE FROM story_connections
                WHERE source_segment_id IN :ids OR target_segment_id IN :ids
            """),
            {"ids": tuple(seg_ids)}
        )
        print("   Cleared existing connections")

        # Insert new connections
        conn_count = 0
        for conn in DHUL_QARNAYN_CONNECTIONS:
            insert_conn = text("""
                INSERT INTO story_connections (
                    source_segment_id, target_segment_id, edge_type, connection_type,
                    is_chronological, strength, justification_en, evidence_chunk_ids,
                    created_at, updated_at
                ) VALUES (
                    :source, :target, :edge_type, :edge_type,
                    :is_chronological, :strength, :justification_en, :evidence_chunk_ids,
                    :created_at, :updated_at
                )
            """)
            session.execute(insert_conn, {
                "source": conn["source"],
                "target": conn["target"],
                "edge_type": conn["edge_type"],
                "is_chronological": conn["is_chronological"],
                "strength": conn["strength"],
                "justification_en": conn.get("justification_en"),
                "evidence_chunk_ids": conn["evidence_chunk_ids"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            conn_count += 1
            print(f"   Added: {conn['source']} -> {conn['target']} ({conn['edge_type']})")

        print(f"\n   Connections added: {conn_count}")

        # Commit
        session.commit()
        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)

        # Verify
        print("\nVerifying data...")
        result = session.execute(text("""
            SELECT id, title_en, narrative_role, chronological_index
            FROM story_segments
            WHERE story_id = 'story_dhulqarnayn'
            ORDER BY chronological_index
        """))
        rows = result.fetchall()
        print(f"\nSegments in database ({len(rows)}):")
        for row in rows:
            print(f"   {row[0]}: {row[1]} (role={row[2]}, index={row[3]})")

        result2 = session.execute(text("""
            SELECT source_segment_id, target_segment_id, edge_type, is_chronological
            FROM story_connections
            WHERE source_segment_id LIKE 'dhulqarnayn%'
            ORDER BY source_segment_id
        """))
        conns = result2.fetchall()
        print(f"\nConnections in database ({len(conns)}):")
        for conn in conns:
            chrono = "CHRONO" if conn[3] else "THEMATIC"
            print(f"   {conn[0]} -> {conn[1]} ({conn[2]}, {chrono})")

    except Exception as e:
        session.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
