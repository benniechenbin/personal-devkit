from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from .protocols import DocumentPipeline, DocumentReader
from .schema import Fragment


class DocumentRouter:
    """分发器：根据文件类型选择合适的 reader 或 pipeline 进行解析。"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.tabular_reader: DocumentReader | None = None
        self.docx_reader: DocumentReader | None = None
        self.vector_pdf_pipeline: DocumentPipeline | None = None

    def parse(self, file_path: str | Path) -> list[Fragment]:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".csv", ".xlsx", ".xlsm"]:
            return self._get_tabular_reader().parse(path)
        elif suffix == ".docx":
            return self._get_docx_reader().parse(path)
        elif suffix == ".pdf":
            return self._parse_pdf(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _parse_pdf(self, path: Path) -> list[Fragment]:
        return self._get_vector_pdf_pipeline().process_pdf(str(path))

    def _get_tabular_reader(self) -> DocumentReader:
        if self.tabular_reader is None:
            from .readers.tabular_reader import TabularReader

            self.tabular_reader = TabularReader()
        return self.tabular_reader

    def _get_docx_reader(self) -> DocumentReader:
        if self.docx_reader is None:
            from .readers.docx_reader import DocxReader

            self.docx_reader = DocxReader()
        return self.docx_reader

    def _get_vector_pdf_pipeline(self) -> DocumentPipeline:
        if self.vector_pdf_pipeline is None:
            from .pipelines.vector_pdf_pipeline import VectorPdfPipeline

            pipeline_cls = cast(Any, VectorPdfPipeline)
            self.vector_pdf_pipeline = cast(
                DocumentPipeline,
                pipeline_cls(output_dir=self.output_dir),
            )
        return self.vector_pdf_pipeline
