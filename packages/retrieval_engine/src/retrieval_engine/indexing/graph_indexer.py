from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from rtrieval_engine.domain import BuildReport, DocumentChunk, GraphExtraction
from rtrieval_engine.indexing.graph_extractor import GraphExtractor
from rtrieval_engine.storage.graph_writer import GraphWriter

ProgressCallback = Callable[[int, str], None]


@dataclass(slots=True)
class GraphIndexResult:
    extraction: GraphExtraction
    source: str | None = None


class GraphIndexer:
    """通过图谱抽取器和图谱写入器把文档片段写入图谱。"""

    def __init__(
        self,
        *,
        extractor: GraphExtractor,
        writer: GraphWriter,
        strict: bool = False,
    ) -> None:
        self.extractor = extractor
        self.writer = writer
        self.strict = strict

    def index_document(
        self,
        document: DocumentChunk,
        *,
        source: str | None = None,
    ) -> GraphIndexResult:
        active_source = source or _source_from_document(document)
        extraction = self.extractor.extract(
            document.page_content,
            metadata=document.metadata,
            source=active_source,
        )
        self.writer.upsert_extraction(extraction, source=active_source)
        return GraphIndexResult(extraction=extraction, source=active_source)

    def index_documents(
        self,
        documents: Sequence[DocumentChunk],
        *,
        progress: ProgressCallback | None = None,
    ) -> BuildReport:
        report = BuildReport(
            total_documents=len(documents),
            total_chunks=len(documents),
        )

        for index, document in enumerate(documents, start=1):
            source = _source_from_document(document)
            try:
                result = self.index_document(document, source=source)
                report.created += len(result.extraction.entities)
                report.updated += len(result.extraction.relationships)
            except Exception as exc:
                if self.strict:
                    raise
                report.errors.append(f"{source or '<unknown>'}: {exc}")

            if progress is not None:
                progress(index, f"Indexed {index}/{len(documents)} graph documents")

        return report


def _source_from_document(document: DocumentChunk) -> str | None:
    source = (
        document.metadata.get("source")
        or document.metadata.get("source_file")
        or document.metadata.get("relative_path")
    )
    return str(source) if source is not None else None
