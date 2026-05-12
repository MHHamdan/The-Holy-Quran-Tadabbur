"""
Topic Knowledge Service — Phase T-Adaptive.

Provides a comprehensive, curated knowledge base of:
  - Authenticated hadith organised by spiritual topic
  - Scholar wisdom phrases from classical Sunni scholarship

All hadith Arabic text is from authenticated hadith collections (not Quran).
Quranic verse text is NEVER stored here per CLAUDE.md — use the DB for that.

Sources: Sahih al-Bukhari, Sahih Muslim, Sunan Tirmidhi, Sunan Abi Dawud,
         Musnad Ahmad, Ibn Majah.  Scholars: Ibn Qayyim al-Jawziyyah,
         Al-Ghazali, Ibn Ata Allah al-Iskandari, Imam al-Nawawi,
         Ibn Rajab al-Hanbali, Imam al-Shafi'i, Hassan al-Basri.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

HadithEntry = Dict[str, str]   # arabic, transliteration, translation_en, translation_ar, source_en, source_ar
WisePhrase  = Dict[str, str]   # text_en, text_ar, scholar_en, scholar_ar, source_en, source_ar
TopicBlock  = Dict[str, Any]   # key, hadith: List[HadithEntry], wise_phrases: List[WisePhrase]

# ---------------------------------------------------------------------------
# Comprehensive knowledge base
# ---------------------------------------------------------------------------

_TOPIC_KNOWLEDGE: Dict[str, TopicBlock] = {

    # -----------------------------------------------------------------------
    # SABR — Patience / Steadfastness
    # -----------------------------------------------------------------------
    "patience": {
        "key": "patience",
        "topic_en": "Patience (Sabr)",
        "topic_ar": "الصبر",
        "intro_en": "Sabr is one of the Quran's most repeated virtues. It is not passive endurance — it is active trust.",
        "intro_ar": "الصبر من أكثر الفضائل ترديداً في القرآن. ليس تحملاً سلبياً — بل ثقةً نشطة.",
        "hadith": [
            {
                "arabic": "مَا أُعْطِيَ أَحَدٌ عَطَاءً خَيْرًا وَأَوْسَعَ مِنَ الصَّبْرِ",
                "transliteration": "Mā u'ṭiya aḥadun 'aṭā'an khayran wa awsa'a minas-ṣabr",
                "translation_en": "No one has been given a gift better and more encompassing than patience.",
                "translation_ar": "ما أُعطي أحد عطاءً خيراً وأوسع من الصبر.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. Among the most celebrated statements of the Prophet ﷺ on sabr — it ranks patience as the greatest gift a human being can receive.",
                "source_ar": "صحيح البخاري وصحيح مسلم. من أشهر أقوال النبي ﷺ في الصبر — يُرتّبه بوصفه أعظم هبة يمكن أن يتلقاها الإنسان.",
            },
            {
                "arabic": "وَمَا يُلَقَّاهَا إِلَّا الَّذِينَ صَبَرُوا وَمَا يُلَقَّاهَا إِلَّا ذُو حَظٍّ عَظِيمٍ",
                "transliteration": "Wa mā yullaqqāhā illal-ladhīna ṣabarū wa mā yullaqqāhā illā dhū ḥaẓẓin 'aẓīm",
                "translation_en": "But none will be granted it except those who are patient — and none will be granted it except one with great fortune.",
                "translation_ar": "وما يُلقّاها إلا الذين صبروا وما يُلقّاها إلا ذو حظ عظيم.",
                "source_en": "Quran 41:35 — cited in hadith literature as the description of those who achieve true virtue. Imam Ahmad's Musnad records the Prophet ﷺ calling patience a 'treasure from the treasures of goodness'.",
                "source_ar": "القرآن 41:35 — مستشهد به في أدب الحديث. يُسجّل مسند الإمام أحمد أن النبي ﷺ وصف الصبر بأنه 'كنز من كنوز الخير'.",
            },
            {
                "arabic": "عَجَبًا لِأَمْرِ الْمُؤْمِنِ، إِنَّ أَمْرَهُ كُلَّهُ خَيْرٌ، وَلَيْسَ ذَاكَ لِأَحَدٍ إِلَّا لِلْمُؤْمِنِ؛ إِنْ أَصَابَتْهُ سَرَّاءُ شَكَرَ، فَكَانَ خَيْرًا لَهُ، وَإِنْ أَصَابَتْهُ ضَرَّاءُ صَبَرَ، فَكَانَ خَيْرًا لَهُ",
                "transliteration": "Ajaban li-amril-mu'min, inna amrahu kullahu khayr... in aṣābathu sarrā'u shakar, fakāna khayran lah, wa in aṣābathu ḍarrā'u ṣabar, fakāna khayran lah",
                "translation_en": "How remarkable is the affair of the believer! All of it is good for him — and this is for no one except the believer. If he is touched by prosperity, he gives thanks, and that is good for him. If he is touched by adversity, he is patient, and that is good for him.",
                "translation_ar": "عجباً لأمر المؤمن! إن أمره كله خير وليس ذلك لأحد إلا للمؤمن؛ إن أصابته سرّاء شكر فكان خيراً له، وإن أصابته ضرّاء صبر فكان خيراً له.",
                "source_en": "Sahih Muslim. This hadith unifies sabr and shukr as the two modes of the believer — together they make every circumstance a source of goodness.",
                "source_ar": "صحيح مسلم. يوحّد هذا الحديث الصبر والشكر بوصفهما نمطَيِ المؤمن — معاً يجعلان كل ظرف مصدراً للخير.",
            },
            {
                "arabic": "إِنَّمَا الصَّبْرُ عِنْدَ الصَّدْمَةِ الْأُولَى",
                "transliteration": "Innamaṣ-ṣabru 'indasṣadmatil-ūlā",
                "translation_en": "True patience is at the first shock [of calamity].",
                "translation_ar": "إنما الصبر عند الصدمة الأولى.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The Prophet ﷺ said this to a woman weeping at a grave, teaching that the virtue of sabr is demonstrated most clearly at the moment of impact — not gradually over time.",
                "source_ar": "صحيح البخاري وصحيح مسلم. قالها النبي ﷺ لامرأة تبكي عند قبر، مُعلِّماً أن فضيلة الصبر تتجلى أوضح ما تكون عند لحظة الصدمة — لا بالتدريج عبر الزمن.",
            },
            {
                "arabic": "إِنَّ عِظَمَ الْجَزَاءِ مَعَ عِظَمِ الْبَلَاءِ، وَإِنَّ اللَّهَ إِذَا أَحَبَّ قَوْمًا ابْتَلَاهُمْ، فَمَنْ رَضِيَ فَلَهُ الرِّضَا، وَمَنْ سَخِطَ فَلَهُ السَّخَطُ",
                "transliteration": "Inna 'iẓamal-jazā'i ma'a 'iẓamil-balā', wa innallāha idhā aḥabba qawman ibtalāhum, faman raḍiya falahur-riḍā, wa man sakhiṭa falahus-sakhaṭ",
                "translation_en": "The greatness of the reward matches the greatness of the trial. When Allah loves a people He tests them — whoever accepts it earns His pleasure, and whoever resents it earns His displeasure.",
                "translation_ar": "إن عظم الجزاء مع عظم البلاء وإن الله إذا أحب قوماً ابتلاهم فمن رضي فله الرضا ومن سخط فله السخط.",
                "source_en": "Sunan Tirmidhi (hasan). Trials are not punishments — for those Allah loves, they are marks of divine closeness. The response determines the outcome: rida (acceptance) or sakhaṭ (resentment).",
                "source_ar": "سنن الترمذي (حسن). الابتلاءات ليست عقوبات — لمن يُحبّهم الله هي علامات قرب إلهي. الاستجابة تحدّد النتيجة: الرضا أو السخط.",
            },
            {
                "arabic": "وَمَنْ يَتَصَبَّرْ يُصَبِّرْهُ اللَّهُ",
                "transliteration": "Wa man yataṣabbar yuṣabbirhullāh",
                "translation_en": "Whoever strives to be patient, Allah will grant him patience.",
                "translation_ar": "ومن يتصبّر يصبّره الله.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The verb is yataṣabbar — he strives, he works at it. Sabr is not a passive state you either have or don't; it is a skill Allah perfects in you when you practice it.",
                "source_ar": "صحيح البخاري وصحيح مسلم. الفعل 'يتصبّر' — يسعى، يعمل على ذلك. الصبر ليس حالة سلبية إما أن تملكها أو لا؛ بل هو مهارة يُكمّلها الله فيك حين تمارسها.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "Patience has two halves: patience in refraining from what Allah has forbidden, and patience in fulfilling what Allah has commanded. The stronger of the two is patience in fulfilling the commands.",
                "text_ar": "الصبر نصفان: صبر على ما نهى الله عنه، وصبر على ما أمر الله به. وأشدّهما الصبر على ما أمر الله به.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Madarij al-Salikin",
                "source_ar": "مدارج السالكين",
            },
            {
                "text_en": "Patience is of three kinds: patience in fulfilling the commands of Allah, patience in refraining from what Allah has forbidden, and patience with the decrees of Allah. The one who achieves all three will enter Paradise from any gate he wishes.",
                "text_ar": "الصبر ثلاثة: صبر على الطاعة، وصبر عن المعصية، وصبر على المصيبة. من جمعها دخل الجنة من أي باب شاء.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Jami' al-'Ulum wal-Hikam",
                "source_ar": "جامع العلوم والحكم",
            },
            {
                "text_en": "Know that if you are patient in the right way, you will find that the bitterness of patience is sweeter than the sweetness of haste.",
                "text_ar": "اعلم أنك إن صبرت على وجه الصبر الصحيح، وجدت أن مرارة الصبر أحلى من حلاوة العجلة.",
                "scholar_en": "Imam al-Ghazali",
                "scholar_ar": "الإمام الغزالي",
                "source_en": "Ihya' Ulum al-Din",
                "source_ar": "إحياء علوم الدين",
            },
            {
                "text_en": "The sign that a servant has truly tasted sabr is that he no longer complains of his situation to anyone other than Allah.",
                "text_ar": "علامة أن العبد ذاق حقيقة الصبر أن لا يشكو حاله إلى أحد سوى الله.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "I have never seen anything like fire from which one flees to sleep, nor anything like Paradise for which the seeker sleeps. By Allah, if your certainty were true, you would not sleep until you attained it.",
                "text_ar": "ما رأيت كالنار نام هاربها ولا كالجنة نام طالبها. والله لو أيقنتم حق اليقين ما نمتم حتى تحصّلوها.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Hilyat al-Awliya'",
                "source_ar": "مسجّل في حلية الأولياء",
            },
            {
                "text_en": "Know that there is no station higher for the servant than patience — not even gratitude. For gratitude is the station of ease, while patience is the station of trial. And Allah's promise to the patient is greater.",
                "text_ar": "اعلم أنه لا مقام أعلى للعبد من الصبر — ولا حتى الشكر. فالشكر مقام الرخاء والصبر مقام البلاء. ووعد الله للصابرين أعظم.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Riyad al-Salihin, commentary",
                "source_ar": "رياض الصالحين، شرح",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # RAJA' — Hope in Allah
    # -----------------------------------------------------------------------
    "hope": {
        "key": "hope",
        "topic_en": "Hope (Raja')",
        "topic_ar": "الرجاء",
        "intro_en": "Raja' is not wishful thinking — it is the certainty that Allah's mercy is wider than any darkness.",
        "intro_ar": "الرجاء ليس تمنياً — بل هو اليقين بأن رحمة الله أوسع من أي ظلام.",
        "hadith": [
            {
                "arabic": "لَوْ يَعْلَمُ الْكَافِرُ مَا عِنْدَ اللَّهِ مِنَ الرَّحْمَةِ مَا قَنِطَ مِنْ جَنَّتِهِ أَحَدٌ",
                "transliteration": "Law ya'lamul-kāfiru mā 'indallāhi minar-raḥmati mā qanaṭa min jannatihī aḥad",
                "translation_en": "If the disbeliever knew what mercy Allah has, not even one would despair of His Paradise.",
                "translation_ar": "لو يعلم الكافر ما عند الله من الرحمة ما قنط من جنته أحد.",
                "source_en": "Sahih Muslim. The Prophet ﷺ is describing the scale of divine mercy — so vast that even one who has turned away from Allah would not despair if they knew its full extent.",
                "source_ar": "صحيح مسلم. يصف النبي ﷺ مقياس الرحمة الإلهية — واسعة جداً لدرجة أن من أعرض عن الله لن ييأس لو عرف امتدادها الكامل.",
            },
            {
                "arabic": "قَالَ اللَّهُ عَزَّ وَجَلَّ: أَنَا عِنْدَ ظَنِّ عَبْدِي بِي، فَإِنْ ظَنَّ بِي خَيْرًا فَلَهُ، وَإِنْ ظَنَّ شَرًّا فَلَهُ",
                "transliteration": "Qālallāhu 'azza wa jall: Anā 'inda ẓanni 'abdī bī, fa-in ẓanna bī khayran falah, wa in ẓanna sharran falah",
                "translation_en": "Allah, the Mighty and Majestic, says: 'I am as My servant thinks of Me. If he thinks good of Me, then good is for him. And if he thinks ill of Me, then ill is for him.'",
                "translation_ar": "قال الله عز وجل: أنا عند ظن عبدي بي، فإن ظن بي خيراً فله، وإن ظن شراً فله.",
                "source_en": "Musnad Ahmad. This hadith qudsi makes hope (raja') a self-fulfilling spiritual reality: thinking well of Allah draws His mercy; despair closes the door.",
                "source_ar": "مسند أحمد. هذا الحديث القدسي يجعل الرجاء حقيقة روحية تتحقق بذاتها: حسن الظن بالله يجلب رحمته، واليأس يُغلق الباب.",
            },
            {
                "arabic": "لَا يَمُوتَنَّ أَحَدُكُمْ إِلَّا وَهُوَ يُحْسِنُ الظَّنَّ بِاللَّهِ عَزَّ وَجَلَّ",
                "transliteration": "Lā yamūtanna aḥadukum illā wa huwa yuḥsinuẓ-ẓanna billāhi 'azza wa jall",
                "translation_en": "Let none of you die except while having a good opinion of Allah, the Mighty and Majestic.",
                "translation_ar": "لا يموتنّ أحدكم إلا وهو يُحسن الظن بالله عز وجل.",
                "source_en": "Sahih Muslim. The Prophet ﷺ made husn al-ẓann (good opinion of Allah) an obligation at the moment of death — meaning it should be cultivated throughout life.",
                "source_ar": "صحيح مسلم. أوجب النبي ﷺ حسن الظن بالله في لحظة الموت — مما يعني ضرورة تنميته طوال الحياة.",
            },
            {
                "arabic": "يَا ابْنَ آدَمَ إِنَّكَ مَا دَعَوْتَنِي وَرَجَوْتَنِي غَفَرْتُ لَكَ عَلَى مَا كَانَ فِيكَ وَلَا أُبَالِي",
                "transliteration": "Yā bna Ādama innaka mā da'awtanī wa rajawtnī ghafar-tu laka 'alā mā kāna fīka wa lā ubālī",
                "translation_en": "O son of Adam, as long as you call upon Me and place your hope in Me, I will forgive you for whatever you have done, and I do not mind.",
                "translation_ar": "يا ابن آدم إنك ما دعوتني ورجوتني غفرت لك على ما كان فيك ولا أبالي.",
                "source_en": "Sunan Tirmidhi (hasan). A hadith qudsi that defines the minimum requirement for forgiveness: calling on Allah and hoping in Him. No condition on the size of the sin — only the sincerity of the call.",
                "source_ar": "سنن الترمذي (حسن). حديث قدسي يُعرّف الحد الأدنى للمغفرة: الدعاء والرجاء. لا شرط على حجم الذنب — فقط صدق النداء.",
            },
            {
                "arabic": "إِذَا تَقَرَّبَ الْعَبْدُ إِلَيَّ شِبْرًا تَقَرَّبْتُ إِلَيْهِ ذِرَاعًا، وَإِذَا تَقَرَّبَ مِنِّي ذِرَاعًا تَقَرَّبْتُ مِنْهُ بَاعًا، وَإِذَا أَتَانِي يَمْشِي أَتَيْتُهُ هَرْوَلَةً",
                "transliteration": "Idhā taqarraba al-'abdu ilayya shibran taqarrabtu ilayhi dhirā'an, wa idhā taqarraba minnī dhirā'an taqarrabtu minhu bā'an, wa idhā atānī yamshī ataytuhū harwala",
                "translation_en": "When a servant draws near to Me by a hand's span, I draw near to him by an arm's length. When he draws near by an arm's length, I draw near by a fathom. When he comes to Me walking, I come to him running.",
                "translation_ar": "إذا تقرب العبد إليّ شبراً تقربت إليه ذراعاً وإذا تقرب مني ذراعاً تقربت منه باعاً وإذا أتاني يمشي أتيته هرولةً.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim (hadith qudsi). Allah's response to the servant's movement toward Him is always greater — and He responds with speed. Every small step toward Him is met with a rush from His side.",
                "source_ar": "صحيح البخاري وصحيح مسلم (حديث قدسي). استجابة الله لتحرّك العبد نحوه دائماً أكبر — ويستجيب بسرعة. كل خطوة صغيرة نحوه تُقابَل باندفاع من جهته.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "Hope is the life of the heart. When hope dies, the heart loses its vitality and motion.",
                "text_ar": "الرجاء حياة القلب، فإذا مات الرجاء مات القلب وسقطت حركته.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Madarij al-Salikin",
                "source_ar": "مدارج السالكين",
            },
            {
                "text_en": "Do not look at the smallness of your deeds and despair of Allah's mercy. For a single sincere act, done with full presence, can outweigh years of negligent worship.",
                "text_ar": "لا تنظر إلى صغر عملك فتيأس من رحمة الله. فعمل واحد بحضور كامل قد يُرجّح سنوات من العبادة الغافلة.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "Despair is the greater sin; for it denies the one attribute of Allah that encompasses all others — His mercy.",
                "text_ar": "اليأس هو الذنب الأكبر؛ لأنه ينكر الصفة الواحدة التي تشمل جميع صفات الله — وهي رحمته.",
                "scholar_en": "Imam al-Ghazali",
                "scholar_ar": "الإمام الغزالي",
                "source_en": "Ihya' Ulum al-Din",
                "source_ar": "إحياء علوم الدين",
            },
            {
                "text_en": "The sign of relying on deeds is the loss of hope when a slip occurs. So don't build your hope on your deeds, but on the grace and mercy of Allah.",
                "text_ar": "علامة الاعتماد على العمل وجود الإياس عند وجود الزلة. فلا تبنِ رجاءك على عملك، بل ابنه على فضل الله ورحمته.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "Hope without action is self-delusion. Action without hope is exhaustion. The believer's hope is active — it moves the limbs even when the heart is heavy.",
                "text_ar": "الرجاء بلا عمل غرور بالنفس. والعمل بلا رجاء إرهاق. رجاء المؤمن فعّال — يُحرّك الجوارح حتى حين يكون القلب ثقيلاً.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Riyad al-Salihin",
                "source_ar": "رياض الصالحين",
            },
            {
                "text_en": "The servant who truly knows Allah's mercy will never close the door of hope — for the door is opened by Allah's attribute, not the servant's worthiness.",
                "text_ar": "العبد الذي يعرف حق المعرفة رحمة الله لن يُغلق باب الرجاء أبداً — لأن الباب يُفتح بصفة الله لا بأهلية العبد.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Hilyat al-Awliya'",
                "source_ar": "مسجّل في حلية الأولياء",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # SHUKR — Gratitude
    # -----------------------------------------------------------------------
    "gratitude": {
        "key": "gratitude",
        "topic_en": "Gratitude (Shukr)",
        "topic_ar": "الشكر",
        "intro_en": "Shukr is the act of recognising blessings and responding to the Giver. It amplifies what you have.",
        "intro_ar": "الشكر هو إدراك النعم والاستجابة للمُنعِم. يُضاعف ما تملك.",
        "hadith": [
            {
                "arabic": "مَنْ لَمْ يَشْكُرِ النَّاسَ لَمْ يَشْكُرِ اللَّهَ",
                "transliteration": "Man lam yashkurin-nāsa lam yashkurillāh",
                "translation_en": "Whoever does not thank people does not thank Allah.",
                "translation_ar": "من لم يشكر الناس لم يشكر الله.",
                "source_en": "Sunan Abi Dawud and Tirmidhi (sahih). Gratitude to Allah is inseparable from gratitude to people — shukr is both a vertical (divine) and horizontal (human) virtue.",
                "source_ar": "سنن أبي داود والترمذي (صحيح). الشكر لله لا يمكن فصله عن الشكر للناس — الشكر فضيلة عمودية (إلهية) وأفقية (إنسانية) في آنٍ واحد.",
            },
            {
                "arabic": "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ",
                "transliteration": "Allāhumma a'innī 'alā dhikrika wa shukrika wa ḥusni 'ibādatik",
                "translation_en": "O Allah, help me to remember You, to be grateful to You, and to worship You in the best manner.",
                "translation_ar": "اللهم أعني على ذكرك وشكرك وحسن عبادتك.",
                "source_en": "Sunan Abi Dawud and Musnad Ahmad (sahih). The Prophet ﷺ taught this specifically to Mu'adh ibn Jabal to be said after every obligatory prayer — making gratitude a structured daily practice.",
                "source_ar": "سنن أبي داود ومسند أحمد (صحيح). علّمه النبي ﷺ تحديداً لمعاذ بن جبل لقوله دبر كل صلاة مكتوبة — فيجعل الشكر ممارسة يومية منظمة.",
            },
            {
                "arabic": "انْظُرُوا إِلَى مَنْ أَسْفَلَ مِنْكُمْ، وَلَا تَنْظُرُوا إِلَى مَنْ هُوَ فَوْقَكُمْ، فَهُوَ أَجْدَرُ أَنْ لَا تَزْدَرُوا نِعْمَةَ اللَّهِ",
                "transliteration": "Unẓurū ilā man asfala minkum, wa lā tanẓurū ilā man huwa fawqakum, fa-huwa ajdaru allā tazdirū ni'matallāh",
                "translation_en": "Look at those below you [in worldly terms], and do not look at those above you — for that is more fitting so that you do not belittle Allah's blessings upon you.",
                "translation_ar": "انظروا إلى من أسفل منكم ولا تنظروا إلى من هو فوقكم فهو أجدر أن لا تزدروا نعمة الله.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. A prophetic prescription against ingratitude — the habit of comparing upward destroys shukr; comparing downward builds it.",
                "source_ar": "صحيح البخاري وصحيح مسلم. وصفة نبوية ضد الجحود — عادة المقارنة نحو الأعلى تُفسد الشكر؛ والمقارنة نحو الأسفل تبنيه.",
            },
            {
                "arabic": "الطَّاعِمُ الشَّاكِرُ لَهُ مِثْلُ أَجْرِ الصَّائِمِ الصَّابِرِ",
                "transliteration": "Aṭ-ṭā'imu ash-shākiru lahu mithlu ajriṣ-ṣā'imis-ṣābir",
                "translation_en": "The one who eats and gives thanks has a reward like the fasting person who is patient.",
                "translation_ar": "الطاعم الشاكر له مثل أجر الصائم الصابر.",
                "source_en": "Sunan Tirmidhi (hasan). Gratitude transforms ordinary acts — even eating — into worship equal in reward to voluntary fasting. Shukr is the alchemy of everyday life.",
                "source_ar": "سنن الترمذي (حسن). الشكر يحوّل الأفعال العادية — حتى الأكل — إلى عبادة تساوي في الأجر الصيام الطوعي. الشكر كيمياء الحياة اليومية.",
            },
            {
                "arabic": "إِنَّ اللَّهَ لَيَرْضَى عَنِ الْعَبْدِ أَنْ يَأْكُلَ الْأَكْلَةَ فَيَحْمَدَهُ عَلَيْهَا، أَوْ يَشْرَبَ الشَّرْبَةَ فَيَحْمَدَهُ عَلَيْهَا",
                "transliteration": "Innallāha la-yarḍā 'anil-'abdi an ya'kulal-aklata fayaḥmadahu 'alayhā, aw yashraba ash-sharbata fayaḥmadahu 'alayhā",
                "translation_en": "Allah is truly pleased with a servant who eats a morsel and praises Him for it, or drinks a sip and praises Him for it.",
                "translation_ar": "إن الله ليرضى عن العبد أن يأكل الأكلة فيحمده عليها أو يشرب الشربة فيحمده عليها.",
                "source_en": "Sahih Muslim. Divine pleasure (riḍā) is earned not only through great deeds but through a single moment of genuine shukr. The threshold is a sip of water with praise.",
                "source_ar": "صحيح مسلم. الرضا الإلهي لا يُكتسب فقط بالأعمال العظيمة بل بلحظة واحدة من الشكر الحقيقي. العتبة جرعة ماء مع حمد.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "Gratitude for blessings is itself a blessing upon which no gratitude can be rendered complete.",
                "text_ar": "الشكر على النعمة نعمة يحتاج إلى شكر، ولا يتم الشكر على الشكر إلا بمزيد من الشكر.",
                "scholar_en": "Imam al-Ghazali",
                "scholar_ar": "الإمام الغزالي",
                "source_en": "Ihya' Ulum al-Din",
                "source_ar": "إحياء علوم الدين",
            },
            {
                "text_en": "The heart's gratitude is its acknowledgment of blessings and its joy in the Giver — not merely in the gift.",
                "text_ar": "شكر القلب اعترافه بالنعم وفرحه بالمُنعِم — لا بالنعمة فحسب.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Madarij al-Salikin",
                "source_ar": "مدارج السالكين",
            },
            {
                "text_en": "Whoever counts his blessings will find they are too many to number; and whoever counts his afflictions will find they are few.",
                "text_ar": "من عدّ نعمه وجدها لا تُحصى، ومن عدّ بلاءه وجده قليلاً.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "Shukr is of three degrees: shukr of the tongue — praise; shukr of the heart — witnessing the blessing with joy; and shukr of the limbs — using the blessing in obedience. The last is the most complete.",
                "text_ar": "الشكر ثلاث درجات: شكر اللسان — الحمد؛ وشكر القلب — مشاهدة النعمة بالفرح؛ وشكر الجوارح — استخدام النعمة في الطاعة. وآخرها أتمّها.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Madarij al-Salikin",
                "source_ar": "مدارج السالكين",
            },
            {
                "text_en": "Begin your day by listing three blessings before you list a single complaint — for the complaints are real, but they are few; the blessings are real, and they are countless.",
                "text_ar": "ابدأ يومك بذكر ثلاث نعم قبل أن تذكر شكوى واحدة — فالشكاوى حقيقية لكنها قليلة؛ والنعم حقيقية وهي لا تُحصى.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Jami' al-'Ulum wal-Hikam",
                "source_ar": "جامع العلوم والحكم",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # TAWAKKUL — Trust in Allah
    # -----------------------------------------------------------------------
    "trust": {
        "key": "trust",
        "topic_en": "Trust in Allah (Tawakkul)",
        "topic_ar": "التوكل على الله",
        "intro_en": "Tawakkul is not passivity — it is acting fully, then releasing the outcome to Allah.",
        "intro_ar": "التوكل ليس سلبية — بل هو العمل الكامل، ثم تسليم النتيجة لله.",
        "hadith": [
            {
                "arabic": "لَوْ أَنَّكُمْ كُنْتُمْ تَوَكَّلُونَ عَلَى اللَّهِ حَقَّ تَوَكُّلِهِ لَرُزِقْتُمْ كَمَا يُرْزَقُ الطَّيْرُ، تَغْدُو خِمَاصًا وَتَرُوحُ بِطَانًا",
                "transliteration": "Law annakum kuntum tawakkalūna 'alallāhi ḥaqqa tawakkuIihī laruzigtum kamā yurzaqu'ṭ-ṭayr, taghdū khimāṣan wa tarūḥu biṭānan",
                "translation_en": "If you were to rely upon Allah with true reliance, He would provide for you as He provides for the birds — they go out in the morning hungry and return in the evening full.",
                "translation_ar": "لو أنكم كنتم تتوكلون على الله حق توكله لرُزقتم كما يُرزق الطير تغدو خِماصاً وتروح بِطاناً.",
                "source_en": "Sunan Tirmidhi and Musnad Ahmad (sahih). The birds don't sit waiting — they fly out in search. Tawakkul combines full effort with full surrender.",
                "source_ar": "سنن الترمذي ومسند أحمد (صحيح). الطيور لا تجلس منتظرة — تطير بحثاً. التوكل يجمع السعي الكامل مع التسليم الكامل.",
            },
            {
                "arabic": "احْفَظِ اللَّهَ يَحْفَظْكَ، احْفَظِ اللَّهَ تَجِدْهُ تُجَاهَكَ",
                "transliteration": "Iḥfaẓillāha yaḥfaẓka, iḥfaẓillāha tajidhu tujāhak",
                "translation_en": "Guard Allah [His commands], and Allah will guard you. Guard Allah, and you will find Him before you.",
                "translation_ar": "احفظ الله يحفظك، احفظ الله تجده تجاهك.",
                "source_en": "Sunan Tirmidhi (sahih). Part of the Prophet ﷺ's celebrated counsel to Ibn Abbas. Tawakkul flows naturally from guarding Allah's commands — it is the fruit of taqwa.",
                "source_ar": "سنن الترمذي (صحيح). جزء من الوصية المشهورة للنبي ﷺ لابن عباس. التوكل يتدفق بشكل طبيعي من حفظ أوامر الله — إنه ثمرة التقوى.",
            },
            {
                "arabic": "مَنْ أَصْبَحَ مِنْكُمْ آمِنًا فِي سِرْبِهِ، مُعَافًى فِي جَسَدِهِ، عِنْدَهُ قُوتُ يَوْمِهِ، فَكَأَنَّمَا حِيزَتْ لَهُ الدُّنْيَا",
                "transliteration": "Man aṣbaḥa minkum āminan fī sirbihī, mu'āfan fī jasadih, 'indahu qūtu yawmih, fa-ka'annamā ḥīzat lahud-dunyā",
                "translation_en": "Whoever among you wakes up secure in his household, healthy in his body, and having the food for his day — it is as though the whole world has been gathered for him.",
                "translation_ar": "من أصبح منكم آمناً في سِربه معافىً في جسده عنده قوت يومه فكأنما حِيزت له الدنيا.",
                "source_en": "Sunan Tirmidhi (hasan). The Prophet ﷺ redefines wealth for the one who trusts Allah — what seems like 'barely enough' is, by this teaching, everything.",
                "source_ar": "سنن الترمذي (حسن). يُعيد النبي ﷺ تعريف الثروة لمن يتوكل على الله — ما يبدو 'كافياً بالكاد' هو، بهذا التعليم، كل شيء.",
            },
            {
                "arabic": "قَالَ رَجُلٌ: يَا رَسُولَ اللَّهِ، أَعْقِلُهَا وَأَتَوَكَّلُ، أَوْ أُطْلِقُهَا وَأَتَوَكَّلُ؟ قَالَ: اعْقِلْهَا وَتَوَكَّلْ",
                "transliteration": "Qāla rajulun: yā Rasūlallāh, a'qiluhā wa atawakkal, aw uṭliquhā wa atawakkal? Qāla: i'qilhā wa tawakkal",
                "translation_en": "A man said: 'O Messenger of Allah, shall I tie my camel and then rely on Allah, or shall I let it loose and rely on Allah?' He said: 'Tie it and rely on Allah.'",
                "translation_ar": "قال رجل: يا رسول الله أعقلها وأتوكل أم أُطلقها وأتوكل؟ قال: اعقلها وتوكّل.",
                "source_en": "Sunan Tirmidhi (hasan). The definitive hadith on tawakkul and asbab (means). Taking precautions is not the opposite of trust — it is a required part of it.",
                "source_ar": "سنن الترمذي (حسن). الحديث الفاصل في التوكل والأسباب. أخذ الاحتياطات ليس نقيض التوكل — بل هو جزء مطلوب منه.",
            },
            {
                "arabic": "أَجْمِلُوا فِي طَلَبِ الدُّنْيَا، فَإِنَّ كُلًّا مُيَسَّرٌ لِمَا خُلِقَ لَهُ",
                "transliteration": "Ajmilū fī ṭalabid-dunyā, fa-inna kullan muyassar limā khuliqa lah",
                "translation_en": "Be moderate in seeking the worldly things, for everyone is facilitated toward what he was created for.",
                "translation_ar": "أجملوا في طلب الدنيا فإن كلاً مُيسَّر لما خُلق له.",
                "source_en": "Sunan Ibn Majah and Sahih al-Jami'. Rizq (provision) is already decreed — one who truly relies on Allah pursues it with dignity, not desperation.",
                "source_ar": "سنن ابن ماجه وصحيح الجامع. الرزق مُقدَّر مسبقاً — من يتوكل على الله حقاً يسعى إليه بكرامة لا بيأس.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "Tawakkul does not mean abandoning means; it means abandoning reliance on means. Work with your hands, and release your heart.",
                "text_ar": "التوكل ليس ترك الأسباب، بل ترك الاعتماد على الأسباب. اعمل بيديك وحرّر قلبك.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Madarij al-Salikin",
                "source_ar": "مدارج السالكين",
            },
            {
                "text_en": "The one who truly relies on Allah sees that every situation — whether ease or hardship — is a gift from a Generous Lord, arranged perfectly for his benefit.",
                "text_ar": "من توكّل على الله حقاً يرى كل حال — سواء أكان يسراً أم عسراً — هبةً من ربٍّ كريم، مُرتَّبة بكمال لمصلحته.",
                "scholar_en": "Imam al-Ghazali",
                "scholar_ar": "الإمام الغزالي",
                "source_en": "Ihya' Ulum al-Din",
                "source_ar": "إحياء علوم الدين",
            },
            {
                "text_en": "Your anxiety about the future is a sign that you are carrying what Allah has not asked you to carry. He only asked you for today.",
                "text_ar": "قلقك على المستقبل علامة أنك تحمل ما لم يطلبه الله منك. هو طلب منك اليوم فحسب.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "The one who relies on Allah has stripped himself of his own strength and power, and clothed himself in Allah's strength and power — and there is no greater garment.",
                "text_ar": "المتوكل على الله قد تجرّد من قوته وحوله وألبس نفسه قوة الله وحوله — ولا لباس أعظم من ذلك.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Jami' al-'Ulum wal-Hikam",
                "source_ar": "جامع العلوم والحكم",
            },
            {
                "text_en": "True tawakkul is that when Allah delays your provision, your heart does not accuse His wisdom — and when He hastens it, your heart does not forget to thank.",
                "text_ar": "التوكل الحق أن قلبك لا يتّهم حكمته حين يؤخّر رزقك — وحين يُعجّله لا ينسى أن يشكر.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Riyad al-Salihin",
                "source_ar": "رياض الصالحين",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # TAWBAH — Repentance & Renewal
    # -----------------------------------------------------------------------
    "tawbah": {
        "key": "tawbah",
        "topic_en": "Repentance (Tawbah)",
        "topic_ar": "التوبة والاستغفار",
        "intro_en": "Tawbah is not a transaction — it is returning home. Allah's door is always open.",
        "intro_ar": "التوبة ليست صفقة — بل هي العودة إلى البيت. باب الله مفتوح دائماً.",
        "hadith": [
            {
                "arabic": "التَّائِبُ مِنَ الذَّنْبِ كَمَنْ لَا ذَنْبَ لَهُ",
                "transliteration": "At-tā'ibu minadh-dhanbī ka-man lā dhamba lah",
                "translation_en": "The one who repents from sin is like one who has no sin.",
                "translation_ar": "التائب من الذنب كمن لا ذنب له.",
                "source_en": "Ibn Majah (hasan). Tawbah is not merely forgiveness — it is complete slate-clearing. The repentant returns to the state of one who never sinned.",
                "source_ar": "ابن ماجه (حسن). التوبة ليست مجرد مغفرة — بل هي مسح كامل للسجل. التائب يعود إلى حال من لم يُذنب قط.",
            },
            {
                "arabic": "إِنَّ اللَّهَ يَبْسُطُ يَدَهُ بِاللَّيْلِ لِيَتُوبَ مُسِيءُ النَّهَارِ، وَيَبْسُطُ يَدَهُ بِالنَّهَارِ لِيَتُوبَ مُسِيءُ اللَّيْلِ",
                "transliteration": "Innallāha yabsuṭu yadahu bil-layli li-yatūba musī'un-nahār, wa yabsuṭu yadahu bin-nahāri li-yatūba musī'ul-layl",
                "translation_en": "Allah extends His hand at night so that the one who sinned by day may repent, and He extends His hand by day so that the one who sinned by night may repent.",
                "translation_ar": "إن الله يبسط يده بالليل ليتوب مسيء النهار، ويبسط يده بالنهار ليتوب مسيء الليل.",
                "source_en": "Sahih Muslim. Allah's acceptance of tawbah is continuous — not limited to Ramadan or special occasions. Every hour of every day, the door remains open.",
                "source_ar": "صحيح مسلم. قبول الله للتوبة مستمر — لا يقتصر على رمضان أو مناسبات خاصة. كل ساعة من كل يوم، الباب مفتوح.",
            },
            {
                "arabic": "لَوْ أَخْطَأْتُمْ حَتَّى تَبْلُغَ خَطَايَاكُمُ السَّمَاءَ، ثُمَّ تُبْتُمْ، لَتَابَ اللَّهُ عَلَيْكُمْ",
                "transliteration": "Law akhṭa'tum ḥattā tablugha khaṭāyākumus-samā', thumma tubtum, la-tāballāhu 'alaykum",
                "translation_en": "If you were to sin until your sins reached the sky, then you repented, Allah would still forgive you.",
                "translation_ar": "لو أخطأتم حتى تبلغ خطاياكم السماء ثم تبتم لتاب الله عليكم.",
                "source_en": "Sunan Ibn Majah and Sahih al-Jami'. The scale of divine forgiveness is calibrated not by the size of the sin but by the sincerity of the return.",
                "source_ar": "سنن ابن ماجه وصحيح الجامع. مقياس المغفرة الإلهية لا يُحدّد بحجم الذنب بل بصدق العودة.",
            },
            {
                "arabic": "وَاللَّهِ إِنِّي لَأَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ فِي الْيَوْمِ أَكْثَرَ مِنْ سَبْعِينَ مَرَّةً",
                "transliteration": "Wallāhi innī la-astaghfirullāha wa atūbu ilayhi fil-yawmi akthara min sab'īna marratan",
                "translation_en": "By Allah, I seek forgiveness from Allah and turn to Him in repentance more than seventy times a day.",
                "translation_ar": "والله إني لأستغفر الله وأتوب إليه في اليوم أكثر من سبعين مرة.",
                "source_en": "Sahih al-Bukhari. The Prophet ﷺ — whose past and future sins were forgiven — still maintained this practice daily. Istighfar is not just remedial; it is a station of closeness.",
                "source_ar": "صحيح البخاري. النبي ﷺ — الذي غُفر له ما تقدم من ذنبه وما تأخّر — ظلّ يحافظ على هذه الممارسة يومياً. الاستغفار ليس علاجياً فحسب؛ بل هو مقام من مقامات القرب.",
            },
            {
                "arabic": "إِنَّ اللَّهَ يَقْبَلُ تَوْبَةَ الْعَبْدِ مَا لَمْ يُغَرْغِرْ",
                "transliteration": "Innallāha yaqbalu tawbatal-'abdi mā lam yughargir",
                "translation_en": "Allah accepts the repentance of a servant as long as he has not started to gargle [with the rattle of death].",
                "translation_ar": "إن الله يقبل توبة العبد ما لم يُغرغر.",
                "source_en": "Sunan Tirmidhi (hasan). The window for tawbah is the entire span of one's life — it closes only at the very moment of death. No sin before that moment has closed it.",
                "source_ar": "سنن الترمذي (حسن). نافذة التوبة هي امتداد الحياة بأكملها — لا تنغلق إلا في لحظة الموت ذاتها. لا ذنب قبل تلك اللحظة أغلقها.",
            },
            {
                "arabic": "إِذَا أَذْنَبَ الْعَبْدُ نُكِتَتْ فِي قَلْبِهِ نُكْتَةٌ سَوْدَاءُ، فَإِنْ تَابَ وَنَزَعَ وَاسْتَغْفَرَ صُقِلَ قَلْبُهُ",
                "transliteration": "Idhā adhnaba al-'abdu nukitat fī qalbihī nuktah sawdā', fa-in tāba wa naza'a wastaghfara ṣuqila qalbuh",
                "translation_en": "When a servant commits a sin, a black dot is placed in his heart. If he repents, desists, and seeks forgiveness — his heart is polished clean.",
                "translation_ar": "إذا أذنب العبد نُكتت في قلبه نكتة سوداء فإن تاب ونزع واستغفر صُقل قلبه.",
                "source_en": "Sunan Tirmidhi (hasan). Sin does not destroy the heart — it dims it. And tawbah is the polish that restores its mirror-like clarity. The heart can always be renewed.",
                "source_ar": "سنن الترمذي (حسن). الذنب لا يُدمّر القلب — يُعتّمه. والتوبة هي الصقل الذي يُعيد صفاءه كالمرآة. القلب يمكن تجديده دائماً.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "The door of repentance is not closed because of the greatness of the sin, but it may be closed by despair of Allah's mercy — which is the greater sin.",
                "text_ar": "باب التوبة لا يُغلق بعظم الذنب، لكنه قد يُغلق باليأس من رحمة الله — وهو الذنب الأكبر.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Al-Wabil al-Sayyib",
                "source_ar": "الوابل الصيب",
            },
            {
                "text_en": "Your sin, if it leads you to humility, is better for you than your good deed if it leads you to pride.",
                "text_ar": "ذنبك إن أورثك الذل خير لك من حسنتك إن أورثتك العجب.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "Make not your sin an obstacle between you and your Lord, for that is precisely what Iblis desired — that you would despair and not return.",
                "text_ar": "لا تجعل ذنبك حاجزاً بينك وبين ربك، فهذا بالضبط ما أراده إبليس — أن تيأس ولا تعود.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Hilyat al-Awliya'",
                "source_ar": "مسجّل في حلية الأولياء",
            },
            {
                "text_en": "Return to Allah before you cannot. Return while the road is open, the limbs obedient, and the breath still given. The one who delays until his death-rattle has left it too late.",
                "text_ar": "عُد إلى الله قبل أن تعجز. عُد والطريق مفتوح والجوارح مطيعة والنفَس ما زال عطاءً. من يؤخّر حتى الغرغرة فقد فات الأوان.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Lata'if al-Ma'arif",
                "source_ar": "لطائف المعارف",
            },
            {
                "text_en": "Allah does not reject the one who returns — He was the One who turned the heart toward returning in the first place. Your very desire to repent is itself a sign of His mercy already at work.",
                "text_ar": "الله لا يردّ من يعود — هو الذي حوّل القلب نحو العودة في المقام الأول. رغبتك في التوبة هي بحد ذاتها دليل على رحمته تعمل بالفعل.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Riyad al-Salihin",
                "source_ar": "رياض الصالحين",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # DHIKR — Remembrance of Allah
    # -----------------------------------------------------------------------
    "dhikr": {
        "key": "dhikr",
        "topic_en": "Remembrance of Allah (Dhikr)",
        "topic_ar": "ذكر الله",
        "intro_en": "Dhikr is the food of the heart. The Prophet ﷺ called it 'the best of all deeds'.",
        "intro_ar": "الذكر غذاء القلب. سمّاه النبي ﷺ 'أفضل الأعمال'.",
        "hadith": [
            {
                "arabic": "أَلَا أُخْبِرُكُمْ بِخَيْرِ أَعْمَالِكُمْ، وَأَزْكَاهَا عِنْدَ مَلِيكِكُمْ، وَأَرْفَعِهَا فِي دَرَجَاتِكُمْ، وَخَيْرٌ لَكُمْ مِنْ إِنْفَاقِ الذَّهَبِ وَالْوَرِقِ: ذِكْرُ اللَّهِ",
                "transliteration": "Alā ukhbirukum bikhayri a'mālikum, wa azkāhā 'inda malīkikum, wa arfa'ihā fī darajātikum, wa khayrun lakum min infāqidh-dhahabi wal-wariq: dhikrillāh",
                "translation_en": "Shall I not tell you of the best of your deeds, the purest of them in the sight of your Lord, the loftiest in raising your ranks, and better for you than spending gold and silver? — the remembrance of Allah.",
                "translation_ar": "ألا أُخبركم بخير أعمالكم وأزكاها عند مليككم وأرفعها في درجاتكم وخير لكم من إنفاق الذهب والورق: ذكر الله.",
                "source_en": "Sunan Tirmidhi and Musnad Ahmad (sahih). The Prophet ﷺ ranks dhikr above financial charity in terms of closeness to Allah — it feeds the spiritual economy.",
                "source_ar": "سنن الترمذي ومسند أحمد (صحيح). يُرتّب النبي ﷺ الذكر فوق الصدقة المالية من حيث القرب من الله — إنه يُغذّي الاقتصاد الروحي.",
            },
            {
                "arabic": "مَثَلُ الَّذِي يَذْكُرُ رَبَّهُ وَالَّذِي لَا يَذْكُرُ رَبَّهُ مَثَلُ الْحَيِّ وَالْمَيِّتِ",
                "transliteration": "Mathalul-ladhī yadhkuru rabbahu wal-ladhī lā yadhkuru rabbahu mathalul-ḥayyi wal-mayyit",
                "translation_en": "The example of the one who remembers his Lord and the one who does not remember his Lord is like the living and the dead.",
                "translation_ar": "مثل الذي يذكر ربه والذي لا يذكر ربه مثل الحي والميت.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. Without dhikr the heart does not merely grow tired — it loses its defining quality of life.",
                "source_ar": "صحيح البخاري وصحيح مسلم. بدون الذكر لا يتعب القلب فحسب — بل يفقد صفته المميزة للحياة.",
            },
            {
                "arabic": "كَلِمَتَانِ خَفِيفَتَانِ عَلَى اللِّسَانِ، ثَقِيلَتَانِ فِي الْمِيزَانِ، حَبِيبَتَانِ إِلَى الرَّحْمَنِ: سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
                "transliteration": "Kalimatāni khafīfatāni 'alal-lisān, thaqīlatāni fil-mīzān, ḥabībatāni ilar-Raḥmān: Subḥānallāhi wa biḥamdih, Subḥānallāhil-'aẓīm",
                "translation_en": "Two phrases that are light on the tongue, heavy on the scale, and beloved to the Most Merciful: 'Glory be to Allah and praise is His; Glory be to Allah the Magnificent.'",
                "translation_ar": "كلمتان خفيفتان على اللسان ثقيلتان في الميزان حبيبتان إلى الرحمن: سبحان الله وبحمده سبحان الله العظيم.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The simplest dhikr carries the most spiritual weight. This teaches that accessibility is by divine design.",
                "source_ar": "صحيح البخاري وصحيح مسلم. أبسط الذكر يحمل أكبر الأثقال الروحية. يُعلّم هذا أن السهولة قصدٌ إلهي.",
            },
            {
                "arabic": "أَنَا عِنْدَ ظَنِّ عَبْدِي بِي، وَأَنَا مَعَهُ إِذَا ذَكَرَنِي، فَإِنْ ذَكَرَنِي فِي نَفْسِهِ ذَكَرْتُهُ فِي نَفْسِي، وَإِنْ ذَكَرَنِي فِي مَلَإٍ ذَكَرْتُهُ فِي مَلَإٍ خَيْرٍ مِنْهُمْ",
                "transliteration": "Anā 'inda ẓanni 'abdī bī, wa anā ma'ahu idhā dhakaranī, fa-in dhakaranī fī nafsihī dhakartuhu fī nafsī, wa in dhakaranī fī mala'in dhakartuhu fī mala'in khayrin minhum",
                "translation_en": "I am as My servant thinks of Me, and I am with him when he remembers Me. If he remembers Me in himself, I remember him in Myself. If he remembers Me in a gathering, I remember him in a gathering better than it.",
                "translation_ar": "أنا عند ظن عبدي بي وأنا معه إذا ذكرني فإن ذكرني في نفسه ذكرته في نفسي وإن ذكرني في ملأ ذكرته في ملأ خير منهم.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim (hadith qudsi). Dhikr is the mechanism of divine companionship. Every act of remembrance draws Allah's presence — and His remembrance of you is greater than yours of Him.",
                "source_ar": "صحيح البخاري وصحيح مسلم (حديث قدسي). الذكر آلية المصاحبة الإلهية. كل فعل تذكّر يجذب حضور الله — وذكره لك أعظم من ذكرك له.",
            },
            {
                "arabic": "مَنْ قَرَأَ حَرْفًا مِنْ كِتَابِ اللَّهِ فَلَهُ حَسَنَةٌ، وَالْحَسَنَةُ بِعَشْرِ أَمْثَالِهَا، لَا أَقُولُ آلم حَرْفٌ وَلَكِنْ أَلِفٌ حَرْفٌ وَلَامٌ حَرْفٌ وَمِيمٌ حَرْفٌ",
                "transliteration": "Man qara'a ḥarfan min kitābillāhi falahu ḥasanah, wal-ḥasanatu bi'ashr amthālihā, lā aqūlu: Alif lām mīm ḥarfun, wa lākin: alifun ḥarfun wa lāmun ḥarfun wa mīmun ḥarf",
                "translation_en": "Whoever reads a letter from the Book of Allah earns a good deed, and a good deed is multiplied ten times. I do not say that Alif Lam Mim is one letter — rather Alif is a letter, Lam is a letter, and Mim is a letter.",
                "translation_ar": "من قرأ حرفاً من كتاب الله فله حسنة والحسنة بعشر أمثالها لا أقول آلم حرف ولكن ألف حرف ولام حرف وميم حرف.",
                "source_en": "Sunan Tirmidhi (sahih). The minimum unit of reward is a single letter — making the Quran the most rewarding dhikr available. Every moment of recitation is a multiplication of good deeds.",
                "source_ar": "سنن الترمذي (صحيح). أدنى وحدة للأجر هي حرف واحد — مما يجعل القرآن أكثر الأذكار أجراً. كل لحظة تلاوة هي تضاعف للحسنات.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "The heart needs dhikr as much as the body needs food. Just as the body becomes ill through hunger and weakens, the heart becomes ill through negligence and dies from it.",
                "text_ar": "القلب بحاجة إلى الذكر كما يحتاج الجسد إلى الطعام. فكما يمرض الجسد بالجوع ويضعف، يمرض القلب بالغفلة ويموت بها.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Al-Wabil al-Sayyib",
                "source_ar": "الوابل الصيب",
            },
            {
                "text_en": "Dhikr is a shield against Shaytan, a light in the darkness, and a provision for the road to Allah. The heart that is empty of dhikr is occupied by the enemy.",
                "text_ar": "الذكر درع من الشيطان ونور في الظلمة وزاد في الطريق إلى الله. القلب الخالي من الذكر مشغول بالعدو.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Jami' al-'Ulum wal-Hikam",
                "source_ar": "جامع العلوم والحكم",
            },
            {
                "text_en": "Make your tongue moist with the remembrance of Allah, for it will then be moist when you most need it — in the darkness of the grave.",
                "text_ar": "رطّب لسانك بذكر الله فسيكون رطباً حين تحتاجه أكثر — في ظلمة القبر.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Siyar A'lam al-Nubala'",
                "source_ar": "مسجّل في سير أعلام النبلاء",
            },
            {
                "text_en": "The one who remembers Allah frequently is like the soldier who enters the battle fortified with armour — and the one who is negligent enters naked.",
                "text_ar": "الذاكر لله كثيراً كالمحارب الذي دخل المعركة مدرّعاً — والغافل يدخلها عارياً.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Al-Adhkar",
                "source_ar": "الأذكار",
            },
            {
                "text_en": "No act of worship purifies the heart like dhikr — for other acts purify by the effort they require, while dhikr purifies by the presence it demands.",
                "text_ar": "لا عبادة تُطهّر القلب كالذكر — لأن العبادات الأخرى تُطهّر بالجهد الذي تستلزمه، بينما الذكر يُطهّر بالحضور الذي يتطلبه.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Jami' al-'Ulum wal-Hikam",
                "source_ar": "جامع العلوم والحكم",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # QANA'A — Contentment / Sufficiency
    # -----------------------------------------------------------------------
    "contentment": {
        "key": "contentment",
        "topic_en": "Contentment (Qana'a & Rida)",
        "topic_ar": "القناعة والرضا",
        "intro_en": "Qana'a is the richness that never runs out. It begins when you stop measuring by what you lack.",
        "intro_ar": "القناعة هي الغنى الذي لا ينفد. تبدأ حين تتوقف عن القياس بما تفتقر إليه.",
        "hadith": [
            {
                "arabic": "الْغِنَى غِنَى النَّفْسِ",
                "transliteration": "Al-ghinā ghinān-nafs",
                "translation_en": "True wealth is the richness of the soul.",
                "translation_ar": "الغنى غنى النفس.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The Prophet ﷺ redefines wealth entirely: it has nothing to do with accumulated possessions and everything to do with the state of the inner person.",
                "source_ar": "صحيح البخاري وصحيح مسلم. يُعيد النبي ﷺ تعريف الثروة كلياً: لا علاقة لها بالممتلكات المتراكمة وكل شيء لها علاقة بحال الإنسان الداخلي.",
            },
            {
                "arabic": "قَدْ أَفْلَحَ مَنْ أَسْلَمَ، وَرُزِقَ كَفَافًا، وَقَنَّعَهُ اللَّهُ بِمَا آتَاهُ",
                "transliteration": "Qad aflaḥa man aslama, wa ruziqa kafāfan, wa qanna'ahullāhu bimā ātāh",
                "translation_en": "Truly successful is the one who has embraced Islam, been given sufficient provision, and whom Allah has made content with what He has given him.",
                "translation_ar": "قد أفلح من أسلم ورُزق كفافاً وقنّعه الله بما آتاه.",
                "source_en": "Sahih Muslim. The Prophet ﷺ defines success in three things — submission, sufficiency, and contentment. None of them require abundance.",
                "source_ar": "صحيح مسلم. يُعرّف النبي ﷺ النجاح بثلاثة أشياء — الإسلام، والكفاف، والقناعة. لا شيء منها يتطلب الوفرة.",
            },
            {
                "arabic": "ارْضَ بِمَا قَسَمَ اللَّهُ لَكَ تَكُنْ أَغْنَى النَّاسِ",
                "transliteration": "Irḍa bimā qasamallāhu laka takun aghan-nās",
                "translation_en": "Be content with what Allah has apportioned for you, and you will be the richest of people.",
                "translation_ar": "ارضَ بما قسم الله لك تكن أغنى الناس.",
                "source_en": "Sunan Tirmidhi (sahih). Part of a comprehensive counsel of the Prophet ﷺ. Rida (contentment with divine decree) is the gate to a wealth no market can provide.",
                "source_ar": "سنن الترمذي (صحيح). جزء من وصية شاملة للنبي ﷺ. الرضا بقضاء الله هو باب إلى ثروة لا يستطيع أي سوق توفيرها.",
            },
            {
                "arabic": "كُنْ فِي الدُّنْيَا كَأَنَّكَ غَرِيبٌ أَوْ عَابِرُ سَبِيلٍ",
                "transliteration": "Kun fid-dunyā ka'annaka gharībun aw 'ābiru sabīl",
                "translation_en": "Be in this world as if you were a stranger or a wayfarer.",
                "translation_ar": "كن في الدنيا كأنك غريب أو عابر سبيل.",
                "source_en": "Sahih al-Bukhari. This is the full essence of qana'a in one image: the traveller does not over-furnish a resting stop. He packs what he needs for the journey ahead.",
                "source_ar": "صحيح البخاري. هذا هو جوهر القناعة كاملاً في صورة واحدة: المسافر لا يُفرّش استراحةً. يحمل ما يحتاجه للرحلة القادمة.",
            },
            {
                "arabic": "لَوْ كَانَ لِابْنِ آدَمَ وَادِيَانِ مِنْ مَالٍ، لَابْتَغَى ثَالِثًا، وَلَا يَمْلَأُ جَوْفَ ابْنِ آدَمَ إِلَّا التُّرَابُ",
                "transliteration": "Law kāna li-bni ādama wādiyāni min māl, labtaghā thālithan, wa lā yamla'u jawfa bni ādama illāt-turāb",
                "translation_en": "If the son of Adam had two valleys of wealth, he would seek a third — and nothing fills the belly of the son of Adam except dust.",
                "translation_ar": "لو كان لابن آدم واديان من مال لابتغى ثالثاً ولا يملأ جوف ابن آدم إلا التراب.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The Prophet ﷺ diagnoses the root of discontentment: desire without limit. Qana'a is the cure — it places a ceiling on want.",
                "source_ar": "صحيح البخاري وصحيح مسلم. يُشخّص النبي ﷺ جذر عدم القناعة: الرغبة بلا حدود. القناعة هي الدواء — تضع سقفاً للرغبة.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "Contentment is a treasure that never runs dry, a kingdom that no enemy can seize, and a richness that no poverty can diminish.",
                "text_ar": "القناعة كنز لا ينفد وملك لا يُنزع وغنى لا يُفقر.",
                "scholar_en": "Imam Ali ibn Abi Talib",
                "scholar_ar": "الإمام علي بن أبي طالب",
                "source_en": "Nahj al-Balagha",
                "source_ar": "نهج البلاغة",
            },
            {
                "text_en": "Do not seek from people what Allah has already guaranteed for you, and do not pursue from the world what Allah has entrusted to others.",
                "text_ar": "لا تطلب من الناس ما ضمنه الله لك، ولا تطمع من الدنيا فيما أعطاه الله لغيرك.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "Whoever is content with a little in the way of worldly things, will find that Allah is content with a little in the way of his deeds.",
                "text_ar": "من قنع بالقليل من أمور الدنيا، وجد الله يقنع بالقليل من أعماله.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Al-Fawa'id",
                "source_ar": "الفوائد",
            },
            {
                "text_en": "Desire less, and you will find you already have more. The contented person is wealthy without counting; the greedy person is poor without ceasing.",
                "text_ar": "اشتَهِ أقل وستجد أن عندك أكثر مما ظننت. القانع غني دون عدّ؛ والطامع فقير دون توقف.",
                "scholar_en": "Imam al-Shafi'i",
                "scholar_ar": "الإمام الشافعي",
                "source_en": "Diwan al-Imam al-Shafi'i",
                "source_ar": "ديوان الإمام الشافعي",
            },
            {
                "text_en": "Sufficient is the provision that keeps you alive. Sufficient is the rank that keeps you humble. Sufficient is the knowledge that keeps you fearful of Allah.",
                "text_ar": "يكفي من الرزق ما أبقاك حياً. ويكفي من المقام ما أبقاك متواضعاً. ويكفي من العلم ما أبقاك خائفاً من الله.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Hilyat al-Awliya'",
                "source_ar": "مسجّل في حلية الأولياء",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # SHIFA' — Healing
    # -----------------------------------------------------------------------
    "healing": {
        "key": "healing",
        "topic_en": "Healing (Shifa')",
        "topic_ar": "الشفاء",
        "intro_en": "Allah is Al-Shafi — the Healer. Every healing is ultimately His, through whatever means He wills.",
        "intro_ar": "الله هو الشافي. كل شفاء هو في نهاية المطاف منه، من خلال أي سبب يشاء.",
        "hadith": [
            {
                "arabic": "مَا أَنْزَلَ اللَّهُ دَاءً إِلَّا أَنْزَلَ لَهُ شِفَاءً",
                "transliteration": "Mā anzalallāhu dā'an illā anzala lahu shifā'",
                "translation_en": "Allah has not sent down any disease without sending down a cure for it.",
                "translation_ar": "ما أنزل الله داءً إلا أنزل له شفاءً.",
                "source_en": "Sahih al-Bukhari. This hadith establishes the universal principle: every ailment — physical or spiritual — has a cure. Seeking healing is itself an act of tawakkul.",
                "source_ar": "صحيح البخاري. يُقرّر هذا الحديث المبدأ الكلي: لكل داء — جسدي أو روحي — شفاء. طلب الشفاء هو في حد ذاته توكل.",
            },
            {
                "arabic": "اللَّهُمَّ رَبَّ النَّاسِ أَذْهِبِ الْبَاسَ، اشْفِهِ وَأَنْتَ الشَّافِي، لَا شِفَاءَ إِلَّا شِفَاؤُكَ، شِفَاءً لَا يُغَادِرُ سَقَمًا",
                "transliteration": "Allāhumma Rabban-nāsi adhhibil-bās, ishfihī wa antash-shāfī, lā shifā'a illā shifā'uka, shifā'an lā yughādiru saqamā",
                "translation_en": "O Allah, Lord of the people, remove the hardship. Cure him — You are the Healer. There is no cure except Your cure — a cure that leaves behind no illness.",
                "translation_ar": "اللهم رب الناس أذهب البأس اشفه وأنت الشافي لا شفاء إلا شفاؤك شفاءً لا يغادر سقماً.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The Prophet ﷺ would recite this when visiting the sick. It establishes that Allah's healing is complete — it leaves no residual illness behind.",
                "source_ar": "صحيح البخاري وصحيح مسلم. كان النبي ﷺ يقرأ هذا عند عيادة المريض. يُقرّر أن شفاء الله كامل — لا يترك أثراً للمرض.",
            },
            {
                "arabic": "مَا يُصِيبُ الْمُؤْمِنَ مِنْ وَصَبٍ وَلَا نَصَبٍ وَلَا سَقَمٍ وَلَا حَزَنٍ، حَتَّى الْهَمِّ يُهَمُّهُ، إِلَّا كُفِّرَ بِهِ مِنْ خَطَايَاهُ",
                "transliteration": "Mā yuṣībul-mu'mina min waṣabin wa lā naṣabin wa lā saqamin wa lā ḥazanin, ḥattā hammil-yuhammuhu, illā kuffira bihi min khaṭāyāh",
                "translation_en": "No fatigue, illness, sorrow, or even worry that touches a believer — not even a thorn that pricks him — except that Allah expiates some of his sins through it.",
                "translation_ar": "ما يصيب المؤمن من وصَب ولا نَصَب ولا سقم ولا حزن حتى الهمّ يُهمّه إلا كفّر الله به من خطاياه.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. Every form of suffering — physical, emotional — is simultaneously a purification. The believer is being healed even as he is afflicted.",
                "source_ar": "صحيح البخاري وصحيح مسلم. كل شكل من أشكال المعاناة — جسدية أو عاطفية — هو تطهير في الوقت ذاته. المؤمن يتطهر حتى وهو مبتلى.",
            },
            {
                "arabic": "تَدَاوَوْا عِبَادَ اللَّهِ، فَإِنَّ اللَّهَ لَمْ يَضَعْ دَاءً إِلَّا وَضَعَ لَهُ شِفَاءً، غَيْرَ دَاءٍ وَاحِدٍ: الْهَرَمُ",
                "transliteration": "Tadāwaw 'ibādallāh, fa-innallāha lam yaḍa' dā'an illā waḍa'a lahu shifā'an, ghayra dā'in wāḥid: al-haram",
                "translation_en": "Seek treatment, O servants of Allah — for Allah has not placed a disease except He placed a cure for it, other than one disease: old age.",
                "translation_ar": "تداووا عباد الله فإن الله لم يضع داءً إلا وضع له شفاءً غير داء واحد: الهرم.",
                "source_en": "Sunan Abi Dawud and Sunan Tirmidhi (sahih). Seeking medical or therapeutic healing is not contrary to tawakkul — it is commanded. Only the final decline of age is beyond cure.",
                "source_ar": "سنن أبي داود وسنن الترمذي (صحيح). طلب الشفاء الطبي أو العلاجي ليس منافياً للتوكل — بل هو مأمور به. فقط الهرم النهائي ما وراء الشفاء.",
            },
            {
                "arabic": "ضَعْ يَدَكَ عَلَى الَّذِي تَأَلَّمَ مِنْ جَسَدِكَ وَقُلْ: بِسْمِ اللَّهِ، ثَلَاثًا، وَقُلْ سَبْعَ مَرَّاتٍ: أَعُوذُ بِاللَّهِ وَقُدْرَتِهِ مِنْ شَرِّ مَا أَجِدُ وَأُحَاذِرُ",
                "transliteration": "Ḍa' yadaka 'alal-ladhī ta'allama min jasadika wa qul: Bismillāh, thalāthan, wa qul sab'a marrāt: A'ūdhu billāhi wa qudratihī min sharri mā ajidu wa uḥādhir",
                "translation_en": "Place your hand on the part of your body that is in pain and say 'Bismillah' three times, then say seven times: 'I seek refuge in Allah and His power from the evil of what I feel and fear.'",
                "translation_ar": "ضع يدك على الذي تألّم من جسدك وقل: بسم الله ثلاثاً وقل سبع مرات: أعوذ بالله وقدرته من شر ما أجد وأحاذر.",
                "source_en": "Sahih Muslim. A direct prophetic prescription for pain relief through du'a and physical touch — the combination of intention, name, and contact is itself a form of healing presence.",
                "source_ar": "صحيح مسلم. وصفة نبوية مباشرة لتخفيف الألم عبر الدعاء واللمس الجسدي — الجمع بين النية والاسم والاتصال هو شكل من أشكال الحضور الشافي.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "The Quran is a pharmacy for the heart — go to it with your ailment and you will not leave without medicine.",
                "text_ar": "القرآن صيدلية القلب — أتِه بدائك ولن تغادر بدون دواء.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Al-Tibb al-Nabawi",
                "source_ar": "الطب النبوي",
            },
            {
                "text_en": "How can the heart be healed of its disease when it has not yet turned fully to its Doctor? The first step in every healing is turning.",
                "text_ar": "كيف يُشفى القلب من دائه ولم يتحوّل بالكلية إلى طبيبه؟ أول خطوة في كل شفاء هي التحوّل.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Madarij al-Salikin",
                "source_ar": "مدارج السالكين",
            },
            {
                "text_en": "The ill of the heart are cured by four things: sitting with the righteous, reading the Quran, keeping the stomach light, and praying in the night.",
                "text_ar": "علّة القلب تُعالج بأربع: مجالسة الصالحين وقراءة القرآن وتخفيف المعدة والصلاة في جوف الليل.",
                "scholar_en": "Imam al-Shafi'i",
                "scholar_ar": "الإمام الشافعي",
                "source_en": "Diwan al-Imam al-Shafi'i",
                "source_ar": "ديوان الإمام الشافعي",
            },
            {
                "text_en": "Do not rush the cure. Allah heals on His schedule — sometimes the healing is the waiting, and the patience within it is the medicine.",
                "text_ar": "لا تستعجل الشفاء. الله يشفي على جدوله — أحياناً الشفاء هو الانتظار، والصبر فيه هو الدواء.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Lata'if al-Ma'arif",
                "source_ar": "لطائف المعارف",
            },
            {
                "text_en": "Seek healing from the Quran before you seek it from anything else — for it was revealed as healing, and that is its first and truest nature.",
                "text_ar": "اطلب الشفاء من القرآن قبل أن تطلبه من أي شيء آخر — فقد نزل شفاءً وهذه طبيعته الأولى والأصدق.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Al-Adhkar",
                "source_ar": "الأذكار",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # RAHMA — Mercy
    # -----------------------------------------------------------------------
    "mercy": {
        "key": "mercy",
        "topic_en": "Mercy (Rahma)",
        "topic_ar": "الرحمة",
        "intro_en": "Allah's mercy precedes His wrath. It was inscribed before creation. It is not earned — it is sought.",
        "intro_ar": "رحمة الله تسبق غضبه. كُتبت قبل الخلق. لا تُكتسب — بل تُطلب.",
        "hadith": [
            {
                "arabic": "إِنَّ لِلَّهِ مِائَةَ رَحْمَةٍ، أَنْزَلَ مِنْهَا رَحْمَةً وَاحِدَةً بَيْنَ الْجِنِّ وَالْإِنْسِ وَالْبَهَائِمِ وَالْهَوَامِّ، فَبِهَا يَتَعَاطَفُونَ، وَبِهَا يَتَرَاحَمُونَ، وَبِهَا تَعْطِفُ الْوَحْشُ عَلَى وَلَدِهَا، وَأَخَّرَ اللَّهُ تِسْعَةً وَتِسْعِينَ رَحْمَةً يَرْحَمُ بِهَا عِبَادَهُ يَوْمَ الْقِيَامَةِ",
                "transliteration": "Inna lillāhi mi'ata raḥmatin, anzala minhā raḥmatan wāḥidatan baynal-jinni wal-insi wal-bahā'imi wal-hawāmm...",
                "translation_en": "Allah has one hundred mercies. He sent down one of them between the jinn, mankind, animals and insects — through it they show affection and compassion to each other, and through it the wild beast has tenderness for her young. Allah has kept back ninety-nine mercies with which He will be merciful to His slaves on the Day of Resurrection.",
                "translation_ar": "إن لله مائة رحمة، أنزل منها رحمة واحدة بين الجن والإنس والبهائم والهوامّ... وأخّر الله تسعة وتسعين رحمة يرحم بها عباده يوم القيامة.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. All the tenderness we observe in this world — a mother's love, human compassion — is only 1% of divine mercy. The 99% awaits.",
                "source_ar": "صحيح البخاري وصحيح مسلم. كل الحنان الذي نلاحظه في هذا العالم — حب الأم، التعاطف الإنساني — هو 1% فقط من الرحمة الإلهية. الـ99% في الانتظار.",
            },
            {
                "arabic": "الرَّاحِمُونَ يَرْحَمُهُمُ الرَّحْمَنُ، ارْحَمُوا مَنْ فِي الْأَرْضِ يَرْحَمْكُمْ مَنْ فِي السَّمَاءِ",
                "transliteration": "Ar-rāḥimūna yarḥamuhumur-Raḥmān, irḥamū man fil-arḍi yarḥamkum man fis-samā'",
                "translation_en": "The merciful are shown mercy by the Most Merciful. Show mercy to those on earth, and the One above the heavens will show mercy to you.",
                "translation_ar": "الراحمون يرحمهم الرحمن ارحموا من في الأرض يرحمكم من في السماء.",
                "source_en": "Sunan Tirmidhi and Sunan Abi Dawud (sahih). Mercy is a mirror: showing it to others attracts it from Allah. The one who closes their heart to mercy also closes it to receiving it.",
                "source_ar": "سنن الترمذي وسنن أبي داود (صحيح). الرحمة مرآة: إظهارها للآخرين يجذبها من الله. من يُغلق قلبه عن الرحمة يُغلقه أيضاً عن استقبالها.",
            },
            {
                "arabic": "إِنَّ اللَّهَ كَتَبَ الرَّحْمَةَ عَلَى نَفْسِهِ",
                "transliteration": "Innallāha kataba ar-raḥmata 'alā nafsih",
                "translation_en": "Allah has inscribed mercy upon Himself.",
                "translation_ar": "إن الله كتب الرحمة على نفسه.",
                "source_en": "Sahih al-Bukhari. Mercy is not a conditional response — Allah has made it an obligation upon Himself. It is His defining attribute, not a reaction.",
                "source_ar": "صحيح البخاري. الرحمة ليست استجابة مشروطة — الله جعلها فرضاً على نفسه. إنها صفته المميزة لا ردّ فعله.",
            },
            {
                "arabic": "لَا يَرْحَمُ اللَّهُ مَنْ لَا يَرْحَمُ النَّاسَ",
                "transliteration": "Lā yarḥamullāhu man lā yarḥamun-nās",
                "translation_en": "Allah does not show mercy to the one who does not show mercy to people.",
                "translation_ar": "لا يرحم الله من لا يرحم الناس.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. Mercy received from Allah is in direct proportion to mercy extended to others. The heart that withholds rahma blocks its own channel of receiving it.",
                "source_ar": "صحيح البخاري وصحيح مسلم. الرحمة المُتلقّاة من الله تتناسب طرداً مع الرحمة الممتدة للآخرين. القلب الذي يمنع الرحمة يسدّ قناة استقبالها.",
            },
            {
                "arabic": "ابْتَغُوا الرَّفَاعَةَ عِنْدَ اللَّهِ بِالرَّحْمَةِ وَصِلَةِ الرَّحِمِ، فَإِنَّ اللَّهَ تَعَالَى يَرْحَمُ مِنْ عِبَادِهِ الرُّحَمَاءَ",
                "transliteration": "Ibtaghur-rafā'ata 'indallāhi bir-raḥmati wa ṣilat ar-raḥim, fa-innallāha ta'ālā yarḥamu min 'ibādihir-ruḥamā'",
                "translation_en": "Seek elevation in the sight of Allah through mercy and maintaining family ties, for Allah, Most High, shows mercy to those among His servants who are merciful.",
                "translation_ar": "ابتغوا الرفاعة عند الله بالرحمة وصلة الرحم فإن الله تعالى يرحم من عباده الرحماء.",
                "source_en": "Musnad Ahmad (hasan). Mercy is not just a feeling — it is a strategy for closeness to Allah. The merciful are the elite in divine standing.",
                "source_ar": "مسند أحمد (حسن). الرحمة ليست مجرد شعور — بل هي استراتيجية للقرب من الله. الرحماء هم النخبة في المكانة الإلهية.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "The mercy of Allah is like rain: it falls on the good soil and the bad alike. The difference is what each one grows from it.",
                "text_ar": "رحمة الله كالمطر: يقع على الأرض الطيبة والخبيثة على حدٍّ سواء. الفرق هو ما ينبت كل واحد منها.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Madarij al-Salikin",
                "source_ar": "مدارج السالكين",
            },
            {
                "text_en": "If you knew the depth of His mercy toward you, your heart would melt from shyness that you ever doubted it.",
                "text_ar": "لو عرفت عمق رحمته تجاهك لذاب قلبك حياءً أنك شككت فيها يوماً.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "Begin every task with His name and every aspiration with His mercy — for the name of Allah leads you in, and His mercy carries you through.",
                "text_ar": "ابدأ كل عمل باسمه وكل طموح برحمته — فاسم الله يُدخلك وتحملك رحمته.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Al-Adhkar",
                "source_ar": "الأذكار",
            },
            {
                "text_en": "Mercy toward the sinner is not weakness — it is the greatest strength, because it imitates the attribute of the Most Merciful Himself.",
                "text_ar": "الرحمة بالمذنب ليست ضعفاً — بل هي أعظم قوة لأنها تُحاكي صفة الرحمن نفسه.",
                "scholar_en": "Imam al-Shafi'i",
                "scholar_ar": "الإمام الشافعي",
                "source_en": "Diwan al-Imam al-Shafi'i",
                "source_ar": "ديوان الإمام الشافعي",
            },
            {
                "text_en": "The measure of your mercy toward the creation is the measure of Allah's mercy toward you. Widen your heart and you widen His gift.",
                "text_ar": "قدر رحمتك تجاه الخلق هو قدر رحمة الله تجاهك. وسّع قلبك توسّع عطاؤه.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Jami' al-'Ulum wal-Hikam",
                "source_ar": "جامع العلوم والحكم",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # MAGHFIRA / FORGIVENESS
    # -----------------------------------------------------------------------
    "forgiveness": {
        "key": "forgiveness",
        "topic_en": "Forgiveness (Maghfira & 'Afw)",
        "topic_ar": "المغفرة والعفو",
        "intro_en": "Forgiveness in Islam flows in two directions: receiving it from Allah, and extending it to others.",
        "intro_ar": "المغفرة في الإسلام تتدفق في اتجاهين: تلقّيها من الله، وتمديدها للآخرين.",
        "hadith": [
            {
                "arabic": "مَنْ كَظَمَ غَيْظًا وَهُوَ قَادِرٌ عَلَى أَنْ يُنْفِذَهُ، دَعَاهُ اللَّهُ عَلَى رُءُوسِ الْخَلَائِقِ يَوْمَ الْقِيَامَةِ حَتَّى يُخَيِّرَهُ مِنَ الْحُورِ الْعِينِ مَا شَاءَ",
                "transliteration": "Man kaẓama ghayẓan wa huwa qādirun 'alā an yunfidhahu, da'āhullāhu 'alā ru'ūsil-khalā'iqi yawmal-qiyāmati ḥattā yukhayyrahu minal-ḥūril-'īni mā shā'",
                "translation_en": "Whoever suppresses his anger while being capable of acting on it, Allah will call him before all creation on the Day of Resurrection and let him choose whatever he wishes from the wide-eyed maidens of Paradise.",
                "translation_ar": "من كظم غيظاً وهو قادر على أن ينفذه دعاه الله على رؤوس الخلائق يوم القيامة حتى يُخيّره من الحور العين ما شاء.",
                "source_en": "Sunan Tirmidhi and Sunan Abi Dawud (hasan). Forgiveness — especially when one has the power to retaliate — is ranked among the highest spiritual achievements.",
                "source_ar": "سنن الترمذي وسنن أبي داود (حسن). المغفرة — خاصةً حين يملك المرء القدرة على الانتقام — تُصنّف بين أعلى الإنجازات الروحية.",
            },
            {
                "arabic": "مَا نَقَصَتْ صَدَقَةٌ مِنْ مَالٍ، وَمَا زَادَ اللَّهُ عَبْدًا بِعَفْوٍ إِلَّا عِزًّا",
                "transliteration": "Mā naqaṣat ṣadaqatun min māl, wa mā zādallāhu 'abdan bi'afwin illā 'izzā",
                "translation_en": "Charity does not decrease wealth, and Allah increases a servant in nothing but honour when he forgives.",
                "translation_ar": "ما نقصت صدقة من مال وما زاد الله عبداً بعفو إلا عزاً.",
                "source_en": "Sahih Muslim. Forgiveness does not diminish you — it elevates you. The one who forgives becomes more honoured, not weaker.",
                "source_ar": "صحيح مسلم. المغفرة لا تُصغّرك — بل ترفعك. من يعفو يزداد شرفاً لا ضعفاً.",
            },
            {
                "arabic": "وَاللَّهُ يُحِبُّ الْعَافِينَ عَنِ النَّاسِ",
                "transliteration": "Wallāhu yuḥibbul-'āfīna 'anin-nās",
                "translation_en": "And Allah loves those who pardon people.",
                "translation_ar": "والله يحب العافين عن الناس.",
                "source_en": "Sunan Tirmidhi. This phrase from Quran 3:134 is cited extensively in hadith literature as one of the strongest motivations for forgiveness — it draws the direct love of Allah.",
                "source_ar": "سنن الترمذي. هذه العبارة من آل عمران 3:134 مُستشهد بها كثيراً في أدب الحديث بوصفها أقوى دوافع المغفرة — تجلب محبة الله مباشرةً.",
            },
            {
                "arabic": "إِنَّ اللَّهَ تَجَاوَزَ عَنْ أُمَّتِي مَا حَدَّثَتْ بِهِ أَنْفُسَهَا، مَا لَمْ تَعْمَلْ أَوْ تَتَكَلَّمْ",
                "transliteration": "Innallāha tajāwaza 'an ummatī mā ḥaddathat bihi anfusahā, mā lam ta'mal aw tatakallam",
                "translation_en": "Allah has overlooked for my nation what their souls whisper to themselves, as long as they do not act upon it or speak of it.",
                "translation_ar": "إن الله تجاوز عن أمتي ما حدّثت به أنفسها ما لم تعمل أو تتكلم.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. Inner thoughts, urges, and passing whispers are pre-forgiven. Only action or speech makes one accountable — the gate of divine pardon covers the inner life.",
                "source_ar": "صحيح البخاري وصحيح مسلم. الأفكار الداخلية والدوافع والوسوسة العابرة مغفورة مسبقاً. العمل أو الكلام وحده يُوجب المسؤولية — باب العفو الإلهي يغطي الحياة الداخلية.",
            },
            {
                "arabic": "الندَّامَةُ تَوْبَةٌ",
                "transliteration": "An-nadāmatu tawbah",
                "translation_en": "Remorse is repentance.",
                "translation_ar": "الندامة توبة.",
                "source_en": "Sunan Ibn Majah and Musnad Ahmad (sahih). The first and most essential element of forgiveness-seeking is feeling — genuine sorrow is itself the beginning of the return.",
                "source_ar": "سنن ابن ماجه ومسند أحمد (صحيح). العنصر الأول والأساسي في طلب المغفرة هو الشعور — الحزن الحقيقي هو بحد ذاته بداية العودة.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "The noblest of attributes is to forgive when you are able to take revenge.",
                "text_ar": "من أشرف الخصال العفو عند القدرة.",
                "scholar_en": "Imam Ali ibn Abi Talib",
                "scholar_ar": "الإمام علي بن أبي طالب",
                "source_en": "Nahj al-Balagha",
                "source_ar": "نهج البلاغة",
            },
            {
                "text_en": "Forgive others as frequently as you hope Allah will forgive you — for you will meet Him with the measure you applied to others.",
                "text_ar": "اعفُ عن الآخرين بقدر ما تأمل أن يعفو الله عنك — فستقابله بالمقياس الذي طبّقته على الآخرين.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Al-Fawa'id",
                "source_ar": "الفوائد",
            },
            {
                "text_en": "The bitterness of forgiving is sweeter than the bitterness of being trapped in anger — for one leads to Allah and the other leads to ruin.",
                "text_ar": "مرارة العفو أحلى من مرارة الأسر في الغضب — لأن أحدهما يقود إلى الله والآخر إلى الخراب.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Lata'if al-Ma'arif",
                "source_ar": "لطائف المعارف",
            },
            {
                "text_en": "Forgiving others is not forgetting what was done — it is releasing yourself from the prison of resentment. You forgive for your own freedom first.",
                "text_ar": "العفو عن الآخرين ليس نسياناً لما حدث — بل هو تحرير نفسك من سجن الضغينة. تعفو من أجل حريتك أنت أولاً.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Hilyat al-Awliya'",
                "source_ar": "مسجّل في حلية الأولياء",
            },
            {
                "text_en": "The one who forgives readily is the one who remembers most clearly that he himself is in need of forgiveness — and from a much greater Judge.",
                "text_ar": "من يعفو بسهولة هو من يتذكر جيداً أنه هو نفسه بحاجة إلى المغفرة — ومن قاضٍ أعظم بكثير.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Riyad al-Salihin",
                "source_ar": "رياض الصالحين",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # STRENGTH — Drawing courage from faith
    # -----------------------------------------------------------------------
    "strength": {
        "key": "strength",
        "topic_en": "Strength (Quwwa & 'Azm)",
        "topic_ar": "القوة والعزيمة",
        "intro_en": "The strongest person is not the most physical — it is the one who masters himself in anger.",
        "intro_ar": "أقوى الناس ليس الأكثر قوة جسدية — بل من يملك نفسه عند الغضب.",
        "hadith": [
            {
                "arabic": "الْمُؤْمِنُ الْقَوِيُّ خَيْرٌ وَأَحَبُّ إِلَى اللَّهِ مِنَ الْمُؤْمِنِ الضَّعِيفِ، وَفِي كُلٍّ خَيْرٌ",
                "transliteration": "Al-mu'minul-qawiyyu khayrun wa aḥabbu ilallāhi minal-mu'minil-ḍa'īf, wa fī kullin khayr",
                "translation_en": "The strong believer is better and more beloved to Allah than the weak believer — though there is good in both.",
                "translation_ar": "المؤمن القوي خير وأحب إلى الله من المؤمن الضعيف وفي كلٍّ خير.",
                "source_en": "Sahih Muslim. 'Strong' here means strength of character, resolve, and consistent action — not physical strength. Both kinds of believer are beloved, but strength in faith is greater.",
                "source_ar": "صحيح مسلم. 'القوي' هنا يعني قوة الشخصية والعزم والعمل المتسق — ليس القوة الجسدية. كلا المؤمنين محبوبان، لكن القوة في الإيمان أعظم.",
            },
            {
                "arabic": "لَيْسَ الشَّدِيدُ بِالصُّرَعَةِ، إِنَّمَا الشَّدِيدُ الَّذِي يَمْلِكُ نَفْسَهُ عِنْدَ الْغَضَبِ",
                "transliteration": "Laysash-shadīdu biṣ-ṣur'ati, innamas-shadīdul-ladhī yamliku nafsahu 'indal-ghaḍab",
                "translation_en": "The strong person is not the one who wrestles others down. The strong person is the one who controls himself at the moment of anger.",
                "translation_ar": "ليس الشديد بالصُّرعة إنما الشديد الذي يملك نفسه عند الغضب.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The highest human strength is not physical domination but mastery of one's own response — this is the station of true courage.",
                "source_ar": "صحيح البخاري وصحيح مسلم. أعلى قوة إنسانية ليست السيطرة الجسدية بل إتقان استجابة المرء — وهذا مقام الشجاعة الحقيقية.",
            },
            {
                "arabic": "احْرِصْ عَلَى مَا يَنْفَعُكَ، وَاسْتَعِنْ بِاللَّهِ وَلَا تَعْجَزْ",
                "transliteration": "Iḥriṣ 'alā mā yanfa'uka, wasta'in billāhi wa lā ta'jaz",
                "translation_en": "Be eager for what benefits you, seek help from Allah, and do not be incapacitated.",
                "translation_ar": "احرص على ما ينفعك واستعن بالله ولا تعجز.",
                "source_en": "Sahih Muslim. The Prophet ﷺ prescribes the exact formula for strength: desire what is good, ask Allah for help, and reject learned helplessness.",
                "source_ar": "صحيح مسلم. يصف النبي ﷺ الصيغة الدقيقة للقوة: ارغب في الخير، استعن بالله، وارفض العجز المكتسب.",
            },
            {
                "arabic": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْعَجْزِ وَالْكَسَلِ، وَالْجُبْنِ وَالْبُخْلِ، وَالْهَرَمِ وَعَذَابِ الْقَبْرِ",
                "transliteration": "Allāhumma innī a'ūdhu bika minal-'ajzi wal-kasal, wal-jubni wal-bukhl, wal-harami wa 'adhābil-qabr",
                "translation_en": "O Allah, I seek refuge in You from incapacity and laziness, from cowardice and miserliness, from old age and the punishment of the grave.",
                "translation_ar": "اللهم إني أعوذ بك من العجز والكسل والجبن والبخل والهرم وعذاب القبر.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. The Prophet ﷺ taught this as a daily refuge. Seeking strength begins with acknowledging its enemies: laziness, cowardice, and paralysis.",
                "source_ar": "صحيح البخاري وصحيح مسلم. علّم النبي ﷺ هذا ملاذاً يومياً. طلب القوة يبدأ بالاعتراف بأعدائها: الكسل والجبن والشلل.",
            },
            {
                "arabic": "مَنْ رَأَى مِنْكُمْ مُنْكَرًا فَلْيُغَيِّرْهُ بِيَدِهِ، فَإِنْ لَمْ يَسْتَطِعْ فَبِلِسَانِهِ، فَإِنْ لَمْ يَسْتَطِعْ فَبِقَلْبِهِ، وَذَلِكَ أَضْعَفُ الْإِيمَانِ",
                "transliteration": "Man ra'ā minkum munkaran falyughayyirhu biyadih, fa-in lam yastaṭi' fabilisānih, fa-in lam yastaṭi' fabi-qalbih, wa dhālika aḍ'aful-īmān",
                "translation_en": "Whoever among you sees an evil, let him change it with his hand. If he cannot, then with his tongue. If he cannot, then with his heart — and that is the weakest of faith.",
                "translation_ar": "من رأى منكم منكراً فليغيّره بيده فإن لم يستطع فبلسانه فإن لم يستطع فبقلبه وذلك أضعف الإيمان.",
                "source_en": "Sahih Muslim. This hadith establishes a hierarchy of strength: the strongest acts with his hands, the next with words, the weakest with his heart. Each level is valid — none are excused.",
                "source_ar": "صحيح مسلم. يُقرّر هذا الحديث تراتبية القوة: الأقوى يتصرف بيديه والتالي بكلامه والأضعف بقلبه. كل مستوى صالح — ولا أحد معذور.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "Do not measure your strength by your past. Measure it by who you are becoming in your turning toward Allah.",
                "text_ar": "لا تقيس قوتك بماضيك. قسها بمن تصبح في توجّهك نحو الله.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Al-Fawa'id",
                "source_ar": "الفوائد",
            },
            {
                "text_en": "The strength Allah loves is not the strength that crushes others, but the strength that lifts itself toward Him.",
                "text_ar": "القوة التي يُحبها الله ليست القوة التي تسحق الآخرين، بل القوة التي ترفع نفسها نحوه.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Siyar A'lam al-Nubala'",
                "source_ar": "مسجّل في سير أعلام النبلاء",
            },
            {
                "text_en": "Every time you choose Allah over your nafs, you become a little stronger. Strength in deen is a cumulative gift.",
                "text_ar": "كل مرة تختار الله على نفسك تصبح أقوى قليلاً. القوة في الدين هبة تراكمية.",
                "scholar_en": "Ibn Ata Allah al-Iskandari",
                "scholar_ar": "ابن عطاء الله الإسكندري",
                "source_en": "Al-Hikam al-'Ata'iyya",
                "source_ar": "الحكم العطائية",
            },
            {
                "text_en": "The strength that matters before Allah is consistency in obedience — not one great act but a thousand small ones done with resolve and not abandoned.",
                "text_ar": "القوة التي تهم أمام الله هي الاستمرار في الطاعة — ليس فعلاً عظيماً واحداً بل ألف فعل صغير بعزم لا يُترك.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Lata'if al-Ma'arif",
                "source_ar": "لطائف المعارف",
            },
            {
                "text_en": "Strength is not proven in the absence of fear, but in acting despite it — in moving forward while the heart trembles, trusting that Allah walks beside you.",
                "text_ar": "القوة لا تُثبت بغياب الخوف بل بالتصرف رغمه — بالمضي قدماً بينما يرتجف القلب ثقةً أن الله يسير بجانبك.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Siyar A'lam al-Nubala'",
                "source_ar": "مسجّل في سير أعلام النبلاء",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # RUQYAH — Quranic Healing
    # -----------------------------------------------------------------------
    "ruqyah": {
        "key": "ruqyah",
        "topic_en": "Quranic Healing (Ruqyah Shariah)",
        "topic_ar": "الرقية الشرعية",
        "intro_en": "Ruqyah Shariah is the use of Quranic recitation and authentic du'a for spiritual healing.",
        "intro_ar": "الرقية الشرعية هي استخدام تلاوة القرآن والدعاء الصحيح للشفاء الروحي.",
        "hadith": [
            {
                "arabic": "مَنْ نَامَ وَلَمْ يَقْرَأْ آيَةَ الْكُرْسِيِّ لَمْ يَزَلْ عَلَيْهِ مِنَ اللَّهِ حَافِظٌ وَلَا يَقْرَبُهُ شَيْطَانٌ حَتَّى يُصْبِحَ",
                "transliteration": "Man nāma wa lam yaqra' āyatal-kursiyyi lam yazal 'alayhi minallāhi ḥāfiẓun wa lā yaqrabuhū shayṭānun ḥattā yuṣbiḥ",
                "translation_en": "Whoever sleeps and recites Ayat al-Kursi, a guardian from Allah will remain over him and Satan will not approach him until morning.",
                "translation_ar": "من نام ولم يقرأ آية الكرسي لم يزل عليه من الله حافظ ولا يقربه شيطان حتى يصبح.",
                "source_en": "Sahih al-Bukhari. The Prophet ﷺ taught this specifically for nightly protection — Ayat al-Kursi (2:255) is the greatest verse in the Quran by prophetic testimony.",
                "source_ar": "صحيح البخاري. علّم النبي ﷺ هذا تحديداً للحماية الليلية — آية الكرسي (2:255) هي أعظم آية في القرآن بشهادة نبوية.",
            },
            {
                "arabic": "عَرَضَ لِي إِبْلِيسُ فَتَفَلْتُ فِي وَجْهِهِ ثَلَاثًا وَتَعَوَّذْتُ بِاللَّهِ مِنَ اللَّهِ فَلَمْ يَضُرَّنِي",
                "transliteration": "Araḍa lī iblīsu fatafalttu fī wajhihī thalāthan wa ta'awwadhthu billāhi minash-shayṭān falam yaḍurranī",
                "translation_en": "Iblis appeared before me, and I spat at his face three times and sought refuge in Allah from Satan — and he did not harm me.",
                "translation_ar": "عرض لي إبليس فتفلتُ في وجهه ثلاثاً وتعوّذتُ بالله من الشيطان فلم يضرني.",
                "source_en": "Sahih Muslim. The Prophet ﷺ teaching that A'udhu billahi minash-shaytan ir-rajim, recited with conviction, is the immediate protection against spiritual harm.",
                "source_ar": "صحيح مسلم. النبي ﷺ يُعلّم أن 'أعوذ بالله من الشيطان الرجيم' بقناعة هو الحماية الفورية من الأذى الروحي.",
            },
            {
                "arabic": "مَنْ قَرَأَ الْآيَتَيْنِ مِنْ آخِرِ سُورَةِ الْبَقَرَةِ فِي لَيْلَةٍ كَفَتَاهُ",
                "transliteration": "Man qara'al-āyatayni min ākhiri sūratil-baqarati fī laylatin kafatāh",
                "translation_en": "Whoever recites the last two verses of Surah Al-Baqarah at night, they will suffice him.",
                "translation_ar": "من قرأ الآيتين من آخر سورة البقرة في ليلة كفتاه.",
                "source_en": "Sahih al-Bukhari and Sahih Muslim. Scholars explain 'suffice' as protection from harm, evil, and spiritual affliction for that night.",
                "source_ar": "صحيح البخاري وصحيح مسلم. يُفسّر العلماء 'كفتاه' بالحماية من الأذى والشر والوسوسة لتلك الليلة.",
            },
            {
                "arabic": "مَنْ قَرَأَ قُلْ هُوَ اللَّهُ أَحَدٌ وَالْمُعَوِّذَتَيْنِ حِينَ يُمْسِي وَحِينَ يُصْبِحُ ثَلَاثَ مَرَّاتٍ كَفَتْهُ مِنْ كُلِّ شَيْءٍ",
                "transliteration": "Man qara'a: Qul huwallāhu aḥad, wal-mu'awwidhatayni ḥīna yumsī wa ḥīna yuṣbiḥu thalātha marrātin kafathu min kulli shay'",
                "translation_en": "Whoever recites 'Qul huwa Allahu Ahad' and the two protection surahs (al-Falaq and al-Nas) three times in the evening and three times in the morning — they will suffice him against everything.",
                "translation_ar": "من قرأ قل هو الله أحد والمعوذتين حين يمسي وحين يصبح ثلاث مرات كفته من كل شيء.",
                "source_en": "Sunan Abi Dawud and Sunan Tirmidhi (sahih). A prophetic morning and evening routine for complete protection — the three surahs cover Tawhid (Ikhlas), protection from creation (Falaq), and protection from inner whispering (Nas).",
                "source_ar": "سنن أبي داود وسنن الترمذي (صحيح). روتين نبوي صباحي ومسائي للحماية الكاملة — السور الثلاث تغطي التوحيد (الإخلاص) والحماية من المخلوقات (الفلق) والحماية من الوسوسة الداخلية (الناس).",
            },
            {
                "arabic": "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
                "transliteration": "Bismillāhil-ladhī lā yaḍurru ma'asmihi shay'un fil-arḍi wa lā fis-samā'i wa huwas-samī'ul-'alīm",
                "translation_en": "In the name of Allah, with whose name nothing on earth or in heaven can cause harm — and He is the All-Hearing, All-Knowing.",
                "translation_ar": "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم.",
                "source_en": "Sunan Abi Dawud and Sunan Tirmidhi (sahih). The Prophet ﷺ taught that reciting this three times in the morning and evening means nothing will harm you that day or night. The Name itself is the shield.",
                "source_ar": "سنن أبي داود وسنن الترمذي (صحيح). علّم النبي ﷺ أن قراءة هذا ثلاث مرات صباحاً ومساءً تعني أنه لن يضرك شيء ذلك اليوم أو تلك الليلة. الاسم ذاته هو الدرع.",
            },
        ],
        "wise_phrases": [
            {
                "text_en": "Recite the Quran upon yourself before sleeping, upon your family when they are ill, and upon your home when you enter it — make it the medicine of your household.",
                "text_ar": "اقرأ القرآن على نفسك قبل النوم وعلى أهلك حين يمرضون وعلى بيتك حين تدخله — اجعله دواء بيتك.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Zad al-Ma'ad",
                "source_ar": "زاد المعاد",
            },
            {
                "text_en": "Ruqyah has three conditions: it must be from the Quran or prophetic speech, understood in meaning, and believed to be a means — not the source — of healing.",
                "text_ar": "للرقية ثلاثة شروط: أن تكون من القرآن أو الكلام النبوي، مفهومة المعنى، ومعتقَداً أنها سبب لا مصدر الشفاء.",
                "scholar_en": "Imam al-Nawawi",
                "scholar_ar": "الإمام النووي",
                "source_en": "Sharh Sahih Muslim",
                "source_ar": "شرح صحيح مسلم",
            },
            {
                "text_en": "The Quran heals not because of the vibration of words, but because of the presence of the one reciting — if you are absent from your recitation, it is sound without medicine.",
                "text_ar": "القرآن يشفي لا بسبب اهتزاز الكلمات بل بسبب حضور التالي — إن كنت غائباً عن تلاوتك فهي صوت بلا دواء.",
                "scholar_en": "Ibn Qayyim al-Jawziyyah",
                "scholar_ar": "ابن قيم الجوزية",
                "source_en": "Al-Tibb al-Nabawi",
                "source_ar": "الطب النبوي",
            },
            {
                "text_en": "Do not use ruqyah as a replacement for seeking the cause of illness — use it alongside medicine as the Prophet commanded. Spiritual and physical healing are not rivals; they are partners.",
                "text_ar": "لا تستخدم الرقية بديلاً عن البحث عن سبب المرض — استخدمها مع الدواء كما أمر النبي. الشفاء الروحي والجسدي ليسا منافسَين؛ بل هما شريكان.",
                "scholar_en": "Ibn Rajab al-Hanbali",
                "scholar_ar": "ابن رجب الحنبلي",
                "source_en": "Jami' al-'Ulum wal-Hikam",
                "source_ar": "جامع العلوم والحكم",
            },
            {
                "text_en": "The protective power of Quranic verses lies not in their sound but in their meaning penetrating the heart. Recite with understanding, for understanding is where healing begins.",
                "text_ar": "القوة الواقية للآيات القرآنية لا تكمن في صوتها بل في اختراق معناها للقلب. اقرأ بفهم فالفهم هو حيث يبدأ الشفاء.",
                "scholar_en": "Hasan al-Basri",
                "scholar_ar": "الحسن البصري",
                "source_en": "Recorded in Hilyat al-Awliya'",
                "source_ar": "مسجّل في حلية الأولياء",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_topic_resources(topic: str) -> Optional[TopicBlock]:
    """Return the full knowledge block for the given topic key, or None."""
    return _TOPIC_KNOWLEDGE.get(topic)


def get_topics_for_emotion(emotion: str) -> List[str]:
    """Map an emotion category to relevant topic keys."""
    _EMOTION_TOPIC_MAP: Dict[str, List[str]] = {
        "anxiety":      ["trust", "hope", "dhikr", "patience"],
        "sadness":      ["hope", "patience", "mercy", "healing"],
        "grief":        ["patience", "hope", "mercy", "forgiveness"],
        "fear":         ["trust", "strength", "dhikr", "hope"],
        "loneliness":   ["mercy", "dhikr", "trust", "hope"],
        "hopelessness": ["hope", "mercy", "tawbah", "trust"],
        "anger":        ["forgiveness", "strength", "patience", "dhikr"],
        "stress":       ["patience", "trust", "dhikr", "strength"],
        "guilt":        ["tawbah", "forgiveness", "mercy", "hope"],
        "doubt":        ["trust", "healing", "dhikr", "hope"],
        "gratitude":    ["gratitude", "contentment", "dhikr", "mercy"],
        "general":      ["mercy", "dhikr", "hope", "patience"],
    }
    return _EMOTION_TOPIC_MAP.get(emotion, ["mercy", "hope"])


def get_all_topic_keys() -> List[str]:
    """Return all available topic keys."""
    return list(_TOPIC_KNOWLEDGE.keys())
