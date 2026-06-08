from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from rtrieval_engine.domain import GraphCommunityHit, GraphRelationshipHit


@runtime_checkable
class GraphStorage(Protocol):
    """图谱召回器使用的图数据后端协议。"""

    def search_relationships(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[GraphRelationshipHit]:
        """按关键词搜索实体邻域关系。"""
        ...

    def search_communities(
        self,
        keyword: str,
        limit: int = 3,
    ) -> list[GraphCommunityHit]:
        """按关键词搜索聚落总结。"""
        ...


@runtime_checkable
class GraphVectorStorage(Protocol):
    """支持实体向量搜索的图谱后端协议。"""

    def search_relationships_by_vector(
        self,
        vector: Sequence[float],
        *,
        entity_limit: int = 5,
        relationship_limit: int = 20,
    ) -> list[GraphRelationshipHit]:
        """按向量搜索相近实体，并展开其关系。"""
        ...

    def search_communities_by_vector(
        self,
        vector: Sequence[float],
        *,
        entity_limit: int = 5,
        community_limit: int = 3,
    ) -> list[GraphCommunityHit]:
        """按向量搜索相近实体，并返回其所属聚落。"""
        ...
