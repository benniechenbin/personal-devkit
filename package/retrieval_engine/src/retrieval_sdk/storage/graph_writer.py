from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from retrieval_sdk.domain import GraphEntity, GraphRelation


@runtime_checkable
class GraphWriter(Protocol):
    """把图谱抽取结果写入图谱后端的协议。"""

    def upsert_entity(self, entity: GraphEntity, *, source: str | None = None) -> None:
        """创建或更新一个图谱实体。"""
        ...

    def upsert_relation(
        self,
        relation: GraphRelation,
        *,
        source: str | None = None,
    ) -> None:
        """创建或更新一条图谱关系。"""
        ...

    def upsert_entities(
        self,
        entities: Sequence[GraphEntity],
        *,
        source: str | None = None,
    ) -> None:
        """创建或更新多个图谱实体。"""
        ...

    def upsert_relations(
        self,
        relations: Sequence[GraphRelation],
        *,
        source: str | None = None,
    ) -> None:
        """创建或更新多条图谱关系。"""
        ...

    def remove_source(self, source: str) -> None:
        """删除只属于某个 source 的图谱资产。"""
        ...

    def clear(self) -> None:
        """删除全部图谱数据。"""
        ...
