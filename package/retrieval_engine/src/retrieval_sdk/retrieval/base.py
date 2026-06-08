from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from retrieval_sdk.domain import DocumentChunk, ScoredDocument

RetrieverResult = ScoredDocument | DocumentChunk


@runtime_checkable
class Retriever(Protocol):
    """文本检索器协议。

    适用于向量召回、词法召回、混合召回等返回文档片段的检索器。
    图谱召回器返回 GraphContext，不强制实现这个协议。
    """

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> Sequence[RetrieverResult]:
        """根据查询返回候选文档。"""
        ...