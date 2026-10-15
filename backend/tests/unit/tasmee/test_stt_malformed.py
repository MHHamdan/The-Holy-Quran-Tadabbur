"""A malformed hosted-STT body must raise a classified MALFORMED error.

Before, a non-string ``text`` raised AttributeError inside ``.strip()``, which
escaped the HF error handling and could kill the Tasmee WebSocket loop.
No network: the HF client is replaced by a local fake.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import SecretStr

from app.ai.hf_client import HFErrorKind, HFInferenceError
from app.core.config import settings
from app.stt.providers import huggingface as hfstt


class _FakeASR:
    def __init__(self, output):
        self.output = output

    def automatic_speech_recognition(self, payload, model=None, extra_body=None):
        return self.output


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(settings, "hf_token", SecretStr("hf_unit_test_token_0000000000000000"))

    def make(output):
        monkeypatch.setattr(hfstt, "task_client", lambda task, **kw: _FakeASR(output))
        return hfstt.HuggingFaceSTTProvider()

    return make


@pytest.mark.parametrize("bad_text", [{"x": 1}, 42, ["a", "b"]])
def test_non_string_text_is_malformed(provider, bad_text):
    p = provider(SimpleNamespace(text=bad_text, chunks=None))
    with pytest.raises(HFInferenceError) as exc:
        p.transcribe(np.zeros(16000, dtype=np.float32))
    assert exc.value.kind == HFErrorKind.MALFORMED


@pytest.mark.parametrize(
    "chunk",
    [
        SimpleNamespace(text={"w": 1}, timestamp=[0.0, 0.5]),
        SimpleNamespace(text="كلمة", timestamp=["abc", 0.5]),
        SimpleNamespace(text="كلمة", timestamp=5),
    ],
)
def test_bad_chunk_is_malformed(provider, chunk):
    p = provider(SimpleNamespace(text="كلمة", chunks=[chunk]))
    with pytest.raises(HFInferenceError) as exc:
        p.transcribe(np.zeros(16000, dtype=np.float32))
    assert exc.value.kind == HFErrorKind.MALFORMED


def test_none_text_is_silence(provider):
    p = provider(SimpleNamespace(text=None, chunks=None))
    assert p.transcribe(np.zeros(16000, dtype=np.float32)).segments == []
