from pathlib import Path

from .pipelines.vector_pdf_pipeline import VectorPdfPipeline
from .readers.docx_reader import DocxReader
from .readers.tabular_reader import TabularReader
from .schema import Fragment


class DocumentRouter:
    """分发器：根据文件类型选择合适的 reader 或 pipeline 进行解析。"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.tabular_reader = TabularReader()
        self.docx_reader = DocxReader()
        self.vector_pdf_pipeline: VectorPdfPipeline | None = None

    def parse(self, file_path: str | Path) -> list[Fragment]:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".csv", ".xlsx", ".xlsm"]:
            return self.tabular_reader.parse(path)
        elif suffix == ".docx":
            return self.docx_reader.parse(path)
        elif suffix == ".pdf":
            if self.vector_pdf_pipeline is None:
                self.vector_pdf_pipeline = VectorPdfPipeline(output_dir=self.output_dir)
            return self._parse_pdf(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _parse_pdf(self, path: Path) -> list[Fragment]:
        return self.vector_pdf_pipeline.process_pdf(str(path))
