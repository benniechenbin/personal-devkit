from pathlib import Path

from .engines.docx_engine import DocxEngine
from .engines.tabular_engine import TabularEngine
from .engines.vector_engine import VectorPipeline
from .schema import Fragment


class DocumentRouter:
    """分发器：根据文件类型选择合适的引擎进行解析"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.tabular_engine = TabularEngine()
        self.docx_engine = DocxEngine()
        self.vector_pipeline = None  # 延迟加载，因为 PDF 处理较重

    def parse(self, file_path: str | Path) -> list[Fragment]:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".csv", ".xlsx", ".xlsm"]:
            return self.tabular_engine.parse(path)
        elif suffix == ".docx":
            return self.docx_engine.parse(path)
        elif suffix == ".pdf":
            if self.vector_pipeline is None:
                self.vector_pipeline = VectorPipeline(output_dir=self.output_dir)
            # 注意：VectorPipeline 目前的接口可能不同，这里假设它有一个类似 parse 的接口
            # 实际上 VectorPipeline 需要 doc 对象，或者我们可以封装它
            return self._parse_pdf(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _parse_pdf(self, path: Path) -> list[Fragment]:
        return self.vector_pipeline.process_pdf(str(path))
