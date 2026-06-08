from __future__ import annotations

from typing import Protocol, runtime_checkable

from retrieval_sdk.domain import (
    CommunityCandidate,
    CommunityDetectionReport,
    CommunitySummary,
)


@runtime_checkable
class CommunityStorage(Protocol):
    """聚落检测和聚落总结持久化协议。"""

    def detect_leiden_communities(
        self,
        *,
        graph_name: str = "knowledge_graph",
        node_label: str = "Entity",
        relationship_type: str = "RELATION",
        write_property: str = "communityId",
        orientation: str = "UNDIRECTED",
        random_seed: int = 42,
        concurrency: int = 1,
        drop_existing_projection: bool = True,
    ) -> CommunityDetectionReport:
        """运行 Leiden 聚落检测，并把聚落 id 写入节点。"""
        ...

    def list_unsummarized_communities(
        self,
        *,
        threshold: int = 20,
        top_node_limit: int = 30,
        limit: int | None = None,
    ) -> list[CommunityCandidate]:
        """返回仍需要 LLM 总结的聚落。"""
        ...

    def save_community_summary(
        self,
        *,
        community_id: int | str,
        size: int,
        summary: CommunitySummary,
    ) -> None:
        """持久化一个聚落总结。"""
        ...
