from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from rtrieval_engine.domain import DocumentChunk, ScoredDocument, VectorRecord

NativeDocument = DocumentChunk


@runtime_checkable
class VectorStore(Protocol):
    """SDK 使用的向量存储后端协议。"""

    def add_documents(self, documents: Sequence[DocumentChunk]) -> None:
        """向现有索引追加文档。"""
        ...

    def replace_documents(self, documents: Sequence[DocumentChunk]) -> None:
        """用给定文档原子替换当前索引。"""
        ...

    def search(self, query: str, top_k: int = 5) -> list[DocumentChunk]:
        """返回与查询最相关的已索引文档。"""
        ...

    def clear(self) -> None:
        """删除全部已索引文档。"""
        ...


@runtime_checkable
class VectorStorage(Protocol):
    """底层向量存储协议。

    存储适配器只接收已经完成 embedding 的向量，不会自行调用模型 provider。
    """

    def add_vectors(self, records: Sequence[VectorRecord]) -> None:
        """向存储追加已向量化的文档记录。"""
        ...

    def replace_vectors(self, records: Sequence[VectorRecord]) -> None:
        """原子替换全部已存储向量。"""
        ...

    def query(self, vector: Sequence[float], top_k: int = 5) -> list[ScoredDocument]:
        """按向量查询，并返回带分数的文档片段。"""
        ...

    def clear(self) -> None:
        """删除全部已存储向量。"""
        ...
