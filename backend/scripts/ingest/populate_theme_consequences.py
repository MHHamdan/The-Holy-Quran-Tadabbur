#!/usr/bin/env python3
"""
Populate theme consequences based on Islamic scholarly requirements.
Commands lead to rewards, prohibitions lead to punishments.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from app.core.config import settings

# Theme consequences: theme_id -> list of (type, desc_ar, desc_en, verses)
THEME_CONSEQUENCES = {
    # Positive consequences for righteous actions
    "theme_tawheed": [
        ("reward", "الهداية والنور", "Guidance and Light", [{"sura": 6, "ayah": 82}, {"sura": 39, "ayah": 22}]),
        ("reward", "الأمن من العذاب", "Safety from Punishment", [{"sura": 6, "ayah": 82}]),
        ("reward", "دخول الجنة", "Entry to Paradise", [{"sura": 98, "ayah": 7}]),
    ],
    "theme_iman_billah": [
        ("reward", "الحياة الطيبة", "A Good Life", [{"sura": 16, "ayah": 97}]),
        ("reward", "محبة الله", "Allah's Love", [{"sura": 3, "ayah": 31}]),
        ("reward", "الولاية والنصر", "Divine Protection and Victory", [{"sura": 22, "ayah": 38}]),
    ],
    "theme_salah": [
        ("reward", "النهي عن الفحشاء والمنكر", "Protection from Immorality", [{"sura": 29, "ayah": 45}]),
        ("reward", "الفلاح والنجاح", "Success and Prosperity", [{"sura": 23, "ayah": 1}, {"sura": 23, "ayah": 2}]),
        ("reward", "السكينة والطمأنينة", "Tranquility and Peace", [{"sura": 13, "ayah": 28}]),
    ],
    "theme_zakah": [
        ("reward", "تزكية النفس", "Purification of Self", [{"sura": 9, "ayah": 103}]),
        ("reward", "مضاعفة الأجر", "Multiplication of Reward", [{"sura": 2, "ayah": 261}]),
        ("reward", "البركة في الرزق", "Blessing in Provision", [{"sura": 34, "ayah": 39}]),
    ],
    "theme_siyam": [
        ("reward", "التقوى", "Attainment of Taqwa", [{"sura": 2, "ayah": 183}]),
        ("reward", "مغفرة الذنوب", "Forgiveness of Sins", [{"sura": 2, "ayah": 184}]),
    ],
    "theme_hajj": [
        ("reward", "محو الذنوب", "Erasure of Sins", [{"sura": 2, "ayah": 197}]),
        ("reward", "شهود المنافع", "Witnessing Benefits", [{"sura": 22, "ayah": 28}]),
    ],
    "theme_sabr": [
        ("reward", "معية الله", "Allah's Companionship", [{"sura": 2, "ayah": 153}]),
        ("reward", "الأجر بغير حساب", "Reward Without Measure", [{"sura": 39, "ayah": 10}]),
        ("reward", "الإمامة في الدين", "Leadership in Religion", [{"sura": 32, "ayah": 24}]),
    ],
    "theme_tawbah": [
        ("reward", "تبديل السيئات حسنات", "Conversion of Bad Deeds to Good", [{"sura": 25, "ayah": 70}]),
        ("reward", "محبة الله", "Allah's Love", [{"sura": 2, "ayah": 222}]),
        ("reward", "دخول الجنة", "Entry to Paradise", [{"sura": 66, "ayah": 8}]),
    ],
    "theme_tawakkul": [
        ("reward", "الكفاية من الله", "Allah's Sufficiency", [{"sura": 65, "ayah": 3}]),
        ("reward", "حسن التوكل", "Best Reliance", [{"sura": 3, "ayah": 173}]),
    ],
    "theme_taqwa": [
        ("reward", "الفرقان والمخرج", "Criterion and Way Out", [{"sura": 8, "ayah": 29}, {"sura": 65, "ayah": 2}]),
        ("reward", "الرزق من حيث لا يحتسب", "Provision from Unexpected Sources", [{"sura": 65, "ayah": 3}]),
        ("reward", "الكرامة عند الله", "Honor with Allah", [{"sura": 49, "ayah": 13}]),
    ],
    "theme_shukr": [
        ("reward", "زيادة النعم", "Increase in Blessings", [{"sura": 14, "ayah": 7}]),
        ("reward", "الجزاء الحسن", "Good Recompense", [{"sura": 54, "ayah": 35}]),
    ],
    "theme_dhikr": [
        ("reward", "طمأنينة القلب", "Tranquility of Heart", [{"sura": 13, "ayah": 28}]),
        ("reward", "ذكر الله له", "Allah's Remembrance of Him", [{"sura": 2, "ayah": 152}]),
    ],
    "theme_ihsan": [
        ("reward", "محبة الله", "Allah's Love", [{"sura": 2, "ayah": 195}]),
        ("reward", "الجزاء الأحسن", "The Best Recompense", [{"sura": 55, "ayah": 60}]),
    ],
    "theme_adl": [
        ("reward", "محبة الله", "Allah's Love", [{"sura": 49, "ayah": 9}]),
        ("reward", "القرب من التقوى", "Closeness to Piety", [{"sura": 5, "ayah": 8}]),
    ],

    # Negative consequences for sins
    "theme_shirk": [
        ("punishment", "حبوط الأعمال", "Nullification of Deeds", [{"sura": 39, "ayah": 65}, {"sura": 6, "ayah": 88}]),
        ("punishment", "الخلود في النار", "Eternal Hellfire", [{"sura": 4, "ayah": 48}]),
        ("punishment", "حرمان الجنة", "Prohibition from Paradise", [{"sura": 5, "ayah": 72}]),
    ],
    "theme_nifaq": [
        ("punishment", "الدرك الأسفل من النار", "Lowest Depths of Hell", [{"sura": 4, "ayah": 145}]),
        ("punishment", "العذاب المهين", "Humiliating Punishment", [{"sura": 4, "ayah": 138}]),
        ("punishment", "مرض القلب", "Disease of Heart", [{"sura": 2, "ayah": 10}]),
    ],
    "theme_kibr": [
        ("punishment", "الطبع على القلب", "Seal on Heart", [{"sura": 40, "ayah": 35}]),
        ("punishment", "دخول جهنم", "Entry to Hellfire", [{"sura": 40, "ayah": 60}]),
        ("punishment", "الصرف عن الآيات", "Turning Away from Signs", [{"sura": 7, "ayah": 146}]),
    ],
    "theme_kidhb": [
        ("punishment", "لعنة الله", "Allah's Curse", [{"sura": 3, "ayah": 61}]),
        ("punishment", "عدم الهداية", "Lack of Guidance", [{"sura": 39, "ayah": 3}]),
    ],
    "theme_riba": [
        ("punishment", "محق البركة", "Removal of Blessing", [{"sura": 2, "ayah": 276}]),
        ("punishment", "الحرب من الله", "War from Allah", [{"sura": 2, "ayah": 279}]),
    ],
    "theme_zulm": [
        ("punishment", "عدم الهداية", "Lack of Guidance", [{"sura": 2, "ayah": 258}]),
        ("punishment", "الهلاك", "Destruction", [{"sura": 11, "ayah": 101}]),
    ],
    "theme_fasad": [
        ("punishment", "العقوبة الدنيوية", "Worldly Punishment", [{"sura": 5, "ayah": 33}]),
        ("punishment", "الفساد في البر والبحر", "Corruption Spreading", [{"sura": 30, "ayah": 41}]),
    ],

    # Paradise descriptions
    "theme_jannah": [
        ("description", "الأنهار الجارية", "Flowing Rivers", [{"sura": 2, "ayah": 25}]),
        ("description", "الخلود والنعيم", "Eternity and Bliss", [{"sura": 9, "ayah": 72}]),
        ("description", "رضوان الله", "Allah's Pleasure", [{"sura": 3, "ayah": 15}]),
    ],

    # Hellfire descriptions
    "theme_nar": [
        ("description", "العذاب الدائم", "Eternal Punishment", [{"sura": 2, "ayah": 39}]),
        ("description", "الشراب والطعام", "Food and Drink of Hell", [{"sura": 44, "ayah": 43}, {"sura": 44, "ayah": 46}]),
    ],
}


def main():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        consequences_created = 0

        for theme_id, consequences in THEME_CONSEQUENCES.items():
            # Check if theme exists
            result = conn.execute(
                text("SELECT id FROM quranic_themes WHERE id = :id"),
                {"id": theme_id}
            ).fetchone()

            if not result:
                print(f"Theme not found: {theme_id}")
                continue

            print(f"Processing: {theme_id}")

            for order, (ctype, desc_ar, desc_en, verses) in enumerate(consequences, 1):
                # Check if consequence exists
                exists = conn.execute(
                    text("""SELECT 1 FROM theme_consequences
                            WHERE theme_id = :tid AND description_ar = :desc"""),
                    {"tid": theme_id, "desc": desc_ar}
                ).fetchone()

                if not exists:
                    import json
                    conn.execute(
                        text("""INSERT INTO theme_consequences
                            (theme_id, consequence_type, description_ar, description_en,
                             supporting_verses, evidence_chunk_ids, display_order)
                            VALUES (:tid, :ctype, :desc_ar, :desc_en, :verses, '{}', :order)"""),
                        {"tid": theme_id, "ctype": ctype, "desc_ar": desc_ar,
                         "desc_en": desc_en, "verses": json.dumps(verses), "order": order}
                    )
                    consequences_created += 1

        conn.commit()
        print(f"\nComplete: {consequences_created} consequences created")


if __name__ == "__main__":
    main()
