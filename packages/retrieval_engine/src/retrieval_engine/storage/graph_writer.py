from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from retrieval_engine.domain import GraphEntity, GraphExtraction, GraphRelation


@runtime_checkable
class GraphWriter(Protocol):
    """将图谱抽取结果持久化到图后端的协议。

    该协议支持增量更新和基于 source 的数据生命周期管理。
    """

    def upsert_extraction(
        self,
        extraction: GraphExtraction,
        *,
        source: str | None = None,
    ) -> None:
        """创建或更新一次完整的图谱抽取结果。

        如果是增量更新，实现应负责维护实体和关系的属性合并或版本更新。
        :param extraction: 抽取的实体和关系集合。
        :param source: 数据来源标识符（如文件名或 URL），用于后续的追踪和清理。
        """
        ...

    def upsert_entity(self, entity: GraphEntity, *, source: str | None = None) -> None:
        """创建或更新单个图谱实体。

        :param entity: 实体领域对象。
        :param source: 数据来源标识符。
        """
        ...

    def upsert_relation(
        self,
        relation: GraphRelation,
        *,
        source: str | None = None,
    ) -> None:
        """创建或更新单条图谱关系。

        :param relation: 关系领域对象。
        :param source: 数据来源标识符。
        """
        ...

    def upsert_entities(
        self,
        entities: Sequence[GraphEntity],
        *,
        source: str | None = None,
    ) -> None:
        """批量创建或更新多个图谱实体。"""
        ...

    def upsert_relations(
        self,
        relations: Sequence[GraphRelation],
        *,
        source: str | None = None,
    ) -> None:
        """批量创建或更新多条图谱关系。"""
        ...

    def remove_source(self, source: str) -> None:
        """删除关联到特定 source 的所有图谱资产。

        该操作通常用于文件重传或删除时的清理。
        """
        ...

    def clear(self) -> None:
        """清空图谱后端的所有数据。"""
        ...
