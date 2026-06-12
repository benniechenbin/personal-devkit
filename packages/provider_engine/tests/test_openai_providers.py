from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
from provider_engine import ChatMessage
from provider_engine._messages import normalize_messages
from provider_engine.embeddings import OpenAIEmbeddingProvider
from provider_engine.errors import ProviderCallError, ProviderConfigurationError
from provider_engine.llms import OpenAIChatProvider


class FakeChatCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            model=kwargs["model"],
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="hello"),
                )
            ],
            usage=SimpleNamespace(
                model_dump=lambda: {
                    "prompt_tokens": 3,
                    "completion_tokens": 2,
                    "total_tokens": 5,
                }
            ),
        )


class FailingCompletions:
    def create(self, **kwargs):
        raise TimeoutError("timeout")


class FakeEmbeddingCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            model=kwargs["model"],
            data=[
                SimpleNamespace(embedding=[1.0, 0.0]),
                SimpleNamespace(embedding=[0.0, 1.0]),
            ],
            usage=SimpleNamespace(
                model_dump=lambda: {
                    "prompt_tokens": 4,
                    "total_tokens": 4,
                }
            ),
        )


class FailingEmbeddings:
    def create(self, **kwargs):
        raise RuntimeError("embedding failed")


def test_openai_chat_provider_returns_content_and_passes_options():
    completions = FakeChatCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    provider = OpenAIChatProvider(model="default-model", client=client)

    content = provider.complete(
        [{"role": "user", "content": "hi"}],
        model="route-model",
        temperature=0,
    )

    assert content == "hello"
    assert completions.calls[0]["model"] == "route-model"
    assert completions.calls[0]["temperature"] == 0
    assert completions.calls[0]["messages"] == [{"role": "user", "content": "hi"}]


def test_openai_chat_provider_wraps_call_errors():
    client = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    provider = OpenAIChatProvider(model="default-model", client=client)

    with pytest.raises(ProviderCallError):
        provider.complete([{"role": "user", "content": "hi"}])


def test_normalize_messages_preserves_chat_message_name():
    messages = normalize_messages([ChatMessage(role="user", content="hi", name="tester")])

    assert messages == [{"role": "user", "content": "hi", "name": "tester"}]


def test_normalize_messages_rejects_missing_role_or_content():
    with pytest.raises(ProviderConfigurationError):
        normalize_messages([{"role": "user"}])


def test_openai_chat_provider_passes_compatible_client_options(monkeypatch):
    captured: dict[str, object] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.chat = SimpleNamespace(completions=FakeChatCompletions())

    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=FakeOpenAI, AsyncOpenAI=FakeOpenAI),
    )
    provider = OpenAIChatProvider(
        model="default-model",
        api_key="key",
        base_url="https://gateway.example/v1",
        timeout=12.5,
    )

    assert provider.complete([{"role": "user", "content": "hi"}]) == "hello"
    assert captured == {
        "api_key": "key",
        "base_url": "https://gateway.example/v1",
        "timeout": 12.5,
    }


def test_openai_embedding_provider_matches_retrieval_protocol_shape():
    embeddings = FakeEmbeddingCompletions()
    client = SimpleNamespace(embeddings=embeddings)
    provider = OpenAIEmbeddingProvider(model="embed-model", client=client)

    vectors = provider.embed_documents(["a", "b"])
    query = provider.embed_query("q")

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert query == [1.0, 0.0]
    assert embeddings.calls[0]["input"] == ["a", "b"]
    assert embeddings.calls[1]["input"] == ["q"]


def test_openai_embedding_provider_wraps_call_errors():
    client = SimpleNamespace(embeddings=FailingEmbeddings())
    provider = OpenAIEmbeddingProvider(model="embed-model", client=client)

    with pytest.raises(ProviderCallError):
        provider.embed_query("q")


def test_openai_embedding_provider_passes_compatible_client_options(monkeypatch):
    captured: dict[str, object] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.embeddings = FakeEmbeddingCompletions()

    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=FakeOpenAI, AsyncOpenAI=FakeOpenAI),
    )
    provider = OpenAIEmbeddingProvider(
        model="embed-model",
        api_key="key",
        base_url="https://gateway.example/v1",
        timeout=12.5,
    )

    assert provider.embed_query("q") == [1.0, 0.0]
    assert captured == {
        "api_key": "key",
        "base_url": "https://gateway.example/v1",
        "timeout": 12.5,
    }
