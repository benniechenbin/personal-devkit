from __future__ import annotations

from dataclasses import dataclass

from retrieval_sdk.domain import CommunityDetectionReport
from retrieval_sdk.storage.community import CommunityStorage


@dataclass(slots=True)
class CommunityDetector:
    """通过注入的社区存储运行图谱聚落检测。"""

    storage: CommunityStorage
    graph_name: str = "knowledge_graph"
    node_label: str = "Entity"
    relationship_type: str = "RELATION"
    write_property: str = "communityId"
    orientation: str = "UNDIRECTED"
    random_seed: int = 42
    concurrency: int = 1
    drop_existing_projection: bool = True

    def run(self) -> CommunityDetectionReport:
        return self.storage.detect_leiden_communities(
            graph_name=self.graph_name,
            node_label=self.node_label,
            relationship_type=self.relationship_type,
            write_property=self.write_property,
            orientation=self.orientation,
            random_seed=self.random_seed,
            concurrency=self.concurrency,
            drop_existing_projection=self.drop_existing_projection,
        )
