from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from rtrieval_engine.domain import GraphCommunityHit, GraphRelationshipHit


class Neo4jGraphStorage:
    """图谱存储查询的 Neo4j 实现。

    这个存储类只负责执行查询。连接配置由宿主项目提供，本类不会读取环境变量。
    """

    def __init__(
        self,
        *,
        driver: Any | None = None,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        vector_index_name: str = "entity_vector",
        verify_connectivity: bool = False,
    ) -> None:
        if driver is None:
            if not uri or not user or password is None:
                raise ValueError("Provide either driver or uri/user/password.")
            driver = self._create_driver(uri=uri, user=user, password=password)

        self.driver = driver
        self.database = database
        self.vector_index_name = vector_index_name
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
        vector_index_name: str = "entity_vector",
        verify_connectivity: bool = False,
    ) -> Neo4jGraphStorage:
        return cls(
            uri=uri,
            user=user,
            password=password,
            database=database,
            vector_index_name=vector_index_name,
            verify_connectivity=verify_connectivity,
        )

    def close(self) -> None:
        close = getattr(self.driver, "close", None)
        if callable(close):
            close()

    def search_relationships(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[GraphRelationshipHit]:
        if not keyword.strip():
            return []

        query = """
        UNWIND $keywords AS keyword
        MATCH (source:Entity)-[relation:RELATION]-(target:Entity)
        WHERE toLower(source.name) CONTAINS keyword
           OR keyword CONTAINS toLower(source.name)
           OR toLower(target.name) CONTAINS keyword
           OR keyword CONTAINS toLower(target.name)
        RETURN source.name AS source,
               source.summary AS source_summary,
               source.type AS source_type,
               coalesce(relation.type, type(relation)) AS relation,
               target.name AS target,
               target.summary AS target_summary,
               target.type AS target_type
        LIMIT $limit
        """
        with self._session() as session:
            rows = session.run(
                query,
                keywords=[keyword.strip().lower()],
                limit=limit,
            ).data()

        return [
            GraphRelationshipHit(
                source=row.get("source") or "",
                source_summary=row.get("source_summary") or "",
                source_type=row.get("source_type") or "",
                relation=row.get("relation") or "",
                target=row.get("target") or "",
                target_summary=row.get("target_summary") or "",
                target_type=row.get("target_type") or "",
            )
            for row in rows
        ]

    def search_communities(
        self,
        keyword: str,
        limit: int = 3,
    ) -> list[GraphCommunityHit]:
        if not keyword.strip():
            return []

        query = """
        UNWIND $keywords AS keyword
        MATCH (entity:Entity)-[:IN_COMMUNITY]-(community:Community)
        WHERE toLower(entity.name) CONTAINS keyword
           OR keyword CONTAINS toLower(entity.name)
        RETURN DISTINCT community.communityId AS community_id,
               community.name AS name,
               community.cluster_type AS cluster_type,
               community.summary AS summary,
               community.size AS size,
               community.confidence AS confidence
        LIMIT $limit
        """
        with self._session() as session:
            rows = session.run(
                query,
                keywords=[keyword.strip().lower()],
                limit=limit,
            ).data()

        return [
            GraphCommunityHit(
                community_id=row.get("community_id"),
                name=row.get("name") or "",
                cluster_type=row.get("cluster_type") or "",
                summary=row.get("summary") or "",
                size=row.get("size"),
                confidence=row.get("confidence"),
            )
            for row in rows
        ]

    def search_relationships_by_vector(
        self,
        vector: Sequence[float],
        *,
        entity_limit: int = 5,
        relationship_limit: int = 20,
    ) -> list[GraphRelationshipHit]:
        if not vector:
            return []

        query = """
        CALL db.index.vector.queryNodes($index_name, $entity_limit, $vector)
        YIELD node AS matched_entity, score
        MATCH (matched_entity)-[relation:RELATION]-(neighbor:Entity)
        RETURN matched_entity.name AS source,
               matched_entity.summary AS source_summary,
               matched_entity.type AS source_type,
               coalesce(relation.type, type(relation)) AS relation,
               neighbor.name AS target,
               neighbor.summary AS target_summary,
               neighbor.type AS target_type,
               score AS score
        ORDER BY score DESC
        LIMIT $relationship_limit
        """
        with self._session() as session:
            rows = session.run(
                query,
                index_name=self.vector_index_name,
                entity_limit=entity_limit,
                relationship_limit=relationship_limit,
                vector=list(vector),
            ).data()

        return [
            GraphRelationshipHit(
                source=row.get("source") or "",
                source_summary=row.get("source_summary") or "",
                source_type=row.get("source_type") or "",
                relation=row.get("relation") or "",
                target=row.get("target") or "",
                target_summary=row.get("target_summary") or "",
                target_type=row.get("target_type") or "",
                score=_float_or_none(row.get("score")),
            )
            for row in rows
        ]

    def search_communities_by_vector(
        self,
        vector: Sequence[float],
        *,
        entity_limit: int = 5,
        community_limit: int = 3,
    ) -> list[GraphCommunityHit]:
        if not vector:
            return []

        query = """
        CALL db.index.vector.queryNodes($index_name, $entity_limit, $vector)
        YIELD node AS matched_entity, score
        MATCH (matched_entity)-[:IN_COMMUNITY]-(community:Community)
        RETURN DISTINCT community.communityId AS community_id,
               community.name AS name,
               community.cluster_type AS cluster_type,
               community.summary AS summary,
               community.size AS size,
               community.confidence AS confidence,
               max(score) AS score
        ORDER BY score DESC
        LIMIT $community_limit
        """
        with self._session() as session:
            rows = session.run(
                query,
                index_name=self.vector_index_name,
                entity_limit=entity_limit,
                community_limit=community_limit,
                vector=list(vector),
            ).data()

        return [
            GraphCommunityHit(
                community_id=row.get("community_id"),
                name=row.get("name") or "",
                cluster_type=row.get("cluster_type") or "",
                summary=row.get("summary") or "",
                size=row.get("size"),
                confidence=row.get("confidence"),
                score=_float_or_none(row.get("score")),
            )
            for row in rows
        ]

    def _create_driver(self, *, uri: str, user: str, password: str):
        try:
            from neo4j import GraphDatabase
        except ModuleNotFoundError as exc:
            message = "Install neo4j to use Neo4jGraphStorage."
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


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
