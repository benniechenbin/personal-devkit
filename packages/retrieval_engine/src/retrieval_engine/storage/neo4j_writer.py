from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from retrieval_engine.domain import GraphEntity, GraphExtraction, GraphRelation
from retrieval_engine.providers import EmbeddingProvider


class Neo4jGraphWriter:
    """用于写入实体和关系的 Neo4j 图谱写入器。

    这个写入器不加载模型，也不读取配置。宿主项目可以注入 embedding provider
    来存储实体向量，也可以不注入，仅构建普通属性图。
    """

    def __init__(
        self,
        *,
        driver: Any | None = None,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_index_name: str = "entity_vector",
        vector_dimensions: int | None = None,
        vector_similarity: str = "cosine",
        verify_connectivity: bool = False,
        create_vector_index: bool = False,
    ) -> None:
        if driver is None:
            if not uri or not user or password is None:
                raise ValueError("Provide either driver or uri/user/password.")
            driver = self._create_driver(uri=uri, user=user, password=password)

        self.driver = driver
        self.database = database
        self.embedding_provider = embedding_provider
        self.vector_index_name = vector_index_name
        self.vector_dimensions = vector_dimensions
        self.vector_similarity = vector_similarity

        if verify_connectivity:
            verify = getattr(self.driver, "verify_connectivity", None)
            if callable(verify):
                verify()

        if create_vector_index:
            self.ensure_vector_index()

    @classmethod
    def from_uri(
        cls,
        *,
        uri: str,
        user: str,
        password: str,
        database: str | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_index_name: str = "entity_vector",
        vector_dimensions: int | None = None,
        vector_similarity: str = "cosine",
        verify_connectivity: bool = False,
        create_vector_index: bool = False,
    ) -> Neo4jGraphWriter:
        return cls(
            uri=uri,
            user=user,
            password=password,
            database=database,
            embedding_provider=embedding_provider,
            vector_index_name=vector_index_name,
            vector_dimensions=vector_dimensions,
            vector_similarity=vector_similarity,
            verify_connectivity=verify_connectivity,
            create_vector_index=create_vector_index,
        )

    def close(self) -> None:
        close = getattr(self.driver, "close", None)
        if callable(close):
            close()

    def ensure_vector_index(self) -> None:
        if self.vector_dimensions is None:
            raise ValueError("vector_dimensions is required to create a vector index.")

        cypher = f"""
        CREATE VECTOR INDEX {self.vector_index_name} IF NOT EXISTS
        FOR (entity:Entity) ON (entity.embedding)
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: $dimensions,
                `vector.similarity_function`: $similarity
            }}
        }}
        """
        with self._session() as session:
            session.run(
                cypher,
                dimensions=self.vector_dimensions,
                similarity=self.vector_similarity,
            )

    def upsert_extraction(
        self,
        extraction: GraphExtraction,
        *,
        source: str | None = None,
    ) -> None:
        self.upsert_entities(extraction.entities, source=source)
        self.upsert_relations(extraction.relationships, source=source)

    def upsert_entities(
        self,
        entities: Sequence[GraphEntity],
        *,
        source: str | None = None,
    ) -> None:
        for entity in entities:
            self.upsert_entity(entity, source=source)

    def upsert_relations(
        self,
        relations: Sequence[GraphRelation],
        *,
        source: str | None = None,
    ) -> None:
        for relation in relations:
            self.upsert_relation(relation, source=source)

    def upsert_entity(self, entity: GraphEntity, *, source: str | None = None) -> None:
        if not entity.id.strip():
            return

        vector = self._embed_entity(entity)
        cypher = """
        MERGE (entity:Entity {name: $name})
        SET entity.type = $type,
            entity.summary = $summary
        """
        params: dict[str, Any] = {
            "name": entity.id,
            "type": entity.type,
            "summary": entity.summary,
            "source": source,
        }
        if vector is not None:
            cypher += ", entity.embedding = $embedding\n"
            params["embedding"] = vector

        if source is not None:
            cypher += """
            SET entity.source_files = CASE
                WHEN entity.source_files IS NULL THEN [$source]
                WHEN $source IN entity.source_files THEN entity.source_files
                ELSE entity.source_files + [$source]
            END
            """

        with self._session() as session:
            session.run(cypher, **params)

    def upsert_relation(
        self,
        relation: GraphRelation,
        *,
        source: str | None = None,
    ) -> None:
        if not relation.source.strip() or not relation.target.strip():
            return

        cypher = """
        MATCH (source:Entity {name: $source_name})
        MATCH (target:Entity {name: $target_name})
        MERGE (source)-[relation:RELATION {type: $relation_type}]->(target)
        """
        params = {
            "source_name": relation.source,
            "target_name": relation.target,
            "relation_type": relation.relation,
            "source": source,
        }

        if source is not None:
            cypher += """
            SET relation.source_files = CASE
                WHEN relation.source_files IS NULL THEN [$source]
                WHEN $source IN relation.source_files THEN relation.source_files
                ELSE relation.source_files + [$source]
            END
            """

        with self._session() as session:
            session.run(cypher, **params)

    def remove_source(self, source: str) -> None:
        with self._session() as session:
            session.run(
                """
                MATCH ()-[relation:RELATION]->()
                WHERE $source IN relation.source_files
                SET relation.source_files = [
                    item IN relation.source_files WHERE item <> $source
                ]
                WITH relation WHERE size(relation.source_files) = 0
                DELETE relation
                """,
                source=source,
            )
            session.run(
                """
                MATCH (entity:Entity)
                WHERE $source IN entity.source_files
                SET entity.source_files = [
                    item IN entity.source_files WHERE item <> $source
                ]
                WITH entity WHERE size(entity.source_files) = 0
                DETACH DELETE entity
                """,
                source=source,
            )

    def clear(self) -> None:
        with self._session() as session:
            session.run("MATCH (node) DETACH DELETE node")

    def _embed_entity(self, entity: GraphEntity) -> list[float] | None:
        if self.embedding_provider is None:
            return None
        text = f"{entity.id}: {entity.summary}" if entity.summary else entity.id
        vector = self.embedding_provider.embed_query(text)
        return [float(value) for value in vector]

    def _create_driver(self, *, uri: str, user: str, password: str) -> Any:
        try:
            from neo4j import GraphDatabase
        except ModuleNotFoundError as exc:
            message = "Install neo4j to use Neo4jGraphWriter."
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
