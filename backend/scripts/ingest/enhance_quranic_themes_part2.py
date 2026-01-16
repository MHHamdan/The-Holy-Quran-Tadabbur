#!/usr/bin/env python3
"""
Quranic Themes Enhancement Script - Part 2
Adds segments for remaining themes with 0 segments.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from app.core.config import settings

# Additional theme segments
THEME_SEGMENTS = {
    "theme_zakah": [
        (2, 43, 43, "أمر الزكاة", "Command of Zakat"),
        (2, 83, 83, "ميثاق بني إسرائيل", "Covenant with Children of Israel"),
        (2, 177, 177, "البر الحقيقي", "True Righteousness"),
        (9, 60, 60, "مصارف الزكاة الثمانية", "Eight Recipients of Zakat"),
        (9, 103, 103, "خذ من أموالهم صدقة", "Take charity from their wealth"),
        (23, 4, 4, "للزكاة فاعلون", "Who give zakah"),
        (30, 39, 39, "الربا والزكاة", "Usury vs Zakat"),
    ],
    "theme_amanah": [
        (2, 283, 283, "أداء الأمانة", "Fulfilling the Trust"),
        (4, 58, 58, "أداء الأمانات", "Rendering Trusts"),
        (8, 27, 27, "خيانة الأمانات", "Betraying Trusts"),
        (23, 8, 8, "رعاية الأمانات", "Guarding Trusts"),
        (33, 72, 72, "الأمانة الكبرى", "The Great Trust"),
        (70, 32, 32, "أماناتهم وعهدهم", "Their trusts and covenant"),
    ],
    "theme_sidq": [
        (2, 177, 177, "الموفون بعهدهم", "Those who fulfill their promise"),
        (9, 119, 119, "كونوا مع الصادقين", "Be with the truthful"),
        (19, 41, 41, "كان صديقا نبيا", "He was a truthful prophet"),
        (33, 23, 24, "رجال صدقوا", "Men who were true"),
        (39, 33, 33, "الذي جاء بالصدق", "Who brought the truth"),
        (49, 15, 15, "أولئك هم الصادقون", "Those are the truthful"),
    ],
    "theme_nifaq": [
        (2, 8, 20, "صفات المنافقين", "Characteristics of Hypocrites"),
        (4, 142, 143, "المنافقون في الصلاة", "Hypocrites in Prayer"),
        (9, 67, 68, "المنافقون والمنافقات", "Male and Female Hypocrites"),
        (9, 73, 73, "جهاد المنافقين", "Striving against Hypocrites"),
        (33, 60, 61, "عقوبة المنافقين", "Punishment of Hypocrites"),
        (63, 1, 8, "سورة المنافقون", "Surah Al-Munafiqun"),
    ],
    "theme_kibr": [
        (2, 34, 34, "تكبر إبليس", "Arrogance of Iblis"),
        (4, 36, 36, "لا يحب المختال الفخور", "Does not love the proud"),
        (7, 36, 36, "استكبروا عنها", "They were arrogant"),
        (16, 23, 23, "لا يحب المستكبرين", "Does not love the arrogant"),
        (31, 18, 18, "لا تمش في الأرض مرحا", "Do not walk on earth arrogantly"),
        (40, 35, 35, "كبر مقتا عند الله", "Great hatred with Allah"),
        (40, 56, 56, "في صدورهم إلا كبر", "Nothing in their chests but pride"),
    ],
    "theme_kidhb": [
        (2, 10, 10, "في قلوبهم مرض", "Disease in their hearts"),
        (3, 61, 61, "لعنة الله على الكاذبين", "Curse of Allah on liars"),
        (6, 21, 21, "من أظلم من افترى على الله كذبا", "Who is more unjust than who invents lie"),
        (16, 105, 105, "إنما يفتري الكذب", "Only those who do not believe fabricate lies"),
        (39, 3, 3, "إن الله لا يهدي من هو كاذب", "Allah does not guide the liar"),
        (51, 10, 11, "قتل الخراصون", "Destroyed are the liars"),
    ],
    "theme_maghfira": [
        (2, 268, 268, "مغفرة من الله وفضل", "Forgiveness from Allah and bounty"),
        (3, 31, 31, "يغفر لكم ذنوبكم", "He will forgive your sins"),
        (3, 135, 136, "استغفروا لذنوبهم", "Sought forgiveness for their sins"),
        (4, 110, 110, "يستغفر الله يجد الله غفورا", "Who seeks forgiveness finds Allah Forgiving"),
        (11, 3, 3, "فاستغفروه ثم توبوا", "Seek His forgiveness then repent"),
        (39, 53, 53, "يغفر الذنوب جميعا", "Forgives all sins"),
        (66, 8, 8, "يكفر عنكم سيئاتكم", "Remove from you your misdeeds"),
    ],
    "theme_ikhlas": [
        (2, 139, 139, "له مخلصين الدين", "Sincere to Him in religion"),
        (7, 29, 29, "وادعوه مخلصين", "Call upon Him being sincere"),
        (39, 2, 3, "فاعبد الله مخلصا", "Worship Allah being sincere"),
        (39, 11, 14, "أمرت أن أعبد الله مخلصا", "Commanded to worship Allah sincerely"),
        (40, 14, 14, "فادعوا الله مخلصين", "Call upon Allah being sincere"),
        (98, 5, 5, "ليعبدوا الله مخلصين", "Worship Allah being sincere"),
    ],
    "theme_khushu": [
        (2, 45, 46, "الخشوع في الصلاة", "Humility in Prayer"),
        (17, 109, 109, "يخرون للأذقان", "They fall upon their faces"),
        (21, 90, 90, "يدعوننا رغبا ورهبا", "Calling upon Us in hope and fear"),
        (23, 2, 2, "في صلاتهم خاشعون", "Humble in their prayers"),
        (33, 35, 35, "والخاشعين والخاشعات", "Humble men and women"),
        (57, 16, 16, "ألم يأن للذين آمنوا أن تخشع قلوبهم", "Has the time not come for believers' hearts to be humble"),
    ],
    "theme_riba": [
        (2, 275, 276, "الذين يأكلون الربا", "Those who consume usury"),
        (2, 278, 279, "ذروا ما بقي من الربا", "Give up what remains of usury"),
        (3, 130, 130, "لا تأكلوا الربا أضعافا", "Do not consume usury doubled"),
        (4, 161, 161, "أخذهم الربا وقد نهوا عنه", "Their taking usury though forbidden"),
        (30, 39, 39, "لا يربو عند الله", "Does not increase with Allah"),
    ],
    "theme_infaq": [
        (2, 261, 261, "مثل الذين ينفقون", "Example of those who spend"),
        (2, 262, 262, "لا يتبعون ما أنفقوا منا ولا أذى", "Not followed by reminders or injury"),
        (2, 265, 265, "مثل الذين ينفقون ابتغاء مرضاة الله", "Example of spending seeking Allah's pleasure"),
        (2, 267, 267, "أنفقوا من طيبات ما كسبتم", "Spend from the good"),
        (3, 92, 92, "لن تنالوا البر حتى تنفقوا", "You will not attain righteousness until you spend"),
        (13, 22, 22, "أنفقوا مما رزقناهم", "Spend from what We provided"),
        (63, 10, 10, "أنفقوا من قبل أن يأتي أحدكم الموت", "Spend before death comes"),
    ],
    "theme_birr_walidayn": [
        (17, 23, 24, "وبالوالدين إحسانا", "And to parents, good treatment"),
        (29, 8, 8, "ووصينا الإنسان بوالديه", "We have enjoined upon man goodness to parents"),
        (31, 14, 14, "ووصينا الإنسان بوالديه", "We enjoined upon man for his parents"),
        (46, 15, 15, "ووصينا الإنسان بوالديه إحسانا", "We enjoined upon man kindness to parents"),
    ],
    "theme_uquq_walidayn": [
        (6, 151, 151, "وبالوالدين إحسانا", "Good treatment of parents"),
        (17, 23, 23, "فلا تقل لهما أف", "Say not to them a word of disrespect"),
        (19, 14, 14, "وبرا بوالديه", "Dutiful to his parents"),
        (19, 32, 32, "وبرا بوالدتي", "Dutiful to my mother"),
    ],
    "theme_silat_rahim": [
        (2, 27, 27, "ويقطعون ما أمر الله به أن يوصل", "They sever what Allah ordered to be joined"),
        (4, 1, 1, "واتقوا الله الذي تساءلون به والأرحام", "Fear Allah through whom you ask and the wombs"),
        (13, 21, 21, "والذين يصلون ما أمر الله به أن يوصل", "Those who join what Allah commanded"),
        (13, 25, 25, "ويقطعون ما أمر الله به أن يوصل", "They sever what Allah commanded"),
        (47, 22, 22, "فهل عسيتم أن تفسدوا", "Would you perhaps cause corruption"),
    ],
    "theme_asma_sifat": [
        (7, 180, 180, "ولله الأسماء الحسنى", "And to Allah belong the most beautiful names"),
        (17, 110, 110, "أيا ما تدعوا فله الأسماء الحسنى", "Whichever you call upon, to Him belong the best names"),
        (20, 8, 8, "له الأسماء الحسنى", "To Him belong the best names"),
        (59, 22, 24, "هو الله الذي لا إله إلا هو", "He is Allah - there is no deity but He"),
    ],
    "theme_tawheed_rububiyyah": [
        (1, 2, 2, "رب العالمين", "Lord of the Worlds"),
        (6, 1, 1, "الحمد لله الذي خلق السماوات والأرض", "Praise to Allah who created heavens and earth"),
        (10, 3, 3, "إن ربكم الله الذي خلق", "Your Lord is Allah who created"),
        (13, 16, 16, "قل الله خالق كل شيء", "Say Allah is Creator of all things"),
        (35, 3, 3, "هل من خالق غير الله", "Is there a creator other than Allah"),
        (39, 62, 62, "الله خالق كل شيء", "Allah is Creator of all things"),
    ],
    "theme_tawheed_uluhiyyah": [
        (2, 21, 21, "اعبدوا ربكم", "Worship your Lord"),
        (4, 36, 36, "واعبدوا الله ولا تشركوا به شيئا", "Worship Allah and associate nothing with Him"),
        (6, 102, 102, "لا إله إلا هو", "There is no deity except Him"),
        (16, 36, 36, "اعبدوا الله واجتنبوا الطاغوت", "Worship Allah and avoid false deities"),
        (21, 25, 25, "أن لا إله إلا أنا فاعبدون", "There is no deity except Me, so worship Me"),
    ],
    "theme_tawadu": [
        (15, 88, 88, "واخفض جناحك للمؤمنين", "Lower your wing to the believers"),
        (17, 37, 37, "ولا تمش في الأرض مرحا", "Do not walk upon earth exultantly"),
        (25, 63, 63, "يمشون على الأرض هونا", "Walk upon earth humbly"),
        (26, 215, 215, "واخفض جناحك لمن اتبعك", "Lower your wing to those who follow you"),
        (31, 18, 19, "ولا تمش في الأرض مرحا", "Do not walk upon earth exultantly"),
    ],
    "theme_islah": [
        (2, 220, 220, "قل إصلاح لهم خير", "Say improvement for them is best"),
        (4, 114, 114, "من أمر بصدقة أو معروف أو إصلاح", "Whoever enjoins charity or good or reconciliation"),
        (7, 170, 170, "والذين يمسكون بالكتاب", "Those who hold to the Book"),
        (8, 1, 1, "فاتقوا الله وأصلحوا ذات بينكم", "Fear Allah and amend relations between yourselves"),
        (49, 9, 9, "فأصلحوا بينهما", "Make reconciliation between them"),
        (49, 10, 10, "إنما المؤمنون إخوة فأصلحوا", "Believers are brothers, so make reconciliation"),
    ],
    "theme_fasad": [
        (2, 11, 12, "لا تفسدوا في الأرض", "Do not cause corruption on earth"),
        (2, 27, 27, "ويفسدون في الأرض", "Cause corruption on earth"),
        (5, 32, 33, "الإفساد في الأرض", "Corruption upon the earth"),
        (7, 56, 56, "ولا تفسدوا في الأرض بعد إصلاحها", "Do not cause corruption after its reformation"),
        (28, 77, 77, "ولا تبغ الفساد في الأرض", "Do not seek corruption on earth"),
        (30, 41, 41, "ظهر الفساد في البر والبحر", "Corruption appeared on land and sea"),
    ],
    "theme_ghish": [
        (3, 161, 161, "وما كان لنبي أن يغل", "It is not for a prophet to deceive"),
        (4, 107, 107, "ولا تجادل عن الذين يختانون أنفسهم", "Do not argue for those who betray themselves"),
        (7, 85, 85, "ولا تنقصوا المكيال والميزان", "Do not decrease measure and weight"),
        (11, 85, 85, "وأوفوا المكيال والميزان", "Give full measure and weight"),
        (26, 181, 182, "أوفوا الكيل ولا تكونوا من المخسرين", "Give full measure and do not be of those who cause loss"),
    ],
    "theme_zulm": [
        (2, 279, 279, "لا تظلمون ولا تظلمون", "You do not wrong nor are wronged"),
        (4, 30, 30, "ومن يفعل ذلك عدوانا وظلما", "Whoever does that in aggression and injustice"),
        (6, 160, 160, "وهم لا يظلمون", "They will not be wronged"),
        (10, 44, 44, "إن الله لا يظلم الناس شيئا", "Allah does not wrong people at all"),
        (11, 101, 101, "وما ظلمناهم ولكن ظلموا أنفسهم", "We wronged them not but they wronged themselves"),
        (42, 42, 42, "إنما السبيل على الذين يظلمون الناس", "The cause is only against those who wrong people"),
    ],
    "theme_sunnah_nasr": [
        (3, 139, 139, "وأنتم الأعلون إن كنتم مؤمنين", "You will be superior if you are believers"),
        (5, 56, 56, "فإن حزب الله هم الغالبون", "The party of Allah will be victorious"),
        (8, 10, 10, "وما النصر إلا من عند الله", "Victory is only from Allah"),
        (22, 40, 40, "ولينصرن الله من ينصره", "Allah will surely support those who support Him"),
        (30, 47, 47, "وكان حقا علينا نصر المؤمنين", "It was incumbent upon Us to support believers"),
        (40, 51, 51, "إنا لننصر رسلنا", "We will surely support Our messengers"),
        (47, 7, 7, "إن تنصروا الله ينصركم", "If you support Allah, He will support you"),
    ],
    "theme_sunnah_taghyir": [
        (8, 53, 53, "لم يك مغيرا نعمة", "He would not change a favor"),
        (13, 11, 11, "لا يغير ما بقوم حتى يغيروا ما بأنفسهم", "Allah does not change a people until they change themselves"),
        (30, 41, 41, "ظهر الفساد في البر والبحر بما كسبت أيدي الناس", "Corruption appeared by what people's hands earned"),
        (42, 30, 30, "وما أصابكم من مصيبة فبما كسبت أيديكم", "Whatever strikes you of disaster is for what your hands earned"),
    ],
    "theme_sunnah_ihlak": [
        (6, 6, 6, "ألم يروا كم أهلكنا", "Have they not seen how many We destroyed"),
        (7, 4, 5, "وكم من قرية أهلكناها", "How many cities have We destroyed"),
        (17, 16, 17, "وإذا أردنا أن نهلك قرية", "When We intend to destroy a city"),
        (20, 128, 128, "أفلم يهد لهم كم أهلكنا", "Has it not guided them how many We destroyed"),
        (28, 58, 59, "وكم أهلكنا من قرية", "How many a city have We destroyed"),
    ],
    "theme_sunnah_ibtila": [
        (2, 155, 155, "ولنبلونكم بشيء من الخوف", "We will surely test you with something of fear"),
        (3, 186, 186, "لتبلون في أموالكم وأنفسكم", "You will surely be tested in your property and selves"),
        (21, 35, 35, "ونبلوكم بالشر والخير فتنة", "We test you with evil and good as trial"),
        (29, 2, 3, "أحسب الناس أن يتركوا أن يقولوا آمنا", "Do people think they will not be tested"),
        (47, 31, 31, "ولنبلونكم حتى نعلم المجاهدين", "We will surely test you until We make evident"),
        (67, 2, 2, "ليبلوكم أيكم أحسن عملا", "To test which of you is best in deed"),
    ],
    "theme_sunnah_istidraj": [
        (6, 44, 44, "فلما نسوا ما ذكروا به فتحنا عليهم", "When they forgot, We opened upon them"),
        (7, 182, 183, "سنستدرجهم من حيث لا يعلمون", "We will progressively lead them"),
        (23, 55, 56, "أيحسبون أنما نمدهم به من مال وبنين", "Do they think that what We extend"),
        (68, 44, 45, "فذرني ومن يكذب بهذا الحديث", "Leave Me with whoever denies this statement"),
    ],
}


def main():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        segments_created = 0
        themes_updated = 0

        for theme_id, segments in THEME_SEGMENTS.items():
            # Check if theme exists
            result = conn.execute(
                text("SELECT id FROM quranic_themes WHERE id = :id"),
                {"id": theme_id}
            ).fetchone()

            if not result:
                print(f"Theme not found: {theme_id}")
                continue

            print(f"Processing: {theme_id}")

            for order, (sura, ayah_start, ayah_end, title_ar, title_en) in enumerate(segments, 1):
                segment_id = f"{theme_id}_seg_{order}"

                exists = conn.execute(
                    text("SELECT 1 FROM theme_segments WHERE id = :id"),
                    {"id": segment_id}
                ).fetchone()

                if not exists:
                    summary_ar = f"آيات في موضوع {title_ar} - سورة {sura} الآيات {ayah_start}-{ayah_end}"
                    summary_en = f"Verses on {title_en} - Surah {sura}, Ayat {ayah_start}-{ayah_end}"

                    conn.execute(
                        text("""INSERT INTO theme_segments
                            (id, theme_id, segment_order, sura_no, ayah_start, ayah_end,
                             title_ar, title_en, summary_ar, summary_en,
                             is_verified, importance_weight, evidence_sources, evidence_chunk_ids)
                            VALUES (:id, :theme_id, :order, :sura, :start, :end,
                                    :title_ar, :title_en, :summary_ar, :summary_en,
                                    true, 1.0, '{}', '{}')"""),
                        {"id": segment_id, "theme_id": theme_id, "order": order,
                         "sura": sura, "start": ayah_start, "end": ayah_end,
                         "title_ar": title_ar, "title_en": title_en,
                         "summary_ar": summary_ar, "summary_en": summary_en}
                    )
                    segments_created += 1

            count = conn.execute(
                text("SELECT COUNT(*) FROM theme_segments WHERE theme_id = :id"),
                {"id": theme_id}
            ).fetchone()[0]

            conn.execute(
                text("UPDATE quranic_themes SET segment_count = :count, is_complete = true WHERE id = :id"),
                {"count": count, "id": theme_id}
            )
            themes_updated += 1

        conn.commit()
        print(f"\nComplete: {segments_created} segments created, {themes_updated} themes updated")


if __name__ == "__main__":
    main()
