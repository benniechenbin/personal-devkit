from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from retrieval_sdk.domain import DocumentChunk
from retrieval_sdk.parsers.markdown import (
    parse_frontmatter,
    should_include_markdown_file,
)

ErrorCallback = Callable[[Path, Exception], None]


@dataclass(slots=True)
class MarkdownLoader:
    """把 Markdown 文件加载为完整文档。

    这个 loader 不做切片，也不做 embedding。切片和 embedding 策略属于
    具体项目，应由宿主项目在调用 indexing/storage 组件前自行提供。
    """

    source_dir: Path | str
    ignore_dirs: tuple[str, ...] = (".obsidian", ".trash")
    ignore_files: tuple[str, ...] = ()
    encoding: str = "utf-8"
    strict: bool = False
    metadata_defaults: dict[str, Any] = field(default_factory=dict)

    def load(self, on_error: ErrorCallback | None = None) -> list[DocumentChunk]:
        source_dir = Path(self.source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(
                f"Markdown source directory does not exist: {source_dir}"
            )

        documents: list[DocumentChunk] = []

        for file_path in self.iter_files():
            try:
                document = self.load_file(file_path)
                if document is not None:
                    documents.append(document)
            except Exception as exc:
                if self.strict:
                    raise
                if on_error is not None:
                    on_error(file_path, exc)

        return documents

    def iter_files(self) -> list[Path]:
        source_dir = Path(self.source_dir)
        return [
            path
            for path in source_dir.rglob("*.md")
            if should_include_markdown_file(
                path,
                ignore_dirs=self.ignore_dirs,
                ignore_files=self.ignore_files,
            )
        ]

    def load_file(self, file_path: Path | str) -> DocumentChunk | None:
        file_path = Path(file_path)
        content = file_path.read_text(encoding=self.encoding)
        global_metadata, body_text = parse_frontmatter(content)
        if not body_text:
            return None

        source_dir = Path(self.source_dir)
        try:
            relative_path = file_path.relative_to(source_dir)
        except ValueError:
            relative_path = Path(file_path.name)

        global_metadata = {
            **self.metadata_defaults,
            **global_metadata,
            "source_file": file_path.name,
            "source": file_path.name,
            "relative_path": str(relative_path),
        }
        return DocumentChunk(page_content=body_text, metadata=global_metadata)


def load_markdown_documents(
    source_dir: Path | str,
    **loader_options: Any,
) -> list[DocumentChunk]:
    """一次性加载 Markdown 文档的便利函数。"""
    return MarkdownLoader(source_dir=source_dir, **loader_options).load()
