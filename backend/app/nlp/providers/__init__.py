"""
NLP provider implementations.

Each provider implements BaseNLPProvider interface:
- QuranicCorpusProvider: Scholar-verified I'rab for Quranic verses (most accurate)
- FarasaProvider: Primary provider for Quranic Arabic
- CamelProvider: Secondary with dialectal support
- StanzaProvider: General fallback
"""
from app.nlp.providers.farasa import FarasaProvider
from app.nlp.providers.camel import CamelProvider
from app.nlp.providers.stanza import StanzaProvider
from app.nlp.providers.quranic_corpus import QuranicCorpusProvider, get_qac_provider

__all__ = [
    "QuranicCorpusProvider",
    "FarasaProvider",
    "CamelProvider",
    "StanzaProvider",
    "get_qac_provider",
]
