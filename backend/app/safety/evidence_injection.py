"""
Instructions planted in retrieved evidence.

Tafsir speaks about the verse, its words and its reports; it never addresses
the software that reads it, nor tells it what to put in "the answer" or what
to tell "the user". A chunk that does either is an injection attempt,
whatever its wording: it stays fenced as data and is still shown verbatim,
but it can never support a claim, and an answer that repeats what it asks
for is treated as obeying it.

Detection is structural, not a list of known attack strings: an addressee
that is the assistant (AI, model, chatbot, assistant, system, "whoever
answers"), or a directive about the response (your answer/reply, when
answering, tell/assure the user/reader/questioner, the citation policy),
combined with an imperative or a meta-instruction marker. Classic
role/chat-template markers and "ignore previous instructions" count alone.
"""
from __future__ import annotations

import re
import unicodedata

_EN_ADDRESSEE = re.compile(
    r"\b(assistant|chat\s*bot|chatbot|bot|a\.?i\.?|artificial\s+intelligence|language\s+model|llm|"
    r"gpt|model|system|ai\s+model)\b",
    re.IGNORECASE,
)
_EN_RESPONSE_META = re.compile(
    r"\byour\s+(answer|reply|response|output|summary|completion)\b"
    r"|\bin\s+(the|your)\s+(answer|reply|response|output)\b"
    r"|\bwhen\s+(you\s+)?(answer|answering|reply|replying|respond|responding|summari[sz]ing|summari[sz]e)\b"
    r"|\b(tell|inform|assure|remind|convince|advise|instruct)\s+(the\s+)?(user|reader|questioner|asker|"
    r"person\s+asking|people\s+asking|audience)\b"
    r"|\b(the\s+)?(user|questioner|asker)\s+(should|must)\s+be\s+told\b"
    r"|\b(citation|grounding|safety|source)\s+(policy|policies|rules?|requirements?)\b"
    r"|\b(previous|prior|earlier|above|system)\s+(instructions?|prompts?|rules?)\b"
    r"|\bnote\s+(to|for)\s+(the\s+)?(reader|model|assistant|ai|bot|system)\b",
    re.IGNORECASE,
)
_EN_IMPERATIVE = re.compile(
    r"(^|[.:;!\n\]]\s*|,\s*)(please\s+)?(ignore|disregard|forget|override|say|state|mention|add|write|"
    r"tell|assure|claim|answer|respond|reply|output|print|insist|explain|include|declare|confirm|"
    r"pretend|act|stop|do\s+not|don't|never|always)\b"
    r"|\b(you\s+(must|should|need\s+to|have\s+to|are\s+to|will))\b",
    re.IGNORECASE,
)
_AR_ADDRESSEE = re.compile(
    r"(?<![ء-ي])(لل|ال|ل)?(مساعد\s+(الذكي|الآلي|الرقمي)|المساعد|مساعد|الذكاء\s+الاصطناعي|الذكاء\s+الصناعي|"
    r"نموذج\s+اللغوي|نموذج\s+لغوي|"
    r"نموذج\s+(اللغة|الذكاء)|النموذج\s+اللغوي|نموذج\s+الذكاء|البوت|الروبوت|لمن\s+يجيب|من\s+يجيب\s+(على|عن)|"
    r"برنامج\s+المحادثة)(?![ء-ي])"
)
_AR_RESPONSE_META = re.compile(
    r"((?<![ء-ي])(إجابتك|اجابتك|جوابك)(?![ء-ي])|عند\s+(الإجابة|الاجابة|الرد)\s+(على|عن)\s+(هذا|السؤال|سؤال)|"
    r"عند\s+(الإجابة|الاجابة|الرد)\s*[،,:]?\s*(اذكر|قل|اكتب|أضف|اضف|أكد|اكد|صرح|بين|أخبر|اخبر)|"
    r"(أخبر|اخبر|قل\s+ل|أكد\s+ل|اكد\s+ل|طمئن|أقنع|اقنع|أبلغ|ابلغ)\s*(ال)?(سائل|مستخدم|قارئ|سائلين|مستخدمين)|"
    r"(ال)?تعليمات\s+(السابقة|النظام|للنظام)|تعليمات\s+(إلى|الى|لل)|سياسة\s+(الاستشهاد|المصادر))"
)
_AR_IMPERATIVE = re.compile(
    r"(?<![ء-ي])[وف]?(تجاهل|انس|انسَ|اكتب|أضف|اضف|قل|أخبر|اخبر|اذكر|صرح|صرّح|أكد|اكد|أجب|اجب|"
    r"تصرف|لا\s+تذكر|لا\s+تستشهد|يجب\s+أن\s+تقول|عليك\s+أن)(?![ء-ي])"
)
_STRUCTURAL = re.compile(
    r"\b(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier|your)\s+"
    r"(instructions|rules|prompts?)\b|\b(system|developer)\s+prompt\b"
    r"|<\s*/?\s*(system|assistant|source|question|user|im_start|im_end)\b|<\|[^|>]{0,40}\|>"
    r"|^\s*(system|assistant|user)\s*:|\bnew\s+system\s+prompt\b"
    r"|تجاهل\s+(كل\s+|جميع\s+)?(التعليمات|الأوامر|القواعد)",
    re.IGNORECASE | re.MULTILINE,
)


_CLAUSES = re.compile(r"(?<=[.!?؟؛;\n])\s*")


def is_injected(text: str) -> bool:
    """True for evidence text that addresses the assistant or directs the answer.

    Judged sentence by sentence: an addressee and a directive must occur in
    the same sentence (a long tafsir chunk contains every common word
    somewhere)."""
    t = unicodedata.normalize("NFKC", text or "")
    if not t:
        return False
    if _STRUCTURAL.search(t):
        return True
    return any(_sentence_injected(s) for s in _CLAUSES.split(t) if s.strip())


def injected_sentences(text: str) -> list:
    """The sentences of ``text`` that carry instructions (all of it when the
    text impersonates prompt structure)."""
    t = unicodedata.normalize("NFKC", text or "")
    if not t:
        return []
    if _STRUCTURAL.search(t):
        return [t]
    return [s for s in _CLAUSES.split(t) if s.strip() and _sentence_injected(s)]


def _sentence_injected(t: str) -> bool:
    en_addr = bool(_EN_ADDRESSEE.search(t))
    en_meta = bool(_EN_RESPONSE_META.search(t))
    en_imp = bool(_EN_IMPERATIVE.search(t))
    if en_meta and (en_addr or en_imp):
        return True
    if en_addr and en_imp and re.search(r"\b(you|your)\b", t, re.IGNORECASE):
        return True
    ar_addr = bool(_AR_ADDRESSEE.search(t))
    ar_meta = bool(_AR_RESPONSE_META.search(t))
    ar_imp = bool(_AR_IMPERATIVE.search(t))
    if ar_meta and (ar_addr or ar_imp):
        return True
    if ar_addr and ar_imp:
        return True
    return False
