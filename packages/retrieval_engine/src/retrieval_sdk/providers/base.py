from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from retrieval_sdk.domain import DocumentChunk


@runtime_checkable
class EmbeddingProvider(Protocol):
    """宿主项目提供的文本 embedding 实现协议。"""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """批量向量化文档文本。"""
        ...

    def embed_query(self, text: str) -> list[float]:
        """向量化查询文本。"""
        ...


@runtime_checkable
class RerankerProvider(Protocol):
    """宿主项目提供的 rerank 实现协议。"""

    def score(self, query: str, documents: Sequence[DocumentChunk]) -> list[float]:
        """为每个候选文档返回一个相关性分数。"""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """图谱抽取和总结流程使用的 LLM 调用协议。"""

    def complete(self, messages: Sequence[dict[str, str]], **kwargs) -> str:
        """基于 chat-style messages 返回文本补全结果。"""
        ...
