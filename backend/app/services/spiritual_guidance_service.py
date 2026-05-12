"""
Spiritual Guidance Service — Phase T.

Provides emotion classification, Quranic verse lookup, and structured
guidance cards for the emotional support / spiritual therapy feature.

Design principles:
  - Emotion classification is keyword-based (no external ML dependency).
  - All Quranic text comes from the QuranVerse DB table (never hard-coded).
  - Lesson summaries, reflection questions, and du'a suggestions are
    platform-authored meta-commentary, NOT tafsir.
  - Tafsir commentary is retrieved from TafseerChunk via the existing RAG
    pipeline when available; the service degrades gracefully without it.
  - Every response includes a professional-help disclaimer.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse
from app.models.therapy import EmotionCategory

# ---------------------------------------------------------------------------
# Emotion keyword bank
# ---------------------------------------------------------------------------

_EMOTION_KEYWORDS: Dict[str, List[str]] = {
    EmotionCategory.ANXIETY: [
        # English
        "anxious", "anxiety", "worry", "worried", "nervous", "panic", "uneasy",
        "restless", "overwhelmed", "tense", "dread", "apprehensive", "overthinking",
        "on edge", "jittery", "scared of future", "what if", "can't relax",
        # Arabic — standard
        "قلق", "توتر", "خوف", "وسواس", "تعب", "ضيق",
        # Arabic — expanded colloquial & literary
        "قلقان", "متوتر", "أفكر كثيراً", "مش قادر أرتاح", "خايف",
        "تعبان نفسياً", "الوسواس", "مرهق ذهنياً", "خوف من المستقبل",
        "قلق على", "مش عارف شو يصير", "تعبت من التفكير",
    ],
    EmotionCategory.SADNESS: [
        # English
        "sad", "sadness", "unhappy", "miserable", "gloomy", "depressed", "crying",
        "tears", "melancholy", "down", "heartbroken", "blue", "despondent",
        "broken", "weeping", "grief-stricken", "heavy heart",
        # Arabic — standard
        "حزين", "حزن", "كئيب", "بكاء", "مكتئب", "دموع",
        # Arabic — expanded
        "حزنان", "زهقت", "مو بخير", "قلبي تعبان", "ما في فايدة",
        "تعبت", "بكيت", "ما لقيت راحة", "وجعت", "مجروح",
        "أشعر بالفراغ", "صدري ضيق", "ثقيل قلبي", "تعب الروح",
    ],
    EmotionCategory.GRIEF: [
        # English
        "grief", "grieving", "loss", "bereaved", "mourning", "died", "death",
        "passed away", "losing someone", "bereavement", "devastating",
        "lost someone", "funeral", "widow", "orphan",
        # Arabic — standard
        "فقد", "فقدان", "وفاة", "حداد", "مصيبة", "رحل", "توفي",
        # Arabic — expanded
        "فقدت", "مات", "ماتت", "توفي", "توفيت", "ابكي على",
        "فارقني", "غيابه", "غيابها", "الله يرحمه", "الله يرحمها",
        "اشتياق", "وجع الفراق", "الفراق", "لن أراه", "لن أراها",
    ],
    EmotionCategory.FEAR: [
        # English
        "fear", "afraid", "scared", "terrified", "frightened", "phobia",
        "terror", "horror", "dread", "fright", "petrified", "panicking",
        # Arabic — standard
        "خائف", "خوف", "رعب", "فزع", "مرعوب", "هلع",
        # Arabic — expanded
        "خايف", "مرعوب", "مذعور", "الخوف يأكلني", "أخشى",
        "أخاف من", "خوفان", "وجل", "فزعان", "الرهبة",
        "أفزعني", "هلعت", "رهبة", "ذعر",
    ],
    EmotionCategory.LONELINESS: [
        # English
        "lonely", "loneliness", "alone", "isolated", "abandoned", "no one",
        "disconnected", "left out", "forgotten", "friendless", "unwanted",
        "no friends", "nobody cares", "invisible",
        # Arabic — standard
        "وحيد", "وحدة", "عزلة", "مهجور", "منعزل", "متروك", "لا أحد",
        # Arabic — expanded
        "وحداني", "ما عندي أحد", "الناس نسيتني", "محد يسألعني",
        "بوحدتي", "لوحدي", "ما في أحد", "مش مهم لأحد",
        "محد يهتم", "الوحدة تقتلني", "منبوذ", "منبوذة",
    ],
    EmotionCategory.HOPELESSNESS: [
        # English
        "hopeless", "hopelessness", "no hope", "giving up", "pointless",
        "meaningless", "futile", "no reason", "lost", "despair", "desperate",
        "can't go on", "what's the point", "nothing matters",
        # Arabic — standard
        "يأس", "قنوط", "لا أمل", "استسلام", "ضايع", "بلا معنى",
        # Arabic — expanded
        "يائس", "مش شايف أمل", "ما في فايدة", "تعبت من الحياة",
        "مستحيل يتحسن", "ما راح يتغير شي", "انتهيت", "قنطت",
        "استسلمت", "كل شي سواد", "لا حياة بعد", "ما أبي أكمل",
    ],
    EmotionCategory.ANGER: [
        # English
        "angry", "anger", "furious", "rage", "frustrated", "irritated",
        "resentful", "bitter", "enraged", "mad", "annoyed",
        "livid", "seething", "outraged", "fuming",
        # Arabic — standard
        "غاضب", "غضب", "حقد", "ضغينة", "نقمة", "محبط", "منزعج",
        # Arabic — expanded
        "زعلان", "عصبي", "مجنون من الزعل", "غضبان", "انفجرت",
        "ما تحملت", "كرهت", "نفذ صبري", "اشتعل", "ثرت",
        "بالغيظ", "كظم الغيظ", "الحقد", "الكراهية", "ضايقني",
    ],
    EmotionCategory.STRESS: [
        # English
        "stress", "stressed", "pressure", "exhausted", "burnout",
        "overwhelmed", "burden", "overloaded", "too much", "can't cope",
        "no energy", "drained", "fatigued", "worn out",
        # Arabic — standard
        "ضغط", "إجهاد", "إرهاق", "محمل", "مرهق", "تعب نفسي",
        # Arabic — expanded
        "مضغوط", "تحت ضغط", "تعبان", "ما قادر أكمل", "خلص طاقتي",
        "منهك", "محروق", "ما قدرت", "فوق طاقتي", "كل شي على",
        "الأعباء كثيرة", "زهقت من الضغط", "لازم أرتاح",
    ],
    EmotionCategory.GUILT: [
        # English
        "guilt", "guilty", "ashamed", "shame", "regret", "remorse",
        "sinned", "wrong", "mistake", "bad person", "forgive me",
        "i did wrong", "can't forgive myself", "confession",
        # Arabic — standard
        "ذنب", "خطيئة", "ندم", "خجل", "أنا مذنب", "تبت", "اعتذار",
        # Arabic — expanded
        "نادم", "أندم", "أشعر بالذنب", "خطأت", "أخطأت",
        "ذنوبي كثيرة", "عملت حاجة غلط", "عيب", "ما أسامح نفسي",
        "الاستغفار", "أستغفر", "تائب", "أتوب", "ذنوب",
        "ارتكبت", "أشكو من نفسي",
    ],
    EmotionCategory.DOUBT: [
        # English
        "doubt", "doubting", "confused", "faith", "uncertain", "questioning",
        "don't understand", "why", "lost faith", "skeptical",
        "not sure", "confused about religion", "questioning belief",
        # Arabic — standard
        "شك", "تشكيك", "حيرة", "ارتباك", "لماذا", "فقدت الإيمان",
        # Arabic — expanded
        "شاك", "مش واثق", "في شك", "مش فاهم", "لماذا يحدث هذا",
        "ما أفهم حكمة الله", "تساؤلات دينية", "الإيمان ضعيف",
        "حيران", "ما متأكد", "الشك في", "تشككت", "الحيرة",
    ],
    EmotionCategory.GRATITUDE: [
        # English
        "grateful", "gratitude", "thankful", "blessed", "appreciate",
        "alhamdulillah", "thankfulness", "content", "joyful", "happy",
        "peace", "peaceful", "fulfilled",
        # Arabic — standard
        "شاكر", "شكر", "الحمد لله", "ممتنن", "نعمة",
        # Arabic — expanded
        "ممتنة", "شاكرة", "نعم الله", "الحمدلله", "سعيد",
        "سعيدة", "بخير", "الله يبارك", "ربي كريم",
        "أشكر الله", "الرضا", "راضي", "راضية", "بركة",
        "الحمد لله على كل شيء", "شكراً لله", "منعم عليّ",
    ],
}

# ---------------------------------------------------------------------------
# Healing themes catalogue
# ---------------------------------------------------------------------------

HEALING_THEMES: Dict[str, Dict[str, Any]] = {
    "mercy": {
        "ar": "رحمة",
        "en": "Mercy",
        "desc_en": "Allah's boundless compassion and care for every soul",
        "desc_ar": "رحمة الله اللامتناهية وعنايته بكل روح",
        "icon": "heart",
        "color": "rose",
    },
    "patience": {
        "ar": "صبر",
        "en": "Patience",
        "desc_en": "Enduring hardship with steadfast trust in Allah's plan",
        "desc_ar": "تحمّل الشدائد بثبات والتوكل على الله",
        "icon": "anchor",
        "color": "amber",
    },
    "hope": {
        "ar": "رجاء",
        "en": "Hope",
        "desc_en": "The certainty that relief and ease are coming",
        "desc_ar": "اليقين بأن الفرج والراحة آتيان",
        "icon": "sun",
        "color": "yellow",
    },
    "forgiveness": {
        "ar": "مغفرة",
        "en": "Forgiveness",
        "desc_en": "Allah's door of repentance is always open",
        "desc_ar": "باب توبة الله مفتوح دائماً",
        "icon": "refresh",
        "color": "green",
    },
    "gratitude": {
        "ar": "شكر",
        "en": "Gratitude",
        "desc_en": "Recognising blessings as a path to inner peace",
        "desc_ar": "التعرف على النعم طريقاً للسلام الداخلي",
        "icon": "star",
        "color": "teal",
    },
    "healing": {
        "ar": "شفاء",
        "en": "Healing",
        "desc_en": "The Quran as a cure for what the heart carries",
        "desc_ar": "القرآن شفاء لما يحمله القلب",
        "icon": "activity",
        "color": "blue",
    },
    "trust": {
        "ar": "توكل",
        "en": "Trust in Allah",
        "desc_en": "Surrendering your worries to the One who holds all affairs",
        "desc_ar": "تسليم همومك لمن بيده كل الأمور",
        "icon": "shield",
        "color": "indigo",
    },
    "strength": {
        "ar": "قوة",
        "en": "Strength",
        "desc_en": "Drawing courage from faith to face life's trials",
        "desc_ar": "استمداد الشجاعة من الإيمان لمواجهة تحديات الحياة",
        "icon": "zap",
        "color": "violet",
    },
    "ruqyah": {
        "ar": "رقية شرعية",
        "en": "Quranic Healing",
        "desc_en": "Healing through authentic Quranic recitations — as taught by the Prophet ﷺ",
        "desc_ar": "الشفاء بتلاوة القرآن الكريم — كما علّمنا النبي ﷺ",
        "icon": "book-open",
        "color": "emerald",
    },
    "tawbah": {
        "ar": "توبة واستغفار",
        "en": "Repentance & Renewal",
        "desc_en": "Turning back to Allah with sincere repentance — the gateway to inner peace",
        "desc_ar": "العودة إلى الله بتوبة صادقة — بوابة السلام الداخلي",
        "icon": "refresh-cw",
        "color": "lime",
    },
    "dhikr": {
        "ar": "ذكر ودعاء",
        "en": "Remembrance & Supplication",
        "desc_en": "Daily dhikr and du'a as spiritual nourishment and emotional healing",
        "desc_ar": "الذكر والدعاء اليومي غذاءً روحياً وشفاءً عاطفياً",
        "icon": "mic",
        "color": "cyan",
    },
    "contentment": {
        "ar": "قناعة ورضا",
        "en": "Contentment & Acceptance",
        "desc_en": "Finding peace through rida (acceptance of Allah's decree) and qana'a (spiritual contentment)",
        "desc_ar": "إيجاد السلام من خلال الرضا بقضاء الله والقناعة الروحية",
        "icon": "feather",
        "color": "sky",
    },
}

# ---------------------------------------------------------------------------
# Verse-emotion-theme guidance bank
# Each entry: surah, ayah_start, (optional ayah_end), theme, bilingual guidance.
# Arabic Quranic text is NEVER stored here — it is fetched from the DB.
# ---------------------------------------------------------------------------

_VERSE_GUIDANCE: Dict[str, List[Dict[str, Any]]] = {
    EmotionCategory.ANXIETY: [
        {
            "surah": 94, "ayah_start": 5, "ayah_end": 6, "theme": "hope",
            "lesson_en": "Allah states this truth twice in two consecutive verses — the repetition is itself a message of reassurance. Hardship is always paired with ease; this is a divine promise, not a vague consolation.",
            "lesson_ar": "كرّر الله هذه الحقيقة في آيتين متتاليتين، والتكرار نفسه رسالة طمأنينة. المشقة مقترنة دائماً باليسر، وهذا وعد إلهي لا مجرد عزاء.",
            "reflection_en": "What 'ease' do you hope will follow your current difficulty?",
            "reflection_ar": "ما اليسر الذي تأمل أن يأتي بعد عسرك الحالي؟",
            "dua_en": "O Allah, You promised that with every hardship comes ease. Grant me relief from my anxiety and fill my heart with trust in Your plan.",
            "dua_ar": "اللهم وعدتَ بأن مع كل عسر يسراً، فارزقني الفرج من قلقي وامنح قلبي الثقة بتدبيرك.",
            "prophet_story": "Prophet Yunus (Jonah) called upon Allah from the darkness of the whale, and relief came.",
        },
        {
            "surah": 2, "ayah_start": 286, "theme": "trust",
            "lesson_en": "Allah does not place a burden on any soul that it cannot bear. Your current struggle is within your capacity — and Allah knows that capacity better than you do.",
            "lesson_ar": "لا يُكلّف الله نفساً إلا وسعها. ما تمرّ به الآن في طاقتك — والله يعلم تلك الطاقة أكثر منك.",
            "reflection_en": "In what ways have you already shown strength you didn't know you had?",
            "reflection_ar": "كيف أظهرت بالفعل قوةً لم تدرك أنك تملكها؟",
            "dua_en": "O Allah, do not burden me beyond what I can bear, and make me steadfast in my trial.",
            "dua_ar": "اللهم لا تحمّلني فوق طاقتي، واجعلني ثابتاً في بلائي.",
        },
        {
            "surah": 65, "ayah_start": 3, "theme": "trust",
            "lesson_en": "Tawakkul — true reliance on Allah — does not mean passivity. It means taking wise action while knowing that outcomes rest with Allah alone.",
            "lesson_ar": "التوكل الحقيقي على الله لا يعني السلبية، بل يعني اتخاذ الخطوات الحكيمة مع إدراك أن النتائج بيد الله وحده.",
            "reflection_en": "What is one step you can take today, and then trust Allah with the rest?",
            "reflection_ar": "ما خطوة واحدة يمكنك اتخاذها اليوم، ثم تتوكل على الله في الباقي؟",
            "dua_en": "O Allah, I have done what I can. I leave the rest to You — You are the best of those who are relied upon.",
            "dua_ar": "اللهم فعلت ما بوسعي، وأكل الأمر إليك، وأنت نعم الوكيل.",
        },
        {
            "surah": 13, "ayah_start": 28, "theme": "healing",
            "lesson_en": "The heart finds its true rest not in circumstances changing, but in turning to Allah. Dhikr (remembrance) is both medicine and anchor.",
            "lesson_ar": "يجد القلب راحته الحقيقية لا في تغيّر الظروف، بل في الالتجاء إلى الله. الذكر دواء ومرساة في آن.",
            "reflection_en": "Try pausing right now: breathe, say 'Alhamdulillah', and notice what shifts.",
            "reflection_ar": "جرّب أن تتوقف الآن: تنفّس، وقل 'الحمد لله'، ولاحظ ما يتغير.",
            "dua_en": "O Allah, make Your remembrance the comfort of my heart and the rest of my soul.",
            "dua_ar": "اللهم اجعل ذكرك راحة قلبي وسكينة روحي.",
        },
    ],

    EmotionCategory.SADNESS: [
        {
            "surah": 93, "ayah_start": 3, "theme": "hope",
            "lesson_en": "This verse was revealed during a period when revelation paused and the Prophet (peace be upon him) felt abandoned. Allah directly denied that abandonment — and the same reassurance extends to every believing heart.",
            "lesson_ar": "نزلت هذه الآية حين انقطع الوحي وشعر النبي صلى الله عليه وسلم بالوحدة. فنفى الله هذا الهجر مباشرةً — وهذه الطمأنينة تمتد لكل قلب مؤمن.",
            "reflection_en": "In what moments have you felt Allah's presence most clearly? Can you return to that feeling now?",
            "reflection_ar": "في أي اللحظات أحسست بوجود الله بشكل أوضح؟ هل تستطيع العودة إلى ذلك الشعور الآن؟",
            "dua_en": "O Allah, I know You have not abandoned me. Help me feel Your closeness in this moment of sadness.",
            "dua_ar": "اللهم أعلم أنك لم تتركني. أعنّي على الإحساس بقربك في هذه اللحظة من الحزن.",
        },
        {
            "surah": 3, "ayah_start": 139, "theme": "strength",
            "lesson_en": "This verse was revealed after a military defeat — yet Allah called the believers 'superior'. True elevation is not about circumstances but about the inner standing that faith provides.",
            "lesson_ar": "نزلت هذه الآية بعد هزيمة في المعركة — ومع ذلك وصف الله المؤمنين بالعلو. الرفعة الحقيقية ليست في الظروف بل في المكانة الداخلية التي يمنحها الإيمان.",
            "reflection_en": "What does it mean to you that Allah calls you 'superior' even in your weakness?",
            "reflection_ar": "ماذا يعني لك أن يصفك الله بالعلو حتى في ضعفك؟",
            "dua_en": "O Allah, lift my spirit. Let not sadness diminish who I am in Your eyes.",
            "dua_ar": "اللهم ارفع روحي، ولا تدع الحزن ينقص مما أنا عليه في عينيك.",
        },
        {
            "surah": 2, "ayah_start": 155, "ayah_end": 156, "theme": "patience",
            "lesson_en": "Allah acknowledges that trials involve real suffering — loss of wealth, health, and people. The response taught here is not denial of pain but a return to one's fundamental identity: belonging to Allah.",
            "lesson_ar": "يُقرّ الله بأن الابتلاء فيه ألم حقيقي — خسارة المال والصحة والأحباء. الاستجابة المعلَّمة هنا ليست إنكار الألم بل العودة للهوية الأساسية: الانتماء إلى الله.",
            "reflection_en": "'We belong to Allah and to Him we return' — how does that phrase land for you today?",
            "reflection_ar": "'إنا لله وإنا إليه راجعون' — كيف تصل إليك هذه العبارة اليوم؟",
            "dua_en": "O Allah, in every loss and trial, let my first response be returning to You.",
            "dua_ar": "اللهم في كل خسارة وابتلاء، اجعل أول استجابتي العودة إليك.",
            "prophet_story": "Prophet Ayyub (Job) endured prolonged suffering yet returned to Allah.",
        },
    ],

    EmotionCategory.GRIEF: [
        {
            "surah": 2, "ayah_start": 155, "ayah_end": 156, "theme": "patience",
            "lesson_en": "Allah validates grief as real. The patient ones are not those who feel nothing — they are those who, while feeling everything, return to Allah.",
            "lesson_ar": "يُثبت الله أن الحزن حقيقي. الصابرون ليسوا من لا يشعرون — بل من يشعرون بكل شيء ثم يرجعون إلى الله.",
            "reflection_en": "What would it look like to hold your grief while also holding onto Allah?",
            "reflection_ar": "كيف يبدو أن تحمل حزنك وتتمسك بالله في الوقت نفسه؟",
            "dua_en": "O Allah, I am in pain. Receive my grief. Grant me patience and closeness to You in this loss.",
            "dua_ar": "اللهم أنا في ألم. تقبّل حزني. ارزقني الصبر والقرب منك في هذا الفقد.",
            "prophet_story": "Prophet Yaqub (Jacob) wept so much for Yusuf that he lost his sight, yet never despaired of Allah.",
        },
        {
            "surah": 12, "ayah_start": 86, "theme": "mercy",
            "lesson_en": "Prophet Yaqub did not suppress his grief — he expressed it directly to Allah. Taking your pain to Allah in prayer is not weakness; it is the deepest form of connection.",
            "lesson_ar": "لم يكبت النبي يعقوب حزنه — بل أفضى به مباشرةً إلى الله. حمل ألمك إلى الله في الدعاء ليس ضعفاً، بل هو أعمق أشكال الصلة.",
            "reflection_en": "What have you not yet told Allah in prayer about what you are carrying?",
            "reflection_ar": "ما الذي لم تقله بعد لله في دعائك عمّا تحمله؟",
            "dua_en": "O Allah, I pour out my grief to You. You are the only One who truly knows and truly hears.",
            "dua_ar": "اللهم أفضي إليك بحزني. أنت وحدك من يعلم حقاً ويسمع حقاً.",
        },
        {
            "surah": 57, "ayah_start": 23, "theme": "trust",
            "lesson_en": "This verse doesn't ask us to be indifferent to loss. It invites us to trust that what we couldn't hold was never ours to hold — it was always in Allah's keeping.",
            "lesson_ar": "لا تطلب هذه الآية منا اللامبالاة تجاه الفقد. بل تدعونا إلى الثقة بأن ما لم نستطع الإمساك به لم يكن لنا أصلاً — كان دائماً في حفظ الله.",
            "reflection_en": "Can you release this to Allah, knowing He held your loved one before you did?",
            "reflection_ar": "هل يمكنك أن تسلّم هذا لله، مدركاً أنه احتضن من تحبه قبلك أنت؟",
            "dua_en": "O Allah, help me to grieve without despair, to remember without forgetting You.",
            "dua_ar": "اللهم أعنّي على الحزن بلا يأس، وعلى الذكر دون نسيانك.",
        },
    ],

    EmotionCategory.FEAR: [
        {
            "surah": 3, "ayah_start": 173, "theme": "trust",
            "lesson_en": "This was said by the companions when warned of an overwhelming army approaching. Their response was not denial of the threat, but a declaration of trust: 'Allah is sufficient for us.'",
            "lesson_ar": "قالها الصحابة حين أُخبروا بجيش عظيم مقبل. لم يكن ردّهم إنكار الخطر بل إعلان التوكل: 'حسبنا الله.'",
            "reflection_en": "What specific fear can you name right now and place in Allah's hands?",
            "reflection_ar": "ما الخوف المحدد الذي يمكنك تسميته الآن وتسليمه بين يدي الله؟",
            "dua_en": "O Allah, You are sufficient for me. You are the best Disposer of all my affairs.",
            "dua_ar": "اللهم أنت حسبي، ونعم الوكيل في كل شأن من شؤوني.",
        },
        {
            "surah": 9, "ayah_start": 51, "theme": "trust",
            "lesson_en": "Fear often comes from imagining outcomes. This verse anchors the heart: nothing will reach you that Allah has not already written. That is not fatalism — it is liberation.",
            "lesson_ar": "غالباً ما يأتي الخوف من توقع النتائج. ترسّخ هذه الآية القلب: لن يصيبك شيء لم يكتبه الله سلفاً. هذا ليس قدرية — بل هو تحرر.",
            "reflection_en": "What are you fearing that is ultimately not in your control — and can you release that to Allah?",
            "reflection_ar": "ما الذي تخافه وهو في نهاية المطاف ليس بيدك؟ هل تستطيع تسليمه لله؟",
            "dua_en": "O Allah, my affairs are in Your hands. What reaches me is by Your decree — give me peace in that truth.",
            "dua_ar": "اللهم أمري بين يديك. ما يصلني هو بقدرك — أعطني السلام في هذه الحقيقة.",
        },
        {
            "surah": 58, "ayah_start": 7, "theme": "mercy",
            "lesson_en": "You are never truly alone in your fear. Allah is present with you at this very moment — not as an abstract idea but as a witnessing, knowing, caring Reality.",
            "lesson_ar": "أنت لست وحيداً حقاً في خوفك. الله موجود معك في هذه اللحظة — ليس كفكرة مجردة بل كحقيقة شاهدة عارفة راعية.",
            "reflection_en": "Sit quietly for a moment and say: 'Allah is with me.' What do you notice?",
            "reflection_ar": "اجلس لحظة بهدوء وقل: 'الله معي.' ماذا تلاحظ؟",
            "dua_en": "O Allah, You are with me. Let that truth be enough to calm what fears me.",
            "dua_ar": "اللهم أنت معي. فليكفِ هذا الحق لتسكين ما أخافني.",
        },
    ],

    EmotionCategory.LONELINESS: [
        {
            "surah": 2, "ayah_start": 186, "theme": "mercy",
            "lesson_en": "Of all verses about the relationship between humans and Allah, this is uniquely intimate: no intermediary is mentioned. When you call, Allah is already near and already listening.",
            "lesson_ar": "من بين كل الآيات عن العلاقة بين الإنسان والله، هذه فريدة في حميميتها: لا وسيط مذكور. حين تدعو، الله قريب بالفعل وسامع بالفعل.",
            "reflection_en": "When did you last speak to Allah as if speaking to someone who is truly present?",
            "reflection_ar": "متى كانت آخر مرة تحدثت مع الله كأنك تتحدث لمن هو حاضر فعلاً؟",
            "dua_en": "O Allah, I feel alone. Remind me through Your nearness that I am never truly alone.",
            "dua_ar": "اللهم أشعر بالوحدة. ذكّرني بقربك أنني لا أكون وحيداً حقاً.",
        },
        {
            "surah": 50, "ayah_start": 16, "theme": "mercy",
            "lesson_en": "Allah knows every thought you have not spoken aloud. That level of closeness is not surveillance — it is intimacy. You are deeply known and deeply present to Allah.",
            "lesson_ar": "يعلم الله كل فكرة لم تنطق بها. هذا القرب ليس مراقبة — بل هو مؤانسة. أنت معروف لله معرفة عميقة وحاضر عنده حضوراً عميقاً.",
            "reflection_en": "What have you been thinking that no one else knows? Share it with Allah now.",
            "reflection_ar": "ما الذي كنت تفكر فيه ولا يعلمه أحد؟ شارك الله به الآن.",
            "dua_en": "O Allah, You know me better than I know myself. Be my companion in my loneliness.",
            "dua_ar": "اللهم أنت تعرفني أكثر مما أعرف نفسي. كن أنيسي في وحدتي.",
        },
        {
            "surah": 9, "ayah_start": 40, "theme": "trust",
            "lesson_en": "These words were spoken in a cave with enemies surrounding them. The Prophet's comfort to Abu Bakr was not a strategy — it was a truth: 'Allah is with us.' That truth is available to you right now.",
            "lesson_ar": "قيلت هذه الكلمات في غار والأعداء محيطون بهم. لم يكن تطمين النبي لأبي بكر استراتيجية بل كان حقيقة: 'الله معنا.' وهذه الحقيقة متاحة لك الآن.",
            "reflection_en": "In your loneliest moment, can you hold onto 'Allah is with me' as your anchor?",
            "reflection_ar": "في أوحش لحظاتك، هل تستطيع التمسك بـ'الله معي' كمرساة لك؟",
            "dua_en": "O Allah, even when I cannot see Your plan, I choose to believe You are with me.",
            "dua_ar": "اللهم حتى حين لا أرى تدبيرك، أختار أن أؤمن بأنك معي.",
        },
    ],

    EmotionCategory.HOPELESSNESS: [
        {
            "surah": 39, "ayah_start": 53, "theme": "hope",
            "lesson_en": "This verse is addressed to those who have 'transgressed against themselves' — not to those who lived perfectly. Despair of Allah's mercy is itself identified as the barrier. The door is open.",
            "lesson_ar": "هذه الآية موجّهة لمن 'أسرفوا على أنفسهم' — لا لمن عاشوا بشكل مثالي. القنوط من رحمة الله هو المانع نفسه. الباب مفتوح.",
            "reflection_en": "What would it mean to stop seeing yourself as the exception to Allah's mercy?",
            "reflection_ar": "ماذا سيعني أن تتوقف عن رؤية نفسك كاستثناء من رحمة الله؟",
            "dua_en": "O Allah, I have given up on myself. But You have told me not to give up on Your mercy. Help me believe that.",
            "dua_ar": "اللهم لقد يئست من نفسي. لكنك أخبرتني ألا أيأس من رحمتك. أعنّي على الإيمان بذلك.",
        },
        {
            "surah": 12, "ayah_start": 87, "theme": "hope",
            "lesson_en": "Prophet Yaqub said this after years of separation from his son, believing him dead. If he could maintain hope across decades of loss, his example is a testament that hope is always possible.",
            "lesson_ar": "قالها النبي يعقوب بعد سنوات من الفراق عن ابنه وهو يظنه ميتاً. إذا كان قادراً على الحفاظ على الأمل عبر عقود من الفقد، فمثاله شهادة على أن الأمل ممكن دائماً.",
            "reflection_en": "What would 'not despairing of Allah's relief' look like for you in the next 24 hours?",
            "reflection_ar": "كيف سيبدو 'عدم اليأس من روح الله' بالنسبة لك في الأربع والعشرين ساعة القادمة؟",
            "dua_en": "O Allah, even when I cannot see relief, teach my heart not to despair of Your promise.",
            "dua_ar": "اللهم حتى حين لا أرى الفرج، علّم قلبي ألا ييأس من وعدك.",
            "prophet_story": "Prophet Yaqub held hope through decades of separation and grief.",
        },
        {
            "surah": 94, "ayah_start": 5, "ayah_end": 6, "theme": "hope",
            "lesson_en": "Notice that in Arabic, 'hardship' (al-'usr) uses the definite article but 'ease' (yusr) does not — scholars note this means the ease spoken of is abundant, not rationed.",
            "lesson_ar": "لاحظ أن 'العُسر' في العربية جاء بـ'ال' التعريف بينما 'يُسر' جاء نكرة — يلاحظ العلماء أن هذا يعني أن اليسر المذكور وفير غير مقيّد.",
            "reflection_en": "What 'ease' — even a small one — can you identify in your life right now?",
            "reflection_ar": "ما 'اليسر' الذي يمكنك تحديده في حياتك الآن، ولو كان صغيراً؟",
            "dua_en": "O Allah, I claim the promise of this verse: after this hardship, ease is coming. Strengthen my heart until it arrives.",
            "dua_ar": "اللهم أتمسك بوعد هذه الآية: بعد هذا العسر يسر آتٍ. قوِّ قلبي حتى يأتي.",
        },
    ],

    EmotionCategory.ANGER: [
        {
            "surah": 3, "ayah_start": 134, "theme": "strength",
            "lesson_en": "Restraining anger is described in this verse as a characteristic of those who earn Allah's love. Anger itself is not condemned — only acting on it destructively. The space between feeling and acting is where character lives.",
            "lesson_ar": "يُوصف كظم الغيظ في هذه الآية بأنه سمة من يكسبون محبة الله. الغضب نفسه غير مذموم — المذموم فقط التصرف به بصورة مدمّرة. المسافة بين الشعور والتصرف هي موطن الشخصية.",
            "reflection_en": "What are you actually protecting through your anger? Is there a hurt underneath it?",
            "reflection_ar": "ما الذي تحمي فعلاً من خلال غضبك؟ هل يكمن تحته جرح ما؟",
            "dua_en": "O Allah, soften what is hardened in me. Let me feel my anger without being ruled by it.",
            "dua_ar": "اللهم ليّن ما تصلّب في داخلي. أجعلني أشعر بغضبي دون أن يتحكم بي.",
        },
        {
            "surah": 41, "ayah_start": 34, "theme": "strength",
            "lesson_en": "Responding with what is better (ahsan) is not weakness — it is power. It transforms enemies into friends and breaks cycles of harm.",
            "lesson_ar": "الاستجابة بما هو أحسن ليست ضعفاً — بل هي قوة. إنها تحوّل الأعداء إلى أصدقاء وتكسر دوامات الأذى.",
            "reflection_en": "In this situation, what would 'better' actually look like in your response?",
            "reflection_ar": "في هذا الموقف، كيف ستبدو الاستجابة 'الأحسن' فعلاً؟",
            "dua_en": "O Allah, give me the wisdom to respond with what is better, even when I want to respond with what is equal.",
            "dua_ar": "اللهم أعطني الحكمة للرد بما هو أحسن، حتى حين أريد الرد بالمثل.",
        },
        {
            "surah": 7, "ayah_start": 199, "theme": "patience",
            "lesson_en": "The word 'jahileen' (ignorant ones) here doesn't mean unintelligent — it means those who act without wisdom. Turning away from provocation is itself an act of inner authority.",
            "lesson_ar": "كلمة 'الجاهلين' هنا لا تعني ناقصي الذكاء — بل تعني من يتصرفون بلا حكمة. الإعراض عن الاستفزاز هو في حد ذاته فعل سيادة داخلية.",
            "reflection_en": "What would you need to believe about yourself to feel secure enough to simply turn away?",
            "reflection_ar": "بماذا تحتاج أن تؤمن عن نفسك لتشعر بالأمان الكافي للإعراض ببساطة؟",
            "dua_en": "O Allah, grant me the inner security that does not need to prove itself through conflict.",
            "dua_ar": "اللهم ارزقني الأمان الداخلي الذي لا يحتاج إلى إثبات نفسه عبر الصراع.",
        },
    ],

    EmotionCategory.STRESS: [
        {
            "surah": 13, "ayah_start": 28, "theme": "healing",
            "lesson_en": "The Arabic word 'tatma'inn' means more than rest — it means a settling, a stilling, a return to ground. The remembrance of Allah is the thing that returns the heart to its natural state of calm.",
            "lesson_ar": "كلمة 'تطمئن' في العربية تعني أكثر من الراحة — تعني الاستقرار والسكون والعودة إلى الأرض. ذكر الله هو ما يعيد القلب إلى حالته الطبيعية من الهدوء.",
            "reflection_en": "What does a few minutes of focused dhikr feel like, compared to the stress you are carrying?",
            "reflection_ar": "كيف تشعر بضع دقائق من الذكر المركّز مقارنةً بالضغط الذي تحمله؟",
            "dua_en": "O Allah, let Your remembrance be my return when stress pulls me away from myself.",
            "dua_ar": "اللهم اجعل ذكرك عودتي حين يشدّني الضغط بعيداً عن نفسي.",
        },
        {
            "surah": 94, "ayah_start": 5, "ayah_end": 6, "theme": "hope",
            "lesson_en": "The Arabic structure of this passage has hardship as singular and ease as something that comes with abundance. This stress is not your final state.",
            "lesson_ar": "البنية العربية لهذا المقطع تجعل العسر مفرداً واليسر شيئاً يأتي بوفرة. هذا الضغط ليس حالتك النهائية.",
            "reflection_en": "What is one small thing you can let go of today to reduce your load?",
            "reflection_ar": "ما شيء صغير واحد يمكنك التخلي عنه اليوم لتخفيف حملك؟",
            "dua_en": "O Allah, relieve me of what I cannot carry, and show me what truly needs my attention.",
            "dua_ar": "اللهم خفّف عني ما لا أطيق حمله، وأرني ما يستحق حقاً اهتمامي.",
        },
        {
            "surah": 65, "ayah_start": 7, "theme": "hope",
            "lesson_en": "This verse addresses those with reduced capacity — 'let him spend according to what Allah has given him.' Allah calibrates your obligations to your actual resources. You are not required to do what you cannot do.",
            "lesson_ar": "تخاطب هذه الآية من قلّت إمكاناته — 'لينفق ذو سعة من سعته.' يُوازن الله التزاماتك مع إمكاناتك الفعلية. لست مطالباً بما لا تستطيع.",
            "reflection_en": "Are you holding yourself to a standard that even Allah does not require of you right now?",
            "reflection_ar": "هل أنت محاسب نفسك بمعيار لا يطلبه الله منك حتى الآن؟",
            "dua_en": "O Allah, ease will come after hardship — I hold Your promise and I wait in trust.",
            "dua_ar": "اللهم إن اليسر سيأتي بعد العسر — أتمسك بوعدك وأنتظر بثقة.",
        },
    ],

    EmotionCategory.GUILT: [
        {
            "surah": 39, "ayah_start": 53, "theme": "forgiveness",
            "lesson_en": "This is one of the most expansive verses about divine forgiveness. 'All sins' — the scope is total. The only condition is turning to Allah. The guilt you carry is a sign you still care. Use it as a turning point, not a prison.",
            "lesson_ar": "هذه من أوسع الآيات في المغفرة الإلهية. 'جميع الذنوب' — النطاق كلي. الشرط الوحيد هو التوجه إلى الله. الذنب الذي تحمله دليل على أنك لا تزال تكترث. استخدمه نقطة تحوّل لا سجناً.",
            "reflection_en": "What would it feel like to accept that your remorse itself is a form of closeness to Allah?",
            "reflection_ar": "كيف ستشعر لو قبلت أن ندمك نفسه شكل من أشكال القرب من الله؟",
            "dua_en": "O Allah, I come to You with all my sins. You said not to despair. I am taking You at Your word.",
            "dua_ar": "اللهم أقبل إليك بكل ذنوبي. قلت لا تيأسوا. أنا آخذ بوعدك.",
        },
        {
            "surah": 3, "ayah_start": 135, "theme": "forgiveness",
            "lesson_en": "Notice the sequence: they wrong themselves, then they remember Allah, then they seek forgiveness. The journey back to Allah starts with remembrance — not with perfection.",
            "lesson_ar": "لاحظ التسلسل: يظلمون أنفسهم، ثم يذكرون الله، ثم يستغفرون. الرحلة العودة إلى الله تبدأ بالذكر — ليس بالكمال.",
            "reflection_en": "Can you make istighfar right now — not as a ritual, but as a genuine reaching out to Allah?",
            "reflection_ar": "هل يمكنك الاستغفار الآن — ليس كطقس بل كتواصل حقيقي مع الله؟",
            "dua_en": "O Allah, I wronged myself. I remember You. I ask Your forgiveness — please forgive me.",
            "dua_ar": "اللهم ظلمت نفسي. أذكرك. أستغفرك — فاغفر لي.",
        },
        {
            "surah": 4, "ayah_start": 110, "theme": "forgiveness",
            "lesson_en": "This verse was revealed for those who had committed serious sins. The prescription is not self-punishment but seeking forgiveness. The door to Allah has no security system that guilt can disable.",
            "lesson_ar": "نزلت هذه الآية لمن ارتكبوا ذنوباً جسيمة. الوصفة ليست عقاب النفس بل طلب المغفرة. باب الله لا يوجد نظام أمان يستطيع الذنب تعطيله.",
            "reflection_en": "What would change for you if you truly believed that Allah's forgiveness was available right now?",
            "reflection_ar": "ما الذي سيتغير إذا آمنت حقاً بأن مغفرة الله متاحة الآن؟",
            "dua_en": "O Allah, I have wronged myself and I seek Your forgiveness. You are Forgiving, Merciful.",
            "dua_ar": "اللهم ظلمت نفسي وأستغفرك. أنت الغفور الرحيم.",
        },
    ],

    EmotionCategory.DOUBT: [
        {
            "surah": 45, "ayah_start": 3, "ayah_end": 4, "theme": "trust",
            "lesson_en": "The Quran repeatedly invites reflection, observation, and questioning as pathways to faith — not obstacles to it. Doubt that seeks is different from doubt that closes. The universe itself is presented as evidence.",
            "lesson_ar": "يدعو القرآن مراراً إلى التأمل والملاحظة والتساؤل كطرق للإيمان — لا عقبات أمامه. الشك الباحث يختلف عن الشك المنغلق. الكون نفسه مقدَّم كدليل.",
            "reflection_en": "What aspect of creation, when you look closely, makes you feel something greater is present?",
            "reflection_ar": "أي جانب من الخلق، حين تتأمله عن كثب، يجعلك تشعر بوجود شيء أعظم؟",
            "dua_en": "O Allah, I have questions. Guide me to what is true. I am seeking, not running away.",
            "dua_ar": "اللهم لدي تساؤلات. اهدني إلى الحق. أنا باحث لا هارب.",
        },
        {
            "surah": 4, "ayah_start": 82, "theme": "healing",
            "lesson_en": "The Quran itself invites pondering as the test of its authenticity. Intellectual engagement with the text is not irreverence — it is the very method the Quran prescribes.",
            "lesson_ar": "يدعو القرآن نفسه إلى التدبر كاختبار لأصالته. التفاعل الفكري مع النص ليس قلة أدب — بل هو المنهج الذي يصفه القرآن.",
            "reflection_en": "What aspect of the Quran, when you engage deeply with it, feels most alive to you?",
            "reflection_ar": "أي جانب من القرآن، حين تتعمق فيه، تشعر بأنه الأكثر حيوية لك؟",
            "dua_en": "O Allah, open my heart to Your book. Let it speak to my doubts, not around them.",
            "dua_ar": "اللهم افتح قلبي لكتابك. دعه يخاطب شكوكي لا يتحاشاها.",
        },
    ],

    EmotionCategory.GRATITUDE: [
        {
            "surah": 14, "ayah_start": 7, "theme": "gratitude",
            "lesson_en": "Gratitude is uniquely positioned in the Quran as something that increases blessing — not as a transaction but as an opening of the heart to receive more. When you notice blessings, more become visible.",
            "lesson_ar": "الشكر موضّع في القرآن بشكل فريد كشيء يزيد النعمة — ليس كمعاملة بل كانفتاح للقلب ليستقبل المزيد. حين تُلاحظ النعم، يصبح المزيد منها مرئياً.",
            "reflection_en": "Name three specific blessings you have today that you may have stopped noticing.",
            "reflection_ar": "سمِّ ثلاث نعم محددة لديك اليوم ربما توقفت عن ملاحظتها.",
            "dua_en": "O Allah, increase me in gratitude. Let thankfulness be how I live, not just what I say.",
            "dua_ar": "اللهم زدني شكراً. اجعل الامتنان طريقة حياتي لا مجرد ما أقوله.",
        },
        {
            "surah": 55, "ayah_start": 13, "theme": "gratitude",
            "lesson_en": "This verse, repeated 31 times in Surah Al-Rahman, names specific blessings of creation. Its rhetorical force is to make dismissal harder — the blessings are real, the denial is the anomaly.",
            "lesson_ar": "تُكرَّر هذه الآية 31 مرة في سورة الرحمن وتُسمّي نعماً خلقية بعينها. قوتها الخطابية تجعل الإنكار أصعب — النعم حقيقية، والإنكار هو الشذوذ.",
            "reflection_en": "Which of Allah's favors have you been most tempted to deny today?",
            "reflection_ar": "أي نعم الله كنت أكثر إغراءً لإنكارها اليوم؟",
            "dua_en": "O Allah, I deny none of Your favors. Alhamdulillah — praise be to You for everything.",
            "dua_ar": "اللهم لا أكذّب بشيء من نعمك. الحمد لله — لك الحمد على كل شيء.",
        },
    ],

    EmotionCategory.GENERAL: [
        {
            "surah": 94, "ayah_start": 5, "ayah_end": 6, "theme": "hope",
            "lesson_en": "Whatever you are facing, this divine promise stands: ease accompanies hardship. That is not a hope — it is a certainty that Allah has declared.",
            "lesson_ar": "مهما كنت تواجه، يبقى هذا الوعد الإلهي قائماً: اليسر مع العسر. ليس هذا أملاً — بل يقين أعلنه الله.",
            "reflection_en": "What is one thing that is still good, even in the midst of what is hard?",
            "reflection_ar": "ما شيء واحد لا يزال جيداً، حتى وسط ما هو صعب؟",
            "dua_en": "O Allah, I turn to You with whatever I am carrying. You know what I cannot yet name.",
            "dua_ar": "اللهم أتوجه إليك بكل ما أحمله. أنت تعلم ما لا أستطيع بعد تسميته.",
        },
        {
            "surah": 13, "ayah_start": 28, "theme": "healing",
            "lesson_en": "In the remembrance of Allah do hearts find rest. This is the prescription the Quran gives for whatever the heart carries.",
            "lesson_ar": "بذكر الله تطمئن القلوب. هذا هو الدواء الذي يصفه القرآن لكل ما يحمله القلب.",
            "reflection_en": "What would it look like to start each morning with even two minutes of deliberate remembrance of Allah?",
            "reflection_ar": "كيف سيبدو أن تبدأ كل صباح بدقيقتين فقط من الذكر المتعمّد لله؟",
            "dua_en": "O Allah, I come to You as I am. Let Your remembrance be the rest my heart cannot find anywhere else.",
            "dua_ar": "اللهم أقبل إليك كما أنا. اجعل ذكرك الراحة التي لا يجدها قلبي في أي مكان آخر.",
        },
        {
            "surah": 10, "ayah_start": 57, "theme": "ruqyah",
            "lesson_en": "This verse is the Quran's own declaration of its healing power — a 'healing for what is in the breasts (chests).' The Arabic word 'shifa'' (شِفَاء) refers to complete removal of illness. Scholars note this healing is both spiritual (diseases of the heart like doubt, grief, and fear) and physical when approached with sincere faith.",
            "lesson_ar": "هذه الآية هي إعلان القرآن عن قدرته الشافية — 'شفاء لما في الصدور'. كلمة 'شفاء' العربية تشير إلى الإزالة الكاملة للمرض. يرى العلماء أن هذا الشفاء روحي (أمراض القلب كالشك والحزن والخوف) وجسدي أيضاً بصدق الإيمان.",
            "reflection_en": "What 'illness of the heart' — doubt, fear, grief, anger — are you bringing to the Quran to be healed today?",
            "reflection_ar": "ما 'مرض القلب' — شك، خوف، حزن، غضب — الذي تحضره إلى القرآن لشفائه اليوم؟",
            "dua_en": "O Allah, make the Quran the spring of my heart, the light of my chest, a departure for my sorrow, and a release for my anxiety.",
            "dua_ar": "اللهم اجعل القرآن ربيع قلبي ونور صدري وجلاء حزني وذهاب همي وغمي.",
        },
    ],
    # -----------------------------------------------------------------------
    # Additional verses for new Ruqyah, Tawbah, Dhikr, and Contentment themes.
    # These entries are tagged with the new theme keys so get_theme_cards()
    # can surface them when a user explores those themes directly.
    # -----------------------------------------------------------------------
    # Repurpose anxiety entries for ruqyah exploration
    "_ruqyah_extra": [
        {
            "surah": 17, "ayah_start": 82, "theme": "ruqyah",
            "lesson_en": "Allah describes the Quran itself as 'a healing and a mercy for the believers.' Ibn Qayyim al-Jawziyyah taught that the Quran heals both physical and spiritual ailments — when the heart of the reciter has sincere faith and reliance on Allah. The key is to recite with presence, reflection (tadabbur), and belief in its healing power.",
            "lesson_ar": "يصف الله القرآن بأنه 'شفاء ورحمة للمؤمنين'. علّم ابن قيم الجوزية أن القرآن يشفي الأمراض الجسدية والروحية — حين يتمتع قلب القارئ بالإيمان الصادق والتوكل على الله. المفتاح هو التلاوة بحضور وتدبر وإيمان بقدرة الشفاء.",
            "reflection_en": "When you recite the Quran, do you experience it as healing? What would it mean to approach each verse as medicine for your heart?",
            "reflection_ar": "حين تتلو القرآن، هل تختبره كشفاء؟ ماذا سيعني أن تتناول كل آية كدواء لقلبك؟",
            "dua_en": "O Allah, make the Quran the spring of my heart, the light of my chest, the departure of my grief, and the release of my anxiety, as Your Prophet ﷺ taught us to ask.",
            "dua_ar": "اللهم اجعل القرآن ربيع قلبي ونور صدري وجلاء حزني وذهاب همي كما علّمنا نبيّك ﷺ أن نسأل.",
        },
        {
            "surah": 2, "ayah_start": 255, "theme": "ruqyah",
            "lesson_en": "Ayat al-Kursi — the Throne Verse — is the greatest verse in the Quran (confirmed by hadith in Sahih Muslim). The Prophet ﷺ taught: 'Whoever recites Ayat al-Kursi after every obligatory prayer, nothing stands between him and entering Paradise except death.' Reciting it before sleep causes an angel to guard you all night and prevents Satan from approaching you (Bukhari). Its healing power comes from its declaration of Allah's absolute sovereignty over all creation.",
            "lesson_ar": "آية الكرسي هي أعظم آية في القرآن (كما ثبت في حديث صحيح مسلم). علّم النبي ﷺ: 'من قرأ آية الكرسي دبر كل صلاة مكتوبة لم يحل بينه وبين دخول الجنة إلا الموت.' قراءتها قبل النوم تجعل ملاكاً يحرسك طوال الليل ويمنع الشيطان من الاقتراب (البخاري). قوتها الشافية تأتي من إعلانها السيادة المطلقة لله على جميع الخلق.",
            "reflection_en": "Have you made Ayat al-Kursi a daily habit? Morning and night, it is one of the most powerful spiritual protections and heart-strengthening practices in the Sunnah.",
            "reflection_ar": "هل جعلت آية الكرسي عادة يومية؟ صباحاً ومساءً، هي من أقوى الحمايات الروحية وممارسات تقوية القلب في السنة.",
            "dua_en": "O Allah, You are Al-Hayy (the Ever-Living) and Al-Qayyum (the Self-Sustaining). There is no deity but You. I seek Your protection through the greatest verse of Your Book.",
            "dua_ar": "اللهم أنت الحي القيوم لا إله إلا أنت. أطلب حمايتك من خلال أعظم آية في كتابك.",
        },
        {
            "surah": 2, "ayah_start": 286, "theme": "ruqyah",
            "lesson_en": "This verse — one of the last two verses of Surah Al-Baqarah — contains a built-in du'a: 'Our Lord, do not burden us beyond what we can bear.' The Prophet ﷺ said these verses were given to him as a special gift on the Night of Isra, and 'whoever recites the last two verses of Surah al-Baqarah at night, they will be sufficient for him' (Bukhari). Scholars interpret 'sufficient' to mean sufficient protection from harm, from Satan, and as reward.",
            "lesson_ar": "تحتوي هذه الآية — إحدى آخر آيتين في سورة البقرة — على دعاء متضمّن: 'ربنا لا تحملنا ما لا طاقة لنا به.' قال النبي ﷺ إن هاتين الآيتين أُعطيتا له هدية في ليلة الإسراء، و'من قرأ الآيتين الأخيرتين من سورة البقرة في ليلة كفتاه' (البخاري). يفسر العلماء 'كفتاه' بأنه يكفيه حمايةً من الأذى ومن الشيطان وثواباً.",
            "reflection_en": "Do you recite the last two verses of Surah Al-Baqarah before sleep? This is among the most authenticated nighttime protections in the Sunnah.",
            "reflection_ar": "هل تتلو آخر آيتين من سورة البقرة قبل النوم؟ هذا من أكثر أعمال الحماية الليلية ثبوتاً في السنة.",
            "dua_en": "Our Lord, do not burden us beyond what we can bear. Pardon us, forgive us, and have mercy on us. You are our Protector — so grant us victory over the disbelieving people.",
            "dua_ar": "ربنا لا تحملنا ما لا طاقة لنا به واعف عنا واغفر لنا وارحمنا أنت مولانا فانصرنا على القوم الكافرين.",
        },
    ],
    "_tawbah_extra": [
        {
            "surah": 2, "ayah_start": 222, "theme": "tawbah",
            "lesson_en": "Allah loves those who repent. The Arabic verb 'tawwab' (توّاب) is in the intensive form — meaning Allah turns again and again in forgiveness to those who turn again and again to Him. Tawbah is not a one-time act; it is a continuous relationship of returning. No matter how many times you have strayed, Allah's love for those who repent is constant and intense.",
            "lesson_ar": "الله يحب التوابين. الفعل 'توّاب' عربياً يأتي على صيغة المبالغة — يعني أن الله يتوب مراراً وتكراراً على من يعودون إليه مراراً وتكراراً. التوبة ليست فعلاً واحداً؛ بل هي علاقة مستمرة من العودة. مهما ابتعدت، محبة الله للتوابين ثابتة وعميقة.",
            "reflection_en": "Tawbah means 'to return.' What would it mean for you to 'return' to Allah today — not as a one-time act, but as a daily orientation of the heart?",
            "reflection_ar": "التوبة تعني 'العودة'. ماذا ستعني 'العودة' إلى الله اليوم — ليس فعلاً واحداً بل توجهاً يومياً للقلب؟",
            "dua_en": "O Allah, You love those who turn back to You repeatedly. I am returning to You now. Receive my tawbah and envelope me in Your love.",
            "dua_ar": "اللهم أنت تحب التوابين. أنا أعود إليك الآن. تقبّل توبتي وأحطني بمحبتك.",
        },
        {
            "surah": 25, "ayah_start": 70, "theme": "tawbah",
            "lesson_en": "This verse promises something extraordinary: that for those who repent sincerely, Allah does not just forgive — He actively converts their bad deeds into good deeds. Ibn Kathir explained this means Allah transforms the very record of evil into a record of good through His mercy. This is the transformative power of sincere tawbah.",
            "lesson_ar": "تعد هذه الآية بشيء استثنائي: أن من يتوب توبةً صادقة، الله لا يغفر فقط — بل يُبدّل سيئاته حسنات فعلاً. وضّح ابن كثير أن هذا يعني أن الله يحوّل سجل الشر إلى سجل خير من خلال رحمته. هذه هي القوة التحويلية للتوبة الصادقة.",
            "reflection_en": "If Allah can literally transform your past wrongs into good deeds through sincere repentance, what does that mean for how you see your history?",
            "reflection_ar": "إذا كان الله قادراً على تحويل ماضيك من شر إلى حسنات بتوبة صادقة، فماذا يعني ذلك لنظرتك إلى تاريخك؟",
            "dua_en": "O Allah, transform my regret into resolve, and my past mistakes into the foundation of a better future. You are Al-Tawwab, the Ever-Accepting of repentance.",
            "dua_ar": "اللهم حوّل ندمي إلى عزم وأخطاء ماضيّ إلى أساس لمستقبل أفضل. أنت التواب.",
        },
        {
            "surah": 110, "ayah_start": 3, "theme": "tawbah",
            "lesson_en": "This final revelation to the Prophet ﷺ came near the end of his life and contains the essence of Islamic renewal: glorify, praise, and seek forgiveness. The Prophet ﷺ, despite having all his sins forgiven, still increased in istighfar after this verse. It teaches that seeking forgiveness is not just for sinners — it is the highest form of worship and the most purifying act for any soul.",
            "lesson_ar": "نزل هذا الوحي الأخير على النبي ﷺ قرب نهاية حياته ويحمل جوهر التجديد الإسلامي: سبّح واحمد واستغفر. النبي ﷺ رغم مغفرة ذنوبه كلها، ازداد في الاستغفار بعد هذه الآية. هذا يعلّمنا أن طلب المغفرة ليس فقط للمذنبين — بل هو أرقى أشكال العبادة وأطهر فعل لأي روح.",
            "reflection_en": "The Prophet ﷺ made istighfar 100 times per day — not out of sin-consciousness but as a form of love and closeness to Allah. How might you integrate this practice?",
            "reflection_ar": "كان النبي ﷺ يستغفر 100 مرة يومياً — ليس بسبب وعي بالذنب بل كشكل من أشكال الحب والقرب من الله. كيف يمكنك تضمين هذه الممارسة في حياتك؟",
            "dua_en": "O Allah, I glorify You with praise. I turn to You seeking Your forgiveness. You are Al-Ghafoor (the Truly Forgiving) Al-Wadood (the Most Loving) Al-Tawwab (the Ever-Accepting of repentance).",
            "dua_ar": "اللهم سبحانك بحمدك. أتوجه إليك طالباً مغفرتك. أنت الغفور الودود التواب.",
        },
    ],
    "_dhikr_extra": [
        {
            "surah": 33, "ayah_start": 41, "theme": "dhikr",
            "lesson_en": "Allah directly commands 'abundant remembrance' (dhikran kathira — ذِكْراً كَثِيرًا). The word 'kathira' means much, frequent, plentiful. This is not a gentle suggestion — it is a divine directive. Ibn Qayyim al-Jawziyyah wrote that the heart is revived by dhikr the way a dead land is revived by rain. Daily, systematic dhikr is preventive medicine for the soul.",
            "lesson_ar": "يأمر الله مباشرةً بالذكر الكثير (ذكراً كثيراً). كلمة 'كثيراً' تعني وفيراً متكرراً غزيراً. هذا ليس اقتراحاً لطيفاً — بل توجيه إلهي. كتب ابن قيم الجوزية أن القلب يُحيا بالذكر كما تُحيا الأرض الميتة بالمطر. الذكر اليومي المنتظم دواء وقائي للروح.",
            "reflection_en": "Ibn Qayyim listed over 70 benefits of dhikr for the heart and soul. What dhikr practice — even 5 minutes daily — could you commit to starting today?",
            "reflection_ar": "ذكر ابن القيم أكثر من 70 فائدة للذكر للقلب والروح. ما ممارسة ذكر — حتى 5 دقائق يومياً — يمكنك الالتزام بالبدء بها اليوم؟",
            "dua_en": "O Allah, make me among those who remember You abundantly — in the morning, in the evening, and in every moment between.",
            "dua_ar": "اللهم اجعلني من الذاكرين لك كثيراً في الصباح والمساء وفي كل لحظة بينهما.",
        },
        {
            "surah": 2, "ayah_start": 152, "theme": "dhikr",
            "lesson_en": "This verse contains a divine reciprocal promise: 'Remember Me, and I will remember you.' The word 'adhkurukum' means Allah will mention you — to His angels, in His highest company. When you remember Allah, Allah remembers you. This transforms dhikr from a religious obligation into an intimate, mutual exchange between the servant and the Lord of all worlds.",
            "lesson_ar": "تتضمن هذه الآية وعداً إلهياً متبادلاً: 'اذكروني أذكركم'. كلمة 'أذكركم' تعني أن الله سيذكرك — لملائكته في أعلى ملأ. حين تذكر الله يذكرك الله. هذا يحوّل الذكر من التزام ديني إلى تبادل حميم متبادل بين العبد ورب العالمين.",
            "reflection_en": "If you truly believed that every time you say 'Subhanallah' Allah speaks of you among His angels, how would that change your dhikr practice?",
            "reflection_ar": "لو آمنت حقاً بأن في كل مرة تقول 'سبحان الله' يذكرك الله بين ملائكته، كيف سيغير ذلك ممارسة ذكرك؟",
            "dua_en": "O Allah, I remember You now. Be my witness. Remember me as You promised — with forgiveness, with mercy, with Your most beautiful names.",
            "dua_ar": "اللهم أذكرك الآن. كن شاهداً. اذكرني كما وعدت — بالمغفرة والرحمة وأسمائك الحسنى.",
        },
        {
            "surah": 29, "ayah_start": 45, "theme": "dhikr",
            "lesson_en": "This verse teaches that salah (prayer) prevents wrongdoing — but it then adds 'and the remembrance of Allah is greater.' The scholars explain that salah is itself a form of dhikr, but dhikr that continues beyond salah — in daily life, in the heart — is even more powerful as a preventive and healing force. The most comprehensive dhikr practice is a life lived in awareness of Allah.",
            "lesson_ar": "تعلّمنا هذه الآية أن الصلاة تنهى عن الفحشاء والمنكر — لكنها تضيف 'ولذكر الله أكبر'. يوضح العلماء أن الصلاة في حد ذاتها شكل من أشكال الذكر، لكن الذكر المستمر بعد الصلاة — في الحياة اليومية وفي القلب — أقوى كقوة وقائية وشافية. أشمل ممارسة للذكر هي حياة تُعاش بوعي بالله.",
            "reflection_en": "Salah is your five structured meetings with Allah each day. How might you carry that awareness of His presence into the moments between your prayers?",
            "reflection_ar": "الصلاة هي لقاءاتك الخمس المنظمة مع الله كل يوم. كيف تحمل وعي حضوره إلى اللحظات بين صلواتك؟",
            "dua_en": "O Allah, let my prayer be the peak of my remembrance, and let every moment between prayers be its continuation. Make dhikr the rhythm of my life.",
            "dua_ar": "اللهم اجعل صلاتي ذروة ذكري وكل لحظة بين الصلوات امتداداً له. اجعل الذكر إيقاع حياتي.",
        },
    ],
    "_contentment_extra": [
        {
            "surah": 89, "ayah_start": 27, "theme": "contentment",
            "lesson_en": "The soul described as 'mutma'inna' (مطمئنة) — the tranquil, settled soul — is called to return to its Lord in a state of rida (mutual contentment). Note: this is called 'al-nafs al-mutma'inna' — a Quranic term for the highest state of the soul, at peace with itself and with Allah. This state is achievable in this life through sustained tawakkul, gratitude, and acceptance of Allah's decree.",
            "lesson_ar": "النفس الموصوفة بـ'المطمئنة' — النفس الهادئة المستقرة — مدعوة للعودة إلى ربها في حالة رضا متبادل. لاحظ: تُسمى 'النفس المطمئنة' — مصطلح قرآني لأعلى حالات النفس، المتصالحة مع ذاتها ومع الله. هذه الحالة قابلة للتحقيق في هذه الحياة من خلال التوكل المستمر والشكر والرضا بقضاء الله.",
            "reflection_en": "The nafs mutma'inna is not achieved by circumstances improving — it is achieved when the heart finds peace with Allah regardless of circumstances. What would that look like for you?",
            "reflection_ar": "النفس المطمئنة لا تتحقق بتحسّن الظروف — بل تتحقق حين يجد القلب السلام مع الله بصرف النظر عن الظروف. كيف سيبدو ذلك بالنسبة لك؟",
            "dua_en": "O Allah, make me of those whose souls are at rest — returning to You content with You and You content with them.",
            "dua_ar": "اللهم اجعلني من أصحاب النفوس المطمئنة — الراجعة إليك راضيةً مرضية.",
        },
        {
            "surah": 16, "ayah_start": 97, "theme": "contentment",
            "lesson_en": "Allah promises a 'good life' (hayatan tayyibah — حياةً طيبةً) to those who do righteous deeds with faith, regardless of their gender. Ibn Kathir explained that this 'good life' is not material wealth — it is contentment (qana'a), peace of heart, and sufficiency in whatever one has. True contentment is a divine gift that transforms any circumstances into a blessed life.",
            "lesson_ar": "يعد الله بـ'حياة طيبة' لمن يعمل صالحاً مع الإيمان بصرف النظر عن جنسه. أوضح ابن كثير أن هذه 'الحياة الطيبة' ليست ثروة مادية — بل هي القناعة وسلام القلب والاكتفاء بما لديه. القناعة الحقيقية هبة إلهية تحوّل أي ظروف إلى حياة مباركة.",
            "reflection_en": "The Quran promises a 'good life' based on faith and righteous action — not on changing circumstances. What would it feel like to live that promise today, exactly as things are?",
            "reflection_ar": "يعد القرآن بـ'حياة طيبة' مبنية على الإيمان والعمل الصالح — لا على تغيّر الظروف. كيف سيبدو عيش ذلك الوعد اليوم بالضبط كما هي الأمور؟",
            "dua_en": "O Allah, grant me qana'a (spiritual contentment) — to find abundance in what I have, peace in what You have written, and beauty in the life You have given me.",
            "dua_ar": "اللهم ارزقني القناعة — أن أجد الغنى فيما عندي والسلام فيما كتبت والجمال في الحياة التي وهبتني.",
        },
        {
            "surah": 9, "ayah_start": 59, "theme": "contentment",
            "lesson_en": "This verse describes those who say 'Hasbiyallah' (حسبي الله — Allah is sufficient for me) with full faith. Ibn Qayyim called this phrase one of the most powerful for healing discontentment. It is not resignation but a declaration that Allah's provision, wisdom, and care are truly sufficient. The one who truly believes this finds freedom from comparison, envy, and anxious striving.",
            "lesson_ar": "تصف هذه الآية من يقول 'حسبي الله' بإيمان كامل. أطلق ابن القيم على هذه العبارة أنها من أقوى العبارات لشفاء الاستياء. إنها ليست استسلاماً بل إعلان بأن رزق الله وحكمته ورعايته كافية حقاً. من يؤمن بذلك حقاً يجد حرية من المقارنة والحسد والسعي القلق.",
            "reflection_en": "Say 'Hasbiyallah' right now — slowly and with full meaning. What happens in your heart when you truly hand your sufficiency over to Allah?",
            "reflection_ar": "قل 'حسبي الله' الآن — ببطء ومعنى كامل. ما الذي يحدث في قلبك حين تُسلّم اكتفاءك حقاً إلى الله؟",
            "dua_en": "O Allah, You are sufficient for me. I release what I cannot control. I accept what You have given me. You are my Lord and You are enough.",
            "dua_ar": "اللهم أنت حسبي. أُطلق ما لا أستطيع السيطرة عليه. أقبل ما أعطيتني. أنت ربي وأنت كافٍ.",
        },
    ],
}

# Emotion → primary recommended themes
_EMOTION_THEMES: Dict[str, List[str]] = {
    EmotionCategory.ANXIETY:     ["trust", "hope", "dhikr", "ruqyah"],
    EmotionCategory.SADNESS:     ["hope", "mercy", "patience", "ruqyah"],
    EmotionCategory.GRIEF:       ["patience", "mercy", "trust", "ruqyah"],
    EmotionCategory.FEAR:        ["trust", "mercy", "strength", "ruqyah"],
    EmotionCategory.LONELINESS:  ["mercy", "hope", "trust", "dhikr"],
    EmotionCategory.HOPELESSNESS:["hope", "mercy", "forgiveness", "ruqyah"],
    EmotionCategory.ANGER:       ["patience", "strength", "forgiveness", "dhikr"],
    EmotionCategory.STRESS:      ["healing", "trust", "hope", "dhikr"],
    EmotionCategory.GUILT:       ["forgiveness", "mercy", "tawbah", "hope"],
    EmotionCategory.DOUBT:       ["trust", "healing", "patience", "ruqyah"],
    EmotionCategory.GRATITUDE:   ["gratitude", "mercy", "contentment", "hope"],
    EmotionCategory.GENERAL:     ["mercy", "hope", "ruqyah", "dhikr"],
}

# Flat list of all extra-theme verse entries (not bound to a single emotion)
_EXTRA_THEME_VERSES: List[Dict[str, Any]] = (
    _VERSE_GUIDANCE.pop("_ruqyah_extra", [])
    + _VERSE_GUIDANCE.pop("_tawbah_extra", [])
    + _VERSE_GUIDANCE.pop("_dhikr_extra", [])
    + _VERSE_GUIDANCE.pop("_contentment_extra", [])
)

# ---------------------------------------------------------------------------
# Emotion classifier
# ---------------------------------------------------------------------------

def _keyword_classify(text: str) -> str:
    """Pure keyword-based classification. Returns EmotionCategory string."""
    text_lower = text.lower()
    scores: Dict[str, int] = {}
    for emotion, keywords in _EMOTION_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                score += 2
            elif kw in text_lower:
                score += 1
        scores[emotion] = score
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else EmotionCategory.GENERAL


def classify_emotion(text: str) -> str:
    """
    Classify the emotional content of `text`.

    Pipeline (Phase T4):
    1. If Arabic-dominant text → keyword classifier (full Arabic keyword bank).
    2. If NLI classifier is enabled and confident (≥ threshold) → NLI result.
    3. Keyword fallback for English when NLI is unavailable or under-confident.
    """
    from app.core.config import get_settings
    from app.services.emotion_classifier import get_classifier, is_arabic_dominant

    # Arabic text: keywords already cover it well; NLI model is English-only.
    if is_arabic_dominant(text):
        return _keyword_classify(text)

    settings = get_settings()
    if settings.emotion_classifier_enabled:
        clf = get_classifier(
            model_name=settings.emotion_model_name,
            confidence_threshold=settings.emotion_confidence_threshold,
        )
        predicted, _confidence = clf.classify(text)
        if predicted:
            return predicted

    # Keyword fallback (model unavailable, disabled, or low confidence)
    return _keyword_classify(text)


# ---------------------------------------------------------------------------
# Guidance card builder
# ---------------------------------------------------------------------------

async def build_guidance_cards(
    emotion: str,
    db: AsyncSession,
    max_cards: int = 3,
) -> List[Dict[str, Any]]:
    """
    Fetch pre-curated verse guidance entries for an emotion.

    For each entry, the verse text is retrieved from the QuranVerse table.
    Entries without a matching DB verse are silently skipped.
    """
    entries = _VERSE_GUIDANCE.get(emotion, _VERSE_GUIDANCE[EmotionCategory.GENERAL])
    cards: List[Dict[str, Any]] = []

    for entry in entries[:max_cards]:
        surah = entry["surah"]
        ayah_start = entry["ayah_start"]
        ayah_end = entry.get("ayah_end", ayah_start)

        # Fetch the first (or only) verse of the range
        result = await db.execute(
            select(QuranVerse).where(
                QuranVerse.sura_no == surah,
                QuranVerse.aya_no == ayah_start,
            )
        )
        verse = result.scalar_one_or_none()
        if verse is None:
            continue

        reference = (
            f"{surah}:{ayah_start}"
            if ayah_start == ayah_end
            else f"{surah}:{ayah_start}-{ayah_end}"
        )

        card: Dict[str, Any] = {
            "reference": reference,
            "surah": surah,
            "ayah_start": ayah_start,
            "ayah_end": ayah_end,
            "surah_name_ar": verse.sura_name_ar,
            "surah_name_en": verse.sura_name_en,
            "text_uthmani": verse.text_uthmani,
            "text_imlaei": verse.text_imlaei,
            "theme": entry["theme"],
            "theme_ar": HEALING_THEMES.get(entry["theme"], {}).get("ar", entry["theme"]),
            "theme_en": HEALING_THEMES.get(entry["theme"], {}).get("en", entry["theme"]),
            "lesson_en": entry["lesson_en"],
            "lesson_ar": entry["lesson_ar"],
            "reflection_en": entry["reflection_en"],
            "reflection_ar": entry["reflection_ar"],
            "dua_en": entry["dua_en"],
            "dua_ar": entry["dua_ar"],
            "prophet_story": entry.get("prophet_story"),
        }
        cards.append(card)

    return cards


def get_recommended_themes(emotion: str) -> List[str]:
    """Return recommended healing theme keys for a given emotion."""
    return _EMOTION_THEMES.get(emotion, _EMOTION_THEMES[EmotionCategory.GENERAL])


async def get_theme_cards(
    theme: str,
    db: AsyncSession,
    max_cards: int = 4,
) -> List[Dict[str, Any]]:
    """
    Retrieve guidance cards for a specific healing theme, pulling from
    all emotions that have an entry with that theme, plus the dedicated
    extra-theme verse bank (_EXTRA_THEME_VERSES).
    """
    seen_refs: set[str] = set()
    cards: List[Dict[str, Any]] = []

    # Prioritise dedicated theme verses first (ruqyah, tawbah, dhikr, contentment)
    all_entries: List[Dict[str, Any]] = list(_EXTRA_THEME_VERSES) + [
        e for entries in _VERSE_GUIDANCE.values() for e in entries
    ]

    for entry in all_entries:
        if len(cards) >= max_cards:
            break
        if entry["theme"] != theme:
            continue
        ref = f"{entry['surah']}:{entry['ayah_start']}"
        if ref in seen_refs:
            continue
        seen_refs.add(ref)

        result = await db.execute(
            select(QuranVerse).where(
                QuranVerse.sura_no == entry["surah"],
                QuranVerse.aya_no == entry["ayah_start"],
            )
        )
        verse = result.scalar_one_or_none()
        if verse is None:
            continue

        ayah_end = entry.get("ayah_end", entry["ayah_start"])
        reference = (
            f"{entry['surah']}:{entry['ayah_start']}"
            if entry["ayah_start"] == ayah_end
            else f"{entry['surah']}:{entry['ayah_start']}-{ayah_end}"
        )

        cards.append({
            "reference": reference,
            "surah": entry["surah"],
            "ayah_start": entry["ayah_start"],
            "ayah_end": ayah_end,
            "surah_name_ar": verse.sura_name_ar,
            "surah_name_en": verse.sura_name_en,
            "text_uthmani": verse.text_uthmani,
            "text_imlaei": verse.text_imlaei,
            "theme": theme,
            "theme_ar": HEALING_THEMES.get(theme, {}).get("ar", theme),
            "theme_en": HEALING_THEMES.get(theme, {}).get("en", theme),
            "lesson_en": entry["lesson_en"],
            "lesson_ar": entry["lesson_ar"],
            "reflection_en": entry["reflection_en"],
            "reflection_ar": entry["reflection_ar"],
            "dua_en": entry["dua_en"],
            "dua_ar": entry["dua_ar"],
            "prophet_story": entry.get("prophet_story"),
        })

    return cards
