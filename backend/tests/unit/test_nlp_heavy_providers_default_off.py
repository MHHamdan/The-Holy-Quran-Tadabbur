"""CAMeL Tools and Stanza (heavy local NLP inference) are off by default.

No user-facing endpoint needs them and production does not install them; they
must be opted into with NLP_ENABLE_CAMEL / NLP_ENABLE_STANZA.
"""
from app.core.config import Settings


def test_camel_and_stanza_default_off(monkeypatch):
    monkeypatch.delenv("NLP_ENABLE_CAMEL", raising=False)
    monkeypatch.delenv("NLP_ENABLE_STANZA", raising=False)
    s = Settings()
    assert s.nlp_enable_camel is False
    assert s.nlp_enable_stanza is False


def test_camel_and_stanza_can_be_enabled_explicitly(monkeypatch):
    monkeypatch.setenv("NLP_ENABLE_CAMEL", "true")
    monkeypatch.setenv("NLP_ENABLE_STANZA", "true")
    s = Settings()
    assert s.nlp_enable_camel is True
    assert s.nlp_enable_stanza is True
