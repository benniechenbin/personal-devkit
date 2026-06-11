from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from .schema import Fragment


@runtime_checkable
class DocumentReader(Protocol):
    """文档读取器协议，支持 .docx, .xlsx 等结构化程度较高的文件。"""

    def parse(self, file_path: Path) -> list[Fragment]:
        """解析文档并返回片段列表。"""
        ...


@runtime_checkable
class DocumentPipeline(Protocol):
    """复杂文档处理流水线协议，支持 PDF、图像等需要 OCR 或复杂分析的文件。"""

    def process_pdf(self, file_path: str) -> list[Fragment]:
        """处理 PDF 文件并返回片段列表。"""
        ...


@runtime_checkable
class DocumentFormatter(Protocol):
    """文本格式化器协议。"""

    def format_to_markdown(self, raw_text: str) -> str:
        """将原始文本格式化为 Markdown。"""
        ...


@runtime_checkable
class DocumentAssembler(Protocol):
    """文档片段重组协议。"""

    def assemble(self, fragments: list[Fragment]) -> str:
        """将离散的片段组装成连续的文本。"""
        ...
