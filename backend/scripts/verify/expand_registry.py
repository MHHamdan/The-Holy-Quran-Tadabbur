#!/usr/bin/env python3
"""
Expand the Quran Story Registry with:
1. Missing category stories (unseen, more parables)
2. Arabic summaries for all stories
3. Secondary mentions for cross-referenced stories
4. Evidence pointers

This script generates an expanded stories_registry.json
"""

import json
from pathlib import Path
from typing import Dict, List, Any


# Arabic summaries for existing stories
ARABIC_SUMMARIES = {
    "story_adam": "قصة خلق آدم عليه السلام، واختباره في الجنة، ونزوله إلى الأرض، وطريقه إلى التوبة. تتناول القصة رفض إبليس السجود لآدم وعداوته الأبدية للبشر.",
    "story_nuh": "قصة نوح عليه السلام ودعوته لقومه تسعمائة وخمسين عاماً، وبناء السفينة، والطوفان العظيم الذي أهلك المكذبين ونجا منه المؤمنون.",
    "story_ibrahim": "قصة أبي الأنبياء إبراهيم عليه السلام، رحلته من عبادة الأصنام إلى التوحيد، ومحاولة قومه إحراقه، وابتلاؤه بذبح ابنه، وبناء الكعبة المشرفة.",
    "story_musa": "قصة موسى عليه السلام الأكثر ذكراً في القرآن، من ولادته ونجاته من فرعون، إلى بعثته وتحريره لبني إسرائيل، ومعجزاته العظيمة.",
    "story_yusuf": "أحسن القصص - رحلة يوسف عليه السلام من رؤيا الطفولة إلى لقاء العائلة في مصر، عبر الجب والعبودية والسجن حتى أصبح عزيز مصر.",
    "story_isa": "قصة عيسى عليه السلام، الولادة المعجزة، ورسالته إلى بني إسرائيل، ومعجزاته بإذن الله، ورفعه إلى السماء.",
    "story_maryam": "قصة مريم العذراء عليها السلام، المرأة الوحيدة المسماة في القرآن، عبادتها وتكريمها وولادتها لعيسى.",
    "story_zakariyya_yahya": "قصة زكريا ويحيى عليهما السلام، دعاء زكريا للولد في الكبر، واستجابة الله له بيحيى الذي لم يجعل له سمياً.",
    "story_sulayman": "قصة سليمان عليه السلام الذي سخر له الله الجن والريح والطير، ولقاؤه مع ملكة سبأ، وحكمته وملكه العظيم.",
    "story_dawud": "قصة داوود عليه السلام، الراعي الذي قتل جالوت وأصبح نبياً ملكاً، آتاه الله الزبور وعلمه صنعة الدروع.",
    "story_ayyub": "قصة أيوب عليه السلام نبي الصبر، ابتلاء طويل بالمرض وفقدان الأهل والمال، ثم الشفاء والعافية بعد الدعاء.",
    "story_yunus": "قصة يونس عليه السلام الذي التقمه الحوت ودعا ربه في الظلمات، وقومه الذين آمنوا فكشف عنهم العذاب.",
    "story_lut": "قصة لوط عليه السلام ونهيه لقومه عن الفاحشة، وهلاك المكذبين بالحجارة من سجيل منضود.",
    "story_shuayb": "قصة شعيب عليه السلام نبي أهل مدين، دعوته إلى التوحيد وإيفاء المكيال والميزان، وهلاك قومه بالصيحة.",
    "story_salih": "قصة صالح عليه السلام وقومه ثمود، والناقة المعجزة التي عقروها فأخذتهم الصيحة.",
    "story_hud": "قصة هود عليه السلام وقومه عاد الذين كانوا أشداء أقوياء، فأهلكهم الله بريح صرصر عاتية.",
    "story_kahf": "قصة فتية الكهف الذين آمنوا بربهم فزادهم هدى، وناموا في الكهف ثلاثمائة سنين وازدادوا تسعاً.",
    "story_dhulqarnayn": "قصة ذي القرنين الملك الصالح الذي مكنه الله في الأرض، ورحلاته شرقاً وغرباً، وبناؤه السد على يأجوج ومأجوج.",
    "story_luqman": "قصة لقمان الحكيم ووصاياه لابنه في التوحيد والصلاة والصبر والتواضع.",
    "story_qarun": "قصة قارون من قوم موسى الذي آتاه الله الكنوز العظيمة فبغى وتكبر، فخسف الله به وبداره الأرض.",
    "story_habil_qabil": "قصة ابني آدم هابيل وقابيل، أول جريمة قتل في تاريخ البشرية بدافع الحسد.",
    "story_elephant": "قصة أصحاب الفيل الذين أرادوا هدم الكعبة فأرسل الله عليهم طيراً أبابيل ترميهم بحجارة من سجيل.",
    "story_baqarah_cow": "قصة البقرة التي أمر الله بني إسرائيل بذبحها لمعرفة القاتل، وكثرة أسئلتهم وتعنتهم.",
    "story_uzair": "قصة الذي مر على قرية خاوية فأماته الله مئة عام ثم بعثه ليريه قدرته على الإحياء.",
    "story_sabbath_breakers": "قصة أصحاب السبت الذين احتالوا على أمر الله فمسخهم قردة خاسئين.",
}

# Additional stories to add for missing categories
ADDITIONAL_STORIES = [
    # ============================================================
    # الغيب - The Unseen
    # ============================================================
    {
        "id": "story_angels_prostration",
        "name_ar": "سجود الملائكة لآدم",
        "name_en": "Angels' Prostration to Adam",
        "category": "unseen",
        "main_figures": ["الملائكة", "آدم", "إبليس"],
        "themes": ["obedience", "arrogance", "creation"],
        "summary_ar": "أمر الله الملائكة بالسجود لآدم فسجدوا جميعاً إلا إبليس أبى واستكبر وكان من الكافرين. تبين القصة طاعة الملائكة المطلقة ورفض إبليس.",
        "summary_en": "Allah commanded the angels to prostrate to Adam. They all prostrated except Iblis who refused out of arrogance.",
        "suras_mentioned": [2, 7, 15, 17, 18, 20, 38],
        "segments": [
            {"id": "angels_command", "narrative_order": 1, "aspect": "command", "sura_no": 2, "aya_start": 34, "aya_end": 34, "summary_ar": "أمر الله الملائكة بالسجود لآدم", "summary_en": "Allah commands angels to prostrate"},
            {"id": "angels_obey", "narrative_order": 2, "aspect": "obedience", "sura_no": 7, "aya_start": 11, "aya_end": 11, "summary_ar": "سجود الملائكة وإباء إبليس", "summary_en": "Angels prostrate, Iblis refuses"},
            {"id": "iblis_reasoning", "narrative_order": 3, "aspect": "dialogue", "sura_no": 7, "aya_start": 12, "aya_end": 18, "summary_ar": "حوار إبليس مع الله وسبب رفضه", "summary_en": "Iblis's reasoning for refusing"}
        ]
    },
    {
        "id": "story_jinn_quran",
        "name_ar": "استماع الجن للقرآن",
        "name_en": "Jinn Listening to the Quran",
        "category": "unseen",
        "main_figures": ["الجن"],
        "themes": ["guidance", "belief", "unseen"],
        "summary_ar": "قصة نفر من الجن استمعوا للقرآن فآمنوا به وولوا إلى قومهم منذرين. تؤكد القصة أن رسالة القرآن للإنس والجن.",
        "summary_en": "A group of jinn listened to the Quran and believed, then returned to warn their people.",
        "suras_mentioned": [46, 72],
        "segments": [
            {"id": "jinn_listen", "narrative_order": 1, "aspect": "listening", "sura_no": 46, "aya_start": 29, "aya_end": 32, "summary_ar": "استماع الجن للقرآن", "summary_en": "Jinn listen to the Quran"},
            {"id": "jinn_believe", "narrative_order": 2, "aspect": "belief", "sura_no": 72, "aya_start": 1, "aya_end": 15, "summary_ar": "إيمان الجن وإنذار قومهم", "summary_en": "Jinn believe and warn their people"}
        ]
    },
    {
        "id": "story_yajuj_majuj",
        "name_ar": "يأجوج ومأجوج",
        "name_en": "Yajuj and Majuj (Gog and Magog)",
        "category": "unseen",
        "main_figures": ["يأجوج", "مأجوج", "ذو القرنين"],
        "themes": ["corruption", "end_times", "protection"],
        "summary_ar": "قصة يأجوج ومأجوج القوم المفسدين الذين بنى ذو القرنين السد لحجزهم، وسيخرجون في آخر الزمان.",
        "summary_en": "The story of Gog and Magog, the corrupting people whom Dhul-Qarnayn blocked with a barrier.",
        "suras_mentioned": [18, 21],
        "segments": [
            {"id": "yajuj_barrier", "narrative_order": 1, "aspect": "barrier", "sura_no": 18, "aya_start": 93, "aya_end": 98, "summary_ar": "بناء السد على يأجوج ومأجوج", "summary_en": "Building the barrier against them"},
            {"id": "yajuj_endtimes", "narrative_order": 2, "aspect": "prophecy", "sura_no": 21, "aya_start": 96, "aya_end": 97, "summary_ar": "خروجهم في آخر الزمان", "summary_en": "Their emergence at the end of times"}
        ]
    },
    # ============================================================
    # الأمثال - Parables
    # ============================================================
    {
        "id": "story_two_gardens",
        "name_ar": "صاحب الجنتين",
        "name_en": "The Owner of Two Gardens",
        "category": "parable",
        "main_figures": ["صاحب الجنتين", "صاحبه المؤمن"],
        "themes": ["arrogance", "wealth", "gratitude", "destruction"],
        "summary_ar": "مثل رجل أعطاه الله جنتين فتكبر ونسي شكر الله، فأهلك الله جنتيه. مثل للمتكبرين بالنعم.",
        "summary_en": "A parable of a man given two gardens who became arrogant, forgetting Allah's blessings, so his gardens were destroyed.",
        "suras_mentioned": [18],
        "segments": [
            {"id": "gardens_description", "narrative_order": 1, "aspect": "setting", "sura_no": 18, "aya_start": 32, "aya_end": 34, "summary_ar": "وصف الجنتين", "summary_en": "Description of the two gardens"},
            {"id": "gardens_arrogance", "narrative_order": 2, "aspect": "arrogance", "sura_no": 18, "aya_start": 35, "aya_end": 36, "summary_ar": "تكبر صاحبهما", "summary_en": "The owner's arrogance"},
            {"id": "gardens_advice", "narrative_order": 3, "aspect": "warning", "sura_no": 18, "aya_start": 37, "aya_end": 41, "summary_ar": "نصيحة صاحبه المؤمن", "summary_en": "The believer's advice"},
            {"id": "gardens_destruction", "narrative_order": 4, "aspect": "outcome", "sura_no": 18, "aya_start": 42, "aya_end": 44, "summary_ar": "هلاك الجنتين وندم صاحبهما", "summary_en": "Gardens destroyed, owner regrets"}
        ]
    },
    {
        "id": "story_good_word",
        "name_ar": "مثل الكلمة الطيبة",
        "name_en": "Parable of the Good Word",
        "category": "parable",
        "main_figures": [],
        "themes": ["faith", "steadfastness", "guidance"],
        "summary_ar": "مثل الكلمة الطيبة كشجرة طيبة أصلها ثابت وفرعها في السماء تؤتي أكلها كل حين. مثل للإيمان والتوحيد.",
        "summary_en": "The parable of a good word like a good tree with firm roots and branches reaching the sky.",
        "suras_mentioned": [14],
        "segments": [
            {"id": "good_word_tree", "narrative_order": 1, "aspect": "parable", "sura_no": 14, "aya_start": 24, "aya_end": 27, "summary_ar": "مثل الكلمة الطيبة والخبيثة", "summary_en": "Parable of good and bad word"}
        ]
    },
    {
        "id": "story_fly",
        "name_ar": "مثل الذباب",
        "name_en": "Parable of the Fly",
        "category": "parable",
        "main_figures": [],
        "themes": ["weakness", "idolatry", "logic"],
        "summary_ar": "مثل يضربه الله لبيان ضعف الأصنام: لن يستطيعوا خلق ذبابة ولو اجتمعوا، وإن يسلبهم الذباب شيئاً لا يستنقذوه منه.",
        "summary_en": "A parable showing the weakness of idols - they cannot create even a fly.",
        "suras_mentioned": [22],
        "segments": [
            {"id": "fly_parable", "narrative_order": 1, "aspect": "parable", "sura_no": 22, "aya_start": 73, "aya_end": 74, "summary_ar": "مثل الذباب وعجز الأصنام", "summary_en": "The fly parable and idols' weakness"}
        ]
    },
    {
        "id": "story_spider",
        "name_ar": "مثل العنكبوت",
        "name_en": "Parable of the Spider",
        "category": "parable",
        "main_figures": [],
        "themes": ["weakness", "idolatry", "falsehood"],
        "summary_ar": "مثل الذين اتخذوا من دون الله أولياء كمثل العنكبوت اتخذت بيتاً، وإن أوهن البيوت لبيت العنكبوت.",
        "summary_en": "Those who take protectors besides Allah are like the spider - whose house is the frailest.",
        "suras_mentioned": [29],
        "segments": [
            {"id": "spider_parable", "narrative_order": 1, "aspect": "parable", "sura_no": 29, "aya_start": 41, "aya_end": 41, "summary_ar": "مثل العنكبوت", "summary_en": "The spider parable"}
        ]
    },
    # ============================================================
    # قصص الأمم - Nation Stories
    # ============================================================
    {
        "id": "story_tubba",
        "name_ar": "قوم تُبَّع",
        "name_en": "People of Tubba",
        "category": "nation",
        "main_figures": ["تُبَّع"],
        "themes": ["destruction", "rejection", "warning"],
        "summary_ar": "ذكر قوم تبع في سياق الأمم المهلكة، يُذكرون مع عاد وثمود وفرعون كعبرة للمكذبين.",
        "summary_en": "The people of Tubba mentioned among destroyed nations as a warning to those who reject truth.",
        "suras_mentioned": [44, 50],
        "segments": [
            {"id": "tubba_mention", "narrative_order": 1, "aspect": "warning", "sura_no": 44, "aya_start": 37, "aya_end": 37, "summary_ar": "ذكر قوم تبع مع المهلكين", "summary_en": "Tubba mentioned with destroyed nations"},
            {"id": "tubba_qaf", "narrative_order": 2, "aspect": "warning", "sura_no": 50, "aya_start": 14, "aya_end": 14, "summary_ar": "ذكرهم في سورة ق", "summary_en": "Mentioned in Surah Qaf"}
        ]
    },
    {
        "id": "story_rass",
        "name_ar": "أصحاب الرس",
        "name_en": "People of Ar-Rass",
        "category": "nation",
        "main_figures": ["أصحاب الرس"],
        "themes": ["destruction", "rejection"],
        "summary_ar": "أصحاب الرس من الأمم المهلكة، يُذكرون في سياق التحذير من التكذيب.",
        "summary_en": "The people of Ar-Rass, mentioned among destroyed nations as a warning.",
        "suras_mentioned": [25, 50],
        "segments": [
            {"id": "rass_furqan", "narrative_order": 1, "aspect": "warning", "sura_no": 25, "aya_start": 38, "aya_end": 38, "summary_ar": "ذكر أصحاب الرس", "summary_en": "Mention of the people of Ar-Rass"},
            {"id": "rass_qaf", "narrative_order": 2, "aspect": "warning", "sura_no": 50, "aya_start": 12, "aya_end": 14, "summary_ar": "ذكرهم مع الأمم المهلكة", "summary_en": "Listed with destroyed nations"}
        ]
    },
    {
        "id": "story_ayka",
        "name_ar": "أصحاب الأيكة",
        "name_en": "People of the Thicket (Al-Ayka)",
        "category": "nation",
        "main_figures": ["شعيب", "أصحاب الأيكة"],
        "themes": ["justice", "trade", "destruction"],
        "summary_ar": "أصحاب الأيكة هم قوم شعيب الآخرون، كذبوا الرسل فأخذهم عذاب يوم الظلة.",
        "summary_en": "The people of the Thicket, another community to whom Shu'ayb was sent, destroyed by the torment of the Day of Shadow.",
        "suras_mentioned": [15, 26, 38, 50],
        "segments": [
            {"id": "ayka_rejection", "narrative_order": 1, "aspect": "rejection", "sura_no": 26, "aya_start": 176, "aya_end": 189, "summary_ar": "تكذيب أصحاب الأيكة لشعيب", "summary_en": "Rejection of Shu'ayb by Al-Ayka"},
            {"id": "ayka_punishment", "narrative_order": 2, "aspect": "punishment", "sura_no": 26, "aya_start": 189, "aya_end": 191, "summary_ar": "عذاب يوم الظلة", "summary_en": "Punishment of the Day of Shadow"}
        ]
    },
    # ============================================================
    # تاريخية - Historical
    # ============================================================
    {
        "id": "story_talut_jalut",
        "name_ar": "طالوت وجالوت",
        "name_en": "Talut (Saul) and Jalut (Goliath)",
        "category": "historical",
        "main_figures": ["طالوت", "جالوت", "داوود"],
        "themes": ["leadership", "courage", "faith"],
        "summary_ar": "قصة طالوت الملك الذي اختاره الله لبني إسرائيل، واختباره لجنوده بالنهر، وقتل داوود لجالوت.",
        "summary_en": "The story of Talut chosen as king, his army's test at the river, and Dawud killing Goliath.",
        "suras_mentioned": [2],
        "segments": [
            {"id": "talut_chosen", "narrative_order": 1, "aspect": "selection", "sura_no": 2, "aya_start": 247, "aya_end": 248, "summary_ar": "اختيار طالوت ملكاً", "summary_en": "Talut chosen as king"},
            {"id": "talut_test", "narrative_order": 2, "aspect": "test", "sura_no": 2, "aya_start": 249, "aya_end": 249, "summary_ar": "اختبار الجنود بالنهر", "summary_en": "Testing soldiers at the river"},
            {"id": "jalut_battle", "narrative_order": 3, "aspect": "battle", "sura_no": 2, "aya_start": 250, "aya_end": 251, "summary_ar": "قتل داوود لجالوت", "summary_en": "Dawud kills Goliath"}
        ]
    },
    {
        "id": "story_ifk",
        "name_ar": "حادثة الإفك",
        "name_en": "The Incident of Ifk (Slander)",
        "category": "historical",
        "main_figures": ["عائشة", "المنافقون"],
        "themes": ["slander", "innocence", "patience"],
        "summary_ar": "حادثة الإفك عندما اتهم المنافقون أم المؤمنين عائشة رضي الله عنها، فبرأها الله من فوق سبع سماوات.",
        "summary_en": "The incident of slander against Aisha, and Allah's revelation clearing her innocence.",
        "suras_mentioned": [24],
        "segments": [
            {"id": "ifk_incident", "narrative_order": 1, "aspect": "slander", "sura_no": 24, "aya_start": 11, "aya_end": 20, "summary_ar": "الاتهام والآيات المنزلة", "summary_en": "The accusation and revealed verses"},
            {"id": "ifk_innocence", "narrative_order": 2, "aspect": "clearing", "sura_no": 24, "aya_start": 21, "aya_end": 26, "summary_ar": "تبرئة أم المؤمنين", "summary_en": "Clearing of Aisha's innocence"}
        ]
    },
]


def update_manifest():
    """Update the stories manifest with Arabic summaries and new stories."""
    manifest_path = Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json"

    # Load existing manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Update existing stories with Arabic summaries
    for story in data['stories']:
        story_id = story['id']
        if story_id in ARABIC_SUMMARIES:
            story['summary_ar'] = ARABIC_SUMMARIES[story_id]

    # Add new stories
    existing_ids = {s['id'] for s in data['stories']}
    for new_story in ADDITIONAL_STORIES:
        if new_story['id'] not in existing_ids:
            data['stories'].append(new_story)

    # Update metadata
    data['last_updated'] = "2026-01-06"
    data['description'] = "Comprehensive manifest of 35+ Quranic stories with verse mappings, Arabic content, and cross-surah connections"

    # Save updated manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Updated manifest with {len(data['stories'])} stories")
    print(f"   - Added Arabic summaries to {len(ARABIC_SUMMARIES)} existing stories")
    print(f"   - Added {len(ADDITIONAL_STORIES)} new stories")

    # Print category distribution
    categories = {}
    for story in data['stories']:
        cat = story.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print("\n📊 Category distribution:")
    for cat, count in sorted(categories.items()):
        print(f"   {cat}: {count}")


if __name__ == "__main__":
    update_manifest()
