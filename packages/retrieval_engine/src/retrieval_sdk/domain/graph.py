from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GraphEntity:
    id: str
    type: str
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphRelation:
    source: str
    target: str
    relation: str
    source_summary: str = ""
    target_summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphCommunity:
    community_id: int | str
    name: str
    summary: str = ""
    size: int = 0
    cluster_type: str = ""
    confidence: float | None = None


@dataclass(slots=True)
class GraphExtraction:
    entities: list[GraphEntity]
    relationships: list[GraphRelation]


@dataclass(slots=True)
class CommunitySummary:
    name: str
    summary: str = ""
    cluster_type: str = ""
    confidence: float | None = None


@dataclass(slots=True)
class CommunityCandidate:
    community_id: int | str
    size: int
    top_nodes: list[str]


@dataclass(slots=True)
class CommunityDetectionReport:
    graph_name: str
    node_count: int = 0
    relationship_count: int = 0
    community_count: int = 0
    node_properties_written: int = 0
    modularity: float | None = None


@dataclass(slots=True)
class GraphRelationshipHit:
    source: str
    relation: str
    target: str
    source_summary: str = ""
    target_summary: str = ""
    source_type: str = ""
    target_type: str = ""
    score: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class GraphCommunityHit:
    name: str
    summary: str = ""
    cluster_type: str = ""
    community_id: int | str | None = None
    size: int | None = None
    confidence: float | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class GraphContext:
    relationships: str = ""
    communities: str = ""

    def as_tuple(self) -> tuple[str, str]:
        """兼容旧接口的二元组形态：relationships, communities。"""
        return self.relationships, self.communities
