"""
Hugging Face LLM provider — mocked unit tests (no network, no HF credit).

Covers the upstream failure matrix required for production: valid response,
timeout, 401, 403, 402/429 quota, unavailable model, malformed response,
network outage, missing token, and that no error ever carries the token.
"""

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from huggingface_hub.errors import HfHubHTTPError
from pydantic import SecretStr

from app.ai import hf_client
from app.ai.hf_client import HFErrorKind, HFInferenceError, classify_exception
from app.core.config import Settings, settings
from app.rag import llm_provider
from app.rag.llm_provider import HuggingFaceLLM

FAKE_TOKEN = "hf_unit_test_token_never_real_0123456789"


def _http_error(status: int) -> HfHubHTTPError:
    request = httpx.Request("POST", "https://router.huggingface.co/v1/chat/completions")
    # The body echoes a secret-looking string to prove it never leaks.
    response = httpx.Response(status, request=request, text=f"upstream body {FAKE_TOKEN}")
    return HfHubHTTPError(f"{status} error {FAKE_TOKEN}", response=response)


def _completion(content="Answer [Ibn Kathir, 2:255]", model="Qwen/Qwen3-235B-A22B-Instruct-2507"):
    return SimpleNamespace(
        model=model,
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=30, total_tokens=150),
    )


class _FakeClient:
    """Stands in for AsyncInferenceClient; replays scripted outcomes."""

    def __init__(self, outcomes, calls):
        self._outcomes = outcomes
        self._calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def chat_completion(self, **kwargs):
        self._calls.append(kwargs)
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        if callable(outcome):
            return await outcome()
        return outcome


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setattr(settings, "hf_token", SecretStr(FAKE_TOKEN))
    yield FAKE_TOKEN


@pytest.fixture
def fake_router(monkeypatch, token):
    """Patch the router client; returns (outcomes list, recorded calls)."""
    outcomes, calls = [], []
    monkeypatch.setattr(
        llm_provider, "router_chat_client", lambda async_=True: _FakeClient(outcomes, calls)
    )
    return outcomes, calls


def _generate(llm, **kw):
    return asyncio.run(llm.generate(system_prompt="SYS", user_message="USER", **kw))


# ---------------------------------------------------------------- success path


def test_valid_response_preserves_messages_and_usage(fake_router):
    outcomes, calls = fake_router
    outcomes.append(_completion())
    llm = HuggingFaceLLM(model="org/model:cheapest")

    resp = _generate(llm, max_tokens=321, temperature=0.2)

    assert resp.content == "Answer [Ibn Kathir, 2:255]"
    assert resp.provider == "huggingface"
    assert resp.model == "Qwen/Qwen3-235B-A22B-Instruct-2507"
    assert (resp.prompt_tokens, resp.completion_tokens, resp.tokens_used) == (120, 30, 150)
    sent = calls[0]
    # System/user separation, temperature and max tokens are passed through.
    assert sent["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]
    assert sent["max_tokens"] == 321 and sent["temperature"] == 0.2
    assert sent["model"] == "org/model:cheapest"


def test_reasoning_block_is_stripped(fake_router):
    outcomes, _ = fake_router
    outcomes.append(_completion(content="<think>private chain of thought</think>\nFinal answer."))
    resp = _generate(HuggingFaceLLM())
    assert resp.content == "Final answer."


def test_json_mode_falls_back_when_provider_rejects_response_format(fake_router):
    outcomes, calls = fake_router
    outcomes.extend([_http_error(400), _completion(content='{"ok": true}')])
    resp = _generate(HuggingFaceLLM(), json_mode=True)
    assert resp.content == '{"ok": true}'
    assert "response_format" in calls[0] and "response_format" not in calls[1]


# --------------------------------------------------------------- failure matrix


@pytest.mark.parametrize(
    "status,kind",
    [
        (401, HFErrorKind.AUTH),
        (403, HFErrorKind.FORBIDDEN),
        (402, HFErrorKind.QUOTA),
        (429, HFErrorKind.QUOTA),
        (404, HFErrorKind.MODEL_UNAVAILABLE),
        (503, HFErrorKind.MODEL_UNAVAILABLE),
        (422, HFErrorKind.BAD_REQUEST),
    ],
)
def test_http_errors_map_to_controlled_kinds(fake_router, status, kind):
    outcomes, calls = fake_router
    outcomes.append(_http_error(status))
    with pytest.raises(HFInferenceError) as info:
        _generate(HuggingFaceLLM())
    assert info.value.kind == kind
    assert info.value.status_code == status
    assert len(calls) == 1  # client errors / quota are not retried


def test_upstream_5xx_is_retried_once_then_succeeds(fake_router, monkeypatch):
    monkeypatch.setattr(llm_provider.asyncio, "sleep", _no_sleep)
    outcomes, calls = fake_router
    outcomes.extend([_http_error(500), _completion()])
    resp = _generate(HuggingFaceLLM())
    assert resp.content.startswith("Answer")
    assert len(calls) == 2


def test_network_outage_is_classified_after_retry(fake_router, monkeypatch):
    monkeypatch.setattr(llm_provider.asyncio, "sleep", _no_sleep)
    outcomes, calls = fake_router
    outcomes.extend([httpx.ConnectError("dns failure"), httpx.ConnectError("dns failure")])
    with pytest.raises(HFInferenceError) as info:
        _generate(HuggingFaceLLM())
    assert info.value.kind == HFErrorKind.NETWORK
    assert len(calls) == 2


def test_timeout_is_enforced(fake_router):
    outcomes, _ = fake_router

    async def slow():
        await asyncio.sleep(5)

    outcomes.append(slow)
    with pytest.raises(HFInferenceError) as info:
        _generate(HuggingFaceLLM(timeout=0.05))
    assert info.value.kind == HFErrorKind.TIMEOUT


@pytest.mark.parametrize(
    "payload",
    [
        SimpleNamespace(model="m", choices=[], usage=None),
        SimpleNamespace(
            model="m", choices=[SimpleNamespace(message=SimpleNamespace(content=""))], usage=None
        ),
        SimpleNamespace(
            model="m", choices=[SimpleNamespace(message=SimpleNamespace(content=None))], usage=None
        ),
        SimpleNamespace(model="m"),
    ],
)
def test_malformed_upstream_response(fake_router, payload):
    outcomes, _ = fake_router
    outcomes.append(payload)
    with pytest.raises(HFInferenceError) as info:
        _generate(HuggingFaceLLM())
    assert info.value.kind == HFErrorKind.MALFORMED


def test_missing_token_is_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "hf_token", None)
    with pytest.raises(HFInferenceError) as info:
        _generate(HuggingFaceLLM())
    assert info.value.kind == HFErrorKind.NOT_CONFIGURED
    assert not asyncio.run(HuggingFaceLLM().health_check())


def test_errors_never_contain_token_or_upstream_body(fake_router):
    outcomes, _ = fake_router
    outcomes.append(_http_error(401))
    with pytest.raises(HFInferenceError) as info:
        _generate(HuggingFaceLLM())
    rendered = f"{info.value} {info.value!r}"
    assert FAKE_TOKEN not in rendered
    assert "upstream body" not in rendered


def test_classify_unknown_exception_is_upstream():
    err = classify_exception(RuntimeError("weird"), "chat")
    assert err.kind == HFErrorKind.UPSTREAM


# --------------------------------------------------------------- configuration


def test_token_aliases_and_secret_masking(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("HUGGINGFACE_TOKEN", FAKE_TOKEN)
    s = Settings(_env_file=None)
    assert s.hf_token.get_secret_value() == FAKE_TOKEN
    assert FAKE_TOKEN not in repr(s) and FAKE_TOKEN not in str(s.model_dump())


def test_empty_token_counts_as_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "hf_token", SecretStr("   "))
    assert hf_client.get_hf_token() is None
    assert not llm_provider.llm_configured()


@pytest.mark.parametrize(
    "model,provider,expected",
    [
        ("org/m", "auto", "org/m"),
        ("org/m", "cheapest", "org/m:cheapest"),
        ("org/m", "novita", "org/m:novita"),
        ("org/m:fastest", "novita", "org/m:fastest"),  # explicit suffix wins
    ],
)
def test_provider_routing_suffix(model, provider, expected):
    s = Settings(_env_file=None, hf_llm_model=model, hf_llm_provider=provider)
    assert s.hf_llm_model_id == expected


async def _no_sleep(*_args, **_kwargs):
    return None


def test_vendored_httpx_errors_are_classified():
    """huggingface_hub 2.x raises from its vendored httpx2 package."""
    httpx2 = pytest.importorskip("httpx2")
    assert classify_exception(httpx2.ReadTimeout("slow"), "zero-shot").kind == HFErrorKind.TIMEOUT
    assert classify_exception(httpx2.ConnectError("down"), "zero-shot").kind == HFErrorKind.NETWORK


def test_model_not_served_by_enabled_provider_is_unavailable(fake_router):
    """The router returns 400 when no enabled provider serves the model."""
    outcomes, _ = fake_router
    request = httpx.Request("POST", "https://router.huggingface.co/v1/chat/completions")
    response = httpx.Response(400, request=request)
    outcomes.append(
        HfHubHTTPError(
            "400 Bad Request: The requested model 'x/y' is not supported by any provider you have enabled.",
            response=response,
        )
    )
    with pytest.raises(HFInferenceError) as info:
        _generate(HuggingFaceLLM())
    assert info.value.kind == HFErrorKind.MODEL_UNAVAILABLE
