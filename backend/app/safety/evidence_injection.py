"""
Instructions planted in retrieved evidence.

Tafsir speaks about the verse, its words and its reports; it never addresses
whatever produces the reply that quotes it, nor tells it what to put in "the
answer" or what to tell "the reader". A chunk that does either is an
injection attempt, whatever its wording: the instruction (and the claim it
carries) is fenced off as data and is still shown verbatim, but it can never
support a claim, and an answer that repeats what it carries is treated as
obeying it.

Detection is structural, not a list of known attack strings. A sentence is
an instruction when it combines a directive (an imperative, a modal of
obligation, a jussive "let…/لـيَفعل") with one of:

* an addressee that is the software: the assistant, a model, a bot, any
  system/program/tool/generator/engine, or an agent noun formed on the
  output ("summary writer", "answer generator", "كاتب الملخص", "المولد
  الآلي");
* a role defined by producing the output: "whoever / whatever / the one
  that writes, drafts, composes, prepares, generates … the answer / reply /
  summary / text", "من يصوغ الجواب", "ما يولد الرد";
* the output itself or its audience: "your answer", "the summary must",
  "tell the reader", "أخبر السائل", "في الجواب".

Prompt structure counts on its own: role / chat-template markers, "ignore
previous instructions", and markdown or label headers that tafsir text never
uses ("### Output directive", "INSTRUCTION:", "توجيه:").

``split_tainted()`` separates a text into the part that is ordinary evidence
and the part an instruction controls: the instruction, everything after it
(the payload usually follows) and, when the instruction closes the text or
points back ("the above", "هذا الحكم"), the sentences just before it.
Calibration: across the whole stored corpus (all sources, both languages)
no chunk is flagged.
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple

_AR = r"ء-ي"

# ------------------------------------------------------------------ English

_EN_ADDRESSEE = re.compile(
    r"\b(assistant|chat\s*bot|chatbot|bot|a\.?i\.?|artificial\s+intelligence|language\s+model|llm|"
    r"gpt|model|ai\s+model)\b",
    re.IGNORECASE,
)
# Output artefacts and their audience.
_EN_OUTPUT = (r"(?:final\s+|generated\s+|eventual\s+|resulting\s+)?(?:answers?|repl(?:y|ies)|responses?|outputs?|"
              r"summar(?:y|ies)|write-?ups?|completions?|final\s+text|generated\s+text|explanations?\s+for\s+the\s+"
              r"(?:reader|user)|digest|synopsis|overview)")
_EN_AUDIENCE = r"(?:reader|readers|user|users|questioner|asker|audience|enquirer|inquirer|person\s+asking|people\s+asking)"
# Agent nouns of producing text, and software nouns.
_EN_AGENT = (r"(?:writer|composer|drafter|generator|producer|summari[sz]er|compiler|responder|answerer|preparer|"
             r"author|editor|maker|engine|pipeline|processor|tool|program|software|system|agent|machine|bot)")
_EN_ROLE = re.compile(
    # "summary writer", "answer generator", "response composer"
    rf"\b{_EN_OUTPUT}[\s-]+{_EN_AGENT}s?\b"
    # "automatic generator", "text engine", "AI summariser"
    r"|\b(?:automatic|automated|auto|machine|text|content|ai|software|digital)[\s-]+(?:generator|writer|composer|"
    r"engine|system|tool|program|pipeline|agent|summari[sz]er|responder|processor|drafter)s?\b"
    # "whoever / whatever / the one that drafts the summary"
    rf"|\b(?:whoever|whatever|whichever|anyone|anything|anybody|someone|something|the\s+one|one|the\s+party|"
    rf"the\s+(?:person|system|process|program|tool|thing))\s+(?:that\s+|who\s+|which\s+)?(?:is\s+)?"
    rf"(?:writ(?:es|ing)|write|compos(?:es|ing)|compose|draft(?:s|ing)?|generat(?:es|ing)|generate|"
    rf"produc(?:es|ing)|produce|prepar(?:es|ing)|prepare|compil(?:es|ing)|compile|summari[sz](?:es|ing)|"
    rf"summari[sz]e|answer(?:s|ing)?|repl(?:ies|ying)|reply|respond(?:s|ing)?|creat(?:es|ing)|create|"
    rf"formulat(?:es|ing)|formulate|assembl(?:es|ing)|assemble|puts?\s+together|writes?\s+up|process(?:es|ing)?|"
    rf"reads?\s+this|uses?\s+this)\b[^.\n]{{0,30}}?\b(?:{_EN_OUTPUT}|this\s+(?:passage|text|note|chunk|"
    rf"document|source|entry|commentary))\b",
    re.IGNORECASE,
)
# "the generator", "any summariser": a software role only with a directive.
_EN_ROLE_WEAK = re.compile(
    r"\b(?:the|any|every|each|this|whichever)\s+(?:generator|summari[sz]er|responder|answerer|drafter|pipeline|"
    r"software|engine|processor)s?\b",
    re.IGNORECASE,
)
_EN_RESPONSE_META = re.compile(
    rf"\b(?:your|the|this|any|every|each|its)\s+{_EN_OUTPUT}\s+(?:must|should|shall|is\s+to|are\s+to|needs?\s+to|"
    rf"has\s+to|have\s+to|ought\s+to|will|may\s+only|can\s+only)\b"
    rf"|\byour\s+{_EN_OUTPUT}\b"
    rf"|\b(?:in|into|within|throughout)\s+(?:the|your|any|every|each|its)\s+{_EN_OUTPUT}\b"
    rf"|\b(?:open|begin|start|end|close|conclude)\s+(?:the|your|every|each|any)\s+{_EN_OUTPUT}\b"
    r"|\bwhen\s+(?:you\s+)?(?:answer|answering|reply|replying|respond|responding|summari[sz]ing|summari[sz]e)\b"
    rf"|\b(?:tell|inform|assure|remind|convince|advise|instruct|reassure|warn|teach|show)\s+(?:the\s+|your\s+|any\s+|"
    rf"every\s+)?{_EN_AUDIENCE}\b"
    rf"|\b(?:for|to)\s+(?:the|your|any|every)\s+{_EN_AUDIENCE}\b"
    rf"|\b(?:the\s+)?{_EN_AUDIENCE}\s+(?:should|must|is\s+to|needs\s+to)\s+(?:be\s+)?(?:told|informed|assured|"
    rf"reminded|shown|given)\b"
    r"|\b(?:citation|grounding|safety|source|sourcing|output|formatting)\s+(?:policy|policies|rules?|requirements?)\b"
    r"|\b(?:previous|prior|earlier|above|system|original)\s+(?:instructions?|prompts?|rules?|guidelines?)\b"
    r"|\bnote\s+(?:to|for)\s+(?:the\s+)?(?:reader|model|assistant|ai|bot|system|writer|editor|generator)\b",
    re.IGNORECASE,
)
_EN_DIRECTIVE_VERBS = (
    r"ignore|disregard|forget|override|say|state|mention|add|write|tell|assure|claim|answer|respond|reply|output|"
    r"print|insist|explain|include|declare|confirm|pretend|act|stop|present|assert|affirm|emphasi[sz]e|stress|"
    r"report|conclude|describe|put|ensure|open|begin|start|end|close|frame|phrase|render|cite|attribute|rule|"
    r"treat|consider|copy|reproduce|repeat|insert|append|prepend|lead|summari[sz]e|translate|announce|inform|"
    r"advise|warn|teach|tell|make|let|use|remove|omit|drop|delete|hide|replace|quote|call|label|listen|do\s+not|"
    r"don't|never|always"
)
_EN_IMPERATIVE = re.compile(
    rf"(?:^|[.:;!\n\]\)#*>\-–—]\s*|,\s*)(?:please\s+|kindly\s+|now\s+|simply\s+|just\s+)?(?:{_EN_DIRECTIVE_VERBS})\b"
    r"|\b(?:you\s+(?:must|should|need\s+to|have\s+to|are\s+to|will|shall))\b"
    r"|\b(?:must|should|shall|is\s+to|are\s+to|needs?\s+to|has\s+to|have\s+to|ought\s+to|is\s+(?:required|"
    r"instructed|expected|asked|told|directed)\s+to|are\s+(?:required|instructed|expected|asked|told|directed)\s+to)"
    r"\s+(?:\w+\s+){0,2}?(?:say|state|mention|add|write|tell|assure|claim|declare|confirm|present|assert|affirm|"
    r"emphasi[sz]e|stress|report|conclude|describe|put|include|open|begin|start|end|close|insist|explain|cite|"
    r"attribute|rule|treat|consider|copy|reproduce|repeat|insert|append|lead|announce|inform|advise|warn|"
    r"teach|answer|respond|reply|output|print|quote|use|be|call|label)\b"
    r"|\blet\s+(?:the|any|every|each|whoever|whatever)\s"
    r"|\b(?:is|are)\s+to\s+be\s+\w+(?:ed|en)\b|\b(?:kindly|please)\s+\w+"
    r"|^\s*(?:dear|attention|attn|reminder|important|notice)\b"
    r"|\b(?:make|be)\s+sure\b|\bensure\s+that\b"
    r"|\b(?:is|are)\s+(?:required|instructed|expected|asked|told|directed|supposed|meant)\s+to\b"
    r"|\bit\s+is\s+(?:essential|important|mandatory|required|necessary|vital|imperative)\s+(?:that|to)\b",
    re.IGNORECASE | re.MULTILINE,
)

# ------------------------------------------------------------------- Arabic

_AR_OUTPUT = (r"(?:ال)?(?:ملخص|خلاصة|خلاصه|تلخيص|جواب|إجابة|اجابة|إجابه|اجابه|رد|ردود|إجابات|اجابات|مخرجات|شرح|"
              r"نص\s+(?:ال)?(?:نهائي|مولد|ناتج|المولد|الناتج|النهائي)|شرح\s+(?:ال)?(?:نهائي|مولد))")
_AR_AUDIENCE = r"(?:ال|لل|ل)?(?:سائل|سائلين|مستخدم|مستخدمين|قارئ|قراء|مستفسر|مستفتي|جمهور)"
_AR_ADDRESSEE = re.compile(
    rf"(?<![{_AR}])(?:لل|ال|ل)?(?:مساعد\s+(?:الذكي|الآلي|الرقمي)|المساعد|مساعد|الذكاء\s+الاصطناعي|"
    r"الذكاء\s+الصناعي|نموذج\s+اللغوي|نموذج\s+لغوي|نموذج\s+(?:اللغة|الذكاء)|النموذج\s+اللغوي|نموذج\s+الذكاء|"
    r"البوت|الروبوت|لمن\s+يجيب|من\s+يجيب\s+(?:على|عن)|برنامج\s+المحادثة)"
    rf"(?![{_AR}])"
)
_AR_ROLE = re.compile(
    # "كاتب الملخص", "محرر الإجابة", "مولد الردود"
    rf"(?<![{_AR}])(?:[وفل]|لل|ال)?(?:كاتب|محرر|صائغ|معد|معدي|منشئ|مولد|مولّد|مؤلف|واضع|مدون|محرك|صانع|مصمم)"
    rf"\s+{_AR_OUTPUT}(?![{_AR}])"
    # "المولد الآلي", "النظام الآلي", "البرنامج الذي يولد…"
    rf"|(?<![{_AR}])(?:[وفل]|لل|ال)?(?:مولد|مولّد|منشئ|محرك|نظام|برنامج|خوارزمية|أداة|اداة|تطبيق|آلة|الة)"
    rf"\s+(?:ال)?(?:آلي|الي|تلقائي|ذكي|نصوص|إجابات|اجابات|ردود|محادثة|توليد)(?![{_AR}])"
    # "من / ما / الذي يصوغ الجواب"
    rf"|(?<![{_AR}])(?:[وفل]?(?:من|ما|الذي|التي|كل\s+من|أيا\s+كان|ايا\s+كان))\s+(?:[يت](?:كتب|صوغ|صيغ|عد|حرر|"
    rf"لخص|جيب|نشئ|ولد|ولّد|جمع|ركب|نسق|عالج|قرأ|قرا|نتج|صنع|عرض|نقل|كتبون|صوغون))(?![{_AR}])"
    rf"[^.\n]{{0,25}}?{_AR_OUTPUT}(?![{_AR}])"
    rf"|(?<![{_AR}])(?:[وفل]?(?:من|ما|الذي|التي))\s+[يت](?:قرأ|قرا|عالج|ستخدم)\s+هذا(?:\s+(?:النص|المقطع|الكلام)|\s*[:،,])"
)
_AR_RESPONSE_META = re.compile(
    rf"(?<![{_AR}])(?:إجابتك|اجابتك|ملخصك|خلاصتك)(?![{_AR}])"
    rf"|عند\s+(?:الإجابة|الاجابة|الرد|التلخيص|الجواب)\s+(?:على|عن)\s+(?:هذا|السؤال|سؤال)"
    rf"|(?<![{_AR}])(?:عند|حين|أثناء|اثناء|قبل|بعد)\s+(?:صياغة|كتابة|إعداد|اعداد|تحرير|توليد|إنشاء|انشاء|تلخيص)\s+"
    rf"(?:ال)?(?:جواب|إجابة|اجابة|رد|ملخص|شرح|خلاصة|نص)"
    rf"|(?<![{_AR}])(?:ال)?مطلوب\s+(?:من|في)\s+(?:ال)?(?:جواب|إجابة|اجابة|رد|ملخص|شرح|خلاصة)(?![{_AR}])"
    rf"|عند\s+(?:الإجابة|الاجابة|الرد|التلخيص|الجواب)\s*[،,:]?\s*(?:اذكر|قل|اكتب|أضف|اضف|أكد|اكد|صرح|بين|أخبر|اخبر)"
    rf"|(?<![{_AR}])(?:في|ضمن|داخل)\s+(?:ال)?(?:ملخص|خلاصة|خلاصه|تلخيص|مخرجات)(?![{_AR}])"
    rf"|(?<![{_AR}])[وف]?(?:أخبر|اخبر|طمئن|أقنع|اقنع|أبلغ|ابلغ|أفهم|افهم)\s*{_AR_AUDIENCE}(?![{_AR}])"
    rf"|(?<![{_AR}])(?:لل|ل)(?:مستخدم|مستفسر)(?![{_AR}])"
    r"|(?:ال)?تعليمات\s+(?:السابقة|النظام|للنظام)|تعليمات\s+(?:إلى|الى|لل)|سياسة\s+(?:الاستشهاد|المصادر)"
)
_AR_DIRECTIVE = re.compile(
    rf"(?<![{_AR}])[وف]?(?:تجاهل|انس|انسَ|اكتب|أضف|اضف|قل|أخبر|اخبر|اذكر|صرح|صرّح|أكد|اكد|أجب|اجب|"
    r"تصرف|قرر|قرّر|ابدأ|ابدا|افتتح|اختم|انقل|انسخ|أورد|اورد|ضع|اجعل|قدم|قدّم|أدرج|ادرج|أثبت|اثبت|"
    r"احرص|تأكد|تاكد|احذف|أسقط|اسقط|اعتمد|استخدم|انص|لا\s+تذكر|لا\s+تستشهد|يجب\s+أن\s+تقول|عليك\s+أن)"
    rf"(?![{_AR}])"
    # jussive "ليذكر", "فليكتب", "ولتؤكد"
    rf"|(?<![{_AR}])[وف]?ل[يت](?:ذكر|كتب|قل|قول|ؤكد|صرح|نص|ضف|ضيف|خبر|بين|قرر|جعل|بدأ|بدا|فتتح|ختم|عرض|ورد|نقل|"
    rf"ثبت|درج|قدم|كن|عتمد)(?![{_AR}])"
    rf"|(?<![{_AR}])(?:يجب|ينبغي|يتعين|يلزم|لا\s+بد|لابد|عليه|عليها|عليك)\s+(?:على\s+\S+\s+)?(?:أن|ان)\s+"
    rf"|(?<![{_AR}])(?:يجب|ينبغي|يتعين|يلزم)\s+(?:على|ل)"
    rf"|(?<![{_AR}])(?:ال)?مطلوب(?![{_AR}])"
    rf"|(?<![{_AR}])(?:يجب|ينبغي|يتعين|يلزم|لا\s*بد\s+من)\s+[{_AR}]{{3,}}"
    rf"|(?<![{_AR}])على\s+(?:كل\s+)?(?:ال)?(?:كاتب|محرر|صائغ|معد|منشئ|مولد|مولّد|نظام|برنامج|مساعد)"
    rf"|(?<![{_AR}])على\s+(?:من|ما|الذي|التي|كل\s+من)\s+[^.\n]{{0,50}}?\s(?:أن|ان)\s"
    rf"|(?<![{_AR}])[وف]?(?:أيها|ايها|يا)\s+(?:ال)?(?:نظام|برنامج|مساعد|كاتب|محرر|معد|مولد)"
)

# Vocabulary of producing the reply: what tafsir prose never talks about.
# With any directive in the same sentence it marks an instruction.
_EN_PRODUCTION = re.compile(
    r"\b(?:(?:tools?|machines?|services?|software|programs?|systems?|models?|apps?|applications?|algorithms?)\s+"
    r"(?:that\s+|which\s+)?(?:reading|reads|processing|processes|using|uses|turning|turns|handling|handles|"
    r"answering|answers|producing|produces|summari[sz]ing|summari[sz]es)|answering\s+(?:service|tool|system|"
    r"machine|engine|program|software|model)|content\s+generat\w*|(?:turns?|turning|converts?|converting|"
    r"rewrites?|rewriting)\s+this\s+(?:\w+\s+)?into|into\s+(?:prose|an?\s+(?:answer|reply|response|summary|"
    r"explanation))|(?:upon|when|while|before|after|in)\s+(?:producing|writing|drafting|composing|preparing|"
    r"generating|formulating|creating|writing\s+up)\s+(?:the|an?|your|any|this)\s+(?:\w+\s+)?(?:answers?|"
    r"repl(?:y|ies)|responses?|explanations?|summar(?:y|ies)|texts?|outputs?)|"
    r"(?:anyone|anybody|whoever|those|people|someone)\s+(?:who\s+(?:is\s+|are\s+)?)?(?:asking|asks|ask)\s+"
    r"(?:about\s+)?(?:this|it|the\s+verse)|reading\s+this\b|(?:the|your|any|each|every|final|this)\s+summar(?:y|ies)|be\s+summari[sz]ed|summari[sz]ing\s+(?:this|it)|"
    r"overviews?|synopsis|write-?ups?|outputs?|generators?|generated\s+(?:text|answers?|repl(?:y|ies)|responses?|"
    r"summar(?:y|ies)|outputs?|explanations?)|drafting|drafter|composer|users?|chat\s*bot|chatbot|"
    r"bots?|a\.i\.|ai|llm|gpt|language\s+model|engine|pipeline|prompts?|directives?|instructions?\s+(?:for|to)|"
    r"(?:your|each|every|final)\s+(?:repl(?:y|ies)|responses?|answers?)|"
    r"(?:any|the)\s+(?:repl(?:y|ies)|responses?|answers?|summar(?:y|ies))\s+(?:built|generated|produced|drawn|"
    r"derived|written|composed|drafted|prepared|based|you|that\s+(?:is|uses|cites|quotes))|"
    r"let\s+(?:the|any|every|each)\s+(?:repl(?:y|ies)|responses?|answers?|summar(?:y|ies)|explanations?)|"
    r"from\s+this\s+(?:passage|commentary|text|note|chunk|entry|excerpt|document)|"
    r"explanations?\s+(?:given|shown|presented|delivered|offered|built|derived|generated|produced)|"
    r"(?:built|derived|generated|produced|drawn|made)\s+from\s+this\s+(?:passage|commentary|text|note|chunk|entry)|"
    r"this\s+(?:passage|commentary|text|chunk|document|entry|note|excerpt)\s+(?:is|are|should|must|shall)\s+"
    r"(?:to\s+)?be\s+\w+ed)\b",
    re.IGNORECASE,
)
_AR_PRODUCTION = re.compile(
    rf"(?<![{_AR}])[وفبل]?(?:ال|لل)?(?:مستخدم|مستخدمين|مخرجات|برنامج|آلي|تعليمات|توجيهات)(?![{_AR}])"
    r"|الذكاء\s+(?:الاصطناعي|الصناعي)|(?<![" + _AR + r"])(?:ال)?نموذج\s+(?:ال)?لغ"
    rf"|(?<![{_AR}])(?:في|للملخص)\s+(?:ال)?(?:ملخص|تلخيص)(?![{_AR}])|(?<![{_AR}])(?:ال)?ملخص\s+(?:ال)?(?:نهائي|مقدم)"
    rf"|(?<![{_AR}])(?:في|ب)\s+(?:أول|اول|بداية|مطلع|صدر|آخر|اخر|نهاية|خاتمة|مستهل)\s+(?:ال)?(?:جواب|إجابة|اجابة|رد|ملخص|خلاصة)"
    rf"(?![{_AR}])"
    rf"|(?<![{_AR}])(?:لل|ل)(?:إجابة|اجابة|جواب|رد|خلاصة)\s+(?:أن|ان)(?![{_AR}])"
    rf"|(?<![{_AR}])(?:ال)?(?:جواب|إجابة|اجابة|رد)\s+(?:ال)?(?:نهائي|مقدم|مولد|موجه)(?![{_AR}])"
    rf"|(?<![{_AR}])(?:ال)?(?:جواب|إجابة|اجابة|رد)\s+(?:على\s+السائل|للسائل|للقارئ|للمستخدم)(?![{_AR}])"
    rf"|(?<![{_AR}])[يت](?:كتب|عد|صوغ|حرر)\s+(?:ال)?(?:جواب|إجابة|اجابة|رد|خلاصة|ملخص)(?![{_AR}])"
    rf"|(?<![{_AR}])(?:من|ما|الذي|التي)\s+[يت]لخص(?![{_AR}])"
    rf"|(?<![{_AR}])[يت]تضمن\s+(?:ال)?(?:ملخص|جواب|إجابة|اجابة|رد|خلاصة)(?![{_AR}])"
    rf"|(?<![{_AR}])[وف]?ل[يت][{_AR}]{{2,}}\s+(?:ال)?مجيب(?![{_AR}])"
    rf"|(?<![{_AR}])هذا\s+(?:التفسير|النص|المقطع)\s+(?:للقارئ|للسائل|للمستخدم)"
)
# "Note for X:", "Attention, text composer:", "إلى البرنامج الذي يجيب:" —
# a sentence that opens by addressing someone.
_DEDICATION_HEAD = re.compile(r"^\s*(?:[#>*_\-\s]*)([^:\n.؟?!]{2,70}?)\s*(?:[:：]|\s[\-–—]\s)")

# ------------------------------------------------------------ structure

_STRUCTURAL = re.compile(
    r"\b(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier|your|other)\s+"
    r"(instructions|rules|prompts?|guidelines)\b|\b(system|developer)\s+prompt\b"
    r"|\b(ignore|disregard|forget)\s+(everything|anything|all)\s+(else|above|before|previous|other)\b"
    r"|<\s*/?\s*(system|assistant|source|question|user|im_start|im_end|instructions?)\b|<\|[^|>]{0,40}\|>"
    r"|^\s*(system|assistant|user|developer)\s*:|\bnew\s+(system\s+)?instructions?\s*:|\bnew\s+system\s+prompt\b"
    r"|تجاهل\s+(كل\s+|جميع\s+)?(التعليمات|الأوامر|الاوامر|القواعد)",
    re.IGNORECASE | re.MULTILINE,
)
# A header line: markdown heading, a bold/bracketed label, or an upper-case
# instruction label. Tafsir text is plain prose: none of these occur in it.
_HEADER = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]+\S[^\n]*|>[ \t]*\S[^\n]{0,40}?:"
    r"|\*[^*\n]{2,40}\*[ \t]*:"
    r"|(?:\*\*|__)[^*_\n]{2,80}(?:\*\*|__)"
    r"|\[[ \t]*(?:instruction|instructions|directive|directives|system|note|important|attention|task|override|"
    r"policy|rule|rules|meta|admin|editor|تعليمات|تعليمة|توجيه|توجيهات|تنبيه|ملاحظة|أمر|امر)[^\]\n]{0,40}\]"
    r"|(?:INSTRUCTIONS?|DIRECTIVES?|SYSTEM|IMPORTANT|ATTENTION|NOTE|TASK|OVERRIDE|POLICY|RULES?)\b[^\n]{0,40}:"
    r"|(?:تعليمات|تعليمة|توجيه|توجيهات|أوامر|اوامر)(?:\s+[^\n:]{0,30})?:)",
    re.MULTILINE,
)
_BACK_REFERENCE = re.compile(
    r"\b(the\s+above|the\s+foregoing|the\s+preceding|the\s+previous\s+(sentence|line|ruling|statement|claim)|"
    r"this\s+(ruling|statement|claim|sentence|line|point|fact|verdict|conclusion)|that\s+(ruling|statement|claim|"
    r"verdict)|these\s+(words|lines|sentences|points))\b"
    rf"|(?<![{_AR}])(?:ما\s+سبق|ما\s+تقدم|ما\s+ذكر|المذكور|ما\s+سلف|هذا\s+(?:الحكم|القول|الكلام|السطر|المعنى)|"
    r"هذه\s+(?:الجملة|العبارة|الفتوى))"
    # an instruction ending on a pronoun for what came before: "…lead with that."
    r"|\b(?:with|by|on|of|state|repeat|use|include|copy)\s+(?:that|this|it|these|them)\s*[.!]?\s*$"
    rf"|(?<![{_AR}])(?:بهذا|بذلك|هذا|ذلك|به|بها)\s*[.!]?\s*$",
    re.IGNORECASE,
)

_SENTENCES = re.compile(r"(?<=[.!?؟؛;\n])\s*")


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"[ً-ْٰـ]", "", t)


# A note addressed to someone: "For the summary writer:", "To whoever drafts
# the reply -", "إلى كاتب الملخص:".
_AR_DEDICATION = re.compile(
    rf"^\s*(?:ملاحظة|رسالة|تنبيه|تذكير|توجيه|تعليمات|تعليمة)\s+(?:إلى|الى|لل|ل)\s*[{_AR}][^:\n]{{0,40}}:"
)
_EN_DEDICATION = re.compile(
    rf"(?:^|[.\n])\s*(?:a\s+)?(?:note|message|reminder|instruction|memo|attention|attn|important)?\s*"
    rf"(?:for|to)?\s*(?:the\s+|any\s+|every\s+)?(?:{_EN_AUDIENCE}|assistant|model|ai|bot|system)\s*[:\-–—]",
    re.IGNORECASE,
)


_EN_VOCATIVE = re.compile(
    r"^\W*(?:dear\s+|hey\s+|hi\s+|o\s+|attention\s+)?(?:the\s+)?(?:assistant|chat\s*bot|chatbot|bot|a\.?i\.?|"
    r"language\s+model|llm|gpt|model|ai\s+model|system)\s*[,:!\-–—]",
    re.IGNORECASE,
)


def _addresses_producer(head: str) -> bool:
    return bool(_EN_PRODUCTION.search(head) or _AR_PRODUCTION.search(head) or _EN_ROLE.search(head)
                or _AR_ROLE.search(head) or _EN_ROLE_WEAK.search(head) or _EN_ADDRESSEE.search(head)
                or _AR_ADDRESSEE.search(head)
                or re.search(r"\b(?:tools?|machines?|services?|software|programs?|systems?|models?|generators?|"
                             r"engines?|bots?)\b", head, re.IGNORECASE)
                or re.search(r"\b(?:the\s+|any\s+)?(?:reader|readers|user|users)\b", head, re.IGNORECASE))


def _sentence_injected(t: str) -> bool:
    # Producing the reply is not a role tafsir text ever addresses or names.
    if _EN_ROLE.search(t) or _AR_ROLE.search(t):
        return True
    if _EN_DEDICATION.search(t) or _AR_DEDICATION.search(t):
        return True
    m = _DEDICATION_HEAD.match(t)
    if m and _addresses_producer(m.group(1)):
        return True
    en_dir = bool(_EN_IMPERATIVE.search(t))
    if en_dir and _EN_PRODUCTION.search(t):
        return True
    if _AR_DIRECTIVE.search(t) and _AR_PRODUCTION.search(t):
        return True
    if en_dir and (_EN_ROLE_WEAK.search(t) or _EN_RESPONSE_META.search(t)):
        return True
    if en_dir and _EN_ADDRESSEE.search(t) and re.search(r"\b(you|your)\b", t, re.IGNORECASE):
        return True
    # The software addressed by name, then ordered: "Assistant, disregard…",
    # "AI: say…".
    if en_dir and _EN_VOCATIVE.match(t):
        return True
    if _EN_RESPONSE_META.search(t) and _EN_ADDRESSEE.search(t):
        return True
    ar_dir = bool(_AR_DIRECTIVE.search(t))
    ar_role = bool(_AR_ROLE.search(t) or _AR_ADDRESSEE.search(t))
    ar_meta = bool(_AR_RESPONSE_META.search(t))
    if ar_dir and (ar_role or ar_meta):
        return True
    if ar_meta and ar_role:
        return True
    # "يا من يقرأ هذا، ليكتب…": a vocative to whoever is reading, with an order.
    if ar_dir and re.search(rf"(?<![{_AR}])(?:يا|أيها|ايها)\s+(?:من|الذي|التي)\s+[يت][{_AR}]+\s+هذا", t):
        return True
    return False


def _units(text: str) -> List[str]:
    """Sentences, keeping a header line together with the line under it."""
    return [s for s in _SENTENCES.split(text) if s and s.strip()]


def _flags(text: str) -> Tuple[List[str], List[bool]]:
    units = _units(text)
    flags = [_sentence_injected(u) for u in units]
    for i, u in enumerate(units):
        if _HEADER.match(u):
            # A header line is an instruction when it or the line under it
            # gives one (any directive form or output/role word).
            block = u + " " + (units[i + 1] if i + 1 < len(units) else "")
            if re.match(r"\s*(?:#{1,6}\s|>)", u) or _EN_IMPERATIVE.search(block) or _AR_DIRECTIVE.search(block) \
                    or _EN_RESPONSE_META.search(block) \
                    or _AR_RESPONSE_META.search(block) or _EN_ROLE.search(block) or _AR_ROLE.search(block) \
                    or re.search(r"\b(instruction|directive|output|override|system)\b|تعليم|توجيه", u, re.I):
                flags[i] = True
                if i + 1 < len(units):
                    flags[i + 1] = True
    return units, flags


def is_injected(text: str) -> bool:
    """True for evidence text that addresses whatever writes the answer or directs the answer."""
    t = _norm(text)
    if not t:
        return False
    if _STRUCTURAL.search(t):
        return True
    return any(_flags(t)[1])


def injected_sentences(text: str) -> List[str]:
    """The sentences of ``text`` that carry instructions (all of it when the
    text impersonates prompt structure)."""
    t = _norm(text)
    if not t:
        return []
    if _STRUCTURAL.search(t):
        return [t]
    units, flags = _flags(t)
    return [u for u, f in zip(units, flags) if f]


def split_tainted(text: str) -> Tuple[str, str]:
    """
    (clean part, tainted part) of an evidence text.

    The tainted part is what an instruction controls: the instruction itself,
    everything after the first instruction (its payload) and, when the
    instruction is the last thing in the text or points back at what precedes
    it, the two sentences before it. The clean part is ordinary evidence.
    Text with no instruction is all clean.
    """
    t = _norm(text)
    if not t:
        return "", ""
    if _STRUCTURAL.search(t):
        return "", t
    units, flags = _flags(t)
    if not any(flags):
        return text, ""
    first = flags.index(True)
    last = len(flags) - 1 - flags[::-1].index(True)
    start = first
    if any(_BACK_REFERENCE.search(u) for u, f in zip(units, flags) if f):
        start = max(0, first - 2)
    return " ".join(units[:start]), " ".join(units[start:])
