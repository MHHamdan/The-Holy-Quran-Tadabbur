#!/usr/bin/env python3
"""
Quranic Themes Enhancement Script
Populates theme_segments with verse associations for existing quranic_themes.
"""

import os
import sys
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from app.core.config import settings

# Theme segments data: theme_id -> list of (sura, ayah_start, ayah_end, title_ar, title_en)
THEME_SEGMENTS = {
    "theme_tawheed": [
        (2, 163, 163, "وحدانية الإله", "Oneness of the Divine"),
        (2, 255, 255, "آية الكرسي", "Ayat al-Kursi"),
        (3, 2, 2, "الحي القيوم", "The Ever-Living"),
        (3, 18, 18, "شهادة التوحيد", "Testimony of Tawhid"),
        (6, 102, 103, "لا تدركه الأبصار", "Vision Cannot Perceive Him"),
        (20, 14, 14, "لا إله إلا أنا", "There is no god but Me"),
        (21, 22, 22, "لو كان فيهما آلهة", "Had there been gods"),
        (23, 91, 91, "ما اتخذ الله من ولد", "Allah has not taken a son"),
        (28, 88, 88, "لا إله إلا هو", "There is no god but Him"),
        (57, 3, 3, "الأول والآخر", "The First and The Last"),
        (59, 22, 24, "أسماء الله الحسنى", "Beautiful Names of Allah"),
        (112, 1, 4, "سورة الإخلاص", "Surah Al-Ikhlas"),
    ],
    "theme_shirk": [
        (2, 165, 165, "محبة الأنداد", "Love of False Gods"),
        (4, 48, 48, "الشرك لا يغفر", "Shirk is Unforgivable"),
        (4, 116, 116, "من يشرك بالله", "Whoever Associates Partners"),
        (6, 88, 88, "لحبط عنهم ما كانوا يعملون", "Their deeds nullified"),
        (7, 33, 33, "أن تشركوا بالله", "To associate with Allah"),
        (16, 51, 51, "لا تتخذوا إلهين", "Do not take two gods"),
        (22, 31, 31, "غير مشركين به", "Not associating partners"),
        (31, 13, 13, "الشرك لظلم عظيم", "Shirk is a great injustice"),
        (39, 65, 65, "لئن أشركت ليحبطن عملك", "If you associate, deeds nullified"),
    ],
    "theme_iman_billah": [
        (2, 3, 4, "صفات المؤمنين", "Qualities of Believers"),
        (2, 285, 285, "إيمان الرسول والمؤمنين", "Faith of Messenger and Believers"),
        (3, 179, 179, "ليميز الله الخبيث", "That Allah may distinguish"),
        (4, 136, 136, "آمنوا بالله ورسوله", "Believe in Allah and His Messenger"),
        (8, 2, 4, "إنما المؤمنون", "The believers are only those"),
        (23, 1, 11, "قد أفلح المؤمنون", "Successful are the believers"),
        (49, 14, 15, "الإيمان الكامل", "Complete Faith"),
    ],
    "theme_iman_malaika": [
        (2, 97, 98, "جبريل والملائكة", "Jibreel and Angels"),
        (2, 177, 177, "الإيمان بالملائكة", "Belief in Angels"),
        (2, 285, 285, "وملائكته", "And His Angels"),
        (4, 136, 136, "وملائكته", "And His Angels"),
        (35, 1, 1, "الملائكة رسلا", "Angels as Messengers"),
        (66, 6, 6, "ملائكة غلاظ شداد", "Angels stern and severe"),
        (82, 10, 12, "الحفظة الكاتبون", "Noble Recording Angels"),
    ],
    "theme_iman_kutub": [
        (2, 4, 4, "الإيمان بما أنزل", "Belief in Revelation"),
        (2, 136, 136, "الكتب المنزلة", "Revealed Books"),
        (3, 3, 4, "التوراة والإنجيل", "Torah and Gospel"),
        (4, 136, 136, "الكتب", "Divine Books"),
        (5, 44, 48, "التوراة والإنجيل والقرآن", "Torah, Gospel, and Quran"),
        (42, 15, 15, "الإيمان بالكتب", "Belief in Books"),
        (87, 18, 19, "صحف إبراهيم وموسى", "Scriptures of Ibrahim and Musa"),
    ],
    "theme_iman_rusul": [
        (2, 136, 136, "الإيمان بالرسل", "Belief in Messengers"),
        (2, 285, 285, "ورسله", "And His Messengers"),
        (3, 84, 84, "لا نفرق بين أحد", "We make no distinction"),
        (4, 150, 152, "من يفرق بين الرسل", "Those who distinguish between Messengers"),
        (4, 163, 165, "رسل قصصناهم", "Messengers We have mentioned"),
        (6, 83, 90, "الأنبياء في القرآن", "Prophets in the Quran"),
        (23, 23, 50, "قصص الأنبياء", "Stories of Prophets"),
    ],
    "theme_iman_yawm_akhir": [
        (2, 4, 4, "يؤمنون بالآخرة", "Believe in the Hereafter"),
        (2, 62, 62, "واليوم الآخر", "And the Last Day"),
        (4, 136, 136, "واليوم الآخر", "And the Last Day"),
        (6, 92, 92, "يؤمنون بالآخرة", "Believe in the Hereafter"),
        (22, 1, 7, "زلزلة الساعة", "Earthquake of the Hour"),
        (56, 1, 56, "يوم الواقعة", "Day of the Event"),
        (75, 1, 15, "يوم القيامة", "Day of Resurrection"),
        (82, 1, 19, "انفطار السماء", "Splitting of Heaven"),
        (99, 1, 8, "زلزال الأرض", "Earth's Earthquake"),
    ],
    "theme_iman_qadr": [
        (3, 145, 145, "بإذن الله", "By Allah's Permission"),
        (6, 17, 17, "إن يمسسك الله بضر", "If Allah touches you with harm"),
        (9, 51, 51, "قل لن يصيبنا", "Say: Nothing will befall us"),
        (25, 2, 2, "قدر كل شيء", "Decreed everything"),
        (33, 38, 38, "قدرا مقدورا", "A destined decree"),
        (54, 49, 49, "كل شيء بقدر", "Everything by measure"),
        (57, 22, 23, "في كتاب من قبل", "In a Book before"),
        (76, 30, 30, "وما تشاءون إلا أن يشاء الله", "You do not will except Allah wills"),
    ],
    "theme_jannah": [
        (2, 25, 25, "جنات تجري من تحتها", "Gardens beneath which rivers flow"),
        (3, 15, 15, "أزواج مطهرة", "Purified spouses"),
        (3, 133, 136, "جنة عرضها السماوات", "Garden as wide as heavens"),
        (4, 57, 57, "ظلا ظليلا", "Perpetual shade"),
        (9, 72, 72, "جنات عدن", "Gardens of Eden"),
        (18, 31, 31, "يحلون فيها من أساور", "Adorned with bracelets"),
        (36, 55, 58, "أصحاب الجنة اليوم", "Companions of Paradise today"),
        (44, 51, 57, "المتقين في مقام أمين", "Righteous in secure position"),
        (55, 46, 78, "ولمن خاف مقام ربه", "For who feared his Lord"),
        (56, 15, 40, "السابقون الأولون", "The Forerunners"),
        (76, 5, 22, "إن الأبرار", "Indeed the righteous"),
    ],
    "theme_nar": [
        (2, 24, 24, "نارا وقودها الناس", "Fire whose fuel is people"),
        (2, 39, 39, "أصحاب النار", "Companions of the Fire"),
        (3, 12, 12, "ستغلبون وتحشرون", "You will be overcome"),
        (4, 56, 56, "بدلناهم جلودا غيرها", "We will replace their skins"),
        (9, 68, 68, "نار جهنم خالدين", "Fire of Hell eternally"),
        (22, 19, 22, "قطعت لهم ثياب من نار", "Garments of fire"),
        (44, 43, 50, "شجرة الزقوم", "Tree of Zaqqum"),
        (56, 41, 56, "أصحاب الشمال", "Companions of the Left"),
        (67, 6, 11, "للذين كفروا بربهم", "For those who disbelieve"),
        (74, 26, 31, "سأصليه سقر", "I will drive him into Saqar"),
        (78, 21, 30, "إن جهنم كانت مرصادا", "Indeed Hell lies in wait"),
    ],
    "theme_salah": [
        (2, 3, 3, "يقيمون الصلاة", "Establish prayer"),
        (2, 43, 43, "أقيموا الصلاة", "Establish prayer"),
        (2, 238, 238, "حافظوا على الصلوات", "Guard your prayers"),
        (4, 101, 103, "صلاة الخوف", "Prayer in Fear"),
        (5, 6, 6, "الوضوء", "Ablution"),
        (11, 114, 114, "أقم الصلاة طرفي النهار", "Establish prayer at both ends"),
        (17, 78, 78, "الصلوات الخمس", "Five Daily Prayers"),
        (20, 14, 14, "أقم الصلاة لذكري", "Establish prayer for My remembrance"),
        (23, 2, 2, "في صلاتهم خاشعون", "Humble in their prayers"),
        (62, 9, 11, "صلاة الجمعة", "Friday Prayer"),
        (73, 20, 20, "قيام الليل", "Night Prayer"),
    ],
    "theme_zakat": [
        (2, 43, 43, "وآتوا الزكاة", "And give zakah"),
        (2, 177, 177, "وآتى الزكاة", "And gives zakah"),
        (2, 267, 274, "آداب الإنفاق", "Etiquettes of Spending"),
        (9, 60, 60, "مصارف الزكاة", "Recipients of Zakah"),
        (9, 103, 103, "خذ من أموالهم صدقة", "Take from their wealth charity"),
        (23, 4, 4, "للزكاة فاعلون", "Who give zakah"),
        (30, 39, 39, "وما آتيتم من زكاة", "What you give in zakah"),
    ],
    "theme_siyam": [
        (2, 183, 183, "كتب عليكم الصيام", "Fasting prescribed"),
        (2, 184, 184, "أياما معدودات", "A limited number of days"),
        (2, 185, 185, "شهر رمضان", "Month of Ramadan"),
        (2, 187, 187, "ليلة الصيام", "Night of Fasting"),
    ],
    "theme_hajj": [
        (2, 125, 129, "البيت الحرام", "The Sacred House"),
        (2, 158, 158, "الصفا والمروة", "Safa and Marwa"),
        (2, 196, 203, "مناسك الحج", "Rites of Hajj"),
        (3, 97, 97, "ولله على الناس حج البيت", "Pilgrimage is a duty"),
        (5, 95, 97, "صيد الحج", "Hunting during Hajj"),
        (22, 26, 33, "أذن في الناس بالحج", "Call to Pilgrimage"),
    ],
    "theme_sabr": [
        (2, 45, 45, "واستعينوا بالصبر", "Seek help through patience"),
        (2, 153, 157, "إن الله مع الصابرين", "Allah is with the patient"),
        (3, 200, 200, "اصبروا وصابروا", "Be patient and endure"),
        (12, 90, 90, "من يتق ويصبر", "Whoever fears and is patient"),
        (16, 126, 127, "واصبر وما صبرك إلا بالله", "Be patient, patience is from Allah"),
        (31, 17, 17, "واصبر على ما أصابك", "Be patient over what befalls"),
        (39, 10, 10, "إنما يوفى الصابرون", "The patient will be given"),
        (42, 43, 43, "لمن صبر وغفر", "Whoever is patient and forgives"),
        (103, 3, 3, "وتواصوا بالصبر", "And advise patience"),
    ],
    "theme_tawbah": [
        (2, 37, 37, "فتاب عليه", "So He turned to him"),
        (2, 128, 128, "وتب علينا", "And accept our repentance"),
        (2, 222, 222, "إن الله يحب التوابين", "Allah loves those who repent"),
        (3, 89, 89, "إلا الذين تابوا", "Except those who repent"),
        (4, 17, 18, "التوبة على الله", "Repentance accepted by Allah"),
        (9, 3, 5, "فإن تبتم فهو خير لكم", "If you repent, it is better"),
        (9, 117, 118, "ثم تاب عليهم", "Then He turned to them"),
        (24, 31, 31, "وتوبوا إلى الله جميعا", "And turn to Allah all of you"),
        (25, 70, 71, "من تاب وآمن", "Whoever repents and believes"),
        (39, 53, 53, "لا تقنطوا من رحمة الله", "Do not despair of Allah's mercy"),
        (66, 8, 8, "توبة نصوحا", "Sincere repentance"),
    ],
    "theme_tawakkul": [
        (3, 159, 159, "فتوكل على الله", "Put your trust in Allah"),
        (3, 173, 173, "حسبنا الله ونعم الوكيل", "Sufficient for us is Allah"),
        (5, 23, 23, "وعلى الله فتوكلوا", "And upon Allah rely"),
        (8, 2, 2, "وعلى ربهم يتوكلون", "And upon their Lord they rely"),
        (9, 51, 51, "قل لن يصيبنا إلا ما كتب الله", "Say: Nothing befalls us except"),
        (9, 129, 129, "حسبي الله", "Sufficient for me is Allah"),
        (11, 123, 123, "فاعبده وتوكل عليه", "Worship Him and rely on Him"),
        (14, 12, 12, "وعلى الله فليتوكل المتوكلون", "Upon Allah let the reliant rely"),
        (65, 3, 3, "ومن يتوكل على الله فهو حسبه", "Whoever relies on Allah, He is sufficient"),
    ],
    "theme_taqwa": [
        (2, 2, 2, "هدى للمتقين", "Guidance for the righteous"),
        (2, 197, 197, "وتزودوا فإن خير الزاد التقوى", "Best provision is Taqwa"),
        (3, 102, 102, "اتقوا الله حق تقاته", "Fear Allah as He should be feared"),
        (3, 133, 133, "أعدت للمتقين", "Prepared for the righteous"),
        (7, 96, 96, "لو أن أهل القرى آمنوا واتقوا", "Had people believed and had taqwa"),
        (49, 13, 13, "إن أكرمكم عند الله أتقاكم", "Most honored is most righteous"),
        (65, 2, 5, "ومن يتق الله يجعل له مخرجا", "Whoever fears Allah, He makes a way out"),
    ],
    "theme_shukr": [
        (2, 152, 152, "فاذكروني أذكركم واشكروا لي", "Remember Me, I remember you, be grateful"),
        (7, 10, 10, "قليلا ما تشكرون", "Little are you grateful"),
        (14, 7, 7, "لئن شكرتم لأزيدنكم", "If you are grateful, I will increase"),
        (16, 78, 78, "لعلكم تشكرون", "That you might be grateful"),
        (27, 40, 40, "ليبلوني أأشكر أم أكفر", "To test whether I am grateful"),
        (31, 12, 12, "أن اشكر لله", "Be grateful to Allah"),
        (34, 13, 13, "اعملوا آل داود شكرا", "Work in gratitude, family of Dawud"),
    ],
    "theme_dhikr": [
        (2, 152, 152, "فاذكروني أذكركم", "Remember Me, I will remember you"),
        (3, 191, 191, "يذكرون الله قياما وقعودا", "Remember Allah standing and sitting"),
        (13, 28, 28, "ألا بذكر الله تطمئن القلوب", "By remembrance hearts find rest"),
        (18, 24, 24, "واذكر ربك إذا نسيت", "Remember your Lord when you forget"),
        (33, 41, 42, "اذكروا الله ذكرا كثيرا", "Remember Allah abundantly"),
        (73, 8, 8, "واذكر اسم ربك", "Remember the name of your Lord"),
        (87, 15, 15, "وذكر اسم ربه فصلى", "Remembers his Lord's name and prays"),
    ],
    "theme_dua": [
        (2, 186, 186, "أجيب دعوة الداع", "I respond to the caller"),
        (3, 38, 38, "دعاء زكريا", "Prayer of Zakariyya"),
        (7, 55, 56, "ادعوا ربكم تضرعا", "Call upon your Lord humbly"),
        (14, 40, 41, "رب اجعلني مقيم الصلاة", "Make me establisher of prayer"),
        (17, 11, 11, "ويدع الإنسان بالشر", "Man supplicates for evil"),
        (21, 89, 90, "دعاء الأنبياء", "Prayers of Prophets"),
        (25, 74, 74, "ربنا هب لنا", "Our Lord, grant us"),
        (40, 60, 60, "ادعوني أستجب لكم", "Call upon Me, I will respond"),
    ],
    "theme_ihsan": [
        (2, 195, 195, "وأحسنوا إن الله يحب المحسنين", "Do good, Allah loves doers of good"),
        (3, 134, 134, "والكاظمين الغيظ", "Those who restrain anger"),
        (4, 125, 125, "من أحسن دينا", "Who is better in religion"),
        (5, 93, 93, "ليس على الذين آمنوا وعملوا الصالحات جناح", "No blame on believers who do good"),
        (16, 90, 90, "إن الله يأمر بالعدل والإحسان", "Allah commands justice and ihsan"),
        (17, 23, 23, "وبالوالدين إحسانا", "And to parents, good treatment"),
        (55, 60, 60, "هل جزاء الإحسان إلا الإحسان", "Is reward for good other than good"),
    ],
    "theme_adl": [
        (4, 58, 58, "إذا حكمتم بين الناس أن تحكموا بالعدل", "Judge with justice"),
        (4, 135, 135, "كونوا قوامين بالقسط", "Be persistently standing firm in justice"),
        (5, 8, 8, "كونوا قوامين لله شهداء بالقسط", "Be witnesses for Allah in justice"),
        (16, 90, 90, "إن الله يأمر بالعدل", "Allah commands justice"),
        (42, 15, 15, "وأمرت لأعدل بينكم", "Commanded to be just"),
        (49, 9, 9, "فأصلحوا بينهما بالعدل", "Make peace between them in justice"),
        (57, 25, 25, "ليقوم الناس بالقسط", "That people may maintain justice"),
    ],
    "theme_rahma": [
        (1, 1, 1, "الرحمن الرحيم", "The Most Gracious, Most Merciful"),
        (6, 12, 12, "كتب على نفسه الرحمة", "He has decreed mercy upon Himself"),
        (6, 54, 54, "كتب ربكم على نفسه الرحمة", "Your Lord has decreed mercy"),
        (7, 156, 156, "ورحمتي وسعت كل شيء", "My mercy encompasses all things"),
        (12, 64, 64, "فالله خير حافظا وهو أرحم الراحمين", "Allah is best guardian, most merciful"),
        (17, 24, 24, "رب ارحمهما", "Lord, have mercy on them"),
        (21, 107, 107, "رحمة للعالمين", "Mercy to the worlds"),
        (39, 53, 53, "لا تقنطوا من رحمة الله", "Do not despair of Allah's mercy"),
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

                # Check if segment exists
                exists = conn.execute(
                    text("SELECT 1 FROM theme_segments WHERE id = :id"),
                    {"id": segment_id}
                ).fetchone()

                if not exists:
                    # Generate summary from title
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

            # Update segment count
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
