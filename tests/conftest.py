from __future__ import annotations

import pytest
from document_engine.schema import Fragment
from retrieval_engine import DocumentChunk

from tests.support.fakes import (
    FakeEmbeddingProvider,
    FakeLLMProvider,
    InMemoryCommunityStorage,
    InMemoryGraphWriter,
    InMemoryVectorStorage,
)


@pytest.fixture
def sample_fragments() -> list[Fragment]:
    return [
        Fragment(
            type="text",
            page_num=0,
            y0=10.0,
            content="GraphRAG 结合向量检索和知识图谱进行复杂问题召回。",
            source="test",
        ),
        Fragment(
            type="text",
            page_num=0,
            y0=20.0,
            content="Qdrant 可以存储文本向量，Neo4j 可以存储实体关系。",
            source="test",
        ),
    ]


@pytest.fixture
def sample_documents() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            page_content="GraphRAG 结合向量检索和知识图谱进行复杂问题召回。",
            metadata={"source": "demo_1.md"},
        ),
        DocumentChunk(
            page_content="Qdrant 可以存储文本向量，Neo4j 可以存储实体关系。",
            metadata={"source": "demo_2.md"},
        ),
    ]


@pytest.fixture
def fake_embedding_provider() -> FakeEmbeddingProvider:
    return FakeEmbeddingProvider()


@pytest.fixture
def fake_llm_provider() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest.fixture
def in_memory_vector_storage() -> InMemoryVectorStorage:
    return InMemoryVectorStorage()


@pytest.fixture
def in_memory_graph_writer() -> InMemoryGraphWriter:
    return InMemoryGraphWriter()


@pytest.fixture
def in_memory_community_storage() -> InMemoryCommunityStorage:
    return InMemoryCommunityStorage()