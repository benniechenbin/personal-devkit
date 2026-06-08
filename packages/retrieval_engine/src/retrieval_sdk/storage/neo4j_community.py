from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from retrieval_sdk.domain import (
    CommunityCandidate,
    CommunityDetectionReport,
    CommunitySummary,
)


class Neo4jCommunityStorage:
    """Neo4j GDS 聚落检测和聚落总结持久化适配器。"""

    def __init__(
        self,
        *,
        driver: Any | None = None,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        verify_connectivity: bool = False,
    ) -> None:
        if driver is None:
            if not uri or not user or password is None:
                raise ValueError("Provide either driver or uri/user/password.")
            driver = self._create_driver(uri=uri, user=user, password=password)

        self.driver = driver
        self.database = database
        if verify_connectivity:
            verify = getattr(self.driver, "verify_connectivity", None)
            if callable(verify):
                verify()

    @classmethod
    def from_uri(
        cls,
        *,
        uri: str,
        user: str,
        password: str,
        database: str | None = None,
        verify_connectivity: bool = False,
    ) -> Neo4jCommunityStorage:
        return cls(
            uri=uri,
            user=user,
            password=password,
            database=database,
            verify_connectivity=verify_connectivity,
        )

    def close(self) -> None:
        close = getattr(self.driver, "close", None)
        if callable(close):
            close()

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
        relationship_projection = {
            relationship_type: {
                "orientation": orientation,
            }
        }
        leiden_config = {
            "writeProperty": write_property,
            "includeIntermediateCommunities": False,
            "randomSeed": random_seed,
            "concurrency": concurrency,
        }

        with self._session() as session:
            if drop_existing_projection:
                session.run(
                    "CALL gds.graph.drop($graph_name, false) YIELD graphName",
                    graph_name=graph_name,
                )

            project_result = session.run(
                """
                CALL gds.graph.project(
                  $graph_name,
                  $node_projection,
                  $relationship_projection
                )
                YIELD nodeCount, relationshipCount
                """,
                graph_name=graph_name,
                node_projection=node_label,
                relationship_projection=relationship_projection,
            ).single()

            leiden_result = session.run(
                """
                CALL gds.leiden.write($graph_name, $config)
                YIELD communityCount, nodePropertiesWritten, modularity
                """,
                graph_name=graph_name,
                config=leiden_config,
            ).single()

        return CommunityDetectionReport(
            graph_name=graph_name,
            node_count=int(_record_get(project_result, "nodeCount", 0) or 0),
            relationship_count=int(_record_get(project_result, "relationshipCount", 0) or 0),
            community_count=int(_record_get(leiden_result, "communityCount", 0) or 0),
            node_properties_written=int(
                _record_get(leiden_result, "nodePropertiesWritten", 0) or 0
            ),
            modularity=_float_or_none(_record_get(leiden_result, "modularity")),
        )

    def list_unsummarized_communities(
        self,
        *,
        threshold: int = 20,
        top_node_limit: int = 30,
        limit: int | None = None,
    ) -> list[CommunityCandidate]:
        community_query = """
        MATCH (entity:Entity)
        WHERE entity.communityId IS NOT NULL
        WITH entity.communityId AS community_id, count(entity) AS size
        WHERE size >= $threshold
        AND NOT EXISTS {
            MATCH (community:Community {communityId: community_id})
            WHERE community.summary IS NOT NULL
        }
        RETURN community_id, size
        ORDER BY size DESC
        """
        if limit is not None:
            community_query += "\nLIMIT $limit"

        with self._session() as session:
            rows = session.run(
                community_query,
                threshold=threshold,
                limit=limit,
            ).data()

            candidates: list[CommunityCandidate] = []
            for row in rows:
                community_id = row.get("community_id")
                size = int(row.get("size") or 0)
                top_nodes = session.run(
                    """
                    MATCH (entity:Entity {communityId: $community_id})-[relation]-()
                    RETURN entity.name AS name, count(relation) AS degree
                    ORDER BY degree DESC
                    LIMIT $top_node_limit
                    """,
                    community_id=community_id,
                    top_node_limit=top_node_limit,
                ).data()
                candidates.append(
                    CommunityCandidate(
                        community_id=community_id,
                        size=size,
                        top_nodes=[
                            str(record.get("name")) for record in top_nodes if record.get("name")
                        ],
                    )
                )

        return candidates

    def save_community_summary(
        self,
        *,
        community_id: int | str,
        size: int,
        summary: CommunitySummary,
    ) -> None:
        with self._session() as session:
            session.run(
                """
                MERGE (community:Community {communityId: $community_id})
                SET community.name = $name,
                    community.summary = $summary,
                    community.size = $size,
                    community.cluster_type = $cluster_type,
                    community.confidence = $confidence
                WITH community
                MATCH (entity:Entity {communityId: $community_id})
                MERGE (entity)-[:IN_COMMUNITY]->(community)
                """,
                community_id=community_id,
                name=summary.name,
                summary=summary.summary,
                size=size,
                cluster_type=summary.cluster_type,
                confidence=summary.confidence,
            )

    def _create_driver(self, *, uri: str, user: str, password: str):
        try:
            from neo4j import GraphDatabase
        except ModuleNotFoundError as exc:
            message = "Install neo4j to use Neo4jCommunityStorage."
            raise RuntimeError(message) from exc
        return GraphDatabase.driver(uri, auth=(user, password))

    @contextmanager
    def _session(self) -> Iterator[Any]:
        if self.database:
            session = self.driver.session(database=self.database)
        else:
            session = self.driver.session()
        try:
            yield session
        finally:
            session.close()


def _record_get(record: Any, key: str, default: Any = None) -> Any:
    if record is None:
        return default
    try:
        return record[key]
    except (KeyError, TypeError):
        if isinstance(record, dict):
            return record.get(key, default)
        return getattr(record, key, default)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
