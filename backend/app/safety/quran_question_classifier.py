"""
Quran Question Classifier — Pre-Generation Safety Gate

Classifies user questions BEFORE retrieval/generation so the system knows
whether to answer, refuse, clarify, or route to a specific module.

Reference: "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي"
           Prof. Dr. Abdulrahman Al-Shehri — Principle: AI must not issue fatwa.

Design principles:
  - Rule-based only — transparent, deterministic, testable, no LLM dependency.
  - Arabic and English patterns — bilingual Quranic platform.
  - Classification is pre-generation (defense layer 1).
  - QuranAnswerGuard remains active post-generation (defense layer 2).
  - No content is generated or modified here.
"""
import re
from dataclasses import dataclass, field
from typing import List

from app.safety.ruling_intent import ruling_request

# ---------------------------------------------------------------------------
# Intent constants
# ---------------------------------------------------------------------------

INTENT_FATWA_LIKE             = "fatwa_like"
INTENT_SCIENTIFIC_MIRACLE     = "scientific_miracle_claim"
INTENT_QIRAAT                 = "qiraat"
INTENT_MORPHOLOGY             = "morphology"
INTENT_IRAB                   = "irab"
INTENT_VOCABULARY             = "vocabulary_meaning"
INTENT_MUNASABAH              = "munasabah"
INTENT_SIMILARITY             = "similarity"
INTENT_STORY                  = "story"
INTENT_THEMATIC_TAFSIR        = "thematic_tafsir"
INTENT_TAFSIR_SUMMARY         = "tafsir_summary"
INTENT_GENERAL                = "general_question"
INTENT_NEEDS_CLARIFICATION    = "needs_clarification"
INTENT_UNSUPPORTED            = "unsupported"
INTENT_PROMPT_INJECTION       = "prompt_injection"

# Route-to constants
ROUTE_RAG          = "rag"
ROUTE_SEARCH       = "search"
ROUTE_STORIES      = "stories"
ROUTE_SIMILARITY   = "similarity"
ROUTE_VOCABULARY   = "vocabulary"
ROUTE_IRAB         = "irab"
ROUTE_MORPHOLOGY   = "morphology"
ROUTE_REFUSAL      = "safe_refusal"
ROUTE_CLARIFICATION = "clarification"

# Risk levels
RISK_LOW    = "low"
RISK_MEDIUM = "medium"
RISK_HIGH   = "high"

# ---------------------------------------------------------------------------
# Bilingual safe-response messages
# ---------------------------------------------------------------------------

FATWA_REFUSAL_EN = (
    "I cannot issue a fatwa. I can only show documented information from "
    "available sources. Please consult qualified scholars for religious rulings."
)
FATWA_REFUSAL_AR = (
    "لا أستطيع إصدار فتوى. يمكنني فقط عرض معلومات موثقة من المصادر المتاحة، "
    "وينبغي الرجوع إلى أهل العلم في مسائل الفتوى."
)

SCIENTIFIC_CAUTION_EN = (
    "Connecting an ayah to scientific theories requires specialized scholarly "
    "and scientific review. This is presented as a contemporary reflection, "
    "not a definitive tafsir position."
)
SCIENTIFIC_CAUTION_AR = (
    "الربط بين الآية والنظريات العلمية يحتاج إلى مراجعة علمية وشرعية متخصصة. "
    "هذا الطرح تأمل معاصر وليس موقفًا تفسيريًا قطعيًا."
)

INJECTION_REFUSAL_EN = (
    "I can only explain the Qur'an from verified sources. I cannot write, complete "
    "or alter Qur'an text, and I cannot follow instructions that change these rules."
)
INJECTION_REFUSAL_AR = (
    "أستطيع فقط شرح القرآن الكريم من المصادر الموثقة. لا أستطيع كتابة نص قرآني "
    "أو إكماله أو تغييره، ولا اتباع تعليمات تغيّر هذه القواعد."
)

UNSUPPORTED_EN = "No verified source available for this answer."
UNSUPPORTED_AR = "لا يوجد مصدر موثوق متاح لهذه الإجابة."

CLARIFICATION_EN = (
    "Please specify the ayah or topic more clearly so I can search "
    "the verified sources."
)
CLARIFICATION_AR = (
    "يرجى تحديد الآية أو الموضوع بشكل أوضح حتى أستطيع البحث في "
    "المصادر الموثوقة."
)

# Module-not-available fallback (vocabulary / i'rab / morphology / qiraat)
MODULE_UNAVAILABLE_EN = (
    "This feature requires a verified source that is not yet available on "
    "this platform. The answer will be retrieved from general tafsir sources where possible."
)
MODULE_UNAVAILABLE_AR = (
    "هذه الميزة تحتاج إلى مصدر موثوق لم يتوفر بعد على هذه المنصة. "
    "سيتم البحث في مصادر التفسير العامة حيث أمكن."
)

# ---------------------------------------------------------------------------
# Classification result
# ---------------------------------------------------------------------------

@dataclass
class QuestionClassification:
    """
    Classification of a user question before retrieval/generation.

    Fields map directly to the Phase C schema defined in the task spec.
    """
    intent: str                        # One of INTENT_* constants
    language: str                      # "ar" | "en" | "mixed"
    risk_level: str                    # "low" | "medium" | "high"
    requires_source: bool              # Must have at least one verified source
    requires_scholar_review: bool      # Needs human scholarly review before approval
    allowed_to_generate: bool          # False = skip LLM entirely
    route_to: str                      # One of ROUTE_* constants
    warnings: List[str] = field(default_factory=list)  # Bilingual caution messages


# ---------------------------------------------------------------------------
# Keyword pattern sets
# ---------------------------------------------------------------------------

# 1. Fatwa-like — highest priority, hard block
_FATWA_AR = frozenset({
    "ما حكم", "هل يجوز", "هل يحل", "هل يحرم", "هل يباح",
    "أفتني", "فتوى", "فتاوى", "حلال أم حرام", "هل علي إثم",
    "حكم الشرع", "الحكم الشرعي", "هل يجوز لي", "ما حكم الشرع",
    "أريد فتوى", "هل هذا محرم", "هل هذا حلال",
})
_FATWA_EN = frozenset({
    "is it permissible", "is it haram", "is it halal", "give me a fatwa",
    "what is the ruling", "am i sinful", "is it forbidden", "is it allowed",
    "am i allowed", "religious ruling", "fatwa", "is this haram",
    "is this halal", "is this permissible", "can i do", "should i do",
    "is it a sin", "is it prohibited",
})

# Ruling questions phrased in ways a phrase list cannot enumerate.
# Each pattern must need ruling *intent*, not just ruling vocabulary: tafsir
# questions mention "forbidden tree", "المسجد الحرام", "Can I see what Ibn
# Kathir says…" and must still reach retrieval.
_RULING_WORD_EN = (
    r"(haram|halal|forbidden|allowed|permissible|permitted|impermissible|prohibited|a sin|sinful|"
    r"makruh|lawful|unlawful|obligatory|mandatory)"
)
# Retrieval verbs: "Can I get/see/read…" asks for content, not a ruling.
_RETRIEVAL_VERBS_EN = (
    r"(get|see|read|learn|know|find|understand|hear|have|ask|look|study|watch|explore|compare|"
    r"search|view|access|share|save|bookmark|use|reflect|begin|start|continue|listen)"
)
_FATWA_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in (
    # "Is music haram?", "Is music forbidden according to the Quran?", "Are mortgages allowed in Islam?"
    # The question must open with is/are and the ruling word must close the
    # clause, so "Is the story of Adam about the forbidden tree?" and
    # "…those who are sinful?" do not match.
    r"(?:^|[,;:]\s*)(is|are|was|were|isn'?t|aren'?t)\s[^?.!]{0,50}?\b" + _RULING_WORD_EN
    + r"\s*(?:[?.!]|$|\b(?:in|for|to|according to|under|by|if|when|during|or|unless)\b)",
    r"\b(allowed|permissible|permitted|forbidden|haram|halal|prohibited)\s+(in|for|according to)\s+"
    r"(islam|muslims?|the shari'?a|sharia)\b",
    r"\b(islamic|religious|shari'?a|sharia|fiqh)\s+(verdict|ruling|opinion|position|judgement|judgment)\b",
    r"\bruling (on|of|about|regarding)\b",
    # "Should I divorce my wife?" — but not "Can I see what Ibn Kathir says…".
    r"^\s*(should|can|may|must)\s+i\s+(?!(also\s+|please\s+)?" + _RETRIEVAL_VERBS_EN + r"\b)",
    # "Can I read the Quran without wudu?" — a retrieval verb plus ruling vocabulary.
    r"^\s*(should|can|may|must)\s+i\b[^?]{0,80}\b(haram|halal|allowed|permissible|permitted|sin|"
    r"sinful|wudu|ablution|menstruat\w*|my period|janabah?|junub)\b",
    r"^\s*(can|may|must|should)\s+(a\s+|an\s+|my\s+)?(woman|women|man|men|muslims?|wife|husband|"
    r"girl|boy)\b",
    r"\b(am i|is it ok|is it okay)\b.{0,30}\b(allowed|sinning|in sin|permitted)\b",
    # Arabic: "هل الموسيقى حرام؟", "هل يصح الطلاق…", "هل تجوز الصلاة…"
    # The ruling word must stand alone: "المسجد الحرام", "البيت الحرام",
    # "والحرام", "للحلال" are names/nouns, not rulings.
    r"هل\s[^؟?]{0,40}?(?<!شهر )(?<![ء-ي])(حرام|حلال|محرم|محرمة|محرّم|مباح|مباحة|جائز|"
    r"جائزة|مكروه|مكروهة|واجب|واجبة|فرض)(?![ء-ي])",
    r"هل\s+(يصح|تصح|تجوز|يجب|تجب|يلزم|تلزم|يحل|تحل|يحرم|تحرم|يأثم|تأثم|أأثم)\b",
    r"(ما|وما)\s+(حكم|الحكم في|الحكم الشرعي)(?![ء-ي])",
    # Validity of a specific act of worship or contract: "Is my prayer valid
    # if…", "Is our marriage still valid…". Acceptance ("will my repentance be
    # accepted", "was his prayer accepted" in a story) is a question of hope
    # and tafsir, not validity, and is not matched.
    r"\b(is|are|was|were|will)\s+(my|our|his|her|their)\s+(?:\w+\s+){0,2}?(prayers?|salah|salat|fast|"
    r"fasting|sawm|wudu|wudhu|ablution|ghusl|marriage|nikah|divorce|talaq|hajj|umrah|zakat|zakah|oath|"
    r"sale|contract|transaction)\b[^?.!]{0,50}?\b(valid|invalid|void|nullified|broken|sound|binding)\b",
    r"\bdoes\s+(my|our|the|a|his|her)\s+[^?.!]{0,40}?\b(break|invalidate|nullify|void)\b"
    r"[^?.!]{0,30}\b(prayer|fast|fasting|wudu|ablution|ghusl|marriage|nikah)\b",
    # Takfir questions about a person's status: "Is someone who abandons
    # prayer a kafir?", "Am I a disbeliever if…". Not "Who are those
    # described as disbelievers in 2:6?" (tafsir of the verse's subjects).
    r"\b(is|are|am|was|were|becomes?)\s+(i|someone|somebody|anyone|anybody|a\s+person|any\s+person|"
    r"a\s+muslim|any\s+muslim|muslims|people\s+who|the\s+one\s+who|one\s+who|whoever|my\s+\w+)\b"
    r"[^?]{0,60}?\b(kafirs?|kaafirs?|kuffar|disbelievers?|apostates?|murtads?|"
    r"out of (the fold of )?islam)\b",
    # Amounts owed: "How much zakat do I have to pay?"
    r"\bhow much\s+(zakat|zakah|zakaat|fidya|fidyah|kaffara|kaffarah|expiation)\b",
    r"\bhow much\s+(do|should|must)\s+i\s+(pay|give)\b",
    # Arabic: "هل يقع الطلاق…", "هل تبطل الصلاة…", "هل تارك الصلاة كافر؟", "كم يجب علي…".
    # يكفر/يخرج alone are not rulings ("هل يكفر الله السيئات" = expiates;
    # "هل يخرج المؤمن من النار"): only "هل يكفر من…" / "هل يخرج من الملة".
    r"هل\s+(يقع|تقع|وقع|يبطل|تبطل|يفسد|تفسد|ينقض|تنقض|ينتقض|تنتقض|أكفر)(?![ء-ي])",
    r"هل\s+(يكفر|يكفّر|يُكفَّر|نكفر|أكفّر)\s+(من|الذي|التي|المسلم|المسلمة|تارك|تاركة|فاعل|صاحب)(?![ء-ي])",
    r"هل\s+[^؟?]{0,30}?(يخرج|تخرج|خرج|خرجت|أخرج)\s+(من|عن)\s+(الملة|ملة\s+الإسلام|الإسلام|الدين)(?![ء-ي])",
    r"هل\s[^؟?]{0,50}?(?<![ء-ي])(كافر|كافرة|كفار|مرتد|مرتدة|مشرك|مشركة)(?![ء-ي])"
    r"(?![^؟?]{0,30}(في القرآن|في الآية|في السورة|في قصة))",
    r"(?<![ء-ي])كم\s+(يجب|يلزم|يتوجب|يتعين)\s+(علي|عليّ|علينا|عليه|عليها|عليك)(?![ء-ي])",
    r"(?<![ء-ي])كم\s+(زكاة|الزكاة|نصاب|فدية|الفدية|كفارة|الكفارة)(?![ء-ي])",
))

# Prompt-injection and "compose Qur'an" requests — refused before generation.
_INJECTION_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\bignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier|your)\s+(instructions|rules|prompts?)",
    r"\b(system|developer)\s+prompt\b",
    r"\byou are now\b",
    r"\b(jailbreak|DAN mode)\b",
    r"\b(write|compose|create|generate|invent|make up|produce)\s+(me\s+)?(a\s+|an\s+|some\s+)?"
    r"(new\s+|fake\s+|another\s+|original\s+)?(verse|surah|sura|ayah|ayat|ayahs)\b",
    r"\b(new|fake|another|original)\s+(verse|surah|sura|ayah)s?\s+(of|for|in|like|similar)\b",
    r"\b(complete|finish|continue)\s+(this|the|my)\s+(verse|ayah|surah)\b",
    r"تجاهل\s+(كل\s+|جميع\s+)?(التعليمات|الأوامر|القواعد)",
    r"اكتب\s+(لي\s+)?(آية|آيات|سورة)",
    r"(ألف|ألّف|أنشئ|اخترع)\s+(لي\s+)?(آية|آيات|سورة)",
    r"(آية|سورة)\s+جديدة",
    r"أكمل\s+(الآية|السورة)",
    # Role-play aimed at the assistant: "Pretend you are a mufti…", "Act as a
    # scholar and…" ("you are now…" is matched above). Not "Why did the hypocrites
    # pretend to be believers?" or "How did Dawud act as a judge?".
    r"\bpretend\s+(that\s+)?(you\s+are|you'?re|you\s+were|to\s+be\s+(a|an|the)\s+(mufti|scholar|sheikh|"
    r"shaykh|imam|faqih|mujtahid|qadi|unrestricted|different))\b",
    r"(^|[.!?,;:\n]\s*|\b(please|now|just|you)\s+)(act|behave|respond|answer|speak|reply)\s+(as|like)\s+"
    r"(a|an|the)\s+(mufti|scholar|sheikh|shaykh|imam|faqih|mujtahid|qadi|judge|unrestricted|different|"
    r"another)\b",
    r"\b(act|behave|respond|answer|speak|reply)\s+(as|like)\s+if\s+you\s+(were|are)\b",
    r"\brole[\s-]?play\b",
    # "Answer from your own knowledge", "skip the sources", "without citations"
    r"\b(from|using|use|with|on)\s+(only\s+)?your\s+own\s+(knowledge|opinion|view|understanding)\b",
    r"\bwithout\s+(any\s+|the\s+|using\s+|citing\s+|giving\s+)?(sources|citations|references)\b",
    r"\b(answer|respond|reply|explain|tell\s+me)\b[^.?!]{0,30}\bwithout\s+(any\s+)?evidence\b",
    r"\b(skip|ignore|disregard|forget|drop|bypass)\s+(all\s+|the\s+|any\s+|your\s+)?(sources|citations|"
    r"references)\b",
    r"\b(skip|ignore|disregard|forget|drop|bypass)\s+(all\s+|any\s+)?(of\s+)?(the\s+)?(your|previous|prior|"
    r"earlier|above|system|safety|these|my)\s+(\w+\s+)?(rules|guidelines|instructions|restrictions|prompt)\b",
    r"\b(skip|ignore|disregard|forget|drop|bypass)\s+(all\s+|any\s+)?(the\s+)?(rules|guidelines|"
    r"instructions|restrictions)\s+(above|before|you\s+were\s+given|given\s+to\s+you)\b",
    r"\b(the\s+)?sources\s+(don'?t|do not|doesn'?t)\s+matter\b",
    r"\bdeveloper\s+mode\b",
    # Markup that impersonates prompt structure: "</question><system>…"
    r"<\s*/?\s*(system|assistant|user|question|source|instructions?|conversation_history|im_start|im_end)\b[^>]*>",
    r"<\|[^|>]{0,40}\|>",
    # Arabic: "تصرف كأنك مفتٍ", "أجب من معرفتك الخاصة", "دون مصادر", "لا تلتزم بالمصادر"
    r"(تصرف|تصرّف|تظاهر|تقمص|تقمّص)\s+(ك|وك)?(أنك|انك|كأنك|كانك|بأنك|بانك|على\s+أنك|دور)",
    r"(اعتبر|تخيل|تخيّل)\s+(أنك|انك|نفسك)",
    r"(من|على|حسب|بحسب)\s+(معرفتك|علمك|رأيك|فهمك)(\s+الخاص(ة)?)?(?![ء-ي])",
    r"(دون|بدون|بلا|من\s+غير)\s+(أي\s+)?(ال)?(مصادر|مراجع|استشهاد|استشهادات|توثيق)(?![ء-ي])",
    r"(لا|ولا)\s+(تلتزم|تتقيد|تتقيّد|تهتم)\s+(بال|ب)?(مصادر|قواعد|تعليمات|مراجع)",
    # Role labels that impersonate the conversation structure.
    r"(^|\n|[.!?]\s+)\s*(system|user|assistant|developer|admin)\s*[:：]",
    r"(^|\n|[.!?]\s*)\s*(النظام|المستخدم|المساعد|المطور)\s*[:：]",
    # Switching the rules off.
    r"\b(citations?|sources?|grounding|safety|filters?|rules|restrictions|guardrails?)\s+(are\s+|is\s+)?"
    r"(now\s+)?(disabled|off|turned\s+off|lifted|removed|not\s+required|optional|suspended)\b",
    r"\bno\s+(need|requirement)\s+(for|of|to\s+(use|cite|follow))\s+(any\s+|the\s+)?(tafsir|tafseer|sources|"
    r"citations|references|evidence|scholars|commentaries|commentators)\b",
    r"\b(unrestricted|unfiltered|uncensored|free[\s-]thinking|jailbroken|independent|unbound)\s+(ai|a\.i\.|assistant|"
    r"model|chatbot|bot|mode|scholar|mujtahid|mufti)\b",
    r"\b(disregard|forget|ignore|override|bypass|drop|skip)\s+(everything|all|anything|whatever)\s+(you\s+(were|have\s+"
    r"been|'ve\s+been)\s+(told|given|instructed)|(said|told|given)\s+(to\s+you\s+)?(before|earlier|previously)|"
    r"(before|earlier|previously|above))",
    r"\b(forget|ignore|disregard|skip|leave\s+aside|set\s+aside|never\s+mind)\s+(the\s+|all\s+the\s+|those\s+)?"
    r"(commentators|scholars|exegetes|mufassirun|tafsirs?|tafseers?|commentaries|sources|books)\b",
    # The assistant's own opinion / interpretation / ijtihad.
    r"\b(your|ur)\s+(\w+\s+){0,2}?(opinion|view|interpretation|take|ijtihad|reading|understanding|tafsir|"
    r"tafseer|verdict|thoughts)\b(?!\s+(of|from)\s+(ibn|al-|the\s+(scholars|tafsir|commentators)))",
    r"\b(pretend|imagine|suppose|assume|act\s+as\s+if)\b[^.?!]{0,30}\b(there\s+(are|is|were)\s+no|without\s+any)\s+"
    r"(rules|restrictions|guidelines|limits|sources|filters)\b",
    r"\b(new|fake|original|invented|made[\s-]up|additional|extra|own|another)\s+(\w+\s+)?(verses?|ayat|ayahs?|surahs?|suras?)\b",
    r"\byou\s+are\s+(now\s+)?(a|an|the)\s+(\w+\s+)?(mufti|scholar|sheikh|shaykh|imam|faqih|mujtahid|qadi)\b"
    r"|\b(with|under)\s+no\s+(rules|restrictions|limits|filters)\b|\blet'?s\s+play\s+a\s+game\b",
    r"\b(like|in\s+the\s+manner\s+of|modelled\s+on|modeled\s+on|imitating)\s+(surah|surat|sura)\s+\S+",
    r"\bwhat\s+do\s+you\s+(personally\s+)?(think|believe|feel)\b",
    # Text styled as the Qur'an.
    r"\b(write|compose|create|generate|produce|craft|draft|make|render|translate|turn|rewrite|put)\b[^.?!]{0,60}"
    r"\b(in\s+the\s+style\s+of\s+(the\s+)?(qur'?an|koran|a\s+verse|an\s+ayah|scripture|revelation)|"
    r"quranic\s+(style|arabic|language|verse|form|prose)|as\s+(though|if)\s+it\s+(were|was)\s+(a|an)\s+"
    r"(verse|ayah|surah)|like\s+(a|an)\s+(verse|ayah|surah)|verse[\s-]like|in\s+(the\s+)?form\s+of\s+(a|an)\s+"
    r"(verse|ayah|surah))",
    r"(على\s+(نسق|نمط|شكل|طريقة|منوال|هيئة)|بأسلوب|بنفس\s+أسلوب|كأنها|كأنه)\s+(آية|آيات|الآيات|القرآن|"
    r"سورة|السور|قرآني|قرآنية)",
    r"(اكتب|ألف|ألّف|أنشئ|صغ|اصنع|ترجم|حول|حوّل)[^.؟!]{0,40}(آية|آيات|سورة|قرآنا|قرآني)",
    # Arabic: forget the rules / answer without the tafsir / own ijtihad.
    r"(تجاوز|انس|انسَ|تجاهل|اترك|أهمل|اهمل)\s+(كل|جميع|كافة)?\s*(ما\s+قيل|التعليمات|الأوامر|القواعد|التوجيهات|"
    r"القيود|ما\s+سبق)",
    r"(دون|بدون|من\s+غير|بلا)\s+(الرجوع|الاستناد|العودة|الاعتماد|النظر)\s+(إلى|الى|على|ل|في)\s*(كتب\s+)?"
    r"(ال)?(تفسير|تفاسير|مصادر|علماء|مراجع|مفسرين)",
    r"(اجتهادك|رأيك|فهمك|تفسيرك|تأويلك|قناعتك)(\s+(الخاص|الشخصي|المستقل))?(?![ء-ي])",
    r"بصفتك\s+(عالما|عالمًا|مجتهدا|مجتهدًا|مفتيا|فقيها|شيخا|مفسرا|إماما)",
    r"(المصادر|الاستشهاد|التوثيق|القواعد)\s+(معطلة|معطل|ملغاة|ملغى|غير\s+مطلوب|غير\s+مطلوبة|تم\s+تعطيلها)",
    r"تم\s+(تعطيل|إلغاء|الغاء)\s+(المصادر|الاستشهاد|القواعد|التعليمات|القيود)",
))

# 2. Scientific miracle claims
_SCIENTIFIC_AR = frozenset({
    "الإعجاز العلمي", "إعجاز علمي", "هل هذه الآية تثبت", "هل القرآن يثبت",
    "الانفجار الكبير", "نظرية علمية", "الطب الحديث", "الفيزياء", "الجيولوجيا",
    "الفلك", "علم الأحياء", "علم الأجنة", "توسع الكون", "الجبال أوتاد",
    "يثبت العلم", "أثبت العلم", "العلم يثبت", "علميًا ثبت", "دليل علمي",
})
_SCIENTIFIC_EN = frozenset({
    "scientific miracle", "does this verse prove", "does the quran prove",
    "big bang", "modern science", "physics", "geology", "biology",
    "embryology", "astronomy", "expanding universe", "mountains as pegs",
    "science proves", "science confirms", "scientifically proven",
    "scientific proof", "scientific evidence", "proven by science",
    "quran predicted", "quran mentions",
})

# 3. Qira'at (recitation variants)
_QIRAAT_AR = frozenset({
    "القراءات", "قراءة قرآنية", "قراءات متواترة", "قراءة شاذة",
    "قراء", "قراءة ورش", "قراءة حفص", "قراءة نافع", "روايات القراءة",
})
_QIRAAT_EN = frozenset({
    "qiraat", "qira'at", "recitation variant", "reading variant",
    "quranic recitation", "warsh", "hafs recitation", "nafi", "quranic reading",
})

# 4. Morphology / tasreef
_MORPHOLOGY_AR = frozenset({
    "تصريف", "الصرف", "الجذر", "الوزن الصرفي", "اشتقاق",
    "وزن الكلمة", "اشتقاق الكلمة",
})
_MORPHOLOGY_EN = frozenset({
    "morphology", "word root", "word pattern", "lemma", "tasreef",
    "root of the word", "root form", "derivation",
})

# 5. I'rab / grammatical analysis
_IRAB_AR = frozenset({
    "إعراب", "أعرب", "النحو", "محل الإعراب", "إعراب الآية",
    "إعراب الكلمة", "موقع الكلمة من الإعراب",
})
_IRAB_EN = frozenset({
    "i'rab", "irab", "parse this word", "grammatical analysis",
    "syntax", "grammatical parsing", "parse the verse",
})

# 6. Vocabulary / gharib al-Quran
_VOCAB_AR = frozenset({
    "معنى كلمة", "ما معنى كلمة", "غريب القرآن", "مفردة قرآنية",
    "معنى مفردة", "تعريف كلمة", "ما دلالة", "دلالة الكلمة",
})
_VOCAB_EN = frozenset({
    "meaning of the word", "vocabulary", "quranic word", "difficult word",
    "word meaning", "what does the word", "explain the word",
    "gharib", "gharib al-quran",
})

# 7. Munasabah / contextual relationships
_MUNASABAH_AR = frozenset({
    "المناسبة", "مناسبة الآيات", "العلاقة بين الآيات",
    "علاقة أول السورة بآخرها", "السياق القرآني", "ترابط الآيات",
    "ترابط السور", "مناسبة السور",
})
_MUNASABAH_EN = frozenset({
    "relationship between ayahs", "relationship between verses", "contextual relationship",
    "connection between verses", "beginning and ending of surah", "verse connection",
    "surah relation", "munasabah", "context of verses",
    # partial phrase: "relationship between" + anything Quran-related
    "relationship between the ayahs", "relationship between these ayahs",
    "relationship between these verses",
})

# 8. Verse similarity
_SIMILARITY_AR = frozenset({
    "صلة الآيات", "آيات مشابهة", "آيات مرتبطة", "آيات متشابهة",
    "الآيات المتعلقة", "آيات قريبة",
    # definite-article forms (with ال prefix)
    "مشابهة", "متشابهة", "مترابطة",
})
_SIMILARITY_EN = frozenset({
    "related ayahs", "similar verses", "verse similarity", "similar ayahs",
    "connected verses", "verses like this",
})

# 9. Story / Quranic narratives
_STORY_AR = frozenset({
    "قصة", "قصص القرآن", "أصحاب", "قوم", "نبي", "أنبياء",
    "حكاية", "رواية", "قصة سيدنا", "ذكر القرآن",
})
_STORY_EN = frozenset({
    "story of", "quran story", "people of", "companions of",
    "prophet story", "narrative of", "tale of", "story about prophet",
})

# 10. Thematic tafsir
_THEMATIC_AR = frozenset({
    "موضوع", "التفسير الموضوعي", "آيات عن", "كيف تناول القرآن",
    "ما قاله القرآن عن", "الآيات التي تتحدث عن", "آيات الصبر",
    "آيات الرحمة", "آيات التقوى",
    # Healing / guidance patterns
    "آيات للتخلص", "آيات لعلاج", "آيات لـ", "آيات عن الهم",
    "آيات عن الحزن", "آيات عن القلق", "آيات عن الخوف",
    "كيف أتخلص", "كيف أتغلب", "علاج الهم", "علاج الحزن",
    "للتخلص من", "للتغلب على", "بر الوالدين", "آيات عن الرزق",
    "دعاء الاستخارة", "آيات عن الصبر", "آيات عن التوكل",
    "آيات الشفاء", "آيات الراحة", "آيات الطمأنينة",
})
_THEMATIC_EN = frozenset({
    "theme", "thematic tafsir", "verses about", "what does the quran say about",
    "quran on the topic of", "all verses about", "quran teachings on",
    "verses for", "verses to", "verses on", "quran verses about",
    "verses relieving", "verses for anxiety", "verses for grief",
    "verses for healing", "quran on anxiety", "quran on grief",
    "quran on sadness", "quran on hope", "quran on patience",
    "verses for relief", "help with", "verses for parents",
})

# 11. Tafsir / verse meaning (broad)
_TAFSIR_AR = frozenset({
    "تفسير", "معنى الآية", "اشرح الآية", "ماذا تعني", "ما معنى",
    "فسر", "شرح", "تأويل", "مراد الآية",
})
_TAFSIR_EN = frozenset({
    "tafsir", "tafseer", "explain this ayah", "meaning of this verse",
    "what does this ayah mean", "explain verse", "interpret",
    "what does this verse mean", "explanation of", "exegesis",
})

# Clearly non-Quranic topics (for unsupported classification)
_UNSUPPORTED_TOPICS = frozenset({
    "weather forecast", "stock market", "football", "soccer", "recipe",
    "movie", "dating", "politics", "election", "cryptocurrency",
    "bitcoin", "programming", "code", "python script",
})

# Arabic script detector
_ARABIC_SCRIPT = re.compile(r'[؀-ۿݐ-ݿࢠ-ࣿ]+')


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class QuranQuestionClassifier:
    """
    Deterministic rule-based classifier for Quranic questions.

    Classification priority (highest to lowest):
      0. prompt_injection     — hard block ("ignore your instructions", "write a new verse")
      1. fatwa_like           — hard block, no generation
      2. scientific_miracle   — allowed with caution labels
      3. qiraat               — route to module (fallback to RAG + warning)
      4. morphology           — route to module (fallback to RAG + warning)
      5. irab                 — route to module (fallback to RAG + warning)
      6. vocabulary_meaning   — route to module (fallback to RAG + warning)
      7. munasabah            — route to RAG with needs_review flag
      8. similarity           — route to similarity module
      9. story                — route to stories module
     10. thematic_tafsir      — route to RAG (thematic retrieval)
     11. tafsir_summary       — route to RAG (standard)
     12. needs_clarification  — request clarification (no generation)
     13. unsupported          — safe refusal (non-Quranic topic)
     14. general_question     — route to RAG (default)
    """

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def classify(self, question: str) -> QuestionClassification:
        """
        Classify a user question.

        Args:
            question: Raw user input (Arabic, English, or mixed).

        Returns:
            QuestionClassification with routing and safety metadata.
        """
        q = question.strip()
        q_lower = q.lower()
        language = self._detect_language(q)

        # Priority-ordered checks
        if any(p.search(q) for p in _INJECTION_PATTERNS):
            return QuestionClassification(
                intent=INTENT_PROMPT_INJECTION,
                language=language,
                risk_level=RISK_HIGH,
                requires_source=False,
                requires_scholar_review=False,
                allowed_to_generate=False,
                route_to=ROUTE_REFUSAL,
                warnings=[INJECTION_REFUSAL_EN, INJECTION_REFUSAL_AR],
            )

        if self._matches_whole(q_lower, _FATWA_AR | _FATWA_EN) or any(
            p.search(q) for p in _FATWA_PATTERNS
        ) or ruling_request(q) is not None:
            return QuestionClassification(
                intent=INTENT_FATWA_LIKE,
                language=language,
                risk_level=RISK_HIGH,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=False,
                route_to=ROUTE_REFUSAL,
                warnings=[FATWA_REFUSAL_EN, FATWA_REFUSAL_AR],
            )

        if self._matches_any(q_lower, _SCIENTIFIC_AR | _SCIENTIFIC_EN):
            return QuestionClassification(
                intent=INTENT_SCIENTIFIC_MIRACLE,
                language=language,
                risk_level=RISK_HIGH,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[SCIENTIFIC_CAUTION_EN, SCIENTIFIC_CAUTION_AR],
            )

        if self._matches_any(q_lower, _QIRAAT_AR | _QIRAAT_EN):
            return QuestionClassification(
                intent=INTENT_QIRAAT,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _MORPHOLOGY_AR | _MORPHOLOGY_EN):
            return QuestionClassification(
                intent=INTENT_MORPHOLOGY,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _IRAB_AR | _IRAB_EN):
            return QuestionClassification(
                intent=INTENT_IRAB,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _VOCAB_AR | _VOCAB_EN):
            return QuestionClassification(
                intent=INTENT_VOCABULARY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _MUNASABAH_AR | _MUNASABAH_EN):
            return QuestionClassification(
                intent=INTENT_MUNASABAH,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[],
            )

        if self._matches_any(q_lower, _SIMILARITY_AR | _SIMILARITY_EN):
            return QuestionClassification(
                intent=INTENT_SIMILARITY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=False,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_SIMILARITY,
                warnings=[],
            )

        if self._matches_any(q_lower, _STORY_AR | _STORY_EN):
            return QuestionClassification(
                intent=INTENT_STORY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_STORIES,
                warnings=[],
            )

        if self._matches_any(q_lower, _THEMATIC_AR | _THEMATIC_EN):
            return QuestionClassification(
                intent=INTENT_THEMATIC_TAFSIR,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[],
            )

        if self._matches_any(q_lower, _TAFSIR_AR | _TAFSIR_EN):
            return QuestionClassification(
                intent=INTENT_TAFSIR_SUMMARY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[],
            )

        # Non-Quranic topic → unsupported
        if self._matches_any(q_lower, _UNSUPPORTED_TOPICS):
            return QuestionClassification(
                intent=INTENT_UNSUPPORTED,
                language=language,
                risk_level=RISK_LOW,
                requires_source=False,
                requires_scholar_review=False,
                allowed_to_generate=False,
                route_to=ROUTE_REFUSAL,
                warnings=[UNSUPPORTED_EN, UNSUPPORTED_AR],
            )

        # Very short queries that lack enough context
        if len(q.split()) < 3:
            return QuestionClassification(
                intent=INTENT_NEEDS_CLARIFICATION,
                language=language,
                risk_level=RISK_LOW,
                requires_source=False,
                requires_scholar_review=False,
                allowed_to_generate=False,
                route_to=ROUTE_CLARIFICATION,
                warnings=[CLARIFICATION_EN, CLARIFICATION_AR],
            )

        # Default: general question — send to RAG
        return QuestionClassification(
            intent=INTENT_GENERAL,
            language=language,
            risk_level=RISK_LOW,
            requires_source=True,
            requires_scholar_review=False,
            allowed_to_generate=True,
            route_to=ROUTE_RAG,
            warnings=[],
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _detect_language(self, text: str) -> str:
        has_arabic = bool(_ARABIC_SCRIPT.search(text))
        # Rough heuristic: if >30% chars are ASCII letters → likely English present
        ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
        has_english = ascii_letters > len(text) * 0.3
        if has_arabic and has_english:
            return "mixed"
        if has_arabic:
            return "ar"
        return "en"

    @staticmethod
    def _matches_whole(text_lower: str, patterns: frozenset) -> bool:
        """Like _matches_any, but a phrase must not run into the next word
        ("ما حكم" = what is the ruling; "ما حكمة" = what is the wisdom)."""
        for p in patterns:
            p = p.lower()
            start = text_lower.find(p)
            while start != -1:
                end = start + len(p)
                nxt = text_lower[end:end + 1]
                if not nxt or not (nxt.isalpha() and p[-1:].isalpha()):
                    return True
                start = text_lower.find(p, start + 1)
        return False

    @staticmethod
    def _matches_any(text_lower: str, patterns: frozenset) -> bool:
        """Return True if any pattern appears as a substring of the lowercased text."""
        return any(p.lower() in text_lower for p in patterns)


# ---------------------------------------------------------------------------
# Helper: map classifier intent → QueryIntent (for backward-compatible pipeline)
# ---------------------------------------------------------------------------

def classifier_intent_to_query_intent(intent: str):
    """
    Map a fine-grained classifier intent to the legacy QueryIntent enum value
    used by RAG retrieval, expansion, and generation.

    Returns the string value (not the enum) to avoid import cycles.
    """
    _MAP = {
        INTENT_FATWA_LIKE:          "ruling",
        INTENT_SCIENTIFIC_MIRACLE:  "verse_meaning",
        INTENT_QIRAAT:              "linguistic",
        INTENT_MORPHOLOGY:          "linguistic",
        INTENT_IRAB:                "linguistic",
        INTENT_VOCABULARY:          "linguistic",
        INTENT_MUNASABAH:           "verse_meaning",
        INTENT_SIMILARITY:          "verse_meaning",
        INTENT_STORY:               "story_exploration",
        INTENT_THEMATIC_TAFSIR:     "theme_search",
        INTENT_TAFSIR_SUMMARY:      "verse_meaning",
        INTENT_GENERAL:             "verse_meaning",
        INTENT_NEEDS_CLARIFICATION: "unknown",
        INTENT_UNSUPPORTED:         "unknown",
        INTENT_PROMPT_INJECTION:    "unknown",
    }
    return _MAP.get(intent, "verse_meaning")


# Module-level singleton
quran_question_classifier = QuranQuestionClassifier()
