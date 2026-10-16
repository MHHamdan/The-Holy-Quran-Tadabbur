"""The NLP fallback chain honours the NLP_* settings.

config.py turned CAMeL Tools and Stanza off by default, but ChainConfig had its
own hard-coded True defaults, so the chain still loaded both providers.
"""
from app.core.config import settings
from app.nlp.fallback_chain import ChainConfig, NLPFallbackChain


def _provider_names(chain: NLPFallbackChain) -> list[str]:
    chain._init_providers()
    return [type(p).__name__ for p in chain._providers]


def test_default_chain_has_no_camel_or_stanza(monkeypatch):
    # The shipped defaults (test_nlp_heavy_providers_default_off checks them).
    monkeypatch.setattr(settings, "nlp_enable_camel", False)
    monkeypatch.setattr(settings, "nlp_enable_stanza", False)
    names = _provider_names(NLPFallbackChain(ChainConfig(cache_results=False)))
    assert "CamelProvider" not in names
    assert "StanzaProvider" not in names
    assert names[-1] == "StaticNLPProvider"


def test_settings_can_enable_camel(monkeypatch):
    monkeypatch.setattr(settings, "nlp_enable_camel", True)
    assert ChainConfig(cache_results=False).enable_camel is True
