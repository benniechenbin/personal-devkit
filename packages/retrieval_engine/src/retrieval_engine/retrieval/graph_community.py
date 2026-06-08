from __future__ import annotations

from collections.abc import Callable, Sequence

from retrieval_engine.domain import GraphCommunityHit, GraphContext
from retrieval_engine.storage import GraphStorage

CommunityFormatter = Callable[[Sequence[GraphCommunityHit]], str]


class CommunityGraphRetriever:
    """当图谱存在聚落数据时，召回宏观聚落上下文。"""

    def __init__(
        self,
        storage: GraphStorage,
        *,
        formatter: CommunityFormatter | None = None,
    ) -> None:
        self.storage = storage
        self.formatter = formatter or format_community_hits

    def search(self, keyword: str, limit: int = 3) -> GraphContext:
        if not keyword.strip():
            return GraphContext()
        hits = self.storage.search_communities(keyword, limit=limit)
        return GraphContext(communities=self.formatter(hits))


def format_community_hits(hits: Sequence[GraphCommunityHit]) -> str:
    if not hits:
        return ""

    lines = ["【宏观聚落背景】"]
    for hit in hits:
        cluster_type = hit.cluster_type or "聚落"
        lines.append(f"- [{cluster_type}] {hit.name}: {hit.summary}")
    return "\n".join(lines)
