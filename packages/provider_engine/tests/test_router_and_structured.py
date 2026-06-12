from __future__ import annotations

import pytest
from provider_engine.errors import ProviderParseError, ProviderRouteError
from provider_engine.routing import ModelRouter
from provider_engine.structured.output import parse_structured_output, structured_complete
from pydantic import BaseModel


class FakeLLM:
    def __init__(self, response: str = '{"steps": ["a", "b"]}') -> None:
        self.response = response
        self.calls: list[dict] = []

    def complete(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})
        return self.response


class FakeEmbedding:
    def embed_query(self, text: str, **kwargs):
        return [float(len(text)), float(kwargs["dim"])]

    def embed_documents(self, texts, **kwargs):
        return [[float(len(text)), float(kwargs["dim"])] for text in texts]


class Plan(BaseModel):
    steps: list[str]


def test_model_router_routes_llm_and_embedding_options():
    router = ModelRouter()
    llm = FakeLLM("ok")
    embedding = FakeEmbedding()

    router.register_llm("planner", llm, model="strong", temperature=0)
    router.register_embedding("default", embedding, dim=2)

    assert router.complete("planner", [{"role": "user", "content": "plan"}]) == "ok"
    assert llm.calls[0]["kwargs"] == {"temperature": 0, "model": "strong"}
    assert router.embed_query("default", "abc") == [3.0, 2.0]
    assert router.embed_documents("default", ["a", "abcd"]) == [[1.0, 2.0], [4.0, 2.0]]


def test_model_router_raises_for_unknown_route():
    router = ModelRouter()

    with pytest.raises(ProviderRouteError):
        router.complete("missing", [])


def test_model_router_raises_for_unknown_embedding_route():
    router = ModelRouter()

    with pytest.raises(ProviderRouteError):
        router.embed_query("missing", "query")


def test_structured_complete_parses_pydantic_model():
    llm = FakeLLM('```json\n{"steps": ["read", "ship"]}\n```')

    plan = structured_complete(llm, [{"role": "user", "content": "make plan"}], Plan)

    assert plan.steps == ["read", "ship"]
    assert llm.calls[0]["messages"][0]["role"] == "system"


def test_parse_structured_output_rejects_invalid_json():
    with pytest.raises(ProviderParseError):
        parse_structured_output("not json", Plan)


def test_parse_structured_output_rejects_pydantic_shape_mismatch():
    with pytest.raises(ProviderParseError):
        parse_structured_output('{"wrong": []}', Plan)
