from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from rtrieval_engine.domain import DocumentChunk, ScoredDocument, VectorRecord


class QdrantVectorStorage:
    """只存储和查询已向量化记录的 Qdrant 适配器。"""

    def __init__(
        self,
        *,
        collection_name: str,
        vector_size: int,
        path: str | Path | None = None,
        distance: str = "cosine",
        client: Any | None = None,
        batch_size: int = 500,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        self.batch_size = batch_size
        self.id_factory = id_factory or (lambda: uuid.uuid4().hex)

        self._models = None
        self._point_struct = None
        self._vector_params = None
        self._distance_enum = None

        if client is None:
            self.client = self._create_client(path)
        else:
            self.client = client
            self._load_qdrant_types()

        self._ensure_collection()

    def close(self) -> None:
        close = getattr(self.client, "close", None)
        if callable(close):
            close()

    def add_vectors(self, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        self._upsert_records(self.collection_name, records)

    def replace_vectors(self, records: Sequence[VectorRecord]) -> None:
        staging_collection = self._versioned_collection_name()
        alias_switched = False
        old_alias_target = self._get_alias_target()
        old_physical_exists = old_alias_target is None and self.client.collection_exists(
            self.collection_name
        )

        self._create_collection(staging_collection)
        try:
            self._upsert_records(staging_collection, records)

            if old_alias_target:
                self.client.update_collection_aliases(
                    [
                        self._models.DeleteAliasOperation(
                            delete_alias=self._models.DeleteAlias(alias_name=self.collection_name)
                        ),
                        self._models.CreateAliasOperation(
                            create_alias=self._models.CreateAlias(
                                collection_name=staging_collection,
                                alias_name=self.collection_name,
                            )
                        ),
                    ]
                )
            else:
                if old_physical_exists:
                    self.client.delete_collection(self.collection_name)
                self._create_alias(staging_collection)

            alias_switched = True

            if old_alias_target and old_alias_target != staging_collection:
                self.client.delete_collection(old_alias_target)
        except Exception:
            if not alias_switched and self.client.collection_exists(staging_collection):
                self.client.delete_collection(staging_collection)
            raise

    def query(self, vector: Sequence[float], top_k: int = 5) -> list[ScoredDocument]:
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=list(vector),
            limit=top_k,
        )
        points = getattr(response, "points", response)
        results: list[ScoredDocument] = []

        for hit in points:
            payload = dict(getattr(hit, "payload", None) or {})
            content = payload.pop("page_content", "")
            score = getattr(hit, "score", None)
            results.append(
                ScoredDocument(
                    document=DocumentChunk(page_content=content, metadata=payload),
                    score=float(score) if score is not None else None,
                    source="vector",
                )
            )
        return results

    def clear(self) -> None:
        self.replace_vectors([])

    def _create_client(self, path: str | Path | None):
        try:
            from qdrant_client import QdrantClient, models
            from qdrant_client.http.models import Distance, PointStruct, VectorParams
        except ModuleNotFoundError as exc:
            message = "Install qdrant-client to use QdrantVectorStorage."
            raise RuntimeError(message) from exc

        self._models = models
        self._point_struct = PointStruct
        self._vector_params = VectorParams
        self._distance_enum = Distance

        if path is None:
            return QdrantClient(":memory:")
        Path(path).mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(path))

    def _load_qdrant_types(self) -> None:
        try:
            from qdrant_client import models
            from qdrant_client.http.models import Distance, PointStruct, VectorParams
        except ModuleNotFoundError as exc:
            message = "Install qdrant-client to use QdrantVectorStorage."
            raise RuntimeError(message) from exc

        self._models = models
        self._point_struct = PointStruct
        self._vector_params = VectorParams
        self._distance_enum = Distance

    def _distance(self):
        distance_name = self.distance.upper()
        if distance_name == "COSINE":
            return self._distance_enum.COSINE
        if distance_name == "DOT":
            return self._distance_enum.DOT
        if distance_name in {"EUCLID", "EUCLIDEAN"}:
            return self._distance_enum.EUCLID
        raise ValueError(f"Unsupported Qdrant distance: {self.distance}")

    def _versioned_collection_name(self) -> str:
        return f"{self.collection_name}_{uuid.uuid4().hex[:12]}"

    def _create_collection(self, collection_name: str) -> None:
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=self._vector_params(
                size=self.vector_size,
                distance=self._distance(),
            ),
        )

    def _create_alias(self, collection_name: str) -> None:
        self.client.update_collection_aliases(
            [
                self._models.CreateAliasOperation(
                    create_alias=self._models.CreateAlias(
                        collection_name=collection_name,
                        alias_name=self.collection_name,
                    )
                )
            ]
        )

    def _get_alias_target(self) -> str | None:
        for alias in self.client.get_aliases().aliases:
            if alias.alias_name == self.collection_name:
                return alias.collection_name
        return None

    def _ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return

        physical_name = self._versioned_collection_name()
        self._create_collection(physical_name)
        self._create_alias(physical_name)

    def _upsert_records(
        self,
        collection_name: str,
        records: Sequence[VectorRecord],
    ) -> None:
        for start in range(0, len(records), self.batch_size):
            batch = records[start : start + self.batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=[self._point_from_record(record) for record in batch],
            )

    def _point_from_record(self, record: VectorRecord):
        payload = {
            **record.document.metadata,
            "page_content": record.document.page_content,
        }
        return self._point_struct(
            id=record.id or self.id_factory(),
            vector=list(record.vector),
            payload=payload,
        )
